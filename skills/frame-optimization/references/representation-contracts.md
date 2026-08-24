# Representation contracts

Read this reference completely when creating or materially reframing an R1-R8 contract. `PROBLEM.md` remains authoritative for problem semantics; these items define search strategy and its permitted claims.

Write the two core Briefs and Contract tables with concrete task nouns. Use the PROBLEM Brief for the task story and the REPRESENTATION Brief for the search story. Say which rendered object the harness measures, what the optimizer proposes, how conversion works, and which actual configs, schedules, models, or decks are searched. Keep labels such as `C`, `E1`, `T1`, and `U` out of the Brief. Use them only in the Contract table or linked details after the underlying items have plain names. Each core Contract cell contains a concise decision, not a TODO; use a second short sentence only when needed for its direct consequence. Do not copy technical terms from this reference into a core document; use the plain-language rewrites in `representation-documents.md`.

## Contents

- R1. Working representations and translation
- R2. Encoding redundancy
- R3. Scale behavior
- R4. Operations, neighborhoods, and legality
- R5. Module decomposition
- R6. Interfaces and composition
- R7. Coupling
- R8. Search run, validation, and old-work compatibility
- Exploratory and modular completion gates

## R1. Working representations and translation

Name one canonical evaluation representation. Slot H must accept it directly or through one pinned adapter.

For each active search representation, record:

- encoder, decoder, and failure behavior;
- exact or lossy translation;
- reachable legal subset;
- search normalization;
- tested round-trip property.

State whether the search representation covers all legal solutions, a defined subset, or an unknown subset. Give the applicable coverage limit.

Use Slot B exact identity for lossless round trips. Use semantic equivalence only when Slot B permits semantics-preserving loss.

Partial or unknown coverage prohibits global-optimality, exhaustion, and non-discovery claims over uncovered parent solutions.

Completion test: A reader can identify every active form, translate it to evaluation form, and state the searched subset and claim limit.

## R2. Encoding redundancy

Keep two relations separate:

- semantic equivalence belongs only to `PROBLEM.md` Slot B;
- encoding redundancy identifies encodings that decode to the same exact legal solution.

For `decode: E -> S`, define `e1 ~G e2` only when both decoded values have the same Slot B exact identity. The quotient `E / ~G` removes encoding freedom; it does not redefine parent semantic equivalence.

Record only current search needs:

- known encodings of one exact candidate;
- normal form, when used;
- effect on sampling, counting, or neighborhoods;
- unresolved effect and next action or claim limit.

Before exploration, classify redundancy as known, absent, or `Unknown`. Pin R2 only when a uniqueness, counting, exhaustive coverage, symmetry reduction, search-efficiency, or proof claim depends on it.

Completion test: Search claims cannot confuse multiple encodings with multiple exact solutions.

## R3. Scale behavior

Reference every scale variable from Slot A. Do not add, remove, or redefine a parent scale variable.

For each variable that affects current search, record applicable changes in:

- encoding size;
- translation or operation cost;
- neighborhood growth;
- module count or interface width.

Pin R3 when a complexity claim, resource allocation, proof, or scale-dependent module boundary depends on it. Otherwise, R3 can remain provisional with a claim limit.

Completion test: A reader can trace each material parent scale variable into representation size, search cost, and decomposition behavior.

## R4. Operations, neighborhoods, and legality

For each primitive operation, define:

- changed decisions;
- preconditions and failure behavior;
- Slot F cost;
- Slot G information use;
- hard-constraint handling.

Assign exactly one legality mode:

- `preserve`: construction stays feasible;
- `guard`: a precondition prevents an illegal candidate;
- `repair`: a defined step attempts to restore legality;
- `reject`: search detects and discards an illegal candidate.

For `repair`, define failure behavior and search-distribution bias. Repair must not silently change candidate meaning.

Define the neighborhood as candidates reachable by one permitted operation. Classify intended-subset reachability as connected, disconnected, or unknown.

For disconnected reachability, identify components or a starting policy that covers them. For unknown reachability, state tests and claim limits.

Check hard constraints against Slot C, soft constraints against Slot D, and probabilistic constraints against Slots E and H.

Completion test: Every move has a cost, information boundary, legality mode, and known reachability scope or explicit claim limit.

## R5. Module decomposition

A module is an optimization unit with owned decisions, a small interface, and independently changeable choices. A source directory or document section is not sufficient.

Keep R5, R6, and R7 at `-` while search treats the candidate as one whole. Do not design modules, interfaces, or coupling rules for a decomposition that is not currently proposed.

For each proposed module, record:

