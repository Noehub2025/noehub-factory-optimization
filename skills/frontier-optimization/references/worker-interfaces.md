# Frontier Worker Interfaces

Load this file when assigning work or undertaking simple implementation directly. It defines working responsibility, exclusive active writes and the small research and user-decision packets. Batch and review branches have separate action files.

## Permissions

The Coordinator names the responsible worker and exact writable files or sections. Keep one active writer per section; input or Candidate Revision paths do not imply write authority. Roles below describe the responsibility being performed, not permanent Agent identities. For simple implementation requiring no independence, one Agent may sequentially coordinate and implement under the same working rules, without a role-switch record or authorization. It may not overwrite another worker's evidence or replace an independent reviewer.

Every current worker assignment cites the owning B, R, V, W, or other human handles plus only the full Git commits, repository-relative paths, external artifact references, limits, and completion condition needed by that worker. It does not create or recompute decision, attestation, authority, execution, or outcome roots. Workflow source, Skills, validators, releases, and deployment paths are not project inputs. Historical typed chains and `workflow_source_binding` remain readable only for retained records that already use them.

Prepare W references under [Work Plan](work-plan.md#saved-design-references) and resolver inputs under [Learning Loop](learning-loop.md#resolver-input-preparation). Pass generated bindings as structured data or write them into the existing assignment with the tool. A textual dispatch names that assignment's location; it does not transcribe digests. The receiver reads the binding rather than recreating it from prose.

| Actor | May write | Meaning | Cannot write or decide |
|---|---|---|---|
| `frontier-optimization` | `FRONTIER.md`; `log.md`; ledger, bounds and claims; W lifecycle and mechanical bindings; current Batch definition, R and V references, limits, status and conclusion | Checked adoption changes campaign meaning; `Batch.apply` changes routine state and `Batch.perform` owns action execution, Attempts, consumption and Consequences | W Design brief or professional concern bodies; another worker's technical evidence or W progress/discoveries; review artifacts; parents |
| `design-implementation` | One assigned W Design brief and the professional bodies of triggered architecture, domain, interfaces, flows, decisions, and verification concern files | Proposed professional implementation design only; its invocation result creates no lifecycle state, identity, review verdict, authority, B, reservation, or spend | Purpose, Scope, Current state, Design map, Delivery map, user-decision adoption, traceability, consuming saved references, Validation, Definition of done, progress/discoveries, Recovery, Outcome, campaign records, reviews, candidate code, execution, measurement, route, or parent contracts |
| `reflect-frontier` | One exclusive `frontier/reflections/generation-<number>.md` assigned after full-closeout reconciliation | Search advantage for the next generation: retained assets, proposal-distribution changes, worthwhile opportunities, search stance, and reconsideration signals | Campaign records, B/E/Q/X, W, reviews, parents, Selection, Budget, authority, claims, execution, measurement, or another generation's Reflection |
| `research-frontier` | One assigned research evidence section and result packet | Proposed Q or D evidence | Campaign records, W, reviews, parents, selection, adoption |
| `grill-frontier` | One assigned answer packet | Preserved user answer | Task documents, V adoption, technical eligibility, consequence |
| `run-frontier-batch` | Assigned working material, its ordinary integration, checks, observations and operation result through the current Batch interface; assigned W progress and discoveries | Evidence only; a Batch result grants no campaign meaning | Worker-forbidden paths; W contract sections; design concern contracts; campaign records; Reviews; E adoption; formal admission or promotion; campaign stop; claims |
| `review-frontier` | One assigned R file against an exact Git subject | Verdict limits later use of those bytes and assumptions | Campaign records, W/design/code/evidence, repair, user choices, spend, integration, promotion, publication |

When required work falls outside the assignment, return proposed content and the exact target without writing it. In particular, an executor reports a shared-interface or other contract-bearing discovery in current progress, without terminalizing B. The Coordinator opens and scopes a W revision; only `design-implementation` revises professional design content, and only the Coordinator regenerates lifecycle and mechanical bindings.

Within its assigned write surface, `run-frontier-batch` applies [Boundary-preserving continuation](batch-current.md#boundary-preserving-continuation). Same-B continuation never expands paths, meaning, Permission, Consequences or cumulative limits.

Only the Coordinator revises Batch operational limits. An in-allocation revision needs no Campaign reservation or user decision. Reserve only governed capacity that must remain unavailable to another allocation before Attempt writeback; lower the affected Batch limit before releasing such a reservation. Write only Budget-governed Attempt use to Campaign Budget before another dependent allocation. The Batch worker reports requested and actual resources in the existing keys and units; it does not edit Budget or protected reserve.

For executable work, keep check names and results under the exact Git Candidate Revision in the current Batch. Use a separate Git-backed engineering plan only when several B records or another system genuinely reuse it. The relevant reviewer judges whether the checks support the proposed later Consequence; it does not prescribe harmless internal commands. Working feedback remains routine Batch work. Engineering-only fixtures grant no measurement or strength conclusion.

When implementing a governance adapter or optional preflight, follow [Review applicability and adoption](batch-current.md#review-applicability-and-adoption); complete the adapter check through adoption followed by `Batch.perform`, not through isolated Review checks alone.

For measurement, the Batch-owned Measurement Definition states the mode, question, comparator, metric, scope, resource ceiling, execution owner, evidence and interpretation limits, and result owner. Add `nonrepeatable_unit`, `resource_owner`, and `consumption_control` only for an Action or adapter that declares `single_use_consumption`; otherwise omit them. The Action cannot carry another definition. `Batch.perform` records the exact definition, Candidate Revision, checks, Attempt, observations, resources, and Consequences. Create an independent protocol reference only when several B records or another system reuse its meaning. Apply the evidence-use and single-use details from [Current Batch measurement](batch-evaluation.md) rather than restating them in an assignment.

For a genuinely single-use routine input, `Batch.perform` binds the named unit to the consuming Attempt under [Evaluation protocol reuse](evaluation-protocol.md). Workflow-owned units need only the stated execution control. User-owned private, scarce or unrecoverable units also require applicable V coverage.

Do not use worker write protection as a global drift rule. `worker_forbidden_paths` answer who may write. A Candidate Revision's Git commit and selected paths identify exact bytes used by its check or action. Unrelated dirty paths, workflow updates and ordinary working changes are not drift. Historical execution-frozen inputs, post-adoption transitions, snapshots and execution-start records remain enforceable only for the retained B that actually contains them.

## Working assignments

W describes the overall design; B pursues one independently judged result; a worker invocation advances a coherent part. In the existing task description or working record, name the next useful deliverable or observation, working location, write surface, applicable source references and known limits, current gap, and what would complete this invocation. Reference existing checks or describe the behavior worth checking when no check exists yet. Read limits and versions from their owners rather than copying them. A new context needs the base task references plus current changes, not an unexplained delta. This needs no separate assignment file, handle, receipt, restatement or completeness proof.

Prefer the existing implementation worker for sustained development and connected parts; a reviewer is not that worker. Keep simple work together, including direct implementation under Permissions above. Split only when dependencies or context load justify it, not by file count. Default to sequential continuation in the same B. The implementation owner connects the resulting work and checks affected seams even when another worker supplies a component. This is ordinary integration, not formal admission or a Campaign conclusion. Reuse sufficient evidence; retain one current writer for shared Batch state without an additional integration role or approval.

An assignment is sufficient when its references support starting the next useful exploration. Unknown benefit, internal methods and unanticipated results are work to investigate, not reasons to demand an exhaustive specification, failure catalogue or test oracle. The implementer may refine internal steps, test methods and error handling from existing goals and evidence. A choice that changes an important interface, state owner, behavior promise, acceptance or measurement meaning goes to its existing owner; pause only dependent work. A needed write outside the assigned surface requires coordination, not a new B or automatic user question.

Workers repair ordinary defects and report progress, retained work, remaining gap and next action at an invocation return. The Coordinator resumes or assigns the next in-scope segment under existing authority; an internal return is neither a terminal B result nor a request for user permission. A missing assignment file or unbound check does not by itself prevent ordinary development. Review adoption, operational-limit changes and Batch conclusion remain Coordinator-owned.

## Research packet

Name `target_id`, exact `decision_root`, `research_mode: route_landscape | focused_question`, exact question, parent bindings, applicability, decision the answer can change, materially different findings and their recorded consequences, evidence channels, action window, fixed search stop, assigned evidence section, result-packet path, and completion check.

A route-landscape packet also names comparison dimensions, reviewed scope, repository and retained evidence, applicable prior-generation Reflection opportunities, and any reopened exclusion or shared high-consequence assumption. Its bounded question may investigate an unknown mechanism or coverage gap; possible findings are prospective decision branches, not known answers or a required winning alternative. Retained evidence carries its scope and limits; prior ranking, exclusion, and stop judgments are assessed under [Scoped evidence reuse](learning-loop.md#scoped-evidence-reuse). The packet asks the worker to map decision-relevant established approach families, representative implementations, known failures, and applicable functional transfer evidence. Inside that one Q invocation, the parent may compile a temporary `role_bundle` from unresolved causal edges:

```yaml
role_bundle:
  role_briefs:
    - workstream_id: <local handle inside this Q>
      target_edge: <one unresolved causal or failure edge>
      lens: <problem-specific professional perspective>
      decision_question: <question that can change the current allocation>
      input_delta: <input beyond the inherited Q packet, or none>
      evidence_channel_delta: <different channel emphasis, or none>
      independence_mode: isolated_first_pass | evidence_reuse_pass
      unique_contribution: <decision-relevant contribution owned only here>
      shared_inputs: <adopted facts or shared retrieval reused across briefs>
      overlap_rule: <question or route family this brief does not duplicate>
      stop_condition: <point after which retrieval is unlikely to change the mechanism or sufficient falsifier>
```

The bundle inherits the Q inputs, fixed evidence protocol, write surface, search stop, completion check, and authority boundary. It is invocation context, not a Q, assignment, file, identity, review object, or Entry input. The parent handles zero or one brief directly and may use parallel return-only specialists only for two or more independently answerable briefs after shared retrieval and duplicate questions are merged. The parent remains the sole evidence and result-packet writer.

A focused-question packet names the triggering adopted evidence and why a cheaper sufficient observation cannot answer it. The parent answers it directly without a role bundle, frame challenger, or specialist fan-out.

The result uses Q or D fields, reports `outcome: completed | blocked | evidence_required`, and names missing evidence when incomplete. The parent normalizes material specialist provenance, conflicts, transfer limits, negative searches, and reopening conditions into this one result. Raw specialist or challenger returns create no project state and are never resolver inputs. Research supplies evidence; it does not approve, select, require, or score a route and cannot establish originality or exhaustive coverage.

## User-decision packet

Name `decision_kind: tradeoff | permission`, the exact unresolved user-owned decision, evidence, technically eligible alternatives or protected Consequence, scope and cumulative limits, affected work, reconsideration trigger, reserved V path, answer path and completion condition. Apply [User decisions](user-decisions.md); reuse an applicable V and do not delegate a question whose answer is already present.

A tradeoff packet gives the material value differences among technically eligible alternatives. A Permission packet gives the uncovered paid, external, sensitive, irreversible or user-controlled scarce-resource Consequence and the effects of permit, decline or conditions. It does not include packet, target, snapshot, authority, execution or result identities. The worker preserves the exact answer; the Coordinator writes V and resumes internal work.
