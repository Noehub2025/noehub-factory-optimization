"""Mechanical adapter tests; no external model calls or behavioral claims."""
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import codex_owner_acceptance as adapter
from frontier_batch import Batch, DefineBatch
from context_delivery import read_retained


@pytest.fixture
def work(tmp_path, monkeypatch):
    monkeypatch.setattr(adapter, "ACCEPTANCE_ROOT", tmp_path)
    root = tmp_path / "allocation-1"
    root.mkdir()
    files, definition, spec = adapter.case("allocation-1")
    for name, body in files.items():
        (root / name).write_text(body)
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    batch = Batch.open(root, "B001")
    batch.apply(DefineBatch(objective=definition["objective"], acceptance=definition["acceptance"],
                           scope=tuple(definition["scope"])))
    prepared = batch.prepare_realization(spec)
    return root, batch, prepared, adapter.request_text(prepared)


def stream(answer=None):
    answer = answer or {"choices": {"selected": ["B", "C"]}, "rationale": "Feasible joint return.",
                        "observation": "Compare terminal return with the incumbent.",
                        "grounds": [{"path": "allocation.md"}]}
    return "\n".join(json.dumps(event) for event in [
        {"type": "thread.started", "thread_id": "local-fixture"}, {"type": "turn.started"},
        {"type": "item.completed", "item": {"type": "agent_message", "text": json.dumps(answer)}},
        {"type": "turn.completed", "usage": {"input_tokens": 100, "output_tokens": 20}}])


def fake_process(monkeypatch, *, output=None, error=None, returncode=0):
    calls = []

    class Process:
        pid = 24680

        def __init__(self, command, **kwargs):
            self.returncode = returncode
            self.count = 0
            calls.append((command, kwargs, self))

        def communicate(self, text=None, timeout=None):
            self.count += 1
            self.last_input = text
            if error and self.count == 1:
                raise error
            return stream() if output is None else output, "synthetic diagnostic"

    monkeypatch.setattr(adapter.subprocess, "Popen", Process)
    monkeypatch.setattr(adapter.subprocess, "run", lambda *a, **k: SimpleNamespace(stdout="codex test-runtime"))
    return calls


def test_fixed_request_only_before_any_process(work, monkeypatch):
    root, batch, prepared, prompt = work
    fake_process(monkeypatch)
    assert len(adapter.validate_input(root, "allocation-1", prompt)) == 6
    with pytest.raises(ValueError, match="arbitrary"):
        adapter.CodexOwnerAdapter("allocation-1").reply(root.parent, prompt)
    with pytest.raises(ValueError, match="differs"):
        adapter.CodexOwnerAdapter("allocation-1").reply(root, prompt + "secret material")
    (root / "allocation.md").write_text("Real project data must not enter the synthetic request.")
    with pytest.raises(ValueError, match="input changed"):
        adapter.CodexOwnerAdapter("allocation-1").reply(root, prompt)
    assert not (root.parent / "allocation-1.attempt.json").exists()


def test_host_skills_cannot_enter_request(work):
    root, _, _, prompt = work
    (root / ".agents").mkdir()
    with pytest.raises(ValueError, match="Skills"):
        adapter.validate_input(root, "allocation-1", prompt)


def test_call_returns_bound_answer_and_cannot_spend_again(work, monkeypatch):
    root, batch, prepared, prompt = work
    calls = fake_process(monkeypatch)
    response = batch.answer_realization(prepared, adapter.CodexOwnerAdapter("allocation-1"))
    batch.adopt_realization(response["invocation_id"])
    trace = batch.view._record["current"]["realization"]["invocation"]["trace"]
    assert "For indivisible requests" in read_retained(root, trace["request"])
    assert trace["runtime"] == "codex test-runtime"
    assert trace["usage"]["input_tokens"] == 100
    command, kwargs, process = calls[0]
    assert kwargs["cwd"] != str(root)
    assert "--ignore-user-config" in command and "--no-daemon" in command
    assert "project_doc_max_bytes=0" in command and 'web_search="disabled"' in command
    assert "features.skip_host_skill_discovery=true" in command
    for feature in adapter.DISABLED_FEATURES:
        assert command[command.index(feature) - 1] == "--disable"
    with pytest.raises(FileExistsError):
        adapter.CodexOwnerAdapter("allocation-1").reply(root, prompt)
    assert len(calls) == 1


