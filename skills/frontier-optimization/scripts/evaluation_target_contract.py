"""Shared evaluation-target contracts and evidence-scope limits."""

from __future__ import annotations

import hashlib
import math
import re
from typing import Any

from finding_effects import add_finding

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required to validate evaluation targets") from exc


TARGET_CONTRACT_V2 = "frontier-evaluation-target/2"
ROUTINE_FOLLOW_UP_CONTRACT = "frontier-routine-follow-up/1"
ROUTINE_TEMPLATE_CONTRACT = "frontier-routine-experiment-template/1"
ROUTINE_ADMISSION_CONTRACT = "frontier-routine-admission/1"
EVALUATION_PROTOCOL_CONTRACT = "frontier-evaluation-protocol/1"
CALIBRATION_RESULT_CONTRACT = "frontier-protocol-calibration-result/1"

SHA256_VALUE = re.compile(r"^(?:sha256:)?[0-9a-f]{64}$")
CONTENT_ROOT = re.compile(r"^frontier-content-root-sha256:[0-9a-f]{64}$")
LEGACY_KEYS = {
    "candidate_identity",
    "candidate_manifest",
    "experiment_identity",
    "implementation_review_state",
}
DIAGNOSTIC_PROHIBITED_CONSEQUENCES = {
    "E",
    "integration",
    "incumbent use",
    "promotion",
    "submission",
    "strength claim",
}
ROUTINE_PROHIBITED_CONSEQUENCES = {
    "E",
    "formal Slot H",
    "sealed confirmation",
    "integration",
    "incumbent use",
    "promotion",
    "submission",
    "external action",
    "paid action",
    "publication",
    "strength claim",
    "direct next-B authority",
}
PROHIBITED_RESULT_KEYS = {
    "claim",
    "e_record",
    "evaluation_record",
    "incumbent",
    "integration",
    "promotion",
    "strength_claim",
    "submission",
}
ROUTINE_PROHIBITED_RESULT_KEYS = PROHIBITED_RESULT_KEYS | {
    "confirmed",
    "confirmation_claim",
    "generalized",
    "generalization",
    "transfer_claim",
    "component_attribution",
    "mechanism_attribution",
    "formal_slot_h",
    "sealed_confirmation",
}
SCOPE_FIELDS = {
    "evidence_class",
    "exposure",
    "confirmation",
    "comparator_scope",
    "data_scope",
    "workload_scope",
    "scenario_scope",
    "metric_scope",
    "mechanism_grain",
    "transfer_scope",
}


def validate_experiment_source(
    experiment: Any,
    *,
    logical_name: str,
    raw: bytes,
    findings: list[dict[str, str]],
) -> None:
    """Validate one exact experiment file against its canonical target binding."""

    if not isinstance(experiment, dict):
        add_finding(
            findings,
            "EXPERIMENT_IDENTITY_MISMATCH",
            "evaluation_target experiment must be a mapping",
        )
        return
    if experiment.get("path") != logical_name:
        add_finding(
            findings,
            "EXPERIMENT_IDENTITY_MISMATCH",
            "experiment source path does not match evaluation_target",
        )
    expected_sha = experiment.get("file_sha256")
    observed_sha = hashlib.sha256(raw).hexdigest()
    if not isinstance(expected_sha, str) or expected_sha.removeprefix("sha256:") != observed_sha:
        add_finding(
            findings,
            "EXPERIMENT_IDENTITY_MISMATCH",
            f"experiment source has SHA-256 {observed_sha}, expected {expected_sha}",
        )
    declared_id = experiment.get("experiment_id")
    try:
        lines = raw.splitlines(keepends=True)
        identity_lines = [
            index for index, line in enumerate(lines) if line.startswith(b"experiment_id:")
        ]
        if len(identity_lines) != 1:
            raise ValueError(
                "experiment source must contain exactly one top-level experiment_id line"
            )
        parsed = yaml.safe_load(raw)
        if not isinstance(parsed, dict) or parsed.get("experiment_id") != declared_id:
            raise ValueError("experiment source experiment_id does not match evaluation_target")
        if not isinstance(declared_id, str) or ":" not in declared_id:
            raise ValueError("experiment_id must be namespaced")
        index = identity_lines[0]
        digest = hashlib.sha256(b"".join(lines[:index] + lines[index + 1 :])).hexdigest()
        expected_id = f"{declared_id.rsplit(':', 1)[0]}:{digest}"
        if declared_id != expected_id:
            raise ValueError(
                f"experiment_id {declared_id!r} does not equal byte-derived {expected_id!r}"
            )
    except (UnicodeDecodeError, ValueError, yaml.YAMLError) as exc:
        add_finding(
            findings,
            "EXPERIMENT_IDENTITY_MISMATCH",
            f"cannot derive evaluation_target experiment identity: {exc}",
        )


