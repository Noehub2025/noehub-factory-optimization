# Frontier Design Review

Load only when freezing a `module` or `system` design, invoking `review-frontier` with `review_kind: design`, or validating its artifact. `direct` has no design review.

Create the packet after `design-implementation` has completed the professional Design brief and applicable concern bodies, and the Coordinator has mechanically completed W maps, traceability, identities, repository evidence, design-choice V records, and planned-slice bindings. Every new design-contract identity requires a new immutable snapshot and fresh-context review. Use a new path per attempt and preserve nonpositive reviews. Include no expected verdict, suspected defect, or proposed repair.

## Review method

1. Verify parents, reviewed scope, route, repository evidence, W revision, design-contract identity, profile, every indexed concern identity, normalized traceability identity, V, and planned slice.
2. Check the profile against task and repository facts. Require every triggered concern and reject any concern that W does not index. W remains a short brief and map; `design-implementation` owns professional meaning once in the Design brief and applicable concern bodies, while Coordinator fields remain mechanical or lifecycle-only.
3. Apply [Technical design's assignment ownership rule](technical-design.md#assign-the-professional-author) before reviewing completeness. Ignore incidental workflow background. If a method owned by Batch is nevertheless normative, return at most one root `scope` finding for that mechanism and do not derive receipt, owner, schema, digest, failure, or recovery findings from it. Missing immutable ownership for reversible, unpublished working material is not a finding. Continue reviewing unrelated technical content.
4. Review applicable architecture, responsibilities, dependencies, integration placement, domain meaning, state ownership, lifecycle, invariants, interfaces, callers, runtime data and control flow, failures, recovery, migration, compatibility, rollback, replacement boundaries, and any human-input schema, provenance, quality, confidentiality, acceptance, and evidence-only terms.
5. Check technical eligibility before preference. Every user-owned tradeoff needed by a reviewed slice has eligible options, an evidence-bounded recommendation, adopted V, consequences, and reconsideration trigger. Design preference is not development authorization.
6. Trace each behavior to its owning module, interface, flow, and distinguishing verification. Require `verification.md` to own each technical slice's behavior, stable prerequisites, design inputs, oracle, failure checks, and recovery point. Require the Coordinator-generated Delivery map and machine-readable traceability file to bind those exact pointers to stable slice identities without future B assignment, attempt namespace, internal evidence destination, or runtime status. A path remains in Design only when a real caller or operator outside the current B or attempt depends on it as a stable interface.
7. Review any implementation-form restriction that materially affects the current slice. Require a current protection rationale tied to a named behavior, interface, invariant, risk, or verification property and its causal relation. A finding may cite the missing or contradicted rationale, or one concrete Design-compatible realization showing infeasibility or material extra complexity without such a rationale. Do not require proof of the narrowest possible rule, exhaustive alternatives, absolute safety, or absence of value in every setting; a non-impacting restriction is at most advisory.
8. Perform a cold-read implementation check. Return a finding if a developer must invent entity meaning, responsibility, interface contract, state owner, runtime transition, failure response, user value decision, test oracle, or slice boundary. Apply the assignment ownership rule to distinguish missing technical meaning from ordinary work methods; the latter need no prior enumeration in a concern.
9. Apply [decisive feasibility](technical-design.md#test-decisive-feasibility-claims) to the promised output, including its distinction between a research hypothesis and an action prerequisite. Check the weakest decisive claim against its evidence and relevant conditions. Judge whether a research observation can be delivered and interpreted, not whether its hypothesis will succeed; full delivery retains its acceptance obligations.
10. Return exactly `DESIGN_READY`, `DESIGN_REPAIR_REQUIRED`, `EVIDENCE_REQUIRED`, `PARENT_REVIEW_REQUIRED`, or `BLOCKED`. A positive result has no finding and no unresolved item blocking the reviewed slice.

Use `DESIGN_REPAIR_REQUIRED` for a conflict or missing capability that design revision can resolve. For insufficient grounds, apply Technical design's evidence-routing rule; use `EVIDENCE_REQUIRED` only for the bounded observation it permits. Return `DESIGN_READY` when every decisive claim for the promised output meets that rule; ordinary implementation risk may remain. Otherwise return the existing parent-owned decision or exact blocker.

`DESIGN_READY` establishes technical readiness only; neither the verdict nor adoption grants authority or decides whether a user delegation covers the change. Initial development requires Entry and user authorization. For a later revision, apply [Boundary-preserving continuation](batch-interface.md#boundary-preserving-continuation): the existing execution checks, not the Design reviewer, determine whether the original explicit authorization still applies.

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
design_traceability: <exact traceability path, normalized identity, stable slices, verification pointers, and required design inputs>
design_choice_records: [<V identifiers and identities, or none>]
planned_slices: [<stable Delivery rows with observable delivery, prerequisite edges, verification identities, and design inputs>]
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
