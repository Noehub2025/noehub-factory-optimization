#!/usr/bin/env python3
"""Regression tests for Frontier Entry packet schema validation."""

from __future__ import annotations

import copy
import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("validate_entry_packet.py")
SPEC = importlib.util.spec_from_file_location("validate_entry_packet", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def base_packet(generation: int = 1) -> dict:
    lineage = None
    if generation > 1:
        lineage = {
            "prior_closeout": "X001 and CLOSEOUT_COMPLETE",
            "candidate_recovery_preflight": None,
            "recovery_authorization": "V001",
            "disposition": "X002",
            "inherited_budget": "Budget identity",
            "reused_identities": ["candidate identity"],
            "implementation_review": "R001",
        }
    return {
        "review_kind": "entry",
        "review_stage": "authorization-readiness",
        "review_id": "R900",
        "packet_path": "frontier/reviews/entry-R900-packet.yaml",
        "entry_schema_preflight_paths": {
            "draft": "frontier/reviews/entry-R900-draft-schema.json",
            "frozen": "frontier/reviews/entry-R900-frozen-schema.json",
        },
        "snapshot_root": "frontier/reviews/entry-R900-snapshot/",
        "snapshot_manifest": "frontier/reviews/entry-R900-snapshot/manifest.yaml",
        "snapshot_id": "entry-R900-sha256:example",
        "task_path": "docs/skills/optimization/example",
        "problem_epoch": 1,
        "problem_generated_at": "2026-01-01T00:00:00Z",
        "representation_revision": 1,
        "representation_generated_at": "2026-01-01T00:00:00Z",
        "representation_review_result": "PROCEED_EXPLORATORY",
        "representation_permitted": "bounded scope",
        "campaign_generation": generation,
        "recovery_lineage": lineage,
        "repository_structure_disposition": "existing-integrated",
        "repository_layout_approval": None,
        "design_gate": "R899 DESIGN_READY",
        "dispatch_contract": "exact packet and preflight",
        "authorization_target": {
            "target_id": "V900",
            "batch_id": "B900",
            "packet_path": "artifacts/frontier/B900/packet.yaml",
            "packet_id": "B900-packet-sha256:example",
            "preflight_id": "B900-packet-preflight-sha256:example",
            "design_contract_identity": "W900-r1-sha256:example",
            "source_base_identity": "source-sha256:example",
            "scope": "one bounded implementation",
            "maximum_spend": "one proposal attempt",
            "stop_boundary": "materialized-stopped",
            "result_path": "artifacts/frontier/V900-result.yaml",
            "proposed_state_transition": {
                "budget": "reserve one proposal attempt for B900",
                "selection": "adopt B900 as Primary",
                "lifecycle": "FIRST_BATCH_PLANNED after adoption",
            },
        },
        "authorization_state": "pending",
        "authorization_adoption_path": "frontier/reviews/entry-R900-adoption.yaml",
        "authorization_adoption_preflight_path": "frontier/reviews/entry-R900-adoption-preflight.json",
        "selected_batches": ["B900"],
        "actual_spend": "zero",
        "snapshot_inputs": "frontier/reviews/entry-R900-snapshot/manifest.yaml#inputs",
        "assigned_review_path": "frontier/reviews/entry-R900.md",
        "completion_check": "review every readiness requirement",
    }


class EntryPacketSchemaTests(unittest.TestCase):
    def test_generation_one_draft_and_frozen_pass(self) -> None:
        draft = base_packet()
        for field in ("snapshot_root", "snapshot_manifest", "snapshot_id", "snapshot_inputs"):
            draft.pop(field)
        draft_result = MODULE.validate(draft, "draft")
        self.assertTrue(draft_result["entry_schema_ready"], draft_result["findings"])

        frozen = base_packet()
        expected = MODULE.validate(frozen, "frozen")["computed_packet_id"]
        frozen["packet_id"] = expected
        result = MODULE.validate(frozen, "frozen")
        self.assertTrue(result["entry_schema_ready"], result["findings"])

    def test_generation_two_requires_recovery_lineage(self) -> None:
        packet = base_packet(2)
        packet.pop("recovery_lineage")
        result = MODULE.validate(packet, "draft")
        codes = {item["code"] for item in result["findings"]}
        self.assertIn("REQUIRED_FIELD_MISSING", codes)
        self.assertIn("RECOVERY_LINEAGE_REQUIRED", codes)

    def test_generation_two_requires_structured_lineage_fields(self) -> None:
        packet = base_packet(2)
        packet["recovery_lineage"].pop("inherited_budget")
        result = MODULE.validate(packet, "draft")
        self.assertIn(
            "RECOVERY_LINEAGE_FIELD_MISSING",
            {item["code"] for item in result["findings"]},
        )

    def test_authorization_must_still_be_pending(self) -> None:
        packet = base_packet()
        packet["authorization_state"] = "authorized"
        result = MODULE.validate(packet, "draft")
        self.assertIn(
            "AUTHORIZATION_STATE_INVALID",
            {item["code"] for item in result["findings"]},
        )

    def test_legacy_audit_rejects_generation_without_recovery_lineage(self) -> None:
        packet = base_packet(2)
        packet.pop("recovery_lineage")
        result = MODULE.validate(packet, "audit")
        self.assertIn(
            "RECOVERY_LINEAGE_REQUIRED",
            {item["code"] for item in result["findings"]},
        )


if __name__ == "__main__":
    unittest.main()
