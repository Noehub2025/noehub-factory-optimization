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
- Produced by: <Q, E, D, failure evidence, or explicit reasoning>
- Starting records: <identifiers>
- Reviewed scope: <forms, operations, or modules>
- Improvement mechanism: <how later work can affect the parent objective or constraints>
- Why it can carry optimization: <usable optimization surfaces, feedback path, and known headroom or limits>
- Tradeoffs: <implementation burden, reversibility, maintenance, dependencies, and user-owned consequences>
- Assumptions: <Q identifiers or None>
- Depends on: <identifiers or None>
- Maximum allocation: <amount and unit>
- Next checkpoint: <bounded output or test>
- First performance check: <comparison or decision result and parent-approved feedback>
- Replacement boundary: <parts that may improve or be replaced, and measurement or evidence interfaces that remain stable>
- Disqualifying evidence: <observable result that makes this route ineligible or not worth continuing>
- Continue when: <observable result>
- Stop or combine when: <condition and affected routes>
- Status: <proposed | active>
```

## V: user decision

```markdown
## V001: <value or authorization choice>

- Recorded at: <ISO-8601 datetime>
- Campaign generation: <positive integer>
- Decision kind: <tradeoff | authorization>
- Decision: <exact user-owned choice>
- Evidence presented: <identifiers or stable links>
- Alternatives: <technically eligible options for tradeoff; authorize, decline, and conditional authorization for authorization>
- Recommendation presented: <recommended option and evidence-bounded reason or None>
- Applies to: <routes, batches, resources, or campaign choice>
- Bound object: <exact authorization target and AUTHORIZATION_READY identity; reviewed design contract and scope; immutable direct packet, preflight, and source; layout; resource; or None for a general tradeoff>
- Effective conditions: <facts and limits>
- Reconsider when: <new evidence or event>
- Consequence: <allocation, exclusion, priority, risk, or authorization effect>
- Supersedes: <V identifier or None>
```

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
- Work: <operations, modules, and worker assignments>
- Repository structure: <existing-integrated with evidence; user-approved-new with V; absent-awaiting-user; or not applicable>
- Source base identity: <commit plus dirty-state identity, immutable source snapshot, or not applicable>
- Workspace isolation: <branch and worktree for code-bearing work, shared sequential workspace with reason, or not applicable>
- Candidate interface: <existing or user-approved seam and callers, or not applicable>
- Allowed code paths: <exclusive paths assigned to this B or not applicable>
- Worker-forbidden paths: <paths this B's worker must not write, including evaluator, runner, interface, schema, Coordinator outputs, or other shared paths; or not applicable>
- Execution-frozen inputs: <path, identity, and exact scope that no actor may change after execution start; or not applicable>
- Packet preflight: <Coordinator-owned path, finding-free preflight identity, computed packet identity, validator identity, and created-before-authorization evidence>
- Authorization readiness: <Entry schema identities, AUTHORIZATION_READY review identity, exact target, Coordinator adoption state, and adoption-validation identity>
- Candidate manifest: <assigned stable path and identity rule, or not applicable>
- Implementation review gate: <required before first performance measurement, integration, or incumbent use; reusable prior review with exact unchanged identity; or not applicable>
- Evaluation target: <immutable candidate identity, manifest, adopted IMPLEMENTATION_READY, planned experiment identity, and Slot H contract for a separate evaluation B; or not applicable>
- Preparation role: <why this work is necessary to establish the baseline or reach a decision, or not applicable>
- Decision hypothesis: <mechanism or assumption this B tests or advances>
- Expected observation: <observable result and direction, including what would contradict the hypothesis>
- Output contract: <one independently verifiable slice or design artifact and its observable behavior>
- Implementation validation: <checks or exact WORK.md section>
- Implementation definition of done: <conditions or exact WORK.md section>
- Planned spend: <amount and unit>
- Actual spend: pending
- Authorization gate: <AUTHORIZATION_READY followed by exact user V and Coordinator ENTRY_READY adoption; direct ENTRY_READY when no user authorization applies; adopted REPLAN_READY for a strategic later change; adopted implementation review before first measurement, integration, or incumbent use; or exact later Selection authority>
- Baseline-establishment checkpoint: <usable artifact and completion check or not applicable>
- First performance check: <comparison or decision result, and whether this B or a later B runs it>
- Preparation budget limit: <maximum allocation before that check>
- Required follow-up reserve: <amount and mandatory confirmation or recovery purpose, or None with the governing rule>
- Decision after checkpoint: <deepen, revise, abandon, or select by observable evidence>
- Comparison-validity checks: <measurement identity, comparable conditions, data quality, drift, confounding, and execution checks required when this B measures a result>
- Measurement and promotion: <Slot H and R8 path>
- Artifacts: <assigned stable paths>
- Resume when: <available input, event, or immediate>
- Outcome: planned
```

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
- Comparison validity: <measurement identity, comparable conditions, data quality, drift or confound checks, and conclusion; or not yet applicable for an unpaired reference>
- Result: <value or vector with required uncertainty>
- Constraints: <legal outcome and checks>
- Operating cost: <value or not applicable>
- Retained as: <reference baseline, incumbent, parent-defined set role, or not retained>
```

Append E only after Coordinator validation establishes valid Slot H measurement and comparison validity. An implementation B, engineering check, invalid experiment, or worker result cannot create E. A recovery measurement uses a new E identifier and cites the generation that ran it; it never edits the reference E or creates a retroactive result for the closed generation. Retention and promotion remain separate R8 and Selection decisions.

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
