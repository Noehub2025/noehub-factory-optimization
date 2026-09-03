# Current Frontier Entry review

Load only when the next actual Consequence needs independent Entry judgment. Same-B preparation, working changes, local repair, harmless checks and technical design revision use [Boundary-preserving continuation](batch-current.md#boundary-preserving-continuation) without another Entry.

Read [Historical Entry formats](entry-review-legacy.md) only when the retained object actually contains those fields.
Classify the effect of any current finding with [Finding effects](finding-effects.md).

## Review subject

Keep the proposed decision mutable until ordinary deterministic checks pass. Save the complete subject in Git and assign one R with:

- the full commit and repository-relative subject paths;
- `review_kind: entry`;
- the next actual Consequence and affected scope;
- applicable parents, adopted evidence, Campaign, Selection and Budget;
- the Batch definition and expected Consequences;
- applicable governing campaign limits, protected reserve and strategic allocation;
- applicable R and V references;
- the current W or Measurement Definition, including any interpretation-bearing resource ceiling, only when the action needs it; and
- one exclusive review path and completion check.

Do not create a content root, decision node, attestation root, authority node, packet, snapshot, adoption identity or validation identity. Workflow source, validator versions, deployment locations and historical identity fields are not project inputs.

## Review method

Judge only whether the proposed decision is technically coherent and reachable under its cited parents, evidence, Selection, Budget, Reviews and existing user boundaries. Check:

- that the resolver result and Selection support the proposed allocation;
- that protected reserve is not assigned to routine work;
- that prerequisites are evidence-backed or explicitly tested before dependent work;
- that the Batch independently judged result, scope and expected Consequences are coherent;
- that the next action fits the governing campaign limits, protected reserve and strategic allocation;
- that the next action has the required technical Review and Measurement Definition;
- that existing V covers every protected Consequence, or that the exact missing user boundary is identified; and
- that result branches, claim limits and recovery conditions match the evidence the action can produce.

A positive Review establishes Entry readiness only. It does not create Permission, execute work, allocate another B, create E or strengthen a claim. Exact Batch operational caps are runtime controls and may be revised without repeating Entry while the reviewed decision, governing limits, protected reserve, strategic allocation, Measurement Definition and expected Consequences remain unchanged. When an existing V applies, the Coordinator continues without asking the user. When a genuine user boundary is missing, apply [User decisions](user-decisions.md) and ask only for that boundary.

Use these current outcomes:

- `ENTRY_READY`: the reviewed decision can proceed through its existing owners;
- `ENTRY_REPAIR_REQUIRED`: the same mutable decision needs a named correction;
- `USER_DECISION_REQUIRED`: one exact user-owned boundary is missing; or
- `BLOCKED`: one exact external fact or incompatible parent prevents judgment.

## Entry repair review

Repair the current draft inside the same B while its independently judged result and user boundaries remain applicable. Preserve the previous Git version and R. Save the corrected complete subject and review the changed dependencies and affected conclusions; reuse unaffected conclusions without a compatibility report or repeated checks.

Intermediate edits create no review object, replacement directory family, new B, Generation or Permission. A corrected technical contract receives the applicable technical Review. A new user answer is required only when the correction crosses the boundary in [User decisions](user-decisions.md).

Entry review is complete when the next affected action is `ENTRY_READY`, has one exact missing user decision, or has one evidence-backed blocker. It must not create a second current execution or authorization contract.
