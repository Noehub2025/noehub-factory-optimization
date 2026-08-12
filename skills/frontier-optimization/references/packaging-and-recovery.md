# Frontier Packaging and Durable Recovery

## Contents

- Preconditions
- Build one immutable handoff package
- Verify recovery without live context
- Optional cleanup
- Post-closeout candidate reuse
- Five-Skill release and regression rule
- Acceptance scenarios

Load this stage only when the recorded-state router selects an explicit packaging request after a complete closeout. Packaging preserves evidence and makes recovery portable; it creates no campaign, spend, measurement, integration, incumbent, promotion, or claim authority.

## Preconditions

Require an adopted `CLOSEOUT_COMPLETE`, a complete final handoff, final Budget, no active worker, no unresolved C branch, and no unclassified retained artifact. Resolve the highest campaign generation and exact stopped or halted status from persisted records. A packaging request does not qualify as a post-closeout recovery request and must not increment `campaign_generation`.

Return `BLOCKED` when closeout, accounting, claim disposition, retained-result limits, or artifact classification is incomplete. Do not repair campaign history during packaging.

## Build one immutable handoff package

Create a package plan outside the final package root. Bind:

- campaign generation and stopped or halted status;
- closeout, final handoff, and final Budget identities;
- every retained candidate, manifest, result, E, D, X, C, A, review, Outcome Reflection, design contract, authorization, packet lifecycle, execution-baseline snapshot, engineering artifact, measurement artifact, and recovery instruction required by the final handoff;
- each source path, `file | subtree` scope, exact content identity, package destination, and evidence role;
- explicit exclusions for credentials, private input not authorized for retention, version-control metadata, environments, caches, and reconstructible intermediates; and
- `authority_effect: none`.

Run `scripts/package_frontier_handoff.py validate` in draft mode before freezing the plan. Insert only its computed `package_id`, freeze the plan, and require finding-free frozen validation. A source identity mismatch, missing byte, path escape, forbidden cache or version-control path, duplicate destination, or changed closeout binding blocks publication.

Run `scripts/package_frontier_handoff.py build` only on the frozen plan. The tool must stage under the destination filesystem, copy exact bytes, write the frozen plan and content manifest, verify the complete file set and every hash, and publish the content-addressed directory atomically. Never reuse or overwrite an existing package root.

Append the package identity and path to `log.md` only after verification. Preserve `campaign_status`, final Budget, Selection, retained results, gap, and all authority dispositions unchanged.

## Verify recovery without live context

Copy or mount only the finished package in a clean temporary directory without repository `.git` data, conversation history, prior worktrees, caches, or mutable source paths. Verify the package manifest and reconstruct:

- the exact closeout reason, campaign generation, final accounting, and authority disposition;
- every retained result and its evidence limit;
- each candidate identity and the bytes needed for audit;
- unresolved gaps, unknown spend, missing measurement, and prohibited claims; and
- the exact prerequisite for a future campaign or recovery request.

The same package bytes must produce the same handoff and next router result. A package may say that an explicit new recovery request is eligible; it must not open that campaign or infer permission from the packaging request.

## Optional cleanup

Perform cleanup only when the user explicitly requests it. Inventory every target first. Delete only an uncited cache, environment, duplicate, staging directory, or other reconstructible intermediate after the verified package contains all required bytes. Never delete canonical task records, frozen packets, execution baselines, terminal results, manifests, reviews, retained evidence, final handoff inputs, or the sole copy of a candidate.

Record what was removed, why it is reconstructible, and whether recovery is possible. Package validation must still pass afterward.

## Post-closeout candidate reuse

Candidate reuse is a separate Entry action selected only by an explicit current recovery request. Before writing a new-generation V, X, review packet, Entry snapshot, or `RECOVERY_CAMPAIGN_STARTED` event:

1. Build a temporary recovery preflight containing the prior closeout and final handoff identities, inherited Budget, requested candidate and manifest identities, candidate root, source generation, proposed next generation, `review_mode: recovery-reuse`, `candidate_mutation: prohibited`, and `new_proposal_attempts: 0`.
2. Run `scripts/validate_candidate_recovery.py` in draft mode against canonical repository artifacts. Derive member and package identities from bytes; never trust a conversation-copied digest.
3. If draft validation fails, return `BLOCKED` with the exact path, requested identity, and recomputed identity. Write no new-generation artifact and spend nothing.
4. If it passes, insert only the computed preflight identity, freeze the preflight at a new stable path, and reproduce finding-free frozen validation.
5. Bind the frozen recovery preflight in the new V, X, Entry snapshot, implementation snapshot, and fresh `review_mode: recovery-reuse` review.

An identity mismatch never authorizes normalization, copying, regeneration, or repair. Any candidate-byte or behavior change leaves recovery reuse and requires a new code-bearing B, current development authorization, candidate identity, and proposal charge.

## Five-Skill release and regression rule

Before releasing the workflow bundle, run every deterministic validator test, the end-to-end Slice 7 suite, `scripts/validate_frontier_skill_bundle.py`, and Skill `quick_validate.py` for exactly `frontier-optimization`, `research-frontier`, `grill-frontier`, `run-frontier-batch`, and `review-frontier`. Reject a sixth claims reviewer, unresolved internal link, host-specific absolute path, missing required script, changed invocation policy, or unmanifested source file.

Freeze one content manifest for the reviewed source, exact spec bindings, immutable fixtures, and produced validation artifacts. A source-control commit alone is insufficient when the worktree contains reviewed bytes outside that commit.

When a later Slice changes a shared template, packet or result schema, router, authority rule, identity rule, validator, or review contract, append an impact analysis naming every earlier Slice review. Mark each affected review `regression-required` for the new source snapshot before using it as release authority. Append a fresh regression review over the new source and fixture manifests. List an unaffected review only with a concrete compatibility reason. Preserve every historical PASS as true only for its bound source snapshot; never edit it to imply current applicability.

Use this review record shape:

```markdown
## <review ID>: <Slice and scope>

- Source snapshot: <content manifest and identity>
- Spec bindings: <exact spec paths and identities>
- Fixture snapshot: <immutable fixture manifest and identity>
- Artifact manifest: <exact paths and identities>
- Review packet: <path and identity>
- Reviewer context: <fresh context identity and isolation evidence>
- Result: <PASS | CHANGES_REQUIRED>
- Blocking findings: <findings or None>
- Checks performed: <checks>
- Depends on: <exact earlier review identities or None>
- Regression triggered by: <later change identity or None>
- Rechecks: <affected review identities or None>
- Supersedes: <earlier attempt or None>
- Current applicability: <current | regression-required | historical>
- Consequence: <next Slice or release permitted or blocked>
```

`Depends on` records original dependency, `Regression triggered by` records the later change, `Rechecks` records conclusions covered again, and `Supersedes` applies only to an earlier attempt. The same immutable source and fixture manifests must produce the same package validation result.

## Acceptance scenarios

| Scenario | Required durable outcome |
|---|---|
| Valid closeout package | Exact bytes are copied once, the content-addressed package verifies without live repository state, and campaign authority remains closed. |
| Source byte changes after plan validation | Frozen validation or build fails; no final package root is published. |
| Package includes `.git`, an environment, cache, path escape, or duplicate destination | Plan validation fails before publication. |
| Correct exact candidate recovery request | Candidate and manifest identities recompute, new generation uses new identifiers and inherited spend, and fresh recovery Entry plus implementation review remain mandatory. |
| Requested candidate or manifest digest is wrong | Validation returns `BLOCKED` before generation creation, V, X, review, Selection, reservation, or spend. |
| Candidate byte changes during recovery validation | Zero-cost reuse ends; no old review, B, or authorization transfers. |
| Context is compacted after acknowledgment, execution-start, result, closeout, or package publication | A fresh Coordinator reconstructs the same next action or blocker from stable artifacts only. |

Slice 7 passes only when package publication is atomic and authority-neutral, exact candidate recovery fails before mutation on any identity mismatch, fresh-context reconstruction needs neither conversation nor Git history, the five-Skill bundle validates, and every affected earlier Slice contract has current regression coverage.
