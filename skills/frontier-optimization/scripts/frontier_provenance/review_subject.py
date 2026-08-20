"""Validate the generated completeness index inside a project decision root."""

from __future__ import annotations

import json
from typing import Any

from .content import ProvenanceError
from .review_contract import (
    ENTRY_STAGES,
    ROLE_ADAPTER_CONTRACT,
    REVIEW_KINDS,
    validate_and_project,
)


SUBJECT_CONTRACT = "frontier-review-subject/1"
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
    if index["contract_version"] != SUBJECT_CONTRACT:
        raise ProvenanceError(f"review subject contract must be {SUBJECT_CONTRACT}")
    if index["role_adapter"] != ROLE_ADAPTER_CONTRACT:
        raise ProvenanceError(f"review subject role adapter must be {ROLE_ADAPTER_CONTRACT}")
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
    )
    if projection != derived:
        raise ProvenanceError("review subject semantic projection disagrees with its members")
    return index
