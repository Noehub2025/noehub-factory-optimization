#!/usr/bin/env python3
"""Regression tests for Frontier execution-baseline freezing."""

from __future__ import annotations

import hashlib
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


SCRIPT = Path(__file__).with_name("freeze_execution_baseline.py")
SPEC = importlib.util.spec_from_file_location("freeze_execution_baseline", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def file_identity(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def write_draft(root: Path, baseline: list[dict]) -> Path:
    draft = {
        "execution_start_path": "artifacts/frontier/B900/execution-start.yaml",
        "packet_path": "artifacts/frontier/B900/packet.yaml",
        "packet_id": "B900-packet-sha256:example",
        "batch_id": "B900",
        "campaign_generation": 2,
        "recorded_by": "frontier-optimization/1",
        "recorded_at": "2026-08-12T08:00:00Z",
        "lifecycle_transition": None,
        "post_transition_baseline": baseline,
        "unchanged_authority_check": "matched",
        "worker_may_start": "yes",
        "blocker": None,
    }
    path = root / "draft.yaml"
    path.write_text(yaml.safe_dump(draft, sort_keys=False))
    return path


class ExecutionBaselineTests(unittest.TestCase):
    def test_freeze_preserves_bytes_after_live_campaign_records_change(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            frontier = root / "docs/task/FRONTIER.md"
            ledger = root / "docs/task/frontier/ledger.md"
            frontier.parent.mkdir(parents=True)
            ledger.parent.mkdir(parents=True)
            frontier.write_bytes(b"campaign_status: running\nversion: start\n")
            ledger.write_bytes(b"Selection: B900\n")
            draft = write_draft(
                root,
                [
                    {"path": "docs/task/FRONTIER.md", "scope": "file", "identity": file_identity(frontier)},
                    {"path": "docs/task/frontier/ledger.md", "scope": "file", "identity": file_identity(ledger)},
                ],
            )
            output = root / "artifacts/frontier/B900/execution-start.yaml"

            frozen = MODULE.freeze(
                draft,
                "artifacts/frontier/B900/execution-baseline/",
                output,
                root.resolve(),
            )
            snapshot_root = root / frozen["baseline_snapshot"]["root"]
            self.assertEqual(
                (snapshot_root / "inputs/docs/task/FRONTIER.md").read_bytes(),
                b"campaign_status: running\nversion: start\n",
            )
            self.assertTrue(MODULE.verify(output, root.resolve(), True)["snapshot_verified"])

            frontier.write_bytes(b"campaign_status: running\nversion: terminal\n")
            ledger.write_bytes(b"Selection: none\n")
            self.assertTrue(MODULE.verify(output, root.resolve(), False)["snapshot_verified"])
            with self.assertRaisesRegex(MODULE.BaselineError, "live baseline drift"):
                MODULE.verify(output, root.resolve(), True)

    def test_identity_mismatch_blocks_before_execution_start_is_written(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "docs/task/FRONTIER.md"
            source.parent.mkdir(parents=True)
            source.write_text("current\n")
            draft = write_draft(
                root,
                [{"path": "docs/task/FRONTIER.md", "scope": "file", "identity": f"sha256:{'0' * 64}"}],
            )
            output = root / "artifacts/frontier/B900/execution-start.yaml"
            with self.assertRaisesRegex(MODULE.BaselineError, "identity mismatch"):
                MODULE.freeze(
                    draft,
                    "artifacts/frontier/B900/execution-baseline/",
                    output,
                    root.resolve(),
                )
            self.assertFalse(output.exists())

    def test_missing_snapshot_member_blocks_recovery_verification(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "src/config.yaml"
            source.parent.mkdir(parents=True)
            source.write_text("value: 1\n")
            draft = write_draft(
                root,
                [{"path": "src/config.yaml", "scope": "file", "identity": file_identity(source)}],
            )
            output = root / "artifacts/frontier/B900/execution-start.yaml"
            frozen = MODULE.freeze(
                draft,
                "artifacts/frontier/B900/execution-baseline/",
                output,
                root.resolve(),
            )
            snapshot_root = root / frozen["baseline_snapshot"]["root"]
            (snapshot_root / "inputs/src/config.yaml").unlink()
            with self.assertRaisesRegex(MODULE.BaselineError, "snapshot file is missing"):
                MODULE.verify(output, root.resolve(), False)

    def test_undeclared_snapshot_member_blocks_recovery_verification(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "src/config.yaml"
            source.parent.mkdir(parents=True)
            source.write_text("value: 1\n")
            draft = write_draft(
                root,
                [{"path": "src/config.yaml", "scope": "file", "identity": file_identity(source)}],
            )
            output = root / "artifacts/frontier/B900/execution-start.yaml"
            frozen = MODULE.freeze(
                draft,
                "artifacts/frontier/B900/execution-baseline/",
                output,
                root.resolve(),
            )
            snapshot_root = root / frozen["baseline_snapshot"]["root"]
            (snapshot_root / "undeclared.txt").write_text("not in manifest\n")
            with self.assertRaisesRegex(MODULE.BaselineError, "undeclared"):
                MODULE.verify(output, root.resolve(), False)

    def test_subtree_identity_and_members_are_recoverable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "src/tree"
            source.mkdir(parents=True)
            (source / "a.txt").write_text("a\n")
            (source / "nested").mkdir()
            (source / "nested/b.txt").write_text("b\n")
            _, identity = MODULE.subtree_inventory(source)
            draft = write_draft(
                root,
                [{"path": "src/tree", "scope": "subtree", "identity": identity}],
            )
            output = root / "artifacts/frontier/B900/execution-start.yaml"
            MODULE.freeze(
                draft,
                "artifacts/frontier/B900/execution-baseline/",
                output,
                root.resolve(),
            )
            result = MODULE.verify(output, root.resolve(), True)
            self.assertEqual(result["input_count"], 1)

    def test_existing_execution_baseline_root_is_never_reused(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "src/config.yaml"
            source.parent.mkdir(parents=True)
            source.write_text("value: 1\n")
            draft = write_draft(
                root,
                [{"path": "src/config.yaml", "scope": "file", "identity": file_identity(source)}],
            )
            baseline_root = root / "artifacts/frontier/B900/execution-baseline"
            baseline_root.mkdir(parents=True)
            output = root / "artifacts/frontier/B900/execution-start.yaml"
            with self.assertRaisesRegex(MODULE.BaselineError, "refusing to reuse"):
                MODULE.freeze(
                    draft,
                    "artifacts/frontier/B900/execution-baseline/",
                    output,
                    root.resolve(),
                )

    def test_baseline_subtree_cannot_contain_execution_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            artifacts = root / "artifacts"
            artifacts.mkdir()
            (artifacts / "authority.yaml").write_text("ready: true\n")
            _, identity = MODULE.subtree_inventory(artifacts)
            draft = write_draft(
                root,
                [{"path": "artifacts", "scope": "subtree", "identity": identity}],
            )
            output = root / "artifacts/frontier/B900/execution-start.yaml"
            with self.assertRaisesRegex(MODULE.BaselineError, "contains a Coordinator"):
                MODULE.freeze(
                    draft,
                    "artifacts/frontier/B900/execution-baseline/",
                    output,
                    root.resolve(),
                )


if __name__ == "__main__":
    unittest.main()
