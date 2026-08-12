#!/usr/bin/env python3
"""Regression tests for Frontier authorization adoption validation."""

from __future__ import annotations

import copy
import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("validate_authorization_adoption.py")
SPEC = importlib.util.spec_from_file_location("validate_authorization_adoption", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def base_record() -> dict:
    return {
        "adoption_path": "frontier/reviews/entry-R900-adoption.yaml",
        "entry_packet_id": "entry-R900-packet-sha256:example",
        "readiness_review": {
            "review_id": "R900",
            "review_result": "AUTHORIZATION_READY",
            "review_artifact": "frontier/reviews/entry-R900.md",
            "review_artifact_identity": "sha256:review",
            "snapshot_id": "entry-R900-snapshot-sha256:example",
            "entry_packet_id": "entry-R900-packet-sha256:example",
        },
        "authorization_target": {"target_id": "authorization-target-sha256:example"},
        "user_result": {
            "path": "artifacts/frontier/V900-result.yaml",
            "identity": "sha256:user-result",
            "target_id": "authorization-target-sha256:example",
            "answer": "authorize",
        },
        "binding_checks": [
            {
                "name": "batch packet",
                "reviewed_identity": "B900-packet-sha256:example",
                "observed_identity": "B900-packet-sha256:example",
                "status": "matched",
            },
            {
                "name": "design contract",
                "reviewed_identity": "W900-r1-sha256:example",
                "observed_identity": "W900-r1-sha256:example",
                "status": "matched",
            },
        ],
        "answer_fidelity": "exact authorize",
        "reviewed_state_transition": "reserve B900 and adopt it as Primary",
        "entry_result": "ENTRY_READY",
        "maximum_consequence": "dispatch B900 within reviewed budget",
    }


class AuthorizationAdoptionTests(unittest.TestCase):
    def test_exact_authorization_passes_draft_and_frozen(self) -> None:
        draft = base_record()
        draft_result = MODULE.validate(draft, "draft")
        self.assertTrue(draft_result["authorization_adoption_valid"], draft_result["findings"])
        frozen = copy.deepcopy(draft)
        frozen["adoption_id"] = draft_result["computed_adoption_id"]
        result = MODULE.validate(frozen, "frozen")
        self.assertTrue(result["authorization_adoption_valid"], result["findings"])

    def test_stale_binding_cannot_produce_entry_ready(self) -> None:
        record = base_record()
        record["binding_checks"][0]["observed_identity"] = "B900-packet-sha256:changed"
        record["binding_checks"][0]["status"] = "mismatch"
        result = MODULE.validate(record, "draft")
        self.assertIn(
            "STALE_ADOPTION_CREATED_AUTHORITY",
            {item["code"] for item in result["findings"]},
        )

    def test_stale_binding_can_return_review_required_without_authority(self) -> None:
        record = base_record()
        record["binding_checks"][0]["observed_identity"] = "B900-packet-sha256:changed"
        record["binding_checks"][0]["status"] = "mismatch"
        record["reviewed_state_transition"] = None
        record["entry_result"] = "REVIEW_REQUIRED"
        record["maximum_consequence"] = "none"
        result = MODULE.validate(record, "draft")
        self.assertTrue(result["authorization_adoption_valid"], result["findings"])

    def test_decline_creates_no_authority(self) -> None:
        record = base_record()
        record["user_result"]["answer"] = "decline"
        record["answer_fidelity"] = "decline"
        record["reviewed_state_transition"] = None
        record["entry_result"] = "DECLINED"
        record["maximum_consequence"] = "none"
        result = MODULE.validate(record, "draft")
        self.assertTrue(result["authorization_adoption_valid"], result["findings"])

    def test_conditional_answer_requires_new_review(self) -> None:
        record = base_record()
        record["user_result"]["answer"] = "conditional"
        record["answer_fidelity"] = "conditional change"
        record["reviewed_state_transition"] = None
        record["entry_result"] = "REVIEW_REQUIRED"
        record["maximum_consequence"] = "none"
        result = MODULE.validate(record, "draft")
        self.assertTrue(result["authorization_adoption_valid"], result["findings"])

    def test_nonready_review_is_rejected(self) -> None:
        record = base_record()
        record["readiness_review"]["review_result"] = "ENTRY_REPAIR_REQUIRED"
        result = MODULE.validate(record, "draft")
        self.assertIn(
            "READINESS_REVIEW_NOT_READY",
            {item["code"] for item in result["findings"]},
        )


if __name__ == "__main__":
    unittest.main()
