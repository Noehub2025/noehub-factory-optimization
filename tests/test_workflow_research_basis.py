"""Verify research material through the maintained task entry in isolated roots.

These tests check delivery, source identity and recovery. They do not certify
research judgment, adoption by an Agent, or improvement of a project outcome.
"""

import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
ENTRY = ROOT / "scripts/workflow_task.py"
REFERENCES = ROOT / "skills/frontier-optimization/scripts/frontier_references.py"
spec = importlib.util.spec_from_file_location("research_workflow_task", ENTRY)
entry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(entry)

from context_delivery import digest, read_retained
from frontier_references import (
    _selected_text,
    check_decision_material,
    decision_material_identity,
)
from identity_bindings import canonical_json, sha256_bytes
from research_basis import basis_digest, select_basis


def write_json(root, path, value):
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    return target


def setup_owner(root, *, owner_path="owner.json", discovery=None, account=None):
    write_json(root, "entry.json", {"receiver": "current_codex"})
    (root / "assignment.md").write_text("Compare the next useful commitments; do not execute them.")
    owner = {
        "current_state": {"campaign_status": "running"},
        "execution_entry": {"configuration": "entry.json"},
        "governing_condition": "Use the existing resource window; do not infer further authority.",
    }
    if discovery is not None:
        owner["decision_material"] = {"discovery": discovery}
    if account is not None:
        owner.update(account)
    write_json(root, owner_path, owner)
    return owner


def current(root, owner="owner.json", invocation="first", event="direction", assignment="assignment.md"):
    result = entry.current(root, owner, assignment, invocation, event)
    directory = entry.direction_owner._location(root, invocation)
    prepared = json.loads((directory / "prepared.json").read_text())
    assert result["request"] == (directory / "request.txt").read_text()
    assert digest(result["request"]) == result["receipt"]["request"]["sha256"]
    assert result["receipt"]["status"] == "material_ready"
    assert "answer" not in result
    return result, prepared


def exact_source(root, prepared, path, commit=None):
    source = next(item for item in prepared["sources"]
                  if item["source"] == {"path": path, **({"commit": commit} if commit else {})})
    retained = read_retained(root, source["retrieval"])
    assert digest(retained) == source["sha256"]
    return retained


def git(root, *arguments):
    result = subprocess.run(["git", "-C", str(root), *arguments], text=True,
                            capture_output=True, check=True)
    return result.stdout.strip()


def references_cli(root, operation, *arguments):
    return subprocess.run([sys.executable, str(REFERENCES), operation,
                           "--repo", str(root), *map(str, arguments)],
                          capture_output=True, text=True)


@pytest.mark.parametrize("event", ["direction", "scope"])
def test_discovery_resolves_each_existing_selector_convention_without_caller_sources(tmp_path, event):
    owner_path = "teams/research/owner.json"
    setup_owner(tmp_path, owner_path=owner_path, discovery=[
        {"path": "arrangement.json", "field": "discovery"}, "arrangement.md#discovery",
    ])
    correct_json = write_json(tmp_path, "arrangement.json", {
        "discovery": "Inspect the untested operating condition before the next resource allocation.",
        "history": "This field is outside the selected passage.",
    })
    write_json(tmp_path, "teams/research/arrangement.json", {"discovery": "WRONG object path."})
    (tmp_path / "arrangement.md").write_text("## Discovery\nWRONG string path.\n")
    correct_markdown = tmp_path / "teams/research/arrangement.md"
    correct_markdown.write_text("## Discovery\nCompare the remaining measurement opportunity at resumption.\n")
    result, prepared = current(tmp_path, owner_path, event=event)
    sources = prepared["decision_material"]["discovery"]
    assert [item["source"] for item in sources] == [
        {"path": "arrangement.json", "field": "discovery"},
        {"path": "teams/research/arrangement.md", "section": "discovery"},
    ]
    for material, actual in zip(sources, [correct_json, correct_markdown]):
        expected = _selected_text(actual.read_text(), material["source"])
        assert material["material_state"] == {"availability": "available", "sha256": digest(expected)}
        assert expected in result["request"]
        assert exact_source(tmp_path, prepared, material["source"]["path"]) == actual.read_text()
    assert "WRONG object path" not in result["request"]
    assert "WRONG string path" not in result["request"]


