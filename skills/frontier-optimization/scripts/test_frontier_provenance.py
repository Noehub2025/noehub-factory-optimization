#!/usr/bin/env python3
"""Interface and attack-path tests for task-neutral Frontier provenance."""

from __future__ import annotations

import copy
import concurrent.futures
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
import yaml

from frontier_provenance import (
    NodeRepository,
    ProvenanceError,
    attest,
    bind_authority,
    freeze_decision,
    freeze_execution,
    record_outcome,
    verify_chain,
    verify_for,
)
from frontier_provenance.source_modules import (
    audit_python_dependencies,
    source_module_root,
    validate_source_modules,
)
from frontier_provenance.compatibility import require_v1_completion
from frontier_provenance.content import authority_payload, canonical_json
from frontier_provenance.stores import (
    ArtifactSource,
    ClosedCollection,
    GitSnapshotStore,
    ProjectPortableStore,
    PortableBundleStore,
    WorkflowReleaseGitStore,
)
from frontier_provenance.handoff import export_handoff, verify_handoff
from frontier_provenance.graph import build_node
from frontier_provenance.review_contract import validate_and_project
from frontier_provenance.review_subject import require_current_review_subject
from frontier_provenance_cli import (
    REQUEST_CONTRACT,
    apply_operation,
    content_resolver as cli_content_resolver,
)
from frontier_review import PREPARATION_CONTRACT, prepare_review


TEST_DOMAINS: dict[str, str] = {}
DOMAIN_ROLES = {
    "project-decision": "decision",
    "review-report": "review",
    "project-authority": "authority",
    "project-state": "state",
    "project-outcome": "outcome",
    "live-receipt": "receipt",
}
DOMAIN_PREFIXES = {
    "project-decision": "project/decision/",
    "review-report": "project/review/",
    "project-authority": "project/authority/",
    "project-state": "project/state/",
    "project-outcome": "project/outcome/",
    "live-receipt": "receipts/",
    "workflow-release": "release/",
}



class LegacyProjectFixture(ProjectPortableStore):
    """Construct historical bundle fixtures to exercise current read compatibility."""

    def capture(self, role, sources, destination, *, project_root, closed_collections=()):
        source_list = list(sources)
        self._validate_frozen_input_names(role, source_list, project_root)
        return PortableBundleStore()._capture_domain(
            source_list, destination, domain={value: key for key, value in DOMAIN_ROLES.items()}[role],
            project_root=project_root, closed_collections=closed_collections)


def save_fixture(root: Path) -> None:
    git(root, "init", "-q")
    git(root, "add", "--all")
    git(root, "-c", "user.name=Provenance Test", "-c", "user.email=test@example.invalid",
        "commit", "--allow-empty", "-qm", "fixture checkpoint")


def typed_root(domain: str, seed: str) -> str:
    root = "frontier-content-root-sha256:" + hashlib.sha256(
        f"{domain}:{seed}".encode()
    ).hexdigest()
    TEST_DOMAINS[root] = domain
    return root


def git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return result.stdout.decode().strip()


def content_resolver(content_root: str) -> dict[str, object]:
    receipt_names = {
        "authority_current",
        "budget_current",
        "reservation_current",
        "inputs_current",
        "resources_available",
        "action_window_open",
        "prior_external_effects_known",
        "budget_accounted",
    }
    result = {
        "content_root": content_root,
        "domain": TEST_DOMAINS[content_root],
        "verified": True,
        "receipt_facts": {
            name: {
                "status": "pass",
                "observed_at": "2026-08-17T00:00:00Z",
                "expires_at": "2026-08-17T02:00:00Z",
            }
            for name in receipt_names
        },
    }
    if TEST_DOMAINS[content_root] == "project-decision":
        result["review_subject"] = {
            "contract_version": "frontier-review-subject/2",
            "role_adapter": "frontier-review-role-adapter/2",
            "review_kind": "entry",
            "subject_mode": "complete",
            "semantic_projection": {"affected_scope": "test decision"},
        }
    return result


def fact(receipt_root: str) -> dict[str, str]:
    return {"receipt_root": receipt_root}


def initialize(root: Path) -> None:
    git(root, "init", "-q")
    (root / "tracked.txt").write_bytes(b"tracked\n")
    git(root, "add", "tracked.txt")
    git(
        root,
        "-c",
        "user.name=Provenance Test",
        "-c",
        "user.email=provenance@example.invalid",
        "commit",
        "-qm",
        "initial",
    )


def _self_identified(field: str, prefix: str, body: bytes) -> bytes:
    remaining = (
        f"identity_rule: {prefix.removesuffix(':')} of exact UTF-8 bytes with the complete {field} line omitted\n"
    ).encode() + body
    return f"{field}: {prefix}{hashlib.sha256(remaining).hexdigest()}\n".encode() + remaining


def prepare_entry_bundle(root: Path, destination: Path, marker: str = "project-v1") -> dict:
    draft = root / f"draft-{destination.name}"
    for name in ("state", "parents", "entry"):
        (draft / name).mkdir(parents=True, exist_ok=True)
    (draft / "state/frontier.md").write_text(f"# Frontier\n\n{marker}\n")
    (draft / "state/ledger.md").write_text("# Ledger\n\n## X001 Selection\n")
    (draft / "state/log.md").write_text("# Log\n")
    (draft / "parents/problem.md").write_text("# Problem\n")
    (draft / "parents/representation.md").write_text("# Representation\n")
    (draft / "parents/handoff.yaml").write_text("contract_version: framing-handoff/1\n")
    (draft / "selection.yaml").write_text(
        "contract_version: frontier-selection-evidence-state/1\n"
        "event_id: X001\n"
        "budget: {ceiling: 3, actual: 0}\n"
        "route_set: {state: complete}\n"
        "resolver: {first_applicable_row: 12}\n"
        "selection: {primary: B001}\n"
        "authority: {current: planning-only}\n"
    )
    (draft / "entry/plan.yaml").write_bytes(
        _self_identified(
            "batch_plan_id",
            "B001-plan-sha256:",
            b"contract_version: frontier-project-batch-plan/3\n"
            b"batch_id: B001\nmaximum_spend: {schedules: 1}\n"
            b"authorization_gate: exact reviewed authorization\n"
            b"stop_conditions: [one result]\n",
        )
    )
    (draft / "entry/work.yaml").write_text(
        "contract_version: frontier-project-experiment/1\n"
        "batch_id: B001\n"
        "purpose: one bounded test\n"
    )
    (draft / "entry/target.yaml").write_bytes(
        _self_identified(
            "target_id",
            "V001-target-sha256:",
            b"contract_version: frontier-project-authorization-target/1\n"
            b"decision_id: V001\nbatch_id: B001\nscope: one bounded test\n"
            b"maximum_spend: {schedules: 1}\nstop_boundary: stop after one result\n"
            b"authorization_question: Authorize the exact test?\n"
            b"authorize_consequence: permit one later acknowledged schedule\n",
        )
    )
    items = (
        ("project/decision/state/frontier.md", "state/frontier.md"),
        ("project/decision/state/ledger.md", "state/ledger.md"),
        ("project/decision/state/log.md", "state/log.md"),
        ("project/decision/parents/problem.md", "parents/problem.md"),
        ("project/decision/parents/representation.md", "parents/representation.md"),
        ("project/decision/parents/handoff.yaml", "parents/handoff.yaml"),
        ("project/decision/selection/evidence-state.yaml", "selection.yaml"),
        ("project/decision/entry/plan.yaml", "entry/plan.yaml"),
        ("project/decision/entry/work.yaml", "entry/work.yaml"),
        ("project/decision/entry/target.yaml", "entry/target.yaml"),
    )
    save_fixture(root)
    result = prepare_review(
        {
            "contract_version": PREPARATION_CONTRACT,
            "review_kind": "entry",
            "artifacts": [
                {
                    "logical_name": logical,
                    "path": str(draft / relative),
                    "kind": "blob",
                    "behavioral_metadata": {},
                }
                for logical, relative in items
            ],
            "closed_collections": [],
            "semantic_projection": {"review_stage": "authorization-readiness"},
        },
        root,
        destination,
    )
    assert result["status"] == "SEALED", result
    return result


def chain(content_root: str) -> tuple[dict, dict, dict, dict, dict[str, dict]]:
    TEST_DOMAINS[content_root] = "live-receipt"
    roots = {
        domain: typed_root(domain, content_root)
        for domain in (
            "project-decision",
            "review-report",
            "project-authority",
            "project-state",
            "project-outcome",
        )
    }
    return chain_with_roots(roots)


def chain_with_roots(
    roots: dict[str, str],
) -> tuple[dict, dict, dict, dict, dict[str, dict]]:
    decision = freeze_decision(decision_root=roots["project-decision"])
    validation = attest(
        decision,
        validation_report_root=roots["review-report"],
        verdict="ready",
        findings=[],
    )
    authority = build_node(
        "authority",
        {},
        parents=[
            {"edge": "decision", "node_id": decision["node_id"]},
            {"edge": "attestation", "node_id": validation["node_id"]},
        ],
        artifact_roots=[roots["project-authority"]],
    )
    execution = freeze_execution(
        authority=authority,
        starting_state_root=roots["project-state"],
    )
    outcome = record_outcome(
        execution=execution,
        outcome_root=roots["project-outcome"],
    )
    nodes = {
        node["node_id"]: node
        for node in (decision, validation, authority, execution, outcome)
    }
    return decision, authority, execution, outcome, nodes


def portable_project_chain(
    root: Path, source: Path
) -> tuple[dict, dict[str, dict], dict[str, object]]:
    roots: dict[str, str] = {}
    bundles: dict[str, Path] = {}
    for domain in (
        "project-decision",
        "review-report",
        "project-authority",
        "project-state",
        "project-outcome",
    ):
        bundle = root / f"content-{domain}"
        if domain == "project-decision":
            prepared = prepare_entry_bundle(root, root / "prepared-decision")
            bundle = root / "prepared-decision/snapshot"
            manifest = LegacyProjectFixture().verify(bundle, expected_role="decision")
        else:
            sources = [ArtifactSource(DOMAIN_PREFIXES[domain] + "project-record.txt", source)]
            manifest = LegacyProjectFixture().capture(
                DOMAIN_ROLES[domain],
                sources,
                bundle,
                project_root=root,
            )
        roots[domain] = manifest["content_root"]
        TEST_DOMAINS[manifest["content_root"]] = domain
        bundles[manifest["content_root"]] = bundle
    _, _, _, outcome, nodes = chain_with_roots(roots)

    return outcome, nodes, [
        {"adapter": json.loads((bundle / "manifest.json").read_text())["storage"]["adapter"],
         "path": str(bundle)}
        for bundle in bundles.values()
    ]


