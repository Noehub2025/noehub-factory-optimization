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
5. **Isolate work.** Pin source-base and dirty-state identity. Assign exclusive worker write surfaces, worker-forbidden paths, execution-frozen inputs, one Coordinator-owned execution-baseline root, one Coordinator-owned execution-start path, and one worker-owned result-validation path. Never freeze the whole W; bind its design sections, concerns, and traceability instead. Parallel code-bearing B records use separate worktrees; a branch or worktree is transport, not candidate identity.
6. **Materialize one slice.** Begin only after the accepted acknowledgment and valid execution-start record binds a complete content-addressed post-transition baseline snapshot. Implement only the selected vertical slice through the candidate interface and required design inputs. Resolve configuration and dependencies, run engineering checks, and write the manifest below. A material behavior-bearing change creates a new candidate identity. Before the immutable result path exists, require finding-free draft and frozen result validation; code materialization always uses `results: []`.
7. **Review implementation.** Stop at the materialized-candidate checkpoint. Freeze an implementation snapshot and invoke fresh-context `review-frontier` with `review_kind: implementation`. Only adopted unchanged `IMPLEMENTATION_READY` permits first performance measurement, mainline integration, or incumbent use.
8. **Measure separately.** Select a new `work_kind: experiment`, `changes_executable_candidate: false` B only after adopted unchanged `IMPLEMENTATION_READY` and the implementation B's Outcome Reflection. Bind the candidate, evaluator, data, controls, protocol, environment, budget, and result paths to one immutable experiment identity before dispatch. Engineering completion, integration, comparison validity, measurement, E adoption, and promotion remain separate decisions.
9. **Integrate or archive.** Integration needs its own B or Selection authority and does not promote. Closeout preserves cited identities before removing only reconstructible workspaces and intermediates.

A configuration-only candidate may reuse review only when reviewed code, interface, dependency identity, configuration schema, evaluator, and allowed configuration space remain unchanged. A code-bearing `mixed` B stops before first measurement, integration, or incumbent use.

## Post-closeout recovery reuse

An explicit new recovery campaign may reuse one materialized candidate without creating another proposal identity only when all of these hold:

- the prior campaign has adopted complete closeout and exact final accounting;
- the new generation has an authorization V and X disposition naming the exact candidate, manifest, source result, engineering evidence, prior B result, prior implementation review, and reuse limits;
- candidate bytes, interface, resolved configuration, dependencies, runtime factors, generated assets, and every identity input recompute exactly;
- no candidate file is copied, regenerated, normalized, patched, or otherwise changed during reuse validation; and
- a fresh `review_mode: recovery-reuse` implementation review returns and is adopted as unchanged `IMPLEMENTATION_READY` before measurement, integration, or incumbent use.

Before any new-generation record, run `scripts/validate_candidate_recovery.py` in draft mode against the canonical candidate root and manifest. Compare requested identities with independently recomputed manifest, member, and package identities. On PASS, freeze the preflight and reproduce its identity before V/X adoption. On mismatch, return `BLOCKED` without a generation update, recovery record, review, Selection, reservation, or spend. Do not treat a conversation-copied digest as canonical evidence.

The recovery review authorizes the unchanged candidate only in the new campaign generation. It does not revise the old B outcome or prior review. A nonpositive old implementation review may be cited as historical diagnosis; the recovery reviewer must independently decide whether its finding concerns candidate fidelity or only closed-generation authority. Any missing byte, identity mismatch, behavior-bearing change, or attempted repair ends zero-cost reuse and requires a new code-bearing B, development authorization, candidate identity, and proposal charge.

## Candidate manifest

The batch worker writes this sole manifest after every listed identity resolves.

```yaml
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
engineering_evidence: [<check and stable evidence identity>]
recovery_artifacts: [<recoverable packet preflight, packet, acknowledgment, execution-baseline snapshot and manifest, execution-start, result validation, candidate, source, configuration, dependency, generated-asset, and evidence bytes with stable identities>]
implementation_review: <assigned review path pending, adopted review identity, reusable review identity, or not required with rule>
created_at: <ISO-8601 datetime>
```

A direct candidate is recoverable only when a fresh Coordinator can reconstruct its finding-free packet preflight, packet, acknowledgment, content-addressed execution-baseline snapshot, execution-start record and post-transition baseline, finding-free result validation, authorization, source base and result, candidate bytes, configuration, dependencies, runtime factors, generated assets, engineering evidence, and candidate identity without relying on a live branch or worktree. Later campaign-record bytes may prove current state but never substitute for the exact start-time snapshot. Recovery preserves the materialized candidate; it grants no performance-evaluation, integration, or incumbent permission before adopted unchanged `IMPLEMENTATION_READY`.
