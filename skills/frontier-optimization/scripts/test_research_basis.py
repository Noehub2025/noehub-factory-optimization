"""Content selection and publication boundaries, not scientific readiness."""

import copy
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
from threading import Barrier

import pytest

import research_basis as research
from current_use import _metadata, _receipt, adopt_current_work, inspect_current_use
from identity_bindings import canonical_json, sha256_bytes


def item(identity, *, links=(), text=None, conditions="Only condition A was measured."):
    return {"id": identity, "kind": "hypothesis", "text": text or f"Possible explanation {identity}.",
            "conditions": conditions, "sources": [], "links": list(links)}


def basis(*items):
    return {"schema": 1, "overview": "Several explanations remain open; the observations do not identify a cause.",
            "items": list(items or [item("explanation")])}


def edge(relation, target):
    return {"relation": relation, "target": target}


def owner(root, metadata=None):
    path = root / "nested" / "owner.md"
    path.parent.mkdir(exist_ok=True)
    import yaml
    path.write_text("---\n" + yaml.safe_dump(metadata or {"ordinary": "keep", "current_state": {"campaign_status": "running"}}) + "---\nKeep the original governing prose.\n")
    return "nested/owner.md"


def adopt(root, path, proposal, operation="proposal-1", **extra):
    raw = (root / path).read_bytes()
    metadata = _metadata(raw, path)
    arguments = {"operation": operation, "expected_owner_sha256": sha256_bytes(raw),
                 "expected_account_sha256": metadata.get("context_account", {}).get("sha256"),
                 "proposed_account": proposal, **extra}
    return research.adopt_context_account(root, path, **arguments), copy.deepcopy(arguments)


def state(root, path):
    return json.loads(_receipt(root, path).read_text())


def test_canonical_identity_matches_existing_field_selection():
    from frontier_references import _selected_text
    account = basis(item("a"))
    owner_text = json.dumps({"research_basis": account})
    assert research.basis_digest(account) == sha256_bytes(_selected_text(owner_text, {"field": "research_basis"}).encode())
    reordered = {"items": account["items"], "overview": account["overview"], "schema": 1}
    assert research.basis_digest(reordered) == research.basis_digest(account)


@pytest.mark.parametrize("mutate", [
    lambda value: value.update(schema=True),
    lambda value: value["items"].append(copy.deepcopy(value["items"][0])),
    lambda value: value["items"][0].update(conditions=""),
    lambda value: value["items"][0].update(links=[edge("proves", "a")]),
    lambda value: value["items"][0].update(links=[edge("supports", "missing")]),
    lambda value: value["items"][0].update(kind="established_by_publication"),
])
def test_invalid_accounts_do_not_gain_a_revision(mutate):
    account = basis(item("a"))
    mutate(account)
    with pytest.raises(ValueError):
        research.basis_digest(account)


def test_dependency_cycles_and_reverse_contrary_edges_are_selected_once():
    account = basis(
        item("a", links=[edge("depends_on", "b")]),
        item("b", links=[edge("depends-on", "a")]),
        item("counter", links=[edge("challenges", "b"), edge("depends_on", "condition")]),
        item("condition"),
        item("distant", links=[edge("supports", "counter")]),
        item("unrelated"),
    )
    view = research.select_basis(account, ["a"])
    assert view["included_ids"] == ["a", "b", "condition", "counter"]
    assert len(view["items"]) == 4
    assert "distant" not in view["included_ids"]
    changed = copy.deepcopy(account)
    changed["items"][3]["conditions"] = "The condition was not measured in population B."
    after = research.select_basis(changed, ["a"])
    assert after["item_sha256"]["condition"] != view["item_sha256"]["condition"]
    assert after["item_sha256"]["a"] == view["item_sha256"]["a"]


def test_bounded_rendering_never_separates_claim_from_conditions():
    account = basis(item("short"), item("large", text="Long claim. " * 500,
                                        conditions="Crucial contrary evidence must remain with this claim."))
    view = research.select_basis(account)
    rendered = research.render_basis(view, max_chars=1300, mermaid=True)
    assert len(rendered["text"]) <= 1300
    assert rendered["omitted_ids"] == ["large"]
    assert "Long claim." not in rendered["text"]
    assert "Only condition A was measured." in rendered["text"]
    assert "1 items" in rendered["text"]
    changed = copy.deepcopy(view)
    changed["items"][0]["conditions"] = "No restriction."
    with pytest.raises(ValueError, match="projection differs"):
        research.render_basis(changed)


