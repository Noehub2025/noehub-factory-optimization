---
name: run-frontier-batch
description: Run assigned Frontier Batch work from initial implementation, debugging and integration through observation. Use when frontier-optimization assigns development, repair, research, experiments, human input or external actions within an owning Batch's objective and scope.
---

# Run Frontier Batch

Use this Skill from the first working change, including simple work performed directly; report evidence without adopting campaign decisions. Follow [Working assignments](../frontier-optimization/references/worker-interfaces.md#working-assignments) for context, implementation responsibility and same-B continuation.

For permission questions, apply [User decisions](../frontier-optimization/references/user-decisions.md). An applicable continuing Permission may cover the action without a new question.

## Accept the assignment

1. Read the assignment's base references and current changes; open its B through [Current Batch](../frontier-optimization/references/batch-current.md). Resolve the next observable result, applicable requirements, allowed writes and limits from their owners. Read existing checks and any Measurement Definition, Reviews or Permissions when the current action needs them; a selected revision or passing check is not a prerequisite for ordinary development. Use [Provenance and Git](../frontier-optimization/references/provenance-and-identity.md) when retained bytes or an external artifact matter. The worker never raises its own limits or edits Campaign Budget.
2. Begin reversible preparation and working changes directly inside the open Batch. When using an existing capability, follow [Reuse working knowledge](../frontier-optimization/references/batch-current.md#reuse-working-knowledge). Do not create an acknowledgment, execution-start, snapshot, packet identity or Attempt for receipt, planning, editing, debugging or harmless checks.
3. For W-backed work, load only the concerns needed by this assignment within `delivery_scope`. On continuation, read relevant changes rather than reloading the whole design. Follow Working assignments for discoveries and internal refinements; keep the mutable work breakdown outside the design contract.
4. Check only facts relevant to the current action. Worker-forbidden paths answer who may write. The selected Git commit and paths answer which bytes a check or Consequence uses. Workflow deployment, unrelated dirty paths and ordinary working changes do not become project inputs. When checking R coverage or using a preflight, apply [Review applicability and adoption](../frontier-optimization/references/batch-current.md#review-applicability-and-adoption).

A missing prerequisite stops its dependent action with the observed facts and recovery condition, not an invented technical conclusion. Report professional discoveries that may change investment through [Working assignments](../frontier-optimization/references/worker-interfaces.md#working-assignments); local implementation choices remain within the assignment.

## Work and report

Start with the earliest interpretable observation. Within [Batch continuation](../frontier-optimization/references/batch-current.md#boundary-preserving-continuation), revise internal steps, repair local defects and continue across invocations. Follow [Evidence at real boundaries](../frontier-optimization/references/implementation-review.md#evidence-at-real-boundaries) for the affected repair path; this pointer supplies working guidance, not a review invocation. Return an obstructing internal limit or obsolete dispatch rule to the Coordinator through [Repair an existing execution restriction](../frontier-optimization/references/batch-current.md#repair-an-existing-execution-restriction). Use `Batch.apply` for reversible progress. Record actual effects and applicable charge events separately from version selection.

Read only the relevant branch:

- Changes project bytes: [Code execution](../frontier-optimization/references/batch-code-execution.md) when the work is software; otherwise apply the task's own implementation method.
- First implementing or changing Batch execution wiring: [Executable example](references/execution-example.md). Reuse an established caller when it already covers the needed behavior.
- Select working bytes or report Batch facts: [Maintained Batch operations](../frontier-optimization/references/batch-current.md#maintained-batch-operations). Review adoption and operational-limit changes remain Coordinator-owned.
- Any work that actually invokes measurement, including diagnostic-only, routine-local, Slot H, or derived-result recovery: [Measurement](../frontier-optimization/references/batch-evaluation.md).
- Observations of working material: use `Batch.apply(RecordObservation)` for harmless routine facts and [perform an action](../frontier-optimization/references/batch-current.md#perform-an-action) when measurement or another Consequence makes repetition matter.
- Research or analysis: answer the assigned question using applicable sources, distinguish observations from hypotheses, explain uncertainty and what observation would change the decision. Do not load candidate or engineering publication rules.
- Human input: follow the assigned request, provenance, confidentiality and acceptance conditions. Return `waiting_for_input` when the response is absent; distinguish receipt from validation. Evidence from a person is not automatically a user authorization.
- External, paid, sensitive or irreversible operations: use an installed `OperationBinding` through `Batch.perform`. The binding declares the protected Consequences inherent to its seam. Act only within the applicable V, actual scope, cumulative limits and the tool's enforceable control. Pause only the uncovered operation.
- Mixed work: apply each component's actual evidence and effect requirements, without promoting its work-kind label to permission.

Complete this invocation's assigned observation or deliverable and affected checks, not every remaining B obligation. Engineering reports and implementation review apply only when required by this work. Preserve failed formal attempts and unknown effects truthfully; unknown consumption is not zero.

When returning between invocations, keep working material in its assigned surface and state progress, remaining gap and the next action. A failed check or local implementation defect stays in the same Batch and creates no new Attempt. Publish no terminal result merely because one internal step failed.

When the B reaches a result, return the observations, actual consumption, actual Consequences, exact Candidate Revision and recovery information recorded by `Batch.perform`. The Coordinator applies [Result adoption](../frontier-optimization/references/result-adoption.md) and concludes the Batch when no affected Attempt is unresolved. Include only evidence possible at the reached phase. Exact project bytes must match their applicable passing checks and Review.

The Coordinator owns the Batch objective and scope, Selection, adopted Evidence, parents and claims. R owns Review meaning; V owns Permission and value limits; Git owns retained project bytes; Batch owns working state, Attempts, actual consumption, Consequences and results. Completion means every applicable deliverable and real Consequence is accounted for; it does not grant the next action.
