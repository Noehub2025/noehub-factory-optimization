"""Small adopted research accounts, derived views and recoverable publication.

These checks establish saved content and declared dependencies. They do not
establish scientific correctness, complete research coverage or authorization.
"""

from __future__ import annotations

import copy
import fcntl
import html
import json
import os
from pathlib import Path
import re

from identity_bindings import canonical_json, normalize_repo_path, sha256_bytes


KINDS = {"question", "observation", "external_report", "hypothesis",
         "interpretation", "approach", "capability", "unknown"}
RELATIONS = {"supports", "challenges", "depends_on", "depends-on", "tests",
             "realizes", "considers", "competes"}
REQUIRED = {"depends_on", "depends-on"}
NEIGHBORS = {"supports", "challenges", "competes"}
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
ITEM_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}\Z")


class SourceVersionError(ValueError):
    """The current source no longer supplies the authorized selected content."""


def _text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be nonempty text")
    return value


def _sha(value, label):
    if not isinstance(value, str) or not SHA256.fullmatch(value):
        raise ValueError(f"{label} must be a SHA-256 digest")
    return value


def _source(value):
    if not isinstance(value, dict):
        raise ValueError("research source must use a source-selector mapping")
    value = copy.deepcopy(value)
    value["path"] = normalize_repo_path(value.get("path"), "research source path")
    if value.get("field") and value.get("section"):
        raise ValueError("research source must select either field or section")
    for key in ("field", "section", "commit"):
        if key in value:
            _text(value[key], f"research source {key}")
    if "attempt" in value:
        if type(value["attempt"]) is not int or value["attempt"] < 1:
            raise ValueError("research return attempt must be a positive integer")
        if value.get("field") or value.get("section"):
            raise ValueError("research source cannot combine attempt and field/section selectors")
    _sha(value.get("sha256"), "research selected source sha256")
    return value


def validate_basis(value: dict) -> dict:
    """Validate schema 1 without adding fields that change its canonical digest."""
    if not isinstance(value, dict) or type(value.get("schema")) is not int or value["schema"] != 1:
        raise ValueError("research_basis must use schema 1")
    value = copy.deepcopy(value)
    _text(value.get("overview"), "research overview")
    if not isinstance(value.get("items"), list):
        raise ValueError("research items must be a list")
    ids = set()
    for item in value["items"]:
        if not isinstance(item, dict):
            raise ValueError("research item must be a mapping")
        identity = item.get("id")
        if not isinstance(identity, str) or not ITEM_ID.fullmatch(identity) or identity in ids:
            raise ValueError("research items need unique stable identifiers")
        ids.add(identity)
        if item.get("kind") not in KINDS:
            raise ValueError("unsupported research evidence kind")
        _text(item.get("text"), "research statement")
        _text(item.get("conditions"), "research conditions (use explicit unknown when needed)")
        if item.get("status", "current") not in {"current", "withdrawn"}:
            raise ValueError("research item status must be current or withdrawn")
        if not isinstance(item.get("sources"), list) or not isinstance(item.get("links"), list):
            raise ValueError("research item needs source and relationship lists")
        for source in item["sources"]:
            normalized = _source(source)
            if normalized != source:
                raise ValueError("research source paths must already be canonical repository paths")
        for link in item["links"]:
            if not isinstance(link, dict) or link.get("relation") not in RELATIONS:
                raise ValueError("unsupported research relationship")
            _text(link.get("target"), "research relationship target")
            if "qualification" in link:
                _text(link["qualification"], "research relationship qualification")
    for item in value["items"]:
        if any(link["target"] not in ids for link in item["links"]):
            raise ValueError("research relationship refers to a missing item")
    # JSON's default NaN encoding is not a meaningful content identity.
    json.dumps(value, allow_nan=False)
    return value


def basis_digest(value: dict) -> str:
    return sha256_bytes(canonical_json(validate_basis(value)))


