#!/usr/bin/env python3
"""Select and run Optimization workflow checks from the current Git change set."""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable, Sequence

import yaml


INSTALLED_SKILLS_ROOT = Path(__file__).resolve().parents[2]


def _installed_workflow_root() -> PurePosixPath:
    """Find this installed Skill bundle relative to its owning Git repository."""
    for candidate in (INSTALLED_SKILLS_ROOT, *INSTALLED_SKILLS_ROOT.parents):
        if (candidate / ".git").exists():
            return PurePosixPath(INSTALLED_SKILLS_ROOT.relative_to(candidate).as_posix())
    # Preserve the conventional project installation path outside a checkout.
    return PurePosixPath(".agents/skills")


WORKFLOW_ROOT = _installed_workflow_root()
FRONTIER_SCRIPTS = WORKFLOW_ROOT / "frontier-optimization/scripts"
FRAME_TEST = WORKFLOW_ROOT / "frame-optimization/scripts/test_validate_frame_skill_bundle.py"
BUNDLE_TEST = FRONTIER_SCRIPTS / "test_validate_current_frontier_skill_bundle.py"
SELECTOR_TEST = FRONTIER_SCRIPTS / "test_run_workflow_checks.py"
DIRECTION_TESTS = (
    FRONTIER_SCRIPTS / "test_direction_resolver_contract.py",
    FRONTIER_SCRIPTS / "test_finding_effects.py",
)
PROVENANCE_TESTS = (
    FRONTIER_SCRIPTS / "test_git_project_content.py",
    FRONTIER_SCRIPTS / "test_frontier_provenance.py",
    FRONTIER_SCRIPTS / "test_project_snapshot.py",
    FRONTIER_SCRIPTS / "test_package_frontier_handoff.py",
)
REVIEW_PREPARATION_TESTS = (
    FRONTIER_SCRIPTS / "test_frontier_review_preparation.py",
    FRONTIER_SCRIPTS / "test_frontier_provenance.py",
)
ENTRY_TESTS = (
    FRONTIER_SCRIPTS / "test_validate_entry_packet.py",
    FRONTIER_SCRIPTS / "test_validate_authorization_adoption.py",
    FRONTIER_SCRIPTS / "test_freeze_execution_baseline.py",
)
CURRENT_BATCH_TESTS = (FRONTIER_SCRIPTS / "test_frontier_batch.py",)
EXECUTION_EXAMPLE_TEST = WORKFLOW_ROOT / "run-frontier-batch/scripts/test_batch_execution_example.py"
REFERENCE_TESTS = (
    FRONTIER_SCRIPTS / "test_frontier_references.py",
    FRONTIER_SCRIPTS / "test_frontier_context.py",
    FRONTIER_SCRIPTS / "test_current_use.py",
)
LEGACY_BATCH_TESTS = (
    FRONTIER_SCRIPTS / "test_validate_batch_packet.py",
    FRONTIER_SCRIPTS / "test_validate_batch_result.py",
    FRONTIER_SCRIPTS / "test_validate_candidate_package.py",
)
RECOVERY_TESTS = (
    FRONTIER_SCRIPTS / "test_validate_candidate_recovery.py",
    FRONTIER_SCRIPTS / "test_slice7_end_to_end.py",
)
DESIGN_TESTS = (FRONTIER_SCRIPTS / "test_slice7_end_to_end.py",)
# The installed source inventory owns current/legacy membership. Selection is
# pure after loading this deployment input, never campaign or project state.
_SOURCE_MODULES = yaml.safe_load(
    (Path(__file__).parents[1] / "references/source-modules.yaml").read_text()
)["modules"]
CURRENT_RELEASE_TESTS = tuple(
    WORKFLOW_ROOT / path for path in _SOURCE_MODULES["release-validation"]["files"]
    if PurePosixPath(path).name.startswith("test_") and path.endswith(".py")
)
LEGACY_TESTS = tuple(
    WORKFLOW_ROOT / path for path in _SOURCE_MODULES["legacy-compatibility"]["files"]
    if PurePosixPath(path).name.startswith("test_") and path.endswith(".py")
)
_SOURCE_OWNERS: dict[str, set[str]] = {}
for _module, _body in _SOURCE_MODULES.items():
    for _path in _body["files"]:
        _SOURCE_OWNERS.setdefault((WORKFLOW_ROOT / _path).as_posix(), set()).add(_module)

