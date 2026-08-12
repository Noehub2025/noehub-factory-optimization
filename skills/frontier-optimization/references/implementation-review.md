# Frontier Implementation Review

Load only after a code-bearing B materializes a candidate, before its first performance measurement, mainline integration, or incumbent use, when checking review reuse, or when a post-closeout recovery Entry proposes an unchanged materialized candidate.

Use a new packet and review path for each attempt. Preserve nonpositive reviews. Include no expected verdict, suspected defect, or proposed repair.

## Review method

1. Verify the declared review mode. For `materialization`, verify parents, immutable B packet, structural preflight, W traceability when applicable, authorization-readiness review, user V, Coordinator Entry adoption, code-bearing flag, direct or design identity, exact design inputs, acknowledgment, content-addressed execution-baseline snapshot, execution-start, finding-free result validation, result, manifest, source identities, code, configuration, dependencies, runtime factors, tests, evaluator, runner, recovery artifacts, and evidence identities. For `recovery-reuse`, verify the new generation, complete prior lineage, and frozen finding-free candidate-recovery preflight produced before every new-generation artifact. Do not reinterpret an old packet through live workflow text.
2. Check repository structure against the recorded disposition. An unapproved top-level root, toolchain or dependency-manager replacement, or public-entrypoint change requires repair.
3. For `materialization`, reconstruct structural validation, full pre-user readiness review, post-answer adoption, and both dispatch phases. Require exact target and answer fidelity, no whole-W freeze, complete evidence traceability, accepted acknowledgment before lifecycle transition, complete baseline snapshot before execution-start, execution-start before spend, matching frozen identities, and byte-identical frozen result validation before the final result. Compare every worker-changed path with B and reject unreported or unauthorized writes. For `recovery-reuse`, reconstruct historical materialization only for provenance and separately verify current authority.
4. Check implementation only against the assigned design inputs and candidate interface. Require the agreed architecture, entities, invariants, flows, failures, compatibility, rollback, observable definition of done, and distinguishing tests. Build success or a smoke run alone is insufficient.
5. Recompute candidate identity from source, result, paths, resolved configuration, dependencies, runtime factors, generated assets, and interface. Require recoverable bytes for every material identity input; a mutable path, branch, worktree, uncommitted state, role name, or hash without recoverable bytes is not an immutable implementation snapshot.
6. Confirm the candidate stopped before performance measurement, mainline integration, and incumbent use. In `recovery-reuse`, also confirm the candidate was not modified after its prior manifest and that the new generation has not measured or adopted it. Reject a snapshot containing unauthorized performance evidence or use. Keep engineering readiness, integration, measurement, comparison validity, promotion, and claims separate.
7. Return exactly `IMPLEMENTATION_READY`, `IMPLEMENTATION_REPAIR_REQUIRED`, `EVIDENCE_REQUIRED`, `PARENT_REVIEW_REQUIRED`, or `BLOCKED`. A positive result has no finding; every nonpositive result has at least one complete finding.

## Packet

