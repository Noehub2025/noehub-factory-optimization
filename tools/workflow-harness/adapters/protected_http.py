"""Optional cooperative HTTP sender with a separate scope activation boundary.

Scope files are the integration owner's projection of an adopted user decision,
not authentication or grants. This entry sends one fully resolved HTTP request;
it follows no redirects, starts no descendants, and retries no admitted request.
"""
from __future__ import annotations

import argparse
from dataclasses import replace
import hashlib
import http.client
import json
import math
from pathlib import Path
import sys
import socket
import threading
import time
from urllib.parse import urlsplit

REPOSITORY = Path(__file__).resolve().parents[3]
SKILL_SCRIPTS = next((REPOSITORY / directory / "frontier-optimization/scripts"
    for directory in ("skills", ".agents/skills", ".claude/skills")
    if (REPOSITORY / directory / "frontier-optimization/scripts").is_dir()), None)
if SKILL_SCRIPTS is None:
    raise RuntimeError("Install the complete Frontier Skill before using this adapter")
if "frontier_batch" not in sys.modules:
    sys.path.insert(0, str(SKILL_SCRIPTS))
from frontier_batch import (Action, Consequence, GitReference, OperationBinding,
                            OperationResult, PermissionAssessment)
from protected_effect import EffectBlocked, EffectController


def load_request(path: Path) -> dict:
    """Resolve body bytes once; later checks and sending never reload this file."""
    raw = json.loads(path.read_text())
    if set(raw) - {"url", "method", "headers", "body_file", "timeout_seconds", "max_response_bytes"}:
        raise ValueError("unsupported HTTP request field")
    body = (path.parent / raw["body_file"]).read_bytes() if raw.get("body_file") else b""
    return {"url": raw["url"], "method": raw.get("method", "POST"),
            "headers": dict(raw.get("headers", {})), "body_hex": body.hex(),
            "timeout_seconds": raw.get("timeout_seconds", 30),
            "max_response_bytes": raw.get("max_response_bytes", 1048576)}


