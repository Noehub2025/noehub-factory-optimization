# Noehub Factory Optimization

Noehub Factory Optimization helps coding agents improve a system without losing track of what “better” means.

Before an agent starts changing code, the workflow makes it explain the task in plain language: what is being improved, what may change, how candidates will be measured, what counts as success, and what the work is not allowed to claim. Once those decisions have been reviewed, the workflow can run a controlled improvement campaign with an explicit budget, small batches of work, independent checks, and a durable record of what was learned.

Use it for tasks such as reducing latency or cost, improving a model or game-playing agent, tuning a configuration, or searching over alternative implementations. It is especially useful when a passing test is not enough to prove that a change is genuinely better.

This repository provides the workflow as ten reusable Agent Skills. It does not provide a domain-specific optimizer or a winning solution.

## What problem does it solve?

Optimization work often goes wrong before the search even begins:

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
| Define the task and search | Explain the real-world task, fix the comparison rules, decide what candidates may look like, and obtain an independent review. | `PROBLEM.md` and `REPRESENTATION.md` |
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
- Planning, user authorization, worker acknowledgment, execution start, implementation review, measurement, result adoption, and claims are separate gates. Each gate applies only to the exact files and identities it names.
- Candidate creation and performance evaluation are separate steps. Passing engineering checks does not prove improvement.
- Results identify the problem and representation versions under which they were produced, so incompatible results are not compared.
- Budget, stopping rules, known limits, and permitted claims remain visible in the main campaign document.
- Independent reviews use fixed copies of the evidence and an agent that has not seen the drafting conversation. If that independent review is unavailable, the workflow reports a blocker instead of readiness.
- Campaign state is recovered from repository files and their recorded versions, not from conversation history.

## Skills

Install all ten Skills as one workflow. Normally, users invoke only the two coordinators; the coordinators assign the narrower worker Skills.

### Define the task and search

- **[frame-optimization](./skills/frame-optimization/SKILL.md)** — Coordinates the problem definition, search representation, repair loops, reviews, and final handoff.
- **[research-optimization](./skills/research-optimization/SKILL.md)** — Investigates one assigned question without changing the task contract.
- **[grill-optimization](./skills/grill-optimization/SKILL.md)** — Collects one decision that only the user can make.
- **[review-optimization](./skills/review-optimization/SKILL.md)** — Independently checks whether the problem definition is ready or whether old and new results remain comparable.
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
  -> decide how candidates can be represented and searched
  -> independently approve an exact search scope
  -> choose a starting approach and budget
  -> review and authorize one exact bounded batch when required
  -> acknowledge the packet and freeze its execution baseline
  -> start and run the batch
  -> review implementations before measuring them
  -> measure under the approved comparison rules
  -> record what was learned and select the next action
  -> close the campaign with final evidence, limits, and files needed to resume later
```

The loop may stop early when evidence is sufficient, the budget or a stopping rule is reached, required permission is missing, or the approved task definition changes.

## Install

### Agent Skills installer

Use this route for Codex, Claude Code, Cursor, and other Agent Skills-compatible coding agents:

```bash
npx skills@latest add Noehub2025/noehub-factory-optimization
```

Choose all ten Skills and the coding agents where you want to install them.

### Claude Code plugin

```text
/plugin marketplace add Noehub2025/noehub-factory-optimization
/plugin install noehub-factory-optimization@noehub
```

The plugin installs all ten Skills as one managed bundle.

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
