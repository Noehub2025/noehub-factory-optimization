"""Typed immediate-parent graph for task-agnostic Frontier provenance."""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable
from typing import Any

from .content import ProvenanceError, canonical_json, sha256_bytes


NODE_CONTRACT = "frontier-provenance-node/4"
ROLES = {"decision", "attestation", "authority", "execution", "outcome"}
ROOT_PREFIXES = {
    role: f"frontier-{role}-root-sha256:" for role in ROLES
}
EXPECTED_PARENT_ROLES = {
    "decision": (),
    "attestation": ("subject",),
    "authority": ("decision", "attestation"),
    "execution": ("authority",),
    "outcome": ("execution",),
}
def _payload(role: str, value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ProvenanceError("provenance payload must be a mapping")
    if role != "attestation":
        if value:
            raise ProvenanceError(f"{role} payload must be empty")
        return {}
    required = {
        "subject_root",
        "verdict",
        "findings",
        "freshness",
        "observed_at",
        "expires_at",
        "invalidation_rule",
    }
    if set(value) != required:
        raise ProvenanceError("attestation payload has unknown or missing fields")
    findings = value["findings"]
    if not isinstance(findings, list) or not all(
        isinstance(item, dict)
        and set(item) == {"effect", "code"}
        and item["effect"] in {"block", "repair", "advisory"}
        and isinstance(item["code"], str)
        and re.fullmatch(r"[A-Z][A-Z0-9_]{1,63}", item["code"])
        for item in findings
    ):
        raise ProvenanceError("attestation findings must contain only effect and code")
    return dict(value)


def _root(value: Any, role: str) -> str:
    if not isinstance(value, str) or not value.startswith(
        "frontier-content-root-sha256:"
    ):
        raise ProvenanceError(f"{role} must be a Frontier content root")
    return value


def _parent_edges(values: Iterable[dict[str, Any]]) -> list[dict[str, str]]:
    parents: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for index, value in enumerate(values):
        if not isinstance(value, dict) or set(value) != {"edge", "node_id"}:
            raise ProvenanceError(f"parents[{index}] has an invalid shape")
        edge = value["edge"]
        node_id = value["node_id"]
        if not isinstance(edge, str) or not edge:
            raise ProvenanceError(f"parents[{index}].edge is invalid")
        if not isinstance(node_id, str) or not node_id.startswith("frontier-"):
            raise ProvenanceError(f"parents[{index}].node_id is invalid")
        pair = (edge, node_id)
        if pair in seen:
            raise ProvenanceError(f"duplicate parent edge: {edge} -> {node_id}")
        seen.add(pair)
        parents.append({"edge": edge, "node_id": node_id})
    return sorted(parents, key=lambda item: (item["edge"], item["node_id"]))


def build_node(
    role: str,
    payload: dict[str, Any],
    *,
    parents: Iterable[dict[str, str]] = (),
    artifact_roots: Iterable[str] = (),
) -> dict[str, Any]:
    if role not in ROLES:
        raise ProvenanceError(f"unsupported provenance role: {role!r}")
    normalized_payload = _payload(role, payload)
    normalized_parents = _parent_edges(parents)
    expected_edges = EXPECTED_PARENT_ROLES[role]
    observed_edges = tuple(item["edge"] for item in normalized_parents)
    if observed_edges != tuple(sorted(expected_edges)):
        raise ProvenanceError(
            f"{role} parents must use edges {sorted(expected_edges)}, got {list(observed_edges)}"
        )
    artifacts = sorted({_root(value, "artifact root") for value in artifact_roots})
    if len(artifacts) != 1:
        raise ProvenanceError(f"{role} requires exactly one role-specific content root")
    body = {
        "node_contract": NODE_CONTRACT,
        "role": role,
        "payload": normalized_payload,
        "parents": normalized_parents,
        "artifact_roots": artifacts,
    }
    return {
        "node_id": ROOT_PREFIXES[role] + sha256_bytes(canonical_json(body)),
        **body,
    }


def verify_node(document: dict[str, Any]) -> str:
    if not isinstance(document, dict):
        raise ProvenanceError("provenance node must be a mapping")
    required = {
        "node_id",
        "node_contract",
        "role",
        "payload",
        "parents",
        "artifact_roots",
    }
    if set(document) != required:
        raise ProvenanceError("provenance node has unknown or missing fields")
    if document.get("node_contract") != NODE_CONTRACT:
        raise ProvenanceError(f"provenance node contract must be {NODE_CONTRACT}")
    rebuilt = build_node(
        document.get("role"),
        document.get("payload"),
        parents=document.get("parents", []),
        artifact_roots=document.get("artifact_roots", []),
    )
    if document.get("node_id") != rebuilt["node_id"]:
        raise ProvenanceError("provenance node identity does not derive from its content")
    return rebuilt["node_id"]


def verify_chain(
    root_id: str,
    load: Callable[[str], dict[str, Any]],
) -> dict[str, Any]:
    visited: set[str] = set()
    active: set[str] = set()

    def visit(node_id: str) -> dict[str, Any]:
        if node_id in active:
            raise ProvenanceError(f"provenance graph contains a cycle at {node_id}")
        document = load(node_id)
        if verify_node(document) != node_id:
            raise ProvenanceError(f"loaded node does not match requested identity: {node_id}")
        if node_id in visited:
            return document
        active.add(node_id)
        parents_by_edge: dict[str, dict[str, Any]] = {}
        for edge in document["parents"]:
            parent = visit(edge["node_id"])
            parents_by_edge[edge["edge"]] = parent
        role = document["role"]
        if role == "attestation":
            subject = parents_by_edge["subject"]
            if subject["role"] == "attestation":
                raise ProvenanceError("an attestation cannot attest another attestation")
            if document["payload"].get("subject_root") != subject["node_id"]:
                raise ProvenanceError("attestation subject does not match its parent")
            if document["payload"].get("freshness") not in {"immutable", "live"}:
                raise ProvenanceError("attestation freshness must be immutable or live")
            if not document["artifact_roots"]:
                raise ProvenanceError("attestation requires a validation report root")
            findings = document["payload"].get("findings")
            if not isinstance(findings, list) or not all(
                isinstance(item, dict)
                and item.get("effect") in {"block", "repair", "advisory"}
                for item in findings
            ):
                raise ProvenanceError("attestation findings have invalid effects")
            if document["payload"].get("verdict") == "ready" and any(
                item["effect"] in {"block", "repair"} for item in findings
            ):
                raise ProvenanceError("ready attestation contains blocking findings")
            if document["payload"].get("freshness") == "immutable":
                if any(
                    document["payload"].get(field) is not None
                    for field in ("observed_at", "expires_at", "invalidation_rule")
                ):
                    raise ProvenanceError("immutable attestation has live fields")
            else:
                rule = document["payload"].get("invalidation_rule")
                if (
                    document["payload"].get("observed_at") is None
                    or not isinstance(rule, dict)
                    or set(rule) != {"required_facts"}
                    or not isinstance(rule["required_facts"], list)
                    or not rule["required_facts"]
                ):
                    raise ProvenanceError("live attestation invalidation rule is invalid")
        elif role == "authority":
            decision = parents_by_edge["decision"]
            attestation = parents_by_edge["attestation"]
            if decision["role"] != "decision":
                raise ProvenanceError("authority decision parent has the wrong role")
            if attestation["role"] != "attestation":
                raise ProvenanceError("authority attestation parent has the wrong role")
            if attestation["payload"].get("subject_root") != decision["node_id"]:
                raise ProvenanceError("authority attestation validates a different decision")
            if attestation["payload"].get("verdict") != "ready":
                raise ProvenanceError("authority requires a ready decision attestation")
        elif role == "execution" and parents_by_edge["authority"]["role"] != "authority":
            raise ProvenanceError("execution authority parent has the wrong role")
        elif role == "outcome" and parents_by_edge["execution"]["role"] != "execution":
            raise ProvenanceError("outcome execution parent has the wrong role")
        active.remove(node_id)
        visited.add(node_id)
        return document

    root = visit(root_id)
    return {"root_id": root_id, "root_role": root["role"], "node_count": len(visited)}


def collect_chain(
    root_id: str, load: Callable[[str], dict[str, Any]]
) -> list[dict[str, Any]]:
    verify_chain(root_id, load)
    collected: dict[str, dict[str, Any]] = {}

    def visit(node_id: str) -> None:
        if node_id in collected:
            return
        node = load(node_id)
        for parent in node["parents"]:
            visit(parent["node_id"])
        collected[node_id] = node

    visit(root_id)
    return list(collected.values())
