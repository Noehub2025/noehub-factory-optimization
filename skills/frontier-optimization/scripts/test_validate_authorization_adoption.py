#!/usr/bin/env python3
"""Regression tests for source-derived authorization adoption validation."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

from test_validate_entry_packet import make_workspace


SCRIPT = Path(__file__).with_name("validate_authorization_adoption.py")
SPEC = importlib.util.spec_from_file_location("validate_authorization_adoption", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def make_record(root: Path) -> dict:
    entry = make_workspace(root, frozen=True)
    entry_path = root / entry["packet_path"]
    entry_path.parent.mkdir(parents=True, exist_ok=True)
    entry_raw = yaml.safe_dump(entry, sort_keys=False).encode()
    entry_path.write_bytes(entry_raw)

    review_relative = "frontier/reviews/entry-R900.md"
    review_raw = (
        "---\n"
        "type: Optimization Frontier Entry Review\n"
        "status: complete\n"
        "review_id: R900\n"
        "review_result: AUTHORIZATION_READY\n"
        f"packet_id: {entry['packet_id']}\n"
        f"snapshot_id: {entry['snapshot_id']}\n"
        "---\n\n"
        "# FRONTIER ENTRY REVIEW\n"
    ).encode()
    review_path = root / review_relative
    review_path.parent.mkdir(parents=True, exist_ok=True)
    review_path.write_bytes(review_raw)

    target = entry["authorization_target"]
    record = {
        "adoption_path": "frontier/reviews/entry-R900-adoption.yaml",
        "entry_packet": {
            "path": entry["packet_path"],
            "packet_id": entry["packet_id"],
            "file_sha256": hashlib.sha256(entry_raw).hexdigest(),
        },
        "readiness_review": {
            "review_id": "R900",
            "review_result": "AUTHORIZATION_READY",
            "review_artifact": review_relative,
            "review_artifact_identity": f"sha256:{hashlib.sha256(review_raw).hexdigest()}",
            "snapshot_id": entry["snapshot_id"],
            "entry_packet_id": entry["packet_id"],
        },
        "authorization_target": {
            "path": target["target_path"],
            "target_id": target["target_id"],
            "file_sha256": target["target_file_sha256"],
            "batch_id": target["batch_id"],
            "packet_id": target["packet_id"],
        },
        "user_result": {
            "path": target["user_result_path"],
            "identity": "pending",
            "identity_field": "result_id",
            "file_sha256": "pending",
            "target_id": target["target_id"],
            "answer": "authorize",
        },
        "adopted_v": None,
        "answer_fidelity": "exact authorize",
        "reviewed_state_transition": target["proposed_state_transition"],
        "entry_result": "ENTRY_READY",
        "maximum_consequence": "dispatch B900 within reviewed budget",
    }
    write_user_result(root, record, "authorize")
    return record


def write_user_result(
    root: Path,
    record: dict,
    answer: str,
    conditions: list[str] | None = None,
) -> None:
    payload = {
        "target_id": record["authorization_target"]["target_id"],
        "answer": answer,
        "conditions": conditions if conditions is not None else [],
    }
    payload_raw = yaml.safe_dump(payload, sort_keys=False).encode()
    result_id = "V900-result-sha256:" + hashlib.sha256(payload_raw).hexdigest()
    raw = f"result_id: {result_id}\n".encode() + payload_raw
    path = root / record["user_result"]["path"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    record["user_result"].update(
        {
            "identity": result_id,
            "file_sha256": hashlib.sha256(raw).hexdigest(),
            "answer": answer,
        }
    )
    record["adopted_v"] = (
        {
            "decision_id": "V900",
            "record_path": "docs/skills/optimization/example/frontier/ledger.md",
            "result_path": record["user_result"]["path"],
            "result_identity": result_id,
            "target_id": record["authorization_target"]["target_id"],
        }
        if answer == "authorize"
        else None
    )


class AuthorizationAdoptionTests(unittest.TestCase):
    def test_adoption_identity_serialization_error_is_repair_not_hard_block(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            record = make_record(root)
            record["adoption_id"] = "authorization-adoption-sha256:stale"

            result = MODULE.validate(record, "frozen", root)

            mismatch = [
                finding
                for finding in result["repair_findings"]
                if finding["code"] == "ADOPTION_ID_MISMATCH"
            ]
            self.assertEqual(1, len(mismatch))
            self.assertEqual([], result["blocking_findings"])

    def test_exact_authorization_requires_source_derived_adopted_v(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            record = make_record(root)
            record["adopted_v"] = None

            result = MODULE.validate(record, "draft", root)

            self.assertIn(
                "ADOPTED_V_INVALID",
                {item["code"] for item in result["findings"]},
            )
            self.assertFalse(result["authorization_adoption_valid"])

    def test_adopted_v_cannot_copy_a_different_answer_identity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            record = make_record(root)
            record["adopted_v"]["result_identity"] = "V899-result-sha256:stale"

            result = MODULE.validate(record, "draft", root)

            self.assertIn(
                "ADOPTED_V_NOT_DERIVED",
                {item["code"] for item in result["findings"]},
            )
            self.assertFalse(result["authorization_adoption_valid"])

    def test_exact_authorization_passes_draft_and_frozen(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            draft = make_record(root)
            draft_result = MODULE.validate(draft, "draft", root)
            self.assertTrue(draft_result["authorization_adoption_valid"], draft_result["findings"])
            self.assertGreaterEqual(len(draft_result["derived_binding_checks"]), 4)
            frozen = copy.deepcopy(draft)
            frozen["adoption_id"] = draft_result["computed_adoption_id"]
            result = MODULE.validate(frozen, "frozen", root)
            self.assertTrue(result["authorization_adoption_valid"], result["findings"])

    def test_frozen_adoption_reproduces_from_snapshot_after_exact_reviewed_transition(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            record = make_record(root)
            draft_result = MODULE.validate(record, "draft", root)
            record["adoption_id"] = draft_result["computed_adoption_id"]
            before = MODULE.validate(record, "frozen", root)
            self.assertTrue(before["authorization_adoption_valid"], before["findings"])

            target = yaml.safe_load(
                (root / record["authorization_target"]["path"]).read_text()
            )
            for item in target["post_adoption_state"]["files"]:
                (root / item["path"]).write_bytes(
                    (root / item["post_source"]["path"]).read_bytes()
                )

            live_result = MODULE.validate(record, "frozen", root)
            self.assertFalse(live_result["authorization_adoption_valid"])
            self.assertIn(
                "ENTRY_SOURCE_RECONCILIATION_FAILED",
                {item["code"] for item in live_result["findings"]},
            )
            snapshot_result = MODULE.validate(
                record,
                "frozen",
                root,
                reconcile_entry_live=False,
            )
            self.assertEqual(snapshot_result, before)

    def test_self_declared_matches_cannot_mask_stale_entry_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            record = make_record(root)
            record["binding_checks"] = [
                {
                    "name": "launcher",
                    "reviewed_identity": "claimed-same",
                    "observed_identity": "claimed-same",
                    "status": "matched",
                }
            ]
            (root / "artifacts/frontier/B900-launcher-preflight.json").write_text("{}")
            result = MODULE.validate(record, "draft", root)
            codes = {item["code"] for item in result["findings"]}
            self.assertIn("ENTRY_SOURCE_RECONCILIATION_FAILED", codes)
            self.assertIn("STALE_ADOPTION_CREATED_AUTHORITY", codes)
            self.assertFalse(result["authorization_adoption_valid"])

    def test_adoption_target_must_come_from_frozen_entry_packet(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            record = make_record(root)
            record["authorization_target"]["packet_id"] = "B899-packet-sha256:stale"
            result = MODULE.validate(record, "draft", root)
            self.assertIn(
                "AUTHORIZATION_TARGET_NOT_DERIVED",
                {item["code"] for item in result["findings"]},
            )

    def test_authorized_transition_must_come_from_frozen_entry_target(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            record = make_record(root)
            record["reviewed_state_transition"] = {"budget": "grant unreviewed spend"}
            result = MODULE.validate(record, "draft", root)
            self.assertIn(
                "STATE_TRANSITION_NOT_DERIVED",
                {item["code"] for item in result["findings"]},
            )

    def test_authorized_consequence_must_come_from_frozen_target(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            record = make_record(root)
            record["maximum_consequence"] = "dispatch a different batch"
            result = MODULE.validate(record, "draft", root)
            self.assertIn(
                "MAXIMUM_CONSEQUENCE_NOT_DERIVED",
                {item["code"] for item in result["findings"]},
            )

    def test_decline_creates_no_authority(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            record = make_record(root)
            write_user_result(root, record, "decline")
            record["answer_fidelity"] = "decline"
            record["reviewed_state_transition"] = None
            record["entry_result"] = "DECLINED"
            record["maximum_consequence"] = "none"
            result = MODULE.validate(record, "draft", root)
            self.assertTrue(result["authorization_adoption_valid"], result["findings"])

    def test_conditional_answer_requires_new_review(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            record = make_record(root)
            write_user_result(root, record, "conditional", ["reduce the spend boundary"])
            record["answer_fidelity"] = "conditional change"
            record["reviewed_state_transition"] = None
            record["entry_result"] = "REVIEW_REQUIRED"
            record["maximum_consequence"] = "none"
            result = MODULE.validate(record, "draft", root)
            self.assertTrue(result["authorization_adoption_valid"], result["findings"])

    def test_exact_authorize_rejects_an_embedded_condition(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            record = make_record(root)
            result_path = root / record["user_result"]["path"]
            payload = yaml.safe_load(result_path.read_text())
            payload.pop("result_id")
            payload["condition"] = "also widen the reviewed scope"
            payload_raw = yaml.safe_dump(payload, sort_keys=False).encode()
            result_id = "V900-result-sha256:" + hashlib.sha256(payload_raw).hexdigest()
            raw = f"result_id: {result_id}\n".encode() + payload_raw
            result_path.write_bytes(raw)
            record["user_result"].update(
                {
                    "identity": result_id,
                    "file_sha256": hashlib.sha256(raw).hexdigest(),
                }
            )
            record["adopted_v"]["result_identity"] = result_id

            result = MODULE.validate(record, "draft", root)

            self.assertIn(
                "USER_RESULT_SCHEMA_INVALID",
                {item["code"] for item in result["findings"]},
            )
            self.assertFalse(result["authorization_adoption_valid"])

    def test_nonready_review_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            record = make_record(root)
            record["readiness_review"]["review_result"] = "ENTRY_REPAIR_REQUIRED"
            result = MODULE.validate(record, "draft", root)
            self.assertIn("READINESS_REVIEW_NOT_READY", {item["code"] for item in result["findings"]})

    def test_review_artifact_must_bind_entry_packet_and_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            record = make_record(root)
            review_path = root / record["readiness_review"]["review_artifact"]
            review_raw = review_path.read_bytes().replace(
                record["readiness_review"]["snapshot_id"].encode(),
                b"R899-snapshot-sha256:stale",
            )
            review_path.write_bytes(review_raw)
            record["readiness_review"]["review_artifact_identity"] = (
                f"sha256:{hashlib.sha256(review_raw).hexdigest()}"
            )
            result = MODULE.validate(record, "draft", root)
            self.assertIn(
                "REVIEW_ARTIFACT_BINDING_MISMATCH",
                {item["code"] for item in result["findings"]},
            )


if __name__ == "__main__":
    unittest.main()