@pytest.mark.parametrize("change", ["passage", "removed"])
def test_prepared_discovery_detects_changed_passage_and_availability(tmp_path, change):
    setup_owner(tmp_path, discovery=[{"path": "arrangement.json", "field": "discovery"}])
    path = write_json(tmp_path, "arrangement.json", {"discovery": "Investigate before the next commitment."})
    _, prepared = current(tmp_path)
    if change == "passage":
        write_json(tmp_path, "arrangement.json", {"discovery": "The opportunity has ended; preserve why."})
    else:
        path.unlink()
    with pytest.raises((ValueError, OSError)):
        entry.consume_request(tmp_path, prepared)
    recovered = entry.recover(tmp_path, "first")
    assert recovered["applicability"] == "requires_owner_reconciliation"
    assert recovered["replayed"] is False


def test_previously_missing_discovery_is_visible_and_new_availability_invalidates_prepared_use(tmp_path):
    setup_owner(tmp_path, discovery=[{"path": "arrangement.json", "field": "discovery"}])
    _, prepared = current(tmp_path)
    material = prepared["decision_material"]["discovery"][0]
    assert material["source"] == {"path": "arrangement.json", "field": "discovery"}
    assert material["material_state"]["availability"] == "source_unavailable"
    write_json(tmp_path, "arrangement.json", {"discovery": "The owner has now arranged a bounded inquiry."})
    with pytest.raises(ValueError):
        entry.consume_request(tmp_path, prepared)


def test_unchanged_selected_discovery_reuses_material_identity_but_refreshes_carrier(tmp_path):
    setup_owner(tmp_path, discovery=[{"path": "arrangement.json", "field": "discovery"}])
    write_json(tmp_path, "arrangement.json", {"discovery": "Inspect before allocation.", "history": 1})
    _, before = current(tmp_path)
    write_json(tmp_path, "arrangement.json", {"discovery": "Inspect before allocation.", "history": 2})
    check_decision_material(tmp_path, before)
    with pytest.raises(ValueError):
        entry.consume_request(tmp_path, before)
    _, after = current(tmp_path, invocation="second")
    assert decision_material_identity(before) == decision_material_identity(after)
    assert before["delivery_identity"] != after["delivery_identity"]


def test_discovery_rejects_historical_selector_while_original_evidence_keeps_its_revision(tmp_path):
    setup_owner(tmp_path)
    write_json(tmp_path, "arrangement.json", {"discovery": "Original arrangement."})
    git(tmp_path, "init", "-q")
    git(tmp_path, "add", ".")
    git(tmp_path, "-c", "user.name=Workflow Test", "-c", "user.email=workflow@example.invalid",
        "commit", "-qm", "Initial evidence")
    revision = git(tmp_path, "rev-parse", "HEAD")
    historical = {"path": "arrangement.json", "field": "discovery", "commit": revision}
    owner = setup_owner(tmp_path, discovery=[historical])
    write_json(tmp_path, "arrangement.json", {"discovery": "Current arrangement."})
    with pytest.raises(ValueError, match="(?i)discovery.*commit|commit.*discovery|current.*discovery|discovery.*current"):
        current(tmp_path)
    assert not entry.direction_owner._location(tmp_path, "first").exists()
    owner["decision_material"] = {"evidence": [historical]}
    write_json(tmp_path, "owner.json", owner)
    result, prepared = current(tmp_path)
    assert prepared["decision_material"]["evidence"][0]["source"] == historical
    assert "Original arrangement." in result["request"]
    assert "Current arrangement." not in result["request"]
    assert "Original arrangement." in exact_source(tmp_path, prepared, "arrangement.json", revision)


