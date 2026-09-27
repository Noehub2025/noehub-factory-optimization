"""Saved adoption and invocation association; no research-quality claims."""
import json
from pathlib import Path

import pytest
import yaml

import frontier_context as context
import frontier_references as refs
from frontier_batch import _write_state


@pytest.fixture
def owner(tmp_path, monkeypatch):
    (tmp_path / ".git").mkdir()
    monkeypatch.setenv("CODEX_SESSION_ID", "owner")
    monkeypatch.setenv("CODEX_THREAD_ID", "owner")
    monkeypatch.delenv("CODEX_AGENT_ID", raising=False)
    selection = tmp_path / "FRONTIER.md"
    selection.write_text("---\ncurrent_state:\n  campaign_status: running\n  primary_batch: B001\n  primary_work: Develop coupled allocation\n---\nExisting owner prose.\n")
    work = tmp_path / "artifacts/frontier/B001/batch.yaml"
    work.parent.mkdir(parents=True)
    work.write_text("batch: B001\ncurrent:\n  status: active\n")
    return tmp_path, selection, work


def pointer(root):
    return root / ".frontier/hook-context/owner.json"


def test_adoption_reads_owner_and_batch_and_proposals_cannot_replace_it(owner):
    root, selection, work = owner
    assert context.register_adopted_work(root, selection)
    binding = json.loads(pointer(root).read_text())
    assert binding["current_state"]["primary_batch"] == "B001"
    assert binding["work"]["path"] == str(work)
    policy = root / refs.DECISION_POLICY_PATH
    policy.parent.mkdir(parents=True)
    policy.write_text("Optional policy")
    proposal = root / "proposal.json"
    proposal.write_text('{"adopted":true,"selected":"other"}')
    assert refs.register_hook_record(root, proposal, "resolver")
    assert json.loads(pointer(root).read_text()) == binding
    with pytest.raises(ValueError, match="current_state"):
        context.register_adopted_work(root, proposal)


def test_normal_batch_write_refreshes_active_work_without_new_decision(owner):
    root, selection, work = owner
    context.register_adopted_work(root, selection)
    previous = json.loads(pointer(root).read_text())
    _write_state(work, {"batch": "B001", "current": {"status": "completed"}})
    binding = json.loads(pointer(root).read_text())
    assert binding["work_status"] == "completed"
    assert binding["work"] != previous["work"]
    other = root / "artifacts/frontier/B002/batch.yaml"
    _write_state(other, {"batch": "B002", "current": {"status": "active"}})
    assert json.loads(pointer(root).read_text()) == binding


def test_pause_source_recheck_and_stale_refresh_cannot_overwrite_new_work(owner):
    root, selection, _ = owner
    context.register_adopted_work(root, selection)
    previous = json.loads(pointer(root).read_text())
    selection.write_text(selection.read_text().replace("running", "paused"))
    assert context.register_adopted_work(root, selection)
    assert not context.register_adopted_work(root, selection, expected_binding=previous)
    assert json.loads(pointer(root).read_text())["current_state"]["campaign_status"] == "paused"


def test_changed_owner_during_snapshot_is_not_published(owner, monkeypatch):
    root, selection, _ = owner
    context.register_adopted_work(root, selection)
    previous = pointer(root).read_bytes()
    original = context._snapshot
    def changed(*args):
        result = original(*args)
        selection.write_text(selection.read_text().replace("running", "paused"))
        return result
    monkeypatch.setattr(context, "_snapshot", changed)
    with pytest.raises(ValueError, match="changed during"):
        context.register_adopted_work(root, selection)
    assert pointer(root).read_bytes() == previous


def test_sessions_and_children_do_not_share_pointers(owner, monkeypatch):
    root, selection, _ = owner
    context.register_adopted_work(root, selection)
    previous = pointer(root).read_bytes()
    assert context.register_adopted_work(root, selection, "second")
    monkeypatch.setenv("CODEX_AGENT_ID", "child")
    assert not context.register_adopted_work(root, selection, "owner")
    assert pointer(root).read_bytes() == previous


def test_escape_duplicate_selection_and_wrong_batch_rejected(owner):
    root, selection, work = owner
    work.write_text("batch: B002\ncurrent: {}")
    with pytest.raises(ValueError, match="does not match"):
        context.register_adopted_work(root, selection)
    selection.write_text("current_state:\n  campaign_status: running\n  campaign_status: paused\n")
    with pytest.raises(ValueError, match="duplicate"):
        context.register_adopted_work(root, selection)
    selection.write_text(yaml.safe_dump({"current_state": {"campaign_status": "running", "work_record": "../outside"}}))
    outside = root.parent / "outside"
    outside.write_text("Other work")
    with pytest.raises(ValueError, match="outside"):
        context.register_adopted_work(root, selection)


def test_return_link_preserves_result_and_original_dispatch_after_switch(owner):
    root, selection, _ = owner
    context.register_adopted_work(root, selection)
    directory = pointer(root).parent
    call = directory / "owner-call-call1.json"
    call.write_text(json.dumps({"session_id": "owner", "tool_use_id": "call1",
                                "adopted_work": json.loads(pointer(root).read_text())}))
    result = root / "result.json"
    result.write_text('{"finding":"useful unexplained outcome"}')
    selection.write_text(selection.read_text().replace("running", "paused"))
    context.register_adopted_work(root, selection)
    linked = context.bind_dispatch_return(root, result, "call1")
    assert linked["finding"] == "useful unexplained outcome"
    assert linked["dispatch_reference"]["dispatch_status"] == "attempted_dispatch"
    assert json.loads(call.read_text())["adopted_work"]["current_state"]["campaign_status"] == "running"
    with pytest.raises(OSError):
        context.bind_dispatch_return(root, result, "no-event")


def test_adopt_cli_writes_only_context(owner, monkeypatch):
    root, selection, work = owner
    before = (selection.read_bytes(), work.read_bytes())
    monkeypatch.setattr("sys.argv", ["frontier_references.py", "adopt-work", "--repo", str(root), "--path", str(selection)])
    assert refs.main() == 0
    assert before == (selection.read_bytes(), work.read_bytes())


@pytest.mark.parametrize("invalid", [None, [], {"kind": "adopted_work", "work": "bad"},
                                    {"kind": "adopted_work", "work": {}, "selection": []}])
def test_corrupt_optional_pointer_cannot_fail_a_successful_batch_write(owner, invalid):
    root, selection, work = owner
    context.register_adopted_work(root, selection)
    pointer(root).write_text(json.dumps(invalid))
    updated = {"batch": "B001", "current": {"status": "completed"}}
    _write_state(work, updated)
    assert yaml.safe_load(work.read_text()) == updated


@pytest.mark.parametrize("changed", [{"session_id": "other"}, {"tool_use_id": "call2"},
                                      {"attempt": "unrelated"}, {"status": "completed"}])
def test_return_rejects_mismatched_post_without_mutating_result(owner, changed):
    root, selection, _ = owner
    context.register_adopted_work(root, selection)
    attempt = pointer(root).parent / "owner-call-call1.json"
    attempt.write_text(json.dumps({"session_id": "owner", "tool_use_id": "call1"}))
    post = {"session_id": "owner", "tool_use_id": "call1", "attempt": str(attempt),
            "status": "confirmed_dispatch", **changed}
    attempt.with_name(attempt.stem + "-post.json").write_text(json.dumps(post))
    result = root / "result.json"
    result.write_text('{"finding":"original"}')
    with pytest.raises(ValueError, match="response does not match"):
        context.bind_dispatch_return(root, result, "call1")
    assert result.read_text() == '{"finding":"original"}'
