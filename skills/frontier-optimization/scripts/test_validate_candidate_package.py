#!/usr/bin/env python3
"""Regression tests for complete candidate-package validation and staging."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


SCRIPT = Path(__file__).with_name("validate_candidate_package.py")
SPEC = importlib.util.spec_from_file_location("validate_candidate_package", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def create_package(root: Path) -> tuple[str, str]:
    candidate = root / "candidates/B900-example"
    candidate.mkdir(parents=True)
    (candidate / "main.py").write_text("def agent(observation, configuration):\n    return {}\n")
    (candidate / "metadata.json").write_text('{"name":"example"}\n')
    members, identity = MODULE.tree_inventory(
        candidate, MODULE.PACKAGE_PATH_SIZE_SHA256_V1
    )
    package_sha256 = identity.removeprefix("sha256:")
    candidate_id = f"B900-example-sha256:{package_sha256}"
    manifest = {
        "candidate_id": candidate_id,
        "source_result_identity": {
            "package_sha256": package_sha256,
            "members": members,
        },
        "code_paths": [
            {"path": item["path"], "sha256": item["sha256"]} for item in members
        ],
    }
    manifest_path = root / "artifacts/frontier/B900/candidate-manifest.yaml"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False))
    return candidate_id, hashlib.sha256(manifest_path.read_bytes()).hexdigest()


def create_final_package(root: Path) -> tuple[str, str, str]:
    candidate_id, _ = create_package(root)
    inventory_path = "artifacts/frontier/B900/package-inventory.yaml"
    inventory = MODULE.write_candidate_inventory(
        root,
        "candidates/B900-example/",
        inventory_path,
        candidate_id,
    )
    evidence_path = root / "artifacts/frontier/B900/engineering/evidence.json"
    evidence_path.parent.mkdir(parents=True)
    evidence_path.write_text(
        json.dumps(
            {
                "inventory_id": inventory["inventory_id"],
                "check": "unit",
                "result": "pass",
            },
            sort_keys=True,
        )
        + "\n"
    )
    review_path = root / "artifacts/frontier/B900/implementation-review.md"
    review_path.write_text(
        "---\n"
        "type: Optimization Frontier Implementation Review\n"
        "status: complete\n"
        "review_result: IMPLEMENTATION_READY\n"
        f"candidate_id: {candidate_id}\n"
        "---\n\n"
        f"Candidate: {candidate_id}\n"
    )
    packet_path = root / "artifacts/frontier/B900/packet.yaml"
    packet_path.write_text("batch_id: B900\n")
    manifest_path = root / "artifacts/frontier/B900/candidate-manifest.yaml"
    manifest = yaml.safe_load(manifest_path.read_text())
    manifest.update(
        {
            "manifest_contract": MODULE.FINAL_MANIFEST_CONTRACT,
            "manifest_state": "final",
            "package_inventory": {
                "path": inventory_path,
                "inventory_id": inventory["inventory_id"],
                "file_sha256": inventory["inventory_sha256"],
            },
            "engineering_evidence": [
                {
                    "path": evidence_path.relative_to(root).as_posix(),
                    "file_sha256": hashlib.sha256(evidence_path.read_bytes()).hexdigest(),
                }
            ],
            "implementation_review": {
                "path": review_path.relative_to(root).as_posix(),
                "file_sha256": hashlib.sha256(review_path.read_bytes()).hexdigest(),
                "review_result": "IMPLEMENTATION_READY",
                "candidate_id": candidate_id,
            },
            "recovery_artifacts": [
                {
                    "role": "packet",
                    "path": packet_path.relative_to(root).as_posix(),
                    "file_sha256": hashlib.sha256(packet_path.read_bytes()).hexdigest(),
                }
            ],
        }
    )
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False))
    return (
        candidate_id,
        inventory_path,
        hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
    )


class CandidatePackageTests(unittest.TestCase):
    def test_complete_package_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate_id, manifest_sha256 = create_package(root)
            result = MODULE.validate_candidate_package(
                root,
                "candidates/B900-example/",
                "artifacts/frontier/B900/candidate-manifest.yaml",
                expected_candidate_id=candidate_id,
                expected_manifest_sha256=manifest_sha256,
            )
            self.assertTrue(result["package_ready"], result["findings"])

    def test_unreported_pycache_blocks_package(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate_id, manifest_sha256 = create_package(root)
            cache = root / "candidates/B900-example/__pycache__/main.pyc"
            cache.parent.mkdir()
            cache.write_bytes(b"bytecode")
            result = MODULE.validate_candidate_package(
                root,
                "candidates/B900-example/",
                "artifacts/frontier/B900/candidate-manifest.yaml",
                expected_candidate_id=candidate_id,
                expected_manifest_sha256=manifest_sha256,
            )
            codes = {item["code"] for item in result["findings"]}
            self.assertIn("CANDIDATE_MEMBER_MISMATCH", codes)
            self.assertIn("EXPECTED_CANDIDATE_IDENTITY_MISMATCH", codes)

    def test_self_consistently_declared_pycache_still_blocks_package(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            create_package(root)
            candidate = root / "candidates/B900-example"
            cache = candidate / "__pycache__/main.pyc"
            cache.parent.mkdir()
            cache.write_bytes(b"declared bytecode")
            members, identity = MODULE.tree_inventory(
                candidate, MODULE.PACKAGE_PATH_SIZE_SHA256_V1
            )
            package_sha256 = identity.removeprefix("sha256:")
            candidate_id = f"B900-example-sha256:{package_sha256}"
            manifest_path = root / "artifacts/frontier/B900/candidate-manifest.yaml"
            manifest_path.write_text(
                yaml.safe_dump(
                    {
                        "candidate_id": candidate_id,
                        "source_result_identity": {
                            "package_sha256": package_sha256,
                            "members": members,
                        },
                        "code_paths": [
                            {"path": item["path"], "sha256": item["sha256"]}
                            for item in members
                        ],
                    },
                    sort_keys=False,
                )
            )

            result = MODULE.validate_candidate_package(
                root,
                "candidates/B900-example/",
                "artifacts/frontier/B900/candidate-manifest.yaml",
                expected_candidate_id=candidate_id,
                expected_manifest_sha256=hashlib.sha256(
                    manifest_path.read_bytes()
                ).hexdigest(),
            )

            self.assertFalse(result["package_ready"])
            self.assertIn(
                "FORBIDDEN_RUNTIME_ARTIFACT",
                {item["code"] for item in result["findings"]},
            )

    def test_symlinked_member_blocks_package(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate_id, manifest_sha256 = create_package(root)
            outside = root / "outside.py"
            outside.write_text("outside\n")
            (root / "candidates/B900-example/link.py").symlink_to(outside)
            result = MODULE.validate_candidate_package(
                root,
                "candidates/B900-example/",
                "artifacts/frontier/B900/candidate-manifest.yaml",
                expected_candidate_id=candidate_id,
                expected_manifest_sha256=manifest_sha256,
            )
            self.assertIn(
                "CANDIDATE_PACKAGE_UNREADABLE",
                {item["code"] for item in result["findings"]},
            )

    def test_isolated_stage_and_python_bytecode_suppression_preserve_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate_id, manifest_sha256 = create_package(root)
            result = MODULE.stage_candidate_package(
                root,
                "candidates/B900-example/",
                "artifacts/frontier/B900/candidate-manifest.yaml",
                "runtime/B900/attempt-1/",
                expected_candidate_id=candidate_id,
                expected_manifest_sha256=manifest_sha256,
            )
            self.assertTrue(result["staged"])
            environment = dict(os.environ)
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            subprocess.run(
                [sys.executable, "-c", "import main"],
                cwd=root / "runtime/B900/attempt-1",
                env=environment,
                check=True,
            )
            self.assertFalse((root / "candidates/B900-example/__pycache__").exists())
            self.assertFalse((root / "runtime/B900/attempt-1/__pycache__").exists())

    def test_inventory_stages_candidate_before_final_manifest_exists(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate_id, _ = create_package(root)
            manifest_path = root / "artifacts/frontier/B900/candidate-manifest.yaml"
            manifest_path.unlink()
            inventory = MODULE.write_candidate_inventory(
                root,
                "candidates/B900-example/",
                "artifacts/frontier/B900/package-inventory.yaml",
                candidate_id,
            )
            result = MODULE.stage_candidate_inventory(
                root,
                "candidates/B900-example/",
                "artifacts/frontier/B900/package-inventory.yaml",
                "runtime/B900/attempt-1/",
                expected_candidate_id=candidate_id,
                expected_inventory_id=inventory["inventory_id"],
                expected_inventory_sha256=inventory["inventory_sha256"],
            )
            self.assertTrue(result["staged"], result["findings"])

    def test_inventory_publication_is_idempotent_for_identical_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate_id, _ = create_package(root)
            path = "artifacts/frontier/B900/package-inventory.yaml"

            first = MODULE.write_candidate_inventory(
                root, "candidates/B900-example/", path, candidate_id
            )
            retry = MODULE.write_candidate_inventory(
                root, "candidates/B900-example/", path, candidate_id
            )

            self.assertEqual(first["publication_status"], "created")
            self.assertEqual(retry["publication_status"], "already-present-identical")
            self.assertEqual(first["inventory_id"], retry["inventory_id"])
            self.assertEqual(first["inventory_sha256"], retry["inventory_sha256"])

    def test_inventory_publication_rejects_conflicting_retry(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate_id, _ = create_package(root)
            path = "artifacts/frontier/B900/package-inventory.yaml"
            MODULE.write_candidate_inventory(
                root, "candidates/B900-example/", path, candidate_id
            )
            (root / path).write_text("conflict\n")

            with self.assertRaisesRegex(
                MODULE.IdentityBindingError, "already exists with different bytes"
            ):
                MODULE.write_candidate_inventory(
                    root, "candidates/B900-example/", path, candidate_id
                )

    def test_cli_inventory_then_stage_requires_no_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate_id, _ = create_package(root)
            (root / "artifacts/frontier/B900/candidate-manifest.yaml").unlink()
            environment = dict(os.environ)
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            write = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "candidates/B900-example/",
                    "--repo-root",
                    str(root),
                    "--expected-candidate-id",
                    candidate_id,
                    "--write-inventory",
                    "artifacts/frontier/B900/package-inventory.yaml",
                ],
                env=environment,
                capture_output=True,
                text=True,
            )
            self.assertEqual(write.returncode, 0, write.stderr)
            written = json.loads(write.stdout)
            stage = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "candidates/B900-example/",
                    "--repo-root",
                    str(root),
                    "--inventory-path",
                    "artifacts/frontier/B900/package-inventory.yaml",
                    "--expected-candidate-id",
                    candidate_id,
                    "--expected-inventory-id",
                    written["inventory_id"],
                    "--expected-inventory-sha256",
                    written["inventory_sha256"],
                    "--stage-root",
                    "runtime/B900/attempt-1/",
                ],
                env=environment,
                capture_output=True,
                text=True,
            )
            self.assertEqual(stage.returncode, 0, stage.stderr)
            self.assertTrue(json.loads(stage.stdout)["staged"])

    def test_inventory_detects_root_mutation_before_staging(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate_id, _ = create_package(root)
            MODULE.write_candidate_inventory(
                root,
                "candidates/B900-example/",
                "artifacts/frontier/B900/package-inventory.yaml",
                candidate_id,
            )
            (root / "candidates/B900-example/main.py").write_text("changed\n")
            result = MODULE.validate_candidate_inventory(
                root,
                "candidates/B900-example/",
                "artifacts/frontier/B900/package-inventory.yaml",
            )
            self.assertFalse(result["inventory_ready"])
            self.assertIn(
                "CANDIDATE_PACKAGE_UNREADABLE",
                {item["code"] for item in result["findings"]},
            )

    def test_final_manifest_binds_inventory_and_completed_engineering_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate_id, _, manifest_sha256 = create_final_package(root)
            result = MODULE.validate_candidate_package(
                root,
                "candidates/B900-example/",
                "artifacts/frontier/B900/candidate-manifest.yaml",
                expected_candidate_id=candidate_id,
                expected_manifest_sha256=manifest_sha256,
                require_final_manifest=True,
            )
            self.assertTrue(result["package_ready"], result["findings"])

    def test_final_manifest_requires_positive_review_of_exact_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate_id, _, _ = create_final_package(root)
            manifest_path = root / "artifacts/frontier/B900/candidate-manifest.yaml"
            manifest = yaml.safe_load(manifest_path.read_text())
            manifest.pop("implementation_review")
            manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False))
            result = MODULE.validate_candidate_package(
                root,
                "candidates/B900-example/",
                "artifacts/frontier/B900/candidate-manifest.yaml",
                expected_candidate_id=candidate_id,
                require_final_manifest=True,
            )
            self.assertFalse(result["package_ready"])
            self.assertIn(
                "IMPLEMENTATION_REVIEW_BINDING_INVALID",
                {item["code"] for item in result["findings"]},
            )

    def test_manifest_cannot_relabel_a_nonpositive_review_as_ready(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate_id, _, _ = create_final_package(root)
            manifest_path = root / "artifacts/frontier/B900/candidate-manifest.yaml"
            manifest = yaml.safe_load(manifest_path.read_text())
            review_path = root / manifest["implementation_review"]["path"]
            review_path.write_text(
                "---\n"
                "type: Optimization Frontier Implementation Review\n"
                "status: complete\n"
                "review_result: IMPLEMENTATION_REPAIR_REQUIRED\n"
                f"candidate_id: {candidate_id}\n"
                "---\n"
            )
            manifest["implementation_review"]["file_sha256"] = hashlib.sha256(
                review_path.read_bytes()
            ).hexdigest()
            manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False))
            result = MODULE.validate_candidate_package(
                root,
                "candidates/B900-example/",
                "artifacts/frontier/B900/candidate-manifest.yaml",
                expected_candidate_id=candidate_id,
                require_final_manifest=True,
            )
            self.assertFalse(result["package_ready"])
            self.assertIn(
                "IMPLEMENTATION_REVIEW_BINDING_INVALID",
                {item["code"] for item in result["findings"]},
            )

    def test_preliminary_manifest_cannot_publish_materialized_result(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate_id, manifest_sha256 = create_package(root)
            result = MODULE.validate_candidate_package(
                root,
                "candidates/B900-example/",
                "artifacts/frontier/B900/candidate-manifest.yaml",
                expected_candidate_id=candidate_id,
                expected_manifest_sha256=manifest_sha256,
                require_final_manifest=True,
            )
            self.assertFalse(result["package_ready"])
            self.assertIn(
                "FINAL_MANIFEST_CONTRACT_INVALID",
                {item["code"] for item in result["findings"]},
            )

    def test_engineering_evidence_cannot_depend_on_final_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate_id, _, _ = create_final_package(root)
            manifest_path = root / "artifacts/frontier/B900/candidate-manifest.yaml"
            manifest = yaml.safe_load(manifest_path.read_text())
            evidence_path = root / manifest["engineering_evidence"][0]["path"]
            evidence_path.write_text(
                f"inventory_id: {manifest['package_inventory']['inventory_id']}\n"
                "depends_on: artifacts/frontier/B900/candidate-manifest.yaml\n"
            )
            manifest["engineering_evidence"][0]["file_sha256"] = hashlib.sha256(
                evidence_path.read_bytes()
            ).hexdigest()
            manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False))
            result = MODULE.validate_candidate_package(
                root,
                "candidates/B900-example/",
                "artifacts/frontier/B900/candidate-manifest.yaml",
                expected_candidate_id=candidate_id,
                require_final_manifest=True,
            )
            self.assertFalse(result["package_ready"])
            self.assertIn(
                "ENGINEERING_EVIDENCE_INVALID",
                {item["code"] for item in result["findings"]},
            )

    def test_engineering_evidence_must_bind_package_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate_id, _, _ = create_final_package(root)
            manifest_path = root / "artifacts/frontier/B900/candidate-manifest.yaml"
            manifest = yaml.safe_load(manifest_path.read_text())
            evidence_path = root / manifest["engineering_evidence"][0]["path"]
            evidence_path.write_text('{"check":"unit","result":"pass"}\n')
            manifest["engineering_evidence"][0]["file_sha256"] = hashlib.sha256(
                evidence_path.read_bytes()
            ).hexdigest()
            manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False))

            result = MODULE.validate_candidate_package(
                root,
                "candidates/B900-example/",
                "artifacts/frontier/B900/candidate-manifest.yaml",
                expected_candidate_id=candidate_id,
                require_final_manifest=True,
            )

            self.assertFalse(result["package_ready"])
            self.assertIn(
                "ENGINEERING_EVIDENCE_INVALID",
                {item["code"] for item in result["findings"]},
            )

    def test_final_manifest_cannot_bind_downstream_result(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate_id, _, _ = create_final_package(root)
            result_path = root / "artifacts/frontier/B900/result.yaml"
            result_path.write_text("outcome: completed\n")
            manifest_path = root / "artifacts/frontier/B900/candidate-manifest.yaml"
            manifest = yaml.safe_load(manifest_path.read_text())
            manifest["recovery_artifacts"].append(
                {
                    "role": "result",
                    "path": result_path.relative_to(root).as_posix(),
                    "file_sha256": hashlib.sha256(result_path.read_bytes()).hexdigest(),
                }
            )
            manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False))
            result = MODULE.validate_candidate_package(
                root,
                "candidates/B900-example/",
                "artifacts/frontier/B900/candidate-manifest.yaml",
                expected_candidate_id=candidate_id,
                require_final_manifest=True,
                prohibited_downstream_paths=("artifacts/frontier/B900/result.yaml",),
            )
            self.assertFalse(result["package_ready"])
            self.assertIn(
                "FINAL_MANIFEST_DOWNSTREAM_DEPENDENCY",
                {item["code"] for item in result["findings"]},
            )


if __name__ == "__main__":
    unittest.main()
