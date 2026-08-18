# Transitive candidate recovery workflow review

Verdict: `WORKFLOW_READY`

## Scope

This independent review covers the current workflow implementation in:

- `scripts/validate_candidate_recovery.py`
- `scripts/test_validate_candidate_recovery.py`
- `references/candidate-lifecycle.md`
- `references/packaging-and-recovery.md`
- the directly imported identity, finding, and package-validation helpers

It does not review or bind any project campaign record, candidate, manifest, legacy sidecar, framing handoff, or workflow release identity.

## Findings

None.

## Review conclusion

The validator permits reuse of an unchanged candidate from an older generation only through the exact consecutive generation range between candidate production and the immediately closed generation. Each hop must bind a frozen recovery preflight, a content-derived reuse disposition, a complete closeout, a complete handoff, and a closed Budget record by repository-relative path, declared identity, and raw-file SHA-256 digest.

Each bound preflight is recursively validated in frozen mode. That recursive check revalidates the candidate root, every package member, the final manifest, the requested candidate and manifest identities, zero proposal attempts, prohibited mutation, prior closeout, handoff, and Budget. Later preflights must consume the preceding hop's closeout, handoff, and Budget identities, and the final hop must equal the current preflight's lineage bindings. Missing, reordered, divergent, cyclic, tampered, incomplete, or Budget-regressing chains fail closed.

Direct recovery remains valid only when the manifest generation equals the immediately closed generation, and it rejects an unnecessary transitive chain. Historical version 2 manifests retain their existing compatibility path: a recorded workflow-source identity is checked exactly, while a genuinely absent historical field requires the complete content-addressed legacy sidecar. The repair does not relax candidate, manifest, member, source, preflight, or lineage identity checks.

## Checks

- Non-writing abstract syntax tree parse of both Python files: passed.
- Focused recovery suite: 28 tests passed.
- Scoped `git diff --check` for the four reviewed workflow files: passed.
- Adversarial cases covered by the suite include one-hop and multi-hop reuse, missing and reordered hops, disposition tampering, linked-preflight tampering, incomplete closeout, Budget regression, invalid source generation, candidate-byte drift, manifest drift, source-binding drift, symbolic links, and legacy cross-binding mismatches.

A bytecode-compilation attempt was not used as evidence because the environment prohibited its cache write. It produced no review finding; the required non-writing syntax check passed.

## Authority effect

This workflow review grants no project authority and creates no campaign, candidate, proposal, reservation, spend, execution, measurement, sealed-input access, remote action, or paid action.
