# Measurement design

Read this reference when `design-measurement` designs or repairs a protocol, when `frame-optimization` adopts its projection, or when `review-optimization` reviews measurement fitness. It defines one professional interface without adding a review branch, verdict, gate, identity, or persistent workflow mode.

## Ownership and adoption

`design-measurement` is the sole professional author and reviser of measurement design. `frame-optimization` is the sole lifecycle coordinator and normative adopter. The Designer writes nonnormative analysis and one complete projection in the Coordinator-selected Slot H detail. The Coordinator adopts or rejects the projection as a whole and never edits, completes, or reinterprets its measurement meaning.

After adoption, `PROBLEM.md`, its adopted Slot details, and `REPRESENTATION.md` are the runtime contract. The Designer record remains design evidence, not a second source of authority. A later semantic change returns to `design-measurement`.

`review-optimization` checks fitness through its existing readiness branch. It reports defects and closure conditions without writing the protocol or requiring one named technique. `review-representation` checks only whether R8 stays within adopted measurement constraints. Measurement-support review checks implementation fidelity only.

## Fresh-context execution

Use exactly one mode:

- `new` only when the task has no current measurement protocol;
- `revision` for any material change to an existing protocol; or
- `repair` for the current `measurement-design` review findings.

Run `design-measurement` in a fresh agent context. For `revision`, the Coordinator first creates empty permitted section anchors in the existing Slot H detail and supplies only the real objective, intended consequence, resources, operating conditions, protocol-independent evidence, and exact write anchor. Phase A does not read Slot H content, the current protocol, its rationale, or results produced by it. The Designer writes `Independent reconstruction — not adopted` at the supplied anchor before Phase B opens those materials.

If the revision Agent already read, wrote, or helped design the current protocol, rationale, or protocol-dependent results before recording the independent reconstruction, it returns `DESIGN_BLOCKED: fresh revision context required`. `repair` starts from the current design and findings and does not repeat Phase A. All modes use the same Slot H detail; do not create a second artifact or review.

## Five-part interface

### 1. Target and claim

State the real objective supplied by the project, the measured object, inferential target, comparison, and observed conditions. Classify each output as the real objective, a proxy, or a diagnostic. State which live explanations the result can distinguish, which alternatives remain, and the maximum attribution and transfer claim.

### 2. Conditions and design

Define the applicable cases, data, scenarios, environments, workload, comparators or references, observation unit, and independent analysis unit. Control material variation with the smallest suitable combination of coverage, sampling, repetition, pairing, blocking, ordering, balancing, or randomization. Define failed, missing, interrupted, and invalid observations before results are seen.

Use task-neutral concepts. A particular task can instantiate them with opponents, seeds, datasets, machines, operators, sites, time periods, physical specimens, or other concrete conditions.

### 3. Resolution and decision risk

State the smallest improvement relevant to the intended decision. The user owns value, risk, and resource choices; the Designer translates them into a detectable contrast and decision rule. When no value threshold exists, a bounded diagnostic may report its resolution and limit its consequence. Survivor selection, route closure, material investment, or formal confirmation cannot silently use any positive value as the threshold.

State uncertainty over the inferential target and what it excludes. Use formal power, simulation, intervals, bounds, or sensitivity analysis only when they can change the design or consequence. Account for the asymmetric cost of false acceptance and false rejection. Use the minimum positive, negative, reference, sensitivity, or calibration checks needed to expose material failure modes; no fixed control taxonomy is mandatory.

Calibration establishes the behavior of a measurement system, proxy, or reference for a named protocol identity. Reuse it across candidates while its assumptions and invalidation conditions remain unchanged. Calibration of a zero point does not establish sensitivity, target linkage, or transfer.

### 4. Evidence use and economy

For every material schedule part, state the decision-relevant information it adds, the explanation it can eliminate, and what capability disappears if it is removed. Mark execution-only checks, calibration, direct comparison, robustness checks, and confirmation by their actual roles. A costly part with no distinct decision contribution is removed, reduced, or reused.

Record when prior results influence later hypothesis generation, parameter choice, screening, ranking, or selection. Only such feedback creates adaptive exposure; ordinary repetition does not. Define an exposure limit or independent confirmation only when adaptation can bias the intended inference.

### 5. Consequence and lifecycle

Map each material result class to its maximum supported inference and maximum investment consequence. State stronger forbidden conclusions, required confirmation, and the conditions that leave the protocol valid, require recalibration, require replacement, or invalidate retained comparisons.

The Designer supplies an evidence ceiling, not authority. R8 may choose a smaller action within that ceiling. The user and existing workflow remain responsible for value choices, resources, route selection, stopping, and authorization.

## Proportional depth

Depth follows consequence, not novelty or uncertainty.

A direct or bounded diagnostic design stays compact when it has low cost, narrow use, no adaptive selection, and no power to promote a candidate, close a route, allocate material resources, serve as formal confirmation, or support a broad claim. An unknown proxy can remain compact when its only result is another bounded probe or an exact claim limit.

Expand only the portions implicated by the intended consequence. Stronger analysis is required when a proxy controls selection or investment, evidence is adaptively reused, a costly schedule needs justification, the minimum useful change approaches resolution, confirmation is claimed, or results are expected to transfer beyond observed conditions. This is not a persistent `light` or `enhanced` mode and does not create another gate.

## Contract projection

The Designer returns complete proposed content for:

```yaml
slot_d: <objective, comparison, threshold, and maximum consequence>
slot_e: <inferential target, analysis unit, aggregation, variation, and uncertainty>
slot_h: <protocol, conditions, schedule roles, decision rule, controls, and calibration>
r8_measurement_constraints: <evidence meaning, consequence ceilings, confirmation, exposure, reuse, and forbidden conclusions>
known_limits: <current restrictions that remain after adoption>
invalidation_and_recalibration: <preserve, recalibrate, replace, and comparability triggers>
```

The projection contains measurement constraints, not search decisions. It cannot select a survivor, prioritize a route, allocate a budget, define campaign stopping, or create authority. The Coordinator copies each complete block into its owning contract location. If a block is not adoptable, return it to the Designer rather than editing its meaning.

Keep exactly one current `Contract projection — not adopted` section. The existing readiness review compares every projection block with its adopted D, E, H, R8, Known limits, and invalidation or recalibration location. A missing or changed block is a mechanical adoption error for `frame-optimization`, not a new professional design finding.

## Review findings

Use `work_type: measurement-design` inside the existing readiness finding schema when professional measurement repair is required. This work type derives the existing `REFRAME_REQUIRED`; it does not add a verdict or review branch.

The reviewer states the defect, decisive evidence, decision risk, required action, and checkable closure condition. It may give nonbinding directions but does not prescribe a single statistical or domain technique. The Designer records `accepted`, `adapted`, `rejected-with-evidence`, or `blocked` in the assigned detail. `frame-optimization` updates only the existing Repair status after the closure condition holds. A fresh readiness review occurs once after the complete repair set changes; no per-finding review is added.
