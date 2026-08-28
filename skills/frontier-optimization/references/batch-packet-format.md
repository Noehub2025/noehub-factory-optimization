# Batch packet compatibility formats

Read only when filling an existing compatibility payload or auditing a record that uses these fields. The current lifecycle and tool interface are owned by [Batch interface](batch-interface.md); these formats do not create a second identity writer.

## Authorization-target specification

For code-bearing work, freeze one source-derived specification before drafting the B packet. It states the stable decision semantics but contains no current packet, preflight, final-target, Entry, answer, adoption, acknowledgment, or execution-start identity. This keeps identity derivation acyclic:

```yaml
target_spec_id: <V identifier plus SHA-256 of exact bytes with this one top-level line omitted>
contract_version: frontier-authorization-target-specification/1
decision_id: <V identifier>
batch_id: <B identifier>
target_path: <exclusive future final-target path>
user_result_path: <exclusive future authorization-answer path>
decision_record_path: <task_path/frontier/ledger.md; one of post_adoption_paths>
design_contract_identity: <reviewed design or exact direct identity>
source_base_identity: <exact source-base identity>
scope: <exact bounded scope>
maximum_spend: <exact maximum spend>
stop_boundary: <exact stop boundary>
result_path: <exact B result path>
proposed_state_transition: {budget: <change>, selection: <change>, lifecycle: <change or null>}
post_adoption_paths: [<each Coordinator-owned live path the reviewed transition may replace>]
authorization_question: <exact question>
authorize_consequence: <maximum consequence of exact authorization>
decline_consequence: <consequence of decline>
conditional_consequence: <fresh-target consequence of a condition or changed scope>
```

The specification binds rules and paths, not post-adoption file bytes. Derive `decision_record_path` mechanically as `<packet.task_path>/frontier/ledger.md`; membership in `post_adoption_paths` alone is insufficient. This ledger remains the canonical V owner. The later user-result file carries the exact answer bytes, and adoption joins that result identity to the reviewed record path and target without putting a future identity in precomputed state bytes. After packet identity and structural preflight resolve, create complete post-adoption source files and the final authorization target. The final target binds the specification, packet, preflight, and exact post-adoption bytes and copies every stable specification field exactly. It uses only the canonical final-target fields; an extra authority field is not an extension. The Entry validator rejects a target that is broader, narrower, stale, or otherwise different. A final-target identity must never be excluded from packet hashing; it is simply not a packet input.

Inside the final target, `exact_object` is binding metadata, not a second authority surface:

```yaml
exact_object:
  batch_id: <B identifier>
  packet: {path: <packet path>, packet_id: <derived packet identity>, file_sha256: <exact digest>}
  structural_preflight: {path: <preflight path>, preflight_id: <derived preflight identity>, file_sha256: <exact digest>}
  reviewed_bindings: <the exact Entry design_gate.bindings list, in the same order>
```

No other `exact_object` fields are accepted. Authority remains exclusively in the stable top-level fields copied from the specification.

## Batch packet

