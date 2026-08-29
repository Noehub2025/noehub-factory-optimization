# Frontier finding effects

Read when interpreting a validator or review finding, not before unrelated planning or research.

## Finding effects

This section is the sole semantic owner of finding effects. Validators derive the effect from a stable code through `finding_effects.py`; callers and reviewers cannot supply or weaken it. An unknown code defaults to `block`.

Apply one decision-impact test: identify the violated requirement or observed evidence gap, the affected next consequence, and why proceeding would make that consequence unauthorized, unreliable, or unrecoverable. A demonstrated violation or unresolved consequential authority, spend, exposure, or external effect blocks only that transition. Uncertain effectiveness, novelty, unfamiliar methods, and hypothetical risk alone do not: select an authorized bounded observation when it can resolve the uncertainty. Reviewers need not prove the absence of every possible failure. This semantic test does not weaken coded findings; unknown validator codes still block until their meaning is resolved.

- `block`: the current action is unsafe or ambiguous. Preserve evidence and stop the affected transition. The effect does not by itself show that parent meaning changed or require a new B, user authorization, parent review, or rerun. Use one of those only when the semantic object, a prior answer, or an actual effect must change.
- `repair`: the current serialization, derived field, or transient realization is unusable, but the authoritative objective, evidence, and maximum consequence are unchanged and mechanically provable. Readiness remains false until correction. Repair inside the same semantic B and V before review or through an already authorized boundary-preserving continuation; rerun only the affected deterministic checks. A changed reviewed semantic input still requires the applicable review of that version, using [Entry repair review](entry-review.md#entry-repair-review) for an Entry correction.
- `advisory`: the canonical structured owner and every authority-bearing byte pass, while only a non-authoritative display timestamp, historical description, redundant prose hash, or generated narrative is stale. Readiness remains true. Preserve immutable records, report the advisory in validator or review output, and create no replacement identity, B, V, review, or authorization.

A timestamp that controls a deadline, ordering, lifecycle transition, or authorization is never advisory. A digest that binds candidate, evaluator, evidence, target, authority, or reproducibility is never advisory. A narrative disagreement is advisory only when `current_state`, its cited ledger decision, and every typed authority projection agree; otherwise it is `block`. Keep advisories out of strength, validity, progress, and constraint conclusions.

Correct a non-authoritative display in the current explanation or working view while retaining the reviewed version. A new version does not invalidate the old review for its own bytes, and the old attestation cannot approve a replacement decision. Existing authorization governs whether changed work may continue; an advisory alone creates no replacement object.

Historical artifacts retain their original validator and review meaning. Apply this contract prospectively; do not rewrite or mass-migrate old B, V, R, E, OR, or X records merely because finding output gained effects.

Throughout Frontier, `finding-free` means zero `block` or `repair` findings. Advisories are reported separately and do not make a ready object nonpositive.
