"""Checks only the cooperative sender boundary, not arbitrary process effects."""
from concurrent.futures import ThreadPoolExecutor
import threading

import pytest
from protected_effect import EffectBlocked, EffectController, EffectUncertain


def policy(scope, effect, cumulative):
    if not scope["enabled"] or effect["target"] not in scope["targets"]:
        raise EffectBlocked("outside scope")
    if cumulative.get("requests", 0) + 1 > scope["limit"]:
        raise EffectBlocked("cumulative limit")


def enabled(limit=2):
    return {"enabled": True, "targets": ["private"], "limit": limit}


def send(controller, name, start=lambda effect: "started", finish=lambda handle: {"observed": True}, prepare=None):
    return controller.send(name, {"target": "private"}, resources={"requests": 1},
                           admit=policy, start=start, finish=finish, prepare=prepare)["result"]


def test_withdrawal_during_preparation_and_wait_has_no_batch_lock_dependency(tmp_path):
    controller = EffectController(tmp_path / "sender.json")
    controller.activate("grant", enabled())
    preparing, resume = threading.Event(), threading.Event()
    sent = []
    def prepare():
        preparing.set()
        assert resume.wait(5)
    with ThreadPoolExecutor() as executor:
        future = executor.submit(send, controller, "first", lambda e: sent.append(e), prepare=prepare)
        assert preparing.wait(5)
        controller.activate("withdrawn", {**enabled(), "enabled": False}, expected_activation="grant")
        resume.set()
        with pytest.raises(EffectBlocked, match="outside scope"):
            future.result(timeout=5)
    assert sent == []
    assert controller.snapshot()["requests"] == {}

    controller.activate("grant-again", enabled(), expected_activation="withdrawn")
    waiting, finish_now = threading.Event(), threading.Event()
    def finish(handle):
        waiting.set()
        assert finish_now.wait(5)
        return {"observed": True}
    with ThreadPoolExecutor() as executor:
        future = executor.submit(send, controller, "second", lambda e: sent.append(e), finish)
        assert waiting.wait(5)
        controller.activate("stop-future", {**enabled(), "enabled": False}, expected_activation="grant-again")
        with pytest.raises(EffectBlocked):
            send(controller, "third", lambda e: sent.append(e))
        finish_now.set()
        assert future.result(timeout=5) == {"observed": True}
    assert len(sent) == 1
    assert controller.snapshot()["requests"]["second"]["activation"] == "grant-again"


def test_lost_ack_recovery_never_replays_and_preserves_reserved_capacity(tmp_path):
    controller = EffectController(tmp_path / "sender.json")
    controller.activate("grant", enabled(1))
    sent = []
    def lost_ack(handle):
        raise TimeoutError("response unavailable")
    with pytest.raises(TimeoutError):
        send(controller, "request", lambda e: sent.append(e), lost_ack)
    recovered = EffectController(controller.path)
    assert recovered.activate("grant", enabled(1))["id"] == "grant"
    with pytest.raises(EffectUncertain):
        send(recovered, "request", lambda e: sent.append(e))
    with pytest.raises(EffectBlocked, match="cumulative"):
        send(recovered, "another", lambda e: sent.append(e))
    assert len(sent) == 1
    recovered.reconcile("request", status="completed", evidence="Observed server receipt", result={"receipt": "r1"})
    assert send(recovered, "request", lambda e: pytest.fail("must not resend")) == {"receipt": "r1"}
    with pytest.raises(EffectBlocked, match="cumulative"):
        send(recovered, "another")


def test_stale_scope_and_request_id_cannot_overwrite_current_state(tmp_path):
    controller = EffectController(tmp_path / "sender.json")
    controller.activate("grant", enabled())
    send(controller, "sent")
    with pytest.raises(EffectBlocked, match="different parameters"):
        controller.send("sent", {"target": "public"}, resources={"requests": 1},
                        admit=policy, start=lambda e: None, finish=lambda h: {})
    controller.activate("deny", {**enabled(), "enabled": False}, expected_activation="grant")
    with pytest.raises(EffectBlocked, match="scope changed"):
        controller.activate("stale-grant", enabled(), expected_activation="grant")
    with pytest.raises(EffectBlocked, match="superseded"):
        controller.activate("grant", enabled(), expected_activation="deny")
    with pytest.raises(EffectBlocked, match="different scope"):
        controller.activate("deny", enabled())
