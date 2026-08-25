# Frontier Review Branches

Use this registry only to select the one review contract named by an immutable review packet. The selected action contract owns the review method, packet schema, allowed verdicts, and artifact schema. Do not combine branches or infer a review kind from conversation context.

## Branch registry

| `review_kind` | Action contract | Load with it | Branch boundary |
|---|---|---|---|
| `entry` | [Entry review](entry-review.md) | [Entry and planning](entry-and-planning.md), [Campaign cycle](campaign-cycle.md), [Campaign state](campaign-state.md), [Planning records](planning-records.md), and [Batch interface](batch-interface.md) | Review Entry or authorization readiness only. For code-bearing work, also load [Entry code planning](entry-code-planning.md), [Candidate lifecycle](candidate-lifecycle.md), and only the W/design inputs cited by the packet. |
| `replan` | [Learning loop](learning-loop.md#strategic-replan-review-method) | [Campaign state](campaign-state.md), [Planning records](planning-records.md), and [Evidence records](evidence-records.md) | Review the strategic replan only. Load a specialized design or implementation contract only when the snapshot cites its existing verdict as current authority. Never complete a claims branch here. |
| `design` | [Design review](design-review.md) | [Planning records](planning-records.md), [Work plan](work-plan.md), and [Technical design](technical-design.md) | Review one `module` or `system` design contract. `direct` has no design review. |
| `implementation` | [Implementation review](implementation-review.md) | [Planning records](planning-records.md), [Batch interface](batch-interface.md), and [Candidate lifecycle](candidate-lifecycle.md) | Review one exact all-pass prepublication realization or recovery reuse. Load only the W/design inputs cited by the packet. Do not publish, measure, integrate, promote, or use the candidate. |
| `claims` | [Claim review](claim-review.md) | [Campaign state](campaign-state.md), [Planning records](planning-records.md), [Evidence records](evidence-records.md), [Claim records](claim-records.md), and [Learning loop](learning-loop.md) | Review every named C and write only the assigned claims-review artifact. Do not write A or X, change campaign status, or decide the later route. |

## Selection checks

1. Match `review_kind` to exactly one row. Return `BLOCKED` for an absent, unknown, or conflicting kind.
2. Load the action contract and every common reference named in that row. Load conditional inputs only when the row permits them and the immutable packet cites their exact identities.
3. Verify that the snapshot contains the selected action contract, its required normative inputs, and stable identities for every parent, rule, bound, implementation input, measurement, and design input the branch must interpret.
4. Do not load another branch's review method. When the packet cites another branch's completed verdict as authority, inspect only that immutable verdict and the inputs needed to verify its freshness.
5. Return `BLOCKED` when a required normative source, snapshot input, identity, or assigned path is missing, inconsistent, or mutable during review.

Selection is complete when one branch owns the review, all permitted references are known before judgment begins, and no unselected review method is in scope.
