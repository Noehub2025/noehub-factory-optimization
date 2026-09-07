# Current Batch measurement

Load only when current work invokes measurement or derives a result from completed measurement. The Batch-owned Measurement Definition fixes meaning; `Batch.perform` fixes the execution facts. Neither selects the next investment.

## Use one Measurement Definition

Before measurement, the Coordinator writes one current definition through `Batch.apply(ReviseBatch(...))`. It states:

- `mode`: `diagnostic-only`, `routine-local`, or `formal-slot-h`;
- question, comparator, metric and scope;
- resource ceiling and execution owner;
- evidence and interpretation limits; and
- `result_owner`: `B` or `E`.

Only when the Action or installed adapter declares `single_use_consumption`, also state `nonrepeatable_unit`, `resource_owner: workflow | user`, and `consumption_control`, and set `Action.repeatable: false`. Omit those fields when there is no real single-use unit; do not write `none`. Current writes use `nonrepeatable_unit`. Historical `non_repeatable_unit` remains readable, but two different alias values are invalid before the adapter starts.

Equivalent existing definitions remain usable even when their field names predate this guide. Update meaning only when the intended measurement changes; do not create a migration or review merely to rename fields.

An Action cannot supply another definition. `Batch.perform` reads the current one, binds it to the selected Git Candidate Revision and passing checks, checks applicable R, V and resource limits, then creates the consuming Attempt before the adapter begins.

## Run the selected mode

| Mode | Use | Maximum evidence produced by the Batch |
|---|---|---|
| `diagnostic-only` | A bounded observation that can change route, repair or measurement decisions | B evidence only |
| `routine-local` | A local screen of the current material under a reusable protocol | B evidence only |
| `formal-slot-h` | The parent-defined independent comparison | E only after comparison validity passes during Result Adoption |

The worker runs only the fixed method and records raw observations, actual use, actual Consequences, external references and recovery state in the Attempt. A mode determines evidence ownership and maximum use only. Repeatability comes from the actual action and resource; assurance comes from the next actual Consequence; Permission comes from user-owned boundaries. R8 and the integrated resolver decide how adopted evidence may affect later work. The worker does not create E, retain or promote a candidate, choose another B, or broaden the interpretation limit.

## Assurance by consequence

Use the least assurance that makes the next actual Consequence reliable. Choose independent technical judgment from the consequences of a support error and what existing checks already establish, not from the labels local, remote, free, paid, or measurement. A bounded, repeatable observation that remains B evidence normally needs focused checks and automatic result validation, not independent Review; applicable Permission is still required. Use `diagnostic-only` for such a remote observation rather than changing the meaning of `routine-local`.

Keep the independent judgments required for formal E, promotion, publication, integration, or an explicit adopted gate. For other work, require independent Review only when existing checks do not sufficiently address a material consequence of error, such as invalidating a valuable single-use observation or causing an irreversible effect. Permission for that effect and technical assurance are separate decisions. Equal material consequences need equal assurance regardless of execution location or price. Reuse sufficient evidence and applicable reviews; do not add a risk score, waiver, or another approval step.

## Protect an actual single-use unit

Apply this section only when the Action or adapter declares `single_use_consumption`. Use the narrowest control already present at the execution seam: the consuming Attempt, an exclusive output or slot key, or an external idempotency reference. Do not add a general lease, heartbeat, retry counter or global registry.

In the existing Measurement Definition, identify the actual resource or inferential property being protected and the event that consumes or exposes it. A complete schedule may be the unit when its sampling or resource meaning requires that scope; an unrelated development check or historical read does not consume it merely because it uses the same support. Revise an overbroad internal definition through its current owner before the affected action, preserving actual consumption and unresolved effects. A changed definition never releases a consumed unit or clears an uncertain Attempt by itself.

- `resource_owner: workflow`: the Attempt and adapter control repetition; no V is needed merely because the unit is single-use.
- `resource_owner: user`: an applicable V must cover the private, scarce or unrecoverable resource before the adapter begins.

An unresolved Attempt blocks another `Batch.perform` in the same B, not ordinary `Batch.apply` work or another B. The same named unit remains blocked across Action-key changes while its prior Attempt is unresolved or records actual `single_use_consumption`. A reconciled failed Attempt with no such Consequence may retry when capacity remains.

## Reuse completed evidence

Deriving a result from already completed measurement creates no new measurement Attempt when it reads unchanged raw evidence, uses unchanged semantics and performs no governed effect. Result Adoption records the derived meaning and its limits. Any new sampling, changed comparator, changed interpretation or effect uses a normal current Measurement Definition and `Batch.perform`.

Reading retained evidence is not resampling. Repairing a mechanical reader or validator may use this unchanged-evidence path; changing what the observations mean returns to the measurement owner and must not be disguised as mechanical repair. No-rerun protects actual sampling and consumption, not the ability to inspect their records.

Development evidence may be reused adaptively for hypothesis generation, screening, ranking or selection when H and R8 allow that use. Record that exposure and keep its conclusion within the applicable ceiling. Adaptive reuse alone does not require independent confirmation or a new protocol; strengthen assurance only when the next actual Consequence requires independent evidence. An exact repeat that cannot change the pending decision is dominated and should not run.

Historical evaluation targets, experiment identities, acknowledgments, execution-start records and frozen result packets remain readable through [Historical Batch interface](batch-interface.md) and [Historical Batch result](batch-result.md). They are not current admission writers.
