# Evaluation protocol reuse and routine follow-up

Load this reference only when Entry may authorize code materialization followed by one low-cost local screen, when such a screen is being admitted, or when its result is adopted or recovered. This file owns that contract. Other references state only their local routing rule.

## Three evaluation modes

| Mode | When it runs | Maximum consequence |
|---|---|---|
| `diagnostic-only` | A bounded observation of unpublished working material inside its existing B, or the exact separate-B historical-candidate exception | B evidence only |
| `routine-local` | The one pre-authorized screen of the unique final candidate after a finding-free implementation review | B evidence only |
| `formal-slot-h` | Independent evaluation under the current Slot H contract | The exact reviewed Slot H consequence |

These modes are not interchangeable. A routine result does not create E, satisfy formal Slot H, confirm a candidate, authorize integration, select an incumbent, promote, submit, publish, support an external or paid action, approve a strength claim, or authorize another B.

## Reusable protocol capsule

`frontier-evaluation-protocol/1` is an ordinary project contract. It freezes:

- evaluator, harness, input and output schema, scoring rule, and environment;
- evaluation scope and the comparator, data, workload, and scenario distribution;
- sampling, seeds, seat or order balancing, metrics, uncertainty treatment, and exposure class;
- calibration requirements and one invalidation key derived from the preceding fields.

`frontier-protocol-calibration-result/1` records one calibration of that exact protocol: protocol identity and invalidation key, environment, controls, evidence manifest, results, and current drift status. Calibration establishes measurement validity only. It provides no candidate-performance evidence.

A candidate identity or campaign generation change does not invalidate the capsule. A change to evaluator behavior, harness, schema, scoring, environment, evaluation scope, comparator or scenario distribution, sampling, balancing, or observed drift does. Recalibrate only after an invalidating change. Do not rerun incumbent self-comparison for each new candidate.

For a composite Entry, include the exact protocol and calibration bytes in the complete `project-decision` content. This keeps provenance node version 4 recoverable without a second root or a reference to mutable live files.

## Composite Entry and single-use slot

Current composite Entry uses `frontier-project-batch-plan/3`. Its optional `frontier-routine-follow-up/1` authorizes, in one review and one user decision:

1. one exact code materialization B; and
2. at most one `routine-local` experiment B on that materialization's unique final candidate.

Freeze the slot ID, materialization B, future routine B, route, protocol, calibration, scientific question, canonical experiment source template, canonical runtime-input template, sample and local-resource ceilings, result contract and paths, stop conditions, action window, Budget boundary, reserve rule, and every prohibited consequence. Every resource-ceiling key is nonempty and every limit is finite, numeric, and positive. Only these candidate fields remain unresolved: `candidate.id`, `candidate.manifest_sha256`, and `candidate.collection_root`. The writer derives them; a caller never supplies them as authority. The writer binds those fields into the source template, derives the omit-line experiment identity and full-file digest, and then requires the frozen experiment and runtime-input bytes to match exactly.

The protocol, calibration, slot, and full experiment template are reviewed in the original Entry. The later implementation review is not a second Entry gate. Its only role is to establish, in a fresh context, that the exact derived candidate is `IMPLEMENTATION_READY` without block or repair findings.

An Entry without a routine follow-up remains valid. Independent sealed confirmation and formal Slot H use their existing complete Entry and review gates.

## Admission through the only execution writer

There is no standalone admission command. `freeze_execution` recognizes `routine-local` and performs the following checks before it creates the execution node:

1. Reproduce the current complete Entry decision, ready attestation, authority, live facts, action window, Budget, reservation, inputs, and resources.
2. Read the reviewed routine slot and experiment template from the Entry projection.
3. Follow the exact materialization execution and terminal outcome under that authority. Derive one final candidate manifest, identity, and closed collection. Reject no outcome, multiple outcomes, caller-selected identities, or byte drift.
4. Reproduce the unique finding-free implementation review for that candidate.
5. Bind only the three allowed candidate fields into the reviewed template. Reject any other template change.
6. Resolve one content-addressed `frontier-routine-live-receipt/1` bound to the decision, authority, slot, template, Budget identity, reservation identity, numeric unprotected balance, reserve state, and action window. Reject a request summary that differs from that receipt, exhausted Budget, any protected-reserve use, prior sampling, or a closed window.
7. Atomically record `slot_id -> execution_root` in the only consumption index derived from the canonical provenance repository. The command accepts no alternate index path.

