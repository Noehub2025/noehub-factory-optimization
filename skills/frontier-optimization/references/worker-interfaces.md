# Frontier Worker Interfaces

Load this file before any worker delegation. It defines non-overlapping write authority and the small research and user-decision packets. Batch and review branches have separate action files.

## Permissions

The Coordinator assigns exact writable files or sections before invocation. No Coordinator and worker permission names the same section.

Every new worker assignment cites the exact decision root and only the project
content roots needed for that assignment. The
worker verifies the typed project chain and recomputes those project roots.
It does not receive workflow source, Skill, validator implementation, release,
or source-module roots. Workflow source closure is checked when the workflow
release is published or installed, where a Git commit or signed tag may identify
the release. Updating or replacing the installed workflow never changes an
assignment, project identity, review, or spend gate. The complete historical
`workflow_source_binding` protocol is available only to an exact-inventory
version 1 audit reader. It cannot create a current assignment, review,
authority, or execution.

| Actor | May write | Meaning | Cannot write or decide |
|---|---|---|---|
| `frontier-optimization` | `FRONTIER.md`; `log.md`; ledger, bounds, claims; W Purpose, Scope, lifecycle, Design map, Delivery map, user-decision links, traceability, identities, Validation, Definition of done, Recovery, and Outcome; mechanical concern-frontmatter bindings; Coordinator packets, execution-baseline snapshots, and execution-start records | Checked adoption changes campaign meaning; mechanical design bindings preserve the professional author's exact pointers; an execution-start record releases one accepted packet only after it binds a complete content-addressed baseline snapshot | W Design brief or professional concern bodies; worker evidence/result packets or result validation; W worker progress/discoveries; review artifacts; parents |
| `design-implementation` | One assigned W Design brief and the professional bodies of triggered architecture, domain, interfaces, flows, decisions, and verification concern files | Proposed professional implementation design only; its invocation result creates no lifecycle state, identity, review verdict, authority, B, reservation, or spend | Purpose, Scope, Current state, Design map, Delivery map, user-decision adoption, traceability, identities or mechanical concern-frontmatter bindings, Validation, Definition of done, progress/discoveries, Recovery, Outcome, campaign records, reviews, candidate code, execution, measurement, route, or parent contracts |
| `research-frontier` | One assigned research evidence section and result packet | Proposed Q or D evidence | Campaign records, W, reviews, parents, selection, adoption |
| `grill-frontier` | One assigned answer packet | Preserved user answer | Task documents, V adoption, technical eligibility, consequence |
| `run-frontier-batch` | Assigned acknowledgment; code/artifacts; candidate package inventory; final candidate manifest; result-validation artifact; result packet; assigned W progress/discoveries | Evidence only; result validation grants no campaign meaning | Worker-forbidden paths; execution-baseline snapshots; execution-start records; W contract sections; design concern contracts; campaign records; reviews; E adoption; integration; promotion; stop; claims |
| `review-frontier` | One assigned immutable review artifact | Verdict limits later adoption | Campaign records, packets, W/design/code/evidence, repair, user choices, spend, integration, promotion, publication |

When required work falls outside the assignment, return proposed content and the exact target without writing it. In particular, an executor reports a shared-interface or other contract-bearing discovery through its result packet. The Coordinator opens and scopes a new W revision; only `design-implementation` revises professional design content, and only the Coordinator regenerates lifecycle and mechanical bindings.

Within its assigned write surface, `run-frontier-batch` applies [Boundary-preserving continuation](batch-interface.md#boundary-preserving-continuation) before publishing a terminal result. This permission preserves the existing B envelope; it never expands paths, semantics, authority, side effects, or spend.

For code-bearing work, the packet freezes one task-neutral engineering check plan. Entry validation verifies the selected units, content-addressed effect sources, and positive limits before snapshot creation; the Entry reviewer judges whether the declared effect closure is semantically sufficient. The worker repeats the selected-unit and effect-limit comparison before execution. A full repository suite is an opaque executable surface unless all collected units and effects are bounded; a zero limit and a selected check that can produce that effect is a blocker. Engineering-only local fixtures grant no measurement or strength consequence.

For experiment work, packet and result share the canonical nested `evaluation_target` from Batch Interface. The worker copies that complete mapping exactly into the result and does not invent flat candidate, experiment, implementation-review, or Slot H aliases. `evaluation_target.experiment` alone owns the experiment identity; prose fields may refer to it but cannot copy the identity. Packet preflight must inventory the complete candidate root, derive the experiment identity from its source bytes, and prove the result contract can be satisfied before Entry review.

For `routine-local`, the Coordinator must first release the execution through the single-use admission in [Evaluation protocol reuse](evaluation-protocol.md). The worker may execute only the frozen schedule and must copy the structured evidence scope into each result. A packet or acknowledgment without the released execution and consumed slot is not sufficient authority.

Do not use worker write protection as a global drift rule. `worker_forbidden_paths` answer who may write. `execution_frozen_inputs` separately answer what no actor may change after execution start. The Coordinator may perform only the reviewed post-acknowledgment transition: replace each listed file with its complete `frontier-post-adoption-state/1` bytes, capture the required lifecycle UTC instant when applicable, and bind the derived receipt and every post-change file into the execution baseline and execution-start. The Coordinator-owned baseline tool recomputes the project-bound packet, Entry adoption, validation, and acknowledgment from the immutable pre-transition snapshot, then separately proves that the live reviewed files equal their post-state bytes and every other snapshot-copy input stayed unchanged. After that record, the worker enforces the dispatch identities, receipt identity, and live equality with the snapshot through result validation.

## Research packet

Name `target_id`, exact `decision_root`, `research_mode: route_landscape | focused_question`, exact question, parent bindings, applicability, decision the answer can change, materially different findings and their recorded consequences, evidence channels, action window, fixed search stop, assigned evidence section, result-packet path, and completion check.

A route-landscape packet also names comparison dimensions, reviewed scope, repository and retained evidence, and any reopened exclusion or shared high-consequence assumption. It asks the worker to map decision-relevant established approach families, representative implementations, known failures, and applicable functional transfer evidence. A post-result focused packet names the triggering Outcome Reflection and why cheaper local evidence is insufficient.

The result uses Q or D fields, reports `outcome: completed | blocked | evidence_required`, and names missing evidence when incomplete. Research supplies evidence; it does not approve, select, require, or score a route and cannot establish originality or exhaustive coverage.

## User-decision packet

Name `target_id`, exact `decision_root`, `decision_kind: tradeoff | authorization`, exact decision, evidence, affected records, conditions, reconsideration trigger, and result-packet path. Record an explicit campaign-opening answer directly from the current request; do not delegate a question whose answer is already present.

A tradeoff packet gives at least two technically eligible alternatives. An authorization packet gives one exact immutable object, scope, reviewed basis, next action, limits, and consequences of authorize, decline, and conditional authorization. When the object names a concrete B packet, it also gives unchanged finding-free `AUTHORIZATION_READY`, structural preflight, Entry schema, and target identities. Any missing, failed, stale, or mismatched gate makes the object ineligible to present. The result uses every V field and preserves the user's exact answer without adopting it.
