"""Ordinary project entry, scoped retrieval, recovery and actual consumption."""
import json
from pathlib import Path
import subprocess
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "adapters"))
import codex_owner as owner
from context_delivery import read_retained
from frontier_batch import Batch, DefineBatch, Action, OperationBinding, OperationResult
from professional_input import OwnerTransportError


@pytest.fixture
def project(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / "AGENTS.md").write_text("Use maintained [capabilities](knowledge.md).")
    (tmp_path / "owner.md").write_text("Select a useful implementation and observation.")
    (tmp_path / "knowledge.md").write_text("# Methods\n\n[Coordinated width](method.md) applies to shared capacity.\n")
    (tmp_path / "method.md").write_text("# Coordinated width\n\nActual method content: coordinate width with the available capacity.\n")
    (tmp_path / "input.json").write_text(json.dumps({"capacity": 2, "progress": 0}))
    (tmp_path / "configuration.json").write_text(json.dumps({"solver": {"width": 1}, "format": "json"}))
    batch = Batch.open(tmp_path, "B417")
    batch.apply(DefineBatch(objective="Use shared capacity effectively.", acceptance="A useful observation.",
                            scope=("local implementation",)))
    spec = {"owner": "owner.md", "intended_decision": "Choose operating width and first observation.",
            "consumer": "existing-program", "operations": ["run", "run-alias"],
            "sources": [{"path": "input.json", "field": "capacity"}], "conditions": {"local": True}}
    packet = owner.prepare_request(tmp_path, "B417", spec=spec)
    return tmp_path, batch, packet


def answer(ids=()):
    return {"kind": "answer", "source_ids": list(ids),
            "choices": [{"selector": "solver.width", "value_json": "2"}],
            "rationale": "Use the supported coordinated width for the current capacity.",
            "observation": "Observe completed work using the selected configuration."}


class Backend:
    def __init__(self, *responses):
        self.responses, self.calls = list(responses), []

    def call(self, root, prompt, timeout):
        self.calls.append(prompt)
        response = self.responses.pop(0)
        if callable(response):
            response = response(root, prompt)
        if isinstance(response, BaseException):
            raise response
        return response, {"request": owner.retain_source(root, prompt), "usage": {"input_tokens": 10}}


def use(project, backend, max_calls=2):
    root, _, packet = project
    return owner.answer_request(root, packet, backend, max_calls=max_calls, timeout_seconds=30)


def test_resource_not_in_assignment_is_requested_before_choice(project):
    root, batch, packet = project
    sid = owner.source_id({"path": "method.md"})
    backend = Backend({"kind": "read", "source_ids": [sid], "choices": [], "rationale": "Read its applicable method.",
                       "observation": ""}, answer([sid]))
    result = use(project, backend)
    assert "Actual method content" not in backend.calls[0]
    assert "Actual method content" in backend.calls[1]
    batch.adopt_realization(result["invocation_id"])
    assert batch.realization_choices() == {"solver.width": 2}
    defaults = {"solver": {"width": 1}, "format": "json"}

    def consume(action, context, effective):
        process = subprocess.run([sys.executable, "-c",
            "import json,sys; c=json.load(sys.stdin); print(json.dumps({'processed':c['solver']['width']}))"],
            input=json.dumps(effective), capture_output=True, text=True, check=True)
        return OperationResult("completed", result=json.loads(process.stdout))

    binding = OperationBinding.configured(lambda a, c: defaults, consume)
    result = Batch.open(root, "B417", operations={"run": binding}).perform(Action("observe", "run", "preparation"))
    assert result.operation_result.result == {"processed": 2}
    assert defaults["solver"]["width"] == 1


def test_unchanged_answer_recovery_uses_no_model_and_ignores_progress(project):
    root, batch, packet = project
    backend = Backend(answer())
    result = use(project, backend)
    batch.adopt_realization(result["invocation_id"])
    (root / "input.json").write_text(json.dumps({"capacity": 2, "progress": 50}))
    again = use(project, backend)
    assert again["response_id"] == result["response_id"]
    assert len(backend.calls) == 1


@pytest.mark.parametrize("change", ["condition", "grounds"])
def test_recovery_rejects_changed_applicability_or_delivered_grounds(project, change):
    root, _, packet = project
    if change == "condition":
        sid = owner.source_id({"path": "input.json", "field": "capacity"})
        result = use(project, Backend(answer([sid])))
        (root / "input.json").write_text(json.dumps({"capacity": 3}))
    else:
        sid = owner.source_id({"path": "method.md"})
        result = use(project, Backend({"kind": "read", "source_ids": [sid], "choices": []}, answer([sid])))
        (root / "method.md").write_text("The retained method was corrected.")
    with pytest.raises(ValueError):
        owner.recover_response(root, "B417")
    with pytest.raises(ValueError):
        Batch.open(root, "B417").adopt_realization(result["invocation_id"])


