"""Retain scoped owner corrections and check saved objects, not scientific judgment."""

from __future__ import annotations

import fcntl
import hashlib
import json
from pathlib import Path
import re


def _digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _path(root: Path, path: str) -> str:
    if not isinstance(path, str) or not path:
        raise ValueError("current-use source needs a path")
    target = (root / path).resolve()
    if not target.is_relative_to(root):
        raise ValueError("current-use source must be inside the workspace")
    return target.relative_to(root).as_posix()


def _file(root: Path, path: str) -> tuple[str, bytes]:
    path = _path(root, path)
    return path, (root / path).read_bytes()


def _metadata(raw: bytes, owner: str) -> dict:
    from frontier_references import _document
    text = raw.decode()
    header = re.match(r"\A---\s*\n(.*?)\n---(?:\s*\n|\Z)", text, re.S)
    if header:
        return _document(header.group(1).encode())
    if owner.endswith(".md") and not text.startswith("---"):
        return {}
    return _document(raw)


def _receipt(root: Path, owner: str) -> Path:
    # Conditional current-owner state shares the existing adopted-context area.
    key = _digest(owner.encode())
    return root / ".frontier/hook-context" / f"owner-{key}-corrections.json"


def _read_receipt(path: Path) -> dict:
    if not path.exists():
        return {}
    from frontier_references import _document
    value = _document(path.read_bytes())
    if not isinstance(value.get("records"), dict):
        raise ValueError("current-use retained association is invalid")
    return value["records"]


def _state(path: Path) -> dict:
    records = _read_receipt(path)
    return json.loads(path.read_bytes()) if path.exists() else {"records": records}


def _relations(root: Path, values) -> list[dict]:
    if not isinstance(values, list):
        raise ValueError("current_use_relations must be a list")
    result = []
    for item in values:
        if not isinstance(item, dict) or item.get("kind") not in {"successor", "dependency"}:
            raise ValueError("current-use relation needs successor or dependency kind")
        entry = {"source": _path(root, item.get("source")), "target": _path(root, item.get("target")), "kind": item["kind"]}
        if entry["source"] == entry["target"]:
            raise ValueError("current-use relation cannot be self")
        if entry not in result:
            result.append(entry)
    return sorted(result, key=lambda item: (item["source"], item["target"], item["kind"]))


def _closure(paths, relations, *, successors_only=False):
    scope = set(paths)
    while True:
        expanded = scope | {item["target"] for item in relations if item["source"] in scope
                            and (not successors_only or item["kind"] == "successor")}
        if expanded == scope:
            return scope
        scope = expanded


