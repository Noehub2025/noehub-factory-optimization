# Frontier Handoff and Recovery

Load for an explicit packaging request after closeout or a requested recovery.
[Provenance, Git, and retained artifacts](provenance-and-identity.md) owns storage,
large-file retention, scoped Generation restore, and existing-chain behavior.

## Preserve the outcome without another archive

The existing closeout record identifies the final Git version, retained
results, spend, objective gap, and next choices. It normally is the handoff.
A separate packaging request creates no campaign, authority, or spend.

When a machine-readable handoff is requested, use the current
`frontier_provenance_cli.py export-handoff` operation with the root ID,
node repository, existing content bindings, and destination. Save the small
node and reference records in an ordinary Git checkpoint first. The operation
writes only `handoff.json`, citing that commit and the records' repository
paths. Existing input versions and external artifacts stay where retained.

Use `verify-handoff` to read the exact records from Git. It also accepts old
portable handoffs as read-only history. New export never copies every input or
creates a dedicated snapshot commit. Workflow deployment files, environments,
caches, and unrelated work are not handoff members.

If the reference record is outside the repository, provide `repo_root` to
`verify-handoff`; the record stays portable and contains no machine-specific
repository path. On another machine this points to the restored Git repository.

Recovery needs the retained Git history and only the external artifacts needed
for the requested next action. A small reference is not proof that a large
payload is available. Restore a missing dependency at its owning location;
repeat no completed measurement or review solely to recreate storage.

## Resume or restore

An interrupted active campaign resumes from the same valid decision chain and
accounting. Restoring a requested Generation's working files uses ordinary
scoped Git operations and preserves evidence, spend, and unrelated work.
Neither operation creates a new Generation merely to accommodate storage.

Opening a new campaign after adopted closeout follows the Entry router and
applicable continuing grant or current request. Packaging alone is not that request.
For unchanged candidate reuse, retain the candidate's exact version, its
existing implementation evidence, and cumulative spend. Apply the existing
recovery Entry and applicability checks only to that new consequence; a Git
restore alone grants none. Historical version-1 recovery readers may verify
retained records, but do not initiate their old archive or migration workflow.

## Cleanup

Clean only on explicit request. Preserve cited sole copies and the Git refs
needed to retain their history. Ordinary scratch files and regenerable caches
need no immutable archive or per-file review. Report material deletion and
recoverability. Storage housekeeping cannot change scientific conclusions,
prior costs, or campaign authority.

## Workflow development checks

This section is the single source for workflow test selection. These checks apply only while developing or releasing the workflow. They remain outside campaigns, B packets, Entry snapshots, project reviews, and ordinary Entry completion checks.

Run `scripts/run_workflow_checks.py --mode fast` for a tight editing loop. It checks Git whitespace and validates the live bundle once. Run `scripts/run_workflow_checks.py --mode affected` after a coherent workflow change. The selector reads committed, staged, unstaged, and untracked Git paths, prints every selected test and reason, and runs only the owning contract tests. Project files do not select workflow regression tests. Git selects scope only; neither Git paths nor workflow bytes enter project identity, authority, or evidence.

Use `--base <revision>` when the check must include committed changes after a known base. Use `--dry-run` to inspect the deterministic plan without running it. The same paths and mode must produce the same plan. A new or unclassified workflow Python file escalates `affected` to the complete suite instead of being skipped. A cross-cutting contract such as Frontier Core, provenance and identity, or the source-module manifest does the same.

Before releasing the workflow bundle, run `scripts/run_workflow_checks.py --mode release` once against a stable candidate. Release mode runs the complete deterministic validator and Slice 7 test suite, reports the slowest tests, and validates the current twelve-Skill bundle. The bundle validator owns common Skill metadata, invocation policy, source closure, link, portability, and required-file checks; do not repeat an external per-Skill validator for the same properties. A deployment adapter may run its own packaging check, such as a Claude Code plugin check, but that check does not become project evidence or a second workflow regression policy.

For a workflow development review, provide the selector's printed paths, reasons, commands, and results. The reviewer accepts the selected tier unless an observed failure crosses another module seam, a changed workflow Python path is unclassified, or the candidate is being released. The mere existence of a broader suite is not a reason to require it. After a repair, rerun `affected`; run `release` only once after the candidate is stable.

Produce one source manifest and one fresh release review for the stable workflow bytes and fixtures. A later fix runs `affected` while iterating and replaces the release result only after one new `release` run. Preserve prior release artifacts as history; do not create per-Slice regression reviews or propagate them into project state. Do not copy workflow bytes into any project snapshot or ask a project reviewer to reproduce release checks.

`Depends on` records original dependency, `Regression triggered by` records the later change, `Rechecks` records conclusions covered again, and `Supersedes` applies only to an earlier attempt. The same immutable source and fixture manifests must produce the same package validation result.


## Behavioral checks

- Several records cite the same selected input without making another content
  copy or dedicated commit.
- A Git handoff survives later working edits and restores the same recorded
  decisions; it supplies no fresh authority.
- An active valid old chain remains usable without conversion or a new fee.
- Missing required external content stops only its dependent action.
- A scoped Generation restore keeps evidence, cumulative spend, and unrelated
  work intact.
