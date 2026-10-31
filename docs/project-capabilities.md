# Managing reusable project capabilities

## Purpose

Some needs are predictable before implementation begins. Evaluation, packaging, submission, storage, recovery, and service adapters often recur across several parts of one optimization project. Planning them early can make execution more stable without turning the project into a platform effort.

Use the project's existing architecture, development, or agent-instruction document as the authoritative capability record. Add a dedicated file only when that makes the information easier to find. Do not create a second catalog that can disagree with an established project source.

## When to plan a capability

Review common needs at project planning, after a material scope change, and before constructing the first dependent execution path. Record a need when the objective and expected work make it concrete. A second consumer, duplicate implementation, or production incident is not required.

For each need, choose one disposition:

- reuse a supported project or external capability;
- construct or extend a maintained capability;
- investigate an unresolved interface or compatibility question;
- use a bounded project-specific path; or
- defer the need with a concrete reason and natural reconsideration point.

This review is part of ordinary planning. It must not become a preliminary platform stage that blocks unrelated research.

## Minimum record

Keep the record short and project-specific:

| Field | Meaning |
|---|---|
| Capability | The common need it serves. |
| Supported entry | The public command, function, protocol, or document that consumers use. |
| Scope and limits | Uses the current implementation supports and important known gaps. |
| Defaults | Version, configuration, or retained support identity selected for ordinary use. |
| Owner | The existing technical owner responsible for the implementation and affected consumers. |
| Checks | Focused commands that exercise the actual entry and receiving seam. |
| Next decision | The use or condition that reopens a deferral, exception, upgrade, or replacement. |

Keep interface details beside the implementation. Keep important tradeoffs and deferrals in the existing plan or design that owns them. A wrapper, checksum, moved file, or earlier successful run does not by itself establish maintained support.

## Relationship to Workflow records

Capability management and optimization execution have different jobs:

- the capability record identifies the maintained entry, supported scope, defaults, and checks;
- Git and retained content identify the implementation and assets actually consumed;
- a Batch selects the capability version and configuration for its current work;
- an Attempt records a measurement or protected effect when repetition and consequence matter;
- result adoption decides what the observation supports.

Freezing a capability version grants no permission to spend, submit externally, access sensitive data, or make an irreversible change. Likewise, changing a support module does not automatically create a new candidate. Classify the change by its actual role in the consuming path.

An evaluation engine can be maintained as a reusable capability while the project still owns its comparator, metric, sampling, and claim limits. A package builder can standardize structure and integrity without deciding what is eligible for release. A submission adapter can maintain transport, idempotency, and recovery while each real submission remains bound to its exact artifact, permission, budget, and provider reference.

## Existing `AGENTS.md` and Claude Code repositories

When the consuming repository already has `AGENTS.md`, preserve its project-specific capability list, build rules, and authority boundaries. Merge the shared `Common project capabilities` behavior once and point it to the existing authoritative document. Do not replace the file or add a competing list.

Claude Code can receive the same shared behavior through direct `AGENTS.md` support or the checked-in `CLAUDE.md` import described in [Deploying shared agent instructions](./agent-instructions.md). Keep project capability facts in `AGENTS.md` or its linked project document. Keep Claude-specific additions in `CLAUDE.md`.

The Codex Hook remains separate. It observes supported Codex events and does not make a capability maintained, grant authority, or provide a Claude Code Hook adapter.

## Professional references at the execution entry

Link the project's existing capability and professional-reference records from
its `AGENTS.md`. The preparation helper can then include their descriptions
independently of the proposed implementation's citations. The record helps the
owner find applicable knowledge; it does not certify that every need is covered.
Retrieve the selected method's actual content before relying on it.

The optional [Codex owner adapter](../tools/workflow-harness/adapters/README.md)
connects that preparation to an actual response, adopted choices, and the
configuration consumed by a maintained operation. Existing valid grounds remain
reusable. The adapter does not install Skills, select a project's model, change
measurement meaning, or grant authority for external effects. Local tests check
the connected path; scientific adequacy and receiving-project outcomes require
their own applicable evidence.

