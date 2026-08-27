# Strategic replan review

Load only to prepare or review a strategic replan selected by the [single direction resolver](learning-loop.md#integrated-direction-resolver). This file adds no resolver, interpretation stage, or user authorization.

Apply [Change impact and retained results](frontier-core.md#change-impact-and-retained-results) when parent rules or retained conclusions are involved. A parent version difference alone does not require Replan; an actual strategic allocation change still requires `REPLAN_READY` before dependent spend. Review the change and affected dependencies, reusing unaffected conclusions.

## Strategic replan review method

Before writing a verdict, the reviewer must:

1. verify every project snapshot identity, current parent authority, proposed decision root; reject workflow source, release, Skill, validator implementation, test, or source-module roots as replan inputs;
2. reconstruct the current adopted evidence from the planned B, result, W outcome, E, X, and cited artifacts;
3. check implementation, measurement, and comparison validity in that order;
4. verify the precommitted hypothesis, observed result, evidence-bounded mechanism grain, attribution limit, and complete parent-owned vector;
5. reconstruct considered diagnostic alternatives, result-to-action branches, stage cost plus unavoidable commitments, reachability, and recorded investment rationale under the single resolver; reject a dominated repeat or a changed persisted choice, not technical discretion among eligible alternatives;
6. apply the single integrated direction resolver and verify that the proposed Selection uses its first applicable row, affected scope, surviving authority, exact next action, and later-spend gates;
7. require another research round only when row 7 or 8 selects it, its result can arrive while the decision remains actionable, and its adopted industrial, academic, community, repository, and retained evidence is sufficient for the current allocation under a fixed search stop;
8. check technical eligibility before every V and preserve the user's actual choice;
9. reconcile Budget, protected reserves, Selection, B, and F2-F4 as one decision; reject any routine use of reserve or dependent strategic spend before unchanged adopted `REPLAN_READY`;
10. preserve separate design, implementation, claim, and parent gates without letting a specialized gate select another direction.

Return exactly `REPLAN_READY`, `REPLAN_REPAIR_REQUIRED`, `EVIDENCE_REQUIRED`, `PARENT_REVIEW_REQUIRED`, or `BLOCKED`. A positive result has no finding; every nonpositive result has at least one complete finding.

Only unchanged adopted `REPLAN_READY` copies the proposed project decision root into `FRONTIER.md` and Selection together with the reviewed strategic state. A nonpositive or stale review leaves the prior project chain and allocation unchanged and authorizes no dependent spend.

## Strategic replan packet

Create a new packet and review path for every attempt. Include no expected verdict or proposed repair.

```yaml
review_kind: replan
review_id: <unique identifier>
packet_path: <frontier/reviews/replan-<review-id>-packet.yaml>
packet_id: <review kind and id plus SHA-256 of canonical packet bytes with this field omitted>
snapshot_manifest: <frontier/reviews/replan-<review-id>-project-snapshot.yaml and identity>
snapshot_id: <immutable snapshot identity>
task_path: <canonical task path>
problem_epoch: <integer>
problem_generated_at: <ISO-8601 datetime>
representation_revision: <integer>
representation_generated_at: <ISO-8601 datetime>
representation_permitted: <exact reviewed text>
project_provenance:
  decision_root: <proposed frontier-decision-root-sha256 identity>
  prior_decision_root: <current decision root>
  governs: [<proposed strategic state and later decision objects created by this Replan>]
triggering_evidence: <adopted B, E, Q, X, D, and result locations and identities that caused the strategic decision>
route_set: <current or refreshed Q, every eligible T, exclusions and deferrals, shared assumptions, prerequisites, reopening evidence, and route-set-state identity>
direction_evidence: <compatible E sequence, governing prospective rules, current experiment conclusions, parent result vector, and context or action-window facts>
diagnostic_paths: <ordered alternatives, distinguishing outcomes, stage cost and unavoidable commitments, reachability, investment rationale and switching condition, or not applicable>
resolver_result: <evidence-state identity, first applicable row, exact direction resolution, next action, and blocker when applicable>
research_reconciliation: <row 7 or 8 Q with industrial, academic, community, repository, retained, and failure evidence plus search stop; or not applicable with reason>
supporting_evidence: [<Q, D, E, X, result, trace, join, or artifact identity>]
user_decisions: [<V identifiers and identities, or none>]
proposed_frontier_updates: <snapshot path and identity for proposed F2-F4 changes>
proposed_budget_update: <snapshot path and identity>
proposed_selection: <snapshot path and identity>
proposed_batches: [<snapshot paths, identifiers, and identities for Primary and Parallel B>]
design_and_implementation_state: [<applicable W, design review, development authorization, candidate, and implementation review identities>]
specialized_gates: [<design, implementation, measurement, integration, promotion, exposure, confirmation, claim, or parent gate and current state>]
assigned_review_path: <frontier/reviews/replan-<review-id>.md>
completion_check: <every replan requirement receives a verdict and every finding cites immutable snapshot evidence>
```

## Strategic replan artifact

Only `review-frontier` writes the assigned file.

```markdown
---
type: Optimization Frontier Strategic Replan Review
status: complete
review_id: <identifier>
review_result: <REPLAN_READY | REPLAN_REPAIR_REQUIRED | EVIDENCE_REQUIRED | PARENT_REVIEW_REQUIRED | BLOCKED>
reviewed_by: review-frontier/1
reviewed_at: "<ISO-8601 datetime>"
snapshot_packet: <path and identity>
generated: { by: review-frontier/1, at: "<ISO-8601 datetime>" }
---

# FRONTIER STRATEGIC REPLAN REVIEW: <effort name>

Result: <allowed result>
Triggering evidence: <adopted records, targets, and identities>
Reviewed snapshot: <packet path and identity>
Reviewed at: <ISO-8601 datetime>

## Readiness checks

- Parent bindings, permitted scope, and authority: <pass or findings>
- Result, implementation, measurement, and comparison validity: <pass or findings>
- Technical hypothesis, observed result, and evidence-bound mechanism grain: <pass or findings>
- Attribution limit, measurement meaning, and full parent result vector: <pass or findings>
- Decision-relevant unknowns and selected information source: <pass or findings>
- Considered diagnostic alternatives, reachability, recorded ordering, and repeat prevention: <pass or findings>
- Research coverage and stop rule: <pass or findings>
- Route-set state, evidence-state identity, and first applicable resolver row: <pass or findings>
- Technical eligibility, V records, and recommendation fidelity: <pass or findings>
- Budget, reserve, Selection, B, and stop rules: <pass or findings>
- Deterministic next action and `REPLAN_READY` dependent-spend boundary: <pass or findings>
- Specialized review boundaries: <pass or findings>

## Findings

### Finding 1: <omit when REPLAN_READY>

- Result effect: <REPLAN_REPAIR_REQUIRED | EVIDENCE_REQUIRED | PARENT_REVIEW_REQUIRED | BLOCKED>
- Affects: <paths, records, or fields>
- Requirement: <exact requirement>
- Observed: <snapshot fact>
- Evidence: <snapshot identities>
- Required correction: <observable condition; no repair text>
```
