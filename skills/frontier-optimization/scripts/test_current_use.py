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


def adoption_request(root, owner):
    from copy import deepcopy
    correction = deepcopy(owner["current_use_corrections"][0])
    correction["status"] = "resolved"
    (root / "adoption.md").write_text("The owner adopts the correction on its original objective.")
    correction["resolution"] = {"reason": "Remove the unsupported restriction.", "evidence": "adoption.md"}
    return {"corrections": [correction], "replacements": [{"path": "task.md", "contents": "Explore the original objective within actual limits."}]}


def test_integrated_adoption_captures_original_without_prior_manual_enrollment(case):
    import current_use as use
    root, owner = case
    before = hashlib.sha256((root / "task.md").read_bytes()).hexdigest()
    request = adoption_request(root, owner)
    owner.pop("current_use_corrections")
    write(root / "owner.json", owner)
    result = use.adopt_current_work(root, "owner.json", sources=["task.md"], **request)
    record = use._read_receipt(use._receipt(root, "owner.json"))["narrowing"]
    assert record["before"] == {"task.md": before}
    assert record["current"]["task.md"] != before
    assert result["current_use"]["checked_sources"] == [str(root / "task.md")]
    assert "pending" not in use._state(use._receipt(root, "owner.json"))
    assert use.adopt_current_work(root, "owner.json", sources=["task.md"])["status"] == "current"


@pytest.mark.parametrize("failure", ["retention", "task", "owner", "final_receipt"])
def test_integrated_adoption_retries_partial_failure_without_new_edit(case, monkeypatch, failure):
    import current_use as use
    root, owner = case
    original = (root / "task.md").read_bytes()
    request = adoption_request(root, owner)
    publish, replace = context._publish, use._replace_bytes
    def failed_publish(path, value):
        if (failure == "retention" and "pending" in value) or (failure == "final_receipt" and "records" in value and "pending" not in value):
            raise OSError("injected receipt failure")
        return publish(path, value)
    def failed_replace(path, raw):
        if path.name == ("task.md" if failure == "task" else "owner.json") and failure in {"task", "owner"}:
            raise OSError("injected write failure")
        return replace(path, raw)
    with monkeypatch.context() as patch:
        patch.setattr(context, "_publish", failed_publish)
        patch.setattr(use, "_replace_bytes", failed_replace)
        with pytest.raises(OSError, match="injected"):
            use.adopt_current_work(root, "owner.json", **request)
    if failure == "retention":
        assert (root / "task.md").read_bytes() == original
        resumed = use.adopt_current_work(root, "owner.json", **request)
    else:
        assert use._state(use._receipt(root, "owner.json"))["pending"]
        with pytest.raises(ValueError, match="requires owner correction"):
            use.check_current_use(root, "owner.json", ["task.md"])
        assert use.check_current_use(root, "owner.json", ["other.md"])["status"] == "current"
        resumed = use.adopt_current_work(root, "owner.json")
    assert resumed["status"] == "current"
    record = use._read_receipt(use._receipt(root, "owner.json"))["narrowing"]
    assert record["before"]["task.md"] == hashlib.sha256(original).hexdigest()
    assert "pending" not in use._state(use._receipt(root, "owner.json"))


def test_changed_request_cannot_replace_pending_adoption(case, monkeypatch):
    import current_use as use
    root, owner = case
    request = adoption_request(root, owner)
    with monkeypatch.context() as patch:
        patch.setattr(use, "_replace_bytes", lambda *args: (_ for _ in ()).throw(OSError("stop")))
        with pytest.raises(OSError):
            use.adopt_current_work(root, "owner.json", **request)
    request["replacements"][0]["contents"] = "A different unadopted request"
    with pytest.raises(ValueError, match="different request"):
        use.adopt_current_work(root, "owner.json", **request)


@pytest.mark.parametrize("status", ["open", "resolved"])
def test_same_owner_successor_and_dependency_preserve_finding_scope(case, status):
    root, owner = case
    inspect_current_use(root, "owner.json")
    obsolete = (root / "task.md").read_text()
    if status == "resolved":
        resolve(root, owner)
        check_current_use(root, "owner.json", ["task.md"])
    (root / "copy.md").write_text(obsolete)
    (root / "consumer.md").write_text("Consume copied task for the next action.")
    owner["current_use_relations"] = [{"source": "task.md", "target": "copy.md", "kind": "successor"},
                                       {"source": "copy.md", "target": "consumer.md", "kind": "dependency"}]
    write(root / "owner.json", owner)
    for path in ["copy.md", "consumer.md"]:
        with pytest.raises(ValueError, match="requires owner correction"):
            check_current_use(root, "owner.json", [path])
    assert check_current_use(root, "owner.json", ["other.md"])["status"] == "current"
    owner.pop("current_use_relations")
    write(root / "owner.json", owner)
    with pytest.raises(ValueError, match="requires owner correction"):
        check_current_use(root, "owner.json", ["consumer.md"])


