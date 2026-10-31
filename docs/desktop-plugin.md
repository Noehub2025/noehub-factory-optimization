# Aka Optimization desktop packaging and setup

The desktop Skills package and complete GitHub archive come from the same
source. `packaging/distributions.json` is their explicit file allowlist. Add a
new runtime dependency there when changing the bundle; arbitrary untracked
files are never added by directory scanning.

Both profiles include the [privacy policy](../PRIVACY.md),
[support information](../SUPPORT.md), [license](../LICENSE), and
[source identification guide](../SOURCE.md). The complete GitHub profile also
includes the [listing materials](marketplace-listing.md). Existing package names,
setup identifiers, and generated project markers retain `noehub` for compatibility.

The market package contains thirteen workflow Skills, `setup-noehub`, their
complete resources, the Python current-conversation entry and its direction
adapter. It excludes lifecycle Hook definitions and Rust execution hosts.
The GitHub package retains the optional Codex-only Hook and source needed to
build it. Neither the portable manifest nor the Claude manifest enables Hooks.

This follows OpenAI's [packaging guide](https://developers.openai.com/plugins/build/plugins),
[desktop-only declaration](https://developers.openai.com/plugins/deploy/desktop-only),
and [Hook submission restriction](https://developers.openai.com/plugins/build/plugins#bundled-mcp-servers-and-lifecycle-hooks).

## Build the two archives

From this repository, using Python 3.10 or later:

```sh
python scripts/build_distribution.py --profile marketplace --output dist/noehub-marketplace.zip
python scripts/build_distribution.py --profile github --output dist/noehub-github.zip
```

Use a new output filename for each candidate; the builder never overwrites an
existing archive. ZIP entry ordering, timestamps and permission modes are
stable. `distribution.json` records the profile, version, source commit and
hashes of the packaged files. Working changes are included only at allowlisted
paths, so the commit alone is not a statement of archive identity. Compare the
archive digest when identifying the candidate actually tested.

`plugin.json` and the Claude manifests share the version of their repository.
Development and public releases still use separate version series. This work
does not assign a new public version or publish a release.

## Project setup

Run the host-discovered `setup-noehub` Skill. Its
[runtime guide](../skills/setup-noehub/references/desktop-runtime.md) owns the
deployment behavior and command examples. The stdlib-only setup planner can
diagnose a missing PyYAML installation. It changes nothing without `--apply`.

The helper modifies only the effective root instruction file, by adding one
marked link, and `.noehub/workflow.md` plus `.noehub/setup.json`. A nonempty root
`AGENTS.override.md` takes precedence over `AGENTS.md`. Existing shared workflow
sections stay project-owned; the Skill compares their meaning before declaring
setup complete. Nested instructions and Claude-specific rules are preserved.

Repeated setup with the same inputs is a no-op. Updates replace only unchanged
managed guidance. Edited or conflicting files require reconciliation. Project
records contain no absolute plugin cache paths. Setup does not install a Hook,
copy Skills, create a running campaign, configure a model, or grant permissions.
To disconnect, remove the marked Noehub link and the two generated files after
preserving any user edits. Keep task evidence and existing instruction content.

## Runtime and local discovery

Plugin resources stay in the installation directory. The current-conversation
entry requires an explicit `--root` for the consuming project, loads helpers
from its own package, and saves context in the project. It works with explicit
owners without a Hook. The existing copied-project layouts remain supported.

The repository includes `.agents/plugins/marketplace.json` for local discovery.
It points to this checkout, not the built ZIP. Use the host's supported local
marketplace installation flow to test discovery; registering this file alone
does not prove the plugin is installed. For an extracted market archive, create
a local marketplace entry pointing to that archive's directory. See the
[official local marketplace guide](https://developers.openai.com/plugins/build/plugins#build-your-own-curated-plugin-list).

## Verification boundary

Run the packaging and receiving checks:

```sh
python -m pytest -q tests/test_desktop_plugin.py tests/test_workflow_task.py
```

They cover archive contents, separate package/project paths, instruction
preservation, repeated setup, source conflicts and explicit context recovery.
They do not claim a live desktop installation, a complete optimization cycle,
independent host review, or approval for the public directory.

| Environment or behavior | Current evidence and limits |
|---|---|
| macOS helper scripts and packaging | Local automated checks cover package contents, project preservation, and checked recovery. |
| Codex desktop installation and first task | Passed on 2026-10-31 in the Codex desktop app (ChatGPT app 26.1027.30824, codex-cli 0.166.0-alpha.5.1, macOS 26.5 arm64) with the exact market archive. The three starter prompts, each prefixed with the `@Aka Optimization` plugin mention, loaded `setup-noehub`, then `frame-optimization` and `frontier-optimization`. Separate review conversations ran for measurement, research, readiness, representation, direction and implementation review. A deliberately slow prime counter became about 28x faster on an independent re-measurement (457 ms to 16.5 ms median), with identical results for all limits from -5 to 3000. A new conversation recovered the completed task. The optimization took about 20 minutes and created Git commits in the test project. The prompts without the plugin mention were not tested. |
| Linux helper scripts | Intended by the current runtime design; no actual Linux validation is recorded. |
| Windows helper scripts | Unsupported by the current runtime, which depends on Portable Operating System Interface (POSIX) file locking. |
| Claude Code and other hosts | Existing instruction and installation guidance is retained; it does not establish equivalent desktop plugin behavior or review capabilities. |

The current preparation supplies text listing materials, logo assets,
privacy/support/terms pages, and source/license guidance. The publisher's
OpenAI developer verification is complete, and one real desktop cycle passed on
macOS. Submission remains unfinished. One test task does not establish results
on other projects or hosts.
Automated checks do not demonstrate usability or better optimization outcomes.
