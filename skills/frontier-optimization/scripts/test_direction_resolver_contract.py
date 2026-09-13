#!/usr/bin/env python3
"""Development-only structural fixtures for the documented direction resolver.

This test does not parse campaign Markdown or ship a runtime resolver. It applies
the documented total order to synthetic facts and declared comparison outcomes.
It checks routing, priority, reuse, and fixture coverage, not agent judgment or
actual invocation counts. Behavioral descriptions are unexecuted test inputs;
passing this module does not close the proposal's behavioral audit findings.
"""

from __future__ import annotations

from copy import deepcopy
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

    # A coverage label is an assessment, not a selected commitment. This input
    # models the comparison's output; it does not calculate an investment order.
    landscape_work = facts.get("selected_landscape_work")
    if landscape_work:
        outcomes = {
            "route-landscape-Q": ("route-landscape Q", "route-landscape-Q"),
            "prerequisite-check": ("local diagnostic", "prerequisite-first-check"),
            "assumption-check": ("local diagnostic", "shared-assumption-check"),
        }
        direction, action = outcomes[landscape_work]
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
            if stop_scope == "candidate":
                if facts.get("same_independently_judged_result") is True:
                    return (
                        11,
                        "local R8",
                        "retire-revision-and-continue-same-B",
                    )
                return 11, "local R8", "retire-candidate-revision-only"
            if stop_scope == "route":
                if facts.get("surviving_route") or facts.get("surviving_action"):
                    return 11, "local R8", "close-route-and-select-surviving-action"
                if facts.get("no_worthwhile_action") is True:
                    return 11, "stop", "full-closeout"
                raise ValueError(
                    "route stop requires a surviving action, selected concern, or campaign closeout"
                )
            if stop_scope != "campaign":
                raise ValueError("evidence-determined stop requires exact stop_scope")
            return 11, "stop", "full-closeout"
        return 11, "strategic replan", "require-REPLAN_READY"

    gate = facts.get("specialized_gate")
    if gate:
        if gate.startswith("focused-Q:"):
            return 12, "focused Q", gate
        return 12, "blocked", f"require-{gate}"

    if routine := facts.get("routine_r8"):
        return 13, "local R8", routine
    raise ValueError("fixture has no applicable resolver condition")


def record_resolution(registry: dict, scenario: dict) -> tuple[int, str, str]:
    """Persist one resolution per immutable evidence-state identity."""

    identity = scenario["evidence_state"]
    if identity in registry:
        raise ValueError(f"evidence state already resolved: {identity}")
    resolution = resolve_persisted_facts(scenario)
    registry[identity] = resolution
    return resolution


def research_dispatch(case: dict) -> str:
    """Return the documented research branch without creating project state."""

    row = case["row"]
    if row == 8:
        return "focused-parent-direct"
    if row != 7:
        return "bypass"
    if case["independent_briefs"] < 2:
        return "landscape-parent-direct"
    return "landscape-parallel"


def adopted_resolver_input(q_result: dict) -> dict:
    """Expose only the adopted normalized Q packet to the resolver."""

    if q_result.get("adopted") is not True or q_result.get("normalized") is not True:
        raise ValueError("resolver input requires an adopted normalized Q result")
    return deepcopy(q_result["normalized_packet"])


def determined_action(entry: dict) -> str | None:
    """Model reuse of an adopted rule, not a Coordinator's fresh preference."""

    rule = entry.get("adopted_rule")
    if rule and rule.get("condition_kind") == "absence-fallback":
        return None
    if rule and set(rule["requires"]) <= set(entry.get("adopted_facts", [])):
        return rule["action"]
    decision = entry.get("adopted_resolution")
    if decision and decision["applicable"]:
        return decision["action"]
    return None


def comparison_required(entry: dict) -> bool:
    """Model invocation after earlier prechecks; this makes no actual calls."""

    return bool(
        entry.get("grounded_challenge")
        or entry.get("unresolved_allocation")
    )


