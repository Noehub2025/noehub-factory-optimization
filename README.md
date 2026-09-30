# Noehub Factory Optimization

Noehub Factory Optimization is a task-agnostic Recursive Self-Improvement (RSI) workflow for automated optimization research. It gives coding agents a durable loop for proposing changes, testing them, learning from measured outcomes, and using that evidence to choose the next improvement.

Here RSI means an evidence-driven recursive research loop, not an unconstrained self-modifying agent. Each validated cycle can improve the target system and, when the task contract permits it, the search strategy, evaluator, tools, or research process used to produce later improvements.

Before an agent starts changing code, the workflow makes it explain the task in plain language: what is being improved, what may change, how candidates will be measured, what counts as success, and what the work is not allowed to claim. Once those decisions have been reviewed, the workflow can run a controlled improvement campaign with an explicit budget, small batches of work, independent checks, and a durable record of what was learned.

The workflow is not tied to a particular benchmark, model, codebase, or optimization method. Use it for tasks such as reducing latency or cost, improving a model or game-playing agent, tuning a configuration, or searching over alternative implementations. It is especially useful when a passing test is not enough to prove that a change is genuinely better.

This repository provides the RSI workflow as thirteen reusable Agent Skills, a
shared `AGENTS.md`, and an optional execution harness with a project-level Codex
Hook. It does not provide a domain-specific optimizer, promise a winning
solution, or remove human authority over consequential actions.

## What problem does it solve?

Optimization work often goes wrong before the search even begins:

- the process runs repeated experiments but does not turn one cycle's evidence into a better next cycle;
- the goal sounds clear but the score, baseline, or success threshold is ambiguous;
- the agent changes something that was supposed to remain fixed;
- two results are compared under different data, code, or evaluation rules;
- a working implementation is mistaken for evidence of improvement;
- useful failures and decisions disappear into chat history;
- later work cannot tell what is still authorized, reusable, or unproven.

This workflow keeps those decisions in the repository. A new user or agent can resume from the files instead of reconstructing the project from an old conversation.

## What does it produce?

The workflow has two stages.

| Stage | What happens | Main result |
|---|---|---|
| Define the task and search | Explain the real-world task, design the decision-relevant measurement protocol, decide what candidates may look like, and obtain an independent review. | `PROBLEM.md` and `REPRESENTATION.md` |
| Run the improvement campaign | Choose a starting approach, design consequential implementation architecture when needed, reuse or obtain Permission for protected consequences, implement and measure candidates separately, learn from results, and close or recover the campaign. | `FRONTIER.md` and records under `frontier/` |

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

## Quick start

The consuming project must use Git. Save ordinary project checkpoints when work becomes a fixed review input, published result, or recovery point, and retain the referenced history. No remote push or new hosting service is required. Keep large payloads in an existing artifact store or retained local directory; Git references alone do not make those payloads available.

First ask the agent to define and review the task:

```text
Use frame-optimization to define inference-cost-reduction and continue through representation readiness.
```

This example requests framing only. After an independent review approves exactly what may be searched, explicitly start the improvement campaign for the same task:

```text
Use frontier-optimization to start the campaign for docs/skills/optimization/inference-cost-reduction/.
```

For an end-to-end optimization request, ask for both stages at the outset:

```text
Use frame-optimization to define and review inference-cost-reduction, then continue with frontier-optimization within the adopted objective, budget, access, and effect limits.
```

When the existing request includes subsequent optimization, a ready framing handoff or completed worker assignment does not end the task. The coordinator continues through the next permitted action. A framing-only, review-only, or planning-only request ends at its requested deliverable; an explicit pause or scope change remains binding.

The agent stores the task under `docs/skills/optimization/<task-name>/` and resumes from those files on later runs.

## How the workflow protects the result

