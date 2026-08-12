# Frontier Claim Records

Load only when creating or adopting a claim request. This file is the sole source for C and A.

## Contents

- [C: claim request](#c-claim-request)
- [A: adopted claim review](#a-adopted-claim-review)
- [Claim-branch completion](#claim-branch-completion)

## C: claim request

```markdown
## C001: <claim request>

- Recorded at: <ISO-8601 datetime>
- Snapshot: <immutable parent, FRONTIER, reflection, replan, W revision, candidate manifest, implementation review, B, E, D, and X identifiers as applicable>
- Requested wording: <exact wording>
- Intended use: <exact external use>
- Scope: <object, instances, scales, and time>
- Problem epoch: <integer>
- Representation revision and permitted scope: <exact binding>
- Evidence: <reflection, replan review, design, user authorization, implementation review, W, B, E, and D identifiers required by the wording>
- Uncertainty and limits: <values and claim ceilings>
- Status: CLAIM_REVIEW_REQUIRED
- Adopted review: None; a later A record supplies the disposition
```

Slice 5 may create C and record `CLAIM_REVIEW_REQUIRED` in `log.md` when exact external wording and intended use exist. It must stop that branch there. Claim snapshot review, A adoption, withdrawal disposition, external-use permission, and return to the campaign belong to Slice 6.

## A: adopted claim review

Append A only after validating the immutable claim-review artifact.

```markdown
## A001: <adopted claim-review result>

- Recorded at: <ISO-8601 datetime>
- Claims: <exact C identifiers>
- Review artifact: <assigned immutable claims-review path and identity>
- Review result: <CLAIMS_SUPPORTED | CLAIMS_DOWNGRADED | EVIDENCE_REQUIRED | PARENT_REVIEW_REQUIRED | BLOCKED>
- Intended use: <exact use reviewed>
- Adopted wording: <exact supported wording, exact reviewer downgrade, or None>
- Wording authority: <exact supported external use and scope, or none>
- Evidence snapshot: <immutable identifiers bound by the review>
- Required action: <action or None>
- Campaign status before and after: <same status for claim-only; stopped or halted for full closeout>
- Adoption consequence: <external-use permission, claim-only repair or blocker without campaign starvation, or full-closeout claim disposition>
- Branch return: <CLAIM_REVIEW_COMPLETE and Cycle when eligible | continue full closeout | parent route>
```

Append A for every C in every finished claim review, including `EVIDENCE_REQUIRED`, `PARENT_REVIEW_REQUIRED`, and `BLOCKED`. Group C records in one A only when their result, wording authority, required action, and branch consequence are identical. A records the disposition; it grants external-use permission only for `CLAIMS_SUPPORTED` exact wording or `CLAIMS_DOWNGRADED` exact reviewer-supplied wording. Every other result uses `Adopted wording: None` and `Wording authority: none`.

## Claim-branch completion

If the user withdraws C before review finishes, append X with `Disposition: withdrawn` instead of A. If review already finished, A is mandatory; a later withdrawal uses an additional X to remove wording use. A valid A or pre-completion withdrawing X ends that C's claim branch. Neither a nonauthorizing A nor X authorizes wording.

For claim-only processing, preserve `campaign_status` and record `CLAIM_REVIEW_COMPLETE`; return to Campaign Cycle when no other stop, halt, parent conflict, or unresolved C exists. For full closeout, continue closeout after every active C has A or X.
