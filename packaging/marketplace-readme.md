<img src="./assets/logo.png" alt="Aka Optimization logo" width="128" height="128">

# Aka Optimization

Aka Optimization is a workflow for engineering and algorithm optimization in
Codex. It helps you define what to improve, research possible approaches,
implement changes, and measure their effects. The results guide what to try
next, while saved experiments and findings let you review earlier work and
continue from where you left off.

## What could you try?

- Investigate ways to make a program run faster without changing its results.
- Explore ways to reduce a model's inference cost while preserving the quality
  you agree to measure.
- Compare algorithm approaches under the same computing budget.

These are example goals, not measured case studies. Bring the relevant project
files and any time or spending limits. Some tasks also need information or
real-world actions that only you can provide.

## Before you start

You need a local Git project, Python 3.10 or later, PyYAML 6.x, and a host that
can provide the separate review conversations required by the workflow. Setup, a
complete optimization task, and continuation in a new conversation have been
tested in the Codex desktop app on macOS. Linux is untested and Windows is
unsupported.

The workflow plans and measures before it changes code, so even a small task can
take 15 to 30 minutes. It saves task records in your project and can create Git
commits as it works.

The package includes thirteen workflow Skills and a separate
[setup Skill](skills/setup-noehub/SKILL.md). After installing it in the host,
select your project and ask:

```text
Help me set up Aka Optimization for this project.
```

Setup checks the required tools, preserves existing project instructions, and
adds a small project guide. It does not begin experiments or install missing
dependencies automatically. The existing setup name `setup-noehub` and `.noehub/`
files are retained for compatibility.

## Start a first task

```text
Use Aka Optimization to help this program run faster without changing its results.
```

Replace the example with your own goal. The conversation helps clarify how to
compare results and what can change. You get a record of what was tried,
comparisons of the results, and a recommendation for the next step. An attempt
can reveal that an approach does not help; improvement is not guaranteed.

To continue a selected task later:

```text
Use Aka Optimization to continue the task I choose from where we left off.
```

In Codex, start each request with the `@Aka Optimization` plugin mention so the
host loads the plugin's Skills. If the host cannot find the right Skill, ask it to find and load `setup-noehub` for setup,
`frame-optimization` to clarify the goal and comparison rules, or
`frontier-optimization` to try approaches or resume a saved task. Naming a Skill
alone does not prove that its instructions were loaded.

The [runtime guide](skills/setup-noehub/references/desktop-runtime.md) explains
local dependencies, package paths, review requirements, and recovery. The
optional Codex Hook and Rust support are separate GitHub integrations; they are
not included or required by this package. The matching source for this version
is the `v1.2.0` tag of the
[public repository](https://github.com/Noehub2025/noehub-factory-optimization).

## Privacy, support, and source

Read the included [privacy policy](PRIVACY.md), [terms of service](TERMS.md),
[support page](SUPPORT.md), and [license and source guide](SOURCE.md). Files saved locally may still be read by
the host's model services or sent to external tools used for your task.

Published by **PARTNERNET SOFTWARE PTY LTD** (ACN 621 438 622), Sydney, Australia.
Developed by **Noehub**, Hangzhou Boshu Technology Co., Ltd.
Contact [support@noehub.com](mailto:support@noehub.com).

Copyright (c) 2026 Ken Chen. Licensed under the
[GNU General Public License version 3 only](LICENSE) (`GPL-3.0-only`).
Logo assets are included. The publisher's OpenAI developer verification is
complete, and a real Codex desktop test passed on macOS. This archive does not claim official
approval or demonstrated improvement on your task.