```yaml
packet_path: <frontier/batches/<B identifier>-packet.yaml or another exclusive stable path>
packet_preflight_path: <stable Coordinator-owned JSON path assigned only to this packet>
packet_id: <absent in the draft; after preflight PASS, B identifier plus SHA-256 of canonical packet bytes with this field omitted>
task_path: <canonical task path>
batch_id: <B identifier>
campaign_generation: <positive integer>
route_id: <T identifier or null>
campaign_baseline: <selected T identifier and role, plus incumbent E identifier when one exists, or null>
work_kind: <design | prototype | code | human_input | experiment | research | external_action | mixed>
changes_executable_candidate: <true | false>
executor: <Agent, user, tool, service, or team>
required_inputs: [<identifiers, paths, schemas, or prerequisites>]
identity_contract: frontier-dispatch-identity/2
result_contract_version: frontier-batch-result/2
decision_root: <exact frontier-decision-root-sha256 identity>
project_content_roots: [<typed project roots required by this packet>]
work_plan: <W path or null>
work_plan_revision: <integer or null>
design_contract_identity: <immutable reviewed design identity, exact direct packet_id, or null>
design_contract_binding: {path: <exact source file>, identity_field: <top-level field or null for file identity>, identity: <derived identity>, file_sha256: <lowercase digest>}
design_profile: <direct | module | system | not-applicable>
required_design_inputs: [<exact W or indexed design concern path, section, and identity; or none>]
design_traceability: <for module or system, exact machine-readable traceability path and whole-file SHA-256; otherwise null>
design_review: <adopted DESIGN_READY path and identity, pending for design work, or null under direct or non-code-bearing work>
development_authorization_target: <for any pending user authorization, {contract_version: frontier-authorization-target-specification/1, path: <exact pre-packet specification path>, identity_field: target_spec_id, identity: <source-derived target_spec_id>, file_sha256: <exact file digest>}; otherwise null>
parallel_set: <label or null>
problem_epoch: <integer>
problem_generated_at: <ISO-8601 datetime>
representation_revision: <integer>
representation_generated_at: <ISO-8601 datetime>
permitted_scope: <exact reviewed text>
starting_artifacts: [<identifiers or paths>]
supporting_evidence: [<Q, V, E, or D identifiers>]
work: <bounded actions>
human_input_request: <exact request and response location, or null>
human_input_schema: <fields, types, units, allowed omissions, and format, or null>
human_input_provenance_requirements: <required source metadata and authenticity checks, or null>
human_input_quality_checks: [<completeness, consistency, legality, domain, or other checks; or none>]
human_input_confidentiality: <handling and destination limits, or null>
human_input_acceptance: <accept or reject conditions and resume event, or null>
repository_structure_disposition: <existing-integrated | absent-awaiting-user | user-approved-new | not-applicable>
repository_structure_evidence: [<project paths, manifests, conventions, or absence checks>]
repository_layout_approval: <V identifier for a new or materially changed layout, or null>
source_base_identity: <commit and dirty-state identity, immutable source snapshot, or null>
source_base_binding: {path: <exact source manifest or snapshot>, identity_field: <top-level field or null for file identity>, identity: <source_base_identity>, file_sha256: <lowercase digest>}
workspace_identity: <branch and worktree, shared sequential workspace with reason, or null>
candidate_interface: <existing or user-approved seam and callers, or null>
allowed_code_paths: [<exclusive paths or none>]
worker_forbidden_paths: [<paths or exact sections the worker must not write, or none>]
execution_frozen_inputs: [<mapping with repository-relative path, file or subtree scope, exact section when narrower than a file, and pre-start identity that no actor may change during execution; or none>]
coordinator_lifecycle_transition: <null when campaign is already running; otherwise the structured first-B contract below>
execution_baseline_root: <exclusive Coordinator-owned subtree in which freeze_execution_baseline.py creates one content-addressed snapshot directory>
execution_start_path: <stable Coordinator-owned path assigned only to this batch>
candidate_root_path: <complete candidate-package root for code-bearing work; otherwise null>
candidate_package_inventory_path: <assigned official immutable inventory path written at publication for code-bearing work; earlier charge evidence stays in the existing accounting source; otherwise null>
candidate_manifest_path: <assigned stable path or null>
engineering_check_plan: <repository-relative path to one frontier-project-engineering-check-plan/1 frozen as a file input, or null>
# Historical version 1 compatibility only. Current project writers omit this
# copy and derive publication and charge behavior from the parent or R8 rule.
publication_policy:
  contract_version: frontier-authoritative-output-publication/1
  charge_event: <historically frozen event>
  charge_amount: <historically frozen amount and unit>
  charge_basis: {kind: <parent-rule | workflow-default>, path: <historical parent bytes>, file_sha256: <lowercase digest>, locator: <exact rule location>}
  repair_mode: <prohibited | deterministic-fidelity-only>
  effect_scope: deterministic-local-checks-only
  authoritative_output_path: <historically assigned output path>
  engineering_evidence_path: <historically assigned evidence path>
implementation_review_gate: <required before first Slot H measurement, integration, or incumbent use; exact diagnostic-only exception under candidate-lifecycle.md; reusable review with exact unchanged identity; or null>
evaluation_target: <canonical experiment target, or an explicitly authorized working_scope diagnostic for any supported work kind; otherwise null>
preparation_role: <why this work is necessary on the baseline path or null>
decision_hypothesis: <mechanism or assumption this batch tests or advances>
expected_observation: <observable result and direction, including what would contradict the hypothesis>
output_contract: <one complete bounded realization or design artifact and its observable behavior>
implementation_validation: <exact checks or WORK.md section>
implementation_definition_of_done: <exact conditions or WORK.md section>
permitted_operations: [<substantive operations or modules and the execution-support operations needed to preserve and validate their evidence>]
allowed_feedback: <exact information>
maximum_spend: <maximum amount and unit under the parent or R8 rule>
accounting_source: <path or system>
authorization_gate: <finding-free authorization-readiness review followed by exact user V and Coordinator Entry adoption; direct spend-readiness when no user authorization applies; adopted REPLAN_READY for a strategic later change; adopted implementation review before first Slot H measurement, integration, or incumbent use; exact diagnostic-only path under candidate-lifecycle.md; or exact later campaign-cycle Selection authority>
authorization_boundary: {scope: <exact reviewed scope>, maximum_spend: <same value as maximum_spend>, stop_boundary: <single exact boundary>, result_path: <same value as result_packet_path>}
baseline_establishment_checkpoint: <usable artifact and completion check or null>
first_performance_check: <comparison or decision result, and whether this batch or a later batch runs it>
preparation_budget_limit: <maximum allocation before that check>
required_follow_up_reserve: <amount and mandatory confirmation or recovery purpose, or null with governing rule>
decision_after_checkpoint: <observable route or allocation decision>
measurement: <Slot H identity and checks, or exact later evaluation path>
comparison_validity_checks: <measurement identity, comparable conditions, data quality, drift, confounding, and execution checks required when measuring a result>
candidate_identity_rule: <Slot B identity>
constraints: <required legality checks>
artifact_paths: [<paths assigned only to this batch, including distinct attempt-evidence paths or one exclusive evidence subtree>]
acknowledgment_path: <stable path assigned only to this batch>
result_validation_path: <stable worker-owned deterministic validation artifact written before the final result path>
result_packet_path: <stable path assigned only to this batch>
resume_when: <available input, event, or immediate>
stop_conditions: [<substantive boundary, resource exhaustion, unresolved side effect, or task-specific conditions; apply boundary-preserving continuation before terminalizing a support failure>]
forced_halts: [<conditions>]
prohibited_actions: [<actions and claims>]
```

