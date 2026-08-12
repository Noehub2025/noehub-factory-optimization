# Frontier Campaign Cycle: Result Adoption, Evidence Learning, and Next-Batch Selection

Load after `frontier-core.md` selects a planned or running campaign with one selected B or a proven-safe parallel set and current spend authority. This stage executes and adopts:

- one simple non-code B with no W; or
- one `direct` code B with no W, ending at the materialized-candidate checkpoint;
- one complex non-code B under a current W;
- one `module` or `system` design checkpoint or code slice under a current W; or
- one human-input B with its request and validation contract in B or W;
- one separate Slot H evaluation B for an unchanged `IMPLEMENTATION_READY` candidate; and
- the learning loop and next Selection after every terminal B.

External action, code-bearing `mixed` work, campaign closeout, and completion of the claim-review branch remain unavailable. Parallel B records are executable only when their shared W revision is identical, mutable paths do not overlap, one integration owner and join check are named, and neither result configures or permits the other. Return `BLOCKED` with `stage implementation pending: <exact later profile>` rather than weakening a gate or creating an ad hoc path.

## Contents

- [Load only the current action](#load-only-the-current-action)
- [Recover the selected B](#recover-the-selected-b)
- [Authorization-readiness gate](#authorization-readiness-gate)
- [Common pre-dispatch gate](#common-pre-dispatch-gate)
- [Dispatch acceptance scenarios](#dispatch-acceptance-scenarios)
- [Simple non-code B](#simple-non-code-b)
- [W-backed work](#w-backed-work)
- [Design gate for module and system](#design-gate-for-module-and-system)
- [Execute a ready module or system design](#execute-a-ready-module-or-system-design)
- [Shared interface and contract changes](#shared-interface-and-contract-changes)
- [Human input](#human-input)
- [Direct code B](#direct-code-b)
- [Freeze and review a materialized candidate](#freeze-and-review-a-materialized-candidate)
- [Reconcile result and spend](#reconcile-result-and-spend)
- [Run measurement as a separate B](#run-measurement-as-a-separate-b)
- [Adopt valid measurement as E](#adopt-valid-measurement-as-e)
- [Complete mandatory Outcome Reflection](#complete-mandatory-outcome-reflection)
- [Join parallel work](#join-parallel-work)
- [Resolve the next Selection](#resolve-the-next-selection)
- [Open a mid-campaign claim branch](#open-a-mid-campaign-claim-branch)
- [Slice 5 acceptance scenarios](#slice-5-acceptance-scenarios)

## Load only the current action

- Load [Campaign state](campaign-state.md) and [Planning records](planning-records.md) to resolve the selected B, baseline, Budget, and authority.
- Load [Batch interface](batch-interface.md) to create, acknowledge, dispatch, or reconcile the exact packet.
- Load [Candidate lifecycle](candidate-lifecycle.md), [Review snapshots](review-snapshots.md), and [Implementation review](implementation-review.md) only for code-bearing work or an implementation-review reuse check.
- Load [Work plan](work-plan.md) when B cites W. Load only W frontmatter, Current state, the selected Delivery row, its applicable Validation and Definition-of-done terms, Recovery, and Design-map rows whose `Read when` condition matches the action.
- Load [Technical design](technical-design.md) only while choosing, drafting, repairing, or changing a `module` or `system` design. Load [Design review](design-review.md) only when freezing, reviewing, or adopting that design.
- Load [Learning loop](learning-loop.md) after a terminal B, an uncovered E, or a pending strategic replan. Load [Evidence records](evidence-records.md) only for a controlling D or X action.
- Load [Claim records](claim-records.md) only when exact external wording or a claim-review request appears. Do not load [Claim review](claim-review.md) in this slice.
- Load [Worker interfaces](worker-interfaces.md) before invoking `run-frontier-batch` or `review-frontier`.

Do not reload `technical-design.md` to execute a `ready` design. Follow W's matching `Read when` pointers and load only the exact concern contracts required by the selected B. Do not load learning-loop, evidence, or claim references before their triggers occur.

## Recover the selected B

Read current parent reviews, `FRONTIER.md`, selected B, latest Budget and Selection, first-spend Entry review or later spend authority, assigned packet preflight, packet, acknowledgment, result, B terminal outcome, accounting evidence, related E, Outcome Reflection, join disposition, replan review, and stable artifacts that already exist. Use recorded identities, never conversation history.

For W-backed work, resolve the exact W path, current `plan_revision`, design-contract identity, Design-map concern identities, applicable `Read when` rows, selected Delivery row, design review, development authorization, worker progress and discoveries, and recovery state. For code, also resolve the source-base identity, candidate manifest, source-result bytes, implementation snapshot packet, review artifact, and adoption log when they exist. Recovery is valid without the original branch or worktree only when the packet preflight, packet, acknowledgment, execution-baseline snapshot and manifest, execution-start record, result validation, result packet, W revision, required concerns, manifest, source base and result, candidate bytes, configuration, dependencies, engineering evidence, and review inputs remain recoverable by stable identity. A hash without recoverable bytes is insufficient.

For human input, recover the request, schema, provenance requirements, quality checks, confidentiality limits, response identity, validation state, and resume event. Do not infer a missing answer or validation from conversation history.

Resume at the first missing durable step for the current B: worker result, Coordinator validation, B terminal outcome, applicable candidate review, E adoption when this B is a separate valid evaluation, Outcome Reflection, classification work, applicable research or V, replan review, join, and next Selection. A later Selection may then authorize a separate evaluation B. Never repeat spend whose outcome is unknown merely because the live workspace is missing.

## Authorization-readiness gate

Before asking the user to authorize work tied to a concrete B packet:

1. Complete every B packet field except `packet_id`, including W traceability, preflight path, worker and Coordinator paths, frozen inputs, lifecycle outputs, and prohibitions.
2. Run `validate_batch_packet.py` in draft phase. Any finding blocks packet freezing. Insert only its computed identity, freeze the packet, and require byte-identical frozen structural preflight.
3. Build the exact authorization target and proposed Budget, Selection, and lifecycle consequence. Do not reserve, adopt Selection, or ask the user yet.
4. Build the Entry assignment with `authorization_state: pending`. Run `validate_entry_packet.py` in draft phase before snapshot creation. For generation greater than 1, require structured recovery lineage. Any finding blocks the snapshot.
5. Freeze the complete authorization-readiness snapshot, insert its identity, compute the Entry packet identity, and require finding-free frozen Entry schema validation at a separate path.
6. Invoke fresh `review-frontier` and adopt only finding-free unchanged `AUTHORIZATION_READY`. This verdict permits only the exact user question.
7. Invoke `grill-frontier` with that review identity and target. On exact authorization, write V and build the Coordinator-owned adoption artifact. Run `validate_authorization_adoption.py` in draft and frozen phases.
8. Only a finding-free frozen adoption validation may produce `ENTRY_READY` and apply the exact reviewed Budget and Selection transition. Decline grants no authority. Any condition or changed object returns `REVIEW_REQUIRED`; create a new packet and readiness review before asking about the replacement.

For direct code, V binds the reviewed packet, preflight, source base, scope, spend, stop boundary, and `AUTHORIZATION_READY`. For `module` or `system`, V also binds the exact design contract and affected scope. It never binds the whole W file, and the answer is never written into W. A repaired packet, traceability file, Entry assignment, or authorization target is a new object; preserve and disposition the old one rather than transferring review or authorization.

## Common pre-dispatch gate

Before any work or spend:

1. Verify the parent epoch, representation revision, exact `Permitted` scope, F8 claim ceilings, selected B, baseline, Budget, reservation, Entry or later Selection authority, and every mandatory stop.
2. Verify that every earlier terminal selected B and every later uncovered E has an Outcome Reflection; every completed parallel set required by this B has a joined X; every required V is adopted; and every applicable Entry, replan, design, and implementation review remains unchanged and positive.
3. For spend requiring user authorization, require unchanged `AUTHORIZATION_READY`, exact user V, Coordinator adoption artifact with `entry_result: ENTRY_READY`, and finding-free frozen adoption validation. For direct spend-readiness, require finding-free `ENTRY_READY`. A stale positive review or adoption grants no permission.
4. Require the immutable packet and fresh finding-free structural preflight produced before authorization-readiness review. Recompute frozen preflight, W traceability, and Entry adoption identities; do not create or repair them here.
5. Invoke `run-frontier-batch` for the acknowledgment phase. Require it to repeat frozen preflight, verify `packet_id`, validate every gate and path class, write the acknowledgment, and return without work or spend.
6. After an accepted acknowledgment, set `campaign_status: running` when the packet requires the exact `planned -> running` transition. Make no other action-controlling change.
7. Verify the exact lifecycle diff, then use the bound baseline tool to copy every execution-frozen and other action-controlling input into the assigned content-addressed execution-baseline snapshot. Write the immutable Coordinator-owned execution-start record only after every copied byte and identity validates.
8. Invoke `run-frontier-batch` for the execution phase. Work and spend may begin only after it verifies the execution-start identity, snapshot manifest, snapshot bytes, and matching live post-transition baseline.

A malformed, stale, underfunded, unauthorized, contradictory, or path-conflicting packet returns `BLOCKED`. Preserve the packet, acknowledgment, and execution-start record when one exists; do not silently repair them worker-side. An accepted acknowledgment without `worker_may_start: yes` is a durable no-spend wait, not permission to execute.

## Dispatch acceptance scenarios

| Scenario | Required durable outcome |
|---|---|
| Draft repeats the B006 acknowledgment/execution-start ownership conflict | Structural preflight fails before `packet_id`, readiness review, user V, Selection, reservation, acknowledgment, work, or spend. |
| W evidence destinations are absent from B worker outputs | Structural preflight fails before authorization-readiness review. |
| Entry generation is greater than 1 but recovery lineage is absent | Entry draft schema fails before snapshot creation or user V. |
| Packet passes structure but its W, Budget, Selection, or target is semantically inconsistent | Fresh authorization-readiness review is nonpositive before the user question. |
| User adds a condition that changes scope, path, spend, or stop boundary | Adoption returns `REVIEW_REQUIRED`; no Selection, reservation, acknowledgment, work, or spend follows. |
| Draft passes, then any packet byte changes | Frozen structural preflight differs; discard the draft identity and require a new readiness review. |
| First B changes campaign status after acknowledgment | Acknowledgment returns before spend; only the exact reviewed `planned -> running` patch occurs; the Coordinator copies and validates the complete post-transition baseline, execution-start binds its snapshot, then the worker starts. |
| Worker-forbidden campaign record changes without being execution-frozen | Block only when the worker made the edit or another authority gate changed; do not treat actor-specific write protection as global drift. |
| Execution-frozen input changes after execution start | Immediate forced halt with the changed identity and truthful spend; no silent rebaseline. |
| A packet freezes a directory containing `FRONTIER.md`, its execution-start path, or a worker output | Reject before acknowledgment as path-conflicting. |
| A post-transition baseline identity has no recoverable snapshot byte | Do not write execution-start or invoke the execution phase; return `BLOCKED` with zero work and spend. |
| A normal terminal adoption later changes `FRONTIER.md`, ledger, or log | Preserve the live update and reconstruct start-time authority from the immutable execution-baseline snapshot. |
| A materialization result draft contains candidate text in `results` | Result validation fails before the immutable result path or accepted terminal outcome exists. |

## Simple non-code B

This profile requires all of the following:

- `changes_executable_candidate: false`;
- `work_plan: null` and `work_plan_revision: null`;
- no code, configuration-schema, dependency, executable-asset, public-interface, or runtime-behavior change;
- one bounded executor, checkpoint, output contract, validation set, spend limit, and recovery point;
- no unavailable human, service, or external input and no shared-interface or multi-checkpoint design dependency.

Do not create W for this profile. If the work reveals a W trigger, executable candidate change, human-input wait, shared contract, or multi-checkpoint dependency, stop and report the new prerequisite or scope deviation.

The result packet may truthfully return `completed`, `interrupted`, `failed`, `blocked`, or `waiting_for_input`. It may report a known amount or `actual_spend: unknown`. Reconcile all outcomes; failure and interruption do not erase artifacts or spend.

Worker artifacts and observations are proposals. They do not automatically create E, change F1-F8, select a route, adopt a bound, or prove optimization performance. The Coordinator must validate the result, append the terminal outcome when applicable, and complete the learning loop before any later spend.

## W-backed work

Use one W for complex non-code recovery, shared module design, system design, or human input that spans checkpoints. Before dispatch:

1. Require B and its immutable packet to cite the exact current W path, `plan_revision`, design-contract identity, selected Delivery row, required design inputs, and machine-readable traceability identity.
2. Reject a stale W revision, superseded design-contract identity, missing concern, mismatched `Read when` condition, incomplete evidence-destination mapping, or B-local redefinition of a shared contract.
3. For a complex non-code W, require `design_profile: not-applicable`, one reasoned not-applicable Design-map row, concrete checkpoints, input contracts when applicable, validation, definition of done, and recovery. Create no technical-design concern files.
4. For `module` or `system`, require W plus every triggered concern and immutable concern identity. A concern absent from the current Design map is outside the contract.
5. For a safe parallel set, require every member to bind the same current W revision and design identity, exclusive mutable paths, one integration owner, one W-owned join check, and failure isolation. Otherwise execute sequentially.

Never use the whole W file as an execution-frozen identity. Freeze its contract through indexed section, concern, source, fixture, and traceability identities. W progress may change only in the assigned worker section, while current authorization remains external to W.

The worker may append only assigned Milestones and progress or Decisions and discoveries content. It cannot edit Purpose, Scope, Design brief, Design map, Human input contracts, Delivery map, Validation, Definition of done, or any concern contract.

## Design gate for module and system

A design B has `changes_executable_candidate: false`. It answers only the assigned design question and returns evidence or proposed contract wording; it does not edit W or concerns and grants no code authority.

When the design evidence is sufficient, the Coordinator:

1. updates the owning W contract sections and applicable concern contracts;
2. increments `plan_revision` for every contract-bearing change and computes a new immutable design-contract identity;
3. marks the former `DESIGN_READY` and every development authorization bound to the old identity invalid for affected B records;
4. replans each affected B against the new revision and exact required concern identities;
5. freezes a new immutable design snapshot and invokes `review-frontier` in a fresh context with `review_kind: design`;
6. adopts only a finding-free `DESIGN_READY` whose design identity and inputs remain unchanged; and
7. after that adoption, completes structural packet and Entry schema validation, obtains `AUTHORIZATION_READY`, and only then invokes `grill-frontier` for the exact reviewed target.

Coordinator adoption of a design or `DESIGN_READY` is technical readiness only. It is not user authorization to develop. Declined, conditional, absent, stale, or differently scoped authorization keeps the affected code B blocked.

## Execute a ready module or system design

Before code execution, require all of the following:

- W `design_status: ready`, exact current `plan_revision`, and immutable design-contract identity;
- every required concern pointer and section identity from the selected Delivery row, with a matching `Read when` condition;
- an unchanged adopted fresh-context `DESIGN_READY` bound to that exact design identity;
- unchanged `AUTHORIZATION_READY`, a separate user development V, and Coordinator Entry adoption bound to the same design identity and exact affected code-bearing scope;
- repository, source-base, workspace, candidate-interface, path, manifest, engineering, recovery, and implementation-review gates from `candidate-lifecycle.md`.

For execution, read the W recovery surfaces and only those matching concern contracts. Do not reload all concerns or `technical-design.md`. If the packet cites a stale revision or old concern identity, return `BLOCKED` before acknowledgment, work, or spend.

The worker materializes only the selected vertical slice, writes the candidate manifest and result packet, and stops before performance evaluation, integration, or incumbent use. Apply the same materialization and implementation-review checkpoint used by direct code, with W, concern, `DESIGN_READY`, and development-authorization identities included in the candidate and review snapshots.

## Shared interface and contract changes

One shared W owns the interface, callers, invariants, compatibility or migration terms, interface tests, integration owner, and join check for every affected B. A B packet cannot redefine them.

When execution exposes a shared-interface or other contract-bearing change:

1. the worker records only the discovery, evidence, affected contract, and consequence in W discoveries and its result packet;
2. the Coordinator either rejects the proposal with evidence or updates the owning W and concern contracts under a new `plan_revision`;
3. the Coordinator invalidates old `DESIGN_READY`, development authorizations, and stale affected B packets;
4. a fresh reviewer reviews the new immutable design and must return `DESIGN_READY`; and
5. each replacement target receives structural and authorization-readiness review, then the user separately reauthorizes every affected development scope before code resumes.

A running B may continue across a W revision only when the Coordinator proves that its work, required design inputs, output, validation, completion condition, mutable paths, and join obligation are unchanged. Otherwise stop it at a recovery point and issue a new packet after the gates above.

## Human input

A human-input B or W must name the exact request, response path, schema, required provenance, quality and legality checks, confidentiality handling, accept or reject conditions, and resume event. The first attempt writes the request and returns `waiting_for_input` with a stable recovery point when the response is unavailable.

After a response arrives, preserve its bytes and provenance metadata, then run the assigned schema, source, and quality checks. Record exactly one state: `received-unvalidated`, `accepted-as-evidence`, or `rejected`. Missing or failed checks do not become accepted data, and a resumed attempt uses a new immutable packet and paths.

User-provided data is evidence only after workflow validation. It does not automatically become a technical conclusion, E, a legality or engineering verdict, or a user value choice. Technical interpretation remains subject to the owning checks and later Coordinator adoption. A preference, tradeoff, or authorization must be asked explicitly and recorded through V; never infer it from supplied data.

## Direct code B

This profile requires all of the following before dispatch:

- `work_kind: code`, `changes_executable_candidate: true`, `design_profile: direct`, and no W;
- reproducible evidence that the change fits `direct` rather than hiding a module or system design;
- repository-structure disposition, candidate interface, exclusive code paths, worker-forbidden paths, execution-frozen inputs, configuration and dependency rules, engineering checks, and recovery artifacts;
- one immutable packet with exact `packet_id`, fresh finding-free structural `preflight_id`, and `source_base_identity`;
- a finding-free unchanged `AUTHORIZATION_READY` for that exact packet, source, scope, spend, and stop boundary;
- an explicit user development V and Coordinator Entry adoption whose bound object names that review, `packet_id`, `preflight_id`, and `source_base_identity` together;
- a candidate-manifest path and an implementation-review gate that bars performance evaluation, mainline integration, and incumbent use.

Direct has no `DESIGN_READY` substitute and needs no design review. A V bound only to `B001`, a mutable ledger section, branch, worktree, general route, approximate source base, or structurally checked but unreviewed packet is invalid. Any packet payload, material scope, source base, spend, or stop-boundary change creates a new target and requires fresh authorization-readiness review before another user question.

The worker implements one bounded vertical slice through the candidate interface, runs only assigned engineering checks, resolves configuration and dependencies, records every changed path, writes the sole candidate manifest, computes the immutable candidate identity, and preserves a recoverable source result. A material behavior-bearing change creates a new candidate identity.

Then stop. Every materialized code result, whether `direct`, `module`, or `system`, must say:

- `materialization_state: materialized-stopped`;
- `implementation_review_state: pending`;
- `performance_evaluation_state: not-authorized`;
- `integration_state: not-authorized`;
- `results: []` for performance results; and
- a recovery point that identifies the packet preflight, packet, acknowledgment, content-addressed execution-baseline snapshot, execution-start record, result validation, applicable W and concern identities, design review and authorization, manifest, source base and result, candidate bytes, configuration, dependencies, engineering evidence, and next permitted action.

A build, unit test, smoke check, local launch, or Coordinator validation is engineering evidence only. It cannot replace `IMPLEMENTATION_READY`.

## Freeze and review a materialized candidate

After reproducing byte-identical frozen result validation and validating the materialization result and spend, the Coordinator:

1. verifies the packet preflight and authorization order, packet, acknowledgment, execution-baseline manifest and every copied byte, execution-start record, lifecycle transition, post-transition baseline, result-validation identity and byte-for-byte frozen reproduction, applicable W revision and concern identities, design review, development V, source base and result, changed paths, manifest, recomputed candidate identity, configuration, dependencies, engineering evidence, worker-forbidden paths, execution-frozen inputs, and recovery point;
2. creates a new immutable implementation snapshot under `frontier/reviews/` using `review-snapshots.md`;
3. includes recoverable copies or allowed stable content-addressed artifacts for every input needed to rebuild and audit the candidate without the live worktree;
4. creates a versioned implementation-review packet with `review_kind: implementation`; and
5. invokes `review-frontier` in a fresh context and preserves every verdict artifact.

Adopt only a finding-free, unchanged `IMPLEMENTATION_READY`. Log the review, packet, snapshot, candidate, B packet and preflight, applicable W/design inputs, source base and result, user authorization, unchanged-input check, and maximum consequence. That consequence is only permission for a separately authorized later measurement or integration B.

Before adopted unchanged `IMPLEMENTATION_READY`, reject every attempt to:

- run or interpret performance evaluation;
- integrate into mainline;
- use the candidate as campaign baseline, incumbent, comparison reference, or retained implementation;
- create E from the candidate; or
- promote or claim performance.

If review is nonpositive, preserve the candidate and snapshot as recoverable evidence. Repair requires a newly materialized candidate identity and a new implementation snapshot when behavior-bearing bytes or identity inputs change.

## Reconcile result and spend

Before result adoption, rerun `validate_batch_result.py` in frozen mode against the exact packet and require byte-identical output to the assigned result-validation artifact. Then validate packet identity, acknowledgment, execution-baseline snapshot, execution-start identity, lifecycle transition, post-transition baseline, parent bindings, scope, output contract, artifacts, recovery, actual spend, accounting evidence, failed checks, deviations, and prohibited actions. For W-backed work, validate the exact current plan revision, permitted worker append surfaces, concern identities, and any human-input contract. For code, validate the complete design, authorization, materialization, and implementation-review boundaries above.

Append one B terminal-outcome block for `completed`, `interrupted`, `failed`, or `blocked`; `waiting_for_input` is a durable pause, not a terminal B. Do not rewrite the planned B. The terminal outcome must cite the immutable result and its finding-free validation, state which output and checks the Coordinator accepted or rejected, preserve the recovery point and deviations, and reconcile the reservation and actual spend. A malformed draft cannot be frozen or accepted. If a legacy or unauthorized writer nevertheless created an invalid immutable result, preserve it as diagnostic evidence, halt adoption, and use a new explicitly authorized attempt rather than rewriting it.

After checking worker evidence, the Coordinator may update W lifecycle, progress, discoveries, recovery, and outcome. Only a Coordinator-authored new revision may change a contract-bearing W section or concern. Record known spend for every outcome. When `actual_spend: unknown`, mark remaining budget unresolved and block all new spend until accounting establishes a safe balance.

For a code-bearing B that materialized a recoverable candidate, perform the implementation review after the terminal outcome. Whether the review is positive or not, include its result in that B's Outcome Reflection. If no candidate materialized, record that the review is not applicable and reflect on the failure or interruption. A materialized candidate without adopted unchanged `IMPLEMENTATION_READY` cannot be selected for evaluation, integration, incumbent use, or promotion.

## Run measurement as a separate B

Implementation and performance evaluation are always separate B records and packets. An evaluation B must:

- use `work_kind: experiment` and `changes_executable_candidate: false`;
- cite one immutable candidate identity, its manifest, and adopted unchanged `IMPLEMENTATION_READY`;
- precompute one experiment identity from the candidate, Slot H evaluator, data, controls, protocol, environment, budget, and exclusive result paths;
- protect candidate bytes, evaluator semantics, comparison controls, and measurement inputs from mutation;
- state the Slot H measurement and comparison-validity checks before dispatch; and
- have its own reservation, acknowledgment, result packet, terminal outcome, and Outcome Reflection.

Do not combine implementation and evaluation in one B, infer evaluation authority from `IMPLEMENTATION_READY`, or interpret engineering checks as Slot H evidence. If the evaluation reveals a candidate, evaluator, protocol, or comparison change, stop the B and create a new applicable identity and gate rather than mutating the experiment.

## Adopt valid measurement as E

After an evaluation B terminates, validate its candidate and experiment identities, unchanged implementation review, Slot H output, legality, uncertainty, operating cost, data quality, comparable conditions, drift, confounding, execution checks, and result artifacts. Append E only when the measurement is valid under the parent Slot H and the comparison-validity conclusion supports the recorded result. Invalid, failed, interrupted, or ambiguous measurement remains in the B result and terminal outcome; it does not create E.

E records evaluated evidence, not automatic retention or promotion. Apply R8 and the latest Selection separately. Before promotion, compare E with every active applicable D and its assumptions and tolerance. An unresolved bound contradiction blocks promotion, incumbent use, claim strengthening, and dependent spend. Authorize only the smallest diagnostic needed to resolve the contradiction unless it changes parent legality or authority, in which case halt and return to the parent or closeout route. Append X only after evidence justifies the bound or result disposition.

## Complete mandatory Outcome Reflection

Use `learning-loop.md` after every terminal B and after every E not already covered by that B's reflection. A single reflection may cover one terminal B and the E produced from its evaluation result. It cannot cover another terminal B. Before later spend, prove that:

1. every terminal B has exactly one controlling Outcome Reflection;
2. every E is named by that reflection or by a later E-only reflection;
3. the reflection cites the exact B terminal outcome, applicable implementation review, E, D, X, spend, and recovery identities;
4. implementation, measurement, and comparison validity are assessed in that order; and
5. the reflection resolves to one durable next action, deferral event, stop, halt, or blocker.

Classify the reflection from recorded evidence:

- **Routine:** the valid result matches the expected range, changes no strategic contract, and R8 uniquely determines the next action. Record why additional research cannot change that action; do not research by default.
- **Diagnostic:** the result is surprising, failed, ambiguous, or may reflect implementation or measurement error. Choose the cheapest distinguishing check first. Use a diagnostic B when the check performs work, changes artifacts, or spends campaign budget; its terminal result receives its own reflection.
- **Strategic:** the result may change the campaign baseline, route family, major allocation, budget policy, stop rule, design profile, irreversible behavior, or claim limit. Run only decision-changing focused research after cheaper diagnosis is insufficient, obtain every user-owned tradeoff through V, freeze the proposed replan, and adopt fresh unchanged `REPLAN_READY` before dependent Selection or spend.

No later B may be acknowledged while a required reflection, V, focused evidence result, join, or applicable Entry, replan, design, or implementation review is missing, nonpositive, or stale.

## Join parallel work

Do not select work that depends on a parallel set until every member has reached a terminal outcome, reconciled spend, completed every applicable candidate review and E adoption, and received its own Outcome Reflection. Then run the W-owned or Selection-owned join check against the fixed member outputs and append one X with `Disposition: joined`, the member and result identities, join evidence, failures or exclusions, and the exact consequence.

A waiting member, unknown spend, missing reflection, stale shared W revision, failed isolation rule, or absent join evidence blocks dependent Selection. Independent work may continue only when the existing Selection already proves that it does not use, configure, permit, or consume any unresolved member.

## Resolve the next Selection

Build the next action only from persisted parent bindings, F1-F8, R8, latest Budget, terminal outcomes, implementation reviews, E, D, X, Outcome Reflections, Q, V, W, and review artifacts. Resolve the same state to the same outcome:

1. apply hard eligibility, stop, halt, accounting, contradiction, reflection, join, and review gates;
2. apply the exact R8 clause and every adopted V condition;
3. if R8 uniquely determines the next action, select it without extra research;
4. if a cheapest diagnostic can distinguish live explanations, select that diagnostic before broader work;
5. if a technical unknown can change the decision and local evidence is insufficient, assign one focused research question;
6. if technically eligible options differ on a user-owned tradeoff, obtain V before choosing;
7. if the change is strategic, require adopted unchanged `REPLAN_READY` over the proposed F2-F4, Budget, Selection, and B state; and
8. append the authoritative Selection and its complete B records only after all applicable gates pass.

The Selection must cite every controlling reflection, the joined X when applicable, the exact evidence-state identity, the exact R8 branch, answered or deferred unknowns, and every review or V that grants authority. When no branch resolves, write the exact blocker instead of choosing arbitrarily. Later spend uses only this latest Selection and its unchanged identities.

## Open a mid-campaign claim branch

When adopted evidence leads to a request for exact external wording, create C in `frontier/claims.md` with the wording, intended use, scope, evidence, uncertainty, and current immutable lineage. Record `CLAIM_REVIEW_REQUIRED` in `log.md` with the C identity and reason. Do not invoke claim review, write A, adopt wording, publish, or continue the claim branch in this slice. The recorded-state router hands that branch to Slice 6.

Creating C grants no claim permission. If no exact wording and intended external use exist, do not create C merely because the result is interesting.

## Slice 5 acceptance scenarios

| Scenario | Required durable outcome |
|---|---|
| Expected valid result and a unique R8 next step | Routine reflection, no extra research, and Selection cites the exact R8 branch. |
| Surprising result that may be an implementation or measurement problem | Diagnostic reflection and the cheapest distinguishing local check before research or promotion. |
| Result changes campaign baseline, route, or major allocation | Targeted evidence, applicable V, immutable replan snapshot, fresh `REPLAN_READY`, then authoritative Selection. |
| Code implementation followed by performance evaluation | Separate implementation B and Slot H evaluation B; evaluation is blocked before unchanged `IMPLEMENTATION_READY`. |
| Parallel selected B records | Terminal reconciliation and reflection for every member, then one joined X before dependent Selection. |
| E contradicts an active applicable bound | No promotion, incumbent use, claim strengthening, or dependent spend until the contradiction is resolved and dispositioned. |
| Mid-campaign external wording request | C plus `CLAIM_REVIEW_REQUIRED`; no claim-review completion or A in this slice. |

This slice is complete when a fresh Coordinator can recover the packet, acknowledgment, content-addressed execution-baseline snapshot, execution-start record and post-transition baseline, finding-free result validation, exact W revision when used, terminal result or human-input wait, artifacts, spend, applicable candidate review, separate evaluation and E lineage, every required Outcome Reflection, classification work, replan review, parallel join, and latest Selection. For code, recovery must also reconstruct the reviewed design and authorization lineage plus immutable candidate, and show either adopted unchanged `IMPLEMENTATION_READY` or a hard prohibition on performance evaluation, integration, and incumbent use. The same persisted state must yield the same next action or blocker. No later spend is permitted without every applicable reflection, V, join, and review.
