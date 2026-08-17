#!/usr/bin/env python3
"""Interface and attack-path tests for task-neutral Frontier provenance."""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
import yaml

from frontier_provenance import (
    NodeRepository,
    ProvenanceError,
    attest,
    bind_authority,
    freeze_decision,
    freeze_execution,
    record_outcome,
    verify_chain,
    verify_for,
)
from frontier_provenance.source_modules import (
    audit_python_dependencies,
    source_module_root,
    validate_source_modules,
)
from frontier_provenance.compatibility import require_v1_completion
from frontier_provenance.content import authority_payload
from frontier_provenance.stores import (
    ArtifactSource,
    ClosedCollection,
    GitSnapshotStore,
    ProjectPortableStore,
    PortableBundleStore,
    WorkflowReleaseGitStore,
)
from frontier_provenance.handoff import export_handoff, verify_handoff
from frontier_provenance.graph import build_node
from frontier_provenance_cli import (
    REQUEST_CONTRACT,
    apply_operation,
    content_resolver as cli_content_resolver,
)


TEST_DOMAINS: dict[str, str] = {}
DOMAIN_ROLES = {
    "project-decision": "decision",
    "review-report": "review",
    "project-authority": "authority",
    "project-state": "state",
    "project-outcome": "outcome",
    "live-receipt": "receipt",
}
DOMAIN_PREFIXES = {
    "project-decision": "project/decision/",
    "review-report": "project/review/",
    "project-authority": "project/authority/",
    "project-state": "project/state/",
    "project-outcome": "project/outcome/",
    "live-receipt": "receipts/",
    "workflow-release": "release/",
}


def typed_root(domain: str, seed: str) -> str:
    root = "frontier-content-root-sha256:" + hashlib.sha256(
        f"{domain}:{seed}".encode()
    ).hexdigest()
    TEST_DOMAINS[root] = domain
    return root


def git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return result.stdout.decode().strip()


def content_resolver(content_root: str) -> dict[str, object]:
    receipt_names = {
        "authority_current",
        "budget_current",
        "reservation_current",
        "inputs_current",
        "resources_available",
        "action_window_open",
        "prior_external_effects_known",
        "budget_accounted",
    }
    return {
        "content_root": content_root,
        "domain": TEST_DOMAINS[content_root],
        "verified": True,
        "receipt_facts": {
            name: {
                "status": "pass",
                "observed_at": "2026-08-17T00:00:00Z",
                "expires_at": "2026-08-17T02:00:00Z",
            }
            for name in receipt_names
        },
    }


def fact(receipt_root: str) -> dict[str, str]:
    return {"receipt_root": receipt_root}


def initialize(root: Path) -> None:
    git(root, "init", "-q")
    (root / "tracked.txt").write_bytes(b"tracked\n")
    git(root, "add", "tracked.txt")
    git(
        root,
        "-c",
        "user.name=Provenance Test",
        "-c",
        "user.email=provenance@example.invalid",
        "commit",
        "-qm",
        "initial",
    )


def chain(content_root: str) -> tuple[dict, dict, dict, dict, dict[str, dict]]:
    TEST_DOMAINS[content_root] = "live-receipt"
    roots = {
        domain: typed_root(domain, content_root)
        for domain in (
            "project-decision",
            "review-report",
            "project-authority",
            "project-state",
            "project-outcome",
        )
    }
    return chain_with_roots(roots)


def chain_with_roots(
    roots: dict[str, str],
) -> tuple[dict, dict, dict, dict, dict[str, dict]]:
    decision = freeze_decision(decision_root=roots["project-decision"])
    validation = attest(
        decision,
        validation_report_root=roots["review-report"],
        verdict="ready",
        findings=[],
    )
    authority = bind_authority(
        authority_root=roots["project-authority"],
        decision=decision,
        validation=validation,
    )
    execution = freeze_execution(
        authority=authority,
        starting_state_root=roots["project-state"],
    )
    outcome = record_outcome(
        execution=execution,
        outcome_root=roots["project-outcome"],
    )
    nodes = {
        node["node_id"]: node
        for node in (decision, validation, authority, execution, outcome)
    }
    return decision, authority, execution, outcome, nodes


def portable_project_chain(
    root: Path, source: Path
) -> tuple[dict, dict[str, dict], dict[str, object]]:
    roots: dict[str, str] = {}
    bundles: dict[str, Path] = {}
    for domain in (
        "project-decision",
        "review-report",
        "project-authority",
        "project-state",
        "project-outcome",
    ):
        bundle = root / f"content-{domain}"
        manifest = ProjectPortableStore().capture(
            DOMAIN_ROLES[domain],
            [ArtifactSource(DOMAIN_PREFIXES[domain] + "project-record.txt", source)],
            bundle,
            project_root=root,
        )
        roots[domain] = manifest["content_root"]
        bundles[manifest["content_root"]] = bundle
    _, _, _, outcome, nodes = chain_with_roots(roots)

    def exporter(source_bundle: Path):
        def copy(destination: Path) -> None:
            shutil.copytree(source_bundle, destination)

        return copy

    return outcome, nodes, {
        content_root: exporter(bundle)
        for content_root, bundle in bundles.items()
    }