def action_is_ready(action: dict, established: list[str]) -> bool:
    """Model the shared Entry/diagnostic prerequisite rule for one action.

    An unknown being tested is distinct from truth required to execute the test.
    An unrelated landscape label has no role in this dependency check.
    """

    return all(
        action.get(field) is True
        for field in ("sufficient", "authorized", "affordable", "reachable")
    ) and set(action.get("requires", [])) <= set(established)


def test_same_persisted_state_yields_same_exact_resolution() -> None:
    for scenario in load_contract()["scenarios"]:
        expected = scenario["expected"]
        exact = (expected["row"], expected["direction"], expected["action"])
        first = resolve_persisted_facts(scenario)
        second = resolve_persisted_facts(scenario)
        assert first == second == exact, scenario["id"]


def test_resource_boundaries_do_not_promote_internal_limits_into_budget() -> None:
    expected = {
        "planning-estimate": ("Coordinator", "same-B", None, False),
        "batch-operational-limit": ("Coordinator", "same-B", None, False),
        "ungoverned-internal-use": ("Batch", "same-B", None, False),
        "measurement-resource-ceiling": (
            "Measurement-Definition",
            "measurement-revision",
            None,
            False,
        ),
        "governing-campaign-limit": ("Campaign-Budget", "resolver", 5, False),
        "strategic-allocation": ("Selection", "resolver", 10, False),
        "user-boundary": ("User", "ask-for-changed-boundary", None, True),
    }

    cases = load_contract()["resource_boundary_scenarios"]
    assert {case["source"] for case in cases} == set(expected)
    for case in cases:
        actual = case["expected"]
        assert (
            actual["owner"],
            actual["continuation"],
            actual["resolver_row"],
            actual["user_decision"],
        ) == expected[case["source"]], case["id"]


def test_research_dispatch_preserves_fast_and_focused_paths() -> None:
    for case in load_contract()["research_dispatch_scenarios"]:
        assert research_dispatch(case) == case["expected_dispatch"], case["id"]

    by_id = {
        item["id"]: item for item in load_contract()["research_dispatch_scenarios"]
    }
    focused = by_id["focused-row-8-bypasses-role-machinery"]
    assert focused["independent_briefs"] > 1
    assert focused["frame_challenge_requested"] is True
    assert research_dispatch(focused) == "focused-parent-direct"


def test_selected_q_creates_one_new_resolver_run_for_e1() -> None:
    contract = load_contract()
    scenarios = {item["id"]: item for item in contract["scenarios"]}

    for sequence in contract["evidence_state_sequences"]:
        registry: dict = {}
        e0 = scenarios[sequence["e0_scenario"]]
        assert record_resolution(registry, e0) == (
            e0["expected"]["row"],
            e0["expected"]["direction"],
            e0["expected"]["action"],
        )
        with pytest.raises(ValueError, match="already resolved"):
            record_resolution(registry, e0)

        q_result = sequence["q_result"]
        assert adopted_resolver_input(q_result) == q_result["normalized_packet"]
        e1 = sequence["e1"]
        assert e1["evidence_state"] != e0["evidence_state"]
        assert record_resolution(registry, e1) == (
            e1["expected"]["row"],
            e1["expected"]["direction"],
            e1["expected"]["action"],
        )
        assert set(registry) == {e0["evidence_state"], e1["evidence_state"]}


def test_raw_worker_returns_cannot_change_resolver_input() -> None:
    for sequence in load_contract()["evidence_state_sequences"]:
        original = sequence["q_result"]
        changed_raw = deepcopy(original)
        changed_raw["raw_worker_returns"] = ["different", "unadopted", "content"]
        assert adopted_resolver_input(changed_raw) == adopted_resolver_input(original)

    with pytest.raises(ValueError, match="adopted normalized"):
        adopted_resolver_input(
            {"adopted": False, "normalized": True, "normalized_packet": {}}
        )


