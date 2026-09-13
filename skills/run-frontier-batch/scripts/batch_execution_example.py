#!/usr/bin/env python3
"""Executable usage example, not a generic runner or a project prerequisite."""

from __future__ import annotations

import argparse
from collections.abc import Callable, Mapping
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any

# Locate the sibling Skill in either a Codex or Claude Code installation.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "frontier-optimization" / "scripts"))
from frontier_batch import (  # noqa: E402
    Action, ActionOutcome, Batch, CandidateRevision, ConcludeBatch, Consequence,
    DefineBatch, GovernanceResolver, OperationBinding, OperationResult, ReviseBatch,
)


from saved_git import normalize_path, read_file


InputReader = Callable[[Path, str, CandidateRevision | None], bytes]


def inspect_inputs(repo: Path, batch_name: str) -> ActionOutcome:
    """Query local availability without invoking the later observation.

    This sample query promises neither input validity nor selected-byte identity.
    It is independent of the measurement's checks and single-use effects.
    """
    def operation(action: Action, context: Mapping[str, Any]) -> OperationResult:
        paths = action.details["paths"]
        return OperationResult(status="completed", result={
            "available": [path for path in paths if (repo / path).is_file()],
        })

    batch = Batch.open(repo, batch_name, operations={
        "inspect-input-availability": OperationBinding(operation, ()),
    })
    return batch.perform(Action(
        key="inspect-input-availability", operation="inspect-input-availability",
        kind="query", repeatable=True,
        details={"paths": batch.view.scope},
    ))


def read_input(repo: Path, path: str, candidate: CandidateRevision | None) -> bytes:
    """Use the selected input bytes when this observation has a selection."""
    path = normalize_path(path)
    if candidate is not None:
        if path not in candidate.paths:
            raise ValueError("example input is outside the selected revision")
        return read_file(repo, candidate.commit, path)
    target = (repo / path).resolve()
    target.relative_to(repo.resolve())
    return target.read_bytes()


def validate_result(result: Mapping[str, Any], inputs: list[str]) -> None:
    """Keep observation outcomes separate from a known support failure."""
    rows = result["rows"]
    if len(rows) > len(inputs):
        raise ValueError("excessive observed rows")
    if [row["path"] for row in rows] != inputs[:len(rows)]:
        raise ValueError("observed rows do not match the input prefix")
    statuses = [row["status"] for row in rows]
    if result["outcome"] == "positive":
        valid = len(rows) == len(inputs) and all(value == "accepted" for value in statuses)
    elif result["outcome"] == "negative":
        valid = bool(rows) and statuses[-1] == "rejected" and all(value == "accepted" for value in statuses[:-1])
    elif result["outcome"] == "support_failure":
        valid = (
            len(rows) < len(inputs) and all(value == "accepted" for value in statuses)
            and result["failure"]["path"] == inputs[len(rows)]
        )
    else:
        valid = False
    if not valid:
        raise ValueError("outcome does not describe the observed sequence")


