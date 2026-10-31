# Connected owner decisions and execution entries

The entries below are optional integrations owned by the project's existing
technical and decision owners. Installing them does not enroll other processes
or authorize an external action. This guide describes the connected paths and
their limits; the local tests use bounded fixtures, not a live research campaign.

These implementations use Python with PyYAML and POSIX file/process primitives;
the managed bridge also needs the built Rust host. Validation uses this project's
Python environment and local host. The Workflow contracts do not require these
languages, but another host needs its own exercised adapter before claiming the
same execution guarantees.

## Direction and scope delivery

`direction_owner.py run` prepares the existing owner, checks current sources,
renders the request and sends those exact bytes to an explicit stdin consumer:

```sh
python tools/workflow-harness/adapters/direction_owner.py run \
  --root . --owner docs/current-work.md --assignment docs/current-assignment.md \
  --invocation direction-1 --timeout-seconds 300 -- consumer-command ARGUMENT
```

The invocation identity is reserved before process start. Its directory under
`artifacts/workflow-harness/direction-calls/` retains the actual request, prepared
input, bounded output and receipt. `recover --root . --invocation direction-1`
reads saved facts without dispatching again. An interrupted or failed consumer
may have acted; reconcile its original identity instead of creating a new one
to bypass uncertainty. The default combined output allowance is 2,000,000 bytes
and the default timeout is 300 seconds; these are configurable transport limits,
not research budgets. The consumer and its descendants are not sandboxed here.

The existing owner may maintain this optional metadata:

```yaml
decision_material:
  evidence:
    - {path: docs/observations.md, section: selected-cases}
  user_scope:
    - original:
        - {path: docs/user-decision.md, section: original-exchange}
      interpretation: {path: docs/current-work.md, section: scope}
```

Selectors refer to repository paths and Markdown heading anchors. Retain the
question, actual options, answer, qualifications and later corrections; label
translations. At `--event direction` (the default), original evidence and user
sources are supplied internally beside the interpretation. `--event scope`
supplies scope sources at affected recovery. `--event continuation` uses retained
references without creating another inquiry. The resolver and recovery helpers
also assemble these materials on their existing decision paths. Missing or
oversized material is a visible limit, not a new permission or a global stop.

Use existing objective/work selectors or an adopted context account to bound the
working input. Full retained source bytes remain retrievable. `prepare --prepared
FILE` is local inspection; `send --prepared FILE -- COMMAND` rechecks before a
later send. The combined `run` is the ordinary entry when controlling dispatch.
The existing owner still judges and adopts the return. Reconsider source choices
when the decision or relevant evidence changes, not on every routine continuation.

## Final effects and cooperative HTTP sends

For a protected operation selected for final-effect checking, use
`OperationBinding.configured_effect(load, consume, protected_consequences,
describe_effect=...)`. Its required callback is
`describe_effect(action, context, effective)`.
It returns the actual Action derived from resolved defaults and adopted choices.
Batch rechecks permissions, requirements and cumulative resources, then consumes
the same effective object. The adapter must faithfully describe and use it;
neither a declaration nor a passing structural check proves this behavior.
Ordinary local configured operations need no permission descriptor.
Existing `configured` bindings without a descriptor remain declaration-only;
they do not acquire this guarantee or become blocked by this update. The selected
HTTP binding uses the strict constructor, which rejects a missing descriptor.

`protected_http.py` supplies a concrete cooperative sender and a Batch binding
for that same sender. It sends one request without redirects, retries or child
commands. Its scope is a technical projection of an already adopted decision,
selected by the integration owner, not an authenticated grant or interpretation
of the user's original answer. For example:

```json
{"enabled":true,"authority_reference":"docs/user-decision.md#feedback",
 "destinations":["https://example.org/feedback"],"methods":["POST"],
 "resource_limits":{"requests":2,"body_bytes":10000}}
```

The request file selects `url`, optional `method` (default `POST`), `headers`,
`body_file` relative to that file, `timeout_seconds` (default 30), and
`max_response_bytes` (default 1 MiB). The body is loaded once. The journal retains
parameters, digests, resource reservations and response status/digest, not the
body or header credentials. URLs are retained, so keep credentials out of URLs.

```sh
python tools/workflow-harness/adapters/protected_http.py activate \
  --state .frontier/feedback-sender.json --scope adopted-scope.json --activation scope-1
python tools/workflow-harness/adapters/protected_http.py send \
  --state .frontier/feedback-sender.json --request request.json --request-id feedback-1
```

