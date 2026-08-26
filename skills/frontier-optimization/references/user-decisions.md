# User decisions and delegated work

Use this rule when deciding whether to ask the user, preparing Entry, or checking permission for the next consequence. It owns the question boundary for framing and Frontier; technical readiness and execution identities remain with their existing owners.

## Ask only for a user-owned decision

The user decides:

- The objective, total budget, accessible resources and important constraints.
- A genuine tradeoff in cost, privacy, maintenance, reversibility or other value that existing preferences and evidence do not settle.
- Permission for paid work, external submission, sensitive access or irreversible effects that the existing grant does not already cover.

Within that meaning, the Coordinator chooses research, routes, technical design, local implementation and repair, checks, measurement, result adoption and B or Generation progression. Novelty, technical uncertainty, a new identifier, a changed working path or a review checkpoint is not a user decision. Resolve technical questions with evidence and the assigned specialist, not a preference poll. Review readiness never grants permission by itself.

Before asking, inspect the current user request and applicable recorded decision. If they already settle the question, record or reuse that answer through its existing adoption path; do not ask it again. If a real boundary is missing, ask once for that boundary and its intended continuing scope, not for each dependent internal action. Continue other permitted work while an affected action waits.

## Keep the user grant separate from an execution object

A user grant states allowed work and consequences; an Entry decision fixes one realization of that work. A saved realization can change while the original grant remains applicable. Preserve old versions and evidence. Use the existing Entry `spend-readiness` branch when a new realization needs review but fits an adopted grant. Same-B work that already fits its packet uses Batch continuation, with no additional Entry or user question.

When permission is newly requested, the existing `frontier-project-authorization-target/1` may explicitly state `continuation: within-scope`. Its scope and user-facing question must explain the continuing objective, resource and access limits, permitted effects and stop boundary. This permits only actions within that meaning, including later B or Generation work when stated. Do not use a per-B ceiling as a fresh allowance on every reuse. Ordinary exact-only targets omit this field or use `exact-only`; never add it to a historical target.

For a replacement Entry under a continuing grant:

- Keep the new batch plan and existing `frontier-project-spend-gate/1` for the current B.
- Set the spend gate's `authority_target` to the original user target. Its `affected_scope` and `later_spend_gate` describe this action and why it fits, including cumulative consumption and changed consequences.
- Set `authorization_basis` to the three logical names `target`, `answer` and `adoption` under `project/decision/authority/`. Include those existing original records in the complete Git-referenced subject, not newly invented answers.
- Preparation binds their identities and raw bytes and derives the original scope and limits. The Entry reviewer judges semantic fit, unresolved conditions, current withdrawal, cumulative Budget, access and effects. The adapter does not interpret natural-language permission or prove live affordability.
- An adopted `ENTRY_READY` binds the new decision and its own attestation to a new execution authority through the existing writer. Cite the original V; create no new V or user question. Never attach an old authority node or attestation to changed project content.

The answer record uses the existing `decision_id`, `target_id`, `exact_answer`, `answer_classification: authorize` and `conditions: []`. Its adoption binds the original target identity and file digest, answer file digest and authority identity. Conditional or ambiguous answers use the existing clarification/adoption path before reuse, not an inferred wider grant.

At execution, use the existing current-authority, budget, reservation, input and effect checks. Preserve all earlier consumption, unknown effects and protected reserve across repairs and generations. No extra receipt, per-action grant register, permission service or repeated check is introduced.

An exact-only historical answer remains exact-only. A workflow update cannot widen it. Changing the objective, cumulative ceiling, resource access, permitted effects or a genuinely user-owned tradeoff requires the relevant new user decision. Technical readiness, scientific validity and claim limits still apply within granted permission. Continuing permission does not override a binding stop rule, withdrawn request or exhausted cumulative budget; a new Generation cannot reset any of them.