- One coordinator owns the task definition and search design; another owns the later campaign. Worker Skills cannot silently change either contract.
- A fresh-context measurement designer can create or repair the complete decision-relevant protocol. It reconstructs how values are initialized, updated, aggregated, and related to the real objective; unsupported proxy relationships remain explicit. It separates execution, the intended change, the observed outcome, and its explanation when that distinction affects the decision, then asks only for evidence justified by the next use and the cost of being wrong. The framing coordinator must adopt that projection as a whole before it becomes part of the task contract.
- A fresh-context implementation designer resolves an important technical question only when existing agreements do not already settle the consequential behavior, ownership, interface, architecture, or migration choice. The designer grounds the answer in expected objective value or learning value; a shared design map and independent design Review are used only when the question and next consequence require them.
- Frontier-seeking design can start from an explicitly untested conjecture grounded in experience, analogy, intuition, retained results, automated search, or mechanism reasoning. It must state the intended change and the objective-relevant observation that would inform further investment, but it does not need a proven bottleneck, complete causal account, or predicted advantage before development. Local refinements remain useful, yet their simplicity or small positive results cannot indefinitely defer comparison with a credible core-mechanism alternative.
- Independent review is selected by the consequence of error, not by a fixed stage sequence. A reviewer checks the exact Git-backed subject and may use separately versioned supporting evidence; an existing review contributes its checked conclusions without becoming an implicit gate for every later action.
- A decision-bearing threshold has one current normative owner. Copied constants, warnings, operational limits, exploratory scenarios, heuristic margins, and convenient engineering targets cannot silently become broader rejection, route, or stopping rules. A changed workload, statistic, scope, direction, or consequence returns only the affected decision to that owner.
- Negative implementation evidence applies first to the exact realization and operating conditions observed. It reaches a shared design or route only when the evidence establishes a limiting cause of the same scope; failure to find another implementation is not proof that none exists.
- The repository's current language, runtime, toolchain, or implementation shape does not restrict the legal solution space unless the task, a verified environment, a hard physical or theoretical boundary, safety, law, or an adopted user decision requires that restriction.
- One Batch is a stable allocation toward one independently judged result, not an immutable packet, command, proposal hash, or candidate identity. Its implementation, checks, Reviews, Permissions, limits, paths, and Candidate Revisions may evolve while that result remains the same.
- The current Batch interface is deliberately small: `Batch.open` defines the work, `Batch.apply` records routine progress, adopts a chosen saved Review, or updates same-result working state, and `Batch.perform` starts an action whose measurement or real-world Consequences make repetition matter. The maintained facts view reports only Batch-owned state; it does not reconstruct campaign accounting or professional conclusions.
- `run-frontier-batch` owns work from the first implementation change through debugging, integration, and observation. Preparation, editing, harmless checks, and repair stay inside the open Batch without acknowledgment, execution-start, snapshot, packet, or result identities. A failed check does not create another Batch or Attempt, and an internal worker return is not a terminal result.
- Complex or cross-context implementation uses a lightweight working plan in ordinary working material. It preserves the current step, prerequisites, progress, feedback, observations, and remaining work without creating another lifecycle, approval gate, or commit requirement.
- Git owns retained project bytes. A Candidate Revision is one full commit plus explicit repository-relative paths, so a Review, check, or action can name exact bytes without copying the repository into workflow snapshots. Design documents keep stable paths, section anchors, and slice keys; their consuming Review, Batch, or assignment owns the saved Git reference, avoiding self-referential document hashes.
- R records own independent Review meaning. A governance resolver reads the saved R and checks whether its conclusions cover the proposed action; only Reviews needed for the current action appear in its required list, while other retained R records remain reusable evidence. V records own user tradeoffs and Permission for uncovered paid, external, sensitive, irreversible, or user-controlled scarce-resource work. Review readiness does not create Permission, and Permission does not prove execution or improvement.
- The agent reuses an applicable V instead of asking again. Ordinary technical choices, local implementation changes, Batch identities, and internal resource allocation do not become user questions. When a valuable action crosses an uncovered user boundary, the resolver may select one exact permission question with its purpose, scope, cost, and expected decision-changing observation; the action remains unavailable until the user grants it.
- Budget owns governing campaign-wide capacity, reservations, actual and unknown governed consumption, and remaining balance. Batch operational limits are separate: the coordinator may revise them within the same independently judged result and existing boundaries, but cannot turn protected reserve into routine capacity or expand the campaign ceiling.
- A working assignment supplies the current research problem, enough context and ownership to begin useful work, and source references as starting points rather than a read whitelist. Open direction research may combine different professional perspectives around the same problem instead of dividing a preset route menu; workers report concrete assumption failures, expanding dependencies, and promising alternatives that may change investment.
- Before consequential adoption or cold recovery, the coordinator reads the controlling objective, incoming restrictions, actual reasons and switching conditions, and intended outgoing work together. A local assignment or historical restriction cannot silently replace the broader objective, while a legitimate focused task remains focused.
- Reusable understanding is retained as one current explanation with its incorporated returns. Exact source and return bytes can be stored once and retrieved by content identity, so a cold receiver gets complete current context without copying the full history into every handoff. Delivery identity proves the bytes supplied, not their truth or authority.
- The coordinator orders early research, prerequisites, implementation, feedback, and long-task recovery around the current research commitment and the missing observation. An ordinary step may be necessary without independently improving the metric or changing direction. Internal process, audit, authorization, or identity machinery that blocks feasible authorized work is a workflow defect: the responsible owner corrects it and work resumes, while real limits and effects already incurred remain binding.
- A known correction must change the affected current task, dependency, dispatch, or return before that work continues. Stable identifiers, status labels, updated records, or disclaimers do not establish current use by themselves. The owner retains the finding, saves the corrected objects, and checks the actual next action; unrelated work remains available.
- A reused consequential judgment stays bound to the objective, evidence, selected consequence, and actual task it covered. Ordinary progress can retain that judgment, but a changed assignment, terminal disposition, or route-ending restriction returns to the existing owner instead of borrowing an old reference or unchanged label.
- The research chain carries its advantage hypothesis and selected target feedback across Batches, versions, and owners. Once the necessary state exists, the coordinator obtains that feedback by default; repeated delay must resolve into feedback, necessary repair, real waiting, or a changed allocation before dependent optional work continues. This uses the existing plan and decision owner rather than adding another ledger, gate, or Review.
- Delayed or changing observations retain an owner, delivery path, due condition, accumulated exposure, and intended decision use across worker returns and context changes. A scheduled or promised read is not a completed observation; failed delivery preserves uncertainty, and unrelated useful work may continue without duplicating an unsettled effect.
- A poor result is interpreted at the scope actually tested. When evidence identifies a concrete mismatch between the proposed capability and its operator, evaluator, or supporting arrangement, the owner compares bounded capability acquisition and remeasurement with a more direct observation, another method, or stopping. Novelty or disappointment alone does not justify support work.
- Research can transfer a mechanism or conditional result to another worthwhile question, and the representation can retain recoverable alternatives that still affect a whole-result choice. Selection changes the actual receiving assignment and preserves conditions, evidence, costs, and unresolved limits; a copied note or local ranking alone establishes neither transfer nor superiority.
- At consequential investment, design, and research choices, the existing owner considers material external changes and intervention-induced effects, including important interactions, delays, and opportunities for a different whole mechanism. This reasoning stays bounded to the decision at hand; it does not add a forecasting stage, scenario quota, universal robustness objective, or invented probabilities.
- Long repair chains retain a named reassessment point and the next meaningful observation across worker, owner, and Batch changes. Before expanding discretionary repair, the coordinator checks whether cumulative findings and remaining work still support the investment; same-B continuity and sunk effort do not answer that question.
- Each Batch owns one Measurement Definition. It records the question, comparator, scope, resource ceiling, lifecycle state, required context, evidence limits, result owner, and why the planned observation is sufficient for its intended decision. Measurement mode controls evidence use, not repeatability, Review, Permission, or resource ownership. Single-use fields are present only when the Action or adapter can consume a real single-use unit.
- Attempts exist only when a measurement or possible Consequence makes repetition important. An unresolved Attempt blocks another consequential performance in the same Batch, while routine work and other Batches continue. For genuine single-use work, the actual unit remains protected across Action-key changes until the Attempt is reconciled.
- Operation bindings protect the real seam involved—such as a paid call, external submission, sensitive access, irreversible change, remote job, or single-use sample—without activating unrelated controls.
- A technical or fidelity finding returns to its existing owner and remains in the same Batch when the independently judged result is unchanged. Repair follows the affected producer-to-consumer path and reruns only relevant checks. An inherited internal restriction that no longer protects a real boundary is corrected through the same Batch rather than promoted into a strategic replan or user decision. Only dependent work pauses; unaffected legal work continues.
- Result adoption separates validity from applicability. Delayed, partial, or support-failed observations retain the raw facts they actually establish without turning missing values into zero or complete comparisons. Objective-relevant costs, adverse observations, and unanswered design questions remain visible when they challenge a still-used advantage or learning premise. When measurement meaning and interpretation limits are unchanged, corrected processing of recoverable raw evidence does not create another measurement attempt, including after an operation starts or fails. A correctly produced initialization value, intermediate state, or unknown proxy may be valid evidence while remaining ineligible for stronger performance or investment conclusions. Repeatable public development evidence may guide hypotheses, screening, provisional ranking, and the next candidate inside its adopted ceiling when adaptive exposure is recorded; an exact repeat that cannot change the pending decision is dominated. Only a valid formal comparison may create adopted Evidence or support stronger claims.
- After each result is adopted, the coordinator establishes its supported meaning, reconciles effects and resources, and recovers the current research question, the observation it still needs, and what the new facts changed. It then continues, repairs, follows an existing branch, or reconsiders the investment. A terminal Batch, a passed prerequisite, or a new follow-on Batch does not by itself trigger another direction resolution.
- `reflect-frontier` can turn the experience of a completed, retired, or replaced route—or a substantial learning checkpoint—into technical insight and promising next ideas while the campaign is still active. Reflection informs professional judgment but does not select work, allocate budget, grant authority, or block otherwise-ready work.
- When an adopted change in shared problem understanding, representation, evaluation meaning, or research premises makes the current agenda unsuitable, the coordinator can advance the research generation without forcing full closeout. Applicable work, evidence, permissions, reservations, and accounting remain intact; only work whose real dependency changed pauses.
- Results identify the problem and representation versions under which they were produced, so incompatible results are not compared.
- Frame documents and handoffs own durable task, comparison, resource, feedback, stop, claim, and reuse rules. Live generation, Selection, Permission, spending, adopted-result, and recovery state stays in `FRONTIER.md`, `frontier/ledger.md`, and the latest complete closeout, so a stale explanatory value in an older handoff does not by itself invalidate the task contract.
- Parent revisions affect only decisions that depend on the changed meaning. Unaffected work and historical conclusions remain usable; a new revision number alone does not force campaign closeout or a new generation. A generation advances only when a material shared-premise change makes the existing research agenda unsuitable or incomplete.
- Project evidence and workflow releases remain separate. Updating an installed Skill does not rewrite or invalidate an existing project decision, Review, Permission, result, or handoff.
- Current automation reads saved Git inputs through one literal-path helper and exposes named Batch facts to ordinary callers. Release checks use the maintained source-module inventory to select current tests and the compatibility tests affected by a change, while unclassified source changes escalate to the full release suite.
- Foreseeable shared capabilities such as evaluation, packaging, submission, storage, and recovery are planned before dependent work makes reuse fragile. A project records the supported entry, scope, defaults, owner, checks, known gaps, and justified deferrals without requiring a central registry or a second consumer first.
- Budget, stopping rules, known limits, and permitted claims remain visible in the main campaign document.
- One ordered direction resolver is used only when choosing the next research problem or when evidence, cost, opportunity, time, resources, or scope may justify changing the current investment. Ordinary implementation, repair, integration, measurement, and technical diagnosis remain with their existing owners.
- A persisted direction resolution governs only the investment it actually selected. The coordinator may reconsider that investment before a Batch ends when repeated support work is not approaching the needed observation, an assumption fails, dependencies materially expand, or a credible higher-value opportunity appears.
- Historical technical rankings remain evidence within their original scope. They do not become strategic boundaries merely because an earlier design, plan, or resolution recorded them; only a change to an actual governing commitment, allocation, stop rule, irreversible behavior, or claim limit requires strategic replanning.
- A closed candidate or route does not end a continuing task. The coordinator re-evaluates worthwhile direct actions and grounded research questions, or records a campaign-wide stop and closes the campaign when neither remains. An empty old route list or an unmet objective alone does not force research or justify waiting for the user to supply a technical target.
- An unresolved investment choice triggers one independent, fresh-context comparison inside that resolver. The coordinator checks the factual basis and applicable limits, preserves the professional ordering, and adopts the result. Before adoption, a concrete source omission, contract misreading, or unequal comparison returns to the original resolver for correction in the same task; finalized results remain historical unless the decision inputs genuinely change.
- Route comparison considers the minimum sufficient commitment, its full cost and opportunity cost, and what its outcome can change. An inexpensive but underpowered probe is not automatically preferable, and sunk cost does not favor the incumbent route.
- A focused research question is investigated directly. A route-landscape assignment can investigate a bounded mechanism or coverage gap before a replacement route is known; distinct independent questions may use temporary specialists, but one parent returns one normalized result for adoption. Research stops when further retrieval is unlikely to change the current allocation and records when its conclusions should be reconsidered.
- If valid execution, measurement, and local-mechanism explanations are exhausted, the workflow can return an exact semantic challenge to the parent task contract instead of repeating in-scope work that can no longer reach the objective.
- Independent reviews use one saved Git commit with explicit subject paths and an agent that has not seen the drafting conversation, but only when the next actual consequence requires that assurance. Supporting parents and evidence keep their own saved versions instead of being copied into the subject. Review methods are not sequential approval stages, and ordinary result validation does not require a separate claims review.
- Reviews answer the remaining consequential question in their assigned branch and reuse applicable earlier conclusions. A professional recommendation informs the coordinator, but does not by itself change route choice, reopen work, or create a new proof, approval, or review obligation.
- Entry repair reviews inspect the corrected saved version, its changes, and affected conclusions. They reuse earlier conclusions only where their assumptions still apply; a reviewer’s suggested repair does not become an extra acceptance requirement.
- Campaign state is recovered from retained Git versions, records, and required artifact payloads, not from conversation history. Normal edits do not invalidate reviews of saved bytes, and restoring working files does not undo spending, evidence, or external effects.
- Reusing retained material preserves its original producing versions, reviews, and charges. Candidate recovery checks the content and latest accounting needed for the proposed use; it does not grant readiness or permission. Existing conclusions need further review only when a relevant change, a new use, or concrete contrary evidence affects them. Missing content pauses its dependent use, not all recovery planning.
- A project handoff cites the existing closing record, Git history, and retained artifacts. An explicit export writes a small reference file, not another complete project archive. The receiving environment must have the referenced history and any payloads needed for its next action.
- Historical packet, snapshot, acknowledgment, execution-start, result-identity, and typed-provenance formats remain readable through isolated compatibility checks. New work uses the current Batch record and does not backfill or regenerate those identities.