```yaml
review_kind: implementation
review_mode: <materialization | recovery-reuse>
review_id: <unique identifier>
packet_path: <frontier/reviews/implementation-<review-id>-packet.yaml>
packet_id: <review kind and id plus SHA-256 of canonical packet bytes with this field omitted>
snapshot_root: <frontier/reviews/implementation-<review-id>-snapshot/>
snapshot_manifest: <snapshot_root/manifest.yaml and identity>
snapshot_id: <immutable snapshot identity>
task_path: <canonical task path>
problem_epoch: <integer>
problem_generated_at: <ISO-8601 datetime>
representation_revision: <integer>
representation_generated_at: <ISO-8601 datetime>
representation_permitted: <exact reviewed text>
campaign_generation: <positive integer>
recovery_lineage: <prior CLOSEOUT_COMPLETE, recovery V and X, inherited Budget, prior B/result/review, and exact reuse limits; or null>
candidate_recovery_preflight: <frozen finding-free preflight path, identity, validation, requested and recomputed candidate and manifest identities; or null>
batch_id: <code-bearing B identifier>
batch_packet: <immutable B packet path and packet_id>
batch_packet_preflight: <stable structural path, preflight_id, computed_packet_id, and packet-validator identity>
authorization_readiness: <Entry schema, AUTHORIZATION_READY, target, V, and Coordinator adoption identities>
changes_executable_candidate: <true>
work_plan: <W path, revision, and design contract identity; or exact direct packet_id>
design_review: <adopted DESIGN_READY path and identity, or not required under direct profile>
development_authorization: <external AUTHORIZATION_READY, V, Coordinator Entry-adoption, and frozen adoption-validation identities for the exact target>
required_design_inputs: [<exact indexed concern sections and identities implemented by this B, or none under direct profile>]
batch_acknowledgment: <stable acknowledgment path and identity from materialization, including historical source acknowledgment in recovery-reuse>
batch_execution_baseline: <stable content-addressed snapshot root, manifest, snapshot identity, and complete input count from materialization; historical source evidence under recovery-reuse>
batch_execution_start: <stable Coordinator-owned execution-start path and identity from materialization; in recovery-reuse, historical source record or null with the exact prior-interface and closeout evidence>
batch_result_validation: <stable finding-free validation path and identity reproduced against the final result; historical result disposition under recovery-reuse>
batch_result: <stable result-packet path and identity>
candidate_id: <immutable identifier>
candidate_manifest: <stable path and identity>
source_base_identity: <commit and dirty-state identity, or immutable source snapshot>
source_result_identity: <head commit and diff identity, content manifest, or immutable packaged source identity>
recovery_artifacts: [<stable recoverable bytes and identities needed without the live worktree>]
materialization_stop: <evidence that performance evaluation, integration, and incumbent use did not occur>
new_generation_zero_change_check: <not applicable for materialization, or exact proof that recovery wrote no candidate byte and created no proposal identity or spend>
snapshot_inputs: <exact snapshot_manifest#inputs reference; do not duplicate the array>
assigned_review_path: <frontier/reviews/implementation-<review-id>.md>
completion_check: <every implementation requirement receives a verdict and every finding cites snapshot evidence>
```

## Artifact

Only `review-frontier` writes the assigned file.

```markdown
---
type: Optimization Frontier Implementation Review
status: complete
review_id: <identifier>
review_result: <IMPLEMENTATION_READY | IMPLEMENTATION_REPAIR_REQUIRED | EVIDENCE_REQUIRED | PARENT_REVIEW_REQUIRED | BLOCKED>
reviewed_by: review-frontier/1
reviewed_at: "<ISO-8601 datetime>"
snapshot_packet: <path and identity>
candidate_id: <immutable identifier>
generated: { by: review-frontier/1, at: "<ISO-8601 datetime>" }
---

# FRONTIER IMPLEMENTATION REVIEW: <candidate name>

Result: <allowed result>
Candidate: <candidate identifier>
Reviewed snapshot: <packet path and identity>
Reviewed at: <ISO-8601 datetime>

## Readiness checks

- Parent, B, W, and permitted scope: <pass or findings>
- Review mode, campaign generation, and recovery lineage: <pass, not applicable, or findings>
- Candidate-recovery preflight order, canonical-byte identity, and zero-write mismatch behavior: <pass, not applicable, or findings>
- Design review, development authorization, and design inputs: <pass or findings>
- Repository structure and approval: <pass or findings>
- Source base, result, diff, and path ownership: <pass or findings>
- Packet structure, W traceability, readiness review, and authorization order: <pass or findings>
- Dispatch transition, execution-baseline recovery, and execution-frozen inputs: <pass or findings>
- Candidate interface and worker-forbidden paths: <pass or findings>
- Manifest, configuration, dependencies, runtime factors, and recovery: <pass or findings>
- Engineering checks and definition of done: <pass or findings>
- Evaluator and comparison-integrity protection: <pass or findings>
- Validated materialization stop, incumbent-use boundary, and claims: <pass or findings>

## Findings

### Finding 1: <omit when IMPLEMENTATION_READY>

- Result effect: <IMPLEMENTATION_REPAIR_REQUIRED | EVIDENCE_REQUIRED | PARENT_REVIEW_REQUIRED | BLOCKED>
- Affects: <paths, records, fields, or candidate identity>
- Requirement: <exact requirement>
- Observed: <snapshot fact>
- Evidence: <snapshot identities>
- Required correction: <observable condition; no repair text>
```
