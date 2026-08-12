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
- [Return one outcome](#return-one-outcome)

Use this stage when no campaign exists, Entry is incomplete, or `frontier-core.md` selected post-closeout recovery mode. Its only successful outcome is one reviewed, reproducible first-batch plan with zero new-generation B spend and fully accounted inherited and Entry cost.

## Load only what Entry reaches

Load [Campaign state](campaign-state.md) and [Planning records](planning-records.md). Load [Evidence records](evidence-records.md) in post-closeout recovery mode. Load [Worker interfaces](worker-interfaces.md) before delegating research, a user decision, Entry review, or any other worker action. Load [Batch interface](batch-interface.md) before freezing any selected first-B packet. If any eligible first batch may change executable code, load [Entry code planning](entry-code-planning.md). When recovery proposes an existing candidate for measurement, load [Candidate lifecycle](candidate-lifecycle.md), [Review snapshots](review-snapshots.md), and [Implementation review](implementation-review.md). Load [Entry review](entry-review.md) only after the proposed Entry artifacts are frozen.

## 1. Validate the handoff

Bind the exact Problem epoch, Representation revision, generation times, positive reviews, reference baseline, measurement identity, exact `Permitted` text, R1-R8, budget authority, and claim limits. Copy no broader meaning into Frontier records.

Return `PARENT_REVIEW_REQUIRED` without creating campaign state when a required parent, review, measurement, budget rule, or R8 instruction is missing, stale, conflicting, or ambiguous. Do not repair parent documents here.

### Rebind a compatible pre-spend campaign

Use this path only when `frontier-core.md` selected pre-spend parent-rebind mode.

1. Verify every rebind condition against current parents, accounting, repository paths, and the upstream disposition. Treat missing candidate or result paths as evidence only after checking the assigned locations.
2. Append X dispositions for the old Selection, selected B, W, Entry packet, review, worker packets, development authorization, and `FIRST_BATCH_PLANNED` authority. Preserve Q, T, V, E, or other adopted evidence only when the upstream disposition names the record reusable and every cited identity still resolves. Unclassified evidence is not retained.
3. Never edit an old B, W, packet, review, or worker result. Create new identifiers for replacement B and W records. `FRONTIER.md` remains the current view and may be rewritten only after the ledger records the disposition and replacement lineage.
4. Append `PARENT_REBIND_STARTED` to `log.md` with old and new parent identities, zero-spend evidence, the upstream disposition, retained and replaced identifiers, and the exact consequence that no B is executable.
5. Continue the normal Entry procedure under the new parents. Reconcile Entry cost, create replacement records from current templates, freeze a new immutable snapshot bundle, and obtain a new Entry review.

The rebind completes only when the Coordinator adopts an unchanged finding-free `ENTRY_READY` and appends `FIRST_BATCH_PLANNED` plus `PARENT_REBOUND` with the new snapshot, review, replacement lineage, and zero-B-spend evidence. Otherwise the old campaign remains preserved and unauthorized.

### Open a post-closeout recovery campaign

Use this path only when `frontier-core.md` selected post-closeout recovery mode.

1. Verify unchanged positive parents, a complete prior `CLOSEOUT_COMPLETE`, final accounting, no unresolved C branch, no active worker, the highest campaign generation, and the exact current user request. Treat legacy records without a generation as generation 1.
2. When the request reuses a materialized candidate, build a temporary recovery preflight and run `scripts/validate_candidate_recovery.py` in draft mode before creating any new-generation artifact. Recompute the manifest, every candidate member, and package identity from canonical bytes. A mismatch returns `BLOCKED` with no V, X, review, generation update, or spend. On PASS, insert only the computed identity, freeze the preflight at a new path, and reproduce finding-free frozen validation.
3. Increment `campaign_generation`. Append a new authorization V that quotes the request and binds the named recovery objective, frozen recovery preflight, and exact reusable identities. Append X dispositions that map every reused evidence object into the new generation. Closed authority remains closed; unclassified objects are not reusable.
4. Carry the parent budget ceiling and all prior, Entry, B, external-action, and unknown spend forward. Releasing an old reserve does not restore authority by itself. New reservations come only from the new Budget and Selection.
5. Use new V, X, W, B, review, packet, acknowledgment, execution-start, result, and log identifiers. Never edit or reuse a closed identifier. Preserve old snapshots and results byte for byte.
6. Reuse current Q, T, V, design, engineering, or reference evidence only when its cited identity still resolves and X states its new-generation role and limits. Refresh research or user tradeoffs only when evidence or values changed.
7. For a byte-identical materialized candidate, bind the frozen finding-free recovery preflight before planning measurement. Reuse creates no new proposal attempt. Freeze a new `review_mode: recovery-reuse` implementation snapshot and adopt only unchanged `IMPLEMENTATION_READY`; the old implementation verdict remains historical and cannot become positive retroactively.
8. If recovery review is positive, plan the first B as a separate experiment with `changes_executable_candidate: false`, a complete evaluation target, and the normal two-phase dispatch. If it is nonpositive, preserve it and plan only the exact repair, evidence, or stop consequence it permits. Any candidate byte or behavior change needs a new code-bearing B, current development authorization, and one new proposal attempt.
9. Append `RECOVERY_CAMPAIGN_STARTED` to `log.md`, update `FRONTIER.md` to the new generation and `campaign_status: planned`, and continue normal Entry planning. The first new-generation B still requires a fresh immutable Entry snapshot and finding-free `ENTRY_READY`.

Recovery does not make the preserved candidate an incumbent, campaign result, or performance claim. It becomes a campaign-baseline candidate only through the new Selection and enters F4 only after valid measurement and retention.

## 2. Initialize the campaign

For generation 1, create only the canonical paths from `frontier-core.md`, append `FRONTIER_STARTED`, and initialize F1-F8, Budget, and E001. For post-closeout recovery, use the recovery procedure above and append within the existing canonical files. Record Entry planning and research cost separately when the governing accounting rule charges it.

Keep E001 as the current-epoch reference baseline. F1 must reproduce the exact reviewed scope. F2 must distinguish total budget, prior spend, reservations, actual spend, required follow-up reserve, and remaining balance. F7 and F8 must preserve every inherited stop, halt, reachability, comparison, and claim limit.

## 3. Build a decision-grade route landscape

Create one route-landscape Q target before research. The packet must name the decision, reviewed scope, comparison dimensions, required evidence channels, repository evidence, search stop, evidence path, and result path.

Use `research-frontier`. For a general optimization campaign, cover applicable current public implementations, domain practice, benchmarks, and academic work. Mark an inapplicable channel with a reason and preserve useful negative searches. Stop when the plausible route families and baseline approaches can be compared and more research is unlikely to change eligibility, selection, allocation, stopping, or a user-owned tradeoff.

Adopt the checked result as Q. Research describes possibilities and limits; it does not select work. Reconcile its charged Entry cost before planning B reservations.

## 4. Create eligible plans

Create a T for every materially different technically eligible route or campaign-baseline approach. Each T must bind the parents and state:

- mechanism and why it may improve the objective;
- repository fit and required change surface;
- measurement and comparison plan;
- expected observation and falsifier;
- preparation needed before the first discriminating check;
- risks, uncertainty, dependencies, reversibility, and stop events;
- replacement boundary and stable evidence interface;
- source support and rejected alternatives.

Reject routes outside exact `Permitted` scope before user preference. Do not invent expected improvement, probability, route scores, calendar estimates, or tie-breaks.

When only one approach is technically eligible, Q must name every other plausible approach considered, the evidence that makes it ineligible, and the reconsideration event when one exists. Create no fake alternative T and request no campaign-baseline tradeoff V.

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

Its packet must also separate worker write surfaces, worker-forbidden paths, and execution-frozen inputs; assign exclusive Coordinator-owned packet-preflight, execution-baseline, and execution-start paths plus a worker-owned result-validation path; and encode the exact post-acknowledgment lifecycle transition when the campaign is planned. For W-backed work, bind machine-readable design traceability and never freeze the whole W. Run draft and frozen structural preflight before Entry snapshot creation. The Entry plan is invalid if any W evidence destination is unassigned, if following Campaign Cycle would trigger drift, if the worker could begin before every post-transition byte has a recoverable snapshot, or if a final result could be written before profile-aware validation.

Preparation must end at the earliest check that can discriminate the chosen mechanism. A baseline-establishment slice may be simple, but it cannot become open-ended infrastructure work.

If the B may change executable candidate code, complete `entry-code-planning.md` before selection. A design, research, or isolated prototype B must explicitly state `changes_executable_candidate: false`; it authorizes no candidate code.

For `human_input`, record the exact request, response path, schema, provenance, quality and legality checks, confidentiality handling, accept or reject conditions, resume event, and evidence-only limit in B or its required W before selection. Supplied data cannot stand in for a technical verdict or V.

## 7. Select reproducibly

Apply exact R8 route, eligibility, priority, uncertainty, promotion, confirmation, parallelism, and fallback clauses. If R8 is silent or ambiguous about a required rule and does not delegate it, return `PARENT_REVIEW_REQUIRED`.

Technically filter first, then apply adopted V records. Propose one Primary B and only demonstrably independent Parallel B records. Record the exact proposed Selection and Budget transition, separate budgets, mutable paths, stable shared resources, failure isolation, and one join point. Do not adopt a reservation or executable Selection before the applicable readiness review and user authorization.

Include the proposed Selection and F2-F4 patch in the reviewed target. Explain why the chosen campaign baseline is useful for later optimization, why each alternative is rejected or deferred, what would reconsider it, and how the selected work reaches the first discriminating check. Before the first B, record `Outcome reflections applied: None before the first B` in that proposal.

## 8. Pin the Entry snapshot

Write a plain-language Brief in `FRONTIER.md` that a fresh reader can use without following identifiers. It must name the reference baseline, replaceable campaign baseline, exact allowed work, remaining budget, selected B and W, first checkpoint, first performance check, preparation limit, protected reserve, comparison and promotion rules, stop and halt rules, and claim limits.

Pin F1-F4, F7, and F8. F5 and F6 may remain provisional or not relevant when the parents provide no usable bound; missing bounds never widen F7 or F8. Confirm new-generation B spend is zero, inherited spend is exact, and every charged Entry cost is already accounted.

## 9. Review before authorization

Load [Entry review](entry-review.md). Run draft Entry schema validation before creating the snapshot. Freeze the complete target, run frozen schema validation, and invoke `review-frontier` in a fresh context. Supply no expected verdict or repair suggestion.

Preserve every review. Repair `ENTRY_REPAIR_REQUIRED` findings in a new snapshot, obtain named evidence after `EVIDENCE_REQUIRED`, return parent conflicts upstream, and expose true blockers. For a target needing user authorization, adopt only finding-free `AUTHORIZATION_READY`, then ask the exact reviewed question. On an exact affirmative answer, write V, build the Coordinator Entry-adoption artifact, and require finding-free draft and frozen adoption validation before applying only the reviewed Selection and Budget transition and recording `entry_result: ENTRY_READY`. A decline grants no spend authority; a condition or changed target requires fresh review before another question. When no user authorization applies, the reviewer may return `ENTRY_READY` directly under `spend-readiness`.

Append `FIRST_BATCH_PLANNED` only after direct `ENTRY_READY` or exact post-answer adoption. Include campaign generation, readiness snapshot and review, V and adoption when applicable, parents, selected B records, inherited and Entry-cost accounting, and zero-B-spend consequence. Do not execute the B.

## Return one outcome

Return exactly one:

- `FIRST_BATCH_PLANNED`: complete Entry, unchanged readiness authority and `ENTRY_READY` adoption, zero new-generation B spend, and reconciled inherited and Entry cost;
- `CLOSEOUT_REQUIRED`: a valid pre-spend stop or halt applies;
- `PARENT_REVIEW_REQUIRED`: parent authority or meaning is missing, stale, or ambiguous;
- `BLOCKED`: required authority, private facts, tools, data, or access are unavailable.

Entry is complete only when artifacts reconstruct campaign generation, structured recovery lineage when applicable, research coverage, baseline choice, replacement boundary, inherited budget, proposed target, readiness review, exact user answer and adoption when applicable, selected work, earliest discriminating check, code gates, and zero-B-spend boundary.
