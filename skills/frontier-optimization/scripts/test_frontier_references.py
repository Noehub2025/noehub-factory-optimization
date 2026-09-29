"""Current reference preparation, propagation and retained-result reuse."""

import json
import subprocess
from pathlib import Path

import pytest
import yaml

import frontier_references as refs


def prepare(root, revision, path, prior_paths=(), **kwargs):
    return refs.prepare_resolver(root, revision, path, prior_paths, owner_source=kwargs.pop("owner_source", "TASK.md"), **kwargs)


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], stderr=subprocess.PIPE).decode().strip()


@pytest.fixture
def repo(tmp_path):
    git(tmp_path, "init")
    git(tmp_path, "config", "user.email", "test@example.invalid")
    git(tmp_path, "config", "user.name", "Reference Test")
    save(tmp_path, {"TASK.md": "---\nfeedback_not_due: The selected prerequisite remains necessary before a useful observation.\n---\n# Task\nImprove the actual outcome.\n"})
    return tmp_path


def save(root, files):
    for path, text in files.items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
    git(root, "add", "--", *files)
    git(root, "commit", "-m", "test checkpoint")
    return git(root, "rev-parse", "HEAD")


def context_body(view, reference):
    return view["sources"][reference["source_index"]]["contents"]


def test_adoption_context_preserves_root_beside_misleading_section(tmp_path):
    (tmp_path / "PROBLEM.md").write_text("---\nepoch: 2\n---\n# Problem\n## Goal\nImprove the whole outcome.\n## Old task\nKeep the old controller. Historical only.\n")
    (tmp_path / "owner.md").write_text("---\ntype: Optimization Frontier\nproblem: PROBLEM.md\nobjective_basis:\n  objective_source: PROBLEM.md#old-task\ncurrent_state:\n  work_record: task.md\n---\n# Current work\n")
    (tmp_path / "task.md").write_text("Only modify the old controller.")
    view = refs.prepare_adoption_context(tmp_path, "owner.md")
    assert "Improve the whole outcome" in context_body(view, view["controlling_context"])
    assert view["controlling_context"]["basis"] == "adopted_problem"
    assert view["selected_sources"]["objective_source"]["source"]["section"] == "old-task"
    assert "Historical only" in view["selected_sources"]["objective_source"]["selected_contents"]
    assert context_body(view, view["outgoing_tasks"][0]) == "Only modify the old controller."
    assert "status" not in view  # Content delivery is not semantic acceptance.


def test_adoption_context_keeps_input_only_restriction_and_complete_decision(tmp_path):
    (tmp_path / "owner.md").write_text("Optimize the whole objective.")
    (tmp_path / "incoming.json").write_text(json.dumps({"completion": "Every answer must preserve interface X."}))
    (tmp_path / "decision.json").write_text(json.dumps({"alternatives": "Any architecture allowed.", "reason": "The incumbent is cheaper.", "reverse_when": "Only if no more costly."}))
    (tmp_path / "task.md").write_text("Preserve X to complete the task.")
    view = refs.prepare_adoption_context(tmp_path, "owner.md", assignment="incoming.json", decision="decision.json", task_sources=["task.md"])
    assert "preserve interface X" in context_body(view, view["incoming_assignments"][0])
    assert "Any architecture allowed" in context_body(view, view["decision"])
    assert "Only if no more costly" in context_body(view, view["decision"])
    assert context_body(view, view["outgoing_tasks"][0]) == "Preserve X to complete the task."


def test_cold_recovery_without_git_result_finding_or_session(tmp_path, monkeypatch, capsys):
    (tmp_path / "owner.md").write_text("---\ncurrent_state:\n  work_record: task.md\n---\n# Inherited task\nContinue unchanged.\n")
    (tmp_path / "goal.md").write_text("The current user objective permits other approaches.")
    (tmp_path / "task.md").write_text("Complete the incumbent only.")
    with monkeypatch.context() as patch:
        patch.setattr("sys.argv", ["frontier_references.py", "recover-work", "--repo", str(tmp_path), "--owner-source", "owner.md", "--controlling-source", "goal.md"])
        assert refs.main() == 0
    view = json.loads(capsys.readouterr().out)
    assert view["phase"] == "recovery"
    assert view["decision"] is None
    assert view["controlling_context"]["basis"] == "explicit_controlling_source"
    assert "other approaches" in context_body(view, view["controlling_context"])
    assert "incumbent only" in context_body(view, view["outgoing_tasks"][0])
    assert not (tmp_path / ".frontier").exists()


def test_standalone_and_legitimate_goal_change_remain_owner_judgments(tmp_path):
    (tmp_path / "owner.md").write_text("The user asks only to fix interface X.")
    view = refs.prepare_adoption_context(tmp_path, "owner.md", phase="recovery")
    assert view["controlling_context"]["basis"] == "owner_only"
    assert any("standalone" in item for item in view["limitations"])
    (tmp_path / "new-goal.md").write_text("The user now requests interface Y instead.")
    updated = refs.prepare_adoption_context(tmp_path, "owner.md", controlling_source="new-goal.md")
    assert "interface Y" in context_body(updated, updated["controlling_context"])
    assert "interface X" in context_body(updated, updated["owner"])


def test_explicit_controlling_source_is_repo_relative_with_nested_owner(tmp_path):
    (tmp_path / "work").mkdir()
    (tmp_path / "work/owner.md").write_text("Local task.")
    (tmp_path / "goal.md").write_text("# Current goal\nThe broader user request.")
    view = refs.prepare_adoption_context(tmp_path, str(tmp_path / "work/owner.md"), controlling_source="goal.md#current-goal")
    assert view["controlling_context"]["source"] == {"path": "goal.md", "section": "current-goal"}
    assert "broader user request" in context_body(view, view["controlling_context"])


def test_context_keeps_full_body_for_missing_selector_and_reports_missing_basis(tmp_path):
    (tmp_path / "owner.md").write_text("---\nobjective_basis:\n  objective_source: goal.md#missing\n---\nSelected local task.\n")
    (tmp_path / "goal.md").write_text("# Real goal\nMeaning remains readable.")
    view = refs.prepare_adoption_context(tmp_path, "owner.md")
    assert "selection_unavailable" in view["selected_sources"]["objective_source"]
    assert "Meaning remains readable" in context_body(view, view["controlling_context"])
    (tmp_path / "goal.md").unlink()
    missing = refs.prepare_adoption_context(tmp_path, "owner.md")
    assert "unavailable" in missing["controlling_context"]
    assert "source_index" not in missing["controlling_context"]
    assert "Selected local task" in context_body(missing, missing["owner"])


