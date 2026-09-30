"""Real delivery boundaries and reuse failures; no claims of model fidelity."""

import json
from pathlib import Path

import pytest
import yaml

import frontier_references as refs
from context_delivery import digest, model_view, read_retained, verify_prepared


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


def test_decoded_source_retains_its_exact_original_bytes(tmp_path):
    text = json.dumps({"fact": "Conditional evidence. " * 50}, indent=4) + "\r\n"
    value = {"sources": [{"source": {"path": "mutable.json"}, "contents": text, "sha256": digest(text)}]}
    view = model_view(tmp_path, value)
    assert isinstance(view["sources"][0]["contents"], dict)
    assert read_retained(tmp_path, view["sources"][0]["retrieval"]) == text
