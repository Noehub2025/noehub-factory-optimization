# Provenance and identity

This contract is task- and technology-neutral. It applies to code, research,
experiments, human input, external actions, documents, data work, model work,
hardware work, and mixed batches.

## Boundary

Project provenance answers which project bytes, decisions, reviews, authority,
starting state, outcomes, and live facts support one consequence. Workflow
release provenance answers which Skill, validator, implementation, and test
bytes make up a workflow release. These are separate identity systems.

A new project object must not contain or reference workflow source files,
workflow snapshots, Skill bytes, validator implementation digests, release
roots, source-module roots, or a copied workflow-source binding. It names only
its project role, immediate project parents, and exact project content root.
Workflow source, release version, semantic or validator contract, deployment
path, installation time, and worker version are never project identity inputs.
Updating the workflow during repository work changes no project node,
authority, review, Selection, spend gate, or handoff identity and requires no
project migration or recomputation.

Git already provides content-addressed workflow release provenance. A release
record may name a full commit object identifier or verified signed tag. That
release locator stays in release records and never enters a project identity.

## Typed project graph

New objects use `frontier-provenance-node/4` and these roles:

```text
decision -> attestation -> authority -> execution -> outcome
```

An attestation has one subject parent. An authority has exactly one decision
parent and one finding-free ready attestation for that decision. An execution
has exactly one authority parent. An outcome has exactly one execution parent.
Missing nodes, wrong parent roles, duplicate edges, cycles, and replay against
another decision fail closed.

Decision, authority, execution, and outcome payloads are empty. Their role,
parents, and project content root already provide the complete identity input.
An attestation payload has a closed schema for subject, verdict, findings,
freshness, timestamps, and invalidation facts; it contains no validator or
workflow identifier. Each node has exactly one role-specific content root.

Use the typed interface in `scripts/frontier_provenance/`:
`freeze_decision`, `attest`, `bind_authority`, `freeze_execution`,
`record_outcome`, `verify_for`, `export_chain`, and
`NodeRepository`. Use `scripts/frontier_provenance_cli.py` for a durable
JSON command boundary. It has no generic payload or parent-link operation.

Prepare every new reviewed decision through
`scripts/frontier_review/preparation.py` or `scripts/frontier_review_cli.py`.
Its single interface validates mutable project drafts before identity allocation
and atomically publishes one complete review subject. Low-level capture and
freeze operations are provenance primitives, not an alternative review writer.

## Typed content roots

`frontier-content-root-sha256/2` hashes canonical JSON containing one content
domain, sorted logical artifact entries, and closed collection membership.
Each entry binds its logical name, kind, behavior-changing metadata, exact byte
length, and raw-byte SHA-256.

Project roles require these domains:

| Node role | Required content domain |
|---|---|
| decision | `project-decision` |
| attestation | `review-report` |
| authority | `project-authority` |
| execution | `project-state` |
| outcome | `project-outcome` |

Live receipts use `live-receipt`. Workflow publication uses
`workflow-release`, which is forbidden in every project role and portable
project handoff. One content root cannot satisfy two project roles.

Project capture uses `ProjectPortableStore` and supplies a role, not a caller-
selected domain. The role fixes both the domain and its logical-name namespace:
`project/decision/`, `project/review/`, `project/authority/`,
`project/state/`, `project/outcome/`, or `receipts/`. Release capture uses the
separate `release/` namespace. Project capture rejects the explicit `.agents`
and `.codex` workflow namespaces in logical names. It also receives an explicit
`project_root`, requires every source to be inside that root, and rejects only
the root-relative workflow deployment trees: `.agents/skills/`,
`.codex/skills/`, and Claude Code's `.claude/skills/`, `.claude/commands/`, and
`.claude/agents/`. Nested copies of those exact roots are also release-only;
other `.claude/` project data remains eligible. Ancestor directory names
outside `project_root` have no effect. `project_root` is a
capture-time boundary and is not stored or hashed. The policy does not infer
identity from generic task or technology names such as `skills` or `validator`.
Portable verification reapplies the manifest policy.

Project artifact metadata is closed and may contain only the executable bit.
Opaque nested source bindings, release locators, or implementation digests are
invalid. Live receipts bind the fact name, status, observation time, expiry,
and raw evidence. Workflow-release metadata may additionally name a release
source module.

