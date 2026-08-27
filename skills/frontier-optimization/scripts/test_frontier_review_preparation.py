#!/usr/bin/env python3
"""Behavioral tests for the single pre-review sealing interface."""

from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

import pytest
import yaml

from frontier_provenance import NodeRepository, ProvenanceError, attest, bind_authority
from frontier_provenance.stores import ArtifactSource, ProjectPortableStore, PortableBundleStore
from frontier_review import PREPARATION_CONTRACT, prepare_review as prepare_saved_review
from frontier_provenance.git_content import GitReferenceStore


def prepare_review(spec: dict, root: Path, output: Path) -> dict:
    """Save fixture drafts normally before exercising review preparation."""
    def git(*args):
        subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)
    git("init", "-q")
    paths = [item["path"] for item in spec["artifacts"] if (root / item["path"]).is_file()]
    if paths:
        git("add", "--", *paths)
    git("-c", "user.name=Review Test", "-c", "user.email=test@example.invalid",
        "commit", "--allow-empty", "-qm", "review fixture checkpoint")
    return prepare_saved_review(spec, root, output)


def self_identified(field: str, prefix: str, body: bytes) -> bytes:
    remaining = (
        f"identity_rule: {prefix.removesuffix(':')} of exact UTF-8 bytes with the complete {field} line omitted\n"
    ).encode() + body
    digest = hashlib.sha256(remaining).hexdigest()
    return f"{field}: {prefix}{digest}\n".encode() + remaining


def write_entry(
    root: Path,
    *,
    bad_identity: bool = False,
    duplicate_x: bool = False,
    duplicate_b_meaning: bool = False,
) -> dict:
    (root / "state").mkdir()
    (root / "parents").mkdir()
    (root / "entry").mkdir()
    ledger = "# Ledger\n\n## X001 First selection\n"
    if duplicate_x:
        ledger += "\n## X001 Conflicting selection\n"
    (root / "state/ledger.md").write_text(ledger)
    if duplicate_b_meaning:
        (root / "state/ledger.md").write_text(
            ledger + "\n## B001: Alpha mechanism\n\n## B001: Beta mechanism\n"
        )
    (root / "state/frontier.md").write_text("# Frontier\n")
    (root / "state/log.md").write_text("# Log\n")
    (root / "parents/problem.md").write_text("# Problem\n")
    (root / "parents/representation.md").write_text("# Representation\n")
    (root / "parents/handoff.yaml").write_text("contract_version: framing-handoff/1\n")
    (root / "selection.yaml").write_text(
        "contract_version: frontier-selection-evidence-state/1\n"
        "event_id: X001\n"
        "budget: {ceiling: 3, actual: 0}\n"
        "route_set: {state: complete}\n"
        "resolver: {first_applicable_row: 12}\n"
        "selection: {primary: B001, parallel: null}\n"
        "authority: {current: planning-only}\n"
    )
    experiment_body = b"contract_version: experiment/1\nbatch_id: B001\n"
    experiment = self_identified(
        "experiment_id", "B001-experiment-sha256:", experiment_body
    )
    if bad_identity:
        experiment = experiment.replace(
            b"B001-experiment-sha256:", b"B001-experiment-sha256:" + b"0" * 64 + b"#",
            1,
        )
    (root / "entry/experiment.yaml").write_bytes(experiment)
    experiment_id = experiment.decode().splitlines()[0].split(": ", 1)[1]
    plan_body = (
        "contract_version: frontier-project-batch-plan/3\n"
        "batch_id: B001\n"
        "maximum_spend: {schedules: 1}\n"
        "authorization_gate: exact reviewed authorization\n"
        "stop_conditions: [one result]\n"
    ).encode()
    (root / "entry/plan.yaml").write_bytes(
        self_identified("batch_plan_id", "B001-plan-sha256:", plan_body)
    )
    target_body = (
        "contract_version: frontier-project-authorization-target/1\n"
        "decision_id: V001\n"
        "batch_id: B001\n"
        f"experiment_path: entry/experiment.yaml\n"
        f"experiment_id: {json.loads(json.dumps(experiment_id))}\n"
        "scope: one bounded experiment\n"
        "maximum_spend: {schedules: 1}\n"
        "stop_boundary: stop after one result\n"
        "authorization_question: Authorize the exact experiment?\n"
        "authorize_consequence: permit one later acknowledged schedule\n"
    ).encode()
    (root / "entry/target.yaml").write_bytes(
        self_identified("target_id", "V001-target-sha256:", target_body)
    )
    artifacts = []
    for logical, path in (
        ("project/decision/state/ledger.md", "state/ledger.md"),
        ("project/decision/state/frontier.md", "state/frontier.md"),
        ("project/decision/state/log.md", "state/log.md"),
        ("project/decision/parents/problem.md", "parents/problem.md"),
        ("project/decision/parents/representation.md", "parents/representation.md"),
        ("project/decision/parents/handoff.yaml", "parents/handoff.yaml"),
        ("project/decision/selection/evidence-state.yaml", "selection.yaml"),
        ("project/decision/entry/experiment.yaml", "entry/experiment.yaml"),
        ("project/decision/entry/plan.yaml", "entry/plan.yaml"),
        ("project/decision/entry/target.yaml", "entry/target.yaml"),
    ):
        artifacts.append(
            {
                "logical_name": logical,
                "path": path,
                "kind": "blob",
                "behavioral_metadata": {},
            }
        )
    return {
        "contract_version": PREPARATION_CONTRACT,
        "review_kind": "entry",
        "artifacts": artifacts,
        "closed_collections": [],
        "semantic_projection": {"review_stage": "authorization-readiness"},
    }


