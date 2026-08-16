#!/usr/bin/env python3
"""Validate a Frontier Entry packet and its source-derived identity bindings."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import posixpath
import re
import sys
from pathlib import Path
from typing import Any

from authorization_target_contract import (
    AuthorizationTargetContractError,
    omitted_top_level_field_digest,
    validate_target_realization,
    validate_target_specification_bytes,
)
from post_adoption_state import PostAdoptionStateError, load_reviewed_files
from project_snapshot import (
    ProjectSnapshotError,
    member_bytes as project_member_bytes,
    read_manifest as read_project_snapshot_manifest,
    verify as verify_project_snapshot,
)

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required to validate Frontier Entry packets") from exc


from finding_effects import add_finding, finalize_findings


VALIDATOR = "frontier-entry-packet-schema/7"
CAMPAIGN_STATE_PROJECTION_CONTRACT = "frontier-current-state-projection/1"
COMMON_REQUIRED = {
    "review_kind",
    "review_stage",
    "review_id",
    "packet_path",
    "entry_schema_preflight_paths",
    "task_path",
    "problem_epoch",
    "problem_generated_at",
    "representation_revision",
    "representation_generated_at",
    "representation_review_result",
    "representation_permitted",
    "campaign_generation",
    "recovery_lineage",
    "repository_structure_disposition",
    "repository_layout_approval",
    "design_gate",
    "dispatch_contract",
    "authorization_target",
    "authorization_state",
    "authorization_adoption_path",
    "authorization_adoption_preflight_path",
    "selected_batches",
    "actual_spend",
    "assigned_review_path",
    "completion_check",
}
FROZEN_REQUIRED = {
    "snapshot_manifest",
    "snapshot_id",
}
RECOVERY_REQUIRED = {
    "prior_closeout",
    "candidate_recovery_preflight",
    "recovery_authorization",
    "disposition",
    "inherited_budget",
    "reused_identities",
    "implementation_review",
}
AUTHORIZATION_TARGET_REQUIRED = {
    "target_path",
    "target_id",
    "target_file_sha256",
    "batch_id",
    "packet_path",
    "packet_id",
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
    "decision_id",
    "target_specification",
    "post_adoption_paths",
    "authorization_question",
    "authorize_consequence",
    "decline_consequence",
    "conditional_consequence",
}
PROPOSED_TRANSITION_REQUIRED = {"budget", "selection", "lifecycle"}
DESIGN_GATE_REQUIRED = {"mode", "bindings"}
DESIGN_GATE_MODES = {"direct", "reviewed-design", "pending", "not-applicable"}
BINDING_REQUIRED = {
    "role",
    "path",
    "identity",
    "identity_field",
    "file_sha256",
    "batch_scoped",
}
TARGET_SUMMARY_FIELDS = {
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
    "decision_id",
    "target_specification",
    "post_adoption_paths",
    "authorization_question",
    "authorize_consequence",
    "decline_consequence",
    "conditional_consequence",
}
SNAPSHOT_MANIFEST_REQUIRED = {"path", "snapshot_id", "file_sha256"}
DISPATCH_CONTRACT_REQUIRED = {
    "batch_id",
    "packet_path",
    "packet_id",
    "preflight_path",
    "preflight_id",
    "preflight_file_sha256",
    "design_contract_identity",
    "source_base_identity",
    "scope",
    "maximum_spend",
    "stop_boundary",
    "result_path",
}
CAMPAIGN_STATE_PROJECTION_FIELDS = {
    "contract_version",
    "live_path",
    "post_source_path",
    "pre",
    "post",
}
CURRENT_STATE_FIELDS = {
    "campaign_generation",
    "campaign_status",
    "primary_batch",
    "parallel_batches",
    "decision_id",
    "authorization_state",
    "execution_batch",
    "execution_state",
}
CAMPAIGN_STATUSES = {"planned", "running", "stopped", "halted"}
AUTHORIZATION_STATES = {"pending", "adopted", "not-required", "closed"}
EXECUTION_STATES = {
    "not-authorized",
    "awaiting-acknowledgment",
    "acknowledged",
    "released",
    "reported",
    "terminal",
}
BATCH_IDENTIFIER = re.compile(r"^B[0-9]+$")
DECISION_IDENTIFIER = re.compile(r"^V[0-9]+$")
OUT_OF_SCOPE_COMPLETION_CHECKS = (
    re.compile(r"\bslice\s*7\b", re.I),
    re.compile(r"\bquick_validate(?:\.py)?\b", re.I),
    re.compile(r"(?:^|\s)\.agents/", re.I),
    re.compile(r"\bvalidate_frontier_skill_bundle(?:\.py)?\b", re.I),
)
EXACT_OUT_OF_SCOPE_COMPLETION_CHECKS = {
    "run Skill validation",
    "run frontier validator tests",
}
ENTRY_ALLOWED_FIELDS = COMMON_REQUIRED | FROZEN_REQUIRED | {
    "packet_id",
    "campaign_state_projection",
}
NON_PROJECT_ENTRY_TEXT = re.compile(
    r"(?:^|[\s'\"`(])(?:\.agents|\.codex)/|"
    r"(?:^|/)\S*-snapshot/inputs(?:/|$)|"
    r"\bworkflow[-_ ]sha256\b|"
    r"\b(?:slice\s*7|quick_validate(?:\.py)?|validate_frontier_skill_bundle(?:\.py)?|frontier\s+validator\s+tests?)\b",
    re.I,
)


def canonical_payload(document: dict[str, Any]) -> bytes:
    payload = dict(document)
    payload.pop("packet_id", None)
    return yaml.safe_dump(payload, sort_keys=False, allow_unicode=True).encode()


def computed_packet_id(document: dict[str, Any], digest: str) -> str:
    return f"entry-{document.get('review_id', 'UNKNOWN')}-packet-sha256:{digest}"


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


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def safe_repo_path(root: Path, value: Any) -> Path | None:
    if not isinstance(value, str) or not value or Path(value).is_absolute():
        return None
    resolved_root = root.resolve()
    resolved = (resolved_root / value).resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError:
        return None
    return resolved


def read_mapping(path: Path) -> tuple[dict[str, Any] | None, bytes | None, str | None]:
    try:
        raw = path.read_bytes()
        parsed = yaml.safe_load(raw)
    except (OSError, yaml.YAMLError) as exc:
        return None, None, str(exc)
    if not isinstance(parsed, dict):
        return None, raw, "file must contain a YAML or JSON mapping"
    return parsed, raw, None


def parse_frontmatter(raw: bytes, role: str, findings: list[dict[str, str]]) -> dict[str, Any] | None:
    """Return one Markdown document's YAML frontmatter."""
    lines = raw.splitlines(keepends=True)
    if not lines or lines[0].strip() != b"---":
        add_finding(findings, "CAMPAIGN_STATE_FRONTMATTER_MISSING", role)
        return None
    closing = next(
        (index for index, line in enumerate(lines[1:], start=1) if line.strip() == b"---"),
        None,
    )
    if closing is None:
        add_finding(findings, "CAMPAIGN_STATE_FRONTMATTER_MISSING", role)
        return None
    try:
        parsed = yaml.safe_load(b"".join(lines[1:closing]))
    except yaml.YAMLError as exc:
        add_finding(findings, "CAMPAIGN_STATE_FRONTMATTER_INVALID", f"{role}: {exc}")
        return None
    if not isinstance(parsed, dict):
        add_finding(findings, "CAMPAIGN_STATE_FRONTMATTER_INVALID", role)
        return None
    return parsed


