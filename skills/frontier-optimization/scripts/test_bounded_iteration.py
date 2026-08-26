"""Focused behavior tests for bounded observations and delegated design edits."""

import copy
import hashlib
import json
from pathlib import Path

import pytest
import yaml

from evaluation_target_contract import validate_evaluation_target_contract, validate_working_observations
from frontier_provenance import attest, freeze_decision, ProvenanceError
from frontier_provenance.facade import validate_design_revision
from frontier_provenance.stores import ArtifactSource, ProjectPortableStore, PortableBundleStore
from frontier_review import prepare_review, PREPARATION_CONTRACT
from test_git_project_content import checkpoint, git
from test_validate_batch_result import diagnostic_evaluation_target, base_result, base_packet
from validate_batch_result import validate_evaluation_boundary, validate_materialization_boundary, validate_packet_result_contract


def working_target():
    target = diagnostic_evaluation_target()
    target.pop("candidate")
    target.pop("exception_evidence")
    target["working_scope"] = {
        "question": "Does the proposed mechanism change the limiting observation?",
        "subjects": ["working-realization"],
        "methods": ["bounded-comparison"],
        "resources": {"units": 3},
        "exposure": {"development_samples": 2},
    }
    return target


def observation(identity="revision-a"):
    return {
        "subject": {"scope": "working-realization", "identity": identity},
        "method": "bounded-comparison",
        "conditions": "fixed comparison conditions",
        "observation": {"difference": 1},
        "evidence": {"path": "observations/raw.json", "file_sha256": "a" * 64},
        "consumption": {"resources": {"units": 1}, "exposure": {"development_samples": 1}},
        "maximum_consequence": "B evidence only",
    }


def test_working_diagnostics_do_not_require_a_published_candidate():
    target = working_target()
    findings = []
    validate_evaluation_target_contract(target, findings)
    validate_working_observations(target, [observation(), observation("revision-b")], findings)
    assert findings == []
    packet = base_packet()
    packet["evaluation_target"] = target
    assert validate_packet_result_contract(packet)["result_contract_ready"]
    result = base_result()
    result.update(evaluation_target=target, results=[observation()], performance_evaluation_state="diagnostic-only")
    validate_materialization_boundary(result, findings)
    validate_evaluation_boundary(result, packet, findings)
    assert findings == []


@pytest.mark.parametrize("mutation,expected", [
    (lambda target, results: results.append(observation()), "DIAGNOSTIC_LIMIT_EXCEEDED"),
    (lambda target, results: results[0]["subject"].update(scope="unapproved"), "DIAGNOSTIC_SUBJECT_OUTSIDE_SCOPE"),
    (lambda target, results: results[0].update(method="unapproved"), "DIAGNOSTIC_METHOD_OUTSIDE_SCOPE"),
    (lambda target, results: results[0]["consumption"]["resources"].update(units=-1), "DIAGNOSTIC_CONSUMPTION_INVALID"),
    (lambda target, results: results[0].pop("evidence"), "EVALUATION_TARGET_SCHEMA_INVALID"),
])
def test_working_observation_limits(mutation, expected):
    target = working_target()
    results = [observation(), observation("revision-b")]
    mutation(target, results)
    findings = []
    validate_working_observations(target, results, findings)
    assert expected in {item["code"] for item in findings}


def test_working_diagnostic_cannot_change_packet_or_claim_strength():
    target = working_target()
    packet = base_packet()
    packet["evaluation_target"] = copy.deepcopy(target)
    result = base_result()
    result.update(evaluation_target=target, results=[observation()], performance_evaluation_state="diagnostic-only")
    target["working_scope"]["methods"].append("extra")
    result["results"][0]["strength_claim"] = "improved"
    findings = []
    validate_evaluation_boundary(result, packet, findings)
    assert {"EVALUATION_TARGET_BINDING_MISMATCH", "DIAGNOSTIC_RESULT_CLAIM_PRESENT"} <= {item["code"] for item in findings}


