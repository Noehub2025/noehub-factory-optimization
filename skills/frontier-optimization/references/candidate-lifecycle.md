# Frontier Candidate Lifecycle

Load only when a proposed or selected B has `changes_executable_candidate: true`, or when checking whether an implementation review remains reusable.

## Terms

- **Repository structure assessment:** inventory project files outside docs, Frontier state, workflow metadata, version-control metadata, caches, environments, and generated artifacts. A root entry file, build manifest, source or test tree, configuration tree, or artifact convention may establish structure.
- **Candidate interface:** smallest existing or user-approved seam through which runner, evaluator, callers, and tests exercise replaceable implementations.
- **Code-bearing B:** any B that changes code, configuration schema, dependencies, executable assets, public interfaces, or behavior-changing runtime material. Work-kind labels cannot weaken its gates.
- **Candidate identity:** immutable binding of parents, source base and result, code, configuration, dependencies, runtime factors, generated assets, and candidate interface. A path, branch, worktree, or role name is not identity.
- **Experiment identity:** separate binding of candidate to evaluator, data, controls, protocol, environment, budget, and result artifacts.

## Lifecycle

1. **Assess structure.** Classify `existing-integrated` or `absent-awaiting-user` from cited project evidence.
2. **Decide placement.** Prefer the smallest native integration. A new top-level root, replacement toolchain or dependency manager, or changed public entrypoint needs a tradeoff V. When structure is absent, record `user-approved-new` only after the user chooses a layout.
3. **Design at the seam.** Choose `direct`, `module`, or `system`. A research, design, or non-code prototype may resolve missing evidence but authorizes no candidate code.
4. **Validate, review, and authorize.** Initial `module` and `system` work needs `DESIGN_READY`, machine-readable W traceability, valid Entry inputs, and `AUTHORIZATION_READY` before the user question. `direct` needs the same gates except Design and W. The user answer and adoption bind the reviewed scope outside W. Subsequent changes follow Batch Interface's continuation rule; a delegated design revision does not automatically repeat Entry.
5. **Isolate work.** Record the saved Git source version and the authorized mutable working scope. Assign exclusive worker write surfaces, worker-forbidden paths, execution-frozen inputs, one Coordinator-owned execution-baseline root, one Coordinator-owned execution-start path, one complete `candidate_root_path`, and one worker-owned result-validation path. Never freeze the whole W; bind its design sections, concerns, and traceability instead. Parallel code-bearing B records use separate worktrees; a branch or worktree is transport, not candidate identity.
6. **Develop the realization.** Begin only after the accepted acknowledgment and valid execution-start record binds a complete content-addressed post-transition baseline snapshot. Satisfy the B's `delivery_scope` and maintain its mutable work breakdown inside the assigned workspace. Use working feedback under the canonical [Boundary-preserving continuation](batch-interface.md#boundary-preserving-continuation), then inventory and stage the exact realization selected for frozen closing checks. The formal attempt starts with the first such check, not with inventory preparation. If the parent charges an earlier identity or exposure event, preserve that recorded boundary instead of treating later bytes as free working material.
7. **Review, then publish.** Once the complete realization satisfies its required engineering and integration checks, freeze its exact inventory and implementation-review inputs. Apply Batch Interface's continuation rule to fidelity or design findings; neither label alone ends B. Only `IMPLEMENTATION_READY` makes those exact bytes publication-eligible. Publish atomically, accept only a byte-identical retry, reconcile the parent-owned charge once, and complete the manifest and result. A material behavior change after publication creates a new candidate identity. Formal Slot H measurement, integration, and incumbent use retain their own gates.
8. **Measure separately.** After adopted unchanged `IMPLEMENTATION_READY`, use either the one pre-authorized `routine-local` slot in [Evaluation protocol reuse](evaluation-protocol.md) or select a separately reviewed formal Slot H B. A routine screen does not require a second Entry, but it remains B evidence and cannot create E. Bind the candidate, evaluator, data, controls, protocol, environment, budget, and result paths to one immutable experiment identity before dispatch. Engineering completion, integration, comparison validity, formal measurement, E adoption, and promotion remain separate decisions.
9. **Integrate or archive.** Integration needs its own B or Selection authority and does not promote. Closeout preserves cited identities before removing only reconstructible workspaces and intermediates.

A candidate publication or byte-identical recovery reuse preserves the campaign lifecycle boundary. It does not by itself increment `campaign_generation`; only the campaign-opening transition owns that lifecycle change.

A configuration-only candidate may reuse review only when its actual reviewed dependencies and allowed configuration space remain valid. Code-bearing work may include explicitly authorized working observations under Batch Interface; formal Slot H measurement, integration, and incumbent use retain their separate gates.

## Diagnostic-only exception