def load_batch_validator() -> Any:
    path = Path(__file__).with_name("validate_batch_packet.py")
    spec = importlib.util.spec_from_file_location("_frontier_batch_packet_validator_for_entry", path)
    if spec is None or spec.loader is None:  # pragma: no cover
        raise RuntimeError("cannot load batch packet validator")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def snapshot_sources(
    document: dict[str, Any],
    root: Path,
    findings: list[dict[str, str]],
    *,
    reconcile_live: bool = True,
) -> dict[str, tuple[bytes, str]]:
    """Load exact project bytes from the filtered Git snapshot bound by Entry."""
    manifest_binding = document.get("snapshot_manifest")
    if not isinstance(manifest_binding, dict):
        add_finding(findings, "SNAPSHOT_MANIFEST_BINDING_INVALID", "snapshot_manifest must be a mapping")
        return {}
    for field in sorted(SNAPSHOT_MANIFEST_REQUIRED - manifest_binding.keys()):
        add_finding(findings, "SNAPSHOT_MANIFEST_FIELD_MISSING", field)
    manifest_path = safe_repo_path(root, manifest_binding.get("path"))
    if manifest_path is None:
        add_finding(findings, "SNAPSHOT_MANIFEST_PATH_INVALID", str(manifest_binding.get("path")))
        return {}
    try:
        manifest, manifest_raw = read_project_snapshot_manifest(manifest_path)
    except ProjectSnapshotError as exc:
        add_finding(findings, "SNAPSHOT_MANIFEST_UNREADABLE", str(exc))
        return {}
    observed_manifest_sha = sha256_bytes(manifest_raw or b"")
    if manifest_binding.get("file_sha256") != observed_manifest_sha:
        add_finding(
            findings,
            "SNAPSHOT_MANIFEST_HASH_MISMATCH",
            f"declared {manifest_binding.get('file_sha256')}, observed {observed_manifest_sha}",
        )
    if manifest_binding.get("snapshot_id") != document.get("snapshot_id"):
        add_finding(
            findings,
            "SNAPSHOT_MANIFEST_BINDING_MISMATCH",
            "snapshot_manifest and Entry packet bind different snapshot identities",
        )
    if manifest.get("snapshot_id") != document.get("snapshot_id"):
        add_finding(
            findings,
            "SNAPSHOT_ID_MISMATCH",
            "Entry packet and snapshot manifest bind different snapshot identities",
        )
    try:
        verify_project_snapshot(root, manifest, require_live=reconcile_live)
    except ProjectSnapshotError as exc:
        code = "LIVE_SOURCE_DRIFT" if reconcile_live and "live project member drift" in str(exc) else "PROJECT_SNAPSHOT_INVALID"
        add_finding(findings, code, str(exc))
        return {}
    sources: dict[str, tuple[bytes, str]] = {}
    for item in manifest.get("members", []):
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            add_finding(findings, "PROJECT_SNAPSHOT_MEMBER_INVALID", str(item))
            continue
        source = item["path"]
        try:
            raw = project_member_bytes(root, manifest, source)
        except ProjectSnapshotError as exc:
            add_finding(findings, "PROJECT_SNAPSHOT_MEMBER_INVALID", str(exc))
            continue
        digest = item.get("file_sha256")
        if not isinstance(digest, str):
            add_finding(findings, "PROJECT_SNAPSHOT_MEMBER_INVALID", source)
            continue
        sources[source] = (raw, digest)
        if reconcile_live:
            live_path = safe_repo_path(root, source)
            try:
                live_raw = live_path.read_bytes() if live_path is not None else None
            except OSError as exc:
                add_finding(findings, "LIVE_BOUND_FILE_UNREADABLE", f"snapshot member {source}: {exc}")
            else:
                if live_raw != raw:
                    add_finding(findings, "LIVE_SOURCE_DRIFT", f"snapshot member: {source}")
    return sources


def source_bytes(
    path_value: Any,
    root: Path | None,
    phase: str,
    sources: dict[str, tuple[bytes, str]],
    findings: list[dict[str, str]],
    role: str,
    *,
    reconcile_live: bool = True,
) -> bytes | None:
    if root is None:
        add_finding(findings, "VALIDATION_ROOT_REQUIRED", f"{role} requires --root")
        return None
    live_path = safe_repo_path(root, path_value)
    if live_path is None:
        add_finding(findings, "BOUND_PATH_INVALID", f"{role}: {path_value}")
        return None
    raw: bytes | None = None
    manifest_digest: str | None = None
    if phase == "frozen":
        source = sources.get(path_value)
        if source is None:
            add_finding(findings, "SNAPSHOT_SOURCE_MISSING", f"{role}: {path_value}")
            return None
        raw, manifest_digest = source
    else:
        try:
            raw = live_path.read_bytes()
        except OSError as exc:
            add_finding(findings, "BOUND_FILE_UNREADABLE", f"{role}: {exc}")
            return None
    digest = sha256_bytes(raw)
    if manifest_digest is not None and digest != manifest_digest:
        add_finding(
            findings,
            "SNAPSHOT_FILE_HASH_MISMATCH",
            f"{role}: manifest {manifest_digest}, observed {digest}",
        )
    if phase == "frozen" and reconcile_live:
        try:
            live_raw = live_path.read_bytes()
        except OSError as exc:
            add_finding(findings, "LIVE_BOUND_FILE_UNREADABLE", f"{role}: {exc}")
        else:
            if live_raw != raw:
                add_finding(findings, "LIVE_SOURCE_DRIFT", f"{role}: {path_value}")
    return raw


def parse_raw_mapping(raw: bytes, role: str, findings: list[dict[str, str]]) -> dict[str, Any] | None:
    try:
        parsed = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        add_finding(findings, "BOUND_FILE_PARSE_FAILED", f"{role}: {exc}")
        return None
    if not isinstance(parsed, dict):
        add_finding(findings, "BOUND_FILE_NOT_MAPPING", role)
        return None
    return parsed


