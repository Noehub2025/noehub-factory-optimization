# Current Frontier Batch

Load this reference for a new B, current same-B continuation, routine progress, an action that may produce a result or Consequence, or current result adoption. Load [Historical Batch interface](batch-interface.md) or [Historical Batch result](batch-result.md) only when the actual retained record contains those legacy fields.

## Interface

`scripts/frontier_batch.py` is the current Batch module:

```text
Batch.open(B)
Batch.apply(RoutineChange)
Batch.perform(Action)
```

A Batch is one stable allocation of work toward one independently judged result. It is not a candidate identity, dispatch instance, command, process, immutable packet, or proposal hash. Its design, implementation, checks, paths, Review and Permission references, resource limits, and Candidate Revisions may evolve while it still pursues that result.

The current state machine is deliberately small:

```text
draft -> open -> completed | stopped
           |
           +-> Attempt 1, Attempt 2, ... only when repetition matters
```

Preparation, editing, local debugging, harmless checks, support repair, and a failed pre-execution transition remain ordinary work in the open Batch. They create no Attempt and no separate identity. A completed or stopped Batch may reopen only through an explicit same-result revision. Work that can be evaluated, stopped, or funded independently requires another B.

The module stores one current `frontier-batch/1` record. Git retains ordinary history. The record has no self-hash and no decision, authority, execution, outcome, packet, acknowledgment, start, result, validation, snapshot, inventory, or handoff identity.

## Ownership

| Owner | Owns | Batch use |
|---|---|---|
| Coordinator | Selection, reservations, protected reserve and allocation changes | Derive the Batch's local limits from the latest available allocation |
| Budget | Campaign-wide authorized total, reservations, actual and unknown consumption, and balance | Supplies allocation facts; Batch does not parse or copy the balance |
| R | Review subject, verdict, findings, reviewer and assumptions | Cite the applicable R; do not copy its meaning or create a review credential |
| V | User Permission, scope, conditions, value limits and withdrawal state | Cite the applicable V and check it immediately before its Consequence |
| Git | Retained project bytes and ordinary change history | Use a full commit and repository-relative paths |
| B | Current work state, Candidate Revision, checks, observations, Attempts, actual consumption, Consequences and result | The only current lifecycle owner |
| E | Adopted measurement meaning and claim limits | Adopt after B returns observations; B does not write E |
| External system | Its job, operation, submission, lease, object or idempotency reference | Preserve only when work crosses that real seam |

Review readiness does not grant Permission. Permission does not prove execution. Execution does not establish Evidence. Preserve those distinctions as fields and owner lookups rather than parallel identity chains.

## Apply routine changes

`Batch.apply` accepts only the closed set implemented by the module:

- define the initial Batch;
- revise the same independently judged result;
- select a Candidate Revision;
- record an ordinary check;
- record a routine observation; or
- reconcile one `running` or `uncertain` Attempt from observed facts; or
- conclude the Batch.

A revision may change design slices, implementation choices, commands, paths, checks, R or V references, resource limits, the current Candidate Revision, and one Batch-owned Measurement Definition. Record why it remains the same independently judged result. Do not create a new B merely because one field, file, design revision, tool, or workflow version changed.

Only the Coordinator may revise `resource_limits`. To increase a limit, first confirm or increase the matching Budget reservation, then revise the Batch. To decrease it, revise the Batch before releasing the reservation. `Batch.perform` records Attempt consumption before the Coordinator writes it back to Budget; do not make another dependent allocation until that writeback finishes. Protected reserve never becomes a Batch limit directly. Budget, reservation, Batch limit and actual use share the same resource keys and units.

A Candidate Revision is a full Git commit plus explicit repository-relative paths. One Batch may use several revisions. Changing bytes, repairing a failed check, or selecting another revision creates no candidate ID, inventory ID, package hash, Attempt, proposal, charge, Review, or Permission by itself.

Ordinary checks and observations bind the Candidate Revision they examined. A failed check returns to routine work. Checks whose execution would spend governed resources, access sensitive material, submit externally, make an irreversible change, consume a single-use sample, or create an independently retained measurement use `Batch.perform` instead.

## Boundary-preserving continuation

Continue the same B while it pursues the same independently judged result and remains inside the user's objective, permitted scope, applicable Permissions, actual cumulative limits, and known effects. A changed implementation plan, W slice allocation, internal work breakdown, local command order, Review revision, Permission update, resource ceiling, or Candidate Revision does not by itself create another B.

Working material stays mutable until exact bytes are selected for a check or action. Use Git to retain that selection. Do not copy the repository into execution snapshots or treat unrelated dirty paths, caches, workflow deployments, progress notes, or harmless local commands as input drift.

When practice disproves a load-bearing technical assumption, pause only dependent work and return the finding to the existing design owner. A revised design and applicable Review may continue in the same B when the independently judged result remains unchanged. When a local defect or support defect is repairable, repair and rerun only affected checks. Do not turn the defect into a new B, Generation, Permission, charge, or full review chain.

