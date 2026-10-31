"""Real delivery boundaries and reuse failures; no claims of model fidelity."""

import json
from pathlib import Path

import pytest
import yaml

import frontier_references as refs
from context_delivery import consume_request, digest, model_view, read_retained, verify_prepared


def account_case(root):
    (root / "understanding.md").write_text("# Current\nResult is positive only under condition C. Alternative Z remains open.\n")
    (root / "evidence.md").write_text("Observed A; C remains necessary.")
    account = {"source": {"path": "understanding.md"},
               "sha256": digest((root / "understanding.md").read_text()),
               "incorporates": [{"path": "evidence.md", "sha256": digest((root / "evidence.md").read_text())}],
               "actual_use": ["evidence.md"]}
    (root / "owner.json").write_text(json.dumps({"objective": "Improve the whole outcome", "context_account": account}))
    return account


def test_shared_content_is_delivered_once_even_across_nested_fields(tmp_path):
    text = "The same original objective and all its qualifications. " * 20
    view = model_view(tmp_path, {"objective": text, "evaluation": text, "nested": {"sources": [text]}})
    assert view["objective"] == text
    assert view["evaluation"] == {"delivered_content_ref": "/objective"}
    assert view["nested"]["sources"][0] == {"delivered_content_ref": "/objective"}


def test_unchanged_preparation_reuses_account_and_exact_evidence(tmp_path):
    account_case(tmp_path)
    first = refs.prepare_adoption_context(tmp_path, "owner.json")
    snapshots = {p: p.stat().st_mtime_ns for p in (tmp_path / "artifacts").rglob("*.txt")}
    for _ in range(3):
        assert refs.prepare_adoption_context(tmp_path, "owner.json") == first
    assert snapshots == {p: p.stat().st_mtime_ns for p in snapshots}
    verify_prepared(tmp_path, model_view(tmp_path, first))
    (tmp_path / "irrelevant.md").write_text("Unrelated new history" * 1000)
    assert refs.prepare_adoption_context(tmp_path, "owner.json") == first


def test_declared_basis_and_actual_request_are_checked_at_consumption(tmp_path):
    account_case(tmp_path)
    view = refs.prepare_adoption_context(tmp_path, "owner.json")
    altered = dict(view, instruction="Different request")
    with pytest.raises(ValueError, match="delivery was changed"):
        verify_prepared(tmp_path, altered)
    (tmp_path / "evidence.md").write_text("Contradictory B.")
    with pytest.raises(ValueError, match="source changed"):
        verify_prepared(tmp_path, view)


def test_account_edit_or_loss_preserves_last_adopted_meaning(tmp_path):
    account_case(tmp_path)
    first = refs.prepare_adoption_context(tmp_path, "owner.json")
    old = first["current_account"]["contents"]
    locator = first["current_account"]["retrieval"]
    (tmp_path / "understanding.md").write_text("Proposed unconditional success; not adopted.")
    changed = refs.prepare_adoption_context(tmp_path, "owner.json")
    assert changed["current_account"]["contents"] == old
    assert "unconditional" in changed["current_account"]["pending_contents"]
    assert read_retained(tmp_path, locator) == old
    (tmp_path / "understanding.md").unlink()
    missing = refs.prepare_adoption_context(tmp_path, "owner.json")
    assert missing["current_account"]["contents"] == old
    assert any("unavailable" in item for item in missing["limitations"])


def test_snapshot_corruption_is_not_silent_newer_evidence(tmp_path):
    account_case(tmp_path)
    view = refs.prepare_adoption_context(tmp_path, "owner.json")
    locator = view["current_account"]["retrieval"]
    (tmp_path / locator["path"]).write_text("Changed bytes")
    with pytest.raises(ValueError, match="retained evidence changed"):
        verify_prepared(tmp_path, view)


