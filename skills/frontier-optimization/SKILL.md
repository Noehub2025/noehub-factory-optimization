---
name: frontier-optimization
description: Coordinate Optimization Frontier campaigns. Use when the user requests campaign work, closeout, recovery, packaging or claim review, or when an existing optimization task reaches a Framing handoff or internal continuation within its requested scope.
---

# Frontier Optimization

Coordinate one canonical optimization task. The Coordinator owns direction, allocation and adoption; specialist workers own their assigned research, design, execution or review.

Read [User decisions](references/user-decisions.md) when interpreting the request, recovering its continuing scope, or determining permission.

## Recover and choose the current action

1. Use the currently installed [Frontier core](references/frontier-core.md). Recover the current research question, missing observation and work from the [FRONTIER Brief](references/campaign-state.md#frontiermd-and-f1-f8), following its source pointers only for facts needed by the action. Reuse sufficient context that still applies. Saved project commits identify evidence, not the Workflow instructions to load. Read parent rules, adopted results and execution limits from their owners as needed. Apply the requested scope from User decisions; correct conflicting current explanations under [Change impact](references/frontier-core.md#change-impact-and-retained-results), preserving real limits and historical evidence.
2. Select one stage using the core router:
   - initial planning or recovery planning: [Entry and planning](references/entry-and-planning.md);
   - active campaign: [Campaign cycle](references/campaign-cycle.md);
   - campaign-wide ending or claim review: [Closeout and claims](references/closeout-and-claims.md);
   - packaging a closed campaign: [Packaging](references/packaging-and-recovery.md).
3. Load action references only at their trigger below. Keep unrelated stage procedures and historical formats unloaded.
4. Complete necessary adoption and accounting, then use the three questions in [Active learning chain](references/learning-loop.md#active-learning-chain) before the next dispatch or route change. Apply that continuation method when restoring a long task as well; load the direction resolver only at its investment trigger. A worker return or Batch outcome does not by itself end the research problem. Read [User-facing handoff](references/user-facing-handoff.md) when the completion boundary in User decisions requires a user return.

For a material shared research-premise change, use [Research-basis transitions](references/frontier-core.md#research-basis-transitions); retain applicable work without full closeout. For a changed parent or retained result, apply [Change impact](references/frontier-core.md#change-impact-and-retained-results). Report only the exact unresolved dependency; a version difference alone does not end the campaign.

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
| Prepare a necessary independent judgment | [Assurance by consequence](references/batch-evaluation.md#assurance-by-consequence), then [Provenance and Git](references/provenance-and-identity.md) and [Review branch](references/review-branches.md) |
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
| Resume work after adoption, recover a long task, or consider a route change | [Active learning chain](references/learning-loop.md#active-learning-chain); read the resolver sections only when investment needs reconsideration |
| Capture substantive route experience or new cross-route learning | [Research Reflection](references/learning-loop.md#research-reflection), then `reflect-frontier` |
| End the whole campaign | [Closeout and claims](references/closeout-and-claims.md) |
| Prepare a selected strategic replan | [Replan review](references/replan-review.md) |
| Interpret a finding | [Finding effects](references/finding-effects.md) |

## Delegate and adopt

Create the assignment using [Working assignments](references/worker-interfaces.md#working-assignments): enough context to start the next useful work, not a complete future specification. That section owns implementation responsibility, including simple work performed directly. Use the existing specialist:

- `research-frontier`: one bounded evidence question.
- `grill-frontier`: one unresolved user-owned decision.
- `design-implementation`: professional design in a fresh context.
- `reflect-frontier`: technical learning from a completed, retired or replaced research route, a substantial learning checkpoint, or new cross-route experience.
- `run-frontier-batch`: implementation, repair, integration and observation within B, not just final execution.
- `review-frontier`: the selected independent review.

The designer writes professional concerns, not lifecycle records or executable output. The Coordinator creates W's scaffold and derives maps and stable slice references from that content. Use Work Plan's saved-reference preparation for design consumers. For resolver dispatch, use Learning Loop's input preparation and [Route-investment ordering](references/learning-loop.md#route-investment-ordering) for question scope and faithful adoption; pass tool-produced bindings directly. A ready W does not trigger another design assignment: load only the concerns needed by the current action. Executable evidence requested during design uses the existing bounded research, prototype or B route.

Adopt supported findings and assess recommendations that change current work or create workflow obligations under [Professional output and workflow decisions](references/worker-interfaces.md#professional-output-and-workflow-decisions). Reuse applicable checks and continue through Active learning chain. Preserve professional meaning; send an actual defect to its owner rather than silently rewriting it. For direction judgments, use [Resolver result completion](references/learning-loop.md#resolver-result-completion) to handle a concrete comparison defect without creating a competing resolution. A draft preparation failure remains editable work, not a new review or recovery chain.

Route working changes and repairs through [Batch continuation](references/batch-current.md#boundary-preserving-continuation) before considering another investment decision; correct inherited procedural gates through [Repair an existing execution restriction](references/batch-current.md#repair-an-existing-execution-restriction), including their dispatch and writeback. Continue the current research problem across working steps and B records; use the [single resolver](references/learning-loop.md#when-to-reconsider-investment) only when investment needs reconsideration. Research Reflection develops technical insight and new ideas under its learning trigger; professional owners judge them independently alongside original evidence. Neither worker output nor a technical review chooses another route or grants a new user permission.

A route-scoped result does not complete a continuing task. A running campaign with no selected next action returns only when the requested bounded deliverable is complete, the user explicitly pauses or requests reporting, or a user-owned boundary blocks every remaining worthwhile action. Otherwise continue the current research problem, reconsider investment when triggered, or close the campaign under [Continuing task and stage instructions](references/user-decisions.md#continuing-task-and-stage-instructions), with persisted state supporting any final report.
