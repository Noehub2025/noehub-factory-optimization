# Noehub Factory Optimization

Noehub Factory Optimization is a task-agnostic Recursive Self-Improvement (RSI) workflow for automated optimization research. It gives coding agents a durable loop for proposing changes, testing them, learning from measured outcomes, and using that evidence to choose the next improvement.

Here RSI means an evidence-driven recursive research loop, not an unconstrained self-modifying agent. Each validated cycle can improve the target system and, when the task contract permits it, the search strategy, evaluator, tools, or research process used to produce later improvements.

Before an agent starts changing code, the workflow makes it explain the task in plain language: what is being improved, what may change, how candidates will be measured, what counts as success, and what the work is not allowed to claim. Once those decisions have been reviewed, the workflow can run a controlled improvement campaign with an explicit budget, small batches of work, independent checks, and a durable record of what was learned.

The workflow is not tied to a particular benchmark, model, codebase, or optimization method. Use it for tasks such as reducing latency or cost, improving a model or game-playing agent, tuning a configuration, or searching over alternative implementations. It is especially useful when a passing test is not enough to prove that a change is genuinely better.

This repository provides the RSI workflow as eleven reusable Agent Skills. It does not provide a domain-specific optimizer, promise a winning solution, or remove human authority over consequential actions.

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
| Run the improvement campaign | Choose a starting approach, authorize bounded work, implement and measure candidates separately, learn from results, and close or recover the campaign. | `FRONTIER.md` and records under `frontier/` |

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

First ask the agent to define and review the task:

```text
Use frame-optimization to define inference-cost-reduction and continue through representation readiness.
```

After an independent review approves exactly what may be searched, explicitly start the improvement campaign for the same task:

```text
Use frontier-optimization to start the campaign for docs/skills/optimization/inference-cost-reduction/.
```

The agent stores the task under `docs/skills/optimization/<task-name>/` and resumes from those files on later runs.

## How the workflow protects the result

- One coordinator owns the task definition and search design; another owns the later campaign. Worker Skills cannot silently change either contract.
- A fresh-context measurement designer can create or repair the complete decision-relevant protocol. The framing coordinator must adopt that projection as a whole before it becomes part of the task contract.
- Planning, user authorization, worker acknowledgment, execution start, implementation review, measurement, result adoption, and claims are separate gates. Each gate applies only to the exact files and identities it names.
- Candidate creation and performance evaluation are separate steps. Passing engineering checks does not prove improvement.
- A fresh-context, read-only analyst interprets each terminal technical result before seeing the current selection, budget, authority, stopping state, or proposed next action. This keeps the technical meaning of the evidence separate from what the campaign may do next.
- After each completed batch, the agent compares the result with the hypothesis fixed before the work, records the strongest mechanism the evidence supports, and keeps unresolved component attribution separate from the proven whole-package effect.
- Results identify the problem and representation versions under which they were produced, so incompatible results are not compared.
- Project evidence and workflow releases use separate identities. Updating an installed Skill does not rewrite or invalidate an existing project decision, review, authorization, result, or handoff.
- Review preparation deterministically freezes the exact project subject, its provenance chain, and the evidence a fresh reviewer may inspect. Workflow implementation files remain outside the project decision identity.
- Budget, stopping rules, known limits, and permitted claims remain visible in the main campaign document.
- One ordered direction resolver selects the first applicable next action or blocker, so research, diagnosis, direct attempts, budget limits, and parent escalation do not compete through separate decision paths.
- If valid execution, measurement, and local-mechanism explanations are exhausted, the workflow can return an exact semantic challenge to the parent task contract instead of repeating in-scope work that can no longer reach the objective.
- Independent reviews use fixed copies of the evidence and an agent that has not seen the drafting conversation. If that independent review is unavailable, the workflow reports a blocker instead of readiness.
- Campaign state is recovered from repository files and their recorded versions, not from conversation history.
- Portable project handoffs can be verified offline from exact project bytes and their typed provenance chain; they do not depend on copied workflow implementation files.

## Skills

Install all eleven Skills as one workflow. Normally, users invoke only the two coordinators; the coordinators assign the narrower worker Skills.

### Define the task and search

