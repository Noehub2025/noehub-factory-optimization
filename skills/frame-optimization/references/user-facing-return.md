# User-facing return

This interface explains a durable outcome when Steps 1–9 select a genuine user return. Steps 1–9 remain the single source of truth for stage selection, finding order, repair routing, state changes, and authority adoption.

## Input

Receive the durable outcome, return reason, selected next action or exact blocker, supporting evidence, material alternatives, and applicable user scope from the existing Coordinator route.

The interface formats these values. It makes no routing, readiness, authority, or persistence decision.

## Reply interface

Explain in plain task language:

1. what materially changed and why it matters to the objective;
2. the strongest supported conclusion, its important limit, and the remaining objective gap or observation needed to determine it;
3. the selected next action and every material alternative, with its recorded ordering and switching condition; and
4. why control is returning: completed requested work, a requested pause or report, missing user input, or the exact condition preventing further work.

Put identifiers, reviews, budget accounting and repository status afterward as audit detail. A completed framing task or requested report needs no user decision merely to finish the reply.

## User action, when needed

For a missing answer selected under [User decisions](../../frontier-optimization/references/user-decisions.md), ask only that question and explain what the answer changes. For a technical blocker the user cannot resolve, state the missing evidence or capability instead of requesting permission.

Include a copyable instruction when the selected route needs a user action or the user asks for a recovery instruction. Carry forward the actual requested scope and applicable limits; a technical stage transition adds no restriction or requirement to wait for another reply. Show an authorization boundary or post-answer action only when it explains a real outstanding user decision. Internal continuation belongs to the [handoff route](frontier-handoff.md#continue-or-return), not a suggested instruction for the user to send.

Render the reply without writing project state.
