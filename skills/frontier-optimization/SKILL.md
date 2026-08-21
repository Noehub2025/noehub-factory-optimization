---
name: frontier-optimization
description: Coordinate Optimization Frontier campaigns from a positive Representation handoff through Entry, repeated batches, closeout, post-closeout recovery, and durable packaging. Use only when the user explicitly asks to start, resume, recover, open a new campaign after closeout, close, package a completed campaign, or review claims for one canonical Frontier task.
---

# Frontier Optimization

Act as the only Frontier Coordinator. Choose the next stage from recorded state, assign bounded work, validate results, and adopt accepted meaning into campaign records. No other Skill may perform Coordinator writes.

## Start with the minimum context

1. Read [Frontier core](references/frontier-core.md) and the shared [Provenance and identity](references/provenance-and-identity.md) contract.
2. Select one canonical task path and validate the exact positive Representation handoff through the shared [Framing-to-Frontier handoff](../frame-optimization/references/frontier-handoff.md).
3. Apply the recorded-state router. Do not infer state from conversation history.
4. Load exactly one stage file:
   - no campaign or incomplete Entry: [Entry and planning](references/entry-and-planning.md);
   - explicit new campaign after an adopted closeout: [Entry and planning](references/entry-and-planning.md) in post-closeout recovery mode;
   - planned or active campaign: [Campaign cycle](references/campaign-cycle.md);
   - stop, halt, or external claim: [Closeout and claims](references/closeout-and-claims.md).
   - explicit packaging after complete closeout: [Packaging and durable recovery](references/packaging-and-recovery.md).
5. Load zero or more action references only when the chosen stage reaches their stated trigger.
6. Immediately before the final reply, read [User-facing handoff](references/user-facing-handoff.md) last and apply its completion check to the already persisted outcome. This formatting pass may not rerun routing, direction resolution, review, or state adoption.

If the router returns `PARENT_REVIEW_REQUIRED`, load no stage file and continue to step 6. If no router row fits, record `BLOCKED` with the conflicting fields and continue to step 6.

## Load references by action

| Action | Load |
|---|---|
| Read or update F1-F8, Budget, or Selection | [Campaign state](references/campaign-state.md) |
| Read or update T, V, B, E, or Q | [Planning records](references/planning-records.md) |
| Read or update D or X | [Evidence records](references/evidence-records.md) |
| Read or update C or A | [Claim records](references/claim-records.md) |
| Create or revise W | [Work plan](references/work-plan.md) |
| Delegate any worker | [Worker interfaces](references/worker-interfaces.md), then the action-specific packet or review reference |
| Freeze, review, validate, or adopt any review snapshot | [Review snapshots](references/review-snapshots.md) |
| Freeze or verify an authority-bearing identity | [Provenance and identity](references/provenance-and-identity.md) |
| Plan executable candidate work during Entry | [Entry code planning](references/entry-code-planning.md) |
| Choose a code-design profile, draft or repair a module or system design, or change a design contract | [Technical design](references/technical-design.md) |
| Manage executable candidate identities | [Candidate lifecycle](references/candidate-lifecycle.md) |
| Reuse an evaluation protocol or admit, adopt, or recover a pre-authorized routine screen | [Evaluation protocol reuse](references/evaluation-protocol.md) |
| Freeze or review an Entry plan | [Entry review](references/entry-review.md) |
| Freeze or review a technical design | [Design review](references/design-review.md) |
| Dispatch or reconcile a B | [Batch interface](references/batch-interface.md) |
| Adopt a terminal B, review a materialized candidate, or adopt E | [Result adoption](references/result-adoption.md) |
| Interpret an experiment, research, representation, mechanism, or candidate-performance result | [Fresh-context Reflection analysis](references/reflection-analysis.md), then [Learning loop](references/learning-loop.md) |
| Reflect, investigate, or replan after a B | [Learning loop](references/learning-loop.md) |
| Review a materialized candidate | [Implementation review](references/implementation-review.md) |
| Review external claim wording | [Claim review](references/claim-review.md) |
| Package a complete closeout or validate exact recovery reuse | [Packaging and durable recovery](references/packaging-and-recovery.md) |

