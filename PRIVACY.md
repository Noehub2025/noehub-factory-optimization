# Aka Optimization privacy policy

Effective date: October 31, 2026.

Aka Optimization is published by **PARTNERNET SOFTWARE PTY LTD** (ACN 621 438 622),
Sydney, New South Wales, Australia. It is developed by **Noehub**,
**Hangzhou Boshu Technology Co., Ltd.**, Hangzhou, Zhejiang, China, which handles
support and privacy requests on the publisher's behalf. In this policy, "we"
means the publisher and Noehub. Contact
[support@noehub.com](mailto:support@noehub.com) for privacy questions or requests.

This policy covers the distributed Skills, local helper scripts, and optional
GitHub integrations in the Noehub Factory Optimization repositories, now
presented as Aka Optimization. It applies to version 1.2.0 and later, including
the desktop plugin and its project setup helper.

## Files and information used for your task

The agent works with the material you make available through its host application
and the tools allowed for your task. Depending on that task, this may include:

- Project code, documents, data, existing instructions, and Git history.
- Your goal, preferences, limits, decisions, and selected source material.
- Experiment inputs, results, comparisons, command output, and error messages.
- File paths, version identifiers, and local environment information needed for
  setup or troubleshooting, such as Python and dependency versions.

Files and output can contain personal information if you include it. Share only
what is needed for the task. Do not put passwords, access keys, or other secrets
into prompts, task records, public issues, or support attachments.

This information is used to understand the work, make and compare changes,
record what happened, and recover the task later. The host application's access
controls and your task instructions determine which files and tools are
available; this plugin is not a separate file-access security boundary.

## What is saved locally

The desktop setup helper checks the selected Git project and local dependencies.
When applied, it adds a marked link to the effective root instruction file and
creates `.noehub/workflow.md` and `.noehub/setup.json`. Existing project rules
remain in place. The setup helper itself makes no network requests and does not
install dependencies automatically.

Workflow task records normally live under `docs/skills/optimization/` in your
project. Depending on the tools you use, the project may also retain generated
files, Git snapshots, experiment artifacts, and recovery records. The optional
current-conversation entry records selected requests and receipts under
`artifacts/workflow-harness/direction-calls/`; explicitly configured command
execution can also save command output and error messages there. Additional GitHub
integrations keep their own local run records.

These records have no automatic time-based deletion. You control how long they
remain in your project and any copies, Git history, backups, or remote repositories
you maintain. Uninstalling the plugin does not delete them.

## When information can leave your computer

Local storage does not mean that all processing stays on your device:

- **Host application and model provider.** Codex or another selected host may
  send prompts, selected file contents, tool results, and other task context to
  its model services under your account settings and that provider's policies.
- **External tools and services.** Research can use the host's web search,
  browser, connectors, or other tools. Your task may also use explicitly selected
  external commands, services, or model runners. Their inputs and results are
  handled by those services under their own terms and settings.
- **Dependency installation.** If you choose to install dependencies, the package
  tools contact the repositories or mirrors you configure.
- **Sharing and publication.** If you publish project files, push a repository,
  or open an issue, the selected hosting service receives that material. A public
  repository or issue is visible to other people.

The distributed code contains no built-in Noehub analytics, telemetry collector,
or endpoint that automatically uploads your project to Noehub. Installing it
does not create a Noehub account. Noehub does not automatically receive your
project files or prompts through this distribution.

The optional Codex Hook is distributed separately on GitHub. It reads saved work
context and supported event information to supply context to Codex. Separate
GitHub adapters can call Codex, configured subprocesses, or selected web
addresses when used. Installing the desktop Skills package does not install
or activate those optional Hook integrations.

## Information you send to support

If you email us, Noehub receives your email address, message, and any details or
attachments you choose to send. We use them to answer your question, investigate
the reported problem, and handle your privacy request. They are available to
the people handling support and the email service providers that deliver and
store the correspondence. We do not use support submissions for advertising
or sell them.

We delete support emails and their attachments within **90 days after the issue
is closed**. You may request earlier deletion at
[support@noehub.com](mailto:support@noehub.com). This support rule does not set
the retention period for your local project, GitHub records, or data held by
your host application and other service providers.

Public GitHub issues and comments may remain available as part of the project's
public history. Their visibility, copies, and retention are not governed by
the support-email deletion period. Use email for private support requests and
remove sensitive information before sending any diagnostic material.

## Your choices

- Choose which project, files, tools, and services the host can access, and change
  those permissions in the host or relevant service.
- Stop an active task through the host. Removing a plugin alone may not stop a
  process that is already running.
- Disconnect desktop setup by removing its marked `noehub-optimization` link
  from the effective root instruction file and the two generated `.noehub/`
  files, after preserving any edits you need. Remove an independently installed
  Hook through the host's Hook settings as well.
- Keep or remove local task records separately. Deleting a working file does
  not remove earlier copies from Git history, backups, or published repositories.
- Use the host's and other providers' controls for information held by them.
- Ask Noehub about the support information it holds about you, request a
  correction, or request deletion by emailing the address above. Include only
  enough context to identify the correspondence.

## Policy updates

We publish changes to this policy in the public repository and update the
effective date. The policy included with an archive describes that distribution;
the public copy describes our current practices. Check the corresponding source
and version when reviewing an older release.
