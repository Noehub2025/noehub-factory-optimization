# Frontier Core

Load this file for every Frontier invocation. It defines authority, canonical paths, document rules, and the recorded-state router. Load no record templates or branch interfaces until the current action needs them.

## Contents

- Authority and upstream handoff
- Canonical task paths
- Document rules and core terms
- Finding effects
- Recorded-state router
- User-facing handoff

## Authority and upstream handoff

`frontier-optimization` is the only Coordinator. It chooses campaign actions, assigns budget, adopts worker evidence, writes Outcome Reflections, changes retained results, stops or halts work, and adopts reviewed claim wording.

The four workers answer one assigned research question, preserve one user decision, execute one B packet, or review one immutable snapshot. Worker output changes no campaign meaning until the Coordinator checks it and writes the result to the canonical record.

Treat the Representation handoff as read-only. It must bind:

- canonical task path;
- problem epoch and `generated.at`;
- representation revision, `generated.at`, positive review, and exact `Permitted` text;
- evaluation and search representations, permitted operations, coverage, reachability, module contracts, global checks, search-state reuse, Slot H harness, and reference-baseline identity.

Before campaign creation, a parent mismatch returns `PARENT_REVIEW_REQUIRED` with the exact conflict and upstream owner. After campaign creation, use the recorded pre-spend rebind route only when every condition below holds; otherwise preserve the campaign and route the mismatch to full closeout. Frontier never edits the parent documents or invokes `$frame-optimization`.

## Canonical task paths

Use the existing task directory. Create no second state directory.

```text
docs/skills/optimization/<task-slug>/
├── PROBLEM.md
├── REPRESENTATION.md
├── FRONTIER.md
├── log.md
├── frontier/
│   ├── ledger.md
│   ├── bounds.md
│   ├── claims.md
│   ├── reviews/
│   ├── work/<W identifier>/
│   │   ├── WORK.md
│   │   └── design/<applicable concern files>
│   └── details/research.md
├── slots/
├── representation/
├── modules/
└── eval/
```

| Content | Canonical path |
|---|---|
| T, V, B, E, Q, X, Outcome Reflection, Selection, Budget | `frontier/ledger.md` |
| D | `frontier/bounds.md` |
| C, A | `frontier/claims.md` |
| W | `frontier/work/<W identifier>/WORK.md` |
| W design concerns | paths indexed by the current W under its `design/` directory |
| Research evidence | assigned section in `frontier/details/research.md` |
| Entry, design, replan, implementation review packets and artifacts | assigned versioned paths in `frontier/reviews/` |
| Claim review artifact | assigned immutable `frontier/reviews/claims-<review-id>.md` |
| Candidate manifest | assigned stable artifact path under repository convention or user-approved layout |
| Return token, reason, cited identities | `log.md` |

For an exact execution V, `frontier/ledger.md` remains the canonical record. Its reviewed authorize-branch bytes are prepared before the final target and identify the decision, target specification, scope, and result path without copying a future target or answer identity. The later user-result file contains the exact byte-derived answer and final-target binding; the validated adoption record joins that result identity to the canonical ledger path. These files form one V and do not create a second record prefix.

When first creating `log.md`, a Frontier Markdown container, or `frontier/details/research.md`, use:

```yaml
---
type: <concrete document type>
status: active
generated: { by: frontier-optimization/1, at: "<ISO-8601 datetime>" }
---
```

## Document rules

- Write task documents in English with concrete task nouns.
- Give each main document a plain Brief that is understandable without its Contract table or detail files.
- Write one complete decision sentence per Contract cell. Put only links in Detail.
- Recover from task files and cited identities, not conversation or Git history.
- Keep record meaning immutable. Append a replacement or X disposition.
- Never reuse an identifier.
- Load by default only the parents, `FRONTIER.md`, latest controlling ledger blocks, and current W brief. Follow a W pointer only when its `Read when` condition matches the action.

## Core terms