Do not compute `packet_id` yet. First complete the deterministic structural preflight below. Only a finding-free draft may be serialized canonically without `packet_id`, hashed, given the preflight's exact `computed_packet_id`, and frozen at `packet_path`. Rerun frozen preflight and require byte-identical PASS output before freezing an authorization-readiness project snapshot. Never overwrite the packet after that point. `identity_contract`, `decision_root`, typed project content roots, `design_contract_binding`, `source_base_binding`, `authorization_boundary`, and the source-derived authorization-target specification make the project authority inputs immutable without creating an identity cycle. Workflow release, Skill, validator implementation, test, and source-module roots are forbidden. This preflight establishes packet structure, not user authorization. A later user V must cite the final target, immutable packet, preflight, finding-free authorization-readiness review, design or direct identity, source base, scope, spend, and stop boundary.

The `publication_policy` mapping in this legacy template exists only so the exact version 1 reader can reproduce historical packets. Do not place it in a current project decision or treat it as another authority source.

For work with formal engineering checks, freeze the required check plan before packet identity. Declare consequential resource use, access, sampling, external effects, and evidence-sensitive conditions, using the existing containment or check evidence; do not enumerate harmless internal operations or require a separate proof for each. Every declared limited effect retains its positive maximum and conservative cost. Choose checks for the affected obligations and required integration, not an unchanged repository-wide baseline by default. `full-repository` freezes every collected unit only when genuinely necessary. Existing formally required check coverage remains binding. Reuse unaffected research, design, or calibration evidence by its actual dependencies, without a reuse report or cache framework. Engineering evidence cannot support promotion, incumbent use, or a strength claim.

