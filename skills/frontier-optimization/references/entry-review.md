# Frontier Entry Review

## Current provenance form

Use [User decisions](user-decisions.md) to distinguish a new user decision from a new execution realization. Initial authorization and changes outside an existing authorization use authorization-readiness; a new realization under an applicable continuing grant uses spend-readiness. Same-B continuation, bounded working observations, and explicitly delegated technical design revisions follow [Boundary-preserving continuation](batch-interface.md#boundary-preserving-continuation). Do not repeat Entry or initial adoption for changes that this existing authorization already covers. A Design reviewer establishes technical readiness, not user authority. The exact-target restrictions in historical records remain effective; this rule does not retroactively broaden them.

Keep a new Entry or Replan mutable until its deterministic checks pass. Call
`prepare_review(draft_spec, project_root, output_root)` once. It validates final
raw-byte self-identities, cross-file path, digest, and identity bindings,
monotonic record namespaces, review-kind role schemas, selected paths, and
closed collections. The caller supplies only the Entry review stage. The role
adapter derives affected scope, Budget, Selection, authority target, and the
later-spend gate from canonical project objects; caller-written summaries are
not accepted. `NOT_READY` returns findings only: it allocates no R
identifier and creates no snapshot, decision, packet, supplement, or recovery
record. Repair the same unspent and unauthorized B draft and call it again.

`SEALED` atomically publishes one Git-referenced `project-decision` content root, one
decision node, one review packet, and one exclusive review assignment. The root
contains a generated `frontier-review-subject/2` index that enumerates every
member, every closed collection, the applied `frontier-review-role-adapter/2`,
and the derived review-kind semantic projection. The
reviewer receives that single complete root. A repaired version is also complete;
its review scope follows [Entry repair review](#entry-repair-review). Keep the
previous saved version and verdict, rather than a base-plus-supplement overlay.

The decision node binds exactly that `project-decision` content root and an empty payload.
Completeness belongs to the verified content and role adapter, not to caller
text stored on the node.

Create one attestation whose report uses the `review-report` domain and whose
subject is that exact decision. After any required user answer, bind one
authority node to the decision, finding-free attestation, and verified complete
subject. Later objects cite only their immediate typed parent.

The current workflow, validator, worker interface, deployment location, and
release identity are never project inputs. Updating any of them while repository
work is in progress does not change a project node, invalidate an adopted review,
automatically trigger Entry, Replan or a Selection change. Apply current rules
to the next decision under [Change impact and retained results](frontier-core.md#change-impact-and-retained-results). Preserve old verdicts;
a removed procedural blocker may change the next decision without changing
historical evidence or the user's actual permission.

The current Entry plan is stored only as `project-decision` content. It contains
the exact project parents, evidence roots, F1-F8, Budget, Selection, route-set
state, persisted resolver result, affected scope, surviving authority, B plan, authority target, and later-spend gates
needed for review. It contains no workflow source binding, semantic-rule version,
validator or worker identity, deployment path, installation time, or release
locator. The review report is separate `review-report` content and the
attestation payload contains no validator identity. A later-spend check validates
the persisted Selection and cited project facts; it never reruns the resolver
under a later workflow.

Current Entry uses `frontier-project-batch-plan/3`. When that plan contains a `frontier-routine-follow-up/1`, the same complete subject must also contain the exact protocol, current calibration, single-use slot, scientific question, experiment template, ceilings, Budget boundary, and prohibitions defined by [Evaluation protocol reuse](evaluation-protocol.md). The review authorizes only the materialization and that conditional screen. The screen is admitted later from derived candidate and implementation-review evidence; it does not require another Entry, review, V, or authority.

Selection must be copied from persisted Reflection without reinterpretation.
The attested `project-decision` content includes the resolver row, route-set state, direction, affected scope, surviving authority,
research disposition, diagnostic dominance or exact blocker, Budget and
protected reserve, and every later-spend gate. A strategic change cannot bind
authority for dependent spend until the same decision has `REPLAN_READY`.
Unresolved validity remains an unresolved fact; it cannot be encoded as route
or frame evidence. A routine R8 result that uniquely determines the next action
records `research_disposition: no-additional-research`.

Historical incomplete attempts remain audit records. They cannot be combined
through prose replacement rules to create a complete Entry, and a supplement-
only decision cannot control a new authority. A pre-review failure has no
review identity to preserve. A nonpositive reviewer verdict is different: keep
that exact subject, report, and attestation, then prepare a new complete subject
if the Coordinator repairs the draft.

The current adapters use stable logical roles and project schemas, not task or
technology names. Entry requires the canonical state, parent, Selection,
batch-plan, and authorization-target or spend-gate objects. Replan,
implementation, and claims each require their own explicit project contract.
Design requires its canonical design index and one closed design collection.
An unsupported project contract returns `NOT_READY`; add a deliberate adapter
instead of accepting unknown identity text. The outer identity of a composite
design index may use an exact top-level omit-line SHA-256 rule while its nested
concern and traceability checks remain owned by Design review.

For a current Entry, review the authorization target's `stop_boundary`, the batch plan's `stop_conditions`, the applicable contractual Work or Design recovery conditions, the authorization question, and its maximum consequence as one contract. Optional W recovery guidance adds no constraint or authority. Each failure boundary must name its dispatch phase. Return `ENTRY_REPAIR_REQUIRED` when these sources conflict, leave the phase ambiguous, or make an unpublished, zero-effect Coordinator transition terminate the technical B. A single proposal does not make the dispatch opportunity single-use unless the exact authorization states that consequence. Apply [Pre-release transition failure](batch-interface.md#pre-release-transition-failure) before judging recovery or successor-B need.

## Entry repair review

Repair the current draft inside the same B when its objective and permitted scope remain applicable. Preserve the previous reviewed Git version and report; ordinary planning files may keep their paths while the draft changes. Save the corrected version when it is ready for review, using an exclusive review-output path. Intermediate edits require no review object, replacement directory family, new B, or Generation. Fixed execution inputs and exact historical authorizations keep their existing restrictions.

During ordinary drafting, use the bound parent as the source of budget, permission, and acceptance rules. The plan explains this action's events and consequences; dispatch, authorization, and state records refer to that meaning rather than inventing parallel policies. Apply [Charging and publication](batch-interface.md#charging-and-publication) before freezing an Entry. This is planning work, not another preflight or reviewer.

For a repair, the Coordinator supplies the previous relevant finding and saved version, the current complete version, and a short change explanation in the existing assignment context. These are facts for independent review, not an expected verdict or a mandatory repair method. The reviewer uses the saved-version diff to inspect the correction and its actual consequences, including related branches. Judge the current version and cite still-applicable earlier conclusions together by relevant scope. An earlier report is an existing judgment, not an instruction to repeat its entire review.

Expand review only where a changed dependency, unsupported earlier conclusion, or newly observed material problem affects the decision. Unchanged bytes alone do not preserve a conclusion after its assumptions or acceptance meaning change. Conversely, reuse needs no per-file proof, dependency register, separate report, recursive rereading of old evidence, or rerun of unaffected checks. The current report explains the change, affected findings, and reused conclusion scope briefly; it still attests the complete current decision. First reviews retain the full applicable review method. This Entry repair method does not select or replace another review branch.

A corrected plan with a material authority or spend conflict needs this review before its authorization question. Work already covered by an existing authorization uses the continuation rule above. Changing a saved version neither transfers an exact old authority nor creates a reason by itself to ask again, reopen Design, or research the route again.

## Current Design-to-Entry seam

For a current W-backed Entry, consume one unchanged adopted `DESIGN_READY` identity whose Delivery map and `traceability.yaml` define stable delivery obligations. Bind the exact B to a nonempty, dependency-complete, unordered `delivery_scope`, the exact execution `source_base_identity`, required design inputs, worker write surface, execution-frozen inputs, and stable output paths. Confirm that this realization satisfies the reviewed behavior, source compatibility, interface, oracle, failure, and recovery conditions without rewriting them. A different B, delivery scope, attempt namespace, execution source, assigned worker surface, stable output path, or frozen input is a different Entry realization and execution authority, not automatically a new user decision; a temporary path or command inside the assigned worker surface is not. It does not reopen Design unless it changes the stable delivery obligations or another load-bearing technical condition.

Apply [Technical design's assignment ownership rule](technical-design.md#assign-the-professional-author) to distinguish technical obligations from explanatory working steps. Assess delivery, evidence, and authority rather than reproduction of an internal work process. Do not turn nonbinding W prose or a reviewer's suggested repair into an Entry requirement, or move ordinary methods omitted from W into frozen Entry steps. An already-frozen mandatory conflict still uses [Review and revision](technical-design.md#review-and-revision); it cannot be silently reclassified as guidance.

Distinguish the repository-evidence snapshot used to support Design review from the execution source used by Entry. Entry may use a different source only under compatibility conditions already stated by Design. If an exact ancestor, preserved byte set, pre-migration state, or other source identity is itself design meaning, Entry must match it. Return `ENTRY_REPAIR_REQUIRED` when realization details are incomplete or incompatible, and `DESIGN_REPAIR_REQUIRED` through the owning design path when compatibility meaning itself is missing or must change.

Require Entry outputs to cover every obligation in `delivery_scope`, including prerequisites satisfied by an explicitly bound reusable input, but do not require Design to preassign repository-relative internal evidence destinations or the worker's mutable step order. Treat an exact path as Design-owned only when a real caller or operator outside the current B or attempt depends on it as a stable interface. Current Design review must reject a new B-keyed `batches` traceability shape; only an exact historical design identity with an already adopted valid `DESIGN_READY` may retain that shape for audit under its original authority.

## Current review method

Inspect the prepared complete subject, not an unrelated Coordinator operating manual. Preparation owns structural identity checks; the reviewer owns these judgments:

1. The proposed action addresses the objective and a decision-relevant uncertainty. Check prerequisites, competing explanations, route coverage and the recorded resolver choice against cited evidence; request more research only when it can change the decision.
2. The user decision actually covers the action, cumulative resources, access, effects and stop conditions. Technical uncertainty is not a user-owned value choice.
3. Budget, prior and unknown consumption, reservations and protected reserve agree. Apply the parent-owned charge event rather than inventing another accounting policy.
4. The deliverable and checks can answer the stated question. Apply design or implementation requirements only where this work needs them; research, analysis and human input do not inherit code publication gates.
5. Measurement and comparison support only their stated inference. Test the proxy's fitness for the intended consequence, not merely whether its definition is precise. Preserve validity and claim limits.
6. Inputs, output ownership and recovery cover the action's actual dependencies and reachable failure phases. A repair suggestion is not a new acceptance requirement.
7. The current selection follows its controlling Reflection and the sole resolver. Read [Learning loop](learning-loop.md) only when judging a new direction or strategic allocation; an unchanged adopted selection needs applicability checks, not a new resolution.

Use [Finding effects](finding-effects.md). Return `AUTHORIZATION_READY` for a complete target requiring a new user decision, or `ENTRY_READY` for applicable spend-readiness under existing permission. Otherwise use `ENTRY_REPAIR_REQUIRED`, `EVIDENCE_REQUIRED`, `PARENT_REVIEW_REQUIRED`, or `BLOCKED`, stating the affected consequence and recovery condition. The report cites the exact subject, checked conclusions, findings, maximum consequence and conditions. For a correction, use Entry repair review above rather than repeating the first review.

Read [Historical Entry formats](entry-review-legacy.md) only for an exact historical object, never to fill gaps in a current review.
