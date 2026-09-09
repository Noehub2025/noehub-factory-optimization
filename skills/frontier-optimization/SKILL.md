---
name: frontier-optimization
description: Coordinate Optimization Frontier campaigns. Use when the user requests campaign work, closeout, recovery, packaging or claim review, or when an existing optimization task reaches a Framing handoff or internal continuation within its requested scope.
---

# Frontier Optimization

Coordinate one canonical optimization task. The Coordinator owns direction, allocation and adoption; specialist workers own their assigned research, design, execution or review.

Read [User decisions](references/user-decisions.md) when interpreting the request, recovering its continuing scope, or determining permission.

## Recover and choose the current action

1. Read [Frontier core](references/frontier-core.md), then the current parent handoff, FRONTIER brief and latest controlling records. Reconstruct project facts, adopted results and execution state from their owners. Apply the requested scope from User decisions; correct a conflicting progress description at the current affected record under [Change impact](references/frontier-core.md#change-impact-and-retained-results), preserving real limits and historical evidence.
2. Select one stage using the core router:
   - initial planning or recovery planning: [Entry and planning](references/entry-and-planning.md);
   - active campaign: [Campaign cycle](references/campaign-cycle.md);
   - campaign-wide ending or claim review: [Closeout and claims](references/closeout-and-claims.md);
   - packaging a closed campaign: [Packaging](references/packaging-and-recovery.md).
3. Load action references only at their trigger below. Keep unrelated stage procedures and historical formats unloaded.
4. Complete necessary adoption and accounting, then use the core router for the next in-scope action. Reuse an applicable direction resolution; enter the existing decision path when the adopted state needs a new one. A worker's return ends its assignment, not the Coordinator's task. Read [User-facing handoff](references/user-facing-handoff.md) when the completion boundary in User decisions requires a user return.

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
| Start or continue implementation, repair or ordinary integration | [Run Frontier Batch](../run-frontier-batch/SKILL.md), from the first working change; use [Working assignments](references/worker-interfaces.md#working-assignments) to choose the implementation owner |
| Save a current review subject | [Provenance and Git](references/provenance-and-identity.md), then [Review branch](references/review-branches.md) |
| Read a historical review snapshot | [Review snapshots](references/review-snapshots.md) |
| Prepare code-bearing Entry work | [Entry code planning](references/entry-code-planning.md) |
| Assign or revise a professional implementation design | [Technical design](references/technical-design.md) |
| Select or use exact project bytes | [Current Batch](references/batch-current.md), then [Candidate lifecycle](references/candidate-lifecycle.md) only for historical or specialized publication |
| Reuse calibration or a conditional routine screen | [Evaluation protocol](references/evaluation-protocol.md) |
| Review Entry, design, implementation or claims | [Review branch](references/review-branches.md) |
| Open, revise, perform or continue a current B | [Current Batch](references/batch-current.md) |
| Adopt a saved R, update working inputs or operational limits, or read Batch facts | [Maintained Batch operations](references/batch-current.md#maintained-batch-operations) |
| Read an identity-heavy historical B | [Historical Batch interface](references/batch-interface.md), and [Historical Batch result](references/batch-result.md) when present |
| Validate or adopt a current result | [Current Batch](references/batch-current.md), [Result adoption](references/result-adoption.md) |
| Select the next investment from adopted evidence | [Learning loop](references/learning-loop.md) |
| Close one technical campaign generation | [Closeout and claims](references/closeout-and-claims.md), then `reflect-frontier` at its closeout trigger |
| Prepare a selected strategic replan | [Replan review](references/replan-review.md) |
| Interpret a finding | [Finding effects](references/finding-effects.md) |

## Delegate and adopt

Create the assignment using [Working assignments](references/worker-interfaces.md#working-assignments): enough context to start the next useful work, not a complete future specification. That section owns implementation responsibility, including simple work performed directly. Use the existing specialist:

- `research-frontier`: one bounded evidence question.
- `grill-frontier`: one unresolved user-owned decision.
- `design-implementation`: professional design in a fresh context.
- `reflect-frontier`: one Generation Reflection after technical closeout reconciliation.
- `run-frontier-batch`: implementation, repair, integration and observation within B, not just final execution.
- `review-frontier`: the selected independent review.

The designer writes professional concerns, not lifecycle records or executable output. The Coordinator creates W's scaffold and derives maps and stable slice references from that content. Use Work Plan's saved-reference preparation for design consumers and Learning Loop's input preparation for resolver dispatch; pass tool-produced bindings directly. A ready W does not trigger another design assignment: load only the concerns needed by the current action. Executable evidence requested during design uses the existing bounded research, prototype or B route.

Adopt a worker result only after its assignment and evidence match. Preserve the specialist's professional meaning; send an actual defect to its owner rather than silently rewriting it. A draft preparation failure remains editable work, not a new review or recovery chain.

Route working changes and repairs through [Batch continuation](references/batch-current.md#boundary-preserving-continuation) before considering another investment decision; correct inherited procedural gates through [Repair an existing execution restriction](references/batch-current.md#repair-an-existing-execution-restriction), including their dispatch and writeback. Use the [single resolver](references/learning-loop.md#integrated-direction-resolver) when the next investment actually changes or a B result is terminal. Generation Reflection improves the next generation's search after closeout; it does not choose a route or grant permission. Neither worker output nor a technical review chooses another route or grants a new user permission.

A route-scoped result does not complete a continuing task. A running campaign with no selected next action returns only when the requested bounded deliverable is complete, the user explicitly pauses or requests reporting, or a user-owned boundary blocks every remaining worthwhile action. Otherwise continue direction resolution or close the campaign under [Continuing task and stage instructions](references/user-decisions.md#continuing-task-and-stage-instructions), with persisted state supporting any final report.
