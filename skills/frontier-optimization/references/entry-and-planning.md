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
- [Record the Entry decision](#8-record-the-entry-decision)
- [Obtain independent Entry review](#9-review-the-entry-decision)
- [Record one outcome, then finalize the return](#record-one-outcome-then-finalize-the-return)

Use this stage for initial Entry, post-closeout recovery, or an affected decision after a parent revision. Initial Entry produces a reproducible first-batch plan with zero new-generation B spend and reconciled inherited and Entry cost. Parent revision follows its scoped branch below without reopening initial Entry.

Match planning to the requested deliverable under the [Coordinator's scope and completion rule](../SKILL.md#recover-and-choose-the-current-action). For campaign-opening planning that needs a first-batch Entry, a ready design is a prerequisite, not a completed plan: continue to `FIRST_BATCH_PLANNED` or an applicable stage blocker. Reuse existing plans and reviews; prepare Entry only for a decision that actually needs it. A design-only, advisory or local planning request may finish at its requested deliverable without creating a B or completing Entry.

## Load only what Entry reaches

Load [Campaign state](campaign-state.md) and [Planning records](planning-records.md). Load [Evidence records](evidence-records.md) in post-closeout recovery mode. Load [Worker interfaces](worker-interfaces.md) before delegating research, a user decision, Entry review, or any other worker action. Load [Current Batch](batch-current.md) before opening a selected B. If eligible work may change software, load [Entry code planning](entry-code-planning.md). When recovery proposes an existing historical candidate for measurement, load [Candidate lifecycle](candidate-lifecycle.md), [Review snapshots](review-snapshots.md), and [Implementation review](implementation-review.md). Load [Entry review](entry-review.md) only after the proposed Entry subject is complete.

## 1. Validate the handoff

Bind the exact Problem epoch, Representation revision, generation times, positive reviews, reference baseline, measurement identity, exact `Permitted` text, R1-R8, budget authority, and claim limits. Copy no broader meaning into Frontier records.

Refer a missing or conflicting requirement to its parent owner under [Change impact and retained results](frontier-core.md#change-impact-and-retained-results). Use `PARENT_REVIEW_REQUIRED` for the dependent action only if that repair cannot proceed within current permission.

### Adopt a parent revision

Use this path when the core router selects parent-revision mode. Apply [Change impact and retained results](frontier-core.md#change-impact-and-retained-results); prior spend does not select another path.

Use the parent owner's adopted revision to update the next affected decision in the existing X, Selection and campaign view. Preserve the generation, B and W when their work remains applicable. Keep historical packets, reviews, execution inputs and charges unchanged. Reuse unaffected conclusions and permission; obtain only the missing or affected Entry, Replan or specialist review required by the changed decision.

A completed parent revision returns to the existing Campaign Cycle. It neither resets Entry accounting nor requires zero historical B spend or a replacement first batch.

### Open a post-closeout recovery campaign

Use this path only when the core router selects post-closeout recovery mode.

1. Read the latest complete closeout and handoff, its Generation Reflection when one was required, authoritative final accounting, highest generation and applicable continuing grant or current request. A closed generation stays closed. Resolve any genuinely unfinished worker or claim branch before treating its closeout as complete.
2. Open the next generation under the current applicable parents, which may differ from the producing parents. Record the prior closeout, current bindings, inherited actual and unknown spend, applicable grant and planning consequence in the existing X/log. Create V only for a new user-owned decision; the Coordinator selects the technical objective.
3. Reference original results and reviews directly. Retain their producing bindings and original limits. Do not enumerate every historical artifact or every intervening generation to prove reuse. Apply [Change impact and retained results](frontier-core.md#change-impact-and-retained-results) only where the next use actually differs or contrary evidence exists.
4. For retained candidate material, use [Candidate recovery](candidate-lifecycle.md#post-closeout-recovery-reuse). Published unchanged material with an applicable positive review needs no new implementation review. An unpublished all-pass realization may complete its missing prepublication review against its original execution evidence; publication is not a prerequisite to that review. Incomplete material remains working material until the missing checks pass.
5. Use the prior Generation Reflection as candidate-generation input: carry forward its retained search assets, produce candidates from its worthwhile opportunities, apply its exploration/exploitation stance, and preserve any unselected material opportunity in the existing route-set deferral with its reconsideration signal. If it names a possible parent implication, add its cited adopted evidence—not the Reflection as a verdict—to the next ordinary evidence state. Then plan the next actual action through normal Entry with inherited accounting and run the integrated resolver once. The Reflection is advisory; only the resolver's existing row 4 can formally refer an affected rule to its parent owner. No second closeout resolver, extra research, or diagnosis follows merely from the Reflection. Use new identities only for new objects, retaining exact historical inputs for evidence. Entry or a missing review may be planned before all prerequisites for execution are ready; no execution, measurement or spend occurs before its applicable readiness and permission.

Recovery alone does not establish a performance claim, promote a candidate or revive ended permission.

## 2. Initialize the campaign

For generation 1, create only the canonical paths from `frontier-core.md`, append `FRONTIER_STARTED`, and initialize F1-F8, Budget, and E001. For post-closeout recovery, use the recovery procedure above and append within the existing canonical files. Record Entry planning and research cost separately when the governing accounting rule charges it.

Keep E001 as the current-epoch reference baseline. F1 must reproduce the exact reviewed scope. F2 must distinguish total budget, prior spend, reservations, actual spend, required follow-up reserve, and remaining balance. F7 and F8 must preserve every inherited stop, halt, reachability, comparison, and claim limit.

## 3. Build a decision-grade route landscape

First fix the current allocation decision, exact reviewed scope, parent objective and measurement meaning, repository and retained evidence, observed constraints and failures, permitted design freedoms, Budget horizon, and one bounded search-and-generation stop.

Treat established approaches, repository evidence, observed failures, functional transfer or recombination, migration or reorganization, new mechanism reasoning, and applicable prior-generation Reflection opportunities as peer route sources. No source must be exhausted before another can produce a provisional route, and external retrieval is not permission to reason. Before or while research runs, preserve provisional mechanism opportunities supported by bound evidence. They grant no Selection, B, or spend authority and create no new record type.

Apply [Scoped evidence reuse](learning-loop.md#scoped-evidence-reuse) and [Route-investment ordering](learning-loop.md#route-investment-ordering) to decide whether retained evidence, bounded research, or direct work best serves this commitment. Use an applicable adopted Q; a changed question requires reassessment, not automatic research. When research is selected, assign it to `research-frontier` with the decision, scope, comparison dimensions, evidence channels, repository evidence, action window, search stop, and existing evidence and result paths. The researcher owns [mechanism synthesis](../../research-frontier/SKILL.md#route-landscape-synthesis), not merely retrieval supporting a favored route. Treat relevant read-only external research as planning unless an exact parent or user rule prohibits that access. A restriction on execution, spend, remote side effects, publication, or claims does not make a read-only evidence channel inapplicable. Mark a channel inapplicable only when it cannot affect the decision, cannot be reached within the action window, or exact authority prohibits that access; cite the reason and preserve useful negative searches.

Check applicability, reconcile material conflicts with current evidence, and adopt the result as Q; reuse the researcher's synthesis rather than writing a second analysis. The Coordinator owns allocation, not a duplicate research report. Research may challenge, bound, merge, or defeat a provisional route; it does not approve, require, or select one. Stop when eligible routes and bounded exclusions suffice for the current allocation and further retrieval or synthesis is unlikely to change it. Preserve evidence-backed reasons and observable reopening events for material exclusions; apply [Opportunity-led reconsideration](learning-loop.md#opportunity-led-reconsideration) when new evidence changes that basis. This is decision completeness, not exhaustive coverage or proof of optimality. Reconcile charged Entry cost before planning B reservations.

## 4. Create eligible plans

Create a T for every materially different technically eligible route or campaign-baseline approach and apply the canonical [T eligibility contract](planning-records.md#t-route). Do not create a T merely to represent a source category, minor parameter variant, or ceremonial alternative.

Apply [Research hypotheses and action prerequisites](planning-records.md#research-hypotheses-and-action-prerequisites) to the proposed action before admitting its route use. An unresolved hypothesis may be tested through that path while work relying on its success remains ineligible.

For every iterative T, record a defensible prospective progress rule, mechanism checkpoint, or reachability condition before governed spend under [Informative checkpoints](planning-records.md#informative-checkpoints), or justify `not applicable`. Do not invent a number merely to complete the template.

Apply the canonical R8 vacuity definition to the first planned check. Current evidence that proves every legal result maps to the same allowed next action makes candidate or evaluation work ineligible. Unknown headroom, noise, resolution, representativeness, or proxy usefulness may instead select the smallest bounded prerequisite or diagnostic check when its possible results change the permitted next action.

Reject routes outside exact `Permitted` scope before user preference. Judge established and new routes by mechanism, eligibility, reachability, and discriminating evidence, not novelty or maturity alone. Do not invent expected improvement, probability, route scores, calendar estimates, originality claims, or tie-breaks.

When only one approach is technically eligible, the reconciled evidence and proposed Selection must disposition only the material decision-relevant mechanism classes considered, with evidence and a reopening event when one exists. Do not demand every imaginable approach. Create no fake alternative T and request no campaign-baseline tradeoff V. For a shared untested high-consequence assumption, identify which commitments rely on it and preserve a useful test when bounding it could change allocation. Its uncertainty does not veto an independent sufficient action selected by the canonical resolver; the action-prerequisite contract still restricts its dependents.

## 5. Resolve user-owned choices

Technical evidence determines eligibility. Use [User decisions](user-decisions.md): invoke `grill-frontier` only for a material value choice that existing preferences and evidence cannot settle, or a genuinely missing permission.

For a campaign-baseline choice, present at least two eligible starting points unless the evidence proves only one is eligible. Explain why each can support later optimization, what it costs to establish, when it should be replaced, and which evidence interfaces remain stable. Recommend one when evidence supports it; do not imply that the baseline must itself be the strongest eventual solution.

Adopt each new answer as V. Its stated scope can authorize continuing work; a mere preference does not. Never use an answer to waive measurement or prove a technical claim, and never ask again solely because the execution object changes.

<a id="select-the-first-work"></a>

## 6. Plan the first observable work

Create the first B from its sole template. Create W only when the work is complex, spans checkpoints, or needs a technical-design map. Do not create empty W or design-concern scaffolding to satisfy a form. For a module or system design, the Coordinator creates only the bounded W scaffold and invokes `design-implementation`; it does not author professional design content. A complex non-code W uses one reasoned `not applicable` Design-map row and no technical-design concern files. Every selected B must precommit:

- decision hypothesis;
- expected observation;
- decision rule for continue, diagnose, research, revise, promote, stop, or halt;
- exact first checkpoint and first performance check;
- preparation cost estimate, governing campaign limit and protected follow-up reserve;
- legality, engineering, measurement, and comparison-validity checks;
- recovery point, stop conditions, and prohibited actions.

List the legal result branches for the first check and their distinct allowed next actions. When the check answers an unknown measurement property, stop at that observation and preserve its decision and claim boundary. When a materialized candidate uses the diagnostic-only exception in `candidate-lifecycle.md`, plan a separate non-code experiment B and keep formal Slot H measurement, E, integration, incumbent use, promotion, and strength claims closed.

Also record `Trajectory contribution` before execution. For prerequisite-first work, bind the output and stop boundary to the prerequisite observation and make dependent implementation explicitly ineligible until the Coordinator adopts passing evidence through the applicable Entry or Replan gate.

The plan separates worker write surfaces from exact project bytes selected later for checks or Consequences. It does not assign execution snapshots, execution-start paths or result identities. For W-backed work, cite the reviewed design and stable delivery obligations; do not freeze the whole W or mutable work breakdown. Apply [Batch continuation](batch-current.md#boundary-preserving-continuation) to distinguish working methods from the independently judged result.

Use [Entry review](entry-review.md) only after ordinary structural checks pass and the complete subject is saved in Git. A failed draft stays mutable within the same B and creates no R, packet, snapshot, identity, or successor B. The reviewed decision must cover the objective, scope, applicable R and V, governing campaign limits, protected reserve, strategic allocation, any interpretation-bearing Measurement Definition ceiling, delivery obligations, earliest useful check, result meaning, and recovery needed by the next Consequence. A planning estimate and exact Batch operational cap do not become frozen review semantics.

Preparation must end at the earliest check that can discriminate the chosen mechanism. A baseline-establishment slice may be simple, but it cannot become open-ended infrastructure work.

If the B may change executable candidate code, complete `entry-code-planning.md` before selection. A design, research, or isolated prototype B must explicitly state `changes_executable_candidate: false`; it authorizes no candidate code.

For `human_input`, record the exact request, response path, schema, provenance, quality and legality checks, confidentiality handling, accept or reject conditions, resume event, and evidence-only limit in B or its required W before selection. Supplied data cannot stand in for a technical verdict or V.

## 7. Select reproducibly

Apply exact R8 route, eligibility, priority, uncertainty, measurement-use, vacuity, promotion, confirmation, parallelism, and fallback clauses. If R8 is silent or ambiguous about a required rule and does not delegate it, record `PARENT_REVIEW_REQUIRED` and use the finalization section below.

Technically filter first, then apply adopted V records. Propose one Primary B and only demonstrably independent Parallel B records. Record the exact proposed Selection and Budget transition, separate budgets, mutable paths, stable shared resources, failure isolation, and one join point. Do not adopt a reservation or executable Selection before the applicable readiness review and applicable user permission.

Include the proposed Selection and F2-F4 patch in the reviewed target. Record the route set as `complete for this decision` or `incomplete`, cite the peer-source generation basis, prior-generation Reflection when applicable, shared assumptions, eligible routes, exclusions, deferrals, prerequisite consequences, and reopening evidence, and explain how the selected work reaches the first discriminating check. These labels describe the assessed scope, not a second chooser: apply the canonical resolver's order and the selected action's evidence and prerequisite requirements. An unrelated landscape gap cannot veto independent sufficient work; a real unresolved dependency still restricts its use. Preserve an inherited label's wider historical scope and explain any narrower current use here, without relabeling history or creating a clearance record. Explain why the chosen campaign baseline is useful for later optimization and how every material alternative is dispositioned.

## 8. Record the Entry decision

Write a plain-language Brief in `FRONTIER.md` that a fresh reader can use without following identifiers. It must name the reference baseline, replaceable campaign baseline, exact allowed work, remaining governing budget, selected B and W, first checkpoint, first performance check, preparation cost estimate, protected reserve, comparison and promotion rules, stop and halt rules, and claim limits.

Pin F1-F4, F7, and F8. F5 and F6 may remain provisional or not relevant when the parents provide no usable bound; missing bounds never widen F7 or F8. Confirm new-generation B spend is zero, inherited spend is exact, and every charged Entry cost is already accounted.

## 9. Review the Entry decision

Load [Entry review](entry-review.md). Keep planning edits mutable until the complete version is ready, run ordinary deterministic checks, then save the exact subject in Git. Invoke `review-frontier` in a fresh context and record one R against that commit and path set. For a corrected Entry, supply the prior finding and saved version plus a short change explanation, and assign [Entry repair review](entry-review.md#entry-repair-review), not a restart of unaffected work. Supply no expected verdict or mandatory repair method.

Preserve every R at its saved Git version. Repair an `ENTRY_REPAIR_REQUIRED` draft, including deterministic defects, before submitting its corrected complete version for the scoped review above. A deterministic defect alone does not require a workflow-development task or another repair artifact. Obtain named evidence for an evidence-backed blocker and return parent conflicts upstream. When the Review identifies one missing user boundary, apply [User decisions](user-decisions.md), ask that question once and record V. An affirmative V permits only its stated Consequences and limits; a decline grants none. When an existing V applies, `ENTRY_READY` proceeds directly. Apply the reviewed Selection and Budget transition without creating an adoption artifact or authority identity.

Append `FIRST_BATCH_PLANNED` only after direct `ENTRY_READY` or exact post-answer adoption. Include campaign generation, applicable Review and V when needed, parents, selected B records, inherited and Entry-cost accounting, and zero-B-spend consequence. Do not execute the B. Historical Entries retain their original readiness snapshot and adoption chain; a current Entry does not create that chain.

## Record one outcome, then finalize the return

Record exactly one stage outcome:

- `FIRST_BATCH_PLANNED`: complete Entry, unchanged readiness authority and `ENTRY_READY` adoption, zero new-generation B spend, and reconciled inherited and Entry cost;
- `CLOSEOUT_REQUIRED`: a valid pre-spend stop or halt applies;
- `PARENT_REVIEW_REQUIRED`: parent authority or meaning is missing, stale, or ambiguous;
- `BLOCKED`: required authority, private facts, tools, data, or access are unavailable.

Return the recorded stage outcome to the Coordinator, which applies the requested completion boundary and existing router. This stage's no-execution boundary does not end a broader request; a planning-only request still stops before execution.

Entry is complete only when project records reconstruct campaign generation, Coordinator-derived objective when applicable, retained-result references, route generation, decision completeness, prerequisite dispositions, baseline choice, replacement boundary, inherited Budget, applicable Entry Review and V, selected work, earliest discriminating check, code gates and zero-B-spend boundary. Technical work proceeds without a separate exact-execution authorization when those owners already cover it.