def test_route_investment_fixtures_resist_conservative_and_aggressive_bias() -> None:
    """Check declared examples, not whether a real resolver avoids bias."""
    cases = {
        item["id"]: item for item in load_contract()["route_investment_scenarios"]
    }

    sufficient = cases["larger-sufficient-test-beats-cheap-underpowered-probe"]
    selected = sufficient["commitments"][sufficient["expected"]["selected"]]
    cheap = sufficient["commitments"]["cheap-probe"]
    assert selected["sufficient"] is True
    assert cheap["cost_rank"] < selected["cost_rank"]
    assert cheap["sufficient"] is False

    breakthrough = cases["admission-route-beats-incumbent-with-no-marginal-value"]
    selected = breakthrough["commitments"][breakthrough["expected"]["selected"]]
    incumbent = breakthrough["commitments"]["mature-incumbent"]
    assert selected["maturity"] == "admission"
    assert selected["final_performance_evidence"] is False
    assert selected["credible_mechanism"] is True
    assert incumbent["marginal_value"] is False

    unsupported = cases["novelty-alone-does-not-win"]
    novel = unsupported["commitments"]["unsupported-novel-route"]
    assert unsupported["expected"]["selected"] != "unsupported-novel-route"
    assert novel["credible_mechanism"] is False
    assert unsupported["expected"]["preserved_routes"][0]["status"] == "conditional"

    transition = cases["transition-maturity-maps-to-existing-owner"]
    assert transition["commitments"][transition["expected"]["selected"]][
        "maturity"
    ] == "transition"
    assert transition["expected"]["next_action"] != "transition"
    assert transition["expected"]["existing_surface"]
    assert transition["expected"]["owner"]

    parallel = cases["parallel-screen-remains-one-selected-allocation"]
    assert len(parallel["commitments"]["parallel-screen-set"]["routes"]) == 2
    assert parallel["expected"]["selected"] == "parallel-screen-set"
    assert parallel["expected"]["next_action"] == "screen"


def test_exact_fixtures_cover_every_row_and_material_branches() -> None:
    scenarios = load_contract()["scenarios"]
    assert {item["expected"]["row"] for item in scenarios} == set(range(1, 14))
    by_id = {item["id"]: item for item in scenarios}
    assert by_id["protected-reserve-zero-spend-replan"]["expected"]["action"] == "prepare-replan-no-spend"
    assert by_id["unresolved-prerequisite-first"]["expected"]["action"] == "prerequisite-first-check"
    assert by_id["evidence-determines-stop"]["expected"]["action"] == "full-closeout"
    assert by_id["candidate-repair-preserves-campaign"]["expected"]["action"] == "retire-revision-and-continue-same-B"
    assert by_id["candidate-stop-without-same-result"]["expected"]["action"] == "retire-candidate-revision-only"
    assert by_id["exact-failure-direct-alternative"]["expected"]["row"] == 13
    assert by_id["current-methods-deferred-with-reopening"]["expected"]["row"] == 13
    assert by_id["repaired-revision-keeps-external-gate"]["expected"]["row"] == 12
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


REPAIR_CASES = load_contract()["route_research_entry_repair"]


def test_missing_prior_order_does_not_make_local_work_a_route_comparison() -> None:
    """Only a route-investment choice or grounded challenge invokes the agent."""

    assert determined_action({}) is None
    assert comparison_required({}) is False
    assert comparison_required({"local_diagnostic": "recorded-order"}) is False
    assert comparison_required({"unresolved_allocation": True}) is True
    assert comparison_required({"grounded_challenge": True}) is True


