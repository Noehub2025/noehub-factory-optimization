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

from identity_bindings import IdentityBindingError, load_file_binding, resolve_repo_file
from finding_effects import add_finding, finalize_findings
from validate_candidate_package import validate_candidate_package
from frontier_provenance.content import ProvenanceError
from frontier_provenance.compatibility import require_v1_completion
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


VALIDATOR = "frontier-batch-result-preflight/6"
IDENTITY_CONTRACT = "frontier-dispatch-identity/2"
SUPPORTED_IDENTITY_CONTRACTS = {IDENTITY_CONTRACT}
RESULT_CONTRACT_V1 = "frontier-batch-result/1"
RESULT_CONTRACT_V2 = "frontier-batch-result/2"
SUPPORTED_RESULT_CONTRACTS = {RESULT_CONTRACT_V1, RESULT_CONTRACT_V2}
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
