# Current Frontier Batch

Load this reference for a new B, current same-B continuation, routine progress, an action that may produce a result or Consequence, or current result adoption. Load [Historical Batch interface](batch-interface.md) or [Historical Batch result](batch-result.md) only when the actual retained record contains those legacy fields.

## Interface

`scripts/frontier_batch.py` is the current Batch module:

```text
Batch.open(B)
Batch.apply(RoutineChange)
Batch.perform(Action)
```

Read current work through `Batch.view`: `defined`, `scope`, `status`, `candidate_revision`, `reviews`, `passed_checks`, `measurement_definition`, `remaining_capacity`, and `latest_attempt`. Candidate Revision and Review references use their existing value types. Mutable results are detached from the snapshot, and an old view remains about its original state. Reopen the Batch for fresh external changes; `perform` still reloads and checks current state before an action.

`passed_checks` reports checks passing on the selected Candidate Revision; it does not choose required checks or Reviews. `remaining_capacity` subtracts exact use and retained conservative charges when reconciliation established bounded use. It reports retained accounting, not permission to execute: unresolved Attempts still block dependent execution through `perform`. Read these facts instead of rebuilding saved objects or subtracting recorded consumption in callers. Project-specific Measurement Definition fields and Review applicability remain with their existing owners.

Use `export_record()` for complete diagnostic or compatibility reads; `data` remains its historical alias. Ordinary current callers use named facts. The persisted `frontier-batch/1` record is unchanged, and reading a fact neither writes the record nor creates an Attempt.

A Batch is one stable allocation of work toward one independently judged result. It is not a candidate identity, dispatch instance, command, process, immutable packet, or proposal hash. Its design, implementation, checks, paths, Review and Permission references, operational limits, and Candidate Revisions may evolve while it still pursues that result.

Write `acceptance` as the result and evidence required to judge this B, and `scope` as its work boundary. Keep a temporary turn limit in current progress, not in acceptance as an inferred user stop. Real user limits come from [User decisions](user-decisions.md). Finishing an implementation-only B can lead to a separate measurement B within the continuing task; it does not enlarge this B's independently judged result.

The current state machine is deliberately small:

```text
draft -> open -> completed | stopped
           |
           +-> Attempt 1, Attempt 2, ... only when repetition matters
```

Preparation, editing, local debugging, harmless checks, support repair, and a failed pre-execution transition remain ordinary work in the open Batch. They create no Attempt and no separate identity. A completed or stopped Batch may reopen only through an explicit same-result revision. Work that can be evaluated, stopped, or funded independently requires another B.

A development failure does not consume an evidence-bearing exposure or single-use unit unless the actual governed effect occurred. Preserve real nonrepeatable consumption, including failed exposures, without applying its repetition limit to unrelated pure repair. Necessary debugging can precede benefit evidence inside a still-worthwhile commitment; it is not a new route-admission test. Conversely, an unexplained but valid outcome can guide allocation without commissioning causal diagnosis.

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

## Reuse working knowledge

