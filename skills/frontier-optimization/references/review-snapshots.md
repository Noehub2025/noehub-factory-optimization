# Frontier Review Snapshots

Load before freezing, reviewing, validating, or adopting any review packet. This file is the sole contract for immutable review inputs.

## Snapshot bundle

Create one new directory per review attempt:

```text
frontier/reviews/<kind>-<review-id>-snapshot/
├── manifest.yaml
└── inputs/<source-relative copies>
```

Never overwrite or reuse a snapshot directory.

The Coordinator copies every mutable evidence input needed by the verdict into `inputs/` byte for byte. Mutable inputs include parent concept documents, reviews, `FRONTIER.md`, ledger sections, W, design concerns, worker results, manifests that may be rewritten, and mutable source/configuration files.

Also copy every normative workflow source whose rules the verdict must reconcile. An authorization-readiness Entry snapshot always includes Campaign Cycle, Batch Interface, Worker Interfaces, the batch, Entry, authorization-adoption, execution-baseline, and result validators, the selected B packet, structural preflight, W traceability when applicable, exact proposed authorization target, and proposed state transition. The reviewer must be able to prove semantic readiness before the user is asked. A materialization implementation snapshot includes the exact workflow-contract and validator versions bound by the executed packet plus structural preflight, authorization-readiness review, user V, adoption artifact, frozen adoption validation, execution-baseline manifest and bytes, execution-start, finding-free result validation, and final result; never reinterpret an old packet through newer live Skill text. A later live `FRONTIER.md`, ledger, or log is current-state evidence only and cannot replace a baseline snapshot copy. A `recovery-reuse` implementation snapshot includes both historical contracts and current recovery authority.

A stable content-addressed artifact may remain outside the bundle only when all are true:

- its path is durable under repository policy;
- its content identity is cryptographic and recorded;
- no workflow step may overwrite that path;
- the reviewer can read it during review and a future audit.

Otherwise copy it. A Git commit, branch, worktree, conversation, or hash without recoverable bytes is not a snapshot.

## Manifest

```yaml
snapshot_id: <kind-review-id and SHA-256 of the canonical manifest bytes with this field omitted>
review_kind: <entry | replan | design | implementation | claims>
created_at: <ISO-8601 datetime>
created_by: frontier-optimization/1
source_state: <read-only description of the live state being frozen>
inputs:
  - source_path: <original canonical path or record section>
    snapshot_path: <byte-identical path under inputs, or null only for an allowed stable artifact>
    sha256: <content identity>
    stability: <snapshot-copy | stable-content-addressed>
    required_use: <why the verdict needs it>
```

Compute and record every input identity, serialize the manifest canonically without `snapshot_id`, compute its SHA-256, then insert the resulting `snapshot_id`. The review packet cites `snapshot_root`, `snapshot_manifest`, and `snapshot_id`; `snapshot_inputs` points to the manifest's exact `inputs` array instead of copying it. Validation repeats the same omit-hash-insert procedure, so the identity is not self-referential and the packet cannot drift from a duplicated input list.

Create the versioned review packet only after `snapshot_id` resolves. Include `packet_id`, defined as the review kind and identifier plus SHA-256 of the canonical packet bytes with the `packet_id` field omitted. Then never overwrite its path. The packet is the assignment that points to the evidence bundle; it is not an evidence input inside its own manifest. The review artifact cites both packet identity and snapshot identity and repeats the omit-hash-insert validation. A changed assignment requires a new packet, snapshot directory, and review identifier.

## Validation and adoption

The reviewer reads mutable evidence only from snapshot copies and verifies all identities before interpreting content. It may compare live state only to determine whether the packet is stale; live bytes never replace snapshot evidence.

The Coordinator adopts a positive verdict only when:

- packet, manifest, snapshot directory, review artifact, and every external stable artifact still resolve;
- the live inputs whose meaning controls the next action still match the snapshot identities;
- no finding remains open;
- the recorded-state router permits the consequence.

After `AUTHORIZATION_READY`, the only permitted pre-dispatch writes are the exact reviewed user-result path, V adoption, Entry-adoption artifact and validation, the exact reviewed Budget and Selection transition after validation, and required lifecycle-log append. The Coordinator must prove byte-for-byte target identity, unchanged live inputs, answer fidelity, and exact reviewed state effects. A condition or any change to scope, path, spend, stop boundary, W contract, packet, source, authority, or proposed state returns `REVIEW_REQUIRED`. Never mutate W to record authorization.

After the frozen adoption validator accepts `ENTRY_READY`, the Coordinator applies only the reviewed Budget and Selection transition. The only later pre-execution edit is the exact `campaign_status: planned -> running` transition encoded in the reviewed B packet after acknowledgment. The Coordinator proves its exact pre- and post-change identities in the execution-start record. Any additional action-controlling change invalidates dispatch authority.

For `review_kind: claims`, validate and disposition every finished artifact through A even when the result is `EVIDENCE_REQUIRED`, `PARENT_REVIEW_REQUIRED`, or `BLOCKED`. This records the terminal claim result; it does not adopt a positive consequence or authorize wording. A pre-completion withdrawal uses X instead.

Preserve every positive and nonpositive packet, snapshot bundle, and review artifact. Cleanup may remove none of them while a retained record cites the review.