@pytest.mark.parametrize(
    "pair,variant",
    [
        pytest.param(pair, variant, id=f"{pair['id']}-{variant['name']}")
        for pair in REPAIR_CASES["pairs"]
        for variant in pair["variants"]
    ],
)
def test_revision2_paired_structural_contract(pair: dict, variant: dict) -> None:
    """Exercise declared premises, never grade a real investment decision."""

    entry = {**pair.get("entry", {}), **variant.get("entry", {})}
    facts = {**pair.get("facts", {}), **variant.get("facts", {})}
    assert comparison_required(entry) is variant["expected_comparison"]

    if "action" in variant:
        ready = action_is_ready(variant["action"], variant["established"])
        assert ready is variant["expected_ready"]
        if not ready:
            assert variant["expected_resolution"] is None
            return  # Only this dependent action is ineligible.

    if "q_result" in variant:
        result = variant["q_result"]
        if not result["adopted"] or not result["normalized"]:
            with pytest.raises(ValueError, match="adopted normalized"):
                adopted_resolver_input(result)
            assert variant["expected_resolution"] is None
            return  # No E1 input exists yet.
        assert adopted_resolver_input(result) == result["normalized_packet"]

    resolved = resolve_persisted_facts({"facts": facts})
    assert resolved == tuple(variant["expected_resolution"])
    if not comparison_required(entry):
        assert resolved[2] == determined_action(entry)


def test_revision2_inventory_separates_behavioral_prompts_from_observations() -> None:
    protocol = REPAIR_CASES["behavioral_protocol"]
    pairs = REPAIR_CASES["pairs"]
    assert REPAIR_CASES["evidence_kind"] == "development-only"
    assert protocol["start"] == "normal-coordinator-entry"
    assert protocol["observations"] == []
    assert [pair["id"] for pair in pairs] == [f"S{i}" for i in range(1, 16)]
    settings = REPAIR_CASES["settings"]
    assert {pair["setting"] for pair in pairs} == set(settings)
    assert len({setting["controlled_object"] for setting in settings.values()}) >= 2
    assert len({setting["evidence_medium"] for setting in settings.values()}) >= 2
    for pair in pairs:
        assert pair["behavioral_input"]
        assert len(pair["variants"]) == 2
        assert len({variant["name"] for variant in pair["variants"]}) == 2
        for variant in pair["variants"]:
            assert variant["input_change"]
            assert variant["decision_class"] in protocol["decision_classes"]
    audit = protocol["audit_coverage"]
    assert {"S13"} <= set(audit["AUD-01"])
    assert {"S10", "S15"} <= set(audit["AUD-02"])
    assert {"S1", "S14"} <= set(audit["AUD-03"])
    assert {"S1", "S8", "S11", "S14"} <= set(audit["AUD-04"])


@pytest.mark.parametrize(
    "label", [None, "incomplete", "complete-for-decision", "reopened-route-landscape"]
)
@pytest.mark.parametrize(
    "action_facts,expected",
    [
        ({"routine_r8": "continue-current"}, (13, "local R8", "continue-current")),
        (
            {"local_diagnostic": "unique"},
            (9, "local diagnostic", "selected-local-diagnostic"),
        ),
        (
            {"focused_fact": "deciding-fact"},
            (8, "focused Q", "focused-Q:deciding-fact"),
        ),
        (
            {"selected_landscape_work": "route-landscape-Q"},
            (7, "route-landscape Q", "route-landscape-Q"),
        ),
    ],
)
def test_coverage_label_cannot_select_or_veto_work(
    label: str | None, action_facts: dict, expected: tuple
) -> None:
    assert resolve_persisted_facts(
        {"facts": {**action_facts, "route_set": label}}
    ) == expected
    with pytest.raises(ValueError, match="no applicable resolver condition"):
        resolve_persisted_facts({"facts": {"route_set": label}})


def test_all_row_overlaps_preserve_first_applicable_precedence() -> None:
    representatives = {}
    for scenario in load_contract()["scenarios"]:
        representatives.setdefault(scenario["expected"]["row"], scenario)
    assert set(representatives) == set(range(1, 14))
    for earlier in range(1, 13):
        for later in range(earlier + 1, 14):
            high = representatives[earlier]
            low = representatives[later]
            overlap = {"facts": {**low["facts"], **high["facts"]}}
            assert resolve_persisted_facts(overlap) == resolve_persisted_facts(high), (
                earlier, later
            )