Do not load a reference merely because it may become relevant later. Every template and normative interface has one owner in this table.

For a recorded W, load Technical design when `design_status` is `drafting`, `review-pending`, or `repair-required`, or when new evidence requires a contract-bearing design change. Do not load it merely because an executing B cites a `ready` module or system design; use W's `Read when` pointers to load only the concern contracts needed for that action.

## Coordinate workers

Before delegation, create the target, fix its parent versions, allowed paths, result path, and completion check. Invoke only:

- `research-frontier` for one evidence question;
- `grill-frontier` for one unresolved user-owned tradeoff or exact execution authorization;
- `run-frontier-batch` for one exact B packet;
- `review-frontier` in a fresh context for one immutable Entry, strategic replan, technical design, candidate implementation, or claim snapshot.

For a user authorization tied to a concrete B packet, apply [Entry review](references/entry-review.md) from structural validation through post-answer adoption. Apply the Frontier Core finding effects at every validator and review seam. Pass the mutable draft through the single `prepare_review` interface before allocating an R identifier or dispatching a reviewer. A `NOT_READY` draft remains ordinary work in the same B; repair it without creating a snapshot, decision, packet, supplement, or recovery chain. Ask only after `AUTHORIZATION_READY` with no block or repair finding; accept authority only after the frozen adoption validator returns `ENTRY_READY` for the unchanged target.

Validate every result against its packet. A worker result changes no campaign state until this Skill records its accepted meaning. Preserve invalid, partial, negative, and costly output with an explicit disposition.

For a terminal result with technical or research meaning, complete one fresh-context Reflection analysis before exposing that analyst to the current Selection, Budget, authority, R8 resolution, campaign stop, closeout, or proposed next action. Fix the accepted evidence-grounded research fields first; only then add operational consequences and run the integrated direction resolver. This analysis is a read-only reasoning pass, not a worker, review, campaign artifact, identity, or authority event.

For code-bearing authorization, freeze the source-derived target specification before packet identity, then derive packet and preflight, exact post-adoption bytes, and the final target in that order. The specification contains stable decision semantics but no current packet or downstream identity. Entry must prove that the final target is its exact realization before asking the user.

