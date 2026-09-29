# Optional consequential-decision bridge

This extends the existing host bridge, not the campaign lifecycle. It is disabled unless configured on one participating research run. Deploy with `observe` first. Mechanical tests and a retained-text calibration do not justify universal enforcement or claim improved research efficiency. Use `enforce` only for a supported boundary class in a deliberately participating path.

## Owner integration

The first supported path is the Frontier Coordinator's proposed new or materially revised investment, current Selection writeback and following professional dispatch. The [owner instructions](../../skills/frontier-optimization/references/worker-interfaces.md#optional-decision-bridge) consume this path. The owner supplies the existing `WorkUpdate.options` entry selected by `selected`, including its question, mechanism, useful result, necessary work and prerequisites. Rationale and switching conditions belong to that commitment. Update these when the assignment changes their substance. Ordinary internal-step wording and remaining progress do not require another check.

The first participating commitment enters the check automatically. Later checks use the existing investment trigger, reported as `update.investment_changed: true`. Ordinary progress, restated rationale and policy-file edits alone do not start another judgment. The owner must report a substantive change even if it retains the same label or prose. Saved commitment text is audit content, not a semantic change detector; this remains a cooperative owner contract. Direct Agent calls, arbitrary Selection writers and nonparticipating runs are not intercepted. Do not claim complete campaign enforcement.

Configured sessions supply the policy to the existing Coordinator and Resolver requests. Reuse that one applicable independent judgment through `update.resolved_invocation` (an accepted Resolver invocation in this run), or `resolved_by` (existing supplied source indices). The owner asserts substantive applicability; the runtime verifies references and records reuse without launching another model or fabricating a `no_finding` verdict. Enforce mode retains the existing current writeback check. Missing policy stays unavailable even when a judgment reference exists. New fields default to ordinary continuation/no reused invocation when reading older records.

For the repository's normal reference-based Workflow, `frontier_references.py resolver` and `bind-resolution` deliver this same policy within the existing assignment/result. Preparation requires `--owner-source` and an explicit timing disposition (`--feedback-trigger` or `--feedback-not-due`, alternatively supplied by that owner). It derives `objective_basis` and readable content from the adopted objective, evaluation and current-work sources, separately from the recommendation packet. Frontier derives objective and evaluation from its adopted Problem; a generic task may use its owning task source. See [the owner path](../../skills/frontier-optimization/references/worker-interfaces.md#decision-policy-in-the-existing-resolver-path) for source selection and operation responsibilities.

A due timing result needs `feedback_decision` with `trigger`, `action`, `basis` and `next_condition`; the basis points into the result's actual comparison. Binding checks source association and current decision facts. Recommendation identity alone cannot reuse a resolution after its objective basis changes. Missing required inputs yield no usable new binding. Historical results remain readable, but cannot become new decisions by omitting the required fields. These checks establish source delivery and a recorded decision, not its wisdom: the existing owner must compare actual adoption, dispatch, steering, direct work and resumed work with both the objective and the commitment. Missing optional native telemetry is a separate limitation and does not block otherwise valid work.

This normal path does not require a harness session, a new native-hook identity, or migration to this optional runtime. Its required inputs are distinct from optional policy-observer coverage. Recorded policy delivery/handling is separate from native callbacks and from correctness of the decision.

Use an existing research `Task` with its actual source excerpts, owner methods and limits. Start through `host start TASK.json NEW_RUN_DIRECTORY`. Configure before returning the participating Coordinator proposal. All commands below are `workflow-harness host COMMAND RUN_DIRECTORY` and read their input as JSON from stdin. Paths in inputs must be absolute.

| Command | Input and effect |
| --- | --- |
| `decision-config` | `{ "mode": "observe", "policy": "/absolute/path/decision-policy.md", "timeout_ms": 120000, "publication": "/absolute/workspace/path/to/existing-owner-record.md" }`. The timeout bounds checker waiting, not research work or user resources. |
| `return` | The existing `{ "backend_handle": "actual coordinator handle", "response": ... }`. An enforce-mode qualifying proposal is retained before adoption. Observe mode emits the normal next invocation plus an optional observation request. |
| `decision-status` | No input. Inspect pending input, actual binding, latest receipt and expected publication; reconcile expiry without dispatch. Older receipts remain in the existing checkpoint. |
| `decision-bind` | `{ "check_id": 1, "backend_handle": "actual checker handle" }`. Reuse the already applicable professional judgment when available, with its real handle and sources. Otherwise invoke one bounded check through the current host, using `pending.input`. Never run a model inside the synchronous handler. |
| `decision-result` | `{ "check_id": 1, "backend_handle": "actual checker handle", "verdict": "no_finding", "reason": "Supported disposition", "findings": [], "model_tokens": null }`. A `revise` finding needs `policy_excerpt`, `decision_excerpt` and `correction`. Excerpts must occur in the supplied policy and proposal. Unknown usage stays null. |
| `decision-resolve` | `{ "check_id": 1, "disposition": "revised", "reason": "Owner reasoning", "evidence": ["/existing/source"], "proposal": ... }`. A revised proposal retains its original Coordinator invocation. `contested` and `boundary` use null proposal. Contested continuation preserves the critique and reason; boundary uses the existing pause/reconciliation path. There is no second model acceptance. |
| `decision-publish` | The numeric check ID, for example `1`. Verify the current owner writeback and emit the next invocation. In observe mode, publication and work follow normal owner rules without a new hold. |
| `next` | No input. Emit the next allowed invocation after a released check with no required publication. An already emitted invocation is reconciled through normal host status, never redispatched blindly. |
| `decision-abandon` | A JSON reason string. Return a proposal whose sources became stale to its original owner; a concrete critique still needs owner disposition. |

