# Task documents — format and writing rules

Shared base reference for skills that write optimization task documents. It defines parent problem paths, formats, ownership, result comparability, and language rules. Read [representation-documents.md](representation-documents.md) for representation-stage document lifecycle and handoff rules.

## Contents

- Task path and layout
- Open Knowledge Format rules
- `PROBLEM.md` template
- Readability and review scope
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

During problem framing, readers normally use `PROBLEM.md` to make decisions. During search design, they normally use `PROBLEM.md` and `REPRESENTATION.md` together. Keep the governing choices visible in the core document; clearly named normative details may supply their exact rules without duplicating them. Create each optional file only when its extra precision is necessary.

Use [Stable contract and live state](frontier-handoff.md#stable-contract-and-live-state) to place a decision. Core documents state durable meaning and allowed freedom, referencing reusable methods and their applicable limits. Details supply precision and evidence. A particular realization or execution choice belongs in W or Batch; a main document need not settle each file, parameter or command chosen there.

Keep existing project documents in place. Link them as sources; publish or rewrite them only when the applicable user grant covers that action; use [User decisions](../../frontier-optimization/references/user-decisions.md) when permission is missing.

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
Compare results only when their measurement meaning supports the proposed use.
For a changed comparison, apply the affected-use disposition in `log.md`; preserve original results and their producing epochs.
```

The Brief is the plain-language entry point to the problem, not an A-H summary and not a second Contract. It must make the task story and relationships easy to follow. The core document states the governing choices and links exact normative details where needed. Use the Contract table as a completeness check after drafting; do not use its row order as the reading order.

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

When assessing readability, use these questions as thinking aids, not a required restatement or checklist:

- What system or process exists before optimization?
- What can this work change?
- What information, input, or conditions does the changed thing receive or face?
- What does it produce, control, or decide?
- How does that output affect the measured result?
- What is one evaluation run, what result is better, and what is the current success test?

A name alone does not explain a relationship. Omit questions that do not help the current reader; apply Readability and review scope to any actual gap.

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

Prefer concrete facts and consequences over workflow jargon in Brief prose. Explain necessary technical terms; no word is by itself a review failure.

The Contract table decides the ordinary problem-level actions and conclusions. Use one concise decision sentence in each Contract cell; use a second short sentence only when the decision and its direct consequence would otherwise be unclear. Never use a request such as `define`, `decide`, `fill in`, or `name` as the Contract. When no defensible decision exists, state exactly what remains undecided. Name a cross-Slot dependency in the affected Contract cells.

Put derivations, evidence, exhaustive parameter tables, validation logs, and multi-step procedures in `slots/<letter>.md`. A detail may fix exact implementation behavior, but it must not introduce a rule that changes an ordinary development, evaluation, acceptance, resource, reuse, or claim decision without a plain-language summary in `PROBLEM.md`. Include a compact formula or ordering rule in the core document when a reader must apply it to calculate or accept a result. The Detail cell contains only one link or stays empty; it never contains status text or explanation.

List every `O` or `~` row exactly once under Open decisions. Each bullet states the pending decision, next action, closure condition, and immediate consequence when it is not obvious. Omit `P` and `-` rows. Write `- None.` when no decision remains open or provisional.

List under Known limits every current restriction on action or conclusion that remains after a row is decided, plus any cross-cutting evidence limit. A `P` row can appear here because its rule is decided even when available evidence cannot support a stronger claim. Do not put a `P` row under Open decisions. Write `- None.` when no known limit remains.

For an older table-only `PROBLEM.md`, add a readable summary from the existing rules when that helps the current work. A faithful editorial change preserves row status, epoch and applicable review assurance. If the rules themselves are absent or conflicting, repair only the affected decisions under Review invalidation.

## Readability and review scope

A new reader should understand what can change, how it affects the objective, how outcomes are measured and what the next use permits. Assess that understanding on first framing, material changes to this story, or an assigned readability repair. Briefs orient the reader; clearly linked normative details may settle exact choices. Read them when needed rather than freezing a judgment made before evidence was available.

Do not require a fixed question list, a Brief-only reading sequence or repeated prose in several documents. Record only an ambiguity that could change the current action or conclusion as a required correction. When the full contract is consistent and understandable, wording, section placement and nonessential format improvements are advisory; the Coordinator may correct them without new technical review.

For a repair, inspect the changed meaning and affected dependencies and reuse applicable conclusions. An actual unresolved misunderstanding requires a focused check of that repair, not a new review of unchanged technical decisions. Do not repeat a completed readability check because another document or stage is being reviewed.

## Status and ownership

- `P` means result interpretation depends on a pinned contract.
- `~` means a documented working answer permits more framing work. Its Open decisions bullet names the pending decision and closure condition.
- `O` means a necessary point remains open. Its Open decisions bullet names the closing action or event.
- `-` means the Slot cannot affect comparison; its Contract gives the reason.

The Primary Framing Agent alone writes the problem Brief, Open decisions, and Known limits and adopts A-H or R1-R8 Contract cells, row status, normative rules, task terms, epochs, representation revisions, module-contract semantics, and downstream handoffs.

The Primary Framing Agent creates or selects each worker detail before delegation. The Research Agent writes only research evidence, sources, observations, candidate representations, risks, unknowns, recommendations, and explicitly proposed Contract text. The Grill Agent writes only user answers, authorizations, decision provenance, necessary context, and unresolved user choices. Each worker returns a packet that matches its durable record.

The Design Measurement Agent writes only its assigned nonnormative design sections. It is the sole professional author and reviser of measurement design. The Primary Framing Agent remains the sole normative adopter under [Contract projection](measurement-design.md#contract-projection), preserving the complete affected professional change without rewriting its meaning.

Research, grill, and measurement-design workers do not edit the problem Brief, Open decisions, Known limits, core Contract cells, row status, adopted normative rules, epochs, representation revisions, lifecycle assurance metadata, or normative module-contract content.

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

## Review notes

<New and reused conclusions, any accepted agent defaults, and material understanding gaps. Record only what this review needs; no question-by-question reconstruction is required.>

## R1: <short finding name>

- Affects: <Slot or cross-cutting rule>
- Work type: <research | grill | measurement-design | reframe | blocker>
- Evidence: <decisive evidence>
- Required action: <one action>
- Complete when: <checkable condition>
- Repair status: <open | complete | blocked>
```

A valid review contains exactly one allowed verdict and the evidence and scope supporting it. `PROCEED` has no open finding; advisory wording improvements do not prevent it. Every other verdict has at least one finding with all six fields. Existing Cold-read reconstruction sections remain historical review notes; neither that heading nor a new reconstruction is required.

`Required action` and `Complete when` define the repair work and its checkable completion, not the user reply. Keep the finding field set unchanged. When control returns to the user, derive the reply through [user-facing-return.md](user-facing-return.md).

The Review Agent initializes each finding to `open`. The Primary Framing Agent sets `complete` only when the completion condition holds and sets `blocked` only with an exact blocker.

Derive the verdict from work types: any `blocker` gives `BLOCKED`; otherwise, any `measurement-design`, `reframe`, or `grill` gives `REFRAME_REQUIRED`; otherwise, factual findings give `RESEARCH_REQUIRED`.

For a technical agent default, the Review Agent records independent acceptance of the exact proposed meaning in the review notes, not as a finding. A `~` row awaiting only this acceptance may be included in `PROCEED` when all substantive requirements pass. Before using that result for a handoff, the Primary Framing Agent pins the accepted row, preserves `Decision source: agent default`, updates Open decisions and checks that adoption changed no reviewed meaning. This mechanical adoption does not require a fresh review. Changed meaning needs only its affected review; a genuinely unresolved user-owned choice cannot be accepted as an agent default.

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

Use [Change impact and retained results](../../frontier-optimization/references/frontier-core.md#change-impact-and-retained-results) as the shared rule. Preserve each saved review as a judgment on its recorded inputs. A changed requirement needs review of its changed meaning and affected dependencies, not recertification of unrelated conclusions or historical results.

Set only the affected current contract scope to draft and remove assurance that would misrepresent the new meaning as already reviewed. Preserve the prior review and cite it for unchanged conclusions. Editorial changes, current-state summaries and workflow updates do not invalidate semantic assurance. A demonstrated readability defect requires review of that repair, not a new technical review of unchanged decisions.

Adopted normative sections in linked Slot documents remain part of the contract. Research, user-decision and measurement-design proposals remain nonnormative until adopted. Request comparability review only when an actual change affects the interpretation or comparison being proposed for retained evidence. Merely having retained results is not a trigger.

Update the Representation's current parent binding after an adopted parent revision. Review Representation only if its own requirements or a relied-on conclusion changed. A changed parent timestamp alone does not require that review.

## Epoch and `log.md`

An epoch identifies a set of comparable results, not the age of a document or workflow. Historical results retain their producing epoch. A change that leaves comparison meaning unchanged keeps the epoch.

When a proposed use crosses changed comparison meaning, the existing comparability branch resolves only the affected result or class:

- `unaffected`: the proposed use remains supported by its original evidence.
- `re-evaluated`: new measurement supports the proposed use; retain the old measurement as history.
- `voided`: the proposed comparison is unsupported; the original result remains valid within its established scope.

Increase the epoch when the comparison meaning changes, not when unrelated policy, workflow or bookkeeping changes. Record the changed meaning and affected use in the existing newest-first `log.md` entry. No migration report or exhaustive historical inventory is required.

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
- The Design Measurement Agent writes `Measurement design analysis — not adopted`, `Independent reconstruction — not adopted` when required, `Contract projection — not adopted`, and `Finding dispositions`. It can update `generated` and `sources`.

Proposed Contract text, candidate representations, and measurement-design projections remain nonnormative until the Primary Framing Agent adopts them.

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

For a core Brief, plain-language readability takes priority over sentence-length targets and formal labels. Explain the task and its relation to the objective; use linked normative details for exact rules instead of repeating them. Apply Readability and review scope to the current use, not a fixed reading order or a vocabulary test.
