#!/usr/bin/env python3
"""Validate or stage one complete Frontier candidate package."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any

from identity_bindings import (
    PACKAGE_PATH_SIZE_SHA256_V1,
    IdentityBindingError,
    normalize_repo_path,
    reject_symlink_components,
    tree_inventory,
)
from finding_effects import add_finding, finalize_findings

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required to validate candidate packages") from exc


VALIDATOR = "frontier-candidate-package-validation/3"
INVENTORY_CONTRACT = "frontier-candidate-package-inventory/1"
FINAL_MANIFEST_CONTRACT = "frontier-candidate-manifest/2"
DOWNSTREAM_MANIFEST_ROLES = {
    "implementation-review",
    "result",
    "result-validation",
}


def resolve_candidate_root(repo_root: Path, raw: Any) -> tuple[str, Path]:
    relative = normalize_repo_path(raw, "candidate_root")
    root = repo_root.resolve()
    reject_symlink_components(root, relative, "candidate_root")
    candidate_root = root / relative
    resolved = candidate_root.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise IdentityBindingError("candidate_root resolves outside the repository") from exc
    if not resolved.is_dir() or candidate_root.is_symlink():
        raise IdentityBindingError("candidate_root is missing, unsafe, or not a directory")
    return relative, resolved


def resolve_manifest(repo_root: Path, raw: Any) -> tuple[str, Path]:
    relative = normalize_repo_path(raw, "candidate_manifest_path")
    root = repo_root.resolve()
    reject_symlink_components(root, relative, "candidate_manifest_path")
    path = (root / relative).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise IdentityBindingError(
            "candidate_manifest_path resolves outside the repository"
        ) from exc
    if not path.is_file():
        raise IdentityBindingError("candidate_manifest_path is missing or is not a file")
    return relative, path


def resolve_output(repo_root: Path, raw: Any, field: str) -> tuple[str, Path]:
    relative = normalize_repo_path(raw, field)
    root = repo_root.resolve()
    reject_symlink_components(root, relative, field)
    path = root / relative
    resolved_parent = path.parent.resolve()
    try:
        resolved_parent.relative_to(root)
    except ValueError as exc:
        raise IdentityBindingError(f"{field} resolves outside the repository") from exc
    if path.exists() or path.is_symlink():
        raise IdentityBindingError(f"{field} must not already exist")
    return relative, path


def normalized_code_paths(value: Any, findings: list[dict[str, str]]) -> list[dict[str, str]]:
    if not isinstance(value, list):
        add_finding(
            findings,
            "MANIFEST_MEMBER_SCHEMA_INVALID",
            "candidate manifest code_paths must be a list",
        )
        return []
    members: list[dict[str, str]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict) or set(item) != {"path", "sha256"}:
            add_finding(
                findings,
                "MANIFEST_MEMBER_SCHEMA_INVALID",
                f"code_paths[{index}] must contain exactly path and sha256",
            )
            continue
        path = item.get("path")
        digest = item.get("sha256")
        if not isinstance(path, str) or not isinstance(digest, str):
            add_finding(
                findings,
                "MANIFEST_MEMBER_SCHEMA_INVALID",
                f"code_paths[{index}] path and sha256 must be strings",
            )
            continue
        members.append({"path": path, "sha256": digest.removeprefix("sha256:")})
    return members


def is_forbidden_runtime_artifact(relative: str) -> bool:
    path = Path(relative)
    return "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"}


def inventory_payload(document: dict[str, Any]) -> bytes:
    payload = dict(document)
    payload.pop("inventory_id", None)
    return yaml.safe_dump(payload, sort_keys=False, allow_unicode=True).encode()


def computed_inventory_id(document: dict[str, Any]) -> str:
    return "candidate-package-inventory-sha256:" + hashlib.sha256(
        inventory_payload(document)
    ).hexdigest()


def derive_candidate_inventory(
    repo_root: Path, candidate_root: Any, candidate_id: Any
) -> dict[str, Any]:
    """Derive the pre-execution package inventory from canonical candidate bytes."""
    root_relative, root_path = resolve_candidate_root(repo_root, candidate_root)
    members, package_identity = tree_inventory(
        root_path, PACKAGE_PATH_SIZE_SHA256_V1
    )
    for member in members:
        if is_forbidden_runtime_artifact(member["path"]):
            raise IdentityBindingError(
                f"candidate root contains prohibited runtime artifact {member['path']}"
            )
    package_sha256 = package_identity.removeprefix("sha256:")
    if not isinstance(candidate_id, str) or ":" not in candidate_id:
        raise IdentityBindingError("candidate_id must be a namespaced identity")
    expected_candidate_id = f"{candidate_id.rsplit(':', 1)[0]}:{package_sha256}"
    if candidate_id != expected_candidate_id:
        raise IdentityBindingError(
            f"candidate_id {candidate_id!r} does not equal byte-derived {expected_candidate_id!r}"
        )
    document: dict[str, Any] = {
        "contract_version": INVENTORY_CONTRACT,
        "candidate_root": root_relative,
        "identity_algorithm": PACKAGE_PATH_SIZE_SHA256_V1,
        "candidate_id": candidate_id,
        "package_sha256": package_sha256,
        "members": members,
    }
    document["inventory_id"] = computed_inventory_id(document)
    return document


def write_candidate_inventory(
    repo_root: Path, candidate_root: Any, inventory_path: Any, candidate_id: Any
) -> dict[str, Any]:
    """Write one immutable pre-execution inventory without requiring a manifest."""
    relative, path = resolve_output(repo_root, inventory_path, "package_inventory_path")
    document = derive_candidate_inventory(repo_root, candidate_root, candidate_id)
    raw = yaml.safe_dump(document, sort_keys=False, allow_unicode=True).encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
    except Exception:
        path.unlink(missing_ok=True)
        raise
    return {
        "validator": VALIDATOR,
        "inventory_path": relative,
        "inventory_sha256": hashlib.sha256(raw).hexdigest(),
        **document,
        "inventory_ready": True,
        "findings": [],
    }


def validate_candidate_inventory(
    repo_root: Path,
    candidate_root: Any,
    inventory_path: Any,
    *,
    expected_candidate_id: Any = None,
    expected_inventory_id: Any = None,
    expected_inventory_sha256: Any = None,
) -> dict[str, Any]:
    """Recompute one inventory from the complete canonical candidate root."""
    findings: list[dict[str, str]] = []
    relative: str | None = None
    observed_sha256: str | None = None
    document: dict[str, Any] | None = None
    try:
        relative, path = resolve_manifest(repo_root, inventory_path)
        raw = path.read_bytes()
        observed_sha256 = hashlib.sha256(raw).hexdigest()
        parsed = yaml.safe_load(raw)
        if not isinstance(parsed, dict):
            raise IdentityBindingError("package inventory must contain a mapping")
        document = parsed
    except (IdentityBindingError, OSError, yaml.YAMLError) as exc:
        add_finding(findings, "PACKAGE_INVENTORY_UNREADABLE", str(exc))

    derived: dict[str, Any] | None = None
    if document is not None:
        if document.get("contract_version") != INVENTORY_CONTRACT:
            add_finding(
                findings,
                "PACKAGE_INVENTORY_CONTRACT_INVALID",
                f"contract_version must be {INVENTORY_CONTRACT}",
            )
        try:
            derived = derive_candidate_inventory(
                repo_root, candidate_root, document.get("candidate_id")
            )
        except (IdentityBindingError, OSError) as exc:
            add_finding(findings, "CANDIDATE_PACKAGE_UNREADABLE", str(exc))
        if document.get("inventory_id") != computed_inventory_id(document):
            add_finding(
                findings,
                "PACKAGE_INVENTORY_IDENTITY_MISMATCH",
                "inventory_id does not equal the canonical inventory payload identity",
            )
        if derived is not None and document != derived:
            add_finding(
                findings,
                "PACKAGE_INVENTORY_CONTENT_MISMATCH",
                "package inventory does not exactly match the complete candidate root",
            )
        if expected_candidate_id is not None and document.get("candidate_id") != expected_candidate_id:
            add_finding(
                findings,
                "EXPECTED_CANDIDATE_IDENTITY_MISMATCH",
                f"declared {expected_candidate_id!r}; inventory records {document.get('candidate_id')!r}",
            )
        if expected_inventory_id is not None and document.get("inventory_id") != expected_inventory_id:
            add_finding(
                findings,
                "EXPECTED_PACKAGE_INVENTORY_IDENTITY_MISMATCH",
                f"declared {expected_inventory_id!r}; inventory records {document.get('inventory_id')!r}",
            )
    if expected_inventory_sha256 is not None and observed_sha256 is not None:
        expected = str(expected_inventory_sha256).removeprefix("sha256:")
        if expected != observed_sha256:
            add_finding(
                findings,
                "EXPECTED_PACKAGE_INVENTORY_SHA256_MISMATCH",
                f"declared {expected!r}; observed {observed_sha256!r}",
            )

    finding_summary = finalize_findings(findings)
    return {
        "validator": VALIDATOR,
        "inventory_path": relative,
        "inventory_sha256": observed_sha256,
        "inventory_id": document.get("inventory_id") if document else None,
        "candidate_id": document.get("candidate_id") if document else None,
        "package_sha256": document.get("package_sha256") if document else None,
        "members": document.get("members", []) if document else [],
        "inventory_ready": finding_summary["ready"],
        "findings": finding_summary["findings"],
        "blocking_findings": finding_summary["blocking_findings"],
        "repair_findings": finding_summary["repair_findings"],
        "advisories": finding_summary["advisories"],
        "finding_effect_counts": finding_summary["finding_effect_counts"],
    }


def validate_file_evidence(
    repo_root: Path,
    entries: Any,
    role: str,
    findings: list[dict[str, str]],
    *,
    manifest_relative: str,
    manifest_sha256: str,
    required_identity: str | None = None,
) -> None:
    if not isinstance(entries, list) or not entries:
        add_finding(
            findings,
            f"{role.upper()}_INVALID",
            f"{role} must be a nonempty list of content-addressed files",
        )
        return
    root = repo_root.resolve()
    required_identity_seen = required_identity is None
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            add_finding(findings, f"{role.upper()}_INVALID", f"{role}[{index}] must be a mapping")
            continue
        relative = entry.get("path")
        expected = entry.get("file_sha256", entry.get("sha256"))
        try:
            normalized = normalize_repo_path(relative, f"{role}[{index}].path")
            reject_symlink_components(root, normalized, f"{role}[{index}].path")
            path = root / normalized
            if not path.is_file():
                raise IdentityBindingError(f"{role}[{index}] is missing or not a regular file")
            digest = str(expected).removeprefix("sha256:")
            if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
                raise IdentityBindingError(f"{role}[{index}].file_sha256 must be a lowercase SHA-256")
            raw = path.read_bytes()
            if required_identity is not None and required_identity.encode() in raw:
                required_identity_seen = True
            observed = hashlib.sha256(raw).hexdigest()
            if observed != digest:
                raise IdentityBindingError(
                    f"{role}[{index}] SHA-256 mismatch: declared {digest}, observed {observed}"
                )
            if normalized == manifest_relative:
                raise IdentityBindingError(f"{role}[{index}] must not bind the candidate manifest itself")
            if role == "engineering_evidence" and (
                manifest_relative.encode() in raw or manifest_sha256.encode() in raw
            ):
                raise IdentityBindingError(
                    f"{role}[{index}] creates a reverse dependency on the final candidate manifest"
                )
        except (IdentityBindingError, OSError) as exc:
            add_finding(findings, f"{role.upper()}_INVALID", str(exc))
    if not required_identity_seen:
        add_finding(
            findings,
            f"{role.upper()}_INVALID",
            f"{role} must include a content-addressed evidence manifest that binds {required_identity}",
        )


def validate_final_manifest_contract(
    repo_root: Path,
    candidate_root: Any,
    manifest: dict[str, Any],
    manifest_relative: str,
    manifest_sha256: str,
    findings: list[dict[str, str]],
    *,
    prohibited_downstream_paths: tuple[str, ...] = (),
) -> None:
    if manifest.get("manifest_contract") != FINAL_MANIFEST_CONTRACT:
        add_finding(
            findings,
            "FINAL_MANIFEST_CONTRACT_INVALID",
            f"manifest_contract must be {FINAL_MANIFEST_CONTRACT}",
        )
        return
    if manifest.get("manifest_state") != "final":
        add_finding(findings, "FINAL_MANIFEST_STATE_INVALID", "manifest_state must be final")
    binding = manifest.get("package_inventory")
    inventory_id: str | None = None
    if not isinstance(binding, dict) or set(binding) != {
        "path",
        "inventory_id",
        "file_sha256",
    }:
        add_finding(findings, "PACKAGE_INVENTORY_BINDING_INVALID", "final manifest requires package_inventory binding")
    else:
        if isinstance(binding.get("inventory_id"), str):
            inventory_id = binding["inventory_id"]
        inventory = validate_candidate_inventory(
            repo_root,
            candidate_root,
            binding.get("path"),
            expected_candidate_id=manifest.get("candidate_id"),
            expected_inventory_id=binding.get("inventory_id"),
            expected_inventory_sha256=binding.get("file_sha256"),
        )
        for finding in inventory["findings"]:
            add_finding(
                findings,
                "PACKAGE_INVENTORY_BINDING_INVALID",
                f"{finding['code']}: {finding['detail']}",
            )
        for advisory in inventory.get("advisories", []):
            add_finding(findings, advisory["code"], advisory["detail"])
    validate_file_evidence(
        repo_root,
        manifest.get("engineering_evidence"),
        "engineering_evidence",
        findings,
        manifest_relative=manifest_relative,
        manifest_sha256=manifest_sha256,
        required_identity=inventory_id,
    )
    recovery = manifest.get("recovery_artifacts")
    validate_file_evidence(
        repo_root,
        recovery,
        "recovery_artifacts",
        findings,
        manifest_relative=manifest_relative,
        manifest_sha256=manifest_sha256,
    )
    if isinstance(recovery, list):
        prohibited = {normalize_repo_path(path, "prohibited_downstream_path") for path in prohibited_downstream_paths}
        for index, entry in enumerate(recovery):
            if not isinstance(entry, dict):
                continue
            role = entry.get("role")
            path = entry.get("path")
            if role in DOWNSTREAM_MANIFEST_ROLES:
                add_finding(
                    findings,
                    "FINAL_MANIFEST_DOWNSTREAM_DEPENDENCY",
                    f"recovery_artifacts[{index}] role {role!r} is downstream of the final candidate manifest",
                )
            try:
                normalized = normalize_repo_path(path, f"recovery_artifacts[{index}].path")
            except IdentityBindingError:
                continue
            if normalized in prohibited:
                add_finding(
                    findings,
                    "FINAL_MANIFEST_DOWNSTREAM_DEPENDENCY",
                    f"recovery_artifacts[{index}] binds downstream path {normalized}",
                )


def validate_candidate_package(
    repo_root: Path,
    candidate_root: Any,
    manifest_path: Any,
    *,
    expected_candidate_id: Any = None,
    expected_manifest_sha256: Any = None,
    require_final_manifest: bool = False,
    prohibited_downstream_paths: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Derive candidate identity from every regular file under candidate_root."""
    findings: list[dict[str, str]] = []
    root_relative: str | None = None
    manifest_relative: str | None = None
    manifest_sha256: str | None = None
    manifest: dict[str, Any] | None = None
    members: list[dict[str, Any]] = []
    package_sha256: str | None = None
    candidate_id: str | None = None
    resolved_root: Path | None = None
    resolved_manifest: Path | None = None

    try:
        root_relative, root_path = resolve_candidate_root(repo_root, candidate_root)
        resolved_root = root_path
        members, package_identity = tree_inventory(
            root_path, PACKAGE_PATH_SIZE_SHA256_V1
        )
        package_sha256 = package_identity.removeprefix("sha256:")
    except (IdentityBindingError, OSError) as exc:
        add_finding(findings, "CANDIDATE_PACKAGE_UNREADABLE", str(exc))

    try:
        manifest_relative, bound_manifest = resolve_manifest(repo_root, manifest_path)
        resolved_manifest = bound_manifest
        raw = bound_manifest.read_bytes()
        manifest_sha256 = hashlib.sha256(raw).hexdigest()
        parsed = yaml.safe_load(raw)
        if not isinstance(parsed, dict):
            raise IdentityBindingError("candidate manifest must contain a mapping")
        manifest = parsed
    except (IdentityBindingError, OSError, yaml.YAMLError) as exc:
        add_finding(findings, "CANDIDATE_MANIFEST_UNREADABLE", str(exc))

    if resolved_root is not None and resolved_manifest is not None:
        try:
            resolved_manifest.relative_to(resolved_root)
        except ValueError:
            pass
        else:
            add_finding(
                findings,
                "MANIFEST_INSIDE_CANDIDATE_ROOT",
                "candidate manifest must be outside the complete candidate root",
            )

    if expected_manifest_sha256 is not None and manifest_sha256 is not None:
        expected = str(expected_manifest_sha256).removeprefix("sha256:")
        if expected != manifest_sha256:
            add_finding(
                findings,
                "CANDIDATE_MANIFEST_IDENTITY_MISMATCH",
                f"declared {expected!r}; observed {manifest_sha256!r}",
            )

    if manifest is not None and package_sha256 is not None:
        for member in members:
            if is_forbidden_runtime_artifact(member["path"]):
                add_finding(
                    findings,
                    "FORBIDDEN_RUNTIME_ARTIFACT",
                    f"candidate root contains prohibited runtime artifact {member['path']}",
                )
        declared_id = manifest.get("candidate_id")
        if not isinstance(declared_id, str) or ":" not in declared_id:
            add_finding(
                findings,
                "MANIFEST_CANDIDATE_ID_INVALID",
                "candidate manifest requires a namespaced candidate_id",
            )
        else:
            candidate_id = f"{declared_id.rsplit(':', 1)[0]}:{package_sha256}"
            if declared_id != candidate_id:
                add_finding(
                    findings,
                    "MANIFEST_CANDIDATE_IDENTITY_MISMATCH",
                    f"manifest records {declared_id!r}; recomputed {candidate_id!r}",
                )
        if expected_candidate_id is not None and expected_candidate_id != candidate_id:
            add_finding(
                findings,
                "EXPECTED_CANDIDATE_IDENTITY_MISMATCH",
                f"declared {expected_candidate_id!r}; recomputed {candidate_id!r}",
            )

        observed_paths = [
            {"path": item["path"], "sha256": item["sha256"]} for item in members
        ]
        recorded_paths = normalized_code_paths(manifest.get("code_paths"), findings)
        if recorded_paths != observed_paths:
            add_finding(
                findings,
                "CANDIDATE_MEMBER_MISMATCH",
                f"manifest members {recorded_paths!r}; complete root inventory {observed_paths!r}",
            )

        source_result = manifest.get("source_result_identity")
        if not isinstance(source_result, dict):
            add_finding(
                findings,
                "PACKAGE_IDENTITY_INPUT_MISSING",
                "candidate manifest requires source_result_identity mapping",
            )
        else:
            if source_result.get("package_sha256") != package_sha256:
                add_finding(
                    findings,
                    "PACKAGE_IDENTITY_MISMATCH",
                    "source_result_identity.package_sha256 does not match the complete root inventory",
                )
            recorded_members = source_result.get("members")
            if recorded_members is not None and recorded_members != members:
                add_finding(
                    findings,
                    "PACKAGE_MEMBER_IDENTITY_MISMATCH",
                    "source_result_identity.members does not exactly match the complete root inventory",
                )
        if require_final_manifest and manifest_relative is not None and manifest_sha256 is not None:
            validate_final_manifest_contract(
                repo_root,
                candidate_root,
                manifest,
                manifest_relative,
                manifest_sha256,
                findings,
                prohibited_downstream_paths=prohibited_downstream_paths,
            )

    finding_summary = finalize_findings(findings)
    return {
        "validator": VALIDATOR,
        "identity_algorithm": PACKAGE_PATH_SIZE_SHA256_V1,
        "candidate_root": root_relative,
        "candidate_manifest_path": manifest_relative,
        "manifest_sha256": manifest_sha256,
        "candidate_id": candidate_id,
        "package_sha256": package_sha256,
        "members": members,
        "package_ready": finding_summary["ready"],
        "findings": finding_summary["findings"],
        "blocking_findings": finding_summary["blocking_findings"],
        "repair_findings": finding_summary["repair_findings"],
        "advisories": finding_summary["advisories"],
        "finding_effect_counts": finding_summary["finding_effect_counts"],
    }