The package inventory and final manifest follow Candidate Lifecycle's single forward dependency chain. Each transient inventory exists before its runtime staging. The final passing inventory is reviewed before publication; the official inventory is then written only from byte-identical reviewed bytes. Completed engineering evidence binds the official inventory and any nonpositive review-repair chain. The final manifest binds that evidence, the official inventory, and the final positive implementation review. Result validation and the result bind the final manifest; the manifest never binds those downstream artifacts.

For `work_kind: experiment`, use one result-binding shape in both packet and result:

```yaml
evaluation_target:
  mode: <formal-slot-h | diagnostic-only>
  candidate:
    id: <immutable candidate identity>
    root_path: <complete immutable candidate-package root>
    manifest_path: <immutable candidate manifest path>
    manifest_sha256: <exact lowercase SHA-256 digest, optionally prefixed by sha256:>
  implementation_review: # formal-slot-h only
    review_id: <R identifier>
    result: IMPLEMENTATION_READY
    path: <immutable implementation-review path>
    file_sha256: <exact lowercase SHA-256 digest, optionally prefixed by sha256:>
  experiment:
    path: <immutable experiment contract path>
    experiment_id: <identity binding evaluator, data, controls, protocol, environment, budget, generation, and result paths>
    file_sha256: <exact lowercase SHA-256 digest, optionally prefixed by sha256:>
  slot_h_contract: # formal-slot-h only
    path: <Slot H contract path>
    file_sha256: <exact lowercase SHA-256 digest, optionally prefixed by sha256:>
```

Diagnostic-only targets use either `working_scope` or the published-candidate `exception_evidence`, with `consequence_limit: B evidence only` and the complete prohibited-consequence list. They omit implementation and Slot H review bindings. The result reproduces the complete target exactly; actual working-subject identities belong in observations. Keep `evaluation_target.experiment` as the sole experiment-identity owner. Verify its contract bytes and all applicable candidate, review, or Slot H bindings before use; unpublished working observations have no candidate manifest to verify. Result validation selects the branch from the frozen target, never the worker's performance-state label.

The referenced source declares its own identity field through one supported top-level `identity_rule`. That field may use a descriptive name such as `matrix_id`; `evaluation_target.experiment.experiment_id` remains the canonical binding and must equal the source field's value. Entry preparation and result publication apply the same declared omit-line SHA-256 rule to the same exact source bytes and verify `file_sha256`. Never infer an identity field from its name or from another field that happens to contain the same value.

Path fields have three different meanings and are not interchangeable:

- `allowed_code_paths`, `artifact_paths`, acknowledgment, result validation, result, and assigned W sections are the worker's exclusive write surface.
- `worker_forbidden_paths` restrict only the worker. They may contain Coordinator-owned campaign records, but they must not overlap any worker write surface.
- `execution_frozen_inputs` are globally immutable only from the accepted execution-start record through the terminal result. Record an exact file or section identity; do not freeze a whole directory that contains a worker write surface, the execution-start record, or a required Coordinator lifecycle write.
- `execution_baseline_root` is a Coordinator-owned output subtree. It may overlap neither worker writes nor any frozen input or other Coordinator output.

For `module` or `system`, never freeze the whole mutable `WORK.md`. Bind the immutable design through `design_contract_identity`, the indexed contract sections and concerns, and `design_traceability`. Current authorization lives only in V, Selection, ledger, and the Coordinator-owned Entry-adoption artifact. It is not a W field and cannot change the design identity.

