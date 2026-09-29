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


def inspect_current_use(root: Path, owner: str, sources=(), *, previous_owner: str | None = None) -> dict | None:
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
    receipt = _receipt(root, owner)
    predecessor = meta.get("current_use_predecessor") or previous_owner
    if not declared and not receipt.exists() and not predecessor:
        return None
    receipt.parent.mkdir(parents=True, exist_ok=True)
    with receipt.with_suffix(".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        retained = _read_receipt(receipt)
        if predecessor:
            predecessor_path = _path(root, predecessor)
            if predecessor_path == owner:
                raise ValueError("current-use predecessor cannot be self")
            inherited = _read_receipt(_receipt(root, predecessor_path))
            if not inherited:
                raise ValueError("current-use predecessor has no retained association")
            for key, value in inherited.items():
                if key in retained and (retained[key]["core"] != value["core"] or retained[key]["before"] != value["before"]):
                    raise ValueError("current-use predecessor conflicts with retained state")
                retained.setdefault(key, value)
        records, files = {}, {}
        requested = {_file(root, path)[0] for path in sources}
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
                if (requested and not set(paths) & requested) or (status != "open" and status == previous["status"] and item.get("resolution") == previous["resolution"]):
                    # A discharged finding does not freeze all subsequent work.
                    # Check the actual requested object at consumption below.
                    records[key] = previous
                    continue
            finding, raw = _file(root, finding)
            files[finding] = raw
            affected = {}
            for path in paths:
                path, raw = _file(root, path)
                if path == owner or path == finding or path in affected:
                    raise ValueError("affected sources must be distinct from owner and finding")
                files[path] = raw
                affected[path] = _digest(raw)
            core = {"finding": finding, "finding_sha256": _digest(files[finding]),
                    "effect": effect, "affected_sources": sorted(affected)}
            if previous and previous["core"] != core:
                raise ValueError("known correction scope cannot be dropped or relabeled; resolve it through its owner")
            before = previous["before"] if previous else affected
            resolution = item.get("resolution")
            if status != "open":
                if not previous:
                    raise ValueError("enroll an open correction before discharging it")
                if not isinstance(resolution, dict) or not isinstance(resolution.get("reason"), str) or not resolution["reason"].strip():
                    raise ValueError("correction discharge needs an owner reason and evidence")
                evidence, raw = _file(root, resolution.get("evidence"))
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
                    path, _ = _file(root, replacement.get("path"))
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
        blocked = []
        for key, item in records.items():
            scope = set(item["core"]["affected_sources"])
            relevant = not requested or bool(scope & requested)
            if relevant and item["core"]["effect"] != "advisory":
                if item["status"] == "open":
                    blocked.append(key)
                elif item["status"] == "resolved":
                    # Exact replay of a superseded object is detectable; a new
                    # semantic defect still needs the existing owner judgment.
                    if any((root / path).is_file() and _digest((root / path).read_bytes()) == item["before"][path]
                           and item["before"][path] != item["current"][path] for path in scope):
                        blocked.append(key)
        if _file(root, owner)[1] != owner_raw:
            raise ValueError("current-use owner changed while reading; retry from current state")
        for path, raw in files.items():
            if _file(root, path)[1] != raw:
                raise ValueError("current-use dependency changed while reading")
        from frontier_context import _publish
        value = {"owner": owner, "records": records}
        if not receipt.exists() or json.loads(receipt.read_text()) != value:
            _publish(receipt, value)
        # Consumption scope is independent of which validation branch ran.
        # Never include another action's files merely because its finding exists.
        consumed = set(requested)
        for item in records.values():
            scope = set(item["core"]["affected_sources"])
            if not requested or scope & requested:
                consumed.update(scope)
                consumed.add(item["core"]["finding"])
                if item["resolution"]:
                    consumed.add(item["resolution"]["evidence"])
        files = {path: _file(root, path)[1] for path in consumed}
        files[owner] = owner_raw
        files[receipt.relative_to(root).as_posix()] = receipt.read_bytes()
        return {"owner": str(root / owner), "correction_ids": sorted(records),
                "blocked_ids": sorted(blocked),
                "files": [{"path": str(root / path), "contents": raw.decode()}
                          for path, raw in sorted(files.items())]}


def check_current_use(root: Path, owner: str, sources=(), prepared: dict | None = None) -> dict:
    """Check an actual use; labels cannot discharge a known affected finding."""
    current = inspect_current_use(root, owner, sources)
    if current and current["blocked_ids"]:
        raise ValueError("current use requires owner correction: " + ", ".join(current["blocked_ids"]))
    if prepared is not None and current != prepared:
        raise ValueError("prepared current use is stale; use the saved adopted objects")
    return {"status": "current", "current_use": current,
            "coverage": "Saved-object checks only; the existing owner judges semantic correction."}
