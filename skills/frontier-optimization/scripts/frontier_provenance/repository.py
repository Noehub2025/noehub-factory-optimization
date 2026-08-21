"""Content-addressed persistence for Frontier provenance nodes."""

from __future__ import annotations

import json
import hashlib
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

    def contains(self, node_id: str) -> bool:
        path = self._path(node_id)
        if not path.exists():
            return False
        self.load(node_id)
        return True

    def iter_role(self, role: str) -> Iterable[dict[str, Any]]:
        if role not in {"decision", "attestation", "authority", "execution", "outcome"}:
            raise ProvenanceError("provenance node role is invalid")
        directory = self.root / role
        if not directory.exists():
            return ()
        if not directory.is_dir() or directory.is_symlink():
            raise ProvenanceError(f"provenance role directory is unsafe: {role}")
        return tuple(
            self.load(f"frontier-{role}-root-sha256:{path.stem}")
            for path in sorted(directory.glob("*.json"))
        )

    def consume_routine_slot(self, slot_id: str, execution_id: str) -> Path:
        """Consume a slot in the one index fixed to this provenance repository."""

        return SlotConsumptionIndex(self.root / "routine-slots").consume(
            slot_id, execution_id
        )

    def load_routine_slot(self, slot_id: str) -> dict[str, str] | None:
        return SlotConsumptionIndex(self.root / "routine-slots").load(slot_id)


class SlotConsumptionIndex:
    """A rebuildable compare-and-create index for single-use routine slots."""

    def __init__(self, root: Path):
        self.root = root.resolve()

    def _path(self, slot_id: str) -> Path:
        if not isinstance(slot_id, str) or not slot_id.strip():
            raise ProvenanceError("routine slot identity is invalid")
        digest = hashlib.sha256(slot_id.encode()).hexdigest()
        return self.root / f"{digest}.json"

    def consume(self, slot_id: str, execution_id: str) -> Path:
        destination = self._path(slot_id)
        body = {"slot_id": slot_id, "execution_root": execution_id}
        raw = canonical_json(body) + b"\n"
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            descriptor = os.open(
                destination,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                0o600,
            )
        except FileExistsError:
            raise ProvenanceError(f"routine slot was already consumed: {slot_id}")
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        return destination

    def load(self, slot_id: str) -> dict[str, str] | None:
        path = self._path(slot_id)
        if not path.exists():
            return None
        if path.is_symlink() or not path.is_file():
            raise ProvenanceError(f"routine slot index is unsafe: {slot_id}")
        try:
            value = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            raise ProvenanceError(f"routine slot index is unreadable: {slot_id}") from exc
        if (
            not isinstance(value, dict)
            or set(value) != {"slot_id", "execution_root"}
            or value.get("slot_id") != slot_id
            or not isinstance(value.get("execution_root"), str)
        ):
            raise ProvenanceError(f"routine slot index is invalid: {slot_id}")
        return value
