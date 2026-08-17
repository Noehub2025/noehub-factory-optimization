#!/usr/bin/env python3
"""Freeze and verify a recoverable Frontier execution-start baseline."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import posixpath
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from identity_bindings import (
    TREE_PATH_SHA256_V1,
    IdentityBindingError,
    load_file_binding,
    tree_inventory,
)
from post_adoption_state import (
    PostAdoptionStateError,
    expected_receipt,
    load_reviewed_files,
)
from project_snapshot import (
    SCHEMA as PROJECT_SNAPSHOT_SCHEMA,
    ProjectSnapshotError,
    capture as capture_project_snapshot,
    member_bytes as project_member_bytes,
    read_manifest as read_project_snapshot_manifest,
    verify as verify_project_snapshot,
)
from workflow_source_binding import (
    WorkflowSourceBindingError,
    source_member_bytes,
)
from frontier_provenance.content import ProvenanceError
from frontier_provenance.compatibility import require_v1_completion

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required to freeze Frontier execution baselines") from exc


LIFECYCLE_CONTRACT = "frontier-lifecycle-transition/1"
IDENTITY_CONTRACT = "frontier-dispatch-identity/2"
SUPPORTED_IDENTITY_CONTRACTS = {IDENTITY_CONTRACT}
DISPATCH_SOURCE_MEMBERS = (
    "scripts/freeze_execution_baseline.py",
    "scripts/validate_batch_packet.py",
    "scripts/validate_authorization_adoption.py",
    "scripts/validate_entry_packet.py",
)


class BaselineError(ValueError):
    """Raised when an execution baseline cannot be frozen or verified."""


def canonical_yaml(document: dict[str, Any], omitted_field: str) -> bytes:
    payload = dict(document)
    payload.pop(omitted_field, None)
    return yaml.safe_dump(payload, sort_keys=False, allow_unicode=True).encode()


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def normalize_repo_path(raw: Any, field: str) -> str:
    if not isinstance(raw, str) or not raw.strip() or raw.startswith("/"):
        raise BaselineError(f"{field} must be a nonempty repository-relative path")
    normalized = posixpath.normpath(raw.strip().rstrip("/"))
    if normalized in {".", ".."} or normalized.startswith("../"):
        raise BaselineError(f"{field} escapes the repository: {raw!r}")
    return normalized


def resolve_inside(repo_root: Path, raw: Any, field: str) -> tuple[str, Path]:
    relative = normalize_repo_path(raw, field)
    resolved = (repo_root / relative).resolve()
    try:
        resolved.relative_to(repo_root)
    except ValueError as exc:
        raise BaselineError(f"{field} resolves outside the repository: {raw!r}") from exc
    return relative, resolved


def declared_identity(entry: dict[str, Any], index: int) -> str:
    identity = entry.get("identity")
    if not isinstance(identity, str) or not identity.startswith("sha256:"):
        raise BaselineError(
            f"post_transition_baseline[{index}].identity must use sha256:<digest>"
        )
    digest = identity.removeprefix("sha256:")
    if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
        raise BaselineError(
            f"post_transition_baseline[{index}].identity is not a lowercase SHA-256"
        )
    return identity


def subtree_inventory(source: Path) -> tuple[list[dict[str, str]], str]:
    try:
        members, identity = tree_inventory(source, TREE_PATH_SHA256_V1)
    except IdentityBindingError as exc:
        raise BaselineError(str(exc)) from exc
    return (
        [{"path": member["path"], "sha256": member["sha256"]} for member in members],
        identity,
    )


def compute_execution_start_id(document: dict[str, Any]) -> str:
    digest = sha256_bytes(canonical_yaml(document, "execution_start_id"))
    return f"{document.get('batch_id', 'UNKNOWN')}-execution-start-sha256:{digest}"


def read_yaml(path: Path, label: str) -> dict[str, Any]:
    try:
        document = yaml.safe_load(path.read_text())
    except (OSError, yaml.YAMLError) as exc:
        raise BaselineError(f"cannot read {label}: {exc}") from exc
    if not isinstance(document, dict):
        raise BaselineError(f"{label} must contain a YAML mapping")
    return document


def load_validator(filename: str, module_name: str) -> Any:
    path = Path(__file__).with_name(filename)
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:  # pragma: no cover
        raise BaselineError(f"cannot load validator from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def canonical_json_artifact(document: dict[str, Any]) -> bytes:
    return (json.dumps(document, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()


def compute_acknowledgment_id(document: dict[str, Any]) -> str:
    digest = sha256_bytes(canonical_yaml(document, "acknowledgment_id"))
    return f"{document.get('batch_id', 'UNKNOWN')}-acknowledgment-sha256:{digest}"


def validate_post_adoption_live(
    execution_start: dict[str, Any],
    adoption: dict[str, Any],
    repo_root: Path,
) -> None:
    """Match live repository bytes to the exact state reviewed before authorization."""
    entry_binding = adoption.get("entry_packet")
    if not isinstance(entry_binding, dict):
        raise BaselineError("authorization adoption lacks its Entry packet binding")
    try:
        entry = load_file_binding(
            repo_root,
            {
                "path": entry_binding.get("path"),
                "identity_field": "packet_id",
                "identity": entry_binding.get("packet_id"),
                "file_sha256": entry_binding.get("file_sha256"),
            },
            "post-adoption Entry packet",
            expected_identity_field="packet_id",
        )
        target = load_file_binding(
            repo_root,
            {
                "path": adoption.get("authorization_target", {}).get("path"),
                "identity_field": "target_id",
                "identity": adoption.get("authorization_target", {}).get("target_id"),
                "file_sha256": adoption.get("authorization_target", {}).get("file_sha256"),
            },
            "post-adoption authorization target",
            expected_identity_field="target_id",
        )
    except IdentityBindingError as exc:
        raise BaselineError(str(exc)) from exc
    if entry.document is None or target.document is None:
        raise BaselineError("post-adoption Entry packet and target must contain mappings")

    manifest_binding = entry.document.get("snapshot_manifest")
    if not isinstance(manifest_binding, dict):
        raise BaselineError("post-adoption Entry packet lacks snapshot_manifest")
    _, manifest_path = resolve_inside(
        repo_root,
        manifest_binding.get("path"),
        "post-adoption snapshot manifest",
    )
    try:
        manifest, _ = read_project_snapshot_manifest(manifest_path)
        verify_project_snapshot(repo_root, manifest)
    except ProjectSnapshotError as exc:
        raise BaselineError(f"post-adoption project snapshot is invalid: {exc}") from exc
    snapshot_inputs: dict[str, tuple[bytes, str]] = {}
    for item in manifest.get("members", []):
        source_path = item.get("path") if isinstance(item, dict) else None
        digest = item.get("file_sha256") if isinstance(item, dict) else None
        if not isinstance(source_path, str) or not isinstance(digest, str):
            raise BaselineError("post-adoption project snapshot member is invalid")
        try:
            raw = project_member_bytes(repo_root, manifest, source_path)
        except ProjectSnapshotError as exc:
            raise BaselineError(str(exc)) from exc
        snapshot_inputs[source_path] = (raw, digest)

    def snapshot_bytes(path_value: str) -> bytes:
        source = snapshot_inputs.get(path_value)
        if source is None:
            raise PostAdoptionStateError(
                f"reviewed post-adoption source is missing from the snapshot: {path_value}"
            )
        raw = source[0]
        if sha256_bytes(raw) != source[1]:
            raise PostAdoptionStateError(
                f"reviewed post-adoption snapshot bytes changed: {path_value}"
            )
        return raw

    def snapshot_sha256(path_value: str) -> str:
        source = snapshot_inputs.get(path_value)
        if source is None:
            raise PostAdoptionStateError(
                f"reviewed post-adoption target is missing from the snapshot: {path_value}"
            )
        return source[1]

    try:
        reviewed_files = load_reviewed_files(
            target.document.get("post_adoption_state"),
            read_source=snapshot_bytes,
            pre_sha256_for=snapshot_sha256,
        )
    except PostAdoptionStateError as exc:
        raise BaselineError(str(exc)) from exc
    reviewed_by_path = {item.path: item for item in reviewed_files}

    for source_path, (snapshot_raw, digest) in snapshot_inputs.items():
        _, live_path = resolve_inside(
            repo_root,
            source_path,
            f"post-adoption live source {source_path}",
        )
        try:
            live_raw = live_path.read_bytes()
        except OSError as exc:
            raise BaselineError(
                f"post-adoption source is unreadable: {source_path}: {exc}"
            ) from exc
        if sha256_bytes(snapshot_raw) != digest:
            raise BaselineError(f"post-adoption snapshot bytes changed: {source_path}")
        reviewed = reviewed_by_path.get(source_path)
        expected = reviewed.post_bytes if reviewed is not None else snapshot_raw
        if live_raw != expected:
            state = "reviewed post-state" if reviewed is not None else "unchanged snapshot"
            raise BaselineError(
                f"post-adoption live source does not equal its {state}: {source_path}"
            )

    user_result = adoption.get("user_result")
    if not isinstance(user_result, dict):
        raise BaselineError("authorization adoption lacks its user result binding")
    receipt = expected_receipt(
        reviewed_files,
        target_id=target.identity,
        adoption_id=str(adoption.get("adoption_id")),
        user_result_id=str(user_result.get("identity")),
    )
    if execution_start.get("post_adoption_state") != receipt:
        raise BaselineError(
            "execution-start post_adoption_state does not equal the reviewed transition receipt"
        )

    baseline = execution_start.get("post_transition_baseline")
    if not isinstance(baseline, list):
        raise BaselineError("post_transition_baseline must be a list")
    for reviewed in reviewed_files:
        matches = [item for item in baseline if isinstance(item, dict) and item.get("path") == reviewed.path]
        if len(matches) != 1 or matches[0].get("scope") != "file":
            raise BaselineError(
                f"reviewed post-adoption path must appear once as a file baseline: {reviewed.path}"
            )
        if matches[0].get("identity") != f"sha256:{reviewed.post_sha256}":
            raise BaselineError(
                f"reviewed post-adoption baseline identity is wrong: {reviewed.path}"
            )


def validate_dispatch_chain(
    document: dict[str, Any], repo_root: Path, *, allow_legacy_audit: bool = False
) -> None:
    """Recompute every authority gate before minting or trusting execution-start."""
    packet_relative, packet_path = resolve_inside(
        repo_root, document.get("packet_path"), "packet_path"
    )
    packet = read_yaml(packet_path, f"packet {packet_relative}")
    if packet.get("identity_contract") not in SUPPORTED_IDENTITY_CONTRACTS:
        if allow_legacy_audit:
            return
        raise BaselineError(
            "packet predates a supported recoverable dispatch identity contract"
        )
    if packet.get("packet_id") != document.get("packet_id"):
        raise BaselineError("execution-start packet_id does not match the live packet")
    source_identity = (
        packet.get("workflow_source_binding", {})
        .get("source_snapshot", {})
        .get("identity")
    )
    if (
        not isinstance(source_identity, str)
        or document.get("workflow_source_identity") != source_identity
        or packet.get("workflow_source_identity") != source_identity
    ):
        raise BaselineError(
            "execution-start workflow source does not match the packet binding"
        )
    try:
        archived_dispatch_sources = {
            member: source_member_bytes(
                packet.get("workflow_source_binding"), repo_root, member
            )
            for member in DISPATCH_SOURCE_MEMBERS
        }
    except WorkflowSourceBindingError as exc:
        raise BaselineError(str(exc)) from exc
    historical_source = (
        packet.get("identity_contract") != IDENTITY_CONTRACT
        or any(
            content
            != (
                Path(__file__).read_bytes()
                if member == "scripts/freeze_execution_baseline.py"
                else Path(__file__).with_name(Path(member).name).read_bytes()
            )
            for member, content in archived_dispatch_sources.items()
        )
    )
    try:
        preflight = load_file_binding(
            repo_root,
            document.get("packet_preflight"),
            "packet_preflight",
            expected_identity_field="preflight_id",
        )
    except IdentityBindingError as exc:
        raise BaselineError(str(exc)) from exc
    if preflight.document is None:
        raise BaselineError("stored packet preflight must contain a mapping")
    if historical_source:
        if (
            preflight.document.get("packet_structure_ready") is not True
            or preflight.document.get("computed_packet_id") != packet.get("packet_id")
            or preflight.document.get("blocking_findings") != []
            or preflight.document.get("repair_findings") != []
        ):
            raise BaselineError(
                "archived-source dispatch requires its finding-free frozen packet preflight"
            )
    else:
        packet_validator = load_validator(
            "validate_batch_packet.py", "_frontier_batch_validator_for_execution"
        )
        recomputed_preflight = packet_validator.validate(packet, "frozen", repo_root)
        if not recomputed_preflight.get("packet_structure_ready"):
            raise BaselineError("live packet no longer passes its bound packet validator")
        if preflight.identity != recomputed_preflight.get("preflight_id"):
            raise BaselineError("stored packet preflight identity differs from recomputation")
        if preflight.raw != canonical_json_artifact(recomputed_preflight):
            raise BaselineError("stored packet preflight bytes do not equal current recomputation")

    def require_exact_entry_dispatch(entry_document: dict[str, Any]) -> None:
        entry_payload_sha256 = sha256_bytes(
            canonical_yaml(entry_document, "packet_id")
        )
        expected_entry_id = (
            f"entry-{entry_document.get('review_id', 'UNKNOWN')}-packet-sha256:"
            f"{entry_payload_sha256}"
        )
        if entry_document.get("packet_id") != expected_entry_id:
            raise BaselineError(
                "archived-source Entry identity does not derive from its canonical payload"
            )
        dispatch = entry_document.get("dispatch_contract")
        expected = {
            "batch_id": packet.get("batch_id"),
            "packet_path": packet_relative,
            "packet_id": packet.get("packet_id"),
            "preflight_path": preflight.relative_path,
            "preflight_id": preflight.identity,
            "preflight_file_sha256": preflight.file_sha256,
            "result_path": packet.get("result_packet_path"),
        }
        if not isinstance(dispatch, dict) or any(
            dispatch.get(field) != value for field, value in expected.items()
        ):
            raise BaselineError(
                "archived-source Entry dispatch does not bind the exact packet and preflight"
            )

    authority = document.get("execution_authority")
    if not isinstance(authority, dict):
        raise BaselineError("new execution-start requires structured execution_authority")
    mode = authority.get("mode")
    expected_mode = (
        "authorization-adoption"
        if packet.get("development_authorization_target") is not None
        else "spend-readiness"
    )
    if mode != expected_mode:
        raise BaselineError(
            f"execution authority mode {mode!r} does not match packet-required {expected_mode!r}"
        )
    authority_identity: str
    validation_identity: str
    if mode == "authorization-adoption":
        try:
            adoption = load_file_binding(
                repo_root,
                authority.get("record"),
                "execution_authority.record",
                expected_identity_field="adoption_id",
            )
            validation = load_file_binding(
                repo_root,
                authority.get("validation"),
                "execution_authority.validation",
                expected_identity_field="validation_id",
            )
        except IdentityBindingError as exc:
            raise BaselineError(str(exc)) from exc
        if adoption.document is None or validation.document is None:
            raise BaselineError("execution authority files must contain mappings")
        if adoption.document.get("entry_result") != "ENTRY_READY":
            raise BaselineError("authorization adoption does not grant ENTRY_READY")
        if historical_source:
            adoption_payload_sha256 = sha256_bytes(
                canonical_yaml(adoption.document, "adoption_id")
            )
            expected_adoption_id = (
                f"authorization-adoption-sha256:{adoption_payload_sha256}"
            )
            adoption_validation_payload = dict(validation.document)
            adoption_validation_payload.pop("validation_id", None)
            expected_validation_id = (
                "authorization-adoption-validation-sha256:"
                + sha256_bytes(
                    json.dumps(
                        adoption_validation_payload,
                        sort_keys=True,
                        separators=(",", ":"),
                        ensure_ascii=False,
                    ).encode()
                )
            )
            if (
                validation.document.get("authorization_adoption_valid") is not True
                or validation.document.get("blocking_findings") != []
                or validation.document.get("repair_findings") != []
            ):
                raise BaselineError(
                    "archived-source dispatch requires its finding-free adoption validation"
                )
            if (
                adoption.document.get("adoption_id") != expected_adoption_id
                or validation.document.get("adoption_payload_sha256")
                != adoption_payload_sha256
                or validation.document.get("computed_adoption_id")
                != expected_adoption_id
                or validation.identity != expected_validation_id
            ):
                raise BaselineError(
                    "archived-source adoption identity does not match its canonical payload and stored validation"
                )
            adopted_source = (
                adoption.document.get("workflow_source_binding", {})
                .get("source_snapshot", {})
                .get("identity")
            )
            if adopted_source != source_identity:
                raise BaselineError(
                    "archived-source adoption does not bind the packet workflow source"
                )
            target = adoption.document.get("authorization_target")
            if not isinstance(target, dict) or (
                target.get("batch_id") != packet.get("batch_id")
                or target.get("packet_id") != packet.get("packet_id")
            ):
                raise BaselineError(
                    "archived-source authorization target does not bind the exact packet"
                )
            try:
                entry_reference = adoption.document.get("entry_packet")
                if not isinstance(entry_reference, dict):
                    raise IdentityBindingError(
                        "authorization_adoption.entry_packet must be a mapping"
                    )
                adopted_entry = load_file_binding(
                    repo_root,
                    {
                        "path": entry_reference.get("path"),
                        "identity_field": "packet_id",
                        "identity": entry_reference.get("packet_id"),
                        "file_sha256": entry_reference.get("file_sha256"),
                    },
                    "authorization_adoption.entry_packet",
                    expected_identity_field="packet_id",
                )
            except IdentityBindingError as exc:
                raise BaselineError(str(exc)) from exc
            if adopted_entry.document is None:
                raise BaselineError("archived-source Entry packet must contain a mapping")
            require_exact_entry_dispatch(adopted_entry.document)
        else:
            adoption_validator = load_validator(
                "validate_authorization_adoption.py",
                "_frontier_adoption_validator_for_execution",
            )
            recomputed_adoption = adoption_validator.validate(
                adoption.document,
                "frozen",
                repo_root,
                reconcile_entry_live=False,
            )
            if not recomputed_adoption.get("authorization_adoption_valid"):
                raise BaselineError("authorization adoption is not valid under the current validator")
            if validation.raw != canonical_json_artifact(recomputed_adoption):
                raise BaselineError("stored adoption validation bytes do not equal current recomputation")
        validate_post_adoption_live(document, adoption.document, repo_root)
        authority_identity = adoption.identity
        validation_identity = validation.identity
    elif mode == "spend-readiness":
        if document.get("post_adoption_state") is not None:
            raise BaselineError("spend-readiness execution-start requires post_adoption_state: null")
        try:
            entry = load_file_binding(
                repo_root,
                authority.get("entry_packet"),
                "execution_authority.entry_packet",
                expected_identity_field="packet_id",
            )
            review = load_file_binding(
                repo_root,
                authority.get("record"),
                "execution_authority.record",
                expected_identity_field=None,
            )
            validation = load_file_binding(
                repo_root,
                authority.get("validation"),
                "execution_authority.validation",
                expected_identity_field="entry_schema_id",
            )
        except IdentityBindingError as exc:
            raise BaselineError(str(exc)) from exc
        if entry.document is None or validation.document is None:
            raise BaselineError("spend-readiness Entry files must contain mappings")
        if entry.document.get("review_stage") != "spend-readiness":
            raise BaselineError("spend-readiness authority requires the matching Entry stage")
        if historical_source:
            entry_payload_sha256 = sha256_bytes(
                canonical_yaml(entry.document, "packet_id")
            )
            expected_entry_id = (
                f"entry-{entry.document.get('review_id', 'UNKNOWN')}-packet-sha256:"
                f"{entry_payload_sha256}"
            )
            entry_validation_payload = dict(validation.document)
            entry_validation_payload.pop("entry_schema_id", None)
            expected_entry_validation_id = (
                f"entry-{entry.document.get('review_id', 'UNKNOWN')}-schema-sha256:"
                + sha256_bytes(
                    json.dumps(
                        entry_validation_payload,
                        sort_keys=True,
                        separators=(",", ":"),
                        ensure_ascii=False,
                    ).encode()
                )
            )
            if (
                validation.document.get("entry_schema_ready") is not True
                or validation.document.get("blocking_findings") != []
                or validation.document.get("repair_findings") != []
            ):
                raise BaselineError(
                    "archived-source dispatch requires its finding-free Entry validation"
                )
            if (
                entry.document.get("packet_id") != expected_entry_id
                or validation.document.get("packet_payload_sha256")
                != entry_payload_sha256
                or validation.document.get("computed_packet_id")
                != expected_entry_id
                or validation.identity != expected_entry_validation_id
            ):
                raise BaselineError(
                    "archived-source Entry identity does not match its canonical payload and stored validation"
                )
            entry_source = (
                entry.document.get("workflow_source_binding", {})
                .get("source_snapshot", {})
                .get("identity")
            )
            if entry_source != source_identity:
                raise BaselineError(
                    "archived-source Entry does not bind the packet workflow source"
                )
            require_exact_entry_dispatch(entry.document)
        else:
            entry_validator = load_validator(
                "validate_entry_packet.py", "_frontier_entry_validator_for_execution"
            )
            recomputed_entry = entry_validator.validate(entry.document, "frozen", repo_root)
            if not recomputed_entry.get("entry_schema_ready"):
                raise BaselineError("spend-readiness Entry packet is not source-valid")
            if validation.raw != canonical_json_artifact(recomputed_entry):
                raise BaselineError("stored Entry validation bytes do not equal current recomputation")
        frontmatter = read_frontmatter(review.raw, review.relative_path)
        if (
            frontmatter.get("review_result") != "ENTRY_READY"
            or frontmatter.get("packet_id") != entry.identity
            or frontmatter.get("snapshot_id") != entry.document.get("snapshot_id")
        ):
            raise BaselineError("spend-readiness review does not bind the Entry packet and snapshot")
        authority_identity = review.identity
        validation_identity = validation.identity
    else:
        raise BaselineError(
            "execution_authority.mode must be authorization-adoption or spend-readiness"
        )

    try:
        acknowledgment = load_file_binding(
            repo_root,
            document.get("acknowledgment"),
            "acknowledgment",
            expected_identity_field="acknowledgment_id",
        )
    except IdentityBindingError as exc:
        raise BaselineError(str(exc)) from exc
    if acknowledgment.document is None:
        raise BaselineError("acknowledgment must contain a mapping")
    ack = acknowledgment.document
    expected_ack_fields = {
        "batch_id": document.get("batch_id"),
        "packet_id": document.get("packet_id"),
        "workflow_source_identity": source_identity,
        "packet_preflight_id": preflight.identity,
        "authority_id": authority_identity,
        "authority_validation_id": validation_identity,
        "acknowledgment": "accepted",
    }
    if any(ack.get(field) != value for field, value in expected_ack_fields.items()):
        raise BaselineError("acknowledgment does not bind the recomputed execution authority")
    if ack.get("acknowledgment_id") != compute_acknowledgment_id(ack):
        raise BaselineError("acknowledgment identity does not derive from its canonical bytes")


def parse_utc_timestamp(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise BaselineError(f"{field} must be an RFC3339 UTC timestamp ending in Z")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise BaselineError(f"{field} is not a valid RFC3339 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise BaselineError(f"{field} must identify a UTC instant")
    return parsed


def normalized_timestamp(value: Any) -> str | None:
    if isinstance(value, datetime) and value.tzinfo is not None:
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    return value if isinstance(value, str) else None


def normalized_date(value: Any) -> str | None:
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return value if isinstance(value, str) else None


def read_frontmatter(content: bytes, path: str) -> dict[str, Any]:
    try:
        text = content.decode()
        if not text.startswith("---\n"):
            raise ValueError("missing YAML frontmatter")
        _, frontmatter_text, _ = text.split("---", 2)
        frontmatter = yaml.safe_load(frontmatter_text)
    except (UnicodeDecodeError, ValueError, yaml.YAMLError) as exc:
        raise BaselineError(f"lifecycle target {path} has invalid frontmatter: {exc}") from exc
    if not isinstance(frontmatter, dict):
        raise BaselineError(f"lifecycle target {path} frontmatter must be a mapping")
    return frontmatter


def validate_lifecycle_record_structure(document: dict[str, Any]) -> dict[str, Any] | None:
    transition = document.get("lifecycle_transition")
    if transition is None:
        return None
    if not isinstance(transition, dict):
        # Historical records used prose and remain governed by their frozen
        # workflow bytes. New structured packets are rejected below unless they
        # provide the versioned receipt.
        return None
    if transition.get("contract_version") != LIFECYCLE_CONTRACT:
        # Historical execution-start records predate the structured contract and
        # remain verifiable through their originally bound workflow bytes.
        return None

    required_strings = (
        "path",
        "transition_timestamp",
        "derived_updated",
        "pre_change_identity",
        "post_change_identity",
    )
    for field in required_strings:
        if not isinstance(transition.get(field), str) or not transition[field]:
            raise BaselineError(f"lifecycle_transition.{field} must be a nonempty string")
    if transition.get("timezone") != "UTC":
        raise BaselineError("lifecycle_transition.timezone must be UTC")

    transition_at = parse_utc_timestamp(
        transition["transition_timestamp"], "lifecycle_transition.transition_timestamp"
    )
    recorded_at = parse_utc_timestamp(document.get("recorded_at"), "recorded_at")
    if recorded_at < transition_at:
        raise BaselineError("recorded_at must not precede the lifecycle transition")
    expected_date = transition_at.date().isoformat()
    if transition["derived_updated"] != expected_date:
        raise BaselineError("derived_updated must be the UTC calendar date of transition_timestamp")

    observed = transition.get("observed_field_diff")
    expected_keys = {"campaign_status", "generated.at", "updated"}
    if not isinstance(observed, dict) or set(observed) != expected_keys:
        raise BaselineError("observed_field_diff must contain exactly the three authorized fields")
    if observed.get("campaign_status") != {"from": "planned", "to": "running"}:
        raise BaselineError("observed campaign_status diff must be planned to running")
    generated = observed.get("generated.at")
    updated = observed.get("updated")
    if not isinstance(generated, dict) or generated.get("to") != transition["transition_timestamp"]:
        raise BaselineError("observed generated.at must end at transition_timestamp")
    if not isinstance(generated.get("from"), str) or not generated["from"]:
        raise BaselineError("observed generated.at must record its prior value")
    if not isinstance(updated, dict) or updated.get("to") != expected_date:
        raise BaselineError("observed updated must end at the derived UTC date")
    if not isinstance(updated.get("from"), str) or not updated["from"]:
        raise BaselineError("observed updated must record its prior value")
    for field in ("pre_change_identity", "post_change_identity"):
        identity = transition[field]
        digest = identity.removeprefix("sha256:")
        if not identity.startswith("sha256:") or len(digest) != 64 or any(
            character not in "0123456789abcdef" for character in digest
        ):
            raise BaselineError(f"lifecycle_transition.{field} must be a lowercase SHA-256")
    return transition


def validate_lifecycle_live(
    document: dict[str, Any], baseline: list[Any], repo_root: Path
) -> None:
    packet_relative, packet_path = resolve_inside(
        repo_root, document.get("packet_path"), "packet_path"
    )
    packet = read_yaml(packet_path, f"packet {packet_relative}")
    if packet.get("packet_id") != document.get("packet_id"):
        raise BaselineError("execution-start packet_id does not match the live packet")
    contract = packet.get("coordinator_lifecycle_transition")
    structured_contract = (
        isinstance(contract, dict) and contract.get("contract_version") == LIFECYCLE_CONTRACT
    )
    raw_transition = document.get("lifecycle_transition")
    if structured_contract and (
        not isinstance(raw_transition, dict)
        or raw_transition.get("contract_version") != LIFECYCLE_CONTRACT
    ):
        raise BaselineError("structured packet lifecycle contract requires a structured receipt")

    transition = validate_lifecycle_record_structure(document)
    if transition is None:
        return
    if not structured_contract:
        raise BaselineError("structured lifecycle record requires the matching packet contract")
    if contract.get("path") != transition["path"]:
        raise BaselineError("lifecycle record path does not match the packet contract")
    precondition = contract.get("precondition")
    if not isinstance(precondition, dict) or precondition.get("file_identity") != transition[
        "pre_change_identity"
    ]:
        raise BaselineError("lifecycle pre-change identity does not match the packet precondition")

    target_relative, target = resolve_inside(
        repo_root, transition["path"], "lifecycle_transition.path"
    )
    if not target.is_file() or target.is_symlink():
        raise BaselineError(f"lifecycle target is missing or unsafe: {target_relative}")
    content = target.read_bytes()
    live_identity = f"sha256:{sha256_bytes(content)}"
    if live_identity != transition["post_change_identity"]:
        raise BaselineError("lifecycle post-change identity does not match the live target")

    matching_baselines = [
        item
        for item in baseline
        if isinstance(item, dict) and item.get("path") == target_relative
    ]
    if len(matching_baselines) != 1 or matching_baselines[0].get("scope") != "file":
        raise BaselineError("lifecycle target must appear once as a file baseline entry")
    if matching_baselines[0].get("identity") != live_identity:
        raise BaselineError("lifecycle target baseline identity must equal its post-change identity")

    frontmatter = read_frontmatter(content, target_relative)
    generated = frontmatter.get("generated")
    if frontmatter.get("campaign_status") != "running":
        raise BaselineError("lifecycle target campaign_status is not running")
    if not isinstance(generated, dict) or normalized_timestamp(generated.get("at")) != transition[
        "transition_timestamp"
    ]:
        raise BaselineError("lifecycle target generated.at does not equal transition_timestamp")
    if normalized_date(frontmatter.get("updated")) != transition["derived_updated"]:
        raise BaselineError("lifecycle target updated does not equal the derived UTC date")


def freeze(
    draft_path: Path, snapshot_base_value: str, output_path: Path, repo_root: Path
) -> dict[str, Any]:
    document = read_yaml(draft_path, "execution-start draft")
    if document.get("execution_start_id") is not None:
        raise BaselineError("execution-start draft must not contain execution_start_id")
    if document.get("baseline_snapshot") is not None:
        raise BaselineError("execution-start draft must not contain baseline_snapshot")
    validate_dispatch_chain(document, repo_root)
    packet_path = resolve_inside(repo_root, document.get("packet_path"), "packet_path")[1]
    packet = read_yaml(packet_path, "version 1 packet")
    if packet.get("identity_contract") in SUPPORTED_IDENTITY_CONTRACTS:
        authority_root = (
            document.get("execution_authority", {}).get("record", {}).get("identity")
        )
        try:
            inventory = read_yaml(
                repo_root / ".frontier/provenance-rollout.yaml",
                "v1 rollout inventory",
            )
            require_v1_completion(
                inventory,
                authority_root=authority_root,
                requested_descendant="execution-start",
                scope_root=packet.get("packet_id"),
                verified_parent_role="acknowledgment",
            )
        except (OSError, ProvenanceError) as exc:
            raise BaselineError(str(exc)) from exc
    baseline = document.get("post_transition_baseline")
    if not isinstance(baseline, list) or not baseline:
        raise BaselineError("post_transition_baseline must be a nonempty list")
    validate_lifecycle_live(document, baseline, repo_root)

    output_relative, expected_output = resolve_inside(
        repo_root, document.get("execution_start_path"), "execution_start_path"
    )
    if expected_output != output_path.resolve():
        raise BaselineError(
            f"execution_start_path {output_relative} does not match --output"
        )
    if output_path.exists():
        raise BaselineError(f"refusing to overwrite execution-start path: {output_relative}")

    snapshot_base_relative, snapshot_base = resolve_inside(
        repo_root, snapshot_base_value, "execution_baseline_root"
    )
    if snapshot_base.exists():
        raise BaselineError(
            f"refusing to reuse execution-baseline root: {snapshot_base_relative}"
        )
    if expected_output == snapshot_base or snapshot_base in expected_output.parents:
        raise BaselineError("execution-start path must be outside execution_baseline_root")
    for index, entry in enumerate(baseline):
        if not isinstance(entry, dict):
            raise BaselineError(f"post_transition_baseline[{index}] must be a mapping")
        _, source = resolve_inside(
            repo_root,
            entry.get("path"),
            f"post_transition_baseline[{index}].path",
        )
        scope = entry.get("scope")
        if source == expected_output or source == snapshot_base:
            raise BaselineError(
                f"post_transition_baseline[{index}] overlaps a Coordinator execution output"
            )
        if scope == "subtree" and (
            source in expected_output.parents or source in snapshot_base.parents
        ):
            raise BaselineError(
                f"post_transition_baseline[{index}] subtree contains a Coordinator execution output"
            )

    selected_paths: list[str] = []
    closed_roots: list[dict[str, Any]] = []
    seen_sources: set[str] = set()
    for index, entry in enumerate(baseline):
        source_path, source = resolve_inside(
            repo_root, entry.get("path"), f"post_transition_baseline[{index}].path"
        )
        if source_path in seen_sources:
            raise BaselineError("post_transition_baseline source paths must be unique")
        seen_sources.add(source_path)
        scope = entry.get("scope")
        expected = declared_identity(entry, index)
        if scope == "file":
            if not source.is_file() or source.is_symlink():
                raise BaselineError(f"baseline file is missing or unsafe: {source_path}")
            observed = f"sha256:{sha256_bytes(source.read_bytes())}"
            if observed != expected:
                raise BaselineError(
                    f"baseline identity mismatch for {source_path}: declared {expected}, computed {observed}"
                )
            selected_paths.append(source_path)
        elif scope == "subtree":
            members, observed = subtree_inventory(source)
            if observed != expected:
                raise BaselineError(
                    f"baseline identity mismatch for {source_path}/: declared {expected}, computed {observed}"
                )
            closed_roots.append(
                {
                    "path": source_path,
                    "expected_members": [item["path"] for item in members],
                }
            )
        else:
            raise BaselineError(
                f"post_transition_baseline[{index}].scope must be file or subtree"
            )

    manifest_path = snapshot_base / "project-snapshot.yaml"
    try:
        manifest = capture_project_snapshot(
            repo_root,
            manifest_path=manifest_path,
            paths=selected_paths,
            closed_roots=closed_roots,
            created_at=document.get("recorded_at"),
        )
    except ProjectSnapshotError as exc:
        raise BaselineError(f"cannot freeze execution project snapshot: {exc}") from exc
    document["baseline_snapshot"] = {
        "root": snapshot_base.relative_to(repo_root).as_posix(),
        "manifest": manifest_path.relative_to(repo_root).as_posix(),
        "snapshot_id": manifest["snapshot_id"],
        "input_count": len(baseline),
    }
    document["execution_start_id"] = compute_execution_start_id(document)
    rendered = yaml.safe_dump(document, sort_keys=False, allow_unicode=True).encode()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_output = output_path.with_name(f".{output_path.name}.tmp")
    if temporary_output.exists():
        raise BaselineError(f"temporary output already exists: {temporary_output}")
    temporary_output.write_bytes(rendered)
    os.replace(temporary_output, output_path)
    return document


def verify(execution_start_path: Path, repo_root: Path, require_live: bool) -> dict[str, Any]:
    document = read_yaml(execution_start_path, "execution-start record")
    validate_dispatch_chain(
        document,
        repo_root,
        allow_legacy_audit=not require_live,
    )
    validate_lifecycle_record_structure(document)
    declared_start_id = document.get("execution_start_id")
    computed_start_id = compute_execution_start_id(document)
    if declared_start_id != computed_start_id:
        raise BaselineError(
            f"execution_start_id mismatch: declared {declared_start_id}, computed {computed_start_id}"
        )
    snapshot = document.get("baseline_snapshot")
    if not isinstance(snapshot, dict):
        raise BaselineError("baseline_snapshot must be a mapping")
    _, snapshot_root = resolve_inside(repo_root, snapshot.get("root"), "baseline_snapshot.root")
    _, manifest_path = resolve_inside(
        repo_root, snapshot.get("manifest"), "baseline_snapshot.manifest"
    )
    if manifest_path.parent != snapshot_root:
        raise BaselineError("baseline manifest must be inside the declared snapshot root")
    manifest = read_yaml(manifest_path, "execution-baseline manifest")
    if manifest.get("schema") == PROJECT_SNAPSHOT_SCHEMA:
        try:
            project_result = verify_project_snapshot(
                repo_root,
                manifest,
                require_live=require_live,
            )
        except ProjectSnapshotError as exc:
            if require_live and (
                "live project member drift" in str(exc)
                or "closed project root" in str(exc)
            ):
                raise BaselineError(f"live baseline drift: {exc}") from exc
            raise BaselineError(f"execution project snapshot is invalid: {exc}") from exc
        if snapshot.get("snapshot_id") != manifest.get("snapshot_id"):
            raise BaselineError("execution-start and project snapshot bind different identities")
        baseline = document.get("post_transition_baseline")
        if not isinstance(baseline, list) or snapshot.get("input_count") != len(baseline):
            raise BaselineError("baseline input count mismatch")
        member_by_path = {
            item.get("path"): item
            for item in manifest.get("members", [])
            if isinstance(item, dict)
        }
        closed_by_path = {
            item.get("path"): item
            for item in manifest.get("closed_roots", [])
            if isinstance(item, dict)
        }
        covered_members: set[str] = set()
        for index, entry in enumerate(baseline):
            if not isinstance(entry, dict):
                raise BaselineError(f"baseline entry {index} must be a mapping")
            source_path = normalize_repo_path(
                entry.get("path"), f"post_transition_baseline[{index}].path"
            )
            expected = declared_identity(entry, index)
            scope = entry.get("scope")
            if scope == "file":
                member = member_by_path.get(source_path)
                if member is None or f"sha256:{member.get('file_sha256')}" != expected:
                    raise BaselineError(f"project snapshot identity mismatch for {source_path}")
                covered_members.add(source_path)
                continue
            if scope != "subtree":
                raise BaselineError(f"invalid snapshot scope for {source_path}")
            closed = closed_by_path.get(source_path)
            if closed is None or not isinstance(closed.get("members"), list):
                raise BaselineError(f"project snapshot closed root is missing: {source_path}")
            payload: list[dict[str, str]] = []
            for relative in closed["members"]:
                path = f"{source_path}/{relative}"
                member = member_by_path.get(path)
                if member is None:
                    raise BaselineError(f"project snapshot subtree member is missing: {path}")
                payload.append({"path": relative, "sha256": member["file_sha256"]})
                covered_members.add(path)
            observed = f"sha256:{sha256_bytes(json.dumps(payload, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode())}"
            if observed != expected:
                raise BaselineError(f"project snapshot subtree identity mismatch for {source_path}")
        if covered_members != set(member_by_path):
            raise BaselineError("project snapshot contains undeclared baseline members")
        actual_root_members = {
            path.relative_to(snapshot_root).as_posix()
            for path in snapshot_root.rglob("*")
            if path.is_file()
        }
        if actual_root_members != {manifest_path.name}:
            raise BaselineError("execution baseline root must contain only its project snapshot manifest")
        return {
            "execution_start_id": computed_start_id,
            "baseline_snapshot_id": manifest["snapshot_id"],
            "input_count": len(baseline),
            "snapshot_verified": project_result["snapshot_verified"],
            "live_baseline_matched": require_live,
        }
    raise BaselineError(
        "legacy copied execution baselines are audit records and cannot verify new authority"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    freeze_parser = subparsers.add_parser("freeze")
    freeze_parser.add_argument("draft", type=Path)
    freeze_parser.add_argument("--snapshot-root", required=True)
    freeze_parser.add_argument("--output", required=True, type=Path)
    freeze_parser.add_argument("--repo-root", type=Path, default=Path.cwd())

    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("execution_start", type=Path)
    verify_parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    verify_parser.add_argument("--live", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    try:
        if args.command == "freeze":
            result = freeze(
                args.draft,
                args.snapshot_root,
                args.output.resolve(),
                repo_root,
            )
            output = {
                "execution_start_id": result["execution_start_id"],
                "baseline_snapshot": result["baseline_snapshot"],
                "frozen": True,
            }
        else:
            output = verify(args.execution_start, repo_root, args.live)
    except (BaselineError, OSError, yaml.YAMLError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    sys.stdout.write(json.dumps(output, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