def routine_execution_fixture(root: Path) -> dict[str, object]:
    entry_content = typed_root("project-decision", "routine-entry")
    review_content = typed_root("review-report", "routine-entry-review")
    authority_content = typed_root("project-authority", "routine-authority")
    materialization_state = typed_root("project-state", "materialization-state")
    outcome_content = typed_root("project-outcome", "materialization-outcome")
    implementation_content = typed_root("project-decision", "implementation-review")
    implementation_report = typed_root("review-report", "implementation-report")
    routine_state = typed_root("project-state", "routine-state")
    receipt_root = typed_root("live-receipt", "routine-receipts")

    entry = freeze_decision(decision_root=entry_content)
    entry_review = attest(
        entry,
        validation_report_root=review_content,
        verdict="ready",
        findings=[],
    )
    authority = build_node(
        "authority",
        {},
        parents=[
            {"edge": "decision", "node_id": entry["node_id"]},
            {"edge": "attestation", "node_id": entry_review["node_id"]},
        ],
        artifact_roots=[authority_content],
    )
    materialization = freeze_execution(
        authority=authority, starting_state_root=materialization_state
    )
    materialization_outcome = record_outcome(
        execution=materialization, outcome_root=outcome_content
    )
    implementation = freeze_decision(decision_root=implementation_content)
    implementation_validation = attest(
        implementation,
        validation_report_root=implementation_report,
        verdict="ready",
        findings=[],
    )
    nodes = {
        node["node_id"]: node
        for node in (
            entry,
            entry_review,
            authority,
            materialization,
            materialization_outcome,
            implementation,
            implementation_validation,
        )
    }

    candidate_manifest_name = "project/state/candidate/manifest.yaml"
    candidate_collection_name = "project/state/candidate"
    candidate_main = b"def candidate(): return 1\n"
    package_members = [
        {
            "path": "main.py",
            "size": len(candidate_main),
            "sha256": hashlib.sha256(candidate_main).hexdigest(),
        }
    ]
    package_sha = hashlib.sha256(canonical_json(package_members)).hexdigest()
    candidate_id = "B001-candidate-sha256:" + package_sha
    candidate_manifest = yaml.safe_dump(
        {
            "manifest_contract": "frontier-candidate-manifest/3",
            "manifest_state": "final",
            "candidate_id": candidate_id,
            "source_result_identity": {
                "package_sha256": package_sha,
                "members": package_members,
            },
            "code_paths": [
                {"path": item["path"], "sha256": item["sha256"]}
                for item in package_members
            ],
        },
        sort_keys=False,
    ).encode()
    collection = {
        "logical_name": candidate_collection_name,
        "members": [
            candidate_manifest_name,
            "project/state/candidate/main.py",
        ],
    }
    collection_root = "sha256:" + package_sha
    manifest_sha = hashlib.sha256(candidate_manifest).hexdigest()
    protocol_key = "protocol-key-sha256:" + "5" * 64
    protocol_id = "protocol-sha256:" + "6" * 64
    calibration_id = "calibration-sha256:" + "7" * 64
    template = {
        "contract_version": "frontier-routine-experiment-template/1",
        "experiment": {
            "contract_version": "frontier-routine-experiment/1",
            "candidate": {
                "id": "$late.candidate.id",
                "manifest_sha256": "$late.candidate.manifest_sha256",
                "collection_root": "$late.candidate.collection_root",
            },
            "scientific_question": "one bounded local question",
            "protocol_id": protocol_id,
            "calibration_id": calibration_id,
            "sample_ceiling": {"runs": 16},
            "resource_ceiling": {"local_minutes": 5},
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
            "result_path": "project/outcome/B002-result.yaml",
            "stop_conditions": ["one bounded local screen"],
        },
        "runtime_inputs": {
            "sample_ceiling": {"runs": 16},
            "resource_ceiling": {"local_minutes": 5},
            "schedule": {"seeds": [1, 2], "order": "fixed"},
        },
        "evaluation_target": {
            "contract_version": "frontier-evaluation-target/2",
            "result_contract_version": "frontier-batch-result/2",
            "mode": "routine-local",
            "sample_ceiling": {"runs": 16},
            "resource_ceiling": {"local_minutes": 5},
            "candidate": {
                "id": "$late.candidate.id",
                "root_path": "candidates/B001",
                "manifest_path": candidate_manifest_name,
                "manifest_sha256": "$late.candidate.manifest_sha256",
                "collection_root": "$late.candidate.collection_root",
            },
            "implementation_review": {
                "result": "IMPLEMENTATION_READY",
                "derivation": "unique finding-free review of the derived candidate",
            },
            "experiment": {
                "path": "project/state/experiment.yaml",
                "experiment_id": "$derived.experiment.id",
                "file_sha256": "$derived.experiment.file_sha256",
            },
            "routine_slot": {
                "contract_version": "frontier-routine-follow-up/1",
                "slot_id": "slot-B001-screen",
                "materialization_batch_id": "B001",
                "follow_up_batch_id": "B002",
                "origin_decision_root": "$entry.origin_decision_root",
                "origin_authority_root": "$entry.origin_authority_root",
                "template_root": "$entry.template_root",
            },
            "protocol": {
                "contract_version": "frontier-evaluation-protocol/1",
                "content_root": "$entry.protocol_content_root",
                "protocol_id": protocol_id,
                "invalidation_key": protocol_key,
            },
            "calibration": {
                "contract_version": "frontier-protocol-calibration-result/1",
                "content_root": "$entry.calibration_content_root",
                "calibration_id": calibration_id,
                "protocol_invalidation_key": protocol_key,
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
        },
    }
    template_root = "sha256:" + hashlib.sha256(canonical_json(template)).hexdigest()
    target = copy.deepcopy(template["evaluation_target"])
    replacements = {
        "$late.candidate.id": candidate_id,
        "$late.candidate.manifest_sha256": manifest_sha,
        "$late.candidate.collection_root": collection_root,
        "$entry.origin_decision_root": entry["node_id"],
        "$entry.origin_authority_root": authority["node_id"],
        "$entry.template_root": template_root,
        "$entry.protocol_content_root": entry_content,
        "$entry.calibration_content_root": entry_content,
    }

    def bind(value):
        if isinstance(value, str):
            return replacements.get(value, value)
        if isinstance(value, list):
            return [bind(item) for item in value]
        if isinstance(value, dict):
            return {key: bind(item) for key, item in value.items()}
        return value

    experiment_body = yaml.safe_dump(
        bind(template["experiment"]), sort_keys=False, allow_unicode=True
    ).encode()
    experiment_id = (
        "B002-experiment-sha256:" + hashlib.sha256(experiment_body).hexdigest()
    )
    experiment_raw = f"experiment_id: {experiment_id}\n".encode() + experiment_body
    replacements["$derived.experiment.id"] = experiment_id
    replacements["$derived.experiment.file_sha256"] = hashlib.sha256(
        experiment_raw
    ).hexdigest()

    target = bind(target)
    late_objects = {
        "candidate_manifest": candidate_manifest_name,
        "candidate_collection": candidate_collection_name,
        "materialization_execution_node": "project/state/nodes/materialization-execution.json",
        "materialization_outcome_node": "project/state/nodes/materialization-outcome.json",
        "materialization_result": "project/state/materialization-result.yaml",
        "materialization_result_validation": "project/state/materialization-result-validation.yaml",
        "implementation_review_decision_node": "project/state/nodes/implementation-decision.json",
        "implementation_review_attestation_node": "project/state/nodes/implementation-attestation.json",
        "implementation_review_input": "project/state/implementation-review-input.yaml",
        "implementation_review_report": "project/state/implementation-review.md",
        "final_experiment": "project/state/experiment.yaml",
        "runtime_inputs": "project/state/runtime-inputs.yaml",
    }
    admission = {
        "contract_version": "frontier-routine-admission/1",
        "evaluation_target": target,
        "origin_decision_root": entry["node_id"],
        "origin_authority_root": authority["node_id"],
        "materialization_execution_root": materialization["node_id"],
        "materialization_outcome_root": materialization_outcome["node_id"],
        "implementation_review_decision_root": implementation["node_id"],
        "implementation_review_attestation_root": implementation_validation["node_id"],
        "live_receipt_root": receipt_root,
        "budget": {
            "budget_identity": "budget-sha256:" + "a" * 64,
            "reservation_identity": "reservation-sha256:" + "b" * 64,
            "planned_spend": 1,
            "available_unprotected": 2,
            "protected_reserve_used": False,
            "reservation_state": "current",
        },
        "late_objects": late_objects,
    }
    state_raw = {
        "project/state/routine-admission.yaml": yaml.safe_dump(admission, sort_keys=False).encode(),
        candidate_manifest_name: candidate_manifest,
        "project/state/candidate/main.py": candidate_main,
        "project/state/nodes/materialization-execution.json": canonical_json(materialization) + b"\n",
        "project/state/nodes/materialization-outcome.json": canonical_json(materialization_outcome) + b"\n",
        "project/state/materialization-result.yaml": yaml.safe_dump(
            {"outcome": "completed", "candidate_identity": candidate_id},
            sort_keys=False,
        ).encode(),
        "project/state/materialization-result-validation.yaml": yaml.safe_dump(
            {
                "result_structure_ready": True,
                "blocking_findings": [],
                "repair_findings": [],
            },
            sort_keys=False,
        ).encode(),
        "project/state/nodes/implementation-decision.json": canonical_json(implementation) + b"\n",
        "project/state/nodes/implementation-attestation.json": canonical_json(implementation_validation) + b"\n",
        "project/state/implementation-review-input.yaml": yaml.safe_dump(
            {
                "candidate": {
                    "id": candidate_id,
                    "root_path": "candidates/B001",
                    "manifest_path": candidate_manifest_name,
                    "manifest_sha256": manifest_sha,
                    "collection_root": collection_root,
                }
            },
            sort_keys=False,
        ).encode(),
        "project/state/implementation-review.md": b"IMPLEMENTATION_READY\n",
        "project/state/experiment.yaml": experiment_raw,
        "project/state/runtime-inputs.yaml": yaml.safe_dump(
            template["runtime_inputs"], sort_keys=False, allow_unicode=True
        ).encode(),
    }
    content = {
        entry_content: {
            "content_root": entry_content,
            "domain": "project-decision",
            "verified": True,
            "review_subject": {
                "contract_version": "frontier-review-subject/2",
                "role_adapter": "frontier-review-role-adapter/2",
                "review_kind": "entry",
                "subject_mode": "complete",
                "semantic_projection": {
                    "routine_follow_up": {
                        "slot_id": "slot-B001-screen",
                        "materialization_batch_id": "B001",
                        "follow_up_batch_id": "B002",
                        "route_id": "route-1",
                        "protocol_id": protocol_id,
                        "calibration_id": calibration_id,
                        "protocol_invalidation_key": protocol_key,
                        "scientific_question": "one bounded local question",
                        "sample_ceiling": {"runs": 16},
                        "resource_ceiling": {"local_minutes": 5},
                        "action_window": "current",
                        "budget_boundary": {"maximum_spend": 1},
                        "template": template,
                        "prohibited_consequences": target["prohibited_consequences"],
                    }
                },
            },
        },
        review_content: {"content_root": review_content, "domain": "review-report", "verified": True},
        authority_content: {"content_root": authority_content, "domain": "project-authority", "verified": True},
        routine_state: {
            "content_root": routine_state,
            "domain": "project-state",
            "verified": True,
            "closed_collections": [collection],
        },
        implementation_content: {
            "content_root": implementation_content,
            "domain": "project-decision",
            "verified": True,
            "review_subject": {
                "contract_version": "frontier-review-subject/2",
                "role_adapter": "frontier-review-role-adapter/2",
                "review_kind": "implementation",
                "subject_mode": "complete",
                "semantic_projection": {
                    "candidate": {
                        "id": candidate_id,
                        "root_path": "candidates/B001",
                        "manifest_path": candidate_manifest_name,
                        "manifest_sha256": manifest_sha,
                        "collection_root": collection_root,
                    }
                },
            },
        },
        implementation_report: {
            "content_root": implementation_report,
            "domain": "review-report",
            "verified": True,
        },
        outcome_content: {"content_root": outcome_content, "domain": "project-outcome", "verified": True},
        receipt_root: {
            "content_root": receipt_root,
            "domain": "live-receipt",
            "verified": True,
            "receipt_facts": {
                name: {
                    "status": "pass",
                    "observed_at": "2026-08-20T00:00:00Z",
                    "expires_at": "2026-08-20T02:00:00Z",
                }
                for name in (
                    "authority_current",
                    "budget_current",
                    "reservation_current",
                    "inputs_current",
                    "resources_available",
                    "action_window_open",
                    "routine_slot_current",
                )
            },
        },
    }
    content[receipt_root]["receipt_facts"]["routine_slot_current"]["document"] = {
        "contract_version": "frontier-routine-live-receipt/1",
        "slot_id": "slot-B001-screen",
        "origin_decision_root": entry["node_id"],
        "origin_authority_root": authority["node_id"],
        "template_root": template_root,
        "budget_identity": "budget-sha256:" + "a" * 64,
        "reservation_identity": "reservation-sha256:" + "b" * 64,
        "planned_spend": 1,
        "available_unprotected": 2,
        "protected_reserve_used": False,
        "reservation_state": "current",
        "action_window": "current",
    }
    raw = {
        routine_state: state_raw,
        outcome_content: {
            "project/outcome/result.yaml": yaml.safe_dump(
                {"outcome": "completed", "candidate_identity": candidate_id},
                sort_keys=False,
            ).encode(),
            "project/outcome/result-validation.yaml": state_raw[
                "project/state/materialization-result-validation.yaml"
            ],
        },
        implementation_content: {
            "project/decision/implementation-review-input.yaml": state_raw[
                "project/state/implementation-review-input.yaml"
            ]
        },
        implementation_report: {
            "review/report.md": state_raw["project/state/implementation-review.md"]
        },
    }
    facts = {
        name: {"receipt_root": receipt_root}
        for name in content[receipt_root]["receipt_facts"]
    }
    return {
        "authority": authority,
        "nodes": nodes,
        "content": content,
        "raw": raw,
        "state_root": routine_state,
        "admission": admission,
        "facts": facts,
    }


def test_routine_execution_derives_candidate_and_consumes_one_slot() -> None:
    with tempfile.TemporaryDirectory() as directory:
        fixture = routine_execution_fixture(Path(directory))
        nodes = fixture["nodes"]
        content = fixture["content"]
        raw = fixture["raw"]
        repository = NodeRepository(Path(directory) / "nodes")
        repository.write_all(nodes.values())
        execution = freeze_execution(
            authority=fixture["authority"],
            starting_state_root=fixture["state_root"],
            routine_admission=fixture["admission"],
            repository=repository,
            resolve_content=content.__getitem__,
            read_content=raw.__getitem__,
            live_facts=fixture["facts"],
            checked_at="2026-08-20T01:00:00Z",
        )
        with pytest.raises(ProvenanceError, match="already consumed"):
            freeze_execution(
                authority=fixture["authority"],
                starting_state_root=fixture["state_root"],
                routine_admission=fixture["admission"],
                repository=repository,
                resolve_content=content.__getitem__,
                read_content=raw.__getitem__,
                live_facts=fixture["facts"],
                checked_at="2026-08-20T01:00:00Z",
            )
        repository.write(execution)
        assert repository.load_routine_slot("slot-B001-screen") == {
            "slot_id": "slot-B001-screen",
            "execution_root": execution["node_id"],
        }
        replay_state = typed_root("project-state", "routine-state-replay")
        content[replay_state] = {
            **content[fixture["state_root"]],
            "content_root": replay_state,
        }
        raw[replay_state] = raw[fixture["state_root"]]
        with pytest.raises(ProvenanceError, match="canonical execution"):
            freeze_execution(
                authority=fixture["authority"],
                starting_state_root=replay_state,
                routine_admission=fixture["admission"],
                repository=repository,
                resolve_content=content.__getitem__,
                read_content=raw.__getitem__,
                live_facts=fixture["facts"],
                checked_at="2026-08-20T01:00:00Z",
            )

        slot_directory = repository.root / "routine-slots"
        slot_directory.rename(repository.root / "routine-slots-backup")
        with pytest.raises(ProvenanceError, match="canonical execution"):
            freeze_execution(
                authority=fixture["authority"],
                starting_state_root=replay_state,
                routine_admission=fixture["admission"],
                repository=repository,
                resolve_content=content.__getitem__,
                read_content=raw.__getitem__,
                live_facts=fixture["facts"],
                checked_at="2026-08-20T01:00:00Z",
            )


def test_concurrent_routine_release_allows_exactly_one_execution() -> None:
    with tempfile.TemporaryDirectory() as directory:
        fixture = routine_execution_fixture(Path(directory))
        repository = NodeRepository(Path(directory) / "nodes")
        repository.write_all(fixture["nodes"].values())

        def release() -> dict:
            return freeze_execution(
                authority=fixture["authority"],
                starting_state_root=fixture["state_root"],
                routine_admission=fixture["admission"],
                repository=repository,
                resolve_content=fixture["content"].__getitem__,
                read_content=fixture["raw"].__getitem__,
                live_facts=fixture["facts"],
                checked_at="2026-08-20T01:00:00Z",
            )

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(release) for _ in range(2)]
            outcomes: list[dict | BaseException] = []
            for future in futures:
                try:
                    outcomes.append(future.result())
                except BaseException as exc:  # capture the competing release
                    outcomes.append(exc)
        assert sum(isinstance(item, dict) for item in outcomes) == 1
        failures = [item for item in outcomes if isinstance(item, BaseException)]
        assert len(failures) == 1
        assert isinstance(failures[0], ProvenanceError)
        assert "already consumed" in str(failures[0])