def test_historical_recovery_preserves_old_basis_and_fresh_current_receives_new_arrangement(tmp_path):
    setup_owner(tmp_path, discovery=[{"path": "arrangement.json", "field": "discovery"}])
    write_json(tmp_path, "arrangement.json", {"discovery": "Compare the operating conditions next."})
    original, _ = current(tmp_path)
    old_directory = entry.direction_owner._location(tmp_path, "first")
    old_prepared = (old_directory / "prepared.json").read_bytes()
    old_request = (old_directory / "request.txt").read_bytes()
    write_json(tmp_path, "arrangement.json", {"discovery": "The new observation makes the opportunity window decisive."})
    historical = entry.recover(tmp_path, "first")
    assert historical["receipt"] == original["receipt"]
    assert historical["applicability"] == "requires_owner_reconciliation"
    assert historical["replayed"] is False
    assert (old_directory / "prepared.json").read_bytes() == old_prepared
    assert (old_directory / "request.txt").read_bytes() == old_request
    resumed, _ = current(tmp_path, invocation="resumed", event="scope")
    assert "The new observation makes the opportunity window decisive." in resumed["request"]
    assert resumed["receipt"]["request"]["sha256"] != original["receipt"]["request"]["sha256"]
    assert "answer" not in resumed


def test_ordinary_prose_account_and_unchanged_continuation_remain_supported(tmp_path):
    prose = "The observation supports a bounded next comparison; alternative explanations remain open."
    (tmp_path / "understanding.md").write_text(prose)
    setup_owner(tmp_path, account={"context_account": {
        "source": {"path": "understanding.md"}, "sha256": digest(prose),
    }})
    first, prepared = current(tmp_path, event="continuation")
    second, _ = current(tmp_path, invocation="unchanged", event="continuation")
    assert prepared["current_account"]["adoption"] == "owner_associated"
    assert first["request"] == second["request"]
    assert prose in first["request"]
    assert exact_source(tmp_path, prepared, "understanding.md") == prose


def research_case(root, *, owner_is_assignment=False, with_result=False):
    """Use cycles and contrary evidence to expose projection shortcuts."""
    def item(identity, text, links=(), sources=()):
        return {"id": identity, "kind": "hypothesis", "text": text,
                "conditions": f"Qualification retained for {identity}.",
                "sources": list(sources), "links": [
                    {"relation": relation, "target": target} for relation, target in links]}

    evidence = write_json(root, "observation.json", {"result": "The components were changed together."})
    selected_evidence = _selected_text(evidence.read_text(), {"field": "result"})
    basis = {"schema": 1, "overview": "The operating condition and the proposed interaction remain distinct explanations.",
             "items": [
                 item("mechanism", "The interaction is the selected mechanism.",
                      [("depends_on", "foundation"), ("supports", "support")],
                      [{"path": "observation.json", "field": "result", "sha256": digest(selected_evidence)}]),
                 item("foundation", "The original observation does not isolate either contribution.",
                      [("depends_on", "mechanism")]),
                 item("support", "This observation provides conditional support.", [("supports", "distant")]),
                 item("contrary", "The reverse edge must preserve this competing explanation.",
                      [("challenges", "mechanism"), ("depends_on", "contrary-basis")]),
                 item("contrary-basis", "The competing explanation depends on a distinct condition."),
                 item("distant", "A second associative hop must not expand the selected view."),
                 item("unrelated", "UNRELATED_ACCOUNT_PAYLOAD " + "long unrelated account text " * 1000),
             ]}
    owner = setup_owner(root, account={
        "research_basis": basis,
        "context_account": {"source": {"path": "owner.json", "field": "research_basis"},
                            "sha256": basis_digest(basis)},
        "objective_basis": {"evaluation_source": {"path": "owner.json", "field": "research_basis"}},
    })
    use = {"owner": "owner.json", "items": ["mechanism"]}
    assignment = "assignment.json"
    if owner_is_assignment:
        owner["research_use"] = use
        assignment = "owner.json"
    else:
        write_json(root, assignment, {"purpose": "Design the discriminating comparison.", "research_use": use})
    if with_result:
        owner["current_state"]["work_record"] = "work.json"
        write_json(root, "work.json", {"batch": "B100", "definition": {"objective": "Inspect a new condition."},
            "current": {"status": "completed"}, "attempts": [{"attempt": "A1", "status": "completed",
            "result": {"finding": "A previously unclassified observation changes a live premise."}}]})
    write_json(root, "owner.json", owner)
    return owner, assignment


