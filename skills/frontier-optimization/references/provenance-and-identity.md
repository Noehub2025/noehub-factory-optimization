# Provenance, Git, and retained artifacts

This is the single storage and verification contract for project work. It
applies to research, documents, data, models, software, experiments, physical
work, and mixed batches. The project requires Git. Workflow deployment remains
separate from the project history it helps manage.

## Problems this contract addresses

| Problem | Required behavior |
|---|---|
| P1: parallel no-Git storage | Git is the project version history; old stores are read-only compatibility inputs. |
| P2: another complete archive at every node | Cite existing versions. A review, acknowledgment, or result does not require another copy or snapshot commit. |
| P3: repeated verification | Separate saved-content integrity, review applicability, and current action facts. Reuse reads inside one operation. |
| P4: normal edits treated as frozen-input drift | Working material remains mutable in the same B. A review remains about its exact saved version. |
| P5: unclear Generation rollback | Record the starting Git version and affected scope in the existing campaign record. Restore only the requested working scope. |
| P6: whole-repository identity | Bind selected project inputs, not the commit's entire tree or installed workflow. |
| P7: storage upgrades force process recovery | Continue valid active chains through the same entrypoint without changing their identities or charging again. |
| P8: large-file duplication or unrecoverable pointers | Retain needed payloads once in an existing store or local directory and cite them; verify availability when needed. |

## Normal project work

Use ordinary branches, commits, diffs, and, when isolation helps, worktrees.
Keep a coherent body of working material through edit, test, observation, and
repair. A normal local iteration creates no proposal identity and consumes no
proposal merely because files changed. Existing parent-owned exposure and
resource limits still apply.

Save a normal project checkpoint when a version must become a fixed review
input, published result, or recovery point. Reuse that commit wherever the
same files are needed. A checkpoint may cover several records. Do not create
dedicated snapshot commits, branches, full-file packages, or commit requirements
for acknowledgment, each check, each slice, or each read. If a fixed input has
not been saved, save the relevant work normally; this is not a new review,
authorization, B, or Generation.

Keep referenced commits reachable from retained ordinary branches or tags.
Git garbage collection and backup are repository operations, not campaign
reviews. A local branch is sufficient for local work; a remote push, signed
tag, or new hosting service is not a prerequisite. Git retention is not an
off-machine backup. Retain old branches or tags before removing the last
reference to history still needed by the campaign.

## Selected input references

The current writer is `GitReferenceStore` in
`scripts/frontier_provenance/git_content.py`. The existing
`ProjectPortableStore.capture` and CLI `capture-project` entrypoints delegate
to it; they no longer write portable project bundles. Supply the project root,
role, and selected files. The writer reads an existing commit and writes only a
small `manifest.json` with `storage.adapter: git-reference/1`, a full commit
identifier, and exact repository-relative paths. It does not commit, stage,
alter refs, or copy input files. Unsaved differences in selected inputs cannot
silently be replaced with HEAD's older bytes.

Git locates the content; it does not define permission or expand review scope.
`frontier-content-root-sha256/2` continues to bind selected logical names,
kinds, executable modes, byte lengths, hashes, and closed collection membership.
Storage paths and commit locators are not hashed into that content root.
Unrelated changes in a later commit do not change unchanged selected inputs.
A closed collection means all behavior-relevant members of that selected
collection, not all files in the repository.

Workflow source, Skills, validators, release identifiers, deployment paths, and
worker versions are outside project identity. This includes nested deployments
at `.agents/skills/`, `.codex/skills/`, and Claude Code's
`.claude/skills/`, `.claude/commands/`, and `.claude/agents/`.
Other project data is not excluded merely because its name contains
`skills`, `validator`, or `.claude`. A workflow can change during project
work without invalidating a review, authorization, candidate, or saved result.

## Historical typed decision relationships

The existing `frontier-provenance-node/4` graph remains a read-only compatibility model for records that already use it:

```text
decision -> attestation -> authority -> execution -> outcome
```

Do not create execution or outcome nodes for a current `frontier-batch/1` B. The current Batch cites R and V, uses Git for exact selected bytes, and records Attempts and actual Consequences directly. Historical nodes still answer which decision, review, permission, starting state, and result supported their original consequence. They reference content; they do not duplicate the ancestor's files.

| Role | Content domain | Logical namespace |
|---|---|---|
| decision | `project-decision` | `project/decision/` |
| attestation | `review-report` | `project/review/` |
| authority | `project-authority` | `project/authority/` |
| execution | `project-state` | `project/state/` |
| outcome | `project-outcome` | `project/outcome/` |

### Historical execution-state authority

For an existing historical chain, `project/state/execution-state.yaml` binds one pre-release starting state to
its exact decision, authority, plan, acknowledgment, and input-resolution
method. It is execution content, not an authority node or a live-fact source.
Its `worker_may_start: false` never releases work. The authority node defines
permitted consequences; consequence-gate receipts establish current Budget,
reservation, inputs, resources, and prior effects; a finding-free
`execution-start` performs the release.

Use one complete input form. A retained-decision state is identified by its
flat decision-content, plan and acknowledgment identities. The acknowledgment's
exact decision-content binding selects the reviewed manifest; that manifest is
the only authority for the retained Git location and project paths. Do not
repeat those locators in a new execution state. Historical
`retained_input_source` content remains preserved but has no effect on form,
permission or input identity.

A retained-decision state resolves every frozen input from that exact reviewed
decision and cannot carry sealed runtime input or a delegated design revision.
A baseline state is identified by its nested plan and acknowledgment bindings
plus logical frozen-input members; use it when execution must add either of
those inputs or another input not fully resolvable from the reviewed decision.
Both forms may use `git-reference/1`; a logical
`project/state/frozen-inputs/` member is not a second physical copy of the
project file. Do not mix the authoritative forms.

`release_condition`, retained-input `note`, and a historical
`resource_envelope` are nonauthoritative descriptions. Preserve their original
bytes, but do not derive permission, current facts, or input identity from
their wording. New states need not repeat those descriptions. A reader update
validates exact structured parents and input bytes without requiring historical
records to adopt later prose or metadata.

Live receipts use `live-receipt` under `receipts/`. Workflow releases use
`workflow-release`, never a project role. The release-only source module
inventory and tests remain outside project operations.

Prepare a new reviewed decision through `prepare_review` or
`frontier_review_cli.py`. It checks the mutable draft and derives the semantic
projection once, before publishing the review subject. Its generated
`frontier-review-subject/2` index is small record metadata stored in the
reference manifest; other members remain Git references. Keep the complete
required subject rather than a base-plus-corrections overlay. Low-level capture
does not replace review preparation.

## Verify at the relevant consequence

1. **Saved content:** resolve the selected commit and paths, or an existing
   historical bundle, and verify the requested content. Use one
   `ContentSession` for a command's resolver and reader. Reuse those bytes
   within that operation; there is no persistent validation cache.
2. **Meaning:** preparation derives the subject's semantics; independent
   review judges them. Later use checks the exact reviewed version and whether
   its assumptions still apply. Merely opening an unchanged record does not
   rerun the role adapter or independent review.
3. **Current action:** immediately before taking a consequence, check only its
   current authority, resources, reservation, required inputs, and prior
   effects. An immutable review cannot answer these live questions.

In a historical chain, acknowledgment remains static and grants no execution. The existing
`frontier-consequence-gates/2` owns live facts, expiry, and limits at execution
and later consequence boundaries. Reusing a static read does not cache live
permission or reset spend.

For a historical retained-decision state, the existing `freeze-execution`
operation verifies the acknowledgment's exact reviewed manifest and every Plan
frozen input before it creates the execution node. Result publication repeats
the same pure verification. This is one check at two existing consequence
boundaries, not a new preflight, receipt, review or persistent gate.

