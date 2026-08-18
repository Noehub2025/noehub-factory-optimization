# User-facing return

This interface converts one durable outcome and one return reason selected by Steps 1–9 into one clear user decision. Steps 1–9 remain the single source of truth for stage selection, finding order, repair routing, state changes, and authority adoption.

## Input

Receive all of these values from the existing Coordinator route:

1. the durable outcome and controlling finding or positive handoff;
2. the selected recommendation or exact blocker;
3. the evidence that makes that recommendation preferable;
4. the authority already present in the current request; and
5. the exact route and stop that follow the user's reply.

The interface formats these values. It makes no routing, readiness, authority, or persistence decision.

## Reply interface

Return these sections in this order:

1. `Current outcome`: state the durable result and controlling finding or positive handoff.
2. `Recommended next action`: recommend one action, or state the exact blocker when no legal action exists.
3. `Why`: explain why the recommendation best advances the recorded objective under the current evidence and constraints.
4. `Copyable instruction`: give one instruction that names the target, maximum permitted consequence, exclusions, and next stop. Omit it when no legal user action exists.
5. `Effect and next stop`: state what the instruction permits and the exact point where the Coordinator returns control.
6. `Material alternatives`: include only an alternative that could become preferable, and state its switching condition. Otherwise write none.
7. `Authority boundary`: state what remains unauthorized. The recommendation itself grants no authority.
8. `After your reply`: name the existing Coordinator route that will process the instruction and its next action.

Use recorded project facts and plain task language. Lead with the preferred action. Present an alternative only with evidence that it could become preferable and the condition that would cause that change. Leave user-owned value judgments to the user.

For a selected authorization request, name the exact target, allowed changes or checks, maximum consequence, and stop. For a selected user question, ask one question and state how each material answer changes the next action. For a selected downstream dependency, name its deliverable and return condition in task-neutral language. For a selected positive handoff, recommend `frontier-optimization` planning and stop before candidate authorization, execution, reservation, or spend. For a selected blocker with no legal user action, omit the copyable instruction and state the exact required change.

Render the reply without writing project state.
