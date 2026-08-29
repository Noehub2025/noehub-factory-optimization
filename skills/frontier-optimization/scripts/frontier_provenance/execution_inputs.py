"""Verify retained-decision execution inputs from their authoritative content."""

from __future__ import annotations

import hashlib
import re
from typing import Any

from identity_bindings import IdentityBindingError, normalize_repo_path

from .content import ProvenanceError, verify_manifest


RETAINED_STATE_FIELDS = {"acknowledgment_id", "plan_id", "decision_content_root"}
BASELINE_STATE_FIELDS = {"acknowledgment", "plan", "execution_frozen_inputs"}


def execution_state_form(state: dict[str, Any]) -> str | None:
    """Classify the two authoritative state forms without using legacy locators."""

    has_retained = bool(RETAINED_STATE_FIELDS.intersection(state))
    has_baseline = bool(BASELINE_STATE_FIELDS.intersection(state))
    if has_retained and has_baseline:
        raise ProvenanceError(
            "project execution-state mixes retained-decision and baseline bindings"
        )
    if has_retained:
        return "retained-decision"
    if has_baseline:
        return "baseline"
    return None


def verify_retained_decision_inputs(
    *,
    plan: dict[str, Any],
    acknowledgment: dict[str, Any],
    state: dict[str, Any],
    baseline_raw: dict[str, bytes],
    decision_id: str,
    decision_content_root: str,
    authority_id: str,
    decision_manifest: dict[str, Any],
    decision_binding: dict[str, Any],
    decision_raw: dict[str, bytes],
    design_input_changes: dict[str, str] | None = None,
) -> None:
    """Verify one retained-decision state from acknowledgment through fixed bytes."""

    if execution_state_form(state) != "retained-decision":
        raise ProvenanceError("project execution-state is not retained-decision form")
    if not RETAINED_STATE_FIELDS.issubset(state):
        raise ProvenanceError(
            "project execution-state retained-decision form is incomplete"
        )
    if design_input_changes:
        raise ProvenanceError(
            "retained-decision inputs do not support delegated design changes"
        )
    if plan.get("sealed_runtime_input") is not None:
        raise ProvenanceError(
            "retained-decision inputs do not support sealed_runtime_input"
        )
    if any(name.startswith("project/state/frozen-inputs/") for name in baseline_raw):
        raise ProvenanceError(
            "project execution-state mixes retained-decision and baseline bindings"
        )

    plan_id = plan.get("batch_plan_id")
    acknowledgment_id = acknowledgment.get("acknowledgment_id")
    expected_state = {
        "contract_version": "frontier-project-execution-state/1",
        "batch_id": plan.get("batch_id"),
        "campaign_generation": plan.get("campaign_generation"),
        "decision_root": decision_id,
        "decision_content_root": decision_content_root,
        "authority_id": authority_id,
        "plan_id": plan_id,
        "acknowledgment_id": acknowledgment_id,
        "worker_may_start": False,
    }
    if any(state.get(field) != value for field, value in expected_state.items()):
        raise ProvenanceError(
            "project execution-state retained-decision parents are incomplete or mismatched"
        )
    if (
        not isinstance(plan_id, str)
        or not isinstance(acknowledgment_id, str)
        or acknowledgment.get("batch_id") != plan.get("batch_id")
        or acknowledgment.get("acknowledgment") != "accepted"
        or acknowledgment.get("decision_root") != decision_id
    ):
        raise ProvenanceError(
            "project acknowledgment does not bind the retained decision parents"
        )

    plan_binding = acknowledgment.get("batch_plan")
    plan_raw = baseline_raw.get("project/state/plan.yaml")
    if (
        not isinstance(plan_binding, dict)
        or plan_binding.get("plan_id") != plan_id
        or not isinstance(plan_raw, bytes)
        or plan_binding.get("file_sha256") != hashlib.sha256(plan_raw).hexdigest()
    ):
        raise ProvenanceError(
            "project acknowledgment does not bind the exact retained plan bytes"
        )

    content_binding = acknowledgment.get("decision_content")
    if not isinstance(content_binding, dict):
        raise ProvenanceError(
            "project acknowledgment lacks its reviewed decision content binding"
        )
    try:
        declared_path = normalize_repo_path(
            content_binding.get("path"), "decision_content.path"
        )
        resolved_path = normalize_repo_path(
            decision_binding.get("path"), "reviewed decision binding path"
        )
    except IdentityBindingError as exc:
        raise ProvenanceError(str(exc)) from exc
    if (
        declared_path != resolved_path
        or content_binding.get("root") != decision_content_root
        or decision_binding.get("manifest_file_sha256")
        != content_binding.get("manifest_file_sha256")
    ):
        raise ProvenanceError(
            "project acknowledgment does not bind the exact reviewed decision manifest"
        )

    try:
        manifest_root = verify_manifest(decision_manifest)
    except (TypeError, ValueError) as exc:
        raise ProvenanceError("reviewed decision manifest is invalid") from exc
    if manifest_root != decision_content_root:
        raise ProvenanceError("reviewed decision content root mismatch")
    storage = decision_manifest.get("storage")
    if (
        not isinstance(storage, dict)
        or storage.get("adapter") != "git-reference/1"
    ):
        raise ProvenanceError(
            "retained-decision requires a reviewed Git content reference"
        )
    paths = storage.get("paths")
    artifacts = decision_manifest.get("artifacts")
    if not isinstance(paths, dict) or not isinstance(artifacts, list):
        raise ProvenanceError(
            "reviewed decision manifest lacks exact path and artifact bindings"
        )

    artifact_by_name: dict[str, dict[str, Any]] = {}
    for artifact in artifacts:
        if not isinstance(artifact, dict) or not isinstance(
            artifact.get("logical_name"), str
        ):
            raise ProvenanceError("reviewed decision artifact binding is malformed")
        logical_name = artifact["logical_name"]
        if logical_name in artifact_by_name:
            raise ProvenanceError("reviewed decision artifact names must be unique")
        artifact_by_name[logical_name] = artifact

    logical_by_path: dict[str, str] = {}
    for logical_name, raw_path in paths.items():
        if logical_name not in artifact_by_name:
            raise ProvenanceError(
                "reviewed decision path references an unknown artifact"
            )
        try:
            relative = normalize_repo_path(
                raw_path, f"reviewed decision path {logical_name}"
            )
        except IdentityBindingError as exc:
            raise ProvenanceError(str(exc)) from exc
        if relative in logical_by_path:
            raise ProvenanceError(
                "reviewed decision repository paths must be unique"
            )
        logical_by_path[relative] = logical_name

    frozen_inputs = plan.get("execution_frozen_inputs")
    if not isinstance(frozen_inputs, list) or not frozen_inputs:
        raise ProvenanceError(
            "retained-decision plan requires nonempty execution_frozen_inputs"
        )
    seen_paths: set[str] = set()
    for index, entry in enumerate(frozen_inputs):
        if not isinstance(entry, dict) or set(entry) != {"path", "scope", "identity"}:
            raise ProvenanceError(
                f"execution_frozen_inputs[{index}] requires exactly path, scope, and identity"
            )
        if entry.get("scope") != "file":
            raise ProvenanceError(
                "retained-decision inputs support only exact file bindings"
            )
        try:
            relative = normalize_repo_path(
                entry.get("path"), f"execution_frozen_inputs[{index}].path"
            )
        except IdentityBindingError as exc:
            raise ProvenanceError(str(exc)) from exc
        if relative in seen_paths:
            raise ProvenanceError("execution_frozen_inputs paths must be unique")
        seen_paths.add(relative)
        identity = entry.get("identity")
        if not isinstance(identity, str) or not re.fullmatch(
            r"sha256:[0-9a-f]{64}", identity
        ):
            raise ProvenanceError(
                f"execution_frozen_inputs[{index}].identity must be one lowercase SHA-256"
            )
        logical_name = logical_by_path.get(relative)
        if logical_name is None:
            raise ProvenanceError(
                f"reviewed decision does not contain frozen input {relative}"
            )
        artifact = artifact_by_name[logical_name]
        raw = decision_raw.get(logical_name)
        expected_digest = identity.removeprefix("sha256:")
        if (
            not isinstance(raw, bytes)
            or artifact.get("kind") != "blob"
            or artifact.get("content_sha256") != expected_digest
            or hashlib.sha256(raw).hexdigest() != expected_digest
        ):
            raise ProvenanceError(
                f"reviewed decision bytes do not match frozen input {relative}"
            )