def test_context_detects_relevant_read_race_but_not_unrelated_save(tmp_path, monkeypatch):
    (tmp_path / "owner.md").write_text("---\ncurrent_state:\n  work_record: task.md\n---\nCurrent objective.\n")
    (tmp_path / "task.md").write_text("Original task.")
    read = refs._working_text
    seen = 0

    def racing_read(root, path):
        nonlocal seen
        body = read(root, path)
        if path == "task.md":
            seen += 1
            if seen == 1:
                (tmp_path / path).write_text("Changed task.")
        return body

    with monkeypatch.context() as patch:
        patch.setattr(refs, "_working_text", racing_read)
        with pytest.raises(refs.ReferenceError, match="changed while reading"):
            refs.prepare_adoption_context(tmp_path, "owner.md")

    def unrelated_read(root, path):
        (tmp_path / "unrelated.txt").write_text("Ordinary unrelated work.")
        return read(root, path)

    with monkeypatch.context() as patch:
        patch.setattr(refs, "_working_text", unrelated_read)
        view = refs.prepare_adoption_context(tmp_path, "owner.md")
        assert context_body(view, view["outgoing_tasks"][0]) == "Changed task."


def test_context_preserves_research_task_alongside_primary_wait(tmp_path):
    (tmp_path / "owner.md").write_text("---\ncurrent_state:\n  primary_batch: B7\n  work_record: inquiry.md\n---\nKeep independent research.\n")
    (tmp_path / "inquiry.md").write_text("Investigate a different mechanism.")
    view = refs.prepare_adoption_context(tmp_path, "owner.md")
    assert context_body(view, view["outgoing_tasks"][0]) == "Investigate a different mechanism."
    assert view["outgoing_tasks"][1]["source"]["path"] == "artifacts/frontier/B7/batch.yaml"
    assert "unavailable" in view["outgoing_tasks"][1]


def test_resolver_and_binding_include_source_context_on_normal_path(repo):
    save(repo, {"evidence.json": '{"question":"Must preserve interface X"}'})
    prepared = prepare(repo, "HEAD", "evidence.json")
    view = prepared["adoption_context"]
    assert "Must preserve interface X" in context_body(view, view["incoming_assignments"][0])
    result = refs.bind_resolution(repo, prepared, {"reason": "Any architecture allowed", "assignment": "Implement using the selected interface."})
    assert result["adoption_context"]["decision"]["provided_body"]["reason"] == "Any architecture allowed"
    assert result["adoption_context"]["incoming_assignments"][-1]["provided_body"] == "Implement using the selected interface."


def test_prepare_adoption_cli_uses_incoming_result_and_actual_task(tmp_path, monkeypatch, capsys):
    for path, body in {"owner.md": "The user's original goal.", "incoming.md": "Only accept the existing interface.", "result.json": '{"reason":"Other architecture is allowed."}', "task.md": "Keep the existing interface."}.items():
        (tmp_path / path).write_text(body)
    with monkeypatch.context() as patch:
        patch.setattr("sys.argv", ["frontier_references.py", "prepare-adoption", "--repo", str(tmp_path), "--owner-source", "owner.md", "--assignment", "incoming.md", "--result", "result.json", "--source", "task.md"])
        assert refs.main() == 0
    view = json.loads(capsys.readouterr().out)
    assert "Only accept" in context_body(view, view["incoming_assignments"][0])
    assert "Other architecture" in context_body(view, view["decision"])
    assert "Keep the existing" in context_body(view, view["outgoing_tasks"][0])


def test_adopt_work_required_report_survives_optional_pointer_failure(tmp_path, monkeypatch, capsys):
    import frontier_context
    import current_use
    (tmp_path / "owner.md").write_text("Current controlling task.")
    calls = []

    def required(root, owner, **kwargs):
        calls.append((owner, kwargs))
        return {"status": "current", "current_use": {"checked_sources": kwargs["sources"]}, "coverage": "Object use only."}

    def optional(*args, **kwargs):
        raise OSError("optional pointer unavailable")

    with monkeypatch.context() as patch:
        patch.setattr(current_use, "adopt_current_work", required)
        patch.setattr(frontier_context, "register_adopted_work", optional)
        patch.setattr("sys.argv", ["frontier_references.py", "adopt-work", "--repo", str(tmp_path), "--path", "owner.md"])
        assert refs.main() == 0
    report = json.loads(capsys.readouterr().out)
    assert calls == [("owner.md", {"sources": []})]
    assert report["current_use"] == {"checked_sources": []}
    assert not report["registered"]
    assert report["native_context_warning"] == "optional pointer unavailable"
    view = report["adoption_context"]
    assert context_body(view, view["owner"]) == "Current controlling task."


def test_adopt_work_does_not_downgrade_required_failure(tmp_path, monkeypatch, capsys):
    import frontier_context
    import current_use

    def failed(*args, **kwargs):
        raise ValueError("required adoption incomplete")

    def unexpected(*args, **kwargs):
        pytest.fail("optional pointer must not publish before required adoption")

    with monkeypatch.context() as patch:
        patch.setattr(current_use, "adopt_current_work", failed)
        patch.setattr(frontier_context, "register_adopted_work", unexpected)
        patch.setattr("sys.argv", ["frontier_references.py", "adopt-work", "--repo", str(tmp_path), "--path", "owner.md"])
        assert refs.main() == 2
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "NOT_READY"
    assert report["error"] == "required adoption incomplete"


def test_adopt_work_cli_retains_then_replaces_without_native_session(tmp_path, monkeypatch, capsys):
    (tmp_path / "owner.json").write_text(json.dumps({"current_state": {"campaign_status": "running", "work_record": "task.md"}}))
    (tmp_path / "task.md").write_text("Only preserve the incumbent.")
    (tmp_path / "finding.md").write_text("The owner found unsupported incumbent-only scope.")
    (tmp_path / "adoption.md").write_text("The owner accepts the broader task within existing authority.")
    request = {"corrections": [{"id": "scope", "finding": "finding.md", "effect": "repair", "affected_sources": ["task.md"], "status": "resolved", "resolution": {"reason": "Remove unsupported scope.", "evidence": "adoption.md"}}], "replacements": [{"path": "task.md", "contents": "Investigate the objective beyond this implementation."}]}
    (tmp_path / "request.json").write_text(json.dumps(request))
    with monkeypatch.context() as patch:
        patch.delenv("CODEX_SESSION_ID", raising=False)
        patch.delenv("CODEX_THREAD_ID", raising=False)
        patch.setattr("sys.argv", ["frontier_references.py", "adopt-work", "--repo", str(tmp_path), "--path", "owner.json", "--source", "task.md", "--correction-request", str(tmp_path / "request.json")])
        assert refs.main() == 0
    report = json.loads(capsys.readouterr().out)
    assert report["current_use"]["blocked_ids"] == []
    assert report["current_use"]["checked_sources"] == [str(tmp_path / "task.md")]
    assert report["registered"] is False
    assert list((tmp_path / ".frontier/hook-context").glob("owner-*-corrections.json"))
    assert (tmp_path / "task.md").read_text() == request["replacements"][0]["contents"]
    view = report["adoption_context"]
    assert context_body(view, view["outgoing_tasks"][0]) == request["replacements"][0]["contents"]