def validate_campaign_state_projection(
    document: dict[str, Any],
    target: dict[str, Any],
    root: Path | None,
    phase: str,
    sources: dict[str, tuple[bytes, str]],
    findings: list[dict[str, str]],
    *,
    reconcile_live: bool = True,
) -> None:
    """Verify the task-neutral current-state projection before semantic review."""
    projection = document.get("campaign_state_projection")
    if not isinstance(projection, dict) or set(projection) != CAMPAIGN_STATE_PROJECTION_FIELDS:
        add_finding(
            findings,
            "CAMPAIGN_STATE_PROJECTION_INVALID",
            "campaign_state_projection must contain exactly contract_version, live_path, post_source_path, pre, and post",
        )
        return
    if projection.get("contract_version") != CAMPAIGN_STATE_PROJECTION_CONTRACT:
        add_finding(
            findings,
            "CAMPAIGN_STATE_PROJECTION_VERSION_INVALID",
            f"contract_version must be {CAMPAIGN_STATE_PROJECTION_CONTRACT}",
        )
    task_path = document.get("task_path")
    expected_live_path = (
        posixpath.join(task_path, "FRONTIER.md") if isinstance(task_path, str) else None
    )
    live_path = projection.get("live_path")
    if live_path != expected_live_path:
        add_finding(
            findings,
            "CAMPAIGN_STATE_LIVE_PATH_MISMATCH",
            f"live_path must be {expected_live_path}",
        )

    post_state = target.get("post_adoption_state")
    post_files = post_state.get("files") if isinstance(post_state, dict) else None
    matching_post_files = [
        item
        for item in post_files or []
        if isinstance(item, dict) and item.get("path") == live_path
    ]
    post_source_path = projection.get("post_source_path")
    if len(matching_post_files) != 1 or not isinstance(
        matching_post_files[0].get("post_source"), dict
    ):
        add_finding(
            findings,
            "CAMPAIGN_STATE_POST_SOURCE_MISSING",
            "post_adoption_state must bind the canonical FRONTIER.md exactly once",
        )
    elif matching_post_files[0]["post_source"].get("path") != post_source_path:
        add_finding(
            findings,
            "CAMPAIGN_STATE_POST_SOURCE_MISMATCH",
            "campaign_state_projection.post_source_path must come from post_adoption_state",
        )

    live_raw = source_bytes(
        live_path,
        root,
        phase,
        sources,
        findings,
        "campaign state pre-state",
        reconcile_live=reconcile_live,
    )
    post_raw = source_bytes(
        post_source_path,
        root,
        phase,
        sources,
        findings,
        "campaign state post-state",
        reconcile_live=reconcile_live,
    )
    observed_states: dict[str, dict[str, Any]] = {}
    for state_name, raw in (("pre", live_raw), ("post", post_raw)):
        declared = projection.get(state_name)
        if not isinstance(declared, dict) or set(declared) != CURRENT_STATE_FIELDS:
            add_finding(
                findings,
                "CAMPAIGN_STATE_FIELDS_INVALID",
                f"campaign_state_projection.{state_name} must contain the exact current-state fields",
            )
            continue
        if raw is None:
            continue
        frontmatter = parse_frontmatter(raw, f"campaign {state_name}-state", findings)
        observed = frontmatter.get("current_state") if frontmatter else None
        if not isinstance(observed, dict) or set(observed) != CURRENT_STATE_FIELDS:
            add_finding(
                findings,
                "CAMPAIGN_STATE_FRONTMATTER_INVALID",
                f"campaign {state_name}-state requires exact current_state fields",
            )
            continue
        observed_states[state_name] = observed
        if observed != declared:
            add_finding(
                findings,
                "CAMPAIGN_STATE_PROJECTION_MISMATCH",
                f"campaign_state_projection.{state_name} differs from FRONTIER.md frontmatter",
            )
        if frontmatter.get("campaign_generation") != observed.get("campaign_generation"):
            add_finding(
                findings,
                "CAMPAIGN_STATE_GENERATION_MISMATCH",
                f"campaign {state_name}-state frontmatter and current_state disagree",
            )
        if frontmatter.get("campaign_status") != observed.get("campaign_status"):
            add_finding(
                findings,
                "CAMPAIGN_STATE_STATUS_MISMATCH",
                f"campaign {state_name}-state frontmatter and current_state disagree",
            )

    pre = projection.get("pre") if isinstance(projection.get("pre"), dict) else {}
    post = projection.get("post") if isinstance(projection.get("post"), dict) else {}
    for state_name, state in (("pre", pre), ("post", post)):
        generation = state.get("campaign_generation")
        if isinstance(generation, bool) or not isinstance(generation, int) or generation < 1:
            add_finding(
                findings,
                "CAMPAIGN_STATE_FIELD_INVALID",
                f"{state_name}.campaign_generation must be a positive integer",
            )
        campaign_status = state.get("campaign_status")
        if not isinstance(campaign_status, str) or campaign_status not in CAMPAIGN_STATUSES:
            add_finding(
                findings,
                "CAMPAIGN_STATE_FIELD_INVALID",
                f"{state_name}.campaign_status must be one of {sorted(CAMPAIGN_STATUSES)}",
            )
        primary = state.get("primary_batch")
        if primary is not None and (
            not isinstance(primary, str) or BATCH_IDENTIFIER.fullmatch(primary) is None
        ):
            add_finding(
                findings,
                "CAMPAIGN_STATE_FIELD_INVALID",
                f"{state_name}.primary_batch must be a B identifier or null",
            )
        parallel = state.get("parallel_batches")
        if not isinstance(parallel, list) or any(
            not isinstance(item, str) or BATCH_IDENTIFIER.fullmatch(item) is None
            for item in parallel
        ) or len(parallel) != len(set(parallel)):
            add_finding(
                findings,
                "CAMPAIGN_STATE_FIELD_INVALID",
                f"{state_name}.parallel_batches must be a unique list of B identifiers",
            )
        decision = state.get("decision_id")
        if decision is not None and (
            not isinstance(decision, str) or DECISION_IDENTIFIER.fullmatch(decision) is None
        ):
            add_finding(
                findings,
                "CAMPAIGN_STATE_FIELD_INVALID",
                f"{state_name}.decision_id must be a V identifier or null",
            )
        authorization_state = state.get("authorization_state")
        if (
            not isinstance(authorization_state, str)
            or authorization_state not in AUTHORIZATION_STATES
        ):
            add_finding(
                findings,
                "CAMPAIGN_STATE_FIELD_INVALID",
                f"{state_name}.authorization_state must be one of {sorted(AUTHORIZATION_STATES)}",
            )
        execution_batch = state.get("execution_batch")
        if execution_batch is not None and (
            not isinstance(execution_batch, str)
            or BATCH_IDENTIFIER.fullmatch(execution_batch) is None
        ):
            add_finding(
                findings,
                "CAMPAIGN_STATE_FIELD_INVALID",
                f"{state_name}.execution_batch must be a B identifier or null",
            )
        execution_state = state.get("execution_state")
        if not isinstance(execution_state, str) or execution_state not in EXECUTION_STATES:
            add_finding(
                findings,
                "CAMPAIGN_STATE_FIELD_INVALID",
                f"{state_name}.execution_state must be one of {sorted(EXECUTION_STATES)}",
            )
    batch_id = target.get("batch_id")
    decision_id = target.get("decision_id")
    for state_name, state in (("pre", pre), ("post", post)):
        if state.get("campaign_generation") != document.get("campaign_generation"):
            add_finding(
                findings,
                "CAMPAIGN_STATE_GENERATION_MISMATCH",
                f"{state_name} campaign_generation must equal the Entry generation",
            )
        if state.get("decision_id") != decision_id or state.get("execution_batch") != batch_id:
            add_finding(
                findings,
                "CAMPAIGN_STATE_IDENTITY_MISMATCH",
                f"{state_name} decision and execution batch must equal the reviewed target",
            )
        parallel = state.get("parallel_batches")
        if not isinstance(parallel, list) or any(
            not isinstance(item, str) or not item for item in parallel
        ) or len(parallel) != len(set(parallel)):
            add_finding(
                findings,
                "CAMPAIGN_STATE_PARALLEL_INVALID",
                f"{state_name} parallel_batches must be a unique string list",
            )
    if pre.get("campaign_status") != post.get("campaign_status"):
        add_finding(
            findings,
            "CAMPAIGN_STATE_STATUS_TRANSITION_INVALID",
            "authorization adoption must preserve campaign_status; the first-B lifecycle transition occurs after acknowledgment",
        )
    if pre.get("authorization_state") != "pending" or post.get("authorization_state") != "adopted":
        add_finding(
            findings,
            "CAMPAIGN_STATE_AUTHORIZATION_TRANSITION_INVALID",
            "authorization-readiness requires pending -> adopted",
        )
    if pre.get("execution_state") != "not-authorized" or post.get("execution_state") != "awaiting-acknowledgment":
        add_finding(
            findings,
            "CAMPAIGN_STATE_EXECUTION_TRANSITION_INVALID",
            "authorization adoption may advance execution only to awaiting-acknowledgment",
        )
    selected = document.get("selected_batches")
    projected_selected = [post.get("primary_batch"), *(post.get("parallel_batches") or [])]
    projected_selected = [item for item in projected_selected if item is not None]
    if isinstance(selected, list) and projected_selected != selected:
        add_finding(
            findings,
            "CAMPAIGN_STATE_SELECTION_MISMATCH",
            "post-state Primary and Parallel must equal selected_batches in order",
        )