## Skills

Install all thirteen Skills as one workflow. Normally, users invoke only the two coordinators; the coordinators assign the narrower worker Skills.

Each Skill entry point routes the agent to the references needed for its current stage or action. Detailed packet formats and historical compatibility rules stay in separate files and are read only when relevant. Install the complete folders so this selective reading does not omit required workflow rules.

### Define the task and search

- **[frame-optimization](./skills/frame-optimization/SKILL.md)** — Coordinates the problem definition, search representation, repair loops, reviews, and final handoff.
- **[design-measurement](./skills/design-measurement/SKILL.md)** — Designs or repairs reusable measurement meaning in a fresh context, including lifecycle, source coverage, target relationship, and evidence ceilings, without adopting it or choosing campaign actions.
- **[research-optimization](./skills/research-optimization/SKILL.md)** — Investigates one assigned question without changing the task contract.
- **[grill-optimization](./skills/grill-optimization/SKILL.md)** — Collects one decision that only the user can make.
- **[review-optimization](./skills/review-optimization/SKILL.md)** — Independently checks problem readiness, measurement-design readiness in proportion to its intended consequence, fixed measurement-support implementations, or retained-result comparability.
- **[review-representation](./skills/review-representation/SKILL.md)** — Independently checks the proposed search space and the exact scope that later work may use.

