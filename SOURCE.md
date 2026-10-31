# License and corresponding source

Copyright (c) 2026 Ken Chen.

This development distribution is licensed under the
[GNU General Public License version 3 only](LICENSE) (`GPL-3.0-only`).
PARTNERNET SOFTWARE PTY LTD publishes Aka Optimization, and Noehub, Hangzhou
Boshu Technology Co., Ltd., develops it. Neither identity replaces the original
author or copyright notice.

## Identify the distribution you have

Generated archives include `distribution.json`, which records the package
profile, version, source commit, and hashes of the included files. The file
hashes identify the packaged bytes. A build can include uncommitted changes,
so its recorded commit alone does not always identify the contents.

The desktop Skills archive includes its Skill instructions, resources, and
Python source. The complete GitHub archive also includes the optional Codex
Hook's Rust source, Cargo manifests and lockfile, and the distribution build
scripts. The desktop archive does not contain a Hook binary or Rust host.

The public source repository is
[Noehub2025/noehub-factory-optimization](https://github.com/Noehub2025/noehub-factory-optimization).
The complete corresponding source for each version is its version tag, such as `v1.2.1`, and the
source archive attached to that version's GitHub Release. The older `v1.1.0` tag is not a
substitute for it.

## Match a future release to its source

For each public distribution, publish its complete corresponding source at an
immutable public commit and release tag, including the scripts and dependency
information needed to build the distributed components. Provide the matching
source archive alongside the packaged archives and link all of them from the
release notes. Include the license, exact source identity, archive checksums,
and build instructions. Verify that every packaged source file matches the
selected public source, accounting for the documented README replacement and
generated distribution records.

Do not distribute a new candidate as a public release while pointing only to
an older public snapshot or an inaccessible private commit. The release notes
must identify the source for that specific distribution. The
[GNU GPL version 3 text](https://www.gnu.org/licenses/gpl-3.0.html) is the license
authority; this source guide does not replace it.

## Historical public release

The existing
[`v1.1.0` release](https://github.com/Noehub2025/noehub-factory-optimization/releases/tag/v1.1.0)
retains the
[MIT license stored in that tag](https://github.com/Noehub2025/noehub-factory-optimization/blob/v1.1.0/LICENSE).
The public branch subsequently changed to GPL-3.0-only in commit
[`66d9787`](https://github.com/Noehub2025/noehub-factory-optimization/commit/66d97871dd223298c4c609d969619d4d77e4f08e).
The historical tag is unchanged. Always read the license in the source version
you are actually using.
