"""Read existing Git versions without creating snapshot commits or file copies."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Iterable

from .content import (
    PROJECT_ROLE_DOMAINS, ProvenanceError, artifact_entry, build_manifest,
    canonical_json, normalize_logical_name, verify_manifest,
)
from .review_subject import INDEX_LOGICAL_NAME, validate_review_subject
from .stores import ArtifactSource, ClosedCollection, _collections, _receipt_facts


ADAPTER = "git-reference/1"


def git_bytes(root: Path, *args: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, check=False,
    )
    if result.returncode:
        raise ProvenanceError(result.stderr.decode(errors="replace").strip())
    return result.stdout


def repository_root(path: Path) -> Path:
    return Path(git_bytes(path, "rev-parse", "--show-toplevel").decode().strip())


def retained_commit(root: Path, revision: str) -> str:
    commit = git_bytes(root, "rev-parse", "--verify", "--end-of-options", revision + "^{commit}").decode().strip()
    if not git_bytes(root, "for-each-ref", "--contains=" + commit, "--format=%(refname)").strip():
        raise ProvenanceError("save this version on a retained branch or tag before citing it")
    return commit


def lfs_target(raw: bytes) -> dict[str, Any] | None:
    if not raw.startswith(b"version https://git-lfs.github.com/spec/v1\n"):
        return None
    try:
        fields = dict(line.split(" ", 1) for line in raw.decode().splitlines())
        algorithm, digest = fields["oid"].split(":", 1)
        size = int(fields["size"])
        if algorithm != "sha256" or len(digest) != 64 or size < 0:
            raise ValueError()
        int(digest, 16)
    except (KeyError, ValueError, UnicodeError) as exc:
        raise ProvenanceError("invalid Git LFS pointer") from exc
    return {"sha256": digest, "size": size}


def verify_retained_artifact(path: Path, *, sha256: str, size: int) -> dict[str, Any]:
    """Check one required local payload on use, not every reference to its record."""
    if not path.is_file() or path.is_symlink():
        raise ProvenanceError(f"required artifact is unavailable: {path}")
    digest = hashlib.sha256()
    count = 0
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            count += len(chunk)
            digest.update(chunk)
    if count != size or digest.hexdigest() != sha256:
        raise ProvenanceError(f"required artifact differs from its retained version: {path}")
    return {"verified": True, "size": count, "sha256": sha256}


class GitReferenceStore:
    """Store a small reference record; leave all existing file content in Git."""

    def __init__(self, root: Path):
        self.root = repository_root(root.resolve())

    def capture(
        self, role: str, sources: Iterable[ArtifactSource], destination: Path,
        *, revision: str = "HEAD", closed_collections: Iterable[ClosedCollection] = (),
        subject_index: dict[str, Any] | None = None,
        expected_bytes: dict[str, bytes] | None = None,
    ) -> dict[str, Any]:
        from .stores import ProjectPortableStore

        domain = PROJECT_ROLE_DOMAINS.get(role)
        if domain is None:
            raise ProvenanceError(f"unsupported project role: {role}")
        source_list = list(sources)
        ProjectPortableStore._validate_frozen_input_names(role, source_list, self.root)
        commit = retained_commit(self.root, revision)
        entries, paths, raw_by_name = [], {}, {}
        for source in source_list:
            name = normalize_logical_name(source.logical_name)
            try:
                relative = source.path.resolve().relative_to(self.root).as_posix()
            except ValueError as exc:
                raise ProvenanceError("project source is outside its repository") from exc
            if name in paths:
                raise ProvenanceError(f"duplicate logical name: {name}")
            self._project_path(relative)
            raw, executable = self._read(commit, relative)
            metadata = dict(source.behavioral_metadata)
            metadata.setdefault("executable", executable)
            if (metadata["executable"] != executable
                    or bool(source.path.stat().st_mode & 0o111) != executable):
                raise ProvenanceError(f"save the executable-mode change before citing {relative}")
            # A reference must describe the chosen input, not silently substitute HEAD.
            if source.path.is_symlink():
                raise ProvenanceError(f"source is a symbolic link: {relative}")
            target = lfs_target(raw)
            if expected_bytes is not None:
                if expected_bytes.get(name) != raw:
                    raise ProvenanceError(f"save the reviewed input in Git before citing {relative}")
            elif target is not None:
                # A pointer-only checkout is valid metadata, not an available payload.
                with source.path.open("rb") as stream:
                    prefix = stream.read(len(raw) + 1)
                if prefix != raw:
                    verify_retained_artifact(source.path, **target)
            else:
                verify_retained_artifact(source.path, sha256=hashlib.sha256(raw).hexdigest(), size=len(raw))
            entries.append(artifact_entry(name, raw, kind=source.kind, behavioral_metadata=metadata))
            paths[name] = relative
            raw_by_name[name] = raw
        generated = {}
        if subject_index is not None:
            if role != "decision" or INDEX_LOGICAL_NAME in paths:
                raise ProvenanceError("only decision preparation may generate a subject index")
            raw = canonical_json(subject_index) + b"\n"
            generated[INDEX_LOGICAL_NAME] = raw.decode()
            raw_by_name[INDEX_LOGICAL_NAME] = raw
            entries.append(artifact_entry(INDEX_LOGICAL_NAME, raw))
        manifest = build_manifest(
            entries, _collections(closed_collections, source_list),
            {"adapter": ADAPTER, "commit": commit, "paths": paths, "generated": generated},
            domain=domain,
        )
        # Preparation owns semantic analysis; storage checks index consistency only.
        validate_review_subject(manifest, raw_by_name, check_semantics=False)
        destination.mkdir(parents=True, exist_ok=True)
        output = destination / "manifest.json"
        if output.exists():
            previous = json.loads(output.read_text())
            if previous.get("content_root") == manifest["content_root"]:
                self.verify(destination)
                return previous
            raise ProvenanceError(f"content reference already exists with different content: {output}")
        fd, temporary = tempfile.mkstemp(prefix=".reference-", dir=destination)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(canonical_json(manifest) + b"\n")
            os.link(temporary, output)
        finally:
            os.unlink(temporary)
        return manifest

    @staticmethod
    def _project_path(relative: str) -> str:
        from .content import WORKFLOW_DEPLOYMENT_ROOTS

        relative = normalize_logical_name(relative)
        parts = tuple(part.lower() for part in Path(relative).parts)
        if any(parts[index:index + 2] in WORKFLOW_DEPLOYMENT_ROOTS for index in range(len(parts) - 1)):
            raise ProvenanceError("workflow deployment content is not a project input")
        return relative

    def _read(self, commit: str, relative: str) -> tuple[bytes, bool]:
        relative = self._project_path(relative)
        listing = git_bytes(self.root, "--literal-pathspecs", "ls-tree", "-z", commit, "--", relative)
        rows = [item for item in listing.split(b"\0") if item]
        if len(rows) != 1:
            raise ProvenanceError(f"save a normal Git checkpoint containing {relative} before citing it")
        metadata, name = rows[0].split(b"\t", 1)
        mode, kind, oid = metadata.decode().split()
        if name.decode() != relative or kind != "blob" or mode not in {"100644", "100755"}:
            raise ProvenanceError(f"reference is not a regular project file: {relative}")
        return git_bytes(self.root, "cat-file", "blob", oid), mode == "100755"

    def verify(
        self, destination: Path, *, manifest: dict[str, Any] | None = None,
        raw_out: dict[str, bytes] | None = None,
        check_semantics: bool = False,
    ) -> dict[str, Any]:
        if manifest is None:
            source = destination / "manifest.json"
            if source.is_symlink() or not source.is_file():
                raise ProvenanceError("Git reference record is missing or unsafe")
            try:
                manifest = json.loads(source.read_text())
            except (OSError, ValueError) as exc:
                raise ProvenanceError("Git reference record is unreadable") from exc
        root = verify_manifest(manifest)
        storage = manifest["storage"]
        if set(storage) != {"adapter", "commit", "paths", "generated"} or storage["adapter"] != ADAPTER:
            raise ProvenanceError("invalid Git content reference")
        commit = retained_commit(self.root, storage["commit"])
        if commit != storage["commit"]:
            raise ProvenanceError("Git content reference must name a full commit object")
        paths, generated = storage["paths"], storage["generated"]
        if not isinstance(paths, dict) or not isinstance(generated, dict) or set(generated) - {INDEX_LOGICAL_NAME}:
            raise ProvenanceError("invalid Git content members")
        expected = {entry["logical_name"] for entry in manifest["artifacts"]}
        if set(paths) & set(generated) or set(paths) | set(generated) != expected:
            raise ProvenanceError("Git content reference members differ from the adopted content")
        raw_by_name = {}
        for entry in manifest["artifacts"]:
            name = entry["logical_name"]
            if name in generated:
                raw, executable = generated[name].encode(), False
            else:
                raw, executable = self._read(commit, paths[name])
            if (len(raw) != entry["size"] or hashlib.sha256(raw).hexdigest() != entry["content_sha256"]
                    or bool(entry["behavioral_metadata"].get("executable", False)) != executable):
                raise ProvenanceError(f"Git content does not match the adopted bytes: {name}")
            raw_by_name[name] = raw
        subject = validate_review_subject(manifest, raw_by_name, check_semantics=check_semantics)
        if raw_out is not None:
            raw_out.update(raw_by_name)
        return {"content_root": root, "domain": manifest["domain"], "adapter": ADAPTER,
                "artifact_count": len(expected), "closed_collections": manifest["closed_collections"],
                "receipt_facts": _receipt_facts(manifest, raw_by_name), "review_subject": subject,
                "verified": True}


class ContentSession:
    """One operation's verified content and reads, shared by all its consumers."""

    def __init__(self, bindings: list[dict[str, Any]]):
        from .stores import PortableBundleStore

        if not isinstance(bindings, list):
            raise ProvenanceError("content_bindings must be a list")
        self.results, self.raw, self.paths = {}, {}, {}
        for binding in bindings:
            if (not isinstance(binding, dict) or not {"adapter", "path"} <= set(binding)
                    or set(binding) - {"adapter", "path", "repo_root"}):
                raise ProvenanceError("invalid content binding")
            path = Path(binding["path"])
            raw = {}
            if binding["adapter"] == ADAPTER:
                result = GitReferenceStore(Path(binding.get("repo_root", path))).verify(path, raw_out=raw)
            elif binding["adapter"] == "portable-bundle/1":
                result = PortableBundleStore().verify(path, raw_out=raw, check_semantics=False)
            else:
                raise ProvenanceError("unsupported content binding")
            if result["adapter"] != binding["adapter"]:
                raise ProvenanceError("content adapter does not match its binding")
            root = result["content_root"]
            if root in self.results:
                raise ProvenanceError(f"duplicate content binding: {root}")
            self.results[root], self.raw[root], self.paths[root] = result, raw, path

    def resolve(self, root: str) -> dict[str, Any]:
        try:
            return self.results[root]
        except KeyError as exc:
            raise ProvenanceError(f"content root has no binding: {root}") from exc

    def read(self, root: str) -> dict[str, bytes]:
        self.resolve(root)
        return self.raw[root]
