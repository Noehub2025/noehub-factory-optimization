# Frontier Implementation Review

Load only when a later measurement, integration, external publication, irreversible operation, or other real Consequence requires independent technical judgment of one exact Git Candidate Revision, or when concrete contrary evidence affects a prior R. Ordinary implementation loops and harmless checks do not require this review.

## Current review method

The assigned subject contains one full Git commit and explicit Candidate Revision paths, applicable W sections or direct behavior target, relevant checks, dependencies that affect behavior, known findings, and the exact later Consequence the verdict may support. It needs no packet, snapshot, inventory, candidate ID, execution-start, authority lineage, content root, or closed collection.

1. Resolve the exact Git revision and inspect its source artifacts, behavior, and applicable checks.
2. Judge it against the requirements applicable to the proposed use, not exhaustive future behavior or a complete handoff. Build success or a smoke run is insufficient when the claimed readiness needs more. When attributing a defect, use relevant Git history and existing repair facts to distinguish a missed earlier requirement, newly clarified behavior and a changed objective. A later clarification is not proof it was handed off earlier; it can still matter to current readiness.
3. Distinguish implementation fidelity, current-use impact and a changed contract. For a new or inherited restriction that blocks the next action, excludes a needed observation, or materially increases cost, apply [Constrain effects, not convenient forms](technical-design.md#constrain-effects-not-convenient-forms) and, for a decision-bearing threshold, [its existing rules](frontier-core.md#decision-bearing-thresholds). Fidelity alone establishes neither the restriction's basis nor repair priority. Apply [Finding effects](finding-effects.md): return `IMPLEMENTATION_REPAIR_REQUIRED` only for a defect that needs correction for this use; a limited-impact defect may remain advisory with `IMPLEMENTATION_READY`. A necessary change in behavior, public seam, ownership, lifecycle, acceptance meaning, resource consequence, or load-bearing design assumption returns to the affected owner, without automatically requiring another independent review.
4. Check only the evidence required by the proposed later Consequence under [Assurance by consequence](batch-evaluation.md#assurance-by-consequence). Reuse prior checked facts and calculations within their assumptions; distinguish a remaining technical question from a subsequent output-integrity check. An external publication may need an external artifact version; routine local development does not. If routine updates in the reviewed implementation force code changes or block continuation, inspect the affected path under [Runtime records and resource use](batch-current.md#runtime-records-and-resource-use) and [Review applicability and adoption](batch-current.md#review-applicability-and-adoption). Confirm that record updates can reach the actual reader and accounting checks; a changed explanation alone does not establish that capability. Repair the affected behavior and reuse unrelated test and Review conclusions.
5. Return `IMPLEMENTATION_READY`, `IMPLEMENTATION_REPAIR_REQUIRED`, `EVIDENCE_REQUIRED`, `PARENT_REVIEW_REQUIRED`, or `BLOCKED`. State the exact Git revision, checked conclusions, findings, assumptions, maximum supported Consequence, and recovery condition.

`IMPLEMENTATION_READY` applies only to the reviewed Git bytes, assumptions, and named maximum Consequence. It does not itself grant V, spend, measurement, integration, promotion, publication, incumbent use, or a claim. A finding returns to the same B under [Current Batch](batch-current.md) unless the independently judged result changes.

Write one R through `review-frontier`. Return the material findings already visible in the assigned scope together; distinguish optional improvements from required corrections. Preserve earlier R records at their Git versions. A corrected revision receives a new R only when the later Consequence still needs independent judgment; review the changed dependencies and affected conclusions rather than restarting unaffected work. A newly exposed defect remains reportable; one-pass perfection is not a readiness requirement.

## Evidence at real boundaries

During ordinary implementation, the implementation owner supplies evidence for the promised deliverable and the dependencies needed by its next use. Build toward the earliest interpretable observation through integrated working steps; an exploratory observation need not satisfy unrelated final-delivery requirements. Start with relevant retained outputs, applicable external specifications, or inspection of existing implementations and dependencies. For a repair, correct the shared cause across the affected producer, transformation, consumers and result writer, rather than merely adding the last reported example. Exercise that affected path before returning the repair for any needed independent judgment. A synthetic fixture derived from the tested implementation's own expectations does not independently establish those expectations about a real dependency. Check that relevant expectations agree with actual behavior; passing counts cannot resolve contrary real evidence.

Fill only a gap that can affect the next action or interpretation, using the smallest sufficient observation through the existing permitted work path. Apply [Reuse working knowledge](batch-current.md#reuse-working-knowledge) for check selection and evidence reuse. A field mapping may be settled by retained data; a lifecycle or ordering assumption may need the relevant real interaction. Reuse the capability's existing verification entry point for a changed dependency or concrete uncovered assumption, without a routine coverage certificate. Establish that the check actually reaches the boundary being claimed: constructing a deferred loader, client or conversion plan does not prove loading, connection or conversion occurred. Reaching that boundary need not run the entire downstream operation or campaign. An unknown that the selected experiment is meant to test need not be resolved in advance: distinguish its question from an unsupported prerequisite for obtaining an interpretable answer.

Treat initialization and other executable checks by their actual effects. No game, measurement or remote request does not imply read-only behavior. Arrange them through existing engineering work and applicable effect controls, rather than silently expanding a read-only preflight. Reuse retained evidence where sufficient; this creates no new permission type.

For measurement support, follow the affected path from actual response through parsing, retained observation and classification to continuation or completion under [Delayed and changing observations](batch-evaluation.md#delayed-and-changing-observations). Check a relevant state sequence, not just isolated classifier cases: a correct final classifier is insufficient if an earlier parser makes its waiting branch unreachable. Reuse retained responses or source-grounded fixtures; this requires neither a full campaign test nor another live effect.

When execution wiring is the changed behavior, exercise its actual action construction, adapter installation, result writeback and reader together. Replace an expensive or external leaf when useful, but keep the connection under test real. Tests using a test-only Action, an always-passing review resolver or disabled input validation establish only the remaining path. Retained provider data or an authoritative implementation grounds a dependency expectation; additional synthetic cases alone do not. Reuse that evidence while its relevant assumptions hold.

Follow a material early-stop or failure result through the same writer and reader as normal completion. A permitted negative prefix must remain a usable partial observation; a protocol requiring complete data still cannot claim completion from that prefix. Preserve independently established raw facts when support fails, and preserve unknown effects when their occurrence is unresolved. An unforeseen result calls for investigation, not automatic invalidation of all observations or a success claim. Apply [Working assignments](worker-interfaces.md#working-assignments) to the affected repair or meaning change and continue unaffected work. Reading or repairing a report does not repeat its producing operation. Select branches important to the current evidence and next use, not a catalogue of all possible failures.

The reviewer judges whether retained or newly obtained evidence covers the proposed use and states any missing prerequisite within the assigned scope; it need not personally repeat sufficient checks. At normal adoption, the Coordinator uses those conclusions for the next action without inflating several local passes into whole-system readiness. Return a material gap to its existing implementation or measurement owner to fill before dependent work; do not add a coverage report, certification stage, or routine second review.

## Historical implementation review

The sections below are compatibility rules for retained review packets and candidate-package lifecycles that already use those fields. Do not generate them for a current Git-backed Batch.

### Historical review method

1. Select `materialization` or `recovery-reuse`. For `materialization`, require the frozen B target, authorization lineage, execution-start, exact transient inventory, closed implementation collection, cumulative attempt reports, design or direct target, source and dependency identities, engineering checks, allowed feedback, and evidence that formal publication, Slot H measurement, integration, and incumbent use have not occurred. Assess formal identity and charge against the existing parent-owned boundary under [Boundary-preserving continuation](batch-interface.md#boundary-preserving-continuation), not a separate no-charge rule in this review. Retained unpublished material uses the same `materialization` mode and its original producing execution evidence, even after closeout; current permission governs the proposed use, not the historical execution. No final manifest is required. For `recovery-reuse`, require the exact published material and the evidence needed for the affected conclusion under [Change impact and retained results](frontier-core.md#change-impact-and-retained-results).
2. Verify repository placement and the assigned interface against the reviewed disposition. An unapproved top-level root, toolchain or dependency-manager replacement, or public-entrypoint change is a finding.
3. For `materialization`, reproduce the exact review collection and transient inventory from project bytes. Require every planned Delivery slice, complete output, integration check, frozen engineering check, cumulative effect, and observable definition of done to be accounted for. An earlier passing realization may appear only with the preserved nonpositive review that caused its replacement. For `recovery-reuse`, verify the published inventory and manifest without changing any candidate byte.
4. Check implementation only against the assigned design inputs and candidate interface. Require the agreed architecture, entities, invariants, flows, failures, compatibility, rollback, observable definition of done, and distinguishing checks. Apply [Technical design's assignment ownership rule](technical-design.md#assign-the-professional-author): a different ordinary work method is not design infidelity. Method freedom neither changes frozen inputs, evidence, or explicit authorization constraints nor extends an existing review to different bytes. Build success or a smoke run alone is insufficient.
5. Distinguish fidelity from contract change. A fidelity finding identifies how the realization fails the unchanged target and returns `IMPLEMENTATION_REPAIR_REQUIRED`. A required change to behavior, public seam, ownership, lifecycle, acceptance meaning, input, effect, spend rule, stop rule, or load-bearing design assumption is not a fidelity repair; identify the affected contract and return the corresponding nonpositive result. Do not prescribe repair code or select the campaign route.
6. For `materialization`, confirm the reviewed bytes have not been published, formally measured, integrated, or used as an incumbent. An authorized working observation under Batch Interface may precede review only as cumulative B evidence inside its fixed question, methods, resources, exposure, and consequence ceiling; it is not formal measurement or a publication. `IMPLEMENTATION_READY` permits only authoritative publication of the exact reviewed inventory. It grants no formal measurement, integration, incumbent, promotion, or claim authority. For `recovery-reuse`, the maximum consequence remains the separately governed unchanged-candidate reuse path.
7. Return exactly `IMPLEMENTATION_READY`, `IMPLEMENTATION_REPAIR_REQUIRED`, `EVIDENCE_REQUIRED`, `PARENT_REVIEW_REQUIRED`, or `BLOCKED`. A positive result has no finding; every nonpositive result has at least one complete finding. State the exact affected realization, design input, or parent boundary.

### Historical packet

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
project_subject: <complete fixed review subject and identity; Git references or retained historical content>
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
materialization_stop: <evidence of no formal publication, measurement, integration, or incumbent use>
allowed_feedback: <exact frozen feedback boundary>
assigned_review_path: <exclusive review artifact path>
completion_check: <every implementation requirement receives an evidence-backed result>
```

`working_inventory`, `attempt_reports`, and `prior_review_repairs` use already assigned B evidence paths. They do not create a new checkpoint, candidate, or review-history artifact type. The review subject's closed collection binds the exact implementation bytes. For `recovery-reuse`, bind the published candidate and applicable original evidence instead of prepublication fields. For retained unpublished material, keep `prepublication` and the original execution-start; do not create a fictitious current-generation execution. Readiness does not grant publication or measurement permission.

### Historical artifact

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
