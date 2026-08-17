#!/usr/bin/env python3
"""Regression tests for Frontier batch result validation."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

import yaml

import validate_candidate_package as PACKAGE
from test_freeze_execution_baseline import write_bound_dispatch_draft


SCRIPT = Path(__file__).with_name("validate_batch_result.py")
SPEC = importlib.util.spec_from_file_location("validate_batch_result", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)
HASH = "a" * 64


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
        "result_contract_version": MODULE.RESULT_CONTRACT_V1,
        "workflow_source_identity": "sha256:" + HASH,
        "changes_executable_candidate": True,
        "candidate_root_path": "candidates/B900/",
        "candidate_package_inventory_path": "artifacts/frontier/B900/package-inventory.yaml",
        "candidate_manifest_path": "artifacts/frontier/B900/candidate-manifest.yaml",
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
        "result_contract_version": MODULE.RESULT_CONTRACT_V1,
        "workflow_source_identity": "sha256:" + HASH,
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


def formal_evaluation_target() -> dict:
    return {
        "mode": "formal-slot-h",
        "candidate": {
            "id": "B900-candidate-sha256:example",
            "root_path": "candidates/B900/",
            "manifest_path": "artifacts/frontier/B900/candidate-manifest.yaml",
            "manifest_sha256": HASH,
        },
        "implementation_review": {
            "review_id": "R900",
            "result": "IMPLEMENTATION_READY",
            "path": "docs/frontier/reviews/implementation-R900.md",
            "file_sha256": HASH,
        },
        "experiment": {
            "path": "artifacts/frontier/B900/experiment.yaml",
            "experiment_id": "B900-experiment-sha256:example",
            "file_sha256": HASH,
        },
        "slot_h_contract": {
            "path": "docs/frontier/slots/H.md",
            "file_sha256": HASH,
        },
    }


def seed_evaluation_sources(root: Path, target: dict) -> None:
    candidate_root = root / target["candidate"]["root_path"]
    candidate_root.mkdir(parents=True, exist_ok=True)
    main = candidate_root / "main.py"
    main.write_text("def agent(observation, configuration):\n    return {}\n")
    members = [
        {
            "path": "main.py",
            "size": main.stat().st_size,
            "sha256": hashlib.sha256(main.read_bytes()).hexdigest(),
        }
    ]
    package_sha256 = hashlib.sha256(
        json.dumps(members, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    candidate_id = f"B900-candidate-sha256:{package_sha256}"
    manifest = {
        "candidate_id": candidate_id,
        "workflow_source_identity": "sha256:" + HASH,
        "source_result_identity": {
            "package_sha256": package_sha256,
            "members": members,
        },
        "code_paths": [
            {"path": item["path"], "sha256": item["sha256"]} for item in members
        ],
    }
    manifest_path = root / target["candidate"]["manifest_path"]
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False))
    target["candidate"]["id"] = candidate_id
    target["candidate"]["manifest_sha256"] = hashlib.sha256(
        manifest_path.read_bytes()
    ).hexdigest()

    payload = b"mode: test\n"
    experiment_id = "B900-experiment-sha256:" + hashlib.sha256(payload).hexdigest()
    experiment_path = root / target["experiment"]["path"]
    experiment_path.parent.mkdir(parents=True, exist_ok=True)
    experiment_path.write_bytes(f"experiment_id: {experiment_id}\n".encode() + payload)
    target["experiment"]["experiment_id"] = experiment_id
    target["experiment"]["file_sha256"] = hashlib.sha256(
        experiment_path.read_bytes()
    ).hexdigest()

    for binding, path_field, hash_field, content in (
        (target["implementation_review"], "path", "file_sha256", b"implementation review"),
        (target["slot_h_contract"], "path", "file_sha256", b"slot h contract"),
    ):
        source = root / binding[path_field]
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_bytes(content)
        binding[hash_field] = hashlib.sha256(content).hexdigest()


def seed_materialized_candidate(root: Path, packet: dict, result: dict) -> None:
    candidate_root = root / packet["candidate_root_path"]
    candidate_root.mkdir(parents=True, exist_ok=True)
    main = candidate_root / "main.py"
    main.write_text("def agent(observation, configuration):\n    return {}\n")
    members = [
        {
            "path": "main.py",
            "size": main.stat().st_size,
            "sha256": hashlib.sha256(main.read_bytes()).hexdigest(),
        }
    ]
    package_sha256 = hashlib.sha256(
        json.dumps(members, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    candidate_id = f"B900-candidate-sha256:{package_sha256}"
    inventory = PACKAGE.write_candidate_inventory(
        root,
        packet["candidate_root_path"],
        packet["candidate_package_inventory_path"],
        candidate_id,
    )
    evidence_path = root / "artifacts/frontier/B900/engineering/evidence.json"
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(
        json.dumps(
            {
                "inventory_id": inventory["inventory_id"],
                "check": "unit",
                "result": "pass",
            },
            sort_keys=True,
        )
        + "\n"
    )
    source_path = root / "artifacts/frontier/B900/source-base.yaml"
    source_path.write_text("source_base_identity: source-sha256:example\n")
    manifest = {
        "manifest_contract": PACKAGE.FINAL_MANIFEST_CONTRACT,
        "manifest_state": "final",
        "candidate_id": candidate_id,
        "source_result_identity": {
            "package_sha256": package_sha256,
            "members": members,
        },
        "code_paths": [
            {"path": item["path"], "sha256": item["sha256"]} for item in members
        ],
        "package_inventory": {
            "path": packet["candidate_package_inventory_path"],
            "inventory_id": inventory["inventory_id"],
            "file_sha256": inventory["inventory_sha256"],
        },
        "engineering_evidence": [
            {
                "path": evidence_path.relative_to(root).as_posix(),
                "file_sha256": hashlib.sha256(evidence_path.read_bytes()).hexdigest(),
            }
        ],
        "recovery_artifacts": [
            {
                "role": "source-base",
                "path": source_path.relative_to(root).as_posix(),
                "file_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
            }
        ],
    }
    manifest_path = root / packet["candidate_manifest_path"]
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False))
    result["candidate_manifest"] = packet["candidate_manifest_path"]
    result["candidate_identity"] = candidate_id
    result["source_result_identity"] = {"package_sha256": package_sha256}


def diagnostic_evaluation_target() -> dict:
    target = formal_evaluation_target()
    target["mode"] = "diagnostic-only"
    target.pop("implementation_review")
    target.pop("slot_h_contract")
    target.update(
        {
            "exception_evidence": {
                "isolation": "local",
                "hard_constraints": "passed",
                "sealed_evidence": "excluded",
            },
            "consequence_limit": "B evidence only",
            "prohibited_consequences": sorted(MODULE.DIAGNOSTIC_PROHIBITED_CONSEQUENCES),
        }
    )
    return target


def experiment_result(target: dict, *, diagnostic: bool = False) -> dict:
    result = base_result()
    for field in MODULE.EXPERIMENT_LEGACY_BINDING_FIELDS:
        result.pop(field)
    result.update(
        {
            "work_kind": "experiment",
            "changes_executable_candidate": False,
            "changed_paths": ["artifacts/frontier/B900/raw-results.json"],
            "source_result_identity": None,
            "evaluation_target": copy.deepcopy(target),
            "materialization_state": "not-applicable",
            "performance_evaluation_state": (
                "diagnostic-only under cited Entry authority"
                if diagnostic
                else "performed under R900 and B900 authority"
            ),
            "integration_state": "not-authorized" if diagnostic else "not-performed",
            "results": [
                {
                    "candidate": "B900-candidate-sha256:example",
                    "score": 0.5,
                    **({"maximum_consequence": "B evidence only"} if diagnostic else {}),
                }
            ],
        }
    )
    return result


def experiment_packet(target: dict) -> dict:
    packet = base_packet()
    packet.update(
        {
            "work_kind": "experiment",
            "changes_executable_candidate": False,
            "evaluation_target": copy.deepcopy(target),
        }
    )
    return packet


def bound_result_workspace(root: Path) -> tuple[dict, dict, Path]:
    draft_path, _, _ = write_bound_dispatch_draft(root)
    baseline = importlib.util.spec_from_file_location(
        "_baseline_for_result_test", SCRIPT.with_name("freeze_execution_baseline.py")
    )
    assert baseline and baseline.loader
    baseline_module = importlib.util.module_from_spec(baseline)
    sys.modules[baseline.name] = baseline_module
    baseline.loader.exec_module(baseline_module)
    execution_start_path = root / "artifacts/frontier/B900/execution-start.yaml"
    baseline_module.freeze(
        draft_path,
        "artifacts/frontier/B900/execution-baseline/",
        execution_start_path,
        root.resolve(),
    )
    packet = yaml.safe_load((root / "artifacts/frontier/B900/packet.yaml").read_text())
    start = yaml.safe_load(execution_start_path.read_text())
    result = base_result()
    for result_field, packet_field in MODULE.PACKET_BINDINGS.items():
        result[result_field] = packet.get(packet_field)
    result["source_base_identity"] = packet["source_base_identity"]
    result["packet_preflight"] = copy.deepcopy(start["packet_preflight"])
    result["acknowledgment"] = copy.deepcopy(start["acknowledgment"])
    raw = execution_start_path.read_bytes()
    result["execution_start"] = {
        "path": execution_start_path.relative_to(root).as_posix(),
        "identity_field": "execution_start_id",
        "identity": start["execution_start_id"],
        "file_sha256": hashlib.sha256(raw).hexdigest(),
    }
    seed_materialized_candidate(root, packet, result)
    return packet, result, execution_start_path


class BatchResultValidationTests(unittest.TestCase):
    def test_result_identity_serialization_error_is_repair_not_hard_block(self) -> None:
        result = base_result()
        result["result_packet_id"] = "B900-result-sha256:stale"
        validation = MODULE.validate(
            result,
            "frozen",
            base_packet(),
            check_dispatch=False,
        )
        mismatch = [
            finding
            for finding in validation["repair_findings"]
            if finding["code"] == "RESULT_ID_MISMATCH"
        ]
        self.assertEqual(1, len(mismatch))
        self.assertEqual([], validation["blocking_findings"])

    def test_new_result_recomputes_complete_dispatch_chain(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet, result, _ = bound_result_workspace(root)
            validation = MODULE.validate(result, "draft", packet, repo_root=root)
            self.assertTrue(validation["result_structure_ready"], validation["findings"])

    def test_released_source_bound_packet_keeps_versioned_result_contract(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet, result, _ = bound_result_workspace(root)
            released_baseline = MODULE.load_baseline_tool()
            released_baseline.IDENTITY_CONTRACT = "frontier-dispatch-identity/3"
            released_baseline.SUPPORTED_IDENTITY_CONTRACTS = {
                "frontier-dispatch-identity/2",
                "frontier-dispatch-identity/3",
            }
            released_baseline.load_validator = mock.Mock(
                side_effect=AssertionError(
                    "historical result publication must not load live validators"
                )
            )
            with (
                mock.patch.object(
                    MODULE,
                    "IDENTITY_CONTRACT",
                    "frontier-dispatch-identity/3",
                ),
                mock.patch.object(
                    MODULE,
                    "SUPPORTED_IDENTITY_CONTRACTS",
                    {
                        "frontier-dispatch-identity/2",
                        "frontier-dispatch-identity/3",
                    },
                ),
                mock.patch.object(
                    MODULE,
                    "load_baseline_tool",
                    return_value=released_baseline,
                ),
            ):
                validation = MODULE.validate(result, "draft", packet, repo_root=root)
            self.assertTrue(validation["result_structure_ready"], validation["findings"])
            released_baseline.load_validator.assert_not_called()

    def test_new_result_rejects_execution_start_byte_drift(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet, result, execution_start_path = bound_result_workspace(root)
            execution_start_path.write_text(execution_start_path.read_text() + "extra: drift\n")
            raw = execution_start_path.read_bytes()
            start = yaml.safe_load(raw)
            result["execution_start"].update(
                {
                    "identity": start["execution_start_id"],
                    "file_sha256": hashlib.sha256(raw).hexdigest(),
                }
            )
            validation = MODULE.validate(result, "draft", packet, repo_root=root)
            self.assertIn(
                "EXECUTION_START_RECOMPUTATION_FAILED",
                {finding["code"] for finding in validation["findings"]},
            )

    def test_materialized_result_rejects_unreported_candidate_bytecode(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet, result, _ = bound_result_workspace(root)
            cache = root / packet["candidate_root_path"] / "__pycache__/main.pyc"
            cache.parent.mkdir()
            cache.write_bytes(b"unreported bytecode")

            validation = MODULE.validate(result, "draft", packet, repo_root=root)

            self.assertIn(
                "MATERIALIZED_CANDIDATE_PACKAGE_INVALID",
                {finding["code"] for finding in validation["findings"]},
            )

    def test_materialized_result_rejects_preliminary_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet, result, _ = bound_result_workspace(root)
            manifest_path = root / packet["candidate_manifest_path"]
            manifest = yaml.safe_load(manifest_path.read_text())
            manifest.pop("manifest_contract")
            manifest.pop("manifest_state")
            manifest["engineering_evidence"] = [
                {"path": "artifacts/frontier/B900/engineering/", "state": "pending"}
            ]
            manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False))

            validation = MODULE.validate(result, "draft", packet, repo_root=root)

            self.assertIn(
                "MATERIALIZED_CANDIDATE_PACKAGE_INVALID",
                {finding["code"] for finding in validation["findings"]},
            )

    def test_materialized_result_rejects_manifest_downstream_dependency(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet, result, _ = bound_result_workspace(root)
            manifest_path = root / packet["candidate_manifest_path"]
            manifest = yaml.safe_load(manifest_path.read_text())
            source = root / "artifacts/frontier/B900/source-base.yaml"
            manifest["recovery_artifacts"].append(
                {
                    "role": "result-validation",
                    "path": source.relative_to(root).as_posix(),
                    "file_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                }
            )
            manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False))

            validation = MODULE.validate(result, "draft", packet, repo_root=root)

            self.assertIn(
                "MATERIALIZED_CANDIDATE_PACKAGE_INVALID",
                {finding["code"] for finding in validation["findings"]},
            )

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
        target = formal_evaluation_target()
        packet = experiment_packet(target)
        result = experiment_result(target)
        validation = MODULE.validate(result, "draft", packet)
        self.assertTrue(validation["result_structure_ready"], validation["findings"])

    def test_diagnostic_only_evaluation_allows_bounded_results_without_review(self) -> None:
        target = diagnostic_evaluation_target()
        packet = experiment_packet(target)
        result = experiment_result(target, diagnostic=True)
        validation = MODULE.validate(result, "draft", packet)
        self.assertTrue(validation["result_structure_ready"], validation["findings"])

    def test_diagnostic_only_evaluation_rejects_integration_drift(self) -> None:
        target = diagnostic_evaluation_target()
        packet = experiment_packet(target)
        result = experiment_result(target, diagnostic=True)
        result["integration_state"] = "not-performed"
        validation = MODULE.validate(result, "draft", packet)
        codes = {finding["code"] for finding in validation["findings"]}
        self.assertIn("DIAGNOSTIC_INTEGRATION_BOUNDARY_INVALID", codes)

    def test_diagnostic_target_controls_boundary_when_worker_changes_state(self) -> None:
        target = diagnostic_evaluation_target()
        packet = experiment_packet(target)
        result = experiment_result(target, diagnostic=True)
        result["performance_evaluation_state"] = "not-performed"
        result["integration_state"] = "performed"
        result["results"] = [{"strength_claim": "strong"}]
        validation = MODULE.validate(result, "draft", packet)
        codes = {finding["code"] for finding in validation["findings"]}
        self.assertIn("DIAGNOSTIC_PERFORMANCE_STATE_INVALID", codes)
        self.assertIn("DIAGNOSTIC_INTEGRATION_BOUNDARY_INVALID", codes)
        self.assertIn("DIAGNOSTIC_RESULT_CLAIM_PRESENT", codes)

    def test_formal_target_rejects_diagnostic_only_bindings(self) -> None:
        target = formal_evaluation_target()
        target.update(
            {
                "exception_evidence": {"isolation": "local"},
                "consequence_limit": "B evidence only",
                "prohibited_consequences": sorted(MODULE.DIAGNOSTIC_PROHIBITED_CONSEQUENCES),
            }
        )
        packet = experiment_packet(target)
        result = experiment_result(target)
        validation = MODULE.validate(result, "draft", packet)
        self.assertIn(
            "FORMAL_DIAGNOSTIC_BINDING_PRESENT",
            {finding["code"] for finding in validation["findings"]},
        )

    def test_diagnostic_target_cannot_reuse_completed_evidence(self) -> None:
        target = diagnostic_evaluation_target()
        target["evidence_reuse"] = {
            "source_batch_id": "B035",
            "raw_artifacts": [
                {
                    "path": "artifacts/frontier/B035/dev/raw-results.json",
                    "file_sha256": HASH,
                }
            ],
            "measurement_execution": "prohibited",
            "reruns": 0,
            "measurement_semantics": "unchanged",
        }
        packet = experiment_packet(target)
        result = experiment_result(target, diagnostic=True)
        validation = MODULE.validate(result, "draft", packet)
        self.assertIn(
            "EVIDENCE_REUSE_MODE_INVALID",
            {finding["code"] for finding in validation["findings"]},
        )

    def test_formal_evaluation_requires_implementation_ready(self) -> None:
        target = formal_evaluation_target()
        target["implementation_review"]["result"] = "NOT_IMPLEMENTATION_READY"
        packet = experiment_packet(target)
        result = experiment_result(target)
        validation = MODULE.validate(result, "draft", packet)
        self.assertIn(
            "FORMAL_EVALUATION_REVIEW_MISSING",
            {finding["code"] for finding in validation["findings"]},
        )

    def test_formal_evaluation_rejects_target_drift(self) -> None:
        target = formal_evaluation_target()
        packet = experiment_packet(target)
        result = experiment_result(target)
        result["evaluation_target"]["candidate"]["id"] = "different-candidate"
        validation = MODULE.validate(result, "draft", packet)
        codes = {finding["code"] for finding in validation["findings"]}
        self.assertIn("EVALUATION_TARGET_BINDING_MISMATCH", codes)

    def test_experiment_rejects_flat_binding_aliases(self) -> None:
        target = formal_evaluation_target()
        packet = experiment_packet(target)
        result = experiment_result(target)
        result["candidate_identity"] = target["candidate"]["id"]
        validation = MODULE.validate(result, "draft", packet)
        self.assertIn(
            "EXPERIMENT_LEGACY_BINDING_PRESENT",
            {finding["code"] for finding in validation["findings"]},
        )

    def test_completed_raw_evidence_can_be_published_without_rerun(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = formal_evaluation_target()
            seed_evaluation_sources(root, target)
            raw_path = root / "artifacts/frontier/B035/dev/raw-results.json"
            raw_path.parent.mkdir(parents=True)
            raw_path.write_bytes(b"exact raw evidence")
            target["evidence_reuse"] = {
                "source_batch_id": "B035",
                "raw_artifacts": [
                    {
                        "path": "artifacts/frontier/B035/dev/raw-results.json",
                        "file_sha256": hashlib.sha256(b"exact raw evidence").hexdigest(),
                    }
                ],
                "measurement_execution": "prohibited",
                "reruns": 0,
                "measurement_semantics": "unchanged",
            }
            packet = experiment_packet(target)
            result = experiment_result(target)
            result["actual_spend"] = "0 new measurement spend"
            result["accounting_evidence"] = "reused content-addressed B035 raw evidence"
            result["evidence_reuse_accounting"] = {
                "new_measurement_executions": 0,
                "reruns": 0,
                "new_measurement_spend": 0,
            }
            validation = MODULE.validate(
                result, "draft", packet, repo_root=root, check_dispatch=False
            )
            self.assertTrue(validation["result_structure_ready"], validation["findings"])
            frozen = copy.deepcopy(result)
            frozen["result_packet_id"] = validation["computed_result_packet_id"]
            self.assertEqual(
                validation,
                MODULE.validate(
                    frozen,
                    "frozen",
                    packet,
                    repo_root=root,
                    check_dispatch=False,
                ),
            )

            result["actual_spend"] = "128 newly rerun games"
            validation = MODULE.validate(result, "draft", packet, repo_root=root)
            self.assertIn(
                "EVIDENCE_REUSE_ACCOUNTING_INVALID",
                {finding["code"] for finding in validation["findings"]},
            )
            result["actual_spend"] = "0 new measurement spend"
            raw_path.write_bytes(b"mutated after packet preflight")
            validation = MODULE.validate(result, "draft", packet, repo_root=root)
            self.assertIn(
                "EVIDENCE_REUSE_SOURCE_IDENTITY_MISMATCH",
                {finding["code"] for finding in validation["findings"]},
            )

    def test_evaluation_rejects_unreported_candidate_bytecode(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = formal_evaluation_target()
            seed_evaluation_sources(root, target)
            cache = root / target["candidate"]["root_path"] / "__pycache__/main.pyc"
            cache.parent.mkdir()
            cache.write_bytes(b"unreported bytecode")

            validation = MODULE.validate(
                experiment_result(target),
                "draft",
                experiment_packet(target),
                repo_root=root,
                check_dispatch=False,
            )

            self.assertIn(
                "EVALUATION_CANDIDATE_PACKAGE_INVALID",
                {finding["code"] for finding in validation["findings"]},
            )

    def test_evaluation_recomputes_experiment_identity_from_source_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = formal_evaluation_target()
            seed_evaluation_sources(root, target)
            target["experiment"]["experiment_id"] = (
                "B899-experiment-sha256:" + "1" * 64
            )

            validation = MODULE.validate(
                experiment_result(target),
                "draft",
                experiment_packet(target),
                repo_root=root,
                check_dispatch=False,
            )

            self.assertIn(
                "EXPERIMENT_IDENTITY_MISMATCH",
                {finding["code"] for finding in validation["findings"]},
            )

    def test_completed_formal_evaluation_requires_nonempty_results(self) -> None:
        target = formal_evaluation_target()
        packet = experiment_packet(target)
        result = experiment_result(target)
        result["results"] = []
        validation = MODULE.validate(result, "draft", packet)
        self.assertIn(
            "FORMAL_EVALUATION_RESULTS_MISSING",
            {finding["code"] for finding in validation["findings"]},
        )

    def test_formal_evaluation_cannot_perform_integration(self) -> None:
        target = formal_evaluation_target()
        packet = experiment_packet(target)
        result = experiment_result(target)
        result["integration_state"] = "performed under alleged integration authority"
        validation = MODULE.validate(result, "draft", packet)
        self.assertIn(
            "FORMAL_EVALUATION_INTEGRATION_INVALID",
            {finding["code"] for finding in validation["findings"]},
        )

    def test_diagnostic_result_requires_bounded_consequence_and_rejects_claims(self) -> None:
        target = diagnostic_evaluation_target()
        packet = experiment_packet(target)
        result = experiment_result(target, diagnostic=True)
        result["results"] = [{"strength_claim": "candidate is strong"}]
        validation = MODULE.validate(result, "draft", packet)
        codes = {finding["code"] for finding in validation["findings"]}
        self.assertIn("DIAGNOSTIC_RESULT_CONSEQUENCE_MISSING", codes)
        self.assertIn("DIAGNOSTIC_RESULT_CLAIM_PRESENT", codes)

    def test_diagnostic_result_rejects_nested_claims(self) -> None:
        target = diagnostic_evaluation_target()
        packet = experiment_packet(target)
        result = experiment_result(target, diagnostic=True)
        result["results"] = [
            {
                "maximum_consequence": "B evidence only",
                "details": {"strength_claim": "strong", "promotion": "yes"},
            }
        ]
        validation = MODULE.validate(result, "draft", packet)
        self.assertIn(
            "DIAGNOSTIC_RESULT_CLAIM_PRESENT",
            {finding["code"] for finding in validation["findings"]},
        )

    def test_result_binding_must_match_packet(self) -> None:
        result = base_result()
        result["campaign_generation"] = 3
        validation = MODULE.validate(result, "draft", base_packet())
        self.assertIn(
            "PACKET_BINDING_MISMATCH",
            {finding["code"] for finding in validation["findings"]},
        )

    def test_non_experiment_result_rejects_evaluation_target(self) -> None:
        result = base_result()
        result["evaluation_target"] = formal_evaluation_target()
        validation = MODULE.validate(result, "draft", base_packet())
        self.assertIn(
            "EVALUATION_TARGET_OUTSIDE_EXPERIMENT",
            {finding["code"] for finding in validation["findings"]},
        )

    def test_accounting_without_evidence_reuse_is_rejected(self) -> None:
        target = formal_evaluation_target()
        packet = experiment_packet(target)
        result = experiment_result(target)
        result["evidence_reuse_accounting"] = {
            "new_measurement_executions": 0,
            "reruns": 0,
            "new_measurement_spend": 0,
        }
        validation = MODULE.validate(result, "draft", packet)
        self.assertIn(
            "EVIDENCE_REUSE_ACCOUNTING_OUTSIDE_RECOVERY",
            {finding["code"] for finding in validation["findings"]},
        )

    def test_cli_rejects_legacy_packet_before_final_result_path_exists(self) -> None:
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
            self.assertEqual(completed.returncode, 1, completed.stderr)
            validation = json.loads(validation_path.read_text())
            self.assertIn(
                "DISPATCH_CONTRACT_UNSUPPORTED",
                {finding["code"] for finding in validation["findings"]},
            )
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
