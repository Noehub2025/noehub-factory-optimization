# Result spend-readiness compatibility code review

Date: 2026-08-27

Review outcome: Zero open findings after one narrow compatibility correction. No authority bypass was found in the focused change.

## Scope and method

This independent code review covers only the new `verify_entry_readiness` helper, its call and raw-content plumbing in `verify_project_nested_dispatch`, the associated options in `write_project_dispatch_fixture`, and `test_result_spend_readiness.py`. The surrounding working tree contains unrelated changes and is not approved by this review.

The review used the current `references/user-decisions.md`, `references/entry-review.md`, and the dispatch/publication paragraphs in `references/batch-result.md`. It traced the existing review adapter, complete-subject checks, role-specific content stores, and typed provenance graph. It did not run tests, project code, evaluators, or games, and did not change workflow rules or project records.

This is a workflow-tool code review, not a Frontier project review. It does not belong in project evidence and grants no permission to execute or publish a project result.

## Finding

### F1: Preserve supported structured-file suffixes when locating the reviewed plan

Priority: P2. Closed after correction and focused verification.

Location: `scripts/validate_batch_result.py:538-545`.

The initial helper filtered plan members using case-sensitive `name.endswith((".yaml", ".yml", ".json"))`. The existing role adapter accepts these suffixes case-insensitively in `scripts/frontier_provenance/review_contract.py:114-119`; preparation also uses `path.suffix.lower()` in `scripts/frontier_review/preparation.py:300-305`. Logical-name validation does not prohibit uppercase suffixes. Consequently, a complete, otherwise valid spend-readiness decision whose plan member ended in `.YAML`, `.YML`, or `.JSON` passed the adapter but was omitted by the new helper. It then failed with `spend-readiness does not attest this exact dispatch plan`, preventing publication despite unchanged authority and plan bindings.

Minimum closure: Make this selection honor the existing adapter's accepted suffix handling, and demonstrate one focused draft/frozen round trip using an uppercase plan-member suffix. No contract or architecture change is needed.

Closure evidence: The coordinator changed the filter to `name.lower().endswith(...)`, added the `uppercase_plan` fixture option to prepare the same plan under a `.YAML` logical name, and added a spend-readiness round-trip case. The reviewer inspected this correction. The coordinator reported that the added case passed with dispatch verification enabled in both draft and frozen phases. Grant, report, and typed-parent checks were unchanged. F1 is closed.

## Supported conclusions

- The legacy arm still requires `AUTHORIZATION_READY`. A current authorization-readiness subject requires that same result; `ENTRY_READY` is accepted only for current spend-readiness.
- Spend-readiness re-derives the semantic projection from verified retained bytes using the existing adapter. It requires the projection to match and to contain the original target, answer, and adoption basis. That adapter rejects exact-only targets, mismatched decisions or targets, nonaffirmative or conditional answers, missing answer text, unadopted results, and changed original target or answer bytes.
- The helper requires the reviewed plan to equal the dispatch plan. It also requires the exact report bytes to occur in the attested review content and checks the report's review identifier, decision root, and `ENTRY_READY` result.
- The surrounding verifier continues to bind the report content to the attestation, the attestation to the exact decision, the authority to that decision and attestation, and execution to that authority. The existing identity, content-root, execution-verification, baseline, and live frozen-input checks remain in the path.
- This repair does not infer permission from readiness. Whether the retained grant actually covers the current action, cumulative resources, access, effects, withdrawal, and stop conditions remains the independent Entry reviewer's judgment and the existing consequence checks. The result validator does not establish those live or natural-language facts itself.

## Test evidence and limits

The coordinator reported an exit-zero run of the following command: 32 tests passed, consisting of 17 new parametrized result-readiness cases and 15 existing user-decision-reuse cases.

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -B -m pytest -q \
  -p no:cacheprovider --noconftest \
  .agents/skills/frontier-optimization/scripts/test_result_spend_readiness.py \
  .agents/skills/frontier-optimization/scripts/test_user_decision_reuse.py
```

The new cases use complete typed fixtures and call result validation with dispatch verification enabled. They cover current spend-readiness, current authorization-readiness, legacy authorization-readiness, missing grant basis, stage/result mismatches, mismatched report decision/review/result metadata, and an unattested report. Both draft and frozen publication are covered.

The coordinator additionally reported three directly affected existing tests passing with exit zero:

- `test_current_project_dispatch_validates_end_to_end_in_draft_and_frozen_phases`
- `test_current_project_dispatch_rechecks_live_frozen_inputs_in_both_phases`
- `test_legacy_project_dispatch_validates_complete_v3_chain_end_to_end`

After the F1 correction, the coordinator ran only the added uppercase-suffix case, selecting `test_result_spend_readiness.py -k 'round_trip and True'` with the same isolated pytest options. It passed with exit zero. Across these runs, 36 focused cases passed; this was not a full rerun of all cases after the one-line correction. The reviewer did not independently rerun tests. No broader regression or live-project readiness claim is made.

## Reviewed file hashes

These hashes identify the inspected working-tree files, not approval of unrelated changes within them.

- `scripts/validate_batch_result.py`: `sha256:be995d832e2bee54b0a1d33b66fa2fab3aea715da957fe0e5ebb3c13b3d93b92`
- `scripts/test_validate_batch_result.py`: `sha256:e8bb1208c3a773c4f742400692f19af631f1e1d9ea3b35709aaeb29e17c87687`
- `scripts/test_result_spend_readiness.py`: `sha256:d05d59c288b7873472e693474011c608f2f6ed7be4918ba4b5cb5a143bf95a97`
