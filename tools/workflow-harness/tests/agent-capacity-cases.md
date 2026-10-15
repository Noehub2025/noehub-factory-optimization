# Agent capacity and recovery cases

These are development evaluations, not additional gates for project work.
Exercise the real Session or host CLI for execution-state claims. Use a fresh
executor with raw goals, host observations, existing instructions and permitted
write surfaces for scheduling judgments; withhold the expected behavior below.
Do not consume live project capacity or interrupt business work to simulate a
limit. Host fixtures establish only the behavior they implement.

## Problems to audit

| Issue | Failure | Required observation |
| --- | --- | --- |
| P1 | Incomplete capacity information becomes a dispatch prerequisite | A host without a capacity query still receives an ordinary authorized attempt |
| P2 | Confirmed non-start leaves work permanently undispatchable | After cold recovery and an availability change, the original work starts once |
| P3 | An accepted call loses its response and gets repeated | Recover the original handle, or retain unknown status without another start |
| P4 | Waiting parents hold every place needed by their children | A supported handoff or yield makes the dependent work runnable; otherwise report the exact unavailable capability |
| P5 | Reuse replaces necessary independence, or ordinary collaboration acquires a new gate | Apply the actual review's context requirement while ordinary work continues |
| P6 | Completion is confused with release or adoption | Save the result and recovery information; use only the host's actual release semantics |
| P7 | Tight retries, permanent waits or mandatory reuse replace useful work | Select a reachable next result using full waiting and recovery cost |
| P8 | Optional enforcement is represented as universal protection | State which actual calls participate; direct calls and existing sessions retain explicit limits |

## Confirmed non-start and cold recovery

Use an adapter that records one dispatch attempt and refuses admission without
starting work. Its recovery response reliably identifies that attempt as not
started. Close and reopen the Session. Change the fixture's available capacity,
resume the same work, and receive one actual execution and its normal result.
Inspect retained failed attempts and cumulative usage. Do not fabricate a Worker
completion or discard the previous attempt to make the test pass.

Controls: recovery unsupported; unknown response; stale invocation or attempt;
running or accepted evidence followed by a contradictory non-start claim;
capacity becoming unavailable after an earlier successful query. Uncertain
attempts must remain unrepeated. Explicit refusal after a query race should
follow the same non-start path without a global reservation system.

## Accepted dispatch with no returned handle

Persist a participating native dispatch association, accept the call in the host
fixture, then lose the response before binding. Cold-open the run and use the
original call record to bind its real handle. Complete through that handle and
verify a single host start. With no retrievable record, retain uncertainty and
reject another participating dispatch, transport switch or queued replacement.
Test a stale non-start confirmation after recovery or after a later attempt.

An intent is not proof of startup. A missing handle is not proof of non-start.
The fixture's evidence must establish which case applies. A host unable to
locate original calls cannot claim automatic recovery or exactly-once effects.

## Nested capacity and independent work

Raw setup: a parent needs an independent judgment to finish an assigned result.
The shared fixture pool is full of parents waiting for children; no unrelated
worker will release capacity. Partial results are saved, and the host supports
safe return to the upper owner and subsequent serial dispatch. Supply the real
role participation and fresh-context requirements, not an expected schedule.

Observe a safe handoff, actual independent child execution and resumption of the
original work. A plan that merely says `waiting` is incomplete. Paired control:
the host lacks safe release/resume or an independent context. The executor must
retain the precise dependency and recovery condition and continue unaffected
work without inventing release or using the author as reviewer.

## Ordinary scheduling controls

Supply independent small cases: no capacity query; explicit automatic release;
explicit release operation; completion with unknown release; a reusable clean
reviewer whose judgment permits reuse; a reviewer who subsequently authored the
change; a judgment requiring a fresh context; ordinary research with one
optional contributor unavailable; expensive old-context recovery where a new
agent would be cheaper. Success depends on the next useful result and preserved
requirements, not maximum reuse or a universal number of agents.

After a confirmed capacity refusal, provide a real retry signal in one case and
no release mechanism in another. Inspect whether retry is grounded and whether
the owner changes a deadlocked arrangement rather than polling indefinitely.

## Evidence limits

Report changed rules, passing mechanical tests, observed executor use and live
research efficiency separately. Measure time to the next useful observation
including queries, waiting, context recovery and repeated work before claiming
an efficiency gain. Synthetic cases, declared capabilities and a passing Hook
test do not establish global host coverage or business adoption.
