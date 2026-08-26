# Frontier Technical Design

## Contents

- [W is the map](#w-is-the-map)
- [Choose the profile](#choose-the-profile)
- [Assign the professional author](#assign-the-professional-author)
- [Constrain effects, not convenient forms](#constrain-effects-not-convenient-forms)
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

For `module` or `system`, the Coordinator creates a W scaffold with fixed Purpose, semantic Scope, parents, source requirements, design-review repository evidence, exclusions, adopted user decisions, and exclusive write sections. Invoke `design-implementation` in a fresh context with mode `new`, `revision`, or `repair`.

Design defines the deliverable's behavior, necessary architecture, interfaces, state ownership, technical dependencies, and acceptance criteria. The executor owns ordinary work breakdown, internal order, temporary material, support operations, and local repair inside the authorized envelope. These choices need no prior enumeration in Design and do not themselves change its contract.

Publication eligibility, authority, accounting, and result closure stay with their existing workflow or parent owners; reference their rules rather than reproducing their operation in W. Explicit user and parent requirements remain binding with the appropriate owner. Their origin, repetition, or inclusion in an earlier assignment does not make them Design-owned.

A method or sequence belongs in the relevant professional contract when it determines deliverable behavior, a necessary interface, evidence meaning, or an irreversible consequence. When a workflow, measurement facility, or publication system is itself the deliverable, design that system normally. Decide from the deliverable and consequences, not the task label or technology. Apply this distinction during ordinary authoring, without a classification record or additional gate.

The designer writes only W's Design brief and triggered concern files. The Coordinator then generates Design map rows, stable Delivery map rows, `traceability.yaml`, design identities, and review lifecycle from the exact professional pointers. This mechanical adoption may add stable concern or slice identities but may not assign a future B, attempt namespace, internal evidence destination, or runtime status to Design, and may not rewrite architecture, domain meaning, interface behavior, flows, technical slices, or verification.

Design authoring is planning and creates no B, proposal identity, reservation, or spend. If a conclusion requires a lower-consequence observation from code execution, a prototype, an experiment, controlled input, an external effect, or protected resources, the designer returns `EVIDENCE_REQUIRED`; the Coordinator obtains that evidence through the existing Q or B path. Do not relabel a runnable, tested, chargeable, irreversible, or protected-resource realization as free design evidence.

## Test decisive feasibility claims

Apply this check inside the existing cold-read implementability work for `module` and `system`; it is not a new gate and does not change the `direct` profile. First apply [Research hypotheses and action prerequisites](planning-records.md#research-hypotheses-and-action-prerequisites) to the promised output. A research slice must support an executable, interpretable observation, not establish its hypothesis in advance. Full delivery retains its acceptance obligations. A decisive feasibility claim is an unestablished, falsifiable claim on which that promised output depends. Novelty, complexity, first implementation, absence of a final deliverable, first-identity charging, and ordinary implementation risk do not establish such a claim by themselves.

For every decisive claim, require positive, reviewable grounds for a credible realization of the promised output under its relevant conditions and acceptance meaning. Grounds may come from analysis, proof, inspection, a same-condition example, demonstration, test, prototype, or another direct source appropriate to that output. Negative examples, internal consistency, or a future acceptance plan alone do not establish its feasibility.

Decide evidence routing separately from whether the claim needs review. Return `EVIDENCE_REQUIRED` only when current grounds are insufficient and one lower-consequence observation is affordable, reachable, and capable of changing the design verdict. If no such observation exists, do not create a recursive evidence gate or weaken readiness: use current grounds to establish a credible realization, revise the design to remove the unsupported dependency, return the exact parent-owned formal-risk decision, or return the exact blocker when no legal path remains. Work that only the normal formal proposal can test stays subject to its parent and R8 consequence; design work cannot make that proposal free.

Use these questions without creating a new field or artifact:

1. Which claim determines whether the complete slice can be delivered?
2. Which capabilities or interactions depend on it?
3. Which conditions and constraints must hold?
4. What end-to-end realization do the current grounds actually support, and what remains assumed?
5. Is there a lower-consequence observation that can falsify or materially strengthen the claim?

Address every decisive claim before design review, starting with the weakest. Do not enumerate non-blocking risks merely to fill the design.

## Constrain effects, not convenient forms

When an implementation-form restriction materially affects a planned slice, name the behavior, interface, invariant, risk, or verification property it protects and explain the causal relation. A reviewer may require repair when that current protection basis is absent or contradicted, or may cite one concrete Design-compatible realization showing that the restriction makes the slice infeasible or materially more complex without a current protection rationale. The reviewer need not prove that the restriction has no value in every setting; the Design owns the current rationale. A theoretically narrower rule, an unenumerated alternative, unfamiliarity, novelty, complexity, or ordinary implementation risk is not a finding by itself. If the restriction does not materially affect the current slice, treat it at most as an advisory.

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

Map each requirement and failure behavior to an observable test oracle. State unit, interface, integration, compatibility, migration, rollback, performance, security, global, and comparison-integrity checks as applicable; fixtures; evidence meaning and format; producer and consumer roles; and any stable external-interface path.

Make each delivery slice's observable behavior, stable prerequisites, exact design inputs, distinguishing oracle, failure checks, and safe recovery point authoritative here. A delivery slice is a stable obligation, not the executor's mutable work breakdown. Entry later binds the exact obligations one B must satisfy to its execution source, worker paths, and internal output destinations without changing their meaning.

Use examples, schemas, state tables, or sequence descriptions whenever prose permits incompatible implementations. A design is not ready while a developer must invent entity meaning, responsibility, interface contract, state owner, runtime transition, failure response, user decision, oracle, or slice boundary.

## Delivery slices

`design-implementation` defines vertical delivery obligations that each produce one observable result through the real seam and records their exact contracts in `verification.md`. Together they must cover the complete realization and its integration check. The Coordinator summarizes each obligation in W's Delivery map under a stable technical name and immutable verification pointer. Entry, not Design, later assigns an exact B and realization paths. One B may satisfy several obligations before one formal publication; obligations never create their own B, candidate, proposal, review, or charge lifecycle. Do not make an executor read unrelated concerns.

Execution owns its mutable work breakdown and may add, remove, merge, replace, or reorder internal steps while the B envelope and delivery obligations remain satisfied. Evidence that an obligation, seam, ownership, acceptance meaning, or load-bearing design assumption must change returns to `design-implementation` as a scoped revision. A local defect, failed check, or inconvenient implementation shape remains implementation feedback.

A design, research, or non-code prototype B may resolve one open question. Its worker may only report evidence and proposed wording. It changes no design contract until the Coordinator adopts a new W revision and concern identity.

## Review and revision

The design contract identity binds W Purpose, semantic Scope, Design brief, Design map, User design decisions, stable Delivery map, applicable Human input contracts, Validation, Definition of done, every indexed concern identity, the exact repository-evidence snapshot used for review, and normalized `traceability.yaml`. It excludes future execution assignment, attempt namespace, internal review or recovery paths, internal evidence destinations, runtime status, lifecycle input state, progress, discoveries, recovery, outcome, and current development authorization.

The review evidence snapshot proves which repository facts supported the Design. Entry separately binds the exact execution `source_base_identity`. A later execution source may differ only under compatibility conditions already stated by Design. When an exact source identity is itself design meaning—for example a required fixed ancestor, preserved bytes, or pre-migration state—Design must state that constraint and Entry must satisfy it; Entry may not invent a compatibility rule.

For new design identities, `traceability.yaml` indexes stable technical slices rather than B realizations. A design identity that already had an adopted, valid `DESIGN_READY` before this authoring rule keeps its exact historical `batches` form for audit under its original authority. Every later design identity, including a new revision of that W, uses the stable-slice form; a new design review must not return `DESIGN_READY` for the historical B-keyed form. This is a prospective change to the existing traceability contract shape, not a new contract family, version field, or identity algorithm.

Keep review-attempt identifiers, packet paths, snapshot paths, pending-review state, and adopted-review identity only in W frontmatter and other lifecycle records outside those contract-bearing sections. A contract-bearing section may require an independent versioned review and state its checks, but it must not name the review attempt that will review that same contract. Otherwise each replacement review changes the object being reviewed and creates an identity cycle.

A contract-bearing change needs a new W revision and fresh technical review. The executor preserves the discovery; the Coordinator scopes the revision; `design-implementation` updates professional meaning; the Coordinator updates mechanical bindings. Follow [Boundary-preserving continuation](batch-interface.md#boundary-preserving-continuation) for reuse of the original explicit authority or return to Entry. Do not require a new user answer solely because a delegated technical concern changed. Lifecycle evidence alone does not change Design. A change to parent legality, permitted operations, acceptance, measurement meaning, or promotion returns to its owning stage.

Apply assignment ownership prospectively. Preserve historical snapshots, verdicts, and explicit constraints; do not reopen them to tidy wording or as a prerequisite for unaffected work. When a frozen mandatory workflow clause actually obstructs current work, address the related conflicting obligations together in the next necessary scoped revision through the existing complete-review and authority path. Reuse unchanged work and evidence, not an old review or authorization for a changed identity. Nonbinding guidance needs no replacement identity.

Design planning is complete when the designer has returned `DRAFT_READY`, the Coordinator's mechanical map and traceability cover every triggered concern and exact technical-slice pointer without semantic drift, every user choice resolves, and the frozen snapshot is ready for `design-review.md`. The invocation result is not a W lifecycle state or readiness verdict; only `review-frontier` may return `DESIGN_READY`.
