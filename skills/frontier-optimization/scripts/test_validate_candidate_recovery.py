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


def configure_legacy_source_binding(root: Path, preflight: dict) -> Path:
    manifest_path = root / preflight["candidate_manifest_path"]
    manifest = yaml.safe_load(manifest_path.read_bytes())
    manifest.pop("workflow_source_identity")
    preflight["source_workflow_identity"] = None

    candidate_root = root / preflight["candidate_root"]
    members, package_sha256 = MODULE.package_inventory(candidate_root)
    inventory = {
        "contract_version": "frontier-candidate-package-inventory/1",
        "candidate_root": preflight["candidate_root"].rstrip("/"),
        "identity_algorithm": "frontier-package-path-size-sha256/1",
        "candidate_id": preflight["requested_candidate_id"],
        "package_sha256": package_sha256,
        "members": members,
    }
    inventory_payload = yaml.safe_dump(inventory, sort_keys=False, allow_unicode=True).encode()
    inventory["inventory_id"] = "candidate-package-inventory-sha256:" + hashlib.sha256(
        inventory_payload
    ).hexdigest()
    inventory_path = root / "artifacts/frontier/B900/candidate-package-inventory.yaml"
    inventory_path.write_text(yaml.safe_dump(inventory, sort_keys=False))
    manifest["package_inventory"] = {
        "path": "artifacts/frontier/B900/candidate-package-inventory.yaml",
        "inventory_id": inventory["inventory_id"],
        "file_sha256": sha256_file(inventory_path),
    }
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False))
    preflight["requested_manifest_sha256"] = sha256_file(manifest_path)

    result_payload = {
        "result_packet_path": "artifacts/frontier/B900/result.yaml",
        "batch_id": "B900",
        "campaign_generation": 2,
        "candidate_manifest": preflight["candidate_manifest_path"],
        "candidate_identity": preflight["requested_candidate_id"],
    }
    result_digest = hashlib.sha256(
        yaml.safe_dump(result_payload, sort_keys=False, allow_unicode=True).encode()
    ).hexdigest()
    result = {
        "result_packet_id": f"B900-result-sha256:{result_digest}",
        **result_payload,
    }
    result_path = root / result["result_packet_path"]
    result_path.write_text(yaml.safe_dump(result, sort_keys=False))
    validation_payload = {
        "batch_id": "B900",
        "result_packet_path": result["result_packet_path"],
        "computed_result_packet_id": result["result_packet_id"],
        "result_structure_ready": True,
        "findings": [],
    }
    validation_digest = hashlib.sha256(
        MODULE.canonical_json(validation_payload)
    ).hexdigest()
    validation = {
        **validation_payload,
        "validation_id": f"batch-result-validation-sha256:{validation_digest}",
    }
    validation_path = root / "artifacts/frontier/B900/result-validation.json"
    validation_path.write_text(yaml.safe_dump(validation, sort_keys=False))
    review_packet_payload = {
        "review_kind": "implementation",
        "review_mode": "materialization",
        "review_id": "R900",
        "batch_id": "B900",
        "candidate_id": preflight["requested_candidate_id"],
        "campaign_generation": 2,
        "candidate_manifest": {
            "path": preflight["candidate_manifest_path"],
            "file_sha256": preflight["requested_manifest_sha256"],
        },
        "candidate_package_inventory": {
            "path": "artifacts/frontier/B900/candidate-package-inventory.yaml",
            "inventory_id": inventory["inventory_id"],
            "file_sha256": sha256_file(inventory_path),
        },
        "batch_result": {
            "path": result["result_packet_path"],
            "identity": result["result_packet_id"],
            "file_sha256": sha256_file(result_path),
        },
        "batch_result_validation": {
            "path": "artifacts/frontier/B900/result-validation.json",
            "identity": validation["validation_id"],
            "file_sha256": sha256_file(validation_path),
        },
        "assigned_review_path": "reviews/implementation-R900.md",
    }
    review_packet_digest = hashlib.sha256(
        yaml.safe_dump(
            review_packet_payload, sort_keys=False, allow_unicode=True
        ).encode()
    ).hexdigest()
    review_packet = {
        "packet_id": f"implementation-R900-packet-sha256:{review_packet_digest}",
        **review_packet_payload,
    }
    review_packet_path = root / "reviews/implementation-R900-packet.yaml"
    review_packet_path.parent.mkdir(parents=True)
    review_packet_path.write_text(yaml.safe_dump(review_packet, sort_keys=False))
    review_path = root / "reviews/implementation-R900.md"
    review_path.write_text(
        "---\n"
        "type: Optimization Frontier Implementation Review\n"
        "review_id: R900\n"
        "review_result: IMPLEMENTATION_READY\n"
        f"candidate_id: {preflight['requested_candidate_id']}\n"
        "snapshot_packet: reviews/implementation-R900-packet.yaml; "
        f"{review_packet['packet_id']}\n"
        "---\n\n# Review\n"
    )

    sidecar = {
        "contract_version": MODULE.LEGACY_SOURCE_CONTRACT,
        "candidate_id": preflight["requested_candidate_id"],
        "producing_campaign_generation": 2,
        "missing_manifest_field": "workflow_source_identity",
        "authority_effect": MODULE.LEGACY_AUTHORITY_EFFECT,
        "candidate_manifest": write_binding(
            root, preflight["candidate_manifest_path"], None
        ),
        "candidate_package_inventory": write_binding(
            root,
            "artifacts/frontier/B900/candidate-package-inventory.yaml",
            "inventory_id",
        ),
        "producing_batch_result": write_binding(
            root, result["result_packet_path"], "result_packet_id"
        ),
        "result_validation": write_binding(
            root, "artifacts/frontier/B900/result-validation.json", "validation_id"
        ),
        "implementation_review_packet": write_binding(
            root, "reviews/implementation-R900-packet.yaml", "packet_id"
        ),
        "implementation_review": write_binding(
            root, "reviews/implementation-R900.md", None
        ),
    }
    sidecar["legacy_source_binding_id"] = MODULE.computed_legacy_source_binding_id(
        sidecar
    )
    ordered = {"legacy_source_binding_id": sidecar.pop("legacy_source_binding_id"), **sidecar}
    sidecar_path = root / "artifacts/frontier/recovery/legacy/B900-source.yaml"
    sidecar_path.parent.mkdir(parents=True)
    sidecar_path.write_text(yaml.safe_dump(ordered, sort_keys=False))
    preflight["legacy_candidate_source_binding"] = write_binding(
        root,
        "artifacts/frontier/recovery/legacy/B900-source.yaml",
        "legacy_source_binding_id",
    )
    return sidecar_path