For the first B of a planned campaign, the immutable packet authorizes a deterministic transition rule, not values predicted before execution. Use exactly this contract:

```yaml
coordinator_lifecycle_transition:
  contract_version: frontier-lifecycle-transition/1
  path: <exact task FRONTIER.md path>
  prerequisite: <accepted acknowledgment identity requirement>
  deadline: before execution baseline and execution-start
  precondition:
    campaign_status: planned
    file_identity: sha256:<exact lowercase digest of pre-transition bytes>
  transition_time:
    capture: once_after_accepted_acknowledgment
    format: RFC3339
    timezone: UTC
  allowed_field_diff:
    campaign_status: {from: planned, to: running}
    generated.at: {derive: transition_time}
    updated: {derive: calendar_date, source: transition_time, timezone: UTC}
  all_other_bytes: unchanged
  on_failure: block_before_work_and_spend
```

Capture one UTC instant after the acknowledgment is accepted and use that same value for `generated.at` and the UTC calendar date in `updated`. A runtime-derived timestamp or date is never a packet literal. A literal date is valid only when the date itself is an intentional, expiring business constraint with an explicit validity check; it cannot stand in for transition metadata. Runtime values that can change scope, spend, authority, candidate identity, evaluator, data, or permissions remain material choices and require a new reviewed packet rather than this derivation rule.

The Coordinator applies only the three authorized field changes while preserving every other byte. A precondition mismatch, ambiguous timezone, second clock read, extra field change, or inability to prove the exact diff blocks before baseline creation, work, or spend. When the campaign is already running, record `null`. A packet that omits a required transition, uses prose instead of this structure, permits a broader edit, overlaps the transition with an execution-frozen input, or cannot distinguish worker prohibition from global immutability is rejected before acknowledgment.

## Packet preflight

Use [validate_batch_packet.py](../scripts/validate_batch_packet.py) before packet identity or authorization-readiness review:

```bash
python .agents/skills/frontier-optimization/scripts/validate_batch_packet.py \
  <draft-packet-path> --phase draft --output <packet_preflight_path>
```

The draft already contains every field except `packet_id`, including `packet_preflight_path`, worker outputs, Coordinator outputs, forbidden paths, frozen paths, lifecycle outputs, prohibitions, the experiment result binding when applicable, and the machine-readable W traceability binding when applicable. The validator canonicalizes repository-relative paths, checks exact and ancestor/descendant overlap, verifies every W evidence destination is covered by the worker write surface, rejects whole-W freezing, calls the same experiment-contract logic used by result validation, reproduces the omit-field packet payload hash, and writes one deterministic JSON artifact:

```json
{
  "validator": "frontier-batch-packet-preflight/9",
  "batch_id": "<B identifier>",
  "packet_path": "<packet path>",
  "packet_payload_sha256": "<SHA-256>",
  "computed_packet_id": "<exact future packet_id>",
  "packet_structure_ready": true,
  "result_contract_probe": {
    "validator": "frontier-batch-result-preflight/7",
    "validation_id": "<complete synthetic experiment-result draft validation identity, or null when not applicable>"
  },
  "checks": {
    "worker_write_vs_forbidden": "PASS",
    "coordinator_outputs_vs_worker": "PASS",
    "coordinator_path_exclusivity": "PASS",
    "worker_output_role_exclusivity": "PASS",
    "frozen_paths_vs_outputs": "PASS",
    "required_outputs_vs_prohibitions": "PASS",
    "packet_identity": "PASS",
    "path_schema": "PASS",
    "lifecycle_transition_contract": "PASS",
    "result_contract_compatibility": "PASS",
    "work_plan_traceability": "PASS"
  },
  "normalized_ownership": {
    "worker_write_paths": ["<path>"],
    "worker_forbidden_paths": ["<path>"],
    "coordinator_paths": ["<path>"],
    "execution_frozen_paths": ["<path>"]
  },
  "findings": [],
  "blocking_findings": [],
  "repair_findings": [],
  "advisories": [],
  "finding_effect_counts": {"block": 0, "repair": 0, "advisory": 0},
  "preflight_id": "<content-addressed identity>"
}
```

