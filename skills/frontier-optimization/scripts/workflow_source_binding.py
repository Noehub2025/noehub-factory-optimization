#!/usr/bin/env python3
"""Read historical version 1 workflow-source bindings for exact audit/completion."""

from __future__ import annotations

import hashlib
import posixpath
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml


CONTRACT_VERSION = "frontier-workflow-source-binding/1"
REQUIRED_FIELDS = {
    "contract_version",
    "adoption_mode",
    "source_manifest",
    "source_snapshot",
    "governs",
}
SOURCE_REQUIRED_FIELDS = {"path", "identity", "file_sha256"}
MANIFEST_CONTRACT = "frontier-workflow-source-manifest/1"
SNAPSHOT_CONTRACT = "frontier-workflow-source-snapshot/1"
CLOSURE_CONTRACT_V1 = "frontier-workflow-source-closure/1"
GOVERNING_PATHS_V1 = frozenset({
    "SKILL.md",
    "agents/openai.yaml",
    "references/batch-interface.md",
    "references/candidate-lifecycle.md",
    "references/claim-records.md",
    "references/claim-review.md",
    "references/closeout-and-claims.md",
    "references/design-review.md",
    "references/entry-and-planning.md",
    "references/entry-code-planning.md",
    "references/evidence-records.md",
    "references/implementation-review.md",
    "references/packaging-and-recovery.md",
    "references/planning-records.md",
    "references/result-adoption.md",
    "references/review-branches.md",
    "references/review-snapshots.md",
    "references/technical-design.md",
    "references/work-plan.md",
    "references/worker-interfaces.md",
    "references/learning-loop.md",
    "references/campaign-state.md",
    "references/campaign-cycle.md",
    "references/frontier-core.md",
    "references/entry-review.md",
    "scripts/authorization_target_contract.py",
    "scripts/finding_effects.py",
    "scripts/freeze_execution_baseline.py",
    "scripts/identity_bindings.py",
    "scripts/package_frontier_handoff.py",
    "scripts/post_adoption_state.py",
    "scripts/project_snapshot.py",
    "scripts/validate_authorization_adoption.py",
    "scripts/validate_batch_packet.py",
    "scripts/validate_batch_result.py",
    "scripts/validate_candidate_package.py",
    "scripts/validate_candidate_recovery.py",
    "scripts/validate_entry_packet.py",
    "scripts/workflow_source_binding.py",
    "workers/grill-frontier/SKILL.md",
    "workers/grill-frontier/agents/openai.yaml",
    "workers/research-frontier/SKILL.md",
    "workers/research-frontier/agents/openai.yaml",
    "workers/review-frontier/SKILL.md",
    "workers/review-frontier/agents/openai.yaml",
    "workers/run-frontier-batch/SKILL.md",
    "workers/run-frontier-batch/agents/openai.yaml",
})
CLOSURE_PATHS_BY_CONTRACT = {CLOSURE_CONTRACT_V1: GOVERNING_PATHS_V1}
CURRENT_CLOSURE_CONTRACT = CLOSURE_CONTRACT_V1
GOVERNING_PATHS = GOVERNING_PATHS_V1


class WorkflowSourceBindingError(ValueError):
    """Raised when a workflow-source binding cannot be reproduced from bytes."""


def _safe_file(root: Path, value: Any, role: str) -> Path:
    if not isinstance(value, str) or not value or Path(value).is_absolute():
        raise WorkflowSourceBindingError(f"{role}.path must be repository-relative")
    resolved_root = root.resolve()
    candidate = resolved_root / value
    current = resolved_root
    for part in Path(value).parts:
        current /= part
        if current.is_symlink():
            raise WorkflowSourceBindingError(f"{role}.path crosses a symbolic link")
    path = candidate.resolve()
    try:
        path.relative_to(resolved_root)
    except ValueError as exc:
        raise WorkflowSourceBindingError(f"{role}.path escapes the repository") from exc
    if path.is_symlink() or not path.is_file():
        raise WorkflowSourceBindingError(f"{role}.path is not a regular file: {value}")
    return path


def _parse_mapping(raw: bytes, role: str) -> dict[str, Any]:
    try:
        value = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise WorkflowSourceBindingError(f"{role} is not valid YAML: {exc}") from exc
    if not isinstance(value, dict):
        raise WorkflowSourceBindingError(f"{role} must contain a mapping")
    return value


def _member_path(value: Any, role: str) -> str:
    if not isinstance(value, str) or not value or value.startswith("/"):
        raise WorkflowSourceBindingError(f"{role}.path must be a relative source path")
    normalized = posixpath.normpath(value)
    if normalized in {".", ".."} or normalized.startswith("../"):
        raise WorkflowSourceBindingError(f"{role}.path escapes the source snapshot")
    return normalized


