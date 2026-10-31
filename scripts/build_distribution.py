#!/usr/bin/env python3
"""Build a reproducible desktop Skills or complete GitHub archive from an allowlist."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import zipfile

from noehub_setup import shared_guidance

ROOT = Path(__file__).resolve().parents[1]


def source_file(root: Path, relative: str) -> Path:
    path = PurePosixPath(relative)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise ValueError(f"Invalid package path: {relative}")
    result = root / relative
    if not result.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"Source escapes the repository: {relative}")
    for item in (result, *result.parents):
        if item == root:
            break
        if item.is_symlink():
            raise ValueError(f"Package sources must not be symlinks: {relative}")
    if not result.is_file():
        raise ValueError(f"Missing package source: {relative}")
    return result


def contents(root: Path, profile: str) -> tuple[dict, dict[str, bytes], dict[str, int]]:
    manifest = json.loads((root / "plugin.json").read_text(encoding="utf-8"))
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:-[A-Za-z0-9.-]+)?", manifest["version"]):
        raise ValueError("Use a semantic bundle version.")
    extension = manifest["extensions"]["com.openai"]
    if extension.get("requires_local_executor") is not True:
        raise ValueError("The desktop plugin must require a local executor.")
    if "hooks" in extension or "hooks" in manifest or "apps" in extension:
        raise ValueError("The shared plugin manifest must not register Hooks or app references.")
    claude = json.loads((root / ".claude-plugin/plugin.json").read_text())
    catalog = json.loads((root / ".claude-plugin/marketplace.json").read_text())
    if manifest["version"] != claude["version"] or manifest["version"] != catalog["plugins"][0]["version"]:
        raise ValueError("Portable and Claude bundle versions must agree within this repository.")
    selection = json.loads((root / "packaging/distributions.json").read_text())
    entry = selection["profiles"][profile]
    paths = selection["common"] + entry["include"]
    if len(paths) != len(set(paths)):
        raise ValueError("The distribution allowlist has duplicate paths.")
    payload, modes = {}, {}
    for name in sorted(paths):
        source = source_file(root, name)
        payload[name] = source.read_bytes()
        modes[name] = 0o755 if source.stat().st_mode & 0o111 else 0o644
    for destination, name in entry.get("replace", {}).items():
        # Apply the same path policy to destinations without requiring their existence.
        path = PurePosixPath(destination)
        if path.is_absolute() or ".." in path.parts or not path.parts:
            raise ValueError(f"Invalid package destination: {destination}")
        payload[destination] = source_file(root, name).read_bytes()
        modes[destination] = 0o644
    payload["resources/shared-workflow.md"] = shared_guidance(root).encode()
    modes["resources/shared-workflow.md"] = 0o644
    onboarding = extension["onboardingSkill"].removeprefix("./")
    expected = {p.removeprefix("./") + "/SKILL.md" for p in claude["skills"]} | {onboarding}
    actual = {p for p in payload if p.startswith("skills/") and p.endswith("/SKILL.md")}
    if actual != expected:
        raise ValueError(f"Package Skill set differs from its declared bundle: {actual ^ expected}")
    if profile == "marketplace" and any(
        name.startswith((".codex/", "hooks/", "tools/workflow-harness/src/"))
        or name.endswith("/hooks.json") for name in payload
    ):
        raise ValueError("The marketplace archive must not contain Hook definitions or Rust hosts.")
    if profile == "github" and ".codex/hooks.json" not in payload:
        raise ValueError("The GitHub archive must retain the optional Codex Hook.")
    return manifest, payload, modes


def build(root: Path, profile: str, output: Path) -> dict:
    manifest, payload, modes = contents(root, profile)
    source = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
                            capture_output=True, text=True, check=True).stdout.strip()
    record = {"schema": "noehub-distribution/1", "profile": profile,
              "version": manifest["version"], "source_commit": source,
              "source_note": "File hashes describe this working-tree build; the commit alone may not.",
              "files": {p: hashlib.sha256(data).hexdigest() for p, data in sorted(payload.items())}}
    payload["distribution.json"] = (json.dumps(record, indent=2, sort_keys=True) + "\n").encode()
    modes["distribution.json"] = 0o644
    # Exclusive output creation prevents replacing a previously reviewed artifact.
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with output.open("xb") as stream:
            with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
                for name, data in sorted(payload.items()):
                    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                    info.create_system = 3
                    info.external_attr = (0o100000 | modes[name]) << 16
                    info.compress_type = zipfile.ZIP_DEFLATED
                    archive.writestr(info, data, compresslevel=9)
    except FileExistsError:
        raise ValueError(f"Output already exists; choose a new path: {output}") from None
    return {"profile": profile, "version": manifest["version"], "files": len(payload),
            "archive": str(output.resolve()), "sha256": hashlib.sha256(output.read_bytes()).hexdigest()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=("marketplace", "github"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(build(ROOT, args.profile, args.output), indent=2))
        return 0
    except (ValueError, OSError, KeyError, subprocess.CalledProcessError) as exc:
        print(json.dumps({"status": "not_built", "error": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
