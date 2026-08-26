---
name: run-frontier-batch
description: Run one exact Frontier B packet for design, prototype, code, human input, experiment, research, external action, or mixed work. Use only when frontier-optimization has fixed the batch, authority, budget, parents, paths, checks, completion conditions, and result path.
---

# Run Frontier Batch

Execute the assigned B; report evidence without adopting campaign decisions. A B can contain repeated working steps and sequential worker invocations inside its existing scope.

For permission questions, apply [User decisions](../frontier-optimization/references/user-decisions.md). The packet fixes this execution; an applicable continuing user grant may cover it without a new question.

## Accept the assignment

1. Resolve the packet's fixed project inputs, current permission, remaining resources, allowed writes, checks and result path. Use [Batch interface](../frontier-optimization/references/batch-interface.md) for the state transition and [Provenance and Git](../frontier-optimization/references/provenance-and-identity.md) when verifying retained input references.
2. Acknowledge only receipt of the immutable assignment, then return. The Coordinator owns the baseline and execution-start. Begin work only from its verified released state, including current authority, Budget, resources and actual frozen inputs.
3. For W-backed work, load only the concerns needed by `delivery_scope`. Keep the worker's mutable work breakdown outside the design contract. A technical discovery goes to the existing design owner.
4. Check only facts relevant to the current consequence. Worker-forbidden paths answer who may write; execution-frozen inputs answer what must remain unchanged. Workflow deployment and updates do not become project inputs.

A missing prerequisite stops its dependent action with the observed facts and recovery condition, not an invented technical conclusion.

## Work and report

Start with the earliest useful checkpoint. Within [Batch continuation](../frontier-optimization/references/batch-interface.md#boundary-preserving-continuation), revise internal steps, repair local defects and continue across invocations. Record real limited effects and formal evidence, not ordinary debugging history. Follow the parent-owned charge event and cumulative limits.

Read only the relevant branch:

- Changes executable candidate: [Code execution](../frontier-optimization/references/batch-code-execution.md).
- Slot H, routine-local measurement or derived-result recovery: [Measurement](../frontier-optimization/references/batch-evaluation.md).
- Authorized observations of working material: [Bounded observations](../frontier-optimization/references/batch-interface.md#bounded-observations-before-publication).
- Research or analysis: answer the assigned question using applicable sources, distinguish observations from hypotheses, explain uncertainty and what observation would change the decision. Do not load candidate or engineering publication rules.
- Human input: follow the assigned request, provenance, confidentiality and acceptance conditions. Return `waiting_for_input` when the response is absent; distinguish receipt from validation. Evidence from a person is not automatically a user authorization.
- External, paid, sensitive or irreversible operations: act only within the actual user-granted target, scope and limits and the tool's enforceable boundary. Pause only the uncovered operation.
- Mixed work: apply each component's actual evidence and effect requirements, without promoting its work-kind label to permission.

Complete the assigned deliverable and checks. Engineering reports and implementation review apply only when required by this work. Preserve failed formal attempts and unknown effects truthfully; unknown consumption is not zero.

When returning between invocations, keep working material in its assigned surface and state progress, remaining gap and the next action. Publish no terminal result merely because one internal step failed.

When the B ends, read [Batch result](../frontier-optimization/references/batch-result.md), validate the actual result once in draft and again against the published bytes, and return it. Include only evidence possible at the reached phase, actual consumption, output references and recovery information. Published candidate bytes must match their applicable passing checks and review.

The Coordinator owns plans, baseline/execution-start, Budget, Selection, adopted evidence, parents and claims. The worker writes only its assigned acknowledgment, working material, evidence, progress and result. Completion means every applicable deliverable and real consequence is accounted for; it does not grant the next action.