def test_consumer_owned_references_derive_affected_uses():
    before = basis(item("a", links=[edge("depends_on", "b")]), item("b"), item("c"))
    after = copy.deepcopy(before)
    after["items"][1]["conditions"] = "Only a narrower condition applies."
    use = {"owner": "owner.json", "items": ["a"]}
    assert research.validate_research_use(use, owner="owner.json", basis=before) == use
    with pytest.raises(ValueError, match="owner differs"):
        research.validate_research_use(use, owner="different.json", basis=before)
    result = research.affected_uses(before, after,
        [{"path": "decision.json", "research_use": use},
         {"path": "independent.json", "research_use": {"owner": "owner.json", "items": ["c"]}},
         {"path": "undeclared.json"}], owner="owner.json")
    assert [entry["path"] for entry in result["uses"]] == ["decision.json"]
    assert result["uses"][0]["changed_items"] == ["b"]
    assert result["undeclared_consumers"] == ["undeclared.json"]


def test_changed_source_nominates_uses_without_claiming_the_statement_changed():
    account = basis(item("a"))
    account["items"][0]["sources"] = [{"path": "evidence.json", "field": "result", "sha256": "a" * 64}]
    consumers = [{"path": "design.json", "research_use": {"owner": "owner.json", "items": ["a"]}}]
    result = research.affected_uses(account, account, consumers, owner="owner.json", changed_sources=["evidence.json"])
    assert result["changed_items"] == []
    assert result["uses"][0]["source_affected_items"] == ["a"]


def test_publication_preserves_owner_and_old_prose_account(tmp_path):
    (tmp_path / "old.md").write_text("Original adopted prose.")
    path = owner(tmp_path, {"permission": "training only", "context_account": {
        "source": {"path": "old.md"}, "sha256": sha256_bytes(b"Original adopted prose.")}})
    account = basis()
    result, args = adopt(tmp_path, path, account)
    metadata = _metadata((tmp_path / path).read_bytes(), path)
    assert result["status"] == "adopted" and result["current"]
    assert metadata["permission"] == "training only"
    assert (tmp_path / path).read_text().endswith("Keep the original governing prose.\n")
    assert metadata["context_account"]["source"] == {"path": path, "field": "research_basis"}
    assert metadata["context_account"]["sha256"] == research.basis_digest(account)
    old = state(tmp_path, path)["research_publications"]["proposal-1"]["previous_account"]
    assert (tmp_path / old["path"]).read_text() == "Original adopted prose."
    assert research.adopt_context_account(tmp_path, path, **args) == result


def test_changed_old_account_needs_verified_retained_history(tmp_path):
    from context_delivery import retain_source
    prior_text = "Original adopted explanation."
    (tmp_path / "old.md").write_text("A changed and unadopted explanation.")
    path = owner(tmp_path, {"context_account": {"source": {"path": "old.md"},
                                               "sha256": sha256_bytes(prior_text.encode())}})
    before = (tmp_path / path).read_bytes()
    with pytest.raises(ValueError, match="previous adopted account is unavailable"):
        adopt(tmp_path, path, basis())
    assert (tmp_path / path).read_bytes() == before
    retain_source(tmp_path, prior_text)
    result, _ = adopt(tmp_path, path, basis())
    assert result["status"] == "adopted"


def test_operation_identity_cannot_be_reused_for_different_inputs(tmp_path):
    path = owner(tmp_path)
    _, args = adopt(tmp_path, path, basis())
    args["proposed_account"] = basis(item("another"))
    before = (tmp_path / path).read_bytes()
    with pytest.raises(ValueError, match="reused with different"):
        research.adopt_context_account(tmp_path, path, **args)
    assert (tmp_path / path).read_bytes() == before


