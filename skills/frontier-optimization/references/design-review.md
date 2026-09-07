# Frontier Design Review

Load only when freezing a `module` or `system` design, invoking `review-frontier` with `review_kind: design`, or validating its artifact. `direct` has no design review.

Prepare the saved Git subject after the professional Design brief, applicable concerns, W maps, traceability and needed user choices are complete. Use [W saved references](work-plan.md#saved-design-references); the consuming review owns the commit, not W. Preserve prior reviews and assess changed content under the existing affected-review rule. The assignment contains no expected verdict or proposed repair.

## Review method

1. Read W, indexed concerns and traceability at the assigned Git commit. Verify parents, scope, route, repository evidence, profile, applicable V and selected stable slice keys. Use the current saved-reference checks, not historical packet or snapshot preparation.
2. Check the profile against task and repository facts. Require every triggered concern and reject any concern that W does not index. W remains a short brief and map; `design-implementation` owns professional meaning once in the Design brief and applicable concern bodies, while Coordinator fields remain mechanical or lifecycle-only.
3. Apply [Technical design's assignment ownership rule](technical-design.md#assign-the-professional-author) before reviewing completeness. Ignore incidental workflow background. If a method owned by Batch is nevertheless normative, return at most one root `scope` finding for that mechanism and do not derive receipt, owner, schema, digest, failure, or recovery findings from it. Missing immutable ownership for reversible, unpublished working material is not a finding. Continue reviewing unrelated technical content.
4. Review applicable architecture, responsibilities, dependencies, integration placement, domain meaning, state ownership, lifecycle, invariants, interfaces, callers, runtime data and control flow, failures, recovery, migration, compatibility, rollback, replacement boundaries, and any human-input schema, provenance, quality, confidentiality, acceptance, and evidence-only terms.
5. Check technical eligibility before preference. Every user-owned tradeoff needed by a reviewed slice has eligible options, an evidence-bounded recommendation, adopted V, consequences, and reconsideration trigger. Design preference is not development authorization.
6. Trace each behavior to its owning module, interface, flow, and distinguishing verification. Require `verification.md` to own each technical slice's behavior, stable prerequisites, design inputs, oracle, failure checks, and recovery point. The Delivery map and traceability associate those pointers with stable slice keys. Future B assignments, attempt namespaces, internal evidence destinations and runtime status remain with execution. A path belongs to Design only when a real caller or operator outside the current B depends on it as a stable interface.
7. Apply [Constrain effects, not convenient forms](technical-design.md#constrain-effects-not-convenient-forms) to restrictions that materially affect this slice, including evidence channels and verification methods. Judge the current protection basis, not merely consistency with an inherited precaution; do not inventory unrelated restrictions.
8. Perform a cold-read implementation check. Return a finding if a developer must invent entity meaning, responsibility, interface contract, state owner, runtime transition, failure response, user value decision, test oracle, or slice boundary. Apply the assignment ownership rule to distinguish missing technical meaning from ordinary work methods; the latter need no prior enumeration in a concern.
9. Apply [decisive feasibility](technical-design.md#test-decisive-feasibility-claims) to the promised output, including its distinction between a research hypothesis and an action prerequisite. Check the weakest decisive claim against its evidence and relevant conditions. Judge whether a research observation can be delivered and interpreted, not whether its hypothesis will succeed; full delivery retains its acceptance obligations.
10. For any condition capable of rejecting the implementation or producing a broader disposition, apply [Decision-bearing thresholds](frontier-core.md#decision-bearing-thresholds). Check the current owner and allowed consequence, and check the complete semantic match when Design calls it `unchanged`. Do not re-prove an unchanged threshold or review ordinary observations, planning estimates, diagnostics, or operational limits as if they were Design acceptance.
11. Return exactly `DESIGN_READY`, `DESIGN_REPAIR_REQUIRED`, `EVIDENCE_REQUIRED`, `PARENT_REVIEW_REQUIRED`, or `BLOCKED`. A positive result has no finding and no unresolved item blocking the reviewed slice.

Use `DESIGN_REPAIR_REQUIRED` for a conflict or missing capability that design revision can resolve. For insufficient grounds, apply Technical design's evidence-routing rule; use `EVIDENCE_REQUIRED` only for the bounded observation it permits. Return `DESIGN_READY` when every decisive claim for the promised output meets that rule; ordinary implementation risk may remain. Otherwise return the existing parent-owned decision or exact blocker.

`DESIGN_READY` establishes technical readiness only; neither the verdict nor adoption grants Permission or decides whether a V covers the change. Initial development uses the current Entry decision and applicable V under [User decisions](user-decisions.md), without another answer when existing boundaries apply. For a later revision, apply [Boundary-preserving continuation](batch-current.md#boundary-preserving-continuation): the current owners, not the Design reviewer, determine whether V still applies.

A nonpositive review changes no design content. The Coordinator scopes a new revision and returns the complete findings to `design-implementation`; the designer repairs professional content, and the Coordinator regenerates only its mechanical bindings before another review. Introducing this authoring role does not invalidate or reopen an existing unchanged finding-free `DESIGN_READY` design.

## Assignment

```yaml
review_kind: design
review_id: <R handle>
subject: <tool-produced Git commit and selected paths, including W and its indexed design files>
parents: [<applicable parent references, including separately versioned source evidence when needed>]
delivery_scope: [<selected stable slice keys>]
assigned_review_path: <frontier/reviews/design-<review-id>.md>
completion_check: <every applicable requirement is assessed against the saved subject>
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
subject: <assigned Git reference>
work_id: <W identifier>
plan_revision: <integer>
generated: { by: review-frontier/1, at: "<ISO-8601 datetime>" }
---

# FRONTIER DESIGN REVIEW: <work name>

Result: <allowed result>
Work plan: <W path and revision at the subject commit>
Reviewed subject: <Git commit and paths>
Reviewed at: <ISO-8601 datetime>
Maximum consequence: technical design readiness for the saved subject; Permission remains with V

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
- Observed: <saved-subject fact>
- Evidence: <subject path and section>
- Required correction: <observable condition; no repair text>
```