def test_retirement_during_actual_host_callback_rejects_old_return(project):
    root, batch, packet = project

    def retired(root, prompt):
        active = Batch.open(root, "B417").view._record["current"]["realization"]["invocation"]
        batch.retire_realization_response(active["id"], "The owner revised this choice.")
        return answer()

    with pytest.raises(Exception, match="superseded"):
        use(project, Backend(retired))
    assert Batch.open(root, "B417").view._record["current"]["realization"]["choice"] is None


def test_unknown_source_does_not_read_files_or_get_another_call(project):
    backend = Backend({"kind": "read", "source_ids": ["../../outside"], "choices": []})
    with pytest.raises(OwnerTransportError, match="unavailable"):
        use(project, backend)
    assert len(backend.calls) == 1


def test_unread_citation_cannot_be_accepted(project):
    with pytest.raises(OwnerTransportError, match="not supplied"):
        use(project, Backend(answer([owner.source_id({"path": "method.md"})])))


def test_call_allowance_stops_without_retry_or_invented_answer(project):
    root, _, _ = project
    sid = owner.source_id({"path": "method.md"})
    backend = Backend({"kind": "read", "source_ids": [sid], "choices": []})
    with pytest.raises(OwnerTransportError, match="call allowance"):
        use(project, backend, max_calls=1)
    with pytest.raises(ValueError, match="failed invocation"):
        use(project, backend)
    assert len(backend.calls) == 1
    assert Batch.open(root, "B417").view._record["current"]["realization"]["choice"] is None


def test_recover_completed_transport_after_host_interruption(project, monkeypatch):
    root, batch, packet = project
    original = Batch.receive_realization
    monkeypatch.setattr(Batch, "receive_realization", lambda *a: (_ for _ in ()).throw(KeyboardInterrupt()))
    backend = Backend(answer())
    with pytest.raises(KeyboardInterrupt):
        use(project, backend)
    monkeypatch.setattr(Batch, "receive_realization", original)
    result = owner.recover_response(root, "B417")
    batch.adopt_realization(result["invocation_id"])
    assert batch.realization_choices()["solver.width"] == 2
    assert len(backend.calls) == 1


def test_incomplete_transport_cannot_be_replayed(project, monkeypatch):
    root, batch, packet = project
    with pytest.raises(KeyboardInterrupt):
        use(project, Backend(KeyboardInterrupt()))
    with pytest.raises(ValueError, match="incomplete or uncertain"):
        owner.recover_response(root, "B417")


def test_explicit_scope_blocks_outside_and_symlink_sources(project, tmp_path):
    root, _, packet = project
    outside = root.parent / "external-material.md"
    outside.write_text("Outside the selected workspace")
    (root / "linked.md").symlink_to(outside)
    for path in [str(outside), "linked.md"]:
        with pytest.raises(ValueError, match="inside the project"):
            owner.prepare_request(root, "B417", materials=[{"path": path}])


def test_missing_maintained_link_is_visible_without_blocking_other_work(project):
    root, _, _ = project
    with (root / "knowledge.md").open("a") as stream:
        stream.write("\n[Unavailable option](missing-method.md)\n")
    packet = owner.prepare_request(root, "B417")
    absent = next(row for row in packet["catalog"] if row["source"]["path"] == "missing-method.md")
    assert not absent["available"]
    result = owner.answer_request(root, packet, Backend(answer()), max_calls=1, timeout_seconds=30)
    assert result["choice"]["choices"]["solver.width"] == 2


def test_outside_instruction_link_is_a_visible_inventory_limit(project):
    root, _, _ = project
    with (root / "AGENTS.md").open("a") as stream:
        stream.write("\n[Host reference](/outside-project/method.md)\n")
    packet = owner.prepare_request(root, "B417")
    assert any("outside the project" in item for item in packet["prepared"]["resources"]["limitations"])
    assert all("outside-project" not in row["source"]["path"] for row in packet["catalog"])


def test_new_conditions_can_be_reprepared_without_touching_prior_results(project):
    root, batch, packet = project
    result = use(project, Backend(answer()))
    batch.adopt_realization(result["invocation_id"])
    batch.retire_realization_response(result["invocation_id"], "Changed capacity needs a new choice.")
    (root / "input.json").write_text(json.dumps({"capacity": 4}))
    newer = owner.prepare_request(root, "B417")
    changed = answer()
    changed["choices"][0]["value_json"] = "4"
    current = owner.answer_request(root, newer, Backend(changed), max_calls=1, timeout_seconds=30)
    batch.adopt_realization(current["invocation_id"])
    assert batch.realization_choices() == {"solver.width": 4}
    assert len(batch.view._record["current"]["realization"]["history"]) == 1


