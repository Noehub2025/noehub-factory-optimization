#!/usr/bin/env python3
"""Prepare current W and resolver references from saved Git bytes."""

from __future__ import annotations

import argparse
from contextvars import ContextVar
from functools import wraps
import json
import os
import posixpath
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml

from identity_bindings import canonical_json, sha256_bytes
from saved_git import SavedGitError, normalize_path, read_file, resolve_revision


ReferenceError = SavedGitError


_REFERENCE_OPERATION_CACHE: ContextVar[dict[str, dict[tuple[str, ...], Any]] | None] = (
    ContextVar("frontier_reference_operation_cache", default=None)
)


def _cached_reference_operation(function):
    """Share immutable Git reads only within one public operation."""
    @wraps(function)
    def wrapped(*args, **kwargs):
        if _REFERENCE_OPERATION_CACHE.get() is not None:
            return function(*args, **kwargs)
        token = _REFERENCE_OPERATION_CACHE.set({"revisions": {}, "files": {}})
        try:
            return function(*args, **kwargs)
        finally:
            _REFERENCE_OPERATION_CACHE.reset(token)

    return wrapped


def _resolved_revision(root: Path, revision: str) -> str:
    cache = _REFERENCE_OPERATION_CACHE.get()
    # Symbolic names such as HEAD remain live observations within the operation.
    # Only immutable full commit identities are reused.
    if cache is None or re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", revision) is None:
        return resolve_revision(root, revision)
    key = (str(root.resolve()), revision)
    if key not in cache["revisions"]:
        cache["revisions"][key] = resolve_revision(root, revision)
    return cache["revisions"][key]


class _UniqueLoader(yaml.SafeLoader):
    pass


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ReferenceError(f"duplicate field: {key}")
        result[key] = value
    return result


def _yaml_mapping(loader, node):
    return _pairs((loader.construct_object(k), loader.construct_object(v)) for k, v in node.value)


_UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _yaml_mapping)


def _document(raw: bytes) -> dict[str, Any]:
    value = yaml.load(raw, Loader=_UniqueLoader)
    if not isinstance(value, dict):
        raise ReferenceError("expected a mapping")
    return value


def reference(root: Path, revision: str, path: str) -> dict[str, str]:
    """Resolve a revision once; consumers retain the returned full commit."""
    ref = {"commit": _resolved_revision(root, revision), "path": normalize_path(path)}
    read_reference(root, ref)
    return ref


def read_reference(root: Path, ref: dict[str, str]) -> bytes:
    commit = ref.get("commit", "")
    path = normalize_path(ref.get("path", ""))
    cache = _REFERENCE_OPERATION_CACHE.get()
    if cache is None:
        return read_file(root, commit, path)
    key = (str(root.resolve()), commit, path)
    if key not in cache["files"]:
        cache["files"][key] = read_file(root, commit, path)
    return cache["files"][key]


@_cached_reference_operation
def prepare_review_reference(root: Path, revision: str, path: str, handle: str | None = None) -> dict:
    """Read a selected R; adoption and professional applicability are separate."""
    ref = reference(root, revision, path)
    text = read_reference(root, ref).decode("utf-8")
    header = re.match(r"\A---\s*\n(.*?)\n---(?:\s*\n|\Z)", text, re.S)
    if header:
        metadata = _document(header.group(1).encode())
    else:
        try:
            metadata = _document(text.encode())
        except (ValueError, yaml.YAMLError):
            metadata = {}
    recorded_handle = metadata.get("review_id")
    if handle is not None and recorded_handle is not None and handle != recorded_handle:
        raise ReferenceError("chosen handle differs from the saved review_id")
    handle = recorded_handle if recorded_handle is not None else handle
    if not isinstance(handle, str) or not re.fullmatch(r"R[0-9]+", handle):
        raise ReferenceError("supply the chosen R handle when the saved record has no review_id")
    return {"reference": {"handle": handle, **ref}, "review_text": text}


def _evidence(root: Path, ref: dict[str, str]) -> tuple[dict, str]:
    facts = json.loads(read_reference(root, ref), object_pairs_hook=_pairs)
    if not isinstance(facts, dict):
        raise ReferenceError("resolver evidence must be a JSON object")
    # Preserve all decision facts. Reject non-JSON numbers rather than invent a normalization.
    json.dumps(facts, allow_nan=False)
    return facts, "frontier-selection-evidence-state-sha256:" + sha256_bytes(canonical_json(facts))


DECISION_POLICY_PATH = "tools/workflow-harness/decision-policy.md"


def _decision_policy(root: Path) -> dict:
    """Supply optional current guidance, not another research evidence identity."""
    policy = {"path": DECISION_POLICY_PATH}
    try:
        raw = (root / DECISION_POLICY_PATH).read_bytes()
        text = raw.decode("utf-8")
        if not text.strip():
            return {**policy, "status": "unavailable", "reason": "policy is empty"}
    except FileNotFoundError:
        return {**policy, "status": "not_provided"}
    except (OSError, UnicodeError) as exc:
        return {**policy, "status": "unavailable", "reason": str(exc)}
    return {**policy, "status": "provided", "sha256": sha256_bytes(raw), "text": text,
            "instruction": "Apply this guidance within the existing independent investment judgment, not a second review. Optionally report policy_disposition with status addressed, not_addressed or unavailable and a brief reason describing actual handling. Missing reporting is not a pass or a blocker."}


def _policy_coverage(root: Path, policy: Any, result: dict) -> dict:
    """Report association and explicit handling, never infer a successful judgment."""
    policy = policy if isinstance(policy, dict) else {}
    digest = policy.get("sha256")
    if policy.get("status") != "provided" or not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        return {"policy_status": "unavailable" if policy.get("status") == "unavailable" else "not_provided",
                "judgment_status": "not_reported"}
    current = _decision_policy(root)
    if current["status"] == "unavailable":
        policy_status = "unavailable"
    else:
        policy_status = "current" if current.get("sha256") == digest else "changed"
    disposition = result.get("policy_disposition")
    judgment_status = "not_reported"
    if isinstance(disposition, dict) and isinstance(disposition.get("reason"), str) and disposition["reason"].strip():
        if disposition.get("status") in {"addressed", "not_addressed", "unavailable"}:
            judgment_status = disposition["status"]
    return {"policy_status": policy_status, "judgment_status": judgment_status, "sha256": digest}


def _source_metadata(text: str) -> dict:
    header = re.match(r"\A---\s*\n(.*?)\n---(?:\s*\n|\Z)", text, re.S)
    if header:
        return _document(header.group(1).encode())
    try:
        return _document(text.encode())
    except (ValueError, yaml.YAMLError):
        return {}


def _source_text(root: Path, ref: dict) -> str:
    text = read_reference(root, ref).decode("utf-8")
    return _selected_text(text, ref)


def _selected_text(text: str, ref: dict) -> str:
    """Select the same meaningful bytes from Git or saved working sources."""
    if ref.get("field"):
        metadata = _source_metadata(text)
        if ref["field"] not in metadata:
            raise ReferenceError(f"missing source field: {ref['field']}")
        return canonical_json(metadata[ref["field"]]).decode()
    if ref.get("section"):
        headings = list(re.finditer(r"^(#{1,6})\s+(.+?)\s*#*\s*$", text, re.M))
        matches = [i for i, item in enumerate(headings) if _anchor(item[2]) == ref["section"]]
        if len(matches) != 1:
            raise ReferenceError(f"missing or ambiguous source section: {ref['section']}")
        index = matches[0]
        start = headings[index]
        end = next((item.start() for item in headings[index + 1:] if len(item[1]) <= len(start[1])), len(text))
        return text[start.start():end]
    return text


