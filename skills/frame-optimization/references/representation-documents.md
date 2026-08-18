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

During search design, readers normally start with only `PROBLEM.md` and `REPRESENTATION.md`. Create optional documents only when their extra detail is necessary.

The two main documents state every choice that a person or agent doing the work must make. They also name the fixed code, manifests, configs, or schemas that remove a choice. Details may contain complete contents, algorithms, command syntax, serialization, validation order, and evidence. If two allowed implementations may choose differently, state the choice or allowed freedom and its limits in the main document that owns it.

## `REPRESENTATION.md` template

Use the same core shape as `PROBLEM.md`: minimal frontmatter, one title, a plain-language Brief, one R1-R8 Contract table, one Open decisions list, one Known limits list, one status key, and a three-line rule block. Do not impose a sentence, paragraph, word, or source-line count on the Brief. Keep the core document compact through the necessity rules below. Use one concise decision sentence in each Contract cell and a second short sentence only when its direct consequence would otherwise be unclear.

```markdown
---
type: Optimization Representation
status: draft
problem: PROBLEM.md
problem_epoch: <positive integer copied from PROBLEM.md>
problem_generated_at: "<PROBLEM.md generated.at>"
representation_revision: 1
updated: <ISO-8601 date>
generated: { by: frame-optimization/1, at: "<ISO-8601 datetime>" }
---

# REPRESENTATION: <effort name>

## Brief

<Name the concrete thing from PROBLEM.md that search changes. In plain language, explain the loop from the starting point through proposal, conversion, rejection or measurement, permitted feedback, selection, and stopping. State whether search changes the whole thing or named parts and what the results cannot prove.>

## Contract

| # | Item | St | Contract | Detail |
|---|---|---|---|---|
| R1 | Measured and proposed forms | O | What the harness measures, what the optimizer proposes, how conversion works, and which options search may try are not decided. | |
| R2 | Duplicate proposals | O | We do not know whether different proposals can produce the same option, so results cannot claim unique or complete coverage. | |
| R3 | Effect of problem size | O | How problem size changes proposal size and scoring cost is undecided, so results cannot claim efficient search. | |
| R4 | Allowed changes | O | Allowed changes, invalid-option handling, and whether repeated changes can reach every allowed option are undecided, so search cannot start. | |
| R5 | Split into parts | - | Search treats each option as one whole; no split is active. | |
| R6 | Part boundaries | - | No rules for joining separately changed parts apply while search treats each option as one whole. | |
| R7 | Cross-part effects | - | No cross-part rule applies because search does not split the option into parts. | |
| R8 | Search run and old work | O | The start, budget, feedback use, selection, stopping, harness checks, and old-work reuse are not decided. | |

## Open decisions

- R1 (O): decide what the harness measures, what the optimizer proposes, how conversion is checked, and which options search may try.
- R2 (O): check whether different proposals produce the same option, or state that results cannot claim unique or complete coverage.
- R3 (O): check how changing problem size affects proposal size and scoring cost before saying search is efficient.
- R4 (O): decide allowed changes, illegal-option handling, starting points, and what search cannot prove before search starts.
- R8 (O): decide the start, budget, allowed feedback, selection and stopping rules, harness checks, and old-work reuse before review.

## Known limits

- None.

St: `P` = decided for this work; `~` = working answer; `O` = not decided; `-` = not relevant.

Rules: `PROBLEM.md` decides what results mean and which results can be compared.
Keep `representation_revision` when old checkpoints and saved search work can still be used without change.
Increase it only when old work must be converted or discarded, and record that decision in `log.md`.
```

Replace the Brief placeholder with inspected task facts. Replace each starter Contract with a task-specific decision when evidence supports one; keep a starter sentence only when it truthfully describes the open state. Do not copy illustrative task nouns into a real task.

The Brief is the plain-language search story, not an R1-R8 summary and not a second Contract. Once search design begins, readers normally use `PROBLEM.md` and `REPRESENTATION.md` together to make decisions. Use the Contract table as a completeness check after drafting; do not use its row order as the reading order.

Explain search through this general path:

1. Name the concrete thing from `PROBLEM.md` that search changes. Do not repeat the full problem Contract.
2. Name the complete thing that measurement code accepts and what search proposes.
3. Explain how a proposal becomes measurable and what happens when conversion or validation fails.
4. State the starting point, allowed changes, reachable set, duplicate handling, and whether search changes the whole thing or named parts.
5. Explain whether earlier results may guide later proposals, how work is selected, and when search confirms, promotes, stops, or expands.
6. Orient the reader to the budget, measurement code, completed checks, old-work reuse, and major limits where they affect this loop. Let the Contract and lists carry exact values and complete coverage.

Adapt the paragraphs to the task. Combine adjacent steps when that improves flow, and add a paragraph when a distinction would otherwise be hidden. Do not give each R row its own sentence.