MODULE_TESTS = {
    "direction": DIRECTION_TESTS,
    "batch-runtime": (*CURRENT_BATCH_TESTS, EXECUTION_EXAMPLE_TEST, *REFERENCE_TESTS, FRONTIER_SCRIPTS / "test_saved_git.py"),
    "execution": CURRENT_BATCH_TESTS,
    "evidence": (*DIRECTION_TESTS, *CURRENT_BATCH_TESTS),
    "claims": DIRECTION_TESTS,
    "validator-runtime": (BUNDLE_TEST, SELECTOR_TEST),
    "validator-support": (*PROVENANCE_TESTS, *ENTRY_TESTS, *LEGACY_BATCH_TESTS, *RECOVERY_TESTS),
    "legacy-validation": (*ENTRY_TESTS, *LEGACY_BATCH_TESTS, *RECOVERY_TESTS),
}

FRAME_SKILLS = {
    "frame-optimization",
    "design-measurement",
    "research-optimization",
    "grill-optimization",
    "review-optimization",
    "review-representation",
}
DESIGN_SKILLS = {"design-implementation"}
DIRECTION_SKILLS = {"research-frontier", "grill-frontier", "reflect-frontier"}

# More focused checks where the document's action spans its inventory owner.
REFERENCE_TESTS_BY_NAME = {
    "entry-code-planning.md": (*DIRECTION_TESTS, *CURRENT_BATCH_TESTS),
    "entry-review.md": (*DIRECTION_TESTS, *CURRENT_BATCH_TESTS),
}

SCRIPT_TESTS = {
    "current_use.py": REFERENCE_TESTS,
    "frontier_context.py": REFERENCE_TESTS,
    "frontier_references.py": (*REFERENCE_TESTS, *CURRENT_BATCH_TESTS),
    "saved_git.py": (*CURRENT_BATCH_TESTS, EXECUTION_EXAMPLE_TEST, *REFERENCE_TESTS, FRONTIER_SCRIPTS / "test_saved_git.py"),
    "authorization_target_contract.py": ENTRY_TESTS,
    "freeze_execution_baseline.py": ENTRY_TESTS,
    "frontier_batch.py": (*CURRENT_BATCH_TESTS, EXECUTION_EXAMPLE_TEST),
    "identity_bindings.py": (*PROVENANCE_TESTS, *ENTRY_TESTS, *REFERENCE_TESTS),
    "package_frontier_handoff.py": (*PROVENANCE_TESTS, *RECOVERY_TESTS),
    "post_adoption_state.py": ENTRY_TESTS,
    "project_snapshot.py": (*PROVENANCE_TESTS, *ENTRY_TESTS),
    "validate_authorization_adoption.py": ENTRY_TESTS,
    "validate_batch_packet.py": (*LEGACY_BATCH_TESTS, FRONTIER_SCRIPTS / "test_slice7_end_to_end.py"),
    "validate_batch_result.py": (*LEGACY_BATCH_TESTS, FRONTIER_SCRIPTS / "test_slice7_end_to_end.py"),
    "validate_candidate_package.py": LEGACY_BATCH_TESTS,
    "validate_candidate_recovery.py": RECOVERY_TESTS,
    "validate_entry_packet.py": (*ENTRY_TESTS, FRONTIER_SCRIPTS / "test_slice7_end_to_end.py"),
    "validate_frontier_skill_bundle.py": (BUNDLE_TEST,),
    "frontier_provenance_cli.py": (*PROVENANCE_TESTS, *ENTRY_TESTS, *LEGACY_BATCH_TESTS, *RECOVERY_TESTS),
    "frontier_review_cli.py": REVIEW_PREPARATION_TESTS,
    "run_workflow_checks.py": (SELECTOR_TEST,),
    "workflow_source_binding.py": (*ENTRY_TESTS, *LEGACY_BATCH_TESTS, *RECOVERY_TESTS),
}


@dataclass(frozen=True)
class CheckPlan:
    mode: str
    changed_paths: tuple[str, ...]
    workflow_paths: tuple[str, ...]
    tests: tuple[str, ...]
    reasons: tuple[str, ...]
    run_bundle_validator: bool
    release: bool


def _as_posix(path: str | PurePosixPath) -> str:
    normalized = PurePosixPath(str(path)).as_posix()
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def _is_workflow_path(path: str) -> bool:
    parts = PurePosixPath(path).parts
    prefix = WORKFLOW_ROOT.parts
    return len(parts) > len(prefix) and parts[: len(prefix)] == prefix


def _add_tests(
    selected: set[str],
    reasons: set[str],
    tests: Iterable[PurePosixPath],
    reason: str,
) -> None:
    selected.update(path.as_posix() for path in tests)
    reasons.add(reason)


