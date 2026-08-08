# External sources — ladder and sufficiency

Disclosed reference for the external-search step. Secondary write-ups may locate a primary source; they do not themselves support a claim.

## Source ladder

Search in this order. Stop ascending once an applicable primary source settles the claim; keep searching peers at the same rung when authorities conflict.

1. **Owning specification or standard** — the document that defines the term, metric, API, protocol, or evaluation rule (RFCs, ISO/IEEE, contest/official problem statements, library language specs).
2. **Original paper or first-party report** — the publication that introduces the method, dataset, or result you cite; prefer the authors' version over a survey that restates it.
3. **Official product or project documentation** — docs for the exact version the task uses (API reference, user guide, dataset card, benchmark handbook).
4. **Canonical source repository** — the project's own code, tests, issue tracker, and release notes when behaviour or version history is the question.
5. **Official benchmark or leaderboard rules** — scoring, data splits, and constraints published by the benchmark owner.
6. **Release notes and changelogs** — only to pin version applicability when the claim depends on a version boundary.

When the claim is local to this repository's chosen stack, prefer the docs and repository of that stack over a generic article about the same idea.

Treat blogs, forum answers, secondary tutorials, marketing pages, and model-written summaries as pointers only: follow them to a rung above, then cite that rung.

## Sufficiency bar

External search is done for a working answer when every material claim in that answer meets one of these:

- it has at least one **applicable** source from rungs 1–5 that **supports** the claim (not merely mentions it), and the owning authority is identified; or
- it is labeled `Unknown`, and the Slot document names the missing owning authority or primary source that would settle it; or
- it is labeled `Disputed`, with each side's applicable primary source recorded.

Before counting a source as support, check applicability against the task:

- **version** — same release or language edition the task uses;
- **scale** — same size regime (data volume, QPS, model size) when the claim depends on scale;
- **distribution** — same input or data distribution when the claim is average-case or dataset-bound;
- **operating conditions** — same online/offline, hardware, or constraint regime when the claim depends on them.

A source outside those bounds may still be recorded as a limit or rejected interpretation; it does not upgrade a claim to `Externally supported`.

One thin source is not enough when the claim is load-bearing for legality, ranking, success, or measurement: obtain a second independent primary source, or record why a second authority does not exist (single-owner definition).

## Search moves

For each material claim:

1. Name who would own the truth (the owning authority).
2. Retrieve that authority's current primary document or repository artifact.
3. Extract only the passage that supports or contradicts the claim; record locator, date or version, and applicability check.
4. Run one search aimed at a newer or conflicting authority (release notes, errata, competing standard, later paper).

Stop when the sufficiency bar holds. Further browsing after that is scope creep, not thoroughness.
