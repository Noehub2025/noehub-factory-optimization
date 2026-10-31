"""Compose owner source adoption and managed invocation replacement.

The retained association lives beside the existing owner's correction receipt.
It is separate from that receipt because progress is not a governing source.
Only the managed Session checkpoint proves activation. This entry never drives
an invocation or retries an action that might already have produced an effect.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

REPOSITORY = Path(__file__).resolve().parents[3]
SKILL_SCRIPTS = next((REPOSITORY / directory / "frontier-optimization/scripts"
                     for directory in ("skills", ".agents/skills", ".claude/skills")
                     if (REPOSITORY / directory / "frontier-optimization/scripts").is_dir()), None)
if SKILL_SCRIPTS is None:
    raise RuntimeError("Install the complete Frontier Skill before using this adapter")
sys.path.insert(0, str(SKILL_SCRIPTS))
from current_use import (_closure, _metadata, _path, _receipt, _relations, _state,
                         adopt_current_work, check_current_use)


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def identity(value: dict) -> str:
    return digest(json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False).encode())


def _journal(root: Path, owner: str, activation: str) -> Path:
    if not isinstance(activation, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", activation):
        raise ValueError("activation needs a nonempty alphanumeric, '-' or '_' identity")
    receipt = _receipt(root, owner)
    return receipt.with_name(f"{receipt.stem}-activation-{activation}.json")


def _publish(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        try:
            json.dump(value, stream, ensure_ascii=False, allow_nan=False)
            stream.flush()
            os.fsync(stream.fileno())
            os.replace(temporary, path)
            descriptor = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
        finally:
            temporary.unlink(missing_ok=True)


@contextmanager
def _locked(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.with_suffix(".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        yield


def _version(root: Path, path: str):
    source = root / path
    return digest(source.read_bytes()) if source.exists() else None


def _checkpoint(root: Path, association: dict) -> dict:
    checkpoint = json.loads((Path(association["session"]) / "state.json").read_text())
    if checkpoint.get("format_version") != 1:
        raise ValueError("unsupported managed Session checkpoint; reconcile through its owner")
    if Path(checkpoint["runtime"]["task"]["workspace"]).resolve() != root:
        raise ValueError("managed Session belongs to a different workspace")
    return checkpoint


def _activation(checkpoint: dict, association: dict) -> dict | None:
    saved = checkpoint.get("managed", {}).get("corrections", {}).get(association["activation_id"])
    correction = association["correction"]
    if saved:
        body, successor = saved
        if json.loads(body) != correction:
            raise ValueError("activation identity has a different managed replacement; reconcile")
        previous = checkpoint["managed"]["invocations"].get(str(correction["expected_invocation"]), {})
        if previous.get("phase") != "retired":
            raise ValueError("activation checkpoint does not retire its predecessor; reconcile")
        request = json.loads((Path(association["session"]) / f"request-{successor}.json").read_text())
        if request.get("invocation_id") != successor:
            raise ValueError("activation checkpoint and saved successor disagree; reconcile")
        active = checkpoint["runtime"].get("outstanding")
        return {"successor": request, "successor_current": bool(active and active["invocation_id"] == successor)}
    active = checkpoint["runtime"].get("outstanding")
    if not active or active["invocation_id"] != correction["expected_invocation"]:
        raise ValueError("expected invocation changed before activation; reconcile without replay")
    if str(correction["expected_invocation"]) not in checkpoint.get("managed", {}).get("invocations", {}):
        raise ValueError("expected invocation is outside managed coverage")
    return None


def _source_adopted(root: Path, owner: str, association: dict) -> bool:
    """Confirm source completion from owner records, never from preparation."""
    request = association["source_request"]
    retained = _state(_receipt(root, owner))
    if retained.get("pending"):
        return False
    metadata = _metadata((root / owner).read_bytes(), owner)
    declared = {item["id"]: item for item in metadata.get("current_use_corrections", [])}
    for proposed in request["corrections"]:
        item = declared.get(proposed["id"])
        observed = retained["records"].get(proposed["id"])
        if item is None or observed is None or observed["status"] != proposed["status"]:
            return False
        if any(item.get(key) != proposed.get(key) for key in ("id", "finding", "effect", "affected_sources", "status")):
            return False
        resolution = item.get("resolution", {})
        if any(resolution.get(key) != proposed["resolution"].get(key) for key in ("reason", "evidence")):
            return False
        if observed.get("resolution") != resolution:
            return False
        expected = {path: version for path, version in association["proposed_sources"].items()
                    if path in _closure(proposed["affected_sources"], association["relations"], successors_only=True)
                    and version is not None}
        if {entry["path"]: entry["sha256"] for entry in resolution.get("replacements", [])} != expected:
            return False
    return all(_version(root, path) == version for path, version in association["proposed_sources"].items())


def _association(root: Path, owner: str, session: Path, activation: str, expected: int, request: dict) -> dict:
    if not isinstance(expected, int) or isinstance(expected, bool) or expected < 1:
        raise ValueError("expected invocation must be a positive integer")
    if set(request) != {"source", "replacement"}:
        raise ValueError("request requires exactly source and replacement")
    source = request["source"]
    if not isinstance(source, dict) or set(source) - {"corrections", "replacements", "relations"}:
        raise ValueError("source request supports corrections, replacements and relations")
    source = {key: source.get(key, []) for key in ("corrections", "replacements", "relations")}
    if not source["corrections"] or not all(isinstance(value, list) for value in source.values()):
        raise ValueError("source request needs owner corrections and list fields")
    metadata = _metadata((root / owner).read_bytes(), owner)
    retained = _state(_receipt(root, owner))
    links = _relations(root, retained.get("relations", []) + metadata.get("current_use_relations", []) + source["relations"])
    roots, dependencies = [], {}
    for item in source["corrections"]:
        if item.get("status") not in {"resolved", "inapplicable"} or not isinstance(item.get("resolution"), dict):
            raise ValueError("source request needs a resolved or inapplicable owner correction")
        roots.extend(_path(root, path) for path in item["affected_sources"])
        for path in (item["finding"], item["resolution"]["evidence"]):
            path = _path(root, path)
            dependencies[path] = _version(root, path)
            if dependencies[path] is None:
                raise ValueError("source adoption evidence is unavailable")
    sources = sorted(_closure(roots, links, successors_only=True))
    before = {path: _version(root, path) for path in sources}
    proposed = dict(before)
    for edit in source["replacements"]:
        path = _path(root, edit["path"])
        if path not in proposed or not isinstance(edit.get("contents"), str):
            raise ValueError("replacement must supply an affected text source")
        proposed[path] = digest(edit["contents"].encode())
    replacement = dict(request["replacement"])
    if set(replacement) - {"assignment", "objective", "constraints", "actual_use"} or not replacement.get("assignment"):
        raise ValueError("replacement needs an assignment and supported queued-work fields")
    actual_use = replacement.get("actual_use") or sources
    replacement = {key: value for key, value in replacement.items() if value is not None}
    replacement["actual_use"] = sorted({str(root / _path(root, path)) for path in actual_use})
    if not replacement["actual_use"]:
        raise ValueError("managed correction requires an actual source-use scope")
    return {"version": 1, "owner": owner, "session": str(session.resolve()), "activation_id": activation,
            "source_request": source, "proposed_sources": proposed,
            "proposed_source_revision": identity(proposed), "before_sources": before,
            "before_owner": _version(root, owner), "dependencies": dependencies, "relations": links,
            "correction": {"correction_id": activation, "expected_invocation": expected, "replacement": replacement}}


def _host(binary: Path, command: str, session: str, value=None, extra=()):
    completed = subprocess.run([str(binary), "host", command, session, *map(str, extra)],
                               input=json.dumps(value) if value is not None else None,
                               text=True, capture_output=True, timeout=30)
    if completed.returncode:
        raise ValueError(f"managed host {command} did not complete: {completed.stderr.strip()}")
    return json.loads(completed.stdout)


def _verify_binding(root: Path, owner: str, association: dict, report: dict) -> None:
    """Match the exact captured bytes, not just a live path or discharged label."""
    binding = report.get("current_use") or {}
    saved = {str(Path(item["path"]).resolve()): item for item in binding.get("files", [])}
    for path, expected in {**association["proposed_sources"], **association["dependencies"]}.items():
        if expected is None:
            continue
        item = saved.get(str(root / path))
        if item is None or "contents" not in item or digest(item["contents"].encode()) != expected:
            raise ValueError("captured source differs from the retained proposal; reconcile before activation")
    if not _source_adopted(root, owner, association):
        raise ValueError("owner adoption changed during binding capture; reconcile before activation")


def _resume(root: Path, owner: str, path: Path, record: dict, binary: Path) -> dict:
    association = record["association"]
    if record.get("identity") != identity(association) or association["owner"] != owner:
        raise ValueError("retained activation association changed; reconcile")
    checkpoint = _checkpoint(root, association)
    activated = _activation(checkpoint, association)
    dependencies_current = all(_version(root, p) == v for p, v in association["dependencies"].items())
    adopted = _source_adopted(root, owner, association)
    if activated:
        # A later source change cannot cause an already activated replacement to run again.
        return {"status": "activated", "activation_id": association["activation_id"], **activated,
                "source_revision_current": adopted and dependencies_current,
                "coverage": "Managed invocation replacement only; no action was dispatched or replayed."}
    if not dependencies_current:
        raise ValueError("source adoption evidence changed; reconcile before activation")
    if not adopted:
        if record.get("source_state") == "adopted":
            raise ValueError("adopted source changed before activation; reconcile")
        pending = _state(_receipt(root, owner)).get("pending")
        if pending:
            if pending["request"] != association["source_request"]:
                raise ValueError("another source adoption is pending; reconcile")
        elif (_version(root, owner) != association["before_owner"] or
              any(_version(root, p) != v for p, v in association["before_sources"].items())):
            raise ValueError("source changed since preparation; reconcile without inferring adoption")
        adopt_current_work(root, owner, **association["source_request"])
        if not _source_adopted(root, owner, association):
            raise ValueError("owner source adoption did not establish the proposed revision")
    if record.get("source_state") != "adopted":
        record = {**record, "source_state": "adopted"}
        _publish(path, record)
    # Install the actual current-use result after source completion. The progress
    # sidecar is deliberately excluded from the governing correction receipt.
    actual_use = association["correction"]["replacement"]["actual_use"]
    report = check_current_use(root, owner, actual_use)
    _verify_binding(root, owner, association, report)
    _activation(_checkpoint(root, association), association)
    try:
        _host(binary, "managed-correct", association["session"],
              {**association["correction"], "current_use": report["current_use"]})
    except (OSError, subprocess.TimeoutExpired, ValueError):
        # A timed-out/lost acknowledgement may follow a committed checkpoint.
        # Read it; do not issue a second mutation in this attempt.
        if not _activation(_checkpoint(root, association), association):
            raise
    activated = _activation(_checkpoint(root, association), association)
    if not activated:
        raise ValueError("source adopted but activation remains pending; recover this same identity")
    return {"status": "activated", "activation_id": association["activation_id"], **activated,
            "source_revision_current": (_source_adopted(root, owner, association) and
                                        all(_version(root, p) == v for p, v in association["dependencies"].items())),
            "coverage": "Managed invocation replacement only; no action was dispatched or replayed."}


def apply(root: Path, owner: str, session: Path, activation: str, expected: int, request: dict, binary: Path) -> dict:
    root = root.resolve()
    owner = _path(root, owner)
    path = _journal(root, owner, activation)
    # Serialize participating source adopters for this owner across activation IDs.
    # The managed host separately owns its short admission/checkpoint boundary.
    with _locked(path.with_name(_receipt(root, owner).stem + "-activations")):
        if path.exists():
            record = json.loads(path.read_text())
            retained = record["association"]
            # Repeated apply may follow source adoption; compare request identity,
            # not a new before-version snapshot of the already changed source.
            if set(request) != {"source", "replacement"} or set(request["source"]) - {"corrections", "replacements", "relations"}:
                raise ValueError("activation request contains unsupported fields")
            normalized = {key: request["source"].get(key, []) for key in ("corrections", "replacements", "relations")}
            replacement = dict(request["replacement"])
            replacement = {key: value for key, value in replacement.items() if value is not None}
            replacement["actual_use"] = sorted({str(root / _path(root, p)) for p in
                                                (replacement.get("actual_use") or retained["proposed_sources"])})
            if (retained["source_request"] != normalized or retained["session"] != str(session.resolve()) or
                    retained["correction"] != {"correction_id": activation, "expected_invocation": expected,
                                                "replacement": replacement}):
                raise ValueError("activation identity already belongs to a different request")
        else:
            association = _association(root, owner, session, activation, expected, request)
            _activation(_checkpoint(root, association), association)
            record = {"association": association, "identity": identity(association), "source_state": "prepared"}
            _publish(path, record)
        return _resume(root, owner, path, record, binary)


def recover(root: Path, owner: str, activation: str, binary: Path) -> dict:
    root = root.resolve()
    owner = _path(root, owner)
    path = _journal(root, owner, activation)
    # Serialize participating source adopters for this owner across activation IDs.
    # The managed host separately owns its short admission/checkpoint boundary.
    with _locked(path.with_name(_receipt(root, owner).stem + "-activations")):
        return _resume(root, owner, path, json.loads(path.read_text()), binary)


def default_binary() -> Path:
    target = REPOSITORY / "tools/workflow-harness/target"
    for profile in ("release", "debug"):
        candidate = target / profile / "workflow-harness"
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate
    return target / "release/workflow-harness"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("apply", "recover"))
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--owner", required=True)
    parser.add_argument("--activation", required=True)
    parser.add_argument("--binary", type=Path, default=default_binary())
    parser.add_argument("--session", type=Path)
    parser.add_argument("--expected-invocation", type=int)
    parser.add_argument("--request", type=Path)
    arguments = parser.parse_args()
    try:
        if arguments.command == "apply":
            if arguments.session is None or arguments.expected_invocation is None or arguments.request is None:
                parser.error("apply requires --session, --expected-invocation and --request")
            result = apply(arguments.root, arguments.owner, arguments.session, arguments.activation,
                           arguments.expected_invocation, json.loads(arguments.request.read_text()), arguments.binary)
        else:
            result = recover(arguments.root, arguments.owner, arguments.activation, arguments.binary)
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    except (OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired) as error:
        parser.exit(2, f"Correction remains incomplete: {error}\n")


if __name__ == "__main__":
    main()
