# Aka Optimization support

Contact **[support@noehub.com](mailto:support@noehub.com)** for help or privacy
requests. Aka Optimization is published by **Noehub**,
**Hangzhou Boshu Technology Co., Ltd.**

Aka Optimization is the public name for the workflow maintained in the Noehub
Factory Optimization repositories. Existing installation names and project
directories still use `noehub`. You do not need to rename an existing installation.

## Before you start

The public **1.1.0** release and the **1.2.0 development desktop candidate** are
different distributions. The public release has thirteen workflow Skills; it
does not include the candidate's desktop setup helper. The candidate has not
been submitted to the official Marketplace.

Read the instructions that came with your version. The public repository's
[README](https://github.com/Noehub2025/noehub-factory-optimization#readme)
describes the content on that branch; its existing public
installation commands do not install the private desktop candidate.

For the desktop candidate, the helper scripts require Git, Python 3.10 or later,
and PyYAML 6.x. Automated checks have been run on macOS. A real desktop
installation, the plain-language starter prompts, separate review conversations,
and a complete optimization-and-resume cycle have not been verified. Linux has
not been tested, and Windows is not supported by the current helper scripts.
The optional Hook supports Codex only and is separate from the Skills package.

## Tell us what happened

Start with a short description of what you wanted to do, what you expected,
and what happened instead. When relevant, include:

- The plugin or source version, and how you installed it.
- Your operating system and host application version.
- The smallest steps that reproduce the problem.
- A short, redacted error message or example that demonstrates it.

Do not send an entire project, full conversation history, private datasets,
credentials, or unedited diagnostic logs. Remove personal information, private
file paths, and secrets. We will ask for a smaller, specific example if more
information is needed.

You can also use the public
[GitHub issue tracker](https://github.com/Noehub2025/noehub-factory-optimization/issues)
for non-sensitive problems. Issues and their attachments are public. Use email
for private reports, including security concerns.

## Pause, disconnect, or remove saved work

Stop active work through your host application first. To remove the plugin,
use that host's plugin controls. For the complete desktop candidate, project
setup is separate: remove the marked `noehub-optimization` block from the
effective root instruction file and `.noehub/workflow.md` plus
`.noehub/setup.json`, preserving any content you added. Existing project rules
and separately installed Skills or Hooks need their own review before removal.

Task records and experiment results are yours to keep. They are not removed by
uninstalling the plugin. If you choose to delete them, account for copies in
Git history, backups, and remote repositories. Do not remove a whole project
instruction file merely because it contains the setup link.

## Privacy requests

See the [privacy policy](PRIVACY.md) for file access, external services, and
retention. Support emails and attachments are deleted within **90 days after
the issue is closed**. To request earlier deletion or a correction, email us
with enough context to find the relevant correspondence. This period does not
apply to public GitHub issues or records kept by your host or other services.

Support is handled by email; no guaranteed response time is offered. A bug report
or support exchange does not establish that a platform, integration, or task
outcome has been verified.
