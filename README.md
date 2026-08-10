# Noehub Factory Optimization

Reusable Agent Skills for preparing optimization work before solution search begins. The workflow first explains the system, what can change, and how that change affects the result. It then turns the task into an evidence-backed A-H comparison contract and defines R1-R8 representations, operations, modules, and safe search scope through independent gates.

The workflow defines how solutions will be compared. It does not search for, implement, or claim a winning solution.

## Skills

- **[frame-optimization](./skills/frame-optimization/SKILL.md)** — The entry point and sole workflow coordinator. It owns A-H problem semantics, R1-R8 representation semantics, lifecycle state, repair loops, and exact-scope handoffs.
- **[research-optimization](./skills/research-optimization/SKILL.md)** — Investigates one bounded A-H or R1-R8 question and writes nonnormative evidence without adopting contract changes.
- **[grill-optimization](./skills/grill-optimization/SKILL.md)** — Asks and records one user-owned decision or authorization without adopting contract changes.
- **[review-optimization](./skills/review-optimization/SKILL.md)** — Runs a fresh-context, fail-closed readiness or result-comparability review.
- **[review-representation](./skills/review-representation/SKILL.md)** — Runs a fresh-context gate for bounded whole-candidate or named modular search scope.

Start with `frame-optimization`. The other four Skills are narrow workers used by that coordinator.

## Install

### skills.sh installer

Use this route for Codex, Claude Code, Cursor, and other Agent Skills-compatible coding agents:

After this repository is published at the configured GitHub address, run:

```bash
npx skills@latest add Noehub2025/noehub-factory-optimization
```

Choose the five Skills and the coding agents where you want to install them.

### Claude Code plugin

```text
/plugin marketplace add Noehub2025/noehub-factory-optimization
/plugin install noehub-factory-optimization@noehub
```

The plugin installs the five Skills as one managed bundle.

### Manual installation

Copy or symlink every folder under `skills/` into the project-level or user-level Skill directory for the target agent:

| Agent | Project-level directory | User-level directory |
|---|---|---|
| Codex | `.agents/skills/` | `~/.agents/skills/` |
| Claude Code | `.claude/skills/` | `~/.claude/skills/` |
| Cursor | `.agents/skills/` or `.cursor/skills/` | `~/.agents/skills/` or `~/.cursor/skills/` |

Keep each complete Skill folder together. Its `SKILL.md`, references, and optional `agents/openai.yaml` file form one unit.

## Use

Ask the coding agent to use `frame-optimization` and provide a task slug or the canonical path under `docs/skills/optimization/`. The same coordinator recovers and advances both `PROBLEM.md` and `REPRESENTATION.md`.

Example:

```text
Use frame-optimization to define inference-cost-reduction and continue through representation readiness.
```

The full workflow requires fresh agent contexts for `review-optimization` and `review-representation`. If the host cannot provide an independent context, the workflow stops with a review-capability blocker instead of reporting readiness.

## Workflow boundary

```text
frame-optimization
  -> research-optimization   bounded A-H or R1-R8 evidence
  -> grill-optimization      one user decision or authorization
  -> review-optimization     parent readiness or comparability gate
  -> review-representation   exploratory or modular scope gate
  -> downstream optimizer    only within the exact permitted scope
```

The coordinator is the single owner of A-H and R1-R8 contracts. Worker Skills return evidence, decisions, or review results through stable interfaces; they do not take over the shared contract.

## Core documents

During problem framing, `PROBLEM.md` is the main document a reader or coding agent uses. During search design, `PROBLEM.md` and `REPRESENTATION.md` are used together. Their Briefs explain the task and search in familiar language. Their Contract tables state exact decisions. The Open decisions sections name unfinished choices, and the Known limits sections state what current work cannot establish.

The main documents must contain every fact needed for ordinary development, evaluation, acceptance, resource, feedback, selection, stopping, reuse, and claim decisions. Linked Slot and representation documents hold evidence, derivations, complete parameter lists, commands, and fixed implementation details. They must not hide a decision that can change the work.

Independent reviews begin with a cold read of only the Briefs. Each review record keeps a `Cold-read reconstruction` so a later reader can see whether the task and search were understandable before details were opened. A positive review created before this field existed is not a valid gate under the current workflow and must be run again. Rewriting a Brief for clarity does not change A-H status, epochs, R1-R8 status, or representation revisions when the underlying meaning is unchanged.

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
