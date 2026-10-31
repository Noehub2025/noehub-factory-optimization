# Installation

For the Codex desktop plugin, installer, and Claude Code plugin commands, start
with the [README](../README.md#get-started). This guide covers a fixed release,
manual installation, and the optional Codex Hook. The
[desktop plugin guide](./desktop-plugin.md) covers the desktop runtime, its
dependencies, and what has been tested.

## Use a specific release

Clone the public 1.2.1 release:

```sh
git clone --branch v1.2.1 --single-branch https://github.com/Noehub2025/noehub-factory-optimization.git
```

The earlier `v1.1.0` tag has thirteen Skills, no desktop setup helper, and the
MIT license.

Use this checkout as the source for the steps below. The installer and
marketplace commands in the README use the public repository; they are not
pinned by this clone command.

## Install the complete Skill folders

Copy or symlink all fourteen folders under `skills/` into the directory for
your agent. Choose project-level installation for one repository or user-level
installation for use across projects.

| Agent | Project-level directory | User-level directory |
|---|---|---|
| Codex | `.agents/skills/` | `~/.agents/skills/` |
| Claude Code | `.claude/skills/` | `~/.claude/skills/` |
| Cursor | `.agents/skills/` or `.cursor/skills/` | `~/.agents/skills/` or `~/.cursor/skills/` |

Keep every Skill folder complete, including its `SKILL.md`, references, scripts,
fixtures, and optional `agents/openai.yaml`. The entry point loads detailed
guidance as needed; copying only `SKILL.md` leaves those dependencies missing.

## Add project instructions

Deploy or merge `AGENTS.md` separately from the Skills. For Claude Code, use the
included `CLAUDE.md` import adapter where appropriate. Preserve existing project
rules and resolve conflicts explicitly.

Follow [Deploying shared agent instructions](./agent-instructions.md) for new
repositories, existing files, nested rules, and checks that the instructions
actually loaded. This also applies when Skills were installed through a plugin.

## Optional Codex Hook

The Hook supports Codex only and is not included in the Claude Code plugin.
It observes saved work context and supported agent dispatches. It does not grant
permission, deny ordinary tools, or automatically continue a session.

1. Copy `tools/workflow-harness/` into the consuming project at the same path.
2. Copy `.codex/hooks.json`. If that file already exists, merge its event entries
   instead of replacing existing Hooks. Keep one representation of this Hook
   in the project layer; do not duplicate it in `config.toml`.
3. Update the relative Skill links in `tools/workflow-harness/decision-policy.md`
   to match the installed location. For Codex project Skills, replace
   `../../skills/` with `../../.agents/skills/`.
4. With Rust 1.89 or later, build the Hook from the consuming repository root:

   ```sh
   cargo build --locked --release \
     --manifest-path tools/workflow-harness/Cargo.toml \
     --bin workflow-codex-hook
   ```

5. In Codex, inspect and approve the exact project definition with `/hooks`.
   Repository Hooks load only after the project layer is trusted.

The command resolves the Git root at runtime. Without a built binary or a valid
adopted-work pointer under `.frontier/hook-context/`, it does not add workflow
context or change a tool decision. Installing the files alone is not evidence
that the Hook is active.

See the [Codex Hook guide](../tools/workflow-harness/README.md#codex-hook) for
supported events and observation limits. The harness also has a host-neutral
execution interface; see [its setup guide](../tools/workflow-harness/README.md)
and [policy path instructions](../tools/workflow-harness/README.md#policy-references-after-installation)
if using it with another Skill layout. This release provides no Hook adapter
for other agents.