def inspect_current_use(root: Path, owner: str, sources=(), *, previous_owner: str | None = None,
                        _corrections=(), _relations_added=(), _pending=None,
                        _complete_pending=False) -> dict | None:
    """Load live corrections, retain known associations, and scope affected use.

    Preparation may inspect an open finding. Only an affected action is held.
    A missing known record cannot release that action. No Git/session is needed.
    """
    root = root.resolve()
    owner, owner_raw = _file(root, owner)
    meta = _metadata(owner_raw, owner)
    declared = meta.get("current_use_corrections", [])
    if not isinstance(declared, list):
        raise ValueError("current_use_corrections must be a list")
    if not all(isinstance(item, dict) for item in declared):
        raise ValueError("current-use correction must be a mapping")
    override = {item["id"]: item for item in _corrections}
    declared = [override.pop(item.get("id"), item) for item in declared] + list(override.values())
    receipt = _receipt(root, owner)
    predecessor = meta.get("current_use_predecessor") or previous_owner
    if not declared and not receipt.exists() and not predecessor:
        return None
    receipt.parent.mkdir(parents=True, exist_ok=True)
    with receipt.with_suffix(".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        state = _state(receipt)
        retained = state["records"]
        inherited_pending = None
        derived = []
        account = meta.get("context_account")
        if isinstance(account, dict) and isinstance(account.get("source"), dict):
            target = account["source"].get("path")
            # This maintained association already declares the derivation.
            # Retain it with known findings even if a later summary drops it.
            inputs = [*account.get("actual_use", []), *(item["path"] for item in account.get("incorporates", []))]
            derived = [{"source": source, "target": target, "kind": "dependency"}
                       for source in inputs if source != target]
        links = _relations(root, state.get("relations", []) + meta.get("current_use_relations", []) + derived + list(_relations_added))
        if predecessor:
            predecessor_path = _path(root, predecessor)
            if predecessor_path == owner:
                raise ValueError("current-use predecessor cannot be self")
            inherited_state = _state(_receipt(root, predecessor_path))
            inherited = inherited_state["records"]
            inherited_pending = inherited_state.get("pending")
            if inherited_pending and state.get("pending") and inherited_pending != state["pending"]:
                raise ValueError("current-use predecessor conflicts with pending adoption")
            if not inherited:
                raise ValueError("current-use predecessor has no retained association")
            for key, value in inherited.items():
                if key in retained and (retained[key]["core"] != value["core"] or retained[key]["before"] != value["before"]):
                    raise ValueError("current-use predecessor conflicts with retained state")
                retained.setdefault(key, value)
            links = _relations(root, links + inherited_state.get("relations", []))
        records, files = {}, {owner: owner_raw}
        missing_files = set()

        def capture(path, optional=False):
            path = _path(root, path)
            if path not in files:
                try:
                    files[path] = _file(root, path)[1]
                except FileNotFoundError:
                    if not optional:
                        raise
                    missing_files.add(path)
                    return path, None
            return path, files[path]

        requested = {_file(root, path)[0] for path in sources}
        for path in requested:
            capture(path)
        for item in declared:
            if not isinstance(item, dict):
                raise ValueError("current-use correction must be a mapping")
            key = item.get("id")
            if not isinstance(key, str) or not key.strip() or key in records:
                raise ValueError("current-use correction needs a unique nonempty id")
            effect, status = item.get("effect"), item.get("status")
            if effect not in {"block", "repair", "advisory"} or status not in {"open", "resolved", "inapplicable"}:
                raise ValueError("unsupported current-use effect or status")
            previous = retained.get(key)
            finding = _path(root, item.get("finding"))
            paths = item.get("affected_sources")
            if not isinstance(paths, list) or not paths:
                raise ValueError("current-use correction needs affected_sources")
            paths = [_path(root, path) for path in paths]
            if len(set(paths)) != len(paths):
                raise ValueError("duplicate affected source")
            if previous:
                if (previous["core"]["finding"] != finding or previous["core"]["effect"] != effect
                        or previous["core"]["affected_sources"] != sorted(paths)):
                    raise ValueError("known correction scope cannot be dropped or relabeled; resolve it through its owner")
                if (requested and not _closure(paths, links) & requested) or (status != "open" and status == previous["status"] and item.get("resolution") == previous["resolution"]):
                    # A discharged finding does not freeze all subsequent work.
                    # Check the actual requested object at consumption below.
                    records[key] = previous
                    continue
            finding, raw = capture(finding)
            files[finding] = raw
            affected = {}
            for path in sorted(_closure(paths, links, successors_only=True)):
                path, raw = capture(path, optional=bool((previous or path not in paths) and path not in requested))
                if raw is None:
                    continue
                if path == owner or path == finding or path in affected:
                    raise ValueError("affected sources must be distinct from owner and finding")
                files[path] = raw
                affected[path] = _digest(raw)
            core = {"finding": finding, "finding_sha256": _digest(files[finding]),
                    "effect": effect, "affected_sources": sorted(paths)}
            if previous and previous["core"] != core:
                raise ValueError("known correction scope cannot be dropped or relabeled; resolve it through its owner")
            before = previous["before"] if previous else affected
            resolution = item.get("resolution")
            if status != "open":
                if not previous:
                    raise ValueError("enroll an open correction before discharging it")
                if not isinstance(resolution, dict) or not isinstance(resolution.get("reason"), str) or not resolution["reason"].strip():
                    raise ValueError("correction discharge needs an owner reason and evidence")
                evidence, raw = capture(resolution.get("evidence"))
                files[evidence] = raw
                if evidence == owner:
                    raise ValueError("discharge needs evidence beyond the status field")
                replacements = resolution.get("replacements")
                if not isinstance(replacements, list):
                    raise ValueError("discharge needs exact current replacement sources")
                supplied = {}
                for replacement in replacements:
                    if not isinstance(replacement, dict):
                        raise ValueError("replacement must identify path and sha256")
                    path, _ = capture(replacement.get("path"))
                    if path in supplied:
                        raise ValueError("duplicate replacement source")
                    supplied[path] = replacement.get("sha256")
                if supplied != affected:
                    raise ValueError("correction replacements differ from current saved sources")
                if status == "resolved" and affected == before:
                    raise ValueError("resolved correction did not change the affected objects")
            records[key] = {"core": core, "before": before, "status": status,
                            "resolution": resolution, "current": affected}
        # Retain omitted entries rather than treating absence as resolution.
        missing = sorted(set(retained) - set(records))
        for key in missing:
            records[key] = retained[key]
        pending = _pending if _pending is not None else state.get("pending") or inherited_pending
        blocked = []
        for key, item in records.items():
            scope = _closure(item["core"]["affected_sources"], links)
            relevant = not requested or bool(scope & requested)
            if relevant:
                for path in scope:
                    capture(path, optional=path not in requested)
                capture(item["core"]["finding"])
                if item["resolution"]:
                    capture(item["resolution"]["evidence"])
            if relevant and item["core"]["effect"] != "advisory":
                available = any(path in files for path in _closure(item["core"]["affected_sources"], links, successors_only=True))
                if item["status"] == "open" or not available or (pending and not _complete_pending and key in pending.get("ids", [])):
                    blocked.append(key)
                elif item["status"] == "resolved":
                    # Exact replay of a superseded object is detectable; a new
                    # semantic defect still needs the existing owner judgment.
                    if any(path in files and _digest(files[path]) == before_hash
                           and (path != original or item["current"].get(path) != before_hash)
                           for original, before_hash in item["before"].items()
                           for path in _closure([original], links)):
                        blocked.append(key)

        def verify():
            for path, raw in files.items():
                if _file(root, path)[1] != raw:
                    raise ValueError("current-use dependency changed while reading")
            if any((root / path).exists() for path in missing_files):
                raise ValueError("current-use dependency changed while reading")

        verify()
        from frontier_context import _publish
        value = {"owner": owner, "records": records}
        if links:
            value["relations"] = links
        if pending and not _complete_pending:
            value["pending"] = pending
        if _complete_pending and blocked:
            raise ValueError("current use requires owner correction: " + ", ".join(blocked))
        expected_receipt = json.dumps(value, ensure_ascii=False, allow_nan=False).encode()
        if not receipt.exists() or receipt.read_bytes() != expected_receipt:
            _publish(receipt, value)
        # Validate after publication as well; report the exact judged bytes.
        try:
            verify()
            if receipt.read_bytes() != expected_receipt:
                raise ValueError("current-use receipt changed during publication")
        except (OSError, ValueError):
            if _complete_pending and state.get("pending"):
                # A failed final snapshot must keep the recoverable operation.
                _publish(receipt, state)
            raise
        files[receipt.relative_to(root).as_posix()] = expected_receipt
        consumed = set(requested) | {owner, receipt.relative_to(root).as_posix()}
        for item in records.values():
            scope = _closure(item["core"]["affected_sources"], links)
            if not requested or scope & requested:
                consumed.update(scope)
                consumed.add(item["core"]["finding"])
                if item["resolution"]:
                    consumed.add(item["resolution"]["evidence"])
        checked = requested or {path for item in records.values()
                                for path in _closure(item["core"]["affected_sources"], links)}
        return {"owner": str(root / owner), "checked_sources": [str(root / path) for path in sorted(checked)],
                "correction_ids": sorted(records),
                "blocked_ids": sorted(blocked),
                "files": [{"path": str(root / path), "contents": raw.decode()}
                          for path, raw in sorted(files.items()) if path in consumed]}


def check_current_use(root: Path, owner: str, sources=(), prepared: dict | None = None) -> dict:
    """Check an actual use; labels cannot discharge a known affected finding."""
    current = inspect_current_use(root, owner, sources)
    if current and current["blocked_ids"]:
        raise ValueError("current use requires owner correction: " + ", ".join(current["blocked_ids"]))
    if prepared is not None and current != prepared:
        raise ValueError("prepared current use is stale; use the saved adopted objects")
    return {"status": "current", "current_use": current,
            "coverage": "Saved-object checks only; the existing owner judges semantic correction."}


def same_corrections(left: dict | None, right: dict | None) -> bool:
    """Compare retained correction meaning without freezing ordinary task bytes.

    Delivery still checks exact bytes. Judgment reuse separately checks its
    substantive task projection, while this comparison retains finding state.
    """
    def association(value):
        if value is None:
            return None
        return {"owner": value.get("owner"), "correction_ids": value.get("correction_ids"),
                "blocked_ids": value.get("blocked_ids"),
                "retained": [item for item in value.get("files", [])
                             if Path(item["path"]).name.endswith("-corrections.json")]}
    return association(left) == association(right)


def _replace_bytes(path: Path, raw: bytes) -> None:
    """Publish one owned file; this is not a multi-file transaction."""
    import os
    import tempfile
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        try:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)


