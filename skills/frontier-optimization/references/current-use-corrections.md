# Applying a known correction to current work

Read only when an existing owner has established a finding that affects a saved task or dependency. [Finding effects](finding-effects.md) owns the consequence judgment. This interface checks record continuity and actual saved objects; it does not judge research value or prove that rewritten prose is correct. Ordinary tasks need no correction block.

## Existing owner record

Keep a conditional `current_use_corrections` list in the existing owner JSON, YAML or Markdown frontmatter. Paths are relative to the repository. Preserve the finding as evidence; a changed judgment needs its existing owner, not a new review stage.

```yaml
current_use_corrections:
  - id: discovery-admission
    finding: work/findings/discovery-admission.md
    effect: repair
    affected_sources:
      - work/research-task.md
    status: open
```

Effects are `block`, `repair`, or `advisory`, adopted under the existing finding rules. An advisory does not hold work. A confirmed restriction's identity, effect and affected scope cannot be silently relabeled after enrollment. An `open` blocking/repair finding holds only uses of its affected objects. Research needed to correct it and unrelated work remain available.

The resolver preparation and adopted-work registration read this live block and retain a conditional owner receipt in the existing `.frontier/hook-context` area. This needs no commit, native session or new general registry. Resolver preparation supplies an open finding to its owner but will not reuse a saved decision over it. Binding checks that the prepared association has not changed; binding alone is not execution permission.

Before affected direct work or dispatch, run:

```sh
python .agents/skills/frontier-optimization/scripts/frontier_references.py check-current-use \
  --repo . --owner-source path/to/existing-owner.md \
  --source work/research-task.md
```

Repeat `--source` for the actual saved objects used by the action. A failed check returns `NOT_READY` and exit code 2. Correct its affected use in place; do not stop unrelated work. Do not supply unrelated source names to obtain a passing result for another action. Source choice and actual outgoing instructions remain the existing owner's responsibility.

## Discharge and transfer

After enrollment, save and adopt the corrected task. Change its status to `resolved` and include an owner reason, an existing adoption/evidence path, and `resolution.replacements`, a list of each affected `path` and the SHA-256 of its actual saved bytes. Use `inapplicable` only when evidence establishes that the finding no longer applies. A bare status or nonempty explanation cannot clear the check. `resolved` requires a real change from the superseded objects. No hash proves semantic correction.

```yaml
status: resolved
resolution:
  reason: The adopted task now permits discovery before a replacement design exists.
  evidence: work/adoption.md
  replacements:
    - path: work/research-task.md
      sha256: <actual saved file SHA-256>
```

Unresolved associations survive omitted fields and context refresh. Within one registered root, adopting another owner carries the previous associations and scopes them to the new actual work, including after a file rename. Outside that registration path, an explicit transfer places `current_use_predecessor: path/to/previous-owner.md` on the successor before adoption; the retained receipt remains usable if the old file was renamed. The predecessor's evidence identity must agree; its older status does not overwrite the successor's valid discharge.

Discharged records remain as references, not permanent freezes on later development. Clearing their display fields does not reopen a finding. Exact replay of a superseded object can still be detected. New semantic regressions need owner judgment. A previously unregistered owner rename with no predecessor reference is outside automatic continuity coverage; do not present it as a verified transfer.

## Participating consumption and limits

The successful helper return contains `current_use`: absolute owner, retained `correction_ids`, scoped `blocked_ids`, and `files` with absolute `path` and exact `contents`. It includes the saved owner, retained receipt, relevant evidence and actual requested objects. Current owner edits require refreshing this snapshot without another investment judgment; arbitrary unrelated repository edits do not invalidate it. Historical comparison evidence stays tied to its original Git revision.

A cooperating `workflow-harness` Session can import this object through `adopt_current_use`. Its Worker preparation and consumption checks preserve the association, saved bytes and queued request identity. The owner checker must supply the validated object; caller-invented empty `blocked_ids` is not validation. `replace_queued_work` applies only to an unstarted request. External dispatchers must use `verify_queued_current_use` with the actual request they will issue. Do not interrupt or replay an already-started operation to refresh a snapshot.

The existing host CLI exposes these same operations as `host current-use-adopt RUN_DIRECTORY OWNER_REPORT.json`, `host current-use-replace RUN_DIRECTORY CORRECTED_ASSIGNMENT.txt`, and `host current-use-check RUN_DIRECTORY ACTUAL_REQUEST.json`. Adoption consumes the owner checker's report, replacement emits a fresh request, and consumption checks that exact request before external dispatch. These commands do not infer semantic validity from a manually constructed report.

The default native Hook remains advisory and does not auto-import this attachment or intercept all worker actions. Direct and unsupported paths use the owner check above and inspect the actual outgoing task. A corrected follow-up explicitly supersedes the old restriction; inspect the next substantive action or return. Report unobserved stages honestly. Do not infer automatic enforcement from registration, source hashes, passing helper output or a sent message.
