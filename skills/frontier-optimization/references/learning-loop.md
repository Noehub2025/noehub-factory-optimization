# Frontier Learning Loop

## Contents

- [Reflection levels](#reflection-levels)
- [Coverage and spend gate](#coverage-and-spend-gate)
- [Close the loop](#close-the-loop)
- [Outcome Reflection](#outcome-reflection)
- [Progress and constraint interpretation](#progress-and-constraint-interpretation)
- [Historical compatibility](#historical-compatibility)
- [Strategic replan review method](#strategic-replan-review-method)
- [Strategic replan packet](#strategic-replan-packet)
- [Strategic replan artifact](#strategic-replan-artifact)

Load after a terminal B, after an uncovered E, or when a strategic replan is pending. This file is the sole source for Outcome Reflection and strategic replan review forms.

## Reflection levels

- **Routine:** valid expected evidence changes no route, baseline, design, budget policy, stop rule, or claim limit. Proceed without research only when R8 already determines the next action.
- **Diagnostic:** surprising, failed, ambiguous, validity-limited, or measurement-property evidence needs the cheapest local check, focused Q, isolated non-candidate prototype, or authorized diagnostic-only experiment that can distinguish material explanations.
- **Strategic:** evidence may change campaign baseline, route family, budget policy, stop rule, design profile, irreversible behavior, or claim limit. It needs sufficient evidence, applicable V, and adopted fresh-context replan review before dependent spend.

## Coverage and spend gate

Treat `completed`, `interrupted`, `failed`, and `blocked` as terminal B outcomes after Coordinator validation. `waiting_for_input` is a paused attempt. Every terminal B needs one controlling Outcome Reflection. Every E created later needs a reflection unless the evaluation B's controlling reflection already names that E and experiment identity.

Before acknowledging any later B, enumerate terminal B records and E records from persisted state and map them to reflections. Reject later spend when any terminal B is uncovered, any E is uncovered, one reflection ambiguously covers multiple terminal B records, or the controlling reflection lacks its required V, join, focused evidence, or applicable review. Timestamps and conversation summaries do not establish coverage; exact immutable identities do.

## Close the loop

1. Reconcile result packet, W state, artifacts, spend, reservations, recovery, E, and X. Preserve negative, failed, ambiguous, and invalid evidence.
2. Establish validity in this order: implementation, measurement, then comparison validity. Stop the inference at the first unresolved layer.
3. Compare the precommitted hypothesis and observation with the complete parent-owned result vector. Reconstruct only compatible E and their controlling reflections; preserve every exclusion and adaptive-exposure limit.
4. Append the reflection below and bound the conclusion. Engineering and diagnostic-only evidence remains B evidence and creates no E.
5. For routine evidence, record why research cannot change the R8 decision.
6. For diagnostic evidence, run the cheapest distinguishing local check before focused research.
7. For strategic evidence, technically filter alternatives, resolve user tradeoffs, prepare proposed F2-F4, Budget, Selection, and B state, then freeze that proposal in the replan snapshot.
8. Adopt a finding-free unchanged `REPLAN_READY`, then append the authoritative F2-F4, Budget, Selection, and B records exactly as reviewed.
9. Before later spend, require a latest Selection citing every controlling reflection and classifying each unknown as answered, deferred with an event, or blocking.

Research is justified only when its answer can change eligibility, route, allocation, stopping, promotion, or claim limit and cheaper local evidence cannot answer it. Routine evidence with a unique R8 branch receives no extra research. Diagnostic evidence starts with the cheapest distinguishing check. A reflection without an explicit next decision, deferral, stop, halt, or blocker is incomplete.

Use specialized gates in addition to replan review: changed design needs design review and authorization; changed candidate needs implementation review; changed claim needs claim review; parent-scope conflict needs parent review.

## Outcome Reflection

Append after each adopted terminal B. One block may cover that B and its E. It cannot cover another terminal B. Add a separate block only for an E not covered by its evaluation B reflection.

```markdown
Outcome Reflection:
- Reflection ID: <OR identifier>
- Recorded at: <ISO-8601 datetime>
- Targets: <B identifier, terminal-outcome identity, and result identity; related E identifier and experiment identity when applicable>
- Evidence-state identity: <immutable identity of the terminal outcome, related E, applicable reviews, active D and X, Budget, and W state used>
- Level: <routine | diagnostic | strategic>
- Planned mechanism and expected observation: <exact B hypothesis and precommitted observation>
- Validity: <implementation, measurement, and comparison validity, each with evidence or not applicable>
- Comparable history: <ordered E identities and their controlling OR identities, exclusions with reasons, insufficient-compatible-evidence with reason, or not-applicable with reason>
- Governing progress rule: <T and B field identities fixed before spend, or None>
- Progress finding: <on-course | weak-under-prospective-rule | emergent-warning | validity-unresolved | insufficient-compatible-evidence | not-applicable>
- Constraint finding: <not-assessed | suspected | demonstrated | shifted, with exact evidence and affected parent objective>
- Observed versus expected: <agreement, deviation, failure, or unresolved difference with evidence>
- Belief update: <supported, weakened, contradicted, and untouched assumptions>
- Competing explanations: <ranked evidence-bounded explanations or None>
- Maximum supported conclusion: <exact conclusion>
- Unsupported conclusions: <claims the result does not support>
- Decision-relevant unknowns: <unknowns that can still change eligibility, route, allocation, stopping, promotion, or claims>
- Smallest distinguishing test: <local check, focused research question, isolated prototype, comparison, or None>
- Research disposition: <none with reason | local diagnosis | focused Q | route landscape refresh | isolated prototype | parent review>
- User decision: <required V and exact tradeoff or authorization, or None>
- Review consequences: <REPLAN_READY and any required design, implementation, claim, or parent review; or none>
- Decision consequence: <continue, revise, abandon, promote, stop, halt, or defer; name affected records>
- Next action: <one exact action, reconsideration event, stop, halt, or blocker determined from persisted state>
- Later-spend gate: <open only after named V, join, evidence, Selection, and reviews; or blocked with exact missing identity>
```

For a bound contradiction, name the D, assumptions, tolerance, E, and experiment identity. For a known-vacuous measurement, cite the current evidence proving that every legal result maps to the same action. Until resolved, the reflection cannot select promotion, incumbent use, claim strengthening, or dependent spend. It may select only the smallest authorized diagnostic unless the contradiction changes parent legality or authority.

## Progress and constraint interpretation

Use exactly one `Progress finding` value:

- `on-course`: compatible valid evidence remains within the prospective rule, every parent-owned mandatory boundary passes, and the next required check remains reachable;
- `weak-under-prospective-rule`: compatible valid evidence crosses a progress rule fixed before the governed spend;
- `emergent-warning`: compatible evidence is decision-relevantly surprising but no earlier rule determines its consequence;
- `validity-unresolved`: implementation, measurement, or comparison validity remains unresolved;
- `insufficient-compatible-evidence`: trajectory interpretation matters, but the compatible evidence cannot yet establish an ordered conclusion; or
- `not-applicable`: cross-B progress cannot affect this decision.

Keep the fields internally consistent. `not-applicable` has no ordered history and uses `Governing progress rule: None`. `insufficient-compatible-evidence` names excluded or missing observations and cannot claim on-course or weak progress. Every other finding names the ordered compatible E and controlling OR identities. `on-course` and `weak-under-prospective-rule` cite the governing T and B fields fixed before spend. `emergent-warning` may use `None` when no sufficiently specific prospective rule existed. A later rule may govern later authorized work, never the evidence that motivated it.

Classify the observed pattern without promoting it beyond its evidence:

- a single departure is an anomaly, not persistence; use `emergent-warning` only when compatible history makes it decision-relevant, otherwise use `insufficient-compatible-evidence`;
- movement within measurement noise or resolution is not a plateau or underperformance finding;
- an expected slowdown that remains inside the prospective rule is `on-course` when every mandatory boundary passes and the next check is reachable;
- pre-specified underperformance is `weak-under-prospective-rule`;
- an unexpected compatible change without a governing consequence is `emergent-warning`, not a retrospective stop rule; and
- a bounded plateau requires compatible valid evidence plus a prospective definition of negligible progress under named conditions. Without that rule, record only the supported warning or evidence insufficiency, never a post-hoc plateau.

Apply the complete parent-owned result vector. A proxy, aggregate, or leading indicator may support its local mechanism claim, but cannot establish overall route progress when a required metric, hard constraint, guardrail, segment, tail condition, delayed confirmation, or operating-cost boundary fails or remains unresolved. Pareto-incomparable valid results retain the full vector and use an existing parent rule; Outcome Reflection creates no post-result weights.

Use `Constraint finding` independently from progress:

- `not-assessed` when no constraint conclusion is supported or needed;
- `suspected` when evidence identifies a plausible limiting factor but has not shown a system-level effect on the parent objective;
- `demonstrated` only when an intervention or discriminating test shows that changing the factor changes the parent objective under the named conditions; and
- `shifted` only when evidence shows that an intervention changed which factor limits the parent objective.

Local difficulty, eliminated alternatives, or improvement in the suspected factor's proxy is insufficient for a bottleneck claim. After a bottleneck intervention, reconsider constraint migration before assigning more work to the former factor. `Maximum supported conclusion` must keep every constraint statement within these bounds.

Outcome Reflection explains adopted evidence. It adds no spend authority, investment resolver, research requirement, review kind, or user decision. Selection must copy its compatible history, progress finding, constraint finding, and maximum conclusion without reinterpretation, then apply the existing R8, Budget, replan, and specialized gates.

## Historical compatibility

Keep every earlier Outcome Reflection immutable and valid under its bound source. The first controlling reflection written under this source may cite compatible old E and their coverage-complete old OR identities without adding the new fields to those records. When no prospective rule governed earlier spend, the new reflection may record an `emergent-warning` or evidence insufficiency, but cannot retroactively declare underperformance or plateau.

For one-shot work, simple non-code work without repeated performance meaning, implementation-only materialization, or unrelated research, record `not-applicable` with a reason. This creates no additional Q, research, review, repeated B, synthetic E, metric, or trajectory artifact.

## Strategic replan review method

Before writing a verdict, the reviewer must:

1. verify every snapshot identity and current parent authority;
2. reconstruct the reflection from the planned B, result, W outcome, E, X, and cited artifacts;
3. check implementation, measurement, and comparison validity in that order;
4. verify the exact compatible E sequence, controlling OR identities, governing prospective rule, complete parent-owned vector, and bounded progress and constraint findings;
5. require the smallest sufficient local diagnosis before broader research;
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
- Comparable history, governing rule, full parent result vector, and progress and constraint findings: <pass or findings>
- Expected observation, deviation, and evidence-bound belief update: <pass or findings>
- Unknowns and smallest distinguishing test: <pass or findings>
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
