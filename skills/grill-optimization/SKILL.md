---
name: grill-optimization
description: Ask one user-owned optimization decision or authorization question, record the answer in a coordinator-selected detail, and return it without adopting Contract changes. Use when frame-optimization delegates an A-H or R1-R8 preference, private fact, authority choice, authorization, or value judgment that evidence cannot settle.
---

# grill-optimization

Ask one exact user-owned question for the Primary Framing Agent. Record the user's answer in one selected detail, then return one matching decision packet.

## Inputs

Require these inputs from `frame-optimization`:

- the canonical task path under `docs/skills/optimization/<task-slug>/`;
- one A-H, R1-R8, or cross-cutting target;
- one exact decision or authorization question;
- the evidence, serious alternatives, recommendation, and consequence needed to answer it;
- one exact existing Slot or representation detail path for the decision record.

Confirm that both paths remain under the selected task and that `PROBLEM.md` exists. Do not create a destination, sweep open rows, select the next decision, or expand one question into an interview plan.

When an input is missing or ambiguous, return the missing input to the coordinator. Do not invent task context.

## Eligibility gate

Ask the user only when all conditions hold:

1. the point is unresolved;
2. the answer can change legality, ranking, success, measurement, feasibility, permitted search scope, representation loss, module responsibility, or coordination cost;
3. available evidence cannot settle it;
4. the answer depends on private context, authority, preference, authorization, or a value choice.

If a condition fails, return `NO USER DECISION` with the failed condition. Do not investigate facts or delegate work to another skill.

## Ask one question

Use this format, then wait:

```text
Question: <one decision or authorization>
Evidence: <what is known, with labels and locators>
Alternatives: <serious options>
Recommendation: <evidence-backed option>
Consequence: <what changes with the answer>
```

Do not ask the user to judge technical completeness. Do not combine unrelated decisions.

## Record and return the answer

After every material user answer, write a concise faithful record before continuing or returning. Follow [task-documents.md](../frame-optimization/references/task-documents.md) for A-H details and [representation-documents.md](../frame-optimization/references/representation-documents.md) for R1-R8 details.

Write only:

- the user's answer;
- the user's authorization, denial, or conditions;
- decision source and necessary context;
- unresolved user choices.

Update `generated`. Do not store a full transcript, secrets, or unnecessary private content.

Return exactly one packet that matches the durable record:

```text
USER DECISION
Task: <canonical task path>
Target: <A-H | R1-R8 | named cross-cutting point>
Question: <exact delegated question>
Decision status: decided | authorized | denied | deferred | unable
User answer: <faithful concise answer>
Authorization: granted | denied | not applicable
Conditions: <user-stated conditions or none>
Decision source: user
Decision context: <minimum context needed to interpret the answer>
Unresolved user choices: <remaining choices or none>
Decision record: <canonical detail path>
```

When the user cannot decide, use `Decision status: unable` and preserve the response and unresolved choice. Do not adopt an agent default. The Primary Framing Agent decides whether an evidence-backed reversible default is permitted.

When the user defers, denies authorization, or lacks authority, preserve that exact distinction. Do not translate it into a Contract status or blocker.

## Protected content

Do not edit:

- `PROBLEM.md` or `REPRESENTATION.md` Brief, Open decisions, or Known limits;
- `PROBLEM.md` or `REPRESENTATION.md` Contract cells;
- A-H or R1-R8 row status;
- adopted normative rules in any detail;
- problem epochs or `representation_revision`;
- `status`, `verified`, or `review_scope`;
- normative module-contract content;
- logs, review files, or downstream handoffs.

Do not write any file except the selected decision detail. In that detail, change only the permitted decision record and `generated`.

Do not research factual questions, choose defaults, interpret the answer into Contract wording, pin a row, or coordinate the next action. The Primary Framing Agent validates the record and packet, then makes every normative decision.
