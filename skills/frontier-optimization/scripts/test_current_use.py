"""Known-correction continuity and real saved-use checks, not semantic quality."""
import hashlib
import json
from pathlib import Path
import subprocess

import pytest

from current_use import check_current_use, inspect_current_use
import frontier_context as context
import frontier_references as refs


def write(path, value):
    path.write_text(json.dumps(value))


@pytest.fixture
def case(tmp_path):
    (tmp_path / "task.md").write_text("Keep the existing architecture; do not discover alternatives.")
    (tmp_path / "other.md").write_text("Complete independent useful work.")
    (tmp_path / "finding.md").write_text("The owner confirmed that this exclusion is unsupported for the open objective.")
    owner = {"feedback_not_due": "No pending feedback.",
             "current_state": {"campaign_status": "running", "work_record": "task.md"},
             "current_use_corrections": [{"id": "narrowing", "finding": "finding.md",
                "effect": "repair", "affected_sources": ["task.md"], "status": "open"}]}
    write(tmp_path / "owner.json", owner)
    return tmp_path, owner


def resolve(root, owner):
    (root / "task.md").write_text("Investigate mechanisms beyond the incumbent before selecting the next commitment.")
    (root / "adoption.md").write_text("The owner adopts this task to replace the unsupported restriction.")
    item = owner["current_use_corrections"][0]
    item["status"] = "resolved"
    item["resolution"] = {"reason": "Remove incumbent-only admission.", "evidence": "adoption.md",
        "replacements": [{"path": "task.md", "sha256": hashlib.sha256((root / "task.md").read_bytes()).hexdigest()}]}
    write(root / "owner.json", owner)


def test_affected_use_held_but_independent_action_available(case):
    root, _ = case
    with pytest.raises(ValueError, match="requires owner correction"):
        check_current_use(root, "owner.json", ["task.md"])
    assert check_current_use(root, "owner.json", ["other.md"])["status"] == "current"


def test_lost_field_and_context_refresh_do_not_erase_finding(case, monkeypatch):
    root, owner = case
    monkeypatch.delenv("CODEX_AGENT_ID", raising=False)
    context.register_adopted_work(root, root / "owner.json", "test")
    owner.pop("current_use_corrections")
    write(root / "owner.json", owner)
    context.register_adopted_work(root, root / "owner.json", "test")
    binding = json.loads((root / ".frontier/hook-context/test.json").read_text())
    assert binding["current_use"]["blocked_ids"] == ["narrowing"]
    with pytest.raises(ValueError, match="requires owner correction"):
        check_current_use(root, "owner.json", ["task.md"])
    assert check_current_use(root, "owner.json", ["other.md"])["status"] == "current"


def test_explicit_owner_transfer_carries_known_association(case):
    root, owner = case
    inspect_current_use(root, "owner.json")
    transferred = {"current_use_predecessor": "owner.json"}
    write(root / "successor.json", transferred)
    with pytest.raises(ValueError, match="requires owner correction"):
        check_current_use(root, "successor.json", ["task.md"])
    transferred.pop("current_use_predecessor")
    write(root / "successor.json", transferred)
    with pytest.raises(ValueError, match="requires owner correction"):
        check_current_use(root, "successor.json", ["task.md"])


def test_fake_resolution_and_scope_relabel_cannot_clear(case):
    root, owner = case
    inspect_current_use(root, "owner.json")
    item = owner["current_use_corrections"][0]
    item["effect"] = "advisory"
    write(root / "owner.json", owner)
    with pytest.raises(ValueError, match="cannot be dropped or relabeled"):
        inspect_current_use(root, "owner.json")
    item["effect"] = "repair"
    item["status"] = "resolved"
    item["resolution"] = {"reason": "Addressed.", "evidence": "finding.md", "replacements": [
        {"path": "task.md", "sha256": hashlib.sha256((root / "task.md").read_bytes()).hexdigest()}]}
    write(root / "owner.json", owner)
    with pytest.raises(ValueError, match="did not change"):
        inspect_current_use(root, "owner.json")


def test_resolution_checks_real_bytes_and_queued_snapshot(case):
    root, owner = case
    queued = inspect_current_use(root, "owner.json", ["task.md"])
    resolve(root, owner)
    with pytest.raises(ValueError, match="stale"):
        check_current_use(root, "owner.json", ["task.md"], queued)
    current = check_current_use(root, "owner.json", ["task.md"])["current_use"]
    assert check_current_use(root, "owner.json", ["task.md"], current)["current_use"] == current
    assert current["blocked_ids"] == []
    assert current["correction_ids"] == ["narrowing"]
    (root / "other.md").write_text("Unrelated work changed.")
    assert check_current_use(root, "owner.json", ["task.md"], current)["status"] == "current"
    (root / "task.md").write_text("Keep the existing architecture; do not discover alternatives.")
    with pytest.raises(ValueError, match="requires owner correction"):
        check_current_use(root, "owner.json", ["task.md"])