def _working_text(root: Path, path: str) -> str:
    root = root.resolve()
    target = (root / normalize_path(path)).resolve(strict=True)
    if not target.is_relative_to(root):
        raise ReferenceError("working source is outside the workspace")
    return target.read_text(encoding="utf-8")


def _continuation_refs(owner_path: str, block: dict) -> list[dict]:
    """Resolve only declared direct dependencies, never crawl linked records."""
    if not isinstance(block, dict):
        raise ReferenceError("continuation must be a mapping")
    for name in ("waiting_on", "affected_work"):
        if not isinstance(block.get(name), list) or not block[name]:
            raise ReferenceError(f"continuation requires nonempty {name}")
    next_work = block.get("next")
    if not isinstance(next_work, dict) or next_work.get("kind") not in {"work", "idle"}:
        raise ReferenceError("continuation next.kind must be work or idle")
    work = next_work.get("work", [])
    if not isinstance(work, list) or (next_work["kind"] == "work" and not work) or (next_work["kind"] == "idle" and work):
        raise ReferenceError("continuation next.work must match its kind")
    condition = block.get("reconsider_when")
    if not isinstance(condition, str) or not condition.strip():
        raise ReferenceError("continuation requires reconsider_when")
    for item in block["affected_work"]:
        if not isinstance(item, dict) or not isinstance(item.get("reason"), str) or not item["reason"].strip():
            raise ReferenceError("affected_work needs a reason for each dependency or displacement")
    items = [block.get("owner_state"), block.get("basis"), *block["waiting_on"], *block["affected_work"], *work]
    refs = []
    for item in items:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            raise ReferenceError("continuation sources require a workspace-relative path")
        ref = {"path": normalize_path(item["path"])}
        selectors = [key for key in ("field", "section") if key in item]
        if len(selectors) > 1 or any(not isinstance(item[key], str) or not item[key].strip() for key in selectors):
            raise ReferenceError("source uses at most one nonempty field or section")
        ref.update({key: item[key] for key in selectors})
        if ref["path"] == owner_path and (not selectors or ref.get("field") == "continuation"):
            raise ReferenceError("owner source must select state or rationale outside continuation")
        if ref not in refs:
            refs.append(ref)
    if block["owner_state"]["path"] != owner_path:
        raise ReferenceError("owner_state must reference the adopted owner")
    return refs


def collect_continuation_sources(root: Path, owner_path: str, block: dict) -> list[dict]:
    """Derive source baselines during normal owner writing, not a new approval."""
    owner_path = normalize_path(owner_path)
    return [{**ref, "sha256": sha256_bytes(_selected_text(_working_text(root, ref["path"]), ref).replace("\r\n", "\n").encode())}
            for ref in _continuation_refs(owner_path, block)]


def check_continuation(root: Path, owner_path: str, block: dict | None = None, *, required: bool = False) -> dict:
    """Check current source applicability; never select work or refresh a baseline."""
    owner_path = normalize_path(owner_path)
    owner = _source_metadata(_working_text(root, owner_path))
    block = owner.get("continuation") if block is None else block
    if block is None:
        if required:
            raise ReferenceError("idle/wait disposition requires continuation in the existing owner or result")
        return {"status": "not_applicable"}
    current = collect_continuation_sources(root, owner_path, block)
    if block.get("source_basis") != current:
        raise ReferenceError("continuation source basis is missing or changed; reconcile current direct sources through the owner")
    basis = block["basis"]
    basis_text = _working_text(root, basis["path"])
    meaning = _source_metadata(basis_text).get(basis["field"]) if basis.get("field") else _selected_text(basis_text, basis).strip()
    if not meaning or (isinstance(meaning, str) and not meaning.strip()):
        raise ReferenceError("continuation comparison basis is empty")
    state = owner.get("current_state")
    if "current_state" in owner and (not isinstance(state, dict) or not state):
        raise ReferenceError("adopted current_state must be a nonempty mapping")
    if owner.get("type") == "Optimization Frontier" and (not isinstance(state, dict) or state.get("campaign_status") != "running"):
        raise ReferenceError("Frontier continuation requires an adopted running current_state")
    if isinstance(state, dict) and owner.get("campaign_status") is not None and owner["campaign_status"] != state.get("campaign_status"):
        raise ReferenceError("owner and current_state disagree on campaign status")
    if isinstance(state, dict):
        if block["owner_state"] != {"path": owner_path, "field": "current_state"}:
            raise ReferenceError("owner_state must cover adopted current_state")
        if state.get("campaign_status") in {"paused", "completed", "closed", "stopped", "halted"}:
            raise ReferenceError("pause or closeout uses its own return path, not continuation")
        selected = []
        primary = state.get("primary_batch")
        if primary:
            selected.append(primary)
        parallel = state.get("parallel_batches", state.get("parallel", []))
        if not isinstance(parallel, list):
            raise ReferenceError("current parallel work must be a list")
        selected.extend(parallel)
        paths = set()
        for batch in selected:
            if not isinstance(batch, str) or not re.fullmatch(r"B[0-9]+", batch):
                raise ReferenceError("invalid selected Batch in current_state")
            paths.add(f"artifacts/frontier/{batch}/batch.yaml")
        if state.get("work_record"):
            paths.add(normalize_path(state["work_record"]))
        dispositioned = {item["path"] for item in block["affected_work"] + block["next"].get("work", [])}
        if paths - dispositioned:
            raise ReferenceError("selected work has no continuation disposition: " + ", ".join(sorted(paths - dispositioned)))
    return {"status": "current", "next": block["next"]["kind"], "sources_checked": len(current),
            "limit": "Structural applicability only; the owner judges value, dependencies and actual next work."}


def _check_result_continuation(root: Path, owner_path: str, result: dict) -> None:
    decision = result.get("feedback_decision", {})
    if not isinstance(decision, dict):
        raise ReferenceError("feedback_decision must be a mapping")
    required = decision.get("action") == "wait"
    block = result.get("continuation")
    if required and block is None:
        raise ReferenceError("wait result requires continuation associated with this result")
    if block is not None or required:
        check_continuation(root, owner_path, block, required=required)


def _source_pointer(root: Path, commit: str, owner_path: str, value: str) -> dict:
    if not isinstance(value, str) or not value.strip():
        raise ReferenceError("owner source pointer must be path#section")
    path, _, section = value.partition("#")
    path = normalize_path(posixpath.normpath(str(Path(owner_path).parent / path))) if path else owner_path
    ref = reference(root, commit, path)
    if section:
        ref["section"] = section
    _source_text(root, ref)
    return ref


def _linked_paths(owner_path: str, text: str) -> set[str]:
    paths = {owner_path}
    for link in re.findall(r"\[[^\]]*\]\(([^)]+)\)", text):
        path = link.split("#", 1)[0]
        if path and "://" not in path:
            try:
                paths.add(normalize_path(posixpath.normpath(str(Path(owner_path).parent / path))))
            except ReferenceError:
                continue
    return paths


