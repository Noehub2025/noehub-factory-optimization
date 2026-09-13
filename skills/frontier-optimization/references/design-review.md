# Frontier Design Review

Load only when [Assurance by consequence](batch-evaluation.md#assurance-by-consequence) selects an independent design judgment, or when interpreting its artifact. Professional involvement, profile selection and a design revision do not themselves require review.

For a needed W design review, prepare the saved subject once the assigned question's relevant concerns, delivery bindings and user choices are available. Reuse existing design content; completeness is judged for the selected use, not every future part of W. Use [W saved references](work-plan.md#saved-design-references); the consuming review owns the commit, not W. Preserve prior reviews and assess only changed content and affected conclusions. The assignment contains no expected verdict or proposed repair.

## Review method

1. Read W, indexed concerns and traceability at the assigned Git commit. Verify parents, scope, route, repository evidence, profile, applicable V and selected stable slice keys. Use the current saved-reference checks, not historical packet or snapshot preparation.
2. Check whether the selected use has the technical agreements it needs under [Choose the profile](technical-design.md#choose-the-profile). A profile does not impose a file bundle. W indexes the concerns used by its contract; the professional owner supplies their meaning and the Coordinator maintains affected maps and lifecycle fields.
3. Apply [Technical design's assignment ownership rule](technical-design.md#assign-the-professional-author) before reviewing completeness. Ignore incidental workflow background. If a method owned by Batch is nevertheless normative, return at most one root `scope` finding for that mechanism and do not derive receipt, owner, schema, digest, failure, or recovery findings from it. Missing immutable ownership for reversible, unpublished working material is not a finding. Continue reviewing unrelated technical content.
4. Review applicable architecture, responsibilities, dependencies, integration placement, domain meaning, state ownership, lifecycle, invariants, interfaces, callers, runtime data and control flow, failures, recovery, migration, compatibility, rollback, replacement boundaries, and any human-input schema, provenance, quality, confidentiality, acceptance, and evidence-only terms.
5. Check [consequential design choices](technical-design.md#ground-consequential-design-choices) against their cited grounds and intended use. Address a source misreading, omitted material cost or dependency, or observation incapable of answering its question when it affects the next delivery or investment's reliability. Reuse sufficient reasoning; finding a better design, enumerating alternatives or proving success is not the reviewer's task. A missing comparison table, modest scale or unfamiliar method is not a finding. Keep other advice non-blocking. Every user-owned tradeoff needed by a reviewed slice retains its eligible options, adopted V and conditions; design preference is not development authorization.
6. Trace each behavior to its owning module, interface, flow, and distinguishing verification under [Technical design: Verification](technical-design.md#verification), including its current-use scope for failure and recovery obligations. The Delivery map and traceability associate those pointers with stable slice keys. Future B assignments, attempt namespaces, internal evidence destinations and runtime status remain with execution. A path belongs to Design only when a real caller or operator outside the current B depends on it as a stable interface.
7. Apply [Constrain effects, not convenient forms](technical-design.md#constrain-effects-not-convenient-forms) to restrictions that materially affect this slice, including evidence channels and verification methods. Judge the current protection basis, not merely consistency with an inherited precaution; do not inventory unrelated restrictions.
8. Perform the cold-read implementation check defined in [Verification](technical-design.md#verification). Distinguish missing consequential technical meaning from ordinary implementation choices. A finding needs a concrete gap affecting the promised use; lack of per-slice recovery machinery or a complete internal test catalogue is not such a gap.
9. Apply [decisive feasibility](technical-design.md#test-decisive-feasibility-claims) to the promised output, including its distinction between a research hypothesis and an action prerequisite. Check the weakest decisive claim against its evidence and relevant conditions. Judge whether a research observation can be delivered and interpreted, not whether its hypothesis will succeed; full delivery retains its acceptance obligations.
10. For any condition capable of rejecting the implementation or producing a broader disposition, apply [Decision-bearing thresholds](frontier-core.md#decision-bearing-thresholds). Check the current owner and allowed consequence, and check the complete semantic match when Design calls it `unchanged`. Do not re-prove an unchanged threshold or review ordinary observations, planning estimates, diagnostics, or operational limits as if they were Design acceptance.
11. Return exactly `DESIGN_READY`, `DESIGN_REPAIR_REQUIRED`, `EVIDENCE_REQUIRED`, `PARENT_REVIEW_REQUIRED`, or `BLOCKED`. A positive result has no finding and no unresolved item blocking the reviewed slice.

Use `DESIGN_REPAIR_REQUIRED` for a conflict or missing capability that design revision can resolve. For insufficient grounds, apply Technical design's evidence-routing rule; use `EVIDENCE_REQUIRED` only for the bounded observation it permits. Return `DESIGN_READY` when every decisive claim for the promised output meets that rule; ordinary implementation risk may remain. Otherwise return the existing parent-owned decision or exact blocker.

`DESIGN_READY` establishes technical readiness only; neither the verdict nor adoption grants Permission or decides whether a V covers the change. Initial development uses the current Entry decision and applicable V under [User decisions](user-decisions.md), without another answer when existing boundaries apply. For a later revision, apply [Boundary-preserving continuation](batch-current.md#boundary-preserving-continuation): the current owners, not the Design reviewer, determine whether V still applies.

A nonpositive review changes no design content. The Coordinator scopes the revision and returns the findings to `design-implementation`; the designer repairs professional content, and the Coordinator regenerates affected mechanical bindings. Select any needed follow-up judgment under [Assurance by consequence](batch-evaluation.md#assurance-by-consequence), using the change and affected conclusions rather than repeating all design checks. Introducing this authoring role does not reopen an unchanged finding-free design.

## Assignment

```yaml
review_kind: design
review_id: <R handle>
subject: <tool-produced Git commit and selected paths, including W and its indexed design files>
parents: [<applicable parent references, including separately versioned source evidence when needed>]
delivery_scope: [<selected stable slice keys>]
assigned_review_path: <frontier/reviews/design-<review-id>.md>
completion_check: <settle the assigned design question for its intended use, identifying reused conclusions and any remaining prerequisite; for repair, assess the change and affected conclusions>
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

- Assigned question and intended use: <supported conclusion or findings>
- Reused evidence and affected technical agreements: <relevant pointers, assumptions and checks>
- Selected delivery, applicable bindings and implementability: <supported conclusion or concrete remaining dependency>
- Other required checks: <only those needed for this use, or omit>

## Findings

### Finding 1: <omit when DESIGN_READY>

- Result effect: <DESIGN_REPAIR_REQUIRED | EVIDENCE_REQUIRED | PARENT_REVIEW_REQUIRED | BLOCKED>
- Affects: <W/design pointers, records, fields, or slices>
- Requirement: <exact requirement>
- Observed: <saved-subject fact>
- Evidence: <subject path and section>
- Required correction: <observable condition; no repair text>
```
