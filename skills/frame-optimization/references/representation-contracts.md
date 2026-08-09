# Representation contracts

Read this reference completely when creating or materially reframing an R1-R8 contract. `PROBLEM.md` remains authoritative for problem semantics; these items define search strategy and its permitted claims.

## Contents

- R1. Working representations and translation
- R2. Encoding redundancy
- R3. Scale behavior
- R4. Operations, neighborhoods, and legality
- R5. Module decomposition
- R6. Interfaces and composition
- R7. Coupling
- R8. Validation and search-state compatibility
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

## R8. Validation and search-state compatibility

Link the executable Slot H harness and current-epoch baseline.

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

For exploratory work, record the starting set, search budget, known coverage limits, and next actions for unresolved redundancy or reachability.

Unknown coverage, reachability, or redundancy permits candidate-level exploration. It prohibits exhaustion, convergence, and absence-of-better-solution claims.

Completion test: Search can start from identified candidates under a fixed budget, run through the parent harness, and use only compatible retained state.

## Exploratory and modular completion gates

Request exploratory review only when:

- the parent is stable, verified, and matches the recorded binding;
- R1 defines evaluation form, active decoders, searched subset, and coverage limit;
- R2 records known, absent, or unknown redundancy with an action or claim limit;
- R4 defines operation preconditions, legality handling, and reachability limit;
- R8 identifies the executable harness, baseline, starting set, and budget;
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
