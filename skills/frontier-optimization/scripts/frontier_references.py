#!/usr/bin/env python3
"""Prepare current W and resolver references from saved Git bytes."""

from __future__ import annotations

import argparse
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
    ref = {"commit": resolve_revision(root, revision), "path": normalize_path(path)}
    read_reference(root, ref)
    return ref


def read_reference(root: Path, ref: dict[str, str]) -> bytes:
    return read_file(root, ref.get("commit", ""), ref.get("path", ""))


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
    if metadata.get("type") == "Optimization Frontier":
        problem = _source_pointer(root, commit, owner_source, metadata.get("problem"))
        parent_text = read_reference(root, problem).decode()
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
            "objective_basis_identity": "frontier-objective-basis-sha256:" + sha256_bytes(canonical_json(facts)),
            "objective_basis_options": {"current_work_source": current_work_source, "feedback_trigger": feedback_trigger, "feedback_not_due": feedback_not_due},
            "feedback_trigger": trigger, "feedback_not_due": not_due}


def _validate_objective_inputs(root: Path, prepared: dict) -> dict:
    owner = prepared.get("objective_owner")
    if not isinstance(owner, dict):
        raise ReferenceError("new commitment requires prepared objective_owner and objective_basis")
    options = prepared.get("objective_basis_options", {})
    original = _objective_inputs(root, owner["commit"], owner["path"], **options)
    if "objective_basis_content" in prepared and prepared["objective_basis_content"] != original["objective_basis_content"]:
        raise ReferenceError("supplied objective content differs from the owning sources")
    if prepared.get("objective_basis") != original["objective_basis"]:
        raise ReferenceError("objective_basis differs from its adopted owner bindings")
    if any(prepared.get(key) != original[key] for key in ("feedback_trigger", "feedback_not_due")):
        raise ReferenceError("feedback timing differs from its prepared owner basis")
    current = _objective_inputs(root, resolve_revision(root, "HEAD"), owner["path"], **options)
    if current["objective_basis_identity"] != original["objective_basis_identity"]:
        raise ReferenceError("decision-relevant objective basis changed; return affected facts to the owner")
    return original


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
            old_owner = prior.get("objective_owner", {})
            old_basis = _objective_inputs(root, old_owner["commit"], old_owner["path"], **prior.get("objective_basis_options", {}))
            if prior["objective_basis"] != old_basis["objective_basis"]:
                raise ReferenceError("prior objective basis differs from its owner")
            if old_basis["objective_basis_identity"] != objective["objective_basis_identity"]:
                continue
            _feedback_decision(objective, prior)
            prepared["reuse_resolution"] = prior_ref
            prepared["reused_policy_coverage"] = _policy_coverage(root, prior.get("decision_policy"), prior)
            break
    return prepared


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
    _feedback_decision(objective, result)
    if result.get("objective_basis"):
        previous_basis = _validate_objective_inputs(root, result)
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
    return {**result, **retained_objective, "evidence_source": ref, "evidence_state_identity": identity,
            "decision_policy": retained_policy, "policy_coverage": _policy_coverage(root, policy, result)}


def _anchor(text: str) -> str:
    return re.sub(r"\s+", "-", re.sub(r"[^\w\s-]", "", text.lower().strip()))


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
        for key in ("evidence_source", "evidence_state_identity", "reuse_resolution", "reused_policy_coverage", "subject", "work_plan", "delivery_scope", "objective_owner", "objective_basis", "objective_basis_content", "objective_basis_identity", "objective_basis_options", "feedback_trigger", "feedback_not_due"):
            if key in value or key in {"reuse_resolution", "reused_policy_coverage"}:
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=("design", "resolver", "bind-resolution", "adopt-work", "bind-return", "batch-review", "batch-update", "batch-view"))
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--revision", help="chosen saved revision; defaults to HEAD for reference preparation")
    parser.add_argument("--path", help="W, evidence, review, or existing prepared assignment path")
    parser.add_argument("--owner-source", help="adopted Frontier or task source at the saved revision; required for resolver")
    parser.add_argument("--current-work-source", help="owner-linked work path#section, relative to owner")
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
        if args.kind == "bind-return":
            if not args.result or not args.call or args.output:
                raise ReferenceError("bind-return requires --result and --call, without --output")
            from frontier_context import bind_dispatch_return
            value = bind_dispatch_return(args.repo, args.result, args.call, args.session)
        elif args.kind == "adopt-work":
            if not args.path or args.output:
                raise ReferenceError("adopt-work requires --path to saved Selection and no --output")
            from frontier_context import register_adopted_work
            value = {"registered": register_adopted_work(args.repo, Path(args.path), args.session)}
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
        else:
            print(json.dumps(value, ensure_ascii=False, indent=2))
        return 0
    except (BatchError, ValueError, KeyError, TypeError, OSError, yaml.YAMLError) as exc:
        print(json.dumps({"status": "NOT_READY", "error": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