- **Parent bindings:** exact problem epoch and generation identity, representation revision and generation identity, positive review, and exact permitted scope.
- **Recorded state:** current task files and cited records. Conversation is not recorded state.
- **Packet:** a Coordinator assignment with fixed inputs, limits, writable paths, result path, and completion checks.
- **Adopt:** check worker output and write accepted meaning to the canonical record.
- **Reference baseline:** current-epoch Slot H result recorded as E001; it anchors comparison.
- **Campaign baseline:** research-backed working approach selected as T/V/W/B; it is replaceable and is not retained E evidence before measurement.
- **Incumbent:** evaluated campaign result currently retained for development comparison.
- **Selected B:** complete planned B named by F3 and the latest Selection as Primary or Parallel.
- **Safe parallel set:** selected B records with separate reservations and mutable paths, no current-result dependency, compatible resources and measurement, failure isolation, and one join point.
- **Stop:** a precommitted ordinary F7 rule triggered; safely finish or interrupt affected work and route to closeout.
- **Halt:** stale parents, safety, legality, authority, access, accounting, a contradiction that changes parent authority or has no authorized diagnostic path, parent change, or withdrawn authorization blocks work; preserve state and route to closeout.
- **Pre-spend parent rebind:** a new positive parent identity replaces an older binding before any B spend, candidate materialization, external action, or accepted claim. It is allowed only when the problem epoch, representation revision, exact `Permitted` scope, measurement meaning, budget authority, stop meaning, and claim ceilings remain compatible; a current upstream disposition explicitly permits every retained evidence or decision record; and the Coordinator replaces every stale downstream authority.
- **Semantic parent challenge:** parent identities remain unchanged, but a latest controlling Outcome Reflection with resolved implementation, measurement, and comparison validity concludes that a parent-owned objective, Representation, Slot H measurement meaning, R8 rule, permitted scope, or claim ceiling is no longer suitable or reachable after disposing every execution-level measurement, implementation, and local-mechanism explanation. It returns through the existing stage-sensitive parent boundary and never edits the parent in Frontier.
- **Project provenance:** one typed decision root, exact project content roots, parent roots, review attestation, authority, execution state, and outcomes. Workflow source, release, Skill, validator, worker interface, test, deployment location, and source-module roots are not campaign identities.
- **Campaign generation:** one append-only Frontier campaign under the canonical task. Generation 1 is implied for legacy records without this field. A later generation never rewrites, reopens, or resets an earlier generation.
- **Post-closeout recovery:** a new campaign generation opened only by an explicit current user request after an adopted complete closeout. It carries prior spend against the same parent ceiling, uses new identifiers, and requires exact reuse dispositions and fresh gates.

## Finding effects

This section is the sole semantic owner of finding effects. Validators derive the effect from a stable code through `finding_effects.py`; callers and reviewers cannot supply or weaken it. An unknown code defaults to `block`.

Apply one decision-impact test: could ignoring the issue change the candidate or source bytes, data, evaluator, sampling, comparison or acceptance semantics, parent scope, user authority, access, spend, stop boundary, external effect, sealed evidence exposure, result interpretation, claim, or the ability to reconstruct any of them? `Yes` or `unknown` is `block`.

- `block`: the current action is unsafe or ambiguous. Preserve evidence and stop the affected transition. Use a new target, authorization, or B only when the semantic object or a prior answer or effect must change.
- `repair`: the current serialization, derived field, or transient realization is unusable, but the authoritative objective, evidence, and maximum consequence are unchanged and mechanically provable. Readiness remains false until correction. Repair inside the same semantic B and V before review or through an already authorized boundary-preserving continuation; rerun only the affected deterministic checks. A changed reviewed semantic input still requires the applicable fresh review.
- `advisory`: the canonical structured owner and every authority-bearing byte pass, while only a non-authoritative display timestamp, historical description, redundant prose hash, or generated narrative is stale. Readiness remains true. Preserve immutable records, report the advisory in validator or review output, and create no replacement identity, B, V, review, or authorization.