def require_nonempty_string(
    value: Any, field: str, findings: list[dict[str, str]]
) -> None:
    if not isinstance(value, str) or not value.strip():
        add_finding(
            findings,
            "EVALUATION_TARGET_SCHEMA_INVALID",
            f"evaluation_target {field} must be a nonempty string",
        )


def require_sha256(value: Any, field: str, findings: list[dict[str, str]]) -> None:
    if not isinstance(value, str) or SHA256_VALUE.fullmatch(value) is None:
        add_finding(
            findings,
            "EVALUATION_TARGET_IDENTITY_INVALID",
            f"evaluation_target {field} must be an exact lowercase SHA-256 value",
        )


def require_content_root(value: Any, field: str, findings: list[dict[str, str]]) -> None:
    if not isinstance(value, str) or CONTENT_ROOT.fullmatch(value) is None:
        add_finding(
            findings,
            "EVALUATION_TARGET_IDENTITY_INVALID",
            f"evaluation_target {field} must be an exact Frontier content root",
        )


def validate_evidence_scope(
    value: Any, findings: list[dict[str, str]], *, role: str = "evidence_scope"
) -> None:
    if not isinstance(value, dict) or set(value) != SCOPE_FIELDS:
        add_finding(
            findings,
            "EVALUATION_SCOPE_INVALID",
            f"{role} must contain exactly the structured evidence-scope fields",
        )
        return
    expected = {
        "evidence_class": "b-evidence",
        "exposure": "development",
        "confirmation": "none",
        "mechanism_grain": "whole-package-at-most",
        "transfer_scope": "local-only",
    }
    for field, required in expected.items():
        if value.get(field) != required:
            add_finding(
                findings,
                "EVALUATION_SCOPE_EXCEEDS_ROUTINE_LIMIT",
                f"{role}.{field} must equal {required!r}",
            )
    for field in SCOPE_FIELDS - expected.keys():
        item = value.get(field)
        if not isinstance(item, (str, list)) or item in ("", []):
            add_finding(
                findings,
                "EVALUATION_SCOPE_INVALID",
                f"{role}.{field} must name the exact observed scope",
            )