@lru_cache(maxsize=8)
def _validated_source_members(
    manifest_raw: bytes,
    snapshot_raw: bytes,
    snapshot_identity: str,
) -> tuple[tuple[str, bytes], ...]:
    manifest = _parse_mapping(manifest_raw, "source_manifest")
    snapshot = _parse_mapping(snapshot_raw, "source_snapshot")
    if manifest.get("contract_version") != MANIFEST_CONTRACT:
        raise WorkflowSourceBindingError(
            f"source_manifest.contract_version must be {MANIFEST_CONTRACT}"
        )
    if snapshot.get("contract_version") != SNAPSHOT_CONTRACT:
        raise WorkflowSourceBindingError(
            f"source_snapshot.contract_version must be {SNAPSHOT_CONTRACT}"
        )
    if set(manifest) != {"contract_version", "closure_contract", "snapshot_identity", "members"}:
        raise WorkflowSourceBindingError(
            "source_manifest must contain exactly contract_version, closure_contract, snapshot_identity, and members"
        )
    if set(snapshot) != {"contract_version", "closure_contract", "members"}:
        raise WorkflowSourceBindingError(
            "source_snapshot must contain exactly contract_version, closure_contract, and members"
        )
    closure_contract = manifest.get("closure_contract")
    if closure_contract != snapshot.get("closure_contract"):
        raise WorkflowSourceBindingError("source manifest and snapshot closure contracts differ")
    required_paths = CLOSURE_PATHS_BY_CONTRACT.get(closure_contract)
    if required_paths is None:
        raise WorkflowSourceBindingError(
            f"unsupported workflow source closure contract: {closure_contract}"
        )
    if manifest.get("snapshot_identity") != snapshot_identity:
        raise WorkflowSourceBindingError(
            "source_manifest.snapshot_identity does not bind source_snapshot bytes"
        )
    manifest_members = manifest.get("members")
    snapshot_members = snapshot.get("members")
    if not isinstance(manifest_members, list) or not manifest_members:
        raise WorkflowSourceBindingError("source_manifest.members must be a nonempty ordered list")
    if not isinstance(snapshot_members, list) or not snapshot_members:
        raise WorkflowSourceBindingError("source_snapshot.members must be a nonempty ordered list")
    if len(manifest_members) != len(snapshot_members):
        raise WorkflowSourceBindingError("source manifest and snapshot member counts differ")

    observed_paths: list[str] = []
    for index, (manifest_member, snapshot_member) in enumerate(
        zip(manifest_members, snapshot_members, strict=True)
    ):
        if not isinstance(manifest_member, dict) or set(manifest_member) != {
            "path",
            "size",
            "sha256",
        }:
            raise WorkflowSourceBindingError(
                f"source_manifest.members[{index}] must contain path, size, and sha256"
            )
        if not isinstance(snapshot_member, dict) or set(snapshot_member) != {"path", "content"}:
            raise WorkflowSourceBindingError(
                f"source_snapshot.members[{index}] must contain path and content"
            )
        manifest_path = _member_path(
            manifest_member.get("path"), f"source_manifest.members[{index}]"
        )
        snapshot_path = _member_path(
            snapshot_member.get("path"), f"source_snapshot.members[{index}]"
        )
        if manifest_path != snapshot_path:
            raise WorkflowSourceBindingError("source manifest and snapshot order or paths differ")
        content = snapshot_member.get("content")
        if not isinstance(content, str):
            raise WorkflowSourceBindingError(
                f"source_snapshot.members[{index}].content must be UTF-8 text"
            )
        content_bytes = content.encode()
        if manifest_member.get("size") != len(content_bytes):
            raise WorkflowSourceBindingError(f"source member size mismatch: {manifest_path}")
        if manifest_member.get("sha256") != hashlib.sha256(content_bytes).hexdigest():
            raise WorkflowSourceBindingError(f"source member digest mismatch: {manifest_path}")
        observed_paths.append(manifest_path)
        if manifest_path == "references/learning-loop.md":
            if "## Integrated direction resolver" not in content or any(
                f"| {row} |" not in content for row in range(1, 14)
            ):
                raise WorkflowSourceBindingError(
                    "learning-loop source does not contain the complete 13-row integrated resolver"
                )
    if len(observed_paths) != len(set(observed_paths)):
        raise WorkflowSourceBindingError("source snapshot contains duplicate member paths")
    observed_path_set = set(observed_paths)
    missing_governing = required_paths - observed_path_set
    extra_governing = observed_path_set - required_paths
    if missing_governing or extra_governing:
        raise WorkflowSourceBindingError(
            "source snapshot member set differs from its closure contract; missing="
            + ",".join(sorted(missing_governing))
            + "; extra="
            + ",".join(sorted(extra_governing))
        )
    return tuple(
        (member["path"], member["content"].encode())
        for member in snapshot_members
    )


