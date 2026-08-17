#!/usr/bin/env python3
"""Validate byte-identical Frontier candidate reuse before opening a generation."""

from __future__ import annotations

import argparse
import hashlib
import json
import posixpath
import sys
from pathlib import Path
from typing import Any

from identity_bindings import (
    PACKAGE_PATH_SIZE_SHA256_V1,
    IdentityBindingError,
    load_file_binding,
    reject_symlink_components,
    tree_inventory,
)
from finding_effects import add_finding, finalize_findings
from validate_candidate_package import (
    FINAL_MANIFEST_CONTRACT,
    LEGACY_FINAL_MANIFEST_CONTRACT,
    validate_candidate_inventory,
    validate_candidate_package,
)

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required to validate candidate recovery") from exc


VALIDATOR = "frontier-candidate-recovery-preflight/5"
LEGACY_SOURCE_CONTRACT = "frontier-legacy-candidate-source-binding/1"
LEGACY_SOURCE_ID_PREFIX = "legacy-candidate-source-binding-sha256:"
LEGACY_AUTHORITY_EFFECT = (
    "historical-provenance-only; fresh recovery-reuse implementation review required"
)
IMPLEMENTATION_REVIEW_RESULTS = {
    "IMPLEMENTATION_READY",
    "IMPLEMENTATION_REPAIR_REQUIRED",
    "EVIDENCE_REQUIRED",
    "PARENT_REVIEW_REQUIRED",
    "BLOCKED",
}
REQUIRED_FIELDS = {
    "recovery_preflight_path",
    "prior_campaign_generation",
    "campaign_generation",
    "prior_closeout",
    "lineage_sources",
    "inherited_budget",
    "candidate_root",
    "candidate_manifest_path",
    "requested_candidate_id",
    "requested_manifest_sha256",
    "review_mode",
    "candidate_mutation",
    "new_proposal_attempts",
}

LEGACY_SOURCE_FIELDS = {
    "legacy_source_binding_id",
    "contract_version",
    "candidate_id",
    "producing_campaign_generation",
    "missing_manifest_field",
    "authority_effect",
    "candidate_manifest",
    "candidate_package_inventory",
    "producing_batch_result",
    "result_validation",
    "implementation_review_packet",
    "implementation_review",
}

LEGACY_ARTIFACT_IDENTITY_FIELDS = {
    "candidate_manifest": None,
    "candidate_package_inventory": "inventory_id",
    "producing_batch_result": "result_packet_id",
    "result_validation": "validation_id",
    "implementation_review_packet": "packet_id",
    "implementation_review": None,
}


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode()


def canonical_payload(document: dict[str, Any]) -> bytes:
    payload = dict(document)
    payload.pop("recovery_preflight_id", None)
    return yaml.safe_dump(payload, sort_keys=False, allow_unicode=True).encode()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_relative(raw: Any, field: str) -> str:
    if not isinstance(raw, str) or not raw.strip() or raw.startswith("/"):
        raise ValueError(f"{field} must be a nonempty repository-relative path")
    normalized = posixpath.normpath(raw.strip().rstrip("/"))
    if normalized in {".", ".."} or normalized.startswith("../"):
        raise ValueError(f"{field} escapes the repository")
    return normalized


def is_sha256_identity(value: Any) -> bool:
    return (
        isinstance(value, str)
        and value.startswith("sha256:")
        and len(value) == 71
        and all(character in "0123456789abcdef" for character in value[7:])
    )


def computed_legacy_source_binding_id(document: dict[str, Any]) -> str:
    payload = dict(document)
    payload.pop("legacy_source_binding_id", None)
    raw = yaml.safe_dump(payload, sort_keys=False, allow_unicode=True).encode()
    return LEGACY_SOURCE_ID_PREFIX + hashlib.sha256(raw).hexdigest()


def markdown_frontmatter(raw: bytes) -> dict[str, Any] | None:
    if not raw.startswith(b"---\n"):
        return None
    _, separator, remainder = raw.partition(b"---\n")
    if not separator:
        return None
    frontmatter, closing, _ = remainder.partition(b"\n---\n")
    if not closing:
        return None
    try:
        value = yaml.safe_load(frontmatter)
    except yaml.YAMLError:
        return None
    return value if isinstance(value, dict) else None


