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

Match planning to the requested deliverable under the [Coordinator's scope and completion rule](../SKILL.md#recover-and-choose-the-current-action). Campaign-opening planning continues to its first applicable B decision or exact unresolved dependency; a completed design alone does not finish that request. Require only the design meaning the selected work depends on. Reuse existing plans and reviews; prepare Entry only for a decision that actually needs it. A design-only, advisory or local planning request may finish at its requested deliverable without creating a B or completing Entry.

## Load only what Entry reaches

Load [Campaign state](campaign-state.md) and [Planning records](planning-records.md). Load [Evidence records](evidence-records.md) in post-closeout recovery mode. Load [Worker interfaces](worker-interfaces.md) before delegating research, a user decision, Entry review, or any other worker action. Load [Current Batch](batch-current.md) before opening a selected B. If eligible work may change software, load [Entry code planning](entry-code-planning.md). When recovery proposes an existing historical candidate for measurement, load [Candidate lifecycle](candidate-lifecycle.md), [Review snapshots](review-snapshots.md), and [Implementation review](implementation-review.md). Load [Entry review](entry-review.md) only after the proposed Entry subject is complete.

## 1. Validate the handoff

Bind the exact Problem epoch, Representation revision, generation times, positive reviews, reference baseline, measurement identity, exact `Permitted` text, R1-R8, budget authority, and claim limits. Copy no broader meaning into Frontier records.

Refer a missing or conflicting requirement to its parent owner under [Change impact and retained results](frontier-core.md#change-impact-and-retained-results). Use `PARENT_REVIEW_REQUIRED` for the dependent action only if that repair cannot proceed within current permission.

### Adopt a parent revision

Use this path when the core router selects parent-revision mode. Apply [Change impact and retained results](frontier-core.md#change-impact-and-retained-results); prior spend does not select another path.

Use the parent owner's adopted revision to update the next affected decision in the existing X, Selection and campaign view. Preserve applicable B and W. Keep the generation for a local revision; apply [Research-basis transitions](frontier-core.md#research-basis-transitions) when shared premises materially change the research agenda, without reopening initial Entry or requiring zero B spend. Keep historical packets, reviews, execution inputs and charges unchanged. Reuse unaffected conclusions and permission; obtain only the missing or affected Entry, Replan or specialist review required by the changed decision.

A completed parent revision returns to the existing Campaign Cycle. It neither resets Entry accounting nor requires zero historical B spend or a replacement first batch.

### Open a post-closeout recovery campaign

Use this path only when the core router selects post-closeout recovery mode.

1. Read the latest complete closeout and handoff, its available research Reflections, authoritative final accounting, highest generation and applicable continuing grant or current request. A closed generation stays closed. Resolve any genuinely unfinished execution worker or claim branch before treating its closeout as complete; an unfinished non-gating Reflection does not prevent recovery.
2. Open the next generation under the current applicable parents, which may differ from the producing parents. Record the prior closeout, current bindings, inherited actual and unknown spend, applicable grant and planning consequence in the existing X/log. Create V only for a new user-owned decision; the Coordinator selects the technical objective.
3. Reference original results and reviews directly. Retain their producing bindings and original limits. Do not enumerate every historical artifact or every intervening generation to prove reuse. Apply [Change impact and retained results](frontier-core.md#change-impact-and-retained-results) only where the next use actually differs or contrary evidence exists.
4. For retained candidate material, use [Candidate recovery](candidate-lifecycle.md#post-closeout-recovery-reuse). Published unchanged material with an applicable positive review needs no new implementation review. An unpublished all-pass realization may complete its missing prepublication review against its original execution evidence; publication is not a prerequisite to that review. Incomplete material remains working material until the missing checks pass.
5. Supply relevant research Reflections together with original evidence, the current objective and open technical questions. Professional owners may extend, reject or replace their suggestions and search stance without approval. Use [Research Reflection](learning-loop.md#research-reflection) and [Technical potential](learning-loop.md#technical-potential), then continue the current research problem or resolve the next investment under Active learning chain. A possible parent implication is a hypothesis to assess, not a verdict; an affected parent rule returns to its existing owner. Recovery creates no mandatory research, repeated Reflection or review of unchanged work. Entry or a missing review may be planned before all execution prerequisites are ready; actual execution still needs its applicable readiness and permission.

Recovery alone does not establish a performance claim, promote a candidate or revive ended permission.

## 2. Initialize the campaign

For generation 1, create only the canonical paths from `frontier-core.md`, append `FRONTIER_STARTED`, and initialize F1-F8, Budget, and E001. For post-closeout recovery, use the recovery procedure above and append within the existing canonical files. Record Entry planning and research cost separately when the governing accounting rule charges it.

Keep E001 as the current-epoch reference baseline. F1 must reproduce the exact reviewed scope. F2 must distinguish total budget, prior spend, reservations, actual spend, required follow-up reserve, and remaining balance. F7 and F8 must preserve every inherited stop, halt, reachability, comparison, and claim limit.

## 3. Build a decision-grade route landscape

Establish the current allocation question, exact reviewed scope, parent objective and measurement meaning, repository and retained evidence, observed constraints and failures, permitted design freedoms, Budget horizon, and one bounded search-and-generation stop. When forming directions, phrase the research question around the objective gap; keep old candidates, historical ordering and proposed measurements as leads. Include active external discovery through [Route-landscape synthesis](../../research-frontier/SKILL.md#route-landscape-synthesis) in this professional work, reusing discovery already done for the decision. The lead may discover a different problem model or whole approach, not just fill known gaps. This adds no separate preflight, Q or approval. For a selected direction's local question, preserve the chosen scope instead of automatically reopening it.

Treat established approaches, repository evidence, observed failures, functional transfer or recombination, migration or reorganization, new mechanism reasoning, and relevant research Reflection as peer route sources. No source must be exhausted before another can produce a provisional route, and external retrieval is not permission to reason. Before or while research runs, preserve provisional mechanism opportunities supported by bound evidence. They grant no Selection, B, or spend authority and create no new record type.

Apply [Scoped evidence reuse](learning-loop.md#scoped-evidence-reuse) and [Route-investment ordering](learning-loop.md#route-investment-ordering) to decide whether retained evidence, bounded research, or direct work best serves this commitment. Use an applicable adopted Q; a changed question requires reassessment, not automatic research. When research is selected, assign the open problem to `research-frontier` through the [Research packet](worker-interfaces.md#research-packet). Its professional lead owns early [Multidisciplinary research](worker-interfaces.md#multidisciplinary-research) and the synthesis connecting proposed changes to the real objective. The Coordinator supplies source references and actual limits, not a preferred answer or a fixed disciplinary breakdown. Treat relevant read-only external research as planning under [Evidence access](worker-interfaces.md#evidence-access). Restrictions on execution, spend, publication or claims do not by themselves exclude a reading channel. Select channels by relevance to the open problem and discovery potential, not a known answer or source-category quota; retain useful negative searches and actual access limits.

Check applicability, reconcile material conflicts with current evidence, and adopt the result as Q with its professional recommendation, objective reasoning and uncertainty intact. Return a concrete omitted source, erroneous premise, missing objective link or unequal comparison to the original author for local correction; a clearly identified untested inference or disagreement alone is not a defect. Preserve adopted history and correct affected use through existing records. Reuse the synthesis in [Route-investment ordering](learning-loop.md#route-investment-ordering): the resolver decides the pending investment and the Coordinator adopts and advances it, without a third ranking or repeated research. Stop when technical judgments and scoped exclusions suffice for the current allocation and further investigation is unlikely to change it. Preserve the reasons and conditions that could reopen material exclusions, including new mechanism or theoretical analysis under [Opportunity-led reconsideration](learning-loop.md#opportunity-led-reconsideration). This is decision completeness, not exhaustive coverage or proof of optimality. Reconcile charged Entry cost before planning B reservations.

## 4. Create eligible plans

Create a T for every materially different technically eligible route or campaign-baseline approach and apply the canonical [T eligibility contract](planning-records.md#t-route). Do not create a T merely to represent a source category, minor parameter variant, or ceremonial alternative.

Apply [Research hypotheses and action prerequisites](planning-records.md#research-hypotheses-and-action-prerequisites) to the proposed action before admitting its route use. An unresolved hypothesis may be tested through that path while work relying on its success remains ineligible.

For every iterative T, record a defensible prospective progress rule, mechanism checkpoint, or reachability condition before governed spend under [Informative checkpoints](planning-records.md#informative-checkpoints), or justify `not applicable`. Do not invent a number merely to complete the template.

Apply the canonical R8 vacuity definition to the first planned check. Current evidence that proves every legal result maps to the same allowed next action makes candidate or evaluation work ineligible. Unknown headroom, noise, resolution, representativeness, or proxy usefulness may instead select the smallest bounded prerequisite or diagnostic check when its possible results change the permitted next action.

Reject routes outside exact `Permitted` scope before user preference. Judge established and new routes by mechanism, eligibility, reachability, and discriminating evidence, not novelty or maturity alone. Do not invent expected improvement, probability, route scores, calendar estimates, originality claims, or tie-breaks.

When only one approach is technically eligible, the reconciled evidence and proposed Selection must disposition only the material decision-relevant mechanism classes considered, with evidence and a reopening event when one exists. Do not demand every imaginable approach. Create no fake alternative T and request no campaign-baseline tradeoff V. For a shared untested high-consequence assumption, identify which commitments rely on it and preserve a useful test when bounding it could change allocation. Its uncertainty does not veto independent sufficient work selected through the applicable continuation or investment path; the action-prerequisite contract still restricts its dependents.

## 5. Resolve user-owned choices

Technical evidence determines eligibility. Use [User decisions](user-decisions.md): invoke `grill-frontier` only for a material value choice that existing preferences and evidence cannot settle, or a genuinely missing permission.

For a campaign-baseline choice, present at least two eligible starting points unless the evidence proves only one is eligible. Explain why each can support later optimization, what it costs to establish, when it should be replaced, and which evidence interfaces remain stable. Recommend one when evidence supports it; do not imply that the baseline must itself be the strongest eventual solution.

Adopt each new answer as V. Its stated scope can authorize continuing work; a mere preference does not. Never use an answer to waive measurement or prove a technical claim, and never ask again solely because the execution object changes.

<a id="select-the-first-work"></a>

## 6. Plan the first observable work

Create the first B from its sole template with the current question or deliverable, selection rationale, scope, relevant sources, actual limits and the result needed to judge its work. Use [Active learning chain](learning-loop.md#active-learning-chain) to order preparation and [Informative checkpoints](planning-records.md#informative-checkpoints) to choose checks at the research commitment's scale. Include result branches, recovery and protected follow-up resources only where they affect this work's actual use or effects; a performance check or distinct next action for every internal step is not required.

Use [Technical design](technical-design.md#choose-the-profile) to decide professional involvement and whether W is needed. Ordinary development progress uses the existing working plan. A query, preparation or implementation that does not depend on an unresolved design can establish or continue its own applicable B scope before the whole W is ready, using the existing Selection and Batch interfaces. This creates no preliminary stage or mandatory B per query.

Apply [Research hypotheses and action prerequisites](planning-records.md#research-hypotheses-and-action-prerequisites) when preparation settles a dependency. Preserve the observation's evidence ceiling and continue when the selected condition is met. When the retained historical-candidate diagnostic exception actually applies, use its separate experiment B and consequence limits.

The plan separates worker write surfaces from exact project bytes selected later for checks or Consequences. It does not assign execution snapshots, execution-start paths or result identities. Work depending on W cites its adopted relevant design and delivery obligations, with a review only when required for that use. Independent preparation does not inherit the whole W's readiness. Apply [Batch continuation](batch-current.md#boundary-preserving-continuation) to distinguish working methods from the independently judged result.

Use [Entry review](entry-review.md) only after ordinary structural checks pass and the complete subject is saved in Git. A failed draft stays mutable within the same B and creates no R, packet, snapshot, identity, or successor B. The reviewed decision must cover the objective, scope, applicable R and V, governing campaign limits, protected reserve, strategic allocation, any interpretation-bearing Measurement Definition ceiling, delivery obligations, earliest useful check, result meaning, and recovery needed by the next Consequence. A planning estimate and exact Batch operational cap do not become frozen review semantics.

Keep preparation tied to the selected useful result under [Reuse working knowledge](batch-current.md#reuse-working-knowledge). Expand support only for a concrete need of that use.

If the B may change executable candidate code, complete `entry-code-planning.md` before selection. A design, research, or isolated prototype B must explicitly state `changes_executable_candidate: false`; it authorizes no candidate code.

For `human_input`, record the exact request, response path, schema, provenance, quality and legality checks, confidentiality handling, accept or reject conditions, resume event, and evidence-only limit in B or its required W before selection. Supplied data cannot stand in for a technical verdict or V.

## 7. Select reproducibly

Apply exact R8 route, eligibility, priority, uncertainty, measurement-use, vacuity, promotion, confirmation, parallelism, and fallback clauses. If R8 is silent or ambiguous about a required rule and does not delegate it, record `PARENT_REVIEW_REQUIRED` and use the finalization section below.

Technically filter first, then apply adopted V records. Propose one Primary B and only demonstrably independent Parallel B records. Record the exact proposed Selection and Budget transition, separate budgets, mutable paths, stable shared resources, failure isolation, and one join point. Do not adopt a reservation or executable Selection before the applicable readiness review and applicable user permission.

Include the proposed Selection and affected F2-F4 update in the reviewed target. For a new investment, cite its professional resolution and the relevant route evidence. For continuation, cite the current research scope and rationale, applicable evidence and next observation without a new resolution or a repeated route inventory. Review the actual action's prerequisites, resources and consequences; an unrelated landscape gap cannot veto independent sufficient work. Preserve historical judgments at their original scope.

## 8. Record the Entry decision

Update only affected explanations in the [FRONTIER Brief](campaign-state.md#frontiermd-and-f1-f8). Keep current question, missing observation, ongoing work and source pointers there; budgets, permissions and execution state remain with their owners.

Pin F1-F4, F7, and F8. F5 and F6 may remain provisional or not relevant when the parents provide no usable bound; missing bounds never widen F7 or F8. Confirm new-generation B spend is zero, inherited spend is exact, and every charged Entry cost is already accounted.

## 9. Review the Entry decision

Use [Entry review](entry-review.md) to decide whether the next actual Consequence needs independent Entry judgment. If it applies, keep planning edits mutable until the complete version is ready, run ordinary deterministic checks, save the exact subject in Git, and invoke `review-frontier` once in a fresh context. For a corrected Entry, supply the prior finding and saved version plus a short change explanation, and assign [Entry repair review](entry-review.md#entry-repair-review), not a restart of unaffected work. Supply no expected verdict or mandatory repair method.

If Entry Review does not apply, record that fact in the existing Entry decision and create no R or substitute verdict. A first B, measurement label, new candidate, or repeatable public local observation does not by itself require independent Entry judgment.

Preserve every R at its saved Git version. Repair an `ENTRY_REPAIR_REQUIRED` draft, including deterministic defects, before submitting its corrected complete version for the scoped review above. A deterministic defect alone does not require a workflow-development task or another repair artifact. Obtain named evidence for an evidence-backed blocker and return parent conflicts upstream. When the Review identifies one missing user boundary, apply [User decisions](user-decisions.md), ask that question once and record V. An affirmative V permits only its stated Consequences and limits; a decline grants none. When an existing V applies, `ENTRY_READY` proceeds directly. Apply the reviewed Selection and Budget transition without creating an adoption artifact or authority identity.

Append `FIRST_BATCH_PLANNED` after applicable `ENTRY_READY` or after recording that no Entry Review applies. Include campaign generation, applicable Review and V when needed, parents, selected B records, inherited and Entry-cost accounting, and zero-B-spend consequence. Do not execute the B inside this planning stage. Historical Entries retain their original readiness snapshot and adoption chain; a current Entry does not create that chain.

## Record one outcome, then finalize the return

Record exactly one stage outcome:

- `FIRST_BATCH_PLANNED`: complete Entry, applicable `ENTRY_READY` adoption or no applicable Entry Review, zero new-generation B spend, and reconciled inherited and Entry cost;
- `CLOSEOUT_REQUIRED`: a valid pre-spend stop or halt applies;
- `PARENT_REVIEW_REQUIRED`: parent authority or meaning is missing, stale, or ambiguous;
- `BLOCKED`: required authority, private facts, tools, data, or access are unavailable.

Return the recorded stage outcome to the Coordinator, which applies the requested completion boundary and existing router. This stage's no-execution boundary does not end a broader request; a planning-only request still stops before execution.

Entry is complete only when project records reconstruct campaign generation, Coordinator-derived objective when applicable, retained-result references, route generation, decision completeness, prerequisite dispositions, baseline choice, replacement boundary, inherited Budget, applicable Entry Review or its non-applicability, applicable V, selected work, earliest discriminating check, code gates and zero-B-spend boundary. Technical work proceeds without a separate exact-execution authorization when those owners already cover it.
