---
name: frame-optimization
description: Frame an optimization problem into an evidence-backed A-H comparison contract before solution work. Use when the user wants to define or clarify an optimization task, resume a task under docs/skills/optimization/, or coordinate research, user decisions, and independent readiness review.
---

# frame-optimization

Build the **frame** that makes solution comparison meaningful. Coordinate evidence, user-owned decisions, contract repair, and independent review without performing optimization.

## Operating contract

Act as the Primary Framing Agent. Own every Contract cell, row status, normative Slot rule, task term, and downstream handoff.

Use the worker skills for bounded work:

- `research-optimization` returns evidence for one factual question.
- `grill-optimization` resolves one user-owned decision at a time.
- `review-optimization` runs readiness or comparability review in a fresh context.

The user supplies private facts, authority, preferences, and value choices. The user does not judge technical completeness or approve a review verdict.

Read [references/task-documents.md](references/task-documents.md) completely before creating or editing task documents. Treat that file as the single source for task paths, formats, ownership, invalidation, epoch, and language rules.

Use the host's native Skill and agent controls. Do not depend on a vendor-specific command name. Research and grilling can run serially when the host has no parallel workers. Readiness and comparability review still require a separate fresh context; when the host cannot provide one, record a review-capability blocker and stop.

## 1. Select or create one task

Require a caller-selected task slug or canonical task path. If several task directories exist without a selection, request one; recency is not a selector.

Validate the slug and resolved path as defined in `task-documents.md`. For a new task, create the task directory and its initial `PROBLEM.md` from that file. Preserve existing project documents and link them as sources.

This step is complete when one safe canonical path is selected and its `PROBLEM.md` exists.

## 2. Recover the durable frame

Read `PROBLEM.md`. Read `log.md` and `review.md` when they exist.

When `review.md` contains an open repair set, select its first safe open finding. Stop when only an unchanged blocker remains.

Otherwise, select the first `O` or `~` row. Open only the linked detail needed for that item.

Confirm an unrecorded last user answer instead of reconstructing it from conversation history.

This step is complete when one next item is selected from repository files, or the recorded frame has no unresolved item.

## 3. Draft the A-H contract

For a new frame or a material reframe, read [references/slot-contracts.md](references/slot-contracts.md) completely before writing rows.

Inspect applicable repository evidence before asking questions. Draft every Slot A through H and use these states:

- `P`: evidence or an authorized decision pins the contract.
- `~`: a documented provisional answer permits more framing work.
- `O`: a necessary point remains open, and the Contract names its closing action.
- `-`: the Slot cannot affect comparison, and the Contract gives the reason.

Create a Slot document only when two Contract sentences cannot carry the rule. Keep detailed evidence, formulas, quantifiers, distributions, and actions in that linked document.

This step is complete when all eight rows exist, every row satisfies its Slot completion test, and no assumption that can change comparison remains hidden.

## 4. Resolve one open item

Classify the next item before acting:

| Work type | Route |
|---|---|
| `research` | Give one bounded factual question and Slot to `research-optimization`. |
| `grill` | Use `grill-optimization` for one private fact, authority question, preference, or value choice that evidence cannot settle. |
| `reframe` | Repair missing or conflicting semantics directly. Route any new factual or user-owned dependency first. |
| `blocker` | Record the exact missing authority, private fact, data, tool, access, or fresh context. |

After research, assess the evidence and make the semantic Contract edit yourself. After grill, record the answer, decision source, and Contract effect before asking another question.

Apply review invalidation in the same change as every meaningful edit. Record an evidence-backed reversible default as `~` with `Decision source: agent default`.

If a required worker skill is unavailable, keep the item `O` and name the missing work. Repeat this step until no safe open work remains.

This step is complete when the selected item is pinned, provisional with evidence, not applicable with a reason, or open with one exact next action or blocker.

## 5. Protect retained results

Before completing a semantic change to a `P` contract, search for retained results that name the task and epoch.

When retained results exist, preserve both old and proposed meanings and request the `comparability` branch of `review-optimization` in a fresh context. Continue only after `log.md`, the epoch, and every affected result record agree with the disposition.

When no retained result exists, apply the change and normal review invalidation without an epoch disposition.

This step is complete when the edit has no retained result, or every retained result is unaffected, re-evaluated, or voided in durable files.

## 6. Run readiness review and repair

Request the `readiness` branch of `review-optimization` in a fresh context when every applicable row is `P` or `-` and the current repair set is complete.

When a documented agent default remains `~`, obtain user confirmation or independent acceptance before the final readiness run. Record independent acceptance as a review finding, pin the row as the Primary Framing Agent, and request a new fresh readiness review.

Pass only the canonical task path and applicable review instructions. Validate the returned verdict and finding schema against `task-documents.md`.

For a valid non-`PROCEED` result, complete every independent safe action in the current repair set. Request another fresh review only after every completion condition holds, every applicable row is `P` or `-`, and a finding-related durable change exists.

For an invalid result, request one fresh replacement. If the replacement is invalid or unavailable, record a review-capability blocker, keep the task `draft`, return workflow outcome `BLOCKED`, and stop.

This step is complete when review returns durable `PROCEED`, a recorded blocker stops the run, or the next required user answer is recorded as an open action.

## 7. Hand off the frame

On `PROCEED`, re-read `PROBLEM.md` and confirm `status: stable`, current `verified`, comparable retained results, and no open repair finding.

Return the canonical task path and current epoch to the downstream optimization workflow. Require that workflow to acknowledge both before it records results.

Report an exact blocker or next action for any other outcome. Keep solution search, candidate implementation, experiments, and production changes outside this skill.

The frame is complete only when the downstream workflow can compare solutions without adding hidden semantics.
