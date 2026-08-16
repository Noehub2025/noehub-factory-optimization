# Framing-to-Frontier Handoff

This interface connects the repository's two Coordinator stages. `frame-optimization` owns and emits the handoff. `frontier-optimization` validates and consumes it. Neither Coordinator invokes the other or writes the other stage's records.

## Stage selection

| Durable state | User entry | Allowed result |
|---|---|---|
| Problem or representation is absent, stale, nonpositive, or still open | `frame-optimization` | Repaired framing state, exact blocker, or reviewed handoff |
| Current representation review is `PROCEED_EXPLORATORY` or `PROCEED_MODULAR` and no parent conflict exists | `frontier-optimization` | Frontier Entry, campaign action, closeout, recovery, or package result |
| Frontier detects a parent conflict before any campaign record | `frame-optimization` on a later user invocation | Repaired parent and a new reviewed handoff, or blocker |
| Frontier detects a parent conflict after campaign records exist | `frontier-optimization` | Exact permitted rebind or closeout; never an upstream edit |

The user selects the Coordinator by asking to frame or run the campaign. A worker never selects, invokes, or substitutes for either Coordinator.

## Handoff contract

Emit one immutable handoff only from the latest positive representation review. Bind:

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

Before creating or resuming campaign state, `frontier-optimization` recomputes every handoff and parent identity from repository bytes. It accepts only an unchanged positive result whose exact scope remains current. A mismatch returns `PARENT_REVIEW_REQUIRED` before any campaign record, Selection, reservation, worker action, or spend.

Admission copies the handoff bindings into Frontier state without changing their meaning. A positive handoff defines permitted search work; it does not authorize candidate development, spend, measurement, integration, incumbent use, promotion, production changes, or claims. Frontier applies its own Entry and lifecycle gates for those consequences.

The handoff is complete when a fresh reader can identify the active Coordinator, reproduce every binding, and reach the same admission result without conversation history or a global Skill installation.