- owned variables and operations;
- interface;
- local objective contribution and inherited constraints;
- search resource allocation;
- practical reason for separation.

Do not assign one decision to two modules. Put a necessary shared decision in R7 and name its coordinator.

Do not create a module without meaningful local alternatives. Keep fixed components as dependencies or interface inputs.

Accept a boundary only when it improves local reasoning, testing, reuse, parallel work, proof structure, or change isolation. Reject boundaries whose coordination cost exceeds their benefit.

Completion test: Every module owns distinct changeable decisions and has a practical reason to exist.

## R6. Interfaces and composition

Each active interface states:

- inputs, outputs, and visible invariants;
- hidden internal decisions;
- failure behavior and compatibility conditions;
- composition and translation to evaluation form.

Keep the interface smaller than the implementation choices it hides. Do not expose an internal decision only to make modules appear independent.

Define candidate composition as an explicit operation. State whether it always produces a legal parent solution.

When composition can fail, define detection, repair, rejection, and responsibility. Every composed candidate must pass the parent Slot H protocol.

For cyclic dependencies, define update order, fixed-point behavior, or a joint coordination step. Do not call a cycle independent parallel work.

Completion test: A reader can compose module outputs, detect failure, and obtain one candidate for parent evaluation.

## R7. Objective, constraint, resource, and information coupling

Record coupling that can change decomposition, search order, constraint handling, resource use, or result interpretation.

Use a table with at least:

```markdown
| Modules | Shared quantity or risk | Evidence | Handling |
|---|---|---|---|
| A, B | boundary state z | measured sensitivity | joint evaluation |
| A, B, C | adaptive capacity constraint | Unknown | global check after composition |
```

Include higher-order, time-dependent, or adaptive coupling when repository evidence, domain structure, or observed failures make it plausible.

Classify each material relation as:

- exactly separable;
- separable with fixed interface variables;
- additive with a bounded coupling term;
- empirically weak without a proved bound;
- non-separable;
- unknown.

Classify every constraint as local, interface-level, or global. Name responsibility for each crossing constraint.

Use `Unknown` instead of `weak` or `small` when no bound, sensitivity result, or applicable source exists.

Apply these claim rules:

1. An exact composition guarantee supports only its stated global claim.
2. A bounded term supports only the claim allowed by its bound.
3. Empirical, unknown, or non-separable coupling requires global evaluation.
4. Unknown coupling permits module proposals but prohibits independent local-to-global improvement claims.

Partition the parent Slot F search budget across modules and coordination. Parallel proposal work can proceed under unknown coupling when each composed candidate gets global evaluation.

Completion test: Every material crossing relation has evidence, handling, responsibility, and a local-to-global claim limit.

## R8. Search run, validation, and old-work compatibility

Link the executable Slot H harness and current-epoch baseline.

For the requested search scope, record:

- starting options and total budget;
- when the parent Budget uses proposal, candidate, attempt, or an equivalent search-opportunity unit, the first observable event that consumes that unit, the amount charged, and the controlling basis; otherwise record `not applicable`;
- whether deterministic local construction and engineering checks may precede that event; any permitted pre-charge repair must preserve one frozen substantive target and may use only non-selection-producing feedback;
- whether later proposals may use earlier proposal, validation, or evaluation results;
- who or what selects the next proposal when that choice is delegated;
- survivor ranking and tie handling;
- confirmation, promotion, stopping, and scale-up rules;
- whether old checkpoints, saved proposals, or cached scores may be reused.

Pre-charge construction may repair fidelity to the unchanged mechanism, algorithm, substantive parameter alternative, representation, inputs, evaluator, acceptance meaning, comparison controls, sampling plan, design, interface, and checks. Formatting, compilation settings, or local implementation shape may change when they do not change that frozen target or create a choice among substantive alternatives. Performance, evaluator, hidden, human, remote, or other selection-producing feedback ends this allowance. All existing preparation, time, compute, effect, attempt, and total-resource limits continue to accumulate; absence of a proposal charge is not an unlimited retry allowance.

Adopt the current `r8_measurement_constraints` from Slots D, E, and H as a ceiling. These constraints define evidence meaning, maximum consequence, required confirmation, forbidden conclusions, adaptive-exposure limits, reuse limits, and measurement invalidation. R8 chooses survivor, route, budget, and stopping actions within that ceiling; it cannot enlarge or repair the measurement design.