def test_partial_incorporation_keeps_new_result_effects_and_brief(tmp_path):
    (tmp_path / "understanding.md").write_text("Old result establishes C, not general superiority. Z remains open.")
    old_result = {"learning": "C only", "raw": "Historical detail " * 1000}
    batch = {"batch": "B1", "definition": {"objective": "Test Z"}, "current": {"status": "running"},
             "consumption": {"calls": 1}, "attempts": [
                 {"attempt": 1, "status": "completed", "result": old_result, "actual_consequences": ["spent 1"], "recovery_condition": "Never repeat"},
                 {"attempt": 2, "status": "completed", "result": {"learning": "New contradictory result"}},
                 {"attempt": 3, "status": "uncertain", "observations": ["Unsettled effects"]}]}
    (tmp_path / "batch.yaml").write_text(yaml.safe_dump(batch))
    account = {"source": {"path": "understanding.md"}, "sha256": digest((tmp_path / "understanding.md").read_text()),
               "incorporates": [{"path": "batch.yaml", "attempt": 1, "sha256": digest(refs.canonical_json(old_result).decode())}]}
    owner = {"type": "Optimization Frontier", "current_state": {"work_record": "batch.yaml"}, "context_account": account}
    (tmp_path / "owner.md").write_text("---\n" + yaml.safe_dump(owner) + "---\n## Brief\nThe broader goal permits other mechanisms.\n## History\n" + "event " * 1000)
    view = refs.prepare_adoption_context(tmp_path, "owner.md")
    shown = yaml.safe_load(view["sources"][view["outgoing_tasks"][0]["source_index"]]["contents"])
    assert "result" not in shown["attempts"][0]
    assert shown["attempts"][0]["actual_consequences"] == ["spent 1"]
    assert "contradictory" in shown["attempts"][1]["result"]["learning"]
    assert shown["attempts"][2] == batch["attempts"][2]
    assert "broader goal" in view["sources"][view["owner"]["source_index"]]["contents"]
    # The adopted attempt stays reusable when another result arrives.
    batch["attempts"].append({"attempt": 4, "status": "running"})
    (tmp_path / "batch.yaml").write_text(yaml.safe_dump(batch))
    later = refs.prepare_adoption_context(tmp_path, "owner.md")
    assert "Historical detail" not in later["sources"][later["outgoing_tasks"][0]["source_index"]]["contents"]


def test_cli_sidecar_cannot_reintroduce_old_merged_fields(tmp_path, monkeypatch, capsys):
    (tmp_path / "owner.md").write_text("A simple scoped task.")
    output = tmp_path / "prepared.json"
    output.write_text(json.dumps({"old_history": "irrelevant " * 10000}))
    monkeypatch.setattr("sys.argv", ["frontier_references.py", "recover-work", "--repo", str(tmp_path),
                                    "--owner-source", "owner.md", "--output", str(output)])
    assert refs.main() == 0
    locator = json.loads(capsys.readouterr().out)
    delivered = json.loads(Path(locator["delivery"]).read_text())
    assert "old_history" not in delivered
    assert "old_history" in json.loads(output.read_text())
    verify_prepared(tmp_path, delivered)


def test_interrupted_snapshot_publication_does_not_poison_reuse(tmp_path, monkeypatch):
    import context_delivery as delivery
    original = delivery.os.link
    with monkeypatch.context() as patch:
        patch.setattr(delivery.os, "link", lambda *args: (_ for _ in ()).throw(InterruptedError("interrupted before publication")))
        with pytest.raises(InterruptedError):
            delivery.retain_source(tmp_path, "Necessary evidence")
    assert not list((tmp_path / "artifacts/workflow-harness/context-sources").iterdir())
    saved = delivery.retain_source(tmp_path, "Necessary evidence")
    assert delivery.read_retained(tmp_path, saved) == "Necessary evidence"
    windows = delivery.retain_source(tmp_path, "Exact\r\nsource\r\n")
    assert delivery.read_retained(tmp_path, windows) == "Exact\r\nsource\r\n"


def test_nested_generated_packet_and_serialized_objective_do_not_multiply_delivery(tmp_path):
    objective = "Original objective with necessary conditions. " * 30
    value = {"objective": objective, "saved": json.dumps({"incoming": {"objective": objective}})}
    view = model_view(tmp_path, value)
    assert view["saved"]["decoded_json"]["incoming"]["objective"] == {"delivered_content_ref": "/objective"}