def validate_design_gate(
    document: dict[str, Any],
    root: Path | None,
    phase: str,
    sources: dict[str, tuple[bytes, str]],
    findings: list[dict[str, str]],
    *,
    reconcile_live: bool = True,
) -> list[dict[str, Any]]:
    gate = document.get("design_gate")
    if not isinstance(gate, dict):
        add_finding(findings, "DESIGN_GATE_INVALID", "design_gate must be a mapping")
        return []
    for field in sorted(DESIGN_GATE_REQUIRED - gate.keys()):
        add_finding(findings, "DESIGN_GATE_FIELD_MISSING", field)
    mode = gate.get("mode")
    if mode not in DESIGN_GATE_MODES:
        add_finding(findings, "DESIGN_GATE_MODE_INVALID", str(mode))
    bindings = gate.get("bindings")
    if not isinstance(bindings, list):
        add_finding(findings, "DESIGN_BINDINGS_INVALID", "design_gate.bindings must be a list")
        return []
    if mode in {"direct", "reviewed-design"} and not bindings:
        add_finding(findings, "DESIGN_BINDINGS_EMPTY", f"{mode} requires at least one binding")
    if mode == "not-applicable" and bindings:
        add_finding(findings, "DESIGN_BINDINGS_UNEXPECTED", "not-applicable requires no bindings")
    valid_bindings: list[dict[str, Any]] = []
    for index, binding in enumerate(bindings):
        label = f"design_gate.bindings[{index}]"
        if not isinstance(binding, dict):
            add_finding(findings, "DESIGN_BINDING_INVALID", f"{label} must be a mapping")
            continue
        for field in sorted(BINDING_REQUIRED - binding.keys()):
            add_finding(findings, "DESIGN_BINDING_FIELD_MISSING", f"{label}.{field}")
        role = binding.get("role")
        identity = binding.get("identity")
        identity_field = binding.get("identity_field")
        declared_sha = binding.get("file_sha256")
        batch_scoped = binding.get("batch_scoped")
        if not isinstance(role, str) or not role:
            add_finding(findings, "DESIGN_BINDING_ROLE_INVALID", label)
        if not isinstance(identity, str) or not identity:
            add_finding(findings, "DESIGN_BINDING_IDENTITY_INVALID", label)
        if identity_field is not None and (not isinstance(identity_field, str) or not identity_field):
            add_finding(findings, "DESIGN_BINDING_IDENTITY_FIELD_INVALID", label)
        if not isinstance(declared_sha, str) or len(declared_sha) != 64:
            add_finding(findings, "DESIGN_BINDING_SHA256_INVALID", label)
        if not isinstance(batch_scoped, bool):
            add_finding(findings, "DESIGN_BINDING_BATCH_SCOPE_INVALID", label)
        raw = source_bytes(
            binding.get("path"),
            root,
            phase,
            sources,
            findings,
            label,
            reconcile_live=reconcile_live,
        )
        if raw is None:
            continue
        observed_sha = sha256_bytes(raw)
        if declared_sha != observed_sha:
            add_finding(
                findings,
                "BOUND_FILE_HASH_MISMATCH",
                f"{label}: declared {declared_sha}, observed {observed_sha}",
            )
        if identity_field is None:
            expected_identity = f"sha256:{observed_sha}"
            if identity != expected_identity:
                add_finding(
                    findings,
                    "BOUND_IDENTITY_MISMATCH",
                    f"{label}: declared {identity}, derived {expected_identity}",
                )
        else:
            parsed = parse_raw_mapping(raw, label, findings)
            observed_identity = parsed.get(identity_field) if parsed else None
            if identity != observed_identity:
                add_finding(
                    findings,
                    "BOUND_IDENTITY_MISMATCH",
                    f"{label}: declared {identity}, derived {observed_identity}",
                )
        valid_bindings.append(binding)
    return valid_bindings


def path_mappings(value: Any, path_value: str) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    if isinstance(value, dict):
        if value.get("path") == path_value:
            matches.append(value)
        for child in value.values():
            matches.extend(path_mappings(child, path_value))
    elif isinstance(value, list):
        for child in value:
            matches.extend(path_mappings(child, path_value))
    return matches


