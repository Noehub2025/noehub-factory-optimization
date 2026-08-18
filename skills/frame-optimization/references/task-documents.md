# Task documents — format and writing rules

Shared base reference for skills that write optimization task documents. It defines parent problem paths, formats, ownership, result comparability, and language rules. Read [representation-documents.md](representation-documents.md) for representation-stage document lifecycle and handoff rules.

## Contents

- Task path and layout
- Open Knowledge Format rules
- `PROBLEM.md` template
- Status and ownership
- `review.md` structure
- Slot documents
- Review invalidation
- Epoch and `log.md`
- Language rules

## Task path and layout

Use one caller-selected task under `docs/skills/optimization/<task-slug>/`. The slug must match `[a-z0-9]+(?:-[a-z0-9]+)*`.

Resolve the canonical path and confirm that it remains under `docs/skills/optimization/`. When several tasks exist without a caller selection, request explicit selection; recency is not a selector.

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

During problem framing, readers normally use `PROBLEM.md` to make decisions. During search design, they normally use `PROBLEM.md` and `REPRESENTATION.md` together. A reader should not need an optional detail for an ordinary development, evaluation, acceptance, resource, reuse, or claim decision. Create each optional file only when its extra precision is necessary.

An ordinary decision chooses an allowed action, value, limit, file, acceptance outcome, reuse outcome, or supported claim. The main document names the executable code and fixed inputs that settle the decision and summarizes what they do. A detail may contain complete seed lists, derivations, serialization rules, command syntax, validation order, and other internals when the named executable or fixed file already removes the choice. If the person or agent doing the work must choose between alternatives, the choice and its limits belong in the main document.

Keep existing project documents in place. Link them as sources; publish or rewrite them only under separate authorization.

## Open Knowledge Format rules

Every Markdown concept document starts with valid YAML frontmatter containing nonempty `type` and `status`. Use `status: draft` before readiness and `status: stable` only after independent review.

Use `generated` for the last meaningful writer and time. Use `verified` only for the current independent reviewer and time. Use standard Markdown links and list load-bearing provenance under `sources`.

Do not create `index.md`. `log.md` uses the reserved Open Knowledge Format date-and-entry structure and has no frontmatter.

Git history can support an audit. File-based recovery must not depend on Git history.

Keep core-document frontmatter to fields required for identity, lifecycle, parent binding, and review freshness. Do not explain Open Knowledge Format or controlled-language rules inside `PROBLEM.md` or `REPRESENTATION.md`.

## `PROBLEM.md` template

Keep the body to one title, a plain-language Brief, one A-H Contract table, one Open decisions list, one Known limits list, one status key, and one epoch rule block. Do not impose a sentence, paragraph, word, or source-line count on the Brief. Keep the core document compact through the necessity rules below, not by merging separate ideas.

