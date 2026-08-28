from pathlib import Path
import re
import unittest


SKILL_ROOT = Path(__file__).resolve().parents[1]


class FrameSkillBundleTests(unittest.TestCase):
    def test_measurement_design_has_one_author_and_one_adopter(self) -> None:
        coordinator = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        designer = (
            SKILL_ROOT.parent / "design-measurement/SKILL.md"
        ).read_text(encoding="utf-8")
        contract = (
            SKILL_ROOT / "references/measurement-design.md"
        ).read_text(encoding="utf-8")
        reviewer = (
            SKILL_ROOT.parent / "review-optimization/SKILL.md"
        ).read_text(encoding="utf-8")
        representation_reviewer = (
            SKILL_ROOT.parent / "review-representation/SKILL.md"
        ).read_text(encoding="utf-8")

        self.assertIn("sole professional author and reviser", designer)
        self.assertIn("sole lifecycle coordinator and normative adopter", contract)
        self.assertIn("adopt or reject its complete projection", coordinator)
        self.assertIn("do not write the protocol", reviewer)
        self.assertIn("check only that R8 faithfully stays within", representation_reviewer)
        self.assertIn("does not select survivors, routes, budgets", designer)

    def test_measurement_design_reuses_readiness_and_routes_its_findings(self) -> None:
        coordinator = (SKILL_ROOT / "references/problem-stage.md").read_text(encoding="utf-8")
        documents = (
            SKILL_ROOT / "references/task-documents.md"
        ).read_text(encoding="utf-8")
        reviewer = (
            SKILL_ROOT.parent / "review-optimization/SKILL.md"
        ).read_text(encoding="utf-8")
        contract = (
            SKILL_ROOT / "references/measurement-design.md"
        ).read_text(encoding="utf-8")

        self.assertIn("| `measurement-design` | Apply the shared measurement-design route", coordinator)
        self.assertIn("any `measurement-design`, `reframe`, or `grill` gives `REFRAME_REQUIRED`", documents)
        self.assertIn("`measurement-design`, `reframe`, or `grill`", reviewer)
        self.assertIn("does not add a verdict or review branch", contract)
        self.assertNotIn("measurement-design branch", reviewer)

    def test_revision_context_and_projection_adoption_are_independently_closed(self) -> None:
        coordinator = (SKILL_ROOT / "references/measurement-work.md").read_text(encoding="utf-8")
        designer = (
            SKILL_ROOT.parent / "design-measurement/SKILL.md"
        ).read_text(encoding="utf-8")
        contract = (
            SKILL_ROOT / "references/measurement-design.md"
        ).read_text(encoding="utf-8")
        reviewer = (
            SKILL_ROOT.parent / "review-optimization/SKILL.md"
        ).read_text(encoding="utf-8")

        self.assertIn("Use `new` only when no current protocol exists", coordinator)
        self.assertIn("do not supply the current protocol", coordinator)
        self.assertIn("DESIGN_BLOCKED: fresh revision context required", designer)
        self.assertIn("Phase A does not read Slot H content", contract)
        self.assertIn("compare every `slot_d`, `slot_e`, `slot_h`", reviewer)
        self.assertIn("mechanical adoption error with work type `reframe`", reviewer)

    def test_measurement_depth_follows_consequence_without_persisted_mode(self) -> None:
        contract = (
            SKILL_ROOT / "references/measurement-design.md"
        ).read_text(encoding="utf-8")

        self.assertIn("An unknown proxy can remain compact", contract)
        self.assertIn("when a proxy controls selection or investment", contract)
        self.assertIn("Repetition alone is not adaptive reuse", (
            SKILL_ROOT.parent / "design-measurement/SKILL.md"
        ).read_text(encoding="utf-8"))
        self.assertIn("This is not a persistent `light` or `enhanced` mode", contract)
        self.assertNotIn("design_mode:", contract)

    def test_r8_stops_have_explicit_scope_and_surviving_authority(self) -> None:
        contract = (
            SKILL_ROOT / "references/representation-contracts.md"
        ).read_text(encoding="utf-8")
        documents = (
            SKILL_ROOT / "references/representation-documents.md"
        ).read_text(encoding="utf-8")

        self.assertIn("the smallest affected scope (`candidate`, `route`, or `campaign`)", contract)
        self.assertIn("the exact identities and authority that survive", contract)
        self.assertIn("stop scope, surviving authority", documents)

    def test_single_user_return_contract_is_referenced_from_core_paths(self) -> None:
        contract = SKILL_ROOT / "references/user-facing-return.md"
        self.assertTrue(contract.is_file())

        coordinator = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        representation = (
            SKILL_ROOT / "references/representation-documents.md"
        ).read_text(encoding="utf-8")
        handoff = (SKILL_ROOT / "references/frontier-handoff.md").read_text(
            encoding="utf-8"
        )

        for text in (coordinator, representation, handoff):
            self.assertIn("user-facing-return.md", text)

        self.assertNotIn("first next action or blocker", coordinator)
        self.assertNotIn("first next action or blocker", representation)

    def test_return_contract_does_not_replace_existing_routing(self) -> None:
        contract = (
            SKILL_ROOT / "references/user-facing-return.md"
        ).read_text(encoding="utf-8")

        self.assertEqual(contract.count("# User-facing return"), 1)
        self.assertIn("Steps 1–9 remain the single source of truth", contract)
        self.assertIn("makes no routing, readiness, authority, or persistence decision", contract)
        self.assertNotIn("Use the first applicable row", contract)
        self.assertNotIn("## Return gate", contract)

    def test_staged_authority_is_owned_by_the_coordinator(self) -> None:
        contract = (
            SKILL_ROOT / "references/user-facing-return.md"
        ).read_text(encoding="utf-8")
        coordinator = (SKILL_ROOT / "references/measurement-work.md").read_text(encoding="utf-8")

        self.assertNotIn("sequencing gate", contract)
        self.assertNotIn("conditional authority", contract)
        self.assertNotIn("Git commit", contract)
        self.assertIn("make implementation review the sequencing gate", coordinator)
        self.assertIn("retain their separate readiness checks", coordinator)
        self.assertIn("request another authorization only when the run falls outside the grant", coordinator)
        self.assertIn("allowed file set, required behavior", coordinator)
        self.assertIn("excluded consequential actions", coordinator)

    def test_measurement_support_review_has_a_frame_owned_route(self) -> None:
        coordinator = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        reviewer = (
            SKILL_ROOT.parent / "review-optimization/SKILL.md"
        ).read_text(encoding="utf-8")

        support = (SKILL_ROOT / "references/measurement-work.md").read_text(encoding="utf-8")
        problem = (SKILL_ROOT / "references/problem-stage.md").read_text(encoding="utf-8")
        representation = (SKILL_ROOT / "references/representation-stage.md").read_text(encoding="utf-8")
        for reference in ("measurement-work.md", "problem-stage.md", "representation-stage.md"):
            self.assertIn(f"references/{reference}", coordinator)
        self.assertIn("## Shared measurement-support gate", support)
        self.assertIn("reachable before problem readiness and after representation begins", support)
        self.assertIn("For a Slot H implementation finding", problem)
        self.assertIn("do not route professional design to measurement support", problem)
        self.assertIn("shared measurement-support gate", representation)
        self.assertIn("`measurement-support` branch of `review-optimization`", support)
        self.assertIn("Accept only a fresh `IMPLEMENTATION_READY` result from `review-optimization/1`", support)
        self.assertIn("## Measurement-support branch", reviewer)
        self.assertIn("reviewed path and SHA-256", reviewer)
        self.assertIn("grants no durable containment, baseline, evaluation", reviewer)
        self.assertNotIn("review-frontier", coordinator)

    def test_reply_is_absent_from_technical_handoff_contract(self) -> None:
        handoff = (SKILL_ROOT / "references/frontier-handoff.md").read_text(
            encoding="utf-8"
        )
        handoff_contract = handoff.split("## Handoff contract", 1)[1].split(
            "## Frontier admission", 1
        )[0]

        for reply_field in (
            "Recommended next action",
            "Copyable instruction",
            "Material alternatives",
            "After your reply",
        ):
            self.assertNotIn(reply_field, handoff_contract)

        self.assertIn("remains complete without the user reply", handoff)

    def test_project_identity_and_deployment_rules_are_structural(self) -> None:
        coordinator = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        handoff = (SKILL_ROOT / "references/frontier-handoff.md").read_text(
            encoding="utf-8"
        )
        reviewer = (
            SKILL_ROOT.parent / "review-optimization/SKILL.md"
        ).read_text(encoding="utf-8")
        normative = "\n".join((coordinator, handoff, reviewer))

        self.assertNotIn("/Users/", normative)
        self.assertNotIn("~/.codex", normative)
        self.assertNotIn("~/.claude", normative)
        self.assertNotIn("Codex", normative)
        self.assertNotIn("Claude", normative)
        self.assertNotIn("agents/openai.yaml", normative)
        self.assertIn("adapter metadata carries discovery and presentation only", coordinator)
        self.assertIn("Preserve past failures and producing inputs", coordinator)
        self.assertIn("current rules govern a new decision", coordinator)
        self.assertIn("without rewriting the old verdict", coordinator)
        self.assertIn("workflow bytes remain outside project identities", handoff)
        self.assertIn("Exclude Skill files, workflow source or release data", reviewer)

    def test_handoff_separates_durable_framing_from_live_campaign_state(self) -> None:
        coordinator = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        documents = (
            SKILL_ROOT / "references/representation-documents.md"
        ).read_text(encoding="utf-8")
        handoff = (SKILL_ROOT / "references/frontier-handoff.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("That reference owns the boundary", coordinator)
        self.assertIn("Framing owns the stable reference-baseline definition", documents)
        self.assertIn("## Stable contract and live state", handoff)
        self.assertIn("`FRONTIER.md` `current_state`", handoff)
        self.assertIn("not a parent mismatch", handoff)
        self.assertIn("creates no mass cleanup, rebinding, or review work", handoff)

    def test_relative_markdown_links_resolve(self) -> None:
        checked_files = (
            SKILL_ROOT / "SKILL.md",
            SKILL_ROOT / "references/measurement-design.md",
            SKILL_ROOT / "references/measurement-work.md",
            SKILL_ROOT / "references/problem-stage.md",
            SKILL_ROOT / "references/representation-stage.md",
            SKILL_ROOT / "references/repair-loop.md",
            SKILL_ROOT / "references/user-facing-return.md",
            SKILL_ROOT / "references/task-documents.md",
            SKILL_ROOT / "references/representation-documents.md",
            SKILL_ROOT / "references/frontier-handoff.md",
            SKILL_ROOT.parent / "design-measurement/SKILL.md",
            SKILL_ROOT.parent / "review-optimization/SKILL.md",
        )
        pattern = re.compile(r"\[[^\]]+\]\(([^)]+\.md)\)")

        for source in checked_files:
            text = source.read_text(encoding="utf-8")
            for target in pattern.findall(text):
                resolved = (source.parent / target).resolve()
                self.assertTrue(resolved.is_file(), f"missing {target} from {source}")


if __name__ == "__main__":
    unittest.main()
