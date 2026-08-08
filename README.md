# Noehub Factory Optimization

Reusable Agent Skills for framing optimization problems before solution work begins. The workflow turns an ambiguous objective into an evidence-backed A-H comparison contract, resolves user-owned decisions, and requires an independent readiness gate.

The workflow defines how solutions will be compared. It does not search for, implement, or claim a winning solution.

## Skills

- **[frame-optimization](./skills/frame-optimization/SKILL.md)** — The entry point and workflow coordinator. It owns the comparison contract, task state, review repair loop, epoch changes, and downstream handoff.
- **[research-optimization](./skills/research-optimization/SKILL.md)** — Investigates one bounded factual question and records labeled evidence without changing contract semantics.
- **[grill-optimization](./skills/grill-optimization/SKILL.md)** — Resolves one user-owned decision at a time when evidence cannot decide it.
- **[review-optimization](./skills/review-optimization/SKILL.md)** — Runs a fresh-context, fail-closed readiness or result-comparability review.

Start with `frame-optimization`. The other three Skills are narrow workers used by that coordinator.

## Install

### skills.sh installer

Use this route for Codex, Claude Code, Cursor, and other Agent Skills-compatible coding agents:

After this repository is published at the configured GitHub address, run:

```bash
npx skills@latest add Noehub2025/noehub-factory-optimization
```

Choose the four Skills and the coding agents where you want to install them.

### Claude Code plugin

```text
/plugin marketplace add Noehub2025/noehub-factory-optimization
/plugin install noehub-factory-optimization@noehub
```

The plugin installs the four Skills as one managed bundle.

### Manual installation

Copy or symlink every folder under `skills/` into the project-level or user-level Skill directory for the target agent:

| Agent | Project-level directory | User-level directory |
|---|---|---|
| Codex | `.agents/skills/` | `~/.agents/skills/` |
| Claude Code | `.claude/skills/` | `~/.claude/skills/` |
| Cursor | `.agents/skills/` or `.cursor/skills/` | `~/.agents/skills/` or `~/.cursor/skills/` |

Keep each complete Skill folder together. Its `SKILL.md`, references, and optional `agents/openai.yaml` file form one unit.

## Use

Ask the coding agent to use `frame-optimization` and provide a task slug or the canonical path under `docs/skills/optimization/`.

Example:

```text
Use frame-optimization to create the comparison contract for inference-cost-reduction.
```

The full readiness gate requires a fresh agent context for `review-optimization`. If the host cannot provide an independent context, the workflow stops with a review-capability blocker instead of reporting readiness.

## Workflow boundary

```text
frame-optimization
  -> research-optimization   factual evidence
  -> grill-optimization      user-owned decisions
  -> review-optimization     independent readiness or comparability gate
  -> downstream optimizer    only after PROCEED
```

The coordinator is the single owner of the A-H contract. Worker Skills return evidence, decisions, or verdicts through stable interfaces; they do not take over the shared contract.

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