def test_resolved_cleanup_and_ordinary_progress_do_not_hold_other_work(case):
    root, owner = case
    inspect_current_use(root, "owner.json")
    resolve(root, owner)
    check_current_use(root, "owner.json", ["task.md"])
    (root / "task.md").write_text("Ordinary progress after the adopted correction.")
    snapshot = check_current_use(root, "owner.json", ["other.md"])["current_use"]
    assert str(root / "task.md") not in {item["path"] for item in snapshot["files"]}
    (root / "task.md").unlink()
    assert check_current_use(root, "owner.json", ["other.md"])["status"] == "current"
    (root / "task.md").write_text("Ordinary progress after the adopted correction.")
    owner.pop("current_use_corrections")
    write(root / "owner.json", owner)
    assert check_current_use(root, "owner.json", ["task.md"])["status"] == "current"


def test_native_owner_rename_without_predecessor_cannot_erase_association(case, monkeypatch):
    root, owner = case
    monkeypatch.delenv("CODEX_AGENT_ID", raising=False)
    context.register_adopted_work(root, root / "owner.json", "rename")
    (root / "owner.json").unlink()
    write(root / "new-owner.json", {"current_state": owner["current_state"]})
    context.register_adopted_work(root, root / "new-owner.json", "rename")
    with pytest.raises(ValueError, match="requires owner correction"):
        check_current_use(root, "new-owner.json", ["task.md"])


def test_resolved_successor_can_be_checked_repeatedly(case):
    root, owner = case
    inspect_current_use(root, "owner.json")
    owner["current_use_predecessor"] = "owner.json"
    write(root / "successor.json", owner)
    inspect_current_use(root, "successor.json")
    resolve(root, owner)
    write(root / "successor.json", owner)
    for _ in range(2):
        assert check_current_use(root, "successor.json", ["task.md"])["status"] == "current"


def test_advisory_and_inapplicable_owner_judgments_have_distinct_controls(case):
    root, owner = case
    item = owner["current_use_corrections"][0]
    item["effect"] = "advisory"
    write(root / "owner.json", owner)
    assert check_current_use(root, "owner.json", ["task.md"])["status"] == "current"
    item["status"] = "inapplicable"
    item["resolution"] = {"reason": "The authoritative user scope changed.", "evidence": "finding.md", "replacements": [
        {"path": "task.md", "sha256": hashlib.sha256((root / "task.md").read_bytes()).hexdigest()}]}
    write(root / "owner.json", owner)
    assert check_current_use(root, "owner.json", ["task.md"])["status"] == "current"


def test_new_unaffected_owner_needs_no_extra_record(tmp_path):
    write(tmp_path / "owner.json", {"task": "Answer the named focused question."})
    assert check_current_use(tmp_path, "owner.json")["current_use"] is None
    assert not (tmp_path / ".frontier").exists()


def test_resolver_does_not_reuse_old_head_over_uncommitted_correction(case):
    root, owner = case
    owner.pop("current_use_corrections")
    write(root / "owner.json", owner)
    write(root / "evidence.json", {"observation": "unchanged"})
    def git(*args):
        return subprocess.check_output(["git", "-C", str(root), *args], stderr=subprocess.PIPE).decode().strip()
    git("init")
    git("config", "user.email", "test@example.invalid")
    git("config", "user.name", "Test")
    git("add", ".")
    git("commit", "-m", "initial")
    prepared = refs.prepare_resolver(root, "HEAD", "evidence.json", owner_source="owner.json")
    result = refs.bind_resolution(root, prepared, {"row": 11, "policy_disposition": {"status": "addressed", "reason": "continue"}})
    write(root / "prior.json", result)
    git("add", "prior.json")
    git("commit", "-m", "prior")
    owner["current_use_corrections"] = [{"id": "narrowing", "finding": "finding.md", "effect": "repair",
        "affected_sources": ["task.md"], "status": "open"}]
    write(root / "owner.json", owner)
    with pytest.raises(ValueError, match="current-use correction changed"):
        refs.bind_resolution(root, prepared, {"row": 11})
    fresh = refs.prepare_resolver(root, "HEAD", "evidence.json", ["prior.json"], owner_source="owner.json")
    assert "reuse_resolution" not in fresh
    assert fresh["current_use"]["blocked_ids"] == ["narrowing"]
    with pytest.raises(ValueError, match="cannot replace"):
        refs.bind_resolution(root, fresh, {"row": 11, "current_use": {"blocked_ids": []}})
    resolve(root, owner)
    assert check_current_use(root, "owner.json", ["task.md"])["status"] == "current"


def test_cli_checks_actual_task_without_native_registration(case):
    root, owner = case
    import sys
    command = [sys.executable, str(Path(refs.__file__)), "check-current-use", "--repo", str(root),
               "--owner-source", "owner.json", "--source", "task.md"]
    first = subprocess.run(command, capture_output=True, text=True)
    assert first.returncode == 2 and "requires owner correction" in first.stdout
    resolve(root, owner)
    second = subprocess.run(command, capture_output=True, text=True)
    assert second.returncode == 0
    assert json.loads(second.stdout)["current_use"]["blocked_ids"] == []
