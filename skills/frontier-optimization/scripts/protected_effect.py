"""Opt-in serialization for a cooperative sender, independent of Batch locks.

The integration owner supplies already adopted scope and a policy callback. This
module does not authenticate user grants, intercept other senders, retire agent
invocations, or make source publication atomic with scope activation.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from contextlib import contextmanager
import copy
import fcntl
import json
import math
import os
from pathlib import Path
import tempfile


class EffectBlocked(RuntimeError):
    pass


class EffectUncertain(RuntimeError):
    pass


def _resources(value):
    result = dict(value)
    for key, amount in result.items():
        if not isinstance(key, str) or not key or isinstance(amount, bool) or not isinstance(amount, (int, float)) or not math.isfinite(amount) or amount < 0:
            raise ValueError("resource reservations must be named, finite, nonnegative numbers")
    return result


class EffectController:
    """Own the narrow activation/send-start boundary for participating sends."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.lock_path = self.path.with_suffix(self.path.suffix + ".lock")

    @contextmanager
    def _locked(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.lock_path.open("a+b") as stream:
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)

    def _read(self):
        if not self.path.exists():
            return {"activation": None, "activations": {}, "requests": {}}
        value = json.loads(self.path.read_text())
        if not isinstance(value, dict) or set(value) != {"activation", "activations", "requests"} or not isinstance(value["requests"], dict) or not isinstance(value["activations"], dict):
            raise EffectBlocked("invalid sender state; reconcile before use")
        return value

    def _write(self, value):
        temporary = None
        try:
            with tempfile.NamedTemporaryFile("w", dir=self.path.parent, delete=False, encoding="utf-8") as stream:
                temporary = stream.name
                json.dump(value, stream, ensure_ascii=False, sort_keys=True, allow_nan=False)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
            temporary = None
            descriptor = os.open(self.path.parent, os.O_RDONLY)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
        finally:
            if temporary is not None:
                Path(temporary).unlink(missing_ok=True)

    def snapshot(self):
        with self._locked():
            return self._read()

    def recover(self, request_id: str, effect: Mapping, *, resources: Mapping):
        """Read one exact completed receipt, without admission, sending or charging.

        Recovery needs no current grant or remaining send capacity. Missing,
        changed, not-sent or uncertain records never fall through to a send.
        """
        if not isinstance(request_id, str) or not request_id:
            raise ValueError("request identity is required")
        prepared = copy.deepcopy(dict(effect))
        reservation = _resources(resources)
        json.dumps(prepared, allow_nan=False)
        with self._locked():
            prior = self._read()["requests"].get(request_id)
            if prior is None:
                raise EffectBlocked("no retained receipt exists for this request identity")
            if prior["effect"] != prepared or prior["resources"] != reservation:
                raise EffectBlocked("request identity already names different parameters")
            if prior["status"] == "uncertain":
                raise EffectUncertain("request outcome is uncertain; reconcile it without resending")
            if prior["status"] != "completed":
                raise EffectBlocked("request has no completed receipt to recover")
            return {"request_id": request_id, "reused": True, "record": copy.deepcopy(prior)}

    def activate(self, activation_id: str, scope: Mapping, *, expected_activation=None):
        """Accept an owner's scope change without waiting for a Batch consumer.

        A repeated identical activation recovers a lost acknowledgement. A new
        activation compares the previous identity, preventing stale overwrites.
        Scope activation stops future affected sends; invocation retirement and
        settlement of already sent requests remain separate owner operations.
        """
        if not isinstance(activation_id, str) or not activation_id:
            raise ValueError("activation identity is required")
        incoming = {"id": activation_id, "scope": copy.deepcopy(dict(scope))}
        with self._locked():
            state = self._read()
            current = state["activation"]
            if current and current["id"] == activation_id:
                if current != incoming:
                    raise EffectBlocked("activation identity already names different scope")
                return current
            if activation_id in state["activations"]:
                raise EffectBlocked("activation was superseded; use a new identity for a newly adopted change")
            if (current["id"] if current else None) != expected_activation:
                raise EffectBlocked("scope changed; reconcile the current activation")
            state["activation"] = incoming
            state["activations"][activation_id] = copy.deepcopy(incoming)
            self._write(state)
            return incoming

    def send(self, request_id: str, effect: Mapping, *, resources: Mapping, admit: Callable,
             start: Callable, finish: Callable, prepare: Callable | None = None):
        """Check and start exactly one request; wait outside the scope lock.

        Optional prepare() runs after a preliminary check and outside the lock;
        its effects require their own coverage. Admission is checked again after
        preparation. start(effect) must send that exact prepared request and return a handle
        without waiting for the remote response. finish(handle) waits and returns
        a JSON result. Neither callback may send another protected request. A
        timeout, crash, or lost acknowledgement keeps the original identity and
        reservation; recovery never automatically sends it again. The returned
        receipt distinguishes a new send from reuse so callers do not charge or
        report the same consequence twice.
        """
        if not isinstance(request_id, str) or not request_id:
            raise ValueError("request identity is required")
        prepared = copy.deepcopy(dict(effect))
        reservation = _resources(resources)
        # Reject nonserializable descriptions before admission or any side effect.
        json.dumps(prepared, allow_nan=False)
        def check(state):
            prior = state["requests"].get(request_id)
            if prior:
                if prior["effect"] != prepared or prior["resources"] != reservation:
                    raise EffectBlocked("request identity already names different parameters")
                if prior["status"] == "completed":
                    return prior
                raise EffectUncertain("request already admitted; inspect or reconcile it without resending")
            if state["activation"] is None:
                raise EffectBlocked("no scope has been activated by the integration owner")
            cumulative = {}
            for item in state["requests"].values():
                for key, amount in item.get("charge", item["resources"]).items():
                    cumulative[key] = cumulative.get(key, 0) + amount
            admit(copy.deepcopy(state["activation"]["scope"]), copy.deepcopy(prepared), cumulative)
            return None

        if prepare is not None:
            with self._locked():
                prior = check(self._read())
                if prior:
                    return {"result": copy.deepcopy(prior["result"]), "reused": True, "request_id": request_id}
            prepare()
        with self._locked():
            state = self._read()
            prior = check(state)
            if prior:
                return {"result": copy.deepcopy(prior["result"]), "reused": True, "request_id": request_id}
            record = {"effect": prepared, "resources": reservation, "status": "uncertain",
                      "activation": state["activation"]["id"]}
            state["requests"][request_id] = record
            self._write(state)
            # Admission is durable before send-start. Even a start exception may
            # mean the peer received bytes, so do not refund or retry automatically.
            handle = start(prepared)
        result = finish(handle)
        json.dumps(result, allow_nan=False)
        with self._locked():
            state = self._read()
            record = state["requests"][request_id]
            if record["status"] != "uncertain":
                raise EffectUncertain("request was reconciled while a response was pending; inspect both outcomes")
            record.update(status="completed", result=copy.deepcopy(result))
            self._write(state)
        return {"result": result, "reused": False, "request_id": request_id}

    def reconcile(self, request_id: str, *, status: str, evidence: str, result=None,
                  resource_use=None):
        """Record observed settlement; never resume or replay an admitted send."""
        if status not in {"completed", "not_sent"} or not evidence.strip():
            raise ValueError("settlement requires an observed status and evidence")
        charge = _resources(resource_use) if resource_use is not None else None
        if status == "not_sent" and (charge is None or any(charge.values())):
            raise ValueError("not_sent settlement requires explicitly observed zero resource use")
        with self._locked():
            state = self._read()
            record = state["requests"][request_id]
            if record["status"] != "uncertain":
                raise EffectBlocked("only an uncertain request can be reconciled")
            record.update(status=status, evidence=evidence, result=result)
            if charge is not None:
                record["charge"] = charge
            self._write(state)
