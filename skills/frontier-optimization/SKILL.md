---
name: frontier-optimization
description: Coordinate Optimization Frontier campaigns from a positive Representation handoff through Entry, repeated batches, closeout, post-closeout recovery, and durable packaging. Use only when the user explicitly asks to start, resume, recover, open a new campaign after closeout, close, package a completed campaign, or review claims for one canonical Frontier task.
---

# Frontier Optimization

Act as the only Frontier Coordinator. Choose the next stage from recorded state, assign bounded work, validate results, and adopt accepted meaning into campaign records. No other Skill may perform Coordinator writes.

## Start with the minimum context

1. Read [Frontier core](references/frontier-core.md).
2. Select one canonical task path and validate the exact positive Representation handoff against its parent documents and reviews.
3. Apply the recorded-state router. Do not infer state from conversation history.
4. Load exactly one stage file:
   - no campaign or incomplete Entry: [Entry and planning](references/entry-and-planning.md);
   - explicit new campaign after an adopted closeout: [Entry and planning](references/entry-and-planning.md) in post-closeout recovery mode;
   - planned or active campaign: [Campaign cycle](references/campaign-cycle.md);
   - stop, halt, or external claim: [Closeout and claims](references/closeout-and-claims.md).
   - explicit packaging after complete closeout: [Packaging and durable recovery](references/packaging-and-recovery.md).
5. Load zero or more action references only when the chosen stage reaches their stated trigger.

If the router returns `PARENT_REVIEW_REQUIRED`, load no stage file. If no router row fits, return `BLOCKED` and name the conflicting fields.

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
| Plan executable candidate work during Entry | [Entry code planning](references/entry-code-planning.md) |
| Choose a code-design profile, draft or repair a module or system design, or change a design contract | [Technical design](references/technical-design.md) |
| Manage executable candidate identities | [Candidate lifecycle](references/candidate-lifecycle.md) |
| Freeze or review an Entry plan | [Entry review](references/entry-review.md) |
| Freeze or review a technical design | [Design review](references/design-review.md) |
| Dispatch or reconcile a B | [Batch interface](references/batch-interface.md) |
| Reflect, investigate, or replan after a B | [Learning loop](references/learning-loop.md) |
| Review a materialized candidate | [Implementation review](references/implementation-review.md) |
| Review external claim wording | [Claim review](references/claim-review.md) |
| Package a complete closeout or validate exact recovery reuse | [Packaging and durable recovery](references/packaging-and-recovery.md) |

Do not load a reference merely because it may become relevant later. Every template and normative interface has one owner in this table.

For a recorded W, load Technical design when `design_status` is `drafting`, `review-pending`, or `repair-required`, or when new evidence requires a contract-bearing design change. Do not load it merely because an executing B cites a `ready` module or system design; use W's `Read when` pointers to load only the concern contracts needed for that action.

## Coordinate workers

Before delegation, create the target, fix its parent versions, allowed paths, result path, and completion check. Invoke only:

- `research-frontier` for one evidence question;
- `grill-frontier` for one user-owned tradeoff or authorization;
- `run-frontier-batch` for one exact B packet;
- `review-frontier` in a fresh context for one immutable Entry, strategic replan, technical design, candidate implementation, or claim snapshot.

Before delegating a user authorization that names a concrete B packet, complete structural packet validation, W traceability when applicable, draft and frozen Entry schema validation, and one fresh full authorization-readiness review. Ask only after finding-free `AUTHORIZATION_READY`. Bind the question to that review and exact target. After the answer, run the deterministic authorization-adoption validator for identity, staleness, and answer fidelity. A condition or changed object requires a new review before another question.

Validate every result against its packet. A worker result changes no campaign state until this Skill records its accepted meaning. Preserve invalid, partial, negative, and costly output with an explicit disposition.

Dispatch every B in two durable phases. Before either phase, reproduce the structural preflight and exact Entry adoption authority. First let `run-frontier-batch` validate the immutable packet and write its acknowledgment, then require it to return without work or spend. Perform only the packet's exact Coordinator lifecycle transition, use the bound baseline tool to copy every post-transition input into the exclusive content-addressed execution-baseline snapshot, and write the Coordinator-owned execution-start record only after snapshot validation passes. Invoke the worker again only after the record binds that snapshot. Never use a worker-forbidden path as shorthand for global immutability.

Require every worker result to pass the bound profile-aware result validator in draft and frozen form before the immutable result path is written. Rerun frozen validation byte for byte before adopting a terminal outcome or creating a review snapshot. A materialization result must keep `results: []`; candidate information belongs in dedicated candidate, source, manifest, and engineering fields.

## Preserve the authority boundary

Treat the inherited evaluated baseline as the comparison reference, not as the automatic campaign baseline. Entry must compare a bounded set of technically eligible starting points using current evidence and must ask the user when the choice depends on value, cost, risk, reversibility, maintenance, or another user-owned preference. A campaign baseline may be simple, but its selection must explain why it can carry later optimization and what evidence would replace it.

Do not begin candidate development without `AUTHORIZATION_READY`, the user's exact answer, and Coordinator `ENTRY_READY` adoption for the unchanged reviewed target. For W-backed work, bind the design identity and scope, never the whole mutable W file; keep current authorization only in external lifecycle records. Keep design readiness, development authorization, implementation readiness, measurement, integration, incumbent use, promotion, and claim approval separate.

After every terminal B, reconcile evidence and complete one controlling Outcome Reflection before later spend. Cover every later E, keep implementation and Slot H evaluation in separate B records, join parallel results before dependent work, and require applicable V and fresh review gates. Derive the next Selection only from persisted state and exact R8 rules so the same state produces the same next action or blocker. Apply maximum optimization pressure at the earliest justified experiment; do not hide unbounded preparation behind a baseline label or defer every discriminating test to later work.

Use the same `review-frontier` worker for claims with `review_kind: claims`. Adopt every finished claim review through A, including nonpositive results; use withdrawing X only when C is withdrawn before review completion. A or X ends that C branch. A claim-only branch preserves campaign status and returns to Cycle when no other stop or halt applies. Only full closeout settles final budget, active work, retained results, gap, and handoff.

A parent conflict before any campaign record returns `PARENT_REVIEW_REQUIRED` and directs the caller to `$frame-optimization`. After campaign records exist, use the exact pre-spend rebind route only when every recorded condition holds; every other parent conflict forces closeout. Never invoke `$frame-optimization` from this Skill, create another Coordinator, or create document-state scripts.

A completed closeout remains immutable. Package it only on an explicit packaging request, with no authority effect, by validating and atomically publishing one content-addressed handoff whose bytes recover without conversation or Git history. Open a later recovery campaign only from a separate explicit current user request and the post-closeout router row. Before any new-generation artifact, mechanically recompute every requested candidate and manifest identity from canonical bytes. Increment `campaign_generation`, carry forward all prior spend against the parent ceiling, use new record identifiers, and append exact V and X mappings for every reused object. Reusing byte-identical candidate bytes creates no second proposal identity, but it grants no measurement, integration, incumbent, or claim permission until the recovery Entry and fresh implementation review are adopted.

The run is complete only when the task files reproduce the reported outcome and every accepted decision appears in its owning record.
