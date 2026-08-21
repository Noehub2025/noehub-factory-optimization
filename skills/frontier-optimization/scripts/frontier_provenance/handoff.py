"""Atomic portable export and offline verification of a complete provenance chain."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
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


def export_handoff(
    root_id: str,
    node_repository: NodeRepository,
    content_exports: dict[str, Callable[[Path], None]],
    destination: Path,
) -> dict[str, Any]:
    nodes = export_chain(root_id, node_repository.load)
    chain_roots = _content_roots(nodes)
    if not chain_roots <= set(content_exports):
        raise ProvenanceError("handoff is missing a reachable content exporter")
    if destination.exists():
        raise ProvenanceError(f"handoff destination already exists: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{destination.name}.", dir=destination.parent))
    try:
        exported_nodes = NodeRepository(staging / "nodes")
        exported_nodes.write_all(nodes)
        exported_paths: dict[str, Path] = {}

        def export_content(content_root: str) -> None:
            digest = content_root.split(":", 1)[1]
            relative = f"content/{digest}"
            content_exports[content_root](staging / relative)
            verified = PortableBundleStore().verify(staging / relative)
            if verified["content_root"] != content_root:
                raise ProvenanceError("handoff exporter produced a different content root")
            exported_paths[content_root] = staging / relative

        for content_root in sorted(chain_roots):
            export_content(content_root)
        prerequisite_roots = _routine_prerequisite_roots(
            nodes,
            lambda value: PortableBundleStore().read_artifacts(exported_paths[value]),
        )
        roots = chain_roots | prerequisite_roots
        if set(content_exports) != roots:
            raise ProvenanceError(
                "handoff content exporters do not match reachable and routine prerequisite roots"
            )
        for content_root in sorted(prerequisite_roots - chain_roots):
            export_content(content_root)
        content_index = [
            {
                "content_root": content_root,
                "path": f"content/{content_root.split(':', 1)[1]}",
            }
            for content_root in sorted(roots)
        ]
        body = {
            "contract_version": HANDOFF_CONTRACT,
            "root_id": root_id,
            "node_ids": sorted(node["node_id"] for node in nodes),
            "content": content_index,
        }
        manifest = {
            "handoff_id": "frontier-provenance-handoff-sha256:"
            + sha256_bytes(canonical_json(body)),
            **body,
        }
        (staging / "handoff.json").write_bytes(canonical_json(manifest) + b"\n")
        verify_handoff(staging)
        os.replace(staging, destination)
        return manifest
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def verify_handoff(root: Path) -> dict[str, Any]:
    manifest_path = root / "handoff.json"
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
) -> dict[str, str]:
    """Rebuild the non-authoritative routine-slot index from frozen state bytes."""

    recovered: dict[str, str] = {}
    portable = PortableBundleStore()

    def resolve(content_root: str) -> dict[str, Any]:
        if content_root not in content_results:
            raise ProvenanceError(f"content root is not reachable in handoff: {content_root}")
        return content_results[content_root]

    def read(content_root: str) -> dict[str, bytes]:
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