def write_w_backed_entry(
    root: Path,
    *,
    traceability_raw: bytes | None = None,
    design_identity: str | None = None,
    digest_prefix: str = "",
) -> tuple[dict, Path]:
    spec = write_entry(root)
    design_identity = design_identity or "W005-r4-sha256:" + "d" * 64
    traceability_raw = traceability_raw or (
        b"work_id: W005\n"
        + f"design_contract_identity: {design_identity}\n".encode()
        + b"identity_rule: SHA-256 of these UTF-8 bytes with the design_contract_identity line omitted\n"
        + b"slices:\n"
        + b"  scheduler-core:\n"
        + b"    delivery_identity: delivery-root\n"
        + b"    prerequisites: []\n"
        + b"    required_design_inputs: [architecture.md]\n"
    )
    (root / "design").mkdir()
    traceability_path = root / "design/traceability-object"
    traceability_path.write_bytes(traceability_raw)
    digest = hashlib.sha256(traceability_raw).hexdigest()

    plan_path = root / "entry/plan.yaml"
    plan = yaml.safe_load(plan_path.read_text())
    plan.pop("batch_plan_id")
    plan.pop("identity_rule")
    plan.update(
        {
            "design_profile": "module",
            "work_plan": "work/W005/WORK.md",
            "work_plan_revision": 4,
            "design_contract_identity": design_identity,
            "design_traceability": {
                "path": "design/traceability-object",
                "sha256": digest_prefix + digest,
            },
            "required_design_inputs": ["architecture.md"],
            "delivery_scope": ["delivery-root"],
        }
    )
    plan_path.write_bytes(
        self_identified(
            "batch_plan_id",
            "B001-plan-sha256:",
            yaml.safe_dump(plan, sort_keys=False).encode(),
        )
    )
    spec["artifacts"].append(
        {
            "logical_name": "project/decision/design/W005/traceability.yaml",
            "path": "design/traceability-object",
            "kind": "blob",
            "behavioral_metadata": {},
        }
    )
    return spec, traceability_path