def test_long_repeated_dependency_paths_keep_their_machine_shape(tmp_path):
    path = "/".join(["long-directory-" * 10] * 3) + "/task.md"
    view = model_view(tmp_path, {"source": {"path": path}, "actual_use": [path], "copy": {"path": path}})
    assert view["source"]["path"] == view["actual_use"][0] == view["copy"]["path"] == path


def test_judgment_cannot_lose_all_decision_carriers_even_with_new_display_digest(tmp_path):
    (tmp_path / "owner.md").write_text("The current task owner.")
    view = refs.prepare_adoption_context(tmp_path, "owner.md")
    view["judgment_binding"] = {"version": 1, "uses": [], "decision_sha256": digest("obsolete decision")}
    view["delivery_identity"] = digest(json.dumps({key: part for key, part in view.items()
                                                  if key != "delivery_identity"}, ensure_ascii=False, sort_keys=True))
    with pytest.raises(ValueError, match="no actual decision carrier"):
        verify_prepared(tmp_path, view)


def test_batch_projection_retains_operative_current_restrictions():
    batch = {"batch": "B1", "definition": {"objective": "Test the mechanism"},
             "current": {"status": "prepared", "measurement_definition": {"resource_ceiling": 1}}, "attempts": []}
    first = refs._use_projection(yaml.safe_dump(batch))
    batch["current"]["status"] = "running"
    batch["current"]["checks"] = ["Support repair passed"]
    assert refs._use_projection(yaml.safe_dump(batch)) == first
    batch["current"]["measurement_definition"]["resource_ceiling"] = 0
    assert refs._use_projection(yaml.safe_dump(batch)) != first

    batch["current"]["measurement_definition"]["resource_ceiling"] = 1
    batch["current"]["status"] = "rejected"
    assert refs._use_projection(yaml.safe_dump(batch)) != first
    batch["current"]["status"] = "completed"
    assert refs._use_projection(yaml.safe_dump(batch)) == first
    batch["current"]["conclusion"] = "Exclude this mechanism permanently."
    assert refs._use_projection(yaml.safe_dump(batch)) != first


def selected_request_case(root):
    (root / "goal.md").write_text("# Current\nCompare useful observations; only the final cold timing excludes reused results.\n"
                                 "# Draft\nProposed: prohibit every reused result.\n# History\n" + "Retired condition. " * 1000)
    (root / "work.md").write_text("# Now\nInspect effective settings and the affected timing claim; retain valid output.\n"
                                 "# Old handoff\nStart all work from scratch regardless of the claim.\n")
    (root / "owner.json").write_text(json.dumps({"objective_basis": {
        "objective_source": {"path": "goal.md", "section": "current"},
        "evaluation_source": {"path": "goal.md", "section": "current"},
        "current_work_source": {"path": "work.md", "section": "now"}}}))


def test_rendered_request_uses_selected_units_and_keeps_history_retrievable(tmp_path):
    selected_request_case(tmp_path)
    prepared = refs.prepare_adoption_context(tmp_path, "owner.json")
    raw = consume_request(tmp_path, prepared)
    projected = consume_request(tmp_path, model_view(tmp_path, prepared))
    assert raw == projected
    assert raw.count("only the final cold timing excludes reused results") == 1
    assert "Inspect effective settings" in raw
    assert "prohibit every reused result" not in raw
    assert "Start all work from scratch" not in raw
    assert "Retired condition" not in raw
    assert "work.md" in prepared["actual_use"]
    goal = next(s for s in prepared["sources"] if s["source"]["path"] == "goal.md")
    # The full source is still accessible without delivering it as current work.
    assert "# Draft" in read_retained(tmp_path, goal.get("retrieval") or
                                      __import__("context_delivery").retain_source(tmp_path, goal["contents"]))


def test_missing_selector_cannot_turn_whole_history_into_current_instructions(tmp_path):
    selected_request_case(tmp_path)
    (tmp_path / "work.md").write_text("# Old handoff\nRestart everything.\n")
    prepared = refs.prepare_adoption_context(tmp_path, "owner.json")
    with pytest.raises(ValueError, match="selection unavailable"):
        consume_request(tmp_path, model_view(tmp_path, prepared))
    # An independent focused request still works; this is not a workspace hold.
    (tmp_path / "independent.md").write_text("Inspect the unrelated parser.")
    assert "unrelated parser" in consume_request(tmp_path, refs.prepare_adoption_context(tmp_path, "independent.md"))


