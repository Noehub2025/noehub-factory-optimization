# Frontier Batch Interface

Load for one selected B before invoking `run-frontier-batch`, validating its result, or resuming it. Load `candidate-lifecycle.md` additionally only when `changes_executable_candidate: true` or implementation-review reuse is in question.

## Contents

- [Batch packet](#batch-packet)
- [Packet preflight](#packet-preflight)
- [Batch acknowledgment](#batch-acknowledgment)
- [Batch execution start](#batch-execution-start)
- [Batch result](#batch-result)

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
workflow_contracts: <immutable Campaign Cycle, Batch Interface, Worker Interfaces, validate_batch_packet.py, validate_entry_packet.py, validate_authorization_adoption.py, freeze_execution_baseline.py, and validate_batch_result.py identities used to plan, preflight, review, authorize, acknowledge, start, execute, and validate this B>
work_plan: <W path or null>
work_plan_revision: <integer or null>
design_contract_identity: <immutable reviewed design identity, exact direct packet_id, or null>
design_profile: <direct | module | system | not-applicable>
required_design_inputs: [<exact W or indexed design concern path, section, and identity; or none>]
design_traceability: <for module or system, exact machine-readable traceability path and whole-file SHA-256; otherwise null>
design_review: <adopted DESIGN_READY path and identity, pending for design work, or null under direct or non-code-bearing work>
development_authorization_target: <exact pending authorization target identity for code-bearing work; null for non-code-bearing work; never mutate this frozen packet to record the later answer>
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
workspace_identity: <branch and worktree, shared sequential workspace with reason, or null>
candidate_interface: <existing or user-approved seam and callers, or null>
allowed_code_paths: [<exclusive paths or none>]
worker_forbidden_paths: [<paths or exact sections the worker must not write, or none>]
execution_frozen_inputs: [<mapping with repository-relative path, file or subtree scope, exact section when narrower than a file, and pre-start identity that no actor may change during execution; or none>]
coordinator_lifecycle_transition: <null when campaign is already running; otherwise exact path, allowed field-diff set, accepted-acknowledgment prerequisite, and pre-start deadline>
execution_baseline_root: <exclusive Coordinator-owned subtree in which freeze_execution_baseline.py creates one content-addressed snapshot directory>
execution_start_path: <stable Coordinator-owned path assigned only to this batch>
candidate_manifest_path: <assigned stable path or null>
implementation_review_gate: <required before first measurement, integration, or incumbent use; reusable review with exact unchanged identity; or null>
evaluation_target: <immutable candidate identity, manifest, adopted IMPLEMENTATION_READY, planned experiment identity, and Slot H contract for a separate evaluation B; or null>
preparation_role: <why this work is necessary on the baseline path or null>
decision_hypothesis: <mechanism or assumption this batch tests or advances>
expected_observation: <observable result and direction, including what would contradict the hypothesis>
output_contract: <one independently verifiable slice or design artifact and its observable behavior>
implementation_validation: <exact checks or WORK.md section>
implementation_definition_of_done: <exact conditions or WORK.md section>
permitted_operations: [<operations or modules>]
allowed_feedback: <exact information>
maximum_spend: <amount and unit>
accounting_source: <path or system>
authorization_gate: <finding-free authorization-readiness review followed by exact user V and Coordinator Entry adoption; direct spend-readiness when no user authorization applies; adopted REPLAN_READY for a strategic later change; adopted implementation review before first measurement, integration, or incumbent use; or exact later campaign-cycle Selection authority>
baseline_establishment_checkpoint: <usable artifact and completion check or null>
first_performance_check: <comparison or decision result, and whether this batch or a later batch runs it>
preparation_budget_limit: <maximum allocation before that check>
required_follow_up_reserve: <amount and mandatory confirmation or recovery purpose, or null with governing rule>
decision_after_checkpoint: <observable route or allocation decision>
measurement: <Slot H identity and checks, or exact later evaluation path>
comparison_validity_checks: <measurement identity, comparable conditions, data quality, drift, confounding, and execution checks required when measuring a result>
candidate_identity_rule: <Slot B identity>
constraints: <required legality checks>
artifact_paths: [<paths assigned only to this batch>]
acknowledgment_path: <stable path assigned only to this batch>
result_validation_path: <stable worker-owned deterministic validation artifact written before the final result path>
result_packet_path: <stable path assigned only to this batch>
resume_when: <available input, event, or immediate>
stop_conditions: [<conditions>]
forced_halts: [<conditions>]
prohibited_actions: [<actions and claims>]
```

Do not compute `packet_id` yet. First complete the deterministic structural preflight below. Only a finding-free draft may be serialized canonically without `packet_id`, hashed, given the preflight's exact `computed_packet_id`, and frozen at `packet_path`. Rerun frozen preflight and require byte-identical PASS output before freezing an authorization-readiness snapshot. Never overwrite the packet after that point. `workflow_contracts` binds the exact dispatch, validator, and permission rules; a later spec change cannot silently reinterpret an existing packet. This preflight establishes packet structure, not user authorization. A later user V must cite the immutable packet, preflight, finding-free authorization-readiness review, design or direct identity, source base, scope, spend, and stop boundary.

Path fields have three different meanings and are not interchangeable:

- `allowed_code_paths`, `artifact_paths`, acknowledgment, result validation, result, and assigned W sections are the worker's exclusive write surface.
- `worker_forbidden_paths` restrict only the worker. They may contain Coordinator-owned campaign records, but they must not overlap any worker write surface.
- `execution_frozen_inputs` are globally immutable only from the accepted execution-start record through the terminal result. Record an exact file or section identity; do not freeze a whole directory that contains a worker write surface, the execution-start record, or a required Coordinator lifecycle write.
- `execution_baseline_root` is a Coordinator-owned output subtree. It may overlap neither worker writes nor any frozen input or other Coordinator output.

For `module` or `system`, never freeze the whole mutable `WORK.md`. Bind the immutable design through `design_contract_identity`, the indexed contract sections and concerns, and `design_traceability`. Current authorization lives only in V, Selection, ledger, and the Coordinator-owned Entry-adoption artifact. It is not a W field and cannot change the design identity.

For the first B of a planned campaign, `coordinator_lifecycle_transition` must name one exact `FRONTIER.md` patch after this packet's acknowledgment is accepted and before the execution-start record is written. The allowed field-diff set contains `campaign_status: planned -> running`, `generated.at` advancing to the transition time, and `updated` changing only when required to equal that transition date; every other byte and field remains unchanged. It grants no other edit. When the campaign is already running, record `null`. A packet that omits a required transition, permits a broader edit, overlaps the transition with an execution-frozen input, or cannot distinguish worker prohibition from global immutability is path-conflicting and must be rejected before acknowledgment.

## Packet preflight

Use [validate_batch_packet.py](../scripts/validate_batch_packet.py) before packet identity or authorization-readiness review:

```bash
python .agents/skills/frontier-optimization/scripts/validate_batch_packet.py \
  <draft-packet-path> --phase draft --output <packet_preflight_path>
```

The draft already contains every field except `packet_id`, including `packet_preflight_path`, worker outputs, Coordinator outputs, forbidden paths, frozen paths, lifecycle outputs, prohibitions, and the machine-readable W traceability binding when applicable. The validator canonicalizes repository-relative paths, checks exact and ancestor/descendant overlap, verifies every W evidence destination is covered by the worker write surface, rejects whole-W freezing, reproduces the omit-field packet payload hash, and writes one deterministic JSON artifact:

```json
{
  "validator": "frontier-batch-packet-preflight/1",
  "batch_id": "<B identifier>",
  "packet_path": "<packet path>",
  "packet_payload_sha256": "<SHA-256>",
  "computed_packet_id": "<exact future packet_id>",
  "packet_structure_ready": true,
  "checks": {
    "worker_write_vs_forbidden": "PASS",
    "coordinator_outputs_vs_worker": "PASS",
    "coordinator_path_exclusivity": "PASS",
    "worker_output_role_exclusivity": "PASS",
    "frozen_paths_vs_outputs": "PASS",
    "required_outputs_vs_prohibitions": "PASS",
    "packet_identity": "PASS",
    "path_schema": "PASS",
    "work_plan_traceability": "PASS"
  },
  "normalized_ownership": {
    "worker_write_paths": ["<path>"],
    "worker_forbidden_paths": ["<path>"],
    "coordinator_paths": ["<path>"],
    "execution_frozen_paths": ["<path>"]
  },
  "findings": [],
  "preflight_id": "<content-addressed identity>"
}
```

Any finding returns nonzero and forbids packet freezing and authorization-readiness review. After PASS, insert only `computed_packet_id`, freeze the packet, and rerun with `--phase frozen` to a temporary path. The frozen run must reproduce the exact preflight bytes already stored at `packet_preflight_path`; otherwise the draft changed or the identity is wrong. Preserve failed output at a non-authoritative diagnostic path when useful, but do not create an authorization target, user V, reservation, acknowledgment, work, or spend from it.

`--phase audit` exists only to diagnose immutable legacy packets that predate these fields. It may explain an old failure, but it never creates a current structural preflight, repairs the old packet, or permits review, authorization, acknowledgment, work, or spend. Any current packet must pass both draft and frozen phases.

The required invariants include:

- worker write paths do not equal, contain, or fall under worker-forbidden paths;
- `execution_start_path`, `execution_baseline_root`, `packet_path`, and `packet_preflight_path` do not overlap worker writes;
- packet, preflight, execution-baseline root, execution-start, and lifecycle outputs are mutually exclusive Coordinator paths;
- acknowledgment, result validation, result, and candidate-manifest roles use mutually exclusive worker paths;
- acknowledgment belongs to the worker and execution-start belongs to the Coordinator;
- no execution-frozen subtree contains worker output, packet preflight, execution-start, or a Coordinator lifecycle output;
- a module or system packet does not freeze its whole W, freezes the exact traceability file, exactly matches its Delivery and required-design-input mapping, and covers every evidence destination in that file;
- `prohibited_actions` does not deny acknowledgment, result, or candidate-manifest writes that the packet requires; and
- the frozen `packet_id` exactly matches the validated draft payload.

Authorization-readiness review supplies the full semantic gate after this structural check. Acknowledgment repeats frozen preflight as defense in depth.

## Batch acknowledgment

Before work or spend, `run-frontier-batch` writes the assigned acknowledgment. It confirms the packet as received; it does not create authority or repair a bad packet.

```yaml
packet_path: <exact batch packet path>
packet_id: <verified batch packet identity>
packet_preflight: <exact pre-authorization path and preflight_id reproduced by the bound validator>
acknowledgment_path: <assigned exclusive path>
acknowledgment_id: <B identifier plus SHA-256 of canonical acknowledgment bytes with this field omitted>
batch_id: <B identifier>
campaign_generation: <positive integer matched to packet>
acknowledged_by: <worker identity>
acknowledged_at: <ISO-8601 datetime>
parent_bindings: <matched | mismatch with exact conflict>
scope_and_work: <matched | mismatch with exact conflict>
work_plan_and_design_inputs: <none and not required | matched | mismatch with exact conflict>
authorization_gates: <matched | missing or stale authority>
learning_and_join_gates: <first spend and not applicable | complete reflection, V, join, Selection, and review identities matched | exact missing or stale gate>
human_input_terms: <not applicable | request, schema, provenance, quality, confidentiality, acceptance, and resume terms matched | exact conflict>
decision_terms: <hypothesis, expected observation, checkpoint decision, and stop terms matched | exact conflict>
spend_terms: <maximum, accounting source, preparation limit, and reserve matched | exact conflict>
paths_and_recovery: <fresh PASS packet preflight; exclusive artifact, acknowledgment, execution-baseline, execution-start, result-validation, result, source, and recovery paths; and separated worker-forbidden and execution-frozen inputs matched | exact conflict>
output_and_checks: <output contract, validation, and definition of done matched | exact conflict>
prohibitions: <acknowledged | exact conflict>
acknowledgment: <accepted | blocked>
blocker: <null or exact reason>
```

Compute `acknowledgment_id` after every other field resolves and never overwrite an acknowledged path. The worker returns `BLOCKED` without work or spend when any acknowledgment row conflicts. Preserve that acknowledgment and cite it from the result packet.

An accepted acknowledgment ends the acknowledgment phase. It does not let the worker start work or spend. The worker returns control to the Coordinator and waits for the immutable execution-start record.

## Batch execution start

After an accepted acknowledgment, the Coordinator performs the packet's exact lifecycle transition when required and verifies that no other action-controlling input changed. Before writing execution-start, it must copy every post-transition baseline byte into the packet's exclusive `execution_baseline_root`. A hash without those bytes is not a frozen baseline.

Use the bound baseline tool to create the content-addressed snapshot and final execution-start record in one fail-closed operation:

```bash
python .agents/skills/frontier-optimization/scripts/freeze_execution_baseline.py freeze \
  <execution-start-draft-path> \
  --snapshot-root <execution_baseline_root> \
  --output <execution_start_path>
```

The draft has every field below except `execution_start_id` and `baseline_snapshot`. Every `post_transition_baseline` row uses `scope: file | subtree` and a lowercase `sha256:<digest>`. File identity is SHA-256 over exact bytes. Subtree identity is SHA-256 over canonical JSON containing the sorted relative member paths and member SHA-256 values. The tool rejects missing, changed, duplicate, symbolic-link, unsafe, or non-regular input; refuses any existing snapshot root or execution-start path; copies exact bytes; writes `manifest.yaml`; computes `snapshot_id`; binds it into execution-start; computes `execution_start_id`; and writes the final execution-start path exactly once.

The final record is:

```yaml
execution_start_path: <exact assigned Coordinator-owned path>
execution_start_id: <B identifier plus SHA-256 of canonical execution-start bytes with this field omitted>
packet_path: <exact batch packet path>
packet_id: <verified batch packet identity>
packet_preflight: <exact pre-authorization path and preflight_id reproduced before acknowledgment>
acknowledgment_path: <accepted acknowledgment path>
acknowledgment_id: <accepted acknowledgment identity>
batch_id: <B identifier>
campaign_generation: <positive integer matched to packet and FRONTIER.md>
recorded_by: frontier-optimization/1
recorded_at: <ISO-8601 datetime>
lifecycle_transition: <not required because campaign was already running, or exact path, field, old value, new value, pre-change identity, and post-change identity>
post_transition_baseline: [<every execution-frozen and other action-controlling file or subtree, its scope, and exact live identity>]
baseline_snapshot:
  root: <execution_baseline_root>/<snapshot digest>
  manifest: <root>/manifest.yaml
  snapshot_id: <B identifier plus SHA-256 of canonical manifest bytes with snapshot_id omitted>
  input_count: <exact number of post_transition_baseline rows>
unchanged_authority_check: <matched workflow contracts, packet preflight, packet, parents, Selection, Budget, reviews, V, W, and other action-controlling inputs; or exact conflict>
worker_may_start: <yes | no>
blocker: <null or exact reason>
```

The snapshot manifest has one row per baseline entry and records source path, scope, declared and recomputed identity, snapshot path, and sorted members for a subtree. The tool computes `execution_start_id` after every other field resolves and never overwrites either output. The record creates no new scope or budget; it proves that the acknowledged packet can begin under a coherent and recoverable post-transition baseline. `worker_may_start: no`, a missing or stale record, missing snapshot byte, unexpected acknowledgment-to-start change, incorrect lifecycle diff, or baseline mismatch returns `BLOCKED` without work or spend.

On the execution-phase invocation, `run-frontier-batch` runs `freeze_execution_baseline.py verify <execution_start_path> --live`, verifies the execution-start and snapshot identities, and matches every live post-transition baseline byte before work. It repeats live verification before writing the terminal result. Only then does it set `started_at` and begin spend. Drift in an execution-frozen input after this point forces a halt. A change only to a worker-forbidden path is not itself drift; it is a worker violation only when the worker made it, unless that path is also listed separately as an execution-frozen input. Later implementation review verifies the immutable snapshot without `--live`, so normal post-terminal campaign-record updates cannot erase start-time evidence.

## Batch result

```yaml
result_packet_path: <exact assigned result path>
result_packet_id: <B identifier plus SHA-256 of canonical result bytes with this field omitted>
packet_path: <exact batch packet path>
packet_id: <verified batch packet identity>
packet_preflight: <exact pre-authorization path and preflight_id reproduced before both dispatch phases>
acknowledgment: <stable acknowledgment path and identity>
execution_start: <stable execution-start path and identity>
batch_id: <B identifier>
campaign_generation: <positive integer matched to packet>
route_id: <T identifier or null>
parallel_set: <label or null>
work_kind: <declared work kind>
problem_epoch: <integer>
representation_revision: <integer>
started_at: <ISO-8601 datetime>
ended_at: <ISO-8601 datetime>
outcome: <completed | interrupted | failed | blocked | waiting_for_input>
changes_executable_candidate: <true | false>
planned_spend: <amount and unit>
actual_spend: <amount and unit or unknown>
accounting_evidence: <stable path, or exact reason evidence is unavailable when actual_spend is unknown>
artifacts: [<stable paths and identities>]
work_plan: <W path, revision, and design contract identity; exact direct packet_id; or null>
design_review: <adopted DESIGN_READY identity, not required under direct profile, or null>
development_authorization: <V identifier and binding for code-bearing work, including reviewed design identity and exact scope plus packet preflight for module or system when the target names B, or exact direct packet_id, preflight_id, and source_base_identity when direct; or null>
design_inputs_used: [<exact pointers and identities, or none>]
source_base_identity: <commit and dirty-state identity, immutable source snapshot, or null>
source_result_identity: <head commit and diff identity, content manifest, or immutable packaged source identity; null when no code changed>
changed_paths: [<path or none>]
candidate_manifest: <stable path and identity or null>
candidate_identity: <immutable identifier or null>
experiment_identity: <candidate, evaluator, data, controls, protocol, environment, budget, and result-artifact binding; or null>
resolved_configuration_identity: <stable path and identity, or null>
dependency_identity: <lockfile, image, environment, or explicit none with reason; null when not applicable>
implementation_review_state: <pending | reusable with review identity | not-required with rule | not-applicable>
materialization_state: <not-applicable | not-started | partial | materialized-stopped>
performance_evaluation_state: <not-authorized | not-performed | performed under cited IMPLEMENTATION_READY and measurement authority>
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
results: [<measurement, uncertainty, legality, comparison-validity evidence, and evidence when performed by an authorized evaluation B; always [] for code-bearing materialization>]
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

Compute `result_packet_id` after every other result field resolves. A resumed attempt uses a new immutable packet and exclusive acknowledgment, execution-baseline, execution-start, result-validation, and result paths. `completed`, `interrupted`, `failed`, `blocked`, and `waiting_for_input` are all reportable outcomes. The first four end the current execution attempt; `waiting_for_input` preserves a paused recovery point. `actual_spend: unknown` is also valid evidence; it forces a new-spend halt until the Coordinator can establish the remaining budget. A result packet is worker evidence only. It never edits a concern contract, creates or updates E, turns human data into a technical conclusion or value choice, adopts a candidate, promotes an incumbent, or changes campaign meaning by itself.

A Slot H evaluation packet uses `work_kind: experiment`, `changes_executable_candidate: false`, and a complete `evaluation_target`. Its experiment identity must bind the immutable candidate, evaluator, data, controls, protocol, environment, budget, campaign generation, and exclusive result paths before acknowledgment. A recovery-generation evaluation must also cite the recovery V, X, inherited Budget, and fresh `IMPLEMENTATION_READY`. It may not change candidate bytes, evaluator semantics, comparison controls, or measurement inputs. The result reports the same experiment identity and raw measurement evidence; only the Coordinator may validate it and append E.