def review_snapshot_packet_matches(
    value: Any, expected_path: str, expected_identity: str
) -> bool:
    """Match the historical semicolon-delimited review binding exactly."""

    if not isinstance(value, str):
        return False
    parts = [part.strip() for part in value.split(";")]
    return (
        len(parts) >= 2
        and all(parts)
        and parts[0] == expected_path
        and parts[1] == expected_identity
    )


def embedded_yaml_identity_matches(
    document: dict[str, Any], field: str, expected_prefix: str
) -> bool:
    identity = document.get(field)
    if not isinstance(identity, str) or not identity.startswith(expected_prefix):
        return False
    payload = dict(document)
    payload.pop(field, None)
    raw = yaml.safe_dump(payload, sort_keys=False, allow_unicode=True).encode()
    return identity.rsplit(":", 1)[-1] == hashlib.sha256(raw).hexdigest()


def embedded_json_identity_matches(
    document: dict[str, Any], field: str, expected_prefix: str
) -> bool:
    identity = document.get(field)
    if not isinstance(identity, str) or not identity.startswith(expected_prefix):
        return False
    payload = dict(document)
    payload.pop(field, None)
    return identity.rsplit(":", 1)[-1] == hashlib.sha256(
        canonical_json(payload)
    ).hexdigest()


