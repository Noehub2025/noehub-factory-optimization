# Frontier Worker Interfaces

Load this file before any worker delegation. It defines non-overlapping write authority and the small research and user-decision packets. Batch and review branches have separate action files.

## Permissions

The Coordinator assigns exact writable files or sections before invocation. No Coordinator and worker permission names the same section.

| Actor | May write | Meaning | Cannot write or decide |
|---|---|---|---|
| `frontier-optimization` | `FRONTIER.md`; `log.md`; ledger, bounds, claims; W contract and lifecycle sections; indexed design concerns; Coordinator packets, execution-baseline snapshots, and execution-start records | Checked adoption changes campaign meaning; an execution-start record releases one accepted packet only after it binds a complete content-addressed baseline snapshot | Worker evidence/result packets or result validation; W worker progress/discoveries; review artifacts; parents |
| `research-frontier` | One assigned research evidence section and result packet | Proposed Q or D evidence | Campaign records, W, reviews, parents, selection, adoption |
| `grill-frontier` | One assigned answer packet | Preserved user answer | Task documents, V adoption, technical eligibility, consequence |
| `run-frontier-batch` | Assigned acknowledgment; code/artifacts; candidate manifest; result-validation artifact; result packet; assigned W progress/discoveries | Evidence only; result validation grants no campaign meaning | Worker-forbidden paths; execution-baseline snapshots; execution-start records; W contract sections; design concern contracts; campaign records; reviews; E adoption; integration; promotion; stop; claims |
| `review-frontier` | One assigned immutable review artifact | Verdict limits later adoption | Campaign records, packets, W/design/code/evidence, repair, user choices, spend, integration, promotion, publication |

When required work falls outside the assignment, return proposed content and the exact target without writing it. In particular, a worker reports a shared-interface or other contract-bearing discovery through its result packet; only the Coordinator may revise W or a concern contract.

Do not use worker write protection as a global drift rule. `worker_forbidden_paths` answer who may write. `execution_frozen_inputs` separately answer what no actor may change after execution start. The Coordinator may perform only the packet's exact post-acknowledgment lifecycle transition, then must copy the complete post-transition baseline into its exclusive immutable snapshot before it writes execution-start. After that record, the worker enforces live equality with the snapshot through result validation.

## Research packet

Name `target_id`, `research_mode: route_landscape | focused_question`, exact question, parent bindings, applicability, decision the answer can change, evidence channels, assigned evidence section, result-packet path, and completion check.

A route-landscape packet also names comparison dimensions and reviewed scope. A post-result focused packet names the triggering Outcome Reflection and why cheaper local evidence is insufficient.

The result uses Q or D fields, reports `outcome: completed | blocked | evidence_required`, and names missing evidence when incomplete.

## User-decision packet

Name `target_id`, `decision_kind: tradeoff | authorization`, exact decision, evidence, affected records, conditions, reconsideration trigger, and result-packet path.

A tradeoff packet gives at least two technically eligible alternatives. An authorization packet gives one exact immutable object, scope, reviewed basis, next action, limits, and consequences of authorize, decline, and conditional authorization. When the object names a concrete B packet, it also gives unchanged finding-free `AUTHORIZATION_READY`, structural preflight, Entry schema, and target identities. Any missing, failed, stale, or mismatched gate makes the object ineligible to present. The result uses every V field and preserves the user's exact answer without adopting it.