### Run the improvement campaign

- **[frontier-optimization](./skills/frontier-optimization/SKILL.md)** — Coordinates campaign entry, planning, budget, batch selection, accepted results, closeout, and recovery.
- **[design-implementation](./skills/design-implementation/SKILL.md)** — Resolves an important implementation-design question in a fresh context when existing agreements do not settle it, without taking over campaign routing, Review, Permission, or execution.
- **[research-frontier](./skills/research-frontier/SKILL.md)** — Answers one focused question or synthesizes technical directions through source-grounded, multidisciplinary research without treating the assigned options as a closed menu.
- **[grill-frontier](./skills/grill-frontier/SKILL.md)** — Collects one unresolved user tradeoff or Permission decision after existing V records and technical evidence have been exhausted.
- **[run-frontier-batch](./skills/run-frontier-batch/SKILL.md)** — Advances assigned Batch work from implementation and research through debugging, integration, and observation, using a recoverable working plan when the work spans contexts.
- **[review-frontier](./skills/review-frontier/SKILL.md)** — Independently reviews one exact Git-backed Entry, replan, design, implementation revision, or proposed claim when a remaining consequential question requires review.
- **[reflect-frontier](./skills/reflect-frontier/SKILL.md)** — Turns substantive route experience or cross-route learning into technical insight and promising ideas without choosing or authorizing work.

