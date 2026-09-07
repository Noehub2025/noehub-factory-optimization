"""Current reference preparation, propagation and retained-result reuse."""

import json
import subprocess
from pathlib import Path

import pytest

import frontier_references as refs


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], stderr=subprocess.PIPE).decode().strip()


@pytest.fixture
def repo(tmp_path):
    git(tmp_path, "init")
    git(tmp_path, "config", "user.email", "test@example.invalid")
    git(tmp_path, "config", "user.name", "Reference Test")
    return tmp_path


def save(root, files):
    for path, text in files.items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
    git(root, "add", "--", *files)
    git(root, "commit", "-m", "test checkpoint")
    return git(root, "rev-parse", "HEAD")


def test_resolver_uses_saved_bytes_and_repairs_derived_binding(repo):
    commit = save(repo, {"evidence.json": '{"goal":"改善","result":1}'})
    prepared = refs.prepare_resolver(repo, "HEAD", "evidence.json")
    (repo / "evidence.json").write_text('{"result":999}')
    body = {"row": 11, "exact_action": "test a new route", "evidence_state_identity": "mistyped"}
    result = refs.bind_resolution(repo, {**prepared, "evidence_state_identity": "also mistyped"}, body)
    assert result["evidence_state_identity"] == prepared["evidence_state_identity"]
    assert result["evidence_source"] == {"commit": commit, "path": "evidence.json"}
    assert result["exact_action"] == body["exact_action"]


def test_same_facts_reuse_result_after_format_location_and_commit_change(repo):
    save(repo, {"evidence.json": '{"a":1,"b":[2,3]}'})
    prepared = refs.prepare_resolver(repo, "HEAD", "evidence.json")
    result = refs.bind_resolution(repo, prepared, {"row": 11, "exact_action": "continue"})
    result["evidence_state_identity"] = "old transcription error"
    save(repo, {"resolution.json": json.dumps(result), "moved.json": '{\n "b": [2, 3], "a": 1\n}', "unrelated.txt": "note"})
    reused = refs.prepare_resolver(repo, "HEAD", "moved.json", ["resolution.json"])
    assert reused["evidence_state_identity"] == prepared["evidence_state_identity"]
    assert reused["reuse_resolution"]["path"] == "resolution.json"
    with pytest.raises(refs.ReferenceError, match="reuse"):
        refs.bind_resolution(repo, reused, {"row": 7})


def test_changed_facts_do_not_reuse_or_rebind_old_judgment(repo):
    save(repo, {"evidence.json": '{"result":1}'})
    old = refs.prepare_resolver(repo, "HEAD", "evidence.json")
    result = refs.bind_resolution(repo, old, {"row": 11})
    save(repo, {"resolution.json": json.dumps(result), "evidence.json": '{"result":2}'})
    new = refs.prepare_resolver(repo, "HEAD", "evidence.json", ["resolution.json"])
    assert "reuse_resolution" not in new
    with pytest.raises(refs.ReferenceError, match="different decision facts"):
        refs.bind_resolution(repo, new, result)


def test_retained_resolution_identity_is_read_without_rewrite(repo):
    save(repo, {"evidence.json": '{"result":1}'})
    identity = refs.prepare_resolver(repo, "HEAD", "evidence.json")["evidence_state_identity"]
    historical = json.dumps({"identity_reproduction": {"evidence_state_identity": identity}, "resolution": {"first_applicable_row": 11}})
    save(repo, {"historical.yaml": historical})
    result = refs.prepare_resolver(repo, "HEAD", "evidence.json", ["historical.yaml"])
    assert result["reuse_resolution"]["path"] == "historical.yaml"
    assert (repo / "historical.yaml").read_text() == historical


@pytest.mark.parametrize("content", ['{"a":1,"a":2}', '{"a":NaN}', '[]', '{'])
def test_invalid_preparation_has_no_output_or_decision(repo, content):
    save(repo, {"evidence.json": content})
    before = git(repo, "status", "--porcelain")
    with pytest.raises(ValueError):
        refs.prepare_resolver(repo, "HEAD", "evidence.json")
    assert git(repo, "status", "--porcelain") == before
    assert not (repo / "resolution.json").exists()


