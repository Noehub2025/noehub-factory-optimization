"""Exercise actual owner/Batch boundaries with a deterministic local adapter.

These tests cannot establish model exposure or professional reasoning quality.
"""
from dataclasses import replace
import json
import subprocess

import pytest

from frontier_batch import (Batch, DefineBatch, Action, OperationBinding, OperationResult,
                            ChangeRejected, ConsequenceBlocked, UpdateWorkingState)
from professional_input import OwnerReply, resource_view


@pytest.fixture
def work(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / "owner.md").write_text("Choose a useful allocation for the terminal outcome.")
    (tmp_path / "AGENTS.md").write_text("Maintained [capabilities](knowledge.md).")
    (tmp_path / "knowledge.md").write_text("# Shared capacity\n[Coordinated allocation](method.md)\n")
    (tmp_path / "method.md").write_text("# Method\nCompare whole allocations under shared capacity.\n")
    (tmp_path / "conditions.json").write_text(json.dumps({"scale": 4, "progress": 0}))
    batch = Batch.open(tmp_path, "B001")
    batch.apply(DefineBatch(objective="Maximize terminal return", acceptance="A useful bounded observation",
                            scope=("local",)))
    spec = {"owner": "owner.md", "intended_decision": "Choose the first allocation observation",
            "consumer": "allocation", "operations": ["observe", "observe_alias"],
            "sources": [{"path": "conditions.json", "field": "scale"}],
            "conditions": {"capacity": 4}}
    return tmp_path, batch, spec


class LocalOwner:
    name = "deterministic-local-test-only"

    def reply(self, root, prompt):
        assert "Shared capacity" in prompt
        return OwnerReply({"choices": {"weight": 0}, "rationale": "Use the existing supported fixed control.",
                           "observation": "Compare terminal allocations.", "grounds": [{"path": "method.md"}]},
                          "local-response-1", {"coverage": "local fixture, not a model"})


def adopt(batch, spec):
    prepared = batch.prepare_realization(spec)
    response = batch.answer_realization(prepared, LocalOwner())
    batch.adopt_realization(response["invocation_id"])
    return response


def test_resources_are_not_limited_to_assignment_citations(work):
    root, batch, spec = work
    view = batch.prepare_realization(spec)
    assert any(e["path"] == "knowledge.md" for e in view["resources"]["entries"])
    assert view["coverage"] == "prepared_only"


def test_preparation_same_call_and_copied_hash_cannot_adopt(work):
    root, batch, spec = work
    prepared = batch.prepare_realization(spec)
    with pytest.raises(ChangeRejected, match="prepared content is not delivery"):
        batch.adopt_realization(prepared["delivery_identity"])
    assert batch.view._record["current"]["realization"]["choice"] is None


def test_adoption_inside_adapter_before_response_is_rejected(work):
    root, batch, spec = work
    prepared = batch.prepare_realization(spec)

    class Interleaving(LocalOwner):
        def reply(self, root, prompt):
            pending = Batch.open(root, "B001").view._record["current"]["realization"]["invocation"]
            with pytest.raises(ChangeRejected):
                batch.adopt_realization(pending["id"])
            return super().reply(root, prompt)

    response = batch.answer_realization(prepared, Interleaving())
    batch.adopt_realization(response["invocation_id"])


def test_completed_response_recovery_reuse_and_progress(work):
    root, batch, spec = work
    response = adopt(batch, spec)
    current = Batch.open(root, "B001")
    (root / "conditions.json").write_text(json.dumps({"scale": 4, "progress": 30}))
    current.apply(UpdateWorkingState("progress", resource_limits={"seconds": 10}))
    current.adopt_realization(response["invocation_id"])
    again = current.prepare_realization()
    assert again["input_identity"] == batch.view._record["current"]["realization"]["choice_input"]["input_identity"]


def test_changed_condition_with_same_consumer_rejects_old_answer(work):
    root, batch, spec = work
    response = adopt(batch, spec)
    (root / "conditions.json").write_text(json.dumps({"scale": 9, "progress": 0}))
    with pytest.raises(ValueError, match="conditions changed"):
        Batch.open(root, "B001").adopt_realization(response["invocation_id"])


def test_superseded_owner_response_is_not_adopted(work):
    root, batch, spec = work
    prepared = batch.prepare_realization(spec)

    class Corrected(LocalOwner):
        def reply(self, root, prompt):
            batch.prepare_realization({**spec, "conditions": {"capacity": 9}})
            return super().reply(root, prompt)

    with pytest.raises(ChangeRejected, match="superseded"):
        batch.answer_realization(prepared, Corrected())
    assert batch.view._record["current"]["realization"]["choice"] is None


def test_reopen_old_binding_and_relabel_do_not_remove_enrollment(work):
    root, batch, spec = work
    adopt(batch, spec)
    called = []
    for name in spec["operations"]:
        legacy = Batch.open(root, "B001", operations={name: OperationBinding(lambda a, c: called.append(a))})
        with pytest.raises(ConsequenceBlocked, match="preparation and consumption"):
            legacy.perform(Action("test", name, "preparation"))
    assert not called
    with pytest.raises(ChangeRejected, match="remove durable"):
        batch.prepare_realization({**spec, "operations": ["observe"]})