Internally, the first stage uses A–H and R1–R8 as completeness checklists. Users do not need to learn those labels before starting; the main documents must explain their meaning in ordinary task language.

## Workflow at a glance

```text
Define the problem
  -> design the decision-relevant measurement protocol in a fresh context
  -> decide how candidates can be represented and searched
  -> independently approve an exact search scope
  -> choose a starting approach and budget
  -> recover the current research commitment, missing observation, and relevant new facts
  -> retain a reachable discovery point and resolve it when due, even while local work succeeds
  -> resolve consequential implementation design in a fresh context only when existing agreements are insufficient
  -> save the exact project subject in Git and obtain only the Review needed by the next actual consequence
  -> reuse an applicable V, or ask once for an uncovered user tradeoff or protected consequence
  -> open one Batch for one independently judged result
  -> order preparation, research, implementation, feedback, and recovery around the research commitment
  -> apply known corrections to the actual current task and affected next action
  -> apply routine preparation, editing, checking, and repair without creating Attempts or identity chains
  -> perform measurement or consequential actions through a bound operation, recording actual use and effects
  -> review exact implementations when required and measure under the approved comparison rules
  -> adopt each result, then recover the current research question, missing observation, and facts that changed
  -> continue, repair, follow an existing branch, or reconsider the investment through the appropriate existing owner
  -> reflect on substantive route experience when it can improve current or future technical choices, without blocking ready work
  -> invoke one ordered direction resolver only when selecting or reconsidering the investment
  -> advance the research generation in place when a material shared-premise change makes the current agenda unsuitable
  -> on a campaign-wide stop or halt, reconcile evidence, spending, retained assets, learning, and the remaining gap
  -> complete closeout with final limits and the files needed to resume later
```