def resolved_effect(effective: dict) -> dict:
    url = urlsplit(effective["url"])
    if url.scheme not in {"http", "https"} or not url.hostname or url.username or url.password or url.fragment:
        raise ValueError("request requires an HTTP(S) destination without URL credentials or fragment")
    method = effective["method"]
    if not isinstance(method, str) or not method.isalpha() or method != method.upper():
        raise ValueError("HTTP method must be uppercase letters")
    headers = effective["headers"]
    if not isinstance(headers, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in headers.items()):
        raise ValueError("HTTP headers must be strings")
    # The transport, rather than caller headers, owns message framing and Host.
    forbidden = {"host", "content-length", "transfer-encoding", "connection"}
    if forbidden.intersection(k.lower() for k in headers) or any("\r" in k + v or "\n" in k + v for k, v in headers.items()):
        raise ValueError("request headers cannot override framing or contain newlines")
    body = bytes.fromhex(effective["body_hex"])
    timeout = effective["timeout_seconds"]
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("transport timeout must be finite and positive")
    maximum = effective["max_response_bytes"]
    if isinstance(maximum, bool) or not isinstance(maximum, int) or maximum <= 0:
        raise ValueError("response byte allowance must be a positive integer")
    encoded = json.dumps(effective, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return {"url": effective["url"], "method": method,
            "body_sha256": hashlib.sha256(body).hexdigest(), "body_bytes": len(body),
            "request_sha256": hashlib.sha256(encoded).hexdigest()}


def describe_effect(action, context, effective):
    effect = resolved_effect(effective)
    return replace(action, requested_resources={"requests": 1, "body_bytes": effect["body_bytes"]},
                   details={**action.details, **effect})


class ScopeGovernance:
    """Adapter-owned HTTP interpretation; the controller supplies the latest scope."""

    def __init__(self, scope):
        self.scope = scope

    def permission(self, reference, action, actual_consumption):
        scope = self.scope
        covered = (scope.get("enabled") is True and bool(scope.get("authority_reference"))
                   and action.details["url"] in scope.get("destinations", [])
                   and action.details["method"] in scope.get("methods", []))
        return PermissionAssessment(covered, "resolved HTTP request is outside activated scope",
            scope.get("resource_limits", {}), ("external_submission",))


def send(controller: EffectController, request_id: str, effective: dict):
    # Detach resolved values from later caller or file mutations before checking.
    effective = json.loads(json.dumps(effective, allow_nan=False))
    effect = resolved_effect(effective)
    action = describe_effect(Action(request_id, "protected-http", "external",
        required_permissions=("active-scope",), possible_consequences=("external_submission",)), {}, effective)
    connection = None

    def admit(scope, supplied, cumulative):
        assessment = ScopeGovernance(scope).permission(
            GitReference("active-scope", "", str(scope.get("authority_reference", ""))), action, cumulative)
        if not assessment.allows:
            raise EffectBlocked(assessment.reason)
        for key, requested in action.requested_resources.items():
            limit = assessment.resource_limits.get(key)
            if isinstance(limit, bool) or not isinstance(limit, (int, float)) or not math.isfinite(limit) or cumulative.get(key, 0) + requested > limit:
                raise EffectBlocked(f"HTTP scope does not cover cumulative resource use: {key}")
        if supplied != effect:
            raise EffectBlocked("request parameters changed before admission")

    def prepare_connection():
        nonlocal connection
        url = urlsplit(effective["url"])
        transport = http.client.HTTPSConnection if url.scheme == "https" else http.client.HTTPConnection
        connection = transport(url.hostname, url.port, timeout=effective["timeout_seconds"])
        # Connection setup has preliminary scope coverage but no request payload.
        # A withdrawal during this step is seen at final admission.
        connection.connect()

    def start(supplied):
        if resolved_effect(effective) != supplied:
            raise EffectBlocked("request parameters changed after admission")
        url = urlsplit(effective["url"])
        # request() sends headers and body; getresponse() below is the remote wait.
        # The send lock is bounded by the configured timeout and body-byte budget.
        connection.request(effective["method"], (url.path or "/") + ("?" + url.query if url.query else ""),
                           body=bytes.fromhex(effective["body_hex"]), headers=effective["headers"])
        return connection

    def finish(connection):
        # A per-read socket timeout alone permits an endless trickle. Interrupt
        # even header parsing when the response phase exhausts its time allowance.
        started = time.monotonic()
        timed_out = threading.Event()
        transport_socket = connection.sock
        def expire():
            timed_out.set()
            try:
                transport_socket.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
        timer = threading.Timer(effective["timeout_seconds"], expire)
        timer.daemon = True
        timer.start()
        try:
            response = connection.getresponse()
            digest, count = hashlib.sha256(), 0
            while True:
                chunk = response.read1(min(65536, effective["max_response_bytes"] + 1 - count))
                if timed_out.is_set() or time.monotonic() - started >= effective["timeout_seconds"]:
                    raise TimeoutError("HTTP response time allowance exhausted; reconcile the admitted request")
                count += len(chunk)
                if count > effective["max_response_bytes"]:
                    raise ValueError("HTTP response exceeded its byte allowance; reconcile the admitted request")
                if not chunk:
                    if response.length not in (None, 0):
                        raise http.client.IncompleteRead(b"", response.length)
                    break
                digest.update(chunk)
            return {"status": response.status, "response_sha256": digest.hexdigest(), "response_bytes": count}
        except Exception as exc:
            if timed_out.is_set():
                raise TimeoutError("HTTP response time allowance exhausted; reconcile the admitted request") from exc
            raise
        finally:
            timer.cancel()

    try:
        receipt = controller.send(request_id, effect, resources=action.requested_resources,
                                  admit=admit, start=start, finish=finish, prepare=prepare_connection)
        return {**receipt["result"], "reused": receipt["reused"], "request_id": receipt["request_id"]}
    finally:
        if connection is not None:
            connection.close()


def recover(controller: EffectController, request_id: str, effective: dict):
    """Recover historical facts before proposing another protected Batch Action.

    This entry does not call Batch.perform or a transport. An owner may attach
    the returned facts with RecordObservation; that records no new consumption.
    """
    effect = resolved_effect(effective)
    receipt = controller.recover(request_id, effect,
        resources={"requests": 1, "body_bytes": effect["body_bytes"]})
    result = receipt["record"]["result"]
    return {**(result if isinstance(result, dict) else {"settlement_result": result}),
            "reused": True, "request_id": request_id, "original_receipt": receipt["record"]}


def operation_binding(controller: EffectController, load):
    """Connect a selected Batch to the same supported sender used by the CLI."""
    def consume(action, context, effective):
        # Retain an explicit request identity when an owner moves recovery to a
        # different Batch. Otherwise isolate ordinary keys by their owning Batch.
        request_id = action.details.get("request_id", f"{context['batch']}:{action.key}")
        result = send(controller, request_id, effective)
        consequences = () if result["reused"] else (Consequence("external_submission",
            external_reference=action.details["url"], idempotency_key=request_id),)
        return OperationResult("completed", consequences=consequences,
            resource_use={} if result["reused"] else action.requested_resources, result=result)
    return OperationBinding.configured_effect(load, consume, ("external_submission",), describe_effect=describe_effect)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("activate", "send", "recover", "inspect", "reconcile"))
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--scope", type=Path)
    parser.add_argument("--activation")
    parser.add_argument("--expected-activation")
    parser.add_argument("--request", type=Path)
    parser.add_argument("--request-id")
    parser.add_argument("--settlement", type=Path)
    args = parser.parse_args(argv)
    controller = EffectController(args.state)
    try:
        if args.command == "activate":
            if not args.scope or not args.activation:
                parser.error("activate requires --scope and --activation")
            value = controller.activate(args.activation, json.loads(args.scope.read_text()), expected_activation=args.expected_activation)
        elif args.command in {"send", "recover"}:
            if not args.request or not args.request_id:
                parser.error(f"{args.command} requires --request and --request-id")
            operation = send if args.command == "send" else recover
            value = operation(controller, args.request_id, load_request(args.request))
        elif args.command == "reconcile":
            if not args.settlement or not args.request_id:
                parser.error("reconcile requires --settlement and --request-id")
            controller.reconcile(args.request_id, **json.loads(args.settlement.read_text()))
            value = controller.snapshot()["requests"][args.request_id]
        else:
            value = controller.snapshot()
        print(json.dumps(value, sort_keys=True))
    except (OSError, ValueError, RuntimeError, http.client.HTTPException) as exc:
        parser.exit(1, f"{type(exc).__name__}: {exc}\n")


if __name__ == "__main__":
    main()
