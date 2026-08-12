#!/usr/bin/env python3
"""Regression tests for the Frontier batch packet preflight."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


SCRIPT = Path(__file__).with_name("validate_batch_packet.py")
SPEC = importlib.util.spec_from_file_location("validate_batch_packet", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def base_packet() -> dict:
    return {
        "packet_path": "artifacts/frontier/B900/packet.yaml",
        "packet_preflight_path": "artifacts/frontier/B900/packet-preflight.json",
        "batch_id": "B900",
        "changes_executable_candidate": True,
        "design_profile": "direct",
        "allowed_code_paths": ["candidates/B900/main.py"],
        "worker_forbidden_paths": [
            "artifacts/frontier/B900/packet.yaml",
            "artifacts/frontier/B900/packet-preflight.json",
            "artifacts/frontier/B900/execution-start.yaml",
            "docs/",
        ],
        "execution_frozen_inputs": [
            {"path": "src/", "scope": "subtree", "identity": "sha256:example"},
        ],
        "coordinator_lifecycle_transition": None,
        "execution_baseline_root": "artifacts/frontier/B900/execution-baseline/",
        "execution_start_path": "artifacts/frontier/B900/execution-start.yaml",
        "candidate_manifest_path": "artifacts/frontier/B900/candidate-manifest.yaml",
        "artifact_paths": [
            "candidates/B900/",
            "artifacts/frontier/B900/result.yaml",
            "artifacts/frontier/B900/candidate-manifest.yaml",
        ],
        "acknowledgment_path": "artifacts/frontier/B900/acknowledgment.yaml",
        "result_validation_path": "artifacts/frontier/B900/result-validation.json",
        "result_packet_path": "artifacts/frontier/B900/result.yaml",
        "prohibited_actions": ["edit packet, execution-start, parents, evaluator, or tests"],
    }


class PacketPreflightTests(unittest.TestCase):
    def test_cli_reproduces_identical_draft_and_frozen_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet_path = root / "packet.yaml"
            draft_output = root / "draft.json"
            frozen_output = root / "frozen.json"
            packet = base_packet()
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False))

            draft = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    str(packet_path),
                    "--phase",
                    "draft",
                    "--output",
                    str(draft_output),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(draft.returncode, 0, draft.stderr)

            packet["packet_id"] = json.loads(draft_output.read_text())["computed_packet_id"]
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False))
            frozen = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    str(packet_path),
                    "--phase",
                    "frozen",
                    "--output",
                    str(frozen_output),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(frozen.returncode, 0, frozen.stderr)
            self.assertEqual(draft_output.read_bytes(), frozen_output.read_bytes())

    def test_valid_draft_and_frozen_packet_share_preflight_identity(self) -> None:
        draft = base_packet()
        draft_result = MODULE.validate(draft, "draft")
        self.assertTrue(draft_result["packet_structure_ready"])
        frozen = copy.deepcopy(draft)
        frozen["packet_id"] = draft_result["computed_packet_id"]
        frozen_result = MODULE.validate(frozen, "frozen")
        self.assertTrue(frozen_result["packet_structure_ready"])
        self.assertEqual(draft_result, frozen_result)

    def test_forbidden_subtree_catches_worker_output(self) -> None:
        packet = base_packet()
        packet["worker_forbidden_paths"].append("candidates/")
        result = MODULE.validate(packet, "draft")
        self.assertIn("WORKER_FORBIDDEN_OVERLAP", {item["code"] for item in result["findings"]})

    def test_execution_start_cannot_be_worker_artifact(self) -> None:
        packet = base_packet()
        packet["artifact_paths"].append(packet["execution_start_path"])
        result = MODULE.validate(packet, "draft")
        self.assertIn("EXECUTION_START_WORKER_OVERLAP", {item["code"] for item in result["findings"]})

    def test_execution_baseline_root_cannot_contain_worker_output(self) -> None:
        packet = base_packet()
        packet["result_validation_path"] = (
            "artifacts/frontier/B900/execution-baseline/result-validation.json"
        )
        result = MODULE.validate(packet, "draft")
        self.assertIn(
            "EXECUTION_BASELINE_WORKER_OVERLAP",
            {item["code"] for item in result["findings"]},
        )

    def test_new_packet_requires_execution_baseline_and_result_validation_paths(self) -> None:
        packet = base_packet()
        packet.pop("execution_baseline_root")
        packet.pop("result_validation_path")
        result = MODULE.validate(packet, "draft")
        self.assertIn("INVALID_PATH_SCHEMA", {item["code"] for item in result["findings"]})

    def test_coordinator_outputs_must_be_exclusive(self) -> None:
        packet = base_packet()
        packet["packet_preflight_path"] = packet["execution_start_path"]
        result = MODULE.validate(packet, "draft")
        self.assertIn("COORDINATOR_PATH_OVERLAP", {item["code"] for item in result["findings"]})

    def test_worker_output_roles_must_be_exclusive(self) -> None:
        packet = base_packet()
        packet["result_packet_path"] = packet["acknowledgment_path"]
        result = MODULE.validate(packet, "draft")
        self.assertIn("WORKER_OUTPUT_ROLE_OVERLAP", {item["code"] for item in result["findings"]})

    def test_frozen_directory_cannot_contain_outputs(self) -> None:
        packet = base_packet()
        packet["execution_frozen_inputs"].append(
            {"path": "artifacts/frontier/B900/", "scope": "subtree", "identity": "sha256:example"}
        )
        result = MODULE.validate(packet, "draft")
        codes = {item["code"] for item in result["findings"]}
        self.assertIn("FROZEN_WORKER_OVERLAP", codes)
        self.assertIn("FROZEN_COORDINATOR_OVERLAP", codes)

    def test_worker_forbidden_lifecycle_path_is_not_globally_frozen(self) -> None:
        packet = base_packet()
        packet["coordinator_lifecycle_transition"] = {
            "path": "docs/skills/optimization/example/FRONTIER.md",
            "allowed_field_diff": "campaign_status: planned -> running",
        }
        result = MODULE.validate(packet, "draft")
        self.assertTrue(result["packet_structure_ready"])

    def test_frozen_lifecycle_directory_is_rejected(self) -> None:
        packet = base_packet()
        packet["coordinator_lifecycle_transition"] = {
            "path": "docs/skills/optimization/example/FRONTIER.md",
            "allowed_field_diff": "campaign_status: planned -> running",
        }
        packet["execution_frozen_inputs"].append(
            {"path": "docs/", "scope": "subtree", "identity": "sha256:example"}
        )
        result = MODULE.validate(packet, "draft")
        self.assertIn("FROZEN_COORDINATOR_OVERLAP", {item["code"] for item in result["findings"]})

    def test_prohibition_cannot_deny_acknowledgment(self) -> None:
        packet = base_packet()
        packet["prohibited_actions"].append("do not write the acknowledgment")
        result = MODULE.validate(packet, "draft")
        self.assertIn("PROHIBITS_REQUIRED_WORKER_OUTPUT", {item["code"] for item in result["findings"]})

    def test_packet_mutation_invalidates_frozen_identity(self) -> None:
        packet = base_packet()
        draft_result = MODULE.validate(packet, "draft")
        packet["packet_id"] = draft_result["computed_packet_id"]
        packet["work"] = "a payload change after draft preflight"
        result = MODULE.validate(packet, "frozen")
        self.assertIn("PACKET_ID_MISMATCH", {item["code"] for item in result["findings"]})

    def test_new_packet_requires_machine_addressable_frozen_inputs(self) -> None:
        packet = base_packet()
        packet["execution_frozen_inputs"] = ["current project and workflow contracts"]
        result = MODULE.validate(packet, "draft")
        self.assertIn("INVALID_PATH_SCHEMA", {item["code"] for item in result["findings"]})

    def test_legacy_audit_rejects_path_and_output_conflicts(self) -> None:
        valid = base_packet()
        invalid = copy.deepcopy(valid)
        invalid["worker_forbidden_paths"].append(invalid["acknowledgment_path"])
        invalid["artifact_paths"].append(invalid["execution_start_path"])
        invalid["prohibited_actions"].append("do not write the acknowledgment")

        invalid_result = MODULE.validate(invalid, "audit")
        valid_result = MODULE.validate(valid, "audit")
        codes = {item["code"] for item in invalid_result["findings"]}
        self.assertFalse(invalid_result["packet_structure_ready"])
        self.assertIn("WORKER_FORBIDDEN_OVERLAP", codes)
        self.assertIn("EXECUTION_START_WORKER_OVERLAP", codes)
        self.assertIn("PROHIBITS_REQUIRED_WORKER_OUTPUT", codes)
        self.assertTrue(valid_result["packet_structure_ready"])

    def test_module_traceability_requires_every_evidence_destination(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            traceability_path = root / "work/W900/design/traceability.yaml"
            traceability_path.parent.mkdir(parents=True)
            (traceability_path.parents[1] / "WORK.md").write_text(
                "---\nplan_revision: 1\ndesign_contract_identity: W900-r1-sha256:example\n---\n"
            )
            traceability = {
                "work_id": "W900",
                "plan_revision": 1,
                "design_contract_identity": "W900-r1-sha256:example",
                "batches": {
                    "B900": {
                        "delivery_identity": "W900-delivery-B900-sha256:example",
                        "required_design_inputs": ["work/W900/design/verification.md#checks@sha256:example"],
                        "evidence_destinations": [
                            "artifacts/frontier/B900/weed-tests.json",
                            "artifacts/frontier/B900/plant-shape-tests.json",
                        ]
                    }
                },
            }
            traceability_path.write_text(yaml.safe_dump(traceability, sort_keys=False))
            packet = base_packet()
            packet.update(
                {
                    "design_profile": "module",
                    "work_plan": "work/W900/WORK.md",
                    "work_plan_revision": 1,
                    "design_contract_identity": "W900-r1-sha256:example",
                    "required_design_inputs": ["work/W900/design/verification.md#checks@sha256:example"],
                    "design_traceability": {
                        "path": "work/W900/design/traceability.yaml",
                        "sha256": hashlib.sha256(traceability_path.read_bytes()).hexdigest(),
                    },
                    "execution_frozen_inputs": [
                        {"path": "src/", "scope": "subtree", "identity": "sha256:example"},
                        {
                            "path": "work/W900/design/traceability.yaml",
                            "scope": "file",
                            "identity": hashlib.sha256(traceability_path.read_bytes()).hexdigest(),
                        },
                    ],
                    "artifact_paths": [
                        "artifacts/frontier/B900/weed-tests.json",
                        "artifacts/frontier/B900/result.yaml",
                        "artifacts/frontier/B900/candidate-manifest.yaml",
                    ],
                }
            )
            result = MODULE.validate(packet, "draft", root)
            self.assertIn(
                "W_EVIDENCE_DESTINATION_UNASSIGNED",
                {item["code"] for item in result["findings"]},
            )

    def test_module_traceability_passes_when_destinations_are_assigned(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            traceability_path = root / "work/W900/design/traceability.yaml"
            traceability_path.parent.mkdir(parents=True)
            (traceability_path.parents[1] / "WORK.md").write_text(
                "---\nplan_revision: 1\ndesign_contract_identity: W900-r1-sha256:example\n---\n"
            )
            traceability = {
                "work_id": "W900",
                "plan_revision": 1,
                "design_contract_identity": "W900-r1-sha256:example",
                "batches": {
                    "B900": {
                        "delivery_identity": "W900-delivery-B900-sha256:example",
                        "required_design_inputs": ["work/W900/design/verification.md#checks@sha256:example"],
                        "evidence_destinations": [
                            "artifacts/frontier/B900/weed-tests.json",
                            "artifacts/frontier/B900/plant-shape-tests.json",
                        ]
                    }
                },
            }
            traceability_path.write_text(yaml.safe_dump(traceability, sort_keys=False))
            packet = base_packet()
            packet.update(
                {
                    "design_profile": "module",
                    "work_plan": "work/W900/WORK.md",
                    "work_plan_revision": 1,
                    "design_contract_identity": "W900-r1-sha256:example",
                    "required_design_inputs": ["work/W900/design/verification.md#checks@sha256:example"],
                    "design_traceability": {
                        "path": "work/W900/design/traceability.yaml",
                        "sha256": hashlib.sha256(traceability_path.read_bytes()).hexdigest(),
                    },
                    "execution_frozen_inputs": [
                        {"path": "src/", "scope": "subtree", "identity": "sha256:example"},
                        {
                            "path": "work/W900/design/traceability.yaml",
                            "scope": "file",
                            "identity": hashlib.sha256(traceability_path.read_bytes()).hexdigest(),
                        },
                    ],
                    "artifact_paths": [
                        "artifacts/frontier/B900/weed-tests.json",
                        "artifacts/frontier/B900/plant-shape-tests.json",
                        "artifacts/frontier/B900/result.yaml",
                        "artifacts/frontier/B900/candidate-manifest.yaml",
                    ],
                }
            )
            result = MODULE.validate(packet, "draft", root)
            self.assertTrue(result["packet_structure_ready"], result["findings"])

    def test_module_packet_cannot_freeze_the_whole_work_plan(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            traceability_path = root / "work/W900/design/traceability.yaml"
            traceability_path.parent.mkdir(parents=True)
            (traceability_path.parents[1] / "WORK.md").write_text(
                "---\nplan_revision: 1\ndesign_contract_identity: W900-r1-sha256:example\n---\n"
            )
            traceability = {
                "work_id": "W900",
                "plan_revision": 1,
                "design_contract_identity": "W900-r1-sha256:example",
                "batches": {
                    "B900": {
                        "delivery_identity": "W900-delivery-B900-sha256:example",
                        "required_design_inputs": ["work/W900/design/verification.md#checks@sha256:example"],
                        "evidence_destinations": [
                            "artifacts/frontier/B900/weed-tests.json"
                        ]
                    }
                },
            }
            traceability_path.write_text(yaml.safe_dump(traceability, sort_keys=False))
            packet = base_packet()
            packet.update(
                {
                    "design_profile": "module",
                    "work_plan": "work/W900/WORK.md",
                    "work_plan_revision": 1,
                    "design_contract_identity": "W900-r1-sha256:example",
                    "required_design_inputs": ["work/W900/design/verification.md#checks@sha256:example"],
                    "design_traceability": {
                        "path": "work/W900/design/traceability.yaml",
                        "sha256": hashlib.sha256(traceability_path.read_bytes()).hexdigest(),
                    },
                    "execution_frozen_inputs": [
                        {
                            "path": "work/W900/WORK.md",
                            "scope": "file",
                            "identity": "sha256:example",
                        },
                        {
                            "path": "work/W900/design/traceability.yaml",
                            "scope": "file",
                            "identity": hashlib.sha256(traceability_path.read_bytes()).hexdigest(),
                        },
                    ],
                    "artifact_paths": [
                        "artifacts/frontier/B900/weed-tests.json",
                        "artifacts/frontier/B900/result.yaml",
                        "artifacts/frontier/B900/candidate-manifest.yaml",
                    ],
                }
            )
            result = MODULE.validate(packet, "draft", root)
            self.assertIn(
                "WHOLE_WORK_PLAN_FROZEN",
                {item["code"] for item in result["findings"]},
            )

    def test_module_work_plan_cannot_own_current_authorization(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            traceability_path = root / "work/W900/design/traceability.yaml"
            traceability_path.parent.mkdir(parents=True)
            (traceability_path.parents[1] / "WORK.md").write_text(
                "---\nplan_revision: 1\ndesign_contract_identity: W900-r1-sha256:example\n"
                "development_authorization: none\n---\n"
            )
            traceability = {
                "work_id": "W900",
                "plan_revision": 1,
                "design_contract_identity": "W900-r1-sha256:example",
                "batches": {
                    "B900": {
                        "delivery_identity": "W900-delivery-B900-sha256:example",
                        "required_design_inputs": ["work/W900/design/verification.md#checks@sha256:example"],
                        "evidence_destinations": ["artifacts/frontier/B900/weed-tests.json"],
                    }
                },
            }
            traceability_path.write_text(yaml.safe_dump(traceability, sort_keys=False))
            packet = base_packet()
            packet.update(
                {
                    "design_profile": "module",
                    "work_plan": "work/W900/WORK.md",
                    "work_plan_revision": 1,
                    "design_contract_identity": "W900-r1-sha256:example",
                    "required_design_inputs": ["work/W900/design/verification.md#checks@sha256:example"],
                    "design_traceability": {
                        "path": "work/W900/design/traceability.yaml",
                        "sha256": hashlib.sha256(traceability_path.read_bytes()).hexdigest(),
                    },
                    "execution_frozen_inputs": [
                        {
                            "path": "work/W900/design/traceability.yaml",
                            "scope": "file",
                            "identity": hashlib.sha256(traceability_path.read_bytes()).hexdigest(),
                        }
                    ],
                    "artifact_paths": [
                        "artifacts/frontier/B900/weed-tests.json",
                        "artifacts/frontier/B900/result.yaml",
                        "artifacts/frontier/B900/candidate-manifest.yaml",
                    ],
                }
            )
            result = MODULE.validate(packet, "draft", root)
            self.assertIn(
                "WORK_PLAN_OWNS_AUTHORIZATION",
                {item["code"] for item in result["findings"]},
            )


if __name__ == "__main__":
    unittest.main()
