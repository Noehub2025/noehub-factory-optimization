"""Small typed interface over Frontier provenance identity mechanics."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import copy
import hashlib
import json

import yaml

from .content import ProvenanceError, verify_manifest
from .graph import build_node, collect_chain, verify_node
from .stores import ProjectPortableStore
from .repository import NodeRepository
from .routine_admission import validate_routine_admission
from .review_subject import INDEX_LOGICAL_NAME, require_current_review_subject, validate_review_subject


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
    decision_content: dict[str, Any] | None = None,
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
    decision_content = decision_content or (
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
    ):
        raise ProvenanceError(
            "new authority requires the verified complete subject of its reviewed decision"
        )
    require_current_review_subject(decision_content.get("review_subject"))
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
    if repository is not None and resolve_content is not None and read_content is not None:
        decision = repository.load(next(parent["node_id"] for parent in authority["parents"] if parent["edge"] == "decision"))
        subject = require_current_review_subject(resolve_content(decision["artifact_roots"][0]).get("review_subject"))
        state_raw = read_content(starting_state_root)
        validate_design_revision(subject["semantic_projection"], state_raw)
        if subject["semantic_projection"].get("design_revision_scope") is not None:
            current = verify_for(authority["node_id"], repository.load, resolve_content,
                                 consequence="execution", live_facts=live_facts, checked_at=checked_at)
            if not current["ready"]:
                raise ProvenanceError("design continuation has unresolved current execution facts")
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
    read_content: Callable[[str], dict[str, bytes]] | None = None,
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
        require_current_review_subject(
            resolved_content[decision_roots[0]].get("review_subject")
        )
    for node in nodes:
        if node["role"] != "execution":
            continue
        decision = next(item for item in nodes if item["role"] == "decision")
        subject = resolved_content[decision["artifact_roots"][0]].get("review_subject") or {}
        projection = subject.get("semantic_projection", {})
        if read_content is not None:
            validate_design_revision(projection, read_content(node["artifact_roots"][0]))
        elif projection.get("design_revision_scope") is not None:
            raise ProvenanceError("delegated design execution requires its starting-state bytes")
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


def validate_design_revision(
    projection: dict[str, Any], state_raw: dict[str, bytes]
) -> dict[str, str]:
    """Check a narrow pre-authorized design edit using proof inside the existing state.

    Return the changed fixed input paths and their new hashes. The Design review
    proves technical readiness; only the original Entry target grants this scope.
    """
    prefix = "project/state/design-revision/"
    if not any(name.startswith(prefix) for name in state_raw):
        return {}
    scope = projection.get("design_revision_scope")
    if not isinstance(scope, dict):
        raise ProvenanceError("original authority did not delegate design revisions")

    def embedded(role: str, domain: str) -> tuple[str, dict[str, bytes], dict[str, Any]]:
        member_prefix = prefix + role + "/"
        try:
            manifest = json.loads(state_raw[member_prefix + "manifest.json"])
            root = verify_manifest(manifest)
            raw = {item["logical_name"]: state_raw[member_prefix + item["logical_name"]] for item in manifest["artifacts"]}
        except (KeyError, TypeError, ValueError) as exc:
            raise ProvenanceError(f"incomplete embedded design {role}") from exc
        if manifest["domain"] != domain:
            raise ProvenanceError(f"embedded design {role} has the wrong domain")
        for item in manifest["artifacts"]:
            value = raw[item["logical_name"]]
            if len(value) != item["size"] or hashlib.sha256(value).hexdigest() != item["content_sha256"]:
                raise ProvenanceError(f"embedded design {role} bytes changed")
        subject = validate_review_subject(manifest, raw) if domain == "project-decision" else {}
        return root, raw, subject or {}

    base_root, base, old_subject = embedded("base", "project-decision")
    new_root, revised, new_subject = embedded("revised", "project-decision")
    report_root, _, _ = embedded("review", "review-report")
    if base_root != scope["base_design_content_root"]:
        raise ProvenanceError("design revision has a different authorized base")
    for subject in (old_subject, new_subject):
        require_current_review_subject(subject, expected_kind="design")
    old_projection = old_subject["semantic_projection"]
    new_projection = new_subject["semantic_projection"]
    for field in ("affected_scope", "implementation_gate"):
        if old_projection[field] != new_projection[field]:
            raise ProvenanceError(f"design revision changes protected {field}; Entry is required")
    try:
        decision = json.loads(state_raw[prefix + "decision.json"])
        review = json.loads(state_raw[prefix + "attestation.json"])
        verify_node(decision)
        verify_node(review)
        review_nodes = {decision["node_id"]: decision, review["node_id"]: review}
        collect_chain(review["node_id"], review_nodes.__getitem__)
    except (KeyError, TypeError, ValueError) as exc:
        raise ProvenanceError("design revision requires its exact technical review nodes") from exc
    if (decision["role"] != "decision" or decision["artifact_roots"] != [new_root]
        or review["role"] != "attestation" or review["artifact_roots"] != [report_root]
        or review["parents"] != [{"edge": "subject", "node_id": decision["node_id"]}]
        or review["payload"].get("subject_root") != decision["node_id"]
        or review["payload"].get("verdict") != "ready"
        or review["payload"].get("freshness") != "immutable"
        or any(item.get("effect") in {"block", "repair"} for item in review["payload"].get("findings", []))):
        raise ProvenanceError("design revision requires a ready review of these exact bytes")
    # Complete subjects contain a generated index. Its projection is checked above;
    # raw concern and parent comparison below supplies the narrower edit boundary.
    subject_name = INDEX_LOGICAL_NAME
    base = {name: raw for name, raw in base.items() if name != subject_name}
    revised = {name: raw for name, raw in revised.items() if name != subject_name}
    if set(base) != set(revised):
        raise ProvenanceError("delegated design revision cannot add or remove contract members")
    allowed = set(scope["mutable_concerns"])
    indexed_concerns = set()
    for name, raw in base.items():
        if name.startswith("project/decision/design/") and name.endswith((".yaml", ".yml", ".json")):
            document = yaml.safe_load(raw)
            if isinstance(document, dict) and "design_contract_id" in document:
                indexed_concerns.update(name.rsplit("/", 1)[0] + "/" + filename for filename in document.get("concerns_normalized", {}))
    if not allowed <= indexed_concerns:
        raise ProvenanceError("only indexed technical concerns may be delegated, not parents, delivery, or the design index")

    def stable(name: str, raw: bytes) -> Any:
        if not name.startswith("project/decision/design/"):
            return raw
        # Hashes and the top-level design binding are derived, not new obligations.
        text = b"".join(line for line in raw.splitlines(keepends=True) if not line.startswith(b"design_contract_identity:"))
        if name.endswith((".yaml", ".yml", ".json")):
            parsed = yaml.safe_load(text)
            if isinstance(parsed, dict) and "design_contract_id" in parsed:
                parsed = copy.deepcopy(parsed)
                parsed.pop("design_contract_id")
                for filename in parsed.get("concerns_normalized", {}):
                    if name.rsplit("/", 1)[0] + "/" + filename in allowed:
                        parsed["concerns_normalized"][filename] = "authorized mutable concern"
                return parsed
        return text

    for name in base:
        if name not in allowed and stable(name, base[name]) != stable(name, revised[name]):
            raise ProvenanceError(f"design revision changes an undelegated member: {name}")
    paths = scope["design_input_paths"]
    for name, path in paths.items():
        if name not in base or scope.get("base_input_identities", {}).get(path) != "sha256:" + hashlib.sha256(base[name]).hexdigest():
            raise ProvenanceError("delegated base design does not match the originally frozen input")
    changes = {}
    for name in base:
        if base[name] == revised[name]:
            continue
        if name not in paths:
            raise ProvenanceError(f"revised design member has no authorized input path: {name}")
        changes[paths[name]] = "sha256:" + hashlib.sha256(revised[name]).hexdigest()
    return changes


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