def test_renamed_task_can_be_corrected_without_rewriting_historical_scope(case):
    import current_use as use
    root, owner = case
    inspect_current_use(root, "owner.json")
    (root / "task.md").rename(root / "renamed.md")
    owner["current_use_relations"] = [{"source": "task.md", "target": "renamed.md", "kind": "successor"}]
    write(root / "owner.json", owner)
    with pytest.raises(ValueError, match="requires owner correction"):
        check_current_use(root, "owner.json", ["renamed.md"])
    request = adoption_request(root, owner)
    request["replacements"][0]["path"] = "renamed.md"
    request["relations"] = owner["current_use_relations"]
    result = use.adopt_current_work(root, "owner.json", sources=["renamed.md"], **request)
    assert result["status"] == "current"
    record = use._read_receipt(use._receipt(root, "owner.json"))["narrowing"]
    assert record["core"]["affected_sources"] == ["task.md"]
    assert "task.md" in record["before"]


def test_unrelated_prepared_scope_cannot_clear_affected_request(case):
    root, owner = case
    inspect_current_use(root, "owner.json")
    resolve(root, owner)
    unrelated = check_current_use(root, "owner.json", ["other.md"])["current_use"]
    with pytest.raises(ValueError, match="stale"):
        check_current_use(root, "owner.json", ["task.md"], unrelated)


@pytest.mark.parametrize("replacement", ["obsolete", "new_correction"])
def test_publication_change_cannot_emit_success_with_unvalidated_task(case, monkeypatch, replacement):
    root, owner = case
    obsolete = (root / "task.md").read_text()
    inspect_current_use(root, "owner.json")
    resolve(root, owner)
    publish = context._publish
    def changed(path, value):
        publish(path, value)
        (root / "task.md").write_text(obsolete if replacement == "obsolete" else "Different unvalidated correction")
    with monkeypatch.context() as patch:
        patch.setattr(context, "_publish", changed)
        with pytest.raises(ValueError, match="dependency changed"):
            check_current_use(root, "owner.json", ["task.md"])


def test_final_snapshot_failure_retains_pending_recovery(case, monkeypatch):
    import current_use as use
    root, owner = case
    request = adoption_request(root, owner)
    publish = context._publish
    def changed(path, value):
        publish(path, value)
        if "records" in value and "pending" not in value:
            (root / "task.md").write_text("Interleaved unvalidated edit")
    with monkeypatch.context() as patch:
        patch.setattr(context, "_publish", changed)
        with pytest.raises(ValueError, match="dependency changed"):
            use.adopt_current_work(root, "owner.json", **request)
    assert use._state(use._receipt(root, "owner.json"))["pending"]
    with pytest.raises(ValueError, match="changed outside pending adoption"):
        use.adopt_current_work(root, "owner.json")
    assert (root / "task.md").read_text() == "Interleaved unvalidated edit"
    # The owner reconciles the concurrent edit explicitly; retry does not erase it.
    (root / "task.md").write_text(request["replacements"][0]["contents"])
    assert use.adopt_current_work(root, "owner.json")["status"] == "current"


@pytest.mark.parametrize("when", ["after_retention", "retry"])
def test_adoption_never_overwrites_a_third_saved_version(case, monkeypatch, when):
    import current_use as use
    root, owner = case
    request = adoption_request(root, owner)
    if when == "after_retention":
        publish = context._publish
        def changed(path, value):
            publish(path, value)
            if "pending" in value:
                (root / "task.md").write_text("Concurrent author's work")
        with monkeypatch.context() as patch:
            patch.setattr(context, "_publish", changed)
            with pytest.raises(ValueError, match="dependency changed"):
                use.adopt_current_work(root, "owner.json", **request)
    else:
        with monkeypatch.context() as patch:
            patch.setattr(use, "_replace_bytes", lambda *args: (_ for _ in ()).throw(OSError("stop")))
            with pytest.raises(OSError):
                use.adopt_current_work(root, "owner.json", **request)
        (root / "task.md").write_text("Concurrent author's work")
    with pytest.raises(ValueError, match="changed outside pending adoption"):
        use.adopt_current_work(root, "owner.json")
    assert (root / "task.md").read_text() == "Concurrent author's work"
    assert use._state(use._receipt(root, "owner.json"))["pending"]