def validate_legacy_candidate_source_binding(
    repo_root: Path,
    binding: Any,
    *,
    candidate_manifest_path: Any,
    candidate_manifest_sha256: str | None,
    candidate_id: str | None,
    candidate_members: list[dict[str, Any]],
    candidate_manifest: dict[str, Any] | None,
    prior_campaign_generation: Any,
) -> list[dict[str, str]]:
    """Validate provenance for a manifest created before workflow-source identities."""

    findings: list[dict[str, str]] = []
    try:
        bound_source = load_file_binding(
            repo_root,
            binding,
            "legacy_candidate_source_binding",
            expected_identity_field="legacy_source_binding_id",
        )
    except IdentityBindingError as exc:
        add_finding(findings, "LEGACY_SOURCE_BINDING_INVALID", str(exc))
        return findings

    source = bound_source.document
    if source is None:  # pragma: no cover - load_file_binding enforces a mapping
        add_finding(
            findings,
            "LEGACY_SOURCE_BINDING_INVALID",
            "legacy source binding must contain a YAML mapping",
        )
        return findings
    if set(source) != LEGACY_SOURCE_FIELDS:
        missing = sorted(LEGACY_SOURCE_FIELDS - source.keys())
        extra = sorted(source.keys() - LEGACY_SOURCE_FIELDS)
        add_finding(
            findings,
            "LEGACY_SOURCE_BINDING_SCHEMA_INVALID",
            f"legacy source binding fields differ; missing={missing}; extra={extra}",
        )
    if source.get("contract_version") != LEGACY_SOURCE_CONTRACT:
        add_finding(
            findings,
            "LEGACY_SOURCE_BINDING_CONTRACT_INVALID",
            f"contract_version must be {LEGACY_SOURCE_CONTRACT}",
        )
    expected_binding_id = computed_legacy_source_binding_id(source)
    if source.get("legacy_source_binding_id") != expected_binding_id:
        add_finding(
            findings,
            "LEGACY_SOURCE_BINDING_IDENTITY_MISMATCH",
            "legacy_source_binding_id does not derive from the complete sidecar payload",
        )
    if source.get("missing_manifest_field") != "workflow_source_identity":
        add_finding(
            findings,
            "LEGACY_SOURCE_BINDING_SCOPE_INVALID",
            "legacy binding applies only to an absent workflow_source_identity field",
        )
    if source.get("authority_effect") != LEGACY_AUTHORITY_EFFECT:
        add_finding(
            findings,
            "LEGACY_SOURCE_BINDING_AUTHORITY_INVALID",
            "legacy binding must remain provenance-only and require a fresh recovery review",
        )
    if source.get("candidate_id") != candidate_id:
        add_finding(
            findings,
            "LEGACY_SOURCE_CANDIDATE_MISMATCH",
            "legacy source binding candidate_id does not match the recomputed candidate",
        )
    if candidate_manifest is not None and "workflow_source_identity" in candidate_manifest:
        add_finding(
            findings,
            "LEGACY_SOURCE_BINDING_NOT_APPLICABLE",
            "legacy binding is forbidden when the manifest contains workflow_source_identity",
        )

    bound_artifacts: dict[str, Any] = {}
    for role, identity_field in LEGACY_ARTIFACT_IDENTITY_FIELDS.items():
        try:
            bound_artifacts[role] = load_file_binding(
                repo_root,
                source.get(role),
                f"legacy_source.{role}",
                expected_identity_field=identity_field,
            )
        except IdentityBindingError as exc:
            add_finding(findings, "LEGACY_SOURCE_ARTIFACT_INVALID", str(exc))

    manifest_binding = bound_artifacts.get("candidate_manifest")
    if manifest_binding is not None:
        try:
            expected_manifest_path = safe_relative(
                candidate_manifest_path, "candidate_manifest_path"
            )
        except ValueError as exc:
            add_finding(findings, "LEGACY_SOURCE_CANDIDATE_MISMATCH", str(exc))
        else:
            if manifest_binding.relative_path != expected_manifest_path:
                add_finding(
                    findings,
                    "LEGACY_SOURCE_CANDIDATE_MISMATCH",
                    "legacy source binding names a different candidate manifest path",
                )
        if manifest_binding.file_sha256 != candidate_manifest_sha256:
            add_finding(
                findings,
                "LEGACY_SOURCE_CANDIDATE_MISMATCH",
                "legacy source binding names different candidate manifest bytes",
            )

    inventory_binding = bound_artifacts.get("candidate_package_inventory")
    inventory = inventory_binding.document if inventory_binding is not None else None
    if inventory_binding is not None:
        # Historical final manifests may name the canonical root only through the inventory.
        # Re-run with that bound root so the sidecar cannot substitute a self-consistent file.
        inventory_root = inventory.get("candidate_root") if inventory is not None else None
        inventory_validation = validate_candidate_inventory(
            repo_root,
            inventory_root,
            inventory_binding.relative_path,
            expected_candidate_id=candidate_id,
            expected_inventory_id=inventory_binding.identity,
            expected_inventory_sha256=inventory_binding.file_sha256,
        )
        if not inventory_validation.get("inventory_ready") or (
            inventory is not None and inventory.get("members") != candidate_members
        ):
            add_finding(
                findings,
                "LEGACY_SOURCE_INVENTORY_MISMATCH",
                "bound package inventory does not reproduce the exact candidate root and members",
            )
    manifest_inventory = (
        candidate_manifest.get("package_inventory")
        if isinstance(candidate_manifest, dict)
        else None
    )
    if inventory_binding is not None and (
        not isinstance(manifest_inventory, dict)
        or manifest_inventory.get("path") != inventory_binding.relative_path
        or manifest_inventory.get("inventory_id") != inventory_binding.identity
        or manifest_inventory.get("file_sha256") != inventory_binding.file_sha256
    ):
        add_finding(
            findings,
            "LEGACY_SOURCE_MANIFEST_INVENTORY_MISMATCH",
            "historical manifest does not bind the exact sidecar package inventory",
        )

    result_binding = bound_artifacts.get("producing_batch_result")
    result = result_binding.document if result_binding is not None else None
    producing_generation = source.get("producing_campaign_generation")
    if not isinstance(producing_generation, int) or isinstance(producing_generation, bool):
        add_finding(
            findings,
            "LEGACY_SOURCE_GENERATION_INVALID",
            "producing_campaign_generation must be an integer",
        )
    elif producing_generation != prior_campaign_generation:
        add_finding(
            findings,
            "LEGACY_SOURCE_GENERATION_MISMATCH",
            "sidecar producing generation does not match the preflight prior generation",
        )
    if candidate_manifest is not None and (
        candidate_manifest.get("campaign_generation") != producing_generation
    ):
        add_finding(
            findings,
            "LEGACY_SOURCE_GENERATION_MISMATCH",
            "sidecar producing generation does not match the historical manifest",
        )
    manifest_batch_id = (
        candidate_manifest.get("batch_id")
        if isinstance(candidate_manifest, dict)
        else None
    )
    if result is not None:
        if (
            not embedded_yaml_identity_matches(
                result,
                "result_packet_id",
                f"{manifest_batch_id}-result-sha256:",
            )
            or result.get("candidate_identity") != candidate_id
            or result.get("candidate_manifest")
            != (manifest_binding.relative_path if manifest_binding is not None else None)
            or result.get("campaign_generation") != producing_generation
            or not isinstance(manifest_batch_id, str)
            or result.get("batch_id") != manifest_batch_id
        ):
            add_finding(
                findings,
                "LEGACY_SOURCE_RESULT_MISMATCH",
                "bound producing result does not match the candidate, manifest, and generation",
            )

    validation_binding = bound_artifacts.get("result_validation")
    validation = validation_binding.document if validation_binding is not None else None
    if validation is not None and result_binding is not None:
        if (
            not embedded_json_identity_matches(
                validation,
                "validation_id",
                "batch-result-validation-sha256:",
            )
            or validation.get("result_packet_path") != result_binding.relative_path
            or validation.get("computed_result_packet_id") != result_binding.identity
            or validation.get("batch_id") != manifest_batch_id
            or validation.get("result_structure_ready") is not True
            or validation.get("findings") != []
        ):
            add_finding(
                findings,
                "LEGACY_SOURCE_RESULT_VALIDATION_MISMATCH",
                "bound result validation is not finding-free for the producing result",
            )

    review_packet_binding = bound_artifacts.get("implementation_review_packet")
    review_packet = (
        review_packet_binding.document if review_packet_binding is not None else None
    )
    if review_packet is not None and result_binding is not None and validation_binding is not None:
        packet_manifest = review_packet.get("candidate_manifest")
        packet_inventory = review_packet.get("candidate_package_inventory")
        packet_result = review_packet.get("batch_result")
        packet_validation = review_packet.get("batch_result_validation")
        review_binding = bound_artifacts.get("implementation_review")
        if (
            not embedded_yaml_identity_matches(
                review_packet,
                "packet_id",
                f"implementation-{review_packet.get('review_id')}-packet-sha256:",
            )
            or review_packet.get("review_kind") != "implementation"
            or review_packet.get("review_mode") != "materialization"
            or review_packet.get("candidate_id") != candidate_id
            or review_packet.get("campaign_generation") != producing_generation
            or review_packet.get("batch_id") != manifest_batch_id
            or not isinstance(packet_manifest, dict)
            or packet_manifest.get("path")
            != (manifest_binding.relative_path if manifest_binding is not None else None)
            or packet_manifest.get("file_sha256") != candidate_manifest_sha256
            or not isinstance(packet_inventory, dict)
            or packet_inventory.get("path")
            != (inventory_binding.relative_path if inventory_binding is not None else None)
            or packet_inventory.get("inventory_id")
            != (inventory_binding.identity if inventory_binding is not None else None)
            or packet_inventory.get("file_sha256")
            != (inventory_binding.file_sha256 if inventory_binding is not None else None)
            or not isinstance(packet_result, dict)
            or packet_result.get("path") != result_binding.relative_path
            or packet_result.get("identity") != result_binding.identity
            or packet_result.get("file_sha256") != result_binding.file_sha256
            or not isinstance(packet_validation, dict)
            or packet_validation.get("path") != validation_binding.relative_path
            or packet_validation.get("identity") != validation_binding.identity
            or packet_validation.get("file_sha256") != validation_binding.file_sha256
            or review_packet.get("assigned_review_path")
            != (review_binding.relative_path if review_binding is not None else None)
        ):
            add_finding(
                findings,
                "LEGACY_SOURCE_REVIEW_PACKET_MISMATCH",
                "bound historical implementation-review packet does not close the producing lineage",
            )

    review_binding = bound_artifacts.get("implementation_review")
    review = markdown_frontmatter(review_binding.raw) if review_binding is not None else None
    if review_binding is not None and (
        review is None
        or review.get("review_result") not in IMPLEMENTATION_REVIEW_RESULTS
        or review.get("candidate_id") != candidate_id
        or (
            review_packet is not None
            and review.get("review_id") != review_packet.get("review_id")
        )
        or (
            review_packet_binding is not None
            and not review_snapshot_packet_matches(
                review.get("snapshot_packet"),
                review_packet_binding.relative_path,
                review_packet_binding.identity,
            )
        )
    ):
        add_finding(
            findings,
            "LEGACY_SOURCE_REVIEW_MISMATCH",
            "bound historical implementation review does not match the exact review lineage",
        )
    return findings


