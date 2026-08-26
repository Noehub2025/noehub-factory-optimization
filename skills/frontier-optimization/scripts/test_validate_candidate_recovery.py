#!/usr/bin/env python3
"""Regression tests for byte-identical candidate recovery preflight."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


SCRIPT = Path(__file__).with_name("validate_candidate_recovery.py")
SPEC = importlib.util.spec_from_file_location("validate_candidate_recovery", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)
WORKFLOW_SOURCE_IDENTITY = "sha256:" + "b" * 64


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def create_candidate(root: Path) -> tuple[str, str]:
    candidate = root / "candidates/B900-example"
    candidate.mkdir(parents=True)
    (candidate / "main.py").write_text("def agent(observation, configuration):\n    return {}\n")
    (candidate / "metadata.json").write_text('{"name":"example"}\n')
    members, package_sha256 = MODULE.package_inventory(candidate)
    candidate_id = f"B900-example-sha256:{package_sha256}"
    inventory = {
        "contract_version": "frontier-candidate-package-inventory/1",
        "candidate_root": "candidates/B900-example",
        "identity_algorithm": "frontier-package-path-size-sha256/1",
        "candidate_id": candidate_id,
        "package_sha256": package_sha256,
        "members": members,
    }
    inventory_payload = yaml.safe_dump(inventory, sort_keys=False, allow_unicode=True).encode()
    inventory["inventory_id"] = "candidate-package-inventory-sha256:" + hashlib.sha256(
        inventory_payload
    ).hexdigest()
    inventory_path = root / "artifacts/frontier/B900/candidate-package-inventory.yaml"
    inventory_path.parent.mkdir(parents=True)
    inventory_path.write_text(yaml.safe_dump(inventory, sort_keys=False))
    engineering_path = root / "artifacts/frontier/B900/engineering-evidence.yaml"
    engineering_path.write_text(f"inventory_id: {inventory['inventory_id']}\n")
    recovery_path = root / "artifacts/frontier/B900/recovery-source.yaml"
    recovery_path.write_text("source: recoverable\n")
    manifest = {
        "manifest_contract": "frontier-candidate-manifest/2",
        "manifest_state": "final",
        "candidate_id": candidate_id,
        "workflow_source_identity": WORKFLOW_SOURCE_IDENTITY,
        "campaign_generation": 2,
        "batch_id": "B900",
        "candidate_interface": "main.py agent(observation, configuration)",
        "source_base_identity": "source-sha256:example",
        "source_result_identity": {
            "package_sha256": package_sha256,
            "members": members,
        },
        "code_paths": [
            {"path": member["path"], "sha256": member["sha256"]}
            for member in members
        ],
        "resolved_configuration": None,
        "dependency_identity": "explicit-none",
        "runtime_factors": ["deterministic=true"],
        "generated_assets": [],
        "package_inventory": {
            "path": inventory_path.relative_to(root).as_posix(),
            "inventory_id": inventory["inventory_id"],
            "file_sha256": sha256_file(inventory_path),
        },
        "engineering_evidence": [
            {
                "path": engineering_path.relative_to(root).as_posix(),
                "file_sha256": sha256_file(engineering_path),
            }
        ],
        "recovery_artifacts": [
            {
                "role": "source",
                "path": recovery_path.relative_to(root).as_posix(),
                "file_sha256": sha256_file(recovery_path),
            }
        ],
    }
    manifest_path = root / "artifacts/frontier/B900/candidate-manifest.yaml"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False))
    return candidate_id, sha256_file(manifest_path)


def base_preflight(root: Path, candidate_id: str, manifest_sha256: str) -> dict:
    sources = {}
    for role in ("closeout", "handoff", "budget"):
        path = root / f"lineage/{role}.yaml"
        path.parent.mkdir(parents=True, exist_ok=True)
        if role == "closeout":
            source_record = {
                "event": "CLOSEOUT_COMPLETE",
                "campaign_generation": 2,
                "campaign_status": "halted",
                "unresolved_claims": [],
                "active_workers": [],
            }
        elif role == "budget":
            source_record = {
                "proposal_attempt_ceiling": 20,
                "actual_spend": 3,
                "unknown_spend": 0,
                "active_reservations": [],
            }
        else:
            source_record = {"handoff_complete": True}
        path.write_text(yaml.safe_dump(source_record, sort_keys=False))
        digest = sha256_file(path)
        sources[role] = {
            "path": path.relative_to(root).as_posix(),
            "identity_field": None,
            "identity": f"sha256:{digest}",
            "file_sha256": digest,
        }
    return {
        "recovery_preflight_path": "artifacts/frontier/recovery/G003/B900-preflight.yaml",
        "prior_campaign_generation": 2,
        "campaign_generation": 3,
        "prior_closeout": {
            "event": "CLOSEOUT_COMPLETE",
            "campaign_generation": 2,
            "campaign_status": "halted",
            "closeout_identity": sources["closeout"]["identity"],
            "final_handoff_identity": sources["handoff"]["identity"],
            "unresolved_claims": [],
            "active_workers": [],
        },
        "inherited_budget": {
            "proposal_attempt_ceiling": 20,
            "actual_spend": 3,
            "unknown_spend": 0,
            "active_reservations": [],
            "budget_identity": sources["budget"]["identity"],
        },
        "lineage_sources": sources,
        "candidate_root": "candidates/B900-example/",
        "candidate_manifest_path": "artifacts/frontier/B900/candidate-manifest.yaml",
        "requested_candidate_id": candidate_id,
        "requested_manifest_sha256": manifest_sha256,
        "source_workflow_identity": WORKFLOW_SOURCE_IDENTITY,
        "legacy_candidate_source_binding": None,
        "review_mode": "recovery-reuse",
        "candidate_mutation": "prohibited",
        "new_proposal_attempts": 0,
    }


def write_binding(root: Path, relative: str, identity_field: str | None) -> dict:
    path = root / relative
    digest = sha256_file(path)
    identity = f"sha256:{digest}"
    if identity_field is not None:
        document = yaml.safe_load(path.read_bytes())
        identity = document[identity_field]
    return {
        "path": relative,
        "identity_field": identity_field,
        "identity": identity,
        "file_sha256": digest,
    }


def write_yaml_binding(
    root: Path,
    relative: str,
    document: dict,
    *,
    identity_field: str | None = None,
) -> dict:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(document, sort_keys=False))
    return write_binding(root, relative, identity_field)


class CandidateRecoveryTests(unittest.TestCase):
    def test_exact_candidate_passes_draft_and_frozen(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            candidate_id, manifest_sha256 = create_candidate(root)
            draft = base_preflight(root, candidate_id, manifest_sha256)
            draft_result = MODULE.validate(draft, "draft", root)
            self.assertTrue(draft_result["recovery_ready"], draft_result["findings"])
            frozen = copy.deepcopy(draft)
            frozen["recovery_preflight_id"] = draft_result["computed_recovery_preflight_id"]
            frozen_result = MODULE.validate(frozen, "frozen", root)
            self.assertTrue(frozen_result["recovery_ready"], frozen_result["findings"])
            self.assertEqual(
                draft_result["computed_recovery_preflight_id"],
                frozen_result["computed_recovery_preflight_id"],
            )

    def test_requested_identity_mismatch_blocks_before_generation_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            candidate_id, manifest_sha256 = create_candidate(root)
            preflight = base_preflight(root, candidate_id.replace("example", "wrong"), manifest_sha256)
            result = MODULE.validate(preflight, "draft", root)
            self.assertFalse(result["recovery_ready"])
            self.assertIn(
                "REQUESTED_CANDIDATE_IDENTITY_MISMATCH",
                {item["code"] for item in result["findings"]},
            )
            self.assertFalse((root / "artifacts/frontier/recovery/G003").exists())

    def test_manifest_digest_mismatch_reports_requested_and_recomputed_values(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            candidate_id, manifest_sha256 = create_candidate(root)
            preflight = base_preflight(root, candidate_id, "0" * 64)
            result = MODULE.validate(preflight, "draft", root)
            finding = next(
                item
                for item in result["findings"]
                if item["code"] == "REQUESTED_MANIFEST_IDENTITY_MISMATCH"
            )
            self.assertIn("requested", finding["detail"])
            self.assertIn("recomputed", finding["detail"])
            self.assertEqual(result["recomputed_manifest_sha256"], manifest_sha256)

    def test_candidate_byte_change_ends_zero_cost_reuse(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            candidate_id, manifest_sha256 = create_candidate(root)
            (root / "candidates/B900-example/main.py").write_text("changed\n")
            result = MODULE.validate(
                base_preflight(root, candidate_id, manifest_sha256), "draft", root
            )
            codes = {item["code"] for item in result["findings"]}
            self.assertIn("REQUESTED_CANDIDATE_IDENTITY_MISMATCH", codes)
            self.assertIn("MANIFEST_CANDIDATE_IDENTITY_MISMATCH", codes)
            self.assertIn("CANDIDATE_MEMBER_MISMATCH", codes)

    def test_closeout_and_budget_must_be_reconciled(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            candidate_id, manifest_sha256 = create_candidate(root)
            preflight = base_preflight(root, candidate_id, manifest_sha256)
            preflight["prior_closeout"]["active_workers"] = ["B901-worker"]
            preflight["inherited_budget"]["active_reservations"] = ["B901"]
            result = MODULE.validate(preflight, "draft", root)
            codes = {item["code"] for item in result["findings"]}
            self.assertIn("ACTIVE_WORKERS", codes)
            self.assertIn("ACTIVE_RESERVATIONS", codes)

    def test_handoff_completion_must_derive_from_bound_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            candidate_id, manifest_sha256 = create_candidate(root)
            preflight = base_preflight(root, candidate_id, manifest_sha256)
            binding = preflight["lineage_sources"]["handoff"]
            handoff_path = root / binding["path"]
            handoff_path.write_text("handoff_complete: false\n")
            digest = sha256_file(handoff_path)
            binding["identity"] = f"sha256:{digest}"
            binding["file_sha256"] = digest
            preflight["prior_closeout"]["final_handoff_identity"] = binding["identity"]
            result = MODULE.validate(preflight, "draft", root)
            self.assertIn(
                "HANDOFF_FACTS_NOT_DERIVED",
                {item["code"] for item in result["findings"]},
            )

    def test_manifest_identity_recomputes_from_preserved_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            candidate_id, manifest_sha256 = create_candidate(root)
            result = MODULE.validate(
                base_preflight(root, candidate_id, manifest_sha256), "draft", root
            )
            self.assertTrue(result["recovery_ready"], result["findings"])
            self.assertEqual(result["recomputed_candidate_id"], candidate_id)

    def test_nonpositive_manifest_generation_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            candidate_id, manifest_sha256 = create_candidate(root)
            preflight = base_preflight(root, candidate_id, manifest_sha256)
            manifest_path = root / preflight["candidate_manifest_path"]
            manifest = yaml.safe_load(manifest_path.read_bytes())
            manifest["campaign_generation"] = 0
            manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False))
            preflight["requested_manifest_sha256"] = sha256_file(manifest_path)

            result = MODULE.validate(preflight, "draft", root)

            self.assertFalse(result["recovery_ready"])
            self.assertIn(
                "PRODUCING_GENERATION_INVALID",
                {item["code"] for item in result["findings"]},
            )

    def test_copied_lineage_identity_is_rejected_even_when_locally_consistent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            candidate_id, manifest_sha256 = create_candidate(root)
            preflight = base_preflight(root, candidate_id, manifest_sha256)
            preflight["prior_closeout"]["closeout_identity"] = "sha256:" + "0" * 64
            result = MODULE.validate(preflight, "draft", root)
            self.assertIn(
                "CLOSEOUT_LINEAGE_NOT_DERIVED",
                {item["code"] for item in result["findings"]},
            )

    def test_candidate_symlink_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            candidate_id, manifest_sha256 = create_candidate(root)
            (root / "outside.py").write_text("outside\n")
            (root / "candidates/B900-example/link.py").symlink_to(root / "outside.py")
            result = MODULE.validate(
                base_preflight(root, candidate_id, manifest_sha256), "draft", root
            )
            self.assertIn(
                "CANDIDATE_RECOVERY_UNREADABLE",
                {item["code"] for item in result["findings"]},
            )

    def test_recomputed_claims_cannot_replace_bound_closeout_and_budget_facts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            candidate_id, manifest_sha256 = create_candidate(root)
            preflight = base_preflight(root, candidate_id, manifest_sha256)
            preflight["prior_closeout"]["campaign_status"] = "stopped"
            preflight["inherited_budget"]["actual_spend"] = 4
            result = MODULE.validate(preflight, "draft", root)
            codes = {item["code"] for item in result["findings"]}
            self.assertIn("CLOSEOUT_FACTS_NOT_DERIVED", codes)
            self.assertIn("BUDGET_FACTS_NOT_DERIVED", codes)

    def test_candidate_root_symlink_is_rejected_before_resolution(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            candidate_id, manifest_sha256 = create_candidate(root)
            real = root / "candidates/B900-real"
            (root / "candidates/B900-example").rename(real)
            (root / "candidates/B900-example").symlink_to(real, target_is_directory=True)
            result = MODULE.validate(
                base_preflight(root, candidate_id, manifest_sha256), "draft", root
            )
            self.assertIn(
                "CANDIDATE_RECOVERY_UNREADABLE",
                {item["code"] for item in result["findings"]},
            )

    def test_legacy_result_needs_no_workflow_backfill_or_new_review(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate_id, digest = create_candidate(root)
            preflight = base_preflight(root, candidate_id, digest)
            manifest_path = root / preflight["candidate_manifest_path"]
            manifest = yaml.safe_load(manifest_path.read_bytes())
            for field in ("workflow_source_identity", "manifest_contract",
                          "manifest_state", "engineering_evidence", "recovery_artifacts"):
                manifest.pop(field, None)
            manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False))
            preflight["requested_manifest_sha256"] = sha256_file(manifest_path)
            preflight.pop("source_workflow_identity")
            preflight.pop("legacy_candidate_source_binding")
            before = {path.relative_to(root): path.read_bytes()
                      for path in root.rglob("*") if path.is_file()}

            result = MODULE.validate(preflight, "draft", root)

            self.assertTrue(result["recovery_ready"], result["findings"])
            self.assertIn("no readiness or permission", result["authority_effect"])
            self.assertEqual(before, {path.relative_to(root): path.read_bytes()
                                     for path in root.rglob("*") if path.is_file()})

    def test_older_candidate_uses_latest_accounting_without_generation_chain(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate_id, digest = create_candidate(root)
            preflight = base_preflight(root, candidate_id, digest)
            preflight["prior_campaign_generation"] = 8
            preflight["campaign_generation"] = 9
            closeout_path = root / preflight["lineage_sources"]["closeout"]["path"]
            closeout = yaml.safe_load(closeout_path.read_bytes())
            closeout["campaign_generation"] = 8
            preflight["lineage_sources"]["closeout"] = write_yaml_binding(
                root, "lineage/closeout.yaml", closeout
            )
            preflight["prior_closeout"]["campaign_generation"] = 8
            preflight["prior_closeout"]["closeout_identity"] = (
                preflight["lineage_sources"]["closeout"]["identity"]
            )
            # Different current parents do not rewrite the producing manifest.
            preflight["current_parents"] = {"problem_epoch": 6, "representation_revision": 4}
            before = (root / preflight["candidate_manifest_path"]).read_bytes()

            result = MODULE.validate(preflight, "draft", root)

            self.assertTrue(result["recovery_ready"], result["findings"])
            self.assertNotIn("intervening_recovery_chain", result)
            self.assertEqual(before, (root / preflight["candidate_manifest_path"]).read_bytes())
            preflight["inherited_budget"]["actual_spend"] = 0
            result = MODULE.validate(preflight, "draft", root)
            self.assertIn("BUDGET_FACTS_NOT_DERIVED", {f["code"] for f in result["findings"]})

    def test_unpublished_inventory_can_be_checked_without_final_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate_id, digest = create_candidate(root)
            preflight = base_preflight(root, candidate_id, digest)
            manifest_path = root / preflight.pop("candidate_manifest_path")
            manifest = yaml.safe_load(manifest_path.read_bytes())
            preflight.pop("requested_manifest_sha256")
            preflight["working_inventory"] = manifest["package_inventory"]
            preflight["publication_state"] = "prepublication"
            preflight["review_mode"] = "materialization"
            manifest_path.unlink()

            result = MODULE.validate(preflight, "draft", root)

            self.assertTrue(result["recovery_ready"], result["findings"])
            self.assertEqual(result["publication_state"], "prepublication")
            self.assertIsNone(result["recomputed_manifest_sha256"])
            self.assertFalse(manifest_path.exists())
            self.assertIn("no readiness or permission", result["authority_effect"])
            for field in ("inventory_id", "file_sha256"):
                with self.subTest(field=field):
                    changed = copy.deepcopy(preflight)
                    changed["working_inventory"][field] = "0" * 64
                    self.assertFalse(MODULE.validate(changed, "draft", root)["recovery_ready"])
            (root / preflight["candidate_root"] / "main.py").write_text("changed\n")
            self.assertFalse(MODULE.validate(preflight, "draft", root)["recovery_ready"])

    def test_content_check_does_not_waive_new_spend_or_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate_id, digest = create_candidate(root)
            preflight = base_preflight(root, candidate_id, digest)
            for field, value, code in (
                ("new_proposal_attempts", 1, "ZERO_COST_REUSE_INVALID"),
                ("candidate_mutation", "allowed", "CANDIDATE_MUTATION_NOT_PROHIBITED"),
            ):
                with self.subTest(field=field):
                    changed = copy.deepcopy(preflight)
                    changed[field] = value
                    result = MODULE.validate(changed, "draft", root)
                    self.assertIn(code, {f["code"] for f in result["findings"]})


if __name__ == "__main__":
    unittest.main()
