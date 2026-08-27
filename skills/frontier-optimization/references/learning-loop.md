# Frontier Learning Loop

## Contents

- [Evidence consequence levels](#evidence-consequence-levels)
- [Active learning chain](#active-learning-chain)
- [Evidence use](#evidence-use)
- [Hypothesis and mechanism interpretation](#hypothesis-and-mechanism-interpretation)
- [Integrated direction resolver](#integrated-direction-resolver)
- [Historical compatibility](#historical-compatibility)

Load after result adoption when the campaign needs another decision, or when a strategic replan is pending. This file owns the one integrated direction resolver. Generation Reflection belongs only to full closeout.

## Evidence consequence levels

- **Routine:** valid expected evidence resolves the addressed decision inside the unchanged route, measurement meaning, material allocation, stop rule, and claim limit. Retaining or replacing an incumbent under an already adopted comparison and retention rule may be routine; the word `baseline` does not decide the level. Apply R8 without extra diagnosis.
- **Diagnostic:** surprising, failed, ambiguous, validity-limited, or decision-limiting measurement evidence may justify a direct attempt, local check, focused Q, isolated prototype, or authorized diagnostic-only observation. Compare next investments under the single resolver below; no unique-dominance requirement applies.
- **Strategic:** evidence supports crossing a reviewed route or material-allocation boundary, or changing budget policy, a stop rule, irreversible behavior, or a claim limit. A comparator, reference, or incumbent change is strategic only when its actual consequence crosses one of those boundaries. Measurement-meaning and design changes use their owning specialized gates; add Replan only when the same change is also strategic. Dependent strategic spend needs sufficient evidence, any applicable V, and adopted fresh-context replan review.

## Active learning chain

Treat `completed`, `interrupted`, `failed`, and `blocked` as terminal B outcomes after Coordinator validation. `waiting_for_input` is a paused attempt. After a terminal result and every eligible E are adopted:

1. Reconcile the result packet, W state, artifacts, spend, reservations, recovery, E, and X. Preserve negative, failed, ambiguous, and invalid evidence.
2. Establish validity in this order: implementation, measurement, then comparison validity. Stop inference at the first unresolved layer.
3. Build one current evidence-state identity from adopted project facts.
4. Apply the integrated resolver exactly once and persist its first applicable row in Selection.
5. Complete only the Q, V, join, Replan, or specialized gate selected by that row. A new decision-relevant fact creates a new evidence state and one new resolver run.

This chain creates no intermediate interpretation stage, Outcome Reflection, coverage record, review, or authority. The resolver reads adopted B, E, Q, X, T, W, D, V, R8, Budget, parent, validity, and gate facts directly. For a safe parallel set, wait for every selected member's terminal outcome and one joined X before dependent allocation. Same-B working observations and fidelity repairs remain inside [Boundary-preserving continuation](batch-interface.md#boundary-preserving-continuation) and do not run the resolver after each observation.

Research or diagnosis is justified only when its answer can change eligibility, route, allocation, stopping, promotion, or claim limit. A direct reversible attempt may be preferable to separate diagnosis. Apply routine R8 without extra research when no earlier resolver condition applies. Use specialized gates in addition to replan review: changed design needs design review and authorization; changed candidate needs implementation review; changed claim needs claim review; parent-scope conflict needs parent review.

## Evidence use

Use adopted evidence; do not rerun the candidate, evaluator, engineering checks, repository tests, or workflow tests. Do not create a snapshot or review merely to decide what valid existing evidence means.

Read the smallest complete evidence chain in this order:

1. **Current technical decision:** read the terminal B's `Decision hypothesis`, `Expected observation`, result, terminal outcome, related E, parent metrics, guardrails, and technical decision boundary.
2. **Originating mechanism:** when B evaluates, confirms, or reuses an executable candidate, follow the exact candidate identity to the originating T or W, the design or implementation B that changed behavior, the executable-difference description or source manifest, the adopted implementation review, and the engineering or behavior evidence. Use identity-bound lineage rather than topic similarity. For a reference measurement, administrative B, or work with no technical mechanism, record `not-applicable` instead of inventing one.
3. **Comparison meaning:** read the adopted evaluator, protocol, comparator, workload or data scope, uncertainty, and result direction from E and its result. Add prior E only when the comparability rule below permits the exact interpretation being made. Read lower-level measurement artifacts only when the adopted result does not already establish a decision-relevant property; never repeat the measurement.
4. **Decision meaning:** read the applicable replacement boundary, disqualifying evidence, known limits, and only those traces, route alternatives, or design surfaces already supported by persisted evidence. Budget, authority, R8, and gate records constrain the action; they do not change what the evidence observed.

Synthesize that chain rather than summarizing each record:

1. Keep the current B decision and the originating technical mechanism as separate layers. Judge the B hypothesis from its expected and observed result; use the complete lineage only for the supported mechanism grain.
2. Connect the evidence explicitly: what behavior-bearing difference was introduced, what implementation evidence shows that its pathways exist, and what valid outcome evidence supports at whole-package level.
3. Name component activity, necessity, dominance, mediation, or numerical contribution only at the grain supported by separating evidence. Otherwise keep the package conclusion and state the attribution limit.
4. Identify the defect, assumption, or local question that the evidence resolves. Do not keep a supported issue open merely because its internal contributions were not decomposed.
5. Admit a new conjecture only when it is grounded in observed evidence and can change the current allocation; label it untested.
6. State whether the measurement remains fit for the next concrete decision. A completed decision stays complete even when its comparator would be too coarse for a future successor decision.
7. Use the strongest bounded conclusion supported by the evidence rather than a gate label such as `admit`, `reject`, or `completed`.

Evidence use is complete when the resolver can distinguish what was observed, what remains unresolved, which actions remain technically live, and which inference limits apply without creating a separate narrative artifact.

## Hypothesis and mechanism interpretation

Judge the precommitted technical question as:

- `supported` when valid evidence matches the predicted observable effect within the named scope;
- `contradicted` when valid evidence violates it;
- `inconclusive` when validity, resolution, or coverage cannot answer it; and
- `not-applicable` for work with no technical hypothesis.

Support is scoped evidence, not universal proof. For a terminal B, recover the controlling decision hypothesis from that B. When the B evaluates, confirms, or reuses an existing candidate, recover the originating mechanism through its exact candidate, T or W, design or implementation B, and adopted implementation evidence; this mechanism context cannot replace the B-level decision. Preserve both layers, the expected observation, contradiction, and decision boundary. Implementation-only evidence may support implementation of the pathway but cannot support its performance effect. A valid whole-treatment comparison may support that the bounded package caused the observed local effect when the treatment is the only executable difference and evaluator, protocol, and comparison integrity remain fixed.

A candidate that violates an adopted design constraint directly establishes that candidate's nonconformance; the possibility that the design may also be wrong does not invalidate the design. Record a design consequence only when valid evidence under the same relevant conditions is incompatible with a named feasibility rationale that supported `DESIGN_READY`. The evidence need not have been produced specifically to test the design.

When several explanations remain, record a missing distinguishing observation only if those explanations lead to different next concrete actions. Otherwise keep the ambiguity as an attribution limit or non-blocking note. Ambiguity alone creates no diagnosis, research, review, blocker, or spend; apply the single integrated resolver to the persisted evidence.

Infer mechanisms at the strongest supported grain:

- **Whole package:** a valid controlled comparison plus exact executable differences can support the package-level causal effect without ablation.
- **Component present:** source and behavior evidence can show that a component pathway exists and behaves as designed.
- **Component contribution:** necessity, dominance, mediation, or numerical contribution needs a separating intervention, ablation, trace, or equivalent evidence.

An unexplained component contribution limits attribution but does not invalidate a valid package-level result or block another bounded reversible attempt. Diagnose it only when the pending decision depends on choosing among those internal explanations. A new conjecture may be grounded in observations, known limits, or mechanism reasoning; label it untested, explain why it could matter and what observation could refute it. Evidence supports the reason to test, not the conjecture's truth. A conjecture grants no research, reuse, incumbent, or spend authority.

Interpret progress only when cross-B history can change the decision. Combine only E with compatible parent objective, measurement meaning, comparator role, protocol, workload, data scope, uncertainty, validity, and result direction, or an explicit equivalence argument. Apply the complete parent-owned vector. A single departure is not persistence; movement within noise or resolution is not a plateau; a bounded plateau or underperformance finding needs a prospective rule. A proxy cannot establish route progress while a required metric, hard constraint, guardrail, segment, tail, delayed confirmation, or operating-cost boundary fails or remains unresolved.

Use Constraint inference only when it affects the decision. `suspected` identifies a plausible limiting factor without system-level effect evidence. `demonstrated` needs an intervention or discriminating test showing that changing the factor changes the parent objective under the named conditions. `shifted` needs evidence that the intervention changed which factor limits that objective. Local difficulty, eliminated alternatives, or movement in a proxy does not establish a bottleneck.

Use a measurement limitation only when it changes a concrete decision. Distinguish a saturated comparator-derived score from exhaustion of the evaluator itself. A limitation that does not prevent the addressed decision remains a future-use note; it creates no protocol-repair requirement. If the limitation prevents the current decision, keep the evidence inconclusive and let the resolver compare a direct candidate attempt, direct incumbent comparison, protocol adjustment, diagnosis, research, or stop by decision information and cost.

Selection records the resolver's evidence-bound decision, diagnostic ordering, first applicable row, affected scope, surviving authority, and exact next action. R8, Budget, Replan, and specialized gates are inputs to that one resolver, not later override systems.

## Integrated direction resolver

This section is the only direction resolver. `frontier-core.md` owns the recorded-state router and the existing stop, halt, parent, and closeout actions to which rows below refer; it does not own a second direction table. `campaign-cycle.md`, `campaign-state.md`, Entry review, Replan review, and later-spend checks cite this section and never restate or reorder it.

### Opportunity-led reconsideration

New adopted evidence or a mechanism argument grounded in current project evidence can reopen a within-parent-scope route comparison when it could change allocation. Examples include newly reachable representations, transferable capabilities, or narrowing headroom in the current method. Record the basis in the existing Q, Entry route evidence, prior-generation Reflection, or current route-set state. An incumbent need not fail first. Mere novelty or another conceivable option does not require a refresh.

Use row 7 when that opportunity leaves the landscape incomplete, row 8 for a missing deciding fact, or rows 10–12 when existing evidence already supports an action subject to their gates. These remain conditions inside the single resolver, not an extra chooser; earlier validity and authority conditions still apply. Routine evidence with no such change stays on row 13. For opportunities outside parent scope, use [Opportunity proposals](frontier-core.md#opportunity-proposals) rather than treating a suggestion as a parent defect.

### Resolver inputs and Budget precheck

Reconstruct one immutable evidence-state identity from the current project decision root, parents and handoff, hard authority facts, adopted terminal outcomes and E dispositions, joins, route set and reopening events, Q and V records, T replacement and checkpoint boundaries, R8, Budget and protected reserve, decision-critical context and action window, and every specialized gate. A prior-generation Reflection may supply opportunity proposals to Entry, but it is not a validity or authority source. Conversation, workflow implementation bytes, a release change, or a preferred answer is not an input.

Every stop consequence has one exact scope. A `candidate` stop closes one immutable candidate, its dependent use, and its consumed B authority while preserving the unchanged route, W design, unused Budget, and open-campaign planning scope. A `route` stop closes one exact T or route allocation while preserving explicitly named surviving routes and authority. A `campaign` stop ends all campaign spend authority and enters full closeout. Select the smallest scope established by the evidence and precommitted R8 rule. A review verdict does not supply scope by its label: map its findings, affected identities, and maximum supported consequence through R8. Map `IMPLEMENTATION_REPAIR_REQUIRED` to candidate scope when the findings establish only that the exact formally published candidate fails its unchanged design and leave the route, design contract, allocation, and parent authority usable. Its behavior-bearing repair requires a new code-bearing B, candidate identity, development authorization, and the proposal charge defined by the parent, but does not increment the campaign generation while that campaign remains open. A pre-publication engineering-check failure has not entered this resolver path when [Boundary-preserving continuation](batch-interface.md#boundary-preserving-continuation) still permits same-B fidelity repair. A missing or conflicting scope is an owning-contract blocker, not a campaign stop.

Before applying row 5, identify the next decision-relevant observation for each still-live unresolved condition under [Informative checkpoints](planning-records.md#informative-checkpoints). It is sufficient when its possible results can change the next allocation, falsify a live explanation, tighten a relevant bound, or determine whether a larger test is warranted; it need not settle the entire research question. Record considered alternatives, what they distinguish, result-to-action branches, governed cost, opportunity cost, latency, dependencies, authority, action window, Budget and reserve effect, and reachability in existing Entry or Selection fields. Fund the next observation plus unavoidable follow-on commitments and safe stopping or recovery. Unknown downstream optional research cost does not block this stage; unknown cost of the authorized stage or unavoidable commitments does.

Honor any explicit R8 ordering and exclude dominated or unreachable alternatives. Unique dominance is sufficient, not necessary, for a technical choice. When non-dominated alternatives remain, the Coordinator records a justified ordering in the existing operational diagnostic fields using the available technical evidence: objective upside, ability to distinguish live explanations, full cost and opportunity cost. Explain why the selected observation is the best next investment and when to switch. Do not invent a score, ask for a new analyst on every tie, or turn technical discretion into a missing-rule blocker. When eligible options are indistinguishable on those dimensions, record that fact and a stable operational order, without claiming technical superiority. Ask the user only for a genuine unresolved value, resource, or authority choice. Selection consumes this recorded decision; it does not invent a second ranking.

Do not ask the user to choose a technical diagnostic. The same diagnostic class cannot repeat from the same evidence-state identity after failing to reduce the uncertainty that separates the live actions. New evidence may make it eligible again only when Selection states how that evidence changes its expected decisiveness.

### Single total order

Apply the rows from 1 through 13 exactly once. The first applicable row governs; no later row may override it.

| Priority | Persisted condition | Deterministic resolution |
|---|---|---|
| 1 | An unresolved parent requirement or adopted revision affects the next decision | Apply [Change impact and retained results](frontier-core.md#change-impact-and-retained-results): refer the affected rule to its owner or update that decision under the current adopted parents. Pause only dependent work; a version difference or prior spend alone neither triggers this row nor forces closeout. |
| 2 | An independently established safety, legality, authority, accounting, explicit campaign-scope unconditional F7 stop, or halt blocks work | Use the existing stop, halt, accounting-resolution, or full-closeout route. Candidate- and route-scope dispositions continue to their later resolver row. Evidence whose validity is disputed cannot establish an evidence-dependent stop in this row. |
| 3 | A selected terminal B has not been adopted; an eligible E lacks disposition; identities conflict; a required join is missing; an owning contract cannot be reconstructed; or a required cross-B interpretation cites incompatible evidence | Return the exact adoption, identity, join, contract, or compatibility blocker. No later spend exists. Missing per-B Reflection is not a blocker. |
| 4 | Current adopted evidence has resolved implementation, measurement, and comparison validity; it establishes that an unchanged parent-owned objective, Representation, Slot H measurement meaning, R8 rule, permitted scope, or claim ceiling is no longer suitable or reachable; and no unresolved execution-level explanation can account for that conclusion | Refer the affected rule to its owner under [Change impact and retained results](frontier-core.md#change-impact-and-retained-results). Pause dependent allocation, preserving unrelated permitted work and historical evidence. An unresolved, unaffordable, or unavailable diagnostic is not evidence of a parent defect. |
| 5 | No sufficient next observation or required check can be funded, including its unavoidable commitments and safe stopping or recovery, by current authorized Budget without consuming protected reserve | Select no B or spend-bearing Q. If T and R8 uniquely require an in-authority campaign stop, use the existing stop and full-closeout route. If they require a strategic allocation change for which authority could be sought, prepare it without spend and obtain `REPLAN_READY` plus any required V. Otherwise return the exact Budget or reserve blocker. Unknown cost of this stage or its unavoidable commitments is not affordable; optional later research need not be fully priced. |
| 6 | Implementation, measurement, or comparison validity, including required adaptive-exposure interpretation or confirmation, is unresolved and at least one sufficient diagnostic passes row 5 | Select the recorded diagnostic using the ordering above. Non-dominated alternatives do not themselves block. Make no trajectory, route, or parent inference while validity remains unresolved. |
| 7 | The plausible route set is incomplete, including an opportunity-led reopening; a shared high-consequence assumption or action prerequisite remains unbounded; or a technical exclusion has reached its reopening event; and the bounded work passes row 5 | Select one route-landscape Q or a sufficient bounded check with a fixed decision, evidence channels, action window, and search stop. Apply the T action-prerequisite rule: testing an unknown is eligible when the test itself is ready; work relying on its success is not. A current-route stop or warning does not preserve a stale exclusion. |
| 8 | The route set is complete, but one named external or repository fact is needed to decide among live routes or explanations, can arrive while the action remains available, cannot be answered by a less costly local observation, and passes row 5 | Select one focused Q bound to that decision and fixed search stop. |
| 9 | The route set is complete and a valid warning or prospective underperformance has more than one live causal explanation that an authorized local check can distinguish, and at least one sufficient path passes row 5 | Select the recorded local diagnostic using the ordering above. Do not infer route exhaustion, alter the parent frame, or repeat a dominated diagnostic. |
| 10 | A route decision requires an empirical probe, prototype, experiment, human-input B, external action, or other spend outside the unchanged reviewed route allocation, while total authority and protected reserve could support a reviewed reallocation | Prepare the exact strategic proposal and obtain unchanged adopted `REPLAN_READY` before that B. This row reallocates available authority; it does not create Budget. |
| 11 | Existing valid evidence and R8, including a prospective progress rule, already determine a candidate or route disposition, route, baseline, material allocation, evidence-dependent scoped stop, stop policy, design profile, irreversible behavior, measurement meaning, or claim-limit change | For candidate scope, close the exact candidate, dependent use, and consumed B authority, preserve named surviving planning authority, and select an in-allocation repair B only when R8 permits it, the technical ordering above records it, row 5 funds it, and its normal Entry, development-authorization, and fresh-candidate gates can be satisfied. For route scope, close the exact route and apply R8 plus the technical ordering above to the surviving route set; select the recorded action or return an exact blocker only when a fact needed to decide or execute remains missing. For campaign scope, use the existing stop and full-closeout route. For a strategic change, prepare the exact proposal and obtain unchanged adopted `REPLAN_READY`. Preserve every specialized or parent gate that also applies. |
| 12 | The proposed action crosses another recorded B, T replacement boundary, checkpoint, integration, promotion, evaluator-exposure, confirmation, exposure, or claim boundary | Require that boundary's named evidence and owning existing gate. Missing evidence selects its exact Q, diagnostic, review, V, or blocker; satisfied evidence does not waive the gate. Budget and reserve were already resolved at row 5. |
| 13 | No route, progress, Budget, parent, context, or decision-window condition above applies | Apply the unique local R8 action inside the unchanged route after confirming its B passes row 5. Perform no additional research, diagnosis, or review. |

If an applicable row still lacks its required result, including a justified operational order when that row delegates a technical choice, return the exact missing evidence, Q, V, R8 rule, stop scope, authority, Budget fact, action-window fact, or specialized gate as the blocker. `Direction resolution` records this row, its condition, affected scope, surviving authority, and exact next action. Resolve an evidence-state identity once, persist that result in Selection, and reject a second competing result for the same identity. Keep this resolution as history. If its next action is still applicable, reuse it. If current rules remove an obsolete procedural blocker or an adopted parent change affects the next decision, record that actual decision change through the existing X/Selection and resolve the new evidence-state once under current rules. Do not create events for updates with no decision effect.

### Research before a formal direction choice

A formal direction choice may receive one additional evidence-completion round only through row 7 or row 8. The Q starts from current adopted results, then reconciles applicable industrial implementations, academic evidence, community reports or artifacts, repository evidence, retained results, observed failures, prior-generation Reflection opportunities, and mechanism reasoning. These are peer evidence channels, not voting groups or mandatory quotas. Record provenance, operating conditions, conflicts, negative evidence, transfer limits, and whether a community result is reproducible or only a lead.

The research target must name the allocation or explanation decision it can change, materially different possible findings and their different recorded actions, why a cheaper local observation cannot answer it, the latest useful return point, assigned evidence channels, and a fixed search stop. Information is sufficient when the route set is complete for the current decision and further retrieval is unlikely to change the current allocation under the available Budget, authority, and action window. It does not mean exhaustive literature or community coverage, proof of originality, or certainty that no better route exists.

After Q adoption, rerun this same resolver on the new evidence-state identity. When the resolver records a determined direction, including a justified ordering among eligible non-dominated actions, proceed through the applicable Replan or specialized gate. If material uncertainty still prevents a decision and no affordable decision-changing source exists, return the exact blocker or stop consequence rather than commissioning open-ended research.

## Historical compatibility

Keep every earlier Outcome Reflection immutable under the project evidence and workflow that produced it. It remains usable within its original evidence boundary, but current active generations require no new per-B OR and no OR coverage migration. A closeout `reflect-frontier` assignment may cite supported conclusions from legacy OR records alongside later adopted evidence without rewriting either source.

Entry adoption fixes the producing project decision root and historical chain. An otherwise-required strategic Replan may propose a new project root, and unchanged adopted `REPLAN_READY` must adopt it with the reviewed strategic state. A workflow source, semantic, validator, worker, deployment, or release change cannot by itself create a Replan, alter project identity, invalidate a review, or change a spend gate. Selected, authorized, acknowledged, or execution-started B records preserve their exact authority and execution inputs. When current rules remove an obsolete procedural blocker from that B's actual next decision, use the existing bounded X/Selection update without rewriting the producing chain or broadening authority. Missing project bytes returns resolver row 3's project-evidence blocker. Version 1 source-bound objects remain available only through the exact-inventory legacy adapter.

Identity recovery, record repair, and administrative work produce no technical inference. Implementation-only work may resolve its implementation hypothesis while measurement and comparison remain not applicable. These outcomes create no additional Q, research, review, repeated B, synthetic E, metric, or trajectory artifact.

For a selected strategic replan, read [Replan review](replan-review.md). Other outcomes do not load its packet or report templates.
