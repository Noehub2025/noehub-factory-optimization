"""Exercise the project dispatch and recovery entry, including its host association."""
import importlib.util
import json
import shutil
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
ENTRY = ROOT / "scripts/workflow_task.py"
spec = importlib.util.spec_from_file_location("workflow_task", ENTRY)
entry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(entry)


def case(root):
    (root / "original.txt").write_text("Question: Training? Answer: Local. Correction: feedback is separate.")
    (root / "interpretation.txt").write_text("Local training; feedback remains separately authorized.")
    (root / "assignment.md").write_text("Recover scope without starting an experiment.")
    consumer = """import json, sys
from pathlib import Path
request = sys.stdin.read()
p = Path('calls')
p.write_text(p.read_text() + 'x' if p.exists() else 'x')
print(json.dumps({'type': 'item.completed', 'item': {'type': 'agent_message', 'text': request}}))
print(json.dumps({'type': 'turn.completed'}))
"""
    (root / "entry.json").write_text(json.dumps({"command": [sys.executable, "-c", consumer]}))
    owner = {"current_state": {"campaign_status": "running"},
             "execution_entry": {"configuration": "entry.json"},
             "decision_material": {"user_scope": [{"original": [{"path": "original.txt"}],
                "interpretation": {"path": "interpretation.txt"}}]}}
    (root / "owner.json").write_text(json.dumps(owner))
    return owner


def cli(root, operation, *extra):
    return subprocess.run([sys.executable, str(ENTRY), operation, "--root", str(root),
        "--invocation", "one", *extra], capture_output=True, text=True)


def test_normal_cli_checks_actual_input_and_recovers_without_another_call(tmp_path):
    case(tmp_path)
    sent = cli(tmp_path, "run", "--owner", "owner.json", "--assignment", "assignment.md")
    assert sent.returncode == 0, sent.stdout + sent.stderr
    result = json.loads(sent.stdout)
    assert "Correction: feedback is separate" in result["answer"]
    assert "Local training; feedback remains separately authorized" in result["answer"]
    assert result["applicability"] == "current"
    restored = cli(tmp_path, "recover")
    assert restored.returncode == 0, restored.stdout + restored.stderr
    assert json.loads(restored.stdout)["receipt"] == result["receipt"]
    duplicate = cli(tmp_path, "run", "--owner", "owner.json", "--assignment", "assignment.md")
    assert duplicate.returncode == 2
    assert (tmp_path / "calls").read_text() == "x"


def test_changed_original_blocks_adoption_but_keeps_historical_receipt(tmp_path):
    case(tmp_path)
    first = entry.run(tmp_path, "owner.json", "assignment.md", "one", "scope")
    (tmp_path / "original.txt").write_text("Permission withdrawn.")
    restored = entry.recover(tmp_path, "one")
    assert restored["applicability"] == "requires_owner_reconciliation"
    assert restored["receipt"] == first["receipt"]
    assert restored["replayed"] is False
    assert (tmp_path / "calls").read_text() == "x"


def test_pause_blocks_dispatch_but_keeps_read_only_recovery(tmp_path):
    owner = case(tmp_path)
    entry.run(tmp_path, "owner.json", "assignment.md", "one", "scope")
    owner["current_state"]["campaign_status"] = "paused"
    (tmp_path / "owner.json").write_text(json.dumps(owner))
    with pytest.raises(ValueError, match="no running work"):
        entry.run(tmp_path, "owner.json", "assignment.md", "two", "scope")
    assert entry.recover(tmp_path, "one")["receipt"]["status"] == "completed"
    assert not entry.direction_owner._location(tmp_path, "two").exists()


def test_default_owner_comes_from_existing_host_pointer(tmp_path, monkeypatch):
    case(tmp_path)
    monkeypatch.setattr(entry, "root_session", lambda: "current")
    directory = tmp_path / ".frontier/hook-context"
    directory.mkdir(parents=True)
    (directory / "current.json").write_text(json.dumps({"kind": "adopted_work",
        "workspace": str(tmp_path), "selection": {"path": "owner.json"}}))
    assert entry.owner_path(tmp_path, None) == "owner.json"


def test_uncertain_record_does_not_invoke_consumer(tmp_path):
    case(tmp_path)
    first = entry.run(tmp_path, "owner.json", "assignment.md", "one", "scope")
    receipt = {**first["receipt"], "status": "started"}
    entry.direction_owner.save(entry.direction_owner._location(tmp_path, "one") / "receipt.json", receipt)
    restored = entry.recover(tmp_path, "one")
    assert restored["applicability"] == "unresolved"
    assert restored["receipt"]["status"] == "uncertain"
    assert (tmp_path / "calls").read_text() == "x"