def _objective_inputs(root: Path, commit: str, owner_source: str, current_work_source: str | None = None,
                      feedback_trigger: str | None = None, feedback_not_due: str | None = None) -> dict:
    if not owner_source:
        raise ReferenceError("new resolver preparation requires an adopted --owner-source")
    owner = reference(root, commit, owner_source)
    text = read_reference(root, owner).decode()
    metadata = _source_metadata(text)
    configured = metadata.get("objective_basis", {})
    if not isinstance(configured, dict):
        raise ReferenceError("owner objective_basis must be a mapping")
    basis = {}
    association = {}
    controlling_binding = None
    if metadata.get("type") == "Optimization Frontier":
        problem = _source_pointer(root, commit, owner_source, metadata.get("problem"))
        parent_text = read_reference(root, problem).decode()
        controlling_binding = {"source": {key: problem[key] for key in ("path", "commit")},
                               "sha256": sha256_bytes(parent_text.encode())}
        parent = _source_metadata(parent_text)
        if metadata.get("problem_epoch") is None or parent.get("epoch") != metadata["problem_epoch"]:
            raise ReferenceError("adopted problem epoch differs from the owning source")
        association = {"problem": problem["path"], "problem_epoch": metadata["problem_epoch"]}
        if metadata.get("representation"):
            representation = _source_pointer(root, commit, owner_source, metadata["representation"])
            representation_meta = _source_metadata(read_reference(root, representation).decode())
            if representation_meta.get("representation_revision") != metadata.get("representation_revision"):
                raise ReferenceError("adopted representation revision differs from the owning source")
            if representation_meta.get("problem_epoch") != metadata["problem_epoch"]:
                raise ReferenceError("representation belongs to a different problem epoch")
            associated_problem = _source_pointer(root, commit, representation["path"], representation_meta.get("problem"))
            if associated_problem["path"] != problem["path"]:
                raise ReferenceError("representation belongs to a different problem source")
            association.update(representation=representation["path"], representation_revision=metadata.get("representation_revision"))
        for role in ("objective_source", "evaluation_source"):
            selected = _source_pointer(root, commit, owner_source, configured[role]) if role in configured else problem
            if selected["path"] not in _linked_paths(problem["path"], parent_text):
                raise ReferenceError(f"{role} is not associated with the adopted problem")
            basis[role] = selected
        if not isinstance(metadata.get("current_state"), dict) or not metadata["current_state"]:
            raise ReferenceError("Frontier owner needs current_state")
        basis["current_work_source"] = {**owner, "field": "current_state"}
    else:
        for role in ("objective_source", "evaluation_source", "current_work_source"):
            basis[role] = _source_pointer(root, commit, owner_source, configured[role]) if role in configured else owner
        controlling = basis["objective_source"]
        controlling_binding = {"source": {key: controlling[key] for key in ("path", "commit")},
                               "sha256": sha256_bytes(read_reference(root, controlling))}
    selected_work = current_work_source or configured.get("current_work_source")
    if selected_work:
        selected = _source_pointer(root, commit, owner_source, selected_work)
        if selected["path"] not in _linked_paths(owner_source, text):
            raise ReferenceError("current_work_source must be linked by its adopted owner")
        basis["current_work_source"] = selected
    explicit_timing = feedback_trigger is not None or feedback_not_due is not None
    trigger = feedback_trigger if explicit_timing else metadata.get("feedback_trigger")
    not_due = feedback_not_due if explicit_timing else metadata.get("feedback_not_due")
    if bool(trigger) == bool(not_due):
        raise ReferenceError("supply exactly one feedback_trigger or feedback_not_due reason for current work")
    if not_due is not None and (not isinstance(not_due, str) or not not_due.strip()):
        raise ReferenceError("feedback_not_due must explain timing for current work")
    if trigger is not None and (not isinstance(trigger, str) or not trigger.strip()):
        raise ReferenceError("feedback_trigger must describe the due timing event")
    content = {role: _source_text(root, source) for role, source in basis.items()}
    # Owner-selected sections define scope. Preserve opaque text, including
    # string literals and indentation that can change evaluation meaning.
    facts = {role: value.replace("\r\n", "\n") for role, value in content.items()}
    facts.update(association=association, feedback_trigger=trigger, feedback_not_due=not_due,
                 owner_timing={key: metadata.get(key) for key in ("feedback_trigger", "feedback_not_due")},
                 source_bindings={key: {k: v for k, v in source.items() if k != "commit"} for key, source in basis.items()})
    if metadata.get("type") == "Optimization Frontier":
        facts["current_state"] = metadata["current_state"]
    return {"objective_owner": owner, "objective_basis": basis, "objective_basis_content": content,
            **({"controlling_objective_binding": controlling_binding} if controlling_binding else {}),
            "objective_basis_identity": "frontier-objective-basis-sha256:" + sha256_bytes(canonical_json(facts)),
            "objective_basis_options": {"current_work_source": current_work_source, "feedback_trigger": feedback_trigger, "feedback_not_due": feedback_not_due},
            "feedback_trigger": trigger, "feedback_not_due": not_due}


def _same_controlling_context(left: dict, right: dict) -> bool:
    """Compare supplied source content without treating a commit as a new goal."""
    def identity(value):
        binding = value.get("controlling_objective_binding")
        if not isinstance(binding, dict) or not isinstance(binding.get("source"), dict):
            return None
        return {"path": binding.get("source", {}).get("path"), "sha256": binding.get("sha256")}
    return identity(left) == identity(right)


def _validate_objective_inputs(root: Path, prepared: dict, *, refresh_prior_context: bool = False) -> dict:
    owner = prepared.get("objective_owner")
    if not isinstance(owner, dict):
        raise ReferenceError("new commitment requires prepared objective_owner and objective_basis")
    options = prepared.get("objective_basis_options", {})
    original = _objective_inputs(root, owner["commit"], owner["path"], **options)
    binding = prepared.get("controlling_objective_binding")
    if binding is not None and binding != original.get("controlling_objective_binding"):
        raise ReferenceError("supplied controlling objective binding differs from its saved source")
    if original.get("controlling_objective_binding") and binding is None and not refresh_prior_context:
        raise ReferenceError("legacy input lacks controlling objective context; refresh owner context before adoption")
    if "objective_basis_content" in prepared and prepared["objective_basis_content"] != original["objective_basis_content"]:
        raise ReferenceError("supplied objective content differs from the owning sources")
    if prepared.get("objective_basis") != original["objective_basis"]:
        raise ReferenceError("objective_basis differs from its adopted owner bindings")
    if any(prepared.get(key) != original[key] for key in ("feedback_trigger", "feedback_not_due")):
        raise ReferenceError("feedback timing differs from its prepared owner basis")
    current = _objective_inputs(root, resolve_revision(root, "HEAD"), owner["path"], **options)
    if current["objective_basis_identity"] != original["objective_basis_identity"]:
        raise ReferenceError("decision-relevant objective basis changed; return affected facts to the owner")
    if not refresh_prior_context and not _same_controlling_context(current, original):
        raise ReferenceError("controlling objective context changed; refresh owner context before adoption; this does not require a different selection or a new experiment")
    return original


