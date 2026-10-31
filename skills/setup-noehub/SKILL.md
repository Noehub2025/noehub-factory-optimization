---
name: setup-noehub
description: Set up or update Aka Optimization in a selected local Git repository after installing the desktop plugin. Check dependencies, preserve existing project instructions, and prepare the first task without starting experiments.
---

# Set up Aka Optimization

Connect this installed plugin to the user's selected project. Explicit user
instructions and existing project rules control this setup. Installation does
not authorize experiments, model calls, external publication, or a Hook.

1. Use the project explicitly selected by the user or the current task. If the
   destination is ambiguous, ask for it before writing. Read its effective
   `AGENTS.md`, `AGENTS.override.md`, and applicable nested instructions. Read
   `CLAUDE.md` only when it governs this environment. Preserve existing rules.
2. Read [desktop runtime](references/desktop-runtime.md). Resolve the package
   root from this host-supplied `SKILL.md`: it is two directories above this
   file. Never use the project's working directory as the plugin location.
   If the root manifest or setup helper is absent, this is an isolated Skill
   installation. Use the complete desktop package for automated setup; do not
   infer missing files from an unrelated checkout.
3. Run the bundled setup helper with an explicit project root:

   ```sh
   python /absolute/plugin/root/scripts/noehub_setup.py --root /absolute/project
   ```

   Substitute the actual paths. This plans changes and reports dependencies
   without writing. Use an existing Python 3.10+ interpreter with PyYAML when
   available. If missing, arrange an isolated project environment as described
   in the runtime guide; do not change system Python or download implicitly.
4. Inspect the plan and existing instruction content. The helper adds one link
   to `.noehub/workflow.md`, preserving the existing instruction file's bytes.
   It copies shared guidance only when the project has no existing shared
   workflow sections. If `review_existing_guidance` is true, compare those
   sections with the package's shared guidance and reconcile only meaningful
   differences within the user's scope. It does not certify semantic agreement.
   Respect a root override; an existing empty override also needs this check.
5. When setup is authorized and the proposed changes fit that scope, run the
   same command with `--apply`; no additional confirmation is needed for that
   authorized setup. Conflicting files or edited managed content require a
   scoped merge, not a force overwrite. Re-run the plan afterward and inspect
   the resulting project instructions. Do not install Hooks, overwrite
   `CLAUDE.md`, duplicate the Skills into the project, or create a fake running
   task. Read the new guidance into this conversation; future discovery must
   be checked in the actual host.
6. Find `frame-optimization` and `frontier-optimization` in the host's available
   Skills, preferably from this same plugin. Load their host-supplied `SKILL.md`
   when invoking them; mentioning a name alone does not load a Skill. Check
   that the host can provide the independent contexts required by reviews.
   A different role name in the same conversation is not independent review.
   Report an unavailable capability and continue only unaffected work.

Return what changed, the dependency and host capabilities actually observed,
and a concrete first-task prompt using the user's objective. If none was given,
use an explicitly editable example:

> Use Aka Optimization to help this program run faster without changing its results.

Tell the user to replace the program example with their own goal and mention
any time or spending limits they already have. Explain that the conversation
helps clarify how to compare results and what can change. Use ordinary language
for the return; the user does not need to learn the internal Skill names first. These
starter prompts still need testing in the actual desktop host. If discovery or
routing fails, explain the specific issue and offer the explicit fallback:

> Use frame-optimization to clarify what I want to improve and how we will compare
> results, then use frontier-optimization to try approaches within my agreed limits.

Setup completion does not establish successful host installation, review
independence, or a completed optimization cycle. Do not start the example unless
the user requested that work.
