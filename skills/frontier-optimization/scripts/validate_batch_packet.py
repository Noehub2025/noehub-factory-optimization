#!/usr/bin/env python3
"""Validate Frontier batch packet structure before authorization review."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import posixpath
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from identity_bindings import (
    IdentityBindingError,
    load_file_binding,
    require_digest,
    resolve_repo_file,
    sha256_bytes,
)
from authorization_target_contract import (
    AuthorizationTargetContractError,
    TARGET_SPEC_BINDING_FIELDS,
    TARGET_SPEC_CONTRACT,
    load_target_specification,
    validate_specification_against_packet,
)
from finding_effects import add_finding, finalize_findings
from workflow_source_binding import WorkflowSourceBindingError, validate_binding

try:
    import yaml
except ImportError as exc:  # pragma: no cover - exercised by the CLI environment
    raise SystemExit("PyYAML is required to validate Frontier batch packets") from exc


VALIDATOR = "frontier-batch-packet-preflight/8"
WRITE_VERBS = re.compile(r"\b(edit|write|create|modify|overwrite|change)\b", re.I)
LIFECYCLE_CONTRACT = "frontier-lifecycle-transition/1"
IDENTITY_CONTRACT = "frontier-dispatch-identity/2"
RESULT_CONTRACT_V1 = "frontier-batch-result/1"
ENGINEERING_CHECK_PLAN_CONTRACT = "frontier-engineering-check-plan/1"
SHA256_IDENTITY = re.compile(r"^sha256:[0-9a-f]{64}$")
EXPERIMENT_IDENTITY = re.compile(
    r"\b[A-Za-z0-9._-]+-experiment-sha256:[0-9a-f]{64}\b"
)
PACKET_REQUIRED_FIELDS = {
    "packet_path",
    "packet_preflight_path",
    "task_path",
    "batch_id",
    "campaign_generation",
    "work_kind",
    "changes_executable_candidate",
    "executor",
    "required_inputs",
    "identity_contract",
    "result_contract_version",
    "workflow_source_binding",
    "workflow_source_identity",
    "worker_source_member",
    "design_profile",
    "design_contract_identity",
    "design_contract_binding",
    "development_authorization_target",
    "source_base_identity",
    "source_base_binding",
    "maximum_spend",
    "authorization_gate",
    "authorization_boundary",
    "stop_conditions",
    "forced_halts",
    "allowed_code_paths",
    "worker_forbidden_paths",
    "execution_frozen_inputs",
    "execution_baseline_root",
    "execution_start_path",
    "candidate_root_path",
    "artifact_paths",
    "acknowledgment_path",
    "result_validation_path",
    "result_packet_path",
    "prohibited_actions",
}
PACKET_ALLOWED_FIELDS = PACKET_REQUIRED_FIELDS | {
    "packet_id",
    "route_id",
    "campaign_baseline",
    "work_plan",
    "work_plan_revision",
    "required_design_inputs",
    "design_traceability",
    "design_review",
    "parallel_set",
    "problem_epoch",
    "problem_generated_at",
    "representation_revision",
    "representation_generated_at",
    "permitted_scope",
    "starting_artifacts",
    "supporting_evidence",
    "work",
    "human_input_request",
    "human_input_schema",
    "human_input_provenance_requirements",
    "human_input_quality_checks",
    "human_input_confidentiality",
    "human_input_acceptance",
    "repository_structure_disposition",
    "repository_structure_evidence",
    "repository_layout_approval",
    "workspace_identity",
    "candidate_interface",
    "candidate_package_inventory_path",
    "candidate_manifest_path",
    "engineering_check_plan",
    "implementation_review_gate",
    "evaluation_target",
    "preparation_role",
    "decision_hypothesis",
    "expected_observation",
    "output_contract",
    "implementation_validation",
    "implementation_definition_of_done",
    "permitted_operations",
    "allowed_feedback",
    "accounting_source",
    "baseline_establishment_checkpoint",
    "first_performance_check",
    "preparation_budget_limit",
    "required_follow_up_reserve",
    "decision_after_checkpoint",
    "measurement",
    "comparison_validity_checks",
    "candidate_identity_rule",
    "constraints",
    "resume_when",
    "coordinator_lifecycle_transition",
}
PROJECT_EXTERNAL_TEXT = re.compile(
    r"(?:^|[\s'\"`(])(?:\.agents|\.codex)/|"
    r"(?:^|/)\S*-snapshot/inputs(?:/|$)|"
    r"\bworkflow[-_ ]sha256\b|"
    r"\b(?:slice\s*7|quick_validate(?:\.py)?|validate_frontier_skill_bundle(?:\.py)?|frontier\s+validator\s+tests?)\b",
    re.I,
)
def load_result_contract_validator() -> Any:
    script = Path(__file__).with_name("validate_batch_result.py")
    spec = importlib.util.spec_from_file_location(
        "frontier_validate_batch_result_contract", script
    )
    if spec is None or spec.loader is None:  # pragma: no cover
        raise RuntimeError(f"cannot load result contract validator from {script}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RESULT_CONTRACT_VALIDATOR = load_result_contract_validator()


@dataclass(frozen=True, order=True)
class PathSpec:
    path: str
    subtree: bool = False

    def render(self) -> str:
        return f"{self.path}/**" if self.subtree else self.path


def canonical_payload(document: dict[str, Any]) -> bytes:
    payload = dict(document)
    payload.pop("packet_id", None)
    return yaml.safe_dump(payload, sort_keys=False, allow_unicode=True).encode()


def computed_packet_id(document: dict[str, Any], digest: str) -> str:
    batch_id = str(document.get("batch_id", "UNKNOWN"))
    return f"{batch_id}-packet-sha256:{digest}"


def normalize_path(raw: str, *, annotated: bool = False) -> PathSpec:
    value = raw.strip()
    if annotated and " as " in value:
        value = value.split(" as ", 1)[0].strip()
    subtree = value.endswith("/")
    value = value.rstrip("/")
    if not value or value.startswith("/"):
        raise ValueError(f"path must be a nonempty repository-relative path: {raw!r}")
    normalized = posixpath.normpath(value)
    if normalized in {".", ".."} or normalized.startswith("../"):
        raise ValueError(f"path escapes the repository: {raw!r}")
    return PathSpec(normalized, subtree)


def parse_path_entry(value: Any, field: str) -> PathSpec:
    if isinstance(value, str):
        return normalize_path(value, annotated=field == "allowed_code_paths")
    if isinstance(value, dict) and isinstance(value.get("path"), str):
        spec = normalize_path(value["path"])
        scope = value.get("scope")
        if scope not in {None, "file", "subtree"}:
            raise ValueError(f"{field} scope must be file or subtree")
        return PathSpec(spec.path, scope == "subtree" or spec.subtree)
    raise ValueError(f"{field} entries must be path strings or mappings with path")


def parse_path_list(document: dict[str, Any], field: str) -> tuple[list[PathSpec], list[str]]:
    findings: list[str] = []
    values = document.get(field, [])
    if values is None:
        return [], findings
    if not isinstance(values, list):
        return [], [f"{field} must be a list"]
    parsed: list[PathSpec] = []
    for index, value in enumerate(values):
        try:
            parsed.append(parse_path_entry(value, field))
        except ValueError as exc:
            findings.append(f"{field}[{index}]: {exc}")
    return parsed, findings


def parse_single_path(document: dict[str, Any], field: str, required: bool = True) -> tuple[PathSpec | None, list[str]]:
    value = document.get(field)
    if value is None:
        return None, [f"{field} is required"] if required else []
    try:
        return parse_path_entry(value, field), []
    except ValueError as exc:
        return None, [f"{field}: {exc}"]


def overlaps(left: PathSpec, right: PathSpec) -> bool:
    if left.path == right.path:
        return True
    if left.subtree and right.path.startswith(left.path + "/"):
        return True
    if right.subtree and left.path.startswith(right.path + "/"):
        return True
    return False


def covers(container: PathSpec, target: PathSpec) -> bool:
    if container.path == target.path:
        return container.subtree or not target.subtree
    return container.subtree and target.path.startswith(container.path + "/")


def strings_with_paths(
    value: Any, path: tuple[str, ...] = ()
) -> list[tuple[tuple[str, ...], str]]:
    if isinstance(value, str):
        return [(path, value)]
    if isinstance(value, list):
        return [
            item
            for index, child in enumerate(value)
            for item in strings_with_paths(child, (*path, str(index)))
        ]
    if isinstance(value, dict):
        return [
            item
            for key, child in value.items()
            for item in strings_with_paths(child, (*path, str(key)))
        ]
    return []


def validate_project_only_packet(
    document: dict[str, Any], phase: str, findings: list[dict[str, str]]
) -> None:
    if phase == "audit":
        return
    for field in sorted(set(document) - PACKET_ALLOWED_FIELDS):
        add_finding(
            findings,
            "UNKNOWN_PACKET_FIELD",
            f"{field} is not part of the closed project batch schema",
        )
    for path, value in strings_with_paths(document):
        if PROJECT_EXTERNAL_TEXT.search(value):
            add_finding(
                findings,
                "NON_PROJECT_PACKET_INPUT",
                f"{'.'.join(path)} refers to workflow, Skill, validator, or retired copied-snapshot state",
            )


def validate_canonical_identity_ownership(
    document: dict[str, Any], phase: str, findings: list[dict[str, str]]
) -> None:
    if phase == "audit" or document.get("work_kind") != "experiment":
        return
    canonical_path = ("evaluation_target", "experiment", "experiment_id")
    for path, value in strings_with_paths(document):
        if path == canonical_path:
            continue
        duplicate = EXPERIMENT_IDENTITY.search(value)
        if duplicate:
            add_finding(
                findings,
                "DUPLICATE_EXPERIMENT_IDENTITY",
                f"{'.'.join(path)} must refer to evaluation_target.experiment without copying experiment identity {duplicate.group(0)}",
            )


def validate_engineering_check_plan(
    document: dict[str, Any],
    phase: str,
    repo_root: Path | None,
    findings: list[dict[str, str]],
) -> None:
    if phase == "audit" or document.get("changes_executable_candidate") is not True:
        return
    plan = document.get("engineering_check_plan")
    if not isinstance(plan, dict):
        add_finding(
            findings,
            "ENGINEERING_CHECK_PLAN_REQUIRED",
            "code-bearing work requires a structured engineering_check_plan",
        )
        return
    if set(plan) != {"contract_version", "checks", "effect_limits", "evidence_use"}:
        add_finding(
            findings,
            "ENGINEERING_CHECK_PLAN_INVALID",
            "engineering_check_plan must contain exactly contract_version, checks, effect_limits, and evidence_use",
        )
    if plan.get("contract_version") != ENGINEERING_CHECK_PLAN_CONTRACT:
        add_finding(
            findings,
            "ENGINEERING_CHECK_PLAN_INVALID",
            f"engineering_check_plan.contract_version must be {ENGINEERING_CHECK_PLAN_CONTRACT}",
        )
    if plan.get("evidence_use") != "engineering-only":
        add_finding(
            findings,
            "ENGINEERING_CHECK_PLAN_INVALID",
            "engineering_check_plan.evidence_use must be engineering-only",
        )
    limits = plan.get("effect_limits")
    if not isinstance(limits, dict) or not limits:
        add_finding(
            findings,
            "ENGINEERING_EFFECT_LIMIT_INVALID",
            "engineering_check_plan.effect_limits must be a nonempty effect-to-maximum mapping",
        )
        limits = {}
    else:
        for effect, maximum in limits.items():
            if (
                not isinstance(effect, str)
                or not effect.strip()
                or not isinstance(maximum, int)
                or isinstance(maximum, bool)
                or maximum < 0
            ):
                add_finding(
                    findings,
                    "ENGINEERING_EFFECT_LIMIT_INVALID",
                    f"effect_limits[{effect!r}] must be a nonnegative integer",
                )
    checks = plan.get("checks")
    if not isinstance(checks, list) or not checks:
        add_finding(
            findings,
            "ENGINEERING_CHECK_PLAN_INVALID",
            "engineering_check_plan.checks must be a nonempty list",
        )
        return
    seen_ids: set[str] = set()
    root = repo_root.resolve() if repo_root is not None else None
    for index, check in enumerate(checks):
        prefix = f"engineering_check_plan.checks[{index}]"
        expected_fields = {
            "id",
            "command",
            "selection",
            "selected_units",
            "declared_effects",
            "effect_evidence",
        }
        if not isinstance(check, dict) or set(check) != expected_fields:
            add_finding(
                findings,
                "ENGINEERING_CHECK_SCHEMA_INVALID",
                f"{prefix} must contain exactly {', '.join(sorted(expected_fields))}",
            )
            continue
        check_id = check.get("id")
        if not isinstance(check_id, str) or not check_id.strip() or check_id in seen_ids:
            add_finding(
                findings,
                "ENGINEERING_CHECK_SCHEMA_INVALID",
                f"{prefix}.id must be a unique nonempty string",
            )
        else:
            seen_ids.add(check_id)
        command = check.get("command")
        if not isinstance(command, list) or not command or not all(
            isinstance(part, str) and part for part in command
        ):
            add_finding(
                findings,
                "ENGINEERING_CHECK_SCHEMA_INVALID",
                f"{prefix}.command must be a nonempty argument list",
            )
        if check.get("selection") not in {"full-repository", "exact", "other"}:
            add_finding(
                findings,
                "ENGINEERING_CHECK_SCHEMA_INVALID",
                f"{prefix}.selection must be full-repository, exact, or other",
            )
        units = check.get("selected_units")
        if not isinstance(units, list) or not units or not all(
            isinstance(unit, str) and unit for unit in units
        ):
            add_finding(
                findings,
                "ENGINEERING_CHECK_SCHEMA_INVALID",
                f"{prefix}.selected_units must freeze every selected test or check unit",
            )
        effects = check.get("declared_effects")
        if not isinstance(effects, list) or not effects or len(effects) != len(set(effects)) or not all(
            isinstance(effect, str) and effect for effect in effects
        ):
            add_finding(
                findings,
                "ENGINEERING_CHECK_SCHEMA_INVALID",
                f"{prefix}.declared_effects must be a nonempty unique string list",
            )
            effects = []
        for effect in effects:
            if not isinstance(limits.get(effect), int) or limits.get(effect, 0) <= 0:
                add_finding(
                    findings,
                    "ENGINEERING_EFFECT_CONFLICT",
                    f"{prefix} declares effect {effect!r} but its authorized maximum is absent or zero",
                )
        evidence = check.get("effect_evidence")
        if not isinstance(evidence, list) or not evidence:
            add_finding(
                findings,
                "ENGINEERING_EFFECT_EVIDENCE_INVALID",
                f"{prefix}.effect_evidence must bind the sources used to classify effects",
            )
            continue
        for evidence_index, binding in enumerate(evidence):
            label = f"{prefix}.effect_evidence[{evidence_index}]"
            if not isinstance(binding, dict) or set(binding) != {"path", "file_sha256"}:
                add_finding(
                    findings,
                    "ENGINEERING_EFFECT_EVIDENCE_INVALID",
                    f"{label} must contain exactly path and file_sha256",
                )
                continue
            try:
                digest = require_digest(binding.get("file_sha256"), f"{label}.file_sha256")
                if root is not None:
                    _, path = resolve_repo_file(root, binding.get("path"), f"{label}.path")
                    observed = sha256_bytes(path.read_bytes())
                    if observed != digest:
                        raise IdentityBindingError(
                            f"{label} SHA-256 mismatch: declared {digest}, observed {observed}"
                        )
            except (IdentityBindingError, OSError) as exc:
                add_finding(findings, "ENGINEERING_EFFECT_EVIDENCE_INVALID", str(exc))


def validate_identity_contract(
    document: dict[str, Any],
    phase: str,
    repo_root: Path | None,
    findings: list[dict[str, str]],
) -> None:
    validate_project_only_packet(document, phase, findings)
    if phase != "audit":
        for field in sorted(PACKET_REQUIRED_FIELDS - document.keys()):
            add_finding(findings, "REQUIRED_FIELD_MISSING", field)
    if phase != "audit" and document.get("identity_contract") != IDENTITY_CONTRACT:
        add_finding(
            findings,
            "IDENTITY_CONTRACT_INVALID",
            f"identity_contract must be {IDENTITY_CONTRACT}",
        )
    if phase != "audit" and document.get("result_contract_version") != RESULT_CONTRACT_V1:
        add_finding(
            findings,
            "RESULT_CONTRACT_INVALID",
            f"result_contract_version must be {RESULT_CONTRACT_V1}",
        )
    if phase != "audit":
        try:
            observed_workflow = validate_binding(
                document.get("workflow_source_binding"), repo_root
            )
            if document.get("workflow_source_identity") != observed_workflow.get(
                "source_snapshot"
            ):
                add_finding(
                    findings,
                    "WORKFLOW_SOURCE_IDENTITY_MISMATCH",
                    "workflow_source_identity must equal the bound source snapshot identity",
                )
            if document.get("worker_source_member") != "workers/run-frontier-batch/SKILL.md":
                add_finding(
                    findings,
                    "WORKFLOW_SOURCE_MEMBER_INVALID",
                    "worker_source_member must be workers/run-frontier-batch/SKILL.md",
                )
        except WorkflowSourceBindingError as exc:
            add_finding(findings, "WORKFLOW_SOURCE_BINDING_INVALID", str(exc))

    generation = document.get("campaign_generation")
    if phase != "audit" and (
        not isinstance(generation, int) or isinstance(generation, bool) or generation < 1
    ):
        add_finding(
            findings,
            "PACKET_FIELD_INVALID",
            "campaign_generation must be a positive integer",
        )
    if phase != "audit" and not isinstance(document.get("changes_executable_candidate"), bool):
        add_finding(
            findings,
            "PACKET_FIELD_INVALID",
            "changes_executable_candidate must be a boolean",
        )
    for field in ("required_inputs", "stop_conditions", "forced_halts"):
        value = document.get(field)
        if phase != "audit" and (not isinstance(value, list) or (field == "stop_conditions" and not value)):
            add_finding(
                findings,
                "PACKET_FIELD_INVALID",
                f"{field} must be {'a nonempty' if field == 'stop_conditions' else 'a'} list",
            )
    for field in ("executor", "maximum_spend", "authorization_gate"):
        if phase != "audit" and (
            not isinstance(document.get(field), str) or not document[field].strip()
        ):
            add_finding(findings, "PACKET_FIELD_INVALID", f"{field} must be a nonempty string")

    boundary = document.get("authorization_boundary")
    boundary_fields = {"scope", "maximum_spend", "stop_boundary", "result_path"}
    if not isinstance(boundary, dict) or set(boundary) != boundary_fields:
        add_finding(
            findings,
            "AUTHORIZATION_BOUNDARY_INVALID",
            "authorization_boundary must contain exactly scope, maximum_spend, stop_boundary, and result_path",
        )
    else:
        for field in boundary_fields:
            if not isinstance(boundary.get(field), str) or not boundary[field].strip():
                add_finding(
                    findings,
                    "AUTHORIZATION_BOUNDARY_INVALID",
                    f"authorization_boundary.{field} must be a nonempty string",
                )
        if boundary.get("maximum_spend") != document.get("maximum_spend"):
            add_finding(
                findings,
                "AUTHORIZATION_BOUNDARY_INVALID",
                "authorization_boundary.maximum_spend must equal packet maximum_spend",
            )
        if boundary.get("result_path") != document.get("result_packet_path"):
            add_finding(
                findings,
                "AUTHORIZATION_BOUNDARY_INVALID",
                "authorization_boundary.result_path must equal result_packet_path",
            )

    if phase != "audit" and "workflow_contracts" in document:
        add_finding(
            findings,
            "WORKFLOW_CONTRACTS_RETIRED",
            "project batch packets contain project facts only; omit workflow and Skill bindings",
        )

    changes_candidate = document.get("changes_executable_candidate") is True
    source_identity = document.get("source_base_identity")
    source_binding = document.get("source_base_binding")
    if changes_candidate and (not isinstance(source_identity, str) or not source_identity.strip()):
        add_finding(
            findings,
            "SOURCE_BASE_IDENTITY_INVALID",
            "code-bearing work requires source_base_identity",
        )
    if changes_candidate and not isinstance(source_binding, dict):
        add_finding(
            findings,
            "SOURCE_BASE_BINDING_REQUIRED",
            "code-bearing work requires a structured source_base_binding",
        )
    elif isinstance(source_binding, dict) and repo_root is not None:
        try:
            load_file_binding(
                repo_root,
                source_binding,
                "source_base_binding",
                expected_identity=source_identity if isinstance(source_identity, str) else None,
            )
        except IdentityBindingError as exc:
            add_finding(findings, "SOURCE_BASE_BINDING_INVALID", str(exc))

    profile = document.get("design_profile")
    if phase != "audit" and profile not in {"direct", "module", "system", "not-applicable"}:
        add_finding(findings, "DESIGN_PROFILE_INVALID", "design_profile is not recognized")
    design_identity = document.get("design_contract_identity")
    design_binding = document.get("design_contract_binding")
    if profile in {"direct", "module", "system"}:
        if not isinstance(design_identity, str) or not design_identity.strip():
            add_finding(
                findings,
                "DESIGN_CONTRACT_IDENTITY_INVALID",
                f"{profile} work requires design_contract_identity",
            )
        if not isinstance(design_binding, dict):
            add_finding(
                findings,
                "DESIGN_CONTRACT_BINDING_REQUIRED",
                f"{profile} work requires design_contract_binding",
            )
        elif repo_root is not None:
            try:
                load_file_binding(
                    repo_root,
                    design_binding,
                    "design_contract_binding",
                    expected_identity=design_identity if isinstance(design_identity, str) else None,
                )
            except IdentityBindingError as exc:
                add_finding(findings, "DESIGN_CONTRACT_BINDING_INVALID", str(exc))
    elif profile == "not-applicable" and (design_identity is not None or design_binding is not None):
        add_finding(
            findings,
            "DESIGN_CONTRACT_BINDING_INVALID",
            "not-applicable design profile requires null design identity and binding",
        )

    authorization_target = document.get("development_authorization_target")
    if changes_candidate and authorization_target is None:
        add_finding(
            findings,
            "DEVELOPMENT_AUTHORIZATION_TARGET_INVALID",
            "code-bearing work requires a structured pre-packet authorization-target specification binding",
        )
    elif authorization_target is not None and not isinstance(authorization_target, dict):
        add_finding(
            findings,
            "DEVELOPMENT_AUTHORIZATION_TARGET_INVALID",
            "a pending user authorization requires a structured pre-packet authorization-target specification binding",
        )
    elif isinstance(authorization_target, dict):
        missing = TARGET_SPEC_BINDING_FIELDS - authorization_target.keys()
        unexpected = authorization_target.keys() - TARGET_SPEC_BINDING_FIELDS
        if missing or unexpected or authorization_target.get("contract_version") != TARGET_SPEC_CONTRACT:
            add_finding(
                findings,
                "DEVELOPMENT_AUTHORIZATION_TARGET_INVALID",
                "development_authorization_target must contain exactly contract_version, path, identity_field, identity, and file_sha256 for the current target specification",
            )
        elif repo_root is not None:
            try:
                specification = load_target_specification(repo_root, authorization_target)
            except AuthorizationTargetContractError as exc:
                add_finding(
                    findings,
                    "DEVELOPMENT_AUTHORIZATION_TARGET_INVALID",
                    str(exc),
                )
            else:
                for difference in validate_specification_against_packet(
                    specification, document
                ):
                    add_finding(
                        findings,
                        "DEVELOPMENT_AUTHORIZATION_TARGET_MISMATCH",
                        difference,
                    )


def validate_lifecycle_transition(
    lifecycle: Any,
    phase: str,
    findings: list[dict[str, str]],
) -> PathSpec | None:
    """Validate the machine-addressable first-B lifecycle transition contract."""
    if lifecycle is None:
        return None
    if phase == "audit" and not isinstance(lifecycle, dict):
        return None
    if not isinstance(lifecycle, dict):
        add_finding(
            findings,
            "LIFECYCLE_SCHEMA_INVALID",
            "coordinator_lifecycle_transition must be null or a structured mapping",
        )
        return None

    lifecycle_path: PathSpec | None = None
    try:
        lifecycle_path = parse_path_entry(
            lifecycle.get("path"), "coordinator_lifecycle_transition.path"
        )
    except ValueError as exc:
        add_finding(findings, "INVALID_PATH_SCHEMA", f"coordinator_lifecycle_transition.path: {exc}")

    if phase == "audit" and lifecycle.get("contract_version") != LIFECYCLE_CONTRACT:
        return lifecycle_path

    if lifecycle.get("contract_version") != LIFECYCLE_CONTRACT:
        add_finding(
            findings,
            "LIFECYCLE_SCHEMA_INVALID",
            f"coordinator_lifecycle_transition.contract_version must be {LIFECYCLE_CONTRACT}",
        )
    for field in ("prerequisite", "deadline"):
        if not isinstance(lifecycle.get(field), str) or not lifecycle[field].strip():
            add_finding(
                findings,
                "LIFECYCLE_SCHEMA_INVALID",
                f"coordinator_lifecycle_transition.{field} must be a nonempty string",
            )

    precondition = lifecycle.get("precondition")
    if not isinstance(precondition, dict):
        add_finding(
            findings,
            "LIFECYCLE_PRECONDITION_INVALID",
            "lifecycle precondition must bind planned status and the exact pre-transition file identity",
        )
    else:
        if precondition.get("campaign_status") != "planned":
            add_finding(
                findings,
                "LIFECYCLE_PRECONDITION_INVALID",
                "lifecycle precondition campaign_status must be planned",
            )
        if not isinstance(precondition.get("file_identity"), str) or not SHA256_IDENTITY.fullmatch(
            precondition["file_identity"]
        ):
            add_finding(
                findings,
                "LIFECYCLE_PRECONDITION_INVALID",
                "lifecycle precondition file_identity must be an exact lowercase sha256 identity",
            )

    transition_time = lifecycle.get("transition_time")
    expected_time = {
        "capture": "once_after_accepted_acknowledgment",
        "format": "RFC3339",
        "timezone": "UTC",
    }
    if transition_time != expected_time:
        add_finding(
            findings,
            "LIFECYCLE_TIME_RULE_INVALID",
            "transition_time must capture once after accepted acknowledgment using RFC3339 UTC",
        )

    allowed_diff = lifecycle.get("allowed_field_diff")
    expected_diff = {
        "campaign_status": {"from": "planned", "to": "running"},
        "generated.at": {"derive": "transition_time"},
        "updated": {
            "derive": "calendar_date",
            "source": "transition_time",
            "timezone": "UTC",
        },
    }
    if allowed_diff != expected_diff:
        add_finding(
            findings,
            "LIFECYCLE_DIFF_INVALID",
            "allowed_field_diff must contain only planned-to-running status, generated.at from transition_time, and updated as the UTC date of the same transition_time",
        )

    if lifecycle.get("all_other_bytes") != "unchanged":
        add_finding(
            findings,
            "LIFECYCLE_DIFF_INVALID",
            "all_other_bytes must be unchanged",
        )
    if lifecycle.get("on_failure") != "block_before_work_and_spend":
        add_finding(
            findings,
            "LIFECYCLE_FAILURE_RULE_INVALID",
            "on_failure must be block_before_work_and_spend",
        )
    return lifecycle_path


def path_like_frozen_entries(
    document: dict[str, Any], phase: str
) -> tuple[list[PathSpec], list[str]]:
    """Read machine-addressable frozen paths, with legacy prose allowed only in audit mode."""
    values = document.get("execution_frozen_inputs", [])
    if values is None:
        return [], []
    if not isinstance(values, list):
        return [], ["execution_frozen_inputs must be a list"]
    parsed: list[PathSpec] = []
    errors: list[str] = []
    for index, value in enumerate(values):
        if isinstance(value, dict) and "path" in value:
            try:
                parsed.append(parse_path_entry(value, "execution_frozen_inputs"))
            except ValueError as exc:
                errors.append(f"execution_frozen_inputs[{index}]: {exc}")
            if phase != "audit" and value.get("scope") not in {"file", "subtree"}:
                errors.append(
                    f"execution_frozen_inputs[{index}] must declare scope as file or subtree"
                )
            if phase != "audit" and not (
                isinstance(value.get("identity"), str) and value["identity"].strip()
            ):
                errors.append(
                    f"execution_frozen_inputs[{index}] must declare an immutable identity"
                )
        elif phase == "audit" and isinstance(value, str) and re.match(
            r"^[A-Za-z0-9_.-]+/[^ ]+/?$", value.strip()
        ):
            try:
                parsed.append(normalize_path(value))
            except ValueError as exc:
                errors.append(f"execution_frozen_inputs[{index}]: {exc}")
        elif phase != "audit":
            errors.append(
                f"execution_frozen_inputs[{index}] must be a mapping with path, scope, and identity"
            )
    return parsed, errors


def validate_traceability(
    document: dict[str, Any],
    phase: str,
    repo_root: Path | None,
    worker_paths: list[PathSpec],
    frozen_paths: list[PathSpec],
    findings: list[dict[str, str]],
) -> None:
    profile = document.get("design_profile")
    if profile not in {"module", "system"}:
        return

    work_plan_value = document.get("work_plan")
    if not isinstance(work_plan_value, str) or not work_plan_value.strip():
        add_finding(
            findings,
            "WORK_PLAN_REQUIRED",
            "module or system packet requires a work_plan path",
        )
    else:
        work_plan: PathSpec | None = None
        try:
            work_plan = normalize_path(work_plan_value)
            for frozen_path in frozen_paths:
                if covers(frozen_path, work_plan):
                    add_finding(
                        findings,
                        "WHOLE_WORK_PLAN_FROZEN",
                        f"execution-frozen path {frozen_path.render()} contains mutable work plan {work_plan.render()}",
                    )
        except ValueError as exc:
            add_finding(findings, "TRACEABILITY_SCHEMA_INVALID", str(exc))

        if repo_root is not None and work_plan is not None:
            live_work_plan = repo_root / work_plan.path
            try:
                work_text = live_work_plan.read_text()
                if not work_text.startswith("---\n"):
                    raise ValueError("missing YAML frontmatter")
                _, frontmatter_text, _ = work_text.split("---", 2)
                frontmatter = yaml.safe_load(frontmatter_text)
                if not isinstance(frontmatter, dict):
                    raise ValueError("frontmatter must be a YAML mapping")
            except (OSError, ValueError, yaml.YAMLError) as exc:
                add_finding(
                    findings,
                    "WORK_PLAN_UNREADABLE",
                    f"cannot read {work_plan.path} frontmatter: {exc}",
                )
            else:
                for field, expected in {
                    "plan_revision": document.get("work_plan_revision"),
                    "design_contract_identity": document.get("design_contract_identity"),
                }.items():
                    if frontmatter.get(field) != expected:
                        add_finding(
                            findings,
                            "WORK_PLAN_BINDING_MISMATCH",
                            f"work plan {field} {frontmatter.get(field)!r} does not match packet {expected!r}",
                        )
                if "development_authorization" in frontmatter:
                    add_finding(
                        findings,
                        "WORK_PLAN_OWNS_AUTHORIZATION",
                        "current development authorization must be absent from WORK.md",
                    )

    revision = document.get("work_plan_revision")
    if not isinstance(revision, int) or isinstance(revision, bool) or revision < 1:
        add_finding(
            findings,
            "WORK_PLAN_REVISION_INVALID",
            "module or system packet requires a positive work_plan_revision",
        )
    identity = document.get("design_contract_identity")
    if not isinstance(identity, str) or not identity.strip():
        add_finding(
            findings,
            "DESIGN_CONTRACT_IDENTITY_INVALID",
            "module or system packet requires design_contract_identity",
        )

    binding = document.get("design_traceability")
    if not isinstance(binding, dict):
        add_finding(
            findings,
            "TRACEABILITY_REQUIRED",
            "module or system packet requires design_traceability mapping",
        )
        return

    path_value = binding.get("path")
    expected_sha256 = binding.get("sha256")
    if not isinstance(path_value, str) or not isinstance(expected_sha256, str):
        add_finding(
            findings,
            "TRACEABILITY_SCHEMA_INVALID",
            "design_traceability requires path and sha256 strings",
        )
        return
    if repo_root is None:
        return

    try:
        traceability_path = normalize_path(path_value)
    except ValueError as exc:
        add_finding(findings, "TRACEABILITY_SCHEMA_INVALID", str(exc))
        return

    if not any(covers(frozen_path, traceability_path) for frozen_path in frozen_paths):
        add_finding(
            findings,
            "TRACEABILITY_NOT_FROZEN",
            f"design traceability {traceability_path.render()} is absent from execution-frozen inputs",
        )
    live_path = repo_root / traceability_path.path
    try:
        traceability_bytes = live_path.read_bytes()
        traceability = yaml.safe_load(traceability_bytes)
    except (OSError, yaml.YAMLError) as exc:
        add_finding(
            findings,
            "TRACEABILITY_UNREADABLE",
            f"cannot read {traceability_path.path}: {exc}",
        )
        return

    actual_sha256 = hashlib.sha256(traceability_bytes).hexdigest()
    if actual_sha256 != expected_sha256.removeprefix("sha256:"):
        add_finding(
            findings,
            "TRACEABILITY_IDENTITY_MISMATCH",
            f"{traceability_path.path} has SHA-256 {actual_sha256}, expected {expected_sha256}",
        )
    if not isinstance(traceability, dict):
        add_finding(
            findings,
            "TRACEABILITY_SCHEMA_INVALID",
            f"{traceability_path.path} must contain a YAML mapping",
        )
        return

    expected_bindings = {
        "plan_revision": document.get("work_plan_revision"),
        "design_contract_identity": document.get("design_contract_identity"),
    }
    for field, expected in expected_bindings.items():
        if traceability.get(field) != expected:
            add_finding(
                findings,
                "TRACEABILITY_BINDING_MISMATCH",
                f"traceability {field} {traceability.get(field)!r} does not match packet {expected!r}",
            )

    if isinstance(work_plan_value, str):
        try:
            expected_work_id = normalize_path(work_plan_value).path.rsplit("/", 2)[-2]
            if traceability.get("work_id") != expected_work_id:
                add_finding(
                    findings,
                    "TRACEABILITY_BINDING_MISMATCH",
                    f"traceability work_id {traceability.get('work_id')!r} does not match packet work plan {expected_work_id!r}",
                )
        except (IndexError, ValueError):
            pass

    batches = traceability.get("batches")
    batch_id = document.get("batch_id")
    batch = batches.get(batch_id) if isinstance(batches, dict) else None
    if not isinstance(batch, dict):
        add_finding(
            findings,
            "TRACEABILITY_BATCH_MISSING",
            f"traceability has no mapping for batch {batch_id}",
        )
        return
    delivery_identity = batch.get("delivery_identity")
    if not isinstance(delivery_identity, str) or not delivery_identity.strip():
        add_finding(
            findings,
            "TRACEABILITY_SCHEMA_INVALID",
            f"traceability batch {batch_id} requires delivery_identity",
        )
    traced_inputs = batch.get("required_design_inputs")
    packet_inputs = document.get("required_design_inputs")
    if not isinstance(traced_inputs, list) or not traced_inputs:
        add_finding(
            findings,
            "TRACEABILITY_SCHEMA_INVALID",
            f"traceability batch {batch_id} requires nonempty required_design_inputs",
        )
    elif traced_inputs != packet_inputs:
        add_finding(
            findings,
            "TRACEABILITY_DESIGN_INPUT_MISMATCH",
            f"traceability required_design_inputs for {batch_id} do not exactly match the packet",
        )
    destinations = batch.get("evidence_destinations")
    if not isinstance(destinations, list) or not destinations:
        add_finding(
            findings,
            "TRACEABILITY_SCHEMA_INVALID",
            f"traceability batch {batch_id} requires nonempty evidence_destinations",
        )
        return
    for index, destination in enumerate(destinations):
        try:
            target = parse_path_entry(destination, "evidence_destinations")
        except ValueError as exc:
            add_finding(
                findings,
                "TRACEABILITY_SCHEMA_INVALID",
                f"evidence_destinations[{index}]: {exc}",
            )
            continue
        if not any(covers(worker_path, target) for worker_path in worker_paths):
            add_finding(
                findings,
                "W_EVIDENCE_DESTINATION_UNASSIGNED",
                f"W evidence destination {target.render()} is absent from worker write paths",
            )


def validate(
    document: dict[str, Any], phase: str, repo_root: Path | None = None
) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    parse_errors: list[str] = []

    validate_identity_contract(document, phase, repo_root, findings)
    validate_canonical_identity_ownership(document, phase, findings)
    validate_engineering_check_plan(document, phase, repo_root, findings)

    allowed_code, errors = parse_path_list(document, "allowed_code_paths")
    parse_errors.extend(errors)
    artifacts, errors = parse_path_list(document, "artifact_paths")
    parse_errors.extend(errors)
    forbidden, errors = parse_path_list(document, "worker_forbidden_paths")
    parse_errors.extend(errors)
    frozen, errors = path_like_frozen_entries(document, phase)
    parse_errors.extend(errors)

    acknowledgment, errors = parse_single_path(document, "acknowledgment_path")
    parse_errors.extend(errors)
    result, errors = parse_single_path(document, "result_packet_path")
    parse_errors.extend(errors)
    result_validation, errors = parse_single_path(
        document,
        "result_validation_path",
        required=phase in {"draft", "frozen"},
    )
    parse_errors.extend(errors)
    manifest, errors = parse_single_path(
        document,
        "candidate_manifest_path",
        required=bool(document.get("changes_executable_candidate")),
    )
    parse_errors.extend(errors)
    package_inventory, errors = parse_single_path(
        document,
        "candidate_package_inventory_path",
        required=bool(document.get("changes_executable_candidate")),
    )
    parse_errors.extend(errors)
    candidate_root, errors = parse_single_path(
        document,
        "candidate_root_path",
        required=bool(document.get("changes_executable_candidate")),
    )
    parse_errors.extend(errors)
    if candidate_root is not None:
        candidate_root = PathSpec(candidate_root.path, True)
    if (
        phase != "audit"
        and not document.get("changes_executable_candidate")
        and document.get("candidate_root_path") is not None
    ):
        add_finding(
            findings,
            "CANDIDATE_ROOT_OUTSIDE_MATERIALIZATION",
            "candidate_root_path must be null when changes_executable_candidate is false",
        )
    packet, errors = parse_single_path(document, "packet_path")
    parse_errors.extend(errors)
    execution_start, errors = parse_single_path(document, "execution_start_path")
    parse_errors.extend(errors)
    execution_baseline_root, errors = parse_single_path(
        document,
        "execution_baseline_root",
        required=phase in {"draft", "frozen"},
    )
    parse_errors.extend(errors)
    if execution_baseline_root is not None:
        execution_baseline_root = PathSpec(execution_baseline_root.path, True)
    preflight, errors = parse_single_path(
        document,
        "packet_preflight_path",
        required=phase in {"draft", "frozen"},
    )
    parse_errors.extend(errors)

    for error in parse_errors:
        add_finding(findings, "INVALID_PATH_SCHEMA", error)

    worker_paths = list(allowed_code) + list(artifacts)
    if candidate_root is not None:
        worker_paths.append(candidate_root)
    for path in (acknowledgment, result_validation, result, manifest, package_inventory):
        if path is not None:
            worker_paths.append(path)
    worker_paths = sorted(set(worker_paths))

    if candidate_root is not None and not any(
        covers(artifact, candidate_root) for artifact in artifacts
    ):
        add_finding(
            findings,
            "CANDIDATE_ROOT_NOT_ASSIGNED",
            "candidate_root_path must be covered by artifact_paths",
        )
    coordinator_paths = [
        path
        for path in (packet, execution_baseline_root, execution_start, preflight)
        if path is not None
    ]

    validate_traceability(document, phase, repo_root, worker_paths, frozen, findings)

    worker_output_roles = [
        path
        for path in (acknowledgment, result_validation, result, manifest)
        if path is not None
    ]
    for index, left in enumerate(worker_output_roles):
        for right in worker_output_roles[index + 1 :]:
            if overlaps(left, right):
                add_finding(
                    findings,
                    "WORKER_OUTPUT_ROLE_OVERLAP",
                    f"required worker outputs {left.render()} and {right.render()} overlap",
                )

    for worker in worker_paths:
        for denied in forbidden:
            if overlaps(worker, denied):
                add_finding(
                    findings,
                    "WORKER_FORBIDDEN_OVERLAP",
                    f"worker path {worker.render()} overlaps forbidden path {denied.render()}",
                )

    if execution_start is not None:
        for worker in worker_paths:
            if overlaps(execution_start, worker):
                add_finding(
                    findings,
                    "EXECUTION_START_WORKER_OVERLAP",
                    f"Coordinator execution-start {execution_start.render()} overlaps worker path {worker.render()}",
                )

    if execution_baseline_root is not None:
        for worker in worker_paths:
            if overlaps(execution_baseline_root, worker):
                add_finding(
                    findings,
                    "EXECUTION_BASELINE_WORKER_OVERLAP",
                    f"Coordinator execution-baseline root {execution_baseline_root.render()} overlaps worker path {worker.render()}",
                )

    if packet is not None:
        for worker in worker_paths:
            if overlaps(packet, worker):
                add_finding(
                    findings,
                    "PACKET_WORKER_OVERLAP",
                    f"Coordinator packet {packet.render()} overlaps worker path {worker.render()}",
                )

    if preflight is not None:
        for worker in worker_paths:
            if overlaps(preflight, worker):
                add_finding(
                    findings,
                    "PREFLIGHT_WORKER_OVERLAP",
                    f"Coordinator preflight {preflight.render()} overlaps worker path {worker.render()}",
                )

    lifecycle = document.get("coordinator_lifecycle_transition")
    lifecycle_path = validate_lifecycle_transition(lifecycle, phase, findings)
    if lifecycle_path is not None:
        coordinator_paths.append(lifecycle_path)

    if lifecycle_path is not None:
        for worker in worker_paths:
            if overlaps(lifecycle_path, worker):
                add_finding(
                    findings,
                    "LIFECYCLE_WORKER_OVERLAP",
                    f"Coordinator lifecycle output {lifecycle_path.render()} overlaps worker path {worker.render()}",
                )

    for index, left in enumerate(coordinator_paths):
        for right in coordinator_paths[index + 1 :]:
            if overlaps(left, right):
                add_finding(
                    findings,
                    "COORDINATOR_PATH_OVERLAP",
                    f"Coordinator outputs {left.render()} and {right.render()} overlap",
                )

    post_packet_coordinator_paths = [
        path
        for path in (execution_baseline_root, execution_start, preflight, lifecycle_path)
        if path is not None
    ]
    for frozen_path in frozen:
        for worker in worker_paths:
            if overlaps(frozen_path, worker):
                add_finding(
                    findings,
                    "FROZEN_WORKER_OVERLAP",
                    f"frozen path {frozen_path.render()} contains worker output {worker.render()}",
                )
        for coordinator in post_packet_coordinator_paths:
            if overlaps(frozen_path, coordinator):
                add_finding(
                    findings,
                    "FROZEN_COORDINATOR_OVERLAP",
                    f"frozen path {frozen_path.render()} contains Coordinator lifecycle output {coordinator.render()}",
                )

    required_aliases = {
        "acknowledgment_path": ("acknowledgment", "acknowledgement"),
        "result_validation_path": ("result validation", "result preflight"),
        "result_packet_path": ("result packet",),
        "candidate_manifest_path": ("candidate manifest",),
        "candidate_package_inventory_path": ("candidate package inventory", "package inventory"),
    }
    prohibited = document.get("prohibited_actions", [])
    if not isinstance(prohibited, list):
        add_finding(findings, "INVALID_PROHIBITIONS", "prohibited_actions must be a list")
    else:
        for index, action in enumerate(prohibited):
            if not isinstance(action, str) or not WRITE_VERBS.search(action):
                continue
            lowered = action.lower()
            for field, aliases in required_aliases.items():
                if document.get(field) is not None and any(alias in lowered for alias in aliases):
                    add_finding(
                        findings,
                        "PROHIBITS_REQUIRED_WORKER_OUTPUT",
                        f"prohibited_actions[{index}] denies required worker output {field}: {action}",
                    )

    payload_sha256 = hashlib.sha256(canonical_payload(document)).hexdigest()
    expected_packet_id = computed_packet_id(document, payload_sha256)
    result_contract_packet = dict(document)
    result_contract_packet["packet_id"] = expected_packet_id
    result_contract = RESULT_CONTRACT_VALIDATOR.validate_packet_result_contract(
        result_contract_packet, repo_root
    )
    for finding in result_contract["findings"]:
        add_finding(findings, finding["code"], finding["detail"])
    for advisory in result_contract.get("advisories", []):
        add_finding(findings, advisory["code"], advisory["detail"])

    declared_packet_id = document.get("packet_id")
    if phase == "draft" and declared_packet_id is not None:
        add_finding(findings, "DRAFT_ALREADY_FROZEN", "draft preflight requires packet_id to be absent")
    if phase == "frozen":
        if declared_packet_id is None:
            add_finding(findings, "PACKET_ID_MISSING", "frozen preflight requires packet_id")
        elif declared_packet_id != expected_packet_id:
            add_finding(
                findings,
                "PACKET_ID_MISMATCH",
                f"declared {declared_packet_id} does not equal computed {expected_packet_id}",
            )
    elif phase == "audit" and declared_packet_id not in {None, expected_packet_id}:
        add_finding(
            findings,
            "PACKET_ID_MISMATCH",
            f"declared {declared_packet_id} does not equal computed {expected_packet_id}",
        )

    finding_summary = finalize_findings(findings)
    actionable_findings = finding_summary["findings"]
    finding_codes = {item["code"] for item in actionable_findings}
    coordinator_worker_codes = {
        "EXECUTION_START_WORKER_OVERLAP",
        "EXECUTION_BASELINE_WORKER_OVERLAP",
        "PACKET_WORKER_OVERLAP",
        "PREFLIGHT_WORKER_OVERLAP",
        "LIFECYCLE_WORKER_OVERLAP",
    }
    packet_identity_codes = {
        "DRAFT_ALREADY_FROZEN",
        "PACKET_ID_MISSING",
        "PACKET_ID_MISMATCH",
    }
    lifecycle_contract_codes = {
        "LIFECYCLE_SCHEMA_INVALID",
        "LIFECYCLE_PRECONDITION_INVALID",
        "LIFECYCLE_TIME_RULE_INVALID",
        "LIFECYCLE_DIFF_INVALID",
        "LIFECYCLE_FAILURE_RULE_INVALID",
    }
    result_document: dict[str, Any] = {
        "validator": VALIDATOR,
        "batch_id": document.get("batch_id"),
        "packet_path": document.get("packet_path"),
        "packet_payload_sha256": payload_sha256,
        "computed_packet_id": expected_packet_id,
        "packet_structure_ready": finding_summary["ready"],
        "result_contract_probe": {
            "validator": result_contract["validator"],
            "validation_id": result_contract["probe_validation_id"],
        },
        "checks": {
            "worker_write_vs_forbidden": (
                "FAIL" if "WORKER_FORBIDDEN_OVERLAP" in finding_codes else "PASS"
            ),
            "coordinator_outputs_vs_worker": (
                "FAIL" if finding_codes & coordinator_worker_codes else "PASS"
            ),
            "coordinator_path_exclusivity": (
                "FAIL" if "COORDINATOR_PATH_OVERLAP" in finding_codes else "PASS"
            ),
            "worker_output_role_exclusivity": (
                "FAIL" if "WORKER_OUTPUT_ROLE_OVERLAP" in finding_codes else "PASS"
            ),
            "frozen_paths_vs_outputs": (
                "FAIL"
                if finding_codes & {"FROZEN_WORKER_OVERLAP", "FROZEN_COORDINATOR_OVERLAP"}
                else "PASS"
            ),
            "required_outputs_vs_prohibitions": (
                "FAIL"
                if finding_codes
                & {"INVALID_PROHIBITIONS", "PROHIBITS_REQUIRED_WORKER_OUTPUT"}
                else "PASS"
            ),
            "packet_identity": (
                "FAIL" if finding_codes & packet_identity_codes else "PASS"
            ),
            "path_schema": (
                "FAIL" if "INVALID_PATH_SCHEMA" in finding_codes else "PASS"
            ),
            "lifecycle_transition_contract": (
                "FAIL" if finding_codes & lifecycle_contract_codes else "PASS"
            ),
            "result_contract_compatibility": (
                "PASS" if result_contract["result_contract_ready"] else "FAIL"
            ),
            "identity_and_authority_contract": (
                "FAIL"
                if finding_codes
                & {
                    "REQUIRED_FIELD_MISSING",
                    "IDENTITY_CONTRACT_INVALID",
                    "PACKET_FIELD_INVALID",
                    "WORKFLOW_CONTRACTS_RETIRED",
                    "SOURCE_BASE_IDENTITY_INVALID",
                    "SOURCE_BASE_BINDING_REQUIRED",
                    "SOURCE_BASE_BINDING_INVALID",
                    "DESIGN_PROFILE_INVALID",
                    "DESIGN_CONTRACT_IDENTITY_INVALID",
                    "DESIGN_CONTRACT_BINDING_REQUIRED",
                    "DESIGN_CONTRACT_BINDING_INVALID",
                    "DEVELOPMENT_AUTHORIZATION_TARGET_INVALID",
                    "DEVELOPMENT_AUTHORIZATION_TARGET_MISMATCH",
                    "AUTHORIZATION_BOUNDARY_INVALID",
                }
                else "PASS"
            ),
            "engineering_execution_contract": (
                "FAIL"
                if finding_codes
                & {
                    "ENGINEERING_CHECK_PLAN_REQUIRED",
                    "ENGINEERING_CHECK_PLAN_INVALID",
                    "ENGINEERING_CHECK_SCHEMA_INVALID",
                    "ENGINEERING_EFFECT_LIMIT_INVALID",
                    "ENGINEERING_EFFECT_CONFLICT",
                    "ENGINEERING_EFFECT_EVIDENCE_INVALID",
                }
                else "PASS"
            ),
            "work_plan_traceability": (
                "FAIL"
                if finding_codes
                & {
                    "TRACEABILITY_REQUIRED",
                    "TRACEABILITY_SCHEMA_INVALID",
                    "TRACEABILITY_UNREADABLE",
                    "TRACEABILITY_IDENTITY_MISMATCH",
                    "TRACEABILITY_BINDING_MISMATCH",
                    "TRACEABILITY_BATCH_MISSING",
                    "TRACEABILITY_DESIGN_INPUT_MISMATCH",
                    "TRACEABILITY_NOT_FROZEN",
                    "W_EVIDENCE_DESTINATION_UNASSIGNED",
                    "WHOLE_WORK_PLAN_FROZEN",
                    "WORK_PLAN_REQUIRED",
                    "WORK_PLAN_REVISION_INVALID",
                    "DESIGN_CONTRACT_IDENTITY_INVALID",
                    "WORK_PLAN_BINDING_MISMATCH",
                    "WORK_PLAN_OWNS_AUTHORIZATION",
                    "WORK_PLAN_UNREADABLE",
                }
                else "PASS"
            ),
        },
        "normalized_ownership": {
            "worker_write_paths": [path.render() for path in worker_paths],
            "worker_forbidden_paths": [path.render() for path in sorted(set(forbidden))],
            "coordinator_paths": [path.render() for path in sorted(set(coordinator_paths))],
            "execution_frozen_paths": [path.render() for path in sorted(set(frozen))],
        },
        "findings": actionable_findings,
        "blocking_findings": finding_summary["blocking_findings"],
        "repair_findings": finding_summary["repair_findings"],
        "advisories": finding_summary["advisories"],
        "finding_effect_counts": finding_summary["finding_effect_counts"],
    }
    canonical = json.dumps(result_document, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    preflight_sha256 = hashlib.sha256(canonical).hexdigest()
    result_document["preflight_id"] = f"{document.get('batch_id', 'UNKNOWN')}-packet-preflight-sha256:{preflight_sha256}"
    return result_document


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packet", type=Path)
    parser.add_argument("--phase", choices=("draft", "frozen", "audit"), default="frozen")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.phase != "audit":
        print("legacy packet writer is closed; use frontier_provenance_cli.py", file=sys.stderr)
        return 2
    try:
        document = yaml.safe_load(args.packet.read_text())
    except (OSError, yaml.YAMLError) as exc:
        print(f"cannot read packet: {exc}", file=sys.stderr)
        return 2
    if not isinstance(document, dict):
        print("packet must be a YAML mapping", file=sys.stderr)
        return 2
    result = validate(document, args.phase, args.repo_root.resolve())
    rendered = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered)
    else:
        sys.stdout.write(rendered)
    return 0 if result["packet_structure_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