def prepare_adoption_context(root: Path, owner_path: str, *, assignment: str | None = None,
                             decision: str | dict | None = None, task_sources=(),
                             controlling_source: str | None = None, phase: str = "adoption",
                             revision: str | None = None, incoming: dict | None = None,
                             account: dict | None = None) -> dict:
    """Present actual sources for owner judgment; neither choose scope nor certify it.

    Recovery reads saved working bytes without Git, a session, or a known finding.
    Resolver preparation can instead retain its historical input revision.
    """
    root = root.resolve()
    if Path(owner_path).is_absolute():
        owner_path = Path(owner_path).resolve().relative_to(root).as_posix()
    owner_path = normalize_path(owner_path)
    captured, catalog, source_indices, limitations = {}, [], {}, []
    from context_delivery import digest, retain_source
    adopted_account = None
    incorporated = {}

    def supplied_body(value, *, omit_objective_projection=False):
        generated = {"adoption_context"}
        if omit_objective_projection:
            generated.add("objective_basis_content")
        omitted = sorted(generated.intersection(value))
        return {"provided_body": {key: item for key, item in value.items() if key not in omitted},
                **({"omitted_generated_fields": omitted} if omitted else {})}

    def pointer(value, *, relative_to=None):
        if isinstance(value, dict):
            ref = {key: value[key] for key in ("path", "section", "field", "commit") if key in value}
        elif isinstance(value, str) and value.strip():
            path, _, section = value.partition("#")
            if relative_to:
                path = posixpath.normpath(str(Path(relative_to).parent / path)) if path else relative_to
            ref = {"path": path}
            if section:
                ref["section"] = section
        else:
            raise ReferenceError("context source needs a path or source reference")
        path = Path(ref["path"])
        if path.is_absolute():
            ref["path"] = path.resolve().relative_to(root).as_posix()
        ref["path"] = normalize_path(ref["path"])
        if revision and "commit" not in ref:
            ref["commit"] = revision
        return ref

    def presentation(body, scope, path):
        """Select known current-record surfaces; never summarize arbitrary prose."""
        parsed = _source_metadata(body)
        frontmatter = re.match(r"\A---\s*\n(.*?)\n---", body, re.S)
        if (scope == "current_owner" and frontmatter and
                parsed.get("type") == "Optimization Frontier" and isinstance(parsed.get("current_state"), dict)):
            try:
                brief = _selected_text(body, {"section": "brief"})
            except ValueError:
                # No maintained explanation means no silent narrative deletion.
                return {"contents": body}
            return {"contents": frontmatter.group(0) + "\n\n" + brief,
                    "presentation": "frontier_current_metadata_and_brief",
                    "omitted_source_parts": [{"part": "other_markdown_sections", "reason": "Current metadata and the existing Brief are delivered; historical events remain available in the exact evidence snapshot. The Brief is not a certificate of current applicability or research completeness."}]}
        if (scope == "current_task" and isinstance(parsed.get("batch"), str) and
                isinstance(parsed.get("definition"), dict) and isinstance(parsed.get("current"), dict) and
                isinstance(parsed.get("attempts"), list)):
            shown, omitted = dict(parsed), []
            shown["attempts"] = []
            for index, attempt in enumerate(parsed["attempts"]):
                if (index < len(parsed["attempts"]) - 1 and isinstance(attempt, dict) and
                        attempt.get("status") in {"completed", "failed"}):
                    # Results may carry cumulative learning or deferral limits.
                    # Preserve them even on old attempts; only duplicate historical
                    # check/observation surfaces use recoverable source pointers.
                    result_identity = digest(canonical_json(attempt.get("result")).decode())
                    covered = (incorporated.get((path, None)) == digest(body) or
                               incorporated.get((path, attempt.get("attempt"))) == result_identity)
                    fields = ("checks", "observations", "result") if covered else ("checks", "observations")
                    history = {key for key in fields if key in attempt}
                    shown["attempts"].append({key: item for key, item in attempt.items() if key not in history})
                    omitted.extend({"json_pointer": f"/attempts/{index}/{key}", "reason": "Historical observation detail; current observations, attempt status, actions, effects, resource use and recovery terms remain visible."} for key in sorted(history))
                else:
                    shown["attempts"].append(attempt)
            return {"contents": yaml.safe_dump(shown, sort_keys=False, allow_unicode=True),
                    "presentation": "batch_current_work_and_attempt_effects", "omitted_source_parts": omitted}
        try:
            parsed_json = json.loads(body)
        except (ValueError, TypeError):
            parsed_json = None
        if isinstance(parsed_json, dict) and "adoption_context" in parsed_json:
            return {"contents": json.dumps({name: item for name, item in parsed_json.items() if name != "adoption_context"}, ensure_ascii=False, indent=2),
                    "omitted_generated_fields": ["adoption_context"]}
        return {"contents": body}

    def document(ref, role, scope="full"):
        key = (ref["path"], ref.get("commit"))
        if key not in captured:
            try:
                captured[key] = (read_reference(root, ref).decode("utf-8") if ref.get("commit")
                                 else _working_text(root, ref["path"]))
            except (OSError, ValueError) as exc:
                limitations.append(f"{role}: {exc}")
                return {"source": ref, "unavailable": str(exc)}
        body = captured[key]
        if key not in source_indices:
            source_indices[key] = len(catalog)
            catalog.append({"source": {name: ref[name] for name in ("path", "commit") if name in ref},
                            "sha256": sha256_bytes(body.encode("utf-8")), **presentation(body, scope, ref["path"])})
        elif scope == "full" and "presentation" in catalog[source_indices[key]]:
            # A source also serving as a goal, decision or incoming assignment
            # needs its full substantive body, regardless of the first role.
            catalog[source_indices[key]] = {"source": catalog[source_indices[key]]["source"],
                                           "sha256": sha256_bytes(body.encode("utf-8")), **presentation(body, "full", ref["path"])}
        value = {"source": ref, "source_index": source_indices[key]}
        if ref.get("field") or ref.get("section"):
            try:
                value["selected_contents"] = _selected_text(body, ref)
            except (ValueError, TypeError, KeyError, yaml.YAMLError) as exc:
                value["selection_unavailable"] = str(exc)
                limitations.append(f"{role}: selector unavailable; the original body is provided")
        return value

    owner_ref = pointer(owner_path)
    owner_body = (read_reference(root, owner_ref).decode("utf-8") if owner_ref.get("commit")
                  else _working_text(root, owner_path))
    captured[(owner_path, owner_ref.get("commit"))] = owner_body
    metadata = _source_metadata(owner_body)
    association = account if account is not None else metadata.get("context_account")
    if association is not None:
        if not isinstance(association, dict) or not isinstance(association.get("source"), dict):
            raise ReferenceError("context_account needs an adopted source reference")
        account_ref = pointer(association["source"])
        try:
            account_body = (read_reference(root, account_ref).decode("utf-8") if account_ref.get("commit")
                            else _working_text(root, account_ref["path"]))
            selected_account = _selected_text(account_body, account_ref)
        except (OSError, ValueError, KeyError) as exc:
            account_body, selected_account = None, ""
            limitations.append(f"Adopted account unavailable; retain necessary explicit context: {exc}")
        if digest(selected_account) != association.get("sha256"):
            # Preserve explicit context and expose the pending edit, never silently adopt it.
            limitations.append("The adopted account passage changed; its proposed update is not adopted by file recency. Necessary source context is retained.")
            adopted_account = {"source": account_ref, "pending_contents": selected_account,
                               "adoption": "changed_since_association"}
            previous = root / "artifacts/workflow-harness/context-sources" / f"{association.get('sha256')}.txt"
            if previous.is_file() and digest(previous.read_bytes().decode()) == association.get("sha256"):
                adopted_account["contents"] = previous.read_bytes().decode()
                adopted_account["sha256"] = association["sha256"]
        else:
            adopted_account = {"source": account_ref, "contents": selected_account,
                               "sha256": digest(selected_account), "adoption": "owner_associated",
                               "incorporates": association.get("incorporates", [])}
            incorporated = {(item["path"], item.get("attempt")): item["sha256"] for item in association.get("incorporates", [])}
            retain_source(root, selected_account)
        if account_body is not None:
            captured[(account_ref["path"], account_ref.get("commit"))] = account_body
            adopted_account["retrieval"] = retain_source(root, account_body)
    owner = document(owner_ref, "owner", "current_owner")
    if "source_index" not in owner:
        raise ReferenceError("cannot read the owner for adoption or recovery")
    metadata = _source_metadata(captured[(owner_ref["path"], owner_ref.get("commit"))])
    configured = metadata.get("objective_basis", {})
    if not isinstance(configured, dict):
        raise ReferenceError("owner objective_basis must be a mapping")
    problem = metadata.get("problem") if metadata.get("type") == "Optimization Frontier" else None
    selected = {}
    for role in ("objective_source", "evaluation_source", "current_work_source"):
        value = configured.get(role) or (problem if role != "current_work_source" else None)
        ref = pointer(value, relative_to=owner_path) if value else owner_ref
        selected[role] = document(ref, role, "current_owner" if ref == owner_ref and role == "current_work_source" else
                                  "current_task" if role == "current_work_source" else "full")
    controlling = controlling_source or problem or configured.get("objective_source")
    controlling_ref = (pointer(controlling_source) if controlling_source else
                       pointer(controlling, relative_to=owner_path) if controlling else owner_ref)
    controlling_context = document(controlling_ref, "controlling objective context")
    controlling_context["basis"] = ("explicit_controlling_source" if controlling_source else
                                     "adopted_problem" if problem else
                                     "owner_configured_source" if controlling else "owner_only")
    if not controlling:
        limitations.append("Only the task owner is supplied. Its relationship to any broader objective is not established by this view; a standalone task needs no invented parent.")

    assignments = []
    if assignment:
        assignments.append(document(pointer(assignment), "incoming assignment"))
    if incoming is not None:
        assignments.append(supplied_body(incoming, omit_objective_projection=True))
    decision_context = None
    retained_basis = metadata.get("continuation", {}).get("basis") if isinstance(metadata.get("continuation"), dict) else None
    if isinstance(decision, str) or (decision is None and isinstance(retained_basis, dict) and retained_basis.get("path")):
        decision_ref = pointer(decision) if isinstance(decision, str) else pointer(retained_basis)
        decision_context = document(decision_ref, "decision")
        decision_body = _source_metadata(catalog[decision_context["source_index"]]["contents"]) if "source_index" in decision_context else {}
    else:
        decision_body = decision or {}
        if decision is not None:
            decision_context = supplied_body(decision)
    inherited_assignment = decision_body.get("assignment")
    if isinstance(inherited_assignment, dict) and "path" in inherited_assignment:
        assignments.append(document(pointer(inherited_assignment), "decision's incoming assignment"))
    elif inherited_assignment is not None:
        assignments.append({"provided_body": inherited_assignment})

    # Current work is separate from the controlling objective. Preserve all
    # selected tasks; a pending primary observation may coexist with research.
    paths = list(task_sources)
    state = metadata.get("current_state", {})
    if isinstance(state, dict):
        if state.get("work_record"):
            paths.append(state["work_record"])
        batches = [state.get("primary_batch"), *state.get("parallel_batches", [])]
        paths.extend(f"artifacts/frontier/{batch}/batch.yaml" for batch in batches if isinstance(batch, str) and re.fullmatch(r"B[0-9]+", batch))
    tasks = []
    for path in dict.fromkeys(paths):
        tasks.append(document(pointer(path), "outgoing or selected task", "full" if path in task_sources and not incorporated else "current_task"))
    if not assignments:
        limitations.append("No separate incoming assignment was supplied; inspect the owner's inherited question and completion conditions.")
    if not tasks:
        limitations.append("No separate outgoing task was supplied or selected; the owner body is the available current work context.")

    actual_use = list(dict.fromkeys([*paths, *(association or {}).get("actual_use", [])]))
    # Supporting evidence and action dependencies remain distinct, but both
    # declared bases must be captured before they can be checked at delivery.
    dependencies = [*actual_use, *(item["path"] for item in (association or {}).get("incorporates", []))]
    for path in dict.fromkeys(dependencies):
        ref = pointer(path)
        key = (ref["path"], ref.get("commit"))
        if key not in captured:
            try:
                captured[key] = (read_reference(root, ref).decode("utf-8") if ref.get("commit") else _working_text(root, path))
            except (OSError, ValueError) as exc:
                limitations.append(f"Declared dependency unavailable: {path}: {exc}")
                continue
        if key not in source_indices:
            source_indices[key] = len(catalog)
            catalog.append({"source": ref, "sha256": digest(captured[key]),
                            "retrieval": retain_source(root, captured[key]),
                            "purpose": "Declared supporting evidence or actual-use dependency; not new authority."})
    for item in (association or {}).get("incorporates", []):
        body = captured.get((item["path"], pointer(item["path"]).get("commit")))
        if body is None:
            continue
        observed = digest(body)
        if item.get("attempt") is not None:
            attempts = _source_metadata(body).get("attempts", [])
            result = next((a.get("result") for a in attempts if a.get("attempt") == item["attempt"]), None)
            observed = digest(canonical_json(result).decode())
        if observed != item["sha256"]:
            limitations.append(f"Incorporated basis changed: {item['path']}; reconcile the affected interpretation. The adopted explanation is not a fresh evidence claim.")

    # Do not combine old applicability with a later reread of changed content.
    for (path, commit), body in captured.items():
        if commit is None and _working_text(root, path) != body:
            raise ReferenceError(f"adoption context changed while reading: {path}")
    # Every source body omitted from delivery has an exact, role-readable copy.
    for item in catalog:
        key = (item["source"]["path"], item["source"].get("commit"))
        if item.get("contents") != captured[key]:
            item["retrieval"] = retain_source(root, captured[key])
    value = {"phase": phase, "sources": catalog, "owner": owner, "controlling_context": controlling_context,
            "selected_sources": selected, "incoming_assignments": assignments,
            "decision": decision_context, "outgoing_tasks": tasks, "limitations": limitations,
            "current_account": adopted_account, "actual_use": actual_use,
            "instruction": "Each source_index refers to one presentation in sources. Reuse the applicable owner-associated account; unincorporated results remain evidence, not adopted meaning. Current Frontier metadata and Brief remain visible. Omitted material is available through exact retrieval snapshots; inspect surrounding evidence independently and pursue new external evidence when useful. A delivered_content_ref is a JSON pointer to identical text in this input. Original task dependencies remain actual_use even when their presentation changes. Determine the controlling objective and source qualifications separately from local scope. A hash, focused label or cached account establishes neither semantic authority nor research completeness. Preserve real limits, pending effects and independent choices. Native hosts must verify the exact prepared input immediately before sending; opaque host paths remain advisory. This view supplies evidence, not a verdict or permission."}
    if adopted_account is not None and account_body is not None:
        # Include its version in the same scoped source checks as other inputs.
        key = (account_ref["path"], account_ref.get("commit"))
        if key not in source_indices:
            value["sources"].append({"source": {k: v for k, v in account_ref.items() if k in {"path", "commit"}},
                                     "sha256": digest(account_body), "retrieval": adopted_account["retrieval"]})
    value["delivery_identity"] = digest(json.dumps(value, ensure_ascii=False, sort_keys=True))
    return value


