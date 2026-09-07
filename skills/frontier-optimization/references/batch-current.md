# Current Frontier Batch

Load this reference for a new B, current same-B continuation, routine progress, an action that may produce a result or Consequence, or current result adoption. Load [Historical Batch interface](batch-interface.md) or [Historical Batch result](batch-result.md) only when the actual retained record contains those legacy fields.

## Interface

`scripts/frontier_batch.py` is the current Batch module:

```text
Batch.open(B)
Batch.apply(RoutineChange)
Batch.perform(Action)
```

A Batch is one stable allocation of work toward one independently judged result. It is not a candidate identity, dispatch instance, command, process, immutable packet, or proposal hash. Its design, implementation, checks, paths, Review and Permission references, operational limits, and Candidate Revisions may evolve while it still pursues that result.

Write `acceptance` as the result and evidence required to judge this B, and `scope` as its work boundary. Keep a temporary turn limit in current progress, not in acceptance as an inferred user stop. Real user limits come from [User decisions](user-decisions.md). Finishing an implementation-only B can lead to a separate measurement B within the continuing task; it does not enlarge this B's independently judged result.

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
| Coordinator | Selection, reservations, protected reserve and allocation changes | Set and revise the Batch's operational limits from current evidence inside governing boundaries |
| Budget | Campaign-wide authorized total, reservations, actual and unknown consumption, and balance | Supplies allocation facts; Batch does not parse or copy the balance |
| R | Review subject, verdict, findings, reviewer and assumptions | Cite the applicable R; do not copy its meaning or create a review credential |
| V | User Permission, scope, conditions, value limits and withdrawal state | Cite the applicable V and check it immediately before its Consequence |
| Git | Retained project bytes and ordinary change history | Use a full commit and repository-relative paths |
| B | Current work state, Candidate Revision, checks, observations, Attempts, actual consumption, Consequences and result | The only current lifecycle owner |
| E | One adopted formal evaluated result and its comparison validity | Create only after a valid `formal-slot-h` result; B does not write E |
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

A revision may change design slices, implementation choices, commands, paths, checks, R or V references, Batch operational limits, the current Candidate Revision, and one Batch-owned Measurement Definition. Record why it remains the same independently judged result. Do not create a new B merely because one field, file, design revision, tool, or workflow version changed.

Only the Coordinator may revise `resource_limits`. These are Batch operational limits, not Campaign Budget or proof of consumption. The Coordinator may raise or lower them in the same B without user input, another Selection, or Replan when the independently judged result, strategic allocation, protected reserve, Measurement Definition meaning and all governing boundaries remain unchanged. Create or increase a Campaign reservation only when governed capacity must stay unavailable to another allocation before Attempt writeback. `Batch.perform` records Attempt use first; write only Budget-governed keys back to Campaign Budget and disposition any matching reservation before another dependent allocation. A protected reserve never becomes a Batch limit directly.

A Candidate Revision is a full Git commit plus explicit repository-relative paths. One Batch may use several revisions. Changing bytes, repairing a failed check, or selecting another revision creates no candidate ID, inventory ID, package hash, Attempt, proposal, charge, Review, or Permission by itself.

Ordinary checks and observations bind the Candidate Revision they examined. A failed check returns to routine work. Checks whose execution would spend governed resources, access sensitive material, submit externally, make an irreversible change, consume a single-use sample, or create an independently retained measurement use `Batch.perform` instead.

## Review applicability and adoption

An R and its subject remain the versions saved in Git. The current Batch records subsequent adoption and progress. `GovernanceResolver.review(reference, action)` reads the saved R and judges whether its conclusions and assumptions cover the proposed action; it is a read-only lookup, not a review writer. Compare relevant decision meaning and selected inputs, not the whole current `batch.yaml` against either the reviewed file or a reconstructed post-adoption file.

