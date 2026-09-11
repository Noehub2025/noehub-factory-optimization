#!/usr/bin/env python3
"""Focused behavioral checks for the deep current Batch module."""

from __future__ import annotations

from dataclasses import replace
import json
import runpy
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from frontier_batch import (
    Action,
    AdoptReview,
    Batch,
    BatchFormatError,
    CandidateRevision,
    ChangeRejected,
    ConcludeBatch,
    Consequence,
    ConsequenceBlocked,
    ConsequenceUncertain,
    DefineBatch,
    GitReference,
    OperationBinding,
    OperationResult,
    OperationContractViolation,
    PermissionAssessment,
    RecordCheck,
    RecordObservation,
    ReconcileAttempt,
    ReviseBatch,
    ReviewAssessment,
    SelectCandidate,
    StorageConflict,
    UpdateWorkingState,
    batch_facts,
)


class Governance:
    def __init__(
        self,
        *,
        review_ready: bool = True,
        permission_ready: bool = True,
        permission_limits: dict[str, int | float] | None = None,
        permitted_consequences: tuple[str, ...] = ("spend",),
    ) -> None:
        self.review_ready = review_ready
        self.permission_ready = permission_ready
        self.permission_limits = permission_limits or {"runs": 2, "proposal": 2}
        self.permitted_consequences = permitted_consequences

    def review(self, reference: GitReference, action: Action) -> ReviewAssessment:
        return ReviewAssessment(self.review_ready, "Review does not apply")

    def permission(
        self,
        reference: GitReference,
        action: Action,
        actual_consumption: dict[str, int | float],
    ) -> PermissionAssessment:
        return PermissionAssessment(
            self.permission_ready,
            "Permission does not allow this action",
            self.permission_limits,
            self.permitted_consequences,
        )


class BatchModuleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.repo = Path(self.temporary.name)
        self._git("init", "-q")
        self._git("config", "user.email", "batch@example.invalid")
        self._git("config", "user.name", "Batch Test")
        (self.repo / "src").mkdir()
        (self.repo / "src" / "candidate.txt").write_text("first\n", encoding="utf-8")
        (self.repo / "records").mkdir()
        (self.repo / "records" / "R001.md").write_text("review\n", encoding="utf-8")
        (self.repo / "records" / "V001.yaml").write_text("permission: true\n", encoding="utf-8")
        self._git("add", "src/candidate.txt", "records/R001.md", "records/V001.yaml")
        self._git("commit", "-qm", "initial")
        self.first_commit = self._git("rev-parse", "HEAD")
        self.state_path = self.repo / "artifacts" / "frontier" / "B001" / "batch.yaml"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _git(self, *arguments: str) -> str:
        return subprocess.run(
            ["git", "-C", str(self.repo), *arguments],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    def _reference(self, handle: str, path: str) -> GitReference:
        return GitReference(handle, self.first_commit, path)

    def _candidate(self, commit: str | None = None) -> CandidateRevision:
        return CandidateRevision(commit or self.first_commit, ("src/candidate.txt",))

    def test_candidate_git_checks_are_batched_and_preserve_path_boundaries(self):
        paths = tuple(f"src/item {index}.txt" for index in range(28)) + ("src/line\nbreak.txt",)
        for path in paths:
            (self.repo / path).write_text("retained input\n")
        self._git("add", "src")
        self._git("commit", "-qm", "many input paths")
        commit = self._git("rev-parse", "HEAD")
        batch = self._defined_batch()
        for selected in (paths[:1], paths):
            with self.subTest(paths=len(selected)):
                with patch("frontier_batch.subprocess.run", wraps=subprocess.run) as git:
                    batch.apply(SelectCandidate(CandidateRevision(commit, selected), "Select inputs."))
                self.assertEqual(git.call_count, 2)
                self.assertIn("--batch-check=%(objectname)", git.call_args.args[0])
                self.assertEqual(git.call_args.kwargs["input"].count(b"\0"), len(selected))
        # Existence at a saved commit remains distinct from current working bytes.
        (self.repo / paths[0]).write_text("uncommitted edit\n")
        batch.apply(RecordCheck("saved-object-only", CandidateRevision(commit, paths), "passed"))
        self.assertEqual(batch.view.data["attempts"], [])

    def test_batched_candidate_rejects_bad_inputs_without_writing(self):
        batch = self._defined_batch()
        original = self.state_path.read_bytes()
        invalid = (
            CandidateRevision("0" * 40, ("src/candidate.txt",)),
            CandidateRevision("HEAD", ("src/candidate.txt",)),
            CandidateRevision(self.first_commit, ("src/candidate.txt", "src/missing.txt")),
            CandidateRevision(self.first_commit, ("../outside",)),
            CandidateRevision(self.first_commit, ("src/candidate.txt", "src/candidate.txt")),
            CandidateRevision(self.first_commit, ()),
        )
        for candidate in invalid:
            with self.subTest(candidate=candidate):
                with self.assertRaises(BatchFormatError):
                    batch.apply(SelectCandidate(candidate, "Invalid selection."))
                self.assertEqual(self.state_path.read_bytes(), original)

    def test_candidate_batching_does_not_cache_current_governance(self):
        calls = []
        owner = Governance()

        def observe(action, context):
            calls.append(action.key)
            return OperationResult(status="completed", resource_use={"runs": 1})

        batch = self._defined_batch(
            governance=owner, operations={"observe": self._operation(observe, ("spend",))},
        )
        candidate = self._candidate()
        batch.apply(SelectCandidate(candidate, "Select inputs."))
        batch.apply(RecordCheck("ready", candidate, "passed"))
        action = Action(
            key="observe", operation="observe", kind="local", candidate=candidate,
            required_checks=("ready",), required_reviews=("R001",),
            required_permissions=("V001",), requested_resources={"runs": 1},
            possible_consequences=("spend",), repeatable=True,
        )
        batch.perform(action)
        owner.review_ready = False
        with self.assertRaisesRegex(ConsequenceBlocked, "Review does not apply"):
            batch.perform(action)
        owner.review_ready = True
        owner.permission_ready = False
        with self.assertRaisesRegex(ConsequenceBlocked, "Permission does not allow"):
            batch.perform(action)
        owner.permission_ready = True
        batch.apply(ReviseBatch(rationale="No remaining allocation.", resource_limits={"runs": 1}))
        with self.assertRaisesRegex(ConsequenceBlocked, "resource limit"):
            batch.perform(action)
        self.assertEqual(calls, ["observe"])
        self.assertEqual(len(batch.view.data["attempts"]), 1)

    def test_peak_constraints_leave_cumulative_accounting_without_rewriting_history(self):
        observed = []

        def observe(action, context):
            definition = context["measurement_definition"]
            peak_limit = definition.get("run_spec", {}).get("parallel_limit")
            if peak_limit is not None:
                self.assertEqual(peak_limit, 2)
                self.assertNotIn("parallel_peak", action.requested_resources)
            observed.append(context["attempt"])
            # This serial fixture needs one worker, below its runtime limit.
            return OperationResult(
                status="completed",
                resource_use={"runs": 1, **({"parallel_peak": 2} if peak_limit is None else {})},
                observations=({"observed_parallel_peak": 1, "estimated_helper_starts_upper": 8},),
            )

        batch = self._defined_batch(
            operations={"observe": self._operation(observe)},
            resource_limits={"runs": 4, "parallel_peak": 2}, expected_consequences=(),
        )
        batch.apply(ReviseBatch(
            rationale="Retained historical accounting.",
            measurement_definition=self._measurement(resource_ceiling={"runs": 4, "parallel_peak": 2}),
        ))
        candidate = self._candidate()
        batch.apply(SelectCandidate(candidate, "Select working material."))
        batch.apply(RecordCheck("ready", candidate, "passed"))
        action = Action(
            key="observe", operation="observe", kind="measurement", candidate=candidate,
            required_checks=("ready",), requested_resources={"runs": 1, "parallel_peak": 2},
            repeatable=True,
        )
        batch.perform(action)
        history = batch.view.data["attempts"][0]
        checks = batch.view.data["current"]["checks"]
        references = batch.view.data["references"]
        with self.assertRaisesRegex(ConsequenceBlocked, "resource limit"):
            batch.perform(action)
        # Replace both current limit maps; old Attempt facts remain untouched.
        batch.apply(ReviseBatch(
            rationale="Keep the peak as an operating constraint, not cumulative use.",
            resource_limits={"runs": 4},
            measurement_definition=self._measurement(
                resource_ceiling={"runs": 4}, run_spec={"parallel_limit": 2},
            ),
        ))
        action = replace(action, requested_resources={"runs": 1})
        for _ in range(2):
            batch.apply(RecordCheck("release", candidate, "passed", {"state": "ready"}))
            batch.perform(action)
        saved = Batch.open(self.repo, "B001", state_path=self.state_path).view
        self.assertEqual(observed, [1, 2, 3])
        self.assertEqual(saved.data["attempts"][0], history)
        self.assertEqual(saved.data["consumption"], {"runs": 3, "parallel_peak": 2})
        self.assertEqual(batch_facts(saved)["remaining_capacity"], {"runs": 1})
        self.assertEqual(saved.data["references"], references)
        self.assertEqual(saved.data["current"]["checks"]["ready"], checks["ready"])
        for attempt in saved.data["attempts"][1:]:
            self.assertEqual(attempt["resource_use"], {"runs": 1})
            self.assertEqual(attempt["observations"][0]["observed_parallel_peak"], 1)
            self.assertEqual(attempt["actual_consequences"], [])

    def _defined_batch(
        self,
        *,
        governance: Governance | None = None,
        operations: dict | None = None,
        resource_limits: dict[str, int | float] | None = None,
        expected_consequences: tuple[str, ...] = ("spend",),
    ) -> Batch:
        batch = Batch.open(
            self.repo,
            "B001",
            state_path=self.state_path,
            governance=governance,
            operations=operations,
        )
        batch.apply(
            DefineBatch(
                objective="Improve the retained result.",
                acceptance="Produce a decision-relevant result.",
                scope=("local work", "local measurement"),
                reviews=(self._reference("R001", "records/R001.md"),),
                permissions=(self._reference("V001", "records/V001.yaml"),),
                resource_limits=resource_limits or {"runs": 2, "proposal": 2},
                expected_consequences=expected_consequences,
            )
        )
        return batch

    def _operation(
        self,
        run,
        protected_consequences: tuple[str, ...] = (),
    ) -> OperationBinding:
        return OperationBinding(run, protected_consequences)

    def _save_review(self, handle="R002", result="IMPLEMENTATION_READY"):
        path = f"records/{handle}.md"
        (self.repo / path).write_text(
            f"---\nreview_id: {handle}\nreview_result: {result}\n---\nOriginal professional conclusion.\n",
            encoding="utf-8",
        )
        self._git("add", path)
        self._git("commit", "-qm", "saved review")
        return path

    def _reference_cli(self, *arguments, success=True):
        script = Path(__file__).with_name("frontier_references.py")
        result = subprocess.run(
            [sys.executable, "-B", str(script), *arguments, "--repo", str(self.repo), "--batch", "B001"],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0 if success else 2, result.stderr + result.stdout)
        return json.loads(result.stdout)

    def test_saved_review_adoption_reads_source_without_copying_verdict(self):
        batch = self._defined_batch()
        path = self._save_review(result="IMPLEMENTATION_REPAIR_REQUIRED")
        saved = self._git("rev-parse", "HEAD")
        (self.repo / path).write_text("unreviewed working edits\n", encoding="utf-8")
        result = batch.apply(AdoptReview(saved, path, "Retain the scoped finding."))
        self.assertEqual(result.data["references"]["reviews"][-1], {
            "handle": "R002", "commit": saved, "path": path,
        })
        self.assertEqual(result.data["current"]["observations"], {})
        self.assertEqual(result.data["consumption"], {})
        self.assertEqual(result.data["attempts"], [])
        before = self.state_path.read_bytes()
        batch.apply(AdoptReview(saved, path, "A repeated request."))
        self.assertEqual(before, self.state_path.read_bytes())
        with self.assertRaisesRegex(ValueError, "differs"):
            batch.apply(AdoptReview(saved, path, "Wrong selected handle.", "R003"))
        self.assertEqual(before, self.state_path.read_bytes())

    def test_working_delta_reads_latest_state_and_repeated_selection_preserves_checks(self):
        stale = self._defined_batch()
        stale.apply(SelectCandidate(self._candidate(), "Select working bytes."))
        stale.apply(RecordCheck("ready", self._candidate(), "passed"))
        path = self._save_review()
        other = Batch.open(self.repo, "B001")
        other.apply(AdoptReview("HEAD", path, "Adopt another applicable review."))
        other.apply(UpdateWorkingState("Add an internal resource.", resource_limits={"calls": 8}))
        stale.apply(UpdateWorkingState(
            "Revise one internal allowance.", revision=self.first_commit,
            paths=("src/candidate.txt",), resource_limits={"runs": 4},
        ))
        data = stale.view.data
        self.assertEqual(data["resource_limits"], {"runs": 4, "proposal": 2, "calls": 8})
        self.assertEqual(len(data["references"]["reviews"]), 2)
        self.assertIn("ready", data["current"]["checks"])
        before = self.state_path.read_bytes()
        stale.apply(UpdateWorkingState(
            "Repeat without resetting checks.", revision=self.first_commit,
            paths=("src/candidate.txt",), resource_limits={"runs": 4},
        ))
        self.assertEqual(before, self.state_path.read_bytes())
        self.assertEqual(data["consumption"], {})

    def test_working_delta_validates_candidate_and_measurement_before_one_save(self):
        batch = self._defined_batch()
        batch.apply(SelectCandidate(self._candidate(), "Initial selection."))
        batch.apply(RecordCheck("ready", self._candidate(), "passed"))
        batch.apply(ReviseBatch("Define measurement.", measurement_definition=self._measurement()))
        (self.repo / "src/candidate.txt").write_text("second\n", encoding="utf-8")
        self._git("add", "src/candidate.txt")
        self._git("commit", "-qm", "changed working input")
        before = self.state_path.read_bytes()
        with self.assertRaises(BatchFormatError):
            batch.apply(UpdateWorkingState(
                "Invalid combined change.", revision="HEAD", paths=("src/candidate.txt",),
                resource_limits={"runs": 4}, measurement_updates={"resource_ceiling": {"runs": -1}},
            ))
        self.assertEqual(before, self.state_path.read_bytes())
        update = UpdateWorkingState(
            "Bind working inputs and affected measurement together.", revision="HEAD",
            paths=("src/candidate.txt",), resource_limits={"runs": 4},
            measurement_updates={"resource_ceiling": {"runs": 3}},
        )
        import frontier_batch
        with patch.object(frontier_batch, "_write_state", wraps=frontier_batch._write_state) as writer:
            batch.apply(update)
            self.assertEqual(writer.call_count, 1)
        self.assertEqual(batch.view.data["current"]["checks"], {})
        self.assertEqual(batch.view.data["current"]["measurement_definition"]["question"], self._measurement()["question"])
        self.assertEqual(batch.view.data["current"]["candidate_revision"]["commit"], self._git("rev-parse", "HEAD"))

    def test_failed_working_save_leaves_original_state_and_can_resume(self):
        batch = self._defined_batch()
        before = self.state_path.read_bytes()
        update = UpdateWorkingState("Adjust local work.", resource_limits={"runs": 5})
        with patch("frontier_batch.os.replace", side_effect=OSError("write unavailable")):
            with self.assertRaises(StorageConflict):
                batch.apply(update)
        self.assertEqual(before, self.state_path.read_bytes())
        self.assertEqual(batch.view.data["resource_limits"]["runs"], 2)
        batch.apply(update)
        self.assertEqual(batch.view.data["resource_limits"]["runs"], 5)

    def test_batch_facts_use_attempts_not_copied_campaign_totals(self):
        batch = self._defined_batch(operations={"observe": self._operation(
            lambda action, context: OperationResult(status="uncertain", recovery_condition="Read retained output."),
        )})
        batch.apply(RecordObservation("old-summary", {
            "proposal_events_after": 900, "remaining": 500, "actual": None,
        }))
        batch.apply(ReviseBatch("Define observation.", measurement_definition=self._measurement()))
        with self.assertRaises(ConsequenceUncertain):
            batch.perform(Action(key="one", kind="measurement", operation="observe", requested_resources={"runs": 1}))
        facts = batch_facts(batch.view)
        self.assertEqual(facts["attempt_consumption"], {})
        self.assertEqual(facts["unresolved_attempts"], [1])
        self.assertNotIn("proposal_events_after", facts)
        self.assertIsNone(batch.view.data["current"]["observations"]["old-summary"]["observation"]["actual"])
        before = self.state_path.read_bytes()
        self._reference_cli("batch-view")
        self._reference_cli("batch-view")
        self.assertEqual(before, self.state_path.read_bytes())

    def test_standard_entry_replaces_old_gate_without_replan_or_charge(self):
        batch = self._defined_batch()
        path = self._save_review()
        # Retained caller reproduces the old dispatch mistake before replacement.
        old = self.repo / "old_select.py"
        old.write_text(
            "from frontier_batch import Batch\nfrom pathlib import Path\n"
            "state = Batch.open(Path(__file__).parent, 'B001').view.data\n"
            "if not any(r['handle'] == 'R999' for r in state['references']['reviews']):\n"
            "    raise ValueError('strategic replan required')\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "strategic replan"):
            runpy.run_path(str(old))
        original = old.read_bytes()
        self._reference_cli("batch-review", "--path", path, "--revision", "HEAD", "--reason", "Adopt chosen review.")
        result = self._reference_cli(
            "batch-update", "--revision", "HEAD", "--candidate-path", "src/candidate.txt",
            "--limit", "runs=4", "--reason", "Continue the same internal work.",
        )
        self.assertEqual(result["resource_limits"]["runs"], 4)
        self.assertEqual(result["candidate_revision"]["commit"], self._git("rev-parse", "HEAD"))
        self.assertEqual(result["attempt_consumption"], {})
        self.assertNotIn("R999", [r["handle"] for r in result["reviews"]])
        self.assertEqual(original, old.read_bytes())
        before = self.state_path.read_bytes()
        self._reference_cli("batch-update", "--limit", "runs=-1", "--reason", "Invalid input.", success=False)
        self.assertEqual(before, self.state_path.read_bytes())

    def _measurement(self, mode: str = "diagnostic-only", **overrides) -> dict:
        definition = {
            "mode": mode,
            "question": "Does the selected change improve the target?",
            "comparator": "retained baseline",
            "metric": "score",
            "scope": "local",
            "resource_ceiling": {"runs": 2},
            "execution_owner": "test adapter",
            "evidence_limit": "Batch evidence only",
            "interpretation_limit": "No broader performance claim",
            "result_owner": "B",
        }
        definition.update(overrides)
        return definition

    def _single_use_measurement(self, **overrides) -> dict:
        fields = {
            "nonrepeatable_unit": "one scheduled run",
            "resource_owner": "workflow",
            "consumption_control": "Attempt",
        }
        fields.update(overrides)
        return self._measurement(**fields)

    def _saved_entry_case(self, *, uncertain: bool = False):
        """Exercise the existing owner seam with a real Git-backed subject."""
        case = self
        calls = []

        class SavedReviewOwner(Governance):
            def review(self, reference, action):
                report = yaml.safe_load(case._git("show", f"{reference.commit}:{reference.path}"))
                saved = yaml.safe_load(case._git(
                    "show", f"{report['subject_commit']}:{report['subject_path']}"
                ))
                current = Batch.open(case.repo, "B001", state_path=case.state_path).view.data
                # This fixture reviews its objective, measurement and chosen revision.
                # It is not a universal projection or field list for project adapters.
                if current["definition"]["objective"] != saved["definition"]["objective"]:
                    return ReviewAssessment(False, "reviewed objective changed")
                if current["current"]["measurement_definition"] != saved["current"]["measurement_definition"]:
                    return ReviewAssessment(False, "reviewed measurement changed")
                candidate = saved["current"]["candidate_revision"]
                if action.candidate != CandidateRevision(candidate["commit"], tuple(candidate["paths"])):
                    return ReviewAssessment(False, "reviewed implementation changed")
                return ReviewAssessment(True)

        def observe(action, context):
            calls.append(action.key)
            return OperationResult(
                status="uncertain" if uncertain else "completed",
                resource_use={"runs": 1},
                recovery_condition="Resolve the observation." if uncertain else None,
            )

        owner = SavedReviewOwner()
        batch = self._defined_batch(
            governance=owner,
            operations={"observe": self._operation(observe)},
            resource_limits={"runs": 3},
        )
        batch.apply(ReviseBatch(
            rationale="Prepare the subject before Entry review exists.",
            reviews=(),
            measurement_definition=self._measurement(resource_ceiling={"runs": 3}),
        ))
        batch.apply(SelectCandidate(self._candidate(), "review this revision"))
        batch.apply(RecordCheck("focused", self._candidate(), "passed"))
        subject_path = self.state_path.relative_to(self.repo).as_posix()
        self._git("add", subject_path)
        self._git("commit", "-qm", "save review subject")
        subject_commit = self._git("rev-parse", "HEAD")
        (self.repo / "records/R002.yaml").write_text(yaml.safe_dump({
            "subject_commit": subject_commit, "subject_path": subject_path,
        }))
        self._git("add", "records/R002.yaml")
        self._git("commit", "-qm", "save Entry review")
        review = GitReference("R002", self._git("rev-parse", "HEAD"), "records/R002.yaml")
        action = Action(
            key="observe-reviewed", operation="observe", kind="measurement",
            candidate=self._candidate(), required_reviews=("R002",),
            required_checks=("focused",), requested_resources={"runs": 1},
        )
        return batch, owner, review, action, calls

    def test_saved_review_adoption_and_progress_allow_execution(self) -> None:
        batch, owner, review, action, calls = self._saved_entry_case()
        reviewed_bytes = self.state_path.read_bytes()
        batch.apply(ReviseBatch(rationale="Adopt Entry.", reviews=(review,)))
        self.assertNotEqual(self.state_path.read_bytes(), reviewed_bytes)
        first = batch.perform(action)
        batch.apply(RecordObservation("progress", {"completed": "first observation"}))
        batch.apply(ReviseBatch(rationale="Allocate remaining local work.", resource_limits={"runs": 2}))
        self.assertTrue(owner.review(review, action).applies)
        second = batch.perform(replace(action, key="another-observation"))
        self.assertEqual((first.attempt, second.attempt), (1, 2))
        self.assertEqual(calls, ["observe-reviewed", "another-observation"])
        batch.apply(ReviseBatch(rationale="Restore available allocation.", resource_limits={"runs": 3}))
        with self.assertRaisesRegex(ConsequenceBlocked, "already completed"):
            batch.perform(action)
        self.assertEqual(batch.view.data["consumption"], {"runs": 2})

    def test_saved_review_rejects_changed_decision_meaning(self) -> None:
        batch, owner, review, action, calls = self._saved_entry_case()
        batch.apply(ReviseBatch(rationale="Adopt Entry.", reviews=(review,)))
        original = batch.view.data
        changes = (
            (ReviseBatch(rationale="Change target.", objective="A different objective."), "objective"),
            (ReviseBatch(rationale="Change measurement.", measurement_definition=self._measurement(
                metric="different metric", resource_ceiling={"runs": 3}
            )), "measurement"),
        )
        for change, reason in changes:
            with self.subTest(reason=reason):
                batch.apply(change)
                with self.assertRaisesRegex(ConsequenceBlocked, f"reviewed {reason} changed"):
                    batch.perform(action)
                batch.apply(ReviseBatch(
                    rationale="Restore the reviewed decision.",
                    objective=original["definition"]["objective"],
                    measurement_definition=original["current"]["measurement_definition"],
                ))
        self.assertEqual(calls, [])
        self.assertEqual(batch.view.data["attempts"], [])

    def test_saved_review_does_not_cover_new_implementation(self) -> None:
        batch, owner, review, action, calls = self._saved_entry_case()
        batch.apply(ReviseBatch(rationale="Adopt Entry.", reviews=(review,)))
        (self.repo / "src/candidate.txt").write_text("changed implementation\n")
        self._git("add", "src/candidate.txt")
        self._git("commit", "-qm", "change implementation")
        candidate = self._candidate(self._git("rev-parse", "HEAD"))
        batch.apply(SelectCandidate(candidate, "new working revision"))
        with self.assertRaises(ConsequenceBlocked):
            batch.perform(action)
        batch.apply(RecordCheck("focused", candidate, "passed"))
        with self.assertRaisesRegex(ConsequenceBlocked, "reviewed implementation changed"):
            batch.perform(replace(action, candidate=candidate))
        self.assertEqual(calls, [])
        self.assertEqual(batch.view.data["attempts"], [])

    def test_saved_review_adoption_keeps_current_runtime_guards(self) -> None:
        batch, owner, review, action, calls = self._saved_entry_case(uncertain=True)
        self.assertTrue(owner.review(review, action).applies)
        with self.assertRaisesRegex(ConsequenceBlocked, "not referenced"):
            batch.perform(action)
        batch.apply(ReviseBatch(rationale="Adopt Entry.", reviews=(review,)))
        batch.apply(ReviseBatch(rationale="Withdraw the adopted reference.", reviews=()))
        with self.assertRaisesRegex(ConsequenceBlocked, "not referenced"):
            batch.perform(action)
        batch.apply(ReviseBatch(rationale="Restore the applicable reference.", reviews=(review,)))
        owner.permission_ready = False
        with self.assertRaisesRegex(ConsequenceBlocked, "Permission does not allow"):
            batch.perform(replace(action, required_permissions=("V001",)))
        owner.permission_ready = True
        batch.apply(ReviseBatch(rationale="No capacity allocated.", resource_limits={"runs": 0}))
        with self.assertRaises(ConsequenceBlocked):
            batch.perform(action)
        batch.apply(ReviseBatch(rationale="Restore allocation.", resource_limits={"runs": 3}))
        batch.apply(RecordCheck("focused", action.candidate, "failed"))
        with self.assertRaisesRegex(ConsequenceBlocked, "has not passed"):
            batch.perform(action)
        batch.apply(RecordCheck("focused", action.candidate, "passed"))
        self.assertEqual(calls, [])
        self.assertEqual(batch.view.data["attempts"], [])
        with self.assertRaises(ConsequenceUncertain):
            batch.perform(action)
        batch.apply(RecordObservation("progress", {"next": "resolve uncertainty"}))
        with self.assertRaises(ConsequenceUncertain):
            batch.perform(replace(action, key="renamed-observation"))
        self.assertEqual(calls, [action.key])
        self.assertEqual(len(batch.view.data["attempts"]), 1)

    def test_saved_review_readiness_before_adoption_is_read_only(self) -> None:
        batch, owner, review, action, calls = self._saved_entry_case()
        # Reading the saved Review does not require a matching working copy.
        (self.repo / review.path).write_text("unrelated working draft\n")

        def files():
            return {p.relative_to(self.repo): p.read_bytes() for p in self.repo.rglob("*")
                    if p.is_file() and ".git" not in p.relative_to(self.repo).parts}

        before = files()
        self.assertTrue(owner.review(review, action).applies)
        self.assertEqual(files(), before)
        self.assertEqual(batch.view.data["references"]["reviews"], [])
        self.assertEqual(batch.view.data["attempts"], [])
        self.assertEqual(batch.view.data["consumption"], {})
        self.assertEqual(calls, [])
        batch.apply(ReviseBatch(rationale="Adopt the saved Review.", reviews=(review,)))
        self.assertEqual(batch.perform(action).attempt, 1)

    def test_routine_revisions_and_candidate_changes_stay_in_one_batch(self) -> None:
        batch = self._defined_batch()
        batch.apply(SelectCandidate(self._candidate(), "first revision"))
        batch.apply(RecordCheck("focused", self._candidate(), "failed"))

        (self.repo / "src" / "candidate.txt").write_text("second\n", encoding="utf-8")
        self._git("add", "src/candidate.txt")
        self._git("commit", "-qm", "repair")
        second_commit = self._git("rev-parse", "HEAD")
        second = self._candidate(second_commit)
        batch.apply(SelectCandidate(second, "repair the failed check"))
        view = batch.apply(RecordCheck("focused", second, "passed"))

        self.assertEqual(view.batch, "B001")
        self.assertEqual(view.data["attempts"], [])
        self.assertEqual(view.data["current"]["checks"]["focused"]["outcome"], "passed")
        self.assertEqual(view.data["current"]["candidate_revision"]["commit"], second_commit)

    def test_existing_repair_gate_and_proposal_writer_can_be_replaced_in_same_batch(self) -> None:
        """Test owner-driven repair, not automatic inference of obsolete policy."""
        writer = self.repo / "support_writer.py"
        imports = "from frontier_batch import SelectCandidate, RecordObservation\n"
        legacy = imports + (
            "def select(batch, candidate):\n"
            "    state = batch.view.data\n"
            "    if state['resource_limits']['revision_slots'] <= 1:\n"
            "        raise ValueError('internal revision allowance exhausted')\n"
            "    if not any(r['handle'] == 'R002' for r in state['references']['reviews']):\n"
            "        raise ValueError('exact new Replan required')\n"
            "    batch.apply(SelectCandidate(candidate, 'legacy selection'))\n"
            "    batch.apply(RecordObservation('new-proposal', {'proposal_event_delta': 1}))\n"
        )
        writer.write_text(legacy, encoding="utf-8")
        self._git("add", "support_writer.py")
        self._git("commit", "-qm", "retained restrictive writer")
        prior = CandidateRevision(
            self._git("rev-parse", "HEAD"), ("src/candidate.txt", "support_writer.py")
        )
        batch = self._defined_batch(
            resource_limits={"runs": 2, "revision_slots": 1},
            expected_consequences=(),
        )
        batch.apply(SelectCandidate(prior, "retained work"))
        batch.apply(RecordCheck("candidate", prior, "passed"))
        batch.apply(RecordObservation("earlier-selection", {"proposal_event_delta": 1}))
        batch.apply(ReviseBatch(
            rationale="Retain the public development question.",
            measurement_definition=self._measurement(),
        ))
        before = batch.view.data
        self._git("add", str(self.state_path.relative_to(self.repo)))
        self._git("commit", "-qm", "retain the blocked Batch")
        blocked_commit = self._git("rev-parse", "HEAD")
        retained_state = self._git("show", f"{blocked_commit}:{self.state_path.relative_to(self.repo)}")

        old_select = runpy.run_path(str(writer))["select"]
        with self.assertRaisesRegex(ValueError, "allowance exhausted"):
            old_select(batch, prior)
        batch.apply(ReviseBatch(
            rationale="Adjust an internal allowance for the same investment.",
            resource_limits={"runs": 2, "revision_slots": 2},
        ))
        # Updating prose or the cap alone leaves the real writer blocked.
        with self.assertRaisesRegex(ValueError, "new Replan required"):
            old_select(batch, prior)
        self.assertEqual(batch.view.data["attempts"], [])

        repaired = imports + (
            "def select(batch, candidate):\n"
            "    batch.apply(SelectCandidate(candidate, 'same-result support repair'))\n"
            "def inspect(action, context):\n"
            "    from frontier_batch import OperationResult\n"
            "    return OperationResult(status='completed', resource_use={'runs': 1},\n"
            "        result={'observation': 'development only', 'independent_confirmation': False})\n"
        )
        writer.write_text(repaired, encoding="utf-8")
        self._git("add", "support_writer.py")
        self._git("commit", "-qm", "replace obsolete gate and proposal writeback")
        current = CandidateRevision(self._git("rev-parse", "HEAD"), prior.paths)
        adapter = runpy.run_path(str(writer))
        batch = Batch.open(
            self.repo, "B001", state_path=self.state_path,
            operations={"inspect": self._operation(adapter["inspect"])},
        )
        adapter["select"](batch, current)
        self.assertEqual(batch.view.data["current"]["checks"], {})
        action = Action(
            key="development", operation="inspect", kind="measurement",
            candidate=current, required_checks=("candidate", "support"),
            requested_resources={"runs": 1}, repeatable=True,
        )
        with self.assertRaises(ConsequenceBlocked):
            batch.perform(action)
        self.assertEqual(batch.view.data["attempts"], [])

        self.assertEqual(self._git("diff", prior.commit, current.commit, "--", "src/candidate.txt"), "")
        batch.apply(RecordCheck("candidate", current, "passed", {
            "retained_check": before["current"]["checks"]["candidate"],
            "unchanged_dependencies": ["src/candidate.txt"],
        }))
        batch.apply(RecordCheck("support", current, "passed", {
            "checked": "repaired selector executed without Replan or charge writeback",
        }))
        self.assertEqual(batch.view.data["current"]["observations"], before["current"]["observations"])
        self.assertEqual(batch.view.data["references"], before["references"])
        self.assertEqual(batch.view.data["consumption"], {})
        first = batch.perform(action)
        second = batch.perform(action)
        self.assertEqual((first.attempt, second.attempt), (1, 2))
        self.assertEqual(second.view.data["consumption"], {"runs": 2})
        self.assertNotIn("new-proposal", second.view.data["current"]["observations"])
        self.assertFalse(second.view.data["attempts"][-1]["result"]["independent_confirmation"])
        self.assertEqual(self._git("show", f"{blocked_commit}:{self.state_path.relative_to(self.repo)}"), retained_state)

    def test_retained_derivation_repair_preserves_raw_failure_without_new_attempt(self) -> None:
        batch = self._defined_batch(expected_consequences=())
        raw = {"values": [3, 5]}
        batch.apply(RecordObservation("original", {
            "raw": raw, "support_failure": "unsupported response shape", "count": None,
        }))
        original = batch.view.data["current"]["observations"]["original"]
        batch.apply(RecordObservation("corrected", {
            "source_observation": "original", "count": len(raw["values"]),
            "support": "repaired", "performance_inference": "unresolved",
        }))
        state = batch.view.data
        self.assertEqual(state["current"]["observations"]["original"], original)
        self.assertIsNone(original["observation"]["count"])
        self.assertEqual(state["current"]["observations"]["corrected"]["observation"]["count"], 2)
        self.assertEqual(state["attempts"], [])
        self.assertEqual(state["consumption"], {})

    def test_current_state_has_no_parallel_identity_chain(self) -> None:
        batch = self._defined_batch()
        batch.apply(SelectCandidate(self._candidate(), "ready"))
        raw = self.state_path.read_text(encoding="utf-8")

        for forbidden in (
            "batch_plan_id",
            "acknowledgment_id",
            "execution_start_id",
            "result_packet_id",
            "decision_root",
            "authority_root",
            "execution_root",
            "outcome_root",
        ):
            self.assertNotIn(forbidden, raw)

    def test_open_rejects_consumption_that_disagrees_with_attempts(self) -> None:
        batch = self._defined_batch()
        state = yaml.safe_load(self.state_path.read_text())
        state["consumption"] = {"runs": 1}
        self.state_path.write_text(yaml.safe_dump(state, sort_keys=False))

        with self.assertRaisesRegex(Exception, "sum of Attempt resource use"):
            Batch.open(self.repo, "B001", state_path=self.state_path)

    def test_harmless_operation_creates_no_attempt(self) -> None:
        calls: list[str] = []

        def inspect(action: Action, context: dict) -> OperationResult:
            calls.append(action.key)
            return OperationResult(
                status="completed",
                observations=({"finding": "reachable"},),
                result={"ready": True},
            )

        batch = self._defined_batch(operations={"inspect": self._operation(inspect)})
        outcome = batch.perform(Action(key="inspect-working", operation="inspect", kind="check"))

        self.assertEqual(calls, ["inspect-working"])
        self.assertIsNone(outcome.attempt)
        self.assertEqual(outcome.view.data["attempts"], [])

    def test_measurement_attempt_binds_revision_checks_and_real_consumption(self) -> None:
        def measure(action: Action, context: dict) -> OperationResult:
            self.assertEqual(context["attempt"], 1)
            return OperationResult(
                status="completed",
                observations=({"score": 1.0},),
                consequences=(Consequence("spend", amount=1),),
                resource_use={"runs": 1, "proposal": 1},
                result={"comparison": "positive"},
            )

        batch = self._defined_batch(
            governance=Governance(),
            operations={"measure": self._operation(measure, ("spend",))},
        )
        candidate = self._candidate()
        batch.apply(SelectCandidate(candidate, "measurement revision"))
        batch.apply(RecordCheck("integration", candidate, "passed"))
        batch.apply(
            ReviseBatch(
                rationale="Set the Batch-owned measurement meaning.",
                measurement_definition=self._measurement(),
            )
        )
        outcome = batch.perform(
            Action(
                key="direct-comparison",
                operation="measure",
                kind="measurement",
                candidate=candidate,
                required_reviews=("R001",),
                required_permissions=("V001",),
                required_checks=("integration",),
                requested_resources={"runs": 1, "proposal": 1},
                possible_consequences=("spend",),
            )
        )

        self.assertEqual(outcome.attempt, 1)
        attempt = outcome.view.data["attempts"][0]
        self.assertEqual(attempt["candidate_revision"]["commit"], self.first_commit)
        self.assertEqual(attempt["checks"]["integration"]["outcome"], "passed")
        self.assertEqual(attempt["actual_consequences"][0]["kind"], "spend")
        self.assertEqual(outcome.view.data["consumption"], {"runs": 1, "proposal": 1})

    def test_permission_blocks_only_action_before_adapter_runs(self) -> None:
        calls: list[str] = []

        def operation(action: Action, context: dict) -> OperationResult:
            calls.append(action.key)
            return OperationResult(status="completed")

        batch = self._defined_batch(
            governance=Governance(permission_ready=False),
            operations={"external": self._operation(operation, ("spend",))},
        )
        with self.assertRaisesRegex(ConsequenceBlocked, "Permission does not allow"):
            batch.perform(
                Action(
                    key="submit",
                    operation="external",
                    kind="external",
                    required_permissions=("V001",),
                    possible_consequences=("spend",),
                )
            )

        self.assertEqual(calls, [])
        self.assertEqual(batch.view.status, "open")
        self.assertEqual(batch.view.data["attempts"], [])

    def test_measurement_reads_the_batch_definition_for_all_current_modes(self) -> None:
        observed: list[str] = []

        def measure(action: Action, context: dict) -> OperationResult:
            observed.append(context["measurement_definition"]["mode"])
            return OperationResult(status="completed", resource_use={"runs": 1})

        batch = self._defined_batch(
            operations={"measure": self._operation(measure)},
            resource_limits={"runs": 3},
        )
        for mode in ("diagnostic-only", "routine-local", "formal-slot-h"):
            definition = self._measurement(
                mode,
                result_owner="E" if mode == "formal-slot-h" else "B",
                resource_ceiling={"runs": 3},
            )
            batch.apply(
                ReviseBatch(
                    rationale=f"Use the {mode} measurement meaning.",
                    measurement_definition=definition,
                )
            )
            batch.perform(
                Action(
                    key=f"measure-{mode}",
                    operation="measure",
                    kind="measurement",
                    requested_resources={"runs": 1},
                )
            )
            self.assertEqual(
                batch.view.data["attempts"][-1]["measurement_definition"],
                definition,
            )

        self.assertEqual(
            observed,
            ["diagnostic-only", "routine-local", "formal-slot-h"],
        )

    def test_repeatable_public_measurement_needs_no_single_use_fields_or_governance(self) -> None:
        calls: list[str] = []

        def measure(action: Action, context: dict) -> OperationResult:
            calls.append(action.key)
            return OperationResult(status="completed", resource_use={"runs": 1})

        batch = self._defined_batch(
            operations={"measure": self._operation(measure)},
            resource_limits={"runs": 2},
            expected_consequences=(),
        )
        definition = self._measurement(
            mode="routine-local",
            resource_ceiling={"runs": 2},
        )
        batch.apply(
            ReviseBatch(
                rationale="Use a repeatable public screen.",
                measurement_definition=definition,
            )
        )
        action = Action(
            key="public-screen",
            operation="measure",
            kind="measurement",
            requested_resources={"runs": 1},
            repeatable=True,
        )

        batch.perform(action)
        outcome = batch.perform(action)

        self.assertEqual(calls, ["public-screen", "public-screen"])
        self.assertEqual(len(outcome.view.data["attempts"]), 2)
        self.assertEqual(outcome.view.data["consumption"], {"runs": 2})
        for field in (
            "nonrepeatable_unit",
            "non_repeatable_unit",
            "resource_owner",
            "consumption_control",
        ):
            self.assertNotIn(field, definition)

    def test_operational_limit_can_be_revised_before_any_attempt(self) -> None:
        calls: list[str] = []

        def inspect(action: Action, context: dict) -> OperationResult:
            calls.append(action.key)
            return OperationResult(status="completed", resource_use={"runs": 2})

        batch = self._defined_batch(
            operations={"inspect": self._operation(inspect)},
            resource_limits={"runs": 1},
        )
        action = Action(
            key="bounded-inspection",
            operation="inspect",
            kind="diagnostic",
            requested_resources={"runs": 2},
        )

        with self.assertRaisesRegex(ConsequenceBlocked, "Batch resource limit"):
            batch.perform(action)

        self.assertEqual(calls, [])
        self.assertEqual(batch.view.data["attempts"], [])

        batch.apply(
            ReviseBatch(
                rationale="Correct the operational cap for the same inspection.",
                resource_limits={"runs": 2},
            )
        )
        outcome = batch.perform(action)

        self.assertEqual(calls, ["bounded-inspection"])
        self.assertEqual(outcome.view.data["consumption"], {"runs": 2})

    def test_measurement_ceiling_is_independent_and_counts_prior_measurements(self) -> None:
        calls: list[str] = []

        def measure(action: Action, context: dict) -> OperationResult:
            calls.append(action.key)
            return OperationResult(status="completed", resource_use={"runs": 1})

        batch = self._defined_batch(
            operations={"measure": self._operation(measure)},
            resource_limits={"runs": 3},
        )
        batch.apply(
            ReviseBatch(
                rationale="Start with one decision-relevant exposure.",
                measurement_definition=self._measurement(
                    resource_ceiling={"runs": 1}
                ),
            )
        )
        batch.perform(
            Action(
                key="first-measurement",
                operation="measure",
                kind="measurement",
                requested_resources={"runs": 1},
            )
        )

        second = Action(
            key="second-measurement",
            operation="measure",
            kind="measurement",
            requested_resources={"runs": 1},
        )
        with self.assertRaisesRegex(
            ConsequenceBlocked,
            "Measurement Definition resource ceiling",
        ):
            batch.perform(second)

        self.assertEqual(calls, ["first-measurement"])
        self.assertEqual(len(batch.view.data["attempts"]), 1)

        with self.assertRaisesRegex(
            ChangeRejected,
            "recorded measurement capacity use",
        ):
            batch.apply(
                ReviseBatch(
                    rationale="Do not erase an exposure that already occurred.",
                    measurement_definition=self._measurement(
                        resource_ceiling={"runs": 0}
                    ),
                )
            )

        batch.apply(
            ReviseBatch(
                rationale="Current evidence justifies one additional exposure.",
                measurement_definition=self._measurement(
                    resource_ceiling={"runs": 2}
                ),
            )
        )
        outcome = batch.perform(second)

        self.assertEqual(calls, ["first-measurement", "second-measurement"])
        self.assertEqual(outcome.view.data["consumption"], {"runs": 2})

    def test_new_measurement_definition_requires_a_valid_resource_ceiling(self) -> None:
        batch = self._defined_batch()
        missing = self._measurement()
        del missing["resource_ceiling"]

        for invalid in (missing, self._measurement(resource_ceiling={"runs": -1})):
            with self.subTest(invalid=invalid):
                with self.assertRaisesRegex(BatchFormatError, "resource_ceiling"):
                    batch.apply(
                        ReviseBatch(
                            rationale="Reject a missing or invalid semantic ceiling.",
                            measurement_definition=invalid,
                        )
                    )

    def test_measurement_context_contract_round_trips_without_reclassifying_execution(self) -> None:
        def measure(action: Action, context: dict) -> OperationResult:
            return OperationResult(
                status="completed",
                observations=({"reachable": True},),
                resource_use={"runs": 1},
                result={
                    "decision_value": 600,
                    "lifecycle_state": "initialization",
                    "context": {"exposure_count": 0},
                },
            )

        batch = self._defined_batch(
            operations={"measure": self._operation(measure)},
            resource_limits={"runs": 1},
        )
        definition = self._measurement(
            required_context_keys=["exposure_count", "comparison_population"],
        )
        batch.apply(
            ReviseBatch(
                rationale="Record the interpretation context expected at adoption.",
                measurement_definition=definition,
            )
        )

        outcome = batch.perform(
            Action(
                key="initialization-observation",
                operation="measure",
                kind="measurement",
                requested_resources={"runs": 1},
            )
        )

        attempt = outcome.view.data["attempts"][0]
        self.assertEqual(attempt["status"], "completed")
        self.assertEqual(attempt["measurement_definition"], definition)
        self.assertEqual(attempt["result"]["decision_value"], 600)
        self.assertEqual(attempt["result"]["lifecycle_state"], "initialization")
        self.assertNotIn("contract_violations", attempt)

    def test_required_context_keys_are_structural_and_unique(self) -> None:
        batch = self._defined_batch()

        for invalid in (
            "exposure_count",
            ["exposure_count", "exposure_count"],
            ["exposure_count", ""],
        ):
            with self.subTest(invalid=invalid):
                with self.assertRaisesRegex(BatchFormatError, "required_context_keys"):
                    batch.apply(
                        ReviseBatch(
                            rationale="Reject a malformed context-key declaration.",
                            measurement_definition=self._measurement(
                                required_context_keys=invalid,
                            ),
                        )
                    )

    def test_measurement_without_batch_definition_never_calls_adapter(self) -> None:
        calls: list[str] = []

        def measure(action: Action, context: dict) -> OperationResult:
            calls.append(action.key)
            return OperationResult(status="completed")

        batch = self._defined_batch(
            operations={"measure": self._operation(measure)}
        )
        with self.assertRaisesRegex(
            ConsequenceBlocked,
            "Batch-owned Measurement Definition",
        ):
            batch.perform(
                Action(key="measure", operation="measure", kind="measurement")
            )

        self.assertEqual(calls, [])

    def test_protected_adapter_requires_declared_and_covered_permission(self) -> None:
        calls: list[str] = []

        def submit(action: Action, context: dict) -> OperationResult:
            calls.append(action.key)
            return OperationResult(
                status="completed",
                consequences=(Consequence("external_submission"),),
            )

        batch = self._defined_batch(
            governance=Governance(
                permitted_consequences=("external_submission",),
            ),
            operations={
                "submit": self._operation(submit, ("external_submission",))
            },
            expected_consequences=("external_submission",),
        )
        with self.assertRaisesRegex(
            ConsequenceBlocked,
            "requires undeclared Consequences",
        ):
            batch.perform(Action(key="submit-1", operation="submit", kind="external"))
        with self.assertRaisesRegex(
            ConsequenceBlocked,
            "require an applicable Permission",
        ):
            batch.perform(
                Action(
                    key="submit-2",
                    operation="submit",
                    kind="external",
                    possible_consequences=("external_submission",),
                )
            )

        self.assertEqual(calls, [])

    def test_permission_limits_do_not_duplicate_internal_batch_resources(self) -> None:
        def submit(action: Action, context: dict) -> OperationResult:
            return OperationResult(
                status="completed",
                consequences=(Consequence("external_submission"),),
                resource_use={"runs": 1},
            )

        batch = self._defined_batch(
            governance=Governance(
                permission_limits={"external_calls": 1},
                permitted_consequences=("external_submission",),
            ),
            operations={
                "submit": self._operation(submit, ("external_submission",))
            },
            expected_consequences=("external_submission",),
        )
        outcome = batch.perform(
            Action(
                key="submit",
                operation="submit",
                kind="external",
                required_permissions=("V001",),
                requested_resources={"runs": 1},
                possible_consequences=("external_submission",),
            )
        )

        self.assertEqual(outcome.view.data["consumption"], {"runs": 1})

    def test_single_use_permission_depends_on_resource_owner(self) -> None:
        calls: list[str] = []

        def consume(action: Action, context: dict) -> OperationResult:
            calls.append(action.key)
            return OperationResult(
                status="completed",
                consequences=(Consequence("single_use_consumption"),),
                resource_use={"runs": 1},
            )

        batch = self._defined_batch(
            governance=Governance(
                permitted_consequences=("single_use_consumption",),
            ),
            operations={
                "consume": self._operation(consume, ("single_use_consumption",))
            },
            expected_consequences=("single_use_consumption",),
        )
        batch.apply(
            ReviseBatch(
                rationale="Use workflow-owned development evidence.",
                measurement_definition=self._single_use_measurement(
                    nonrepeatable_unit="workflow sample",
                    resource_owner="workflow",
                ),
            )
        )
        batch.perform(
            Action(
                key="workflow-sample",
                operation="consume",
                kind="measurement",
                requested_resources={"runs": 1},
                possible_consequences=("single_use_consumption",),
            )
        )

        batch.apply(
            ReviseBatch(
                rationale="Use a user-controlled scarce sample.",
                measurement_definition=self._single_use_measurement(
                    nonrepeatable_unit="user sample",
                    resource_owner="user",
                ),
            )
        )
        with self.assertRaisesRegex(
            ConsequenceBlocked,
            "require an applicable Permission",
        ):
            batch.perform(
                Action(
                    key="user-sample",
                    operation="consume",
                    kind="measurement",
                    requested_resources={"runs": 1},
                    possible_consequences=("single_use_consumption",),
                )
            )
        batch.perform(
            Action(
                key="user-sample",
                operation="consume",
                kind="measurement",
                required_permissions=("V001",),
                requested_resources={"runs": 1},
                possible_consequences=("single_use_consumption",),
            )
        )

        self.assertEqual(calls, ["workflow-sample", "user-sample"])

    def test_single_use_contract_is_required_only_at_a_single_use_action(self) -> None:
        calls: list[str] = []

        def consume(action: Action, context: dict) -> OperationResult:
            calls.append(action.key)
            return OperationResult(
                status="completed",
                consequences=(Consequence("single_use_consumption"),),
            )

        batch = self._defined_batch(
            governance=Governance(
                permitted_consequences=("single_use_consumption",),
            ),
            operations={
                "consume": self._operation(consume, ("single_use_consumption",))
            },
            expected_consequences=("single_use_consumption",),
        )
        action = Action(
            key="consume",
            operation="consume",
            kind="measurement",
            possible_consequences=("single_use_consumption",),
        )

        invalid_definitions = (
            self._measurement(),
            self._measurement(nonrepeatable_unit="sample"),
            self._measurement(
                nonrepeatable_unit="sample",
                resource_owner="workflow",
            ),
        )
        for definition in invalid_definitions:
            with self.subTest(definition=definition):
                batch.apply(
                    ReviseBatch(
                        rationale="Check one incomplete single-use definition.",
                        measurement_definition=definition,
                    )
                )
                with self.assertRaises(ConsequenceBlocked):
                    batch.perform(action)

        batch.apply(
            ReviseBatch(
                rationale="Complete the single-use definition.",
                measurement_definition=self._single_use_measurement(),
            )
        )
        with self.assertRaisesRegex(ConsequenceBlocked, "must not be repeatable"):
            batch.perform(
                Action(
                    key="consume",
                    operation="consume",
                    kind="measurement",
                    possible_consequences=("single_use_consumption",),
                    repeatable=True,
                )
            )

        batch.apply(
            ReviseBatch(
                rationale="Use a user-owned single-use unit.",
                measurement_definition=self._single_use_measurement(
                    resource_owner="user"
                ),
            )
        )
        with self.assertRaisesRegex(
            ConsequenceBlocked,
            "require an applicable Permission",
        ):
            batch.perform(action)

        self.assertEqual(calls, [])
        self.assertEqual(batch.view.data["attempts"], [])

    def test_single_use_unit_cannot_be_bypassed_by_changing_action_key(self) -> None:
        calls: list[str] = []

        def consume(action: Action, context: dict) -> OperationResult:
            calls.append(action.key)
            return OperationResult(
                status="completed",
                consequences=(Consequence("single_use_consumption"),),
            )

        batch = self._defined_batch(
            operations={
                "consume": self._operation(consume, ("single_use_consumption",))
            },
            expected_consequences=("single_use_consumption",),
        )
        batch.apply(
            ReviseBatch(
                rationale="Name the actual single-use unit.",
                measurement_definition=self._single_use_measurement(
                    nonrepeatable_unit="fixed public schedule"
                ),
            )
        )
        first = Action(
            key="schedule-a",
            operation="consume",
            kind="measurement",
            possible_consequences=("single_use_consumption",),
        )
        batch.perform(first)

        with self.assertRaisesRegex(ConsequenceBlocked, "already consumed"):
            batch.perform(
                Action(
                    key="renamed-schedule-a",
                    operation="consume",
                    kind="measurement",
                    possible_consequences=("single_use_consumption",),
                )
            )

        self.assertEqual(calls, ["schedule-a"])

    def test_reconciled_zero_effect_single_use_attempt_can_retry_under_a_new_key(self) -> None:
        calls: list[str] = []

        def consume(action: Action, context: dict) -> OperationResult:
            calls.append(action.key)
            if len(calls) == 1:
                raise RuntimeError("lost before the unit was consumed")
            return OperationResult(status="completed")

        batch = self._defined_batch(
            operations={
                "consume": self._operation(consume, ("single_use_consumption",))
            },
            expected_consequences=("single_use_consumption",),
        )
        batch.apply(
            ReviseBatch(
                rationale="Name the retry-controlled single-use unit.",
                measurement_definition=self._single_use_measurement(
                    nonrepeatable_unit="recoverable slot"
                ),
            )
        )
        first = Action(
            key="first-key",
            operation="consume",
            kind="measurement",
            possible_consequences=("single_use_consumption",),
        )
        with self.assertRaises(ConsequenceUncertain):
            batch.perform(first)

        with self.assertRaisesRegex(ConsequenceUncertain, "single-use unit"):
            batch.perform(
                Action(
                    key="second-key",
                    operation="consume",
                    kind="measurement",
                    possible_consequences=("single_use_consumption",),
                )
            )

        batch.apply(
            ReconcileAttempt(
                attempt=1,
                status="failed",
                rationale="Observed facts prove that the unit was not consumed.",
            )
        )
        outcome = batch.perform(
            Action(
                key="second-key",
                operation="consume",
                kind="measurement",
                possible_consequences=("single_use_consumption",),
            )
        )

        self.assertEqual(calls, ["first-key", "second-key"])
        self.assertEqual(outcome.view.data["attempts"][1]["status"], "completed")

    def test_historical_single_use_alias_is_read_and_current_writes_are_canonical(self) -> None:
        batch = self._defined_batch()
        alias_definition = self._single_use_measurement()
        alias_definition["non_repeatable_unit"] = alias_definition.pop(
            "nonrepeatable_unit"
        )
        view = batch.apply(
            ReviseBatch(
                rationale="Read the historical alias and write the current key.",
                measurement_definition=alias_definition,
            )
        )
        stored = view.data["current"]["measurement_definition"]
        self.assertEqual(stored["nonrepeatable_unit"], "one scheduled run")
        self.assertNotIn("non_repeatable_unit", stored)

        historical = yaml.safe_load(self.state_path.read_text())
        historical_definition = historical["current"]["measurement_definition"]
        historical_definition["non_repeatable_unit"] = historical_definition.pop(
            "nonrepeatable_unit"
        )
        self.state_path.write_text(yaml.safe_dump(historical, sort_keys=False))
        reopened = Batch.open(self.repo, "B001", state_path=self.state_path)
        self.assertEqual(
            reopened.view.data["current"]["measurement_definition"][
                "non_repeatable_unit"
            ],
            "one scheduled run",
        )

        conflicting = self._single_use_measurement(
            non_repeatable_unit="another scheduled run"
        )
        with self.assertRaisesRegex(BatchFormatError, "aliases disagree"):
            reopened.apply(
                ReviseBatch(
                    rationale="Reject conflicting unit aliases.",
                    measurement_definition=conflicting,
                )
            )

    def test_adapter_failure_leaves_one_uncertain_attempt_and_blocks_repeat(self) -> None:
        def operation(action: Action, context: dict) -> OperationResult:
            raise RuntimeError("connection lost")

        batch = self._defined_batch(operations={"external": self._operation(operation)})
        action = Action(
            key="paid-call",
            operation="external",
            kind="external",
            requested_resources={"runs": 1},
        )
        with self.assertRaises(ConsequenceUncertain):
            batch.perform(action)

        self.assertEqual(batch.view.data["attempts"][0]["status"], "uncertain")
        batch.apply(
            RecordObservation(
                key="unrelated-note",
                observation={"status": "routine work may continue"},
            )
        )
        self.assertIn("unrelated-note", batch.view.data["current"]["observations"])
        with self.assertRaises(ConsequenceUncertain):
            batch.perform(action)
        self.assertEqual(len(batch.view.data["attempts"]), 1)

    def test_nonrepeatable_completed_action_cannot_run_twice(self) -> None:
        calls = 0

        def operation(action: Action, context: dict) -> OperationResult:
            nonlocal calls
            calls += 1
            return OperationResult(status="completed", resource_use={"runs": 1})

        batch = self._defined_batch(operations={"measure": self._operation(operation)})
        batch.apply(
            ReviseBatch(
                rationale="Set the Batch-owned measurement meaning.",
                measurement_definition=self._measurement(),
            )
        )
        action = Action(
            key="one-measurement",
            operation="measure",
            kind="measurement",
            requested_resources={"runs": 1},
        )
        batch.perform(action)
        with self.assertRaisesRegex(ConsequenceBlocked, "already completed"):
            batch.perform(action)

        self.assertEqual(calls, 1)
        self.assertEqual(len(batch.view.data["attempts"]), 1)

    def test_historical_projection_is_read_only_until_current_change(self) -> None:
        legacy_state = {
            "contract_version": "frontier-batch/1",
            "batch": "B001",
            "definition": {
                "objective": "Continue the original result.",
                "acceptance": "Preserve the original meaning.",
                "scope": ["repair"],
                "expected_consequences": [],
            },
            "references": {"reviews": [], "permissions": []},
            "current": {
                "status": "open",
                "candidate_revision": None,
                "measurement_definition": None,
                "checks": {},
                "observations": {},
                "conclusion": None,
            },
            "resource_limits": {},
            "consumption": {},
            "attempts": [],
        }
        batch = Batch.open(
            self.repo,
            "B001",
            state_path=self.state_path,
            legacy_projector=lambda repo, batch: legacy_state,
        )

        self.assertFalse(self.state_path.exists())
        batch.apply(ReviseBatch(rationale="Use the current writer."))
        self.assertTrue(self.state_path.exists())
        self.assertEqual(yaml.safe_load(self.state_path.read_text())["batch"], "B001")

    def test_conclusion_rejects_uncertain_attempt(self) -> None:
        def operation(action: Action, context: dict) -> OperationResult:
            return OperationResult(status="uncertain", recovery_condition="Check provider state.")

        batch = self._defined_batch(operations={"external": self._operation(operation, ("spend",))})
        with self.assertRaises(ConsequenceUncertain):
            batch.perform(
                Action(
                    key="external",
                    operation="external",
                    kind="external",
                    possible_consequences=("spend",),
                )
            )
        with self.assertRaisesRegex(Exception, "unresolved Attempt"):
            batch.apply(
                ConcludeBatch(
                    status="stopped",
                    result={"status": "unknown"},
                    remaining_gap="Resolve the external effect.",
                )
            )

    def test_reconcile_uncertain_attempt_preserves_actual_use_and_allows_conclusion(self) -> None:
        def operation(action: Action, context: dict) -> OperationResult:
            raise RuntimeError("connection lost")

        batch = self._defined_batch(operations={"external": self._operation(operation, ("spend",))})
        with self.assertRaises(ConsequenceUncertain):
            batch.perform(
                Action(
                    key="external",
                    operation="external",
                    kind="external",
                    possible_consequences=("spend",),
                    requested_resources={"runs": 1},
                )
            )

        batch.apply(
            ReconcileAttempt(
                attempt=1,
                status="failed",
                rationale="Provider history proves one charged failed request.",
                consequences=(Consequence("spend", amount=1),),
                resource_use={"runs": 1},
                result={"provider_status": "failed"},
            )
        )
        view = batch.apply(
            ConcludeBatch(
                status="stopped",
                result={"status": "failed request"},
                remaining_gap="Choose a different reachable action.",
            )
        )

        self.assertEqual(view.data["consumption"], {"runs": 1})
        self.assertEqual(view.data["attempts"][0]["actual_consequences"][0]["kind"], "spend")
        self.assertNotIn("resource_bounds", view.data["attempts"][0])
        self.assertNotIn("capacity_charge", view.data["attempts"][0])
        self.assertEqual(view.status, "stopped")

    def test_reconcile_preserves_explicit_zero_resource_use(self) -> None:
        def operation(action: Action, context: dict) -> OperationResult:
            raise RuntimeError("connection lost")

        batch = self._defined_batch(
            operations={"external": self._operation(operation)},
            resource_limits={"runs": 1, "external_effects": 0},
        )
        with self.assertRaises(ConsequenceUncertain):
            batch.perform(
                Action(
                    key="external",
                    operation="external",
                    kind="external",
                    requested_resources={"runs": 1, "external_effects": 0},
                )
            )

        view = batch.apply(
            ReconcileAttempt(
                attempt=1,
                status="failed",
                rationale="Retained evidence proves one run and zero external effects.",
                resource_use={"runs": 1, "external_effects": 0},
            )
        )

        self.assertEqual(
            view.data["consumption"],
            {"runs": 1, "external_effects": 0},
        )
        self.assertEqual(
            view.data["attempts"][0]["resource_use"],
            {"runs": 1, "external_effects": 0},
        )

    def test_reconcile_unknown_exact_use_preserves_bounds_and_charges_capacity(self) -> None:
        remaining: list[dict[str, int | float]] = []

        def interrupted(action: Action, context: dict) -> OperationResult:
            raise RuntimeError("local process ended before exact counters were retained")

        def followup(action: Action, context: dict) -> OperationResult:
            remaining.append(context["remaining_resources"])
            return OperationResult(
                status="completed",
                resource_use={"candidate_calls": 1, "processes": 1},
            )

        batch = self._defined_batch(
            operations={
                "interrupted": self._operation(interrupted),
                "followup": self._operation(followup),
            },
            resource_limits={"candidate_calls": 6, "processes": 2},
        )
        with self.assertRaises(ConsequenceUncertain):
            batch.perform(
                Action(
                    key="first-diagnostic",
                    operation="interrupted",
                    kind="diagnostic",
                    requested_resources={"candidate_calls": 5, "processes": 1},
                )
            )

        view = batch.apply(
            ReconcileAttempt(
                attempt=1,
                status="failed",
                rationale="The retained journal proves only a bounded call count.",
                resource_use={"processes": 1},
                resource_bounds={
                    "candidate_calls": {
                        "minimum": 3,
                        "maximum": 5,
                        "exact": "unknown",
                    }
                },
                capacity_charge={"candidate_calls": 5},
            )
        )

        attempt = view.data["attempts"][0]
        self.assertEqual(view.data["consumption"], {"processes": 1})
        self.assertEqual(attempt["resource_bounds"]["candidate_calls"]["minimum"], 3)
        self.assertEqual(attempt["capacity_charge"], {"candidate_calls": 5})
        with self.assertRaisesRegex(ChangeRejected, "recorded capacity use"):
            batch.apply(
                ReviseBatch(
                    rationale="This limit would understate the retained upper bound.",
                    resource_limits={"candidate_calls": 4, "processes": 2},
                )
            )

        outcome = batch.perform(
            Action(
                key="second-diagnostic",
                operation="followup",
                kind="diagnostic",
                requested_resources={"candidate_calls": 1, "processes": 1},
            )
        )
        self.assertEqual(remaining, [{"candidate_calls": 1, "processes": 1}])
        self.assertEqual(
            outcome.view.data["consumption"],
            {"processes": 2, "candidate_calls": 1},
        )

    def test_permission_limit_uses_conservative_reconciled_capacity(self) -> None:
        permission_actual: list[dict[str, int | float]] = []
        adapter_calls: list[str] = []

        class RecordingGovernance(Governance):
            def permission(
                self,
                reference: GitReference,
                action: Action,
                actual_consumption: dict[str, int | float],
            ) -> PermissionAssessment:
                permission_actual.append(dict(actual_consumption))
                return super().permission(reference, action, actual_consumption)

        def interrupted(action: Action, context: dict) -> OperationResult:
            raise RuntimeError("counter journal incomplete")

        def followup(action: Action, context: dict) -> OperationResult:
            adapter_calls.append(action.key)
            return OperationResult(status="completed", resource_use={"calls": 2})

        batch = self._defined_batch(
            governance=RecordingGovernance(permission_limits={"calls": 6}),
            operations={
                "interrupted": self._operation(interrupted),
                "followup": self._operation(followup),
            },
            resource_limits={"calls": 10},
        )
        with self.assertRaises(ConsequenceUncertain):
            batch.perform(
                Action(
                    key="first-diagnostic",
                    operation="interrupted",
                    kind="diagnostic",
                    requested_resources={"calls": 5},
                )
            )
        batch.apply(
            ReconcileAttempt(
                attempt=1,
                status="failed",
                rationale="Only a bounded call count survived.",
                resource_bounds={
                    "calls": {"minimum": 3, "maximum": 5, "exact": "unknown"}
                },
                capacity_charge={"calls": 5},
            )
        )

        with self.assertRaisesRegex(ConsequenceBlocked, "Permission resource limit"):
            batch.perform(
                Action(
                    key="second-diagnostic",
                    operation="followup",
                    kind="diagnostic",
                    required_permissions=("V001",),
                    requested_resources={"calls": 2},
                )
            )

        self.assertEqual(permission_actual, [{"calls": 5}])
        self.assertEqual(adapter_calls, [])
        self.assertEqual(len(batch.view.data["attempts"]), 1)

    def test_reconcile_unknown_exact_use_rejects_malformed_or_mixed_facts(self) -> None:
        def interrupted(action: Action, context: dict) -> OperationResult:
            raise RuntimeError("counter journal incomplete")

        batch = self._defined_batch(
            operations={"interrupted": self._operation(interrupted)},
            resource_limits={"calls": 10},
        )
        with self.assertRaises(ConsequenceUncertain):
            batch.perform(
                Action(
                    key="diagnostic",
                    operation="interrupted",
                    kind="diagnostic",
                    requested_resources={"calls": 10},
                )
            )

        valid_bounds = {
            "calls": {"minimum": 3, "maximum": 5, "exact": "unknown"}
        }
        invalid_cases = (
            (
                "missing charge",
                {},
                valid_bounds,
                {},
                "keys must exactly match",
            ),
            (
                "extra charge",
                {},
                valid_bounds,
                {"calls": 5, "other": 1},
                "keys must exactly match",
            ),
            (
                "wrong charge",
                {},
                valid_bounds,
                {"calls": 4},
                "conservative maximum",
            ),
            (
                "mixed exact and ranged",
                {"calls": 3},
                valid_bounds,
                {"calls": 5},
                "exact use and unknown bounds",
            ),
            (
                "extra bound field",
                {},
                {
                    "calls": {
                        "minimum": 3,
                        "maximum": 5,
                        "exact": "unknown",
                        "estimate": 4,
                    }
                },
                {"calls": 5},
                "must contain only",
            ),
            (
                "known exact marker",
                {},
                {"calls": {"minimum": 3, "maximum": 5, "exact": 4}},
                {"calls": 5},
                "must be 'unknown'",
            ),
            (
                "reversed range",
                {},
                {"calls": {"minimum": 6, "maximum": 5, "exact": "unknown"}},
                {"calls": 5},
                "cannot exceed maximum",
            ),
        )
        for label, exact, bounds, charge, message in invalid_cases:
            with self.subTest(label=label):
                with self.assertRaisesRegex(BatchFormatError, message):
                    batch.apply(
                        ReconcileAttempt(
                            attempt=1,
                            status="failed",
                            rationale="Preserve only defensible resource facts.",
                            resource_use=exact,
                            resource_bounds=bounds,
                            capacity_charge=charge,
                        )
                    )

        with self.assertRaisesRegex(BatchFormatError, "only reconcile a failed Attempt"):
            batch.apply(
                ReconcileAttempt(
                    attempt=1,
                    status="completed",
                    rationale="A completed result cannot retain unknown exact use.",
                    resource_bounds=valid_bounds,
                    capacity_charge={"calls": 5},
                )
            )

    def test_open_rejects_tampered_unknown_resource_capacity_charge(self) -> None:
        def interrupted(action: Action, context: dict) -> OperationResult:
            raise RuntimeError("counter journal incomplete")

        batch = self._defined_batch(
            operations={"interrupted": self._operation(interrupted)},
            resource_limits={"calls": 10},
        )
        with self.assertRaises(ConsequenceUncertain):
            batch.perform(
                Action(
                    key="diagnostic",
                    operation="interrupted",
                    kind="diagnostic",
                    requested_resources={"calls": 10},
                )
            )
        batch.apply(
            ReconcileAttempt(
                attempt=1,
                status="failed",
                rationale="Only a bounded call count survived.",
                resource_bounds={
                    "calls": {"minimum": 3, "maximum": 5, "exact": "unknown"}
                },
                capacity_charge={"calls": 5},
            )
        )
        valid_state = yaml.safe_load(self.state_path.read_text())
        state = yaml.safe_load(self.state_path.read_text())
        state["attempts"][0]["capacity_charge"]["calls"] = 4
        self.state_path.write_text(yaml.safe_dump(state, sort_keys=False))

        with self.assertRaisesRegex(BatchFormatError, "conservative maximum"):
            Batch.open(self.repo, "B001", state_path=self.state_path)

        valid_state["resource_limits"]["calls"] = 4
        self.state_path.write_text(yaml.safe_dump(valid_state, sort_keys=False))
        with self.assertRaisesRegex(BatchFormatError, "capacity use.*exceeds"):
            Batch.open(self.repo, "B001", state_path=self.state_path)

    def test_unexpected_effect_is_retained_as_an_attempt(self) -> None:
        def inspect(action: Action, context: dict) -> OperationResult:
            return OperationResult(
                status="completed",
                consequences=(Consequence("spend", amount=1),),
                resource_use={"runs": 1},
            )

        batch = self._defined_batch(operations={"inspect": self._operation(inspect)})
        with self.assertRaises(OperationContractViolation):
            batch.perform(Action(key="inspect", operation="inspect", kind="check"))

        attempt = batch.view.data["attempts"][0]
        self.assertEqual(attempt["status"], "completed")
        self.assertEqual(attempt["actual_consequences"][0]["kind"], "spend")
        self.assertIn("undeclared Attempt", attempt["contract_violations"][-1])

    def test_invalid_operation_status_leaves_reconcilable_uncertainty(self) -> None:
        def operation(action: Action, context: dict) -> OperationResult:
            return OperationResult(status="invented")

        batch = self._defined_batch(operations={"operation": self._operation(operation)})
        batch.apply(
            ReviseBatch(
                rationale="Set the Batch-owned measurement meaning.",
                measurement_definition=self._measurement(),
            )
        )
        with self.assertRaises(OperationContractViolation):
            batch.perform(
                Action(
                    key="ambiguous",
                    operation="operation",
                    kind="measurement",
                )
            )

        self.assertEqual(batch.view.data["attempts"][0]["status"], "uncertain")
        batch.apply(
            ReconcileAttempt(
                attempt=1,
                status="failed",
                rationale="The adapter produced no usable result or effect.",
            )
        )
        self.assertEqual(batch.view.data["attempts"][0]["status"], "failed")

    def test_malformed_adapter_result_does_not_leave_a_running_attempt(self) -> None:
        def operation(action: Action, context: dict) -> OperationResult:
            return OperationResult(status="completed", observations=(None,))  # type: ignore[arg-type]

        batch = self._defined_batch(operations={"operation": self._operation(operation)})
        batch.apply(
            ReviseBatch(
                rationale="Set the Batch-owned measurement meaning.",
                measurement_definition=self._measurement(),
            )
        )
        with self.assertRaises(OperationContractViolation):
            batch.perform(
                Action(
                    key="malformed",
                    operation="operation",
                    kind="measurement",
                )
            )

        attempt = batch.view.data["attempts"][0]
        self.assertEqual(attempt["status"], "uncertain")
        self.assertIn("could not be recorded", attempt["adapter_error"])


if __name__ == "__main__":
    unittest.main()
