"""Historical synthetic-only Codex acceptance adapter for the owner interface.

This adapter is deliberately limited to four authorized synthetic trials. It
cannot receive live task material. Other hosts implement the same OwnerReply
interface without depending on Codex. Widening this transport's data scope needs
separate authorization; the current trial runner is not a production entry.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time

REPOSITORY = Path(__file__).resolve().parents[3]
SKILL_SCRIPTS = next(
    (REPOSITORY / directory / "frontier-optimization/scripts"
     for directory in ("skills", ".agents/skills", ".claude/skills")
     if (REPOSITORY / directory / "frontier-optimization/scripts").is_dir()),
    None,
)
if SKILL_SCRIPTS is None:
    raise RuntimeError("Install the complete Frontier Skill before using this adapter")
sys.path.insert(0, str(SKILL_SCRIPTS))
from context_delivery import digest, retain_source
from professional_input import OwnerReply, prepare, request_text, selected_source

BINARY = "codex"
ACCEPTANCE_ROOT = REPOSITORY / "artifacts/workflow-harness/codex-owner-20261016"
TRIALS = ("allocation-1", "simple-1", "allocation-2", "simple-2")
MODEL, EFFORT, TIMEOUT = "gpt-6-astra", "xhigh", 180

COMMON = {
    "AGENTS.md": "Use the maintained [capabilities](knowledge.md) for this bounded local task.\n",
    "owner.md": "Select the concrete input and first useful observation. The proposal is revisable.\n",
    "knowledge.md": "# Available methods\n\nMaintained methods for the current local capabilities.\n\n"
        "[Shared-capacity allocation](allocation.md) covers indivisible requests competing for one capacity.\n"
        "[Fixed calibration](calibration.md) covers retained additive correction with unchanged units and device.\n",
    "allocation.md": "# Shared-capacity allocation\n\nFor indivisible requests sharing one capacity, "
        "evaluate feasible sets by terminal total return. Individually favorable priorities can consume "
        "capacity needed by a better set. For a small set, enumerating feasible subsets is sufficient; "
        "no optimizer framework is needed. Compare the chosen set with the incumbent under the same "
        "capacity and completion rule. Record both consumed capacity and total delivered value.\n",
    "calibration.md": "# Fixed calibration\n\nAn additive offset established on the same device and "
        "units can be retained while its applicability remains unchanged. Subtract the offset and inspect "
        "paired residuals against references. A new fitting stage is unnecessary for this observation. "
        "Reconsider the offset if device, units or observed residual behavior changes.\n",
}


def case(trial: str) -> tuple[dict, dict, dict]:
    if trial not in TRIALS:
        raise ValueError("only the four authorized synthetic trials are supported")
    if trial.startswith("allocation"):
        data = {"capacity": 12, "jobs": {"A": {"cost": 8, "value": 16},
                "B": {"cost": 6, "value": 11}, "C": {"cost": 6, "value": 11}},
                "proposal": {"selected": ["A"]},
                "completion": "Indivisible jobs; return is received only for completed jobs.",
                "interface": "choices.selected is a list of distinct job identifiers."}
        objective = "Maximize delivered value within shared capacity."
    else:
        data = {"readings": [13, 17, 12], "references": [10, 14, 9],
                "proposal": {"offset": 3}, "conditions": "Same device and units as retained calibration.",
                "interface": "choices.offset is the number subtracted from each reading."}
        objective = "Obtain a useful bounded observation of the retained calibration."
    files = {**COMMON, "inputs.json": json.dumps(data, sort_keys=True, indent=2)}
    definition = {"objective": objective, "acceptance": "A justified concrete input and useful first observation.",
                  "scope": ["synthetic local observation"], "measurement": None}
    spec = {"owner": "owner.md", "intended_decision": "Select the next concrete input and observation.",
            "consumer": "synthetic-observation", "operations": ["observe"],
            "sources": [{"path": "inputs.json"}], "conditions": {"synthetic": True}}
    return files, definition, spec


def validate_input(root: Path, trial: str, prompt: str) -> tuple[dict, ...]:
    """Check fixed approved bytes before constructing any model request."""
    if root.resolve() != (ACCEPTANCE_ROOT / trial).resolve():
        raise ValueError("Codex acceptance cannot read a live or arbitrary workspace")
    files, definition, spec = case(trial)
    if (root / ".agents").exists():
        raise ValueError("synthetic trials cannot load host or project Skills")
    for name, body in files.items():
        path = root / name
        if path.is_symlink() or path.read_text() != body:
            raise ValueError(f"synthetic input changed: {name}")
    expected = request_text(prepare(root, "B001", definition, spec))
    if prompt != expected:
        raise ValueError("owner request differs from the authorized synthetic input")
    return tuple(selected_source(root, {"path": name}) for name in files)


DISABLED_FEATURES = (
    "shell_tool", "unified_exec", "code_mode", "code_mode_host", "apps", "plugins",
    "browser_use", "computer_use", "in_app_browser", "memories", "hooks", "multi_agent",
    "multi_agent_v2", "shell_snapshot", "view_image", "skill_search",
    "skill_mcp_dependency_install", "image_generation", "workspace_dependencies", "goals",
)


def answer_schema(trial: str) -> dict:
    selected = {"type": "object", "properties": {"selected": {
        "type": "array", "items": {"type": "string", "enum": ["A", "B", "C"]}}},
        "required": ["selected"], "additionalProperties": False}
    offset = {"type": "object", "properties": {"offset": {"type": "number"}},
              "required": ["offset"], "additionalProperties": False}
    return {"type": "object", "additionalProperties": False,
            "properties": {"choices": selected if trial.startswith("allocation") else offset,
                           "rationale": {"type": "string"}, "observation": {"type": "string"},
                           "grounds": {"type": "array", "items": {"type": "object",
                               "properties": {"path": {"type": "string", "enum": list(COMMON) + ["inputs.json"]}},
                               "required": ["path"], "additionalProperties": False}}},
            "required": ["choices", "rationale", "observation", "grounds"]}


def command(directory: Path) -> list[str]:
    args = [BINARY, "--no-daemon", "exec", "--ephemeral", "--ignore-user-config", "--strict-config",
            "--skip-git-repo-check", "--json", "-s", "read-only", "-C", str(directory), "-m", MODEL,
            "--output-schema", str(directory / "answer-schema.json")]
    config = {"model_reasoning_effort": EFFORT, "approval_policy": "never", "web_search": "disabled",
              "agents.enabled": False, "project_doc_max_bytes": 0,
              "features.skip_host_skill_discovery": True,
              "memories.use_memories": False, "memories.generate_memories": False}
    for key, value in config.items():
        args += ["-c", key + "=" + json.dumps(value)]
    for feature in DISABLED_FEATURES:
        args += ["--disable", feature]
    return args + ["-"]


def parse_response(stdout: str) -> tuple[dict, dict]:
    events = [json.loads(line) for line in stdout.splitlines() if line.strip()]
    completed, messages, usage, thread, started = False, [], {}, None, False
    for event in events:
        kind = event.get("type")
        if kind in {"turn.failed", "error"}:
            raise ValueError("Codex reported a failed turn; see the retained stream")
        if kind == "thread.started":
            thread = event.get("thread_id")
        elif kind == "turn.started":
            started = True
        elif kind == "turn.completed":
            completed, usage = True, event.get("usage", {})
        elif kind in {"item.started", "item.updated", "item.completed"}:
            item = event.get("item", {})
            # These pre-turn CLI diagnostics describe the deliberately disabled
            # facilities. They are neither tool activity nor a failed model turn.
            if (not started and item.get("type") == "error"
                    and item.get("message", "").startswith((
                        "Under-development features enabled: skip_host_skill_discovery.",
                        "Code Mode is unavailable because code-mode host is disabled."))):
                continue
            if item.get("type") not in {"agent_message", "reasoning", "todo_list"}:
                raise ValueError("unexpected model-side tool activity; response cannot be adopted")
            if kind == "item.completed" and item.get("type") == "agent_message":
                messages.append(item.get("text", ""))
    if not completed or not messages:
        raise ValueError("Codex did not return a completed owner answer")
    answer = json.loads(messages[-1])
    if not isinstance(answer, dict):
        raise ValueError("Codex owner answer must be a JSON object")
    return answer, {"thread_id": thread, "usage": usage}


class CodexOwnerAdapter:
    name = "codex-synthetic-owner"

    def __init__(self, trial: str):
        case(trial)
        self.trial = trial

    def reply(self, root: Path, prompt: str) -> OwnerReply:
        sources = validate_input(root, self.trial, prompt)
        # Reserve before launch. Failure and interruption consume the planned
        # attempt; recovery must not automatically send it again.
        marker = ACCEPTANCE_ROOT / f"{self.trial}.attempt.json"
        with marker.open("x") as stream:
            json.dump({"trial": self.trial, "status": "started"}, stream)
        delivered = (prompt + "\n\nSupplied maintained source contents (evidence, not new authority):\n"
                     + json.dumps(sources, ensure_ascii=False, indent=2)
                     + '\n\nReturn only one JSON object with keys "choices", "rationale", '
                       '"observation", "grounds". Rationale and observation are prose strings; '
                       'each grounds entry contains only a whole-file "path". Tools are disabled; use the supplied source paths '
                       "and state any unresolved gap.")
        trace = {"adapter": self.name, "model_requested": MODEL, "reasoning_effort": EFFORT,
                 "timeout_seconds": TIMEOUT, "request": retain_source(root, delivered),
                 "scope": "Fixed synthetic text only; isolated directory; integrations and execution disabled."}
        started = time.monotonic()
        stdout = stderr = ""
        status = "failed"
        try:
            version = subprocess.run([BINARY, "--version"], capture_output=True, text=True,
                                     check=True, timeout=10)
            trace["runtime"] = version.stdout.strip()
            with tempfile.TemporaryDirectory(prefix="workflow-owner-") as directory:
                schema = json.dumps(answer_schema(self.trial), indent=2)
                (Path(directory) / "answer-schema.json").write_text(schema)
                trace["answer_schema"] = retain_source(root, schema)
                args = command(Path(directory))
                trace["command"] = args
                process = subprocess.Popen(args, cwd=directory, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE, text=True, start_new_session=True)
                try:
                    remaining = max(0.001, TIMEOUT - (time.monotonic() - started))
                    stdout, stderr = process.communicate(delivered, timeout=remaining)
                except BaseException:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    stdout, stderr = process.communicate()
                    raise
                trace["returncode"] = process.returncode
                if process.returncode:
                    raise ValueError(f"Codex exited with status {process.returncode}")
            answer, runtime = parse_response(stdout)
            trace.update(runtime)
            # Check the actual supplied files before handing the answer back.
            validate_input(root, self.trial, prompt)
            status = "responded"
        except BaseException as exc:
            trace["error"] = f"{type(exc).__name__}: {exc}"
            raise
        finally:
            trace.update(elapsed_seconds=time.monotonic() - started,
                         stdout=retain_source(root, stdout), stderr=retain_source(root, stderr))
            marker.write_text(json.dumps({"trial": self.trial, "status": status, "trace": trace}, indent=2))
        return OwnerReply(answer, digest(delivered + "\n" + stdout), trace)


def run_trial(trial: str) -> dict:
    from frontier_batch import Batch, DefineBatch, Action, OperationBinding, OperationResult

    files, definition, spec = case(trial)
    root = ACCEPTANCE_ROOT / trial
    root.mkdir(parents=True, exist_ok=False)
    for name, body in files.items():
        (root / name).write_text(body)
    subprocess.run(["git", "init", "-q", str(root)], check=True, capture_output=True)
    batch = Batch.open(root, "B001")
    batch.apply(DefineBatch(objective=definition["objective"], acceptance=definition["acceptance"],
                            scope=tuple(definition["scope"])))
    response = batch.answer_realization(batch.prepare_realization(spec), CodexOwnerAdapter(trial))
    batch.adopt_realization(response["invocation_id"])
    choices = response["choice"]["choices"]
    data = json.loads(files["inputs.json"])

    def consume(action, context, effective):
        if trial.startswith("allocation"):
            selected = effective["selected"]
            if not isinstance(selected, list) or len(set(selected)) != len(selected):
                raise ValueError("selection must contain distinct jobs")
            cost = sum(data["jobs"][key]["cost"] for key in selected)
            if cost > data["capacity"]:
                raise ValueError("selected jobs exceed shared capacity")
            observation = {"cost": cost, "return": sum(data["jobs"][key]["value"] for key in selected),
                           "incumbent_return": 16}
        else:
            residuals = [value - effective["offset"] - ref
                         for value, ref in zip(data["readings"], data["references"])]
            observation = {"residuals": residuals}
        return OperationResult("completed", result=observation)

    def no_legacy(action, context):
        raise AssertionError("an enrolled choice must use the checked effective input")

    binding = OperationBinding(no_legacy, prepare=lambda a, c: choices, consume=consume)
    runner = Batch.open(root, "B001", operations={"observe": binding})
    outcome = runner.perform(Action("first-observation", "observe", "preparation"))
    result = {"trial": trial, "response": response,
              "outcome": {"attempt": outcome.attempt, "result": outcome.operation_result.result}}
    (root / "result.json").write_text(json.dumps(result, indent=2))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trial", choices=TRIALS, required=True)
    args = parser.parse_args()
    print(json.dumps(run_trial(args.trial), indent=2))


if __name__ == "__main__":
    main()
