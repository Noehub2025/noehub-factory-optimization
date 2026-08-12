#!/usr/bin/env python3
"""Validate a Frontier Entry authorization-readiness packet schema."""

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
    raise SystemExit("PyYAML is required to validate Frontier Entry packets") from exc


VALIDATOR = "frontier-entry-packet-schema/1"
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
    "snapshot_root",
    "snapshot_manifest",
    "snapshot_id",
    "snapshot_inputs",
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
    "target_id",
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
    "proposed_state_transition",
}
PROPOSED_TRANSITION_REQUIRED = {"budget", "selection", "lifecycle"}


def canonical_payload(document: dict[str, Any]) -> bytes:
    payload = dict(document)
    payload.pop("packet_id", None)
    return yaml.safe_dump(payload, sort_keys=False, allow_unicode=True).encode()


def computed_packet_id(document: dict[str, Any], digest: str) -> str:
    return f"entry-{document.get('review_id', 'UNKNOWN')}-packet-sha256:{digest}"


def add_finding(findings: list[dict[str, str]], code: str, detail: str) -> None:
    finding = {"code": code, "detail": detail}
    if finding not in findings:
        findings.append(finding)


def validate(document: dict[str, Any], phase: str) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    required = set(COMMON_REQUIRED)
    if phase == "frozen":
        required |= FROZEN_REQUIRED
    for field in sorted(required):
        if field not in document:
            add_finding(findings, "REQUIRED_FIELD_MISSING", field)

    if document.get("review_kind") != "entry":
        add_finding(findings, "REVIEW_KIND_INVALID", "review_kind must be entry")
    stage = document.get("review_stage")
    if phase != "audit" and stage not in {
        "authorization-readiness",
        "spend-readiness",
    }:
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
        add_finding(
            findings,
            "RECOVERY_LINEAGE_INVALID",
            "generation 1 requires recovery_lineage: null",
        )
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
                add_finding(
                    findings,
                    "RECOVERY_LINEAGE_FIELD_MISSING",
                    field,
                )

    selected = document.get("selected_batches")
    if not isinstance(selected, list) or not selected:
        add_finding(
            findings,
            "SELECTED_BATCHES_INVALID",
            "selected_batches must be a nonempty list",
        )

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

    target = document.get("authorization_target")
    if phase != "audit" and stage == "authorization-readiness":
        if not isinstance(target, dict):
            add_finding(
                findings,
                "AUTHORIZATION_TARGET_INVALID",
                "authorization_target must be a mapping",
            )
        else:
            for field in sorted(AUTHORIZATION_TARGET_REQUIRED - target.keys()):
                add_finding(
                    findings,
                    "AUTHORIZATION_TARGET_FIELD_MISSING",
                    field,
                )
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
                    add_finding(
                        findings,
                        "PROPOSED_STATE_TRANSITION_FIELD_MISSING",
                        field,
                    )
    elif phase != "audit" and stage == "spend-readiness":
        if target is not None or document.get("authorization_state") != "not-required":
            add_finding(
                findings,
                "AUTHORIZATION_STATE_INVALID",
                "spend-readiness requires null target and authorization_state: not-required",
            )

    payload_sha256 = hashlib.sha256(canonical_payload(document)).hexdigest()
    expected_packet_id = computed_packet_id(document, payload_sha256)
    declared_packet_id = document.get("packet_id")
    if phase == "draft" and declared_packet_id is not None:
        add_finding(
            findings,
            "DRAFT_ALREADY_FROZEN",
            "draft schema validation requires packet_id to be absent",
        )
    elif phase == "frozen":
        if declared_packet_id is None:
            add_finding(findings, "PACKET_ID_MISSING", "frozen packet requires packet_id")
        elif declared_packet_id != expected_packet_id:
            add_finding(
                findings,
                "PACKET_ID_MISMATCH",
                f"declared {declared_packet_id} does not equal computed {expected_packet_id}",
            )

    findings.sort(key=lambda item: (item["code"], item["detail"]))
    result: dict[str, Any] = {
        "validator": VALIDATOR,
        "review_id": document.get("review_id"),
        "packet_path": document.get("packet_path"),
        "packet_payload_sha256": payload_sha256,
        "computed_packet_id": expected_packet_id,
        "entry_schema_ready": not findings,
        "findings": findings,
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
    result = validate(document, args.phase)
    rendered = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered)
    else:
        sys.stdout.write(rendered)
    return 0 if result["entry_schema_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