def _feedback_decision(prepared: dict, result: dict) -> None:
    trigger = prepared.get("feedback_trigger")
    if not trigger:
        return
    decision = result.get("feedback_decision")
    if not isinstance(decision, dict) or any(not isinstance(decision.get(key), str) or not decision[key].strip()
                                             for key in ("trigger", "action", "basis", "next_condition")):
        raise ReferenceError("due timing judgment requires feedback_decision: trigger, action, basis, next_condition")
    if decision["trigger"] != trigger:
        raise ReferenceError("feedback_decision trigger differs from the due event")
    if decision["action"] not in {"observe", "prepare", "request_authority", "wait", "prefer_other_work", "retire"}:
        raise ReferenceError("unsupported feedback_decision action")
    pointer = decision["basis"]
    if not pointer.startswith("/") or pointer.startswith("/feedback_decision"):
        raise ReferenceError("feedback_decision basis must point to the comparison in this result using a JSON pointer")
    value = result
    try:
        for key in pointer[1:].split("/"):
            key = key.replace("~1", "/").replace("~0", "~")
            value = value[int(key)] if isinstance(value, list) else value[key]
    except (KeyError, TypeError, ValueError, IndexError) as exc:
        raise ReferenceError("feedback_decision basis does not resolve in this result") from exc
    if not value:
        raise ReferenceError("feedback_decision basis is empty")


