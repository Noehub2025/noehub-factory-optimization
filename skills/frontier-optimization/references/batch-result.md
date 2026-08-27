# Batch result format

Read when preparing, validating, or adopting a result. Apply only fields belonging to the packet's work kind and reached phase; a research or human-input result does not need candidate or engineering evidence.

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
evaluation_target: <exact copy of the authorized packet target, including working_scope diagnostics; omit when the packet has none>
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
engineering_validation: [<check, result, and evidence; for reviewed prepublication work, exactly one binding to frontier-engineering-evidence/1>]
implementation_definition_of_done: <met | not_met | not_applicable, with evidence>
results: [<authorized diagnostic observations with their consequence limit, or formal Slot H evidence; [] for materialization without an explicit working diagnostic target>]
observed_vs_expected: <observed evidence against the packet's expected observation; no campaign decision>
decision_relevant_surprises: [<unexpected result, failed assumption, or none>]
failed_checks: [<check and evidence>]
new_prerequisites: [<exact prerequisite>]
possible_follow_up: <nonnormative suggestion or null>
scope_deviation: <None or exact deviation>
```

Candidate identity, manifest, source result, engineering evidence, and materialization state belong only in their dedicated fields. Never place them in `results` to make a materialization result nonempty.

For reviewed prepublication work, `frontier-engineering-evidence/1` records only formal closing attempts: an ordered `attempts` list, the packet's `effect_limits`, derived `effects`, final `status`, `evidence_use: engineering-only`, `official_output`, and `review_repair_history` when an earlier passing realization was replaced after a nonpositive implementation review. Each attempt has consecutive `sequence`, a unique content-addressed `snapshot_id` whose digest equals its snapshot-manifest or inventory file SHA-256, the frozen checks actually run with exact IDs and results, one content-addressed combined `frontier-engineering-check-report/1`, `pass` or `fail`, and per-effect counts. Inventory preparation and working feedback do not appear in this list. The combined report binds the snapshot, ordered check IDs, frozen command digests, exit status, and log digests. The validator derives each attempt's effects from the frozen per-invocation `effect_costs`; the worker cannot lower them after execution. An attempt is `pass` if and only if every frozen check ran in order and passed. The final attempt must pass. Every earlier passing attempt must have exactly one history entry that names its sequence and the verified nonpositive implementation-review handoff that caused its replacement. The official output must be byte-identical to the final reviewed passing snapshot. Result accounting follows [Charging and publication](batch-interface.md#charging-and-publication). A terminal failure without publication preserves attempts, cumulative effects, and any earlier charged formal proposal in the existing accounting evidence; it has no published output or final candidate manifest. The result validator checks recorded engineering coverage, cumulative effects, accounting fields, and output equality; the Coordinator reconciles project-owned charges for every outcome.

Before the immutable result path exists, the worker serializes a temporary draft without `result_packet_id` and runs:

```bash
python .agents/skills/frontier-optimization/scripts/validate_batch_result.py \
  <temporary-result-draft> --packet <packet_path> --phase draft \
  --output <result_validation_path>
