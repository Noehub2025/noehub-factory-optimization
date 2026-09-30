"""Mechanical delivery and exact evidence access; never synthesize understanding."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def retain_source(root: Path, text: str) -> dict:
    """Retain only evidence needed by a prepared use, shared across repeat uses."""
    identity = digest(text)
    path = root / "artifacts/workflow-harness/context-sources" / f"{identity}.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes().decode("utf-8") != text:
            raise ValueError(f"evidence snapshot differs: {path}")
    else:
        with tempfile.NamedTemporaryFile(dir=path.parent, mode="wb", delete=False) as stream:
            temporary = Path(stream.name)
            try:
                stream.write(text.encode("utf-8"))
                stream.flush()
                os.fsync(stream.fileno())
                try:
                    os.link(temporary, path)
                except FileExistsError:
                    if path.read_bytes().decode("utf-8") != text:
                        raise ValueError(f"evidence snapshot differs: {path}")
            finally:
                temporary.unlink(missing_ok=True)
    return {"path": path.relative_to(root).as_posix(), "sha256": identity}


def read_retained(root: Path, locator: dict) -> str:
    path = (root / locator["path"]).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("evidence must be inside the workspace")
    text = path.read_bytes().decode("utf-8")
    if digest(text) != locator["sha256"]:
        raise ValueError("retained evidence changed; do not substitute newer bytes")
    return text


def delivery_view(value):
    """Deduplicate exact long strings across nested fields without merging claims.

    JSON pointers refer to a substantive occurrence in this same delivered value.
    Raw exports and internal checker inputs are deliberately unaffected.
    """
    seen = {}

    def visit(item, pointer):
        if isinstance(item, str) and len(item.encode("utf-8")) >= 256:
            if item in seen:
                return {"delivered_content_ref": seen[item]}
            seen[item] = pointer
            # Saved packets sometimes embed another JSON document as text.
            # Expose its structure in the display only, so nested duplication
            # cannot hide behind a second serialization layer.
            try:
                decoded = json.loads(item)
            except ValueError:
                decoded = None
            if isinstance(decoded, (dict, list)):
                return {"decoded_json": visit(decoded, pointer + "/decoded_json")}
        if isinstance(item, dict):
            # Keep machine-consumed locator/scope shapes even for long paths.
            # References replace repeated prose, never an execution dependency.
            structural = {"path", "source_path", "source", "retrieval", "actual_use", "checked_sources", "sha256", "delivery_identity", "judgment_binding", "current_sources"}
            if item.get("judgment_binding") and "sources" not in item:
                # These are the actual judged values. Keep their exact shape so
                # consumption can compare the decision digest as well as uses.
                from frontier_references import _JUDGMENT_DERIVED
                structural.update(set(item) - _JUDGMENT_DERIVED)
            return {key: part if key in structural else visit(part, pointer + "/" + str(key).replace("~", "~0").replace("/", "~1"))
                    for key, part in item.items()}
        if isinstance(item, list):
            return [visit(part, pointer + f"/{index}") for index, part in enumerate(item)]
        return item

    return visit(value, "")


def model_view(root: Path, value: dict) -> dict:
    """Project known machine bindings, then deduplicate the complete delivery."""
    def project(item):
        if isinstance(item, list):
            return [project(part) for part in item]
        if not isinstance(item, dict):
            return item
        if {"checked_sources", "blocked_ids", "files"} <= item.keys():
            return {**{key: project(part) for key, part in item.items() if key != "files"},
                    "validation_sources": [{"source_path": part["path"],
                                            **({"retrieval": retain_source(root, part["contents"])}
                                               if "contents" in part else
                                               {"sha256": part["sha256"], "size_bytes": part["size_bytes"]})}
                                           for part in item["files"]],
                    "coverage": "Internal validation bytes retained separately; this display is not a checker binding."}
        # Decoding an embedded JSON document preserves meaning but not its exact
        # whitespace. Keep the original version before changing presentation.
        contents = item.get("contents")
        if ("source" in item and "retrieval" not in item and isinstance(contents, str)
                and len(contents.encode("utf-8")) >= 256 and digest(contents) == item.get("sha256")):
            try:
                decoded = json.loads(contents)
            except ValueError:
                decoded = None
            if isinstance(decoded, (dict, list)):
                item = {**item, "retrieval": retain_source(root, contents)}
        return {key: project(part) for key, part in item.items()}
    result = delivery_view(project(value))
    if "delivery_identity" in result or isinstance(result.get("adoption_context"), dict):
        result["delivery_identity"] = digest(json.dumps({key: part for key, part in result.items()
                                                         if key != "delivery_identity"}, ensure_ascii=False, sort_keys=True))
    return result


def verify_prepared(root: Path, view: dict) -> None:
    """Verify the exact supplied view and scoped sources before a native send.

    Native callers still must send these checked bytes. This helper cannot
    intercept an opaque host invocation or establish semantic adoption.
    """
    from frontier_references import _working_text, read_reference
    expected = view.get("delivery_identity")
    body = {key: part for key, part in view.items() if key != "delivery_identity"}
    if expected != digest(json.dumps(body, ensure_ascii=False, sort_keys=True)):
        raise ValueError("prepared delivery was changed; prepare the affected use again")
    context = view if "sources" in view else view.get("adoption_context")
    if not isinstance(context, dict) or "sources" not in context:
        raise ValueError("this output has no prepared source context; coverage is unavailable")
    if context is not view and view.get("judgment_binding") is not None:
        if view["judgment_binding"] != context.get("judgment_binding"):
            raise ValueError("prepared decision lost its judgment correspondence")
    elif context is not view and "policy_coverage" in view:
        # This is a generated result with its binding removed, not an ordinary
        # unbound resolver input. Other preparation metadata remains supported.
        raise ValueError("prepared result needs its own judgment correspondence")
    for source in context.get("current_sources", []):
        if digest(_working_text(root, source["path"])) != source["sha256"]:
            raise ValueError(f"prepared current source changed: {source['path']}")
    if context.get("judgment_binding"):
        from frontier_references import (check_judgment_use, _JUDGMENT_DERIVED,
                                         _judgment_uses, _validate_objective_inputs, _source_metadata)
        from identity_bindings import canonical_json, sha256_bytes
        check_judgment_use(root, context["judgment_binding"])
        decisions = [view] if context is not view and view.get("judgment_binding") else []
        provided = (context.get("decision") or {}).get("provided_body")
        if isinstance(provided, dict) and provided.get("judgment_binding"):
            decisions.append(provided)
        decision_ref = (context.get("decision") or {}).get("source")
        if decision_ref:
            decisions.append(_source_metadata(read_reference(root, decision_ref).decode("utf-8")
                             if decision_ref.get("commit") else _working_text(root, decision_ref["path"])))
        if not decisions:
            raise ValueError("prepared judgment has no actual decision carrier")
        if {item["path"] for item in context["judgment_binding"]["uses"]} - set(context.get("actual_use", [])):
            raise ValueError("prepared judgment lost an actual task association")
        for decision in decisions:
            body = {key: part for key, part in decision.items() if key not in _JUDGMENT_DERIVED}
            if sha256_bytes(canonical_json(body)) != context["judgment_binding"]["decision_sha256"]:
                raise ValueError("prepared decision differs from its judged consequence")
            _validate_objective_inputs(root, decision)
            binding = context["judgment_binding"]
            actual = _judgment_uses(root, context["owner"]["source"]["path"], decision,
                                   binding["task_sources"], binding["assignment"])
            if actual != binding["uses"]:
                raise ValueError("prepared actual task differs from its judgment correspondence")
    for item in context["sources"]:
        ref = item["source"]
        current = (read_reference(root, ref).decode("utf-8") if ref.get("commit")
                   else _working_text(root, ref["path"]))
        if digest(current) != item["sha256"]:
            raise ValueError(f"prepared source changed: {ref['path']}")
        if item.get("retrieval"):
            read_retained(root, item["retrieval"])
    # Terminal adoption has no Worker task, but still consumes the owner's
    # known corrections. It must not escape through an empty task list.
    from current_use import check_current_use
    check_current_use(root, context["owner"]["source"]["path"], context.get("actual_use", []))