Adopting an R, updating a rationale, or recording progress does not invalidate that R. Revised operational caps follow the existing rule above. A change to behavior, acceptance, measurement meaning, or reviewed implementation requires reconsidering only the affected conclusions. Keep this judgment in the existing owner resolver; do not introduce a generic field whitelist or another review-validity registry.

Fixed action inputs retain their existing version checks. Runtime facts remain current: `Batch.perform` reloads the Batch and checks required R membership and applicability, V coverage, selected inputs and checks, available resources, unresolved Attempts, and repetition limits before invoking the operation. A removed Review, withdrawn Permission, or prior consumption cannot be ignored as bookkeeping. A selected input set must not include the live Batch merely to preserve its review-time bytes; the module already owns its current execution state.

If an adapter offers a read-only preflight, pass the saved R reference and proposed Action directly, including before R adoption. Read current state without applying a revision, creating an Attempt, or invoking the operation. Report only the readiness facts actually checked. Preflight is optional and grants no execution credential. For execution, the Coordinator adopts applicable R references through `Batch.apply(ReviseBatch)`, then `Batch.perform` checks the actual current state. Neither a successful preflight nor a simulated adoption replaces those checks.

## Boundary-preserving continuation

Continue the same B while it pursues the same independently judged result and remains inside the user's objective, permitted scope, applicable Permissions, governing campaign limits, protected reserve, Measurement Definition and known effects. A changed implementation plan, W slice allocation, internal work breakdown, local command order, Review revision, Permission update, Batch operational limit, planning estimate, or Candidate Revision does not by itself create another B.

Working material stays mutable until exact bytes are selected for a check or action. Use Git to retain that selection. Do not copy the repository into execution snapshots or treat unrelated dirty paths, caches, workflow deployments, progress notes, or harmless local commands as input drift.

When practice disproves a load-bearing technical assumption, pause only dependent work and return the finding to the existing design owner. A revised design and applicable Review may continue in the same B when the independently judged result remains unchanged. When a local defect or support defect is repairable, repair and rerun only affected checks. Do not turn the defect into a new B, Generation, Permission, charge, or full review chain.