@_cached_reference_operation
def prepare_resolver(root: Path, revision: str, path: str, prior_paths=(), *, owner_source: str,
                     current_work_source: str | None = None, feedback_trigger: str | None = None, feedback_not_due: str | None = None) -> dict:
    """Return input binding or reuse an existing resolution; never choose a row."""
    ref = reference(root, revision, path)
    _, identity = _evidence(root, ref)
    if normalize_path(owner_source) == ref["path"]:
        raise ReferenceError("objective owner must be separate from the recommendation evidence")
    objective = _objective_inputs(root, ref["commit"], owner_source, current_work_source, feedback_trigger, feedback_not_due)
    prepared = {"evidence_source": ref, "evidence_state_identity": identity,
                "decision_policy": _decision_policy(root), **objective}
    _validate_objective_inputs(root, prepared)
    from current_use import inspect_current_use
    current_use = inspect_current_use(root, owner_source)
    if current_use is not None:
        prepared["current_use"] = current_use
    for prior_path in prior_paths:
        prior_ref = reference(root, ref["commit"], prior_path)
        prior = _document(read_reference(root, prior_ref))
        if "evidence_source" in prior:
            _, previous = _evidence(root, prior["evidence_source"])
        else:
            # Retained resolutions may expose the same key under identity_reproduction.
            previous = prior.get("evidence_state_identity") or prior.get("identity_reproduction", {}).get("evidence_state_identity")
            if not previous:
                raise ReferenceError("prior resolution needs its original evidence reference or retained identity")
        if previous == identity and prior.get("objective_basis"):
            # A live correction is independent of historical evidence identity.
            # Open corrections remain visible to the resolver, never a reuse pass.
            if (current_use and current_use["blocked_ids"]) or prior.get("current_use") != current_use:
                continue
            old_owner = prior.get("objective_owner", {})
            old_basis = _objective_inputs(root, old_owner["commit"], old_owner["path"], **prior.get("objective_basis_options", {}))
            if prior["objective_basis"] != old_basis["objective_basis"]:
                raise ReferenceError("prior objective basis differs from its owner")
            if old_basis["objective_basis_identity"] != objective["objective_basis_identity"]:
                continue
            if not _same_controlling_context(prior, old_basis) or not _same_controlling_context(old_basis, objective):
                # Refresh the owner input instead of silently reusing stale full
                # goal context. The owner may retain the same supported decision.
                continue
            _feedback_decision(objective, prior)
            _check_result_continuation(root, owner_source, prior)
            prepared["reuse_resolution"] = prior_ref
            prepared["reused_policy_coverage"] = _policy_coverage(root, prior.get("decision_policy"), prior)
            break
    prepared["adoption_context"] = prepare_adoption_context(
        root, owner_source, revision=ref["commit"], assignment=ref["path"],
        decision=prior if prepared.get("reuse_resolution") else None, phase="investment_preparation")
    return prepared


@_cached_reference_operation
def bind_resolution(root: Path, prepared: dict, result: dict, *, historical_source: dict | None = None) -> dict:
    """Bind an existing result body to saved input without transcribing a digest."""
    if prepared.get("reuse_resolution"):
        raise ReferenceError("reuse the referenced resolution instead of publishing another")
    if not prepared.get("objective_owner") and result.get("evidence_source") and not result.get("objective_basis"):
        if historical_source is None or _document(read_reference(root, historical_source)) != result:
            raise ReferenceError("historical rebinding requires the unchanged saved result; prepare an objective basis for new work")
        _, old_identity = _evidence(root, result["evidence_source"])
        _, prepared_identity = _evidence(root, prepared["evidence_source"])
        if old_identity != prepared_identity:
            raise ReferenceError("historical result belongs to different decision facts")
        return {**result, "evidence_state_identity": old_identity}
    objective = _validate_objective_inputs(root, prepared)
    from current_use import inspect_current_use
    current_use = inspect_current_use(root, objective["objective_owner"]["path"])
    if current_use != prepared.get("current_use"):
        raise ReferenceError("current-use correction changed; prepare from saved adopted objects")
    if "current_use" in result and result["current_use"] != current_use:
        raise ReferenceError("result cannot replace the prepared current-use association")
    _feedback_decision(objective, result)
    _check_result_continuation(root, objective["objective_owner"]["path"], result)
    if result.get("objective_basis"):
        previous_basis = _validate_objective_inputs(root, result, refresh_prior_context=True)
        if previous_basis["objective_basis_identity"] != objective["objective_basis_identity"]:
            raise ReferenceError("result belongs to a different objective basis")
    elif result.get("evidence_source"):
        raise ReferenceError("historical judgment has no objective basis for this new commitment")
    ref = prepared["evidence_source"]
    _, identity = _evidence(root, ref)
    if result.get("evidence_source"):
        _, previous = _evidence(root, result["evidence_source"])
        if previous != identity:
            raise ReferenceError("result belongs to different decision facts")
    # Derived fields are owned here. Professional result fields are preserved.
    # Rebinding an existing judgment does not retroactively apply new guidance to it.
    policy = result.get("decision_policy", prepared.get("decision_policy"))
    # Keep the supplied policy identity with this result; the full text stays in its assignment.
    retained_policy = {key: value for key, value in policy.items() if key not in {"text", "instruction"}} if isinstance(policy, dict) else {"status": "not_provided"}
    retained_objective = {key: value for key, value in objective.items() if key != "objective_basis_content"}
    current_binding = {"current_use": current_use} if current_use is not None else {}
    return {**result, **retained_objective, **current_binding, "evidence_source": ref, "evidence_state_identity": identity,
            "decision_policy": retained_policy, "policy_coverage": _policy_coverage(root, policy, result),
            "adoption_context": prepare_adoption_context(root, objective["objective_owner"]["path"],
                revision=objective["objective_owner"]["commit"], decision=result, incoming=prepared,
                phase="result_adoption")}