def validate_evaluation_target_contract(
    evaluation_target: Any, findings: list[dict[str, str]]
) -> None:
    """Validate the canonical packet/result target for experiment work."""

    if not isinstance(evaluation_target, dict):
        add_finding(
            findings,
            "EVALUATION_TARGET_INVALID",
            "experiment work requires a structured evaluation_target",
        )
        return
    for field in sorted(LEGACY_KEYS & evaluation_target.keys()):
        add_finding(
            findings,
            "EVALUATION_TARGET_LEGACY_BINDING_PRESENT",
            f"evaluation_target must use its canonical nested mapping instead of {field}",
        )

    mode = evaluation_target.get("mode")
    if mode not in {"formal-slot-h", "diagnostic-only", "routine-local"}:
        add_finding(
            findings,
            "EVALUATION_TARGET_MODE_INVALID",
            "evaluation_target mode must be formal-slot-h, diagnostic-only, or routine-local",
        )

    candidate = evaluation_target.get("candidate")
    if not isinstance(candidate, dict):
        add_finding(
            findings,
            "EVALUATION_TARGET_SCHEMA_INVALID",
            "evaluation_target candidate must be a mapping",
        )
    else:
        for field in ("id", "root_path", "manifest_path"):
            require_nonempty_string(candidate.get(field), f"candidate.{field}", findings)
        require_sha256(candidate.get("manifest_sha256"), "candidate.manifest_sha256", findings)
        if mode == "routine-local":
            require_sha256(
                candidate.get("collection_root"), "candidate.collection_root", findings
            )

    experiment = evaluation_target.get("experiment")
    if not isinstance(experiment, dict):
        add_finding(
            findings,
            "EVALUATION_TARGET_SCHEMA_INVALID",
            "evaluation_target experiment must be a mapping",
        )
    else:
        for field in ("path", "experiment_id"):
            require_nonempty_string(experiment.get(field), f"experiment.{field}", findings)
        require_sha256(experiment.get("file_sha256"), "experiment.file_sha256", findings)

    if mode == "formal-slot-h":
        _validate_formal(evaluation_target, findings)
    elif mode == "diagnostic-only":
        _validate_diagnostic(evaluation_target, findings)
    elif mode == "routine-local":
        _validate_routine(evaluation_target, findings)

    _validate_evidence_reuse(evaluation_target, mode, findings)


def _validate_implementation_review(
    value: Any, findings: list[dict[str, str]], *, routine: bool = False
) -> None:
    if not isinstance(value, dict):
        add_finding(
            findings,
            "FORMAL_EVALUATION_REVIEW_MISSING",
            "post-implementation evaluation requires a structured implementation_review",
        )
        return
    fields = ("review_id", "path")
    for field in fields:
        require_nonempty_string(value.get(field), f"implementation_review.{field}", findings)
    require_sha256(value.get("file_sha256"), "implementation_review.file_sha256", findings)
    if routine:
        require_nonempty_string(
            value.get("decision_root"), "implementation_review.decision_root", findings
        )
        require_nonempty_string(
            value.get("attestation_root"), "implementation_review.attestation_root", findings
        )
    if value.get("result") != "IMPLEMENTATION_READY":
        add_finding(
            findings,
            "FORMAL_EVALUATION_REVIEW_MISSING",
            "post-implementation evaluation requires implementation_review.result: IMPLEMENTATION_READY",
        )


def _validate_formal(target: dict[str, Any], findings: list[dict[str, str]]) -> None:
    for field in ("exception_evidence", "consequence_limit", "prohibited_consequences"):
        if field in target:
            add_finding(
                findings,
                "FORMAL_DIAGNOSTIC_BINDING_PRESENT",
                f"formal-slot-h evaluation_target must omit {field}",
            )
    _validate_implementation_review(target.get("implementation_review"), findings)
    slot = target.get("slot_h_contract")
    if not isinstance(slot, dict):
        add_finding(
            findings,
            "FORMAL_EVALUATION_CONTRACT_MISSING",
            "formal Slot H evaluation requires a structured slot_h_contract",
        )
    else:
        require_nonempty_string(slot.get("path"), "slot_h_contract.path", findings)
        require_sha256(slot.get("file_sha256"), "slot_h_contract.file_sha256", findings)


def _validate_diagnostic(target: dict[str, Any], findings: list[dict[str, str]]) -> None:
    for field in ("implementation_review", "slot_h_contract", "routine_slot", "protocol", "calibration"):
        if field in target:
            add_finding(
                findings,
                "DIAGNOSTIC_FORMAL_BINDING_PRESENT",
                f"diagnostic-only evaluation_target must omit {field}",
            )
    if target.get("consequence_limit") != "B evidence only":
        add_finding(
            findings,
            "DIAGNOSTIC_CONSEQUENCE_BOUNDARY_MISSING",
            "diagnostic-only packet requires consequence_limit: B evidence only",
        )
    if not target.get("exception_evidence"):
        add_finding(
            findings,
            "DIAGNOSTIC_EXCEPTION_EVIDENCE_MISSING",
            "diagnostic-only packet requires its candidate-lifecycle exception evidence",
        )
    prohibited = target.get("prohibited_consequences")
    if not isinstance(prohibited, list) or not DIAGNOSTIC_PROHIBITED_CONSEQUENCES <= set(prohibited):
        add_finding(
            findings,
            "DIAGNOSTIC_PROHIBITIONS_INCOMPLETE",
            "diagnostic-only packet must prohibit E, integration, incumbent use, promotion, submission, and strength claims",
        )


