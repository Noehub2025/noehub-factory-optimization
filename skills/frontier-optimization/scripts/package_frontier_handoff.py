#!/usr/bin/env python3
"""Build and verify an immutable post-closeout Frontier handoff package."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import posixpath
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required to package Frontier handoffs") from exc


VALIDATOR = "frontier-handoff-package/1"
FORBIDDEN_PARTS = {".git", ".venv", "__pycache__"}
FORBIDDEN_SUFFIXES = {".pyc", ".pyo"}
REQUIRED_FIELDS = {
    "package_plan_path",
    "campaign_generation",
    "campaign_status",
    "closeout_identity",
    "final_handoff_identity",
    "final_budget_identity",
    "entries",
    "authority_effect",
}


class PackageError(ValueError):
    """Raised when a package cannot be built or verified safely."""


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode()


def canonical_payload(document: dict[str, Any]) -> bytes:
    payload = dict(document)
    payload.pop("package_id", None)
    return yaml.safe_dump(payload, sort_keys=False, allow_unicode=True).encode()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_relative(raw: Any, field: str) -> str:
    if not isinstance(raw, str) or not raw.strip() or raw.startswith("/"):
        raise PackageError(f"{field} must be a nonempty repository-relative path")
    normalized = posixpath.normpath(raw.strip().rstrip("/"))
    if normalized in {".", ".."} or normalized.startswith("../"):
        raise PackageError(f"{field} escapes its root")
    parts = Path(normalized).parts
    if any(part in FORBIDDEN_PARTS for part in parts) or Path(normalized).suffix in FORBIDDEN_SUFFIXES:
        raise PackageError(f"{field} contains excluded cache or version-control content: {normalized}")
    return normalized


def subtree_inventory(root: Path) -> tuple[list[dict[str, Any]], str]:
    files: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if any(part in FORBIDDEN_PARTS for part in relative.parts) or path.suffix in FORBIDDEN_SUFFIXES:
            continue
        files.append(
            {
                "path": relative.as_posix(),
                "size": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    if not files:
        raise PackageError(f"empty package subtree: {root}")
    return files, f"sha256:{hashlib.sha256(canonical_json(files)).hexdigest()}"


def source_identity(path: Path, scope: str) -> tuple[list[dict[str, Any]], str]:
    if scope == "file":
        if not path.is_file():
            raise PackageError(f"package source file is missing: {path}")
        record = {"path": path.name, "size": path.stat().st_size, "sha256": sha256_file(path)}
        return [record], f"sha256:{record['sha256']}"
    if scope == "subtree":
        if not path.is_dir():
            raise PackageError(f"package source subtree is missing: {path}")
        return subtree_inventory(path)
    raise PackageError("package entry scope must be file or subtree")


def add_finding(findings: list[dict[str, str]], code: str, detail: str) -> None:
    finding = {"code": code, "detail": detail}
    if finding not in findings:
        findings.append(finding)


def validate_plan(document: dict[str, Any], phase: str, repo_root: Path) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    for field in sorted(REQUIRED_FIELDS - document.keys()):
        add_finding(findings, "REQUIRED_FIELD_MISSING", field)
    generation = document.get("campaign_generation")
    if not isinstance(generation, int) or isinstance(generation, bool) or generation < 1:
        add_finding(findings, "CAMPAIGN_GENERATION_INVALID", "campaign_generation must be positive")
    if document.get("campaign_status") not in {"stopped", "halted"}:
        add_finding(
            findings,
            "CAMPAIGN_NOT_CLOSED",
            "handoff packaging requires stopped or halted campaign status",
        )
    if document.get("authority_effect") != "none":
        add_finding(
            findings,
            "PACKAGE_CREATED_AUTHORITY",
            "packaging must have authority_effect: none",
        )
    for field in ("closeout_identity", "final_handoff_identity", "final_budget_identity"):
        if not isinstance(document.get(field), str) or not document[field].strip():
            add_finding(findings, "CLOSEOUT_BINDING_MISSING", field)

    expanded_entries: list[dict[str, Any]] = []
    destination_files: set[str] = set()
    entries = document.get("entries")
    if not isinstance(entries, list) or not entries:
        add_finding(findings, "PACKAGE_ENTRIES_INVALID", "entries must be a nonempty list")
    else:
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict):
                add_finding(findings, "PACKAGE_ENTRY_INVALID", f"entries[{index}] must be a mapping")
                continue
            try:
                source_value = safe_relative(entry.get("source"), f"entries[{index}].source")
                destination_value = safe_relative(
                    entry.get("destination"), f"entries[{index}].destination"
                )
                scope = entry.get("scope")
                role = entry.get("role")
                expected_identity = entry.get("identity")
                if not isinstance(role, str) or not role.strip():
                    raise PackageError(f"entries[{index}].role is required")
                if not isinstance(expected_identity, str) or not expected_identity.startswith("sha256:"):
                    raise PackageError(f"entries[{index}].identity must be sha256:<digest>")
                source = (repo_root / source_value).resolve()
                if repo_root not in source.parents:
                    raise PackageError(f"entries[{index}].source escapes the repository")
                members, observed_identity = source_identity(source, scope)
                if observed_identity != expected_identity:
                    raise PackageError(
                        f"entries[{index}] identity mismatch: expected {expected_identity}, observed {observed_identity}"
                    )
                mapped: list[dict[str, Any]] = []
                if scope == "file":
                    destinations = [destination_value]
                else:
                    destinations = [posixpath.join(destination_value, member["path"]) for member in members]
                for member, destination in zip(members, destinations, strict=True):
                    if destination in destination_files:
                        raise PackageError(f"duplicate package destination: {destination}")
                    destination_files.add(destination)
                    mapped.append(
                        {
                            "source_member": member["path"],
                            "destination": destination,
                            "size": member["size"],
                            "sha256": member["sha256"],
                        }
                    )
                expanded_entries.append(
                    {
                        "source": source_value,
                        "scope": scope,
                        "identity": observed_identity,
                        "destination": destination_value,
                        "role": role,
                        "members": mapped,
                    }
                )
            except (OSError, PackageError) as exc:
                add_finding(findings, "PACKAGE_ENTRY_INVALID", str(exc))

    plan_sha256 = hashlib.sha256(canonical_payload(document)).hexdigest()
    expected_id = f"frontier-package-sha256:{plan_sha256}"
    declared_id = document.get("package_id")
    if phase == "draft" and declared_id is not None:
        add_finding(findings, "DRAFT_ALREADY_FROZEN", "draft package plan must omit package_id")
    elif phase == "frozen":
        if declared_id is None:
            add_finding(findings, "PACKAGE_ID_MISSING", "frozen package plan requires package_id")
        elif declared_id != expected_id:
            add_finding(
                findings,
                "PACKAGE_ID_MISMATCH",
                f"declared {declared_id!r}; computed {expected_id!r}",
            )
    elif phase not in {"draft", "frozen", "audit"}:
        add_finding(findings, "PHASE_INVALID", "phase must be draft, frozen, or audit")

    findings.sort(key=lambda item: (item["code"], item["detail"]))
    return {
        "validator": VALIDATOR,
        "campaign_generation": generation,
        "computed_package_id": expected_id,
        "package_ready": not findings,
        "expanded_entries": expanded_entries,
        "findings": findings,
    }


def package_directory_name(package_id: str) -> str:
    return package_id.replace(":", "-")


def build(plan_path: Path, output_parent: Path, repo_root: Path) -> Path:
    document = yaml.safe_load(plan_path.read_bytes())
    if not isinstance(document, dict):
        raise PackageError("package plan must contain a YAML mapping")
    validation = validate_plan(document, "frozen", repo_root)
    if not validation["package_ready"]:
        raise PackageError(json.dumps(validation["findings"], sort_keys=True))
    package_id = validation["computed_package_id"]
    output_parent.mkdir(parents=True, exist_ok=True)
    final_root = output_parent / package_directory_name(package_id)
    if final_root.exists():
        raise PackageError(f"refusing to reuse package root: {final_root}")

    stage = Path(tempfile.mkdtemp(prefix=".frontier-package-", dir=output_parent))
    published = False
    try:
        payload_root = stage / "payload"
        payload_root.mkdir()
        manifest_files: list[dict[str, Any]] = []
        for entry in validation["expanded_entries"]:
            source_root = repo_root / entry["source"]
            for member in entry["members"]:
                source = source_root if entry["scope"] == "file" else source_root / member["source_member"]
                destination = payload_root / member["destination"]
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, destination)
                if sha256_file(destination) != member["sha256"]:
                    raise PackageError(f"copied byte identity mismatch: {member['destination']}")
                manifest_files.append(
                    {
                        "path": f"payload/{member['destination']}",
                        "sha256": member["sha256"],
                        "size": member["size"],
                        "role": entry["role"],
                        "source": entry["source"],
                    }
                )
        (stage / "package-plan.yaml").write_bytes(plan_path.read_bytes())
        manifest = {
            "validator": VALIDATOR,
            "package_id": package_id,
            "campaign_generation": document["campaign_generation"],
            "closeout_identity": document["closeout_identity"],
            "final_handoff_identity": document["final_handoff_identity"],
            "final_budget_identity": document["final_budget_identity"],
            "authority_effect": "none",
            "files": sorted(manifest_files, key=lambda item: item["path"]),
        }
        (stage / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        os.replace(stage, final_root)
        published = True
    finally:
        if not published:
            shutil.rmtree(stage, ignore_errors=True)
    verify(final_root)
    return final_root


def verify(package_root: Path) -> dict[str, Any]:
    manifest_path = package_root / "manifest.json"
    plan_path = package_root / "package-plan.yaml"
    if not manifest_path.is_file() or not plan_path.is_file():
        raise PackageError("package is missing manifest.json or package-plan.yaml")
    manifest = json.loads(manifest_path.read_text())
    plan = yaml.safe_load(plan_path.read_bytes())
    if not isinstance(manifest, dict) or not isinstance(manifest.get("files"), list):
        raise PackageError("package manifest is invalid")
    if not isinstance(plan, dict):
        raise PackageError("frozen package plan is invalid")
    expected_package_id = (
        f"frontier-package-sha256:{hashlib.sha256(canonical_payload(plan)).hexdigest()}"
    )
    if plan.get("package_id") != expected_package_id:
        raise PackageError("frozen package plan identity mismatch")
    if manifest.get("package_id") != expected_package_id:
        raise PackageError("package manifest and frozen plan bind different package identities")
    if package_root.name != package_directory_name(expected_package_id):
        raise PackageError("package root is not the content-addressed package identity")

    expected_manifest_files: list[dict[str, Any]] = []
    entries = plan.get("entries")
    if not isinstance(entries, list) or not entries:
        raise PackageError("frozen package plan has no entries")
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise PackageError(f"frozen package entry {index} is invalid")
        destination = safe_relative(entry.get("destination"), f"entries[{index}].destination")
        source = safe_relative(entry.get("source"), f"entries[{index}].source")
        scope = entry.get("scope")
        packaged_source = package_root / "payload" / destination
        members, observed_identity = source_identity(packaged_source, scope)
        if observed_identity != entry.get("identity"):
            raise PackageError(f"packaged entry identity mismatch: {destination}")
        for member in members:
            relative = destination if scope == "file" else posixpath.join(destination, member["path"])
            expected_manifest_files.append(
                {
                    "path": f"payload/{relative}",
                    "sha256": member["sha256"],
                    "size": member["size"],
                    "role": entry.get("role"),
                    "source": source,
                }
            )
    expected_manifest_files.sort(key=lambda item: item["path"])
    if manifest["files"] != expected_manifest_files:
        raise PackageError(
            "package manifest does not reproduce the frozen package plan: "
            f"expected {expected_manifest_files!r}, observed {manifest['files']!r}"
        )
    expected_paths = {"manifest.json", "package-plan.yaml"}
    for record in manifest["files"]:
        relative = safe_relative(record.get("path"), "manifest file path")
        expected_paths.add(relative)
        path = package_root / relative
        if not path.is_file():
            raise PackageError(f"package member is missing: {relative}")
        if sha256_file(path) != record.get("sha256") or path.stat().st_size != record.get("size"):
            raise PackageError(f"package member identity mismatch: {relative}")
    observed_paths = {
        path.relative_to(package_root).as_posix()
        for path in package_root.rglob("*")
        if path.is_file()
    }
    if observed_paths != expected_paths:
        raise PackageError(
            f"package file set mismatch: expected {sorted(expected_paths)}, observed {sorted(observed_paths)}"
        )
    return {
        "validator": VALIDATOR,
        "package_id": manifest.get("package_id"),
        "campaign_generation": manifest.get("campaign_generation"),
        "file_count": len(manifest["files"]),
        "package_verified": True,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("plan", type=Path)
    validate_parser.add_argument("--phase", choices=("draft", "frozen", "audit"), required=True)
    validate_parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    validate_parser.add_argument("--output", type=Path)

    build_parser = subparsers.add_parser("build")
    build_parser.add_argument("plan", type=Path)
    build_parser.add_argument("--output-parent", type=Path, required=True)
    build_parser.add_argument("--repo-root", type=Path, default=Path.cwd())

    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("package_root", type=Path)

    args = parser.parse_args(argv)
    try:
        if args.command == "validate":
            document = yaml.safe_load(args.plan.read_bytes())
            if not isinstance(document, dict):
                raise PackageError("package plan must contain a YAML mapping")
            result = validate_plan(document, args.phase, args.repo_root.resolve())
            rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(rendered)
            else:
                print(rendered, end="")
            return 0 if result["package_ready"] else 1
        if args.command == "build":
            root = build(args.plan, args.output_parent, args.repo_root.resolve())
            print(root)
            return 0
        result = verify(args.package_root)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (OSError, PackageError, json.JSONDecodeError, yaml.YAMLError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