def test_routine_execution_rejects_forged_candidate_and_protected_reserve() -> None:
    with tempfile.TemporaryDirectory() as directory:
        fixture = routine_execution_fixture(Path(directory))
        repository = NodeRepository(Path(directory) / "nodes")
        repository.write_all(fixture["nodes"].values())
        for mutation in ("candidate", "reserve"):
            admission = copy.deepcopy(fixture["admission"])
            raw = copy.deepcopy(fixture["raw"])
            if mutation == "candidate":
                admission["evaluation_target"]["candidate"]["id"] = "forged"
            else:
                admission["budget"]["protected_reserve_used"] = True
            raw[fixture["state_root"]]["project/state/routine-admission.yaml"] = yaml.safe_dump(
                admission, sort_keys=False
            ).encode()
            with pytest.raises(ProvenanceError):
                freeze_execution(
                    authority=fixture["authority"],
                    starting_state_root=fixture["state_root"],
                    routine_admission=admission,
                    repository=repository,
                    resolve_content=fixture["content"].__getitem__,
                    read_content=raw.__getitem__,
                    live_facts=fixture["facts"],
                    checked_at="2026-08-20T01:00:00Z",
                )


def test_routine_execution_rejects_candidate_experiment_and_live_budget_drift() -> None:
    with tempfile.TemporaryDirectory() as directory:
        fixture = routine_execution_fixture(Path(directory))
        for mutation in (
            "candidate-bytes",
            "experiment-bytes",
            "live-budget",
            "review-report",
            "result-validation",
        ):
            raw = copy.deepcopy(fixture["raw"])
            content = copy.deepcopy(fixture["content"])
            if mutation == "candidate-bytes":
                raw[fixture["state_root"]][
                    "project/state/candidate/main.py"
                ] = b"def candidate(): return 2\n"
            elif mutation == "experiment-bytes":
                raw[fixture["state_root"]][
                    "project/state/experiment.yaml"
                ] += b"extra: sample\n"
            elif mutation == "live-budget":
                content[next(iter(fixture["facts"].values()))["receipt_root"]][
                    "receipt_facts"
                ]["routine_slot_current"]["document"]["available_unprotected"] = 0
            elif mutation == "review-report":
                raw[fixture["state_root"]][
                    "project/state/implementation-review.md"
                ] = b"IMPLEMENTATION_REPAIR_REQUIRED: blocking defect\n"
            else:
                raw[fixture["state_root"]][
                    "project/state/materialization-result-validation.yaml"
                ] = yaml.safe_dump(
                    {
                        "result_structure_ready": True,
                        "blocking_findings": [],
                        "repair_findings": [],
                        "extra_unbound": True,
                    },
                    sort_keys=False,
                ).encode()
            repository = NodeRepository(Path(directory) / f"nodes-{mutation}")
            repository.write_all(fixture["nodes"].values())
            with pytest.raises(ProvenanceError):
                freeze_execution(
                    authority=fixture["authority"],
                    starting_state_root=fixture["state_root"],
                    routine_admission=fixture["admission"],
                    repository=repository,
                    resolve_content=content.__getitem__,
                    read_content=raw.__getitem__,
                    live_facts=fixture["facts"],
                    checked_at="2026-08-20T01:00:00Z",
                )


