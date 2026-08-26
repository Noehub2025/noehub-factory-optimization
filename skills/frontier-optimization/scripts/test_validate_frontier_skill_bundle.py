#!/usr/bin/env python3
"""Regression tests for the repository-local Optimization workflow validator."""

from __future__ import annotations

import importlib.util
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("validate_frontier_skill_bundle.py")
SPEC = importlib.util.spec_from_file_location("validate_frontier_skill_bundle", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

REFLECTION_FIELDS = (
    "Decision addressed",
    "Technical hypothesis",
    "Hypothesis result",
    "Evidence validity",
    "Mechanism inference",
    "Attribution limit",
    "R&D implication",
    "Measurement implication",
    "Progress interpretation",
    "Constraint inference",
    "Maximum supported conclusion",
    "Claim boundary",
    "Diagnostic alternatives considered",
    "Diagnostic decision",
)
REFLECTION_REQUIRED_MARKERS = {
    "planning-records.md": (
        "`Decision hypothesis` and `Expected observation` are the pre-spend owners",
        "An upstream T or W provides only mechanism context explicitly inherited by B and cannot replace the B-level decision",
        "The reflection cannot replace either source with a result-shaped story",
        "adaptive-exposure lineage across attempts and B/E records",
        "complete parent-owned value or vector",
        "every parent-owned hard constraint and guardrail",
        "E records one evaluated result, not a technical hypothesis, mechanism conclusion, trend, or route verdict",
        "evidence-bounded mechanism inference",
        "An improved proxy or aggregate does not establish route progress",
    ),
    "learning-loop.md": (
        "Establish validity in this order: implementation, measurement, then comparison validity",
        "Judge that unchanged pre-work hypothesis",
        "For a terminal B, recover the controlling decision hypothesis from that B",
        "A valid whole-treatment comparison may support that the bounded package caused the observed local effect",
        "Component contribution",
        "needs a separating intervention, ablation, trace, or equivalent evidence",
        "does not invalidate a valid package-level result or block another bounded reversible attempt",
        "Diagnose it only when the pending decision depends on choosing among those internal explanations",
        "A limitation that does not prevent the addressed decision remains a future-use note",
        "Distinguish a saturated comparator-derived score from exhaustion of the evaluator itself",
        "a direct reversible attempt may be preferable to separate diagnosis",
        "it has no mandatory finding enum",
        "This section is the only direction resolver",
        "Apply the rows from 1 through 13 exactly once",
        "Perform no additional research, diagnosis, or review",
        "Research before a formal direction choice",
        "industrial implementations, academic evidence, community reports or artifacts",
        "Unique dominance is sufficient, not necessary, for a technical choice",
        "Selection must apply its hypothesis result, mechanism inference, attribution limit, R&D implication, measurement implication, maximum conclusion, diagnostic alternatives, and recorded diagnostic ordering without strengthening or reinterpretation",
        "Keep every earlier Outcome Reflection immutable under its recorded project evidence",
        "These forms create no additional Q, research, review, repeated B, synthetic E, metric, or trajectory artifact",
        "complete [Fresh-context Reflection analysis](reflection-analysis.md) before showing that analyst",
        "A precommitted stop can determine the action while leaving the technical interpretation unchanged",
    ),
    "reflection-analysis.md": (
        "Dispatch one analyst with no inherited conversation",
        "Before reading the calibration contrasts below, draft the final candidate content",
        "Insufficient component separation limits attribution; it does not erase valid package-level or implementation learning",
        "fixes the accepted research content before restoring operational context",
    ),
    "reflection-calibration.md": (
        "They calibrate evidence use; they are not prose templates",
        "Whole package and component contribution",
        "Implemented pathway and performance effect",
        "Research meaning and a precommitted stop",
    ),
    "campaign-cycle.md": (
        "recover the exact technical hypothesis and expected observation fixed before work",
        "A valid controlled whole-package comparison may support that the bounded package caused the local result without ablation",
        "claiming that a component was active, necessary, dominant, or numerically responsible needs separating evidence",
        "Incompatible, stale, invalid, or unresolved E remains campaign evidence but cannot form an ordered trajectory",
        "A single proxy improvement cannot establish route success",
        "Selection applies the reflection; it cannot rebuild the evidence sequence, strengthen the mechanism granularity",
        "This interpretation step creates no trajectory record, diagnosis, research task, review, B, spend, or authority by itself",
        "An attribution limit is non-blocking unless the pending decision depends on distinguishing the internal explanations",
        "saturation of one comparator-derived score does not prove evaluator exhaustion",
        "One-shot, administrative, and implementation-only work use the applicable `not-applicable` fields",
        "Older OR records remain immutable under their source",
        "Use only [Integrated direction resolver](learning-loop.md#integrated-direction-resolver)",
        "another evidence round is permitted only when resolver row 7 or row 8 selects it",
        "Until an unchanged review is adopted as `REPLAN_READY`",
    ),
    "campaign-state.md": (
        "Selection applies the reviewed Entry evidence or latest controlling reflection; it does not reinterpret validity, technical learning, route eligibility",
        "exactly one persisted first applicable resolver row and deterministic resolution",
        "Routine row 13 adds no research, diagnosis, or review",
        "routine work cannot consume protected reserve",
    ),
}


def reflection_contract_findings(skills_root: Path) -> list[str]:
    references = skills_root / "frontier-optimization/references"
    documents = {
        name: (references / name).read_text()
        for name in REFLECTION_REQUIRED_MARKERS
    }
    findings: list[str] = []
    entrypoint = (skills_root / "frontier-optimization/SKILL.md").read_text()
    if "references/reflection-analysis.md" not in MODULE.LINK_PATTERN.findall(entrypoint):
        findings.append("frontier-optimization SKILL omits fresh-context Reflection routing")
    all_markdown = [path.read_text() for path in skills_root.rglob("*.md")]
    for field in REFLECTION_FIELDS:
        # Selection cites the controlling decision; that pointer is not an owner.
        count = sum(
            text.count(f"- {field}: <")
            - text.count(f"- {field}: <controlling Reflection or Entry,")
            for text in all_markdown
        )
        if count != 1:
            findings.append(f"{field} has {count} canonical template owners")

    learning = documents["learning-loop.md"]
    anchor = "```markdown\nOutcome Reflection:\n"
    if anchor not in learning:
        findings.append("Outcome Reflection template is missing")
    else:
        template = learning.split(anchor, 1)[1].split("```", 1)[0]
        for field in REFLECTION_FIELDS:
            if f"- {field}: <" not in template:
                findings.append(f"Outcome Reflection omits {field}")
        match = re.search(r"^- Hypothesis result: <([^,>]+)", template, re.MULTILINE)
        observed = {value.strip() for value in match.group(1).split("|")} if match else set()
        expected = {"supported", "contradicted", "inconclusive", "not-applicable"}
        if observed != expected:
            findings.append(f"hypothesis results are {sorted(observed)}")

    for name, markers in REFLECTION_REQUIRED_MARKERS.items():
        for marker in markers:
            if marker not in documents[name]:
                findings.append(f"{name} omits {marker}")
    combined = documents["learning-loop.md"] + documents["campaign-cycle.md"]
    for prohibited in ("review_kind: trajectory", "Trajectory record:"):
        if prohibited in combined:
            findings.append(f"new trajectory process found: {prohibited}")
    return findings


RESOLVER_ROW_MARKERS = {
    1: "An unresolved parent requirement or adopted revision affects the next decision",
    2: "safety, legality, authority, accounting, explicit campaign-scope unconditional F7 stop, or halt",
    3: "terminal B or E lacks coverage",
    4: "parent-owned objective, Representation, Slot H measurement meaning, R8 rule, permitted scope, or claim ceiling",
    5: "without consuming protected reserve",
    6: "Implementation, measurement, or comparison validity",
    7: "plausible route set is incomplete",
    8: "one named external or repository fact",
    9: "more than one live causal explanation",
    10: "spend outside the unchanged reviewed route allocation",
    11: "Existing valid evidence and R8",
    12: "crosses another recorded B, T replacement boundary, checkpoint, integration, promotion",
    13: "No route, progress, Budget, parent, context, or decision-window condition above applies",
}


def direction_resolver_contract_findings(skills_root: Path) -> list[str]:
    references = skills_root / "frontier-optimization/references"
    markdown = {path.name: path.read_text() for path in references.glob("*.md")}
    learning = markdown["learning-loop.md"]
    findings: list[str] = []

    heading = "## Integrated direction resolver"
    owners = [name for name, text in markdown.items() if heading in text]
    if owners != ["learning-loop.md"]:
        findings.append(f"direction resolver owners are {owners}")
        return findings

    section = learning.split(heading, 1)[1].split("### Research before a formal direction choice", 1)[0]
    rows = {
        int(match.group(1)): match.group(0)
        for match in re.finditer(r"^\| (\d+) \| .* \|$", section, re.MULTILINE)
    }
    if list(sorted(rows)) != list(range(1, 14)):
        findings.append(f"resolver priorities are {sorted(rows)}")
    for priority, marker in RESOLVER_ROW_MARKERS.items():
        if marker not in rows.get(priority, ""):
            findings.append(f"resolver row {priority} omits {marker}")

    required = {
        "learning-loop.md": (
            "Apply the rows from 1 through 13 exactly once",
            "The first applicable row governs; no later row may override it",
            "Every stop consequence has one exact scope",
            "Unknown cost of this stage or its unavoidable commitments is not affordable",
            "Do not ask the user to choose a technical diagnostic",
            "The same diagnostic class cannot repeat from the same evidence-state identity",
            "Make no trajectory, route, or parent inference",
            "one additional evidence-completion round only through row 7 or row 8",
            "further retrieval is unlikely to change the current allocation",
            "Entry adoption fixes one project decision root",
            "Selected, authorized, acknowledged, or execution-started B records continue under their exact project chain",
        ),
        "campaign-state.md": (
            "first applicable row from learning-loop.md",
            "do not introduce a separate uniqueness test here",
            "Routine row 13 adds no research, diagnosis, or review",
            "does not reinterpret validity, technical learning, route eligibility, progress, constraint meaning, diagnostic alternatives, dominance, affected scope, or surviving authority",
            "Affected scope",
            "Surviving authority",
            "Project provenance",
        ),
        "entry-review.md": (
            "Budget, prior and unknown consumption, reservations and protected reserve agree",
            "The current selection follows its controlling Reflection and the sole resolver",
            "`project-decision` content root and an empty payload",
            "entry-review-legacy.md",
        ),
        "campaign-cycle.md": (
            "This file adds no direction table, fallback priority, research-first exception, or post-resolver R8 override",
            "another evidence round is permitted only when resolver row 7 or row 8 selects it",
            "Until an unchanged review is adopted as `REPLAN_READY`",
            "apply its persisted row, exact next action, and later-spend gates without running the resolver again",
        ),
        "frontier-core.md": (
            "Semantic parent challenge",
            "Project provenance",
            "An unresolved or unaffordable validity, implementation, or local-mechanism diagnostic is not a semantic parent challenge",
            "A running B preserves its exact execution inputs and actual permission",
        ),
        "closeout-and-claims.md": (
            "Preserve final direction state",
            "Do not rewrite an older Outcome Reflection",
            "latest first applicable direction-resolver row",
            "each surviving project decision root, parent chain",
        ),
        "packaging-and-recovery.md": (
            "Use `verify-handoff` to read the exact records from Git",
            "Workflow deployment files, environments,\ncaches, and unrelated work are not handoff members",
            "Restore a missing dependency at its owning location",
        ),
    }
    for name, markers in required.items():
        for marker in markers:
            if marker not in markdown[name]:
                findings.append(f"{name} omits {marker}")

    if learning.count("Unique dominance is sufficient, not necessary, for a technical choice") != 1:
        findings.append("technical diagnostic ordering rule is not canonical")
    return findings


class FrontierSkillBundleTests(unittest.TestCase):
    def test_outcome_reflection_has_one_hypothesis_centered_canonical_owner(self) -> None:
        skills_root = SCRIPT.parents[2]
        self.assertEqual([], reflection_contract_findings(skills_root))

    def test_reflection_inference_is_useful_bounded_and_non_blocking(self) -> None:
        skills_root = SCRIPT.parents[2]
        mutations = (
            (
                "frontier-optimization/references/learning-loop.md",
                "A valid whole-treatment comparison may support that the bounded package caused the observed local effect",
                "A valid whole-treatment comparison cannot support a package effect without ablation",
            ),
            (
                "frontier-optimization/references/learning-loop.md",
                "does not invalidate a valid package-level result or block another bounded reversible attempt",
                "invalidates the package result and blocks another attempt",
            ),
            (
                "frontier-optimization/references/campaign-cycle.md",
                "An attribution limit is non-blocking unless the pending decision depends on distinguishing the internal explanations",
                "An attribution limit always requires diagnosis before later work",
            ),
            (
                "frontier-optimization/references/campaign-state.md",
                "",
                "\n".join(f"- {field}: <duplicate>" for field in REFLECTION_FIELDS),
            ),
        )
        for relative, old, new in mutations:
            with self.subTest(relative=relative, replacement=new):
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory) / "skills"
                    shutil.copytree(
                        skills_root,
                        root,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
                    )
                    path = root / relative
                    text = path.read_text()
                    if old:
                        self.assertIn(old, text)
                    path.write_text(text.replace(old, new, 1) if old else text + new)
                    self.assertNotEqual([], reflection_contract_findings(root))

    def test_direction_resolver_has_one_complete_total_order(self) -> None:
        skills_root = SCRIPT.parents[2]
        self.assertEqual([], direction_resolver_contract_findings(skills_root))

    def test_direction_resolver_rejects_priority_drift_overresearch_and_reserve_leakage(self) -> None:
        live_root = SCRIPT.parents[2]
        mutations = (
            (
                "frontier-optimization/references/learning-loop.md",
                "| 5 | No sufficient next observation",
                "| 15 | No sufficient next observation",
            ),
            (
                "frontier-optimization/references/campaign-state.md",
                "Routine row 13 adds no research, diagnosis, or review",
                "Routine row 13 adds research for confidence",
            ),
            (
                "frontier-optimization/references/entry-review.md",
                "Budget, prior and unknown consumption, reservations and protected reserve agree",
                "Ignore earlier spending and permit routine use of protected reserve",
            ),
        )
        for relative, old, new in mutations:
            with self.subTest(relative=relative):
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory) / "skills"
                    shutil.copytree(
                        live_root,
                        root,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
                    )
                    path = root / relative
                    text = path.read_text()
                    self.assertIn(old, text)
                    path.write_text(text.replace(old, new, 1))
                    self.assertNotEqual([], direction_resolver_contract_findings(root))

    def test_live_expected_skill_bundle_is_valid_and_content_addressed(self) -> None:
        skills_root = SCRIPT.parents[2]
        result = MODULE.validate(skills_root)
        self.assertTrue(result["bundle_ready"], result["findings"])
        self.assertEqual(set(result["expected_skills"]), set(MODULE.EXPECTED_SKILLS))
        self.assertEqual(len(result["bundle_sha256"]), 64)
        self.assertGreater(len(result["source_manifest"]), 20)

    def test_bundle_validator_owns_common_skill_description_checks(self) -> None:
        live_root = SCRIPT.parents[2]
        for invalid_description in ("", "contains <placeholder>", "x" * 1025):
            with self.subTest(description=invalid_description[:24]):
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory) / "skills"
                    shutil.copytree(
                        live_root,
                        root,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
                    )
                    skill = root / "frame-optimization/SKILL.md"
                    text = skill.read_text()
                    text = re.sub(
                        r"^description:.*$",
                        f"description: {invalid_description}",
                        text,
                        count=1,
                        flags=re.MULTILINE,
                    )
                    skill.write_text(text)
                    result = MODULE.validate(root)
                    self.assertIn(
                        "SKILL_DESCRIPTION_INVALID",
                        {item["code"] for item in result["findings"]},
                    )

    def test_finding_effect_owner_cannot_fail_open_or_create_identity_churn(self) -> None:
        live_root = SCRIPT.parents[2]
        mutations = (
            (
                "frontier-optimization/scripts/finding_effects.py",
                "return BLOCK",
                "return ADVISORY",
            ),
            (
                "frontier-optimization/references/finding-effects.md",
                "create no replacement identity, B, V, review, or authorization",
                "create a replacement B and review for every advisory",
            ),
        )
        for relative, old, new in mutations:
            with self.subTest(relative=relative):
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory) / "skills"
                    shutil.copytree(
                        live_root,
                        root,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
                    )
                    path = root / relative
                    text = path.read_text()
                    self.assertIn(old, text)
                    path.write_text(text.replace(old, new, 1))
                    result = MODULE.validate(root)
                    self.assertIn(
                        "FINDING_EFFECT_CONTRACT_INVALID",
                        {item["code"] for item in result["findings"]},
                    )

    def test_missing_framing_coordinator_is_rejected(self) -> None:
        live_root = SCRIPT.parents[2]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "skills"
            shutil.copytree(
                live_root,
                root,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
            )
            shutil.rmtree(root / "frame-optimization")
            result = MODULE.validate(root)
            self.assertIn(
                {
                    "code": "SKILL_MISSING",
                    "effect": "block",
                    "detail": "frame-optimization",
                },
                result["findings"],
            )

    def test_sixth_claim_reviewer_is_rejected(self) -> None:
        live_root = SCRIPT.parents[2]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "skills"
            shutil.copytree(
                live_root,
                root,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
            )
            extra = root / "review-frontier-claims"
            extra.mkdir()
            result = MODULE.validate(root)
            self.assertIn(
                "EXTRA_REVIEWER_SKILL",
                {item["code"] for item in result["findings"]},
            )
            self.assertIn(
                "UNEXPECTED_SKILL",
                {item["code"] for item in result["findings"]},
            )

    def test_worker_cannot_disable_implicit_invocation(self) -> None:
        live_root = SCRIPT.parents[2]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "skills"
            shutil.copytree(live_root, root, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            metadata = root / "run-frontier-batch/agents/openai.yaml"
            metadata.write_text(metadata.read_text().replace("true", "false"))
            result = MODULE.validate(root)
            self.assertIn(
                "INVOCATION_POLICY_INVALID",
                {item["code"] for item in result["findings"]},
            )

    def test_framing_coordinator_cannot_enable_implicit_invocation(self) -> None:
        live_root = SCRIPT.parents[2]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "skills"
            shutil.copytree(live_root, root, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            metadata = root / "frame-optimization/agents/openai.yaml"
            metadata.write_text(metadata.read_text().replace("false", "true"))
            result = MODULE.validate(root)
            self.assertIn(
                "INVOCATION_POLICY_INVALID",
                {item["code"] for item in result["findings"]},
            )

    def test_host_absolute_path_is_not_portable(self) -> None:
        live_root = SCRIPT.parents[2]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "skills"
            shutil.copytree(live_root, root, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            skill = root / "research-frontier/SKILL.md"
            skill.write_text(skill.read_text() + "\nRead /Users/example/private.md.\n")
            result = MODULE.validate(root)
            self.assertIn(
                "HOST_PATH_NOT_PORTABLE",
                {item["code"] for item in result["findings"]},
            )

    def test_dispatch_callers_must_use_the_shared_state_machine(self) -> None:
        live_root = SCRIPT.parents[2]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "skills"
            shutil.copytree(live_root, root, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            cycle = root / "frontier-optimization/references/campaign-cycle.md"
            cycle.write_text(cycle.read_text().replace("batch-interface.md#dispatch-state-machine", "batch-interface.md"))
            result = MODULE.validate(root)
            self.assertIn(
                "DISPATCH_INTERFACE_POINTER_MISSING",
                {item["code"] for item in result["findings"]},
            )

    def test_campaign_router_must_expose_result_adoption(self) -> None:
        live_root = SCRIPT.parents[2]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "skills"
            shutil.copytree(live_root, root, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            coordinator = root / "frontier-optimization/SKILL.md"
            coordinator.write_text(coordinator.read_text().replace("references/result-adoption.md", "references/campaign-cycle.md"))
            result = MODULE.validate(root)
            self.assertIn(
                "CAMPAIGN_ACTION_ROUTER_INVALID",
                {item["code"] for item in result["findings"]},
            )

    def test_reviewer_must_use_the_shared_branch_registry(self) -> None:
        live_root = SCRIPT.parents[2]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "skills"
            shutil.copytree(live_root, root, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            reviewer = root / "review-frontier/SKILL.md"
            reviewer.write_text(reviewer.read_text().replace(MODULE.REVIEW_BRANCH_POINTER, ""))
            result = MODULE.validate(root)
            self.assertIn(
                "REVIEW_BRANCH_REGISTRY_INVALID",
                {item["code"] for item in result["findings"]},
            )

    def test_branch_registry_must_cover_every_review_kind(self) -> None:
        live_root = SCRIPT.parents[2]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "skills"
            shutil.copytree(live_root, root, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            registry = root / "frontier-optimization/references/review-branches.md"
            registry.write_text(registry.read_text().replace("claim-review.md", "learning-loop.md"))
            result = MODULE.validate(root)
            self.assertIn(
                "REVIEW_BRANCH_REGISTRY_INVALID",
                {item["code"] for item in result["findings"]},
            )

    def test_both_coordinators_must_use_the_shared_handoff(self) -> None:
        live_root = SCRIPT.parents[2]
        for relative, pointer in MODULE.STAGE_HANDOFF_REQUIREMENTS.items():
            with self.subTest(relative=relative), tempfile.TemporaryDirectory() as directory:
                root = Path(directory) / "skills"
                shutil.copytree(live_root, root, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
                source = root / relative
                text = source.read_text()
                self.assertIn(pointer, MODULE.LINK_PATTERN.findall(text))
                source.write_text(text.replace(pointer, "missing-handoff.md"))
                result = MODULE.validate(root)
                self.assertIn(
                    "STAGE_HANDOFF_POINTER_MISSING",
                    {item["code"] for item in result["findings"]},
                )

    def test_split_contract_routes_remain_required(self) -> None:
        live_root = SCRIPT.parents[2]
        routes = (
            ("frontier-optimization/references/frontier-core.md", "finding-effects.md", "FINDING_EFFECT_CONTRACT_INVALID"),
            ("frontier-optimization/references/entry-review.md", "entry-review-legacy.md", "FINDING_EFFECT_CONTRACT_INVALID"),
            ("frontier-optimization/references/batch-interface.md", "batch-packet-format.md", "RESULT_CONTRACT_INVALID"),
            ("frontier-optimization/references/batch-interface.md", "batch-result.md", "RESULT_CONTRACT_INVALID"),
            ("run-frontier-batch/SKILL.md", "../frontier-optimization/references/batch-evaluation.md", "RESULT_CONTRACT_INVALID"),
            ("frontier-optimization/references/review-branches.md", "replan-review.md", "REVIEW_BRANCH_REGISTRY_INVALID"),
        )
        for relative, pointer, expected in routes:
            with self.subTest(relative=relative, pointer=pointer), tempfile.TemporaryDirectory() as directory:
                root = Path(directory) / "skills"
                shutil.copytree(live_root, root, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
                source = root / relative
                text = source.read_text()
                self.assertIn(pointer, MODULE.LINK_PATTERN.findall(text))
                source.write_text(text.replace(pointer, "missing-contract.md"))
                result = MODULE.validate(root)
                self.assertIn(expected, {item["code"] for item in result["findings"]})

    def test_boundary_preserving_continuation_callers_use_one_contract(self) -> None:
        live_root = SCRIPT.parents[2]
        result = MODULE.validate(live_root)
        self.assertTrue(result["bundle_ready"], result["findings"])
        for relative, pointer in MODULE.BOUNDARY_CONTINUATION_REQUIREMENTS.items():
            with self.subTest(relative=relative):
                self.assertIn(pointer, (live_root / relative).read_text())

    def test_missing_boundary_preserving_continuation_pointer_is_rejected(self) -> None:
        live_root = SCRIPT.parents[2]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "skills"
            shutil.copytree(
                live_root,
                root,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
            )
            worker = root / "run-frontier-batch/SKILL.md"
            pointer = MODULE.BOUNDARY_CONTINUATION_REQUIREMENTS[
                "run-frontier-batch/SKILL.md"
            ]
            worker.write_text(worker.read_text().replace(pointer, ""))
            result = MODULE.validate(root)
            self.assertIn(
                "BOUNDARY_CONTINUATION_POINTER_MISSING",
                {item["code"] for item in result["findings"]},
            )

    def test_entry_identity_chain_is_one_source_derived_contract(self) -> None:
        live_root = SCRIPT.parents[2]
        result = MODULE.validate(live_root)
        self.assertTrue(result["bundle_ready"], result["findings"])
        for relative, markers in MODULE.ENTRY_IDENTITY_CONTRACT_REQUIREMENTS.items():
            text = (live_root / relative).read_text()
            for marker in markers:
                with self.subTest(relative=relative, marker=marker):
                    self.assertIn(marker, text)

    def test_packet_and_result_share_one_experiment_contract(self) -> None:
        live_root = SCRIPT.parents[2]
        result = MODULE.validate(live_root)
        self.assertTrue(result["bundle_ready"], result["findings"])
        for relative, markers in MODULE.RESULT_CONTRACT_REQUIREMENTS.items():
            text = (live_root / relative).read_text()
            for marker in markers:
                with self.subTest(relative=relative, marker=marker):
                    self.assertIn(marker, text)

    def test_missing_packet_to_result_preflight_is_rejected(self) -> None:
        live_root = SCRIPT.parents[2]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "skills"
            shutil.copytree(
                live_root,
                root,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
            )
            validator = root / "frontier-optimization/scripts/validate_batch_packet.py"
            validator.write_text(
                validator.read_text().replace(
                    '"result_contract_compatibility": (',
                    '"removed_result_contract_check": (',
                )
            )
            result = MODULE.validate(root)
            self.assertIn(
                "RESULT_CONTRACT_INVALID",
                {item["code"] for item in result["findings"]},
            )

    def test_self_declared_binding_contract_cannot_replace_source_derivation(self) -> None:
        live_root = SCRIPT.parents[2]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "skills"
            shutil.copytree(
                live_root,
                root,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
            )
            adoption = root / "frontier-optimization/scripts/validate_authorization_adoption.py"
            adoption.write_text(adoption.read_text().replace("AUTHORIZATION_TARGET_NOT_DERIVED", "DECLARED_BINDING_ACCEPTED"))
            result = MODULE.validate(root)
            self.assertIn(
                "ENTRY_IDENTITY_CONTRACT_INVALID",
                {item["code"] for item in result["findings"]},
            )

    def test_boundary_preserving_continuation_is_task_neutral_and_fail_closed(self) -> None:
        skills_root = SCRIPT.parents[2]
        batch_interface = (
            skills_root / "frontier-optimization/references/batch-interface.md"
        ).read_text()
        section = batch_interface.split("## Boundary-preserving continuation", 1)[1].split(
            "## Batch packet", 1
        )[0]
        semantic_markers = (
            "A B is one bounded objective, authority, evidence, and spend envelope",
            "Apply [Charging and publication](#charging-and-publication)",
            "The worker owns a mutable work breakdown",
            "One execution-start may support several sequential worker invocations",
            "preserve and count any limited effect already incurred",
            "A realization is review-ready only when the complete B output",
            "When implementation review returns a fidelity finding",
            "Byte-identical output alone does not establish that two operations are the same event",
            "After authoritative publication or the immutable result",
        )
        for marker in semantic_markers:
            with self.subTest(marker=marker):
                self.assertIn(marker, section)
        for task_specific_term in ("pytest", "JUnit", "Kaggle", "B027", "B028"):
            with self.subTest(task_specific_term=task_specific_term):
                self.assertNotIn(task_specific_term, section)

    def test_prepublication_fidelity_repair_is_parent_first_across_roles(self) -> None:
        skills_root = SCRIPT.parents[2]
        documents = {
            "lifecycle": (
                skills_root
                / "frontier-optimization/references/candidate-lifecycle.md"
            ).read_text(),
            "worker": (skills_root / "frontier-optimization/references/batch-code-execution.md").read_text(),
            "entry": (
                skills_root / "frontier-optimization/references/entry-review.md"
            ).read_text(),
            "implementation_review": (
                skills_root
                / "frontier-optimization/references/implementation-review.md"
            ).read_text(),
            "learning": (
                skills_root / "frontier-optimization/references/learning-loop.md"
            ).read_text(),
        }
        required = {
            "lifecycle": (
                "Apply Batch Interface's continuation rule to fidelity or design findings",
                "inventory identity establishes content equality, not whether a new budget event occurred",
            ),
            "worker": (
                "Apply Batch Interface's continuation rule to fidelity findings, design revisions, and failed retries",
                "it proves content equality, not a free new proposal",
            ),
            "entry": (
                "use the bound parent as the source of budget, permission, and acceptance rules",
                "rather than inventing parallel policies",
                "batch-interface.md#charging-and-publication",
            ),
            "implementation_review": (
                "complete all-pass realization ready for prepublication review",
                "IMPLEMENTATION_READY` permits only authoritative publication",
            ),
            "learning": (
                "A pre-publication engineering-check failure has not entered this resolver path",
            ),
        }
        for role, markers in required.items():
            for marker in markers:
                with self.subTest(role=role, marker=marker):
                    self.assertIn(marker, documents[role])

        self.assertNotIn(
            "Implement one observable slice, then use the bound "
            "`validate_candidate_package.py --write-inventory`",
            documents["worker"],
        )

    def test_measurement_use_and_vacuity_rules_are_consistent_across_gates(self) -> None:
        skills_root = SCRIPT.parents[2]
        canonical = (
            skills_root / "frame-optimization/references/representation-contracts.md"
        ).read_text()
        problem_review = (skills_root / "review-optimization/SKILL.md").read_text()
        representation_review = (skills_root / "review-representation/SKILL.md").read_text()
        planning = (
            skills_root
            / "frontier-optimization/references/entry-and-planning.md"
        ).read_text()
        entry_review = (
            skills_root / "frontier-optimization/references/entry-review.md"
        ).read_text()
        lifecycle = (
            skills_root / "frontier-optimization/references/candidate-lifecycle.md"
        ).read_text()
        adoption = (
            skills_root / "frontier-optimization/references/result-adoption.md"
        ).read_text()

        canonical_rule = (
            "every legal result maps to the same allowed next action"
        )
        for document in (canonical, problem_review, planning):
            with self.subTest(document=document[:80]):
                self.assertIn(canonical_rule, document)

        self.assertIn("Test the proxy's fitness for the intended consequence", entry_review)
        self.assertIn("Preserve validity and claim limits", entry_review)

        self.assertIn("canonical R8 vacuity definition", representation_review)
        self.assertIn("headroom, noise, resolution", canonical)
        self.assertIn("keep formal Slot H measurement, E", planning)
        self.assertIn("Diagnostic-only exception", lifecycle)
        self.assertIn("create no E", adoption)
        for prohibited_consequence in (
            "integration",
            "incumbent use",
            "promotion",
            "submission",
            "strength",
        ):
            with self.subTest(prohibited_consequence=prohibited_consequence):
                self.assertIn(prohibited_consequence, lifecycle)


if __name__ == "__main__":
    unittest.main()
