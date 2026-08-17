#!/usr/bin/env python3
"""Apply one typed Frontier provenance operation from a JSON request."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any

from frontier_provenance import (
    NodeRepository,
    ProvenanceError,
    attest,
    bind_authority,
    export_chain,
    freeze_decision,
    freeze_execution,
    record_outcome,
    verify_for,
)
from frontier_provenance.content import canonical_json
from frontier_provenance.stores import (
    ArtifactSource,
    ClosedCollection,
    ProjectPortableStore,
    PortableBundleStore,
    WorkflowReleaseGitStore,
)
from frontier_provenance.handoff import export_handoff, verify_handoff


REQUEST_CONTRACT = "frontier-provenance-operation/4"


def load_mapping(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise ProvenanceError(f"request is unreadable: {exc}") from exc
    if not isinstance(value, dict):
        raise ProvenanceError("request must be a JSON object")
    return value


def require_fields(request: dict[str, Any], operation: str, fields: set[str]) -> None:
    expected = {"contract_version", "operation", *fields}
    if set(request) != expected:
        raise ProvenanceError(
            f"{operation} request fields must be exactly {sorted(expected)}"
        )
    if request["contract_version"] != REQUEST_CONTRACT:
        raise ProvenanceError(f"request contract must be {REQUEST_CONTRACT}")


def apply_operation(request: dict[str, Any], repository: NodeRepository) -> dict[str, Any]:
    operation = request.get("operation")
    if operation == "export-handoff":
        require_fields(request, operation, {"root_id", "content_bindings", "destination"})
        manifest = export_handoff(
            request["root_id"],
            repository,
            handoff_exports(request["content_bindings"]),
            Path(request["destination"]),
        )
        return {"handoff_id": manifest["handoff_id"], "root_id": manifest["root_id"]}
    elif operation == "verify-handoff":
        require_fields(request, operation, {"path"})
        return verify_handoff(Path(request["path"]))
    elif operation == "capture-project":
        require_fields(
            request,
            operation,
            {
                "role",
                "project_root",
                "artifacts",
                "closed_collections",
                "destination",
            },
        )
        sources, collections = capture_inputs(request)
        manifest = ProjectPortableStore().capture(
            request["role"],
            sources,
            Path(request["destination"]),
            project_root=Path(request["project_root"]),
            closed_collections=collections,
        )
        return {"content_root": manifest["content_root"], "adapter": "portable-bundle/1"}
    elif operation == "capture-release-git":
        require_fields(
            request,
            operation,
            {"artifacts", "closed_collections", "repo_root", "reference", "created_at", "manifest_output"},
        )
        sources, collections = capture_inputs(request)
        output = Path(request["manifest_output"])
        if output.exists():
            raise ProvenanceError(f"manifest output already exists: {output}")
        manifest = WorkflowReleaseGitStore(
            Path(request["repo_root"]), request["reference"]
        ).capture_release(
            sources,
            closed_collections=collections,
            created_at=request["created_at"],
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(canonical_json(manifest) + b"\n")
        return {"content_root": manifest["content_root"], "adapter": "git-snapshot/1", "manifest": str(output)}
    elif operation == "verify-release-git":
        require_fields(
            request,
            operation,
            {"repo_root", "reference", "manifest_path"},
        )
        manifest = load_mapping(Path(request["manifest_path"]))
        return WorkflowReleaseGitStore(
            Path(request["repo_root"]), request["reference"]
        ).verify(manifest)
    elif operation == "freeze-decision":
        require_fields(request, operation, {"decision_root"})
        node = freeze_decision(
            decision_root=request["decision_root"],
        )
    elif operation == "attest":
        require_fields(
            request,
            operation,
            {
                "subject_id",
                "validation_report_root",
                "verdict",
                "findings",
                "freshness",
                "observed_at",
                "expires_at",
                "invalidation_rule",
            },
        )
        node = attest(
            repository.load(request["subject_id"]),
            validation_report_root=request["validation_report_root"],
            verdict=request["verdict"],
            findings=request["findings"],
            freshness=request["freshness"],
            observed_at=request["observed_at"],
            expires_at=request["expires_at"],
            invalidation_rule=request["invalidation_rule"],
        )
    elif operation == "bind-authority":
        require_fields(
            request,
            operation,
            {"authority_root", "decision_id", "attestation_id"},
        )
        node = bind_authority(
            authority_root=request["authority_root"],
            decision=repository.load(request["decision_id"]),
            validation=repository.load(request["attestation_id"]),
        )
    elif operation == "freeze-execution":
        require_fields(
            request,
            operation,
            {"authority_id", "starting_state_root"},
        )
        node = freeze_execution(
            authority=repository.load(request["authority_id"]),
            starting_state_root=request["starting_state_root"],
        )
    elif operation == "record-outcome":
        require_fields(
            request,
            operation,
            {"execution_id", "outcome_root"},
        )
        node = record_outcome(
            execution=repository.load(request["execution_id"]),
            outcome_root=request["outcome_root"],
        )
    elif operation == "verify":
        require_fields(
            request,
            operation,
            {"root_id", "consequence", "live_facts", "checked_at", "content_bindings"},
        )
        resolver = content_resolver(request["content_bindings"])
        return verify_for(
            request["root_id"],
            repository.load,
            resolver,
            consequence=request["consequence"],
            live_facts=request["live_facts"],
            checked_at=request["checked_at"],
        )
    elif operation == "export":
        require_fields(request, operation, {"root_id"})
        return {"root_id": request["root_id"], "nodes": export_chain(request["root_id"], repository.load)}
    else:
        raise ProvenanceError(f"unsupported provenance operation: {operation!r}")
    path = repository.write(node)
    return {"node_id": node["node_id"], "role": node["role"], "path": str(path)}


def capture_inputs(request: dict[str, Any]) -> tuple[list[ArtifactSource], list[ClosedCollection]]:
    artifacts = request["artifacts"]
    collections = request["closed_collections"]
    if not isinstance(artifacts, list) or not artifacts:
        raise ProvenanceError("capture artifacts must be a nonempty list")
    sources: list[ArtifactSource] = []
    for index, item in enumerate(artifacts):
        if not isinstance(item, dict) or set(item) != {
            "logical_name", "path", "kind", "behavioral_metadata"
        }:
            raise ProvenanceError(f"artifacts[{index}] is invalid")
        sources.append(
            ArtifactSource(
                item["logical_name"],
                Path(item["path"]),
                item["kind"],
                item["behavioral_metadata"],
            )
        )
    if not isinstance(collections, list):
        raise ProvenanceError("closed_collections must be a list")
    closed: list[ClosedCollection] = []
    for index, item in enumerate(collections):
        if not isinstance(item, dict) or set(item) != {"logical_name", "directory", "members"}:
            raise ProvenanceError(f"closed_collections[{index}] is invalid")
        if not isinstance(item["members"], list):
            raise ProvenanceError(f"closed_collections[{index}].members is invalid")
        closed.append(
            ClosedCollection(
                item["logical_name"], Path(item["directory"]), tuple(item["members"])
            )
        )
    return sources, closed


def content_resolver(bindings: Any):
    if not isinstance(bindings, list):
        raise ProvenanceError("content_bindings must be a list")
    resolved: dict[str, dict[str, Any]] = {}
    for index, binding in enumerate(bindings):
        if not isinstance(binding, dict) or "adapter" not in binding:
            raise ProvenanceError(f"content_bindings[{index}] is invalid")
        adapter = binding["adapter"]
        if adapter == "portable-bundle/1" and set(binding) == {"adapter", "path"}:
            result = PortableBundleStore().verify(Path(binding["path"]))
        else:
            raise ProvenanceError(
                f"content_bindings[{index}] must be a portable project bundle"
            )
        content_root = result["content_root"]
        if content_root in resolved:
            raise ProvenanceError(f"duplicate content binding: {content_root}")
        resolved[content_root] = result

    def resolve(content_root: str) -> dict[str, Any]:
        if content_root not in resolved:
            raise ProvenanceError(f"content root has no resolver binding: {content_root}")
        return resolved[content_root]

    return resolve


def handoff_exports(bindings: Any):
    if not isinstance(bindings, list):
        raise ProvenanceError("content_bindings must be a list")
    exports = {}
    for index, binding in enumerate(bindings):
        if not isinstance(binding, dict) or "adapter" not in binding:
            raise ProvenanceError(f"content_bindings[{index}] is invalid")
        if binding["adapter"] == "portable-bundle/1" and set(binding) == {"adapter", "path"}:
            source = Path(binding["path"])
            result = PortableBundleStore().verify(source)

            def copy(destination: Path, source: Path = source) -> None:
                shutil.copytree(source, destination)

            exporter = copy
        else:
            raise ProvenanceError(
                f"content_bindings[{index}] must be a portable project bundle"
            )
        root = result["content_root"]
        if root in exports:
            raise ProvenanceError(f"duplicate content binding: {root}")
        exports[root] = exporter
    return exports


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()
    try:
        result = apply_operation(
            load_mapping(arguments.request), NodeRepository(arguments.repository)
        )
    except ProvenanceError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    raw = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if arguments.output is None:
        print(raw, end="")
    else:
        arguments.output.write_text(raw)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
