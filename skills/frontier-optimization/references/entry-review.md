# Frontier Entry Review

Load only when validating an Entry assignment, freezing the pre-authorization or direct-spend snapshot, invoking `review-frontier` with `review_kind: entry`, or adopting the later user answer.

Create the packet after F1-F8, the proposed Budget and Selection consequence, B, applicable W/design and traceability, research evidence, worker packets, structural packet preflights, and one exact authorization target are complete. Do this before asking the user. Include immutable copies of Campaign Cycle, Batch Interface, Worker Interfaces, all three validators, and every semantic input needed to decide whether the exact target is eligible to present. Use a new path for each attempt and preserve nonpositive reviews. Include no expected verdict, suspected defect, or proposed repair.

Run `validate_entry_packet.py` in draft phase before creating the snapshot. A finding blocks snapshot creation. After snapshot identity resolves, insert it, compute the Entry packet identity, run frozen schema validation to a different immutable path, and only then invoke the reviewer. Schema validation checks structure; the reviewer checks full meaning.

## Review method

1. Verify every immutable identity. Return `PARENT_REVIEW_REQUIRED` for a stale, draft, conflicting, or incomplete parent, handoff, reference baseline, measurement, budget authority, or R8 rule. In post-closeout recovery, also verify the prior complete handoff, incremented campaign generation, exact proposed current-generation authority, and immutable reuse lineage.
2. Check cited research, not only Q summaries. Require identifiable sources, applicable findings, explicit conflicts and limits, material alternatives, useful negative searches, and a justified search stop. Accept one eligible approach only when Q disposes every other plausible approach as technically ineligible; reject invented alternatives.
3. Check every eligible T and the campaign baseline. Require a credible mechanism, measurable feedback, headroom or known limits, replacement boundary, technical eligibility, and evidence-bounded recommendation. Legality, basic operation, convenience, or one local tweak is insufficient by itself.
4. Check adopted tradeoff V records and the proposed authorization target. A tradeoff follows technical filtering and faithfully records a real user choice. The target binds one exact packet, structural preflight, reviewed design or direct identity, source base, scope, maximum spend, stop boundary, proposed Budget and Selection consequence, result path, and adoption path. In recovery, require current-generation authority rather than treating closed authorization as current. Do not require or accept a completed answer in an `authorization-readiness` snapshot.
5. For code-bearing work, verify repository fit against project files. Require the recorded structure disposition, candidate interface, exclusive worker write surfaces, worker-forbidden paths, execution-frozen inputs, profile evidence, exact pending authorization target, manifest, workspace isolation, and planned implementation review. For `module` or `system`, consume an unchanged adopted `DESIGN_READY` rather than repeating design review.
6. Check the Brief, F1-F8, proposed Budget and Selection consequence, B, applicable W, and worker packets as one plan. Require exact parent scope, zero new B spend before adoption, exact inherited spend and remaining ceiling, reconciled Entry planning and research cost, a usable baseline checkpoint, decision-changing first performance check, comparison-validity checks, preparation limit, protected reserve, observable continuation and stop rules, unchanged claim ceilings, and a precommitted hypothesis, contradictory observation, and checkpoint decision for every selected B. For recovery reuse, require adopted fresh `IMPLEMENTATION_READY`, unchanged candidate identity, zero new proposal charge, and a separate experiment B. Reject an untriggered or empty W. For human input, require the complete input contract and evidence-only limit.
7. For W-backed work, require the selected Delivery row, required concern identities, and machine-readable evidence destinations to map completely into B. Reject whole-W freezing. Current authorization must be absent from W and owned by external lifecycle records.
8. Reconstruct dispatch from the snapshotted contracts, validators, packet, preflight, and permissions. Recompute both structural and Entry schema checks. Require acknowledgment before work or spend, the exact Coordinator lifecycle transition when applicable, exclusive Coordinator execution-baseline and execution-start outputs, recoverable bytes for every post-transition baseline identity, profile-aware result validation before the final result path, and a second worker invocation. Reject any state that could become executable only by mutating a reviewed packet, design contract, source, or whole W after the user answers.
9. For `authorization-readiness`, return exactly `AUTHORIZATION_READY`, `ENTRY_REPAIR_REQUIRED`, `EVIDENCE_REQUIRED`, `PARENT_REVIEW_REQUIRED`, or `BLOCKED`. For `spend-readiness` with no user authorization, use `ENTRY_READY` as the positive result. A positive result has no finding; every nonpositive result has at least one complete finding.

## Packet