def rewrite_sidecar(root: Path, preflight: dict, sidecar: dict) -> Path:
    sidecar.pop("legacy_source_binding_id", None)
    sidecar["legacy_source_binding_id"] = MODULE.computed_legacy_source_binding_id(
        sidecar
    )
    ordered = {
        "legacy_source_binding_id": sidecar.pop("legacy_source_binding_id"),
        **sidecar,
    }
    path = root / "artifacts/frontier/recovery/legacy/B900-source.yaml"
    path.write_text(yaml.safe_dump(ordered, sort_keys=False))
    preflight["legacy_candidate_source_binding"] = write_binding(
        root, path.relative_to(root).as_posix(), "legacy_source_binding_id"
    )
    return path


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

    def test_legacy_manifest_passes_only_with_closed_content_addressed_lineage(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            candidate_id, manifest_sha256 = create_candidate(root)
            preflight = base_preflight(root, candidate_id, manifest_sha256)
            configure_legacy_source_binding(root, preflight)
            result = MODULE.validate(preflight, "draft", root)
            self.assertTrue(result["recovery_ready"], result["findings"])

    def test_legacy_manifest_without_sidecar_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            candidate_id, manifest_sha256 = create_candidate(root)
            preflight = base_preflight(root, candidate_id, manifest_sha256)
            manifest_path = root / preflight["candidate_manifest_path"]
            manifest = yaml.safe_load(manifest_path.read_bytes())
            manifest.pop("workflow_source_identity")
            manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False))
            preflight["requested_manifest_sha256"] = sha256_file(manifest_path)
            preflight["source_workflow_identity"] = None
            result = MODULE.validate(preflight, "draft", root)
            codes = {item["code"] for item in result["findings"]}
            self.assertIn("LEGACY_SOURCE_BINDING_REQUIRED", codes)
            self.assertIn("WORKFLOW_SOURCE_IDENTITY_INVALID", codes)

    def test_legacy_sidecar_tamper_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            candidate_id, manifest_sha256 = create_candidate(root)
            preflight = base_preflight(root, candidate_id, manifest_sha256)
            sidecar_path = configure_legacy_source_binding(root, preflight)
            sidecar = yaml.safe_load(sidecar_path.read_bytes())
            sidecar["candidate_id"] = "B900-wrong-sha256:" + "0" * 64
            sidecar_path.write_text(yaml.safe_dump(sidecar, sort_keys=False))
            digest = sha256_file(sidecar_path)
            preflight["legacy_candidate_source_binding"]["file_sha256"] = digest
            result = MODULE.validate(preflight, "draft", root)
            codes = {item["code"] for item in result["findings"]}
            self.assertIn("LEGACY_SOURCE_BINDING_IDENTITY_MISMATCH", codes)

    def test_legacy_result_cross_binding_mismatch_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            candidate_id, manifest_sha256 = create_candidate(root)
            preflight = base_preflight(root, candidate_id, manifest_sha256)
            sidecar_path = configure_legacy_source_binding(root, preflight)
            result_path = root / "artifacts/frontier/B900/result.yaml"
            result_document = yaml.safe_load(result_path.read_bytes())
            result_document["candidate_identity"] = "B900-wrong-sha256:" + "0" * 64
            result_path.write_text(yaml.safe_dump(result_document, sort_keys=False))
            result_digest = sha256_file(result_path)
            sidecar = yaml.safe_load(sidecar_path.read_bytes())
            sidecar["producing_batch_result"]["file_sha256"] = result_digest
            sidecar.pop("legacy_source_binding_id")
            sidecar["legacy_source_binding_id"] = MODULE.computed_legacy_source_binding_id(
                sidecar
            )
            sidecar = {
                "legacy_source_binding_id": sidecar.pop("legacy_source_binding_id"),
                **sidecar,
            }
            sidecar_path.write_text(yaml.safe_dump(sidecar, sort_keys=False))
            preflight["legacy_candidate_source_binding"] = write_binding(
                root,
                "artifacts/frontier/recovery/legacy/B900-source.yaml",
                "legacy_source_binding_id",
            )
            result = MODULE.validate(preflight, "draft", root)
            codes = {item["code"] for item in result["findings"]}
            self.assertIn("LEGACY_SOURCE_RESULT_MISMATCH", codes)

    def test_legacy_generation_cross_link_mismatch_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            candidate_id, manifest_sha256 = create_candidate(root)
            preflight = base_preflight(root, candidate_id, manifest_sha256)
            sidecar_path = configure_legacy_source_binding(root, preflight)
            sidecar = yaml.safe_load(sidecar_path.read_bytes())
            sidecar["producing_campaign_generation"] = 3
            rewrite_sidecar(root, preflight, sidecar)
            result = MODULE.validate(preflight, "draft", root)
            self.assertIn(
                "LEGACY_SOURCE_GENERATION_MISMATCH",
                {item["code"] for item in result["findings"]},
            )

    def test_legacy_manifest_inventory_cross_link_mismatch_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            candidate_id, manifest_sha256 = create_candidate(root)
            preflight = base_preflight(root, candidate_id, manifest_sha256)
            sidecar_path = configure_legacy_source_binding(root, preflight)
            copied_inventory = root / "artifacts/frontier/B900/copied-inventory.yaml"
            copied_inventory.write_bytes(
                (root / "artifacts/frontier/B900/candidate-package-inventory.yaml").read_bytes()
            )
            sidecar = yaml.safe_load(sidecar_path.read_bytes())
            sidecar["candidate_package_inventory"] = write_binding(
                root,
                "artifacts/frontier/B900/copied-inventory.yaml",
                "inventory_id",
            )
            rewrite_sidecar(root, preflight, sidecar)
            result = MODULE.validate(preflight, "draft", root)
            self.assertIn(
                "LEGACY_SOURCE_MANIFEST_INVENTORY_MISMATCH",
                {item["code"] for item in result["findings"]},
            )

    def test_legacy_review_must_name_exact_packet(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            candidate_id, manifest_sha256 = create_candidate(root)
            preflight = base_preflight(root, candidate_id, manifest_sha256)
            sidecar_path = configure_legacy_source_binding(root, preflight)
            review_path = root / "reviews/implementation-R900.md"
            review_path.write_text(review_path.read_text().replace(
                "snapshot_packet: reviews/implementation-R900-packet.yaml; ",
                "snapshot_packet: reviews/other-packet.yaml; ",
            ))
            sidecar = yaml.safe_load(sidecar_path.read_bytes())
            sidecar["implementation_review"] = write_binding(
                root, "reviews/implementation-R900.md", None
            )
            rewrite_sidecar(root, preflight, sidecar)
            result = MODULE.validate(preflight, "draft", root)
            self.assertIn(
                "LEGACY_SOURCE_REVIEW_MISMATCH",
                {item["code"] for item in result["findings"]},
            )

    def test_legacy_review_rejects_substring_packet_binding(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            candidate_id, manifest_sha256 = create_candidate(root)
            preflight = base_preflight(root, candidate_id, manifest_sha256)
            sidecar_path = configure_legacy_source_binding(root, preflight)
            review_path = root / "reviews/implementation-R900.md"
            review_path.write_text(
                review_path.read_text().replace(
                    "snapshot_packet: reviews/implementation-R900-packet.yaml; "
                    "implementation-R900-packet-sha256:",
                    "snapshot_packet: prefixreviews/implementation-R900-packet.yaml-suffix; "
                    "prefiximplementation-R900-packet-sha256:",
                ).replace(
                    "\ncandidate_id:",
                    "suffix\ncandidate_id:",
                    1,
                )
            )
            sidecar = yaml.safe_load(sidecar_path.read_bytes())
            sidecar["implementation_review"] = write_binding(
                root, "reviews/implementation-R900.md", None
            )
            rewrite_sidecar(root, preflight, sidecar)
            result = MODULE.validate(preflight, "draft", root)
            self.assertIn(
                "LEGACY_SOURCE_REVIEW_MISMATCH",
                {item["code"] for item in result["findings"]},
            )

    def test_nonpositive_historical_review_remains_provenance_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            candidate_id, manifest_sha256 = create_candidate(root)
            preflight = base_preflight(root, candidate_id, manifest_sha256)
            sidecar_path = configure_legacy_source_binding(root, preflight)
            review_path = root / "reviews/implementation-R900.md"
            review_path.write_text(review_path.read_text().replace(
                "review_result: IMPLEMENTATION_READY",
                "review_result: IMPLEMENTATION_REPAIR_REQUIRED",
            ))
            sidecar = yaml.safe_load(sidecar_path.read_bytes())
            sidecar["implementation_review"] = write_binding(
                root, "reviews/implementation-R900.md", None
            )
            rewrite_sidecar(root, preflight, sidecar)
            result = MODULE.validate(preflight, "draft", root)
            self.assertTrue(result["recovery_ready"], result["findings"])


if __name__ == "__main__":
    unittest.main()
