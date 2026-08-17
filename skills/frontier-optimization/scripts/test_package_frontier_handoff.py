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

from test_validate_entry_packet import write_workflow_source_binding


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
    workflow = root / "artifacts/frontier/workflow/R900"
    task.mkdir(parents=True)
    evidence.mkdir(parents=True)
    (task / "FRONTIER.md").write_text(
        yaml.safe_dump(
            {
                "event": "CLOSEOUT_COMPLETE",
                "campaign_generation": 2,
                "campaign_status": "halted",
                "unresolved_claims": [],
                "active_workers": [],
            },
            sort_keys=False,
        )
    )
    (task / "log.md").write_text("handoff_complete: true\n")
    (evidence / "result.yaml").write_text(
        yaml.safe_dump(
            {
                "proposal_attempt_ceiling": 20,
                "actual_spend": 3,
                "unknown_spend": 0,
                "active_reservations": [],
            },
            sort_keys=False,
        )
    )
    workflow_source_binding = write_workflow_source_binding(root)
    workflow_source_binding["governs"] = [
        "Selection-final",
        "B900",
        "Outcome Reflection-final",
    ]
    lineage_paths = {
        "closeout": task / "FRONTIER.md",
        "handoff": task / "log.md",
        "budget": evidence / "result.yaml",
    }
    lineage_sources = {
        role: {
            "path": path.relative_to(root).as_posix(),
            "identity_field": None,
            "identity": file_identity(path),
            "file_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
        for role, path in lineage_paths.items()
    }
    return {
        "package_plan_path": "artifacts/frontier/packages/G002/plan.yaml",
        "campaign_generation": 2,
        "campaign_status": "halted",
        "closeout_identity": lineage_sources["closeout"]["identity"],
        "final_handoff_identity": lineage_sources["handoff"]["identity"],
        "final_budget_identity": lineage_sources["budget"]["identity"],
        "lineage_sources": lineage_sources,
        "final_direction_state": {
            "compatible_evidence": ["E900"],
            "controlling_reflections": ["OR900"],
            "progress_meaning": "bounded diminishing returns under tested conditions",
            "constraint_meaning": "the tested route remains locally constrained",
            "route_set_state": "decision-complete; no reopening event observed",
            "reopening_events": [],
            "diagnostic_dominance": "no diagnostic selected at closeout",
            "resolver": {
                "evidence_state_identity": "sha256:final-evidence-state",
                "row": 11,
                "direction_resolution": "stop",
                "exact_action": "full-closeout",
            },
            "budget_reachability": "no permitted work reaches another meaningful check",
            "workflow_source_identity": workflow_source_binding["source_snapshot"]["identity"],
        },
        "workflow_source_bindings": [workflow_source_binding],
        "subtree_identity_algorithm": MODULE.PACKAGE_PATH_SIZE_SHA256_V1,
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
            {
                "source": "artifacts/frontier/workflow/R900/source-manifest.yaml",
                "scope": "file",
                "identity": file_identity(workflow / "source-manifest.yaml"),
                "destination": "workflow/R900/source-manifest.yaml",
                "role": "workflow-source-manifest",
            },
            {
                "source": "artifacts/frontier/workflow/R900/source-snapshot.yaml",
                "scope": "file",
                "identity": file_identity(workflow / "source-snapshot.yaml"),
                "destination": "workflow/R900/source-snapshot.yaml",
                "role": "workflow-source-snapshot",
            },
        ],
    }


