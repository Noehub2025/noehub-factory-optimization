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
            *MODULE.BATCH_TESTS,
            *MODULE.RECOVERY_TESTS,
        ):
            self.assertIn(expected.as_posix(), plan.tests)
        self.assertNotIn(MODULE.FRAME_TEST.as_posix(), plan.tests)

    def test_cross_cutting_contract_escalates_to_complete_suite(self) -> None:
        plan = MODULE.select_checks(
            (".agents/skills/frontier-optimization/references/frontier-core.md",),
            "affected",
        )

        self.assertTrue(plan.release)
        self.assertEqual(
            plan.tests,
            tuple(path.as_posix() for path in MODULE.RELEASE_TEST_ROOTS),
        )

    def test_unknown_workflow_python_escalates_instead_of_skipping(self) -> None:
        plan = MODULE.select_checks(
            (".agents/skills/frontier-optimization/scripts/new_validator.py",),
            "affected",
        )

        self.assertTrue(plan.release)
        self.assertIn("affected mode escalated to the complete suite", plan.reasons)

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
