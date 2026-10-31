#!/usr/bin/env python3
"""Plan or apply a small, reversible project connection for the desktop plugin."""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

PACKAGE = Path(__file__).resolve().parents[1]
BEGIN = "<!-- noehub-optimization:begin -->"
END = "<!-- noehub-optimization:end -->"
BLOCK = (BEGIN + "\nFor Noehub optimization work, read "
         "[the project workflow guidance](.noehub/workflow.md).\n" + END)
SHARED_HEADINGS = ("## Frontier-seeking workflow behavior", "## User-facing workflow returns",
                   "## Common project capabilities")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def shared_guidance(package: Path) -> str:
    source = package / "AGENTS.md"
    if not source.is_file():
        source = package / "resources/shared-workflow.md"
    text = source.read_text(encoding="utf-8")
    return text[text.index(SHARED_HEADINGS[0]):].strip() + "\n"


def checked_path(root: Path, relative: str) -> Path:
    path = root / relative
    if not path.resolve().is_relative_to(root):
        raise ValueError(f"Destination escapes the selected repository: {relative}")
    for part in (path, *path.parents):
        if part == root:
            break
        if part.is_symlink():
            raise ValueError(f"Reconcile the symlink before setup: {relative}")
    return path


def environment() -> dict:
    try:
        yaml_version = importlib.metadata.version("PyYAML")
    except importlib.metadata.PackageNotFoundError:
        yaml_version = None
    ready = (os.name == "posix" and sys.version_info >= (3, 10)
             and bool(yaml_version and yaml_version.split('.')[0] == '6'))
    return {"python": sys.version.split()[0], "interpreter": sys.executable,
            "PyYAML": yaml_version, "platform": sys.platform, "ready": ready,
            "remedy": None if ready else "Use macOS or Linux with Python 3.10+ and requirements-runtime.txt in an isolated project environment."}


