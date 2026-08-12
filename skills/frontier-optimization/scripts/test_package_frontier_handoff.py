#!/usr/bin/env python3
"""Regression tests for immutable Frontier closeout packages."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


SCRIPT = Path(__file__).with_name("package_frontier_handoff.py")
SPEC = importlib.util.spec_from_file_location("package_frontier_handoff", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def file_identity(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def create_sources(root: Path) -> dict:
    task = root / "docs/task"
    evidence = root / "artifacts/frontier/B900"
    task.mkdir(parents=True)
    evidence.mkdir(parents=True)
    (task / "FRONTIER.md").write_text("campaign_status: halted\n")
    (task / "log.md").write_text("CLOSEOUT_COMPLETE\n")
    (evidence / "result.yaml").write_text("outcome: completed\n")
    return {
        "package_plan_path": "artifacts/frontier/packages/G002/plan.yaml",
        "campaign_generation": 2,
        "campaign_status": "halted",
        "closeout_identity": "X025-sha256:example",
        "final_handoff_identity": "handoff-sha256:example",
        "final_budget_identity": "budget-sha256:example",
        "authority_effect": "none",
        "entries": [
            {
                "source": "docs/task/FRONTIER.md",
                "scope": "file",
                "identity": file_identity(task / "FRONTIER.md"),
                "destination": "task/FRONTIER.md",
                "role": "final-state",
            },
            {
                "source": "docs/task/log.md",
                "scope": "file",
                "identity": file_identity(task / "log.md"),
                "destination": "task/log.md",
                "role": "final-handoff",
            },
            {
                "source": "artifacts/frontier/B900/",
                "scope": "subtree",
                "identity": MODULE.subtree_inventory(evidence)[1],
                "destination": "evidence/B900",
                "role": "terminal-result",
            },
        ],
    }


class HandoffPackageTests(unittest.TestCase):
    def test_valid_plan_builds_atomic_content_addressed_package(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            draft = create_sources(root)
            draft_result = MODULE.validate_plan(draft, "draft", root)
            self.assertTrue(draft_result["package_ready"], draft_result["findings"])
            frozen = copy.deepcopy(draft)
            frozen["package_id"] = draft_result["computed_package_id"]
            plan = root / "plan.yaml"
            plan.write_text(yaml.safe_dump(frozen, sort_keys=False))
            output_parent = root / "packages"
            package_root = MODULE.build(plan, output_parent, root)
            result = MODULE.verify(package_root)
            self.assertTrue(result["package_verified"])
            self.assertEqual(result["file_count"], 3)
            self.assertEqual(package_root.parent, output_parent)

    def test_source_change_after_plan_validation_blocks_publication(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            draft = create_sources(root)
            frozen = copy.deepcopy(draft)
            frozen["package_id"] = MODULE.validate_plan(draft, "draft", root)["computed_package_id"]
            plan = root / "plan.yaml"
            plan.write_text(yaml.safe_dump(frozen, sort_keys=False))
            (root / "docs/task/FRONTIER.md").write_text("changed\n")
            output_parent = root / "packages"
            with self.assertRaisesRegex(MODULE.PackageError, "identity mismatch"):
                MODULE.build(plan, output_parent, root)
            self.assertFalse(output_parent.exists())

    def test_duplicate_destination_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            plan = create_sources(root)
            plan["entries"][1]["destination"] = plan["entries"][0]["destination"]
            result = MODULE.validate_plan(plan, "draft", root)
            self.assertIn(
                "PACKAGE_ENTRY_INVALID",
                {item["code"] for item in result["findings"]},
            )

    def test_git_cache_and_path_escape_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            plan = create_sources(root)
            plan["entries"][0]["source"] = ".git/config"
            plan["entries"][1]["destination"] = "../outside"
            result = MODULE.validate_plan(plan, "draft", root)
            details = "\n".join(item["detail"] for item in result["findings"])
            self.assertIn("excluded cache or version-control", details)
            self.assertIn("escapes", details)

    def test_package_remains_recoverable_after_live_sources_change(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            draft = create_sources(root)
            frozen = copy.deepcopy(draft)
            frozen["package_id"] = MODULE.validate_plan(draft, "draft", root)["computed_package_id"]
            plan = root / "plan.yaml"
            plan.write_text(yaml.safe_dump(frozen, sort_keys=False))
            package_root = MODULE.build(plan, root / "packages", root)
            (root / "docs/task/FRONTIER.md").write_text("later generation\n")
            (root / "artifacts/frontier/B900/result.yaml").unlink()
            self.assertTrue(MODULE.verify(package_root)["package_verified"])

    def test_existing_package_root_is_never_reused(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            draft = create_sources(root)
            frozen = copy.deepcopy(draft)
            frozen["package_id"] = MODULE.validate_plan(draft, "draft", root)["computed_package_id"]
            plan = root / "plan.yaml"
            plan.write_text(yaml.safe_dump(frozen, sort_keys=False))
            output_parent = root / "packages"
            MODULE.build(plan, output_parent, root)
            with self.assertRaisesRegex(MODULE.PackageError, "refusing to reuse"):
                MODULE.build(plan, output_parent, root)

    def test_tampered_frozen_plan_or_manifest_blocks_offline_verification(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            draft = create_sources(root)
            frozen = copy.deepcopy(draft)
            frozen["package_id"] = MODULE.validate_plan(draft, "draft", root)["computed_package_id"]
            plan = root / "plan.yaml"
            plan.write_text(yaml.safe_dump(frozen, sort_keys=False))
            package_root = MODULE.build(plan, root / "packages", root)
            packaged_plan = package_root / "package-plan.yaml"
            original_plan = packaged_plan.read_bytes()
            changed_plan = yaml.safe_load(original_plan)
            changed_plan["final_budget_identity"] = "budget-sha256:changed"
            packaged_plan.write_text(yaml.safe_dump(changed_plan, sort_keys=False))
            with self.assertRaisesRegex(MODULE.PackageError, "plan identity mismatch"):
                MODULE.verify(package_root)
            packaged_plan.write_bytes(original_plan)
            manifest = package_root / "manifest.json"
            manifest.write_text(manifest.read_text().replace("final-state", "other-role"))
            with self.assertRaisesRegex(MODULE.PackageError, "does not reproduce"):
                MODULE.verify(package_root)


if __name__ == "__main__":
    unittest.main()