def test_two_writers_with_same_base_cannot_overwrite_each_other(tmp_path):
    path = owner(tmp_path)
    expected = sha256_bytes((tmp_path / path).read_bytes())
    barrier = Barrier(2)

    def publish(number):
        barrier.wait()
        try:
            return research.adopt_context_account(tmp_path, path, operation=f"operation-{number}",
                expected_owner_sha256=expected, expected_account_sha256=None,
                proposed_account=basis(item(f"claim-{number}")))["status"]
        except ValueError as exc:
            return str(exc)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(publish, (1, 2)))
    assert sum(value == "adopted" for value in results) == 1
    assert sum("base changed" in value for value in results) == 1
    publications = state(tmp_path, path)["research_publications"]
    assert sorted(entry["status"] for entry in publications.values()) == ["adopted", "conflict"]
    assert all((tmp_path / entry["proposal"]["path"]).is_file() for entry in publications.values())


@pytest.mark.parametrize("after_replace", [False, True])
def test_crash_before_or_after_publication_recovers_exact_operation(tmp_path, monkeypatch, after_replace):
    path = owner(tmp_path)
    before = (tmp_path / path).read_bytes()
    args = {"operation": "recover-me", "expected_owner_sha256": sha256_bytes(before),
            "expected_account_sha256": None, "proposed_account": basis()}
    original = research._publish_owner

    def crash(target, raw):
        if after_replace:
            original(target, raw)
        raise RuntimeError("simulated process interruption")

    monkeypatch.setattr(research, "_publish_owner", crash)
    with pytest.raises(RuntimeError):
        research.adopt_context_account(tmp_path, path, **args)
    assert state(tmp_path, path)["research_publications"]["recover-me"]["status"] == "pending"
    assert ((tmp_path / path).read_bytes() == before) != after_replace
    monkeypatch.setattr(research, "_publish_owner", original)
    result = research.adopt_context_account(tmp_path, path, **args)
    assert result["status"] == "adopted" and result["current"]
    assert research.adopt_context_account(tmp_path, path, **args) == result


def test_pending_publication_cannot_overwrite_new_external_owner(tmp_path, monkeypatch):
    path = owner(tmp_path)
    original = research._publish_owner
    monkeypatch.setattr(research, "_publish_owner", lambda *_: (_ for _ in ()).throw(RuntimeError()))
    before = (tmp_path / path).read_bytes()
    args = {"operation": "pending", "expected_owner_sha256": sha256_bytes(before),
            "expected_account_sha256": None, "proposed_account": basis()}
    with pytest.raises(RuntimeError):
        research.adopt_context_account(tmp_path, path, **args)
    (tmp_path / path).write_bytes(before + b"New owner instruction.\n")
    changed = (tmp_path / path).read_bytes()
    monkeypatch.setattr(research, "_publish_owner", original)
    with pytest.raises(ValueError, match="conflicts with the current owner"):
        research.adopt_context_account(tmp_path, path, **args)
    assert (tmp_path / path).read_bytes() == changed


def test_retained_corruption_is_not_replaced_with_newer_evidence(tmp_path, monkeypatch):
    path = owner(tmp_path)
    original = research._publish_owner
    monkeypatch.setattr(research, "_publish_owner", lambda *_: (_ for _ in ()).throw(RuntimeError()))
    args = {"operation": "pending", "expected_owner_sha256": sha256_bytes((tmp_path / path).read_bytes()),
            "expected_account_sha256": None, "proposed_account": basis()}
    with pytest.raises(RuntimeError):
        research.adopt_context_account(tmp_path, path, **args)
    entry = state(tmp_path, path)["research_publications"]["pending"]
    (tmp_path / entry["after"]["path"]).write_text("Corrupt snapshot")
    monkeypatch.setattr(research, "_publish_owner", original)
    with pytest.raises(ValueError, match="retained evidence changed"):
        research.adopt_context_account(tmp_path, path, **args)


def test_source_selection_and_incorporation_match_existing_observation(tmp_path):
    path = owner(tmp_path)
    result = {"finding": "The observed effect has two remaining explanations."}
    (tmp_path / "result.json").write_text(json.dumps({"attempts": [{"attempt": 1, "result": result}]}))
    source = {"path": "result.json", "attempt": 1, "sha256": sha256_bytes(canonical_json(result))}
    returned, _ = adopt(tmp_path, path, basis(), incorporates=[source])
    assert returned["status"] == "adopted"
    metadata = _metadata((tmp_path / path).read_bytes(), path)
    assert metadata["context_account"]["incorporates"] == [source]
    wrong = dict(source, sha256="0" * 64)
    before = (tmp_path / path).read_bytes()
    with pytest.raises(ValueError, match="source differs"):
        adopt(tmp_path, path, basis(), operation="incorrect", incorporates=[wrong])
    assert (tmp_path / path).read_bytes() == before