@pytest.mark.parametrize("owner_is_assignment", [False, True])
def test_design_receives_one_selected_projection_without_owner_or_incoming_fallback(tmp_path, owner_is_assignment):
    owner, assignment = research_case(tmp_path, owner_is_assignment=owner_is_assignment)
    result, prepared = current(tmp_path, event="design", assignment=assignment)
    account = prepared["current_account"]
    view = account["research_view"]
    expected = select_basis(owner["research_basis"], ["mechanism"])
    assert view["sha256"] == expected["sha256"]
    assert view["included_ids"] == ["contrary", "contrary-basis", "foundation", "mechanism", "support"]
    assert account["sha256"] == basis_digest(owner["research_basis"])
    assert account["research_render"]["complete"] is True
    assert "UNRELATED_ACCOUNT_PAYLOAD" not in result["request"]
    assert "A second associative hop must not expand the selected view." not in result["request"]
    for item in expected["items"]:
        assert result["request"].count(item["text"]) == 1
        assert result["request"].count(item["conditions"]) == 1
    assert owner["governing_condition"] in result["request"]
    full_owner = exact_source(tmp_path, prepared, "owner.json")
    assert json.loads(full_owner) == owner
    assert "UNRELATED_ACCOUNT_PAYLOAD" in full_owner
    assert prepared["selected_sources"]["evaluation_source"]["source"] == {
        "path": "owner.json", "field": "research_basis"}
    if owner_is_assignment:
        assert any(item.get("source", {}).get("path") == "owner.json"
                   for item in prepared["incoming_assignments"])


def test_direction_keeps_the_current_overview_beyond_a_narrow_consumer_declaration(tmp_path):
    owner, assignment = research_case(tmp_path)
    _, prepared = current(tmp_path, event="direction", assignment=assignment)
    view = prepared["current_account"]["research_view"]
    assert set(view["included_ids"]) == {item["id"] for item in owner["research_basis"]["items"]}
    rendered = prepared["current_account"]["research_render"]
    assert rendered["complete"] is False
    assert "unrelated" in rendered["omitted_ids"]
    assert json.loads(exact_source(tmp_path, prepared, "owner.json"))["research_basis"] == owner["research_basis"]


def test_selected_source_change_invalidates_only_the_prepared_use_and_preserves_receipt(tmp_path):
    _, assignment = research_case(tmp_path)
    original, prepared = current(tmp_path, event="design", assignment=assignment)
    captured = exact_source(tmp_path, prepared, "observation.json")
    write_json(tmp_path, "observation.json", {"result": "The new comparison separates the components."})
    with pytest.raises(ValueError):
        entry.consume_request(tmp_path, prepared)
    recovered = entry.recover(tmp_path, "first")
    assert recovered["receipt"] == original["receipt"]
    assert recovered["applicability"] == "requires_owner_reconciliation"
    assert recovered["replayed"] is False
    assert exact_source(tmp_path, prepared, "observation.json") == captured


def test_changed_declared_premise_requires_reconciliation_but_allows_owner_research(tmp_path):
    _, assignment = research_case(tmp_path)
    write_json(tmp_path, "observation.json", {"result": "A changed premise must be considered by its owner."})
    with pytest.raises(ValueError, match="research dependency changed"):
        current(tmp_path, event="design", assignment=assignment)
    assert not entry.direction_owner._location(tmp_path, "first").exists()
    result, prepared = current(tmp_path, event="scope", assignment=assignment)
    assert any(source["research_item"] == "mechanism" and source["basis_changed"]
               for source in prepared["decision_material"]["research"])
    assert "A changed premise must be considered by its owner." in result["request"]