def test_pending_account_revision_is_not_the_governing_request(tmp_path):
    selected_request_case(tmp_path)
    account_case(tmp_path)
    first = refs.prepare_adoption_context(tmp_path, "owner.json")
    (tmp_path / "understanding.md").write_text("Proposed unconditional success; not adopted.")
    updated = model_view(tmp_path, refs.prepare_adoption_context(tmp_path, "owner.json"))
    request = consume_request(tmp_path, updated)
    assert first["current_account"]["contents"] in request
    assert "Proposed unconditional success" not in request


def test_adopted_account_controls_overlapping_source_until_owner_adopts_revision(tmp_path):
    account = account_case(tmp_path)
    owner = json.loads((tmp_path / "owner.json").read_text())
    owner["objective_basis"] = {role: {"path": "understanding.md"} for role in
                               ("objective_source", "evaluation_source", "current_work_source")}
    (tmp_path / "owner.json").write_text(json.dumps(owner))
    first = refs.prepare_adoption_context(tmp_path, "owner.json")
    (tmp_path / "understanding.md").write_text("Proposed unconditional success; not adopted.")
    pending = model_view(tmp_path, refs.prepare_adoption_context(tmp_path, "owner.json"))
    rendered = consume_request(tmp_path, pending)
    assert "Proposed unconditional success" not in rendered
    assert first["current_account"]["contents"] in rendered
    owner["context_account"]["sha256"] = digest((tmp_path / "understanding.md").read_text())
    (tmp_path / "owner.json").write_text(json.dumps(owner))
    adopted = refs.prepare_adoption_context(tmp_path, "owner.json")
    assert "Proposed unconditional success" in consume_request(tmp_path, model_view(tmp_path, adopted))
    with pytest.raises(ValueError, match="source changed"):
        consume_request(tmp_path, pending)


def test_selected_work_is_not_reexpanded_by_current_state_or_explicit_source(tmp_path):
    selected_request_case(tmp_path)
    owner = json.loads((tmp_path / "owner.json").read_text())
    owner["current_state"] = {"work_record": "work.md"}
    (tmp_path / "owner.json").write_text(json.dumps(owner))
    request = consume_request(tmp_path, model_view(tmp_path, refs.prepare_adoption_context(
        tmp_path, "owner.json", task_sources=["work.md"])))
    assert "Start all work from scratch" not in request
    assert request.count("Inspect effective settings") == 1


@pytest.mark.parametrize("governing,adopted,overlap", [
    ("current", "adopted", True), ("adopted", "current", True), ("independent", "adopted", False)])
def test_pending_nested_sections_do_not_compete_with_adoption(tmp_path, governing, adopted, overlap):
    original = "# Current\nScope C.\n## Adopted\nConditional only.\n# Independent\nInspect the parser.\n"
    (tmp_path / "meaning.md").write_text(original)
    association = {"source": {"path": "meaning.md", "section": adopted},
                   "sha256": digest(refs._selected_text(original, {"section": adopted}))}
    (tmp_path / "owner.json").write_text(json.dumps({"context_account": association, "objective_basis": {
        role: {"path": "meaning.md", "section": governing} for role in
        ("objective_source", "evaluation_source", "current_work_source")}}))
    refs.prepare_adoption_context(tmp_path, "owner.json")
    (tmp_path / "meaning.md").write_text(original.replace("Conditional only.", "Pending unconditional revision."))
    prepared = model_view(tmp_path, refs.prepare_adoption_context(tmp_path, "owner.json"))
    if overlap:
        with pytest.raises(ValueError, match="overlaps a pending"):
            consume_request(tmp_path, prepared)
    else:
        request = consume_request(tmp_path, prepared)
        assert "Pending unconditional revision" not in request
        assert "Inspect the parser" in request