def design_files():
    return {
        "work/W001/WORK.md": "---\nwork_id: W001\nplan_revision: 1\n---\n# Design\n\n## Design map\n\n| Concern | Authoritative pointer |\n|---|---|\n| Verification | work/W001/design/verification.md |\n\n## Progress\nDraft\n",
        "work/W001/design/verification.md": "# Verification\n\n## First slice\nDeliver an observation.\n\n## Second slice\nUse the first observation.\n",
        "work/W001/design/traceability.yaml": "work_id: W001\nplan_revision: 1\nslices:\n  first:\n    verification_pointer: work/W001/design/verification.md#first-slice\n    prerequisites: []\n    required_design_inputs: []\n  second:\n    verification_pointer: work/W001/design/verification.md#second-slice\n    prerequisites: [first]\n    required_design_inputs: [work/W001/design/verification.md#first-slice]\n",
    }


def test_design_requires_no_hashes_or_self_commit_and_keeps_stable_scope(repo):
    files = design_files()
    original = save(repo, files)
    first = refs.prepare_design(repo, "HEAD", "work/W001/WORK.md", ["first", "second"])
    changed = files["work/W001/design/verification.md"].replace("Deliver an observation.", "Deliver a more useful observation.")
    latest = save(repo, {"work/W001/design/verification.md": changed})
    second = refs.prepare_design(repo, "HEAD", "work/W001/WORK.md", ["first", "second"])
    assert first["subject"]["commit"] == original
    assert second["subject"]["commit"] == latest
    assert first["delivery_scope"] == second["delivery_scope"]
    assert set(second["subject"]["paths"]) == set(files)
    assert (repo / "work/W001/WORK.md").read_text() == files["work/W001/WORK.md"]
    assert "sha256" not in json.dumps(second)
    for commit in (original, latest):
        assert commit not in (repo / "work/W001/WORK.md").read_text()


def test_design_checks_scope_and_saved_pointer(repo):
    files = design_files()
    save(repo, files)
    with pytest.raises(refs.ReferenceError, match="omits prerequisite"):
        refs.prepare_design(repo, "HEAD", "work/W001/WORK.md", ["second"])
    with pytest.raises(refs.ReferenceError, match="unknown"):
        refs.prepare_design(repo, "HEAD", "work/W001/WORK.md", ["missing"])
    save(repo, {"work/W001/design/verification.md": "# Verification\n## Renamed\n"})
    with pytest.raises(refs.ReferenceError, match="missing or ambiguous"):
        refs.prepare_design(repo, "HEAD", "work/W001/WORK.md")
    with pytest.raises(refs.ReferenceError):
        refs.reference(repo, "HEAD", "missing.json")


def test_cli_writes_existing_assignment_and_result_without_transcription(repo, monkeypatch):
    save(repo, {"evidence.json": '{"result":1}'})
    assignment = repo / "assignment.json"
    assignment.write_text('{"purpose":"choose next observation","limits":{"calls":0}}')
    monkeypatch.setattr("sys.argv", ["frontier_references.py", "resolver", "--repo", str(repo), "--path", "evidence.json", "--output", str(assignment)])
    assert refs.main() == 0
    prepared = json.loads(assignment.read_text())
    assert prepared["purpose"] == "choose next observation"
    assert prepared["limits"] == {"calls": 0}
    draft = repo / "resolution.json"
    draft.write_text('{"row":11,"exact_action":"continue"}')
    monkeypatch.setattr("sys.argv", ["frontier_references.py", "bind-resolution", "--repo", str(repo), "--path", "assignment.json", "--result", str(draft), "--output", str(draft)])
    assert refs.main() == 0
    bound = json.loads(draft.read_text())
    assert bound["evidence_source"] == prepared["evidence_source"]
    assert bound["evidence_state_identity"] == prepared["evidence_state_identity"]
    assert bound["exact_action"] == "continue"
