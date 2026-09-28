# Framing-to-Frontier Handoff

This interface connects the repository's two Coordinator stages. `frame-optimization` owns and emits the handoff. `frontier-optimization` validates and consumes it. Each Coordinator writes only its own stage's records. Frontier may delegate an affected parent repair to Framing within the existing user grant, then consume the adopted handoff.

## Stage selection

| Durable state | User entry | Allowed result |
|---|---|---|
| Problem or representation is absent, stale, nonpositive, or still open | `frame-optimization` | Repaired framing state, exact blocker, or reviewed handoff |
| Current representation review is `PROCEED_EXPLORATORY` or `PROCEED_MODULAR` and no parent conflict exists | `frontier-optimization` | Frontier Entry, campaign action, closeout, recovery, or package result |
| Frontier detects a parent requirement affecting the next action | `frontier-optimization` delegates to `frame-optimization` within the grant | Adopted scoped repair and updated binding, or an exact dependent-action blocker |

The user's task selects the initial Coordinator. Technical stage transitions within its grant need no new user question; workers still return to their assigned owner.

## Stable contract and live state

Keep content at the scope where it governs work:

| Content | Owner |
|---|---|
| Real objective and success meaning, external evaluation mechanism, legal solution space and user boundaries | Problem: D retains objective-side success; E retains the external evaluation and applicable aggregation meaning |
| Search forms, substantive decisions they express, evaluation translation and search rules | Representation |
| Reusable comparison method, evidence meaning, applicability and use limits | Measurement definition referenced by H |
| Current realization, exact inputs, schedule, observation window, local engineering arrangements and recovery | W or Batch |

A fixed reference, dataset or parameter may define one reusable protocol without becoming the only permitted condition for all search. An instance change stays in the Batch while the method's meaning, applicability and supported use remain intact; a change to those premises goes to the existing professional owner. Keep D's objective separate from a particular diagnostic's result classes, and R8's search rules separate from its execution sequence. Frontier owns live campaign facts:

When updating the current projection, D retains success meaning and E retains the evaluator's applicable aggregation and changing-value behavior; H points to reusable measurement meaning. Exact schedules, result branches and current candidates remain with their W or Batch. Correct an obsolete instance presented as the current contract without discarding its historical evidence or reopening unaffected reviews. Supply these adopted sources separately from a proposed route's recommendation when the next investment is prepared. Refresh a source fact when it could change that decision, not by a universal expiration timer.

| Live fact | Current owner |
|---|---|
| Generation, campaign status and Selection | `FRONTIER.md` `current_state` |
| User decisions and Permission | V records, citing the adopted Frame source when applicable |
| Actual and unknown spend, reservations, balance, adopted results, and their decision use | Budget and E records in `frontier/ledger.md` |
| Batch limits, Attempts, actual consumption and Consequences | current B record |
| Research-basis transition and continued work | existing Frontier X and `current_state` under [Research-basis transitions](../../frontier-optimization/references/frontier-core.md#research-basis-transitions) |
| Whole-campaign closeout and its recovery entry | latest complete `CLOSEOUT_COMPLETE` |

Current retained-result status means adoption, elite or survivor status, current Selection, or intended next use. It does not include the stable reference-baseline definition, comparison meaning, result-comparability rules, search-state compatibility, or old-work reuse rules; those remain with Framing.

Do not copy live values into normative Frame content or use them to decide parent freshness. A historical handoff or Frame explanation that contains such values remains a point-in-time record. When the typed Frontier owners agree, a difference confined to that nonauthoritative explanation is an advisory under [Frontier finding effects](../../frontier-optimization/references/finding-effects.md), not a parent mismatch. It does not invalidate a handoff or review, require reframing or reauthorization, or block Frontier work.

Only a changed durable parent meaning or concrete contrary evidence can affect a parent conclusion. Leave historical summaries unchanged unless one actually misleads the current read or the owning document is already changing for a valid reason; this rule creates no mass cleanup, rebinding, or review work.

## Research knowledge in the handoff

At initial handoff, a material framing change or an actual applicability challenge, use relevant retained research to explain what changes the pending search judgment. A limitation that undermines the current method goes to its professional owner rather than only becoming a disclaimer. Unknowns that do not affect the choice need no new research. Frontier consumes this reasoning through [Investment comparison](../../frontier-optimization/references/learning-loop.md#route-investment-ordering), including theory-grounded exploration without promoting an unsupported proxy conclusion. Use the existing handoff and decision work; this adds no per-result analysis, research checkpoint or review.

## Handoff contract

Emit the current handoff from applicable positive conclusions and adopted changes. Cite each saved review for its actual scope; a new handoff does not claim an old review signed changed bytes. Bind:

- canonical task path;
- parent problem epoch and `generated.at`;
- representation revision and `generated.at`;
- positive review result and exact `Permitted` text;
- reviewed-path manifest and review identity;
- canonical evaluation representation and each permitted search representation;
- permitted operations, feedback, survivor selection, and stopping rules;
- coverage, reachability, redundancy, and claim limits;
- applicable module contracts, interfaces, coupling, resource partitions, and global evaluation rules;
- retained search-state dispositions; and
- Slot H harness, baseline, evaluator, and measurement identities; and
- adopted user decisions that constrain Frontier objective, total resources, access or protected Consequences.

`PROCEED_EXPLORATORY` permits only the reviewed bounded whole-candidate scope. `PROCEED_MODULAR` adds only the exact modules and operations named in `Permitted`. A nonpositive, stale, malformed, incomplete, or mutable review emits no handoff.

## Frontier admission

Bind the current adopted parent and handoff for the next action, retaining saved reviews for the scope they actually established. Read live campaign facts from the owners above. Use [Change impact and retained results](../../frontier-optimization/references/frontier-core.md#change-impact-and-retained-results) for revisions: inspect the changed meaning and its dependencies, not every historical object. A missing applicable requirement pauses only dependent work. A workflow-only update or stale live-state explanation does not invalidate the project handoff, and workflow bytes remain outside project identities.

Admission references the handoff bindings without changing their meaning. A positive handoff does not select a route, allocate a Batch, prove technical readiness, establish measurement validity, promote a result or approve a claim. Within its adopted objective, total resources, access and protected-Consequence boundaries, Frontier makes those technical and allocation decisions without another user question. When a Batch needs a V handle for an already adopted Frame decision, the Coordinator records one operational reference to that source; V cannot reinterpret or widen it.

The handoff is complete when a fresh reader can identify the active Coordinator, reproduce every binding, and reach the same admission result without conversation history or a global Skill installation.

## Continue or return

Use the current request and applicable [User decisions](../../frontier-optimization/references/user-decisions.md) to continue within the existing scope:

- For work delegated by Frontier, return the adopted handoff or exact dependent-action blocker to that Coordinator. It adopts the result and resumes its existing router.
- For a task started in Frame whose request includes subsequent optimization, continue through [Frontier Optimization](../../frontier-optimization/SKILL.md) after the handoff is ready. Frontier selects the next action through its existing router.
- For a framing-only or report-only request, or an explicit pause, return the requested outcome to the user. Preserve the user's stated limits.

Reuse applicable handoffs, reviews and user decisions for their established scope. Internal handoff needs no new user instruction or permission record. Technical work still follows the existing readiness and recovery routes; a technical blocker goes to its owner while other permitted work continues.

Apply [user-facing-return.md](user-facing-return.md) only when the requested scope is complete, the user requested a pause or report, a user-owned input is missing, or no safe reachable action remains. The technical handoff contract above remains complete without the user reply.
