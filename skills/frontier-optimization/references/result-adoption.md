# Frontier Result Adoption

Load only after a worker result exists, when freezing or adopting a materialized-candidate review, or when validating and appending E. This file is the sole action contract for turning worker evidence into Coordinator-owned result meaning.

## Contents

- [Validate and disposition the result](#validate-and-disposition-the-result)
- [Review a materialized candidate](#review-a-materialized-candidate)
- [Adopt diagnostic-only evidence](#adopt-diagnostic-only-evidence)
- [Adopt routine-local evidence](#adopt-routine-local-evidence)
- [Adopt valid measurement as E](#adopt-valid-measurement-as-e)
- [Completion](#completion)

## Validate and disposition the result

Rerun `validate_batch_result.py` in frozen mode against the exact packet and require byte-identical output to the assigned result-validation artifact. Validate packet identity, acknowledgment, execution baseline, execution start, lifecycle transition, parent bindings, scope, outputs, recovery, actual spend, accounting, failed checks, deviations, and prohibited actions. For W-backed work, also validate the exact revision, permitted worker append surfaces, concern identities, and human-input contract. For code, validate the complete design, authorization, materialization, and review boundaries in [Candidate lifecycle](candidate-lifecycle.md).

Append one B terminal-outcome block from [Planning records](planning-records.md) for `completed`, `interrupted`, `failed`, or `blocked`; `waiting_for_input` is a durable pause. Preserve the immutable result and its validation, accepted and rejected output, recovery, deviations, reservation, and actual spend. Preserve an invalid immutable legacy result only as diagnostic evidence and use a new authorized attempt rather than rewriting it.

For every outcome, reconcile the worker's actual spend with the existing accounting source under [Charging and publication](batch-interface.md#charging-and-publication). A structural validator PASS is not a project budget verdict. After checking worker evidence, update only Coordinator-owned W lifecycle, recovery, and outcome surfaces. A contract-bearing W change creates a new revision and invalidates dependent review and authorization. When `actual_spend: unknown`, mark remaining budget unresolved and block new spend.

## Review a materialized candidate

For a recoverable materialized candidate, verify the packet or current project plan, authorization order, acknowledgment, execution-baseline bytes, execution start, W and concern identities when used, design review, development V, source base, changed paths, cumulative attempts, positive prepublication implementation review, official inventory, engineering evidence, final manifest, frozen result validation, result, write ownership, accounting reconciliation, and recovery point before appending the B terminal outcome.

Require the official inventory identity to equal the final positively reviewed transient inventory. Reconcile its publication with the actual event using Charging and publication above; an equal inventory is not evidence that a repeated proposal or resource use is free.

Adopt the unchanged `IMPLEMENTATION_READY` already bound by the final manifest and result; do not create another implementation review after publication. Its maximum consequence is eligibility for a separately selected measurement or integration B. A nonpositive prepublication review either returned to fidelity repair inside the same B or ended the B without a candidate. A later finding against an already published candidate follows the normal post-publication resolver and new-B path; it cannot reopen the prepublication loop.

If no realization reached implementation review, record it as not applicable. If a nonpositive prepublication review ended the B without publication, preserve that actual review result as terminal evidence for the resolver and eventual Generation Reflection.

## Adopt diagnostic-only evidence

Do not enter result adoption merely because one bounded working observation completed. Keep sequential observations cumulative inside the existing nonterminal B under [Batch Interface](batch-interface.md#bounded-observations-before-publication); they do not individually create a terminal outcome, resolver run, or successor B. When that B later terminates, validate its cumulative observations and effects with its ordinary terminal result.

For an experiment selected through the [diagnostic-only exception](candidate-lifecycle.md#diagnostic-only-exception), validate its Entry authority, candidate and experiment identities, local isolation, hard-constraint checks, sealed-evidence exclusion, maximum spend, result validation, and prohibited consequences. Append the B terminal outcome. Preserve the result only as diagnostic B evidence; create no E and grant no implementation readiness, integration, incumbent use, promotion, submission, or strength consequence.

A useful diagnostic may select a later implementation review, repair, abandonment, or formal Slot H experiment plan. It cannot make its own measurement comparison-valid or bypass any later gate.

## Adopt routine-local evidence

For `evaluation_target.mode: routine-local`, rerun the shared target and result validator, reproduce admission through the original Entry authority, and require the exact consumed slot, derived candidate, finding-free implementation review, unchanged protocol and calibration, current live facts, unprotected Budget, and frozen experiment template. Enforce the structured evidence scope in [Evaluation protocol reuse](evaluation-protocol.md#structured-evidence-ceiling).

Append only the routine B terminal outcome. Create no E. The result cannot satisfy formal Slot H, confirm or promote the candidate, authorize integration or incumbent use, support submission, publication, external or paid action, approve a claim, or directly authorize the next B. Run the integrated resolver once on the new evidence state.

## Adopt valid measurement as E

Implementation and formal Slot H evaluation use separate B records. A Slot H evaluation B uses `work_kind: experiment`, `changes_executable_candidate: false`, one immutable candidate and manifest, adopted unchanged `IMPLEMENTATION_READY`, and a precomputed experiment identity binding evaluator, data, controls, protocol, environment, budget, campaign generation, and result paths.

After the evaluation B terminates, validate candidate and experiment identities, unchanged implementation review, Slot H output, legality, uncertainty, operating cost, data quality, comparable conditions, drift, confounding, execution checks, and result artifacts. Append E from [Planning records](planning-records.md) only when the measurement and comparison validity satisfy the parent Slot H contract. Invalid, failed, interrupted, or ambiguous measurement remains B evidence and creates no E.

E records evaluated evidence, not automatic retention or promotion. Before promotion, compare E with every active applicable D and tolerance. An unresolved contradiction blocks promotion, incumbent use, claim strengthening, and dependent spend until a diagnostic supports an X disposition.

## Completion

Result adoption is complete only when the immutable result and validation remain recoverable, B outcome and spend are dispositioned, any materialized candidate has an adopted review or an explicit prohibition on later use, and every valid measurement has an E disposition. Worker output never creates E or campaign meaning by itself. The next investment, stop, or blocker comes from one resolver run on this adopted evidence state.
