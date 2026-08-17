# Frontier Batch Interface

Load for one selected B before invoking `run-frontier-batch`, validating its result, or resuming it. Load `candidate-lifecycle.md` additionally only when `changes_executable_candidate: true` or implementation-review reuse is in question.

## Contents

- [Dispatch state machine](#dispatch-state-machine)
- [Boundary-preserving continuation](#boundary-preserving-continuation)
- [Authorization-target specification](#authorization-target-specification)
- [Batch packet](#batch-packet)
- [Packet preflight](#packet-preflight)
- [Batch acknowledgment](#batch-acknowledgment)
- [Batch execution start](#batch-execution-start)
- [Batch result](#batch-result)

## Dispatch state machine

This file is the sole interface for dispatching one B. Coordinator and worker instructions point here instead of restating the sequence.

For a new B, represent the lifecycle with the typed version 2 graph in
[Provenance and identity](provenance-and-identity.md): the frozen packet and
Entry or Replan state form the decision root; a content-addressed validation
report forms its attestation; accepted authority binds those two immediate
parents; execution binds the authority and starting-state content roots; and
the outcome binds execution plus produced content roots. Store nodes with
`scripts/frontier_provenance_cli.py`. Do not copy full ancestry or individual
file digests into descendants.

Before acknowledgment, execution, spend, external action, or outcome
publication, run `verify` for the named consequence and supply the applicable
live facts. Static ancestry may be reused; current authority, Budget and
reservation, expiry or action window, resource availability, known prior
external effects, and starting-state drift may not. A false or unresolved live
fact blocks only that consequence and does not reinterpret the immutable
chain. Strategic dependent spend additionally requires the unchanged decision
root to contain adopted `REPLAN_READY`. A routine R8 result that uniquely
selects the next action does not authorize added research.

The detailed packet, preflight, adoption, acknowledgment, and execution-start
schemas below define legacy semantic payloads and the restricted version 1
completion path. They are not parallel identity writers for new work.

| State | Owner | Required durable output | Maximum consequence |
|---|---|---|---|
| Packet draft | Coordinator | Complete packet without `packet_id` | Eligible for structural validation only |
| Structurally ready | Coordinator validator | Finding-free draft preflight, inserted `packet_id`, byte-identical frozen preflight | Eligible for the applicable Entry review only |
| Authorized | Entry review, user when required, then Coordinator adoption | Unchanged positive review and, when required, exact V plus finding-free frozen adoption validation | Eligible for worker acknowledgment only |
| Acknowledged | `run-frontier-batch` | Immutable accepted acknowledgment | Eligible for the exact Coordinator lifecycle transition and baseline freeze only |
| Released | Coordinator | Content-addressed execution baseline and immutable execution-start with `worker_may_start: yes` | Eligible for worker execution only |
| Reported | `run-frontier-batch` | Finding-free draft and frozen result validation plus one immutable result packet | Evidence for Coordinator validation only |
| Adopted | Coordinator | Frozen result validation reproduced byte for byte and accepted meaning written to the owning record | Only the consequence allowed by the current stage and review gates |

Advance one row at a time. A failed or missing row preserves earlier artifacts and grants no later consequence. Dispatch is complete only when the current B is durably acknowledged and waiting, released for execution, reported for adoption, or terminally blocked with truthful spend and recovery evidence.

## Boundary-preserving continuation

A B is one bounded objective, authority, evidence, and spend envelope; it is not one command or one internal try. Before publishing the immutable result, the worker may repair execution-support machinery and continue within the same B only when all of these invariants remain true:

- the authorized objective and substantive target identity are unchanged;
- acceptance, evaluation, comparison, and expected-observation semantics are unchanged;
- frozen inputs and the resolved dependency and runtime identity are unchanged; an equivalent launcher is allowed only when it resolves to that same identity;
- allowed operations, write paths, access, external effects, and the spend ceiling are unchanged;
- the continuation creates no additional sampling or selection opportunity; any stochastic, human, or side-effecting retry must already be part of the authorized protocol, account for every attempt, and establish the prior side effect; and
- every failed try, repair, and later observation is preserved at a distinct assigned evidence path and included in the final artifacts and engineering-validation record.

Execution-support machinery launches, captures, serializes, transports, inventories, or mechanically verifies evidence under the already authorized acceptance rule. It does not produce or select substantive observations or redefine their interpretation. Changing a candidate or other work product, data, prompt, evaluator, test meaning, acceptance rule, comparison control, or sampling plan is a substantive change rather than support repair.

Existing `maximum_spend`, `stop_conditions`, and `forced_halts` bound this continuation; a packet may set a stricter task-specific limit. Do not add a universal retry count. Treat a repaired support failure as intermediate engineering evidence, not an unresolved `failed_checks` item. Publish a truthful terminal result when an invariant changes, the existing bounds are exhausted, a prior external effect is unknown, or the repair cannot complete inside assigned paths. After the authoritative result exists, any continuation requires a new immutable B packet and every otherwise applicable review or authorization. Never rewrite a historical B or its evidence.

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
result_contract_version: frontier-batch-result/1
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
candidate_package_inventory_path: <assigned immutable pre-execution inventory path for code-bearing work; otherwise null>
candidate_manifest_path: <assigned stable path or null>
engineering_check_plan:
  contract_version: frontier-engineering-check-plan/1
  checks:
  - id: <unique check identifier>
    command: [<exact argument vector>]
    selection: <full-repository | exact | other>
    selected_units: [<every collected or otherwise selected test/check unit>]
    declared_effects: [<task-neutral effect classes the command can exercise>]
    effect_evidence: [{path: <source used to classify effects>, file_sha256: <lowercase digest>}]
  effect_limits: {<effect class>: <nonnegative maximum occurrence count>}
  evidence_use: engineering-only
implementation_review_gate: <required before first Slot H measurement, integration, or incumbent use; exact diagnostic-only exception under candidate-lifecycle.md; reusable review with exact unchanged identity; or null>
evaluation_target: <for experiment work, the canonical nested binding below; otherwise null>
preparation_role: <why this work is necessary on the baseline path or null>
decision_hypothesis: <mechanism or assumption this batch tests or advances>
expected_observation: <observable result and direction, including what would contradict the hypothesis>
output_contract: <one independently verifiable slice or design artifact and its observable behavior>
implementation_validation: <exact checks or WORK.md section>
implementation_definition_of_done: <exact conditions or WORK.md section>
permitted_operations: [<substantive operations or modules and the execution-support operations needed to preserve and validate their evidence>]
allowed_feedback: <exact information>
maximum_spend: <amount and unit>
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

For code-bearing work, freeze the engineering check plan before packet identity. A check declares every effect it can exercise, including local simulation or evaluator fixtures even when their results are engineering evidence only. Every declared effect requires a positive maximum; a zero or missing maximum is a structural conflict. `full-repository` means every collected unit is frozen in `selected_units`; use a non-executing discovery command when the test runner provides one. Entry review verifies the content-addressed effect evidence and rejects an opaque command whose effects are not bounded. The worker repeats this comparison before starting any check and blocks rather than learning a prohibited effect by executing it. Local engineering fixtures remain distinct from candidate performance measurement: `evidence_use: engineering-only` cannot support comparison, promotion, incumbent use, or a strength claim.

The package inventory and final manifest follow Candidate Lifecycle's single forward dependency chain. The inventory exists before runtime staging. Completed engineering evidence binds that inventory, and the final manifest then binds both. Result validation and the result bind the final manifest; the manifest never binds those downstream artifacts.

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

Diagnostic-only targets add `exception_evidence`, `consequence_limit: B evidence only`, and the complete `prohibited_consequences` list from Candidate Lifecycle. They omit `implementation_review` and `slot_h_contract`; formal targets omit those three diagnostic-only fields. Additional task-neutral bindings may remain nested under `evaluation_target`; the result reproduces the complete mapping exactly. Do not add parallel flat candidate, experiment, review, or Slot H aliases to an experiment result. `evaluation_target.experiment` is the only owner of the experiment identity: `required_inputs`, `starting_artifacts`, and other prose may refer to that field or path but must not copy any experiment identity. Packet preflight inventories the complete candidate root, rehashes the candidate manifest and experiment contract, derives the experiment identity from the exact source bytes with its one top-level `experiment_id` line omitted, and rehashes every mode-specific review or Slot H contract before Entry review. Result validation repeats those checks and selects the safety branch from the frozen target `mode`, never from a worker-reported performance state.

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
  "validator": "frontier-batch-packet-preflight/8",
  "batch_id": "<B identifier>",
  "packet_path": "<packet path>",
  "packet_payload_sha256": "<SHA-256>",
  "computed_packet_id": "<exact future packet_id>",
  "packet_structure_ready": true,
  "result_contract_probe": {
    "validator": "frontier-batch-result-preflight/6",
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

Apply [Finding effects](frontier-core.md#finding-effects). Any `block` or `repair` finding returns nonzero and forbids packet freezing and authorization-readiness review; an advisory remains in output and preserves readiness. Draft the packet and preflight in transient paths; failed bytes are diagnostic evidence, not immutable lifecycle objects. While the B objective, target specification, candidate or source, inputs, evaluator, sampling, comparison and acceptance semantics, scope, spend, effects, stop, and result consequence remain unchanged and no answer, adoption, acknowledgment, execution effect, spend, or result exists, repair and rerun the draft under the same B. After PASS, atomically publish the packet and preflight to their exclusive paths, insert only `computed_packet_id`, and rerun with `--phase frozen` to a temporary path. The frozen run must reproduce the published preflight bytes; otherwise the project realization changed or the identity is wrong. A workflow update never invalidates or migrates a project packet, review, authority, acknowledgment, result, or spend gate. A substantive project change creates a new plan and applicable review; an authoritative result requires a new immutable packet under Boundary-preserving continuation. Do not create a review snapshot, target question, reservation, acknowledgment, work, or spend from failed draft bytes.

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

Before work or spend, `run-frontier-batch` writes the assigned acknowledgment. It confirms the packet as received; it does not create authority or repair a bad packet.

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

## Batch result

```yaml
result_packet_path: <exact assigned result path>
result_packet_id: <B identifier plus SHA-256 of canonical result bytes with this field omitted>
packet_path: <exact batch packet path>
packet_id: <verified batch packet identity>
packet_preflight: {path: <JSON path>, identity_field: preflight_id, identity: <preflight_id>, file_sha256: <exact digest>}
acknowledgment: {path: <acknowledgment path>, identity_field: acknowledgment_id, identity: <acknowledgment_id>, file_sha256: <exact digest>}
execution_start: {path: <execution-start path>, identity_field: execution_start_id, identity: <execution_start_id>, file_sha256: <exact digest>}
batch_id: <B identifier>
campaign_generation: <positive integer matched to packet>
route_id: <T identifier or null>
parallel_set: <label or null>
work_kind: <declared work kind>
problem_epoch: <integer>
representation_revision: <integer>
result_contract_version: <exact packet result contract version>
decision_root: <exact packet and execution-start decision root>
started_at: <ISO-8601 datetime>
ended_at: <ISO-8601 datetime>
outcome: <completed | interrupted | failed | blocked | waiting_for_input>
changes_executable_candidate: <true | false>
planned_spend: <amount and unit>
actual_spend: <amount and unit or unknown>
accounting_evidence: <stable path, or exact reason evidence is unavailable when actual_spend is unknown>
evidence_reuse_accounting: <for evidence-reuse publication only, {new_measurement_executions: 0, reruns: 0, new_measurement_spend: 0}; omit otherwise>
artifacts: [<stable paths and identities>]
work_plan: <W path, revision, and design contract identity; exact direct packet_id; or null>
design_review: <adopted DESIGN_READY identity, not required under direct profile, or null>
development_authorization: <V identifier and binding for code-bearing work, including reviewed design identity and exact scope plus packet preflight for module or system when the target names B, or exact direct packet_id, preflight_id, and source_base_identity when direct; or null>
design_inputs_used: [<exact pointers and identities, or none>]
source_base_identity: <commit and dirty-state identity, immutable source snapshot, or null>
source_result_identity: <head commit and diff identity, content manifest, or immutable packaged source identity; null when no code changed>
changed_paths: [<path or none>]
candidate_manifest: <for non-experiment work, stable path and identity or null; omit for experiment work>
candidate_identity: <for non-experiment work, immutable identifier or null; omit for experiment work>
experiment_identity: <for non-experiment work, null or a legacy audit value; omit for experiment work>
resolved_configuration_identity: <stable path and identity, or null>
dependency_identity: <lockfile, image, environment, or explicit none with reason; null when not applicable>
implementation_review_state: <for non-experiment work, pending | not-required with rule | not-applicable; omit for experiment work>
evaluation_target: <for experiment work, an exact complete copy of the packet evaluation_target; omit otherwise>
materialization_state: <not-applicable | not-started | partial | materialized-stopped>
performance_evaluation_state: <not-authorized | not-performed | diagnostic-only under cited Entry authority | performed under cited IMPLEMENTATION_READY and Slot H measurement authority>
integration_state: <not-authorized | not-performed | performed under cited IMPLEMENTATION_READY and integration authority>
work_plan_progress: <W updates and next recovery point or null>
design_change_proposals: [<discovery, affected contract, evidence, and consequence; or none>]
recovery_point: <stable packet preflight, packet, acknowledgment, execution-start, artifacts, and identities sufficient to resume or audit, plus the exact next permitted action>
human_input_state: <not-applicable | requested | waiting-for-input | received-unvalidated | accepted-as-evidence | rejected>
human_input_artifacts: [<response path, stable identity, and provenance metadata; or none>]
human_input_validation: [<schema, provenance, and quality check with evidence; or none>]
human_input_evidence_limit: <why accepted data remains evidence rather than a technical conclusion, E, or user value choice; or not applicable>
engineering_validation: [<check, result, and evidence>]
implementation_definition_of_done: <met | not_met | not_applicable, with evidence>
results: [<diagnostic evidence with its consequence limit, or measurement, uncertainty, legality, and comparison-validity evidence from an authorized Slot H evaluation B; always [] for code-bearing materialization>]
observed_vs_expected: <observed evidence against the packet's expected observation; no campaign decision>
decision_relevant_surprises: [<unexpected result, failed assumption, or none>]
failed_checks: [<check and evidence>]
new_prerequisites: [<exact prerequisite>]
possible_follow_up: <nonnormative suggestion or null>
scope_deviation: <None or exact deviation>
```

Candidate identity, manifest, source result, engineering evidence, and materialization state belong only in their dedicated fields. Never place them in `results` to make a materialization result nonempty.

Before the immutable result path exists, the worker serializes a temporary draft without `result_packet_id` and runs:

```bash
python .agents/skills/frontier-optimization/scripts/validate_batch_result.py \
  <temporary-result-draft> --packet <packet_path> --phase draft \
  --output <result_validation_path>
```

Only a finding-free draft may receive the validator's `computed_result_packet_id`. Validate that completed temporary form with `--phase frozen` to another temporary path and require byte-identical output to the assigned `result_validation_path`. Only then atomically place the validated bytes at `result_packet_path`. Never use the authoritative result path as the draft or overwrite it after validation. The Coordinator reruns frozen validation and requires byte-identical output before accepting a terminal result, writing the terminal-outcome meaning, or freezing an implementation-review snapshot. An invalid draft is preserved only at a non-authoritative diagnostic path and cannot become an accepted terminal result.

Compute `result_packet_id` after every other result field resolves. A current result is publishable only after the result validator re-reads the three structured dispatch bindings, verifies the exact execution-start identity and live baseline, and recomputes the authority chain contained in execution-start. After the authoritative result exists, a resumed attempt uses a new immutable packet and exclusive acknowledgment, execution-baseline, execution-start, result-validation, and result paths. Before that publication, use [Boundary-preserving continuation](#boundary-preserving-continuation) when its invariants hold. `completed`, `interrupted`, `failed`, `blocked`, and `waiting_for_input` are all reportable outcomes. The first four end the current execution attempt; `waiting_for_input` preserves a paused recovery point. `actual_spend: unknown` is also valid evidence; it forces a new-spend halt until the Coordinator can establish the remaining budget. A result packet is worker evidence only. It never edits a concern contract, creates or updates E, turns human data into a technical conclusion or value choice, adopts a candidate, promotes an incumbent, or changes campaign meaning by itself.

Draft or frozen publication requires the project packet's supported `result_contract_version` copied exactly from that packet. A released B continues only through its exact project decision root, packet, preflight, acknowledgment, execution-start, baseline, result format, and result identities. A workflow update does not change any of them; a packet whose own project result format is unsupported remains audit-only.

A Slot H evaluation packet uses `work_kind: experiment`, `changes_executable_candidate: false`, and the canonical nested `evaluation_target` with `mode: formal-slot-h`. Its experiment identity must bind the immutable candidate, evaluator, data, controls, protocol, environment, budget, campaign generation, and exclusive result paths before acknowledgment. A recovery-generation evaluation must also cite the recovery V, X, inherited Budget, and fresh `IMPLEMENTATION_READY`. It may not change candidate bytes, evaluator semantics, comparison controls, or measurement inputs. The result reproduces the complete packet `evaluation_target` exactly; only the Coordinator may validate it and append E.

When a completed measurement cannot be published solely because an old packet and result validator used incompatible field shapes, preserve that B and its raw evidence unchanged. Only a formal Slot H target may use `evaluation_target.evidence_reuse`; the diagnostic-only exception cannot recover completed evidence. A new recovery B may publish from the existing evidence without rerunning the measurement only when its reuse mapping binds `source_batch_id`, a nonempty list of raw artifact `{path, file_sha256}` mappings, `measurement_semantics: unchanged`, `reruns: 0`, and `measurement_execution: prohibited`. Packet preflight reads each raw artifact and recomputes its SHA-256 before Entry review; result validation repeats the same byte check immediately before publication. The recovery result reproduces those bindings, uses `actual_spend: 0 new measurement spend`, reports the exact zero-valued `evidence_reuse_accounting` mapping above, includes at least one measurement result whenever it reports formal evaluation as performed, and reports integration as `not-performed` or `not-authorized`. It never presents itself as the historical B's result. Packet and result validation reject any other value. Any missing or changed raw byte, identity mismatch, empty performed result, changed interpretation, integration, or new sampling requires a normal new evaluation packet instead.

A diagnostic-only experiment also uses `work_kind: experiment` and `changes_executable_candidate: false`, but follows the complete exception in `candidate-lifecycle.md`. Its canonical nested `evaluation_target` uses `mode: diagnostic-only`; binds the immutable newly materialized candidate, manifest, experiment identity, diagnostic evaluator and inputs, local isolation, hard-constraint evidence, maximum spend, legal result branches, and sealed-evidence exclusion as `exception_evidence`; sets `consequence_limit: B evidence only`; and lists E, integration, incumbent use, promotion, submission, and strength claim under `prohibited_consequences`. Its result reproduces that target exactly, reports `performance_evaluation_state: diagnostic-only under cited Entry authority`, and includes `maximum_consequence: B evidence only` on every result item. It contains no claim or stronger-consequence field at any nesting depth. Only the Coordinator may adopt it as B evidence and write its Outcome Reflection.