def test_precommitted_switch_exempts_comparison_but_keeps_existing_gates() -> None:
    pair = next(pair for pair in REPAIR_CASES["pairs"] if pair["id"] == "S14")
    satisfied, unsatisfied = pair["variants"]
    entry = {**pair["entry"], **satisfied["entry"]}
    assert determined_action(entry) != entry["previous_action"]
    assert comparison_required(entry) is False
    assert resolve_persisted_facts({"facts": pair["facts"]}) == (
        11, "strategic replan", "require-REPLAN_READY"
    )
    assert determined_action({**entry, **unsatisfied["entry"]}) is None
    # Applicability or allocation uncertainty defeats reuse even after a switch.
    for challenge in ("grounded_challenge", "unresolved_allocation"):
        assert comparison_required({**entry, challenge: True}) is True
    for extra in ({"hard_block": "authority"}, {"budget_block": "exact-blocker"}):
        facts = {**pair["facts"], **extra}
        assert resolve_persisted_facts({"facts": facts})[0] in {2, 5}


def test_absence_fallback_cannot_self_establish_determined_action() -> None:
    entry = {
        "adopted_rule": {
            "requires": [],
            "action": "preserve-frontier",
            "condition_kind": "absence-fallback",
        },
        "unresolved_allocation": True,
    }
    assert determined_action(entry) is None
    assert comparison_required(entry) is True


def test_route_stop_requires_continuation_or_campaign_closeout() -> None:
    by_id = {item["id"]: item for item in load_contract()["scenarios"]}
    assert resolve_persisted_facts(by_id["route-stop-preserves-campaign"]) == (
        11,
        "local R8",
        "close-route-and-select-surviving-action",
    )
    assert resolve_persisted_facts(by_id["route-stop-grounded-concern"]) == (
        7,
        "route-landscape Q",
        "route-landscape-Q",
    )
    assert resolve_persisted_facts(by_id["route-stop-no-worthwhile-action"]) == (
        11,
        "stop",
        "full-closeout",
    )
    with pytest.raises(ValueError, match="surviving action, selected concern"):
        resolve_persisted_facts(
            {"facts": {"evidence_determined": "route-stop", "stop_scope": "route"}}
        )


def test_running_return_and_no_action_recovery_contracts_are_closed() -> None:
    skill_root = Path(__file__).parent.parent
    skill = (skill_root / "SKILL.md").read_text()
    state = (skill_root / "references/campaign-state.md").read_text()
    handoff = (skill_root / "references/user-facing-handoff.md").read_text()
    core = (skill_root / "references/frontier-core.md").read_text()

    assert "A route-scoped result does not complete a continuing task." in skill
    assert "an empty Selection alone neither completes a continuing task nor triggers direction resolution" in state
    assert "A running campaign with no selected next action is transitional" in handoff
    assert "A boundary affecting only one action does not end independent permitted work" in handoff
    assert "An ordinary `continue` is not that event" in core


def test_comparison_can_exit_at_row13_and_be_consumed_without_rerunning() -> None:
    pair = next(pair for pair in REPAIR_CASES["pairs"] if pair["id"] == "S13")
    scenario = {
        "evidence_state": "synthetic:comparison-keeps-action",
        "facts": pair["facts"],
    }
    assert comparison_required(pair["entry"]) is True
    registry: dict = {}
    result = record_resolution(registry, scenario)
    assert result == (13, "local R8", "continue-current")
    # Model the adopted answer after the concern was considered and resolved.
    # This is a state-transition assertion, not an observed agent call count.
    adopted = {"adopted_resolution": {"applicable": True, "action": result[2]}}
    assert comparison_required(adopted) is False
    with pytest.raises(ValueError, match="already resolved"):
        record_resolution(registry, scenario)
    assert len(registry) == 1