@pytest.mark.parametrize("retry_old_first", [False, True])
def test_selected_source_change_allows_new_explicit_merge_without_restoring_old_evidence(tmp_path, monkeypatch, retry_old_first):
    path = owner(tmp_path)
    (tmp_path / "result.json").write_text(json.dumps({"evidence": "A", "unrelated": 1}))
    source = {"path": "result.json", "field": "evidence", "sha256": sha256_bytes(canonical_json("A"))}
    account = basis()
    account["items"][0]["sources"] = [source]
    args = {"operation": "pending", "expected_owner_sha256": sha256_bytes((tmp_path / path).read_bytes()),
            "expected_account_sha256": None, "proposed_account": account}
    original = research._publish_owner
    monkeypatch.setattr(research, "_publish_owner", lambda *_: (_ for _ in ()).throw(RuntimeError()))
    with pytest.raises(RuntimeError):
        research.adopt_context_account(tmp_path, path, **args)
    (tmp_path / "result.json").write_text(json.dumps({"evidence": "B", "unrelated": 1}))
    monkeypatch.setattr(research, "_publish_owner", original)
    if retry_old_first:
        with pytest.raises(ValueError, match="conflicting proposal"):
            research.adopt_context_account(tmp_path, path, **args)
        assert state(tmp_path, path)["research_publications"]["pending"]["status"] == "conflict"
    fresh = copy.deepcopy(account)
    fresh["items"][0]["sources"][0]["sha256"] = sha256_bytes(canonical_json("B"))
    result, _ = adopt(tmp_path, path, fresh, operation="explicit-merge")
    assert result["status"] == "adopted"
    publications = state(tmp_path, path)["research_publications"]
    assert publications["pending"]["status"] == "conflict"
    assert publications["pending"]["conflict"]["reason"] == "source_changed_before_publication"
    assert json.loads((tmp_path / publications["pending"]["proposal"]["path"]).read_text()) == account
    assert json.loads((tmp_path / "result.json").read_text())["evidence"] == "B"


def test_unrelated_source_edit_keeps_exact_pending_publication_recoverable(tmp_path, monkeypatch):
    path = owner(tmp_path)
    (tmp_path / "result.json").write_text(json.dumps({"evidence": "A", "unrelated": 1}))
    account = basis()
    account["items"][0]["sources"] = [{"path": "result.json", "field": "evidence", "sha256": sha256_bytes(canonical_json("A"))}]
    args = {"operation": "pending", "expected_owner_sha256": sha256_bytes((tmp_path / path).read_bytes()),
            "expected_account_sha256": None, "proposed_account": account}
    original = research._publish_owner
    monkeypatch.setattr(research, "_publish_owner", lambda *_: (_ for _ in ()).throw(RuntimeError()))
    with pytest.raises(RuntimeError):
        research.adopt_context_account(tmp_path, path, **args)
    (tmp_path / "result.json").write_text(json.dumps({"evidence": "A", "unrelated": 2}))
    monkeypatch.setattr(research, "_publish_owner", original)
    assert research.adopt_context_account(tmp_path, path, **args)["status"] == "adopted"


def test_source_race_before_publication_is_retained_conflict_not_success(tmp_path, monkeypatch):
    path = owner(tmp_path)
    (tmp_path / "evidence.md").write_text("Original evidence.")
    before = (tmp_path / path).read_bytes()
    account = basis()
    account["items"][0]["sources"] = [{"path": "evidence.md", "sha256": sha256_bytes(b"Original evidence.")}]
    original = research._save_state

    def change_after_pending_saved(receipt, value):
        original(receipt, value)
        if any(entry["status"] == "pending" for entry in value.get("research_publications", {}).values()):
            (tmp_path / "evidence.md").write_text("Changed before publication.")

    monkeypatch.setattr(research, "_save_state", change_after_pending_saved)
    with pytest.raises(ValueError, match="conflicting proposal"):
        adopt(tmp_path, path, account)
    assert (tmp_path / path).read_bytes() == before
    assert state(tmp_path, path)["research_publications"]["proposal-1"]["status"] == "conflict"