def test_consumer_cannot_silently_select_another_owners_research(tmp_path):
    _, assignment = research_case(tmp_path)
    write_json(tmp_path, assignment, {"research_use": {"owner": "another-owner.json", "items": ["mechanism"]}})
    with pytest.raises(ValueError, match="owner"):
        current(tmp_path, event="design", assignment=assignment)
    assert not entry.direction_owner._location(tmp_path, "first").exists()


def test_unclassified_registered_result_reaches_owner_before_selection_and_is_versioned(tmp_path):
    _, assignment = research_case(tmp_path, with_result=True)
    result, prepared = current(tmp_path, event="design", assignment=assignment)
    work = json.loads((tmp_path / "work.json").read_text())
    original_result = work["attempts"][0]["result"]
    pending = prepared["research_pending"]
    assert any(item["source"] == {"path": "work.json", "attempt": "A1"}
               and item["sha256"] == sha256_bytes(canonical_json(original_result)) for item in pending)
    assert original_result["finding"] in result["request"]
    assert "work.json" in prepared["actual_use"]
    assert json.loads(exact_source(tmp_path, prepared, "work.json")) == work
    work["attempts"].append({"attempt": "A2", "status": "completed",
                             "result": {"finding": "A further result arrived before delivery."}})
    write_json(tmp_path, "work.json", work)
    with pytest.raises(ValueError):
        entry.consume_request(tmp_path, prepared)


def test_exact_incorporation_reuses_existing_result_state_and_changed_result_reappears(tmp_path):
    owner, assignment = research_case(tmp_path, with_result=True)
    work = json.loads((tmp_path / "work.json").read_text())
    original_result = work["attempts"][0]["result"]
    owner["context_account"]["incorporates"] = [{"path": "work.json", "attempt": "A1",
        "sha256": sha256_bytes(canonical_json(original_result))}]
    write_json(tmp_path, "owner.json", owner)
    _, incorporated = current(tmp_path, event="design", assignment=assignment)
    assert incorporated["research_pending"] == []
    work["attempts"][0]["result"] = {"finding": "The returned result changed after incorporation."}
    write_json(tmp_path, "work.json", work)
    _, changed = current(tmp_path, invocation="changed-result", event="scope", assignment=assignment)
    assert len(changed["research_pending"]) == 1
    assert changed["research_pending"][0]["source"] == {"path": "work.json", "attempt": "A1"}
    assert changed["research_pending"][0]["sha256"] != owner["context_account"]["incorporates"][0]["sha256"]


def test_initial_inquiry_without_a_research_account_is_not_a_readiness_gate(tmp_path):
    owner = setup_owner(tmp_path)
    result, prepared = current(tmp_path)
    assert prepared["current_account"] is None
    assert owner["governing_condition"] in result["request"]
    assert prepared["research_pending"] == []


