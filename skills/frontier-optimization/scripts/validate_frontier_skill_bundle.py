#!/usr/bin/env python3
"""Validate and inventory the repository-local Optimization workflow bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

from finding_effects import add_finding, finalize_findings
from frontier_provenance import ProvenanceError
from frontier_provenance.source_modules import (
    audit_python_dependencies,
    validate_source_modules,
)

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required to validate the Optimization workflow bundle") from exc


VALIDATOR = "optimization-workflow-bundle/4"
EXPECTED_SKILLS = {
    "frame-optimization": False,
    "design-measurement": True,
    "design-implementation": True,
    "research-optimization": True,
    "grill-optimization": True,
    "review-optimization": True,
    "review-representation": True,
    "frontier-optimization": False,
    "research-frontier": True,
    "grill-frontier": True,
    "run-frontier-batch": True,
    "review-frontier": True,
}
REQUIRED_COORDINATOR_SCRIPTS = {
    "authorization_target_contract.py",
    "freeze_execution_baseline.py",
    "finding_effects.py",
    "identity_bindings.py",
    "package_frontier_handoff.py",
    "post_adoption_state.py",
    "project_snapshot.py",
    "frontier_provenance_cli.py",
    "validate_authorization_adoption.py",
    "validate_batch_packet.py",
    "validate_batch_result.py",
    "validate_candidate_package.py",
    "validate_candidate_recovery.py",
    "validate_entry_packet.py",
    "validate_frontier_skill_bundle.py",
    "run_workflow_checks.py",
}
LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
RUNTIME_ARTIFACT_LINKS = {"FRONTIER.md", "log.md"}
DISPATCH_INTERFACE_REQUIREMENTS = {
    "frontier-optimization/SKILL.md": "references/batch-interface.md#dispatch-state-machine",
    "frontier-optimization/references/campaign-cycle.md": "batch-interface.md#dispatch-state-machine",
    "run-frontier-batch/SKILL.md": "../frontier-optimization/references/batch-interface.md#dispatch-state-machine",
}
ACTION_ROUTER_REQUIREMENTS = {
    "frontier-optimization/SKILL.md": "references/result-adoption.md",
    "frontier-optimization/references/campaign-cycle.md": "result-adoption.md",
}
REVIEW_BRANCH_POINTER = "../frontier-optimization/references/review-branches.md"
REVIEW_BRANCH_ACTIONS = {
    "`entry`": "entry-review.md",
    "`replan`": "learning-loop.md#strategic-replan-review-method",
    "`design`": "design-review.md",
    "`implementation`": "implementation-review.md",
    "`claims`": "claim-review.md",
}
STAGE_HANDOFF_REQUIREMENTS = {
    "frame-optimization/SKILL.md": "references/frontier-handoff.md",
    "frontier-optimization/SKILL.md": "../frame-optimization/references/frontier-handoff.md",
}
BOUNDARY_CONTINUATION_REQUIREMENTS = {
    "frontier-optimization/references/planning-records.md": (
        "batch-interface.md#boundary-preserving-continuation"
    ),
    "frontier-optimization/references/entry-review.md": (
        "batch-interface.md#boundary-preserving-continuation"
    ),
    "frontier-optimization/references/worker-interfaces.md": (
        "batch-interface.md#boundary-preserving-continuation"
    ),
    "run-frontier-batch/SKILL.md": (
        "../frontier-optimization/references/"
        "batch-interface.md#boundary-preserving-continuation"
    ),
}
BOUNDARY_CONTINUATION_HEADING = "## Boundary-preserving continuation"
ENTRY_IDENTITY_CONTRACT_REQUIREMENTS = {
    "frontier-optimization/references/entry-review.md": (
        "entry_bindings_ready: true",
        "target_file_sha256",
        "derived_binding_checks",
        "non-authoritative",
        "frontier-post-adoption-state/1",
        "frontier-authorization-target-specification/1",
        "unique realization",
    ),
    "frontier-optimization/scripts/validate_entry_packet.py": (
        'VALIDATOR = "frontier-entry-packet-schema/7"',
        'CAMPAIGN_STATE_PROJECTION_CONTRACT = "frontier-current-state-projection/1"',
        "BOUND_IDENTITY_MISMATCH",
        "TARGET_DESIGN_BINDING_MISMATCH",
        "BATCH_PACKET_RECOMPUTATION_FAILED",
        "DESIGN_BATCH_SCOPED_IDENTITY_MISMATCH",
        "TARGET_SOURCE_BASE_IDENTITY_MISMATCH",
        "DISPATCH_CONTRACT_NOT_DERIVED",
        "AUTHORIZATION_TARGET_DISPATCH_MISMATCH",
        "POST_ADOPTION_STATE_INVALID",
        "TARGET_SPECIFICATION_REALIZATION_MISMATCH",
        "ARTIFACT_PATH_COLLISION",
        "PROJECT_SNAPSHOT_INVALID",
    ),
    "frontier-optimization/scripts/project_snapshot.py": (
        'SCHEMA = "frontier-project-snapshot/1"',
        'DEFAULT_REF = "refs/frontier/project-snapshots/current"',
        "GIT_INDEX_FILE",
        "FORBIDDEN_TOP_LEVEL",
        "publish_artifact",
        "update-ref",
    ),
    "frontier-optimization/scripts/authorization_target_contract.py": (
        'TARGET_SPEC_CONTRACT = "frontier-authorization-target-specification/1"',
        "omitted_top_level_field_digest",
        "validate_specification_against_packet",
        "validate_target_realization",
        "CURRENT_CHAIN_IDENTITY_PATTERNS",
    ),
    "frontier-optimization/scripts/validate_authorization_adoption.py": (
        'VALIDATOR = "frontier-authorization-adoption/6"',
        "ENTRY_SOURCE_RECONCILIATION_FAILED",
        "AUTHORIZATION_TARGET_NOT_DERIVED",
        "USER_ANSWER_NOT_DERIVED",
        "STATE_TRANSITION_NOT_DERIVED",
        "packet_id",
        "snapshot_id",
        "reconcile_entry_live",
        "ADOPTED_V_NOT_DERIVED",
        "USER_RESULT_IDENTITY_NOT_DERIVED",
        "USER_RESULT_SCHEMA_INVALID",
        "USER_RESULT_CONDITIONS_INVALID",
    ),
    "frontier-optimization/scripts/freeze_execution_baseline.py": (
        "validate_post_adoption_live",
        "reconcile_entry_live=False",
        "post_adoption_state",
        "capture_project_snapshot",
    ),
    "frontier-optimization/scripts/post_adoption_state.py": (
        'CONTRACT_VERSION = "frontier-post-adoption-state/1"',
        "load_reviewed_files",
        "expected_receipt",
    ),
}
RESULT_CONTRACT_REQUIREMENTS = {
    "frontier-optimization/references/batch-interface.md": (
        "result_contract_compatibility",
        "canonical nested `evaluation_target`",
        "without rerunning the measurement",
    ),
    "frontier-optimization/scripts/validate_batch_packet.py": (
        'VALIDATOR = "frontier-batch-packet-preflight/9"',
        'ENGINEERING_CHECK_PLAN_CONTRACT = "frontier-engineering-check-plan/1"',
        "ENGINEERING_EFFECT_CONFLICT",
        "validate_packet_result_contract",
        "DUPLICATE_EXPERIMENT_IDENTITY",
        "result_contract_compatibility",
        "frontier-dispatch-identity/2",
        "RESULT_CONTRACT_V1",
    ),
    "frontier-optimization/scripts/validate_batch_result.py": (
        'VALIDATOR = "frontier-batch-result-preflight/7"',
        "validate_evaluation_target_contract",
        "EXPERIMENT_LEGACY_BINDING_PRESENT",
        "DIAGNOSTIC_PERFORMANCE_STATE_INVALID",
        "EVALUATION_TARGET_SOURCE_IDENTITY_MISMATCH",
        "EVIDENCE_REUSE_SOURCE_IDENTITY_MISMATCH",
        "EVIDENCE_REUSE_ACCOUNTING_INVALID",
        "FORMAL_EVALUATION_RESULTS_MISSING",
        "EVIDENCE_REUSE_ACCOUNTING_OUTSIDE_RECOVERY",
        "FORMAL_EVALUATION_INTEGRATION_INVALID",
        "normalized_nested_keys",
        "validate_dispatch_bindings",
        "SUPPORTED_RESULT_CONTRACTS",
        "RESULT_CONTRACT_UNSUPPORTED",
    ),
    "frontier-optimization/scripts/evaluation_target_contract.py": (
        'TARGET_CONTRACT_V2 = "frontier-evaluation-target/2"',
        'ROUTINE_ADMISSION_CONTRACT = "frontier-routine-admission/1"',
        "EVALUATION_TARGET_LEGACY_BINDING_PRESENT",
        "DIAGNOSTIC_FORMAL_BINDING_PRESENT",
        "FORMAL_DIAGNOSTIC_BINDING_PRESENT",
        "EVIDENCE_REUSE_MODE_INVALID",
        "ROUTINE_PROHIBITIONS_INCOMPLETE",
        "EVALUATION_SCOPE_EXCEEDS_ROUTINE_LIMIT",
    ),
    "frontier-optimization/scripts/freeze_execution_baseline.py": (
        "validate_dispatch_chain",
        "authorization-adoption",
        "spend-readiness",
        "SUPPORTED_IDENTITY_CONTRACTS",
        "source_member_bytes",
        "archived-source dispatch",
    ),
    "frontier-optimization/scripts/validate_candidate_recovery.py": (
        'VALIDATOR = "frontier-candidate-recovery-preflight/5"',
        "CLOSEOUT_FACTS_NOT_DERIVED",
        "HANDOFF_FACTS_NOT_DERIVED",
        "BUDGET_FACTS_NOT_DERIVED",
        "reject_symlink_components",
    ),
    "frontier-optimization/scripts/validate_candidate_package.py": (
        'VALIDATOR = "frontier-candidate-package-validation/3"',
        'INVENTORY_CONTRACT = "frontier-candidate-package-inventory/1"',
        'FINAL_MANIFEST_CONTRACT = "frontier-candidate-manifest/3"',
        'LEGACY_FINAL_MANIFEST_CONTRACT = "frontier-candidate-manifest/2"',
        "PACKAGE_PATH_SIZE_SHA256_V1",
        "CANDIDATE_MEMBER_MISMATCH",
        "FORBIDDEN_RUNTIME_ARTIFACT",
        "stage_candidate_inventory",
        "stage_candidate_package",
    ),
    "frontier-optimization/scripts/package_frontier_handoff.py": (
        'VALIDATOR = "frontier-handoff-package/3"',
        "LINEAGE_SOURCE_NOT_PACKAGED",
        "CLOSEOUT_FACTS_NOT_DERIVED",
        "HANDOFF_FACTS_NOT_DERIVED",
        "BUDGET_FACTS_NOT_DERIVED",
        "reject_symlink_components",
    ),
    "run-frontier-batch/SKILL.md": (
        "canonical nested `evaluation_target`",
        "result-publication recovery B",
    ),
}
FINDING_EFFECT_REQUIREMENTS = {
    "frontier-optimization/references/frontier-core.md": (
        "## Finding effects",
        "An unknown code defaults to `block`",
        "Apply one decision-impact test",
        "create no replacement identity, B, V, review, or authorization",
        "Apply this contract prospectively",
        "`finding-free` means zero `block` or `repair` findings",
    ),
    "frontier-optimization/references/entry-review.md": (
        "frontier-entry-packet-schema/7",
        "zero `block` or `repair` findings",
        "## Advisories",
        "frontier-authorization-adoption/6",
    ),
    "frontier-optimization/references/batch-interface.md": (
        "frontier-batch-packet-preflight/9",
        "frontier-batch-result-preflight/7",
        '"blocking_findings": []',
        '"repair_findings": []',
        '"advisories": []',
    ),
    "frontier-optimization/scripts/finding_effects.py": (
        'BLOCK = "block"',
        'REPAIR = "repair"',
        'ADVISORY = "advisory"',
        "return BLOCK",
        "finalize_findings",
    ),
    "frontier-optimization/scripts/validate_entry_packet.py": (
        "finalize_findings",
        '"blocking_findings"',
        '"repair_findings"',
        '"advisories"',
    ),
    "frontier-optimization/scripts/validate_batch_packet.py": (
        "finalize_findings",
        '"blocking_findings"',
        '"repair_findings"',
        '"advisories"',
    ),
    "frontier-optimization/scripts/validate_batch_result.py": (
        "finalize_findings",
        '"blocking_findings"',
        '"repair_findings"',
        '"advisories"',
    ),
    "frontier-optimization/scripts/validate_authorization_adoption.py": (
        "finalize_findings",
        '"blocking_findings"',
        '"repair_findings"',
        '"advisories"',
    ),
    "frontier-optimization/scripts/validate_candidate_package.py": (
        "finalize_findings",
        '"blocking_findings"',
        '"repair_findings"',
        '"advisories"',
    ),
    "frontier-optimization/scripts/validate_candidate_recovery.py": (
        "finalize_findings",
        '"blocking_findings"',
        '"repair_findings"',
        '"advisories"',
    ),
    "frontier-optimization/scripts/package_frontier_handoff.py": (
        "finalize_findings",
        '"blocking_findings"',
        '"repair_findings"',
        '"advisories"',
    ),
    "frontier-optimization/scripts/validate_frontier_skill_bundle.py": (
        "finalize_findings",
        '"blocking_findings"',
        '"repair_findings"',
        '"advisories"',
    ),
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_frontmatter(path: Path) -> dict[str, Any]:
    text = path.read_text()
    if not text.startswith("---\n"):
        raise ValueError("missing YAML frontmatter")
    _, raw, _ = text.split("---", 2)
    parsed = yaml.safe_load(raw)
    if not isinstance(parsed, dict):
        raise ValueError("frontmatter must be a mapping")
    return parsed


def validate(skills_root: Path) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    source_files: list[dict[str, Any]] = []
    discovered = {path.name for path in skills_root.iterdir() if path.is_dir()}
    missing = sorted(set(EXPECTED_SKILLS) - discovered)
    for name in missing:
        add_finding(findings, "SKILL_MISSING", name)
    for name in sorted(discovered - set(EXPECTED_SKILLS)):
        add_finding(findings, "UNEXPECTED_SKILL", name)
    if "review-frontier-claims" in discovered:
        add_finding(
            findings,
            "EXTRA_REVIEWER_SKILL",
            "claims must use review-frontier with review_kind: claims",
        )

    for name, implicit_expected in EXPECTED_SKILLS.items():
        skill_root = skills_root / name
        skill_md = skill_root / "SKILL.md"
        openai_yaml = skill_root / "agents/openai.yaml"
        if not skill_md.is_file() or not openai_yaml.is_file():
            continue
        try:
            frontmatter = parse_frontmatter(skill_md)
            if set(frontmatter) != {"name", "description"}:
                add_finding(
                    findings,
                    "SKILL_FRONTMATTER_INVALID",
                    f"{name} frontmatter must contain exactly name and description",
                )
            if frontmatter.get("name") != name:
                add_finding(
                    findings,
                    "SKILL_NAME_MISMATCH",
                    f"{name} declares {frontmatter.get('name')!r}",
                )
            description = frontmatter.get("description")
            if (
                not isinstance(description, str)
                or not description.strip()
                or len(description) > 1024
                or "<" in description
                or ">" in description
            ):
                add_finding(
                    findings,
                    "SKILL_DESCRIPTION_INVALID",
                    f"{name} description must be nonempty, at most 1024 characters, and contain no angle brackets",
                )
            metadata = yaml.safe_load(openai_yaml.read_text())
            implicit = metadata.get("policy", {}).get("allow_implicit_invocation")
            if implicit is not implicit_expected:
                add_finding(
                    findings,
                    "INVOCATION_POLICY_INVALID",
                    f"{name} allow_implicit_invocation is {implicit!r}, expected {implicit_expected!r}",
                )
        except (OSError, ValueError, yaml.YAMLError) as exc:
            add_finding(findings, "SKILL_METADATA_INVALID", f"{name}: {exc}")

    for relative, pointer in DISPATCH_INTERFACE_REQUIREMENTS.items():
        path = skills_root / relative
        if not path.is_file() or pointer not in path.read_text():
            add_finding(
                findings,
                "DISPATCH_INTERFACE_POINTER_MISSING",
                f"{relative} must point to {pointer}",
            )

    for relative, pointer in ACTION_ROUTER_REQUIREMENTS.items():
        path = skills_root / relative
        if not path.is_file() or pointer not in path.read_text():
            add_finding(
                findings,
                "CAMPAIGN_ACTION_ROUTER_INVALID",
                f"{relative} must point to {pointer}",
            )

    for relative, pointer in STAGE_HANDOFF_REQUIREMENTS.items():
        path = skills_root / relative
        if not path.is_file() or pointer not in path.read_text():
            add_finding(
                findings,
                "STAGE_HANDOFF_POINTER_MISSING",
                f"{relative} must point to {pointer}",
            )

    continuation_contract = (
        skills_root / "frontier-optimization/references/batch-interface.md"
    )
    continuation_text = (
        continuation_contract.read_text() if continuation_contract.is_file() else ""
    )
    if BOUNDARY_CONTINUATION_HEADING not in continuation_text:
        add_finding(
            findings,
            "BOUNDARY_CONTINUATION_CONTRACT_INVALID",
            "batch-interface.md must own boundary-preserving continuation",
        )
    for relative, pointer in BOUNDARY_CONTINUATION_REQUIREMENTS.items():
        path = skills_root / relative
        if not path.is_file() or pointer not in path.read_text():
            add_finding(
                findings,
                "BOUNDARY_CONTINUATION_POINTER_MISSING",
                f"{relative} must point to {pointer}",
            )

    for relative, markers in ENTRY_IDENTITY_CONTRACT_REQUIREMENTS.items():
        path = skills_root / relative
        text = path.read_text() if path.is_file() else ""
        for marker in markers:
            if marker not in text:
                add_finding(
                    findings,
                    "ENTRY_IDENTITY_CONTRACT_INVALID",
                    f"{relative} must contain {marker}",
                )

    for relative, markers in RESULT_CONTRACT_REQUIREMENTS.items():
        path = skills_root / relative
        text = path.read_text() if path.is_file() else ""
        for marker in markers:
            if marker not in text:
                add_finding(
                    findings,
                    "RESULT_CONTRACT_INVALID",
                    f"{relative} must contain {marker}",
                )

    for relative, markers in FINDING_EFFECT_REQUIREMENTS.items():
        path = skills_root / relative
        text = path.read_text() if path.is_file() else ""
        for marker in markers:
            if marker not in text:
                add_finding(
                    findings,
                    "FINDING_EFFECT_CONTRACT_INVALID",
                    f"{relative} must contain {marker}",
                )

    reviewer = skills_root / "review-frontier/SKILL.md"
    if not reviewer.is_file() or REVIEW_BRANCH_POINTER not in reviewer.read_text():
        add_finding(
            findings,
            "REVIEW_BRANCH_REGISTRY_INVALID",
            f"review-frontier/SKILL.md must point to {REVIEW_BRANCH_POINTER}",
        )
    registry = skills_root / "frontier-optimization/references/review-branches.md"
    registry_text = registry.read_text() if registry.is_file() else ""
    for review_kind, action in REVIEW_BRANCH_ACTIONS.items():
        if review_kind not in registry_text or action not in registry_text:
            add_finding(
                findings,
                "REVIEW_BRANCH_REGISTRY_INVALID",
                f"{review_kind} must select {action}",
            )

    scripts_root = skills_root / "frontier-optimization/scripts"
    observed_scripts = {path.name for path in scripts_root.glob("*.py") if not path.name.startswith("test_")}
    for name in sorted(REQUIRED_COORDINATOR_SCRIPTS - observed_scripts):
        add_finding(findings, "REQUIRED_SCRIPT_MISSING", name)

    source_module_manifest = (
        skills_root
        / "frontier-optimization/references/source-modules.yaml"
    )
    try:
        source_modules = yaml.safe_load(source_module_manifest.read_text())
        validate_source_modules(source_modules, skills_root)
        audit_python_dependencies(source_modules, skills_root)
    except (OSError, yaml.YAMLError, ProvenanceError) as exc:
        add_finding(
            findings,
            "SOURCE_MODULE_MANIFEST_INVALID",
            str(exc),
        )

    for skill_name in EXPECTED_SKILLS:
        skill_root = skills_root / skill_name
        if not skill_root.exists():
            continue
        for path in sorted(skill_root.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(skills_root)
            if "__pycache__" in relative.parts or path.suffix in {".pyc", ".pyo"}:
                continue
            if path.is_symlink():
                add_finding(findings, "SYMLINK_NOT_PORTABLE", relative.as_posix())
                continue
            data = path.read_bytes()
            source_files.append(
                {
                    "path": relative.as_posix(),
                    "size": len(data),
                    "sha256": hashlib.sha256(data).hexdigest(),
                }
            )
            if path.suffix == ".md":
                text = data.decode()
                if "/Users/" in text or "file://" in text:
                    add_finding(
                        findings,
                        "HOST_PATH_NOT_PORTABLE",
                        relative.as_posix(),
                    )
                for raw_target in LINK_PATTERN.findall(text):
                    target = raw_target.split("#", 1)[0]
                    if not target or "://" in target or target.startswith("/"):
                        continue
                    if target in RUNTIME_ARTIFACT_LINKS or target.startswith("frontier/"):
                        continue
                    resolved = (path.parent / target).resolve()
                    try:
                        resolved.relative_to(skills_root.resolve())
                    except ValueError:
                        add_finding(
                            findings,
                            "LINK_ESCAPES_BUNDLE",
                            f"{relative.as_posix()} -> {raw_target}",
                        )
                        continue
                    if not resolved.exists():
                        add_finding(
                            findings,
                            "BROKEN_INTERNAL_LINK",
                            f"{relative.as_posix()} -> {raw_target}",
                        )

    source_files.sort(key=lambda item: item["path"])
    bundle_sha256 = hashlib.sha256(
        json.dumps(
            source_files,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode()
    ).hexdigest()
    finding_summary = finalize_findings(findings)
    return {
        "validator": VALIDATOR,
        "expected_skills": sorted(EXPECTED_SKILLS),
        "bundle_sha256": bundle_sha256,
        "source_manifest": source_files,
        "bundle_ready": finding_summary["ready"],
        "findings": finding_summary["findings"],
        "blocking_findings": finding_summary["blocking_findings"],
        "repair_findings": finding_summary["repair_findings"],
        "advisories": finding_summary["advisories"],
        "finding_effect_counts": finding_summary["finding_effect_counts"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skills_root", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        result = validate(args.skills_root.resolve())
    except OSError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered)
    else:
        print(rendered, end="")
    return 0 if result["bundle_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
