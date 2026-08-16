#!/usr/bin/env python3
"""Source-derived authorization-target specification contract."""

from __future__ import annotations

import posixpath
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from identity_bindings import (
    BoundFile,
    IdentityBindingError,
    load_file_binding,
    sha256_bytes,
)


TARGET_SPEC_CONTRACT = "frontier-authorization-target-specification/1"
TARGET_SPEC_BINDING_FIELDS = {
    "contract_version",
    "path",
    "identity_field",
    "identity",
    "file_sha256",
}
TARGET_SPEC_REQUIRED_FIELDS = {
    "target_spec_id",
    "contract_version",
    "decision_id",
    "batch_id",
    "target_path",
    "user_result_path",
    "decision_record_path",
    "design_contract_identity",
    "source_base_identity",
    "scope",
    "maximum_spend",
    "stop_boundary",
    "result_path",
    "proposed_state_transition",
    "post_adoption_paths",
    "authorization_question",
    "authorize_consequence",
    "decline_consequence",
    "conditional_consequence",
}
TARGET_SPEC_STABLE_FIELDS = TARGET_SPEC_REQUIRED_FIELDS - {
    "target_spec_id",
    "contract_version",
    "target_path",
}
FINAL_TARGET_FIELDS = {
    "target_id",
    "identity_rule",
    "decision_id",
    "target_specification",
    "batch_id",
    "preflight_id",
    "design_contract_identity",
    "source_base_identity",
    "scope",
    "maximum_spend",
    "stop_boundary",
    "result_path",
    "user_result_path",
    "decision_record_path",
    "proposed_state_transition",
    "post_adoption_state",
    "post_adoption_paths",
    "authorization_question",
    "authorize_consequence",
    "decline_consequence",
    "conditional_consequence",
    "exact_object",
}
EXACT_OBJECT_FIELDS = {
    "batch_id",
    "packet",
    "structural_preflight",
    "reviewed_bindings",
}
EXACT_PACKET_FIELDS = {"path", "packet_id", "file_sha256"}
EXACT_PREFLIGHT_FIELDS = {"path", "preflight_id", "file_sha256"}
EXACT_REVIEWED_BINDING_FIELDS = {
    "role",
    "path",
    "identity",
    "identity_field",
    "file_sha256",
    "batch_scoped",
}
PROPOSED_TRANSITION_FIELDS = {"budget", "selection", "lifecycle"}
CURRENT_CHAIN_IDENTITY_PATTERNS = (
    ("batch packet", "{batch_id}-packet-sha256:"),
    ("batch preflight", "{batch_id}-packet-preflight-sha256:"),
    ("final authorization target", "{decision_id}-target-sha256:"),
    ("authorization answer", "{decision_id}-result-sha256:"),
    ("adoption", "authorization-adoption-sha256:"),
    ("acknowledgment", "{batch_id}-acknowledgment-sha256:"),
    ("execution start", "{batch_id}-execution-start-sha256:"),
)
ENTRY_IDENTITY_PATTERN = re.compile(
    r"\bentry-R[0-9]+(?:-packet)?-sha256:[0-9a-f]{64}\b"
)


class AuthorizationTargetContractError(ValueError):
    """Raised when the authorization-target chain is not source-derived."""


@dataclass(frozen=True)
class BoundTargetSpecification:
    """One verified authorization-target specification and its file binding."""

    source: BoundFile
    document: dict[str, Any]
    binding: dict[str, Any]


def _nonempty_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AuthorizationTargetContractError(f"{field} must be a nonempty string")
    return value


def _repo_relative_path(value: Any, field: str) -> str:
    raw = _nonempty_string(value, field)
    if raw.startswith("/"):
        raise AuthorizationTargetContractError(f"{field} must be repository-relative")
    normalized = posixpath.normpath(raw)
    if normalized in {".", ".."} or normalized.startswith("../"):
        raise AuthorizationTargetContractError(f"{field} escapes the repository")
    if normalized != raw:
        raise AuthorizationTargetContractError(f"{field} must be a canonical path")
    return normalized


def _strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for child in value for item in _strings(child)]
    if isinstance(value, dict):
        return [item for child in value.values() for item in _strings(child)]
    return []


def omitted_top_level_field_digest(raw: bytes, field: str) -> str:
    """Hash exact bytes after removing exactly one unindented ``field`` line."""
    marker = f"{field}:".encode()
    kept: list[bytes] = []
    found = 0
    for line in raw.splitlines(keepends=True):
        if line.startswith(marker):
            found += 1
            continue
        kept.append(line)
    if found != 1:
        raise AuthorizationTargetContractError(
            f"source must contain exactly one top-level {field} line"
        )
    return sha256_bytes(b"".join(kept))