def item_digests(value: dict) -> dict[str, str]:
    return {item["id"]: sha256_bytes(canonical_json(item))
            for item in validate_basis(value)["items"]}


def select_basis(value: dict, item_ids=None) -> dict:
    """Expand required dependencies and one direct evidence neighborhood.

    Required edges point from the dependent item to its prerequisite. Evidence
    edges count in either direction. Newly included evidence adds its required
    dependencies, not another unbounded associative neighborhood.
    """
    value = validate_basis(value)
    items = {item["id"]: item for item in value["items"]}
    selected = list(items) if item_ids is None else list(item_ids)
    if any(not isinstance(key, str) for key in selected) or len(set(selected)) != len(selected):
        raise ValueError("research selection needs distinct item identifiers")
    if set(selected) - items.keys():
        raise ValueError("research selection refers to a missing item")

    def required_closure(keys):
        found, pending = set(keys), list(keys)
        while pending:
            for link in items[pending.pop()]["links"]:
                if link["relation"] in REQUIRED and link["target"] not in found:
                    found.add(link["target"])
                    pending.append(link["target"])
        return found

    core = required_closure(selected)
    neighbors = set(core)
    for key, item in items.items():
        for link in item["links"]:
            if link["relation"] in NEIGHBORS and (key in core or link["target"] in core):
                neighbors.update((key, link["target"]))
    included = required_closure(neighbors)
    projection = {"schema": 1, "revision": basis_digest(value), "overview": value["overview"],
                  "selected_ids": sorted(selected), "included_ids": sorted(included),
                  "items": [item for item in value["items"] if item["id"] in included]}
    projection["item_sha256"] = {key: digest for key, digest in item_digests(value).items() if key in included}
    projection["sha256"] = sha256_bytes(canonical_json(projection))
    return projection


def _verified_view(view):
    value = copy.deepcopy(view)
    digest = value.pop("sha256", None)
    if digest != sha256_bytes(canonical_json(value)):
        raise ValueError("research projection differs from its derived digest")
    return value


def render_basis(view: dict, *, max_chars: int = 16000, mermaid: bool = False) -> dict:
    """Render whole statements with conditions; expose omissions instead of clipping."""
    _verified_view(view)
    if type(max_chars) is not int or max_chars < 512:
        raise ValueError("research rendering budget must be at least 512 characters")
    header = (f"Research projection; adopted revision: {view['revision']}\n"
              f"Projection digest: {view['sha256']}\n"
              "Derived view, not a separate authority. Full source remains available through its retained locator.\n")
    # Reserve room for an explicit omission summary, including large selections.
    budget = max_chars - 200
    parts = [header]
    overview = f"\nCurrent understanding\n{view['overview']}\n"
    overview_omitted = len(header) + len(overview) > budget
    if not overview_omitted:
        parts.append(overview)
    shown, omitted = [], []
    for item in view["items"]:
        sources = "; ".join(json.dumps(source, ensure_ascii=False, sort_keys=True) for source in item["sources"]) or "No source claimed."
        links = "; ".join(f"{link['relation']} {link['target']}" +
                          (f" ({link['qualification']})" if link.get("qualification") else "")
                          for link in item["links"]) or "None declared."
        block = (f"\n{item['id']} [{item['kind']}; {item.get('status', 'current')}]\n"
                 f"{item['text']}\nConditions: {item['conditions']}\nSources: {sources}\nRelationships: {links}\n")
        if sum(map(len, parts)) + len(block) <= budget:
            parts.append(block)
            shown.append(item)
        else:
            omitted.append(item["id"])
    diagram_omitted = False
    if mermaid:
        nodes = {item["id"]: f"n{index}" for index, item in enumerate(shown)}
        lines = ["\n```mermaid", "flowchart TD"]
        for item in shown:
            label = html.escape(f"{item['id']} [{item['kind']}; {item.get('status', 'current')}]: {item['text']}", quote=True).replace("\n", "<br/>")
            lines.append(f'    {nodes[item["id"]]}["{label}"]')
        for item in shown:
            for link in item["links"]:
                if link["target"] in nodes:
                    lines.append(f'    {nodes[item["id"]]} -->|{link["relation"]}| {nodes[link["target"]]}')
        lines.append("```\n")
        diagram = "\n".join(lines)
        if sum(map(len, parts)) + len(diagram) <= budget:
            parts.append(diagram)
        else:
            diagram_omitted = True
    parts.append(f"\nOmitted by display budget: {len(omitted)} items; overview omitted: {overview_omitted}; diagram omitted: {diagram_omitted}. Retrieve the complete projection/source before relying on omitted material.\n")
    return {"text": "".join(parts), "omitted_ids": omitted, "overview_omitted": overview_omitted,
            "diagram_omitted": diagram_omitted, "complete": not omitted and not overview_omitted and not diagram_omitted,
            "revision": view["revision"], "sha256": view["sha256"]}


