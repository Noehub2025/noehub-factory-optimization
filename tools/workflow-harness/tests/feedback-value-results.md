# Feedback value repair verification

This is an inherited source-verification record. The source executor samples
and independent reviews were not rerun during distribution migration.
Distribution checks are reported separately. Consuming-project code and business
state described below are outside this portable bundle.

Date: 2026-10-06. Scope: the installed platform-neutral Workflow, its optional
Codex context prompt, decision-source receiving, and the current project's
recovery summary. No algorithm, investment allocation, permission, submission or
other business operation was changed by this repair. The optimization owner had
already adopted its own reconsideration before the summary was synchronized.

## Problems and changes

| Problem | Change | Evidence boundary |
| --- | --- | --- |
| Unknown outcome treated as value | Retain existing objective, information and remaining-cost comparison; do not introduce another form or mandatory prediction. | The original business resolution already contained reasons and alternatives. It was not diagnosed as reason-free merely because reviewers disagreed. |
| Evaluation limits erase adverse evidence | Learning Loop applies relevant limits to favorable and adverse inferences for the same use and distinguishes uncertainty from absence of information. | Different treatment remains possible with a concrete basis; equal weights are not required. |
| Complementarity becomes combination priority | Distinguish useful information from the particular realization's use of it. | No complexity, tuning, local-win or comparator quota was added. |
| Result scope expands in later work | Result adoption inspects what the next task actually retains, changes or excludes. Limited results may change investment without proving mechanism failure. | Full attribution and a conclusive single trial are not prerequisites. |
| Ready feedback protects a challenged choice | Selected feedback proceeds when its basis still applies. New facts, a recognized defect in the original rationale or a stronger opportunity use existing judgment responsibilities. | Mere disagreement or a policy revision does not reopen history. |
| Recovery restores old instructions | Synchronize affected operative state, continuation, summary and task, marking superseded instructions as history. | Source identity is not semantic correctness; already started effects are preserved. |

The main rules remain in `learning-loop.md`, with small receiving changes in
`result-adoption.md`, `worker-interfaces.md`, `decision-policy.md` and the actual
`native_context.rs` prompt. Existing independent investment judgment and owner
adoption remain unchanged. No state machine, new schema, approval or global
runtime gate was added. Technical-design guidance was reused without modification.

## Receiving defect found during implementation

The project owner selected `user_challenge_reconsideration` inside a retained
historical resolution. `prepare_adoption_context` displayed this selected field
but interpreted the entire parent as the decision, so its obsolete binding
rejected the newly adopted use. `verify_prepared` independently had the same
whole-file assumption. This was an actual receiving failure, not a disagreement
about research value.

Both entries now share `_decision_source_body`: an explicitly selected mapping
field is its own decision; scalar fields and prose sections remain excerpts of
the parent decision and retain its assignment and binding checks. A missing or
ambiguous decision selector cannot fall back to another decision. Full source
material remains available. An unbound selected paragraph does not inherit a
historical binding or gain authority merely by being delivered.

The first reproduction produced five failures and one expected pass. The first
repair passed those cases but the existing full suite exposed lost incoming-task
context for `field=reason`. That compatibility failure was retained and repaired
by distinguishing mapping selections from excerpts. Nine added regression cases
now cover selected bound and unbound decisions, missing/ambiguous selectors,
changed selection after recomputing display identity, changed source contents,
whole-decision validation, and scalar excerpts retaining parent correspondence.
No formal resolver binding or reuse requirement was relaxed.

## Observed Agent behavior

Three fresh executor contexts received ordinary assignments, raw fixture files,
the installed relevant rules and a local consumer. They did not receive this
report, expected answers or the audit diagnosis. The existing-worker context
received later evidence in a follow-up. The source used disposable local fixtures whose operator notes retained
inputs and invocation details. The case recipes extend
[target-feedback-cases.md](target-feedback-cases.md), L-O.