def validate_exclusive_artifact_paths(
    document: dict[str, Any],
    packet: dict[str, Any] | None,
    findings: list[dict[str, str]],
) -> None:
    """Reject aliases and collisions among Entry-owned chain artifacts."""

    target = document.get("authorization_target")
    target = target if isinstance(target, dict) else {}
    target_specification = target.get("target_specification")
    target_specification = (
        target_specification if isinstance(target_specification, dict) else {}
    )
    schema_paths = document.get("entry_schema_preflight_paths")
    schema_paths = schema_paths if isinstance(schema_paths, dict) else {}
    snapshot_manifest = document.get("snapshot_manifest")
    snapshot_manifest = snapshot_manifest if isinstance(snapshot_manifest, dict) else {}
    packet = packet if isinstance(packet, dict) else {}

    artifacts = {
        "entry_packet": document.get("packet_path"),
        "entry_draft_preflight": schema_paths.get("draft"),
        "entry_frozen_preflight": schema_paths.get("frozen"),
        "entry_snapshot_manifest": snapshot_manifest.get("path"),
        "entry_review": document.get("assigned_review_path"),
        "authorization_target_specification": target_specification.get("path"),
        "authorization_target": target.get("target_path"),
        "authorization_user_result": target.get("user_result_path"),
        "authorization_adoption": document.get("authorization_adoption_path"),
        "authorization_adoption_preflight": document.get(
            "authorization_adoption_preflight_path"
        ),
        "batch_packet": packet.get("packet_path"),
        "batch_preflight": packet.get("packet_preflight_path"),
        "batch_acknowledgment": packet.get("acknowledgment_path"),
        "batch_execution_start": packet.get("execution_start_path"),
        "batch_candidate_manifest": packet.get("candidate_manifest_path"),
        "batch_result_validation": packet.get("result_validation_path"),
        "batch_result": packet.get("result_packet_path") or target.get("result_path"),
    }

    canonical: dict[str, str] = {}
    for role, raw in artifacts.items():
        if raw is None:
            continue
        if not isinstance(raw, str) or not raw or raw.startswith("/"):
            add_finding(
                findings,
                "ARTIFACT_PATH_INVALID",
                f"{role} must be a nonempty repository-relative path",
            )
            continue
        normalized = posixpath.normpath(raw)
        if (
            normalized in {".", ".."}
            or normalized.startswith("../")
            or normalized != raw
        ):
            add_finding(
                findings,
                "ARTIFACT_PATH_NOT_CANONICAL",
                f"{role}: {raw}",
            )
            continue
        canonical[role] = normalized

    by_path: dict[str, list[str]] = {}
    for role, path in canonical.items():
        by_path.setdefault(path, []).append(role)
    for path, roles in by_path.items():
        if len(roles) > 1:
            add_finding(
                findings,
                "ARTIFACT_PATH_COLLISION",
                f"{path}: {', '.join(sorted(roles))}",
            )

def field_mappings(value: Any, field: str, expected: Any) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    if isinstance(value, dict):
        if value.get(field) == expected:
            matches.append(value)
        for child in value.values():
            matches.extend(field_mappings(child, field, expected))
    elif isinstance(value, list):
        for child in value:
            matches.extend(field_mappings(child, field, expected))
    return matches


def target_digest(raw: bytes) -> str | None:
    try:
        return omitted_top_level_field_digest(raw, "target_id")
    except AuthorizationTargetContractError:
        return None


