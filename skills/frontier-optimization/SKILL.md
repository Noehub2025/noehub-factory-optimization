---
name: frontier-optimization
description: Coordinate Optimization Frontier campaigns from a positive Representation handoff through Entry, repeated batches, closeout, post-closeout recovery, and Git-backed handoff. Use only when the user explicitly asks to start, resume, recover, open a new campaign after closeout, close, package a completed campaign, or review claims for one canonical Frontier task.
---

# Frontier Optimization

Coordinate one canonical optimization task. The Coordinator owns direction, allocation and adoption; specialist workers own their assigned research, design, execution or review.

Read [User decisions](references/user-decisions.md) when determining permission or deciding whether to ask the user.

## Recover and choose the current action

1. Read [Frontier core](references/frontier-core.md), then the current parent handoff, FRONTIER brief and latest controlling records. Use retained project evidence rather than conversation to reconstruct state.
2. Select one stage using the core router:
   - initial planning or recovery planning: [Entry and planning](references/entry-and-planning.md);
   - active campaign: [Campaign cycle](references/campaign-cycle.md);
   - stop, halt or claim review: [Closeout and claims](references/closeout-and-claims.md);
   - packaging a closed campaign: [Packaging](references/packaging-and-recovery.md).
3. Load action references only at their trigger below. Keep unrelated stage procedures and historical formats unloaded.
4. After adopting the result, read [User-facing handoff](references/user-facing-handoff.md). Explain objective progress, evidence limits, remaining gap and material next choices before audit details. This return step does not rerun the resolver.

For a changed parent or retained result, apply [Change impact](references/frontier-core.md#change-impact-and-retained-results). Report only the exact unresolved dependency; a version difference alone does not end the campaign.

## Action references

| Current action | Read |
|---|---|
| Verify, retain or restore project inputs | [Provenance and Git](references/provenance-and-identity.md) |
| Validate the upstream handoff | [Framing handoff](../frame-optimization/references/frontier-handoff.md) |
| Update F1-F8, Budget or Selection | [Campaign state](references/campaign-state.md) |
| Create or interpret a T, V, B, E or Q record | [Planning records](references/planning-records.md) |
| Update D or X | [Evidence records](references/evidence-records.md) |
| Update C or A | [Claim records](references/claim-records.md) |
| Create or maintain W lifecycle and mechanical bindings | [Work plan](references/work-plan.md) |
| Delegate a worker | [Worker interfaces](references/worker-interfaces.md) |
| Prepare a review subject | [Review preparation](references/review-snapshots.md) |
| Prepare code-bearing Entry work | [Entry code planning](references/entry-code-planning.md) |
| Assign or revise a professional implementation design | [Technical design](references/technical-design.md) |
| Manage a formal candidate | [Candidate lifecycle](references/candidate-lifecycle.md) |
| Reuse calibration or a conditional routine screen | [Evaluation protocol](references/evaluation-protocol.md) |
| Review Entry, design, implementation or claims | [Review branch](references/review-branches.md) |
| Dispatch or continue B | [Batch interface](references/batch-interface.md) |
| Validate or adopt a terminal result | [Batch result](references/batch-result.md), [Result adoption](references/result-adoption.md) |
| Select the next investment from adopted evidence | [Learning loop](references/learning-loop.md) |
| Close one technical campaign generation | [Closeout and claims](references/closeout-and-claims.md), then `reflect-frontier` at its closeout trigger |
| Prepare a selected strategic replan | [Replan review](references/replan-review.md) |
| Interpret a finding | [Finding effects](references/finding-effects.md) |

## Delegate and adopt

Create the assignment with fixed purpose, project parents, allowed writes, limits and completion condition. Use the existing specialist:

- `research-frontier`: one bounded evidence question.
- `grill-frontier`: one unresolved user-owned decision.
- `design-implementation`: professional design in a fresh context.
- `reflect-frontier`: one Generation Reflection after technical closeout reconciliation.
- `run-frontier-batch`: the selected B.
- `review-frontier`: the selected independent review.

The designer writes professional concerns, not lifecycle records or executable output. The Coordinator creates W's scaffold and derives maps and identities from the designer's exact content. A ready W does not trigger another design assignment: load only the concern pointers needed by the current action. Executable evidence requested during design uses the existing bounded research, prototype or B route.

Adopt a worker result only after its assignment and evidence match. Preserve the specialist's professional meaning; send an actual defect to its owner rather than silently rewriting it. A draft preparation failure remains editable work, not a new review or recovery chain.

Use the [Batch continuation rule](references/batch-interface.md#boundary-preserving-continuation) for working changes and repairs. Use the [single resolver](references/learning-loop.md#integrated-direction-resolver) for direction directly from adopted current evidence. Generation Reflection improves the next generation's search after closeout; it does not choose a route or grant permission. Neither worker output nor a technical review chooses another route or grants a new user permission.

Completion means the persisted outcome supports the report and the user-facing return explains progress and legal next actions. The task's objective, budget, access and actual consequences determine continuation, not the number of artifacts produced.
