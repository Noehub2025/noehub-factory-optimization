#!/usr/bin/env python3
"""Validate the post-answer Frontier authorization adoption record."""

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
    raise SystemExit("PyYAML is required to validate Frontier authorization adoption") from exc


VALIDATOR = "frontier-authorization-adoption/1"
REQUIRED_FIELDS = {
    "adoption_path",
    "entry_packet_id",
    "readiness_review",
    "authorization_target",
    "user_result",
    "binding_checks",
    "answer_fidelity",
    "reviewed_state_transition",
    "entry_result",
    "maximum_consequence",
}
READINESS_REQUIRED = {
    "review_id",
    "review_result",
    "review_artifact",
    "review_artifact_identity",
    "snapshot_id",
    "entry_packet_id",
}
USER_RESULT_REQUIRED = {"path", "identity", "target_id", "answer"}
BINDING_CHECK_REQUIRED = {"name", "reviewed_identity", "observed_identity", "status"}


def canonical_payload(document: dict[str, Any]) -> bytes:
    payload = dict(document)
    payload.pop("adoption_id", None)
    return yaml.safe_dump(payload, sort_keys=False, allow_unicode=True).encode()


def computed_adoption_id(document: dict[str, Any], digest: str) -> str:
    return f"authorization-adoption-sha256:{digest}"


def add_finding(findings: list[dict[str, str]], code: str, detail: str) -> None:
    finding = {"code": code, "detail": detail}
    if finding not in findings:
        findings.append(finding)


def is_none_transition(value: Any) -> bool:
    return value is None or value == "none"


def validate(document: dict[str, Any], phase: str) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    for field in sorted(REQUIRED_FIELDS - document.keys()):
        add_finding(findings, "REQUIRED_FIELD_MISSING", field)

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
        if readiness.get("entry_packet_id") != document.get("entry_packet_id"):
            add_finding(
                findings,
                "ENTRY_PACKET_ID_MISMATCH",
                "readiness review and adoption record bind different Entry packets",
            )

    target = document.get("authorization_target")
    target_id = target.get("target_id") if isinstance(target, dict) else None
    if not isinstance(target, dict) or not isinstance(target_id, str) or not target_id:
        add_finding(
            findings,
            "AUTHORIZATION_TARGET_INVALID",
            "authorization_target requires a nonempty target_id",
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

    checks = document.get("binding_checks")
    all_matched = True
    if not isinstance(checks, list) or not checks:
        add_finding(
            findings,
            "BINDING_CHECKS_INVALID",
            "binding_checks must be a nonempty list",
        )
        all_matched = False
    else:
        for index, check in enumerate(checks):
            if not isinstance(check, dict):
                add_finding(
                    findings,
                    "BINDING_CHECK_INVALID",
                    f"binding_checks[{index}] must be a mapping",
                )
                all_matched = False
                continue
            for field in sorted(BINDING_CHECK_REQUIRED - check.keys()):
                add_finding(
                    findings,
                    "BINDING_CHECK_FIELD_MISSING",
                    f"binding_checks[{index}].{field}",
                )
            matched = (
                check.get("status") == "matched"
                and check.get("reviewed_identity") == check.get("observed_identity")
            )
            if not matched:
                all_matched = False

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
            add_finding(
                findings,
                "STATE_TRANSITION_MISSING",
                "ENTRY_READY requires the exact reviewed state transition",
            )
        if consequence in {None, "none"}:
            add_finding(
                findings,
                "MAXIMUM_CONSEQUENCE_MISSING",
                "ENTRY_READY requires a bounded dispatch consequence",
            )
    elif answer == "decline" and all_matched:
        if result != "DECLINED":
            add_finding(findings, "ADOPTION_RESULT_INVALID", "decline requires DECLINED")
        if not is_none_transition(transition) or consequence not in {None, "none"}:
            add_finding(
                findings,
                "DECLINE_CREATED_AUTHORITY",
                "decline must not apply a state transition or dispatch consequence",
            )
    elif answer == "conditional" and all_matched:
        if result != "REVIEW_REQUIRED":
            add_finding(
                findings,
                "ADOPTION_RESULT_INVALID",
                "conditional answer requires REVIEW_REQUIRED",
            )
        if not is_none_transition(transition) or consequence not in {None, "none"}:
            add_finding(
                findings,
                "CONDITIONAL_ANSWER_CREATED_AUTHORITY",
                "conditional answer must not apply a state transition or dispatch consequence",
            )
    elif not all_matched:
        if result not in {"REVIEW_REQUIRED", "BLOCKED"}:
            add_finding(
                findings,
                "STALE_ADOPTION_CREATED_AUTHORITY",
                "identity mismatch permits only REVIEW_REQUIRED or BLOCKED",
            )
        if not is_none_transition(transition) or consequence not in {None, "none"}:
            add_finding(
                findings,
                "STALE_ADOPTION_CREATED_AUTHORITY",
                "identity mismatch must not apply a state transition or dispatch consequence",
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

    findings.sort(key=lambda item: (item["code"], item["detail"]))
    output: dict[str, Any] = {
        "validator": VALIDATOR,
        "adoption_path": document.get("adoption_path"),
        "adoption_payload_sha256": payload_sha256,
        "computed_adoption_id": expected_id,
        "authorization_adoption_valid": not findings,
        "findings": findings,
    }
    canonical = json.dumps(output, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    output["validation_id"] = f"authorization-adoption-validation-sha256:{hashlib.sha256(canonical).hexdigest()}"
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path)
    parser.add_argument("--phase", choices=("draft", "frozen"), default="frozen")
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        document = yaml.safe_load(args.record.read_text())
    except (OSError, yaml.YAMLError) as exc:
        print(f"cannot read adoption record: {exc}", file=sys.stderr)
        return 2
    if not isinstance(document, dict):
        print("adoption record must be a YAML mapping", file=sys.stderr)
        return 2
    result = validate(document, args.phase)
    rendered = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered)
    else:
        sys.stdout.write(rendered)
    return 0 if result["authorization_adoption_valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
