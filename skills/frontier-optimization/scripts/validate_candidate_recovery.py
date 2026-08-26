#!/usr/bin/env python3
"""Check retained candidate content and latest accounting for a proposed use."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from identity_bindings import (
    PACKAGE_PATH_SIZE_SHA256_V1,
    IdentityBindingError,
    load_file_binding,
    tree_inventory,
)
from finding_effects import add_finding, finalize_findings
from validate_candidate_package import (
    FINAL_MANIFEST_CONTRACT,
    LEGACY_FINAL_MANIFEST_CONTRACT,
    resolve_manifest,
    validate_candidate_inventory,
    validate_candidate_package,
)

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required to validate candidate recovery") from exc


VALIDATOR = "frontier-candidate-recovery-preflight/6"
REQUIRED_FIELDS = {
    "recovery_preflight_path",
    "prior_campaign_generation",
    "campaign_generation",
    "prior_closeout",
    "lineage_sources",
    "inherited_budget",
    "candidate_root",
    "requested_candidate_id",
    "review_mode",
    "candidate_mutation",
    "new_proposal_attempts",
}


def canonical_payload(document: dict[str, Any]) -> bytes:
    payload = dict(document)
    payload.pop("recovery_preflight_id", None)
    return yaml.safe_dump(payload, sort_keys=False, allow_unicode=True).encode()


def package_inventory(root: Path) -> tuple[list[dict[str, Any]], str]:
    members, identity = tree_inventory(root, PACKAGE_PATH_SIZE_SHA256_V1)
    return members, identity.removeprefix("sha256:")


def validate(
    document: dict[str, Any],
    phase: str,
    repo_root: Path,
) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    publication_state = document.get("publication_state", "published-recovery")
    if publication_state not in {"prepublication", "published-recovery"}:
        add_finding(findings, "PUBLICATION_STATE_INVALID",
                    "publication_state must be prepublication or published-recovery")
    prepublication = publication_state == "prepublication"
    required = REQUIRED_FIELDS | (
        {"working_inventory"} if prepublication
        else {"candidate_manifest_path", "requested_manifest_sha256"}
    )
    for field in sorted(required - document.keys()):
        add_finding(findings, "REQUIRED_FIELD_MISSING", field)

    lineage = document.get("lineage_sources")
    bound_lineage: dict[str, str] = {}
    lineage_documents: dict[str, dict[str, Any]] = {}
    if not isinstance(lineage, dict):
        add_finding(
            findings,
            "LINEAGE_SOURCES_INVALID",
            "lineage_sources must bind closeout, handoff, and budget files",
        )
    else:
        for role in ("closeout", "handoff", "budget"):
            try:
                bound = load_file_binding(
                    repo_root,
                    lineage.get(role),
                    f"lineage_sources.{role}",
                    expected_identity_field=None,
                )
                bound_lineage[role] = bound.identity
                try:
                    parsed = yaml.safe_load(bound.raw)
                except yaml.YAMLError as exc:
                    raise IdentityBindingError(
                        f"lineage_sources.{role} is not valid YAML: {exc}"
                    ) from exc
                if not isinstance(parsed, dict):
                    raise IdentityBindingError(
                        f"lineage_sources.{role} must contain a source record mapping"
                    )
                lineage_documents[role] = parsed
            except IdentityBindingError as exc:
                add_finding(findings, "LINEAGE_SOURCE_INVALID", str(exc))

    prior_generation = document.get("prior_campaign_generation")
    generation = document.get("campaign_generation")
    if (
        not isinstance(prior_generation, int)
        or isinstance(prior_generation, bool)
        or prior_generation < 1
        or generation != prior_generation + 1
    ):
        add_finding(
            findings,
            "GENERATION_LINEAGE_INVALID",
            "campaign_generation must equal prior_campaign_generation + 1",
        )

    closeout = document.get("prior_closeout")
    if not isinstance(closeout, dict):
        add_finding(findings, "CLOSEOUT_LINEAGE_INVALID", "prior_closeout must be a mapping")
    else:
        if closeout.get("event") != "CLOSEOUT_COMPLETE":
            add_finding(
                findings,
                "CLOSEOUT_INCOMPLETE",
                "prior closeout event must be CLOSEOUT_COMPLETE",
            )
        if closeout.get("campaign_generation") != prior_generation:
            add_finding(
                findings,
                "CLOSEOUT_LINEAGE_INVALID",
                "prior closeout generation does not match prior_campaign_generation",
            )
        if closeout.get("campaign_status") not in {"stopped", "halted"}:
            add_finding(
                findings,
                "CLOSEOUT_STATUS_INVALID",
                "prior closeout status must be stopped or halted",
            )
        if closeout.get("unresolved_claims") != []:
            add_finding(
                findings,
                "UNRESOLVED_CLAIMS",
                "post-closeout recovery requires no unresolved claim branch",
            )
        if closeout.get("active_workers") != []:
            add_finding(
                findings,
                "ACTIVE_WORKERS",
                "post-closeout recovery requires no active worker",
            )
        for field in ("closeout_identity", "final_handoff_identity"):
            if not isinstance(closeout.get(field), str) or not closeout[field].strip():
                add_finding(
                    findings,
                    "CLOSEOUT_LINEAGE_INVALID",
                    f"prior_closeout requires {field}",
                )
        if bound_lineage and (
            closeout.get("closeout_identity") != bound_lineage.get("closeout")
            or closeout.get("final_handoff_identity") != bound_lineage.get("handoff")
        ):
            add_finding(
                findings,
                "CLOSEOUT_LINEAGE_NOT_DERIVED",
                "closeout and handoff identities must derive from bound source bytes",
            )
        closeout_source = lineage_documents.get("closeout")
        closeout_facts = (
            "event",
            "campaign_generation",
            "campaign_status",
            "unresolved_claims",
            "active_workers",
        )
        if closeout_source is not None and any(
            closeout.get(field) != closeout_source.get(field)
            for field in closeout_facts
        ):
            add_finding(
                findings,
                "CLOSEOUT_FACTS_NOT_DERIVED",
                "closeout state, generation, claims, and workers must derive from the bound closeout record",
            )
        handoff_source = lineage_documents.get("handoff")
        if handoff_source is not None and handoff_source.get("handoff_complete") is not True:
            add_finding(
                findings,
                "HANDOFF_FACTS_NOT_DERIVED",
                "bound handoff record must report handoff_complete: true",
            )

    budget = document.get("inherited_budget")
    if not isinstance(budget, dict):
        add_finding(findings, "BUDGET_LINEAGE_INVALID", "inherited_budget must be a mapping")
    else:
        for field in ("proposal_attempt_ceiling", "actual_spend", "unknown_spend"):
            value = budget.get(field)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                add_finding(
                    findings,
                    "BUDGET_LINEAGE_INVALID",
                    f"inherited_budget {field} must be a nonnegative integer",
                )
        ceiling = budget.get("proposal_attempt_ceiling")
        spent = budget.get("actual_spend")
        unknown = budget.get("unknown_spend")
        if all(isinstance(value, int) and not isinstance(value, bool) for value in (ceiling, spent, unknown)):
            if spent + unknown > ceiling:
                add_finding(
                    findings,
                    "BUDGET_LINEAGE_INVALID",
                    "actual and unknown spend exceed the inherited ceiling",
                )
        if budget.get("active_reservations") != []:
            add_finding(
                findings,
                "ACTIVE_RESERVATIONS",
                "complete closeout must not carry active reservations",
            )
        if not isinstance(budget.get("budget_identity"), str) or not budget["budget_identity"].strip():
            add_finding(
                findings,
                "BUDGET_LINEAGE_INVALID",
                "inherited_budget requires budget_identity",
            )
        elif bound_lineage and budget.get("budget_identity") != bound_lineage.get("budget"):
            add_finding(
                findings,
                "BUDGET_LINEAGE_NOT_DERIVED",
                "budget identity must derive from the bound budget source bytes",
            )
        budget_source = lineage_documents.get("budget")
        budget_facts = (
            "proposal_attempt_ceiling",
            "actual_spend",
            "unknown_spend",
            "active_reservations",
        )
        if budget_source is not None and any(
            budget.get(field) != budget_source.get(field) for field in budget_facts
        ):
            add_finding(
                findings,
                "BUDGET_FACTS_NOT_DERIVED",
                "budget ceiling, spend, unknown spend, and reservations must derive from the bound budget record",
            )

    expected_mode = "materialization" if prepublication else "recovery-reuse"
    if document.get("review_mode") != expected_mode:
        add_finding(
            findings,
            "REVIEW_MODE_INVALID",
            f"retained material requires review_mode: {expected_mode}",
        )
    if document.get("candidate_mutation") != "prohibited":
        add_finding(
            findings,
            "CANDIDATE_MUTATION_NOT_PROHIBITED",
            "recovery validation must prohibit candidate mutation",
        )
    if document.get("new_proposal_attempts") != 0:
        add_finding(
            findings,
            "ZERO_COST_REUSE_INVALID",
            "byte-identical recovery validation requires zero new proposal attempts",
        )

    # Material identity is checked here; readiness and permission belong to
    # their existing gates. Original parents and review verdicts stay historical.
    manifest: dict[str, Any] | None = None
    if prepublication:
        binding = document.get("working_inventory")
        if not isinstance(binding, dict) or any(
            not isinstance(binding.get(field), str) or not binding[field]
            for field in ("path", "inventory_id", "file_sha256")
        ):
            add_finding(
                findings, "WORKING_INVENTORY_REQUIRED",
                "prepublication reuse requires the existing exact working inventory",
            )
            binding = {}
        package_validation = validate_candidate_inventory(
            repo_root, document.get("candidate_root"), binding.get("path"),
            expected_candidate_id=document.get("requested_candidate_id"),
            expected_inventory_id=binding.get("inventory_id"),
            expected_inventory_sha256=binding.get("file_sha256"),
        )
        manifest_sha256 = None
    else:
        package_validation = validate_candidate_package(
            repo_root,
            document.get("candidate_root"),
            document.get("candidate_manifest_path"),
            expected_candidate_id=document.get("requested_candidate_id"),
            expected_manifest_sha256=document.get("requested_manifest_sha256"),
            allow_missing_workflow_source_identity=True,
            allow_legacy_manifest=True,
            require_final_manifest=False,
        )
        manifest_sha256 = package_validation["manifest_sha256"]
        try:
            _, manifest_path = resolve_manifest(
                repo_root, document.get("candidate_manifest_path")
            )
            parsed = yaml.safe_load(manifest_path.read_bytes())
            if isinstance(parsed, dict):
                manifest = parsed
        except (IdentityBindingError, OSError, ValueError, yaml.YAMLError):
            pass
        if manifest is not None:
            if manifest.get("manifest_contract") not in {
                None, LEGACY_FINAL_MANIFEST_CONTRACT, FINAL_MANIFEST_CONTRACT,
            }:
                add_finding(findings, "MANIFEST_CONTRACT_INVALID",
                            "unsupported historical manifest contract")
            producing_generation = manifest.get("campaign_generation")
            if producing_generation is not None and (
                not isinstance(producing_generation, int)
                or isinstance(producing_generation, bool)
                or producing_generation < 1
                or (isinstance(prior_generation, int)
                    and producing_generation > prior_generation)
            ):
                add_finding(findings, "PRODUCING_GENERATION_INVALID",
                            "recorded production must precede the recovery generation")

    members = package_validation["members"]
    canonical_candidate_id = package_validation["candidate_id"]
    code_map = {
        "CANDIDATE_PACKAGE_UNREADABLE": "CANDIDATE_RECOVERY_UNREADABLE",
        "CANDIDATE_MANIFEST_UNREADABLE": "CANDIDATE_RECOVERY_UNREADABLE",
        "CANDIDATE_MANIFEST_IDENTITY_MISMATCH": "REQUESTED_MANIFEST_IDENTITY_MISMATCH",
        "EXPECTED_CANDIDATE_IDENTITY_MISMATCH": "REQUESTED_CANDIDATE_IDENTITY_MISMATCH",
    }
    for finding in package_validation["findings"]:
        detail = finding["detail"]
        if finding["code"] == "CANDIDATE_MANIFEST_IDENTITY_MISMATCH":
            detail = detail.replace("declared", "requested").replace(
                "observed", "recomputed"
            )
        add_finding(
            findings,
            code_map.get(finding["code"], finding["code"]),
            detail,
        )
    for advisory in package_validation.get("advisories", []):
        add_finding(findings, advisory["code"], advisory["detail"])

    payload_sha256 = hashlib.sha256(canonical_payload(document)).hexdigest()
    expected_id = f"candidate-recovery-preflight-sha256:{payload_sha256}"
    declared_id = document.get("recovery_preflight_id")
    if phase == "draft" and declared_id is not None:
        add_finding(
            findings,
            "DRAFT_ALREADY_FROZEN",
            "draft recovery validation requires recovery_preflight_id to be absent",
        )
    elif phase == "frozen":
        if declared_id is None:
            add_finding(findings, "RECOVERY_PREFLIGHT_ID_MISSING", "frozen preflight requires recovery_preflight_id")
        elif declared_id != expected_id:
            add_finding(
                findings,
                "RECOVERY_PREFLIGHT_ID_MISMATCH",
                f"declared {declared_id!r}; computed {expected_id!r}",
            )
    elif phase not in {"draft", "frozen", "audit"}:
        add_finding(findings, "PHASE_INVALID", "phase must be draft, frozen, or audit")

    finding_summary = finalize_findings(findings)
    result = {
        "validator": VALIDATOR,
        "recovery_preflight_path": document.get("recovery_preflight_path"),
        "prior_campaign_generation": prior_generation,
        "campaign_generation": generation,
        "candidate_manifest_path": document.get("candidate_manifest_path"),
        "recomputed_manifest_sha256": manifest_sha256,
        "recomputed_candidate_id": canonical_candidate_id,
        "recomputed_members": members,
        "computed_recovery_preflight_id": expected_id,
        "recovery_ready": finding_summary["ready"],
        "findings": finding_summary["findings"],
        "blocking_findings": finding_summary["blocking_findings"],
        "repair_findings": finding_summary["repair_findings"],
        "advisories": finding_summary["advisories"],
        "finding_effect_counts": finding_summary["finding_effect_counts"],
    }
    if prepublication:
        result["recomputed_inventory_id"] = package_validation["inventory_id"]
        result["recomputed_inventory_sha256"] = package_validation["inventory_sha256"]
    result["publication_state"] = "prepublication" if prepublication else "published-recovery"
    result["authority_effect"] = "content-and-accounting-only; no readiness or permission granted"
    return result


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("preflight", type=Path)
    parser.add_argument("--phase", choices=("draft", "frozen", "audit"), required=True)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        document = yaml.safe_load(args.preflight.read_bytes())
    except (OSError, yaml.YAMLError) as exc:
        print(f"cannot read recovery preflight: {exc}", file=sys.stderr)
        return 2
    if not isinstance(document, dict):
        print("recovery preflight must contain a YAML mapping", file=sys.stderr)
        return 2
    result = validate(document, args.phase, args.repo_root.resolve())
    if args.output is not None:
        write_json(args.output, result)
    else:
        print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["recovery_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