```

Only a finding-free draft may receive the validator's `computed_result_packet_id`. Validate that completed temporary form with `--phase frozen` to another temporary path and require byte-identical output to the assigned `result_validation_path`. Only then atomically place the validated bytes at `result_packet_path`. Never use the authoritative result path as the draft or overwrite it after validation. The Coordinator reruns frozen validation and requires byte-identical output before accepting a terminal result or writing terminal-outcome meaning. A prepublication implementation-review snapshot is frozen earlier from the passing working inventory and engineering evidence defined by Implementation Review; it does not wait for this terminal result. An invalid result draft is preserved only at a non-authoritative diagnostic path and cannot become an accepted terminal result.

Compute `result_packet_id` after every other result field resolves. A current result is publishable only after the result validator re-reads the three structured dispatch bindings, verifies the exact execution-start identity and live baseline, and recomputes the authority chain contained in execution-start. After the authoritative result exists, a resumed attempt uses a new immutable packet and exclusive acknowledgment, execution-baseline, execution-start, result-validation, and result paths. Before that publication, use [Boundary-preserving continuation](batch-interface.md#boundary-preserving-continuation) when its invariants hold. `completed`, `interrupted`, `failed`, `blocked`, and `waiting_for_input` are all reportable outcomes. The first four end the current execution attempt; `waiting_for_input` preserves a paused recovery point. `actual_spend: unknown` is also valid evidence; it forces a new-spend halt until the Coordinator can establish the remaining budget. A result packet is worker evidence only. It never edits a concern contract, creates or updates E, turns human data into a technical conclusion or value choice, adopts a candidate, promotes an incumbent, or changes campaign meaning by itself.

An already-frozen version 4 project dispatch may complete result publication through one fail-closed union when its acknowledgment uses `frontier-project-batch-acknowledgment/1` and its execution-start uses `frontier-project-execution-start/1`. The validator recognizes the arm from the complete binding shape, never from `contract_version` alone:

- The legacy arm requires all three plan fields `packet_path`, `packet_id`, and `packet_preflight_path`; acknowledgment `batch_plan` has exactly `path`, `packet_id`, and `file_sha256`; acknowledgment and result each bind the exact packet preflight; and the result retains `packet_path`, `packet_id`, `packet_preflight`, and `workflow_source_identity` under its historical schema. It forbids `batch_plan_id`.
- The current arm requires `batch_plan_id` and forbids every legacy packet and preflight field. Acknowledgment `batch_plan` has exactly `path`, `plan_id`, and `file_sha256` and contains no `packet_preflight`. The result has one exact `{path, identity_field: batch_plan_id, identity, file_sha256}` `batch_plan` binding and the typed `decision_root`; it forbids `packet_path`, `packet_id`, `packet_preflight`, and `workflow_source_identity`.

Mixed, partial, or extra binding families fail before result publication. Both arms recompute acknowledgment and execution-start exact-byte self-identities, the bound plan identity, execution-verification bytes and finding-free result, the complete decision-to-execution typed graph, all four role-specific portable content roots, and the exact plan and acknowledgment bytes preserved in the execution baseline. The legacy arm additionally recomputes and preserves the packet preflight. The current arm requires the typed `project/state/execution-state.yaml` to reproduce the plan's complete `execution_frozen_inputs` list and requires the state bundle to contain exactly those raw bytes under `project/state/frozen-inputs/<repository-relative-path>`. Immediately before every draft and frozen result publication, it rehashes every live file or closed subtree and compares it with both the plan identity and those typed baseline bytes. Missing, extra, changed, symbolic-link, unsafe, or unsupported input fails closed.

Other acknowledgment fields remain frozen by the acknowledgment self-identity and baseline copy but grant no separately inferred authority. The adapter never rewrites a project record, creates authority, changes spend, or imports workflow identity into project state.

Draft or frozen publication requires the project packet's supported `result_contract_version` copied exactly from that packet. A released B continues only through its exact project decision root, packet, preflight, acknowledgment, execution-start, baseline, result format, and result identities. A workflow update does not change any of them; a packet whose own project result format is unsupported remains audit-only.

A Slot H evaluation packet uses `work_kind: experiment`, `changes_executable_candidate: false`, and the canonical nested `evaluation_target` with `mode: formal-slot-h`. Its experiment identity must bind the immutable candidate, evaluator, data, controls, protocol, environment, budget, campaign generation, and exclusive result paths before acknowledgment. A recovery-generation evaluation cites applicable permission, inherited Budget and the implementation conclusion allowed by [Candidate recovery](candidate-lifecycle.md#post-closeout-recovery-reuse); a new generation alone does not require fresh `IMPLEMENTATION_READY`. It may not change candidate bytes, evaluator semantics, comparison controls, or measurement inputs. The result reproduces the complete packet `evaluation_target` exactly; only the Coordinator may validate it and append E.

When a completed measurement cannot be published solely because an old packet and result validator used incompatible field shapes, preserve that B and its raw evidence unchanged. Only a formal Slot H target may use `evaluation_target.evidence_reuse`; the diagnostic-only exception cannot recover completed evidence. A new recovery B may publish from the existing evidence without rerunning the measurement only when its reuse mapping binds `source_batch_id`, a nonempty list of raw artifact `{path, file_sha256}` mappings, `measurement_semantics: unchanged`, `reruns: 0`, and `measurement_execution: prohibited`. Packet preflight reads each raw artifact and recomputes its SHA-256 before Entry review; result validation repeats the same byte check immediately before publication. The recovery result reproduces those bindings, uses `actual_spend: 0 new measurement spend`, reports the exact zero-valued `evidence_reuse_accounting` mapping above, includes at least one measurement result whenever it reports formal evaluation as performed, and reports integration as `not-performed` or `not-authorized`. It never presents itself as the historical B's result. Packet and result validation reject any other value. Any missing or changed raw byte, identity mismatch, empty performed result, changed interpretation, integration, or new sampling requires a normal new evaluation packet instead.

A diagnostic-only target either follows [Bounded observations before publication](batch-interface.md#bounded-observations-before-publication) or the published-candidate exception in `candidate-lifecycle.md`. Only the latter requires a separate experiment B with `changes_executable_candidate: false` and `exception_evidence`. Both preserve the exact target, `B evidence only` limit, and prohibited consequences; neither permits claim or stronger-consequence fields. Only the Coordinator adopts the evidence and writes its Outcome Reflection.
