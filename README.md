# Noehub Factory Optimization

Noehub Factory Optimization is a task-agnostic Recursive Self-Improvement (RSI) workflow for automated optimization research. It gives coding agents a durable loop for proposing changes, testing them, learning from measured outcomes, and using that evidence to choose the next improvement.

Here RSI means an evidence-driven recursive research loop, not an unconstrained self-modifying agent. Each validated cycle can improve the target system and, when the task contract permits it, the search strategy, evaluator, tools, or research process used to produce later improvements.

Before an agent starts changing code, the workflow makes it explain the task in plain language: what is being improved, what may change, how candidates will be measured, what counts as success, and what the work is not allowed to claim. Once those decisions have been reviewed, the workflow can run a controlled improvement campaign with an explicit budget, small batches of work, independent checks, and a durable record of what was learned.

The workflow is not tied to a particular benchmark, model, codebase, or optimization method. Use it for tasks such as reducing latency or cost, improving a model or game-playing agent, tuning a configuration, or searching over alternative implementations. It is especially useful when a passing test is not enough to prove that a change is genuinely better.

This repository provides the RSI workflow as thirteen reusable Agent Skills. It does not provide a domain-specific optimizer, promise a winning solution, or remove human authority over consequential actions.

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
- A fresh-context measurement designer can create or repair the complete decision-relevant protocol. It reconstructs how values are initialized, updated, aggregated, and related to the real objective; unsupported proxy relationships remain explicit. The framing coordinator must adopt that projection as a whole before it becomes part of the task contract.
- A fresh-context implementation designer owns architecture and interface meaning when work changes a consequential technical seam. A separate reviewer checks the exact Git-backed design before affected implementation proceeds.
- A consequential implementation design must positively ground every decisive feasibility claim under the relevant conditions. Missing final implementation, novelty, or ordinary implementation risk alone does not justify another evidence gate.
- A decision-bearing threshold has one current normative owner. Copied constants, warnings, operational limits, and convenient engineering targets cannot silently become broader rejection, route, or stopping rules. A changed workload, statistic, scope, direction, or consequence returns only the affected decision to that owner.
- Negative implementation evidence applies first to the exact realization and operating conditions observed. It reaches a shared design or route only when the evidence establishes a limiting cause of the same scope; failure to find another implementation is not proof that none exists.
- The repository's current language, runtime, toolchain, or implementation shape does not restrict the legal solution space unless the task, a verified environment, a hard physical or theoretical boundary, safety, law, or an adopted user decision requires that restriction.
- One Batch is a stable allocation toward one independently judged result, not an immutable packet, command, proposal hash, or candidate identity. Its implementation, checks, Reviews, Permissions, limits, paths, and Candidate Revisions may evolve while that result remains the same.
- The current Batch interface is deliberately small: `Batch.open` defines the work, `Batch.apply` records routine progress, and `Batch.perform` starts an action whose measurement or real-world Consequences make repetition matter.
- Preparation, editing, local debugging, harmless checks, and repair stay inside the open Batch without acknowledgment, execution-start, snapshot, packet, or result identities. A failed check does not create another Batch or Attempt.
- Git owns retained project bytes. A Candidate Revision is one full commit plus explicit repository-relative paths, so a Review, check, or action can name exact bytes without copying the repository into workflow snapshots.
- R records own independent Review meaning. V records own user tradeoffs and Permission for uncovered paid, external, sensitive, irreversible, or user-controlled scarce-resource work. Review readiness does not create Permission, and Permission does not prove execution or improvement.
- The agent reuses an applicable V instead of asking again. Ordinary technical choices, local implementation changes, Batch identities, and internal resource allocation do not become user questions.
- Budget owns governing campaign-wide capacity, reservations, actual and unknown governed consumption, and remaining balance. Batch operational limits are separate: the coordinator may revise them within the same independently judged result and existing boundaries, but cannot turn protected reserve into routine capacity or expand the campaign ceiling.
- Candidate creation and performance evaluation are separate steps. Passing engineering checks does not prove improvement.
- Each Batch owns one Measurement Definition. It records the question, comparator, scope, resource ceiling, lifecycle state, required context, evidence limits, and result owner. Measurement mode controls evidence use, not repeatability, Review, Permission, or resource ownership. Single-use fields are present only when the Action or adapter can consume a real single-use unit.
- Attempts exist only when a measurement or possible Consequence makes repetition important. An unresolved Attempt blocks another consequential performance in the same Batch, while routine work and other Batches continue. For genuine single-use work, the actual unit remains protected across Action-key changes until the Attempt is reconciled.
- Operation bindings protect the real seam involved—such as a paid call, external submission, sensitive access, irreversible change, remote job, or single-use sample—without activating unrelated controls.
- A technical or fidelity finding returns to its existing owner and remains in the same Batch when the independently judged result is unchanged. Only dependent work pauses; unaffected legal work continues.
- Result adoption separates validity from applicability. A correctly produced initialization value, intermediate state, or unknown proxy may be valid evidence while remaining ineligible for stronger performance or investment conclusions. Repeatable public development evidence may guide hypotheses, screening, provisional ranking, and the next candidate inside its adopted ceiling when adaptive exposure is recorded; an exact repeat that cannot change the pending decision is dominated. Only a valid formal comparison may create adopted Evidence or support stronger claims.
- After each terminal result is adopted, the coordinator establishes implementation, measurement, and comparison validity, connects the result to its pre-work hypothesis and exact technical lineage, and applies one ordered direction resolver directly to the adopted evidence. This creates no intermediate per-batch reflection gate or narrative artifact.
- At a campaign-wide closeout, a fresh-context `reflect-frontier` pass turns the generation's adopted successes, failures, costs, retained assets, and remaining gap into search advantage and a small set of worthwhile opportunities for the next generation. It does not select work, allocate budget, or grant authority.
- If closing evidence may challenge durable problem or representation meaning, Reflection carries the cited adopted evidence—not its own verdict—into the next ordinary Entry. The existing direction resolver may refer only the affected rule back to Framing; this creates no second resolver, extra diagnosis, or new reflection gate.
- Results identify the problem and representation versions under which they were produced, so incompatible results are not compared.
- Frame documents and handoffs own durable task, comparison, resource, feedback, stop, claim, and reuse rules. Live generation, Selection, Permission, spending, adopted-result, and recovery state stays in `FRONTIER.md`, `frontier/ledger.md`, and the latest complete closeout, so a stale explanatory value in an older handoff does not by itself invalidate the task contract.
- Parent revisions affect only decisions that depend on the changed meaning. Unaffected work and historical conclusions remain usable; prior spending or a new revision number alone does not force campaign closeout, a new generation, or a replacement candidate. The campaign coordinator can delegate an in-scope parent repair to the framing coordinator without asking the user to switch stages.
- Project evidence and workflow releases remain separate. Updating an installed Skill does not rewrite or invalidate an existing project decision, Review, Permission, result, or handoff.
- Budget, stopping rules, known limits, and permitted claims remain visible in the main campaign document.
- One ordered direction resolver selects the first applicable next action or blocker, so research, diagnosis, direct attempts, budget limits, and parent escalation do not compete through separate decision paths.
- A closed candidate or route does not end a continuing task. The coordinator re-evaluates worthwhile direct actions and grounded research questions, or records a campaign-wide stop and closes the campaign when neither remains. An empty old route list or an unmet objective alone does not force research or justify waiting for the user to supply a technical target.
- An unresolved route allocation or an evidence-grounded challenge triggers one independent, fresh-context comparison inside that resolver. The coordinator checks the factual inputs and applicable limits, preserves the technical ordering, and adopts the result. An already determined action or still-applicable resolution needs no repeat comparison unless a grounded challenge remains.
- Route comparison considers the minimum sufficient commitment, its full cost and opportunity cost, and what its outcome can change. An inexpensive but underpowered probe is not automatically preferable, and sunk cost does not favor the incumbent route.
- A focused research question is investigated directly. A route-landscape assignment can investigate a bounded mechanism or coverage gap before a replacement route is known; distinct independent questions may use temporary specialists, but one parent returns one normalized result for adoption. Research stops when further retrieval is unlikely to change the current allocation and records when its conclusions should be reconsidered.
- If valid execution, measurement, and local-mechanism explanations are exhausted, the workflow can return an exact semantic challenge to the parent task contract instead of repeating in-scope work that can no longer reach the objective.
- Independent reviews use one saved Git commit, explicit subject paths, and an agent that has not seen the drafting conversation, but only when the next actual consequence requires that assurance. A first Batch, measurement label, new candidate, or repeatable public local observation does not by itself require Entry Review; when no Review applies, Entry records that fact instead of creating a substitute verdict.
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
- **[design-implementation](./skills/design-implementation/SKILL.md)** — Authors or repairs consequential implementation architecture in a fresh context without taking over campaign routing, Review, Permission, or execution.
- **[research-frontier](./skills/research-frontier/SKILL.md)** — Answers one focused question directly or synthesizes a bounded route landscape, with temporary specialist contributions only where they add distinct evidence.
- **[grill-frontier](./skills/grill-frontier/SKILL.md)** — Collects one unresolved user tradeoff or Permission decision after existing V records and technical evidence have been exhausted.
- **[run-frontier-batch](./skills/run-frontier-batch/SKILL.md)** — Executes one bounded research, design, implementation, or evaluation batch.
- **[review-frontier](./skills/review-frontier/SKILL.md)** — Independently reviews one exact Git-backed Entry, replan, design, implementation revision, or proposed claim.
- **[reflect-frontier](./skills/reflect-frontier/SKILL.md)** — Converts one closing generation's adopted evidence into search assets and worthwhile opportunities for the next generation without choosing or authorizing work.