An unresolved actual effect, exhausted limit, unavailable required input, or repeated unchanged deterministic failure blocks only the affected action. State the observed fact and recovery condition. A finding, tool error, or process interruption does not close the B automatically.

## Perform an action

`Batch.perform` is the only current entry point that may start work capable of producing a measurement result or Consequence. A Consequence is actual spend, external submission, sensitive access, irreversible change, or single-use consumption whose repetition matters.

The Batch record is the sole current Measurement Definition owner. A measurement Action cannot carry or replace another definition. The current definition states the mode, question, comparator, metric, scope, resource ceiling, non-repeatable unit, resource owner, consumption control, execution owner, evidence and interpretation limits, and result owner. Existing definitions with equivalent meaning remain usable; do not create a schema-migration gate merely to rename fields.

Before the operation adapter starts, the Batch implementation:

1. resolves the current Batch;
2. verifies the selected Git commit and paths when bytes affect the result;
3. verifies required checks against that Candidate Revision;
4. reads applicable R and V from their owners;
5. checks every requested resource against Batch limits and only V-owned cost or resource keys against Permission limits;
6. rejects an unresolved or prohibited repeat; and
7. creates the next local Attempt only when measurement or possible Consequences make repetition matter.

After the adapter returns, record the Attempt, actual observations, actual consumption, actual Consequences, external references when present, result, and exact recovery condition. Never trust a declared zero after an operation may have begun. Unexpected adapter failure leaves the affected Attempt `uncertain` and forbids blind repetition; unrelated routine work remains legal.

When later facts resolve an uncertain operation, use `Batch.apply(ReconcileAttempt)` once to record the actual status, use, Consequences, result, and rationale. Reconciliation updates the existing Attempt; it does not create another Attempt, identity, Review, Permission, charge, or result packet. If an operation unexpectedly reports resource use or a Consequence without a planned Attempt, the module retains it as an Attempt and flags the adapter contract violation rather than dropping the effect.

A harmless synchronous operation may complete without an Attempt. A local serial operation normally uses `B/1`. A remote or asynchronous worker may use the provider's job or run reference inside the Attempt. Do not add local acknowledgment, start, execution or outcome IDs around that external reference.

Operation adapters sit behind the internal execution seam. Install each adapter through `OperationBinding`. The binding names the protected Consequences inherent to that seam so a caller cannot omit them. When the fixed or declared set includes external submission, sensitive access or irreversible change, `Batch.perform` requires applicable V coverage before invoking the adapter. A user-owned single-use unit receives the same treatment; a workflow-owned unit does not. The adapter still enforces its actual provider or physical boundary.

Add only the adapter and control required by the actual case:

| Actual seam | Additional control |
|---|---|
| Paid external call | Provider operation reference or idempotency key and cost limit |
| External submission | Exact artifact reference and provider submission reference |
| Sensitive access | Applicable V and provider audit reference when available |
| Irreversible action | Applicable V and one idempotent operation reference |
| Concurrent allocation | Scheduler reservation or lease reference |
| Remote or asynchronous worker | Provider job or run reference and exact input reference |
| External artifact | Existing store version or checksum and stable locator |
| Workflow-owned single-use sample | Slot key atomically bound to the consuming Attempt |
| User-owned private, scarce or unrecoverable sample | Applicable V plus the consuming Attempt and actual provider or storage control |

One elevated seam does not activate the others.

## Result and recovery

For an action that needed an Attempt, store its bounded action, exact Candidate Revision, required checks, observations, actual Consequences, actual resource use, result and recovery condition under that Attempt. The Attempt number is local to B, not a global identity. A harmless action may update routine observations without an Attempt.

- Record only evidence possible at the reached phase.
- Record actual consumption and Consequences even when the action failed or publication did not occur.
- Use `unknown` or `uncertain` when an effect cannot be established; never infer zero.
- Do not repeat an unresolved action until its recovery condition is satisfied.
- A failed check or failed Attempt does not create a new B or close the current B automatically.
- A result does not create E, select another route, promote a candidate, expand Permission, or establish a claim.

The Coordinator applies [Result adoption](result-adoption.md). E owns adopted measurement meaning and its claim limits. Concluding a Batch records `completed` or `stopped`, the strongest supported result and the remaining objective gap. An unresolved Attempt prevents conclusion. The same B may reopen only for explicit continuation of the same independently judged result; prior Attempts, consumption and Consequences remain unchanged.

## Historical compatibility

Old packet, preflight, acknowledgment, execution-start, result-packet, snapshot and typed provenance formats remain immutable historical records. Their existing validators are read-only compatibility adapters. They verify an old object under its recorded rules; they do not define the current writer.

When continuing historical work, project only still-valid work facts into the current Batch view. Preserve all old bytes. New changes under the same B use `frontier-batch/1` and never regenerate legacy roots, self-hashes, copied ancestry, packet identities, or result identities. A workflow update does not retrospectively re-review or rewrite a published result.

Compatibility is not a second active contract. If removing the historical adapter would change current writes or the current interface, the seam is leaking and must be repaired.