def _validate_spec_document(document: dict[str, Any], raw: bytes) -> None:
    missing = TARGET_SPEC_REQUIRED_FIELDS - document.keys()
    unexpected = document.keys() - TARGET_SPEC_REQUIRED_FIELDS
    if missing:
        raise AuthorizationTargetContractError(
            "target specification is missing " + ", ".join(sorted(missing))
        )
    if unexpected:
        raise AuthorizationTargetContractError(
            "target specification contains unsupported fields: "
            + ", ".join(sorted(unexpected))
        )
    if document.get("contract_version") != TARGET_SPEC_CONTRACT:
        raise AuthorizationTargetContractError(
            f"target specification contract_version must be {TARGET_SPEC_CONTRACT}"
        )
    decision_id = _nonempty_string(document.get("decision_id"), "decision_id")
    batch_id = _nonempty_string(document.get("batch_id"), "batch_id")
    declared_identity = _nonempty_string(document.get("target_spec_id"), "target_spec_id")
    digest = omitted_top_level_field_digest(raw, "target_spec_id")
    expected_identity = f"{decision_id}-target-spec-sha256:{digest}"
    if declared_identity != expected_identity:
        raise AuthorizationTargetContractError(
            f"target_spec_id must be {expected_identity}, observed {declared_identity}"
        )

    for field in (
        "target_path",
        "user_result_path",
        "decision_record_path",
        "result_path",
    ):
        _repo_relative_path(document.get(field), field)
    for field in (
        "design_contract_identity",
        "source_base_identity",
        "scope",
        "maximum_spend",
        "stop_boundary",
        "authorization_question",
        "authorize_consequence",
        "decline_consequence",
        "conditional_consequence",
    ):
        _nonempty_string(document.get(field), field)

    transition = document.get("proposed_state_transition")
    if not isinstance(transition, dict) or set(transition) != PROPOSED_TRANSITION_FIELDS:
        raise AuthorizationTargetContractError(
            "proposed_state_transition must contain exactly budget, selection, and lifecycle"
        )
    paths = document.get("post_adoption_paths")
    if not isinstance(paths, list) or not paths:
        raise AuthorizationTargetContractError(
            "post_adoption_paths must be a nonempty list"
        )
    normalized_paths = [
        _repo_relative_path(value, f"post_adoption_paths[{index}]")
        for index, value in enumerate(paths)
    ]
    if len(set(normalized_paths)) != len(normalized_paths):
        raise AuthorizationTargetContractError("post_adoption_paths must be unique")
    if document.get("decision_record_path") not in normalized_paths:
        raise AuthorizationTargetContractError(
            "decision_record_path must be one of post_adoption_paths"
        )

    for label, template in CURRENT_CHAIN_IDENTITY_PATTERNS:
        marker = template.format(batch_id=batch_id, decision_id=decision_id)
        if any(marker in value for value in _strings(document)):
            raise AuthorizationTargetContractError(
                f"target specification must not contain the future current-chain {label} identity"
            )
    if any(ENTRY_IDENTITY_PATTERN.search(value) for value in _strings(document)):
        raise AuthorizationTargetContractError(
            "target specification must not contain an Entry packet or snapshot identity"
        )


def load_target_specification(
    repo_root: Path,
    binding: Any,
    *,
    role: str = "development_authorization_target",
) -> BoundTargetSpecification:
    """Load and validate one exact pre-packet authorization-target specification."""
    if not isinstance(binding, dict):
        raise AuthorizationTargetContractError(f"{role} must be a mapping")
    missing = TARGET_SPEC_BINDING_FIELDS - binding.keys()
    unexpected = binding.keys() - TARGET_SPEC_BINDING_FIELDS
    if missing:
        raise AuthorizationTargetContractError(
            f"{role} is missing " + ", ".join(sorted(missing))
        )
    if unexpected:
        raise AuthorizationTargetContractError(
            f"{role} contains unsupported fields: " + ", ".join(sorted(unexpected))
        )
    if binding.get("contract_version") != TARGET_SPEC_CONTRACT:
        raise AuthorizationTargetContractError(
            f"{role}.contract_version must be {TARGET_SPEC_CONTRACT}"
        )
    canonical_binding_path = _repo_relative_path(binding.get("path"), f"{role}.path")
    if binding.get("path") != canonical_binding_path:
        raise AuthorizationTargetContractError(f"{role}.path must be canonical")
    file_binding = {key: binding[key] for key in binding if key != "contract_version"}
    try:
        source = load_file_binding(
            repo_root,
            file_binding,
            role,
            expected_identity_field="target_spec_id",
        )
    except IdentityBindingError as exc:
        raise AuthorizationTargetContractError(str(exc)) from exc
    if source.document is None:
        raise AuthorizationTargetContractError(
            f"{role} source must contain a YAML or JSON mapping"
        )
    _validate_spec_document(source.document, source.raw)
    if source.document.get("contract_version") != binding.get("contract_version"):
        raise AuthorizationTargetContractError(
            f"{role} and its source declare different contract versions"
        )
    return BoundTargetSpecification(
        source=source,
        document=source.document,
        binding=dict(binding),
    )