def test_release_git_and_portable_adapters_share_one_raw_byte_content_root() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory) / "repo"
        root.mkdir()
        initialize(root)
        (root / ".gitattributes").write_text("*.txt text eol=crlf\n")
        closed_directory = root / "input-dir"
        closed_directory.mkdir()
        ignored = closed_directory / "raw.txt"
        ignored.write_bytes(b"raw-lf\n")
        (root / ".gitignore").write_text("input-dir/\n")
        sources = [ArtifactSource("release/inputs/raw.txt", ignored)]
        collections = [
            ClosedCollection(
                "release/inputs", closed_directory, ("release/inputs/raw.txt",)
            )
        ]
        ordinary_tree = git(root, "write-tree")
        worktree_status = git(root, "status", "--porcelain", "--untracked-files=all")

        git_store = WorkflowReleaseGitStore(root)
        git_manifest = git_store.capture_release(
            sources,
            closed_collections=collections,
            created_at="2026-08-17T00:00:00Z",
        )
        portable_root = Path(directory) / "portable"
        portable_manifest = PortableBundleStore().capture(
            sources,
            portable_root,
            domain="workflow-release",
            closed_collections=collections,
        )

        assert git_manifest["content_root"] == portable_manifest["content_root"]
        assert git_store.raw_artifacts(git_manifest)["release/inputs/raw.txt"] == b"raw-lf\n"
        assert PortableBundleStore().verify(portable_root)["verified"] is True
        assert git(root, "write-tree") == ordinary_tree
        assert git(root, "status", "--porcelain", "--untracked-files=all") == worktree_status
        ignored.write_bytes(b"changed\n")
        assert (
            git_store.compare_release_sources(
                git_manifest,
                sources,
                closed_collections=collections,
            )["verified"]
            is False
        )


def test_git_verifier_checks_object_format_and_parent_binding() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        initialize(root)
        source = root / "source.bin"
        source.write_bytes(b"source")
        store = WorkflowReleaseGitStore(root)
        manifest = store.capture_release(
            [ArtifactSource("release/source.bin", source)],
            created_at="2026-08-17T00:00:00Z",
        )
        wrong_format = copy.deepcopy(manifest)
        wrong_format["storage"]["object_format"] = "sha256"
        with pytest.raises(ProvenanceError, match="object format"):
            store.verify(wrong_format)
        wrong_parent = copy.deepcopy(manifest)
        wrong_parent["storage"]["parent_commit"] = manifest["storage"]["commit"]
        with pytest.raises(ProvenanceError, match="parent commit"):
            store.verify(wrong_parent)


def test_export_from_git_verifies_without_dot_git() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory) / "repo"
        root.mkdir()
        initialize(root)
        source = root / "untracked.bin"
        source.write_bytes(b"portable\x00bytes")
        git_store = WorkflowReleaseGitStore(root)
        manifest = git_store.capture_release(
            [ArtifactSource("release/artifact.bin", source)],
            created_at="2026-08-17T00:00:00Z",
        )
        destination = Path(directory) / "export"
        exported = PortableBundleStore().export_from_git(
            git_store, manifest, destination
        )

        assert exported["content_root"] == manifest["content_root"]
        assert not (destination / ".git").exists()
        assert PortableBundleStore().verify(destination)["verified"] is True


def test_portable_bundle_rejects_unexpected_member() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        source = root / "source.txt"
        source.write_text("value\n")
        destination = root / "bundle"
        store = ProjectPortableStore()
        store.capture(
            "decision",
            [ArtifactSource("project/decision/source.txt", source)],
            destination,
            project_root=root,
        )
        (destination / "extra.txt").write_text("unexpected\n")
        with pytest.raises(ProvenanceError, match="unexpected"):
            store.verify(destination, expected_role="decision")


def test_portable_bundle_rejects_external_manifest_symlink() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        source = root / "source.txt"
        source.write_text("value\n")
        bundle = root / "bundle"
        store = ProjectPortableStore()
        store.capture(
            "decision",
            [ArtifactSource("project/decision/source.txt", source)],
            bundle,
            project_root=root,
        )
        external = root / "external-manifest.json"
        (bundle / "manifest.json").replace(external)
        (bundle / "manifest.json").symlink_to(external)
        with pytest.raises(ProvenanceError, match="missing or unsafe"):
            store.verify(bundle, expected_role="decision")


def test_closed_collection_rejects_unlisted_directory_member() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        collection = root / "collection"
        collection.mkdir()
        selected = collection / "selected.txt"
        selected.write_text("selected\n")
        (collection / "extra.txt").write_text("extra\n")
        with pytest.raises(ProvenanceError, match="membership mismatch"):
            ProjectPortableStore().capture(
                "decision",
                [ArtifactSource("project/decision/inputs/selected.txt", selected)],
                root / "bundle",
                project_root=root,
                closed_collections=[
                    ClosedCollection(
                        "project/decision/inputs",
                        collection,
                        ("project/decision/inputs/selected.txt",),
                    )
                ],
            )