def test_nested_proposal_references_remain_readable_in_standalone_request(tmp_path):
    selected_request_case(tmp_path)
    detail = "A conditional recommendation, not adopted. " * 20
    prepared = refs.prepare_adoption_context(tmp_path, "owner.json", incoming={
        "requested_work": detail, "conditions": {"same": [detail]},
        "serialized": json.dumps({"notes": detail}, indent=4)})
    raw = consume_request(tmp_path, prepared)
    projected = consume_request(tmp_path, model_view(tmp_path, prepared))
    assert projected == raw
    assert "delivered_content_ref" not in projected
    assert "decoded_json" not in projected


def test_selected_work_cannot_omit_its_known_correction_scope(tmp_path):
    selected_request_case(tmp_path)
    (tmp_path / "finding.md").write_text("The selected work needs an owner correction.")
    owner = json.loads((tmp_path / "owner.json").read_text())
    owner["current_use_corrections"] = [{"id": "selected-work", "finding": "finding.md",
        "effect": "repair", "affected_sources": ["work.md"], "status": "open"}]
    (tmp_path / "owner.json").write_text(json.dumps(owner))
    prepared = refs.prepare_adoption_context(tmp_path, "owner.json")
    with pytest.raises(ValueError, match="requires owner correction"):
        consume_request(tmp_path, model_view(tmp_path, prepared))


def test_normal_cli_delivers_the_actual_request_and_rejects_stale_use(tmp_path):
    import subprocess
    import sys

    selected_request_case(tmp_path)
    script = Path(refs.__file__)
    command = [sys.executable, str(script)]
    prepared = subprocess.run(command + ["recover-work", "--repo", str(tmp_path),
        "--owner-source", "owner.json", "--output", str(tmp_path / "prepared.json")],
        capture_output=True, text=True, check=True)
    delivery = json.loads(prepared.stdout)["delivery"]
    received = tmp_path / "received.txt"

    def handoff():
        result = subprocess.run(command + ["deliver", "--repo", str(tmp_path), "--path", delivery],
                                capture_output=True, text=True)
        if result.returncode == 0:
            # A real receiving process gets the emitted request unchanged.
            subprocess.run([sys.executable, "-c", "import pathlib,sys; pathlib.Path(sys.argv[1]).write_bytes(sys.stdin.buffer.read())",
                            str(received)], input=result.stdout.encode(), check=True)
        return result

    assert handoff().returncode == 0
    original = received.read_text()
    assert "only the final cold timing" in original
    (tmp_path / "unrelated.md").write_text("New progress elsewhere.")
    assert handoff().returncode == 0
    assert received.read_text() == original
    (tmp_path / "goal.md").write_text("# Current\nThe owner has adopted a changed observation.\n")
    assert handoff().returncode == 2
    assert received.read_text() == original  # No stale second delivery occurred.


@pytest.mark.parametrize("choice", [
    "Reuse the produced reference; changed source or scale requires refresh. Inspect the next consumer.",
    "Defer extraction for the remaining short use. Its cost is uncertain; revisit if the horizon grows.",
])
def test_ordinary_choice_survives_owner_transfer_and_cli_recovery(tmp_path, choice):
    import subprocess
    import sys

    account_case(tmp_path)
    (tmp_path / "understanding.md").write_text(choice)
    owner = json.loads((tmp_path / "owner.json").read_text())
    owner["context_account"]["sha256"] = digest(choice)
    owner["objective_basis"] = {"current_work_source": "work.md"}
    (tmp_path / "work.md").write_text("Complete the next useful request under the current choice.")
    (tmp_path / "owner.json").write_text(json.dumps(owner))
    initial = refs.prepare_adoption_context(tmp_path, "owner.json")
    assert initial["current_use"] is None
    assert choice in consume_request(tmp_path, model_view(tmp_path, initial))

    # Ordinary decisions transfer by their adopted source, not a finding receipt.
    (tmp_path / "successor.md").write_text("Receive the next request; apply the retained choice and its conditions.")
    owner["objective_basis"]["current_work_source"] = "successor.md"
    (tmp_path / "next-owner.json").write_text(json.dumps(owner))
    (tmp_path / "owner.json").unlink()
    script = Path(refs.__file__).resolve()
    prepared = subprocess.run([sys.executable, str(script), "recover-work", "--repo", str(tmp_path),
        "--owner-source", "next-owner.json", "--output", str(tmp_path / "recovered.json")],
        capture_output=True, text=True, check=True)
    delivery = json.loads(prepared.stdout)["delivery"]
    command = [sys.executable, str(script), "deliver", "--repo", str(tmp_path), "--path", delivery]
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    received = subprocess.run([sys.executable, "-c", "import sys; print(sys.stdin.read(), end='')"],
                              input=result.stdout, capture_output=True, text=True, check=True)
    assert choice in received.stdout
    assert (tmp_path / "successor.md").read_text() in received.stdout
    assert (tmp_path / "work.md").read_text() not in received.stdout
    recovered = json.loads((tmp_path / "recovered.json").read_text())
    assert recovered["current_use"] is None
    (tmp_path / "unrelated.md").write_text("Unrelated progress does not reset this choice.")
    assert subprocess.run(command, capture_output=True, text=True, check=True).stdout == received.stdout
    (tmp_path / "understanding.md").write_text("Proposed change to the retained choice; not yet adopted.")
    assert subprocess.run(command, capture_output=True, text=True).returncode == 2


