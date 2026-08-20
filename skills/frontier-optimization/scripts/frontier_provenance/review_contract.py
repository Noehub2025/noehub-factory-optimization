"""Review-kind role adapters for complete Frontier project decisions."""

from __future__ import annotations

import hashlib
import json
from typing import Any

import yaml

from .content import ProvenanceError


ROLE_ADAPTER_CONTRACT = "frontier-review-role-adapter/1"
REVIEW_KINDS = {"entry", "replan", "design", "implementation", "claims"}
ENTRY_STAGES = {"authorization-readiness", "spend-readiness"}
OVERLAY_ROLES = {"repair", "correction", "supplement", "overlay"}
OVERLAY_KEYS = {
    "replacement_order",
    "supplement_of",
    "overlay_of",
    "correction_of",
    "base_content_root",
    "base_decision_root",
}


def validate_and_project(
    review_kind: str,
    raw_by_name: dict[str, bytes],
    *,
    review_stage: str | None = None,
    closed_collections: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Validate one complete role set and derive its semantic projection."""

    if review_kind not in REVIEW_KINDS:
        raise ProvenanceError(f"unsupported review kind: {review_kind!r}")
    parsed = {name: _parse(name, raw) for name, raw in raw_by_name.items()}
    _reject_overlay_semantics(parsed)
    collections = closed_collections or []
    return {
        "entry": _entry_projection,
        "replan": _replan_projection,
        "design": lambda parsed, stage, collections: _design_projection(
            parsed, stage, collections, raw_by_name
        ),
        "implementation": _implementation_projection,
        "claims": _claims_projection,
    }[review_kind](parsed, review_stage, collections)


def _parse(name: str, raw: bytes) -> Any:
    suffix = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    if suffix not in {"yaml", "yml", "json"}:
        return None
    try:
        return yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise ProvenanceError(f"structured review member is invalid: {name}: {exc}") from exc


def _reject_overlay_semantics(parsed: dict[str, Any]) -> None:
    for name, document in parsed.items():
        parts = name.split("/")
        if any(part.lower() in OVERLAY_ROLES for part in parts[2:]):
            raise ProvenanceError(f"current review subject cannot use overlay role: {name}")
        for mapping in _mappings(document):
            overlap = OVERLAY_KEYS.intersection(mapping)
            if overlap:
                raise ProvenanceError(
                    f"current review subject cannot compose an external base: {name}: {sorted(overlap)}"
                )


def _entry_projection(
    parsed: dict[str, Any], review_stage: str | None, collections: list[dict[str, Any]]
) -> dict[str, Any]:
    if review_stage not in ENTRY_STAGES:
        raise ProvenanceError("entry review_stage is invalid")
    _require_names(
        parsed,
        {
            "project/decision/state/frontier.md",
            "project/decision/state/ledger.md",
            "project/decision/state/log.md",
            "project/decision/parents/problem.md",
            "project/decision/parents/representation.md",
            "project/decision/parents/handoff.yaml",
            "project/decision/selection/evidence-state.yaml",
        },
        "entry",
    )
    selection = _mapping(
        parsed["project/decision/selection/evidence-state.yaml"],
        "entry selection evidence state",
    )
    _require_contract(selection, "frontier-selection-evidence-state/1")
    _require_fields(
        selection,
        {"event_id", "budget", "selection", "authority", "resolver", "route_set"},
        "entry selection evidence state",
    )
    plan = _one_contract(parsed, "project/decision/entry/", "frontier-project-batch-plan/2")
    _require_fields(
        plan,
        {"batch_id", "maximum_spend", "authorization_gate", "stop_conditions"},
        "entry batch plan",
    )
    work_objects = [
        document
        for name, document in parsed.items()
        if name.startswith("project/decision/entry/")
        and isinstance(document, dict)
        and isinstance(document.get("contract_version"), str)
        and document.get("batch_id") == plan["batch_id"]
        and document.get("contract_version")
        not in {
            "frontier-project-batch-plan/2",
            "frontier-project-authorization-target/1",
            "frontier-project-spend-gate/1",
        }
    ]
    if not work_objects:
        raise ProvenanceError("entry review subject is missing its work-defining object")
    if review_stage == "authorization-readiness":
        gate = _one_contract(
            parsed,
            "project/decision/entry/",
            "frontier-project-authorization-target/1",
        )
        _require_fields(
            gate,
            {
                "target_id",
                "decision_id",
                "batch_id",
                "scope",
                "maximum_spend",
                "stop_boundary",
                "authorization_question",
                "authorize_consequence",
            },
            "entry authorization target",
        )
        if gate["batch_id"] != plan["batch_id"]:
            raise ProvenanceError("entry plan and authorization target name different batches")
        authority_target = gate["target_id"]
        affected_scope = gate["scope"]
        later_spend_gate = gate["authorize_consequence"]
    else:
        gate = _one_contract(
            parsed, "project/decision/entry/", "frontier-project-spend-gate/1"
        )
        _require_fields(
            gate,
            {"batch_id", "affected_scope", "authority_target", "later_spend_gate"},
            "entry spend gate",
        )
        if gate["batch_id"] != plan["batch_id"]:
            raise ProvenanceError("entry plan and spend gate name different batches")
        authority_target = gate["authority_target"]
        affected_scope = gate["affected_scope"]
        later_spend_gate = gate["later_spend_gate"]
    return _substantive(
        {
            "review_stage": review_stage,
            "affected_scope": affected_scope,
            "budget": selection["budget"],
            "selection": selection["selection"],
            "authority_target": authority_target,
            "later_spend_gate": later_spend_gate,
        }
    )


def _replan_projection(
    parsed: dict[str, Any], review_stage: str | None, collections: list[dict[str, Any]]
) -> dict[str, Any]:
    if review_stage is not None:
        raise ProvenanceError("replan does not accept review_stage")
    _require_names(
        parsed,
        {
            "project/decision/state/frontier.md",
            "project/decision/state/ledger.md",
            "project/decision/state/log.md",
            "project/decision/parents/problem.md",
            "project/decision/parents/representation.md",
            "project/decision/parents/handoff.yaml",
            "project/decision/selection/evidence-state.yaml",
        },
        "replan",
    )
    decision = _one_contract(parsed, "project/decision/replan/", "frontier-project-replan/1")
    _require_fields(
        decision,
        {"affected_scope", "budget", "selection", "authority_target", "later_spend_gate"},
        "replan decision",
    )
    return _substantive(
        {field: decision[field] for field in (
            "affected_scope", "budget", "selection", "authority_target", "later_spend_gate"
        )}
    )


def _design_projection(
    parsed: dict[str, Any],
    review_stage: str | None,
    collections: list[dict[str, Any]],
    raw_by_name: dict[str, bytes],
) -> dict[str, Any]:
    if review_stage is not None:
        raise ProvenanceError("design does not accept review_stage")
    if not any(name.startswith("project/decision/parents/") for name in parsed):
        raise ProvenanceError("design review subject is missing project parents")
    index = _one_mapping_with_fields(
        parsed,
        "project/decision/design/",
        {"design_contract_id", "work_id", "problem_epoch", "representation_revision", "route", "delivery"},
        "design index",
    )
    if not any(
        item.get("logical_name", "").startswith("project/decision/design")
        for item in collections
    ):
        raise ProvenanceError("design review requires a closed design collection")
    _validate_design_bindings(parsed, raw_by_name, index)
    return _substantive(
        {
            "affected_scope": {
                "work_id": index["work_id"],
                "route": index["route"],
                "problem_epoch": index["problem_epoch"],
                "representation_revision": index["representation_revision"],
            },
            "design_contract": index["design_contract_id"],
            "implementation_gate": index["delivery"],
        }
    )


def _validate_design_bindings(
    parsed: dict[str, Any], raw_by_name: dict[str, bytes], index: dict[str, Any]
) -> None:
    design_root = next(
        name.rsplit("/", 1)[0]
        for name, document in parsed.items()
        if document is index
    )
    design_id = index["design_contract_id"]
    for name, document in parsed.items():
        if not name.startswith(design_root + "/") or not isinstance(document, dict):
            continue
        bound = document.get("design_contract_identity")
        if bound is not None and bound != design_id:
            raise ProvenanceError(f"design member binds a different contract: {name}")

    supporting = _mapping(index.get("supporting_inputs"), "design supporting inputs")
    source_name = design_root + "/source-base.yaml"
    source = _mapping(parsed.get(source_name), "design source base")
    expected_source = supporting.get("source-base.yaml")
    if source.get("source_base_id") != expected_source:
        raise ProvenanceError("design index and source base identity disagree")

    traceability_name = design_root + "/traceability.yaml"
    traceability = _mapping(parsed.get(traceability_name), "design traceability")
    if traceability.get("design_contract_identity") != design_id:
        raise ProvenanceError("design traceability binds a different design contract")
    expected_traceability = supporting.get("traceability.yaml.normalized")
    observed_traceability = _omit_exact_line(
        raw_by_name[traceability_name], "design_contract_identity"
    )
    if expected_traceability != observed_traceability:
        raise ProvenanceError("design traceability normalized digest disagrees with index")

    concerns = _mapping(index.get("concerns_normalized"), "design concern index")
    for filename, expected in concerns.items():
        if not isinstance(filename, str) or not isinstance(expected, str):
            raise ProvenanceError("design concern index is invalid")
        name = design_root + "/" + filename
        if name not in raw_by_name:
            raise ProvenanceError(f"design concern is missing: {filename}")
        observed = _omit_exact_line(raw_by_name[name], "design_contract_identity")
        if observed != expected:
            raise ProvenanceError(f"design concern digest disagrees with index: {filename}")


def _omit_exact_line(raw: bytes, field: str) -> str:
    marker = f"{field}:".encode()
    kept: list[bytes] = []
    found = 0
    for line in raw.splitlines(keepends=True):
        if line.startswith(marker):
            found += 1
        else:
            kept.append(line)
    if found != 1:
        raise ProvenanceError(f"design member must contain exactly one {field} line")
    return hashlib.sha256(b"".join(kept)).hexdigest()


def _implementation_projection(
    parsed: dict[str, Any], review_stage: str | None, collections: list[dict[str, Any]]
) -> dict[str, Any]:
    if review_stage is not None:
        raise ProvenanceError("implementation does not accept review_stage")
    decision = _one_contract(
        parsed,
        "project/decision/implementation/",
        "frontier-project-implementation-review-input/1",
    )
    _require_fields(decision, {"affected_scope", "candidate", "reviewed_design"}, "implementation input")
    if not any(
        item.get("logical_name", "").startswith("project/decision/candidate")
        for item in collections
    ):
        raise ProvenanceError("implementation review requires a closed candidate collection")
    return _substantive(
        {field: decision[field] for field in ("affected_scope", "candidate", "reviewed_design")}
    )


def _claims_projection(
    parsed: dict[str, Any], review_stage: str | None, collections: list[dict[str, Any]]
) -> dict[str, Any]:
    if review_stage is not None:
        raise ProvenanceError("claims does not accept review_stage")
    decision = _one_contract(parsed, "project/decision/claims/", "frontier-project-claims/1")
    _require_fields(decision, {"affected_scope", "outcomes", "claim_ceiling"}, "claims input")
    if not any(name.startswith("project/decision/outcome/") for name in parsed):
        raise ProvenanceError("claims review subject is missing outcome evidence")
    return _substantive(
        {field: decision[field] for field in ("affected_scope", "outcomes", "claim_ceiling")}
    )


def _require_names(parsed: dict[str, Any], required: set[str], role: str) -> None:
    missing = sorted(required - parsed.keys())
    if missing:
        raise ProvenanceError(f"{role} review subject is missing canonical roles {missing}")


def _one_contract(parsed: dict[str, Any], prefix: str, contract: str) -> dict[str, Any]:
    matches = [
        document
        for name, document in parsed.items()
        if name.startswith(prefix)
        and isinstance(document, dict)
        and document.get("contract_version") == contract
    ]
    if len(matches) != 1:
        raise ProvenanceError(
            f"review subject requires exactly one {contract} object under {prefix}"
        )
    return matches[0]


def _one_mapping_with_fields(
    parsed: dict[str, Any], prefix: str, fields: set[str], role: str
) -> dict[str, Any]:
    matches = [
        document
        for name, document in parsed.items()
        if name.startswith(prefix) and isinstance(document, dict) and fields <= document.keys()
    ]
    if len(matches) != 1:
        raise ProvenanceError(f"review subject requires exactly one canonical {role}")
    return matches[0]


def _mapping(value: Any, role: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ProvenanceError(f"{role} must be a mapping")
    return value


def _require_contract(value: dict[str, Any], contract: str) -> None:
    if value.get("contract_version") != contract:
        raise ProvenanceError(f"object must use supported contract {contract}")


def _require_fields(value: dict[str, Any], fields: set[str], role: str) -> None:
    missing = sorted(field for field in fields if value.get(field) in (None, "", [], {}))
    if missing:
        raise ProvenanceError(f"{role} is missing substantive fields {missing}")


def _substantive(value: dict[str, Any]) -> dict[str, Any]:
    missing = sorted(field for field, item in value.items() if item in (None, "", [], {}))
    if missing:
        raise ProvenanceError(f"derived semantic projection is empty at {missing}")
    json.dumps(value, sort_keys=True)
    return value


def _mappings(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _mappings(child)
    elif isinstance(value, list):
        for child in value:
            yield from _mappings(child)
