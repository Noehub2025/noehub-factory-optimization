# Representation documents — format and lifecycle rules

Read this reference completely before creating or editing representation-stage task documents. It defines the shared `REPRESENTATION.md` template, authority, revision, invalidation, review, continuity, and handoff rules.

## Contents

- Task layout
- `REPRESENTATION.md` template
- Frontmatter and row status
- Authority boundary
- Detail and module documents
- Representation review record
- Revision and search-state compatibility
- Invalidation
- Continuity and recovery
- Review outcomes and handoff

## Task layout

Use the caller-selected task under `docs/skills/optimization/<task-slug>/`. Apply the path and slug validation in [task-documents.md](task-documents.md).

```text
docs/skills/optimization/<task-slug>/
├── PROBLEM.md
├── REPRESENTATION.md
├── log.md
├── review.md
├── representation-review.md
├── terms.md
├── slots/
├── representation/
├── modules/
└── eval/
```

`PROBLEM.md` must exist before `REPRESENTATION.md`. Do not create a second core representation file or a separate state directory.

Only `PROBLEM.md` and `REPRESENTATION.md` are default representation-stage context. Create optional documents only when their content is necessary.

## `REPRESENTATION.md` template

Keep the body to one title, one R1-R8 table, one status key, and one authority and revision rule block. The body has at most 40 nonblank lines. Each Contract cell has at most two sentences, and each sentence has at most 25 words.

```markdown
---
type: Optimization Representation
title: <effort name> representation and decomposition
description: Defines candidate encodings, moves, modules, and search-state compatibility for <effort name>.
tags: [optimization, representation, decomposition]
status: draft
problem: PROBLEM.md
problem_epoch: <positive integer copied from PROBLEM.md>
problem_generated_at: "<PROBLEM.md generated.at>"
representation_revision: 1
updated: <ISO-8601 date>
generated: { by: frame-optimization/1, at: "<ISO-8601 datetime>" }
---

# REPRESENTATION: <effort name>

| # | Item | St | Contract | Detail |
|---|---|---|---|---|
| R1 | Working forms | O | Name the canonical evaluation form, active search forms, translations, searched subset, and coverage limit. | |
| R2 | Redundancy | O | Record redundancy as known, absent, or Unknown. Define its search effect, next action, or claim limit. | |
| R3 | Scale behavior | O | Map each material Slot A scale variable to encoding size, operation cost, neighborhood growth, and module structure. | |
| R4 | Moves and legality | O | Define operations, legality modes, neighborhoods, and reachability. Name the action or claim limit for every unknown. | |
| R5 | Modules | O | Define module-owned and shared decisions, local alternatives, resource partitions, and the practical reason for each boundary. | |
| R6 | Interfaces | O | Define active interfaces, invariants, failure behavior, composition, and translation to the evaluation representation. | |
| R7 | Coupling | O | Record material objective, constraint, resource, and information coupling. Define coordination, global evaluation, or a claim limit. | |
| R8 | Validation and state | O | Identify the harness, baseline, starting set, budget, validation limits, and retained search-state dispositions. | |

St: `P` = pinned; `~` = provisional; `O` = open; `-` = not applicable.

Rules: `PROBLEM.md` owns problem semantics and result comparability. Representation changes do not change its epoch.
Increase `representation_revision` only when retained search state requires migration or becomes invalid. Record its disposition in `log.md`.
```

Replace each placeholder with inspected evidence, an authorized decision, or an exact closing action. Do not copy illustrative contracts into a real task.

## Frontmatter and row status

Use these core fields:

- `type`: `Optimization Representation`.
- `status`: `draft` or `stable`.
- `problem`: the relative link to the canonical parent `PROBLEM.md`.
- `problem_epoch`: the current parent epoch.
- `problem_generated_at`: the current parent `generated.at` content binding.
- `representation_revision`: a positive integer.
- `updated` and `generated`: the last meaningful writer and time.
- `review_scope`: add `exploratory` or `modular` only after the matching positive review.
- `verified`: add only after the current independent representation review passes.
- `sources`: add only for load-bearing sources in the core document.

A verification-only parent edit does not change `problem_generated_at`. A parent semantic edit changes `generated.at` and makes the representation binding stale.

Use row statuses as follows:

- `P`: the current search or proof claim depends on the contract.
- `~`: a documented hypothesis permits limited work but cannot support a stronger claim.
- `O`: a necessary item is unresolved; the Contract names the closing action or event.
- `-`: the item cannot affect the requested search scope; the Contract gives the reason.

A stable exploratory document can contain `~` rows when each row states a next action or claim limit. Provisional module rows do not permit independent module optimization.

A modular review requires pinned module, interface, and coupling contracts for the named work. A row can remain provisional only when the permitted work does not depend on it.

## Authority boundary

`PROBLEM.md` is the only authority for problem semantics. `REPRESENTATION.md` owns search strategy and references the parent instead of restating it as a new decision.

Use this ownership boundary:

| Concept | Normative owner |
|---|---|
| Optimized object, instance space, and scale variables | `PROBLEM.md` Slot A |
| Legal solution space, exact identity, and semantic equivalence | `PROBLEM.md` Slot B |
| Correctness and legality constraints | `PROBLEM.md` Slot C |
| Objective and comparison | `PROBLEM.md` Slots D and E |
| Resource limits | `PROBLEM.md` Slot F |
| Information model | `PROBLEM.md` Slot G |
| Measurement protocol and baseline meaning | `PROBLEM.md` Slot H |
| Canonical and search encodings, translations, and coverage | `REPRESENTATION.md` R1 |
| Encoding redundancy for exact candidates | `REPRESENTATION.md` R2 |
| Scale effects on search structures | `REPRESENTATION.md` R3 |
| Operations, neighborhoods, reachability, and legality handling | `REPRESENTATION.md` R4 |
| Module ownership and practical boundaries | `REPRESENTATION.md` R5 |
| Interfaces and candidate composition | `REPRESENTATION.md` R6 |
| Coupling and local-to-global claim limits | `REPRESENTATION.md` R7 |
| Representation validation and search-state compatibility | `REPRESENTATION.md` R8 |

A search representation can cover a subset of legal solutions. It cannot redefine the legal solution space.

A module can define a local objective. It cannot replace the parent objective, weaken a parent constraint, expand the information model, or increase the parent resource limit.

When a representation document conflicts with `PROBLEM.md`, the parent wins. Preserve the conflict, set the affected R item to `O`, invalidate representation assurance, and return to the applicable A-H work.

## Detail and module documents

Create `representation/<item>.md` only when two Contract sentences cannot define the rule. Use this minimum frontmatter:

```yaml
---
type: Optimization Representation Detail
title: "R7: Coupling"
description: Defines coupling facts that do not fit in the R7 contract.
status: draft
generated: { by: frame-optimization/1, at: "<ISO-8601 datetime>" }
sources: []
---
```

Keep adopted normative rules, research records, and user-decision records under separate headings.

- The Primary Framing Agent writes adopted normative sections.
- A Research Agent writes the delegated question and scope, research evidence and sources, code or experiment observations, candidate representations, risks, unknowns, recommendations, and `Proposed Contract text — not adopted`. It can update `generated` and `sources`.
- A Grill Agent writes user answers, authorizations, decision source and context, and unresolved user choices. It can update `generated`.

Proposed Contract text and candidate representations remain nonnormative until the Primary Framing Agent adopts them. Neither worker edits core Contract cells, R1-R8 status, adopted normative rules, `representation_revision`, lifecycle assurance metadata, or normative module-contract content.

Create `modules/<module-slug>/PROBLEM.md` only for actual separate optimization, proof, review, or delegation. Use the A-H template and add:

```yaml
scope: module
parent_problem: ../../PROBLEM.md
parent_epoch: <parent epoch>
representation: ../../REPRESENTATION.md
representation_revision: <current revision>
epoch: 1
```

The module contract refines the parent without copying it. Use `Inherit parent Slot <letter> without change` when no local refinement is needed.

Use one module layer by default. R5 must state the separate work and practical benefit before a nested module contract exists.

## Representation review record

The independent reviewer writes `representation-review.md`. Use this minimum frontmatter:

```yaml
---
type: Optimization Representation Review
title: <effort name> representation review
description: Records the latest representation review and current repair set.
status: draft
review_result: <allowed result>
review_scope: <none | exploratory | modular>
reviewed_by: review-representation/1
reviewed_at: "<ISO-8601 datetime>"
generated: { by: review-representation/1, at: "<ISO-8601 datetime>" }
---
```

Use this minimum body before any findings:

```markdown
# REPRESENTATION REVIEW: <effort name>

Result: <allowed result>
Reviewed: <canonical path to REPRESENTATION.md and every reviewed detail or module contract>
Reviewed at: <ISO-8601 datetime>
Permitted: <none | bounded whole-candidate search | exact named modules and operations plus bounded whole-candidate search>
```

Allowed results are `PROCEED_EXPLORATORY`, `PROCEED_MODULAR`, `RESEARCH_REQUIRED`, `REDESIGN_REQUIRED`, `REFRAME_REQUIRED`, and `BLOCKED`.

Each nonpositive finding uses this schema:

```markdown
## R1: <short finding name>

- Affects: <R item, module Slot, or cross-cutting rule>
- Work type: <research | grill | redesign | reframe-problem | blocker>
- Prevents: <exploratory | modular | both>
- Evidence: <decisive evidence>
- Required action: <one action>
- Complete when: <checkable condition>
- Repair status: <open | complete | blocked>
```

A positive result has no open finding. A nonpositive result has at least one finding with every field. `Reviewed` names the complete review surface. `Permitted` names exact modules and operations for modular scope. The reviewer owns result and finding text. The coordinator can update only repair status and writer metadata.