def add_current_engineering_plan(root: Path, spec: dict) -> Path:
    """Attach the current external engineering plan to an Entry fixture."""

    check_path = root / "entry/engineering-checks.yaml"
    check_document = {
        "contract_version": "frontier-project-engineering-check-plan/1",
        "batch_id": "B001",
        "consequence": "engineering evidence only",
        "limits": {
            "cumulative_local_wall_seconds": 60,
            "per_command_timeout_seconds": 30,
            "processes": 1,
            "new_output_bytes": 4096,
            "proposal_attempts": 1,
            "development_schedules": 0,
            "evaluator_runs": 0,
            "games": 0,
            "sealed_inputs": 0,
            "paid_actions": 0,
        },
        "formal_units": [
            {"id": "focused-check", "argv": ["tool", "check"]},
        ],
    }
    check_path.write_text(yaml.safe_dump(check_document, sort_keys=False))
    check_digest = hashlib.sha256(check_path.read_bytes()).hexdigest()

    plan_path = root / "entry/plan.yaml"
    plan = yaml.safe_load(plan_path.read_text())
    plan.pop("batch_plan_id")
    plan.pop("identity_rule")
    plan["engineering_check_plan"] = "entry/engineering-checks.yaml"
    plan["execution_frozen_inputs"] = [
        {
            "path": "entry/engineering-checks.yaml",
            "scope": "file",
            "identity": "sha256:" + check_digest,
        }
    ]
    plan_path.write_bytes(
        self_identified(
            "batch_plan_id",
            "B001-plan-sha256:",
            yaml.safe_dump(plan, sort_keys=False).encode(),
        )
    )
    spec["artifacts"].append(
        {
            "logical_name": "project/decision/entry/engineering-checks.yaml",
            "path": "entry/engineering-checks.yaml",
            "kind": "blob",
            "behavioral_metadata": {},
        }
    )
    return check_path


def rewrite_entry_plan(root: Path, mutate) -> None:
    plan_path = root / "entry/plan.yaml"
    plan = yaml.safe_load(plan_path.read_text())
    plan.pop("batch_plan_id")
    plan.pop("identity_rule")
    mutate(plan)
    plan_path.write_bytes(
        self_identified(
            "batch_plan_id",
            "B001-plan-sha256:",
            yaml.safe_dump(plan, sort_keys=False).encode(),
        )
    )


