"""Technology-neutral content identities for Frontier provenance roots."""

from __future__ import annotations

import hashlib
import json
from pathlib import PurePosixPath
from typing import Any, Iterable


CONTENT_CONTRACT = "frontier-content-root-sha256/2"
CONTENT_ROOT_PREFIX = "frontier-content-root-sha256:"
ARTIFACT_KINDS = {"blob", "closed-collection-member", "external-receipt"}
CONTENT_DOMAINS = {
    "project-decision",
    "review-report",
    "project-authority",
    "project-state",
    "project-outcome",
    "live-receipt",
    "workflow-release",
}
PROJECT_DOMAINS = CONTENT_DOMAINS - {"workflow-release"}
PROJECT_ROLE_DOMAINS = {
    "decision": "project-decision",
    "review": "review-report",
    "authority": "project-authority",
    "state": "project-state",
    "outcome": "project-outcome",
    "receipt": "live-receipt",
}
DOMAIN_LOGICAL_PREFIXES = {
    "project-decision": "project/decision/",
    "review-report": "project/review/",
    "project-authority": "project/authority/",
    "project-state": "project/state/",
    "project-outcome": "project/outcome/",
    "live-receipt": "receipts/",
    "workflow-release": "release/",
}
WORKFLOW_DEPLOYMENT_ROOTS = {
    (".agents", "skills"),
    (".codex", "skills"),
    (".claude", "skills"),
    (".claude", "commands"),
    (".claude", "agents"),
}


class ProvenanceError(ValueError):
    """Raised when provenance content cannot be reproduced safely."""


def _validate_receipt_metadata(metadata: dict[str, Any]) -> None:
    if (
        set(metadata) not in (
            {"fact", "status", "observed_at", "expires_at"},
            {"fact", "status", "observed_at", "expires_at", "executable"},
        )
        or not isinstance(metadata.get("fact"), str)
        or not metadata["fact"]
        or metadata.get("status") not in {"pass", "fail"}
        or not isinstance(metadata.get("observed_at"), str)
        or not metadata["observed_at"]
        or not isinstance(metadata.get("expires_at"), str)
        or not metadata["expires_at"]
        or (
            "executable" in metadata
            and not isinstance(metadata["executable"], bool)
        )
    ):
        raise ProvenanceError("external receipt metadata is invalid")


def _validate_domain_metadata(
    domain: str, kind: str, metadata: dict[str, Any]
) -> None:
    """Keep project identities free of opaque workflow or source bindings."""

    if kind == "external-receipt":
        _validate_receipt_metadata(metadata)
        return
    if domain == "workflow-release":
        allowed = {"executable", "source_module"}
        if not set(metadata) <= allowed:
            raise ProvenanceError("workflow-release artifact metadata is invalid")
        module = metadata.get("source_module")
        if module is not None and (
            not isinstance(module, str)
            or not module
            or any(character not in "abcdefghijklmnopqrstuvwxyz0123456789-" for character in module)
        ):
            raise ProvenanceError("workflow-release source_module is invalid")
    elif set(metadata) not in (set(), {"executable"}):
        raise ProvenanceError(
            "project artifact metadata may contain only executable"
        )
    if "executable" in metadata and not isinstance(metadata["executable"], bool):
        raise ProvenanceError("artifact executable metadata must be boolean")


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def normalize_logical_name(value: Any, role: str = "logical_name") -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise ProvenanceError(f"{role} must be a nonempty POSIX name")
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or path.as_posix() != value
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise ProvenanceError(f"{role} is not canonical: {value!r}")
    return value


def validate_domain_logical_name(
    domain: str, value: Any, role: str = "logical_name"
) -> str:
    """Keep release and project names in disjoint, role-specific namespaces."""

    name = normalize_logical_name(value, role)
    prefix = DOMAIN_LOGICAL_PREFIXES.get(domain)
    if prefix is None or not name.startswith(prefix) or name == prefix:
        raise ProvenanceError(
            f"{domain} artifact names must start with {prefix!r}"
        )
    parts = PurePosixPath(name).parts
    lowered = tuple(part.lower() for part in parts)
    contains_workflow_root = any(
        lowered[index : index + 2] in WORKFLOW_DEPLOYMENT_ROOTS
        for index in range(len(lowered) - 1)
    )
    if domain in PROJECT_DOMAINS and contains_workflow_root:
        raise ProvenanceError("project artifact name refers to workflow release content")
    return name