For a positive result, the reviewer sets `REPRESENTATION.md` and every reviewed normative detail or active module contract to `stable`. The reviewer adds current `verified` metadata and sets the core `review_scope` to `exploratory` or `modular`. The reviewer also sets `representation-review.md` to `stable`.

For a nonpositive result, the reviewer sets each affected contract document to `draft` and removes stale `review_scope` and `verified` metadata. If a required metadata write fails, the result is `BLOCKED`, not positive.

A review is stale when a reviewed Markdown document has no `generated.at` or has a `generated.at` later than `reviewed_at`.

Derive a nonpositive result from the complete finding set:

1. Any `blocker` gives `BLOCKED`.
2. Otherwise, any `reframe-problem` gives `REFRAME_REQUIRED`.
3. Otherwise, any `redesign` or `grill` gives `REDESIGN_REQUIRED`.
4. Otherwise, factual findings give `RESEARCH_REQUIRED`.

Reject one invalid review and request one fresh replacement. If the replacement is invalid or unavailable, record a review-capability blocker and keep affected documents draft.

## Revision and search-state compatibility

Problem results and representation-dependent search state use separate compatibility rules.

Every evaluation result records the canonical task path, parent epoch, canonical candidate identity, and Slot H measurement identity. A representation change does not decide result comparability or change the parent epoch.

Search state includes checkpoints, populations, proposal models, neighborhood caches, surrogate models, module-local scores, and representation-dependent proofs. Each retained search artifact records:

- canonical task path;
- parent problem epoch;
- representation revision;
- each applicable module epoch;
- producing representation or module.

Increase `representation_revision` only when a meaningful change requires migration or invalidates retained search state. Keep the revision for editorial changes and changes that leave all retained search state reusable.

Record one disposition for each affected artifact or artifact class:

- `reusable`: meaning and use remain unchanged;
- `migrated`: a checked translation makes the artifact valid under the new revision;
- `voided`: the artifact cannot be used under the new revision.

Write the newest `log.md` entry first. Include the date, changed R item, old revision, new revision, affected artifacts, disposition, reason, and evidence.

Do not void evaluation results because a search artifact becomes invalid. Do not keep a search artifact merely because its evaluated candidates remain comparable.

## Invalidation

Apply invalidation in the same change as every meaningful semantic edit.

- For a core representation change, set `REPRESENTATION.md` to `draft` and remove `review_scope` and `verified`.
- For a linked representation-detail change, apply the same invalidation to that detail and `REPRESENTATION.md`.
- For an active module-contract change, apply the same invalidation to that module contract and `REPRESENTATION.md`.
- For a parent semantic change, invalidate representation assurance even when the parent epoch stays unchanged.

After a changed parent passes fresh problem review, copy its current epoch and `generated.at` into the representation binding. Then request fresh representation review.

Meaningful changes include coverage, translation, redundancy, neighborhood, reachability, legality handling, module ownership, interfaces, composition, coupling, local-to-global claims, and search-state compatibility.

Editorial changes, links that preserve meaning, repair-status updates, and verification metadata do not invalidate semantics.

## Continuity and recovery

After compaction or a new session:

1. Read the selected `PROBLEM.md` completely.
2. Return to problem definition when the parent is draft, stale, or unverified.
3. Otherwise, read the same `REPRESENTATION.md` completely.
4. Confirm `problem_epoch` and `problem_generated_at` against the parent.
5. Read relevant representation dispositions in `log.md`.
6. Read `representation-review.md` when it exists.
7. Continue the first safe open finding.
8. Otherwise, continue each `O` row and claim-limiting `~` row.
9. Open only details needed for the next action.
10. Confirm harness and baseline readiness before positive review.

If the last decision was not recorded, confirm only that decision. Do not reconstruct it from uncertain conversation context.

## Review outcomes and handoff

`PROCEED_EXPLORATORY` permits bounded whole-candidate search. It prohibits independent module optimization and unsupported local-to-global improvement claims.

When coverage, reachability, or redundancy remains unresolved, exploratory non-discovery cannot show exhaustion or absence of a better solution.

`PROCEED_MODULAR` also permits only the named module work within reviewed interfaces, coupling rules, and resource partitions. Every composed candidate remains subject to parent global evaluation.

A positive handoff contains:

- canonical task path;
- parent problem epoch and `generated.at` binding;
- representation revision;
- positive review result and permitted scope;
- canonical evaluation representation;
- each permitted search representation;
- permitted operation set;
- candidate coverage limits;
- reachability status and material redundancy effects;
- applicable module contracts;
- required coordination and global evaluation;
- search-state compatibility rules;
- Slot H harness and baseline identity.

Require the downstream workflow to acknowledge the task path, parent epoch, parent binding, representation revision, and permitted scope before recording search state or results.

For `RESEARCH_REQUIRED`, `REDESIGN_REQUIRED`, `REFRAME_REQUIRED`, or `BLOCKED`, return the exact result, affected item, canonical task path, and first next action or blocker. Do not emit a positive search handoff.

A positive result means the named search work is defined. It does not predict optimization success.
