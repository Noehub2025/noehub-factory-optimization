# Frontier Evidence Records

Load only when writing a bound/reference D or disposition X. Outcome Reflection has its own action file.

## D: reference, conjecture, or bound

Create D only when selection, gap, stopping, contradiction, or a claim needs it. Kind states origin; authority states permitted use.

```markdown
## D001: <reference, conjecture, or bound>

- Recorded at: <ISO-8601 datetime>
- Kind: <empirical record | relaxation | analytical | exhaustive | conjecture>
- Direction or comparison meaning: <exact meaning>
- Value, vector, set, or rule: <content>
- Instance and scale scope: <scope>
- Assumptions: <identifiers or exact assumptions>
- Derivation: <method and stable evidence>
- Validation: <checks and evidence>
- Tolerance: <value and meaning>
- Problem epoch: <integer>
- Authority: <reference | gap-valid | claim-certified>
- State: <active | superseded | invalid | withdrawn>
```

## X: disposition

```markdown
## X001: <disposition>

- Recorded at: <ISO-8601 datetime>
- Affects: <identifiers>
- Disposition: <superseded | re-evaluated | invalid | voided | withdrawn | paused | closed | merged | joined>
- Reason: <exact reason>
- Evidence: <links or identifiers>
- Recovery or reopening condition: <exact event and new authority, or None>
- Consequence: <comparison, reuse, promotion, stopping, or claim effect>
```

For post-closeout recovery, preserve the closing X and reference only the retained material needed by the next action in the existing opening X. Apply [Candidate recovery](candidate-lifecycle.md#post-closeout-recovery-reuse): unchanged original-use results retain their existing implementation conclusion; complete only missing or affected reviews. Exact bytes establish content, not new permission. The actual proposed measurement, integration or other consequence retains its applicable gate.

When E contradicts an active applicable D beyond its stated tolerance, preserve both records and treat the contradiction as unresolved. Do not promote, use the candidate as incumbent, strengthen a claim, or authorize dependent spend. Append X only after a diagnostic establishes whether D, E, or both are superseded, re-evaluated, invalid, or otherwise limited; cite the exact assumptions, experiment identity, and evidence. An unresolved safety, legality, or authority contradiction halts the campaign rather than opening an ordinary diagnostic path.

For C withdrawn before claim-review completion, append X with `Disposition: withdrawn`, cite the user's withdrawal, and state `claim branch complete; no wording authorized`. This X preserves claim-only `campaign_status` and returns routing to Cycle when no other stop, halt, parent conflict, or unresolved C exists. If the review artifact already finished, A remains mandatory; a later X withdraws wording use but does not replace A.