- **[frame-optimization](./skills/frame-optimization/SKILL.md)** — Coordinates the problem definition, search representation, repair loops, reviews, and final handoff.
- **[design-measurement](./skills/design-measurement/SKILL.md)** — Designs or repairs the decision-relevant measurement protocol in a fresh context without adopting it or choosing campaign actions.
- **[research-optimization](./skills/research-optimization/SKILL.md)** — Investigates one assigned question without changing the task contract.
- **[grill-optimization](./skills/grill-optimization/SKILL.md)** — Collects one decision that only the user can make.
- **[review-optimization](./skills/review-optimization/SKILL.md)** — Independently checks problem readiness, fixed measurement-support implementations, or whether old and new results remain comparable.
- **[review-representation](./skills/review-representation/SKILL.md)** — Independently checks the proposed search space and the exact scope that later work may use.

### Run the improvement campaign

- **[frontier-optimization](./skills/frontier-optimization/SKILL.md)** — Coordinates campaign entry, planning, budget, batch selection, accepted results, closeout, and recovery.
- **[research-frontier](./skills/research-frontier/SKILL.md)** — Researches one assigned approach landscape or evidence question.
- **[grill-frontier](./skills/grill-frontier/SKILL.md)** — Collects one user tradeoff or authorization for an exact reviewed choice.
- **[run-frontier-batch](./skills/run-frontier-batch/SKILL.md)** — Executes one bounded research, design, implementation, or evaluation batch.
- **[review-frontier](./skills/review-frontier/SKILL.md)** — Independently reviews one frozen plan, design, implementation, recovery decision, or proposed claim.

Internally, the first stage uses A–H and R1–R8 as completeness checklists. Users do not need to learn those labels before starting; the main documents must explain their meaning in ordinary task language.

## Workflow at a glance

```text
Define the problem
  -> design the decision-relevant measurement protocol in a fresh context
  -> decide how candidates can be represented and searched
  -> independently approve an exact search scope
  -> choose a starting approach and budget
  -> review and authorize one exact bounded batch when required
  -> deterministically prepare the exact project-only subject for each fresh review
  -> acknowledge the packet and freeze its execution baseline
  -> start and run the batch
  -> review implementations before measuring them
  -> measure under the approved comparison rules
  -> interpret the technical evidence in a fresh context, then compare it with the precommitted hypothesis and record supported mechanisms and limits
  -> apply one ordered direction resolver to select the next action or blocker
  -> close the campaign with final evidence, limits, and files needed to resume later
```

The loop may stop early when evidence is sufficient, the budget or a stopping rule is reached, required permission is missing, or the approved task definition changes.

## Shared agent instructions

This repository includes a task-neutral [`AGENTS.md`](./AGENTS.md) for outcome-oriented optimization behavior. The detailed workflow remains in the Skills. Codex reads `AGENTS.md` directly; Claude Code uses the checked-in [`CLAUDE.md`](./CLAUDE.md) adapter, which imports `AGENTS.md` instead of duplicating it.

When adding the workflow to another repository:

- if no agent instruction file exists, copy `AGENTS.md` and add a `CLAUDE.md` containing `@AGENTS.md` for Claude Code;
- if `AGENTS.md` already exists, merge the `Frontier-seeking workflow behavior` and `User-facing workflow returns` sections once each and preserve all repository-specific rules;
- if `CLAUDE.md` already exists, add `@AGENTS.md` once without replacing its Claude Code-specific content; and
- resolve conflicts explicitly. Shared optimization behavior never broadens existing authority or weakens task-specific safety, resource, evidence, or validation rules.

Claude Code plugins provide Skills but do not load a plugin-root `CLAUDE.md` as project context, so deploy or merge the instruction files separately. See [Deploying shared agent instructions](./docs/agent-instructions.md) for the complete new-repository, existing-file, nested-instruction, and verification procedure.

## Install

### Agent Skills installer

Use this route for Codex, Claude Code, Cursor, and other Agent Skills-compatible coding agents:

```bash
npx skills@latest add Noehub2025/noehub-factory-optimization
```

Choose all eleven Skills and the coding agents where you want to install them.

### Claude Code plugin

```text
/plugin marketplace add Noehub2025/noehub-factory-optimization
/plugin install noehub-factory-optimization@noehub
```

The plugin installs all eleven Skills as one managed bundle.

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