def test_routine_cli_rejects_caller_selected_slot_index() -> None:
    with tempfile.TemporaryDirectory() as directory:
        repository = NodeRepository(Path(directory) / "nodes")
        with pytest.raises(ProvenanceError, match="complete legacy or routine shape"):
            apply_operation(
                {
                    "contract_version": REQUEST_CONTRACT,
                    "operation": "freeze-execution",
                    "authority_id": "frontier-authority-root-sha256:" + "1" * 64,
                    "starting_state_root": typed_root("project-state", "state"),
                    "content_bindings": [],
                    "routine_admission": {},
                    "live_facts": {},
                    "checked_at": "2026-08-20T01:00:00Z",
                    "slot_index_root": str(Path(directory) / "alternate"),
                },
                repository,
            )


def test_release_git_and_portable_adapters_share_one_raw_byte_content_root() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory) / "repo"
        root.mkdir()
        initialize(root)
        (root / ".gitattributes").write_text("*.txt text eol=crlf\n")
        closed_directory = root / "input-dir"
        closed_directory.mkdir()
        ignored = closed_directory / "raw.txt"
        ignored.write_bytes(b"raw-lf\n")
        (root / ".gitignore").write_text("input-dir/\n")
        sources = [ArtifactSource("release/inputs/raw.txt", ignored)]
        collections = [
            ClosedCollection(
                "release/inputs", closed_directory, ("release/inputs/raw.txt",)
            )
        ]
        ordinary_tree = git(root, "write-tree")
        worktree_status = git(root, "status", "--porcelain", "--untracked-files=all")

        git_store = WorkflowReleaseGitStore(root)
        git_manifest = git_store.capture_release(
            sources,
            closed_collections=collections,
            created_at="2026-08-17T00:00:00Z",
        )
        portable_root = Path(directory) / "portable"
        portable_manifest = PortableBundleStore().capture(
            sources,
            portable_root,
            domain="workflow-release",
            closed_collections=collections,
        )

        assert git_manifest["content_root"] == portable_manifest["content_root"]
        assert git_store.raw_artifacts(git_manifest)["release/inputs/raw.txt"] == b"raw-lf\n"
        assert PortableBundleStore().verify(portable_root)["verified"] is True
        assert git(root, "write-tree") == ordinary_tree
        assert git(root, "status", "--porcelain", "--untracked-files=all") == worktree_status
        ignored.write_bytes(b"changed\n")
        assert (
            git_store.compare_release_sources(
                git_manifest,
                sources,
                closed_collections=collections,
            )["verified"]
            is False
        )


def test_git_verifier_checks_object_format_and_parent_binding() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        initialize(root)
        source = root / "source.bin"
        source.write_bytes(b"source")
        store = WorkflowReleaseGitStore(root)
        manifest = store.capture_release(
            [ArtifactSource("release/source.bin", source)],
            created_at="2026-08-17T00:00:00Z",
        )
        wrong_format = copy.deepcopy(manifest)
        wrong_format["storage"]["object_format"] = "sha256"
        with pytest.raises(ProvenanceError, match="object format"):
            store.verify(wrong_format)
        wrong_parent = copy.deepcopy(manifest)
        wrong_parent["storage"]["parent_commit"] = manifest["storage"]["commit"]
        with pytest.raises(ProvenanceError, match="parent commit"):
            store.verify(wrong_parent)


def test_export_from_git_verifies_without_dot_git() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory) / "repo"
        root.mkdir()
        initialize(root)
        source = root / "untracked.bin"
        source.write_bytes(b"portable\x00bytes")
        git_store = WorkflowReleaseGitStore(root)
        manifest = git_store.capture_release(
            [ArtifactSource("release/artifact.bin", source)],
            created_at="2026-08-17T00:00:00Z",
        )
        destination = Path(directory) / "export"
        exported = PortableBundleStore().export_from_git(
            git_store, manifest, destination
        )

        assert exported["content_root"] == manifest["content_root"]
        assert not (destination / ".git").exists()
        assert PortableBundleStore().verify(destination)["verified"] is True


def test_portable_bundle_rejects_unexpected_member() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        source = root / "source.txt"
        source.write_text("value\n")
        destination = root / "bundle"
        store = LegacyProjectFixture()
        store.capture(
            "decision",
            [ArtifactSource("project/decision/source.txt", source)],
            destination,
            project_root=root,
        )
        (destination / "extra.txt").write_text("unexpected\n")
        with pytest.raises(ProvenanceError, match="unexpected"):
            store.verify(destination, expected_role="decision")


def test_portable_bundle_rejects_external_manifest_symlink() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        source = root / "source.txt"
        source.write_text("value\n")
        bundle = root / "bundle"
        store = LegacyProjectFixture()
        store.capture(
            "decision",
            [ArtifactSource("project/decision/source.txt", source)],
            bundle,
            project_root=root,
        )
        external = root / "external-manifest.json"
        (bundle / "manifest.json").replace(external)
        (bundle / "manifest.json").symlink_to(external)
        with pytest.raises(ProvenanceError, match="missing or unsafe"):
            store.verify(bundle, expected_role="decision")


def test_closed_collection_rejects_unlisted_directory_member() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        collection = root / "collection"
        collection.mkdir()
        selected = collection / "selected.txt"
        selected.write_text("selected\n")
        (collection / "extra.txt").write_text("extra\n")
        with pytest.raises(ProvenanceError, match="membership mismatch"):
            LegacyProjectFixture().capture(
                "decision",
                [ArtifactSource("project/decision/inputs/selected.txt", selected)],
                root / "bundle",
                project_root=root,
                closed_collections=[
                    ClosedCollection(
                        "project/decision/inputs",
                        collection,
                        ("project/decision/inputs/selected.txt",),
                    )
                ],
            )


@pytest.mark.parametrize(
    "logical_name",
    (
        ".agents/skills/frontier/SKILL.md",
        "skills/frontier/SKILL.md",
        "validator_source.py",
        "project/decision/.agents/skills/frontier/SKILL.md",
        "project/decision/.claude/skills/frontier/SKILL.md",
        "project/decision/packages/service/.claude/agents/reviewer.md",
    ),
)
def test_project_capture_rejects_workflow_logical_names(logical_name: str) -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        source = root / "decision.txt"
        source.write_text("project decision\n")
        with pytest.raises(ProvenanceError):
            LegacyProjectFixture().capture(
                "decision",
                [ArtifactSource(logical_name, source)],
                root / "bundle",
                project_root=root,
            )


def test_git_capture_rejects_project_domains() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        initialize(root)
        source = root / "decision.txt"
        source.write_text("project decision\n")
        with pytest.raises(ProvenanceError, match="reserved for workflow releases"):
            GitSnapshotStore(root).capture(
                [ArtifactSource("project/decision/decision.txt", source)],
                domain="project-decision",
                created_at="2026-08-17T00:00:00Z",
            )


def test_project_capture_allows_task_and_technology_names() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        skills = root / "skills"
        skills.mkdir()
        model = skills / "model.py"
        validator = root / "validator_source.py"
        model.write_text("MODEL = object()\n")
        validator.write_text("def validate(value): return value\n")
        result = LegacyProjectFixture().capture(
            "state",
            [
                ArtifactSource("project/state/src/skills/model.py", model),
                ArtifactSource("project/state/src/validator_source.py", validator),
            ],
            root / "bundle",
            project_root=root,
        )
        assert result["domain"] == "project-state"


def test_project_capture_accepts_exact_frozen_input_source_path() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        source = root / "records" / "decision" / "digest.json"
        source.parent.mkdir(parents=True)
        source.write_text('{"decision":"exact"}\n')
        bundle = root / "bundle"

        result = LegacyProjectFixture().capture(
            "state",
            [
                ArtifactSource(
                    "project/state/frozen-inputs/records/decision/digest.json",
                    source,
                )
            ],
            bundle,
            project_root=root,
        )

        assert result["domain"] == "project-state"
        assert LegacyProjectFixture().verify(bundle, expected_role="state")[
            "verified"
        ] is True


@pytest.mark.parametrize(
    "logical_suffix",
    (
        "decision.json",
        "records/decision/alias.json",
        "records/decision/object",
    ),
)
def test_project_capture_rejects_inexact_frozen_input_source_path(
    logical_suffix: str,
) -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        source = root / "records" / "decision" / "digest.json"
        source.parent.mkdir(parents=True)
        source.write_text('{"decision":"same bytes"}\n')
        bundle = root / "bundle"

        with pytest.raises(
            ProvenanceError,
            match="frozen input logical name must match its project-relative source path",
        ):
            LegacyProjectFixture().capture(
                "state",
                [
                    ArtifactSource(
                        f"project/state/frozen-inputs/{logical_suffix}", source
                    )
                ],
                bundle,
                project_root=root,
            )

        assert not bundle.exists()


@pytest.mark.parametrize(
    "workflow_prefix",
    (
        (".agents", "skills"),
        (".codex", "skills"),
        (".claude", "skills"),
        (".claude", "commands"),
        (".claude", "agents"),
        ("packages", "service", ".claude", "skills"),
    ),
)
def test_project_capture_rejects_explicit_workflow_roots(
    workflow_prefix: tuple[str, ...],
) -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        workflow_root = root.joinpath(*workflow_prefix, "frontier")
        workflow_root.mkdir(parents=True)
        source = workflow_root / "module.py"
        source.write_text("WORKFLOW = True\n")
        with pytest.raises(ProvenanceError, match="cannot capture workflow source"):
            LegacyProjectFixture().capture(
                "state",
                [ArtifactSource("project/state/src/module.py", source)],
                root / "bundle",
                project_root=root,
            )


def test_project_under_codex_ancestor_is_not_misclassified() -> None:
    with tempfile.TemporaryDirectory() as directory:
        project_root = Path(directory) / ".codex" / "worktrees" / "ordinary-project"
        project_root.mkdir(parents=True)
        source = project_root / "model.py"
        source.write_text("MODEL = object()\n")
        result = LegacyProjectFixture().capture(
            "state",
            [ArtifactSource("project/state/model.py", source)],
            project_root / "bundle",
            project_root=project_root,
        )
        assert result["domain"] == "project-state"


