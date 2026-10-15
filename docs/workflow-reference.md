# Workflow reference

This reference explains the roles, project files, and detailed behavior behind
the [quick start](../README.md#get-started). The individual Skill files remain
the authority for their procedures and record formats.

Start with [Skills](#skills) or [Project files](#project-files). For a specific
question, use the topic links below:

- [Responsibilities and design](#responsibilities-and-design)
- [Choosing and reconsidering research](#choosing-and-reconsidering-research)
- [Assignments, context, and corrections](#assignments-context-and-corrections)
- [Implementation and measurement](#implementation-and-measurement)
- [Review, permission, and resources](#review-permission-and-resources)
- [Learning and changes to the task](#learning-and-changes-to-the-task)
- [Recovery and compatibility](#recovery-and-compatibility)

## Skills

Install all thirteen Skills as one workflow. Normally, users invoke only the two coordinators; the coordinators assign the narrower worker Skills.

Each Skill entry point routes the agent to the references needed for its current stage or action. Detailed packet formats and historical compatibility rules stay in separate files and are read only when relevant. Install the complete folders so this selective reading does not omit required workflow rules.

### Define the task and search

- **[frame-optimization](../skills/frame-optimization/SKILL.md)** — Coordinates the problem definition, search representation, repair loops, reviews, and final handoff.
- **[design-measurement](../skills/design-measurement/SKILL.md)** — Designs or repairs reusable measurement meaning in a fresh context, including lifecycle, source coverage, target relationship, and evidence ceilings, without adopting it or choosing campaign actions.
- **[research-optimization](../skills/research-optimization/SKILL.md)** — Investigates one assigned question without changing the task contract.
- **[grill-optimization](../skills/grill-optimization/SKILL.md)** — Collects one decision that only the user can make.
- **[review-optimization](../skills/review-optimization/SKILL.md)** — Independently checks problem readiness, measurement-design readiness in proportion to its intended consequence, fixed measurement-support implementations, or retained-result comparability.
- **[review-representation](../skills/review-representation/SKILL.md)** — Independently checks the proposed search space and the exact scope that later work may use.

### Run the improvement campaign

- **[frontier-optimization](../skills/frontier-optimization/SKILL.md)** — Coordinates campaign entry, planning, budget, batch selection, accepted results, closeout, and recovery.
- **[design-implementation](../skills/design-implementation/SKILL.md)** — Resolves an important implementation-design question in a fresh context when existing agreements do not settle it, without taking over campaign routing, Review, Permission, or execution.
- **[research-frontier](../skills/research-frontier/SKILL.md)** — Answers one focused question or synthesizes technical directions through source-grounded, multidisciplinary research without treating the assigned options as a closed menu.
- **[grill-frontier](../skills/grill-frontier/SKILL.md)** — Collects one unresolved user tradeoff or Permission decision after existing V records and technical evidence have been exhausted.
- **[run-frontier-batch](../skills/run-frontier-batch/SKILL.md)** — Advances assigned Batch work from implementation and research through debugging, integration, and observation, using a recoverable working plan when the work spans contexts.
- **[review-frontier](../skills/review-frontier/SKILL.md)** — Independently reviews one exact Git-backed Entry, replan, design, implementation revision, or proposed claim when a remaining consequential question requires review.
- **[reflect-frontier](../skills/reflect-frontier/SKILL.md)** — Turns substantive route experience or cross-route learning into technical insight and promising ideas without choosing or authorizing work.

Internally, the first stage uses A–H and R1–R8 as completeness checklists. Users do not need to learn those labels before starting; the main documents must explain their meaning in ordinary task language.

## Project files

The agent keeps each task under `docs/skills/optimization/<task-name>/`.
Framing produces `PROBLEM.md` and `REPRESENTATION.md`; the campaign adds
`FRONTIER.md` and supporting records under `frontier/`.

`PROBLEM.md` answers:

- What are we improving, and why?
- What may be changed?
- What rules must every candidate obey?
- How is a result measured and compared?
- What resources and information are allowed?
- What evidence would count as success?

`REPRESENTATION.md` answers:

- What does the optimizer propose?
- How does a proposal become something the evaluator can run?
- Which parts of the allowed solution space are actually searchable?
- What changes can one search step make?
- Is the candidate searched as a whole or in separately owned modules?
- How are feedback, selection, stopping, and saved search state handled?

`FRONTIER.md` is the readable campaign overview. It states the approved scope, current comparison reference, working approach, remaining budget, next batch, first performance check, stopping conditions, and claim limits. Supporting records preserve research, user decisions, plans, implementations, measurements, reviews, spending, and lessons learned.

The main documents are designed to be usable on their own. Linked detail files hold evidence, commands, full parameter lists, and fixed implementation details; they must not hide a decision that would change ordinary development or evaluation.

## Detailed behavior

Each section below groups related rules from the workflow. These are explanations
of the existing Skills, not additional stages or approval requirements.

### Responsibilities and design

- One coordinator owns the task definition and search design; another owns the later campaign. Worker Skills cannot silently change either contract.

- A fresh-context measurement designer can create or repair the complete decision-relevant protocol. It reconstructs how values are initialized, updated, aggregated, and related to the real objective; unsupported proxy relationships remain explicit. It separates execution, the intended change, the observed outcome, and its explanation when that distinction affects the decision, then asks only for evidence justified by the next use and the cost of being wrong. The framing coordinator must adopt that projection as a whole before it becomes part of the task contract.

- A fresh-context implementation designer resolves an important technical question only when existing agreements do not already settle the consequential behavior, ownership, interface, architecture, or migration choice. The designer grounds the answer in expected objective value or learning value; a shared design map and independent design Review are used only when the question and next consequence require them.

- Frontier-seeking design can start from an explicitly untested conjecture grounded in experience, analogy, intuition, retained results, automated search, or mechanism reasoning. It must state the intended change and the objective-relevant observation that would inform further investment, but it does not need a proven bottleneck, complete causal account, or predicted advantage before development. Local refinements remain useful, yet their simplicity or small positive results cannot indefinitely defer comparison with a credible core-mechanism alternative.

- The repository's current language, runtime, toolchain, or implementation shape does not restrict the legal solution space unless the task, a verified environment, a hard physical or theoretical boundary, safety, law, or an adopted user decision requires that restriction.

- A decision-bearing threshold has one current normative owner. Copied constants, warnings, operational limits, exploratory scenarios, heuristic margins, and convenient engineering targets cannot silently become broader rejection, route, or stopping rules. A changed workload, statistic, scope, direction, or consequence returns only the affected decision to that owner.

- Foreseeable shared capabilities such as evaluation, packaging, submission, storage, and recovery are planned before dependent work makes reuse fragile. A project records the supported entry, scope, defaults, owner, checks, known gaps, and justified deferrals without requiring a central registry or a second consumer first.

### Choosing and reconsidering research

- One ordered direction resolver is used only when choosing the next research problem or when evidence, cost, opportunity, time, resources, or scope may justify changing the current investment. Ordinary implementation, repair, integration, measurement, and technical diagnosis remain with their existing owners.

- A persisted direction resolution governs only the investment it actually selected. The coordinator may reconsider that investment before a Batch ends when repeated support work is not approaching the needed observation, an assumption fails, dependencies materially expand, or a credible higher-value opportunity appears.

- Historical technical rankings remain evidence within their original scope. They do not become strategic boundaries merely because an earlier design, plan, or resolution recorded them; only a change to an actual governing commitment, allocation, stop rule, irreversible behavior, or claim limit requires strategic replanning.

- An unresolved investment choice triggers one independent, fresh-context comparison inside that resolver. The coordinator checks the factual basis and applicable limits, preserves the professional ordering, and adopts the result. Before adoption, a concrete source omission, contract misreading, or unequal comparison returns to the original resolver for correction in the same task; finalized results remain historical unless the decision inputs genuinely change.

- Route comparison considers the minimum sufficient commitment, its full cost and opportunity cost, and what its outcome can change. An inexpensive but underpowered probe is not automatically preferable, and sunk cost does not favor the incumbent route.

- A focused research question is investigated directly. A route-landscape assignment can investigate a bounded mechanism or coverage gap before a replacement route is known; distinct independent questions may use temporary specialists, but one parent returns one normalized result for adoption. Research stops when further retrieval is unlikely to change the current allocation and records when its conclusions should be reconsidered.

- At consequential investment, design, and research choices, the existing owner considers material external changes and intervention-induced effects, including important interactions, delays, and opportunities for a different whole mechanism. This reasoning stays bounded to the decision at hand; it does not add a forecasting stage, scenario quota, universal robustness objective, or invented probabilities.

- Research can transfer a mechanism or conditional result to another worthwhile question, and the representation can retain recoverable alternatives that still affect a whole-result choice. Selection changes the actual receiving assignment and preserves conditions, evidence, costs, and unresolved limits; a copied note or local ranking alone establishes neither transfer nor superiority.

- A poor result is interpreted at the scope actually tested. When evidence identifies a concrete mismatch between the proposed capability and its operator, evaluator, or supporting arrangement, the owner compares bounded capability acquisition and remeasurement with a more direct observation, another method, or stopping. Novelty or disappointment alone does not justify support work.

- Negative implementation evidence applies first to the exact realization and operating conditions observed. It reaches a shared design or route only when the evidence establishes a limiting cause of the same scope; failure to find another implementation is not proof that none exists.

- A closed candidate or route does not end a continuing task. The coordinator re-evaluates worthwhile direct actions and grounded research questions, or records a campaign-wide stop and closes the campaign when neither remains. An empty old route list or an unmet objective alone does not force research or justify waiting for the user to supply a technical target.

- If valid execution, measurement, and local-mechanism explanations are exhausted, the workflow can return an exact semantic challenge to the parent task contract instead of repeating in-scope work that can no longer reach the objective.

### Assignments, context, and corrections

- A working assignment supplies the current research problem, enough context and ownership to begin useful work, and source references as starting points rather than a read whitelist. Open direction research may combine different professional perspectives around the same problem instead of dividing a preset route menu; workers report concrete assumption failures, expanding dependencies, and promising alternatives that may change investment.

- Before consequential adoption or cold recovery, the coordinator reads the controlling objective, incoming restrictions, actual reasons and switching conditions, and intended outgoing work together. A local assignment or historical restriction cannot silently replace the broader objective, while a legitimate focused task remains focused.

- Reusable understanding is retained as one current explanation with its incorporated returns. Exact source and return bytes can be stored once and retrieved by content identity, so a cold receiver gets complete current context without copying the full history into every handoff. Delivery identity proves the bytes supplied, not their truth or authority.

- The coordinator orders early research, prerequisites, implementation, feedback, and long-task recovery around the current research commitment and the missing observation. An ordinary step may be necessary without independently improving the metric or changing direction. Internal process, audit, authorization, or identity machinery that blocks feasible authorized work is a workflow defect: the responsible owner corrects it and work resumes, while real limits and effects already incurred remain binding.

- A known correction must change the affected current task, dependency, dispatch, or return before that work continues. Stable identifiers, status labels, updated records, or disclaimers do not establish current use by themselves. The owner retains the finding, saves the corrected objects, and checks the actual next action; unrelated work remains available.

- A reused consequential judgment stays bound to the objective, evidence, selected consequence, and actual task it covered. Ordinary progress can retain that judgment, but a changed assignment, terminal disposition, or route-ending restriction returns to the existing owner instead of borrowing an old reference or unchanged label.

- The research chain carries its advantage hypothesis and selected target feedback across Batches, versions, and owners. Once the necessary state exists, the coordinator obtains that feedback by default; repeated delay must resolve into feedback, necessary repair, real waiting, or a changed allocation before dependent optional work continues. This uses the existing plan and decision owner rather than adding another ledger, gate, or Review.

- Delayed or changing observations retain an owner, delivery path, due condition, accumulated exposure, and intended decision use across worker returns and context changes. A scheduled or promised read is not a completed observation; failed delivery preserves uncertainty, and unrelated useful work may continue without duplicating an unsettled effect.

- Long repair chains retain a named reassessment point and the next meaningful observation across worker, owner, and Batch changes. Before expanding discretionary repair, the coordinator checks whether cumulative findings and remaining work still support the investment; same-B continuity and sunk effort do not answer that question.

### Implementation and measurement

- One Batch is a stable allocation toward one independently judged result, not an immutable packet, command, proposal hash, or candidate identity. Its implementation, checks, Reviews, Permissions, limits, paths, and Candidate Revisions may evolve while that result remains the same.

- The current Batch interface is deliberately small: `Batch.open` defines the work, `Batch.apply` records routine progress, adopts a chosen saved Review, or updates same-result working state, and `Batch.perform` starts an action whose measurement or real-world Consequences make repetition matter. The maintained facts view reports only Batch-owned state; it does not reconstruct campaign accounting or professional conclusions.

- `run-frontier-batch` owns work from the first implementation change through debugging, integration, and observation. Preparation, editing, harmless checks, and repair stay inside the open Batch without acknowledgment, execution-start, snapshot, packet, or result identities. A failed check does not create another Batch or Attempt, and an internal worker return is not a terminal result.

- Complex or cross-context implementation uses a lightweight working plan in ordinary working material. It preserves the current step, prerequisites, progress, feedback, observations, and remaining work without creating another lifecycle, approval gate, or commit requirement.

- Each Batch owns one Measurement Definition. It records the question, comparator, scope, resource ceiling, lifecycle state, required context, evidence limits, result owner, and why the planned observation is sufficient for its intended decision. Measurement mode controls evidence use, not repeatability, Review, Permission, or resource ownership. Single-use fields are present only when the Action or adapter can consume a real single-use unit.

- Attempts exist only when a measurement or possible Consequence makes repetition important. An unresolved Attempt blocks another consequential performance in the same Batch, while routine work and other Batches continue. For genuine single-use work, the actual unit remains protected across Action-key changes until the Attempt is reconciled.

- Operation bindings protect the real seam involved—such as a paid call, external submission, sensitive access, irreversible change, remote job, or single-use sample—without activating unrelated controls.

- A technical or fidelity finding returns to its existing owner and remains in the same Batch when the independently judged result is unchanged. Repair follows the affected producer-to-consumer path and reruns only relevant checks. An inherited internal restriction that no longer protects a real boundary is corrected through the same Batch rather than promoted into a strategic replan or user decision. Only dependent work pauses; unaffected legal work continues.

- Result adoption separates validity from applicability. Delayed, partial, or support-failed observations retain the raw facts they actually establish without turning missing values into zero or complete comparisons. Objective-relevant costs, adverse observations, and unanswered design questions remain visible when they challenge a still-used advantage or learning premise. When measurement meaning and interpretation limits are unchanged, corrected processing of recoverable raw evidence does not create another measurement attempt, including after an operation starts or fails. A correctly produced initialization value, intermediate state, or unknown proxy may be valid evidence while remaining ineligible for stronger performance or investment conclusions. Repeatable public development evidence may guide hypotheses, screening, provisional ranking, and the next candidate inside its adopted ceiling when adaptive exposure is recorded; an exact repeat that cannot change the pending decision is dominated. Only a valid formal comparison may create adopted Evidence or support stronger claims.

- Results identify the problem and representation versions under which they were produced, so incompatible results are not compared.

### Review, permission, and resources

- Independent review is selected by the consequence of error, not by a fixed stage sequence. A reviewer checks the exact Git-backed subject and may use separately versioned supporting evidence; an existing review contributes its checked conclusions without becoming an implicit gate for every later action.

- Git owns retained project bytes. A Candidate Revision is one full commit plus explicit repository-relative paths, so a Review, check, or action can name exact bytes without copying the repository into workflow snapshots. Design documents keep stable paths, section anchors, and slice keys; their consuming Review, Batch, or assignment owns the saved Git reference, avoiding self-referential document hashes.

- R records own independent Review meaning. A governance resolver reads the saved R and checks whether its conclusions cover the proposed action; only Reviews needed for the current action appear in its required list, while other retained R records remain reusable evidence. V records own user tradeoffs and Permission for uncovered paid, external, sensitive, irreversible, or user-controlled scarce-resource work. Review readiness does not create Permission, and Permission does not prove execution or improvement.

- The agent reuses an applicable V instead of asking again. Ordinary technical choices, local implementation changes, Batch identities, and internal resource allocation do not become user questions. When a valuable action crosses an uncovered user boundary, the resolver may select one exact permission question with its purpose, scope, cost, and expected decision-changing observation; the action remains unavailable until the user grants it.

- Budget owns governing campaign-wide capacity, reservations, actual and unknown governed consumption, and remaining balance. Batch operational limits are separate: the coordinator may revise them within the same independently judged result and existing boundaries, but cannot turn protected reserve into routine capacity or expand the campaign ceiling.

- Budget, stopping rules, known limits, and permitted claims remain visible in the main campaign document.

- Independent reviews use one saved Git commit with explicit subject paths and an agent that has not seen the drafting conversation, but only when the next actual consequence requires that assurance. Supporting parents and evidence keep their own saved versions instead of being copied into the subject. Review methods are not sequential approval stages, and ordinary result validation does not require a separate claims review.

- Reviews answer the remaining consequential question in their assigned branch and reuse applicable earlier conclusions. A professional recommendation informs the coordinator, but does not by itself change route choice, reopen work, or create a new proof, approval, or review obligation.

- Entry repair reviews inspect the corrected saved version, its changes, and affected conclusions. They reuse earlier conclusions only where their assumptions still apply; a reviewer’s suggested repair does not become an extra acceptance requirement.

### Learning and changes to the task

- After each result is adopted, the coordinator establishes its supported meaning, reconciles effects and resources, and recovers the current research question, the observation it still needs, and what the new facts changed. It then continues, repairs, follows an existing branch, or reconsiders the investment. A terminal Batch, a passed prerequisite, or a new follow-on Batch does not by itself trigger another direction resolution.

- `reflect-frontier` can turn the experience of a completed, retired, or replaced route—or a substantial learning checkpoint—into technical insight and promising next ideas while the campaign is still active. Reflection informs professional judgment but does not select work, allocate budget, grant authority, or block otherwise-ready work.

- When an adopted change in shared problem understanding, representation, evaluation meaning, or research premises makes the current agenda unsuitable, the coordinator can advance the research generation without forcing full closeout. Applicable work, evidence, permissions, reservations, and accounting remain intact; only work whose real dependency changed pauses.

- Frame documents and handoffs own durable task, comparison, resource, feedback, stop, claim, and reuse rules. Live generation, Selection, Permission, spending, adopted-result, and recovery state stays in `FRONTIER.md`, `frontier/ledger.md`, and the latest complete closeout, so a stale explanatory value in an older handoff does not by itself invalidate the task contract.

- Parent revisions affect only decisions that depend on the changed meaning. Unaffected work and historical conclusions remain usable; a new revision number alone does not force campaign closeout or a new generation. A generation advances only when a material shared-premise change makes the existing research agenda unsuitable or incomplete.

- Project evidence and workflow releases remain separate. Updating an installed Skill does not rewrite or invalidate an existing project decision, Review, Permission, result, or handoff.

### Recovery and compatibility

- Campaign state is recovered from retained Git versions, records, and required artifact payloads, not from conversation history. Normal edits do not invalidate reviews of saved bytes, and restoring working files does not undo spending, evidence, or external effects.

- Reusing retained material preserves its original producing versions, reviews, and charges. Candidate recovery checks the content and latest accounting needed for the proposed use; it does not grant readiness or permission. Existing conclusions need further review only when a relevant change, a new use, or concrete contrary evidence affects them. Missing content pauses its dependent use, not all recovery planning.

- A project handoff cites the existing closing record, Git history, and retained artifacts. An explicit export writes a small reference file, not another complete project archive. The receiving environment must have the referenced history and any payloads needed for its next action.

- Current automation reads saved Git inputs through one literal-path helper and exposes named Batch facts to ordinary callers. Release checks use the maintained source-module inventory to select current tests and the compatibility tests affected by a change, while unclassified source changes escalate to the full release suite.

- Historical packet, snapshot, acknowledgment, execution-start, result-identity, and typed-provenance formats remain readable through isolated compatibility checks. New work uses the current Batch record and does not backfill or regenerate those identities.
