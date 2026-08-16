#!/usr/bin/env python3
"""Regression tests for Frontier execution-baseline freezing."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

import yaml

from test_validate_authorization_adoption import make_record
from test_validate_entry_packet import PROJECT_SNAPSHOT, make_workspace


SCRIPT = Path(__file__).with_name("freeze_execution_baseline.py")
SPEC = importlib.util.spec_from_file_location("freeze_execution_baseline", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def file_identity(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def file_binding(path: Path, root: Path, identity_field: str, identity: str) -> dict:
    return {
        "path": path.relative_to(root).as_posix(),
        "identity_field": identity_field,
        "identity": identity,
        "file_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def write_bound_dispatch_draft(root: Path) -> tuple[Path, Path, dict]:
    adoption = make_record(root)
    adoption_draft = MODULE.load_validator(
        "validate_authorization_adoption.py", "_adoption_for_baseline_test"
    ).validate(adoption, "draft", root)
    adoption["adoption_id"] = adoption_draft["computed_adoption_id"]
    adoption_path = root / adoption["adoption_path"]
    adoption_path.parent.mkdir(parents=True, exist_ok=True)
    adoption_path.write_text(yaml.safe_dump(adoption, sort_keys=False))
    adoption_validation = MODULE.load_validator(
        "validate_authorization_adoption.py", "_adoption_validation_for_baseline_test"
    ).validate(adoption, "frozen", root)
    validation_path = adoption_path.with_name("entry-R900-adoption-validation.json")
    validation_path.write_bytes(MODULE.canonical_json_artifact(adoption_validation))

    packet_path = root / "artifacts/frontier/B900/packet.yaml"
    packet = yaml.safe_load(packet_path.read_text())
    preflight_path = root / packet["packet_preflight_path"]
    preflight = json.loads(preflight_path.read_text())
    acknowledgment = {
        "batch_id": "B900",
        "packet_id": packet["packet_id"],
        "packet_preflight_id": preflight["preflight_id"],
        "authority_id": adoption["adoption_id"],
        "authority_validation_id": adoption_validation["validation_id"],
        "acknowledgment": "accepted",
    }
    acknowledgment["acknowledgment_id"] = MODULE.compute_acknowledgment_id(acknowledgment)
    acknowledgment_path = root / packet["acknowledgment_path"]
    acknowledgment_path.parent.mkdir(parents=True, exist_ok=True)
    acknowledgment_path.write_text(yaml.safe_dump(acknowledgment, sort_keys=False))

    target_path = root / adoption["authorization_target"]["path"]
    target = yaml.safe_load(target_path.read_text())
    transitioned_baseline = []
    receipt_files = []
    for item in target["post_adoption_state"]["files"]:
        live_path = root / item["path"]
        post_path = root / item["post_source"]["path"]
        live_path.write_bytes(post_path.read_bytes())
        post_sha256 = hashlib.sha256(live_path.read_bytes()).hexdigest()
        receipt_files.append(
            {
                "path": item["path"],
                "pre_sha256": item["pre_sha256"],
                "post_sha256": post_sha256,
            }
        )
        transitioned_baseline.append(
            {
                "path": item["path"],
                "scope": "file",
                "identity": f"sha256:{post_sha256}",
            }
        )

    source = root / "src/config.yaml"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("value: 1\n")
    draft = {
        "execution_start_path": packet["execution_start_path"],
        "packet_path": packet["packet_path"],
        "packet_id": packet["packet_id"],
        "packet_preflight": file_binding(
            preflight_path, root, "preflight_id", preflight["preflight_id"]
        ),
        "execution_authority": {
            "mode": "authorization-adoption",
            "record": file_binding(
                adoption_path, root, "adoption_id", adoption["adoption_id"]
            ),
            "validation": file_binding(
                validation_path,
                root,
                "validation_id",
                adoption_validation["validation_id"],
            ),
        },
        "acknowledgment": file_binding(
            acknowledgment_path,
            root,
            "acknowledgment_id",
            acknowledgment["acknowledgment_id"],
        ),
        "batch_id": "B900",
        "campaign_generation": 1,
        "recorded_by": "frontier-optimization/1",
        "recorded_at": "2026-08-15T08:00:00Z",
        "lifecycle_transition": None,
        "post_adoption_state": {
            "contract_version": "frontier-post-adoption-state/1",
            "target_id": adoption["authorization_target"]["target_id"],
            "adoption_id": adoption["adoption_id"],
            "user_result_id": adoption["user_result"]["identity"],
            "files": receipt_files,
        },
        "post_transition_baseline": [
            {"path": "src/config.yaml", "scope": "file", "identity": file_identity(source)},
            *transitioned_baseline,
        ],
        "worker_may_start": "yes",
        "blocker": None,
    }
    draft_path = root / "dispatch-draft.yaml"
    draft_path.write_text(yaml.safe_dump(draft, sort_keys=False))
    return draft_path, source, draft


def freeze_baseline(*args, **kwargs):
    """Exercise baseline mechanics without claiming dispatch authority."""
    repo_root = Path(args[3] if len(args) > 3 else kwargs["repo_root"])
    if not (repo_root / ".git").exists():
        subprocess.run(["git", "init", "-q", str(repo_root)], check=True)
    with mock.patch.object(MODULE, "validate_dispatch_chain", return_value=None):
        return MODULE.freeze(*args, **kwargs)


def verify_baseline(*args, **kwargs):
    """Exercise snapshot verification without treating a legacy chain as authority."""
    with mock.patch.object(MODULE, "validate_dispatch_chain", return_value=None):
        return MODULE.verify(*args, **kwargs)


def write_draft(root: Path, baseline: list[dict]) -> Path:
    if not (root / ".git").exists():
        subprocess.run(["git", "init", "-q", str(root)], check=True)
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
    packet_path = root / draft["packet_path"]
    packet_path.parent.mkdir(parents=True, exist_ok=True)
    packet_path.write_text(
        yaml.safe_dump(
            {
                "packet_id": draft["packet_id"],
                "coordinator_lifecycle_transition": None,
            },
            sort_keys=False,
        )
    )
    path = root / "draft.yaml"
    path.write_text(yaml.safe_dump(draft, sort_keys=False))
    return path


def write_lifecycle_draft(
    root: Path,
    *,
    transition_timestamp: str = "2026-08-14T00:01:52Z",
    derived_updated: str = "2026-08-14",
) -> tuple[Path, Path]:
    frontier = root / "docs/task/FRONTIER.md"
    frontier.parent.mkdir(parents=True)
    frontier.write_text(
        "---\n"
        "campaign_status: running\n"
        f"updated: '{derived_updated}'\n"
        f"generated: {{by: frontier-optimization/1, at: '{transition_timestamp}'}}\n"
        "---\n\n# FRONTIER\n"
    )
    pre_identity = f"sha256:{'1' * 64}"
    post_identity = file_identity(frontier)
    packet = {
        "packet_id": "B900-packet-sha256:example",
        "coordinator_lifecycle_transition": {
            "contract_version": "frontier-lifecycle-transition/1",
            "path": "docs/task/FRONTIER.md",
            "prerequisite": "accepted B900 acknowledgment",
            "deadline": "before execution baseline and execution-start",
            "precondition": {
                "campaign_status": "planned",
                "file_identity": pre_identity,
            },
            "transition_time": {
                "capture": "once_after_accepted_acknowledgment",
                "format": "RFC3339",
                "timezone": "UTC",
            },
            "allowed_field_diff": {
                "campaign_status": {"from": "planned", "to": "running"},
                "generated.at": {"derive": "transition_time"},
                "updated": {
                    "derive": "calendar_date",
                    "source": "transition_time",
                    "timezone": "UTC",
                },
            },
            "all_other_bytes": "unchanged",
            "on_failure": "block_before_work_and_spend",
        }
    }
    packet_path = root / "artifacts/frontier/B900/packet.yaml"
    packet_path.parent.mkdir(parents=True)
    packet_path.write_text(yaml.safe_dump(packet, sort_keys=False))
    draft = {
        "execution_start_path": "artifacts/frontier/B900/execution-start.yaml",
        "packet_path": "artifacts/frontier/B900/packet.yaml",
        "packet_id": "B900-packet-sha256:example",
        "batch_id": "B900",
        "campaign_generation": 2,
        "recorded_by": "frontier-optimization/1",
        "recorded_at": transition_timestamp,
        "lifecycle_transition": {
            "contract_version": "frontier-lifecycle-transition/1",
            "path": "docs/task/FRONTIER.md",
            "transition_timestamp": transition_timestamp,
            "timezone": "UTC",
            "derived_updated": derived_updated,
            "pre_change_identity": pre_identity,
            "post_change_identity": post_identity,
            "observed_field_diff": {
                "campaign_status": {"from": "planned", "to": "running"},
                "generated.at": {"from": "2026-08-13T23:55:00Z", "to": transition_timestamp},
                "updated": {"from": "2026-08-13", "to": derived_updated},
            },
        },
        "post_transition_baseline": [
            {
                "path": "docs/task/FRONTIER.md",
                "scope": "file",
                "identity": post_identity,
            }
        ],
        "unchanged_authority_check": "matched",
        "worker_may_start": "yes",
        "blocker": None,
    }
    draft_path = root / "start-draft.yaml"
    draft_path.write_text(yaml.safe_dump(draft, sort_keys=False))
    return draft_path, frontier


class ExecutionBaselineTests(unittest.TestCase):
    def test_partial_post_adoption_transition_blocks_execution_start(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            draft, _, document = write_bound_dispatch_draft(root)
            frontier = root / "docs/skills/optimization/example/FRONTIER.md"
            frontier.write_text("FRONTIER.md: before\n")
            output = root / "artifacts/frontier/B900/execution-start.yaml"
            with self.assertRaisesRegex(MODULE.BaselineError, "reviewed post-state"):
                MODULE.freeze(
                    draft,
                    "artifacts/frontier/B900/execution-baseline/",
                    output,
                    root.resolve(),
                )

    def test_extra_unreviewed_drift_blocks_execution_start(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            draft, _, _ = write_bound_dispatch_draft(root)
            post_source = root / "artifacts/frontier/B900/proposed-log.md"
            post_source.write_text("changed after review\n")
            output = root / "artifacts/frontier/B900/execution-start.yaml"
            with self.assertRaisesRegex(MODULE.BaselineError, "unchanged snapshot"):
                MODULE.freeze(
                    draft,
                    "artifacts/frontier/B900/execution-baseline/",
                    output,
                    root.resolve(),
                )

    def test_self_declared_post_adoption_receipt_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            draft, _, document = write_bound_dispatch_draft(root)
            document["post_adoption_state"]["files"][0]["post_sha256"] = "0" * 64
            draft.write_text(yaml.safe_dump(document, sort_keys=False))
            output = root / "artifacts/frontier/B900/execution-start.yaml"
            with self.assertRaisesRegex(MODULE.BaselineError, "transition receipt"):
                MODULE.freeze(
                    draft,
                    "artifacts/frontier/B900/execution-baseline/",
                    output,
                    root.resolve(),
                )

    def test_reviewed_post_adoption_path_must_be_in_execution_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            draft, _, document = write_bound_dispatch_draft(root)
            omitted = document["post_adoption_state"]["files"][0]["path"]
            document["post_transition_baseline"] = [
                item
                for item in document["post_transition_baseline"]
                if item["path"] != omitted
            ]
            draft.write_text(yaml.safe_dump(document, sort_keys=False))
            output = root / "artifacts/frontier/B900/execution-start.yaml"
            with self.assertRaisesRegex(MODULE.BaselineError, "must appear once"):
                MODULE.freeze(
                    draft,
                    "artifacts/frontier/B900/execution-baseline/",
                    output,
                    root.resolve(),
                )

    def test_legacy_packet_cannot_mint_a_new_execution_start(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "src/config.yaml"
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_text("value: 1\n")
            draft = write_draft(
                root,
                [
                    {
                        "path": "src/config.yaml",
                        "scope": "file",
                        "identity": file_identity(source),
                    }
                ],
            )
            output = root / "artifacts/frontier/B900/execution-start.yaml"
            with self.assertRaisesRegex(MODULE.BaselineError, "legacy packet"):
                MODULE.freeze(
                    draft,
                    "artifacts/frontier/B900/execution-baseline/",
                    output,
                    root.resolve(),
                )

    def test_legacy_execution_start_cannot_pass_live_verification(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "src/config.yaml"
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_text("value: 1\n")
            draft = write_draft(
                root,
                [{"path": "src/config.yaml", "scope": "file", "identity": file_identity(source)}],
            )
            output = root / "artifacts/frontier/B900/execution-start.yaml"
            freeze_baseline(
                draft,
                "artifacts/frontier/B900/execution-baseline/",
                output,
                root.resolve(),
            )
            self.assertTrue(MODULE.verify(output, root.resolve(), False)["snapshot_verified"])
            with self.assertRaisesRegex(MODULE.BaselineError, "legacy packet"):
                MODULE.verify(output, root.resolve(), True)

    def test_spend_readiness_chain_is_recomputed_without_user_adoption(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            entry = make_workspace(root, frozen=True)
            packet_path = root / "artifacts/frontier/B900/packet.yaml"
            packet = yaml.safe_load(packet_path.read_text())
            packet.pop("packet_id")
            packet.update(
                {
                    "work_kind": "research",
                    "changes_executable_candidate": False,
                    "development_authorization_target": None,
                    "candidate_root_path": None,
                    "candidate_manifest_path": None,
                }
            )
            packet_validator = MODULE.load_validator(
                "validate_batch_packet.py", "_packet_for_spend_readiness_test"
            )
            packet_draft = packet_validator.validate(packet, "draft", root)
            self.assertTrue(packet_draft["packet_structure_ready"], packet_draft["findings"])
            packet["packet_id"] = packet_draft["computed_packet_id"]
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False))
            preflight_path = root / packet["packet_preflight_path"]
            preflight_path.write_bytes(MODULE.canonical_json_artifact(packet_draft))

            manifest_path = root / entry["snapshot_manifest"]["path"]
            manifest = yaml.safe_load(manifest_path.read_text())
            replacement_manifest_path = root / "frontier/reviews/entry-R901-project-snapshot.yaml"
            replacement_manifest = PROJECT_SNAPSHOT.capture(
                root,
                manifest_path=replacement_manifest_path,
                paths=[item["path"] for item in manifest["members"]],
                created_at="2026-08-16T00:00:01Z",
            )
            entry.update(
                {
                    "snapshot_id": replacement_manifest["snapshot_id"],
                    "snapshot_manifest": {
                        "path": replacement_manifest_path.relative_to(root).as_posix(),
                        "snapshot_id": replacement_manifest["snapshot_id"],
                        "file_sha256": hashlib.sha256(replacement_manifest_path.read_bytes()).hexdigest(),
                    },
                }
            )
            boundary = packet["authorization_boundary"]
            entry.update(
                {
                    "review_stage": "spend-readiness",
                    "authorization_target": None,
                    "authorization_state": "not-required",
                    "dispatch_contract": {
                        "batch_id": packet["batch_id"],
                        "packet_path": packet["packet_path"],
                        "packet_id": packet["packet_id"],
                        "preflight_path": packet["packet_preflight_path"],
                        "preflight_id": packet_draft["preflight_id"],
                        "preflight_file_sha256": hashlib.sha256(
                            preflight_path.read_bytes()
                        ).hexdigest(),
                        "design_contract_identity": packet[
                            "design_contract_identity"
                        ],
                        "source_base_identity": packet["source_base_identity"],
                        "scope": boundary["scope"],
                        "maximum_spend": boundary["maximum_spend"],
                        "stop_boundary": boundary["stop_boundary"],
                        "result_path": boundary["result_path"],
                    },
                }
            )
            entry.pop("packet_id")
            entry_validator = MODULE.load_validator(
                "validate_entry_packet.py", "_entry_for_spend_readiness_test"
            )
            entry_draft = entry_validator.validate(entry, "draft", root)
            self.assertTrue(entry_draft["entry_schema_ready"], entry_draft["findings"])
            entry["packet_id"] = entry_draft["computed_packet_id"]
            entry_path = root / entry["packet_path"]
            entry_path.parent.mkdir(parents=True, exist_ok=True)
            entry_path.write_text(yaml.safe_dump(entry, sort_keys=False))
            entry_validation = entry_validator.validate(entry, "frozen", root)
            validation_path = root / "frontier/reviews/entry-R900-spend-validation.json"
            validation_path.write_bytes(MODULE.canonical_json_artifact(entry_validation))
            review_path = root / entry["assigned_review_path"]
            review_path.parent.mkdir(parents=True, exist_ok=True)
            review_path.write_text(
                "---\n"
                "review_id: R900\n"
                "review_result: ENTRY_READY\n"
                f"packet_id: {entry['packet_id']}\n"
                f"snapshot_id: {entry['snapshot_id']}\n"
                "---\n\n# Review\n"
            )

            preflight = __import__("json").loads(preflight_path.read_text())
            authority_id = file_identity(review_path)
            acknowledgment = {
                "batch_id": "B900",
                "packet_id": packet["packet_id"],
                "packet_preflight_id": preflight["preflight_id"],
                "authority_id": authority_id,
                "authority_validation_id": entry_validation["entry_schema_id"],
                "acknowledgment": "accepted",
            }
            acknowledgment["acknowledgment_id"] = MODULE.compute_acknowledgment_id(
                acknowledgment
            )
            acknowledgment_path = root / packet["acknowledgment_path"]
            acknowledgment_path.write_text(yaml.safe_dump(acknowledgment, sort_keys=False))
            source = root / "src/spend-ready.yaml"
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_text("ready: true\n")
            draft = {
                "execution_start_path": packet["execution_start_path"],
                "packet_path": packet["packet_path"],
                "packet_id": packet["packet_id"],
                "packet_preflight": file_binding(
                    preflight_path, root, "preflight_id", preflight["preflight_id"]
                ),
                "execution_authority": {
                    "mode": "spend-readiness",
                    "entry_packet": file_binding(
                        entry_path, root, "packet_id", entry["packet_id"]
                    ),
                    "record": {
                        "path": review_path.relative_to(root).as_posix(),
                        "identity_field": None,
                        "identity": authority_id,
                        "file_sha256": hashlib.sha256(review_path.read_bytes()).hexdigest(),
                    },
                    "validation": file_binding(
                        validation_path,
                        root,
                        "entry_schema_id",
                        entry_validation["entry_schema_id"],
                    ),
                },
                "acknowledgment": file_binding(
                    acknowledgment_path,
                    root,
                    "acknowledgment_id",
                    acknowledgment["acknowledgment_id"],
                ),
                "batch_id": "B900",
                "campaign_generation": 1,
                "recorded_by": "frontier-optimization/1",
                "recorded_at": "2026-08-15T08:00:00Z",
                "lifecycle_transition": None,
                "post_transition_baseline": [
                    {
                        "path": "src/spend-ready.yaml",
                        "scope": "file",
                        "identity": file_identity(source),
                    }
                ],
                "worker_may_start": "yes",
                "blocker": None,
            }
            draft_path = root / "spend-readiness-draft.yaml"
            draft_path.write_text(yaml.safe_dump(draft, sort_keys=False))
            output = root / packet["execution_start_path"]
            frozen = MODULE.freeze(
                draft_path,
                packet["execution_baseline_root"],
                output,
                root.resolve(),
            )
            self.assertTrue(frozen["execution_start_id"])

    def test_new_dispatch_chain_is_recomputed_before_freeze(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            draft, _, _ = write_bound_dispatch_draft(root)
            output = root / "artifacts/frontier/B900/execution-start.yaml"
            frozen = MODULE.freeze(
                draft,
                "artifacts/frontier/B900/execution-baseline/",
                output,
                root.resolve(),
            )
            self.assertTrue(frozen["execution_start_id"])
            self.assertTrue(MODULE.verify(output, root.resolve(), True)["snapshot_verified"])

    def test_new_dispatch_chain_rejects_stale_acknowledgment(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            draft, _, document = write_bound_dispatch_draft(root)
            acknowledgment_path = root / document["acknowledgment"]["path"]
            acknowledgment = yaml.safe_load(acknowledgment_path.read_text())
            acknowledgment["packet_id"] = "B899-packet-sha256:stale"
            acknowledgment["acknowledgment_id"] = MODULE.compute_acknowledgment_id(
                acknowledgment
            )
            acknowledgment_path.write_text(yaml.safe_dump(acknowledgment, sort_keys=False))
            raw = acknowledgment_path.read_bytes()
            document["acknowledgment"].update(
                {
                    "identity": acknowledgment["acknowledgment_id"],
                    "file_sha256": hashlib.sha256(raw).hexdigest(),
                }
            )
            draft.write_text(yaml.safe_dump(document, sort_keys=False))
            output = root / "artifacts/frontier/B900/execution-start.yaml"
            with self.assertRaisesRegex(MODULE.BaselineError, "does not bind"):
                MODULE.freeze(
                    draft,
                    "artifacts/frontier/B900/execution-baseline/",
                    output,
                    root.resolve(),
                )
    def test_structured_lifecycle_crosses_utc_midnight(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            draft, _ = write_lifecycle_draft(root)
            output = root / "artifacts/frontier/B900/execution-start.yaml"
            frozen = freeze_baseline(
                draft,
                "artifacts/frontier/B900/execution-baseline/",
                output,
                root.resolve(),
            )
            self.assertEqual(
                frozen["lifecycle_transition"]["derived_updated"], "2026-08-14"
            )
            self.assertTrue(verify_baseline(output, root.resolve(), True)["snapshot_verified"])

    def test_structured_lifecycle_rejects_wrong_derived_date(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            draft, _ = write_lifecycle_draft(root, derived_updated="2026-08-13")
            output = root / "artifacts/frontier/B900/execution-start.yaml"
            with self.assertRaisesRegex(MODULE.BaselineError, "derived_updated"):
                freeze_baseline(
                    draft,
                    "artifacts/frontier/B900/execution-baseline/",
                    output,
                    root.resolve(),
                )
            self.assertFalse(output.exists())

    def test_structured_lifecycle_rejects_ambiguous_timezone(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            draft, _ = write_lifecycle_draft(root)
            document = yaml.safe_load(draft.read_text())
            document["lifecycle_transition"]["timezone"] = "local"
            draft.write_text(yaml.safe_dump(document, sort_keys=False))
            output = root / "artifacts/frontier/B900/execution-start.yaml"
            with self.assertRaisesRegex(MODULE.BaselineError, "timezone must be UTC"):
                freeze_baseline(
                    draft,
                    "artifacts/frontier/B900/execution-baseline/",
                    output,
                    root.resolve(),
                )

    def test_structured_lifecycle_rejects_extra_field_diff(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            draft, _ = write_lifecycle_draft(root)
            document = yaml.safe_load(draft.read_text())
            document["lifecycle_transition"]["observed_field_diff"]["campaign_generation"] = {
                "from": 2,
                "to": 3,
            }
            draft.write_text(yaml.safe_dump(document, sort_keys=False))
            output = root / "artifacts/frontier/B900/execution-start.yaml"
            with self.assertRaisesRegex(MODULE.BaselineError, "exactly the three"):
                freeze_baseline(
                    draft,
                    "artifacts/frontier/B900/execution-baseline/",
                    output,
                    root.resolve(),
                )

    def test_structured_lifecycle_rejects_post_transition_drift(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            draft, frontier = write_lifecycle_draft(root)
            frontier.write_text(frontier.read_text() + "unexpected\n")
            output = root / "artifacts/frontier/B900/execution-start.yaml"
            with self.assertRaisesRegex(MODULE.BaselineError, "post-change identity"):
                freeze_baseline(
                    draft,
                    "artifacts/frontier/B900/execution-baseline/",
                    output,
                    root.resolve(),
                )

    def test_structured_packet_cannot_omit_transition_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            draft, _ = write_lifecycle_draft(root)
            document = yaml.safe_load(draft.read_text())
            document["lifecycle_transition"] = None
            draft.write_text(yaml.safe_dump(document, sort_keys=False))
            output = root / "artifacts/frontier/B900/execution-start.yaml"
            with self.assertRaisesRegex(MODULE.BaselineError, "requires a structured receipt"):
                freeze_baseline(
                    draft,
                    "artifacts/frontier/B900/execution-baseline/",
                    output,
                    root.resolve(),
                )

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

            frozen = freeze_baseline(
                draft,
                "artifacts/frontier/B900/execution-baseline/",
                output,
                root.resolve(),
            )
            snapshot_root = root / frozen["baseline_snapshot"]["root"]
            manifest = yaml.safe_load(
                (root / frozen["baseline_snapshot"]["manifest"]).read_text()
            )
            self.assertEqual(
                PROJECT_SNAPSHOT.member_bytes(root, manifest, "docs/task/FRONTIER.md"),
                b"campaign_status: running\nversion: start\n",
            )
            self.assertTrue(verify_baseline(output, root.resolve(), True)["snapshot_verified"])

            frontier.write_bytes(b"campaign_status: running\nversion: terminal\n")
            ledger.write_bytes(b"Selection: none\n")
            self.assertTrue(verify_baseline(output, root.resolve(), False)["snapshot_verified"])
            with self.assertRaisesRegex(MODULE.BaselineError, "live baseline drift"):
                verify_baseline(output, root.resolve(), True)

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
                freeze_baseline(
                    draft,
                    "artifacts/frontier/B900/execution-baseline/",
                    output,
                    root.resolve(),
                )
            self.assertFalse(output.exists())

    def test_missing_snapshot_ref_blocks_recovery_verification(self) -> None:
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
            frozen = freeze_baseline(
                draft,
                "artifacts/frontier/B900/execution-baseline/",
                output,
                root.resolve(),
            )
            manifest = yaml.safe_load(
                (root / frozen["baseline_snapshot"]["manifest"]).read_text()
            )
            subprocess.run(
                ["git", "-C", str(root), "update-ref", "-d", manifest["storage"]["ref"]],
                check=True,
            )
            with self.assertRaisesRegex(MODULE.BaselineError, "snapshot ref is missing"):
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
            frozen = freeze_baseline(
                draft,
                "artifacts/frontier/B900/execution-baseline/",
                output,
                root.resolve(),
            )
            snapshot_root = root / frozen["baseline_snapshot"]["root"]
            (snapshot_root / "undeclared.txt").write_text("not in manifest\n")
            with self.assertRaisesRegex(MODULE.BaselineError, "only its project snapshot manifest"):
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
            freeze_baseline(
                draft,
                "artifacts/frontier/B900/execution-baseline/",
                output,
                root.resolve(),
            )
            result = verify_baseline(output, root.resolve(), True)
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
                freeze_baseline(
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
                freeze_baseline(
                    draft,
                    "artifacts/frontier/B900/execution-baseline/",
                    output,
                    root.resolve(),
                )


if __name__ == "__main__":
    unittest.main()