Apply [Finding effects](finding-effects.md). Any `block` or `repair` finding returns nonzero and forbids packet freezing and authorization-readiness review; an advisory remains in output and preserves readiness. Draft the packet and preflight in transient paths; failed bytes are diagnostic evidence, not immutable lifecycle objects. While the B objective, target specification, candidate or source, inputs, evaluator, sampling, comparison and acceptance semantics, scope, spend, effects, stop, and result consequence remain unchanged and no answer, adoption, acknowledgment, execution effect, spend, or result exists, repair and rerun the draft under the same B. After PASS, atomically publish the packet and preflight to their exclusive paths, insert only `computed_packet_id`, and rerun with `--phase frozen` to a temporary path. The frozen run must reproduce the published preflight bytes; otherwise the project realization changed or the identity is wrong. A workflow update never invalidates or migrates a project packet, review, authority, acknowledgment, result, or spend gate. A substantive project change creates a new plan and applicable review; an authoritative result requires a new immutable packet under Boundary-preserving continuation. Do not create a review snapshot, target question, reservation, acknowledgment, work, or spend from failed draft bytes.

`--phase audit` exists only for immutable version 1 packets selected by the exact rollout inventory. It may explain an old failure but cannot create, repair, review, authorize, acknowledge, execute, or spend from a new legacy object. A current packet continues through its exact project decision root and stable project dispatch and result bytes. Workflow updates never alter it.

The required invariants include:

- worker write paths do not equal, contain, or fall under worker-forbidden paths;
- `execution_start_path`, `execution_baseline_root`, `packet_path`, and `packet_preflight_path` do not overlap worker writes;
- packet, preflight, execution-baseline root, execution-start, and lifecycle outputs are mutually exclusive Coordinator paths;
- acknowledgment, result validation, result, and candidate-manifest roles use mutually exclusive worker paths;
- acknowledgment belongs to the worker and execution-start belongs to the Coordinator;
- no execution-frozen subtree contains worker output, packet preflight, execution-start, or a Coordinator lifecycle output;
- an experiment packet uses the canonical nested `evaluation_target` and can produce a result with the same exact binding;
- a code-bearing packet binds a finding-free `frontier-authorization-target-specification/1` whose batch, design, source, scope, spend, stop, and result fields equal the packet;
- a module or system packet does not freeze its whole W, freezes the exact traceability file, exactly matches its Delivery and required-design-input mapping, and covers every evidence destination in that file;
- `prohibited_actions` does not deny acknowledgment, result, or candidate-manifest writes that the packet requires; and
- the frozen `packet_id` exactly matches the validated draft payload.

Authorization-readiness review supplies the full semantic gate after this structural check. Acknowledgment repeats frozen preflight as defense in depth.

## Batch acknowledgment

Before work or spend, `run-frontier-batch` writes the assigned acknowledgment. It confirms the packet as received; it does not create authority or repair a bad packet. This phase verifies exact immutable identities and requires no current-state receipt, observation time, or expiry. A later authority, Budget, reservation, input, resource, or project-state change leaves the acknowledgment intact and blocks at the applicable execution or spend gate.

```yaml
acknowledgment_id: <B identifier plus SHA-256 of canonical acknowledgment bytes with this field omitted>
batch_id: <B identifier>
packet_id: <verified batch packet identity>
decision_root: <exact packet decision root>
packet_preflight_id: <preflight_id recomputed from the frozen packet>
authority_id: <frozen authorization-adoption identity>
authority_validation_id: <finding-free adoption-validation identity>
acknowledgment: <accepted | blocked>
blocker: <null or exact reason>
```