A closed collection includes its complete sorted member set. Capture rejects
missing, extra, symbolic-link, and nonregular members. The portable adapter
rejects symbolic links and unexpected members at every authority manifest.
`WorkflowReleaseGitStore` hashes raw release bytes without clean filters,
writes a dedicated reachable commit, and verifies each release blob against
the release content root. It cannot capture a project domain. Project content
uses the portable raw-byte store so a project handoff never depends on Git.

Every new reviewed decision root contains one generated
`project/decision/review-subject-index.json`. The index uses
`frontier-review-subject/2`, declares `subject_mode: complete`, and reproduces
the manifest's complete member and closed-collection sets. It also carries the
`frontier-review-role-adapter/2` result and its derived review-kind semantic
projection so a reviewer can see exactly what consequence the subject controls.
Portable verification reruns that adapter against the raw members and rejects
unknown role contracts, correction or supplement namespaces, external-base
composition fields, and projection disagreement. The index is an ordinary
member of the content root, not a second identity or a workflow binding.

`bind_authority` requires the verified decision content as an input and rejects
a missing or incomplete subject index. The durable CLI therefore requires the
decision bundle in `content_bindings` when binding new authority. Existing
nodes remain byte-identical and auditable; this rule prevents an old partial
decision or a new supplement from creating another authority.

Consequence verification repeats the same boundary. Before acknowledgment,
execution, spend, external action, or outcome publication, `verify_for` resolves
the decision ancestor and requires its portable bundle to rerun a complete role
adapter. A manually assembled authority or descendant cannot make a historical,
partial, or supplement-only decision actionable.

## Static and live verification

`frontier-consequence-gates/2` defines the allowed root role and required live
facts for each consequence. Unknown consequences fail closed. Acknowledgment
is static-only: it verifies the complete immutable decision, attestation, and
authority chain with empty live facts and does not evaluate live-attestation
freshness. Each fact required by an action-taking consequence must resolve
through a verified `live-receipt`; the check time must be on or after
observation and on or before expiry. A bare boolean or unrelated content root
is not evidence.

An immutable attestation has no observation time, expiry, or invalidation rule.
A live attestation records its observation time and invalidating facts. Every
consequence other than acknowledgment requires its observation not to be in
the future and applies its expiry and invalidation facts. Every finding contains
only a code and one `block`, `repair`, or `advisory` effect. A ready attestation
cannot contain block or repair findings.

## Workflow release validation

`references/source-modules.yaml` and
`scripts/frontier_provenance/source_modules.py` are release-only facilities.
They validate the workflow source inventory, transitive local imports, dynamic
validator loads, Skill files, and release tests before publication or
installation. They are not exported by the project provenance facade and no
project caller may import or invoke them.

A workflow release byte change changes only its release root. Even a workflow
semantic change has no automatic project consequence. The currently installed
workflow reads the existing project evidence and may create a new project
decision only when ordinary project facts, authority, or user intent require
one; the release change itself never does. A resolver result already persisted
in Selection is a project decision and is never recomputed under a later
workflow. Later-spend checks validate its cited project facts and gates rather
than rerunning the resolver implementation.

## Portable project recovery

`export-handoff` exports only the reachable project nodes and their five typed
project content domains. `verify-handoff` reproduces the chain offline,
requires canonical content paths, rejects symbolic links and unexpected files,
and fails if any workflow-release root is present. A project handoff does not
package workflow Skills, validators, tests, or source modules.

For a routine-local execution, the execution's `project-state` root contains the late materialization and implementation-review node bytes and proofs required by [Evaluation protocol reuse](evaluation-protocol.md#routine-project-state-closure-and-recovery). `verify-handoff` validates that closure and rebuilds the non-authoritative `slot_id -> execution_root` mapping. A naked node or content reference that is neither graph-reachable nor embedded in that closure fails recovery.

## Historical audit compatibility

Version 4 is the only writer for new project provenance nodes. Historical
version 1 objects remain byte-identical and readable only through audit tools.
They cannot enter a current Entry, review, authority, execution, result
adoption, recovery action, or project handoff. Before installing the current
runtime, close or explicitly migrate every active authority or execution that
still depends on an older contract; do not keep parallel runtime interfaces.

Within version 4, the historical review-subject `/1`, role-adapter `/1`, batch-plan `/2`, and result `/1` combination is audit-only. Current Entry writing and runtime use review-subject `/2`, role-adapter `/2`, batch-plan `/3`, evaluation-target `/2`, and result `/2`. Historical and mixed combinations cannot create review consequences, authority, execution, or result adoption.
