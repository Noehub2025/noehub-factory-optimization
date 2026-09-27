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
    policy_file(repo)
    assignment = repo / "assignment.json"
    assignment.write_text('{"purpose":"choose next observation","limits":{"calls":0}}')
    monkeypatch.setattr("sys.argv", ["frontier_references.py", "resolver", "--repo", str(repo), "--path", "evidence.json", "--output", str(assignment)])
    assert refs.main() == 0
    prepared = json.loads(assignment.read_text())
    assert prepared["purpose"] == "choose next observation"
    assert prepared["limits"] == {"calls": 0}
    assert prepared["decision_policy"]["status"] == "provided"
    draft = repo / "resolution.json"
    draft.write_text('{"row":11,"exact_action":"continue"}')
    monkeypatch.setattr("sys.argv", ["frontier_references.py", "bind-resolution", "--repo", str(repo), "--path", "assignment.json", "--result", str(draft), "--output", str(draft)])
    assert refs.main() == 0
    bound = json.loads(draft.read_text())
    assert bound["evidence_source"] == prepared["evidence_source"]
    assert bound["evidence_state_identity"] == prepared["evidence_state_identity"]
    assert bound["exact_action"] == "continue"
    assert bound["policy_coverage"]["judgment_status"] == "not_reported"


def policy_file(repo, text="Use the same investment judgment; do not require benefit proof."):
    path = repo / refs.DECISION_POLICY_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_cli_keeps_proposals_separate_from_adopted_work(repo, monkeypatch):
    save(repo, {"evidence.json": '{"result":1}'})
    policy_file(repo)
    monkeypatch.setenv("CODEX_SESSION_ID", "current-owner")
    monkeypatch.setenv("CODEX_THREAD_ID", "current-owner")
    monkeypatch.delenv("CODEX_AGENT_ID", raising=False)
    assignment = repo / "assignment.json"
    monkeypatch.setattr("sys.argv", ["frontier_references.py", "resolver", "--repo", str(repo),
                                    "--path", "evidence.json", "--output", str(assignment)])
    assert refs.main() == 0
    pointer = repo / ".frontier/hook-context/current-owner-proposal.json"
    assert not (pointer.parent / "current-owner.json").exists()
    assert json.loads(pointer.read_text())["record"] == str(assignment.resolve())
    result = repo / "result.json"
    result.write_text('{"row":11}')
    monkeypatch.setattr("sys.argv", ["frontier_references.py", "bind-resolution", "--repo", str(repo),
                                    "--path", "assignment.json", "--result", str(result), "--output", str(result)])
    assert refs.main() == 0
    assert json.loads(pointer.read_text())["record"] == str(result.resolve())
    assert json.loads(pointer.read_text())["phase"] == "bind-resolution"
    assert json.loads(result.read_text())["policy_coverage"]["judgment_status"] == "not_reported"
    before = pointer.read_bytes()
    monkeypatch.setenv("CODEX_THREAD_ID", "child-task")
    assert not refs.register_hook_record(repo, assignment, "resolver")
    assert pointer.read_bytes() == before
    monkeypatch.setenv("CODEX_THREAD_ID", "another-owner")
    monkeypatch.setenv("CODEX_SESSION_ID", "another-owner")
    assert refs.register_hook_record(repo, assignment, "resolver")
    assert pointer.read_bytes() == before


def test_native_registration_failure_does_not_discard_the_decision(repo, monkeypatch):
    save(repo, {"evidence.json": '{"result":1}'})
    policy_file(repo)
    assignment = repo / "assignment.json"
    def unavailable(*args, **kwargs):
        raise OSError("context directory unavailable")
    monkeypatch.setattr(refs, "register_hook_record", unavailable)
    monkeypatch.setattr("sys.argv", ["frontier_references.py", "resolver", "--repo", str(repo),
                                    "--path", "evidence.json", "--output", str(assignment)])
    assert refs.main() == 0
    assert json.loads(assignment.read_text())["evidence_state_identity"]


def test_optional_policy_is_supplied_to_existing_resolver_without_claiming_handling(repo):
    save(repo, {"evidence.json": '{"result":1}'})
    absent = refs.prepare_resolver(repo, "HEAD", "evidence.json")
    policy_file(repo)
    supplied = refs.prepare_resolver(repo, "HEAD", "evidence.json")
    assert supplied["evidence_state_identity"] == absent["evidence_state_identity"]
    assert supplied["decision_policy"]["status"] == "provided"
    assert "same investment judgment" in supplied["decision_policy"]["text"]
    result = refs.bind_resolution(repo, supplied, {"row": 11})
    assert result["policy_coverage"]["policy_status"] == "current"
    assert result["policy_coverage"]["judgment_status"] == "not_reported"
    assert "text" not in result["decision_policy"]


@pytest.mark.parametrize("status", ["addressed", "not_addressed", "unavailable"])
def test_coverage_records_explicit_handling_without_a_second_judgment(repo, status):
    save(repo, {"evidence.json": '{"result":1}'})
    policy_file(repo)
    prepared = refs.prepare_resolver(repo, "HEAD", "evidence.json")
    disposition = {"status": status, "reason": "Compared direct design with diagnosis in the existing rationale."}
    body = {"row": 11, "exact_action": "develop the whole mechanism", "policy_disposition": disposition,
            "policy_coverage": {"policy_status": "invented_pass"}}
    result = refs.bind_resolution(repo, prepared, body)
    assert result["policy_disposition"] == disposition
    assert result["policy_coverage"]["judgment_status"] == status
    assert result["policy_coverage"]["policy_status"] == "current"
    assert result["exact_action"] == body["exact_action"]


