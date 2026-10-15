# Agent capacity repair verification

Date: 2026-10-05. Scope: installed platform-neutral Workflow rules and the
optional local Harness in the source installation. This inherited record
retains the source review and executor samples; those model samples were not
rerun during distribution migration. Distribution checks are reported separately.
The consuming campaign, historical results, running workers and external
operations are outside this repair.

## Problems and repair scope

| Issue | Repair | Verification required |
| --- | --- | --- |
| P1: capacity information becomes a prerequisite | Unknown capacity permits ordinary authorized dispatch; queries do not reserve capacity | Normal dispatch and a query/admission race control |
| P2: confirmed non-start cannot resume | Preserve the failed attempt and permit a correlated retry of the same work | Real Session cold recovery and actual single execution |
| P3: lost dispatch response leads to repetition | Persist a participating host-call association before dispatch; recover the original handle | Lost-response recovery and unknown-outcome rejection |
| P4: waiting parents occupy required child capacity | Existing owners arrange safe return, serial work or supported yield/resume | Isolated scheduling exercise; no live-host universal guarantee |
| P5: reuse violates independence | Reuse remains conditional on existing context and participation rules | Independent rule review and scheduling controls |
| P6: completion, reuse and release are conflated | Use actual host release semantics after saving needed results and recovery data | Rule review; Harness does not release host capacity |
| P7: retries and administration replace useful work | Ground retries in recovery evidence and reuse unchanged arrangements | Rule review and reachable continuation checks |
| P8: optional coverage is treated as universal | Common rules have ordinary entry links; README separates supported paths | Source links, adapter tests and explicit uncovered paths |

The executable and behavioral cases are specified in
[agent-capacity-cases.md](agent-capacity-cases.md). These are development checks,
not additional project workflow gates. No global capacity registry, new
scheduler, fixed thread count, mandatory per-dispatch inventory or approval was
introduced. The Codex Hook remains Codex-only.

## Independent rule review

An independent reviewer checked the actual shared section and its Frame,
Frontier, research and Batch entry links. Two findings were adopted: unresolved
startup blocks only the same work or overlapping effects; ordinary follow-up
reuses a still-applicable arrangement without another scheduling comparison.
The reviewer found no need to copy the rules into every professional Skill or
relax existing fresh-context requirements, and confirmed both wording repairs.

## Runtime reproduction and review

Before the code repair, the new non-start recovery test failed with
`replace only unstarted worker requests; reconcile existing effects first`.
The failed attempt remained registered even after non-start recovery, so neither
normal dispatch nor queued replacement could continue that work. The repair
uses a correlated non-start receipt and an explicit retry with a new invocation
associated with the original work. It preserves failed attempts and cumulative
usage without manufacturing a Worker result. Legacy uncorrelated `NotStarted`
remains readable but cannot establish permission to retry.

The native bridge now records a host-supported correlation before dispatch.
Recovered acceptance binds the original handle; missing or unknown outcomes
block repetition on participating transports. A host without such a recoverable
association retains the documented legacy coverage limit. The controlled CLI
also exposes structured recovery, so the repair is reachable without writing a
new adapter or fabricating a response.

Independent review initially found two invalid test setups: a controlled Worker
returned without its required execution and settled termination evidence. The
fixtures were corrected to perform that handshake; production checks were not
weakened. A later review found that the two new controlled recovery branches
could leave hot Session state behind an already-published checkpoint when the
directory synchronization failed. The reviewer reproduced this with real Unix
directory permissions in a disposable source-audit workspace: the checkpoint
contained
`start_confirmed: true`, but the hot Session accepted a contradictory non-start
receipt. The repair reuses the existing checkpoint synchronization helper in
both recovery branches. The original reviewer reran its independent permission
failure test against the repaired source and confirmed that the contradictory
receipt is rejected. It also independently verified that enforced judgment and
current-use bindings survive cold retry without another checker, while changed
source bytes still prevent dispatch. No must-fix finding remained at final
review. These are implementation findings, not a certification of every host.

## Fresh executor work samples