def test_current_cli_supports_real_design_entry(tmp_path):
    _, assignment = research_case(tmp_path)
    result = subprocess.run([sys.executable, str(ENTRY), "current", "--root", str(tmp_path),
        "--owner", "owner.json", "--assignment", assignment, "--invocation", "cli-design",
        "--event", "design"], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    directory = entry.direction_owner._location(tmp_path, "cli-design")
    assert result.stdout == (directory / "request.txt").read_text()
    prepared = json.loads((directory / "prepared.json").read_text())
    assert prepared["current_account"]["research_view"]["selected_ids"] == ["mechanism"]
    assert "UNRELATED_ACCOUNT_PAYLOAD" not in result.stdout


def test_maintained_publication_view_and_impact_commands_use_actual_owner_and_consumer_sources(tmp_path):
    owner, assignment = research_case(tmp_path)
    old_basis = owner["research_basis"]
    write_json(tmp_path, "old-basis.json", old_basis)
    proposed = json.loads(json.dumps(old_basis))
    proposed["items"][0]["conditions"] = "The owner adopted a narrower applicability condition."
    unchanged_source = (tmp_path / "observation.json").read_bytes()
    unchanged_consumer = (tmp_path / assignment).read_bytes()
    (tmp_path / "chart.md").write_text("A user-maintained unrelated file must not be overwritten.")
    request = write_json(tmp_path, "publication.json", {
        "operation": "adopt-bounded-research-update",
        "expected_owner_sha256": sha256_bytes((tmp_path / "owner.json").read_bytes()),
        "expected_account_sha256": basis_digest(old_basis),
        "proposed_account": proposed,
    })
    published = references_cli(tmp_path, "adopt-context-account", "--owner-source", "owner.json",
                               "--result", request.resolve(), "--raw")
    assert published.returncode == 0, published.stdout + published.stderr
    receipt = json.loads(published.stdout)
    after_bytes = (tmp_path / "owner.json").read_bytes()
    after = json.loads(after_bytes)
    assert receipt["status"] == "adopted" and receipt["current"] is True
    assert receipt["owner_sha256"] == sha256_bytes(after_bytes)
    assert receipt["account_sha256"] == basis_digest(proposed)
    assert after["research_basis"] == proposed
    assert after["context_account"]["source"] == {"path": "owner.json", "field": "research_basis"}
    assert after["context_account"]["sha256"] == basis_digest(proposed)
    assert after["governing_condition"] == owner["governing_condition"]
    assert after["current_state"] == owner["current_state"]
    assert json.loads(read_retained(tmp_path, receipt["proposal"])) == proposed
    repeated = references_cli(tmp_path, "adopt-context-account", "--owner-source", "owner.json",
                              "--result", request.resolve(), "--raw")
    assert repeated.returncode == 0, repeated.stdout + repeated.stderr
    assert json.loads(repeated.stdout) == receipt
    assert (tmp_path / "owner.json").read_bytes() == after_bytes

    view = references_cli(tmp_path, "research-view", "--owner-source", "owner.json",
                          "--item", "mechanism", "--mermaid", "--raw")
    assert view.returncode == 0, view.stdout + view.stderr
    chart = json.loads(view.stdout)
    assert chart["source"] == after["context_account"]["source"]
    assert chart["view"] == select_basis(proposed, ["mechanism"])
    assert chart["view"]["revision"] == after["context_account"]["sha256"]
    assert "```mermaid" in chart["render"]["text"]
    assert "The owner adopted a narrower applicability condition." in chart["render"]["text"]
    assert "UNRELATED_ACCOUNT_PAYLOAD" not in chart["render"]["text"]
    rendered = references_cli(tmp_path, "research-view", "--owner-source", "owner.json",
                              "--item", "mechanism", "--mermaid")
    assert rendered.returncode == 0, rendered.stdout + rendered.stderr
    assert rendered.stdout == chart["render"]["text"]

    write_json(tmp_path, "unrelated-consumer.json", {"research_use": {
        "owner": "owner.json", "items": ["unrelated"]}})
    write_json(tmp_path, "undeclared-consumer.json", {"purpose": "This consumer has no declared research links."})
    impact = references_cli(tmp_path, "research-impact", "--owner-source", "owner.json",
        "--prior", "old-basis.json", "--source", assignment,
        "--source", "unrelated-consumer.json", "--source", "undeclared-consumer.json", "--raw")
    assert impact.returncode == 0, impact.stdout + impact.stderr
    affected = json.loads(impact.stdout)
    assert affected["changed_items"] == ["mechanism"]
    assert [use["path"] for use in affected["uses"]] == [assignment]
    assert affected["uses"][0]["changed_items"] == ["mechanism"]
    assert affected["undeclared_consumers"] == ["undeclared-consumer.json"]
    assert (tmp_path / "owner.json").read_bytes() == after_bytes
    assert (tmp_path / "observation.json").read_bytes() == unchanged_source
    assert (tmp_path / assignment).read_bytes() == unchanged_consumer
    assert (tmp_path / "chart.md").read_text() == "A user-maintained unrelated file must not be overwritten."


def test_view_command_rejects_unadopted_edits_and_has_no_account_overwrite_option(tmp_path):
    owner, _ = research_case(tmp_path)
    untouched = (tmp_path / "owner.json").read_bytes()
    overwrite = references_cli(tmp_path, "research-view", "--owner-source", "owner.json",
                                "--output", tmp_path / "owner.json")
    assert overwrite.returncode == 2
    assert (tmp_path / "owner.json").read_bytes() == untouched
    owner["research_basis"]["overview"] = "This edit has not been adopted."
    write_json(tmp_path, "owner.json", owner)
    drifted = (tmp_path / "owner.json").read_bytes()
    view = references_cli(tmp_path, "research-view", "--owner-source", "owner.json", "--raw")
    assert view.returncode == 2
    assert json.loads(view.stdout)["status"] == "NOT_READY"
    assert "changed since adoption" in json.loads(view.stdout)["error"]
    assert (tmp_path / "owner.json").read_bytes() == drifted


def test_top_level_result_incorporation_checks_selected_result_instead_of_unrelated_fields(tmp_path):
    owner, assignment = research_case(tmp_path)
    returned = {"result": {"finding": "The observed condition is now represented in the adopted account."},
                "runtime_note": "Initial ancillary information."}
    result_path = write_json(tmp_path, "return.json", returned)
    owner["current_state"]["work_record"] = "return.json"
    selected_sha = digest(_selected_text(result_path.read_text(), {"field": "result"}))
    owner["context_account"]["incorporates"] = [{"path": "return.json", "field": "result", "sha256": selected_sha}]
    write_json(tmp_path, "owner.json", owner)
    _, first = current(tmp_path, event="design", assignment=assignment)
    assert first["research_pending"] == []
    assert not any("Incorporated basis changed" in limitation for limitation in first["limitations"])
    returned["runtime_note"] = "Only unrelated ancillary information changed."
    write_json(tmp_path, "return.json", returned)
    _, ancillary = current(tmp_path, invocation="ancillary", event="design", assignment=assignment)
    assert ancillary["research_pending"] == []
    assert not any("Incorporated basis changed" in limitation for limitation in ancillary["limitations"])
    assert first["delivery_identity"] != ancillary["delivery_identity"]
    returned["result"] = {"finding": "The substantive result now differs from its incorporated version."}
    write_json(tmp_path, "return.json", returned)
    _, changed = current(tmp_path, invocation="changed", event="scope", assignment=assignment)
    assert any("Incorporated basis changed: return.json" in limitation for limitation in changed["limitations"])
    assert len(changed["research_pending"]) == 1
    assert changed["research_pending"][0]["source"] == {"path": "return.json"}
    assert changed["research_pending"][0]["sha256"] != selected_sha


def test_registered_missing_return_appearing_after_preparation_refreshes_input(tmp_path):
    owner, assignment = research_case(tmp_path)
    owner["current_state"]["work_record"] = "late-return.json"
    write_json(tmp_path, "owner.json", owner)
    _, prepared = entry.prepare_call(tmp_path, "owner.json", assignment, "direction")
    assert {"source": {"path": "late-return.json"}, "availability": "source_unavailable"} in prepared["research_return_sources"]
    write_json(tmp_path, "late-return.json", {"result": {"finding": "The registered result arrived before use."}})
    with pytest.raises(ValueError):
        entry.consume_request(tmp_path, prepared)
    result, refreshed = current(tmp_path, event="direction", assignment=assignment)
    assert any(source["source"] == {"path": "late-return.json"} and source["availability"] == "available"
               for source in refreshed["research_return_sources"])
    assert refreshed["research_pending"][0]["source"] == {"path": "late-return.json"}
    assert "The registered result arrived before use." in result["request"]
