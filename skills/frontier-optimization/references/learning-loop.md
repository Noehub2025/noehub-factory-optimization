# Frontier Learning Loop

## Contents

- [Reflection levels](#reflection-levels)
- [Coverage and spend gate](#coverage-and-spend-gate)
- [Close the loop](#close-the-loop)
- [Build the evidence chain](#build-the-evidence-chain)
- [Outcome Reflection](#outcome-reflection)
- [Hypothesis and mechanism interpretation](#hypothesis-and-mechanism-interpretation)
- [Historical compatibility](#historical-compatibility)
- [Strategic replan review method](#strategic-replan-review-method)
- [Strategic replan packet](#strategic-replan-packet)
- [Strategic replan artifact](#strategic-replan-artifact)

Load after a terminal B, after an uncovered E, or when a strategic replan is pending. This file is the sole source for Outcome Reflection and strategic replan review forms.

## Reflection levels

- **Routine:** valid expected evidence resolves the addressed decision without changing a route, baseline, design, budget policy, stop rule, or claim limit. Record the technical learning and apply R8 without extra diagnosis.
- **Diagnostic:** surprising, failed, ambiguous, validity-limited, or decision-limiting measurement evidence may justify a direct attempt, local check, focused Q, isolated prototype, or authorized diagnostic-only experiment. Choose among them by expected decision information relative to time, compute, risk, and opportunity cost.
- **Strategic:** evidence may change campaign baseline, route family, budget policy, stop rule, design profile, irreversible behavior, or claim limit. It needs sufficient evidence, applicable V, and adopted fresh-context replan review before dependent spend.

## Coverage and spend gate

Treat `completed`, `interrupted`, `failed`, and `blocked` as terminal B outcomes after Coordinator validation. `waiting_for_input` is a paused attempt. Every terminal B needs one controlling Outcome Reflection. Every E created later needs a reflection unless the evaluation B's controlling reflection already names that E and experiment identity.

Before acknowledging any later B, enumerate terminal B records and E records from persisted state and map them to reflections. Reject later spend when any terminal B is uncovered, any E is uncovered, one reflection ambiguously covers multiple terminal B records, or the controlling reflection lacks its required V, join, focused evidence, or applicable review. Timestamps and conversation summaries do not establish coverage; exact immutable identities do.

## Close the loop

1. Reconcile result packet, W state, artifacts, spend, reservations, recovery, E, and X. Preserve negative, failed, ambiguous, and invalid evidence.
2. Establish validity in this order: implementation, measurement, then comparison validity. Stop the inference at the first unresolved layer.
3. Build the evidence chain below. Recover the exact technical hypothesis and expected observation fixed before work. The terminal B controls the addressed decision; an exact candidate lineage supplies the originating mechanism when the B evaluates or confirms already implemented behavior. Judge the controlling B hypothesis `supported`, `contradicted`, `inconclusive`, or `not-applicable`; do not invent a post-result hypothesis.
4. Infer the strongest useful mechanism supported by the implementation, behavior, and outcome evidence. Distinguish a whole-package effect from evidence that a component was active, necessary, dominant, or numerically responsible.
5. Record the attribution limit and the R&D implication. An attribution limit creates no diagnosis, research, review, B, or spend by itself.
6. Interpret comparable history, progress, constraints, or measurement properties only when they can change the addressed or next concrete decision. Preserve every exclusion, adaptive-exposure limit, parent-owned metric, and guardrail that the interpretation uses.
7. Append the reflection below and bound the conclusion. Engineering and diagnostic-only evidence remains B evidence and creates no E.
8. For strategic evidence, technically filter alternatives, resolve user tradeoffs, prepare proposed F2-F4, Budget, Selection, and B state, then freeze that proposal in the replan snapshot.
9. Adopt a finding-free unchanged `REPLAN_READY`, then append the authoritative F2-F4, Budget, Selection, and B records exactly as reviewed.
10. Before later spend, require a latest Selection citing every controlling reflection and classifying each decision-relevant unknown as answered, deferred with an event, or blocking.

Research or diagnosis is justified only when its answer can change eligibility, route, allocation, stopping, promotion, or claim limit. Prefer the available action with the highest expected decision information relative to its cost and risk; a direct reversible candidate attempt may be more useful than mechanism diagnosis. Routine evidence with a unique R8 branch receives no extra work. A reflection without an explicit next decision, deferral, stop, halt, or blocker is incomplete.

Use specialized gates in addition to replan review: changed design needs design review and authorization; changed candidate needs implementation review; changed claim needs claim review; parent-scope conflict needs parent review.

## Build the evidence chain

Write a Reflection from adopted evidence; do not rerun the candidate, evaluator, engineering checks, repository tests, or workflow tests. Do not create a new snapshot or review merely to interpret evidence that is already valid.

Read the smallest complete evidence chain in this order:

1. **Current decision:** read the terminal B's `Decision hypothesis`, `Expected observation`, result, terminal outcome, related E, and the R8 rule, parent metrics, guardrails, and decision boundary that govern its consequence.
2. **Originating mechanism:** when B evaluates, confirms, or reuses an executable candidate, follow the exact candidate identity to the originating T or W, the design or implementation B that changed behavior, the executable-difference description or source manifest, the adopted implementation review, and the engineering or behavior evidence. Use identity-bound lineage rather than topic similarity. For a reference measurement, administrative B, or work with no technical mechanism, record `not-applicable` instead of inventing one.
3. **Comparison meaning:** read the adopted evaluator, protocol, comparator, workload or data scope, uncertainty, and result direction from E and its result. Add prior E and their controlling OR only when the comparability rule below permits the exact interpretation being made. Read lower-level measurement artifacts only when the adopted result does not already establish a decision-relevant property; never repeat the measurement.
4. **R&D decision:** read the applicable replacement boundary, disqualifying evidence, known limits, current Selection, and only those traces, route alternatives, or design surfaces already supported by persisted evidence. Budget and authority determine what may happen next, not what the evidence means.

Synthesize that chain rather than summarizing each record:

1. State the current B decision and the originating technical mechanism as separate layers. `Hypothesis result` judges the current B hypothesis; `Mechanism inference` explains what the complete lineage supports about the implemented mechanism.
2. Connect the evidence explicitly: what behavior-bearing difference was introduced, what implementation evidence shows that its pathways exist, and what valid outcome evidence supports at whole-package level.
3. Name component activity, necessity, dominance, mediation, or numerical contribution only at the grain supported by separating evidence. Otherwise keep the package conclusion and state the attribution limit.
4. Identify the defect, assumption, or local question that the evidence resolves. Do not keep a supported issue open merely because its internal contributions were not decomposed.
5. Turn the learning into R&D direction: state what later work should preserve or stop repeating, and name a next technical surface only when current traces, known limits, route evidence, or the replacement boundary supports it. A plausible list without evidence is not a conclusion.
6. State whether the measurement remains fit for the next concrete decision. A completed decision stays complete even when its comparator would be too coarse for a future successor decision.
7. Make `Maximum supported conclusion` include the strongest bounded mechanism conclusion as well as the resolved B decision; do not reduce it to a gate label such as `admit`, `reject`, or `completed`.

The Reflection is complete when a fresh Coordinator can answer from it: what was hypothesized, why the result supports or contradicts it, which mechanism is supported at what grain, what is now resolved, what remains decision-relevant, and what later work should preserve, change, defer, or stop. This interpretation creates no test, experiment, diagnosis, research task, review, B, spend, or authority.

## Outcome Reflection

Append after each adopted terminal B. One block may cover that B and its E. It cannot cover another terminal B. Add a separate block only for an E not covered by its evaluation B reflection.

```markdown
Outcome Reflection:
- Reflection ID: <OR identifier>
- Recorded at: <ISO-8601 datetime>
- Targets: <B identifier, terminal-outcome identity, and result identity; related E identifier and experiment identity when applicable>
- Evidence-state identity: <immutable identity of the terminal outcome, related E, applicable reviews, active D and X, Budget, and W state used>
- Level: <routine | diagnostic | strategic>
- Decision addressed: <the decision this work was intended to answer>
- Technical hypothesis: <exact terminal B Decision hypothesis and Expected observation, plus the identity-bound originating mechanism when this B evaluates, confirms, or reuses implemented behavior; or not-applicable with reason>
- Hypothesis result: <supported | contradicted | inconclusive | not-applicable, with the shortest sufficient evidence chain>
- Evidence validity: <implementation, measurement, and comparison validity in that order, each with evidence or not-applicable>
- Mechanism inference: <strongest useful whole-package, component, or mediated-pathway conclusion supported by the evidence>
- Attribution limit: <what the current design cannot separate or quantify; this field creates no follow-up work>
- R&D implication: <what later work should preserve, stop repeating, investigate, or defer, without creating authority>
- Measurement implication: <only a property that changes a concrete addressed or next decision, or not-applicable with reason>
- Progress interpretation: <compatible history, prospective rule, complete parent vector, and bounded interpretation only when they affect the decision; otherwise not-applicable>
- Constraint inference: <suspected, demonstrated, or shifted system-level constraint only when supported and decision-relevant; otherwise not-applicable>
- Maximum supported conclusion: <exact conclusion>
- Claim boundary: <important unsupported extensions>
- Decision-relevant unknowns: <unknowns that can still change eligibility, route, allocation, stopping, promotion, or claims>
- User decision: <required V and exact tradeoff or authorization, or None>
- Review consequences: <REPLAN_READY and any required design, implementation, claim, or parent review; or none>
- Decision consequence: <continue, revise, abandon, promote, stop, halt, or defer; name affected records>
- Next action: <one exact action, reconsideration event, stop, halt, or blocker determined from persisted state>
- Later-spend gate: <open only after named V, join, evidence, Selection, and reviews; or blocked with exact missing identity>
```

For a bound contradiction, name the D, assumptions, tolerance, E, and experiment identity. For a known-vacuous measurement, cite the current evidence proving that every legal result maps to the same action. Until resolved, the reflection cannot select promotion, incumbent use, claim strengthening, or dependent spend. Choose the highest-information authorized response rather than automatically creating a diagnostic batch.

## Hypothesis and mechanism interpretation

`Hypothesis result` answers the precommitted technical question:

- `supported` when valid evidence matches the predicted observable effect within the named scope;
- `contradicted` when valid evidence violates it;
- `inconclusive` when validity, resolution, or coverage cannot answer it; and
- `not-applicable` for work with no technical hypothesis.

Support is scoped evidence, not universal proof. For a terminal B, recover the controlling decision hypothesis from that B. When the B evaluates, confirms, or reuses an existing candidate, recover the originating mechanism through its exact candidate, T or W, design or implementation B, and adopted implementation evidence; this mechanism context cannot replace the B-level decision. Preserve both layers, the expected observation, contradiction, and decision boundary. Implementation-only evidence may support implementation of the pathway but cannot support its performance effect. A valid whole-treatment comparison may support that the bounded package caused the observed local effect when the treatment is the only executable difference and evaluator, protocol, and comparison integrity remain fixed.

Infer mechanisms at the strongest supported grain:

- **Whole package:** a valid controlled comparison plus exact executable differences can support the package-level causal effect without ablation.
- **Component present:** source and behavior evidence can show that a component pathway exists and behaves as designed.
- **Component contribution:** necessity, dominance, mediation, or numerical contribution needs a separating intervention, ablation, trace, or equivalent evidence.

An unexplained component contribution limits attribution but does not invalidate a valid package-level result or block another bounded reversible attempt. Diagnose it only when the pending decision depends on choosing among those internal explanations. `R&D implication` must turn the supported learning into useful direction: preserve a supported local mechanism as a default hypothesis, stop repeating a resolved local question, name an evidence-backed next surface, or defer when the evidence does not discriminate. It cannot confer incumbent status, reuse permission, or spend.

Write `Progress interpretation` in evidence-bounded prose only when cross-B history can change the decision; it has no mandatory finding enum. Combine only E with compatible parent objective, measurement meaning, comparator role, protocol, workload, data scope, uncertainty, validity, and result direction, or an explicit equivalence argument. Apply the complete parent-owned vector. A single departure is not persistence; movement within noise or resolution is not a plateau; a bounded plateau or underperformance finding needs a prospective rule. A proxy cannot establish route progress while a required metric, hard constraint, guardrail, segment, tail, delayed confirmation, or operating-cost boundary fails or remains unresolved.

Write `Constraint inference` only when it affects the decision. `suspected` identifies a plausible limiting factor without system-level effect evidence. `demonstrated` needs an intervention or discriminating test showing that changing the factor changes the parent objective under the named conditions. `shifted` needs evidence that the intervention changed which factor limits that objective. Local difficulty, eliminated alternatives, or movement in a proxy does not establish a bottleneck.

Write `Measurement implication` only when a measurement property changes a concrete decision. Distinguish a saturated comparator-derived score from exhaustion of the evaluator itself. A limitation that does not prevent the addressed decision remains a future-use note; it creates no protocol-repair requirement. If the limitation prevents the current decision, record `inconclusive` and let Selection compare a direct candidate attempt, direct incumbent comparison, protocol adjustment, diagnosis, research, or stop by decision information and cost.

Outcome Reflection explains adopted evidence. It adds no spend authority, investment resolver, research requirement, review kind, or user decision. Selection must apply its hypothesis result, mechanism inference, attribution limit, R&D implication, measurement implication, and maximum conclusion without strengthening or reinterpretation, then apply the existing R8, Budget, replan, and specialized gates.

## Historical compatibility

Keep every earlier Outcome Reflection immutable and valid under its bound source. The first controlling reflection written under this source may cite compatible old E and their coverage-complete old OR identities without adding the new fields to those records. A later reflection may recover the original pre-spend hypothesis but cannot invent one or retroactively declare underperformance or plateau.

For identity recovery, record repair, administrative work, or other work that produces no technical evidence, use `Technical hypothesis: not-applicable`, `Hypothesis result: not-applicable`, and `R&D implication: none; no technical evidence was produced`. For one-shot work without repeated performance meaning, use `Progress interpretation: not-applicable`. Implementation-only work judges the implementation hypothesis and keeps measurement and comparison `not-applicable`. These forms create no additional Q, research, review, repeated B, synthetic E, metric, or trajectory artifact.

## Strategic replan review method

Before writing a verdict, the reviewer must:

1. verify every snapshot identity and current parent authority;
2. reconstruct the reflection from the planned B, result, W outcome, E, X, and cited artifacts;
3. check implementation, measurement, and comparison validity in that order;
4. verify the precommitted hypothesis, hypothesis result, evidence-bounded mechanism inference, attribution limit, R&D implication, and complete parent-owned vector;
5. verify that any diagnosis or research can change the affected strategic decision and is preferable to a cheaper direct source of decision information;
6. require sufficient current research only for the affected strategic decision;
7. check technical eligibility before every V and preserve the user's actual choice;
8. reconcile Budget, protected reserves, Selection, B, and F2-F4 as one decision;
9. preserve separate design, implementation, claim, and parent gates.

Return exactly `REPLAN_READY`, `REPLAN_REPAIR_REQUIRED`, `EVIDENCE_REQUIRED`, `PARENT_REVIEW_REQUIRED`, or `BLOCKED`. A positive result has no finding; every nonpositive result has at least one complete finding.

## Strategic replan packet

Create a new packet and review path for every attempt. Include no expected verdict or proposed repair.

```yaml
review_kind: replan
review_id: <unique identifier>
packet_path: <frontier/reviews/replan-<review-id>-packet.yaml>
packet_id: <review kind and id plus SHA-256 of canonical packet bytes with this field omitted>
snapshot_manifest: <frontier/reviews/replan-<review-id>-project-snapshot.yaml and identity>
snapshot_id: <immutable snapshot identity>
task_path: <canonical task path>
problem_epoch: <integer>
problem_generated_at: <ISO-8601 datetime>
representation_revision: <integer>
representation_generated_at: <ISO-8601 datetime>
representation_permitted: <exact reviewed text>
triggering_reflection: <ledger block location, targets, and immutable identity>
supporting_evidence: [<Q, D, E, X, result, trace, join, or artifact identity>]
user_decisions: [<V identifiers and identities, or none>]
proposed_frontier_updates: <snapshot path and identity for proposed F2-F4 changes>
proposed_budget_update: <snapshot path and identity>
proposed_selection: <snapshot path and identity>
proposed_batches: [<snapshot paths, identifiers, and identities for Primary and Parallel B>]
design_and_implementation_state: [<applicable W, design review, development authorization, candidate, and implementation review identities>]
assigned_review_path: <frontier/reviews/replan-<review-id>.md>
completion_check: <every replan requirement receives a verdict and every finding cites immutable snapshot evidence>
```

## Strategic replan artifact

Only `review-frontier` writes the assigned file.

```markdown
---
type: Optimization Frontier Strategic Replan Review
status: complete
review_id: <identifier>
review_result: <REPLAN_READY | REPLAN_REPAIR_REQUIRED | EVIDENCE_REQUIRED | PARENT_REVIEW_REQUIRED | BLOCKED>
reviewed_by: review-frontier/1
reviewed_at: "<ISO-8601 datetime>"
snapshot_packet: <path and identity>
generated: { by: review-frontier/1, at: "<ISO-8601 datetime>" }
---

# FRONTIER STRATEGIC REPLAN REVIEW: <effort name>

Result: <allowed result>
Triggering reflection: <ledger location, targets, and identity>
Reviewed snapshot: <packet path and identity>
Reviewed at: <ISO-8601 datetime>

## Readiness checks

- Parent bindings, permitted scope, and authority: <pass or findings>
- Result, implementation, measurement, and comparison validity: <pass or findings>
- Technical hypothesis, hypothesis result, and evidence-bound mechanism inference: <pass or findings>
- Attribution limit, R&D implication, measurement implication, and full parent result vector: <pass or findings>
- Decision-relevant unknowns and selected information source: <pass or findings>
- Research coverage and stop rule: <pass or findings>
- Technical eligibility, V records, and recommendation fidelity: <pass or findings>
- Budget, reserve, Selection, B, and stop rules: <pass or findings>
- Deterministic next action and complete reflection coverage: <pass or findings>
- Specialized review boundaries: <pass or findings>

## Findings

### Finding 1: <omit when REPLAN_READY>

- Result effect: <REPLAN_REPAIR_REQUIRED | EVIDENCE_REQUIRED | PARENT_REVIEW_REQUIRED | BLOCKED>
- Affects: <paths, records, or fields>
- Requirement: <exact requirement>
- Observed: <snapshot fact>
- Evidence: <snapshot identities>
- Required correction: <observable condition; no repair text>
```
