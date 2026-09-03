# Current Batch measurement

Load only when current work invokes measurement or derives a result from completed measurement. The Batch-owned Measurement Definition fixes meaning; `Batch.perform` fixes the execution facts. Neither selects the next investment.

## Use one Measurement Definition

Before measurement, the Coordinator writes one current definition through `Batch.apply(ReviseBatch(...))`. It states:

- `mode`: `diagnostic-only`, `routine-local`, or `formal-slot-h`;
- question, comparator, metric and scope;
- resource ceiling and the non-repeatable unit;
- `resource_owner`: `workflow` or `user`, plus its consumption control and execution owner;
- evidence and interpretation limits; and
- `result_owner`: `B` or `E`.

Equivalent existing definitions remain usable even when their field names predate this guide. Update meaning only when the intended measurement changes; do not create a migration or review merely to rename fields.

An Action cannot supply another definition. `Batch.perform` reads the current one, binds it to the selected Git Candidate Revision and passing checks, checks applicable R, V and resource limits, then creates the consuming Attempt before the adapter begins.

## Run the selected mode

| Mode | Use | Maximum evidence produced by the Batch |
|---|---|---|
| `diagnostic-only` | A bounded observation that can change route, repair or measurement decisions | B evidence only |
| `routine-local` | A local screen of the current reviewed material under a reusable protocol | B evidence only |
| `formal-slot-h` | The parent-defined independent comparison | E only after comparison validity passes during Result Adoption |

The worker runs only the fixed method and records raw observations, actual use, actual Consequences, external references and recovery state in the Attempt. These limits describe evidence ownership, not investment permission: R8 and the integrated resolver decide how adopted evidence may affect later work. The worker does not create E, retain or promote a candidate, choose another B, or broaden the interpretation limit.

## Protect the actual non-repeatable unit

Use the narrowest control already present at the execution seam: the consuming Attempt, an exclusive output or slot key, or an external idempotency reference. Do not add a general lease, heartbeat, retry counter or global registry.

- `resource_owner: workflow`: the Attempt and adapter control repetition; no V is needed merely because the unit is single-use.
- `resource_owner: user`: an applicable V must cover the private, scarce or unrecoverable resource before the adapter begins.

An uncertain unit cannot be rerun until observed facts prove the effect did not start, prove retry is safe, or reconcile the original Attempt. Unrelated routine work and unclaimed units remain legal when the definition permits them.

## Reuse completed evidence

Deriving a result from already completed measurement creates no new measurement Attempt when it reads unchanged raw evidence, uses unchanged semantics and performs no governed effect. Result Adoption records the derived meaning and its limits. Any new sampling, changed comparator, changed interpretation or effect uses a normal current Measurement Definition and `Batch.perform`.

Historical evaluation targets, experiment identities, acknowledgments, execution-start records and frozen result packets remain readable through [Historical Batch interface](batch-interface.md) and [Historical Batch result](batch-result.md). They are not current admission writers.
