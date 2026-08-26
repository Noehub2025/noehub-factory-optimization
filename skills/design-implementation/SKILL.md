---
name: design-implementation
description: Design or revise implementation architecture in a fresh context when frontier-optimization has fixed the behavior target and the work changes a shared interface, state ownership, interacting modules, migration, or another consequential technical seam.
---

# Design Implementation

Act as the sole professional author and reviser of a Frontier implementation design. Turn one fixed behavior target into a design that an executor can implement without inventing key semantics. Leave campaign routing, Batch continuation, formalization, identity, review, authority, Budget, result closure, and implementation to their existing owners.

## Require one bounded assignment

Require:

- one canonical Frontier task and exact project decision root;
- mode `new`, `revision`, or `repair`;
- one Coordinator-created W scaffold with fixed Purpose, semantic Scope, parents, source requirements, design-review repository evidence, exclusions, and exact writable sections and concern paths;
- the fixed route and behavior target, existing repository seams, runtime and resource constraints, and adopted user decisions;
- for `revision`, the current design and the evidence that requires a contract-bearing change; and
- for `repair`, the complete current design-review findings.

Read [Technical design](../frontier-optimization/references/technical-design.md) and the assigned W through [Work plan](../frontier-optimization/references/work-plan.md). Read repository files and external technical evidence only inside the assignment. Return `BLOCKED` before writing when the target or write surface is ambiguous.

This step is complete when the design question, evidence surface, and exclusive write surface are reproducible without conversation history.

## Check the seam before designing

Confirm that the work actually crosses a professional design trigger from Technical design. A bounded, reversible behavior change may touch multiple files and remain `direct` when established seams, ownership, interfaces, schemas, lifecycle, dependency direction, failure semantics, and migration remain unchanged.

Return `DIRECT_ELIGIBLE` without writing when the assignment was misrouted. Do not make this check a routine gate for work that the Coordinator has already proved direct.

This step is complete when the work is either returned as direct or has a concrete `module` or `system` reason.

## Reconstruct the implementation design

Inspect the current modules, callers, state, dependencies, runtime flow, failures, tests, and deployment or migration facts that bear on the fixed target. Keep parent-owned decisions with their owners:

- a route, solution identity, or investment change returns `PARENT_REVIEW_REQUIRED`;
- a measurement meaning change returns to the measurement owner;
- a user-owned cost, lock-in, maintenance, migration, privacy, or operating tradeoff returns `USER_DECISION_REQUIRED` with technically eligible options and a recommendation; and
- a conclusion that needs a lower-consequence observation from code execution, a prototype, an experiment, controlled input, an external effect, or protected resources returns `EVIDENCE_REQUIRED` with the smallest decision-changing evidence request; do not disguise the normal formal proposal as free design evidence.

Read-only design work is planning. It creates no B, proposal identity, reservation, or spend.

This step is complete when every unresolved item has one owner and no hidden execution is needed to support the proposed design.

## Challenge decisive feasibility claims

Apply [Technical design's decisive-feasibility rule](../frontier-optimization/references/technical-design.md#test-decisive-feasibility-claims) to the promised output. It owns the distinction between an executable research observation and complete final delivery, the required grounds, and evidence routing. Use its questions only for claims that determine whether that output can be delivered; ordinary implementation risk stays in the normal B.

This step is complete when each decisive claim for the promised output has positive grounds or one exact existing return boundary. Keep the reasoning in the owning concern.

## Author the existing design contract

Write only the assigned W `Design brief` and triggered concern files. For `module` or `system`, cover architecture, interfaces, flows, and verification; add domain or decisions only when their triggers apply. Apply security, performance, reliability, compatibility, migration, and rollback requirements in the owning concern when they materially affect the design.

In `verification.md`, make each delivery slice a stable, verifiable obligation with one observable behavior, prerequisite set, exact design inputs, distinguishing oracle, failure checks, and safe recovery point. Together the obligations must cover one complete realization. They do not prescribe the executor's mutable work breakdown or execution order. The Coordinator later maps those pointers to stable Delivery and traceability rows; Entry binds the exact delivery obligations one B must satisfy.

For any implementation-form restriction that materially affects a slice, apply [Technical design: Constrain effects, not convenient forms](../frontier-optimization/references/technical-design.md#constrain-effects-not-convenient-forms). State the current protection rationale and causal relation; do not optimize the design for an easy syntactic check.

Use schemas, examples, state tables, or sequence descriptions when prose would allow incompatible implementations. State the necessary technical constraints and leave ordinary work methods to the executor.

Apply [Technical design's assignment ownership rule](../frontier-optimization/references/technical-design.md#assign-the-professional-author). Treat incidental workflow wording as context, not professional content. When an unpublished assignment misplaces workflow requirements in Purpose or Scope, coordinate correction with the Coordinator on the same scaffold and continue the authoring task. Preserve explicit constraints with their existing owner. This is ordinary coordination on a discovered conflict, not a routine gate or a formal design failure; it creates no new W, revision, review, authority, identity, or repair artifact. Use the existing return paths only for genuinely unresolved technical, user, or authority decisions. Keep Batch continuation and publication mechanics with [Boundary-preserving continuation](../frontier-optimization/references/batch-interface.md#boundary-preserving-continuation).

Do not write Design map rows, Delivery map rows, `traceability.yaml`, design identities, lifecycle fields, V, B, Selection, Budget, review artifacts, candidate code, or campaign records. The Coordinator generates stable concern and slice bindings without changing professional meaning; it does not assign a future B or internal execution path into Design.

This step is complete when the assigned design files contain one coherent design and no other actor must fill a professional section.

## Finish at cold-read implementability

Return `DRAFT_READY` only when a fresh executor can implement every planned slice in dependency order, integrate the complete realization, and recover after any slice without inventing entity meaning, responsibility, interface behavior, state ownership, runtime transitions, failure response, compatibility behavior, test oracle, or recovery boundary. For `repair`, resolve every finding in the revised design or return the exact remaining blocker; create no separate finding-disposition artifact.

If execution evidence shows only that the order or internal split is inefficient, keep the design contract unchanged and let the Batch record a revised next action. If it shows that a slice cannot deliver its observable result without changing a public seam, ownership, lifecycle, acceptance meaning, or another load-bearing design assumption, identify the affected contract and return it to the Coordinator for a scoped design revision. Do not turn ordinary implementation defects into design changes or let an executor invent missing contract meaning.

Return exactly:

```text
RESULT: DRAFT_READY | DIRECT_ELIGIBLE | EVIDENCE_REQUIRED | USER_DECISION_REQUIRED | PARENT_REVIEW_REQUIRED | BLOCKED
Task: <canonical task path>
Mode: new | revision | repair
Work plan: <W path and revision>
Written design: <exact Design brief and concern paths, or none>
Technical slices: <exact verification pointers, or none>
Required next owner: <Coordinator | grill-frontier | research or B evidence path | parent stage | none>
Blocker: <omit when none>
```

These results are invocation outcomes only. They create no W lifecycle state, ledger entry, identity, readiness verdict, authority, spend, or implementation permission. Only an unchanged finding-free `DESIGN_READY` from `review-frontier`, followed by the existing Entry and authorization chain, can make the design eligible for development.
