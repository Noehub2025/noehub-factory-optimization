#!/usr/bin/env python3
"""Regression tests for the Frontier batch packet preflight."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

from test_validate_entry_packet import write_workflow_source_binding


SCRIPT = Path(__file__).with_name("validate_batch_packet.py")
SPEC = importlib.util.spec_from_file_location("validate_batch_packet", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)
HASH = "a" * 64
REPO_ROOT = SCRIPT.parents[4]


def file_binding(path: Path, identity_field: str | None = None) -> dict:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    identity = (
        yaml.safe_load(path.read_text())[identity_field]
        if identity_field is not None
        else f"sha256:{digest}"
    )
    return {
        "path": path.relative_to(REPO_ROOT).as_posix(),
        "identity_field": identity_field,
        "identity": identity,
        "file_sha256": digest,
    }


def project_fixture_binding(name: str, identity_field: str | None = None) -> dict:
    source = SCRIPT.parent / "fixtures" / name
    binding = file_binding(source, identity_field)
    binding["path"] = f"artifacts/frontier/test-fixtures/{name}"
    return binding


def seed_identity_sources(root: Path, packet: dict) -> None:
    packet["workflow_source_binding"] = write_workflow_source_binding(root)
    packet["workflow_source_identity"] = packet["workflow_source_binding"][
        "source_snapshot"
    ]["identity"]
    bindings = [packet["source_base_binding"], packet["design_contract_binding"]]
    for binding in bindings:
        relative = binding["path"]
        destination = root / relative
        if destination.is_file():
            continue
        source = REPO_ROOT / relative
        if not source.is_file():
            source = SCRIPT.parent / "fixtures" / Path(relative).name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
    target_binding = packet.get("development_authorization_target")
    if isinstance(target_binding, dict):
        template_source = REPO_ROOT / target_binding["path"]
        if not template_source.is_file():
            template_source = SCRIPT.parent / "fixtures" / Path(target_binding["path"]).name
        template = yaml.safe_load(template_source.read_text())
        template.pop("target_spec_id", None)
        boundary = packet["authorization_boundary"]
        template.update(
            {
                "batch_id": packet["batch_id"],
                "design_contract_identity": packet["design_contract_identity"],
                "source_base_identity": packet["source_base_identity"],
                "scope": boundary["scope"],
                "maximum_spend": boundary["maximum_spend"],
                "stop_boundary": boundary["stop_boundary"],
                "result_path": boundary["result_path"],
            }
        )
        payload = yaml.safe_dump(template, sort_keys=False).encode()
        identity = (
            f"{template['decision_id']}-target-spec-sha256:"
            + hashlib.sha256(payload).hexdigest()
        )
        raw = f"target_spec_id: {identity}\n".encode() + payload
        destination = root / target_binding["path"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(raw)
        target_binding.update(
            {
                "identity": identity,
                "file_sha256": hashlib.sha256(raw).hexdigest(),
            }
        )


def base_packet() -> dict:
    direct_binding = project_fixture_binding("authorization-source.txt")
    target_spec_binding = project_fixture_binding(
        "authorization-target-spec.yaml",
        "target_spec_id",
    )
    target_spec_binding["contract_version"] = (
        "frontier-authorization-target-specification/1"
    )
    return {
        "packet_path": "artifacts/frontier/B900/packet.yaml",
        "packet_preflight_path": "artifacts/frontier/B900/packet-preflight.json",
        "task_path": "docs/skills/optimization/example",
        "batch_id": "B900",
        "campaign_generation": 2,
        "route_id": "T900",
        "parallel_set": None,
        "work_kind": "code",
        "problem_epoch": 3,
        "representation_revision": 4,
        "changes_executable_candidate": True,
        "executor": "Agent",
        "required_inputs": [],
        "identity_contract": MODULE.IDENTITY_CONTRACT,
        "result_contract_version": MODULE.RESULT_CONTRACT_V2,
        "workflow_source_binding": {
            "contract_version": "frontier-workflow-source-binding/1",
            "adoption_mode": "entry",
            "source_manifest": {
                "path": "artifacts/frontier/workflow/R900/source-manifest.yaml",
                "identity": f"sha256:{HASH}",
                "file_sha256": HASH,
            },
            "source_snapshot": {
                "path": "artifacts/frontier/workflow/R900/source-snapshot.yaml",
                "identity": f"sha256:{HASH}",
                "file_sha256": HASH,
            },
            "governs": ["B900", "packet", "execution", "result"],
        },
        "workflow_source_identity": f"sha256:{HASH}",
        "worker_source_member": "workers/run-frontier-batch/SKILL.md",
        "design_profile": "direct",
        "design_contract_identity": direct_binding["identity"],
        "design_contract_binding": copy.deepcopy(direct_binding),
        "development_authorization_target": target_spec_binding,
        "source_base_identity": direct_binding["identity"],
        "source_base_binding": copy.deepcopy(direct_binding),
        "maximum_spend": "one proposal attempt",
        "authorization_gate": "finding-free Entry adoption",
        "authorization_boundary": {
            "scope": "one bounded implementation",
            "maximum_spend": "one proposal attempt",
            "stop_boundary": "materialized-stopped",
            "result_path": "artifacts/frontier/B900/result.yaml",
        },
        "stop_conditions": ["stop at the packet boundary"],
        "forced_halts": [],
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
        "candidate_root_path": "candidates/B900/",
        "candidate_package_inventory_path": "artifacts/frontier/B900/package-inventory.yaml",
        "candidate_manifest_path": "artifacts/frontier/B900/candidate-manifest.yaml",
        "engineering_check_plan": {
            "contract_version": MODULE.ENGINEERING_CHECK_PLAN_CONTRACT,
            "checks": [
                {
                    "id": "bounded-unit-check",
                    "command": ["python", "-m", "unittest", "tests.test_unit"],
                    "selection": "exact",
                    "selected_units": ["tests.test_unit"],
                    "declared_effects": ["local-code-execution"],
                    "effect_evidence": [
                        {
                            "path": direct_binding["path"],
                            "file_sha256": direct_binding["file_sha256"],
                        }
                    ],
                }
            ],
            "effect_limits": {"local-code-execution": 1},
            "evidence_use": "engineering-only",
        },
        "artifact_paths": [
            "candidates/B900/",
            "artifacts/frontier/B900/result.yaml",
            "artifacts/frontier/B900/package-inventory.yaml",
            "artifacts/frontier/B900/candidate-manifest.yaml",
        ],
        "acknowledgment_path": "artifacts/frontier/B900/acknowledgment.yaml",
        "result_validation_path": "artifacts/frontier/B900/result-validation.json",
        "result_packet_path": "artifacts/frontier/B900/result.yaml",
        "prohibited_actions": ["edit packet, execution-start, parents, evaluator, or tests"],
    }


class ProjectOnlyBatchSchemaTests(unittest.TestCase):
    def test_unknown_workflow_identity_field_is_rejected(self) -> None:
        packet = base_packet()
        packet["workflow_release_identity"] = "workflow-sha256:" + "a" * 64

        result = MODULE.validate(packet, "draft")

        self.assertIn("UNKNOWN_PACKET_FIELD", {item["code"] for item in result["findings"]})
        self.assertEqual([], result["blocking_findings"])
        self.assertEqual("repair", result["repair_findings"][0]["effect"])

    def test_workflow_skill_path_is_rejected_outside_named_legacy_field(self) -> None:
        packet = base_packet()
        packet["required_inputs"] = [".agents/skills/frontier-optimization/SKILL.md"]

        result = MODULE.validate(packet, "draft")

        self.assertIn("NON_PROJECT_PACKET_INPUT", {item["code"] for item in result["findings"]})

    def test_project_workflow_validator_and_skill_terms_remain_task_neutral(self) -> None:
        packet = base_packet()
        packet.update(
            {
                "work": "Improve the project workflow source parser",
                "implementation_validation": "run project validator tests",
                "expected_observation": "Skill validation accuracy improves",
            }
        )

        result = MODULE.validate(packet, "draft")

        self.assertTrue(result["packet_structure_ready"], result["findings"])


def lifecycle_contract() -> dict:
    return {
        "contract_version": "frontier-lifecycle-transition/1",
        "path": "docs/skills/optimization/example/FRONTIER.md",
        "prerequisite": "accepted B900 acknowledgment",
        "deadline": "before execution baseline and execution-start",
        "precondition": {
            "campaign_status": "planned",
            "file_identity": f"sha256:{'0' * 64}",
        },
        "transition_time": {
            "capture": "once_after_accepted_acknowledgment",
            "format": "RFC3339",
            "timezone": "UTC",
        },
        "allowed_field_diff": {
            "campaign_status": {"from": "planned", "to": "running"},
            "generated.at": {"derive": "transition_time"},
            "updated": {
                "derive": "calendar_date",
                "source": "transition_time",
                "timezone": "UTC",
            },
        },
        "all_other_bytes": "unchanged",
        "on_failure": "block_before_work_and_spend",
    }


def formal_evaluation_target() -> dict:
    return {
        "mode": "formal-slot-h",
        "candidate": {
            "id": "B026-candidate-sha256:example",
            "root_path": "candidates/B026/",
            "manifest_path": "artifacts/frontier/B026/candidate-manifest.yaml",
            "manifest_sha256": HASH,
        },
        "implementation_review": {
            "review_id": "R056",
            "result": "IMPLEMENTATION_READY",
            "path": "docs/frontier/reviews/implementation-R056.md",
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
    (candidate_root / "main.py").write_text("def agent(observation, configuration):\n    return {}\n")
    members = [
        {
            "path": "main.py",
            "size": (candidate_root / "main.py").stat().st_size,
            "sha256": hashlib.sha256((candidate_root / "main.py").read_bytes()).hexdigest(),
        }
    ]
    package_sha256 = hashlib.sha256(
        json.dumps(members, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    candidate_id = f"B900-candidate-sha256:{package_sha256}"
    manifest = {
        "candidate_id": candidate_id,
        "workflow_source_identity": f"sha256:{HASH}",
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

    experiment_payload = b"mode: test\n"
    experiment_id = (
        "B900-experiment-sha256:" + hashlib.sha256(experiment_payload).hexdigest()
    )
    experiment_path = root / target["experiment"]["path"]
    experiment_path.parent.mkdir(parents=True, exist_ok=True)
    experiment_path.write_bytes(
        f"experiment_id: {experiment_id}\n".encode() + experiment_payload
    )
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


class PacketPreflightTests(unittest.TestCase):
    def test_code_packet_requires_pre_execution_inventory_path(self) -> None:
        packet = base_packet()
        packet.pop("candidate_package_inventory_path")

        result = MODULE.validate(packet, "draft", REPO_ROOT)

        self.assertIn(
            "INVALID_PATH_SCHEMA",
            {item["code"] for item in result["findings"]},
        )

    def test_code_packet_requires_engineering_check_plan(self) -> None:
        packet = base_packet()
        packet.pop("engineering_check_plan")

        result = MODULE.validate(packet, "draft", REPO_ROOT)

        self.assertIn(
            "ENGINEERING_CHECK_PLAN_REQUIRED",
            {item["code"] for item in result["findings"]},
        )

    def test_declared_engineering_effect_cannot_have_zero_authority(self) -> None:
        packet = base_packet()
        check = packet["engineering_check_plan"]["checks"][0]
        check["selection"] = "full-repository"
        check["selected_units"] = [
            "tests/test_harness.py::test_evaluator_fixture"
        ]
        check["declared_effects"] = ["local-evaluator-fixture"]
        packet["engineering_check_plan"]["effect_limits"] = {
            "local-evaluator-fixture": 0
        }

        result = MODULE.validate(packet, "draft", REPO_ROOT)

        self.assertIn(
            "ENGINEERING_EFFECT_CONFLICT",
            {item["code"] for item in result["findings"]},
        )

    def test_engineering_effect_classification_source_is_content_addressed(self) -> None:
        packet = base_packet()
        packet["engineering_check_plan"]["checks"][0]["effect_evidence"][0][
            "file_sha256"
        ] = "0" * 64

        result = MODULE.validate(packet, "draft", REPO_ROOT)

        self.assertIn(
            "ENGINEERING_EFFECT_EVIDENCE_INVALID",
            {item["code"] for item in result["findings"]},
        )

    def test_scalar_final_target_identity_is_rejected_before_packet_freeze(self) -> None:
        packet = base_packet()
        packet["development_authorization_target"] = (
            f"V900-target-sha256:{'1' * 64}"
        )

        result = MODULE.validate(packet, "draft", REPO_ROOT)

        self.assertIn(
            "DEVELOPMENT_AUTHORIZATION_TARGET_INVALID",
            {item["code"] for item in result["findings"]},
        )

    def test_target_specification_cannot_contain_current_packet_identity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet = base_packet()
            seed_identity_sources(root, packet)
            binding = packet["development_authorization_target"]
            path = root / binding["path"]
            document = yaml.safe_load(path.read_text())
            document.pop("target_spec_id")
            document["authorization_question"] = (
                f"Authorize B900-packet-sha256:{'1' * 64}?"
            )
            payload = yaml.safe_dump(document, sort_keys=False).encode()
            identity = (
                "V900-target-spec-sha256:" + hashlib.sha256(payload).hexdigest()
            )
            raw = f"target_spec_id: {identity}\n".encode() + payload
            path.write_bytes(raw)
            binding.update(
                {
                    "identity": identity,
                    "file_sha256": hashlib.sha256(raw).hexdigest(),
                }
            )

            result = MODULE.validate(packet, "draft", root)

            self.assertIn(
                "DEVELOPMENT_AUTHORIZATION_TARGET_INVALID",
                {item["code"] for item in result["findings"]},
            )

    def test_target_specification_cannot_contain_downstream_chain_identities(self) -> None:
        identities = (
            f"entry-R999-packet-sha256:{'1' * 64}",
            f"authorization-adoption-sha256:{'2' * 64}",
            f"B900-acknowledgment-sha256:{'3' * 64}",
            f"B900-execution-start-sha256:{'4' * 64}",
        )
        for forbidden_identity in identities:
            with self.subTest(forbidden_identity=forbidden_identity):
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    packet = base_packet()
                    seed_identity_sources(root, packet)
                    binding = packet["development_authorization_target"]
                    path = root / binding["path"]
                    document = yaml.safe_load(path.read_text())
                    document.pop("target_spec_id")
                    document["authorization_question"] = forbidden_identity
                    payload = yaml.safe_dump(document, sort_keys=False).encode()
                    identity = (
                        "V900-target-spec-sha256:"
                        + hashlib.sha256(payload).hexdigest()
                    )
                    raw = f"target_spec_id: {identity}\n".encode() + payload
                    path.write_bytes(raw)
                    binding.update(
                        {
                            "identity": identity,
                            "file_sha256": hashlib.sha256(raw).hexdigest(),
                        }
                    )

                    result = MODULE.validate(packet, "draft", root)

                    self.assertIn(
                        "DEVELOPMENT_AUTHORIZATION_TARGET_INVALID",
                        {item["code"] for item in result["findings"]},
                    )

    def test_target_specification_path_cannot_collide_with_packet_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet = base_packet()
            seed_identity_sources(root, packet)
            binding = packet["development_authorization_target"]
            path = root / binding["path"]
            document = yaml.safe_load(path.read_text())
            document.pop("target_spec_id")
            document["target_path"] = packet["packet_path"]
            payload = yaml.safe_dump(document, sort_keys=False).encode()
            identity = (
                "V900-target-spec-sha256:" + hashlib.sha256(payload).hexdigest()
            )
            raw = f"target_spec_id: {identity}\n".encode() + payload
            path.write_bytes(raw)
            binding.update(
                {
                    "identity": identity,
                    "file_sha256": hashlib.sha256(raw).hexdigest(),
                }
            )

            result = MODULE.validate(packet, "draft", root)

            self.assertIn(
                "DEVELOPMENT_AUTHORIZATION_TARGET_MISMATCH",
                {item["code"] for item in result["findings"]},
            )

    def test_target_specification_requires_canonical_task_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet = base_packet()
            seed_identity_sources(root, packet)
            binding = packet["development_authorization_target"]
            path = root / binding["path"]
            document = yaml.safe_load(path.read_text())
            document.pop("target_spec_id")
            document["decision_record_path"] = packet["task_path"] + "/decisions.md"
            document["post_adoption_paths"].append(document["decision_record_path"])
            payload = yaml.safe_dump(document, sort_keys=False).encode()
            identity = "V900-target-spec-sha256:" + hashlib.sha256(payload).hexdigest()
            raw = f"target_spec_id: {identity}\n".encode() + payload
            path.write_bytes(raw)
            binding.update(
                {
                    "identity": identity,
                    "file_sha256": hashlib.sha256(raw).hexdigest(),
                }
            )

            result = MODULE.validate(packet, "draft", root)

            self.assertIn(
                "DEVELOPMENT_AUTHORIZATION_TARGET_MISMATCH",
                {item["code"] for item in result["findings"]},
            )

    def test_target_specification_binding_path_must_be_canonical(self) -> None:
        packet = base_packet()
        packet["development_authorization_target"]["path"] = (
            ".agents/skills/frontier-optimization/scripts/fixtures/../fixtures/"
            "authorization-target-spec.yaml"
        )

        result = MODULE.validate(packet, "draft", REPO_ROOT)

        self.assertIn(
            "DEVELOPMENT_AUTHORIZATION_TARGET_INVALID",
            {item["code"] for item in result["findings"]},
        )

    def test_workflow_and_skill_bindings_are_rejected_from_project_packet(self) -> None:
        packet = base_packet()
        packet["workflow_contracts"] = {
            "worker_skill": {
                "path": ".agents/skills/run-frontier-batch/SKILL.md",
                "sha256": "0" * 64,
            }
        }

        result = MODULE.validate(packet, "draft", REPO_ROOT)

        self.assertFalse(result["packet_structure_ready"])
        self.assertIn(
            "WORKFLOW_CONTRACTS_RETIRED",
            {item["code"] for item in result["findings"]},
        )

    def test_cli_closes_legacy_draft_and_frozen_writers(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet_path = root / "packet.yaml"
            draft_output = root / "draft.json"
            frozen_output = root / "frozen.json"
            packet = base_packet()
            seed_identity_sources(root, packet)
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
                    "--repo-root",
                    str(root),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(draft.returncode, 2)
            self.assertIn("legacy packet writer is closed", draft.stderr)
            self.assertFalse(draft_output.exists())

            frozen = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    str(packet_path),
                    "--phase",
                    "frozen",
                    "--output",
                    str(frozen_output),
                    "--repo-root",
                    str(root),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(frozen.returncode, 2)
            self.assertIn("legacy packet writer is closed", frozen.stderr)
            self.assertFalse(frozen_output.exists())

    def test_valid_draft_and_frozen_packet_share_preflight_identity(self) -> None:
        draft = base_packet()
        draft_result = MODULE.validate(draft, "draft")
        self.assertTrue(draft_result["packet_structure_ready"])
        frozen = copy.deepcopy(draft)
        frozen["packet_id"] = draft_result["computed_packet_id"]
        frozen_result = MODULE.validate(frozen, "frozen")
        self.assertTrue(frozen_result["packet_structure_ready"])
        self.assertEqual(draft_result, frozen_result)

    def test_formal_evaluation_packet_passes_result_contract_before_authorization(self) -> None:
        packet = base_packet()
        packet.update(
            {
                "work_kind": "experiment",
                "changes_executable_candidate": False,
                "candidate_root_path": None,
                "candidate_manifest_path": None,
                "evaluation_target": formal_evaluation_target(),
            }
        )
        result = MODULE.validate(packet, "draft")
        self.assertTrue(result["packet_structure_ready"], result["findings"])
        self.assertEqual(result["checks"]["result_contract_compatibility"], "PASS")
        self.assertEqual(
            result["result_contract_probe"]["validator"],
            "frontier-batch-result-preflight/6",
        )
        self.assertTrue(result["result_contract_probe"]["validation_id"])
        frozen = copy.deepcopy(packet)
        frozen["packet_id"] = result["computed_packet_id"]
        self.assertEqual(result, MODULE.validate(frozen, "frozen"))

    def test_experiment_identity_must_not_be_copied_into_prose_fields(self) -> None:
        packet = base_packet()
        target = formal_evaluation_target()
        packet.update(
            {
                "work_kind": "experiment",
                "changes_executable_candidate": False,
                "candidate_root_path": None,
                "candidate_manifest_path": None,
                "evaluation_target": target,
                "starting_artifacts": [
                    f"stale experiment B899-experiment-sha256:{'1' * 64}"
                ],
            }
        )
        packet["required_inputs"] = [
            f"matching experiment B900-experiment-sha256:{'2' * 64}"
        ]
        packet["expected_observation"] = (
            f"stale experiment B898-experiment-sha256:{'3' * 64}"
        )
        packet["comparison_validity_checks"] = {
            "nested": [f"stale experiment B897-experiment-sha256:{'4' * 64}"]
        }

        result = MODULE.validate(packet, "draft")

        duplicates = [
            item
            for item in result["findings"]
            if item["code"] == "DUPLICATE_EXPERIMENT_IDENTITY"
        ]
        self.assertEqual(len(duplicates), 4)

    def test_formal_evaluation_packet_rejects_legacy_flat_result_contract(self) -> None:
        packet = base_packet()
        packet.update(
            {
                "work_kind": "experiment",
                "changes_executable_candidate": False,
                "candidate_root_path": None,
                "candidate_manifest_path": None,
                "evaluation_target": {
                    "mode": "formal-slot-h",
                    "candidate_identity": "B026-candidate-sha256:example",
                    "candidate_manifest": "artifacts/frontier/B026/candidate-manifest.yaml",
                    "experiment_identity": "B900-experiment-sha256:example",
                    "implementation_review": {
                        "review_result": "IMPLEMENTATION_READY",
                        "review_identity": "R056-sha256:example",
                    },
                    "slot_h_contract": "slot-h-sha256:example",
                },
            }
        )
        result = MODULE.validate(packet, "draft")
        self.assertFalse(result["packet_structure_ready"])
        self.assertEqual(result["checks"]["result_contract_compatibility"], "FAIL")
        self.assertIn(
            "EVALUATION_TARGET_LEGACY_BINDING_PRESENT",
            {finding["code"] for finding in result["findings"]},
        )

    def test_canonical_target_rejects_added_flat_aliases(self) -> None:
        packet = base_packet()
        target = formal_evaluation_target()
        target["candidate_identity"] = target["candidate"]["id"]
        target["candidate_manifest"] = target["candidate"]["manifest_path"]
        target["experiment_identity"] = target["experiment"]["experiment_id"]
        packet.update(
            {
                "work_kind": "experiment",
                "changes_executable_candidate": False,
                "candidate_root_path": None,
                "candidate_manifest_path": None,
                "evaluation_target": target,
            }
        )
        result = MODULE.validate(packet, "draft")
        self.assertIn(
            "EVALUATION_TARGET_LEGACY_BINDING_PRESENT",
            {finding["code"] for finding in result["findings"]},
        )

    def test_diagnostic_target_rejects_formal_only_bindings(self) -> None:
        packet = base_packet()
        target = formal_evaluation_target()
        target.update(
            {
                "mode": "diagnostic-only",
                "exception_evidence": {"isolation": "local"},
                "consequence_limit": "B evidence only",
                "prohibited_consequences": sorted(
                    MODULE.RESULT_CONTRACT_VALIDATOR.DIAGNOSTIC_PROHIBITED_CONSEQUENCES
                ),
            }
        )
        packet.update(
            {
                "work_kind": "experiment",
                "changes_executable_candidate": False,
                "candidate_root_path": None,
                "candidate_manifest_path": None,
                "evaluation_target": target,
            }
        )
        result = MODULE.validate(packet, "draft")
        self.assertIn(
            "DIAGNOSTIC_FORMAL_BINDING_PRESENT",
            {finding["code"] for finding in result["findings"]},
        )

    def test_evaluation_target_rejects_non_sha256_identity(self) -> None:
        packet = base_packet()
        target = formal_evaluation_target()
        target["slot_h_contract"]["file_sha256"] = "not-a-sha256"
        packet.update(
            {
                "work_kind": "experiment",
                "changes_executable_candidate": False,
                "candidate_root_path": None,
                "candidate_manifest_path": None,
                "evaluation_target": target,
            }
        )
        result = MODULE.validate(packet, "draft")
        self.assertIn(
            "EVALUATION_TARGET_IDENTITY_INVALID",
            {finding["code"] for finding in result["findings"]},
        )

    def test_formal_evaluation_packet_rejects_unpublishable_slot_contract(self) -> None:
        packet = base_packet()
        target = formal_evaluation_target()
        target["slot_h_contract"].pop("file_sha256")
        packet.update(
            {
                "work_kind": "experiment",
                "changes_executable_candidate": False,
                "candidate_root_path": None,
                "candidate_manifest_path": None,
                "evaluation_target": target,
            }
        )
        result = MODULE.validate(packet, "draft")
        self.assertEqual(result["checks"]["result_contract_compatibility"], "FAIL")
        self.assertIn(
            "EVALUATION_TARGET_IDENTITY_INVALID",
            {finding["code"] for finding in result["findings"]},
        )

    def test_evidence_reuse_packet_rejects_new_measurement_or_rerun(self) -> None:
        packet = base_packet()
        target = formal_evaluation_target()
        target["evidence_reuse"] = {
            "source_batch_id": "B035",
            "raw_artifacts": [
                {
                    "path": "artifacts/frontier/B035/dev/raw-results.json",
                    "file_sha256": HASH,
                }
            ],
            "measurement_execution": "allowed",
            "reruns": 1,
            "measurement_semantics": "unchanged",
        }
        packet.update(
            {
                "work_kind": "experiment",
                "changes_executable_candidate": False,
                "candidate_root_path": None,
                "candidate_manifest_path": None,
                "evaluation_target": target,
            }
        )
        result = MODULE.validate(packet, "draft")
        self.assertEqual(result["checks"]["result_contract_compatibility"], "FAIL")
        self.assertIn(
            "EVIDENCE_REUSE_CONTRACT_INVALID",
            {finding["code"] for finding in result["findings"]},
        )

    def test_evidence_reuse_packet_recomputes_raw_artifact_identity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw_path = root / "artifacts/frontier/B035/dev/raw-results.json"
            raw_path.parent.mkdir(parents=True)
            raw_path.write_bytes(b"exact raw evidence")
            packet = base_packet()
            target = formal_evaluation_target()
            seed_evaluation_sources(root, target)
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
            packet.update(
                {
                    "work_kind": "experiment",
                    "changes_executable_candidate": False,
                    "candidate_root_path": None,
                    "candidate_manifest_path": None,
                    "evaluation_target": target,
                }
            )
            seed_identity_sources(root, packet)
            self.assertTrue(MODULE.validate(packet, "draft", root)["packet_structure_ready"])
            target["evidence_reuse"]["raw_artifacts"][0]["file_sha256"] = HASH
            result = MODULE.validate(packet, "draft", root)
            self.assertIn(
                "EVIDENCE_REUSE_SOURCE_IDENTITY_MISMATCH",
                {finding["code"] for finding in result["findings"]},
            )

    def test_forbidden_subtree_catches_worker_output(self) -> None:
        packet = base_packet()
        packet["worker_forbidden_paths"].append("candidates/")
        result = MODULE.validate(packet, "draft")
        self.assertIn("WORKER_FORBIDDEN_OVERLAP", {item["code"] for item in result["findings"]})
        self.assertEqual("block", result["blocking_findings"][0]["effect"])

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
        packet["coordinator_lifecycle_transition"] = lifecycle_contract()
        result = MODULE.validate(packet, "draft")
        self.assertTrue(result["packet_structure_ready"])

    def test_frozen_lifecycle_directory_is_rejected(self) -> None:
        packet = base_packet()
        packet["coordinator_lifecycle_transition"] = lifecycle_contract()
        packet["execution_frozen_inputs"].append(
            {"path": "docs/", "scope": "subtree", "identity": "sha256:example"}
        )
        result = MODULE.validate(packet, "draft")
        self.assertIn("FROZEN_COORDINATOR_OVERLAP", {item["code"] for item in result["findings"]})

    def test_lifecycle_transition_rejects_free_text_diff(self) -> None:
        packet = base_packet()
        transition = lifecycle_contract()
        transition["allowed_field_diff"] = "campaign_status: planned -> running"
        packet["coordinator_lifecycle_transition"] = transition
        result = MODULE.validate(packet, "draft")
        self.assertIn("LIFECYCLE_DIFF_INVALID", {item["code"] for item in result["findings"]})
        self.assertEqual(result["checks"]["lifecycle_transition_contract"], "FAIL")

    def test_lifecycle_transition_rejects_literal_runtime_date(self) -> None:
        packet = base_packet()
        transition = lifecycle_contract()
        transition["allowed_field_diff"]["updated"] = {"to": "2026-08-13"}
        packet["coordinator_lifecycle_transition"] = transition
        result = MODULE.validate(packet, "draft")
        self.assertIn("LIFECYCLE_DIFF_INVALID", {item["code"] for item in result["findings"]})

    def test_lifecycle_transition_rejects_ambiguous_timezone(self) -> None:
        packet = base_packet()
        transition = lifecycle_contract()
        transition["transition_time"]["timezone"] = "local"
        transition["allowed_field_diff"]["updated"]["timezone"] = "local"
        packet["coordinator_lifecycle_transition"] = transition
        result = MODULE.validate(packet, "draft")
        codes = {item["code"] for item in result["findings"]}
        self.assertIn("LIFECYCLE_TIME_RULE_INVALID", codes)
        self.assertIn("LIFECYCLE_DIFF_INVALID", codes)

    def test_lifecycle_transition_rejects_missing_pre_transition_identity(self) -> None:
        packet = base_packet()
        transition = lifecycle_contract()
        transition["precondition"].pop("file_identity")
        packet["coordinator_lifecycle_transition"] = transition
        result = MODULE.validate(packet, "draft")
        self.assertIn(
            "LIFECYCLE_PRECONDITION_INVALID",
            {item["code"] for item in result["findings"]},
        )

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
        packet["execution_frozen_inputs"] = ["current project inputs"]
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
                        "candidates/B900/",
                        "artifacts/frontier/B900/weed-tests.json",
                        "artifacts/frontier/B900/result.yaml",
                        "artifacts/frontier/B900/candidate-manifest.yaml",
                    ],
                }
            )
            packet["design_contract_binding"] = {
                "path": "work/W900/design/traceability.yaml",
                "identity_field": "design_contract_identity",
                "identity": "W900-r1-sha256:example",
                "file_sha256": hashlib.sha256(
                    traceability_path.read_bytes()
                ).hexdigest(),
            }
            seed_identity_sources(root, packet)
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
                        "candidates/B900/",
                        "artifacts/frontier/B900/weed-tests.json",
                        "artifacts/frontier/B900/plant-shape-tests.json",
                        "artifacts/frontier/B900/result.yaml",
                        "artifacts/frontier/B900/candidate-manifest.yaml",
                    ],
                }
            )
            packet["design_contract_binding"] = {
                "path": "work/W900/design/traceability.yaml",
                "identity_field": "design_contract_identity",
                "identity": "W900-r1-sha256:example",
                "file_sha256": hashlib.sha256(
                    traceability_path.read_bytes()
                ).hexdigest(),
            }
            seed_identity_sources(root, packet)
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

    def test_legacy_result_contract_is_read_only_for_new_packets(self) -> None:
        packet = base_packet()
        packet["result_contract_version"] = MODULE.RESULT_CONTRACT_V1
        draft = MODULE.validate(packet, "draft")
        self.assertIn(
            "RESULT_CONTRACT_INVALID",
            {item["code"] for item in draft["findings"]},
        )
        audit = MODULE.validate(packet, "audit")
        self.assertNotIn(
            "RESULT_CONTRACT_INVALID",
            {item["code"] for item in audit["findings"]},
        )


if __name__ == "__main__":
    unittest.main()
