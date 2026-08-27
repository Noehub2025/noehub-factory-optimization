---
name: grill-frontier
description: Ask one Frontier tradeoff or authorization question that only the user can decide, including the campaign baseline, design, interface, migration, cost, risk, dependency, reversibility, maintenance, operations, deadline, exploration, or permission to proceed. Use when `frontier-optimization` has created the target and supplied technically eligible options or one exact authorizable object with evidence.
---

# Grill Frontier

Collect one Coordinator-assigned user choice. Ask only the question needed for the named decision record.

Apply [User decisions](../frontier-optimization/references/user-decisions.md) before asking. Return an already recorded applicable answer without repeating the question. A technical choice or new B identity alone is not a user decision.

## Execute the assignment

1. Require `decision_kind: tradeoff | authorization`, exact `decision_root`, a reserved V identifier, exact decision, evidence, affected records, conditions, reconsideration trigger, and result-packet path. New packets must not include workflow release or implementation identities. For a post-result strategic tradeoff, also require the triggering adopted evidence and technically filtered options that the proposed replan cannot resolve from evidence. For `tradeoff`, require at least two technically eligible alternatives and return `BLOCKED` if the assignment asks the user to judge technical eligibility. For `authorization`, require one exact object, immutable identity, scope, reviewed basis, and the consequences of authorize, decline, and conditional authorization; do not require two technical alternatives. When that object names a concrete B packet, require unchanged finding-free `AUTHORIZATION_READY` for the exact target, reproduce the structural packet preflight, Entry schema, snapshot, and live-input identities, and require all bytes to match before presenting the question. Return `BLOCKED` before asking when any check is missing, failed, stale, or mismatched.
2. Verify the typed project provenance chain, then use the installed shared worker interface. Workflow source closure is checked only when the workflow release is published or installed. Historical version 1 objects are audit evidence and never current user-decision assignments.
   The installed workflow may change between invocations. That change never changes this assignment, its project identity, or its result path; apply the current interface only to the unchanged project facts.
3. Present the decision in plain language. For `tradeoff`, present the evidence, technically eligible alternatives, recommendation when supported, uncertainty, consequence of each choice, and reconsideration event. For a campaign baseline choice, explain how each alternative supports later optimization without implying that the baseline itself must be the strongest eventual solution. For a design choice, explain the user-visible cost, lock-in, reversibility, maintenance, operational, interface, migration, and risk differences that actually vary; leave local reversible implementation details with the design's bounded executor choices. For `authorization`, present the exact object, identity, scope, review state, known limits, next action, and consequences of authorize, decline, or attach conditions; do not reopen the technical choice unless the user asks.
4. Ask one question. Record the user's exact answer, decision root, its conditions, affected work, consequence, reconsideration trigger, readiness-review identity, target identity, and any superseded V identifier in the assigned result packet. Do not ask another question in the same run. Do not claim that a conditional answer changed the reviewed object; the Coordinator classifies it as exact, declined, or review-required.

The assignment is complete only when the answer is clear enough for the Coordinator to check and record as one V record.

## Authority

The user can choose among technically eligible tradeoffs and can authorize, decline, condition, delegate, or withdraw work within their authority. A user answer cannot legalize invalid work, waive measurement, prove an assumption, or strengthen a claim. The answer changes campaign state only after the Coordinator writes the V record. Only the Coordinator may change allocation or other campaign records.