def test_changed_material_between_delivery_and_return_does_not_borrow_current_bytes(project):
    root, _, _ = project
    sid = owner.source_id({"path": "method.md"})

    def changed(root, prompt):
        (root / "method.md").write_text("The conditions for this method changed.")
        return answer([sid])

    backend = Backend({"kind": "read", "source_ids": [sid], "choices": []}, changed)
    with pytest.raises(OwnerTransportError, match="grounds changed"):
        use(project, backend)


def test_configured_consumer_keeps_effect_policy_and_rejects_unknown_selectors(project):
    root, batch, packet = project
    result = use(project, Backend(answer()))
    batch.adopt_realization(result["invocation_id"])
    binding = OperationBinding.configured(lambda a, c: {}, lambda *a: pytest.fail("must not run"))
    with pytest.raises(Exception, match="lacks selected"):
        Batch.open(root, "B417", operations={"run": binding}).perform(Action("bad", "run", "preparation"))
    protected = OperationBinding.configured(lambda a, c: {}, lambda *a: None, ("external_execution",))
    assert protected.protected_consequences == ("external_execution",)


def test_normal_cli_entry_works_with_nonfixture_batch(project):
    root, batch, _ = project
    request = root / "owner-request.json"
    binary = root / "local-transport-fixture"
    body = "\n".join(json.dumps(e) for e in [
        {"type": "thread.started", "thread_id": "local-fixture"}, {"type": "turn.started"},
        {"type": "item.completed", "item": {"type": "agent_message", "text": json.dumps(answer())}},
        {"type": "turn.completed", "usage": {"input_tokens": 0, "output_tokens": 0}}])
    binary.write_text("#!/usr/bin/env python3\nimport sys\n"
                      "if '--version' in sys.argv: print('local-fixture');sys.exit(0)\n"
                      "sys.stdin.read()\nprint(" + repr(body) + ")\n")
    binary.chmod(0o700)
    command = [sys.executable, str(Path(owner.__file__)), "prepare", "--root", str(root), "--batch", "B417",
               "--request", str(request)]
    subprocess.run(command, check=True, capture_output=True, text=True)
    command[2] = "answer"
    command += ["--binary", str(binary), "--model", "test-model", "--effort", "low",
                "--max-calls", "1", "--timeout-seconds", "30"]
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    response = json.loads(result.stdout)
    subprocess.run([sys.executable, str(Path(owner.__file__)), "adopt", "--root", str(root), "--batch", "B417",
                    "--invocation", response["invocation_id"]], check=True, capture_output=True)
    assert Batch.open(root, "B417").realization_choices() == {"solver.width": 2}


@pytest.mark.parametrize("stream", ["", '{"type":"turn.completed"}', '{"type":"turn.failed"}',
    '{"type":"item.started","item":{"type":"command_execution"}}'])
def test_project_transport_rejects_missing_completion_and_tool_activity(stream):
    with pytest.raises(ValueError):
        owner.parse_response(stream)


def test_project_transport_timeout_retains_failure_and_drains_once(project, monkeypatch):
    from types import SimpleNamespace

    root, _, _ = project
    calls, killed = [], []

    class Process:
        pid = 123456
        returncode = -9

        def communicate(self, text=None, timeout=None):
            calls.append((text, timeout))
            if len(calls) == 1:
                raise subprocess.TimeoutExpired("codex", timeout)
            return "partial response", "timeout diagnostic"

    monkeypatch.setattr(owner.subprocess, "run", lambda *a, **k: SimpleNamespace(stdout="test-runtime"))
    monkeypatch.setattr(owner.subprocess, "Popen", lambda *a, **k: Process())
    monkeypatch.setattr(owner.os, "killpg", lambda pid, sig: killed.append(pid))
    with pytest.raises(OwnerTransportError) as caught:
        owner.CodexBackend(binary="test", model="selected", effort="low").call(root, "supplied input", 10)
    assert killed == [123456]
    assert calls[0][0] == "supplied input" and calls[1] == (None, None)
    assert read_retained(root, caught.value.trace["stdout"]) == "partial response"


def test_retired_read_request_cannot_continue_another_model_round(project):
    root, batch, _ = project
    sid = owner.source_id({"path": "method.md"})

    def retire_before_read(root, prompt):
        invocation = Batch.open(root, "B417").view._record["current"]["realization"]["invocation"]
        batch.retire_realization_response(invocation["id"], "Corrected active work.")
        return {"kind": "read", "source_ids": [sid], "choices": []}

    backend = Backend(retire_before_read, answer([sid]))
    with pytest.raises(OwnerTransportError, match="retired or replaced"):
        use(project, backend)
    assert len(backend.calls) == 1