def add_routine_follow_up(root: Path, spec: dict) -> None:
    protocol_id = "protocol-sha256:" + "1" * 64
    calibration_id = "calibration-sha256:" + "2" * 64
    invalidation_key = "pending"
    template = {
        "contract_version": "frontier-routine-experiment-template/1",
        "experiment": {
            "contract_version": "frontier-routine-experiment/1",
            "candidate": {
                "id": "$late.candidate.id",
                "manifest_sha256": "$late.candidate.manifest_sha256",
                "collection_root": "$late.candidate.collection_root",
            },
            "scientific_question": "Does the exact candidate change the predeclared local metric?",
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
            "mode": "routine-local",
            "result_contract_version": "frontier-batch-result/2",
            "consequence_limit": "B evidence only",
            "sample_ceiling": {"runs": 16},
            "resource_ceiling": {"local_minutes": 5},
            "candidate": {
                "id": "$late.candidate.id",
                "root_path": "candidates/B001",
                "manifest_path": "project/state/candidate-manifest.yaml",
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
                "invalidation_key": "$entry.protocol_invalidation_key",
            },
            "calibration": {
                "contract_version": "frontier-protocol-calibration-result/1",
                "content_root": "$entry.calibration_content_root",
                "calibration_id": calibration_id,
                "protocol_invalidation_key": "$entry.protocol_invalidation_key",
            },
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
    plan = {
        "contract_version": "frontier-project-batch-plan/3",
        "batch_id": "B001",
        "maximum_spend": {"schedules": 2},
        "authorization_gate": "exact reviewed composite authorization",
        "stop_conditions": ["one materialization and at most one routine follow-up"],
        "routine_follow_up": {
            "contract_version": "frontier-routine-follow-up/1",
            "slot_id": "slot-B001-screen",
            "materialization_batch_id": "B001",
            "follow_up_batch_id": "B002",
            "route_id": "route-1",
            "protocol_id": protocol_id,
            "calibration_id": calibration_id,
            "scientific_question": "Does the exact candidate change the predeclared local metric?",
            "sample_ceiling": {"runs": 16},
            "resource_ceiling": {"local_minutes": 5},
            "result_contract_version": "frontier-batch-result/2",
            "action_window": "before the Entry expiry",
            "budget_boundary": {"maximum_spend": 1},
            "protected_reserve": "prohibited",
            "late_bindings": [
                "candidate.id",
                "candidate.manifest_sha256",
                "candidate.collection_root",
            ],
            "experiment_template": template,
            "prohibited_consequences": template["evaluation_target"][
                "prohibited_consequences"
            ],
        },
    }
    plan_body = yaml.safe_dump(plan, sort_keys=False).encode()
    (root / "entry/plan.yaml").write_bytes(
        self_identified("batch_plan_id", "B001-plan-sha256:", plan_body)
    )
    protocol = {
        "contract_version": "frontier-evaluation-protocol/1",
        "protocol_id": protocol_id,
        "evaluator": "exact local evaluator version",
        "harness": "exact harness version",
        "schema": "exact input and output schema",
        "scoring": "exact score rule",
        "environment": "exact local environment",
        "evaluation_scope": "development only",
        "comparison_distribution": "predeclared comparator and scenario distribution",
        "sampling": "fixed seeds and balanced seats",
        "metrics": ["primary metric"],
        "uncertainty": "predeclared interval",
        "exposure": "development",
        "calibration_requirements": ["self-check once per protocol version"],
        "invalidation_key": invalidation_key,
    }
    invalidation_body = {
        key: value
        for key, value in protocol.items()
        if key not in {"protocol_id", "invalidation_key", "identity_rule"}
    }
    invalidation_key = "sha256:" + hashlib.sha256(
        json.dumps(
            invalidation_body,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode()
    ).hexdigest()
    protocol["invalidation_key"] = invalidation_key
    calibration = {
        "contract_version": "frontier-protocol-calibration-result/1",
        "calibration_id": calibration_id,
        "protocol_id": protocol_id,
        "protocol_invalidation_key": invalidation_key,
        "environment": "exact local environment",
        "controls": ["incumbent self-comparison"],
        "evidence_manifest": ["calibration-output.json"],
        "results": ["measurement path valid"],
        "drift_status": "current",
    }
    (root / "entry/protocol.yaml").write_text(yaml.safe_dump(protocol, sort_keys=False))
    (root / "entry/calibration.yaml").write_text(
        yaml.safe_dump(calibration, sort_keys=False)
    )
    for name in ("protocol", "calibration"):
        spec["artifacts"].append(
            {
                "logical_name": f"project/decision/entry/{name}.yaml",
                "path": f"entry/{name}.yaml",
                "kind": "blob",
                "behavioral_metadata": {},
            }
        )


def test_bad_self_identity_returns_not_ready_without_formal_artifacts() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        spec = write_entry(root, bad_identity=True)
        output = root / "sealed"
        result = prepare_review(spec, root, output)
        assert result["status"] == "NOT_READY"
        assert result["findings"][0]["code"] == "DRAFT_INVALID"
        assert not output.exists()


def test_entry_seals_one_frozen_current_engineering_plan() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        spec = write_entry(root)
        add_current_engineering_plan(root, spec)
        result = prepare_review(spec, root, root / "sealed")
        assert result["status"] == "SEALED", result.get("findings")


def test_entry_rejects_current_engineering_plan_digest_drift() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        spec = write_entry(root)
        check_path = add_current_engineering_plan(root, spec)
        check_path.write_text(check_path.read_text() + "notes: changed after binding\n")
        result = prepare_review(spec, root, root / "sealed")
        assert result["status"] == "NOT_READY"
        assert "frozen input binding" in result["findings"][0]["message"]


def test_duplicate_record_identifier_returns_not_ready_without_review_id() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        spec = write_entry(root, duplicate_x=True)
        result = prepare_review(spec, root, root / "sealed")
        assert result["status"] == "NOT_READY"
        assert "review_id" not in result
        assert not (root / "sealed").exists()


def test_conflicting_duplicate_batch_meaning_is_rejected() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        result = prepare_review(
            write_entry(root, duplicate_b_meaning=True), root, root / "sealed"
        )
        assert result["status"] == "NOT_READY"
        assert "conflicting repeated meanings" in result["findings"][0]["message"]
        assert not (root / "sealed").exists()


def test_entry_overlay_cannot_impersonate_a_complete_subject() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        spec = write_entry(root)
        repair = root / "entry/repair.yaml"
        repair.write_text("replacement_order: [base, repair]\n")
        spec["artifacts"] = [
            item
            for item in spec["artifacts"]
            if item["logical_name"]
            in {
                "project/decision/state/ledger.md",
                "project/decision/parents/problem.md",
                "project/decision/selection/evidence-state.yaml",
            }
        ]
        spec["artifacts"].append(
            {
                "logical_name": "project/decision/entry/repair.yaml",
                "path": "entry/repair.yaml",
                "kind": "blob",
                "behavioral_metadata": {},
            }
        )
        result = prepare_review(spec, root, root / "sealed")
        assert result["status"] == "NOT_READY"
        assert not (root / "sealed").exists()


def test_entry_cannot_omit_a_bound_work_object() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        spec = write_entry(root)
        spec["artifacts"] = [
            item
            for item in spec["artifacts"]
            if item["logical_name"] != "project/decision/entry/experiment.yaml"
        ]
        result = prepare_review(spec, root, root / "sealed")
        assert result["status"] == "NOT_READY"
        assert not (root / "sealed").exists()


def test_caller_cannot_supply_unreconciled_semantic_projection() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        spec = write_entry(root)
        spec["semantic_projection"]["budget"] = "same"
        result = prepare_review(spec, root, root / "sealed")
        assert result["status"] == "NOT_READY"
        assert "derived from canonical project objects" in result["findings"][0]["message"]


def test_design_composite_outer_identity_rule_is_supported() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        (root / "parents").mkdir()
        (root / "design").mkdir()
        (root / "parents/problem.md").write_text("# Problem\n")
        rule = (
            "SHA-256 of these UTF-8 bytes with the design_contract_id line omitted; "
            "concern hashes omit their design_contract_identity line; traceability hash "
            "omits its design_contract_identity line; work section hashes cover bytes from "
            "each named level-2 heading through the byte before the next level-2 heading"
        )
        source_body = b"identity_rule: SHA-256 of these UTF-8 bytes with the source_base_id line omitted\nsource: exact\n"
        source_id = "source-base-W005-r1-sha256:" + hashlib.sha256(source_body).hexdigest()
        (root / "design/source-base.yaml").write_bytes(
            f"source_base_id: {source_id}\n".encode() + source_body
        )
        concern_without_binding = b"---\nwork_id: W005\n---\n\n# Architecture\n"
        concern_digest = hashlib.sha256(concern_without_binding).hexdigest()
        verification_without_binding = (
            b"---\nwork_id: W005\n---\n\n# Verification\n\n## Scheduler core\n"
        )
        verification_digest = hashlib.sha256(verification_without_binding).hexdigest()
        trace_without_binding = (
            b"work_id: W005\n"
            + b"identity_rule: SHA-256 of these UTF-8 bytes with the design_contract_identity line omitted\n"
            + b"slices:\n"
            + b"  scheduler-core:\n"
            + f"    verification_pointer: design/verification.md#scheduler-core@sha256:{verification_digest}\n".encode()
            + b"    delivery_identity: delivery-root\n"
            + b"    prerequisites: []\n"
            + b"    required_design_inputs: [architecture.md]\n"
        )
        trace_digest = hashlib.sha256(trace_without_binding).hexdigest()
        remaining = (
            f"identity_rule: {rule}\n"
            "work_id: W005\n"
            "problem_epoch: 5\n"
            "representation_revision: 1\n"
            "route: T009\n"
            "delivery: {scheduler-core: delivery-root}\n"
            f"concerns_normalized: {{architecture.md: {concern_digest}, verification.md: {verification_digest}}}\n"
            "supporting_inputs:\n"
            f"  source-base.yaml: {source_id}\n"
            f"  traceability.yaml.normalized: {trace_digest}\n"
        ).encode()
        digest = hashlib.sha256(remaining).hexdigest()
        design_id = f"W005-r4-sha256:{digest}"
        (root / "design/index.yaml").write_bytes(
            f"design_contract_id: {design_id}\n".encode() + remaining
        )
        (root / "design/architecture.md").write_bytes(
            b"---\nwork_id: W005\n"
            + f"design_contract_identity: {design_id}\n".encode()
            + b"---\n\n# Architecture\n"
        )
        (root / "design/verification.md").write_bytes(
            b"---\nwork_id: W005\n"
            + f"design_contract_identity: {design_id}\n".encode()
            + b"---\n\n# Verification\n\n## Scheduler core\n"
        )
        (root / "design/traceability.yaml").write_bytes(
            b"work_id: W005\n"
            + f"design_contract_identity: {design_id}\n".encode()
            + b"identity_rule: SHA-256 of these UTF-8 bytes with the design_contract_identity line omitted\n"
            + b"slices:\n"
            + b"  scheduler-core:\n"
            + f"    verification_pointer: design/verification.md#scheduler-core@sha256:{verification_digest}\n".encode()
            + b"    delivery_identity: delivery-root\n"
            + b"    prerequisites: []\n"
            + b"    required_design_inputs: [architecture.md]\n"
        )
        spec = {
            "contract_version": PREPARATION_CONTRACT,
            "review_kind": "design",
            "artifacts": [
                {
                    "logical_name": "project/decision/parents/problem.md",
                    "path": "parents/problem.md",
                    "kind": "blob",
                    "behavioral_metadata": {},
                },
                {
                    "logical_name": "project/decision/design/W005/index.yaml",
                    "path": "design/index.yaml",
                    "kind": "blob",
                    "behavioral_metadata": {},
                },
                *[
                    {
                        "logical_name": f"project/decision/design/W005/{name}",
                        "path": f"design/{name}",
                        "kind": "blob",
                        "behavioral_metadata": {},
                    }
                    for name in (
                        "architecture.md",
                        "source-base.yaml",
                        "traceability.yaml",
                        "verification.md",
                    )
                ],
            ],
            "closed_collections": [
                {
                    "logical_name": "project/decision/design/W005",
                    "directory": "design",
                    "members": [
                        "project/decision/design/W005/architecture.md",
                        "project/decision/design/W005/index.yaml",
                        "project/decision/design/W005/source-base.yaml",
                        "project/decision/design/W005/traceability.yaml",
                        "project/decision/design/W005/verification.md",
                    ],
                }
            ],
            "semantic_projection": {},
        }
        result = prepare_review(spec, root, root / "sealed")
        assert result["status"] == "SEALED"

        entry_root = root / "entry-case"
        entry_root.mkdir()
        entry_spec, _ = write_w_backed_entry(
            entry_root,
            traceability_raw=(root / "design/traceability.yaml").read_bytes(),
            design_identity=design_id,
        )
        entry_result = prepare_review(entry_spec, entry_root, entry_root / "sealed")
        assert entry_result["status"] == "SEALED", entry_result


@pytest.mark.parametrize("digest_prefix", ["", "sha256:"])
def test_w_backed_entry_binds_extensionless_traceability_source(
    digest_prefix: str,
) -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        spec, _ = write_w_backed_entry(root, digest_prefix=digest_prefix)

        result = prepare_review(spec, root, root / "sealed")

        assert result["status"] == "SEALED", result


@pytest.mark.parametrize(
    ("case", "message"),
    [
        ("changed-sha", "whole-file SHA-256 does not match"),
        ("changed-bytes", "whole-file SHA-256 does not match"),
        ("missing-path", "path must be nonempty text"),
        ("outside-root", "path is outside project_root"),
        ("uncaptured-path", "path is absent from the review subject"),
        ("noncanonical-path", "does not carry the canonical traceability role"),
        ("invalid-sha", "sha256 is invalid"),
    ],
)
def test_w_backed_entry_rejects_invalid_traceability_binding(
    case: str, message: str
) -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        spec, traceability_path = write_w_backed_entry(root)

        if case == "changed-bytes":
            traceability_path.write_bytes(
                traceability_path.read_bytes() + b"# changed after binding\n"
            )
        elif case == "noncanonical-path":
            alternate = root / "design/traceability-review-object"
            alternate.write_bytes(traceability_path.read_bytes())
            spec["artifacts"].append(
                {
                    "logical_name": "project/decision/design/review/R005-traceability-object",
                    "path": "design/traceability-review-object",
                    "kind": "blob",
                    "behavioral_metadata": {},
                }
            )
            rewrite_entry_plan(
                root,
                lambda plan: plan["design_traceability"].update(
                    {"path": "design/traceability-review-object"}
                ),
            )
        else:

            def mutate(plan: dict) -> None:
                binding = plan["design_traceability"]
                if case == "changed-sha":
                    binding["sha256"] = "f" * 64
                elif case == "missing-path":
                    binding.pop("path")
                elif case == "outside-root":
                    binding["path"] = "../traceability-object"
                elif case == "uncaptured-path":
                    uncaptured = root / "design/uncaptured-traceability-object"
                    uncaptured.write_bytes(traceability_path.read_bytes())
                    binding["path"] = "design/uncaptured-traceability-object"
                elif case == "invalid-sha":
                    binding["sha256"] = "sha256:not-a-digest"

            rewrite_entry_plan(root, mutate)

        result = prepare_review(spec, root, root / "sealed")

        assert result["status"] == "NOT_READY"
        assert result["findings"][0]["code"] == "DRAFT_INVALID"
        assert message in result["findings"][0]["message"]
        assert not (root / "sealed").exists()


def test_valid_entry_seals_one_complete_root_and_one_decision() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        result = prepare_review(write_entry(root), root, root / "sealed")
        assert result["status"] == "SEALED"
        verified = ProjectPortableStore().verify(
            root / "sealed/snapshot", expected_role="decision"
        )
        assert verified["content_root"] == result["content_root"]
        assert verified["review_subject"]["subject_mode"] == "complete"
        assert verified["review_subject"]["review_kind"] == "entry"
        nodes = list((root / "sealed/nodes/decision").glob("*.json"))
        assert len(nodes) == 1
        assert json.loads(nodes[0].read_text())["node_id"] == result["decision_root"]


def test_composite_entry_freezes_one_reusable_protocol_and_one_routine_slot() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        spec = write_entry(root)
        add_routine_follow_up(root, spec)
        result = prepare_review(spec, root, root / "sealed")
        assert result["status"] == "SEALED", result
        verified = ProjectPortableStore().verify(
            root / "sealed/snapshot", expected_role="decision"
        )
        subject = verified["review_subject"]
        assert subject["contract_version"] == "frontier-review-subject/2"
        routine = subject["semantic_projection"]["routine_follow_up"]
        assert routine["slot_id"] == "slot-B001-screen"
        assert routine["protocol_invalidation_key"].startswith("sha256:")
        assert routine["sample_ceiling"] == {"runs": 16}


def test_composite_entry_rejects_stale_protocol_calibration() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        spec = write_entry(root)
        add_routine_follow_up(root, spec)
        calibration_path = root / "entry/calibration.yaml"
        calibration = yaml.safe_load(calibration_path.read_text())
        calibration["protocol_invalidation_key"] = "protocol-key-sha256:" + "9" * 64
        calibration_path.write_text(yaml.safe_dump(calibration, sort_keys=False))
        result = prepare_review(spec, root, root / "sealed")
        assert result["status"] == "NOT_READY"
        assert "invalidated by protocol drift" in result["findings"][0]["message"]


def test_composite_entry_rejects_nonpositive_routine_resource_ceiling() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        spec = write_entry(root)
        add_routine_follow_up(root, spec)
        plan_path = root / "entry/plan.yaml"
        plan = yaml.safe_load(plan_path.read_text())
        routine = plan["routine_follow_up"]
        invalid = {"local_minutes": -1}
        routine["resource_ceiling"] = invalid
        routine["experiment_template"]["experiment"]["resource_ceiling"] = invalid
        routine["experiment_template"]["runtime_inputs"]["resource_ceiling"] = invalid
        routine["experiment_template"]["evaluation_target"]["resource_ceiling"] = invalid
        plan.pop("batch_plan_id")
        plan.pop("identity_rule")
        plan_path.write_bytes(
            self_identified(
                "batch_plan_id",
                "B001-plan-sha256:",
                yaml.safe_dump(plan, sort_keys=False).encode(),
            )
        )
        result = prepare_review(spec, root, root / "sealed")
        assert result["status"] == "NOT_READY"
        assert "finite positive numeric limits" in result["findings"][0]["message"]


def test_composite_entry_requires_protocol_key_change_after_evaluator_change() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        spec = write_entry(root)
        add_routine_follow_up(root, spec)
        protocol_path = root / "entry/protocol.yaml"
        protocol = yaml.safe_load(protocol_path.read_text())
        protocol["evaluator"] = "different evaluator behavior"
        protocol_path.write_text(yaml.safe_dump(protocol, sort_keys=False))
        result = prepare_review(spec, root, root / "sealed")
        assert result["status"] == "NOT_READY"
        assert "invalidation key does not derive" in result["findings"][0]["message"]


def test_complete_review_subject_can_bind_new_authority() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        result = prepare_review(write_entry(root), root, root / "sealed")
        repository = NodeRepository(root / "sealed/nodes")
        decision = repository.load(result["decision_root"])
        validation = attest(
            decision,
            validation_report_root="frontier-content-root-sha256:" + "2" * 64,
            verdict="ready",
            findings=[],
        )
        authority = bind_authority(
            authority_root="frontier-content-root-sha256:" + "3" * 64,
            decision=decision,
            validation=validation,
            decision_bundle=root / "sealed/snapshot",
        )
        assert authority["role"] == "authority"


def test_supplement_only_decision_cannot_bind_new_authority() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        source = root / "repair.yaml"
        source.write_text("replacement: X001 to X002\n")
        manifest = PortableBundleStore()._capture_domain(
            [ArtifactSource("project/decision/repair/change.yaml", source)],
            root / "supplement",
            domain="project-decision",
            project_root=root,
        )
        decision = {
            "node_id": "frontier-decision-root-sha256:" + "1" * 64,
            "artifact_roots": [manifest["content_root"]],
        }
        validation = {
            "node_id": "frontier-attestation-root-sha256:" + "2" * 64,
            "payload": {"verdict": "ready", "subject_root": decision["node_id"], "findings": []},
        }
        with pytest.raises(ProvenanceError, match="complete subject"):
            bind_authority(
                authority_root="frontier-content-root-sha256:" + "3" * 64,
                decision=decision,
                validation=validation,
                decision_bundle=root / "supplement",
            )


def test_workflow_bytes_do_not_change_project_review_identity() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        spec = write_entry(root)
        first = prepare_review(spec, root, root / "first")
        workflow = root / ".agents/skills/frontier/SKILL.md"
        workflow.parent.mkdir(parents=True)
        workflow.write_text("version one\n")
        second = prepare_review(spec, root, root / "second")
        workflow.write_text("version two\n")
        third = prepare_review(spec, root, root / "third")
        assert first["content_root"] == second["content_root"] == third["content_root"]
        assert first["decision_root"] == second["decision_root"] == third["decision_root"]


def test_later_working_changes_do_not_change_the_sealed_git_version(monkeypatch: pytest.MonkeyPatch) -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        spec = write_entry(root)
        original = GitReferenceStore.capture

        def capture_then_drift(store, *args, **kwargs):
            manifest = original(store, *args, **kwargs)
            (root / "selection.yaml").write_text("event_id: X002\n")
            return manifest

        monkeypatch.setattr(GitReferenceStore, "capture", capture_then_drift)
        result = prepare_review(spec, root, root / "sealed")
        assert result["status"] == "SEALED", result
        raw = PortableBundleStore().read_artifacts(root / "sealed/snapshot")
        assert b"X001" in raw["project/decision/selection/evidence-state.yaml"]
        assert (root / "selection.yaml").read_text() == "event_id: X002\n"
