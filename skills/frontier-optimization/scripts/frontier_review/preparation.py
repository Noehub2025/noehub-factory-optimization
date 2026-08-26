"""Validate a mutable draft, then atomically seal one complete review subject."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any

import yaml

from frontier_provenance import NodeRepository, ProvenanceError, freeze_decision
from frontier_provenance.content import canonical_json
from frontier_provenance.git_content import GitReferenceStore
from frontier_provenance.review_contract import (
    ENTRY_STAGES,
    ROLE_ADAPTER_CONTRACT,
    REVIEW_KINDS,
    validate_and_project,
)
from frontier_provenance.review_subject import SUBJECT_CONTRACT
from frontier_provenance.stores import (
    ArtifactSource,
    ClosedCollection,
)


PREPARATION_CONTRACT = "frontier-review-preparation/1"
PACKET_CONTRACT = "frontier-review-packet/1"
ASSIGNMENT_CONTRACT = "frontier-review-assignment/1"
INDEX_LOGICAL_NAME = "project/decision/review-subject-index.json"
SELF_ID_RULE = re.compile(
    r"^(?P<prefix>[A-Za-z0-9_.-]+-sha256) of exact UTF-8 bytes with the complete "
    r"(?P<field>[A-Za-z][A-Za-z0-9_]*) line omitted$"
)
SELF_ID_RULE_WITHOUT_PREFIX = re.compile(
    r"^exact UTF-8 bytes with the complete (?P<field>[A-Za-z][A-Za-z0-9_]*) line omitted$"
)
SELF_ID_REMOVE_LINE_RULE = re.compile(
    r"^Remove the complete (?P<field>[A-Za-z][A-Za-z0-9_]*) line, then compute "
    r"SHA-256 over the remaining UTF-8 file bytes including the final newline\.$"
)
SELF_ID_SHA_RULE = re.compile(
    r"^SHA-256 of these UTF-8 bytes with the (?P<field>[A-Za-z][A-Za-z0-9_]*) "
    r"line omitted(?:;.*)?$"
)
DESIGN_TRACEABILITY_IDENTITY_RULE = (
    "SHA-256 of these UTF-8 bytes with the design_contract_identity line omitted"
)
SHA256_DIGEST = re.compile(r"^[0-9a-f]{64}$")
RECORD_HEADING = re.compile(
    r"^#{1,6}\s+([A-Z]{1,3}\d{3})\b([^\n]*)$", re.MULTILINE
)


def prepare_review(
    draft_spec: dict[str, Any], project_root: Path, output_root: Path
) -> dict[str, Any]:
    """Return NOT_READY findings or atomically publish one SEALED review subject."""

    findings: list[dict[str, str]] = []
    try:
        normalized = _normalize_spec(draft_spec, project_root)
        captured = _read_and_validate(normalized, project_root)
    except ProvenanceError as exc:
        findings.append({"code": "DRAFT_INVALID", "message": str(exc)})
        return {"status": "NOT_READY", "findings": findings}

    project_root = project_root.resolve()
    try:
        output_root = _output_path(output_root, project_root)
    except ProvenanceError as exc:
        return {
            "status": "NOT_READY",
            "findings": [{"code": "OUTPUT_INVALID", "message": str(exc)}],
        }
    if output_root.exists():
        return {
            "status": "NOT_READY",
            "findings": [
                {
                    "code": "OUTPUT_EXISTS",
                    "message": f"review output already exists: {output_root}",
                }
            ],
        }

    output_root.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(
        tempfile.mkdtemp(prefix=f".{output_root.name}.", dir=output_root.parent)
    )
    published = False
    try:
        normalized["semantic_projection"] = captured["semantic_projection"]
        review_id = _next_review_id(captured["raw_by_name"])
        index = _subject_index(normalized, review_id)
        sources = list(normalized["sources"])
        snapshot = staging / "snapshot"
        manifest = GitReferenceStore(project_root).capture(
            "decision",
            sources,
            snapshot,
            closed_collections=normalized["closed_collections"],
            subject_index=index,
            expected_bytes=captured["raw_by_name"],
        )
        _assert_frozen_bytes(manifest, captured["raw_by_name"], canonical_json(index) + b"\n")

        decision = freeze_decision(decision_root=manifest["content_root"])
        repository = NodeRepository(staging / "nodes")
        decision_path = repository.write(decision)
        packet = {
            "contract_version": PACKET_CONTRACT,
            "review_id": review_id,
            "review_kind": normalized["review_kind"],
            "subject": {
                "mode": "complete",
                "content_root": manifest["content_root"],
                "decision_root": decision["node_id"],
                "bundle": "snapshot",
                "index": INDEX_LOGICAL_NAME,
            },
            "completion_check": _completion_check(normalized["review_kind"]),
        }
        packet_path = staging / "review-packet.json"
        packet_path.write_bytes(canonical_json(packet) + b"\n")
        assignment = {
            "contract_version": ASSIGNMENT_CONTRACT,
            "review_id": review_id,
            "review_kind": normalized["review_kind"],
            "exclusive_reviewer": "review-frontier/1",
            "packet": "review-packet.json",
            "subject_decision_root": decision["node_id"],
            "allowed_outputs": _allowed_outputs(
                normalized["review_kind"], normalized["semantic_projection"]
            ),
        }
        assignment_path = staging / "review-assignment.json"
        assignment_path.write_bytes(canonical_json(assignment) + b"\n")
        # Draft semantics and chosen Git bytes were checked above, once.
        os.replace(staging, output_root)
        published = True
        return {
            "status": "SEALED",
            "review_id": review_id,
            "content_root": manifest["content_root"],
            "decision_root": decision["node_id"],
            "review_packet": str(output_root / "review-packet.json"),
            "review_assignment": str(output_root / "review-assignment.json"),
        }
    except (OSError, ProvenanceError) as exc:
        return {
            "status": "NOT_READY",
            "findings": [{"code": "SEAL_FAILED", "message": str(exc)}],
        }
    finally:
        if not published and staging.exists():
            shutil.rmtree(staging)


def _normalize_spec(value: Any, project_root: Path) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {
        "contract_version",
        "review_kind",
        "artifacts",
        "closed_collections",
        "semantic_projection",
    }:
        raise ProvenanceError("review draft has unknown or missing fields")
    if value["contract_version"] != PREPARATION_CONTRACT:
        raise ProvenanceError(f"review draft contract must be {PREPARATION_CONTRACT}")
    review_kind = value["review_kind"]
    if review_kind not in REVIEW_KINDS:
        raise ProvenanceError(f"unsupported review kind: {review_kind!r}")
    projection_request = value["semantic_projection"]
    if not isinstance(projection_request, dict):
        raise ProvenanceError("semantic_projection must be a mapping")
    expected_projection_keys = {"review_stage"} if review_kind == "entry" else set()
    if set(projection_request) != expected_projection_keys:
        raise ProvenanceError(
            "semantic_projection accepts only review-stage control; all consequence "
            "fields are derived from canonical project objects"
        )
    review_stage = projection_request.get("review_stage")
    if review_kind == "entry" and review_stage not in ENTRY_STAGES:
        raise ProvenanceError("entry review_stage is invalid")

    artifacts = value["artifacts"]
    if not isinstance(artifacts, list) or not artifacts:
        raise ProvenanceError("review draft requires project artifacts")
    sources: list[ArtifactSource] = []
    seen: set[str] = set()
    root = project_root.resolve()
    for index, item in enumerate(artifacts):
        if not isinstance(item, dict) or set(item) != {
            "logical_name",
            "path",
            "kind",
            "behavioral_metadata",
        }:
            raise ProvenanceError(f"artifacts[{index}] is invalid")
        name = item["logical_name"]
        if name == INDEX_LOGICAL_NAME:
            raise ProvenanceError("the review subject index is generated by prepare_review")
        if name in seen:
            raise ProvenanceError(f"duplicate review artifact: {name}")
        seen.add(name)
        path = Path(item["path"])
        if not path.is_absolute():
            path = root / path
        sources.append(
            ArtifactSource(name, path, item["kind"], item["behavioral_metadata"])
        )
    collections = value["closed_collections"]
    if not isinstance(collections, list):
        raise ProvenanceError("closed_collections must be a list")
    closed: list[ClosedCollection] = []
    for index, item in enumerate(collections):
        if not isinstance(item, dict) or set(item) != {"logical_name", "directory", "members"}:
            raise ProvenanceError(f"closed_collections[{index}] is invalid")
        if not isinstance(item["members"], list) or not item["members"]:
            raise ProvenanceError(f"closed_collections[{index}].members is invalid")
        directory = Path(item["directory"])
        if not directory.is_absolute():
            directory = root / directory
        closed.append(
            ClosedCollection(item["logical_name"], directory, tuple(item["members"]))
        )
    return {
        "review_kind": review_kind,
        "review_stage": review_stage,
        "sources": sources,
        "closed_collections": closed,
    }


def _read_and_validate(spec: dict[str, Any], project_root: Path) -> dict[str, Any]:
    raw_by_name: dict[str, bytes] = {}
    parsed_by_name: dict[str, Any] = {}
    self_ids_by_path: dict[Path, dict[str, str]] = {}
    source_by_path: dict[Path, ArtifactSource] = {}
    root = project_root.resolve()
    for source in spec["sources"]:
        path = source.path
        if path.is_symlink() or not path.is_file():
            raise ProvenanceError(f"review artifact is missing or unsafe: {path}")
        resolved = path.resolve()
        try:
            resolved.relative_to(root)
        except ValueError as exc:
            raise ProvenanceError(f"review artifact is outside project_root: {path}") from exc
        raw = resolved.read_bytes()
        raw_by_name[source.logical_name] = raw
        if resolved in source_by_path:
            raise ProvenanceError(
                f"one project file has multiple review roles: {resolved}"
            )
        source_by_path[resolved] = source
        parsed = _parse_document(resolved, raw, logical_name=source.logical_name)
        parsed_by_name[source.logical_name] = parsed
        declared = _validate_self_identity(
            resolved,
            raw,
            parsed,
            logical_name=source.logical_name,
        )
        if declared:
            self_ids_by_path[resolved] = declared

    _validate_entry_design_traceability_binding(
        spec,
        parsed_by_name,
        raw_by_name,
        source_by_path,
        root,
    )

    collection_projection = [
        {"logical_name": item.logical_name, "members": list(item.members)}
        for item in spec["closed_collections"]
    ]
    semantic_projection = validate_and_project(
        spec["review_kind"],
        raw_by_name,
        review_stage=spec["review_stage"],
        closed_collections=collection_projection,
    )
    _validate_cross_file_bindings(parsed_by_name, source_by_path, self_ids_by_path, root)
    _validate_record_namespaces(raw_by_name, parsed_by_name)
    return {
        "raw_by_name": raw_by_name,
        "semantic_projection": semantic_projection,
    }


def _parse_document(path: Path, raw: bytes, *, logical_name: str) -> Any:
    is_traceability = _is_design_traceability_logical_name(logical_name)
    if not is_traceability and path.suffix.lower() not in {".yaml", ".yml", ".json"}:
        return None
    try:
        return yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise ProvenanceError(f"structured review artifact is invalid: {path}: {exc}") from exc


def _validate_self_identity(
    path: Path,
    raw: bytes,
    parsed: Any,
    *,
    logical_name: str,
) -> dict[str, str]:
    if not isinstance(parsed, dict) or "identity_rule" not in parsed:
        return {}
    rule = parsed["identity_rule"]
    if not isinstance(rule, str):
        raise ProvenanceError(f"identity_rule must be text: {path}")
    if _is_design_traceability_normalization_rule(logical_name, parsed):
        return {}
    match = SELF_ID_RULE.fullmatch(rule)
    prefixless = SELF_ID_RULE_WITHOUT_PREFIX.fullmatch(rule)
    remove_line = SELF_ID_REMOVE_LINE_RULE.fullmatch(rule)
    sha_rule = SELF_ID_SHA_RULE.fullmatch(rule)
    recognized = match or prefixless or remove_line or sha_rule
    if recognized is None:
        raise ProvenanceError(f"unsupported identity_rule in {path}")
    field = recognized.group("field")
    declared = parsed.get(field)
    if not isinstance(declared, str):
        raise ProvenanceError(f"{field} is missing from {path}")
    digest = _omit_top_level_field(raw, field)
    if match is not None:
        prefix = match.group("prefix") + ":"
    else:
        if ":" not in declared:
            raise ProvenanceError(f"{field} has no identity prefix in {path}")
        prefix = declared.rsplit(":", 1)[0] + ":"
    expected = prefix + digest
    if declared != expected:
        raise ProvenanceError(
            f"{path} declares {declared}, but final raw bytes derive {expected}"
        )
    return {field: declared}


def _is_design_traceability_logical_name(logical_name: str) -> bool:
    return logical_name.startswith(
        "project/decision/design/"
    ) and logical_name.endswith("/traceability.yaml")


def _is_design_traceability_normalization_rule(
    logical_name: str, document: dict[str, Any]
) -> bool:
    if not _is_design_traceability_logical_name(logical_name):
        return False
    if document.get("identity_rule") != DESIGN_TRACEABILITY_IDENTITY_RULE:
        return False
    if not isinstance(document.get("design_contract_identity"), str):
        raise ProvenanceError(
            "design traceability normalization requires design_contract_identity"
        )
    return True


def _validate_entry_design_traceability_binding(
    spec: dict[str, Any],
    parsed_by_name: dict[str, Any],
    raw_by_name: dict[str, bytes],
    source_by_path: dict[Path, ArtifactSource],
    project_root: Path,
) -> None:
    """Bind one W-backed Entry to the exact captured traceability source."""

    if spec["review_kind"] != "entry":
        return
    plans = [
        document
        for logical_name, document in parsed_by_name.items()
        if logical_name.startswith("project/decision/entry/")
        and isinstance(document, dict)
        and document.get("contract_version") == "frontier-project-batch-plan/3"
    ]
    if len(plans) != 1 or plans[0].get("design_profile") not in {"module", "system"}:
        return
    plan = plans[0]
    binding = plan.get("design_traceability")
    if not isinstance(binding, dict):
        raise ProvenanceError(
            "W-backed entry design_traceability binding must be a mapping"
        )
    path_value = binding.get("path")
    if not isinstance(path_value, str) or not path_value.strip():
        raise ProvenanceError(
            "W-backed entry design_traceability path must be nonempty text"
        )
    expected_digest = _sha256_digest(binding.get("sha256"))

    bound_path = Path(path_value)
    if not bound_path.is_absolute():
        bound_path = project_root / bound_path
    bound_path = bound_path.resolve()
    try:
        bound_path.relative_to(project_root)
    except ValueError as exc:
        raise ProvenanceError(
            "W-backed entry design_traceability path is outside project_root"
        ) from exc
    bound_source = source_by_path.get(bound_path)
    if bound_source is None:
        raise ProvenanceError(
            "W-backed entry design_traceability path is absent from the review subject"
        )

    design_identity = plan.get("design_contract_identity")
    matching_names = [
        logical_name
        for logical_name, document in parsed_by_name.items()
        if _is_design_traceability_logical_name(logical_name)
        and isinstance(document, dict)
        and document.get("design_contract_identity") == design_identity
    ]
    if len(matching_names) != 1 or bound_source.logical_name != matching_names[0]:
        raise ProvenanceError(
            "W-backed entry design_traceability path does not carry the canonical traceability role"
        )
    actual_digest = hashlib.sha256(raw_by_name[bound_source.logical_name]).hexdigest()
    if actual_digest != expected_digest:
        raise ProvenanceError(
            "W-backed entry design_traceability whole-file SHA-256 does not match the plan binding"
        )


def _sha256_digest(value: Any) -> str:
    if not isinstance(value, str):
        raise ProvenanceError("W-backed entry design_traceability sha256 must be text")
    digest = value.removeprefix("sha256:")
    if SHA256_DIGEST.fullmatch(digest) is None:
        raise ProvenanceError("W-backed entry design_traceability sha256 is invalid")
    return digest


def _omit_top_level_field(raw: bytes, field: str) -> str:
    marker = f"{field}:".encode()
    kept: list[bytes] = []
    found = 0
    for line in raw.splitlines(keepends=True):
        if line.startswith(marker):
            found += 1
        else:
            kept.append(line)
    if found != 1:
        raise ProvenanceError(f"source must contain exactly one top-level {field} line")
    return hashlib.sha256(b"".join(kept)).hexdigest()


def _validate_cross_file_bindings(
    parsed_by_name: dict[str, Any],
    source_by_path: dict[Path, ArtifactSource],
    self_ids_by_path: dict[Path, dict[str, str]],
    project_root: Path,
) -> None:
    control_prefixes = (
        "project/decision/entry/",
        "project/decision/replan/",
        "project/decision/implementation/",
        "project/decision/claims/",
    )
    for logical_name, document in parsed_by_name.items():
        if not (
            logical_name.startswith(control_prefixes)
            or logical_name == "project/decision/selection/evidence-state.yaml"
        ):
            continue
        for mapping in _mappings(document):
            for key, value in mapping.items():
                if key != "path" and not key.endswith("_path"):
                    continue
                if not isinstance(value, str):
                    continue
                target = (project_root / value).resolve()
                source = source_by_path.get(target)
                stem = key.removesuffix("_path")
                binding_keys = {
                    candidate
                    for candidate in (
                        "file_sha256",
                        stem + "_sha256",
                        stem + "_id",
                        stem + "_identity",
                    )
                    if candidate in mapping
                }
                if key == "path":
                    binding_keys.update(
                        candidate
                        for candidate in mapping
                        if candidate.endswith(("_id", "_identity"))
                    )
                if source is None:
                    delayed_binding = binding_keys and all(
                        isinstance(mapping[candidate], str)
                        and mapping[candidate].startswith(("$late.", "$derived."))
                        for candidate in binding_keys
                    )
                    if binding_keys and not delayed_binding:
                        raise ProvenanceError(
                            f"bound project path is absent from the review subject: {value}"
                        )
                    continue
                raw = source.path.resolve().read_bytes()
                digest_key = "file_sha256" if "file_sha256" in mapping else stem + "_sha256"
                if digest_key in mapping and mapping[digest_key] != hashlib.sha256(raw).hexdigest():
                    raise ProvenanceError(
                        f"{value} does not match bound {digest_key}"
                    )
                for identity_field, identity in self_ids_by_path.get(target, {}).items():
                    if identity_field in mapping and mapping[identity_field] != identity:
                        raise ProvenanceError(
                            f"{value} does not match bound {identity_field}"
                        )


def _mappings(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _mappings(child)
    elif isinstance(value, list):
        for child in value:
            yield from _mappings(child)


def _validate_record_namespaces(
    raw_by_name: dict[str, bytes], parsed_by_name: dict[str, Any]
) -> None:
    assigned: dict[str, list[str]] = {}
    active_b_v = {
        value
        for logical_name, document in parsed_by_name.items()
        if logical_name.startswith(
            (
                "project/decision/entry/",
                "project/decision/replan/",
                "project/decision/implementation/",
                "project/decision/claims/",
            )
        )
        for mapping in _mappings(document)
        for key, value in mapping.items()
        if key in {"batch_id", "decision_id"}
        and isinstance(value, str)
        and re.fullmatch(r"[BV]\d{3}", value)
    }
    for name, raw in raw_by_name.items():
        if not name.endswith("/ledger.md"):
            continue
        text = raw.decode("utf-8", errors="strict")
        for record_id, tail in RECORD_HEADING.findall(text):
            prior = assigned.setdefault(record_id, [])
            if prior and not record_id.startswith(("B", "V")):
                raise ProvenanceError(
                    f"record identifier {record_id} is assigned more than once"
                )
            prior.append(tail.strip())
    for record_id in active_b_v:
        canonical_assignments = sum(
            heading.startswith(":") for heading in assigned.get(record_id, [])
        )
        if canonical_assignments > 1:
            raise ProvenanceError(
                f"record identifier {record_id} has conflicting repeated meanings"
            )
    for name, document in parsed_by_name.items():
        if not isinstance(document, dict):
            continue
        event_id = document.get("event_id")
        if isinstance(event_id, str) and RECORD_HEADING.fullmatch(f"## {event_id}"):
            if event_id not in assigned:
                raise ProvenanceError(
                    f"structured event {event_id} in {name} has no unique ledger assignment"
                )


def _next_review_id(raw_by_name: dict[str, bytes]) -> str:
    maximum = 0
    pattern = re.compile(r"^#{1,6}\s+R(\d{3})\b", re.MULTILINE)
    for name, raw in raw_by_name.items():
        if name.endswith("/ledger.md"):
            for value in pattern.findall(raw.decode("utf-8", errors="strict")):
                maximum = max(maximum, int(value))
    return f"R{maximum + 1:03d}"


def _subject_index(spec: dict[str, Any], review_id: str) -> dict[str, Any]:
    members = sorted(source.logical_name for source in spec["sources"])
    collections = sorted(
        (
            {
                "logical_name": item.logical_name,
                "members": sorted(item.members),
            }
            for item in spec["closed_collections"]
        ),
        key=lambda item: item["logical_name"],
    )
    return {
        "contract_version": SUBJECT_CONTRACT,
        "role_adapter": ROLE_ADAPTER_CONTRACT,
        "review_id": review_id,
        "review_kind": spec["review_kind"],
        "subject_mode": "complete",
        "members": members,
        "closed_collections": collections,
        "semantic_projection": spec["semantic_projection"],
    }


def _assert_frozen_bytes(
    manifest: dict[str, Any], raw_by_name: dict[str, bytes], index_raw: bytes
) -> None:
    expected = {name: hashlib.sha256(raw).hexdigest() for name, raw in raw_by_name.items()}
    expected[INDEX_LOGICAL_NAME] = hashlib.sha256(index_raw).hexdigest()
    observed = {item["logical_name"]: item["content_sha256"] for item in manifest["artifacts"]}
    if observed != expected:
        raise ProvenanceError("captured bytes changed after draft validation")






def _output_path(value: Path, project_root: Path) -> Path:
    output = value if value.is_absolute() else project_root / value
    output = output.resolve()
    try:
        output.relative_to(project_root)
    except ValueError as exc:
        raise ProvenanceError("review output must stay under project_root") from exc
    return output


def _completion_check(review_kind: str) -> str:
    check = (
        f"Review the one complete {review_kind} project-decision root. Verify its subject "
        "index, exact members, closed collections, semantic projection, project bindings, "
        "and consequence gates. Write one immutable finding report for this decision only."
    )
    if review_kind == "entry":
        check += (
            " For a repaired Entry, apply entry-review.md#entry-repair-review: inspect "
            "the change and its consequences and briefly cite applicable earlier "
            "conclusions; completeness does not require repeating unaffected review."
        )
    return check


def _allowed_outputs(review_kind: str, projection: dict[str, Any]) -> list[str]:
    if review_kind == "entry":
        positive = (
            "AUTHORIZATION_READY"
            if projection["review_stage"] == "authorization-readiness"
            else "ENTRY_READY"
        )
        return [
            positive,
            "ENTRY_REPAIR_REQUIRED",
            "EVIDENCE_REQUIRED",
            "PARENT_REVIEW_REQUIRED",
            "BLOCKED",
        ]
    return {
        "replan": ["REPLAN_READY", "REPLAN_REPAIR_REQUIRED", "EVIDENCE_REQUIRED", "PARENT_REVIEW_REQUIRED", "BLOCKED"],
        "design": ["DESIGN_READY", "DESIGN_REPAIR_REQUIRED", "EVIDENCE_REQUIRED", "PARENT_REVIEW_REQUIRED", "BLOCKED"],
        "implementation": ["IMPLEMENTATION_READY", "IMPLEMENTATION_REPAIR_REQUIRED", "EVIDENCE_REQUIRED", "PARENT_REVIEW_REQUIRED", "BLOCKED"],
        "claims": ["CLAIMS_SUPPORTED", "CLAIMS_DOWNGRADED", "EVIDENCE_REQUIRED", "PARENT_REVIEW_REQUIRED", "BLOCKED"],
    }[review_kind]
