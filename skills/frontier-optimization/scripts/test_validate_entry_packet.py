#!/usr/bin/env python3
"""Regression tests for source-derived Frontier Entry validation."""

from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from functools import lru_cache
from pathlib import Path

import yaml
import workflow_source_binding as WORKFLOW_SOURCE

from workflow_source_binding import (
    CLOSURE_CONTRACT_V1,
    CLOSURE_PATHS_BY_CONTRACT,
    CURRENT_CLOSURE_CONTRACT,
    GOVERNING_PATHS,
    validate_binding,
    validate_source_closure,
)


SCRIPT = Path(__file__).with_name("validate_entry_packet.py")
SPEC = importlib.util.spec_from_file_location("validate_entry_packet", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

BATCH_SCRIPT = Path(__file__).with_name("validate_batch_packet.py")
BATCH_SPEC = importlib.util.spec_from_file_location("validate_batch_packet_for_entry_tests", BATCH_SCRIPT)
assert BATCH_SPEC and BATCH_SPEC.loader
BATCH = importlib.util.module_from_spec(BATCH_SPEC)
sys.modules[BATCH_SPEC.name] = BATCH
BATCH_SPEC.loader.exec_module(BATCH)

PROJECT_SNAPSHOT_SCRIPT = Path(__file__).with_name("project_snapshot.py")
PROJECT_SNAPSHOT_SPEC = importlib.util.spec_from_file_location(
    "project_snapshot_for_entry_tests", PROJECT_SNAPSHOT_SCRIPT
)
assert PROJECT_SNAPSHOT_SPEC and PROJECT_SNAPSHOT_SPEC.loader
PROJECT_SNAPSHOT = importlib.util.module_from_spec(PROJECT_SNAPSHOT_SPEC)
sys.modules[PROJECT_SNAPSHOT_SPEC.name] = PROJECT_SNAPSHOT
PROJECT_SNAPSHOT_SPEC.loader.exec_module(PROJECT_SNAPSHOT)


def write_mapping(root: Path, relative: str, value: dict) -> bytes:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = yaml.safe_dump(value, sort_keys=False).encode()
    path.write_bytes(raw)
    return raw


def write_target(root: Path, payload: dict) -> tuple[str, str]:
    payload_raw = yaml.safe_dump(payload, sort_keys=False).encode()
    digest = MODULE.sha256_bytes(payload_raw)
    target_id = f"V900-target-sha256:{digest}"
    raw = f"target_id: {target_id}\n".encode() + payload_raw
    path = root / "artifacts/frontier/V900-target.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return target_id, MODULE.sha256_bytes(raw)


def write_target_specification(root: Path, payload: dict) -> dict:
    payload_raw = yaml.safe_dump(payload, sort_keys=False).encode()
    digest = MODULE.sha256_bytes(payload_raw)
    target_spec_id = f"V900-target-spec-sha256:{digest}"
    raw = f"target_spec_id: {target_spec_id}\n".encode() + payload_raw
    relative = "artifacts/frontier/V900-target-spec.yaml"
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return {
        "contract_version": "frontier-authorization-target-specification/1",
        "path": relative,
        "identity_field": "target_spec_id",
        "identity": target_spec_id,
        "file_sha256": MODULE.sha256_bytes(raw),
    }


def frontier_bytes(current_state: dict) -> bytes:
    frontmatter = {
        "campaign_generation": current_state["campaign_generation"],
        "campaign_status": current_state["campaign_status"],
        "current_state": current_state,
    }
    return (
        b"---\n"
        + yaml.safe_dump(frontmatter, sort_keys=False).encode()
        + b"---\n\n# FRONTIER\n"
    )


def ensure_git_repository(root: Path) -> None:
    if not (root / ".git").exists():
        subprocess.run(["git", "init", "-q", str(root)], check=True)


@lru_cache(maxsize=1)
def workflow_source_fixture() -> tuple[bytes, bytes, dict]:
    """Build the immutable version 1 source fixture once per test process."""
    skill_root = Path(__file__).parent.parent
    source_paths = tuple(sorted(GOVERNING_PATHS))

    def source_file(logical_path: str) -> Path:
        if logical_path.startswith("workers/"):
            _, skill_name, *relative = Path(logical_path).parts
            return skill_root.parent / skill_name / Path(*relative)
        return skill_root / logical_path

    source_members = {path: source_file(path).read_text() for path in source_paths}
    snapshot = {
        "contract_version": "frontier-workflow-source-snapshot/1",
        "closure_contract": CURRENT_CLOSURE_CONTRACT,
        "members": [
            {"path": path, "content": content}
            for path, content in source_members.items()
        ],
    }
    snapshot_raw = yaml.safe_dump(snapshot, sort_keys=False).encode()
    snapshot_digest = MODULE.sha256_bytes(snapshot_raw)
    manifest = {
        "contract_version": "frontier-workflow-source-manifest/1",
        "closure_contract": CURRENT_CLOSURE_CONTRACT,
        "snapshot_identity": f"sha256:{snapshot_digest}",
        "members": [
            {
                "path": path,
                "size": len(content.encode()),
                "sha256": MODULE.sha256_bytes(content.encode()),
            }
            for path, content in source_members.items()
        ],
    }
    manifest_raw = yaml.safe_dump(manifest, sort_keys=False).encode()
    manifest_digest = MODULE.sha256_bytes(manifest_raw)
    binding = {
        "contract_version": "frontier-workflow-source-binding/1",
        "adoption_mode": "entry",
        "source_manifest": {
            "path": "artifacts/frontier/workflow/R900/source-manifest.yaml",
            "identity": f"sha256:{manifest_digest}",
            "file_sha256": manifest_digest,
        },
        "source_snapshot": {
            "path": "artifacts/frontier/workflow/R900/source-snapshot.yaml",
            "identity": f"sha256:{snapshot_digest}",
            "file_sha256": snapshot_digest,
        },
        "governs": ["Selection", "B900", "V900", "Outcome Reflection"],
    }
    return snapshot_raw, manifest_raw, binding


def write_workflow_source_binding(root: Path) -> dict:
    snapshot_raw, manifest_raw, binding = workflow_source_fixture()
    snapshot_path = root / "artifacts/frontier/workflow/R900/source-snapshot.yaml"
    manifest_path = root / "artifacts/frontier/workflow/R900/source-manifest.yaml"
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_bytes(snapshot_raw)
    manifest_path.write_bytes(manifest_raw)
    return copy.deepcopy(binding)


def make_workspace(root: Path, frozen: bool = False, target_launcher_id: str | None = None) -> dict:
    workflow_source_binding = write_workflow_source_binding(root)
    direct_raw = write_mapping(root, "artifacts/frontier/B900-direct-profile.yaml", {"profile": "direct"})
    direct_identity = f"sha256:{MODULE.sha256_bytes(direct_raw)}"
    source_base_identity = "source-sha256:example"
    source_manifest_raw = write_mapping(
        root,
        "artifacts/frontier/B900/source-manifest.yaml",
        {"candidate_id": source_base_identity, "members": []},
    )
    launcher_id = "B900-launcher-preflight-sha256:correct"
    launcher_raw = json.dumps(
        {"preflight_id": launcher_id, "status": "PASS"}, sort_keys=True
    ).encode()
    launcher_path = root / "artifacts/frontier/B900-launcher-preflight.json"
    launcher_path.parent.mkdir(parents=True, exist_ok=True)
    launcher_path.write_bytes(launcher_raw)
    proposed_transition = {
        "budget": "reserve one proposal attempt for B900",
        "selection": "adopt B900 as Primary",
        "lifecycle": "FIRST_BATCH_PLANNED after adoption",
    }
    post_adoption_paths = [
        "docs/skills/optimization/example/FRONTIER.md",
        "docs/skills/optimization/example/frontier/ledger.md",
        "docs/skills/optimization/example/log.md",
    ]
    decision_record_path = "docs/skills/optimization/example/frontier/ledger.md"
    result_path = "artifacts/frontier/B900/result.yaml"
    user_result_path = "artifacts/frontier/V900-result.yaml"
    scope = "one bounded implementation"
    maximum_spend = "one proposal attempt"
    stop_boundary = "materialized-stopped"
    authorization_question = "Authorize exactly the reviewed B900 materialization?"
    authorize_consequence = "dispatch B900 within reviewed budget"
    decline_consequence = "keep B900 undispatched"
    conditional_consequence = "require a fresh target and Entry review"
    target_specification = write_target_specification(
        root,
        {
            "contract_version": "frontier-authorization-target-specification/1",
            "decision_id": "V900",
            "batch_id": "B900",
            "target_path": "artifacts/frontier/V900-target.yaml",
            "user_result_path": user_result_path,
            "decision_record_path": decision_record_path,
            "design_contract_identity": direct_identity,
            "source_base_identity": source_base_identity,
            "scope": scope,
            "maximum_spend": maximum_spend,
            "stop_boundary": stop_boundary,
            "result_path": result_path,
            "proposed_state_transition": proposed_transition,
            "post_adoption_paths": post_adoption_paths,
            "authorization_question": authorization_question,
            "authorize_consequence": authorize_consequence,
            "decline_consequence": decline_consequence,
            "conditional_consequence": conditional_consequence,
        },
    )
    packet_document = {
        "packet_path": "artifacts/frontier/B900/packet.yaml",
        "packet_preflight_path": "artifacts/frontier/B900/packet-preflight.json",
        "task_path": "docs/skills/optimization/example",
        "batch_id": "B900",
        "campaign_generation": 1,
        "route_id": "T900",
        "parallel_set": None,
        "work_kind": "code",
        "problem_epoch": 1,
        "representation_revision": 1,
        "changes_executable_candidate": True,
        "executor": "Agent",
        "required_inputs": [],
            "identity_contract": BATCH.IDENTITY_CONTRACT,
            "result_contract_version": BATCH.RESULT_CONTRACT_V2,
            "workflow_source_binding": copy.deepcopy(workflow_source_binding),
            "workflow_source_identity": workflow_source_binding["source_snapshot"]["identity"],
            "worker_source_member": "workers/run-frontier-batch/SKILL.md",
        "design_profile": "direct",
        "design_contract_identity": direct_identity,
        "design_contract_binding": {
            "path": "artifacts/frontier/B900-direct-profile.yaml",
            "identity_field": None,
            "identity": direct_identity,
            "file_sha256": MODULE.sha256_bytes(direct_raw),
        },
        "development_authorization_target": target_specification,
        "source_base_identity": source_base_identity,
        "source_base_binding": {
            "path": "artifacts/frontier/B900/source-manifest.yaml",
            "identity_field": "candidate_id",
            "identity": source_base_identity,
            "file_sha256": MODULE.sha256_bytes(source_manifest_raw),
        },
        "maximum_spend": "one proposal attempt",
        "authorization_gate": "finding-free Entry adoption",
        "authorization_boundary": {
            "scope": "one bounded implementation",
            "maximum_spend": "one proposal attempt",
            "stop_boundary": "materialized-stopped",
            "result_path": "artifacts/frontier/B900/result.yaml",
        },
        "stop_conditions": ["stop at the materialized boundary"],
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
                "path": "artifacts/frontier/B900-direct-profile.yaml",
                "scope": "file",
                "identity": f"sha256:{MODULE.sha256_bytes(direct_raw)}",
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
                            "path": "artifacts/frontier/B900-direct-profile.yaml",
                            "file_sha256": MODULE.sha256_bytes(direct_raw),
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
                    "path": "artifacts/frontier/B900-direct-profile.yaml",
                    "file_sha256": MODULE.sha256_bytes(direct_raw),
                    "locator": "fixture parent charges first candidate identity",
                },
                "repair_mode": "prohibited",
                "effect_scope": "deterministic-local-checks-only",
                "authoritative_output_path": "artifacts/frontier/B900/package-inventory.yaml",
                "engineering_evidence_path": "artifacts/frontier/B900/engineering-evidence.json",
            },
            "artifact_paths": [
                "candidates/B900-example/",
                "artifacts/frontier/B900/package-inventory.yaml",
                "artifacts/frontier/B900/candidate-manifest.yaml",
                "artifacts/frontier/B900/engineering-evidence.json",
                "artifacts/frontier/B900/result-validation.json",
            "artifacts/frontier/B900/result.yaml",
        ],
        "acknowledgment_path": "artifacts/frontier/B900/acknowledgment.yaml",
        "result_validation_path": "artifacts/frontier/B900/result-validation.json",
        "result_packet_path": "artifacts/frontier/B900/result.yaml",
        "prohibited_actions": ["edit Coordinator outputs or perform measurement"],
    }
    packet_draft = BATCH.validate(packet_document, "draft", root)
    if not packet_draft["packet_structure_ready"]:
        raise AssertionError(packet_draft["findings"])
    packet_id = packet_draft["computed_packet_id"]
    packet_document["packet_id"] = packet_id
    packet_raw = write_mapping(
        root,
        "artifacts/frontier/B900/packet.yaml",
        packet_document,
    )
    structural_preflight = BATCH.validate(packet_document, "frozen", root)
    if not structural_preflight["packet_structure_ready"]:
        raise AssertionError(structural_preflight["findings"])
    structural_preflight_id = structural_preflight["preflight_id"]
    structural_preflight_raw = (
        json.dumps(structural_preflight, indent=2, sort_keys=True) + "\n"
    ).encode()
    structural_preflight_path = root / "artifacts/frontier/B900/packet-preflight.json"
    structural_preflight_path.write_bytes(structural_preflight_raw)
    pre_current_state = {
        "campaign_generation": 1,
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
    post_adoption_files = []
    for name, live_relative in (
        ("FRONTIER.md", "docs/skills/optimization/example/FRONTIER.md"),
        ("ledger.md", "docs/skills/optimization/example/frontier/ledger.md"),
        ("log.md", "docs/skills/optimization/example/log.md"),
    ):
        post_relative = f"artifacts/frontier/B900/proposed-{name}"
        live_path = root / live_relative
        post_path = root / post_relative
        live_path.parent.mkdir(parents=True, exist_ok=True)
        post_path.parent.mkdir(parents=True, exist_ok=True)
        if name == "FRONTIER.md":
            live_path.write_bytes(frontier_bytes(pre_current_state))
            post_path.write_bytes(frontier_bytes(post_current_state))
        else:
            live_path.write_text(f"{name}: before\n")
            post_path.write_text(f"{name}: after B900 adoption\n")
        post_adoption_files.append(
            {
                "path": live_relative,
                "pre_sha256": MODULE.sha256_bytes(live_path.read_bytes()),
                "post_source": {
                    "path": post_relative,
                    "file_sha256": MODULE.sha256_bytes(post_path.read_bytes()),
                },
            }
        )
    post_adoption_state = {
        "contract_version": "frontier-post-adoption-state/1",
        "files": post_adoption_files,
    }
    entry_reviewed_bindings = [
        {
            "role": "direct_profile",
            "path": "artifacts/frontier/B900-direct-profile.yaml",
            "identity": direct_identity,
            "identity_field": None,
            "file_sha256": MODULE.sha256_bytes(direct_raw),
            "batch_scoped": False,
        },
        {
            "role": "launcher_preflight",
            "path": "artifacts/frontier/B900-launcher-preflight.json",
            "identity": launcher_id,
            "identity_field": "preflight_id",
            "file_sha256": MODULE.sha256_bytes(launcher_raw),
            "batch_scoped": True,
        },
        {
            "role": "source_base",
            "path": "artifacts/frontier/B900/source-manifest.yaml",
            "identity": source_base_identity,
            "identity_field": "candidate_id",
            "file_sha256": MODULE.sha256_bytes(source_manifest_raw),
            "batch_scoped": False,
        },
    ]
    target_reviewed_bindings = yaml.safe_load(
        yaml.safe_dump(entry_reviewed_bindings, sort_keys=False)
    )
    target_reviewed_bindings[1]["identity"] = target_launcher_id or launcher_id
    target_id, target_sha = write_target(
        root,
        {
            "identity_rule": "exact UTF-8 bytes with the complete target_id line omitted",
            "decision_id": "V900",
            "target_specification": target_specification,
            "batch_id": "B900",
            "preflight_id": structural_preflight_id,
            "design_contract_identity": direct_identity,
            "source_base_identity": source_base_identity,
            "scope": scope,
            "maximum_spend": maximum_spend,
            "stop_boundary": stop_boundary,
            "result_path": result_path,
            "user_result_path": user_result_path,
            "decision_record_path": decision_record_path,
            "proposed_state_transition": proposed_transition,
            "post_adoption_state": post_adoption_state,
            "post_adoption_paths": post_adoption_paths,
            "authorization_question": authorization_question,
            "exact_object": {
                "batch_id": "B900",
                "packet": {
                    "path": "artifacts/frontier/B900/packet.yaml",
                    "packet_id": packet_id,
                    "file_sha256": MODULE.sha256_bytes(packet_raw),
                },
                "structural_preflight": {
                    "path": "artifacts/frontier/B900/packet-preflight.json",
                    "preflight_id": structural_preflight_id,
                    "file_sha256": MODULE.sha256_bytes(structural_preflight_raw),
                },
                "reviewed_bindings": target_reviewed_bindings,
            },
            "authorize_consequence": authorize_consequence,
            "decline_consequence": decline_consequence,
            "conditional_consequence": conditional_consequence,
        },
    )
    packet = {
        "review_kind": "entry",
        "review_stage": "authorization-readiness",
        "review_id": "R900",
        "packet_path": "frontier/reviews/entry-R900-packet.yaml",
        "entry_schema_preflight_paths": {
            "draft": "frontier/reviews/entry-R900-draft-schema.json",
            "frozen": "frontier/reviews/entry-R900-frozen-schema.json",
        },
        "task_path": "docs/skills/optimization/example",
        "problem_epoch": 1,
        "problem_generated_at": "2026-01-01T00:00:00Z",
        "representation_revision": 1,
        "representation_generated_at": "2026-01-01T00:00:00Z",
        "representation_review_result": "PROCEED_EXPLORATORY",
        "representation_permitted": "bounded scope",
        "workflow_source_binding": workflow_source_binding,
        "campaign_generation": 1,
        "recovery_lineage": None,
        "repository_structure_disposition": "existing-integrated",
        "repository_layout_approval": None,
        "design_gate": {
            "mode": "direct",
            "bindings": entry_reviewed_bindings,
        },
        "dispatch_contract": {
            "batch_id": "B900",
            "packet_path": "artifacts/frontier/B900/packet.yaml",
            "packet_id": packet_id,
            "preflight_path": "artifacts/frontier/B900/packet-preflight.json",
            "preflight_id": structural_preflight_id,
            "preflight_file_sha256": MODULE.sha256_bytes(structural_preflight_raw),
            "design_contract_identity": direct_identity,
            "source_base_identity": source_base_identity,
            "scope": scope,
            "maximum_spend": maximum_spend,
            "stop_boundary": stop_boundary,
            "result_path": result_path,
        },
        "authorization_target": {
            "target_path": "artifacts/frontier/V900-target.yaml",
            "target_id": target_id,
            "target_file_sha256": target_sha,
            "batch_id": "B900",
            "decision_id": "V900",
            "target_specification": target_specification,
            "packet_path": "artifacts/frontier/B900/packet.yaml",
            "packet_id": packet_id,
            "preflight_id": structural_preflight_id,
            "design_contract_identity": direct_identity,
            "source_base_identity": source_base_identity,
            "scope": scope,
            "maximum_spend": maximum_spend,
            "stop_boundary": stop_boundary,
            "result_path": result_path,
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
            "contract_version": MODULE.CAMPAIGN_STATE_PROJECTION_CONTRACT,
            "live_path": "docs/skills/optimization/example/FRONTIER.md",
            "post_source_path": "artifacts/frontier/B900/proposed-FRONTIER.md",
            "pre": pre_current_state,
            "post": post_current_state,
        },
        "authorization_adoption_path": "frontier/reviews/entry-R900-adoption.yaml",
        "authorization_adoption_preflight_path": "frontier/reviews/entry-R900-adoption-preflight.json",
        "selected_batches": ["B900"],
        "actual_spend": "zero",
        "assigned_review_path": "frontier/reviews/entry-R900.md",
        "completion_check": "review every readiness requirement",
    }
    if frozen:
        ensure_git_repository(root)
        project_paths = [
            "artifacts/frontier/B900-direct-profile.yaml",
            "artifacts/frontier/B900-launcher-preflight.json",
            "artifacts/frontier/B900/packet.yaml",
            "artifacts/frontier/B900/packet-preflight.json",
            "artifacts/frontier/B900/source-manifest.yaml",
            "artifacts/frontier/V900-target-spec.yaml",
            "artifacts/frontier/V900-target.yaml",
            "docs/skills/optimization/example/FRONTIER.md",
            "docs/skills/optimization/example/frontier/ledger.md",
            "docs/skills/optimization/example/log.md",
            "artifacts/frontier/B900/proposed-FRONTIER.md",
            "artifacts/frontier/B900/proposed-ledger.md",
            "artifacts/frontier/B900/proposed-log.md",
        ]
        manifest_relative = "frontier/reviews/entry-R900-project-snapshot.yaml"
        manifest = PROJECT_SNAPSHOT.capture(
            root,
            manifest_path=root / manifest_relative,
            paths=project_paths,
            created_at="2026-08-16T00:00:00Z",
        )
        manifest_raw = (root / manifest_relative).read_bytes()
        packet.update(
            {
                "snapshot_manifest": {
                    "path": manifest_relative,
                    "snapshot_id": manifest["snapshot_id"],
                    "file_sha256": MODULE.sha256_bytes(manifest_raw),
                },
                "snapshot_id": manifest["snapshot_id"],
            }
        )
        packet["packet_id"] = MODULE.validate(packet, "frozen", root)["computed_packet_id"]
    return packet


class EntryPacketSchemaTests(unittest.TestCase):
    def test_unknown_workflow_identity_field_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            entry = make_workspace(root)
            entry["workflow_release_identity"] = "workflow-sha256:" + "a" * 64

            result = MODULE.validate(entry, "draft", root)

            self.assertIn("UNKNOWN_ENTRY_FIELD", {item["code"] for item in result["findings"]})

    def test_entry_completion_check_rejects_workflow_release_checks(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for completion_check in (
                "run validate_frontier_skill_bundle.py",
                "run frontier validator tests",
                "run Skill validation",
            ):
                with self.subTest(completion_check=completion_check):
                    entry = make_workspace(root)
                    entry["completion_check"] = completion_check

                    result = MODULE.validate(entry, "draft", root)

                    self.assertIn(
                        "ENTRY_COMPLETION_CHECK_OUT_OF_SCOPE",
                        {item["code"] for item in result["findings"]},
                    )
                    self.assertEqual([], result["blocking_findings"])
                    self.assertEqual("repair", result["repair_findings"][0]["effect"])

    def test_project_workflow_completion_check_remains_task_neutral(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            entry = make_workspace(root)
            entry["completion_check"] = "verify the project workflow test suite"

            result = MODULE.validate(entry, "draft", root)

            self.assertTrue(result["entry_schema_ready"], result["findings"])

    def test_entry_live_reconciliation_rejects_executable_mode_drift(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            entry = make_workspace(root, frozen=True)
            source = root / "artifacts/frontier/B900-direct-profile.yaml"
            source.chmod(0o755)

            result = MODULE.validate(entry, "frozen", root)

            self.assertIn("LIVE_SOURCE_DRIFT", {item["code"] for item in result["findings"]})

    def test_authorization_readiness_requires_typed_campaign_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            entry = make_workspace(root)
            entry.pop("campaign_state_projection")

            result = MODULE.validate(entry, "draft", root)

            self.assertIn(
                "CAMPAIGN_STATE_PROJECTION_INVALID",
                {item["code"] for item in result["findings"]},
            )

    def test_current_state_rejects_invalid_types_and_enums_after_rebinding(self) -> None:
        cases = {
            "campaign_generation": (0, 0),
            "campaign_status": ("invalid-status", "invalid-status"),
            "primary_batch": (7, 7),
            "parallel_batches": ("B901", "B901"),
            "decision_id": ("B900", "B900"),
            "authorization_state": ("waiting", "accepted"),
            "execution_batch": ("V900", "V900"),
            "execution_state": ("queued", "running"),
        }
        for field, (pre_value, post_value) in cases.items():
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                entry = make_workspace(root)
                projection = entry["campaign_state_projection"]
                pre = dict(projection["pre"])
                post = dict(projection["post"])
                pre[field] = pre_value
                post[field] = post_value
                projection["pre"] = pre
                projection["post"] = post

                live_path = root / projection["live_path"]
                post_path = root / projection["post_source_path"]
                live_path.write_bytes(frontier_bytes(pre))
                post_path.write_bytes(frontier_bytes(post))

                target_path = root / entry["authorization_target"]["target_path"]
                target_payload = yaml.safe_load(target_path.read_text())
                target_payload.pop("target_id")
                post_state = target_payload["post_adoption_state"]
                post_state["files"][0]["pre_sha256"] = MODULE.sha256_bytes(
                    live_path.read_bytes()
                )
                post_state["files"][0]["post_source"]["file_sha256"] = (
                    MODULE.sha256_bytes(post_path.read_bytes())
                )
                target_id, target_sha = write_target(root, target_payload)
                entry["authorization_target"].update(
                    {
                        "target_id": target_id,
                        "target_file_sha256": target_sha,
                        "post_adoption_state": post_state,
                    }
                )

                result = MODULE.validate(entry, "draft", root)

                matching = [
                    item
                    for item in result["findings"]
                    if item["code"] == "CAMPAIGN_STATE_FIELD_INVALID"
                    and field in item["detail"]
                ]
                self.assertTrue(matching, result["findings"])

    def test_post_state_pending_claim_fails_before_review(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            entry = make_workspace(root)
            post_path = root / entry["campaign_state_projection"]["post_source_path"]
            contradictory = dict(entry["campaign_state_projection"]["post"])
            contradictory["authorization_state"] = "pending"
            post_path.write_bytes(frontier_bytes(contradictory))

            target_path = root / entry["authorization_target"]["target_path"]
            target_payload = yaml.safe_load(target_path.read_text())
            target_payload.pop("target_id")
            post_state = target_payload["post_adoption_state"]
            post_state["files"][0]["post_source"]["file_sha256"] = MODULE.sha256_bytes(
                post_path.read_bytes()
            )
            target_id, target_sha = write_target(root, target_payload)
            entry["authorization_target"].update(
                {
                    "target_id": target_id,
                    "target_file_sha256": target_sha,
                    "post_adoption_state": post_state,
                }
            )

            result = MODULE.validate(entry, "draft", root)

            self.assertIn(
                "CAMPAIGN_STATE_PROJECTION_MISMATCH",
                {item["code"] for item in result["findings"]},
            )

    def test_final_target_must_exactly_realize_the_pre_packet_specification(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            entry = make_workspace(root)
            target_path = root / entry["authorization_target"]["target_path"]
            target_payload = yaml.safe_load(target_path.read_text())
            target_payload.pop("target_id")
            target_payload["authorize_consequence"] = "dispatch ten unrelated batches"
            target_id, target_sha = write_target(root, target_payload)
            entry["authorization_target"].update(
                {
                    "target_id": target_id,
                    "target_file_sha256": target_sha,
                    "authorize_consequence": "dispatch ten unrelated batches",
                }
            )

            result = MODULE.validate(entry, "draft", root)

            self.assertIn(
                "TARGET_SPECIFICATION_REALIZATION_MISMATCH",
                {item["code"] for item in result["findings"]},
            )

    def test_final_target_rejects_an_extra_authority_field(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            entry = make_workspace(root)
            target_path = root / entry["authorization_target"]["target_path"]
            target_payload = yaml.safe_load(target_path.read_text())
            target_payload.pop("target_id")
            target_payload["additional_authority"] = "publish externally"
            target_id, target_sha = write_target(root, target_payload)
            entry["authorization_target"].update(
                {"target_id": target_id, "target_file_sha256": target_sha}
            )

            result = MODULE.validate(entry, "draft", root)

            self.assertIn(
                "TARGET_SPECIFICATION_REALIZATION_MISMATCH",
                {item["code"] for item in result["findings"]},
            )

    def test_exact_object_rejects_nested_authority(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            entry = make_workspace(root)
            target_path = root / entry["authorization_target"]["target_path"]
            target_payload = yaml.safe_load(target_path.read_text())
            target_payload.pop("target_id")
            target_payload["exact_object"]["additional_authority"] = (
                "publish externally"
            )
            target_id, target_sha = write_target(root, target_payload)
            entry["authorization_target"].update(
                {"target_id": target_id, "target_file_sha256": target_sha}
            )

            result = MODULE.validate(entry, "draft", root)

            self.assertIn(
                "TARGET_SPECIFICATION_REALIZATION_MISMATCH",
                {item["code"] for item in result["findings"]},
            )

    def test_authorization_adoption_path_cannot_overwrite_target(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            entry = make_workspace(root)
            entry["authorization_adoption_path"] = entry["authorization_target"][
                "target_path"
            ]

            result = MODULE.validate(entry, "draft", root)

            self.assertIn(
                "ARTIFACT_PATH_COLLISION",
                {item["code"] for item in result["findings"]},
            )

    def test_post_adoption_state_requires_exact_reviewed_pre_and_post_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            entry = make_workspace(root)
            entry["authorization_target"]["post_adoption_state"]["files"][0][
                "pre_sha256"
            ] = "0" * 64
            result = MODULE.validate(entry, "draft", root)
            self.assertIn(
                "POST_ADOPTION_STATE_INVALID",
                {item["code"] for item in result["findings"]},
            )

    def test_nonempty_transition_cannot_omit_post_adoption_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            entry = make_workspace(root)
            entry["authorization_target"]["post_adoption_state"]["files"] = []
            result = MODULE.validate(entry, "draft", root)
            self.assertIn(
                "POST_ADOPTION_STATE_MISSING",
                {item["code"] for item in result["findings"]},
            )

    def test_frozen_post_source_drift_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            entry = make_workspace(root, frozen=True)
            (root / "artifacts/frontier/B900/proposed-log.md").write_text("changed\n")
            result = MODULE.validate(entry, "frozen", root)
            self.assertIn(
                "LIVE_SOURCE_DRIFT",
                {item["code"] for item in result["findings"]},
            )

    def test_packet_spend_change_cannot_keep_the_frozen_target_specification(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            entry = make_workspace(root)
            packet_path = root / entry["dispatch_contract"]["packet_path"]
            packet = yaml.safe_load(packet_path.read_text())
            packet.pop("packet_id")
            packet["maximum_spend"] = "TEN proposal attempts"
            packet["authorization_boundary"]["maximum_spend"] = "TEN proposal attempts"
            draft = BATCH.validate(packet, "draft", root)
            self.assertIn(
                "DEVELOPMENT_AUTHORIZATION_TARGET_MISMATCH",
                {item["code"] for item in draft["findings"]},
            )

    def test_draft_and_frozen_source_reconciliation_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            draft = make_workspace(root)
            draft_result = MODULE.validate(draft, "draft", root)
            self.assertTrue(draft_result["entry_schema_ready"], draft_result["findings"])

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            frozen = make_workspace(root, frozen=True)
            result = MODULE.validate(frozen, "frozen", root)
            self.assertTrue(result["entry_schema_ready"], result["findings"])
            self.assertTrue(result["entry_bindings_ready"])

    def test_stale_launcher_identity_fails_before_review(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet = make_workspace(root)
            packet["design_gate"]["bindings"][1]["identity"] = (
                "B899-launcher-preflight-sha256:stale"
            )
            result = MODULE.validate(packet, "draft", root)
            self.assertIn("BOUND_IDENTITY_MISMATCH", {item["code"] for item in result["findings"]})

    def test_wholly_copied_prior_batch_launcher_artifact_fails_before_review(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet = make_workspace(root)
            stale_identity = "B899-launcher-preflight-sha256:stale"
            launcher_path = root / "artifacts/frontier/B900-launcher-preflight.json"
            launcher_document = json.loads(launcher_path.read_text())
            launcher_document["preflight_id"] = stale_identity
            launcher_path.write_text(json.dumps(launcher_document, sort_keys=True))
            launcher_sha = MODULE.sha256_bytes(launcher_path.read_bytes())
            packet["design_gate"]["bindings"][1].update(
                {"identity": stale_identity, "file_sha256": launcher_sha}
            )

            target_path = root / packet["authorization_target"]["target_path"]
            target_payload = yaml.safe_load(target_path.read_text())
            target_payload.pop("target_id")
            target_payload["exact_object"]["reviewed_bindings"][1].update(
                {"identity": stale_identity, "file_sha256": launcher_sha}
            )
            target_id, target_sha = write_target(root, target_payload)
            packet["authorization_target"].update(
                {"target_id": target_id, "target_file_sha256": target_sha}
            )
            result = MODULE.validate(packet, "draft", root)
            self.assertIn(
                "DESIGN_BATCH_SCOPED_IDENTITY_MISMATCH",
                {item["code"] for item in result["findings"]},
            )

    def test_non_batch_access_preflight_remains_eligible(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet = make_workspace(root)
            access_identity = "access-preflight-sha256:exact"
            access_path = root / "artifacts/frontier/B900-launcher-preflight.json"
            access_document = json.loads(access_path.read_text())
            access_document["preflight_id"] = access_identity
            access_path.write_text(json.dumps(access_document, sort_keys=True))
            access_sha = MODULE.sha256_bytes(access_path.read_bytes())
            packet["design_gate"]["bindings"][1].update(
                {
                    "role": "access_preflight",
                    "identity": access_identity,
                    "file_sha256": access_sha,
                    "batch_scoped": False,
                }
            )
            target_path = root / packet["authorization_target"]["target_path"]
            target_payload = yaml.safe_load(target_path.read_text())
            target_payload.pop("target_id")
            target_payload["exact_object"]["reviewed_bindings"][1].update(
                {
                    "role": "access_preflight",
                    "identity": access_identity,
                    "file_sha256": access_sha,
                    "batch_scoped": False,
                }
            )
            target_id, target_sha = write_target(root, target_payload)
            packet["authorization_target"].update(
                {"target_id": target_id, "target_file_sha256": target_sha}
            )
            result = MODULE.validate(packet, "draft", root)
            self.assertTrue(result["entry_schema_ready"], result["findings"])

    def test_target_cannot_bind_a_different_launcher_identity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet = make_workspace(root, target_launcher_id="B899-launcher-preflight-sha256:stale")
            result = MODULE.validate(packet, "draft", root)
            self.assertIn(
                "TARGET_DESIGN_BINDING_MISMATCH",
                {item["code"] for item in result["findings"]},
            )

    def test_stale_structural_preflight_identity_fails_before_review(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet = make_workspace(root)
            packet["authorization_target"]["preflight_id"] = (
                "B899-packet-preflight-sha256:stale"
            )
            result = MODULE.validate(packet, "draft", root)
            self.assertIn(
                "TARGET_PREFLIGHT_BINDING_MISSING",
                {item["code"] for item in result["findings"]},
            )

    def test_self_consistent_stale_batch_chain_cannot_replace_packet_derivation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet = make_workspace(root)
            stale_packet_id = "B899-packet-sha256:stale"
            packet_path = root / packet["authorization_target"]["packet_path"]
            packet_document = yaml.safe_load(packet_path.read_text())
            packet_document["packet_id"] = stale_packet_id
            packet_path.write_text(yaml.safe_dump(packet_document, sort_keys=False))

            preflight_payload = {
                "batch_id": "B900",
                "computed_packet_id": stale_packet_id,
                "packet_structure_ready": True,
                "findings": [],
            }
            stale_preflight_id = (
                "B900-packet-preflight-sha256:"
                + MODULE.sha256_bytes(
                    json.dumps(
                        preflight_payload,
                        sort_keys=True,
                        separators=(",", ":"),
                    ).encode()
                )
            )
            preflight_path = root / "artifacts/frontier/B900/packet-preflight.json"
            preflight_path.write_text(
                json.dumps({**preflight_payload, "preflight_id": stale_preflight_id}, sort_keys=True)
            )

            target_path = root / packet["authorization_target"]["target_path"]
            target_payload = yaml.safe_load(target_path.read_text())
            target_payload.pop("target_id")
            target_payload["preflight_id"] = stale_preflight_id
            target_payload["exact_object"]["packet"].update(
                {
                    "packet_id": stale_packet_id,
                    "file_sha256": MODULE.sha256_bytes(packet_path.read_bytes()),
                }
            )
            target_payload["exact_object"]["structural_preflight"].update(
                {
                    "preflight_id": stale_preflight_id,
                    "file_sha256": MODULE.sha256_bytes(preflight_path.read_bytes()),
                }
            )
            target_id, target_sha = write_target(root, target_payload)
            packet["authorization_target"].update(
                {
                    "target_id": target_id,
                    "target_file_sha256": target_sha,
                    "packet_id": stale_packet_id,
                    "preflight_id": stale_preflight_id,
                }
            )
            result = MODULE.validate(packet, "draft", root)
            self.assertIn(
                "BATCH_PACKET_ID_NOT_DERIVED",
                {item["code"] for item in result["findings"]},
            )

    def test_consistently_copied_stale_source_identity_is_not_source_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet = make_workspace(root)
            stale_source = "source-sha256:prior-B899"
            target_path = root / packet["authorization_target"]["target_path"]
            target_payload = yaml.safe_load(target_path.read_text())
            target_payload.pop("target_id")
            target_payload["source_base_identity"] = stale_source
            target_payload["exact_object"]["reviewed_bindings"][2]["identity"] = stale_source
            target_id, target_sha = write_target(root, target_payload)
            packet["authorization_target"].update(
                {
                    "target_id": target_id,
                    "target_file_sha256": target_sha,
                    "source_base_identity": stale_source,
                }
            )
            result = MODULE.validate(packet, "draft", root)
            self.assertIn(
                "TARGET_SOURCE_BASE_IDENTITY_MISMATCH",
                {item["code"] for item in result["findings"]},
            )

    def test_live_drift_after_snapshot_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet = make_workspace(root, frozen=True)
            (root / "artifacts/frontier/B900-launcher-preflight.json").write_text("{}")
            result = MODULE.validate(packet, "frozen", root)
            self.assertIn("LIVE_SOURCE_DRIFT", {item["code"] for item in result["findings"]})

    def test_frozen_entry_uses_filtered_project_snapshot_without_copy_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet = make_workspace(root, frozen=True)
            result = MODULE.validate(packet, "frozen", root)

            self.assertTrue(result["entry_schema_ready"], result["findings"])
            self.assertNotIn("snapshot_root", packet)
            self.assertNotIn("snapshot_inputs", packet)
            manifest = yaml.safe_load((root / packet["snapshot_manifest"]["path"]).read_text())
            self.assertEqual(PROJECT_SNAPSHOT.SCHEMA, manifest["schema"])
            self.assertNotIn("inputs", manifest)

    def test_legacy_copied_snapshot_cannot_authorize_new_entry(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet = make_workspace(root, frozen=True)
            manifest_path = root / packet["snapshot_manifest"]["path"]
            legacy = {
                "snapshot_id": "entry-R899-sha256:" + "0" * 64,
                "inputs": [],
            }
            manifest_path.write_text(yaml.safe_dump(legacy, sort_keys=False))
            packet["snapshot_id"] = legacy["snapshot_id"]
            packet["snapshot_manifest"].update(
                {
                    "snapshot_id": legacy["snapshot_id"],
                    "file_sha256": MODULE.sha256_bytes(manifest_path.read_bytes()),
                }
            )
            packet["packet_id"] = MODULE.validate(packet, "frozen", root)["computed_packet_id"]

            result = MODULE.validate(packet, "frozen", root)

            self.assertIn(
                "PROJECT_SNAPSHOT_INVALID",
                {finding["code"] for finding in result["findings"]},
            )

    def test_manifest_member_tampering_fails_before_entry_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet = make_workspace(root, frozen=True)
            manifest_path = root / packet["snapshot_manifest"]["path"]
            manifest = yaml.safe_load(manifest_path.read_text())
            manifest["members"][0]["file_sha256"] = "0" * 64
            manifest["snapshot_id"] = PROJECT_SNAPSHOT.compute_snapshot_id(manifest)
            manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False))
            packet["snapshot_id"] = manifest["snapshot_id"]
            packet["snapshot_manifest"].update(
                {
                    "snapshot_id": manifest["snapshot_id"],
                    "file_sha256": MODULE.sha256_bytes(manifest_path.read_bytes()),
                }
            )
            packet["packet_id"] = MODULE.validate(packet, "frozen", root)["computed_packet_id"]

            result = MODULE.validate(packet, "frozen", root)

            self.assertIn(
                "PROJECT_SNAPSHOT_INVALID",
                {finding["code"] for finding in result["findings"]},
            )

    def test_generation_two_requires_recovery_lineage(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet = make_workspace(root)
            packet["campaign_generation"] = 2
            packet.pop("recovery_lineage")
            result = MODULE.validate(packet, "draft", root)
            codes = {item["code"] for item in result["findings"]}
            self.assertIn("REQUIRED_FIELD_MISSING", codes)
            self.assertIn("RECOVERY_LINEAGE_REQUIRED", codes)

    def test_authorization_must_still_be_pending(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet = make_workspace(root)
            packet["authorization_state"] = "authorized"
            result = MODULE.validate(packet, "draft", root)
            self.assertIn("AUTHORIZATION_STATE_INVALID", {item["code"] for item in result["findings"]})

    def test_legacy_audit_retains_generation_guard(self) -> None:
        packet = {"review_kind": "entry", "campaign_generation": 2, "selected_batches": ["B001"]}
        result = MODULE.validate(packet, "audit")
        self.assertIn("RECOVERY_LINEAGE_REQUIRED", {item["code"] for item in result["findings"]})

    def test_entry_requires_recoverable_workflow_source_binding(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet = make_workspace(root)
            packet.pop("workflow_source_binding")

            result = MODULE.validate(packet, "draft", root)

            codes = {item["code"] for item in result["findings"]}
            self.assertIn("REQUIRED_FIELD_MISSING", codes)
            self.assertIn("WORKFLOW_SOURCE_BINDING_INVALID", codes)

    def test_entry_rejects_changed_workflow_source_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet = make_workspace(root)
            source_path = root / packet["workflow_source_binding"]["source_snapshot"]["path"]
            source_path.write_text("resolver: changed\n")

            result = MODULE.validate(packet, "draft", root)

            self.assertIn(
                "WORKFLOW_SOURCE_BINDING_INVALID",
                {item["code"] for item in result["findings"]},
            )

    def test_entry_rejects_self_consistent_but_incomplete_workflow_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet = make_workspace(root)
            binding = packet["workflow_source_binding"]
            snapshot_path = root / binding["source_snapshot"]["path"]
            snapshot = yaml.safe_load(snapshot_path.read_text())
            snapshot["members"] = [
                item
                for item in snapshot["members"]
                if item["path"] != "references/campaign-cycle.md"
            ]
            snapshot_path.write_text(yaml.safe_dump(snapshot, sort_keys=False))
            snapshot_digest = MODULE.sha256_bytes(snapshot_path.read_bytes())
            binding["source_snapshot"].update(
                {
                    "identity": f"sha256:{snapshot_digest}",
                    "file_sha256": snapshot_digest,
                }
            )
            manifest_path = root / binding["source_manifest"]["path"]
            manifest = yaml.safe_load(manifest_path.read_text())
            manifest["snapshot_identity"] = f"sha256:{snapshot_digest}"
            manifest["members"] = [
                item
                for item in manifest["members"]
                if item["path"] != "references/campaign-cycle.md"
            ]
            manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False))
            manifest_digest = MODULE.sha256_bytes(manifest_path.read_bytes())
            binding["source_manifest"].update(
                {
                    "identity": f"sha256:{manifest_digest}",
                    "file_sha256": manifest_digest,
                }
            )

            result = MODULE.validate(packet, "draft", root)

            self.assertIn(
                "WORKFLOW_SOURCE_BINDING_INVALID",
                {item["code"] for item in result["findings"]},
            )

    def test_replan_workflow_source_binding_requires_and_accepts_prior_binding(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            binding = write_workflow_source_binding(root)
            binding["adoption_mode"] = "replan"
            binding["prior_binding"] = "sha256:prior-workflow-source"

            observed = validate_binding(
                binding,
                root,
                expected_adoption_mode="replan",
            )

            self.assertEqual(
                observed["source_snapshot"],
                binding["source_snapshot"]["identity"],
            )
            binding.pop("prior_binding")
            with self.assertRaisesRegex(ValueError, "requires prior_binding"):
                validate_binding(binding, root, expected_adoption_mode="replan")

    def test_v1_workflow_source_closure_remains_immutable(self) -> None:
        skill_root = Path(__file__).parent.parent
        normative_references = {
            path.relative_to(skill_root).as_posix()
            for path in (skill_root / "references").glob("*.md")
        }
        production_scripts = {
            path.relative_to(skill_root).as_posix()
            for path in (skill_root / "scripts").glob("*.py")
            if not path.name.startswith("test_")
            and path.name != "validate_frontier_skill_bundle.py"
        }
        coordinator_config = {"agents/openai.yaml"}
        worker_sources = {
            f"workers/{skill_name}/{relative}"
            for skill_name in (
                "grill-frontier",
                "research-frontier",
                "review-frontier",
                "run-frontier-batch",
            )
            for relative in ("SKILL.md", "agents/openai.yaml")
        }
        post_v1_only = {
            "references/batch-code-execution.md",
            "references/batch-current.md",
            "references/batch-evaluation.md",
            "references/batch-packet-format.md",
            "references/batch-result.md",
            "references/entry-review-legacy.md",
            "references/evaluation-protocol.md",
            "references/finding-effects.md",
            "references/provenance-and-identity.md",
            "references/reflection-analysis.md",
            "references/reflection-calibration.md",
            "references/replan-review.md",
            "references/user-decisions.md",
            "references/user-facing-handoff.md",
            "scripts/evaluation_target_contract.py",
            "scripts/engineering_check_plan.py",
            "scripts/frontier_provenance_cli.py",
            "scripts/frontier_references.py",
            "scripts/frontier_review_cli.py",
            "scripts/frontier_batch.py",
            "scripts/run_workflow_checks.py",
        }

        self.assertEqual(
            set(GOVERNING_PATHS),
            (
                {"SKILL.md"}
                | coordinator_config
                | normative_references
                | production_scripts
                | worker_sources
            )
            - post_v1_only,
        )
        self.assertEqual(
            CLOSURE_PATHS_BY_CONTRACT[CLOSURE_CONTRACT_V1],
            GOVERNING_PATHS,
        )

    def test_source_closure_rejects_self_consistent_extra_member(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            binding = write_workflow_source_binding(root)
            snapshot_path = root / binding["source_snapshot"]["path"]
            manifest_path = root / binding["source_manifest"]["path"]
            snapshot = yaml.safe_load(snapshot_path.read_text())
            manifest = yaml.safe_load(manifest_path.read_text())
            content = "def test_release_only(): pass\n"
            snapshot["members"].append(
                {"path": "scripts/test_release_only.py", "content": content}
            )
            manifest["members"].append(
                {
                    "path": "scripts/test_release_only.py",
                    "size": len(content.encode()),
                    "sha256": MODULE.sha256_bytes(content.encode()),
                }
            )
            snapshot_raw = yaml.safe_dump(snapshot, sort_keys=False).encode()
            snapshot_identity = f"sha256:{MODULE.sha256_bytes(snapshot_raw)}"
            manifest["snapshot_identity"] = snapshot_identity
            manifest_raw = yaml.safe_dump(manifest, sort_keys=False).encode()

            with self.assertRaisesRegex(ValueError, "extra=scripts/test_release_only.py"):
                validate_source_closure(
                    manifest_raw,
                    snapshot_raw,
                    snapshot_identity,
                )

    def test_historical_closure_remains_valid_after_a_new_current_version(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            binding = write_workflow_source_binding(root)
            manifest_raw = (root / binding["source_manifest"]["path"]).read_bytes()
            snapshot_raw = (root / binding["source_snapshot"]["path"]).read_bytes()
            v2 = "frontier-workflow-source-closure/2-test"
            original_current = WORKFLOW_SOURCE.CURRENT_CLOSURE_CONTRACT
            try:
                WORKFLOW_SOURCE.CLOSURE_PATHS_BY_CONTRACT[v2] = frozenset(
                    set(GOVERNING_PATHS) | {"references/future-contract.md"}
                )
                WORKFLOW_SOURCE.CURRENT_CLOSURE_CONTRACT = v2

                validate_source_closure(
                    manifest_raw,
                    snapshot_raw,
                    binding["source_snapshot"]["identity"],
                )
            finally:
                WORKFLOW_SOURCE.CURRENT_CLOSURE_CONTRACT = original_current
                WORKFLOW_SOURCE.CLOSURE_PATHS_BY_CONTRACT.pop(v2, None)


if __name__ == "__main__":
    unittest.main()