## Project-owned affected checks

Projects can connect their shared modules and deployment files to the workflow check selector with `tools/project-checks.json`:

```json
{
  "schema": "project-checks/1",
  "rules": [
    {
      "name": "evaluation capability",
      "paths": [
        "AGENTS.md",
        "docs/development/capabilities.md",
        "src/evaluation/**",
        "tests/test_evaluation.py"
      ],
      "commands": [
        ["{python}", "-m", "pytest", "-q", "tests/test_evaluation.py"]
      ]
    },
    {
      "name": "submission adapter",
      "paths": ["src/submission/**", "tests/test_submission.py"],
      "commands": [
        ["{python}", "-m", "pytest", "-q", "tests/test_submission.py"]
      ]
    }
  ]
}
```

Run:

```sh
python skills/frontier-optimization/scripts/run_workflow_checks.py \
  --mode affected \
  --project-checks tools/project-checks.json
```

Use argument arrays, not shell strings. `{python}` resolves to the interpreter running the selector. The file is executable repository configuration and should be reviewed like other build configuration. A missing explicitly requested map or a malformed map fails instead of silently skipping project checks.

Use repeated `--path` arguments only for an intentionally scoped dirty-worktree check, and report that scope. Release checks still run the current Workflow suite and the project commands selected by the changed paths.

## Task context, research and selected effects

The repository maintainer owns the portable adapters; each consuming project
selects its actual owner, receiver and effect scope. See the
[task entry](workflow/task-entry.md), [research account](workflow/research-basis.md)
and [adapter guide](../tools/workflow-harness/adapters/README.md).

| Entry | Dependencies and important defaults | Checks and limits |
|---|---|---|
| `scripts/workflow_task.py current` / `recover` | Python 3.10+, PyYAML, POSIX file locking, complete copied layout or desktop package; required consuming `--root`, explicit owner or existing Codex work association; receiver `current_codex` has no command | `tests/test_workflow_task.py`, `tests/test_workflow_research_basis.py`, `tests/test_desktop_plugin.py`; no native dispatch interception or authenticated native model return |
| `scripts/noehub_setup.py` | Python 3.10+, Git and the complete package; defaults to a read-only plan; `--apply` adds project guidance after checking dependencies | `tests/test_desktop_plugin.py`; preserves existing instruction bytes and edited managed files, but cannot certify semantic agreement or host discovery |
| `scripts/build_distribution.py` | Python 3.10+, Git and `packaging/distributions.json`; explicit profile and new output path; stable ZIP metadata | `tests/test_desktop_plugin.py`; market profile excludes Hooks, GitHub profile retains them; build success is not marketplace approval |
| `frontier_references.py` research operations | Existing owner and sufficient prose or an optional adopted structured account | `test_research_basis.py`, `test_frontier_references.py`; publication and selected views do not establish complete research or semantic adoption |
| `direction_owner.py` | Python, PyYAML and POSIX processes; explicit stdin consumer; 300-second timeout and 2,000,000-byte output allowance by default | `test_direction_owner.py`; no sandbox or automatic replay of an uncertain call |
| `protected_http.py` | Python, local complete Skills and an owner-selected scope; one request, no redirects or retries | `test_protected_http.py`, `test_protected_effect.py`; only cooperative connected senders, with bounded withdrawal timing |
| `managed_correction.py` | Python, PyYAML and a built Rust managed host; release binary preferred, debug fallback | `test_managed_correction.py`, Rust managed tests; source publication and Session activation are separate operations |

Reconsider these arrangements when the consuming host, selected sources, actual
configuration, effect scope or receiving path changes. Ordinary unchanged use
can reuse applicable evidence. Passing local tests establishes neither live
adoption nor better optimization outcomes. The Hook remains Codex-only.
