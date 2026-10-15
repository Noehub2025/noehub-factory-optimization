# Noehub Factory Optimization

**An optimization research workflow for coding agents.**

Define what better means, test promising ideas, and use the results to choose
the next improvement. Goals, evaluation rules, budgets, and decisions stay in
your repository so another session can pick up the work.

Use it to reduce inference cost or latency, improve a model or game-playing
agent, tune a configuration, or explore alternative implementations. It is
especially useful when passing tests alone cannot tell you whether a change
is better.

[Get started](#get-started) · [How it works](#how-it-works) ·
[Documentation](#documentation) · [Release 1.1.0](./CHANGELOG.md)

## How it works

The workflow aims for the best attainable result. It encourages ambitious
hypotheses, compares alternative approaches, and chooses tests that can resolve
the uncertainty that matters most to the next decision.

```text
Define the goal and comparison rules
  → Decide what can be changed and searched
  → Research, implement, and measure promising approaches
  → Use the evidence to improve, change direction, or stop
```

Two coordinator Skills manage this process. They assign specialist Skills for
research, design, implementation, review, and questions that need your judgment.

| Coordinator | Responsibility | Main project files |
|---|---|---|
| [frame-optimization](./skills/frame-optimization/SKILL.md) | Define the objective, measurement rules, and allowed search space; obtain the required independent review. | `PROBLEM.md`, `REPRESENTATION.md` |
| [frontier-optimization](./skills/frontier-optimization/SKILL.md) | Run the improvement campaign within the agreed limits, learn from results, and preserve the context needed to resume. | `FRONTIER.md`, `frontier/` |

This is Recursive Self-Improvement (RSI): evidence from one cycle informs the
next. Where the task permits it, that can also improve the search strategy,
evaluator, or tools. Changes to comparison rules remain explicit so results
from incompatible evaluations are not treated as comparable.

## Get started

Use a Git repository for your project. Retain the commits and artifacts used
for reviews, results, and recovery; a remote repository is optional.

### 1. Install the Skills

Choose one installation method. **Install all thirteen Skills together**, even
though you normally invoke only the two coordinators.

**Codex and other Agent Skills-compatible agents**

```sh
npx skills@latest add Noehub2025/noehub-factory-optimization
```

Select all thirteen Skills and your target agent in the installer.

**Claude Code plugin**

Run these commands inside Claude Code:

```text
/plugin marketplace add Noehub2025/noehub-factory-optimization
/plugin install noehub-factory-optimization@noehub
```

The plugin installs all thirteen Skills as one bundle. For a version-pinned
checkout or manual installation, see the [installation guide](./docs/installation.md).

### 2. Add the project instructions

Copy [`AGENTS.md`](./AGENTS.md) into your project root. If one already exists,
merge the three shared sections while preserving the project's existing rules.

For Claude Code, the included [`CLAUDE.md`](./CLAUDE.md) imports those instructions
with `@AGENTS.md`. Add that import once to an existing root `CLAUDE.md`, or copy
the adapter if the project has none. Skills installation and plugin installation
do not replace this step.

See [shared instruction setup](./docs/agent-instructions.md) for existing files,
nested instructions, direct Claude Code support, and verification. Start a new
agent session after setup and confirm that the project instructions are loaded.

### 3. Start a task

Describe your objective and ask for both stages. For example:

```text
I want to reduce inference cost while preserving the quality we agree to measure.
Use frame-optimization to define and review inference-cost-reduction,
then continue with frontier-optimization within the adopted objective,
budget, access, and effect limits.
```

The agent saves the task under
`docs/skills/optimization/inference-cost-reduction/`. Later sessions can resume
from that directory and its referenced history and artifacts.

To define and review the task first, request only `frame-optimization`. To start
the campaign after framing is ready:

```text
Use frontier-optimization to start the campaign for
docs/skills/optimization/inference-cost-reduction/.
```

## What to expect

- **Comparable results.** The task states what may change, how it is measured,
  and which conclusions the evidence supports.
- **Learning across experiments.** Failed ideas, useful alternatives, and reasons
  for changing direction remain available to later work.
- **Work within your limits.** The agent reuses applicable decisions and asks
  when a consequential action needs authorization you have not already given.
- **Recoverable progress.** Project files retain the current question, next
  observation, resource use, and conditions for continuing or stopping.

The repository provides a research workflow, not a domain-specific optimizer.
Successful installation and passing checks do not establish that it will improve
your target system; that needs evidence from your task.

## Optional Codex Hook

The Skills and project instructions are the starting point. An optional
[Rust execution harness](./tools/workflow-harness/README.md) supports controlled
execution and recovery. Its [Codex Hook](./.codex/hooks.json) restores saved work
context and observes supported agent dispatches.

**The Hook supports Codex only.** It is separate from the Claude Code plugin,
grants no permission, and does not automatically continue a session. Setup
requires building the binary and trusting the project Hook definition; see
[Hook installation](./docs/installation.md#optional-codex-hook).

## Documentation

| If you want to… | Read |
|---|---|
| Install a specific version or copy Skills manually | [Installation guide](./docs/installation.md) |
| Merge instructions into an existing project | [Shared agent instructions](./docs/agent-instructions.md) |
| Browse all thirteen Skills and understand the detailed rules | [Workflow reference](./docs/workflow-reference.md) |
| Maintain shared evaluation, packaging, or submission tools | [Reusable project capabilities](./docs/project-capabilities.md) |
| Configure execution, recovery, or the Codex Hook | [Harness guide](./tools/workflow-harness/README.md) |
| Check release changes or publish a release | [Changelog](./CHANGELOG.md) · [Release procedure](./docs/releasing.md) |

The public release is **1.1.0**. Public and development versions use separate
version series.

## License

[MIT](./LICENSE)