Dispatch every B through the [Batch Interface state machine](references/batch-interface.md#dispatch-state-machine). Perform only the Coordinator-owned rows; require packet preflight to prove result-contract compatibility and source-derived project design, source-base, and authorization-target bindings before Entry review. For experiment work, require the canonical nested target to bind the complete candidate root and derive the experiment identity from the exact contract bytes; reject copied experiment identities in prose fields. For code-bearing work, require a frozen engineering check plan whose selected units, content-addressed effect evidence, positive effect limits, and engineering-only consequence agree. Run the shared candidate-package validator and enforce the forward-only inventory, staged checks, completed evidence, final manifest, result sequence before result adoption. Require the Entry review artifact itself to bind its exact packet and complete portable review subject. Workflow, Skill, validator, Slice 7, bundle, and workflow-test bytes never enter the review subject, B packet, or ordinary Entry completion check. For every Coordinator file that authorization may change, bind complete pre- and post-state bytes through `frontier-post-adoption-state/1`; do not use patches or drift exclusions. Require `run-frontier-batch` to return after acknowledgment, and invoke it again only after the baseline tool has recomputed the packet, adoption, acknowledgment, and execution-start chain. The tool must reproduce authorization from the Entry subject, verify the exact reviewed live post-state separately, and reject every other live project change. For the first B of a planned campaign, authorize the structured lifecycle rule from Batch Interface, instantiate its UTC values only after accepted acknowledgment, and freeze its exact receipt and post-transition bytes in one portable `project-state` root. Rerun result validation and the bound execution chain byte for byte before adopting a terminal outcome or preparing another review subject.

Delegation is complete only when the assigned worker has written its exclusive result, the result satisfies the packet's completion check, and this Skill has either adopted its checked meaning or recorded the exact blocker and recovery point.

New lifecycle objects use the current typed Provenance writer. The detailed version 1 identity fields remain available only through its bounded completion adapter.

## Preserve the authority boundary

Apply each restriction only to its named consequence. Treat decision-relevant read-only evidence gathering as planning unless an exact parent or user rule prohibits that access; restrictions on execution, spend, remote side effects, publication, or claims do not prohibit it.

Treat the inherited evaluated baseline as the comparison reference, not as the automatic campaign baseline. Entry must compare a bounded set of technically eligible starting points using current evidence and must ask the user when the choice depends on value, cost, risk, reversibility, maintenance, or another user-owned preference. A campaign baseline may be simple, but its selection must explain why it can carry later optimization and what evidence would replace it.

At Entry, apply [Entry and planning](references/entry-and-planning.md) to reconcile peer route sources into a decision-complete route set. Apply the [T eligibility contract](references/planning-records.md#t-route) before Selection: one eligible route needs no ceremonial T or user-choice V, and an unresolved load-bearing prerequisite permits only its smallest sufficient prerequisite-first work.

Do not begin candidate development without `AUTHORIZATION_READY`, the user's exact answer, and Coordinator `ENTRY_READY` adoption for the unchanged reviewed target. For W-backed work, bind the design identity and scope, never the whole mutable W file; keep current authorization only in external lifecycle records. Keep design readiness, development authorization, implementation readiness, diagnostic evidence, Slot H measurement, integration, incumbent use, promotion, and claim approval separate. Load the diagnostic-only exception in [Candidate lifecycle](references/candidate-lifecycle.md#diagnostic-only-exception) only for a low-risk local first signal before implementation review. After a finding-free implementation review, use a pre-authorized single-use screen only through [Evaluation protocol reuse](references/evaluation-protocol.md). Both remain B evidence and grant no later consequence.

After every terminal B, reconcile evidence and complete one controlling Outcome Reflection before later spend. Resolve direction inside that mandatory learning loop; do not add a separate direction stage or let a worker choose the route. Cover every later E, keep implementation and Slot H evaluation in separate B records, join parallel results before dependent work, and require applicable V and fresh review gates. Derive the next Selection only from persisted state and exact R8 rules so the same state produces the same next action or blocker. Apply maximum optimization pressure at the earliest justified experiment; do not hide unbounded preparation behind a baseline label or defer every discriminating test to later work.

Use the same `review-frontier` worker for claims with `review_kind: claims`. Adopt every finished claim review through A, including nonpositive results; use withdrawing X only when C is withdrawn before review completion. A or X ends that C branch. A claim-only branch preserves campaign status and returns to Cycle when no other stop or halt applies. Only full closeout settles final budget, active work, retained results, gap, and handoff.

A parent conflict before any campaign record returns `PARENT_REVIEW_REQUIRED` and directs the caller to `$frame-optimization`. After campaign records exist, use the exact pre-spend rebind route only when every recorded condition holds; every other parent conflict forces closeout. Never invoke `$frame-optimization` from this Skill, create another Coordinator, or create document-state scripts.

A completed closeout remains immutable. Package it only on an explicit packaging request, with no authority effect, by validating and atomically publishing one content-addressed handoff whose bytes recover without conversation or Git history. Open a later recovery campaign only from a separate explicit current user request and the post-closeout router row. A general reopen request grants planning-only campaign-opening authority: record that request, then derive the proposed technical objective from the unchanged parents and retained closeout evidence. Keep that opening authority separate from any later user-owned route tradeoff and from exact B authorization. Require a user-named objective only when the request names a particular recovery object or outcome. Before any new-generation artifact, mechanically recompute every requested candidate and manifest identity from canonical bytes. Increment `campaign_generation`, carry forward all prior spend against the parent ceiling, use new record identifiers, and append exact V and X mappings for every reused object. Reusing byte-identical candidate bytes creates no second proposal identity, but it grants no measurement, integration, incumbent, or claim permission until the recovery Entry and fresh implementation review are adopted.

The run is complete only when the task files reproduce the reported outcome, every accepted decision appears in its owning record, and the final reply passes step 6.