def validate_source_closure(
    manifest_raw: bytes,
    snapshot_raw: bytes,
    snapshot_identity: str,
) -> None:
    """Validate immutable legacy source bytes, reusing exact-byte results in-process."""
    _validated_source_members(manifest_raw, snapshot_raw, snapshot_identity)


def validate_binding(
    binding: Any,
    root: Path | None,
    *,
    expected_adoption_mode: str | None = None,
) -> dict[str, str]:
    """Return observed identities after validating one exact source binding."""

    if not isinstance(binding, dict):
        raise WorkflowSourceBindingError("workflow_source_binding must be a mapping")
    missing = REQUIRED_FIELDS - binding.keys()
    if missing:
        raise WorkflowSourceBindingError(
            "workflow_source_binding is missing: " + ", ".join(sorted(missing))
        )
    allowed_fields = REQUIRED_FIELDS | {"prior_binding"}
    extra = binding.keys() - allowed_fields
    if extra:
        raise WorkflowSourceBindingError(
            "workflow_source_binding has unknown fields: " + ", ".join(sorted(extra))
        )
    if binding.get("contract_version") != CONTRACT_VERSION:
        raise WorkflowSourceBindingError(f"contract_version must be {CONTRACT_VERSION}")
    adoption_mode = binding.get("adoption_mode")
    if adoption_mode not in {"entry", "replan"}:
        raise WorkflowSourceBindingError("adoption_mode must be entry or replan")
    if expected_adoption_mode is not None and adoption_mode != expected_adoption_mode:
        raise WorkflowSourceBindingError(f"adoption_mode must be {expected_adoption_mode}")
    prior_binding = binding.get("prior_binding")
    if adoption_mode == "replan" and (
        not isinstance(prior_binding, str) or not prior_binding.strip()
    ):
        raise WorkflowSourceBindingError("replan adoption requires prior_binding")
    if adoption_mode == "entry" and "prior_binding" in binding:
        raise WorkflowSourceBindingError("entry adoption must not contain prior_binding")
    governs = binding.get("governs")
    if not (
        isinstance(governs, list)
        and governs
        and all(isinstance(item, str) and item.strip() for item in governs)
    ):
        raise WorkflowSourceBindingError("governs must be a nonempty list of object names")
    observed: dict[str, str] = {}
    raw_sources: dict[str, bytes] = {}
    for role in ("source_manifest", "source_snapshot"):
        source = binding.get(role)
        if not isinstance(source, dict):
            raise WorkflowSourceBindingError(f"{role} must be a mapping")
        missing_source = SOURCE_REQUIRED_FIELDS - source.keys()
        if missing_source:
            raise WorkflowSourceBindingError(
                f"{role} is missing: " + ", ".join(sorted(missing_source))
            )
        extra_source = source.keys() - SOURCE_REQUIRED_FIELDS
        if extra_source:
            raise WorkflowSourceBindingError(
                f"{role} has unknown fields: " + ", ".join(sorted(extra_source))
            )
        declared_digest = source.get("file_sha256")
        if not (
            isinstance(declared_digest, str)
            and len(declared_digest) == 64
            and all(character in "0123456789abcdef" for character in declared_digest)
        ):
            raise WorkflowSourceBindingError(f"{role}.file_sha256 must be a lowercase SHA-256")
        declared_identity = f"sha256:{declared_digest}"
        if source.get("identity") != declared_identity:
            raise WorkflowSourceBindingError(f"{role}.identity must match file_sha256")
        if root is None:
            observed[role] = declared_identity
            continue
        path = _safe_file(root, source.get("path"), role)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if source.get("file_sha256") != digest:
            raise WorkflowSourceBindingError(f"{role}.file_sha256 does not match source bytes")
        identity = f"sha256:{digest}"
        if source.get("identity") != identity:
            raise WorkflowSourceBindingError(f"{role}.identity must derive from source bytes")
        observed[role] = identity
        raw_sources[role] = path.read_bytes()
    if root is None:
        return observed
    validate_source_closure(
        raw_sources["source_manifest"],
        raw_sources["source_snapshot"],
        observed["source_snapshot"],
    )
    return observed


def source_member_bytes(binding: Any, root: Path, logical_path: str) -> bytes:
    """Return one verified archived source member from a complete binding."""

    validate_binding(binding, root)
    manifest_source = binding["source_manifest"]
    snapshot_source = binding["source_snapshot"]
    manifest_path = _safe_file(root, manifest_source["path"], "source_manifest")
    snapshot_path = _safe_file(root, snapshot_source["path"], "source_snapshot")
    members = _validated_source_members(
        manifest_path.read_bytes(),
        snapshot_path.read_bytes(),
        snapshot_source["identity"],
    )
    matches = [
        content
        for path, content in members
        if path == logical_path
    ]
    if len(matches) != 1:
        raise WorkflowSourceBindingError(
            f"source snapshot must contain exactly one UTF-8 member {logical_path}"
        )
    return matches[0]
