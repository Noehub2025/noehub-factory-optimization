#!/usr/bin/env python3
"""Regression tests for Frontier batch result validation."""

from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


SCRIPT = Path(__file__).with_name("validate_batch_result.py")
SPEC = importlib.util.spec_from_file_location("validate_batch_result", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def base_packet() -> dict:
    return {
        "packet_path": "artifacts/frontier/B900/packet.yaml",
        "packet_id": "B900-packet-sha256:example",
        "batch_id": "B900",
        "campaign_generation": 2,
        "route_id": "T900",
        "parallel_set": None,
        "work_kind": "code",
        "problem_epoch": 3,
        "representation_revision": 4,
        "changes_executable_candidate": True,
        "result_validation_path": "artifacts/frontier/B900/result-validation.json",
        "result_packet_path": "artifacts/frontier/B900/result.yaml",
    }


def base_result() -> dict:
    return {
        "result_packet_path": "artifacts/frontier/B900/result.yaml",
        "packet_path": "artifacts/frontier/B900/packet.yaml",
        "packet_id": "B900-packet-sha256:example",
        "packet_preflight": "B900-packet-preflight-sha256:example",
        "acknowledgment": "B900-acknowledgment-sha256:example",
        "execution_start": "B900-execution-start-sha256:example",
        "batch_id": "B900",
        "campaign_generation": 2,
        "route_id": "T900",
        "parallel_set": None,
        "work_kind": "code",
        "problem_epoch": 3,
        "representation_revision": 4,
        "started_at": "2026-08-12T08:01:00Z",
        "ended_at": "2026-08-12T08:02:00Z",
        "outcome": "completed",
        "changes_executable_candidate": True,
        "planned_spend": "1 proposal attempt",
        "actual_spend": "1 proposal attempt",
        "accounting_evidence": "candidate identity changed",
        "artifacts": ["artifacts/frontier/B900/candidate-manifest.yaml"],
        "work_plan": None,
        "design_review": None,
        "development_authorization": "V900",
        "design_inputs_used": [],
        "source_base_identity": "source-sha256:example",
        "source_result_identity": "result-source-sha256:example",
        "changed_paths": ["candidates/B900/main.py"],
        "candidate_manifest": "artifacts/frontier/B900/candidate-manifest.yaml",
        "candidate_identity": "B900-candidate-sha256:example",
        "experiment_identity": None,
        "resolved_configuration_identity": None,
        "dependency_identity": "lock-sha256:example",
        "implementation_review_state": "pending",
        "materialization_state": "materialized-stopped",
        "performance_evaluation_state": "not-authorized",
        "integration_state": "not-authorized",
        "work_plan_progress": None,
        "design_change_proposals": [],
        "recovery_point": "recoverable execution baseline and candidate artifacts",
        "human_input_state": "not-applicable",
        "human_input_artifacts": [],
        "human_input_validation": [],
        "human_input_evidence_limit": "not applicable",
        "engineering_validation": [{"check": "unit", "result": "pass"}],
        "implementation_definition_of_done": "met",
        "results": [],
        "observed_vs_expected": "matched engineering expectations",
        "decision_relevant_surprises": [],
        "failed_checks": [],
        "new_prerequisites": ["fresh implementation review"],
        "possible_follow_up": None,
        "scope_deviation": "None",
    }


class BatchResultValidationTests(unittest.TestCase):
    def test_valid_materialization_draft_and_frozen_outputs_are_identical(self) -> None:
        packet = base_packet()
        draft = base_result()
        draft_validation = MODULE.validate(draft, "draft", packet)
        self.assertTrue(draft_validation["result_structure_ready"], draft_validation["findings"])
        frozen = copy.deepcopy(draft)
        frozen["result_packet_id"] = draft_validation["computed_result_packet_id"]
        frozen_validation = MODULE.validate(frozen, "frozen", packet)
        self.assertEqual(draft_validation, frozen_validation)

    def test_materialization_rejects_nonempty_results(self) -> None:
        result = base_result()
        result["results"] = [{"candidate": result["candidate_identity"], "measurement": None}]
        validation = MODULE.validate(result, "draft", base_packet())
        self.assertIn(
            "MATERIALIZATION_RESULTS_NOT_EMPTY",
            {finding["code"] for finding in validation["findings"]},
        )

    def test_materialization_rejects_performance_or_integration_authority(self) -> None:
        result = base_result()
        result["performance_evaluation_state"] = "not-performed"
        result["integration_state"] = "not-performed"
        validation = MODULE.validate(result, "draft", base_packet())
        codes = {finding["code"] for finding in validation["findings"]}
        self.assertIn("MATERIALIZATION_BOUNDARY_INVALID", codes)

    def test_slot_h_evaluation_allows_measurement_results(self) -> None:
        packet = base_packet()
        packet.update(
            {
                "work_kind": "experiment",
                "changes_executable_candidate": False,
            }
        )
        result = base_result()
        result.update(
            {
                "work_kind": "experiment",
                "changes_executable_candidate": False,
                "changed_paths": ["artifacts/frontier/B900/raw-results.json"],
                "source_result_identity": None,
                "experiment_identity": {"id": "experiment-sha256:example"},
                "implementation_review_state": "reusable with R900 IMPLEMENTATION_READY",
                "materialization_state": "not-applicable",
                "performance_evaluation_state": "performed under R900 and B900 authority",
                "integration_state": "not-performed",
                "results": [{"candidate": "B900-candidate-sha256:example", "score": 0.5}],
            }
        )
        validation = MODULE.validate(result, "draft", packet)
        self.assertTrue(validation["result_structure_ready"], validation["findings"])

    def test_result_binding_must_match_packet(self) -> None:
        result = base_result()
        result["campaign_generation"] = 3
        validation = MODULE.validate(result, "draft", base_packet())
        self.assertIn(
            "PACKET_BINDING_MISMATCH",
            {finding["code"] for finding in validation["findings"]},
        )

    def test_cli_writes_validation_before_final_result_path_exists(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet_path = root / "packet.yaml"
            draft_path = root / "result-draft.yaml"
            validation_path = root / "artifacts/frontier/B900/result-validation.json"
            packet_path.write_text(yaml.safe_dump(base_packet(), sort_keys=False))
            draft_path.write_text(yaml.safe_dump(base_result(), sort_keys=False))
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    str(draft_path),
                    "--packet",
                    str(packet_path),
                    "--phase",
                    "draft",
                    "--output",
                    str(validation_path),
                    "--repo-root",
                    str(root),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            validation = json.loads(validation_path.read_text())
            self.assertTrue(validation["result_structure_ready"])
            self.assertFalse((root / "artifacts/frontier/B900/result.yaml").exists())

    def test_legacy_audit_diagnoses_materialization_without_rewriting_it(self) -> None:
        result = base_result()
        result["implementation_review_state"] = "reusable historical review"
        result["results"] = [{"candidate": result["candidate_identity"], "score": None}]
        original = copy.deepcopy(result)

        validation = MODULE.validate(result, "audit", base_packet())
        codes = {finding["code"] for finding in validation["findings"]}
        self.assertIn("IMPLEMENTATION_REVIEW_STATE_INVALID", codes)
        self.assertIn("MATERIALIZATION_RESULTS_NOT_EMPTY", codes)
        self.assertEqual(result, original)

    def test_cli_refuses_to_validate_draft_at_authoritative_result_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet_path = root / "packet.yaml"
            result_path = root / "artifacts/frontier/B900/result.yaml"
            validation_path = root / "artifacts/frontier/B900/result-validation.json"
            result_path.parent.mkdir(parents=True)
            packet_path.write_text(yaml.safe_dump(base_packet(), sort_keys=False))
            result_path.write_text(yaml.safe_dump(base_result(), sort_keys=False))
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    str(result_path),
                    "--packet",
                    str(packet_path),
                    "--phase",
                    "draft",
                    "--output",
                    str(validation_path),
                    "--repo-root",
                    str(root),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 2)
            self.assertIn("before the authoritative result path exists", completed.stderr)


if __name__ == "__main__":
    unittest.main()