@pytest.mark.parametrize("disposition", [None, "addressed", {"status": "addressed"},
                                         {"status": "addressed", "reason": " "},
                                         {"status": "passed", "reason": "All good"}])
def test_missing_or_incomplete_optional_handling_is_uncovered_not_blocked(repo, disposition):
    save(repo, {"evidence.json": '{"result":1}'})
    policy_file(repo)
    prepared = refs.prepare_resolver(repo, "HEAD", "evidence.json")
    result = refs.bind_resolution(repo, prepared, {"row": 11, "policy_disposition": disposition})
    assert result["row"] == 11
    assert result["policy_coverage"]["judgment_status"] == "not_reported"


def test_changed_policy_preserves_reported_handling_but_does_not_claim_current_coverage(repo):
    save(repo, {"evidence.json": '{"result":1}'})
    path = policy_file(repo)
    prepared = refs.prepare_resolver(repo, "HEAD", "evidence.json")
    path.write_text("Changed guidance", encoding="utf-8")
    result = refs.bind_resolution(repo, prepared, {"row": 11, "policy_disposition": {
        "status": "addressed", "reason": "Used the supplied guidance in the original comparison."}})
    assert result["policy_coverage"]["policy_status"] == "changed"
    assert result["policy_coverage"]["judgment_status"] == "addressed"
    assert result["decision_policy"]["sha256"] == prepared["decision_policy"]["sha256"]


def test_missing_unreadable_and_old_policy_context_do_not_block_existing_work(repo):
    save(repo, {"evidence.json": '{"result":1}'})
    absent = refs.prepare_resolver(repo, "HEAD", "evidence.json")
    old = {key: value for key, value in absent.items() if key != "decision_policy"}
    for prepared in (absent, old):
        result = refs.bind_resolution(repo, prepared, {"row": 11})
        assert result["policy_coverage"] == {"policy_status": "not_provided", "judgment_status": "not_reported"}
    path = policy_file(repo)
    path.write_bytes(b"\xff")
    unavailable = refs.prepare_resolver(repo, "HEAD", "evidence.json")
    result = refs.bind_resolution(repo, unavailable, {"row": 11})
    assert result["policy_coverage"]["policy_status"] == "unavailable"
    assert result["row"] == 11


@pytest.mark.parametrize("change_policy", [False, True])
def test_prior_judgment_reuse_reports_actual_original_coverage_without_reopening(repo, change_policy):
    save(repo, {"evidence.json": '{"result":1}'})
    path = policy_file(repo)
    prepared = refs.prepare_resolver(repo, "HEAD", "evidence.json")
    result = refs.bind_resolution(repo, prepared, {"row": 11, "policy_disposition": {
        "status": "addressed", "reason": "The existing comparison applied the supplied policy."}})
    save(repo, {"resolution.json": json.dumps(result)})
    if change_policy:
        path.write_text("Updated optional guidance", encoding="utf-8")
    reused = refs.prepare_resolver(repo, "HEAD", "evidence.json", ["resolution.json"])
    assert reused["reuse_resolution"]["path"] == "resolution.json"
    assert reused["reused_policy_coverage"]["policy_status"] == ("changed" if change_policy else "current")
    assert reused["reused_policy_coverage"]["judgment_status"] == "addressed"
    assert json.loads((repo / "resolution.json").read_text()) == result


def test_rebinding_an_existing_judgment_cannot_refresh_its_policy_coverage(repo):
    save(repo, {"evidence.json": '{"result":1}'})
    path = policy_file(repo)
    first = refs.prepare_resolver(repo, "HEAD", "evidence.json")
    result = refs.bind_resolution(repo, first, {"row": 11, "policy_disposition": {
        "status": "addressed", "reason": "Applied the original supplied guidance."}})
    path.write_text("Different current guidance", encoding="utf-8")
    current = refs.prepare_resolver(repo, "HEAD", "evidence.json")
    rebound = refs.bind_resolution(repo, current, result)
    assert rebound["decision_policy"] == result["decision_policy"]
    assert rebound["policy_coverage"]["policy_status"] == "changed"
    assert rebound["policy_coverage"]["judgment_status"] == "addressed"


def test_cli_reusing_assignment_clears_prior_policy_coverage_when_facts_change(repo, monkeypatch):
    save(repo, {"evidence.json": '{"result":1}'})
    policy_file(repo)
    prepared = refs.prepare_resolver(repo, "HEAD", "evidence.json")
    result = refs.bind_resolution(repo, prepared, {"row": 11, "policy_disposition": {
        "status": "addressed", "reason": "Applied the supplied policy in this judgment."}})
    save(repo, {"resolution.json": json.dumps(result)})
    assignment = repo / "assignment.json"
    command = ["frontier_references.py", "resolver", "--repo", str(repo), "--path", "evidence.json",
               "--prior", "resolution.json", "--output", str(assignment)]
    monkeypatch.setattr("sys.argv", command)
    assert refs.main() == 0
    reused = json.loads(assignment.read_text())
    assert reused["reused_policy_coverage"]["judgment_status"] == "addressed"
    assert "reuse_resolution" in reused
    save(repo, {"evidence.json": '{"result":2}'})
    assert refs.main() == 0
    fresh = json.loads(assignment.read_text())
    assert "reuse_resolution" not in fresh
    assert "reused_policy_coverage" not in fresh
    assert fresh["evidence_state_identity"] != reused["evidence_state_identity"]
    assert fresh["decision_policy"]["status"] == "provided"
