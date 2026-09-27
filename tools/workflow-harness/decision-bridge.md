# Optional consequential-decision bridge

This extends the existing host bridge, not the campaign lifecycle. It is disabled unless configured on one participating research run. Deploy with `observe` first. Mechanical tests and a retained-text calibration do not justify universal enforcement or claim improved research efficiency. Use `enforce` only for a supported boundary class in a deliberately participating path.

## Owner integration

The first supported path is the Frontier Coordinator's proposed new or materially revised investment, current Selection writeback and following professional dispatch. The [owner instructions](../../skills/frontier-optimization/references/worker-interfaces.md#optional-decision-bridge) consume this path. The owner supplies the existing `WorkUpdate.options` entry selected by `selected`, including its question, mechanism, useful result, necessary work and prerequisites. Rationale and switching conditions belong to that commitment. Update these when the assignment changes their substance. Ordinary internal-step wording and remaining progress do not require another check.

The first participating commitment enters the check automatically. Later checks use the existing investment trigger, reported as `update.investment_changed: true`. Ordinary progress, restated rationale and policy-file edits alone do not start another judgment. The owner must report a substantive change even if it retains the same label or prose. Saved commitment text is audit content, not a semantic change detector; this remains a cooperative owner contract. Direct Agent calls, arbitrary Selection writers and nonparticipating runs are not intercepted. Do not claim complete campaign enforcement.

Configured sessions supply the policy to the existing Coordinator and Resolver requests. Reuse that one applicable independent judgment through `update.resolved_invocation` (an accepted Resolver invocation in this run), or `resolved_by` (existing supplied source indices). The owner asserts substantive applicability; the runtime verifies references and records reuse without launching another model or fabricating a `no_finding` verdict. Enforce mode retains the existing current writeback check. Missing policy stays unavailable even when a judgment reference exists. New fields default to ordinary continuation/no reused invocation when reading older records.

For the repository's normal reference-based Workflow, `frontier_references.py resolver` and `bind-resolution` now deliver this same policy and retain coverage within their existing assignment/result. See [the owner path](../../skills/frontier-optimization/references/worker-interfaces.md#decision-policy-in-the-existing-resolver-path). It does not require a harness session, a new native-hook identity, or migration to this runtime. Recorded policy delivery/handling is separate from native callbacks and from correctness of the decision.

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

The root observer captures structured inputs only for `spawn_agent` and
`followup_task` (including qualified names, the desktop's concatenated namespace
names such as observed `collaborationfollowup_task`, and the native `Agent` alias),
then matches `PostToolUse` by session, tool name, call ID and actual input. These
are adapter-supported names; native host coverage requires real receipts.
Every follow-up has its own call. Unknown response envelopes stay uncertain;
successful structured handles establish dispatch, never worker completion.
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

This repository ships an observation-only project definition. Native loading,
session identity, resume or compaction delivery, and latency remain unverified in
each consuming environment until real receipts establish them. Subprocess tests
exercise the event handler only. Trust the exact definition through Codex; do not
edit trust storage or treat a retained receipt as proof of current coverage.

## Verification and interpretation

Run `cargo test --locked --manifest-path tools/workflow-harness/Cargo.toml -- --test-threads=1`. Decision tests cover held adoption, restart, correlation, invalid/late returns, stale input, unavailable policy, owner correction/disagreement/boundary, exact current writeback, unchanged internal work and native context isolation. Existing tests retain permission/effect/continuation coverage. These do not certify a model's research judgment.

Keep semantic observations in the existing design or working result. Record detected defects, missed defects and false alarms, actual changed work, available model calls/tokens and waiting time. Unknown usage is not zero. A useful retained-text judgment is weaker than corrected real dispatch, which is weaker than improved objective outcomes. If the adapter adds waiting without changing consequential decisions, simplify or disable it.