A timestamp that controls a deadline, ordering, lifecycle transition, or authorization is never advisory. A digest that binds candidate, evaluator, evidence, target, authority, or reproducibility is never advisory. A narrative disagreement is advisory only when `current_state`, its cited ledger decision, and every typed authority projection agree; otherwise it is `block`. Keep advisories out of strength, validity, progress, and constraint conclusions.

Historical artifacts retain their original validator and review meaning. Apply this contract prospectively; do not rewrite or mass-migrate old B, V, R, E, OR, or X records merely because finding output gained effects.

Throughout Frontier, `finding-free` means zero `block` or `repair` findings. Advisories are reported separately and do not make a ready object nonpositive.

## Recorded-state router

Compare parent bindings first, then evaluate top to bottom.

| Recorded state | Action |
|---|---|
| Parent or handoff mismatch; no Frontier record | Record `PARENT_REVIEW_REQUIRED`, finalize through User-facing handoff, and load no stage |
| Parent identity changed; Frontier records exist; all pre-spend parent-rebind conditions hold | Load `entry-and-planning.md` in pre-spend parent-rebind mode |
| Parent or handoff mismatch; adopted `CLOSEOUT_COMPLETE` cites the forced-halt handoff | Use the recorded closeout handoff as return input, finalize `PARENT_REVIEW_REQUIRED` through User-facing handoff, and load no stage |
| Other parent or handoff mismatch; Frontier record exists | Load `closeout-and-claims.md` for forced-halt reconciliation |
| Parent identities still match; the latest controlling Outcome Reflection establishes a semantic parent challenge | Load `closeout-and-claims.md` for forced-halt reconciliation and an exact `PARENT_REVIEW_REQUIRED` handoff naming the parent-owned defect and disposed in-frame explanations |
| Parent and handoff still match; adopted `CLOSEOUT_COMPLETE` cites a complete final handoff; current user explicitly requests a new campaign or exact recovery | Load `entry-and-planning.md` in post-closeout recovery mode |
| Parent and handoff still match; adopted `CLOSEOUT_COMPLETE` cites a complete final handoff; current user explicitly requests packaging | Load `packaging-and-recovery.md`; preserve the closed generation and create no authority |
| No closeout or claim trigger; no `FRONTIER.md`, incomplete F1-F4/F7/F8, no planned B, or no current adopted Entry review | Load `entry-and-planning.md` |
| Adopted `CLOSEOUT_COMPLETE` cites complete final handoff and no unresolved authority or claim branch | Use the recorded closeout handoff as return input, finalize through User-facing handoff, and load no stage |
| `CLOSEOUT_REQUIRED`, stopped, halted, or unresolved stop/halt | Load `closeout-and-claims.md` full closeout |
| Current `CLAIM_REVIEW_REQUIRED` names C with neither an adopted A nor a withdrawing X, and no stop or halt applies | Load `closeout-and-claims.md` claim-only branch |
| Planned or running campaign with selected B, adopted first-B-spend Entry review, and current later Selection authority | Load `campaign-cycle.md` |

If no row matches, record `BLOCKED` with the conflicting fields and finalize through User-facing handoff.

A finished claim review always ends with an A disposition, including `EVIDENCE_REQUIRED`, `PARENT_REVIEW_REQUIRED`, and `BLOCKED`; only exact supported or reviewer-supplied downgraded wording receives external-use permission. If the request is withdrawn before review finishes, append X with `Disposition: withdrawn`. Either record resolves that C for routing, but neither a nonauthorizing A nor X authorizes wording. Record `CLAIM_REVIEW_COMPLETE`, preserve claim-only `campaign_status`, and return to Cycle when no other stop, halt, parent conflict, or unresolved C applies. Do not leave a completed or withdrawn claim branch without one of these terminal dispositions.

