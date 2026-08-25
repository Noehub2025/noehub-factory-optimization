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
from frontier_provenance import (
    NodeRepository,
    attest,
    bind_authority,
    freeze_execution,
)
from frontier_provenance.stores import ArtifactSource, ProjectPortableStore
from frontier_review import prepare_review
from test_freeze_execution_baseline import write_bound_dispatch_draft
from test_frontier_review_preparation import write_entry


SCRIPT = Path(__file__).with_name("validate_batch_result.py")
SPEC = importlib.util.spec_from_file_location("validate_batch_result", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)
HASH = "a" * 64


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def file_binding(path: Path, root: Path, identity_field: str, identity: str) -> dict:
    return {
        "path": path.relative_to(root).as_posix(),
        "identity_field": identity_field,
        "identity": identity,
        "file_sha256": file_sha256(path),
    }


def write_line_identified_yaml(
    path: Path, document: dict, identity_field: str, prefix: str
) -> dict:
    payload = yaml.safe_dump(document, sort_keys=False, allow_unicode=True).encode()
    identity = prefix + hashlib.sha256(payload).hexdigest()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(f"{identity_field}: {identity}\n".encode() + payload)
    return yaml.safe_load(path.read_text())


def write_project_dispatch_fixture(root: Path, family: str) -> tuple[dict, dict, Path]:
    """Create one complete typed project dispatch without mocking validation."""

    if family not in {"current", "legacy"}:
        raise ValueError(f"unsupported dispatch family: {family}")

    frozen_input = root / "project/input.txt"
    frozen_input.parent.mkdir(parents=True)
    frozen_input.write_bytes(b"frozen input\n")
    frozen_inputs = [
        {
            "path": frozen_input.relative_to(root).as_posix(),
            "scope": "file",
            "identity": "sha256:" + file_sha256(frozen_input),
        }
    ]

    spec = write_entry(root)
    plan_path = root / "entry/plan.yaml"
    common = {
        "contract_version": MODULE.PROJECT_BATCH_PLAN_CONTRACT,
        "batch_id": "B001",
        "campaign_generation": 2,
        "route_id": "T900",
        "parallel_set": None,
        "work_kind": "code",
        "problem_epoch": 3,
        "representation_revision": 4,
        "result_contract_version": MODULE.RESULT_CONTRACT_V2,
        "identity_contract": MODULE.IDENTITY_CONTRACT,
        "changes_executable_candidate": False,
        "candidate_root_path": "candidates/B001/",
        "candidate_package_inventory_path": "artifacts/frontier/B001/package-inventory.yaml",
        "candidate_manifest_path": "artifacts/frontier/B001/candidate-manifest.yaml",
        "result_validation_path": "artifacts/frontier/B001/result-validation.json",
        "result_packet_path": "artifacts/frontier/B001/result.yaml",
        "execution_baseline_root": "artifacts/frontier/B001/execution-baseline",
        "maximum_spend": {"proposal_attempts": 1},
        "authorization_gate": "exact reviewed authorization",
        "stop_conditions": ["one result"],
    }
    preflight_path: Path | None = None
    preflight: dict | None = None
    if family == "current":
        common["execution_frozen_inputs"] = frozen_inputs
        packet = write_line_identified_yaml(
            plan_path, common, "batch_plan_id", "B001-plan-sha256:"
        )
        dispatch_identity = packet["batch_plan_id"]
    else:
        common.update(
            {
                "packet_path": plan_path.relative_to(root).as_posix(),
                "packet_preflight_path": "artifacts/frontier/B001/preflight.json",
                "workflow_source_identity": "sha256:" + HASH,
            }
        )
        packet_payload = yaml.safe_dump(
            common, sort_keys=False, allow_unicode=True
        ).encode()
        packet = {
            **common,
            "packet_id": "B001-packet-sha256:"
            + hashlib.sha256(packet_payload).hexdigest(),
        }
        plan_path.write_text(yaml.safe_dump(packet, sort_keys=False, allow_unicode=True))
        dispatch_identity = packet["packet_id"]
        preflight_path = root / packet["packet_preflight_path"]
        preflight_path.parent.mkdir(parents=True, exist_ok=True)
        preflight_payload = {
            "computed_packet_id": packet["packet_id"],
            "packet_payload_sha256": hashlib.sha256(packet_payload).hexdigest(),
            "packet_structure_ready": True,
            "blocking_findings": [],
            "repair_findings": [],
        }
        preflight = {
            "preflight_id": "B001-packet-preflight-sha256:"
            + hashlib.sha256(
                json.dumps(
                    preflight_payload,
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=False,
                ).encode()
            ).hexdigest(),
            **preflight_payload,
        }
        preflight_path.write_text(
            json.dumps(preflight, sort_keys=True, separators=(",", ":")) + "\n"
        )

    decision_parent = root / "artifacts/frontier/B001/entry-R900-complete"
    prepared = prepare_review(spec, root, decision_parent)
    assert prepared["status"] == "SEALED", prepared
    decision_bundle = decision_parent / "snapshot"
    repository = NodeRepository(decision_parent / "nodes")
    decision = repository.load(prepared["decision_root"])

    entry_review_path = root / "artifacts/frontier/B001/entry-R900.md"
    entry_review_path.parent.mkdir(parents=True, exist_ok=True)
    entry_review_path.write_text("# Entry review\n\nResult: AUTHORIZATION_READY\n")
    review_bundle = entry_review_path.with_name(
        f"{entry_review_path.stem}-review-report"
    )
    review_content = ProjectPortableStore().capture(
        "review",
        [ArtifactSource("project/review/entry-R900.md", entry_review_path)],
        review_bundle,
        project_root=root,
    )
    attestation = attest(
        decision,
        validation_report_root=review_content["content_root"],
        verdict="ready",
        findings=[],
    )

    authority_source = root / "artifacts/frontier/B001/authority.yaml"
    authority_source.write_text("decision: exact reviewed authorization\n")
    authority_bundle = root / "artifacts/frontier/B001/authority-content"
    authority_content = ProjectPortableStore().capture(
        "authority",
        [ArtifactSource("project/authority/authorization.yaml", authority_source)],
        authority_bundle,
        project_root=root,
    )
    authority = bind_authority(
        authority_root=authority_content["content_root"],
        decision=decision,
        validation=attestation,
        decision_bundle=decision_bundle,
    )
    repository.write_all((attestation, authority))

    plan_binding = {
        "path": plan_path.relative_to(root).as_posix(),
        ("plan_id" if family == "current" else "packet_id"): dispatch_identity,
        "file_sha256": file_sha256(plan_path),
    }
    acknowledgment_document = {
        "contract_version": MODULE.PROJECT_ACKNOWLEDGMENT_CONTRACT,
        "batch_id": "B001",
        "acknowledgment": "accepted",
        "batch_plan": plan_binding,
        "decision_root": decision["node_id"],
        "decision_content": {
            "path": decision_bundle.relative_to(root).as_posix(),
            "root": prepared["content_root"],
            "manifest_file_sha256": file_sha256(decision_bundle / "manifest.json"),
        },
        "entry_review": {
            "path": entry_review_path.relative_to(root).as_posix(),
            "result": "AUTHORIZATION_READY",
            "file_sha256": file_sha256(entry_review_path),
        },
        "entry_attestation": attestation["node_id"],
        "authority": {
            "node": authority["node_id"],
            "content_path": authority_bundle.relative_to(root).as_posix(),
            "content_root": authority_content["content_root"],
            "content_manifest_sha256": file_sha256(authority_bundle / "manifest.json"),
        },
    }
    if family == "legacy":
        assert preflight_path is not None and preflight is not None
        acknowledgment_document["packet_preflight"] = {
            "path": preflight_path.relative_to(root).as_posix(),
            "preflight_id": preflight["preflight_id"],
            "file_sha256": file_sha256(preflight_path),
        }
    acknowledgment_path = root / "artifacts/frontier/B001/acknowledgment.yaml"
    acknowledgment = write_line_identified_yaml(
        acknowledgment_path,
        acknowledgment_document,
        "acknowledgment_id",
        "B001-acknowledgment-sha256:",
    )

    state_document = {
        "decision_root": decision["node_id"],
        "authority_id": authority["node_id"],
        "acknowledgment": {"identity": acknowledgment["acknowledgment_id"]},
        "plan": {"identity": dispatch_identity},
        "worker_may_start": False,
        "release_condition": (
            "exact execution-start.yaml with finding-free execution verification"
        ),
    }
    if family == "current":
        state_document["execution_frozen_inputs"] = copy.deepcopy(frozen_inputs)
    state_path = root / "artifacts/frontier/B001/execution-state.yaml"
    state_path.write_text(yaml.safe_dump(state_document, sort_keys=False))
    state_sources = [
        ArtifactSource("project/state/plan.yaml", plan_path),
        ArtifactSource("project/state/acknowledgment.yaml", acknowledgment_path),
        ArtifactSource("project/state/execution-state.yaml", state_path),
    ]
    if family == "legacy":
        assert preflight_path is not None
        state_sources.append(
            ArtifactSource("project/state/preflight.json", preflight_path)
        )
    else:
        state_sources.append(
            ArtifactSource(
                "project/state/frozen-inputs/project/input.txt", frozen_input
            )
        )
    execution_bundle = root / packet["execution_baseline_root"]
    execution_content = ProjectPortableStore().capture(
        "state", state_sources, execution_bundle, project_root=root
    )
    execution = freeze_execution(
        authority=authority,
        starting_state_root=execution_content["content_root"],
    )
    repository.write(execution)

    verification_path = root / "artifacts/frontier/B001/execution-verification.json"
    verification_path.write_text(
        json.dumps(
            {
                "ready": True,
                "unresolved_live_facts": [],
                "static_chain_verified": True,
                "root_id": execution["node_id"],
                "consequence": "execution",
            },
            sort_keys=True,
        )
        + "\n"
    )
    start_document = {
        "contract_version": MODULE.PROJECT_EXECUTION_START_CONTRACT,
        "batch_id": "B001",
        "campaign_generation": packet["campaign_generation"],
        "plan_id": dispatch_identity,
        "acknowledgment_id": acknowledgment["acknowledgment_id"],
        "candidate_root": packet["candidate_root_path"],
        "result_validation": packet["result_validation_path"],
        "result": packet["result_packet_path"],
        "worker_may_start": True,
        "decision_root": decision["node_id"],
        "authority_id": authority["node_id"],
        "execution_node": execution["node_id"],
        "starting_state_root": execution_content["content_root"],
        "execution_verification": {
            "path": verification_path.relative_to(root).as_posix(),
            "file_sha256": file_sha256(verification_path),
            "ready": True,
            "unresolved_live_facts": [],
        },
    }
    execution_start_path = root / "artifacts/frontier/B001/execution-start.yaml"
    execution_start = write_line_identified_yaml(
        execution_start_path,
        start_document,
        "execution_start_id",
        "B001-execution-start-sha256:",
    )

    result = base_result()
    result.update(
        {
            "result_packet_path": packet["result_packet_path"],
            "batch_id": packet["batch_id"],
            "campaign_generation": packet["campaign_generation"],
            "route_id": packet["route_id"],
            "parallel_set": packet["parallel_set"],
            "work_kind": packet["work_kind"],
            "problem_epoch": packet["problem_epoch"],
            "representation_revision": packet["representation_revision"],
            "result_contract_version": packet["result_contract_version"],
            "changes_executable_candidate": False,
            "outcome": "blocked",
            "materialization_state": "not-started",
            "acknowledgment": file_binding(
                acknowledgment_path,
                root,
                "acknowledgment_id",
                acknowledgment["acknowledgment_id"],
            ),
            "execution_start": file_binding(
                execution_start_path,
                root,
                "execution_start_id",
                execution_start["execution_start_id"],
            ),
        }
    )
    if family == "current":
        for field in MODULE.LEGACY_RESULT_BINDING_FIELDS:
            result.pop(field, None)
        result.update(
            {
                "batch_plan": file_binding(
                    plan_path, root, "batch_plan_id", packet["batch_plan_id"]
                ),
                "decision_root": decision["node_id"],
            }
        )
    else:
        assert preflight_path is not None and preflight is not None
        result.update(
            {
                "packet_path": packet["packet_path"],
                "packet_id": packet["packet_id"],
                "workflow_source_identity": packet["workflow_source_identity"],
                "packet_preflight": file_binding(
                    preflight_path,
                    root,
                    "preflight_id",
                    preflight["preflight_id"],
                ),
            }
        )
    return packet, result, frozen_input


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
        "result_contract_version": MODULE.RESULT_CONTRACT_V2,
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
        "result_contract_version": MODULE.RESULT_CONTRACT_V2,
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
        "implementation_review_state": "IMPLEMENTATION_READY",
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