@pytest.mark.parametrize(
    "logical_name",
    (
        ".agents/skills/frontier/SKILL.md",
        "skills/frontier/SKILL.md",
        "validator_source.py",
        "project/decision/.agents/skills/frontier/SKILL.md",
        "project/decision/.claude/skills/frontier/SKILL.md",
        "project/decision/packages/service/.claude/agents/reviewer.md",
    ),
)
def test_project_capture_rejects_workflow_logical_names(logical_name: str) -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        source = root / "decision.txt"
        source.write_text("project decision\n")
        with pytest.raises(ProvenanceError):
            ProjectPortableStore().capture(
                "decision",
                [ArtifactSource(logical_name, source)],
                root / "bundle",
                project_root=root,
            )


def test_git_capture_rejects_project_domains() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        initialize(root)
        source = root / "decision.txt"
        source.write_text("project decision\n")
        with pytest.raises(ProvenanceError, match="reserved for workflow releases"):
            GitSnapshotStore(root).capture(
                [ArtifactSource("project/decision/decision.txt", source)],
                domain="project-decision",
                created_at="2026-08-17T00:00:00Z",
            )


def test_project_capture_allows_task_and_technology_names() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        skills = root / "skills"
        skills.mkdir()
        model = skills / "model.py"
        validator = root / "validator_source.py"
        model.write_text("MODEL = object()\n")
        validator.write_text("def validate(value): return value\n")
        result = ProjectPortableStore().capture(
            "state",
            [
                ArtifactSource("project/state/src/skills/model.py", model),
                ArtifactSource("project/state/src/validator_source.py", validator),
            ],
            root / "bundle",
            project_root=root,
        )
        assert result["domain"] == "project-state"


@pytest.mark.parametrize(
    "workflow_prefix",
    (
        (".agents", "skills"),
        (".codex", "skills"),
        (".claude", "skills"),
        (".claude", "commands"),
        (".claude", "agents"),
        ("packages", "service", ".claude", "skills"),
    ),
)
def test_project_capture_rejects_explicit_workflow_roots(
    workflow_prefix: tuple[str, ...],
) -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        workflow_root = root.joinpath(*workflow_prefix, "frontier")
        workflow_root.mkdir(parents=True)
        source = workflow_root / "module.py"
        source.write_text("WORKFLOW = True\n")
        with pytest.raises(ProvenanceError, match="cannot capture workflow source"):
            ProjectPortableStore().capture(
                "state",
                [ArtifactSource("project/state/src/module.py", source)],
                root / "bundle",
                project_root=root,
            )


def test_project_under_codex_ancestor_is_not_misclassified() -> None:
    with tempfile.TemporaryDirectory() as directory:
        project_root = Path(directory) / ".codex" / "worktrees" / "ordinary-project"
        project_root.mkdir(parents=True)
        source = project_root / "model.py"
        source.write_text("MODEL = object()\n")
        result = ProjectPortableStore().capture(
            "state",
            [ArtifactSource("project/state/model.py", source)],
            project_root / "bundle",
            project_root=project_root,
        )
        assert result["domain"] == "project-state"


def test_nonworkflow_claude_project_directory_is_allowed() -> None:
    with tempfile.TemporaryDirectory() as directory:
        project_root = Path(directory) / "project"
        source_root = project_root / ".claude" / "data"
        source_root.mkdir(parents=True)
        source = source_root / "model.json"
        source.write_text('{"model":"project-data"}\n')
        result = ProjectPortableStore().capture(
            "state",
            [ArtifactSource("project/state/.claude/data/model.json", source)],
            project_root / "bundle",
            project_root=project_root,
        )
        assert result["domain"] == "project-state"


def test_project_capture_rejects_sources_outside_project_root() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        project_root = root / "project"
        project_root.mkdir()
        source = root / "outside.txt"
        source.write_text("outside\n")
        with pytest.raises(ProvenanceError, match="outside project_root"):
            ProjectPortableStore().capture(
                "state",
                [ArtifactSource("project/state/outside.txt", source)],
                project_root / "bundle",
                project_root=project_root,
            )


def test_git_verify_rejects_a_project_domain_manifest() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        initialize(root)
        source = root / "release.txt"
        source.write_text("release\n")
        store = WorkflowReleaseGitStore(root)
        manifest = store.capture_release(
            [ArtifactSource("release/release.txt", source)],
            created_at="2026-08-17T00:00:00Z",
        )
        forged = copy.deepcopy(manifest)
        forged["domain"] = "project-decision"
        forged["artifacts"][0]["logical_name"] = "project/decision/input.txt"
        with pytest.raises(ProvenanceError, match="reserved for workflow releases"):
            store.verify(forged)


def test_project_consequence_resolver_rejects_git_bindings() -> None:
    with pytest.raises(ProvenanceError, match="portable project bundle"):
        cli_content_resolver(
            [
                {
                    "adapter": "git-snapshot/1",
                    "repo_root": "/unused",
                    "reference": "refs/frontier/release",
                    "manifest_path": "/unused/manifest.json",
                }
            ]
        )


