#!/usr/bin/env python3
"""Select and run Optimization workflow checks from the current Git change set."""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable, Sequence


WORKFLOW_ROOT = PurePosixPath(".agents/skills")
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
CURRENT_RELEASE_TESTS = (
    FRAME_TEST,
    BUNDLE_TEST,
    SELECTOR_TEST,
    *DIRECTION_TESTS,
    *CURRENT_BATCH_TESTS,
)
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

DIRECTION_REFERENCES = {
    "campaign-cycle.md",
    "campaign-state.md",
    "entry-and-planning.md",
    "learning-loop.md",
    "planning-records.md",
}
ENTRY_REFERENCES = {
    "entry-code-planning.md",
    "entry-review.md",
}
BATCH_REFERENCES = {
    "batch-current.md",
    "batch-evaluation.md",
    "evaluation-protocol.md",
    "implementation-review.md",
    "technical-design.md",
    "work-plan.md",
    "worker-interfaces.md",
}
RECOVERY_REFERENCES = {
    "closeout-and-claims.md",
    "packaging-and-recovery.md",
    "result-adoption.md",
}
LEGACY_REFERENCES = {
    "batch-interface.md",
    "batch-packet-format.md",
    "batch-result.md",
    "candidate-lifecycle.md",
    "entry-review-legacy.md",
    "review-snapshots.md",
}
CROSS_CUTTING_REFERENCES = {
    "frontier-core.md",
    "provenance-and-identity.md",
    "provenance-rollout.yaml",
    "source-modules.yaml",
    "user-facing-handoff.md",
}

SCRIPT_TESTS = {
    "authorization_target_contract.py": ENTRY_TESTS,
    "freeze_execution_baseline.py": ENTRY_TESTS,
    "frontier_batch.py": (FRONTIER_SCRIPTS / "test_frontier_batch.py",),
    "identity_bindings.py": (*PROVENANCE_TESTS, *ENTRY_TESTS),
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
    return len(parts) >= 3 and parts[:2] == WORKFLOW_ROOT.parts


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
        return CheckPlan(
            mode=mode,
            changed_paths=changed,
            workflow_paths=workflow,
            tests=tuple(path.as_posix() for path in CURRENT_RELEASE_TESTS),
            reasons=("release mode requires the current workflow contract suite",),
            run_bundle_validator=True,
            release=True,
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
        skill = parts[2]

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
            _add_tests(selected, reasons, CURRENT_BATCH_TESTS, "execution worker changed")
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
            continue

        if len(parts) < 4:
            escalate = True
            reasons.add(f"unclassified Frontier path: {raw_path}")
            continue

        area = parts[3]
        if area == "references":
            if path.name in CROSS_CUTTING_REFERENCES:
                escalate = True
                reasons.add(f"cross-cutting workflow contract changed: {path.name}")
            elif path.name in DIRECTION_REFERENCES:
                _add_tests(selected, reasons, DIRECTION_TESTS, f"direction contract changed: {path.name}")
            elif path.name in ENTRY_REFERENCES:
                _add_tests(selected, reasons, (*DIRECTION_TESTS, *CURRENT_BATCH_TESTS), f"Entry contract changed: {path.name}")
            elif path.name in BATCH_REFERENCES:
                _add_tests(selected, reasons, CURRENT_BATCH_TESTS, f"execution contract changed: {path.name}")
            elif path.name in RECOVERY_REFERENCES:
                _add_tests(selected, reasons, (*DIRECTION_TESTS, *CURRENT_BATCH_TESTS), f"current recovery contract changed: {path.name}")
            elif path.name in LEGACY_REFERENCES:
                _add_tests(selected, reasons, (*ENTRY_TESTS, *LEGACY_BATCH_TESTS, *RECOVERY_TESTS), f"legacy compatibility contract changed: {path.name}")
            continue

        if area == "scripts":
            if len(parts) >= 5 and parts[4] == "frontier_review":
                _add_tests(
                    selected,
                    reasons,
                    REVIEW_PREPARATION_TESTS,
                    "review preparation module changed",
                )
                continue
            if len(parts) >= 5 and parts[4] == "frontier_provenance":
                if path.name in {"review_contract.py", "review_subject.py"}:
                    _add_tests(
                        selected,
                        reasons,
                        REVIEW_PREPARATION_TESTS,
                        "review subject contract changed",
                    )
                    continue
                _add_tests(
                    selected,
                    reasons,
                    (*PROVENANCE_TESTS, *ENTRY_TESTS, *LEGACY_BATCH_TESTS, *RECOVERY_TESTS),
                    "shared provenance module changed",
                )
                continue
            mapped = SCRIPT_TESTS.get(path.name)
            if mapped:
                _add_tests(selected, reasons, mapped, f"workflow script changed: {path.name}")
            elif path.suffix == ".py":
                escalate = True
                reasons.add(f"unclassified workflow Python changed: {raw_path}")

    if escalate:
        selected = {path.as_posix() for path in CURRENT_RELEASE_TESTS}
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
