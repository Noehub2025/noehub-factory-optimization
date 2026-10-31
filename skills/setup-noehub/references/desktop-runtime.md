# Desktop runtime

The plugin directory owns executable code, Skills and reference material. The
selected Git repository owns project instructions, task documents, experiment
outputs, and recovery records. Keep these locations separate, even when the
plugin is inside a host cache or installed for several projects.

## Locate and prepare the runtime

Discover the installed `setup-noehub` Skill through the host and read its
host-supplied file. Its package root is two directories above `SKILL.md`.
Resolve sibling Skills from the same installed bundle. Do not search unrelated
user folders, depend on a cached absolute path from a previous installation,
or silently use a different installed version.

The first runtime targets macOS and Linux (POSIX file locking); Windows runtime
support is not claimed. Use Python 3.10+ with PyYAML 6.x and Git. The setup planner reports availability
using its own interpreter. Core script use needs no Rust build, credentials,
MCP server, separate model process, or Codex Hook. Optional GitHub adapters have
their own dependencies and are not activated by installing the market package.

Prefer a suitable existing project environment. If dependencies are missing,
use a project-local virtual environment after arranging the required package
installation within the user's existing authorization:

```sh
python3 -m venv /absolute/project/.venv-noehub
/absolute/project/.venv-noehub/bin/python -m pip install -r /absolute/plugin/root/requirements-runtime.txt
```

Do not install into the plugin cache or global Python. Exclude a newly created environment
from the project's version control using its existing ignore arrangements.
Setup itself neither creates this environment nor accesses the network.

## Start and resume work

The two coordinators retain the complete research workflow. Load the selected
Skill from host discovery, then use its package-relative references. Commands
shown in older examples as `.agents/skills/<name>/...` refer to the installed
Skill's actual path; do not create a second installation just to match them.
Pass the selected project's absolute path as each script's `--repo`, `--root`,
or corresponding documented project argument. Run project commands with that
project as their working directory. Runtime files must never become scientific
project inputs merely because they share a filesystem.

`run_workflow_checks.py` is a maintainer check selector for a source checkout.
Do not run it against a consuming project as if the plugin's tests were that
project's evaluator. Use the project's maintained tests and adopted measurement
protocol for its experiments; the plugin's own tests additionally need pytest.

Task state remains under `docs/skills/optimization/<task-slug>/`. On recovery,
read the selected task's `PROBLEM.md`, `REPRESENTATION.md`, `FRONTIER.md` and
linked current records as required by the coordinator. Reuse adopted limits;
do not restart paused work or replay uncertain effects.

## Optional checked current-conversation input

The market package includes `scripts/workflow_task.py` and its Python adapter.
Invoke the packaged entry directly; no local copy or Hook is needed. When an
existing owner already uses this entry, its metadata names a configuration:

```yaml
execution_entry:
  configuration: docs/workflow/task-entry.json
```

That configuration contains `{"receiver": "current_codex"}` without `command`.
Preserve the existing owner's actual status, sources and assignment. Do not
create a running status to make a check pass. The owner prepares decision
material under the [existing interface](../../frontier-optimization/references/worker-interfaces.md#reuse-understanding-and-deliver-the-actual-input).
Use the owner's real paths, not the illustrative paths below:

```sh
python /absolute/plugin/root/scripts/workflow_task.py current --root /absolute/project \
  --owner docs/current-work.md --assignment docs/current-assignment.md \
  --invocation direction-1 --event direction
python /absolute/plugin/root/scripts/workflow_task.py recover --root /absolute/project \
  --invocation direction-1
```

Without a Hook, always supply `--owner` for a new reading. The invocation
identifier locates one saved call; select a new identifier for genuinely new
work, not to repeat an uncertain effect. The exact input and receipt remain in
the project at `artifacts/workflow-harness/direction-calls/<invocation>/`.
Recovery does not launch another model or replay work. Changed sources require
owner reconciliation; a receipt is not an accepted research result.

## Host capabilities and updates

Use the host's actual tools for delegation and necessary independent reviews.
Discover and load the assigned Skill in the worker's context. Preserve the
fresh-context and independence requirements of that judgment. If the host lacks
the necessary mechanism, name the affected review and continue only independent
work; do not substitute self-review or install an external model runner.

After a plugin update or relocation, rediscover its current path and re-run
setup for the selected project. The setup record contains version and content
digests, not machine-specific cache paths. A package update does not invalidate
unchanged scientific results or automatically resume work. Edited project
guidance stays user-owned until its changes are reconciled.

The [GitHub distribution](https://github.com/Noehub2025/noehub-factory-optimization)
provides the optional Codex-only Hook. Install it separately only when requested;
market installation does not enable it or claim native dispatch enforcement.
