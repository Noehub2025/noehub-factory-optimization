# Frontier Core

Load this file for every Frontier invocation. It defines authority, canonical paths, document rules, and the recorded-state router. Load no record templates or branch interfaces until the current action needs them.

## Contents

- Authority and upstream handoff
- Canonical task paths
- Document rules and core terms
- Finding effects
- Recorded-state router

## Authority and upstream handoff

`frontier-optimization` is the only Coordinator. It chooses campaign actions, assigns budget, adopts worker evidence, writes Outcome Reflections, changes retained results, stops or halts work, and adopts reviewed claim wording.

The four workers answer one assigned research question, preserve one user decision, execute one B packet, or review one immutable snapshot. Worker output changes no campaign meaning until the Coordinator checks it and writes the result to the canonical record.

One composite Entry may authorize an exact code materialization and one conditional local screen of its unique reviewed candidate. Apply the single-use slot and reusable protocol rules in [Evaluation protocol reuse](evaluation-protocol.md). That screen remains B evidence; independent Slot H evaluation and sealed confirmation keep their existing gates.

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
- **Halt:** stale parents, safety, legality, authority, access, accounting, a contradiction that changes parent authority or has no authorized diagnostic path, parent change, or withdrawn authorization blocks work; preserve state and route to closeout. A valid test refuting its research hypothesis follows ordinary R8 and resolver disposition; refutation alone is not a halt.
- **Pre-spend parent rebind:** a new positive parent identity replaces an older binding before any B spend, candidate materialization, external action, or accepted claim. It is allowed only when the problem epoch, representation revision, exact `Permitted` scope, measurement meaning, budget authority, stop meaning, and claim ceilings remain compatible; a current upstream disposition explicitly permits every retained evidence or decision record; and the Coordinator replaces every stale downstream authority.
- **Semantic parent challenge:** parent identities remain unchanged, but a latest controlling Outcome Reflection with resolved implementation, measurement, and comparison validity concludes that a parent-owned objective, Representation, Slot H measurement meaning, R8 rule, permitted scope, or claim ceiling is no longer suitable or reachable after disposing every execution-level measurement, implementation, and local-mechanism explanation. It returns through the existing stage-sensitive parent boundary and never edits the parent in Frontier.
- **Project provenance:** one typed decision root, exact project content roots, parent roots, review attestation, authority, execution state, and outcomes. Workflow source, release, Skill, validator, worker interface, test, deployment location, and source-module roots are not campaign identities.
- **Campaign generation:** one append-only Frontier campaign under the canonical task. Generation 1 is implied for legacy records without this field. A later generation never rewrites, reopens, or resets an earlier generation.
- **Post-closeout recovery:** a new campaign generation opened only by an explicit current user request after an adopted complete closeout. It carries prior spend against the same parent ceiling, uses new identifiers, and requires exact reuse dispositions and fresh gates.

## Opportunity proposals

A potentially better route outside the current parent scope is a proposal, not evidence that the parent is invalid. Preserve it in the existing Q recommendation, `R&D implication`, or user-facing handoff for the owning parent stage. State the suggested change, its mechanism basis, and the decision it could improve; use the ordinary return without new project status or artifacts. The suggestion alone neither revokes current authority nor triggers the semantic-parent forced closeout. Continue otherwise-selected in-scope work when its existing conditions allow it.