The loop pauses only work affected by an exhausted limit, missing permission, an unresolved dependency, or a relevant task-definition change. Unaffected permitted work can continue. Full closeout requires a campaign-wide ending condition or an explicit user stop.

## Shared agent instructions

This repository includes a task-neutral [`AGENTS.md`](./AGENTS.md) for outcome-oriented optimization behavior. The detailed workflow remains in the Skills. Codex reads `AGENTS.md` directly. Claude Code 2.1.277 or later can also read `AGENTS.md` directly when no project `CLAUDE.md` or `CLAUDE.local.md` takes precedence; the checked-in [`CLAUDE.md`](./CLAUDE.md) imports `AGENTS.md` to support mixed-file repositories, older versions, and sessions where direct support is unavailable.

When adding the workflow to another repository:

- if no agent instruction file exists, copy `AGENTS.md`; modern Claude Code can use it directly, while a `CLAUDE.md` containing `@AGENTS.md` provides the broadest compatibility;
- if `AGENTS.md` already exists, merge the `Frontier-seeking workflow behavior`, `User-facing workflow returns`, and `Common project capabilities` sections once each and preserve all repository-specific rules and capability records;
- if `CLAUDE.md` already exists, add `@AGENTS.md` once without replacing its Claude Code-specific content; for `.claude/CLAUDE.md`, use `@../AGENTS.md` instead;
- inspect nested instruction files and `AGENTS.override.md` before choosing where the shared rules should apply; and
- resolve conflicts explicitly. Shared optimization behavior never broadens existing authority or weakens task-specific safety, resource, evidence, or validation rules.

Claude Code plugins provide Skills but do not load a plugin-root project instruction file for the consuming repository, so deploy or merge the instruction files separately. See [Deploying shared agent instructions](./docs/agent-instructions.md) for direct `AGENTS.md` support, compatibility adapters, existing-file handling, nested instructions, and verification.