The worker may include detailed scope, spend, path, input, and prohibition checks from the packet, but the fields above are the machine authority chain. Compute `acknowledgment_id` after every other field resolves and never overwrite an acknowledged path. The worker returns `BLOCKED` without work or spend when any acknowledgment row conflicts. Preserve that acknowledgment and cite it from the result packet.

An accepted acknowledgment ends the acknowledgment phase. It does not let the worker start work or spend. The worker returns control to the Coordinator and waits for the immutable execution-start record.

## Batch execution start

After an accepted acknowledgment, the Coordinator applies only the complete post-state files bound by the reviewed target's `frontier-post-adoption-state/1` contract and verifies that no other snapshotted project member changed. Before writing execution-start, it captures every post-transition baseline byte in one filtered project Git tree and writes only its small manifest under the packet's exclusive `execution_baseline_root`. The manifest SHA-256 is the authority identity; the reachable Git commit stores and deduplicates the bytes. A hash without reachable verified bytes is not a frozen baseline.

Use the bound baseline tool to create the content-addressed snapshot and final execution-start record in one fail-closed operation:

```bash
python .agents/skills/frontier-optimization/scripts/freeze_execution_baseline.py freeze \
  <execution-start-draft-path> \
  --snapshot-root <execution_baseline_root> \
  --output <execution_start_path>
```

The version 1 draft has every field below except `execution_start_id` and `baseline_snapshot`. Every `post_transition_baseline` row uses `scope: file | subtree` and a lowercase `sha256:<digest>`. File identity is SHA-256 over exact bytes. Subtree identity uses `frontier-tree-path-sha256/1`: SHA-256 over canonical JSON containing the sorted relative member paths and member SHA-256 values. Candidate and package trees use the separately named `frontier-package-path-size-sha256/1`; neither bare digest may be interpreted under the other algorithm. The tool rejects missing, changed, duplicate, symbolic-link, unsafe, or non-regular input; refuses any existing snapshot root or execution-start path; writes the selected raw bytes to one reachable filtered Git tree; writes `project-snapshot.yaml`; computes `snapshot_id`; binds it into execution-start; computes `execution_start_id`; and writes the final execution-start path exactly once.

The final record is:

```yaml
execution_start_path: <exact assigned Coordinator-owned path>
execution_start_id: <B identifier plus SHA-256 of canonical execution-start bytes with this field omitted>
packet_path: <exact batch packet path>
packet_id: <verified batch packet identity>
decision_root: <exact packet decision root>
packet_preflight: {path: <JSON path>, identity_field: preflight_id, identity: <recomputed preflight_id>, file_sha256: <exact digest>}
execution_authority:
  mode: <authorization-adoption | spend-readiness>
  entry_packet: <for spend-readiness only: {path, identity_field: packet_id, identity, file_sha256}>
  record: <adoption binding with identity_field: adoption_id, or ENTRY_READY review binding with identity_field: null>
  validation: <adoption validation binding with identity_field: validation_id, or Entry schema binding with identity_field: entry_schema_id>
acknowledgment: {path: <acknowledgment path>, identity_field: acknowledgment_id, identity: <acknowledgment_id>, file_sha256: <exact digest>}
batch_id: <B identifier>
campaign_generation: <positive integer matched to packet and FRONTIER.md>
recorded_by: frontier-optimization/1
recorded_at: <ISO-8601 datetime>
lifecycle_transition: <null when no transition was required; otherwise the structured transition receipt below>
post_adoption_state: <null for spend-readiness; otherwise the exact frontier-post-adoption-state/1 receipt derived by the baseline tool>
post_transition_baseline: [<every execution-frozen and other action-controlling file or subtree, its scope, and exact live identity>]
baseline_snapshot:
  root: <execution_baseline_root>/<snapshot digest>
  manifest: <root>/manifest.yaml
  snapshot_id: <B identifier plus SHA-256 of canonical manifest bytes with snapshot_id omitted>
  input_count: <exact number of post_transition_baseline rows>
worker_may_start: <yes | no>
blocker: <null or exact reason>
```

