# Frontier Batch Interface

Load for one selected B before invoking `run-frontier-batch`, validating its result, or resuming it. Load `candidate-lifecycle.md` additionally only when `changes_executable_candidate: true` or implementation-review reuse is in question. Load [Evaluation protocol reuse](evaluation-protocol.md) when `evaluation_target.mode` is `routine-local`.

## Contents

- [Dispatch state machine](#dispatch-state-machine)
- [Pre-release transition failure](#pre-release-transition-failure)
- [Boundary-preserving continuation](#boundary-preserving-continuation)
- [Payload formats](#payload-formats)

## Dispatch state machine

This file is the sole interface for dispatching one B. [User decisions](user-decisions.md) owns whether this execution needs a new user answer. A B packet is not the scope of every user grant. Coordinator and worker instructions point here instead of restating the sequence.

For a new B, represent the lifecycle with the current typed graph in
[Provenance and identity](provenance-and-identity.md): the frozen packet and
Entry or Replan state form the decision root; a content-addressed validation
report forms its attestation; accepted authority binds those two immediate
parents; execution binds the authority and starting-state content roots; and
the outcome binds execution plus produced content roots. Store nodes with
`scripts/frontier_provenance_cli.py`. Do not copy full ancestry or individual
file digests into descendants.

Store selected project inputs through existing Git versions under
[Provenance, Git, and retained artifacts](provenance-and-identity.md).
An execution baseline is a reference to required starting inputs, not another
archive of the repository. Working outputs remain mutable within the B.
The same command shares verified content reads; live checks apply only at their
own consequence. Historical payload examples below do not reinstate old storage
writers or require a new B when storage changes.

Before acknowledgment, run `verify` with empty live facts and `checked_at:
null`. This static-only consequence proves the complete immutable decision,
attestation, and authority chain. Before execution, spend, external action, or
outcome publication, run `verify` for the named consequence and supply its
live facts. Current authority, Budget and reservation, expiry or action window,
resource availability, known prior external effects, and starting-state drift
may not be reused from static ancestry. A false or unresolved live fact blocks
only that consequence and does not reinterpret the immutable chain. Strategic
dependent spend additionally requires the unchanged decision root to contain
adopted `REPLAN_READY`. A routine R8 result that uniquely selects the next
action does not authorize added research.

`freeze_execution` is also the only routine-local admission writer. It derives the candidate and single-use slot from the complete Entry and materialization lineage, checks the finding-free implementation review and live spend gates, and records slot consumption before release. A routine packet or caller-provided digest cannot bypass that writer.

The separate packet compatibility reference describes historical semantic
payloads and fields still read by compatibility adapters. They are not
parallel identity writers or runtime interfaces for current work.

| State | Owner | Required durable output | Maximum consequence |
|---|---|---|---|
| Plan draft | Coordinator | Complete current batch plan, work-defining object and applicable gate | Eligible for preparation only |
| Prepared | Existing Entry preparation | One sealed complete decision and its generated review assignment | Eligible for the applicable Entry review only |
| Authorized | Entry review, user when required, then Coordinator adoption | Unchanged positive review and, when required, exact V plus finding-free frozen adoption validation | Eligible for worker acknowledgment only |
| Acknowledged | `run-frontier-batch` | Immutable accepted acknowledgment | Eligible for the exact Coordinator lifecycle transition and baseline freeze only |
| Released | Coordinator | Content-addressed execution baseline and immutable execution-start with `worker_may_start: yes` | Eligible for worker execution only |
| Reported | `run-frontier-batch` | Finding-free draft and frozen result validation plus one immutable result packet | Evidence for Coordinator validation only |
| Adopted | Coordinator | Frozen result validation reproduced byte for byte and accepted meaning written to the owning record | Only the consequence allowed by the current stage and review gates |

Current Entry preparation owns deterministic sealing. Do not also run historical packet-preflight or authorization-adoption writers for a current plan. Load compatibility fields only when the actual bound object uses them. Advance one row at a time. A failed or missing row preserves earlier artifacts and grants no later consequence. Dispatch is complete only when the current B is durably acknowledged and waiting, released for execution, reported for adoption, or terminally blocked with truthful spend and recovery evidence.

## Pre-release transition failure

Recover the failed state-table transition, not every earlier row. Before `worker_may_start: yes`, use a read-only check to determine whether that transition published its durable output. When it did not, and its exact parents, reviewed bindings, and target paths remain unchanged, correct an unpublished transient request or repeat the same operation without recreating the plan, Entry, authority, or acknowledgment. An accepted acknowledgment may remain the parent of a retried baseline transition. Correct a known deterministic defect before another invocation.

When the failed transition published an immutable bad output, or the correction changes a reviewed, authorized, or parent binding, preserve the old bytes and use an exclusive new path. Reuse a persistent object only when its own bytes, direct parents, and every exact binding remain unchanged; a changed object needs a new exact binding for future actions that consume its changed meaning. Historical descendants remain valid records of their original inputs; apply [Change impact and retained results](frontier-core.md#change-impact-and-retained-results) before revising a future decision. Keep the same B only when the objective, allowed consequences, public seam, ownership, acceptance meaning, Budget, risk, and one-way-effect boundary remain unchanged. Apply the existing fresh-review and user-answer rule under [Boundary-preserving continuation](#boundary-preserving-continuation); never attach an old authority node to a new decision.

Stop automatic recovery with an exact blocker when an effect is unknown, the claimed correction repeats the same deterministic failure, the existing bindings cannot be proved applicable, or the authorization made the dispatch opportunity itself single-use. After a valid `worker_may_start: yes`, use the existing Released-state and boundary-preserving continuation rules; execution-start alone does not require a new B. A historical portable bundle may still verify its stored manifest and bytes, but that verification does not prove its original source-path mapping or restore authority, execution, or result eligibility.

## Charging and publication

Working versions, budget events, and authoritative publication are distinct. The bound parent or R8 owns each charge's trigger, unit, and amount. The B cites that source and maps the planned action to its events; it does not create another policy. A saved Git version, digest, inventory, or review is not automatically a proposal or charge. An explicit parent-owned creation, runnable-material, test, sampling, exposure, or publication trigger still applies at that event. Historical authorizations retain their recorded restrictions.

Record incurred consumption in the existing accounting source when its event occurs. Failure, interruption, or absence of publication does not erase it. Publication reconciles any earlier charge rather than charging it again. Only completion or recovery of the same recorded event avoids a duplicate charge: a new proposal, execution, or sample may be chargeable even when its output bytes match. Use the existing B and accounting record to distinguish those cases, not the output digest alone. Proposal charging and other resource consumption remain separate; limits are cumulative.

On every outcome, the worker reports actual spend and the existing accounting evidence, or `unknown` with the precise missing fact. The Coordinator reconciles these with the bound rule and actual events before adopting budget meaning. Structural result validation does not interpret arbitrary parent prose or prove that no charge occurred. Resolve uncertain accounting for the affected action without inventing a transaction service or receipt.

## Boundary-preserving continuation

For parent revisions, apply [Change impact and retained results](frontier-core.md#change-impact-and-retained-results). In new plans, keep decision-only parent documents in the decision's Git-referenced subject, not automatically in `execution_frozen_inputs`. Freeze files the worker actually consumes at their recoverable execution locations. If it reads a parent document during execution, bind that original version as an input; do not replace it with an edited live copy. Existing frozen input lists remain exact. Current ledger and parent summaries are not runtime inputs merely because they describe the work.

A B is one bounded objective, authority, evidence, and spend envelope; it is not one command, slice, or internal try. Apply [Charging and publication](#charging-and-publication) while using the working loop below.

Working feedback is worker-owned implementation before a frozen closing check starts. It includes editing, compiling, linting, focused local checks, debugging, temporary materialization, inventory preparation, internal command order, and support implementation. While it stays reversible and unpublished inside the assigned write and resource envelope and has not crossed a parent-owned event, it creates no formal attempt, engineering evidence, receipt, proposal identity, review, or command history. Its actual consumption follows Charging and publication. Its result cannot support measurement, selection, promotion, or a claim.

Continue inside the existing B while its objective, acceptance meaning, permitted effects, access, and cumulative resource limits remain valid. Working feedback is the unrecorded reversible branch; observations use their explicitly authorized evidence and accounting requirements. A B need not require implementation review when its task does not need that gate. External, paid, human, or physical actions remain separate consequence-bearing operations, never implicit working feedback: execute only when the original authorization fixes their exact target, permitted action, affected scope, cumulative limits, and stop conditions and an available tool can enforce those bounds. Otherwise block that operation. Honor explicit historical restrictions; a workflow update cannot expand an old exact-command authorization.

Within that boundary, the B binds an unordered `delivery_scope` of stable W obligations. The worker owns a mutable work breakdown and may implement, check, repair, integrate, add, remove, merge, replace, or reorder its internal steps without changing the B. The complete result must satisfy every scoped obligation and integration check. A local defect or failed check remains inside this loop.

One execution-start may support several sequential worker invocations. An invocation may return without a result while the B remains in its existing Released state. A recoverable support failure before any parent-owned or actual one-way effect stays in that state. Keep the working material in its assigned paths; for W-backed work, update the existing progress region. State the current blocker, remaining completion gap, and next action with its switching condition in ordinary progress prose. A later worker re-derives the live project root and verifies the execution-start inputs, execution-frozen inputs, remaining envelope, formal-attempt prefix, and cumulative limited effects, not the history of working feedback. If continuation becomes impossible, the terminal result requires only evidence that could exist at the reached failure point; later role-specific receipts remain absent.

A formal closing attempt begins only when the first frozen engineering check starts against an exact realization staged from its transient inventory. Inventory preparation alone remains working feedback. From that seam, record the attempt's content-addressed inventory, frozen checks actually run, outcomes, necessary failure logs, and every real effect or resource use. A failed formal attempt may return to working feedback while the same B envelope remains valid; preserve and count any limited effect already incurred. An extra command invalidates formal evidence only when it runs in or can affect the formal runtime, changes the exact realization or a frozen input, or incurs a limited or one-way effect. A separate harmless working command does not invalidate the formal attempt.

The worker may remove clearly reconstructible bytes produced by this B in its exclusive working or temporary surface when those bytes are not frozen inputs, formal evidence, or published output. This applies across sequential invocations when origin is clear and creates no cleanup record. When origin is unclear, leave the bytes and use a clean runtime without ending the B. Pause only the affected action when an invariant changes, a cumulative bound is exhausted, a consequential prior effect is unknown, or the work cannot continue inside assigned paths. Do not repeat an unchanged deterministic failure. New evidence or a material repair may justify another attempt within the original time, resource, and stop limits; the repeated finding label alone does not end B. Do not add a retry counter.

A realization is review-ready only when the complete B output, not merely one slice, passes every assigned engineering check and the review collection exactly matches that inventory. The collection and inventory bind the reviewed content; publication eligibility and any earlier formal identity or charge follow Charging and publication. Preparing the review grants no measurement, adoption, or later-use authority. Freeze an implementation-review subject from the exact passing bytes, cumulative attempt reports, frozen design or direct target, execution-start, and allowed feedback. `IMPLEMENTATION_READY` permits only publication of those exact reviewed bytes. It does not permit measurement, integration, incumbent use, promotion, or a claim.

When implementation review returns a fidelity finding, repair the working realization in the same B and reuse unaffected evidence when its actual dependencies remain valid. Rerun affected checks and required integration checks, then review the exact resulting bytes. Preserve prior formal attempts and effects; do not require a separate reuse report. When practice disproves a load-bearing design assumption, pause dependent work and ask the existing design owner to revise it. A technical design revision needs the existing Design review, not a new review type. Internal work breakdown and implementation methods do not themselves change the design contract.

An original authorization may explicitly delegate bounded same-B design revisions while fixing the objective, acceptance, external seams, ownership, access, effects, resources, and parent route. Within that scope, a fresh positive Design review establishes technical readiness; it does not decide authority. Verify applicability at execution-start, retain the original Entry and authority, and freeze a new starting-state snapshot with the revised design and review. Preserve previous executions, observations, and consumption. Do not repeat Entry, initial adoption, or the user question just to replace delegated design inputs. Changes outside this same-packet mechanism use existing Entry or Replan; reuse a broader applicable grant through spend-readiness, and ask the user only under User decisions. Never infer this delegation from an old exact-only answer.

The optional same-packet technical delegation is `design_revision_scope` in the reviewed authorization target: `base_design_content_root`, `mutable_concerns` (exact logical members), and `design_input_paths` (logical member to fixed source path). Only named technical concerns and their derived identity bindings may change; complete membership, parent bytes, delivery obligations, other design content, and fixed input paths remain unchanged. Do not put user-owned policy or external seams in the mutable concerns. If that distinction cannot be made explicitly, use existing Entry instead of semantic permission inference.

Carry the original and revised complete design manifests and logical bytes under `project/state/design-revision/base/` and `revised/`, the technical review manifest and logical bytes under `review/`, and its exact `decision.json` and `attestation.json` beside them. These are inputs inside the existing execution snapshot, not a new receipt or gate. Use the current `freeze-execution` request with `content_bindings`, `live_facts`, and `checked_at`; current execution verification and offline audit verify this embedded proof. The new state's frozen-input list may replace only the derived hashes at the explicitly delegated fixed design paths. No other packet input is relaxed.

Give the new execution-start a `starting_state_path` and the matching `starting_state_root` for its new immutable bundle. Retain the original plan, acknowledgment, authority, and previous snapshot; never overwrite the packet's original baseline. Without a verified delegated design revision, the result validator still requires that original baseline location. The original Entry projection derives base input identities from its frozen-input list, so the declared base design must match what was actually authorized.

After the final positive review, publish the authoritative output atomically and require byte equality with the reviewed inventory. For current executable candidates, the official package inventory is that publication boundary; the final manifest binds the existing combined check report, and the result directly binds that report plus the existing resource observation. The shared adapter checks both against the frozen external plan before accepting the immutable result. Do not create an aggregate evidence wrapper merely for publication. Reconcile consumption under [Charging and publication](#charging-and-publication), linking this publication to its actual recorded event. Byte-identical output alone does not establish that two operations are the same event.

### Bounded observations before publication

Use the existing `diagnostic-only` mode for a decision-relevant observation of working material; neither a complete W nor a published candidate is a prerequisite. In the existing `evaluation_target`, replace `candidate` with `working_scope`: a `question`, named `subjects` and `methods`, and cumulative `resources` and `exposure` limits. Keep the exact `experiment` method contract and existing `B evidence only` consequence limit and prohibitions. An empty exposure mapping means no governed exposure is authorized, not unbounded access. The authorized method contract defines the meaning of each subject, method, unit, and access restriction; these labels are not permission wildcards.

Keep this scope unchanged through the same B. Each observation in the existing result `results` binds its actual `subject` (`scope`, `identity`), `method`, `conditions`, `observation`, raw `evidence` (`path`, `file_sha256`), `consumption` (`resources`, `exposure`), and `maximum_consequence: B evidence only`. Accumulate all observations and real effects across invocations, including failures; no reset of sampling, spend, or exposure. Changing the working material within the allowed subject range does not change the packet. Ordinary debugging remains unrecorded working feedback, not a diagnostic observation.

Use observations to continue, repair, or stop the current B; campaign-level route and investment changes still pass through Reflection and the single resolver. Diagnostics do not authorize confirmation, adoption, incumbent use, promotion, submission, or strength claims. Changes to the question, method range, acceptance meaning, or effects use the existing revision path. Parent-owned early charging rules still apply. Code-bearing or other mixed work may carry this explicit diagnostic target; without it the materialization result remains `results: []` and performance evaluation remains `not-authorized`.

After authoritative publication or the immutable result, a behavior-bearing continuation requires a new immutable B packet and every otherwise applicable review or authorization. Never rewrite historical B or evidence bytes.

The current `frontier-project-batch-plan/3` carries `delivery_scope` only for `module` or `system` work. The field is a nonempty unordered list of stable delivery identities from the bound Design traceability. Current Entry preparation rejects duplicates, unknown identities, missing prerequisites, and required design inputs that do not cover the selected obligations. Direct and non-W work omit the field. A changed scope creates a new plan identity and Entry realization even when it remains inside the same B envelope.

## Payload formats

For result writing or adoption, read [Batch result](batch-result.md). Read [Packet compatibility formats](batch-packet-format.md) only when constructing or auditing a payload that uses those fields. Use the current provenance tools for current identity operations; retain historical bytes without replaying their old writers.
