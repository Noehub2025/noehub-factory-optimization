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

Only `PROBLEM.md` is always in context. Representation work also loads `REPRESENTATION.md`. Create each optional file only when its content is necessary.

Keep existing project documents in place. Link them as sources; publish or rewrite them only under separate authorization.

## Open Knowledge Format rules

Every Markdown concept document starts with valid YAML frontmatter containing nonempty `type` and `status`. Use `status: draft` before readiness and `status: stable` only after independent review.

Use `generated` for the last meaningful writer and time. Use `verified` only for the current independent reviewer and time. Use standard Markdown links and list load-bearing provenance under `sources`.

Do not create `index.md`. `log.md` uses the reserved Open Knowledge Format date-and-entry structure and has no frontmatter.

Git history can support an audit. File-based recovery must not depend on Git history.

## `PROBLEM.md` template

Keep the body to one title, one A-H table, one status key, and one epoch rule block. The body has at most 35 nonblank lines.

```markdown
---
type: Optimization Problem
title: <effort name>
description: Defines the comparison contract for <effort name>.
tags: [optimization]
status: draft
epoch: 1
updated: <ISO-8601 date>
generated: { by: frame-optimization/1, at: <ISO-8601 datetime> }
---

# PROBLEM: <effort name>

| # | Slot | St | Contract | Detail |
|---|---|---|---|---|
| A | Object/space | O | <contract or closing action> | |
| B | Solutions | O | <contract or closing action> | |
| C | Constraints | O | <contract or closing action> | |
| D | Objective | O | <contract or closing action> | |
| E | Evaluation | O | <contract or closing action> | |
| F | Resources | O | <contract or closing action> | |
| G | Interaction | O | <contract or closing action> | |
| H | Measurement | O | <contract or closing action> | |

St: `P` = pinned; `~` = provisional; `O` = open; `-` = not applicable.

Rules: Each result records `epoch`. Compare results only within one epoch.
When retained results exist, review each change to a `P` contract. Record the disposition in `log.md`.
```

Use one or two sentences in each Contract cell. Put formulas, quantifiers, distributions, evidence, and detailed actions in a linked Slot document when two sentences are insufficient.

## Status and ownership

- `P` means result interpretation depends on a pinned contract.
- `~` means a documented provisional answer permits more framing work.
- `O` means a necessary point remains open; its Contract names the closing action or event.
- `-` means the Slot cannot affect comparison; its Contract gives the reason.

The Primary Framing Agent alone adopts A-H or R1-R8 Contract cells, row status, normative rules, task terms, epochs, representation revisions, module-contract semantics, and downstream handoffs.

The Primary Framing Agent creates or selects each worker detail before delegation. The Research Agent writes only research evidence, sources, observations, candidate representations, risks, unknowns, recommendations, and explicitly proposed Contract text. The Grill Agent writes only user answers, authorizations, decision provenance, necessary context, and unresolved user choices. Each worker returns a packet that matches its durable record.

Research and grill workers do not edit core Contract cells, row status, adopted normative rules, epochs, representation revisions, lifecycle assurance metadata, or normative module-contract content.

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

## R1: <short finding name>

- Affects: <Slot or cross-cutting rule>
- Work type: <research | grill | reframe | blocker>
- Evidence: <decisive evidence>
- Required action: <one action>
- Complete when: <checkable condition>
- Repair status: <open | complete | blocked>
```

A valid review contains exactly one allowed verdict. `PROCEED` has no open finding. Every other verdict has at least one finding with all six fields.

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

A meaningful change can alter legality, ranking, success, measurement, resource feasibility, or result interpretation. Spelling, links, and clearer text that keep the same contract carry no invalidation; changes only to review metadata do not invalidate themselves.

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

- One or two sentences per Contract cell; each sentence carries one instruction in at most 25 words.
- An `O` row's cell states the action or event that closes it.
- A `-` row's cell gives the reason the Slot does not apply.

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
5. Limit procedural sentences to 20 words.
6. Limit descriptive sentences to 25 words.
7. Write one instruction in each sentence.
8. Keep one topic in each paragraph.
9. Keep each paragraph to six sentences or fewer.
10. Use American English spelling.
11. Do not use Latin abbreviations.
12. Replace an ambiguous pronoun with its noun.

File paths, code identifiers, formulas, and exact quotations keep their original form. Optimization terms are project technical terms: define a local term in its Slot document, and a term used by multiple Slots in `terms.md`, linked from where it is used.