def stage_candidate_package(
    repo_root: Path,
    candidate_root: Any,
    manifest_path: Any,
    runtime_root: Any,
    *,
    expected_candidate_id: Any = None,
    expected_manifest_sha256: Any = None,
) -> dict[str, Any]:
    """Copy only validated manifest members to a new isolated runtime directory."""
    validation = validate_candidate_package(
        repo_root,
        candidate_root,
        manifest_path,
        expected_candidate_id=expected_candidate_id,
        expected_manifest_sha256=expected_manifest_sha256,
    )
    if not validation["package_ready"]:
        return {**validation, "staged": False, "runtime_root": None}

    runtime_relative = normalize_repo_path(runtime_root, "runtime_root")
    root = repo_root.resolve()
    reject_symlink_components(root, runtime_relative, "runtime_root")
    destination = root / runtime_relative
    if destination.exists():
        raise IdentityBindingError("runtime_root must not already exist")
    source = (root / str(validation["candidate_root"])).resolve()
    resolved_destination = destination.resolve()
    try:
        resolved_destination.relative_to(source)
    except ValueError:
        pass
    else:
        raise IdentityBindingError("runtime_root must be outside candidate_root")
    try:
        source.relative_to(resolved_destination)
    except ValueError:
        pass
    else:
        raise IdentityBindingError("runtime_root must not contain candidate_root")
    destination.mkdir(parents=True)
    for member in validation["members"]:
        source_path = source / member["path"]
        destination_path = destination / member["path"]
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination_path)
    staged_members, staged_identity = tree_inventory(
        destination, PACKAGE_PATH_SIZE_SHA256_V1
    )
    if staged_members != validation["members"]:
        raise IdentityBindingError("staged runtime bytes do not match the candidate package")
    return {
        **validation,
        "staged": True,
        "runtime_root": runtime_relative,
        "runtime_package_sha256": staged_identity.removeprefix("sha256:"),
    }