Internally, the first stage uses A–H and R1–R8 as completeness checklists. Users do not need to learn those labels before starting; the main documents must explain their meaning in ordinary task language.

## Workflow at a glance

```text
Define the problem
  -> design the decision-relevant measurement protocol in a fresh context
  -> decide how candidates can be represented and searched
  -> independently approve an exact search scope
  -> choose a starting approach and budget
  -> design consequential implementation architecture in a fresh context when established seams are not sufficient
  -> save the exact project subject in Git and obtain only the Review needed by the next actual consequence
  -> reuse an applicable V, or ask once for an uncovered user tradeoff or protected consequence
  -> open one Batch for one independently judged result
  -> apply routine preparation, editing, checking, and repair without creating Attempts or identity chains
  -> perform measurement or consequential actions through a bound operation, recording actual use and effects
  -> review exact implementations when required and measure under the approved comparison rules
  -> adopt the result, establish its validity, apply scoped conclusions and threshold ownership, and use one ordered direction resolver directly on the evidence
  -> on a campaign-wide stop or halt, reconcile the generation's evidence, spending, retained assets, and remaining gap
  -> reflect once in a fresh context to improve the next generation's search
  -> complete closeout with final limits and the files needed to resume later
```

The loop pauses only work affected by an exhausted limit, missing permission, an unresolved dependency, or a relevant task-definition change. Unaffected permitted work can continue. Full closeout requires a campaign-wide ending condition or an explicit user stop.

