---
name: review-frontier
description: Review one exact Git-backed Frontier Entry, strategic replan, technical design, implementation revision, or claim set in a fresh context. Use only when frontier-optimization supplies the review kind, full Git commit, subject paths, R handle and path, applicable parents, and completion check.
---

# Review Frontier

Review one saved project subject independently and write one R. R is the only current review record; it is not a permission credential or execution identity. Do not repair, research, reselect, ask the user, recommend a Coordinator route, or adopt campaign state.

## Select one review branch

1. Require `review_kind: entry | replan | design | implementation | claims`, one full Git commit, explicit repository-relative subject paths, one R handle and output path, applicable parent handles, and a completion check. The subject must contain every fact needed by the selected review, but it does not need a content root, closed-collection identity, packet, snapshot, decision node, or attestation node.
2. Resolve the commit and paths through [Provenance and Git](../frontier-optimization/references/provenance-and-identity.md). Return `BLOCKED` only when a required subject path, parent, or external artifact cannot be retrieved or is internally inconsistent. A later working-copy change does not alter the saved subject.
3. Match `review_kind` to exactly one row in the [review branch registry](../frontier-optimization/references/review-branches.md). Load only that method and supporting material triggered by the subject.
4. Apply the selected method to the saved project facts. For a correction, inspect the saved diff, changed dependencies, and affected conclusions; do not repeat unaffected work merely because the commit changed.

An installed workflow update never changes the historical subject or verdict. Apply current review rules to the next review without making workflow files, validators, bundle versions, or deployment paths part of the project subject.

Historical review packets, snapshots, content roots, and typed provenance remain readable only when the retained R actually uses them. Do not generate or backfill those fields for current work.

## Preserve review independence

Check source artifacts, not only summaries. Apply [Finding effects](../frontier-optimization/references/finding-effects.md). Cite the Git subject path and relevant content for every block, repair, advisory, and checked positive result. Do not return a positive verdict while a block or repair remains open. Keep advisories separate from readiness, strength, validity, progress, and constraint conclusions. Do not turn user preference into technical proof or let one review substitute for another decision.

Each finding states the existing requirement, observed violation, affected consequence, and recovery condition. Accept any repair that satisfies the requirement. An optional suggestion is not a new requirement, and a method difference is not a defect by itself.

Write only the assigned R artifact with:

- R handle and review kind;
- subject Git commit and paths;
- applicable parent handles;
- verdict and checked conclusions;
- findings and advisories;
- reviewer and assumptions;
- maximum supported consequence; and
- recovery condition when nonpositive.

Do not edit the subject, Campaign, Selection, Batch, Budget, V, E, W, or claims. The Coordinator decides adoption and the next stage. Review completion means the selected method has evidence-backed conclusions and the R artifact passes its ordinary completion check. Reuse checks the prior R's actual subject and assumptions; it does not transfer an attestation or authority node.