def test_new_successor_absence_cannot_authorize_overwriting_concurrent_file(case, monkeypatch):
    import current_use as use
    root, owner = case
    request = adoption_request(root, owner)
    request["relations"] = [{"source": "task.md", "target": "new.md", "kind": "successor"}]
    request["replacements"].append({"path": "new.md", "contents": "New corrected task"})
    with monkeypatch.context() as patch:
        patch.setattr(use, "_replace_bytes", lambda *args: (_ for _ in ()).throw(OSError("stop")))
        with pytest.raises(OSError):
            use.adopt_current_work(root, "owner.json", **request)
    assert use._state(use._receipt(root, "owner.json"))["pending"]["expected_versions"]["new.md"] is None
    (root / "new.md").write_text("Another writer created this file")
    with pytest.raises(ValueError, match="changed outside pending adoption"):
        use.adopt_current_work(root, "owner.json")
    assert (root / "new.md").read_text() == "Another writer created this file"


def test_first_unrelated_preparation_is_stable_after_required_enrollment(case):
    root, _ = case
    prepared = check_current_use(root, "owner.json", ["other.md"])["current_use"]
    assert str(root / "task.md") not in {item["path"] for item in prepared["files"]}
    (root / "task.md").write_text("Independent progress under its own owner")
    assert check_current_use(root, "owner.json", ["other.md"], prepared)["status"] == "current"


def test_owner_transfer_cannot_erase_partially_published_adoption(case, monkeypatch):
    import current_use as use
    root, owner = case
    request = adoption_request(root, owner)
    publish = context._publish
    def fail_final(path, value):
        if "records" in value and "pending" not in value:
            raise OSError("publication failed")
        return publish(path, value)
    with monkeypatch.context() as patch:
        patch.setattr(context, "_publish", fail_final)
        with pytest.raises(OSError):
            use.adopt_current_work(root, "owner.json", **request)
    # The owner metadata is resolved, but required adoption is still pending.
    inspect_current_use(root, "owner.json", ["task.md"])
    write(root / "successor.json", {"current_use_predecessor": "owner.json"})
    with pytest.raises(ValueError, match="requires owner correction"):
        check_current_use(root, "successor.json", ["task.md"])
    assert use._state(use._receipt(root, "successor.json"))["pending"]


def test_each_replacement_checks_for_changes_after_prior_save(case, monkeypatch):
    import current_use as use
    root, owner = case
    (root / "second.md").write_text("Original second task")
    owner["current_use_corrections"][0]["affected_sources"].append("second.md")
    write(root / "owner.json", owner)
    request = adoption_request(root, owner)
    request["replacements"].append({"path": "second.md", "contents": "Corrected second task"})
    replace = use._replace_bytes
    def change_second(path, raw):
        replace(path, raw)
        if path.name == "task.md":
            (root / "second.md").write_text("Concurrent second task")
    with monkeypatch.context() as patch:
        patch.setattr(use, "_replace_bytes", change_second)
        with pytest.raises(ValueError, match="changed outside pending adoption"):
            use.adopt_current_work(root, "owner.json", **request)
    assert (root / "second.md").read_text() == "Concurrent second task"
    assert use._state(use._receipt(root, "owner.json"))["pending"]


@pytest.mark.parametrize("when", ["after_task_save", "after_owner_save"])
def test_adoption_cannot_bless_a_third_version_as_its_replacement(case, monkeypatch, when):
    import current_use as use
    root, owner = case
    request = adoption_request(root, owner)
    original_replace, original_owner = use._replace_bytes, use._save_owner
    def after_task(path, raw):
        original_replace(path, raw)
        if path.name == "task.md":
            path.write_text("Concurrent version must not be adopted")
    def after_owner(*args):
        original_owner(*args)
        (root / "task.md").write_text("Concurrent version must not be adopted")
    with monkeypatch.context() as patch:
        if when == "after_task_save":
            patch.setattr(use, "_replace_bytes", after_task)
        else:
            patch.setattr(use, "_save_owner", after_owner)
        with pytest.raises(ValueError, match="changed outside pending adoption"):
            use.adopt_current_work(root, "owner.json", **request)
    state = use._state(use._receipt(root, "owner.json"))
    assert state["pending"]
    assert (root / "task.md").read_text() == "Concurrent version must not be adopted"
    with pytest.raises(ValueError, match="changed outside pending adoption"):
        use.adopt_current_work(root, "owner.json")
