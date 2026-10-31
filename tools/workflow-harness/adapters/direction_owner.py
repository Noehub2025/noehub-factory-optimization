"""Prepare and deliver current owner context to an explicit stdin consumer.

This optional normal entry controls the exact request and local subprocess. It
neither sandboxes the receiver nor authorizes its effects. A retained response
is not an adopted research conclusion. Interrupted sends are never replayed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import selectors
import signal
import subprocess
import sys
import tempfile
import time
import uuid

REPOSITORY = Path(__file__).resolve().parents[3]
SKILL_SCRIPTS = next((REPOSITORY / directory / "frontier-optimization/scripts"
                     for directory in ("skills", ".agents/skills", ".claude/skills")
                     if (REPOSITORY / directory / "frontier-optimization/scripts").is_dir()), None)
if SKILL_SCRIPTS is None:
    raise RuntimeError("Install the complete Frontier Skill before using this adapter")
sys.path.insert(0, str(SKILL_SCRIPTS))
from context_delivery import consume_request, model_view
from frontier_references import _document, prepare_adoption_context


def save(path: Path, value: dict) -> None:
    """Replace one small receipt durably; do not promise cross-file atomicity."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, mode="w", delete=False) as stream:
        temporary = Path(stream.name)
        try:
            json.dump(value, stream, ensure_ascii=False, allow_nan=False, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
            os.replace(temporary, path)
            directory = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        finally:
            temporary.unlink(missing_ok=True)


def prepare(root: Path, owner: str, *, assignment=None, sources=(), controlling_source=None,
            event="direction") -> dict:
    """Default direction entry supplies owner-maintained material internally."""
    view = prepare_adoption_context(root, owner, assignment=assignment, task_sources=sources,
                                    controlling_source=controlling_source, phase="direction_dispatch",
                                    material_event=event)
    return model_view(root, view)


def _location(root: Path, invocation: str) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,99}", invocation):
        raise ValueError("invocation must be a short filename-safe identifier")
    return root / "artifacts/workflow-harness/direction-calls" / invocation


def recover(root: Path, invocation: str) -> dict:
    """Return saved facts only. No completed or uncertain invocation is replayed."""
    location = _location(root, invocation)
    path = location / "receipt.json"
    if not path.exists():
        if location.exists():
            return {"invocation": invocation, "status": "uncertain", "reason": "Interrupted before a complete receipt; inspect retained files. No replay was attempted."}
        raise ValueError("invocation was not found")
    result = _document(path.read_bytes())
    if result["status"] == "started":
        result = {**result, "status": "uncertain", "reason": "No completed receipt; the receiver may have run or remain active. Reconcile before any new invocation."}
    for key in ("request", "stdout", "stderr"):
        item = result.get(key)
        if item and item.get("sha256"):
            path = root / item["path"]
            if hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
                raise ValueError(f"retained {key} changed")
    return result