def test_corrupt_retained_source_is_not_misclassified_as_changed_live_evidence(tmp_path, monkeypatch):
    path = owner(tmp_path)
    (tmp_path / "evidence.md").write_text("Original evidence.")
    account = basis()
    account["items"][0]["sources"] = [{"path": "evidence.md", "sha256": sha256_bytes(b"Original evidence.")}]
    args = {"operation": "pending", "expected_owner_sha256": sha256_bytes((tmp_path / path).read_bytes()),
            "expected_account_sha256": None, "proposed_account": account}
    original = research._publish_owner
    monkeypatch.setattr(research, "_publish_owner", lambda *_: (_ for _ in ()).throw(RuntimeError()))
    with pytest.raises(RuntimeError):
        research.adopt_context_account(tmp_path, path, **args)
    retained = state(tmp_path, path)["research_publications"]["pending"]["sources"][0]["retrieval"]
    (tmp_path / retained["path"]).write_text("Corrupted retained evidence.")
    monkeypatch.setattr(research, "_publish_owner", original)
    with pytest.raises(ValueError, match="retained evidence changed"):
        research.adopt_context_account(tmp_path, path, **args)
    assert state(tmp_path, path)["research_publications"]["pending"]["status"] == "pending"
    assert (tmp_path / "evidence.md").read_text() == "Original evidence."


def test_changed_source_after_publication_does_not_relabel_actual_adoption(tmp_path, monkeypatch):
    path = owner(tmp_path)
    (tmp_path / "evidence.md").write_text("Original evidence.")
    account = basis()
    account["items"][0]["sources"] = [{"path": "evidence.md", "sha256": sha256_bytes(b"Original evidence.")}]
    args = {"operation": "published", "expected_owner_sha256": sha256_bytes((tmp_path / path).read_bytes()),
            "expected_account_sha256": None, "proposed_account": account}
    original = research._publish_owner

    def interrupted_after_write(target, raw):
        original(target, raw)
        raise RuntimeError("interrupted after publication")

    monkeypatch.setattr(research, "_publish_owner", interrupted_after_write)
    with pytest.raises(RuntimeError):
        research.adopt_context_account(tmp_path, path, **args)
    published = (tmp_path / path).read_bytes()
    (tmp_path / "evidence.md").write_text("New evidence that needs later interpretation.")
    monkeypatch.setattr(research, "_publish_owner", original)
    assert research.adopt_context_account(tmp_path, path, **args)["status"] == "adopted"
    assert (tmp_path / path).read_bytes() == published


def test_current_use_correction_remains_open_and_receipt_preserves_publication(tmp_path):
    (tmp_path / "finding.md").write_text("This source needs correction.")
    (tmp_path / "work.md").write_text("Affected existing work.")
    correction = {"id": "unresolved", "finding": "finding.md", "affected_sources": ["work.md"],
                  "effect": "repair", "status": "open"}
    path = owner(tmp_path, {"current_use_corrections": [correction]})
    inspect_current_use(tmp_path, path, ["work.md"])
    adopt(tmp_path, path, basis())
    current = inspect_current_use(tmp_path, path, ["work.md"])
    assert current["blocked_ids"] == ["unresolved"]
    assert state(tmp_path, path)["research_publications"]["proposal-1"]["status"] == "adopted"


def test_historical_evidence_does_not_become_an_execution_dependency(tmp_path):
    (tmp_path / "finding.md").write_text("The implementation cannot run again until repaired.")
    (tmp_path / "implementation.md").write_text("A failed implementation that remains useful historical evidence.")
    correction = {"id": "unrepaired", "finding": "finding.md", "affected_sources": ["implementation.md"],
                  "effect": "repair", "status": "open"}
    path = owner(tmp_path, {"current_use_corrections": [correction]})
    assert inspect_current_use(tmp_path, path, [path])["blocked_ids"] == []
    account = basis()
    account["items"][0]["sources"] = [{"path": "implementation.md", "sha256": sha256_bytes((tmp_path / "implementation.md").read_bytes())}]
    adopt(tmp_path, path, account)
    metadata = _metadata((tmp_path / path).read_bytes(), path)
    assert "actual_use" not in metadata["context_account"]
    assert inspect_current_use(tmp_path, path, [path])["blocked_ids"] == []
    assert inspect_current_use(tmp_path, path, ["implementation.md"])["blocked_ids"] == ["unrepaired"]