def current_project_packet() -> dict:
    packet = base_packet()
    for field in (
        "packet_path",
        "packet_id",
        "packet_preflight_path",
        "workflow_source_identity",
        "workflow_source_binding",
    ):
        packet.pop(field, None)
    packet.update(
        {
            "contract_version": MODULE.PROJECT_BATCH_PLAN_CONTRACT,
            "batch_plan_id": "B900-plan-sha256:" + "b" * 64,
            "identity_contract": MODULE.IDENTITY_CONTRACT,
            "execution_frozen_inputs": [],
        }
    )
    return packet


def current_project_result(packet: dict | None = None) -> dict:
    packet = packet or current_project_packet()
    result = base_result()
    for field in MODULE.LEGACY_RESULT_BINDING_FIELDS:
        result.pop(field, None)
    result["batch_plan"] = {
        "path": "artifacts/frontier/B900/B900-plan.yaml",
        "identity_field": "batch_plan_id",
        "identity": packet["batch_plan_id"],
        "file_sha256": "c" * 64,
    }
    result["decision_root"] = "frontier-decision-root-sha256:" + "d" * 64
    return result


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
    review_path = root / "artifacts/frontier/B900/implementation-review.md"
    review_path.write_text(
        "---\n"
        "type: Optimization Frontier Implementation Review\n"
        "status: complete\n"
        "review_result: IMPLEMENTATION_READY\n"
        f"candidate_id: {candidate_id}\n"
        "---\n\n"
        f"Candidate: {candidate_id}\n"
    )
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
        "implementation_review": {
            "path": review_path.relative_to(root).as_posix(),
            "file_sha256": hashlib.sha256(review_path.read_bytes()).hexdigest(),
            "review_result": "IMPLEMENTATION_READY",
            "candidate_id": candidate_id,
        },
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
    policy = packet.get("publication_policy")
    if isinstance(policy, dict):
        charge_amount = policy.get("charge_amount")
        result["planned_spend"] = charge_amount
        result["actual_spend"] = charge_amount
        result["accounting_evidence"] = (
            f"authoritative output {packet['candidate_package_inventory_path']} "
            f"sha256:{inventory['inventory_sha256']}"
        )


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


def routine_evaluation_target() -> dict:
    target = formal_evaluation_target()
    target.update(
        {
            "contract_version": "frontier-evaluation-target/2",
            "result_contract_version": "frontier-batch-result/2",
            "mode": "routine-local",
            "sample_ceiling": {"runs": 16},
            "resource_ceiling": {"local_minutes": 5},
            "routine_slot": {
                "contract_version": "frontier-routine-follow-up/1",
                "slot_id": "slot-B900-screen",
                "materialization_batch_id": "B900",
                "follow_up_batch_id": "B901",
                "origin_decision_root": "frontier-decision-root-sha256:" + HASH,
                "origin_authority_root": "frontier-authority-root-sha256:" + HASH,
                "template_root": "sha256:" + HASH,
            },
            "protocol": {
                "contract_version": "frontier-evaluation-protocol/1",
                "content_root": "frontier-content-root-sha256:" + HASH,
                "protocol_id": "protocol-sha256:" + HASH,
                "invalidation_key": "protocol-key-sha256:" + HASH,
            },
            "calibration": {
                "contract_version": "frontier-protocol-calibration-result/1",
                "content_root": "frontier-content-root-sha256:" + HASH,
                "calibration_id": "calibration-sha256:" + HASH,
                "protocol_invalidation_key": "protocol-key-sha256:" + HASH,
            },
            "consequence_limit": "B evidence only",
            "prohibited_consequences": sorted(
                {
                    "E",
                    "formal Slot H",
                    "sealed confirmation",
                    "integration",
                    "incumbent use",
                    "promotion",
                    "submission",
                    "external action",
                    "paid action",
                    "publication",
                    "strength claim",
                    "direct next-B authority",
                }
            ),
            "evidence_scope": {
                "evidence_class": "b-evidence",
                "exposure": "development",
                "confirmation": "none",
                "comparator_scope": "one fixed development comparator",
                "data_scope": "one fixed development sample",
                "workload_scope": "one local workload",
                "scenario_scope": "one named scenario set",
                "metric_scope": "one predeclared metric set",
                "mechanism_grain": "whole-package-at-most",
                "transfer_scope": "local-only",
            },
        }
    )
    target.pop("slot_h_contract")
    target["candidate"]["collection_root"] = "sha256:" + HASH
    target["implementation_review"] = {
        "result": "IMPLEMENTATION_READY",
        "derivation": "unique finding-free review of the derived candidate",
    }
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