Two fresh agents received raw local tasks, the documented fixture interface and
the installed Workflow rules, without expected answers or the audit notes.
The host fixture executes real local commands and persists their results, but
its independent checker is deterministic code under a distinct fixture
identity, not an independent AI review or a real platform thread.

1. Supported safe handoff in a disposable local workspace: the executor saved its
   continuation and performed `handoff`, `review`, `release`, `resume`, `finish`
   in that order. The only review invocation was `review-1`. The same builder
   resumed and produced `category-summary.json`: six records, hardware 15,
   support 7, supplies 11, total 33. It did not need a failed dispatch or repeated
   query before arranging useful work. Completion was correctly distinguished
   from release: the checker was explicitly released after its report was saved;
   the completed builder was not described as released.
2. No safe handoff in a separate disposable local workspace: the executor inspected
   actual host state, preserved the required independent check, and saved an
   outcome identifying the occupied pool and unavailable safe-handoff operation.
   It performed no futile dispatch, invented release, author self-review or
   final-artifact bypass. The unfinished delivery and precise recovery condition
   remain recorded; this control did not complete the business artifact.

The main agent independently checked the persisted operation trace, expected
totals, report-to-source hashes, unchanged candidate and inputs across the two
fixtures, and retained continuation hash. The unsupported control retained an
empty operation history. These samples demonstrate observed use of the new
rule on the exposed fixture interfaces. They do not establish live platform
scheduling, independent model review, response-loss recovery, universal
reliability or a net research-efficiency gain. Total model/context cost was not
measured. Temporary workspaces are local evidence and may later be removed;
the companion cases preserve their purpose and reproducible conditions.

## Mechanical validation

Python source-delivery and bundle regressions: 141 passed. Metadata validation
passed for Frame, Frontier, research-frontier and run-frontier-batch; 183 local
Markdown links and anchors resolved. These checks do not establish scheduling
judgment or live adoption.

Final Rust suite: 139 passed, including 18 control tests and 78 decision tests.
This repair adds 11 tests to the previous 128-test suite. Coverage includes
confirmed non-start and cold retry, retained usage and work, unsupported and
unknown recovery, stale receipts, accepted/running/event contradictions,
lost native responses, transport bypass attempts, failed checkpoint/journal
publication, and preserved enforced judgment/current-use checks. The real Unix
permission regression exercises both recovery directions in hot and cold
Sessions. It was not skipped on this non-root host; privileged users unable to
induce the permission failure receive an explicit test diagnostic.

`cargo fmt --check` and `git diff --check` passed. Both local release binaries
were rebuilt at the existing launcher's preferred paths:
`tools/workflow-harness/target/release/workflow-harness` and
`tools/workflow-harness/target/release/workflow-codex-hook`. No target-directory
override or Hook configuration change was made. Two actual release-CLI tests
passed: stream-process creation failure through recovery/retry/completion, and
native pre-dispatch association through recovered binding/controlled return.

```sh
cargo test --offline --locked --manifest-path tools/workflow-harness/Cargo.toml
cargo build --offline --locked --release \
  --manifest-path tools/workflow-harness/Cargo.toml \
  --bin workflow-harness --bin workflow-codex-hook
cargo test --offline --locked --release \
  --manifest-path tools/workflow-harness/Cargo.toml --test control host_cli_
```

At the source verification checkpoint, deployment was limited to local source
and binary updates. No Git commit, push, live worker restart or external
business action had been performed at that checkpoint.

## Coverage and efficiency limits

Participating adapters must tell the truth about backend state. A recorded
intent does not prove startup or non-start; unknown outcomes remain unresolved.
The Harness does not allocate slots, implement platform release, inspect every
direct call, or supply fresh model context. A host without a recoverable call
association cannot claim automatic recovery of a lost response.

Rules apply on future use of the installed entries. This repair does not
restart or migrate existing business sessions, rewrite their assignments, or
claim that they have adopted the changes. Synthetic fixtures and passing tests
cannot establish improved research throughput. That requires observation of
time to useful results, including waiting, context recovery and repeated work,
in an actual consuming task.
