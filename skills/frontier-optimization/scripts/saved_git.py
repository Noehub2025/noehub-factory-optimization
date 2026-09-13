"""Read exact project inputs without importing historical provenance machinery."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path, PurePosixPath
import re
import subprocess


class SavedGitError(ValueError):
    """A selected revision or input cannot be read as requested."""


def normalize_path(value: str) -> str:
    """Preserve literal filename characters while rejecting paths outside the repo."""
    if not isinstance(value, str) or not value or "\0" in value:
        raise SavedGitError("repository path must be a nonempty string without NUL")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or ".git" in path.parts or path.as_posix() == ".":
        raise SavedGitError(f"invalid repository-relative path: {value!r}")
    return path.as_posix()


def _git(root: Path, *args: str, input: bytes | None = None) -> bytes:
    try:
        return subprocess.run(
            ["git", "--literal-pathspecs", "-C", str(root), *args],
            input=input, check=True, capture_output=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError) as exc:
        raise SavedGitError(f"cannot read saved Git input: {exc}") from exc


def resolve_revision(root: Path, revision: str, *, exact: bool = False) -> str:
    """Resolve a revision to a commit; saved selections require an exact full hash."""
    if not isinstance(revision, str) or not revision or "\0" in revision:
        raise SavedGitError("Git revision must be a nonempty string without NUL")
    if exact and not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", revision):
        raise SavedGitError("saved input requires a full Git commit")
    commit = _git(root, "rev-parse", "--verify", "--end-of-options", revision + "^{commit}").decode().strip()
    if exact and commit != revision:
        raise SavedGitError("saved input must name its exact Git commit")
    return commit


def validate_selection(root: Path, commit: str, paths: Iterable[str]) -> None:
    """Check selected objects in two Git calls, allowing Candidate Revision trees."""
    selected = tuple(normalize_path(path) for path in paths)
    if not selected or len(set(selected)) != len(selected):
        raise SavedGitError("selected paths must be nonempty and unique")
    commit = resolve_revision(root, commit, exact=True)
    # Input is NUL-delimited; successful output contains only hashes, never paths.
    rows = _git(
        root, "cat-file", "--batch-check=%(objectname)", "-z",
        input=b"".join(f"{commit}:{path}\0".encode() for path in selected),
    ).splitlines()
    if len(rows) != len(selected) or any(
        re.fullmatch(rb"[0-9a-f]{40}|[0-9a-f]{64}", row) is None for row in rows
    ):
        raise SavedGitError("selected paths are unavailable at the saved commit")


def read_file(root: Path, commit: str, path: str) -> bytes:
    """Read one regular file literally; directories and symlinks are not documents."""
    path = normalize_path(path)
    commit = resolve_revision(root, commit, exact=True)
    rows = _git(root, "ls-tree", "-z", "--full-tree", commit, "--", path).split(b"\0")
    entries = [row.split(b"\t", 1) for row in rows if row]
    if len(entries) != 1 or len(entries[0]) != 2 or entries[0][1] != path.encode():
        raise SavedGitError(f"required regular file is absent at saved version: {path!r}")
    metadata = entries[0][0].split()
    if len(metadata) != 3 or metadata[0] not in {b"100644", b"100755"} or metadata[1] != b"blob":
        raise SavedGitError(f"saved document must be a regular file: {path!r}")
    return _git(root, "cat-file", "blob", metadata[2].decode())