def test_repeated_views_do_not_duplicate_sources_or_recurse_into_generated_context(tmp_path):
    (tmp_path / "owner.md").write_text("---\nobjective_basis:\n  objective_source: goal.md\n  evaluation_source: goal.md\n---\nCurrent task.")
    (tmp_path / "goal.md").write_text("The controlling objective. " * 100)
    result = {"reason": "Preserve this substantive decision and condition.", "assignment": "Use interface X."}
    sizes = []
    for _ in range(4):
        (tmp_path / "result.json").write_text(json.dumps(result))
        view = refs.prepare_adoption_context(tmp_path, "owner.md", decision="result.json", phase="recovery")
        assert len(view["sources"]) == 3
        assert sum("The controlling objective" in source["contents"] for source in view["sources"]) == 1
        assert "Preserve this substantive decision" in context_body(view, view["decision"])
        assert "adoption_context" not in json.loads(context_body(view, view["decision"]))
        sizes.append(len(json.dumps(view)))
        result["adoption_context"] = view
    # One explicit omitted-field note appears after the first saved view;
    # subsequent views must not grow with prior generated context.
    assert sizes[2:] == [sizes[1], sizes[1]]
    # One exact snapshot locator is added when generated content is omitted.
    assert sizes[1] - sizes[0] < 400


def test_cold_recovery_scopes_history_without_losing_current_decision_or_effects(tmp_path):
    owner = "---\ntype: Optimization Frontier\nproblem: goal.md\ncurrent_state:\n  primary_batch: B1\ncontinuation:\n  basis:\n    path: decision.json\n    field: reason\n---\n"
    (tmp_path / "owner.md").write_text(owner + "## Brief\nCurrent understanding and open alternatives.\n## History\nOld history.")
    (tmp_path / "goal.md").write_text("The full objective permits any implementation.")
    (tmp_path / "incoming.json").write_text('{"completion":"Only accept the old interface."}')
    (tmp_path / "decision.json").write_text(json.dumps({"assignment": {"path": "incoming.json"}, "reason": "Prefer the incumbent because it is cheap.", "reverse_when": "Only if the alternative costs no more."}))
    batch = {"batch": "B1", "definition": {"objective": "Explore another mechanism", "completion": "Keep the old interface"},
             "current": {"conclusion": "The objective gap remains", "observations": ["Current evidence"]},
             "resource_limits": {"calls": 1}, "consumption": {"calls": 1},
             "attempts": [{"attempt": 1, "status": "completed", "observations": ["Historical detail"],
                           "result": {"learning": "Deferral recurred", "objective_gap": "Still unresolved"},
                           "actual_consequences": ["One call consumed"], "recovery_condition": "Never repeat"},
                          {"attempt": 2, "status": "completed", "observations": ["Latest complete evidence"], "result": {"claim": "Latest result"}},
                          {"attempt": 3, "status": "uncertain", "observations": ["Uncertain effects must remain"]}]}
    path = tmp_path / "artifacts/frontier/B1/batch.yaml"
    path.parent.mkdir(parents=True)
    path.write_text(yaml.safe_dump(batch))
    first = refs.prepare_adoption_context(tmp_path, "owner.md", phase="recovery")
    assert "any implementation" in context_body(first, first["controlling_context"])
    assert "costs no more" in context_body(first, first["decision"])
    assert "Only accept the old interface" in context_body(first, first["incoming_assignments"][0])
    task = yaml.safe_load(context_body(first, first["outgoing_tasks"][0]))
    assert task["definition"] == batch["definition"]
    assert task["current"] == batch["current"]
    assert task["attempts"][0]["result"] == batch["attempts"][0]["result"]
    assert task["attempts"][0]["actual_consequences"] == ["One call consumed"]
    assert task["attempts"][0]["recovery_condition"] == "Never repeat"
    assert task["attempts"][-1] == batch["attempts"][-1]
    source = first["sources"][first["outgoing_tasks"][0]["source_index"]]
    assert source["omitted_source_parts"][0]["json_pointer"] == "/attempts/0/observations"
    (tmp_path / "owner.md").write_text(owner + "## Brief\nCurrent understanding and open alternatives.\n## History\n" + "Unrelated old event. " * 30000)
    batch["attempts"][0]["observations"] = ["Historical raw observation. " * 30000]
    path.write_text(yaml.safe_dump(batch))
    later = refs.prepare_adoption_context(tmp_path, "owner.md", phase="recovery")
    assert len(json.dumps(later)) == len(json.dumps(first))
    # Explicit task input and incoming records are never projected as history.
    explicit = refs.prepare_adoption_context(tmp_path, "owner.md", task_sources=[path.relative_to(tmp_path).as_posix()])
    assert "Historical raw observation" in context_body(explicit, explicit["outgoing_tasks"][0])
    # A source also used as an incoming assignment is promoted to full content.
    incoming_owner = refs.prepare_adoption_context(tmp_path, "owner.md", assignment="owner.md")
    assert "Unrelated old event" in context_body(incoming_owner, incoming_owner["owner"])


def test_latest_completed_attempt_remains_complete_in_recovery(tmp_path):
    (tmp_path / "owner.md").write_text("---\ncurrent_state:\n  primary_batch: B1\n---\nCurrent task.")
    path = tmp_path / "artifacts/frontier/B1/batch.yaml"
    path.parent.mkdir(parents=True)
    batch = {"batch": "B1", "definition": {}, "current": {}, "attempts": [
        {"status": "completed", "observations": ["Result being adopted"], "checks": ["Latest check"], "result": {"reason": "Meaningful learning"}}]}
    path.write_text(yaml.safe_dump(batch))
    view = refs.prepare_adoption_context(tmp_path, "owner.md", phase="recovery")
    assert yaml.safe_load(context_body(view, view["outgoing_tasks"][0])) == batch


def test_resolver_uses_saved_bytes_and_repairs_derived_binding(repo):
    commit = save(repo, {"evidence.json": '{"goal":"改善","result":1}'})
    prepared = prepare(repo, "HEAD", "evidence.json")
    (repo / "evidence.json").write_text('{"result":999}')
    body = {"row": 11, "exact_action": "test a new route", "evidence_state_identity": "mistyped"}
    result = refs.bind_resolution(repo, {**prepared, "evidence_state_identity": "also mistyped"}, body)
    assert result["evidence_state_identity"] == prepared["evidence_state_identity"]
    assert result["evidence_source"] == {"commit": commit, "path": "evidence.json"}
    assert result["exact_action"] == body["exact_action"]


