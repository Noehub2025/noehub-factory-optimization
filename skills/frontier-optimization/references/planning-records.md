# Frontier Planning Records

Load only when reading or writing T, V, B, E, or Q. This file is their sole template source. Use one monotonic namespace per prefix and never change assigned meaning.

## Contents

- [T: route](#t-route)
- [V: user decision](#v-user-decision)
- [B: batch plan](#b-batch-plan)
- [B terminal outcome](#b-terminal-outcome)
- [E: evaluated result](#e-evaluated-result)
- [Q: research finding](#q-research-finding)

## T: route

Create T for each technically eligible campaign-baseline candidate. Later direct work needs T only when it spans B records or competes with another route.

```markdown
## T001: <technical route>

- Recorded at: <ISO-8601 datetime>
- Campaign-baseline role: <candidate | not applicable>
- Produced by: <established approach, Q, repository evidence, E, D, failure finding, functional transfer or recombination, migration or reorganization, new mechanism reasoning, or a combination; sources are peers>
- Starting records: <decision-relevant observations, constraints, source mechanisms, and identifiers>
- Reviewed scope: <forms, operations, or modules>
- Improvement mechanism: <proposed limiting or enabling mechanism, permitted change, and expected causal path to the parent objective>
- Why it can carry optimization: <expected behavior, usable optimization surfaces, feedback path, and known headroom or limits>
- Iteration shape: <one-shot | repeated comparable evidence expected | repeated evidence not comparable, with reason>
- Prospective progress rule: <expectation envelope, meaningful threshold, mechanism checkpoint, reachability condition, or not applicable with reason>
- Progress-rule source: <parent, R8, D, Q, measurement resolution, or explicit reasoning fixed before the governed spend>
- Tradeoffs: <implementation burden, reversibility, maintenance, dependencies, transfer mismatch, and user-owned consequences>
- Assumptions: <each load-bearing data, coverage, label, feedback, evaluator, compute, access, dependency, or other feasibility prerequisite, with satisfied evidence, a bounded prerequisite-first path and pass/fail observation, or unavailable disposition>
- Depends on: <identifiers, including prerequisite checks that must pass before dependent work, or None>
- Maximum allocation: <amount and unit>
- Next checkpoint: <earliest affordable bounded output or discriminating test>
- First performance check: <comparison or decision result and parent-approved feedback>
- Replacement boundary: <exact mechanism boundary beyond which a new T and strategic Replan are required; parts that may improve or be replaced; stable measurement or evidence interfaces>
- Disqualifying evidence: <competing explanation, transfer mismatch, failed prerequisite, or other observable result that falsifies the causal path or makes the route ineligible or not worth continuing>
- Continue when: <observable result>
- Stop or combine when: <condition and affected routes>
- Status: <proposed | active>
```

The T fields must preserve one evidence-bounded chain: observation or constraint -> mechanism -> permitted change -> causal path -> competing explanation or transfer mismatch -> disconfirming observation -> earliest affordable discriminating check. A transferred or recombined route must map the source function and expected behavior to the target constraint and name where the transfer fails. Surface resemblance is insufficient.

Technical conceivability is not eligibility. Every load-bearing prerequisite must be satisfied by cited current evidence, assigned one bounded and funded prerequisite-first path, or dispositioned as unavailable within current scope, Budget, authority, or decision horizon. While a prerequisite remains unresolved, no dependent candidate development, general tuning, evaluation, integration, or performance claim may be planned. A failed prerequisite activates the T disqualifying consequence until new evidence passes the applicable Entry or Replan gate.

## V: user decision

```markdown
## V001: <value or authorization choice>

- Recorded at: <ISO-8601 datetime>
- Campaign generation: <positive integer>
- Decision kind: <tradeoff | authorization>
- Authorization class: <campaign-opening | execution | not applicable for tradeoff>
- Decision: <exact user-owned choice>
- Evidence presented: <identifiers or stable links>
- Alternatives: <technically eligible options for tradeoff; authorize, decline, and conditional authorization for execution; current explicit request for campaign-opening>
- Recommendation presented: <recommended option and evidence-bounded reason or None>
- Applies to: <routes, batches, resources, or campaign choice>
- Bound object: <prior closeout, unchanged parents, next generation, inherited Budget, and planning-only zero-spend boundary for campaign-opening; exact AUTHORIZATION_READY target, reviewed design contract and scope, immutable direct packet, preflight and source, layout, or resource for execution; or None for tradeoff>
- Effective conditions: <facts and limits>
- Reconsider when: <new evidence or event>
- Consequence: <allocation, exclusion, priority, risk, or authorization effect>
- Supersedes: <V identifier or None>
```

A `campaign-opening` V records an explicit current post-closeout reopen request. Bind it to the prior closeout, unchanged parent identities, proposed next generation, inherited Budget, and `planning only; zero B spend`. It records the answer already present in the request, needs no `AUTHORIZATION_READY`, and cannot present the Coordinator-derived technical objective as a user choice. A later user-owned route tradeoff uses a separate V. An `execution` V retains the exact immutable target and readiness rules. Its canonical ledger row is the reviewed authorize-branch record at `decision_record_path`; before the answer, that row may bind the stable target specification and assigned result path but not a future target or answer identity. The byte-derived user-result file binds the final target and exact answer. A finding-free adoption joins the ledger path, decision identifier, result identity, and target identity; together they are the one execution V.

## B: batch plan

```markdown
## B001: <batch name>

- Recorded at: <ISO-8601 datetime>
- Campaign generation: <positive integer>
- Recovery lineage: <prior closed B, candidate, V, X, review, and exact reuse consequence; or not applicable>
- Route: <T identifier or None>
- Campaign baseline: <chosen T identifier and role, plus incumbent E identifier when one exists, or not applicable>
- Work kind: <design | prototype | code | human_input | experiment | research | external_action | mixed>
- Changes executable candidate: <true | false>
- Executor: <Agent, user, tool, service, or team>
- Required inputs: <identifiers, paths, schemas, or None>
- Human input contract: <exact request, response path, schema, provenance, quality and legality checks, confidentiality handling, accept or reject conditions, and resume event; or not applicable>
- Human input meaning: <evidence only after workflow validation; never automatic technical conclusion, E, or user value choice; or not applicable>
- Work plan: <W identifier, path, plan revision, and design contract identity; or None>
- Design profile: <direct | module | system | not applicable>
- Required design inputs: <exact W and indexed concern sections with identities, or None>
- Design review: <adopted DESIGN_READY review bound to those inputs, pending for design work, or not applicable under direct profile>
- Development authorization: <external AUTHORIZATION_READY, V, Coordinator Entry adoption, and frozen adoption validation bound to the exact target; pending before readiness review; not applicable for non-code-bearing work>
- Parallel set: <label or None>
- Depends on: <identifiers or None>
- User values applied: <V identifiers or None>
- Epoch: <integer>
- Representation revision: <integer>
- Permitted scope: <exact reviewed scope>
- Starting records: <identifiers>
- Project provenance: <exact decision and authority roots governing this B>
- Work: <operations, modules, and worker assignments>
- Repository structure: <existing-integrated with evidence; user-approved-new with V; absent-awaiting-user; or not applicable>
- Source base identity: <commit plus dirty-state identity, immutable source snapshot, or not applicable>
- Workspace isolation: <branch and worktree for code-bearing work, shared sequential workspace with reason, or not applicable>
- Candidate interface: <existing or user-approved seam and callers, or not applicable>
- Allowed code paths: <exclusive paths assigned to this B or not applicable>
- Worker-forbidden paths: <paths this B's worker must not write, including evaluator, runner, interface, schema, Coordinator outputs, or other shared paths; or not applicable>
- Execution-frozen inputs: <path, identity, and exact scope that no actor may change after execution start; or not applicable>
- Packet preflight: <Coordinator-owned path, finding-free preflight identity, computed packet identity, validator identity, and created-before-authorization evidence>
- Result contract version: <versioned result schema and validation branch frozen in the B packet>
- Authorization readiness: <Entry schema identities, AUTHORIZATION_READY review identity, exact target, Coordinator adoption state, and adoption-validation identity>
- Candidate package inventory: <assigned official immutable path, byte-derived identity rule, and parent-owned charge event; or not applicable>
- Candidate manifest: <assigned stable path and identity rule, or not applicable>
- Engineering check plan: <exact selected units, argument vectors, content-addressed effect evidence, positive cumulative effect limits across all attempts, and engineering-only consequence; or not applicable>
- Publication policy: <frontier-authoritative-output-publication/1 with exact parent or default charge basis, authoritative output and evidence paths, and prohibited or deterministic-fidelity-only repair mode>
- Implementation review gate: <required before routine-local or first Slot H measurement, integration, or incumbent use; exact diagnostic-only exception under candidate-lifecycle.md; reusable prior review with exact unchanged identity; or not applicable>
- Evaluation target: <for formal Slot H, immutable candidate, review, experiment, and Slot H contract; for diagnostic-only, its exception evidence and consequence boundary; for routine-local, the derived candidate plus exact pre-authorized slot, protocol, calibration, structured evidence scope, and B-evidence-only boundary; or not applicable>
- Routine follow-up slot: <available slot identity and originating materialization B | consumed by exact execution root | invalid with reason | not applicable>
- Preparation role: <why this work is necessary to establish the baseline or reach a decision, or not applicable>
- Decision hypothesis: <mechanism or assumption this B tests or advances>
- Expected observation: <observable result and direction, including what would contradict the hypothesis>
- Trajectory contribution: <ordered comparison to named prior E under the T progress rule | first observation in the route | not applicable with reason>
- Output contract: <one independently verifiable slice or design artifact and its observable behavior>
- Implementation validation: <checks or exact WORK.md section>
- Implementation definition of done: <conditions or exact WORK.md section>
- Planned spend: <maximum amount and unit; publication charge event and amount are owned by Publication policy>
- Actual spend: pending
- Authorization gate: <AUTHORIZATION_READY followed by exact user V and Coordinator ENTRY_READY adoption; direct ENTRY_READY when no user authorization applies; adopted REPLAN_READY for a strategic later change; adopted implementation review before first Slot H measurement, integration, or incumbent use; exact diagnostic-only path under candidate-lifecycle.md; or exact later Selection authority>
- Baseline-establishment checkpoint: <usable artifact and completion check or not applicable>
- First performance check: <comparison or decision result, and whether this B or a later B runs it>
- Preparation budget limit: <maximum allocation before that check>
- Required follow-up reserve: <amount and mandatory confirmation or recovery purpose, or None with the governing rule>
- Decision after checkpoint: <deepen, revise, abandon, or select by observable evidence>
- Comparison-validity checks: <measurement identity, comparable conditions, data quality, drift, confounding, and execution checks required when this B measures a result>
- Measurement and promotion: <Slot H and R8 path>
- Artifacts: <assigned stable paths, including distinct attempt-evidence paths or one exclusive evidence subtree>
- Resume when: <available input, event, or immediate>
- Outcome: planned
```

A B authorizes one bounded objective, authority, evidence, and spend envelope rather than one command. Before authority or effects, deterministic draft repair stays in the same B while the target specification and every substantive, measurement, spend, effect, stop, and consequence field remain unchanged; failed draft bytes are diagnostic rather than a new B or review record. A later workflow-version migration may also stay in the same B and pending V only under the narrower preserved-history rule in Entry Review: no answer or effect, no semantic boundary change, new exclusive lifecycle paths, all current validators, and fresh independent review. During execution, its packet applies [Boundary-preserving continuation](batch-interface.md#boundary-preserving-continuation): the parent or R8 charge event decides whether the first identity named by that rule is already formal, or whether unchanged-specification fidelity repair may continue before one formal publication. Count all effects and resources cumulatively. Require a new B after a substantive boundary changes, authoritative publication, or an immutable result. Do not make the first eligible engineering failure terminal by default or add an unbounded retry path.

`Decision hypothesis` and `Expected observation` are the pre-spend owners of the B-level technical hypothesis. State the mechanism or assumption, predicted observable effect, contradiction, and decision it can resolve. A formal Slot H B that evaluates or confirms an unchanged candidate must state its immediate comparison hypothesis and cite the applicable originating T or W, design or implementation B, and exact candidate identity as mechanism lineage in the existing prose; reference measurements and candidates with no technical mechanism say `not applicable`. An upstream T or W provides only mechanism context explicitly inherited by B and cannot replace the B-level decision. After the terminal result, Outcome Reflection must recover both sources. The reflection cannot replace either source with a result-shaped story. Identity recovery, record repair, and administrative work use `not applicable` rather than inventing a technical mechanism.

When B is the bounded path for an unresolved prerequisite, its work, allowed paths, output contract, spend, and decision after checkpoint must stop at the prerequisite observation. Its `Depends on` and `Authorization gate` must make every dependent implementation or evaluation B ineligible until the Coordinator adopts evidence that the prerequisite passed through the applicable Entry or Replan gate.

Apply the canonical R8 vacuity definition before selecting B. Known-vacuous work is ineligible. An unknown measurement property may instead be the bounded first observation when its possible results lead to different permitted next actions. A diagnostic-only experiment follows `candidate-lifecycle.md`, remains B evidence, and cannot create E or any promotion, integration, incumbent, or strength consequence.

A routine-local B follows [Evaluation protocol reuse](evaluation-protocol.md). It consumes the one slot reviewed with its materialization B, never protected reserve, and ends at a terminal B outcome plus Outcome Reflection. It cannot create E or directly authorize another B.

## B terminal outcome

Append one block after Coordinator validation of a result with `completed`, `interrupted`, `failed`, or `blocked`. Do not rewrite the B plan. `waiting_for_input` is a paused attempt and has no terminal-outcome block until a resumed attempt terminates.

```markdown
B terminal outcome:
- Recorded at: <ISO-8601 datetime>
- Batch: <B identifier>
- Result: <result-packet path and immutable identity>
- Outcome: <completed | interrupted | failed | blocked>
- Coordinator validation: <accepted, partially accepted, or rejected, with exact scope and evidence>
- Output disposition: <available evidence, unavailable work, candidate materialized pending review, or other bounded meaning>
- Checks and deviations: <passed, failed, missing, and out-of-scope items with evidence>
- Spend: <actual amount and accounting evidence, or unknown and new-spend blocker>
- Reservation disposition: <released, partially consumed, retained with reason, or unresolved>
- Recovery: <stable recovery point and next permitted non-spend action>
- Applicable next gate: <implementation review | evaluation selection | Outcome Reflection | accounting resolution | other exact gate>
```

## E: evaluated result

```markdown
## E001: <evaluated option or set>

- Recorded at: <ISO-8601 datetime>
- Campaign generation: <positive integer>
- Batch: <B identifier, reference-baseline establishment packet, or existing result identifier>
- Candidate identity: <canonical Slot B identity>
- Experiment identity: <candidate, evaluator, data, controls, protocol, environment, budget, and result-artifact binding>
- Epoch: <integer>
- Representation revision: <integer>
- Measurement: <Slot H identity and evidence link>
- Comparison validity: <measurement identity, comparable conditions, data quality, drift or confound checks, adaptive-exposure lineage across attempts and B/E records, selection mechanism, shared evaluator/data/seeds, material omitted negative attempts, independent-confirmation status, and conclusion; or not yet applicable for an unpaired reference>
- Result: <complete parent-owned value or vector with required uncertainty, including every mandatory segment, tail, and delayed confirmation>
- Constraints: <every parent-owned hard constraint and guardrail with legal outcome and checks>
- Operating cost: <value or not applicable>
- Retained as: <reference baseline, incumbent, parent-defined set role, or not retained>
```

Append E only after Coordinator validation establishes valid Slot H measurement and comparison validity. An implementation B, engineering check, diagnostic-only experiment, invalid experiment, or worker result cannot create E. A recovery measurement uses a new E identifier and cites the generation that ran it; it never edits the reference E or creates a retroactive result for the closed generation. Retention and promotion remain separate R8 and Selection decisions.

E records one evaluated result, not a technical hypothesis, mechanism conclusion, trend, or route verdict. Outcome Reflection is the canonical owner of the hypothesis result, evidence-bounded mechanism inference, attribution limit, R&D implication, and any decision-relevant progress, constraint, or measurement interpretation. Combine E records only when their parent objective, measurement meaning, comparator role, protocol, workload, data scope, uncertainty, validity, and result directions remain comparable or have an explicit equivalence argument. Preserve excluded E with the reason. An improved proxy or aggregate does not establish route progress while any parent-owned metric, hard constraint, guardrail, required segment, tail condition, delayed confirmation, or operating-cost boundary fails or remains unresolved.

## Q: research finding

```markdown
## Q001: <research finding or assumption>

- Recorded at: <ISO-8601 datetime>
- Research mode: <route landscape | focused question>
- Target question: <bounded question>
- Coverage: <repository, prior results, public implementation, benchmark, domain, and academic channels used or marked not applicable>
- Search stop: <why more searching is unlikely to change eligibility, recommendation, allocation, stopping, or claim limits>
- Finding or assumption: <answer or exact Unknown>
- Alternatives found: <materially different approaches or None>
- Recommendation: <evidence-backed recommendation and reason or None>
- Source identity: <sources and stable evidence links>
- Applicability: <routes, batches, instances, scales, or claims>
- Limits: <uncertainty and exclusions>
- Decision-changing test: <observable test or None>
- Later-use links: <identifiers or None>
```