def validate_research_use(value: dict, *, owner: str, basis: dict) -> dict:
    if not isinstance(value, dict) or not isinstance(value.get("items"), list):
        raise ValueError("research_use needs an owner and item identifiers")
    owner = normalize_repo_path(owner, "research owner")
    supplied = normalize_repo_path(value.get("owner"), "research_use owner")
    if supplied != owner:
        raise ValueError("research_use owner differs from the prepared owner")
    select_basis(basis, value["items"])
    if "revision" in value and value["revision"] != basis_digest(basis):
        raise ValueError("research_use revision differs from the adopted account")
    return copy.deepcopy(value)


def affected_uses(before: dict, after: dict, consumers, *, owner: str, changed_sources=()) -> dict:
    """Derive candidates from consumer declarations, never a second dependency ledger."""
    old, new = item_digests(before), item_digests(after)
    changed = {key for key in old.keys() | new.keys() if old.get(key) != new.get(key)}
    source_paths = {normalize_repo_path(path, "changed research source") for path in changed_sources}
    # Source paths nominate possible effects. The actual selected passage may
    # remain unchanged; the caller/owner must distinguish that from an item edit.
    source_affected = {item["id"] for account in (before, after) for item in account["items"]
                       if any(source["path"] in source_paths for source in item["sources"])}
    overview_changed = before["overview"] != after["overview"]
    uses, undeclared = [], []
    for consumer in consumers:
        path = normalize_repo_path(consumer.get("path"), "research consumer")
        use = consumer.get("research_use")
        if use is None:
            undeclared.append(path)
            continue
        if normalize_repo_path(use.get("owner"), "research_use owner") != normalize_repo_path(owner, "research owner"):
            continue
        keys = use.get("items")
        if not isinstance(keys, list) or any(not isinstance(key, str) for key in keys):
            raise ValueError("research_use needs item identifiers")
        missing = set(keys) - new.keys()
        dependencies = set(keys)
        for account, ids in ((before, old), (after, new)):
            dependencies.update(select_basis(account, [key for key in keys if key in ids])["included_ids"])
        relevant = sorted(changed & dependencies)
        source_candidates = sorted(source_affected & dependencies)
        if relevant or missing or overview_changed or source_candidates:
            uses.append({"path": path, "changed_items": relevant, "missing_items": sorted(missing),
                         "overview_changed": overview_changed, "source_affected_items": source_candidates})
    return {"changed_items": sorted(changed), "uses": uses, "undeclared_consumers": undeclared,
            "coverage": "Declared consumers only; omitted references and semantic relevance need owner judgment."}


def _sync_directory(path: Path):
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _save_state(path: Path, state: dict):
    from frontier_context import _publish
    _publish(path, state)
    _sync_directory(path.parent)


def _retain(root: Path, text: str) -> dict:
    from context_delivery import retain_source
    result = retain_source(root, text)
    _sync_directory((root / result["path"]).parent)
    return result


