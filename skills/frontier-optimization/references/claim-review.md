# Frontier Claim Review

Load for a named C whose wording and intended use need independent judgment under [Assurance by consequence](batch-evaluation.md#assurance-by-consequence). Ordinary result validation and retained-data recovery use [Result adoption](result-adoption.md).

## Current subject

Use the Git subject and R fields from [Review Frontier](../../review-frontier/SKILL.md). Include exact C wording, intended use, and only the evidence and parent requirements needed to judge it. A supporting R supplies its checked conclusions and assumptions, not an obligation to repeat its procedure. Current work needs no review packet, snapshot manifest or copied identity lineage.

## Review method

1. Resolve what each C asserts and how it will be used. Inspect the source evidence needed for that assertion.
2. Reuse applicable checked facts. Judge remaining questions about comparison conditions, uncertainty, target or proxy meaning, exposure, operating conditions, engineering readiness or bounds only where the wording relies on them. Workflow stages and unrelated history are not additional subjects.
3. Apply [Finding effects](finding-effects.md). Distinguish evidence that limits the claim from an optional technical improvement. An observed narrow result need not prove a broader claim that was never proposed.
4. Return `CLAIMS_SUPPORTED`, `CLAIMS_DOWNGRADED`, `EVIDENCE_REQUIRED`, `PARENT_REVIEW_REQUIRED`, or `BLOCKED`. For each C, give the checked wording, decisive evidence, supported scope, findings and advisories, and required action if any. A downgrade provides the exact maximum supported wording.

Complete when every assigned C has an evidence-backed disposition, not when all possible future uses are established. Preserve the saved subject; the reviewer writes only its assigned R.

## Adoption

The Coordinator uses [Closeout and claims](closeout-and-claims.md#adopt-every-finished-review-through-a) to dispose each reviewed C through A, including nonpositive results. Only supported or explicitly downgraded wording may be adopted for its stated use; `EVIDENCE_REQUIRED`, `PARENT_REVIEW_REQUIRED` and `BLOCKED` grant no wording authority. Withdrawal follows the existing X path. A does not grant permission for an external action.

Unrelated later records do not stale a review. Changed evidence or wording reopens only the dependent conclusion under [Change impact and retained results](frontier-core.md#change-impact-and-retained-results). Preserve old verdicts rather than turning a nonpositive report into approval.

## Historical compatibility

Read [Review snapshots](review-snapshots.md) only when interpreting a retained snapshot-based report. Its original bytes and verdict remain historical evidence; its packet fields and procedural sequence do not define a current assignment.
