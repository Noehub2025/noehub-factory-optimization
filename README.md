# Noehub Factory Optimization

Reusable Agent Skills for two connected stages of optimization work. The framing stage explains the task, fixes how options will be compared, and approves an exact search scope. The Frontier stage turns that approved scope into a budgeted campaign of research, design, implementation, evaluation, learning, closeout, and recovery.

The workflow keeps user decisions, spending authority, engineering checks, performance evidence, and external claims separate. It does not treat a completed implementation or passing test as proof that a candidate is better.

## Skills

### Frame the task and search space

- **[frame-optimization](./skills/frame-optimization/SKILL.md)** — The entry point and sole workflow coordinator. It owns A-H problem semantics, R1-R8 representation semantics, lifecycle state, repair loops, and exact-scope handoffs.
- **[research-optimization](./skills/research-optimization/SKILL.md)** — Investigates one bounded A-H or R1-R8 question and writes nonnormative evidence without adopting contract changes.
- **[grill-optimization](./skills/grill-optimization/SKILL.md)** — Asks and records one user-owned decision or authorization without adopting contract changes.
- **[review-optimization](./skills/review-optimization/SKILL.md)** — Runs a fresh-context, fail-closed readiness or result-comparability review.
- **[review-representation](./skills/review-representation/SKILL.md)** — Runs a fresh-context gate for bounded whole-candidate or named modular search scope.

Start with `frame-optimization`. The other four Skills are narrow workers used by that coordinator.

### Run a Frontier campaign

- **[frontier-optimization](./skills/frontier-optimization/SKILL.md)** — The only Frontier coordinator. It opens or resumes a campaign from an approved representation, controls plans and budget, adopts worker results, closes work, and packages durable recovery state.
- **[research-frontier](./skills/research-frontier/SKILL.md)** — Researches one assigned route landscape or evidence question without changing campaign state.
- **[grill-frontier](./skills/grill-frontier/SKILL.md)** — Collects one user-owned tradeoff or authorization for an exact reviewed choice.
- **[run-frontier-batch](./skills/run-frontier-batch/SKILL.md)** — Executes one fully specified batch after its inputs, authority, paths, budget, and stopping conditions are fixed.
- **[review-frontier](./skills/review-frontier/SKILL.md)** — Independently reviews one frozen campaign plan, replan, technical design, candidate implementation, recovery reuse, or claim set.

Start Frontier work only after `frame-optimization` has produced a positive representation review and exact permitted scope. Invoke `frontier-optimization` explicitly; it delegates the other four Frontier Skills as narrow workers.

## Install

### skills.sh installer

Use this route for Codex, Claude Code, Cursor, and other Agent Skills-compatible coding agents:

After this repository is published at the configured GitHub address, run:

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

Keep each complete Skill folder together. Its `SKILL.md`, references, and optional `agents/openai.yaml` file form one unit.

## Use

Ask the coding agent to use `frame-optimization` and provide a task slug or the canonical path under `docs/skills/optimization/`. That coordinator recovers and advances both `PROBLEM.md` and `REPRESENTATION.md`.

Example:

```text
Use frame-optimization to define inference-cost-reduction and continue through representation readiness.
```

After representation readiness, explicitly start the Frontier campaign for the same task:

```text
Use frontier-optimization to start the Frontier campaign for docs/skills/optimization/inference-cost-reduction/.
```

The full workflow requires fresh agent contexts for `review-optimization`, `review-representation`, and `review-frontier`. If the host cannot provide an independent context, the affected stage stops instead of reporting readiness.

## Workflow boundary

```text
frame-optimization
  -> research-optimization   bounded A-H or R1-R8 evidence
  -> grill-optimization      one user decision or authorization
  -> review-optimization     parent readiness or comparability gate
  -> review-representation   exploratory or modular scope gate
  -> frontier-optimization   budgeted campaign within the exact permitted scope
       -> research-frontier  one route landscape or evidence question
       -> grill-frontier     one user tradeoff or authorization
       -> run-frontier-batch one exact research, design, code, or evaluation batch
       -> review-frontier    one frozen plan, design, implementation, or claim review
       -> closeout           final accounting, retained results, limits, and handoff
```

The framing coordinator is the single owner of A-H and R1-R8 contracts. The Frontier coordinator is the single owner of campaign plans, budget, selections, accepted results, and closeout. Worker Skills return evidence, decisions, execution results, or reviews through fixed interfaces; they do not take over either coordinator's records.

## Core documents

During problem framing, `PROBLEM.md` is the main document a reader or coding agent uses. During search design, `PROBLEM.md` and `REPRESENTATION.md` are used together. Their Briefs explain the task and search in familiar language. Their Contract tables state exact decisions. The Open decisions sections name unfinished choices, and the Known limits sections state what current work cannot establish.

The main documents must contain every fact needed for ordinary development, evaluation, acceptance, resource, feedback, selection, stopping, reuse, and claim decisions. Linked Slot and representation documents hold evidence, derivations, complete parameter lists, commands, and fixed implementation details. They must not hide a decision that can change the work.

Independent reviews begin with a cold read of only the Briefs. Each review record keeps a `Cold-read reconstruction` so a later reader can see whether the task and search were understandable before details were opened. A positive review created before this field existed is not a valid gate under the current workflow and must be run again. Rewriting a Brief for clarity does not change A-H status, epochs, R1-R8 status, or representation revisions when the underlying meaning is unchanged.

After a positive representation handoff, `FRONTIER.md` becomes the readable campaign overview. It states the approved scope, current baseline, remaining budget, next work, first performance check, stopping rules, and claim limits. `frontier/ledger.md` records routes, user decisions, batch plans, evaluated results, learning, selection, and budget; `frontier/bounds.md`, `frontier/claims.md`, `frontier/reviews/`, and `frontier/work/` hold the supporting evidence and fixed work details. The coordinator recovers campaign state from these files and their recorded identities, not from conversation history.

## Layout

```text
skills/<skill-name>/
  SKILL.md
  references/          optional detailed guidance
  agents/openai.yaml   optional Codex display metadata
.claude-plugin/
  plugin.json
  marketplace.json
```

## License

MIT
