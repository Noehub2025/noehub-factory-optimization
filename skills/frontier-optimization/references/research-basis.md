# Shared research understanding

Use one adopted account to connect observations, prior knowledge, current explanations and demonstrated approach coverage. The account helps the team form useful questions and choose work. It is not a certificate that research is complete or a second place to decide goals, permissions, budgets or route selection.

The Coordinator adopts this understanding in existing working material. Researchers, designers, implementers and reviewers propose changes through their ordinary returns. Original observations stay in their artifacts; the problem, measurement, investment and authorization owners retain their decisions. The Brief points to the account. Decisions and designs reference the particular statements and conditions they use. A short prose account remains sufficient when it supports the work; structured items are useful for consequential reuse across tasks and Sessions.

Professional judgment follows [Research understanding](learning-loop.md#research-understanding), [Discovery allocation](learning-loop.md#discovery-allocation) and [technical design](technical-design.md#ground-consequential-design-choices). These are related responsibilities, not a serial research pipeline. A focused question does not require a field survey; a candidate screen does not require complete causal explanation. A stronger ambition does call for proportionate investigation beyond the supplied menu and depth on the premises that could change the direction.

## An illustrative decision trace

This hypothetical trace abstracts distinctions exposed by the project's existing research and experiment records. Its observations and results are invented to explain the Workflow; they are not project evidence or a recommendation for the current campaign. The subject could be an algorithm, a work process, a physical treatment or a service.

The objective is to improve the useful outcome under real operating conditions. A retained approach has a promising development result but lacks a usable route to the next relevant observation. A proposed alternative is convenient to implement and rests on a plausible local signal.

| Work | Shared understanding and its consequence |
|---|---|
| Inspect comparable cases and conditions | The local signal appears in selected cases, while workload and operating conditions also change. Record the signal as an observation under those conditions and the proposed explanation as a hypothesis. The cases do not establish frequency or a stable cause. |
| Investigate prior work and current approaches | Original evidence suggests two mechanisms with different necessary conditions. Inspect enough of the current approach and its outputs to see which capability it demonstrates; a component list alone does not answer this. A further reachable lead remains open. The researcher connects these findings rather than only listing references. |
| Form the useful question | Ask whether the signal adds useful information beyond the retained approach under relevant conditions. This replaces the looser question, "Can we implement another mechanism?" If current evidence cannot support this question yet, inspect the decisive missing comparison rather than inventing confidence. |
| Sketch the observation before committing | The proposed comparison changes the target and surrounding conditions together. It could screen the whole treatment but could not distinguish the two explanations. The designer identifies a suitable control or a different observation, and estimates its necessary setup and delay. No complete design for every route is needed. |
| Select the next investment | Compare the corrected experiment's next sufficient commitment with restoring the retained approach's observation capability and the remaining discovery lead. Any can win on objective contribution, useful learning and full remaining cost. For this illustration, assume the owner chooses capability recovery because it makes the decisive comparison reachable sooner. Record the open inquiry and a discovery point reachable even if recovery succeeds. |
| Adopt the actual result | If recovery succeeds, update the capability statement and send the real next comparison to its executing owner. If it fails, retain the observed failure's scope and compare the remaining cost; do not declare the competing mechanism superior. A later ambiguous comparison may justify a narrower screen, further inquiry or another allocation, while preserving the unanswered explanation. |

The account can change the question, design, investment or intended use; it need not change the selected winner to be useful. A second legitimate path would deliberately select an integrated candidate screen with a grounded performance opportunity, accept limited attribution and adopt its result within that scope. Neither path earns priority merely by using a different mechanism or filling the account.

## Optional structured account

The installed representation places an optional `research_basis` object in the existing owner document. Its `context_account.source` selects that field, and `context_account.sha256` identifies the adopted canonical content. The digest is the revision; no independently maintained revision counter is needed. Keep the original goal and controlling decisions at their current sources.

```yaml
research_basis:
  schema: 1
  overview: "The current question, strongest supported understanding and material open leads."
  items:
    - id: observed-effect
      kind: observation
      text: "The complete treatment improved the observed outcome under condition A."
      conditions: "This comparison does not isolate the contributions of its parts."
      sources:
        - path: existing/result.json
          field: observations
          sha256: <selected-source-digest>
      links: []
    - id: interaction-explanation
      kind: hypothesis
      text: "An interaction may explain the observed improvement."
      conditions: "Separate contributions and operating-condition effects remain possible."
      sources: []
      links:
        - relation: considers
          target: observed-effect
context_account:
  source:
    path: existing/owner.yaml
    field: research_basis
  sha256: <canonical-account-digest>
decision_material:
  discovery:
    - path: existing/investment.json
      field: discovery
```

Paths and statements in this example are illustrative. Use existing project material, not a new file for each role. Only decision-bearing content needs an item identifier. Distinguish observations, attributed reports, hypotheses and interpretations; adoption does not change their evidence kind. Preserve conditions and material competing explanations. Do not recycle identifiers or erase a withdrawn statement while a current consumer still refers to it.

Source selectors follow the installed convention: object `path` values are repository-relative; string references are relative to the owner. A `field` selects structured content and a `section` selects a Markdown heading. Display the resolved repository path. Use retained source content and its digest when a consequential claim depends on a particular version; a mutable web address alone does not identify that version.

`decision_material.discovery` points to the existing investment owner's current inquiry arrangement. It contains no copied schedule or completion flag. This role reads the current working source and rejects an explicit historical `commit`; historical evidence roles remain available for past results. Direction and owner scope/resumption views include the arrangement independently of research-item links. Missing arrangement is shown as unknown. For a continuing open objective, the existing owner retains or establishes a reachable discovery point, or grounds ending discovery for the real remaining opportunity window. Merely displaying unknown does not make that decision.

An existing decision or design may identify its substantive dependencies in its own metadata:

```yaml
research_use:
  owner: existing/owner.yaml
  items: [observed-effect, interaction-explanation]
```

The consumer owns these references. Generated views can derive reverse links; do not maintain another editable copy in the account. The actual delivered revision belongs to the retained use record. Missing links limit automatic impact coverage and do not show that a new finding is irrelevant.

## Adoption and receiving work

Workers return a proposed change through their existing result association and write scope. The Coordinator preserves the conclusion, source conditions and dissent, adopts a supported change or unchanged account, and updates the actual affected assignment or design. Receiving a report, changing its status or refreshing a chart is not adoption in the work. Use the maintained publication operation for structured adoption so the account, association, incorporation references and publication marker change together; preserve unrelated owner content and reconcile version conflicts rather than overwriting them.

Use existing return identities and incorporation records for pending findings. Do not create another queue. Present new findings with no known link before filtering at consequential owner events; where only a bounded portion fits, show the remaining count and exact retrieval path. A worker is not required to predict every affected dependency. Findings that the receiving path never observes are outside automatic coverage. A current-Codex reading receipt is not an authenticated native worker answer.

The normal entry delivers a relevant projection with the adopted revision, selected items, conditions, necessary dependencies, direct supporting or contrary evidence and pending changes. The full source remains available for exact retrieval. Generated overview, decision/design and change views use the same maintained content; a table or chart is not edited separately. A stale rendering is regenerated or labeled. Unknown or initial understanding permits discovery and useful probes; the structured form creates no research-readiness gate.

Use the consuming project's maintained direction/design entry, linked from its effective instructions, for present preparation. A fresh or reset receiver needs the available baseline; a delta is sufficient only when its retained baseline is known. Recovering an old invocation retains that invocation's original input, receipt and effects. Resuming current research after reconciling uncertain actions prepares current material under a fresh invocation identity. Do not attach newer evidence to an old answer or replay an uncertain effect.

The support checks selected sources, coherent publication and the input actually delivered on enrolled paths. It cannot establish scientific completeness, correct reasoning, complete dependencies or adoption by an unobserved worker. Original-source checks and selective independent judgment remain professional work. Ordinary unchanged continuation needs no new research, review, summary or approval.

## Supported operations

The installed Python helper uses PyYAML and the existing owner lock and retained-source directory. It adds no server or model process. The source is [`research_basis.py`](../scripts/research_basis.py); ordinary commands reuse [`frontier_references.py`](../scripts/frontier_references.py).

Publish an already chosen account through its existing owner:

```sh
python3 .agents/skills/frontier-optimization/scripts/frontier_references.py \
  adopt-context-account --repo . --owner-source path/to/existing-owner.json \
  --result path/to/publication-request.json
```

The request contains `operation`, `expected_owner_sha256` for the complete current owner bytes, `expected_account_sha256` from its adopted association (or `null` for first adoption), and `proposed_account`. Optional `sources` and `incorporates` name the exact selected evidence and observed returns. A source has `path`, its selected-content `sha256`, and optionally one `field`, `section`, or positive integer `attempt` selecting a saved attempt result. A commit may identify historical evidence. The owner chooses and authorizes the content through its normal responsibility; writing a request does not grant new authority.

Retry an interrupted publication with the same operation and unchanged request. The helper retains the proposed and prior bytes before replacing the owner, publishes the account and association together, and distinguishes a completed adoption from an unstarted or conflicting proposal. A changed basis requires a content-aware new proposal with current expected versions; never rewrite the old operation's meaning. Existing correction state and unrelated metadata remain intact.

Generate an overview or a selected view directly from the adopted source:

```sh
python3 .agents/skills/frontier-optimization/scripts/frontier_references.py \
  research-view --repo . --owner-source path/to/existing-owner.json --mermaid
python3 .agents/skills/frontier-optimization/scripts/frontier_references.py \
  research-view --repo . --owner-source path/to/existing-owner.json --item selected-question
```

These commands emit derived text without changing the account. `--raw` includes the projection, source and render metadata as JSON. `--max-chars` controls the display allowance; whole statements and their conditions stay together, and omissions remain explicit. A saved chart carries its source revision and must be regenerated before being presented as current.

Derive affected known consumers after an adopted update:

```sh
python3 .agents/skills/frontier-optimization/scripts/frontier_references.py \
  research-impact --repo . --owner-source path/to/existing-owner.json \
  --prior path/to/prior-account.json --source path/to/existing-design.json
```

Repeat `--source` for the existing consumers to inspect. The result uses their own `research_use` declarations; it is not a separate dependency ledger or proof that every affected task is known. A missing declaration is a coverage limit. Use the normal direction/design entry for actual delivery and existing correction mechanisms for affected work.

## Project adoption and effectiveness

The executing task's owner adopts the initial account from current relevant findings and sources, with any material gaps explicit. Retain original results and history; do not migrate every past record. The Workflow maintenance Session supplies the generic capability and handoff, while the executing Session decides how to update its current questions and assignments within existing authority.

Judge the repair separately at four levels: implemented behavior, actual receiving entry, adoption in current work and research benefit. Useful evidence includes less repeated reconstruction, a corrected question or design, an avoided unsupported commitment, a useful new route or well-supported unchanged choice. Include maintenance effort and feedback delay in the cost. More sources, more chart items and passing checks do not establish research benefit; simplify the account if its overhead outweighs its use.
