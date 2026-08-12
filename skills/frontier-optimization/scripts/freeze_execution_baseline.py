#!/usr/bin/env python3
"""Freeze and verify a recoverable Frontier execution-start baseline."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import posixpath
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required to freeze Frontier execution baselines") from exc


MANIFEST_KIND = "frontier-execution-baseline/1"


class BaselineError(ValueError):
    """Raised when an execution baseline cannot be frozen or verified."""


def canonical_yaml(document: dict[str, Any], omitted_field: str) -> bytes:
    payload = dict(document)
    payload.pop(omitted_field, None)
    return yaml.safe_dump(payload, sort_keys=False, allow_unicode=True).encode()


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def normalize_repo_path(raw: Any, field: str) -> str:
    if not isinstance(raw, str) or not raw.strip() or raw.startswith("/"):
        raise BaselineError(f"{field} must be a nonempty repository-relative path")
    normalized = posixpath.normpath(raw.strip().rstrip("/"))
    if normalized in {".", ".."} or normalized.startswith("../"):
        raise BaselineError(f"{field} escapes the repository: {raw!r}")
    return normalized


def resolve_inside(repo_root: Path, raw: Any, field: str) -> tuple[str, Path]:
    relative = normalize_repo_path(raw, field)
    resolved = (repo_root / relative).resolve()
    try:
        resolved.relative_to(repo_root)
    except ValueError as exc:
        raise BaselineError(f"{field} resolves outside the repository: {raw!r}") from exc
    return relative, resolved


def declared_identity(entry: dict[str, Any], index: int) -> str:
    identity = entry.get("identity")
    if not isinstance(identity, str) or not identity.startswith("sha256:"):
        raise BaselineError(
            f"post_transition_baseline[{index}].identity must use sha256:<digest>"
        )
    digest = identity.removeprefix("sha256:")
    if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
        raise BaselineError(
            f"post_transition_baseline[{index}].identity is not a lowercase SHA-256"
        )
    return identity


def subtree_inventory(source: Path) -> tuple[list[dict[str, str]], str]:
    if not source.is_dir():
        raise BaselineError(f"subtree source is not a directory: {source}")
    members: list[dict[str, str]] = []
    for member in sorted(source.rglob("*")):
        if member.is_symlink():
            raise BaselineError(f"baseline subtree contains a symbolic link: {member}")
        if member.is_dir():
            continue
        if not member.is_file():
            raise BaselineError(f"baseline subtree contains a non-regular file: {member}")
        relative = member.relative_to(source).as_posix()
        members.append({"path": relative, "sha256": sha256_bytes(member.read_bytes())})
    payload = json.dumps(
        members, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()
    return members, f"sha256:{sha256_bytes(payload)}"


def materialize_input(
    entry: dict[str, Any], index: int, repo_root: Path, staging_root: Path
) -> dict[str, Any]:
    source_path, source = resolve_inside(
        repo_root, entry.get("path"), f"post_transition_baseline[{index}].path"
    )
    scope = entry.get("scope")
    if scope not in {"file", "subtree"}:
        raise BaselineError(
            f"post_transition_baseline[{index}].scope must be file or subtree"
        )
    expected = declared_identity(entry, index)
    snapshot_path = Path("inputs") / Path(source_path)
    destination = staging_root / snapshot_path

    if source.is_symlink():
        raise BaselineError(f"baseline source is a symbolic link: {source_path}")
    if scope == "file":
        if not source.is_file():
            raise BaselineError(f"baseline file is missing or not regular: {source_path}")
        content = source.read_bytes()
        computed = f"sha256:{sha256_bytes(content)}"
        if computed != expected:
            raise BaselineError(
                f"baseline identity mismatch for {source_path}: declared {expected}, computed {computed}"
            )
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
        return {
            "source_path": source_path,
            "scope": scope,
            "declared_identity": expected,
            "computed_identity": computed,
            "snapshot_path": snapshot_path.as_posix(),
        }

    members, computed = subtree_inventory(source)
    if computed != expected:
        raise BaselineError(
            f"baseline identity mismatch for {source_path}/: declared {expected}, computed {computed}"
        )
    for member in members:
        source_member = source / member["path"]
        destination_member = destination / member["path"]
        destination_member.parent.mkdir(parents=True, exist_ok=True)
        destination_member.write_bytes(source_member.read_bytes())
    return {
        "source_path": source_path,
        "scope": scope,
        "declared_identity": expected,
        "computed_identity": computed,
        "snapshot_path": snapshot_path.as_posix(),
        "members": members,
    }


def compute_manifest_id(manifest: dict[str, Any]) -> str:
    digest = sha256_bytes(canonical_yaml(manifest, "snapshot_id"))
    return f"{manifest.get('batch_id', 'UNKNOWN')}-execution-baseline-sha256:{digest}"


def compute_execution_start_id(document: dict[str, Any]) -> str:
    digest = sha256_bytes(canonical_yaml(document, "execution_start_id"))
    return f"{document.get('batch_id', 'UNKNOWN')}-execution-start-sha256:{digest}"


def read_yaml(path: Path, label: str) -> dict[str, Any]:
    try:
        document = yaml.safe_load(path.read_text())
    except (OSError, yaml.YAMLError) as exc:
        raise BaselineError(f"cannot read {label}: {exc}") from exc
    if not isinstance(document, dict):
        raise BaselineError(f"{label} must contain a YAML mapping")
    return document


def freeze(
    draft_path: Path, snapshot_base_value: str, output_path: Path, repo_root: Path
) -> dict[str, Any]:
    document = read_yaml(draft_path, "execution-start draft")
    if document.get("execution_start_id") is not None:
        raise BaselineError("execution-start draft must not contain execution_start_id")
    if document.get("baseline_snapshot") is not None:
        raise BaselineError("execution-start draft must not contain baseline_snapshot")
    baseline = document.get("post_transition_baseline")
    if not isinstance(baseline, list) or not baseline:
        raise BaselineError("post_transition_baseline must be a nonempty list")

    output_relative, expected_output = resolve_inside(
        repo_root, document.get("execution_start_path"), "execution_start_path"
    )
    if expected_output != output_path.resolve():
        raise BaselineError(
            f"execution_start_path {output_relative} does not match --output"
        )
    if output_path.exists():
        raise BaselineError(f"refusing to overwrite execution-start path: {output_relative}")

    snapshot_base_relative, snapshot_base = resolve_inside(
        repo_root, snapshot_base_value, "execution_baseline_root"
    )
    if snapshot_base.exists():
        raise BaselineError(
            f"refusing to reuse execution-baseline root: {snapshot_base_relative}"
        )
    if expected_output == snapshot_base or snapshot_base in expected_output.parents:
        raise BaselineError("execution-start path must be outside execution_baseline_root")
    for index, entry in enumerate(baseline):
        if not isinstance(entry, dict):
            raise BaselineError(f"post_transition_baseline[{index}] must be a mapping")
        _, source = resolve_inside(
            repo_root,
            entry.get("path"),
            f"post_transition_baseline[{index}].path",
        )
        scope = entry.get("scope")
        if source == expected_output or source == snapshot_base:
            raise BaselineError(
                f"post_transition_baseline[{index}] overlaps a Coordinator execution output"
            )
        if scope == "subtree" and (
            source in expected_output.parents or source in snapshot_base.parents
        ):
            raise BaselineError(
                f"post_transition_baseline[{index}] subtree contains a Coordinator execution output"
            )

    staging_parent = snapshot_base.parent
    staging_parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".execution-baseline-", dir=staging_parent))
    try:
        inputs = [
            materialize_input(entry, index, repo_root, staging)
            for index, entry in enumerate(baseline)
        ]
        sources = [entry["source_path"] for entry in inputs]
        if len(sources) != len(set(sources)):
            raise BaselineError("post_transition_baseline source paths must be unique")

        manifest: dict[str, Any] = {
            "manifest_kind": MANIFEST_KIND,
            "batch_id": document.get("batch_id"),
            "campaign_generation": document.get("campaign_generation"),
            "created_at": document.get("recorded_at"),
            "created_by": "frontier-optimization/1",
            "inputs": inputs,
        }
        snapshot_id = compute_manifest_id(manifest)
        manifest = {"snapshot_id": snapshot_id, **manifest}
        digest = snapshot_id.rsplit(":", 1)[-1]
        final_root = snapshot_base / digest
        manifest_path = final_root / "manifest.yaml"
        (staging / "manifest.yaml").write_bytes(
            yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True).encode()
        )

        snapshot_base.mkdir()
        os.replace(staging, final_root)
        document["baseline_snapshot"] = {
            "root": final_root.relative_to(repo_root).as_posix(),
            "manifest": manifest_path.relative_to(repo_root).as_posix(),
            "snapshot_id": snapshot_id,
            "input_count": len(inputs),
        }
        document["execution_start_id"] = compute_execution_start_id(document)
        rendered = yaml.safe_dump(document, sort_keys=False, allow_unicode=True).encode()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_output = output_path.with_name(f".{output_path.name}.tmp")
        if temporary_output.exists():
            raise BaselineError(f"temporary output already exists: {temporary_output}")
        temporary_output.write_bytes(rendered)
        os.replace(temporary_output, output_path)
        return document
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        raise


def verify_manifest_input(
    item: dict[str, Any], snapshot_root: Path, repo_root: Path, require_live: bool
) -> None:
    source_path, live_source = resolve_inside(repo_root, item.get("source_path"), "source_path")
    scope = item.get("scope")
    expected = item.get("computed_identity")
    if item.get("declared_identity") != expected:
        raise BaselineError(f"declared and computed identities differ for {source_path}")
    snapshot_relative = normalize_repo_path(item.get("snapshot_path"), "snapshot_path")
    snapshot_source = (snapshot_root / snapshot_relative).resolve()
    try:
        snapshot_source.relative_to(snapshot_root)
    except ValueError as exc:
        raise BaselineError(f"snapshot_path escapes snapshot root: {snapshot_relative}") from exc

    if scope == "file":
        if not snapshot_source.is_file() or snapshot_source.is_symlink():
            raise BaselineError(f"snapshot file is missing or unsafe: {snapshot_relative}")
        observed = f"sha256:{sha256_bytes(snapshot_source.read_bytes())}"
        if observed != expected:
            raise BaselineError(f"snapshot identity mismatch for {source_path}")
        if require_live:
            if not live_source.is_file() or live_source.is_symlink():
                raise BaselineError(f"live baseline file is missing or unsafe: {source_path}")
            live_identity = f"sha256:{sha256_bytes(live_source.read_bytes())}"
            if live_identity != expected:
                raise BaselineError(f"live baseline drift for {source_path}")
        return

    if scope != "subtree" or not isinstance(item.get("members"), list):
        raise BaselineError(f"invalid snapshot scope for {source_path}")
    snapshot_members, observed = subtree_inventory(snapshot_source)
    if snapshot_members != item["members"] or observed != expected:
        raise BaselineError(f"snapshot subtree identity mismatch for {source_path}")
    if require_live:
        live_members, live_identity = subtree_inventory(live_source)
        if live_members != item["members"] or live_identity != expected:
            raise BaselineError(f"live baseline drift for {source_path}/")


def verify(execution_start_path: Path, repo_root: Path, require_live: bool) -> dict[str, Any]:
    document = read_yaml(execution_start_path, "execution-start record")
    declared_start_id = document.get("execution_start_id")
    computed_start_id = compute_execution_start_id(document)
    if declared_start_id != computed_start_id:
        raise BaselineError(
            f"execution_start_id mismatch: declared {declared_start_id}, computed {computed_start_id}"
        )
    snapshot = document.get("baseline_snapshot")
    if not isinstance(snapshot, dict):
        raise BaselineError("baseline_snapshot must be a mapping")
    _, snapshot_root = resolve_inside(repo_root, snapshot.get("root"), "baseline_snapshot.root")
    _, manifest_path = resolve_inside(
        repo_root, snapshot.get("manifest"), "baseline_snapshot.manifest"
    )
    if manifest_path.parent != snapshot_root:
        raise BaselineError("baseline manifest must be inside the declared snapshot root")
    manifest = read_yaml(manifest_path, "execution-baseline manifest")
    if manifest.get("manifest_kind") != MANIFEST_KIND:
        raise BaselineError("execution-baseline manifest kind is invalid")
    computed_snapshot_id = compute_manifest_id(manifest)
    if manifest.get("snapshot_id") != computed_snapshot_id:
        raise BaselineError("execution-baseline manifest identity mismatch")
    if snapshot.get("snapshot_id") != computed_snapshot_id:
        raise BaselineError("execution-start and manifest bind different snapshot identities")
    if snapshot_root.name != computed_snapshot_id.rsplit(":", 1)[-1]:
        raise BaselineError("snapshot root does not use the content-addressed digest")
    inputs = manifest.get("inputs")
    baseline = document.get("post_transition_baseline")
    if not isinstance(inputs, list) or not isinstance(baseline, list):
        raise BaselineError("baseline inputs must be lists")
    if snapshot.get("input_count") != len(inputs) or len(inputs) != len(baseline):
        raise BaselineError("baseline input count mismatch")
    expected_snapshot_files: set[str] = set()
    for index, (baseline_entry, manifest_entry) in enumerate(zip(baseline, inputs, strict=True)):
        if not isinstance(baseline_entry, dict) or not isinstance(manifest_entry, dict):
            raise BaselineError(f"baseline entry {index} must be a mapping")
        expected_binding = {
            "path": manifest_entry.get("source_path"),
            "scope": manifest_entry.get("scope"),
            "identity": manifest_entry.get("declared_identity"),
        }
        if {key: baseline_entry.get(key) for key in expected_binding} != expected_binding:
            raise BaselineError(f"baseline entry {index} does not match snapshot manifest")
        verify_manifest_input(manifest_entry, snapshot_root, repo_root, require_live)
        snapshot_path = normalize_repo_path(
            manifest_entry.get("snapshot_path"), "snapshot_path"
        )
        if manifest_entry.get("scope") == "file":
            expected_snapshot_files.add(snapshot_path)
        else:
            for member in manifest_entry.get("members", []):
                expected_snapshot_files.add(
                    (Path(snapshot_path) / member["path"]).as_posix()
                )
    actual_snapshot_files: set[str] = set()
    for member in snapshot_root.rglob("*"):
        if member.is_symlink():
            raise BaselineError(f"snapshot contains a symbolic link: {member}")
        if member.is_file() and member != manifest_path:
            actual_snapshot_files.add(member.relative_to(snapshot_root).as_posix())
    if actual_snapshot_files != expected_snapshot_files:
        raise BaselineError("snapshot contains missing or undeclared input files")
    return {
        "execution_start_id": computed_start_id,
        "baseline_snapshot_id": computed_snapshot_id,
        "input_count": len(inputs),
        "snapshot_verified": True,
        "live_baseline_matched": require_live,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    freeze_parser = subparsers.add_parser("freeze")
    freeze_parser.add_argument("draft", type=Path)
    freeze_parser.add_argument("--snapshot-root", required=True)
    freeze_parser.add_argument("--output", required=True, type=Path)
    freeze_parser.add_argument("--repo-root", type=Path, default=Path.cwd())

    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("execution_start", type=Path)
    verify_parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    verify_parser.add_argument("--live", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    try:
        if args.command == "freeze":
            result = freeze(
                args.draft,
                args.snapshot_root,
                args.output.resolve(),
                repo_root,
            )
            output = {
                "execution_start_id": result["execution_start_id"],
                "baseline_snapshot": result["baseline_snapshot"],
                "frozen": True,
            }
        else:
            output = verify(args.execution_start, repo_root, args.live)
    except (BaselineError, OSError, yaml.YAMLError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    sys.stdout.write(json.dumps(output, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