A replacement or withdrawal uses `activate` with a new identity and
`--expected-activation scope-1`. Activate a known withdrawal at this sender
before slower source adoption or successor preparation; it does not wait for a
Batch consumer. Connection preparation has an initial check. Final scope check,
durable reservation and payload send share a short separate lock. Response wait
is outside that lock. Withdrawal during connection preparation prevents the
payload but cannot undo a connection already begun. The send lock lasts until
the bounded payload send finishes; this is not instantaneous cancellation.

`inspect` reads the controller. `reconcile --request-id ID --settlement FILE`
records observed completion or confirmed non-send with supporting evidence and
actual resources; it never resends. Unknown outcomes retain their reservation.
For a completed historical receipt, use the explicit `recover` command below.
It validates the same request identity and resolved parameters, then reads the
saved receipt without a new grant, Batch send preflight, connection or charge.
An absent, uncertain or changed receipt is an error; recovery never sends.
Batch defaults send identity to `Batch:key`; an explicit
`Action.details.request_id` associates an existing identity across Batches.
If attaching a recovered result to another Batch, use its existing observation
recording path, not another `perform` of the protected send. Generic send preflight
continues to reject new sends after withdrawal or capacity exhaustion.

```sh
python tools/workflow-harness/adapters/protected_http.py recover \
  --state .frontier/feedback-sender.json --request request.json --request-id feedback-1
```

Scope activation and invocation retirement are separate operations: retiring an
Agent does not withdraw a sender grant, and a grant does not restore a retired
Agent. Unconnected external-service adapters and opaque command descendants are not enrolled.
Reconsider integration only when an actual protected sender needs this guarantee.

## Source adoption and managed activation recovery

`managed_correction.py` composes the existing source adoption and managed host.
Its request contains the ordinary `source` corrections/replacements/relations
and `replacement` assignment, with optional objective, constraints and actual_use.

```sh
python tools/workflow-harness/adapters/managed_correction.py apply \
  --root . --owner docs/current-owner.json --session RUN_DIRECTORY \
  --activation repair-1 --expected-invocation 1 --request correction.json
python tools/workflow-harness/adapters/managed_correction.py recover \
  --root . --owner docs/current-owner.json --activation repair-1
```

The entry prefers the executable from the documented `target/release` build,
then falls back to `target/debug`. Rebuild after source changes; use `--binary`
to select a different built `workflow-harness` executable. Before
adoption, the entry saves the proposed source revisions, original request,
Session, expected invocation, activation identity and replacement in a sidecar
beside the existing owner correction journal. Progress must not modify a receipt
that the successor itself uses as evidence. A source receipt establishes adoption;
the real Session checkpoint establishes activation. Recovery compares both and
reuses an activated identity after a lost acknowledgement. A changed invocation
or source requires reconciliation. The entry never drives the successor or
replays actions. Its owner lock coordinates callers of this entry only; direct
file writes and other hosts are outside it.

The existing `host managed-correct` accepts optional `current_use`, installing
that binding with invocation validation and replacement under the same Session
lock. Source publication remains a separate operation; this does not promise
an atomic transaction across source files and runtime state. Observe the next
affected receiver before reporting adoption of the corrected work.

## Professional configuration choices

The ordinary project entry is `codex_owner.py`. It uses the platform-neutral
`Batch.prepare_realization`, `answer_realization`, `adopt_realization` and
`OperationBinding` interfaces. It supports arbitrary owning Batches, objectives,
source selectors and JSON configuration values. No task name, model, trial count
or optimization method is built into the entry.

Use this at a consequential new or changed professional choice. Reuse an adopted
choice and its applicable grounds for ordinary continuation. This is an existing
owner's work, not another reviewer or a new approval stage.

## Prepare and answer

The existing owner defines the Batch and selects the intended decision, consumer,
operation names and relevant conditions. A realization specification is JSON:

```json
{
  "owner": "docs/current-owner.md",
  "intended_decision": "Select the concrete implementation and first observation",
  "consumer": "maintained-project-entry",
  "operations": ["run-selected-work"],
  "sources": [{"path": "docs/current-problem.md", "section": "Current conditions"}],
  "conditions": {"operating_regime": "current declared conditions"}
}
```

Prepare locally. This does not contact Codex:

```sh
python tools/workflow-harness/adapters/codex_owner.py prepare \
  --root . --batch B123 --spec realization-spec.json --request owner-request.json
```

The request contains the actual problem, available descriptions and an exact
material scope. By default, that scope covers maintained entries, their direct
local links and repository-installed Skill bodies. It does not recursively scan
history or read all method bodies. Missing links remain visible as unavailable.
To replace the default material scope, pass `--materials` with a JSON list of
`path` and optional `field` or `section` selectors. The original problem sources
remain supplied. Descriptions and selected task text are also part of the request;
inspect or select them through the existing owner when their disclosure matters.
Paths must resolve inside the selected project, including after following symlinks.