def test_resolver_reuses_saved_reads_only_within_one_operation(repo, monkeypatch):
    save(repo, {"evidence.json": '{"goal":"improve","result":1}'})
    original = refs.read_file
    calls = []

    def counted(root, commit, path):
        calls.append((commit, path))
        return original(root, commit, path)

    monkeypatch.setattr(refs, "read_file", counted)
    prepare(repo, "HEAD", "evidence.json")
    first_operation = list(calls)
    assert first_operation
    assert len(first_operation) == len(set(first_operation))

    prepare(repo, "HEAD", "evidence.json")
    assert calls == first_operation + first_operation


def continuation_fixture(root, kind="idle"):
    owner = {"feedback_not_due": "Already selected observation is pending.",
             "current_state": {"campaign_status": "running", "work_record": "work.yaml"},
             "comparison": "A brief wait costs less than switching; resume on the result."}
    (root / "owner.yaml").write_text(json.dumps(owner))
    (root / "work.yaml").write_text('current: waiting\n')
    (root / "observation.yaml").write_text('current: pending\n')
    block = {"owner_state": {"path": "owner.yaml", "field": "current_state"},
             "waiting_on": [{"path": "observation.yaml", "field": "current"}],
             "affected_work": [{"path": "work.yaml", "field": "current", "reason": "The next dependent step needs this observation."}],
             "next": {"kind": kind}, "basis": {"path": "owner.yaml", "field": "comparison"},
             "reconsider_when": "The selected result arrives or useful compatible work becomes available."}
    if kind == "work":
        (root / "independent.md").write_text("Continue the selected inquiry; owner is the Coordinator; yield before integration.")
        block["next"]["work"] = [{"path": "independent.md"}]
    block["source_basis"] = refs.collect_continuation_sources(root, "owner.yaml", block)
    owner["continuation"] = block
    (root / "owner.yaml").write_text(json.dumps(owner))
    return owner, block


@pytest.mark.parametrize("kind", ["idle", "work"])
def test_continuation_current_working_sources_without_git_or_session(tmp_path, kind):
    _, block = continuation_fixture(tmp_path, kind)
    result = refs.check_continuation(tmp_path, "owner.yaml")
    assert result["status"] == "current" and result["next"] == kind
    assert result["sources_checked"] == (5 if kind == "work" else 4)
    assert block["source_basis"] == refs.collect_continuation_sources(tmp_path, "owner.yaml", block)


@pytest.mark.parametrize("changed", ["observation", "owner", "work"])
def test_continuation_rejects_dirty_direct_sources_without_owner_commit(tmp_path, changed):
    owner, _ = continuation_fixture(tmp_path)
    if changed == "owner":
        owner["current_state"]["work_record"] = "new.md"
        (tmp_path / "owner.yaml").write_text(json.dumps(owner))
    else:
        (tmp_path / f"{changed}.yaml").write_text("current: ready\n")
    with pytest.raises(refs.ReferenceError, match="source basis"):
        refs.check_continuation(tmp_path, "owner.yaml")


def test_continuation_reuses_unrelated_history_and_requires_selected_disposition(tmp_path):
    owner, block = continuation_fixture(tmp_path)
    with (tmp_path / "observation.yaml").open("a") as out:
        out.write("history: unrelated annotation\n")
    assert refs.check_continuation(tmp_path, "owner.yaml")["status"] == "current"
    owner["current_state"]["parallel_batches"] = ["B12"]
    (tmp_path / "owner.yaml").write_text(json.dumps(owner))
    block["source_basis"] = refs.collect_continuation_sources(tmp_path, "owner.yaml", block)
    with pytest.raises(refs.ReferenceError, match="no continuation disposition"):
        refs.check_continuation(tmp_path, "owner.yaml", block)


@pytest.mark.parametrize("bad", ["missing_basis", "missing_reason", "empty_work", "owner_whole", "outside"])
def test_continuation_rejects_unsupported_arrangements(tmp_path, bad):
    _, block = continuation_fixture(tmp_path)
    if bad == "missing_basis": block.pop("source_basis")
    elif bad == "missing_reason": block["affected_work"][0].pop("reason")
    elif bad == "empty_work": block["next"] = {"kind": "work", "work": []}
    elif bad == "owner_whole": block["owner_state"] = {"path": "owner.yaml"}
    else: block["waiting_on"] = [{"path": "../outside"}]
    with pytest.raises((refs.ReferenceError, OSError)):
        refs.check_continuation(tmp_path, "owner.yaml", block)


def test_continuation_binding_and_reuse_validate_live_dependencies(repo):
    owner, block = continuation_fixture(repo)
    save(repo, {"owner.yaml": json.dumps(owner), "evidence.json": '{"result":1}',
                "work.yaml": (repo / "work.yaml").read_text(), "observation.yaml": (repo / "observation.yaml").read_text()})
    prepared = prepare(repo, "HEAD", "evidence.json", owner_source="owner.yaml")
    result = refs.bind_resolution(repo, prepared, {"row": 11, "continuation": block})
    save(repo, {"resolution.json": json.dumps(result)})
    assert "reuse_resolution" in prepare(repo, "HEAD", "evidence.json", ["resolution.json"], owner_source="owner.yaml")
    (repo / "observation.yaml").write_text("current: complete\n")
    with pytest.raises(refs.ReferenceError, match="source basis"):
        refs.bind_resolution(repo, prepared, {"row": 11, "continuation": block})
    with pytest.raises(refs.ReferenceError, match="source basis"):
        prepare(repo, "HEAD", "evidence.json", ["resolution.json"], owner_source="owner.yaml")


def test_wait_requires_arrangement_but_ordinary_result_does_not(repo):
    save(repo, {"evidence.json": '{}'})
    prepared = prepare(repo, "HEAD", "evidence.json", feedback_trigger="observation due")
    body = {"rationale": "Wait for a useful observation.", "feedback_decision": {
        "trigger": "observation due", "action": "wait", "basis": "/rationale", "next_condition": "result arrives"}}
    with pytest.raises(refs.ReferenceError, match="requires continuation"):
        refs.bind_resolution(repo, prepared, body)
    body["feedback_decision"]["action"] = "observe"
    assert refs.bind_resolution(repo, prepared, body)["feedback_decision"]["action"] == "observe"


