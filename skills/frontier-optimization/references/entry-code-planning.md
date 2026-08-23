# Entry Planning for Executable Candidate Work

Load only when an eligible Entry B may create or change executable candidate code. This file connects Entry planning to the technical-design and candidate-code gates without making every Entry load those systems.

## Assess repository fit

Inspect the existing project structure, build and dependency conventions, candidate interface, source base, tests, every selected test or check unit and its possible execution effects, exclusive worker write surfaces, worker-forbidden paths, execution-frozen inputs, the Coordinator lifecycle transition, exclusive execution-baseline root, execution-start path, package-inventory path, final-manifest path, result-validation path, and workspace isolation.

Record one disposition:

- `existing-integrated`: use the established structure and seam;
- `user-approved-new`: create only the layout in the cited V authorization;
- `absent-awaiting-user`: recommend a layout and stop before creating code paths;
- `incompatible`: explain the conflict and return to route or design planning.

If no usable project structure exists, or the proposal materially changes the top-level layout, toolchain, dependency manager, or public entrypoint, present technically eligible options and a recommendation through `grill-frontier`. The user's answer chooses among eligible consequences; it cannot make an invalid structure valid.

## Choose the design profile

Load [Technical design](technical-design.md). The Coordinator may choose `direct` only when every direct condition is supported by repository facts and change scope. Otherwise create a W scaffold and invoke `design-implementation` in a fresh context; the designer selects `module` or `system` and authors the professional design.

- `direct`: the exact B fully specifies one bounded reversible behavior change through established seams. It may touch multiple files when ownership, interfaces, schemas, lifecycle, dependency direction, failure semantics, and migration remain unchanged. No design W or design review is required.
- `module`: `design-implementation` writes the Design brief and triggered concern files for one module or stable seam.
- `system`: `design-implementation` writes the Design brief and every applicable concern file for cross-module interaction, state ownership, migration, external operation, or coordinated rollout.

Load [Work plan](work-plan.md) only for `module` or `system`. The Coordinator owns the W scaffold, lifecycle, Design map, Delivery map, traceability, and identities; it mechanically binds the designer's exact pointers without rewriting professional meaning. Resolve every user-owned design choice as V and return contract-bearing answers to the designer before freezing the design.

## Separate the gates

For `module` or `system`:

1. Require `design-implementation` to return `DRAFT_READY`, then complete the W map and traceability mechanically from its exact concern and technical-slice pointers.
2. Load [Design review](design-review.md) and adopt only `DESIGN_READY` for an unchanged design identity.
3. Complete the machine-readable W traceability binding, draft the first code B packet, run finding-free draft and frozen structural preflight from `batch-interface.md`, and preserve its exact identity.
4. Freeze a complete authorization-readiness Entry snapshot and adopt only a finding-free `AUTHORIZATION_READY` for the exact target.
5. Ask the user separately to authorize that reviewed candidate-development target. Adopt it only through the post-answer identity and staleness check; store current authorization outside W.

For `direct`, record reproducible profile evidence, complete every packet field except `packet_id`, run finding-free draft preflight, insert only the computed identity, freeze the packet, reproduce the same PASS artifact in frozen preflight, obtain `AUTHORIZATION_READY`, and only then ask the user to authorize that reviewed packet, preflight, source base, scope, spend, and stop boundary.

Design preference, Coordinator design adoption, `DESIGN_READY`, and packet structural preflight do not authorize development. Any contract-bearing design or traceability change creates a new `plan_revision` and invalidates its review, authorization-readiness verdict, and every development authorization bound to the old identity.

Design authoring itself is planning and creates no B, proposal identity, reservation, or spend. When the designer returns `EVIDENCE_REQUIRED`, obtain only the named executable evidence through the existing research, prototype, or B path, then start a scoped design revision.

## Plan candidate identity and review

Load [Candidate lifecycle](candidate-lifecycle.md). Give every materialized implementation an immutable candidate identity, pinned source base, assigned workspace, allowed paths, interface, configuration space, package-inventory path, final-manifest path, engineering checks, and recovery point. Resolve the exact proposal charge event from the parent or R8; if neither defines one, record the workflow default explicitly in `frontier-authoritative-output-publication/1`. Freeze every selected check unit, exact argument vector, content-addressed effect-classification source, and positive cumulative effect maximum across all attempts. Assign the engineering-evidence path before Entry. A full or opaque suite is eligible only when that evidence bounds every possible effect. Keep local engineering fixtures separate from candidate performance measurement and limit their consequence to engineering evidence.

Every materially changed executable candidate must stop for fresh implementation review before its first Slot H measurement or mainline integration. A separate diagnostic-only experiment may precede that review only through every condition in [Candidate lifecycle](candidate-lifecycle.md#diagnostic-only-exception); record its distinct B, exact result branches, local isolation, prohibited consequences, and stop boundary. Record the implementation-review checkpoint, review packet path, and protected follow-up budget in B and Selection. Keep E, integration, incumbent use, promotion, and claim use as later Coordinator decisions.

Before freezing a first code B, run `scripts/validate_batch_packet.py` and require every ownership, W evidence-destination, frozen-subtree, required-output, prohibition, path-schema, and identity check to pass. Also prove that acknowledgment returns before any work or spend, the only required post-acknowledgment campaign edit is the exact `planned -> running` transition, the Coordinator freezes every post-transition input byte under the assigned execution-baseline root, and the worker starts only from the execution-start record that binds that snapshot. Require draft and frozen `validate_batch_result.py` before the final result path. Do not freeze the whole W. Do not put the lifecycle edit, packet preflight, execution-baseline root, execution-start record, or any worker output under an execution-frozen directory. A worker-forbidden campaign path may remain Coordinator-owned; it is not globally immutable unless listed separately with an exact execution-frozen identity.

Code planning is complete only when the selected B can reach one observable vertical slice without requiring its executor to invent architecture, entity meaning, interface contracts, data flow, user choices, test oracles, or rollback behavior.