def test_typed_chain_accepts_immediate_parents_and_live_facts() -> None:
    content_root = "frontier-content-root-sha256:" + "a" * 64
    _, _, _, outcome, nodes = chain(content_root)
    result = verify_for(
        outcome["node_id"],
        nodes.__getitem__,
        content_resolver,
        consequence="outcome-publication",
        live_facts={
            "authority_current": fact(content_root),
            "inputs_current": fact(content_root),
            "budget_accounted": fact(content_root),
            "prior_external_effects_known": fact(content_root),
        },
        checked_at="2026-08-17T01:00:00Z",
    )
    assert result["ready"] is True
    assert result["node_count"] == 5


def test_live_fact_failure_does_not_reinterpret_static_chain() -> None:
    content_root = "frontier-content-root-sha256:" + "b" * 64
    _, _, _, outcome, nodes = chain(content_root)
    result = verify_for(
        outcome["node_id"],
        nodes.__getitem__,
        content_resolver,
        consequence="outcome-publication",
        live_facts={
            "authority_current": fact(content_root),
            "inputs_current": fact(content_root),
            "budget_accounted": {},
            "prior_external_effects_known": fact(content_root),
        },
        checked_at="2026-08-17T01:00:00Z",
    )
    assert result["static_chain_verified"] is True
    assert result["ready"] is False
    assert result["unresolved_live_facts"] == ["budget_accounted"]


def test_live_attestation_requires_explicit_current_fact() -> None:
    content_root = "frontier-content-root-sha256:" + "2" * 64
    TEST_DOMAINS[content_root] = "live-receipt"
    decision_root = typed_root("project-decision", content_root)
    report_root = typed_root("review-report", content_root)
    decision = freeze_decision(decision_root=decision_root)
    validation = attest(
        decision,
        validation_report_root=report_root,
        verdict="ready",
        findings=[],
        freshness="live",
        observed_at="2026-08-17T00:00:00Z",
        expires_at="2026-08-18T00:00:00Z",
        invalidation_rule={"required_facts": ["inputs_current"]},
    )
    nodes = {node["node_id"]: node for node in (decision, validation)}
    result = verify_for(
        validation["node_id"],
        nodes.__getitem__,
        content_resolver,
        consequence="review",
        checked_at="2026-08-17T01:00:00Z",
    )
    assert result["ready"] is False
    assert result["unresolved_live_facts"] == [
        "inputs_current"
    ]


def test_live_attestation_cannot_authorize_before_its_observation() -> None:
    content_root = "frontier-content-root-sha256:" + "9" * 64
    TEST_DOMAINS[content_root] = "live-receipt"
    decision_root = typed_root("project-decision", content_root)
    report_root = typed_root("review-report", content_root)
    decision = freeze_decision(decision_root=decision_root)
    validation = attest(
        decision,
        validation_report_root=report_root,
        verdict="ready",
        findings=[],
        freshness="live",
        observed_at="2030-01-01T00:00:00Z",
        expires_at="2040-01-01T00:00:00Z",
        invalidation_rule={"required_facts": ["inputs_current"]},
    )
    nodes = {node["node_id"]: node for node in (decision, validation)}
    with pytest.raises(ProvenanceError, match="observation is in the future"):
        verify_for(
            validation["node_id"],
            nodes.__getitem__,
            content_resolver,
            consequence="review",
            live_facts={"inputs_current": fact(content_root)},
            checked_at="2026-08-17T01:00:00Z",
        )


def test_cross_decision_attestation_replay_fails() -> None:
    root_a = "frontier-content-root-sha256:" + "c" * 64
    root_b = "frontier-content-root-sha256:" + "d" * 64
    decision_a = freeze_decision(decision_root=root_a)
    decision_b = freeze_decision(decision_root=root_b)
    validation_a = attest(
        decision_a,
        validation_report_root=typed_root("review-report", root_a),
        verdict="ready",
        findings=[],
    )
    with pytest.raises(ProvenanceError, match="does not attest"):
        bind_authority(
            authority_root=typed_root("project-authority", root_b),
            decision=decision_b,
            validation=validation_a,
        )


def test_attestation_rejects_workflow_contract_and_blocking_ready_finding() -> None:
    content_root = "frontier-content-root-sha256:" + "3" * 64
    decision = freeze_decision(decision_root=content_root)
    with pytest.raises(ProvenanceError, match="unknown or missing fields"):
        build_node(
            "attestation",
            {
                "subject_root": decision["node_id"],
                "validator_contract": "frontier-test-validator/1",
                "verdict": "ready",
                "findings": [],
                "freshness": "immutable",
                "observed_at": None,
                "expires_at": None,
                "invalidation_rule": None,
            },
            parents=[{"edge": "subject", "node_id": decision["node_id"]}],
            artifact_roots=[typed_root("review-report", content_root)],
        )
    with pytest.raises(ProvenanceError, match="block or repair"):
        attest(
            decision,
            validation_report_root=typed_root("review-report", content_root),
            verdict="ready",
            findings=[{"effect": "block", "code": "NO"}],
        )


