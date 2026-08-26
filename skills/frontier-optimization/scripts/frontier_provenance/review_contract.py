"""Review-kind role adapters for complete Frontier project decisions."""

from __future__ import annotations

import hashlib
import json
from typing import Any

import yaml

from evaluation_target_contract import validate_evaluation_target_contract

from .content import ProvenanceError


ROLE_ADAPTER_CONTRACT = "frontier-review-role-adapter/2"
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
        "entry": lambda parsed, stage, collections: _entry_projection(
            parsed, stage, collections, raw_by_name
        ),
        "replan": _replan_projection,
        "design": lambda parsed, stage, collections: _design_projection(
            parsed, stage, collections, raw_by_name
        ),
        "implementation": _implementation_projection,
        "claims": _claims_projection,
    }[review_kind](parsed, review_stage, collections)


def _authorization_basis(
    gate: dict[str, Any], parsed: dict[str, Any], raw_by_name: dict[str, bytes]
) -> dict[str, Any]:
    """Bind a reused user decision; the Entry reviewer judges semantic scope fit.

    This is the existing spend-readiness path, not a new authority writer.
    Current budget and effect checks still run at the actual consequence.
    """
    basis = gate["authorization_basis"]
    if not isinstance(basis, dict) or set(basis) != {"target", "answer", "adoption"}:
        raise ProvenanceError("authorization_basis must reference the original target, answer, and adoption")
    documents = {}
    for role, name in basis.items():
        if not isinstance(name, str) or not name.startswith("project/decision/authority/") or name not in parsed:
            raise ProvenanceError(f"authorization_basis {role} must be a retained authority member")
        documents[role] = _mapping(parsed[name], f"authorization_basis {role}")
    target, answer, adoption = (documents[role] for role in ("target", "answer", "adoption"))
    _require_contract(target, "frontier-project-authorization-target/1")
    _require_fields(target, {"target_id", "decision_id", "scope", "maximum_spend", "stop_boundary"}, "original authorization target")
    if target.get("continuation") != "within-scope":
        raise ProvenanceError("an exact-only authorization cannot authorize a replacement decision")
    if target["target_id"] != gate["authority_target"]:
        raise ProvenanceError("spend gate must cite the original user target")
    if any(doc.get("decision_id") != target["decision_id"] for doc in (answer, adoption)):
        raise ProvenanceError("authorization basis names different user decisions")
    if answer.get("target_id") != target["target_id"]:
        raise ProvenanceError("user answer names a different target")
    if answer.get("answer_classification") != "authorize" or answer.get("conditions") != []:
        raise ProvenanceError("reuse requires an adopted affirmative answer without unresolved conditions")
    if not isinstance(answer.get("exact_answer"), str) or not answer["exact_answer"].strip():
        raise ProvenanceError("reuse requires the preserved user answer")
    if adoption.get("result") != "ENTRY_READY":
        raise ProvenanceError("authorization basis is not adopted")
    target_binding = adoption.get("target", {})
    answer_binding = adoption.get("user_result", {})
    if not isinstance(target_binding, dict) or not isinstance(answer_binding, dict):
        raise ProvenanceError("authorization adoption lacks its original content bindings")
    if target_binding.get("identity") != target["target_id"]:
        raise ProvenanceError("adoption names a different target")
    for role, binding in (("target", target_binding), ("answer", answer_binding)):
        if binding.get("file_sha256") != hashlib.sha256(raw_by_name[basis[role]]).hexdigest():
            raise ProvenanceError(f"authorization adoption does not bind the original {role} bytes")
    authority = adoption.get("authority_id")
    if not isinstance(authority, str) or not authority.startswith("frontier-authority-root-sha256:"):
        raise ProvenanceError("authorization adoption lacks its original authority identity")
    return {
        **basis,
        "target_id": target["target_id"],
        "decision_id": target["decision_id"],
        "authority_id": authority,
        "scope": target["scope"],
        "maximum_spend": target["maximum_spend"],
        "stop_boundary": target["stop_boundary"],
        "continuation": "within-scope",
    }


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
    parsed: dict[str, Any], review_stage: str | None, collections: list[dict[str, Any]],
    raw_by_name: dict[str, bytes],
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
    plan = _one_contract(parsed, "project/decision/entry/", "frontier-project-batch-plan/3")
    _require_fields(
        plan,
        {"batch_id", "maximum_spend", "authorization_gate", "stop_conditions"},
        "entry batch plan",
    )
    delivery_scope = _validate_delivery_scope(parsed, plan)
    if plan.get("evaluation_target") is not None:
        target_findings: list[dict[str, str]] = []
        validate_evaluation_target_contract(plan["evaluation_target"], target_findings)
        if target_findings:
            raise ProvenanceError("Entry evaluation target is invalid: " + "; ".join(item["detail"] for item in target_findings))
    work_objects = [
        document
        for name, document in parsed.items()
        if name.startswith("project/decision/entry/")
        and isinstance(document, dict)
        and isinstance(document.get("contract_version"), str)
        and document.get("batch_id") == plan["batch_id"]
        and document.get("contract_version")
        not in {
            "frontier-project-batch-plan/3",
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
        if gate.get("continuation", "exact-only") not in ("exact-only", "within-scope"):
            raise ProvenanceError("authorization continuation must be exact-only or within-scope")
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
    projection = {
        "review_stage": review_stage,
        "affected_scope": affected_scope,
        "budget": selection["budget"],
        "selection": selection["selection"],
        "authority_target": authority_target,
        "later_spend_gate": later_spend_gate,
    }
    if review_stage == "spend-readiness" and gate.get("authorization_basis") is not None:
        projection["authorization_basis"] = _authorization_basis(gate, parsed, raw_by_name)
    if delivery_scope is not None:
        projection["delivery_scope"] = delivery_scope
    revision = gate.get("design_revision_scope")
    if revision is not None:
        if not isinstance(revision, dict) or set(revision) != {
            "base_design_content_root", "mutable_concerns", "design_input_paths"
        }:
            raise ProvenanceError("design_revision_scope requires a base design, named mutable concerns, and fixed input paths")
        if not isinstance(revision["base_design_content_root"], str) or not revision["base_design_content_root"].startswith("frontier-content-root-sha256:"):
            raise ProvenanceError("design_revision_scope requires an exact base design content root")
        concerns = revision["mutable_concerns"]
        paths = revision["design_input_paths"]
        if not isinstance(concerns, list) or not concerns or not all(isinstance(name, str) and name.startswith("project/decision/design/") for name in concerns):
            raise ProvenanceError("design_revision_scope must name mutable design concerns")
        if not isinstance(paths, dict) or not paths or not all(isinstance(name, str) and name.startswith("project/decision/design/") and isinstance(path, str) and path for name, path in paths.items()):
            raise ProvenanceError("design_revision_scope requires exact design input paths")
        if len(set(paths.values())) != len(paths) or not set(concerns) <= set(paths):
            raise ProvenanceError("mutable concerns require distinct frozen input paths")
        inputs = plan.get("execution_frozen_inputs", [])
        fixed = {item.get("path"): item.get("identity") for item in inputs if isinstance(item, dict) and item.get("scope") == "file"}
        if not set(paths.values()) <= set(fixed):
            raise ProvenanceError("delegated design paths must be original individually frozen inputs")
        projection["design_revision_scope"] = {
            **revision, "base_input_identities": {path: fixed[path] for path in paths.values()}
        }
    routine = plan.get("routine_follow_up")
    if routine is not None:
        projection["routine_follow_up"] = _routine_follow_up_projection(parsed, plan)
    return _substantive(projection)


def _validate_delivery_scope(
    parsed: dict[str, Any], plan: dict[str, Any]
) -> dict[str, Any] | None:
    """Validate the stable delivery obligations selected by one W-backed B."""

    profile = plan.get("design_profile")
    scope = plan.get("delivery_scope")
    if profile not in {"module", "system"}:
        if scope not in (None, []):
            raise ProvenanceError(
                "delivery_scope is available only to module or system work"
            )
        return None

    _require_fields(
        plan,
        {
            "work_plan",
            "work_plan_revision",
            "design_contract_identity",
            "required_design_inputs",
            "delivery_scope",
        },
        "W-backed entry batch plan",
    )
    if (
        not isinstance(scope, list)
        or not all(isinstance(item, str) and item.strip() for item in scope)
        or len(scope) != len(set(scope))
    ):
        raise ProvenanceError(
            "W-backed entry delivery_scope must be a nonempty unique list of delivery identities"
        )

    traceability_matches = [
        document
        for name, document in parsed.items()
        if name.startswith("project/decision/design/")
        and name.endswith("/traceability.yaml")
        and isinstance(document, dict)
        and document.get("design_contract_identity")
        == plan["design_contract_identity"]
    ]
    if len(traceability_matches) != 1:
        raise ProvenanceError(
            "W-backed entry review requires one matching design traceability object"
        )
    traceability = traceability_matches[0]
    slices = _mapping(traceability.get("slices"), "design traceability slices")
    by_delivery: dict[str, dict[str, Any]] = {}
    for name, value in slices.items():
        item = _mapping(value, f"design traceability slice {name}")
        delivery_identity = item.get("delivery_identity")
        if (
            not isinstance(delivery_identity, str)
            or not delivery_identity.strip()
            or delivery_identity in by_delivery
        ):
            raise ProvenanceError(
                "design traceability contains an invalid or duplicate delivery identity"
            )
        by_delivery[delivery_identity] = item

    unknown = sorted(set(scope) - by_delivery.keys())
    if unknown:
        raise ProvenanceError(f"entry delivery_scope contains unknown obligations {unknown}")
    for delivery_identity in scope:
        item = by_delivery[delivery_identity]
        prerequisites = item.get("prerequisites")
        required_inputs = item.get("required_design_inputs")
        if (
            not isinstance(prerequisites, list)
            or not all(
                isinstance(prerequisite, str) and prerequisite.strip()
                for prerequisite in prerequisites
            )
            or len(prerequisites) != len(set(prerequisites))
            or not isinstance(required_inputs, list)
            or not required_inputs
        ):
            raise ProvenanceError(
                "selected delivery_scope obligation has invalid traceability"
            )
    missing_prerequisites = sorted(
        {
            prerequisite
            for delivery_identity in scope
            for prerequisite in by_delivery[delivery_identity]["prerequisites"]
            if prerequisite not in scope
        }
    )
    if missing_prerequisites:
        raise ProvenanceError(
            "entry delivery_scope omits prerequisite obligations "
            f"{missing_prerequisites}"
        )

    plan_inputs = plan["required_design_inputs"]
    if not isinstance(plan_inputs, list):
        raise ProvenanceError("W-backed entry required_design_inputs must be a list")
    encoded_plan_inputs = {_stable_value(item) for item in plan_inputs}
    uncovered_inputs = sorted(
        {
            _stable_value(required_input)
            for delivery_identity in scope
            for required_input in by_delivery[delivery_identity][
                "required_design_inputs"
            ]
            if _stable_value(required_input) not in encoded_plan_inputs
        }
    )
    if uncovered_inputs:
        raise ProvenanceError(
            "entry required_design_inputs do not cover delivery_scope requirements"
        )
    return {
        "design_contract_identity": plan["design_contract_identity"],
        "deliveries": sorted(scope),
    }


def _stable_value(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _routine_follow_up_projection(
    parsed: dict[str, Any], plan: dict[str, Any]
) -> dict[str, Any]:
    routine = _mapping(plan.get("routine_follow_up"), "routine follow-up")
    _require_contract(routine, "frontier-routine-follow-up/1")
    _require_fields(
        routine,
        {
            "slot_id",
            "materialization_batch_id",
            "follow_up_batch_id",
            "route_id",
            "protocol_id",
            "calibration_id",
            "scientific_question",
            "sample_ceiling",
            "resource_ceiling",
            "result_contract_version",
            "action_window",
            "budget_boundary",
            "protected_reserve",
            "late_bindings",
            "experiment_template",
            "prohibited_consequences",
        },
        "routine follow-up",
    )
    if routine["materialization_batch_id"] != plan["batch_id"]:
        raise ProvenanceError("routine follow-up must belong to its materialization batch")
    if routine["result_contract_version"] != "frontier-batch-result/2":
        raise ProvenanceError("routine follow-up must write frontier-batch-result/2")
    if routine["protected_reserve"] != "prohibited":
        raise ProvenanceError("routine follow-up cannot use protected reserve")
    if routine["late_bindings"] != [
        "candidate.id",
        "candidate.manifest_sha256",
        "candidate.collection_root",
    ]:
        raise ProvenanceError("routine follow-up has an invalid delayed-binding set")
    template = _mapping(routine["experiment_template"], "routine experiment template")
    _require_contract(template, "frontier-routine-experiment-template/1")
    _require_fields(
        template,
        {"experiment", "runtime_inputs", "evaluation_target"},
        "routine experiment template",
    )
    experiment = _mapping(template["experiment"], "routine experiment source template")
    _require_contract(experiment, "frontier-routine-experiment/1")
    _require_fields(
        experiment,
        {
            "candidate",
            "scientific_question",
            "protocol_id",
            "calibration_id",
            "sample_ceiling",
            "resource_ceiling",
            "evidence_scope",
            "result_path",
            "stop_conditions",
        },
        "routine experiment source template",
    )
    if "experiment_id" in experiment:
        raise ProvenanceError(
            "routine experiment source template must omit its derived experiment_id"
        )
    if experiment["candidate"] != {
        "id": "$late.candidate.id",
        "manifest_sha256": "$late.candidate.manifest_sha256",
        "collection_root": "$late.candidate.collection_root",
    }:
        raise ProvenanceError("routine experiment source has an invalid candidate template")
    runtime_inputs = _mapping(
        template["runtime_inputs"], "routine runtime-input template"
    )
    _require_fields(
        runtime_inputs,
        {"sample_ceiling", "resource_ceiling", "schedule"},
        "routine runtime-input template",
    )
    if (
        runtime_inputs["sample_ceiling"] != routine["sample_ceiling"]
        or runtime_inputs["resource_ceiling"] != routine["resource_ceiling"]
    ):
        raise ProvenanceError("routine runtime inputs exceed the reviewed slot")
    target = _mapping(template["evaluation_target"], "routine evaluation target template")
    if target.get("mode") != "routine-local" or target.get("consequence_limit") != "B evidence only":
        raise ProvenanceError("routine experiment template exceeds B-evidence-only scope")
    target_experiment = _mapping(target.get("experiment"), "routine experiment target")
    if target_experiment.get("experiment_id") != "$derived.experiment.id" or target_experiment.get(
        "file_sha256"
    ) != "$derived.experiment.file_sha256":
        raise ProvenanceError("routine experiment target must use system-derived identity fields")
    if (
        target.get("sample_ceiling") != routine["sample_ceiling"]
        or target.get("resource_ceiling") != routine["resource_ceiling"]
    ):
        raise ProvenanceError("routine target exceeds the reviewed sample or resource ceiling")
    if (
        experiment["scientific_question"] != routine["scientific_question"]
        or experiment["protocol_id"] != routine["protocol_id"]
        or experiment["calibration_id"] != routine["calibration_id"]
        or experiment["sample_ceiling"] != routine["sample_ceiling"]
        or experiment["resource_ceiling"] != routine["resource_ceiling"]
        or experiment["evidence_scope"] != target.get("evidence_scope")
    ):
        raise ProvenanceError("routine experiment source differs from its reviewed slot")
    probe = _replace_tokens(
        target,
        {
            "$late.candidate.id": "candidate-sha256:" + "1" * 64,
            "$late.candidate.manifest_sha256": "2" * 64,
            "$late.candidate.collection_root": "sha256:" + "3" * 64,
            "$entry.origin_decision_root": "frontier-decision-root-sha256:" + "4" * 64,
            "$entry.origin_authority_root": "frontier-authority-root-sha256:" + "5" * 64,
            "$entry.template_root": "sha256:" + "6" * 64,
            "$entry.protocol_content_root": "frontier-content-root-sha256:" + "7" * 64,
            "$entry.calibration_content_root": "frontier-content-root-sha256:" + "7" * 64,
            "$entry.protocol_invalidation_key": "sha256:" + "a" * 64,
            "$derived.experiment.id": "routine-experiment-sha256:" + "8" * 64,
            "$derived.experiment.file_sha256": "9" * 64,
        },
    )
    target_findings: list[dict[str, str]] = []
    validate_evaluation_target_contract(probe, target_findings)
    if target_findings:
        details = "; ".join(item["detail"] for item in target_findings)
        raise ProvenanceError(f"routine experiment target is incomplete: {details}")
    if routine["prohibited_consequences"] != target.get("prohibited_consequences"):
        raise ProvenanceError(
            "routine follow-up prohibitions must equal the canonical target prohibitions"
        )
    protocol = _one_contract(
        parsed, "project/decision/entry/", "frontier-evaluation-protocol/1"
    )
    calibration = _one_contract(
        parsed,
        "project/decision/entry/",
        "frontier-protocol-calibration-result/1",
    )
    _require_fields(
        protocol,
        {
            "protocol_id",
            "evaluator",
            "harness",
            "schema",
            "scoring",
            "environment",
            "evaluation_scope",
            "comparison_distribution",
            "sampling",
            "metrics",
            "uncertainty",
            "exposure",
            "calibration_requirements",
            "invalidation_key",
        },
        "evaluation protocol",
    )
    invalidation_body = {
        key: value
        for key, value in protocol.items()
        if key not in {"protocol_id", "invalidation_key", "identity_rule"}
    }
    derived_invalidation_key = "sha256:" + hashlib.sha256(
        json.dumps(
            invalidation_body,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode()
    ).hexdigest()
    if protocol["invalidation_key"] != derived_invalidation_key:
        raise ProvenanceError("evaluation protocol invalidation key does not derive from protocol semantics")
    _require_fields(
        calibration,
        {
            "calibration_id",
            "protocol_id",
            "protocol_invalidation_key",
            "environment",
            "controls",
            "evidence_manifest",
            "results",
            "drift_status",
        },
        "protocol calibration result",
    )
    if routine["protocol_id"] != protocol["protocol_id"]:
        raise ProvenanceError("routine follow-up binds a different evaluation protocol")
    if routine["calibration_id"] != calibration["calibration_id"]:
        raise ProvenanceError("routine follow-up binds a different protocol calibration")
    if calibration["protocol_id"] != protocol["protocol_id"]:
        raise ProvenanceError("protocol calibration binds a different protocol")
    if calibration["protocol_invalidation_key"] != protocol["invalidation_key"]:
        raise ProvenanceError("protocol calibration is invalidated by protocol drift")
    if calibration["drift_status"] != "current":
        raise ProvenanceError("routine follow-up requires current protocol calibration")
    return {
        "slot_id": routine["slot_id"],
        "materialization_batch_id": routine["materialization_batch_id"],
        "follow_up_batch_id": routine["follow_up_batch_id"],
        "route_id": routine["route_id"],
        "protocol_id": routine["protocol_id"],
        "calibration_id": routine["calibration_id"],
        "protocol_invalidation_key": protocol["invalidation_key"],
        "scientific_question": routine["scientific_question"],
        "sample_ceiling": routine["sample_ceiling"],
        "resource_ceiling": routine["resource_ceiling"],
        "action_window": routine["action_window"],
        "budget_boundary": routine["budget_boundary"],
        "template": template,
        "prohibited_consequences": routine["prohibited_consequences"],
    }


def _replace_tokens(value: Any, replacements: dict[str, str]) -> Any:
    if isinstance(value, str):
        return replacements.get(value, value)
    if isinstance(value, list):
        return [_replace_tokens(item, replacements) for item in value]
    if isinstance(value, dict):
        return {key: _replace_tokens(item, replacements) for key, item in value.items()}
    return value


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
    parsed: dict[str, Any],
    review_stage: str | None,
    collections: list[dict[str, Any]],
) -> dict[str, Any]:
    if review_stage is not None:
        raise ProvenanceError("implementation does not accept review_stage")
    decision = _one_contract(
        parsed,
        "project/decision/implementation/",
        "frontier-project-implementation-review-input/1",
    )
    fields = {
        "affected_scope",
        "candidate",
        "reviewed_design",
        "publication_state",
        "execution_start",
        "engineering_state",
        "allowed_feedback",
    }
    _require_fields(decision, fields, "implementation input")
    if decision["publication_state"] not in {
        "prepublication",
        "published-recovery",
    }:
        raise ProvenanceError("implementation publication_state is invalid")
    if decision["publication_state"] == "prepublication":
        if not isinstance(decision["execution_start"], str) or not decision[
            "execution_start"
        ].strip():
            raise ProvenanceError(
                "prepublication implementation review requires execution_start"
            )
        engineering_state = decision["engineering_state"]
        if (
            not isinstance(engineering_state, dict)
            or engineering_state.get("status") != "pass"
            or not isinstance(engineering_state.get("final_attempt"), int)
            or isinstance(engineering_state.get("final_attempt"), bool)
            or engineering_state.get("final_attempt") <= 0
        ):
            raise ProvenanceError(
                "prepublication implementation review requires one positive final all-pass engineering state"
            )
        if not isinstance(decision["allowed_feedback"], str) or not decision[
            "allowed_feedback"
        ].strip():
            raise ProvenanceError(
                "prepublication implementation review requires allowed_feedback"
            )
    if not any(
        item.get("logical_name", "").startswith("project/decision/candidate")
        for item in collections
    ):
        raise ProvenanceError("implementation review requires a closed candidate collection")
    return _substantive({field: decision[field] for field in fields})


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