Actual parent adoption and out-of-scope work retain their existing owner, binding, and authorization rules. Within parent scope, apply [Opportunity-led reconsideration](learning-loop.md#opportunity-led-reconsideration). A demonstrated semantic parent challenge still uses the recorded-state router below; a proposal does not supply that finding.

## Finding effects

This section is the sole semantic owner of finding effects. Validators derive the effect from a stable code through `finding_effects.py`; callers and reviewers cannot supply or weaken it. An unknown code defaults to `block`.

Apply one decision-impact test: identify the violated requirement or observed evidence gap, the affected next consequence, and why proceeding would make that consequence unauthorized, unreliable, or unrecoverable. A demonstrated violation or unresolved consequential authority, spend, exposure, or external effect blocks only that transition. Uncertain effectiveness, novelty, unfamiliar methods, and hypothetical risk alone do not: select an authorized bounded observation when it can resolve the uncertainty. Reviewers need not prove the absence of every possible failure. This semantic test does not weaken coded findings; unknown validator codes still block until their meaning is resolved.

- `block`: the current action is unsafe or ambiguous. Preserve evidence and stop the affected transition. Use a new target, authorization, or B only when the semantic object or a prior answer or effect must change.
- `repair`: the current serialization, derived field, or transient realization is unusable, but the authoritative objective, evidence, and maximum consequence are unchanged and mechanically provable. Readiness remains false until correction. Repair inside the same semantic B and V before review or through an already authorized boundary-preserving continuation; rerun only the affected deterministic checks. A changed reviewed semantic input still requires the applicable review of that version, using [Entry repair review](entry-review.md#entry-repair-review) for an Entry correction.
- `advisory`: the canonical structured owner and every authority-bearing byte pass, while only a non-authoritative display timestamp, historical description, redundant prose hash, or generated narrative is stale. Readiness remains true. Preserve immutable records, report the advisory in validator or review output, and create no replacement identity, B, V, review, or authorization.

A timestamp that controls a deadline, ordering, lifecycle transition, or authorization is never advisory. A digest that binds candidate, evaluator, evidence, target, authority, or reproducibility is never advisory. A narrative disagreement is advisory only when `current_state`, its cited ledger decision, and every typed authority projection agree; otherwise it is `block`. Keep advisories out of strength, validity, progress, and constraint conclusions.

Correct a non-authoritative display in the current explanation or working view while retaining the reviewed version. A new version does not invalidate the old review for its own bytes, and the old attestation cannot approve a replacement decision. Existing authorization governs whether changed work may continue; an advisory alone creates no replacement object.

Historical artifacts retain their original validator and review meaning. Apply this contract prospectively; do not rewrite or mass-migrate old B, V, R, E, OR, or X records merely because finding output gained effects.

Throughout Frontier, `finding-free` means zero `block` or `repair` findings. Advisories are reported separately and do not make a ready object nonpositive.

## Recorded-state router

Compare parent bindings first, then evaluate top to bottom.

| Recorded state | Action |
|---|---|
| Parent or handoff mismatch; no Frontier record | Record `PARENT_REVIEW_REQUIRED`, return, and load no stage |
| Parent identity changed; Frontier records exist; all pre-spend parent-rebind conditions hold | Load `entry-and-planning.md` in pre-spend parent-rebind mode |
| Parent or handoff mismatch; adopted `CLOSEOUT_COMPLETE` cites the forced-halt handoff | Use the recorded closeout handoff as return input, record `PARENT_REVIEW_REQUIRED`, and load no stage |
| Other parent or handoff mismatch; Frontier record exists | Load `closeout-and-claims.md` for forced-halt reconciliation |
| Parent identities still match; the latest controlling Outcome Reflection establishes a semantic parent challenge | Load `closeout-and-claims.md` for forced-halt reconciliation and an exact `PARENT_REVIEW_REQUIRED` handoff naming the parent-owned defect and disposed in-frame explanations |
| Parent and handoff still match; adopted `CLOSEOUT_COMPLETE` cites a complete final handoff; current user explicitly requests a new campaign or exact recovery | Load `entry-and-planning.md` in post-closeout recovery mode |
| Parent and handoff still match; adopted `CLOSEOUT_COMPLETE` cites a complete final handoff; current user explicitly requests packaging | Load `packaging-and-recovery.md`; preserve the closed generation and create no authority |
| No closeout or claim trigger; no `FRONTIER.md`, incomplete F1-F4/F7/F8, no planned B, or no current adopted Entry review | Load `entry-and-planning.md` |
| Adopted `CLOSEOUT_COMPLETE` cites complete final handoff and no unresolved authority or claim branch | Use the recorded closeout handoff as return input and load no stage |
| `CLOSEOUT_REQUIRED`, stopped, halted, or unresolved stop/halt | Load `closeout-and-claims.md` full closeout |
| Current `CLAIM_REVIEW_REQUIRED` names C with neither an adopted A nor a withdrawing X, and no stop or halt applies | Load `closeout-and-claims.md` claim-only branch |
| Planned or running campaign with selected B, adopted first-B-spend Entry review, and current later Selection authority | Load `campaign-cycle.md` |

If no row matches, record `BLOCKED` with the conflicting fields and return.

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

If the user requests recovery but any prerequisite above is missing or conflicting, record `BLOCKED` with the exact field and return. Do not fall through to the completed-closeout handoff and do not silently reactivate old authority.

The pre-spend rebind row requires all of these checks:

- actual B spend and external-action spend are zero, no candidate has materialized, no B has started, and no C has an adopted A;
- the current positive parents preserve the same problem epoch and representation revision;
- exact permitted operations, measurement and comparison meaning, budget ceiling, stopping meaning, and claim ceilings are unchanged or explicitly mapped without widening;
- one current upstream disposition names every retained E, Q, T, V, or other adopted evidence or decision record as reusable; any unclassified record is not retained;
- the Coordinator marks every existing B, W, Selection, Entry review, review packet, worker packet, and development authorization as `replace` or `void` unless it is an immutable evidence source cited by a retained record and has no authority under the new parents;
- retained records and their cited evidence have every identity required by the new handoff.

Silence, semantic ambiguity, missing accounting, or any completed spend uses forced closeout instead. Rebind never makes an old Entry review positive and never edits an old record's meaning.
