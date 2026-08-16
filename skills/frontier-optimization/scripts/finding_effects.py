#!/usr/bin/env python3
"""Classify Frontier validator findings by their maximum workflow effect."""

from __future__ import annotations

from typing import Iterable


BLOCK = "block"
REPAIR = "repair"
ADVISORY = "advisory"
EFFECTS = {BLOCK, REPAIR, ADVISORY}

# These findings make the current serialization or draft unusable, but do not
# by themselves change the authorized objective, evidence, or consequence.
REPAIR_CODES = {
    "ADOPTION_ID_MISMATCH",
    "ADOPTION_ID_MISSING",
    "ARTIFACT_PATH_NOT_CANONICAL",
    "COMPLETION_CHECK_INVALID",
    "DRAFT_ALREADY_FROZEN",
    "ENTRY_COMPLETION_CHECK_OUT_OF_SCOPE",
    "NON_PROJECT_ENTRY_INPUT",
    "NON_PROJECT_PACKET_INPUT",
    "PACKET_ID_MISMATCH",
    "PACKET_ID_MISSING",
    "RESULT_ID_MISMATCH",
    "RESULT_ID_MISSING",
    "SCHEMA_PREFLIGHT_PATHS_INVALID",
    "TARGET_SUMMARY_FIELD_MISMATCH",
    "UNKNOWN_ENTRY_FIELD",
    "UNKNOWN_PACKET_FIELD",
}

# These codes are reserved for non-authoritative record observations. They may
# be used only when the canonical structured owner and every authority-bearing
# byte have already been verified.
ADVISORY_CODES = {
    "DISPLAY_TIMESTAMP_NONCANONICAL",
    "HISTORICAL_DESCRIPTION_MISMATCH",
    "NARRATIVE_STATE_STALE",
    "REDUNDANT_DOCUMENT_HASH_MISMATCH",
}


def effect_for(code: str) -> str:
    """Return a fail-closed effect for one stable finding code."""
    if code in ADVISORY_CODES:
        return ADVISORY
    if code in REPAIR_CODES:
        return REPAIR
    return BLOCK


def add_finding(findings: list[dict[str, str]], code: str, detail: str) -> None:
    """Add one deduplicated finding with its centrally derived effect."""
    finding = {"code": code, "effect": effect_for(code), "detail": detail}
    if finding not in findings:
        findings.append(finding)


def finalize_findings(findings: Iterable[dict[str, str]]) -> dict[str, object]:
    """Partition findings while keeping advisories out of readiness failures."""
    normalized: list[dict[str, str]] = []
    for item in findings:
        code = str(item.get("code", "UNKNOWN"))
        detail = str(item.get("detail", ""))
        expected_effect = effect_for(code)
        normalized_item = {"code": code, "effect": expected_effect, "detail": detail}
        if normalized_item not in normalized:
            normalized.append(normalized_item)
    normalized.sort(key=lambda item: (item["effect"], item["code"], item["detail"]))
    blocking = [item for item in normalized if item["effect"] == BLOCK]
    repairs = [item for item in normalized if item["effect"] == REPAIR]
    advisories = [item for item in normalized if item["effect"] == ADVISORY]
    actionable = sorted(blocking + repairs, key=lambda item: (item["code"], item["detail"]))
    return {
        "ready": not actionable,
        "findings": actionable,
        "blocking_findings": blocking,
        "repair_findings": repairs,
        "advisories": advisories,
        "finding_effect_counts": {
            BLOCK: len(blocking),
            REPAIR: len(repairs),
            ADVISORY: len(advisories),
        },
    }


def has_actionable_findings(findings: Iterable[dict[str, str]]) -> bool:
    """Return whether any finding must be blocked or repaired before readiness."""
    return not bool(finalize_findings(findings)["ready"])