def test_checked_object_is_the_consumed_object_and_override_is_blocked(work):
    root, batch, spec = work
    adopt(batch, spec)
    effective = {"weight": 0, "adaptive_state": [1, 2]}
    seen = []

    def consume(action, context, supplied):
        assert supplied is effective
        seen.append(supplied["weight"])
        return OperationResult("completed", result={"weight": supplied["weight"]})

    binding = OperationBinding(lambda a, c: pytest.fail("legacy callback must not run"),
                               prepare=lambda a, c: effective, consume=consume)
    runner = Batch.open(root, "B001", operations={"observe": binding})
    runner.perform(Action("first", "observe", "preparation"))
    effective["weight"] = 1
    with pytest.raises(ConsequenceBlocked, match="differs"):
        runner.perform(Action("second", "observe", "preparation"))
    assert seen == [0]


def test_method_change_is_not_hidden_by_unchanged_consumer(work):
    root, batch, spec = work
    adopt(batch, spec)
    (root / "method.md").write_text("The formerly retained method no longer applies.")
    runner = Batch.open(root, "B001", operations={"observe": OperationBinding(lambda a, c: None,
        prepare=lambda a, c: {"weight": 0}, consume=lambda a, c, e: pytest.fail("must not run"))})
    with pytest.raises(ConsequenceBlocked, match="grounds changed"):
        runner.perform(Action("test", "observe", "preparation"))


def test_unrelated_legacy_operation_remains_available(work):
    root, batch, spec = work
    batch.prepare_realization(spec)
    runner = Batch.open(root, "B001", operations={"inspect": OperationBinding(
        lambda a, c: OperationResult("completed", result={"ok": True}))})
    runner.perform(Action("inspect", "inspect", "preparation"))


def test_retired_response_cannot_restore_eligibility(work):
    root, batch, spec = work
    response = adopt(batch, spec)
    batch.retire_realization_response(response["invocation_id"], "The current owner withdrew this choice.")
    with pytest.raises(ChangeRejected):
        batch.adopt_realization(response["invocation_id"])
    runner = Batch.open(root, "B001", operations={"observe": OperationBinding(lambda a, c: None)})
    with pytest.raises(ConsequenceBlocked, match="adopted realization"):
        runner.perform(Action("stale", "observe", "preparation"))


def test_pending_response_recovery_does_not_replay_adapter(work):
    root, batch, spec = work
    prepared = batch.prepare_realization(spec)

    class Lost(LocalOwner):
        def reply(self, root, prompt):
            # Simulate controller loss rather than a settled transport failure.
            raise KeyboardInterrupt()

    with pytest.raises(KeyboardInterrupt):
        batch.answer_realization(prepared, Lost())
    recovered = Batch.open(root, "B001")
    with pytest.raises(ChangeRejected, match="pending"):
        recovered.answer_realization(prepared, LocalOwner())
    pending = recovered.view._record["current"]["realization"]["invocation"]
    with pytest.raises(ChangeRejected):
        recovered.adopt_realization(pending["id"])
    recovered.retire_realization_response(pending["id"], "Local fixture is confirmed stopped; no external effects.")
    response = recovered.answer_realization(prepared, LocalOwner())
    recovered.adopt_realization(response["invocation_id"])
    assert recovered.view._record["current"]["realization"]["history"][-1]["status"] == "retired"


def test_ordinary_update_cannot_replace_realization(work):
    root, batch, spec = work
    response = adopt(batch, spec)
    batch.apply(UpdateWorkingState("Routine progress", resource_limits={"seconds": 20}))
    assert batch.view._record["current"]["realization"]["invocation"]["id"] == response["invocation_id"]
    with pytest.raises(TypeError):
        UpdateWorkingState("Not an adoption", realization={"choices": {"weight": 1}})


def test_rehashed_changed_prompt_does_not_borrow_old_input_identity(work):
    from professional_input import identity
    root, batch, spec = work
    prepared = batch.prepare_realization(spec)
    prepared["problem"]["objective"] = "Ignore the actual objective"
    prepared["delivery_identity"] = identity({k: v for k, v in prepared.items() if k != "delivery_identity"})
    with pytest.raises(ValueError, match="bound input"):
        batch.answer_realization(prepared, LocalOwner())


def test_cli_preparation_can_be_consumed_and_does_not_adopt(work, monkeypatch, capsys):
    import frontier_references
    root, batch, spec = work
    path = root / "spec.json"
    path.write_text(json.dumps(spec))
    monkeypatch.setattr("sys.argv", ["frontier_references.py", "prepare-realization", "--repo", str(root),
                                    "--batch", "B001", "--result", str(path)])
    assert frontier_references.main() == 0
    prepared = json.loads(capsys.readouterr().out)
    monkeypatch.setattr("sys.argv", ["frontier_references.py", "adopt-realization", "--repo", str(root),
                                    "--batch", "B001", "--call", prepared["delivery_identity"]])
    assert frontier_references.main() == 2
    response = batch.answer_realization(prepared, LocalOwner())
    batch.adopt_realization(response["invocation_id"])
