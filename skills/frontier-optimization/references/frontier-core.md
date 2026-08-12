# Frontier Core

Load this file for every Frontier invocation. It defines authority, canonical paths, document rules, and the recorded-state router. Load no record templates or branch interfaces until the current action needs them.

## Contents

- Authority and upstream handoff
- Canonical task paths
- Document rules and core terms
- Recorded-state router

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
- **Campaign generation:** one append-only Frontier campaign under the canonical task. Generation 1 is implied for legacy records without this field. A later generation never rewrites, reopens, or resets an earlier generation.
- **Post-closeout recovery:** a new campaign generation opened only by an explicit current user request after an adopted complete closeout. It carries prior spend against the same parent ceiling, uses new identifiers, and requires exact reuse dispositions and fresh gates.

## Recorded-state router

Compare parent bindings first, then evaluate top to bottom.

| Recorded state | Action |
|---|---|
| Parent or handoff mismatch; no Frontier record | Return `PARENT_REVIEW_REQUIRED`; load no stage |
| Parent identity changed; Frontier records exist; all pre-spend parent-rebind conditions hold | Load `entry-and-planning.md` in pre-spend parent-rebind mode |
| Parent or handoff mismatch; adopted `CLOSEOUT_COMPLETE` cites the forced-halt handoff | Return the recorded handoff and `PARENT_REVIEW_REQUIRED`; load no stage |
| Other parent or handoff mismatch; Frontier record exists | Load `closeout-and-claims.md` for forced-halt reconciliation |
| Parent and handoff still match; adopted `CLOSEOUT_COMPLETE` cites a complete final handoff; current user explicitly requests a new campaign or exact recovery | Load `entry-and-planning.md` in post-closeout recovery mode |
| Parent and handoff still match; adopted `CLOSEOUT_COMPLETE` cites a complete final handoff; current user explicitly requests packaging | Load `packaging-and-recovery.md`; preserve the closed generation and create no authority |
| No closeout or claim trigger; no `FRONTIER.md`, incomplete F1-F4/F7/F8, no planned B, or no current adopted Entry review | Load `entry-and-planning.md` |
| Adopted `CLOSEOUT_COMPLETE` cites complete final handoff and no unresolved authority or claim branch | Return the recorded final handoff; load no stage |
| `CLOSEOUT_REQUIRED`, stopped, halted, or unresolved stop/halt | Load `closeout-and-claims.md` full closeout |
| Current `CLAIM_REVIEW_REQUIRED` names C with neither an adopted A nor a withdrawing X, and no stop or halt applies | Load `closeout-and-claims.md` claim-only branch |
| Planned or running campaign with selected B, adopted first-B-spend Entry review, and current later Selection authority | Load `campaign-cycle.md` |

If no row matches, return `BLOCKED` with the conflicting fields.

A finished claim review always ends with an A disposition, including `EVIDENCE_REQUIRED`, `PARENT_REVIEW_REQUIRED`, and `BLOCKED`; only exact supported or reviewer-supplied downgraded wording receives external-use permission. If the request is withdrawn before review finishes, append X with `Disposition: withdrawn`. Either record resolves that C for routing, but neither a nonauthorizing A nor X authorizes wording. Record `CLAIM_REVIEW_COMPLETE`, preserve claim-only `campaign_status`, and return to Cycle when no other stop, halt, parent conflict, or unresolved C applies. Do not leave a completed or withdrawn claim branch without one of these terminal dispositions.

Treat a return token as adopted only when `log.md` cites its reason and required identities. Before first spend, any Entry-reviewed input change invalidates `FIRST_BATCH_PLANNED`. A strategic allocation requires unchanged `REPLAN_READY`; a code design requires unchanged `DESIGN_READY`; candidate measurement, integration, or incumbent use requires unchanged `IMPLEMENTATION_READY`. Every later spend requires complete Outcome Reflection coverage, applicable V, a joined X for dependent parallel work, and the latest authoritative Selection. A stop or halt remains unresolved until affected started B records reconcile spend, artifacts, W state, and required Outcome Reflection.

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

If the user requests recovery but any prerequisite above is missing or conflicting, return `BLOCKED` with the exact field. Do not fall through to the completed-closeout handoff and do not silently reactivate old authority.

The pre-spend rebind row requires all of these checks:

- actual B spend and external-action spend are zero, no candidate has materialized, no B has started, and no C has an adopted A;
- the current positive parents preserve the same problem epoch and representation revision;
- exact permitted operations, measurement and comparison meaning, budget ceiling, stopping meaning, and claim ceilings are unchanged or explicitly mapped without widening;
- one current upstream disposition names every retained E, Q, T, V, or other adopted evidence or decision record as reusable; any unclassified record is not retained;
- the Coordinator marks every existing B, W, Selection, Entry review, review packet, worker packet, and development authorization as `replace` or `void` unless it is an immutable evidence source cited by a retained record and has no authority under the new parents;
- retained records and their cited evidence have every identity required by the new handoff.

Silence, semantic ambiguity, missing accounting, or any completed spend uses forced closeout instead. Rebind never makes an old Entry review positive and never edits an old record's meaning.