An emitted `decision_pending` is not a Worker assignment. The CLI command exits and releases its lock before the host checks anything. Bind the actual check call once. On restart, inspect that binding and obtain its result; do not repeat an uncertain invocation. Use `unavailable` for known checker failure or unusable output; a lost call expires on the next bridge interaction. Late replies are retained without reviving a hold. A concrete finding does not expire into a pass. Changed or unreadable decision sources return the unadopted proposal to its original owner; required Workflow sources still govern normal dispatch.

After enforce-mode release, the existing owner writes its normal current decision. Include exactly one current block in that same record, using `publication.check_id` and the complete `publication.proposal` returned by the bridge:

```text
<!-- workflow-current-decision:begin -->
{"check_id": 1, "proposal": { ... exact cleared response ... }}
<!-- workflow-current-decision:end -->
```

This is the correspondence marker in the existing record, not a second selection ledger or a required format for nonparticipating work. Historical mentions cannot satisfy it. The bridge checks it again when generating the dependent invocation. A failed writeback emits no Worker invocation. File writeback, checkpoint update and actual host dispatch are separate operations, not an atomic transaction. After a permitted invocation is emitted, the Coordinator makes the corresponding existing `spawn_agent` or `followup_task` call and records its real handle with `host bind`; the bridge does not own the host's Agent API. Preserve unsettled effects, permissions and original scope. Do not use `next` to repeat a call already launched.

Disable with `decision-config` using `mode: "disabled"` and the existing other fields. A pending unanswered check becomes unavailable and returns to its owner. Resolve an existing concrete finding first; disabling never clears pending owner writeback or independent execution controls. The observation adapter does not queue an unlimited stream of checks: while one is pending, later proposals proceed without another observation, so that interval has incomplete semantic coverage.

## Optional Codex context

The normal `check-continuation --path <adopted-owner>` command and applicable resolver binding/reuse checks do not depend on this optional adapter. See Learning Loop's `evaluation-implementation-and-continuation` rule. Their saved source basis covers current direct observation and work sources; native pointer freshness does not substitute for it. The owner compares actual work, steering and return wording with the adopted arrangement. The command applies only to a new or challenged wait arrangement or whole-effort idle return; ordinary work and completed bounded-deliverable returns need no invocation merely because another observation remains pending. This adapter does not capture all messages or intercept final answers. Test omitted applicable invocation, unavailable registration and resumed old context separately from Hook event handling.

The installed project definition now uses `workflow-codex-hook --record-context
WORKSPACE`. It resolves only the native root session's pointer under
`.frontier/hook-context/SESSION_ID.json` and reads that owner's existing decision
record. The Coordinator calls `frontier_references.py adopt-work --path <owner>`
in the same operation that saves Selection or changes active work. The helper
reads saved `current_state` and its selected Batch. Direct development may point
`current_state.work_record` to its existing work document instead. Ordinary
Batch writes refresh that root's active association. Source fingerprints detect
stale bytes, not semantic fidelity or security. The pointer stores derived
context and references, not a second decision or approval. A racing refresh
cannot replace a newer pointer with its prior snapshot.

`resolver` and `bind-resolution` register only `SESSION_ID-proposal.json`; they
never publish adoption. Legacy pointers remain readable as proposal context,
without adopted-work or dispatch coverage. Register the saved current work to
participate in the new path. Other roots, unmapped children and workspaces cannot
borrow the pointer. Pause and completion stay visible without automatic resume.
Missing or corrupt optional state never denies ordinary work.