def send(root: Path, prepared: dict, command: list[str], *, invocation=None,
         timeout_seconds=300.0, max_output_bytes=2_000_000) -> dict:
    """Verify then send exactly the rendered UTF-8 bytes to a chosen consumer."""
    root = root.resolve()
    if not command or any(not isinstance(item, str) or not item for item in command):
        raise ValueError("supply an explicit command argument list")
    if not math.isfinite(timeout_seconds) or timeout_seconds <= 0 or type(max_output_bytes) is not int or max_output_bytes < 1:
        raise ValueError("timeout and output allowance must be positive")
    request = consume_request(root, prepared).encode("utf-8")
    invocation = invocation or uuid.uuid4().hex
    location = _location(root, invocation)
    # Exclusive creation also serializes duplicate sends. A crash at any later
    # point leaves this identity reserved, even without a receipt.
    location.mkdir(parents=True, exist_ok=False)
    request_path = location / "request.txt"
    with request_path.open("xb") as stream:
        stream.write(request)
        stream.flush()
        os.fsync(stream.fileno())
    save(location / "prepared.json", prepared)
    def locator(path, body):
        return {"path": path.relative_to(root).as_posix(), "sha256": hashlib.sha256(body).hexdigest(), "bytes": len(body)}
    receipt = {"invocation": invocation, "status": "started", "command": command,
               "delivery_identity": prepared["delivery_identity"], "request": locator(request_path, request),
               "timeout_seconds": timeout_seconds, "max_output_bytes": max_output_bytes,
               "coverage": "Exact stdin to this subprocess only; no receiver sandbox, semantic adoption, external-effect authorization or automatic replay."}
    save(location / "receipt.json", receipt)
    # Check again after local persistence. Uncoordinated source edits after this
    # check are outside this entry's serialization boundary; outgoing bytes stay
    # exact and recoverable. Participating host corrections use their own entry.
    if consume_request(root, prepared).encode("utf-8") != request:
        raise ValueError("request changed before process start")
    process = None
    buffers = {"stdout": bytearray(), "stderr": bytearray()}
    started = time.monotonic()
    try:
        # Send the checked in-memory bytes from a private file descriptor, not
        # from the named audit copy that another process could replace.
        with tempfile.TemporaryFile(mode="w+b") as incoming:
            incoming.write(request)
            incoming.seek(0)
            process = subprocess.Popen(command, cwd=root, stdin=incoming,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
        receipt["pid"] = process.pid
        save(location / "receipt.json", receipt)
        with selectors.DefaultSelector() as selector:
            for key in buffers:
                pipe = getattr(process, key)
                os.set_blocking(pipe.fileno(), False)
                selector.register(pipe, selectors.EVENT_READ, key)
            while selector.get_map():
                left = timeout_seconds - (time.monotonic() - started)
                if left <= 0:
                    raise TimeoutError("receiver exceeded its time allowance")
                for selected, _ in selector.select(min(left, 0.1)):
                    chunk = os.read(selected.fd, 65536)
                    if not chunk:
                        selector.unregister(selected.fileobj)
                        selected.fileobj.close()
                        continue
                    remaining = max_output_bytes - sum(map(len, buffers.values()))
                    buffers[selected.data].extend(chunk[:remaining])
                    if len(chunk) > remaining:
                        receipt["output_truncated"] = True
                        raise ValueError("receiver exceeded its output allowance")
            process.wait(timeout=max(.001, timeout_seconds - (time.monotonic() - started)))
        receipt["returncode"] = process.returncode
        receipt["status"] = "completed" if process.returncode == 0 else "uncertain"
        if process.returncode:
            receipt["reason"] = "Receiver exited unsuccessfully; do not infer absence of effects or replay."
    except BaseException as exc:
        if process is not None:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
        receipt.update(status="uncertain", reason=str(exc))
        if not isinstance(exc, Exception):
            raise
    finally:
        receipt["elapsed_seconds"] = time.monotonic() - started
        for key, content in buffers.items():
            path = location / (key + ".bin")
            with path.open("wb") as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            receipt[key] = locator(path, content)
        save(location / "receipt.json", receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("prepare", "run", "send", "recover"))
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--owner")
    parser.add_argument("--assignment")
    parser.add_argument("--source", action="append", default=[])
    parser.add_argument("--controlling-source")
    parser.add_argument("--event", choices=("direction", "scope", "design", "continuation"), default="direction")
    parser.add_argument("--prepared", type=Path)
    parser.add_argument("--invocation")
    parser.add_argument("--timeout-seconds", type=float, default=300)
    parser.add_argument("--max-output-bytes", type=int, default=2_000_000)
    # The consumer follows --; argparse REMAINDER would swallow normal options.
    arguments = sys.argv[1:]
    split = arguments.index("--") if "--" in arguments else len(arguments)
    args = parser.parse_args(arguments[:split])
    command = arguments[split + 1:]
    try:
        root = args.root.resolve()
        if args.operation == "recover":
            if not args.invocation or command:
                raise ValueError("recover requires --invocation and no command")
            result = recover(root, args.invocation)
        else:
            if args.operation == "send":
                if not args.prepared:
                    raise ValueError("send requires --prepared")
                prepared = _document(args.prepared.read_bytes())
            else:
                if not args.owner:
                    raise ValueError("prepare/run requires --owner")
                prepared = prepare(root, args.owner, assignment=args.assignment, sources=args.source,
                                   controlling_source=args.controlling_source, event=args.event)
            if args.operation == "prepare":
                if command or not args.prepared:
                    raise ValueError("prepare requires --prepared output and no command")
                save(args.prepared, prepared)
                result = {"prepared": str(args.prepared), "delivery_identity": prepared["delivery_identity"]}
            else:
                result = send(root, prepared, command, invocation=args.invocation,
                              timeout_seconds=args.timeout_seconds, max_output_bytes=args.max_output_bytes)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("status") != "uncertain" else 2
    except (ValueError, OSError) as exc:
        print(json.dumps({"status": "not_dispatched_by_this_call", "error": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