def validate_target_specification_bytes(
    raw: bytes,
    binding: Any,
    *,
    role: str = "development_authorization_target",
) -> dict[str, Any]:
    """Validate snapshotted specification bytes against the exact packet binding."""
    if not isinstance(binding, dict):
        raise AuthorizationTargetContractError(f"{role} must be a mapping")
    missing = TARGET_SPEC_BINDING_FIELDS - binding.keys()
    unexpected = binding.keys() - TARGET_SPEC_BINDING_FIELDS
    if missing or unexpected:
        raise AuthorizationTargetContractError(
            f"{role} must contain exactly "
            + ", ".join(sorted(TARGET_SPEC_BINDING_FIELDS))
        )
    if binding.get("contract_version") != TARGET_SPEC_CONTRACT:
        raise AuthorizationTargetContractError(
            f"{role}.contract_version must be {TARGET_SPEC_CONTRACT}"
        )
    canonical_binding_path = _repo_relative_path(binding.get("path"), f"{role}.path")
    if binding.get("path") != canonical_binding_path:
        raise AuthorizationTargetContractError(f"{role}.path must be canonical")
    if binding.get("identity_field") != "target_spec_id":
        raise AuthorizationTargetContractError(
            f"{role}.identity_field must be 'target_spec_id'"
        )
    if binding.get("file_sha256") != sha256_bytes(raw):
        raise AuthorizationTargetContractError(f"{role} file SHA-256 mismatch")
    try:
        document = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise AuthorizationTargetContractError(
            f"{role} source is not valid YAML or JSON: {exc}"
        ) from exc
    if not isinstance(document, dict):
        raise AuthorizationTargetContractError(f"{role} source must contain a mapping")
    _validate_spec_document(document, raw)
    if binding.get("identity") != document.get("target_spec_id"):
        raise AuthorizationTargetContractError(f"{role} identity mismatch")
    if binding.get("contract_version") != document.get("contract_version"):
        raise AuthorizationTargetContractError(f"{role} contract version mismatch")
    return document


def validate_specification_against_packet(
    specification: BoundTargetSpecification,
    packet: dict[str, Any],
) -> list[str]:
    """Return semantic differences between a target specification and its packet."""
    spec = specification.document
    boundary = packet.get("authorization_boundary")
    expected = {
        "batch_id": packet.get("batch_id"),
        "design_contract_identity": packet.get("design_contract_identity"),
        "source_base_identity": packet.get("source_base_identity"),
        "scope": boundary.get("scope") if isinstance(boundary, dict) else None,
        "maximum_spend": (
            boundary.get("maximum_spend") if isinstance(boundary, dict) else None
        ),
        "stop_boundary": (
            boundary.get("stop_boundary") if isinstance(boundary, dict) else None
        ),
        "result_path": boundary.get("result_path") if isinstance(boundary, dict) else None,
    }
    differences = [
        f"{field}: specification {spec.get(field)!r}, packet {value!r}"
        for field, value in expected.items()
        if spec.get(field) != value
    ]
    if packet.get("maximum_spend") != spec.get("maximum_spend"):
        differences.append(
            "maximum_spend: packet top-level value does not equal target specification"
        )
    task_path = packet.get("task_path")
    if isinstance(task_path, str):
        expected_decision_record_path = posixpath.join(
            task_path, "frontier", "ledger.md"
        )
        if spec.get("decision_record_path") != expected_decision_record_path:
            differences.append(
                "decision_record_path: specification must use the task's canonical "
                f"Frontier ledger {expected_decision_record_path!r}"
            )
    target_path = spec.get("target_path")
    user_result_path = spec.get("user_result_path")
    post_adoption_paths = spec.get("post_adoption_paths", [])
    occupied_paths = {
        specification.source.relative_path,
        packet.get("packet_path"),
        packet.get("packet_preflight_path"),
        packet.get("acknowledgment_path"),
        packet.get("execution_start_path"),
        packet.get("candidate_manifest_path"),
        packet.get("result_validation_path"),
        packet.get("result_packet_path"),
    }
    if target_path in occupied_paths or target_path in post_adoption_paths:
        differences.append("target_path collides with another chain artifact or live transition path")
    if (
        user_result_path in occupied_paths
        or user_result_path == target_path
        or user_result_path in post_adoption_paths
    ):
        differences.append(
            "user_result_path collides with another chain artifact or live transition path"
        )
    if specification.source.relative_path in post_adoption_paths:
        differences.append(
            "the target specification cannot be replaced by the reviewed state transition"
        )
    return differences