def validate_authorization_target_files(
    document: dict[str, Any],
    target: dict[str, Any],
    bindings: list[dict[str, Any]],
    root: Path | None,
    phase: str,
    sources: dict[str, tuple[bytes, str]],
    findings: list[dict[str, str]],
    *,
    reconcile_live: bool = True,
) -> None:
    target_raw = source_bytes(
        target.get("target_path"),
        root,
        phase,
        sources,
        findings,
        "authorization target",
        reconcile_live=reconcile_live,
    )
    if target_raw is None:
        return
    observed_target_sha = sha256_bytes(target_raw)
    if target.get("target_file_sha256") != observed_target_sha:
        add_finding(
            findings,
            "TARGET_FILE_HASH_MISMATCH",
            f"declared {target.get('target_file_sha256')}, observed {observed_target_sha}",
        )
    target_document = parse_raw_mapping(target_raw, "authorization target", findings)
    if target_document is None:
        return
    if target_document.get("target_id") != target.get("target_id"):
        add_finding(
            findings,
            "TARGET_ID_MISMATCH",
            "Entry packet and target file bind different target identities",
        )
    digest = target_digest(target_raw)
    declared_target_id = target.get("target_id")
    if (
        digest is None
        or not isinstance(declared_target_id, str)
        or "-target-sha256:" not in declared_target_id
        or declared_target_id.rsplit("-target-sha256:", 1)[1] != digest
    ):
        add_finding(
            findings,
            "TARGET_ID_NOT_DERIVED",
            "target_id must end with SHA-256 of exact target bytes with the target_id line omitted",
        )

    recomputed_preflight: dict[str, Any] | None = None
    packet_document: dict[str, Any] | None = None
    packet_raw = source_bytes(
        target.get("packet_path"),
        root,
        phase,
        sources,
        findings,
        "authorization batch packet",
        reconcile_live=reconcile_live,
    )
    if packet_raw is not None:
        packet_document = parse_raw_mapping(packet_raw, "authorization batch packet", findings)
        if packet_document and packet_document.get("packet_id") != target.get("packet_id"):
            add_finding(
                findings,
                "BATCH_PACKET_ID_MISMATCH",
                "Entry target and bound batch packet contain different packet identities",
            )


        if packet_document is not None:
            packet_payload = dict(packet_document)
            packet_payload.pop("packet_id", None)
            derived_packet_id = (
                f"{target.get('batch_id')}-packet-sha256:"
                + sha256_bytes(
                    yaml.safe_dump(packet_payload, sort_keys=False, allow_unicode=True).encode()
                )
            )
            if (
                packet_document.get("batch_id") != target.get("batch_id")
                or target.get("packet_id") != derived_packet_id
            ):
                add_finding(
                    findings,
                    "BATCH_PACKET_ID_NOT_DERIVED",
                    "batch_id and packet_id must derive from the observed batch packet",
                )
            if root is not None:
                recomputed_preflight = load_batch_validator().validate(
                    packet_document, "frozen", root
                )
                if not recomputed_preflight.get("packet_structure_ready"):
                    for item in recomputed_preflight.get("findings", []):
                        add_finding(
                            findings,
                            "BATCH_PACKET_RECOMPUTATION_FAILED",
                            f"{item.get('code')}: {item.get('detail')}",
                        )
                for item in recomputed_preflight.get("advisories", []):
                    add_finding(findings, item["code"], item["detail"])

    if packet_document is not None:
        specification_binding = packet_document.get("development_authorization_target")
        if not isinstance(specification_binding, dict):
            add_finding(
                findings,
                "TARGET_SPECIFICATION_BINDING_INVALID",
                "the current packet must bind a structured authorization-target specification",
            )
        else:
            specification_raw = source_bytes(
                specification_binding.get("path"),
                root,
                phase,
                sources,
                findings,
                "authorization-target specification",
                reconcile_live=reconcile_live,
            )
            if specification_raw is not None:
                try:
                    specification_document = validate_target_specification_bytes(
                        specification_raw,
                        specification_binding,
                    )
                    differences = validate_target_realization(
                        specification_document,
                        target_document,
                        target,
                        binding=specification_binding,
                    )
                except AuthorizationTargetContractError as exc:
                    add_finding(
                        findings,
                        "TARGET_SPECIFICATION_INVALID",
                        str(exc),
                    )
                else:
                    for difference in differences:
                        add_finding(
                            findings,
                            "TARGET_SPECIFICATION_REALIZATION_MISMATCH",
                            difference,
                        )
        target_packet_bindings = path_mappings(target_document, str(target.get("packet_path")))
        if not target_packet_bindings:
            add_finding(findings, "TARGET_PACKET_BINDING_MISSING", str(target.get("packet_path")))
        elif not any(
            item.get("packet_id") == target.get("packet_id")
            and item.get("file_sha256") == sha256_bytes(packet_raw)
            for item in target_packet_bindings
        ):
            add_finding(
                findings,
                "TARGET_PACKET_BINDING_MISMATCH",
                "target file does not bind the observed batch packet identity and bytes",
            )

    for field in sorted(TARGET_SUMMARY_FIELDS):
        if target_document.get(field) != target.get(field):
            add_finding(
                findings,
                "TARGET_SUMMARY_FIELD_MISMATCH",
                f"authorization_target.{field} must derive from target file field {field}",
            )

    def reviewed_source_bytes(path_value: str) -> bytes:
        raw = source_bytes(
            path_value,
            root,
            phase,
            sources,
            findings,
            "post-adoption state source",
            reconcile_live=reconcile_live,
        )
        if raw is None:
            raise PostAdoptionStateError(
                f"post-adoption state source is unavailable: {path_value}"
            )
        return raw

    def reviewed_pre_sha256(path_value: str) -> str:
        if phase == "frozen":
            source = sources.get(path_value)
            if source is None:
                raise PostAdoptionStateError(
                    f"post-adoption target is missing from the snapshot: {path_value}"
                )
            return source[1]
        if root is None:
            raise PostAdoptionStateError(
                f"post-adoption target requires --root: {path_value}"
            )
        path = safe_repo_path(root, path_value)
        if path is None:
            raise PostAdoptionStateError(
                f"post-adoption target path is invalid: {path_value}"
            )
        try:
            return sha256_bytes(path.read_bytes())
        except OSError as exc:
            raise PostAdoptionStateError(
                f"post-adoption target is unreadable: {path_value}: {exc}"
            ) from exc

    try:
        reviewed_files = load_reviewed_files(
            target.get("post_adoption_state"),
            read_source=reviewed_source_bytes,
            pre_sha256_for=reviewed_pre_sha256,
        )
    except PostAdoptionStateError as exc:
        add_finding(findings, "POST_ADOPTION_STATE_INVALID", str(exc))
        reviewed_files = []
    if isinstance(declared_target_id, str) and any(
        declared_target_id.encode() in item.post_bytes for item in reviewed_files
    ):
        add_finding(
            findings,
            "POST_ADOPTION_TARGET_ID_CYCLE",
            "post-adoption source bytes must not contain the future final target identity",
        )
    transition = target.get("proposed_state_transition")
    if isinstance(transition, dict) and any(
        value is not None and value != "none" for value in transition.values()
    ) and not reviewed_files:
        add_finding(
            findings,
            "POST_ADOPTION_STATE_MISSING",
            "a nonempty reviewed state transition requires exact post-adoption file bytes",
        )

    design_identity = target.get("design_contract_identity")
    design_roles = {"direct_profile", "design_contract"}
    design_identities = {
        binding.get("identity")
        for binding in bindings
        if binding.get("role") in design_roles
    }
    if design_identity is not None and design_identity not in design_identities:
        add_finding(
            findings,
            "TARGET_DESIGN_IDENTITY_MISMATCH",
            "design_contract_identity must come from the structured design gate",
        )
    source_identity = target.get("source_base_identity")
    source_identities = {
        binding.get("identity")
        for binding in bindings
        if binding.get("role") == "source_base"
    }
    if source_identity is not None and source_identity not in source_identities:
        add_finding(
            findings,
            "TARGET_SOURCE_BASE_IDENTITY_MISMATCH",
            "source_base_identity must come from a structured source_base binding",
        )

    preflight_id = target.get("preflight_id")
    preflight_bindings = field_mappings(target_document, "preflight_id", preflight_id)
    if not preflight_bindings:
        add_finding(
            findings,
            "TARGET_PREFLIGHT_BINDING_MISSING",
            "target file does not bind preflight_id",
        )
    elif not any(
        isinstance(item.get("path"), str) and isinstance(item.get("file_sha256"), str)
        for item in preflight_bindings
    ):
        add_finding(
            findings,
            "TARGET_PREFLIGHT_BINDING_INVALID",
            "preflight binding requires path, preflight_id, and file_sha256",
        )
    else:
        verified_preflight = False
        for item in preflight_bindings:
            if not isinstance(item.get("path"), str) or not isinstance(item.get("file_sha256"), str):
                continue
            preflight_raw = source_bytes(
                item["path"],
                root,
                phase,
                sources,
                findings,
                "authorization structural preflight",
                reconcile_live=reconcile_live,
            )
            if preflight_raw is None:
                continue
            preflight_document = parse_raw_mapping(
                preflight_raw, "authorization structural preflight", findings
            )
            if (
                sha256_bytes(preflight_raw) == item["file_sha256"]
                and preflight_document is not None
                and preflight_document.get("preflight_id") == preflight_id
                and preflight_document.get("batch_id") == target.get("batch_id")
                and preflight_document.get("computed_packet_id") == target.get("packet_id")
                and preflight_document.get("packet_structure_ready") is True
                and preflight_document.get("findings") == []
                and recomputed_preflight is not None
                and preflight_document == recomputed_preflight
            ):
                preflight_payload = dict(preflight_document)
                preflight_payload.pop("preflight_id", None)
                derived_preflight_id = (
                    f"{target.get('batch_id')}-packet-preflight-sha256:"
                    + sha256_bytes(
                        json.dumps(
                            preflight_payload,
                            sort_keys=True,
                            separators=(",", ":"),
                            ensure_ascii=False,
                        ).encode()
                    )
                )
                verified_preflight = derived_preflight_id == preflight_id
        if not verified_preflight:
            add_finding(
                findings,
                "TARGET_PREFLIGHT_BINDING_MISMATCH",
                "target, preflight file identity, and preflight bytes disagree",
            )

    for binding in bindings:
        role = str(binding.get("role"))
        identity = binding.get("identity")
        identity_names_a_batch = isinstance(identity, str) and re.match(r"^B[0-9]+-", identity)
        if (binding.get("batch_scoped") is True or identity_names_a_batch) and (
            not isinstance(identity, str)
            or not identity.startswith(f"{target.get('batch_id')}-")
        ):
            add_finding(
                findings,
                "DESIGN_BATCH_SCOPED_IDENTITY_MISMATCH",
                f"batch-scoped {role} identity must belong to batch {target.get('batch_id')}",
            )
        matches = path_mappings(target_document, str(binding.get("path")))
        if not matches:
            add_finding(
                findings,
                "TARGET_DESIGN_BINDING_MISSING",
                f"{binding.get('role')}: {binding.get('path')}",
            )
            continue
        identity_field = binding.get("identity_field")
        if not any(
            item.get("file_sha256") == binding.get("file_sha256")
            and (
                identity_field is None
                or item.get(identity_field) == binding.get("identity")
                or (
                    item.get("identity_field") == identity_field
                    and item.get("identity") == binding.get("identity")
                )
            )
            for item in matches
        ):
            add_finding(
                findings,
                "TARGET_DESIGN_BINDING_MISMATCH",
                f"{binding.get('role')}: target, Entry packet, and observed file disagree",
            )

    exact_object = target_document.get("exact_object")
    reviewed_bindings = (
        exact_object.get("reviewed_bindings")
        if isinstance(exact_object, dict)
        else None
    )
    if reviewed_bindings != bindings:
        add_finding(
            findings,
            "TARGET_REVIEWED_BINDINGS_MISMATCH",
            "final target reviewed_bindings must equal the structured Entry design gate in order and content",
        )


