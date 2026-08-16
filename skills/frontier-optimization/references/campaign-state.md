# Frontier Campaign State

## Contents

- [FRONTIER.md and F1-F8](#frontiermd-and-f1-f8)
- [Budget update](#budget-update)
- [Selection](#selection)

Load this file only when creating or changing `FRONTIER.md`, Budget, or Selection. It is the sole source for those forms.

## FRONTIER.md and F1-F8

```markdown
---
type: Optimization Frontier
status: draft
problem: PROBLEM.md
problem_epoch: <integer>
problem_generated_at: "<ISO-8601 datetime>"
representation: REPRESENTATION.md
representation_revision: <integer>
representation_generated_at: "<ISO-8601 datetime>"
representation_review_result: <PROCEED_EXPLORATORY | PROCEED_MODULAR>
representation_reviewed_at: "<ISO-8601 datetime>"
representation_permitted: "<exact reviewed Permitted text>"
campaign_generation: <positive integer; legacy omission means 1>
campaign_status: <planned | running | stopped | halted>
current_state:
  campaign_generation: <same generation>
  campaign_status: <same status>
  primary_batch: <B identifier or null>
  parallel_batches: [<B identifiers>]
  decision_id: <current execution V identifier or null>
  authorization_state: <pending | adopted | not-required | closed>
  execution_batch: <current B identifier or null>
  execution_state: <not-authorized | awaiting-acknowledgment | acknowledged | released | reported | terminal>
updated: <ISO-8601 date>
generated: { by: frontier-optimization/1, at: "<ISO-8601 datetime>" }
---

# FRONTIER: <effort name>

## Brief

<Explain the campaign generation and recovery lineage when applicable, reference baseline, replaceable campaign baseline, reason it can carry optimization, exact scope, repository integration when relevant, remaining budget, next work, review authority, first performance check, protected reserve, latest decisive reflection, stop or halt conditions, and claim limits. Use concrete names, not bare identifiers.>

## Contract

| # | Item | St | Contract | Detail |
|---|---|---|---|---|
| F1 | Scope and bindings | <St> | Use problem epoch <n> and representation revision <n>; permit only <exact reviewed scope> with <required global checks>. | <detail link or blank> |
| F2 | Spend | <St> | Authorize <total>; <prior and Entry cost> plus <B actual> is used, <reservations> is reserved, <required reserve> is protected, and <balance> remains. | [frontier/ledger.md](frontier/ledger.md) |
| F3 | Baseline and next batch | <St> | Under <Entry or replan authority>, use <design and user authorization> for <baseline and B>; reach <check> within <limit>; reflect, protect <reserve>, then apply <R8>. | [frontier/ledger.md](frontier/ledger.md) |
| F4 | Retained results | <St> | Retain <E identities and parent-defined roles> under the current epoch; start with E001 as the reference baseline and name an incumbent only after valid measurement and retention. | [frontier/ledger.md](frontier/ledger.md) |
| F5 | References and bounds | <St> | Use <D records and authority> for <allowed use>, or state that no usable reference exists. | <detail link or blank> |
| F6 | Gap | <St> | Report <gap> from <compatible records>, or state why no valid gap exists. | <detail link or blank> |
| F7 | Stop | <St> | Stop or halt when <observable rules>; these rules support only <exact conclusion>. | [frontier/ledger.md](frontier/ledger.md) |
| F8 | Claims | <St> | Allow <exact wording and use> while preserving <coverage, reachability, composition, non-discovery, and claim limits>. | <detail link or blank> |

## Open decisions

- <F item and exact provisional or blocking decision>

## Known limits

- <limit and consequence>
```

`St`: `P` decided; `~` usable with a stated limit; `O` blocks affected spend; `-` not relevant.

`current_state` is the sole machine-readable owner of current Selection, authorization, and dispatch state. Ledger records own the decisions and evidence that justify it; `log.md` owns event order. The Brief and F table explain those records but grant no authority independently. For every authorization-readiness Entry, freeze a `frontier-current-state-projection/1` with exact pre- and post-adoption mappings from the live and proposed `FRONTIER.md` files. `validate_entry_packet.py` must reject a missing, extra, stale, or contradictory mapping before snapshot creation. Authorization adoption preserves `campaign_status`, changes `authorization_state` from `pending` to `adopted`, changes execution only from `not-authorized` to `awaiting-acknowledgment`, and makes the reviewed Primary and Parallel list equal `selected_batches`. The later first-B lifecycle rule remains separate.

Generate the Brief and F-table status wording from `current_state` and its cited ledger decision before presentation. When those typed owners agree, stale explanatory wording is `NARRATIVE_STATE_STALE` advisory under [Finding effects](frontier-core.md#finding-effects), not a new B, V, snapshot, or review. A disagreement among typed owners, or wording that is itself the user-facing authorization scope, spend, stop, or consequence, remains blocking.

The first-B lifecycle transition is a bounded status patch, not a general `FRONTIER.md` rewrite. Use the structured [first-B lifecycle contract](batch-interface.md#batch-packet): after accepted acknowledgment, capture one RFC3339 UTC transition instant, change `campaign_status` from `planned` to `running`, set `generated.at` to that instant, derive `updated` from its UTC calendar date, and preserve `campaign_generation` plus every other byte. Freeze the complete post-change bytes and record the structured transition receipt before execution start. A packet fixes this derivation rule and the pre-transition identity; it never predicts the runtime timestamp or date.

Pin F1-F4, F7, and F8 before first B spend. F1 copies exact `Permitted`; F8 copies every claim ceiling. E001 resolves the current-epoch reference-baseline identity and existing Slot H evidence from the handoff. Frontier does not create or repair that evidence. Selection keeps the replaceable campaign baseline in F3 and T/V/W/B; it enters F4 only after valid measurement creates E and Slots D, E, H, and R8 retain it.

The Brief passes only when a fresh reader can identify the baselines, project integration when relevant, allowed work, first performance check, protected reserve, remaining budget, success and comparison rules, latest decisive learning, stopping rules, and claim limits without reading the table. Read current Selection, authorization, and dispatch state from `current_state`; keep historical chronology in ledger and log references instead of restating every superseded repair chain.

## Budget update

Append whenever authorization, reservation, actual spend, reserve, or balance changes.

```markdown
Budget update:
- Recorded at: <ISO-8601 datetime>
- Campaign generation: <positive integer>
- Update kind: <interim | final closeout>
- Total authorized: <amount and unit>
- Prior setup spend: <amount and cited record>
- Inherited closed-generation spend: <amount and cited final Budgets, or zero for generation 1>
- Entry planning and research spend: <amount and cited records, or zero under the governing accounting rule>
- Active reservations: <B identifiers, amounts, accounting sources, or None>
- Actual campaign spend: <amount and cited records>
- Required follow-up reserve: <amount, unit, and mandatory confirmation or recovery purpose; Pending before campaign-baseline selection; or None with the governing rule>
- Unreserved balance: <amount and calculation>
- Per-batch limit: <amount and rule>
- Accounting source: <stable path or system>
- Candidate operating cost: <separate value and unit or not applicable>
```

Before Selection, replace `Pending` with a concrete reserve or `None` under R8. Account for Entry evidence work under the governing budget rule; it is not B spend, but it is never free when the authority charges it. In a recovery generation, carry earlier-generation spend forward exactly once and never reset the parent ceiling. Subtract prior setup spend, inherited closed-generation spend, charged current-generation Entry spend, current-generation campaign spend, active reservations, and the reserve exactly once. When the reserved purpose becomes a selected B, move that amount from required reserve to active reservation in one update.

A final-closeout update releases or dispositions every reservation, reports unknown spend explicitly, and leaves no active spend authority. Claim-only processing never writes a final-closeout Budget update.

## Selection

For the Entry Selection, use the Entry gate before any B exists. For every later Selection, append only after every previously selected B has a terminal outcome and controlling Outcome Reflection, every applicable E is covered, and every completed parallel set has a joined X. A paused `waiting_for_input` B remains selected and blocks dependent Selection. F3 names the same Primary and Parallel identifiers.

```markdown
Selection:
- Recorded at: <ISO-8601 datetime>
- Campaign generation: <positive integer>
- Recovery lineage: <prior CLOSEOUT_COMPLETE, recovery V and X identities, reused objects and limits; or None for generation 1>
- Evidence-state identity: <immutable identity of controlling terminal outcomes, E, reflections, Q, V, D, X, Budget, W, and reviews>
- Outcome reflections applied: <every controlling reflection, or None before the first B>
- Route-set state: <complete for this decision | incomplete | reopened, with Q, T, peer-source basis, shared assumptions, exclusions, deferrals, prerequisites, and reopening evidence>
- Direction resolution: <local R8 | local diagnostic | focused Q | route-landscape Q | strategic replan | stop | halt | blocked, with the first applicable rule>
- Terminal and join coverage: <terminal selected B identifiers, E coverage, joined X identity, or exact blocker>
- Route research: <route landscape Q and coverage conclusion>
- Campaign-baseline candidates: <eligible T identifiers, plain-language mechanisms, and route-generation basis>
- Eligible: <B and T identifiers with satisfied prerequisites or prerequisite-first limit>
- Ineligible or blocked: <identifiers, evidence-backed reasons, failed or unavailable prerequisites, and reopening events when one exists>
- Mandatory decision work: <identifier or None>
- Campaign-baseline choice: <chosen T, recommendation, V identifier, and decisive tradeoff; or sole eligible T and evidence>
- Repository structure: <existing structure and integration recommendation; or absent structure, user-approved V, and approved layout>
- Candidate interface and code integration: <existing or user-approved seam, source, tests, configuration, artifact convention, and stable shared paths; or not applicable>
- Design profile and map: <direct with evidence; current W revision, immutable design contract identity, indexed concerns, and affected B bindings; or not applicable>
- Design review: <adopted DESIGN_READY identity, pending design B, or not applicable under direct profile>
- Development authorization: <external AUTHORIZATION_READY, exact V, Coordinator ENTRY_READY adoption, and frozen adoption validation bound to the target; pending readiness review; not applicable for non-code-bearing work>
- Implementation review gate: <required review before first measurement, integration, or incumbent use; reusable prior review and exact unchanged identity; or not applicable>
- User values applied: <V identifiers and effective conditions or None>
- Decision-relevant unknowns: <answered, deferred with event, or blocking>
- Research disposition: <none with reason | local diagnosis | focused Q | route landscape refresh | isolated prototype | parent review>
- Strategic replan gate: <assigned review path requiring adopted REPLAN_READY, unchanged prior identity, or not applicable>
- Adopted replan review: <unchanged REPLAN_READY identity whose reviewed proposal exactly matches this Selection and B state, or not applicable>
- R8 rule applied: <exact clause>
- Deterministic resolution: <unique R8 action, cheapest diagnostic, focused research target, required V, strategic review, stop, halt, or exact blocker>
- Primary: <B identifier and reason>
- Parallel: <identifiers and independence reason or None>
- Parallel checks: <same current W revision when shared, reservations, exclusive mutable paths, shared-resource safety, integration ownership, measurement compatibility, and failure isolation; or None>
- Join point: <one W-owned interface, integration, or comparison check after all members terminate, or None>
- Baseline-establishment checkpoint: <usable artifact and completion check>
- First performance check: <parent-approved comparison or decision result>
- Preparation budget limit: <maximum cumulative allocation before that check>
- Required follow-up reserve: <amount and mandatory confirmation or recovery purpose, or None with governing rule>
- Deferred: <identifiers, reasons, unresolved or unavailable prerequisite consequences, and observable reconsideration events>
```

Selection applies the reviewed Entry evidence or latest controlling reflection; it does not reinterpret route eligibility to make a proposed B pass. `complete for this decision` supports the current allocation only and makes no exhaustive-search, originality, or optimality claim. A sole eligible route is sufficient when every material decision-relevant mechanism class is dispositioned. When a load-bearing prerequisite is unresolved, the only eligible route-related B is its smallest sufficient prerequisite-first check; dependent implementation remains ineligible until passing evidence is adopted through the applicable Entry or Replan gate.

The same evidence-state identity must produce the same deterministic resolution. If multiple technically eligible actions remain and R8 does not choose among them, require the exact missing Q or V instead of selecting by preference or conversation context. No later spend authority exists until the Selection cites every required reflection, V, join, and applicable positive review.
