#!/usr/bin/env python3
"""Development-only exact fixtures for the documented direction resolver.

This test does not parse campaign Markdown or ship a runtime resolver. It applies
the documented total order to explicit persisted facts and checks exact actions,
priority overlaps, recovery determinism, and Section 18 coverage traceability.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml


FIXTURE = Path(__file__).parent / "fixtures/direction-resolver-scenarios.yaml"


def load_contract() -> dict:
    return yaml.safe_load(FIXTURE.read_text())


def resolve_persisted_facts(scenario: dict) -> tuple[int, str, str]:
    """Return the first row and exact action for one immutable fixture state."""

    facts = scenario["facts"]
    parent = facts.get("parent_change")
    if parent == "unresolved-required-meaning":
        return 1, "blocked", "PARENT_REVIEW_REQUIRED"
    if parent == "adopted-affecting-next-decision":
        return 1, "parent revision", "update-affected-decision"

    hard = facts.get("hard_block")
    if hard:
        if hard == "unconditional-f7":
            return 2, "stop", "full-closeout"
        return 2, "halt", f"{hard}-halt-closeout"

    if blocker := facts.get("coverage_blocker"):
        return 3, "blocked", blocker

    if facts.get("semantic_parent_challenge"):
        return 4, "parent revision", "refer-affected-rule-to-parent-owner"

    budget = facts.get("budget_block")
    if budget:
        outcomes = {
            "exact-blocker": ("blocked", "budget-or-reserve-blocker"),
            "unique-stop": ("stop", "full-closeout"),
            "zero-spend-replan": ("strategic replan", "prepare-replan-no-spend"),
        }
        direction, action = outcomes[budget]
        return 5, direction, action

    validity = facts.get("validity")
    if validity:
        diagnostic = facts.get("validity_diagnostic")
        if not isinstance(diagnostic, dict):
            raise ValueError("validity requires persisted diagnostic eligibility facts")
        if not all(
            diagnostic.get(field) is True
            for field in ("sufficient", "affordable", "reachable")
        ):
            raise ValueError("validity diagnostic did not pass row-5 eligibility")
        non_dominated = diagnostic.get("non_dominated")
        if not isinstance(non_dominated, list) or not non_dominated:
            raise ValueError("validity diagnostic requires non-dominated alternatives")
        if diagnostic.get("selected") not in non_dominated:
            raise ValueError("selected validity diagnostic must be eligible and non-dominated")
        if len(non_dominated) > 1 and not diagnostic.get("selection_reason"):
            raise ValueError("a technical ordering requires its recorded investment rationale")
        return 6, "local diagnostic", "selected-validity-diagnostic"

    route_set = facts.get("route_set")
    if route_set:
        outcomes = {
            "incomplete": ("route-landscape Q", "route-landscape-Q"),
            "reopened-route-landscape": ("route-landscape Q", "route-landscape-Q"),
            "prerequisite-check": ("local diagnostic", "prerequisite-first-check"),
            "assumption-check": ("local diagnostic", "shared-assumption-check"),
        }
        direction, action = outcomes[route_set]
        return 7, direction, action

    if focused := facts.get("focused_fact"):
        return 8, "focused Q", f"focused-Q:{focused}"

    local = facts.get("local_diagnostic")
    if local:
        outcomes = {
            "unique": ("local diagnostic", "selected-local-diagnostic"),
            "recorded-order": ("local diagnostic", "selected-local-diagnostic"),
            "dominated-repeat": ("blocked", "dominated-diagnostic-repeat-blocker"),
        }
        direction, action = outcomes[local]
        return 9, direction, action

    if facts.get("outside_allocation"):
        return 10, "strategic replan", "require-REPLAN_READY-before-dependent-B"

    evidence = facts.get("evidence_determined")
    if evidence:
        if evidence.endswith("-stop"):
            stop_scope = facts.get("stop_scope")
            outcomes = {
                "candidate": (
                    "local R8",
                    "close-candidate-and-plan-in-generation-repair",
                ),
                "route": ("local R8", "close-route-and-select-surviving-action"),
                "campaign": ("stop", "full-closeout"),
            }
            if stop_scope not in outcomes:
                raise ValueError("evidence-determined stop requires exact stop_scope")
            direction, action = outcomes[stop_scope]
            return 11, direction, action
        return 11, "strategic replan", "require-REPLAN_READY"

    gate = facts.get("specialized_gate")
    if gate:
        if gate.startswith("focused-Q:"):
            return 12, "focused Q", gate
        return 12, "blocked", f"require-{gate}"

    if routine := facts.get("routine_r8"):
        return 13, "local R8", routine
    raise ValueError("fixture has no applicable resolver condition")


def test_same_persisted_state_yields_same_exact_resolution() -> None:
    for scenario in load_contract()["scenarios"]:
        expected = scenario["expected"]
        exact = (expected["row"], expected["direction"], expected["action"])
        first = resolve_persisted_facts(scenario)
        second = resolve_persisted_facts(scenario)
        assert first == second == exact, scenario["id"]


def test_exact_fixtures_cover_every_row_and_material_branches() -> None:
    scenarios = load_contract()["scenarios"]
    assert {item["expected"]["row"] for item in scenarios} == set(range(1, 14))
    by_id = {item["id"]: item for item in scenarios}
    assert by_id["protected-reserve-zero-spend-replan"]["expected"]["action"] == "prepare-replan-no-spend"
    assert by_id["unresolved-prerequisite-first"]["expected"]["action"] == "prerequisite-first-check"
    assert by_id["evidence-determines-stop"]["expected"]["action"] == "full-closeout"
    assert by_id["candidate-repair-preserves-campaign"]["expected"]["action"] == "close-candidate-and-plan-in-generation-repair"
    assert by_id["route-stop-preserves-campaign"]["expected"]["action"] == "close-route-and-select-surviving-action"
    assert by_id["specialized-user-authorization"]["expected"]["action"] == "require-execution-V"
    assert by_id["routine-unique-r8"]["expected"]["direction"] == "local R8"


def test_evidence_determined_stop_requires_exact_scope() -> None:
    with pytest.raises(ValueError, match="exact stop_scope"):
        resolve_persisted_facts(
            {"facts": {"evidence_determined": "candidate-stop"}}
        )


def test_candidate_identity_and_campaign_generation_remain_separate() -> None:
    skill_root = Path(__file__).parent.parent
    candidate_contract = (
        skill_root / "references/candidate-lifecycle.md"
    ).read_text()
    resolver_contract = (skill_root / "references/learning-loop.md").read_text()
    assert "It does not by itself increment `campaign_generation`" in candidate_contract
    assert "Every stop consequence has one exact scope" in resolver_contract


def test_section_18_acceptance_coverage_is_complete_and_unique() -> None:
    contract = load_contract()
    scenarios = contract["acceptance_scenarios"]
    numbers = [item["number"] for item in scenarios]
    assert numbers == list(range(1, 59))
    assert all(isinstance(item["name"], str) and item["name"] for item in scenarios)

    fixture_ids = {item["id"] for item in contract["scenarios"]}
    skill_root = Path(__file__).parent.parent
    for item in scenarios:
        target = item["target"]
        kind = target["kind"]
        if kind == "resolver-fixture":
            assert target["id"] in fixture_ids, item
            fixture = next(
                scenario
                for scenario in contract["scenarios"]
                if scenario["id"] == target["id"]
            )
            expected = fixture["expected"]
            assert resolve_persisted_facts(fixture) == (
                expected["row"],
                expected["direction"],
                expected["action"],
            ), item
        elif kind == "contract-assertion":
            source = skill_root / target["path"]
            assert source.is_file(), item
            assert target["marker"] in source.read_text(), item
        elif kind == "regression-test":
            source = skill_root / target["path"]
            assert source.is_file(), item
            assert f"def {target['test']}(" in source.read_text(), item
        else:
            raise AssertionError(f"unknown acceptance target kind: {kind}")


def test_scenario_specific_trajectory_validity_and_budget_facts_are_preserved() -> None:
    by_id = {item["id"]: item for item in load_contract()["scenarios"]}

    checkpoint = by_id["positive-checkpoint-due"]
    assert checkpoint["facts"]["result"] == "positive"
    assert checkpoint["facts"]["checkpoint"] == "due"
    assert resolve_persisted_facts(checkpoint) == (
        12,
        "blocked",
        "require-route-checkpoint",
    )

    unfunded_validity = by_id["unfunded-validity-diagnosis"]
    unfunded_refresh = by_id["unfunded-route-refresh"]
    assert unfunded_validity["facts"]["required_path"] == "validity-diagnostic"
    assert unfunded_validity["facts"]["validity"] == "unresolved-funded"
    assert unfunded_refresh["facts"]["required_path"] == "route-landscape-Q"
    assert unfunded_refresh["facts"]["route_set"] == "incomplete"
    assert resolve_persisted_facts(unfunded_validity)[0] == 5
    assert resolve_persisted_facts(unfunded_refresh)[0] == 5

    maturation = by_id["expected-maturation"]
    assert maturation["facts"]["compatible_increments"] == [0.9, 0.7, 0.5]
    assert maturation["facts"]["prospective_envelope"] == "positive-above-resolution"
    assert maturation["facts"]["within_allocation"] is True
    assert resolve_persisted_facts(maturation) == (
        13,
        "local R8",
        "continue-current-route",
    )

    drift = by_id["protocol-drift-validity-first"]
    floor = by_id["measurement-floor-confirmation"]
    nonunique = by_id["non-unique-validity-diagnostic"]
    assert drift["facts"]["changed_dimensions"] == [
        "evaluator",
        "workload",
        "comparator",
    ]
    assert drift["facts"]["forbidden_inference"] == "trajectory-decline"
    assert floor["facts"]["apparent_change"] == "below-resolution"
    assert floor["facts"]["forbidden_inference"] == "route-exhaustion"
    assert drift["facts"]["validity_diagnostic"]["selected"] == "D-protocol-comparability"
    assert floor["facts"]["validity_diagnostic"]["selected"] == "D-resolution-bound"
    assert nonunique["facts"].get("local_diagnostic") is None
    assert nonunique["facts"]["validity_diagnostic"]["non_dominated"] == [
        "D-validity-a",
        "D-validity-b",
    ]
    assert resolve_persisted_facts(drift)[:2] == (6, "local diagnostic")
    assert resolve_persisted_facts(floor)[:2] == (6, "local diagnostic")