Do not copy the parent Contract into `REPRESENTATION.md`. Readers normally load both main documents during search design. Repeat only enough problem context to make the search story flow, and keep `PROBLEM.md` as the authority. Any mismatch is a defect.

Use concrete task nouns. At first use, define a task-specific term as a familiar kind of thing and state its role before using its short name. Do not define one unexplained term with another. Use verbs to show how one search step produces the next. If one sentence contains two terms that a new reader cannot explain, split or rewrite it.

Keep the Brief compact by removing evidence history, rejected alternatives, full formulas, file hashes, and step-by-step procedures. Keep a version, path, or identifier only when a reader needs it to interpret the current result. Remove repeated meaning, but never merge separate concepts only to shorten the document.

The Contract table decides the ordinary search actions and conclusions. Use one concise decision sentence in each Contract cell and a second short sentence only when its direct consequence would otherwise be unclear. Never write a request to define or fill in information. Put derivations, evidence, exhaustive operation parameters, validation logs, and multi-step procedures in `representation/<item>.md`. A detail must not introduce a rule that changes permitted proposals, feedback use, selection, stopping, evaluation, reuse, or claims without a plain-language summary in one of the two main documents. The Detail cell contains only one link or stays empty.

Use this main-document test: if omitting a fact could make two reasonable readers or agents propose different kinds of work, use different feedback, select different survivors, stop at different times, choose different fixed evaluation code or inputs, exceed the budget, reuse incompatible state, or make different search claims, summarize that fact in `REPRESENTATION.md` or the row in `PROBLEM.md` that owns it. Exact contents and internal behavior may stay in a detail when a named executable, manifest, config, or schema already removes the choice.

List every `O` or `~` row exactly once under Open decisions. Each bullet states the pending decision, next action, closure condition, and immediate consequence when it is not obvious. Omit `P` and `-` rows. Write `- None.` when no decision remains open or provisional.

List under Known limits every current restriction on search or conclusions that remains after a row is decided, plus any cross-cutting evidence limit. A `P` row can appear here because its search rule is decided even when available evidence cannot support a stronger claim. Do not put a `P` row under Open decisions. Write `- None.` when no known limit remains.

Use the same plain language in the Brief, Contract cells, Open decisions, and Known limits. Prefer the task's real noun, such as `config`, `schedule`, `model`, or `deck`, over `candidate`, `solution`, or `representation`.

Use plain names before formal labels:

| Avoid in the Brief | Write instead |
|---|---|
| canonical form C | the rendered config the harness measures |
| search form E1 | the parameter vector the optimizer proposes |
| checked translation T1 | the render step and the checks that verify it |
| subset U | the configs this search is allowed to propose |
| encoding redundancy | different proposals can produce the same config |
| reachability | repeated allowed changes can reach every allowed config |
| decomposition | search is split into separately changed parts |
| claim limit | what the results cannot prove |
| state compatibility | whether old checkpoints may be reused |
| evaluation protocol | the data, code, repetitions, hardware, and score calculation |
| candidate legality | which configs or schedules are allowed |
| exact identity or equivalence | when two configs or schedules count as the same |
| normalization | which one of several equivalent proposals search keeps |
| exhaustion | testing every allowed config or schedule |
| retained search state | old checkpoints, saved proposals, and cached scores |
| search efficiency | how the time and computing needed for search grow with problem size |
| parent contract | the rules in `PROBLEM.md` |
| representation review is not ready | state the missing fact or file and the action it blocks |
| pinned | decided and fixed for the current work |

Formal labels can appear in the Contract table or a linked detail only after the Brief has introduced the underlying item in plain language. A label never replaces the concrete noun.

Words such as `canonical`, `normative`, `encoding`, `redundancy`, `reachability`, `decomposition`, `coupling`, `semantics`, `claim limit`, `exhaustion`, `state compatibility`, `epoch`, `revision`, and `review` fail the plain-language check in Brief prose unless an exact field or quotation requires them. Rewrite the concrete fact and consequence.

Read both Briefs before review. Without merely repeating task-specific labels, a new reader must be able to explain:

- what system or process is being improved, what can change, and how that change affects the result;
- the complete thing measurement accepts and what search proposes;
- the path from starting point through proposal, conversion, rejection or measurement, feedback, selection, and stopping;
- whether search changes the whole thing or named parts;
- what the search results cannot prove.

Then read the complete `PROBLEM.md` and `REPRESENTATION.md` without opening details. The pair passes the decision check only when the reader can decide what search may try, how proposals become measurable, how invalid work is handled, how feedback and budget may be used, how work is selected or stopped, whether search is split, which old work may be reused, what remains unknown, and what the results cannot prove.

