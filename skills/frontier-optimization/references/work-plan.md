# Frontier Work Plan

## Contents

- [Template](#template): W frontmatter plus Purpose, Scope, design, delivery, input, progress, validation, recovery, and outcome sections.

Load only when work needs W. This is the sole `WORK.md` template. Use one W across B records that share one design contract or operational outcome. W stays a short map; indexed concern files hold exact design contracts.

Increment `plan_revision` for a material change to purpose, scope, design profile, concern contract or identity, user design choice, delivery slice, input contract, traceability, validation, or definition of done. Every contract-bearing change invalidates the prior `DESIGN_READY` and every external development authorization bound to that design identity. Never store current development-authorization state in W; V, Selection, ledger, and Entry adoption own it.

## Template

```markdown
---
type: Frontier Work Plan
status: <proposed | active | completed | paused | blocked | superseded>
work_id: W001
plan_revision: <integer>
problem_epoch: <integer>
representation_revision: <integer>
affected_routes: [<T identifiers>]
affected_batches: [<B identifiers or none; lifecycle-only, never part of design delivery authority>]
design_profile: <module | system | not-applicable>
design_status: <not-required | drafting | review-pending | ready | repair-required | superseded>
design_contract_identity: <immutable identity of the design-contract sections and indexed concerns, pending, or not applicable>
design_review: <adopted DESIGN_READY path and identity, pending review path, or not applicable; lifecycle-only and never copied into a contract-bearing section>
input_state: <not-required | request-pending | waiting-for-input | received-unvalidated | accepted-as-evidence | rejected>
repository_structure_disposition: <existing-integrated | absent-awaiting-user | user-approved-new | not-applicable>
source_base_identity: <exact repository evidence snapshot used for design review, an exact source identity required by design meaning, or not applicable; not the later Entry execution source by default>
candidate_interface: <existing or user-approved seam, or not applicable>
generated: { by: frontier-optimization/1, at: "<ISO-8601 datetime>" }
---

# WORK: <work name>

## Purpose

<Coordinator: state the change, why the work exists, its campaign baseline role, and the usable artifact it must produce.>

## Scope

<Coordinator: name routes, semantic repository areas, source requirements and compatibility conditions, true interfaces, callers, dependencies, and excluded work. Keep future B assignments, attempt namespaces, worker paths, execution-frozen inputs, and internal review, evidence, recovery, or result destinations in Entry.>

## Current state

<Coordinator: state the adopted checkpoint, next action, blockers, stable artifacts, design-review state, candidate-code lifecycle state, first performance check, preparation budget limit, and required follow-up reserve. Keep current authorization in external lifecycle records.>

## Design brief

<Design implementation author: in plain language, state the design profile and reason, selected architecture shape, stable external seam, decisive user choices, open blockers, and replacement boundary. Keep detail in the indexed concern that owns it.>

## Design map

| Concern | Authoritative pointer and identity | Applies because | Read when | Status |
|---|---|---|---|---|
| <architecture, domain, interfaces, flows, decisions, or verification> | <exact path and section plus identity> | <profile trigger> | <specific review or B action> | <draft | current | blocked | not applicable with reason> |

<Coordinator: generate this map mechanically from the designer's exact concern paths, triggers, read conditions, and identities. Do not rewrite professional meaning. A concern absent from this map is outside the design contract. For non-code W, record one not-applicable row with the work kind.>

## User design decisions

<Coordinator: list user-owned design V records, the choice each controls, effective conditions, and reconsideration trigger. Link to the owning decision record rather than repeating alternatives and consequences.>

## Delivery map

| Slice | Observable delivery | Blocked by | Required design inputs | Check and recovery point |
|---|---|---|---|---|
| <stable technical name and exact verification section identity> | <one independently verifiable behavior or artifact> | <stable prerequisite slice or technical condition, or None> | <exact indexed pointers needed by an executor> | <distinguishing check and safe resume point> |

`design/verification.md` is the single source for each technical slice's observable behavior, stable prerequisites, required design inputs, oracle, failure checks, and recovery point. The Coordinator copies a concise summary plus exact technical pointers into this table without changing that meaning. Selection and Entry later bind one exact B and execution realization; their status and paths never enter this contract-bearing table.

Every selected B must cite this exact `plan_revision`, `design_contract_identity`, and stable slice identity. Reject a B that names a stale revision, a superseded concern identity, or design inputs outside its selected slice.

For `module` or `system`, the Coordinator maintains `design/traceability.yaml` as a contract-bearing machine-readable index. `design-implementation` does not write it:

```yaml
work_id: <W identifier>
plan_revision: <integer>
design_contract_identity: <identity, omitted when hashing this file>
slices:
  <stable technical slice name>:
    verification_pointer: <exact path, section, and immutable identity>
    delivery_identity: <exact Delivery row identity>
    required_design_inputs: [<exact concern pointers and identities>]
```

Add the normalized traceability-file hash to the design index and design identity. Entry binds the selected stable slice to one exact B, execution source, worker write surface, and internal output paths, then proves that those realization details satisfy the owning verification contract. A path belongs to Design only when a real caller or operator outside the current B or attempt depends on that exact path as a stable interface.

The `slices` shape is required for every new design identity, including a new revision of an older W. An exact design identity with an already adopted valid `DESIGN_READY` may retain its historical `batches` shape for audit under its original authority; it cannot receive a new `DESIGN_READY`, new B assignment, or broader path authority from that form.

## Human input contracts

| Input | Exact request and schema | Provenance and quality checks | Confidentiality and destination | Accept or reject condition | Resume event |
|---|---|---|---|---|---|
| <input identifier or not applicable> | <requested fields, types, units, allowed omissions, and response format> | <required source metadata, authenticity, completeness, consistency, legality, and domain checks> | <handling limits and stable response path> | <observable workflow validation rule> | <event that permits a new execution attempt> |

<Coordinator: create a row only when W owns human input. Supplied data is evidence after the workflow validates schema, provenance, and quality. It is not a technical conclusion, optimization result, or user value choice. Route a value choice through V.>

## Milestones and progress

<Batch worker: append bounded checkpoint observations from the assigned B packet.>

## Validation

<Coordinator: summarize lifecycle gates and point to the designer-owned verification sections. Name design review, engineering checks, interface and failure checks, compatibility and global checks, candidate-manifest validation, implementation review, baseline establishment, first performance check, comparison validity, and required evidence without adding technical requirements or copying their detailed contracts.>

State the design-review requirement generically here. Keep the current review identifier, packet path, snapshot path, and review result in frontmatter or other lifecycle records outside the design contract, so a replacement review does not change the contract it reviews.

## Definition of done

<Coordinator: state the exact observable campaign state required for completion, including current design review and user authorization when code-bearing work is involved, terminal delivery slices, artifacts, designer-owned technical oracles, immutable candidate identity, implementation review, baseline establishment, and handoff to the first performance check without consuming the required follow-up reserve. Point to professional requirements rather than rewriting them.>

## Decisions and discoveries

<Batch worker: append technical evidence, surprises, consequences, and suggested design changes. A suggestion changes no plan term or concern contract. The Coordinator opens and scopes an accepted contract-bearing revision; `design-implementation` updates professional design content, and the Coordinator regenerates only its mechanical bindings.>

## Recovery

<Coordinator: after checking the batch result, record exact commands, paths, prerequisites, and the safe next step from each adopted checkpoint.>

## Outcome

<Coordinator: after checking the batch result, record completed, blocked, superseded, or active work and stable artifact links.>
```

A route states why work may improve the objective. W maps design and delivery. B authorizes one slice, its inputs, and spend. Engineering completion does not prove optimization success.