def validate_dispatch_contract(
    document: dict[str, Any],
    root: Path | None,
    phase: str,
    sources: dict[str, bytes],
    findings: list[dict[str, str]],
    *,
    reconcile_live: bool = True,
) -> dict[str, Any] | None:
    contract = document.get("dispatch_contract")
    if not isinstance(contract, dict) or set(contract) != DISPATCH_CONTRACT_REQUIRED:
        add_finding(
            findings,
            "DISPATCH_CONTRACT_INVALID",
            "dispatch_contract must contain the exact current packet, preflight, design, source, scope, spend, stop, and result bindings",
        )
        return None
    packet_raw = source_bytes(
        contract.get("packet_path"),
        root,
        phase,
        sources,
        findings,
        "dispatch batch packet",
        reconcile_live=reconcile_live,
    )
    preflight_raw = source_bytes(
        contract.get("preflight_path"),
        root,
        phase,
        sources,
        findings,
        "dispatch packet preflight",
        reconcile_live=reconcile_live,
    )
    if packet_raw is None or preflight_raw is None:
        return None
    packet = parse_raw_mapping(packet_raw, "dispatch batch packet", findings)
    preflight = parse_raw_mapping(preflight_raw, "dispatch packet preflight", findings)
    if packet is None or preflight is None or root is None:
        return packet
    recomputed = load_batch_validator().validate(packet, "frozen", root)
    if not recomputed.get("packet_structure_ready"):
        for item in recomputed.get("findings", []):
            add_finding(
                findings,
                "BATCH_PACKET_RECOMPUTATION_FAILED",
                f"{item.get('code')}: {item.get('detail')}",
            )
    for item in recomputed.get("advisories", []):
        add_finding(findings, item["code"], item["detail"])
    canonical_preflight = (
        json.dumps(recomputed, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode()
    if preflight_raw != canonical_preflight:
        add_finding(
            findings,
            "DISPATCH_PREFLIGHT_RECOMPUTATION_FAILED",
            "stored packet preflight bytes differ from deterministic recomputation",
        )
    boundary = packet.get("authorization_boundary")
    expected = {
        "batch_id": packet.get("batch_id"),
        "packet_path": packet.get("packet_path"),
        "packet_id": packet.get("packet_id"),
        "preflight_path": packet.get("packet_preflight_path"),
        "preflight_id": recomputed.get("preflight_id"),
        "preflight_file_sha256": sha256_bytes(preflight_raw),
        "design_contract_identity": packet.get("design_contract_identity"),
        "source_base_identity": packet.get("source_base_identity"),
        "scope": boundary.get("scope") if isinstance(boundary, dict) else None,
        "maximum_spend": boundary.get("maximum_spend") if isinstance(boundary, dict) else None,
        "stop_boundary": boundary.get("stop_boundary") if isinstance(boundary, dict) else None,
        "result_path": boundary.get("result_path") if isinstance(boundary, dict) else None,
    }
    if contract != expected:
        add_finding(
            findings,
            "DISPATCH_CONTRACT_NOT_DERIVED",
            "dispatch_contract must derive exactly from the observed packet and recomputed preflight",
        )
    selected = document.get("selected_batches")
    if isinstance(selected, list) and contract.get("batch_id") not in selected:
        add_finding(
            findings,
            "DISPATCH_BATCH_NOT_SELECTED",
            "dispatch_contract batch must be selected by Entry",
        )
    stage = document.get("review_stage")
    development_target = packet.get("development_authorization_target")
    if stage == "authorization-readiness" and not development_target:
        add_finding(
            findings,
            "DISPATCH_AUTHORITY_MODE_MISMATCH",
            "authorization-readiness requires a packet development_authorization_target",
        )
    if stage == "spend-readiness" and development_target is not None:
        add_finding(
            findings,
            "DISPATCH_AUTHORITY_MODE_MISMATCH",
            "spend-readiness requires packet development_authorization_target: null",
        )
    return packet


def validate(
    document: dict[str, Any],
    phase: str,
    root: Path | None = None,
    *,
    reconcile_live: bool = True,
) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    required = set(COMMON_REQUIRED)
    if phase == "frozen":
        required |= FROZEN_REQUIRED
    for field in sorted(required):
        if field not in document:
            add_finding(findings, "REQUIRED_FIELD_MISSING", field)
    if phase != "audit":
        for field in sorted(set(document) - ENTRY_ALLOWED_FIELDS):
            add_finding(
                findings,
                "UNKNOWN_ENTRY_FIELD",
                f"{field} is not part of the closed project Entry schema",
            )
        for path, value in strings_with_paths(document):
            if NON_PROJECT_ENTRY_TEXT.search(value):
                add_finding(
                    findings,
                    "NON_PROJECT_ENTRY_INPUT",
                    f"{'.'.join(path)} refers to workflow, Skill, validator, or retired copied-snapshot state",
                )

    if document.get("review_kind") != "entry":
        add_finding(findings, "REVIEW_KIND_INVALID", "review_kind must be entry")
    stage = document.get("review_stage")
    if phase != "audit" and stage not in {"authorization-readiness", "spend-readiness"}:
        add_finding(
            findings,
            "REVIEW_STAGE_INVALID",
            "review_stage must be authorization-readiness or spend-readiness",
        )
    if (
        phase != "audit"
        and stage == "authorization-readiness"
        and document.get("authorization_state") != "pending"
    ):
        add_finding(
            findings,
            "AUTHORIZATION_STATE_INVALID",
            "authorization-readiness review requires authorization_state: pending",
        )

    generation = document.get("campaign_generation")
    if not isinstance(generation, int) or isinstance(generation, bool) or generation < 1:
        add_finding(
            findings,
            "CAMPAIGN_GENERATION_INVALID",
            "campaign_generation must be a positive integer",
        )
    elif phase != "audit" and generation == 1 and document.get("recovery_lineage") is not None:
        add_finding(findings, "RECOVERY_LINEAGE_INVALID", "generation 1 requires recovery_lineage: null")
    elif generation > 1:
        lineage = document.get("recovery_lineage")
        if not isinstance(lineage, dict):
            add_finding(
                findings,
                "RECOVERY_LINEAGE_REQUIRED",
                "campaign_generation greater than 1 requires a recovery_lineage mapping",
            )
        elif phase != "audit":
            for field in sorted(RECOVERY_REQUIRED - lineage.keys()):
                add_finding(findings, "RECOVERY_LINEAGE_FIELD_MISSING", field)

    selected = document.get("selected_batches")
    if not isinstance(selected, list) or not selected:
        add_finding(findings, "SELECTED_BATCHES_INVALID", "selected_batches must be a nonempty list")

    paths = document.get("entry_schema_preflight_paths")
    if phase != "audit" and not (
        isinstance(paths, dict)
        and isinstance(paths.get("draft"), str)
        and isinstance(paths.get("frozen"), str)
        and paths["draft"] != paths["frozen"]
    ):
        add_finding(
            findings,
            "SCHEMA_PREFLIGHT_PATHS_INVALID",
            "entry_schema_preflight_paths requires distinct draft and frozen paths",
        )

    adoption_path = document.get("authorization_adoption_path")
    adoption_preflight_path = document.get("authorization_adoption_preflight_path")
    if phase != "audit" and not (
        isinstance(adoption_path, str)
        and adoption_path
        and isinstance(adoption_preflight_path, str)
        and adoption_preflight_path
        and adoption_path != adoption_preflight_path
    ):
        add_finding(
            findings,
            "ADOPTION_PATHS_INVALID",
            "authorization adoption and validation require distinct nonempty paths",
        )

    completion_check = document.get("completion_check")
    if phase != "audit" and (
        not isinstance(completion_check, str)
        or not completion_check.strip()
    ):
        add_finding(
            findings,
            "COMPLETION_CHECK_INVALID",
            "completion_check must name the project checks required by this Entry",
        )
    elif phase != "audit" and (
        any(pattern.search(completion_check) for pattern in OUT_OF_SCOPE_COMPLETION_CHECKS)
        or completion_check in EXACT_OUT_OF_SCOPE_COMPLETION_CHECKS
    ):
        add_finding(
            findings,
            "ENTRY_COMPLETION_CHECK_OUT_OF_SCOPE",
            "ordinary Entry completion checks contain project checks only",
        )

    sources = (
        snapshot_sources(
            document,
            root,
            findings,
            reconcile_live=reconcile_live,
        )
        if phase == "frozen" and root
        else {}
    )
    bindings = (
        validate_design_gate(
            document,
            root,
            phase,
            sources,
            findings,
            reconcile_live=reconcile_live,
        )
        if phase != "audit"
        else []
    )
    dispatch_packet = None
    if phase != "audit":
        dispatch_packet = validate_dispatch_contract(
            document,
            root,
            phase,
            sources,
            findings,
            reconcile_live=reconcile_live,
        )

    target = document.get("authorization_target")
    if phase != "audit" and stage == "authorization-readiness":
        if not isinstance(target, dict):
            add_finding(findings, "AUTHORIZATION_TARGET_INVALID", "authorization_target must be a mapping")
        else:
            for field in sorted(AUTHORIZATION_TARGET_REQUIRED - target.keys()):
                add_finding(findings, "AUTHORIZATION_TARGET_FIELD_MISSING", field)
            target_batch = target.get("batch_id")
            if isinstance(selected, list) and target_batch not in selected:
                add_finding(
                    findings,
                    "AUTHORIZATION_TARGET_BATCH_MISMATCH",
                    f"target batch {target_batch} is not selected",
                )
            transition = target.get("proposed_state_transition")
            if not isinstance(transition, dict):
                add_finding(
                    findings,
                    "PROPOSED_STATE_TRANSITION_INVALID",
                    "authorization target requires a proposed_state_transition mapping",
                )
            else:
                for field in sorted(PROPOSED_TRANSITION_REQUIRED - transition.keys()):
                    add_finding(findings, "PROPOSED_STATE_TRANSITION_FIELD_MISSING", field)
            validate_authorization_target_files(
                document,
                target,
                bindings,
                root,
                phase,
                sources,
                findings,
                reconcile_live=reconcile_live,
            )
            validate_campaign_state_projection(
                document,
                target,
                root,
                phase,
                sources,
                findings,
                reconcile_live=reconcile_live,
            )
            contract = document.get("dispatch_contract")
            if isinstance(contract, dict):
                target_dispatch = {
                    field: target.get(field)
                    for field in (
                        "batch_id",
                        "packet_path",
                        "packet_id",
                        "preflight_id",
                        "design_contract_identity",
                        "source_base_identity",
                        "scope",
                        "maximum_spend",
                        "stop_boundary",
                        "result_path",
                    )
                }
                expected_target_dispatch = {
                    field: contract.get(field) for field in target_dispatch
                }
                if target_dispatch != expected_target_dispatch:
                    add_finding(
                        findings,
                        "AUTHORIZATION_TARGET_DISPATCH_MISMATCH",
                        "authorization target must equal the source-derived dispatch contract",
                    )
    elif phase != "audit" and stage == "spend-readiness":
        if target is not None or document.get("authorization_state") != "not-required":
            add_finding(
                findings,
                "AUTHORIZATION_STATE_INVALID",
                "spend-readiness requires null target and authorization_state: not-required",
            )

    if phase != "audit":
        validate_exclusive_artifact_paths(document, dispatch_packet, findings)

    payload_sha256 = hashlib.sha256(canonical_payload(document)).hexdigest()
    expected_packet_id = computed_packet_id(document, payload_sha256)
    declared_packet_id = document.get("packet_id")
    if phase == "draft" and declared_packet_id is not None:
        add_finding(findings, "DRAFT_ALREADY_FROZEN", "draft schema validation requires packet_id to be absent")
    elif phase == "frozen":
        if declared_packet_id is None:
            add_finding(findings, "PACKET_ID_MISSING", "frozen packet requires packet_id")
        elif declared_packet_id != expected_packet_id:
            add_finding(
                findings,
                "PACKET_ID_MISMATCH",
                f"declared {declared_packet_id} does not equal computed {expected_packet_id}",
            )

    finding_summary = finalize_findings(findings)
    actionable_findings = finding_summary["findings"]
    result: dict[str, Any] = {
        "validator": VALIDATOR,
        "review_id": document.get("review_id"),
        "packet_path": document.get("packet_path"),
        "packet_payload_sha256": payload_sha256,
        "computed_packet_id": expected_packet_id,
        "derived_binding_count": len(bindings),
        "entry_bindings_ready": not any(
            item["code"].startswith(("BOUND_", "DESIGN_", "LIVE_", "SNAPSHOT_", "TARGET_", "BATCH_"))
            for item in actionable_findings
        ),
        "entry_schema_ready": finding_summary["ready"],
        "findings": actionable_findings,
        "blocking_findings": finding_summary["blocking_findings"],
        "repair_findings": finding_summary["repair_findings"],
        "advisories": finding_summary["advisories"],
        "finding_effect_counts": finding_summary["finding_effect_counts"],
    }
    canonical = json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    result["entry_schema_id"] = (
        f"entry-{document.get('review_id', 'UNKNOWN')}-schema-sha256:"
        f"{hashlib.sha256(canonical).hexdigest()}"
    )
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packet", type=Path)
    parser.add_argument("--phase", choices=("draft", "frozen", "audit"), default="frozen")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path)
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
    result = validate(document, args.phase, args.root)
    rendered = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered)
    else:
        sys.stdout.write(rendered)
    return 0 if result["entry_schema_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
