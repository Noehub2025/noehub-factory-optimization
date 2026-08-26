"""Focused checks for reusing one adopted user grant through existing Entry."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
import yaml

from frontier_provenance import NodeRepository, ProvenanceError, attest, bind_authority
from frontier_provenance.review_contract import validate_and_project
from test_frontier_review_preparation import prepare_review, self_identified, write_entry


def reuse_fixture(root: Path, batch: str = "B002") -> tuple[dict, dict[str, bytes]]:
    spec = write_entry(root)
    target = yaml.safe_load((root / "entry/target.yaml").read_bytes())
    for key in ("target_id", "identity_rule", "experiment_path", "experiment_id"):
        target.pop(key)
    target.update(
        continuation="within-scope",
        scope="Research and local analysis toward the agreed objective across batches; no paid, sensitive, external or irreversible actions.",
        maximum_spend={"schedules": 3},
        stop_boundary="Stop at cumulative ceiling or withdrawn permission.",
        authorization_question="Authorize this bounded continuing research?",
    )
    target_raw = self_identified("target_id", "V001-target-sha256:", yaml.safe_dump(target).encode())
    target = yaml.safe_load(target_raw)
    answer = {
        "decision_id": "V001", "target_id": target["target_id"],
        "exact_answer": "Authorize the stated continuing research scope.",
        "answer_classification": "authorize", "conditions": [],
    }
    answer_raw = yaml.safe_dump(answer).encode()
    adoption = {
        "decision_id": "V001", "result": "ENTRY_READY",
        "target": {"identity": target["target_id"], "file_sha256": hashlib.sha256(target_raw).hexdigest()},
        "user_result": {"file_sha256": hashlib.sha256(answer_raw).hexdigest()},
        "authority_id": "frontier-authority-root-sha256:" + "a" * 64,
    }
    original = {"target": target_raw, "answer": answer_raw, "adoption": yaml.safe_dump(adoption).encode()}
    spec["artifacts"] = [item for item in spec["artifacts"] if item["path"] != "entry/target.yaml"]
    (root / "authority").mkdir()
    for role, raw in original.items():
        (root / f"authority/{role}.yaml").write_bytes(raw)
        spec["artifacts"].append({
            "logical_name": f"project/decision/authority/{role}.yaml",
            "path": f"authority/{role}.yaml", "kind": "blob", "behavioral_metadata": {},
        })
    plan = yaml.safe_load((root / "entry/plan.yaml").read_bytes())
    plan.pop("identity_rule")
    plan.pop("batch_plan_id")
    plan.update(batch_id=batch, authorization_gate="existing grant through spend-readiness")
    (root / "entry/plan.yaml").write_bytes(self_identified("batch_plan_id", f"{batch}-plan-sha256:", yaml.safe_dump(plan).encode()))
    (root / "entry/experiment.yaml").write_text(
        f"contract_version: research-assignment/1\nbatch_id: {batch}\nquestion: Which observation separates the live explanations?\n"
    )
    selection = yaml.safe_load((root / "selection.yaml").read_bytes())
    selection.update(
        budget={"ceiling": 3, "actual": 1, "reserved": 0, "protected_reserve": 1},
        selection={"primary": batch, "parallel": None},
        authority={"current": "V001 continuing grant"},
    )
    (root / "selection.yaml").write_text(yaml.safe_dump(selection))
    gate = {
        "contract_version": "frontier-project-spend-gate/1", "batch_id": batch,
        "authority_target": target["target_id"], "affected_scope": "One in-scope research observation.",
        "later_spend_gate": "Existing current authority and cumulative Budget checks.",
        "authorization_basis": {role: f"project/decision/authority/{role}.yaml" for role in original},
    }
    (root / "entry/gate.yaml").write_text(yaml.safe_dump(gate))
    spec["artifacts"].append({
        "logical_name": "project/decision/entry/gate.yaml", "path": "entry/gate.yaml",
        "kind": "blob", "behavioral_metadata": {},
    })
    spec["semantic_projection"]["review_stage"] = "spend-readiness"
    return spec, {item["logical_name"]: (root / item["path"]).read_bytes() for item in spec["artifacts"]}


@pytest.mark.parametrize("batch", ["B001", "B002"])
def test_scope_reuse_keeps_original_decision_and_cumulative_budget(tmp_path: Path, batch: str) -> None:
    _, raw = reuse_fixture(tmp_path, batch)
    projection = validate_and_project("entry", raw, review_stage="spend-readiness")
    assert projection["authorization_basis"]["decision_id"] == "V001"
    assert projection["authorization_basis"]["maximum_spend"] == {"schedules": 3}
    assert projection["budget"] == {"ceiling": 3, "actual": 1, "reserved": 0, "protected_reserve": 1}
    assert projection["selection"]["primary"] == batch


@pytest.mark.parametrize(
    "role,field,value,expected",
    [
        ("target", "continuation", "exact-only", "exact-only"),
        ("target", "continuation", None, "exact-only"),
        ("answer", "target_id", "different", "different target"),
        ("answer", "answer_classification", "decline", "affirmative answer"),
        ("answer", "conditions", ["Ask before each batch"], "unresolved conditions"),
        ("answer", "exact_answer", "", "preserved user answer"),
        ("adoption", "decision_id", "V002", "different user decisions"),
        ("adoption", "result", "AUTHORIZATION_READY", "not adopted"),
    ],
)
def test_reuse_rejects_inapplicable_or_unadopted_answer(tmp_path: Path, role: str, field: str, value, expected: str) -> None:
    _, raw = reuse_fixture(tmp_path)
    name = f"project/decision/authority/{role}.yaml"
    document = yaml.safe_load(raw[name])
    document[field] = value
    raw[name] = yaml.safe_dump(document).encode()
    with pytest.raises(ProvenanceError, match=expected):
        validate_and_project("entry", raw, review_stage="spend-readiness")


def test_reuse_rejects_changed_original_bytes(tmp_path: Path) -> None:
    _, raw = reuse_fixture(tmp_path)
    raw["project/decision/authority/answer.yaml"] += b"# changed after adoption\n"
    with pytest.raises(ProvenanceError, match="original answer bytes"):
        validate_and_project("entry", raw, review_stage="spend-readiness")


def test_reuse_prepares_complete_noncode_entry_and_binds_current_authority(tmp_path: Path) -> None:
    spec, _ = reuse_fixture(tmp_path)
    result = prepare_review(spec, tmp_path, tmp_path / "sealed")
    assert result["status"] == "SEALED", result
    decision = NodeRepository(tmp_path / "sealed/nodes").load(result["decision_root"])
    validation = attest(
        decision, validation_report_root="frontier-content-root-sha256:" + "b" * 64,
        verdict="ready", findings=[],
    )
    authority = bind_authority(
        authority_root="frontier-content-root-sha256:" + "c" * 64,
        decision=decision, validation=validation, decision_bundle=tmp_path / "sealed/snapshot",
    )
    assert {item["node_id"] for item in authority["parents"]} == {decision["node_id"], validation["node_id"]}


@pytest.mark.parametrize(
    "consequence,missing",
    [("execution", "budget_current"), ("execution", "authority_current"), ("external-action", "authority_current")],
)
def test_reused_grant_does_not_bypass_current_consequence_checks(consequence: str, missing: str) -> None:
    from frontier_provenance import verify_for
    from test_frontier_provenance import chain, content_resolver, fact

    receipt = "frontier-content-root-sha256:" + "d" * 64
    _, authority, execution, _, nodes = chain(receipt)
    root = execution if consequence == "external-action" else authority
    facts = {name: fact(receipt) for name in (
        "authority_current", "budget_current", "reservation_current", "inputs_current",
        "resources_available", "action_window_open", "prior_external_effects_known",
    )}
    facts.pop(missing)
    result = verify_for(
        root["node_id"], nodes.__getitem__, content_resolver,
        consequence=consequence, live_facts=facts, checked_at="2026-08-17T01:00:00Z",
    )
    assert result["static_chain_verified"] is True
    assert result["ready"] is False
    assert result["unresolved_live_facts"] == [missing]