For unpublished working material, use [Bounded observations before publication](batch-interface.md#bounded-observations-before-publication), including within the same B. The following exception concerns already published candidates under historical publication-before-review parents; it does not restrict working-material diagnostics.

A separate `work_kind: experiment`, `changes_executable_candidate: false` B may measure a formally published candidate before implementation review only when its controlling parent required publication before review and Entry verifies all of these conditions. The normal prepublication-review path is not eligible because it creates no candidate before review:

- the code-bearing B is terminal, its result validation is finding-free, and its immutable candidate identity, manifest, engineering evidence, recovery point, and controlling Outcome Reflection exist;
- the experiment is local, isolated, reversible, bounded, and free of production, user, external-system, sensitive-data, paid-resource, safety-critical, or other material external effect;
- applicable hard constraints and the minimum checks needed to execute safely have passed;
- the experiment uses no sealed confirmation, hidden holdout, submission, deployment, or other evidence reserved for a later decision;
- the experiment identity binds the candidate, evaluator, diagnostic inputs, controls, environment, maximum spend, and exclusive result paths before dispatch; and
- the packet states the result branches for continue, revise, stop, or plan a later formal check, and prohibits E, integration, incumbent use, promotion, submission, and strength claims.

The accepted result remains B evidence and enters one Outcome Reflection. It cannot create E, satisfy Slot H comparison validity, stand in for implementation review, or support any stronger consequence. Complete and adopt fresh unchanged `IMPLEMENTATION_READY` before formal Slot H measurement, integration, or incumbent use. Recovery reuse is not eligible for this exception.

## Post-closeout recovery reuse

An explicit new recovery campaign may reuse one materialized candidate without creating another proposal identity only when all of these hold:

- the prior campaign has adopted complete closeout and exact final accounting;
- the new generation has an authorization V and X disposition naming the exact candidate, manifest, source result, engineering evidence, prior B result, prior implementation review, and reuse limits;
- candidate bytes, interface, resolved configuration, dependencies, runtime factors, generated assets, and every identity input recompute exactly;
- no candidate file is copied, regenerated, normalized, patched, or otherwise changed during reuse validation; and
- a fresh `review_mode: recovery-reuse` implementation review returns and is adopted as unchanged `IMPLEMENTATION_READY` before measurement, integration, or incumbent use.

Before any new-generation record, run `scripts/validate_candidate_recovery.py` in draft mode against the canonical candidate root and manifest. Compare requested identities with independently recomputed manifest, member, and package identities. On PASS, freeze the preflight and reproduce its identity before V/X adoption. On mismatch, return `BLOCKED` without a generation update, recovery record, review, Selection, reservation, or spend. Do not treat a conversation-copied digest as canonical evidence.

When the candidate was produced before the immediately closed generation, `intervening_recovery_chain` is mandatory. It contains exactly one consecutive link for each generation after production through the immediately closed generation. Every link binds the frozen recovery preflight, the byte-identical reuse disposition, the completed closeout, the completed handoff, and final Budget by exact path, embedded identity when present, and file digest. The linked preflight must recursively validate the same candidate root, manifest, package identity, no-mutation rule, and zero-proposal rule; each later preflight must consume the preceding link's closeout, handoff, and Budget identities. The final link must equal the current preflight's prior-lineage bindings. A missing, repeated, reordered, divergent, unclosed, non-content-addressed, or Budget-regressing link blocks reuse. No chain is allowed when the candidate came from the immediately closed generation.

Historical candidate manifests remain byte-identical and may use the exact-inventory legacy reader. A legacy `frontier-candidate-manifest/2` may retain its recorded `workflow_source_identity`; a provenance-only sidecar may supply a genuinely absent historical binding only when the recovery inventory and validator require it. A current `frontier-candidate-manifest/3` rejects that field. The sidecar never creates current authority and never replaces the fresh `recovery-reuse` implementation review.

The recovery review authorizes the unchanged candidate only in the new campaign generation. It does not revise the old B outcome or prior review. A nonpositive old implementation review may be cited as historical diagnosis; the recovery reviewer must independently decide whether its finding concerns candidate fidelity or only closed-generation authority. Any missing byte, identity mismatch, behavior-bearing change, or attempted repair ends zero-cost reuse and requires a new code-bearing B, development authorization, candidate identity, and proposal charge.

## Candidate package and final manifest

Before frozen closing checks, the batch worker derives a transient inventory from every regular file in the exact submitted realization under `candidate_root_path`, ordered by relative path and represented as `{path, size, sha256}`. Working feedback and inventory preparation create no formal attempt, authority, or later-use eligibility by themselves; any parent-owned identity or charge follows [Charging and publication](batch-interface.md#charging-and-publication). A submitted realization contains no cache, bytecode, temporary file, or other non-deliverable member; any `__pycache__`, `.pyc`, or `.pyo` member in that realization is prohibited even when declared.

After a positive implementation review, publish one official immutable package inventory outside `candidate_root_path` from byte-identical reviewed bytes. The existing writer creates it exclusively; an identical existing inventory returns `already-present-identical`, while different bytes return a conflict. Reconcile the publication's recorded event under [Charging and publication](batch-interface.md#charging-and-publication); its inventory identity establishes content equality, not whether a new budget event occurred. This inventory is not the final manifest or engineering evidence.

```yaml
contract_version: frontier-candidate-package-inventory/1
candidate_root: <complete candidate root>
identity_algorithm: package-path-size-sha256-v1
candidate_id: <byte-derived immutable identifier>
package_sha256: <lowercase digest>
members: [<ordered path, size, and sha256 mappings>]
inventory_id: <SHA-256 of this mapping with inventory_id omitted>
```

Run formal closing checks against the selected realization. Use an isolated runtime when needed; temporary materialization is not another archival snapshot. Apply the scoped consumption checks in [Provenance, Git, and retained artifacts](provenance-and-identity.md), rechecking declared inputs when they may have changed instead of scanning the canonical root after every command. Engineering evidence binds the ordered formal-attempt summary, any nonfinal passing inventory's nonpositive review handoff, official inventory, packet authority, exact selected check units, observed cumulative effects, and accounting, but never working feedback or the later final manifest. The final manifest separately binds the positive implementation review. The official inventory must reproduce the candidate and package identities of the final positively reviewed transient inventory.

After all engineering evidence identities resolve, write the final manifest below exactly once. `code_paths` must exactly equal the inventory by path and digest; `source_result_identity.package_sha256` and, when present, `.members` must describe the same inventory. The final manifest binds the package inventory, completed engineering evidence, and the positive implementation review of those bytes. Result validation, result, Outcome Reflection, and closeout are downstream and never appear inside the manifest.

```yaml
manifest_contract: frontier-candidate-manifest/3
manifest_state: final
candidate_id: <immutable identifier>
campaign_generation: <positive integer>
role: <campaign-baseline-candidate | challenger | incumbent-candidate | retained-support | other exact role>
parent_candidates: [<candidate identifiers or reference baseline identity>]
problem_epoch: <integer>
representation_revision: <integer>
route_id: <T identifier or null>
batch_id: <B identifier>
work_plan: <W path, revision, and design contract identity; or exact direct packet_id>
design_review: <adopted DESIGN_READY identity, or not required under direct profile>
required_design_inputs: [<implemented concern pointers and identities, or none>]
development_authorization: <unchanged AUTHORIZATION_READY, V, Coordinator Entry-adoption identity, and frozen adoption-validation identity bound to the exact reviewed target>
source_base_identity: <retained Git commit and selected source scope>
source_result_identity: <head commit and diff identity, content manifest, or immutable packaged source identity>
candidate_interface: <seam and interface identity>
code_paths: [<path and content identity>]
resolved_configuration: <stable path and identity, or null>
dependency_identity: <lockfile, image, environment, or explicit none with reason>
runtime_factors: [<behavior-changing factor and fixed value>]
generated_assets: [<stable path and identity, or none>]
package_inventory: {path: <inventory path>, inventory_id: <source-derived identity>, file_sha256: <lowercase digest>}
engineering_evidence: [<completed content-addressed evidence manifest that binds package_inventory.inventory_id, plus any directly bound evidence paths and file_sha256 values>]
recovery_artifacts: [<role, path, and file_sha256 for packet preflight, packet, authorization, acknowledgment, execution-baseline manifest, execution-start, source, configuration, dependency, generated assets, and other upstream bytes>]
implementation_review: {path: <positive review artifact>, file_sha256: <lowercase digest>, review_result: IMPLEMENTATION_READY, candidate_id: <this exact candidate identifier>}
created_at: <ISO-8601 datetime>
```

`workflow_source_identity` is forbidden in every newly written version 3 manifest. Do not rewrite an immutable version 2 manifest; use the exact legacy recovery adapter when that historical object is eligible.

A direct candidate is recoverable only when a fresh Coordinator can reconstruct the inventory, final manifest, finding-free packet preflight, packet, acknowledgment, content-addressed execution-baseline snapshot, execution-start record and post-transition baseline, finding-free result validation, authorization, source base and result, candidate bytes, configuration, dependencies, runtime factors, generated assets, engineering evidence, and candidate identity from retained Git versions and required external artifacts rather than the current working copy. The implementation-review snapshot joins the final manifest with its downstream result and result validation. Later campaign-record bytes may prove current state but never substitute for the exact start-time snapshot. Recovery preserves the materialized candidate; it grants no performance-evaluation, integration, or incumbent permission before adopted unchanged `IMPLEMENTATION_READY`.

Before the first frozen closing check, use `validate_candidate_package.py --inventory-path <inventory-path> --stage-root <exclusive-runtime-path>` to copy only inventory members into a new isolated runtime directory. Run formal loaders, evaluators, tests, and engineering checks there; Python invocations also use `-B` or `PYTHONDONTWRITEBYTECODE=1`. After each formal operation that could load candidate code, revalidate the canonical root against the applicable inventory. Immediately before result validation, require `validate_candidate_package.py --require-final-manifest` to pass. After official inventory publication, any new root member or changed byte blocks result publication, implementation review, evaluation, and recovery. Preserve that blocker and require an explicitly authorized successor repair.

Historical manifest forms remain audit evidence and may support an already adopted unchanged implementation review. They cannot publish a new code-materialization result or grant new implementation readiness. New materialization uses the inventory and `frontier-candidate-manifest/3` chain above.