@pytest.mark.parametrize(
    ("operation_request", "removed_field"),
    [
        (
            {"operation": "freeze-decision", "decision_root": "unused"},
            "semantic_contract",
        ),
        (
            {
                "operation": "attest",
                "subject_id": "unused",
                "validation_report_root": "unused",
                "verdict": "ready",
                "findings": [],
                "freshness": "immutable",
                "observed_at": None,
                "expires_at": None,
                "invalidation_rule": None,
            },
            "validator_contract",
        ),
        (
            {
                "operation": "bind-authority",
                "authority_root": "unused",
                "decision_id": "unused",
                "attestation_id": "unused",
            },
            "authority_contract",
        ),
        (
            {
                "operation": "freeze-execution",
                "authority_id": "unused",
                "starting_state_root": "unused",
            },
            "execution_contract",
        ),
        (
            {
                "operation": "record-outcome",
                "execution_id": "unused",
                "outcome_root": "unused",
            },
            "outcome_contract",
        ),
    ],
)
def test_current_cli_rejects_workflow_contract_fields(
    operation_request: dict[str, object], removed_field: str
) -> None:
    with tempfile.TemporaryDirectory() as directory:
        request = {
            "contract_version": REQUEST_CONTRACT,
            **operation_request,
            removed_field: "frontier-workflow/1",
        }
        with pytest.raises(ProvenanceError, match="request fields must be exactly"):
            apply_operation(request, NodeRepository(Path(directory) / "nodes"))


def test_project_nodes_and_manifests_reject_embedded_workflow_bindings() -> None:
    root = typed_root("project-decision", "closed-payload")
    with pytest.raises(ProvenanceError, match="payload must be empty"):
        build_node(
            "decision",
            {
                "workflow_source_binding": {
                    "identity": "sha256:" + "a" * 64
                },
            },
            artifact_roots=[root],
        )
    with pytest.raises(
        ProvenanceError, match="metadata may contain only executable"
    ):
        authority_payload(
            [
                {
                    "logical_name": "project/decision/decision.json",
                    "kind": "blob",
                    "behavioral_metadata": {
                        "workflow_source_identity": "sha256:" + "a" * 64
                    },
                    "size": 1,
                    "content_sha256": "0" * 64,
                }
            ],
            domain="project-decision",
        )


def test_workflow_release_content_cannot_satisfy_a_project_role() -> None:
    release_root = typed_root("workflow-release", "release")
    decision = freeze_decision(decision_root=release_root)
    nodes = {decision["node_id"]: decision}
    with pytest.raises(ProvenanceError, match="project-decision domain"):
        verify_for(
            decision["node_id"],
            nodes.__getitem__,
            content_resolver,
            consequence="review",
        )


def test_verification_requires_real_content_and_consequence_facts() -> None:
    content_root = "frontier-content-root-sha256:" + "4" * 64
    decision, authority, _, _, nodes = chain(content_root)

    def missing(_: str) -> dict[str, object]:
        raise ProvenanceError("missing content")

    with pytest.raises(ProvenanceError, match="missing content"):
        verify_for(
            decision["node_id"], nodes.__getitem__, missing, consequence="review"
        )
    result = verify_for(
        authority["node_id"],
        nodes.__getitem__,
        content_resolver,
        consequence="spend",
        live_facts={},
        checked_at="2026-08-17T01:00:00Z",
    )
    assert result["ready"] is False
    assert "budget_current" in result["unresolved_live_facts"]
    with pytest.raises(ProvenanceError, match="unsupported consequence"):
        verify_for(
            authority["node_id"],
            nodes.__getitem__,
            content_resolver,
            consequence="custom",
        )


def test_manual_external_receipt_manifest_rejects_empty_semantics() -> None:
    with pytest.raises(ProvenanceError, match="external receipt metadata"):
        authority_payload(
            [
                {
                    "logical_name": "receipts/receipt.txt",
                    "kind": "external-receipt",
                    "behavioral_metadata": {
                        "fact": "",
                        "status": "pass",
                        "observed_at": "",
                        "expires_at": "",
                    },
                    "size": 1,
                    "content_sha256": "0" * 64,
                }
            ],
            domain="live-receipt",
        )


def test_expired_live_receipt_cannot_be_replayed_for_spend() -> None:
    content_root = "frontier-content-root-sha256:" + "5" * 64
    _, authority, _, _, nodes = chain(content_root)
    names = {
        "authority_current",
        "budget_current",
        "reservation_current",
        "inputs_current",
        "resources_available",
    }

    def expired(root: str) -> dict[str, object]:
        return {
            "content_root": root,
            "domain": TEST_DOMAINS[root],
            "verified": True,
            "receipt_facts": {
                name: {
                    "status": "pass",
                    "observed_at": "2020-01-01T00:00:00Z",
                    "expires_at": "2020-01-01T00:05:00Z",
                }
                for name in names
            },
        }

    result = verify_for(
        authority["node_id"],
        nodes.__getitem__,
        expired,
        consequence="spend",
        live_facts={name: fact(content_root) for name in names},
        checked_at="2026-08-17T00:00:00Z",
    )
    assert result["ready"] is False
    assert set(result["unresolved_live_facts"]) == names


