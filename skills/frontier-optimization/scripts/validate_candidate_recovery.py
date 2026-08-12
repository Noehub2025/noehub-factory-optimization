#!/usr/bin/env python3
"""Validate byte-identical Frontier candidate reuse before opening a generation."""

from __future__ import annotations

import argparse
import hashlib
import json
import posixpath
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required to validate candidate recovery") from exc


VALIDATOR = "frontier-candidate-recovery-preflight/1"
REQUIRED_FIELDS = {
    "recovery_preflight_path",
    "prior_campaign_generation",
    "campaign_generation",
    "prior_closeout",
    "inherited_budget",
    "candidate_root",
    "candidate_manifest_path",
    "requested_candidate_id",
    "requested_manifest_sha256",
    "review_mode",
    "candidate_mutation",
    "new_proposal_attempts",
}


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode()


def canonical_payload(document: dict[str, Any]) -> bytes:
    payload = dict(document)
    payload.pop("recovery_preflight_id", None)
    return yaml.safe_dump(payload, sort_keys=False, allow_unicode=True).encode()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_relative(raw: Any, field: str) -> str:
    if not isinstance(raw, str) or not raw.strip() or raw.startswith("/"):
        raise ValueError(f"{field} must be a nonempty repository-relative path")
    normalized = posixpath.normpath(raw.strip().rstrip("/"))
    if normalized in {".", ".."} or normalized.startswith("../"):
        raise ValueError(f"{field} escapes the repository")
    return normalized


