#!/usr/bin/env python3
"""Validate and inventory the five-Skill Frontier workflow bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required to validate the Frontier Skill bundle") from exc


VALIDATOR = "frontier-skill-bundle/1"
EXPECTED_SKILLS = {
    "frontier-optimization": False,
    "research-frontier": True,
    "grill-frontier": True,
    "run-frontier-batch": True,
    "review-frontier": True,
}
REQUIRED_COORDINATOR_SCRIPTS = {
    "freeze_execution_baseline.py",
    "package_frontier_handoff.py",
    "validate_authorization_adoption.py",
    "validate_batch_packet.py",
    "validate_batch_result.py",
    "validate_candidate_recovery.py",
    "validate_entry_packet.py",
    "validate_frontier_skill_bundle.py",
}
LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
RUNTIME_ARTIFACT_LINKS = {"FRONTIER.md", "log.md"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def add_finding(findings: list[dict[str, str]], code: str, detail: str) -> None:
    finding = {"code": code, "detail": detail}
    if finding not in findings:
        findings.append(finding)


def parse_frontmatter(path: Path) -> dict[str, Any]:
    text = path.read_text()
    if not text.startswith("---\n"):
        raise ValueError("missing YAML frontmatter")
    _, raw, _ = text.split("---", 2)
    parsed = yaml.safe_load(raw)
    if not isinstance(parsed, dict):
        raise ValueError("frontmatter must be a mapping")
    return parsed


def validate(skills_root: Path) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    source_files: list[dict[str, Any]] = []
    discovered = {path.name for path in skills_root.iterdir() if path.is_dir()}
    missing = sorted(set(EXPECTED_SKILLS) - discovered)
    for name in missing:
        add_finding(findings, "SKILL_MISSING", name)
    if "review-frontier-claims" in discovered:
        add_finding(
            findings,
            "EXTRA_REVIEWER_SKILL",
            "claims must use review-frontier with review_kind: claims",
        )

    for name, implicit_expected in EXPECTED_SKILLS.items():
        skill_root = skills_root / name
        skill_md = skill_root / "SKILL.md"
        openai_yaml = skill_root / "agents/openai.yaml"
        if not skill_md.is_file() or not openai_yaml.is_file():
            continue
        try:
            frontmatter = parse_frontmatter(skill_md)
            if set(frontmatter) != {"name", "description"}:
                add_finding(
                    findings,
                    "SKILL_FRONTMATTER_INVALID",
                    f"{name} frontmatter must contain exactly name and description",
                )
            if frontmatter.get("name") != name:
                add_finding(
                    findings,
                    "SKILL_NAME_MISMATCH",
                    f"{name} declares {frontmatter.get('name')!r}",
                )
            metadata = yaml.safe_load(openai_yaml.read_text())
            implicit = metadata.get("policy", {}).get("allow_implicit_invocation")
            if implicit is not implicit_expected:
                add_finding(
                    findings,
                    "INVOCATION_POLICY_INVALID",
                    f"{name} allow_implicit_invocation is {implicit!r}, expected {implicit_expected!r}",
                )
        except (OSError, ValueError, yaml.YAMLError) as exc:
            add_finding(findings, "SKILL_METADATA_INVALID", f"{name}: {exc}")

    scripts_root = skills_root / "frontier-optimization/scripts"
    observed_scripts = {path.name for path in scripts_root.glob("*.py") if not path.name.startswith("test_")}
    for name in sorted(REQUIRED_COORDINATOR_SCRIPTS - observed_scripts):
        add_finding(findings, "REQUIRED_SCRIPT_MISSING", name)

    for skill_name in EXPECTED_SKILLS:
        skill_root = skills_root / skill_name
        if not skill_root.exists():
            continue
        for path in sorted(skill_root.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(skills_root)
            if "__pycache__" in relative.parts or path.suffix in {".pyc", ".pyo"}:
                continue
            if path.is_symlink():
                add_finding(findings, "SYMLINK_NOT_PORTABLE", relative.as_posix())
                continue
            data = path.read_bytes()
            source_files.append(
                {
                    "path": relative.as_posix(),
                    "size": len(data),
                    "sha256": hashlib.sha256(data).hexdigest(),
                }
            )
            if path.suffix == ".md":
                text = data.decode()
                if "/Users/" in text or "file://" in text:
                    add_finding(
                        findings,
                        "HOST_PATH_NOT_PORTABLE",
                        relative.as_posix(),
                    )
                for raw_target in LINK_PATTERN.findall(text):
                    target = raw_target.split("#", 1)[0]
                    if not target or "://" in target or target.startswith("/"):
                        continue
                    if target in RUNTIME_ARTIFACT_LINKS or target.startswith("frontier/"):
                        continue
                    resolved = (path.parent / target).resolve()
                    try:
                        resolved.relative_to(skills_root.resolve())
                    except ValueError:
                        add_finding(
                            findings,
                            "LINK_ESCAPES_BUNDLE",
                            f"{relative.as_posix()} -> {raw_target}",
                        )
                        continue
                    if not resolved.exists():
                        add_finding(
                            findings,
                            "BROKEN_INTERNAL_LINK",
                            f"{relative.as_posix()} -> {raw_target}",
                        )

    source_files.sort(key=lambda item: item["path"])
    bundle_sha256 = hashlib.sha256(
        json.dumps(
            source_files,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode()
    ).hexdigest()
    findings.sort(key=lambda item: (item["code"], item["detail"]))
    return {
        "validator": VALIDATOR,
        "expected_skills": sorted(EXPECTED_SKILLS),
        "bundle_sha256": bundle_sha256,
        "source_manifest": source_files,
        "bundle_ready": not findings,
        "findings": findings,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skills_root", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        result = validate(args.skills_root.resolve())
    except OSError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered)
    else:
        print(rendered, end="")
    return 0 if result["bundle_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