def test_missing_parent_and_tampered_node_fail_closed() -> None:
    content_root = "frontier-content-root-sha256:" + "e" * 64
    _, _, _, outcome, nodes = chain(content_root)
    missing = dict(nodes)
    execution_parent = outcome["parents"][0]["node_id"]
    missing.pop(execution_parent)
    with pytest.raises(KeyError):
        verify_chain(outcome["node_id"], missing.__getitem__)

    tampered = copy.deepcopy(nodes)
    tampered[outcome["node_id"]]["payload"]["workflow_release"] = "changed"
    with pytest.raises(ProvenanceError, match="payload must be empty"):
        verify_chain(outcome["node_id"], tampered.__getitem__)


def test_v1_adapter_allows_completion_but_not_new_authority() -> None:
    inventory = {
        "contract_version": "frontier-v1-completion-inventory/1",
        "rollout_cutoff": "2026-08-17T00:00:00Z",
        "active_authorities": [
            {
                "state": "acknowledged",
                "authority_root": "legacy-authority",
                "contract_version": "frontier-dispatch-identity/2",
                "scope_root": "legacy-packet",
            }
        ],
    }
    require_v1_completion(
        inventory,
        authority_root="legacy-authority",
        requested_descendant="execution-start",
        scope_root="legacy-packet",
        verified_parent_role="acknowledgment",
    )
    with pytest.raises(ProvenanceError, match="only completion"):
        require_v1_completion(
            inventory,
            authority_root="legacy-authority",
            requested_descendant="authorization",
            scope_root="legacy-packet",
            verified_parent_role="authority",
        )


def test_source_modules_expand_dependencies_and_ignore_unrelated_files() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        (root / "common.txt").write_text("common\n")
        (root / "direction.txt").write_text("direction\n")
        (root / "unrelated.txt").write_text("one\n")
        manifest = {
            "contract_version": "frontier-source-modules/1",
            "modules": {
                "common": {"depends_on": [], "files": ["common.txt"]},
                "direction": {
                    "depends_on": ["common"],
                    "files": ["direction.txt"],
                },
            },
        }
        closure = validate_source_modules(manifest, root)
        assert closure["direction"] == {"common.txt", "direction.txt"}
        before = source_module_root(manifest, root, "direction")
        (root / "unrelated.txt").write_text("two\n")
        assert source_module_root(manifest, root, "direction") == before
        (root / "common.txt").write_text("changed\n")
        assert source_module_root(manifest, root, "direction") != before


def test_workflow_release_mutation_does_not_change_project_identity() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        project = root / "project.txt"
        workflow = root / "workflow.py"
        project.write_text("project-v1\n")
        workflow.write_text("workflow-v1\n")
        project_manifest = ProjectPortableStore().capture(
            "decision",
            [ArtifactSource("project/decision/project.txt", project)],
            root / "project-v1",
            project_root=root,
        )
        decision = freeze_decision(decision_root=project_manifest["content_root"])
        report_root = typed_root("review-report", "stable-report")
        authority_root = typed_root("project-authority", "stable-authority")
        validation = attest(
            decision,
            validation_report_root=report_root,
            verdict="ready",
            findings=[],
        )
        authority = bind_authority(
            authority_root=authority_root,
            decision=decision,
            validation=validation,
        )
        release_v1 = PortableBundleStore().capture(
            [ArtifactSource("release/workflow.py", workflow)],
            root / "release-v1",
            domain="workflow-release",
        )
        workflow.write_text("workflow-v2\n")
        release_v2 = PortableBundleStore().capture(
            [ArtifactSource("release/workflow.py", workflow)],
            root / "release-v2",
            domain="workflow-release",
        )
        same_decision = freeze_decision(
            decision_root=project_manifest["content_root"]
        )
        same_validation = attest(
            same_decision,
            validation_report_root=report_root,
            verdict="ready",
            findings=[],
        )
        same_authority = bind_authority(
            authority_root=authority_root,
            decision=same_decision,
            validation=same_validation,
        )
        assert release_v1["content_root"] != release_v2["content_root"]
        assert same_decision["node_id"] == decision["node_id"]
        assert same_validation["node_id"] == validation["node_id"]
        assert same_authority["node_id"] == authority["node_id"]
        assert release_v1["content_root"] not in decision["artifact_roots"]
        assert release_v2["content_root"] not in decision["artifact_roots"]


def test_project_byte_mutation_changes_project_root_and_node() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        project = root / "project.txt"
        project.write_text("project-v1\n")
        first = ProjectPortableStore().capture(
            "decision",
            [ArtifactSource("project/decision/project.txt", project)],
            root / "project-v1",
            project_root=root,
        )
        project.write_text("project-v2\n")
        second = ProjectPortableStore().capture(
            "decision",
            [ArtifactSource("project/decision/project.txt", project)],
            root / "project-v2",
            project_root=root,
        )
        first_node = freeze_decision(decision_root=first["content_root"])
        second_node = freeze_decision(decision_root=second["content_root"])
        assert first["content_root"] != second["content_root"]
        assert first_node["node_id"] != second_node["node_id"]


