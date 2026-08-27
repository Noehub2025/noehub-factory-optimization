# Entry Planning for Executable Candidate Work

Load only when an eligible Entry B may create or change executable candidate code. This file connects Entry planning to the technical-design and candidate-code gates without making every Entry load those systems.

## Assess repository fit

Inspect the existing project structure, build and dependency conventions, candidate interface, source base, tests, every selected test or check unit and its possible execution effects, exclusive worker write surfaces, worker-forbidden paths, execution-frozen inputs, the Coordinator lifecycle transition, exclusive execution-baseline root, execution-start path, package-inventory path, final-manifest path, result-validation path, and workspace isolation.

Record one disposition:

- `existing-integrated`: use the established structure and seam;
- `new-in-scope`: select a suitable layout within the current grant;
- `user-choice-needed`: a specific unresolved value or access decision prevents selecting the layout;
- `incompatible`: explain the conflict and return to route or design planning.

The technical owner selects layout and tools within the objective and constraints. Use [User decisions](user-decisions.md) only when that choice changes a user-owned value or permission boundary; an absent structure alone is not a reason to ask.

## Choose the design profile

Load [Technical design](technical-design.md). The Coordinator may choose `direct` only when every direct condition is supported by repository facts and change scope. Otherwise create a W scaffold and invoke `design-implementation` in a fresh context; the designer selects `module` or `system` and authors the professional design.

- `direct`: the exact B fully specifies one bounded reversible behavior change through established seams. It may touch multiple files when ownership, interfaces, schemas, lifecycle, dependency direction, failure semantics, and migration remain unchanged. No design W or design review is required.
- `module`: `design-implementation` writes the Design brief and triggered concern files for one module or stable seam.
- `system`: `design-implementation` writes the Design brief and every applicable concern file for cross-module interaction, state ownership, migration, external operation, or coordinated rollout.

Load [Work plan](work-plan.md) only for `module` or `system`. The Coordinator owns the W scaffold, lifecycle, Design map, stable Delivery map, traceability, and identities; it mechanically binds the designer's exact concern and slice pointers without rewriting professional meaning or assigning a future B, attempt, internal path, or runtime status into Design. Resolve every user-owned design choice as V and return contract-bearing answers to the designer before freezing the design.

## Separate the gates

For `module` or `system`, adopt an applicable `DESIGN_READY` before preparing its Entry realization. For `direct`, record reproducible profile evidence without a design review. In both cases, prepare the complete B and use the current Entry checks once.

Apply [User decisions](user-decisions.md). If the realization fits an adopted grant, use spend-readiness and bind current execution authority without asking again. Otherwise obtain `AUTHORIZATION_READY`, ask only for the missing user-owned permission and adopt that answer. Design preference, `DESIGN_READY` and packet structure do not themselves grant execution permission.

A changed technical contract needs the affected design review and current execution binding. It does not automatically revoke a broader user grant. Use Batch continuation for delegated same-packet design changes or Entry spend-readiness for a new realization.

Design authoring itself is planning and creates no B or proposal identity. Account for actual resources under the parent rule. When the designer returns `EVIDENCE_REQUIRED`, obtain only decision-relevant evidence through the existing research, prototype or B path, then revise the affected design.

## Plan candidate identity and review

Load [Candidate lifecycle](candidate-lifecycle.md). Give every materialized implementation a pinned execution source, assigned workspace, allowed paths, interface, configuration space, transient evidence paths, official package-inventory path, final-manifest path, engineering checks, implementation-review path, and recovery point. When the parent Budget uses proposal, candidate, attempt, or an equivalent search-opportunity unit, cite the parent or R8 rule that owns the first formal identity, amount, and charge event in the existing B plan; do not copy it into another policy object. Otherwise record proposal charge as `not applicable`. Freeze every selected check unit, exact argument vector, content-addressed effect-classification source, and positive cumulative effect maximum across all attempts. A full or opaque suite is eligible only when that evidence bounds every possible effect. Keep local engineering fixtures separate from candidate performance measurement and limit their consequence to engineering evidence.

Every materially changed executable candidate must stop for fresh implementation review before its first Slot H measurement or mainline integration. Unpublished working material may receive a bounded observation inside the same B only through [Batch Interface](batch-interface.md#bounded-observations-before-publication). A separate diagnostic-only B before review is limited to the historical published-candidate exception in [Candidate lifecycle](candidate-lifecycle.md#diagnostic-only-exception); record its exact result branches, isolation, prohibited consequences, and stop boundary. Record the implementation-review checkpoint, review packet path, and protected follow-up budget in B and Selection. Keep E, integration, incumbent use, promotion, and claim use as later Coordinator decisions.

Before freezing a first code B, run the current project preparation checks selected by [Batch interface](batch-interface.md) and require ownership, complete `delivery_scope`, frozen-subtree, required-output, prohibition, path-schema, and identity checks to pass. Use `scripts/validate_batch_packet.py` only for an exact historical object admitted by its legacy compatibility branch. Also prove that acknowledgment returns before any work or spend, the only required post-acknowledgment campaign edit is the exact `planned -> running` transition, the Coordinator freezes every post-transition input byte under the assigned execution-baseline root, and the worker starts only from the execution-start record that binds that snapshot. Require the current profile-aware draft and frozen result validation before the final result path. Do not freeze the whole W or a mutable implementation breakdown. Do not put the lifecycle edit, packet preflight, execution-baseline root, execution-start record, or any worker output under an execution-frozen directory. A worker-forbidden campaign path may remain Coordinator-owned; it is not globally immutable unless listed separately with an exact execution-frozen identity.

Code planning is complete only when the selected B can satisfy its complete `delivery_scope` without requiring its executor to invent architecture, entity meaning, interface contracts, data flow, user choices, test oracles, or rollback behavior.