For `frontier-lifecycle-transition/1`, the receipt is:

```yaml
lifecycle_transition:
  contract_version: frontier-lifecycle-transition/1
  path: <exact task FRONTIER.md path>
  transition_timestamp: <captured RFC3339 UTC instant ending in Z>
  timezone: UTC
  derived_updated: <UTC calendar date derived from transition_timestamp>
  pre_change_identity: sha256:<exact pre-transition bytes>
  post_change_identity: sha256:<exact post-transition bytes>
  observed_field_diff:
    campaign_status: {from: planned, to: running}
    generated.at: {from: <prior timestamp>, to: <transition_timestamp>}
    updated: {from: <prior date>, to: <derived_updated>}
```

`recorded_at` cannot precede `transition_timestamp`. The lifecycle target appears exactly once as a file in `post_transition_baseline`, using `post_change_identity`. The baseline tool verifies the packet contract, precondition binding, UTC derivation, exact three-field receipt, live post-transition bytes, frontmatter values, and project-snapshot identity before it writes either immutable output. Historical execution-start records remain audit evidence only; this contract applies to new authority.

For user-owned authorization, `post_adoption_state` is a derived receipt containing the contract version, target, adoption, and user-result identities, plus the pre- and post-state digest for each reviewed file. The Coordinator does not author this receipt independently. The baseline tool recomputes authorization from the immutable pre-transition snapshot, verifies every listed live file against its complete reviewed post-state bytes, verifies every other snapshot-copy input against its unchanged snapshot bytes, and requires each transitioned file exactly once in `post_transition_baseline`. A partial transition, an extra change, a changed frozen post-state source, or a self-declared receipt blocks before work or spend.

Before minting `execution_start_id`, the baseline tool reruns the frozen packet validator and requires the stored packet-preflight bytes to equal the deterministic recomputation. For user-owned authorization it reruns the exact frozen adoption validator against the Entry snapshot, then performs the separate post-adoption live-state check above; for direct spend-readiness it reruns the exact frozen Entry packet and requires an `ENTRY_READY` review whose frontmatter binds that packet and snapshot. It requires the stored validation bytes to match and derives the acknowledgment from its own bytes. The snapshot manifest has one row per baseline entry and records source path, scope, declared and recomputed identity, snapshot path, and sorted members for a subtree. The tool computes `execution_start_id` after every other field resolves and never overwrites either output. The record creates no new scope or budget; it proves that the acknowledged packet can begin under a coherent and recoverable post-transition baseline. `worker_may_start: no`, a missing or stale record, missing snapshot byte, unexpected acknowledgment-to-start change, incorrect lifecycle rule or receipt, or baseline mismatch returns `BLOCKED` without work or spend.

An immutable version 1 packet is audit-only unless `.frontier/provenance-rollout.yaml` explicitly permits its exact authority, scope, and next descendant. That compatibility branch verifies the frozen packet preflight, Entry or adoption validation, every project file identity, authorization chain, acknowledgment, post-adoption state, and execution baseline. Archived workflow source remains inert audit evidence. The branch cannot create a new review or authorization, execute archived code, repair or migrate history, replay authority onto another packet, or broaden a B.

On the execution-phase invocation, `run-frontier-batch` runs `freeze_execution_baseline.py verify <execution_start_path> --live`, verifies the execution-start and snapshot identities, and matches every live post-transition baseline byte before work. It repeats live verification before writing the terminal result. Only then does it set `started_at` and begin spend. Drift in an execution-frozen input after this point forces a halt. A change only to a worker-forbidden path is not itself drift; it is a worker violation only when the worker made it, unless that path is also listed separately as an execution-frozen input. Later implementation review verifies the immutable snapshot without `--live`, so normal post-terminal campaign-record updates cannot erase start-time evidence.