Research recovery follows the owner's existing plan for the whole-chain advantage
hypothesis, its decisive prospective conditions, outstanding target feedback and
remaining path, not just its latest completed step. Use Learning Loop's
`prospective-reasoning` rule in the existing investment judgment; native context
does not evaluate future scenarios or require a forecasting stage. Keep that
context in the owner's normal current-work summary or
plan reference. The native reminder points to Learning Loop's
`whole-chain-investment-and-target-feedback` rule; it does not parse the plan,
decide readiness or classify delays. At handoff, the owner compares the actual
task with the selected feedback arrangement. An unsupported postponement must
change the affected next task, not just its disclaimer. This reuses the existing
judgment and adds no per-step review, model call or automatic denial.

The root observer captures structured inputs only for `spawn_agent` and
`followup_task` (including qualified names, the desktop's concatenated namespace
names such as observed `collaborationfollowup_task`, and the native `Agent` alias),
then matches `PostToolUse` by session, tool name, call ID and actual input. These
are adapter-supported names; native host coverage requires real receipts.
Every follow-up has its own call. The observer accepts an object response or one
JSON string encoding an object, preserves the original response, and gives
explicit errors precedence over handles. It does not recursively decode strings.
Malformed, scalar and unknown response envelopes stay uncertain; successful
structured handles establish dispatch, never worker completion.
The observed desktop path can expose an opaque task body. Such a receipt retains
host bytes and call identity but not readable assignment meaning. The adapter
marks this limitation and leaves substantive comparison to the actual task in
the existing owner conversation. It does not decode payloads or claim complete
assignment capture from a prepared copy. New envelope formats remain unverified.
At the existing return, `bind-return --result <existing-result.json> --call <id>`
links the result to the original attempt and available response. Other return
formats retain the same references in their existing record. This authored
association still requires the owner's substantive reading of the actual result.

Missing posts never authorize a repeat. Late posts retain their original work
association. No shell text, transcript, per-command development trace or semantic
model is inspected. Ordinary context is deduplicated; each actual dispatch is
retained. The new path has observation mode only, with no automatic denial or
continuation. Updated definitions require the host's normal trust review. Tests
of event shapes do not establish native delivery or research efficiency.

The older explicitly bound runtime adapter below remains available for existing
participants; the project definition no longer points to its installation run.

Build the existing binary with `cargo build --locked --manifest-path tools/workflow-harness/Cargo.toml`. The new command is:

```text
workflow-codex-hook --decision-context WORKSPACE SESSION_ID OWNER_AGENT_ID RUN_DIRECTORY
```

Use verified current identities and canonical workspace paths. `OWNER_AGENT_ID` is `-` only for a verified root callback with no native `agent_id`; a child uses its exact native ID. This is separate from the existing controlled Worker command. Never reuse identities from an old pilot.

Configure this command as a synchronous command hook, with a two-second timeout, for `SessionStart`, `SubagentStart` where that owner is actually bound, and `PreToolUse`. Use the [official Hooks configuration and trust flow](https://learn.chatgpt.com/docs/hooks); preserve other definitions. The handler adds at most 4,000 characters of current context. Ordinary pre-tool calls return nothing; one pending condition produces at most one pre-tool reminder. A single first-delivery receipt per configured event kind retains identifiers and timing without command arguments or transcripts. It neither reads command text nor invokes a model, rewrites a call or denies all Coordinator tools. Malformed optional state degrades context delivery without blocking the owner's recovery tools.

No `Stop` hook is installed: this implementation chooses zero automatic continuations, which respects user interruption without guessing cancellation from unstable transcript fields. Context-only hooks cannot themselves force correct decisions. Enforcement remains at the participating owner operation; the existing fixed-Worker adapter retains its separate tested behavior.

This repository ships an observation-only Codex project definition. Native loading,
root and child identity, resume or compaction delivery, and latency remain unverified
for a consuming repository until its own receipts establish them. Subprocess tests
exercise the event handler only. Review and trust the exact scoped definition through
Codex; do not edit trust storage to bypass that review. Continue ordinary research
without a separate validation campaign.

## Verification and interpretation

Run `cargo test --locked --manifest-path tools/workflow-harness/Cargo.toml -- --test-threads=1`. Decision tests cover held adoption, restart, correlation, invalid/late returns, stale input, unavailable policy, owner correction/disagreement/boundary, exact current writeback, unchanged internal work and native context isolation. Existing tests retain permission/effect/continuation coverage. These do not certify a model's research judgment.

Keep semantic observations in the existing design or working result. Record detected defects, missed defects and false alarms, actual changed work, available model calls/tokens and waiting time. Unknown usage is not zero. A useful retained-text judgment is weaker than corrected real dispatch, which is weaker than improved objective outcomes. If the adapter adds waiting without changing consequential decisions, simplify or disable it.
