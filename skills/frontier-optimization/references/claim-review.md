# Frontier Claim Review

Load only when creating a claims-review packet, invoking `review-frontier` with `review_kind: claims`, or validating its artifact.

## Review method

For every C, verify exact wording and intended use; current parents and reviews; F8; applicable reflection and replan lineage; candidate identity; design, user authorization, and implementation-review lineage; legality and engineering evidence; Slot H measurement; Slot D comparison; Slot E uncertainty; R8 meaning; bound authority; gap arithmetic; and later dispositions.

Return exactly `CLAIMS_SUPPORTED`, `CLAIMS_DOWNGRADED`, `EVIDENCE_REQUIRED`, `PARENT_REVIEW_REQUIRED`, or `BLOCKED`. A positive result has no finding. Every nonpositive result identifies the affected C, decisive evidence, and required action. A downgrade supplies exact maximum supported wording.

## Packet

Supply the canonical task path; project-snapshot manifest and identity; exact C identifiers, wording, and intended use; current parent bindings and Frontier scope; `FRONTIER.md`; cited Generation Reflections or legacy Outcome Reflections and replans; Q/E/D/X and earlier applicable A records; cited W and B; design-review and authorization lineage; candidate manifests and implementation reviews; engineering and measurement evidence; exact F8 and R8 sources; applicable Slots D, E, and H; module contracts; search-state dispositions; and one exclusive review path. Every cited project input must appear in the snapshot manifest and remain immutable during review.

```yaml
review_kind: claims
review_id: <unique identifier>
packet_path: <frontier/reviews/claims-<review-id>-packet.yaml>
packet_id: <review kind and id plus SHA-256 of canonical packet bytes with this field omitted>
snapshot_manifest: <frontier/reviews/claims-<review-id>-project-snapshot.yaml and identity>
snapshot_id: <immutable snapshot identity>
task_path: <canonical task path>
problem_epoch: <integer>
problem_generated_at: <ISO-8601 datetime>
representation_revision: <integer>
representation_generated_at: <ISO-8601 datetime>
representation_permitted: <exact reviewed text>
claim_branch_mode: <claim-only | full-closeout>
campaign_status_at_trigger: <planned | running | stopped | halted>
claims: [<C identifier, immutable identity, exact wording, intended use, and scope>]
supporting_evidence: [<reflection, replan, Q, E, D, X, A, W, B, design, authorization, candidate, implementation, engineering, measurement, Slot, or module-contract identity>]
assigned_review_path: <exclusive immutable claims-review artifact path>
completion_check: <every C receives an allowed result and every finding cites immutable snapshot evidence>
```

## Artifact

Only `review-frontier` writes the assigned claims-review artifact. The Coordinator adopts every finished result through A, including a nonpositive result. If the user withdraws the request before review finishes, the Coordinator appends a withdrawing X instead. A or X ends that C's routing branch; only explicitly supported A wording may be used externally.

```markdown
---
type: Optimization Frontier Claims Review
status: complete
review_id: <identifier>
review_result: <CLAIMS_SUPPORTED | CLAIMS_DOWNGRADED | EVIDENCE_REQUIRED | PARENT_REVIEW_REQUIRED | BLOCKED>
reviewed_by: review-frontier/1
reviewed_at: "<ISO-8601 datetime>"
snapshot_packet: <path and identity>
generated: { by: review-frontier/1, at: "<ISO-8601 datetime>" }
---

# FRONTIER CLAIMS REVIEW: <effort name>

Result: <allowed result>
Claims: <exact C identifiers>
Intended use: <exact external use>
Reviewed records: <paths and identifiers>
Reviewed at: <ISO-8601 datetime>

## Claim under review: <C identifier and name>

- Claim: <exact reviewed wording>
- Result: <supported | downgrade | evidence required | parent review required | blocked>
- Decisive authority: <records and authority>
- Maximum supported wording: <exact wording or unchanged>
- Required action: <one action or None>
- Complete when: <checkable condition or complete>
```

The reviewer writes no A or X, changes no campaign status, and grants no wording authority directly. `CLAIMS_DOWNGRADED` supplies exact maximum supported wording; `EVIDENCE_REQUIRED`, `PARENT_REVIEW_REQUIRED`, and `BLOCKED` supply no usable wording. The Coordinator validates and records the consequence from durable state.

A claims review binds exact C and evidence identities. Later unrelated campaign records do not stale it. A later X that invalidates, supersedes, voids, or withdraws cited evidence makes the dependent wording unusable. A semantic wording change creates a new C and requires a new review. Never promote an old nonpositive review into approval.
