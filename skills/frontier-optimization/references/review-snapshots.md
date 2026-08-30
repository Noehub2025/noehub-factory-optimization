# Fixed review inputs

> Historical compatibility reference. A current review uses one full Git commit, explicit subject paths, and one R through `review-frontier`. Load this file only when a retained review actually contains a review-subject index, decision node, packet, snapshot manifest, or attestation.

Storage, working-copy behavior,
large artifacts, and historical continuation are owned by
[Provenance, Git, and retained artifacts](provenance-and-identity.md).

## Prepare a complete subject

Use `prepare_review` or `frontier_review_cli.py` for new reviews. Supply the
review kind, complete required project files, closed collections, and Entry
stage when applicable. Validate and repair the mutable draft before allocating
a review. Save the selected version in normal Git history when it is ready to
be fixed.

Preparation derives the consequence projection from the actual project
objects. It references their saved Git paths and publishes the generated
subject index, decision node, packet, and assignment together. The historical
directory name `snapshot` now contains a small Git-reference manifest, not a
copy of the project. Reuse saved input versions between reviews.

The `frontier-review-subject/2` index contains the complete logical member set,
closed collections, review kind, and derived semantic projection. It has no
independent identity. A partial patch, correction overlay, or caller-written
summary cannot replace the required subject. The review's file set is complete
for its decision, not for the whole repository.

## Review and use

The reviewer reads the exact referenced version and judges the assigned
decision. Working edits made afterward do not alter that version. A positive
review applies to its fixed content and stated assumptions, not automatically
to later edits.

Bind the finding report and attestation to that decision. At a later action,
check the exact review binding and the action's current requirements. Reuse
content already verified in that operation; do not derive the same semantic
projection again merely to read or acknowledge unchanged evidence.

A review covers project facts, not installed Skills, validators, workflow
tests, or release bytes. Follow the current method without changing previously
saved project identities.

## Completion

A review is ready when its required selected inputs are retrievable, the
complete subject has passed preparation, and the packet assigns one review
kind and output path. An ordinary Entry checks the selected work, prerequisites,
budget, effects, stop conditions, and directly required engineering evidence.
Workflow regression and release checks remain outside project Entry.

Keep existing valid reviews and active chains on their retained storage.
Storage changes alone trigger no new B, reviewer, answer, or authorization.
Historical semantic versions already restricted to audit remain so.
