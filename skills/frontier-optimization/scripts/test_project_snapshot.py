#!/usr/bin/env python3
"""Regression tests for filtered Frontier project snapshots."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path


SCRIPT = Path(__file__).with_name("project_snapshot.py")
SPEC = importlib.util.spec_from_file_location("project_snapshot", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return result.stdout.decode().strip()


def initialize(root: Path) -> None:
    git(root, "init", "-q")
    (root / "project.txt").write_text("initial\n")
    git(root, "add", "project.txt")
    git(
        root,
        "-c",
        "user.name=Snapshot Test",
        "-c",
        "user.email=snapshot@example.invalid",
        "commit",
        "-qm",
        "initial",
    )


class ProjectSnapshotTests(unittest.TestCase):
    @staticmethod
    def rebind(manifest: dict) -> dict:
        manifest["snapshot_id"] = MODULE.compute_snapshot_id(manifest)
        return manifest

    def test_capture_uses_live_dirty_and_explicit_untracked_bytes_without_mutating_git_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            initialize(root)
            (root / "project.txt").write_text("dirty\n")
            (root / "untracked.txt").write_text("untracked\n")
            status_before = git(root, "status", "--porcelain=v1")
            index_before = git(root, "write-tree")

            manifest = MODULE.capture(
                root,
                manifest_path=root / "frontier/reviews/R900-project-snapshot.yaml",
                paths=["project.txt", "untracked.txt"],
                created_at="2026-08-16T00:00:00Z",
            )

            status_after = git(root, "status", "--porcelain=v1")
            self.assertEqual(
                status_before.splitlines(),
                [line for line in status_after.splitlines() if not line.endswith(" frontier/")],
            )
            self.assertEqual(index_before, git(root, "write-tree"))
            self.assertEqual(b"dirty\n", MODULE.member_bytes(root, manifest, "project.txt"))
            self.assertEqual(b"untracked\n", MODULE.member_bytes(root, manifest, "untracked.txt"))
            self.assertTrue(MODULE.verify(root, manifest, require_live=True)["snapshot_verified"])

    def test_forbidden_workflow_path_fails_before_writing_git_objects(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            initialize(root)
            workflow = root / ".agents/skills/frontier/SKILL.md"
            workflow.parent.mkdir(parents=True)
            workflow.write_text("workflow\n")
            count_before = git(root, "count-objects", "-v")

            with self.assertRaisesRegex(MODULE.ProjectSnapshotError, "outside project evidence"):
                MODULE.capture(
                    root,
                    manifest_path=root / "frontier/reviews/R900-project-snapshot.yaml",
                    paths=[".agents/skills/frontier/SKILL.md"],
                    created_at="2026-08-16T00:00:00Z",
                )

            self.assertEqual(count_before, git(root, "count-objects", "-v"))
            self.assertFalse((root / "frontier/reviews/R900-project-snapshot.yaml").exists())

    def test_retired_snapshot_input_path_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            initialize(root)
            copied = root / "frontier/reviews/entry-R899-snapshot/inputs/source.py"
            copied.parent.mkdir(parents=True)
            copied.write_text("copied\n")

            with self.assertRaisesRegex(MODULE.ProjectSnapshotError, "retired copied snapshot"):
                MODULE.capture(
                    root,
                    manifest_path=root / "frontier/reviews/R900-project-snapshot.yaml",
                    paths=["frontier/reviews/entry-R899-snapshot/inputs/source.py"],
                )

    def test_closed_root_finds_ignored_runtime_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            initialize(root)
            (root / ".gitignore").write_text("__pycache__/\n")
            candidate = root / "candidates/B900"
            candidate.mkdir(parents=True)
            (candidate / "main.py").write_text("VALUE = 1\n")
            cache = candidate / "__pycache__"
            cache.mkdir()
            (cache / "main.pyc").write_bytes(b"bytecode")

            with self.assertRaisesRegex(MODULE.ProjectSnapshotError, "runtime artifact"):
                MODULE.capture(
                    root,
                    manifest_path=root / "frontier/reviews/R900-project-snapshot.yaml",
                    paths=["project.txt"],
                    closed_roots=[{"path": "candidates/B900", "expected_members": ["main.py"]}],
                )

    def test_closed_root_rejects_unreported_regular_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            initialize(root)
            candidate = root / "candidates/B900"
            candidate.mkdir(parents=True)
            (candidate / "main.py").write_text("VALUE = 1\n")
            (candidate / "extra.txt").write_text("extra\n")

            with self.assertRaisesRegex(MODULE.ProjectSnapshotError, "inventory mismatch"):
                MODULE.capture(
                    root,
                    manifest_path=root / "frontier/reviews/R900-project-snapshot.yaml",
                    paths=["project.txt"],
                    closed_roots=[{"path": "candidates/B900", "expected_members": ["main.py"]}],
                )

    def test_symbolic_link_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            initialize(root)
            (root / "link.txt").symlink_to(root / "project.txt")

            with self.assertRaisesRegex(MODULE.ProjectSnapshotError, "symbolic link"):
                MODULE.capture(
                    root,
                    manifest_path=root / "frontier/reviews/R900-project-snapshot.yaml",
                    paths=["link.txt"],
                )

    def test_snapshot_commit_remains_reachable_through_single_ref_chain(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            initialize(root)
            first = MODULE.capture(
                root,
                manifest_path=root / "frontier/reviews/R900-project-snapshot.yaml",
                paths=["project.txt"],
                created_at="2026-08-16T00:00:00Z",
            )
            (root / "project.txt").write_text("second\n")
            second = MODULE.capture(
                root,
                manifest_path=root / "frontier/reviews/R901-project-snapshot.yaml",
                paths=["project.txt"],
                created_at="2026-08-16T00:00:01Z",
            )

            self.assertEqual(first["storage"]["commit"], second["storage"]["parent_commit"])
            self.assertEqual(second["storage"]["commit"], git(root, "rev-parse", MODULE.DEFAULT_REF))
            subprocess.run(
                ["git", "-C", str(root), "merge-base", "--is-ancestor", first["storage"]["commit"], MODULE.DEFAULT_REF],
                check=True,
            )

    def test_verify_rejects_ref_outside_dedicated_namespace_even_when_rebound(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            initialize(root)
            manifest = MODULE.capture(
                root,
                manifest_path=root / "frontier/reviews/R900-project-snapshot.yaml",
                paths=["project.txt"],
                created_at="2026-08-16T00:00:00Z",
            )
            manifest["storage"]["ref"] = "HEAD"
            self.rebind(manifest)

            with self.assertRaisesRegex(MODULE.ProjectSnapshotError, "must be exactly"):
                MODULE.verify(root, manifest)

    def test_capture_rejects_alternate_snapshot_ref(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            initialize(root)

            with self.assertRaisesRegex(MODULE.ProjectSnapshotError, "must be exactly"):
                MODULE.capture(
                    root,
                    manifest_path=root / "frontier/reviews/R900-project-snapshot.yaml",
                    paths=["project.txt"],
                    reference="refs/frontier/project-snapshots/alternate",
                    created_at="2026-08-16T00:00:00Z",
                )

    def test_verify_rejects_false_parent_binding_even_when_rebound(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            initialize(root)
            manifest = MODULE.capture(
                root,
                manifest_path=root / "frontier/reviews/R900-project-snapshot.yaml",
                paths=["project.txt"],
                created_at="2026-08-16T00:00:00Z",
            )
            manifest["storage"]["parent_commit"] = "0" * 40
            self.rebind(manifest)

            with self.assertRaisesRegex(MODULE.ProjectSnapshotError, "parent binding"):
                MODULE.verify(root, manifest)

    def test_verify_rejects_self_consistent_runtime_artifact_tree(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            initialize(root)
            cache = root / "candidate/__pycache__"
            cache.mkdir(parents=True)
            (cache / "main.pyc").write_bytes(b"self-consistent bytecode")
            git(root, "add", "-f", "candidate/__pycache__/main.pyc")
            git(
                root,
                "-c",
                "user.name=Snapshot Test",
                "-c",
                "user.email=snapshot@example.invalid",
                "commit",
                "-qm",
                "malicious runtime artifact",
            )
            commit = git(root, "rev-parse", "HEAD")
            parent = git(root, "rev-parse", "HEAD^")
            git(root, "update-ref", MODULE.DEFAULT_REF, commit)
            manifest = {
                "schema": MODULE.SCHEMA,
                "storage": {
                    "commit": commit,
                    "ref": MODULE.DEFAULT_REF,
                    "parent_commit": parent,
                },
                "members": MODULE._tree_members(root, f"{commit}^{{tree}}"),
                "closed_roots": [],
                "external_artifacts": [],
            }
            self.rebind(manifest)

            with self.assertRaisesRegex(MODULE.ProjectSnapshotError, "runtime artifact"):
                MODULE.verify(root, manifest)

    def test_member_change_during_capture_fails_before_ref_publication(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            initialize(root)
            original_tree_members = MODULE._tree_members

            def mutate_after_tree(repo_root: Path, treeish: str):
                members = original_tree_members(repo_root, treeish)
                (root / "project.txt").write_text("changed after staging\n")
                return members

            with mock.patch.object(MODULE, "_tree_members", side_effect=mutate_after_tree):
                with self.assertRaisesRegex(MODULE.ProjectSnapshotError, "changed during"):
                    MODULE.capture(
                        root,
                        manifest_path=root / "frontier/reviews/R900-project-snapshot.yaml",
                        paths=["project.txt"],
                        created_at="2026-08-16T00:00:00Z",
                    )

            self.assertFalse((root / "frontier/reviews/R900-project-snapshot.yaml").exists())
            self.assertNotEqual(0, subprocess.run(
                ["git", "-C", str(root), "rev-parse", "--verify", "--quiet", MODULE.DEFAULT_REF],
                check=False,
            ).returncode)

    def test_live_verification_rejects_executable_mode_drift_both_directions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            initialize(root)
            script = root / "run.sh"
            script.write_text("#!/bin/sh\nexit 0\n")
            for index, (frozen_mode, live_mode) in enumerate(((0o644, 0o755), (0o755, 0o644))):
                script.chmod(frozen_mode)
                manifest = MODULE.capture(
                    root,
                    manifest_path=root / f"frontier/reviews/R{900 + index}-project-snapshot.yaml",
                    paths=["run.sh"],
                    created_at=f"2026-08-16T00:00:0{index}Z",
                )
                script.chmod(live_mode)
                with self.subTest(frozen_mode=frozen_mode, live_mode=live_mode):
                    with self.assertRaisesRegex(MODULE.ProjectSnapshotError, "live project member drift"):
                        MODULE.verify(root, manifest, require_live=True)

    def test_repeated_snapshots_reuse_the_same_content_blob(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            initialize(root)
            object_ids: set[str] = set()
            for index in range(100):
                manifest = MODULE.capture(
                    root,
                    manifest_path=root / f"frontier/reviews/R{900 + index}-project-snapshot.yaml",
                    paths=["project.txt"],
                    created_at=f"2026-08-16T00:{index // 60:02d}:{index % 60:02d}Z",
                )
                record = git(root, "ls-tree", manifest["storage"]["commit"], "project.txt")
                object_ids.add(record.split()[2])

            self.assertEqual(1, len(object_ids))

    def test_manifest_sha256_is_the_only_authority_identity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            initialize(root)
            manifest = MODULE.capture(
                root,
                manifest_path=root / "frontier/reviews/R900-project-snapshot.yaml",
                paths=["project.txt"],
                created_at="2026-08-16T00:00:00Z",
            )
            manifest["members"][0]["file_sha256"] = "0" * 64

            with self.assertRaisesRegex(MODULE.ProjectSnapshotError, "identity is not derived"):
                MODULE.verify(root, manifest)

    def test_content_addressed_artifact_is_reused_and_drift_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            initialize(root)
            source = root / "large-result.bin"
            source.write_bytes(b"measurement evidence")
            first = MODULE.publish_artifact(source, root)
            second = MODULE.publish_artifact(source, root)
            self.assertEqual(first, second)
            manifest = MODULE.capture(
                root,
                manifest_path=root / "frontier/reviews/R900-project-snapshot.yaml",
                paths=["project.txt"],
                external_artifacts=[first],
                created_at="2026-08-16T00:00:00Z",
            )
            self.assertTrue(MODULE.verify(root, manifest)["snapshot_verified"])
            (root / first["locator"]).write_bytes(b"drift")
            with self.assertRaisesRegex(MODULE.ProjectSnapshotError, "identity mismatch"):
                MODULE.verify(root, manifest)

    def test_external_artifact_locator_must_derive_from_sha256(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            initialize(root)
            artifact = root / "artifacts/arbitrary.bin"
            artifact.parent.mkdir(parents=True)
            artifact.write_bytes(b"evidence")
            binding = {
                "locator": "artifacts/arbitrary.bin",
                "size": artifact.stat().st_size,
                "file_sha256": MODULE.sha256_file(artifact),
            }

            with self.assertRaisesRegex(MODULE.ProjectSnapshotError, "not derived"):
                MODULE.capture(
                    root,
                    manifest_path=root / "frontier/reviews/R900-project-snapshot.yaml",
                    paths=["project.txt"],
                    external_artifacts=[binding],
                )

    def test_materialize_recovers_exact_project_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            initialize(root)
            (root / "project.txt").write_text("frozen\n")
            manifest = MODULE.capture(
                root,
                manifest_path=root / "frontier/reviews/R900-project-snapshot.yaml",
                paths=["project.txt"],
                created_at="2026-08-16T00:00:00Z",
            )
            (root / "project.txt").write_text("live drift\n")
            destination = root / "materialized"

            result = MODULE.materialize(root, manifest, destination)

            self.assertTrue(result["materialized"])
            self.assertEqual("frozen\n", (destination / "project.txt").read_text())


if __name__ == "__main__":
    unittest.main()