def test_selected_json_retains_exact_bytes_after_model_projection(tmp_path):
    settings = {"condition": "Preserve effective scope. " * 30, "mode": "current"}
    (tmp_path / "owner.json").write_text(json.dumps({"objective_basis": {
        "objective_source": {"path": "settings.json", "field": "current"},
        "evaluation_source": {"path": "settings.json", "field": "current"},
        "current_work_source": {"path": "settings.json", "field": "current"}}}))
    (tmp_path / "settings.json").write_text(json.dumps({"current": settings, "draft": "prohibit all work"}))
    prepared = refs.prepare_adoption_context(tmp_path, "owner.json")
    assert consume_request(tmp_path, prepared) == consume_request(tmp_path, model_view(tmp_path, prepared))


def test_decoded_source_retains_its_exact_original_bytes(tmp_path):
    text = json.dumps({"fact": "Conditional evidence. " * 50}, indent=4) + "\r\n"
    value = {"sources": [{"source": {"path": "mutable.json"}, "contents": text, "sha256": digest(text)}]}
    view = model_view(tmp_path, value)
    assert isinstance(view["sources"][0]["contents"], dict)
    assert read_retained(tmp_path, view["sources"][0]["retrieval"]) == text


def decision_material_case(root):
    (root / "observations.md").write_text("# Matched cases\nCase A changes its answer under condition C; B does not.\n")
    (root / "exchange.md").write_text("# Exchange\nQuestion: use local, hosted or mixed compute?\nOptions: A local training; B hosted training.\nAnswer: A; feedback remains to be decided.\nCorrection: do not turn local training into a submission prohibition.\n")
    (root / "scope.md").write_text("# Scope\nStatus: explicit denial. No external feedback.\n")
    owner = {"objective": "Improve the useful outcome", "decision_material": {
        "evidence": [{"path": "observations.md", "section": "matched-cases"}],
        "user_scope": [{"original": [{"path": "exchange.md", "section": "exchange"}],
                        "interpretation": {"path": "scope.md", "section": "scope"}}]}}
    (root / "owner.json").write_text(json.dumps(owner))


def test_material_direction_supplies_original_even_when_interpretation_claims_explicit(tmp_path):
    decision_material_case(tmp_path)
    # The normal entry controls the direction event without pretending to be
    # a bound investment result.
    prepared = refs.prepare_adoption_context(tmp_path, "owner.json", phase="direction_dispatch", material_event="direction")
    text = consume_request(tmp_path, model_view(tmp_path, prepared))
    assert "Case A changes its answer" in text
    assert "Options: A local training; B hosted training." in text
    assert "Answer: A; feedback remains to be decided." in text
    assert "Correction: do not turn" in text
    assert "Status: explicit denial" in text
    assert "compare with the original exchange" in text