def artifact_entry(
    logical_name: str,
    raw: bytes,
    *,
    kind: str = "blob",
    behavioral_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    logical_name = normalize_logical_name(logical_name)
    if kind not in ARTIFACT_KINDS:
        raise ProvenanceError(f"unsupported artifact kind: {kind!r}")
    metadata = behavioral_metadata or {}
    if not isinstance(metadata, dict):
        raise ProvenanceError("behavioral_metadata must be a mapping")
    if kind == "external-receipt":
        _validate_receipt_metadata(metadata)
    canonical_json(metadata)
    return {
        "logical_name": logical_name,
        "kind": kind,
        "behavioral_metadata": metadata,
        "size": len(raw),
        "content_sha256": sha256_bytes(raw),
    }


def _normalize_collections(
    values: Iterable[dict[str, Any]] | None,
    artifact_names: set[str],
    domain: str,
) -> list[dict[str, Any]]:
    collections: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, value in enumerate(values or []):
        if not isinstance(value, dict) or set(value) != {"logical_name", "members"}:
            raise ProvenanceError(
                f"closed_collections[{index}] requires logical_name and members"
            )
        name = validate_domain_logical_name(
            domain,
            value["logical_name"],
            f"closed_collections[{index}].logical_name",
        )
        if name in seen:
            raise ProvenanceError(f"duplicate closed collection: {name}")
        seen.add(name)
        members = value["members"]
        if not isinstance(members, list) or not members:
            raise ProvenanceError(f"closed collection {name} must contain members")
        normalized = sorted(
            validate_domain_logical_name(
                domain, member, f"closed collection {name} member"
            )
            for member in members
        )
        if len(set(normalized)) != len(normalized):
            raise ProvenanceError(f"closed collection {name} has duplicate members")
        missing = sorted(set(normalized) - artifact_names)
        if missing:
            raise ProvenanceError(
                f"closed collection {name} cites missing artifacts: {missing}"
            )
        collections.append({"logical_name": name, "members": normalized})
    return sorted(collections, key=lambda item: item["logical_name"])


def authority_payload(
    artifacts: Iterable[dict[str, Any]],
    closed_collections: Iterable[dict[str, Any]] | None = None,
    *,
    domain: str,
) -> dict[str, Any]:
    if domain not in CONTENT_DOMAINS:
        raise ProvenanceError(f"unsupported content domain: {domain!r}")
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    required = {
        "logical_name",
        "kind",
        "behavioral_metadata",
        "size",
        "content_sha256",
    }
    for index, artifact in enumerate(artifacts):
        if not isinstance(artifact, dict) or set(artifact) != required:
            raise ProvenanceError(f"artifacts[{index}] has an invalid shape")
        name = validate_domain_logical_name(
            domain,
            artifact["logical_name"], f"artifacts[{index}].logical_name"
        )
        if name in seen:
            raise ProvenanceError(f"duplicate artifact logical name: {name}")
        seen.add(name)
        if artifact["kind"] not in ARTIFACT_KINDS:
            raise ProvenanceError(f"artifacts[{index}].kind is unsupported")
        if not isinstance(artifact["behavioral_metadata"], dict):
            raise ProvenanceError(
                f"artifacts[{index}].behavioral_metadata must be a mapping"
            )
        _validate_domain_metadata(
            domain,
            artifact["kind"],
            artifact["behavioral_metadata"],
        )
        if (
            not isinstance(artifact["size"], int)
            or isinstance(artifact["size"], bool)
            or artifact["size"] < 0
        ):
            raise ProvenanceError(f"artifacts[{index}].size is invalid")
        digest = artifact["content_sha256"]
        if (
            not isinstance(digest, str)
            or len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
        ):
            raise ProvenanceError(f"artifacts[{index}].content_sha256 is invalid")
        canonical_json(artifact["behavioral_metadata"])
        normalized.append(dict(artifact))
    if not normalized:
        raise ProvenanceError("a content root requires at least one artifact")
    normalized.sort(key=lambda item: item["logical_name"])
    collections = _normalize_collections(closed_collections, seen, domain)
    kinds = {item["kind"] for item in normalized}
    if domain == "live-receipt" and kinds != {"external-receipt"}:
        raise ProvenanceError("live-receipt content requires only external receipts")
    if domain != "live-receipt" and "external-receipt" in kinds:
        raise ProvenanceError("external receipts require the live-receipt domain")
    return {
        "contract_version": CONTENT_CONTRACT,
        "domain": domain,
        "artifacts": normalized,
        "closed_collections": collections,
    }


def compute_content_root(payload: dict[str, Any]) -> str:
    normalized = authority_payload(
        payload.get("artifacts", []),
        payload.get("closed_collections", []),
        domain=payload.get("domain"),
    )
    if payload.get("contract_version") != CONTENT_CONTRACT:
        raise ProvenanceError(
            f"content contract must be exactly {CONTENT_CONTRACT}"
        )
    return CONTENT_ROOT_PREFIX + sha256_bytes(canonical_json(normalized))


def build_manifest(
    artifacts: Iterable[dict[str, Any]],
    closed_collections: Iterable[dict[str, Any]] | None,
    storage: dict[str, Any],
    *,
    domain: str,
) -> dict[str, Any]:
    payload = authority_payload(artifacts, closed_collections, domain=domain)
    if not isinstance(storage, dict) or not storage:
        raise ProvenanceError("storage must be a nonempty mapping")
    return {
        "content_root": compute_content_root(payload),
        **payload,
        "storage": storage,
    }


def verify_manifest(document: dict[str, Any]) -> str:
    if not isinstance(document, dict):
        raise ProvenanceError("content manifest must be a mapping")
    required = {
        "content_root",
        "contract_version",
        "domain",
        "artifacts",
        "closed_collections",
        "storage",
    }
    if set(document) != required:
        raise ProvenanceError("content manifest has unknown or missing fields")
    expected = compute_content_root(document)
    if document.get("content_root") != expected:
        raise ProvenanceError("content root does not derive from the canonical manifest")
    if not isinstance(document.get("storage"), dict) or not document["storage"]:
        raise ProvenanceError("content manifest storage is invalid")
    return expected