## Shared agent instructions

This repository includes a task-neutral [`AGENTS.md`](./AGENTS.md) for outcome-oriented optimization behavior. The detailed workflow remains in the Skills. Codex reads `AGENTS.md` directly; Claude Code uses the checked-in [`CLAUDE.md`](./CLAUDE.md) adapter, which imports `AGENTS.md` instead of duplicating it.

When adding the workflow to another repository:

- if no agent instruction file exists, copy `AGENTS.md` and add a `CLAUDE.md` containing `@AGENTS.md` for Claude Code;
- if `AGENTS.md` already exists, merge the `Frontier-seeking workflow behavior` and `User-facing workflow returns` sections once each and preserve all repository-specific rules;
- if `CLAUDE.md` already exists, add `@AGENTS.md` once without replacing its Claude Code-specific content; for `.claude/CLAUDE.md`, use `@../AGENTS.md` instead;
- inspect nested instruction files and `AGENTS.override.md` before choosing where the shared rules should apply; and
- resolve conflicts explicitly. Shared optimization behavior never broadens existing authority or weakens task-specific safety, resource, evidence, or validation rules.

Claude Code plugins provide Skills but do not load a plugin-root `CLAUDE.md` as project context, so deploy or merge the instruction files separately. See [Deploying shared agent instructions](./docs/agent-instructions.md) for the complete new-repository, existing-file, nested-instruction, and verification procedure.

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
skills/<skill-name>/
  SKILL.md
  references/          optional detailed guidance
  scripts/             optional deterministic checks and packaging tools
  agents/openai.yaml   optional Codex display metadata
.claude-plugin/
  plugin.json
  marketplace.json
```

## License

MIT
