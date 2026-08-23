# B066 nested-dispatch compatibility workflow review

Verdict: `WORKFLOW_READY`

Review artifact identity: `b066-nested-dispatch-compatibility-workflow-review-sha256:55aa53cbc3a12e0308172335a5ec94711b293438c7eaf2dac8ece8e76857f28b`

Identity rule: SHA-256 of the exact UTF-8 review bytes with the complete `Review artifact identity:` line omitted.

## Scope

This independent review covers only the focused, non-executing recovery change in:

- `.agents/skills/frontier-optimization/scripts/validate_batch_result.py`
- `.agents/skills/frontier-optimization/scripts/test_validate_batch_result.py`
- the project-dispatch recovery paragraph in `.agents/skills/frontier-optimization/references/batch-interface.md`

The implementation scope is the exact `frontier-project-batch-acknowledgment/1` and `frontier-project-execution-start/1` branch, including `omitted_line_identity`, `resolve_project_directory`, `verify_project_nested_dispatch`, the `project_dispatch` selection branch, and the three focused compatibility tests.

The review also used the frozen B066 packet, preflight, acknowledgment, execution-start, execution baseline, candidate package, raw engineering evidence, and `/private/tmp/B066-result-draft.yaml` as read-only validation inputs. It did not modify any B066 project artifact.

## Findings

None.

## Review conclusion

The standard dispatch path remains separate. The compatibility selector activates if either project contract appears, while `verify_project_nested_dispatch` requires both exact project contracts. A mixed shape, missing record, wrong file binding, or any compatibility exception returns `PROJECT_DISPATCH_RECOVERY_FAILED`; it cannot fall through to a more permissive standard path. The existing standard-chain acceptance and execution-start byte-drift rejection tests both continue to pass.

The recovery branch does not infer missing authority. It verifies the result's content-addressed packet, preflight, acknowledgment, and execution-start bindings before entering the compatibility helper. It then recomputes both project record self-identities from exact bytes, recomputes the packet and preflight identities, and requires the acknowledgment's exact packet and preflight path, identity, and raw-file digest bindings.

The helper verifies the execution-start's batch, generation, packet, acknowledgment, candidate root, result paths, worker release, execution verification, and exact-byte self-identity. Repository-relative files and directories are normalized, symbolic-link components are rejected, and every required file digest is recomputed.

The decision, review, authority, and execution portable bundles are independently verified in their role-specific project domains. Their exact content roots are matched to the frozen records and provenance nodes. The typed decision-to-attestation-to-authority-to-execution graph is loaded by content-derived node identity and checked by the shared provenance verifier. The execution baseline must preserve the exact packet, preflight, and acknowledgment bytes and the frozen non-released execution-state binding.

The compatible B066 result remains project-only. Its packet and draft both carry `workflow_source_identity: null`; the recovery helper neither reads a workflow identity into the project chain nor creates a project identity. The Batch Interface paragraph accurately describes the verified recovery set and explicitly says that other acknowledgment fields remain frozen by the acknowledgment self-identity and baseline copy without granting separately inferred authority. The repair changes no authorization, execution, measurement, reservation, or spend rule.

The exact frozen B066 draft validates finding-free in memory. Its computed result identity is `B066-result-sha256:a1cfa5a39f4ff01bc44b87013446dd2d58bf572315c74f96ceb2f6e229343f13`. A read-only mutation of the acknowledgment file digest is rejected with `DISPATCH_CHAIN_BINDING_INVALID`.

## Reviewed identities

- `validate_batch_result.py`: `sha256:7fbc03c2b7a43d5e4e9832a34fafadb14233c105fb0008741fc5980f102825f0`
- `test_validate_batch_result.py`: `sha256:ca8c43ae8952dd0c2bcc5202cd4634adb14855251b95ec302d612cd6b489ce9c`
- `batch-interface.md`: `sha256:e7e8f929ddcbeb911eee9a1c4d67fe46135b2b4816064d76c9a5758ce8a466c8`
- frozen B066 draft: `sha256:5e3c71a5b06bcdbfbf001bbc698e856ba51179d967d1ab35a6fc08e35a0889e2`

## Commands and results

Working directory for the unit-test command: `.agents/skills/frontier-optimization/scripts`.

```bash
../../../../.venv/bin/python -m unittest \
  test_validate_batch_result.BatchResultValidationTests.test_project_dispatch_recovery_uses_the_exact_nested_compatibility_gate \
  test_validate_batch_result.BatchResultValidationTests.test_project_dispatch_recovery_fails_closed_on_any_compatibility_error \
  test_validate_batch_result.BatchResultValidationTests.test_exact_line_identity_rejects_duplicate_identity_fields \
  test_validate_batch_result.BatchResultValidationTests.test_new_result_recomputes_complete_dispatch_chain \
  test_validate_batch_result.BatchResultValidationTests.test_new_result_rejects_execution_start_byte_drift
```

Result: 5 tests passed in 8.580 seconds.

```bash
../../../../.venv/bin/python -c '<non-writing AST parse; in-memory exact B066 draft validation; in-memory acknowledgment-digest tamper probe>'
```

Result: both reviewed Python files parsed; the exact B066 draft was finding-free; the digest-tampered binding failed closed with `DISPATCH_CHAIN_BINDING_INVALID`. Candidate code was not imported or executed.

```bash
git diff --check -- \
  .agents/skills/frontier-optimization/scripts/validate_batch_result.py \
  .agents/skills/frontier-optimization/scripts/test_validate_batch_result.py \
  .agents/skills/frontier-optimization/references/batch-interface.md
```

Result: passed with no whitespace errors.

```bash
sha256sum \
  candidates/B066-w006-r6-source-evidence-closure-repair/{main.py,metadata.json,policy.py} \
  artifacts/frontier/B066/project-only/r2/{candidate-package-inventory.yaml,candidate-manifest.yaml,manifest-validation.json,unit-tests.json,junit.xml,engineering-evidence-manifest.json,acknowledgment.yaml,execution-start.yaml,B066-plan.yaml,packet-preflight-r3.json}
```

Result: the frozen candidate, acknowledgment, execution-start, JUnit, raw evidence, manifests, packet, and preflight retained their recorded SHA-256 values. No B066 byte was changed.

## Authority effect

This workflow review grants no project authority and creates no campaign record, candidate, proposal, reservation, spend, execution, measurement, evaluator or game access, successor-input access, remote action, paid action, integration, promotion, publication, or strength claim. It supports only non-executing validation and publication of the already frozen B066 result through the exact reviewed compatibility path.