def _owner_bytes(owner: str, metadata: dict, original: bytes) -> bytes:
    import yaml
    text = original.decode()
    header = re.match(r"\A---\s*\n(.*?)\n---(?:\s*\n|\Z)", text, re.S)
    if owner.endswith(".md"):
        body = text[header.end():] if header else text
        return ("---\n" + yaml.safe_dump(metadata, sort_keys=False) + "---\n" + body).encode()
    if owner.endswith(".json"):
        return json.dumps(metadata, ensure_ascii=False, allow_nan=False).encode()
    return yaml.safe_dump(metadata, sort_keys=False).encode()


def _publish_owner(path: Path, raw: bytes):
    from current_use import _replace_bytes
    _replace_bytes(path, raw)
    _sync_directory(path.parent)


def _read_sources(root: Path, sources):
    import yaml
    from context_delivery import digest
    from frontier_references import _selected_text, _source_metadata, read_reference
    captured = []
    for source in sources:
        source = _source(source)
        path = (root / source["path"]).resolve()
        if not path.is_relative_to(root):
            raise SourceVersionError("research source must stay inside the workspace")
        try:
            text = read_reference(root, source).decode() if source.get("commit") else path.read_text()
            selected = _selected_text(text, source)
            if "attempt" in source:
                result = [item for item in _source_metadata(text).get("attempts", [])
                          if item.get("attempt") == source["attempt"] and "result" in item]
                if len(result) != 1:
                    raise ValueError("incorporation needs one existing return result")
                selected = canonical_json(result[0]["result"]).decode()
        except (OSError, ValueError, yaml.YAMLError) as exc:
            raise SourceVersionError(f"research source selection is unavailable: {source['path']}: {exc}") from exc
        if digest(selected) != source["sha256"]:
            raise SourceVersionError("research source differs from the authorized selected version")
        # Storage failures are distinct from an obsolete source version. They
        # must not silently abandon an otherwise recoverable publication.
        captured.append({"source": source, "retrieval": _retain(root, text)})
    return captured


def _publication_result(operation, entry, current: bytes):
    return {"operation": operation, "status": entry["status"],
            "request_sha256": entry["request_sha256"], "account_sha256": entry["account_sha256"],
            "owner_sha256": entry.get("after", {}).get("sha256"),
            "current": sha256_bytes(current) == entry.get("after", {}).get("sha256"),
            "proposal": entry["proposal"]}


def _previous_account(root: Path, previous: dict) -> dict | None:
    """Retain the adopted passage, including an existing ordinary prose account."""
    from context_delivery import read_retained
    from frontier_references import _selected_text, read_reference
    identity = previous.get("sha256")
    if identity is None:
        return None
    _sha(identity, "previous adopted account sha256")
    source = previous.get("source")
    selected = None
    if isinstance(source, dict) and isinstance(source.get("path"), str):
        path = (root / source["path"]).resolve()
        if not path.is_relative_to(root):
            raise ValueError("previous account source must stay inside the workspace")
        try:
            text = read_reference(root, source).decode() if source.get("commit") else path.read_text()
            selected = _selected_text(text, source)
        except (OSError, ValueError):
            pass
    if selected is not None and sha256_bytes(selected.encode()) == identity:
        return _retain(root, selected)
    locator = {"path": f"artifacts/workflow-harness/context-sources/{identity}.txt", "sha256": identity}
    try:
        read_retained(root, locator)
    except (OSError, ValueError) as exc:
        raise ValueError("previous adopted account is unavailable; recover verified history before replacing it") from exc
    return locator


