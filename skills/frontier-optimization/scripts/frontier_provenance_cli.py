#!/usr/bin/env python3
"""Apply one typed Frontier provenance operation from a JSON request."""

from __future__ import annotations

import argparse
import json
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
    WorkflowReleaseGitStore,
)
from frontier_provenance.handoff import export_handoff, verify_handoff
from frontier_provenance.git_content import ContentSession, verify_retained_artifact


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
    if operation == "verify-artifact":
        require_fields(request, operation, {"path", "sha256", "size"})
        return verify_retained_artifact(Path(request["path"]), sha256=request["sha256"], size=request["size"])
    elif operation == "export-handoff":
        require_fields(request, operation, {"root_id", "content_bindings", "destination"})
        manifest = export_handoff(
            request["root_id"],
            repository,
            request["content_bindings"],
            Path(request["destination"]),
        )
        return {"handoff_id": manifest["handoff_id"], "root_id": manifest["root_id"]}
    elif operation == "verify-handoff":
        require_fields(request, operation, {"path", "repo_root"} if "repo_root" in request else {"path"})
        return verify_handoff(Path(request["path"]),
            repo_root=Path(request["repo_root"]) if "repo_root" in request else None)
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
        return {"content_root": manifest["content_root"], "adapter": manifest["storage"]["adapter"]}
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
            {"authority_root", "decision_id", "attestation_id", "content_bindings"},
        )
        decision = repository.load(request["decision_id"])
        content = ContentSession(request["content_bindings"])
        node = bind_authority(
            authority_root=request["authority_root"],
            decision=decision,
            validation=repository.load(request["attestation_id"]),
            decision_content=content.resolve(decision["artifact_roots"][0]),
        )
    elif operation == "freeze-execution":
        legacy_fields = {"authority_id", "starting_state_root"}
        routine_fields = legacy_fields | {
            "content_bindings",
            "routine_admission",
            "live_facts",
            "checked_at",
        }
        current_fields = routine_fields - {"routine_admission"}
        observed = set(request) - {"contract_version", "operation"}
        if observed == legacy_fields:
            require_fields(request, operation, legacy_fields)
            node = freeze_execution(
                authority=repository.load(request["authority_id"]),
                starting_state_root=request["starting_state_root"],
            )
        elif observed in (routine_fields, current_fields):
            require_fields(request, operation, observed)
            content = ContentSession(request["content_bindings"])
            node = freeze_execution(
                authority=repository.load(request["authority_id"]),
                starting_state_root=request["starting_state_root"],
                routine_admission=request.get("routine_admission"),
                repository=repository,
                resolve_content=content.resolve,
                read_content=content.read,
                live_facts=request["live_facts"],
                checked_at=request["checked_at"],
            )
        else:
            raise ProvenanceError(
                "freeze-execution request fields must be exactly one complete legacy or routine shape"
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
        content = ContentSession(request["content_bindings"])
        return verify_for(
            request["root_id"],
            repository.load,
            content.resolve,
            consequence=request["consequence"],
            live_facts=request["live_facts"],
            checked_at=request["checked_at"],
            read_content=content.read,
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
    """Compatibility helper; multi-consumer operations share one ContentSession."""
    return ContentSession(bindings).resolve


def content_bundle_path(bindings: Any, content_root: str) -> Path:
    content = ContentSession(bindings)
    content.resolve(content_root)
    return content.paths[content_root]


def content_reader(bindings: Any):
    return ContentSession(bindings).read


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