```yaml
review_kind: entry
review_stage: <authorization-readiness | spend-readiness>
review_id: <unique identifier>
packet_path: <frontier/reviews/entry-<review-id>-packet.yaml>
entry_schema_preflight_paths: {draft: <exclusive draft JSON path>, frozen: <exclusive frozen JSON path>}
packet_id: <review kind and id plus SHA-256 of canonical packet bytes with this field omitted>
snapshot_root: <frontier/reviews/entry-<review-id>-snapshot/>
snapshot_manifest: <snapshot_root/manifest.yaml and identity>
snapshot_id: <immutable snapshot identity>
task_path: <canonical task path>
problem_epoch: <integer>
problem_generated_at: <ISO-8601 datetime>
representation_revision: <integer>
representation_generated_at: <ISO-8601 datetime>
representation_review_result: <PROCEED_EXPLORATORY | PROCEED_MODULAR>
representation_permitted: <exact reviewed text>
campaign_generation: <positive integer>
recovery_lineage: <for generation 1, null; otherwise mapping with prior_closeout, frozen candidate_recovery_preflight when applicable, recovery_authorization, disposition, inherited_budget, reused_identities, and implementation_review>
repository_structure_disposition: <existing-integrated | absent-awaiting-user | user-approved-new | not-applicable>
repository_layout_approval: <V identifier or null>
design_gate: <for code-bearing work, direct profile evidence or adopted DESIGN_READY identity plus exact pending authorization scope; pending design or prototype B; or not applicable>
dispatch_contract: <snapshotted Campaign Cycle, Batch Interface, Worker Interfaces, packet, Entry, authorization-adoption, execution-baseline, and result-validator identities plus exact packet-preflight paths and identities, acknowledgment, lifecycle-transition, execution-baseline root, execution-start, result-validation, and path-separation consequence>
authorization_target: <exact target id, batch id, B packet, preflight, design or direct identity, source base, scope, spend, stop boundary, result path, and proposed Budget, Selection, and lifecycle transition; or null for spend-readiness>
authorization_state: <pending for authorization-readiness | not-required for spend-readiness>
authorization_adoption_path: <exclusive Coordinator-owned path for the post-answer identity and staleness check>
authorization_adoption_preflight_path: <exclusive Coordinator-owned JSON path for the frozen adoption validation>
snapshot_inputs: <exact snapshot_manifest#inputs reference; do not duplicate the array>
selected_batches: [<Primary and Parallel B identifiers>]
actual_spend: <inherited closed-generation spend, zero new-generation B spend, plus cited current Entry planning and research cost under the governing accounting rule>
assigned_review_path: <frontier/reviews/entry-<review-id>.md>
completion_check: <every Entry requirement receives a verdict and every finding cites snapshot evidence>
```

## Artifact

Only `review-frontier` writes the assigned file.

```markdown
---
type: Optimization Frontier Entry Review
status: complete
review_id: <identifier>
review_result: <AUTHORIZATION_READY | ENTRY_READY | ENTRY_REPAIR_REQUIRED | EVIDENCE_REQUIRED | PARENT_REVIEW_REQUIRED | BLOCKED>
reviewed_by: review-frontier/1
reviewed_at: "<ISO-8601 datetime>"
snapshot_packet: <path and identity>
generated: { by: review-frontier/1, at: "<ISO-8601 datetime>" }
---

# FRONTIER ENTRY REVIEW: <effort name>

Result: <allowed result for review_stage>
Reviewed snapshot: <packet path and identity>
Reviewed at: <ISO-8601 datetime>

## Readiness checks

- Parent and handoff: <pass or findings>
- Campaign generation and recovery lineage: <pass, not applicable, or findings>
- Reference baseline: <pass or findings>
- Route research and alternatives: <pass or findings>
- Campaign-baseline quality and choice: <pass or findings>
- Repository structure, approval, and candidate interface: <pass or findings>
- Design profile, review, choices, and proposed authorization target: <pass or findings>
- Candidate lifecycle and planned implementation review: <pass or findings>
- Bounded path, comparison validity, and budget: <pass or findings>
- Precommitted hypothesis, observation, and decision: <pass or findings>
- Packet structure, W traceability, and Entry schema: <pass or findings>
- Dispatch state machine and path ownership: <pass or findings>
- F1-F8, Selection, B, W, packets, and permissions: <pass or findings>
- Human input contract and evidence-only boundary: <pass, not applicable, or findings>
- Inherited spend, proposed reservation, Entry-cost accounting, and zero-pre-adoption-spend boundary: <pass or findings>

## Findings

### Finding 1: <omit when ENTRY_READY>

- Result effect: <ENTRY_REPAIR_REQUIRED | EVIDENCE_REQUIRED | PARENT_REVIEW_REQUIRED | BLOCKED>
- Affects: <paths, records, or fields>
- Requirement: <exact requirement>
- Observed: <snapshot fact>
- Evidence: <snapshot identities>
- Required correction: <observable condition; no repair text>
```

`AUTHORIZATION_READY` permits only presenting the exact reviewed target to the user. It grants no reservation, Selection adoption, acknowledgment, execution-start, work, or spend.

## Post-answer adoption

After `AUTHORIZATION_READY`, `grill-frontier` asks only the reviewed question. The Coordinator builds the exclusive adoption artifact; no reviewer writes it:

```yaml
adoption_path: <assigned authorization_adoption_path>
adoption_id: <content identity with this field omitted>
readiness_review: <unchanged AUTHORIZATION_READY packet, snapshot, artifact, and identities>
authorization_target: <exact reviewed target identity>
user_result: <exact result path, identity, and answer>
adopted_v: <V identifier and identity, or null on decline>
binding_checks: [<name, reviewed_identity, observed_identity, and matched or mismatch for every target and live input>]
answer_fidelity: <exact authorize | decline | conditional change>
reviewed_state_transition: <exact reviewed Budget, Selection, and lifecycle change to apply after validation, or none>
entry_result: <ENTRY_READY | DECLINED | REVIEW_REQUIRED | BLOCKED>
maximum_consequence: <exact dispatch consequence or none>
```

Run `validate_authorization_adoption.py` on the draft, insert only its computed identity, freeze the record, and reproduce the same finding-free result at `authorization_adoption_preflight_path`. Only `exact authorize` against unchanged inputs may produce `ENTRY_READY`; the Coordinator may then apply only the exact reviewed state transition. Decline produces no dispatch authority. A condition, changed scope, changed path, changed spend, changed stop boundary, stale input, or repair creates a new target and requires new structural validation, Entry schema validation, snapshot, and authorization-readiness review before another authorization question. Never update W to record the answer.
