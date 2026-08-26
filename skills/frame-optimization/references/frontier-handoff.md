# Framing-to-Frontier Handoff

This interface connects the repository's two Coordinator stages. `frame-optimization` owns and emits the handoff. `frontier-optimization` validates and consumes it. Each Coordinator writes only its own stage's records. Frontier may delegate an affected parent repair to Framing within the existing user grant, then consume the adopted handoff.

## Stage selection

| Durable state | User entry | Allowed result |
|---|---|---|
| Problem or representation is absent, stale, nonpositive, or still open | `frame-optimization` | Repaired framing state, exact blocker, or reviewed handoff |
| Current representation review is `PROCEED_EXPLORATORY` or `PROCEED_MODULAR` and no parent conflict exists | `frontier-optimization` | Frontier Entry, campaign action, closeout, recovery, or package result |
| Frontier detects a parent requirement affecting the next action | `frontier-optimization` delegates to `frame-optimization` within the grant | Adopted scoped repair and updated binding, or an exact dependent-action blocker |

The user's task selects the initial Coordinator. Technical stage transitions within its grant need no new user question; workers still return to their assigned owner.

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
- Slot H harness, baseline, evaluator, and measurement identities.

`PROCEED_EXPLORATORY` permits only the reviewed bounded whole-candidate scope. `PROCEED_MODULAR` adds only the exact modules and operations named in `Permitted`. A nonpositive, stale, malformed, incomplete, or mutable review emits no handoff.

## Frontier admission

Bind the current adopted parent and handoff for the next action, retaining saved reviews for the scope they actually established. Use [Change impact and retained results](../../frontier-optimization/references/frontier-core.md#change-impact-and-retained-results) for revisions: inspect the changed meaning and its dependencies, not every historical object. A missing applicable requirement pauses only dependent work. A workflow-only update does not invalidate the project handoff, and workflow bytes remain outside project identities.

Admission copies the handoff bindings into Frontier state without changing their meaning. A positive handoff defines permitted search work; it does not authorize candidate development, spend, measurement, integration, incumbent use, promotion, production changes, or claims. Frontier applies its own Entry and lifecycle gates for those consequences.

The handoff is complete when a fresh reader can identify the active Coordinator, reproduce every binding, and reach the same admission result without conversation history or a global Skill installation.

## User return

After validating the technical handoff, apply [user-facing-return.md](user-facing-return.md). The technical handoff contract above remains complete without the user reply.
