from pathlib import Path
import re
import unittest


SKILL_ROOT = Path(__file__).resolve().parents[1]


class FrameSkillBundleTests(unittest.TestCase):
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
        coordinator = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")

        self.assertNotIn("sequencing gate", contract)
        self.assertNotIn("conditional authority", contract)
        self.assertNotIn("Git commit", contract)
        self.assertIn("make implementation review the sequencing gate", coordinator)
        self.assertIn("grants the exact run conditional on the reviewed target", coordinator)
        self.assertIn("names its exact file set and maximum consequence", coordinator)

    def test_measurement_support_review_has_a_frame_owned_route(self) -> None:
        coordinator = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        reviewer = (
            SKILL_ROOT.parent / "review-optimization/SKILL.md"
        ).read_text(encoding="utf-8")

        shared_gate = coordinator.index("## Shared measurement-support gate")
        problem_stage = coordinator.index("## 3. Complete the problem-definition stage")
        representation_stage = coordinator.index("## 4. Enter the representation stage")
        self.assertLess(shared_gate, problem_stage)
        self.assertLess(shared_gate, representation_stage)
        self.assertIn("Slot H `reframe` finding", coordinator)
        self.assertIn("`measurement-support` branch of `review-optimization`", coordinator)
        self.assertIn("Accept only a fresh `IMPLEMENTATION_READY` result from `review-optimization/1`", coordinator)
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
        self.assertIn("cannot validate an output that failed its issuing Skill's preconditions", coordinator)
        self.assertIn("transient user replies are not identity inputs", handoff)
        self.assertIn("Exclude Skill files, workflow source or release data", reviewer)

    def test_relative_markdown_links_resolve(self) -> None:
        checked_files = (
            SKILL_ROOT / "SKILL.md",
            SKILL_ROOT / "references/user-facing-return.md",
            SKILL_ROOT / "references/task-documents.md",
            SKILL_ROOT / "references/representation-documents.md",
            SKILL_ROOT / "references/frontier-handoff.md",
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