def test_nonworkflow_claude_project_directory_is_allowed() -> None:
    with tempfile.TemporaryDirectory() as directory:
        project_root = Path(directory) / "project"
        source_root = project_root / ".claude" / "data"
        source_root.mkdir(parents=True)
        source = source_root / "model.json"
        source.write_text('{"model":"project-data"}\n')
        result = LegacyProjectFixture().capture(
            "state",
            [ArtifactSource("project/state/.claude/data/model.json", source)],
            project_root / "bundle",
            project_root=project_root,
        )
        assert result["domain"] == "project-state"


def test_project_capture_rejects_sources_outside_project_root() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        project_root = root / "project"
        project_root.mkdir()
        source = root / "outside.txt"
        source.write_text("outside\n")
        with pytest.raises(ProvenanceError, match="outside project_root"):
            LegacyProjectFixture().capture(
                "state",
                [ArtifactSource("project/state/outside.txt", source)],
                project_root / "bundle",
                project_root=project_root,
            )


def test_git_verify_rejects_a_project_domain_manifest() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        initialize(root)
        source = root / "release.txt"
        source.write_text("release\n")
        store = WorkflowReleaseGitStore(root)
        manifest = store.capture_release(
            [ArtifactSource("release/release.txt", source)],
            created_at="2026-08-17T00:00:00Z",
        )
        forged = copy.deepcopy(manifest)
        forged["domain"] = "project-decision"
        forged["artifacts"][0]["logical_name"] = "project/decision/input.txt"
        with pytest.raises(ProvenanceError, match="reserved for workflow releases"):
            store.verify(forged)


def test_project_consequence_resolver_rejects_workflow_release_bindings() -> None:
    with pytest.raises(ProvenanceError, match="invalid content binding"):
        cli_content_resolver(
            [
                {
                    "adapter": "git-snapshot/1",
                    "repo_root": "/unused",
                    "reference": "refs/frontier/release",
                    "manifest_path": "/unused/manifest.json",
                }
            ]
        )


def test_typed_chain_accepts_immediate_parents_and_live_facts() -> None:
    content_root = "frontier-content-root-sha256:" + "a" * 64
    _, _, _, outcome, nodes = chain(content_root)
    result = verify_for(
        outcome["node_id"],
        nodes.__getitem__,
        content_resolver,
        consequence="outcome-publication",
        live_facts={
            "authority_current": fact(content_root),
            "inputs_current": fact(content_root),
            "budget_accounted": fact(content_root),
            "prior_external_effects_known": fact(content_root),
        },
        checked_at="2026-08-17T01:00:00Z",
    )
    assert result["ready"] is True
    assert result["node_count"] == 5


def test_action_verification_rejects_a_manually_built_partial_decision() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        source = root / "repair-only.txt"
        source.write_text("partial\n")
        bundle = root / "partial-decision"
        manifest = LegacyProjectFixture().capture(
            "decision",
            [ArtifactSource("project/decision/repair-only.txt", source)],
            bundle,
            project_root=root,
        )
        decision_root = manifest["content_root"]
        TEST_DOMAINS[decision_root] = "project-decision"
        decision = freeze_decision(decision_root=decision_root)
        validation = attest(
            decision,
            validation_report_root=typed_root("review-report", "partial"),
            verdict="ready",
            findings=[],
        )
        authority = build_node(
            "authority",
            {},
            parents=[
                {"edge": "decision", "node_id": decision["node_id"]},
                {"edge": "attestation", "node_id": validation["node_id"]},
            ],
            artifact_roots=[typed_root("project-authority", "partial")],
        )
        nodes = {
            node["node_id"]: node for node in (decision, validation, authority)
        }

        def resolve(content_root: str) -> dict[str, object]:
            if content_root == decision_root:
                return LegacyProjectFixture().verify(bundle, expected_role="decision")
            return content_resolver(content_root)

        with pytest.raises(ProvenanceError, match="complete review subject"):
            verify_for(
                authority["node_id"],
                nodes.__getitem__,
                resolve,
                consequence="acknowledgment",
            )


def test_acknowledgment_verifies_complete_static_authority_without_live_facts() -> None:
    content_root = "frontier-content-root-sha256:" + "6" * 64
    _, authority, _, _, nodes = chain(content_root)

    result = verify_for(
        authority["node_id"],
        nodes.__getitem__,
        content_resolver,
        consequence="acknowledgment",
        live_facts={},
        checked_at=None,
    )

    assert result["ready"] is True
    assert result["consequence_contract"] == "frontier-consequence-gates/2"
    assert result["live_facts_checked"] == []


def test_acknowledgment_does_not_inherit_live_attestation_freshness() -> None:
    decision = freeze_decision(
        decision_root=typed_root("project-decision", "live-acknowledgment")
    )
    validation = attest(
        decision,
        validation_report_root=typed_root("review-report", "live-acknowledgment"),
        verdict="ready",
        findings=[],
        freshness="live",
        observed_at="2026-08-17T00:00:00Z",
        expires_at="2026-08-18T00:00:00Z",
        invalidation_rule={"required_facts": ["inputs_current"]},
    )
    authority = build_node(
        "authority",
        {},
        parents=[
            {"edge": "decision", "node_id": decision["node_id"]},
            {"edge": "attestation", "node_id": validation["node_id"]},
        ],
        artifact_roots=[typed_root("project-authority", "live-acknowledgment")],
    )
    nodes = {
        node["node_id"]: node for node in (decision, validation, authority)
    }

    without_clock = verify_for(
        authority["node_id"],
        nodes.__getitem__,
        content_resolver,
        consequence="acknowledgment",
        live_facts={},
        checked_at=None,
    )
    after_expiry = verify_for(
        authority["node_id"],
        nodes.__getitem__,
        content_resolver,
        consequence="acknowledgment",
        live_facts={},
        checked_at="2030-01-01T00:00:00Z",
    )

    assert without_clock == after_expiry
    assert without_clock["ready"] is True
    with pytest.raises(ProvenanceError, match="live attestation has expired"):
        verify_for(
            authority["node_id"],
            nodes.__getitem__,
            content_resolver,
            consequence="execution",
            live_facts={},
            checked_at="2030-01-01T00:00:00Z",
        )


def test_live_fact_failure_does_not_reinterpret_static_chain() -> None:
    content_root = "frontier-content-root-sha256:" + "b" * 64
    _, _, _, outcome, nodes = chain(content_root)
    result = verify_for(
        outcome["node_id"],
        nodes.__getitem__,
        content_resolver,
        consequence="outcome-publication",
        live_facts={
            "authority_current": fact(content_root),
            "inputs_current": fact(content_root),
            "budget_accounted": {},
            "prior_external_effects_known": fact(content_root),
        },
        checked_at="2026-08-17T01:00:00Z",
    )
    assert result["static_chain_verified"] is True
    assert result["ready"] is False
    assert result["unresolved_live_facts"] == ["budget_accounted"]


def test_live_attestation_requires_explicit_current_fact() -> None:
    content_root = "frontier-content-root-sha256:" + "2" * 64
    TEST_DOMAINS[content_root] = "live-receipt"
    decision_root = typed_root("project-decision", content_root)
    report_root = typed_root("review-report", content_root)
    decision = freeze_decision(decision_root=decision_root)
    validation = attest(
        decision,
        validation_report_root=report_root,
        verdict="ready",
        findings=[],
        freshness="live",
        observed_at="2026-08-17T00:00:00Z",
        expires_at="2026-08-18T00:00:00Z",
        invalidation_rule={"required_facts": ["inputs_current"]},
    )
    nodes = {node["node_id"]: node for node in (decision, validation)}
    result = verify_for(
        validation["node_id"],
        nodes.__getitem__,
        content_resolver,
        consequence="review",
        checked_at="2026-08-17T01:00:00Z",
    )
    assert result["ready"] is False
    assert result["unresolved_live_facts"] == [
        "inputs_current"
    ]


def test_live_attestation_cannot_authorize_before_its_observation() -> None:
    content_root = "frontier-content-root-sha256:" + "9" * 64
    TEST_DOMAINS[content_root] = "live-receipt"
    decision_root = typed_root("project-decision", content_root)
    report_root = typed_root("review-report", content_root)
    decision = freeze_decision(decision_root=decision_root)
    validation = attest(
        decision,
        validation_report_root=report_root,
        verdict="ready",
        findings=[],
        freshness="live",
        observed_at="2030-01-01T00:00:00Z",
        expires_at="2040-01-01T00:00:00Z",
        invalidation_rule={"required_facts": ["inputs_current"]},
    )
    nodes = {node["node_id"]: node for node in (decision, validation)}
    with pytest.raises(ProvenanceError, match="observation is in the future"):
        verify_for(
            validation["node_id"],
            nodes.__getitem__,
            content_resolver,
            consequence="review",
            live_facts={"inputs_current": fact(content_root)},
            checked_at="2026-08-17T01:00:00Z",
        )


def test_cross_decision_attestation_replay_fails() -> None:
    root_a = "frontier-content-root-sha256:" + "c" * 64
    root_b = "frontier-content-root-sha256:" + "d" * 64
    decision_a = freeze_decision(decision_root=root_a)
    decision_b = freeze_decision(decision_root=root_b)
    validation_a = attest(
        decision_a,
        validation_report_root=typed_root("review-report", root_a),
        verdict="ready",
        findings=[],
    )
    with pytest.raises(ProvenanceError, match="does not attest"):
        bind_authority(
            authority_root=typed_root("project-authority", root_b),
            decision=decision_b,
            validation=validation_a,
        )


def test_attestation_rejects_workflow_contract_and_blocking_ready_finding() -> None:
    content_root = "frontier-content-root-sha256:" + "3" * 64
    decision = freeze_decision(decision_root=content_root)
    with pytest.raises(ProvenanceError, match="unknown or missing fields"):
        build_node(
            "attestation",
            {
                "subject_root": decision["node_id"],
                "validator_contract": "frontier-test-validator/1",
                "verdict": "ready",
                "findings": [],
                "freshness": "immutable",
                "observed_at": None,
                "expires_at": None,
                "invalidation_rule": None,
            },
            parents=[{"edge": "subject", "node_id": decision["node_id"]}],
            artifact_roots=[typed_root("review-report", content_root)],
        )
    with pytest.raises(ProvenanceError, match="block or repair"):
        attest(
            decision,
            validation_report_root=typed_root("review-report", content_root),
            verdict="ready",
            findings=[{"effect": "block", "code": "NO"}],
        )