def test_source_module_audit_rejects_imported_but_unlisted_local_file() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        (root / "main.py").write_text("import helper\n")
        (root / "helper.py").write_text("VALUE = 1\n")
        manifest = {
            "contract_version": "frontier-source-modules/1",
            "modules": {
                "core": {"depends_on": [], "files": ["main.py"]},
            },
        }
        with pytest.raises(ProvenanceError, match="omits Python dependencies"):
            audit_python_dependencies(manifest, root)


def test_source_module_audit_ignores_same_stem_outside_import_path() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        (root / "main.py").write_text("import json\n")
        (root / "unrelated").mkdir()
        (root / "unrelated/json.py").write_text("VALUE = 1\n")
        manifest = {
            "contract_version": "frontier-source-modules/1",
            "modules": {
                "core": {"depends_on": [], "files": ["main.py"]},
            },
        }
        assert audit_python_dependencies(manifest, root)["core"] == {"main.py"}


def test_source_module_audit_resolves_package_and_relative_imports() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        (root / "package").mkdir()
        (root / "package/__init__.py").write_text("from . import helper\n")
        (root / "package/helper.py").write_text("VALUE = 1\n")
        manifest = {
            "contract_version": "frontier-source-modules/1",
            "modules": {
                "core": {"depends_on": [], "files": ["package/__init__.py"]},
            },
        }
        with pytest.raises(ProvenanceError, match="omits Python dependencies"):
            audit_python_dependencies(manifest, root)


def test_live_source_module_manifest_covers_existing_files() -> None:
    skill = Path(__file__).parent.parent
    skills_root = skill.parent
    manifest = yaml.safe_load(
        (skill / "references/source-modules.yaml").read_text()
    )
    closure = validate_source_modules(manifest, skills_root)
    assert {
        "graph-core",
        "storage-recovery",
        "provenance-runtime",
        "direction",
        "execution",
        "evidence",
        "claims",
        "legacy-validation",
    } == set(closure)
    assert all(source_module_root(manifest, skills_root, name) for name in closure)
    assert (
        "frontier-optimization/scripts/frontier_provenance/stores.py"
        not in closure["direction"]
    )
    assert (
        "frontier-optimization/scripts/validate_candidate_package.py"
        in closure["legacy-validation"]
    )


def test_node_repository_is_immutable_and_recomputes_loaded_identity() -> None:
    with tempfile.TemporaryDirectory() as directory:
        repository = NodeRepository(Path(directory))
        content_root = "frontier-content-root-sha256:" + "f" * 64
        decision = freeze_decision(decision_root=content_root)
        path = repository.write(decision)
        assert repository.load(decision["node_id"]) == decision
        tampered = json.loads(path.read_text())
        tampered["payload"]["workflow_release"] = "changed"
        path.write_text(json.dumps(tampered, sort_keys=True, separators=(",", ":")))
        with pytest.raises(ProvenanceError, match="payload must be empty"):
            repository.load(decision["node_id"])


