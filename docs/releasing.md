# Public releases

The procedure below applies to every public release. Version 1.2.0 was the
first public release of the desktop plugin.

## Independent version numbers

The public repository is the release channel. Its bundle version is recorded in
root `plugin.json`, `.claude-plugin/plugin.json` and the matching plugin entry in
`.claude-plugin/marketplace.json`. All three must contain the same public version.
The release tag is `v` followed by that version, such as `v1.1.0`.

The development repository has a separate version series and remains the normal
destination for development commits. Promoting reviewed content does not change
its manifests, move its default branch or create a development release tag.
Internal component versions remain owned by their components; the non-published
Rust harness package version is not the public bundle version.

## Prepare a public release

1. Inspect the current development checkout, the public default branch, existing
   tags and release records. Record the exact selected source locally. Do not
   include unrelated working changes in the release.
2. Start an isolated checkout from the public default branch. Transfer reviewed
   tracked content into that checkout, preserving the public history. Do not
   merge or push private development history wholesale.
3. Inspect the complete outgoing files for credentials, personal paths, private
   project data, local dependencies and build outputs. Preserve necessary test
   fixtures and the stated scope of inherited evidence. A historical fixture
   path is not an installed dependency or a claim that its workspace is bundled.
4. Set the three public version declarations to the chosen public version. Update the public
   README, changelog and installation examples. Keep development versions out of
   the public release sequence. Preserve the shared instruction adapters and
   Codex-only Hook boundary.
5. Run the bundle validator, the repository's release check selector with its
   project checks, appropriate build and format checks, and the configured Hook
   smoke check. Verify the exact outgoing diff and unchanged code against the
   selected source. Keep mechanical results distinct from effectiveness claims.

Use the maintained release selector from the checkout:

```sh
python skills/frontier-optimization/scripts/run_workflow_checks.py \
  --mode release --repo-root .
```

See the [harness guide](../tools/workflow-harness/README.md#build-and-test) for
Rust builds and tests, and the [deployment guide](./agent-instructions.md) for
shared instructions and existing-file merges. Use an environment with the
Python and Rust dependencies already available or install them through the
project's authorized setup.

## Publish and verify

Review the [listing materials](marketplace-listing.md), [privacy policy](../PRIVACY.md),
[support page](../SUPPORT.md), and [license and source guide](../SOURCE.md).
Use the actual selected source and verification results. Do not label a source
version as GPL-3.0-only merely because a newer branch uses that license: the
historical public `v1.1.0` tag still contains MIT.

Prepare complete corresponding source for the new release at an immutable public
commit and tag, including the build scripts and dependency manifests needed for
distributed components. Supply a matching source archive with the release,
record checksums for both distribution profiles and the source archive, and
verify their contents against that source. A private commit identifier or the
older public release is not a substitute for the new release's source.

Check the listing text against the current
[OpenAI submission fields](https://developers.openai.com/plugins/deploy/submission#listing-metadata):
the display name and subtitle are at most 30 characters, the description at most
4,000, and each of at most three starter prompts at most 128. Check that the
privacy and support links open without authentication. The directory publisher
name comes from the selected verified developer identity; prepared metadata
does not establish that verification.

Build the two profiles using the [desktop packaging guide](desktop-plugin.md).
The market ZIP excludes Hooks; the GitHub ZIP retains the optional Codex-only
integration. The file allowlist is explicit. Preserve the archive digest and
test the exact candidate before publication. An OpenAI submission additionally
requires listing materials, developer verification and review; building the ZIP
does not perform or certify any of those actions.

Review and stage explicit release paths. Commit on top of the public branch,
create the annotated version tag, and push only that branch and tag to the
explicit public remote. Use a normal fast-forward push; a changed remote head
requires reconciliation. Never use a mirror or force push for this procedure.

Publish the GitHub Release from the verified tag with the reviewed release
notes. Verify the actual remote branch, peeled tag commit, manifest versions and
Release status. Confirm that the development branch, version and tags are
unchanged. Future development continues in its existing checkout and version
series; do not copy public version metadata back into that checkout.
