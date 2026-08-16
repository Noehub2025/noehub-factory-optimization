#!/usr/bin/env python3
"""Regression tests for fail-closed Frontier finding effects."""

from __future__ import annotations

import unittest

from finding_effects import ADVISORY, BLOCK, REPAIR, add_finding, effect_for, finalize_findings


class FindingEffectsTests(unittest.TestCase):
    def test_known_effects_are_classified_centrally(self) -> None:
        cases = (
            ("DISPLAY_TIMESTAMP_NONCANONICAL", ADVISORY),
            ("PACKET_ID_MISMATCH", REPAIR),
            ("CANDIDATE_MEMBER_MISMATCH", BLOCK),
            ("SEALED_DATA_EXPOSURE", BLOCK),
            ("NEW_UNRECOGNIZED_FINDING", BLOCK),
        )
        for code, expected in cases:
            with self.subTest(code=code):
                self.assertEqual(expected, effect_for(code))

    def test_advisory_does_not_fail_readiness(self) -> None:
        raw: list[dict[str, str]] = []
        add_finding(raw, "NARRATIVE_STATE_STALE", "typed current_state is unchanged")
        result = finalize_findings(raw)
        self.assertTrue(result["ready"])
        self.assertEqual([], result["findings"])
        self.assertEqual(1, result["finding_effect_counts"][ADVISORY])

    def test_repair_fails_readiness_without_becoming_a_hard_block(self) -> None:
        raw: list[dict[str, str]] = []
        add_finding(raw, "TARGET_SUMMARY_FIELD_MISMATCH", "regenerate the summary")
        result = finalize_findings(raw)
        self.assertFalse(result["ready"])
        self.assertEqual([], result["blocking_findings"])
        self.assertEqual(REPAIR, result["repair_findings"][0]["effect"])

    def test_unknown_and_authority_findings_fail_closed(self) -> None:
        codes = (
            "BOUND_FILE_HASH_MISMATCH",
            "EVALUATION_TARGET_BINDING_MISMATCH",
            "LIVE_SOURCE_DRIFT",
            "USER_ANSWER_NOT_DERIVED",
            "SCOPE_OR_SPEND_MISMATCH",
        )
        for code in codes:
            with self.subTest(code=code):
                raw: list[dict[str, str]] = []
                add_finding(raw, code, "material uncertainty")
                result = finalize_findings(raw)
                self.assertFalse(result["ready"])
                self.assertEqual(BLOCK, result["blocking_findings"][0]["effect"])

    def test_caller_cannot_forge_a_weaker_effect(self) -> None:
        result = finalize_findings(
            [
                {
                    "code": "BOUND_FILE_HASH_MISMATCH",
                    "effect": ADVISORY,
                    "detail": "forged downgrade",
                }
            ]
        )
        self.assertFalse(result["ready"])
        self.assertEqual(BLOCK, result["blocking_findings"][0]["effect"])


if __name__ == "__main__":
    unittest.main()