def test_cli_facade_freezes_and_verifies_a_decision() -> None:
    with tempfile.TemporaryDirectory() as directory:
        repository = NodeRepository(Path(directory))
        source = Path(directory) / "decision.txt"
        source.write_text("one exact decision\n")
        bindings: list[dict[str, str]] = []
        roots: dict[str, str] = {}
        for domain in (
            "project-decision",
            "review-report",
            "project-authority",
            "project-state",
            "project-outcome",
        ):
            bundle = Path(directory) / domain
            captured = apply_operation(
                {
                    "contract_version": REQUEST_CONTRACT,
                    "operation": "capture-project",
                    "role": DOMAIN_ROLES[domain],
                    "project_root": str(Path(directory)),
                    "artifacts": [
                        {
                            "logical_name": DOMAIN_PREFIXES[domain] + "project-record.txt",
                            "path": str(source),
                            "kind": "blob",
                            "behavioral_metadata": {},
                        }
                    ],
                    "closed_collections": [],
                    "destination": str(bundle),
                },
                repository,
            )
            roots[domain] = captured["content_root"]
            bindings.append({"adapter": "portable-bundle/1", "path": str(bundle)})
        receipt_bundle = Path(directory) / "live-receipt"
        receipt = apply_operation(
            {
                "contract_version": REQUEST_CONTRACT,
                "operation": "capture-project",
                "role": "receipt",
                "project_root": str(Path(directory)),
                "artifacts": [
                    *[
                        {
                            "logical_name": f"receipts/{name}.txt",
                            "path": str(source),
                            "kind": "external-receipt",
                            "behavioral_metadata": {
                                "fact": name,
                                "status": "pass",
                                "observed_at": "2026-08-17T00:00:00Z",
                                "expires_at": "2026-08-17T02:00:00Z",
                            },
                        }
                        for name in (
                            "authority_current",
                            "inputs_current",
                            "budget_accounted",
                            "prior_external_effects_known",
                        )
                    ],
                ],
                "closed_collections": [],
                "destination": str(receipt_bundle),
            },
            repository,
        )
        bindings.append(
            {"adapter": "portable-bundle/1", "path": str(receipt_bundle)}
        )
        frozen = apply_operation(
            {
                "contract_version": REQUEST_CONTRACT,
                "operation": "freeze-decision",
                "decision_root": roots["project-decision"],
            },
            repository,
        )
        attestation = apply_operation(
            {
                "contract_version": REQUEST_CONTRACT,
                "operation": "attest",
                "subject_id": frozen["node_id"],
                "validation_report_root": roots["review-report"],
                "verdict": "ready",
                "findings": [],
                "freshness": "immutable",
                "observed_at": None,
                "expires_at": None,
                "invalidation_rule": None,
            },
            repository,
        )
        authority = apply_operation(
            {
                "contract_version": REQUEST_CONTRACT,
                "operation": "bind-authority",
                "authority_root": roots["project-authority"],
                "decision_id": frozen["node_id"],
                "attestation_id": attestation["node_id"],
            },
            repository,
        )
        execution = apply_operation(
            {
                "contract_version": REQUEST_CONTRACT,
                "operation": "freeze-execution",
                "authority_id": authority["node_id"],
                "starting_state_root": roots["project-state"],
            },
            repository,
        )
        outcome = apply_operation(
            {
                "contract_version": REQUEST_CONTRACT,
                "operation": "record-outcome",
                "execution_id": execution["node_id"],
                "outcome_root": roots["project-outcome"],
            },
            repository,
        )
        verified = apply_operation(
            {
                "contract_version": REQUEST_CONTRACT,
                "operation": "verify",
                "root_id": outcome["node_id"],
                "consequence": "outcome-publication",
                "live_facts": {
                    name: fact(receipt["content_root"])
                    for name in (
                        "authority_current",
                        "inputs_current",
                        "budget_accounted",
                        "prior_external_effects_known",
                    )
                },
                "checked_at": "2026-08-17T01:00:00Z",
                "content_bindings": bindings,
            },
            repository,
        )
        assert verified["ready"] is True
        assert verified["root_role"] == "outcome"
        exported = apply_operation(
            {
                "contract_version": REQUEST_CONTRACT,
                "operation": "export",
                "root_id": outcome["node_id"],
            },
            repository,
        )
        serialized = json.dumps(exported, sort_keys=True)
        assert "workflow_source" not in serialized
        assert "source_roots" not in serialized
        assert "validator_source" not in serialized


def test_complete_handoff_verifies_offline_from_outcome_root() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        source = root / "artifact.txt"
        source.write_text("artifact\n")
        outcome, nodes, exporters = portable_project_chain(root, source)
        repository = NodeRepository(root / "nodes")
        repository.write_all(nodes.values())

        handoff = root / "handoff"
        export_handoff(
            outcome["node_id"],
            repository,
            exporters,
            handoff,
        )
        assert not (handoff / ".git").exists()
        assert verify_handoff(handoff)["verified"] is True
        manifest = json.loads((handoff / "handoff.json").read_text())
        domains = {
            json.loads(
                (handoff / item["path"] / "manifest.json").read_text()
            )["domain"]
            for item in manifest["content"]
        }
        assert "workflow-release" not in domains


def test_handoff_rejects_external_manifest_symlink() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        source = root / "artifact.txt"
        source.write_text("artifact\n")
        outcome, nodes, exporters = portable_project_chain(root, source)
        repository = NodeRepository(root / "nodes")
        repository.write_all(nodes.values())

        handoff = root / "handoff"
        export_handoff(
            outcome["node_id"],
            repository,
            exporters,
            handoff,
        )
        external = root / "external-handoff.json"
        (handoff / "handoff.json").replace(external)
        (handoff / "handoff.json").symlink_to(external)
        with pytest.raises(ProvenanceError, match="missing or unsafe"):
            verify_handoff(handoff)


def test_rollout_closes_legacy_entry_packet_and_authority_writers() -> None:
    scripts = Path(__file__).parent
    repo_root = scripts.parents[3]
    assert (repo_root / ".frontier/provenance-rollout.yaml").is_file()
    commands = [
        [
            str(scripts / "validate_entry_packet.py"),
            "missing.yaml",
            "--phase",
            "draft",
            "--root",
            str(repo_root),
        ],
        [
            str(scripts / "validate_batch_packet.py"),
            "missing.yaml",
            "--phase",
            "draft",
            "--repo-root",
            str(repo_root),
        ],
        [
            str(scripts / "validate_authorization_adoption.py"),
            "missing.yaml",
            "--phase",
            "draft",
            "--root",
            str(repo_root),
        ],
    ]
    for command in commands:
        result = subprocess.run(
            [str(Path(sys.executable)), *command],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        assert result.returncode == 2
        assert b"legacy" in result.stderr