```markdown
---
type: Optimization Problem
status: draft
epoch: 1
updated: <ISO-8601 date>
generated: { by: frame-optimization/1, at: <ISO-8601 datetime> }
---

# PROBLEM: <effort name>

## Brief

<In familiar words, explain the system or process and one complete run. State what this work can change, what that thing receives or faces, what it produces or controls, and how that affects the result. Then explain how results are compared, what counts as success now, and how that differs from the real goal.>

## Contract

| # | Slot | St | Contract | Detail |
|---|---|---|---|---|
| A | What is improved | O | The improved object, covered cases, size range, and operating conditions have not been decided for the current work. | |
| B | Allowed options | O | The allowed options and rule for when two options count as the same have not been decided. | |
| C | Rules to satisfy | O | The required safety and quality rules, allowed risk, and violation consequences have not been decided. | |
| D | Score and success | O | The score, baseline, comparison rule, and success test have not been decided. | |
| E | How runs combine | O | No rule combines cases and repeated runs or defines changing problem size and hostile inputs. | |
| F | Time and computing | O | The cost of running an option and the budget for finding one have not been decided. | |
| G | Allowed data and feedback | O | No rule says which data, feedback, future information, or adaptation the optimizer may use. | |
| H | How the score is measured | O | The data, repetition count, score calculation, hardware, and executable measurement code have not been decided. | |

## Open decisions

- A (O): decide what is improved, which cases and sizes are covered, and under which conditions.
- B (O): decide which options are allowed, how they are written, and when two options count as the same before comparing them.
- C (O): decide each required safety and quality rule, allowed risk, and violation consequence before evaluation.
- D (O): decide the score, baseline, comparison rule, and success test before evaluation.
- E (O): decide how cases and repeated runs combine, how problem size changes, and which hostile inputs are allowed.
- F (O): decide the cost of running an option and the authorized budget for finding one before search starts.
- G (O): decide which data, feedback, future information, and adaptation the optimizer may use before search starts.
- H (O): decide the data, repetition count, score calculation, hardware, and executable measurement code before evaluation.

## Known limits

- None.

St: `P` = decided for this work; `~` = working answer; `O` = not decided; `-` = not relevant.

Rules: Each result records the task path and `epoch`.
Compare results only within one epoch.
When a `P` row changes, record whether old results still apply, must be rerun, or must be discarded in `log.md`.
```

The Brief is the plain-language entry point to the problem, not an A-H summary and not a second Contract. It must make the task story and relationships easy to follow. `PROBLEM.md` as a whole must support ordinary problem-level decisions without opening a detail. Use the Contract table as a completeness check after drafting; do not use its row order as the reading order.

Explain the task through this general path:

1. Describe the system, process, or activity in familiar words and show where one complete run starts and ends.
2. State what this work can change.
3. State what the changed thing receives, observes, or faces. If none applies, state the conditions that govern its choices.
4. State what it produces, controls, or decides, and explain how that output changes the observed result.
5. Explain one raw result, how repeated results become a comparison, the baseline, current success, and the real goal.
6. Orient the reader to important data, feedback, resource, open-decision, or evidence limits only when they change this story. Let the Contract and lists carry exact values and complete coverage.

Adapt the paragraphs to the task. Combine adjacent steps when that improves flow, and add a paragraph when a distinction would otherwise be hidden. Do not give each A-H row its own sentence.

Use concrete task nouns. Prefer `schedule`, `config`, `model`, `deck`, or another domain noun over `candidate` or `solution`. At first use, define a task-specific term as a familiar kind of thing and state its role before using its short name. For example, write `the ranking method that turns pairwise wins into an ordered list (Bradley-Terry)` before `Bradley-Terry rank`. Do not define one unexplained term with another. If one sentence contains two terms that a new reader cannot explain, split or rewrite it.

Use verbs to explain relationships that affect the optimization. Naming two components is not enough when one changes the input, state, cost, or opportunity seen by the other. State that effect in ordinary language.

Before drafting the Contract table, restate the Brief without relying on task-specific labels. The restatement must answer:

- What system or process exists before optimization?
- What can this work change?
- What information, input, or conditions does the changed thing receive or face?
- What does it produce, control, or decide?
- How does that output affect the measured result?
- What is one evaluation run, what result is better, and what is the current success test?

If a question does not apply, the Brief must make the reason clear. A name such as a product, environment, model, benchmark, algorithm, file set, or dataset does not answer a question by itself.

Keep the Brief compact by removing evidence history, rejected alternatives, full formulas, file hashes, and step-by-step procedures. Keep a version, path, or identifier only when a reader needs it to interpret the current result. Remove repeated meaning, but never merge separate concepts only to shorten the document.

A Brief can summarize a rule that the Contract table decides exactly. It does not need to repeat every value or restriction from the table and lists. An omission is a defect when the story becomes unclear, a relationship is hidden, or a term cannot be understood. A mismatch is always a defect. Use the same plain language in the Brief, Contract cells, Open decisions, and Known limits.