def _binding_contract(
    value: Any,
    role: str,
    contract: str,
    findings: list[dict[str, str]],
) -> None:
    if not isinstance(value, dict):
        add_finding(findings, "ROUTINE_BINDING_MISSING", f"routine-local requires {role}")
        return
    if value.get("contract_version") != contract:
        add_finding(
            findings,
            "ROUTINE_BINDING_CONTRACT_INVALID",
            f"{role}.contract_version must be {contract}",
        )
    require_content_root(value.get("content_root"), f"{role}.content_root", findings)


def _validate_routine(target: dict[str, Any], findings: list[dict[str, str]]) -> None:
    if target.get("contract_version") != TARGET_CONTRACT_V2:
        add_finding(
            findings,
            "ROUTINE_TARGET_CONTRACT_INVALID",
            f"routine-local evaluation_target must use {TARGET_CONTRACT_V2}",
        )
    if target.get("result_contract_version") != "frontier-batch-result/2":
        add_finding(
            findings,
            "ROUTINE_RESULT_CONTRACT_INVALID",
            "routine-local requires frontier-batch-result/2",
        )
    if "slot_h_contract" in target or "exception_evidence" in target:
        add_finding(
            findings,
            "ROUTINE_FORMAL_BINDING_PRESENT",
            "routine-local target cannot use the diagnostic exception or formal Slot H gate",
        )
    routine_review = target.get("implementation_review")
    if not isinstance(routine_review, dict) or set(routine_review) != {"result", "derivation"}:
        add_finding(
            findings,
            "FORMAL_EVALUATION_REVIEW_MISSING",
            "routine-local requires the fixed derived-review rule",
        )
    else:
        if routine_review.get("result") != "IMPLEMENTATION_READY":
            add_finding(
                findings,
                "FORMAL_EVALUATION_REVIEW_MISSING",
                "routine-local requires IMPLEMENTATION_READY",
            )
        if routine_review.get("derivation") != "unique finding-free review of the derived candidate":
            add_finding(
                findings,
                "FORMAL_EVALUATION_REVIEW_MISSING",
                "routine-local implementation review must be derived, not caller-selected",
            )
    _binding_contract(
        target.get("protocol"), "protocol", EVALUATION_PROTOCOL_CONTRACT, findings
    )
    _binding_contract(
        target.get("calibration"), "calibration", CALIBRATION_RESULT_CONTRACT, findings
    )
    if isinstance(target.get("protocol"), dict):
        require_nonempty_string(target["protocol"].get("protocol_id"), "protocol.protocol_id", findings)
        require_nonempty_string(
            target["protocol"].get("invalidation_key"), "protocol.invalidation_key", findings
        )
    if isinstance(target.get("calibration"), dict):
        require_nonempty_string(
            target["calibration"].get("calibration_id"), "calibration.calibration_id", findings
        )
        require_nonempty_string(
            target["calibration"].get("protocol_invalidation_key"),
            "calibration.protocol_invalidation_key",
            findings,
        )
    slot = target.get("routine_slot")
    if not isinstance(slot, dict):
        add_finding(findings, "ROUTINE_SLOT_MISSING", "routine-local requires routine_slot")
    else:
        if slot.get("contract_version") != ROUTINE_FOLLOW_UP_CONTRACT:
            add_finding(
                findings,
                "ROUTINE_SLOT_CONTRACT_INVALID",
                f"routine_slot.contract_version must be {ROUTINE_FOLLOW_UP_CONTRACT}",
            )
        for field in (
            "slot_id",
            "materialization_batch_id",
            "follow_up_batch_id",
            "origin_decision_root",
            "origin_authority_root",
            "template_root",
        ):
            require_nonempty_string(slot.get(field), f"routine_slot.{field}", findings)
    if target.get("consequence_limit") != "B evidence only":
        add_finding(
            findings,
            "ROUTINE_CONSEQUENCE_BOUNDARY_MISSING",
            "routine-local packet requires consequence_limit: B evidence only",
        )
    sample_ceiling = target.get("sample_ceiling")
    if (
        not isinstance(sample_ceiling, dict)
        or set(sample_ceiling) != {"runs"}
        or not isinstance(sample_ceiling.get("runs"), int)
        or isinstance(sample_ceiling.get("runs"), bool)
        or sample_ceiling["runs"] < 1
    ):
        add_finding(
            findings,
            "ROUTINE_SAMPLE_CEILING_INVALID",
            "routine-local requires sample_ceiling with one positive integer runs field",
        )
    resource_ceiling = target.get("resource_ceiling")
    if (
        not isinstance(resource_ceiling, dict)
        or not resource_ceiling
        or any(
            not isinstance(name, str)
            or not name.strip()
            or not isinstance(limit, (int, float))
            or isinstance(limit, bool)
            or not math.isfinite(limit)
            or limit <= 0
            for name, limit in resource_ceiling.items()
        )
    ):
        add_finding(
            findings,
            "ROUTINE_RESOURCE_CEILING_INVALID",
            "routine-local resource_ceiling requires nonempty names and finite positive numeric limits",
        )
    prohibited = target.get("prohibited_consequences")
    if not isinstance(prohibited, list) or not ROUTINE_PROHIBITED_CONSEQUENCES <= set(prohibited):
        add_finding(
            findings,
            "ROUTINE_PROHIBITIONS_INCOMPLETE",
            "routine-local packet does not prohibit every later or external consequence",
        )
    validate_evidence_scope(target.get("evidence_scope"), findings)