@pytest.mark.parametrize(
    ("operation_request", "removed_field"),
    [
        (
            {"operation": "freeze-decision", "decision_root": "unused"},
            "semantic_contract",
        ),
        (
            {
                "operation": "attest",
                "subject_id": "unused",
                "validation_report_root": "unused",
                "verdict": "ready",
                "findings": [],
                "freshness": "immutable",
                "observed_at": None,
                "expires_at": None,
                "invalidation_rule": None,
            },
            "validator_contract",
        ),
        (
            {
                "operation": "bind-authority",
                "authority_root": "unused",
                "decision_id": "unused",
                "attestation_id": "unused",
            },
            "authority_contract",
        ),
        (
            {
                "operation": "freeze-execution",
                "authority_id": "unused",
                "starting_state_root": "unused",
            },
            "execution_contract",
        ),
        (
            {
                "operation": "record-outcome",
                "execution_id": "unused",
                "outcome_root": "unused",
            },
            "outcome_contract",
        ),
    ],
)
def test_current_cli_rejects_workflow_contract_fields(
    operation_request: dict[str, object], removed_field: str
) -> None:
    with tempfile.TemporaryDirectory() as directory:
        request = {
            "contract_version": REQUEST_CONTRACT,
            **operation_request,
            removed_field: "frontier-workflow/1",
        }
        with pytest.raises(ProvenanceError, match="request fields must be exactly"):
            apply_operation(request, NodeRepository(Path(directory) / "nodes"))


def test_project_nodes_and_manifests_reject_embedded_workflow_bindings() -> None:
    root = typed_root("project-decision", "closed-payload")
    with pytest.raises(ProvenanceError, match="payload must be empty"):
        build_node(
            "decision",
            {
                "workflow_source_binding": {
                    "identity": "sha256:" + "a" * 64
                },
            },
            artifact_roots=[root],
        )
    with pytest.raises(
        ProvenanceError, match="metadata may contain only executable"
    ):
        authority_payload(
            [
                {
                    "logical_name": "project/decision/decision.json",
                    "kind": "blob",
                    "behavioral_metadata": {
                        "workflow_source_identity": "sha256:" + "a" * 64
                    },
                    "size": 1,
                    "content_sha256": "0" * 64,
                }
            ],
            domain="project-decision",
        )


def test_workflow_release_content_cannot_satisfy_a_project_role() -> None:
    release_root = typed_root("workflow-release", "release")
    decision = freeze_decision(decision_root=release_root)
    nodes = {decision["node_id"]: decision}
    with pytest.raises(ProvenanceError, match="project-decision domain"):
        verify_for(
            decision["node_id"],
            nodes.__getitem__,
            content_resolver,
            consequence="review",
        )


def test_verification_requires_real_content_and_consequence_facts() -> None:
    content_root = "frontier-content-root-sha256:" + "4" * 64
    decision, authority, _, _, nodes = chain(content_root)

    def missing(_: str) -> dict[str, object]:
        raise ProvenanceError("missing content")

    with pytest.raises(ProvenanceError, match="missing content"):
        verify_for(
            decision["node_id"], nodes.__getitem__, missing, consequence="review"
        )
    result = verify_for(
        authority["node_id"],
        nodes.__getitem__,
        content_resolver,
        consequence="spend",
        live_facts={},
        checked_at="2026-08-17T01:00:00Z",
    )
    assert result["ready"] is False
    assert "budget_current" in result["unresolved_live_facts"]
    with pytest.raises(ProvenanceError, match="unsupported consequence"):
        verify_for(
            authority["node_id"],
            nodes.__getitem__,
            content_resolver,
            consequence="custom",
        )


def test_manual_external_receipt_manifest_rejects_empty_semantics() -> None:
    with pytest.raises(ProvenanceError, match="external receipt metadata"):
        authority_payload(
            [
                {
                    "logical_name": "receipts/receipt.txt",
                    "kind": "external-receipt",
                    "behavioral_metadata": {
                        "fact": "",
                        "status": "pass",
                        "observed_at": "",
                        "expires_at": "",
                    },
                    "size": 1,
                    "content_sha256": "0" * 64,
                }
            ],
            domain="live-receipt",
        )


def test_expired_live_receipt_cannot_be_replayed_for_spend() -> None:
    content_root = "frontier-content-root-sha256:" + "5" * 64
    _, authority, _, _, nodes = chain(content_root)
    names = {
        "authority_current",
        "budget_current",
        "reservation_current",
        "inputs_current",
        "resources_available",
    }

    def expired(root: str) -> dict[str, object]:
        result: dict[str, object] = {
            "content_root": root,
            "domain": TEST_DOMAINS[root],
            "verified": True,
            "receipt_facts": {
                name: {
                    "status": "pass",
                    "observed_at": "2020-01-01T00:00:00Z",
                    "expires_at": "2020-01-01T00:05:00Z",
                }
                for name in names
            },
        }
        if TEST_DOMAINS[root] == "project-decision":
            result["review_subject"] = {
                "contract_version": "frontier-review-subject/2",
                "role_adapter": "frontier-review-role-adapter/2",
                "review_kind": "entry",
                "subject_mode": "complete",
                "semantic_projection": {"affected_scope": "expired receipt test"},
            }
        return result

    result = verify_for(
        authority["node_id"],
        nodes.__getitem__,
        expired,
        consequence="spend",
        live_facts={name: fact(content_root) for name in names},
        checked_at="2026-08-17T00:00:00Z",
    )
    assert result["ready"] is False
    assert set(result["unresolved_live_facts"]) == names


def test_missing_parent_and_tampered_node_fail_closed() -> None:
    content_root = "frontier-content-root-sha256:" + "e" * 64
    _, _, _, outcome, nodes = chain(content_root)
    missing = dict(nodes)
    execution_parent = outcome["parents"][0]["node_id"]
    missing.pop(execution_parent)
    with pytest.raises(KeyError):
        verify_chain(outcome["node_id"], missing.__getitem__)

    tampered = copy.deepcopy(nodes)
    tampered[outcome["node_id"]]["payload"]["workflow_release"] = "changed"
    with pytest.raises(ProvenanceError, match="payload must be empty"):
        verify_chain(outcome["node_id"], tampered.__getitem__)


def test_v1_adapter_allows_completion_but_not_new_authority() -> None:
    inventory = {
        "contract_version": "frontier-v1-completion-inventory/1",
        "rollout_cutoff": "2026-08-17T00:00:00Z",
        "active_authorities": [
            {
                "state": "acknowledged",
                "authority_root": "legacy-authority",
                "contract_version": "frontier-dispatch-identity/2",
                "scope_root": "legacy-packet",
            }
        ],
    }
    require_v1_completion(
        inventory,
        authority_root="legacy-authority",
        requested_descendant="execution-start",
        scope_root="legacy-packet",
        verified_parent_role="acknowledgment",
    )
    with pytest.raises(ProvenanceError, match="only completion"):
        require_v1_completion(
            inventory,
            authority_root="legacy-authority",
            requested_descendant="authorization",
            scope_root="legacy-packet",
            verified_parent_role="authority",
        )


def test_source_modules_expand_dependencies_and_ignore_unrelated_files() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        (root / "common.txt").write_text("common\n")
        (root / "direction.txt").write_text("direction\n")
        (root / "unrelated.txt").write_text("one\n")
        manifest = {
            "contract_version": "frontier-source-modules/1",
            "modules": {
                "common": {"depends_on": [], "files": ["common.txt"]},
                "direction": {
                    "depends_on": ["common"],
                    "files": ["direction.txt"],
                },
            },
        }
        closure = validate_source_modules(manifest, root)
        assert closure["direction"] == {"common.txt", "direction.txt"}
        before = source_module_root(manifest, root, "direction")
        (root / "unrelated.txt").write_text("two\n")
        assert source_module_root(manifest, root, "direction") == before
        (root / "common.txt").write_text("changed\n")
        assert source_module_root(manifest, root, "direction") != before


def test_workflow_release_mutation_does_not_change_project_identity() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        project = root / "project.txt"
        workflow = root / "workflow.py"
        project.write_text("project-v1\n")
        workflow.write_text("workflow-v1\n")
        prepared = prepare_entry_bundle(root, root / "project-v1")
        project_manifest = LegacyProjectFixture().verify(
            root / "project-v1/snapshot", expected_role="decision"
        )
        decision = freeze_decision(decision_root=prepared["content_root"])
        report_root = typed_root("review-report", "stable-report")
        authority_root = typed_root("project-authority", "stable-authority")
        validation = attest(
            decision,
            validation_report_root=report_root,
            verdict="ready",
            findings=[],
        )
        authority = bind_authority(
            authority_root=authority_root,
            decision=decision,
            validation=validation,
            decision_bundle=root / "project-v1/snapshot",
        )
        release_v1 = PortableBundleStore().capture(
            [ArtifactSource("release/workflow.py", workflow)],
            root / "release-v1",
            domain="workflow-release",
        )
        workflow.write_text("workflow-v2\n")
        release_v2 = PortableBundleStore().capture(
            [ArtifactSource("release/workflow.py", workflow)],
            root / "release-v2",
            domain="workflow-release",
        )
        same_decision = freeze_decision(
            decision_root=project_manifest["content_root"]
        )
        same_validation = attest(
            same_decision,
            validation_report_root=report_root,
            verdict="ready",
            findings=[],
        )
        same_authority = bind_authority(
            authority_root=authority_root,
            decision=same_decision,
            validation=same_validation,
            decision_bundle=root / "project-v1/snapshot",
        )
        assert release_v1["content_root"] != release_v2["content_root"]
        assert same_decision["node_id"] == decision["node_id"]
        assert same_validation["node_id"] == validation["node_id"]
        assert same_authority["node_id"] == authority["node_id"]
        assert release_v1["content_root"] not in decision["artifact_roots"]
        assert release_v2["content_root"] not in decision["artifact_roots"]


def test_project_byte_mutation_changes_project_root_and_node() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        project = root / "project.txt"
        project.write_text("project-v1\n")
        first = LegacyProjectFixture().capture(
            "decision",
            [ArtifactSource("project/decision/project.txt", project)],
            root / "project-v1",
            project_root=root,
        )
        project.write_text("project-v2\n")
        second = LegacyProjectFixture().capture(
            "decision",
            [ArtifactSource("project/decision/project.txt", project)],
            root / "project-v2",
            project_root=root,
        )
        first_node = freeze_decision(decision_root=first["content_root"])
        second_node = freeze_decision(decision_root=second["content_root"])
        assert first["content_root"] != second["content_root"]
        assert first_node["node_id"] != second_node["node_id"]


