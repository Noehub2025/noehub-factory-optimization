"""Optional native context derived from saved owner records, never authority."""

from __future__ import annotations

import fcntl
import json
import os
from pathlib import Path
import re
import tempfile

import yaml


def root_session(explicit: str | None = None) -> str | None:
    session = explicit or os.environ.get("CODEX_SESSION_ID") or os.environ.get("CODEX_THREAD_ID")
    if not session or not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", session):
        return None
    if os.environ.get("CODEX_AGENT_ID"):
        return None
    if explicit is None and os.environ.get("CODEX_THREAD_ID", session) != session:
        return None
    return session


def fingerprint(raw: bytes) -> str:
    """FNV-1a detects changed context bytes; it is not a security certificate."""
    value = 0xCBF29CE484222325
    for byte in raw:
        value = ((value ^ byte) * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
    return f"{value:016x}"


def _read(root: Path, path: Path) -> tuple[dict, bytes]:
    resolved = (root / path).resolve(strict=True)
    if not resolved.is_relative_to(root):
        raise ValueError("owner record is outside the workspace")
    raw = resolved.read_bytes()
    return {"path": str(resolved), "fingerprint": fingerprint(raw)}, raw


def _document(raw: bytes) -> dict:
    text = raw.decode("utf-8")
    if text.startswith("---\n"):
        text = text.split("---\n", 2)[1]
    # Reuse duplicate-key rejection from the reference helper.
    from frontier_references import _document as parse
    return parse(text.encode("utf-8"))


def _snapshot(root: Path, selection: Path, session: str) -> dict:
    source, raw = _read(root, selection)
    current = _document(raw).get("current_state")
    if not isinstance(current, dict) or not current.get("campaign_status"):
        raise ValueError("saved owner needs current_state with campaign_status")
    batch = current.get("primary_batch")
    work_path = current.get("work_record")
    if batch is not None:
        if not isinstance(batch, str) or not re.fullmatch(r"B[0-9]+", batch):
            raise ValueError("invalid selected Batch")
        work_path = f"artifacts/frontier/{batch}/batch.yaml"
    work, work_status = None, None
    if work_path:
        work, work_raw = _read(root, Path(work_path))
        if batch:
            state = _document(work_raw)
            if state.get("batch") != batch:
                raise ValueError("selected Batch does not match its saved work")
            work_status = state.get("current", {}).get("status")
    from current_use import inspect_current_use
    current_use = inspect_current_use(root, str(selection), [work_path] if work_path else [])
    corrections = {"current_use": current_use} if current_use is not None else {}
    return {"kind": "adopted_work", "workspace": str(root), "session_id": session, **corrections,
            "selection": source, "work": work, "current_state": current,
            "work_status": work_status, "mode": "observe"}


def _publish(path: Path, value: dict) -> None:
    with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        try:
            json.dump(value, stream, ensure_ascii=False, allow_nan=False)
            stream.flush()
            os.fsync(stream.fileno())
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)


def register_adopted_work(root: Path, selection: Path, session_id: str | None = None,
                          *, expected_binding: dict | None = None) -> bool:
    """Read adoption from its owner; proposals cannot publish this pointer."""
    # Required finding retention is independent of optional native pointers.
    # An open finding may be presented during preparation, but not consumed.
    from current_use import inspect_current_use
    root = root.resolve()
    inspect_current_use(root, str(selection))
    session = root_session(session_id)
    if session is None:
        return False
    directory = root / ".frontier/hook-context"
    directory.mkdir(parents=True, exist_ok=True)
    pointer = directory / f"{session}.json"
    with (directory / f"{session}.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if expected_binding is not None and json.loads(pointer.read_text()) != expected_binding:
            return False
        value = _snapshot(root, selection, session)
        if pointer.exists():
            previous = json.loads(pointer.read_text())
            previous_use = previous.get("current_use")
            if previous_use and previous_use["owner"] != value["selection"]["path"]:
                from current_use import inspect_current_use
                actual = [value["work"]["path"]] if value["work"] else []
                value["current_use"] = inspect_current_use(root, value["selection"]["path"], actual,
                                                          previous_owner=previous_use["owner"])
        for ref in (value["selection"], value["work"]):
            if ref and _read(root, Path(ref["path"]))[0] != ref:
                raise ValueError("owner changed during registration; refresh from current work")
        _publish(pointer, value)
    return True


def refresh_active_work(path: Path) -> None:
    """Refresh only this root's registered work after an ordinary Batch write."""
    session = root_session()
    if session is None:
        return
    # Batch writes can use an explicit state path; find the participating root.
    root = next((p for p in path.resolve().parents if (p / ".git").exists()), None)
    if root is None:
        return
    pointer = root / ".frontier/hook-context" / f"{session}.json"
    try:
        binding = json.loads(pointer.read_text())
        if not isinstance(binding, dict):
            raise ValueError("optional context is not an object")
        if binding.get("kind") != "adopted_work":
            return
        if not isinstance(binding.get("work"), dict) or not isinstance(binding.get("selection"), dict):
            raise ValueError("optional context has no valid work or Selection reference")
        if binding["work"].get("path") != str(path.resolve()):
            return
        register_adopted_work(root, Path(binding["selection"]["path"]),
                              expected_binding=binding)
    except (OSError, ValueError, KeyError, TypeError, yaml.YAMLError) as exc:
        # The Batch write has succeeded; context failure cannot undo it.
        import sys
        print(f"Optional adopted-work context is stale or unavailable: {exc}", file=sys.stderr)


def bind_dispatch_return(root: Path, result: Path, call: str, session_id: str | None = None) -> dict:
    """Link an existing result to the original actual invocation, even if work moved on."""
    session = root_session(session_id)
    if session is None or not re.fullmatch(r"[A-Za-z0-9_-]{1,200}", call):
        raise ValueError("return binding needs a root session and actual tool_use_id")
    root = root.resolve()
    ref, raw = _read(root, result)
    body = json.loads(raw)
    if not isinstance(body, dict):
        raise ValueError("existing result must be a JSON object")
    attempt = root / ".frontier/hook-context" / f"{session}-call-{call}.json"
    observed = json.loads(attempt.read_bytes())
    if not isinstance(observed, dict) or observed.get("session_id") != session or observed.get("tool_use_id") != call:
        raise ValueError("return does not match retained invocation")
    post = attempt.with_name(attempt.stem + "-post.json")
    response = json.loads(post.read_bytes()) if post.exists() else {}
    if post.exists() and (not isinstance(response, dict) or response.get("session_id") != session
                          or response.get("tool_use_id") != call or response.get("attempt") != str(attempt)
                          or response.get("status") not in {"confirmed_dispatch", "failed", "uncertain"}):
        raise ValueError("response does not match retained invocation")
    body["dispatch_reference"] = {"tool_use_id": call, "attempt": str(attempt),
                                  "response": str(post) if post.exists() else None,
                                  "dispatch_status": response.get("status", "attempted_dispatch")}
    # This association is authored at the existing return; it is not proof of completion.
    if _read(root, result)[0] != ref:
        raise ValueError("result changed during return binding")
    _publish(Path(ref["path"]), body)
    return body
