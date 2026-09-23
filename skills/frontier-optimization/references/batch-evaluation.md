# Current Batch measurement

Load only when current work invokes measurement or derives a result from completed measurement. The Batch-owned Measurement Definition fixes meaning; `Batch.perform` fixes the execution facts. Neither selects the next investment.

## Use one Measurement Definition

Before measurement, the Coordinator writes one current definition through `Batch.apply(ReviseBatch(...))`. It states:

- `mode`: `diagnostic-only`, `routine-local`, or `formal-slot-h`;
- question, comparator, metric and scope;
- resource ceiling and execution owner, using [Runtime records and resource use](batch-current.md#runtime-records-and-resource-use) for cumulative use, peak constraints and estimates;
- evidence and interpretation limits; and
- `result_owner`: `B` or `E`.

Use or reference the existing basis for [Evidence sufficient for the decision](../../frame-optimization/references/measurement-design.md#evidence-sufficient-for-the-decision), including the observation's stopping conditions and actual intended use. Keep decision-relevant value, lifecycle and context available to the adapter and [Result Adoption](result-adoption.md#preserve-meaning-through-the-use-path) using the existing definition and result structure. This adds no mandatory fields or separate evidence record.

Only when the Action or installed adapter declares `single_use_consumption`, also state `nonrepeatable_unit`, `resource_owner: workflow | user`, and `consumption_control`, and set `Action.repeatable: false`. Omit those fields when there is no real single-use unit; do not write `none`. Current writes use `nonrepeatable_unit`. Historical `non_repeatable_unit` remains readable, but two different alias values are invalid before the adapter starts.

Equivalent existing definitions remain usable even when their field names predate this guide. Instantiating a still-valid protocol or repairing its implementation follows [Measurement design and support](../../frame-optimization/references/measurement-work.md); only changed measurement meaning or a concrete challenge to its basis needs professional revision. Field renaming alone creates no migration or review.

An Action cannot supply another definition. `Batch.perform` reads the current one, binds it to the selected Git Candidate Revision and passing checks, checks applicable R, V and resource limits, then creates the consuming Attempt before the adapter begins.

## Run the selected mode

| Mode | Use | Maximum evidence produced by the Batch |
|---|---|---|
| `diagnostic-only` | A bounded observation that can change route, repair or measurement decisions | B evidence only |
| `routine-local` | A local screen of the current material under a reusable protocol | B evidence only |
| `formal-slot-h` | The parent-defined independent comparison | E only after comparison validity passes during Result Adoption |

The worker preserves the defined measurement question, sampling, comparison and interpretation, and records raw observations, actual use, actual Consequences, external references and recovery state in the Attempt. Correcting an implementation to realize that meaning uses [Batch continuation](batch-current.md#boundary-preserving-continuation), not a requirement to preserve erroneous program steps. Selected execution inputs, applicable Reviews and real user boundaries still govern each action. A mode determines evidence ownership and maximum use only. Repeatability comes from the actual action and resource; assurance comes from the next actual Consequence; Permission comes from user-owned boundaries. The Coordinator uses R8 and [Active learning chain](learning-loop.md#active-learning-chain) to continue work or reconsider investment after adoption. The worker does not create E, retain or promote a candidate, choose another B, or broaden the interpretation limit.

## Delayed and changing observations

The implementation owner realizes the selected observation conditions against the actual dependency. Handle its legitimate empty, pending and partially available responses as those states, preserving available facts and continuing only the observations worth obtaining within the applicable limits. Values and auxiliary evidence may arrive independently. A parsing or observation-support defect affects dependent interpretation, not an already established operation or object result; distinguish it from an attributable failure of the object being evaluated. Malformed or unrecognized responses retain their uncertainty rather than being silently treated as empty.

After a confirmed external effect, continue or repair observation of the same external reference through the existing permitted path, preserving past use and that effect. Observation recovery does not repeat the original mutation or restore consumed capacity. Reuse [Evidence at real boundaries](implementation-review.md#evidence-at-real-boundaries) to check the relevant transitions with existing outputs or dependency evidence, not a new live operation by default.

## Assurance by consequence

This is the shared method for choosing review work, not another approval stage. The Coordinator starts with the next actual use, not a list of review roles:

1. Use existing checks and the relevant professional owner's conclusions to identify a gap that matters to the current use under [Finding effects](finding-effects.md). Tools establish mechanical facts; professional owners interpret them. Reuse actual conclusions within their inputs and assumptions, including conclusions from another review kind.
2. Decide repair and independent review separately. A necessary mechanical correction needs its affected check, not automatically another reviewer. If the claimed consequence comes from an unsupported use of exploratory evidence, correct that use at its owner before choosing assurance; do not manufacture review necessity by giving a heuristic an unjustified route veto. Preserve consequences established by actual effects or applicable requirements. Continue when the current use is sufficiently supported, including with non-blocking defects. Select independent judgment only for a remaining important consequence of error, such as losing a valuable single-use observation or causing an irreversible effect, or where the current Workflow, an explicit user requirement or a verified external requirement requires it. An important unknown that the selected observation will test does not itself require prior review; distinguish it from a missing prerequisite for an interpretable answer. Permission remains separate.
3. Assign that question to the appropriate reviewer. In the existing scope and completion condition, name the intended use, reused conclusions and the question still to settle. A repair covers the change and affected dependencies; broaden it only when those effects cannot reasonably be isolated. Multiple reviewers address distinct questions, not a quota of roles. After adoption, continue the covered next action; another review needs its own unresolved question or applicable requirement.

A bounded, repeatable observation that remains B evidence normally uses focused checks and automatic result validation. Use `diagnostic-only` for such a remote observation rather than changing the meaning of `routine-local`. Location, price, a new file, commit or worker return does not decide assurance.

Use [Review applicability and adoption](batch-current.md#review-applicability-and-adoption) to carry the chosen judgments into execution and correct an obsolete stage requirement. Reuse and scope correction use the existing assignment or adoption record, not a waiver, approval or separate report proving that review is unnecessary.

## Protect an actual single-use unit

Apply this section only when the Action or adapter declares `single_use_consumption`. Use the narrowest control already present at the execution seam: the consuming Attempt, an exclusive output or slot key, or an external idempotency reference. Do not add a general lease, heartbeat, retry counter or global registry.

In the existing Measurement Definition, identify the actual resource or inferential property being protected and the event that consumes or exposes it. A complete schedule may be the unit when its sampling or resource meaning requires that scope. Reusable development conditions support an authorized run, retained feedback, repair and another run inside their evidence ceiling. A real call, public visibility or an earlier `single-use` label alone does not establish repeatability; the actual resource and intended inference do. An unrelated check or historical read does not consume a unit merely because it uses the same support.

If an internal definition overstated that property, its current owner revises the prospective definition through `ReviseBatch` and aligns the actual Action and installed `OperationBinding` or adapter before dependent execution. Base the change on the resource and intended evidence use, not on deleting a flag or renaming a unit. Ordinary repeatable exploration may continue in the same B when those real boundaries permit it. Keep terminal Attempts, recorded use and prior verdicts unchanged; the current revision rationale explains the corrected prospective treatment. It restores neither consumed capacity nor sample independence and never clears an unresolved effect. A documentation change alone does not repair an adapter that still enforces the old restriction.

- `resource_owner: workflow`: the Attempt and adapter control repetition; no V is needed merely because the unit is single-use.
- `resource_owner: user`: an applicable V must cover the private, scarce or unrecoverable resource before the adapter begins.

An unresolved Attempt blocks another `Batch.perform` in the same B, not ordinary `Batch.apply` work or another B. The same named unit remains blocked across Action-key changes while its prior Attempt is unresolved or records actual `single_use_consumption`. A reconciled failed Attempt with no such Consequence may retry when capacity remains.

## Reuse completed evidence

Deriving a result from recoverable, unchanged raw evidence creates no new measurement Attempt when measurement meaning and interpretation limits are unchanged and no new sampling or governed effect occurs. This applies after an operation starts or fails as well as before execution. A mechanical reader or validator repair may change program steps or derived output to implement that same meaning; it is not a change of measurement method. Check the affected derivation against the retained evidence, then use [Result Adoption](result-adoption.md#reuse-completed-evidence) to record the supported conclusion. No-rerun protects actual sampling and consumption, not inspection or corrected processing of its records. Correct an inherited restriction through its owner before dependent use; preserve unknown effects, original failures and any valid completeness requirement.

Changing the comparator, statistical method, sampling, scope or interpretation returns to the existing measurement owner and uses the normal current Measurement Definition and `Batch.perform` path. New runs may continue in the same B under its revised definition and real resource boundaries; neither a reader repair nor missing diagnostic information justifies inventing a complete result, dropping adverse observations, or treating repeated data as independent.

Development evidence may be reused adaptively for hypothesis generation, screening, ranking or selection when H and R8 allow that use. Record that exposure and keep its conclusion within the applicable ceiling. Adaptive reuse alone does not require independent confirmation or a new protocol; strengthen assurance only when the next actual Consequence requires independent evidence. An exact repeat that cannot change the pending decision is dominated and should not run.

Historical evaluation targets, experiment identities, acknowledgments, execution-start records and frozen result packets remain readable through [Historical Batch interface](batch-interface.md) and [Historical Batch result](batch-result.md). They are not current admission writers.
