# Frontier Implementation Review

Load only when a code-bearing B has one complete all-pass realization ready for prepublication review, when the same B returns repaired fidelity bytes for another review, or when a post-closeout recovery Entry proposes an unchanged published candidate.

Use a new immutable review packet and path for each exact realization. Preserve every verdict. Include no expected verdict, suspected defect, or proposed repair.

## Review method

1. Select `materialization` or `recovery-reuse`. For `materialization`, require the frozen B target, authorization lineage, execution-start, exact transient inventory, closed implementation collection, cumulative attempt reports, design or direct target, source and dependency identities, engineering checks, allowed feedback, and evidence that formal publication, candidate identity, proposal charge, Slot H measurement, integration, and incumbent use have not occurred. For `recovery-reuse`, require the published candidate's complete historical materialization, new-generation authority, and finding-free no-change recovery preflight.
2. Verify repository placement and the assigned interface against the reviewed disposition. An unapproved top-level root, toolchain or dependency-manager replacement, or public-entrypoint change is a finding.
3. For `materialization`, reproduce the exact review collection and transient inventory from project bytes. Require every planned Delivery slice, complete output, integration check, frozen engineering check, cumulative effect, and observable definition of done to be accounted for. An earlier passing realization may appear only with the preserved nonpositive review that caused its replacement. For `recovery-reuse`, verify the published inventory and manifest without changing any candidate byte.
4. Check implementation only against the assigned design inputs and candidate interface. Require the agreed architecture, entities, invariants, flows, failures, compatibility, rollback, observable definition of done, and distinguishing checks. Build success or a smoke run alone is insufficient.
5. Distinguish fidelity from contract change. A fidelity finding identifies how the realization fails the unchanged target and returns `IMPLEMENTATION_REPAIR_REQUIRED`. A required change to behavior, public seam, ownership, lifecycle, acceptance meaning, input, effect, spend rule, stop rule, or load-bearing design assumption is not a fidelity repair; identify the affected contract and return the corresponding nonpositive result. Do not prescribe repair code or select the campaign route.
6. Confirm the reviewed bytes have not been published, measured, integrated, or used as an incumbent. `IMPLEMENTATION_READY` permits only authoritative publication of the exact reviewed inventory. It grants no measurement, integration, incumbent, promotion, or claim authority. For `recovery-reuse`, the maximum consequence remains the separately governed unchanged-candidate reuse path.
7. Return exactly `IMPLEMENTATION_READY`, `IMPLEMENTATION_REPAIR_REQUIRED`, `EVIDENCE_REQUIRED`, `PARENT_REVIEW_REQUIRED`, or `BLOCKED`. A positive result has no finding; every nonpositive result has at least one complete finding. State the exact affected realization, design input, or parent boundary.

## Packet

Use the existing implementation review input and complete project review subject. For `materialization`, bind the working realization rather than a final result or manifest:

The existing `project/decision/implementation/` input contains the current role-adapter fields below. This is part of the review subject, not a new lifecycle artifact:

```yaml
contract_version: frontier-project-implementation-review-input/1
affected_scope: <complete realization under review>
candidate: <byte-derived working realization identity and inventory binding>
reviewed_design: <W design identity or exact direct target>
publication_state: prepublication
execution_start: <exact released execution identity>
engineering_state: {status: pass, final_attempt: <positive sequence>}
allowed_feedback: <fidelity boundary of the unchanged reviewed target>
```

```yaml
review_kind: implementation
review_mode: <materialization | recovery-reuse>
review_id: <unique identifier>
packet_path: <assigned immutable review packet>
packet_id: <content-derived identity>
decision_root: <exact implementation decision root>
project_subject: <complete portable review subject and identity>
task_path: <canonical task path>
campaign_generation: <positive integer>
batch_id: <code-bearing B identifier>
batch_target: <frozen packet or current project plan identity>
development_authorization: <exact reviewed authority lineage>
batch_execution_start: <exact execution-start identity>
work_plan: <W revision and design identity, or direct target>
required_design_inputs: [<exact pointers and identities>]
working_inventory: <transient inventory path, inventory identity, file SHA-256, and candidate identity>
attempt_reports: [<ordered reports from execution-start through this inventory>]
prior_review_repairs: [<earlier passing inventory and its nonpositive review handoff, or none>]
source_base_identity: <recoverable source identity>
dependency_identity: <resolved dependency identity or explicit none>
materialization_stop: <evidence of no formal publication, charge, measurement, integration, or incumbent use>
allowed_feedback: <exact frozen feedback boundary>
assigned_review_path: <exclusive review artifact path>
completion_check: <every implementation requirement receives an evidence-backed result>
```

`working_inventory`, `attempt_reports`, and `prior_review_repairs` use already assigned B evidence paths. They do not create a new checkpoint, candidate, or review-history artifact type. The review subject's closed collection binds the exact implementation bytes. For `recovery-reuse`, retain the existing published candidate, manifest, prior result, closeout, and recovery-preflight bindings instead of the prepublication fields that do not apply.

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
candidate_id: <byte-derived working or published candidate identifier>
generated: { by: review-frontier/1, at: "<ISO-8601 datetime>" }
---

# FRONTIER IMPLEMENTATION REVIEW: <realization name>

Result: <allowed result>
Candidate: <candidate identifier>
Reviewed snapshot: <packet path and identity>
Reviewed at: <ISO-8601 datetime>

## Readiness checks

- Parent, B, W, and permitted scope: <pass or findings>
- Review mode and campaign generation: <pass or findings>
- Development authorization and execution-start: <pass or findings>
- Exact inventory and closed collection: <pass or findings>
- Delivery slices, engineering checks, and cumulative attempts: <pass or findings>
- Design inputs, interface, behavior, and failures: <pass or findings>
- Source, dependencies, recovery, and path ownership: <pass or findings>
- Prepublication or recovery boundary: <pass or findings>

## Findings

### Finding 1: <omit when IMPLEMENTATION_READY>

- Result effect: <allowed nonpositive result>
- Affects: <exact bytes, requirement, design input, or parent boundary>
- Requirement: <exact requirement>
- Observed: <snapshot fact>
- Evidence: <immutable project evidence>
- Completion condition: <observable condition for a later complete subject>
```

The review is complete when every assigned requirement has an evidence-backed result, the artifact passes its completion check, and its maximum consequence is limited to the exact reviewed realization.