For an execution that reads directly from a retained Git version, later edits
to the working copy are not input drift. If a tool must read mutable paths,
compare the actual declared input files at its consumption boundary or use an
isolated working materialization. Check again when a declared input may have
changed; do not repeatedly scan the whole repository. Git status and diff help
identify changed paths, but cannot alone prove ignored or external inputs.
Work outputs, ordinary caches, progress notes, and unrelated user work do not
become frozen inputs merely because they coexist with them.

Keep a review valid for its original bytes. Apply it to changed work only after
the relevant changed dependencies have been addressed. Storage changes alone
require no new Entry, reviewer, authorization, candidate, or fee.

## Large files and external artifacts

Use Git for source, small records, configurations, and compact evidence.
For large data, weights, traces, media, or outputs, use the project's existing
artifact store, Git LFS when already suitable, or an ordinary retained local
directory. No new service, upload, LFS installation, or universal size threshold
is required. Choose from actual size, change frequency, access, and recovery
needs.

Keep a small versioned reference with a stable locator, exact version or
checksum, size, and purpose. An existing object version can be reused; a local
directory is enough if the required bytes are retained there. Reuse one
reference from many B, review, and Generation records. Routine references do
not hash or download the payload again.

A Git LFS pointer proves the pointer's version, not payload availability.
Before an action actually consumes an external payload, resolve its exact
version and verify it using the store's content guarantee or the existing
checksum. `verify-artifact` in the provenance CLI performs a streaming size
and SHA-256 check of one required local file. A missing or changed payload
blocks only the action needing it, not unrelated planning or research. Do not
silently replace a missing version with the newest available one.

Retain objects necessary to reproduce accepted evidence or resume retained
work. Regenerable caches and incidental scratch outputs need not become
immutable artifacts. No per-file retention review or new registry is required;
use existing records and project backup policy. A referenced sole copy is not
a cleanup target. Deletion still needs the user's authorization.

“Retain once” removes duplicate archives at each workflow node. It does not
forbid working copies, caches, backups, a clone, or a tool's necessary temporary
materialization, and it promises no physical zero-copy storage.

## Generation history, restore, and handoff

At Generation opening, put the starting commit and intended working scope in
the existing campaign record. At closeout, record the ending or retained
version, outcome, remaining objective gap, and usable next choices. Use
`git diff <start> <end> -- <scope>` to see the substantive change.

When the user asks to restore a Generation's working result, inspect pending
changes and preserve unrelated work first. Use an ordinary scoped restore or a
revert as appropriate. Restore the requested work, not the evidence, reviews,
budget ledger, or other actors' changes. Restoring bytes cannot undo consumed
resources, external effects, or a closed campaign. Resuming unchanged active
work and opening a new campaign after closeout remain different decisions.
There is no workflow-specific rollback engine.

The final handoff is normally the existing closing record plus Git versions
and retained artifact references. An explicit `export-handoff` request writes
only a small Git-reference `handoff.json`; it cites checkpointed node and
content-reference paths. `verify-handoff` reads those records from Git and
checks the required chain. It does not copy all project bytes or require a
Git-free recovery directory. On another machine, obtain the Git history and
the external artifacts needed for the requested action.

## Existing records

Keep valid active typed chains and their IDs, reviews, answers, budget, and
results unchanged. The same current reader accepts `git-reference/1` and
existing `portable-bundle/1` content. The old bundle is read in place; new
records use Git references. Storage adoption does not require bulk conversion,
an artificial closeout, or a fresh authority chain. Earlier semantic contracts
that were already audit-only remain audit-only: a storage update neither
revokes valid authority nor revives invalid authority.

Historical handoff and snapshot readers remain for retained evidence. Their
old archive-writing instructions are not a second current workflow. When a
historical dependency is genuinely missing, recover that object; do not
reconstruct the entire campaign or charge its candidate again.