def package_inventory(root: Path) -> tuple[list[dict[str, Any]], str]:
    members, identity = tree_inventory(root, PACKAGE_PATH_SIZE_SHA256_V1)
    return members, identity.removeprefix("sha256:")


def validate(
    document: dict[str, Any], phase: str, repo_root: Path
) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    for field in sorted(REQUIRED_FIELDS - document.keys()):
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

    if document.get("review_mode") != "recovery-reuse":
        add_finding(
            findings,
            "REVIEW_MODE_INVALID",
            "byte-identical reuse requires review_mode: recovery-reuse",
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

    manifest_contract: Any = None
    try:
        manifest_relative = safe_relative(
            document.get("candidate_manifest_path"), "candidate_manifest_path"
        )
        manifest_document = yaml.safe_load(
            (repo_root / manifest_relative).read_bytes()
        )
        if isinstance(manifest_document, dict):
            manifest_contract = manifest_document.get("manifest_contract")
    except (OSError, ValueError, yaml.YAMLError):
        pass

    source_workflow_identity = document.get("source_workflow_identity")
    legacy_source_binding = document.get("legacy_candidate_source_binding")
    current_manifest = manifest_contract == FINAL_MANIFEST_CONTRACT
    legacy_manifest = manifest_contract in {
        LEGACY_FINAL_MANIFEST_CONTRACT,
        None,
    }
    legacy_source_mode = legacy_manifest and source_workflow_identity is None
    if current_manifest:
        if source_workflow_identity is not None:
            add_finding(
                findings,
                "SOURCE_WORKFLOW_IDENTITY_RETIRED",
                "version 3 recovery must not contain source_workflow_identity",
            )
        if legacy_source_binding is not None:
            add_finding(
                findings,
                "LEGACY_SOURCE_BINDING_RETIRED",
                "version 3 recovery must not contain a legacy source binding",
            )
    elif legacy_source_mode:
        if not isinstance(legacy_source_binding, dict):
            add_finding(
                findings,
                "LEGACY_SOURCE_BINDING_REQUIRED",
                "an eligible historical manifest without workflow_source_identity requires one bound legacy provenance sidecar",
            )
    elif legacy_manifest:
        if not is_sha256_identity(source_workflow_identity):
            add_finding(
                findings,
                "SOURCE_WORKFLOW_IDENTITY_INVALID",
                "historical source_workflow_identity must be a lowercase sha256 identity",
            )
        if legacy_source_binding is not None:
            add_finding(
                findings,
                "SOURCE_WORKFLOW_BINDING_AMBIGUOUS",
                "historical workflow identity and legacy provenance binding are mutually exclusive",
            )

    package_validation = validate_candidate_package(
        repo_root,
        document.get("candidate_root"),
        document.get("candidate_manifest_path"),
        expected_candidate_id=document.get("requested_candidate_id"),
        expected_manifest_sha256=document.get("requested_manifest_sha256"),
        expected_workflow_source_identity=(
            None if current_manifest else source_workflow_identity
        ),
        allow_missing_workflow_source_identity=(
            legacy_source_mode and isinstance(legacy_source_binding, dict)
        ),
        allow_legacy_manifest=True,
        require_final_manifest=True,
    )
    manifest_sha256 = package_validation["manifest_sha256"]
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

    manifest: dict[str, Any] | None = None
    try:
        manifest_value = safe_relative(
            document.get("candidate_manifest_path"), "candidate_manifest_path"
        )
        manifest_path = (repo_root / manifest_value).resolve()
        parsed = yaml.safe_load(manifest_path.read_bytes())
        if isinstance(parsed, dict):
            manifest = parsed
    except (OSError, ValueError, yaml.YAMLError):
        pass

    if manifest is not None:
        if manifest.get("campaign_generation") != prior_generation:
            add_finding(
                findings,
                "CANDIDATE_GENERATION_MISMATCH",
                "candidate manifest generation does not match the closed source generation",
            )
        for field in (
            "candidate_interface",
            "source_base_identity",
            "source_result_identity",
            "dependency_identity",
            "runtime_factors",
            "generated_assets",
        ):
            if field not in manifest:
                add_finding(
                    findings,
                    "IDENTITY_INPUT_MISSING",
                    f"candidate manifest is missing {field}",
                )
        if legacy_manifest and legacy_source_mode:
            findings.extend(
                validate_legacy_candidate_source_binding(
                    repo_root,
                    legacy_source_binding,
                    candidate_manifest_path=document.get("candidate_manifest_path"),
                    candidate_manifest_sha256=manifest_sha256,
                    candidate_id=canonical_candidate_id,
                    candidate_members=members,
                    candidate_manifest=manifest,
                    prior_campaign_generation=prior_generation,
                )
            )
        elif legacy_manifest and "workflow_source_identity" not in manifest:
            add_finding(
                findings,
                "IDENTITY_INPUT_MISSING",
                "historical candidate manifest is missing workflow_source_identity",
            )

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
    if legacy_manifest:
        result["source_workflow_identity"] = source_workflow_identity
        result["legacy_candidate_source_binding"] = legacy_source_binding
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