def _anchor(text: str) -> str:
    return re.sub(r"\s+", "-", re.sub(r"[^\w\s-]", "", text.lower().strip()))


@_cached_reference_operation
def prepare_design(root: Path, revision: str, work: str, scope=()) -> dict:
    """Resolve the current Design map and stable-slice traceability at one commit."""
    ref = reference(root, revision, work)
    commit = ref["commit"]
    files = {ref["path"]: read_reference(root, ref)}

    def pointer(value):
        if not isinstance(value, str) or not value.strip():
            raise ReferenceError("design pointer must be path#section-anchor")
        link = re.fullmatch(r"\[[^\]]*\]\(([^)]+)\)", value.strip())
        value = (link.group(1) if link else value.strip()).strip("`")
        path, _, section = value.partition("#")
        path = normalize_path(path)
        if path not in files:
            files[path] = read_reference(root, {"commit": commit, "path": path})
        if section:
            headings = re.findall(r"^#{1,6}\s+(.+?)\s*#*\s*$", files[path].decode(), re.M)
            if sum(_anchor(h) == section for h in headings) != 1:
                raise ReferenceError(f"missing or ambiguous design section: {value}")
        return path

    text = files[ref["path"]].decode()
    match = re.search(r"^## Design map\s*\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    if not match:
        raise ReferenceError("W needs a Design map")
    concerns = set()
    for line in match.group(1).splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if line.strip().startswith("|") and len(cells) >= 2 and cells[0] not in {"Concern", "---"}:
            concerns.add(pointer(cells[1]))
    if not concerns:
        raise ReferenceError("Design map needs indexed concerns")
    trace_path = str(Path(ref["path"]).parent / "design/traceability.yaml")
    pointer(trace_path)
    trace = _document(files[trace_path])
    frontmatter = re.match(r"\A---\s*\n(.*?)\n---", text, re.S)
    if frontmatter:
        owner = _document(frontmatter.group(1).encode())
        if any(trace.get(key) != owner.get(key) for key in ("work_id", "plan_revision")):
            raise ReferenceError("traceability belongs to a different W revision")
    slices = trace.get("slices")
    if not isinstance(slices, dict) or not slices:
        raise ReferenceError("current traceability needs stable slices")
    selected = list(scope) if scope else list(slices)
    if len(set(selected)) != len(selected) or any(key not in slices for key in selected):
        raise ReferenceError("unknown or duplicate selected slice")
    for key, item in slices.items():
        if not isinstance(key, str) or not isinstance(item, dict):
            raise ReferenceError("invalid slice")
        prerequisites = item.get("prerequisites")
        inputs = item.get("required_design_inputs")
        if not isinstance(prerequisites, list) or not isinstance(inputs, list):
            raise ReferenceError(f"slice {key} needs prerequisites and design inputs")
        if any(dep not in slices for dep in prerequisites):
            raise ReferenceError(f"slice {key} has an unknown prerequisite")
        if key in selected and any(dep not in selected for dep in prerequisites):
            raise ReferenceError(f"selected scope omits prerequisite of {key}")
        for value in [item.get("verification_pointer"), *inputs]:
            if pointer(value) not in concerns:
                raise ReferenceError(f"slice {key} uses an unindexed concern")
    return {"subject": {"commit": commit, "paths": sorted(files)}, "work_plan": ref["path"], "delivery_scope": selected}


def _write(path: Path, value: dict, *, merge: bool = False) -> None:
    if merge and path.exists():
        existing = _document(path.read_bytes())
        for key in ("evidence_source", "evidence_state_identity", "reuse_resolution", "reused_policy_coverage", "subject", "work_plan", "delivery_scope", "objective_owner", "objective_basis", "objective_basis_content", "objective_basis_identity", "objective_basis_options", "controlling_objective_binding", "feedback_trigger", "feedback_not_due", "current_use", "adoption_context"):
            if key in value or key in {"reuse_resolution", "reused_policy_coverage", "current_use"}:
                existing.pop(key, None)
        value = {**existing, **value}
    raw = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        try:
            stream.write(raw)
            stream.close()
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)


def register_hook_record(root: Path, output: Path, phase: str, session_id: str | None = None) -> bool:
    """Retain a proposal reference without replacing the owner's adopted work."""
    from frontier_context import root_session
    session = root_session(session_id)
    if session is None:
        return False
    root, output = root.resolve(), output.resolve(strict=True)
    if not output.is_relative_to(root) or not (root / DECISION_POLICY_PATH).is_file():
        return False
    directory = root / ".frontier/hook-context"
    directory.mkdir(parents=True, exist_ok=True)
    _write(directory / f"{session}-proposal.json", {"workspace": str(root), "session_id": session,
           "record": str(output), "phase": phase})
    return True


