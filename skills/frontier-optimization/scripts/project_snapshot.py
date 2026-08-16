#!/usr/bin/env python3
"""Capture and verify filtered project snapshots without copying source trees."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required to manage Frontier project snapshots") from exc


SCHEMA = "frontier-project-snapshot/1"
SNAPSHOT_ID_PREFIX = "project-snapshot-sha256:"
DEFAULT_REF = "refs/frontier/project-snapshots/current"
FORBIDDEN_TOP_LEVEL = {".agents", ".codex", ".git"}
FORBIDDEN_RUNTIME_PARTS = {"__pycache__"}
FORBIDDEN_RUNTIME_SUFFIXES = {".pyc", ".pyo"}


class ProjectSnapshotError(ValueError):
    """Raised when project bytes cannot form or reproduce a safe snapshot."""


def _canonical_bytes(document: dict[str, Any]) -> bytes:
    payload = dict(document)
    payload.pop("snapshot_id", None)
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode()


def compute_snapshot_id(document: dict[str, Any]) -> str:
    return SNAPSHOT_ID_PREFIX + hashlib.sha256(_canonical_bytes(document)).hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_project_path(value: Any, role: str = "path") -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise ProjectSnapshotError(f"{role} must be a nonempty POSIX project path")
    path = PurePosixPath(value)
    normalized = path.as_posix()
    if path.is_absolute() or normalized != value or any(part in {"", ".", ".."} for part in path.parts):
        raise ProjectSnapshotError(f"{role} is not canonical: {value}")
    if path.parts[0] in FORBIDDEN_TOP_LEVEL:
        raise ProjectSnapshotError(f"{role} is outside project evidence: {value}")
    for index, part in enumerate(path.parts[:-1]):
        if part.endswith("-snapshot") and path.parts[index + 1] == "inputs":
            raise ProjectSnapshotError(f"{role} uses a retired copied snapshot path: {value}")
    return normalized


def _reject_symlink_components(repo_root: Path, relative: str, *, allow_missing_leaf: bool = False) -> Path:
    current = repo_root
    parts = PurePosixPath(relative).parts
    for index, part in enumerate(parts):
        current = current / part
        if allow_missing_leaf and not current.exists():
            break
        try:
            mode = current.lstat().st_mode
        except OSError as exc:
            raise ProjectSnapshotError(f"project path is unreadable: {relative}: {exc}") from exc
        if stat.S_ISLNK(mode):
            raise ProjectSnapshotError(f"project path contains a symbolic link: {relative}")
    return repo_root / relative


def _run_git(
    repo_root: Path,
    args: list[str],
    *,
    index_path: Path | None = None,
    input_bytes: bytes | None = None,
    check: bool = True,
    extra_env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[bytes]:
    env = os.environ.copy()
    if index_path is not None:
        env["GIT_INDEX_FILE"] = str(index_path)
    if extra_env:
        env.update(extra_env)
    result = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        check=False,
    )
    if check and result.returncode != 0:
        detail = result.stderr.decode(errors="replace").strip()
        raise ProjectSnapshotError(f"git {' '.join(args)} failed: {detail}")
    return result


def _ensure_git_repository(repo_root: Path) -> None:
    result = _run_git(repo_root, ["rev-parse", "--is-inside-work-tree"], check=False)
    if result.returncode != 0 or result.stdout.strip() != b"true":
        raise ProjectSnapshotError(f"not a Git worktree: {repo_root}")


def _runtime_artifact_forbidden(relative: str) -> bool:
    path = PurePosixPath(relative)
    return any(part in FORBIDDEN_RUNTIME_PARTS for part in path.parts) or path.suffix in FORBIDDEN_RUNTIME_SUFFIXES


def _git_mode(path: Path) -> str:
    return "100755" if path.stat().st_mode & 0o111 else "100644"


def _inventory_closed_root(repo_root: Path, root_value: Any, expected_value: Any) -> tuple[str, list[str]]:
    root = normalize_project_path(root_value, "closed_roots.path").rstrip("/")
    root_path = _reject_symlink_components(repo_root, root)
    if not root_path.is_dir():
        raise ProjectSnapshotError(f"closed project root is not a directory: {root}")
    if not isinstance(expected_value, list) or not all(isinstance(item, str) for item in expected_value):
        raise ProjectSnapshotError(f"closed project root requires expected_members: {root}")
    expected = sorted({normalize_project_path(f"{root}/{item}", "closed root member")[len(root) + 1 :] for item in expected_value})
    if len(expected) != len(expected_value):
        raise ProjectSnapshotError(f"closed project root has duplicate expected members: {root}")
    actual: list[str] = []
    for member in sorted(root_path.rglob("*")):
        relative = member.relative_to(root_path).as_posix()
        if member.is_symlink():
            raise ProjectSnapshotError(f"closed project root contains a symbolic link: {root}/{relative}")
        if member.is_file():
            if _runtime_artifact_forbidden(relative):
                raise ProjectSnapshotError(f"closed project root contains a runtime artifact: {root}/{relative}")
            actual.append(relative)
        elif not member.is_dir():
            raise ProjectSnapshotError(f"closed project root contains an unsupported member: {root}/{relative}")
    if actual != expected:
        missing = sorted(set(expected) - set(actual))
        extra = sorted(set(actual) - set(expected))
        raise ProjectSnapshotError(
            f"closed project root inventory mismatch for {root}: missing={missing}, extra={extra}"
        )
    return root, actual


def _validate_external_artifacts(repo_root: Path, values: Any) -> list[dict[str, Any]]:
    if values is None:
        return []
    if not isinstance(values, list):
        raise ProjectSnapshotError("external_artifacts must be a list")
    artifacts: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, value in enumerate(values):
        if not isinstance(value, dict) or set(value) != {"locator", "size", "file_sha256"}:
            raise ProjectSnapshotError(f"external_artifacts[{index}] has an invalid shape")
        locator = normalize_project_path(value.get("locator"), f"external_artifacts[{index}].locator")
        if locator in seen:
            raise ProjectSnapshotError(f"duplicate external artifact locator: {locator}")
        seen.add(locator)
        digest = value.get("file_sha256")
        size = value.get("size")
        if not isinstance(digest, str) or len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
            raise ProjectSnapshotError(f"external_artifacts[{index}].file_sha256 is invalid")
        if not isinstance(size, int) or isinstance(size, bool) or size < 0:
            raise ProjectSnapshotError(f"external_artifacts[{index}].size is invalid")
        locator_parts = PurePosixPath(locator).parts
        if len(locator_parts) < 3 or locator_parts[-1] != digest or locator_parts[-2] != digest[:2]:
            raise ProjectSnapshotError(
                f"external_artifacts[{index}].locator is not derived from its SHA-256"
            )
        path = _reject_symlink_components(repo_root, locator)
        if not path.is_file():
            raise ProjectSnapshotError(f"external artifact is missing: {locator}")
        observed_size = path.stat().st_size
        observed_digest = sha256_file(path)
        if observed_size != size or observed_digest != digest:
            raise ProjectSnapshotError(f"external artifact identity mismatch: {locator}")
        artifacts.append({"locator": locator, "size": size, "file_sha256": digest})
    return sorted(artifacts, key=lambda item: item["locator"])


def _tree_members(repo_root: Path, treeish: str) -> list[dict[str, Any]]:
    output = _run_git(repo_root, ["ls-tree", "-r", "-z", treeish]).stdout
    members: list[dict[str, Any]] = []
    for record in output.split(b"\0"):
        if not record:
            continue
        metadata, raw_path = record.split(b"\t", 1)
        mode, kind, object_id = metadata.decode().split(" ", 2)
        path = raw_path.decode()
        if kind != "blob" or mode not in {"100644", "100755"}:
            raise ProjectSnapshotError(f"snapshot tree contains an unsupported member: {path}")
        raw = _run_git(repo_root, ["cat-file", "blob", object_id]).stdout
        members.append(
            {
                "path": path,
                "mode": mode,
                "size": len(raw),
                "file_sha256": sha256_bytes(raw),
            }
        )
    return sorted(members, key=lambda item: item["path"])


def _current_ref(repo_root: Path, reference: str) -> str | None:
    result = _run_git(repo_root, ["rev-parse", "--verify", "--quiet", reference], check=False)
    return result.stdout.decode().strip() if result.returncode == 0 else None


def capture(
    repo_root: Path,
    *,
    manifest_path: Path,
    paths: Iterable[str],
    closed_roots: list[dict[str, Any]] | None = None,
    external_artifacts: list[dict[str, Any]] | None = None,
    reference: str = DEFAULT_REF,
    created_at: str | None = None,
) -> dict[str, Any]:
    """Capture selected live project bytes in one filtered Git tree and ref chain."""
    repo_root = repo_root.resolve()
    _ensure_git_repository(repo_root)
    if reference != DEFAULT_REF:
        raise ProjectSnapshotError(f"snapshot ref must be exactly {DEFAULT_REF}")
    try:
        manifest_relative = manifest_path.resolve().relative_to(repo_root).as_posix()
    except ValueError as exc:
        raise ProjectSnapshotError("manifest path must stay inside the project") from exc
    normalize_project_path(manifest_relative, "manifest_path")
    if manifest_path.exists():
        raise ProjectSnapshotError(f"refusing to overwrite snapshot manifest: {manifest_relative}")

    selected: set[str] = set()
    for index, value in enumerate(paths):
        relative = normalize_project_path(value, f"paths[{index}]")
        if relative == manifest_relative:
            raise ProjectSnapshotError("a snapshot cannot contain its own manifest")
        path = _reject_symlink_components(repo_root, relative)
        if not path.is_file():
            raise ProjectSnapshotError(f"selected project member is not a regular file: {relative}")
        if _runtime_artifact_forbidden(relative):
            raise ProjectSnapshotError(f"selected project member is a runtime artifact: {relative}")
        selected.add(relative)

    closed: list[dict[str, Any]] = []
    for value in closed_roots or []:
        if not isinstance(value, dict) or set(value) != {"path", "expected_members"}:
            raise ProjectSnapshotError("closed_roots entries require path and expected_members")
        root, members = _inventory_closed_root(repo_root, value["path"], value["expected_members"])
        closed.append({"path": root, "members": members})
        selected.update(f"{root}/{member}" for member in members)
    if not selected:
        raise ProjectSnapshotError("a project snapshot requires at least one project member")
    artifacts = _validate_external_artifacts(repo_root, external_artifacts)

    created_at = created_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    previous = _current_ref(repo_root, reference)
    object_format = _run_git(repo_root, ["rev-parse", "--show-object-format"]).stdout.decode().strip()
    zero_object = "0" * (64 if object_format == "sha256" else 40)

    with tempfile.TemporaryDirectory(prefix="frontier-project-snapshot-") as directory:
        index_path = Path(directory) / "index"
        _run_git(repo_root, ["read-tree", "--empty"], index_path=index_path)
        for relative in sorted(selected):
            _run_git(repo_root, ["add", "--force", "--", relative], index_path=index_path)
        tree = _run_git(repo_root, ["write-tree"], index_path=index_path).stdout.decode().strip()
        members = _tree_members(repo_root, tree)
        if [item["path"] for item in members] != sorted(selected):
            raise ProjectSnapshotError("filtered Git tree does not equal the selected project member set")
        for item in members:
            live = _reject_symlink_components(repo_root, item["path"])
            if (
                not live.is_file()
                or _git_mode(live) != item["mode"]
                or live.stat().st_size != item["size"]
                or sha256_file(live) != item["file_sha256"]
            ):
                raise ProjectSnapshotError(
                    f"project member changed during snapshot capture: {item['path']}"
                )
        for item in closed:
            _inventory_closed_root(repo_root, item["path"], item["members"])
        commit_args = ["commit-tree", tree]
        if previous is not None:
            commit_args.extend(["-p", previous])
        identity_env = {
            "GIT_AUTHOR_NAME": "Frontier Project Snapshot",
            "GIT_AUTHOR_EMAIL": "frontier-snapshot@local.invalid",
            "GIT_COMMITTER_NAME": "Frontier Project Snapshot",
            "GIT_COMMITTER_EMAIL": "frontier-snapshot@local.invalid",
            "GIT_AUTHOR_DATE": created_at,
            "GIT_COMMITTER_DATE": created_at,
        }
        commit = _run_git(
            repo_root,
            commit_args,
            input_bytes=f"Frontier project snapshot at {created_at}\n".encode(),
            extra_env=identity_env,
        ).stdout.decode().strip()

    manifest: dict[str, Any] = {
        "schema": SCHEMA,
        "storage": {
            "commit": commit,
            "ref": reference,
            "parent_commit": previous,
        },
        "members": members,
        "closed_roots": sorted(closed, key=lambda item: item["path"]),
        "external_artifacts": artifacts,
    }
    manifest = {"snapshot_id": compute_snapshot_id(manifest), **manifest}
    rendered = yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True).encode()
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = manifest_path.with_name(f".{manifest_path.name}.tmp")
    if temporary.exists():
        raise ProjectSnapshotError(f"temporary manifest already exists: {temporary}")
    temporary.write_bytes(rendered)
    try:
        os.replace(temporary, manifest_path)
        _run_git(repo_root, ["update-ref", reference, commit, previous or zero_object])
    except Exception:
        temporary.unlink(missing_ok=True)
        manifest_path.unlink(missing_ok=True)
        raise
    return manifest


def read_manifest(path: Path) -> tuple[dict[str, Any], bytes]:
    try:
        raw = path.read_bytes()
        document = yaml.safe_load(raw)
    except (OSError, yaml.YAMLError) as exc:
        raise ProjectSnapshotError(f"snapshot manifest is unreadable: {path}: {exc}") from exc
    if not isinstance(document, dict):
        raise ProjectSnapshotError("snapshot manifest must contain a mapping")
    return document, raw


def verify(
    repo_root: Path,
    manifest: dict[str, Any] | Path,
    *,
    require_live: bool = False,
) -> dict[str, Any]:
    """Verify one project snapshot, its Git reachability, and external artifacts."""
    repo_root = repo_root.resolve()
    _ensure_git_repository(repo_root)
    document = read_manifest(manifest)[0] if isinstance(manifest, Path) else manifest
    if document.get("schema") != SCHEMA:
        raise ProjectSnapshotError(f"snapshot schema must be {SCHEMA}")
    if document.get("snapshot_id") != compute_snapshot_id(document):
        raise ProjectSnapshotError("project snapshot identity is not derived from canonical manifest bytes")
    if set(document) != {"snapshot_id", "schema", "storage", "members", "closed_roots", "external_artifacts"}:
        raise ProjectSnapshotError("project snapshot manifest has unknown or missing fields")
    storage = document.get("storage")
    if not isinstance(storage, dict) or set(storage) != {"commit", "ref", "parent_commit"}:
        raise ProjectSnapshotError("project snapshot storage binding is invalid")
    commit = storage.get("commit")
    reference = storage.get("ref")
    if not isinstance(commit, str) or not isinstance(reference, str):
        raise ProjectSnapshotError("project snapshot commit and ref are required")
    if reference != DEFAULT_REF:
        raise ProjectSnapshotError(f"project snapshot ref must be exactly {DEFAULT_REF}")
    current = _current_ref(repo_root, reference)
    if current is None:
        raise ProjectSnapshotError(f"project snapshot ref is missing: {reference}")
    reachable = _run_git(repo_root, ["merge-base", "--is-ancestor", commit, current], check=False)
    if reachable.returncode != 0:
        raise ProjectSnapshotError("project snapshot commit is not reachable from its dedicated ref")
    ancestry = _run_git(repo_root, ["rev-list", "--parents", "-n", "1", commit]).stdout.decode().split()
    if not ancestry or ancestry[0] != commit or len(ancestry) > 2:
        raise ProjectSnapshotError("project snapshot commit ancestry is invalid")
    observed_parent = ancestry[1] if len(ancestry) == 2 else None
    if storage.get("parent_commit") != observed_parent:
        raise ProjectSnapshotError("project snapshot parent binding does not match the Git commit")
    observed_members = _tree_members(repo_root, f"{commit}^{{tree}}")
    if document.get("members") != observed_members:
        raise ProjectSnapshotError("project snapshot member identities do not match the Git tree")
    paths = [item["path"] for item in observed_members]
    for path in paths:
        normalize_project_path(path, "snapshot member")
        if _runtime_artifact_forbidden(path):
            raise ProjectSnapshotError(f"project snapshot contains a runtime artifact: {path}")
    for closed in document.get("closed_roots", []):
        if not isinstance(closed, dict) or set(closed) != {"path", "members"}:
            raise ProjectSnapshotError("project snapshot closed root is invalid")
        root = normalize_project_path(closed.get("path"), "closed root")
        expected = sorted(
            path[len(root) + 1 :]
            for path in paths
            if path.startswith(f"{root}/")
        )
        if closed.get("members") != expected:
            raise ProjectSnapshotError(f"project snapshot closed root does not match its tree: {root}")
    artifacts = _validate_external_artifacts(repo_root, document.get("external_artifacts"))
    if artifacts != document.get("external_artifacts"):
        raise ProjectSnapshotError("external artifact ordering is not canonical")
    if require_live:
        member_by_path = {item["path"]: item for item in observed_members}
        for relative, item in member_by_path.items():
            path = _reject_symlink_components(repo_root, relative)
            if (
                not path.is_file()
                or _git_mode(path) != item["mode"]
                or path.stat().st_size != item["size"]
                or sha256_file(path) != item["file_sha256"]
            ):
                raise ProjectSnapshotError(f"live project member drift: {relative}")
        for closed in document.get("closed_roots", []):
            _inventory_closed_root(repo_root, closed["path"], closed["members"])
    return {
        "snapshot_id": document["snapshot_id"],
        "commit": commit,
        "member_count": len(observed_members),
        "external_artifact_count": len(artifacts),
        "snapshot_verified": True,
        "live_project_matched": require_live,
    }


def member_bytes(repo_root: Path, manifest: dict[str, Any], relative: str) -> bytes:
    """Read one verified project member directly from its immutable Git commit."""
    relative = normalize_project_path(relative, "project member")
    members = {item.get("path"): item for item in manifest.get("members", []) if isinstance(item, dict)}
    if relative not in members:
        raise ProjectSnapshotError(f"project member is absent from the snapshot: {relative}")
    storage = manifest.get("storage")
    if not isinstance(storage, dict) or not isinstance(storage.get("commit"), str):
        raise ProjectSnapshotError("project snapshot storage binding is invalid")
    raw = _run_git(repo_root.resolve(), ["show", f"{storage['commit']}:{relative}"]).stdout
    item = members[relative]
    if len(raw) != item.get("size") or sha256_bytes(raw) != item.get("file_sha256"):
        raise ProjectSnapshotError(f"project member identity mismatch: {relative}")
    return raw


def materialize(repo_root: Path, manifest: dict[str, Any] | Path, destination: Path) -> dict[str, Any]:
    """Materialize one verified project snapshot for review or export."""
    document = read_manifest(manifest)[0] if isinstance(manifest, Path) else manifest
    verify(repo_root, document)
    if destination.exists() and any(destination.iterdir()):
        raise ProjectSnapshotError(f"materialization destination is not empty: {destination}")
    destination.mkdir(parents=True, exist_ok=True)
    for item in document["members"]:
        output = destination / item["path"]
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(member_bytes(repo_root, document, item["path"]))
        output.chmod(0o755 if item["mode"] == "100755" else 0o644)
    return {"snapshot_id": document["snapshot_id"], "member_count": len(document["members"]), "materialized": True}


def publish_artifact(source: Path, repo_root: Path, store_root: str = "artifacts/sha256") -> dict[str, Any]:
    """Publish one immutable large project artifact under its SHA-256 locator."""
    if not source.is_file() or source.is_symlink():
        raise ProjectSnapshotError(f"artifact source is not a safe regular file: {source}")
    digest = sha256_file(source)
    size = source.stat().st_size
    store = normalize_project_path(store_root, "artifact store root").rstrip("/")
    locator = f"{store}/{digest[:2]}/{digest}"
    destination = _reject_symlink_components(repo_root.resolve(), locator, allow_missing_leaf=True)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if not destination.is_file() or destination.is_symlink() or destination.stat().st_size != size or sha256_file(destination) != digest:
            raise ProjectSnapshotError(f"content-addressed artifact destination conflicts: {locator}")
    else:
        handle, temporary_name = tempfile.mkstemp(prefix=".artifact-", dir=destination.parent)
        os.close(handle)
        temporary = Path(temporary_name)
        try:
            shutil.copyfile(source, temporary)
            if temporary.stat().st_size != size or sha256_file(temporary) != digest:
                raise ProjectSnapshotError("artifact changed during publication")
            os.replace(temporary, destination)
        finally:
            temporary.unlink(missing_ok=True)
    return {"locator": locator, "size": size, "file_sha256": digest}


def _load_spec(path: Path) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_bytes())
    except (OSError, yaml.YAMLError) as exc:
        raise ProjectSnapshotError(f"snapshot specification is unreadable: {exc}") from exc
    if not isinstance(value, dict):
        raise ProjectSnapshotError("snapshot specification must contain a mapping")
    return value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    capture_parser = subparsers.add_parser("capture")
    capture_parser.add_argument("spec", type=Path)
    capture_parser.add_argument("--output", required=True, type=Path)
    capture_parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("manifest", type=Path)
    verify_parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    verify_parser.add_argument("--live", action="store_true")
    materialize_parser = subparsers.add_parser("materialize")
    materialize_parser.add_argument("manifest", type=Path)
    materialize_parser.add_argument("destination", type=Path)
    materialize_parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    publish_parser = subparsers.add_parser("publish-artifact")
    publish_parser.add_argument("source", type=Path)
    publish_parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    publish_parser.add_argument("--store-root", default="artifacts/sha256")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.command == "capture":
            spec = _load_spec(args.spec)
            result = capture(
                args.repo_root,
                manifest_path=args.output,
                paths=spec.get("paths", []),
                closed_roots=spec.get("closed_roots", []),
                external_artifacts=spec.get("external_artifacts", []),
                reference=spec.get("ref", DEFAULT_REF),
                created_at=spec.get("created_at"),
            )
        elif args.command == "verify":
            result = verify(args.repo_root, args.manifest, require_live=args.live)
        elif args.command == "materialize":
            result = materialize(args.repo_root, args.manifest, args.destination)
        else:
            result = publish_artifact(args.source, args.repo_root, args.store_root)
    except (OSError, ProjectSnapshotError, yaml.YAMLError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
