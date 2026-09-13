#!/usr/bin/env python3
"""Tests for Git-aware Optimization workflow check selection."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("run_workflow_checks.py")
SPEC = importlib.util.spec_from_file_location("run_workflow_checks", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class WorkflowCheckSelectionTests(unittest.TestCase):
    def test_expansion_and_release_preserve_affected_compatibility_tests(self) -> None:
        preparation = ".agents/skills/frontier-optimization/scripts/frontier_review/preparation.py"
        core = ".agents/skills/frontier-optimization/references/frontier-core.md"
        affected = set(MODULE.select_checks((preparation,), "affected").tests)
        for paths in ((preparation, core), (core, preparation)):
            for mode in ("affected", "release"):
                with self.subTest(paths=paths, mode=mode):
                    plan = MODULE.select_checks(paths, mode)
                    self.assertLessEqual(affected, set(plan.tests))
                    self.assertLessEqual(
                        {test.as_posix() for test in MODULE.CURRENT_RELEASE_TESTS}, set(plan.tests),
                    )
        current_release = MODULE.select_checks((core,), "release")
        self.assertFalse(affected & set(current_release.tests))

    def test_reference_ownership_and_unknown_contracts_never_silently_skip(self) -> None:
        for name in ("user-decisions.md", "new-current-contract.md"):
            plan = MODULE.select_checks(
                (f".agents/skills/frontier-optimization/references/{name}",), "affected",
            )
            self.assertTrue(plan.tests)
            self.assertTrue(plan.run_bundle_validator)

    def test_shared_git_change_selects_all_current_consumers_without_legacy(self) -> None:
        plan = MODULE.select_checks(
            (".agents/skills/frontier-optimization/scripts/saved_git.py",), "affected",
        )
        self.assertLessEqual(
            {"test_frontier_batch.py", "test_frontier_references.py", "test_saved_git.py", "test_batch_execution_example.py"},
            {Path(test).name for test in plan.tests},
        )
        self.assertNotIn("test_frontier_provenance.py", {Path(test).name for test in plan.tests})

    def test_fixture_changes_select_their_current_or_legacy_consumers(self) -> None:
        fixtures = ".agents/skills/frontier-optimization/scripts/fixtures/"
        for relative, expected in (
            ("direction-resolver-scenarios.yaml", MODULE.DIRECTION_TESTS),
            ("slice7/scenarios.yaml", MODULE.RECOVERY_TESTS),
        ):
            plan = MODULE.select_checks((fixtures + relative,), "affected")
            self.assertEqual(set(plan.tests), {test.as_posix() for test in expected})

    def test_project_changes_do_not_select_workflow_regression(self) -> None:
        plan = MODULE.select_checks(
            ("src/example.py", "tests/test_example.py", "docs/campaign/log.md"),
            "affected",
        )

        self.assertEqual(plan.workflow_paths, ())
        self.assertEqual(plan.tests, ())
        self.assertFalse(plan.run_bundle_validator)

    def test_frame_change_selects_only_frame_contract_tests(self) -> None:
        plan = MODULE.select_checks(
            (".agents/skills/frame-optimization/references/task-documents.md",),
            "affected",
        )

        self.assertEqual(plan.tests, (MODULE.FRAME_TEST.as_posix(),))
        self.assertTrue(plan.run_bundle_validator)
        self.assertFalse(plan.release)

    def test_measurement_designer_change_selects_only_frame_contract_tests(self) -> None:
        plan = MODULE.select_checks(
            (".agents/skills/design-measurement/SKILL.md",),
            "affected",
        )

        self.assertEqual(plan.tests, (MODULE.FRAME_TEST.as_posix(),))
        self.assertTrue(plan.run_bundle_validator)
        self.assertFalse(plan.release)

    def test_implementation_designer_change_selects_only_design_contract_tests(self) -> None:
        plan = MODULE.select_checks(
            (".agents/skills/design-implementation/SKILL.md",),
            "affected",
        )

        self.assertEqual(
            plan.tests,
            tuple(path.as_posix() for path in MODULE.CURRENT_BATCH_TESTS),
        )
        self.assertTrue(plan.run_bundle_validator)
        self.assertFalse(plan.release)

    def test_direction_change_does_not_select_provenance_or_recovery(self) -> None:
        plan = MODULE.select_checks(
            (".agents/skills/frontier-optimization/references/learning-loop.md",),
            "affected",
        )

        self.assertEqual(plan.tests, tuple(sorted(path.as_posix() for path in MODULE.DIRECTION_TESTS)))
        self.assertNotIn(
            MODULE.FRONTIER_SCRIPTS.joinpath("test_frontier_provenance.py").as_posix(),
            plan.tests,
        )
        self.assertNotIn(
            MODULE.FRONTIER_SCRIPTS.joinpath("test_validate_candidate_recovery.py").as_posix(),
            plan.tests,
        )

    def test_changed_test_selects_itself_without_expanding_its_group(self) -> None:
        changed = MODULE.FRONTIER_SCRIPTS / "test_validate_batch_result.py"
        plan = MODULE.select_checks((changed.as_posix(),), "affected")

        self.assertEqual(plan.tests, (changed.as_posix(),))
        self.assertFalse(plan.release)

    def test_execution_example_stays_focused_and_tracks_batch_api(self) -> None:
        example = MODULE.EXECUTION_EXAMPLE_TEST.as_posix()
        plan = MODULE.select_checks(
            (".agents/skills/run-frontier-batch/scripts/batch_execution_example.py",),
            "affected",
        )
        self.assertEqual(plan.tests, (example,))
        self.assertFalse(plan.release)
        batch_plan = MODULE.select_checks(
            (".agents/skills/frontier-optimization/scripts/frontier_batch.py",),
            "affected",
        )
        self.assertIn(example, batch_plan.tests)
        release_plan = MODULE.select_checks((), "release")
        self.assertIn(example, release_plan.tests)

    def test_validator_change_selects_its_group_and_end_to_end_seam(self) -> None:
        plan = MODULE.select_checks(
            (".agents/skills/frontier-optimization/scripts/validate_batch_result.py",),
            "affected",
        )

        self.assertIn(
            MODULE.FRONTIER_SCRIPTS.joinpath("test_validate_batch_result.py").as_posix(),
            plan.tests,
        )
        self.assertIn(
            MODULE.FRONTIER_SCRIPTS.joinpath("test_slice7_end_to_end.py").as_posix(),
            plan.tests,
        )
        self.assertNotIn(
            MODULE.FRONTIER_SCRIPTS.joinpath("test_frontier_provenance.py").as_posix(),
            plan.tests,
        )

    def test_shared_provenance_change_selects_all_downstream_contract_groups(self) -> None:
        plan = MODULE.select_checks(
            (".agents/skills/frontier-optimization/scripts/frontier_provenance/graph.py",),
            "affected",
        )

        for expected in (
            *MODULE.PROVENANCE_TESTS,
            *MODULE.ENTRY_TESTS,
            *MODULE.LEGACY_BATCH_TESTS,
            *MODULE.RECOVERY_TESTS,
        ):
            self.assertIn(expected.as_posix(), plan.tests)
        self.assertNotIn(MODULE.FRAME_TEST.as_posix(), plan.tests)

    def test_review_preparation_change_selects_only_its_interface_tests(self) -> None:
        plan = MODULE.select_checks(
            (".agents/skills/frontier-optimization/scripts/frontier_review/preparation.py",),
            "affected",
        )

        self.assertEqual(
            plan.tests,
            tuple(sorted(path.as_posix() for path in MODULE.REVIEW_PREPARATION_TESTS)),
        )
        self.assertFalse(plan.release)

    def test_review_subject_contract_uses_the_same_focused_tests(self) -> None:
        plan = MODULE.select_checks(
            (
                ".agents/skills/frontier-optimization/scripts/"
                "frontier_provenance/review_contract.py",
            ),
            "affected",
        )

        self.assertEqual(
            plan.tests,
            tuple(sorted(path.as_posix() for path in MODULE.REVIEW_PREPARATION_TESTS)),
        )
        self.assertFalse(plan.release)

    def test_cross_cutting_contract_escalates_to_complete_suite(self) -> None:
        plan = MODULE.select_checks(
            (".agents/skills/frontier-optimization/references/frontier-core.md",),
            "affected",
        )

        self.assertTrue(plan.release)
        self.assertEqual(
            plan.tests,
            tuple(sorted(path.as_posix() for path in MODULE.CURRENT_RELEASE_TESTS)),
        )

    def test_unknown_workflow_python_escalates_instead_of_skipping(self) -> None:
        plan = MODULE.select_checks(
            (".agents/skills/frontier-optimization/scripts/new_validator.py",),
            "affected",
        )

        self.assertTrue(plan.release)
        self.assertIn("affected mode escalated to the current contract suite", plan.reasons)

    def test_fast_mode_runs_no_pytest_group(self) -> None:
        plan = MODULE.select_checks(
            (".agents/skills/frontier-optimization/SKILL.md",),
            "fast",
        )

        self.assertEqual(plan.tests, ())
        self.assertTrue(plan.run_bundle_validator)

    def test_release_mode_is_independent_of_changed_paths(self) -> None:
        project_only = MODULE.select_checks(("src/example.py",), "release")
        no_changes = MODULE.select_checks((), "release")

        self.assertEqual(project_only.tests, no_changes.tests)
        self.assertTrue(project_only.release)
        self.assertTrue(project_only.run_bundle_validator)

    def test_same_paths_produce_the_same_plan(self) -> None:
        paths = (
            ".agents/skills/frontier-optimization/references/learning-loop.md",
            ".agents/skills/frame-optimization/SKILL.md",
        )

        self.assertEqual(
            MODULE.select_checks(paths, "affected"),
            MODULE.select_checks(reversed(paths), "affected"),
        )

    def test_git_collection_includes_unstaged_staged_and_untracked_paths(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(("git", "init", "-q", str(root)), check=True)
            subprocess.run(("git", "-C", str(root), "config", "user.email", "tests@example.invalid"), check=True)
            subprocess.run(("git", "-C", str(root), "config", "user.name", "Workflow Tests"), check=True)
            (root / "tracked.md").write_text("one\n", encoding="utf-8")
            (root / "staged.md").write_text("one\n", encoding="utf-8")
            subprocess.run(("git", "-C", str(root), "add", "tracked.md", "staged.md"), check=True)
            subprocess.run(("git", "-C", str(root), "commit", "-qm", "base"), check=True)

            (root / "tracked.md").write_text("two\n", encoding="utf-8")
            (root / "staged.md").write_text("two\n", encoding="utf-8")
            subprocess.run(("git", "-C", str(root), "add", "staged.md"), check=True)
            (root / "untracked.md").write_text("three\n", encoding="utf-8")

            self.assertEqual(
                MODULE.collect_changed_paths(root),
                ("staged.md", "tracked.md", "untracked.md"),
            )


class WorkflowCheckPolicyTests(unittest.TestCase):
    def test_policy_has_one_selector_and_separates_project_changes(self) -> None:
        policy = (
            Path(__file__).resolve().parents[1]
            / "references/packaging-and-recovery.md"
        ).read_text(encoding="utf-8")

        self.assertIn("run_workflow_checks.py --mode affected", policy)
        self.assertIn("run_workflow_checks.py --mode release", policy)
        self.assertIn("Project files do not select workflow regression tests", policy)
        self.assertIn("Git selects scope only", policy)
        self.assertIn("The mere existence of a broader suite is not a reason to require it", policy)
        self.assertIn("run `release` only once after the candidate is stable", policy)
        self.assertNotIn("Skill `quick_validate.py` for exactly", policy)


if __name__ == "__main__":
    unittest.main()