def _validate_evidence_reuse(
    target: dict[str, Any], mode: Any, findings: list[dict[str, str]]
) -> None:
    reuse = target.get("evidence_reuse")
    if reuse is None:
        return
    if mode != "formal-slot-h":
        add_finding(
            findings,
            "EVIDENCE_REUSE_MODE_INVALID",
            "evidence_reuse is permitted only for formal-slot-h publication recovery",
        )
    if not isinstance(reuse, dict):
        add_finding(
            findings,
            "EVIDENCE_REUSE_CONTRACT_INVALID",
            "evaluation_target evidence_reuse must be a mapping",
        )
        return
    require_nonempty_string(reuse.get("source_batch_id"), "evidence_reuse.source_batch_id", findings)
    artifacts = reuse.get("raw_artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        add_finding(
            findings,
            "EVIDENCE_REUSE_CONTRACT_INVALID",
            "evidence_reuse raw_artifacts must be a nonempty list",
        )
    else:
        for index, artifact in enumerate(artifacts):
            if not isinstance(artifact, dict):
                add_finding(
                    findings,
                    "EVIDENCE_REUSE_CONTRACT_INVALID",
                    f"evidence_reuse raw_artifacts[{index}] must be a mapping",
                )
                continue
            require_nonempty_string(artifact.get("path"), f"evidence_reuse.raw_artifacts[{index}].path", findings)
            require_sha256(artifact.get("file_sha256"), f"evidence_reuse.raw_artifacts[{index}].file_sha256", findings)
    expected = {
        "measurement_execution": "prohibited",
        "reruns": 0,
        "measurement_semantics": "unchanged",
    }
    for field, value in expected.items():
        if reuse.get(field) != value:
            add_finding(
                findings,
                "EVIDENCE_REUSE_CONTRACT_INVALID",
                f"evidence_reuse {field} must equal {value!r}",
            )


def normalized_nested_keys(value: Any) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            keys.add(str(key).lower().replace("-", "_").replace(" ", "_"))
            keys.update(normalized_nested_keys(child))
    elif isinstance(value, list):
        for child in value:
            keys.update(normalized_nested_keys(child))
    return keys
