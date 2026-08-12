#!/usr/bin/env python3
"""Validate a Frontier batch result before its immutable path is written."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required to validate Frontier batch results") from exc


VALIDATOR = "frontier-batch-result-preflight/1"
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
    "candidate_manifest",
    "candidate_identity",
    "experiment_identity",
    "resolved_configuration_identity",
    "dependency_identity",
    "implementation_review_state",
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
    "changes_executable_candidate": "changes_executable_candidate",
    "result_packet_path": "result_packet_path",
}


def canonical_payload(document: dict[str, Any]) -> bytes:
    payload = dict(document)
    payload.pop("result_packet_id", None)
    return yaml.safe_dump(payload, sort_keys=False, allow_unicode=True).encode()


def computed_result_id(document: dict[str, Any], digest: str) -> str:
    return f"{document.get('batch_id', 'UNKNOWN')}-result-sha256:{digest}"


def add_finding(findings: list[dict[str, str]], code: str, detail: str) -> None:
    finding = {"code": code, "detail": detail}
    if finding not in findings:
        findings.append(finding)


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


def validate_evaluation_boundary(
    document: dict[str, Any], findings: list[dict[str, str]]
) -> None:
    if document.get("work_kind") != "experiment":
        if str(document.get("performance_evaluation_state", "")).startswith("performed"):
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
    for field in ("experiment_identity", "candidate_manifest", "candidate_identity"):
        if document.get(field) is None or document.get(field) == "":
            add_finding(
                findings,
                "EVALUATION_BINDING_MISSING",
                f"Slot H evaluation requires {field}",
            )


def validate(
    document: dict[str, Any], phase: str, packet: dict[str, Any] | None = None
) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    for field in sorted(REQUIRED_FIELDS - document.keys()):
        add_finding(findings, "REQUIRED_FIELD_MISSING", field)
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
    validate_materialization_boundary(document, findings)
    validate_evaluation_boundary(document, findings)

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

    findings.sort(key=lambda item: (item["code"], item["detail"]))
    finding_codes = {item["code"] for item in findings}
    output: dict[str, Any] = {
        "validator": VALIDATOR,
        "batch_id": document.get("batch_id"),
        "result_packet_path": document.get("result_packet_path"),
        "result_payload_sha256": payload_sha256,
        "computed_result_packet_id": expected_id,
        "result_structure_ready": not findings,
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
            if finding_codes
            & {
                "PERFORMANCE_RESULT_OUTSIDE_EVALUATION",
                "EVALUATION_CHANGED_CANDIDATE",
                "EVALUATION_MATERIALIZATION_STATE_INVALID",
                "EVALUATION_BINDING_MISSING",
            }
            else "PASS",
        },
        "findings": findings,
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
    validation = validate(result_document, args.phase, packet_document)
    rendered = json.dumps(validation, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered)
    else:
        sys.stdout.write(rendered)
    return 0 if validation["result_structure_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
