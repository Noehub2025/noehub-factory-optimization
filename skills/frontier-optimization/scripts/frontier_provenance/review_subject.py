"""Validate the generated completeness index inside a project decision root."""

from __future__ import annotations

import json
from typing import Any

from .content import ProvenanceError
from .review_contract import (
    ENTRY_STAGES,
    ROLE_ADAPTER_CONTRACT,
    ROLE_ADAPTER_CONTRACT_V1,
    ROLE_ADAPTER_CONTRACT_V2,
    REVIEW_KINDS,
    validate_and_project,
)


SUBJECT_CONTRACT_V1 = "frontier-review-subject/1"
SUBJECT_CONTRACT_V2 = "frontier-review-subject/2"
SUBJECT_CONTRACT = SUBJECT_CONTRACT_V2
SUBJECT_ADAPTER_PAIRS = {
    SUBJECT_CONTRACT_V1: ROLE_ADAPTER_CONTRACT_V1,
    SUBJECT_CONTRACT_V2: ROLE_ADAPTER_CONTRACT_V2,
}
INDEX_LOGICAL_NAME = "project/decision/review-subject-index.json"


def validate_review_subject(
    manifest: dict[str, Any], raw_by_name: dict[str, bytes]
) -> dict[str, Any] | None:
    """Return the complete subject projection, or None for a historical decision."""

    if manifest.get("domain") != "project-decision":
        return None
    raw = raw_by_name.get(INDEX_LOGICAL_NAME)
    if raw is None:
        return None
    try:
        index = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProvenanceError(f"review subject index is unreadable: {exc}") from exc
    required = {
        "contract_version",
        "role_adapter",
        "review_id",
        "review_kind",
        "subject_mode",
        "members",
        "closed_collections",
        "semantic_projection",
    }
    if not isinstance(index, dict) or set(index) != required:
        raise ProvenanceError("review subject index has unknown or missing fields")
    expected_adapter = SUBJECT_ADAPTER_PAIRS.get(index["contract_version"])
    if expected_adapter is None:
        raise ProvenanceError("review subject contract is unsupported")
    if index["role_adapter"] != expected_adapter:
        raise ProvenanceError("review subject and role adapter versions cannot be mixed")
    if index["review_kind"] not in REVIEW_KINDS:
        raise ProvenanceError("review subject kind is invalid")
    if index["subject_mode"] != "complete":
        raise ProvenanceError("review subject must be complete")
    if not isinstance(index["review_id"], str) or not index["review_id"].startswith("R"):
        raise ProvenanceError("review subject review_id is invalid")
    expected_members = sorted(
        item["logical_name"]
        for item in manifest["artifacts"]
        if item["logical_name"] != INDEX_LOGICAL_NAME
    )
    if index["members"] != expected_members or len(set(expected_members)) != len(expected_members):
        raise ProvenanceError("review subject index does not enumerate the complete manifest")
    expected_collections = sorted(
        (
            {
                "logical_name": item["logical_name"],
                "members": sorted(item["members"]),
            }
            for item in manifest["closed_collections"]
        ),
        key=lambda item: item["logical_name"],
    )
    if index["closed_collections"] != expected_collections:
        raise ProvenanceError("review subject index does not enumerate closed collections")
    projection = index["semantic_projection"]
    if not isinstance(projection, dict):
        raise ProvenanceError("review subject semantic projection is invalid")
    review_stage = projection.get("review_stage") if index["review_kind"] == "entry" else None
    if index["review_kind"] == "entry" and review_stage not in ENTRY_STAGES:
        raise ProvenanceError("review subject entry stage is invalid")
    derived = validate_and_project(
        index["review_kind"],
        {name: raw_by_name[name] for name in expected_members},
        review_stage=review_stage,
        closed_collections=manifest["closed_collections"],
        role_adapter=index["role_adapter"],
    )
    if projection != derived:
        raise ProvenanceError("review subject semantic projection disagrees with its members")
    return index
