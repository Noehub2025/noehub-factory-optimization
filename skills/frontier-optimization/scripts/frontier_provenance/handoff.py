"""Atomic portable export and offline verification of a complete provenance chain."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Callable

from .content import ProvenanceError, canonical_json, sha256_bytes
from .facade import export_chain, verify_for
from .repository import NodeRepository
from .stores import PortableBundleStore


HANDOFF_CONTRACT = "frontier-provenance-handoff/1"


def export_handoff(
    root_id: str,
    node_repository: NodeRepository,
    content_exports: dict[str, Callable[[Path], None]],
    destination: Path,
) -> dict[str, Any]:
    nodes = export_chain(root_id, node_repository.load)
    roots = _content_roots(nodes)
    if set(content_exports) != roots:
        raise ProvenanceError("handoff content exporters do not match reachable roots")
    if destination.exists():
        raise ProvenanceError(f"handoff destination already exists: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{destination.name}.", dir=destination.parent))
    try:
        exported_nodes = NodeRepository(staging / "nodes")
        exported_nodes.write_all(nodes)
        content_index: list[dict[str, str]] = []
        for content_root in sorted(roots):
            digest = content_root.split(":", 1)[1]
            relative = f"content/{digest}"
            content_exports[content_root](staging / relative)
            verified = PortableBundleStore().verify(staging / relative)
            if verified["content_root"] != content_root:
                raise ProvenanceError("handoff exporter produced a different content root")
            content_index.append({"content_root": content_root, "path": relative})
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
    return {**verified, "handoff_id": expected_id, "verified": True}


def _content_roots(nodes: list[dict[str, Any]]) -> set[str]:
    return {
        value
        for node in nodes
        for value in node["artifact_roots"]
    }
