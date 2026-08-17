#!/usr/bin/env python3
"""Audit and verify historical version 1 Frontier handoff packages."""

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

from identity_bindings import (
    PACKAGE_PATH_SIZE_SHA256_V1,
    IdentityBindingError,
    load_file_binding,
    reject_symlink_components,
    tree_inventory,
)
from finding_effects import add_finding, finalize_findings
from workflow_source_binding import (
    WorkflowSourceBindingError,
    validate_binding,
    validate_source_closure,
)

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required to package Frontier handoffs") from exc


VALIDATOR = "frontier-handoff-package/3"
FORBIDDEN_PARTS = {".git", ".venv", "__pycache__"}
FORBIDDEN_SUFFIXES = {".pyc", ".pyo"}
REQUIRED_FIELDS = {
    "package_plan_path",
    "campaign_generation",
    "campaign_status",
    "closeout_identity",
    "final_handoff_identity",
    "final_budget_identity",
    "lineage_sources",
    "final_direction_state",
    "workflow_source_bindings",
    "subtree_identity_algorithm",
    "entries",
    "authority_effect",
}
FINAL_DIRECTION_REQUIRED = {
    "compatible_evidence",
    "controlling_reflections",
    "progress_meaning",
    "constraint_meaning",
    "route_set_state",
    "reopening_events",
    "diagnostic_dominance",
    "resolver",
    "budget_reachability",
    "workflow_source_identity",
}
FINAL_RESOLVER_REQUIRED = {
    "evidence_state_identity",
    "row",
    "direction_resolution",
    "exact_action",
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
    try:
        return tree_inventory(root, PACKAGE_PATH_SIZE_SHA256_V1)
    except IdentityBindingError as exc:
        raise PackageError(str(exc)) from exc


def source_identity(path: Path, scope: str) -> tuple[list[dict[str, Any]], str]:
    if scope == "file":
        if not path.is_file() or path.is_symlink():
            raise PackageError(f"package source file is missing: {path}")
        record = {"path": path.name, "size": path.stat().st_size, "sha256": sha256_file(path)}
        return [record], f"sha256:{record['sha256']}"
    if scope == "subtree":
        if not path.is_dir():
            raise PackageError(f"package source subtree is missing: {path}")
        return subtree_inventory(path)
    raise PackageError("package entry scope must be file or subtree")


def validate_plan(document: dict[str, Any], phase: str, repo_root: Path) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    if phase != "audit":
        add_finding(
            findings,
            "LEGACY_PACKAGER_READ_ONLY",
            "new handoffs must use frontier_provenance_cli export-handoff",
        )
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
    if document.get("subtree_identity_algorithm") != PACKAGE_PATH_SIZE_SHA256_V1:
        add_finding(
            findings,
            "SUBTREE_IDENTITY_ALGORITHM_INVALID",
            f"subtree_identity_algorithm must be {PACKAGE_PATH_SIZE_SHA256_V1}",
        )

    final_direction = document.get("final_direction_state")
    if not isinstance(final_direction, dict):
        add_finding(
            findings,
            "FINAL_DIRECTION_STATE_INVALID",
            "final_direction_state must be a mapping",
        )
    else:
        missing_direction = FINAL_DIRECTION_REQUIRED - final_direction.keys()
        if missing_direction:
            add_finding(
                findings,
                "FINAL_DIRECTION_STATE_INVALID",
                "missing fields: " + ", ".join(sorted(missing_direction)),
            )
        for field in ("compatible_evidence", "controlling_reflections", "reopening_events"):
            if not isinstance(final_direction.get(field), list):
                add_finding(
                    findings,
                    "FINAL_DIRECTION_STATE_INVALID",
                    f"{field} must be a list",
                )
        for field in (
            "progress_meaning",
            "constraint_meaning",
            "route_set_state",
            "diagnostic_dominance",
            "budget_reachability",
            "workflow_source_identity",
        ):
            if not isinstance(final_direction.get(field), str) or not final_direction[field].strip():
                add_finding(
                    findings,
                    "FINAL_DIRECTION_STATE_INVALID",
                    f"{field} must be a nonempty string",
                )
        resolver = final_direction.get("resolver")
        if not isinstance(resolver, dict) or FINAL_RESOLVER_REQUIRED - resolver.keys():
            add_finding(
                findings,
                "FINAL_DIRECTION_STATE_INVALID",
                "resolver must contain evidence_state_identity, row, direction_resolution, and exact_action",
            )
        elif (
            not isinstance(resolver.get("row"), int)
            or isinstance(resolver.get("row"), bool)
            or resolver["row"] not in range(1, 14)
            or any(
                not isinstance(resolver.get(field), str) or not resolver[field].strip()
                for field in ("evidence_state_identity", "direction_resolution", "exact_action")
            )
        ):
            add_finding(
                findings,
                "FINAL_DIRECTION_STATE_INVALID",
                "resolver fields must identify one exact row and action",
            )

    workflow_sources = document.get("workflow_source_bindings")
    validated_workflow_sources: list[dict[str, Any]] = []
    if not isinstance(workflow_sources, list) or not workflow_sources:
        add_finding(
            findings,
            "WORKFLOW_SOURCE_BINDINGS_INVALID",
            "workflow_source_bindings must be a nonempty list",
        )
    else:
        for index, binding in enumerate(workflow_sources):
            try:
                observed = validate_binding(binding, repo_root)
                validated_workflow_sources.append(
                    {"binding": binding, "observed": observed}
                )
            except WorkflowSourceBindingError as exc:
                add_finding(
                    findings,
                    "WORKFLOW_SOURCE_BINDING_INVALID",
                    f"workflow_source_bindings[{index}]: {exc}",
                )
        if isinstance(final_direction, dict):
            source_identities = {
                item["binding"]["source_snapshot"]["identity"]
                for item in validated_workflow_sources
            }
            if final_direction.get("workflow_source_identity") not in source_identities:
                add_finding(
                    findings,
                    "FINAL_DIRECTION_WORKFLOW_SOURCE_MISMATCH",
                    "final direction state must name one packaged adopted workflow source",
                )
    lineage = document.get("lineage_sources")
    observed_lineage: dict[str, str] = {}
    lineage_documents: dict[str, dict[str, Any]] = {}
    if not isinstance(lineage, dict):
        add_finding(
            findings,
            "LINEAGE_SOURCES_INVALID",
            "lineage_sources must bind closeout, handoff, and budget files",
        )
    else:
        for role in ("closeout", "handoff", "budget"):
            try:
                binding = load_file_binding(
                    repo_root,
                    lineage.get(role),
                    f"lineage_sources.{role}",
                    expected_identity_field=None,
                )
                observed_lineage[role] = binding.identity
                try:
                    parsed = yaml.safe_load(binding.raw)
                except yaml.YAMLError as exc:
                    raise IdentityBindingError(
                        f"lineage_sources.{role} is not valid YAML: {exc}"
                    ) from exc
                if not isinstance(parsed, dict):
                    raise IdentityBindingError(
                        f"lineage_sources.{role} must contain a source record mapping"
                    )
                lineage_documents[role] = parsed
            except IdentityBindingError as exc:
                add_finding(findings, "LINEAGE_SOURCE_INVALID", str(exc))
    for field in ("closeout_identity", "final_handoff_identity", "final_budget_identity"):
        if not isinstance(document.get(field), str) or not document[field].strip():
            add_finding(findings, "CLOSEOUT_BINDING_MISSING", field)
    expected_lineage = {
        "closeout_identity": observed_lineage.get("closeout"),
        "final_handoff_identity": observed_lineage.get("handoff"),
        "final_budget_identity": observed_lineage.get("budget"),
    }
    if observed_lineage and any(
        document.get(field) != identity for field, identity in expected_lineage.items()
    ):
        add_finding(
            findings,
            "LINEAGE_IDENTITY_NOT_DERIVED",
            "package lineage identities must derive from their bound source bytes",
        )
    closeout_source = lineage_documents.get("closeout")
    if closeout_source is not None and (
        closeout_source.get("event") != "CLOSEOUT_COMPLETE"
        or closeout_source.get("campaign_generation") != generation
        or closeout_source.get("campaign_status") != document.get("campaign_status")
        or closeout_source.get("unresolved_claims") != []
        or closeout_source.get("active_workers") != []
    ):
        add_finding(
            findings,
            "CLOSEOUT_FACTS_NOT_DERIVED",
            "package generation and status require a complete bound closeout record with no open claim or worker",
        )
    handoff_source = lineage_documents.get("handoff")
    if handoff_source is not None and handoff_source.get("handoff_complete") is not True:
        add_finding(
            findings,
            "HANDOFF_FACTS_NOT_DERIVED",
            "bound handoff record must report handoff_complete: true",
        )
    budget_source = lineage_documents.get("budget")
    if budget_source is not None:
        required_budget_facts = {
            "proposal_attempt_ceiling",
            "actual_spend",
            "unknown_spend",
            "active_reservations",
        }
        budget_values = tuple(
            budget_source.get(field)
            for field in (
                "proposal_attempt_ceiling",
                "actual_spend",
                "unknown_spend",
            )
        )
        budget_values_valid = all(
            isinstance(value, int) and not isinstance(value, bool) and value >= 0
            for value in budget_values
        )
        spend_within_ceiling = (
            budget_values_valid
            and budget_values[1] + budget_values[2] <= budget_values[0]
        )
        if (
            required_budget_facts - budget_source.keys()
            or budget_source.get("active_reservations") != []
            or not budget_values_valid
            or not spend_within_ceiling
        ):
            add_finding(
                findings,
                "BUDGET_FACTS_NOT_DERIVED",
                "bound budget record must contain nonnegative integer spend facts within the ceiling and no active reservation",
            )

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
                reject_symlink_components(
                    repo_root, source_value, f"entries[{index}].source"
                )
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
            except (OSError, PackageError, IdentityBindingError) as exc:
                add_finding(findings, "PACKAGE_ENTRY_INVALID", str(exc))

    if isinstance(lineage, dict) and expanded_entries:
        for role, binding in lineage.items():
            lineage_path = binding.get("path") if isinstance(binding, dict) else None
            covered = any(
                lineage_path == entry["source"]
                or (
                    entry["scope"] == "subtree"
                    and isinstance(lineage_path, str)
                    and lineage_path.startswith(entry["source"].rstrip("/") + "/")
                )
                for entry in expanded_entries
            )
            if isinstance(binding, dict) and not covered:
                add_finding(
                    findings,
                    "LINEAGE_SOURCE_NOT_PACKAGED",
                    f"lineage_sources.{role}.path must be included as an exact package entry",
                )

    if validated_workflow_sources and expanded_entries:
        for index, item in enumerate(validated_workflow_sources):
            for role in ("source_manifest", "source_snapshot"):
                source_path = item["binding"][role]["path"]
                covered = any(
                    source_path == entry["source"]
                    or (
                        entry["scope"] == "subtree"
                        and source_path.startswith(entry["source"].rstrip("/") + "/")
                    )
                    for entry in expanded_entries
                )
                if not covered:
                    add_finding(
                        findings,
                        "WORKFLOW_SOURCE_NOT_PACKAGED",
                        f"workflow_source_bindings[{index}].{role}.path must be included in entries",
                    )

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

    finding_summary = finalize_findings(findings)
    return {
        "validator": VALIDATOR,
        "campaign_generation": generation,
        "computed_package_id": expected_id,
        "package_ready": finding_summary["ready"],
        "expanded_entries": expanded_entries,
        "findings": finding_summary["findings"],
        "blocking_findings": finding_summary["blocking_findings"],
        "repair_findings": finding_summary["repair_findings"],
        "advisories": finding_summary["advisories"],
        "finding_effect_counts": finding_summary["finding_effect_counts"],
    }


def package_directory_name(package_id: str) -> str:
    return package_id.replace(":", "-")


def build(plan_path: Path, output_parent: Path, repo_root: Path) -> Path:
    del plan_path, output_parent, repo_root
    raise PackageError(
        "legacy handoff build is closed; use frontier_provenance_cli export-handoff"
    )

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
    top_level_bindings = (
        "validator",
        "campaign_generation",
        "closeout_identity",
        "final_handoff_identity",
        "final_budget_identity",
        "final_direction_state",
        "workflow_source_bindings",
        "authority_effect",
        "subtree_identity_algorithm",
    )
    expected_top_level = {
        "validator": VALIDATOR,
        **{field: plan.get(field) for field in top_level_bindings if field != "validator"},
    }
    observed_top_level = {field: manifest.get(field) for field in top_level_bindings}
    if observed_top_level != expected_top_level:
        raise PackageError("package manifest top-level provenance differs from the frozen plan")
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

    def packaged_source_path(source_path: str) -> Path | None:
        for entry_index, entry in enumerate(entries):
            entry_source = safe_relative(
                entry.get("source"), f"entries[{entry_index}].source"
            )
            destination = safe_relative(
                entry.get("destination"), f"entries[{entry_index}].destination"
            )
            if entry.get("scope") == "file" and entry_source == source_path:
                return package_root / "payload" / destination
            source_prefix = entry_source.rstrip("/") + "/"
            if entry.get("scope") == "subtree" and source_path.startswith(source_prefix):
                return package_root / "payload" / destination / source_path[len(source_prefix) :]
        return None

    workflow_sources = plan.get("workflow_source_bindings")
    if not isinstance(workflow_sources, list) or not workflow_sources:
        raise PackageError("frozen package plan has no workflow source bindings")
    for index, binding in enumerate(workflow_sources):
        if not isinstance(binding, dict):
            raise PackageError(f"workflow source binding {index} is invalid")
        recovered: dict[str, bytes] = {}
        for role in ("source_manifest", "source_snapshot"):
            source_binding = binding.get(role)
            if not isinstance(source_binding, dict) or not isinstance(
                source_binding.get("path"), str
            ):
                raise PackageError(f"workflow source binding {index}.{role} is invalid")
            recovered_path = packaged_source_path(source_binding["path"])
            if recovered_path is None or not recovered_path.is_file():
                raise PackageError(f"packaged workflow source is missing: {source_binding['path']}")
            raw = recovered_path.read_bytes()
            digest = hashlib.sha256(raw).hexdigest()
            if (
                source_binding.get("file_sha256") != digest
                or source_binding.get("identity") != f"sha256:{digest}"
            ):
                raise PackageError(
                    f"packaged workflow source identity mismatch: {source_binding['path']}"
                )
            recovered[role] = raw
        try:
            validate_source_closure(
                recovered["source_manifest"],
                recovered["source_snapshot"],
                binding["source_snapshot"]["identity"],
            )
        except WorkflowSourceBindingError as exc:
            raise PackageError(f"packaged workflow source is not recoverable: {exc}") from exc
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
    if any(path.is_symlink() for path in package_root.rglob("*")):
        raise PackageError("package contains a symbolic link")
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