def test_source_module_audit_rejects_imported_but_unlisted_local_file() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        (root / "main.py").write_text("import helper\n")
        (root / "helper.py").write_text("VALUE = 1\n")
        manifest = {
            "contract_version": "frontier-source-modules/1",
            "modules": {
                "core": {"depends_on": [], "files": ["main.py"]},
            },
        }
        with pytest.raises(ProvenanceError, match="omits Python dependencies"):
            audit_python_dependencies(manifest, root)


def test_source_module_audit_ignores_same_stem_outside_import_path() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        (root / "main.py").write_text("import json\n")
        (root / "unrelated").mkdir()
        (root / "unrelated/json.py").write_text("VALUE = 1\n")
        manifest = {
            "contract_version": "frontier-source-modules/1",
            "modules": {
                "core": {"depends_on": [], "files": ["main.py"]},
            },
        }
        assert audit_python_dependencies(manifest, root)["core"] == {"main.py"}


def test_source_module_audit_resolves_package_and_relative_imports() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        (root / "package").mkdir()
        (root / "package/__init__.py").write_text("from . import helper\n")
        (root / "package/helper.py").write_text("VALUE = 1\n")
        manifest = {
            "contract_version": "frontier-source-modules/1",
            "modules": {
                "core": {"depends_on": [], "files": ["package/__init__.py"]},
            },
        }
        with pytest.raises(ProvenanceError, match="omits Python dependencies"):
            audit_python_dependencies(manifest, root)


def test_live_source_module_manifest_covers_existing_files() -> None:
    skill = Path(__file__).parent.parent
    skills_root = skill.parent
    manifest = yaml.safe_load(
        (skill / "references/source-modules.yaml").read_text()
    )
    closure = validate_source_modules(manifest, skills_root)
    assert {
        "graph-core",
        "storage-recovery",
        "provenance-runtime",
        "direction",
        "execution",
        "evidence",
        "claims",
        "legacy-validation",
        "release-validation",
    } == set(closure)
    assert all(source_module_root(manifest, skills_root, name) for name in closure)
    assert (
        "frontier-optimization/scripts/frontier_provenance/stores.py"
        not in closure["direction"]
    )
    assert (
        "frontier-optimization/scripts/validate_candidate_package.py"
        in closure["legacy-validation"]
    )


def test_node_repository_is_immutable_and_recomputes_loaded_identity() -> None:
    with tempfile.TemporaryDirectory() as directory:
        repository = NodeRepository(Path(directory))
        content_root = "frontier-content-root-sha256:" + "f" * 64
        decision = freeze_decision(decision_root=content_root)
        path = repository.write(decision)
        assert repository.load(decision["node_id"]) == decision
        tampered = json.loads(path.read_text())
        tampered["payload"]["workflow_release"] = "changed"
        path.write_text(json.dumps(tampered, sort_keys=True, separators=(",", ":")))
        with pytest.raises(ProvenanceError, match="payload must be empty"):
            repository.load(decision["node_id"])


def test_cli_facade_freezes_and_verifies_a_decision() -> None:
    with tempfile.TemporaryDirectory() as directory:
        repository = NodeRepository(Path(directory))
        source = Path(directory) / "decision.txt"
        source.write_text("one exact decision\n")
        prepared = prepare_entry_bundle(Path(directory), Path(directory) / "prepared")
        bindings: list[dict[str, str]] = [
            {
                "adapter": "git-reference/1",
                "path": str(Path(directory) / "prepared/snapshot"),
            }
        ]
        roots: dict[str, str] = {"project-decision": prepared["content_root"]}
        for domain in (
            "review-report",
            "project-authority",
            "project-state",
            "project-outcome",
        ):
            bundle = Path(directory) / domain
            artifacts = [
                {
                    "logical_name": DOMAIN_PREFIXES[domain] + "project-record.txt",
                    "path": str(source),
                    "kind": "blob",
                    "behavioral_metadata": {},
                }
            ]
            captured = apply_operation(
                {
                    "contract_version": REQUEST_CONTRACT,
                    "operation": "capture-project",
                    "role": DOMAIN_ROLES[domain],
                    "project_root": str(Path(directory)),
                        "artifacts": artifacts,
                    "closed_collections": [],
                    "destination": str(bundle),
                },
                repository,
            )
            roots[domain] = captured["content_root"]
            bindings.append({"adapter": "git-reference/1", "path": str(bundle)})
        receipt_bundle = Path(directory) / "live-receipt"
        receipt = apply_operation(
            {
                "contract_version": REQUEST_CONTRACT,
                "operation": "capture-project",
                "role": "receipt",
                "project_root": str(Path(directory)),
                "artifacts": [
                    *[
                        {
                            "logical_name": f"receipts/{name}.txt",
                            "path": str(source),
                            "kind": "external-receipt",
                            "behavioral_metadata": {
                                "fact": name,
                                "status": "pass",
                                "observed_at": "2026-08-17T00:00:00Z",
                                "expires_at": "2026-08-17T02:00:00Z",
                            },
                        }
                        for name in (
                            "authority_current",
                            "inputs_current",
                            "budget_accounted",
                            "prior_external_effects_known",
                        )
                    ],
                ],
                "closed_collections": [],
                "destination": str(receipt_bundle),
            },
            repository,
        )
        bindings.append(
            {"adapter": "git-reference/1", "path": str(receipt_bundle)}
        )
        frozen = apply_operation(
            {
                "contract_version": REQUEST_CONTRACT,
                "operation": "freeze-decision",
                "decision_root": roots["project-decision"],
            },
            repository,
        )
        attestation = apply_operation(
            {
                "contract_version": REQUEST_CONTRACT,
                "operation": "attest",
                "subject_id": frozen["node_id"],
                "validation_report_root": roots["review-report"],
                "verdict": "ready",
                "findings": [],
                "freshness": "immutable",
                "observed_at": None,
                "expires_at": None,
                "invalidation_rule": None,
            },
            repository,
        )
        authority = apply_operation(
            {
                "contract_version": REQUEST_CONTRACT,
                "operation": "bind-authority",
                "authority_root": roots["project-authority"],
                "decision_id": frozen["node_id"],
                "attestation_id": attestation["node_id"],
                "content_bindings": bindings,
            },
            repository,
        )
        acknowledged = apply_operation(
            {
                "contract_version": REQUEST_CONTRACT,
                "operation": "verify",
                "root_id": authority["node_id"],
                "consequence": "acknowledgment",
                "live_facts": {},
                "checked_at": None,
                "content_bindings": bindings,
            },
            repository,
        )
        assert acknowledged["ready"] is True
        assert acknowledged["live_facts_checked"] == []
        execution = apply_operation(
            {
                "contract_version": REQUEST_CONTRACT,
                "operation": "freeze-execution",
                "authority_id": authority["node_id"],
                "starting_state_root": roots["project-state"],
            },
            repository,
        )
        outcome = apply_operation(
            {
                "contract_version": REQUEST_CONTRACT,
                "operation": "record-outcome",
                "execution_id": execution["node_id"],
                "outcome_root": roots["project-outcome"],
            },
            repository,
        )
        verified = apply_operation(
            {
                "contract_version": REQUEST_CONTRACT,
                "operation": "verify",
                "root_id": outcome["node_id"],
                "consequence": "outcome-publication",
                "live_facts": {
                    name: fact(receipt["content_root"])
                    for name in (
                        "authority_current",
                        "inputs_current",
                        "budget_accounted",
                        "prior_external_effects_known",
                    )
                },
                "checked_at": "2026-08-17T01:00:00Z",
                "content_bindings": bindings,
            },
            repository,
        )
        assert verified["ready"] is True
        assert verified["root_role"] == "outcome"
        exported = apply_operation(
            {
                "contract_version": REQUEST_CONTRACT,
                "operation": "export",
                "root_id": outcome["node_id"],
            },
            repository,
        )
        serialized = json.dumps(exported, sort_keys=True)
        assert "workflow_source" not in serialized
        assert "source_roots" not in serialized
        assert "validator_source" not in serialized


def test_complete_handoff_references_git_and_retained_legacy_roots() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        source = root / "artifact.txt"
        source.write_text("artifact\n")
        outcome, nodes, exporters = portable_project_chain(root, source)
        repository = NodeRepository(root / "nodes")
        repository.write_all(nodes.values())

        save_fixture(root)
        handoff = root / "handoff"
        export_handoff(
            outcome["node_id"],
            repository,
            exporters,
            handoff,
        )
        assert not (handoff / ".git").exists()
        assert verify_handoff(handoff)["verified"] is True
        manifest = json.loads((handoff / "handoff.json").read_text())
        domains = {
            json.loads(
                (root / item["path"] / "manifest.json").read_text()
            )["domain"]
            for item in manifest["content_bindings"]
        }
        assert "workflow-release" not in domains


def test_handoff_rejects_external_manifest_symlink() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        source = root / "artifact.txt"
        source.write_text("artifact\n")
        outcome, nodes, exporters = portable_project_chain(root, source)
        repository = NodeRepository(root / "nodes")
        repository.write_all(nodes.values())

        save_fixture(root)
        handoff = root / "handoff"
        export_handoff(
            outcome["node_id"],
            repository,
            exporters,
            handoff,
        )
        external = root / "external-handoff.json"
        (handoff / "handoff.json").replace(external)
        (handoff / "handoff.json").symlink_to(external)
        with pytest.raises(ProvenanceError, match="missing or unsafe"):
            verify_handoff(handoff)