def _reconcile_locked(root: Path, owner: str, state: dict, *, complete: bool):
    """Called while both existing owner-adoption and receipt locks are held."""
    from context_delivery import read_retained
    from current_use import _metadata
    changed = False
    for operation, entry in state.get("research_publications", {}).items():
        if entry["status"] != "pending":
            continue
        request_text = read_retained(root, entry["request"])
        if sha256_bytes(request_text.encode()) != entry["request_sha256"]:
            raise ValueError("retained research publication request is corrupt")
        request = json.loads(request_text)
        before = read_retained(root, entry["before"]).encode()
        after = read_retained(root, entry["after"]).encode()
        if entry.get("previous_account"):
            read_retained(root, entry["previous_account"])
        for captured in entry.get("sources", []):
            read_retained(root, captured["retrieval"])
        current = (root / owner).read_bytes()
        after_meta = _metadata(after, owner)
        association = after_meta.get("context_account", {})
        marker = association.get("publication")
        expected_marker = {"operation": operation, "request_sha256": entry["request_sha256"]}
        if (marker != expected_marker or sha256_bytes(before) != request["expected_owner_sha256"]
                or request.get("owner") != owner or request.get("operation") != operation
                or after_meta.get("research_basis") != request["proposed_account"]
                or association.get("sha256") != basis_digest(request["proposed_account"])
                or association.get("source") != {"path": owner, "field": "research_basis"}):
            raise ValueError("retained research publication does not match its immutable request")
        if current == after:
            entry["status"] = "adopted"
            changed = True
        elif current == before:
            try:
                _read_sources(root, [*request["sources"], *request["incorporates"]])
            except SourceVersionError as exc:
                # Publication did not occur and its original evidence no longer
                # applies. Retain the exact rejected proposal, allowing a new
                # owner-authored operation to merge against current evidence.
                # Never perform this transition after owner replacement or when
                # the owner differs from both verified snapshots.
                entry["status"] = "conflict"
                entry["conflict"] = {"reason": "source_changed_before_publication", "detail": str(exc)}
                changed = True
                continue
            if not complete:
                raise ValueError("unfinished research publication must be recovered before another owner write")
            if (root / owner).read_bytes() != before:
                raise ValueError("research owner changed outside the shared publication lock")
            _publish_owner(root / owner, after)
            if (root / owner).read_bytes() != after:
                raise ValueError("research owner changed outside the shared publication lock")
            entry["status"] = "adopted"
            changed = True
        else:
            raise ValueError("unfinished research publication conflicts with the current owner; reconcile saved work")
    return changed