def test_continuation_cli_reads_owner_without_optional_registration(tmp_path):
    import sys
    continuation_fixture(tmp_path)
    command = [sys.executable, str(Path(refs.__file__)), "check-continuation", "--repo", str(tmp_path), "--path", "owner.yaml"]
    before = sorted(p.name for p in tmp_path.iterdir())
    result = subprocess.run(command, text=True, capture_output=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["status"] == "current"
    assert sorted(p.name for p in tmp_path.iterdir()) == before
    (tmp_path / "observation.yaml").write_text("current: complete\n")
    failed = subprocess.run(command, text=True, capture_output=True)
    assert failed.returncode == 2
    assert json.loads(failed.stdout)["status"] == "NOT_READY"


def test_wait_result_cannot_borrow_owner_arrangement(tmp_path):
    continuation_fixture(tmp_path)
    with pytest.raises(refs.ReferenceError, match="associated with this result"):
        refs._check_result_continuation(tmp_path, "owner.yaml", {"feedback_decision": {"action": "wait"}})
    for invalid in (None, [], "wait"):
        with pytest.raises(refs.ReferenceError, match="mapping"):
            refs._check_result_continuation(tmp_path, "owner.yaml", {"feedback_decision": invalid})


def test_halted_owner_cannot_validate_continuation(tmp_path):
    owner, block = continuation_fixture(tmp_path)
    owner["current_state"]["campaign_status"] = "halted"
    (tmp_path / "owner.yaml").write_text(json.dumps(owner))
    block["source_basis"] = refs.collect_continuation_sources(tmp_path, "owner.yaml", block)
    with pytest.raises(refs.ReferenceError, match="pause or closeout"):
        refs.check_continuation(tmp_path, "owner.yaml", block)


@pytest.mark.parametrize("defect", ["empty_basis", "blank_basis", "scalar_state", "empty_state", "frontier_status", "conflicting_status"])
def test_continuation_rejects_empty_meaning_and_malformed_state(tmp_path, defect):
    owner, block = continuation_fixture(tmp_path)
    if defect == "empty_basis": owner["comparison"] = ""
    elif defect == "blank_basis": owner["comparison"] = "  "
    elif defect == "scalar_state": owner["current_state"] = "running"
    elif defect == "empty_state": owner["current_state"] = {}
    elif defect == "conflicting_status": owner["campaign_status"] = "halted"
    else:
        owner["type"] = "Optimization Frontier"
        owner["current_state"].pop("campaign_status")
    (tmp_path / "owner.yaml").write_text(json.dumps(owner))
    block["source_basis"] = refs.collect_continuation_sources(tmp_path, "owner.yaml", block)
    with pytest.raises(refs.ReferenceError, match="empty|current_state"):
        refs.check_continuation(tmp_path, "owner.yaml", block)


def test_same_facts_reuse_result_after_format_location_and_commit_change(repo):
    save(repo, {"evidence.json": '{"a":1,"b":[2,3]}'})
    prepared = prepare(repo, "HEAD", "evidence.json")
    result = refs.bind_resolution(repo, prepared, {"row": 11, "exact_action": "continue"})
    result["evidence_state_identity"] = "old transcription error"
    save(repo, {"resolution.json": json.dumps(result), "moved.json": '{\n "b": [2, 3], "a": 1\n}', "unrelated.txt": "note"})
    reused = prepare(repo, "HEAD", "moved.json", ["resolution.json"])
    assert reused["evidence_state_identity"] == prepared["evidence_state_identity"]
    assert reused["reuse_resolution"]["path"] == "resolution.json"
    with pytest.raises(refs.ReferenceError, match="reuse"):
        refs.bind_resolution(repo, reused, {"row": 7})


def test_changed_facts_do_not_reuse_or_rebind_old_judgment(repo):
    save(repo, {"evidence.json": '{"result":1}'})
    old = prepare(repo, "HEAD", "evidence.json")
    result = refs.bind_resolution(repo, old, {"row": 11})
    save(repo, {"resolution.json": json.dumps(result), "evidence.json": '{"result":2}'})
    new = prepare(repo, "HEAD", "evidence.json", ["resolution.json"])
    assert "reuse_resolution" not in new
    with pytest.raises(refs.ReferenceError, match="different decision facts"):
        refs.bind_resolution(repo, new, result)


def test_retained_resolution_identity_is_read_without_rewrite(repo):
    save(repo, {"evidence.json": '{"result":1}'})
    identity = prepare(repo, "HEAD", "evidence.json")["evidence_state_identity"]
    historical = json.dumps({"identity_reproduction": {"evidence_state_identity": identity}, "resolution": {"first_applicable_row": 11}})
    save(repo, {"historical.yaml": historical})
    result = prepare(repo, "HEAD", "evidence.json", ["historical.yaml"])
    assert "reuse_resolution" not in result
    legacy = {"evidence_source": refs.reference(repo, "HEAD", "evidence.json"), "row": 11}
    save(repo, {"legacy.json": json.dumps(legacy)})
    rebound = refs.bind_resolution(repo, {"evidence_source": legacy["evidence_source"]}, legacy,
                                   historical_source=refs.reference(repo, "HEAD", "legacy.json"))
    assert rebound["row"] == 11
    assert (repo / "historical.yaml").read_text() == historical


@pytest.mark.parametrize("content", ['{"a":1,"a":2}', '{"a":NaN}', '[]', '{'])
def test_invalid_preparation_has_no_output_or_decision(repo, content):
    save(repo, {"evidence.json": content})
    before = git(repo, "status", "--porcelain")
    with pytest.raises(ValueError):
        prepare(repo, "HEAD", "evidence.json")
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
    monkeypatch.setattr("sys.argv", ["frontier_references.py", "resolver", "--owner-source", "TASK.md", "--repo", str(repo), "--path", "evidence.json", "--output", str(assignment)])
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
    monkeypatch.setattr("sys.argv", ["frontier_references.py", "resolver", "--owner-source", "TASK.md", "--repo", str(repo),
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
    monkeypatch.setattr("sys.argv", ["frontier_references.py", "resolver", "--owner-source", "TASK.md", "--repo", str(repo),
                                    "--path", "evidence.json", "--output", str(assignment)])
    assert refs.main() == 0
    assert json.loads(assignment.read_text())["evidence_state_identity"]


def test_optional_policy_is_supplied_to_existing_resolver_without_claiming_handling(repo):
    save(repo, {"evidence.json": '{"result":1}'})
    absent = prepare(repo, "HEAD", "evidence.json")
    policy_file(repo)
    supplied = prepare(repo, "HEAD", "evidence.json")
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
    prepared = prepare(repo, "HEAD", "evidence.json")
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
    prepared = prepare(repo, "HEAD", "evidence.json")
    result = refs.bind_resolution(repo, prepared, {"row": 11, "policy_disposition": disposition})
    assert result["row"] == 11
    assert result["policy_coverage"]["judgment_status"] == "not_reported"


def test_changed_policy_preserves_reported_handling_but_does_not_claim_current_coverage(repo):
    save(repo, {"evidence.json": '{"result":1}'})
    path = policy_file(repo)
    prepared = prepare(repo, "HEAD", "evidence.json")
    path.write_text("Changed guidance", encoding="utf-8")
    result = refs.bind_resolution(repo, prepared, {"row": 11, "policy_disposition": {
        "status": "addressed", "reason": "Used the supplied guidance in the original comparison."}})
    assert result["policy_coverage"]["policy_status"] == "changed"
    assert result["policy_coverage"]["judgment_status"] == "addressed"
    assert result["decision_policy"]["sha256"] == prepared["decision_policy"]["sha256"]


def test_missing_unreadable_and_old_policy_context_do_not_block_existing_work(repo):
    save(repo, {"evidence.json": '{"result":1}'})
    absent = prepare(repo, "HEAD", "evidence.json")
    old = {key: value for key, value in absent.items() if key != "decision_policy"}
    for prepared in (absent, old):
        result = refs.bind_resolution(repo, prepared, {"row": 11})
        assert result["policy_coverage"] == {"policy_status": "not_provided", "judgment_status": "not_reported"}
    path = policy_file(repo)
    path.write_bytes(b"\xff")
    unavailable = prepare(repo, "HEAD", "evidence.json")
    result = refs.bind_resolution(repo, unavailable, {"row": 11})
    assert result["policy_coverage"]["policy_status"] == "unavailable"
    assert result["row"] == 11


@pytest.mark.parametrize("change_policy", [False, True])
def test_prior_judgment_reuse_reports_actual_original_coverage_without_reopening(repo, change_policy):
    save(repo, {"evidence.json": '{"result":1}'})
    path = policy_file(repo)
    prepared = prepare(repo, "HEAD", "evidence.json")
    result = refs.bind_resolution(repo, prepared, {"row": 11, "policy_disposition": {
        "status": "addressed", "reason": "The existing comparison applied the supplied policy."}})
    save(repo, {"resolution.json": json.dumps(result)})
    if change_policy:
        path.write_text("Updated optional guidance", encoding="utf-8")
    reused = prepare(repo, "HEAD", "evidence.json", ["resolution.json"])
    assert reused["reuse_resolution"]["path"] == "resolution.json"
    assert reused["reused_policy_coverage"]["policy_status"] == ("changed" if change_policy else "current")
    assert reused["reused_policy_coverage"]["judgment_status"] == "addressed"
    assert json.loads((repo / "resolution.json").read_text()) == result


def test_rebinding_an_existing_judgment_cannot_refresh_its_policy_coverage(repo):
    save(repo, {"evidence.json": '{"result":1}'})
    path = policy_file(repo)
    first = prepare(repo, "HEAD", "evidence.json")
    result = refs.bind_resolution(repo, first, {"row": 11, "policy_disposition": {
        "status": "addressed", "reason": "Applied the original supplied guidance."}})
    path.write_text("Different current guidance", encoding="utf-8")
    current = prepare(repo, "HEAD", "evidence.json")
    rebound = refs.bind_resolution(repo, current, result)
    assert rebound["decision_policy"] == result["decision_policy"]
    assert rebound["policy_coverage"]["policy_status"] == "changed"
    assert rebound["policy_coverage"]["judgment_status"] == "addressed"


def test_cli_reusing_assignment_clears_prior_policy_coverage_when_facts_change(repo, monkeypatch):
    save(repo, {"evidence.json": '{"result":1}'})
    policy_file(repo)
    prepared = prepare(repo, "HEAD", "evidence.json")
    result = refs.bind_resolution(repo, prepared, {"row": 11, "policy_disposition": {
        "status": "addressed", "reason": "Applied the supplied policy in this judgment."}})
    save(repo, {"resolution.json": json.dumps(result)})
    assignment = repo / "assignment.json"
    command = ["frontier_references.py", "resolver", "--owner-source", "TASK.md", "--repo", str(repo), "--path", "evidence.json",
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


def frontier_files(*, due=True):
    timing = 'feedback_trigger: The candidate can now produce useful objective evidence.\n' if due else 'feedback_not_due: The prerequisite still cannot produce useful evidence.\n'
    return {
        "campaign/FRONTIER.md": '---\ntype: Optimization Frontier\nproblem: PROBLEM.md\nproblem_epoch: 2\nrepresentation: REPRESENTATION.md\nrepresentation_revision: 3\ncurrent_state:\n  primary_batch: B001\n  pending_observation: Result becomes usable after exposure.\nobjective_basis:\n  objective_source: PROBLEM.md#goal\n  evaluation_source: PROBLEM.md#evaluation\n' + timing + '---\n# Campaign\n[Work](WORK.md#pending)\n## History\nUnrelated past work.\n',
        "campaign/PROBLEM.md": '---\nepoch: 2\n---\n# Problem\n## Goal\nImprove the real outcome.\n## Evaluation\nCompare outcomes under the named conditions.\n## History\nEarlier work.\n',
        "campaign/REPRESENTATION.md": '---\nproblem: PROBLEM.md\nproblem_epoch: 2\nrepresentation_revision: 3\n---\n# Representation\nSearch translation.\n',
        "campaign/WORK.md": '# Work\n## Pending\nObserve after the first usable exposure.\n## History\nEarlier work.\n',
        "evidence.json": '{"recommended":"local diagnosis"}',
    }


def feedback_result():
    return {"comparison": "The available observation can distinguish the live explanations before optional diagnosis.",
            "feedback_decision": {"trigger": "The candidate can now produce useful objective evidence.",
                                  "action": "observe", "basis": "/comparison", "next_condition": "Adopt the observation before choosing dependent work."}}


def test_preparation_derives_adopted_sources_outside_recommendations(repo):
    save(repo, frontier_files())
    prepared = prepare(repo, "HEAD", "evidence.json", owner_source="campaign/FRONTIER.md")
    assert prepared["objective_basis"]["objective_source"]["path"] == "campaign/PROBLEM.md"
    assert prepared["objective_basis"]["evaluation_source"]["section"] == "evaluation"
    assert prepared["objective_basis"]["current_work_source"]["field"] == "current_state"
    assert "Improve the real outcome" in prepared["objective_basis_content"]["objective_source"]
    assert "Earlier work" not in json.dumps(prepared["objective_basis_content"])
    assert refs.bind_resolution(repo, prepared, feedback_result())["feedback_decision"]["action"] == "observe"


@pytest.mark.parametrize("change", ["missing", "bad_action", "missing_basis", "wrong_trigger", "self_basis"])
def test_due_feedback_requires_concrete_linkage(repo, change):
    save(repo, frontier_files())
    prepared = prepare(repo, "HEAD", "evidence.json", owner_source="campaign/FRONTIER.md")
    result = feedback_result()
    if change == "missing":
        result.pop("feedback_decision")
    else:
        field, value = {"bad_action": ("action", "passed"), "missing_basis": ("basis", "/absent"),
                        "wrong_trigger": ("trigger", "An unrelated event"), "self_basis": ("basis", "/feedback_decision/action")}[change]
        result["feedback_decision"][field] = value
    with pytest.raises(refs.ReferenceError):
        refs.bind_resolution(repo, prepared, result)


@pytest.mark.parametrize("change", ["goal", "evaluation", "pending", "timing", "epoch", "parent"])
def test_relevant_source_change_prevents_reuse_and_binding(repo, change):
    files = frontier_files()
    save(repo, files)
    prepared = prepare(repo, "HEAD", "evidence.json", owner_source="campaign/FRONTIER.md")
    result = refs.bind_resolution(repo, prepared, feedback_result())
    updates = {"resolution.json": json.dumps(result)}
    if change in {"goal", "evaluation"}:
        updates["campaign/PROBLEM.md"] = files["campaign/PROBLEM.md"].replace(
            "Improve the real outcome." if change == "goal" else "Compare outcomes under the named conditions.", "A decision-relevant change.")
    else:
        old, new = {"pending": ("Result becomes usable after exposure.", "A new result is available."),
                    "timing": ("The candidate can now produce useful objective evidence.", "The deadline changed."),
                    "epoch": ("problem_epoch: 2", "problem_epoch: 9"),
                    "parent": ("problem: PROBLEM.md", "problem: OTHER.md")}[change]
        updates["campaign/FRONTIER.md"] = files["campaign/FRONTIER.md"].replace(old, new)
    save(repo, updates)
    with pytest.raises(refs.ReferenceError):
        refs.bind_resolution(repo, prepared, feedback_result())
    if change in {"epoch", "parent"}:
        with pytest.raises(refs.ReferenceError):
            prepare(repo, "HEAD", "evidence.json", ["resolution.json"], owner_source="campaign/FRONTIER.md")
    else:
        fresh = prepare(repo, "HEAD", "evidence.json", ["resolution.json"], owner_source="campaign/FRONTIER.md")
        assert fresh["evidence_state_identity"] == prepared["evidence_state_identity"]
        assert "reuse_resolution" not in fresh


def test_unrelated_source_sections_commits_and_dirty_files_preserve_reuse(repo):
    files = frontier_files()
    save(repo, files)
    prepared = prepare(repo, "HEAD", "evidence.json", owner_source="campaign/FRONTIER.md")
    result = refs.bind_resolution(repo, prepared, feedback_result())
    save(repo, {"resolution.json": json.dumps(result), "unrelated.txt": "New unrelated work.",
                "campaign/FRONTIER.md": files["campaign/FRONTIER.md"].replace("Unrelated past work.", "More unrelated history.")})
    (repo / "unrelated.txt").write_text("Unsaved unrelated changes.")
    reused = prepare(repo, "HEAD", "evidence.json", ["resolution.json"], owner_source="campaign/FRONTIER.md")
    assert reused["reuse_resolution"]["path"] == "resolution.json"
    assert refs.bind_resolution(repo, prepared, feedback_result())["objective_basis_identity"] == result["objective_basis_identity"]
    assert (repo / "unrelated.txt").read_text() == "Unsaved unrelated changes."


@pytest.mark.parametrize("replacement", ["Current controlling target changed outside the selected excerpt.", "More unrelated historical detail."])
def test_full_controlling_source_change_refreshes_context_without_forcing_reranking(repo, replacement):
    files = frontier_files()
    save(repo, files)
    prepared = prepare(repo, "HEAD", "evidence.json", owner_source="campaign/FRONTIER.md")
    result = refs.bind_resolution(repo, prepared, feedback_result())
    save(repo, {"resolution.json": json.dumps(result),
                "campaign/PROBLEM.md": files["campaign/PROBLEM.md"].replace("Earlier work.", replacement)})
    with pytest.raises(refs.ReferenceError, match="refresh owner context"):
        refs.bind_resolution(repo, prepared, feedback_result())
    fresh = prepare(repo, "HEAD", "evidence.json", ["resolution.json"], owner_source="campaign/FRONTIER.md")
    assert "reuse_resolution" not in fresh
    assert replacement in context_body(fresh["adoption_context"], fresh["adoption_context"]["controlling_context"])
    assert fresh["objective_basis_identity"] == prepared["objective_basis_identity"]
    # Explicit owner adoption can retain the same supported professional result.
    rebound = refs.bind_resolution(repo, fresh, result)
    assert rebound["feedback_decision"] == result["feedback_decision"]
    assert rebound["comparison"] == result["comparison"]
    assert rebound["controlling_objective_binding"] == fresh["controlling_objective_binding"]
    assert rebound["controlling_objective_binding"]["sha256"] != result["controlling_objective_binding"]["sha256"]


def test_generic_narrow_objective_refresh_and_legacy_result_need_no_new_parent(repo):
    owner = "---\nobjective_basis:\n  objective_source: GOAL.md#local\nfeedback_not_due: The prerequisite remains necessary.\n---\nCurrent task."
    goal = "# Goal\n## Local\nPreserve the selected legitimate interface.\n## Context\nThe wider user goal.\n"
    save(repo, {"TASK.md": owner, "GOAL.md": goal, "evidence.json": '{"result":1}'})
    prepared = prepare(repo, "HEAD", "evidence.json")
    result = refs.bind_resolution(repo, prepared, {"reason": "Keep the supported focused task."})
    legacy = {key: value for key, value in result.items() if key != "controlling_objective_binding"}
    save(repo, {"legacy.json": json.dumps(legacy), "GOAL.md": goal.replace("wider user goal", "updated wider user goal")})
    with pytest.raises(refs.ReferenceError, match="refresh owner context"):
        refs.bind_resolution(repo, prepared, {"reason": "Keep the supported focused task."})
    fresh = prepare(repo, "HEAD", "evidence.json", ["legacy.json"])
    assert "reuse_resolution" not in fresh
    assert fresh["objective_basis_identity"] == prepared["objective_basis_identity"]
    assert "updated wider user goal" in context_body(fresh["adoption_context"], fresh["adoption_context"]["controlling_context"])
    rebound = refs.bind_resolution(repo, fresh, legacy)
    assert rebound["reason"] == result["reason"]
    assert rebound["controlling_objective_binding"] == fresh["controlling_objective_binding"]


@pytest.mark.parametrize("pointer", ["MISSING.md", "PROBLEM.md#missing", "UNRELATED.md"])
def test_bad_owner_sources_fail_before_assignment(repo, pointer):
    files = frontier_files()
    files["campaign/FRONTIER.md"] = files["campaign/FRONTIER.md"].replace("PROBLEM.md#goal", pointer)
    files["campaign/UNRELATED.md"] = "An arbitrary recommendation source."
    save(repo, files)
    with pytest.raises(refs.ReferenceError):
        prepare(repo, "HEAD", "evidence.json", owner_source="campaign/FRONTIER.md")


def test_missing_timing_and_owner_fail_normal_cli_without_replacing_output(repo, monkeypatch, capsys):
    save(repo, {"TASK.md": "# Actual task\nA goal and a pending decision.", "evidence.json": '{}'})
    output = repo / "assignment.json"
    output.write_text('{"retained":"existing assignment"}')
    command = ["frontier_references.py", "resolver", "--repo", str(repo), "--path", "evidence.json", "--output", str(output)]
    for extra in ([], ["--owner-source", "TASK.md"]):
        monkeypatch.setattr("sys.argv", command + extra)
        assert refs.main() == 2
        assert json.loads(capsys.readouterr().out)["status"] == "NOT_READY"
        assert output.read_text() == '{"retained":"existing assignment"}'
    monkeypatch.setattr("sys.argv", command + ["--owner-source", "TASK.md", "--feedback-not-due", "The necessary prerequisite is incomplete."])
    assert refs.main() == 0
    assert json.loads(output.read_text())["feedback_not_due"]


def test_due_cli_binding_failure_keeps_draft_and_assignment(repo, monkeypatch, capsys):
    save(repo, frontier_files())
    assignment, draft = repo / "assignment.json", repo / "result.json"
    monkeypatch.setattr("sys.argv", ["frontier_references.py", "resolver", "--repo", str(repo), "--path", "evidence.json",
                                    "--owner-source", "campaign/FRONTIER.md", "--output", str(assignment)])
    assert refs.main() == 0
    before = assignment.read_bytes()
    draft.write_text('{"comparison":"Keep diagnosing."}')
    monkeypatch.setattr("sys.argv", ["frontier_references.py", "bind-resolution", "--repo", str(repo), "--path", "assignment.json",
                                    "--result", str(draft), "--output", str(draft)])
    assert refs.main() == 2
    assert "feedback_decision" in capsys.readouterr().out
    assert assignment.read_bytes() == before
    assert draft.read_text() == '{"comparison":"Keep diagnosing."}'


def test_tampered_basis_and_unlinked_current_work_rejected(repo):
    save(repo, frontier_files())
    prepared = prepare(repo, "HEAD", "evidence.json", owner_source="campaign/FRONTIER.md")
    prepared["objective_basis"]["objective_source"]["section"] = "history"
    with pytest.raises(refs.ReferenceError, match="bindings"):
        refs.bind_resolution(repo, prepared, feedback_result())
    with pytest.raises(refs.ReferenceError, match="linked"):
        prepare(repo, "HEAD", "evidence.json", owner_source="campaign/FRONTIER.md", current_work_source="REPRESENTATION.md")
    valid = prepare(repo, "HEAD", "evidence.json", owner_source="campaign/FRONTIER.md", current_work_source="WORK.md#pending")
    assert valid["objective_basis"]["current_work_source"]["path"] == "campaign/WORK.md"


def test_stripping_objective_fields_cannot_make_a_new_judgment_historical(repo):
    save(repo, {"evidence.json": '{"result":1}'})
    source = refs.reference(repo, "HEAD", "evidence.json")
    fake = {"evidence_source": source, "row": 11}
    with pytest.raises(refs.ReferenceError, match="unchanged saved result"):
        refs.bind_resolution(repo, {"evidence_source": source}, fake)


def test_tampered_supplied_objective_content_rejected(repo):
    save(repo, frontier_files())
    prepared = prepare(repo, "HEAD", "evidence.json", owner_source="campaign/FRONTIER.md")
    prepared["objective_basis_content"]["objective_source"] = "Optimize only the recommended local proxy."
    with pytest.raises(refs.ReferenceError, match="content differs"):
        refs.bind_resolution(repo, prepared, feedback_result())


def test_generic_owner_can_use_existing_relative_sections_without_new_documents(repo):
    save(repo, {"notes/TASK.md": "---\nobjective_basis:\n  objective_source: ../GOAL.md#goal\n  evaluation_source: ../GOAL.md#evaluation\n  current_work_source: '#pending'\nfeedback_not_due: The prerequisite remains incomplete.\n---\n# Work\n## Pending\nImplement the prerequisite.\n",
                "GOAL.md": "# Task\n## Goal\nImprove the real outcome.\n## Evaluation\nUse observed outcomes.\n", "evidence.json": '{}'})
    result = prepare(repo, "HEAD", "evidence.json", owner_source="notes/TASK.md")
    assert result["objective_basis"]["objective_source"]["path"] == "GOAL.md"
    assert result["objective_basis"]["current_work_source"]["section"] == "pending"


def test_old_saved_revision_cannot_prepare_changed_current_owner(repo):
    files = frontier_files()
    original = save(repo, files)
    save(repo, {"campaign/PROBLEM.md": files["campaign/PROBLEM.md"].replace("Improve the real outcome.", "A changed objective.")})
    with pytest.raises(refs.ReferenceError, match="basis changed"):
        prepare(repo, original, "evidence.json", owner_source="campaign/FRONTIER.md")


@pytest.mark.parametrize("before,after", [
    ('Accept exactly `red blue`.', 'Accept exactly `red  blue`.'),
    ('```yaml\ncondition:\n  required: true\n```', '```yaml\ncondition:\nrequired: true\n```'),
])
def test_meaningful_source_whitespace_prevents_reuse_and_binding(repo, before, after):
    files = frontier_files()
    files["campaign/PROBLEM.md"] = files["campaign/PROBLEM.md"].replace(
        "Compare outcomes under the named conditions.", before)
    save(repo, files)
    prepared = prepare(repo, "HEAD", "evidence.json", owner_source="campaign/FRONTIER.md")
    result = refs.bind_resolution(repo, prepared, feedback_result())
    save(repo, {"resolution.json": json.dumps(result),
                "campaign/PROBLEM.md": files["campaign/PROBLEM.md"].replace(before, after)})
    current = prepare(repo, "HEAD", "evidence.json", ["resolution.json"], owner_source="campaign/FRONTIER.md")
    assert current["evidence_state_identity"] == prepared["evidence_state_identity"]
    assert current["objective_basis_identity"] != prepared["objective_basis_identity"]
    assert "reuse_resolution" not in current
    with pytest.raises(refs.ReferenceError, match="basis changed"):
        refs.bind_resolution(repo, prepared, feedback_result())