def _save_owner(root: Path, owner: str, meta: dict, original: bytes) -> None:
    import yaml
    text = original.decode()
    header = re.match(r"\A---\s*\n(.*?)\n---(?:\s*\n|\Z)", text, re.S)
    if owner.endswith(".md"):
        body = text[header.end():] if header else text
        raw = ("---\n" + yaml.safe_dump(meta, sort_keys=False) + "---\n" + body).encode()
    elif owner.endswith(".json"):
        raw = json.dumps(meta, ensure_ascii=False, allow_nan=False).encode()
    else:
        raw = yaml.safe_dump(meta, sort_keys=False).encode()
    if _file(root, owner)[1] != original:
        raise ValueError("current-use owner changed during adoption")
    if raw != original:
        _replace_bytes(root / owner, raw)


def adopt_current_work(root: Path, owner: str, *, corrections=(), replacements=(), relations=(), sources=()) -> dict:
    """Retain original versions before edits and recover the same owner operation.

    Findings and their semantic discharge are supplied by the existing owner.
    Pending intent uses the existing receipt, independently of native sessions.
    """
    root = root.resolve()
    owner = _path(root, str(owner))
    receipt = _receipt(root, owner)
    request = {"corrections": list(corrections), "replacements": list(replacements), "relations": list(relations)}
    pending = _state(receipt).get("pending")
    supplied = any(request.values())
    if pending:
        if supplied and pending["request"] != request:
            raise ValueError("unfinished current-use adoption has a different request")
        request = pending["request"]
    if not pending and not supplied:
        return check_current_use(root, owner, sources)
    receipt.parent.mkdir(parents=True, exist_ok=True)
    with receipt.with_suffix(".adoption.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        state = _state(receipt)
        pending = state.get("pending")
        if pending and pending["request"] != request:
            raise ValueError("unfinished current-use adoption has a different request")
        items = request["corrections"]
        if not all(isinstance(item, dict) for item in items):
            raise ValueError("adoption corrections must be mappings")
        ids = [item.get("id") for item in items]
        if any(not isinstance(key, str) or not key for key in ids) or len(set(ids)) != len(ids):
            raise ValueError("adoption correction needs unique ids")
        links = _relations(root, state.get("relations", []) + request["relations"])
        for item in items:
            if item.get("status") not in {"resolved", "inapplicable"}:
                raise ValueError("adoption must resolve or establish inapplicability")
            resolution = item.get("resolution")
            if not isinstance(resolution, dict) or not resolution.get("reason") or not resolution.get("evidence"):
                raise ValueError("adoption discharge needs reason and evidence")
        roots = [_path(root, path) for item in items for path in item.get("affected_sources", [])]
        writable = _closure(roots, links, successors_only=True)
        edits = {}
        for edit in request["replacements"]:
            path = _path(root, edit.get("path"))
            if path not in writable or path == owner or path in edits or not isinstance(edit.get("contents"), str):
                raise ValueError("replacement must name one affected source and text contents")
            edits[path] = edit["contents"].encode()
        if not pending:
            opened = [{**item, "status": "open", "resolution": None} for item in items]
            expected = {path: _digest((root / path).read_bytes()) if (root / path).exists() else None for path in writable}
            pending = {"ids": ids, "request": request, "expected_versions": expected}
            inspect_current_use(root, owner, _corrections=opened, _relations_added=links, _pending=pending)
        for path, raw in edits.items():
            target = root / path
            current = _digest(target.read_bytes()) if target.exists() else None
            expected = pending.get("expected_versions", {})
            if path not in expected or current not in {expected[path], _digest(raw)}:
                raise ValueError("affected source changed outside pending adoption; reconcile saved work")
            if current != _digest(raw):
                _replace_bytes(target, raw)

        desired = dict(pending.get("expected_versions", {}))
        desired.update({path: _digest(raw) for path, raw in edits.items()})

        def verify_replacements():
            for path, expected in desired.items():
                target = root / path
                current = _digest(target.read_bytes()) if target.exists() else None
                if current != expected:
                    raise ValueError("affected source changed outside pending adoption; reconcile saved work")

        verify_replacements()
        owner_raw = _file(root, owner)[1]
        meta = _metadata(owner_raw, owner)
        adopted = {item["id"]: item for item in meta.get("current_use_corrections", [])}
        for original in items:
            item = dict(original)
            item["resolution"] = dict(item["resolution"])
            active = _closure([_path(root, path) for path in item["affected_sources"]], links, successors_only=True)
            item["resolution"]["replacements"] = [{"path": path, "sha256": desired[path]}
                                                       for path in sorted(active) if desired.get(path) is not None]
            adopted[item["id"]] = item
        meta["current_use_corrections"] = list(adopted.values())
        if links:
            meta["current_use_relations"] = links
        _save_owner(root, owner, meta, owner_raw)
        verify_replacements()
        # Validate every changed finding before clearing the pending operation;
        # an unrelated requested source cannot discharge affected work.
        adopted_sources = sorted(path for path in _closure(roots, links) if (root / path).is_file())
        recoverable = _state(receipt)
        try:
            inspect_current_use(root, owner, adopted_sources, _complete_pending=True)
            verify_replacements()
            result = check_current_use(root, owner, sources or adopted_sources)
            verify_replacements()
        except (OSError, ValueError):
            from frontier_context import _publish
            if recoverable.get("pending") and not _state(receipt).get("pending"):
                _publish(receipt, recoverable)
            raise
        return result
