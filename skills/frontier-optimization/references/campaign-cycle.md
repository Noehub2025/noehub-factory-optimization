# Frontier Campaign Cycle: Result Adoption, Evidence Learning, and Next-Batch Selection

Load when `frontier-core.md` selects active campaign work, result adoption, or a pending next decision, including when no B is currently selected. Also load for a recorded `drafting` or `repair-required` W design action under planning authority. Execution still needs the gates for its actual Consequence. This stage handles:

- one simple non-code B with no W; or
- one `direct` code B with no W, ending at the materialized-candidate checkpoint;
- one complex non-code B under a current W;
- one professional design answer, draft or revision, using W only when its shared map is needed;
- one evidence-producing design checkpoint or code slice under a current W; or
- one human-input B with its request and validation contract in B or W;
- one executable or mixed B with an explicit working-observation target inside the current Batch scope;
- one diagnostic-only measurement inside its current B, or the retained historical-candidate exception when it actually applies;
- one routine-local measurement through the current Batch-owned Measurement Definition;
- one separate formal Slot H evaluation B for an unchanged `IMPLEMENTATION_READY` candidate; and
- result adoption and continuous research, with direction resolution only when investment needs reconsideration.

An explicit working-observation target does not authorize an external, paid, human, physical, sensitive, or other Consequence beyond its existing V. Parallel B records are executable only when mutable paths do not overlap, shared technical obligations remain compatible, one integration owner and join check are named, and neither result configures or permits the other. Record `BLOCKED` with the exact missing owner or condition when no listed profile owns the action.

## Contents

