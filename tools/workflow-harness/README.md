# Workflow invocation harness

This optional Rust harness preserves a bounded optimization assignment across
agent calls, records cumulative execution evidence, and returns every worker
result to its coordinator for adoption. It complements the Skills; it does not
replace their professional judgment, permission boundaries, or project records.

The core is host-neutral. The checked-in project Hook is a Codex adapter only.
This release intentionally provides no Hook configuration or compatibility
shim for Claude Code, Cursor, or other agent hosts.

## What it controls

Protocol version 2 is enabled when a task includes a `research` object. It can:

- deliver a research question, missing observation, current rationale, sources,
  constraints, alternatives, and role-specific methods;
- preserve the whole-chain advantage hypothesis, decisive prospective
  conditions, and selected target feedback across owner and Batch handoffs;
- bind a consequential decision to its adopted objective, evaluation, and
  current-work sources, including an explicit feedback-timing disposition;
- carry validated current-use corrections into Worker preparation, reject stale
  queued work, and replace only requests that have not started;
- retain delayed observations, delivery failures, capability limitations, and
  recoverable alternatives without converting them into automatic support work;
- correlate a worker return with the invocation that created it;
- retain cumulative elapsed time, model tokens, compute, and currency-specific
  spending without treating unknown values as zero;
- withhold continuation at a selected return boundary, changed source, pause,
  unresolved effect, or material challenge; and
- recover persisted state without blindly repeating an uncertain call.

The harness does not sandbox an uncooperative process, settle external effects,
prove that a result is correct, or intercept host tools that are not connected
to one of its adapters.

Current-use checks verify retained finding identity, saved source bytes, and the
request consumed by a cooperating host. They do not decide whether a correction
is semantically sound. The existing owner must first validate and adopt the
corrected work with the Skill helper; direct or unsupported dispatch paths still
require that owner to inspect the actual outgoing task.

The native context is a concise reminder, not a forecasting engine or decision
maker. The existing owner still decides whether target feedback is ready,
whether a delay is necessary, and how external changes or intervention-induced
effects alter the next commitment. Behavioral examples live in
[`tests/target-feedback-cases.md`](./tests/target-feedback-cases.md) and
[`tests/foresight-cases.md`](./tests/foresight-cases.md). Additional bounded
cases cover [capability learning](./tests/capability-learning-cases.md),
[research judgment](./tests/research-judgment-cases.md), and
[research transfer](./tests/research-transfer-cases.md). These cases test
decision behavior; they do not prove objective improvement in a live campaign.

## Build and test

Rust 1.89 or later is required.

```sh
cargo build --locked --release \
  --manifest-path tools/workflow-harness/Cargo.toml \
  --bin workflow-harness \
  --bin workflow-codex-hook

cargo test --locked \
  --manifest-path tools/workflow-harness/Cargo.toml \
  -- --test-threads=1
```

The project Hook calls `run-codex-hook`, which selects the release binary first
and then a debug binary. Until one has been built, it exits without changing a
tool decision. Build artifacts remain local and are excluded from Git.

## Host-neutral controlled execution

Start a task with a process that implements the JSON-line transport:

```sh
tools/workflow-harness/target/release/workflow-harness \
  TASK.json NEW_RUN_DIRECTORY --stream-adapter ADAPTER.json
```

The adapter configuration names a process and its literal arguments plus its
actual capabilities: events, controlled continuation, cooperative cancellation,
recovery, fresh context, and isolation. Capability declarations are not proof;
the selected backend must route the covered actions through the boundary.

At an idle boundary, the backend waits for a `continuation` message. A `return`
decision permits settling current work and returning evidence, not starting new
discretionary work. Cancellation begins as pending. Unknown live effects stay
unknown until reconciled, and recovery never converts a persisted intention
into proof that the backend received or completed it.

## Use an agent host directly

The host bridge lets the current coordinating agent perform its normal agent
calls while the harness preserves identity and ordering:

```sh
tools/workflow-harness/target/release/workflow-harness \
  host start TASK.json NEW_RUN_DIRECTORY
```

The coordinator sends the emitted prompt to the emitted role, then records the
actual returned handle:

```json
{"invocation_id":1,"backend_handle":"actual-host-agent-handle"}
```

Pass that object to `host bind RUN_DIRECTORY`. When the agent returns, pass its
handle and structured response to `host return RUN_DIRECTORY`. Use `host status`
to recover an existing pending invocation and `host continue` only when no
invocation remains pending. Never use a new run directory to bypass unresolved
effects or an uncertain dispatch.

For a participating current-use correction, validate the owner and affected
sources with `frontier_references.py check-current-use`, then pass that JSON
report to `host current-use-adopt`. If an affected Worker request is queued but
has not started, `host current-use-replace` emits a corrected replacement.
Before external dispatch, `host current-use-check` compares the actual request
with the retained binding. These operations preserve the owner's judgment; they
do not create a new approval or infer correctness from hashes.

This path orders participating calls but does not own the host's agent API and
cannot safely stop arbitrary work already running outside its boundary.

## Optional consequential-decision bridge

The bridge in [decision-bridge.md](decision-bridge.md) can attach one bounded,
independent check to a materially new or revised investment. It is opt-in and
starts in observation mode. Ordinary implementation progress does not create
another review, and a retained judgment can be reused when its scope still
applies. The detailed command contract and recovery rules live in that file.

The bridge does not prove better optimization decisions. Evaluate it by whether
it changes consequential work or reduces uncertainty at acceptable cost, not by
the number of checks or receipts it creates.

## Codex Hook

The repository includes [`.codex/hooks.json`](../../.codex/hooks.json). Codex
loads this project layer only after the repository is trusted, and changes to
the definition require normal Hook review. Inspect the active definition with
`/hooks` in Codex.

The Hook resolves the repository with `git rev-parse --show-toplevel`; it does
not contain a machine-specific checkout path. It observes only a root Codex
session that has an explicit pointer at:

```text
.frontier/hook-context/<session-id>.json
```

The Frontier helper creates or refreshes that pointer when the coordinator runs
`frontier_references.py adopt-work` for saved current work. Without a valid
pointer, the Hook emits no workflow context and never blocks ordinary work.

Configured events are deliberately narrow:

- `SessionStart` restores concise adopted-work context after startup, resume,
  or compaction;
- `PreToolUse` refreshes that context and records the exact input for supported
  agent dispatch calls; and
- `PostToolUse` correlates the response for those same dispatch calls.

The observer does not inspect arbitrary shell text, call a model, grant
permission, deny tools, rewrite calls, resume paused work, or continue a session
automatically. A successful dispatch receipt is not worker completion or
semantic acceptance. Missing or malformed optional state degrades observation
coverage without creating a new authority boundary.

Do not copy this Hook into another agent's configuration format. For Claude Code,
deploy `AGENTS.md` or its documented `CLAUDE.md` import adapter; those instruction
files are separate from Codex Hook execution.

## Scoped worker adapter

The same binary also retains an explicitly bound worker mode:

```text
workflow-codex-hook WORKSPACE SESSION_ID AGENT_ID RUN_DIRECTORY
```

It applies only to one verified worker, session, repository, pending invocation,
and native turn. Enable it with `run/hook-enabled.json` containing JSON `true`.
Disable it before removing a cached host definition. The adapter can return a
Codex `PreToolUse` denial when the shared session says the worker must return to
its coordinator; unrelated parent, sibling, repository, and tool activity stays
outside that binding.

Use this mode only after verifying the host's actual session and agent identity.
An instruction or declaration is not evidence that native callbacks cover the
intended action.

## Evidence limits

The test suite covers persistence, event correlation, continuation, cancellation,
recovery, decision-check state, owner context, dispatch receipts, and scoped
Hook behavior. Subprocess tests establish component behavior only. They do not
establish native delivery in every Codex release, complete host coverage,
scientific correctness, or improved objective outcomes.