def select_checks(paths: Iterable[str], mode: str) -> CheckPlan:
    """Return a deterministic check plan without reading or changing repository state."""
    if mode not in {"fast", "affected", "release"}:
        raise ValueError(f"unsupported mode: {mode}")

    changed = tuple(sorted({_as_posix(path) for path in paths if str(path).strip()}))
    workflow = tuple(path for path in changed if _is_workflow_path(path))
    if mode == "release":
        affected = select_checks(changed, "affected")
        tests = set(affected.tests) | {path.as_posix() for path in CURRENT_RELEASE_TESTS}
        return CheckPlan(
            mode, changed, workflow, tuple(sorted(tests)),
            tuple(sorted({*affected.reasons, "release mode requires current tests plus affected compatibility tests"})),
            True, True,
        )

    if not workflow:
        return CheckPlan(mode, changed, (), (), (), False, False)

    if mode == "fast":
        return CheckPlan(
            mode=mode,
            changed_paths=changed,
            workflow_paths=workflow,
            tests=(),
            reasons=("workflow files changed; validate the live bundle once",),
            run_bundle_validator=True,
            release=False,
        )

    selected: set[str] = set()
    reasons: set[str] = set()
    escalate = False

    for raw_path in workflow:
        path = PurePosixPath(raw_path)
        parts = path.parts
        prefix_length = len(WORKFLOW_ROOT.parts)
        skill = parts[prefix_length]

        if path.name.startswith("test_") and path.suffix == ".py":
            _add_tests(selected, reasons, (path,), f"changed test: {raw_path}")
            continue

        if skill in FRAME_SKILLS:
            _add_tests(selected, reasons, (FRAME_TEST,), f"framing Skill changed: {skill}")
            continue
        if skill in DESIGN_SKILLS:
            _add_tests(selected, reasons, CURRENT_BATCH_TESTS, f"implementation designer changed: {skill}")
            continue
        if skill in DIRECTION_SKILLS:
            _add_tests(selected, reasons, DIRECTION_TESTS, f"direction worker changed: {skill}")
            continue
        if skill == "run-frontier-batch":
            tests = (EXECUTION_EXAMPLE_TEST,) if path.name == "batch_execution_example.py" else (*CURRENT_BATCH_TESTS, EXECUTION_EXAMPLE_TEST)
            _add_tests(selected, reasons, tests, "execution worker changed")
            continue
        if skill == "review-frontier":
            _add_tests(
                selected,
                reasons,
                CURRENT_RELEASE_TESTS,
                "shared Frontier reviewer changed",
            )
            continue
        if skill != "frontier-optimization":
            escalate = True
            reasons.add(f"unclassified workflow Skill changed: {skill}")
            continue

        if len(parts) < prefix_length + 2:
            escalate = True
            reasons.add(f"unclassified Frontier path: {raw_path}")
            continue

        if path.name == "SKILL.md" or parts[prefix_length + 1] == "agents":
            escalate = True
            reasons.add("Frontier coordinator entrypoint changed")
            continue

        area = parts[prefix_length + 1]
        if area == "references":
            focused = REFERENCE_TESTS_BY_NAME.get(path.name)
            owners = _SOURCE_OWNERS.get(raw_path, set())
            if focused:
                _add_tests(selected, reasons, focused, f"action contract changed: {path.name}")
            elif "graph-core" in owners or not owners:
                escalate = True
                reasons.add(f"shared or unclassified workflow contract changed: {path.name}")
            else:
                for owner in sorted(owners):
                    _add_tests(selected, reasons, MODULE_TESTS.get(owner, CURRENT_RELEASE_TESTS), f"{owner} contract changed: {path.name}")
            continue

        if area == "scripts":
            if parts[prefix_length + 2 : prefix_length + 4] == ("fixtures", "slice7"):
                _add_tests(selected, reasons, RECOVERY_TESTS, "legacy recovery fixture changed")
                continue
            if len(parts) >= prefix_length + 3 and parts[prefix_length + 2] == "frontier_review":
                _add_tests(
                    selected,
                    reasons,
                    REVIEW_PREPARATION_TESTS,
                    "review preparation module changed",
                )
                continue
            if len(parts) >= prefix_length + 3 and parts[prefix_length + 2] == "frontier_provenance":
                if path.name in {"review_contract.py", "review_subject.py"}:
                    _add_tests(
                        selected,
                        reasons,
                        REVIEW_PREPARATION_TESTS,
                        "review subject contract changed",
                    )
                    continue
                tests = (*PROVENANCE_TESTS, *ENTRY_TESTS, *LEGACY_BATCH_TESTS, *RECOVERY_TESTS)
                if "validator-support" in _SOURCE_OWNERS.get(raw_path, set()):
                    tests = (*tests, BUNDLE_TEST)
                _add_tests(selected, reasons, tests, "shared provenance module changed")
                continue
            mapped = SCRIPT_TESTS.get(path.name)
            if mapped:
                _add_tests(selected, reasons, mapped, f"workflow script changed: {path.name}")
            elif "legacy-validation" in _SOURCE_OWNERS.get(raw_path, set()):
                _add_tests(selected, reasons, LEGACY_TESTS, f"legacy implementation changed: {path.name}")
            elif path.suffix == ".py":
                escalate = True
                reasons.add(f"unclassified workflow Python changed: {raw_path}")
            else:
                for owner in sorted(_SOURCE_OWNERS.get(raw_path, set())):
                    _add_tests(selected, reasons, MODULE_TESTS.get(owner, CURRENT_RELEASE_TESTS), f"{owner} input changed: {path.name}")

    if escalate:
        selected.update(path.as_posix() for path in CURRENT_RELEASE_TESTS)
        reasons.add("affected mode escalated to the current contract suite")

    return CheckPlan(
        mode=mode,
        changed_paths=changed,
        workflow_paths=workflow,
        tests=tuple(sorted(selected)),
        reasons=tuple(sorted(reasons)),
        run_bundle_validator=True,
        release=escalate,
    )


