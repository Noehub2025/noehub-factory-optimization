# Restriction drift repair verification

Date: 2026-10-05. Scope: installed Workflow rules, the optional portable Harness,
and isolated synthetic work in the source installation. This inherited record
retains that review and its observations; the model work samples were not rerun
during distribution migration. Distribution checks are reported separately.
This record does not change a consuming campaign, its historical observations,
resource allocations or running workers.

## Problems and changes

| Issue | Change | Evidence boundary |
| --- | --- | --- |
| P1: technical choices acquire user/environment authority | The common worker rules inspect owner-written restrictions in the local objective and menu; prior adoption and agreement do not prove their basis | Fresh first-delegation preparation corrected a dictionary-only question while retaining real limits |
| P2: local conditions become development-wide | First writing and summarization preserve the affected stage/use; Technical design requires grounds for extension | Fresh recovery separated final offline delivery from development methods and preserved a valid paired-experiment control |
| P3: temporary defaults become permanent | Existing recovery distinguishes original errors, changed conditions and still-valid choices before an unchanged shortcut | Recovery corrected an old scope error without a new result; changed-scale preparation retained uncertainty and chose a reachable observation |
| P4: summaries lose qualifications | The common rule is reachable from Frame, research, direct Working assignments and resolver policy | A staged history with successive paraphrases was supplied to a fresh receiver; generation of those earlier paraphrases was not itself observed |
| P5: the body changes but the active header does not | An existing-owner correction can update objective/constraints and assignment together, preserving omitted values and execution controls | Real Session and CLI regressions pass for header-only differences, persistence, recovery and rejection of started work; independent recheck passed |
| P6: checks are mistaken for judgment | Complete delivery, known-finding enforcement and semantic recognition are tested separately; documentation states each coverage limit | Fresh model work samples and mechanical fixtures are separate evidence, not an end-to-end live campaign trial |

No restriction registry, routine review call, approval stage, alternative-method
win requirement or historical migration was introduced. Rules apply to
consequential restrictions, not every debugging choice. Valid experiment
conditions, internal resource reservations and incurred effects remain binding.

## Independent review and repair

The rule reviewer found that the initial first-writing wording could include
every implementation choice. It was narrowed to consequential restrictions.
An adjacent research instruction was merged into its existing question step,
and policy wording permits an internal technical basis without demanding an
external source for every choice.

The runtime reviewer reproduced a new bypass in the first implementation:
changing only the task header could reuse an enforced judgment when assignment,
actual-use paths and file sources were unchanged. An isolated failing test reproduced this bypass in the source audit. Its
portable regression remains in `tests/decision.rs`. The implementation was repaired: the existing judgment projection now includes the objective and
constraints as `task_header`, outside source indices. Enforced header correction
returns the existing Coordinator for explicit applicability reuse or the normal
judgment path before a new Worker. Earlier Resolver/external judgments do not
automatically acquire the new header. Legacy checkpoints can consume their old
judgment only when the adopting Coordinator's actual saved request proves the
same header; missing or conflicting evidence has a supported owner recovery
path. Valid unchanged legacy replacement adds no owner round trip, and its next
adoption can reuse applicable reasoning without an additional checker.

The original reviewer independently reran six header regressions and the
checkpoint-after-write failure regression, all passing, and reported no
remaining must-fix issue. This closes the reproduced association defect, not
the semantic correctness of any future owner's applicability reason.

## Fresh-context work samples

The executors received raw goals and records, permitted local write surfaces,
and the shared installed instructions. They did not receive the expected answer,
suspected defect or proposed fix. These are single synthetic samples, with no
before/after control population or estimate of reliability.

Total elapsed effort, context use and audit cost were not completely measured;
these samples cannot establish a net research-efficiency improvement.

1. **No-result recovery and valid-control pair.** The source exercise used a
   disposable local workspace.
   The executor corrected an inherited browser-only/two-record restriction in
   `working-plan.md`, created `build_report.py`, and consumed all six records in
   `report.html`. Python construction and independent Node arithmetic checks
   produced parts 22, services 9, tools 9, total 40. The separate comparison's
   browser version, six inputs, seed 17 and ten repetitions remained fixed;
   no comparison ran because its second arm was missing. Goal, history,
   comparison and input source hashes were unchanged. A headless browser attempt
   failed with exit 134 and no DOM output; rendering was not verified and was
   not reported as a report defect or a new development restriction.
2. **First delegation with a larger available corpus.** The source exercise used
   a separate disposable local workspace.
   The executor wrote `work.md` around local retrieval quality over the available
   80,000 documents, rather than the encoding smoke check's dictionary and ten
   records. It preserved 512 MiB, no uploads/paid services and offline lookup.
   It selected a streaming size/memory observation, retaining unknown index
   feasibility and missing relevance judgments. This sample demonstrates adopted
   task preparation, not execution of the research or better search quality.

The raw cases and expected checks are maintained in
[restriction-drift-cases.md](restriction-drift-cases.md). Temporary workspaces
are local evidence and may be removed later; the case descriptions retain the
inputs and interpretation needed to reproduce the exercises.

## Validation and deployment

Python source-delivery and bundle regressions: 141 passed. Skill metadata checks
passed for Frame, Frontier and research-optimization. The final changed-file
check resolved 266 local Markdown links, including section anchors. Mechanical
results do not certify semantic correctness.

Rust full suite: 128 passed, including 77 decision tests. Subsequent enhancements
to the real CLI and legacy same-turn reuse assertions passed in targeted reruns;
production code did not change after the full run. `cargo fmt --check` and
`git diff --check` passed. The original reviewer separately repeated the seven
regressions described above.

Both local release binaries were rebuilt at
`tools/workflow-harness/target/release/workflow-harness` and
`tools/workflow-harness/target/release/workflow-codex-hook`, the existing
launcher's preferred paths. No target-directory override was used. The real CLI
correction regression also passed against the release binary:

```sh
cargo build --offline --locked --release \
  --manifest-path tools/workflow-harness/Cargo.toml \
  --bin workflow-harness --bin workflow-codex-hook
cargo test --offline --locked --release \
  --manifest-path tools/workflow-harness/Cargo.toml \
  --test decision host_cli_corrects_task_header_and_rejects_started_or_invalid_updates
```

This repair did not restart a live session, rewrite a pending business request,
rerun a candidate or perform an external submission. Actual adoption of these
Workflow changes by existing workers and improved project
efficiency remain unverified. Concurrent business progress is separate evidence;
it is not attributed to this Workflow repair.
