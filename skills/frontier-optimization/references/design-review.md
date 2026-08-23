# Frontier Design Review

Load only when freezing a `module` or `system` design, invoking `review-frontier` with `review_kind: design`, or validating its artifact. `direct` has no design review.

Create the packet after `design-implementation` has completed the professional Design brief and applicable concern bodies, and the Coordinator has mechanically completed W maps, traceability, identities, repository evidence, design-choice V records, and planned-slice bindings. Every new design-contract identity requires a new immutable snapshot and fresh-context review. Use a new path per attempt and preserve nonpositive reviews. Include no expected verdict, suspected defect, or proposed repair.

## Review method

1. Verify parents, reviewed scope, route, repository evidence, W revision, design-contract identity, profile, every indexed concern identity, normalized traceability identity, V, and planned slice.
2. Check the profile against task and repository facts. Require every triggered concern and reject any concern that W does not index. W remains a short brief and map; `design-implementation` owns professional meaning once in the Design brief and applicable concern bodies, while Coordinator fields remain mechanical or lifecycle-only.
3. Review applicable architecture, responsibilities, dependencies, integration placement, domain meaning, state ownership, lifecycle, invariants, interfaces, callers, runtime data and control flow, failures, recovery, migration, compatibility, rollback, replacement boundaries, and any human-input schema, provenance, quality, confidentiality, acceptance, and evidence-only terms.
4. Check technical eligibility before preference. Every user-owned tradeoff needed by a reviewed slice has eligible options, an evidence-bounded recommendation, adopted V, consequences, and reconsideration trigger. Design preference is not development authorization.
5. Trace each behavior to its owning module, interface, flow, and distinguishing verification. Require `verification.md` to own each technical slice's behavior, blocking dependencies, design inputs, oracle, failure checks, and recovery point. Require the Coordinator-generated Delivery map and machine-readable traceability file to bind those exact pointers to B identifiers and repository-relative evidence destinations without semantic drift. Each code-bearing B delivers one observable vertical slice and reads only exact required inputs.
6. Perform a cold-read implementation check. Return a finding if a developer must invent entity meaning, responsibility, interface contract, state owner, runtime transition, failure response, user value decision, test oracle, or slice boundary. An executor choice passes only when a concern labels and bounds it.
7. Apply [decisive feasibility](technical-design.md#test-decisive-feasibility-claims). Identify every unestablished, falsifiable claim that determines whether the complete slice can be delivered, starting with the weakest. Attack its positive grounds by seeking a counterexample or checking the claimed end-to-end realization under the same relevant conditions and acceptance meaning. Do not enumerate non-blocking risks, but do not return `DESIGN_READY` while another decisive claim remains unresolved.
8. Return exactly `DESIGN_READY`, `DESIGN_REPAIR_REQUIRED`, `EVIDENCE_REQUIRED`, `PARENT_REVIEW_REQUIRED`, or `BLOCKED`. A positive result has no finding and no unresolved item blocking the reviewed slice.

Use `DESIGN_REPAIR_REQUIRED` when the reviewed design itself shows a conflict, omits a required capability, or lacks a complete realization that design revision can supply. Use `EVIDENCE_REQUIRED` only when current grounds are insufficient and one lower-consequence observation is affordable, reachable, and capable of changing the verdict. Use `DESIGN_READY` only when every decisive claim has positive, reviewable grounds for a credible end-to-end realization; ordinary implementation risk may remain. When no lower-consequence observation exists, do not treat that absence as readiness and do not create a recursive evidence gate: decide from the current grounds, return the parent-owned formal-risk boundary, or return the exact blocker when no legal path remains. A future acceptance plan, internal consistency, or negative examples alone are not feasibility evidence.

`DESIGN_READY` means only that the exact reviewed design is technically ready. Coordinator adoption records that verdict; neither the verdict nor its adoption authorizes candidate development. Development starts only after fresh `AUTHORIZATION_READY`, a separate user authorization V, and finding-free Coordinator adoption validation bind the exact design-contract identity and affected code-bearing scope.

A nonpositive review changes no design content. The Coordinator scopes a new revision and returns the complete findings to `design-implementation`; the designer repairs professional content, and the Coordinator regenerates only its mechanical bindings before another review. Introducing this authoring role does not invalidate or reopen an existing unchanged finding-free `DESIGN_READY` design.

## Packet

```yaml
review_kind: design
review_id: <unique identifier>
packet_path: <frontier/reviews/design-<review-id>-packet.yaml>
packet_id: <review kind and id plus SHA-256 of canonical packet bytes with this field omitted>
snapshot_manifest: <frontier/reviews/design-<review-id>-project-snapshot.yaml and identity>
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
- Cold-read implementability, decisive feasibility, and lifecycle boundaries: <pass or findings>

## Findings

### Finding 1: <omit when DESIGN_READY>

- Result effect: <DESIGN_REPAIR_REQUIRED | EVIDENCE_REQUIRED | PARENT_REVIEW_REQUIRED | BLOCKED>
- Affects: <W/design pointers, records, fields, or slices>
- Requirement: <exact requirement>
- Observed: <snapshot fact>
- Evidence: <snapshot identities>
- Required correction: <observable condition; no repair text>
```