- [Load only the current action](#load-only-the-current-action)
- [Recover the selected B](#recover-the-selected-b)
- [Current readiness and consequence gate](#current-readiness-and-consequence-gate)
- [Current action acceptance scenarios](#current-action-acceptance-scenarios)
- [Resolve direction before Selection](#resolve-direction-before-selection)
- [Route the current action](#route-the-current-action)
- [Slice 5 acceptance scenarios](#slice-5-acceptance-scenarios)

## Load only the current action

- Load [Campaign state](campaign-state.md) and [Planning records](planning-records.md) for current allocation, adopted results, baseline and Budget; resolve the selected B only when one exists.
- Load [Current Batch](batch-current.md) to open, revise, perform, continue or reconcile a new B. Load [Historical Batch interface](batch-interface.md) only when the retained B actually contains those fields.
- Load [Executable work](batch-code-execution.md) for current executable material. Load [Candidate lifecycle](candidate-lifecycle.md), [Review snapshots](review-snapshots.md), and historical implementation-review material only when an actual retained record or external publication seam uses them. Load [Evaluation protocol reuse](evaluation-protocol.md) only when the current Measurement Definition reuses calibration or shared protocol meaning.
- Load [Result adoption](result-adoption.md) only after a worker result exists, when freezing a materialized candidate review, adopting diagnostic evidence, or validating and adopting E.
- Load [Work plan](work-plan.md) when B cites W. Load only W frontmatter, Current state, the obligations named by the B's `delivery_scope`, applicable Validation and Definition-of-done terms, Recovery, and Design-map rows whose `Read when` condition matches the action.
- Load [Technical design](technical-design.md) for a consequential unresolved design question or affected adoption. Load [Design review](design-review.md) only for required independent judgment or its adoption.
- Use [Active learning chain](learning-loop.md#active-learning-chain) to order current work, including early preparation. Load the resolver only when its investment trigger applies, and [Evidence records](evidence-records.md) only for a controlling D or X action.
- Load [Claim records](claim-records.md) only when exact external wording or a claim-review request appears. Do not load [Claim review](claim-review.md) in this slice.
- Load [Worker interfaces](worker-interfaces.md) before invoking `design-implementation`, `run-frontier-batch`, or `review-frontier`.

Do not reload `technical-design.md` to execute a `ready` design. Follow W's matching `Read when` pointers and load only the exact concern contracts required by the selected B. Do not load learning-loop, evidence, or claim references before their triggers occur.

For a current `frontier-batch/1` record, use [Current Batch](batch-current.md) for lifecycle and result ownership. Existing Entry Review, Permission, Budget, resolver, adoption and claim rules remain in force at their actual Consequences. References below to packet, acknowledgment, execution-start, snapshots, self-identities or typed execution and outcome roots apply only when an actual historical B already contains them; they are not current writer requirements.

## Recover the selected B

Apply [Change impact](frontier-core.md#change-impact-and-retained-results) before treating a parent difference as a blocker. Continue unaffected work and reuse applicable saved reviews; update only the next affected decision. A material shared-premise change follows [Research-basis transitions](frontier-core.md#research-basis-transitions), not full closeout.

Read current parent reviews, `FRONTIER.md`, latest Budget and Selection, applicable V, and the records needed by the current action. For result adoption, read the producing B, result, accounting and related E or join disposition even if that B is no longer Primary. When no B is selected and adoption is complete, skip B and W execution recovery and proceed to [Resolve direction before Selection](#resolve-direction-before-selection); create no placeholder B. Owning records establish project facts; user instructions establish requested scope under [User decisions](user-decisions.md). Read historical identities only when recovering a B that already contains them.

For W-backed work, resolve the exact W path, current `plan_revision`, applicable design sections, the B's delivery obligations, design Review, current Permission, worker progress, discoveries, and recovery state. Treat the worker's mutable work breakdown as progress, not authority. For executable work, recover the latest working or selected Git Candidate Revision, retained checks, Attempts, consumption, Consequences, result, and next affected action. Recovery without the original branch or worktree is valid when the required Git or external artifact references remain available. It does not require a package, snapshot, manifest, execution-start, or result identity that the current B never created.

For human input, recover the request, schema, provenance requirements, quality checks, confidentiality limits, response identity, validation state, and resume event. Do not infer a missing answer or validation from conversation history.

Before resuming a recorded next action, recover the research question, missing observation and changed remaining work through [Active learning chain](learning-loop.md#active-learning-chain). Historical repair ordering does not override a current material investment challenge. When the retained rationale still applies, resume at the first missing applicable step: working continuation and affected checks; an applicable Review; `Batch.perform` for a measurement or Consequence; result reconciliation; B conclusion; E adoption when valid; applicable research or V; replan review; join; and next-investment Selection. Skip stages that do not apply. Never repeat an Attempt whose result or Consequence is unknown merely because the live workspace is missing.

## Current readiness and consequence gate

Use [Entry review](entry-review.md) only when a fresh technical or value decision is actually required. A current B begins routine preparation under the selected objective, applicable R and V, and Batch limits. Planning, editing, debugging, harmless checks, design-slice revision, and repair do not require a packet, acknowledgment, snapshot, execution-start, result identity, or repeated Entry.

Before a measurement or Consequence, call `Batch.perform`. It reads the Batch-owned Measurement Definition when applicable, verifies the selected Git revision, required checks, R applicability, protected-Consequence V coverage, Batch operational limits, the Measurement Definition resource ceiling, V-owned resource limits and prior Attempts. Ask the user only when the action crosses an uncovered boundary in [User decisions](user-decisions.md). A changed internal method, local limit or Candidate Revision does not itself require another question.

If the operation can be repeated safely and has no measurement or Consequence, use `Batch.apply` and continue. If repetition could duplicate an effect, `Batch.perform` creates a local Attempt before invoking the adapter. A blocked precheck creates no Attempt. An operation failure after start leaves the Attempt `uncertain`. Until reconciliation, it blocks another `Batch.perform` in that B; ordinary `Batch.apply` work and other B records continue. For single-use work, [Current Batch measurement](batch-evaluation.md) protects the actual unit across Action-key changes.

Historical B records continue through their recorded packet and dispatch contracts. Do not convert them or make those contracts requirements for a current B.

## Current action acceptance scenarios

| Scenario | Required durable outcome |
|---|---|
| Routine preparation, editing, or a harmless check fails | Keep the same B open, repair the affected work, and rerun only affected checks; create no Attempt or new B. |
| The selected Git revision or required passing check does not match the action | Block the affected action before the adapter starts; select or check the correct revision. |
| R no longer applies or V does not cover a protected Consequence | Block the affected action before an Attempt; obtain only the missing Review or user decision. |
| Requested resources exceed a Batch operational limit, while the same investment remains inside its strategic allocation, Measurement Definition and governing boundaries | Block before the adapter starts, record no Attempt, let the Coordinator revise the same B's limit from current evidence, and continue. Do not invoke the resolver, Replan, or the user. |
| A measurement request exceeds its Measurement Definition resource ceiling | Block before the adapter starts and record no Attempt. Revise the existing measurement contract through its applicable owner only if the evidence justifies different exposure or meaning; do not treat the ceiling as Campaign Budget or user authority. |
| A V-owned resource exceeds its applicable user boundary | Block before the adapter starts; reuse current V when it covers the action, otherwise ask only for the boundary that must change. |
| Governing campaign capacity or protected reserve cannot fund the next sufficient commitment | Pause the unfunded action through the existing resource owner. If the investment must change, use Learning Loop; an internal estimate or Batch operational cap alone creates no direction decision. |
| An adapter fails after an Attempt starts | Mark that Attempt `uncertain`, preserve known effects, and block another `Batch.perform` in that B until reconciled; continue routine changes and other B records. |
| An operation reports more use or a different Consequence than declared | Preserve actual facts, flag the contract violation, and block dependent use; do not rewrite the record to match the plan. |
| Unrelated files, workflow deployment, caches, or working notes change | Continue unless they are selected inputs or change an owning decision. |
| A historical B already has packet and execution identities | Validate that B with its historical compatibility reader; do not generate those identities for current work. |

## Resolve direction before Selection

Use only [Integrated direction resolver](learning-loop.md#integrated-direction-resolver). This file adds no direction table, fallback priority, research-first exception, or post-resolver R8 override.

Use [Active learning chain](learning-loop.md#active-learning-chain) to continue the current research problem after adoption. A terminal B or a new follow-on B does not itself require a direction resolution. Update only affected progress and Selection facts, reusing the applicable research rationale.

At [When to reconsider investment](learning-loop.md#when-to-reconsider-investment), supply the relevant adopted evidence and professional findings to one independent resolver. Follow [Selection](campaign-state.md#selection) to apply an in-flight switch without waiting for unrelated work or releasing resources still in use.

At a formal direction choice, another evidence round is permitted only when resolver row 7 or row 8 selects it. Bind the Q to current adopted results. Reconcile relevant industrial implementations, academic evidence, community reports or artifacts, repository evidence, retained results, observed failures, and related research Reflection and original sources under one decision, action window, evidence-channel assignment, and search stop. Stop when the information is sufficient for the current allocation and further retrieval is unlikely to change it. Do not require exhaustive coverage, a source quota, or research after routine row 13.

For a strategic change, prepare the proposal without dependent spend. Until an unchanged review is adopted as `REPLAN_READY`, the current route allocation remains authoritative and no dependent B, reservation, implementation, evaluation, integration, promotion, or claim consequence may proceed. A later specialized gate remains separate but cannot select a different direction from the resolver.

A Candidate Revision or route-scope disposition does not by itself enter full closeout. Preserve the rejected revision or closed route and every applicable Permission. A repair inside the same independently judged result returns to the same B under [Boundary-preserving continuation](batch-current.md#boundary-preserving-continuation), even when an earlier revision was retained or externally published. Record a new Candidate Revision and apply only the Review, Permission, cost, or external-publication consequence that the changed use actually requires. After a route disposition, follow a still-applicable surviving action; if none is named, resolve the current action space rather than treating an empty prior list as a blocker or completion. Continue a worthwhile direct action, select one grounded row-7 inquiry when it can change allocation, or select campaign stop and full closeout when neither remains. Route-list exhaustion and an unmet objective alone do not require research. Only a campaign-wide ending enters full closeout. Research-basis transitions can advance Generation while applicable work continues; use the core transition rules, not the full stopping and recovery chain.

At a substantive route completion, retirement, replacement or learning checkpoint, use [Research Reflection](learning-loop.md#research-reflection). This captures experience without inserting a Reflection between every result and its next action.

## Route the current action

Choose one row below to load the owner of the current action. Adoption, accounting and required joins precede dependent work; the Coordinator continues the current research problem or consumes an applicable investment judgment. If that next execution decision needs an Entry, use [Entry and planning](entry-and-planning.md), then resume here. This file-loading table cannot alter the resolver's technical choice.

| Current action | Load | Completion criterion |
|---|---|---|
| Execute one simple non-executable B | [Current Batch](batch-current.md) and [Planning records](planning-records.md) | One bounded result or recovery condition is recorded; worker observations have no adopted campaign meaning |
| Resolve or revise an important design question | [Technical design](technical-design.md), then `design-implementation`; load [Work plan](work-plan.md) only when W is needed | Designer answers in the assigned existing work or design content; the Coordinator adopts it and any required delivery bindings or independent judgment, then continues covered work |
| Execute complex non-code, shared W, design-evidence, or human-input work | [Work plan](work-plan.md); add [Technical design](technical-design.md) only when the evidence changes a contract | Exact W revision, stable Delivery slice, and Entry realization govern the B; only assigned progress or discoveries change worker-side |
| Develop, recover, review, or measure executable material | [Executable work](batch-code-execution.md), then [Result adoption](result-adoption.md) when a result exists | Working revisions and checks remain in one B; measurement uses an Attempt and its result receives only supported meaning |
| Validate a result, reconcile spend, freeze implementation review, or append E | [Result adoption](result-adoption.md) | Result meaning, spend, recovery, candidate review, and E eligibility are durably dispositioned |
| Diagnose, research, replan, join, or select the next B | [Learning loop](learning-loop.md); add [Campaign state](campaign-state.md) or [Evidence records](evidence-records.md) only for the record being written | Every selected terminal B is adopted, every eligible E is dispositioned, and the same state yields the same next action or blocker |
| Open an exact external wording request | [Claim records](claim-records.md) | C and `CLAIM_REVIEW_REQUIRED` are durable; the claim branch stops before review or A |

For simple non-code work, require `changes_executable_candidate: false`, no W, no executable or public-interface change, one bounded checkpoint and recovery point, and no unavailable input. If execution reveals a W, code, human-input, shared-contract, or multi-checkpoint prerequisite, stop and report the scope change. A result may be `completed`, `interrupted`, `failed`, `blocked`, or `waiting_for_input`; `actual_spend: unknown` remains truthful evidence and blocks new spend until reconciled.

When a separate implementation Review is required for a later measurement or integration Consequence, it must apply to the exact selected Git Candidate Revision. Working material may receive an explicit bounded observation inside its existing B when its current V and resources cover the action. A separately funded or independently judged evaluation uses another B; a one-off measurement inside the current judged result uses a local Attempt. Neither raw observation automatically creates E, promotion, integration, incumbent use, or a claim.

Finish the current action's completion criterion before loading its successor. Return the recorded outcome to the Coordinator, which adopts it and advances through the core router within [the continuing task](user-decisions.md#continuing-task-and-stage-instructions). Completion of one row is not completion of the overall task.

## Slice 5 acceptance scenarios

| Scenario | Required durable outcome |
|---|---|
| Expected valid result within the current research problem | Adopt it and arrange the next necessary work without a new resolver, row-13 record or additional analysis stage. |
| Surprising result that may be an implementation or measurement problem | Its professional owner investigates the affected condition; use the investment trigger only when the discovery may change allocation. Unresolved validity cannot support route failure. |
| Formal direction choice has an experiment-bound evidence gap | Resolver row 7 or 8 selects one bounded Q that reconciles current experiment results with applicable industrial, academic, community, repository, and retained evidence, then reruns the same resolver after adoption. |
| Formal direction choice is already supported by complete evidence and a determined R8 action or technical ordering | Do not add another Q merely because a direction is being selected; apply the determined row and next gate. |
| Result retains or changes a reference, comparator, incumbent, route, or allocation | Apply the role and actual consequence: use normal retention under an unchanged rule, the owning measurement gate for changed comparison meaning, or Replan only when the change crosses an actual governing strategic boundary under [Evidence consequence levels](learning-loop.md#evidence-consequence-levels). Historical technical ordering alone does not establish that boundary. |
| Two funded diagnostic paths remain non-dominated | The technical owner handles local diagnosis; use the independent resolver for a reopened investment choice, not user arbitration. |
| A sufficient check would consume protected reserve | Resolver row 5 selects no B or spend-bearing Q and returns the exact Budget, stop, or zero-spend Replan consequence. |
| Code implementation followed by performance evaluation | Separate implementation B and Slot H evaluation B; evaluation is blocked before unchanged `IMPLEMENTATION_READY`. |
| Unpublished working material needs a bounded decision-relevant signal | Continue inside its existing B only when the explicit working-observation target covers the question, methods, resources, and exposure. Do not terminalize the B or run the resolver after each observation. |
| An already published historical candidate needs a signal before implementation review | A separate diagnostic-only experiment may run only under the candidate-lifecycle exception; it creates no E and grants no integration, incumbent, promotion, submission, or strength consequence. |
| Parallel selected B records | Adopt each result when available; wait for the relevant join only before dependent work. Unrelated work can continue. |
| E contradicts an active applicable bound | No promotion, incumbent use, claim strengthening, or dependent spend until the contradiction is resolved and dispositioned. |
| Two E use different evaluator, comparator, protocol, workload, epoch, or parent meaning | Exclude the incompatible E with its reason; do not form a trajectory from them. |
| Valid whole-package comparison with no ablation | Support the bounded package-level effect; record component contribution as unresolved without creating diagnosis or research. |
| Source and behavior checks prove component pathways exist, but performance evidence is aggregate | Describe the pathways as present and consistent; do not call any one active, necessary, dominant, or numerically responsible. |
| Positive proxy movement accompanies a failed guardrail or required segment | Preserve the full parent-owned vector; the route is not established. |
| Increments shrink but no prospective negligible-progress rule governed the spend | Record only the supported observation; do not declare a plateau retroactively. |
| A factor has only local or proxy evidence | Record a suspected constraint only when it changes the decision; do not call it the bottleneck. |
| Changing a factor changes the parent objective under the named conditions | A demonstrated constraint is available; after intervention, check whether the limiting constraint shifted. |
| One-shot, administrative, or implementation-only work has no cross-B performance meaning | Use the applicable `not-applicable` fields and create no extra diagnosis, research, review, metric, E, or trajectory artifact. |
| A terminal implementation result has positive implementation review but no later resolver result | Adopt the result and arrange the next work within the current research problem. A separate measurement B needs its execution prerequisites, not a new direction comparison. Implementation evidence is not performance evidence. |
| A comparator-derived score saturates after resolving its addressed decision | Preserve the completed decision; record a future-use measurement implication only if a concrete successor decision would need more discrimination. |
| Current work cites E interpreted by a legacy OR | Preserve the old OR bytes and original limits; current Selection uses compatible adopted evidence without migrating OR coverage. |
| Mid-campaign external wording request | C plus `CLAIM_REVIEW_REQUIRED`; no claim-review completion or A in this slice. |

At terminal completion, a fresh Coordinator must be able to recover the current Batch definition, selected Git Candidate Revision when used, applicable R and V references, checks, Attempts, actual consumption and Consequences, terminal result or human-input wait, artifacts, spend, E disposition, an investment resolution when one was needed, adopted research, replan review, parallel join, and latest Selection. Historical B records additionally retain their original packet, acknowledgment, snapshot, execution-start, identity, and validation chain; do not recreate it for current work. A real next-decision change uses the existing X and Selection path. No later Consequence is permitted without the applicable evidence, V, necessary join, Review and remaining resource conditions. A fresh direction resolution is not an execution credential for ordinary continuation.