Treat a return token as adopted only when `log.md` cites its reason and required identities. Before first spend, any Entry-reviewed project input change invalidates `FIRST_BATCH_PLANNED`; a workflow update does not. A strategic allocation requires unchanged `REPLAN_READY`; a code design requires unchanged `DESIGN_READY`; candidate measurement, integration, or incumbent use requires unchanged `IMPLEMENTATION_READY`. Every later spend requires complete Outcome Reflection coverage, applicable adopted Q and V records, a joined X for dependent parallel work, and a latest authoritative Selection with one persisted `Direction resolution` created by the [Integrated direction resolver](learning-loop.md#integrated-direction-resolver). Verify that its cited evidence-state identity, affected scope, surviving authority, and project facts remain unchanged; do not re-run the resolver under the current workflow. A candidate- or route-scope disposition blocks only work outside its recorded surviving authority. A campaign-scope stop or halt remains unresolved until affected started B records reconcile spend, artifacts, W state, and required Outcome Reflection.

An unresolved or unaffordable validity, implementation, or local-mechanism diagnostic is not a semantic parent challenge. It follows the resolver's Budget, validity, or exact-blocker row. A valid semantic parent challenge outranks route research, local diagnosis, and another in-frame B, but it does not bypass the existing forced-closeout reconciliation or create parent-edit authority.

Resolve the persisted project decision root before applying a direction row. Historical records remain immutable and are never rewritten to add later fields. A selected, authorized, acknowledged, or execution-started B continues under its exact project chain. Any workflow update, including a changed decision rule, validator, worker interface, deployment location, or release, applies prospectively and never creates a project identity, Entry, Replan, review, Selection, or spend-gate transition. Only a changed project fact or project decision may require a new project object and an otherwise-required review. Missing required project bytes returns resolver row 3's exact project-evidence blocker.

`CLOSEOUT_COMPLETE` is valid only after full closeout; claim-only processing cannot write it. `CLAIM_REVIEW_COMPLETE` resolves only the named C and does not change campaign status, Selection, or spend authority.

The packaging row and post-closeout recovery row are mutually exclusive. Packaging preserves the closed generation, changes no Budget or Selection, and cannot infer a recovery request. Post-closeout recovery applies only when the prior final handoff has complete accounting, no unresolved claim branch, and no active worker. The current user request must explicitly start a new campaign or name an exact recovery objective; ordinary `continue` or `package` does not qualify. In recovery mode:

- treat legacy records without `campaign_generation` as generation 1 and increment the highest recorded generation by one;
- preserve the prior closeout, terminal B records, reviews, Outcome Reflections, and final Budget unchanged;
- never reset the parent budget ceiling or reuse an identifier; inherit every prior and unknown spend before assigning new reservations;
- append one new authorization V that faithfully records the current request and one or more X records that map each reused Q, T, V, W or design, candidate, engineering, review, or result object into the new generation with exact limits;
- treat closed selections, worker packets, development authorizations, positive or nonpositive reviews, and return tokens as evidence only unless a recovery rule explicitly requires and revalidates them;
- charge no new proposal attempt for reusing an unchanged existing candidate identity, but charge the first byte or behavior change under the parent rule; and
- require fresh recovery Entry review before the first B and fresh implementation review before the reused candidate's first measurement, integration, or incumbent use.

When the recovery objective names an existing candidate, run the bound candidate-recovery validator against canonical manifest and member bytes before appending the new V, X, or generation event. A requested or recorded digest mismatch returns `BLOCKED` with zero new-generation artifacts and zero spend. After a match, freeze and bind the finding-free recovery preflight; never recompute identity from conversation text.

If the user requests recovery but any prerequisite above is missing or conflicting, record `BLOCKED` with the exact field and finalize through User-facing handoff. Do not fall through to the completed-closeout handoff and do not silently reactivate old authority.

## User-facing handoff

Apply this contract whenever control returns to the user, including a block, wait, authorization question, parent conflict, completed action, packaging result, or completed closeout. A durable closeout handoff record is input to the user-facing return reply; it does not replace that reply. Render only persisted state and do not rerun the router or direction resolver. The reply is complete only when it states:

1. the current objective and reference point in task language;
2. the work completed since the prior handoff, expressed as the concrete change, experiment, decision, or recovered capability rather than as a list of record identifiers;
3. the strongest result and learning supported by the controlling evidence, followed immediately by the important limit on that conclusion;
4. progress toward the objective at two levels: the valid objective gap from F6, or `unknown` with the missing bound or comparison that makes it unknown; and the nearest decision-changing evidence milestone plus any conditional later milestones already fixed by the parent contract;
5. the complete decision-relevant next-step set, or the exact unresolved Q, V, evidence, resolver event, or external event that prevents the set from being completed;
6. the recorded ordering: one dominant or preferred action, conditional preferences, or an exact non-dominated tie, with the evidence and user values that control that result;
7. one copyable instruction for each action the user can choose now, with its effect, authority, and next stop; and
8. the current authority boundary and the action the Coordinator will take after the user's instruction.

Build this explanation from the existing owners. Read the objective, reference point, valid gap, and parent milestones from the current Brief and F1, F3, F5, and F6. Read completed work and learning from the latest terminal B, its controlling Outcome Reflection, and any adopted result. Read candidates and ordering only from the persisted resolver result and Selection. Read resource availability and permissions from Budget and authority records. Do not reopen lower-level evidence merely to make the prose richer when its owning record already states the needed property.

Present the management explanation before audit detail. In semantic order, cover the outcome, progress toward the objective, next-step candidates, what the user can choose now, and only then operational details. Use project concepts as the subjects of sentences; place B, E, OR, V, R, identity, and digest values after the plain-language description when they help recovery or verification. Budget consumption, artifact count, passed checks, lifecycle gates, and a clean or dirty working tree are resources or operational facts, not measures of progress toward the objective.

When F6 is unknown, do not invent a percentage, imply that remaining Budget measures distance, or leave the reader with only `gap: Unknown`. State why the result cannot yet be placed against a valid bound, identify the closest missing observation that can change the decision, and show later milestones as conditional rather than promised work. A next procedural gate must be paired with the substantive question it exists to answer; creating an evidence-state identity, running the resolver, obtaining review, or opening Entry is never by itself the project outcome or research direction.

When no later resolver result or Selection exists because the authorized scope ended, say that the direction is not yet resolved. State the closest substantive decision exposed by the latest Reflection and the exact event needed to produce the complete candidate set. Offer a planning-only continuation instruction when it is legally available. Do not promote a visible candidate into a recommendation, claim that the visible candidates are exhaustive, or hide the unresolved decision behind the evidence-state or resolver mechanics.

Legal availability does not make actions equally advisable. When a persisted resolver result and Selection exist, surface every decision-relevant candidate, then give the recorded ordering and why, copyable instructions for currently user-selectable actions, switching conditions, and the authority boundary. When one action dominates or is the best-supported way to advance the recorded objective, label it `Recommended` and retain only material alternatives. When several candidates remain live, do not hide the set behind one recommendation. A recommendation is advice only: it grants no authority and creates no record until the user sends the instruction as a current request.

Offer only real decisions. When an unresolved user-owned value, cost, risk, reversibility, maintenance, or timing tradeoff prevents one unconditional recommendation, give the evidence-supported conditional ordering and ask one exact tradeoff question. Say what preference would switch the ordering. When technically eligible candidates remain non-dominated and the persisted resolver and R8 cannot rank them, show their distinguishing purpose, full cost, reachability, authority boundary, and next stop, then return the exact technical blocker; do not invent a recommendation or delegate the technical tie to the user. If the current request already supplies a qualifying reopening request, tradeoff answer, exact authorization, or input, apply it through the normal router and gates instead of asking the user to repeat it.

Use the applicable row below. Replace every placeholder with recorded identities and concrete task language; omit rows that are not legal in the current state.

| Current decision | Copyable instruction to suggest | Effect and required next stop |
|---|---|---|
| Continue an open campaign after a terminal action when no later resolver result or Selection exists | `Use $frontier-optimization. Continue campaign generation <generation> from <controlling reflection>. Preserve <reference point, completed result, retained evidence, and Budget>. Create one current project evidence state, run the integrated resolver exactly once, present the complete next-step candidate set and its recorded ordering, and stop before any new execution, measurement, reservation, or spend.` | Grants planning and direction resolution only. The Coordinator reports the resolver result and stops; any selected work still requires its ordinary Entry, review, and exact authorization gates. |
| Open a new campaign after closeout without a user-named technical objective | `Use $frontier-optimization. Open a new campaign from <closeout identity>. Preserve <closed generation and retained evidence>. Plan only, derive the proposed objective from the recorded handoff, and stop before any exact B authorization, execution, or spend.` | Grants campaign-opening planning only; the Coordinator derives the objective and stops at the next user-owned tradeoff or finding-free authorization-readiness gate. |
| Recover one named object or outcome after closeout | `Use $frontier-optimization. Open the next campaign generation in exact-recovery mode for <object or outcome>. Preserve <closed records>. Verify <reuse identities and prerequisites>, prepare a new reviewed target, and stop after finding-free AUTHORIZATION_READY to present the exact authorization target. Do not execute, mutate, rerun, reserve, or spend before my exact authorization.` | Grants planning and recovery preflight only; it creates no B execution authority. If no exact B exists yet, do not invent an identifier or ask the user to authorize one. |
| Package a completed closeout without reopening it | `Use $frontier-optimization. Package <closeout identity> as an authority-neutral durable handoff. Preserve the closed generation and do not start recovery or spend.` | Permits packaging only and returns the package identity and verification result. |
| Choose among reviewed user-owned alternatives | `Choose <option> for <exact tradeoff and V target>. Preserve the stated limits and do not treat this choice as B authorization.` | Records only the tradeoff answer, then stops at the next unresolved tradeoff or exact authorization gate. |
| Decide one exact target after finding-free `AUTHORIZATION_READY` | Lead with the response recommended by the unchanged Selection, objective, evidence, reviews, Budget, and recorded user values: `Authorize exactly <reviewed target, scope, spend, and stop boundary>.`; `Decline <reviewed target>; preserve the reviewed evidence and grant no execution or spend authority.`; or `Do not authorize <reviewed target>. Prepare a revised target with <requested condition> and obtain fresh AUTHORIZATION_READY before asking again.` Include another response only with its switching condition. | An exact affirmative answer may enter adoption; decline closes that target's authority; a condition or revision requires a new immutable target and fresh review. |
| Resolve a parent or Representation conflict | `Use $frame-optimization. Review <exact conflicting parent fields and identities>. Preserve the Frontier campaign and return a new positive handoff or an explicit non-reuse disposition.` | Grants no Frontier continuation; the Coordinator waits for a current compatible parent handoff. |
| Supply a missing private fact, access grant, resource, or artifact | `Provide <exact missing input> for <bound decision>. Treat it as evidence only and stop before any later authorization or spend.` | Re-evaluates the blocked gate without implying a route choice or execution authority. |
| No legal user action exists yet | Suggest no command. State the exact evidence, event, worker result, or external change that must occur before the user can decide. | Preserves the blocker and prevents a false continuation path. |

Every authorization suggestion must come from the unchanged reviewed object. Every reopening or recovery suggestion must name planning-only authority and its next stop. Never present a planning instruction as execution permission, reduce a known recovery path to only `BLOCKED` or `no authority`, or present legal alternatives as equally recommended when recorded evidence supports a preference.

The pre-spend rebind row requires all of these checks:

- actual B spend and external-action spend are zero, no candidate has materialized, no B has started, and no C has an adopted A;
- the current positive parents preserve the same problem epoch and representation revision;
- exact permitted operations, measurement and comparison meaning, budget ceiling, stopping meaning, and claim ceilings are unchanged or explicitly mapped without widening;
- one current upstream disposition names every retained E, Q, T, V, or other adopted evidence or decision record as reusable; any unclassified record is not retained;
- the Coordinator marks every existing B, W, Selection, Entry review, review packet, worker packet, and development authorization as `replace` or `void` unless it is an immutable evidence source cited by a retained record and has no authority under the new parents;
- retained records and their cited evidence have every identity required by the new handoff.

Silence, semantic ambiguity, missing accounting, or any completed spend uses forced closeout instead. Rebind never makes an old Entry review positive and never edits an old record's meaning.
