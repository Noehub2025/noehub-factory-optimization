"""Small typed interface over Frontier provenance identity mechanics."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from .content import ProvenanceError
from .graph import build_node, collect_chain
from .stores import ProjectPortableStore
from .repository import NodeRepository
from .routine_admission import validate_routine_admission


READY_VERDICTS = {"ready", "blocked", "repair"}
CONSEQUENCE_CONTRACT = "frontier-consequence-gates/2"
CONSEQUENCES = {
    "audit": ({"decision", "attestation", "authority", "execution", "outcome"}, set()),
    "review": ({"decision", "attestation"}, set()),
    "acknowledgment": ({"authority"}, set()),
    "execution": (
        {"authority", "execution"},
        {"authority_current", "budget_current", "reservation_current", "inputs_current", "resources_available"},
    ),
    "spend": (
        {"authority", "execution"},
        {"authority_current", "budget_current", "reservation_current", "inputs_current", "resources_available"},
    ),
    "routine-local-execution": (
        {"authority", "execution"},
        {
            "authority_current",
            "budget_current",
            "reservation_current",
            "inputs_current",
            "resources_available",
            "action_window_open",
            "routine_slot_current",
        },
    ),
    "external-action": (
        {"execution"},
        {"authority_current", "budget_current", "reservation_current", "inputs_current", "resources_available", "action_window_open", "prior_external_effects_known"},
    ),
    "outcome-publication": (
        {"outcome"},
        {"authority_current", "inputs_current", "budget_accounted", "prior_external_effects_known"},
    ),
}
COMPLETE_SUBJECT_CONSEQUENCES = {
    "acknowledgment",
    "execution",
    "spend",
    "external-action",
    "outcome-publication",
}


def freeze_decision(*, decision_root: str) -> dict[str, Any]:
    return build_node(
        "decision",
        {},
        artifact_roots=[decision_root],
    )


def attest(
    subject: dict[str, Any],
    *,
    validation_report_root: str,
    verdict: str,
    findings: list[dict[str, Any]],
    freshness: str = "immutable",
    observed_at: str | None = None,
    expires_at: str | None = None,
    invalidation_rule: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if verdict not in READY_VERDICTS:
        raise ProvenanceError(f"unsupported attestation verdict: {verdict!r}")
    if freshness == "immutable" and any(
        value is not None for value in (observed_at, expires_at, invalidation_rule)
    ):
        raise ProvenanceError(
            "immutable attestations cannot carry live observation fields"
        )
    if freshness == "live" and observed_at is None:
        raise ProvenanceError(
            "live attestations require observed_at"
        )
    if freshness == "live":
        if not isinstance(invalidation_rule, dict) or set(invalidation_rule) != {
            "required_facts"
        }:
            raise ProvenanceError("live attestation invalidation rule is invalid")
        required_facts = invalidation_rule["required_facts"]
        if not isinstance(required_facts, list) or not required_facts or not all(
            isinstance(value, str) and value for value in required_facts
        ):
            raise ProvenanceError("live attestation requires named invalidation facts")
        observed = _instant(observed_at)
        if expires_at is not None and observed > _instant(expires_at):
            raise ProvenanceError("live attestation observation follows its expiry")
    if not isinstance(findings, list) or not all(
        isinstance(finding, dict)
        and set(finding) == {"effect", "code"}
        and finding.get("effect") in {"block", "repair", "advisory"}
        for finding in findings
    ):
        raise ProvenanceError("every attestation finding requires a known effect")
    if verdict == "ready" and any(
        finding["effect"] in {"block", "repair"} for finding in findings
    ):
        raise ProvenanceError("ready attestation cannot contain block or repair findings")
    payload = {
        "subject_root": subject["node_id"],
        "verdict": verdict,
        "findings": findings,
        "freshness": freshness,
        "observed_at": observed_at,
        "expires_at": expires_at,
        "invalidation_rule": invalidation_rule,
    }
    return build_node(
        "attestation",
        payload,
        parents=[{"edge": "subject", "node_id": subject["node_id"]}],
        artifact_roots=[validation_report_root],
    )


def bind_authority(
    *,
    authority_root: str,
    decision: dict[str, Any],
    validation: dict[str, Any],
    decision_bundle: Path | None = None,
) -> dict[str, Any]:
    if validation.get("payload", {}).get("verdict") != "ready":
        raise ProvenanceError("authority cannot bind a non-ready validation")
    if validation.get("payload", {}).get("subject_root") != decision.get("node_id"):
        raise ProvenanceError("authority validation does not attest its decision")
    if validation.get("payload", {}).get("findings") and any(
        item.get("effect") in {"block", "repair"}
        for item in validation["payload"]["findings"]
    ):
        raise ProvenanceError("authority validation contains a blocking finding")
    decision_roots = decision.get("artifact_roots", [])
    decision_content = (
        ProjectPortableStore().verify(decision_bundle, expected_role="decision")
        if isinstance(decision_bundle, Path)
        else None
    )
    if (
        not isinstance(decision_content, dict)
        or decision_content.get("verified") is not True
        or decision_content.get("domain") != "project-decision"
        or len(decision_roots) != 1
        or decision_content.get("content_root") != decision_roots[0]
        or not isinstance(decision_content.get("review_subject"), dict)
        or decision_content["review_subject"].get("subject_mode") != "complete"
        or decision_content["review_subject"].get("contract_version")
        != "frontier-review-subject/2"
    ):
        raise ProvenanceError(
            "new authority requires the verified complete subject of its reviewed decision"
        )
    return build_node(
        "authority",
        {},
        parents=[
            {"edge": "decision", "node_id": decision["node_id"]},
            {"edge": "attestation", "node_id": validation["node_id"]},
        ],
        artifact_roots=[authority_root],
    )


def freeze_execution(
    *,
    authority: dict[str, Any],
    starting_state_root: str,
    routine_admission: dict[str, Any] | None = None,
    repository: NodeRepository | None = None,
    resolve_content: Callable[[str], dict[str, Any]] | None = None,
    read_content: Callable[[str], dict[str, bytes]] | None = None,
    live_facts: dict[str, dict[str, Any]] | None = None,
    checked_at: str | None = None,
) -> dict[str, Any]:
    admission_result: dict[str, Any] | None = None
    if routine_admission is not None:
        if not all((repository, resolve_content, read_content)):
            raise ProvenanceError(
                "routine execution requires its canonical repository and content resolvers"
            )
        load = repository.load
        gate = verify_for(
            authority["node_id"],
            load,
            resolve_content,
            consequence="routine-local-execution",
            live_facts=live_facts,
            checked_at=checked_at,
        )
        if not gate["ready"]:
            raise ProvenanceError(
                "routine execution has unresolved live facts: "
                + ", ".join(gate["unresolved_live_facts"])
            )
        state_content = resolve_content(starting_state_root)
        routine_receipt_root = (live_facts or {}).get(
            "routine_slot_current", {}
        ).get("receipt_root")
        if routine_receipt_root != routine_admission.get("live_receipt_root"):
            raise ProvenanceError(
                "routine execution live receipt differs from its frozen admission"
            )
        admission_result = validate_routine_admission(
            admission=routine_admission,
            authority=authority,
            state_root=starting_state_root,
            state_content=state_content,
            state_raw=read_content(starting_state_root),
            load=load,
            resolve_content=resolve_content,
            read_content=read_content,
        )
        for prior in repository.iter_role("execution"):
            if prior["node_id"] == routine_admission["materialization_execution_root"]:
                continue
            if not any(
                parent["edge"] == "authority"
                and parent["node_id"] == authority["node_id"]
                for parent in prior["parents"]
            ):
                continue
            try:
                prior_raw = read_content(prior["artifact_roots"][0])
            except (KeyError, ProvenanceError) as exc:
                raise ProvenanceError(
                    "cannot rule out a prior routine execution under this authority"
                ) from exc
            prior_admission_raw = prior_raw.get("project/state/routine-admission.yaml")
            if prior_admission_raw is None:
                continue
            try:
                prior_admission = yaml.safe_load(prior_admission_raw)
            except yaml.YAMLError as exc:
                raise ProvenanceError("prior routine admission is unreadable") from exc
            prior_target = (
                prior_admission.get("evaluation_target", {})
                if isinstance(prior_admission, dict)
                else {}
            )
            prior_slot = prior_target.get("routine_slot", {}).get("slot_id")
            if prior_slot == admission_result["slot_id"]:
                raise ProvenanceError(
                    "routine slot already has a canonical execution; replay cannot sample again"
                )
    execution = build_node(
        "execution",
        {},
        parents=[{"edge": "authority", "node_id": authority["node_id"]}],
        artifact_roots=[starting_state_root],
    )
    if admission_result is not None:
        if repository.contains(execution["node_id"]):
            raise ProvenanceError(
                "routine execution already exists; a replay cannot release a worker or sample again"
            )
        repository.consume_routine_slot(
            admission_result["slot_id"], execution["node_id"]
        )
    return execution


def record_outcome(
    *,
    execution: dict[str, Any],
    outcome_root: str,
) -> dict[str, Any]:
    return build_node(
        "outcome",
        {},
        parents=[{"edge": "execution", "node_id": execution["node_id"]}],
        artifact_roots=[outcome_root],
    )


def verify_for(
    root_id: str,
    load: Callable[[str], dict[str, Any]],
    resolve_content: Callable[[str], dict[str, Any]],
    *,
    consequence: str,
    live_facts: dict[str, dict[str, Any]] | None = None,
    checked_at: str | None = None,
) -> dict[str, Any]:
    if consequence not in CONSEQUENCES:
        raise ProvenanceError(f"unsupported consequence: {consequence!r}")
    nodes = collect_chain(root_id, load)
    root = next(node for node in nodes if node["node_id"] == root_id)
    allowed_roles, required_facts = CONSEQUENCES[consequence]
    if root["role"] not in allowed_roles:
        raise ProvenanceError(
            f"{consequence} requires root role in {sorted(allowed_roles)}"
        )
    content_roots = {
        value
        for node in nodes
        for value in node["artifact_roots"]
    }
    expected_domains = {
        "decision": "project-decision",
        "attestation": "review-report",
        "authority": "project-authority",
        "execution": "project-state",
        "outcome": "project-outcome",
    }
    root_roles: dict[str, str] = {}
    resolved_content: dict[str, dict[str, Any]] = {}
    for node in nodes:
        for content_root in node["artifact_roots"]:
            prior = root_roles.setdefault(content_root, node["role"])
            if prior != node["role"]:
                raise ProvenanceError(
                    "one content root cannot satisfy different project domains"
                )
    for content_root in sorted(content_roots):
        resolved = resolve_content(content_root)
        if (
            not isinstance(resolved, dict)
            or resolved.get("verified") is not True
            or resolved.get("content_root") != content_root
        ):
            raise ProvenanceError(f"content root did not verify: {content_root}")
        resolved_content[content_root] = resolved
        expected_domain = expected_domains[root_roles[content_root]]
        if resolved.get("domain") != expected_domain:
            raise ProvenanceError(
                f"{root_roles[content_root]} content must use {expected_domain} domain"
            )
    if consequence in COMPLETE_SUBJECT_CONSEQUENCES:
        decision_roots = [
            content_root
            for content_root, role in root_roles.items()
            if role == "decision"
        ]
        if len(decision_roots) != 1:
            raise ProvenanceError("action consequence requires one reviewed decision")
        subject = resolved_content[decision_roots[0]].get("review_subject")
        if not isinstance(subject, dict) or subject.get("subject_mode") != "complete":
            raise ProvenanceError(
                "action consequence requires a verified complete review subject"
            )
    chain = {
        "root_id": root_id,
        "root_role": root["role"],
        "node_count": len(nodes),
    }
    facts = dict(live_facts or {})
    required = set(required_facts)
    if consequence != "acknowledgment":
        for node in nodes:
            if (
                node["role"] == "attestation"
                and node["payload"].get("freshness") == "live"
            ):
                rule = node["payload"]["invalidation_rule"]
                required.update(rule["required_facts"])
                if checked_at is None:
                    raise ProvenanceError(
                        "live attestation verification requires checked_at"
                    )
                checked = _instant(checked_at)
                observed = _instant(node["payload"]["observed_at"])
                if observed > checked:
                    raise ProvenanceError("live attestation observation is in the future")
                expires_at = node["payload"].get("expires_at")
                if expires_at is not None and checked > _instant(expires_at):
                    raise ProvenanceError("live attestation has expired")
    unresolved: list[str] = []
    if required and checked_at is None:
        raise ProvenanceError("live consequence verification requires checked_at")
    for name in sorted(required):
        fact = facts.get(name)
        if not isinstance(fact, dict) or set(fact) != {"receipt_root"}:
            unresolved.append(name)
            continue
        receipt_root = fact["receipt_root"]
        resolved = resolve_content(receipt_root)
        receipt = resolved.get("receipt_facts", {}).get(name)
        if (
            resolved.get("verified") is not True
            or resolved.get("content_root") != receipt_root
            or resolved.get("domain") != "live-receipt"
            or not isinstance(receipt, dict)
            or receipt.get("status") != "pass"
            or _instant(receipt.get("observed_at")) > _instant(checked_at)
            or _instant(receipt.get("expires_at")) < _instant(checked_at)
        ):
            unresolved.append(name)
    return {
        **chain,
        "consequence_contract": CONSEQUENCE_CONTRACT,
        "consequence": consequence,
        "static_chain_verified": True,
        "live_facts_checked": sorted(required),
        "ready": not unresolved,
        "unresolved_live_facts": unresolved,
    }


def _instant(value: str) -> datetime:
    if not isinstance(value, str):
        raise ProvenanceError("timestamp must be an ISO-8601 string")
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ProvenanceError(f"timestamp is invalid: {value!r}") from exc
    if parsed.tzinfo is None:
        raise ProvenanceError("timestamp must include a timezone")
    return parsed.astimezone(timezone.utc)


def export_chain(
    root_id: str, load: Callable[[str], dict[str, Any]]
) -> list[dict[str, Any]]:
    return collect_chain(root_id, load)
