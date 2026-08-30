"""Focused checks for current versus legacy Frontier bundle readiness."""

from __future__ import annotations

import importlib.util
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("validate_frontier_skill_bundle.py")
SPEC = importlib.util.spec_from_file_location("validate_frontier_skill_bundle", SCRIPT)
if SPEC is None or SPEC.loader is None:  # pragma: no cover
    raise RuntimeError("unable to load bundle validator")
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class CurrentBundleReadinessTests(unittest.TestCase):
    def test_live_current_and_legacy_contracts_are_valid(self) -> None:
        result = MODULE.validate(SCRIPT.parents[2])

        self.assertTrue(result["bundle_ready"], result["findings"])
        self.assertTrue(
            result["legacy_compatibility_ready"], result["legacy_findings"]
        )

    def test_current_contract_failure_blocks_current_readiness(self) -> None:
        with self._copy_skills() as root:
            runtime = root / "frontier-optimization/scripts/frontier_batch.py"
            runtime.write_text(
                runtime.read_text().replace("class OperationBinding:", "class RemovedBinding:")
            )

            result = MODULE.validate(root)

        self.assertFalse(result["bundle_ready"])
        self.assertIn(
            "CURRENT_BATCH_CONTRACT_INVALID",
            {finding["code"] for finding in result["findings"]},
        )

    def test_legacy_contract_failure_does_not_block_current_readiness(self) -> None:
        with self._copy_skills() as root:
            validator = root / "frontier-optimization/scripts/validate_batch_packet.py"
            validator.write_text(
                validator.read_text().replace(
                    'VALIDATOR = "frontier-batch-packet-preflight/9"',
                    'VALIDATOR = "removed-legacy-validator"',
                )
            )

            result = MODULE.validate(root)

        self.assertTrue(result["bundle_ready"], result["findings"])
        self.assertFalse(result["legacy_compatibility_ready"])
        self.assertIn(
            "RESULT_CONTRACT_INVALID",
            {finding["code"] for finding in result["legacy_findings"]},
        )

    def test_current_source_closure_excludes_legacy_validators(self) -> None:
        import yaml

        root = SCRIPT.parents[2]
        manifest = yaml.safe_load(
            (root / "frontier-optimization/references/source-modules.yaml").read_text()
        )
        current = MODULE.source_module_subset(manifest, "release-validation")
        closure = MODULE.validate_source_modules(current, root)["release-validation"]

        self.assertIn("frontier-optimization/scripts/frontier_batch.py", closure)
        self.assertNotIn("frontier-optimization/scripts/validate_batch_packet.py", closure)
        self.assertNotIn("frontier-optimization/references/batch-interface.md", closure)

    def _copy_skills(self):
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name) / "skills"
        shutil.copytree(
            SCRIPT.parents[2],
            root,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )

        class CopiedSkills:
            def __enter__(self):
                return root

            def __exit__(self, *args):
                temporary.cleanup()

        return CopiedSkills()


if __name__ == "__main__":
    unittest.main()
