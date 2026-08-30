# Frontier Core

Load this file for every Frontier invocation. It defines authority, canonical paths, document rules, and the recorded-state router. Load no record templates or branch interfaces until the current action needs them.

## Contents

- Authority and upstream handoff
- Canonical task paths
- Document rules and core terms
- Finding effects
- Recorded-state router
- Change impact and retained results

## Authority and upstream handoff

`frontier-optimization` is the only Coordinator. It chooses campaign actions, assigns budget, adopts worker evidence, changes retained results, stops or halts work, and adopts reviewed claim wording. `reflect-frontier` exclusively writes the one Generation Reflection assigned during full closeout; that file creates no campaign decision or authority.

Specialist workers answer one assigned research question, preserve one user decision, design one technical seam, execute one B, reflect on one closed Generation, or review one exact Git subject. Worker output changes no campaign meaning until the Coordinator checks it and writes the result to the canonical record.

Current diagnostic, routine and formal measurement use one Batch-owned Measurement Definition and `Batch.perform`. Apply protocol reuse and single-use controls in [Evaluation protocol reuse](evaluation-protocol.md). Diagnostic and routine results remain B evidence; formal Slot H comparison keeps its technical readiness and validity gates.

Treat the Representation handoff as read-only. It must bind:

- canonical task path;
- problem epoch and `generated.at`;
- representation revision, `generated.at`, positive review, and exact `Permitted` text;
- evaluation and search representations, permitted operations, coverage, reachability, module contracts, global checks, search-state reuse, Slot H harness, and reference-baseline identity.

