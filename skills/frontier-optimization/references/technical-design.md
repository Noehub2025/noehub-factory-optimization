# Frontier Technical Design

## Contents

- [W is the map](#w-is-the-map)
- [Choose the profile](#choose-the-profile)
- [Assign the professional author](#assign-the-professional-author)
- [Early design feedback](#early-design-feedback)
- [Ground consequential design choices](#ground-consequential-design-choices)
- [Constrain effects, not convenient forms](#constrain-effects-not-convenient-forms)
- [Resolve user-owned design choices](#resolve-user-owned-design-choices)
- [Concern contracts](#concern-contracts)
- [Delivery slices](#delivery-slices)
- [Review and revision](#review-and-revision)

Load only when proving a direct profile; preparing, reviewing, or repairing a `module` or `system` design assignment; changing a shared interface, state owner, lifecycle, or schema; running an evidence-producing design batch; or responding to evidence that requires a contract-bearing design change. This reference is the single source for profile triggers and concern coverage. Do not load it merely to execute a `ready` design; follow W's `Read when` pointers to the required concern contracts. Load `work-plan.md` only when W is required and `design-review.md` only when freezing or reviewing a `module` or `system` design.

Treat a legacy W as `repair-required` only when the next changed work relies on missing technical meaning. Preserve useful content and update the affected design. Permission is owned by V, not by W completeness.

## W is the map

`WORK.md` holds the human-readable brief, current lifecycle, concern index, delivery slices, validation pointers, and recovery. `design-implementation` owns the professional Design brief and design contracts in indexed concern files. The Coordinator owns W lifecycle and the derived Design map, Delivery map and traceability:

```text
frontier/work/W001/design/
├── architecture.md
├── domain.md
├── interfaces.md
├── flows.md
├── decisions.md
├── verification.md
└── traceability.yaml
```

Create only triggered concerns, plus Coordinator-generated `traceability.yaml` for every `module` or `system`. Every W pointer states path, section, trigger, `Read when` and readiness. Use [W saved references](work-plan.md#saved-design-references) for version binding. A file absent from the Design map is outside the design contract.

## Choose the profile

### Direct

Use B without code-design W only when all are true:

- one bounded and reversible behavior change stays within established seams; it may touch multiple files;
- entities, state ownership, identity, invariants, lifecycle, shared or public interfaces, persisted schemas, dependency direction, migration, and contract-bearing failure behavior remain unchanged;
- B identifies the next useful behavior or observation, relevant source base, working paths and constraints, including recovery needs that matter to its actual effects;
- remaining executor choices impose no consequential architecture or interface obligations on another B or later technical route; and
- no unresolved user-owned design tradeoff remains.

Record the repository evidence and direct-profile reasoning. Apply the current Entry checks needed by the next actual Consequence. Development proceeds under an applicable existing V; ask the user only when [User decisions](user-decisions.md) identifies an uncovered boundary.

### Module

Use when one module or stable seam changes and callers need a revised contract. Create W plus `architecture`, `interfaces`, `flows`, and `verification`; add `domain` or `decisions` when triggered.

### System

Use when work changes interaction across modules, state ownership or lifecycle, migration, external operations, or coordinated rollout and recovery. Create W and every applicable concern. Editing several files is not sufficient by itself.

Profile selection is complete only when a fresh reviewer can reproduce it from cited task and repository facts. Understating the profile is a design finding.

Invoke `design-implementation` when any of these conditions holds:

- a shared, public, or persisted interface or schema changes;
- state ownership, identity, invariants, or lifecycle changes;
- responsibility, ordering, failure propagation, or an integration seam changes across modules;
- data, configuration, protocol, or deployment needs migration;
- an architecture or algorithm choice constrains several later slices, materially changes a performance or reliability limit, or is costly to replace; or
- the next work requires a consequential decision about entity meaning, interface behavior, state ownership, runtime transitions, failure propagation or acceptance meaning that existing agreements do not settle.

Choose the profile from relevant task and repository facts. Unknown research benefit, ordinary internal responses, test methods and work segmentation do not by themselves trigger professional design or require exhaustive checks before development. The Coordinator does not routinely call the designer to confirm a direct case. A misrouted designer may return `DIRECT_ELIGIBLE` without writing.

## Assign the professional author

For `module` or `system`, the Coordinator creates a W scaffold with the research problem, intended progress, actual scope and constraints, parents, source starting points, adopted user decisions and exclusive write sections. Keep tentative combinations, scale and methods in the professional Design brief or concerns, not binding Purpose or Scope. Apply [Evidence access](worker-interfaces.md#evidence-access). Invoke `design-implementation` in a fresh context with mode `new`, `revision`, or `repair`.

Design defines the deliverable's behavior, necessary architecture, interfaces, state ownership, technical dependencies, and acceptance criteria. The executor owns ordinary work breakdown, internal order, temporary material, support operations, and local repair inside the authorized envelope. Refine choices through [Working assignments](worker-interfaces.md#working-assignments); an unchanged investment does not waive an affected design or measurement owner's decision.

If an unpublished scaffold mistakes a tentative choice or incidental workflow method for a binding requirement, the designer and Coordinator correct their respective sections in the same task. This creates no new W, revision, review or repair record. Retain actual constraints; a change to adopted technical meaning still follows the affected revision path below. An earlier positive review is reusable evidence, not a reason to preserve a choice whose supporting premise has been contradicted.

When the design uses or replaces an existing capability, apply [Reuse working knowledge](batch-current.md#reuse-working-knowledge) within the assigned scope before inventing another interface or interpretation.

Publication eligibility, authority, accounting, and result closure stay with their existing workflow or parent owners; reference their rules rather than reproducing their operation in W. Apply [Professional output and workflow decisions](worker-interfaces.md#professional-output-and-workflow-decisions) when Design proposes another review or stage. Explicit user and parent requirements retain their original owner; their appearance in W does not make them Design-owned.

Apply [Decision-bearing thresholds](frontier-core.md#decision-bearing-thresholds) only to a condition that can change the acceptance or disposition of the planned work. W owns an implementation-acceptance threshold only when that consequence belongs to the designed module or system; cite a parent, Measurement Definition, or direct-B owner instead of copying its threshold into Design. When W does own the threshold, state its basis, applicable workload and statistic, allowed consequence, and reconsideration trigger in Decisions or Verification. Reusing an `unchanged` threshold requires the complete semantic match defined by Frontier Core, not merely the same value.

A method or sequence belongs in the relevant professional contract when it determines deliverable behavior, a necessary interface, evidence meaning, or an irreversible consequence. When a workflow, measurement facility, or publication system is itself the deliverable, design that system normally. Decide from the deliverable and consequences, not the task label or technology. Apply this distinction during ordinary authoring, without a classification record or additional gate.

The designer writes only W's Design brief and triggered concern files. The Coordinator derives Design map rows, Delivery map rows and `traceability.yaml` from those pointers and stable slice keys, then prepares the saved reference for review. Preserve professional meaning and leave future B assignments, attempt namespaces, internal evidence destinations and runtime status with their execution owners.

### Early design feedback

When a consequential assumption needs practical feedback, the designer names the uncertainty and smallest observation that could change the design. The Coordinator first reuses existing evidence or arranges that observation with the implementation or evidence-work owner in the current authorized work, then returns the facts to the original designer to continue. Use existing assignment and progress records. This coordination does not itself require a new Q, B, review, terminal result or user pause; create further work only when the observation's actual scope or effects require it. Test a decisive real-interface assumption early enough to revise the affected design before dependent construction, rather than leaving the first useful feedback to review.

Design authoring remains planning, with no execution authority or automatic proposal charge. Evidence work retains its owner's write scope and the normal controls for its actual effects, protected resources and charge events. Use `EVIDENCE_REQUIRED` only under [Test decisive feasibility claims](#test-decisive-feasibility-claims); it requests the missing observation, not a new evidence stage. Ordinary implementation feedback stays in development. A formal proposal does not become free by calling it design evidence.

## Ground consequential design choices

For choices that can materially change the current observation or its cost, explain in the existing Design brief or Decisions why the realization is worth trying: plausible objective improvement or useful learning, supporting facts and assumptions, and what result would reduce its appeal. Carry the selected research rationale and critical assumptions into these choices. The professional author may replace, combine or remove proposed components with technical reasons in the same design; preserve the problem and address its reasoning, not the initial answer. Compare only alternatives that could change this choice, using existing evidence, relevant source inspection or simple calculations. Reuse sufficient reasoning on continuation; revisit grounds affected by new facts, not every invocation.

Choose scale, duration and conditions that can expose the addressed mechanism or distinguish the pending question, retaining the interactions on which a whole-solution hypothesis depends. Use normal slices and integration to reach that observation; component attribution is needed only when it informs an actual development choice. A prerequisite test supports only what it tests: a local defect or absent activation does not automatically reject the route, while evidence against a genuine necessary condition may exclude the affected scope. Judge interpretability prospectively, without requiring activation, profit or hypothesis success in advance. Familiarity, small size and easy verification describe cost, not value; a larger probe earns its cost only when the extra observation matters.

Keep source claims at their supported scope. A weak warning is a hypothesis to assess, not a whole-route exclusion; a claim limit bounds conclusions but supplies no selection rationale. A short explanation suffices for an evident choice. This is part of ordinary design, not a new heading requirement, alternative quota, economic model, optimality proof, research assignment or review gate.

Derive supporting requirements from the promised observation or deliverable and its actual effects before prescribing facilities. Reuse existing execution, accounting and recovery capabilities. Add capability only for a concrete unmet need of this use, not generic completeness, speculative future use or easier review. Keep that rationale with the affected choice rather than creating a requirement inventory. Simplify the support around an ambitious, informative experiment; do not shrink the experiment until it can no longer test its hypothesis.

## Test decisive feasibility claims

Apply this check inside the existing cold-read implementability work for `module` and `system`; it is not a new gate and does not change the `direct` profile. First apply [Research hypotheses and action prerequisites](planning-records.md#research-hypotheses-and-action-prerequisites) to the promised output. A research slice must support an executable, interpretable observation, not establish its hypothesis in advance. Full delivery retains its acceptance obligations. A decisive feasibility claim is an unestablished, falsifiable claim on which that promised output depends. Novelty, complexity, first implementation, absence of a final deliverable, first-identity charging, and ordinary implementation risk do not establish such a claim by themselves.

For every decisive claim, require positive, reviewable grounds for a credible realization of the promised output under its relevant conditions and acceptance meaning. Grounds may come from analysis, proof, inspection, a same-condition example, demonstration, test, prototype, or another direct source appropriate to that output. Negative examples, internal consistency, or a future acceptance plan alone do not establish its feasibility.

Decide evidence routing separately from whether the claim needs review. Return `EVIDENCE_REQUIRED` only when current grounds are insufficient and one lower-consequence observation is affordable, reachable, and capable of changing the design verdict; continue through [Early design feedback](#early-design-feedback). If no such observation exists, do not create a recursive evidence gate or weaken readiness: use current grounds to establish a credible realization, revise the design to remove the unsupported dependency, return the exact parent-owned formal-risk decision, or return the exact blocker when no legal path remains. Work that only the normal formal proposal can test stays subject to its parent and R8 consequence; design work cannot make that proposal free.

Use these questions without creating a new field or artifact:

1. Which claim determines whether the complete slice can be delivered?
2. Which capabilities or interactions depend on it?
3. Which conditions and constraints must hold?
4. What end-to-end realization do the current grounds actually support, and what remains assumed?
5. Is there a lower-consequence observation that can falsify or materially strengthen the claim?

Address every decisive claim before design review, starting with the weakest. Do not enumerate non-blocking risks merely to fill the design.

## Constrain effects, not convenient forms

When a restriction on implementation form, evidence access, or verification method materially affects the current work, identify its owner and protection basis: an actual user or external constraint, a sampling or irreversible-effect requirement, or an internal technical choice. Explain what it protects and how. Prior adoption or an `unchanged` label is not itself a protection basis; a planner's precaution remains an internal choice rather than becoming a user prohibition or external rule.

When a source, license, integrity, or provenance concern would block current use, explain in the existing rationale the applicable requirement, intended use, relevant available evidence, and consequential gap. Consider supplied declarations before claiming that permission or source evidence is absent; assess concrete conflicting evidence rather than treating a public label as conclusive. Separate artifact identity, source claims, usage conditions and technical compatibility. Require further upstream or derived-material tracing only to answer a concrete question relevant to the current use, not to complete an unbounded provenance chain. Future-only publication or distribution obligations do not block an otherwise supported present use; local use is not automatically exempt from applicable conditions.

A reviewer may require repair when that current basis is absent or contradicted, or cite a concrete compatible alternative showing that the restriction prevents a useful observation or makes delivery infeasible or materially more costly without a protection rationale. The reviewer need not prove the narrowest possible rule or examine every restriction. Novelty, unfamiliarity, and ordinary implementation risk are not findings. A restriction that does not affect the current work is at most advisory.

The existing owner may revise an internal choice within the real user, resource, and evidence boundaries before affected work proceeds. Apply the existing scoped revision and review rules only to conclusions that actually change; do not automatically create a new B, V, or full review. Preserve historical evidence and actual consumption. A reviewer-only execution exclusion does not prohibit the implementation owner from obtaining relevant evidence through the normal permitted path.

Use [Finding effects](finding-effects.md#finding-effects) for unresolved necessary evidence or corrected premises. Do not preserve a rejection by escalating proof demands after its original basis has been resolved; a further concern needs its own concrete, applicable basis. These questions guide the affected decision, not a new checklist, certificate or approval stage.

## Resolve user-owned design choices

Evidence decides technical eligibility. Apply [User decisions](user-decisions.md#ask-only-for-a-user-owned-decision) to identify a genuine value tradeoff that evidence and existing preferences or grants do not settle. Cost, maintenance, migration or implementation differences alone do not require a user answer; the professional owner decides ordinary technical choices within the delegated scope.

For each unresolved user-owned choice:

1. Record alternatives, recommendation, evidence, uncertainty, and consequences in `decisions.md`.
2. Invoke `grill-frontier` with `decision_kind: tradeoff`.
3. Adopt the answer in V, then invoke `design-implementation` to update the owning concern and W brief under a new revision when the answer changes contract-bearing meaning.
4. Give local reversible executor choices explicit bounds instead of asking the user.

Prepare design review only after every user choice needed by the planned slice resolves. After adopting `DESIGN_READY`, return to the work that required the design: continue [Entry planning](entry-and-planning.md) when a first B still needs it, or [same-B continuation](batch-current.md#boundary-preserving-continuation) for a design revision within an existing B. A design-only request may finish here; apply the [Coordinator's scope and completion rule](../SKILL.md#recover-and-choose-the-current-action). Reuse an applicable V and obtain only checks required by the next actual Consequence. `DESIGN_READY` neither grants Permission nor blocks work already permitted by its owner.

## Concern contracts

`design-implementation` owns each triggered concern's professional content. Identify sections with stable headings. Inherit the W and saved version from [W saved references](work-plan.md#saved-design-references); concern files need no repeated design identity, revision, status or parent frontmatter. State a separately versioned input only where its version affects technical meaning.

### Architecture

Trigger for `module` or `system`.

State system context, current and proposed modules, responsibilities, boundaries, dependency direction, runtime or deployment topology when relevant, integration seam, protected components, alternatives, and rejected shapes.

### Domain

Trigger when entity meaning, identity, state, ownership, lifecycle, persistence, or invariants change.

Define core entities and value objects, identifiers, owner of each state, lifecycle and transitions, invariants, invalid states, persistence meaning, and mapping to existing concepts.

### Interfaces

Trigger when a caller-facing seam, schema, command, event, file, configuration contract, or external dependency changes.

Name callers and providers; inputs and outputs; schemas and examples; preconditions and postconditions; errors; side effects; idempotency; compatibility; versioning; timeouts; and stable test seam.

### Flows

Trigger for `module` or `system` or when sequencing, data movement, asynchronous work, or failure recovery matters.

Describe end-to-end control and data flow; state owner at each step; concurrency; ordering; retries; timeouts; cancellation; failure propagation; recovery; observability; and security or privacy boundaries.

### Decisions

Trigger for alternatives, user tradeoffs, migration, hard-to-reverse choices, material quality limits, or unresolved questions.

For each decision, record status, alternatives, technical eligibility, recommendation, evidence, consequence, reconsideration event, and which slices it blocks. Cite a user owner and adopted V only when a user decision applies; ordinary technical choices do not create one.

### Verification

Trigger for every `module` or `system` design.

State how to distinguish the promised behavior or observation from an implementation defect. Cover the requirements and failure behavior material to this use, including applicable interface, integration, compatibility, performance, migration or evidence-integrity checks. Specify evidence meaning, producer and consumer responsibilities, and stable external-interface behavior where they affect interpretation. Internal test methods and unanticipated research outcomes remain implementation work, not an exhaustive design-time catalogue.

Apply [Evidence at real boundaries](implementation-review.md#evidence-at-real-boundaries) to assumptions about actual dependencies that the next use relies on. The implementation owner covers the complete deliverable, including its relevant dependency seams; splitting implementation work or review scope does not transfer that responsibility to an unassigned future reviewer.

Make each delivery slice's observable behavior, stable prerequisites, required design inputs and distinguishing verification authoritative here. Specify failure and recovery obligations only where they affect the promised deliverable, a shared interface, actual effects or evidence interpretation. Reuse [Result and recovery](batch-current.md#result-and-recovery) for retained facts and unresolved effects; an exception need not produce an immediate final conclusion. A slice does not need its own recovery facility or resume point when ordinary working repair suffices. Entry binds these stable obligations to execution sources and working paths; it does not freeze the implementer's mutable work breakdown.

Use examples, schemas, state tables, or sequence descriptions when prose permits incompatible consequential behavior. A fresh executor must be able to implement and integrate the promised realization without inventing shared entity meaning, ownership, interface behavior, acceptance meaning, or failure and recovery obligations material to this use. Ordinary internal error handling, test implementation and work segmentation need not be settled in Design. Research needs an executable observation with interpretable outcomes, not advance proof of success or complete attribution.

## Delivery slices

`design-implementation` defines vertical delivery obligations that each produce one observable result through the real seam and records their exact contracts in `verification.md`. Together they must cover the complete realization and its integration check. The Coordinator summarizes each obligation in W's Delivery map under a stable technical name and immutable verification pointer. Entry, not Design, later assigns an exact B and realization paths. One B may satisfy several obligations before one formal publication; obligations never create their own B, candidate, proposal, review, or charge lifecycle. Do not make an executor read unrelated concerns.

The implementation owner maintains the mutable [Working plan](worker-interfaces.md#working-plan) outside W's design obligations and Batch lifecycle. Internal steps may be added, removed, merged, replaced or reordered while the B envelope and delivery obligations remain satisfied. Stable verification obligations do not freeze every test implementation or require one worker invocation to deliver all slices. Evidence that an obligation, seam, ownership, acceptance meaning, or load-bearing design assumption must change returns to `design-implementation` as a scoped revision. A local defect, failed check, or inconvenient implementation shape remains implementation feedback.

A design, research, or non-code prototype B may resolve one open question. Its worker reports evidence and proposed wording; a changed contract takes effect through an adopted W revision.

## Review and revision

Review the technical meaning of W Purpose, Scope, Design brief, Design map, User design decisions, Delivery map, applicable Human input contracts, Validation, Definition of done, indexed concerns and traceability at the saved Git reference. Progress, discoveries, recovery, outcome and current lifecycle records remain outside technical obligations. Their later changes do not require renewed Design Review.

The review's source references establish which repository facts supported Design. Entry separately selects the execution source. A required fixed ancestor, preserved artifact or pre-migration state remains an explicit design constraint; later execution must satisfy its stated compatibility conditions.

Use the current stable-slice traceability shape from Work Plan for new or materially revised designs. Retained designs keep their original representation and review; updating the workflow does not require their conversion.

Keep the current R and pending-review state in lifecycle fields. Technical obligations may specify required review checks but do not name their own future reviewer record. The consuming review stores its subject commit; W never backfills its own commit.

A contract-bearing change needs a new W revision and fresh technical review. The executor preserves the discovery; the Coordinator scopes the revision; `design-implementation` updates professional meaning; the Coordinator updates mechanical bindings. Follow [Boundary-preserving continuation](batch-current.md#boundary-preserving-continuation) for same-B work. Do not require a new user answer solely because a delegated technical concern changed. Lifecycle evidence alone does not change Design. A change to parent legality, permitted operations, acceptance, measurement meaning, or promotion returns to its owning stage.

Apply assignment ownership prospectively. Preserve historical verdicts and explicit constraints. Repair conflicting obligations in the next necessary scoped revision and reuse unaffected evidence and review conclusions. A corrected reference or guidance change creates no new design revision by itself.

Design planning is complete when the designer has returned `DRAFT_READY`, the maps and traceability cover every triggered concern and selected obligation without semantic drift, needed user choices resolve, and the saved Git subject is ready for `design-review.md`. Only `review-frontier` may return `DESIGN_READY`.
