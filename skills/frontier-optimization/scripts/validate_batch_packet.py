#!/usr/bin/env python3
"""Validate Frontier batch packet structure before authorization review."""

from __future__ import annotations

import argparse
import hashlib
import json
import posixpath
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover - exercised by the CLI environment
    raise SystemExit("PyYAML is required to validate Frontier batch packets") from exc


VALIDATOR = "frontier-batch-packet-preflight/1"
WRITE_VERBS = re.compile(r"\b(edit|write|create|modify|overwrite|change)\b", re.I)


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


def add_finding(findings: list[dict[str, str]], code: str, detail: str) -> None:
    finding = {"code": code, "detail": detail}
    if finding not in findings:
        findings.append(finding)


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
    for path in (acknowledgment, result_validation, result, manifest):
        if path is not None:
            worker_paths.append(path)
    worker_paths = sorted(set(worker_paths))
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
    lifecycle_path: PathSpec | None = None
    if isinstance(lifecycle, dict) and lifecycle.get("path"):
        try:
            lifecycle_path = parse_path_entry(lifecycle["path"], "coordinator_lifecycle_transition.path")
            coordinator_paths.append(lifecycle_path)
        except ValueError as exc:
            add_finding(findings, "INVALID_PATH_SCHEMA", f"coordinator_lifecycle_transition.path: {exc}")
    elif lifecycle is not None and phase != "audit":
        add_finding(
            findings,
            "INVALID_PATH_SCHEMA",
            "coordinator_lifecycle_transition must be null or a mapping with path",
        )

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

    findings.sort(key=lambda item: (item["code"], item["detail"]))
    finding_codes = {item["code"] for item in findings}
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
    result_document: dict[str, Any] = {
        "validator": VALIDATOR,
        "batch_id": document.get("batch_id"),
        "packet_path": document.get("packet_path"),
        "packet_payload_sha256": payload_sha256,
        "computed_packet_id": expected_packet_id,
        "packet_structure_ready": not findings,
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
        "findings": findings,
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
