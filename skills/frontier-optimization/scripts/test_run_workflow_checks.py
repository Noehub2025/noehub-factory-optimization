#!/usr/bin/env python3
"""Tests for Git-aware Optimization workflow check selection."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).with_name("run_workflow_checks.py")
SPEC = importlib.util.spec_from_file_location("run_workflow_checks", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)
WORKFLOW = MODULE.WORKFLOW_ROOT.as_posix()


class WorkflowCheckSelectionTests(unittest.TestCase):
    def test_project_map_covers_instruction_only_and_host_only_changes(self) -> None:
        config = {
            "schema": "project-checks/1",
            "rules": [
                {
                    "paths": ["AGENTS.md", "src/shared.py"],
                    "commands": [["{python}", "-m", "pytest", "tests/test_shared.py"]],
                },
                {
                    "paths": ["tools/host/*"],
                    "commands": [["cargo", "test", "--manifest-path", "tools/host/Cargo.toml"]],
                },
            ],
        }
        for path in ("AGENTS.md", "src/shared.py", "tools/host/src/lib.rs"):
            plan = MODULE.select_checks([path], "affected", config)
            self.assertTrue(plan.project_commands)
            self.assertFalse(plan.tests)
            self.assertFalse(plan.run_bundle_validator)
            commands = MODULE._commands(plan, Path("/tmp/project"), None)
            self.assertEqual(
                commands[-1][0], "cargo" if path.startswith("tools/") else sys.executable
            )
        self.assertFalse(
            MODULE.select_checks(["unrelated.txt"], "affected", config).project_commands
        )
        self.assertFalse(MODULE.select_checks(["AGENTS.md"], "fast", config).project_commands)
        self.assertTrue(MODULE.select_checks(["AGENTS.md"], "release", config).project_commands)

    def test_invalid_project_map_does_not_silently_drop_checks(self) -> None:
        invalid = (
            {},
            {
                "schema": "project-checks/1",
                "rules": [{"paths": ["*"], "commands": ["shell string"]}],
            },
        )
        for config in invalid:
            with self.assertRaises(ValueError):
                MODULE.select_checks(["AGENTS.md"], "affected", config)

    def test_main_rejects_missing_null_and_malformed_required_map(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            check_map = root / "checks.json"
            arguments = [
                "--repo-root",
                str(root),
                "--project-checks",
                "checks.json",
                "--path",
                "AGENTS.md",
                "--dry-run",
            ]
            with patch.object(MODULE, "_run") as run:
                self.assertEqual(MODULE.main(arguments), 2)
                for contents in (
                    "null",
                    "[]",
                    "{",
                    '{"schema":"project-checks/1","rules":[{}]}',
                ):
                    check_map.write_text(contents)
                    self.assertEqual(MODULE.main(arguments), 2)
                run.assert_not_called()

    def test_deleted_default_map_is_not_treated_as_unconfigured(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            self.assertEqual(
                MODULE.main(
                    [
                        "--repo-root",
                        temporary,
                        "--path",
                        "tools/project-checks.json",
                        "--dry-run",
                    ]
                ),
                2,
            )

    def test_expansion_and_release_preserve_affected_compatibility_tests(self) -> None:
        preparation = f"{WORKFLOW}/frontier-optimization/scripts/frontier_review/preparation.py"
        core = f"{WORKFLOW}/frontier-optimization/references/frontier-core.md"
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
                (f"{WORKFLOW}/frontier-optimization/references/{name}",), "affected",
            )
            self.assertTrue(plan.tests)
            self.assertTrue(plan.run_bundle_validator)

    def test_shared_git_change_selects_all_current_consumers_without_legacy(self) -> None:
        plan = MODULE.select_checks(
            (f"{WORKFLOW}/frontier-optimization/scripts/saved_git.py",), "affected",
        )
        self.assertLessEqual(
            {"test_frontier_batch.py", "test_frontier_references.py", "test_saved_git.py", "test_batch_execution_example.py"},
            {Path(test).name for test in plan.tests},
        )
        self.assertNotIn("test_frontier_provenance.py", {Path(test).name for test in plan.tests})

    def test_fixture_changes_select_their_current_or_legacy_consumers(self) -> None:
        fixtures = f"{WORKFLOW}/frontier-optimization/scripts/fixtures/"
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
            (f"{WORKFLOW}/frame-optimization/references/task-documents.md",),
            "affected",
        )

        self.assertEqual(plan.tests, (MODULE.FRAME_TEST.as_posix(),))
        self.assertTrue(plan.run_bundle_validator)
        self.assertFalse(plan.release)

    def test_measurement_designer_change_selects_only_frame_contract_tests(self) -> None:
        plan = MODULE.select_checks(
            (f"{WORKFLOW}/design-measurement/SKILL.md",),
            "affected",
        )

        self.assertEqual(plan.tests, (MODULE.FRAME_TEST.as_posix(),))
        self.assertTrue(plan.run_bundle_validator)
        self.assertFalse(plan.release)

    def test_implementation_designer_change_selects_only_design_contract_tests(self) -> None:
        plan = MODULE.select_checks(
            (f"{WORKFLOW}/design-implementation/SKILL.md",),
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
            (f"{WORKFLOW}/frontier-optimization/references/learning-loop.md",),
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
            (f"{WORKFLOW}/run-frontier-batch/scripts/batch_execution_example.py",),
            "affected",
        )
        self.assertEqual(plan.tests, (example,))
        self.assertFalse(plan.release)
        batch_plan = MODULE.select_checks(
            (f"{WORKFLOW}/frontier-optimization/scripts/frontier_batch.py",),
            "affected",
        )
        self.assertIn(example, batch_plan.tests)
        release_plan = MODULE.select_checks((), "release")
        self.assertIn(example, release_plan.tests)

    def test_validator_change_selects_its_group_and_end_to_end_seam(self) -> None:
        plan = MODULE.select_checks(
            (f"{WORKFLOW}/frontier-optimization/scripts/validate_batch_result.py",),
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
            (f"{WORKFLOW}/frontier-optimization/scripts/frontier_provenance/graph.py",),
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
            (f"{WORKFLOW}/frontier-optimization/scripts/frontier_review/preparation.py",),
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
                f"{WORKFLOW}/frontier-optimization/scripts/"
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
            (f"{WORKFLOW}/frontier-optimization/references/frontier-core.md",),
            "affected",
        )

        self.assertTrue(plan.release)
        self.assertEqual(
            plan.tests,
            tuple(sorted(path.as_posix() for path in MODULE.CURRENT_RELEASE_TESTS)),
        )

    def test_unknown_workflow_python_escalates_instead_of_skipping(self) -> None:
        plan = MODULE.select_checks(
            (f"{WORKFLOW}/frontier-optimization/scripts/new_validator.py",),
            "affected",
        )

        self.assertTrue(plan.release)
        self.assertIn("affected mode escalated to the current contract suite", plan.reasons)

    def test_fast_mode_runs_no_pytest_group(self) -> None:
        plan = MODULE.select_checks(
            (f"{WORKFLOW}/frontier-optimization/SKILL.md",),
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
            f"{WORKFLOW}/frontier-optimization/references/learning-loop.md",
            f"{WORKFLOW}/frame-optimization/SKILL.md",
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