def _design(root: Path, method: str, *, delivery="unchanged"):
    root.mkdir()
    design = root / "design"
    design.mkdir()
    (root / "problem.md").write_text("# Fixed objective\n")
    source = b"source: fixed\n"
    source_id = "source-sha256:" + hashlib.sha256(source).hexdigest()
    (design / "source-base.yaml").write_bytes(f"source_base_id: {source_id}\n".encode() + source)
    concern = f"# Mechanism\n{method}\n".encode()
    trace = b"slices:\n  whole:\n    delivery_identity: unchanged\n"
    index = {
        "work_id": "W900", "problem_epoch": 1, "representation_revision": 1,
        "route": "T900", "delivery": {"whole": delivery},
        "concerns_normalized": {"method.md": hashlib.sha256(concern).hexdigest()},
        "supporting_inputs": {"source-base.yaml": source_id, "traceability.yaml.normalized": hashlib.sha256(trace).hexdigest()},
    }
    index_raw = yaml.safe_dump(index).encode()
    identity = "W900-design-sha256:" + hashlib.sha256(index_raw).hexdigest()
    (design / "index.yaml").write_bytes(f"design_contract_id: {identity}\n".encode() + index_raw)
    (design / "method.md").write_bytes(f"design_contract_identity: {identity}\n".encode() + concern)
    (design / "traceability.yaml").write_bytes(f"design_contract_identity: {identity}\n".encode() + trace)
    names = ["index.yaml", "source-base.yaml", "method.md", "traceability.yaml"]
    artifacts = [{"logical_name": "project/decision/parents/problem.md", "path": "problem.md", "kind": "blob", "behavioral_metadata": {}}]
    artifacts += [{"logical_name": f"project/decision/design/W900/{name}", "path": f"design/{name}", "kind": "blob", "behavioral_metadata": {}} for name in names]
    checkpoint(root)
    result = prepare_review({
        "contract_version": PREPARATION_CONTRACT, "review_kind": "design", "artifacts": artifacts,
        "closed_collections": [{"logical_name": "project/decision/design/W900", "directory": "design", "members": [f"project/decision/design/W900/{name}" for name in names]}],
        "semantic_projection": {},
    }, root, root / "sealed")
    assert result["status"] == "SEALED", result
    # Use the real Git-backed subject, not a hand-written semantic projection.
    bundle = next(path.parent for path in (root / "sealed").rglob("manifest.json") if json.loads(path.read_text())["domain"] == "project-decision")
    return bundle


def revision_fixture(tmp_path, *, delivery="unchanged", verdict="ready"):
    git(tmp_path, "init", "-q")
    store = ProjectPortableStore()
    base = _design(tmp_path / "base", "initial mechanism")
    revised = _design(tmp_path / "revised", "revised mechanism", delivery=delivery)
    report = tmp_path / "report.md"
    report.write_text("Technical review only.\n")
    checkpoint(tmp_path)
    review_bundle = tmp_path / "review"
    store.capture("review", [ArtifactSource("project/review/report.md", report)], review_bundle, project_root=tmp_path)
    new_content = store.verify(revised)
    assert new_content["adapter"] == "git-reference/1"
    decision = freeze_decision(decision_root=new_content["content_root"])
    review = attest(decision, validation_report_root=store.verify(review_bundle)["content_root"], verdict=verdict, findings=[])
    prefix = "project/state/design-revision/"
    state = {prefix + "decision.json": json.dumps(decision).encode(), prefix + "attestation.json": json.dumps(review).encode()}
    for role, bundle in (("base", base), ("revised", revised), ("review", review_bundle)):
        state[prefix + role + "/manifest.json"] = (bundle / "manifest.json").read_bytes()
        state.update({prefix + role + "/" + name: raw for name, raw in PortableBundleStore().read_artifacts(bundle).items()})
    paths = {name: "design/" + name.rsplit("/", 1)[-1] for name in PortableBundleStore().read_artifacts(base) if name.startswith("project/decision/design/")}
    scope = {"base_design_content_root": store.verify(base)["content_root"], "mutable_concerns": ["project/decision/design/W900/method.md"], "design_input_paths": paths}
    scope["base_input_identities"] = {paths[name]: "sha256:" + hashlib.sha256(raw).hexdigest() for name, raw in PortableBundleStore().read_artifacts(base).items() if name in paths}
    return {"design_revision_scope": scope}, state


@pytest.mark.parametrize("field", ["subjects", "methods"])
def test_malformed_working_scope_reports_findings_instead_of_crashing(field):
    target = working_target()
    target["working_scope"][field] = None
    findings = []
    validate_evaluation_target_contract(target, findings)
    validate_working_observations(target, [observation()], findings)
    assert findings


@pytest.mark.parametrize("defect", ["base-input", "review-subject", "immutable-review"])
def test_design_revision_rejects_wrong_base_or_review(tmp_path, defect):
    from frontier_provenance.graph import build_node
    projection, state = revision_fixture(tmp_path)
    if defect == "base-input":
        projection["design_revision_scope"]["base_input_identities"]["design/method.md"] = "sha256:" + "0" * 64
    else:
        key = "project/state/design-revision/attestation.json"
        review = json.loads(state[key])
        if defect == "review-subject":
            review["payload"]["subject_root"] = "frontier-decision-root-sha256:" + "0" * 64
        else:
            review["payload"]["expires_at"] = "2026-09-01T00:00:00Z"
        review = build_node("attestation", review["payload"], parents=review["parents"], artifact_roots=review["artifact_roots"])
        state[key] = json.dumps(review).encode()
    with pytest.raises(ProvenanceError):
        validate_design_revision(projection, state)


def test_reviewed_design_revision_uses_original_delegation(tmp_path):
    projection, state = revision_fixture(tmp_path)
    changes = validate_design_revision(projection, state)
    assert set(changes) == {"design/index.yaml", "design/method.md", "design/traceability.yaml"}
    with pytest.raises(ProvenanceError, match="did not delegate"):
        validate_design_revision({}, state)


@pytest.mark.parametrize("delivery,verdict", [("changed", "ready"), ("unchanged", "repair")])
def test_design_revision_keeps_delivery_and_readiness_boundaries(tmp_path, delivery, verdict):
    projection, state = revision_fixture(tmp_path, delivery=delivery, verdict=verdict)
    with pytest.raises(ProvenanceError):
        validate_design_revision(projection, state)


