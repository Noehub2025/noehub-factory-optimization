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

Frame documents and the handoff bind durable problem, representation, comparison, resource, feedback, stop, claim, and reuse rules. Frontier owns live campaign facts:

| Live fact | Current owner |
|---|---|
| Generation, campaign status and Selection | `FRONTIER.md` `current_state` |
| User decisions and Permission | V records, citing the adopted Frame source when applicable |
| Actual and unknown spend, reservations, balance, adopted results, and their decision use | Budget and E records in `frontier/ledger.md` |
| Batch limits, Attempts, actual consumption and Consequences | current B record |
| Completed Generation and its recovery entry | latest complete `CLOSEOUT_COMPLETE` |

Current retained-result status means adoption, elite or survivor status, current Selection, or intended next use. It does not include the stable reference-baseline definition, comparison meaning, result-comparability rules, search-state compatibility, or old-work reuse rules; those remain with Framing.

Do not copy live values into normative Frame content or use them to decide parent freshness. A historical handoff or Frame explanation that contains such values remains a point-in-time record. When the typed Frontier owners agree, a difference confined to that nonauthoritative explanation is an advisory under [Frontier finding effects](../../frontier-optimization/references/finding-effects.md), not a parent mismatch. It does not invalidate a handoff or review, require reframing or reauthorization, or block Frontier work.

Only a changed durable parent meaning or concrete contrary evidence can affect a parent conclusion. Leave historical summaries unchanged unless one actually misleads the current read or the owning document is already changing for a valid reason; this rule creates no mass cleanup, rebinding, or review work.

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

## User return

After validating the technical handoff, apply [user-facing-return.md](user-facing-return.md). The technical handoff contract above remains complete without the user reply.