def reconcile_context_publications(root: Path, owner: str) -> None:
    """Protect other participating owner writers; caller holds the adoption lock."""
    from current_use import _path, _receipt, _state
    root = root.resolve()
    owner = _path(root, owner)
    receipt = _receipt(root, owner)
    if not receipt.exists():
        return
    with receipt.with_suffix(".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        state = _state(receipt)
        if _reconcile_locked(root, owner, state, complete=False):
            _save_state(receipt, state)


def adopt_context_account(root: Path, owner: str, *, operation: str,
                          expected_owner_sha256: str, expected_account_sha256: str | None,
                          proposed_account: dict, sources=(), incorporates=None) -> dict:
    """Publish one adopted account, or recover that exact authorized publication.

    The owner file is the publication point. Existing correction state remains
    unresolved. Repeated operation identities cannot acquire different meaning.
    Cooperating writers use the existing per-owner lock; direct editors remain
    outside its guarantee.
    """
    from context_delivery import read_retained
    from current_use import _metadata, _path, _receipt, _state
    root = root.resolve()
    owner = _path(root, owner)
    _text(operation, "research publication operation")
    if len(operation) > 128:
        raise ValueError("research publication operation is too long")
    _sha(expected_owner_sha256, "expected owner sha256")
    if expected_account_sha256 is not None:
        _sha(expected_account_sha256, "expected account sha256")
    proposed = validate_basis(proposed_account)
    source_values = []
    for source in [*sources, *(source for item in proposed["items"] for source in item["sources"])]:
        value = _source(source)
        if value not in source_values:
            source_values.append(value)
    incorporated = []
    for item in incorporates or []:
        value = _source(item)
        if value not in incorporated:
            incorporated.append(value)
    request = {"operation": operation, "owner": owner,
               "expected_owner_sha256": expected_owner_sha256,
               "expected_account_sha256": expected_account_sha256,
               "proposed_account": proposed, "sources": source_values,
               "incorporates": incorporated}
    request_text = canonical_json(request).decode()
    request_sha = sha256_bytes(request_text.encode())
    receipt = _receipt(root, owner)
    receipt.parent.mkdir(parents=True, exist_ok=True)
    with receipt.with_suffix(".adoption.lock").open("a") as adoption_lock:
        fcntl.flock(adoption_lock, fcntl.LOCK_EX)
        with receipt.with_suffix(".lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            state = _state(receipt)
            publications = state.setdefault("research_publications", {})
            existing = publications.get(operation)
            if existing and existing["request_sha256"] != request_sha:
                raise ValueError("research publication operation was reused with different inputs")
            if _reconcile_locked(root, owner, state, complete=True):
                _save_state(receipt, state)
            if existing:
                if existing["status"] == "conflict":
                    raise ValueError("research publication retains a conflicting proposal; merge under a new operation")
                # Verified history remains history after a later valid publication.
                read_retained(root, existing["request"])
                read_retained(root, existing["after"])
                return _publication_result(operation, existing, (root / owner).read_bytes())
            original = (root / owner).read_bytes()
            metadata = _metadata(original, owner)
            previous = metadata.get("context_account") or {}
            if not isinstance(previous, dict):
                raise ValueError("existing context_account must be a mapping")
            account_sha = basis_digest(proposed)
            entry = {"status": "conflict", "request_sha256": request_sha,
                     "request": _retain(root, request_text),
                     "proposal": _retain(root, canonical_json(proposed).decode()),
                     "account_sha256": account_sha}
            publications[operation] = entry
            if sha256_bytes(original) != expected_owner_sha256 or previous.get("sha256") != expected_account_sha256:
                _save_state(receipt, state)
                raise ValueError("research publication base changed; retained proposal needs a content-aware merge")
            previous_account = _previous_account(root, previous)
            if "research_basis" in metadata:
                prior_ids = {item["id"] for item in validate_basis(metadata["research_basis"])["items"]}
                if prior_ids - {item["id"] for item in proposed["items"]}:
                    raise ValueError("retain withdrawn research identifiers rather than deleting or recycling them")
            captured = _read_sources(root, [*source_values, *incorporated])
            # Preserve prior incorporated return identities, including unresolved
            # correction dependencies. New content for an old identity needs an
            # explicit new return revision rather than silent replacement.
            merged = copy.deepcopy(previous.get("incorporates", []))
            by_identity = {(item["path"], item.get("attempt")): item for item in merged}
            for item in incorporated:
                identity = (item["path"], item.get("attempt"))
                if identity in by_identity and by_identity[identity] != item:
                    raise ValueError("incorporated return identity has changed content")
                if identity not in by_identity:
                    merged.append(item)
                    by_identity[identity] = item
            association = copy.deepcopy(previous)
            association.update({"source": {"path": owner, "field": "research_basis"},
                                "sha256": account_sha, "incorporates": merged,
                                "publication": {"operation": operation, "request_sha256": request_sha}})
            # Evidence can concern an unusable implementation. Reading it is
            # not an execution dependency; preserve actual_use only as declared
            # by its existing owner rather than deriving it from citations.
            metadata["research_basis"] = proposed
            metadata["context_account"] = association
            target = _owner_bytes(owner, metadata, original)
            entry.update({"status": "pending", "before": _retain(root, original.decode()),
                          "after": _retain(root, target.decode()), "sources": captured,
                          "previous_account": previous_account})
            # Persist intent and exact bytes before the sole publication point.
            _save_state(receipt, state)
            _reconcile_locked(root, owner, state, complete=True)
            _save_state(receipt, state)
            if entry["status"] != "adopted":
                raise ValueError("research publication retains a conflicting proposal; merge under a new operation")
            return _publication_result(operation, entry, (root / owner).read_bytes())
