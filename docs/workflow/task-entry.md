# Task context in current Codex

Use `scripts/workflow_task.py` to assemble checked direction, scope or design
material for the current Codex conversation. This entry composes the existing
direction adapter and current-use checks. It starts no model process by default.
The task owner selects relevant material, judges the result and records adoption.
The entry does not turn a receipt into a research conclusion or resume paused work.

## Install and connect an existing owner

Use Python 3.10 or later with PyYAML. Deploy the complete Frontier Skill bundle,
`tools/workflow-harness/` and `scripts/workflow_task.py` at those project-relative
paths. The adapter locates `skills/`, `.agents/skills/` or `.claude/skills/` relative
to its own installed package. A complete desktop plugin includes the task entry,
direction adapter and Skill bundle: invoke its script directly and always pass
the consuming project's `--root`. An isolated user-level Skill installation
does not provide those root-level helpers. Basic Skill and instruction use needs
no task script. See the [desktop runtime guide](../../skills/setup-noehub/references/desktop-runtime.md)
for a package installed outside the project.

Preserve an existing script at the destination: merge the supported entry or
choose another maintained path and update its references. Configure the existing
task owner rather than replacing the project's research record. Its metadata
can be JSON or Markdown YAML front matter. For example:

```yaml
current_state:
  campaign_status: running
execution_entry:
  configuration: docs/workflow/task-entry.json
decision_material:
  evidence:
    - {path: docs/observations.md, section: selected-cases}
  discovery:
    - {path: docs/investment.md, section: current-arrangement}
  user_scope:
    - original:
        - {path: docs/user-decision.md, section: original-exchange}
      interpretation: {path: docs/current-work.md, section: scope}
```

These are illustrative paths, not files created by the installer. Preserve the
actual pause or completion state; setting `running` requires an already adopted
task. Put this configuration at the owner's declared path:

```json
{"receiver": "current_codex"}
```

Do not include a `command` for this receiver. Link the actual task entry and
capability records from the project's active instructions. With the Codex Hook's
existing adopted-work association, `--owner` can be omitted. Otherwise supply
the existing owner explicitly. An association provides no additional authority.

## Read and recover

Run from the consuming project root with its Python interpreter:

```sh
python scripts/workflow_task.py current --root . \
  --owner docs/current-work.md --assignment docs/current-assignment.md \
  --invocation direction-1 --event direction
python scripts/workflow_task.py recover --root . --invocation direction-1
```

`direction` supplies selected decision material. `scope` also supplies original
user exchanges and the current discovery arrangement. `design` uses the actual
assignment's `research_use` references with the relevant conditions and contrary
evidence. `continuation` supports unchanged ordinary work through retained
references. The [research guide](research-basis.md) explains the optional account.

The entry checks the running owner, selected source bytes, configuration and
current use. It labels observations, adopted understanding, original user
exchanges and the owner's interpretation separately. The exact request,
prepared input and `material_ready` receipt remain under
`artifacts/workflow-harness/direction-calls/<invocation>/`. Read necessary retained
text if the host truncates its output; do not repeat the invocation to work
around truncation. A receipt establishes local preparation, not model acceptance.

Recovery checks the original record without substituting newer evidence or
repeating an operation. Changed input requires owner reconciliation before a
fresh reading. Paused or completed work allows historical inspection while
preventing a new reading presented as active work. Retain uncertain effects and
native call identities before any fresh dispatch. Record the actual adopted
judgment in the existing task or result record.

## Other receivers and limits

An explicitly configured `subprocess` receiver can use `run` with an argument
array in `command`, an optional `timeout_seconds` and `max_output_bytes`. That
path expects the completed Codex JSON-line event stream when receiving an
answer, and uses the [direction adapter](../../tools/workflow-harness/adapters/README.md#direction-and-scope-delivery).
It requires authority for that actual consumer and disclosure. It is separate
from the default current-conversation path and does not sandbox descendants.

This entry does not intercept native agent dispatch, arbitrary shell commands,
unassociated returns or external-service adapters. Full server-side context,
authenticated native model returns and sound research judgment are outside its
mechanical guarantee. Original user quotations are evidence copies, not permission
tokens. Full source-carrier changes can require reconciliation after an unrelated
edit, without invalidating historical scientific evidence.

Local verification covers task input, research views, source checks, installed
repository layouts and recovery:

```sh
python -m pytest -q tests/test_workflow_task.py \
  tests/test_workflow_research_basis.py \
  tools/workflow-harness/tests/test_direction_owner.py
```

These tests use bounded fixtures. Receiving-project adoption and research benefit
need evidence from that project's actual work; no recurring reviewer is added.
