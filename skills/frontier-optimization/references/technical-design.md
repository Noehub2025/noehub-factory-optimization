# Frontier Technical Design

## Contents

- [W is the map](#w-is-the-map)
- [Choose the profile](#choose-the-profile)
- [Assign the professional author](#assign-the-professional-author)
- [Resolve user-owned design choices](#resolve-user-owned-design-choices)
- [Concern contracts](#concern-contracts)
- [Delivery slices](#delivery-slices)
- [Review and revision](#review-and-revision)

Load only when proving a direct profile; preparing, reviewing, or repairing a `module` or `system` design assignment; changing a shared interface, state owner, lifecycle, or schema; running an evidence-producing design batch; or responding to evidence that requires a contract-bearing design change. This reference is the single source for profile triggers and concern coverage. Do not load it merely to execute a `ready` design; follow W's `Read when` pointers to the required concern contracts. Load `work-plan.md` only when W is required and `design-review.md` only when freezing or reviewing a `module` or `system` design.

Treat a legacy code-bearing W without the current profile, map, identities, and review as `repair-required`. Preserve useful content, create a new revision, and re-run the applicable gates. Current development authorization is an external lifecycle record, not part of W completeness.

## W is the map

`WORK.md` holds the human-readable brief, current lifecycle, concern index, delivery slices, validation pointers, and recovery. `design-implementation` owns the professional Design brief and exact design contracts in indexed concern files. The Coordinator owns W lifecycle plus the mechanically derived Design map, Delivery map, traceability, and identities:

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

Create only triggered concerns, plus Coordinator-generated `traceability.yaml` for every `module` or `system`. Every W pointer states path, section, immutable identity, trigger, `Read when`, and readiness. A file absent from the current Design map or traceability binding is outside the design contract.

## Choose the profile

### Direct

Use B without code-design W only when all are true:

- one bounded and reversible behavior change stays within established seams; it may touch multiple files;
- entities, state ownership, identity, invariants, lifecycle, shared or public interfaces, persisted schemas, dependency direction, migration, and failure behavior remain unchanged;
- B can state complete behavior, checks, source base, paths, rollback, and recovery;
- remaining executor choices affect neither another B nor a later technical route; and
- no unresolved user-owned design tradeoff remains.

Record the evidence. Run finding-free draft and frozen packet preflight and Entry schema validation, obtain fresh `AUTHORIZATION_READY` for the complete target, and only then ask the user to authorize that immutable packet, preflight identity, source-base identity, scope, spend, and stop boundary together before code.

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
- without a design, the executor must invent entity meaning, interface behavior, a state owner, runtime transition, failure response, test oracle, or slice boundary.

The Coordinator may choose `direct` only from complete recorded evidence. It does not routinely call the designer to confirm a direct case. A misrouted designer may return `DIRECT_ELIGIBLE` without writing.

## Assign the professional author

For `module` or `system`, the Coordinator creates a W scaffold with fixed Purpose, Scope, parents, source base, exclusions, adopted user decisions, and exclusive write sections. Invoke `design-implementation` in a fresh context with mode `new`, `revision`, or `repair`.

The designer writes only W's Design brief and triggered concern files. The Coordinator then generates Design map rows, Delivery map rows, `traceability.yaml`, design identities, review lifecycle, and B bindings from the exact professional pointers. This mechanical adoption may add identifiers and paths but may not rewrite architecture, domain meaning, interface behavior, flows, technical slices, or verification.

Design authoring is planning and creates no B, proposal identity, reservation, or spend. If a conclusion requires a lower-consequence observation from code execution, a prototype, an experiment, controlled input, an external effect, or protected resources, the designer returns `EVIDENCE_REQUIRED`; the Coordinator obtains that evidence through the existing Q or B path. Do not relabel a runnable, tested, chargeable, irreversible, or protected-resource realization as free design evidence.

## Test decisive feasibility claims

Apply this check inside the existing cold-read implementability work for `module` and `system`; it is not a new gate and does not change the `direct` profile. A decisive feasibility claim is an unestablished, falsifiable claim on which complete delivery of a planned slice depends. It may concern one required capability or several constraints that must hold together. Novelty, complexity, first implementation, absence of a final deliverable, first-identity charging, and ordinary implementation risk do not establish such a claim by themselves.

For every decisive claim, require positive, reviewable grounds for at least one credible end-to-end realization under the same relevant conditions and acceptance meaning. Grounds may come from analysis, proof, inspection, a same-condition example, demonstration, test, prototype, or another direct source appropriate to the deliverable. Negative examples, internal consistency, or a future acceptance plan alone do not establish feasibility.

Decide evidence routing separately from whether the claim needs review. Return `EVIDENCE_REQUIRED` only when current grounds are insufficient and one lower-consequence observation is affordable, reachable, and capable of changing the design verdict. If no such observation exists, do not create a recursive evidence gate or weaken readiness: use current grounds to establish a credible realization, revise the design to remove the unsupported dependency, return the exact parent-owned formal-risk decision, or return the exact blocker when no legal path remains. Work that only the normal formal proposal can test stays subject to its parent and R8 consequence; design work cannot make that proposal free.

Use these questions without creating a new field or artifact:

1. Which claim determines whether the complete slice can be delivered?
2. Which capabilities or interactions depend on it?
3. Which conditions and constraints must hold?
4. What end-to-end realization do the current grounds actually support, and what remains assumed?
5. Is there a lower-consequence observation that can falsify or materially strengthen the claim?

Address every decisive claim before design review, starting with the weakest. Do not enumerate non-blocking risks merely to fill the design.

## Resolve user-owned design choices

Evidence decides technical eligibility. The user decides among eligible options when the difference concerns cost, lock-in, reversibility, maintenance, operations, interface ergonomics, migration disruption, deadline, privacy, safety tolerance, or build-versus-buy preference.

For each such choice:

1. Record alternatives, recommendation, evidence, uncertainty, and consequences in `decisions.md`.
2. Invoke `grill-frontier` with `decision_kind: tradeoff`.
3. Adopt the answer in V, then invoke `design-implementation` to update the owning concern and W brief under a new revision when the answer changes contract-bearing meaning.
4. Give local reversible executor choices explicit bounds instead of asking the user.

Freeze design review only after every user choice needed by the planned slice resolves. After adopted `DESIGN_READY`, complete packet and Entry validation and obtain fresh `AUTHORIZATION_READY`; then ask separately for development authorization against the exact reviewed target and design identity. Design preference is not development permission.

## Concern contracts

`design-implementation` owns the professional content of every triggered concern. Each concern document starts with frontmatter that binds `work_id`, `plan_revision`, `design_contract_identity`, parent versions, status, and generation identity. The Coordinator fills only mechanical binding fields after the professional draft is complete. To avoid a self-referential identity, compute each concern's contract hash from its canonical bytes with the `design_contract_identity` field omitted; the review snapshot separately records the whole-file hash. Give each contract-bearing section an immutable content identity.

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

For each decision, record status, alternatives, technical eligibility, recommendation, evidence, user owner, adopted V, consequence, reconsideration event, and which slices it blocks.

### Verification

Trigger for every `module` or `system` design.

Map each requirement and failure behavior to an observable test oracle. State unit, interface, integration, compatibility, migration, rollback, performance, security, global, and comparison-integrity checks as applicable; fixtures; and evidence paths.

Make each technical slice's observable behavior, blocking dependencies, exact design inputs, distinguishing oracle, failure checks, and safe recovery point authoritative here. The Coordinator later maps those exact pointers to existing B identifiers, worker paths, and evidence destinations without changing their meaning.

Use examples, schemas, state tables, or sequence descriptions whenever prose permits incompatible implementations. A design is not ready while a developer must invent entity meaning, responsibility, interface contract, state owner, runtime transition, failure response, user decision, oracle, or slice boundary.

## Delivery slices

`design-implementation` plans vertical slices that each deliver one observable result through the real seam and records their exact contracts in `verification.md`. The Coordinator summarizes each slice in W's existing Delivery map, assigns its B identifier, and points to the exact technical contract. Do not make an executor read unrelated concerns.

A design, research, or non-code prototype B may resolve one open question. Its worker may only report evidence and proposed wording. It changes no design contract until the Coordinator adopts a new W revision and concern identity.

## Review and revision

The design contract identity binds W Purpose, Scope, Design brief, Design map, User design decisions, Delivery map, applicable Human input contracts, Validation, Definition of done, every indexed concern identity, and normalized `traceability.yaml`. It excludes lifecycle input state, progress, discoveries, recovery, and outcome. Current development authorization is not stored in W at all.

Keep review-attempt identifiers, packet paths, snapshot paths, pending-review state, and adopted-review identity only in W frontmatter and other lifecycle records outside those contract-bearing sections. A contract-bearing section may require an independent versioned review and state its checks, but it must not name the review attempt that will review that same contract. Otherwise each replacement review changes the object being reviewed and creates an identity cycle.

A contract-bearing change creates a new W revision and invalidates dependent `DESIGN_READY` and external development authorization. The executor only proposes the discovery; the Coordinator opens the revision and fixes its scope, `design-implementation` updates the owning professional contract, the Coordinator regenerates traceability and affected B bindings, a fresh reviewer reviews the new immutable design, and the user separately reauthorizes every affected development scope after authorization-readiness review. Lifecycle evidence alone does not change the revision. When design changes parent legality, solution identity, permitted operations, module scope, measurement, or promotion, stop and return to the owning parent stage.

Design planning is complete when the designer has returned `DRAFT_READY`, the Coordinator's mechanical map and traceability cover every triggered concern and exact technical-slice pointer without semantic drift, every user choice resolves, and the frozen snapshot is ready for `design-review.md`. The invocation result is not a W lifecycle state or readiness verdict; only `review-frontier` may return `DESIGN_READY`.