def test_current_codex_reads_checked_context_without_another_consumer(tmp_path):
    case(tmp_path)
    (tmp_path / "entry.json").write_text('{"receiver":"current_codex"}')
    result = cli(tmp_path, "current", "--owner", "owner.json", "--assignment", "assignment.md")
    assert result.returncode == 0, result.stdout + result.stderr
    directory = entry.direction_owner._location(tmp_path, "one")
    assert result.stdout == (directory / "request.txt").read_text()
    assert "Correction: feedback is separate" in result.stdout
    assert not (tmp_path / "calls").exists()
    restored = json.loads(cli(tmp_path, "recover").stdout)
    assert restored["applicability"] == "current" and not restored["replayed"]
    assert restored["receipt"]["status"] == "material_ready"
    assert "answer" not in restored


def test_current_codex_configuration_cannot_launch_cli(tmp_path):
    case(tmp_path)
    (tmp_path / "entry.json").write_text('{"receiver":"current_codex"}')
    with pytest.raises(ValueError, match="no CLI model call"):
        entry.run(tmp_path, "owner.json", "assignment.md", "one", "scope")
    assert not entry.direction_owner._location(tmp_path, "one").exists()


def test_current_codex_recovery_keeps_changed_basis_historical(tmp_path):
    case(tmp_path)
    (tmp_path / "entry.json").write_text('{"receiver":"current_codex"}')
    entry.current(tmp_path, "owner.json", "assignment.md", "one", "scope")
    (tmp_path / "original.txt").write_text("The original scope changed.")
    result = entry.recover(tmp_path, "one")
    assert result["applicability"] == "requires_owner_reconciliation"
    assert "answer" not in result and not result["replayed"]


def test_failed_or_incomplete_model_turn_is_not_adoptable():
    for raw in [b'{"type":"turn.failed"}\n', b'{"type":"thread.started"}\n']:
        with pytest.raises(ValueError):
            entry.final_message(raw)


def test_pause_before_preparation_cannot_pass_as_current(tmp_path, monkeypatch):
    owner = case(tmp_path)
    original_prepare = entry.direction_owner.prepare

    def pause_then_prepare(*args, **kwargs):
        owner["current_state"]["campaign_status"] = "paused"
        (tmp_path / "owner.json").write_text(json.dumps(owner))
        return original_prepare(*args, **kwargs)

    monkeypatch.setattr(entry.direction_owner, "prepare", pause_then_prepare)
    with pytest.raises(ValueError, match="Owner changed"):
        entry.run(tmp_path, "owner.json", "assignment.md", "one", "scope")
    assert not (tmp_path / "calls").exists()



@pytest.mark.parametrize("layout", [".agents/skills", ".claude/skills"])
def test_installed_task_entry_reads_and_recovers_without_distribution_paths(tmp_path, layout):
    case(tmp_path)
    (tmp_path / "entry.json").write_text('{"receiver":"current_codex"}')
    shutil.copytree(ROOT / "skills", tmp_path / layout,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copytree(ROOT / "tools/workflow-harness/adapters",
                    tmp_path / "tools/workflow-harness/adapters",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    (tmp_path / "scripts").mkdir()
    installed = tmp_path / "scripts/workflow_task.py"
    shutil.copy2(ENTRY, installed)
    command = [sys.executable, str(installed), "current", "--root", str(tmp_path),
               "--owner", "owner.json", "--assignment", "assignment.md",
               "--invocation", "installed", "--event", "scope"]
    read = subprocess.run(command, capture_output=True, text=True)
    assert read.returncode == 0, read.stdout + read.stderr
    assert "Correction: feedback is separate" in read.stdout
    saved = tmp_path / "artifacts/workflow-harness/direction-calls/installed/request.txt"
    assert read.stdout == saved.read_text()
    recovered = subprocess.run([sys.executable, str(installed), "recover",
        "--root", str(tmp_path), "--invocation", "installed"], capture_output=True, text=True)
    assert recovered.returncode == 0, recovered.stdout + recovered.stderr
    result = json.loads(recovered.stdout)
    assert result["applicability"] == "current" and not result["replayed"]
    assert result["receipt"]["status"] == "material_ready"
    assert not (tmp_path / "calls").exists()