def package_inventory(root: Path) -> tuple[list[dict[str, Any]], str]:
    members: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if "__pycache__" in relative.parts or path.suffix in {".pyc", ".pyo"}:
            continue
        members.append(
            {
                "path": relative.as_posix(),
                "size": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    if not members:
        raise ValueError("candidate package is empty")
    return members, hashlib.sha256(canonical_json(members)).hexdigest()


def add_finding(findings: list[dict[str, str]], code: str, detail: str) -> None:
    finding = {"code": code, "detail": detail}
    if finding not in findings:
        findings.append(finding)


def validate(
    document: dict[str, Any], phase: str, repo_root: Path
) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    for field in sorted(REQUIRED_FIELDS - document.keys()):
        add_finding(findings, "REQUIRED_FIELD_MISSING", field)

    prior_generation = document.get("prior_campaign_generation")
    generation = document.get("campaign_generation")
    if (
        not isinstance(prior_generation, int)
        or isinstance(prior_generation, bool)
        or prior_generation < 1
        or generation != prior_generation + 1
    ):
        add_finding(
            findings,
            "GENERATION_LINEAGE_INVALID",
            "campaign_generation must equal prior_campaign_generation + 1",
        )

    closeout = document.get("prior_closeout")
    if not isinstance(closeout, dict):
        add_finding(findings, "CLOSEOUT_LINEAGE_INVALID", "prior_closeout must be a mapping")
    else:
        if closeout.get("event") != "CLOSEOUT_COMPLETE":
            add_finding(
                findings,
                "CLOSEOUT_INCOMPLETE",
                "prior closeout event must be CLOSEOUT_COMPLETE",
            )
        if closeout.get("campaign_generation") != prior_generation:
            add_finding(
                findings,
                "CLOSEOUT_LINEAGE_INVALID",
                "prior closeout generation does not match prior_campaign_generation",
            )
        if closeout.get("campaign_status") not in {"stopped", "halted"}:
            add_finding(
                findings,
                "CLOSEOUT_STATUS_INVALID",
                "prior closeout status must be stopped or halted",
            )
        if closeout.get("unresolved_claims") != []:
            add_finding(
                findings,
                "UNRESOLVED_CLAIMS",
                "post-closeout recovery requires no unresolved claim branch",
            )
        if closeout.get("active_workers") != []:
            add_finding(
                findings,
                "ACTIVE_WORKERS",
                "post-closeout recovery requires no active worker",
            )
        for field in ("closeout_identity", "final_handoff_identity"):
            if not isinstance(closeout.get(field), str) or not closeout[field].strip():
                add_finding(
                    findings,
                    "CLOSEOUT_LINEAGE_INVALID",
                    f"prior_closeout requires {field}",
                )

    budget = document.get("inherited_budget")
    if not isinstance(budget, dict):
        add_finding(findings, "BUDGET_LINEAGE_INVALID", "inherited_budget must be a mapping")
    else:
        for field in ("proposal_attempt_ceiling", "actual_spend", "unknown_spend"):
            value = budget.get(field)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                add_finding(
                    findings,
                    "BUDGET_LINEAGE_INVALID",
                    f"inherited_budget {field} must be a nonnegative integer",
                )
        ceiling = budget.get("proposal_attempt_ceiling")
        spent = budget.get("actual_spend")
        unknown = budget.get("unknown_spend")
        if all(isinstance(value, int) and not isinstance(value, bool) for value in (ceiling, spent, unknown)):
            if spent + unknown > ceiling:
                add_finding(
                    findings,
                    "BUDGET_LINEAGE_INVALID",
                    "actual and unknown spend exceed the inherited ceiling",
                )
        if budget.get("active_reservations") != []:
            add_finding(
                findings,
                "ACTIVE_RESERVATIONS",
                "complete closeout must not carry active reservations",
            )
        if not isinstance(budget.get("budget_identity"), str) or not budget["budget_identity"].strip():
            add_finding(
                findings,
                "BUDGET_LINEAGE_INVALID",
                "inherited_budget requires budget_identity",
            )

    if document.get("review_mode") != "recovery-reuse":
        add_finding(
            findings,
            "REVIEW_MODE_INVALID",
            "byte-identical reuse requires review_mode: recovery-reuse",
        )
    if document.get("candidate_mutation") != "prohibited":
        add_finding(
            findings,
            "CANDIDATE_MUTATION_NOT_PROHIBITED",
            "recovery validation must prohibit candidate mutation",
        )
    if document.get("new_proposal_attempts") != 0:
        add_finding(
            findings,
            "ZERO_COST_REUSE_INVALID",
            "byte-identical recovery validation requires zero new proposal attempts",
        )

    manifest: dict[str, Any] | None = None
    manifest_sha256: str | None = None
    members: list[dict[str, Any]] = []
    package_sha256: str | None = None
    try:
        candidate_root_value = safe_relative(document.get("candidate_root"), "candidate_root")
        manifest_value = safe_relative(
            document.get("candidate_manifest_path"), "candidate_manifest_path"
        )
        candidate_root = (repo_root / candidate_root_value).resolve()
        manifest_path = (repo_root / manifest_value).resolve()
        if repo_root not in candidate_root.parents or repo_root not in manifest_path.parents:
            raise ValueError("candidate or manifest path escapes the repository")
        if not candidate_root.is_dir():
            raise ValueError(f"candidate root is missing: {candidate_root_value}")
        if not manifest_path.is_file():
            raise ValueError(f"candidate manifest is missing: {manifest_value}")
        manifest_sha256 = sha256_file(manifest_path)
        parsed = yaml.safe_load(manifest_path.read_bytes())
        if not isinstance(parsed, dict):
            raise ValueError("candidate manifest must contain a YAML mapping")
        manifest = parsed
        members, package_sha256 = package_inventory(candidate_root)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        add_finding(findings, "CANDIDATE_RECOVERY_UNREADABLE", str(exc))

    requested_manifest = document.get("requested_manifest_sha256")
    if manifest_sha256 is not None and requested_manifest != manifest_sha256:
        add_finding(
            findings,
            "REQUESTED_MANIFEST_IDENTITY_MISMATCH",
            f"requested {requested_manifest!r}; recomputed {manifest_sha256!r}",
        )

    canonical_candidate_id: str | None = None
    if manifest is not None and package_sha256 is not None:
        manifest_candidate_id = manifest.get("candidate_id")
        if isinstance(manifest_candidate_id, str) and ":" in manifest_candidate_id:
            canonical_candidate_id = f"{manifest_candidate_id.rsplit(':', 1)[0]}:{package_sha256}"
        else:
            add_finding(
                findings,
                "MANIFEST_CANDIDATE_ID_INVALID",
                "candidate manifest requires a namespaced candidate_id",
            )
        if manifest_candidate_id != canonical_candidate_id:
            add_finding(
                findings,
                "MANIFEST_CANDIDATE_IDENTITY_MISMATCH",
                f"manifest records {manifest_candidate_id!r}; recomputed {canonical_candidate_id!r}",
            )
        requested_candidate = document.get("requested_candidate_id")
        if requested_candidate != canonical_candidate_id:
            add_finding(
                findings,
                "REQUESTED_CANDIDATE_IDENTITY_MISMATCH",
                f"requested {requested_candidate!r}; recomputed {canonical_candidate_id!r}",
            )
        if manifest.get("campaign_generation") != prior_generation:
            add_finding(
                findings,
                "CANDIDATE_GENERATION_MISMATCH",
                "candidate manifest generation does not match the closed source generation",
            )

        recorded_paths = manifest.get("code_paths")
        if not isinstance(recorded_paths, list):
            add_finding(
                findings,
                "MANIFEST_MEMBER_SCHEMA_INVALID",
                "candidate manifest code_paths must be a list",
            )
        else:
            recorded: list[dict[str, str]] = []
            for item in recorded_paths:
                if not isinstance(item, dict) or not isinstance(item.get("path"), str) or not isinstance(item.get("sha256"), str):
                    add_finding(
                        findings,
                        "MANIFEST_MEMBER_SCHEMA_INVALID",
                        "each code_paths entry requires path and sha256 strings",
                    )
                    continue
                recorded.append({"path": item["path"], "sha256": item["sha256"].removeprefix("sha256:")})
            observed = [{"path": item["path"], "sha256": item["sha256"]} for item in members]
            if recorded != observed:
                add_finding(
                    findings,
                    "CANDIDATE_MEMBER_MISMATCH",
                    f"manifest members {recorded!r}; recomputed {observed!r}",
                )

        for field in (
            "candidate_interface",
            "source_base_identity",
            "source_result_identity",
            "dependency_identity",
            "runtime_factors",
            "generated_assets",
        ):
            if field not in manifest:
                add_finding(
                    findings,
                    "IDENTITY_INPUT_MISSING",
                    f"candidate manifest is missing {field}",
                )

    payload_sha256 = hashlib.sha256(canonical_payload(document)).hexdigest()
    expected_id = f"candidate-recovery-preflight-sha256:{payload_sha256}"
    declared_id = document.get("recovery_preflight_id")
    if phase == "draft" and declared_id is not None:
        add_finding(
            findings,
            "DRAFT_ALREADY_FROZEN",
            "draft recovery validation requires recovery_preflight_id to be absent",
        )
    elif phase == "frozen":
        if declared_id is None:
            add_finding(findings, "RECOVERY_PREFLIGHT_ID_MISSING", "frozen preflight requires recovery_preflight_id")
        elif declared_id != expected_id:
            add_finding(
                findings,
                "RECOVERY_PREFLIGHT_ID_MISMATCH",
                f"declared {declared_id!r}; computed {expected_id!r}",
            )
    elif phase not in {"draft", "frozen", "audit"}:
        add_finding(findings, "PHASE_INVALID", "phase must be draft, frozen, or audit")

    findings.sort(key=lambda item: (item["code"], item["detail"]))
    return {
        "validator": VALIDATOR,
        "recovery_preflight_path": document.get("recovery_preflight_path"),
        "prior_campaign_generation": prior_generation,
        "campaign_generation": generation,
        "candidate_manifest_path": document.get("candidate_manifest_path"),
        "recomputed_manifest_sha256": manifest_sha256,
        "recomputed_candidate_id": canonical_candidate_id,
        "recomputed_members": members,
        "computed_recovery_preflight_id": expected_id,
        "recovery_ready": not findings,
        "findings": findings,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("preflight", type=Path)
    parser.add_argument("--phase", choices=("draft", "frozen", "audit"), required=True)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        document = yaml.safe_load(args.preflight.read_bytes())
    except (OSError, yaml.YAMLError) as exc:
        print(f"cannot read recovery preflight: {exc}", file=sys.stderr)
        return 2
    if not isinstance(document, dict):
        print("recovery preflight must contain a YAML mapping", file=sys.stderr)
        return 2
    result = validate(document, args.phase, args.repo_root.resolve())
    if args.output is not None:
        write_json(args.output, result)
    else:
        print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["recovery_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