Use this main-document test: if omitting a fact could make two reasonable readers or agents choose different development work or fixed evaluation code and inputs, accept different results, exceed authorization, reuse incompatible work, or make different strength claims, summarize that fact in `PROBLEM.md`. Evidence history, derivations, exhaustive parameter lists, commands, validation logs, and internal behavior already fixed by a named executable can stay in a detail.

| Avoid | Write instead |
|---|---|
| candidate legality | which schedules or configs are allowed |
| identity or equivalence | when two schedules or configs count as the same |
| aggregation | how results from cases or seeds are combined |
| evaluation semantics | exactly how runs produce one score |
| resource contract | the time, money, hardware, or samples allowed |
| information model | the data and feedback the optimizer may use |
| measurement protocol | the data, code, repetitions, hardware, and score calculation |
| proxy gap | where the measured score differs from the real goal |
| pinned | decided and fixed for the current work |
| parent contract | the rules in `PROBLEM.md` |
| review is not ready | state the missing fact or file and the action it blocks |

Words such as `canonical`, `normative`, `semantics`, `quantifier`, `adversary`, `claim limit`, `epoch`, `revision`, and `review` fail the plain-language check in Brief prose unless an exact field or quotation requires them. Rewrite the concrete fact and consequence.

The Contract table decides the ordinary problem-level actions and conclusions. Use one concise decision sentence in each Contract cell; use a second short sentence only when the decision and its direct consequence would otherwise be unclear. Never use a request such as `define`, `decide`, `fill in`, or `name` as the Contract. When no defensible decision exists, state exactly what remains undecided. Name a cross-Slot dependency in the affected Contract cells.

Put derivations, evidence, exhaustive parameter tables, validation logs, and multi-step procedures in `slots/<letter>.md`. A detail may fix exact implementation behavior, but it must not introduce a rule that changes an ordinary development, evaluation, acceptance, resource, reuse, or claim decision without a plain-language summary in `PROBLEM.md`. Include a compact formula or ordering rule in the core document when a reader must apply it to calculate or accept a result. The Detail cell contains only one link or stays empty; it never contains status text or explanation.

List every `O` or `~` row exactly once under Open decisions. Each bullet states the pending decision, next action, closure condition, and immediate consequence when it is not obvious. Omit `P` and `-` rows. Write `- None.` when no decision remains open or provisional.

List under Known limits every current restriction on action or conclusion that remains after a row is decided, plus any cross-cutting evidence limit. A `P` row can appear here because its rule is decided even when available evidence cannot support a stronger claim. Do not put a `P` row under Open decisions. Write `- None.` when no known limit remains.

For an older table-only `PROBLEM.md`, derive the Brief, Open decisions, and Known limits from the current table and linked rule details. Apply both the task-understanding check and the main-document decision test before preserving review assurance. When the task meaning already exists consistently and only the Brief explanation is missing, keep A-H status and the epoch, rewrite the Brief, set `PROBLEM.md` to draft, remove `verified`, and require a fresh readability review. When the underlying meaning is absent or conflicting, set the affected row to `O`, name the missing decision under Open decisions, and apply the normal semantic invalidation and epoch rules.

## Status and ownership

- `P` means result interpretation depends on a pinned contract.
- `~` means a documented working answer permits more framing work. Its Open decisions bullet names the pending decision and closure condition.
- `O` means a necessary point remains open. Its Open decisions bullet names the closing action or event.
- `-` means the Slot cannot affect comparison; its Contract gives the reason.

The Primary Framing Agent alone writes the problem Brief, Open decisions, and Known limits and adopts A-H or R1-R8 Contract cells, row status, normative rules, task terms, epochs, representation revisions, module-contract semantics, and downstream handoffs.

The Primary Framing Agent creates or selects each worker detail before delegation. The Research Agent writes only research evidence, sources, observations, candidate representations, risks, unknowns, recommendations, and explicitly proposed Contract text. The Grill Agent writes only user answers, authorizations, decision provenance, necessary context, and unresolved user choices. Each worker returns a packet that matches its durable record.

