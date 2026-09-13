"""Saved-input behavior against real disposable Git repositories."""

from pathlib import Path
import subprocess
from unittest.mock import patch

import pytest

from saved_git import SavedGitError, read_file, resolve_revision, validate_selection


def git(root: Path, *args: str) -> bytes:
    return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True).stdout


@pytest.fixture
def saved(tmp_path):
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.name", "Saved Input Test")
    git(tmp_path, "config", "user.email", "tests@example.invalid")
    paths = ("plain", "space name", "line\nbreak", "tab\tname", "[literal]*", "-leading", " trailing ", ":(glob)literal")
    for name in paths:
        (tmp_path / name).write_bytes(name.encode() + b"\0saved bytes")
    (tmp_path / "dir").mkdir()
    (tmp_path / "dir/child").write_bytes(b"child")
    (tmp_path / "link").symlink_to("plain")
    git(tmp_path, "add", "--all")
    git(tmp_path, "commit", "-qm", "saved inputs")
    commit = git(tmp_path, "rev-parse", "HEAD").decode().strip()
    return tmp_path, commit, paths


def test_saved_bytes_ignore_working_changes_and_preserve_literal_paths(saved):
    repo, commit, paths = saved
    for path in paths:
        (repo / path).write_bytes(b"changed")
        assert read_file(repo, commit, path) == path.encode() + b"\0saved bytes"
    assert resolve_revision(repo, "HEAD") == commit
    with patch("saved_git.subprocess.run", wraps=subprocess.run) as commands:
        validate_selection(repo, commit, (*paths, "dir"))
    assert commands.call_count == 2


@pytest.mark.parametrize("path", ["dir", "link", "pla*", ":(glob)pla*", "absent", "../plain", "/plain", ".git/config", "plain\0other"])
def test_document_reads_reject_nonfiles_and_never_expand_pathspecs(saved, path):
    repo, commit, _ = saved
    with pytest.raises(SavedGitError):
        read_file(repo, commit, path)


def test_candidate_objects_and_document_files_keep_different_rules(saved):
    repo, commit, _ = saved
    validate_selection(repo, commit, ("dir", "link"))
    for revision in ("HEAD", commit[:12], "0" * 40):
        with pytest.raises(SavedGitError):
            validate_selection(repo, revision, ("plain",))
        with pytest.raises(SavedGitError):
            read_file(repo, revision, "plain")
    for paths in ((), ("plain", "plain"), ("absent\nfile",)):
        with pytest.raises(SavedGitError):
            validate_selection(repo, commit, paths)
