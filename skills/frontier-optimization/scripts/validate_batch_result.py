#!/usr/bin/env python3
"""Validate a Frontier batch result before its immutable path is written."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

from identity_bindings import (
    IdentityBindingError,
    load_file_binding,
    normalize_repo_path,
    reject_symlink_components,
    resolve_repo_file,
)
from finding_effects import add_finding, finalize_findings
from validate_candidate_package import validate_candidate_package
from frontier_provenance.content import ProvenanceError
from frontier_provenance.compatibility import require_v1_completion
from frontier_provenance.facade import verify_for
from frontier_provenance.repository import NodeRepository
from frontier_provenance.stores import PortableBundleStore, ProjectPortableStore
from evaluation_target_contract import (
    DIAGNOSTIC_PROHIBITED_CONSEQUENCES,
    LEGACY_KEYS as EVALUATION_TARGET_LEGACY_KEYS,
    PROHIBITED_RESULT_KEYS as DIAGNOSTIC_PROHIBITED_KEYS,
    ROUTINE_PROHIBITED_RESULT_KEYS,
    validate_evidence_scope,
    validate_experiment_source,
    normalized_nested_keys,
    validate_evaluation_target_contract,
)

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required to validate Frontier batch results") from exc


VALIDATOR = "frontier-batch-result-preflight/7"
IDENTITY_CONTRACT = "frontier-dispatch-identity/2"
SUPPORTED_IDENTITY_CONTRACTS = {IDENTITY_CONTRACT}
RESULT_CONTRACT_V1 = "frontier-batch-result/1"
RESULT_CONTRACT_V2 = "frontier-batch-result/2"
SUPPORTED_RESULT_CONTRACTS = {RESULT_CONTRACT_V1, RESULT_CONTRACT_V2}
ENGINEERING_EVIDENCE_CONTRACT = "frontier-engineering-evidence/1"
ENGINEERING_CHECK_REPORT_CONTRACT = "frontier-engineering-check-report/1"
POST_CHECK_CHARGE = "authoritative-publication-after-engineering-checks"
PROJECT_ACKNOWLEDGMENT_CONTRACT = "frontier-project-batch-acknowledgment/1"
PROJECT_EXECUTION_START_CONTRACT = "frontier-project-execution-start/1"
SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")
SNAPSHOT_ID = re.compile(r"^(?:sha256:|[A-Za-z0-9._-]+-sha256:)[0-9a-f]{64}$")
OUTCOMES = {"completed", "interrupted", "failed", "blocked", "waiting_for_input"}
REQUIRED_FIELDS = {
    "result_packet_path",
    "packet_path",
    "packet_id",
    "packet_preflight",
    "acknowledgment",
    "execution_start",
    "batch_id",
    "campaign_generation",
    "route_id",
    "parallel_set",
    "work_kind",
    "problem_epoch",
    "representation_revision",
    "result_contract_version",
    "workflow_source_identity",
    "started_at",
    "ended_at",
    "outcome",
    "changes_executable_candidate",
    "planned_spend",
    "actual_spend",
    "accounting_evidence",
    "artifacts",
    "work_plan",
    "design_review",
    "development_authorization",
    "design_inputs_used",
    "source_base_identity",
    "source_result_identity",
    "changed_paths",
    "resolved_configuration_identity",
    "dependency_identity",
    "materialization_state",
    "performance_evaluation_state",
    "integration_state",
    "work_plan_progress",
    "design_change_proposals",
    "recovery_point",
    "human_input_state",
    "human_input_artifacts",
    "human_input_validation",
    "human_input_evidence_limit",
    "engineering_validation",
    "implementation_definition_of_done",
    "results",
    "observed_vs_expected",
    "decision_relevant_surprises",
    "failed_checks",
    "new_prerequisites",
    "possible_follow_up",
    "scope_deviation",
}
MATERIALIZATION_BINDING_FIELDS = {
    "candidate_manifest",
    "candidate_identity",
    "experiment_identity",
    "implementation_review_state",
}
EXPERIMENT_LEGACY_BINDING_FIELDS = MATERIALIZATION_BINDING_FIELDS
LIST_FIELDS = {
    "artifacts",
    "design_inputs_used",
    "changed_paths",
    "design_change_proposals",
    "human_input_artifacts",
    "human_input_validation",
    "engineering_validation",
    "results",
    "decision_relevant_surprises",
    "failed_checks",
    "new_prerequisites",
}


def command_sha256(command: Any) -> str | None:
    if not isinstance(command, list) or not command or not all(
        isinstance(part, str) and part for part in command
    ):
        return None
    canonical = json.dumps(
        command,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()
PACKET_BINDINGS = {
    "packet_path": "packet_path",
    "packet_id": "packet_id",
    "batch_id": "batch_id",
    "campaign_generation": "campaign_generation",
    "route_id": "route_id",
    "parallel_set": "parallel_set",
    "work_kind": "work_kind",
    "problem_epoch": "problem_epoch",
    "representation_revision": "representation_revision",
    "result_contract_version": "result_contract_version",
    "workflow_source_identity": "workflow_source_identity",
    "changes_executable_candidate": "changes_executable_candidate",
    "result_packet_path": "result_packet_path",
}


def canonical_payload(document: dict[str, Any]) -> bytes:
    payload = dict(document)
    payload.pop("result_packet_id", None)
    return yaml.safe_dump(payload, sort_keys=False, allow_unicode=True).encode()


def computed_result_id(document: dict[str, Any], digest: str) -> str:
    return f"{document.get('batch_id', 'UNKNOWN')}-result-sha256:{digest}"


def validate_packet_bindings(
    document: dict[str, Any], packet: dict[str, Any] | None, findings: list[dict[str, str]]
) -> None:
    if packet is None:
        return
    for result_field, packet_field in PACKET_BINDINGS.items():
        if document.get(result_field) != packet.get(packet_field):
            add_finding(
                findings,
                "PACKET_BINDING_MISMATCH",
                f"result {result_field} {document.get(result_field)!r} does not match packet {packet_field} {packet.get(packet_field)!r}",
            )


def load_baseline_tool() -> Any:
    path = Path(__file__).with_name("freeze_execution_baseline.py")
    spec = importlib.util.spec_from_file_location(
        "_frontier_execution_baseline_for_result", path
    )
    if spec is None or spec.loader is None:  # pragma: no cover
        raise RuntimeError(f"cannot load execution baseline verifier from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def omitted_line_identity(raw: bytes, field: str, prefix: str) -> str:
    """Recompute an exact-byte identity whose one top-level field line is omitted."""

    pattern = re.compile(
        rb"^" + re.escape(field.encode("ascii")) + rb":[^\r\n]*(?:\r?\n|$)"
    )
    lines = raw.splitlines(keepends=True)
    matches = [index for index, line in enumerate(lines) if pattern.fullmatch(line)]
    if len(matches) != 1:
        raise ValueError(f"{field} must appear as exactly one complete top-level line")
    payload = b"".join(line for index, line in enumerate(lines) if index != matches[0])
    return f"{prefix}{hashlib.sha256(payload).hexdigest()}"


def require_file_sha256(path: Path, expected: Any, role: str) -> bytes:
    if not isinstance(expected, str) or not SHA256_HEX.fullmatch(expected):
        raise ValueError(f"{role} requires one lowercase SHA-256 digest")
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"{role} is missing or unsafe")
    raw = path.read_bytes()
    observed = hashlib.sha256(raw).hexdigest()
    if observed != expected:
        raise ValueError(
            f"{role} SHA-256 mismatch: declared {expected}, observed {observed}"
        )
    return raw


def resolve_project_directory(repo_root: Path, value: Any, role: str) -> tuple[str, Path]:
    try:
        relative = normalize_repo_path(value, role)
        reject_symlink_components(repo_root.resolve(), relative, role)
    except IdentityBindingError as exc:
        raise ValueError(str(exc)) from exc
    candidate = repo_root.resolve() / relative
    resolved = candidate.resolve()
    try:
        observed_relative = resolved.relative_to(repo_root.resolve()).as_posix()
    except ValueError as exc:
        raise ValueError(f"{role} resolves outside the repository") from exc
    if observed_relative != relative or not resolved.is_dir() or candidate.is_symlink():
        raise ValueError(f"{role} is missing, unsafe, or noncanonical")
    return relative, resolved


def verify_project_nested_dispatch(
    *,
    document: dict[str, Any],
    packet: dict[str, Any],
    preflight: Any,
    acknowledgment: Any,
    execution_start: Any,
    repo_root: Path,
) -> None:
    """Verify the frozen project-only dispatch form without rewriting it.

    This compatibility path accepts no inferred authority. Every recovered edge must
    be present as an exact path, embedded identity, and raw-file digest, or must be a
    typed provenance edge whose content root is independently reproducible.
    """

    ack = acknowledgment.document
    start = execution_start.document
    if not isinstance(ack, dict) or not isinstance(start, dict):
        raise ValueError("project dispatch records must contain mappings")
    if (
        ack.get("contract_version") != PROJECT_ACKNOWLEDGMENT_CONTRACT
        or start.get("contract_version") != PROJECT_EXECUTION_START_CONTRACT
    ):
        raise ValueError("project dispatch compatibility requires both exact contracts")
    batch_id = packet.get("batch_id")
    if not isinstance(batch_id, str) or not batch_id:
        raise ValueError("project dispatch packet requires batch_id")
    expected_ack_id = omitted_line_identity(
        acknowledgment.raw,
        "acknowledgment_id",
        f"{batch_id}-acknowledgment-sha256:",
    )
    expected_start_id = omitted_line_identity(
        execution_start.raw,
        "execution_start_id",
        f"{batch_id}-execution-start-sha256:",
    )
    if acknowledgment.identity != expected_ack_id or execution_start.identity != expected_start_id:
        raise ValueError("project dispatch self-identity does not derive from exact bytes")

    packet_relative, packet_path = resolve_repo_file(
        repo_root, document.get("packet_path"), "packet_path"
    )
    packet_raw = packet_path.read_bytes()
    if read_yaml(packet_path, "project packet") != packet:
        raise ValueError("project dispatch packet bytes differ from the supplied packet")
    packet_payload = dict(packet)
    packet_payload.pop("packet_id", None)
    packet_payload_sha256 = hashlib.sha256(
        yaml.safe_dump(packet_payload, sort_keys=False, allow_unicode=True).encode()
    ).hexdigest()
    expected_packet_id = f"{batch_id}-packet-sha256:{packet_payload_sha256}"
    if packet.get("packet_id") != expected_packet_id:
        raise ValueError("project packet identity does not derive from canonical packet bytes")

    plan_binding = ack.get("batch_plan")
    ack_preflight = ack.get("packet_preflight")
    if not isinstance(plan_binding, dict) or set(plan_binding) != {
        "path",
        "packet_id",
        "file_sha256",
    }:
        raise ValueError("project acknowledgment batch_plan binding is incomplete")
    if not isinstance(ack_preflight, dict) or set(ack_preflight) != {
        "path",
        "preflight_id",
        "file_sha256",
    }:
        raise ValueError("project acknowledgment packet_preflight binding is incomplete")
    if (
        plan_binding.get("path") != packet_relative
        or plan_binding.get("packet_id") != packet.get("packet_id")
        or plan_binding.get("file_sha256") != hashlib.sha256(packet_raw).hexdigest()
    ):
        raise ValueError("project acknowledgment does not bind the exact packet bytes")
    if (
        ack_preflight.get("path") != preflight.relative_path
        or ack_preflight.get("preflight_id") != preflight.identity
        or ack_preflight.get("file_sha256") != preflight.file_sha256
    ):
        raise ValueError("project acknowledgment does not bind the exact preflight bytes")
    preflight_document = preflight.document
    if not isinstance(preflight_document, dict):
        raise ValueError("project packet preflight must contain a mapping")
    preflight_payload = dict(preflight_document)
    declared_preflight_id = preflight_payload.pop("preflight_id", None)
    expected_preflight_id = (
        f"{batch_id}-packet-preflight-sha256:"
        + hashlib.sha256(
            json.dumps(
                preflight_payload,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            ).encode()
        ).hexdigest()
    )
    if (
        declared_preflight_id != expected_preflight_id
        or preflight.identity != expected_preflight_id
        or preflight_document.get("computed_packet_id") != packet.get("packet_id")
        or preflight_document.get("packet_payload_sha256") != packet_payload_sha256
        or preflight_document.get("packet_structure_ready") is not True
        or preflight_document.get("blocking_findings") != []
        or preflight_document.get("repair_findings") != []
    ):
        raise ValueError("project packet preflight is not exact and finding-free")

    expected_start_values = {
        "batch_id": batch_id,
        "campaign_generation": packet.get("campaign_generation"),
        "plan_id": packet.get("packet_id"),
        "acknowledgment_id": acknowledgment.identity,
        "candidate_root": packet.get("candidate_root_path"),
        "result_validation": packet.get("result_validation_path"),
        "result": packet.get("result_packet_path"),
    }
    for field, expected in expected_start_values.items():
        if start.get(field) != expected:
            raise ValueError(f"project execution-start {field} does not bind the packet")
    if start.get("worker_may_start") is not True:
        raise ValueError("project execution-start did not release the worker")
    if ack.get("batch_id") != batch_id or ack.get("acknowledgment") != "accepted":
        raise ValueError("project acknowledgment is not accepted for this batch")
    if ack.get("decision_root") != start.get("decision_root"):
        raise ValueError("project acknowledgment and execution-start bind different decisions")

    verification_binding = start.get("execution_verification")
    if not isinstance(verification_binding, dict) or set(verification_binding) != {
        "path",
        "file_sha256",
        "ready",
        "unresolved_live_facts",
    }:
        raise ValueError("project execution verification binding is incomplete")
    verification_relative, verification_path = resolve_repo_file(
        repo_root,
        verification_binding.get("path"),
        "execution_verification.path",
    )
    verification_raw = require_file_sha256(
        verification_path,
        verification_binding.get("file_sha256"),
        "execution verification",
    )
    try:
        verification_document = json.loads(verification_raw)
    except json.JSONDecodeError as exc:
        raise ValueError("execution verification is not valid JSON") from exc
    if (
        verification_binding.get("ready") is not True
        or verification_binding.get("unresolved_live_facts") != []
        or verification_document.get("ready") is not True
        or verification_document.get("unresolved_live_facts") != []
        or verification_document.get("static_chain_verified") is not True
        or verification_document.get("root_id") != start.get("execution_node")
        or verification_document.get("consequence") != "execution"
    ):
        raise ValueError("project execution verification is not exact and finding-free")
    if verification_relative != verification_binding.get("path"):
        raise ValueError("execution verification path is noncanonical")

    decision_content = ack.get("decision_content")
    authority_content = ack.get("authority")
    entry_review = ack.get("entry_review")
    if not isinstance(decision_content, dict) or not isinstance(authority_content, dict):
        raise ValueError("project dispatch content bindings are incomplete")
    if not isinstance(entry_review, dict):
        raise ValueError("project dispatch Entry review binding is incomplete")
    _, decision_bundle = resolve_project_directory(
        repo_root, decision_content.get("path"), "decision_content.path"
    )
    _, authority_bundle = resolve_project_directory(
        repo_root, authority_content.get("content_path"), "authority.content_path"
    )
    _, execution_bundle = resolve_project_directory(
        repo_root, packet.get("execution_baseline_root"), "execution_baseline_root"
    )
    decision_result = ProjectPortableStore().verify(decision_bundle, expected_role="decision")
    authority_result = ProjectPortableStore().verify(authority_bundle, expected_role="authority")
    execution_result = ProjectPortableStore().verify(execution_bundle, expected_role="state")
    if (
        decision_result.get("content_root") != decision_content.get("root")
        or decision_result.get("content_root") != ack.get("decision_content", {}).get("root")
        or authority_result.get("content_root") != authority_content.get("content_root")
        or execution_result.get("content_root") != start.get("starting_state_root")
        or decision_result.get("review_subject", {}).get("subject_mode") != "complete"
    ):
        raise ValueError("project dispatch portable content roots do not match the records")
    require_file_sha256(
        decision_bundle / "manifest.json",
        decision_content.get("manifest_file_sha256"),
        "decision content manifest",
    )
    require_file_sha256(
        authority_bundle / "manifest.json",
        authority_content.get("content_manifest_sha256"),
        "authority content manifest",
    )

    entry_relative, entry_path = resolve_repo_file(
        repo_root, entry_review.get("path"), "entry_review.path"
    )
    require_file_sha256(
        entry_path, entry_review.get("file_sha256"), "Entry review"
    )
    if entry_review.get("result") != "AUTHORIZATION_READY":
        raise ValueError("project dispatch Entry review is not authorization-ready")
    review_bundle_name = f"{Path(entry_relative).stem}-review-report"
    review_bundle = entry_path.parent / review_bundle_name
    if not review_bundle.is_dir() or review_bundle.is_symlink():
        raise ValueError("project dispatch review-report bundle is missing or unsafe")
    review_result = ProjectPortableStore().verify(review_bundle, expected_role="review")

    nodes_root = decision_bundle.parent / "nodes"
    repository = NodeRepository(nodes_root)
    decision_id = start.get("decision_root")
    attestation_id = ack.get("entry_attestation")
    authority_id = start.get("authority_id")
    execution_id = start.get("execution_node")
    decision_node = repository.load(decision_id)
    attestation_node = repository.load(attestation_id)
    authority_node = repository.load(authority_id)
    execution_node = repository.load(execution_id)
    if (
        ack.get("decision_root") != decision_id
        or authority_content.get("node") != authority_id
        or authority_node.get("parents")
        != [
            {"edge": "attestation", "node_id": attestation_id},
            {"edge": "decision", "node_id": decision_id},
        ]
        or execution_node.get("parents")
        != [{"edge": "authority", "node_id": authority_id}]
        or decision_node.get("artifact_roots") != [decision_result["content_root"]]
        or attestation_node.get("artifact_roots") != [review_result["content_root"]]
        or authority_node.get("artifact_roots") != [authority_result["content_root"]]
        or execution_node.get("artifact_roots") != [execution_result["content_root"]]
    ):
        raise ValueError("project dispatch typed provenance edges do not match")
    resolved = {
        decision_result["content_root"]: decision_result,
        review_result["content_root"]: review_result,
        authority_result["content_root"]: authority_result,
        execution_result["content_root"]: execution_result,
    }
    audit = verify_for(
        execution_id,
        repository.load,
        lambda root: resolved[root],
        consequence="audit",
    )
    if audit.get("ready") is not True or audit.get("static_chain_verified") is not True:
        raise ValueError("project execution provenance did not verify")

    baseline_raw = PortableBundleStore().read_artifacts(execution_bundle)
    exact_baseline_members = {
        "project/state/plan.yaml": packet_raw,
        "project/state/preflight.json": preflight.raw,
        "project/state/acknowledgment.yaml": acknowledgment.raw,
    }
    for logical_name, expected_raw in exact_baseline_members.items():
        if baseline_raw.get(logical_name) != expected_raw:
            raise ValueError(
                f"project execution baseline does not preserve exact {logical_name} bytes"
            )
    state_raw = baseline_raw.get("project/state/execution-state.yaml")
    try:
        state = yaml.safe_load(state_raw)
    except (TypeError, yaml.YAMLError) as exc:
        raise ValueError("project execution-state evidence is unreadable") from exc
    if not isinstance(state, dict) or (
        state.get("decision_root") != decision_id
        or state.get("authority_id") != authority_id
        or state.get("acknowledgment", {}).get("identity") != acknowledgment.identity
        or state.get("plan", {}).get("identity") != packet.get("packet_id")
        or state.get("worker_may_start") is not False
        or state.get("release_condition")
        != "exact execution-start.yaml with finding-free execution verification"
    ):
        raise ValueError("project execution-state evidence does not bind the dispatch chain")


def validate_dispatch_bindings(
    document: dict[str, Any],
    packet: dict[str, Any] | None,
    repo_root: Path | None,
    findings: list[dict[str, str]],
) -> None:
    if not isinstance(packet, dict) or packet.get("identity_contract") not in SUPPORTED_IDENTITY_CONTRACTS:
        return
    if repo_root is None:
        add_finding(
            findings,
            "DISPATCH_CHAIN_UNVERIFIED",
            "new result publication requires repo_root to verify the dispatch chain",
        )
        return
    try:
        preflight = load_file_binding(
            repo_root,
            document.get("packet_preflight"),
            "packet_preflight",
            expected_identity_field="preflight_id",
        )
        acknowledgment = load_file_binding(
            repo_root,
            document.get("acknowledgment"),
            "acknowledgment",
            expected_identity_field="acknowledgment_id",
        )
        execution_start = load_file_binding(
            repo_root,
            document.get("execution_start"),
            "execution_start",
            expected_identity_field="execution_start_id",
        )
    except IdentityBindingError as exc:
        add_finding(findings, "DISPATCH_CHAIN_BINDING_INVALID", str(exc))
        return
    if execution_start.document is None:
        add_finding(
            findings,
            "DISPATCH_CHAIN_BINDING_INVALID",
            "execution_start must contain a mapping",
        )
        return
    start = execution_start.document
    project_dispatch = (
        acknowledgment.document is not None
        and acknowledgment.document.get("contract_version")
        == PROJECT_ACKNOWLEDGMENT_CONTRACT
    ) or start.get("contract_version") == PROJECT_EXECUTION_START_CONTRACT
    if project_dispatch:
        try:
            verify_project_nested_dispatch(
                document=document,
                packet=packet,
                preflight=preflight,
                acknowledgment=acknowledgment,
                execution_start=execution_start,
                repo_root=repo_root,
            )
        except (KeyError, OSError, ValueError, yaml.YAMLError, ProvenanceError) as exc:
            add_finding(findings, "PROJECT_DISPATCH_RECOVERY_FAILED", str(exc))
        return
    if start.get("packet_id") != packet.get("packet_id"):
        add_finding(
            findings,
            "DISPATCH_CHAIN_MISMATCH",
            "execution-start binds a different packet",
        )
    if start.get("packet_preflight") != document.get("packet_preflight"):
        add_finding(
            findings,
            "DISPATCH_CHAIN_MISMATCH",
            "result and execution-start bind different packet preflights",
        )
    if start.get("acknowledgment") != document.get("acknowledgment"):
        add_finding(
            findings,
            "DISPATCH_CHAIN_MISMATCH",
            "result and execution-start bind different acknowledgments",
        )
    if acknowledgment.document is not None and (
        acknowledgment.document.get("packet_preflight_id") != preflight.identity
        or acknowledgment.document.get("packet_id") != packet.get("packet_id")
    ):
        add_finding(
            findings,
            "DISPATCH_CHAIN_MISMATCH",
            "acknowledgment does not bind the result packet and preflight",
        )
    try:
        verification = load_baseline_tool().verify(
            execution_start.path, repo_root.resolve(), True
        )
        if verification.get("execution_start_id") != execution_start.identity:
            raise ValueError("execution-start verifier returned a different identity")
        authority_root = (
            start.get("execution_authority", {}).get("record", {}).get("identity")
        )
        inventory = read_yaml(
            repo_root / ".frontier/provenance-rollout.yaml",
            "v1 rollout inventory",
        )
        require_v1_completion(
            inventory,
            authority_root=authority_root,
            requested_descendant="outcome",
            scope_root=packet.get("packet_id"),
            verified_parent_role="execution",
        )
    except (OSError, ValueError, yaml.YAMLError, ProvenanceError) as exc:
        add_finding(findings, "EXECUTION_START_RECOMPUTATION_FAILED", str(exc))


def build_experiment_result_contract_probe(packet: dict[str, Any]) -> dict[str, Any]:
    """Build a complete non-authoritative result draft for packet preflight."""
    target = packet.get("evaluation_target")
    diagnostic = isinstance(target, dict) and target.get("mode") == "diagnostic-only"
    routine = isinstance(target, dict) and target.get("mode") == "routine-local"
    probe = {
        "result_packet_path": packet.get("result_packet_path"),
        "packet_path": packet.get("packet_path"),
        "packet_id": packet.get("packet_id"),
        "packet_preflight": "contract-probe",
        "acknowledgment": "contract-probe",
        "execution_start": "contract-probe",
        "batch_id": packet.get("batch_id"),
        "campaign_generation": packet.get("campaign_generation"),
        "route_id": packet.get("route_id"),
        "parallel_set": packet.get("parallel_set"),
        "work_kind": packet.get("work_kind"),
        "problem_epoch": packet.get("problem_epoch"),
        "representation_revision": packet.get("representation_revision"),
        "result_contract_version": packet.get("result_contract_version"),
        "workflow_source_identity": (
            packet.get("workflow_source_binding", {})
            .get("source_snapshot", {})
            .get("identity")
        ),
        "started_at": "contract-probe",
        "ended_at": "contract-probe",
        "outcome": "completed",
        "changes_executable_candidate": packet.get("changes_executable_candidate"),
        "planned_spend": "contract-probe",
        "actual_spend": "contract-probe",
        "accounting_evidence": "contract-probe",
        "artifacts": [],
        "work_plan": None,
        "design_review": None,
        "development_authorization": None,
        "design_inputs_used": [],
        "source_base_identity": packet.get("source_base_identity"),
        "source_result_identity": None,
        "changed_paths": [],
        "resolved_configuration_identity": None,
        "dependency_identity": None,
        "evaluation_target": target,
        "materialization_state": "not-applicable",
        "performance_evaluation_state": (
            "diagnostic-only under cited Entry authority"
            if diagnostic
            else "routine-local under the pre-authorized single-use slot"
            if routine
            else "performed under cited IMPLEMENTATION_READY and Slot H measurement authority"
        ),
        "integration_state": "not-authorized" if diagnostic or routine else "not-performed",
        "work_plan_progress": None,
        "design_change_proposals": [],
        "recovery_point": "contract-probe",
        "human_input_state": "not-applicable",
        "human_input_artifacts": [],
        "human_input_validation": [],
        "human_input_evidence_limit": "not applicable",
        "engineering_validation": [],
        "implementation_definition_of_done": "not_applicable",
        "results": [
            {
                "contract_probe": True,
                **(
                    {
                        "maximum_consequence": "B evidence only",
                        **(
                            {"evidence_scope": target.get("evidence_scope")}
                            if routine
                            else {}
                        ),
                    }
                    if diagnostic or routine
                    else {}
                ),
            }
        ],
        "observed_vs_expected": "contract-probe",
        "decision_relevant_surprises": [],
        "failed_checks": [],
        "new_prerequisites": [],
        "possible_follow_up": None,
        "scope_deviation": "None",
    }
    if isinstance(target, dict) and isinstance(target.get("evidence_reuse"), dict):
        probe["actual_spend"] = "0 new measurement spend"
        probe["evidence_reuse_accounting"] = {
            "new_measurement_executions": 0,
            "reruns": 0,
            "new_measurement_spend": 0,
        }
    return probe


def validate_packet_result_contract(
    packet: dict[str, Any], repo_root: Path | None = None
) -> dict[str, Any]:
    """Check before authorization that a packet can produce a valid result draft."""
    findings: list[dict[str, str]] = []
    probe_validation_id: str | None = None
    if packet.get("work_kind") == "experiment":
        target = packet.get("evaluation_target")
        if (
            isinstance(target, dict)
            and target.get("mode") == "routine-local"
            and packet.get("result_contract_version") != "frontier-batch-result/2"
        ):
            add_finding(
                findings,
                "ROUTINE_RESULT_CONTRACT_INVALID",
                "routine-local packet must use frontier-batch-result/2",
            )
        probe_validation = validate(
            build_experiment_result_contract_probe(packet),
            "draft",
            packet,
            repo_root=repo_root,
            check_dispatch=False,
        )
        probe_validation_id = probe_validation["validation_id"]
        for finding in probe_validation["findings"]:
            add_finding(findings, finding["code"], finding["detail"])
        for advisory in probe_validation.get("advisories", []):
            add_finding(findings, advisory["code"], advisory["detail"])
    elif packet.get("evaluation_target") is not None:
        add_finding(
            findings,
            "EVALUATION_TARGET_OUTSIDE_EXPERIMENT",
            "evaluation_target must be null outside work_kind: experiment",
        )
    validate_evaluation_target_sources(packet, repo_root, findings)
    finding_summary = finalize_findings(findings)
    return {
        "validator": VALIDATOR,
        "result_contract_ready": finding_summary["ready"],
        "probe_validation_id": probe_validation_id,
        "findings": finding_summary["findings"],
        "blocking_findings": finding_summary["blocking_findings"],
        "repair_findings": finding_summary["repair_findings"],
        "advisories": finding_summary["advisories"],
        "finding_effect_counts": finding_summary["finding_effect_counts"],
    }


def validate_evaluation_target_sources(
    packet: dict[str, Any],
    repo_root: Path | None,
    findings: list[dict[str, str]],
) -> None:
    target = packet.get("evaluation_target")
    if not isinstance(target, dict):
        return
    reuse = target.get("evidence_reuse")
    if repo_root is None:
        if isinstance(reuse, dict):
            add_finding(
                findings,
                "EVIDENCE_REUSE_SOURCE_UNVERIFIED",
                "evidence_reuse requires repo_root to verify every raw artifact byte",
            )
        return
    root = repo_root.resolve()
    bindings: list[tuple[str, Any, Any, str, str, str]] = []
    candidate = target.get("candidate")
    if isinstance(candidate, dict):
        package_validation = validate_candidate_package(
            root,
            candidate.get("root_path"),
            candidate.get("manifest_path"),
            expected_candidate_id=candidate.get("id"),
            expected_manifest_sha256=candidate.get("manifest_sha256"),
        )
        for finding in package_validation["findings"]:
            add_finding(
                findings,
                "EVALUATION_CANDIDATE_PACKAGE_INVALID",
                f"{finding['code']}: {finding['detail']}",
            )
        bindings.append(
            (
                "candidate manifest",
                candidate.get("manifest_path"),
                candidate.get("manifest_sha256"),
                "EVALUATION_TARGET_SOURCE_UNVERIFIED",
                "EVALUATION_TARGET_SOURCE_IDENTITY_MISMATCH",
                "candidate.manifest_path",
            )
        )
    experiment = target.get("experiment")
    if isinstance(experiment, dict):
        bindings.append(
            (
                "experiment contract",
                experiment.get("path"),
                experiment.get("file_sha256"),
                "EVALUATION_TARGET_SOURCE_UNVERIFIED",
                "EVALUATION_TARGET_SOURCE_IDENTITY_MISMATCH",
                "experiment.path",
            )
        )
    for key, label in (
        ("implementation_review", "implementation review"),
        ("slot_h_contract", "Slot H contract"),
    ):
        binding = target.get(key)
        if isinstance(binding, dict):
            bindings.append(
                (
                    label,
                    binding.get("path"),
                    binding.get("file_sha256"),
                    "EVALUATION_TARGET_SOURCE_UNVERIFIED",
                    "EVALUATION_TARGET_SOURCE_IDENTITY_MISMATCH",
                    f"{key}.path",
                )
            )
    if isinstance(reuse, dict) and isinstance(reuse.get("raw_artifacts"), list):
        for index, artifact in enumerate(reuse["raw_artifacts"]):
            if isinstance(artifact, dict):
                bindings.append(
                    (
                        f"evidence_reuse raw_artifacts[{index}]",
                        artifact.get("path"),
                        artifact.get("file_sha256"),
                        "EVIDENCE_REUSE_SOURCE_UNVERIFIED",
                        "EVIDENCE_REUSE_SOURCE_IDENTITY_MISMATCH",
                        f"evidence_reuse.raw_artifacts[{index}].path",
                    )
                )

    for label, relative, expected, unreadable_code, mismatch_code, field in bindings:
        if not isinstance(relative, str) or not isinstance(expected, str):
            continue
        try:
            _, source_path = resolve_repo_file(root, relative, field)
            raw = source_path.read_bytes()
        except (IdentityBindingError, OSError) as exc:
            add_finding(
                findings,
                unreadable_code,
                f"cannot verify evaluation_target {field} {relative}: {exc}",
            )
            continue
        observed = hashlib.sha256(raw).hexdigest()
        if observed != expected.removeprefix("sha256:"):
            add_finding(
                findings,
                mismatch_code,
                f"{label} {relative} has SHA-256 {observed}, expected {expected}",
            )

    if isinstance(experiment, dict) and isinstance(experiment.get("path"), str):
        try:
            relative, path = resolve_repo_file(root, experiment["path"], "experiment.path")
            validate_experiment_source(
                experiment,
                logical_name=relative,
                raw=path.read_bytes(),
                findings=findings,
            )
        except (IdentityBindingError, OSError) as exc:
            add_finding(
                findings,
                "EXPERIMENT_IDENTITY_MISMATCH",
                f"cannot read evaluation_target experiment source: {exc}",
            )


def validate_materialization_boundary(
    document: dict[str, Any], findings: list[dict[str, str]]
) -> None:
    if document.get("changes_executable_candidate") is not True:
        return
    if document.get("work_kind") not in {"code", "mixed"}:
        add_finding(
            findings,
            "CODE_PROFILE_INVALID",
            "changes_executable_candidate: true requires work_kind code or mixed",
        )
    if document.get("results") != []:
        add_finding(
            findings,
            "MATERIALIZATION_RESULTS_NOT_EMPTY",
            "code-bearing materialization requires results: []; candidate information belongs in dedicated fields",
        )
    if document.get("experiment_identity") is not None:
        add_finding(
            findings,
            "MATERIALIZATION_EXPERIMENT_PRESENT",
            "code-bearing materialization requires experiment_identity: null",
        )
    for field in ("performance_evaluation_state", "integration_state"):
        if document.get(field) != "not-authorized":
            add_finding(
                findings,
                "MATERIALIZATION_BOUNDARY_INVALID",
                f"code-bearing materialization requires {field}: not-authorized",
            )
    if document.get("materialization_state") == "materialized-stopped":
        if document.get("implementation_review_state") != "pending":
            add_finding(
                findings,
                "IMPLEMENTATION_REVIEW_STATE_INVALID",
                "materialized-stopped result requires implementation_review_state: pending",
            )
        for field in ("candidate_manifest", "candidate_identity", "source_result_identity"):
            if document.get(field) is None or document.get(field) == "":
                add_finding(
                    findings,
                    "MATERIALIZED_CANDIDATE_FIELD_MISSING",
                    f"materialized-stopped result requires {field}",
                )


def validate_materialized_candidate_sources(
    document: dict[str, Any],
    packet: dict[str, Any] | None,
    repo_root: Path | None,
    findings: list[dict[str, str]],
) -> None:
    if (
        document.get("changes_executable_candidate") is not True
        or document.get("materialization_state") != "materialized-stopped"
    ):
        return
    if not isinstance(packet, dict) or repo_root is None:
        return
    if document.get("candidate_manifest") != packet.get("candidate_manifest_path"):
        add_finding(
            findings,
            "MATERIALIZED_CANDIDATE_BINDING_MISMATCH",
            "result candidate_manifest must equal packet candidate_manifest_path",
        )
        return
    package_validation = validate_candidate_package(
        repo_root,
        packet.get("candidate_root_path"),
        packet.get("candidate_manifest_path"),
        expected_candidate_id=document.get("candidate_identity"),
        expected_workflow_source_identity=document.get("workflow_source_identity"),
        require_final_manifest=True,
        prohibited_downstream_paths=tuple(
            path
            for path in (
                packet.get("result_validation_path"),
                packet.get("result_packet_path"),
            )
            if isinstance(path, str)
        ),
    )
    for finding in package_validation["findings"]:
        add_finding(
            findings,
            "MATERIALIZED_CANDIDATE_PACKAGE_INVALID",
            f"{finding['code']}: {finding['detail']}",
        )


def validate_prepublication_engineering_evidence(
    document: dict[str, Any],
    packet: dict[str, Any] | None,
    repo_root: Path | None,
    findings: list[dict[str, str]],
) -> None:
    if not isinstance(packet, dict):
        return
    policy = packet.get("publication_policy")
    if not isinstance(policy, dict) or policy.get("charge_event") != POST_CHECK_CHARGE:
        return
    validation_items = document.get("engineering_validation")
    bindings = [
        item
        for item in validation_items
        if isinstance(item, dict)
        and item.get("contract_version") == ENGINEERING_EVIDENCE_CONTRACT
    ] if isinstance(validation_items, list) else []
    if len(bindings) != 1:
        add_finding(
            findings,
            "PREPUBLICATION_EVIDENCE_BINDING_INVALID",
            "post-check publication requires exactly one frontier-engineering-evidence/1 binding in engineering_validation",
        )
        return
    binding = bindings[0]
    if set(binding) != {"contract_version", "path", "file_sha256"}:
        add_finding(
            findings,
            "PREPUBLICATION_EVIDENCE_BINDING_INVALID",
            "engineering evidence binding must contain exactly contract_version, path, and file_sha256",
        )
        return
    evidence_path = binding.get("path")
    expected_digest = binding.get("file_sha256")
    if evidence_path != policy.get("engineering_evidence_path"):
        add_finding(
            findings,
            "PREPUBLICATION_EVIDENCE_BINDING_INVALID",
            "engineering evidence path must equal publication_policy.engineering_evidence_path",
        )
    if repo_root is None:
        add_finding(
            findings,
            "PREPUBLICATION_EVIDENCE_UNVERIFIED",
            "post-check publication requires repo_root to verify engineering evidence",
        )
        return
    if not isinstance(evidence_path, str) or not isinstance(expected_digest, str) or not SHA256_HEX.fullmatch(expected_digest):
        add_finding(
            findings,
            "PREPUBLICATION_EVIDENCE_BINDING_INVALID",
            "engineering evidence binding requires a project path and lowercase SHA-256",
        )
        return
    try:
        _, path = resolve_repo_file(repo_root, evidence_path, "engineering_validation.path")
        raw = path.read_bytes()
        evidence = yaml.safe_load(raw)
    except (IdentityBindingError, OSError, yaml.YAMLError) as exc:
        add_finding(
            findings,
            "PREPUBLICATION_EVIDENCE_UNVERIFIED",
            f"cannot read engineering evidence: {exc}",
        )
        return
    observed_digest = hashlib.sha256(raw).hexdigest()
    if observed_digest != expected_digest:
        add_finding(
            findings,
            "PREPUBLICATION_EVIDENCE_DIGEST_MISMATCH",
            f"engineering evidence has SHA-256 {observed_digest}, expected {expected_digest}",
        )
    if not isinstance(evidence, dict) or evidence.get("contract_version") != ENGINEERING_EVIDENCE_CONTRACT:
        add_finding(
            findings,
            "PREPUBLICATION_EVIDENCE_INVALID",
            f"engineering evidence must use {ENGINEERING_EVIDENCE_CONTRACT}",
        )
        return
    if evidence.get("evidence_use") != "engineering-only":
        add_finding(
            findings,
            "PREPUBLICATION_EVIDENCE_INVALID",
            "engineering evidence must remain engineering-only",
        )
    expected_policy = {
        "charge_event": POST_CHECK_CHARGE,
        "charge_amount": policy.get("charge_amount"),
        "authoritative_output_path": policy.get("authoritative_output_path"),
    }
    if evidence.get("publication_policy") != expected_policy:
        add_finding(
            findings,
            "PREPUBLICATION_POLICY_MISMATCH",
            "engineering evidence must copy the packet charge event and authoritative output path exactly",
        )
    plan = packet.get("engineering_check_plan")
    limits = plan.get("effect_limits") if isinstance(plan, dict) else None
    planned_checks = plan.get("checks") if isinstance(plan, dict) else None
    planned_check_ids = [
        check.get("id")
        for check in planned_checks
        if isinstance(check, dict) and isinstance(check.get("id"), str)
    ] if isinstance(planned_checks, list) else []
    planned_checks_by_id = {
        check["id"]: check
        for check in planned_checks
        if isinstance(check, dict) and isinstance(check.get("id"), str)
    } if isinstance(planned_checks, list) else {}
    if (
        not isinstance(planned_checks, list)
        or not planned_checks
        or len(planned_check_ids) != len(planned_checks)
        or len(planned_check_ids) != len(set(planned_check_ids))
        or any(
            command_sha256(check.get("command")) is None
            or not isinstance(check.get("effect_costs"), dict)
            or not check.get("effect_costs")
            or any(
                not isinstance(effect, str)
                or not isinstance(limits, dict)
                or effect not in limits
                or not isinstance(cost, int)
                or isinstance(cost, bool)
                or cost <= 0
                for effect, cost in check.get("effect_costs", {}).items()
            )
            for check in planned_checks
            if isinstance(check, dict)
        )
    ):
        add_finding(
            findings,
            "PREPUBLICATION_CHECK_PLAN_INVALID",
            "post-check evidence requires a nonempty packet check plan with unique IDs",
        )
        planned_check_ids = []
    if (
        not isinstance(limits, dict)
        or not limits
        or any(
            not isinstance(maximum, int)
            or isinstance(maximum, bool)
            or maximum <= 0
            for maximum in limits.values()
        )
        or evidence.get("effect_limits") != limits
    ):
        add_finding(
            findings,
            "PREPUBLICATION_EFFECT_LIMIT_MISMATCH",
            "engineering evidence effect_limits must equal the packet engineering check plan",
        )
        limits = {}
    attempts = evidence.get("attempts")
    if not isinstance(attempts, list):
        add_finding(
            findings,
            "PREPUBLICATION_ATTEMPTS_INVALID",
            "engineering evidence attempts must be an ordered list",
        )
        attempts = []
    cumulative = {effect: 0 for effect in limits}
    seen_snapshots: set[str] = set()
    pass_positions: list[int] = []
    for index, attempt in enumerate(attempts, start=1):
        expected_fields = {
            "sequence",
            "snapshot_id",
            "snapshot_file_sha256",
            "outcome",
            "checks",
            "check_report",
            "effects",
        }
        if not isinstance(attempt, dict) or set(attempt) != expected_fields:
            add_finding(
                findings,
                "PREPUBLICATION_ATTEMPT_INVALID",
                f"attempt {index} must contain exactly sequence, snapshot_id, snapshot_file_sha256, outcome, checks, check_report, and effects",
            )
            continue
        snapshot_id = attempt.get("snapshot_id")
        sequence = attempt.get("sequence")
        if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence != index:
            add_finding(
                findings,
                "PREPUBLICATION_ATTEMPT_ORDER_INVALID",
                f"attempt {index} must have sequence {index}",
            )
        if not isinstance(snapshot_id, str) or not SNAPSHOT_ID.fullmatch(snapshot_id) or snapshot_id in seen_snapshots:
            add_finding(
                findings,
                "PREPUBLICATION_SNAPSHOT_ID_INVALID",
                f"attempt {index} requires a unique content-addressed snapshot_id",
            )
        else:
            seen_snapshots.add(snapshot_id)
        snapshot_digest = attempt.get("snapshot_file_sha256")
        if not isinstance(snapshot_digest, str) or not SHA256_HEX.fullmatch(snapshot_digest):
            add_finding(
                findings,
                "PREPUBLICATION_SNAPSHOT_ID_INVALID",
                f"attempt {index} requires a lowercase snapshot_file_sha256",
            )
        elif isinstance(snapshot_id, str) and snapshot_id.rsplit(":", 1)[-1] != snapshot_digest:
            add_finding(
                findings,
                "PREPUBLICATION_SNAPSHOT_ID_INVALID",
                f"attempt {index} snapshot_id digest must equal snapshot_file_sha256",
            )
        if attempt.get("outcome") not in {"pass", "fail"}:
            add_finding(
                findings,
                "PREPUBLICATION_ATTEMPT_INVALID",
                f"attempt {index} outcome must be pass or fail",
            )
        elif attempt.get("outcome") == "pass":
            pass_positions.append(index)
        check_results = attempt.get("checks")
        attempt_check_ids: list[str] = []
        if not isinstance(check_results, list):
            add_finding(
                findings,
                "PREPUBLICATION_CHECK_RESULTS_INVALID",
                f"attempt {index} checks must be a list",
            )
            check_results = []
        for check_index, check_result in enumerate(check_results):
            if (
                not isinstance(check_result, dict)
                or set(check_result) != {"id", "result"}
                or not isinstance(check_result.get("id"), str)
                or check_result.get("result") not in {"pass", "fail", "error", "blocked"}
            ):
                add_finding(
                    findings,
                    "PREPUBLICATION_CHECK_RESULTS_INVALID",
                    f"attempt {index} checks[{check_index}] requires an exact plan ID and pass, fail, error, or blocked",
                )
                continue
            attempt_check_ids.append(check_result["id"])
        if len(attempt_check_ids) != len(set(attempt_check_ids)) or not set(attempt_check_ids).issubset(set(planned_check_ids)):
            add_finding(
                findings,
                "PREPUBLICATION_CHECK_RESULTS_INVALID",
                f"attempt {index} check IDs must be a unique subset of the frozen plan",
            )
        report = attempt.get("check_report")
        parsed_report: dict[str, Any] | None = None
        if (
            not isinstance(report, dict)
            or set(report) != {"path", "file_sha256"}
            or not isinstance(report.get("path"), str)
            or not isinstance(report.get("file_sha256"), str)
            or not SHA256_HEX.fullmatch(report["file_sha256"])
        ):
            add_finding(
                findings,
                "PREPUBLICATION_CHECK_REPORT_INVALID",
                f"attempt {index} requires one content-addressed combined check report",
            )
        else:
            try:
                _, report_path = resolve_repo_file(
                    repo_root,
                    report["path"],
                    f"attempts[{index - 1}].check_report.path",
                )
                report_raw = report_path.read_bytes()
                report_digest = hashlib.sha256(report_raw).hexdigest()
                loaded_report = yaml.safe_load(report_raw)
            except (IdentityBindingError, OSError, yaml.YAMLError) as exc:
                add_finding(
                    findings,
                    "PREPUBLICATION_CHECK_REPORT_INVALID",
                    f"cannot verify attempt {index} check report: {exc}",
                )
            else:
                if report_digest != report["file_sha256"]:
                    add_finding(
                        findings,
                        "PREPUBLICATION_CHECK_REPORT_INVALID",
                        f"attempt {index} check report SHA-256 mismatch",
                    )
                elif not isinstance(loaded_report, dict) or set(loaded_report) != {
                    "contract_version",
                    "snapshot_id",
                    "checks",
                }:
                    add_finding(
                        findings,
                        "PREPUBLICATION_CHECK_REPORT_INVALID",
                        f"attempt {index} check report must use the closed {ENGINEERING_CHECK_REPORT_CONTRACT} schema",
                    )
                else:
                    parsed_report = loaded_report
        if parsed_report is not None:
            report_checks = parsed_report.get("checks")
            if (
                parsed_report.get("contract_version") != ENGINEERING_CHECK_REPORT_CONTRACT
                or parsed_report.get("snapshot_id") != snapshot_id
                or not isinstance(report_checks, list)
                or len(report_checks) != len(check_results)
            ):
                add_finding(
                    findings,
                    "PREPUBLICATION_CHECK_REPORT_INVALID",
                    f"attempt {index} check report must bind the attempt snapshot and every reported invocation",
                )
            else:
                for check_index, (reported, summarized) in enumerate(zip(report_checks, check_results)):
                    check_id = summarized.get("id") if isinstance(summarized, dict) else None
                    planned = planned_checks_by_id.get(check_id)
                    expected_argv = command_sha256(planned.get("command")) if isinstance(planned, dict) else None
                    expected_result = summarized.get("result") if isinstance(summarized, dict) else None
                    valid_reported = (
                        isinstance(reported, dict)
                        and set(reported) == {
                            "id",
                            "argv_sha256",
                            "result",
                            "exit_status",
                            "log",
                            "log_sha256",
                        }
                        and reported.get("id") == check_id
                        and reported.get("argv_sha256") == expected_argv
                        and reported.get("result") == expected_result
                        and isinstance(reported.get("log"), str)
                        and bool(reported.get("log"))
                        and reported.get("log_sha256")
                        == hashlib.sha256(reported.get("log", "").encode("utf-8")).hexdigest()
                    )
                    exit_status = reported.get("exit_status") if isinstance(reported, dict) else None
                    if expected_result == "pass":
                        valid_reported = (
                            valid_reported
                            and isinstance(exit_status, int)
                            and not isinstance(exit_status, bool)
                            and exit_status == 0
                        )
                    elif expected_result in {"fail", "error"}:
                        valid_reported = (
                            valid_reported
                            and isinstance(exit_status, int)
                            and not isinstance(exit_status, bool)
                            and exit_status != 0
                        )
                    elif expected_result == "blocked":
                        valid_reported = valid_reported and exit_status is None
                    if not valid_reported:
                        add_finding(
                            findings,
                            "PREPUBLICATION_CHECK_REPORT_INVALID",
                            f"attempt {index} report check {check_index} must match the frozen command, summarized result, exit status, and log digest",
                        )
        full_all_pass = (
            attempt_check_ids == planned_check_ids
            and len(check_results) == len(planned_check_ids)
            and all(
                isinstance(item, dict) and item.get("result") == "pass"
                for item in check_results
            )
        )
        if (attempt.get("outcome") == "pass") != full_all_pass:
            add_finding(
                findings,
                "PREPUBLICATION_ATTEMPT_OUTCOME_INVALID",
                f"attempt {index} outcome must be pass if and only if every frozen check ran in order and passed",
            )
        effects = attempt.get("effects")
        if not isinstance(effects, dict) or set(effects) != set(limits):
            add_finding(
                findings,
                "PREPUBLICATION_EFFECT_ACCOUNTING_INVALID",
                f"attempt {index} effects must contain exactly the packet effect classes",
            )
            continue
        if any(
            not isinstance(value, int)
            or isinstance(value, bool)
            or value < 0
            for value in effects.values()
        ):
            add_finding(
                findings,
                "PREPUBLICATION_EFFECT_ACCOUNTING_INVALID",
                f"attempt {index} effect counts must be nonnegative integers",
            )
        derived_effects = {effect: 0 for effect in limits}
        for check_id in attempt_check_ids:
            planned = planned_checks_by_id.get(check_id)
            effect_costs = planned.get("effect_costs") if isinstance(planned, dict) else None
            if not isinstance(effect_costs, dict):
                add_finding(
                    findings,
                    "PREPUBLICATION_EFFECT_ACCOUNTING_INVALID",
                    f"attempt {index} check {check_id!r} has no frozen per-invocation effect costs",
                )
                continue
            for effect, value in effect_costs.items():
                if effect in derived_effects and isinstance(value, int) and not isinstance(value, bool):
                    derived_effects[effect] += value
        if effects != derived_effects:
            add_finding(
                findings,
                "PREPUBLICATION_EFFECT_ACCOUNTING_INVALID",
                f"attempt {index} effects must be derived from the frozen cost of each reported check invocation",
            )
        for effect, value in derived_effects.items():
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                add_finding(
                    findings,
                    "PREPUBLICATION_EFFECT_ACCOUNTING_INVALID",
                    f"attempt {index} effect {effect!r} must be a nonnegative integer",
                )
                continue
            cumulative[effect] += value
    reported_effects = evidence.get("effects")
    if (
        not isinstance(reported_effects, dict)
        or set(reported_effects) != set(cumulative)
        or any(
            not isinstance(value, int) or isinstance(value, bool) or value < 0
            for value in reported_effects.values()
        )
        or reported_effects != cumulative
    ):
        add_finding(
            findings,
            "PREPUBLICATION_EFFECT_ACCOUNTING_INVALID",
            "engineering evidence effects must equal the sum across every attempt",
        )
    for effect, total in cumulative.items():
        maximum = limits.get(effect)
        if isinstance(maximum, int) and total > maximum:
            add_finding(
                findings,
                "PREPUBLICATION_EFFECT_LIMIT_EXCEEDED",
                f"cumulative effect {effect!r} is {total}, above maximum {maximum}",
            )
    published = document.get("outcome") == "completed"
    official_output = evidence.get("official_output")
    if published:
        if not attempts or pass_positions != [len(attempts)] or evidence.get("status") != "pass":
            add_finding(
                findings,
                "PREPUBLICATION_FINAL_PASS_MISSING",
                "completed post-check publication requires exactly the final attempt to pass",
            )
        if not isinstance(official_output, dict) or set(official_output) != {"path", "file_sha256"}:
            add_finding(
                findings,
                "PREPUBLICATION_OFFICIAL_OUTPUT_INVALID",
                "completed post-check publication requires one official output binding",
            )
            return
        if official_output.get("path") != policy.get("authoritative_output_path"):
            add_finding(
                findings,
                "PREPUBLICATION_OFFICIAL_OUTPUT_INVALID",
                "official output path must equal the packet publication policy",
            )
        final_digest = attempts[-1].get("snapshot_file_sha256") if attempts and isinstance(attempts[-1], dict) else None
        if official_output.get("file_sha256") != final_digest:
            add_finding(
                findings,
                "PREPUBLICATION_FINAL_SNAPSHOT_MISMATCH",
                "official output must be byte-identical to the final passing transient snapshot",
            )
        try:
            _, official_path = resolve_repo_file(
                repo_root,
                official_output.get("path"),
                "official_output.path",
            )
            actual_official_digest = hashlib.sha256(official_path.read_bytes()).hexdigest()
        except (IdentityBindingError, OSError) as exc:
            add_finding(
                findings,
                "PREPUBLICATION_OFFICIAL_OUTPUT_UNVERIFIED",
                f"cannot read official output: {exc}",
            )
        else:
            if actual_official_digest != official_output.get("file_sha256"):
                add_finding(
                    findings,
                    "PREPUBLICATION_FINAL_SNAPSHOT_MISMATCH",
                    "official output bytes do not match the final passing transient snapshot",
                )
    else:
        if pass_positions or evidence.get("status") not in {"fail", "blocked"} or official_output is not None:
            add_finding(
                findings,
                "PREPUBLICATION_TERMINAL_EVIDENCE_INVALID",
                "a non-materialized post-check result must contain no passing attempt or official output",
            )
        output_relative = policy.get("authoritative_output_path")
        if isinstance(output_relative, str):
            output_path = (repo_root.resolve() / output_relative).resolve()
            try:
                output_path.relative_to(repo_root.resolve())
            except ValueError:
                add_finding(
                    findings,
                    "PREPUBLICATION_OFFICIAL_OUTPUT_INVALID",
                    "authoritative output path escapes repo_root",
                )
            else:
                if output_path.exists() or output_path.is_symlink():
                    add_finding(
                        findings,
                        "PREPUBLICATION_TERMINAL_EVIDENCE_INVALID",
                        "a non-materialized post-check result must not leave an authoritative output",
                    )
        if document.get("changes_executable_candidate") is True:
            for field in ("candidate_manifest", "candidate_identity", "source_result_identity"):
                value = document.get(field)
                if value is not None and value != "":
                    add_finding(
                        findings,
                        "PREPUBLICATION_TERMINAL_CANDIDATE_INVALID",
                        f"a failed post-check code result requires {field}: null",
                    )
            manifest_relative = packet.get("candidate_manifest_path")
            if isinstance(manifest_relative, str):
                manifest_path = (repo_root.resolve() / manifest_relative).resolve()
                try:
                    manifest_path.relative_to(repo_root.resolve())
                except ValueError:
                    add_finding(
                        findings,
                        "PREPUBLICATION_TERMINAL_CANDIDATE_INVALID",
                        "candidate manifest path escapes repo_root",
                    )
                else:
                    if manifest_path.exists() or manifest_path.is_symlink():
                        add_finding(
                            findings,
                            "PREPUBLICATION_TERMINAL_CANDIDATE_INVALID",
                            "a failed post-check code result must not leave a final candidate manifest",
                        )


def validate_publication_charge(
    document: dict[str, Any],
    packet: dict[str, Any] | None,
    repo_root: Path | None,
    findings: list[dict[str, str]],
) -> None:
    """Bind either supported publication event to the one official output charge."""
    if (
        not isinstance(packet, dict)
        or document.get("outcome") != "completed"
        or document.get("work_kind") not in {"code", "design", "prototype"}
    ):
        return
    policy = packet.get("publication_policy")
    if not isinstance(policy, dict):
        return
    output_relative = policy.get("authoritative_output_path")
    charge_amount = policy.get("charge_amount")
    if repo_root is None or not isinstance(output_relative, str):
        add_finding(
            findings,
            "PUBLICATION_CHARGE_ACCOUNTING_UNVERIFIED",
            "a current authoritative publication requires repo_root and its policy output path",
        )
        return
    try:
        _, output_path = resolve_repo_file(
            repo_root,
            output_relative,
            "publication_policy.authoritative_output_path",
        )
        output_digest = hashlib.sha256(output_path.read_bytes()).hexdigest()
    except (IdentityBindingError, OSError) as exc:
        add_finding(
            findings,
            "PUBLICATION_CHARGE_ACCOUNTING_UNVERIFIED",
            f"cannot bind publication charge to the official output: {exc}",
        )
        return
    expected_accounting = (
        f"authoritative output {output_relative} sha256:{output_digest}"
    )
    if (
        document.get("planned_spend") != charge_amount
        or document.get("actual_spend") != charge_amount
        or document.get("accounting_evidence") != expected_accounting
    ):
        add_finding(
            findings,
            "PUBLICATION_CHARGE_ACCOUNTING_INVALID",
            "every current authoritative publication must record the policy charge amount and bind it to the official output identity",
        )


def validate_evaluation_boundary(
    document: dict[str, Any],
    packet: dict[str, Any] | None,
    findings: list[dict[str, str]],
) -> None:
    performance_state = str(document.get("performance_evaluation_state", ""))
    if document.get("work_kind") != "experiment":
        if performance_state.startswith(("performed", "diagnostic-only", "routine-local")):
            add_finding(
                findings,
                "PERFORMANCE_RESULT_OUTSIDE_EVALUATION",
                "only a work_kind: experiment result may report performed performance evaluation",
            )
        return
    if document.get("changes_executable_candidate") is not False:
        add_finding(
            findings,
            "EVALUATION_CHANGED_CANDIDATE",
            "Slot H evaluation requires changes_executable_candidate: false",
        )
    if document.get("materialization_state") != "not-applicable":
        add_finding(
            findings,
            "EVALUATION_MATERIALIZATION_STATE_INVALID",
            "Slot H evaluation requires materialization_state: not-applicable",
        )
    evaluation_target = document.get("evaluation_target")
    validate_evaluation_target_contract(evaluation_target, findings)
    packet_target = packet.get("evaluation_target") if packet else None
    if evaluation_target != packet_target:
        add_finding(
            findings,
            "EVALUATION_TARGET_BINDING_MISMATCH",
            "result evaluation_target must exactly equal the packet evaluation_target",
        )
    if not isinstance(evaluation_target, dict):
        evaluation_target = {}
    if isinstance(evaluation_target.get("evidence_reuse"), dict):
        expected_accounting = {
            "new_measurement_executions": 0,
            "reruns": 0,
            "new_measurement_spend": 0,
        }
        if document.get("evidence_reuse_accounting") != expected_accounting:
            add_finding(
                findings,
                "EVIDENCE_REUSE_ACCOUNTING_INVALID",
                "evidence-reuse result requires zero executions, reruns, and new measurement spend",
            )
        if document.get("actual_spend") != "0 new measurement spend":
            add_finding(
                findings,
                "EVIDENCE_REUSE_ACCOUNTING_INVALID",
                "evidence-reuse result requires actual_spend: 0 new measurement spend",
            )
    if evaluation_target.get("mode") in {"diagnostic-only", "routine-local"}:
        bounded_mode = evaluation_target.get("mode")
        if document.get("outcome") == "completed" and not performance_state.startswith(
            bounded_mode
        ):
            add_finding(
                findings,
                "DIAGNOSTIC_PERFORMANCE_STATE_INVALID",
                f"completed {bounded_mode} result must report {bounded_mode} performance state",
            )
        elif document.get("outcome") != "completed" and not performance_state.startswith(
            (bounded_mode, "not-performed", "not-authorized")
        ):
            add_finding(
                findings,
                "DIAGNOSTIC_PERFORMANCE_STATE_INVALID",
                f"non-completed {bounded_mode} result must report its mode, not-performed, or not-authorized state",
            )
        if document.get("integration_state") != "not-authorized":
            add_finding(
                findings,
                "DIAGNOSTIC_INTEGRATION_BOUNDARY_INVALID",
                f"{bounded_mode} evaluation requires integration_state: not-authorized",
            )
        results = document.get("results")
        if performance_state.startswith(bounded_mode) and (
            not isinstance(results, list) or not results
        ):
            add_finding(
                findings,
                "DIAGNOSTIC_RESULTS_MISSING",
                f"{bounded_mode} evaluation requires at least one bounded result",
            )
        if isinstance(results, list):
            for index, result in enumerate(results):
                if not isinstance(result, dict):
                    add_finding(
                        findings,
                        "DIAGNOSTIC_RESULT_INVALID",
                        f"diagnostic result {index} must be a mapping",
                    )
                    continue
                if result.get("maximum_consequence") != "B evidence only":
                    add_finding(
                        findings,
                        "DIAGNOSTIC_RESULT_CONSEQUENCE_MISSING",
                        f"diagnostic result {index} requires maximum_consequence: B evidence only",
                    )
                if bounded_mode == "routine-local":
                    if set(result) != {
                        "observations",
                        "maximum_consequence",
                        "evidence_scope",
                    } or not isinstance(result.get("observations"), list) or not result[
                        "observations"
                    ]:
                        add_finding(
                            findings,
                            "ROUTINE_RESULT_SCHEMA_INVALID",
                            "routine results must contain exactly nonempty structured observations, maximum_consequence, and evidence_scope",
                        )
                    else:
                        for observation_index, observation in enumerate(
                            result["observations"]
                        ):
                            if (
                                not isinstance(observation, dict)
                                or set(observation)
                                != {"metric", "value", "unit", "sample_count"}
                                or not isinstance(observation.get("metric"), str)
                                or not observation["metric"].strip()
                                or not isinstance(observation.get("unit"), str)
                                or not observation["unit"].strip()
                                or not isinstance(observation.get("sample_count"), int)
                                or isinstance(observation.get("sample_count"), bool)
                                or observation["sample_count"] < 1
                                or not isinstance(
                                    observation.get("value"), (int, float, bool)
                                )
                            ):
                                add_finding(
                                    findings,
                                    "ROUTINE_OBSERVATION_INVALID",
                                    f"routine observation {index}.{observation_index} must be one measured scalar with metric, value, unit, and positive sample_count",
                                )
                    validate_evidence_scope(
                        result.get("evidence_scope"),
                        findings,
                        role=f"results[{index}].evidence_scope",
                    )
                    if result.get("evidence_scope") != evaluation_target.get("evidence_scope"):
                        add_finding(
                            findings,
                            "ROUTINE_RESULT_SCOPE_MISMATCH",
                            f"routine result {index} must preserve the packet evidence_scope exactly",
                        )
                    routine_payload = {
                        key: value
                        for key, value in result.items()
                        if key != "evidence_scope"
                    }
                    prohibited_routine_keys = (
                        normalized_nested_keys(routine_payload)
                        & ROUTINE_PROHIBITED_RESULT_KEYS
                    )
                    if prohibited_routine_keys:
                        add_finding(
                            findings,
                            "ROUTINE_RESULT_CLAIM_PRESENT",
                            f"routine result {index} contains claims beyond its structured scope: {sorted(prohibited_routine_keys)}",
                        )
                prohibited_keys = normalized_nested_keys(result) & DIAGNOSTIC_PROHIBITED_KEYS
                if prohibited_keys:
                    add_finding(
                        findings,
                        "DIAGNOSTIC_RESULT_CLAIM_PRESENT",
                        f"diagnostic result {index} contains prohibited consequence fields: {sorted(prohibited_keys)}",
                    )
        if bounded_mode == "routine-local":
            routine_measurement_completed = performance_state.startswith("routine-local")
            if routine_measurement_completed and (
                not isinstance(results, list) or len(results) != 1
            ):
                add_finding(
                    findings,
                    "ROUTINE_RESULT_CONTAINER_INVALID",
                    "a completed routine measurement requires exactly one result container",
                )
            elif not routine_measurement_completed and results != []:
                add_finding(
                    findings,
                    "ROUTINE_RESULT_CONTAINER_INVALID",
                    "a routine action that ended before measurement requires an empty results list",
                )
            sample_count = 0
            for result in results or []:
                if not isinstance(result, dict):
                    continue
                for observation in result.get("observations", []):
                    if not isinstance(observation, dict):
                        continue
                    value = observation.get("value")
                    if isinstance(value, float) and not math.isfinite(value):
                        add_finding(
                            findings,
                            "ROUTINE_OBSERVATION_INVALID",
                            "routine observation values must be finite",
                        )
                    count = observation.get("sample_count")
                    if isinstance(count, int) and not isinstance(count, bool):
                        sample_count = max(sample_count, count)
            sample_ceiling = evaluation_target.get("sample_ceiling", {}).get("runs")
            if not isinstance(sample_ceiling, int) or sample_count > sample_ceiling:
                add_finding(
                    findings,
                    "ROUTINE_SAMPLE_CEILING_EXCEEDED",
                    "routine result sample_count exceeds the Entry-authorized ceiling",
                )
            if document.get("possible_follow_up") is not None:
                add_finding(
                    findings,
                    "ROUTINE_FOLLOW_UP_AUTHORITY_PRESENT",
                    "routine result possible_follow_up must be null; only Reflection and the integrated resolver may choose a next action",
                )
            expected_observation_summary = (
                "recorded in structured routine observations"
                if routine_measurement_completed
                else "no structured routine observation completed"
            )
            if document.get("observed_vs_expected") != expected_observation_summary:
                add_finding(
                    findings,
                    "ROUTINE_RESULT_NARRATIVE_PRESENT",
                    "routine observed_vs_expected must use the exact neutral text for its measurement state",
                )
            if document.get("decision_relevant_surprises") != []:
                add_finding(
                    findings,
                    "ROUTINE_RESULT_NARRATIVE_PRESENT",
                    "routine result surprises must be represented as structured observations for later Reflection",
                )
            neutral_fields = {
                "work_plan_progress": None,
                "design_change_proposals": [],
                "recovery_point": "routine result recorded; no later consequence authorized",
                "engineering_validation": [],
                "new_prerequisites": [],
                "scope_deviation": "None",
            }
            drifted_neutral_fields = sorted(
                field
                for field, expected in neutral_fields.items()
                if document.get(field) != expected
            )
            if drifted_neutral_fields:
                add_finding(
                    findings,
                    "ROUTINE_RESULT_AUTHORITY_LEAKAGE",
                    "routine result must keep generic planning, recovery, validation, prerequisite, and scope fields neutral: "
                    + ", ".join(drifted_neutral_fields),
                )
    elif evaluation_target.get("mode") == "formal-slot-h":
        if document.get("integration_state") not in {"not-performed", "not-authorized"}:
            add_finding(
                findings,
                "FORMAL_EVALUATION_INTEGRATION_INVALID",
                "formal Slot H evaluation result cannot perform integration",
            )
        if document.get("outcome") == "completed" and not performance_state.startswith(
            "performed"
        ):
            add_finding(
                findings,
                "FORMAL_EVALUATION_STATE_INVALID",
                "completed formal Slot H result must report performed performance state",
            )
        elif document.get("outcome") != "completed" and not performance_state.startswith(
            ("performed", "not-performed", "not-authorized")
        ):
            add_finding(
                findings,
                "FORMAL_EVALUATION_STATE_INVALID",
                "non-completed formal result must report performed, not-performed, or not-authorized state",
            )
        if performance_state.startswith("performed") and (
            not isinstance(document.get("results"), list) or not document["results"]
        ):
            add_finding(
                findings,
                "FORMAL_EVALUATION_RESULTS_MISSING",
                "performed formal Slot H result requires at least one measurement result",
            )


def validate(
    document: dict[str, Any],
    phase: str,
    packet: dict[str, Any] | None = None,
    repo_root: Path | None = None,
    check_dispatch: bool = True,
) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    result_contract = document.get("result_contract_version")
    packet_result_contract = (
        packet.get("result_contract_version") if isinstance(packet, dict) else None
    )
    if (
        result_contract not in SUPPORTED_RESULT_CONTRACTS
        or packet_result_contract not in SUPPORTED_RESULT_CONTRACTS
        or result_contract != packet_result_contract
    ):
        add_finding(
            findings,
            "RESULT_CONTRACT_UNSUPPORTED",
            "result and packet must name the same supported versioned result contract",
        )
    if (
        phase != "audit"
        and result_contract != RESULT_CONTRACT_V2
        and (not check_dispatch or repo_root is None)
    ):
        add_finding(
            findings,
            "RESULT_CONTRACT_LEGACY_WRITE_FORBIDDEN",
            f"current result writing requires {RESULT_CONTRACT_V2}",
        )
    for field in sorted(REQUIRED_FIELDS - document.keys()):
        add_finding(findings, "REQUIRED_FIELD_MISSING", field)
    if document.get("work_kind") == "experiment":
        if "evaluation_target" not in document:
            add_finding(findings, "REQUIRED_FIELD_MISSING", "evaluation_target")
        for field in sorted(EXPERIMENT_LEGACY_BINDING_FIELDS & document.keys()):
            add_finding(
                findings,
                "EXPERIMENT_LEGACY_BINDING_PRESENT",
                f"experiment result must use evaluation_target instead of {field}",
            )
    else:
        for field in sorted(MATERIALIZATION_BINDING_FIELDS - document.keys()):
            add_finding(findings, "REQUIRED_FIELD_MISSING", field)
        if document.get("evaluation_target") is not None:
            add_finding(
                findings,
                "EVALUATION_TARGET_OUTSIDE_EXPERIMENT",
                "evaluation_target must be omitted outside work_kind: experiment",
            )
    target = document.get("evaluation_target")
    target_reuses_evidence = isinstance(target, dict) and isinstance(
        target.get("evidence_reuse"), dict
    )
    if "evidence_reuse_accounting" in document and not target_reuses_evidence:
        add_finding(
            findings,
            "EVIDENCE_REUSE_ACCOUNTING_OUTSIDE_RECOVERY",
            "evidence_reuse_accounting must be omitted without evidence_reuse",
        )
    for field in sorted(LIST_FIELDS):
        if field in document and not isinstance(document[field], list):
            add_finding(findings, "LIST_FIELD_INVALID", f"{field} must be a list")
    if document.get("outcome") not in OUTCOMES:
        add_finding(findings, "OUTCOME_INVALID", "outcome is not an allowed batch result")
    generation = document.get("campaign_generation")
    if not isinstance(generation, int) or isinstance(generation, bool) or generation < 1:
        add_finding(
            findings,
            "CAMPAIGN_GENERATION_INVALID",
            "campaign_generation must be a positive integer",
        )
    if not isinstance(document.get("changes_executable_candidate"), bool):
        add_finding(
            findings,
            "CANDIDATE_CHANGE_FLAG_INVALID",
            "changes_executable_candidate must be a boolean",
        )

    validate_packet_bindings(document, packet, findings)
    if check_dispatch:
        if (
            repo_root is not None
            and phase != "audit"
            and isinstance(packet, dict)
            and packet.get("identity_contract") not in SUPPORTED_IDENTITY_CONTRACTS
        ):
            add_finding(
                findings,
                "DISPATCH_CONTRACT_UNSUPPORTED",
                "packet predates a supported recoverable dispatch identity contract",
            )
        else:
            validate_dispatch_bindings(document, packet, repo_root, findings)
    validate_materialization_boundary(document, findings)
    validate_materialized_candidate_sources(document, packet, repo_root, findings)
    validate_prepublication_engineering_evidence(document, packet, repo_root, findings)
    validate_publication_charge(document, packet, repo_root, findings)
    validate_evaluation_boundary(document, packet, findings)
    if document.get("work_kind") == "experiment":
        validate_evaluation_target_sources(document, repo_root, findings)

    payload_sha256 = hashlib.sha256(canonical_payload(document)).hexdigest()
    expected_id = computed_result_id(document, payload_sha256)
    declared_id = document.get("result_packet_id")
    if phase == "draft" and declared_id is not None:
        add_finding(
            findings,
            "DRAFT_ALREADY_FROZEN",
            "draft result validation requires result_packet_id to be absent",
        )
    elif phase == "frozen":
        if declared_id is None:
            add_finding(findings, "RESULT_ID_MISSING", "frozen result requires result_packet_id")
        elif declared_id != expected_id:
            add_finding(
                findings,
                "RESULT_ID_MISMATCH",
                f"declared {declared_id} does not equal computed {expected_id}",
            )
    elif phase == "audit" and declared_id not in {None, expected_id}:
        add_finding(
            findings,
            "RESULT_ID_MISMATCH",
            f"declared {declared_id} does not equal computed {expected_id}",
        )

    finding_summary = finalize_findings(findings)
    actionable_findings = finding_summary["findings"]
    finding_codes = {item["code"] for item in actionable_findings}
    output: dict[str, Any] = {
        "validator": VALIDATOR,
        "batch_id": document.get("batch_id"),
        "result_packet_path": document.get("result_packet_path"),
        "result_payload_sha256": payload_sha256,
        "computed_result_packet_id": expected_id,
        "result_structure_ready": finding_summary["ready"],
        "checks": {
            "field_schema": "FAIL"
            if finding_codes
            & {
                "REQUIRED_FIELD_MISSING",
                "LIST_FIELD_INVALID",
                "OUTCOME_INVALID",
                "CAMPAIGN_GENERATION_INVALID",
                "CANDIDATE_CHANGE_FLAG_INVALID",
                "CODE_PROFILE_INVALID",
            }
            else "PASS",
            "packet_binding": "FAIL"
            if "PACKET_BINDING_MISMATCH" in finding_codes
            else "PASS",
            "result_identity": "FAIL"
            if finding_codes
            & {"DRAFT_ALREADY_FROZEN", "RESULT_ID_MISSING", "RESULT_ID_MISMATCH"}
            else "PASS",
            "materialization_boundary": "FAIL"
            if any(code.startswith("MATERIAL") or code == "IMPLEMENTATION_REVIEW_STATE_INVALID" for code in finding_codes)
            else "PASS",
            "evaluation_boundary": "FAIL"
            if any(
                code.startswith(("EVALUATION_", "FORMAL_EVALUATION_", "DIAGNOSTIC_"))
                or code == "EXPERIMENT_LEGACY_BINDING_PRESENT"
                for code in finding_codes
            )
            else "PASS",
        },
        "findings": actionable_findings,
        "blocking_findings": finding_summary["blocking_findings"],
        "repair_findings": finding_summary["repair_findings"],
        "advisories": finding_summary["advisories"],
        "finding_effect_counts": finding_summary["finding_effect_counts"],
    }
    canonical = json.dumps(
        output, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()
    output["validation_id"] = f"batch-result-validation-sha256:{hashlib.sha256(canonical).hexdigest()}"
    return output


def read_yaml(path: Path, label: str) -> dict[str, Any]:
    try:
        document = yaml.safe_load(path.read_text())
    except (OSError, yaml.YAMLError) as exc:
        raise ValueError(f"cannot read {label}: {exc}") from exc
    if not isinstance(document, dict):
        raise ValueError(f"{label} must contain a YAML mapping")
    return document


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path)
    parser.add_argument("--packet", required=True, type=Path)
    parser.add_argument("--phase", choices=("draft", "frozen", "audit"), default="frozen")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        result_document = read_yaml(args.result, "result")
        packet_document = read_yaml(args.packet, "packet")
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if args.phase == "draft":
        if args.output is None:
            print("draft result validation requires --output", file=sys.stderr)
            return 2
        repo_root = args.repo_root.resolve()
        validation_path = packet_document.get("result_validation_path")
        result_path = packet_document.get("result_packet_path")
        if not isinstance(validation_path, str) or not isinstance(result_path, str):
            print(
                "packet requires result_validation_path and result_packet_path",
                file=sys.stderr,
            )
            return 2
        expected_validation = (repo_root / validation_path).resolve()
        authoritative_result = (repo_root / result_path).resolve()
        if args.output.resolve() != expected_validation:
            print("draft validation output does not match packet result_validation_path", file=sys.stderr)
            return 2
        if args.result.resolve() == authoritative_result or authoritative_result.exists():
            print(
                "draft validation must run before the authoritative result path exists",
                file=sys.stderr,
            )
            return 2
    validation = validate(
        result_document,
        args.phase,
        packet_document,
        repo_root=args.repo_root.resolve(),
    )
    rendered = json.dumps(validation, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered)
    else:
        sys.stdout.write(rendered)
    return 0 if validation["result_structure_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