def test_rollout_closes_legacy_entry_packet_and_authority_writers() -> None:
    scripts = Path(__file__).parent
    rollout_fixture = scripts.parent / "references/provenance-rollout.yaml"
    with tempfile.TemporaryDirectory() as directory:
        repo_root = Path(directory)
        rollout_path = repo_root / ".frontier/provenance-rollout.yaml"
        rollout_path.parent.mkdir(parents=True)
        rollout_path.write_bytes(rollout_fixture.read_bytes())
        commands = [
            [
                str(scripts / "validate_entry_packet.py"),
                "missing.yaml",
                "--phase",
                "draft",
                "--root",
                str(repo_root),
            ],
            [
                str(scripts / "validate_batch_packet.py"),
                "missing.yaml",
                "--phase",
                "draft",
                "--repo-root",
                str(repo_root),
            ],
            [
                str(scripts / "validate_authorization_adoption.py"),
                "missing.yaml",
                "--phase",
                "draft",
                "--root",
                str(repo_root),
            ],
        ]
        for command in commands:
            result = subprocess.run(
                [str(Path(sys.executable)), *command],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            assert result.returncode == 2
            assert b"legacy" in result.stderr


def _w_backed_entry_subject(delivery_scope: list[str]) -> dict[str, bytes]:
    design_identity = "W900-design-sha256:" + "d" * 64
    documents: dict[str, object] = {
        "project/decision/parents/handoff.yaml": {
            "contract_version": "framing-handoff/1"
        },
        "project/decision/selection/evidence-state.yaml": {
            "contract_version": "frontier-selection-evidence-state/1",
            "event_id": "X900",
            "budget": {"ceiling": 4, "actual": 0},
            "selection": {"primary": "B900"},
            "authority": {"current": "planning-only"},
            "resolver": {"first_applicable_row": 12},
            "route_set": {"state": "complete"},
        },
        "project/decision/entry/plan.yaml": {
            "contract_version": "frontier-project-batch-plan/3",
            "batch_id": "B900",
            "maximum_spend": {"proposals": 1},
            "authorization_gate": "exact reviewed authorization",
            "stop_conditions": ["one terminal result"],
            "design_profile": "module",
            "work_plan": "W900",
            "work_plan_revision": 4,
            "design_contract_identity": design_identity,
            "required_design_inputs": ["architecture.md", "interfaces.md"],
            "delivery_scope": delivery_scope,
        },
        "project/decision/entry/work.yaml": {
            "contract_version": "frontier-project-code-work/1",
            "batch_id": "B900",
        },
        "project/decision/entry/target.yaml": {
            "contract_version": "frontier-project-authorization-target/1",
            "target_id": "V900-target-sha256:" + "a" * 64,
            "decision_id": "V900",
            "batch_id": "B900",
            "scope": "complete W900 realization",
            "maximum_spend": {"proposals": 1},
            "stop_boundary": "one terminal result",
            "authorization_question": "Authorize this realization?",
            "authorize_consequence": "permit one bounded execution",
        },
        "project/decision/design/W900/traceability.yaml": {
            "design_contract_identity": design_identity,
            "slices": {
                "foundation": {
                    "delivery_identity": "delivery-foundation",
                    "prerequisites": [],
                    "required_design_inputs": ["architecture.md"],
                },
                "integration": {
                    "delivery_identity": "delivery-integration",
                    "prerequisites": ["delivery-foundation"],
                    "required_design_inputs": ["interfaces.md"],
                },
            },
        },
    }
    raw = {
        name: yaml.safe_dump(document, sort_keys=False).encode()
        for name, document in documents.items()
    }
    raw.update(
        {
            "project/decision/state/frontier.md": b"# Frontier\n",
            "project/decision/state/ledger.md": b"# Ledger\n",
            "project/decision/state/log.md": b"# Log\n",
            "project/decision/parents/problem.md": b"# Problem\n",
            "project/decision/parents/representation.md": b"# Representation\n",
        }
    )
    return raw


def test_w_backed_entry_projects_unordered_dependency_complete_delivery_scope() -> None:
    projection = validate_and_project(
        "entry",
        _w_backed_entry_subject(["delivery-integration", "delivery-foundation"]),
        review_stage="authorization-readiness",
    )

    assert projection["delivery_scope"] == {
        "design_contract_identity": "W900-design-sha256:" + "d" * 64,
        "deliveries": ["delivery-foundation", "delivery-integration"],
    }


def test_w_backed_entry_rejects_scope_without_delivery_prerequisite() -> None:
    with pytest.raises(ProvenanceError, match="omits prerequisite obligations"):
        validate_and_project(
            "entry",
            _w_backed_entry_subject(["delivery-integration"]),
            review_stage="authorization-readiness",
        )


@pytest.mark.parametrize(
    ("delivery_scope", "message"),
    [
        ([], "missing substantive fields"),
        (
            ["delivery-foundation", "delivery-foundation"],
            "nonempty unique list",
        ),
        (["delivery-unknown"], "unknown obligations"),
    ],
)
def test_w_backed_entry_rejects_invalid_delivery_scope(
    delivery_scope: list[str], message: str
) -> None:
    with pytest.raises(ProvenanceError, match=message):
        validate_and_project(
            "entry",
            _w_backed_entry_subject(delivery_scope),
            review_stage="authorization-readiness",
        )


def test_w_backed_entry_requires_inputs_for_every_scoped_delivery() -> None:
    raw = _w_backed_entry_subject(
        ["delivery-foundation", "delivery-integration"]
    )
    plan = yaml.safe_load(raw["project/decision/entry/plan.yaml"])
    plan["required_design_inputs"] = ["architecture.md"]
    raw["project/decision/entry/plan.yaml"] = yaml.safe_dump(
        plan, sort_keys=False
    ).encode()

    with pytest.raises(ProvenanceError, match="do not cover"):
        validate_and_project(
            "entry", raw, review_stage="authorization-readiness"
        )


def test_w_backed_entry_does_not_revalidate_unselected_delivery_details() -> None:
    raw = _w_backed_entry_subject(["delivery-foundation"])
    traceability = yaml.safe_load(
        raw["project/decision/design/W900/traceability.yaml"]
    )
    traceability["slices"]["integration"].pop("prerequisites")
    traceability["slices"]["integration"].pop("required_design_inputs")
    raw["project/decision/design/W900/traceability.yaml"] = yaml.safe_dump(
        traceability, sort_keys=False
    ).encode()

    projection = validate_and_project(
        "entry", raw, review_stage="authorization-readiness"
    )

    assert projection["delivery_scope"]["deliveries"] == ["delivery-foundation"]


def test_same_batch_accepts_revised_delivery_scope_as_new_entry_realization() -> None:
    first = validate_and_project(
        "entry",
        _w_backed_entry_subject(["delivery-foundation"]),
        review_stage="authorization-readiness",
    )
    revised = validate_and_project(
        "entry",
        _w_backed_entry_subject(["delivery-foundation", "delivery-integration"]),
        review_stage="authorization-readiness",
    )

    assert first["delivery_scope"] != revised["delivery_scope"]


def test_current_review_subject_rejects_historical_contract() -> None:
    subject = {
        "contract_version": "frontier-review-subject/1",
        "role_adapter": "frontier-review-role-adapter/1",
        "review_kind": "entry",
        "subject_mode": "complete",
        "semantic_projection": {"affected_scope": "historical"},
    }

    with pytest.raises(ProvenanceError, match="current consequence"):
        require_current_review_subject(subject, expected_kind="entry")


def test_current_implementation_review_projects_prepublication_state() -> None:
    decision = {
        "contract_version": "frontier-project-implementation-review-input/1",
        "affected_scope": "exact working realization",
        "candidate": {"id": "B900-candidate-sha256:" + "a" * 64},
        "reviewed_design": "W900-design-sha256:" + "b" * 64,
        "publication_state": "prepublication",
        "execution_start": "B900-execution-start-sha256:" + "c" * 64,
        "engineering_state": {"final_attempt": 2, "status": "pass"},
        "allowed_feedback": "fidelity to the unchanged reviewed target",
    }
    projection = validate_and_project(
        "implementation",
        {
            "project/decision/implementation/input.yaml": yaml.safe_dump(
                decision, sort_keys=False
            ).encode()
        },
        closed_collections=[
            {
                "logical_name": "project/decision/candidate-working",
                "members": ["project/decision/implementation/input.yaml"],
            }
        ],
    )

    assert projection["publication_state"] == "prepublication"
    assert projection["engineering_state"]["status"] == "pass"


def test_current_implementation_review_rejects_missing_publication_state() -> None:
    decision = {
        "contract_version": "frontier-project-implementation-review-input/1",
        "affected_scope": "exact realization",
        "candidate": {"id": "B900-candidate-sha256:" + "a" * 64},
        "reviewed_design": "W900-design-sha256:" + "b" * 64,
    }
    with pytest.raises(ProvenanceError, match="missing substantive fields"):
        validate_and_project(
            "implementation",
            {
                "project/decision/implementation/input.yaml": yaml.safe_dump(
                    decision, sort_keys=False
                ).encode()
            },
            closed_collections=[
                {
                    "logical_name": "project/decision/candidate-working",
                    "members": ["project/decision/implementation/input.yaml"],
                }
            ],
        )


def test_retained_unpublished_review_keeps_original_execution_without_final_manifest() -> None:
    decision = {
        "contract_version": "frontier-project-implementation-review-input/1",
        "affected_scope": "publication of a retained complete realization",
        "candidate": {"id": "retained-sha256:" + "a" * 64},
        "reviewed_design": "design-sha256:" + "b" * 64,
        "publication_state": "prepublication",
        "execution_start": "original-generation-execution-sha256:" + "c" * 64,
        "engineering_state": {"final_attempt": 2, "status": "pass"},
        "allowed_feedback": "unchanged target",
    }
    subject = {
        "project/decision/implementation/input.yaml": yaml.safe_dump(decision).encode(),
        "project/decision/parents/problem.md": b"Current parent for proposed publication\n",
    }
    projection = validate_and_project(
        "implementation", subject,
        closed_collections=[{
            "logical_name": "project/decision/candidate-working",
            "members": ["project/decision/implementation/input.yaml"],
        }],
    )
    assert projection["execution_start"] == decision["execution_start"]
    assert projection["publication_state"] == "prepublication"
    assert "candidate_manifest" not in projection


def test_current_implementation_review_rejects_nonpassing_engineering_state() -> None:
    decision = {
        "contract_version": "frontier-project-implementation-review-input/1",
        "affected_scope": "exact working realization",
        "candidate": {"id": "B900-candidate-sha256:" + "a" * 64},
        "reviewed_design": "W900-design-sha256:" + "b" * 64,
        "publication_state": "prepublication",
        "execution_start": "B900-execution-start-sha256:" + "c" * 64,
        "engineering_state": {"final_attempt": 2, "status": "fail"},
        "allowed_feedback": "fidelity to the unchanged reviewed target",
    }
    with pytest.raises(ProvenanceError, match="final all-pass"):
        validate_and_project(
            "implementation",
            {
                "project/decision/implementation/input.yaml": yaml.safe_dump(
                    decision, sort_keys=False
                ).encode()
            },
            closed_collections=[
                {
                    "logical_name": "project/decision/candidate-working",
                    "members": ["project/decision/implementation/input.yaml"],
                }
            ],
        )