@pytest.mark.parametrize("bad", ["", '{"type":"turn.completed"}',
    '{"type":"turn.failed"}', '{"type":"item.started","item":{"type":"command_execution"}}',
    "not-json"])
def test_no_completion_or_tool_activity_cannot_be_adopted(bad):
    with pytest.raises(ValueError):
        adapter.parse_response(bad)


def test_known_startup_diagnostic_is_not_tool_activity():
    diagnostic = json.dumps({"type": "item.completed", "item": {"type": "error",
        "message": "Code Mode is unavailable because code-mode host is disabled. Closed."}})
    answer, _ = adapter.parse_response(diagnostic + "\n" + stream())
    assert answer["choices"] == {"selected": ["B", "C"]}
    with pytest.raises(ValueError):
        adapter.parse_response(diagnostic.replace("Code Mode is unavailable", "Unexpected failure") + "\n" + stream())


def test_schema_constrains_format_without_selecting_a_solution():
    schema = adapter.answer_schema("allocation-1")
    assert schema["properties"]["observation"]["type"] == "string"
    assert schema["properties"]["choices"]["properties"]["selected"]["items"]["enum"] == ["A", "B", "C"]


def test_timeout_kills_and_drains_without_resending(work, monkeypatch):
    root, batch, prepared, prompt = work
    calls = fake_process(monkeypatch, error=subprocess.TimeoutExpired("codex", 180))
    killed = []
    monkeypatch.setattr(adapter.os, "killpg", lambda pid, signal: killed.append(pid))
    with pytest.raises(subprocess.TimeoutExpired):
        batch.answer_realization(prepared, adapter.CodexOwnerAdapter("allocation-1"))
    assert killed == [24680]
    assert calls[0][2].count == 2 and calls[0][2].last_input is None
    saved = json.loads((root.parent / "allocation-1.attempt.json").read_text())
    assert saved["status"] == "failed"
    assert read_retained(root, saved["trace"]["stdout"])
    assert batch.view._record["current"]["realization"]["invocation"]["status"] == "failed"


def test_nonzero_exit_never_uses_an_answer(work, monkeypatch):
    root, batch, prepared, _ = work
    fake_process(monkeypatch, returncode=1)
    with pytest.raises(ValueError, match="status 1"):
        batch.answer_realization(prepared, adapter.CodexOwnerAdapter("allocation-1"))
    assert batch.view._record["current"]["realization"]["choice"] is None


def test_input_changed_during_reply_is_not_adopted(work, monkeypatch):
    root, batch, prepared, _ = work
    fake_process(monkeypatch)
    original = adapter.parse_response

    def changed(text):
        (root / "allocation.md").write_text("Changed method after dispatch.")
        return original(text)

    monkeypatch.setattr(adapter, "parse_response", changed)
    with pytest.raises(ValueError, match="input changed"):
        batch.answer_realization(prepared, adapter.CodexOwnerAdapter("allocation-1"))
    assert batch.view._record["current"]["realization"]["choice"] is None


def test_actual_consumer_uses_response_without_another_call(tmp_path, monkeypatch):
    monkeypatch.setattr(adapter, "ACCEPTANCE_ROOT", tmp_path)
    actual_run = subprocess.run
    actual_popen = subprocess.Popen
    fake_process(monkeypatch)
    fixture_popen = subprocess.Popen
    monkeypatch.setattr(adapter.subprocess, "Popen", lambda args, **kw:
        actual_popen(args, **kw) if args[0] == "git" else fixture_popen(args, **kw))
    monkeypatch.setattr(adapter.subprocess, "run", lambda args, **kw:
        actual_run(args, **kw) if args[0] == "git" else SimpleNamespace(stdout="codex test-runtime"))
    result = adapter.run_trial("allocation-1")
    assert result["outcome"]["result"] == {"cost": 12, "return": 22, "incumbent_return": 16}
    with pytest.raises(FileExistsError):
        adapter.run_trial("allocation-1")