Apply [Decision-bearing thresholds](frontier-core.md#decision-bearing-thresholds) before a threshold changes the Batch's disposition. When the current normative owner and complete threshold meaning are unchanged but Entry, execution, or a check bound them incorrectly, fix the derived binding in the same B and rerun only affected checks. Repeat Entry only if its reviewed decision meaning changed; do not revise W. When the normative threshold or its meaning must change, revise its existing owner in scope; a W-owned change receives one applicable Design Review and continues in the same B. Repeat Entry only when the next actual decision changes, and ask the user only when the change crosses a user-owned boundary.

A cheap diagnostic may skip later work only when its current owner explicitly gives it that consequence under the observed conditions. Otherwise retain the observation, repair or calibrate the affected threshold if needed, and continue every unaffected action. Apply [Finding effects](finding-effects.md#finding-effects); do not turn a diagnostic failure or stale copied constant into route failure or `technical no-path`.

An unresolved actual effect, exhausted limit, unavailable required input, or repeated unchanged deterministic failure blocks only the affected action. State the observed fact and recovery condition. A finding, tool error, or process interruption does not close the B automatically.

## Perform an action

`Batch.perform` is the only current entry point that may start work capable of producing a measurement result or Consequence. A Consequence is actual spend, external submission, sensitive access, irreversible change, or single-use consumption whose repetition matters.

The Batch record is the sole current Measurement Definition owner. A measurement Action cannot carry or replace another definition. Every definition states the mode, question, comparator, metric, scope, resource ceiling, execution owner, evidence and interpretation limits, and result owner. Only an Action or installed adapter that declares `single_use_consumption` also requires `nonrepeatable_unit`, `resource_owner: workflow | user`, and `consumption_control`; omit those fields when no real single-use unit exists. Current writes use `nonrepeatable_unit`; the historical alias `non_repeatable_unit` remains readable, and conflicting aliases fail before execution. The mode controls evidence use only. It does not decide repeatability, Review, Permission, or resource ownership.

The resource ceiling bounds exposure or use that affects interpretation and is enforced independently of the Batch operational limit. A change to that ceiling follows the existing measurement-design and review gate only when it changes measurement meaning or a later allowed inference; it does not automatically require user input, Campaign Budget, or strategic Replan. The definition references the applicable parent H measurement and R8 rule rather than copying their reusable meaning. Existing definitions with equivalent meaning remain usable; do not create a schema-migration gate merely to rename fields.

Inside an adopted H `diagnostic-only` category, the definition may specify this observation's local inputs, initialization, update events, observation window and within-window calculation. It does not establish or change target linkage, cross-instance inference, formal comparison meaning or an investment consequence. A new local calculation alone does not invoke measurement design or review.

When lifecycle context changes interpretation, set `required_context_keys` to unique nonempty keys. The operation result keeps the raw `decision_value`, parent-defined `lifecycle_state` and observed `context` in its existing result mapping. The Batch module preserves these facts. Missing context limits later adoption; it is not an execution failure, uncertain effect or reason to discard the observation.

Before the operation adapter starts, the Batch implementation:

1. resolves the current Batch;
2. verifies the selected Git commit and paths when bytes affect the result;
3. verifies required checks against that Candidate Revision;
4. checks every requested resource against Batch operational limits and measurement resources against the current Measurement Definition ceiling;
5. reads applicable R and V from their owners and checks only V-owned cost or resource keys against Permission limits;
6. rejects an unresolved Attempt or a repeat of the same actual single-use unit, even when the Action key changes; and
7. creates the next local Attempt only when measurement or possible Consequences make repetition matter.

After the adapter returns, record the Attempt, actual observations, actual consumption, actual Consequences, external references when present, raw result, and exact recovery condition. Never trust a declared zero after an operation may have begun. Unexpected adapter failure leaves the affected Attempt `uncertain` and forbids blind repetition; unrelated routine work remains legal. The Attempt records what happened; it does not classify target improvement or choose an action.

When later facts resolve an uncertain operation, use `Batch.apply(ReconcileAttempt)` once to record the actual status, use, Consequences, result, and rationale. Reconciliation updates the existing Attempt; it does not create another Attempt, identity, Review, Permission, charge, or result packet. If an operation unexpectedly reports resource use or a Consequence without a planned Attempt, the module retains it as an Attempt and flags the adapter contract violation rather than dropping the effect.

For a declared single-use unit, a `running` or `uncertain` prior Attempt blocks that same unit across Action-key changes. A reconciled failed Attempt with no actual `single_use_consumption` may retry when capacity remains. Once that Consequence is recorded, renaming the Action cannot make the unit available again.

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
- Do not start another `Batch.perform` in the same B while one Attempt is unresolved. Continue ordinary `Batch.apply` work and unrelated B records.
- A failed check or failed Attempt does not create a new B or close the current B automatically.
- A result does not create E, select another route, promote a candidate, expand Permission, or establish a claim.

The Coordinator applies [Result adoption](result-adoption.md). H retains reusable measurement meaning and factual limits; E records only a valid formal evaluated result. Concluding a Batch records `completed` or `stopped`, the strongest supported result and the remaining objective gap. An unresolved Attempt prevents conclusion. The same B may reopen only for explicit continuation of the same independently judged result; prior Attempts, consumption and Consequences remain unchanged.

## Historical compatibility

Old packet, preflight, acknowledgment, execution-start, result-packet, snapshot and typed provenance formats remain immutable historical records. Their existing validators are read-only compatibility adapters. They verify an old object under its recorded rules; they do not define the current writer.

When continuing historical work, project only still-valid work facts into the current Batch view. Preserve all old bytes. New changes under the same B use `frontier-batch/1` and never regenerate legacy roots, self-hashes, copied ancestry, packet identities, or result identities. A workflow update does not retrospectively re-review or rewrite a published result.

Compatibility is not a second active contract. If removing the historical adapter would change current writes or the current interface, the seam is leaking and must be repaired.
