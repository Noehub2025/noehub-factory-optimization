# Frontier Packaging and Durable Recovery

## Contents

- Preconditions
- Build one immutable handoff package
- Verify recovery without live context
- Optional cleanup
- Post-closeout candidate reuse
- Ten-Skill release and regression rule
- Acceptance scenarios

Load this stage only when the recorded-state router selects an explicit packaging request after a complete closeout. Packaging preserves evidence and makes recovery portable; it creates no campaign, spend, measurement, integration, incumbent, promotion, or claim authority.

For version 3 provenance, export every retained typed node and portable project
content root. Verify the exported chain and roots in a directory without
`.git`. Git commits and signed tags identify workflow releases separately;
they are never project handoff inputs. Missing objects, unexpected members, or
changed bytes block publication.

Use `frontier_provenance_cli.py` with `export-handoff` and then
`verify-handoff` for a version 3 root. That atomic writer includes every
reachable node and referenced raw object. `package_frontier_handoff.py` below is
the version 1 closeout packager and cannot package a new version 3 authority
chain.

## Preconditions

Require adopted `CLOSEOUT_COMPLETE`, a final outcome root, final Budget,
preserved direction state, no active worker, no unresolved claim branch, and no
unclassified retained project artifact. Packaging creates no campaign
generation, authority, Selection, or spend.

## Export one immutable project handoff

Use `frontier_provenance_cli.py` with `operation: export-handoff`. Supply the
exact outcome root, node repository, destination, and one verified content
binding for every reachable role-specific project root. The exporter requires
the binding set to equal the reachable roots exactly.

The handoff contains:

- the decision, attestation, authority, execution, and outcome nodes;
- `project-decision`, `review-report`, `project-authority`,
  `project-state`, and `project-outcome` content bundles;
- complete closed project collections and exact raw project bytes; and
- one canonical `handoff.json` whose identity covers the node and content
  inventory.

The handoff must not contain workflow release roots, workflow Skills,
validators, tests, source modules, copied workflow-source bindings, Git
metadata, environments, caches, credentials, or unrelated project files. A
workflow release may be recovered separately from its Git commit or verified
signed tag; it is not part of the project handoff.

Export stages beside the destination, verifies the complete project chain and
every content bundle, then publishes atomically. It never reuses or overwrites
an existing destination.

## Verify recovery without live context

Copy or mount only the finished handoff in a clean temporary directory without
repository `.git` data, conversation history, prior worktrees, caches, or
mutable source paths. Run `operation: verify-handoff`. Verification requires
canonical content paths, regular non-symbolic-link authority manifests, exact
node and file inventories, role-to-domain agreement, and reproducible content
roots.

The same handoff bytes must reproduce the same project root chain, route-set
state, progress and constraint limits, first applicable resolver row, exact
next action or blocker, final accounting, retained-result limits, and
reopening requirements. Missing project bytes are a recovery blocker. Missing
workflow implementation bytes are not, because they were never a project
identity input.

`package_frontier_handoff.py` is retained only as a version 1 audit and
exact-inventory completion reader. It cannot build a new handoff, add workflow
source to a current package, migrate old authority, or execute archived code.

## Optional cleanup

Perform cleanup only when the user explicitly requests it. Inventory every target first. Delete only an uncited cache, environment, duplicate, staging directory, or other reconstructible intermediate after the verified package contains all required bytes. Never delete canonical task records, frozen packets, execution baselines, terminal results, manifests, reviews, retained evidence, final handoff inputs, or the sole copy of a candidate.

Record what was removed, why it is reconstructible, and whether recovery is possible. Package validation must still pass afterward.

## Post-closeout candidate reuse

Candidate reuse is a separate Entry action selected only by an explicit current recovery request. Before writing a new-generation V, X, review packet, Entry snapshot, or `RECOVERY_CAMPAIGN_STARTED` event:

1. Build a temporary recovery preflight containing the prior closeout and final handoff identities, inherited Budget, requested candidate and manifest identities, candidate root, source generation, proposed next generation, `review_mode: recovery-reuse`, `candidate_mutation: prohibited`, and `new_proposal_attempts: 0`. Add `lineage_sources.closeout`, `.handoff`, and `.budget` as exact `{path, identity_field: null, identity, file_sha256}` bindings. Parse those source records and derive the closeout event, generation, status, unresolved claims, active workers, Budget ceiling, actual and unknown spend, and active reservations; copied summary fields cannot replace them. A current version 3 manifest and preflight contain no workflow-source identity. The validator accepts a version 2 workflow-source binding only through its exact historical compatibility path.
2. Run `scripts/validate_candidate_recovery.py` in draft mode against canonical repository artifacts. Derive member and package identities from bytes; never trust a conversation-copied digest.
3. If draft validation fails, return `BLOCKED` with the exact path, requested identity, and recomputed identity. Write no new-generation artifact and spend nothing.
4. If it passes, insert only the computed preflight identity, freeze the preflight at a new stable path, and reproduce finding-free frozen validation.
5. Bind the frozen recovery preflight in the new V, X, Entry snapshot, implementation snapshot, and fresh `review_mode: recovery-reuse` review.

An identity mismatch never authorizes normalization, copying, regeneration, or repair. Any candidate-byte or behavior change leaves recovery reuse and requires a new code-bearing B, current development authorization, candidate identity, and proposal charge.

## Workflow release check

This check applies only while developing or releasing the workflow. It is outside campaigns, B packets, Entry snapshots, and ordinary Entry completion checks. Before releasing the workflow bundle, run every deterministic validator test, the end-to-end Slice 7 suite, `scripts/validate_frontier_skill_bundle.py`, and Skill `quick_validate.py` for exactly the five framing Skills and five Frontier Skills. Require `frame-optimization` and `frontier-optimization` to be explicit user-invoked Coordinators, require their eight workers to permit implicit invocation, and require both Coordinators to use the same framing-to-Frontier handoff. Reject an eleventh Skill, a separate claims reviewer, unresolved internal link, host-specific absolute path, missing required script, changed invocation policy, or unmanifested source file.

Produce one source manifest and one fresh release review for the current workflow bytes and fixtures. Do not copy those bytes into any project snapshot or ask a project reviewer to reproduce this release check.

When a later workflow change affects a shared contract or validator, rerun the current release suite and replace the prior release review with one new current review record. Preserve prior review artifacts as history; do not create per-Slice regression reviews or propagate them into project state.

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
| Handoff spans several project decisions | Every object retains only its typed project roots and parent chain; every workflow, validator, worker-interface, deployment, and release identity remains absent. |

Slice 7 passes only when package publication is atomic and authority-neutral, exact candidate recovery fails before mutation on any identity mismatch, a portable package contains every project byte it claims to carry, and the ten-Skill workflow bundle validates. This release result is never a project-strength or Entry-readiness claim.
