#!/usr/bin/env python3
"""Regression tests for the Frontier five-Skill bundle validator."""

from __future__ import annotations

import importlib.util
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("validate_frontier_skill_bundle.py")
SPEC = importlib.util.spec_from_file_location("validate_frontier_skill_bundle", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class FrontierSkillBundleTests(unittest.TestCase):
    def test_live_five_skill_bundle_is_valid_and_content_addressed(self) -> None:
        skills_root = SCRIPT.parents[2]
        result = MODULE.validate(skills_root)
        self.assertTrue(result["bundle_ready"], result["findings"])
        self.assertEqual(set(result["expected_skills"]), set(MODULE.EXPECTED_SKILLS))
        self.assertEqual(len(result["bundle_sha256"]), 64)
        self.assertGreater(len(result["source_manifest"]), 20)

    def test_sixth_claim_reviewer_is_rejected(self) -> None:
        live_root = SCRIPT.parents[2]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "skills"
            shutil.copytree(live_root, root, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            extra = root / "review-frontier-claims"
            extra.mkdir()
            result = MODULE.validate(root)
            self.assertIn(
                "EXTRA_REVIEWER_SKILL",
                {item["code"] for item in result["findings"]},
            )

    def test_worker_cannot_disable_implicit_invocation(self) -> None:
        live_root = SCRIPT.parents[2]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "skills"
            shutil.copytree(live_root, root, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            metadata = root / "run-frontier-batch/agents/openai.yaml"
            metadata.write_text(metadata.read_text().replace("true", "false"))
            result = MODULE.validate(root)
            self.assertIn(
                "INVOCATION_POLICY_INVALID",
                {item["code"] for item in result["findings"]},
            )

    def test_host_absolute_path_is_not_portable(self) -> None:
        live_root = SCRIPT.parents[2]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "skills"
            shutil.copytree(live_root, root, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            skill = root / "research-frontier/SKILL.md"
            skill.write_text(skill.read_text() + "\nRead /Users/example/private.md.\n")
            result = MODULE.validate(root)
            self.assertIn(
                "HOST_PATH_NOT_PORTABLE",
                {item["code"] for item in result["findings"]},
            )


if __name__ == "__main__":
    unittest.main()