def plan(root: Path, package: Path = PACKAGE) -> tuple[dict, dict[str, bytes], dict[str, bytes | None]]:
    root, package = root.resolve(strict=True), package.resolve(strict=True)
    git = subprocess.run(["git", "-C", str(root), "rev-parse", "--show-toplevel"],
                         capture_output=True, text=True, check=True)
    if Path(git.stdout.strip()).resolve() != root:
        raise ValueError("Select the Git repository root explicitly, not a nested directory.")
    if root == package or root.is_relative_to(package):
        raise ValueError("Select the consuming project, not the installed plugin directory.")
    manifest = json.loads((package / "plugin.json").read_text(encoding="utf-8"))
    state_path = checked_path(root, ".noehub/setup.json")
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else None
    if state is not None and (not isinstance(state, dict)
                              or state.get("schema") != "noehub-setup/1"
                              or state.get("plugin") != manifest["name"]):
        raise ValueError("Existing .noehub/setup.json is not this plugin's setup record.")
    override = checked_path(root, "AGENTS.override.md")
    instructions = "AGENTS.override.md" if override.exists() and override.read_bytes().strip() else "AGENTS.md"
    instruction_path = checked_path(root, instructions)
    original = instruction_path.read_bytes() if instruction_path.exists() else b""
    text = original.decode("utf-8")
    if state and state.get("instruction_file") != instructions:
        raise ValueError("The effective root instruction file changed; reconcile the previous Noehub block first.")
    if BEGIN in text or END in text:
        if text.count(BEGIN) != 1 or text.count(END) != 1 or BLOCK not in text:
            raise ValueError("The existing Noehub instruction block was edited; merge it before setup.")
        updated = original
    else:
        # Retain every original byte, including its newline convention.
        updated = original + (b"\n\n" if original else b"") + BLOCK.encode() + b"\n"
    project_owned = any(heading in text for heading in SHARED_HEADINGS)
    guidance = (
        "# Noehub project workflow\n\n"
        "The user's task limits and existing project instructions control this guidance.\n"
        "Use it for requested optimization work; it does not activate a campaign.\n\n"
        "Discover `setup-noehub` through the host and load its host-supplied `SKILL.md`\n"
        "when setting up or repairing this connection. Its `references/desktop-runtime.md`\n"
        "explains package paths, dependencies, independent review and explicit recovery.\n"
        "Discover and load `frame-optimization` or `frontier-optimization` for the\n"
        "selected task. Naming a Skill alone does not load its instructions.\n\n"
        "Keep task records in `docs/skills/optimization/<task-slug>/` and recovery\n"
        "records in the project. Pass this repository explicitly to packaged scripts.\n"
        "Keep plugin code in its installation directory; rediscover that location\n"
        "after updates. No Hook or Rust build is required for the core workflow.\n\n"
        "Maintain shared research understanding in existing task material when forming\n"
        "questions, comparing investments, designing observations and adopting results.\n"
        "Use sufficient prose or the Frontier Skill's structured research-basis guide;\n"
        "neither form grants permission or certifies complete research.\n\n"
    )
    guidance += ("The shared workflow sections already in the project's instructions remain\n"
                 "project-owned. Reconcile meaningful differences there; do not duplicate them.\n"
                 if project_owned else shared_guidance(package))
    files = {instructions: updated, ".noehub/workflow.md": guidance.encode()}
    managed = {".noehub/workflow.md": digest(files[".noehub/workflow.md"])}
    record = {"schema": "noehub-setup/1", "plugin": manifest["name"],
              "version": manifest["version"], "instruction_file": instructions,
              "shared_guidance": "project-owned" if project_owned else "bundled",
              "files": managed}
    files[".noehub/setup.json"] = (json.dumps(record, indent=2) + "\n").encode()
    originals = {}
    for relative, data in files.items():
        path = checked_path(root, relative)
        before = path.read_bytes() if path.exists() else None
        originals[relative] = before
        if relative == ".noehub/workflow.md" and before is not None and before != data:
            if not state or state.get("files", {}).get(relative) != digest(before):
                raise ValueError(f"Preserve and merge existing edited content before setup: {relative}")
    report = {"project": str(root), "plugin": manifest["name"], "version": manifest["version"],
              "instruction_file": instructions, "environment": environment(),
              "review_existing_guidance": project_owned,
              "changes": [p for p, data in files.items() if originals[p] != data],
              "host_installation_verified": False, "independent_review_verified": False,
              "hook_installed": False}
    return report, files, originals


def apply(root: Path, files: dict[str, bytes], originals: dict[str, bytes | None]) -> None:
    """Check all conflicts before writing; each replacement is atomic, not the group."""
    root = root.resolve()
    for relative, before in originals.items():
        path = checked_path(root, relative)
        if (path.read_bytes() if path.exists() else None) != before:
            raise ValueError(f"File changed after planning: {relative}")
    # Persist the state last. An interrupted setup retains readable project files.
    for relative, data in files.items():
        if originals[relative] == data:
            continue
        path = checked_path(root, relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            try:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
                temporary.chmod(path.stat().st_mode & 0o777 if path.exists() else 0o644)
                os.replace(temporary, path)
            finally:
                temporary.unlink(missing_ok=True)


def main() -> int:
    if sys.version_info < (3, 10):
        print(json.dumps({"status": "unsupported_runtime", "error": "Use Python 3.10 or later."}))
        return 2
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--apply", action="store_true", help="Apply the planned project instruction changes.")
    args = parser.parse_args()
    try:
        report, files, originals = plan(args.root)
        if args.apply:
            if not report["environment"]["ready"]:
                raise ValueError(report["environment"]["remedy"])
            apply(args.root, files, originals)
        print(json.dumps({"status": "applied" if args.apply else "planned", **report}, indent=2))
        return 0
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        print(json.dumps({"status": "needs_reconciliation", "error": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
