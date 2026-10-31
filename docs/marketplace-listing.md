# Aka Optimization listing materials

Status: listing prepared for version 1.2.0 after a real Codex desktop test. Not yet submitted or approved.

## Audience and first impression

Write for people already using Codex for engineering or algorithm work who may
be unfamiliar with optimization methods. Lead with concrete tasks, a first
request, and the results they can inspect. Explain how the workflow researches
approaches, implements changes, measures results, and uses those results to
choose the next step. Keep the detailed workflow controls after that introduction.
Engineering and algorithm optimization are the main focus of the introduction;
this positioning does not add a task or technology restriction to the workflow.
Users can start by describing a goal, then clarify comparisons and constraints
through conversation. Do not promise that expertise is unnecessary or that a
task will achieve a performance or cost improvement.

## Prepared listing

The root `plugin.json` owns the executable listing metadata. Its OpenAI interface
contains the following prepared text; the identifiers and version remain unchanged.

| Field | Prepared value |
|---|---|
| Display name | Aka Optimization |
| Subtitle | Engineering and algorithms |
| Publisher display name | Set by the verified identity of the PartnerNetSoftware OpenAI organization |
| Legal publisher | PARTNERNET SOFTWARE PTY LTD (ACN 621 438 622), Sydney, NSW, Australia |
| Developer | Noehub, Hangzhou Boshu Technology Co., Ltd. (handles support) |
| Category | Productivity |
| Support contact | support@noehub.com |
| License | GNU General Public License version 3 only (`GPL-3.0-only`) |
| Website | https://github.com/Noehub2025/noehub-factory-optimization |
| Privacy | https://github.com/Noehub2025/noehub-factory-optimization/blob/main/PRIVACY.md |
| Support | https://github.com/Noehub2025/noehub-factory-optimization/blob/main/SUPPORT.md |
| Terms | https://github.com/Noehub2025/noehub-factory-optimization/blob/main/TERMS.md |

### Long description

Aka Optimization is a workflow for engineering and algorithm optimization in Codex. Describe what you want to improve, and it helps you define how results will be compared, research possible approaches, implement changes, and measure their effects, with independent reviews along the way. Saved task records let you review earlier work and continue in a later conversation. Possible tasks include making a program run faster while preserving its results, investigating model inference cost at an agreed quality level, or comparing algorithms under the same computing budget. Improvement is not guaranteed. The workflow plans and measures before it changes code, so even a small task can take 15 to 30 minutes. It saves task records in your project and can create Git commits as it works. It needs a local Git project, Python 3.10 or later, PyYAML 6.x, and Codex with sub-agents. Tested on macOS; Linux is untested and the helper scripts do not support Windows.

### Starter prompts

Use one prompt at a time. These are prepared examples, not verified desktop
activation results.

- Help me set up Aka Optimization for this project.
- Use Aka Optimization to help this program run faster without changing its results.
- Use Aka Optimization to continue the task I choose from where we left off.

### Names that remain unchanged

Keep `noehub-factory-optimization`, the existing catalog identifiers,
`setup-noehub`, and `.noehub/` project paths. Existing generated instruction
markers and runtime text are preserved so the branding update does not require
project migration. Preserve Ken Chen as author and copyright holder.

### Logo assets

The original orange glass design, dark background, and spacing are preserved.
Both distribution archives include the following PNG files, referenced from
the plugin root in `extensions.com.openai.interface`:

| Field | File | Dimensions |
|---|---|---|
| `logo` | `./assets/logo.png` | 512 by 512 pixels |
| `composerIcon` | `./assets/icon.png` | 256 by 256 pixels |

The supplied 1254 by 1254 PNG is retained byte-for-byte as
`assets/logo-source.png` in the repository and GitHub archive. The exports use
macOS `sips` to resize that source without cropping, removing the background,
additional sharpening, or AI redrawing. No dark variants or brand colors are
declared. Local previews at 48, 128, and 512 pixels on light and dark backgrounds
retain a recognizable outline and central opening. Glass details reduce at
48 pixels, and the opaque dark square remains visible on a light background.
These previews do not establish a live host appearance or Marketplace approval.

## Reference examples used for the wording

These are observations of first-party pages, not evidence of higher conversion
or a promise that Aka offers the same capabilities:

- [Lovable](https://lovable.dev/build) starts with an outcome users recognize and
  offers templates that make a first request concrete.
- [Granola](https://www.granola.ai/) introduces a familiar meeting situation and
  shows what happens to the user's notes.
- [Claude Cowork](https://claude.com/resources/guides/claude-cowork-product-guide/getting-started)
  encourages a first task using real work the user already understands.
- [Superpowers](https://github.com/obra/superpowers#how-it-works) narrates what
  happens after the user brings an idea to the agent, with details for developers
  later in the guide.
- [autoresearch](https://github.com/karpathy/autoresearch) makes repeated research
  tangible through actions and experiment records. Its overnight operation and
  hardware requirements are not claims made for Aka.

Use these references for how to explain a product, not for choosing Aka's task
scope. Introduce engineering and algorithm problems, a request to try, results
the user can inspect, then details. Do not invent testimonials, improvement
percentages, verified ease of use, or successful desktop screenshots.

## Privacy and support basis

The [privacy policy](../PRIVACY.md) and [support page](../SUPPORT.md) apply to the
software and company support practices. They distinguish local records, host
model processing, external tools, and information users voluntarily email.
Noehub deletes support emails and attachments within 90 days after an issue
closes; that policy does not control local files or third-party retention.

The behavior review used the packaged paths in `packaging/distributions.json`:
setup writes the project instruction link and two `.noehub/` files; task reading
and recovery retain selected requests and receipts; an explicitly configured
subprocess can save output and errors. Research Skills can use host-provided
external tools. Separate GitHub adapters can call model services or web addresses. There is
no built-in Noehub telemetry or automatic project-upload endpoint in this code.
The responsible implementation entries are `scripts/noehub_setup.py`,
`scripts/workflow_task.py`, and `tools/workflow-harness/adapters/`, together with
the research and execution Skills. No executable runtime code changes in this
materials update.

## Source, platform evidence, and remaining release work

Use [license and source](../SOURCE.md) to identify a distribution. Keep the
historical MIT-licensed public v1.1.0 tag separate from the current GPL-3.0-only
branches. The older public repository is not the corresponding source of the
new desktop candidate. A later release must publish its matching source with
its distribution archives.

The [desktop verification table](desktop-plugin.md#verification-boundary) is the
platform statement: macOS automated helper/package checks, no complete desktop
workflow verification, no actual Linux validation, and unsupported Windows
helpers. Existing Claude Code guidance is not proof of equivalent host behavior.

PARTNERNET SOFTWARE PTY LTD completed OpenAI business verification for its
PartnerNetSoftware organization and will upload the package as publisher. A real
Codex desktop install and complete improvement-and-resume task passed on
macOS on 2026-10-31; see the [verification table](desktop-plugin.md#verification-boundary).
Marketplace submission remains unfinished. The public
repository already has privacy/support pages and their README entry. This
description revision changes only the development materials; development
version 1.2.0 remains unreleased there.

The [official submission fields](https://developers.openai.com/plugins/deploy/submission#listing-metadata)
limit the name and subtitle to 30 characters, the long description to 4,000,
and each of up to three starter prompts to 128. The directory publisher comes
from the selected verified identity. The
[plugin guidelines](https://developers.openai.com/plugins/plugin-guidelines)
require accurate descriptions, published privacy information, and support details.
Preparing text and passing package checks do not establish eligibility or approval.
