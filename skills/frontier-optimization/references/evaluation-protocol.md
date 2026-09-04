# Evaluation protocol reuse

Load only when a current Measurement Definition reuses a calibrated protocol or when protocol meaning may have changed. Execution always enters through [Current Batch measurement](batch-evaluation.md), not through a separate admission writer.

## Reuse rule

A protocol may be reused while its inferential target, comparator role, metric, data or workload distribution, balancing, uncertainty method, controls, runtime assumptions and interpretation limits remain applicable. Candidate changes alone do not require recalibration or another user decision.

Calibrate once per protocol version when calibration can change whether results are interpretable. Repeat calibration only after a relevant protocol, evaluator, environment or control change, or concrete evidence that the calibration no longer holds. A self-comparison, smoke schedule or other control contributes only the information it actually measures.

## Current modes

- `diagnostic-only` answers one bounded decision question and produces B evidence.
- `routine-local` applies a reusable local screen to the current material and produces B evidence.
- `formal-slot-h` applies the parent-defined comparison and may produce E only after Result Adoption establishes comparison validity.

All three modes use the Batch-owned Measurement Definition, Attempt and actual resource accounting. Mode determines evidence use only; it does not make an action repeatable or single-use, trigger Review, or create Permission. A protocol reference may identify shared method meaning, but it does not own execution, Permission, candidate bytes, results or a single-use slot.

## Structured evidence ceiling

The Measurement Definition states the exact evidence and interpretation limits. At minimum, preserve:

- what subjects, comparators, conditions and observations were included;
- what uncertainty and controls the result actually covers;
- what exposure, workload, data, scale or opponent distribution it does not cover;
- whether development evidence was adaptively reused; and
- which later decision the result may change.

A routine or diagnostic result cannot satisfy formal comparison validity, establish general improvement, support promotion or authorize another action. A formal result cannot exceed its parent measurement and claim limits.

## Single-use units

Only when the Action or adapter declares `single_use_consumption`, the Measurement Definition names `nonrepeatable_unit`, its `resource_owner`, and `consumption_control`; otherwise those fields are absent. `Batch.perform` binds the actual unit to the consuming Attempt before the effect and rejects reuse across Action-key changes. Workflow-owned units need no V merely because they are single-use. User-owned private, scarce or unrecoverable units require applicable V coverage.

Historical `evaluation_target`, `freeze_execution`, live-receipt and slot-index contracts remain read-only compatibility data. Do not use them to admit a current measurement.
