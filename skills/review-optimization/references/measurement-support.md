## Measurement-support branch

Use this branch for a remaining independent technical question under [Shared measurement-support gate](../../frame-optimization/references/measurement-work.md#shared-measurement-support-gate), not merely because an implementation makes Slot H or R8 executable.

Apply [Constrain effects, not convenient forms](../../frontier-optimization/references/technical-design.md#constrain-effects-not-convenient-forms) when an internal restriction excludes evidence needed by this verdict. Return the affected restriction to its owner rather than treating synthetic-only compliance as sufficient readiness.

Require the caller to supply one existing review-target path and one new review-record path under the selected task's `eval/` directory. The target belongs to `frame-optimization`; the review record belongs to `review-optimization`. The target must state:

- the next use, framing rule or open finding, applicable retained conclusions and the remaining question;
- the exact allowed file set;
- required behavior and failure cases relevant to that question;
- each focused check needed and authorized for this review;
- every consequential action excluded from the review; and
- a completion condition for the remaining question and intended use, combining new judgment with applicable retained conclusions rather than requiring another full implementation pass.

Return `BLOCKED` when either path escapes the selected task, the target is incomplete, the review path already exists, or the current authority does not cover an allowed check required for the verdict.

Read the current Slot H, R8 when present, the controlling finding, the target and applicable prior conclusions. Use the Git changes and affected dependencies to inspect implementation, tests and schemas needed for the remaining question. Reuse unchanged coverage when its bytes, assumptions and use still apply, regardless of review-kind label; otherwise inspect the affected gap. Include retained real evidence and dependency specifications needed for [Evidence at real boundaries](../../frontier-optimization/references/implementation-review.md#evidence-at-real-boundaries); synthetic agreement alone does not establish an external premise. Use Git to inspect the named files and their containment; do not stage, commit, switch, reset, or rewrite project files.

Run only the target's authorized focused checks. Formal measurement, new protected-input exposure, paid execution, external submission, or other protected effects belong to the execution owner, not this review. Reading retained outputs or inspecting a dependency is not a new experiment merely because it concerns a real system. A missing real observation returns to the existing implementation or measurement owner through the normal permitted path; the reviewer's exclusions do not forbid that owner from obtaining it. Do not turn every dependency into a mandatory live check.

Resolve the allowed project file set, distinguishing newly examined files from unchanged coverage reused by reference. Identify any required implementation outside that scope. Exclude Skill files, workflow source or release data, and transient user replies from the reviewed-byte manifest. Confirm the assigned behavior and relevant failure handling while preserving parent measurement meaning. Record the SHA-256 of newly reviewed implementation and test files and reference retained byte bindings for reused coverage; a reference-only change needs applicability checks, not repeated implementation tests.

Write the new review record with:

- `type: Optimization Measurement Support Review`;
- `status: stable` for `IMPLEMENTATION_READY`, otherwise `draft`;
- branch, task, target, reviewer, and review time;
- one result: `IMPLEMENTATION_READY`, `REPAIR_REQUIRED`, or `BLOCKED`;
- newly reviewed paths and SHA-256, plus references and applicability of reused coverage;
- performed focused checks and results, and applicable retained check results;
- findings with evidence, required action, and completion condition; and
- an authority statement that excludes durable containment and every consequential run.

Return `IMPLEMENTATION_READY` when new and retained evidence settles the assigned question for the named use, the relevant byte bindings and required check results are accounted for, and no required correction remains. State the covered conclusions and their limits; distinguish optional improvements from defects that obstruct this use. Return `REPAIR_REQUIRED` for an implementation defect affecting the required judgment. Return `BLOCKED` only for a missing capability, authority, input, or safe review path.

This branch writes only its new review record. It does not edit the implementation, core task documents, findings, logs, handoffs, or project identity. Its result grants no durable containment, baseline, evaluation, experiment, candidate, search, spend, remote, production, or claim authority.

The measurement-support branch is complete when its record contains one result for the assigned question, new and reused evidence references, required check results and any unresolved findings. It does not reopen unrelated readiness work.

## Output

For measurement support, return:

```text
RESULT: IMPLEMENTATION_READY | REPAIR_REQUIRED | BLOCKED
Task: <canonical task path>
Target: <canonical review-target path>
Review record: <canonical review-record path>
Reviewed bytes: <new path and SHA-256 entries; applicable retained bindings by reference>
Checks: <performed commands and results; applicable retained results by reference>
Findings: <omit for IMPLEMENTATION_READY>
- Evidence: <decisive evidence>
  Required action: <one action>
  Complete when: <checkable condition>
```
