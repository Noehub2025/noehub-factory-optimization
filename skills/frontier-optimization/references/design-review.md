# Frontier Design Review

Load only when freezing a `module` or `system` design, invoking `review-frontier` with `review_kind: design`, or validating its artifact. `direct` has no design review.

Create the packet after W, applicable concerns, repository evidence, design-choice V records, and planned slices are complete. Every new design-contract identity requires a new immutable snapshot and fresh-context review. Use a new path per attempt and preserve nonpositive reviews. Include no expected verdict, suspected defect, or proposed repair.

## Review method

1. Verify parents, reviewed scope, route, repository evidence, W revision, design-contract identity, profile, every indexed concern identity, normalized traceability identity, V, and planned slice.
2. Check the profile against task and repository facts. Require every triggered concern and reject any concern that W does not index. W remains a short brief and map; detailed meaning has one owning concern.
3. Review applicable architecture, responsibilities, dependencies, integration placement, domain meaning, state ownership, lifecycle, invariants, interfaces, callers, runtime data and control flow, failures, recovery, migration, compatibility, rollback, replacement boundaries, and any human-input schema, provenance, quality, confidentiality, acceptance, and evidence-only terms.
4. Check technical eligibility before preference. Every user-owned tradeoff needed by a reviewed slice has eligible options, an evidence-bounded recommendation, adopted V, consequences, and reconsideration trigger. Design preference is not development authorization.
5. Trace each behavior to its owning module, interface, flow, and distinguishing verification. Require the machine-readable traceability file to list every slice's exact required design inputs and repository-relative evidence destinations. Each code-bearing B delivers one observable vertical slice, reads only exact required inputs, names real blocking edges, and preserves a recovery point.
6. Perform a cold-read implementation check. Return a finding if a developer must invent entity meaning, responsibility, interface contract, state owner, runtime transition, failure response, user value decision, test oracle, or slice boundary. An executor choice passes only when a concern labels and bounds it.
7. Return exactly `DESIGN_READY`, `DESIGN_REPAIR_REQUIRED`, `EVIDENCE_REQUIRED`, `PARENT_REVIEW_REQUIRED`, or `BLOCKED`. A positive result has no finding and no unresolved item blocking the reviewed slice.

`DESIGN_READY` means only that the exact reviewed design is technically ready. Coordinator adoption records that verdict; neither the verdict nor its adoption authorizes candidate development. Development starts only after fresh `AUTHORIZATION_READY`, a separate user authorization V, and finding-free Coordinator adoption validation bind the exact design-contract identity and affected code-bearing scope.

## Packet

```yaml
review_kind: design
review_id: <unique identifier>
packet_path: <frontier/reviews/design-<review-id>-packet.yaml>
packet_id: <review kind and id plus SHA-256 of canonical packet bytes with this field omitted>
snapshot_root: <frontier/reviews/design-<review-id>-snapshot/>
snapshot_manifest: <snapshot_root/manifest.yaml and identity>
snapshot_id: <immutable snapshot identity>
task_path: <canonical task path>
problem_epoch: <integer>
problem_generated_at: <ISO-8601 datetime>
representation_revision: <integer>
representation_generated_at: <ISO-8601 datetime>
representation_permitted: <exact reviewed text>
work_plan: <W path, plan revision, and design contract identity>
design_profile: <module | system>
design_map: [<each applicable concern, exact pointer, identity, trigger, and read condition>]
design_traceability: <exact traceability path, normalized identity, batches, required inputs, and evidence destinations>
design_choice_records: [<V identifiers and identities, or none>]
planned_slices: [<Delivery rows with B identifiers, observable delivery, blocking edges, and design inputs>]
repository_evidence: [<paths and identities>]
snapshot_inputs: <exact snapshot_manifest#inputs reference; do not duplicate the array>
assigned_review_path: <frontier/reviews/design-<review-id>.md>
completion_check: <every applicable design requirement receives a verdict and every finding cites immutable evidence>
```

## Artifact

Only `review-frontier` writes the assigned file.

```markdown
---
type: Optimization Frontier Design Review
status: complete
review_id: <identifier>
review_result: <DESIGN_READY | DESIGN_REPAIR_REQUIRED | EVIDENCE_REQUIRED | PARENT_REVIEW_REQUIRED | BLOCKED>
reviewed_by: review-frontier/1
reviewed_at: "<ISO-8601 datetime>"
snapshot_packet: <path and identity>
work_id: <W identifier>
plan_revision: <integer>
design_contract_identity: <immutable identity>
generated: { by: review-frontier/1, at: "<ISO-8601 datetime>" }
---

# FRONTIER DESIGN REVIEW: <work name>

Result: <allowed result>
Work plan: <W path, revision, and design contract identity>
Reviewed snapshot: <packet path and identity>
Reviewed at: <ISO-8601 datetime>
Maximum consequence: technical design readiness for the exact snapshot only; no development authorization

## Readiness checks

- Parent, route, scope, and repository evidence: <pass or findings>
- Design profile and concern coverage: <pass or findings>
- W brief, map, pointer precision, and single-source ownership: <pass or findings>
- Architecture, responsibilities, dependencies, and integration: <pass or findings>
- Domain entities, state, lifecycle, and invariants: <pass, not applicable, or findings>
- Interfaces, callers, contracts, and test seams: <pass or findings>
- Runtime, data, failure, and recovery flows: <pass or findings>
- Technical decisions, V records, and open ownership: <pass or findings>
- Human input contract and evidence-only boundary: <pass, not applicable, or findings>
- Verification traceability, slices, blocking edges, and recovery: <pass or findings>
- Cold-read implementability and lifecycle boundaries: <pass or findings>

## Findings

### Finding 1: <omit when DESIGN_READY>

- Result effect: <DESIGN_REPAIR_REQUIRED | EVIDENCE_REQUIRED | PARENT_REVIEW_REQUIRED | BLOCKED>
- Affects: <W/design pointers, records, fields, or slices>
- Requirement: <exact requirement>
- Observed: <snapshot fact>
- Evidence: <snapshot identities>
- Required correction: <observable condition; no repair text>
```
