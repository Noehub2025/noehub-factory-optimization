# Frontier Worker Interfaces

Load this file before any worker delegation. It defines non-overlapping write authority and the small research and user-decision packets. Batch and review branches have separate action files.

## Permissions

The Coordinator assigns exact writable files or sections before invocation. No Coordinator and worker permission names the same section.

Every current worker assignment cites the owning B, R, V, W, or other human handles plus only the full Git commits, repository-relative paths, external artifact references, limits, and completion condition needed by that worker. It does not create or recompute decision, attestation, authority, execution, or outcome roots. Workflow source, Skills, validators, releases, and deployment paths are not project inputs. Historical typed chains and `workflow_source_binding` remain readable only for retained records that already use them.

| Actor | May write | Meaning | Cannot write or decide |
|---|---|---|---|
| `frontier-optimization` | `FRONTIER.md`; `log.md`; ledger, bounds and claims; W lifecycle and mechanical bindings; current Batch definition, R and V references, limits, status and conclusion | Checked adoption changes campaign meaning; `Batch.apply` changes routine state and `Batch.perform` owns action execution, Attempts, consumption and Consequences | W Design brief or professional concern bodies; worker technical evidence; W worker progress/discoveries; review artifacts; parents |
| `design-implementation` | One assigned W Design brief and the professional bodies of triggered architecture, domain, interfaces, flows, decisions, and verification concern files | Proposed professional implementation design only; its invocation result creates no lifecycle state, identity, review verdict, authority, B, reservation, or spend | Purpose, Scope, Current state, Design map, Delivery map, user-decision adoption, traceability, identities or mechanical concern-frontmatter bindings, Validation, Definition of done, progress/discoveries, Recovery, Outcome, campaign records, reviews, candidate code, execution, measurement, route, or parent contracts |
| `reflect-frontier` | One exclusive `frontier/reflections/generation-<number>.md` assigned after full-closeout reconciliation | Search advantage for the next generation: retained assets, proposal-distribution changes, worthwhile opportunities, search stance, and reconsideration signals | Campaign records, B/E/Q/X, W, reviews, parents, Selection, Budget, authority, claims, execution, measurement, or another generation's Reflection |
| `research-frontier` | One assigned research evidence section and result packet | Proposed Q or D evidence | Campaign records, W, reviews, parents, selection, adoption |
| `grill-frontier` | One assigned answer packet | Preserved user answer | Task documents, V adoption, technical eligibility, consequence |
| `run-frontier-batch` | Assigned working material, checks, observations and operation result through the current Batch interface; assigned W progress and discoveries | Evidence only; a Batch result grants no campaign meaning | Worker-forbidden paths; W contract sections; design concern contracts; campaign records; Reviews; E adoption; integration; promotion; stop; claims |
| `review-frontier` | One assigned R file against an exact Git subject | Verdict limits later use of those bytes and assumptions | Campaign records, W/design/code/evidence, repair, user choices, spend, integration, promotion, publication |

When required work falls outside the assignment, return proposed content and the exact target without writing it. In particular, an executor reports a shared-interface or other contract-bearing discovery through its Batch result. The Coordinator opens and scopes a W revision; only `design-implementation` revises professional design content, and only the Coordinator regenerates lifecycle and mechanical bindings.

Within its assigned write surface, `run-frontier-batch` applies [Boundary-preserving continuation](batch-current.md#boundary-preserving-continuation). Same-B continuation never expands paths, meaning, Permission, Consequences or cumulative limits.

Only the Coordinator revises Batch resource limits. It first reserves any increase in Campaign Budget, lowers a Batch limit before releasing a reservation, and writes completed Attempt consumption back to Budget before another dependent allocation. The Batch worker reports requested and actual resources in the existing keys and units; it does not edit Budget or protected reserve.

For executable work, keep check names and results under the exact Git Candidate Revision in the current Batch. Use a separate Git-backed engineering plan only when several B records or another system genuinely reuse it. The relevant reviewer judges whether the checks support the proposed later Consequence; it does not prescribe harmless internal commands. Working feedback remains routine Batch work. Engineering-only fixtures grant no measurement or strength conclusion.

For measurement, the Batch-owned Measurement Definition states the mode, question, comparator, metric, scope, resource ceiling, non-repeatable unit, resource owner, consumption control, execution owner, evidence and interpretation limits, and result owner. The Action cannot carry another definition. `Batch.perform` records the exact definition, Candidate Revision, checks, Attempt, observations, resources, and Consequences. Create an independent protocol reference only when several B records or another system reuse its meaning.

For a genuinely single-use routine input, `Batch.perform` binds the named unit to the consuming Attempt under [Evaluation protocol reuse](evaluation-protocol.md). Workflow-owned units need only the stated execution control. User-owned private, scarce or unrecoverable units also require applicable V coverage.

Do not use worker write protection as a global drift rule. `worker_forbidden_paths` answer who may write. A Candidate Revision's Git commit and selected paths identify exact bytes used by its check or action. Unrelated dirty paths, workflow updates and ordinary working changes are not drift. Historical execution-frozen inputs, post-adoption transitions, snapshots and execution-start records remain enforceable only for the retained B that actually contains them.

## Research packet

Name `target_id`, exact `decision_root`, `research_mode: route_landscape | focused_question`, exact question, parent bindings, applicability, decision the answer can change, materially different findings and their recorded consequences, evidence channels, action window, fixed search stop, assigned evidence section, result-packet path, and completion check.

A route-landscape packet also names comparison dimensions, reviewed scope, repository and retained evidence, applicable prior-generation Reflection opportunities, and any reopened exclusion or shared high-consequence assumption. It asks the worker to map decision-relevant established approach families, representative implementations, known failures, and applicable functional transfer evidence. A post-result focused packet names the triggering adopted evidence and why cheaper local evidence is insufficient.

The result uses Q or D fields, reports `outcome: completed | blocked | evidence_required`, and names missing evidence when incomplete. Research supplies evidence; it does not approve, select, require, or score a route and cannot establish originality or exhaustive coverage.

## User-decision packet

Name `decision_kind: tradeoff | permission`, the exact unresolved user-owned decision, evidence, technically eligible alternatives or protected Consequence, scope and cumulative limits, affected work, reconsideration trigger, reserved V path, answer path and completion condition. Apply [User decisions](user-decisions.md); reuse an applicable V and do not delegate a question whose answer is already present.

A tradeoff packet gives the material value differences among technically eligible alternatives. A Permission packet gives the uncovered paid, external, sensitive, irreversible or user-controlled scarce-resource Consequence and the effects of permit, decline or conditions. It does not include packet, target, snapshot, authority, execution or result identities. The worker preserves the exact answer; the Coordinator writes V and resumes internal work.
