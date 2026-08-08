---
name: grill-optimization
description: Interview the user for the user-owned decisions an optimization frame needs. Use when frame-optimization delegates an unresolved decision point, or when an A-H contract row waits on a preference, authority, private context, or value choice that evidence cannot settle.
---

# grill-optimization

Resolve the **user-owned decisions** of an optimization framing task — a directory under `docs/skills/optimization/<task-slug>/` holding a `PROBLEM.md` A–H contract. Decisions are the user's; facts are yours.

## Inputs

Require the canonical task path — confirm it resolves under `docs/skills/optimization/` and contains `PROBLEM.md`. Take the caller's decision point when given; otherwise sweep the `O` and `~` rows for eligible points.

When a previous session ended with an unrecorded answer, confirm only that answer before anything else; a reconstruction from a summary is not a record.

## Eligibility gate

Put a point to the user only when all four hold:

1. it is unresolved;
2. the answer can change legality, ranking, success, measurement, or feasibility;
3. available evidence cannot answer it;
4. it depends on private context, authority, preference, or a value choice.

A point that fails condition 3 or 4 is a fact: investigate it yourself or delegate it to `research-optimization`, and let only its downstream decisions wait on the result.

## Interview

Map the eligible decisions as a **design tree**: every decision branches into the decisions that hang off it. The **frontier** is every decision whose prerequisites are settled. Ask one question per turn — the frontier's most upstream decision — then wait for the answer.

```
❓ **<decision title>** — <the decision at stake>

Evidence: <what is known, labeled, with source locators>
Alternatives: <the serious options>
➡️ Recommendation: <the evidence-backed answer>
Consequence: <what changes depending on the answer>
```

**Return, record, then continue.** After each material answer, return the Slot, answer, decision source, and Contract effect to the Primary Framing Agent. The Primary Framing Agent records the answer under [task-documents.md](../frame-optimization/references/task-documents.md) before the next question. An explicit user answer can pin (`P`) its row. Each durable decision reshapes the tree; recompute the frontier.

## When the user cannot decide

For a reversible choice, recommend the evidence-backed default with its evidence. The Primary Framing Agent records it provisional (`~`) with `Decision source: agent default`. Only explicit user confirmation or independent review pins a default.

Block — rather than default — when the gap is missing authority, a private fact, or a safety boundary; record in the row's open action what unblocks it.

## Done

The interview is done when the frontier is empty and the Primary Framing Agent has recorded every decision as answered, defaulted-provisional, or blocked with its unblocking condition.