def _git(repo_root: Path, *args: str) -> tuple[str, ...]:
    completed = subprocess.run(
        ("git", "-C", str(repo_root), *args),
        check=True,
        capture_output=True,
        text=True,
    )
    return tuple(line for line in completed.stdout.splitlines() if line)


def collect_changed_paths(repo_root: Path, base: str | None = None) -> tuple[str, ...]:
    """Collect committed, staged, unstaged, and untracked paths from Git."""
    paths: set[str] = set()
    if base:
        _git(repo_root, "rev-parse", "--verify", f"{base}^{{commit}}")
        paths.update(_git(repo_root, "diff", "--name-only", "--diff-filter=ACMRD", f"{base}...HEAD"))
    paths.update(_git(repo_root, "diff", "--name-only", "--diff-filter=ACMRD"))
    paths.update(_git(repo_root, "diff", "--cached", "--name-only", "--diff-filter=ACMRD"))
    paths.update(_git(repo_root, "ls-files", "--others", "--exclude-standard"))
    return tuple(sorted(_as_posix(path) for path in paths))


def _commands(plan: CheckPlan, repo_root: Path, base: str | None) -> list[tuple[str, ...]]:
    commands: list[tuple[str, ...]] = [
        ("git", "-C", str(repo_root), "diff", "--check"),
        ("git", "-C", str(repo_root), "diff", "--cached", "--check"),
    ]
    if base:
        commands.append(("git", "-C", str(repo_root), "diff", "--check", f"{base}...HEAD"))
    if plan.run_bundle_validator:
        commands.append(
            (
                sys.executable,
                str(repo_root / FRONTIER_SCRIPTS / "validate_frontier_skill_bundle.py"),
                str(repo_root / WORKFLOW_ROOT),
            )
        )
    if plan.tests:
        pytest = [sys.executable, "-m", "pytest", "-q"]
        if plan.release:
            pytest.extend(("--durations=20",))
        pytest.extend(str(repo_root / path) for path in plan.tests)
        commands.append(tuple(pytest))
    return commands


def _print_plan(plan: CheckPlan, commands: Sequence[Sequence[str]]) -> None:
    print(f"mode: {plan.mode}")
    print(f"workflow changes: {len(plan.workflow_paths)}")
    if plan.reasons:
        print("reasons:")
        for reason in plan.reasons:
            print(f"  - {reason}")
    if plan.tests:
        print("selected tests:")
        for test in plan.tests:
            print(f"  - {test}")
    else:
        print("selected tests: none")
    print("commands:")
    for command in commands:
        print("  - " + " ".join(command))


def _run(command: Sequence[str], repo_root: Path) -> int:
    is_bundle_validator = any(
        Path(argument).name == "validate_frontier_skill_bundle.py"
        for argument in command
    )
    completed = subprocess.run(
        command,
        cwd=repo_root,
        capture_output=is_bundle_validator,
        text=is_bundle_validator,
    )
    if is_bundle_validator:
        if completed.returncode:
            if completed.stdout:
                print(completed.stdout, end="")
            if completed.stderr:
                print(completed.stderr, end="", file=sys.stderr)
        else:
            print("PASS: live workflow bundle")
    return completed.returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("fast", "affected", "release"), default="affected")
    parser.add_argument("--base", help="include committed changes from BASE...HEAD")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    try:
        paths = collect_changed_paths(repo_root, args.base)
        plan = select_checks(paths, args.mode)
        commands = _commands(plan, repo_root, args.base)
        _print_plan(plan, commands)
        if args.dry_run:
            return 0
        for command in commands:
            returncode = _run(command, repo_root)
            if returncode:
                return returncode
        return 0
    except (OSError, subprocess.CalledProcessError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
