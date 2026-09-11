# A thin executable Batch path

Read when first implementing or changing Batch execution wiring. Reuse an established caller that already covers the needed behavior. This example is an executable usage reference, not a new execution API, mandatory fixture, or project migration.

[`batch_execution_example.py`](../scripts/batch_execution_example.py) reads a small retained sequence of status documents, stops at the first rejection, and saves the observed prefix through the existing Batch module. It is domain-neutral sample data, not an optimization experiment or a model of an external provider. The command below creates and removes its own temporary Git repository; it never opens a project B:

```sh
python <installed-skill-directory>/scripts/batch_execution_example.py --demo
```

## What to follow

- `execute()` is the example's actual caller. It reads the current candidate and Measurement Definition, installs the adapter, builds the Action, and invokes `Batch.perform`. Tests call this same function.
- The caller receives only the Review and check handles needed for this action under [Assurance by consequence](../../frontier-optimization/references/batch-evaluation.md#assurance-by-consequence), not every retained R. Existing `GovernanceResolver` and Batch checks judge applicability. The example selects no professional requirements or passing verdicts; an observation can proceed with an empty required list while historical R references remain saved.
- `read_input()` is the replaceable leaf. Selected inputs are read at their saved Git revision. Without a selection, the example reads the retained local documents and claims no frozen-input guarantee. The parser, early-stop logic, result validation, adapter installation and Batch writeback stay real in integration tests.
- The optional `nonrepeatable_unit` in the example definition demonstrates a workflow-owned test unit, not a default for public data. When present, the same known effect is installed and declared; successful consumption is recorded in `OperationResult`. External or user-owned effects need their own applicable Permission and adapter.
- A negative observation is a completed operation with a shorter prefix, not an exception. A known parse failure records a failed support operation, its accepted prefix and the input that could not be interpreted. An unexpected reader interruption leaves the Attempt uncertain under the existing Batch behavior. Retained inputs survive; repairing a reader does not settle unknown effects or authorize a retry.
- `read_result()` reopens a settled observation or support failure without invoking the operation. The demo's Coordinator concludes B after reading the completed observation; the worker-side `execute()` does not conclude it.

The example does not prove project-specific review applicability, provider semantics, resource instrumentation, or performance. Keep those with their existing owners. Adapt only what the actual task needs; do not copy the example's status names, resource counter or repeatability choice into unrelated work.

## Focused verification

Run `test_batch_execution_example.py` when changing this example. It covers normal and early-negative writeback, selected Git inputs and checks, Review rejection, optional single-use consumption, known support failure, unknown execution and read-only result recovery. It uses disposable Git repositories and no external effects. For project callers, exercise their real assembly and affected writer/reader instead of treating this sample's passes as project readiness.