def validate_target_realization(
    specification: BoundTargetSpecification | dict[str, Any],
    target_document: dict[str, Any],
    entry_target: dict[str, Any],
    *,
    binding: dict[str, Any] | None = None,
) -> list[str]:
    """Return differences between the stable specification and final target."""
    if isinstance(specification, BoundTargetSpecification):
        spec = specification.document
        expected_binding = specification.binding
    else:
        spec = specification
        expected_binding = binding
    if not isinstance(expected_binding, dict):
        raise AuthorizationTargetContractError(
            "target realization requires the exact specification binding"
        )
    differences: list[str] = []
    missing_target_fields = FINAL_TARGET_FIELDS - target_document.keys()
    unexpected_target_fields = target_document.keys() - FINAL_TARGET_FIELDS
    if missing_target_fields or unexpected_target_fields:
        differences.append(
            "final target fields differ from the canonical schema: "
            f"missing={sorted(missing_target_fields)}, "
            f"unsupported={sorted(unexpected_target_fields)}"
        )
    if target_document.get("identity_rule") != (
        "exact UTF-8 bytes with the complete target_id line omitted"
    ):
        differences.append("final target identity_rule is not canonical")
    exact_object = target_document.get("exact_object")
    if not isinstance(exact_object, dict) or set(exact_object) != EXACT_OBJECT_FIELDS:
        differences.append(
            "final target exact_object must contain exactly batch_id, packet, structural_preflight, and reviewed_bindings"
        )
    else:
        if exact_object.get("batch_id") != spec.get("batch_id"):
            differences.append("final target exact_object.batch_id does not equal the specification")
        packet_binding = exact_object.get("packet")
        if not isinstance(packet_binding, dict) or set(packet_binding) != EXACT_PACKET_FIELDS:
            differences.append("final target exact_object.packet schema is invalid")
        preflight_binding = exact_object.get("structural_preflight")
        if (
            not isinstance(preflight_binding, dict)
            or set(preflight_binding) != EXACT_PREFLIGHT_FIELDS
        ):
            differences.append(
                "final target exact_object.structural_preflight schema is invalid"
            )
        reviewed_bindings = exact_object.get("reviewed_bindings")
        if not isinstance(reviewed_bindings, list) or any(
            not isinstance(item, dict)
            or set(item) != EXACT_REVIEWED_BINDING_FIELDS
            for item in reviewed_bindings
        ):
            differences.append(
                "final target exact_object.reviewed_bindings schema is invalid"
            )
    if target_document.get("target_specification") != expected_binding:
        differences.append(
            "target_document.target_specification does not equal the packet-bound specification"
        )
    if entry_target.get("target_specification") != expected_binding:
        differences.append(
            "Entry authorization_target.target_specification does not equal the packet-bound specification"
        )
    if entry_target.get("target_path") != spec.get("target_path"):
        differences.append("Entry target_path does not equal the target specification")
    for field in sorted(TARGET_SPEC_STABLE_FIELDS):
        if target_document.get(field) != spec.get(field):
            differences.append(
                f"target_document.{field} does not equal the target specification"
            )
        if entry_target.get(field) != spec.get(field):
            differences.append(
                f"Entry authorization_target.{field} does not equal the target specification"
            )

    post_state = target_document.get("post_adoption_state")
    files = post_state.get("files") if isinstance(post_state, dict) else None
    realized_paths = (
        [item.get("path") for item in files if isinstance(item, dict)]
        if isinstance(files, list)
        else None
    )
    if realized_paths != spec.get("post_adoption_paths"):
        differences.append(
            "post_adoption_state file paths do not exactly realize post_adoption_paths"
        )
    return differences