Research and grill workers do not edit the problem Brief, Open decisions, Known limits, core Contract cells, row status, adopted normative rules, epochs, representation revisions, lifecycle assurance metadata, or normative module-contract content.

The Review Agent writes valid verdicts and finding text in `review.md`. It can edit review metadata and contract-document frontmatter without changing A-H semantics.

The Representation Review Agent writes valid results and finding text in `representation-review.md`. It can edit review metadata and reviewed-document frontmatter without changing representation semantics.

If a required valid review is unavailable, the Primary Framing Agent records a review-capability blocker in the applicable review file and keeps affected documents draft.

## `review.md` structure

Use `status: draft` while a repair set is open. Use `status: stable` after valid `PROCEED`.

```markdown
---
type: Optimization Review
title: Review of <effort name>
description: Records the latest independent review and current repair set.
status: draft
updated: <ISO-8601 date>
generated: { by: review-optimization/1, at: <ISO-8601 datetime> }
---

# REVIEW: <effort name>

Verdict: <PROCEED | RESEARCH_REQUIRED | REFRAME_REQUIRED | BLOCKED>
Reviewed: <canonical task paths>
Reviewed at: <ISO-8601 datetime>

## Cold-read reconstruction

- System and run: <plain restatement based only on the Brief>
- Change and effect: <what can change and how it affects the result>
- Evaluation and success: <one evaluation, current success, and real goal>
- Unexplained terms or relationships: <None or exact gaps>

## R1: <short finding name>

- Affects: <Slot or cross-cutting rule>
- Work type: <research | grill | reframe | blocker>
- Evidence: <decisive evidence>
- Required action: <one action>
- Complete when: <checkable condition>
- Repair status: <open | complete | blocked>
```

A valid review contains exactly one allowed verdict and a Cold-read reconstruction written before details were opened. `PROCEED` has no open finding and says `None` for unexplained terms or relationships. Every other verdict has at least one finding with all six fields.

`Required action` and `Complete when` define the repair work and its checkable completion, not the user reply. Keep the finding schema unchanged. When control returns to the user, derive the reply through [user-facing-return.md](user-facing-return.md).

The Review Agent initializes each finding to `open`. The Primary Framing Agent sets `complete` only when the completion condition holds and sets `blocked` only with an exact blocker.

Derive the verdict from work types: any `blocker` gives `BLOCKED`; otherwise, any `reframe` or `grill` gives `REFRAME_REQUIRED`; otherwise, factual findings give `RESEARCH_REQUIRED`.

A Review Agent accepts an evidence-backed agent default through a `reframe` finding. The Primary Framing Agent records that acceptance, changes the row to `P`, and requests a fresh readiness review.

## Slot document frontmatter

```yaml
---
type: Optimization Slot Detail
title: "Slot E: Evaluation semantics"
description: Defines evaluation semantics that do not fit in the Slot E contract.
status: draft
generated: { by: frame-optimization/1, at: <ISO-8601 datetime> }
sources: []
---
```

- `status` is mandatory on every task document: `draft` before readiness, `stable` only after independent review.
- On every meaningful change, set `generated` to your own actor and time.
- List load-bearing sources in `sources`; long source lists belong here, in the Slot document, keeping `PROBLEM.md` small.

## Review invalidation

Any meaningful change to `PROBLEM.md` or a linked contract document invalidates the prior review. Apply this in the same change as the edit:

- for a `PROBLEM.md` change: set `status: draft` and remove `verified` from that file;
- for a linked-document change: set `status: draft` and remove `verified` from both that document and `PROBLEM.md`.

