---
name: design-implementation
description: Resolve an important implementation-design question in a fresh context when existing agreements do not settle shared behavior, state ownership, architecture, migration or another consequential technical choice.
---

# Design Implementation

Act as the sole professional author and reviser of a Frontier implementation design. Choose a realization worth trying within the assigned research problem and actual constraints, and make it implementable without inventing key semantics. Leave campaign routing, Batch continuation, formalization, identity, review, authority, Budget, result closure, and implementation to their existing owners.

## Require one bounded assignment

Require:

- one canonical Frontier task and exact project decision root;
- mode `new`, `revision`, or `repair`;
- the unresolved question, relevant existing agreements and evidence, and exact writable sections in current work or design material; include W when a shared design map is needed;
- the selected investment and behavior target, existing repository seams, actual runtime and resource constraints, and adopted user decisions;
- for `revision`, the current design and the evidence that requires a contract-bearing change; and
- for `repair`, the complete current design-review findings.

Read [Technical design](../frontier-optimization/references/technical-design.md), and [Work plan](../frontier-optimization/references/work-plan.md) only when W is used. Use [Evidence access](../frontier-optimization/references/worker-interfaces.md#evidence-access) for relevant original-source checks. Resolve a missing target or write surface with the Coordinator; a short source list does not itself block work.

This step is complete when the design question, evidence surface, and exclusive write surface are reproducible without conversation history.

## Check the seam before designing

Apply [Choose the profile](../frontier-optimization/references/technical-design.md#choose-the-profile) to distinguish the professional question, needed design content and any later independent judgment. Return `DIRECT_ELIGIBLE` without writing when established agreements already settle the important choices; do not routinely recheck the Coordinator's direct cases.

This step is complete when the remaining professional question and affected scope are clear, or the work is returned for direct implementation.

## Reconstruct the implementation design

Inspect the current modules, callers, state, dependencies, runtime flow, failures, tests, and deployment or migration facts that bear on the target. Apply [Ground consequential design choices](../frontier-optimization/references/technical-design.md#ground-consequential-design-choices) when selecting the realization. Keep parent-owned decisions with their owners:

- a change to the research problem or substantive investment returns `PARENT_REVIEW_REQUIRED`; refine tentative technical choices through [Working assignments](../frontier-optimization/references/worker-interfaces.md#working-assignments);
- a measurement meaning change returns to the measurement owner;
- a user-owned cost, lock-in, maintenance, migration, privacy, or operating tradeoff returns `USER_DECISION_REQUIRED` with technically eligible options and a recommendation; and
- a consequential assumption needing practical feedback follows [Early design feedback](../frontier-optimization/references/technical-design.md#early-design-feedback): name the uncertainty and smallest useful observation, obtain it through the existing work owner, and continue the original design task.

Read-only design work is planning. It creates no B, proposal identity, reservation, or spend.

This step is complete when every unresolved item has one owner and no hidden execution is needed to support the proposed design.

## Challenge decisive feasibility claims

Apply [Technical design's decisive-feasibility rule](../frontier-optimization/references/technical-design.md#test-decisive-feasibility-claims) to the promised output. It owns the distinction between an executable research observation and complete final delivery, the required grounds, and evidence routing. Use its questions only for claims that determine whether that output can be delivered; ordinary implementation risk stays in the normal B.

This step is complete when each decisive claim for the promised output has positive grounds or one exact existing return boundary. Keep the reasoning in the owning concern.

## Author the existing design contract

Write the assigned answer or affected existing design content, creating only the concerns needed by the current problem under Technical design. Preserve applicable security, performance, reliability, compatibility, migration and recovery requirements with their owning agreement.

Where W carries stable delivery obligations, define them through [Verification](../frontier-optimization/references/technical-design.md#verification). The Coordinator maps those pointers to Delivery and traceability; Entry binds only the obligations its B depends on. Otherwise reference existing applicable checks in the answer. Ordinary test methods and mutable work breakdown remain with the implementer.

For any implementation-form restriction that materially affects a slice, apply [Technical design: Constrain effects, not convenient forms](../frontier-optimization/references/technical-design.md#constrain-effects-not-convenient-forms). State the current protection rationale and causal relation; do not optimize the design for an easy syntactic check.

For any condition that can reject the implementation or produce a broader disposition, apply [Frontier Core: Decision-bearing thresholds](../frontier-optimization/references/frontier-core.md#decision-bearing-thresholds). Cite the current owner when the condition belongs to a parent, Measurement Definition, direct B, or execution control. Write a normative threshold in W only when W owns implementation acceptance, and then include its current basis, applicable conditions and statistic, allowed consequence, and reconsideration trigger. Treat the same value under a different workload, aggregation, scope, or consequence as changed meaning. Do not create a second threshold source or ask for routine freshness evidence when the complete meaning is unchanged.

Use schemas, examples, state tables, or sequence descriptions when prose would allow incompatible implementations. State the necessary technical constraints and leave ordinary work methods to the executor.

Apply [Technical design's assignment ownership rule](../frontier-optimization/references/technical-design.md#assign-the-professional-author) when tentative choices or workflow methods have been misplaced in Purpose or Scope. Correct the scaffold with the Coordinator in the same task. Keep Batch continuation with [Boundary-preserving continuation](../frontier-optimization/references/batch-current.md#boundary-preserving-continuation).

When W is used, the Coordinator owns maps, traceability, lifecycle fields and the consuming saved reference under [Work Plan](../frontier-optimization/references/work-plan.md#saved-design-references). Keep V, B, Selection, Budget, review artifacts, candidate code and campaign records with their existing owners.

This step is complete when the assigned content answers the professional question, relevant decision-bearing thresholds retain their grounds and owners, and no consequential meaning needed by the promised use remains implicit.

## Finish at cold-read implementability

Return `DRAFT_READY` when consequential choices have the grounds described above and a fresh executor can implement and integrate the promised realization under [Verification's implementability boundary](../frontier-optimization/references/technical-design.md#verification). Remaining ordinary implementation choices and unknown research outcomes are work to investigate, not missing design obligations. For `repair`, resolve the supplied findings and any newly discovered fact affecting those grounds; reuse unaffected conclusions and return an exact remaining blocker when necessary. Create no separate finding-disposition artifact.

If execution evidence shows only that the order or internal split is inefficient, keep the design contract unchanged and let the Batch record a revised next action. If it shows that a slice cannot deliver its observable result without changing a public seam, ownership, lifecycle, acceptance meaning, or another load-bearing design assumption, identify the affected contract and return it to the Coordinator for a scoped design revision. Do not turn ordinary implementation defects into design changes or let an executor invent missing contract meaning.

Return exactly:

```text
RESULT: DRAFT_READY | DIRECT_ELIGIBLE | EVIDENCE_REQUIRED | USER_DECISION_REQUIRED | PARENT_REVIEW_REQUIRED | BLOCKED
Task: <canonical task path>
Mode: new | revision | repair
Work plan: <W path and revision, or none>
Written design: <assigned answer or affected design paths, or none>
Technical slices: <exact verification pointers, or none>
Required next owner: <Coordinator | grill-frontier | existing evidence-work owner | parent stage | none>
Blocker: <omit when none>
```

These results are invocation outcomes only. They create no lifecycle state, review verdict, Permission, spend or implementation result. The Coordinator adopts the answer through [Review and revision](../frontier-optimization/references/technical-design.md#review-and-revision), selects any remaining required independent judgment, and continues the covered work under its actual Entry and V conditions.