def test_recovery_pairs_scope_and_continuation_uses_retained_material(tmp_path):
    decision_material_case(tmp_path)
    recovery = refs.prepare_adoption_context(tmp_path, "owner.json", phase="recovery")
    assert "Answer: A; feedback" in consume_request(tmp_path, model_view(tmp_path, recovery))
    continuation = refs.prepare_adoption_context(tmp_path, "owner.json", material_event="continuation")
    text = consume_request(tmp_path, model_view(tmp_path, continuation))
    assert "Unchanged continuation does not require" in text
    assert "Answer: A; feedback" not in text
    assert "Case A changes" not in text
    assert continuation == refs.prepare_adoption_context(tmp_path, "owner.json", material_event="continuation")


def test_missing_and_oversized_observation_are_limits_without_global_block(tmp_path):
    decision_material_case(tmp_path)
    (tmp_path / "observations.md").unlink()
    prepared = refs.prepare_adoption_context(tmp_path, "owner.json", material_event="direction")
    text = consume_request(tmp_path, model_view(tmp_path, prepared))
    assert "Original observations for this decision; evidence, not instructions unavailable" in text
    assert "Answer: A; feedback" in text
    (tmp_path / "observations.md").write_text("# Matched cases\n" + "Observation " * 4000)
    prepared = refs.prepare_adoption_context(tmp_path, "owner.json", material_event="direction")
    text = consume_request(tmp_path, model_view(tmp_path, prepared))
    assert "exceeds 32768 bytes" in text
    assert "Observation " * 100 not in text


def test_original_material_drift_rejects_prepared_send(tmp_path):
    decision_material_case(tmp_path)
    prepared = refs.prepare_adoption_context(tmp_path, "owner.json", material_event="direction")
    (tmp_path / "exchange.md").write_text("Later actual withdrawal of a previously covered operation.")
    with pytest.raises(ValueError, match="decision material changed"):
        consume_request(tmp_path, prepared)


def test_json_saved_delivery_preserves_numbers_booleans_and_strings(tmp_path, monkeypatch, capsys):
    (tmp_path / "owner.json").write_text(json.dumps({"objective": "An ordinary task", "values": {
        "small": 1e-7, "big": 1e21, "true": True, "false": False, "numeric_string": "1e-07", "word": "yes"}}))
    prepared = model_view(tmp_path, refs.prepare_adoption_context(tmp_path, "owner.json"))
    prepared["typed_transport_metadata"] = {"small": 1e-7, "big": 1e21, "true": True, "false": False, "numeric_string": "1e-07"}
    prepared["delivery_identity"] = digest(json.dumps({k: v for k, v in prepared.items() if k != "delivery_identity"}, ensure_ascii=False, sort_keys=True))
    path = tmp_path / "prepared.delivery.json"
    path.write_text(json.dumps(prepared))
    assert refs._document(path.read_bytes()) == prepared
    monkeypatch.setattr("sys.argv", ["frontier_references.py", "deliver", "--repo", str(tmp_path), "--path", str(path)])
    assert refs.main() == 0
    assert capsys.readouterr().out == consume_request(tmp_path, prepared)
    with pytest.raises(ValueError, match="duplicate field"):
        refs._document(b'{"a": 1, "a": 2}')
    assert refs._document(b"a: true\nb: 2\n") == {"a": True, "b": 2}


@pytest.mark.parametrize("initial", ["missing_file", "missing_section"])
def test_material_availability_is_rechecked_before_delivery(tmp_path, initial):
    decision_material_case(tmp_path)
    if initial == "missing_file":
        (tmp_path / "exchange.md").unlink()
    else:
        (tmp_path / "exchange.md").write_text("# Unrelated\nNo selected exchange is available yet.\n")
    prepared = model_view(tmp_path, refs.prepare_adoption_context(tmp_path, "owner.json", material_event="direction"))
    first = consume_request(tmp_path, prepared)
    assert "exchange" in first and "unavailable" in first
    # Unchanged absence remains a usable packet with a concrete limit.
    assert consume_request(tmp_path, prepared) == first
    (tmp_path / "exchange.md").write_text("# Exchange\nLater actual instruction: do not perform the operation.\n")
    with pytest.raises(ValueError, match="decision material changed"):
        consume_request(tmp_path, prepared)
    refreshed = model_view(tmp_path, refs.prepare_adoption_context(tmp_path, "owner.json", material_event="scope"))
    assert "Later actual instruction" in consume_request(tmp_path, refreshed)
