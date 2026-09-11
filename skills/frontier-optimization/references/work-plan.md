# Frontier Work Plan

## Contents

- [Template](#template): W frontmatter plus Purpose, Scope, design, delivery, input, progress, validation, recovery, and outcome sections.

Load only when work needs W. This is the sole `WORK.md` template. Use one W across B records that share one design contract or operational outcome. W stays a short map; indexed concern files hold exact design contracts.

Increment `plan_revision` for a material change to purpose, scope, design profile, concern meaning, user design choice, delivery obligation, input contract, validation, or definition of done. Apply [Technical design's assignment ownership rule](technical-design.md#assign-the-professional-author) to ordinary working-method changes. Assess the affected review conclusions and Permissions against the actual change; progress, corrected pointers and unrelated commits do not invalidate them.

## Saved design references

W owns relative file and section pointers plus stable slice keys. The consuming R, B or assignment owns the saved Git commit and selected paths. All pointers in that design reference resolve at that commit. W may cite an earlier source version, but never records the commit containing its own current bytes. Use `frontier_references.py design` as described in [Provenance and Git](provenance-and-identity.md#current-reference-tools) to prepare the reference and check the selected scope.

Current W writes have no section hashes, delivery hashes, normalized traceability hash, design self-hash or hash index. Git retains their bytes. Existing historical fields remain readable at their original version; update only the affected current design when needed, without migrating retained reviews or results.

## Template

```markdown
---
type: Frontier Work Plan
status: <proposed | active | completed | paused | blocked | superseded>
work_id: W001
plan_revision: <integer>
problem_epoch: <integer>
representation_revision: <integer>
affected_routes: [<T identifiers>]
affected_batches: [<B identifiers or none; lifecycle-only, never part of design delivery authority>]
design_profile: <module | system | not-applicable>
design_status: <not-required | drafting | review-pending | ready | repair-required | superseded>
design_review: <applicable R reference, pending review path, or not applicable; lifecycle-only>
input_state: <not-required | request-pending | waiting-for-input | received-unvalidated | accepted-as-evidence | rejected>
repository_structure_disposition: <existing-integrated | new-in-scope | user-choice-needed | not-applicable>
source_base: <existing source Git reference when design meaning requires it, or not applicable>
candidate_interface: <existing or user-approved seam, or not applicable>
generated: { by: frontier-optimization/1, at: "<ISO-8601 datetime>" }
---

# WORK: <work name>

## Purpose

<Coordinator: state the research problem, intended progress and required observable result, including the campaign baseline role when relevant.>

## Scope

<Coordinator: state the selected investment, actual constraints and exclusions, necessary interfaces and compatibility conditions, and relevant source starting points. Keep tentative combinations, scale and methods in the professional Design brief or concerns under Technical design's assignment ownership rule. Leave Batch assignments and frozen execution bindings to Entry; ordinary working methods and temporary paths remain with the executor.>

## Current state

<Coordinator: state the adopted checkpoint, next action, blockers, stable artifacts, design-review state, candidate-code lifecycle state, first performance check, preparation cost estimate, and required follow-up reserve. A preparation estimate is non-binding and does not create allocation, authority, consumption, or a hard limit. Keep current authorization in external lifecycle records.>

## Design brief

<Design implementation author: state the profile, proposed realization and why it is worth trying under Technical design's consequential-choice rule, stable external seam, decisive user choices and open assumptions. Distinguish tentative choices from adopted obligations. Keep detail in the indexed concern that owns it.>

## Design map

| Concern | Authoritative pointer | Applies because | Read when | Status |
|---|---|---|---|---|
| <architecture, domain, interfaces, flows, decisions, or verification> | <repository-relative path and section anchor> | <profile trigger> | <specific review or B action> | <draft | current | blocked | not applicable with reason> |

<Coordinator: derive this map from the designer's concern paths, triggers and read conditions, preserving professional meaning. A concern absent from this map is outside the design contract.>

## User design decisions

<Coordinator: list user-owned design V records, the choice each controls, effective conditions, and reconsideration trigger. Link to the owning decision record rather than repeating alternatives and consequences.>

## Delivery map

| Slice | Observable delivery | Blocked by | Required design inputs | Check and recovery point |
|---|---|---|---|---|
| <stable slice key and verification pointer> | <one independently verifiable behavior or artifact> | <stable prerequisite slice or technical condition, or None> | <indexed pointers needed by an executor> | <distinguishing check and safe resume point> |

`design/verification.md` is the single source for each delivery obligation's observable behavior, stable prerequisites, required design inputs, oracle, failure checks, and recovery point. The Coordinator copies a concise summary plus exact technical pointers into this table without changing that meaning. Selection and Entry later bind one exact B and execution realization; their status, paths, mutable work breakdown, and execution order never enter this contract-bearing table. One B may satisfy several obligations. An obligation is not independently published or charged unless a parent explicitly selected it as a standalone objective.

Every selected W-backed B cites the saved design reference and a nonempty unordered `delivery_scope` of stable slice keys through its existing Entry assignment or applicable R. The current Batch's `reviews` references that R; record selected obligations in its existing scope and acceptance rather than adding subject fields to `frontier-batch/1`. Resolve the selected scope at the design reference, including prerequisites and required inputs. A changed commit alone does not invalidate a review of unchanged relevant content.

For `module` or `system`, the Coordinator maintains `design/traceability.yaml` as a contract-bearing machine-readable index. `design-implementation` does not write it:

```yaml
work_id: <W identifier>
plan_revision: <integer>
slices:
  <stable slice key>:
    verification_pointer: <repository-relative path#section-anchor>
    prerequisites: [<stable slice keys, or empty>]
    required_design_inputs: [<repository-relative path#section-anchor>]
```

Entry reads traceability through the saved design reference and binds the selected obligations to B's execution source and work surface. A reused prerequisite remains in `delivery_scope`; B may satisfy it from retained evidence rather than rebuild it. Temporary paths and command order remain realization details. A path belongs to Design only when a real caller or operator outside the current B depends on it as a stable interface.

New or materially revised designs use `slices`. Retained designs and reviews keep their historical representation; an unchanged adopted design does not need conversion merely to remain usable.

## Human input contracts

| Input | Exact request and schema | Provenance and quality checks | Confidentiality and destination | Accept or reject condition | Resume event |
|---|---|---|---|---|---|
| <input identifier or not applicable> | <requested fields, types, units, allowed omissions, and response format> | <required source metadata, authenticity, completeness, consistency, legality, and domain checks> | <handling limits and stable response path> | <observable workflow validation rule> | <event that permits a new execution attempt> |

<Coordinator: create a row only when W owns human input. Supplied data is evidence after the workflow validates schema, provenance, and quality. It is not a technical conclusion, optimization result, or user value choice. Route a value choice through V.>

## Milestones and progress

<Batch worker: append bounded checkpoint observations from the assigned B packet.>

## Validation

<Coordinator: state the properties this delivery must establish and point to their owning verification sections and acceptance criteria. Reference applicable workflow conditions at their owner instead of reproducing lifecycle steps or adding technical requirements.>

State the design-review requirement generically here. Keep the current R reference and review result in lifecycle fields, so replacing a review does not change the technical obligations it reviews.

## Definition of done

<Coordinator: state the observable conditions that complete this delivery, citing its technical obligations and acceptance criteria. Include later measurement or other activities only when they belong to the assigned objective, not as automatic lifecycle requirements.>

## Decisions and discoveries

<Batch worker: record relevant evidence, surprises or opportunities in normal progress. Follow Working assignments for the affected owner and continuation; a suggestion changes no plan term or concern contract.>

## Recovery

<Coordinator: when useful, keep current recovery guidance near the preserved work, including commands or paths that help the next executor. This guidance is optional and updateable outside technical obligations; it creates no authority and cannot override existing constraints.>

## Outcome

<Coordinator: after checking the batch result, record completed, blocked, superseded, or active work and stable artifact links.>
```

A route states why work may improve the objective. W maps design and stable delivery obligations. B authorizes one bounded objective, its unordered `delivery_scope`, inputs, and spend envelope. The worker's mutable work breakdown is implementation detail, not a separate B or proposal. Engineering completion does not prove optimization success.