A meaningful change can alter legality, ranking, success, measurement, resource feasibility, or result interpretation. Spelling, link repair, and small wording improvements that already passed the current task-understanding check carry no invalidation. A rewrite needed because the Brief failed that check keeps A-H status and the epoch when meaning is unchanged, but it invalidates review assurance: set the core document to draft, remove `verified`, and require a fresh review. Changes only to review metadata do not invalidate themselves.

The linked Slot document is part of the row contract: formulas, quantifiers, distributions, seed rules, and measurement rules in it are normative. A semantic change to a pinned (`P`) contract while retained results exist additionally requires a comparability review and a `log.md` disposition — flag this to the caller; the disposition decision belongs to `review-optimization`.

When `REPRESENTATION.md` exists, a parent semantic change also invalidates its parent binding and review assurance. Follow [representation-documents.md](representation-documents.md) without changing the parent epoch solely for representation state.

## Epoch and `log.md`

An epoch is one set of comparable results. Every downstream result records the canonical task path and current positive integer epoch.

For a semantic change to a pinned contract with retained results, record one disposition:

- `unaffected`: preserve result meaning and keep the epoch.
- `re-evaluated`: rerun all retained results, mark old measurements superseded, and keep the epoch.
- `voided`: exclude old results from comparison and increase the epoch.

Write the newest `log.md` entry first. Include date, Slot, old epoch, new epoch, disposition, reason, and affected results.

## Contract cells

- Use one concise decision sentence per Contract cell. Use a second short sentence only when needed to state the direct consequence clearly.
- Do not write a TODO or an instruction to the next writer in a Contract cell.
- An `O` row's cell states the known boundary or unresolved point. Its Open decisions bullet states the closing action or event.
- A `~` row's cell states the working answer. Its Open decisions bullet states the pending decision and closure condition.
- A `-` row's cell gives the reason the Slot does not apply.
- When one Slot depends on another, name the dependency in the affected cells. The Brief can orient the reader but cannot carry the rule alone.

## Slot document body

A Slot document can contain: evidence and source links; rejected interpretations; formulas and quantifier order; research results; discussion results; a detailed action that can close an open point. The A–H table lives only in `PROBLEM.md`.

Keep adopted normative rules, research records, and user-decision records under separate headings.

- The Primary Framing Agent writes adopted normative sections.
- A Research Agent writes the delegated question and scope, research evidence and sources, code or experiment observations, candidate representations, risks, unknowns, recommendations, and `Proposed Contract text — not adopted`. It can update `generated` and `sources`.
- A Grill Agent writes user answers, authorizations, decision source and context, and unresolved user choices. It can update `generated`.

Proposed Contract text and candidate representations remain nonnormative until the Primary Framing Agent adopts them.

When a default was adopted because the user could not decide, mark it `Decision source: agent default` and give its evidence.

## Language — ASD-STE100 profile

Task documents are in English and follow this 12-rule profile from ASD-STE100 Issue 9:

1. Use approved Issue 9 dictionary words or recorded project technical terms.
2. Use one word for one meaning.
3. Use the same term for the same item.
4. Use active voice unless the agent is unknown.
5. Target 20 words for procedural sentences.
6. Target 25 words for descriptive sentences.
7. Write one instruction in each sentence.
8. Keep one topic in each paragraph.
9. Keep each paragraph to six sentences or fewer.
10. Use American English spelling.
11. Do not use Latin abbreviations.
12. Replace an ambiguous pronoun with its noun.

File paths, code identifiers, formulas, and exact quotations keep their original form. Optimization terms are project technical terms: define a local term in its Slot document, and a term used by multiple Slots in `terms.md`, linked from where it is used.

For a core Brief, plain-language readability takes priority over sentence-length targets and formal labels. Do not omit a relationship or stack nouns to shorten a sentence. A reader who has not seen the task or this workflow must understand the task story and every term used in that story without opening the table or a detail. After reading the complete `PROBLEM.md`, the reader must be able to decide which options and results are valid, how results are compared, what counts as current success, which resources and feedback are allowed, what remains undecided, and what the results cannot conclude.