def test_existing_actual_execution_dependencies_are_preserved(tmp_path):
    (tmp_path / "old.md").write_text("Earlier adopted account.")
    path = owner(tmp_path, {"context_account": {"source": {"path": "old.md"},
        "sha256": sha256_bytes(b"Earlier adopted account."), "actual_use": ["real-task.md"]}})
    adopt(tmp_path, path, basis())
    assert _metadata((tmp_path / path).read_bytes(), path)["context_account"]["actual_use"] == ["real-task.md"]


@pytest.mark.parametrize("selector", ["field", "section"])
def test_selected_incorporation_keeps_its_exact_selector(tmp_path, selector):
    from frontier_references import _selected_text, prepare_adoption_context
    path = owner(tmp_path)
    if selector == "field":
        source_path = "return.json"
        body = json.dumps({"result": {"finding": "Conditional observation."}, "other": "Not incorporated."})
        source = {"path": source_path, "field": "result"}
    else:
        source_path = "return.md"
        body = "# Return\n## Finding\nConditional observation.\n## Other\nNot incorporated.\n"
        source = {"path": source_path, "section": "finding"}
    (tmp_path / source_path).write_text(body)
    source["sha256"] = sha256_bytes(_selected_text(body, source).encode())
    result, _ = adopt(tmp_path, path, basis(), incorporates=[source])
    assert result["status"] == "adopted"
    assert _metadata((tmp_path / path).read_bytes(), path)["context_account"]["incorporates"] == [source]
    prepared = prepare_adoption_context(tmp_path, path)
    assert not any("Incorporated basis changed" in limit for limit in prepared["limitations"])


def test_original_adoption_lock_does_not_obscure_pending_research(tmp_path, monkeypatch):
    (tmp_path / "finding.md").write_text("This source needs correction.")
    (tmp_path / "work.md").write_text("Affected existing work.")
    (tmp_path / "reason.md").write_text("New scoped work addresses the finding.")
    correction = {"id": "repair", "finding": "finding.md", "affected_sources": ["work.md"],
                  "effect": "repair", "status": "open"}
    path = owner(tmp_path, {"current_use_corrections": [correction]})
    inspect_current_use(tmp_path, path, ["work.md"])
    monkeypatch.setattr(research, "_publish_owner", lambda *_: (_ for _ in ()).throw(RuntimeError()))
    with pytest.raises(RuntimeError):
        adopt(tmp_path, path, basis())
    resolved = {**correction, "status": "resolved", "resolution": {"reason": "Repair adopted", "evidence": "reason.md"}}
    with pytest.raises(ValueError, match="unfinished research publication"):
        adopt_current_work(tmp_path, path, corrections=[resolved],
                           replacements=[{"path": "work.md", "contents": "Corrected work."}])
    assert (tmp_path / "work.md").read_text() == "Affected existing work."


def test_replay_old_adoption_after_new_one_stays_historical(tmp_path):
    path = owner(tmp_path)
    account = basis()
    _, first = adopt(tmp_path, path, account)
    account["items"][0]["conditions"] = "A new condition narrows the interpretation."
    second, _ = adopt(tmp_path, path, account, operation="proposal-2")
    before = (tmp_path / path).read_bytes()
    historical = research.adopt_context_account(tmp_path, path, **first)
    assert historical["status"] == "adopted" and not historical["current"]
    assert historical["account_sha256"] != second["account_sha256"]
    assert (tmp_path / path).read_bytes() == before


def test_withdrawal_preserves_reference_identity(tmp_path):
    path = owner(tmp_path)
    adopt(tmp_path, path, basis(item("a"), item("b")))
    with pytest.raises(ValueError, match="retain withdrawn"):
        adopt(tmp_path, path, basis(item("a")), operation="delete")
    account = basis(item("a"), {**item("b"), "status": "withdrawn"})
    result, _ = adopt(tmp_path, path, account, operation="withdraw")
    assert result["status"] == "adopted"
