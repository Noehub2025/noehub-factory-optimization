"""Derive and validate one pre-authorized routine follow-up execution."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from typing import Any

import yaml

from evaluation_target_contract import (
    ROUTINE_ADMISSION_CONTRACT,
    validate_evaluation_target_contract,
    validate_experiment_source,
)

from .content import ProvenanceError, canonical_json
from .graph import verify_node
from .review_subject import require_current_review_subject


ADMISSION_LOGICAL_NAME = "project/state/routine-admission.yaml"
REQUIRED_LATE_OBJECTS = {
    "candidate_manifest",
    "candidate_collection",
    "materialization_execution_node",
    "materialization_outcome_node",
    "materialization_result",
    "materialization_result_validation",
    "implementation_review_decision_node",
    "implementation_review_attestation_node",
    "implementation_review_input",
    "implementation_review_report",
    "final_experiment",
    "runtime_inputs",
}


def validate_routine_admission(
    *,
    admission: dict[str, Any],
    authority: dict[str, Any],
    state_root: str,
    state_content: dict[str, Any],
    state_raw: dict[str, bytes],
    load: Callable[[str], dict[str, Any]],
    resolve_content: Callable[[str], dict[str, Any]],
    read_content: Callable[[str], dict[str, bytes]],
) -> dict[str, Any]:
    """Return the derived slot and target after fail-closed lineage checks."""

    required = {
        "contract_version",
        "evaluation_target",
        "origin_decision_root",
        "origin_authority_root",
        "materialization_execution_root",
        "materialization_outcome_root",
        "implementation_review_decision_root",
        "implementation_review_attestation_root",
        "live_receipt_root",
        "budget",
        "late_objects",
    }
    if not isinstance(admission, dict) or set(admission) != required:
        raise ProvenanceError("routine admission has unknown or missing fields")
    if admission["contract_version"] != ROUTINE_ADMISSION_CONTRACT:
        raise ProvenanceError(f"routine admission must use {ROUTINE_ADMISSION_CONTRACT}")
    verify_node(authority)
    if authority.get("role") != "authority":
        raise ProvenanceError("routine admission requires an authority node")
    if admission["origin_authority_root"] != authority["node_id"]:
        raise ProvenanceError("routine admission binds a different authority")

    decision_id = _parent(authority, "decision")
    if admission["origin_decision_root"] != decision_id:
        raise ProvenanceError("routine admission binds a different Entry decision")
    decision = load(decision_id)
    verify_node(decision)
    decision_content_root = decision["artifact_roots"][0]
    decision_content = resolve_content(decision_content_root)
    subject = require_current_review_subject(
        decision_content.get("review_subject"), expected_kind="entry"
    )
    projection = subject.get("semantic_projection", {}).get("routine_follow_up")
    if not isinstance(projection, dict):
        raise ProvenanceError("Entry did not pre-authorize a routine follow-up")

    target = admission["evaluation_target"]
    findings: list[dict[str, str]] = []
    validate_evaluation_target_contract(target, findings)
    if findings:
        raise ProvenanceError(
            "routine evaluation target is invalid: "
            + "; ".join(item["detail"] for item in findings)
        )
    slot = target["routine_slot"]
    expected_slot = {
        "contract_version": "frontier-routine-follow-up/1",
        "slot_id": projection["slot_id"],
        "materialization_batch_id": projection["materialization_batch_id"],
        "follow_up_batch_id": projection["follow_up_batch_id"],
        "origin_decision_root": decision_id,
        "origin_authority_root": authority["node_id"],
        "template_root": _template_root(projection["template"]),
    }
    if slot != expected_slot:
        raise ProvenanceError("routine target does not match the Entry-authorized slot")
    if target["protocol"] != {
        "contract_version": "frontier-evaluation-protocol/1",
        "content_root": decision_content_root,
        "protocol_id": projection["protocol_id"],
        "invalidation_key": projection["protocol_invalidation_key"],
    }:
        raise ProvenanceError("routine target protocol binding is invalid")
    if target["calibration"] != {
        "contract_version": "frontier-protocol-calibration-result/1",
        "content_root": decision_content_root,
        "calibration_id": projection["calibration_id"],
        "protocol_invalidation_key": projection["protocol_invalidation_key"],
    }:
        raise ProvenanceError("routine target calibration is stale or mismatched")

    _validate_state_closure(admission, state_root, state_content, state_raw)
    _validate_embedded_nodes(admission, state_raw, load)
    candidate = _derive_candidate(
        admission,
        state_content,
        state_raw,
        root_path=projection["template"]["evaluation_target"]["candidate"]["root_path"],
    )
    _validate_materialization(
        admission,
        authority,
        candidate,
        state_raw,
        load,
        resolve_content,
        read_content,
    )
    _validate_implementation_review(
        admission, candidate, state_raw, load, resolve_content, read_content
    )
    if target["candidate"] != candidate:
        raise ProvenanceError("routine target candidate was not derived from the materialization outcome")

    late_bindings = {
        "$late.candidate.id": candidate["id"],
        "$late.candidate.manifest_sha256": candidate["manifest_sha256"],
        "$late.candidate.collection_root": candidate["collection_root"],
    }
    expected_experiment_raw, experiment_id, experiment_sha = _materialize_experiment(
        projection["template"]["experiment"],
        late_bindings,
        projection["follow_up_batch_id"],
    )
    expected_target = _bind_template(
        projection["template"]["evaluation_target"],
        {
            **late_bindings,
            "$entry.origin_decision_root": decision_id,
            "$entry.origin_authority_root": authority["node_id"],
            "$entry.template_root": expected_slot["template_root"],
            "$entry.protocol_content_root": decision_content_root,
            "$entry.calibration_content_root": decision_content_root,
            "$entry.protocol_invalidation_key": projection[
                "protocol_invalidation_key"
            ],
            "$derived.experiment.id": experiment_id,
            "$derived.experiment.file_sha256": experiment_sha,
        },
    )
    if target != expected_target:
        raise ProvenanceError("routine target differs from the reviewed experiment template")
    experiment_name = admission["late_objects"]["final_experiment"]
    experiment_raw = state_raw[experiment_name]
    if experiment_raw != expected_experiment_raw:
        raise ProvenanceError("routine experiment bytes differ from the reviewed template")
    experiment_findings: list[dict[str, str]] = []
    validate_experiment_source(
        target["experiment"],
        logical_name=experiment_name,
        raw=experiment_raw,
        findings=experiment_findings,
    )
    if experiment_findings:
        raise ProvenanceError(
            "routine experiment identity is invalid: "
            + "; ".join(item["detail"] for item in experiment_findings)
        )
    runtime_name = admission["late_objects"]["runtime_inputs"]
    expected_runtime_raw = yaml.safe_dump(
        projection["template"]["runtime_inputs"],
        sort_keys=False,
        allow_unicode=True,
    ).encode()
    if state_raw[runtime_name] != expected_runtime_raw:
        raise ProvenanceError("routine runtime inputs differ from the reviewed template")
    live_receipt_content = resolve_content(admission["live_receipt_root"])
    live_receipt = live_receipt_content.get("receipt_facts", {}).get(
        "routine_slot_current", {}
    ).get("document")
    if (
        live_receipt_content.get("verified") is not True
        or live_receipt_content.get("domain") != "live-receipt"
        or not isinstance(live_receipt, dict)
    ):
        raise ProvenanceError("routine admission has no verified structured live receipt")
    _validate_budget(
        admission["budget"],
        projection,
        live_receipt=live_receipt,
        decision_root=decision_id,
        authority_root=authority["node_id"],
        template_root=expected_slot["template_root"],
    )
    return {
        "slot_id": projection["slot_id"],
        "follow_up_batch_id": projection["follow_up_batch_id"],
        "candidate": candidate,
        "evaluation_target": target,
    }


def _parent(node: dict[str, Any], edge: str) -> str:
    matches = [item["node_id"] for item in node["parents"] if item["edge"] == edge]
    if len(matches) != 1:
        raise ProvenanceError(f"node requires one {edge} parent")
    return matches[0]


def _template_root(value: dict[str, Any]) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value)).hexdigest()


def _parse(raw: bytes, role: str) -> dict[str, Any]:
    try:
        value = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise ProvenanceError(f"{role} is invalid: {exc}") from exc
    if not isinstance(value, dict):
        raise ProvenanceError(f"{role} must be a mapping")
    return value


def _validate_state_closure(
    admission: dict[str, Any],
    state_root: str,
    state_content: dict[str, Any],
    state_raw: dict[str, bytes],
) -> None:
    if state_content.get("content_root") != state_root or state_content.get("domain") != "project-state":
        raise ProvenanceError("routine admission state content does not match execution state")
    late = admission["late_objects"]
    if not isinstance(late, dict) or set(late) != REQUIRED_LATE_OBJECTS:
        raise ProvenanceError("routine admission late-object inventory is incomplete")
    file_objects = {value for key, value in late.items() if key != "candidate_collection"}
    if file_objects - state_raw.keys():
        raise ProvenanceError("routine admission cites missing late objects")
    if ADMISSION_LOGICAL_NAME not in state_raw:
        raise ProvenanceError("routine admission record is missing from project state")
    if _parse(state_raw[ADMISSION_LOGICAL_NAME], "routine admission record") != admission:
        raise ProvenanceError("routine admission request differs from frozen project state")
    collection_name = late["candidate_collection"]
    collections = state_content.get("closed_collections")
    matches = [item for item in collections or [] if item.get("logical_name") == collection_name]
    if (
        not isinstance(collections, list)
        or len(collections) != 1
        or len(matches) != 1
        or late["candidate_manifest"] not in matches[0].get("members", [])
    ):
        raise ProvenanceError("routine candidate collection is not closed over its manifest")
    expected_names = file_objects | set(matches[0]["members"]) | {ADMISSION_LOGICAL_NAME}
    if set(state_raw) != expected_names:
        raise ProvenanceError("routine project state has missing or unrelated artifacts")


def _derive_candidate(
    admission: dict[str, Any],
    state_content: dict[str, Any],
    state_raw: dict[str, bytes],
    *,
    root_path: str,
) -> dict[str, str]:
    late = admission["late_objects"]
    manifest = _parse(state_raw[late["candidate_manifest"]], "candidate manifest")
    candidate_id = manifest.get("candidate_id")
    if not isinstance(candidate_id, str) or not candidate_id:
        raise ProvenanceError("candidate manifest has no candidate identity")
    if manifest.get("manifest_contract") != "frontier-candidate-manifest/3" or manifest.get(
        "manifest_state"
    ) != "final":
        raise ProvenanceError("routine candidate requires a current final manifest")
    manifest_sha = hashlib.sha256(state_raw[late["candidate_manifest"]]).hexdigest()
    collection = next(
        item
        for item in state_content["closed_collections"]
        if item["logical_name"] == late["candidate_collection"]
    )
    prefix = collection["logical_name"].rstrip("/") + "/"
    member_names = collection.get("members")
    if not isinstance(member_names, list) or len(set(member_names)) != len(member_names):
        raise ProvenanceError("routine candidate collection membership is invalid")
    package_members: list[dict[str, Any]] = []
    for name in sorted(member_names):
        if name == late["candidate_manifest"]:
            continue
        if not isinstance(name, str) or not name.startswith(prefix) or name not in state_raw:
            raise ProvenanceError("routine candidate collection contains an invalid member")
        relative = name.removeprefix(prefix)
        if not relative or relative.startswith("../"):
            raise ProvenanceError("routine candidate member path is invalid")
        raw = state_raw[name]
        package_members.append(
            {
                "path": relative,
                "size": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
            }
        )
    if not package_members:
        raise ProvenanceError("routine candidate collection has no candidate bytes")
    package_sha = hashlib.sha256(canonical_json(package_members)).hexdigest()
    if ":" not in candidate_id or candidate_id != f"{candidate_id.rsplit(':', 1)[0]}:{package_sha}":
        raise ProvenanceError("routine candidate identity does not derive from candidate bytes")
    if manifest.get("source_result_identity") != {
        "package_sha256": package_sha,
        "members": package_members,
    }:
        raise ProvenanceError("routine candidate manifest package inventory is stale")
    if manifest.get("code_paths") != [
        {"path": item["path"], "sha256": item["sha256"]} for item in package_members
    ]:
        raise ProvenanceError("routine candidate manifest code paths are stale")
    collection_root = "sha256:" + package_sha
    return {
        "id": candidate_id,
        "root_path": root_path,
        "manifest_path": late["candidate_manifest"],
        "manifest_sha256": manifest_sha,
        "collection_root": collection_root,
    }


def _validate_embedded_nodes(
    admission: dict[str, Any],
    state_raw: dict[str, bytes],
    load: Callable[[str], dict[str, Any]],
) -> None:
    late = admission["late_objects"]
    bindings = (
        ("materialization_execution_node", admission["materialization_execution_root"]),
        ("materialization_outcome_node", admission["materialization_outcome_root"]),
        ("implementation_review_decision_node", admission["implementation_review_decision_root"]),
        (
            "implementation_review_attestation_node",
            admission["implementation_review_attestation_root"],
        ),
    )
    for role, node_id in bindings:
        try:
            embedded = json.loads(state_raw[late[role]])
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ProvenanceError(f"embedded {role} is unreadable") from exc
        if embedded != load(node_id) or verify_node(embedded) != node_id:
            raise ProvenanceError(f"embedded {role} differs from its canonical node")


def _validate_materialization(
    admission: dict[str, Any],
    authority: dict[str, Any],
    candidate: dict[str, str],
    state_raw: dict[str, bytes],
    load: Callable[[str], dict[str, Any]],
    resolve_content: Callable[[str], dict[str, Any]],
    read_content: Callable[[str], dict[str, bytes]],
) -> None:
    execution = load(admission["materialization_execution_root"])
    outcome = load(admission["materialization_outcome_root"])
    verify_node(execution)
    verify_node(outcome)
    if execution.get("role") != "execution" or _parent(execution, "authority") != authority["node_id"]:
        raise ProvenanceError("materialization execution does not descend from the Entry authority")
    if outcome.get("role") != "outcome" or _parent(outcome, "execution") != execution["node_id"]:
        raise ProvenanceError("materialization outcome does not descend from its execution")
    outcome_root = outcome["artifact_roots"][0]
    resolved = resolve_content(outcome_root)
    if resolved.get("domain") != "project-outcome" or resolved.get("verified") is not True:
        raise ProvenanceError("materialization outcome content did not verify")
    outcome_bytes = list(read_content(outcome_root).values())
    state_result = state_raw[admission["late_objects"]["materialization_result"]]
    state_validation = state_raw[
        admission["late_objects"]["materialization_result_validation"]
    ]
    if outcome_bytes.count(state_result) != 1 or outcome_bytes.count(state_validation) != 1:
        raise ProvenanceError(
            "materialization result or validation differs from canonical outcome content"
        )
    matches = []
    for raw in outcome_bytes:
        try:
            value = yaml.safe_load(raw)
        except yaml.YAMLError:
            continue
        if isinstance(value, dict) and value.get("candidate_identity") == candidate["id"]:
            matches.append(value)
    if len(matches) != 1 or matches[0].get("outcome") != "completed":
        raise ProvenanceError("materialization has no unique completed outcome for the candidate")
    validation = _parse(
        state_raw[admission["late_objects"]["materialization_result_validation"]],
        "materialization result validation",
    )
    if (
        validation.get("result_structure_ready") is not True
        or validation.get("blocking_findings") != []
        or validation.get("repair_findings") != []
    ):
        raise ProvenanceError("materialization result validation is not finding-free")


def _validate_implementation_review(
    admission: dict[str, Any],
    candidate: dict[str, str],
    state_raw: dict[str, bytes],
    load: Callable[[str], dict[str, Any]],
    resolve_content: Callable[[str], dict[str, Any]],
    read_content: Callable[[str], dict[str, bytes]],
) -> None:
    decision = load(admission["implementation_review_decision_root"])
    attestation = load(admission["implementation_review_attestation_root"])
    verify_node(decision)
    verify_node(attestation)
    if attestation.get("role") != "attestation" or _parent(attestation, "subject") != decision["node_id"]:
        raise ProvenanceError("implementation attestation binds a different decision")
    if attestation["payload"].get("verdict") != "ready" or any(
        item.get("effect") in {"block", "repair"}
        for item in attestation["payload"].get("findings", [])
    ):
        raise ProvenanceError("routine admission requires a finding-free implementation review")
    subject = require_current_review_subject(
        resolve_content(decision["artifact_roots"][0]).get("review_subject"),
        expected_kind="implementation",
    )
    reviewed = subject.get("semantic_projection", {}).get("candidate")
    if reviewed != candidate:
        raise ProvenanceError("implementation review covers a different candidate")
    decision_bytes = list(read_content(decision["artifact_roots"][0]).values())
    state_input = state_raw[admission["late_objects"]["implementation_review_input"]]
    if decision_bytes.count(state_input) != 1:
        raise ProvenanceError(
            "implementation review input differs from canonical decision content"
        )
    report_root = attestation["artifact_roots"][0]
    report_content = resolve_content(report_root)
    if report_content.get("domain") != "review-report" or report_content.get("verified") is not True:
        raise ProvenanceError("implementation review report content did not verify")
    report_bytes = list(read_content(report_root).values())
    state_report = state_raw[admission["late_objects"]["implementation_review_report"]]
    if report_bytes.count(state_report) != 1:
        raise ProvenanceError(
            "implementation review report differs from canonical review content"
        )


def _bind_template(value: Any, bindings: dict[str, str]) -> Any:
    if isinstance(value, str):
        return bindings.get(value, value)
    if isinstance(value, list):
        return [_bind_template(item, bindings) for item in value]
    if isinstance(value, dict):
        return {key: _bind_template(item, bindings) for key, item in value.items()}
    return value


def _materialize_experiment(
    template: dict[str, Any], bindings: dict[str, str], batch_id: str
) -> tuple[bytes, str, str]:
    document = _bind_template(template, bindings)
    document = {
        "identity_rule": (
            f"{batch_id}-experiment-sha256 of exact UTF-8 bytes with the "
            "complete experiment_id line omitted"
        ),
        **document,
    }
    body = yaml.safe_dump(document, sort_keys=False, allow_unicode=True).encode()
    experiment_id = f"{batch_id}-experiment-sha256:{hashlib.sha256(body).hexdigest()}"
    raw = f"experiment_id: {experiment_id}\n".encode() + body
    return raw, experiment_id, hashlib.sha256(raw).hexdigest()


def _validate_budget(
    value: Any,
    projection: dict[str, Any],
    *,
    live_receipt: dict[str, Any],
    decision_root: str,
    authority_root: str,
    template_root: str,
) -> None:
    required = {
        "budget_identity",
        "reservation_identity",
        "planned_spend",
        "available_unprotected",
        "protected_reserve_used",
        "reservation_state",
    }
    if not isinstance(value, dict) or set(value) != required:
        raise ProvenanceError("routine admission Budget check is incomplete")
    expected_receipt = {
        "contract_version": "frontier-routine-live-receipt/1",
        "slot_id": projection["slot_id"],
        "origin_decision_root": decision_root,
        "origin_authority_root": authority_root,
        "template_root": template_root,
        "budget_identity": value["budget_identity"],
        "reservation_identity": value["reservation_identity"],
        "planned_spend": value["planned_spend"],
        "available_unprotected": value["available_unprotected"],
        "protected_reserve_used": value["protected_reserve_used"],
        "reservation_state": value["reservation_state"],
        "action_window": projection["action_window"],
    }
    if live_receipt != expected_receipt:
        raise ProvenanceError(
            "routine Budget, reservation, or action window differs from its live receipt"
        )
    planned = value["planned_spend"]
    available = value["available_unprotected"]
    if not isinstance(planned, (int, float)) or planned < 0:
        raise ProvenanceError("routine planned spend is invalid")
    if not isinstance(available, (int, float)) or planned > available:
        raise ProvenanceError("routine follow-up exceeds unprotected Budget")
    if value["protected_reserve_used"] is not False:
        raise ProvenanceError("routine follow-up cannot use protected reserve")
    if value["reservation_state"] != "current":
        raise ProvenanceError("routine follow-up reservation is not current")
    boundary = projection.get("budget_boundary")
    if isinstance(boundary, dict):
        ceiling = boundary.get("maximum_spend")
        if isinstance(ceiling, (int, float)) and planned > ceiling:
            raise ProvenanceError("routine follow-up exceeds its Entry Budget ceiling")