def write_check_report(
    root: Path,
    relative: str,
    snapshot_id: str,
    result: str,
) -> dict[str, str]:
    log = f"local-check: {result}\n"
    report = {
        "contract_version": MODULE.ENGINEERING_CHECK_REPORT_CONTRACT,
        "snapshot_id": snapshot_id,
        "checks": [
            {
                "id": "local-check",
                "argv_sha256": MODULE.command_sha256(["local-check"]),
                "result": result,
                "exit_status": 0 if result == "pass" else (None if result == "blocked" else 1),
                "log": log,
                "log_sha256": hashlib.sha256(log.encode()).hexdigest(),
            }
        ],
    }
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, sort_keys=True) + "\n")
    return {
        "path": relative,
        "file_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def post_check_publication_workspace(root: Path) -> tuple[dict, dict, Path]:
    packet = base_packet()
    packet["engineering_check_plan"] = {
        "contract_version": "frontier-engineering-check-plan/1",
        "checks": [
            {
                "id": "local-check",
                "command": ["local-check"],
                "effect_costs": {"local-check": 1},
            }
        ],
        "effect_limits": {"local-check": 2},
        "evidence_use": "engineering-only",
    }
    evidence_relative = "artifacts/frontier/B900/prepublication-evidence.json"
    packet["publication_policy"] = {
        "contract_version": "frontier-authoritative-output-publication/1",
        "charge_event": MODULE.POST_CHECK_CHARGE,
        "charge_amount": "1 proposal attempt",
        "charge_basis": {
            "kind": "workflow-default",
            "path": "parents/R8.yaml",
            "file_sha256": "a" * 64,
            "locator": "reviewed parent set contains no charge event",
        },
        "repair_mode": "deterministic-fidelity-only",
        "effect_scope": "deterministic-local-checks-only",
        "authoritative_output_path": packet["candidate_package_inventory_path"],
        "engineering_evidence_path": evidence_relative,
    }
    result = base_result()
    seed_materialized_candidate(root, packet, result)
    inventory_path = root / packet["candidate_package_inventory_path"]
    inventory_digest = hashlib.sha256(inventory_path.read_bytes()).hexdigest()
    reports: list[dict[str, str]] = []
    snapshots = ("snapshot-sha256:" + "b" * 64, "snapshot-sha256:" + inventory_digest)
    for sequence, (snapshot_id, check_result) in enumerate(
        zip(snapshots, ("fail", "pass")),
        start=1,
    ):
        report_relative = f"artifacts/frontier/B900/check-report-{sequence}.json"
        report_path = root / report_relative
        log = f"local-check: {check_result}\n"
        report_document = {
            "contract_version": MODULE.ENGINEERING_CHECK_REPORT_CONTRACT,
            "snapshot_id": snapshot_id,
            "checks": [
                {
                    "id": "local-check",
                    "argv_sha256": MODULE.command_sha256(["local-check"]),
                    "result": check_result,
                    "exit_status": 0 if check_result == "pass" else 1,
                    "log": log,
                    "log_sha256": hashlib.sha256(log.encode()).hexdigest(),
                }
            ],
        }
        report_path.write_text(json.dumps(report_document, sort_keys=True) + "\n")
        reports.append(
            {
                "path": report_relative,
                "file_sha256": hashlib.sha256(report_path.read_bytes()).hexdigest(),
            }
        )
    evidence = {
        "contract_version": MODULE.ENGINEERING_EVIDENCE_CONTRACT,
        "publication_policy": {
            "charge_event": MODULE.POST_CHECK_CHARGE,
            "charge_amount": "1 proposal attempt",
            "authoritative_output_path": packet["candidate_package_inventory_path"],
        },
        "attempts": [
            {
                "sequence": 1,
                "snapshot_id": snapshots[0],
                "snapshot_file_sha256": "b" * 64,
                "outcome": "fail",
                "checks": [{"id": "local-check", "result": "fail"}],
                "check_report": reports[0],
                "effects": {"local-check": 1},
            },
            {
                "sequence": 2,
                "snapshot_id": snapshots[1],
                "snapshot_file_sha256": inventory_digest,
                "outcome": "pass",
                "checks": [{"id": "local-check", "result": "pass"}],
                "check_report": reports[1],
                "effects": {"local-check": 1},
            },
        ],
        "effect_limits": {"local-check": 2},
        "effects": {"local-check": 2},
        "status": "pass",
        "official_output": {
            "path": packet["candidate_package_inventory_path"],
            "file_sha256": inventory_digest,
        },
        "evidence_use": "engineering-only",
    }
    evidence_path = root / evidence_relative
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(json.dumps(evidence, sort_keys=True) + "\n")
    result["engineering_validation"] = [
        {
            "contract_version": MODULE.ENGINEERING_EVIDENCE_CONTRACT,
            "path": evidence_relative,
            "file_sha256": hashlib.sha256(evidence_path.read_bytes()).hexdigest(),
        }
    ]
    result["planned_spend"] = packet["publication_policy"]["charge_amount"]
    result["actual_spend"] = packet["publication_policy"]["charge_amount"]
    result["accounting_evidence"] = (
        f"authoritative output {packet['candidate_package_inventory_path']} "
        f"sha256:{inventory_digest}"
    )
    return packet, result, evidence_path


class BatchResultValidationTests(unittest.TestCase):
    def test_review_repair_history_accepts_one_nonpositive_review_per_earlier_pass(self) -> None:
        evidence = {
            "review_repair_history": [
                {
                    "after_attempt_sequence": 1,
                    "review_chain": {
                        "path": "artifacts/frontier/B900/review-handoff",
                        "handoff_id": "frontier-provenance-handoff-sha256:" + "a" * 64,
                    },
                }
            ]
        }
        findings: list[dict[str, str]] = []
        attestation = {
            "role": "attestation",
            "payload": {
                "verdict": "repair",
                "findings": [{"effect": "repair", "code": "IMPLEMENTATION_FIDELITY"}],
            },
        }
        with mock.patch.object(
            MODULE,
            "verify_handoff",
            return_value={
                "root_id": "frontier-node-sha256:" + "b" * 64,
                "handoff_id": evidence["review_repair_history"][0]["review_chain"]["handoff_id"],
            },
        ), mock.patch.object(MODULE, "NodeRepository") as repository:
            repository.return_value.load.return_value = attestation
            MODULE.validate_review_repair_history(evidence, [1], Path("."), findings)

        self.assertEqual([], findings)

    def test_review_repair_history_rejects_an_unbound_earlier_pass(self) -> None:
        findings: list[dict[str, str]] = []

        MODULE.validate_review_repair_history(
            {"review_repair_history": []}, [1], Path("."), findings
        )

        self.assertIn(
            "PREPUBLICATION_REVIEW_REPAIR_HISTORY_INVALID",
            {finding["code"] for finding in findings},
        )

    def test_post_check_fail_repair_pass_binds_final_official_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet, result, _ = post_check_publication_workspace(root)

            validation = MODULE.validate(
                result,
                "draft",
                packet,
                repo_root=root,
                check_dispatch=False,
            )

            self.assertTrue(validation["result_structure_ready"], validation["findings"])

    def test_current_reviewed_publication_derives_output_without_policy_copy(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet, result, evidence_path = post_check_publication_workspace(root)
            packet.pop("publication_policy")
            evidence = json.loads(evidence_path.read_text())
            evidence.pop("publication_policy")
            evidence_path.write_text(json.dumps(evidence, sort_keys=True) + "\n")
            result["engineering_validation"][0]["file_sha256"] = hashlib.sha256(
                evidence_path.read_bytes()
            ).hexdigest()
            inventory = yaml.safe_load(
                (root / packet["candidate_package_inventory_path"]).read_text()
            )
            result["accounting_evidence"] = (
                f"official inventory {inventory['inventory_id']}"
            )

            validation = MODULE.validate(
                result,
                "draft",
                packet,
                repo_root=root,
                check_dispatch=False,
            )

            self.assertTrue(validation["result_structure_ready"], validation["findings"])

    def test_post_check_rejects_cumulative_effect_limit_exceeded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet, result, evidence_path = post_check_publication_workspace(root)
            evidence = json.loads(evidence_path.read_text())
            packet["engineering_check_plan"]["effect_limits"]["local-check"] = 1
            evidence["effect_limits"]["local-check"] = 1
            evidence_path.write_text(json.dumps(evidence, sort_keys=True) + "\n")
            result["engineering_validation"][0]["file_sha256"] = hashlib.sha256(
                evidence_path.read_bytes()
            ).hexdigest()

            validation = MODULE.validate(
                result,
                "draft",
                packet,
                repo_root=root,
                check_dispatch=False,
            )

            self.assertIn(
                "PREPUBLICATION_EFFECT_LIMIT_EXCEEDED",
                {finding["code"] for finding in validation["findings"]},
            )

    def test_post_check_rejects_final_snapshot_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet, result, evidence_path = post_check_publication_workspace(root)
            evidence = json.loads(evidence_path.read_text())
            evidence["attempts"][-1]["snapshot_file_sha256"] = "c" * 64
            evidence_path.write_text(json.dumps(evidence, sort_keys=True) + "\n")
            result["engineering_validation"][0]["file_sha256"] = hashlib.sha256(
                evidence_path.read_bytes()
            ).hexdigest()

            validation = MODULE.validate(
                result,
                "draft",
                packet,
                repo_root=root,
                check_dispatch=False,
            )

            self.assertIn(
                "PREPUBLICATION_FINAL_SNAPSHOT_MISMATCH",
                {finding["code"] for finding in validation["findings"]},
            )

    def test_post_check_effect_exhaustion_can_end_without_official_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet = base_packet()
            evidence_relative = "artifacts/frontier/B900/prepublication-evidence.json"
            packet["engineering_check_plan"] = {
                "contract_version": "frontier-engineering-check-plan/1",
                "checks": [
                    {
                        "id": "local-check",
                        "command": ["local-check"],
                        "effect_costs": {"local-check": 1},
                    }
                ],
                "effect_limits": {"local-check": 1},
                "evidence_use": "engineering-only",
            }
            packet["publication_policy"] = {
                "contract_version": "frontier-authoritative-output-publication/1",
                "charge_event": MODULE.POST_CHECK_CHARGE,
                "charge_amount": "1 proposal attempt",
                "charge_basis": {
                    "kind": "workflow-default",
                    "path": "parents/R8.yaml",
                    "file_sha256": "a" * 64,
                    "locator": "reviewed parent set contains no charge event",
                },
                "repair_mode": "deterministic-fidelity-only",
                "effect_scope": "deterministic-local-checks-only",
                "authoritative_output_path": packet["candidate_package_inventory_path"],
                "engineering_evidence_path": evidence_relative,
            }
            report_binding = write_check_report(
                root,
                "artifacts/frontier/B900/check-report-1.json",
                "snapshot-sha256:" + "b" * 64,
                "fail",
            )
            evidence = {
                "contract_version": MODULE.ENGINEERING_EVIDENCE_CONTRACT,
                "publication_policy": {
                    "charge_event": MODULE.POST_CHECK_CHARGE,
                    "charge_amount": "1 proposal attempt",
                    "authoritative_output_path": packet["candidate_package_inventory_path"],
                },
                "attempts": [
                    {
                        "sequence": 1,
                        "snapshot_id": "snapshot-sha256:" + "b" * 64,
                        "snapshot_file_sha256": "b" * 64,
                        "outcome": "fail",
                        "checks": [{"id": "local-check", "result": "fail"}],
                        "check_report": report_binding,
                        "effects": {"local-check": 1},
                    }
                ],
                "effect_limits": {"local-check": 1},
                "effects": {"local-check": 1},
                "status": "fail",
                "official_output": None,
                "evidence_use": "engineering-only",
            }
            evidence_path = root / evidence_relative
            evidence_path.parent.mkdir(parents=True, exist_ok=True)
            evidence_path.write_text(json.dumps(evidence, sort_keys=True) + "\n")
            result = base_result()
            result.update(
                {
                    "outcome": "failed",
                    "materialization_state": "partial",
                    "candidate_manifest": None,
                    "candidate_identity": None,
                    "source_result_identity": None,
                    "implementation_review_state": "not-applicable",
                    "engineering_validation": [
                        {
                            "contract_version": MODULE.ENGINEERING_EVIDENCE_CONTRACT,
                            "path": evidence_relative,
                            "file_sha256": hashlib.sha256(
                                evidence_path.read_bytes()
                            ).hexdigest(),
                        }
                    ],
                }
            )

            validation = MODULE.validate(
                result,
                "draft",
                packet,
                repo_root=root,
                check_dispatch=False,
            )

            self.assertTrue(validation["result_structure_ready"], validation["findings"])

    def test_post_check_publication_supports_deterministic_noncode_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output_relative = "artifacts/frontier/B900/design.md"
            evidence_relative = "artifacts/frontier/B900/prepublication-evidence.json"
            output_path = root / output_relative
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text("# Frozen design\n")
            output_digest = hashlib.sha256(output_path.read_bytes()).hexdigest()
            packet = base_packet()
            packet.update(
                {
                    "work_kind": "design",
                    "changes_executable_candidate": False,
                    "engineering_check_plan": {
                        "contract_version": "frontier-engineering-check-plan/1",
                        "checks": [
                            {
                                "id": "local-check",
                                "command": ["local-check"],
                                "effect_costs": {"local-check": 1},
                            }
                        ],
                        "effect_limits": {"local-check": 1},
                        "evidence_use": "engineering-only",
                    },
                    "publication_policy": {
                        "contract_version": "frontier-authoritative-output-publication/1",
                        "charge_event": MODULE.POST_CHECK_CHARGE,
                        "charge_amount": "1 proposal attempt",
                        "charge_basis": {
                            "kind": "workflow-default",
                            "path": "parents/R8.yaml",
                            "file_sha256": "a" * 64,
                            "locator": "reviewed parent set contains no charge event",
                        },
                        "repair_mode": "deterministic-fidelity-only",
                        "effect_scope": "deterministic-local-checks-only",
                        "authoritative_output_path": output_relative,
                        "engineering_evidence_path": evidence_relative,
                    },
                }
            )
            report_binding = write_check_report(
                root,
                "artifacts/frontier/B900/check-report-1.json",
                "snapshot-sha256:" + output_digest,
                "pass",
            )
            evidence = {
                "contract_version": MODULE.ENGINEERING_EVIDENCE_CONTRACT,
                "publication_policy": {
                    "charge_event": MODULE.POST_CHECK_CHARGE,
                    "charge_amount": "1 proposal attempt",
                    "authoritative_output_path": output_relative,
                },
                "attempts": [
                    {
                        "sequence": 1,
                        "snapshot_id": "snapshot-sha256:" + output_digest,
                        "snapshot_file_sha256": output_digest,
                        "outcome": "pass",
                        "checks": [{"id": "local-check", "result": "pass"}],
                        "check_report": report_binding,
                        "effects": {"local-check": 1},
                    }
                ],
                "effect_limits": {"local-check": 1},
                "effects": {"local-check": 1},
                "status": "pass",
                "official_output": {
                    "path": output_relative,
                    "file_sha256": output_digest,
                },
                "evidence_use": "engineering-only",
            }
            evidence_path = root / evidence_relative
            evidence_path.write_text(json.dumps(evidence, sort_keys=True) + "\n")
            result = base_result()
            result.update(
                {
                    "work_kind": "design",
                    "changes_executable_candidate": False,
                    "materialization_state": "not-applicable",
                    "candidate_manifest": None,
                    "candidate_identity": None,
                    "source_result_identity": None,
                    "implementation_review_state": "not-applicable",
                    "engineering_validation": [
                        {
                            "contract_version": MODULE.ENGINEERING_EVIDENCE_CONTRACT,
                            "path": evidence_relative,
                            "file_sha256": hashlib.sha256(
                                evidence_path.read_bytes()
                            ).hexdigest(),
                        }
                    ],
                }
            )
            result["planned_spend"] = "1 proposal attempt"
            result["actual_spend"] = "1 proposal attempt"
            result["accounting_evidence"] = (
                f"authoritative output {output_relative} sha256:{output_digest}"
            )

            validation = MODULE.validate(
                result,
                "draft",
                packet,
                repo_root=root,
                check_dispatch=False,
            )

            self.assertTrue(validation["result_structure_ready"], validation["findings"])

    def test_post_check_rejects_boolean_effect_accounting(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet, result, evidence_path = post_check_publication_workspace(root)
            evidence = json.loads(evidence_path.read_text())
            evidence["attempts"][0]["effects"]["local-check"] = True
            evidence["effects"]["local-check"] = 2
            evidence_path.write_text(json.dumps(evidence, sort_keys=True) + "\n")
            result["engineering_validation"][0]["file_sha256"] = hashlib.sha256(
                evidence_path.read_bytes()
            ).hexdigest()

            validation = MODULE.validate(
                result,
                "draft",
                packet,
                repo_root=root,
                check_dispatch=False,
            )

            self.assertIn(
                "PREPUBLICATION_EFFECT_ACCOUNTING_INVALID",
                {finding["code"] for finding in validation["findings"]},
            )

    def test_post_check_rejects_unstructured_check_report_even_when_rehashed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet, result, evidence_path = post_check_publication_workspace(root)
            evidence = json.loads(evidence_path.read_text())
            report_binding = evidence["attempts"][-1]["check_report"]
            report_path = root / report_binding["path"]
            report_path.write_text("check was not run\n")
            report_binding["file_sha256"] = hashlib.sha256(
                report_path.read_bytes()
            ).hexdigest()
            evidence_path.write_text(json.dumps(evidence, sort_keys=True) + "\n")
            result["engineering_validation"][0]["file_sha256"] = hashlib.sha256(
                evidence_path.read_bytes()
            ).hexdigest()

            validation = MODULE.validate(
                result,
                "draft",
                packet,
                repo_root=root,
                check_dispatch=False,
            )

            self.assertIn(
                "PREPUBLICATION_CHECK_REPORT_INVALID",
                {finding["code"] for finding in validation["findings"]},
            )

    def test_post_check_pass_exit_status_requires_integer_zero(self) -> None:
        for invalid_status in (False, 0.0):
            with self.subTest(exit_status=invalid_status), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                packet, result, evidence_path = post_check_publication_workspace(root)
                evidence = json.loads(evidence_path.read_text())
                report_binding = evidence["attempts"][-1]["check_report"]
                report_path = root / report_binding["path"]
                report = json.loads(report_path.read_text())
                report["checks"][0]["exit_status"] = invalid_status
                report_path.write_text(json.dumps(report, sort_keys=True) + "\n")
                report_binding["file_sha256"] = hashlib.sha256(
                    report_path.read_bytes()
                ).hexdigest()
                evidence_path.write_text(json.dumps(evidence, sort_keys=True) + "\n")
                result["engineering_validation"][0]["file_sha256"] = hashlib.sha256(
                    evidence_path.read_bytes()
                ).hexdigest()

                validation = MODULE.validate(
                    result,
                    "draft",
                    packet,
                    repo_root=root,
                    check_dispatch=False,
                )

                self.assertIn(
                    "PREPUBLICATION_CHECK_REPORT_INVALID",
                    {finding["code"] for finding in validation["findings"]},
                )

    def test_post_check_rejects_zero_effects_when_checks_ran(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet, result, evidence_path = post_check_publication_workspace(root)
            evidence = json.loads(evidence_path.read_text())
            for attempt in evidence["attempts"]:
                attempt["effects"] = {"local-check": 0}
            evidence["effects"] = {"local-check": 0}
            evidence_path.write_text(json.dumps(evidence, sort_keys=True) + "\n")
            result["engineering_validation"][0]["file_sha256"] = hashlib.sha256(
                evidence_path.read_bytes()
            ).hexdigest()

            validation = MODULE.validate(
                result,
                "draft",
                packet,
                repo_root=root,
                check_dispatch=False,
            )

            self.assertIn(
                "PREPUBLICATION_EFFECT_ACCOUNTING_INVALID",
                {finding["code"] for finding in validation["findings"]},
            )

    def test_post_check_rejects_all_pass_attempt_relabelled_as_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet, result, evidence_path = post_check_publication_workspace(root)
            evidence = json.loads(evidence_path.read_text())
            evidence["attempts"][-1]["outcome"] = "fail"
            evidence_path.write_text(json.dumps(evidence, sort_keys=True) + "\n")
            result["engineering_validation"][0]["file_sha256"] = hashlib.sha256(
                evidence_path.read_bytes()
            ).hexdigest()

            validation = MODULE.validate(
                result,
                "draft",
                packet,
                repo_root=root,
                check_dispatch=False,
            )

            self.assertIn(
                "PREPUBLICATION_ATTEMPT_OUTCOME_INVALID",
                {finding["code"] for finding in validation["findings"]},
            )

    def test_first_identity_publication_cannot_omit_policy_charge(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet = base_packet()
            packet["publication_policy"] = {
                "contract_version": "frontier-authoritative-output-publication/1",
                "charge_event": "first-parent-chargeable-identity",
                "charge_amount": "1 proposal attempt",
                "charge_basis": {
                    "kind": "parent-rule",
                    "path": "parents/R8.yaml",
                    "file_sha256": "a" * 64,
                    "locator": "fixture first identity rule",
                },
                "repair_mode": "prohibited",
                "effect_scope": "deterministic-local-checks-only",
                "authoritative_output_path": packet["candidate_package_inventory_path"],
                "engineering_evidence_path": "artifacts/frontier/B900/engineering-evidence.json",
            }
            result = base_result()
            seed_materialized_candidate(root, packet, result)
            result["actual_spend"] = "0 proposal attempts"
            result["accounting_evidence"] = "none"

            validation = MODULE.validate(
                result,
                "draft",
                packet,
                repo_root=root,
                check_dispatch=False,
            )

            self.assertIn(
                "PUBLICATION_CHARGE_ACCOUNTING_INVALID",
                {finding["code"] for finding in validation["findings"]},
            )

    def test_post_check_final_attempt_must_cover_every_frozen_check(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet, result, _ = post_check_publication_workspace(root)
            packet["engineering_check_plan"]["checks"].append(
                {
                    "id": "second-check",
                    "command": ["second-check"],
                    "effect_costs": {"local-check": 1},
                }
            )

            validation = MODULE.validate(
                result,
                "draft",
                packet,
                repo_root=root,
                check_dispatch=False,
            )

            self.assertIn(
                "PREPUBLICATION_ATTEMPT_OUTCOME_INVALID",
                {finding["code"] for finding in validation["findings"]},
            )

    def test_post_check_snapshot_id_must_match_snapshot_digest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet, result, evidence_path = post_check_publication_workspace(root)
            evidence = json.loads(evidence_path.read_text())
            evidence["attempts"][-1]["snapshot_id"] = "snapshot-sha256:" + "c" * 64
            evidence_path.write_text(json.dumps(evidence, sort_keys=True) + "\n")
            result["engineering_validation"][0]["file_sha256"] = hashlib.sha256(
                evidence_path.read_bytes()
            ).hexdigest()

            validation = MODULE.validate(
                result,
                "draft",
                packet,
                repo_root=root,
                check_dispatch=False,
            )

            self.assertIn(
                "PREPUBLICATION_SNAPSHOT_ID_INVALID",
                {finding["code"] for finding in validation["findings"]},
            )

    def test_post_check_completed_publication_requires_charge_accounting(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet, result, _ = post_check_publication_workspace(root)
            result["actual_spend"] = "0 proposal attempts"

            validation = MODULE.validate(
                result,
                "draft",
                packet,
                repo_root=root,
                check_dispatch=False,
            )

            self.assertIn(
                "PUBLICATION_CHARGE_ACCOUNTING_INVALID",
                {finding["code"] for finding in validation["findings"]},
            )

    def test_post_check_failed_code_cannot_leave_formal_candidate_residue(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet, result, evidence_path = post_check_publication_workspace(root)
            evidence = json.loads(evidence_path.read_text())
            evidence["attempts"] = evidence["attempts"][:1]
            evidence["effects"] = {"local-check": 1}
            evidence["status"] = "fail"
            evidence["official_output"] = None
            evidence_path.write_text(json.dumps(evidence, sort_keys=True) + "\n")
            result["engineering_validation"][0]["file_sha256"] = hashlib.sha256(
                evidence_path.read_bytes()
            ).hexdigest()
            result["outcome"] = "failed"
            result["materialization_state"] = "partial"

            validation = MODULE.validate(
                result,
                "draft",
                packet,
                repo_root=root,
                check_dispatch=False,
            )

            codes = {finding["code"] for finding in validation["findings"]}
            self.assertIn("PREPUBLICATION_TERMINAL_EVIDENCE_INVALID", codes)
            self.assertIn("PREPUBLICATION_TERMINAL_CANDIDATE_INVALID", codes)

    def test_result_identity_serialization_error_is_repair_not_hard_block(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet, result, _ = post_check_publication_workspace(root)
            result["result_packet_id"] = "B900-result-sha256:stale"
            validation = MODULE.validate(
                result,
                "frozen",
                packet,
                repo_root=root,
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

    def test_project_dispatch_recovery_uses_the_exact_nested_compatibility_gate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            preflight_path = root / "artifacts/frontier/B900/preflight.json"
            acknowledgment_path = root / "artifacts/frontier/B900/acknowledgment.yaml"
            execution_start_path = root / "artifacts/frontier/B900/execution-start.yaml"
            preflight_path.parent.mkdir(parents=True)
            preflight_path.write_text(
                json.dumps({"preflight_id": "B900-preflight-sha256:exact"}) + "\n"
            )
            acknowledgment_path.write_text(
                "acknowledgment_id: B900-acknowledgment-sha256:exact\n"
                f"contract_version: {MODULE.PROJECT_ACKNOWLEDGMENT_CONTRACT}\n"
                "batch_plan:\n"
                "  path: artifacts/frontier/B900/packet.yaml\n"
                "  packet_id: B900-packet-sha256:example\n"
                f"  file_sha256: {HASH}\n"
                "packet_preflight:\n"
                "  path: artifacts/frontier/B900/preflight.json\n"
                "  preflight_id: B900-preflight-sha256:exact\n"
                f"  file_sha256: {hashlib.sha256(preflight_path.read_bytes()).hexdigest()}\n"
            )
            execution_start_path.write_text(
                "execution_start_id: B900-execution-start-sha256:exact\n"
                f"contract_version: {MODULE.PROJECT_EXECUTION_START_CONTRACT}\n"
            )
            result = base_result()
            result["packet_preflight"] = {
                "path": preflight_path.relative_to(root).as_posix(),
                "identity_field": "preflight_id",
                "identity": "B900-preflight-sha256:exact",
                "file_sha256": hashlib.sha256(preflight_path.read_bytes()).hexdigest(),
            }
            result["acknowledgment"] = {
                "path": acknowledgment_path.relative_to(root).as_posix(),
                "identity_field": "acknowledgment_id",
                "identity": "B900-acknowledgment-sha256:exact",
                "file_sha256": hashlib.sha256(acknowledgment_path.read_bytes()).hexdigest(),
            }
            result["execution_start"] = {
                "path": execution_start_path.relative_to(root).as_posix(),
                "identity_field": "execution_start_id",
                "identity": "B900-execution-start-sha256:exact",
                "file_sha256": hashlib.sha256(execution_start_path.read_bytes()).hexdigest(),
            }
            packet = base_packet()
            packet["identity_contract"] = MODULE.IDENTITY_CONTRACT
            packet["packet_preflight_path"] = "artifacts/frontier/B900/preflight.json"
            findings: list[dict[str, str]] = []

            with mock.patch.object(MODULE, "verify_project_nested_dispatch") as verify:
                MODULE.validate_dispatch_bindings(result, packet, root, findings)

            verify.assert_called_once()
            self.assertEqual([], findings)

    def test_project_dispatch_recovery_fails_closed_on_any_compatibility_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            preflight_path = root / "preflight.json"
            acknowledgment_path = root / "acknowledgment.yaml"
            execution_start_path = root / "execution-start.yaml"
            preflight_path.write_text(
                json.dumps({"preflight_id": "B900-preflight-sha256:exact"}) + "\n"
            )
            acknowledgment_path.write_text(
                "acknowledgment_id: B900-acknowledgment-sha256:exact\n"
                f"contract_version: {MODULE.PROJECT_ACKNOWLEDGMENT_CONTRACT}\n"
                "batch_plan:\n"
                "  path: artifacts/frontier/B900/packet.yaml\n"
                "  packet_id: B900-packet-sha256:example\n"
                f"  file_sha256: {HASH}\n"
                "packet_preflight:\n"
                "  path: preflight.json\n"
                "  preflight_id: B900-preflight-sha256:exact\n"
                f"  file_sha256: {hashlib.sha256(preflight_path.read_bytes()).hexdigest()}\n"
            )
            execution_start_path.write_text(
                "execution_start_id: B900-execution-start-sha256:exact\n"
                f"contract_version: {MODULE.PROJECT_EXECUTION_START_CONTRACT}\n"
            )
            result = base_result()
            for field, path, identity_field, identity in (
                (
                    "packet_preflight",
                    preflight_path,
                    "preflight_id",
                    "B900-preflight-sha256:exact",
                ),
                (
                    "acknowledgment",
                    acknowledgment_path,
                    "acknowledgment_id",
                    "B900-acknowledgment-sha256:exact",
                ),
                (
                    "execution_start",
                    execution_start_path,
                    "execution_start_id",
                    "B900-execution-start-sha256:exact",
                ),
            ):
                result[field] = {
                    "path": path.relative_to(root).as_posix(),
                    "identity_field": identity_field,
                    "identity": identity,
                    "file_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                }
            packet = base_packet()
            packet["identity_contract"] = MODULE.IDENTITY_CONTRACT
            packet["packet_preflight_path"] = "preflight.json"
            findings: list[dict[str, str]] = []

            with mock.patch.object(
                MODULE,
                "verify_project_nested_dispatch",
                side_effect=ValueError("nested packet digest changed"),
            ):
                MODULE.validate_dispatch_bindings(result, packet, root, findings)

            self.assertEqual(
                ["PROJECT_DISPATCH_RECOVERY_FAILED"],
                [finding["code"] for finding in findings],
            )
            self.assertIn("nested packet digest changed", findings[0]["detail"])

    def test_project_dispatch_shape_uses_complete_fields_not_contract_version(self) -> None:
        legacy = base_packet()
        legacy.update(
            {
                "contract_version": MODULE.PROJECT_BATCH_PLAN_CONTRACT,
                "packet_preflight_path": "artifacts/frontier/B900/preflight.json",
            }
        )
        legacy_ack = {
            "batch_plan": {
                "path": legacy["packet_path"],
                "packet_id": legacy["packet_id"],
                "file_sha256": HASH,
            },
            "packet_preflight": {
                "path": legacy["packet_preflight_path"],
                "preflight_id": "B900-preflight-sha256:" + HASH,
                "file_sha256": HASH,
            },
        }
        current = current_project_packet()
        current_ack = {
            "batch_plan": {
                "path": "artifacts/frontier/B900/B900-plan.yaml",
                "plan_id": current["batch_plan_id"],
                "file_sha256": HASH,
            }
        }

        self.assertEqual(
            "legacy-packet-preflight",
            MODULE.classify_project_dispatch_shape(legacy, legacy_ack),
        )
        self.assertEqual(
            "current-batch-plan",
            MODULE.classify_project_dispatch_shape(current, current_ack),
        )

        mixed = copy.deepcopy(current)
        mixed["packet_id"] = "B900-packet-sha256:" + HASH
        partial_ack = copy.deepcopy(current_ack)
        partial_ack["packet_preflight"] = None
        for bad_packet, bad_ack in (
            (mixed, current_ack),
            (current, partial_ack),
            ({**current, "workflow_source_identity": "sha256:" + HASH}, current_ack),
        ):
            with self.subTest(packet=bad_packet, acknowledgment=bad_ack):
                with self.assertRaisesRegex(ValueError, "mixed and partial"):
                    MODULE.classify_project_dispatch_shape(bad_packet, bad_ack)

    def test_current_project_result_requires_decision_root_and_forbids_legacy_family(self) -> None:
        packet = current_project_packet()
        result = current_project_result(packet)

        accepted = MODULE.validate(
            result,
            "draft",
            packet,
            check_dispatch=False,
        )
        accepted_codes = {finding["code"] for finding in accepted["findings"]}
        self.assertNotIn("REQUIRED_FIELD_MISSING", accepted_codes)
        self.assertNotIn("PROJECT_RESULT_BINDING_FAMILY_INVALID", accepted_codes)
        self.assertNotIn("PROJECT_DECISION_ROOT_INVALID", accepted_codes)
        self.assertNotIn("PACKET_BINDING_MISMATCH", accepted_codes)

        for field, value, code in (
            ("decision_root", None, "PROJECT_DECISION_ROOT_INVALID"),
            ("workflow_source_identity", "sha256:" + HASH, "PROJECT_RESULT_BINDING_FAMILY_INVALID"),
            ("packet_id", "B900-packet-sha256:" + HASH, "PROJECT_RESULT_BINDING_FAMILY_INVALID"),
            ("packet_preflight", {}, "PROJECT_RESULT_BINDING_FAMILY_INVALID"),
        ):
            changed = copy.deepcopy(result)
            if value is None:
                changed.pop(field)
            else:
                changed[field] = value
            validation = MODULE.validate(
                changed,
                "draft",
                packet,
                check_dispatch=False,
            )
            codes = {finding["code"] for finding in validation["findings"]}
            self.assertIn(code, codes, field)

    def test_legacy_project_result_schema_remains_unchanged_for_batch_plan_v3(self) -> None:
        packet = base_packet()
        packet.update(
            {
                "contract_version": MODULE.PROJECT_BATCH_PLAN_CONTRACT,
                "packet_preflight_path": "artifacts/frontier/B900/preflight.json",
            }
        )
        result = base_result()

        validation = MODULE.validate(
            result,
            "draft",
            packet,
            check_dispatch=False,
        )

        codes = {finding["code"] for finding in validation["findings"]}
        self.assertNotIn("REQUIRED_FIELD_MISSING", codes)
        self.assertNotIn("PROJECT_RESULT_BINDING_FAMILY_INVALID", codes)
        self.assertNotIn("PROJECT_DECISION_ROOT_INVALID", codes)
        self.assertNotIn("PROJECT_DISPATCH_SHAPE_INVALID", codes)

        mixed = copy.deepcopy(result)
        mixed["batch_plan"] = {
            "path": packet["packet_path"],
            "identity_field": "batch_plan_id",
            "identity": "B900-plan-sha256:" + HASH,
            "file_sha256": HASH,
        }
        mixed_validation = MODULE.validate(
            mixed,
            "draft",
            packet,
            check_dispatch=False,
        )
        self.assertIn(
            "PROJECT_RESULT_BINDING_FAMILY_INVALID",
            {finding["code"] for finding in mixed_validation["findings"]},
        )

    def test_current_project_frozen_inputs_match_typed_baseline_and_live_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "project/first.txt"
            second = root / "project/second.txt"
            first.parent.mkdir(parents=True)
            first.write_bytes(b"first\n")
            second.write_bytes(b"second\n")
            frozen = [
                {
                    "path": path.relative_to(root).as_posix(),
                    "scope": "file",
                    "identity": "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest(),
                }
                for path in (first, second)
            ]
            packet = {"execution_frozen_inputs": frozen}
            state = {"execution_frozen_inputs": copy.deepcopy(frozen)}
            baseline = {
                f"project/state/frozen-inputs/{entry['path']}":
                (root / entry["path"]).read_bytes()
                for entry in frozen
            }

            MODULE.verify_current_execution_frozen_inputs(
                packet=packet,
                state=state,
                baseline_raw=baseline,
                repo_root=root,
            )

            live_drift = copy.deepcopy(baseline)
            first.write_bytes(b"changed live bytes\n")
            with self.assertRaisesRegex(ValueError, "live frozen input drift"):
                MODULE.verify_current_execution_frozen_inputs(
                    packet=packet,
                    state=state,
                    baseline_raw=live_drift,
                    repo_root=root,
                )

            first.write_bytes(b"first\n")
            baseline_drift = copy.deepcopy(baseline)
            baseline_drift[f"project/state/frozen-inputs/{frozen[0]['path']}"] = b"changed baseline\n"
            with self.assertRaisesRegex(ValueError, "baseline differs"):
                MODULE.verify_current_execution_frozen_inputs(
                    packet=packet,
                    state=state,
                    baseline_raw=baseline_drift,
                    repo_root=root,
                )

            incomplete_state = {"execution_frozen_inputs": frozen[:1]}
            with self.assertRaisesRegex(ValueError, "complete frozen-input list"):
                MODULE.verify_current_execution_frozen_inputs(
                    packet=packet,
                    state=incomplete_state,
                    baseline_raw=baseline,
                    repo_root=root,
                )

            extra_baseline = copy.deepcopy(baseline)
            extra_baseline["project/state/frozen-inputs/project/extra.txt"] = b"extra\n"
            with self.assertRaisesRegex(ValueError, "exactly the complete frozen inputs"):
                MODULE.verify_current_execution_frozen_inputs(
                    packet=packet,
                    state=state,
                    baseline_raw=extra_baseline,
                    repo_root=root,
                )

    def test_current_project_dispatch_validates_end_to_end_in_draft_and_frozen_phases(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet, result, _ = write_project_dispatch_fixture(root, "current")

            draft = MODULE.validate(
                result, "draft", packet, repo_root=root, check_dispatch=True
            )
            self.assertTrue(draft["result_structure_ready"], draft["findings"])
            frozen = copy.deepcopy(result)
            frozen["result_packet_id"] = draft["computed_result_packet_id"]
            self.assertEqual(
                draft,
                MODULE.validate(
                    frozen, "frozen", packet, repo_root=root, check_dispatch=True
                ),
            )

    def test_current_project_dispatch_rechecks_live_frozen_inputs_in_both_phases(self) -> None:
        for phase in ("draft", "frozen"):
            with self.subTest(phase=phase), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                packet, result, frozen_input = write_project_dispatch_fixture(
                    root, "current"
                )
                if phase == "frozen":
                    result["result_packet_id"] = MODULE.computed_result_id(
                        result,
                        hashlib.sha256(MODULE.canonical_payload(result)).hexdigest(),
                    )
                frozen_input.write_bytes(b"live drift after execution freeze\n")

                validation = MODULE.validate(
                    result, phase, packet, repo_root=root, check_dispatch=True
                )

                failures = [
                    finding
                    for finding in validation["findings"]
                    if finding["code"] == "PROJECT_DISPATCH_RECOVERY_FAILED"
                ]
                self.assertEqual(1, len(failures), validation["findings"])
                self.assertIn("live frozen input drift", failures[0]["detail"])

    def test_current_project_dispatch_rejects_execution_baseline_byte_drift(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet, result, _ = write_project_dispatch_fixture(root, "current")
            bundle = root / packet["execution_baseline_root"]
            manifest = json.loads((bundle / "manifest.json").read_text())
            frozen_member = next(
                item
                for item in manifest["artifacts"]
                if item["logical_name"]
                == "project/state/frozen-inputs/project/input.txt"
            )
            object_path = (
                bundle
                / "objects"
                / frozen_member["content_sha256"][:2]
                / frozen_member["content_sha256"]
            )
            object_path.write_bytes(b"mutated baseline bytes\n")

            validation = MODULE.validate(
                result, "draft", packet, repo_root=root, check_dispatch=True
            )

            failures = [
                finding
                for finding in validation["findings"]
                if finding["code"] == "PROJECT_DISPATCH_RECOVERY_FAILED"
            ]
            self.assertEqual(1, len(failures), validation["findings"])
            self.assertFalse(validation["result_structure_ready"])

    def test_legacy_project_dispatch_validates_complete_v3_chain_end_to_end(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet, result, _ = write_project_dispatch_fixture(root, "legacy")

            draft = MODULE.validate(
                result, "draft", packet, repo_root=root, check_dispatch=True
            )
            self.assertTrue(draft["result_structure_ready"], draft["findings"])
            frozen = copy.deepcopy(result)
            frozen["result_packet_id"] = draft["computed_result_packet_id"]
            self.assertEqual(
                draft,
                MODULE.validate(
                    frozen, "frozen", packet, repo_root=root, check_dispatch=True
                ),
            )

    def test_project_dispatch_union_rejects_every_missing_mixed_and_extra_family_field(self) -> None:
        legacy = base_packet()
        legacy["packet_preflight_path"] = "artifacts/frontier/B900/preflight.json"
        legacy_ack = {
            "batch_plan": {
                "path": legacy["packet_path"],
                "packet_id": legacy["packet_id"],
                "file_sha256": HASH,
            },
            "packet_preflight": {
                "path": legacy["packet_preflight_path"],
                "preflight_id": "B900-preflight-sha256:" + HASH,
                "file_sha256": HASH,
            },
        }
        current = current_project_packet()
        current_ack = {
            "batch_plan": {
                "path": "artifacts/frontier/B900/B900-plan.yaml",
                "plan_id": current["batch_plan_id"],
                "file_sha256": HASH,
            }
        }
        cases: list[tuple[str, dict, dict]] = []

        for field in ("packet_path", "packet_id", "packet_preflight_path"):
            changed = copy.deepcopy(legacy)
            changed.pop(field)
            cases.append((f"legacy packet missing {field}", changed, legacy_ack))
        changed = copy.deepcopy(current)
        changed.pop("batch_plan_id")
        cases.append(("current packet missing batch_plan_id", changed, current_ack))

        for field, value in (
            ("packet_path", "artifacts/frontier/B900/packet.yaml"),
            ("packet_id", "B900-packet-sha256:" + HASH),
            ("packet_preflight_path", "artifacts/frontier/B900/preflight.json"),
            ("workflow_source_identity", "sha256:" + HASH),
            ("workflow_source_binding", {"root": "sha256:" + HASH}),
        ):
            changed = copy.deepcopy(current)
            changed[field] = value
            cases.append((f"current packet mixed extra {field}", changed, current_ack))
        changed = copy.deepcopy(legacy)
        changed["batch_plan_id"] = "B900-plan-sha256:" + HASH
        cases.append(("legacy packet mixed extra batch_plan_id", changed, legacy_ack))

        for family, packet, acknowledgment in (
            ("current", current, current_ack),
            ("legacy", legacy, legacy_ack),
        ):
            changed = copy.deepcopy(acknowledgment)
            changed.pop("batch_plan")
            cases.append(
                (f"{family} acknowledgment missing batch_plan", packet, changed)
            )
            for field in tuple(acknowledgment["batch_plan"]):
                changed = copy.deepcopy(acknowledgment)
                changed["batch_plan"].pop(field)
                cases.append(
                    (f"{family} acknowledgment plan missing {field}", packet, changed)
                )
            changed = copy.deepcopy(acknowledgment)
            changed["batch_plan"][
                "packet_id" if family == "current" else "plan_id"
            ] = "mixed"
            cases.append(
                (f"{family} acknowledgment plan has mixed identity field", packet, changed)
            )

        for field in tuple(legacy_ack["packet_preflight"]):
            changed = copy.deepcopy(legacy_ack)
            changed["packet_preflight"].pop(field)
            cases.append((f"legacy preflight missing {field}", legacy, changed))
        changed = copy.deepcopy(legacy_ack)
        changed["packet_preflight"]["plan_id"] = "extra"
        cases.append(("legacy preflight has extra current field", legacy, changed))
        changed = copy.deepcopy(legacy_ack)
        changed.pop("packet_preflight")
        cases.append(("legacy acknowledgment missing preflight", legacy, changed))
        for value in (None, copy.deepcopy(legacy_ack["packet_preflight"])):
            changed = copy.deepcopy(current_ack)
            changed["packet_preflight"] = value
            cases.append(("current acknowledgment has extra preflight", current, changed))

        for label, packet, acknowledgment in cases:
            with self.subTest(case=label):
                with self.assertRaisesRegex(ValueError, "mixed and partial"):
                    MODULE.classify_project_dispatch_shape(packet, acknowledgment)

    def test_exact_line_identity_rejects_duplicate_identity_fields(self) -> None:
        body = b"contract_version: exact\n"
        expected = "prefix:" + hashlib.sha256(body).hexdigest()
        self.assertEqual(
            expected,
            MODULE.omitted_line_identity(
                b"record_id: value\n" + body,
                "record_id",
                "prefix:",
            ),
        )
        with self.assertRaisesRegex(ValueError, "exactly one"):
            MODULE.omitted_line_identity(
                b"record_id: one\nrecord_id: two\n" + body,
                "record_id",
                "prefix:",
            )

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
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet, draft, _ = post_check_publication_workspace(root)
            draft_validation = MODULE.validate(
                draft, "draft", packet, repo_root=root, check_dispatch=False
            )
            self.assertTrue(
                draft_validation["result_structure_ready"],
                draft_validation["findings"],
            )
            frozen = copy.deepcopy(draft)
            frozen["result_packet_id"] = draft_validation["computed_result_packet_id"]
            frozen_validation = MODULE.validate(
                frozen, "frozen", packet, repo_root=root, check_dispatch=False
            )
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

    def test_routine_local_evaluation_accepts_only_b_evidence_scope(self) -> None:
        target = routine_evaluation_target()
        packet = experiment_packet(target)
        packet["result_contract_version"] = "frontier-batch-result/2"
        result = experiment_result(target)
        result["result_contract_version"] = "frontier-batch-result/2"
        result["performance_evaluation_state"] = "routine-local under the pre-authorized slot"
        result["integration_state"] = "not-authorized"
        result["results"] = [
            {
                "observations": [
                    {
                        "metric": "score",
                        "value": 0.5,
                        "unit": "points",
                        "sample_count": 16,
                    }
                ],
                "maximum_consequence": "B evidence only",
                "evidence_scope": copy.deepcopy(target["evidence_scope"]),
            }
        ]
        result["observed_vs_expected"] = "recorded in structured routine observations"
        result["recovery_point"] = "routine result recorded; no later consequence authorized"
        result["engineering_validation"] = []
        result["new_prerequisites"] = []
        validation = MODULE.validate(result, "draft", packet)
        self.assertTrue(validation["result_structure_ready"], validation["findings"])

    def test_routine_local_rejects_invalid_resource_ceilings(self) -> None:
        for resource_ceiling in (
            {"local_minutes": 0},
            {"local_minutes": -1},
            {"local_minutes": True},
            {"local_minutes": float("nan")},
            {"local_minutes": float("inf")},
            {"": 1},
        ):
            target = routine_evaluation_target()
            target["resource_ceiling"] = resource_ceiling
            findings: list[dict[str, str]] = []
            MODULE.validate_evaluation_target_contract(target, findings)
            self.assertIn(
                "ROUTINE_RESOURCE_CEILING_INVALID",
                {finding["code"] for finding in findings},
            )

    def test_routine_local_rejects_a_missing_later_consequence_prohibition(self) -> None:
        target = routine_evaluation_target()
        target["prohibited_consequences"].remove("direct next-B authority")
        findings: list[dict[str, str]] = []
        MODULE.validate_evaluation_target_contract(target, findings)
        self.assertIn(
            "ROUTINE_PROHIBITIONS_INCOMPLETE",
            {finding["code"] for finding in findings},
        )

    def test_routine_local_rejects_confirmation_or_transfer_claims(self) -> None:
        target = routine_evaluation_target()
        target["evidence_scope"]["confirmation"] = "confirmed"
        target["evidence_scope"]["transfer_scope"] = "general"
        findings: list[dict[str, str]] = []
        MODULE.validate_evaluation_target_contract(target, findings)
        self.assertIn(
            "EVALUATION_SCOPE_EXCEEDS_ROUTINE_LIMIT",
            {finding["code"] for finding in findings},
        )

    def test_routine_result_rejects_component_attribution(self) -> None:
        target = routine_evaluation_target()
        packet = experiment_packet(target)
        packet["result_contract_version"] = "frontier-batch-result/2"
        result = experiment_result(target)
        result["result_contract_version"] = "frontier-batch-result/2"
        result["performance_evaluation_state"] = "routine-local under the pre-authorized slot"
        result["integration_state"] = "not-authorized"
        result["results"] = [
            {
                "observations": [
                    {
                        "metric": "score",
                        "value": 0.5,
                        "unit": "points",
                        "sample_count": 16,
                    }
                ],
                "component_attribution": "the changed component caused the whole gain",
                "maximum_consequence": "B evidence only",
                "evidence_scope": copy.deepcopy(target["evidence_scope"]),
            }
        ]
        validation = MODULE.validate(result, "draft", packet)
        self.assertIn(
            "ROUTINE_RESULT_CLAIM_PRESENT",
            {finding["code"] for finding in validation["findings"]},
        )

    def test_routine_result_rejects_narrative_claims_and_direct_follow_up(self) -> None:
        target = routine_evaluation_target()
        packet = experiment_packet(target)
        packet["result_contract_version"] = "frontier-batch-result/2"
        result = experiment_result(target)
        result["result_contract_version"] = "frontier-batch-result/2"
        result["performance_evaluation_state"] = "routine-local under the pre-authorized slot"
        result["results"] = [
            {
                "analysis": "This confirms general superiority and one component caused the gain.",
                "maximum_consequence": "B evidence only",
                "evidence_scope": copy.deepcopy(target["evidence_scope"]),
            }
        ]
        result["possible_follow_up"] = "Authorize the next B and promote the candidate"
        validation = MODULE.validate(result, "draft", packet)
        codes = {finding["code"] for finding in validation["findings"]}
        self.assertIn("ROUTINE_RESULT_SCHEMA_INVALID", codes)
        self.assertIn("ROUTINE_FOLLOW_UP_AUTHORITY_PRESENT", codes)
        self.assertIn("ROUTINE_RESULT_NARRATIVE_PRESENT", codes)

    def test_routine_result_rejects_top_level_authority_leakage(self) -> None:
        target = routine_evaluation_target()
        packet = experiment_packet(target)
        packet["result_contract_version"] = "frontier-batch-result/2"
        result = experiment_result(target)
        result["result_contract_version"] = "frontier-batch-result/2"
        result["performance_evaluation_state"] = "routine-local under the pre-authorized slot"
        result["integration_state"] = "not-authorized"
        result["results"] = [
            {
                "observations": [
                    {
                        "metric": "score",
                        "value": 0.5,
                        "unit": "points",
                        "sample_count": 16,
                    }
                ],
                "maximum_consequence": "B evidence only",
                "evidence_scope": copy.deepcopy(target["evidence_scope"]),
            }
        ]
        result["observed_vs_expected"] = "recorded in structured routine observations"
        result["new_prerequisites"] = ["Promote this candidate and authorize B003 next"]
        result["scope_deviation"] = "Publish the result externally"
        validation = MODULE.validate(result, "draft", packet)
        self.assertIn(
            "ROUTINE_RESULT_AUTHORITY_LEAKAGE",
            {finding["code"] for finding in validation["findings"]},
        )

    def test_routine_result_rejects_extra_sampling_and_nonfinite_values(self) -> None:
        target = routine_evaluation_target()
        packet = experiment_packet(target)
        packet["result_contract_version"] = "frontier-batch-result/2"
        result = experiment_result(target)
        result["result_contract_version"] = "frontier-batch-result/2"
        result["performance_evaluation_state"] = "routine-local under the pre-authorized slot"
        item = {
            "observations": [
                {
                    "metric": "score",
                    "value": float("nan"),
                    "unit": "points",
                    "sample_count": 999999,
                }
            ],
            "maximum_consequence": "B evidence only",
            "evidence_scope": copy.deepcopy(target["evidence_scope"]),
        }
        result["results"] = [item, copy.deepcopy(item)]
        result["observed_vs_expected"] = "recorded in structured routine observations"
        validation = MODULE.validate(result, "draft", packet)
        codes = {finding["code"] for finding in validation["findings"]}
        self.assertIn("ROUTINE_RESULT_CONTAINER_INVALID", codes)
        self.assertIn("ROUTINE_SAMPLE_CEILING_EXCEEDED", codes)
        self.assertIn("ROUTINE_OBSERVATION_INVALID", codes)

    def test_routine_blocked_before_sampling_accepts_empty_results(self) -> None:
        target = routine_evaluation_target()
        packet = experiment_packet(target)
        packet["result_contract_version"] = "frontier-batch-result/2"
        result = experiment_result(target)
        result["result_contract_version"] = "frontier-batch-result/2"
        result["outcome"] = "blocked"
        result["performance_evaluation_state"] = (
            "not-authorized: required local input unavailable"
        )
        result["integration_state"] = "not-authorized"
        result["results"] = []
        result["observed_vs_expected"] = "no structured routine observation completed"
        result["failed_checks"] = ["required local input unavailable"]
        result["recovery_point"] = "routine result recorded; no later consequence authorized"
        result["engineering_validation"] = []
        result["new_prerequisites"] = []
        validation = MODULE.validate(result, "draft", packet)
        self.assertTrue(validation["result_structure_ready"], validation["findings"])

    def test_routine_completed_measurement_rejects_empty_results(self) -> None:
        target = routine_evaluation_target()
        packet = experiment_packet(target)
        packet["result_contract_version"] = "frontier-batch-result/2"
        result = experiment_result(target)
        result["result_contract_version"] = "frontier-batch-result/2"
        result["performance_evaluation_state"] = "routine-local under the pre-authorized slot"
        result["integration_state"] = "not-authorized"
        result["results"] = []
        result["observed_vs_expected"] = "recorded in structured routine observations"
        result["recovery_point"] = "routine result recorded; no later consequence authorized"
        result["engineering_validation"] = []
        result["new_prerequisites"] = []
        validation = MODULE.validate(result, "draft", packet)
        self.assertIn(
            "ROUTINE_RESULT_CONTAINER_INVALID",
            {finding["code"] for finding in validation["findings"]},
        )

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
