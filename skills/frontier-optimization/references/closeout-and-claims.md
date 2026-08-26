# Frontier Closeout and Claims

Load only after `frontier-core.md` selects either one unresolved claim-only branch or full campaign closeout. These modes share claim forms but have different consequences:

- **Claim-only branch:** review or withdraw one named C without changing `campaign_status`, final budget, route state, or campaign handoff.
- **Full closeout:** stop new spend, reconcile the whole campaign, dispose active work, settle retained evidence and gap, finish applicable claims, and write the final handoff.

Use only the five Frontier Skills. Claims review is one branch of the existing `review-frontier` Skill with `review_kind: claims`. Never create or invoke `review-frontier-claims` or another reviewer.

## Contents

- [Choose one mode from recorded state](#choose-one-mode-from-recorded-state)
- [Claim-only branch](#claim-only-branch)
- [Freeze and review claims](#freeze-and-review-claims)
- [Adopt every finished review through A](#adopt-every-finished-review-through-a)
- [Withdraw C before review completion](#withdraw-c-before-review-completion)
- [Finish the claim-only branch](#finish-the-claim-only-branch)
- [Full closeout](#full-closeout)
- [Reconcile final budget and active work](#reconcile-final-budget-and-active-work)
- [Settle retained results and gap](#settle-retained-results-and-gap)
- [Dispose T W B and search state](#dispose-t-w-b-and-search-state)
- [Preserve final direction state](#preserve-final-direction-state)
- [Claims during full closeout](#claims-during-full-closeout)
- [Write the final handoff](#write-the-final-handoff)
- [Slice 6 acceptance scenarios](#slice-6-acceptance-scenarios)

## Choose one mode from recorded state

Read current parent bindings, `FRONTIER.md`, every surviving project decision root, latest Budget and Selection, terminal B outcomes, W states, E, D, X, Outcome Reflections, replan lineage, C, A, review packets and artifacts, and `log.md`. Use exact recorded project identities, never conversation history or workflow identities.

Choose claim-only only when all are true:

- one named C has `Status: CLAIM_REVIEW_REQUIRED`;
- C has neither an A disposition nor a withdrawing X;
- no ordinary stop, forced halt, unresolved `CLOSEOUT_REQUIRED`, or parent conflict is active; and
- the campaign was planned or running before the claim trigger.

Choose full closeout for a durable campaign-scope ordinary stop, forced halt, stopped or halted campaign, unresolved `CLOSEOUT_REQUIRED`, or parent mismatch after campaign records exist. A candidate- or route-scope disposition returns to Campaign Cycle under the persisted resolver result and never enters full closeout by itself. Full closeout wins when a claim and a campaign-scope stop or halt are both active.

If neither mode fits, record `BLOCKED` with the conflicting records and continue to the canonical return finalization. Do not convert a claim-only request into closeout or use claim review to repair campaign state.

## Claim-only branch

Preserve the exact campaign status, Budget, Selection, reservations, selected B records, W lifecycle, retained E, and route dispositions that existed before `CLAIM_REVIEW_REQUIRED`. The claim snapshot is read-only and grants no spend, integration, promotion, publication, deployment, or submission authority.

Load [Claim records](claim-records.md), [Claim review](claim-review.md), [Review snapshots](review-snapshots.md), and [Worker interfaces](worker-interfaces.md). Load campaign, planning, evidence, learning, W, design, candidate, or implementation references only when the named C cites those records and the reviewer must interpret them.

The branch has exactly two terminal paths:

1. a finished review artifact is validated and adopted through A; or
2. the user withdraws C before review completion and the Coordinator appends a withdrawing X.

Do not leave a reviewed or withdrawn C active. Do not require a positive review to end the branch.

## Freeze and review claims

For an active C that is not withdrawn:

1. freeze one immutable claims snapshot with the exact C wording, intended use, parents, F8, R8, applicable Slots D, E, and H, FRONTIER state, Outcome Reflections, replans, Q, E, D, X, prior A, W, B, design, user authorization, candidate, implementation review, engineering, measurement, and search-state evidence required by the wording;
2. create one immutable packet with `review_kind: claims`, one review identifier, one exclusive review-artifact path, and one completion check;
3. invoke the existing `review-frontier` in a fresh context; and
4. preserve the packet, snapshot, and artifact for every result.

The reviewer writes only the assigned review artifact. It cannot edit C, write A or X, change campaign status, repair evidence, choose follow-up work, authorize wording, publish, or write the final handoff.

## Adopt every finished review through A

After `review-frontier` finishes, the Coordinator validates the packet, snapshot, artifact identity, named C, evidence freshness, and allowed result. Append exactly one A for each reviewed C, including:

- `CLAIMS_SUPPORTED`;
- `CLAIMS_DOWNGRADED`;
- `EVIDENCE_REQUIRED`;
- `PARENT_REVIEW_REQUIRED`; and
- `BLOCKED`.

Never discard or leave a nonpositive review unadopted. A records the finished disposition without editing C or changing valid E.

Only these A records authorize wording:

- `CLAIMS_SUPPORTED` with the exact reviewed wording; or
- `CLAIMS_DOWNGRADED` with the reviewer's exact maximum supported wording copied without semantic change.

An A with `EVIDENCE_REQUIRED`, `PARENT_REVIEW_REQUIRED`, or `BLOCKED` must use `Adopted wording: None` and `Wording authority: none`. It ends the C branch but grants no external use. A later attempt needs a new or still-valid C as required by `claim-review.md`; never reinterpret the old A as approval.

## Withdraw C before review completion

When the user withdraws C before a complete review artifact exists, append X with:

- `Affects: <exact C identifier>`;
- `Disposition: withdrawn`;
- the user withdrawal evidence;
- `Consequence: claim branch complete; no wording authorized`; and
- the unchanged campaign status and return condition.

Do not write A for a review that did not finish. If the review artifact already finished, adopt it through A first; a later withdrawal is a separate X that removes any wording use. Preserve any partial packet, snapshot, or reviewer artifact as nonauthoritative evidence.

## Finish the claim-only branch

A valid A or withdrawing X terminates the named C branch. Append `CLAIM_REVIEW_COMPLETE` to `log.md` with the C, A or X, review packet and artifact when applicable, wording authority, unchanged campaign status, and next router action.

When no other stop, halt, parent conflict, or unresolved C exists, return to Campaign Cycle under the unchanged latest Selection. `EVIDENCE_REQUIRED` and `BLOCKED` do not starve the campaign: they block only the reviewed wording and any work that explicitly depends on that wording. A withdrawing X likewise blocks only that wording.

Claim-only completion must not:

- change `campaign_status`;
- perform final budget reconciliation;
- close, pause, merge, invalidate, or supersede T, W, or B;
- change retained results or gap;
- write a final campaign handoff; or
- imply that the campaign stopped.

## Full closeout

Require one exact durable stop or halt reason. An ordinary stop must cite a rule fixed before the spend it judges. A halt must cite stale parents, safety, legality, authority, access, accounting, an unresolved controlling contradiction, required parent change, or withdrawn further-spend authorization.

For an ordinary stop, set `campaign_status: stopped`. For a forced halt, set `campaign_status: halted`. Start no new B, research spend, external action, integration, or claim use. Let active workers reach a safe interruption point, preserve their result and spend, and invalidate every outstanding spend authority.

Budget exhaustion and diminishing returns do not support optimality. Parent success supports only the parent Slot D meaning. A gap stop supports only the compatible D authority it cites. If the reason was invented after the result, reject it and use the earlier valid rule or parent-return path.

## Reconcile final budget and active work

Append a final Budget update that accounts for total authorization, prior and Entry spend, every B actual spend, unknown spend, released reservations, remaining authorization, and accounting sources exactly once. If actual spend cannot be reconstructed, keep `campaign_status: halted`, record the unresolved amount, and do not claim clean budget exhaustion.

For every started B, preserve its result, terminal outcome or waiting state, artifacts, checks, actual spend, and recovery point. Safely interrupt work that can stop; use X to pause or close any remaining authority. Never mark unfinished work complete.

For every cited W, record its exact current `plan_revision`, design identity, last checkpoint, artifacts, failed checks, pending input or authorization, recovery step, and truthful Outcome. Full closeout may update W lifecycle and recovery sections but cannot rewrite an old contract or worker evidence.

Before final claims, ensure every terminal B and uncovered E has an Outcome Reflection. Reconstruct a missing reflection only from preserved plan and evidence. Keep unresolved strategic meaning, nonpositive replan review, unknown spend, and missing measurement explicit; closeout cannot approve them retroactively.

Do not rewrite an older Outcome Reflection to add current fields, later X records, final Budget, a new resolver result, or later workflow semantics. Closeout may cite an immutable older reflection and record its final disposition separately; it never recomputes that reflection or its persisted resolver result under the current workflow.

## Settle retained results and gap

Set F4 to exactly the result relation authorized by parent Slots D, E, H, and R8: one best option with applicable ties, a lexicographic best, a confirmed non-dominated set, a threshold-qualified set, or another exact parent-defined relation. Retain only valid E identities with their uncertainty, comparison validity, candidate and experiment identities, and promotion evidence.

For F5 and F6, use only active D records compatible with the final baseline, retained E, epoch, objective, scope, assumptions, direction, and tolerance. Report a scalar gap only when that complete comparison is valid. Otherwise record `gap: Unknown` with the exact missing authority. An unresolved bound contradiction forces halted closeout and bars the affected bound, gap, promotion, and claim.

Do not turn non-discovery, budget exhaustion, local rank, engineering readiness, or a Pareto set among evaluated options into a broader optimality claim.

## Dispose T W B and search state

Append X for every active T, W or W revision, selected or authorized B, and reusable search-state object that would otherwise retain authority after closeout. Use:

- `closed` when no more spend is authorized under current parents;
- `paused` when one named event, input, review, authorization, or resource can reopen work;
- `merged` when future work belongs to another route or plan;
- `superseded` when a named revision or object replaces it; or
- `invalid` or `voided` only when evidence or parent authority prevents reuse.

Each X must name affected identities, reason, evidence, recovery or reopening condition, and comparison, promotion, spend, and claim consequences. A shared W may remain reusable even when one linked route closes, but its surviving scope and revision must be explicit. Parent-owned search-state compatibility returns to `frame-optimization`; Frontier does not infer it.

## Preserve final direction state

Before `CLOSEOUT_COMPLETE`, freeze the final direction state in the handoff and final `FRONTIER.md` view without changing any historical B, E, Outcome Reflection, Selection, or review. Preserve:

- the final compatible E sequence and every controlling Outcome Reflection identity, including exclusions and adaptive-exposure limits;
- the strongest bounded progress and constraint meaning supported under the tested conditions, with unresolved validity kept explicit;
- the latest `Route-set state`, eligible routes, exclusions, deferrals, shared assumptions, prerequisite outcomes, and observable reopening events;
- the considered diagnostic alternatives and recorded ordering that control the final decision under the single Learning Loop resolver;
- the latest first applicable direction-resolver row, its evidence-state identity, exact stop, halt, parent handoff, or blocker, and why no later row applies;
- final Budget reachability, protected-reserve disposition, unknown spend, and any unfunded required check; and
- each surviving project decision root, parent chain, and adopting Entry or Replan identity.

A plateau, diminishing-return, or bottleneck statement remains limited to its exact conditions and evidence. Closeout may say that no permitted work can reach another meaningful check under the final Budget and authority; it cannot claim a local optimum, global optimum, impossibility, or that no better route exists.

## Claims during full closeout

Create C only for exact wording and intended use beyond a raw measurement record. Process each important external claim through the same `review-frontier` claims branch and A or withdrawing X rules above. Full closeout continues after every active C receives a terminal A or X disposition.

Claim disposition does not reopen spend or change stopped or halted status. Preserve supported, downgraded, unaudited, nonpositive, and withdrawn wording separately. A later X that invalidates cited evidence makes the dependent A wording unusable until a new C and review establish current support.

## Write the final handoff

Write the final handoff to `log.md` and update the `FRONTIER.md` Brief and F2-F8 final view. Include:

- exact stop or halt reason and status;
- Generation starting and ending or retained Git versions and the affected working scope;
- final budget and unresolved accounting;
- measured and retained E with candidate and experiment identities;
- completed, paused, superseded, invalid, or reusable T, W, B, and search state, including recovery steps;
- applicable design, development authorization, implementation review, integration, and archive state;
- Outcome Reflections, compatible evidence sequence, bounded progress and constraint meaning, focused research, V, and replan lineage;
- final route-set state, reopening events, diagnostic dominance, first applicable resolver row, and exact direction consequence;
- project decision, attestation, authority, execution, and outcome roots for every surviving object;
- active compatible D records and valid gap, or `gap: Unknown`;
- C, A, X, supported wording, and wording that remains unauthorized; and
- exact evidence, review, authorization, resource, or parent change required before continuation.

Record `CLOSEOUT_COMPLETE` only when the surviving files reproduce all final state and no active campaign authority, unresolved claim branch, or unclassified retained artifact remains. Campaign completion does not imply optimality, publication, deployment, submission, integration, or further-spend permission. Preserve all cited artifacts. On a later explicit request, use [Packaging and durable recovery](packaging-and-recovery.md); packaging and cleanup never occur implicitly during closeout.

Return the recorded claim or closeout outcome to the Coordinator.

## Slice 6 acceptance scenarios

| Scenario | Required durable outcome |
|---|---|
| Claim review returns `EVIDENCE_REQUIRED` or `BLOCKED` | Coordinator appends A with no adopted wording, records `CLAIM_REVIEW_COMPLETE`, preserves `campaign_status`, and routes back to Cycle when no other stop or halt applies. |
| User withdraws C before review completion | Coordinator appends withdrawing X, writes no A for the unfinished review, records no wording authority, preserves `campaign_status`, and routes back to Cycle when no other stop or halt applies. |
| Claim review supports or downgrades wording | Coordinator appends A; only exact supported or exact reviewer-supplied downgraded wording receives the stated external-use authority. |
| Claim and stop or halt are both active | Full closeout wins; claim disposition does not resume the campaign. |
| Full closeout with unresolved accounting or bound contradiction | Campaign remains halted, affected gap and claims remain unavailable, and the handoff names the exact recovery requirement. |
| Full closeout after direction resolution | The handoff preserves the final compatible evidence, route set and reopening events, diagnostic dominance, exact resolver row and consequence, Budget reachability, and typed project provenance without rewriting an earlier record. |

Slice 6 passes only when every completed claim review has A, every pre-completion withdrawal has X, each C branch has exactly one controlling terminal disposition, claim-only processing leaves campaign state unchanged, and full closeout alone performs final budget, T/W/B, retained-result, gap, and handoff reconciliation.
