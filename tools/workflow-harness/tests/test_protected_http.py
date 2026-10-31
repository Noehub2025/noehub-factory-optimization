"""Exercise the maintained HTTP receiver against a local server only."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import http.client as client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import json
from pathlib import Path
import sys
import subprocess
import threading

import pytest

# Respect an explicitly selected complete Skill installation during preinstall tests.
try:
    import frontier_batch
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "skills/frontier-optimization/scripts"))
    import frontier_batch

spec = importlib.util.spec_from_file_location("protected_http", Path(__file__).resolve().parents[1] / "adapters/protected_http.py")
http = importlib.util.module_from_spec(spec)
spec.loader.exec_module(http)
from protected_effect import EffectBlocked, EffectController, EffectUncertain


@pytest.fixture
def server():
    received, waiting, release = [], threading.Event(), threading.Event()
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            received.append(self.rfile.read(int(self.headers["Content-Length"])))
            waiting.set()
            assert release.wait(5)
            self.send_response(204)
            self.end_headers()
        def log_message(self, *args):
            pass
    instance = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=instance.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{instance.server_port}/feedback", received, waiting, release
    release.set()
    instance.shutdown()
    instance.server_close()
    thread.join(5)


def sender_case(tmp_path, url):
    controller = EffectController(tmp_path / "sender.json")
    scope = {"enabled": True, "authority_reference": "test-owned-decision", "destinations": [url],
             "methods": ["POST"], "resource_limits": {"requests": 2, "body_bytes": 100}}
    controller.activate("grant", scope)
    (tmp_path / "body.txt").write_text("selected bytes")
    request = tmp_path / "request.json"
    request.write_text(json.dumps({"url": url, "body_file": "body.txt", "timeout_seconds": 2}))
    return controller, scope, http.load_request(request)


def test_real_receiver_consumes_resolved_bytes_and_withdrawal_does_not_wait(tmp_path, server):
    url, received, waiting, release = server
    controller, scope, effective = sender_case(tmp_path, url)
    (tmp_path / "body.txt").write_text("changed file must not be reloaded")
    with ThreadPoolExecutor() as executor:
        future = executor.submit(http.send, controller, "first", effective)
        assert waiting.wait(5)
        controller.activate("withdrawn", {**scope, "enabled": False}, expected_activation="grant")
        with pytest.raises(EffectBlocked):
            http.send(controller, "second", effective)
        release.set()
        assert future.result(timeout=5)["status"] == 204
    assert received == [b"selected bytes"]
    assert http.send(controller, "first", effective)["reused"] is True
    assert received == [b"selected bytes"]
    # Direct clients do not participate in this controller and remain uncovered.
    direct = client.HTTPConnection("127.0.0.1", int(url.split(":")[2].split("/")[0]), timeout=2)
    direct.request("POST", "/feedback", body=b"unmediated")
    assert direct.getresponse().status == 204
    direct.close()
    assert received[-1] == b"unmediated"
    assert len(controller.snapshot()["requests"]) == 1


def test_withdrawal_after_connection_preparation_sends_no_request(tmp_path, server, monkeypatch):
    url, received, waiting, release = server
    controller, scope, effective = sender_case(tmp_path, url)
    connected, continue_connect = threading.Event(), threading.Event()
    base = client.HTTPConnection
    class Connection(base):
        def connect(self):
            super().connect()
            connected.set()
            assert continue_connect.wait(5)
    monkeypatch.setattr(http.http.client, "HTTPConnection", Connection)
    with ThreadPoolExecutor() as executor:
        future = executor.submit(http.send, controller, "first", effective)
        assert connected.wait(5)
        controller.activate("withdrawn", {**scope, "enabled": False}, expected_activation="grant")
        continue_connect.set()
        with pytest.raises(EffectBlocked):
            future.result(timeout=5)
    assert received == []
    assert controller.snapshot()["requests"] == {}


def test_actual_batch_binding_uses_final_target_and_consumes_same_bytes(tmp_path, server):
    url, received, waiting, release = server
    controller, scope, effective = sender_case(tmp_path, url)
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / "decision.md").write_text("Local receiver test is authorized for this isolated test.\n")
    subprocess.run(["git", "-C", str(tmp_path), "add", "decision.md"], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "-c", "user.name=Workflow test", "-c", "user.email=workflow@example.invalid", "commit", "-qm", "test decision"], check=True)
    commit = subprocess.check_output(["git", "-C", str(tmp_path), "rev-parse", "HEAD"], text=True).strip()
    batch = frontier_batch.Batch.open(tmp_path, "B999", governance=http.ScopeGovernance(scope),
        operations={"http": http.operation_binding(controller, lambda a, c: effective)})
    # This retained reference is intentionally opaque to this adapter-owned resolver.
    batch.apply(frontier_batch.DefineBatch("Inspect feedback", "Receive selected response", ("local test",),
        permissions=(frontier_batch.GitReference("V001", commit, "decision.md"),),
        resource_limits={"requests": 2, "body_bytes": 100}, expected_consequences=("external_submission",)))
    action = frontier_batch.Action("send", "http", "external", required_permissions=("V001",),
        possible_consequences=("external_submission",), repeatable=True, details={"url": url, "method": "POST"})
    effective["url"] = url + "/different"
    with pytest.raises(frontier_batch.ConsequenceBlocked, match="outside activated scope"):
        batch.perform(action)
    assert received == []
    effective["url"] = url
    with ThreadPoolExecutor() as executor:
        future = executor.submit(batch.perform, action)
        assert waiting.wait(5)
        # Batch.perform still owns its long consumer lock here. Scope activation
        # uses another lock and therefore does not wait for this response.
        controller.activate("withdrawn", {**scope, "enabled": False}, expected_activation="grant")
        release.set()
        outcome = future.result(timeout=5)
    assert outcome.operation_result.result["status"] == 204
    assert outcome.view.latest_attempt["action"]["details"]["body_sha256"]
    again = batch.perform(action)
    assert again.operation_result.result["reused"] is True
    assert again.operation_result.consequences == ()
    assert again.view.remaining_capacity["requests"] == 1
    fresh = frontier_batch.Batch.open(tmp_path, "B1000", governance=http.ScopeGovernance(scope),
        operations={"http": http.operation_binding(controller, lambda a, c: effective)})
    fresh.apply(frontier_batch.DefineBatch("Recover receipt", "Retain known response", ("local test",),
        permissions=(frontier_batch.GitReference("V001", commit, "decision.md"),),
        resource_limits={"requests": 2, "body_bytes": 100}, expected_consequences=("external_submission",)))
    recovered = fresh.perform(replace(action, details={**action.details, "request_id": "B999:send"}))
    assert recovered.operation_result.result["reused"] is True
    assert recovered.operation_result.consequences == ()
    assert recovered.view.remaining_capacity["requests"] == 2
    assert received == [b"selected bytes"]


def test_lost_http_response_retains_identity_and_never_retries(tmp_path, server):
    url, received, waiting, release = server
    controller, scope, effective = sender_case(tmp_path, url)
    effective["timeout_seconds"] = 0.1
    with pytest.raises(TimeoutError):
        http.send(controller, "uncertain", effective)
    assert received == [b"selected bytes"]
    assert controller.snapshot()["requests"]["uncertain"]["status"] == "uncertain"
    with pytest.raises(EffectUncertain):
        http.send(EffectController(controller.path), "uncertain", effective)
    assert received == [b"selected bytes"]
    release.set()


def test_oversized_response_keeps_admitted_request_uncertain(tmp_path):
    received = []
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            received.append(self.rfile.read(int(self.headers["Content-Length"])))
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"response exceeds allowance")
        def log_message(self, *args):
            pass
    instance = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=instance.serve_forever, daemon=True)
    thread.start()
    try:
        controller, scope, effective = sender_case(tmp_path, f"http://127.0.0.1:{instance.server_port}/feedback")
        effective["max_response_bytes"] = 4
        with pytest.raises(ValueError, match="byte allowance"):
            http.send(controller, "oversized", effective)
        assert controller.snapshot()["requests"]["oversized"]["status"] == "uncertain"
        with pytest.raises(EffectUncertain):
            http.send(controller, "oversized", effective)
        assert received == [b"selected bytes"]
    finally:
        instance.shutdown()
        instance.server_close()
        thread.join(5)


@pytest.mark.parametrize("unavailable_send", ["withdrawn", "exhausted"])
def test_receipt_only_recovery_works_without_new_batch_admission(tmp_path, monkeypatch, capsys, unavailable_send):
    url = "http://127.0.0.1:1/no-network"
    controller, scope, effective = sender_case(tmp_path, url)
    effect = http.resolved_effect(effective)
    controller.send("original:send", effect, resources={"requests": 1, "body_bytes": effect["body_bytes"]},
        admit=lambda *args: None, start=lambda effect: None,
        finish=lambda handle: {"status": 204, "response_sha256": "retained", "response_bytes": 0})
    if unavailable_send == "withdrawn":
        scope = {**scope, "enabled": False}
        controller.activate("withdrawn", scope, expected_activation="grant")
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / "decision.md").write_text("Historical receipt test.\n")
    subprocess.run(["git", "-C", str(tmp_path), "add", "decision.md"], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "-c", "user.name=Workflow test", "-c", "user.email=workflow@example.invalid", "commit", "-qm", "test decision"], check=True)
    commit = subprocess.check_output(["git", "-C", str(tmp_path), "rev-parse", "HEAD"], text=True).strip()
    batch = frontier_batch.Batch.open(tmp_path, "B2000", governance=http.ScopeGovernance(scope),
        operations={"http": http.operation_binding(controller, lambda a, c: effective)})
    batch.apply(frontier_batch.DefineBatch("Recover receipt", "Retain facts", ("local read",),
        permissions=(frontier_batch.GitReference("V001", commit, "decision.md"),),
        resource_limits={"requests": 0 if unavailable_send == "exhausted" else 1, "body_bytes": 100},
        expected_consequences=("external_submission",)))
    action = frontier_batch.Action("send", "http", "external", required_permissions=("V001",),
        possible_consequences=("external_submission",),
        details={"url": url, "method": "POST", "request_id": "original:send"})
    with pytest.raises(frontier_batch.ConsequenceBlocked):
        batch.perform(action)
    before = controller.snapshot()
    monkeypatch.setattr(http, "send", lambda *args: pytest.fail("receipt recovery must never enter send"))
    recovered = http.recover(controller, "original:send", effective)
    assert recovered["reused"] is True and recovered["status"] == 204
    batch.apply(frontier_batch.RecordObservation("original-receipt", recovered))
    assert batch.view.export_record()["attempts"] == []
    assert batch.view.export_record()["consumption"] == {}
    http.main(["recover", "--state", str(controller.path), "--request", str(tmp_path / "request.json"),
               "--request-id", "original:send"])
    assert json.loads(capsys.readouterr().out)["original_receipt"]["activation"] == "grant"
    assert controller.snapshot() == before


def test_receipt_only_recovery_rejects_missing_changed_and_unsettled_requests(tmp_path, monkeypatch):
    controller, scope, effective = sender_case(tmp_path, "http://127.0.0.1:1/no-network")
    effect = http.resolved_effect(effective)
    resources = {"requests": 1, "body_bytes": effect["body_bytes"]}
    with pytest.raises(TimeoutError):
        controller.send("unsettled", effect, resources=resources, admit=lambda *args: None,
            start=lambda e: None, finish=lambda h: (_ for _ in ()).throw(TimeoutError("lost")))
    monkeypatch.setattr(http, "send", lambda *args: pytest.fail("recovery cannot fall through to sending"))
    with pytest.raises(EffectBlocked, match="no retained receipt"):
        http.recover(controller, "missing", effective)
    with pytest.raises(EffectBlocked, match="different parameters"):
        http.recover(controller, "unsettled", {**effective, "headers": {"X-Changed": "yes"}})
    with pytest.raises(EffectUncertain, match="uncertain"):
        http.recover(controller, "unsettled", effective)
    controller.reconcile("unsettled", status="not_sent", evidence="Observed local failure before send", resource_use={})
    with pytest.raises(EffectBlocked, match="no completed receipt"):
        http.recover(controller, "unsettled", effective)