## Reusable project capabilities

The workflow now treats predictable shared modules as project capabilities that should be planned at project start, on a material scope change, or before the first dependent execution path is built. The project can keep a small capability table in its existing architecture or development documentation; no new service or global registry is required.

The shared record should identify the public entry, supported use, important defaults, implementation owner, focused checks, known gaps, and the next point at which a deferred need must be reconsidered. Evaluation engines, package builders, and submission adapters may be maintained this way, while each project still owns measurement meaning and each protected external action still requires its own permission and effect record.

An optional `tools/project-checks.json` lets the workflow's affected-check command select project-owned checks for instruction files, shared modules, and host adapters. See [Managing reusable project capabilities](./docs/project-capabilities.md) for the record shape, deployment guidance, and check-map example.

## Optional Codex Hook and execution harness

The repository includes a host-neutral Rust [workflow harness](./tools/workflow-harness/README.md)
and a project-level [Codex Hook](./.codex/hooks.json). The harness can preserve a
bounded research assignment, correlate agent returns, retain cumulative usage,
and withhold continuation at an explicit return condition. The Hook adds a
narrow observation layer for restored adopted-work context and supported agent
dispatch evidence.

The Hook is Codex-only in this release. It does not provide Claude Code, Cursor,
or other tool compatibility, and it is not part of the Claude Code plugin. Use
`AGENTS.md` and the documented `CLAUDE.md` import for shared behavior in Claude
Code; do not translate `.codex/hooks.json` into another host's Hook format.

Before using the Hook, build its binary:

```sh
cargo build --locked --release \
  --manifest-path tools/workflow-harness/Cargo.toml \
  --bin workflow-codex-hook
```

Codex loads repository Hooks only after the project layer is trusted. Inspect
and approve the exact definition with `/hooks`. If a consuming repository
already has `.codex/hooks.json`, merge the event entries instead of replacing
its Hooks; all matching Hooks run. Keep one Hook representation per project
layer rather than duplicating the same definition in `config.toml`.

The checked-in command resolves the Git root at runtime and contains no local
checkout path. Without a valid adopted-work pointer under
`.frontier/hook-context/`, it exits without changing a tool decision. The Hook
does not grant permission, deny ordinary tools, call a model, resume paused work,
or continue a session automatically. See the harness documentation for setup,
scope, and evidence limits.

## Install

### Agent Skills installer

Use this route for Codex, Claude Code, Cursor, and other Agent Skills-compatible coding agents:

```bash
npx skills@latest add Noehub2025/noehub-factory-optimization
```

Choose all thirteen Skills and the coding agents where you want to install them.

### Claude Code plugin

```text
/plugin marketplace add Noehub2025/noehub-factory-optimization
/plugin install noehub-factory-optimization@noehub
```

The plugin installs all thirteen Skills as one managed bundle.

### Manual installation

Copy or symlink every folder under `skills/` into the project-level or user-level Skill directory for the target agent:

| Agent | Project-level directory | User-level directory |
|---|---|---|
| Codex | `.agents/skills/` | `~/.agents/skills/` |
| Claude Code | `.claude/skills/` | `~/.claude/skills/` |
| Cursor | `.agents/skills/` or `.cursor/skills/` | `~/.agents/skills/` or `~/.cursor/skills/` |

Keep each complete Skill folder together. Its `SKILL.md`, references, scripts, fixtures, and optional `agents/openai.yaml` file form one unit.

## Repository layout

```text
AGENTS.md             shared cross-agent workflow behavior
CLAUDE.md             Claude Code adapter that imports AGENTS.md
docs/
  agent-instructions.md
  project-capabilities.md
.codex/
  hooks.json           Codex-only project Hook definition
skills/<skill-name>/
  SKILL.md
  references/          optional detailed guidance
  scripts/             optional deterministic checks and packaging tools
  agents/openai.yaml   optional Codex display metadata
tools/workflow-harness/
  Cargo.toml           host-neutral runtime and Codex adapter
  run-codex-hook       portable launcher for the built Hook binary
tools/project-checks.json
                       project-owned affected-check map
.claude-plugin/
  plugin.json
  marketplace.json
```

## License

MIT