@pytest.mark.parametrize("consumer", ["Entry", "row-9-diagnostic"])
def test_independent_action_and_real_dependencies_share_one_rule(consumer: str) -> None:
    pair = next(pair for pair in REPAIR_CASES["pairs"] if pair["id"] == "S15")
    variant = next(item for item in pair["variants"] if item["consumer"] == consumer)
    action = variant["action"]
    established = variant["established"]
    assert pair["facts"]["route_set"] == "incomplete"
    assert action_is_ready(action, established)
    dependent = {
        **action, "requires": [*action["requires"], "untested-staffing-assumption"]
    }
    assert not action_is_ready(dependent, established)
    assert action_is_ready(dependent, [*established, "untested-staffing-assumption"])
    # Changing the subject of a test cannot waive the test's own prerequisites.
    assert action_is_ready(
        {**action, "tests": ["untested-staffing-assumption"]}, established
    )
    for condition in ("sufficient", "authorized", "affordable", "reachable"):
        assert not action_is_ready({**action, condition: False}, established)
    assert not action_is_ready(action, [])


@pytest.mark.parametrize(
    "adopted,normalized", [(False, False), (False, True), (True, False), (True, True)]
)
def test_no_expansion_q_requires_adoption_before_e1_continuation(
    adopted: bool, normalized: bool
) -> None:
    contract = load_contract()
    e0 = next(
        item for item in contract["scenarios"]
        if item["id"] == "incomplete-route-landscape"
    )
    result = {
        "adopted": adopted,
        "normalized": normalized,
        "normalized_packet": {
            "finding": "no-decision-changing-expansion", "limit": "wider-question-open"
        },
        "raw_worker_returns": ["unadopted-winner"],
    }
    registry: dict = {}
    assert record_resolution(registry, e0)[0] == 7
    if not (adopted and normalized):
        with pytest.raises(ValueError, match="adopted normalized"):
            adopted_resolver_input(result)
        assert len(registry) == 1
        return
    normalized_input = adopted_resolver_input(result)
    changed_raw = deepcopy(result)
    changed_raw["raw_worker_returns"] = ["different-unadopted-winner"]
    assert adopted_resolver_input(changed_raw) == normalized_input
    # Copy isolation prevents a consumer from modifying the retained packet.
    normalized_input["finding"] = "consumer-mutated-copy"
    assert result["normalized_packet"]["finding"] == "no-decision-changing-expansion"
    e1 = {
        "evidence_state": "synthetic:no-expansion-adopted",
        "facts": {"route_set": "incomplete", "routine_r8": "continue-current"},
    }
    assert record_resolution(registry, e1) == (13, "local R8", "continue-current")
    with pytest.raises(ValueError, match="already resolved"):
        record_resolution(registry, e1)
    assert len(registry) == 2


def test_equal_metered_cost_and_rationale_quality_are_behavioral_obligations() -> None:
    """Retain the counterexamples without pretending to implement their judge."""

    pairs = {pair["id"]: pair for pair in REPAIR_CASES["pairs"]}
    design, inquiry = (pairs["S8"]["commitments"][name] for name in ("design", "inquiry"))
    assert design["metered_proposals"] == inquiry["metered_proposals"] == 0
    assert design["effort"] != inquiry["effort"]
    assert design["decision_value"] != inquiry["decision_value"]
    assert {v["decision_class"] for v in pairs["S8"]["variants"]} == {
        "decisive-research", "ambiguous-investment"
    }
    supported, invalid = pairs["S12"]["variants"]
    assert supported["expected_resolution"] == invalid["expected_resolution"]
    assert supported["rationale_review"] != invalid["rationale_review"]
    assert set(invalid["invalid_reason_examples"]) == {
        "expired-stop", "novelty-alone", "incumbent-must-fail"
    }
    assert REPAIR_CASES["behavioral_protocol"]["observations"] == []
