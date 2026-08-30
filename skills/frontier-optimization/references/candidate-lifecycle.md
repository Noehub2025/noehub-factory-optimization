# Frontier Candidate Lifecycle

Load only for historical candidate publication or a specialized publication seam that truly needs a separately retained package. Current working implementation and checks use [Current Batch](batch-current.md) and Git Candidate Revisions; changing bytes inside the same independently judged result does not create a Candidate identity, proposal, Attempt, charge, Review, Permission, or new B.

The identity-heavy lifecycle below is a compatibility contract for retained records that already use it. It is not a sequence for a current B. Current development uses [Executable work](batch-code-execution.md), one Git Candidate Revision, focused checks and the applicable implementation Review. A new workflow must not select this file merely because work changes code, data, a model, configuration or another executable artifact. If an external publication boundary requires an immutable package, keep that external package reference in the producing Attempt and add only the controls required by that seam.

## Terms

- **Repository structure assessment:** inventory project files outside docs, Frontier state, workflow metadata, version-control metadata, caches, environments, and generated artifacts. A root entry file, build manifest, source or test tree, configuration tree, or artifact convention may establish structure.
- **Candidate interface:** smallest existing or user-approved seam through which runner, evaluator, callers, and tests exercise replaceable implementations.
- **Code-bearing B:** any B that changes code, configuration schema, dependencies, executable assets, public interfaces, or behavior-changing runtime material. Work-kind labels cannot weaken its gates.
- **Candidate identity:** immutable binding of parents, source base and result, code, configuration, dependencies, runtime factors, generated assets, and candidate interface. A path, branch, worktree, or role name is not identity.
- **Experiment identity:** separate binding of candidate to evaluator, data, controls, protocol, environment, budget, and result artifacts.

## Historical retained lifecycle

The numbered steps in this section describe old retained objects. Follow them only to interpret or validate an object that already contains those fields. Never generate acknowledgment, execution-start, snapshot, packet, candidate identity or experiment identity for current work from this section.

1. **Assess structure.** Use Entry code planning's repository-fit dispositions from cited project evidence.
2. **Decide placement.** Prefer the smallest native integration. The technical owner selects structure and tools; ask only for an unresolved user-owned consequence under [User decisions](user-decisions.md).
3. **Design at the seam.** Choose `direct`, `module`, or `system`. A research, design, or non-code prototype may resolve missing evidence but authorizes no candidate code.
4. **Validate, review, and authorize.** Initial `module` and `system` work needs `DESIGN_READY`, machine-readable W traceability and valid Entry inputs. `direct` needs the same gates except Design and W. Entry uses spend-readiness under an applicable grant, or authorization-readiness before a genuinely needed user question. The original user grant remains outside W. Subsequent changes follow Batch Interface's continuation rule; a delegated design revision does not automatically repeat Entry.
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

- the code-bearing B is terminal, its result validation is finding-free, and its immutable candidate identity, manifest, engineering evidence, and recovery point exist;
- the experiment is local, isolated, reversible, bounded, and free of production, user, external-system, sensitive-data, paid-resource, safety-critical, or other material external effect;
- applicable hard constraints and the minimum checks needed to execute safely have passed;
- the experiment uses no sealed confirmation, hidden holdout, submission, deployment, or other evidence reserved for a later decision;
- the experiment identity binds the candidate, evaluator, diagnostic inputs, controls, environment, maximum spend, and exclusive result paths before dispatch; and
- the packet states the result branches for continue, revise, stop, or plan a later formal check, and prohibits E, integration, incumbent use, promotion, submission, and strength claims.

The accepted result remains B evidence and enters the next resolver state. It cannot create E, satisfy Slot H comparison validity, stand in for implementation review, or support any stronger consequence. Complete and adopt fresh unchanged `IMPLEMENTATION_READY` before formal Slot H measurement, integration, or incumbent use. Recovery reuse is not eligible for this exception.

## Post-closeout recovery reuse

Apply [Change impact and retained results](frontier-core.md#change-impact-and-retained-results). Recovery changes the context of the next use, not the historical production record.

- **Published, unchanged, same use:** retain the original implementation conclusion. No recovery implementation review, provenance sidecar or intervening-generation proof is required merely because parents, workflow or generation changed.
- **Unpublished retained realization:** use the existing `materialization` review with `publication_state: prepublication`. Bind its exact working inventory, original execution-start and engineering evidence. Current permission governs the proposed publication; the original execution remains bound to its producing parents. A final manifest or published candidate is not an input to this review. If checks are incomplete, continue the missing working checks within applicable permission first.
- **Changed use or concrete contrary evidence:** check only the affected conclusion or missing evidence through the existing review mode. A new review does not overwrite an old verdict, and old evidence is not upgraded to a broader claim.
- **Changed candidate bytes:** retain the original candidate and use normal working development and the applicable charge rule for the new material. Missing historical material pauses its dependent use; it is not itself a chargeable event or a requirement to replace B.

When exact material needs checking for a proposed use, `validate_candidate_recovery.py` validates the original manifest or working inventory and latest closeout accounting. It is not a routine generation-opening gate or a proof of permission, implementation readiness or comparability. A candidate may come from any earlier generation. Keep historical files unchanged; no workflow-identity backfill is required.


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

After all engineering evidence identities resolve, write the final manifest below exactly once. `code_paths` must exactly equal the inventory by path and digest; `source_result_identity.package_sha256` and, when present, `.members` must describe the same inventory. The final manifest binds the package inventory, completed engineering evidence, and the positive implementation review of those bytes. Result validation, result adoption, resolver decisions, and closeout are downstream and never appear inside the manifest.

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
