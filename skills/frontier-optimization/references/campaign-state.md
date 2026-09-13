# Frontier Campaign State

At Generation opening, record the starting Git commit and intended working scope
in the existing campaign record; at a research-basis transition or full closeout,
cite the ending or retained version without requiring a clean worktree.
These locators support comparison and scoped restore, not a second state ledger.
Use [Provenance, Git, and retained artifacts](provenance-and-identity.md) for
retention and restore behavior. Working restores preserve evidence and spend.

Parent goals and rules remain in their owning contracts. Campaign generation and Selection live here. Budget owns campaign accounting and reservations; each B owns its actual consumption and Consequences, which Budget reconciles without copying the Batch lifecycle. Parent summaries are explanatory only. Apply [Change impact](frontier-core.md#change-impact-and-retained-results) when a parent rule actually changes.

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
project_start:
  commit: <full Git commit>
  paths: [<repository-relative paths that define the campaign starting scope>]
campaign_generation: <positive integer; legacy omission means 1>
campaign_status: <planned | running | stopped | halted>
current_state:
  campaign_generation: <same generation>
  campaign_status: <same status>
  primary_batch: <B identifier or null>
  parallel_batches: [<B identifiers>]
updated: <ISO-8601 date>
generated: { by: frontier-optimization/1, at: "<ISO-8601 datetime>" }
---

# FRONTIER: <effort name>

## Brief

<State the current research question and its relationship to the objective, the key observation still missing, and the work underway. Link to the current work and relevant evidence sources. Use concrete names, not bare identifiers.>

## Contract

| # | Item | St | Contract | Detail |
|---|---|---|---|---|
| F1 | Scope and bindings | <St> | Use problem epoch <n> and representation revision <n>; permit only <exact reviewed scope> with <required global checks>. | <detail link or blank> |
| F2 | Spend | <St> | Authorize <total>; <prior and Entry cost> plus <B actual> is used, <reservations> is reserved, <required reserve> is protected, and <balance> remains. | [frontier/ledger.md](frontier/ledger.md) |
| F3 | Baseline and next batch | <St> | Under <Selection and current user boundaries>, use <design and applicable V> for <baseline and B>; reach <check> within <limit>; adopt the result, protect <reserve>, then apply <R8>. | [frontier/ledger.md](frontier/ledger.md) |
| F4 | Retained results | <St> | Retain <E identities and parent-defined roles> under the current epoch; start with E001 as the reference baseline and name an incumbent only after valid measurement and retention. | [frontier/ledger.md](frontier/ledger.md) |
| F5 | References and bounds | <St> | Use <D records and authority> for <allowed use>, or state that no usable reference exists. | <detail link or blank> |
| F6 | Gap | <St> | Report <gap> from <compatible records>, or state why no valid gap exists. | <detail link or blank> |
| F7 | Stop | <St> | Stop or halt <affected scope> when <observable rules and their source>; these rules support only <exact conclusion>. | [frontier/ledger.md](frontier/ledger.md) |
| F8 | Claims | <St> | Allow <exact wording and use> while preserving <coverage, reachability, composition, non-discovery, and claim limits>. | <detail link or blank> |

## Open decisions

- <F item and exact provisional or blocking decision>

## Known limits

- <limit and consequence>
```

`St`: `P` decided; `~` usable with a stated limit; `O` blocks affected spend; `-` not relevant.

`current_state` is the sole machine-readable owner of current Campaign and Selection state. It names the selected B records but does not copy their lifecycle, Reviews, Permissions, Budget, Attempts, consumption, Consequences, or results. Each current B owns that work state through [Current Batch](batch-current.md); R, V, Budget, and E retain their own facts. `log.md` owns event order. The Brief and F table explain those records but grant no authority independently.

Historical `current_state` fields such as `decision_id`, `authorization_state`, `execution_batch`, and `execution_state` remain readable in their original records. Do not populate them in a current record or use them as current writers. The historical `frontier-current-state-projection/1`, Entry packet, acknowledgment, execution-start, and first-B lifecycle transition apply only to B records that actually contain that contract.

When a composite Entry has a routine follow-up, the governing B records the slot as `available`, `consumed: B/<Attempt>`, or `invalid: <exact reason>`. Selection names the governing B but does not duplicate the slot state. A consumed or invalid slot cannot reappear as available without a recorded correction of the owning Batch fact.

Build the F-table explanation from its owning Campaign, Selection, R, V, Budget and E records. Obtain Batch-owned facts through [Maintained Batch operations](batch-current.md#maintained-batch-operations) when needed by the current action; keep technical interpretation as authored explanation. Budget, permissions and execution state stay with their owners and need not be repeated in the Brief. Do not fill unknown values or cumulative totals from historical prose. F7 cites the current stopping-rule owner and affected scope; its summary creates no additional gate. A temporary pause or agent-inferred turn limit belongs in current progress, not in F7. Apply [User decisions](user-decisions.md) to distinguish the user's instruction from an agent's explanation.

When the owners agree, stale explanatory wording is `NARRATIVE_STATE_STALE` advisory under [Finding effects](finding-effects.md). Correct only the current description relied on, preserving history and actual limits; this creates no new B, V or review of unchanged technical content. A real disagreement among owners or an actual change to permission, spend, stopping or Consequences still blocks its dependent use and follows the existing owner. An old review does not certify changed bytes.

Change `campaign_status` from `planned` to `running` when the first selected B begins meaningful work. This is a Campaign fact, not a Batch execution credential. Update only Campaign and Selection state plus their explanatory wording; do not create an acknowledgment, snapshot, execution-start, transition receipt, or another identity. Historical records that used the old first-B lifecycle contract retain their original transition bytes.

After adoption, `running` with no Primary or Parallel may exist while the Coordinator arranges the next action. Use [Active learning chain](learning-loop.md#active-learning-chain); an empty Selection alone neither completes a continuing task nor triggers direction resolution. Return only at an existing completion boundary: the requested bounded deliverable is complete, the user explicitly pauses or requests reporting, or a user-owned boundary blocks every remaining worthwhile action. Otherwise continue, repair, apply a factually satisfied branch or reconsider investment as that method requires. When no safe, reachable and worthwhile direct action or grounded decision-changing inquiry remains, record a campaign stop and enter closeout.

Pin F1-F4, F7, and F8 before first B spend. F1 copies exact `Permitted`; F8 copies every claim ceiling. E001 resolves the current-epoch reference-baseline identity and existing Slot H evidence from the handoff. Frontier does not create or repair that evidence. Selection keeps the replaceable campaign baseline in F3 and T/V/W/B; it enters F4 only after valid measurement creates E and Slots D, E, H, and R8 retain it.

The Brief is a short navigation aid and explanation, not authoritative state or an acceptance object. If its information is unchanged, leave it untouched. When the understanding or arrangement of current work changes, update only the affected explanation or source pointer. Ordinary development progress stays in the existing working plan; history stays in the ledger, log and source records. Stale Brief wording does not itself block execution: correct the explanation from clear current facts and continue. Read execution state, permissions, spend and adopted meaning from their owners only as the current action requires.

## Budget update

Append whenever authorization, reservation, actual spend, reserve, or balance changes.

```markdown
Budget update:
- Recorded at: <ISO-8601 datetime>
- Campaign generation: <positive integer>
- Update kind: <interim | final closeout>
- Governing campaign limit: <amount, unit, and Problem, Frame, V, or verified external-capacity source; or None>
- Prior setup spend: <newly reconciled amount not already in the prior Budget total, and cited source; or zero>
- Previously reconciled spend: <cumulative governed consumption at the cited prior Budget update, including earlier generations; or zero>
- Entry planning and research spend: <newly reconciled charged amount not already in the prior Budget total, and cited sources; or zero>
- Active reservations: <B identifiers, amounts, accounting sources, or None>
- Actual campaign spend: <newly reconciled B/Attempt consumption not already in the prior Budget total, with source references, regardless of producing generation>
- Required follow-up reserve: <amount, unit, and mandatory confirmation or recovery purpose; Pending before campaign-baseline selection; or None with the governing rule>
- Unreserved balance: <amount and calculation>
- Accounting source: <stable path or system>
- Candidate operating cost: <separate value and unit or not applicable>
```

Include only resource keys governed by a cumulative Problem, Frame, V, or verified external-capacity limit. Keep planning estimates, Batch operational limits, Measurement Definition ceilings, and ungoverned internal use in their owning records; do not manufacture a Budget ceiling for them. Before Selection, replace `Pending` with a concrete reserve or `None` under R8. Account for Entry evidence work only when the governing accounting rule charges it. Use the cited prior Budget as a carried cumulative total and add only consumption not already reconciled there, identified by its original source event. Subtract that cumulative consumption, active reservations and protected reserve exactly once from the governing limit. A late result from an earlier generation remains owned by its original B/Attempt and contributes only its unreconciled use, not the whole B total again. Keep unknown consumption explicit. Generation changes never reset accounting or require summing overlapping per-generation totals; historical Budget formats remain readable without migration. When the reserved purpose becomes a selected B, move that amount from required reserve to active reservation in one update.

The Coordinator is the only owner that changes a strategic allocation or Batch operational limit. A Batch limit revision inside the same investment needs no Budget reservation when it stays within the current strategic allocation and governing balance. Create or increase a reservation only when governed capacity must remain unavailable to another allocation before Attempt use is written back; lower the affected operational limit before releasing such a reservation. After `Batch.perform`, retain the Attempt and actual `resource_use` first, then write only governed keys to Budget and disposition any matching reservation before making another dependent allocation. Use identical keys and units wherever the same governed resource appears. A protected reserve is not available until Selection assigns its stated purpose.

A research-basis transition uses an interim update and retains outstanding reservations and unknown use under [Research-basis transitions](frontier-core.md#research-basis-transitions); it requires no final old-generation Budget. A final-closeout update releases or dispositions every reservation, reports unknown spend explicitly, and leaves no active spend authority. Claim-only processing never writes a final-closeout Budget update.

## Selection

For the Entry Selection, use the Entry gate before any B exists. During an active task, the Coordinator may update the selected B references and current progress within the research problem under [Active learning chain](learning-loop.md#active-learning-chain). Preserve applicable investment rationale by reference; ordinary continuation creates no new direction resolution. A different independently judged result uses another B, not a broader acceptance for the old B.

An investment comparison may occur before active B records finish; comparison itself changes no allocation. To adopt a switch, stop adding affected old work, reconcile its actual effects, unresolved operations, retained results and resource occupation, and apply existing safe stopping and dependency rules. Update the affected B and Selection without fabricating a terminal result. Unrelated parallel work can continue; only the necessary result, join or shared resource delays dependent new work. Unresolved effects retain their controls, and reserved capacity is not released while still in use.

When current rules remove an obsolete procedural blocker, correct the affected current owner without rewriting history or broadening actual permission. Apply the continuation or investment trigger in Learning Loop rather than treating a historical instruction to rerun the resolver as a current obligation. An unchanged investment needs only its current progress or selected-work update, not a new X decision.

```markdown
Selection:
- Recorded at: <ISO-8601 datetime>
- Campaign generation: <positive integer>
- Recovery lineage: <existing research-basis transition X or prior CLOSEOUT_COMPLETE and recovery context; reused work and limits; or None>
- Project provenance: <full Git commit and affected repository-relative paths; no workflow identity>
- Evidence source and resolution: <applicable evidence references; saved professional resolution when investment was reconsidered; otherwise reference the current research scope and rationale>
- Route-set state: <complete for this decision | incomplete | reopened, with Q, T, peer-source basis, shared assumptions, exclusions, deferrals, prerequisites, and reopening evidence>
- Direction resolution: <applicable saved investment judgment and row, or not applicable for ordinary continuation; no placeholder resolution>
- Affected scope: <candidate | route | campaign, with exact affected identities and evidence; or not applicable>
- Surviving authority: <unchanged routes, W, Budget, and permissions preserved by the resolver; none for campaign stop or halt; or not applicable>
- Terminal and join coverage: <terminal selected B identifiers, E coverage, joined X identity, or exact blocker>
- Route research: <route landscape Q and coverage conclusion>
- Campaign-baseline candidates: <eligible T identifiers, plain-language mechanisms, and route-generation basis>
- Eligible: <B and T identifiers with satisfied prerequisites or prerequisite-first limit>
- Ineligible or blocked: <identifiers, evidence-backed reasons, failed or unavailable prerequisites, and reopening events when one exists>
- Mandatory decision work: <identifier or None>
- Campaign-baseline choice: <chosen T, recommendation, V identifier, and decisive tradeoff; or sole eligible T and evidence>
- Repository structure: <existing structure and integration recommendation; or absent structure, user-approved V, and approved layout>
- Candidate interface and code integration: <existing or user-approved seam, source, tests, configuration, artifact convention, and stable shared paths; or not applicable>
- Design profile and map: <direct with evidence; or saved W reference, indexed concerns, stable slice keys and required source references under Work Plan; or not applicable>
- Design review: <applicable DESIGN_READY R reference, pending design work, or not applicable under direct profile>
- Development authorization: <applicable user grant, current Entry readiness and execution authority; cite a new V only when User decisions requires one; not applicable when no execution is proposed>
- Implementation review gate: <required review before first measurement, integration, or incumbent use; reusable prior review and exact unchanged identity; or not applicable>
- User values applied: <V identifiers and effective conditions or None>
- Decision-relevant unknowns: <answered, deferred with event, or blocking>
- Diagnostic decision: <current adopted evidence or Entry, ordered alternatives, selected path, investment rationale and switching condition under the single Learning Loop resolver; or not applicable>
- Research disposition: <none with reason | local diagnosis | focused Q | route landscape refresh | isolated prototype | parent review>
- Strategic replan gate: <assigned review path requiring adopted REPLAN_READY, unchanged prior identity, or not applicable>
- Adopted replan review: <unchanged REPLAN_READY identity whose reviewed proposal exactly matches this Selection and B state, or not applicable>
- R8 rule applied: <exact clause>
- Deterministic resolution: <applicable saved investment resolution, or not applicable for ordinary continuation>
- Primary: <B identifier, next action and owner; reason within current research scope or applicable investment resolution>
- Parallel: <identifiers and independence reason or None>
- Parallel checks: <same current W revision when shared, reservations, exclusive mutable paths, shared-resource safety, integration ownership, measurement compatibility, and failure isolation; or None>
- Join point: <one W-owned interface, integration, or comparison check after all members terminate, or None>
- Baseline-establishment checkpoint: <usable artifact and completion check>
- First performance check: <parent-approved comparison or decision result>
- Preparation cost estimate: <current non-binding estimate through that check, its basis, and uncertainty; not allocation, authority, consumption, or a hard limit>
- Required follow-up reserve: <amount and mandatory confirmation or recovery purpose, or None with governing rule>
- Deferred: <identifiers, reasons, unresolved or unavailable prerequisite consequences, and observable reconsideration events>
```

Selection uses reviewed Entry, adopted observations and explicitly unverified professional reasoning without presenting hypotheses as measured conclusions. Apply [Technical potential](learning-loop.md#technical-potential) and retain independent judgment rather than treating Reflection suggestions as obligations. For ordinary continuation, update only current work references and changed facts, retaining the research scope and applicable rationale. For an investment decision, adopt the resolver's professional comparison. Neither path proves exhaustive search or global optimality. Apply [Research hypotheses and action prerequisites](planning-records.md#research-hypotheses-and-action-prerequisites) to the actual action.

When an investment resolution exists, adopt its finalized judgment and binding under [Resolver result completion](learning-loop.md#resolver-result-completion); preserve history and reject competing judgments for the same decision input. New observations and ordinary Selection updates do not each need such an identity or row. Entry and later work may use the Coordinator's continuation decision under the existing research scope without a fresh resolution. Cite the applicable evidence, Review, Permission, resource and dependency conditions for the actual action; routine work cannot consume protected reserve. Use Q for decision-relevant missing evidence and V only for a genuine user-owned boundary.
