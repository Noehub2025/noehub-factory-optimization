#!/usr/bin/env python3
"""Prepare current W and resolver references from saved Git bytes."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import yaml

from identity_bindings import canonical_json, normalize_repo_path, sha256_bytes


class ReferenceError(ValueError):
    """A required saved input cannot be interpreted unambiguously."""


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


def _git(root: Path, *args: str) -> bytes:
    try:
        return subprocess.run(
            ["git", "-C", str(root), *args], check=True, capture_output=True
        ).stdout
    except subprocess.CalledProcessError as exc:
        raise ReferenceError(exc.stderr.decode(errors="replace").strip()) from exc


def reference(root: Path, revision: str, path: str) -> dict[str, str]:
    """Resolve a revision once; consumers retain the returned full commit."""
    commit = _git(root, "rev-parse", "--verify", "--end-of-options", revision + "^{commit}").decode().strip()
    ref = {"commit": commit, "path": normalize_repo_path(path, "path")}
    read_reference(root, ref)
    return ref


def read_reference(root: Path, ref: dict[str, str]) -> bytes:
    commit = ref.get("commit", "")
    if not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", commit):
        raise ReferenceError("saved reference needs a full Git commit")
    path = normalize_repo_path(ref.get("path"), "path")
    # Trees and symlinks are not document inputs.
    row = _git(root, "ls-tree", commit, "--", path).decode().split("\t", 1)[0]
    if not row.startswith(("100644 blob ", "100755 blob ")):
        raise ReferenceError(f"required regular file is absent at saved version: {path}")
    return _git(root, "show", f"{commit}:{path}")


def _evidence(root: Path, ref: dict[str, str]) -> tuple[dict, str]:
    facts = json.loads(read_reference(root, ref), object_pairs_hook=_pairs)
    if not isinstance(facts, dict):
        raise ReferenceError("resolver evidence must be a JSON object")
    # Preserve all decision facts. Reject non-JSON numbers rather than invent a normalization.
    json.dumps(facts, allow_nan=False)
    return facts, "frontier-selection-evidence-state-sha256:" + sha256_bytes(canonical_json(facts))


def prepare_resolver(root: Path, revision: str, path: str, prior_paths=()) -> dict:
    """Return input binding or reuse an existing resolution; never choose a row."""
    ref = reference(root, revision, path)
    _, identity = _evidence(root, ref)
    prepared = {"evidence_source": ref, "evidence_state_identity": identity}
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
        if previous == identity:
            prepared["reuse_resolution"] = prior_ref
            break
    return prepared


def bind_resolution(root: Path, prepared: dict, result: dict) -> dict:
    """Bind an existing result body to saved input without transcribing a digest."""
    if prepared.get("reuse_resolution"):
        raise ReferenceError("reuse the referenced resolution instead of publishing another")
    ref = prepared["evidence_source"]
    _, identity = _evidence(root, ref)
    if result.get("evidence_source"):
        _, previous = _evidence(root, result["evidence_source"])
        if previous != identity:
            raise ReferenceError("result belongs to different decision facts")
    # Derived fields are owned here. Professional result fields are preserved.
    return {**result, "evidence_source": ref, "evidence_state_identity": identity}


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
        path = normalize_repo_path(path, "design pointer")
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
        for key in ("evidence_source", "evidence_state_identity", "reuse_resolution", "subject", "work_plan", "delivery_scope"):
            if key in value or key == "reuse_resolution":
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=("design", "resolver", "bind-resolution"))
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--revision", default="HEAD")
    parser.add_argument("--path", required=True, help="W, evidence, or existing prepared assignment path")
    parser.add_argument("--scope", action="append", default=[])
    parser.add_argument("--prior", action="append", default=[], help="known resolution path at revision; repeat as needed")
    parser.add_argument("--result", type=Path, help="existing result draft for binding")
    parser.add_argument("--output", type=Path, help="write into the existing assignment or result location")
    args = parser.parse_args()
    try:
        if args.kind == "design":
            value = prepare_design(args.repo, args.revision, args.path, args.scope)
        elif args.kind == "resolver":
            value = prepare_resolver(args.repo, args.revision, args.path, args.prior)
        else:
            if args.result is None:
                raise ReferenceError("bind-resolution requires --result")
            prepared = _document((args.repo / args.path).read_bytes())
            value = bind_resolution(args.repo, prepared, _document(args.result.read_bytes()))
        if args.output:
            _write(args.output, value, merge=args.kind != "bind-resolution")
        else:
            print(json.dumps(value, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, KeyError, TypeError, OSError, yaml.YAMLError) as exc:
        print(json.dumps({"status": "NOT_READY", "error": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
