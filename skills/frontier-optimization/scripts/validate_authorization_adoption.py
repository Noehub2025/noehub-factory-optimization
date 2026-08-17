#!/usr/bin/env python3
"""Validate authorization adoption from frozen Entry sources, not declarations."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

from authorization_target_contract import (
    AuthorizationTargetContractError,
    omitted_top_level_field_digest,
)
from finding_effects import add_finding, finalize_findings, has_actionable_findings
from workflow_source_binding import WorkflowSourceBindingError, validate_binding

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required to validate Frontier authorization adoption") from exc


VALIDATOR = "frontier-authorization-adoption/6"
REQUIRED_FIELDS = {
    "adoption_path",
    "entry_packet",
    "workflow_source_binding",
    "readiness_review",
    "authorization_target",
    "user_result",
    "adopted_v",
    "answer_fidelity",
    "reviewed_state_transition",
    "entry_result",
    "maximum_consequence",
}
ENTRY_PACKET_REQUIRED = {"path", "packet_id", "file_sha256"}
READINESS_REQUIRED = {
    "review_id",
    "review_result",
    "review_artifact",
    "review_artifact_identity",
    "snapshot_id",
    "entry_packet_id",
}
TARGET_REQUIRED = {"path", "target_id", "file_sha256", "batch_id", "packet_id"}
USER_RESULT_REQUIRED = {
    "path",
    "identity",
    "identity_field",
    "file_sha256",
    "target_id",
    "answer",
}
ADOPTED_V_REQUIRED = {
    "decision_id",
    "record_path",
    "result_path",
    "result_identity",
    "target_id",
}
USER_RESULT_DOCUMENT_FIELDS = {"result_id", "target_id", "answer", "conditions"}


def canonical_payload(document: dict[str, Any]) -> bytes:
    payload = dict(document)
    payload.pop("adoption_id", None)
    return yaml.safe_dump(payload, sort_keys=False, allow_unicode=True).encode()


def computed_adoption_id(document: dict[str, Any], digest: str) -> str:
    return f"authorization-adoption-sha256:{digest}"


def is_none_transition(value: Any) -> bool:
    return value is None or value == "none"


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


def read_bytes(
    root: Path | None,
    value: Any,
    findings: list[dict[str, str]],
    role: str,
) -> bytes | None:
    if root is None:
        add_finding(findings, "VALIDATION_ROOT_REQUIRED", f"{role} requires --root")
        return None
    path = safe_repo_path(root, value)
    if path is None:
        add_finding(findings, "BOUND_PATH_INVALID", f"{role}: {value}")
        return None
    try:
        return path.read_bytes()
    except OSError as exc:
        add_finding(findings, "BOUND_FILE_UNREADABLE", f"{role}: {exc}")
        return None


def parse_mapping(raw: bytes, findings: list[dict[str, str]], role: str) -> dict[str, Any] | None:
    try:
        parsed = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        add_finding(findings, "BOUND_FILE_PARSE_FAILED", f"{role}: {exc}")
        return None
    if not isinstance(parsed, dict):
        add_finding(findings, "BOUND_FILE_NOT_MAPPING", role)
        return None
    return parsed


def parse_frontmatter(raw: bytes, findings: list[dict[str, str]]) -> dict[str, Any] | None:
    try:
        text = raw.decode()
    except UnicodeDecodeError as exc:
        add_finding(findings, "REVIEW_ARTIFACT_INVALID", str(exc))
        return None
    if not text.startswith("---\n") or "\n---\n" not in text[4:]:
        add_finding(findings, "REVIEW_ARTIFACT_INVALID", "review artifact lacks YAML frontmatter")
        return None
    raw_frontmatter = text[4:].split("\n---\n", 1)[0]
    try:
        frontmatter = yaml.safe_load(raw_frontmatter)
    except yaml.YAMLError as exc:
        add_finding(findings, "REVIEW_ARTIFACT_INVALID", str(exc))
        return None
    if not isinstance(frontmatter, dict):
        add_finding(findings, "REVIEW_ARTIFACT_INVALID", "frontmatter must be a mapping")
        return None
    return frontmatter


def load_entry_validator() -> Any:
    path = Path(__file__).with_name("validate_entry_packet.py")
    spec = importlib.util.spec_from_file_location("_frontier_entry_packet_validator_v3", path)
    if spec is None or spec.loader is None:  # pragma: no cover
        raise RuntimeError("cannot load Entry packet validator")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def validate(
    document: dict[str, Any],
    phase: str,
    root: Path | None = None,
    *,
    reconcile_entry_live: bool = True,
) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    derived_checks: list[dict[str, str]] = []
    for field in sorted(REQUIRED_FIELDS - document.keys()):
        add_finding(findings, "REQUIRED_FIELD_MISSING", field)

    entry_binding = document.get("entry_packet")
    entry_document: dict[str, Any] | None = None
    if not isinstance(entry_binding, dict):
        add_finding(findings, "ENTRY_PACKET_INVALID", "entry_packet must be a mapping")
    else:
        for field in sorted(ENTRY_PACKET_REQUIRED - entry_binding.keys()):
            add_finding(findings, "ENTRY_PACKET_FIELD_MISSING", field)
        entry_raw = read_bytes(root, entry_binding.get("path"), findings, "Entry packet")
        if entry_raw is not None:
            observed_sha = hashlib.sha256(entry_raw).hexdigest()
            declared_sha = entry_binding.get("file_sha256")
            matched = declared_sha == observed_sha
            derived_checks.append(
                {
                    "name": "entry_packet_file",
                    "reviewed_identity": f"sha256:{declared_sha}",
                    "observed_identity": f"sha256:{observed_sha}",
                    "status": "matched" if matched else "mismatch",
                }
            )
            if not matched:
                add_finding(
                    findings,
                    "ENTRY_PACKET_FILE_HASH_MISMATCH",
                    f"declared {declared_sha}, observed {observed_sha}",
                )
            entry_document = parse_mapping(entry_raw, findings, "Entry packet")
            if entry_document is not None:
                observed_packet_id = entry_document.get("packet_id")
                declared_packet_id = entry_binding.get("packet_id")
                id_matched = observed_packet_id == declared_packet_id
                derived_checks.append(
                    {
                        "name": "entry_packet_identity",
                        "reviewed_identity": str(declared_packet_id),
                        "observed_identity": str(observed_packet_id),
                        "status": "matched" if id_matched else "mismatch",
                    }
                )
                if not id_matched:
                    add_finding(
                        findings,
                        "ENTRY_PACKET_ID_MISMATCH",
                        "adoption binding and frozen Entry packet contain different identities",
                    )
                entry_validation = load_entry_validator().validate(
                    entry_document,
                    "frozen",
                    root,
                    reconcile_live=reconcile_entry_live,
                )
                derived_checks.append(
                    {
                        "name": "entry_source_reconciliation",
                        "reviewed_identity": "finding-free frozen Entry bindings",
                        "observed_identity": (
                            "finding-free frozen Entry bindings"
                            if entry_validation["entry_schema_ready"]
                            else "Entry binding findings present"
                        ),
                        "status": "matched" if entry_validation["entry_schema_ready"] else "mismatch",
                    }
                )
                for item in entry_validation["findings"]:
                    add_finding(
                        findings,
                        "ENTRY_SOURCE_RECONCILIATION_FAILED",
                        f"{item['code']}: {item['detail']}",
                    )
                for item in entry_validation.get("advisories", []):
                    add_finding(findings, item["code"], item["detail"])

    adopted_workflow_source = document.get("workflow_source_binding")
    if entry_document is not None:
        entry_workflow_source = entry_document.get("workflow_source_binding")
        if adopted_workflow_source != entry_workflow_source:
            add_finding(
                findings,
                "WORKFLOW_SOURCE_BINDING_NOT_COPIED",
                "adoption must copy the exact workflow_source_binding from the frozen Entry packet",
            )
        else:
            try:
                validate_binding(
                    adopted_workflow_source,
                    root,
                    expected_adoption_mode="entry",
                )
                source_identity = str(
                    entry_workflow_source.get("source_snapshot", {}).get("identity")
                )
                derived_checks.append(
                    {
                        "name": "workflow_source_binding_from_entry",
                        "reviewed_identity": source_identity,
                        "observed_identity": source_identity,
                        "status": "matched",
                    }
                )
            except WorkflowSourceBindingError as exc:
                add_finding(findings, "WORKFLOW_SOURCE_BINDING_INVALID", str(exc))

    readiness = document.get("readiness_review")
    if not isinstance(readiness, dict):
        add_finding(findings, "READINESS_REVIEW_INVALID", "readiness_review must be a mapping")
    else:
        for field in sorted(READINESS_REQUIRED - readiness.keys()):
            add_finding(findings, "READINESS_REVIEW_FIELD_MISSING", field)
        if readiness.get("review_result") != "AUTHORIZATION_READY":
            add_finding(
                findings,
                "READINESS_REVIEW_NOT_READY",
                "readiness review must have result AUTHORIZATION_READY",
            )
        if isinstance(entry_binding, dict) and readiness.get("entry_packet_id") != entry_binding.get("packet_id"):
            add_finding(
                findings,
                "ENTRY_PACKET_ID_MISMATCH",
                "readiness review and adoption record bind different Entry packets",
            )
        if entry_document is not None:
            if readiness.get("review_id") != entry_document.get("review_id"):
                add_finding(findings, "READINESS_REVIEW_ID_MISMATCH", "review_id differs from Entry packet")
            if readiness.get("snapshot_id") != entry_document.get("snapshot_id"):
                add_finding(findings, "READINESS_SNAPSHOT_ID_MISMATCH", "snapshot_id differs from Entry packet")
        review_raw = read_bytes(root, readiness.get("review_artifact"), findings, "Entry review artifact")
        if review_raw is not None:
            observed_review_identity = f"sha256:{hashlib.sha256(review_raw).hexdigest()}"
            reviewed_identity = readiness.get("review_artifact_identity")
            review_matched = reviewed_identity == observed_review_identity
            derived_checks.append(
                {
                    "name": "entry_review_artifact",
                    "reviewed_identity": str(reviewed_identity),
                    "observed_identity": observed_review_identity,
                    "status": "matched" if review_matched else "mismatch",
                }
            )
            if not review_matched:
                add_finding(findings, "REVIEW_ARTIFACT_HASH_MISMATCH", "review artifact bytes changed")
            frontmatter = parse_frontmatter(review_raw, findings)
            if frontmatter is not None:
                expected_review_binding = {
                    "review_id": readiness.get("review_id"),
                    "review_result": readiness.get("review_result"),
                    "packet_id": readiness.get("entry_packet_id"),
                    "snapshot_id": readiness.get("snapshot_id"),
                }
                observed_review_binding = {
                    field: frontmatter.get(field) for field in expected_review_binding
                }
                if observed_review_binding != expected_review_binding:
                    add_finding(
                        findings,
                        "REVIEW_ARTIFACT_BINDING_MISMATCH",
                        "review artifact frontmatter must bind the exact Entry packet and snapshot",
                    )

    target = document.get("authorization_target")
    target_id = target.get("target_id") if isinstance(target, dict) else None
    if not isinstance(target, dict):
        add_finding(findings, "AUTHORIZATION_TARGET_INVALID", "authorization_target must be a mapping")
    else:
        for field in sorted(TARGET_REQUIRED - target.keys()):
            add_finding(findings, "AUTHORIZATION_TARGET_FIELD_MISSING", field)
    reviewed_target: dict[str, Any] | None = None
    reviewed_target_document: dict[str, Any] | None = None
    if entry_document is not None:
        candidate_reviewed_target = entry_document.get("authorization_target")
        reviewed_target = candidate_reviewed_target if isinstance(candidate_reviewed_target, dict) else None
        if not isinstance(reviewed_target, dict):
            add_finding(findings, "ENTRY_AUTHORIZATION_TARGET_INVALID", "Entry packet target is missing")
        elif isinstance(target, dict):
            derived_target = {
                "path": reviewed_target.get("target_path"),
                "target_id": reviewed_target.get("target_id"),
                "file_sha256": reviewed_target.get("target_file_sha256"),
                "batch_id": reviewed_target.get("batch_id"),
                "packet_id": reviewed_target.get("packet_id"),
            }
            target_matched = all(target.get(key) == value for key, value in derived_target.items())
            derived_checks.append(
                {
                    "name": "authorization_target_from_entry",
                    "reviewed_identity": str(derived_target.get("target_id")),
                    "observed_identity": str(target.get("target_id")),
                    "status": "matched" if target_matched else "mismatch",
                }
            )
            if not target_matched:
                add_finding(
                    findings,
                    "AUTHORIZATION_TARGET_NOT_DERIVED",
                    "adoption target must equal the target derived from the frozen Entry packet",
                )
            reviewed_target_raw = read_bytes(
                root,
                reviewed_target.get("target_path"),
                findings,
                "reviewed authorization target",
            )
            if reviewed_target_raw is not None:
                reviewed_target_document = parse_mapping(
                    reviewed_target_raw, findings, "reviewed authorization target"
                )

    user_result = document.get("user_result")
    answer = None
    if not isinstance(user_result, dict):
        add_finding(findings, "USER_RESULT_INVALID", "user_result must be a mapping")
    else:
        for field in sorted(USER_RESULT_REQUIRED - user_result.keys()):
            add_finding(findings, "USER_RESULT_FIELD_MISSING", field)
        answer = user_result.get("answer")
        if answer not in {"authorize", "decline", "conditional"}:
            add_finding(
                findings,
                "USER_ANSWER_INVALID",
                "user_result answer must be authorize, decline, or conditional",
            )
        if target_id is not None and user_result.get("target_id") != target_id:
            add_finding(
                findings,
                "AUTHORIZATION_TARGET_MISMATCH",
                "user result does not bind the reviewed authorization target",
            )
        if reviewed_target is not None and user_result.get("path") != reviewed_target.get("user_result_path"):
            add_finding(
                findings,
                "USER_RESULT_PATH_NOT_DERIVED",
                "user result path must come from the frozen Entry authorization target",
            )
        result_raw = read_bytes(root, user_result.get("path"), findings, "user result")
        if result_raw is not None:
            observed_result_sha = hashlib.sha256(result_raw).hexdigest()
            if user_result.get("file_sha256") != observed_result_sha:
                add_finding(findings, "USER_RESULT_FILE_HASH_MISMATCH", "user result bytes changed")
            result_document = parse_mapping(result_raw, findings, "user result")
            identity_field = user_result.get("identity_field")
            if (
                not isinstance(identity_field, str)
                or result_document is None
                or result_document.get(identity_field) != user_result.get("identity")
            ):
                add_finding(
                    findings,
                    "USER_RESULT_IDENTITY_MISMATCH",
                    "user result identity must derive from its declared top-level identity field",
                )
            if result_document is not None and reviewed_target_document is not None:
                if set(result_document) != USER_RESULT_DOCUMENT_FIELDS:
                    add_finding(
                        findings,
                        "USER_RESULT_SCHEMA_INVALID",
                        "user result must contain exactly result_id, target_id, answer, and conditions",
                    )
                conditions = result_document.get("conditions")
                if answer == "conditional":
                    if not (
                        isinstance(conditions, list)
                        and conditions
                        and all(isinstance(item, str) and item.strip() for item in conditions)
                    ):
                        add_finding(
                            findings,
                            "USER_RESULT_CONDITIONS_INVALID",
                            "a conditional answer requires a nonempty list of explicit conditions",
                        )
                elif conditions != []:
                    add_finding(
                        findings,
                        "USER_RESULT_CONDITIONS_INVALID",
                        "authorize and decline require conditions: []",
                    )
                decision_id = reviewed_target_document.get("decision_id")
                try:
                    result_digest = omitted_top_level_field_digest(
                        result_raw, str(identity_field)
                    )
                except AuthorizationTargetContractError as exc:
                    add_finding(
                        findings,
                        "USER_RESULT_IDENTITY_NOT_DERIVED",
                        str(exc),
                    )
                else:
                    expected_result_id = f"{decision_id}-result-sha256:{result_digest}"
                    if (
                        result_document.get(identity_field) != expected_result_id
                        or user_result.get("identity") != expected_result_id
                    ):
                        add_finding(
                            findings,
                            "USER_RESULT_IDENTITY_NOT_DERIVED",
                            "user result identity must derive from exact result bytes with its one top-level identity line omitted",
                        )
            if result_document is not None and result_document.get("target_id") != target_id:
                add_finding(
                    findings,
                    "USER_RESULT_TARGET_MISMATCH",
                    "user result file does not bind the reviewed authorization target",
                )
            if result_document is not None and result_document.get("answer") != answer:
                add_finding(
                    findings,
                    "USER_ANSWER_NOT_DERIVED",
                    "adoption answer must equal the answer in the identity-bound user result",
                )

    adopted_v = document.get("adopted_v")
    if answer == "authorize":
        if not isinstance(adopted_v, dict) or set(adopted_v) != ADOPTED_V_REQUIRED:
            add_finding(
                findings,
                "ADOPTED_V_INVALID",
                "exact authorization requires adopted_v with decision_id, record_path, result_path, result_identity, and target_id",
            )
        else:
            expected_adopted_v = {
                "decision_id": (
                    reviewed_target_document.get("decision_id")
                    if reviewed_target_document is not None
                    else None
                ),
                "record_path": (
                    reviewed_target_document.get("decision_record_path")
                    if reviewed_target_document is not None
                    else None
                ),
                "result_path": (
                    user_result.get("path") if isinstance(user_result, dict) else None
                ),
                "result_identity": (
                    user_result.get("identity") if isinstance(user_result, dict) else None
                ),
                "target_id": target_id,
            }
            if adopted_v != expected_adopted_v:
                add_finding(
                    findings,
                    "ADOPTED_V_NOT_DERIVED",
                    "adopted_v must derive exactly from the reviewed target and identity-bound user result",
                )
    elif adopted_v is not None:
        add_finding(
            findings,
            "ADOPTED_V_CREATED_AUTHORITY",
            "decline, conditional answer, or invalid answer requires adopted_v: null",
        )

    all_matched = not has_actionable_findings(findings)
    fidelity = document.get("answer_fidelity")
    result = document.get("entry_result")
    transition = document.get("reviewed_state_transition")
    consequence = document.get("maximum_consequence")
    expected_fidelity = {
        "authorize": "exact authorize",
        "decline": "decline",
        "conditional": "conditional change",
    }.get(answer)
    if expected_fidelity is not None and fidelity != expected_fidelity:
        add_finding(
            findings,
            "ANSWER_FIDELITY_MISMATCH",
            f"answer {answer} requires answer_fidelity: {expected_fidelity}",
        )

    if answer == "authorize" and all_matched:
        if result != "ENTRY_READY":
            add_finding(findings, "ADOPTION_RESULT_INVALID", "exact unchanged authorization requires ENTRY_READY")
        if is_none_transition(transition):
            add_finding(findings, "STATE_TRANSITION_MISSING", "ENTRY_READY requires the exact reviewed state transition")
        if consequence in {None, "none"}:
            add_finding(findings, "MAXIMUM_CONSEQUENCE_MISSING", "ENTRY_READY requires a bounded dispatch consequence")
        if reviewed_target is not None and transition != reviewed_target.get("proposed_state_transition"):
            add_finding(
                findings,
                "STATE_TRANSITION_NOT_DERIVED",
                "authorized state transition must equal the frozen Entry target transition",
            )
        expected_consequence = (
            reviewed_target_document.get("authorize_consequence")
            if reviewed_target_document is not None
            else None
        )
        if consequence != expected_consequence:
            add_finding(
                findings,
                "MAXIMUM_CONSEQUENCE_NOT_DERIVED",
                "authorized maximum consequence must equal the frozen target consequence",
            )
    elif answer == "decline" and all_matched:
        if result != "DECLINED":
            add_finding(findings, "ADOPTION_RESULT_INVALID", "decline requires DECLINED")
        if not is_none_transition(transition) or consequence not in {None, "none"}:
            add_finding(findings, "DECLINE_CREATED_AUTHORITY", "decline must not create authority")
    elif answer == "conditional" and all_matched:
        if result != "REVIEW_REQUIRED":
            add_finding(findings, "ADOPTION_RESULT_INVALID", "conditional answer requires REVIEW_REQUIRED")
        if not is_none_transition(transition) or consequence not in {None, "none"}:
            add_finding(findings, "CONDITIONAL_ANSWER_CREATED_AUTHORITY", "conditional answer must not create authority")
    elif not all_matched:
        if result not in {"REVIEW_REQUIRED", "BLOCKED"}:
            add_finding(
                findings,
                "STALE_ADOPTION_CREATED_AUTHORITY",
                "derived identity mismatch permits only REVIEW_REQUIRED or BLOCKED",
            )
        if not is_none_transition(transition) or consequence not in {None, "none"}:
            add_finding(
                findings,
                "STALE_ADOPTION_CREATED_AUTHORITY",
                "derived identity mismatch must not apply a transition or dispatch consequence",
            )

    payload_sha256 = hashlib.sha256(canonical_payload(document)).hexdigest()
    expected_id = computed_adoption_id(document, payload_sha256)
    declared_id = document.get("adoption_id")
    if phase == "draft" and declared_id is not None:
        add_finding(findings, "DRAFT_ALREADY_FROZEN", "draft requires adoption_id to be absent")
    elif phase == "frozen":
        if declared_id is None:
            add_finding(findings, "ADOPTION_ID_MISSING", "frozen record requires adoption_id")
        elif declared_id != expected_id:
            add_finding(
                findings,
                "ADOPTION_ID_MISMATCH",
                f"declared {declared_id} does not equal computed {expected_id}",
            )

    finding_summary = finalize_findings(findings)
    output: dict[str, Any] = {
        "validator": VALIDATOR,
        "adoption_path": document.get("adoption_path"),
        "adoption_payload_sha256": payload_sha256,
        "computed_adoption_id": expected_id,
        "derived_binding_checks": derived_checks,
        "authorization_adoption_valid": finding_summary["ready"],
        "findings": finding_summary["findings"],
        "blocking_findings": finding_summary["blocking_findings"],
        "repair_findings": finding_summary["repair_findings"],
        "advisories": finding_summary["advisories"],
        "finding_effect_counts": finding_summary["finding_effect_counts"],
    }
    canonical = json.dumps(output, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    output["validation_id"] = f"authorization-adoption-validation-sha256:{hashlib.sha256(canonical).hexdigest()}"
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path)
    parser.add_argument("--phase", choices=("draft", "frozen"), default="frozen")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.phase != "audit":
        print("legacy authority writer is closed; use frontier_provenance_cli.py", file=sys.stderr)
        return 2
    try:
        document = yaml.safe_load(args.record.read_text())
    except (OSError, yaml.YAMLError) as exc:
        print(f"cannot read adoption record: {exc}", file=sys.stderr)
        return 2
    if not isinstance(document, dict):
        print("adoption record must be a YAML mapping", file=sys.stderr)
        return 2
    result = validate(document, args.phase, args.root)
    rendered = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered)
    else:
        sys.stdout.write(rendered)
    return 0 if result["authorization_adoption_valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
