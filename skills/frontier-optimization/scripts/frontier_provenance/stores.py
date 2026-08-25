"""Git and portable content-store adapters for Frontier provenance."""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import yaml

from .content import (
    PROJECT_DOMAINS,
    PROJECT_ROLE_DOMAINS,
    WORKFLOW_DEPLOYMENT_ROOTS,
    ProvenanceError,
    artifact_entry,
    authority_payload,
    build_manifest,
    canonical_json,
    normalize_logical_name,
    sha256_bytes,
    verify_manifest,
)
from .review_subject import validate_review_subject


DEFAULT_GIT_REF = "refs/frontier/provenance/current"
FROZEN_INPUT_PREFIX = "project/state/frozen-inputs/"


@dataclass(frozen=True)
class ArtifactSource:
    logical_name: str
    path: Path
    kind: str = "blob"
    behavioral_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ClosedCollection:
    logical_name: str
    directory: Path
    members: tuple[str, ...]


def _safe_regular_file(path: Path, role: str) -> Path:
    if path.is_symlink():
        raise ProvenanceError(f"{role} is a symbolic link: {path}")
    candidate = path.resolve()
    try:
        mode = candidate.lstat().st_mode
    except OSError as exc:
        raise ProvenanceError(f"{role} is unreadable: {path}: {exc}") from exc
    if not stat.S_ISREG(mode):
        raise ProvenanceError(f"{role} is not a regular file: {path}")
    return candidate


def _sources(
    values: Iterable[ArtifactSource],
    domain: str,
    *,
    project_root: Path | None = None,
) -> tuple[list[ArtifactSource], list[dict[str, Any]], dict[str, bytes]]:
    sources = sorted(values, key=lambda item: item.logical_name)
    if not sources:
        raise ProvenanceError("capture requires at least one artifact source")
    seen: set[str] = set()
    entries: list[dict[str, Any]] = []
    raw_by_name: dict[str, bytes] = {}
    normalized_sources: list[ArtifactSource] = []
    resolved_project_root: Path | None = None
    if domain in PROJECT_DOMAINS:
        if project_root is None or project_root.is_symlink():
            raise ProvenanceError("project capture requires a safe project_root")
        resolved_project_root = project_root.resolve()
        if not resolved_project_root.is_dir():
            raise ProvenanceError("project_root must be an existing directory")
    for source in sources:
        name = normalize_logical_name(source.logical_name)
        if name in seen:
            raise ProvenanceError(f"duplicate artifact source: {name}")
        seen.add(name)
        path = _safe_regular_file(source.path, f"artifact {name}")
        if resolved_project_root is not None:
            try:
                relative_parts = path.relative_to(resolved_project_root).parts
            except ValueError as exc:
                raise ProvenanceError(
                    f"project artifact is outside project_root: {path}"
                ) from exc
            lowered = tuple(part.lower() for part in relative_parts)
            if any(
                lowered[index : index + 2] in WORKFLOW_DEPLOYMENT_ROOTS
                for index in range(len(lowered) - 1)
            ):
                raise ProvenanceError(
                    f"project content cannot capture workflow source: {path}"
                )
        raw = path.read_bytes()
        metadata = dict(source.behavioral_metadata)
        metadata.setdefault("executable", bool(path.stat().st_mode & 0o111))
        normalized_sources.append(
            ArtifactSource(name, path, source.kind, metadata)
        )
        entries.append(
            artifact_entry(
                name,
                raw,
                kind=source.kind,
                behavioral_metadata=metadata,
            )
        )
        raw_by_name[name] = raw
    authority_payload(entries, [], domain=domain)
    return normalized_sources, entries, raw_by_name


