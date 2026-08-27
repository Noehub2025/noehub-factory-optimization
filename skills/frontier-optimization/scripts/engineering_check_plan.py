"""Normalize the current project engineering-check plan for all consumers."""

from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

import yaml

from identity_bindings import IdentityBindingError, normalize_repo_path, resolve_repo_file
from validate_candidate_package import validate_candidate_inventory


CURRENT_PLAN_CONTRACT = "frontier-project-engineering-check-plan/1"
CHECK_REPORT_CONTRACT = "frontier-engineering-check-report/1"
RESOURCE_OBSERVATION_CONTRACT = "frontier-project-local-resource-observation/1"
SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")
LIMIT_FIELDS = {
    "cumulative_local_wall_seconds",
    "per_command_timeout_seconds",
    "processes",
    "new_output_bytes",
    "proposal_attempts",
    "development_schedules",
    "evaluator_runs",
    "games",
    "sealed_inputs",
    "paid_actions",
}


class EngineeringCheckPlanError(ValueError):
    """The declared engineering-check plan cannot be interpreted safely."""


def _is_nonnegative_finite_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and (not isinstance(value, float) or math.isfinite(value))
        and value >= 0
    )


def _digest(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise EngineeringCheckPlanError(f"{field} must be a SHA-256 identity")
    digest = value.removeprefix("sha256:")
    if SHA256_HEX.fullmatch(digest) is None:
        raise EngineeringCheckPlanError(f"{field} must be a lowercase SHA-256 identity")
    return digest


def _frozen_plan_digest(batch_plan: dict[str, Any], plan_path: str) -> str:
    matches = [
        item
        for item in batch_plan.get("execution_frozen_inputs", [])
        if isinstance(item, dict)
        and item.get("path") == plan_path
        and item.get("scope") == "file"
    ]
    if len(matches) != 1:
        raise EngineeringCheckPlanError(
            "engineering_check_plan must have exactly one file binding in execution_frozen_inputs"
        )
    return _digest(matches[0].get("identity"), "engineering check plan identity")


def normalize_current_plan_bytes(
    batch_plan: dict[str, Any],
    plan_path: str,
    raw: bytes,
) -> dict[str, Any]:
    """Return one task-neutral projection of a frozen current-format plan."""

    try:
        canonical_path = normalize_repo_path(plan_path, "engineering_check_plan")
    except IdentityBindingError as exc:
        raise EngineeringCheckPlanError(str(exc)) from exc
    if canonical_path != plan_path:
        raise EngineeringCheckPlanError(
            "engineering_check_plan must use its canonical repository-relative path"
        )
    if hashlib.sha256(raw).hexdigest() != _frozen_plan_digest(batch_plan, plan_path):
        raise EngineeringCheckPlanError(
            "engineering check plan bytes do not match the frozen input binding"
        )
    try:
        document = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise EngineeringCheckPlanError(f"engineering check plan is invalid YAML: {exc}") from exc
    if not isinstance(document, dict):
        raise EngineeringCheckPlanError("engineering check plan must be a mapping")
    if document.get("contract_version") != CURRENT_PLAN_CONTRACT:
        raise EngineeringCheckPlanError(
            f"external engineering check plan must use {CURRENT_PLAN_CONTRACT}"
        )
    if document.get("batch_id") != batch_plan.get("batch_id"):
        raise EngineeringCheckPlanError(
            "engineering check plan and batch plan name different batches"
        )
    if document.get("consequence") != "engineering evidence only":
        raise EngineeringCheckPlanError(
            "engineering check plan consequence must be engineering evidence only"
        )

    limits = document.get("limits")
    if not isinstance(limits, dict) or set(limits) != LIMIT_FIELDS:
        raise EngineeringCheckPlanError(
            "engineering check plan limits must contain exactly the current bounded resource fields"
        )
    for name, value in limits.items():
        if not _is_nonnegative_finite_number(value):
            raise EngineeringCheckPlanError(f"engineering check limit {name!r} must be nonnegative")
    for name in (
        "cumulative_local_wall_seconds",
        "per_command_timeout_seconds",
        "processes",
        "new_output_bytes",
        "proposal_attempts",
    ):
        if limits[name] <= 0:
            raise EngineeringCheckPlanError(f"engineering check limit {name!r} must be positive")

    formal_units = document.get("formal_units")
    if not isinstance(formal_units, list) or not formal_units:
        raise EngineeringCheckPlanError("engineering check plan formal_units must be nonempty")
    units: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, unit in enumerate(formal_units):
        if not isinstance(unit, dict):
            raise EngineeringCheckPlanError(f"formal_units[{index}] must be a mapping")
        unit_id = unit.get("id")
        if not isinstance(unit_id, str) or not unit_id.strip() or unit_id in seen:
            raise EngineeringCheckPlanError(
                f"formal_units[{index}].id must be nonempty and unique"
            )
        seen.add(unit_id)
        argv = unit.get("argv")
        if argv is not None and (
            not isinstance(argv, list)
            or not argv
            or not all(isinstance(part, str) and part for part in argv)
        ):
            raise EngineeringCheckPlanError(
                f"formal_units[{index}].argv must be a nonempty string list when present"
            )
        if argv is None and not isinstance(unit.get("command_kind"), str):
            raise EngineeringCheckPlanError(
                f"formal_units[{index}] requires argv or command_kind"
            )
        units.append({"id": unit_id, "argv": argv})

    return {
        "family": "current-external",
        "contract_version": CURRENT_PLAN_CONTRACT,
        "path": plan_path,
        "file_sha256": hashlib.sha256(raw).hexdigest(),
        "batch_id": document["batch_id"],
        "limits": dict(limits),
        "units": units,
    }


def load_current_plan(batch_plan: dict[str, Any], repo_root: Path) -> dict[str, Any] | None:
    """Load the external current plan, or return None for a historical inline plan."""

    reference = batch_plan.get("engineering_check_plan")
    if isinstance(reference, dict):
        return None
    if not isinstance(reference, str) or not reference.strip():
        raise EngineeringCheckPlanError(
            "engineering_check_plan must name one frozen external current-format plan"
        )
    try:
        normalized, path = resolve_repo_file(
            repo_root.resolve(), reference, "engineering_check_plan"
        )
        raw = path.read_bytes()
    except (IdentityBindingError, OSError) as exc:
        raise EngineeringCheckPlanError(f"cannot read engineering check plan: {exc}") from exc
    return normalize_current_plan_bytes(batch_plan, normalized, raw)


def _command_sha256(argv: Any) -> str | None:
    if not isinstance(argv, list) or not argv or not all(
        isinstance(part, str) and part for part in argv
    ):
        return None
    return hashlib.sha256(
        json.dumps(argv, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _load_binding(
    root: Path,
    binding: Any,
    *,
    contract: str,
    role: str,
) -> tuple[dict[str, Any], str, str]:
    if (
        not isinstance(binding, dict)
        or set(binding) != {"contract_version", "path", "file_sha256"}
        or binding.get("contract_version") != contract
        or not isinstance(binding.get("path"), str)
    ):
        raise EngineeringCheckPlanError(
            f"{role} must be one exact {contract} file binding"
        )
    expected = _digest(binding.get("file_sha256"), f"{role}.file_sha256")
    try:
        normalized, path = resolve_repo_file(root, binding["path"], f"{role}.path")
        raw = path.read_bytes()
        document = yaml.safe_load(raw)
    except (IdentityBindingError, OSError, yaml.YAMLError) as exc:
        raise EngineeringCheckPlanError(f"cannot read {role}: {exc}") from exc
    observed = hashlib.sha256(raw).hexdigest()
    if observed != expected:
        raise EngineeringCheckPlanError(
            f"{role} has SHA-256 {observed}, expected {expected}"
        )
    if not isinstance(document, dict) or document.get("contract_version") != contract:
        raise EngineeringCheckPlanError(f"{role} must use {contract}")
    return document, normalized, observed


def _verify_content_binding(root: Path, binding: Any, role: str) -> bytes:
    if (
        not isinstance(binding, dict)
        or not isinstance(binding.get("path"), str)
        or not isinstance(binding.get("file_sha256"), str)
    ):
        raise EngineeringCheckPlanError(f"{role} requires path and file_sha256")
    expected = _digest(binding["file_sha256"], f"{role}.file_sha256")
    try:
        _, path = resolve_repo_file(root, binding["path"], f"{role}.path")
        raw = path.read_bytes()
    except (IdentityBindingError, OSError) as exc:
        raise EngineeringCheckPlanError(f"cannot read {role}: {exc}") from exc
    if hashlib.sha256(raw).hexdigest() != expected:
        raise EngineeringCheckPlanError(f"{role} SHA-256 does not match its binding")
    return raw


def _validated_inventory(
    root: Path,
    binding: Any,
    *,
    role: str,
    expected_candidate_id: Any,
) -> dict[str, Any]:
    """Load one path-bearing inventory and verify it against its own candidate root."""

    if not isinstance(binding, dict) or set(binding) != {
        "path",
        "inventory_id",
        "file_sha256",
    }:
        raise EngineeringCheckPlanError(
            f"{role} must contain exactly path, inventory_id, and file_sha256"
        )
    try:
        raw = _verify_content_binding(root, binding, role)
        document = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise EngineeringCheckPlanError(f"cannot parse {role}: {exc}") from exc
    if not isinstance(document, dict):
        raise EngineeringCheckPlanError(f"{role} must be a mapping")

    validation = validate_candidate_inventory(
        root,
        document.get("candidate_root"),
        binding["path"],
        expected_candidate_id=expected_candidate_id,
        expected_inventory_id=binding["inventory_id"],
        expected_inventory_sha256=binding["file_sha256"],
    )
    if not validation.get("inventory_ready"):
        details = "; ".join(
            f"{finding.get('code')}: {finding.get('detail')}"
            for finding in validation.get("findings", [])
            if isinstance(finding, dict)
        )
        raise EngineeringCheckPlanError(f"{role} is invalid: {details}")
    return document


def _same_candidate_content(left: dict[str, Any], right: dict[str, Any]) -> bool:
    """Compare candidate bytes while intentionally excluding their publication roots."""

    return all(
        left.get(field) == right.get(field)
        for field in ("candidate_id", "package_sha256", "members")
    )


def validate_current_evidence(
    result: dict[str, Any],
    batch_plan: dict[str, Any],
    repo_root: Path,
) -> list[str]:
    """Validate current external-plan evidence without translating it to the legacy schema."""

    errors: list[str] = []
    try:
        normalized = load_current_plan(batch_plan, repo_root)
    except EngineeringCheckPlanError as exc:
        return [str(exc)]
    if normalized is None:
        return []

    bindings = result.get("engineering_validation")
    if not isinstance(bindings, list):
        return ["engineering_validation must be a list"]
    report_bindings = [
        item
        for item in bindings
        if isinstance(item, dict)
        and item.get("contract_version") == CHECK_REPORT_CONTRACT
    ]
    resource_bindings = [
        item
        for item in bindings
        if isinstance(item, dict)
        and item.get("contract_version") == RESOURCE_OBSERVATION_CONTRACT
    ]
    if len(report_bindings) != 1 or len(resource_bindings) != 1 or len(bindings) != 2:
        return [
            "current engineering_validation requires exactly one combined check report and one resource observation binding"
        ]
    try:
        report, _, report_digest = _load_binding(
            repo_root,
            report_bindings[0],
            contract=CHECK_REPORT_CONTRACT,
            role="combined check report",
        )
        observation, _, _ = _load_binding(
            repo_root,
            resource_bindings[0],
            contract=RESOURCE_OBSERVATION_CONTRACT,
            role="resource observation",
        )
    except EngineeringCheckPlanError as exc:
        return [str(exc)]

    batch_id = batch_plan.get("batch_id")
    for role, document in (("combined check report", report), ("resource observation", observation)):
        if document.get("batch_id") != batch_id:
            errors.append(f"{role} names a different batch")

    planned_units = normalized["units"]
    planned_ids = [unit["id"] for unit in planned_units]
    reported_checks = report.get("checks")
    reported_ids = [
        item.get("id") for item in reported_checks if isinstance(item, dict)
    ] if isinstance(reported_checks, list) else []
    if reported_ids != planned_ids or len(reported_ids) != len(reported_checks or []):
        errors.append("combined check report must contain every formal unit once and in frozen order")
        reported_checks = []
    if report.get("ordered_checks_complete") is not True or report.get("all_pass") is not True:
        errors.append("current publication requires an ordered all-pass combined check report")
    if report.get("official_candidate_created") is not False or report.get("publication_state") != "prepublication":
        errors.append("combined check report must preserve its prepublication state")

    timeout = normalized["limits"]["per_command_timeout_seconds"]
    formal_elapsed = 0.0
    for index, (planned, reported) in enumerate(zip(planned_units, reported_checks)):
        if not isinstance(reported, dict):
            errors.append(f"reported check {index} must be a mapping")
            continue
        if reported.get("result") != "pass" or reported.get("exit_status") != 0:
            errors.append(f"reported check {planned['id']!r} must pass with exit status zero")
        reported_argv_digest = reported.get("argv_sha256")
        if not isinstance(reported_argv_digest, str) or SHA256_HEX.fullmatch(reported_argv_digest) is None:
            errors.append(f"reported check {planned['id']!r} requires an argv SHA-256")
        expected_argv_digest = _command_sha256(planned.get("argv"))
        if expected_argv_digest is not None and reported_argv_digest != expected_argv_digest:
            errors.append(f"reported check {planned['id']!r} does not match the frozen argv")
        try:
            log_raw = _verify_content_binding(
                repo_root,
                {"path": reported.get("log"), "file_sha256": reported.get("log_sha256")},
                f"reported check {planned['id']!r} log",
            )
            log = json.loads(log_raw)
        except (EngineeringCheckPlanError, json.JSONDecodeError) as exc:
            errors.append(str(exc))
            log = None
        if isinstance(log, dict):
            log_argv_digest = _command_sha256(log.get("argv"))
            elapsed = log.get("elapsed_seconds")
            if (
                log_argv_digest != reported_argv_digest
                or log.get("argv_sha256") != reported_argv_digest
                or log.get("exit_status") != reported.get("exit_status")
                or log.get("timed_out") is not False
            ):
                errors.append(f"reported check {planned['id']!r} log does not match its summary")
            if not _is_nonnegative_finite_number(elapsed):
                errors.append(f"reported check {planned['id']!r} has invalid elapsed time")
            else:
                formal_elapsed += float(elapsed)
                if elapsed > timeout:
                    errors.append(f"reported check {planned['id']!r} exceeded its timeout")
        evidence_items = reported.get("evidence")
        if not isinstance(evidence_items, list):
            errors.append(f"reported check {planned['id']!r} evidence must be a list")
        else:
            for evidence_index, evidence in enumerate(evidence_items):
                try:
                    _verify_content_binding(
                        repo_root,
                        evidence,
                        f"reported check {planned['id']!r} evidence[{evidence_index}]",
                    )
                except EngineeringCheckPlanError as exc:
                    errors.append(str(exc))

    report_elapsed = report.get("formal_command_elapsed_seconds")
    if (
        not _is_nonnegative_finite_number(report_elapsed)
        or abs(float(report_elapsed) - formal_elapsed) > 1e-6
    ):
        errors.append("combined check report formal elapsed time must equal its verified logs")

    limits = normalized["limits"]
    observed_values = {
        "cumulative_local_wall_seconds": observation.get("release_to_observation_elapsed_seconds"),
        "processes": observation.get("processes_concurrent_maximum"),
        "new_output_bytes": (
            observation.get("payload_observed_before_this_receipt", {}).get("bytes")
            if isinstance(observation.get("payload_observed_before_this_receipt"), dict)
            else None
        ),
        "proposal_attempts": report.get("resource_accounting", {}).get("proposal_attempts")
        if isinstance(report.get("resource_accounting"), dict)
        else None,
        "development_schedules": observation.get("development_schedules"),
        "evaluator_runs": observation.get("evaluator_runs"),
        "games": observation.get("games"),
        "sealed_inputs": observation.get("sealed_inputs"),
        "paid_actions": observation.get("paid_actions"),
    }
    for name, value in observed_values.items():
        if not _is_nonnegative_finite_number(value):
            errors.append(f"resource observation {name!r} must be nonnegative")
        elif value > limits[name]:
            errors.append(f"resource observation {name!r} exceeds the frozen limit")
    if observation.get("within_limits") is not True:
        errors.append("resource observation must report within_limits: true")
    if observation.get("formal_command_elapsed_seconds") != report_elapsed:
        errors.append("resource observation and combined report disagree on formal elapsed time")
    report_accounting = report.get("resource_accounting")
    if isinstance(report_accounting, dict):
        for name in (
            "development_schedules",
            "evaluator_runs",
            "games",
            "sealed_inputs",
            "paid_actions",
        ):
            if report_accounting.get(name) != observation.get(name):
                errors.append(f"combined report and resource observation disagree on {name!r}")
        if report_accounting.get("processes_concurrent") != observation.get("processes_concurrent_maximum"):
            errors.append("combined report and resource observation disagree on concurrent processes")
        if report_accounting.get("execution_seconds_limit") != limits["cumulative_local_wall_seconds"]:
            errors.append("combined report does not preserve the frozen wall-time limit")
        if report_accounting.get("output_bytes_limit") != limits["new_output_bytes"]:
            errors.append("combined report does not preserve the frozen output limit")

    submitted_inventory: dict[str, Any] | None = None
    proposal = report.get("proposal")
    if not isinstance(proposal, dict):
        errors.append("combined check report requires the formal proposal binding")
    else:
        try:
            proposal_raw = _verify_content_binding(repo_root, proposal, "formal proposal")
            proposal_document = yaml.safe_load(proposal_raw)
        except (EngineeringCheckPlanError, yaml.YAMLError) as exc:
            errors.append(str(exc))
            proposal_document = None
        if isinstance(proposal_document, dict):
            inventory = proposal_document.get("package_inventory")
            if (
                proposal_document.get("batch_id") != batch_id
                or proposal_document.get("proposal_identity") != report.get("candidate_id")
                or not isinstance(inventory, dict)
                or inventory.get("inventory_id") != report.get("inventory_id")
            ):
                errors.append("formal proposal does not bind the reported candidate and inventory")
            elif report.get("snapshot_id") != f"sha256:{inventory.get('file_sha256')}":
                errors.append("combined check report snapshot does not bind the submitted inventory bytes")
            else:
                try:
                    submitted_inventory = _validated_inventory(
                        repo_root,
                        inventory,
                        role="submitted inventory",
                        expected_candidate_id=report.get("candidate_id"),
                    )
                except EngineeringCheckPlanError as exc:
                    errors.append(str(exc))
        else:
            errors.append("formal proposal must be a mapping")
        if proposal.get("proposal_attempts_incurred") != observed_values["proposal_attempts"]:
            errors.append("formal proposal and resource accounting disagree on proposal attempts")

    if result.get("candidate_identity") != report.get("candidate_id"):
        errors.append("result and combined check report name different candidate identities")
    manifest_path = result.get("candidate_manifest")
    if isinstance(manifest_path, str):
        try:
            _, path = resolve_repo_file(repo_root, manifest_path, "candidate_manifest")
            manifest = yaml.safe_load(path.read_bytes())
        except (IdentityBindingError, OSError, yaml.YAMLError) as exc:
            errors.append(f"cannot verify candidate manifest engineering evidence: {exc}")
        else:
            expected_binding = {
                "path": report_bindings[0]["path"],
                "file_sha256": report_digest,
            }
            actual = manifest.get("engineering_evidence") if isinstance(manifest, dict) else None
            if not isinstance(actual, list) or not any(
                isinstance(item, dict)
                and item.get("path") == expected_binding["path"]
                and item.get("file_sha256") == expected_binding["file_sha256"]
                for item in actual
            ):
                errors.append("candidate manifest does not bind the verified combined check report")
            manifest_inventory = manifest.get("package_inventory") if isinstance(manifest, dict) else None
            if (
                not isinstance(manifest_inventory, dict)
                or manifest_inventory.get("path")
                != batch_plan.get("candidate_package_inventory_path")
            ):
                errors.append(
                    "official inventory path must equal the batch plan candidate_package_inventory_path"
                )
            else:
                try:
                    official_inventory = _validated_inventory(
                        repo_root,
                        manifest_inventory,
                        role="official inventory",
                        expected_candidate_id=report.get("candidate_id"),
                    )
                except EngineeringCheckPlanError as exc:
                    errors.append(str(exc))
                else:
                    if official_inventory.get("candidate_root") != batch_plan.get(
                        "candidate_root_path"
                    ):
                        errors.append(
                            "official inventory candidate_root must equal the batch plan candidate_root_path"
                        )
                    if submitted_inventory is None or not _same_candidate_content(
                        submitted_inventory, official_inventory
                    ):
                        errors.append(
                            "official inventory does not contain the exact reviewed submitted candidate bytes"
                        )
    return errors