Retain and use relevant recoverable alternatives under the adopted [R8 selection and reuse rules](../../frame-optimization/references/representation-contracts.md#r8-search-run-validation-and-old-work-compatibility), including alternatives with different quality, cost or reliability where they can affect the whole-result choice. Route an evidenced conflict with those rules to their existing owner rather than silently overriding them. Reuse current versions and evidence; ordinary retention or candidate progress requires no new R8 pass or registry, and unaffected work continues.

When work touches an existing capability, start from its current tool, implementation or method, usage reference, and relevant retained evidence. Use an adequate established path directly; add support only for a concrete unmet need of the current research commitment and its necessary follow-up. Result acquisition and later analysis can proceed separately when the later work does not determine safe execution or require evidence that cannot be recovered afterward. General recovery, classification and future reuse facilities are not prerequisites merely because they may eventually help. Cite the relevant entry point in the existing assignment. Contrary evidence or changed needs may justify repair or replacement.

Keep interface facts beside the capability they explain and significant choices with their rationale in the existing W, Frame, or measurement design. Include sources and applicable versions or conditions where they affect use; keep changing values as dated observations. When a relevant compatibility check exists only in historical task material, the implementation owner adapts its method and applicable conditions into the capability's current verification entry point and updates its existing usage reference. Reuse the method, not obsolete task-specific paths, limits or passing verdicts. Complete that repair by exercising the current entry point against the current deliverable; adding an uncalled helper or a lesson alone is insufficient. For a real dependency, apply [Evidence at real boundaries](implementation-review.md#evidence-at-real-boundaries).

Run the smallest affected check when the next use first depends on an unproven condition, when a deliverable, packaging, dependency, configuration or host change affects prior coverage, or when contrary evidence appears. Reuse sufficient evidence for unchanged relevant content and conditions. A new B, unrelated commit or report-path change alone requires no rerun. Judge this in existing work, without a per-task classification form or full historical revalidation.

Use existing locations and Git history. Add a short pointer only when the relevant entry point is missing. This is ordinary work, not a knowledge inventory, adoption gate, or prerequisite to unrelated optimization. Operational corrections happen during repair; technical learning uses [Research Reflection](learning-loop.md#research-reflection) at substantive research checkpoints.

## Apply routine changes

`Batch.apply` accepts only the closed set implemented by the module:

- define the initial Batch;
- revise the same independently judged result;
- select a Candidate Revision;
- adopt a chosen saved Review reference or apply a working-state delta through the maintained operations below;
- record an ordinary check;
- record a routine observation; or
- reconcile one `running` or `uncertain` Attempt from observed facts; or
- conclude the Batch.

A revision may change design slices, implementation choices, commands, paths, checks, R or V references, Batch operational limits, the current Candidate Revision, and one Batch-owned Measurement Definition. Record why it remains the same independently judged result. Do not create a new B merely because one field, file, design revision, tool, or workflow version changed.

Only the Coordinator may revise `resource_limits`. These are Batch operational limits, not Campaign Budget or proof of consumption. The Coordinator may raise or lower them in the same B without user input, another Selection, or Replan when the independently judged result, strategic allocation, protected reserve, Measurement Definition meaning and all governing boundaries remain unchanged. Create or increase a Campaign reservation only when governed capacity must stay unavailable to another allocation before Attempt writeback. `Batch.perform` records Attempt use first; write only Budget-governed keys back to Campaign Budget and disposition any matching reservation before another dependent allocation. A protected reserve never becomes a Batch limit directly.

A Candidate Revision is a full Git commit plus explicit repository-relative paths. One Batch may use several revisions. Saving, selecting or reviewing those bytes does not itself create a proposal or charge; record only an actual event under the applicable parent charging rule. A support or review-subject revision is not a new search candidate merely because the Git commit changes. Include configuration, dependencies and other behavior-bearing inputs when judging whether the candidate changed. Preserve actual use and historical charges independently of that judgment.

Ordinary checks and observations bind the Candidate Revision they examined. A failed check returns to routine work. Selecting a different Candidate Revision clears current checks, not their retained evidence: rerun affected checks and reuse still-applicable evidence with its original subject and unchanged dependencies when recording current applicability. Repeating the same selection preserves checks; changed measurement meaning still requires the affected applicability judgment. A new commit alone calls for neither copying pass status nor repeating every check. Checks whose execution would spend governed resources, access sensitive material, submit externally, make an irreversible change, consume a single-use sample, or create an independently retained measurement use `Batch.perform` instead.

### Maintained Batch operations

For review adoption and same-result working revisions, use `scripts/frontier_references.py` from the installed Skill directory, or its corresponding `Batch.apply` changes. Supply the chosen source and the intended change; the tool resolves saved references and writes the existing Batch. The Coordinator decides Review applicability and operational-limit changes before invoking the writer.

```text
frontier_references.py batch-review --repo <repo> --batch <B> --revision <saved-revision> --path <R-path> --reason <adoption-reason>
frontier_references.py batch-update --repo <repo> --batch <B> --revision <saved-revision> --candidate-path <path> --limit <resource>=<number> --reason <same-result-reason>
frontier_references.py batch-view --repo <repo> --batch <B>
```

For `batch-review`, the saved `review_id` supplies the handle; use `--handle` for a retained report without that field. The writer stores only the reference, not another verdict, permission or charge. Read professional findings from the saved R. In Python use `AdoptReview(revision, path, rationale, handle=None)`.

For `batch-update`, omit candidate options when only limits change; repeat `--candidate-path` or `--limit` for the changed entries. `--measurement-updates <file>` accepts a draft YAML/JSON mapping containing only changed Measurement Definition fields: nested mappings merge, lists and scalars replace the named field, and omitted fields remain current. The Batch remains the owner after application; this draft is not another current contract. Use the selected Batch revision when constructing its Action instead of mirroring its commit in measurement configuration. Independently selected comparators or external inputs retain their own references. In Python use `UpdateWorkingState(rationale, revision=None, paths=None, resource_limits=None, measurement_updates=None)`.

Each change loads current state under the Batch lock, resolves the chosen inputs, validates the complete update and saves once. Identical adoption or an already-effective delta preserves current checks and accounting. Keep the returned saved reference when repeating a selection; a moving branch name can resolve to different bytes later. A source or write error leaves the original Batch available for ordinary correction. Report generation can be repeated from `batch-view` without repeating the update or any external action. Other routine changes retain the existing `Batch.apply` interface.

`batch-view` and Python `batch_facts(view)` expose Batch status, selected revision, R references, operational limits, recorded Attempt consumption, remaining capacity and unresolved Attempts. The consumption field covers Attempts only; unresolved use is not a zero-spend conclusion or execution permission. Cite Campaign Budget and professional conclusions at their existing owners. Do not reconstruct Campaign totals or charge events from arbitrary observations or historical prose. This is a facts view, not another ledger or a generic report generator.

When replacing a repeated one-off caller, remove its copied counters, derived identities and superseded gate together, then exercise the affected path through these operations. Completion means the current caller uses owner lookups and the returned facts; adding a helper while leaving the old enforcing path active is incomplete. Preserve historical scripts and recorded effects, without requiring a repository-wide migration.

### Runtime records and resource use

Keep observed call counts and receipt locations in existing runtime records, and calculate remaining work from actual use and current applicable limits. Program logic interprets those records; a particular run's historical count, receipt filename or remaining observation count is not an implementation constant.

Ordinary engineering statistics, including helper-process counts, belong in retained receipts or observations when useful; they are not mandatory budgets. Set a hard limit only for an actual user boundary, platform constraint or concrete operating risk, with its existing basis. One computing task may include a waiting parent and a helper process. Correct an unsupported internal limit through [Batch continuation](#repair-an-existing-execution-restriction), not another Permission or Replan.

Use `requested_resources`, `resource_use` and cumulative limits for additive consumption that needs Batch enforcement. Requests may use justified upper bounds; successful results return actual use, not the requested bound. Put ordinary estimates in observations as estimates. Existing range-based reconciliation applies to failed Attempts with unknown exact use; it is not an accounting interface for arbitrary successful estimates. Batch consumption remains the sum of Attempt use.

Keep peak concurrency, memory or temporary-space constraints in the existing run configuration and enforce real hard limits at the adapter or host. Record observed peaks in existing observations, not cumulative consumption. When correcting an old peak-as-budget definition, align all four current uses before continuing: Batch `resource_limits`, Measurement Definition `resource_ceiling`, Action `requested_resources`, and result `resource_use`. Use existing `ReviseBatch` replacement mappings to remove the old current keys; `batch-update` merges omitted fields rather than deleting them. Preserve historical Attempts and their summed consumption. Retired peak keys no longer define a current remaining balance; real cumulative use and user limits remain governed. Field names alone do not determine resource meaning.

Cover preparation, Batch checks and adapter work together only when a real limit governs that whole interval. Count each governed use once; ordinary auxiliary statistics need neither per-command receipts nor a new monitor. `RecordObservation` saves facts without debiting Batch capacity. One bounded read-only action may group related queries through `Batch.perform` when accounting needs its Attempt. Such accounting adds no B, formal measurement, Review or Permission by itself.

Preserve earlier use under its original operation and count it once. A later operation reports only its own additional use, not a cumulative total as new consumption. If required past use was recorded outside the supported Batch accounting path, resolve that specific gap before dependent spend rather than treating a receipt as a completed debit. Adjusting remaining observation counts needs reconsideration only where it changes required evidence or a supported conclusion.

## Review applicability and adoption

An R and its subject remain the versions saved in Git. The Coordinator adopts its conclusions, limits and unresolved issues separately from any suggested procedure under [Professional output and workflow decisions](worker-interfaces.md#professional-output-and-workflow-decisions). The current Batch records adoption and progress. `GovernanceResolver.review(reference, action)` judges whether the saved conclusions and assumptions cover the proposed action; it does not convert recovery prose into new requirements. Compare relevant decision meaning and selected inputs, not the whole current `batch.yaml` against a review-time or reconstructed post-adoption file.

When preparing an Action, the Coordinator selects necessary judgments under [Assurance by consequence](batch-evaluation.md#assurance-by-consequence); the implementation owner resolves those R handles from current Batch references. `references.reviews` retains evidence; `Action.required_reviews` contains only judgments required for this action and may be empty. Carry this selection through requirement generation, any pre-Action role-completeness checks, the Action list and `GovernanceResolver.review`. A fixed implementation/measurement-support/Entry bundle can reject work before the Action exists; correcting only its final handle list is insufficient. Replace an unsupported bundle in the current caller with the selected judgments, preserving real subject, assumption, use and Permission checks. Retaining or citing an R does not itself make it a gate, and clearing the list does not resolve a genuinely missing judgment.

Adopting an R or recording progress does not invalidate its checked conclusions. Separate a procedural phrase such as "for later Entry review" from the report's actual coverage. Current rules may remove an unsupported stage requirement without rewriting the R or asking for another report to clarify that phrase. They cannot establish checks the reviewer never performed: retain technical use limits and assumptions, inspect a genuinely missing professional question, and obtain changing facts such as current capacity or Permission applicability at the appropriate execution boundary. Combine actual conclusions rather than transferring readiness labels. Reference-only changes need reference and applicability checks; changed behavior, acceptance or interpretation reopens only affected conclusions through the existing owner. This creates no review-validity registry.

The same applies to a historical nonpositive R: preserve its facts and verdict, but assess the defect's current impact under [Finding effects](finding-effects.md). Sufficient retained facts can support proceeding under current rules without a replacement R merely to change classification. Explain the current use in ordinary adoption or scope correction, not a waiver. If needed, the existing professional owner clarifies a consequential disagreement in the same task. Carry the selected requirements and current-use assessment into the actual caller and governance adapter; neither a renamed verdict nor a narrative decision clears a machine failure or supplies missing evidence.

Fixed action inputs retain their existing version checks. Runtime facts remain current: `Batch.perform` reloads the Batch and checks required R membership and applicability, V coverage, selected inputs and checks, available resources, unresolved Attempts, and repetition limits before invoking the operation. A removed Review, withdrawn Permission, or prior consumption cannot be ignored as bookkeeping. A selected input set must not include the live Batch merely to preserve its review-time bytes; the module already owns its current execution state.

The module checks saved candidate objects in one batch of Git requests. It does not verify all working files the adapter may read; retain that responsibility at the existing execution input boundary. A caller may reuse saved Review text by repository, full commit and path, while assessing applicability and Permission against the current Action. Reading an immutable object again does not establish current working-file integrity or current authority.

Keep ordinary accounting, review adoption and recovery prose outside the fixed technical input set unless their content actually affects execution or interpretation. A path that selects input, destination or access scope still matters; a report's storage location alone does not invalidate unchanged technical evidence.

For a state-only preflight, pass the saved R reference and proposed Action directly, including before R adoption. Inspect saved state without applying a revision, creating an Attempt, or invoking the operation. Queries that use resources follow [Runtime records and resource use](#runtime-records-and-resource-use), even when read-only. Report only the readiness facts actually checked. Preflight is optional and grants no execution credential. For execution, adopt the chosen R through [Maintained Batch operations](#maintained-batch-operations), then `Batch.perform` checks actual current state and applicability. Neither a successful preflight nor a simulated adoption replaces those checks.

Obtain early facts that decide feasibility or useful implementation scope through the query's own permitted path; future submission, recovery or long-term observation code is not its prerequisite. Each query must use an `OperationBinding` that actually performs only that query, with its own effects, access conditions and necessary checks. Clearing an Action list cannot hide effects inherent to its installed operation. Complete the safeguards necessary for an external effect before producing it. Collect changing facts needed for that effect close to invocation, reusing earlier facts when still applicable rather than mandating a second query. Host approval decided only at invocation is not a separate advance-clearance prerequisite; apply it when it occurs.

Preflight age is distinct from Permission validity and input integrity. Apply V's actual conditions, withdrawal and expiry, and the existing version checks for fixed inputs. An internal preflight deadline does not shorten V's validity or expire fixed inputs. Refresh dynamic facts only as needed for the next action. A real token, lease or reservation retains its actual expiry. An internal age limit is a technical choice subject to [Decision-bearing thresholds](frontier-core.md#decision-bearing-thresholds), not a universal preflight lifetime or a substitute for checking changed state. Refreshing a needed fact does not itself require renewed Permission or Review.

## Boundary-preserving continuation

Continue the same B while it pursues the same independently judged result and remains inside the user's objective, permitted scope, applicable Permissions, governing campaign limits, protected reserve, Measurement Definition and known effects. A changed implementation plan, W slice allocation, internal work breakdown, local command order, Review revision, Permission update, Batch operational limit, planning estimate, or Candidate Revision does not by itself create another B.

Working material stays mutable until exact bytes are selected for a check or action. Use Git to retain that selection. For a bounded iterative operation, distinguish the selected procedure and inputs that define its adaptive behavior from intermediate outputs it generates. Reuse a suitable existing operation binding without treating every output as a new proposal. Grouping or resuming work never resets consumption, restores a consumed unit or authorizes adaptive changes to a fixed confirmatory protocol. If the binding cannot preserve real limits and meaning, repair that specific seam before dependent execution. Do not copy the repository into execution snapshots or treat unrelated dirty paths, caches, workflow deployments, progress notes, or harmless local commands as input drift.

When practice disproves a load-bearing technical assumption, pause only dependent work and return the finding to the existing design owner. A revised design and applicable Review may continue in the same B when the independently judged result remains unchanged. For a local or support defect, apply [Finding effects](finding-effects.md); when correction is needed, repair the affected use path and rerun only relevant checks. Deriving a result from retained evidence follows [Reuse completed evidence](batch-evaluation.md#reuse-completed-evidence); a new measurement uses the current definition and `Batch.perform` after unresolved effects are reconciled. The repair itself creates no new B, Generation, Permission, charge, or full review chain.

When repeated repair delays meaningful feedback or support work outgrows the pending question, assess the changed remaining commitment under [When to reconsider investment](learning-loop.md#when-to-reconsider-investment) before assigning further discretionary repair. Simplifying dependencies or reusing sufficient capability with the existing owner is one possible response, not a prerequisite to comparison. Same-B continuity does not settle the investment question. Preserve an observation large enough to answer the question; a smaller but uninformative trial is not progress. When the rationale remains applicable, continue ordinary repair directly. Neither sunk effort nor a fixed number of failures decides it; this adds no per-finding report.

When cumulative delay matters, use retained event times, actual consumption and the still-missing observation across renamed work and recovery. Missing timing stays unknown; do not create a timesheet or recharge completed support as remaining work. Keep shared dependencies in every option that actually needs them and retain route-specific incremental cost. At handoff, return and cold recovery, reuse the applicable scope judgment and account; those boundaries alone require no additional semantic invocation or repeated full-history synthesis. Check changed facts and actual current-use bindings rather than reranking unchanged work.

Apply [Decision-bearing thresholds](frontier-core.md#decision-bearing-thresholds) before a threshold changes the Batch's disposition. When the current normative owner and complete threshold meaning are unchanged but Entry, execution, or a check bound them incorrectly, fix the derived binding in the same B and rerun only affected checks. Repeat Entry only if its reviewed decision meaning changed; do not revise W. When the normative threshold or its meaning must change, revise its existing owner in scope; a W-owned change receives one applicable Design Review and continues in the same B. Repeat Entry only when the next actual decision changes, and ask the user only when the change crosses a user-owned boundary.

### Repair an existing execution restriction

For an unsupported restriction, apply [Constrain effects, not convenient forms](technical-design.md#constrain-effects-not-convenient-forms). Classify it by the actual goal, investment, resource and evidence boundary it protects, not by the document or Review that contains it. Internal revision allowances, check quotas and development stop conditions remain Coordinator-adjustable inside the same investment; their presence in W, X or R does not make them strategic. Revise their current owning definition and resume ordinary work without a new Replan or permission question. A real design, measurement, strategic or user-boundary change retains its existing owner and applicable gate.

Complete this correction through the existing assignment, current Batch and actual enforcing code or configuration. Resolve applicable Review references from current state rather than a hard-coded R; keep revision selection separate from charge-event writeback. Replace an obsolete gate and its dependent writer together, checking the affected path from the retained restricted state to the next legal action. Preserve original records, actual consumption and unresolved effects. This is scoped repair, not a restriction audit, historical migration or blanket gate bypass. Reuse unaffected conclusions under [Review applicability and adoption](#review-applicability-and-adoption).

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