For every result-based stopping trigger, record the trigger, the smallest affected scope (`candidate`, `route`, or `campaign`), the exact identities and authority that survive, the next eligible action, and the reopening condition. Candidate scope ends one immutable candidate and its dependent use. Route scope ends one exact search route while preserving named alternatives. Campaign scope ends all campaign spend authority. Use campaign scope for an aggregate review condition only when every verdict covered by that condition makes all remaining permitted campaign work unavailable. A behavior-bearing repair creates a new candidate, B, authorization, and proposal charge; it stays in the current generation while the campaign remains open.

For the first planned check, name every result branch that would change the next allowed action. A check is **vacuous** only when current evidence proves that every legal result maps to the same allowed next action. Reject known-vacuous candidate or evaluation work before spend. When headroom, noise, resolution, representativeness, or proxy usefulness is unknown, the first bounded check may measure that unknown instead of presupposing its answer.

Use each measurement only for the decision consequence permitted by Slots D and H. An unknown proxy-to-objective relationship may permit a bounded diagnostic or another low-cost probe without stronger assurance. It cannot control survivor selection, route closure, material allocation, formal confirmation, transfer, safety, reliability, or real-objective claims until the adopted measurement constraints support that consequence. Recheck vacuity and permitted use when the baseline, measurement meaning, comparison conditions, decision rule, or adaptive exposure changes.

Apply the adopted schedule roles and evidence-use limits. Execution checks and reusable calibration do not become strength evidence, and a candidate change alone does not require protocol recalibration. Earlier evidence becomes adaptive exposure only when it guides later generation, tuning, screening, ranking, or selection.

The representation does not need to choose a specific search algorithm when the person or agent doing the work may choose it. In that case, state what they may choose and the feedback, operation, budget, selection, confirmation, and stopping limits that still apply.

Record applicable validation for:

- encoding of the intended legal subset;
- legal, repaired, or rejected decoding;
- meaning-preserving normalization;
- Slot B round trips;
- operation legality modes;
- stated move-graph reachability;
- module-interface and composition invariants;
- parent measurement of composed candidates;
- coupling claims against global measurements or bounds;
- retained search-state dispositions.

Distinguish a finite diagnostic from a proof. A finite test proves universal coverage, connectedness, or legality only when the tested space is exhaustive.

For exploratory work, record the starting set, search budget, feedback policy, survivor-selection rule, stopping rule, known coverage limits, and next actions for unresolved redundancy or reachability.

Unknown coverage, reachability, or redundancy permits candidate-level exploration. It prohibits exhaustion, convergence, and absence-of-better-solution claims.

Completion test: Two reasonable readers or agents using only the two main documents would follow the same search limits, feedback rules, first decision-changing check, survivor rule, scoped stopping rule and surviving authority, problem harness, measurement-use limits, vacuity decision, and old-work policy.

## Exploratory and modular completion gates

Request exploratory review only when:

- the parent is stable, verified, and matches the recorded binding;
- the PROBLEM Brief explains the system or process, what can change, what the changed thing receives or faces, what it produces or controls, and how that affects the result without relying on unexplained task labels;
- the REPRESENTATION Brief explains the search loop from starting point through proposal, conversion, rejection or measurement, feedback, selection, and stopping without opening a detail;
- the complete `PROBLEM.md` and `REPRESENTATION.md`, read without optional details, contain every fact needed for ordinary legality, evaluation, success, resource, proposal, feedback, selection, stopping, reuse, and claim decisions;
- every core Contract cell states a concise decision rather than a request to fill in information;
- Open decisions lists every `O` or `~` row with its next action and closure condition;
- Known limits lists every remaining restriction on search or conclusions, including restrictions carried by `P` rows;
- R1 defines evaluation form, active decoders, searched subset, and coverage limit;
- R2 records known, absent, or unknown redundancy with an action or claim limit;
- R4 defines operation preconditions, legality handling, and reachability limit;
- R8 identifies the executable harness, baseline, starting set, budget, feedback policy, first decision-changing check, survivor-selection rule, every stop trigger's candidate, route, or campaign scope and surviving authority, measurement-use limits, vacuity decision, and old-work policy;
- every unresolved item has a next action or permitted-claim limit;
- every retained search artifact has a compatibility disposition.

Request modular review only when all exploratory conditions hold and:

- R5 pins ownership and shared decisions for named modules;
- R6 pins active interfaces and composition;
- R7 records material known or plausible coupling and its handling;
- unknown or empirical coupling requires global evaluation;
- active module contracts exist only for actual separate work;
- module budgets fit parent Slot F;
- module information fits parent Slot G;
- crossing constraints have named checks;
- unresolved items have coordination, global evaluation, or claim limits.

`PROCEED_MODULAR` applies only to named modules and operations. It is not approval for every possible decomposition.