def test_design_revision_rejects_changed_proof_bytes(tmp_path):
    projection, state = revision_fixture(tmp_path)
    state["project/state/design-revision/revised/project/decision/design/W900/method.md"] += b"changed after review\n"
    with pytest.raises(ProvenanceError, match="bytes changed"):
        validate_design_revision(projection, state)


def test_same_authority_new_state_validates_without_new_entry(tmp_path):
    from frontier_provenance import NodeRepository, freeze_execution
    from test_validate_batch_result import write_project_dispatch_fixture, write_line_identified_yaml, file_binding, file_sha256
    from validate_batch_result import validate

    design_root = tmp_path / "design-proof"
    design_root.mkdir()
    projection, proof = revision_fixture(design_root)
    root = tmp_path / "project"
    root.mkdir()
    packet, result, _ = write_project_dispatch_fixture(root, "current", design_revision=(projection, proof))
    original_plan = (root / result["batch_plan"]["path"]).read_bytes()
    original_start = yaml.safe_load((root / result["execution_start"]["path"]).read_text())
    original_bundle = root / packet["execution_baseline_root"]
    original_manifest = (original_bundle / "manifest.json").read_bytes()
    original_state = PortableBundleStore().read_artifacts(original_bundle)
    current = dict(original_state)
    current.update(proof)
    changes = validate_design_revision(projection, proof)
    state = yaml.safe_load(current["project/state/execution-state.yaml"])
    for item in state["execution_frozen_inputs"]:
        if item["path"] in changes:
            item["identity"] = changes[item["path"]]
    paths = projection["design_revision_scope"]["design_input_paths"]
    for name, relative in paths.items():
        new_raw = proof["project/state/design-revision/revised/" + name]
        (root / relative).write_bytes(new_raw)
        current["project/state/frozen-inputs/" + relative] = new_raw
    current["project/state/execution-state.yaml"] = yaml.safe_dump(state).encode()
    sources = []
    for name, raw in current.items():
        if name.startswith("project/state/frozen-inputs/"):
            path = root / name.removeprefix("project/state/frozen-inputs/")
        else:
            path = root / "state-draft" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        sources.append(ArtifactSource(name, path))
    new_bundle = root / "artifacts/frontier/B001/revised-baseline"
    git(root, "init", "-q")
    checkpoint(root)
    content = ProjectPortableStore().capture("state", sources, new_bundle, project_root=root)
    repository = NodeRepository(root / "artifacts/frontier/B001/entry-R900-complete/nodes")
    authority = repository.load(original_start["authority_id"])
    execution = freeze_execution(authority=authority, starting_state_root=content["content_root"])
    repository.write(execution)
    verification = root / "revised-verification.json"
    verification.write_text(json.dumps({"ready": True, "unresolved_live_facts": [], "static_chain_verified": True, "root_id": execution["node_id"], "consequence": "execution"}))
    start = dict(original_start)
    start.pop("execution_start_id")
    start.update(execution_node=execution["node_id"], starting_state_root=content["content_root"], starting_state_path=new_bundle.relative_to(root).as_posix())
    start["execution_verification"] = {"path": verification.relative_to(root).as_posix(), "file_sha256": file_sha256(verification), "ready": True, "unresolved_live_facts": []}
    start_path = root / "revised-start.yaml"
    start = write_line_identified_yaml(start_path, start, "execution_start_id", "B001-execution-start-sha256:")
    result["execution_start"] = file_binding(start_path, root, "execution_start_id", start["execution_start_id"])
    checked = validate(result, "draft", packet, repo_root=root)
    assert checked["result_structure_ready"], checked
    assert start["authority_id"] == original_start["authority_id"]
    assert (root / result["batch_plan"]["path"]).read_bytes() == original_plan
    assert (original_bundle / "manifest.json").read_bytes() == original_manifest

    (root / "project/input.txt").write_text("unrelated protected input drift\n")
    assert not validate(result, "draft", packet, repo_root=root)["result_structure_ready"]


def test_current_working_observation_verifies_raw_evidence(tmp_path):
    from test_validate_batch_result import write_project_dispatch_fixture
    from validate_batch_result import validate

    packet, result, _ = write_project_dispatch_fixture(tmp_path, "current", diagnostic_target=working_target())
    evidence = tmp_path / "observations/raw.json"
    evidence.parent.mkdir()
    evidence.write_text('{"difference": 1}\n')
    observed = observation()
    observed["evidence"]["file_sha256"] = hashlib.sha256(evidence.read_bytes()).hexdigest()
    result.update(evaluation_target=packet["evaluation_target"], results=[observed], performance_evaluation_state="diagnostic-only")
    checked = validate(result, "draft", packet, repo_root=tmp_path)
    assert checked["result_structure_ready"], checked
    evidence.write_text('{"difference": 99}\n')
    checked = validate(result, "draft", packet, repo_root=tmp_path)
    assert not checked["result_structure_ready"]
    assert "EVALUATION_TARGET_SOURCE_UNVERIFIED" in {item["code"] for item in checked["findings"]}