Use [Change impact](#change-impact-and-retained-results) for a changed parent or unresolved parent requirement. Framing retains parent authorship; Frontier may delegate the affected repair to `frame-optimization` within the current user grant and consume its handoff without another user invocation.

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
│   ├── reflections/
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
| T, V, B, E, Q, X, Selection, Budget | `frontier/ledger.md` |
| Generation Reflection | `frontier/reflections/generation-<number>.md` |
| D | `frontier/bounds.md` |
| C, A | `frontier/claims.md` |
| W | `frontier/work/<W identifier>/WORK.md` |
| W design concerns | paths indexed by the current W under its `design/` directory |
| Research evidence | assigned section in `frontier/details/research.md` |
| Entry, design, replan, implementation review packets and artifacts | assigned versioned paths in `frontier/reviews/` |
| Claim review artifact | assigned immutable `frontier/reviews/claims-<review-id>.md` |
| Candidate manifest | assigned stable artifact path under repository convention or user-approved layout |
| Return token, reason, cited identities | `log.md` |

`frontier/ledger.md` is the canonical current V location. One V records the user decision, scope, controlled resources or costs, permitted Consequences, conditions, withdrawal state, cumulative limits and reconsideration event. Current work creates no target, answer, adoption, authority-node or receipt chain around it. Retained historical chains remain readable under their original rules.

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
- Recover from the recorded decisions and their retained Git versions and artifact references; conversation is not a substitute for those records.
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
- **Halt:** a demonstrated safety, legality, authority, access or accounting boundary pauses its dependent action. Full closeout follows only a campaign-wide ending condition or explicit user stop. A parent revision, unresolved local question or refuted hypothesis alone does not end the campaign.
- **Parent revision:** a versioned change adopted by the existing parent owner. Its actual effect, not prior spend or the revision number, determines which future decisions need updating.
- **Semantic parent challenge:** parent identities remain unchanged, but current adopted evidence with resolved implementation, measurement, and comparison validity establishes that a parent-owned objective, Representation, Slot H measurement meaning, R8 rule, permitted scope, or claim ceiling is no longer suitable or reachable after disposing every execution-level measurement, implementation, and local-mechanism explanation. Refer the affected rule to its parent owner and pause only dependent work under Change impact.
- **Project provenance:** the applicable parent and campaign records plus full Git commits and repository-relative paths for exact project bytes, and stable external references only at real external seams. Workflow source, release, Skill, validator, worker interface, test and deployment location are not campaign identities.
- **Campaign generation:** one append-only Frontier campaign under the canonical task. Generation 1 is implied for legacy records without this field. A later generation never rewrites, reopens, or resets an earlier generation.
- **Post-closeout recovery:** a new campaign generation opened after adopted complete closeout under an applicable continuing user grant or an explicit current user request. It inherits recorded consumption, applies the current authorized ceiling and creates only the records and gates required by the next actual action.

## Opportunity proposals

A potentially better route outside the current parent scope is a proposal, not evidence that the parent is invalid. Preserve it in the existing Q recommendation or user-facing handoff; the Generation Reflection later consolidates surviving opportunities for the next Entry. State the suggested change, its mechanism basis, and the decision it could improve without creating a new project status. The suggestion alone does not revoke current authority or end the campaign. Continue otherwise-selected in-scope work when its existing conditions allow it.

Actual parent adoption and out-of-scope work retain their existing owner, binding, and authorization rules. Within parent scope, apply [Opportunity-led reconsideration](learning-loop.md#opportunity-led-reconsideration). A demonstrated semantic parent challenge still uses the recorded-state router below; a proposal does not supply that finding.

## Finding effects

Use [Finding effects](finding-effects.md) when a validator or reviewer reports a finding. It is the sole owner of block, repair and advisory consequences.

## Recorded-state router

Resolve known parent changes through Change impact, then evaluate top to bottom. A different version alone does not invalidate an unaffected decision.

| Recorded state | Action |
|---|---|
| An actual campaign-wide ending condition or explicit user stop requires closeout | Load `closeout-and-claims.md`; preserve unaffected historical results |
| A parent requirement needed by the next action is unresolved | Refer the affected repair to Framing within the grant; return `PARENT_REVIEW_REQUIRED` only for that action when the owner cannot resolve it; continue independent permitted work |
| An open campaign has an adopted parent revision affecting its next decision | Load `entry-and-planning.md` in parent-revision mode; retain this generation and unaffected work |
| Adopted `CLOSEOUT_COMPLETE` cites a complete final handoff; current user explicitly requests packaging | Load `packaging-and-recovery.md`; preserve the closed generation and create no authority |
| Adopted `CLOSEOUT_COMPLETE` cites a complete final handoff; an applicable continuing grant or current explicit request covers a new campaign or recovery | Load `entry-and-planning.md` in post-closeout recovery mode under the current applicable parents |
| No closeout or claim trigger; no `FRONTIER.md`, incomplete F1-F4/F7/F8, no planned B, or no current adopted Entry review | Load `entry-and-planning.md` |
| Adopted `CLOSEOUT_COMPLETE` cites complete final handoff and no unresolved authority or claim branch | Use the recorded closeout handoff as return input and load no stage |
| `CLOSEOUT_REQUIRED`, stopped, halted, or unresolved stop/halt | Load `closeout-and-claims.md` full closeout |
| Current `CLAIM_REVIEW_REQUIRED` names C with neither an adopted A nor a withdrawing X, and no stop or halt applies | Load `closeout-and-claims.md` claim-only branch |
| Planned or running campaign with selected B and every Entry, Review, V and Selection fact required by its next actual Consequence | Load `campaign-cycle.md` |

If no row matches, record `BLOCKED` with the conflicting fields and return.

A finished claim review always ends with an A disposition, including `EVIDENCE_REQUIRED`, `PARENT_REVIEW_REQUIRED`, and `BLOCKED`; only exact supported or reviewer-supplied downgraded wording receives external-use permission. If the request is withdrawn before review finishes, append X with `Disposition: withdrawn`. Either record resolves that C for routing, but neither a nonauthorizing A nor X authorizes wording. Record `CLAIM_REVIEW_COMPLETE`, preserve claim-only `campaign_status`, and return to Cycle when no other stop, halt, parent conflict, or unresolved C applies. Do not leave a completed or withdrawn claim branch without one of these terminal dispositions.

Treat a return token as adopted only when `log.md` cites its reason and controlling records. Revise `FIRST_BATCH_PLANNED` only when its actual decision or a relied-on conclusion changes. A strategic allocation requires unchanged `REPLAN_READY`; a code design requires unchanged `DESIGN_READY`; candidate measurement, integration or incumbent use requires unchanged `IMPLEMENTATION_READY` when that consequence needs it. Internal spend follows Budget, reservation, protected reserve and Selection; V is required only for a user-owned boundary under [User decisions](user-decisions.md). Later allocation also requires adopted terminal outcomes and eligible E dispositions, applicable Q records, a joined X for dependent parallel work, and the latest authoritative Selection with one persisted `Direction resolution` from the [Integrated direction resolver](learning-loop.md#integrated-direction-resolver). Reuse that resolution while its decision-relevant facts remain applicable. A candidate- or route-scope disposition blocks only work outside its recorded surviving scope. A campaign-scope stop or halt enters full closeout after affected B records reconcile consumption, artifacts, W state and terminal evidence; Generation Reflection then runs once before `CLOSEOUT_COMPLETE`.

An unresolved or unaffordable validity, implementation, or local-mechanism diagnostic is not a semantic parent challenge. It follows the resolver's Budget, validity, or exact-blocker row. A valid semantic parent challenge pauses dependent allocation and refers that rule to its owner through Change impact; it does not force closeout or pause unrelated permitted work.

Resolve the persisted project decision root before applying a direction row. Historical records remain immutable and are never rewritten to add later fields. A running B preserves its exact execution inputs and actual permission. Apply current workflow rules to its next decision, including removal of an obsolete procedural blocker, through the existing decision event. The update itself creates no mandatory migration, review or new object; create only a decision or binding that the next action actually changes. Missing required project bytes returns resolver row 3's exact project-evidence blocker.

`CLOSEOUT_COMPLETE` is valid only after full closeout; claim-only processing cannot write it. `CLAIM_REVIEW_COMPLETE` resolves only the named C and does not change campaign status, Selection, or spend authority.

The packaging row and post-closeout recovery row are mutually exclusive. An explicit current request to package, pause or stop takes precedence over automatic continuation. Packaging preserves the closed generation, changes no Budget or Selection, and cannot infer a recovery request. Post-closeout recovery applies only when the prior final handoff has complete accounting, no unresolved claim branch, and no active worker. Apply [User decisions](user-decisions.md): an applicable continuing grant can cover a Coordinator-selected next generation. Without it, the current request must explicitly open recovery; ordinary `continue` or `package` cannot broaden an old exact-only permission. In recovery mode:

- increment the highest recorded generation once; legacy records without a generation remain generation 1;
- retain prior closeout, terminal outcomes, reviews and original producing-parent bindings;
- inherit actual and unknown consumption from the existing authoritative accounting; a new generation neither resets a limit nor revives ended permission;
- cite the applicable grant and original evidence needed by the next action in the existing planning/X context; create V only for a new user-owned decision;
- follow [Candidate recovery](candidate-lifecycle.md#post-closeout-recovery-reuse) for published or unpublished material; use an existing positive review in its original scope, or complete only a missing or affected review;
- obtain Entry only for a new execution decision that actually needs it, using the existing difference-focused review and permission-reuse rules.

Recovery planning may name retained material before all evidence for its later use is available. Check the content needed for that use at its existing gate, not as a prerequisite to opening planning. Missing bytes pause their dependent use; they neither erase a prior result nor require a replacement proposal.

## Change impact and retained results

This section owns parent-revision and historical-result behavior for Framing and Frontier. Current workflow rules govern new and changed work; historical workflow rules describe how earlier work was produced, not a permanent veto on future actions. Explicit user limits remain binding until the user changes them.

Retain completed results and their reviews in the scope originally established. Workflow, template, validator, storage or generation changes alone create no new review, historical field, migration or recertification. With no relevant change or concrete contrary evidence, use the existing conclusion directly; require no routine compatibility report, per-file proof or recursive generation chain.

Reconsider only a changed deliverable, an actual change to its use, operating conditions, acceptance or measurement meaning, concrete evidence affecting a relied-on conclusion, or a new resource/access/external consequence. Inspect that change and its dependencies. Reuse unrelated conclusions; uncertainty about unrelated hypothetical failures is not a trigger.

The parent owner edits its rule and records the changed meaning and affected consequence in the existing revision/handoff context. Frontier adopts only the needed current binding in its existing X/decision records. Prior spend, materialization and a changed epoch or revision number alone do not force a new generation or candidate. Ask the user only for a boundary in [User decisions](user-decisions.md); delegate an in-scope parent repair to its existing owner without making the user switch stages.

Historical producing parents, execution inputs, failures, reviews and charges remain exact. Current parents and permission govern the next use, not a rewrite of how the material was produced. New evidence may support a new judgment without rewriting an old nonpositive verdict. A real new chargeable event still counts; unchanged bytes alone do not prove the event is the same.

A parent revision leaves already-frozen execution inputs unchanged. An unrelated revision does not interrupt that execution. A relevant revision pauses only dependent work; update the next action's existing decision/execution bindings under applicable permission. An old attestation never signs new bytes. Use scoped Entry repair only when its reviewed decision changes, not to certify that unrelated work is still compatible.

Parent documents own goals, acceptance, resource ceilings and charging/feedback/stop rules. Current consumption, reservations, generation, allocation and next action belong to the existing ledger and campaign state; any parent summary is nonauthoritative. An update to a summary does not change the rules.

Completion: the next affected action has an applicable parent, evidence and permission, or an exact unresolved dependency; unaffected work and valid historical conclusions remain usable. No change-review type, migration packet or additional resolver is introduced.
