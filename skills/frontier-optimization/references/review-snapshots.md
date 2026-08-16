# Frontier Project Snapshots

Load before freezing, reviewing, validating, adopting, or executing a reviewed project state. This file is the sole contract for immutable review inputs.

## Scope

A snapshot contains project facts only: project source, configuration, campaign state, candidate bytes, packets, authorization targets, evaluator configuration, and project-produced evidence. Workflow, Skill, validator, bundle, Slice 7, and workflow-test bytes are execution tools, not project evidence. They never appear in a project snapshot, Entry packet completion check, or B packet.

Historical copied snapshot directories remain audit records only. They transfer no answer, adoption, acknowledgment, execution, spend, result, or claim authority into a new Entry. Do not read, copy, map, convert, or migrate their `inputs/` trees when creating new authority.

## Filtered Git snapshot

Create one `frontier-project-snapshot/1` manifest per review attempt. Use `scripts/project_snapshot.py capture` with a temporary Git index. Capture the selected worktree bytes, including explicitly selected dirty tracked and untracked files, without changing the current branch, worktree, or ordinary index.

The filtered tree contains only explicitly selected project files and the complete members of declared closed project roots. It excludes `.agents/**`, `.codex/**`, `.git/**`, and every historical `*-snapshot/inputs/**` path before writing a Git object. A path containing `skills` is not excluded by name: canonical campaign records under the task path remain project facts.

Use the single ref `refs/frontier/project-snapshots/current`. Each new snapshot commit has the prior ref commit as its parent, and capture updates the ref atomically against the observed old value. Never create one branch per review and never leave an authority-bearing snapshot as an unreachable commit.

## Manifest and identity

```yaml
snapshot_id: project-snapshot-sha256:<canonical manifest SHA-256>
schema: frontier-project-snapshot/1
storage:
  commit: <Git commit used for storage and recovery>
  ref: refs/frontier/project-snapshots/current
  parent_commit: <prior snapshot commit or null>
members:
  - path: <canonical project-relative file path>
    mode: <100644 or 100755>
    size: <nonnegative byte count>
    file_sha256: <exact lowercase SHA-256>
closed_roots:
  - path: <canonical project-relative directory>
    members: [<complete relative member paths>]
external_artifacts:
  - locator: <stable project-relative content-addressed path>
    size: <nonnegative byte count>
    file_sha256: <exact lowercase SHA-256>
```

Compute `snapshot_id` from canonical JSON of the complete manifest with `snapshot_id` omitted. This SHA-256 is the only snapshot authority identity. Git commit and tree identities provide storage, deduplication, reachability, and recovery; they never replace `snapshot_id` in an authorization binding. The manifest is outside the commit it describes, which keeps the identity acyclic. A later snapshot may include an earlier manifest as an ordinary project record when the current decision needs it.

The review packet binds the manifest through exact `{path, snapshot_id, file_sha256}` fields. It does not contain `snapshot_root`, `snapshot_inputs`, copied source paths, workflow identities, or Git tree identities.

## Closed project roots

Use a closed root for every candidate, package source, or other directory whose complete membership affects behavior. Supply the exact expected member list before capture. Capture scans the real directory, including ignored files, and fails on a missing, extra, symbolic-link, nonregular, `__pycache__`, `.pyc`, or `.pyo` member. It adds the verified members with `git add --force` through the temporary index so `.gitignore` cannot hide bytes.

## Large project evidence

Keep large immutable evidence outside Git under a locator derived from its SHA-256, normally `artifacts/sha256/<first-two-digest-characters>/<full-digest>`. Publish through `scripts/project_snapshot.py publish-artifact`: write a temporary file on the destination filesystem, verify size and SHA-256, and atomically publish it. An existing identical object is reused; a conflicting object fails.

Every reference records `locator`, `size`, and `file_sha256`. Validation fails when the object is missing, unsafe, overwritten, truncated, or changed. A referenced object remains retained. Cleanup discovers live references by scanning current manifests; it needs no review-time database or per-B reference-count service. Backup policy is project operations, not Entry review.

## Validation and adoption

The reviewer reads frozen project members from the bound Git commit and reads large evidence from its content-addressed locator. Validation reproduces the manifest SHA-256, commit tree, member modes, sizes and SHA-256 values, external evidence, and ref reachability before interpretation.

Before adoption, compare every action-controlling live project file with its frozen project member. After an exact reviewed adoption, execution-start accepts only the complete reviewed post-state for listed transition paths and unchanged frozen bytes everywhere else. A partial transition, extra drift, missing Git object, unreachable commit, external evidence mismatch, or unreviewed path returns `REVIEW_REQUIRED` or `BLOCKED` before execution.

Apply [Finding effects](frontier-core.md#finding-effects) before expanding snapshot or review scope. Snapshot exact action-controlling project bytes and the typed projections that define authority. A stale narrative, redundant prose digest, or display timestamp does not become action-controlling merely because it appears in a project document. When the typed owner and its cited evidence agree, report that discrepancy as an advisory without copying, repairing, or reviewing another identity. A mismatch in an authority-bearing digest, deadline, transition time, or typed state remains blocking.

The first Entry under this contract is the new authority origin. Preserve earlier reviews as historical records, but do not transfer their user answers, adoption, acknowledgment, execution-start, spend, or result authority. An unchanged active B may keep its B identity and technical semantics, but it requires one fresh project snapshot and Entry review before authorization can be presented.

## Completion checks

An ordinary Entry completion check covers only the selected B, its project bindings, prerequisites, candidate or closed roots, evaluator, budget, scope, stop conditions, authorization target, result contract, project snapshot, and directly required project engineering checks. Workflow regression suites, Skill bundle checks, Slice 7, validator source checks, and repository-wide tests belong to workflow development or a B that explicitly changes the corresponding project surface; they are not repeated for every Entry.

Preserve each manifest, packet, and review artifact. Removing the legacy copied snapshot store is a separate cleanup action requiring explicit user authorization after every current authority path has moved to a verified project snapshot.
