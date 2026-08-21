# Frontier Entry and Planning

## Contents

- [Load only what Entry reaches](#load-only-what-entry-reaches)
- [Validate the handoff](#1-validate-the-handoff)
- [Open a post-closeout recovery campaign](#open-a-post-closeout-recovery-campaign)
- [Initialize the campaign](#2-initialize-the-campaign)
- [Build a decision-grade route landscape](#3-build-a-decision-grade-route-landscape)
- [Create eligible plans](#4-create-eligible-plans)
- [Resolve user-owned choices](#5-resolve-user-owned-choices)
- [Plan the first observable work](#6-plan-the-first-observable-work)
- [Select reproducibly](#7-select-reproducibly)
- [Pin the Entry snapshot](#8-pin-the-entry-snapshot)
- [Obtain independent Entry review](#9-obtain-independent-entry-review)
- [Record one outcome, then finalize the return](#record-one-outcome-then-finalize-the-return)

Use this stage when no campaign exists, Entry is incomplete, or `frontier-core.md` selected post-closeout recovery mode. Its only successful outcome is one reviewed, reproducible first-batch plan with zero new-generation B spend and fully accounted inherited and Entry cost.

## Load only what Entry reaches

Load [Campaign state](campaign-state.md) and [Planning records](planning-records.md). Load [Evidence records](evidence-records.md) in post-closeout recovery mode. Load [Worker interfaces](worker-interfaces.md) before delegating research, a user decision, Entry review, or any other worker action. Load [Batch interface](batch-interface.md) before freezing any selected first-B packet. If any eligible first batch may change executable code, load [Entry code planning](entry-code-planning.md). When recovery proposes an existing candidate for measurement, load [Candidate lifecycle](candidate-lifecycle.md), [Review snapshots](review-snapshots.md), and [Implementation review](implementation-review.md). Load [Entry review](entry-review.md) only after the proposed Entry artifacts are frozen.

## 1. Validate the handoff

Bind the exact Problem epoch, Representation revision, generation times, positive reviews, reference baseline, measurement identity, exact `Permitted` text, R1-R8, budget authority, and claim limits. Copy no broader meaning into Frontier records.

Record `PARENT_REVIEW_REQUIRED` without creating campaign state when a required parent, review, measurement, budget rule, or R8 instruction is missing, stale, conflicting, or ambiguous, then use the finalization section below. Do not repair parent documents here.

### Rebind a compatible pre-spend campaign

Use this path only when `frontier-core.md` selected pre-spend parent-rebind mode.

1. Verify every rebind condition against current parents, accounting, repository paths, and the upstream disposition. Treat missing candidate or result paths as evidence only after checking the assigned locations.
2. Append X dispositions for the old Selection, selected B, W, Entry packet, review, worker packets, development authorization, and `FIRST_BATCH_PLANNED` authority. Preserve Q, T, V, E, or other adopted evidence only when the upstream disposition names the record reusable and every cited identity still resolves. Unclassified evidence is not retained.
3. Never edit an old B, W, packet, project snapshot, review, or worker result. Create new identifiers for replacement B and W records. `FRONTIER.md` remains the current view and may be rewritten only after the ledger records the disposition and replacement lineage.
4. Append `PARENT_REBIND_STARTED` to `log.md` with old and new parent identities, zero-spend evidence, the upstream disposition, retained and replaced identifiers, and the exact consequence that no B is executable.
5. Continue the normal Entry procedure under the new parents. Reconcile Entry cost, create replacement records from current templates, freeze one filtered immutable project snapshot, and obtain a new Entry review.

The rebind completes only when the Coordinator adopts an unchanged finding-free `ENTRY_READY` and appends `FIRST_BATCH_PLANNED` plus `PARENT_REBOUND` with the new snapshot, review, replacement lineage, and zero-B-spend evidence. Otherwise the old campaign remains preserved and unauthorized.

### Open a post-closeout recovery campaign

Use this path only when `frontier-core.md` selected post-closeout recovery mode.

1. Verify unchanged positive parents, a complete prior `CLOSEOUT_COMPLETE`, final accounting, no unresolved C branch, no active worker, the highest campaign generation, and the exact current user request. Treat legacy records without a generation as generation 1.
2. When the request reuses a materialized candidate, build a temporary recovery preflight and run `scripts/validate_candidate_recovery.py` in draft mode before creating any new-generation artifact. Recompute the manifest, every candidate member, and package identity from canonical bytes. An eligible version 2 manifest uses only the exact-inventory legacy reader and remains byte-identical; a current version 3 manifest contains no workflow identity. A mismatch returns `BLOCKED` with no V, X, review, generation update, or spend. On PASS, insert only the computed project identity, freeze the preflight at a new path, and reproduce finding-free frozen validation.
3. Increment `campaign_generation`. Append a `campaign-opening` V that quotes the explicit current request and binds the prior closeout, unchanged parents, proposed generation, inherited Budget, and `planning only; zero B spend`. The Coordinator derives the proposed technical objective from the current parent handoff, active D, F5-F6, retained E, final Outcome Reflection, X route dispositions, and closeout handoff. Do not claim the user chose that objective. Require a user-named objective only when the request names a particular recovery object or outcome. Append X dispositions that map every reused evidence object into the new generation. Closed authority remains closed; unclassified objects are not reusable.
4. Carry the parent budget ceiling and all prior, Entry, B, external-action, and unknown spend forward. Releasing an old reserve does not restore authority by itself. New reservations come only from the new Budget and Selection.
5. Use new V, X, W, B, review, packet, acknowledgment, execution-start, result, and log identifiers. Never edit or reuse a closed identifier. Preserve old snapshots and results byte for byte.
6. Reuse current Q, T, V, design, engineering, or reference evidence only when its cited identity still resolves and X states its new-generation role and limits. Test the Coordinator-derived objective through the normal route-generation and Q reconciliation below. Revise it when evidence requires while staying inside parent authority. Use a separate V only for a remaining user-owned route tradeoff, and keep exact first-B authorization separate again.
7. For a byte-identical materialized candidate, bind the frozen finding-free recovery preflight before planning measurement. Reuse creates no new proposal attempt. Freeze a new `review_mode: recovery-reuse` implementation snapshot and adopt only unchanged `IMPLEMENTATION_READY`; the old implementation verdict remains historical and cannot become positive retroactively.
8. If recovery review is positive, plan the first B as a separate experiment with `changes_executable_candidate: false`, a complete evaluation target, and the normal two-phase dispatch. If it is nonpositive, preserve it and plan only the exact repair, evidence, or stop consequence it permits. Any candidate byte or behavior change needs a new code-bearing B, current development authorization, and one new proposal attempt.
9. Append `RECOVERY_CAMPAIGN_STARTED` to `log.md`, update `FRONTIER.md` to the new generation and `campaign_status: planned`, and continue normal Entry planning. The first new-generation B still requires a fresh immutable Entry snapshot and finding-free `ENTRY_READY`.

Recovery does not make the preserved candidate an incumbent, campaign result, or performance claim. It becomes a campaign-baseline candidate only through the new Selection and enters F4 only after valid measurement and retention.

## 2. Initialize the campaign

For generation 1, create only the canonical paths from `frontier-core.md`, append `FRONTIER_STARTED`, and initialize F1-F8, Budget, and E001. For post-closeout recovery, use the recovery procedure above and append within the existing canonical files. Record Entry planning and research cost separately when the governing accounting rule charges it.

Keep E001 as the current-epoch reference baseline. F1 must reproduce the exact reviewed scope. F2 must distinguish total budget, prior spend, reservations, actual spend, required follow-up reserve, and remaining balance. F7 and F8 must preserve every inherited stop, halt, reachability, comparison, and claim limit.

## 3. Build a decision-grade route landscape

First fix the current allocation decision, exact reviewed scope, parent objective and measurement meaning, repository and retained evidence, observed constraints and failures, permitted design freedoms, Budget horizon, and one bounded search-and-generation stop.

Treat established approaches, repository evidence, observed failures, functional transfer or recombination, migration or reorganization, and new mechanism reasoning as peer route sources. No source must be exhausted before another can produce a provisional route, and external retrieval is not permission to reason. Before or while research runs, preserve provisional mechanism opportunities supported by bound evidence. They grant no Selection, B, or spend authority and create no new record type.

Create one route-landscape Q target. The packet must name the decision, reviewed scope, comparison dimensions, required evidence channels, repository evidence, action window, search stop, evidence path, and result path. Use `research-frontier` to map decision-relevant established approach families, representative current implementations, known failures, and applicable transfer evidence. Treat relevant read-only external research as planning unless an exact parent or user rule prohibits that access. A restriction on execution, spend, remote side effects, publication, or claims does not make a read-only evidence channel inapplicable. Mark a channel inapplicable only when it cannot affect the decision, cannot be reached within the action window, or exact authority prohibits that access; cite the reason and preserve useful negative searches.

Adopt the checked result as Q, then reconcile it with provisional mechanisms, retained evidence, failures, transfers, migrations, reorganizations, and applicable new mechanisms. Research may challenge, bound, merge, or defeat a provisional route; it does not approve, require, or select one. Stop when the route set is complete for the current decision: eligible routes and bounded exclusions suffice for the next allocation, further retrieval or mechanism synthesis is unlikely to change it, and each material deferred or excluded mechanism class has an evidence-backed reason and observable reopening event when one exists. This is decision completeness, not exhaustive coverage, proof of originality, or proof that no better route exists. Reconcile charged Entry cost before planning B reservations.

## 4. Create eligible plans

Create a T for every materially different technically eligible route or campaign-baseline approach and apply the canonical [T eligibility contract](planning-records.md#t-route). Do not create a T merely to represent a source category, minor parameter variant, or ceremonial alternative.

Before admitting a route, disposition every load-bearing prerequisite through that contract. An unresolved but reachable prerequisite selects only its smallest sufficient check. An unavailable or failed prerequisite excludes or defers the route, and dependent implementation remains ineligible until new passing evidence completes the applicable Entry or Replan gate.

For every iterative T, record a defensible prospective progress rule, mechanism checkpoint, or reachability condition before governed spend, or justify `not applicable`. Do not invent a number merely to complete the template.

Apply the canonical R8 vacuity definition to the first planned check. Current evidence that proves every legal result maps to the same allowed next action makes candidate or evaluation work ineligible. Unknown headroom, noise, resolution, representativeness, or proxy usefulness may instead select the smallest bounded prerequisite or diagnostic check when its possible results change the permitted next action.

Reject routes outside exact `Permitted` scope before user preference. Judge established and new routes by mechanism, eligibility, reachability, and discriminating evidence, not novelty or maturity alone. Do not invent expected improvement, probability, route scores, calendar estimates, originality claims, or tie-breaks.

When only one approach is technically eligible, the reconciled Q and proposed Selection must disposition only the material decision-relevant mechanism classes considered, with evidence and a reopening event when one exists. Do not demand every imaginable approach. Create no fake alternative T and request no campaign-baseline tradeoff V. A shared untested high-consequence assumption keeps the route set incomplete when bounding it could change the allocation, unless the exact parent contract fixes it.

## 5. Resolve user-owned choices

Technical evidence determines eligibility. Use `grill-frontier` when eligible alternatives differ in user value, cost, lock-in, reversibility, maintenance, operations, deadline, privacy, safety tolerance, or risk.

For a campaign-baseline choice, present at least two eligible starting points unless the evidence proves only one is eligible. Explain why each can support later optimization, what it costs to establish, when it should be replaced, and which evidence interfaces remain stable. Recommend one when evidence supports it; do not imply that the baseline must itself be the strongest eventual solution.

Adopt each answer as V. A user choice cannot widen scope, waive measurement, prove a technical claim, or authorize candidate development unless it is a separate authorization V for one exact object.

<a id="select-the-first-work"></a>

## 6. Plan the first observable work

Create the first B from its sole template. Create W only when the work is complex, spans checkpoints, or needs a technical-design map. Do not create empty W or design-concern scaffolding to satisfy a form. A complex non-code W uses one reasoned `not applicable` Design-map row and no technical-design concern files. Every selected B must precommit:

- decision hypothesis;
- expected observation;
- decision rule for continue, diagnose, research, revise, promote, stop, or halt;
- exact first checkpoint and first performance check;
- preparation budget limit and protected follow-up reserve;
- legality, engineering, measurement, and comparison-validity checks;
- recovery point, stop conditions, and prohibited actions.

List the legal result branches for the first check and their distinct allowed next actions. When the check answers an unknown measurement property, stop at that observation and preserve its decision and claim boundary. When a materialized candidate uses the diagnostic-only exception in `candidate-lifecycle.md`, plan a separate non-code experiment B and keep formal Slot H measurement, E, integration, incumbent use, promotion, and strength claims closed.

Also record `Trajectory contribution` before execution. For prerequisite-first work, bind the output and stop boundary to the prerequisite observation and make dependent implementation explicitly ineligible until the Coordinator adopts passing evidence through the applicable Entry or Replan gate.

Its packet must also separate worker write surfaces, worker-forbidden paths, and execution-frozen inputs; assign exclusive Coordinator-owned packet-preflight, execution-baseline, and execution-start paths plus a worker-owned result-validation path; and use the structured post-acknowledgment lifecycle rule from Batch Interface when the campaign is planned. For W-backed work, bind machine-readable design traceability and never freeze the whole W. Run draft structural preflight from transient files before publishing packet or review artifacts. A failed draft may be repaired within the same B only under the unchanged-boundary rule in Entry Review; it creates no review assignment, snapshot, user question, or successor B. Publish and freeze the packet and preflight only after the draft is finding-free, then reproduce frozen validation before Entry snapshot creation. The Entry plan is invalid if any W evidence destination is unassigned, if following Campaign Cycle would trigger drift, if a runtime timestamp or date is frozen as a packet literal, if the worker could begin before every post-transition byte has a recoverable snapshot, or if a final result could be written before profile-aware validation.

Preparation must end at the earliest check that can discriminate the chosen mechanism. A baseline-establishment slice may be simple, but it cannot become open-ended infrastructure work.

If the B may change executable candidate code, complete `entry-code-planning.md` before selection. A design, research, or isolated prototype B must explicitly state `changes_executable_candidate: false`; it authorizes no candidate code.

For `human_input`, record the exact request, response path, schema, provenance, quality and legality checks, confidentiality handling, accept or reject conditions, resume event, and evidence-only limit in B or its required W before selection. Supplied data cannot stand in for a technical verdict or V.

## 7. Select reproducibly

Apply exact R8 route, eligibility, priority, uncertainty, measurement-use, vacuity, promotion, confirmation, parallelism, and fallback clauses. If R8 is silent or ambiguous about a required rule and does not delegate it, record `PARENT_REVIEW_REQUIRED` and use the finalization section below.

Technically filter first, then apply adopted V records. Propose one Primary B and only demonstrably independent Parallel B records. Record the exact proposed Selection and Budget transition, separate budgets, mutable paths, stable shared resources, failure isolation, and one join point. Do not adopt a reservation or executable Selection before the applicable readiness review and user authorization.

Include the proposed Selection and F2-F4 patch in the reviewed target. Record the route set as `complete for this decision` or `incomplete`, cite the peer-source generation basis, shared assumptions, eligible routes, exclusions, deferrals, prerequisite consequences, and reopening evidence, and explain how the selected work reaches the first discriminating check. An incomplete route set may select only its bounded route-landscape, assumption, or prerequisite work; it cannot select dependent candidate work. Explain why the chosen campaign baseline is useful for later optimization and how every material alternative is dispositioned. Before the first B, record `Outcome reflections applied: None before the first B` in that proposal.

## 8. Pin the Entry snapshot

Write a plain-language Brief in `FRONTIER.md` that a fresh reader can use without following identifiers. It must name the reference baseline, replaceable campaign baseline, exact allowed work, remaining budget, selected B and W, first checkpoint, first performance check, preparation limit, protected reserve, comparison and promotion rules, stop and halt rules, and claim limits.

Pin F1-F4, F7, and F8. F5 and F6 may remain provisional or not relevant when the parents provide no usable bound; missing bounds never widen F7 or F8. Confirm new-generation B spend is zero, inherited spend is exact, and every charged Entry cost is already accounted.

## 9. Review before authorization

Load [Entry review](entry-review.md). Build the typed current-state projection and run draft Entry schema validation before allocating immutable review artifacts. Repair every deterministic finding in transient files under the unchanged-B rule. After a finding-free draft, publish the complete target, create one filtered project snapshot, run frozen schema validation, and invoke `review-frontier` in a fresh context. The snapshot and completion check contain project evidence only; omit workflow, Skill, validator, Slice 7, bundle, and workflow-test inputs. Supply no expected verdict or repair suggestion.

Preserve every review. A semantic `ENTRY_REPAIR_REQUIRED` finding receives a new snapshot; a deterministic identity, schema, snapshot, or state-projection defect indicates validator coverage failure and is repaired before the replacement review. Obtain named evidence after `EVIDENCE_REQUIRED`, return parent conflicts upstream, and expose true blockers. For a target needing user authorization, adopt only finding-free `AUTHORIZATION_READY`, then ask the exact reviewed question. On an exact affirmative answer, write V, build the Coordinator Entry-adoption artifact, and require finding-free draft and frozen adoption validation before applying only the reviewed Selection and Budget transition and recording `entry_result: ENTRY_READY`. A decline grants no spend authority; a condition or changed target requires fresh review before another question. When no user authorization applies, the reviewer may return `ENTRY_READY` directly under `spend-readiness`.

Append `FIRST_BATCH_PLANNED` only after direct `ENTRY_READY` or exact post-answer adoption. Include campaign generation, readiness snapshot and review, V and adoption when applicable, parents, selected B records, inherited and Entry-cost accounting, and zero-B-spend consequence. Do not execute the B.

## Record one outcome, then finalize the return

Record exactly one stage outcome:

- `FIRST_BATCH_PLANNED`: complete Entry, unchanged readiness authority and `ENTRY_READY` adoption, zero new-generation B spend, and reconciled inherited and Entry cost;
- `CLOSEOUT_REQUIRED`: a valid pre-spend stop or halt applies;
- `PARENT_REVIEW_REQUIRED`: parent authority or meaning is missing, stale, or ambiguous;
- `BLOCKED`: required authority, private facts, tools, data, or access are unavailable.

Return the recorded stage outcome to the Coordinator.

Entry is complete only when artifacts reconstruct campaign generation, planning-only opening authority and Coordinator-derived objective when applicable, structured recovery lineage, peer-source route generation, decision completeness, prerequisite dispositions, baseline choice, replacement boundary, inherited budget, proposed target, readiness review, separate user tradeoff and exact execution authorization when applicable, selected work, earliest discriminating check, code gates, and zero-B-spend boundary.
