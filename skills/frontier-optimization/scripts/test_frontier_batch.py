#!/usr/bin/env python3
"""Focused behavioral checks for the deep current Batch module."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml

from frontier_batch import (
    Action,
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
    ReconcileAttempt,
    ReviseBatch,
    ReviewAssessment,
    SelectCandidate,
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

    def _measurement(self, mode: str = "diagnostic-only", **overrides) -> dict:
        definition = {
            "mode": mode,
            "question": "Does the selected change improve the target?",
            "comparator": "retained baseline",
            "metric": "score",
            "scope": "local",
            "resource_ceiling": {"runs": 2},
            "nonrepeatable_unit": "one scheduled run",
            "resource_owner": "workflow",
            "consumption_control": "Attempt",
            "execution_owner": "test adapter",
            "evidence_limit": "Batch evidence only",
            "interpretation_limit": "No broader performance claim",
            "result_owner": "B",
        }
        definition.update(overrides)
        return definition

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
                measurement_definition=self._measurement(resource_owner="workflow"),
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
                measurement_definition=self._measurement(resource_owner="user"),
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
