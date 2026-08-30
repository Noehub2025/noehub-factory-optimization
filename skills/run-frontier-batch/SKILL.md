---
name: run-frontier-batch
description: Run one selected Frontier Batch for design, prototype, code, human input, experiment, research, external action, or mixed work. Use only when frontier-optimization has fixed the Batch objective, scope, applicable Reviews and Permissions, limits, paths, checks, completion conditions, and result ownership.
---

# Run Frontier Batch

Execute the assigned B; report evidence without adopting campaign decisions. A Batch can contain repeated working steps, several Candidate Revisions and sequential worker invocations while it pursues the same independently judged result.

For permission questions, apply [User decisions](../frontier-optimization/references/user-decisions.md). An applicable continuing Permission may cover the action without a new question.

## Accept the assignment

1. Open the current B through [Current Batch](../frontier-optimization/references/batch-current.md). Resolve its objective, scope, applicable Reviews and Permissions, Coordinator-set resource limits, allowed writes, checks, Batch-owned Measurement Definition and result ownership. Use [Provenance and Git](../frontier-optimization/references/provenance-and-identity.md) only when exact retained bytes or an external artifact matter. The worker never raises its own limits or edits Campaign Budget.
2. Begin reversible preparation and working changes directly inside the open Batch. Do not create an acknowledgment, execution-start, snapshot, packet identity or Attempt for receipt, planning, editing, debugging or harmless checks.
3. For W-backed work, load only the concerns needed by `delivery_scope`. Keep the worker's mutable work breakdown outside the design contract. A technical discovery goes to the existing design owner.
4. Check only facts relevant to the current action. Worker-forbidden paths answer who may write. The selected Git commit and paths answer which bytes a check or Consequence uses. Workflow deployment, unrelated dirty paths and ordinary working changes do not become project inputs.

A missing prerequisite stops its dependent action with the observed facts and recovery condition, not an invented technical conclusion.

## Work and report

Start with the earliest useful checkpoint. Within [Batch continuation](../frontier-optimization/references/batch-current.md#boundary-preserving-continuation), revise internal steps, repair local defects and continue across invocations. Use `Batch.apply` for reversible progress. Record real limited effects and decision-relevant evidence, not ordinary debugging history. Follow the parent-owned charge event and cumulative limits.

Read only the relevant branch:

- Changes project bytes: [Code execution](../frontier-optimization/references/batch-code-execution.md) when the work is software; otherwise apply the task's own implementation method.
- Any work that actually invokes measurement, including diagnostic-only, routine-local, Slot H, or derived-result recovery: [Measurement](../frontier-optimization/references/batch-evaluation.md).
- Observations of working material: use `Batch.apply(RecordObservation)` for harmless routine facts and [perform an action](../frontier-optimization/references/batch-current.md#perform-an-action) when measurement or another Consequence makes repetition matter.
- Research or analysis: answer the assigned question using applicable sources, distinguish observations from hypotheses, explain uncertainty and what observation would change the decision. Do not load candidate or engineering publication rules.
- Human input: follow the assigned request, provenance, confidentiality and acceptance conditions. Return `waiting_for_input` when the response is absent; distinguish receipt from validation. Evidence from a person is not automatically a user authorization.
- External, paid, sensitive or irreversible operations: use an installed `OperationBinding` through `Batch.perform`. The binding declares the protected Consequences inherent to its seam. Act only within the applicable V, actual scope, cumulative limits and the tool's enforceable control. Pause only the uncovered operation.
- Mixed work: apply each component's actual evidence and effect requirements, without promoting its work-kind label to permission.

Complete the assigned deliverable and checks. Engineering reports and implementation review apply only when required by this work. Preserve failed formal attempts and unknown effects truthfully; unknown consumption is not zero.

When returning between invocations, keep working material in its assigned surface and state progress, remaining gap and the next action. A failed check or local implementation defect stays in the same Batch and creates no new Attempt. Publish no terminal result merely because one internal step failed.

When the B reaches a result, return the observations, actual consumption, actual Consequences, exact Candidate Revision and recovery information recorded by `Batch.perform`. The Coordinator applies [Result adoption](../frontier-optimization/references/result-adoption.md) and concludes the Batch when no affected Attempt is unresolved. Include only evidence possible at the reached phase. Exact project bytes must match their applicable passing checks and Review.

The Coordinator owns the Batch objective and scope, Selection, adopted Evidence, parents and claims. R owns Review meaning; V owns Permission and value limits; Git owns retained project bytes; Batch owns working state, Attempts, actual consumption, Consequences and results. Completion means every applicable deliverable and real Consequence is accounted for; it does not grant the next action.