def _collections(
    values: Iterable[ClosedCollection], sources: Iterable[ArtifactSource]
) -> list[dict[str, Any]]:
    source_paths = {source.logical_name: source.path.resolve() for source in sources}
    result: list[dict[str, Any]] = []
    for value in values:
        directory = value.directory.resolve()
        if not directory.is_dir() or value.directory.is_symlink():
            raise ProvenanceError(f"closed collection is missing or unsafe: {value.logical_name}")
        observed: set[str] = set()
        for path in directory.rglob("*"):
            if path.is_symlink():
                raise ProvenanceError(f"closed collection contains a symbolic link: {path}")
            if path.is_dir():
                continue
            if not path.is_file():
                raise ProvenanceError(f"closed collection contains a nonregular member: {path}")
            observed.add(path.relative_to(directory).as_posix())
        prefix = normalize_logical_name(value.logical_name)
        expected_relative: set[str] = set()
        for logical_name in value.members:
            normalized = normalize_logical_name(logical_name)
            if not normalized.startswith(prefix + "/"):
                raise ProvenanceError(
                    f"closed collection member is outside {prefix}: {normalized}"
                )
            relative = normalized[len(prefix) + 1 :]
            expected_relative.add(relative)
            if source_paths.get(normalized) != (directory / relative).resolve():
                raise ProvenanceError(
                    f"closed collection source does not match directory member: {normalized}"
                )
        if observed != expected_relative:
            raise ProvenanceError(
                f"closed collection membership mismatch for {prefix}: "
                f"missing={sorted(expected_relative - observed)}, extra={sorted(observed - expected_relative)}"
            )
        result.append({"logical_name": prefix, "members": sorted(value.members)})
    return result


