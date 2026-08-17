"""Content-addressed persistence for Frontier provenance nodes."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Iterable

from .content import ProvenanceError, canonical_json
from .graph import verify_node


class NodeRepository:
    """Store immutable nodes by verified identity in a portable directory."""

    def __init__(self, root: Path):
        self.root = root.resolve()

    def _path(self, node_id: str) -> Path:
        if not isinstance(node_id, str) or ":" not in node_id:
            raise ProvenanceError("node identity is invalid")
        prefix, digest = node_id.split(":", 1)
        role = prefix.removeprefix("frontier-").removesuffix("-root-sha256")
        if role not in {"decision", "attestation", "authority", "execution", "outcome"}:
            raise ProvenanceError("node identity has an unsupported role")
        if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
            raise ProvenanceError("node identity has an invalid digest")
        return self.root / role / f"{digest}.json"

    def write(self, node: dict[str, Any]) -> Path:
        node_id = verify_node(node)
        destination = self._path(node_id)
        raw = canonical_json(node) + b"\n"
        if destination.exists():
            if destination.is_symlink() or destination.read_bytes() != raw:
                raise ProvenanceError(f"node identity collision: {node_id}")
            return destination
        destination.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(
            prefix=f".{destination.name}.", dir=destination.parent
        )
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, destination)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
        return destination

    def load(self, node_id: str) -> dict[str, Any]:
        path = self._path(node_id)
        if not path.is_file() or path.is_symlink():
            raise ProvenanceError(f"provenance node is missing or unsafe: {node_id}")
        try:
            node = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            raise ProvenanceError(f"provenance node is unreadable: {node_id}: {exc}") from exc
        if verify_node(node) != node_id:
            raise ProvenanceError(f"provenance node does not match its path: {node_id}")
        return node

    def write_all(self, nodes: Iterable[dict[str, Any]]) -> list[Path]:
        return [self.write(node) for node in nodes]
