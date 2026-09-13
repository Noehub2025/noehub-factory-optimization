# Frontier Planning Records

Load only when reading or writing T, V, B, E, or Q. This file is their sole template source. Use one monotonic namespace per prefix and never change assigned meaning.

## Contents

- [T: route](#t-route)
- [V: user decision](#v-user-decision)
- [B: Batch selection record](#b-batch-selection-record)
- [B conclusion](#b-conclusion)
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
- First performance check: <comparison and permitted feedback when this route needs one; otherwise the relevant theoretical or technical result>
- Replacement boundary: <exact mechanism boundary beyond which a new T and strategic Replan are required; parts that may improve or be replaced; stable measurement or evidence interfaces>
- Disqualifying evidence: <competing explanation, transfer mismatch, failed prerequisite, or other observable result that falsifies the causal path or makes the route ineligible or not worth continuing>
- Continue when: <observable result>
- Stop or combine when: <condition and affected routes>
- Status: <proposed | active>
```

The T fields must preserve one evidence-bounded chain: observation or constraint -> mechanism -> permitted change -> causal path -> competing explanation or transfer mismatch -> disconfirming observation -> earliest affordable discriminating check. A transferred or recombined route must map the source function and expected behavior to the target constraint and name where the transfer fails. Surface resemblance is insufficient.

When a route substantively completes, is retired or replaced, retain its learning through [Research Reflection](learning-loop.md#research-reflection). Combine related W/B experience and continue clear next work; a status update or individual B result is not a Reflection trigger.

### Research hypotheses and action prerequisites

Judge eligibility for the action being proposed, not for the route's eventual success. An unestablished hypothesis is the subject of its test, not a prerequisite that must pass before that test. The test itself needs an executable method, interpretable outcomes, and satisfied resource, safety, access, and authority conditions. A valid negative result or a bounded inconclusive observation can complete the assigned research question at its supported scope; it does not complete a promised final deliverable. Ordinary implementation, theoretical derivation and experiment preparation can contribute jointly to a research commitment without each producing a performance result, distinct next-action branches or a new investment decision. Continuing the selected work can be the appropriate consequence of a useful result.

Identify the prerequisites the proposed action actually depends on and reuse sufficient current evidence. Obtain a missing fact through appropriate authorized work; continue other work that does not depend on it. A failed prerequisite limits its dependent use until the needed condition is established. When evidence satisfies an already selected condition, continue directly; use Entry or Replan only when the resulting decision itself requires it. This is dependency handling, not a requirement to enumerate every possible failure before development.

Use [current Batch actions](batch-current.md#perform-an-action) for authorized empirical tests without a complete W or published candidate. Research Permission does not make the eventual route delivery-ready or waive parent-owned charges. Keep an existing full-delivery commitment intact unless its owner changes it through the existing revision path.

### Informative checkpoints

Arrange checks at the scale of the current research commitment, including the conditions, scale, duration, setup, interpretation and recovery needed for a useful result. Prefer lower cost among observations that can answer the question; theoretical work, coupled implementation or a larger experiment may be the most informative affordable choice. Necessary internal steps do not each need a separate performance check or proof of value. An early or reduced-scale result may eliminate a route only when it can distinguish the mechanism under test. Otherwise bound the conclusion and compare the next informative observation under the existing resource and stop limits; a new observation window is a prospective allocation, not a retrospective extension of a triggered stop.

Preserve a useful non-winner's distinct capability, mechanism evidence, or plausible transfer in existing evidence. Retention creates no ongoing funding, maintenance, review, or retest obligation. Adjust measurement only when its limitation can change the pending selection or claim.

## V: user decision

```markdown
## V001: <value or authorization choice>

- Recorded at: <ISO-8601 datetime>
- Campaign generation: <positive integer>
- Decision kind: <tradeoff | authorization>
- Permission class: <campaign-opening | protected Consequence | not applicable for tradeoff>
- Decision: <exact user-owned choice>
- Evidence presented: <record handles or stable links>
- Alternatives: <technically eligible options for tradeoff; authorize, decline, and conditional authorization for execution; current explicit request for campaign-opening>
- Recommendation presented: <recommended option and evidence-bounded reason or None>
- Applies to: <routes, B records, actions, resources, or campaign choice>
- Permitted Consequences: <paid work beyond the existing cost boundary, external submission, sensitive access, irreversible change, user-controlled scarce consumption, or None>
- Scope and resources: <allowed objective, resources, data, systems, cumulative limits, and important restrictions>
- Effective conditions: <facts, start or end condition, withdrawal state, and stop boundary>
- Reconsider when: <new evidence or event>
- Consequence: <allocation, exclusion, priority, risk, or authorization effect>
- Supersedes: <V identifier or None>
```

A `campaign-opening` V records an explicit current post-closeout reopen request and inherited user boundaries. A later user-owned tradeoff uses a separate V. A protected-Consequence V states the exact user choice, affected scope, controlled resources or costs, permitted Consequences, cumulative limits, conditions and stop boundary. Internal campaign spend within the adopted total and workflow-owned single-use consumption do not require another V. It is a human decision record, not an execution token or cryptographic credential. The Batch cites the applicable V immediately before `Batch.perform`; do not create target, adoption, authority or result identities around it.

## B: Batch selection record

Create one short selection record, then create or open its authoritative state through `Batch.open(B)`:

```markdown
## B001: <batch name>

- Recorded at: <ISO-8601 datetime>
- Campaign generation: <positive integer>
- Route: <T identifier or None>
- Selection role: <Primary | Parallel with join owner | later independent work>
- Batch state: artifacts/frontier/B001/batch.yaml
- Independently judged result: <the result that makes this one B>
- Why this is a new B: <independently evaluable, stoppable, or fundable boundary>
- Depends on: <records or observations that must exist before an affected action, or None>
```

The `frontier-batch/1` record owns objective, acceptance, scope, R and V references, resource limits, expected Consequences, Candidate Revision, Measurement Definition, checks, observations, Attempts, actual consumption, Consequences, conclusion, and recovery. Do not duplicate those facts in this planning record, `FRONTIER.md`, a packet, or a terminal-outcome block.

A B is one stable allocation toward one independently judged result rather than one command, slice, candidate, dispatch, or internal try. Draft repair, implementation changes, Review or Permission updates, resource-limit revisions and Candidate Revision changes stay in the same B while that result remains the same. Create a new B only for work that can be evaluated, stopped, or funded independently. Apply [Boundary-preserving continuation](batch-current.md#boundary-preserving-continuation).

State the technical hypothesis, expected observation, contradiction, and decision inside the Batch objective, acceptance, Measurement Definition, or action details as appropriate. An upstream T or W supplies only explicitly inherited mechanism context. Raw observations do not become E and a Batch conclusion does not select the next investment.

## B conclusion

Conclude through `Batch.apply(ConcludeBatch(...))`. The Batch record preserves the strongest supported result and remaining objective gap after every Attempt is resolved. Reconcile actual spend with Budget and adopt valid measurement meaning through E. Do not append another result identity, validation identity, or duplicate terminal outcome.

## E: evaluated result

```markdown
## E001: <evaluated option or set>

- Recorded at: <ISO-8601 datetime>
- Campaign generation: <positive integer>
- Batch: <B identifier, reference-baseline establishment packet, or existing result identifier>
- Candidate Revision: <full Git commit and selected repository-relative paths, or retained external candidate reference>
- Measurement source: <B identifier, Attempt, Batch-owned Measurement Definition, raw evidence, evaluator or protocol reference when independently reused>
- Epoch: <integer>
- Representation revision: <integer>
- Measurement: <formal-slot-h definition and evidence link>
- Comparison validity: <measurement identity, comparable conditions, data quality, drift or confound checks, adaptive-exposure lineage across attempts and B/E records, selection mechanism, shared evaluator/data/seeds, material omitted negative attempts, independent-confirmation status, and conclusion; or not yet applicable for an unpaired reference>
- Result: <complete parent-owned value or vector with required uncertainty, including every mandatory segment, tail, and delayed confirmation>
- Constraints: <every parent-owned hard constraint and guardrail with legal outcome and checks>
- Operating cost: <value or not applicable>
- Retained as: <reference baseline, incumbent, parent-defined set role, or not retained>
```

Append E only after Coordinator validation establishes valid Slot H measurement and comparison validity. An implementation B, engineering check, diagnostic-only experiment, invalid experiment, or worker result cannot create E. A recovery measurement uses a new E identifier and cites the generation that ran it; it never edits the reference E or creates a retroactive result for the closed generation. Retention and promotion remain separate R8 and Selection decisions.

E records one evaluated result, not a technical hypothesis, mechanism conclusion, trend, or route verdict. The active resolver applies E together with its B hypothesis, lineage, validity, parent objective, R8, and current constraints; research Reflection develops explanations and next ideas from relevant experience without turning its hypotheses into measured effects. Combine E records only when their parent objective, measurement meaning, comparator role, protocol, workload, data scope, uncertainty, validity, and result directions remain comparable or have an explicit equivalence argument. Preserve excluded E with the reason. An improved proxy or aggregate does not establish route progress while any parent-owned metric, hard constraint, guardrail, required segment, tail condition, delayed confirmation, or operating-cost boundary fails or remains unresolved.

## Q: research finding

Use [Route-landscape synthesis](../../research-frontier/SKILL.md#route-landscape-synthesis) when forming or comparing technical directions; a focused question needs only its factual answer and relevant limits. These fields preserve the result, not a required sequence of reasoning or proof that the research is sufficient. A recommendation remains advisory for [Route-investment ordering](learning-loop.md#route-investment-ordering).

```markdown
## Q001: <research finding or assumption>

- Recorded at: <ISO-8601 datetime>
- Research mode: <route landscape | focused question>
- Target question: <bounded question>
- Coverage: <sources and retained evidence used, with material applicability limits; no source-category checklist>
- Search stop: <why reasoning or practical work is now more useful than further retrieval, or the actual research bound reached; retain usable findings and uncertainty>
- Finding or assumption: <answer or exact Unknown>
- Alternatives found: <materially different approaches or None>
- Recommendation: <professional recommendation, decisive reason and uncertainty; distinguish evidence from theoretical assumptions; or None>
- Source identity: <sources and stable evidence links>
- Applicability: <routes, batches, instances, scales, or claims>
- Limits: <uncertainty and exclusions>
- Decision-changing test: <observable test or None>
- Later-use links: <identifiers or None>
```