The host must have authority to send the selected content to its model service.
The request file records the input scope; its hash is not an authorization token.
No recurring human confirmation is introduced when existing authorization covers
the selected work and data. Do not add credentials or unrelated private records.

Answer using the installed Codex binary and the host's selected model, effort,
call allowance and total transport timeout:

```sh
python tools/workflow-harness/adapters/codex_owner.py answer \
  --root . --batch B123 --request owner-request.json \
  --binary /path/to/codex --model HOST_SELECTED_MODEL --effort HOST_SELECTED_EFFORT \
  --max-calls 3 --timeout-seconds 180
```

The two numerical values above are examples for the owner call, not research
limits or execution timeouts. Choose them for the actual work. The adapter does
not substitute a model or silently increase them. It uses existing authentication
without installing anything. The project must already provide Python and PyYAML,
as required by the existing Batch tools.

The first model input includes the available descriptions even when the proposed
implementation cites no professional method. The owner can request actual material
by its identifier. The host resolves only allowed sources, supplies their contents
and records the next response. A model never receives filesystem or shell access
through this interface. The final response gives concrete selectors and values,
design grounds and the first observation. A source can substantiate an unchanged
choice; no minimum source count or compulsory retrieval is enforced.

## Adopt and execute

The answer command returns an invocation identifier. Adopt that saved answer:

```sh
python tools/workflow-harness/adapters/codex_owner.py adopt \
  --root . --batch B123 --invocation RETURNED_INVOCATION_ID
```

This adopts only the professional choice; it does not grant permission for an
external effect, revise the optimization objective or launch project work.

Connect the actual configuration loader and receiving function once at the
maintained project entry:

```python
binding = OperationBinding.configured(
    load=load_effective_configuration,
    consume=execute_with_configuration,
    protected_consequences=existing_protected_consequences,
)
batch = Batch.open(repo, batch_name, governance=existing_governance,
                   operations={"run-selected-work": binding})
outcome = batch.perform(action_selected_by_the_existing_owner)
```

`load(action, context)` returns the real configuration after ordinary defaults
and overrides. The binding applies the adopted selectors to existing fields.
`consume(action, context, effective)` receives that exact checked object and
returns the existing `OperationResult`, including actual resource use and effects.
It must not reload a different configuration. The existing Action, measurement
meaning, permissions and effect policy still apply. A changed measurement scope
belongs with its measurement owner, not a hidden configuration override.

For non-configuration consumers, keep their existing explicit `prepare` and
`consume` binding. `Batch.realization_choices()` exposes the current adopted
selectors without relying on private record layout. It validates current input
and selected grounds. Do not call it inside a Batch callback that already holds
the Batch lock; the callback's `context["realization"]` supplies that same choice.

## Recovery and correction

`answer` reuses a valid completed response without another model call. `recover`
reads an existing response or completes delivery from a finished local transport
journal after a host interruption. Neither command repeats an uncertain call:

```sh
python tools/workflow-harness/adapters/codex_owner.py recover --root . --batch B123
```

Failed or incomplete calls remain visible. Reconcile the actual state and then
use `retire --invocation ID --reason TEXT` if the existing owner withdraws that
invocation. Retirement prevents later adoption; it does not assert that a backend
has stopped. Prepare changed conditions before a replacement answer. Retired
responses cannot restore eligibility. Unrelated progress does not invalidate a
choice, and changed selected grounds are rejected before adoption or execution.

The journal under `artifacts/workflow-harness/owner-calls/` retains raw delivery,
response and failure evidence. The operative choice remains in the owning Batch;
the journal is not a second editable decision source. Material content is stored
through the existing context-source store. A read request alone cannot become a
decision, and a final answer cannot cite content the host never supplied.

## Coverage

The main Workflow has no Codex import or model dependency. Other hosts implement
`OwnerReply` and the same Batch interfaces. This adapter covers its controlled
owner calls and connected consumers; it cannot intercept unrelated direct shell
commands or guarantee the soundness of professional reasoning.

The older four-case acceptance runner is retained as
`../tests/codex_owner_acceptance.py`. Its exhausted trial slots and original
failures remain historical evidence; they do not limit this project entry.
Current mechanical tests include an ordinary arbitrary Batch, source retrieval,
actual subprocess consumption and recovery without another call. The source
installation retains its behavioral observations separately; its project log and
live campaign records are outside this portable bundle. Those observations do
not establish effectiveness in a receiving project. The retained acceptance and
smoke runners use `codex` from the host PATH; running them makes model calls and
is separate from the local test suite.