| Path | Actual observed use | Limit |
| --- | --- | --- |
| Direct A | Read available target evidence and consumed a twenty-minute ordering experiment instead of two days of feature expansion; both pilot and adverse development evidence remained conditional on unmatched inputs. | The new experiment was accepted by the synthetic consumer, not scientifically run. |
| Direct B | Used 5/100 misses against an absolute requirement of at most 6 and cancelled comparator reconstruction. | Does not establish relative improvement or future-window performance. |
| Direct C | Consumed still-supported paired feedback and adopted C9 without another experiment or attribution gate. | Applies to the supplied workload only. |
| Direct D | Replaced blanket compression retirement with a mixed-workload experiment after a limited configuration result. | No improvement from that future experiment was observed. |
| Cold recovery | Corrected task, summary and plan; reconciled the original effect. History contains the original execute and one reconcile, with one accepted effect. | Demonstrates this local fixture's consumption and absence of repetition, not host authorization enforcement. |
| Existing worker | Initially consumed valid paired evidence. After changed counter semantics and request lists, corrected the task and plan, read raw logs, then consumed a fresh paired capture and withdrew the earlier preference. Five events remain, with no execute. | Feedback is pre-recorded synthetic data. Missing latency only limits the complete objective claim. |

Independent review found a real first-pass closure failure: Direct A/B/D had
changed their plan and consumed task but left conflicting current commands in
`task.md`. The original executor corrected those files in the same context and
marked original instructions as superseded history. No consumer call or
experiment was repeated: eight direct events and two accepted synthetic effects
remain, with unchanged hashes for all three environment records. Guidance now
explicitly addresses competing current commands. These samples therefore show
review-assisted closure, not flawless first-pass autonomous compliance.

The existing worker's initial return suggested another matched window because
repeatability remained unknown; it did not consume that extra observation.
Accordingly, the samples do not prove that unnecessary verification tendencies
are eliminated. Direct C is the positive evidence for adopting adequate feedback
without another measurement. No pre-change randomized behavior comparison or
end-to-end research cost measurement was performed.

## Mechanical checks and actual receiving

- Reference/context suite: 136 passed, including nine added regression cases.
- Rust decision, native context and correspondence integration suite: 78 passed.
- Skill validation, complete installed bundle validation, Rust formatting and
  `git diff --check` passed.
- The release `workflow-codex-hook` was rebuilt. The configured `run-codex-hook`
  launcher was invoked against an isolated adopted-work fixture; its 2,094-character
  context contained both priority and delay guidance, with no permission decision.
- At the receiving checkpoint, the project's real `prepare_adoption_context ->
  model_view -> verify_prepared` path received the selected reconsideration field
  and updated Brief without inheriting the historical parent binding.
  `check_continuation` reported current with five source checks. The prepared
  snapshot was retained in the source audit workspace.
- Subsequent business progress changed FRONTIER, so that saved snapshot was
  correctly rejected. Continuation checks also detected changes in
  the consuming project's matched-assessment assignment and Batch record. The original owner must reconcile the
  actual changes and prepare and verify a fresh view before its next dependent
  use. This repair did not refresh business hashes or change the allocation to
  make stale evidence pass. The earlier checkpoint is not a current acceptance.

Independent reviewers checked rule closure, efficiency and execution separately.
The rule review found no additional mandatory gate. The efficiency reviewer
found the first-pass task synchronization defect described above and verified
the original executor's correction without repeated effects. The execution
reviewer independently passed ten selected new and existing recovery tests and
invoked the actual release launcher, confirming the updated advisory context.
That reviewer also reproduced the later rejection of the stale project snapshot.

Reproduction commands:

```sh
pytest -q skills/frontier-optimization/scripts/test_frontier_references.py skills/frontier-optimization/scripts/test_frontier_context.py
cargo test --offline --locked --manifest-path tools/workflow-harness/Cargo.toml --test decision
cargo build --offline --locked --release --manifest-path tools/workflow-harness/Cargo.toml --bin workflow-codex-hook
python skills/frontier-optimization/scripts/validate_frontier_skill_bundle.py skills --output /tmp/workflow-feedback-bundle.json
```

Context7 resolution timed out before programming; the official
[Cargo test documentation](https://doc.rust-lang.org/cargo/commands/cargo-test.html)
was used for the existing integration-test entry. No dependency was installed.

## Adoption and coverage

The source project owner independently changed its allocation. That source
repair synchronized the maintained Brief with the already-adopted decision and
fixed its actual source receiving. Historical instructions remained history;
distinct user authorizations retained their original meanings;
no message was sent to a separate user-owned chat and no external action occurred.
The owner decision is not evidence that this rule patch caused better research.

The native Hook remains advisory and does not capture every steering message.
Direct execution, existing workers and cold recovery have the bounded sample
evidence above; other platforms and all live contexts are not certified.
Successful delivery, sound judgment, actual adoption and improved research
outcomes remain separate claims. Broad scientific or efficiency benefit remains
unmeasured.
