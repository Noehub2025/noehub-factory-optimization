# Frontier Technical Design

## Contents

- [W is the map](#w-is-the-map)
- [Choose the profile](#choose-the-profile)
- [Resolve user-owned design choices](#resolve-user-owned-design-choices)
- [Concern contracts](#concern-contracts)
- [Delivery slices](#delivery-slices)
- [Review and revision](#review-and-revision)

Load only when choosing a code-design profile; drafting, reviewing, or repairing a `module` or `system` design; changing a public interface or schema; running a design batch; or responding to evidence that requires a contract-bearing design change. Choose the profile and applicable concern files from this reference. Do not load it merely to execute a `ready` design; follow W's `Read when` pointers to the required concern contracts. Load `work-plan.md` only when W is required and `design-review.md` only when freezing or reviewing a `module` or `system` design.

Treat a legacy code-bearing W without the current profile, map, identities, and review as `repair-required`. Preserve useful content, create a new revision, and re-run the applicable gates. Current development authorization is an external lifecycle record, not part of W completeness.

## W is the map

`WORK.md` holds the human-readable brief, current lifecycle, concern index, delivery slices, validation pointers, and recovery. Exact design contracts live only in indexed concern files:

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

Create only triggered concerns, plus `traceability.yaml` for every `module` or `system`. Every W pointer states path, section, immutable identity, trigger, `Read when`, and readiness. A file absent from the current Design map or traceability binding is outside the design contract.

## Choose the profile

### Direct

Use B without code-design W only when all are true:

- one local reversible change uses an established seam;
- entities, state ownership, public interfaces, schemas, dependencies, migration, and failure behavior remain unchanged;
- B can state complete behavior, checks, source base, paths, rollback, and recovery;
- no unresolved user-owned design tradeoff remains.

Record the evidence. Run finding-free draft and frozen packet preflight and Entry schema validation, obtain fresh `AUTHORIZATION_READY` for the complete target, and only then ask the user to authorize that immutable packet, preflight identity, source-base identity, scope, spend, and stop boundary together before code.

### Module

Use when one component or stable seam changes and callers can depend on a small contract. Create W plus `architecture`, `interfaces`, `flows`, and `verification`; add `domain` or `decisions` when triggered.

### System

Use when work spans components, changes state ownership or lifecycle, introduces migration or external operations, or requires coordinated rollout and recovery. Create W and every applicable concern.

Profile selection is complete only when a fresh reviewer can reproduce it from cited task and repository facts. Understating the profile is a design finding.

## Resolve user-owned design choices

Evidence decides technical eligibility. The user decides among eligible options when the difference concerns cost, lock-in, reversibility, maintenance, operations, interface ergonomics, migration disruption, deadline, privacy, safety tolerance, or build-versus-buy preference.

For each such choice:

1. Record alternatives, recommendation, evidence, uncertainty, and consequences in `decisions.md`.
2. Invoke `grill-frontier` with `decision_kind: tradeoff`.
3. Adopt the answer in V and update the owning concern and W brief.
4. Give local reversible executor choices explicit bounds instead of asking the user.

Freeze design review only after every user choice needed by the planned slice resolves. After adopted `DESIGN_READY`, complete packet and Entry validation and obtain fresh `AUTHORIZATION_READY`; then ask separately for development authorization against the exact reviewed target and design identity. Design preference is not development permission.

## Concern contracts

Each concern document starts with frontmatter that binds `work_id`, `plan_revision`, `design_contract_identity`, parent versions, status, and generation identity. To avoid a self-referential identity, compute each concern's contract hash from its canonical bytes with the `design_contract_identity` field omitted; the review snapshot separately records the whole-file hash. Give each contract-bearing section an immutable content identity.

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

Map each requirement and failure behavior to an observable test oracle. State unit, interface, integration, compatibility, migration, rollback, performance, security, global, and comparison-integrity checks as applicable; fixtures; evidence paths; and which B runs each check.

Use examples, schemas, state tables, or sequence descriptions whenever prose permits incompatible implementations. A design is not ready while a developer must invent entity meaning, responsibility, interface contract, state owner, runtime transition, failure response, user decision, oracle, or slice boundary.

## Delivery slices

Plan vertical slices that each deliver one observable result through the real seam. Record exact required design inputs, true blocking edges, distinguishing check, and safe recovery point. Do not make an executor read unrelated concerns.

A design, research, or non-code prototype B may resolve one open question. Its worker may only report evidence and proposed wording. It changes no design contract until the Coordinator adopts a new W revision and concern identity.

## Review and revision

The design contract identity binds W Purpose, Scope, Design brief, Design map, User design decisions, Delivery map, applicable Human input contracts, Validation, Definition of done, every indexed concern identity, and normalized `traceability.yaml`. It excludes lifecycle input state, progress, discoveries, recovery, and outcome. Current development authorization is not stored in W at all.

Keep review-attempt identifiers, packet paths, snapshot paths, pending-review state, and adopted-review identity only in W frontmatter and other lifecycle records outside those contract-bearing sections. A contract-bearing section may require an independent versioned review and state its checks, but it must not name the review attempt that will review that same contract. Otherwise each replacement review changes the object being reviewed and creates an identity cycle.

A contract-bearing change creates a new W revision and invalidates dependent `DESIGN_READY` and external development authorization. The worker only proposes the discovery; the Coordinator updates the owning contract, traceability, and affected B records, a fresh reviewer reviews the new immutable design, and the user separately reauthorizes every affected development scope after authorization-readiness review. Lifecycle evidence alone does not change the revision. When design changes parent legality, solution identity, permitted operations, module scope, measurement, or promotion, stop and return to the owning parent stage.

Design planning is complete when the current map covers every triggered concern, each planned slice names only its required inputs, every user choice resolves, and the frozen snapshot is ready for `design-review.md`.