For an older table-only `REPRESENTATION.md`, derive the Brief, Open decisions, and Known limits from the current table and linked rule details. Apply both the task-to-search understanding check and the two-document decision test before preserving review assurance. When the search meaning already exists consistently and only the Brief explanation is missing, keep R1-R8 status and `representation_revision`, rewrite the Brief, set `REPRESENTATION.md` to draft, remove `review_scope` and `verified`, and require a fresh readability review. When an underlying search decision is absent, set the affected row to `O`, name the missing decision under Open decisions, invalidate representation assurance, and apply the search-state rules. In particular, absent feedback, survivor selection, tie handling, confirmation, promotion, stopping, or scale-up rules are missing R8 decisions, not wording omissions.

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
- `~`: a documented working decision permits limited work but cannot support a stronger conclusion. Its Open decisions bullet states the next action and closure condition.
- `O`: a necessary item is unresolved; the Contract states the current boundary and its Open decisions bullet states the closing action.
- `-`: the item cannot affect the requested search scope; the Contract gives the reason.

A stable exploratory document can contain `~` rows when each row states a next action or claim limit. Provisional module rows do not permit independent module optimization.

A modular review requires pinned module, interface, and coupling contracts for the named work. A row can remain provisional only when the permitted work does not depend on it.

## Authority boundary

`PROBLEM.md` is the only authority for problem semantics. `REPRESENTATION.md` owns search strategy and references the parent instead of restating it as a new decision.

The representation Brief is the search half of the two-document story, not a second problem contract. It gives only the parent context needed to understand search. `PROBLEM.md` supplies the score, required rules, baseline, success test, run combination, resources, and measurement meaning, and resolves any conflict.

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
| Search-run rules, validation, and old-work compatibility | `REPRESENTATION.md` R8 |

A search representation can cover a subset of legal solutions. It cannot redefine the legal solution space.

A module can define a local objective. It cannot replace the parent objective, weaken a parent constraint, expand the information model, or increase the parent resource limit.

When a representation document conflicts with `PROBLEM.md`, the parent wins. Preserve the conflict, set the affected R item to `O`, invalidate representation assurance, and return to the applicable A-H work.

## Detail and module documents

Create `representation/<item>.md` when one Contract sentence cannot define the rule. Use this minimum frontmatter:

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

Proposed Contract text and candidate representations remain nonnormative until the Primary Framing Agent adopts them. Neither worker edits the representation Brief, Open decisions, Known limits, core Contract cells, R1-R8 status, adopted normative rules, `representation_revision`, lifecycle assurance metadata, or normative module-contract content.

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

Use one module layer by default. Keep R5-R7 at `-` until an actual decomposition is proposed. R5 must state the separate work and practical benefit before a nested module contract exists.

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

## Cold-read reconstruction

- Task and result: <plain restatement based only on both Briefs>
- Proposal path: <what measurement accepts, what search proposes, and how it becomes measurable>
- Search loop: <start, propose, reject or measure, use feedback, select, and stop>
- Unexplained terms or relationships: <None or exact gaps>
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

A positive result has no open finding and says `None` for unexplained terms or relationships in its Cold-read reconstruction. A nonpositive result has at least one finding with every field. `Reviewed` names the complete review surface. `Permitted` names exact modules and operations for modular scope. The reviewer owns result, Cold-read reconstruction, and finding text. The coordinator can update only repair status and writer metadata.

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

Small wording improvements that already pass the current understanding check, links that preserve meaning, repair-status updates, and verification metadata do not invalidate semantics. A rewrite needed because either Brief failed the understanding check keeps R1-R8 status and `representation_revision` when meaning is unchanged, but it invalidates review assurance and requires a fresh review.

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

Before selecting work, read both main documents without opening optional details. Confirm that their Briefs tell one coherent story, both tables agree, Open decisions lists every unresolved decision, Known limits lists every remaining restriction, and the pair contains every fact needed for ordinary search and result decisions.

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
- permitted feedback, selection, promotion, and stopping rules;
- candidate coverage limits;
- reachability status and material redundancy effects;
- applicable module contracts;
- required coordination and global evaluation;
- search-state compatibility rules;
- Slot H harness and baseline identity.

Require the downstream workflow to acknowledge the task path, parent epoch, parent binding, representation revision, and permitted scope before recording search state or results.

For `RESEARCH_REQUIRED`, `REDESIGN_REQUIRED`, or `REFRAME_REQUIRED`, continue every safe, reachable, in-scope, and authorized repair route. The result alone does not require a user return. `BLOCKED` permits a return only when the existing rules leave no legal internal action. Do not emit a positive search handoff.

When an existing route determines that control must return, use [user-facing-return.md](user-facing-return.md). Keep the review finding as the unchanged repair manifest.

A positive result means the named search work is defined. It does not predict optimization success.
