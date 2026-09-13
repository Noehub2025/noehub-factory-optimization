# A thin executable Batch path

Read when first implementing or changing Batch execution wiring. Reuse an established caller that already covers the needed behavior. This example is an executable usage reference, not a new execution API, mandatory fixture, or project migration.

[`batch_execution_example.py`](../scripts/batch_execution_example.py) reads a small retained sequence of status documents, stops at the first rejection, and saves the observed prefix through the existing Batch module. It is domain-neutral sample data, not an optimization experiment or a model of an external provider. The command below creates and removes its own temporary Git repository; it never opens a project B:

```sh
python <installed-skill-directory>/scripts/batch_execution_example.py --demo
```

## What to follow

- `execute()` is the example's actual caller. It reads the current candidate and Measurement Definition, installs the adapter, builds the Action, and invokes `Batch.perform`. Tests call this same function.
- `inspect_inputs()` is an optional earlier local availability query with its own query-only binding. It does not parse or consume the observation inputs and needs none of the later measurement's reviews or checks. Availability proves neither validity nor byte identity. Use this distinction when early facts can shape preparation; it is not a mandatory preflight, and remote or sensitive queries still need their own applicable access conditions.
- The caller implements the Coordinator's review selection under [Assurance by consequence](../../frontier-optimization/references/batch-evaluation.md#assurance-by-consequence), including applicable Workflow requirements. A report's recovery prose or role list is not another source of review policy; apply [Professional output and workflow decisions](../../frontier-optimization/references/worker-interfaces.md#professional-output-and-workflow-decisions). Follow [Review applicability and adoption](../../frontier-optimization/references/batch-current.md#review-applicability-and-adoption) through pre-Action checks and `GovernanceResolver`. The example passes selected handles directly, without inventing requirements or passing verdicts; retained R references alone are not gates.
- Retaining a nonpositive R does not force another report when its facts already support current use under [Finding effects](../../frontier-optimization/references/finding-effects.md). Preserve the original report and defect, select only the remaining necessary judgments, and pass that selection to the real caller. A retained advisory is not a claim that the defect was repaired; machine failures and important missing evidence still need resolution.
- `read_input()` is the replaceable leaf. Selected inputs are read at their saved Git revision. Without a selection, the example reads the retained local documents and claims no frozen-input guarantee. The parser, early-stop logic, result validation, adapter installation and Batch writeback stay real in integration tests.
- The optional `nonrepeatable_unit` in the example definition demonstrates a workflow-owned test unit, not a default for public data. When present, the same known effect is installed and declared; successful consumption is recorded in `OperationResult`. External or user-owned effects need their own applicable Permission and adapter.
- A negative observation is a completed operation with a shorter prefix, not an exception. A known parse failure records a failed support operation, its accepted prefix and the input that could not be interpreted. An unexpected reader interruption leaves the Attempt uncertain under the existing Batch behavior. Retained inputs survive; repairing a reader does not settle unknown effects or authorize a retry.
- `read_result()` reopens a settled observation or support failure without invoking the operation. The demo's Coordinator concludes B after reading the completed observation; the worker-side `execute()` does not conclude it.

The example does not prove project-specific review applicability, provider semantics, resource instrumentation, or performance. Keep those with their existing owners. Adapt only what the actual task needs; do not copy the example's status names, resource counter or repeatability choice into unrelated work.

## Focused verification

Run `test_batch_execution_example.py` when changing the executable example. It covers normal and early-negative writeback, selected Git inputs and checks, Review rejection, optional single-use consumption, known support failure, unknown execution and read-only result recovery. It uses disposable Git repositories and no external effects. For project callers, exercise their real assembly and affected writer/reader instead of treating this sample's passes as project readiness. A documentation-only correction needs inspection of its guidance and links, not an execution rerun.
