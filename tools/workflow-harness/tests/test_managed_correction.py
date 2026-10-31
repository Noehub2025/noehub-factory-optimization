"""Crash recovery through the ordinary Python entry and real managed host."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

ROOT = Path(__file__).resolve().parents[3]
ENTRY = ROOT / "tools/workflow-harness/adapters/managed_correction.py"
BINARY = ROOT / "tools/workflow-harness/target/debug/workflow-harness"
spec = importlib.util.spec_from_file_location("managed_correction", ENTRY)
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)


def test_default_binary_follows_documented_build_and_keeps_debug_fallback(tmp_path, monkeypatch):
    monkeypatch.setattr(adapter, "REPOSITORY", tmp_path)
    target = tmp_path / "tools/workflow-harness/target"
    release = target / "release/workflow-harness"
    debug = target / "debug/workflow-harness"
    assert adapter.default_binary() == release
    debug.parent.mkdir(parents=True)
    debug.write_text("fixture")
    debug.chmod(0o700)
    assert adapter.default_binary() == debug
    release.parent.mkdir(parents=True)
    release.write_text("fixture")
    release.chmod(0o600)
    assert adapter.default_binary() == debug
    release.chmod(0o700)
    assert adapter.default_binary() == release


@pytest.fixture
def work(tmp_path):
    if not BINARY.is_file():
        pytest.skip("Build workflow-harness before running real host integration tests")
    (tmp_path / "source.md").write_text("Old selected scope.\n")
    (tmp_path / "finding.md").write_text("The owner confirmed the source scope needs correction.\n")
    (tmp_path / "adoption.md").write_text("The owner adopts the new scope for this receiving use.\n")
    (tmp_path / "owner.json").write_text('{}')
    task = {"objective": "Check the selected scope", "controlling_objective": 0,
            "workspace": str(tmp_path), "constraints": "Local test only",
            "sources": [{"path": "source.md", "first_line": 1, "last_line": 1,
                         "purpose": "governing source", "roles": ["coordinator", "worker"]}],
            "invocation_limit": 8}
    (tmp_path / "task.json").write_text(json.dumps(task))
    session = tmp_path / "run"
    started = subprocess.run([str(BINARY), "host", "start", str(tmp_path / "task.json"), str(session)],
                             text=True, capture_output=True, check=True)
    assert json.loads(started.stdout)["invocation_id"] == 1
    backend = tmp_path / "backend.py"
    backend.write_text("import json,pathlib,sys,time\nr=json.loads(sys.stdin.readline())\n"
                       "pathlib.Path('installed').touch()\nwhile not pathlib.Path('stop-backend').exists(): time.sleep(.05)\n")
    driver = subprocess.Popen([str(BINARY), "host", "managed-drive", str(session)],
                              stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              text=True, start_new_session=True)
    driver.stdin.write(json.dumps({"program": sys.executable, "args": [str(backend)]}))
    driver.stdin.close()
    deadline = time.monotonic() + 5
    while not (tmp_path / "installed").exists():
        if time.monotonic() >= deadline:
            pytest.fail("managed host did not install the fixture backend")
        time.sleep(.01)
    request = {"source": {"corrections": [{"id": "scope", "finding": "finding.md", "effect": "repair",
                "affected_sources": ["source.md"], "status": "resolved",
                "resolution": {"reason": "Use the owner's corrected scope", "evidence": "adoption.md"}}],
                "replacements": [{"path": "source.md", "contents": "Corrected selected scope.\n"}]},
               "replacement": {"assignment": "Use the corrected scope and retain earlier effects."}}
    yield tmp_path, session, request
    (tmp_path / "stop-backend").touch()
    try:
        driver.wait(timeout=3)
    except subprocess.TimeoutExpired:
        # Only a stuck fixture needs forced cleanup; completed process groups
        # may no longer be signalable on a sandboxed host.
        import signal
        try:
            os.killpg(driver.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        driver.wait(timeout=5)
    driver.stdout.close()
    driver.stderr.close()


def cli(root, *args):
    return subprocess.run([sys.executable, str(ENTRY), *args, "--root", str(root), "--owner", "owner.json",
                           "--activation", "repair-1", "--binary", str(BINARY)],
                          text=True, capture_output=True, timeout=10)


def checkpoint(session):
    return json.loads((session / "state.json").read_text())


def test_normal_cli_adopts_and_retires_then_recovery_does_not_redispatch(work):
    root, session, request = work
    (root / "correction.json").write_text(json.dumps(request))
    result = cli(root, "apply", "--session", str(session), "--expected-invocation", "1", "--request", str(root / "correction.json"))
    assert result.returncode == 0, result.stderr
    activated = json.loads(result.stdout)
    assert activated["status"] == "activated" and activated["source_revision_current"]
    assert "Corrected selected scope." in activated["successor"]["prompt"]
    saved = checkpoint(session)
    assert saved["managed"]["invocations"]["1"]["phase"] == "retired"
    recovered = cli(root, "recover")
    assert recovered.returncode == 0, recovered.stderr
    assert json.loads(recovered.stdout)["successor"]["invocation_id"] == activated["successor"]["invocation_id"]
    assert checkpoint(session)["runtime"]["next_id"] == saved["runtime"]["next_id"]
    # Progress does not invalidate the actual current-use bytes installed in the host.
    for source in checkpoint(session)["current_use"]["adopted"]["files"]:
        assert Path(source["path"]).read_text() == source["contents"]


def test_crash_after_source_completion_recovers_from_retained_association(work, monkeypatch):
    root, session, request = work
    real_adopt = adapter.adopt_current_work
    def interrupted(*args, **kwargs):
        real_adopt(*args, **kwargs)
        raise RuntimeError("process interrupted after source completion")
    monkeypatch.setattr(adapter, "adopt_current_work", interrupted)
    with pytest.raises(RuntimeError, match="after source completion"):
        adapter.apply(root, "owner.json", session, "repair-1", 1, request, BINARY)
    association = json.loads(adapter._journal(root, "owner.json", "repair-1").read_text())
    assert association["source_state"] == "prepared"
    assert (root / "source.md").read_text() == "Corrected selected scope.\n"
    assert "repair-1" not in checkpoint(session)["managed"]["corrections"]
    # A fresh process receives only the journal lookup identity, not the request.
    recovered = cli(root, "recover")
    assert recovered.returncode == 0, recovered.stderr
    assert json.loads(recovered.stdout)["status"] == "activated"


def test_preparation_does_not_claim_adoption(work, monkeypatch):
    root, session, request = work
    monkeypatch.setattr(adapter, "adopt_current_work", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("before adoption")))
    with pytest.raises(RuntimeError):
        adapter.apply(root, "owner.json", session, "repair-1", 1, request, BINARY)
    record = json.loads(adapter._journal(root, "owner.json", "repair-1").read_text())
    assert not adapter._source_adopted(root, "owner.json", record["association"])
    assert (root / "source.md").read_text() == "Old selected scope.\n"
    assert cli(root, "recover").returncode == 0


def test_lost_activation_acknowledgement_reuses_checkpoint(work, monkeypatch):
    root, session, request = work
    real_host = adapter._host
    calls = []
    def lost_ack(binary, command, *args, **kwargs):
        result = real_host(binary, command, *args, **kwargs)
        if command == "managed-correct":
            calls.append(command)
            raise subprocess.TimeoutExpired(command, 30)
        return result
    monkeypatch.setattr(adapter, "_host", lost_ack)
    result = adapter.apply(root, "owner.json", session, "repair-1", 1, request, BINARY)
    assert result["status"] == "activated" and calls == ["managed-correct"]
    assert cli(root, "recover").returncode == 0
    assert len(checkpoint(session)["managed"]["corrections"]) == 1


def test_changed_expected_invocation_requires_reconciliation(work, monkeypatch):
    root, session, request = work
    real_host = adapter._host
    def before_activation(binary, command, *args, **kwargs):
        if command == "managed-correct":
            raise RuntimeError("interrupted before activation")
        return real_host(binary, command, *args, **kwargs)
    monkeypatch.setattr(adapter, "_host", before_activation)
    with pytest.raises(RuntimeError):
        adapter.apply(root, "owner.json", session, "repair-1", 1, request, BINARY)
    other = {"correction_id": "other-owner", "expected_invocation": 1,
             "replacement": {"assignment": "A different current replacement", "actual_use": [str(root / "source.md")]}}
    report = adapter.check_current_use(root, "owner.json", [str(root / "source.md")])
    real_host(BINARY, "managed-correct", str(session), {**other, "current_use": report["current_use"]})
    result = cli(root, "recover")
    assert result.returncode == 2 and "expected invocation changed" in result.stderr
    assert "repair-1" not in checkpoint(session)["managed"]["corrections"]


def test_new_source_after_adoption_is_not_overwritten(work, monkeypatch):
    root, session, request = work
    real_host = adapter._host
    def stop(binary, command, *args, **kwargs):
        if command == "managed-correct":
            raise RuntimeError("stop")
        return real_host(binary, command, *args, **kwargs)
    monkeypatch.setattr(adapter, "_host", stop)
    with pytest.raises(RuntimeError):
        adapter.apply(root, "owner.json", session, "repair-1", 1, request, BINARY)
    (root / "source.md").write_text("Later owner revision.\n")
    result = cli(root, "recover")
    assert result.returncode == 2 and "source changed before activation" in result.stderr
    assert (root / "source.md").read_text() == "Later owner revision.\n"


def test_lost_ack_before_activation_stays_pending_until_recovery(work, monkeypatch):
    root, session, request = work
    real_host = adapter._host
    def timeout_before_send(binary, command, *args, **kwargs):
        if command == "managed-correct":
            raise subprocess.TimeoutExpired(command, 30)
        return real_host(binary, command, *args, **kwargs)
    monkeypatch.setattr(adapter, "_host", timeout_before_send)
    with pytest.raises(subprocess.TimeoutExpired):
        adapter.apply(root, "owner.json", session, "repair-1", 1, request, BINARY)
    assert "repair-1" not in checkpoint(session)["managed"]["corrections"]
    assert cli(root, "recover").returncode == 0
    assert len(checkpoint(session)["managed"]["corrections"]) == 1


def test_competitor_advance_cannot_install_stale_binding(work, monkeypatch):
    root, session, request = work
    (root / "other.md").write_text("Independent current use.\n")
    real_host = adapter._host
    def competing_activation(binary, command, target, value=None, extra=()):
        if command == "managed-correct":
            report = adapter.check_current_use(root, "owner.json", ["other.md"])
            other = {"correction_id": "competing", "expected_invocation": 1,
                     "replacement": {"assignment": "Use the independent current work.",
                                     "actual_use": [str(root / "other.md")]},
                     "current_use": report["current_use"]}
            real_host(binary, command, target, other)
        return real_host(binary, command, target, value, extra)
    monkeypatch.setattr(adapter, "_host", competing_activation)
    with pytest.raises(ValueError, match="expected invocation changed"):
        adapter.apply(root, "owner.json", session, "repair-1", 1, request, BINARY)
    saved = checkpoint(session)
    assert saved["current_use"]["adopted"]["checked_sources"] == [str(root / "other.md")]
    assert "repair-1" not in saved["managed"]["corrections"]
    assert saved["runtime"]["actual_use"] == [str(root / "other.md")]


def test_two_corrections_for_same_owner_cannot_publish_conflicting_sources(work):
    root, session, request = work
    second = json.loads(json.dumps(request))
    second["source"]["replacements"][0]["contents"] = "Another corrected selected scope.\n"
    second["replacement"]["assignment"] = "Use the competing corrected scope."
    processes = []
    for key, proposed in (("first", request), ("second", second)):
        path = root / f"{key}.json"
        path.write_text(json.dumps(proposed))
        processes.append((key, proposed, subprocess.Popen(
            [sys.executable, str(ENTRY), "apply", "--root", str(root), "--owner", "owner.json",
             "--activation", key, "--binary", str(BINARY), "--session", str(session),
             "--expected-invocation", "1", "--request", str(path)],
            text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)))
    results = [(key, proposed, child, child.communicate(timeout=10)) for key, proposed, child in processes]
    winners = [(key, proposed) for key, proposed, child, _ in results if child.returncode == 0]
    assert len(winners) == 1, results
    winner, proposed = winners[0]
    assert (root / "source.md").read_text() == proposed["source"]["replacements"][0]["contents"]
    assert set(checkpoint(session)["managed"]["corrections"]) == {winner}
    loser = next(output for _, _, child, output in results if child.returncode != 0)
    assert "expected invocation changed" in loser[1]


@pytest.mark.parametrize("changed", ["source.md", "adoption.md", "finding.md"])
def test_drift_before_binding_capture_cannot_activate_old_proposal(work, monkeypatch, changed):
    root, session, request = work
    original = adapter.check_current_use
    def advance_before_capture(*args, **kwargs):
        (root / changed).write_text("Later owner material requires reconciliation.\n")
        return original(*args, **kwargs)
    monkeypatch.setattr(adapter, "check_current_use", advance_before_capture)
    with pytest.raises(ValueError):
        adapter.apply(root, "owner.json", session, "repair-1", 1, request, BINARY)
    saved = checkpoint(session)
    assert "repair-1" not in saved["managed"]["corrections"]
    assert saved["managed"]["invocations"]["1"]["phase"] != "retired"
    assert (root / changed).read_text() == "Later owner material requires reconciliation.\n"
    record = json.loads(adapter._journal(root, "owner.json", "repair-1").read_text())
    assert record["association"]["activation_id"] == "repair-1"
    recovered = cli(root, "recover")
    assert recovered.returncode == 2 and "reconcile" in recovered.stderr


def test_pause_commits_complete_successor_and_resume_keeps_same_identity(work, monkeypatch):
    root, session, request = work
    original = adapter._host
    def pause_at_host_boundary(binary, command, target, value=None, extra=()):
        if command == "managed-correct":
            original(binary, "pause", target, "Pause until the owner resumes this fixture")
        return original(binary, command, target, value, extra)
    monkeypatch.setattr(adapter, "_host", pause_at_host_boundary)
    result = adapter.apply(root, "owner.json", session, "repair-1", 1, request, BINARY)
    successor = result["successor"]["invocation_id"]
    saved = checkpoint(session)
    assert saved["runtime"]["paused"] == "Pause until the owner resumes this fixture"
    assert saved["runtime"]["outstanding"]["invocation_id"] == successor
    assert saved["managed"]["invocations"]["1"]["phase"] == "retired"
    assert (session / f"request-{successor}.json").is_file()
    # Pause prevents installation, not just a later action inside the backend.
    blocked = subprocess.run([str(BINARY), "host", "managed-drive", str(session)],
                             input=json.dumps({"program": sys.executable, "args": ["-c", "raise AssertionError('must not run')"]}),
                             text=True, capture_output=True, timeout=10)
    assert blocked.returncode != 0 and "paused" in blocked.stderr
    assert cli(root, "recover").returncode == 0
    resumed = original(BINARY, "resume", str(session))
    assert resumed["invocation_id"] == successor
    recovered = json.loads(cli(root, "recover").stdout)
    assert recovered["successor"]["invocation_id"] == successor
    assert checkpoint(session)["runtime"]["paused"] is None
    assert checkpoint(session)["runtime"]["next_id"] == saved["runtime"]["next_id"]
    assert not (session / "pause-request.json").exists()


def test_post_activation_currentness_is_observed_not_assumed(work, monkeypatch):
    root, session, request = work
    original = adapter._host
    def advance_after_commit(binary, command, target, value=None, extra=()):
        result = original(binary, command, target, value, extra)
        if command == "managed-correct":
            (root / "source.md").write_text("A later source after the completed activation.\n")
        return result
    monkeypatch.setattr(adapter, "_host", advance_after_commit)
    result = adapter.apply(root, "owner.json", session, "repair-1", 1, request, BINARY)
    assert result["status"] == "activated" and result["source_revision_current"] is False
    assert "Corrected selected scope." in result["successor"]["prompt"]
    recovered = json.loads(cli(root, "recover").stdout)
    assert recovered["source_revision_current"] is False
    assert len(checkpoint(session)["managed"]["corrections"]) == 1
