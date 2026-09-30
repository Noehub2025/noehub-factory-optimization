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

Load when deciding whether an unresolved technical question needs professional design, assigning or revising that design, or reviewing its meaning. This reference owns design involvement, scope and concern coverage. To execute an adopted design, follow its relevant pointers instead. Load `work-plan.md` only when W is needed and `design-review.md` only for a required independent design judgment.

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

Use W when implementation needs a shared map of design agreements and delivery obligations. A local professional answer may stay in its assigned existing work or design record. For W, create only concerns needed to state those agreements; maintain `traceability.yaml` when selecting stable delivery obligations through W. Every W pointer states path, section, applicability, `Read when` and readiness. Use [W saved references](work-plan.md#saved-design-references) for selected delivery scope. A file absent from the Design map is outside the W contract.

## Choose the profile

### Direct

Continue directly when established tools, interfaces and agreements settle the important technical choices for the proposed work. The implementation owner handles ordinary choices and affected checks within the assigned scope. Reuse sufficient source context; no separate proof of a direct profile is needed. Apply [User decisions](user-decisions.md) and Entry only for the next action's actual requirements.

### Module

Use to describe professional design focused on one module or stable seam. Update only the agreements and concerns the current problem needs; reuse existing content.

### System

Use when unresolved interactions, ownership, migration or other consequential choices need a coordinated design across the promised realization. Full design is appropriate when that problem requires it; file count, an external operation or changed failure handling alone does not establish that need.

Decide professional involvement, documentation scope and independent review separately. Invoke `design-implementation` for an important technical question that existing agreements do not settle, such as shared behavior, state ownership, migration or a consequential architecture choice. Give it that question and existing grounds. Profile names describe scope; they do not impose a document bundle or review. Use [Assurance by consequence](batch-evaluation.md#assurance-by-consequence) for any remaining independent judgment. Unknown research benefit and ordinary implementation choices stay in development; a misrouted designer may return `DIRECT_ELIGIBLE` without writing.

## Assign the professional author

Give `design-implementation` the research problem, unresolved technical question, relevant existing agreements and evidence, actual constraints and an exclusive write surface in existing work or design material. Create a W scaffold only when the work needs the map described above. Keep tentative combinations and methods in professional reasoning, not binding Purpose or Scope. Apply [Evidence access](worker-interfaces.md#evidence-access); use a fresh context with mode `new`, `revision`, or `repair`.

Design defines the deliverable's behavior, necessary architecture, interfaces, state ownership, technical dependencies, and acceptance criteria. The executor owns ordinary work breakdown, internal order, temporary material, support operations, and local repair inside the authorized envelope. Refine choices through [Working assignments](worker-interfaces.md#working-assignments); an unchanged investment does not waive an affected design or measurement owner's decision.

If an unpublished scaffold mistakes a tentative choice or incidental workflow method for a binding requirement, the designer and Coordinator correct their respective sections in the same task. This creates no new W, revision, review or repair record. Retain actual constraints; a change to adopted technical meaning still follows the affected revision path below. An earlier positive review is reusable evidence, not a reason to preserve a choice whose supporting premise has been contradicted.

When the design uses or replaces an existing capability, apply [Reuse working knowledge](batch-current.md#reuse-working-knowledge) within the assigned scope before inventing another interface or interpretation.

Publication eligibility, authority, accounting, and result closure stay with their existing workflow or parent owners; reference their rules rather than reproducing their operation in W. Apply [Professional output and workflow decisions](worker-interfaces.md#professional-output-and-workflow-decisions) when Design proposes another review or stage. Explicit user and parent requirements retain their original owner; their appearance in W does not make them Design-owned.

Apply [Decision-bearing thresholds](frontier-core.md#decision-bearing-thresholds) only to a condition that can change the acceptance or disposition of the planned work. W owns an implementation-acceptance threshold only when that consequence belongs to the designed module or system; cite a parent, Measurement Definition, or direct-B owner instead of copying its threshold into Design. When W does own the threshold, state its basis, applicable workload and statistic, allowed consequence, and reconsideration trigger in Decisions or Verification. Reusing an `unchanged` threshold requires the complete semantic match defined by Frontier Core, not merely the same value.

A method or sequence belongs in the relevant professional contract when it determines deliverable behavior, a necessary interface, evidence meaning, or an irreversible consequence. When a workflow, measurement facility, or publication system is itself the deliverable, design that system normally. Decide from the deliverable and consequences, not the task label or technology. Apply this distinction during ordinary authoring, without a classification record or additional gate.

The designer writes the assigned professional answer or affected design content. When W carries delivery obligations, the Coordinator derives its maps and traceability from the professional pointers and stable slice keys. Prepare a review subject only when independent judgment is needed. Preserve professional meaning and leave B assignments, internal evidence destinations and runtime status with their execution owners.

### Early design feedback

When a consequential assumption needs practical feedback, the designer names the uncertainty and smallest observation that could change the design. The Coordinator first reuses existing evidence or arranges that observation with the implementation or evidence-work owner in the current authorized work, then returns the facts to the original designer to continue. Use existing assignment and progress records. This coordination does not itself require a new Q, B, review, terminal result or user pause; create further work only when the observation's actual scope or effects require it. Test a decisive real-interface assumption early enough to revise the affected design before dependent construction, rather than leaving the first useful feedback to review.

Design authoring remains planning, with no execution authority or automatic proposal charge. Evidence work retains its owner's write scope and the normal controls for its actual effects, protected resources and charge events. Use `EVIDENCE_REQUIRED` only under [Test decisive feasibility claims](#test-decisive-feasibility-claims); it requests the missing observation, not a new evidence stage. Ordinary implementation feedback stays in development. A formal proposal does not become free by calling it design evidence.

## Ground consequential design choices

Apply [Prospective reasoning](learning-loop.md#prospective-reasoning) to design choices whose downstream effects could change the selected mechanism or useful feedback. Preserve consequential joint behavior and duration, including opportunities created by the change; do not turn each possible effect into a protection or explanatory prerequisite. Reuse settled understanding. This also applies to important choices made directly under the Direct profile, without requiring a separate design invocation.

For choices that can materially change the current observation or its cost, explain in the existing Design brief or Decisions why the realization is worth trying: plausible objective improvement or useful learning, supporting facts and assumptions, and what result would reduce its appeal. Carry the selected research rationale and critical assumptions into these choices. The professional author may replace, combine or remove proposed components with technical reasons in the same design; preserve the problem and address its reasoning, not the initial answer. Compare only alternatives that could change this choice, using existing evidence, relevant source inspection or simple calculations. Reuse sufficient reasoning on continuation; revisit grounds affected by new facts, not every invocation.

For frontier-seeking work, apply [Technical potential](learning-loop.md#technical-potential) to the core mechanism, not just an editable local detail. Strong references supply capabilities and comparisons, not a mandatory architecture. A selected whole idea must survive decomposition: retain the joint behavior that could change the objective, even when it requires several coordinated changes. A prerequisite check is an internal step, not a substitute deliverable or an admission gate for the mechanism. Reuse sufficient conceptual work; further modelling or explanation must justify its cost against direct development. Preserve the coordinated changes needed to investigate or realize the mechanism; economical implementation and support must not remove its advantage source.

At ordinary design completion, check that the intended change, necessary implementation semantics and useful evaluation are sufficiently clear for the selected commitment. An untested conjecture can supply the reason to try it; unknown benefit or internal causal explanation is not a completion defect. Resolve a missing technical decision that prevents the next work through its owner. Reconsider investment when concrete evidence challenges the rationale or remaining cost, using the existing trigger rather than returning every unanswered research question. Technical readiness, cheap execution and relabeling work as a feasibility probe do not by themselves justify its priority.

Choose scale, duration and conditions that can answer the pending question, retaining the interactions on which a whole-solution hypothesis depends. Use normal slices and integration to reach that observation. Interpretability means knowing what changed, what was observed and the comparison's limits, not explaining every internal cause. Explanatory models, scenario calculations and component attribution are optional unless needed for a concrete decision or explicitly promised deliverable; choose such analysis under [Learning Loop](learning-loop.md#when-to-reconsider-investment). A prerequisite test supports only what it tests: a local defect or absent activation does not automatically reject the route, while evidence against a genuine necessary condition may exclude the affected scope. Do not require activation, profit or hypothesis success in advance. Familiarity, small size and easy verification describe cost, not value; a larger probe earns its cost only when the extra observation matters.

Keep source claims at their supported scope. A weak warning is a hypothesis to assess, not a whole-route exclusion; a claim limit bounds conclusions but supplies no selection rationale. A short explanation suffices for an evident choice. This is part of ordinary design, not a new heading requirement, alternative quota, economic model, optimality proof, research assignment or review gate.

Derive supporting requirements from the promised observation or deliverable and its actual effects before prescribing facilities. Reuse existing execution, accounting and recovery capabilities. Add capability only for a concrete unmet need of this use, not generic completeness, speculative future use or easier review. Missing optional attribution limits its explanation, not an independently valid outcome. Do not change candidate behavior solely to simplify diagnostics or make diagnostic-only failure trigger fallback; missing state needed for correct action still constrains that action. Keep the rationale with the affected choice rather than creating a requirement inventory. Simplify the support around an ambitious, informative experiment; do not shrink the experiment until it can no longer test its hypothesis.

### Preserve the mechanism in the first realization

Before dependent construction, work through the few relationships that can supply the selected advantage: relevant inputs, state changes, timing, shared resources and objective effects. Carry the originating rationale into selection and design; agreement among the selected task, design and code does not establish fidelity when all inherited the same reduced scope. A worked choice, calculation, interface or pseudocode should resolve materially different interpretations and include the interaction or delayed effect most likely to disappear. Reuse applicable examples. This is ordinary design content, not a new document, review or proof that the hypothesis succeeds.

Make the relevant organization executable: which decisions are joint, which can be separated, who owns shared state or resources, and how admission, allocation and execution compose under the same constraints. Whole-candidate evaluation and an inactive formal search decomposition do not waive this work. A compact rule or retained programme may suffice; module names or a larger score do not establish coordination. Resolve only meaning needed by the next construction, or select development that investigates it. Under Direct work the implementer reuses settled agreements and owns ordinary choices; a newly unresolved consequential relationship returns to its professional owner despite an earlier settled label.

Connect the estimate or selection to what execution actually does and how its effects are observed. Prefer shared domain meaning or an explicit translation over inconsistent formulas. Arrange the first useful end-to-end implementation to preserve the critical relationship; internal construction slices need not individually deliver it. Reducing exposure, support code or candidate count must not silently remove the advantage. A library API or convenient code boundary is an implementation choice, not a replacement objective.

For a consequential simplification, distinguish retained behavior with applicable grounds, adequacy that the selected work will investigate, and omitted or changed behavior. Retain its reason, expected effect and scope in the existing decision. A short horizon, independent score, menu or cap may remove the relationship even when every action is legal. A compact approximation may preserve it. Use the cheapest relevant inspection, calculation, contrasting case, prototype or target observation; do not require exact optimization or full simulation. A passing case in which the disputed interaction is inactive cannot validate that interaction, and a changed input need not change the correct action.

A worked example can settle design meaning; realized coordination needs applicable execution evidence engaging the relevant interaction. Objective advantage needs an appropriate comparison. Keep these claims separate in existing progress, not new lifecycle states. Useful partial feedback may precede a full-mechanism test and cannot silently close its unanswered question. Unknown adequacy permits a worthwhile investigation; it is neither proof of failure nor permission to claim that the implementation already preserves the advantage.

Resolve missing meaning needed by dependent construction, or select a useful bounded investigation of it. Implementation may be the cheapest way to learn even when analysis is possible. When behavior is deliberately omitted, repair within the commitment or return the changed proposition to its existing owner before dependent use. Preserve the original unanswered question and the actual allocation consequence of a partial observation; a disclaimer, owner approval or retrospective prototype label cannot make a narrow realization a full-mechanism test.

### Choose a realization on the same required behavior

For a consequential capability, compare credible custom, mature-component, offline construction/calibration/reference and mixed paths using applicable research and missing primary-source facts. Explain what the selected path supplies and what adaptation or modeling remains. These are options, not a product quota or a requirement to install a library. Make this choice or select its useful investigation before extensive dependent construction makes reuse expensive.

Compare the same required behavior and next useful observation, including remaining modeling, implementation, integration and validation costs on both sides. Separate the current probe from later liabilities. Existing code's missing semantics are not free, and a new path does not bear an entire hypothetical deployment cycle against one incumbent test. A lower capability ceiling stays visible in the allocation; familiarity and small size alone do not establish value.

Unknown compatibility or runtime is not a prohibition. When it decides against a credible path, compare the smallest resolving observation with other current work; defer only on substantive current cost, opportunity or actual boundary grounds. Retain that basis and reopening condition in the existing choice. Reconsider when the affected choice is reused and the unresolved premise matters, or when new evidence changes it; a local condition such as waiting for custom code to fail cannot cancel this trigger. Still-applicable grounds can justify continuing a deferral without expiry timers or repeated benchmarks.

Judge runtime and offline use separately: a packaging or latency restriction does not prohibit offline construction or reference use. A local import proves neither hosted eligibility nor model adequacy. A solver's optimum or bound applies to its encoded problem unless a justified relation supports a broader claim; independent code sharing a wrong assumption does not validate it. Apply [Intended use, tools and payment](user-decisions.md#intended-use-tools-and-payment) to actual rights and effects, without creating a package approval step.

### Design consequential parameter choices

Identify the few influential adjustable coefficients, cutoffs, resolutions or candidate ranges: their meaning, initial basis, admissible range and consequential interactions. Distinguish supplied rules and user constraints from empirical choices; runtime option enumeration does not establish parameter optimization. Expose settings needed for worthwhile search without rewriting the mechanism. A categorical setting that changes the mechanism retains that structural meaning.

Co-design the first useful observation with one or several informative configurations under [Parameter search and first feedback](learning-loop.md#parameter-search-and-first-feedback). Search cannot repair a representation that cannot express the selected relationship. Neither fixed defaults nor a mandatory tuning study are universal requirements.

## Test decisive feasibility claims

Apply this check inside the existing cold-read implementability work for `module` and `system`; it is not a new gate and does not change the `direct` profile. First apply [Research hypotheses and action prerequisites](planning-records.md#research-hypotheses-and-action-prerequisites) to the promised output. A decisive feasibility claim concerns a prerequisite for the next action or promised delivery, not an unknown the authorized development or experiment is intended to resolve. A feasibility experiment may fail to realize its proposed mechanism; it needs a usable observation of that attempt, not an earlier prototype proving the same question. Full delivery retains its acceptance obligations, including a formal proof when that is part of the requested deliverable. Novelty, complexity, first implementation, absence of a final deliverable, first-identity charging, and ordinary implementation risk do not establish a prerequisite by themselves.

For a genuine prerequisite, require grounds proportionate to the dependent action and its consequences. Analysis, inspection, an applicable example, test, prototype or other direct evidence may suffice. Ordinary development can obtain feasibility feedback before the dependent use; name only missing inputs or uncontrolled effects that actually prevent that use. A future acceptance plan does not establish a required capability, but advance proof of benefit or a complete causal pathway is not such a capability. When an optional model fails, withdraw its unsupported conclusions and preserve independent implementation or evaluation paths through the existing owner.

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

Resolve user choices needed by the dependent work, then adopt the supported design and any required independent judgment. Return to [Entry planning](entry-and-planning.md) when the first B needs it, or [same-B continuation](batch-current.md#boundary-preserving-continuation) for existing work. A design-only request may finish here under the [Coordinator's completion rule](../SKILL.md#recover-and-choose-the-current-action). Reuse applicable V; independent work continues while another design dependency remains unresolved.

## Concern contracts

`design-implementation` owns the needed professional content. The concerns below are reference coverage for an actual design question, not a file or field checklist. Use only details that affect the promised use, retaining existing agreements. For W, inherit its saved version through [W saved references](work-plan.md#saved-design-references); concern files need no repeated design identity or parent frontmatter.

### Architecture

Use when module responsibilities, boundaries or integration need a new or revised agreement.

State system context, current and proposed modules, responsibilities, boundaries, dependency direction, runtime or deployment topology when relevant, integration seam, protected components, alternatives, and rejected shapes.

### Domain

Trigger when entity meaning, identity, state, ownership, lifecycle, persistence, or invariants change.

Define core entities and value objects, identifiers, owner of each state, lifecycle and transitions, invariants, invalid states, persistence meaning, and mapping to existing concepts.

### Interfaces

Trigger when a caller-facing seam, schema, command, event, file, configuration contract, or external dependency changes.

Name callers and providers; inputs and outputs; schemas and examples; preconditions and postconditions; errors; side effects; idempotency; compatibility; versioning; timeouts; and stable test seam.

### Flows

Use when sequencing, data movement, asynchronous work or failure recovery needs an agreement that affects the promised use.

Describe end-to-end control and data flow; state owner at each step; concurrency; ordering; retries; timeouts; cancellation; failure propagation; recovery; observability; and security or privacy boundaries.

### Decisions

Trigger for alternatives, user tradeoffs, migration, hard-to-reverse choices, material quality limits, or unresolved questions.

For each decision, record status, alternatives, technical eligibility, recommendation, evidence, consequence, reconsideration event, and which slices it blocks. Cite a user owner and adopted V only when a user decision applies; ordinary technical choices do not create one.

### Verification

Use when designed behavior needs explicit acceptance or stable delivery obligations. A local answer may reference the existing applicable checks instead.

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

A contract-bearing W change needs a scoped W revision. The executor preserves the discovery; the Coordinator scopes the affected work; `design-implementation` updates professional meaning; the Coordinator updates affected bindings. Select independent review under [Assurance by consequence](batch-evaluation.md#assurance-by-consequence), rather than from the revision alone. Follow [Boundary-preserving continuation](batch-current.md#boundary-preserving-continuation); changed technical meaning does not itself require another user answer. Lifecycle evidence alone does not change Design. A changed parent requirement returns to its owning stage.

Apply assignment ownership prospectively. Preserve historical verdicts and explicit constraints. Repair conflicting obligations in the next necessary scoped revision and reuse unaffected evidence and review conclusions. A corrected reference or guidance change creates no new design revision by itself.

Design authoring is complete when the assigned question has a supported, implementable answer or a specific unresolved dependency. Adopt it in the existing work; where W is used, update its affected content and required delivery bindings. Proceed when the next use is sufficiently supported, obtaining an independent judgment only when required. Only `review-frontier` issues `DESIGN_READY`; adoption without a new review creates no substitute verdict or review record.