@_cached_reference_operation
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=("design", "resolver", "bind-resolution", "prepare-adoption", "recover-work", "verify-delivery", "read-evidence", "check-continuation", "check-current-use", "adopt-work", "bind-return", "batch-review", "batch-update", "batch-view"))
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--revision", help="chosen saved revision; defaults to HEAD for reference preparation")
    parser.add_argument("--path", help="W, evidence, review, or existing prepared assignment path")
    parser.add_argument("--owner-source", help="adopted Frontier or task source at the saved revision; required for resolver")
    parser.add_argument("--current-work-source", help="owner-linked work path#section, relative to owner")
    parser.add_argument("--controlling-source", help="current controlling request/objective repository-relative path#section; source role remains an owner judgment")
    parser.add_argument("--assignment", help="saved incoming assignment path for adoption or recovery context")
    parser.add_argument("--account", type=Path, help="existing owner-adopted context association; no automatic summary adoption")
    parser.add_argument("--raw", action="store_true", help="explicit full diagnostic export; never the default dispatch input")
    parser.add_argument("--correction-request", type=Path, help="existing adopt-work correction request with corrections, replacements and relations")
    parser.add_argument("--source", action="append", default=[], help="saved object used by the affected action; repeat for current-use checks")
    timing = parser.add_mutually_exclusive_group()
    timing.add_argument("--feedback-trigger", help="observed event requiring a feedback timing decision")
    timing.add_argument("--feedback-not-due", help="why current work does not require a timing decision")
    parser.add_argument("--session", help="explicit root owner for adopted-work registration")
    parser.add_argument("--call", help="actual native tool_use_id for an existing work return")
    parser.add_argument("--scope", action="append", default=[])
    parser.add_argument("--prior", action="append", default=[], help="known resolution path at revision; repeat as needed")
    parser.add_argument("--result", type=Path, help="existing result draft for binding")
    parser.add_argument("--output", type=Path, help="write into the existing assignment or result location")
    parser.add_argument("--batch", help="target Batch for batch-review, batch-update or batch-view")
    parser.add_argument("--handle", help="chosen R handle only when absent from the saved review")
    parser.add_argument("--reason", help="Coordinator's adoption or same-result revision rationale")
    parser.add_argument("--candidate-path", action="append", default=[], help="selected candidate path; repeat as needed")
    parser.add_argument("--limit", action="append", default=[], help="changed operational limit as key=number")
    parser.add_argument("--measurement-updates", type=Path, help="only changed Measurement Definition fields, as YAML or JSON")
    args = parser.parse_args()
    from frontier_batch import AdoptReview, Batch, BatchError, UpdateWorkingState, batch_facts

    try:
        if args.kind == "verify-delivery":
            from context_delivery import verify_prepared
            value = _document((args.repo / args.path).read_bytes())
            verify_prepared(args.repo.resolve(), value)
            value = {"status": "current", "delivery": args.path,
                     "coverage": "Exact supplied prepared view only; send these bytes. Native interception remains unavailable."}
        elif args.kind == "read-evidence":
            from context_delivery import read_retained
            locator = _document((args.repo / args.path).read_bytes())
            value = {"contents": read_retained(args.repo.resolve(), locator)}
        elif args.kind in {"prepare-adoption", "recover-work"}:
            if not args.owner_source:
                raise ReferenceError(f"{args.kind} requires --owner-source")
            value = prepare_adoption_context(args.repo, args.owner_source, assignment=args.assignment,
                decision=str(args.result) if args.result else None, task_sources=args.source,
                controlling_source=args.controlling_source,
                phase="recovery" if args.kind == "recover-work" else "adoption",
                account=_document(args.account.read_bytes()) if args.account else None)
        elif args.kind == "check-current-use":
            if not args.owner_source or not args.source or args.result:
                raise ReferenceError("check-current-use requires --owner-source and actual --source objects")
            from current_use import check_current_use
            value = check_current_use(args.repo, args.owner_source, args.source)
        elif args.kind == "check-continuation":
            if not args.path or args.output or args.result:
                raise ReferenceError("check-continuation requires --path to the adopted owner and writes no output file")
            value = check_continuation(args.repo, args.path, required=True)
        elif args.kind == "bind-return":
            if not args.result or not args.call or args.output:
                raise ReferenceError("bind-return requires --result and --call, without --output")
            from frontier_context import bind_dispatch_return
            value = bind_dispatch_return(args.repo, args.result, args.call, args.session)
        elif args.kind == "adopt-work":
            if not args.path or args.output:
                raise ReferenceError("adopt-work requires --path to saved Selection and no --output")
            from current_use import adopt_current_work
            request = _document(args.correction_request.read_bytes()) if args.correction_request else {}
            if set(request) - {"corrections", "replacements", "relations"}:
                raise ReferenceError("correction request supports corrections, replacements and relations only")
            required = adopt_current_work(args.repo, args.path, sources=args.source, **request)
            context = prepare_adoption_context(args.repo, args.path, assignment=args.assignment,
                decision=str(args.result) if args.result else None, task_sources=args.source,
                controlling_source=args.controlling_source)
            from frontier_context import register_adopted_work
            value = {**required, "adoption_context": context}
            try:
                value["registered"] = register_adopted_work(args.repo, Path(args.path), args.session)
            except (OSError, ValueError) as exc:
                value.update(registered=False, native_context_warning=str(exc))
        elif args.kind.startswith("batch-"):
            if not args.batch:
                raise ReferenceError("Batch operations require --batch")
            if args.output:
                raise ReferenceError("Batch operations return stdout; their only write is the existing Batch record")
            batch = Batch.open(args.repo, args.batch)
            if args.kind == "batch-review":
                if not args.path or not args.revision or not args.reason:
                    raise ReferenceError("batch-review requires --path, --revision and --reason")
                view = batch.apply(AdoptReview(args.revision, args.path, args.reason, args.handle))
            elif args.kind == "batch-update":
                if not args.reason:
                    raise ReferenceError("batch-update requires --reason")
                limits = {}
                for item in args.limit:
                    key, separator, number = item.partition("=")
                    if not separator or key in limits:
                        raise ReferenceError("each --limit must be a distinct key=number")
                    limits[key] = json.loads(number)
                view = batch.apply(UpdateWorkingState(
                    rationale=args.reason, revision=args.revision,
                    paths=tuple(args.candidate_path) if args.candidate_path else None,
                    resource_limits=limits or None,
                    measurement_updates=_document(args.measurement_updates.read_bytes()) if args.measurement_updates else None,
                ))
            else:
                view = batch.view
            value = batch_facts(view)
        elif not args.path:
            raise ReferenceError("reference preparation requires --path")
        elif args.kind == "design":
            value = prepare_design(args.repo, args.revision or "HEAD", args.path, args.scope)
        elif args.kind == "resolver":
            if not args.owner_source:
                raise ReferenceError("resolver requires --owner-source")
            value = prepare_resolver(args.repo, args.revision or "HEAD", args.path, args.prior,
                                     owner_source=args.owner_source, current_work_source=args.current_work_source,
                                     feedback_trigger=args.feedback_trigger, feedback_not_due=args.feedback_not_due)
        else:
            if args.result is None:
                raise ReferenceError("bind-resolution requires --result")
            prepared = _document((args.repo / args.path).read_bytes())
            result = _document(args.result.read_bytes())
            historical_source = None
            if not prepared.get("objective_owner") and result.get("evidence_source"):
                result_path = args.result.resolve().relative_to(args.repo.resolve()).as_posix()
                historical_source = reference(args.repo, args.revision or "HEAD", result_path)
            value = bind_resolution(args.repo, prepared, result, historical_source=historical_source)
        if args.output:
            _write(args.output, value, merge=args.kind != "bind-resolution")
            if args.kind in {"resolver", "bind-resolution"}:
                try:
                    register_hook_record(args.repo, args.output, args.kind)
                except (OSError, ValueError) as exc:
                    print(f"Native decision context not registered; existing result is retained: {exc}", file=sys.stderr)
            if not args.raw:
                from context_delivery import model_view
                # Serialize the newly prepared value, not old fields retained by
                # the internal record merge. The sidecar is the delivery input.
                delivery = args.output.with_name(args.output.stem + ".delivery.json")
                _write(delivery, model_view(args.repo.resolve(), value))
                print(json.dumps({"delivery": str(delivery), "internal_record": str(args.output),
                                  "serialized_bytes": delivery.stat().st_size,
                                  "instruction": "Send the delivery file; the internal record is for exact checks or explicit audit."}))
        else:
            from context_delivery import model_view
            print(json.dumps(value if args.raw else model_view(args.repo.resolve(), value), ensure_ascii=False, indent=2))
        return 0
    except (BatchError, ValueError, KeyError, TypeError, OSError, yaml.YAMLError) as exc:
        print(json.dumps({"status": "NOT_READY", "error": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
