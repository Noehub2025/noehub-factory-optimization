"""Focused behavior checks for Git-backed project history and legacy reads."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from frontier_provenance import NodeRepository, ProvenanceError, freeze_decision
from frontier_provenance.content import PROJECT_ROLE_DOMAINS
from frontier_provenance.git_content import (
    ADAPTER, ContentSession, GitReferenceStore, verify_retained_artifact,
)
from frontier_provenance.handoff import export_handoff, verify_handoff
from frontier_provenance.stores import ArtifactSource, PortableBundleStore, ProjectPortableStore
from frontier_provenance_cli import REQUEST_CONTRACT, apply_operation
from frontier_review import prepare_review
from test_frontier_review_preparation import write_entry


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], stderr=subprocess.PIPE).decode().strip()


def checkpoint(root: Path) -> str:
    git(root, "add", "--all")
    git(root, "-c", "user.name=Workflow Test", "-c", "user.email=test@example.invalid",
        "commit", "--allow-empty", "-qm", "ordinary checkpoint")
    return git(root, "rev-parse", "HEAD")


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    git(tmp_path, "init", "-q")
    (tmp_path / "input.txt").write_text("retained input\n")
    checkpoint(tmp_path)
    return tmp_path


def capture(root: Path, destination: str = "record") -> dict:
    return ProjectPortableStore().capture(
        "outcome", [ArtifactSource("project/outcome/input.txt", root / "input.txt")],
        root / destination, project_root=root)


def test_capture_references_existing_commit_without_git_mutation(repo: Path) -> None:
    head = git(repo, "rev-parse", "HEAD")
    index = git(repo, "ls-files", "--stage")
    refs = git(repo, "show-ref")
    manifest = capture(repo)
    assert manifest["storage"]["commit"] == head
    assert manifest["storage"]["adapter"] == ADAPTER
    assert list((repo / "record").iterdir()) == [repo / "record/manifest.json"]
    assert git(repo, "rev-parse", "HEAD") == head
    assert git(repo, "ls-files", "--stage") == index
    assert git(repo, "show-ref") == refs


def test_unrelated_commit_and_workflow_update_do_not_change_scope_identity(repo: Path) -> None:
    first = capture(repo)
    deployed = repo / ".claude/skills/example/SKILL.md"
    deployed.parent.mkdir(parents=True)
    deployed.write_text("new workflow\n")
    (repo / "unrelated.txt").write_text("unrelated work\n")
    checkpoint(repo)
    second = capture(repo, "later")
    assert first["content_root"] == second["content_root"]
    assert first["storage"]["commit"] != second["storage"]["commit"]
    with pytest.raises(ProvenanceError, match="workflow deployment"):
        GitReferenceStore(repo).capture("decision", [ArtifactSource("project/decision/tool", deployed)], repo / "bad")


def test_working_changes_preserve_retained_evidence_but_cannot_be_silently_captured(repo: Path) -> None:
    original = capture(repo)
    (repo / "input.txt").write_text("next working revision\n")
    session = ContentSession([{"adapter": ADAPTER, "path": str(repo / "record")}])
    assert session.read(original["content_root"])["project/outcome/input.txt"] == b"retained input\n"
    with pytest.raises(ProvenanceError, match="differs"):
        capture(repo, "dirty")
    checkpoint(repo)
    assert capture(repo, "revised")["content_root"] != original["content_root"]


def test_new_capture_requires_git_without_creating_a_repository(tmp_path: Path) -> None:
    (tmp_path / "input.txt").write_text("input")
    with pytest.raises(ProvenanceError, match="git repository"):
        capture(tmp_path)
    assert not (tmp_path / ".git").exists()


def test_unsaved_executable_mode_is_not_silently_replaced(repo: Path) -> None:
    (repo / "input.txt").chmod(0o755)
    with pytest.raises(ProvenanceError, match="executable-mode"):
        capture(repo)
    checkpoint(repo)
    assert capture(repo)["artifacts"][0]["behavioral_metadata"]["executable"]


def test_session_reads_each_member_once(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    manifest = capture(repo)
    original = GitReferenceStore._read
    calls = []

    def counted(self, commit, relative):
        calls.append(relative)
        return original(self, commit, relative)

    monkeypatch.setattr(GitReferenceStore, "_read", counted)
    session = ContentSession([{"adapter": ADAPTER, "path": str(repo / "record")}])
    session.resolve(manifest["content_root"])
    session.read(manifest["content_root"])
    session.read(manifest["content_root"])
    assert calls == ["input.txt"]


def test_legacy_bundle_is_readable_through_current_cli_without_migration(repo: Path) -> None:
    manifest = PortableBundleStore()._capture_domain(
        [ArtifactSource("project/decision/input", repo / "input.txt")], repo / "legacy",
        domain=PROJECT_ROLE_DOMAINS["decision"], project_root=repo)
    node = freeze_decision(decision_root=manifest["content_root"])
    nodes = NodeRepository(repo / "nodes")
    nodes.write(node)
    before = (repo / "legacy/manifest.json").read_bytes()
    result = apply_operation({"contract_version": REQUEST_CONTRACT, "operation": "verify",
        "root_id": node["node_id"], "consequence": "audit", "live_facts": {}, "checked_at": None,
        "content_bindings": [{"adapter": "portable-bundle/1", "path": str(repo / "legacy")}]}, nodes)
    assert result["ready"]
    assert (repo / "legacy/manifest.json").read_bytes() == before


def test_review_preparation_uses_git_without_an_objects_directory(repo: Path) -> None:
    spec = write_entry(repo)
    checkpoint(repo)
    result = prepare_review(spec, repo, repo / "review")
    assert result["status"] == "SEALED", result
    assert not (repo / "review/snapshot/objects").exists()
    verified = ProjectPortableStore().verify(repo / "review/snapshot", expected_role="decision")
    assert verified["review_subject"]["subject_mode"] == "complete"
    # Later source edits do not rewrite the reviewed version.
    (repo / "selection.yaml").write_text("next working selection\n")
    assert ProjectPortableStore().verify(repo / "review/snapshot")["content_root"] == result["content_root"]


def test_git_handoff_cites_checkpoint_and_survives_later_record_edits(repo: Path) -> None:
    spec = write_entry(repo)
    checkpoint(repo)
    result = prepare_review(spec, repo, repo / "review")
    assert result["status"] == "SEALED", result
    nodes = NodeRepository(repo / "review/nodes")
    checkpoint(repo)
    export_handoff(result["decision_root"], nodes,
        [{"adapter": ADAPTER, "path": str(repo / "review/snapshot")}], repo / "handoff")
    assert list((repo / "handoff").iterdir()) == [repo / "handoff/handoff.json"]
    (repo / "review/snapshot/manifest.json").write_text("working corruption\n")
    nodes._path(result["decision_root"]).write_text("working corruption\n")
    assert verify_handoff(repo / "handoff")["verified"]


def test_handoff_outside_repo_accepts_explicit_repository(repo: Path, tmp_path_factory) -> None:
    spec = write_entry(repo)
    checkpoint(repo)
    result = prepare_review(spec, repo, repo / "review")
    nodes = NodeRepository(repo / "review/nodes")
    checkpoint(repo)
    destination = tmp_path_factory.mktemp("external-handoff")
    export_handoff(result["decision_root"], nodes,
        [{"adapter": ADAPTER, "path": str(repo / "review/snapshot")}], destination)
    result = apply_operation({"contract_version": REQUEST_CONTRACT, "operation": "verify-handoff",
        "path": str(destination), "repo_root": str(repo)}, nodes)
    assert result["verified"]


def test_large_artifact_reference_is_not_payload_availability(repo: Path) -> None:
    payload = b"large retained payload\n" * 100
    digest = hashlib.sha256(payload).hexdigest()
    pointer = f"version https://git-lfs.github.com/spec/v1\noid sha256:{digest}\nsize {len(payload)}\n"
    (repo / "input.txt").write_text(pointer)
    checkpoint(repo)
    manifest = capture(repo)
    assert ProjectPortableStore().verify(repo / "record")["verified"]
    with pytest.raises(ProvenanceError, match="unavailable"):
        verify_retained_artifact(repo / "retained.bin", sha256=digest, size=len(payload))
    (repo / "retained.bin").write_bytes(payload)
    assert verify_retained_artifact(repo / "retained.bin", sha256=digest, size=len(payload))["verified"]
    assert len(manifest["artifacts"]) == 1
    assert not (repo / "record/objects").exists()


def test_tampered_content_and_missing_commit_fail_only_the_affected_read(repo: Path) -> None:
    capture(repo)
    path = repo / "record/manifest.json"
    manifest = json.loads(path.read_text())
    manifest["storage"]["paths"]["project/outcome/input.txt"] = "absent.txt"
    path.write_text(json.dumps(manifest))
    with pytest.raises(ProvenanceError, match="checkpoint"):
        ProjectPortableStore().verify(repo / "record")
    assert (repo / "input.txt").read_text() == "retained input\n"


def test_generation_restore_is_scoped_and_keeps_evidence_and_spend(repo: Path) -> None:
    start = git(repo, "rev-parse", "HEAD")
    (repo / "input.txt").write_text("new generation implementation\n")
    (repo / "evidence.txt").write_text("failed experiment, spend=3\n")
    checkpoint(repo)
    (repo / "unrelated.txt").write_text("unfinished user work\n")
    git(repo, "restore", "--source=" + start, "--", "input.txt")
    assert (repo / "input.txt").read_text() == "retained input\n"
    assert (repo / "evidence.txt").read_text() == "failed experiment, spend=3\n"
    assert (repo / "unrelated.txt").read_text() == "unfinished user work\n"
