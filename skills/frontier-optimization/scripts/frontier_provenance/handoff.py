"""Git-reference handoff writing and read-only legacy handoff verification."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

import yaml

from .content import ProvenanceError, canonical_json, sha256_bytes
from .facade import export_chain, verify_for
from .graph import verify_node
from .repository import NodeRepository
from .stores import PortableBundleStore
from .routine_admission import ADMISSION_LOGICAL_NAME, validate_routine_admission


HANDOFF_CONTRACT = "frontier-provenance-handoff/1"


GIT_HANDOFF_CONTRACT = "frontier-git-handoff/1"


def export_handoff(
    root_id: str, node_repository: NodeRepository,
    content_bindings: list[dict[str, Any]], destination: Path,
) -> dict[str, Any]:
    """Write references to a normal checkpoint, never another copy of its files."""
    from .git_content import ContentSession, GitReferenceStore, retained_commit

    store = GitReferenceStore(node_repository.root)
    commit = retained_commit(store.root, "HEAD")
    session = ContentSession(content_bindings)
    nodes = export_chain(root_id, node_repository.load)
    roots = _content_roots(nodes) | _routine_prerequisite_roots(nodes, session.read)
    if roots != set(session.results):
        raise ProvenanceError("handoff bindings must match the reachable content")
    # Only the small records must be in this checkpoint. Input blobs stay at
    # their original commits and large payloads stay in their retained store.
    for node in nodes:
        path = node_repository._path(node["node_id"])
        relative = path.relative_to(store.root).as_posix()
        raw, _ = store._read(commit, relative)
        if raw != path.read_bytes():
            raise ProvenanceError(f"save the updated record in a normal Git checkpoint: {relative}")
    bindings = []
    for binding in content_bindings:
        path = Path(binding["path"]).resolve()
        relative = path.relative_to(store.root).as_posix()
        raw, _ = store._read(commit, relative + "/manifest.json")
        if raw != (path / "manifest.json").read_bytes():
            raise ProvenanceError(f"save the updated content reference: {relative}")
        bindings.append({"adapter": binding["adapter"], "path": relative})
    verified = verify_for(root_id, node_repository.load, session.resolve,
                          consequence="audit", read_content=session.read)
    if not verified["ready"]:
        raise ProvenanceError("handoff chain is not readable")
    body = {
        "contract_version": GIT_HANDOFF_CONTRACT, "root_id": root_id,
        "commit": commit,
        "node_repository": node_repository.root.relative_to(store.root).as_posix(),
        "content_bindings": sorted(bindings, key=lambda item: item["path"]),
    }
    manifest = {"handoff_id": "frontier-provenance-handoff-sha256:" +
                sha256_bytes(canonical_json(body)), **body}
    destination.mkdir(parents=True, exist_ok=True)
    with (destination / "handoff.json").open("xb") as stream:
        stream.write(canonical_json(manifest) + b"\n")
    return manifest


def _verify_git_handoff(root: Path, manifest: dict[str, Any], repo_root: Path | None = None) -> dict[str, Any]:
    from .git_content import ADAPTER, GitReferenceStore, retained_commit
    from .content import normalize_logical_name

    store = GitReferenceStore(repo_root if repo_root is not None else root)
    body = {key: value for key, value in manifest.items() if key != "handoff_id"}
    expected_id = "frontier-provenance-handoff-sha256:" + sha256_bytes(canonical_json(body))
    if (set(body) != {"contract_version", "root_id", "commit", "node_repository", "content_bindings"}
            or manifest.get("handoff_id") != expected_id):
        raise ProvenanceError("Git handoff record is invalid")
    commit = retained_commit(store.root, body["commit"])
    if commit != body["commit"]:
        raise ProvenanceError("handoff must name a full commit")
    relative_repository = normalize_logical_name(body["node_repository"])

    class RetainedNodes(NodeRepository):
        def load(self, node_id: str) -> dict[str, Any]:
            relative = self._path(node_id).relative_to(store.root).as_posix()
            raw, _ = store._read(commit, relative)
            node = json.loads(raw)
            if verify_node(node) != node_id:
                raise ProvenanceError("retained node does not match its identity")
            return node

    repository = RetainedNodes(store.root / relative_repository)
    results, raw_by_root = {}, {}
    for binding in body["content_bindings"]:
        if not isinstance(binding, dict) or set(binding) != {"adapter", "path"}:
            raise ProvenanceError("invalid handoff content binding")
        relative = normalize_logical_name(binding["path"])
        raw, _ = store._read(commit, relative + "/manifest.json")
        content_manifest = json.loads(raw)
        content_raw = {}
        path = store.root / relative
        if binding["adapter"] == ADAPTER:
            result = store.verify(path, manifest=content_manifest, raw_out=content_raw)
        elif binding["adapter"] == "portable-bundle/1":
            result = PortableBundleStore().verify(
                path, content_manifest, raw_out=content_raw, check_semantics=False)
        else:
            raise ProvenanceError("unknown handoff content adapter")
        content_root = result["content_root"]
        if result["adapter"] != binding["adapter"] or content_root in results:
            raise ProvenanceError("handoff content adapter or membership mismatch")
        results[content_root], raw_by_root[content_root] = result, content_raw
    nodes = export_chain(body["root_id"], repository.load)
    if set(results) != _content_roots(nodes) | _routine_prerequisite_roots(nodes, raw_by_root.__getitem__):
        raise ProvenanceError("handoff is missing reachable content")
    verified = verify_for(body["root_id"], repository.load, results.__getitem__,
                          consequence="audit", read_content=raw_by_root.__getitem__)
    slots = _recover_routine_slot_consumption(
        nodes, repository, results, {}, read_content=raw_by_root.__getitem__)
    return {**verified, "handoff_id": expected_id, "verified": True,
            "routine_slot_consumption": slots}


def verify_handoff(root: Path, *, repo_root: Path | None = None) -> dict[str, Any]:
    manifest_path = root / "handoff.json"
    if manifest_path.is_file() and not manifest_path.is_symlink():
        try:
            reference = json.loads(manifest_path.read_text())
        except (OSError, ValueError) as exc:
            raise ProvenanceError("handoff reference is unreadable") from exc
        if reference.get("contract_version") == GIT_HANDOFF_CONTRACT:
            return _verify_git_handoff(root, reference, repo_root)
    nodes_root = root / "nodes"
    content_root = root / "content"
    if not root.is_dir() or root.is_symlink():
        raise ProvenanceError("handoff root is missing or unsafe")
    if (
        not manifest_path.is_file()
        or manifest_path.is_symlink()
        or not nodes_root.is_dir()
        or nodes_root.is_symlink()
        or not content_root.is_dir()
        or content_root.is_symlink()
    ):
        raise ProvenanceError("handoff manifest or storage root is missing or unsafe")
    try:
        manifest = json.loads(manifest_path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise ProvenanceError(f"handoff manifest is unreadable: {exc}") from exc
    required = {"handoff_id", "contract_version", "root_id", "node_ids", "content"}
    if not isinstance(manifest, dict) or set(manifest) != required:
        raise ProvenanceError("handoff manifest has an invalid shape")
    body = {key: value for key, value in manifest.items() if key != "handoff_id"}
    expected_id = "frontier-provenance-handoff-sha256:" + sha256_bytes(
        canonical_json(body)
    )
    if manifest["contract_version"] != HANDOFF_CONTRACT or manifest["handoff_id"] != expected_id:
        raise ProvenanceError("handoff identity is invalid")
    content_results: dict[str, dict[str, Any]] = {}
    content_paths: dict[str, Path] = {}
    seen_content_roots: set[str] = set()
    expected_paths = {"handoff.json"}
    for item in manifest["content"]:
        if not isinstance(item, dict) or set(item) != {"content_root", "path"}:
            raise ProvenanceError("handoff content index is invalid")
        digest = item["content_root"].split(":", 1)[-1]
        if item["path"] != f"content/{digest}" or item["content_root"] in seen_content_roots:
            raise ProvenanceError("handoff content index path or uniqueness is invalid")
        seen_content_roots.add(item["content_root"])
        path = root / item["path"]
        result = PortableBundleStore().verify(path)
        if result["content_root"] != item["content_root"]:
            raise ProvenanceError("handoff content index root mismatch")
        content_results[item["content_root"]] = result
        content_paths[item["content_root"]] = path
        expected_paths.update(
            child.relative_to(root).as_posix() for child in path.rglob("*") if child.is_file()
        )
    repository = NodeRepository(nodes_root)
    verified = verify_for(
        manifest["root_id"],
        repository.load,
        content_results.__getitem__,
        consequence="audit",
        read_content=lambda content_root: PortableBundleStore().read_artifacts(content_paths[content_root]),
    )
    nodes = export_chain(manifest["root_id"], repository.load)
    if sorted(node["node_id"] for node in nodes) != manifest["node_ids"]:
        raise ProvenanceError("handoff node inventory is incomplete")
    expected_paths.update(
        child.relative_to(root).as_posix()
        for child in nodes_root.rglob("*")
        if child.is_file()
    )
    observed_paths = {
        child.relative_to(root).as_posix() for child in root.rglob("*") if child.is_file()
    }
    if observed_paths != expected_paths:
        raise ProvenanceError("handoff contains missing or unexpected files")
    expected_content_roots = _content_roots(nodes) | _routine_prerequisite_roots(
        nodes,
        lambda value: PortableBundleStore().read_artifacts(content_paths[value]),
    )
    if set(content_results) != expected_content_roots:
        raise ProvenanceError(
            "handoff content inventory does not close routine prerequisites"
        )
    slot_consumption = _recover_routine_slot_consumption(
        nodes, repository, content_results, content_paths
    )
    return {
        **verified,
        "handoff_id": expected_id,
        "routine_slot_consumption": slot_consumption,
        "verified": True,
    }


def _content_roots(nodes: list[dict[str, Any]]) -> set[str]:
    return {
        value
        for node in nodes
        for value in node["artifact_roots"]
    }


def _routine_prerequisite_roots(
    nodes: list[dict[str, Any]], read_content: Callable[[str], dict[str, bytes]]
) -> set[str]:
    """Find exact late decision/outcome roots named by routine execution state."""

    roots: set[str] = set()
    for execution in (node for node in nodes if node["role"] == "execution"):
        state_raw = read_content(execution["artifact_roots"][0])
        admission_raw = state_raw.get(ADMISSION_LOGICAL_NAME)
        if admission_raw is None:
            continue
        try:
            admission = yaml.safe_load(admission_raw)
        except yaml.YAMLError as exc:
            raise ProvenanceError("routine admission in handoff is unreadable") from exc
        late = admission.get("late_objects") if isinstance(admission, dict) else None
        if not isinstance(late, dict):
            raise ProvenanceError("routine admission has no late-object inventory")
        for role, root_field in (
            ("materialization_outcome_node", "materialization_outcome_root"),
            ("implementation_review_decision_node", "implementation_review_decision_root"),
            (
                "implementation_review_attestation_node",
                "implementation_review_attestation_root",
            ),
        ):
            logical_name = late.get(role)
            if not isinstance(logical_name, str) or logical_name not in state_raw:
                raise ProvenanceError(f"routine state is missing {role}")
            try:
                node = json.loads(state_raw[logical_name])
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ProvenanceError(f"routine state {role} is unreadable") from exc
            if verify_node(node) != admission.get(root_field):
                raise ProvenanceError(f"routine state {role} binds a different node")
            roots.update(node["artifact_roots"])
        live_receipt_root = admission.get("live_receipt_root")
        if not isinstance(live_receipt_root, str):
            raise ProvenanceError("routine admission has no live receipt root")
        roots.add(live_receipt_root)
    return roots


def _recover_routine_slot_consumption(
    nodes: list[dict[str, Any]],
    repository: NodeRepository,
    content_results: dict[str, dict[str, Any]],
    content_paths: dict[str, Path],
    *, read_content: Callable[[str], dict[str, bytes]] | None = None,
) -> dict[str, str]:
    """Rebuild the non-authoritative routine-slot index from frozen state bytes."""

    recovered: dict[str, str] = {}
    portable = PortableBundleStore()

    def resolve(content_root: str) -> dict[str, Any]:
        if content_root not in content_results:
            raise ProvenanceError(f"content root is not reachable in handoff: {content_root}")
        return content_results[content_root]

    def read(content_root: str) -> dict[str, bytes]:
        if read_content is not None:
            return read_content(content_root)
        if content_root not in content_paths:
            raise ProvenanceError(f"content bytes are not reachable in handoff: {content_root}")
        return portable.read_artifacts(content_paths[content_root])

    for execution in (node for node in nodes if node["role"] == "execution"):
        state_root = execution["artifact_roots"][0]
        raw = read(state_root)
        admission_raw = raw.get(ADMISSION_LOGICAL_NAME)
        if admission_raw is None:
            continue
        try:
            admission = yaml.safe_load(admission_raw)
        except yaml.YAMLError as exc:
            raise ProvenanceError("routine admission in handoff is unreadable") from exc
        if not isinstance(admission, dict):
            raise ProvenanceError("routine admission in handoff must be a mapping")
        late = admission.get("late_objects")
        if not isinstance(late, dict):
            raise ProvenanceError("routine admission in handoff has no late-object inventory")
        embedded: dict[str, dict[str, Any]] = {}
        for key in (
            "materialization_execution_node",
            "materialization_outcome_node",
            "implementation_review_decision_node",
            "implementation_review_attestation_node",
        ):
            name = late.get(key)
            if not isinstance(name, str) or name not in raw:
                raise ProvenanceError(f"routine handoff is missing {key}")
            try:
                node = json.loads(raw[name])
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ProvenanceError(f"routine handoff {key} is unreadable") from exc
            embedded[node.get("node_id")] = node

        def load(node_id: str) -> dict[str, Any]:
            if node_id in embedded:
                return embedded[node_id]
            return repository.load(node_id)

        authority = load(next(item["node_id"] for item in execution["parents"] if item["edge"] == "authority"))
        result = validate_routine_admission(
            admission=admission,
            authority=authority,
            state_root=state_root,
            state_content=resolve(state_root),
            state_raw=raw,
            load=load,
            resolve_content=resolve,
            read_content=read,
        )
        prior = recovered.setdefault(result["slot_id"], execution["node_id"])
        if prior != execution["node_id"]:
            raise ProvenanceError(f"routine slot has multiple executions: {result['slot_id']}")
    return dict(sorted(recovered.items()))
