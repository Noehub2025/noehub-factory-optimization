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
4. **Validate, review, and authorize.** `module` and `system` need unchanged `DESIGN_READY`, machine-readable W traceability, finding-free structural packet and Entry schema validation, and fresh `AUTHORIZATION_READY` before the user question. `direct` needs the same gates except design review and W. The user V and Coordinator Entry adoption bind the exact reviewed target. Current authorization lives outside W. A changed design contract, traceability, packet, preflight, source, scope, spend, or stop boundary requires fresh authorization-readiness review.
5. **Isolate work.** Pin source-base and dirty-state identity. Assign exclusive worker write surfaces, worker-forbidden paths, execution-frozen inputs, one Coordinator-owned execution-baseline root, one Coordinator-owned execution-start path, one complete `candidate_root_path`, and one worker-owned result-validation path. Never freeze the whole W; bind its design sections, concerns, and traceability instead. Parallel code-bearing B records use separate worktrees; a branch or worktree is transport, not candidate identity.
6. **Materialize one slice.** Begin only after the accepted acknowledgment and valid execution-start record binds a complete content-addressed post-transition baseline snapshot. Implement only the selected vertical slice through the candidate interface and required design inputs. Resolve configuration and dependencies, write the package inventory below, stage only that inventory into an isolated runtime, and run the packet's frozen engineering check plan there. After every check and evidence identity resolves, write the final manifest exactly once and validate it against the unchanged inventory and canonical root. A material behavior-bearing change creates a new candidate identity. It does not by itself increment `campaign_generation`: a still-open campaign may authorize the new candidate through a new code-bearing B, while only post-closeout recovery opens the next generation. Before the immutable result path exists, require finding-free draft and frozen result validation; code materialization always uses `results: []`.
7. **Review implementation.** Stop at the materialized-candidate checkpoint. Freeze an implementation snapshot and invoke fresh-context `review-frontier` with `review_kind: implementation`. Only adopted unchanged `IMPLEMENTATION_READY` permits first Slot H measurement, mainline integration, or incumbent use. The diagnostic-only exception below may run before this review without granting any of those consequences.
8. **Measure separately.** Select a new `work_kind: experiment`, `changes_executable_candidate: false` B only after adopted unchanged `IMPLEMENTATION_READY` and the implementation B's Outcome Reflection. Bind the candidate, evaluator, data, controls, protocol, environment, budget, and result paths to one immutable experiment identity before dispatch. Engineering completion, integration, comparison validity, measurement, E adoption, and promotion remain separate decisions.
9. **Integrate or archive.** Integration needs its own B or Selection authority and does not promote. Closeout preserves cited identities before removing only reconstructible workspaces and intermediates.

A configuration-only candidate may reuse review only when reviewed code, interface, dependency identity, configuration schema, evaluator, and allowed configuration space remain unchanged. A code-bearing `mixed` B stops before first diagnostic or Slot H measurement, integration, or incumbent use.

## Diagnostic-only exception

A separate `work_kind: experiment`, `changes_executable_candidate: false` B may measure a newly materialized candidate before implementation review only when Entry verifies all of these conditions:

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

The batch worker first writes one immutable package inventory outside `candidate_root_path`. This is a staging input, not a candidate manifest and not engineering evidence. It derives the candidate identity from every regular file under `candidate_root_path`, ordered by relative path and represented as `{path, size, sha256}`. No cache, bytecode, temporary file, or other extra file is ignored. Any `__pycache__` member or `.pyc` or `.pyo` file is prohibited even when declared.

```yaml
contract_version: frontier-candidate-package-inventory/1
candidate_root: <complete candidate root>
identity_algorithm: package-path-size-sha256-v1
candidate_id: <byte-derived immutable identifier>
package_sha256: <lowercase digest>
members: [<ordered path, size, and sha256 mappings>]
inventory_id: <SHA-256 of this mapping with inventory_id omitted>
```

Run every import, compilation, test, evaluator-backed engineering fixture, or other check only from a runtime staged from that exact inventory. Revalidate the canonical root against the inventory after every operation that could load candidate code. The engineering evidence binds the inventory, packet authority, exact selected check units, observed effects and accounting, but never the later final manifest.

After all engineering evidence identities resolve, write the final manifest below exactly once. `code_paths` must exactly equal the inventory by path and digest; `source_result_identity.package_sha256` and, when present, `.members` must describe the same inventory. The final manifest binds the package inventory and completed engineering evidence. It contains only upstream recovery artifacts. Result validation, result, Outcome Reflection, closeout, and implementation review are downstream: they bind the final manifest and belong together in the implementation-review snapshot, never inside the manifest.

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
source_base_identity: <commit and dirty-state identity, or immutable source snapshot>
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
implementation_review: <assigned review path pending, adopted review identity, reusable review identity, or not required with rule>
created_at: <ISO-8601 datetime>
```

`workflow_source_identity` is forbidden in every newly written version 3 manifest. Do not rewrite an immutable version 2 manifest; use the exact legacy recovery adapter when that historical object is eligible.

A direct candidate is recoverable only when a fresh Coordinator can reconstruct the inventory, final manifest, finding-free packet preflight, packet, acknowledgment, content-addressed execution-baseline snapshot, execution-start record and post-transition baseline, finding-free result validation, authorization, source base and result, candidate bytes, configuration, dependencies, runtime factors, generated assets, engineering evidence, and candidate identity without relying on a live branch or worktree. The implementation-review snapshot joins the final manifest with its downstream result and result validation. Later campaign-record bytes may prove current state but never substitute for the exact start-time snapshot. Recovery preserves the materialized candidate; it grants no performance-evaluation, integration, or incumbent permission before adopted unchanged `IMPLEMENTATION_READY`.

After the inventory exists, never import, execute, compile, or inspect executable candidate code in the canonical candidate root. Use `validate_candidate_package.py --inventory-path <inventory-path> --stage-root <exclusive-runtime-path>` to copy only inventory members into a new isolated runtime directory, then run every loader, evaluator, test, or engineering check there. Python invocations also use `-B` or `PYTHONDONTWRITEBYTECODE=1`; this is a secondary defense, not a substitute for isolation. After any operation that could load candidate code, revalidate the canonical root against the inventory. Immediately before result validation, require `validate_candidate_package.py --require-final-manifest` to pass. Any new root member or changed byte blocks result publication, implementation review, evaluation, and recovery. Do not delete or normalize the unexpected byte automatically; preserve the blocker and require an explicitly authorized successor repair.

Historical manifest forms remain audit evidence and may support an already adopted unchanged implementation review. They cannot publish a new code-materialization result or grant new implementation readiness. New materialization uses the inventory and `frontier-candidate-manifest/3` chain above.