class HandoffPackageTests(unittest.TestCase):
    def test_legacy_plan_is_audit_only_and_build_is_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            plan_document = create_sources(root)
            audit = MODULE.validate_plan(plan_document, "audit", root)
            self.assertTrue(audit["package_ready"], audit["findings"])
            draft = MODULE.validate_plan(plan_document, "draft", root)
            self.assertFalse(draft["package_ready"])
            self.assertIn(
                "LEGACY_PACKAGER_READ_ONLY",
                {item["code"] for item in draft["findings"]},
            )
            frozen = copy.deepcopy(plan_document)
            frozen["package_id"] = audit["computed_package_id"]
            plan = root / "plan.yaml"
            plan.write_text(yaml.safe_dump(frozen, sort_keys=False))
            with self.assertRaisesRegex(MODULE.PackageError, "build is closed"):
                MODULE.build(plan, root / "packages", root)
            self.assertFalse((root / "packages").exists())

    def test_legacy_audit_detects_source_change_without_publishing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            plan = create_sources(root)
            self.assertTrue(MODULE.validate_plan(plan, "audit", root)["package_ready"])
            (root / "docs/task/FRONTIER.md").write_text("changed\n")
            result = MODULE.validate_plan(plan, "audit", root)
            self.assertFalse(result["package_ready"])
            self.assertFalse((root / "packages").exists())
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

    def test_closed_build_api_never_reuses_or_creates_a_destination(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            plan = root / "plan.yaml"
            plan.write_text("{}\n")
            output_parent = root / "packages"
            with self.assertRaisesRegex(MODULE.PackageError, "build is closed"):
                MODULE.build(plan, output_parent, root)
            self.assertFalse(output_parent.exists())
    def test_budget_source_requires_numeric_nonnegative_spend_within_ceiling(self) -> None:
        invalid_records = (
            {
                "proposal_attempt_ceiling": 1,
                "actual_spend": 999,
                "unknown_spend": 0,
                "active_reservations": [],
            },
            {
                "proposal_attempt_ceiling": 20,
                "actual_spend": "3",
                "unknown_spend": 0,
                "active_reservations": [],
            },
            {
                "proposal_attempt_ceiling": 20,
                "actual_spend": -1,
                "unknown_spend": 0,
                "active_reservations": [],
            },
        )
        for invalid_record in invalid_records:
            with self.subTest(invalid_record=invalid_record), tempfile.TemporaryDirectory() as directory:
                root = Path(directory).resolve()
                draft = create_sources(root)
                budget_path = root / draft["lineage_sources"]["budget"]["path"]
                budget_path.write_text(yaml.safe_dump(invalid_record, sort_keys=False))
                budget_identity = file_identity(budget_path)
                draft["lineage_sources"]["budget"].update(
                    {
                        "identity": budget_identity,
                        "file_sha256": budget_identity.removeprefix("sha256:"),
                    }
                )
                draft["final_budget_identity"] = budget_identity
                draft["entries"][2]["identity"] = MODULE.subtree_inventory(
                    root / "artifacts/frontier/B900"
                )[1]
                result = MODULE.validate_plan(draft, "draft", root)
                self.assertIn(
                    "BUDGET_FACTS_NOT_DERIVED",
                    {item["code"] for item in result["findings"]},
                )

    def test_legacy_verify_rejects_an_unrecognized_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            with self.assertRaisesRegex(MODULE.PackageError, "missing manifest"):
                MODULE.verify(root)
    def test_symlinked_source_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            draft = create_sources(root)
            outside = root / "outside.txt"
            outside.write_text("outside\n")
            link = root / "artifacts/frontier/B900/link.txt"
            link.symlink_to(outside)
            draft["entries"][2]["identity"] = file_identity(outside)
            result = MODULE.validate_plan(draft, "draft", root)
            self.assertIn(
                "PACKAGE_ENTRY_INVALID",
                {item["code"] for item in result["findings"]},
            )

    def test_package_root_symlink_is_rejected_before_resolution(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            draft = create_sources(root)
            real = root / "artifacts/frontier/B900-real"
            (root / "artifacts/frontier/B900").rename(real)
            (root / "artifacts/frontier/B900").symlink_to(real, target_is_directory=True)
            result = MODULE.validate_plan(draft, "draft", root)
            self.assertIn(
                "PACKAGE_ENTRY_INVALID",
                {item["code"] for item in result["findings"]},
            )

    def test_package_requires_final_direction_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            draft = create_sources(root)
            draft.pop("final_direction_state")

            result = MODULE.validate_plan(draft, "draft", root)

            codes = {item["code"] for item in result["findings"]}
            self.assertIn("REQUIRED_FIELD_MISSING", codes)
            self.assertIn("FINAL_DIRECTION_STATE_INVALID", codes)

    def test_every_workflow_source_byte_must_be_packaged(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            draft = create_sources(root)
            draft["entries"] = [
                entry
                for entry in draft["entries"]
                if entry["role"] != "workflow-source-snapshot"
            ]

            result = MODULE.validate_plan(draft, "draft", root)

            self.assertIn(
                "WORKFLOW_SOURCE_NOT_PACKAGED",
                {item["code"] for item in result["findings"]},
            )


if __name__ == "__main__":
    unittest.main()
