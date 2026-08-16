#!/usr/bin/env python3
"""Shared content-identity primitives for Frontier validators."""

from __future__ import annotations

import hashlib
import json
import posixpath
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


SHA256_DIGEST = re.compile(r"^[0-9a-f]{64}$")
FILE_BINDING_FIELDS = {"path", "identity_field", "identity", "file_sha256"}
TREE_PATH_SHA256_V1 = "frontier-tree-path-sha256/1"
PACKAGE_PATH_SIZE_SHA256_V1 = "frontier-package-path-size-sha256/1"


class IdentityBindingError(ValueError):
    """Raised when a content binding cannot be derived from repository bytes."""


@dataclass(frozen=True)
class BoundFile:
    path: Path
    relative_path: str
    raw: bytes
    document: dict[str, Any] | None
    identity: str
    file_sha256: str


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode()


def normalize_repo_path(raw: Any, field: str) -> str:
    if not isinstance(raw, str) or not raw.strip() or raw.startswith("/"):
        raise IdentityBindingError(f"{field} must be a nonempty repository-relative path")
    normalized = posixpath.normpath(raw.strip().rstrip("/"))
    if normalized in {".", ".."} or normalized.startswith("../"):
        raise IdentityBindingError(f"{field} escapes the repository")
    return normalized


def resolve_repo_file(repo_root: Path, raw: Any, field: str) -> tuple[str, Path]:
    relative = normalize_repo_path(raw, field)
    root = repo_root.resolve()
    candidate = root / relative
    reject_symlink_components(root, relative, field)
    resolved = candidate.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise IdentityBindingError(f"{field} resolves outside the repository") from exc
    if not resolved.is_file():
        raise IdentityBindingError(f"{field} is missing or is not a regular file")
    return relative, resolved


def reject_symlink_components(repo_root: Path, relative: str, field: str) -> None:
    """Reject a symlink at the source or in any repository-relative parent."""
    current = repo_root.resolve()
    for part in Path(relative).parts:
        current = current / part
        if current.is_symlink():
            raise IdentityBindingError(f"{field} contains a symbolic link: {current}")


def require_digest(value: Any, field: str) -> str:
    if not isinstance(value, str) or not SHA256_DIGEST.fullmatch(value):
        raise IdentityBindingError(f"{field} must be a lowercase 64-character SHA-256 digest")
    return value


def load_file_binding(
    repo_root: Path,
    binding: Any,
    role: str,
    *,
    expected_identity_field: str | None | object = ...,
    expected_identity: str | None = None,
) -> BoundFile:
    """Load one exact file binding and derive its identity from the bound bytes."""
    if not isinstance(binding, dict):
        raise IdentityBindingError(f"{role} binding must be a mapping")
    missing = FILE_BINDING_FIELDS - binding.keys()
    if missing:
        raise IdentityBindingError(f"{role} binding is missing {', '.join(sorted(missing))}")
    unexpected = binding.keys() - FILE_BINDING_FIELDS
    if unexpected:
        raise IdentityBindingError(
            f"{role} binding contains unsupported fields: {', '.join(sorted(unexpected))}"
        )
    relative, path = resolve_repo_file(repo_root, binding.get("path"), f"{role}.path")
    raw = path.read_bytes()
    observed_sha256 = sha256_bytes(raw)
    declared_sha256 = require_digest(binding.get("file_sha256"), f"{role}.file_sha256")
    if declared_sha256 != observed_sha256:
        raise IdentityBindingError(
            f"{role} file SHA-256 mismatch: declared {declared_sha256}, observed {observed_sha256}"
        )

    identity_field = binding.get("identity_field")
    if identity_field is not None and not isinstance(identity_field, str):
        raise IdentityBindingError(f"{role}.identity_field must be a string or null")
    if expected_identity_field is not ... and identity_field != expected_identity_field:
        raise IdentityBindingError(
            f"{role}.identity_field must be {expected_identity_field!r}"
        )

    document: dict[str, Any] | None = None
    if identity_field is None:
        observed_identity = f"sha256:{observed_sha256}"
    else:
        try:
            parsed = yaml.safe_load(raw)
        except yaml.YAMLError as exc:
            raise IdentityBindingError(f"{role} file is not valid YAML or JSON: {exc}") from exc
        if not isinstance(parsed, dict):
            raise IdentityBindingError(f"{role} file must contain a mapping")
        document = parsed
        observed_identity = parsed.get(identity_field)
        if not isinstance(observed_identity, str) or not observed_identity:
            raise IdentityBindingError(
                f"{role} file does not contain a nonempty top-level {identity_field}"
            )

    if binding.get("identity") != observed_identity:
        raise IdentityBindingError(
            f"{role} identity mismatch: declared {binding.get('identity')!r}, observed {observed_identity!r}"
        )
    if expected_identity is not None and observed_identity != expected_identity:
        raise IdentityBindingError(
            f"{role} identity {observed_identity!r} does not equal expected {expected_identity!r}"
        )
    return BoundFile(
        path=path,
        relative_path=relative,
        raw=raw,
        document=document,
        identity=observed_identity,
        file_sha256=observed_sha256,
    )


def tree_inventory(root: Path, algorithm: str) -> tuple[list[dict[str, Any]], str]:
    """Inventory a regular-file tree under one explicit identity algorithm."""
    if not root.is_dir() or root.is_symlink():
        raise IdentityBindingError(f"tree root is missing, unsafe, or not a directory: {root}")
    members: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise IdentityBindingError(f"tree contains a symbolic link: {path}")
        if path.is_dir():
            continue
        if not path.is_file():
            raise IdentityBindingError(f"tree contains a non-regular file: {path}")
        members.append(
            {
                "path": path.relative_to(root).as_posix(),
                "size": path.stat().st_size,
                "sha256": sha256_bytes(path.read_bytes()),
            }
        )
    if not members:
        raise IdentityBindingError(f"tree is empty: {root}")
    if algorithm == TREE_PATH_SHA256_V1:
        payload = [{"path": item["path"], "sha256": item["sha256"]} for item in members]
    elif algorithm == PACKAGE_PATH_SIZE_SHA256_V1:
        payload = members
    else:
        raise IdentityBindingError(f"unknown tree identity algorithm: {algorithm}")
    return members, f"sha256:{sha256_bytes(canonical_json(payload))}"