def execute(
    repo: Path,
    batch_name: str,
    *,
    reader: InputReader = read_input,
    required_reviews: tuple[str, ...] = (),
    required_checks: tuple[str, ...] = (),
    governance: GovernanceResolver | None = None,
) -> ActionOutcome:
    """Run the observation with requirements chosen for this action.

    Retained Batch review references are evidence, not an implicit gate list.
    """
    view = Batch.open(repo, batch_name).view
    definition = view.measurement_definition
    if definition is None:
        raise ValueError("example requires a Measurement Definition")
    inputs = definition["inputs"]
    if not isinstance(inputs, list) or not inputs or not all(isinstance(p, str) for p in inputs):
        raise ValueError("example requires a nonempty input list")
    candidate = view.candidate_revision
    single_use = bool(definition.get("nonrepeatable_unit"))
    effects = ("single_use_consumption",) if single_use else ()

    def operation(action: Action, context: Mapping[str, Any]) -> OperationResult:
        # Batch supplies the definition accepted at execution, not a prose copy.
        active = context["measurement_definition"]
        rows = []
        failure = None
        read_count = 0
        for path in active["inputs"]:
            raw = reader(repo, path, action.candidate)
            read_count += 1
            try:
                document = json.loads(raw)
                status = document["status"]
                if status not in {"accepted", "rejected"}:
                    raise ValueError("unsupported status in example input")
            except (ValueError, KeyError, TypeError) as exc:
                failure = {"path": path, "reason": str(exc)}
                break
            rows.append({"path": path, "status": status})
            if status == "rejected":
                break
        result = {
            "outcome": "support_failure" if failure else (
                "negative" if rows[-1]["status"] == "rejected" else "positive"
            ),
            "rows": rows,
        }
        if failure:
            result["failure"] = failure
        validate_result(result, active["inputs"])
        consequences = ()
        if effects:
            unit = active["nonrepeatable_unit"]
            consequences = (Consequence(
                kind="single_use_consumption",
                idempotency_key=f"{context['batch']}:{unit}",
                details={"nonrepeatable_unit": unit},
            ),)
        return OperationResult(
            status="failed" if failure else "completed", result=result,
            resource_use={"records": read_count}, consequences=consequences,
        )

    batch = Batch.open(
        repo, batch_name, governance=governance,
        operations={"observe-status-sequence": OperationBinding(operation, effects)},
    )
    return batch.perform(Action(
        key="observe-status-sequence", operation="observe-status-sequence", kind="measurement",
        candidate=candidate, required_reviews=required_reviews, required_checks=required_checks,
        requested_resources={"records": len(inputs)},
        possible_consequences=effects, repeatable=not single_use,
    ))


def read_result(repo: Path, batch_name: str) -> Mapping[str, Any]:
    """Reopen a settled observation or support failure without retrying work."""
    attempt = Batch.open(repo, batch_name).view.latest_attempt
    if attempt is None:
        raise ValueError("no observation has started")
    if attempt["status"] not in {"completed", "failed"}:
        raise ValueError("observation is not settled; inspect the saved Attempt")
    result = attempt["result"]
    validate_result(result, attempt["measurement_definition"]["inputs"])
    return result


def prepare_demo(repo: Path, statuses: tuple[str, ...], *, single_use: bool = False) -> Batch:
    """Coordinator-side setup in a fresh disposable repository only."""
    repo.mkdir(parents=True, exist_ok=True)
    if any(repo.iterdir()):
        raise ValueError("demo setup requires an empty directory")
    subprocess.run(["git", "init", "-q", str(repo)], check=True, capture_output=True)
    inputs = []
    for index, status in enumerate(statuses):
        path = f"input-{index}.json"
        (repo / path).write_text(json.dumps({"status": status}) + "\n", encoding="utf-8")
        inputs.append(path)
    batch = Batch.open(repo, "B001")
    batch.apply(DefineBatch(
        objective="Observe a retained status sequence.",
        acceptance="Retain all accepted rows or stop at the first rejection.",
        scope=tuple(inputs), resource_limits={"records": len(inputs)},
        expected_consequences=("single_use_consumption",) if single_use else (),
    ))
    definition = {
        "mode": "diagnostic-only", "question": "Does the sequence contain a rejection?",
        "comparator": "not applicable", "metric": "first rejection or all accepted",
        "scope": "the listed retained documents in order", "inputs": inputs,
        "resource_ceiling": {"records": len(inputs)},
        "execution_owner": "example worker", "result_owner": "example Coordinator",
        "evidence_limit": "the listed retained status documents only",
        "interpretation_limit": "no performance or provider-compatibility inference",
    }
    if single_use:
        definition.update(
            nonrepeatable_unit="demonstration-unit", resource_owner="workflow",
            consumption_control="The installed adapter consumes this test unit at first read.",
        )
    batch.apply(ReviseBatch("Set the example observation.", measurement_definition=definition))
    return batch


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", action="store_true", required=True)
    parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="frontier-execution-example-") as directory:
        repo = Path(directory)
        prepare_demo(repo, ("accepted", "rejected", "accepted"))
        execute(repo, "B001")
        result = read_result(repo, "B001")
        # This is the demo Coordinator, not the worker's execute() function.
        view = Batch.open(repo, "B001").apply(ConcludeBatch(
            "completed", result, "A negative prefix answers the assigned example question.",
        ))
        print(json.dumps({"status": view.status, "result": result}, sort_keys=True))


if __name__ == "__main__":
    main()
