#!/usr/bin/env python3
"""End-to-end Slice 7 workflow composition and contract regressions."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


SCRIPT_ROOT = Path(__file__).parent


def load_module(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPT_ROOT / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


BATCH = load_module("validate_batch_packet")
ENTRY = load_module("validate_entry_packet")
ADOPTION = load_module("validate_authorization_adoption")
BASELINE = load_module("freeze_execution_baseline")
RESULT = load_module("validate_batch_result")
RECOVERY = load_module("validate_candidate_recovery")
PACKAGE = load_module("package_frontier_handoff")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Slice7EndToEndTests(unittest.TestCase):
    def test_materialize_close_recover_and_package_from_persisted_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            source = root / "src/input.txt"
            source.parent.mkdir(parents=True)
            source.write_text("source base\n")

            packet = {
                "packet_path": "artifacts/frontier/B900/packet.yaml",
                "packet_preflight_path": "artifacts/frontier/B900/packet-preflight.json",
                "batch_id": "B900",
                "campaign_generation": 2,
                "route_id": "T900",
                "parallel_set": None,
                "work_kind": "code",
                "problem_epoch": 3,
                "representation_revision": 4,
                "changes_executable_candidate": True,
                "design_profile": "direct",
                "allowed_code_paths": ["candidates/B900-example/"],
                "worker_forbidden_paths": [
                    "artifacts/frontier/B900/packet.yaml",
                    "artifacts/frontier/B900/packet-preflight.json",
                    "artifacts/frontier/B900/execution-baseline/",
                    "artifacts/frontier/B900/execution-start.yaml",
                    "docs/",
                ],
                "execution_frozen_inputs": [
                    {
                        "path": "src/input.txt",
                        "scope": "file",
                        "identity": f"sha256:{sha256_file(source)}",
                    }
                ],
                "coordinator_lifecycle_transition": None,
                "execution_baseline_root": "artifacts/frontier/B900/execution-baseline/",
                "execution_start_path": "artifacts/frontier/B900/execution-start.yaml",
                "candidate_manifest_path": "artifacts/frontier/B900/candidate-manifest.yaml",
                "artifact_paths": [
                    "candidates/B900-example/",
                    "artifacts/frontier/B900/candidate-manifest.yaml",
                    "artifacts/frontier/B900/result-validation.json",
                    "artifacts/frontier/B900/result.yaml",
                ],
                "acknowledgment_path": "artifacts/frontier/B900/acknowledgment.yaml",
                "result_validation_path": "artifacts/frontier/B900/result-validation.json",
                "result_packet_path": "artifacts/frontier/B900/result.yaml",
                "prohibited_actions": ["edit Coordinator outputs or perform measurement"],
            }
            packet_draft = BATCH.validate(packet, "draft", root)
            self.assertTrue(packet_draft["packet_structure_ready"], packet_draft["findings"])
            packet["packet_id"] = packet_draft["computed_packet_id"]
            self.assertTrue(BATCH.validate(packet, "frozen", root)["packet_structure_ready"])

            entry = {
                "review_kind": "entry",
                "review_stage": "authorization-readiness",
                "review_id": "R900",
                "packet_path": "frontier/reviews/entry-R900-packet.yaml",
                "entry_schema_preflight_paths": {
                    "draft": "frontier/reviews/entry-R900-draft.json",
                    "frozen": "frontier/reviews/entry-R900-frozen.json",
                },
                "snapshot_root": "frontier/reviews/entry-R900-snapshot/",
                "snapshot_manifest": "frontier/reviews/entry-R900-snapshot/manifest.yaml",
                "snapshot_id": "entry-R900-sha256:example",
                "task_path": "docs/task",
                "problem_epoch": 3,
                "problem_generated_at": "2026-01-01T00:00:00Z",
                "representation_revision": 4,
                "representation_generated_at": "2026-01-01T00:00:00Z",
                "representation_review_result": "PROCEED_EXPLORATORY",
                "representation_permitted": "bounded scope",
                "campaign_generation": 2,
                "recovery_lineage": {
                    "prior_closeout": "X899",
                    "candidate_recovery_preflight": None,
                    "recovery_authorization": "V899",
                    "disposition": "X900",
                    "inherited_budget": "budget-sha256:example",
                    "reused_identities": ["source-sha256:example"],
                    "implementation_review": "R899",
                },
                "repository_structure_disposition": "existing-integrated",
                "repository_layout_approval": None,
                "design_gate": "direct profile evidence",
                "dispatch_contract": packet["packet_id"],
                "authorization_target": {
                    "target_id": "authorization-target-sha256:example",
                    "batch_id": "B900",
                    "packet_path": packet["packet_path"],
                    "packet_id": packet["packet_id"],
                    "preflight_id": packet_draft["preflight_id"],
                    "design_contract_identity": None,
                    "source_base_identity": "source-sha256:example",
                    "scope": "one direct materialization",
                    "maximum_spend": "one proposal attempt",
                    "stop_boundary": "materialized-stopped",
                    "result_path": "artifacts/frontier/V900-result.yaml",
                    "proposed_state_transition": {
                        "budget": "reserve B900",
                        "selection": "B900 Primary",
                        "lifecycle": "FIRST_BATCH_PLANNED",
                    },
                },
                "authorization_state": "pending",
                "authorization_adoption_path": "frontier/reviews/entry-R900-adoption.yaml",
                "authorization_adoption_preflight_path": "frontier/reviews/entry-R900-adoption.json",
                "selected_batches": ["B900"],
                "actual_spend": "zero",
                "snapshot_inputs": "frontier/reviews/entry-R900-snapshot/manifest.yaml#inputs",
                "assigned_review_path": "frontier/reviews/entry-R900.md",
                "completion_check": "full authorization readiness",
            }
            entry_result = ENTRY.validate(entry, "frozen")
            entry["packet_id"] = entry_result["computed_packet_id"]
            self.assertTrue(ENTRY.validate(entry, "frozen")["entry_schema_ready"])

            adoption = {
                "adoption_path": "frontier/reviews/entry-R900-adoption.yaml",
                "entry_packet_id": entry["packet_id"],
                "readiness_review": {
                    "review_id": "R900",
                    "review_result": "AUTHORIZATION_READY",
                    "review_artifact": "frontier/reviews/entry-R900.md",
                    "review_artifact_identity": "sha256:review",
                    "snapshot_id": entry["snapshot_id"],
                    "entry_packet_id": entry["packet_id"],
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
                        "reviewed_identity": packet["packet_id"],
                        "observed_identity": packet["packet_id"],
                        "status": "matched",
                    }
                ],
                "answer_fidelity": "exact authorize",
                "reviewed_state_transition": "reserve B900 and select it",
                "entry_result": "ENTRY_READY",
                "maximum_consequence": "dispatch exact B900",
            }
            adoption_result = ADOPTION.validate(adoption, "draft")
            self.assertTrue(adoption_result["authorization_adoption_valid"])

            start_draft = {
                "execution_start_path": packet["execution_start_path"],
                "packet_path": packet["packet_path"],
                "packet_id": packet["packet_id"],
                "batch_id": "B900",
                "campaign_generation": 2,
                "recorded_by": "frontier-optimization/1",
                "recorded_at": "2026-08-12T08:00:00Z",
                "lifecycle_transition": None,
                "post_transition_baseline": packet["execution_frozen_inputs"],
                "unchanged_authority_check": "matched",
                "worker_may_start": "yes",
                "blocker": None,
            }
            start_draft_path = root / "start-draft.yaml"
            start_draft_path.write_text(yaml.safe_dump(start_draft, sort_keys=False))
            start_path = root / packet["execution_start_path"]
            BASELINE.freeze(start_draft_path, packet["execution_baseline_root"], start_path, root)
            self.assertTrue(BASELINE.verify(start_path, root, True)["snapshot_verified"])

            candidate = root / "candidates/B900-example"
            candidate.mkdir(parents=True)
            (candidate / "main.py").write_text("def agent(observation, configuration):\n    return {}\n")
            members, package_sha256 = RECOVERY.package_inventory(candidate)
            candidate_id = f"B900-example-sha256:{package_sha256}"
            manifest = {
                "candidate_id": candidate_id,
                "campaign_generation": 2,
                "candidate_interface": "main.py agent(observation, configuration)",
                "source_base_identity": "source-sha256:example",
                "source_result_identity": {"package_sha256": package_sha256},
                "code_paths": [
                    {"path": item["path"], "sha256": item["sha256"]} for item in members
                ],
                "resolved_configuration": None,
                "dependency_identity": "explicit-none",
                "runtime_factors": ["deterministic=true"],
                "generated_assets": [],
            }
            manifest_path = root / packet["candidate_manifest_path"]
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False))

            result = {
                "result_packet_path": packet["result_packet_path"],
                "packet_path": packet["packet_path"],
                "packet_id": packet["packet_id"],
                "packet_preflight": packet_draft["preflight_id"],
                "acknowledgment": "B900-acknowledgment-sha256:example",
                "execution_start": yaml.safe_load(start_path.read_text())["execution_start_id"],
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
                "accounting_evidence": candidate_id,
                "artifacts": [packet["candidate_manifest_path"]],
                "work_plan": None,
                "design_review": None,
                "development_authorization": "V900",
                "design_inputs_used": [],
                "source_base_identity": "source-sha256:example",
                "source_result_identity": {"package_sha256": package_sha256},
                "changed_paths": ["candidates/B900-example/main.py"],
                "candidate_manifest": packet["candidate_manifest_path"],
                "candidate_identity": candidate_id,
                "experiment_identity": None,
                "resolved_configuration_identity": None,
                "dependency_identity": "explicit-none",
                "implementation_review_state": "pending",
                "materialization_state": "materialized-stopped",
                "performance_evaluation_state": "not-authorized",
                "integration_state": "not-authorized",
                "work_plan_progress": None,
                "design_change_proposals": [],
                "recovery_point": "candidate, manifest, and execution baseline",
                "human_input_state": "not-applicable",
                "human_input_artifacts": [],
                "human_input_validation": [],
                "human_input_evidence_limit": "not applicable",
                "engineering_validation": [{"check": "unit", "result": "pass"}],
                "implementation_definition_of_done": "met",
                "results": [],
                "observed_vs_expected": "matched",
                "decision_relevant_surprises": [],
                "failed_checks": [],
                "new_prerequisites": ["fresh implementation review"],
                "possible_follow_up": None,
                "scope_deviation": "None",
            }
            result_packet = {
                key: packet[key]
                for key in (
                    "packet_path",
                    "packet_id",
                    "batch_id",
                    "campaign_generation",
                    "route_id",
                    "parallel_set",
                    "work_kind",
                    "problem_epoch",
                    "representation_revision",
                    "changes_executable_candidate",
                    "result_packet_path",
                )
            }
            result_validation = RESULT.validate(result, "draft", result_packet)
            self.assertTrue(result_validation["result_structure_ready"], result_validation["findings"])
            result["result_packet_id"] = result_validation["computed_result_packet_id"]
            self.assertTrue(RESULT.validate(result, "frozen", result_packet)["result_structure_ready"])
            result_path = root / packet["result_packet_path"]
            result_path.write_text(yaml.safe_dump(result, sort_keys=False))

            closeout = root / "docs/task/log.md"
            closeout.parent.mkdir(parents=True)
            closeout.write_text("CLOSEOUT_COMPLETE generation 2; spend 1; no authority\n")
            recovery = {
                "recovery_preflight_path": "artifacts/frontier/recovery/G003/B900.yaml",
                "prior_campaign_generation": 2,
                "campaign_generation": 3,
                "prior_closeout": {
                    "event": "CLOSEOUT_COMPLETE",
                    "campaign_generation": 2,
                    "campaign_status": "halted",
                    "closeout_identity": "X900-sha256:example",
                    "final_handoff_identity": f"sha256:{sha256_file(closeout)}",
                    "unresolved_claims": [],
                    "active_workers": [],
                },
                "inherited_budget": {
                    "proposal_attempt_ceiling": 20,
                    "actual_spend": 1,
                    "unknown_spend": 0,
                    "active_reservations": [],
                    "budget_identity": "budget-sha256:example",
                },
                "candidate_root": "candidates/B900-example/",
                "candidate_manifest_path": packet["candidate_manifest_path"],
                "requested_candidate_id": candidate_id,
                "requested_manifest_sha256": sha256_file(manifest_path),
                "review_mode": "recovery-reuse",
                "candidate_mutation": "prohibited",
                "new_proposal_attempts": 0,
            }
            recovery_result = RECOVERY.validate(recovery, "draft", root)
            self.assertTrue(recovery_result["recovery_ready"], recovery_result["findings"])

            package_plan = {
                "package_plan_path": "artifacts/frontier/packages/G002/plan.yaml",
                "campaign_generation": 2,
                "campaign_status": "halted",
                "closeout_identity": "X900-sha256:example",
                "final_handoff_identity": f"sha256:{sha256_file(closeout)}",
                "final_budget_identity": "budget-sha256:example",
                "authority_effect": "none",
                "entries": [
                    {
                        "source": "docs/task/log.md",
                        "scope": "file",
                        "identity": f"sha256:{sha256_file(closeout)}",
                        "destination": "task/log.md",
                        "role": "final-handoff",
                    },
                    {
                        "source": packet["candidate_manifest_path"],
                        "scope": "file",
                        "identity": f"sha256:{sha256_file(manifest_path)}",
                        "destination": "candidate/candidate-manifest.yaml",
                        "role": "candidate-manifest",
                    },
                    {
                        "source": "candidates/B900-example/",
                        "scope": "subtree",
                        "identity": f"sha256:{RECOVERY.package_inventory(candidate)[1]}",
                        "destination": "candidate/bytes",
                        "role": "candidate-bytes",
                    },
                ],
            }
            package_draft = PACKAGE.validate_plan(package_plan, "draft", root)
            self.assertTrue(package_draft["package_ready"], package_draft["findings"])
            package_plan["package_id"] = package_draft["computed_package_id"]
            plan_path = root / "package-plan.yaml"
            plan_path.write_text(yaml.safe_dump(package_plan, sort_keys=False))
            package_root = PACKAGE.build(plan_path, root / "packages", root)
            source.write_text("live state changed after closeout\n")
            self.assertTrue(PACKAGE.verify(package_root)["package_verified"])


class Slice7ContractTests(unittest.TestCase):
    def assert_contract_contains(self, relative: str, *fragments: str) -> None:
        text = (SCRIPT_ROOT.parent / "references" / relative).read_text()
        for fragment in fragments:
            with self.subTest(reference=relative, fragment=fragment):
                self.assertIn(fragment, text)

    def test_single_route_and_noncode_w_exceptions(self) -> None:
        self.assert_contract_contains(
            "entry-and-planning.md",
            "Create no fake alternative T",
            "request no campaign-baseline tradeoff V",
            "A complex non-code W uses one reasoned `not applicable` Design-map row",
        )

    def test_progressive_design_and_candidate_measurement_boundary(self) -> None:
        self.assert_contract_contains(
            "campaign-cycle.md",
            "Do not reload `technical-design.md` to execute a `ready` design",
            "without adopted unchanged `IMPLEMENTATION_READY` cannot be selected for evaluation",
        )

    def test_reflection_claim_and_parent_change_routes(self) -> None:
        self.assert_contract_contains(
            "learning-loop.md",
            "For routine evidence",
            "For diagnostic evidence",
            "For strategic evidence",
            "REPLAN_READY",
        )
        self.assert_contract_contains(
            "closeout-and-claims.md",
            "do not starve the campaign",
            "A withdrawing X likewise blocks only that wording",
        )
        self.assert_contract_contains(
            "frontier-core.md",
            "pre-spend parent-rebind",
            "forced closeout",
        )

    def test_recovery_never_uses_conversation_or_git_history(self) -> None:
        self.assert_contract_contains(
            "frontier-core.md",
            "not conversation or Git history",
            "run the bound candidate-recovery validator",
        )
        self.assert_contract_contains(
            "packaging-and-recovery.md",
            "without repository `.git` data, conversation history",
            "same package bytes must produce the same handoff and next router result",
        )

    def test_parent_change_uses_a_new_immutable_fixture_identity(self) -> None:
        fixtures = SCRIPT_ROOT / "fixtures/slice7"
        old_path = fixtures / "parent-v1.yaml"
        new_path = fixtures / "parent-v2.yaml"
        old_before = old_path.read_bytes()
        old_identity = hashlib.sha256(old_before).hexdigest()
        new_identity = hashlib.sha256(new_path.read_bytes()).hexdigest()
        self.assertNotEqual(old_identity, new_identity)
        self.assertEqual(old_path.read_bytes(), old_before)
        old = yaml.safe_load(old_before)
        new = yaml.safe_load(new_path.read_bytes())
        self.assertEqual(new["replacement_for"], "parent-v1")
        self.assertEqual(old["representation_revision"] + 1, new["representation_revision"])

    def test_acceptance_matrix_names_every_slice7_boundary(self) -> None:
        matrix = yaml.safe_load(
            (SCRIPT_ROOT / "fixtures/slice7/scenarios.yaml").read_bytes()
        )
        scenario_ids = {item["id"] for item in matrix["scenarios"]}
        self.assertEqual(len(scenario_ids), 21)
        self.assertIn("candidate-recovery-identity-mismatch", scenario_ids)
        self.assertIn("post-closeout-package", scenario_ids)
        self.assertIn("compacted-context", scenario_ids)


if __name__ == "__main__":
    unittest.main()
