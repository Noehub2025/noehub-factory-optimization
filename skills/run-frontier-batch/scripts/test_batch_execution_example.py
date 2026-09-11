"""Exercise the maintained caller in disposable repositories, not project B records."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
import subprocess
import sys

import pytest

import batch_execution_example as example
from frontier_batch import (
    AdoptReview, Batch, CandidateRevision, ConsequenceBlocked, ConsequenceUncertain,
    GitReference, RecordCheck, ReviewAssessment, ReviseBatch, SelectCandidate,
)


def commit_inputs(repo: Path) -> CandidateRevision:
    inputs = sorted(path.name for path in repo.glob("input-*.json"))
    subprocess.run(["git", "-C", str(repo), "add", "--", *inputs], check=True, capture_output=True)
    subprocess.run([
        "git", "-C", str(repo), "-c", "user.name=Example Test",
        "-c", "user.email=example@invalid", "-c", "commit.gpgsign=false",
        "commit", "-qm", "Retain example inputs",
    ], check=True, capture_output=True)
    commit = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    return CandidateRevision(commit, tuple(inputs))


@pytest.mark.parametrize(("statuses", "single_use", "expected", "count"), [
    (("accepted", "accepted", "accepted"), False, "positive", 3),
    (("accepted", "rejected", "accepted"), False, "negative", 2),
    (("accepted", "rejected", "accepted"), True, "negative", 2),
])
def test_real_caller_records_complete_or_negative_prefix(tmp_path, statuses, single_use, expected, count):
    batch = example.prepare_demo(tmp_path, statuses, single_use=single_use)
    if single_use:
        # Leave capacity for another request so this reaches the repeat check.
        definition = dict(batch.view.data["current"]["measurement_definition"])
        definition["resource_ceiling"] = {"records": 2 * len(statuses)}
        batch.apply(ReviseBatch(
            "Isolate single-use protection from capacity exhaustion.",
            resource_limits={"records": 2 * len(statuses)}, measurement_definition=definition,
        ))
    calls = []

    def reader(repo, path, candidate):
        calls.append(path)
        return example.read_input(repo, path, candidate)

    outcome = example.execute(tmp_path, "B001", reader=reader)
    state = Batch.open(tmp_path, "B001").view.data
    assert state["current"]["status"] == "open"  # Worker did not conclude B.
    attempt = state["attempts"][0]
    assert attempt["status"] == "completed"
    assert attempt["result"]["outcome"] == expected
    assert len(calls) == len(attempt["result"]["rows"]) == count
    assert state["consumption"] == {"records": count}
    assert attempt["action"]["required_reviews"] == []
    assert attempt["candidate_revision"] is None
    assert attempt["action"]["possible_consequences"] == (["single_use_consumption"] if single_use else [])
    assert [effect["kind"] for effect in attempt["actual_consequences"]] == (
        ["single_use_consumption"] if single_use else []
    )
    record = tmp_path / "artifacts/frontier/B001/batch.yaml"
    saved = record.read_bytes()
    assert example.read_result(tmp_path, "B001") == outcome.operation_result.result
    assert example.read_result(tmp_path, "B001") == outcome.operation_result.result
    assert record.read_bytes() == saved and len(calls) == count
    if single_use:
        with pytest.raises(ConsequenceBlocked, match="already consumed"):
            example.execute(tmp_path, "B001", reader=reader)
        assert len(calls) == count and record.read_bytes() == saved


def test_selected_inputs_and_required_check_use_real_git_validation(tmp_path):
    batch = example.prepare_demo(tmp_path, ("accepted",))
    selected = commit_inputs(tmp_path)
    batch.apply(SelectCandidate(selected, "Use retained inputs."))
    with pytest.raises(ConsequenceBlocked, match="required check"):
        example.execute(tmp_path, "B001", required_checks=("input-format",))
    assert Batch.open(tmp_path, "B001").view.data["attempts"] == []
    for path in selected.paths:
        assert json.loads(example.read_input(tmp_path, path, selected))["status"] == "accepted"
    batch.apply(RecordCheck("input-format", selected, "passed", {"method": "read selected JSON"}))
    (tmp_path / "input-0.json").write_text('{"status":"rejected"}\n')
    example.execute(tmp_path, "B001", required_checks=("input-format",))
    assert example.read_result(tmp_path, "B001")["outcome"] == "positive"
    attempt = Batch.open(tmp_path, "B001").view.data["attempts"][0]
    assert attempt["candidate_revision"]["commit"] == selected.commit
    assert list(attempt["checks"]) == ["input-format"]


def test_installed_effect_blocks_an_omitted_action_declaration(tmp_path, monkeypatch):
    example.prepare_demo(tmp_path, ("accepted",), single_use=True)
    action_type = example.Action

    def omit_effect(**fields):
        return replace(action_type(**fields), possible_consequences=())

    def forbidden_reader(*args):
        raise AssertionError("installed effect must reject the omission before reading")

    # Fault injection: retain the real adapter installation and Batch checks.
    monkeypatch.setattr(example, "Action", omit_effect)
    with pytest.raises(ConsequenceBlocked, match="undeclared Consequences"):
        example.execute(tmp_path, "B001", reader=forbidden_reader)
    assert Batch.open(tmp_path, "B001").view.data["attempts"] == []


def test_caller_passes_chosen_review_to_owner_and_blocks_before_read(tmp_path):
    batch = example.prepare_demo(tmp_path, ("accepted",))
    selected = commit_inputs(tmp_path)
    batch.apply(SelectCandidate(selected, "Use retained inputs."))
    (tmp_path / "review.md").write_text("Not applicable to this observation.\n")
    subprocess.run(["git", "-C", str(tmp_path), "add", "review.md"], check=True, capture_output=True)
    review_commit = commit_inputs(tmp_path).commit
    reference = GitReference("R001", review_commit, "review.md")
    batch.apply(ReviseBatch("Select the review to check.", reviews=(reference,)))
    calls = []

    class Owner:
        def review(self, retained, action):
            calls.append((retained, action.candidate))
            # A real saved source feeds this deliberately narrow example owner.
            body = subprocess.run([
                "git", "-C", str(tmp_path), "show", f"{retained.commit}:{retained.path}",
            ], check=True, capture_output=True, text=True).stdout
            return ReviewAssessment(False, body.strip())

        def permission(self, *args):
            raise AssertionError("no permission is needed by this example")

    def forbidden_reader(*args):
        raise AssertionError("reader must not run after a rejected review")

    with pytest.raises(ConsequenceBlocked, match="Not applicable"):
        example.execute(tmp_path, "B001", reader=forbidden_reader, required_reviews=("R001",), governance=Owner())
    assert calls == [(reference, selected)]
    assert Batch.open(tmp_path, "B001").view.data["attempts"] == []


def test_adopted_review_is_retained_without_becoming_an_action_gate(tmp_path):
    batch = example.prepare_demo(tmp_path, ("accepted",))
    (tmp_path / "review.md").write_text(
        "---\nreview_id: R001\nreview_result: IMPLEMENTATION_READY\n---\n"
        "Checked an earlier use. That plan required another result review.\n"
    )
    subprocess.run(["git", "-C", str(tmp_path), "add", "review.md"], check=True, capture_output=True)
    review_commit = commit_inputs(tmp_path).commit
    batch.apply(AdoptReview(review_commit, "review.md", "Retain the earlier judgment."))
    retained = Batch.open(tmp_path, "B001").view.data["references"]["reviews"]
    assert retained == [{"handle": "R001", "commit": review_commit, "path": "review.md"}]
    saved_report = (tmp_path / "review.md").read_bytes()

    # The current caller needs no independent judgment. No owner lookup is installed.
    outcome = example.execute(tmp_path, "B001")
    state = Batch.open(tmp_path, "B001").view.data
    assert outcome.operation_result.result["outcome"] == "positive"
    assert state["attempts"][0]["action"]["required_reviews"] == []
    assert state["references"]["reviews"] == retained
    assert state["current"]["status"] == "open"
    assert example.read_result(tmp_path, "B001") == outcome.operation_result.result
    assert (tmp_path / "review.md").read_bytes() == saved_report
    assert len(Batch.open(tmp_path, "B001").view.data["attempts"]) == 1


def test_known_parser_failure_retains_partial_facts_and_can_be_read(tmp_path):
    example.prepare_demo(tmp_path, ("accepted", "unsupported"))
    example.execute(tmp_path, "B001")
    state = Batch.open(tmp_path, "B001").view.data
    assert state["attempts"][0]["status"] == "failed"
    assert state["consumption"] == {"records": 2}
    result = example.read_result(tmp_path, "B001")
    assert result["outcome"] == "support_failure"
    assert result["rows"] == [{"path": "input-0.json", "status": "accepted"}]
    assert result["failure"]["path"] == "input-1.json"
    assert json.loads((tmp_path / "input-1.json").read_bytes())["status"] == "unsupported"
    assert len(Batch.open(tmp_path, "B001").view.data["attempts"]) == 1


def test_unexpected_reader_failure_preserves_uncertainty_and_does_not_retry(tmp_path):
    example.prepare_demo(tmp_path, ("accepted", "accepted"))
    calls = []

    def reader(repo, path, candidate):
        calls.append(path)
        if path == "input-1.json":
            raise RuntimeError("reader interrupted with unresolved effects")
        return example.read_input(repo, path, candidate)

    with pytest.raises(ConsequenceUncertain):
        example.execute(tmp_path, "B001", reader=reader)
    assert len(calls) == 2
    state = Batch.open(tmp_path, "B001").view.data
    assert state["attempts"][0]["status"] == "uncertain"
    assert "reader interrupted" in state["attempts"][0]["adapter_error"]
    assert json.loads((tmp_path / "input-1.json").read_bytes())["status"] == "accepted"
    with pytest.raises(ValueError, match="not settled"):
        example.read_result(tmp_path, "B001")
    with pytest.raises(ConsequenceUncertain):
        example.execute(tmp_path, "B001", reader=reader)
    assert len(calls) == 2
    assert len(Batch.open(tmp_path, "B001").view.data["attempts"]) == 1


def test_cli_demo_uses_the_same_entry_and_finishes(tmp_path):
    completed = subprocess.run(
        [sys.executable, "-B", str(Path(example.__file__)), "--demo"],
        cwd=tmp_path, check=True, capture_output=True, text=True,
    )
    report = json.loads(completed.stdout)
    assert report["status"] == "completed"
    assert report["result"]["outcome"] == "negative"
    assert len(report["result"]["rows"]) == 2
    assert list(tmp_path.iterdir()) == []
