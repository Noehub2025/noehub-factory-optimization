#!/usr/bin/env python3
"""End-to-end Slice 7 workflow composition and contract regressions."""

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

from test_validate_entry_packet import write_workflow_source_binding


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
CANDIDATE_PACKAGE = load_module("validate_candidate_package")
PROJECT_SNAPSHOT = load_module("project_snapshot")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def file_binding(
    root: Path, path: Path, identity_field: str | None, identity: str
) -> dict:
    return {
        "path": path.relative_to(root).as_posix(),
        "identity_field": identity_field,
        "identity": identity,
        "file_sha256": sha256_file(path),
    }


class Slice7EndToEndTests(unittest.TestCase):
    def test_materialize_close_recover_and_package_from_persisted_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            source = root / "src/input.txt"
            source.parent.mkdir(parents=True)
            source.write_text("source base\n")
            source_identity = f"sha256:{sha256_file(source)}"
            workflow_source_binding = write_workflow_source_binding(root)
            campaign_state = root / "docs/task/frontier/ledger.md"
            campaign_state.parent.mkdir(parents=True)
            campaign_state.write_text("status: planned\n")
            proposed_campaign_state = root / "artifacts/frontier/B900/proposed-campaign-state.md"
            proposed_campaign_state.parent.mkdir(parents=True)
            proposed_campaign_state.write_text("status: running\n")
            pre_current_state = {
                "campaign_generation": 2,
                "campaign_status": "running",
                "primary_batch": None,
                "parallel_batches": [],
                "decision_id": "V900",
                "authorization_state": "pending",
                "execution_batch": "B900",
                "execution_state": "not-authorized",
            }
            post_current_state = {
                **pre_current_state,
                "primary_batch": "B900",
                "authorization_state": "adopted",
                "execution_state": "awaiting-acknowledgment",
            }

            def frontier_bytes(state: dict) -> bytes:
                return (
                    b"---\n"
                    + yaml.safe_dump(
                        {
                            "campaign_generation": state["campaign_generation"],
                            "campaign_status": state["campaign_status"],
                            "current_state": state,
                        },
                        sort_keys=False,
                    ).encode()
                    + b"---\n\n# FRONTIER\n"
                )

            frontier_state = root / "docs/task/FRONTIER.md"
            frontier_state.write_bytes(frontier_bytes(pre_current_state))
            proposed_frontier_state = root / "artifacts/frontier/B900/proposed-FRONTIER.md"
            proposed_frontier_state.write_bytes(frontier_bytes(post_current_state))
            proposed_transition = {
                "budget": "reserve B900",
                "selection": "B900 Primary",
                "lifecycle": "FIRST_BATCH_PLANNED",
            }
            direct_identity = f"sha256:{sha256_file(source)}"
            source_base_identity = direct_identity
            target_scope = "one direct materialization"
            target_spend = "one proposal attempt"
            target_stop = "materialized-stopped"
            target_result_path = "artifacts/frontier/B900/result.yaml"
            user_result_path = "artifacts/frontier/V900-result.yaml"
            post_adoption_paths = [
                "docs/task/FRONTIER.md",
                "docs/task/frontier/ledger.md",
            ]
            decision_record_path = "docs/task/frontier/ledger.md"
            authorization_question = "Authorize exactly the reviewed B900 materialization?"
            authorize_consequence = "dispatch exact B900"
            decline_consequence = "keep B900 undispatched"
            conditional_consequence = "require a fresh target and Entry review"
            target_spec_payload = {
                "contract_version": "frontier-authorization-target-specification/1",
                "decision_id": "V900",
                "batch_id": "B900",
                "target_path": "artifacts/frontier/V900-target.yaml",
                "user_result_path": user_result_path,
                "decision_record_path": decision_record_path,
                "design_contract_identity": direct_identity,
                "source_base_identity": source_base_identity,
                "scope": target_scope,
                "maximum_spend": target_spend,
                "stop_boundary": target_stop,
                "result_path": target_result_path,
                "proposed_state_transition": proposed_transition,
                "post_adoption_paths": post_adoption_paths,
                "authorization_question": authorization_question,
                "authorize_consequence": authorize_consequence,
                "decline_consequence": decline_consequence,
                "conditional_consequence": conditional_consequence,
            }
            target_spec_payload_raw = yaml.safe_dump(
                target_spec_payload, sort_keys=False
            ).encode()
            target_spec_id = (
                "V900-target-spec-sha256:"
                + hashlib.sha256(target_spec_payload_raw).hexdigest()
            )
            target_spec_path = root / "artifacts/frontier/V900-target-spec.yaml"
            target_spec_path.write_bytes(
                f"target_spec_id: {target_spec_id}\n".encode()
                + target_spec_payload_raw
            )
            target_specification = {
                "contract_version": "frontier-authorization-target-specification/1",
                "path": "artifacts/frontier/V900-target-spec.yaml",
                "identity_field": "target_spec_id",
                "identity": target_spec_id,
                "file_sha256": sha256_file(target_spec_path),
            }

            packet = {
                "packet_path": "artifacts/frontier/B900/packet.yaml",
                "packet_preflight_path": "artifacts/frontier/B900/packet-preflight.json",
                "task_path": "docs/task",
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
                "identity_contract": BATCH.IDENTITY_CONTRACT,
                "result_contract_version": BATCH.RESULT_CONTRACT_V2,
                "workflow_source_binding": copy.deepcopy(workflow_source_binding),
                "workflow_source_identity": workflow_source_binding["source_snapshot"]["identity"],
                "worker_source_member": "workers/run-frontier-batch/SKILL.md",
                "design_profile": "direct",
                "design_contract_identity": source_identity,
                "design_contract_binding": {
                    "path": "src/input.txt",
                    "identity_field": None,
                    "identity": source_identity,
                    "file_sha256": sha256_file(source),
                },
                "development_authorization_target": target_specification,
                "source_base_identity": source_identity,
                "source_base_binding": {
                    "path": "src/input.txt",
                    "identity_field": None,
                    "identity": source_identity,
                    "file_sha256": sha256_file(source),
                },
                "maximum_spend": "one proposal attempt",
                "authorization_gate": "finding-free Entry adoption",
                "authorization_boundary": {
                    "scope": "one direct materialization",
                    "maximum_spend": "one proposal attempt",
                    "stop_boundary": "materialized-stopped",
                    "result_path": "artifacts/frontier/B900/result.yaml",
                },
                "stop_conditions": ["stop after materialization"],
                "forced_halts": [],
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
                "candidate_root_path": "candidates/B900-example/",
                "candidate_package_inventory_path": "artifacts/frontier/B900/package-inventory.yaml",
                "candidate_manifest_path": "artifacts/frontier/B900/candidate-manifest.yaml",
                "engineering_check_plan": {
                    "contract_version": BATCH.ENGINEERING_CHECK_PLAN_CONTRACT,
                    "checks": [
                        {
                            "id": "bounded-unit-check",
                            "command": ["python", "-m", "unittest", "tests.test_unit"],
                            "selection": "exact",
                            "selected_units": ["tests.test_unit"],
                            "declared_effects": ["local-code-execution"],
                            "effect_costs": {"local-code-execution": 1},
                            "effect_evidence": [
                                {
                                    "path": "src/input.txt",
                                    "file_sha256": sha256_file(source),
                                }
                            ],
                        }
                    ],
                    "effect_limits": {"local-code-execution": 1},
                    "evidence_use": "engineering-only",
                },
                "publication_policy": {
                    "contract_version": BATCH.PUBLICATION_POLICY_CONTRACT,
                    "charge_event": BATCH.FIRST_IDENTITY_CHARGE,
                    "charge_amount": "1 proposal attempt",
                    "charge_basis": {
                        "kind": "parent-rule",
                        "path": "src/input.txt",
                        "file_sha256": sha256_file(source),
                        "locator": "fixture parent charges first candidate identity",
                    },
                    "repair_mode": "prohibited",
                    "effect_scope": "deterministic-local-checks-only",
                    "authoritative_output_path": "artifacts/frontier/B900/package-inventory.yaml",
                    "engineering_evidence_path": "artifacts/frontier/B900/engineering/evidence.json",
                },
                "artifact_paths": [
                    "candidates/B900-example/",
                    "artifacts/frontier/B900/package-inventory.yaml",
                    "artifacts/frontier/B900/candidate-manifest.yaml",
                    "artifacts/frontier/B900/engineering/",
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
            live_packet_path = root / packet["packet_path"]
            live_packet_path.parent.mkdir(parents=True, exist_ok=True)
            live_packet_path.write_text(yaml.safe_dump(packet, sort_keys=False))
            live_preflight_path = root / packet["packet_preflight_path"]
            live_preflight_path.write_text(
                json.dumps(packet_draft, indent=2, sort_keys=True) + "\n"
            )

            post_adoption_state = {
                "contract_version": "frontier-post-adoption-state/1",
                "files": [
                    {
                        "path": "docs/task/FRONTIER.md",
                        "pre_sha256": sha256_file(frontier_state),
                        "post_source": {
                            "path": "artifacts/frontier/B900/proposed-FRONTIER.md",
                            "file_sha256": sha256_file(proposed_frontier_state),
                        },
                    },
                    {
                        "path": "docs/task/frontier/ledger.md",
                        "pre_sha256": sha256_file(campaign_state),
                        "post_source": {
                            "path": "artifacts/frontier/B900/proposed-campaign-state.md",
                            "file_sha256": sha256_file(proposed_campaign_state),
                        },
                    }
                ],
            }

            entry_reviewed_bindings = [
                {
                    "role": "direct_profile",
                    "path": "src/input.txt",
                    "identity": direct_identity,
                    "identity_field": None,
                    "file_sha256": sha256_file(source),
                    "batch_scoped": False,
                },
                {
                    "role": "source_base",
                    "path": "src/input.txt",
                    "identity": source_base_identity,
                    "identity_field": None,
                    "file_sha256": sha256_file(source),
                    "batch_scoped": False,
                },
            ]

            target_payload = {
                "identity_rule": "exact UTF-8 bytes with the complete target_id line omitted",
                "decision_id": "V900",
                "target_specification": target_specification,
                "batch_id": "B900",
                "preflight_id": packet_draft["preflight_id"],
                "design_contract_identity": direct_identity,
                "source_base_identity": source_base_identity,
                "scope": target_scope,
                "maximum_spend": target_spend,
                "stop_boundary": target_stop,
                "result_path": target_result_path,
                "user_result_path": user_result_path,
                "decision_record_path": decision_record_path,
                "proposed_state_transition": proposed_transition,
                "post_adoption_state": post_adoption_state,
                "post_adoption_paths": post_adoption_paths,
                "authorization_question": authorization_question,
                "exact_object": {
                    "batch_id": "B900",
                    "packet": {
                        "path": packet["packet_path"],
                        "packet_id": packet["packet_id"],
                        "file_sha256": sha256_file(live_packet_path),
                    },
                    "structural_preflight": {
                        "path": packet["packet_preflight_path"],
                        "preflight_id": packet_draft["preflight_id"],
                        "file_sha256": sha256_file(live_preflight_path),
                    },
                    "reviewed_bindings": entry_reviewed_bindings,
                },
                "authorize_consequence": authorize_consequence,
                "decline_consequence": decline_consequence,
                "conditional_consequence": conditional_consequence,
            }
            target_payload_raw = yaml.safe_dump(target_payload, sort_keys=False).encode()
            target_id = f"V900-target-sha256:{hashlib.sha256(target_payload_raw).hexdigest()}"
            target_path = root / "artifacts/frontier/V900-target.yaml"
            target_path.write_bytes(f"target_id: {target_id}\n".encode() + target_payload_raw)

            entry = {
                "review_kind": "entry",
                "review_stage": "authorization-readiness",
                "review_id": "R900",
                "packet_path": "frontier/reviews/entry-R900-packet.yaml",
                "entry_schema_preflight_paths": {
                    "draft": "frontier/reviews/entry-R900-draft.json",
                    "frozen": "frontier/reviews/entry-R900-frozen.json",
                },
                "snapshot_manifest": None,
                "snapshot_id": None,
                "task_path": "docs/task",
                "problem_epoch": 3,
                "problem_generated_at": "2026-01-01T00:00:00Z",
                "representation_revision": 4,
                "representation_generated_at": "2026-01-01T00:00:00Z",
                "representation_review_result": "PROCEED_EXPLORATORY",
                "representation_permitted": "bounded scope",
                "workflow_source_binding": workflow_source_binding,
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
                "design_gate": {
                    "mode": "direct",
                    "bindings": entry_reviewed_bindings,
                },
                "dispatch_contract": {
                    "batch_id": "B900",
                    "packet_path": packet["packet_path"],
                    "packet_id": packet["packet_id"],
                    "preflight_path": packet["packet_preflight_path"],
                    "preflight_id": packet_draft["preflight_id"],
                    "preflight_file_sha256": sha256_file(live_preflight_path),
                    "design_contract_identity": direct_identity,
                    "source_base_identity": source_base_identity,
                    "scope": target_scope,
                    "maximum_spend": target_spend,
                    "stop_boundary": target_stop,
                    "result_path": target_result_path,
                },
                "authorization_target": {
                    "target_path": "artifacts/frontier/V900-target.yaml",
                    "target_id": target_id,
                    "target_file_sha256": sha256_file(target_path),
                    "batch_id": "B900",
                    "decision_id": "V900",
                    "target_specification": target_specification,
                    "packet_path": packet["packet_path"],
                    "packet_id": packet["packet_id"],
                    "preflight_id": packet_draft["preflight_id"],
                    "design_contract_identity": direct_identity,
                    "source_base_identity": source_base_identity,
                    "scope": target_scope,
                    "maximum_spend": target_spend,
                    "stop_boundary": target_stop,
                    "result_path": target_result_path,
                    "user_result_path": user_result_path,
                    "decision_record_path": decision_record_path,
                    "proposed_state_transition": proposed_transition,
                    "post_adoption_state": post_adoption_state,
                    "post_adoption_paths": post_adoption_paths,
                    "authorization_question": authorization_question,
                    "authorize_consequence": authorize_consequence,
                    "decline_consequence": decline_consequence,
                    "conditional_consequence": conditional_consequence,
                },
                "authorization_state": "pending",
                "campaign_state_projection": {
                    "contract_version": ENTRY.CAMPAIGN_STATE_PROJECTION_CONTRACT,
                    "live_path": "docs/task/FRONTIER.md",
                    "post_source_path": "artifacts/frontier/B900/proposed-FRONTIER.md",
                    "pre": pre_current_state,
                    "post": post_current_state,
                },
                "authorization_adoption_path": "frontier/reviews/entry-R900-adoption.yaml",
                "authorization_adoption_preflight_path": "frontier/reviews/entry-R900-adoption.json",
                "selected_batches": ["B900"],
                "actual_spend": "zero",
                "assigned_review_path": "frontier/reviews/entry-R900.md",
                "completion_check": "full authorization readiness",
            }
            project_paths = [
                "src/input.txt",
                packet["packet_path"],
                packet["packet_preflight_path"],
                "artifacts/frontier/V900-target-spec.yaml",
                "artifacts/frontier/V900-target.yaml",
                "docs/task/FRONTIER.md",
                "docs/task/frontier/ledger.md",
                "artifacts/frontier/B900/proposed-FRONTIER.md",
                "artifacts/frontier/B900/proposed-campaign-state.md",
            ]
            snapshot_manifest_relative = "frontier/reviews/entry-R900-project-snapshot.yaml"
            snapshot_manifest_path = root / snapshot_manifest_relative
            snapshot_manifest = PROJECT_SNAPSHOT.capture(
                root,
                manifest_path=snapshot_manifest_path,
                paths=project_paths,
                created_at="2026-08-16T00:00:00Z",
            )
            entry["snapshot_id"] = snapshot_manifest["snapshot_id"]
            entry["snapshot_manifest"] = {
                "path": snapshot_manifest_relative,
                "snapshot_id": entry["snapshot_id"],
                "file_sha256": sha256_file(snapshot_manifest_path),
            }
            entry_result = ENTRY.validate(entry, "frozen", root)
            entry["packet_id"] = entry_result["computed_packet_id"]
            frozen_entry = ENTRY.validate(entry, "frozen", root)
            self.assertTrue(frozen_entry["entry_schema_ready"], frozen_entry["findings"])

            live_entry_path = root / entry["packet_path"]
            live_entry_path.parent.mkdir(parents=True, exist_ok=True)
            live_entry_path.write_text(yaml.safe_dump(entry, sort_keys=False))
            review_path = root / entry["assigned_review_path"]
            review_path.write_text(
                "---\n"
                "review_id: R900\n"
                "review_result: AUTHORIZATION_READY\n"
                f"packet_id: {entry['packet_id']}\n"
                f"snapshot_id: {entry['snapshot_id']}\n"
                "---\n\n# Review\n"
            )
            user_result_file = root / user_result_path
            user_result_file.parent.mkdir(parents=True, exist_ok=True)
            user_result_payload = {
                "target_id": target_id,
                "answer": "authorize",
                "conditions": [],
            }
            user_result_payload_raw = yaml.safe_dump(
                user_result_payload, sort_keys=False
            ).encode()
            user_result_id = (
                "V900-result-sha256:"
                + hashlib.sha256(user_result_payload_raw).hexdigest()
            )
            user_result_file.write_bytes(
                f"result_id: {user_result_id}\n".encode()
                + user_result_payload_raw
            )

            adoption = {
                "adoption_path": "frontier/reviews/entry-R900-adoption.yaml",
                "entry_packet": {
                    "path": entry["packet_path"],
                    "packet_id": entry["packet_id"],
                    "file_sha256": sha256_file(live_entry_path),
                },
                "workflow_source_binding": copy.deepcopy(workflow_source_binding),
                "readiness_review": {
                    "review_id": "R900",
                    "review_result": "AUTHORIZATION_READY",
                    "review_artifact": "frontier/reviews/entry-R900.md",
                    "review_artifact_identity": f"sha256:{sha256_file(review_path)}",
                    "snapshot_id": entry["snapshot_id"],
                    "entry_packet_id": entry["packet_id"],
                },
                "authorization_target": {
                    "path": "artifacts/frontier/V900-target.yaml",
                    "target_id": target_id,
                    "file_sha256": sha256_file(target_path),
                    "batch_id": "B900",
                    "packet_id": packet["packet_id"],
                },
                "user_result": {
                    "path": user_result_path,
                    "identity": user_result_id,
                    "identity_field": "result_id",
                    "file_sha256": sha256_file(user_result_file),
                    "target_id": target_id,
                    "answer": "authorize",
                },
                "adopted_v": {
                    "decision_id": "V900",
                    "record_path": decision_record_path,
                    "result_path": user_result_path,
                    "result_identity": user_result_id,
                    "target_id": target_id,
                },
                "answer_fidelity": "exact authorize",
                "reviewed_state_transition": proposed_transition,
                "entry_result": "ENTRY_READY",
                "maximum_consequence": "dispatch exact B900",
            }
            adoption_result = ADOPTION.validate(adoption, "draft", root)
            self.assertTrue(adoption_result["authorization_adoption_valid"])
            adoption["adoption_id"] = adoption_result["computed_adoption_id"]
            adoption_path = root / adoption["adoption_path"]
            adoption_path.write_text(yaml.safe_dump(adoption, sort_keys=False))
            adoption_validation = ADOPTION.validate(adoption, "frozen", root)
            self.assertTrue(adoption_validation["authorization_adoption_valid"])
            adoption_validation_path = root / "frontier/reviews/entry-R900-adoption.json"
            adoption_validation_path.write_text(
                json.dumps(adoption_validation, indent=2, sort_keys=True) + "\n"
            )
            frontier_state.write_bytes(proposed_frontier_state.read_bytes())
            campaign_state.write_bytes(proposed_campaign_state.read_bytes())
            acknowledgment = {
                "batch_id": "B900",
                "packet_id": packet["packet_id"],
                "workflow_source_identity": workflow_source_binding["source_snapshot"]["identity"],
                "packet_preflight_id": packet_draft["preflight_id"],
                "authority_id": adoption["adoption_id"],
                "authority_validation_id": adoption_validation["validation_id"],
                "acknowledgment": "accepted",
            }
            acknowledgment["acknowledgment_id"] = BASELINE.compute_acknowledgment_id(
                acknowledgment
            )
            acknowledgment_path = root / packet["acknowledgment_path"]
            acknowledgment_path.write_text(yaml.safe_dump(acknowledgment, sort_keys=False))

            start_draft = {
                "execution_start_path": packet["execution_start_path"],
                "packet_path": packet["packet_path"],
                "packet_id": packet["packet_id"],
                "workflow_source_identity": workflow_source_binding["source_snapshot"]["identity"],
                "packet_preflight": file_binding(
                    root,
                    live_preflight_path,
                    "preflight_id",
                    packet_draft["preflight_id"],
                ),
                "execution_authority": {
                    "mode": "authorization-adoption",
                    "record": file_binding(
                        root, adoption_path, "adoption_id", adoption["adoption_id"]
                    ),
                    "validation": file_binding(
                        root,
                        adoption_validation_path,
                        "validation_id",
                        adoption_validation["validation_id"],
                    ),
                },
                "acknowledgment": file_binding(
                    root,
                    acknowledgment_path,
                    "acknowledgment_id",
                    acknowledgment["acknowledgment_id"],
                ),
                "batch_id": "B900",
                "campaign_generation": 2,
                "recorded_by": "frontier-optimization/1",
                "recorded_at": "2026-08-12T08:00:00Z",
                "lifecycle_transition": None,
                "post_adoption_state": {
                    "contract_version": "frontier-post-adoption-state/1",
                    "target_id": target_id,
                    "adoption_id": adoption["adoption_id"],
                    "user_result_id": user_result_id,
                    "files": [
                        {
                            "path": "docs/task/FRONTIER.md",
                            "pre_sha256": post_adoption_state["files"][0]["pre_sha256"],
                            "post_sha256": sha256_file(frontier_state),
                        },
                        {
                            "path": "docs/task/frontier/ledger.md",
                            "pre_sha256": post_adoption_state["files"][1]["pre_sha256"],
                            "post_sha256": sha256_file(campaign_state),
                        }
                    ],
                },
                "post_transition_baseline": packet["execution_frozen_inputs"]
                + [
                    {
                        "path": "docs/task/FRONTIER.md",
                        "scope": "file",
                        "identity": f"sha256:{sha256_file(frontier_state)}",
                    },
                    {
                        "path": "docs/task/frontier/ledger.md",
                        "scope": "file",
                        "identity": f"sha256:{sha256_file(campaign_state)}",
                    }
                ],
                "unchanged_authority_check": "matched",
                "worker_may_start": "yes",
                "blocker": None,
            }
            start_draft_path = root / "start-draft.yaml"
            start_draft_path.write_text(yaml.safe_dump(start_draft, sort_keys=False))
            rollout = root / ".frontier/provenance-rollout.yaml"
            rollout.parent.mkdir(parents=True, exist_ok=True)
            rollout.write_text(
                yaml.safe_dump(
                    {
                        "contract_version": "frontier-v1-completion-inventory/1",
                        "rollout_cutoff": "2026-08-17T00:00:00Z",
                        "active_authorities": [
                            {
                                "authority_root": adoption["adoption_id"],
                                "contract_version": packet["identity_contract"],
                                "state": "acknowledged",
                                "scope_root": packet["packet_id"],
                            }
                        ],
                    },
                    sort_keys=False,
                )
            )
            start_path = root / packet["execution_start_path"]
            BASELINE.freeze(start_draft_path, packet["execution_baseline_root"], start_path, root)
            self.assertTrue(BASELINE.verify(start_path, root, True)["snapshot_verified"])

            candidate = root / "candidates/B900-example"
            candidate.mkdir(parents=True)
            (candidate / "main.py").write_text("def agent(observation, configuration):\n    return {}\n")
            members, package_sha256 = RECOVERY.package_inventory(candidate)
            candidate_id = f"B900-example-sha256:{package_sha256}"
            inventory = CANDIDATE_PACKAGE.write_candidate_inventory(
                root,
                packet["candidate_root_path"],
                packet["candidate_package_inventory_path"],
                candidate_id,
            )
            engineering_path = root / "artifacts/frontier/B900/engineering/evidence.json"
            engineering_path.parent.mkdir(parents=True, exist_ok=True)
            engineering_path.write_text(
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
            implementation_review_path = (
                root / "artifacts/frontier/B900/implementation-review.md"
            )
            implementation_review_path.write_text(
                "---\n"
                "type: Optimization Frontier Implementation Review\n"
                "status: complete\n"
                "review_result: IMPLEMENTATION_READY\n"
                f"candidate_id: {candidate_id}\n"
                "---\n\n"
                f"Candidate: {candidate_id}\n"
            )
            manifest = {
                "manifest_contract": CANDIDATE_PACKAGE.FINAL_MANIFEST_CONTRACT,
                "manifest_state": "final",
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
                "package_inventory": {
                    "path": packet["candidate_package_inventory_path"],
                    "inventory_id": inventory["inventory_id"],
                    "file_sha256": inventory["inventory_sha256"],
                },
                "engineering_evidence": [
                    {
                        "path": engineering_path.relative_to(root).as_posix(),
                        "file_sha256": sha256_file(engineering_path),
                    }
                ],
                "implementation_review": {
                    "path": implementation_review_path.relative_to(root).as_posix(),
                    "file_sha256": sha256_file(implementation_review_path),
                    "review_result": "IMPLEMENTATION_READY",
                    "candidate_id": candidate_id,
                },
                "recovery_artifacts": [
                    {
                        "role": "source-base",
                        "path": source.relative_to(root).as_posix(),
                        "file_sha256": sha256_file(source),
                    }
                ],
            }
            manifest_path = root / packet["candidate_manifest_path"]
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False))

            result = {
                "result_packet_path": packet["result_packet_path"],
                "packet_path": packet["packet_path"],
                "packet_id": packet["packet_id"],
                "packet_preflight": copy.deepcopy(start_draft["packet_preflight"]),
                "acknowledgment": copy.deepcopy(start_draft["acknowledgment"]),
                "execution_start": file_binding(
                    root,
                    start_path,
                    "execution_start_id",
                    yaml.safe_load(start_path.read_text())["execution_start_id"],
                ),
                "batch_id": "B900",
                "campaign_generation": 2,
                "route_id": "T900",
                "parallel_set": None,
                "work_kind": "code",
                "problem_epoch": 3,
                "representation_revision": 4,
                "result_contract_version": BATCH.RESULT_CONTRACT_V2,
                "workflow_source_identity": workflow_source_binding["source_snapshot"]["identity"],
                "started_at": "2026-08-12T08:01:00Z",
                "ended_at": "2026-08-12T08:02:00Z",
                "outcome": "completed",
                "changes_executable_candidate": True,
                "planned_spend": "1 proposal attempt",
                "actual_spend": "1 proposal attempt",
                "accounting_evidence": (
                    f"authoritative output {packet['candidate_package_inventory_path']} "
                    f"sha256:{inventory['inventory_sha256']}"
                ),
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
                "implementation_review_state": "IMPLEMENTATION_READY",
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
            result_packet = packet
            result_validation = RESULT.validate(result, "draft", result_packet, repo_root=root)
            self.assertTrue(result_validation["result_structure_ready"], result_validation["findings"])
            result["result_packet_id"] = result_validation["computed_result_packet_id"]
            self.assertTrue(
                RESULT.validate(result, "frozen", result_packet, repo_root=root)[
                    "result_structure_ready"
                ]
            )
            result_path = root / packet["result_packet_path"]
            result_path.write_text(yaml.safe_dump(result, sort_keys=False))

            closeout = root / "docs/task/log.md"
            closeout.parent.mkdir(parents=True, exist_ok=True)
            closeout.write_text(
                yaml.safe_dump(
                    {
                        "event": "CLOSEOUT_COMPLETE",
                        "campaign_generation": 2,
                        "campaign_status": "halted",
                        "unresolved_claims": [],
                        "active_workers": [],
                        "handoff_complete": True,
                    },
                    sort_keys=False,
                )
            )
            budget_path = root / "docs/task/budget.yaml"
            budget_path.write_text(
                yaml.safe_dump(
                    {
                        "proposal_attempt_ceiling": 20,
                        "actual_spend": 1,
                        "unknown_spend": 0,
                        "active_reservations": [],
                    },
                    sort_keys=False,
                )
            )
            closeout_binding = file_binding(
                root, closeout, None, f"sha256:{sha256_file(closeout)}"
            )
            budget_binding = file_binding(
                root, budget_path, None, f"sha256:{sha256_file(budget_path)}"
            )
            lineage_sources = {
                "closeout": copy.deepcopy(closeout_binding),
                "handoff": copy.deepcopy(closeout_binding),
                "budget": copy.deepcopy(budget_binding),
            }
            recovery = {
                "recovery_preflight_path": "artifacts/frontier/recovery/G003/B900.yaml",
                "prior_campaign_generation": 2,
                "campaign_generation": 3,
                "prior_closeout": {
                    "event": "CLOSEOUT_COMPLETE",
                    "campaign_generation": 2,
                    "campaign_status": "halted",
                    "closeout_identity": closeout_binding["identity"],
                    "final_handoff_identity": closeout_binding["identity"],
                    "unresolved_claims": [],
                    "active_workers": [],
                },
                "inherited_budget": {
                    "proposal_attempt_ceiling": 20,
                    "actual_spend": 1,
                    "unknown_spend": 0,
                    "active_reservations": [],
                    "budget_identity": budget_binding["identity"],
                },
                "lineage_sources": lineage_sources,
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
                "closeout_identity": closeout_binding["identity"],
                "final_handoff_identity": closeout_binding["identity"],
                "final_budget_identity": budget_binding["identity"],
                "lineage_sources": copy.deepcopy(lineage_sources),
                "final_direction_state": {
                    "compatible_evidence": ["E900"],
                    "controlling_reflections": ["OR900"],
                    "progress_meaning": "bounded local effect under tested conditions",
                    "constraint_meaning": "the remaining constraint is unresolved",
                    "route_set_state": "decision-complete at closeout",
                    "reopening_events": [],
                    "diagnostic_dominance": "no diagnostic selected at closeout",
                    "resolver": {
                        "evidence_state_identity": "sha256:final-evidence-state",
                        "row": 11,
                        "direction_resolution": "stop",
                        "exact_action": "full-closeout",
                    },
                    "budget_reachability": "no funded path reaches another meaningful check",
                    "workflow_source_identity": workflow_source_binding["source_snapshot"]["identity"],
                },
                "workflow_source_bindings": [copy.deepcopy(workflow_source_binding)],
                "subtree_identity_algorithm": PACKAGE.PACKAGE_PATH_SIZE_SHA256_V1,
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
                        "source": "docs/task/budget.yaml",
                        "scope": "file",
                        "identity": f"sha256:{sha256_file(budget_path)}",
                        "destination": "task/budget.yaml",
                        "role": "final-budget",
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
                    {
                        "source": workflow_source_binding["source_manifest"]["path"],
                        "scope": "file",
                        "identity": workflow_source_binding["source_manifest"]["identity"],
                        "destination": "workflow/R900/source-manifest.yaml",
                        "role": "workflow-source-manifest",
                    },
                    {
                        "source": workflow_source_binding["source_snapshot"]["path"],
                        "scope": "file",
                        "identity": workflow_source_binding["source_snapshot"]["identity"],
                        "destination": "workflow/R900/source-snapshot.yaml",
                        "role": "workflow-source-snapshot",
                    },
                ],
            }
            package_audit = PACKAGE.validate_plan(package_plan, "audit", root)
            self.assertTrue(package_audit["package_ready"], package_audit["findings"])
            package_plan["package_id"] = package_audit["computed_package_id"]
            plan_path = root / "package-plan.yaml"
            plan_path.write_text(yaml.safe_dump(package_plan, sort_keys=False))
            with self.assertRaisesRegex(PACKAGE.PackageError, "build is closed"):
                PACKAGE.build(plan_path, root / "packages", root)
            self.assertFalse((root / "packages").exists())


class Slice7ContractTests(unittest.TestCase):
    def assert_contract_contains(self, relative: str, *fragments: str) -> None:
        text = (SCRIPT_ROOT.parent / "references" / relative).read_text()
        for fragment in fragments:
            with self.subTest(reference=relative, fragment=fragment):
                self.assertIn(fragment, text)

    def test_single_route_and_optional_w_profile(self) -> None:
        self.assert_contract_contains(
            "entry-and-planning.md",
            "Create no fake alternative T",
            "request no campaign-baseline tradeoff V",
            "decide professional involvement and whether W is needed",
        )

    def test_progressive_design_and_candidate_measurement_boundary(self) -> None:
        self.assert_contract_contains(
            "campaign-cycle.md",
            "Do not reload `technical-design.md` to execute a `ready` design",
            "one separate formal Slot H evaluation B for an unchanged `IMPLEMENTATION_READY` candidate",
            "retained historical-candidate exception when it actually applies",
        )

    def test_implementation_design_has_one_professional_author_and_a_direct_escape(self) -> None:
        designer = (
            SCRIPT_ROOT.parents[1] / "design-implementation/SKILL.md"
        ).read_text()
        for fragment in (
            "Return `DIRECT_ELIGIBLE` without writing when established agreements already settle the important choices",
            "Write the assigned answer or affected existing design content",
            "When W is used, the Coordinator owns maps, traceability, lifecycle fields",
            "creates no B, proposal identity, reservation, or spend",
            "RESULT: DRAFT_READY | DIRECT_ELIGIBLE",
        ):
            self.assertIn(fragment, designer)

        self.assert_contract_contains(
            "technical-design.md",
            "Continue directly when established tools, interfaces and agreements settle the important technical choices",
            "A local professional answer may stay in its assigned existing work or design record",
            "`design-implementation` owns the professional Design brief and design contracts",
            "The Coordinator owns W lifecycle and the derived Design map, Delivery map and traceability",
        )
        self.assert_contract_contains(
            "worker-interfaces.md",
            "| `design-implementation` |",
            "only `design-implementation` revises professional design content",
        )
        self.assert_contract_contains(
            "design-review.md",
            "Introducing this authoring role does not reopen an unchanged finding-free design",
        )

    def test_reflection_claim_and_parent_change_routes(self) -> None:
        self.assert_contract_contains(
            "learning-loop.md",
            "Batch completion or failure does not establish route completion or failure",
            "relative to direct development or stronger outcome evidence",
            "Dependent strategic spend needs sufficient evidence",
            "A valid whole-treatment comparison may support that the bounded package caused the observed local effect",
            "This section is the only investment-direction resolver",
            "Only after an investment trigger, apply the rows from 1 through 13 once",
            "REPLAN_READY",
        )
        self.assert_contract_contains(
            "closeout-and-claims.md",
            "do not starve the campaign",
            "A withdrawing X likewise blocks only that wording",
            "Preserve final direction state",
            "Preserve legacy Outcome Reflections exactly as produced",
            "each surviving project decision root, parent chain",
        )
        self.assert_contract_contains(
            "frontier-core.md",
            "## Change impact and retained results",
            "Prior spend, materialization and a changed epoch or revision number alone do not force a new generation or candidate",
            "Project provenance",
            "Workflow, template, validator, storage or generation changes alone create no new review",
        )

    def test_recovery_uses_retained_git_and_artifacts_not_conversation(self) -> None:
        self.assert_contract_contains(
            "frontier-core.md",
            "Recover project facts from recorded decisions, retained Git versions and artifact references",
            "Conversation is not recorded state",
            "Check the content needed for that use at its existing gate",
            "Missing bytes pause their dependent use",
        )
        self.assert_contract_contains(
            "packaging-and-recovery.md",
            "writes only `handoff.json`, citing that commit and the records' repository",
            "Use `verify-handoff` to read the exact records from Git",
            "Workflow deployment files, environments,\ncaches, and unrelated work are not handoff members",
            "Recovery needs the retained Git history and only the external artifacts needed",
        )

    def test_first_batch_transition_authorizes_a_rule_not_a_date_literal(self) -> None:
        self.assert_contract_contains(
            "batch-packet-format.md",
            "frontier-lifecycle-transition/1",
            "capture: once_after_accepted_acknowledgment",
            "updated: {derive: calendar_date, source: transition_time, timezone: UTC}",
            "A runtime-derived timestamp or date is never a packet literal",
        )

    def test_user_facing_handoff_is_manager_readable_and_exposes_each_real_decision(self) -> None:
        self.assert_contract_contains(
            "user-facing-handoff.md",
            "Load when [Continuing task and stage instructions]",
            "selects a user return:",
            "Otherwise continue through the existing Coordinator route",
            "It does not rerun the router, resolver, Review or adoption",
            "what materially changed and why it matters to the objective",
            "the strongest supported conclusion and its important limit",
            "the remaining objective gap or the observation needed to determine it",
            "every material next candidate, recorded ordering and switching condition",
            "A procedural gate must be paired with the substantive question it protects",
            "Preserve non-dominated alternatives and switching conditions",
            "perform it instead of returning a planning instruction",
            "Ask only for a boundary owned by",
            "Reuse an applicable V",
            "If the current request already supplies the decision or Permission",
            "Do not offer “authorize this exact B”",
            "suggest no command",
        )
        coordinator = (SCRIPT_ROOT.parent / "SKILL.md").read_text()
        self.assertIn("references/user-facing-handoff.md", coordinator)
        self.assertIn("Select one stage using the core router", coordinator)
        self.assertIn(
            "use [Active learning chain]",
            coordinator,
        )
        self.assertIn("A worker return or Batch outcome does not by itself end the research problem", coordinator)
        self.assert_contract_contains(
            "user-decisions.md",
            "Continue necessary in-scope work after each stage completes",
            "the user requests a pause or a report-only response",
            "A standalone analysis, review or planning request ends at its requested deliverable and grants no implementation authority",
        )
        for reference in (
            "entry-and-planning.md",
            "campaign-cycle.md",
            "closeout-and-claims.md",
            "packaging-and-recovery.md",
        ):
            with self.subTest(reference=reference):
                contract = (SCRIPT_ROOT.parent / "references" / reference).read_text()
                self.assertNotIn("User-facing handoff", contract)
                if reference == "packaging-and-recovery.md":
                    self.assertIn("follows the Entry router", contract)
                else:
                    self.assertIn("Coordinator", contract)

        core = (SCRIPT_ROOT.parent / "references/frontier-core.md").read_text()
        self.assertNotIn("## User-facing handoff", core)

        cycle = (SCRIPT_ROOT.parent / "references" / "campaign-cycle.md").read_text()
        for behavior in (
            "A terminal implementation result has positive implementation review but no later resolver result",
            "Adopt the result and arrange the next work within the current research problem",
            "Implementation evidence is not performance evidence",
            "A fresh direction resolution is not an execution credential for ordinary continuation",
        ):
            with self.subTest(behavior=behavior):
                self.assertIn(behavior, cycle)

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
        self.assertEqual(len(scenario_ids), 38)
        self.assertIn("candidate-recovery-identity-mismatch", scenario_ids)
        self.assertIn("post-closeout-package", scenario_ids)
        self.assertIn("compacted-context", scenario_ids)
        self.assertIn("known-vacuous-ceiling", scenario_ids)
        self.assertIn("unknown-noise-resolution", scenario_ids)
        self.assertIn("diagnostic-before-implementation-review", scenario_ids)
        self.assertIn("formal-evaluation-before-implementation-review", scenario_ids)
        self.assertIn("high-risk-diagnostic-experiment", scenario_ids)
        self.assertIn("measurement-protocol-change", scenario_ids)
        self.assertIn("first-b-crosses-utc-midnight", scenario_ids)
        self.assertIn("handoff-known-recovery", scenario_ids)
        self.assertIn("handoff-authorization-ready", scenario_ids)
        self.assertIn("handoff-current-request-already-qualifies", scenario_ids)
        self.assertIn("handoff-parent-review-required", scenario_ids)
        self.assertIn("handoff-no-legal-continuation", scenario_ids)
        self.assertIn("handoff-genuine-user-tradeoff", scenario_ids)


if __name__ == "__main__":
    unittest.main()
