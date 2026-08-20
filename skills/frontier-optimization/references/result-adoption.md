# Frontier Result Adoption

Load only after a worker result exists, when freezing or adopting a materialized-candidate review, or when validating and appending E. This file is the sole action contract for turning worker evidence into Coordinator-owned result meaning.

## Contents

- [Validate and disposition the result](#validate-and-disposition-the-result)
- [Review a materialized candidate](#review-a-materialized-candidate)
- [Adopt diagnostic-only evidence](#adopt-diagnostic-only-evidence)
- [Adopt valid measurement as E](#adopt-valid-measurement-as-e)
- [Completion](#completion)

## Validate and disposition the result

Rerun `validate_batch_result.py` in frozen mode against the exact packet and require byte-identical output to the assigned result-validation artifact. Validate packet identity, acknowledgment, execution baseline, execution start, lifecycle transition, parent bindings, scope, outputs, recovery, actual spend, accounting, failed checks, deviations, and prohibited actions. For W-backed work, also validate the exact revision, permitted worker append surfaces, concern identities, and human-input contract. For code, validate the complete design, authorization, materialization, and review boundaries in [Candidate lifecycle](candidate-lifecycle.md).

Append one B terminal-outcome block from [Planning records](planning-records.md) for `completed`, `interrupted`, `failed`, or `blocked`; `waiting_for_input` is a durable pause. Preserve the immutable result and its validation, accepted and rejected output, recovery, deviations, reservation, and actual spend. Preserve an invalid immutable legacy result only as diagnostic evidence and use a new authorized attempt rather than rewriting it.

After checking worker evidence, update only Coordinator-owned W lifecycle, recovery, and outcome surfaces. A contract-bearing W change creates a new revision and invalidates dependent review and authorization. When `actual_spend: unknown`, mark remaining budget unresolved and block new spend.

## Review a materialized candidate

For a recoverable materialized candidate, first append the B terminal outcome. Then verify the packet preflight, authorization order, packet, acknowledgment, execution-baseline bytes, execution start, lifecycle transition, frozen result validation, W and concern identities when used, design review, development V, source base and result, changed paths, manifest, recomputed candidate identity, configuration, dependencies, engineering evidence, write ownership, and recovery point.

Create a new immutable implementation snapshot through [Review snapshots](review-snapshots.md), create one versioned packet from [Implementation review](implementation-review.md), and invoke fresh-context `review-frontier`. Preserve every verdict. Adopt only a finding-free unchanged `IMPLEMENTATION_READY`; its maximum consequence is eligibility for a separately selected measurement or integration B. A nonpositive review preserves the candidate as evidence and grants no measurement, integration, incumbent, promotion, or claim authority. The verdict does not decide campaign scope. The controlling Outcome Reflection and integrated resolver map the findings through R8 to the smallest supported candidate, route, or campaign disposition. When `IMPLEMENTATION_REPAIR_REQUIRED` affects only the exact candidate under an unchanged usable design, route, allocation, and parent, preserve that surviving authority and let the resolver consider a new in-generation repair B with a new candidate identity, authorization, and proposal charge.

If no candidate materialized, record implementation review as not applicable and reflect on the failure or interruption. Include the actual review result in the B's Outcome Reflection.

## Adopt diagnostic-only evidence

For an experiment selected through the [diagnostic-only exception](candidate-lifecycle.md#diagnostic-only-exception), validate its Entry authority, candidate and experiment identities, local isolation, hard-constraint checks, sealed-evidence exclusion, maximum spend, result validation, and prohibited consequences. Append the B terminal outcome and one controlling Outcome Reflection. Preserve the result only as diagnostic B evidence; create no E and grant no implementation readiness, integration, incumbent use, promotion, submission, or strength consequence.

A useful diagnostic may select a later implementation review, repair, abandonment, or formal Slot H experiment plan. It cannot make its own measurement comparison-valid or bypass any later gate.

## Adopt valid measurement as E

Implementation and formal Slot H evaluation use separate B records. A Slot H evaluation B uses `work_kind: experiment`, `changes_executable_candidate: false`, one immutable candidate and manifest, adopted unchanged `IMPLEMENTATION_READY`, and a precomputed experiment identity binding evaluator, data, controls, protocol, environment, budget, campaign generation, and result paths.

After the evaluation B terminates, validate candidate and experiment identities, unchanged implementation review, Slot H output, legality, uncertainty, operating cost, data quality, comparable conditions, drift, confounding, execution checks, and result artifacts. Append E from [Planning records](planning-records.md) only when the measurement and comparison validity satisfy the parent Slot H contract. Invalid, failed, interrupted, or ambiguous measurement remains B evidence and creates no E.

E records evaluated evidence, not automatic retention or promotion. Before promotion, compare E with every active applicable D and tolerance. An unresolved contradiction blocks promotion, incumbent use, claim strengthening, and dependent spend until a diagnostic supports an X disposition.

## Completion

Result adoption is complete only when the immutable result and validation remain recoverable, B outcome and spend are dispositioned, any materialized candidate has an adopted review or an explicit prohibition on later use, every valid measurement has an E disposition, and the exact next required Outcome Reflection is named. Worker output never creates E or campaign meaning by itself.