def stage_candidate_inventory(
    repo_root: Path,
    candidate_root: Any,
    inventory_path: Any,
    runtime_root: Any,
    *,
    expected_candidate_id: Any = None,
    expected_inventory_id: Any = None,
    expected_inventory_sha256: Any = None,
) -> dict[str, Any]:
    """Stage canonical bytes from a validated pre-execution package inventory."""
    validation = validate_candidate_inventory(
        repo_root,
        candidate_root,
        inventory_path,
        expected_candidate_id=expected_candidate_id,
        expected_inventory_id=expected_inventory_id,
        expected_inventory_sha256=expected_inventory_sha256,
    )
    if not validation["inventory_ready"]:
        return {**validation, "staged": False, "runtime_root": None}
    runtime_relative = normalize_repo_path(runtime_root, "runtime_root")
    root = repo_root.resolve()
    reject_symlink_components(root, runtime_relative, "runtime_root")
    destination = root / runtime_relative
    if destination.exists():
        raise IdentityBindingError("runtime_root must not already exist")
    _, source = resolve_candidate_root(repo_root, candidate_root)
    resolved_destination = destination.resolve()
    try:
        resolved_destination.relative_to(source)
    except ValueError:
        pass
    else:
        raise IdentityBindingError("runtime_root must be outside candidate_root")
    try:
        source.relative_to(resolved_destination)
    except ValueError:
        pass
    else:
        raise IdentityBindingError("runtime_root must not contain candidate_root")
    destination.mkdir(parents=True)
    for member in validation["members"]:
        source_path = source / member["path"]
        destination_path = destination / member["path"]
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination_path)
    staged_members, staged_identity = tree_inventory(destination, PACKAGE_PATH_SIZE_SHA256_V1)
    if staged_members != validation["members"]:
        raise IdentityBindingError("staged runtime bytes do not match package inventory")
    return {
        **validation,
        "staged": True,
        "runtime_root": runtime_relative,
        "runtime_package_sha256": staged_identity.removeprefix("sha256:"),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate_root")
    parser.add_argument("candidate_manifest_path", nargs="?")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--expected-candidate-id")
    parser.add_argument("--expected-manifest-sha256")
    parser.add_argument("--stage-root")
    parser.add_argument("--inventory-path")
    parser.add_argument("--write-inventory")
    parser.add_argument("--expected-inventory-id")
    parser.add_argument("--expected-inventory-sha256")
    parser.add_argument("--require-final-manifest", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.write_inventory:
            if not args.expected_candidate_id:
                parser.error("--write-inventory requires --expected-candidate-id")
            result = write_candidate_inventory(
                args.repo_root,
                args.candidate_root,
                args.write_inventory,
                args.expected_candidate_id,
            )
        elif args.inventory_path and args.stage_root:
            result = stage_candidate_inventory(
                args.repo_root,
                args.candidate_root,
                args.inventory_path,
                args.stage_root,
                expected_candidate_id=args.expected_candidate_id,
                expected_inventory_id=args.expected_inventory_id,
                expected_inventory_sha256=args.expected_inventory_sha256,
            )
        elif args.inventory_path:
            result = validate_candidate_inventory(
                args.repo_root,
                args.candidate_root,
                args.inventory_path,
                expected_candidate_id=args.expected_candidate_id,
                expected_inventory_id=args.expected_inventory_id,
                expected_inventory_sha256=args.expected_inventory_sha256,
            )
        elif args.stage_root:
            if not args.candidate_manifest_path:
                parser.error("legacy manifest staging requires candidate_manifest_path")
            result = stage_candidate_package(
                args.repo_root,
                args.candidate_root,
                args.candidate_manifest_path,
                args.stage_root,
                expected_candidate_id=args.expected_candidate_id,
                expected_manifest_sha256=args.expected_manifest_sha256,
            )
        else:
            if not args.candidate_manifest_path:
                parser.error("final validation requires candidate_manifest_path")
            result = validate_candidate_package(
                args.repo_root,
                args.candidate_root,
                args.candidate_manifest_path,
                expected_candidate_id=args.expected_candidate_id,
                expected_manifest_sha256=args.expected_manifest_sha256,
                require_final_manifest=args.require_final_manifest,
            )
    except (IdentityBindingError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered)
    else:
        print(rendered, end="")
    ready = result.get("package_ready", result.get("inventory_ready", False))
    return 0 if ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