The slot index is not authority. Canonical execution and frozen project-state bytes remain authoritative. The first atomic slot consumption is the only call that may release an execution. Every later release attempt fails, including an identical call made before the first node is saved. Recovery rebuilds the index from canonical executions; it never grants a second release.

## Routine project-state closure and recovery

Because provenance node version 4 gives an execution only its authority parent, the routine `project-state` content must carry all late prerequisites needed offline:

- final candidate manifest and closed candidate collection;
- canonical materialization execution and outcome nodes plus the terminal result proof;
- canonical implementation-review decision and attestation nodes, review input, and report;
- final experiment contract, admission record, runtime inputs, and the live receipt roots used at admission.

The original Entry ancestry already carries protocol and calibration bytes; do not duplicate them. The state does not need another copy of the whole ledger, log, `FRONTIER.md`, parent documents, or Entry review prose.

Handoff cites the otherwise non-parent-reachable materialization outcome, implementation decision, and live receipt roots named by routine admission. It reconstructs slot consumption from retained execution nodes and admission bytes. Missing required content, missing embedded nodes, unresolved references, incomplete closed collections, or two executions for one slot block the dependent recovery action. Storage and historical reads follow [Provenance, Git, and retained artifacts](provenance-and-identity.md); the handoff does not copy those inputs again.

## Structured evidence ceiling

Every `routine-local` target and completed result carries the same exact structured scope:

```yaml
evidence_class: b-evidence
exposure: development
confirmation: none
comparator_scope: <exact comparator set>
data_scope: <exact data or sample set>
workload_scope: <exact workload set>
scenario_scope: <exact scenario set>
metric_scope: <exact metric set>
mechanism_grain: whole-package-at-most
transfer_scope: local-only
```

Derive conclusions from these fields, not from persuasive prose. One comparator supports only comparator-relative evidence. Missing structured parent scope supports only a local observation. Calibration supports only measurement-validity statements. A whole-package result does not attribute effect to one component.

When measurement completes, the single routine result item contains only measured scalar observations (`metric`, finite numeric or boolean `value`, `unit`, and positive `sample_count` no greater than the Entry ceiling), the exact evidence scope, and `maximum_consequence: B evidence only`. If the action is blocked, fails, or waits for input before measurement, record no result item, use the exact no-observation summary, and preserve the technical blocker in `failed_checks`; never invent an observation. Execution-result narrative and `possible_follow_up` are forbidden. Generic planning, recovery, validation, prerequisite, and scope-deviation fields stay at their exact neutral values; they cannot carry promotion, publication, or next-B instructions. After validation, adopt the result as the routine B's terminal evidence and run the integrated resolver once on the new evidence state. The routine result does not choose or authorize its own follow-up.

## Version support and cutover

The exact historical combination `frontier-review-subject/1`, `frontier-review-role-adapter/1`, `frontier-project-batch-plan/2`, and `frontier-batch-result/1` remains readable only for audit. Current writing and runtime use subject `/2`, role adapter `/2`, plan `/3`, evaluation target `/2`, and result `/2`. Historical audit readability does not make an old or mixed combination eligible for a new current review, authority, execution, or result adoption.

Apply current workflow rules to the next affected action under [Change impact and retained results](frontier-core.md#change-impact-and-retained-results). Installing or updating the runtime does not require ending unaffected active chains. When the next action genuinely needs a current contract that its retained object cannot supply, preserve the old object and prepare only that affected current decision under applicable permission. Do not reinterpret an old implementation review as current readiness or build a general migration layer.