class GitSnapshotStore:
    """Store raw selected bytes in Git without filters; SHA-256 remains authority."""

    def __init__(self, repo_root: Path, reference: str = DEFAULT_GIT_REF):
        self.repo_root = repo_root.resolve()
        self.reference = reference
        check = self._git("rev-parse", "--is-inside-work-tree", check=False)
        if check.returncode != 0 or check.stdout.strip() != b"true":
            raise ProvenanceError(f"not a Git worktree: {self.repo_root}")
        if not reference.startswith("refs/frontier/"):
            raise ProvenanceError("Git provenance ref must stay under refs/frontier/")

    def _git(
        self,
        *args: str,
        input_bytes: bytes | None = None,
        index_path: Path | None = None,
        check: bool = True,
        extra_env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[bytes]:
        env = os.environ.copy()
        if index_path is not None:
            env["GIT_INDEX_FILE"] = str(index_path)
        if extra_env:
            env.update(extra_env)
        result = subprocess.run(
            ["git", "-C", str(self.repo_root), *args],
            input=input_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            check=False,
        )
        if check and result.returncode != 0:
            detail = result.stderr.decode(errors="replace").strip()
            raise ProvenanceError(f"git {' '.join(args)} failed: {detail}")
        return result

    def _current_ref(self) -> str | None:
        result = self._git(
            "rev-parse", "--verify", "--quiet", self.reference, check=False
        )
        return result.stdout.decode().strip() if result.returncode == 0 else None

    def capture(
        self,
        sources: Iterable[ArtifactSource],
        *,
        domain: str,
        closed_collections: Iterable[ClosedCollection] = (),
        created_at: str,
    ) -> dict[str, Any]:
        if domain != "workflow-release":
            raise ProvenanceError(
                "Git capture is reserved for workflow releases; use ProjectPortableStore"
            )
        normalized, entries, raw_by_name = _sources(sources, domain)
        previous = self._current_ref()
        object_format = self._git(
            "rev-parse", "--show-object-format"
        ).stdout.decode().strip()
        zero = "0" * (64 if object_format == "sha256" else 40)
        with tempfile.TemporaryDirectory(prefix="frontier-provenance-") as directory:
            index = Path(directory) / "index"
            self._git("read-tree", "--empty", index_path=index)
            for source in normalized:
                raw = raw_by_name[source.logical_name]
                oid = self._git(
                    "hash-object", "-w", "--no-filters", "--stdin", input_bytes=raw
                ).stdout.decode().strip()
                mode = "100755" if source.behavioral_metadata["executable"] else "100644"
                self._git(
                    "update-index",
                    "--add",
                    "--cacheinfo",
                    mode,
                    oid,
                    source.logical_name,
                    index_path=index,
                )
            tree = self._git("write-tree", index_path=index).stdout.decode().strip()
            commit_args = ["commit-tree", tree]
            if previous is not None:
                commit_args.extend(["-p", previous])
            identity = {
                "GIT_AUTHOR_NAME": "Frontier Provenance",
                "GIT_AUTHOR_EMAIL": "frontier-provenance@local.invalid",
                "GIT_COMMITTER_NAME": "Frontier Provenance",
                "GIT_COMMITTER_EMAIL": "frontier-provenance@local.invalid",
                "GIT_AUTHOR_DATE": created_at,
                "GIT_COMMITTER_DATE": created_at,
            }
            commit = self._git(
                *commit_args,
                input_bytes=f"Frontier provenance snapshot at {created_at}\n".encode(),
                extra_env=identity,
            ).stdout.decode().strip()
        manifest = build_manifest(
            entries,
            _collections(closed_collections, normalized),
            {
                "adapter": "git-snapshot/1",
                "commit": commit,
                "tree": tree,
                "ref": self.reference,
                "parent_commit": previous,
                "object_format": object_format,
            },
            domain=domain,
        )
        self.verify(manifest, require_reachable=False)
        self._git("update-ref", self.reference, commit, previous or zero)
        self.verify(manifest)
        return manifest

    def _tree(self, treeish: str) -> dict[str, tuple[str, str, bytes]]:
        output = self._git("ls-tree", "-r", "-z", treeish).stdout
        observed: dict[str, tuple[str, str, bytes]] = {}
        for row in output.split(b"\0"):
            if not row:
                continue
            metadata, raw_name = row.split(b"\t", 1)
            mode, kind, oid = metadata.decode().split(" ", 2)
            if kind != "blob" or mode not in {"100644", "100755"}:
                raise ProvenanceError("Git provenance tree contains a non-blob member")
            name = raw_name.decode()
            observed[name] = (
                mode,
                oid,
                self._git("cat-file", "blob", oid).stdout,
            )
        return observed

    def verify(
        self,
        manifest: dict[str, Any],
        *,
        require_live: bool = False,
        require_reachable: bool = True,
    ) -> dict[str, Any]:
        if not isinstance(manifest, dict) or manifest.get("domain") != "workflow-release":
            raise ProvenanceError("Git verification is reserved for workflow releases")
        content_root = verify_manifest(manifest)
        storage = manifest["storage"]
        required = {
            "adapter",
            "commit",
            "tree",
            "ref",
            "parent_commit",
            "object_format",
        }
        if set(storage) != required or storage.get("adapter") != "git-snapshot/1":
            raise ProvenanceError("Git storage binding is invalid")
        if storage.get("ref") != self.reference:
            raise ProvenanceError("Git storage ref does not match this adapter")
        actual_format = self._git("rev-parse", "--show-object-format").stdout.decode().strip()
        if storage["object_format"] != actual_format:
            raise ProvenanceError("Git object format binding is invalid")
        parent_line = self._git(
            "rev-list", "--parents", "-n", "1", storage["commit"]
        ).stdout.decode().strip().split()
        observed_parent = parent_line[1] if len(parent_line) == 2 else None
        if len(parent_line) > 2 or observed_parent != storage["parent_commit"]:
            raise ProvenanceError("Git parent commit binding is invalid")
        if require_reachable:
            current = self._current_ref()
            if current is None:
                raise ProvenanceError("Git provenance ref is missing")
            reachable = self._git(
                "merge-base", "--is-ancestor", storage["commit"], current, check=False
            )
            if reachable.returncode != 0:
                raise ProvenanceError("Git provenance commit is unreachable")
        commit_tree = self._git(
            "rev-parse", f"{storage['commit']}^{{tree}}"
        ).stdout.decode().strip()
        if commit_tree != storage["tree"]:
            raise ProvenanceError("Git provenance commit binds a different tree")
        observed = self._tree(storage["tree"])
        expected_names = {item["logical_name"] for item in manifest["artifacts"]}
        if set(observed) != expected_names:
            raise ProvenanceError("Git provenance tree membership changed")
        for item in manifest["artifacts"]:
            mode, _, raw = observed[item["logical_name"]]
            executable = item["behavioral_metadata"].get("executable") is True
            if mode != ("100755" if executable else "100644"):
                raise ProvenanceError(
                    f"Git provenance mode changed: {item['logical_name']}"
                )
            if len(raw) != item["size"] or sha256_bytes(raw) != item["content_sha256"]:
                raise ProvenanceError(
                    f"Git provenance bytes changed: {item['logical_name']}"
                )
        if require_live:
            raise ProvenanceError(
                "live verification requires a new capture request; a stored logical tree cannot infer source locations"
            )
        return {
            "content_root": content_root,
            "domain": manifest["domain"],
            "adapter": "git-snapshot/1",
            "artifact_count": len(observed),
            "receipt_facts": _receipt_facts(
                manifest,
                {name: value[2] for name, value in observed.items()},
            ),
            "verified": True,
        }

    def compare_sources(
        self,
        manifest: dict[str, Any],
        sources: Iterable[ArtifactSource],
        *,
        domain: str,
        closed_collections: Iterable[ClosedCollection] = (),
    ) -> dict[str, Any]:
        """Recompute selected live raw bytes without writing Git objects."""

        if domain != "workflow-release":
            raise ProvenanceError(
                "Git comparison is reserved for workflow releases"
            )

        normalized, entries, _ = _sources(sources, domain)
        live = build_manifest(
            entries,
            _collections(closed_collections, normalized),
            manifest["storage"],
            domain=domain,
        )
        expected = verify_manifest(manifest)
        observed = verify_manifest(live)
        return {
            "content_root": expected,
            "observed_content_root": observed,
            "verified": expected == observed,
        }

    def raw_artifacts(self, manifest: dict[str, Any]) -> dict[str, bytes]:
        self.verify(manifest)
        return {
            name: raw
            for name, (_, _, raw) in self._tree(manifest["storage"]["tree"]).items()
        }


class PortableBundleStore:
    """Portable exact-byte adapter that verifies without a Git repository."""

    def capture(
        self,
        sources: Iterable[ArtifactSource],
        destination: Path,
        *,
        domain: str,
        closed_collections: Iterable[ClosedCollection] = (),
    ) -> dict[str, Any]:
        if domain in PROJECT_DOMAINS:
            raise ProvenanceError(
                "project capture requires the role-specific ProjectPortableStore"
            )
        return self._capture_domain(
            sources,
            destination,
            domain=domain,
            closed_collections=closed_collections,
        )

    def _capture_domain(
        self,
        sources: Iterable[ArtifactSource],
        destination: Path,
        *,
        domain: str,
        closed_collections: Iterable[ClosedCollection] = (),
        project_root: Path | None = None,
    ) -> dict[str, Any]:
        normalized, entries, raw_by_name = _sources(
            sources, domain, project_root=project_root
        )
        return self._write(
            entries,
            raw_by_name,
            destination,
            closed_collections,
            normalized,
            domain,
        )

    def _write(
        self,
        entries: list[dict[str, Any]],
        raw_by_name: dict[str, bytes],
        destination: Path,
        closed_collections: Iterable[ClosedCollection],
        sources: Iterable[ArtifactSource] | None,
        domain: str,
    ) -> dict[str, Any]:
        if destination.exists():
            raise ProvenanceError(f"portable destination already exists: {destination}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        staging = Path(
            tempfile.mkdtemp(prefix=f".{destination.name}.", dir=destination.parent)
        )
        try:
            objects = staging / "objects"
            objects.mkdir()
            for item in entries:
                digest = item["content_sha256"]
                output = objects / digest[:2] / digest
                output.parent.mkdir(parents=True, exist_ok=True)
                raw = raw_by_name[item["logical_name"]]
                if output.exists() and output.read_bytes() != raw:
                    raise ProvenanceError(f"portable object collision: {digest}")
                output.write_bytes(raw)
            manifest = build_manifest(
                entries,
                (
                    _collections(closed_collections, sources)
                    if sources is not None
                    else [
                        {"logical_name": item.logical_name, "members": list(item.members)}
                        for item in closed_collections
                    ]
                ),
                {"adapter": "portable-bundle/1", "object_root": "objects"},
                domain=domain,
            )
            (staging / "manifest.json").write_bytes(canonical_json(manifest) + b"\n")
            self.verify(staging, manifest)
            os.replace(staging, destination)
            return manifest
        finally:
            if staging.exists():
                shutil.rmtree(staging)

    def export_from_git(
        self,
        git_store: GitSnapshotStore,
        manifest: dict[str, Any],
        destination: Path,
    ) -> dict[str, Any]:
        raw = git_store.raw_artifacts(manifest)
        entries = [dict(item) for item in manifest["artifacts"]]
        collections = [
            ClosedCollection(item["logical_name"], Path("."), tuple(item["members"]))
            for item in manifest["closed_collections"]
        ]
        return self._write(
            entries,
            raw,
            destination,
            collections,
            None,
            manifest["domain"],
        )

    def verify(
        self, destination: Path, manifest: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        if not destination.is_dir() or destination.is_symlink():
            raise ProvenanceError("portable bundle root is missing or unsafe")
        manifest_path = destination / "manifest.json"
        objects_root = destination / "objects"
        if (
            not manifest_path.is_file()
            or manifest_path.is_symlink()
            or not objects_root.is_dir()
            or objects_root.is_symlink()
        ):
            raise ProvenanceError("portable manifest or object root is missing or unsafe")
        if manifest is None:
            try:
                manifest = json.loads(manifest_path.read_text())
            except (OSError, json.JSONDecodeError) as exc:
                raise ProvenanceError(f"portable manifest is unreadable: {exc}") from exc
        content_root = verify_manifest(manifest)
        storage = manifest["storage"]
        if storage != {"adapter": "portable-bundle/1", "object_root": "objects"}:
            raise ProvenanceError("portable storage binding is invalid")
        expected: set[str] = set()
        raw_by_name: dict[str, bytes] = {}
        for item in manifest["artifacts"]:
            digest = item["content_sha256"]
            relative = f"objects/{digest[:2]}/{digest}"
            expected.add(relative)
            path = destination / relative
            if (
                not path.is_file()
                or path.is_symlink()
                or path.parent.is_symlink()
            ):
                raise ProvenanceError(f"portable object is missing or unsafe: {relative}")
            raw = path.read_bytes()
            if len(raw) != item["size"] or sha256_bytes(raw) != digest:
                raise ProvenanceError(f"portable object identity mismatch: {relative}")
            raw_by_name[item["logical_name"]] = raw
        observed = {
            path.relative_to(destination).as_posix()
            for path in destination.rglob("*")
            if path.is_file()
        }
        if observed != expected | {"manifest.json"}:
            raise ProvenanceError("portable bundle contains missing or unexpected files")
        return {
            "content_root": content_root,
            "domain": manifest["domain"],
            "adapter": "portable-bundle/1",
            "artifact_count": len(manifest["artifacts"]),
            "closed_collections": manifest["closed_collections"],
            "receipt_facts": _receipt_facts(manifest, raw_by_name),
            "review_subject": validate_review_subject(manifest, raw_by_name),
            "verified": True,
        }

    def read_artifacts(self, destination: Path) -> dict[str, bytes]:
        """Return verified logical bytes from one portable bundle."""

        self.verify(destination)
        try:
            manifest = json.loads((destination / "manifest.json").read_text())
        except (OSError, json.JSONDecodeError) as exc:  # pragma: no cover - verify owns this path
            raise ProvenanceError(f"portable manifest is unreadable: {exc}") from exc
        return {
            item["logical_name"]: (
                destination
                / "objects"
                / item["content_sha256"][:2]
                / item["content_sha256"]
            ).read_bytes()
            for item in manifest["artifacts"]
        }


class ProjectPortableStore:
    """Capture project bytes through a role that fixes the content domain."""

    @staticmethod
    def _validate_frozen_input_names(
        role: str, sources: list[ArtifactSource], project_root: Path
    ) -> None:
        if role != "state":
            return
        resolved_root = project_root.resolve()
        for source in sources:
            logical_name = normalize_logical_name(source.logical_name)
            if not logical_name.startswith(FROZEN_INPUT_PREFIX):
                continue
            resolved_source = source.path.resolve()
            try:
                relative = resolved_source.relative_to(resolved_root).as_posix()
            except ValueError as exc:
                raise ProvenanceError(
                    f"project artifact is outside project_root: {resolved_source}"
                ) from exc
            if logical_name.removeprefix(FROZEN_INPUT_PREFIX) != relative:
                raise ProvenanceError(
                    "frozen input logical name must match its project-relative "
                    f"source path: {logical_name} != {FROZEN_INPUT_PREFIX}{relative}"
                )

    def capture(
        self,
        role: str,
        sources: Iterable[ArtifactSource],
        destination: Path,
        *,
        project_root: Path,
        closed_collections: Iterable[ClosedCollection] = (),
    ) -> dict[str, Any]:
        domain = PROJECT_ROLE_DOMAINS.get(role)
        if domain is None:
            raise ProvenanceError(f"unsupported project content role: {role!r}")
        source_list = list(sources)
        self._validate_frozen_input_names(role, source_list, project_root)
        return PortableBundleStore()._capture_domain(
            source_list,
            destination,
            domain=domain,
            closed_collections=closed_collections,
            project_root=project_root,
        )

    def verify(
        self, destination: Path, *, expected_role: str | None = None
    ) -> dict[str, Any]:
        """Verify stored bytes, not their historical source-path eligibility."""

        result = PortableBundleStore().verify(destination)
        if result["domain"] not in PROJECT_DOMAINS:
            raise ProvenanceError("project store cannot verify a workflow release")
        if expected_role is not None:
            expected = PROJECT_ROLE_DOMAINS.get(expected_role)
            if expected is None or result["domain"] != expected:
                raise ProvenanceError("project bundle role does not match its domain")
        return result


class WorkflowReleaseGitStore(GitSnapshotStore):
    """Store workflow release bytes in Git without exposing a domain choice."""

    def capture_release(
        self,
        sources: Iterable[ArtifactSource],
        *,
        closed_collections: Iterable[ClosedCollection] = (),
        created_at: str,
    ) -> dict[str, Any]:
        return super().capture(
            sources,
            domain="workflow-release",
            closed_collections=closed_collections,
            created_at=created_at,
        )

    def compare_release_sources(
        self,
        manifest: dict[str, Any],
        sources: Iterable[ArtifactSource],
        *,
        closed_collections: Iterable[ClosedCollection] = (),
    ) -> dict[str, Any]:
        return super().compare_sources(
            manifest,
            sources,
            domain="workflow-release",
            closed_collections=closed_collections,
        )


def _receipt_facts(
    manifest: dict[str, Any], raw_by_name: dict[str, bytes]
) -> dict[str, dict[str, Any]]:
    receipts: dict[str, dict[str, Any]] = {}
    for item in manifest["artifacts"]:
        if item["kind"] != "external-receipt":
            continue
        metadata = item["behavioral_metadata"]
        fact = metadata["fact"]
        if fact in receipts:
            raise ProvenanceError(f"duplicate external receipt fact: {fact}")
        receipt: dict[str, Any] = {
            "status": metadata["status"],
            "observed_at": metadata["observed_at"],
            "expires_at": metadata["expires_at"],
        }
        try:
            document = yaml.safe_load(raw_by_name[item["logical_name"]])
        except yaml.YAMLError as exc:
            raise ProvenanceError(f"external receipt body is unreadable: {fact}") from exc
        if isinstance(document, dict):
            receipt["document"] = document
        receipts[fact] = receipt
    return receipts
