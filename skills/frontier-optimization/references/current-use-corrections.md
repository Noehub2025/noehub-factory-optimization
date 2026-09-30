# Applying a known correction to current work

Use the source view at consequential adoption or existing recovery; use the correction operation only when an owner establishes a finding affecting saved work. [Finding effects](finding-effects.md) owns the consequence judgment. The helpers preserve source context, record continuity and actual saved objects; they do not judge research value or certify rewritten prose. Ordinary tasks need no correction block.

## Adoption and recovery source view

Before adopting a consequential result, read the controlling objective, incoming task, returned reasons and switches, and intended outgoing task together:

```sh
python .agents/skills/frontier-optimization/scripts/frontier_references.py prepare-adoption \
  --repo . --owner-source path/to/owner.md --assignment path/to/input.json \
  --result path/to/result.json --source path/to/outgoing-task.md
```

At recovery with no new result, use `recover-work --repo . --owner-source path/to/owner.md --source path/to/task.md`. Omit `--source` when the owner's selected work supplies it. Reuse already-applicable context rather than rebuilding an unchanged comparison on each edit. Both operations present sources without publishing a Selection, finding or semantic verdict. Resolver preparation and binding also include this view; `adopt-work` returns it alongside the saved adoption operation.

Frontier retains its controlling Problem separately from owner-selected excerpts. A generic task may supply `--controlling-source path/to/goal.md#section` when a broader objective applies. Inspect the actual selector and relevant full source, not just its role label: a historical section or subordinate task cannot silently replace the controlling request. No parent is invented for a standalone task. Incoming completion restrictions matter even when omitted from the returned reasons. The existing owner corrects a consequential scope discrepancy under [Current-use correction](worker-interfaces.md#current-use-correction); the helper cannot establish authority from a link or hash.

Sources share a catalog rather than repeating full bodies at each role. Known Frontier owner metadata and automatically selected Batch records use explicit current-work presentations; omitted history retains original locations and hashes for retrieval. Complete controlling goals, incoming assignments, decisions and explicit task sources remain available. Read omitted history when it bears on the current question; the presentation does not establish its irrelevance.

Resolver preparation retains the delivered controlling source separately from the selected comparison facts. A change outside the selected excerpt requires current owner context before reuse or binding; it does not by itself require another investment judgment. A fresh preparation can explicitly adopt the same professional result when still supported. Older records without this source binding remain readable but need that refresh before automatic reuse; do not invent an experiment or change the result merely to migrate the record.

Normal resolver preparation and binding validate their referenced Git sources against `HEAD`; they do not certify an uncommitted objective change. `prepare-adoption`, `recover-work` and current-use correction read saved working files. At actual adoption, reconcile any newer working objective through the existing owner before dependent action. Do not describe a historical prepared view as current working authority or add a whole-repository clean-state requirement.

Preparation derives `judgment_scope` from the effective task sources and incoming assignment. Binding retains `judgment_binding`: the substantive decision digest, evidence and objective identities, and current task projections. Reuse checks this correspondence at preparation, adoption and participating delivery, including a terminal decision without a Worker dispatch. An old resolution reference, an unchanged route label or a false change flag cannot substitute for these checks. The saved bodies remain at their existing sources; the binding does not copy the history.

Ordinary Batch progress is separate from its operative definition. Progress, attempts and consumption remain evidence but do not alone invalidate the definition's correspondence. Prepared delivery still checks its exact supplied bytes; refresh stale delivery in the existing owner turn. A changed operative assignment needs an applicability judgment, not an automatic new research review. To retain applicable meaning while changing wording, prepare the current scope and supply a fresh professional result with `judgment_reuse: {source: {path: "path/to/prior-result.json", commit: "<saved revision>"}, reason: "<why the prior judgment still applies>"}`. Omit the prior generated binding; normal binding derives the new one and verifies the prior result, decision facts and objective basis. The reason is the owner's judgment, not machine-certified equivalence. Materially changed facts or consequences use the existing decision process.

The optional Harness offers the same distinction through `host judgment-view RUN_DIRECTORY`, with the proposed Response on standard input. It returns the previous/current identities for `update.judgment_reuse` without another model call or saved proof document. A terminal `completion` closes an already selected bounded deliverable; `mandatory_stop` stops only the affected operation under a real limit. An investment-ending `Finish`, including an unspecified terminal scope, enters the configured decision path. Honest terminal classification remains the owner's responsibility.

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

The resolver preparation and adopted-work registration read this live block and retain a conditional owner receipt in the existing `.frontier/hook-context` area, before optional native-session publication. This needs no commit, native session or new general registry. Resolver preparation supplies an open finding to its owner but will not reuse a saved decision over it. Binding checks that the prepared association has not changed; binding alone is not execution permission.

For a newly confirmed correction, use `adopt-work --repo . --path path/to/owner.md --correction-request path/to/correction.json --source path/to/task.md` instead of replacing the task before enrollment. The existing operation retains the original object and finding, saves the corrected bytes, discharges through owner evidence, and only then refreshes optional native context. A minimal request is:

```json
{
  "corrections": [{
    "id": "discovery-admission",
    "finding": "work/findings/discovery-admission.md",
    "effect": "repair",
    "affected_sources": ["work/research-task.md"],
    "status": "resolved",
    "resolution": {"reason": "Remove the unsupported prerequisite.", "evidence": "work/adoption.md"}
  }],
  "replacements": [{"path": "work/research-task.md", "contents": "The adopted corrected assignment.\n"}]
}
```

The request is the existing owner's prepared correction, not another approval. The helper retains the expected original versions and exact requested replacement bytes. Required write or validation failure leaves affected adoption incomplete; retry the same operation to recover retained intent without inventing a further edit. A third version visible at verification stops replacement until its owner reconciles it. Coordinate writers to affected files: optimistic verification cannot protect a write made by an uncoordinated process between the version check and file replacement. Keep the saved original finding and scope. Optional native failure does not undo completed required adoption. Entirely unsaved recognition has no recoverable receipt and must be established again; never claim that a failed operation completed adoption.

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

Unresolved associations survive omitted fields and context refresh. For a copied or renamed successor or a task consuming affected work, the existing owner carries the relation explicitly: `relations: [{source: "work/research-task.md", target: "work/successor.md", kind: "successor"}]` in the same adoption request; use `dependency` for a consuming task. This extends known use without relabeling the finding's historical affected paths or scanning for similar files. Independent tasks remain independent. Within one registered root, changing owner carries the previous associations. Outside that path, an explicit transfer places `current_use_predecessor: path/to/previous-owner.md` on the successor before adoption; its retained receipt remains usable if the old file was renamed. The predecessor's evidence identity must agree; its older status does not overwrite valid discharge.

Discharged records remain as references, not permanent freezes on later development. Clearing their display fields does not reopen a finding. Exact replay of a superseded object can still be detected. New semantic regressions need owner judgment. A previously unregistered owner rename with no predecessor reference is outside automatic continuity coverage; do not present it as a verified transfer.

## Participating consumption and limits

The successful helper return contains `current_use`: absolute owner, retained `correction_ids`, scoped `blocked_ids`, `checked_sources` for the actual requested objects, and `files` with absolute `path` and exact `contents`. Scope follows explicit successor/dependency relations. Snapshot bytes are the same bytes used for validation and are checked again after receipt publication; a relevant concurrent save fails that preparation. Later consumption still checks the saved versions. This is not a lock against arbitrary writes after a standalone check. Current owner edits need a refreshed snapshot, not another investment judgment; unrelated repository edits do not invalidate it.

A cooperating `workflow-harness` Session can import this object through `adopt_current_use`. The Coordinator's response separately identifies the next Work's saved task/dependencies in `actual_use`; preparation and consumption require that use to match the report's `checked_sources`, as well as checking bytes and queued identity. A report for independent B cannot clear request A. Missing scope on an attached binding is unsupported coverage, not permission to infer use from its files. The owner checker must supply the validated object; caller-invented empty `blocked_ids` is not validation. `replace_queued_work` applies only to an unstarted request. External dispatchers use `verify_queued_current_use` with the actual request they will issue. Preserve the normal return of already-started work rather than interrupting or replaying it to refresh context.

The existing host CLI exposes these same operations as `host current-use-adopt RUN_DIRECTORY OWNER_REPORT.json`, `host current-use-replace RUN_DIRECTORY CORRECTED_ASSIGNMENT.txt [ACTUAL_SOURCE ...]`, and `host current-use-check RUN_DIRECTORY ACTUAL_REQUEST.json`. Adoption consumes the owner checker's report, replacement emits a fresh request, and consumption checks that exact request before external dispatch. Replacement retains the prior actual-use scope when no source arguments are supplied; a successor task must supply its new scope. These commands do not infer semantic validity from a manually constructed report.

The default native Hook remains advisory and does not auto-import this attachment or intercept all worker actions. Direct and unsupported paths use the owner check above and inspect the actual outgoing task. A corrected follow-up explicitly supersedes the old restriction; inspect the next substantive action or return. Report unobserved stages honestly. Do not infer automatic enforcement from registration, source hashes, passing helper output or a sent message.
