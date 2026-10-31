"""Optional Codex owner adapter for ordinary project work.

Preparation is local. Answering sends the prepared task, resource descriptions
and explicitly scoped material to the signed-in Codex service. The model can
request allowed sources by identifier, but cannot run commands, browse files,
install Skills or change a campaign. Batch remains the owner of the decision.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import math
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
from context_delivery import retain_source, read_retained
from frontier_batch import Batch, _realization_definition
from professional_input import (OwnerReply, OwnerTransportError, identity, request_text,
                                selected_source, verify, validate_choice, check_grounds)


def source_id(ref: dict) -> str:
    return "source-" + identity(ref)[:16]


def catalog(root: Path, prepared: dict, materials=None) -> list[dict]:
    """Collect descriptions without opening every method body.

    The default scope is maintained entries, their direct local links and
    repository-installed Skills. Explicit material selectors replace that scope.
    Neither mode scans history or follows arbitrary filesystem links.
    """
    descriptions = {}
    for entry in prepared["resources"]["entries"]:
        descriptions[entry["path"]] = entry["description_excerpt"]
        for link in entry["links"]:
            locator = link["locator"].split("#")[0]
            if not locator or "://" in locator:
                continue
            path = (root / entry["path"]).parent / locator
            if path.resolve().is_relative_to(root):
                descriptions[str(path.resolve().relative_to(root))] = link["description"]
    for skill in prepared["resources"]["installed_skills"]:
        path = Path(skill["path"]).resolve()
        if path.is_relative_to(root):
            descriptions[str(path.relative_to(root))] = skill["description"]
    refs = materials if materials is not None else [{"path": p} for p in descriptions]
    entries = {}
    for ref in [s["source"] for s in prepared["problem"]["sources"]] + list(refs):
        if (not isinstance(ref, dict) or not isinstance(ref.get("path"), str)
                or set(ref) - {"path", "field", "section"}):
            raise ValueError("materials require exact path and optional field or section selectors")
        path = (root / ref["path"]).resolve()
        accessible = path.is_relative_to(root) and path.is_file()
        if not accessible and materials is not None:
            raise ValueError(f"material is unavailable inside the project: {ref['path']}")
        entries[source_id(ref)] = {"id": source_id(ref), "source": ref,
                                   "description": descriptions.get(ref["path"], "Host-selected source"),
                                   "available": accessible}
    return list(entries.values())


def prepare_request(root: Path, batch_name: str, *, spec=None, materials=None) -> dict:
    """Prepare an inspectable input scope without making a model call."""
    root = root.resolve()
    prepared = Batch.open(root, batch_name).prepare_realization(spec)
    packet = {"version": "owner-request/1", "batch": batch_name, "prepared": prepared,
              "catalog": catalog(root, prepared, materials)}
    packet["identity"] = identity(packet)
    return packet


def verify_packet(root: Path, packet: dict) -> None:
    if packet.get("version") != "owner-request/1" or packet.get("identity") != identity(
            {k: v for k, v in packet.items() if k != "identity"}):
        raise ValueError("owner request changed; prepare its current input scope")
    batch = Batch.open(root, packet["batch"])
    state = batch.view._record
    current = state["current"].get("realization", {})
    verify(root, packet["batch"], _realization_definition(state), current["spec"], packet["prepared"])
    seen = set()
    for item in packet["catalog"]:
        if item["id"] != source_id(item["source"]) or item["id"] in seen:
            raise ValueError("invalid or duplicate source identifier")
        seen.add(item["id"])


def response_schema() -> dict:
    """Represent arbitrary JSON choices without imposing domain-specific fields."""
    return {"type": "object", "additionalProperties": False,
            "properties": {"kind": {"type": "string", "enum": ["read", "answer"]},
                "source_ids": {"type": "array", "items": {"type": "string"}},
                "choices": {"type": "array", "items": {"type": "object", "additionalProperties": False,
                    "properties": {"selector": {"type": "string"}, "value_json": {"type": "string"}},
                    "required": ["selector", "value_json"]}},
                "rationale": {"type": "string"}, "observation": {"type": "string"}},
            "required": ["kind", "source_ids", "choices", "rationale", "observation"]}


DISABLED_FEATURES = (
    "shell_tool", "unified_exec", "code_mode", "code_mode_host", "apps", "plugins", "browser_use",
    "computer_use", "in_app_browser", "memories", "hooks", "multi_agent", "multi_agent_v2",
    "shell_snapshot", "view_image", "skill_search", "skill_mcp_dependency_install",
    "image_generation", "workspace_dependencies", "goals",
)


def parse_response(stdout: str) -> tuple[dict, dict]:
    completed, messages, usage, thread, started = False, [], {}, None, False
    for line in stdout.splitlines():
        if not line.strip():
            continue
        event = json.loads(line)
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
            if (not started and item.get("type") == "error" and item.get("message", "").startswith((
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
        raise ValueError("Codex answer must be a JSON object")
    return answer, {"thread_id": thread, "usage": usage}


class CodexBackend:
    """Model transport only; no source selection or decision authority."""
    def __init__(self, *, binary: str, model: str, effort: str):
        if not all(isinstance(v, str) and v.strip() for v in (binary, model, effort)):
            raise ValueError("select the installed binary, model and reasoning effort")
        self.binary, self.model, self.effort = binary, model, effort

    def command(self, directory: Path) -> list[str]:
        args = [self.binary, "--no-daemon", "exec", "--ephemeral", "--ignore-user-config", "--strict-config",
                "--skip-git-repo-check", "--json", "-s", "read-only", "-C", str(directory),
                "-m", self.model, "--output-schema", str(directory / "answer-schema.json")]
        settings = {"model_reasoning_effort": self.effort, "approval_policy": "never",
                    "web_search": "disabled", "agents.enabled": False, "project_doc_max_bytes": 0,
                    "features.skip_host_skill_discovery": True, "memories.use_memories": False,
                    "memories.generate_memories": False}
        for key, value in settings.items():
            args += ["-c", key + "=" + json.dumps(value)]
        for feature in DISABLED_FEATURES:
            args += ["--disable", feature]
        return args + ["-"]

    def call(self, root: Path, prompt: str, timeout: float) -> tuple[dict, dict]:
        trace = {"request": retain_source(root, prompt), "model_requested": self.model,
                 "reasoning_effort": self.effort, "timeout_seconds": timeout}
        started = time.monotonic()
        stdout = stderr = ""
        try:
            version = subprocess.run([self.binary, "--version"], capture_output=True, text=True,
                                     check=True, timeout=min(10, timeout))
            trace["runtime"] = version.stdout.strip()
            with tempfile.TemporaryDirectory(prefix="workflow-owner-") as directory:
                schema = json.dumps(response_schema())
                (Path(directory) / "answer-schema.json").write_text(schema)
                trace["schema"] = retain_source(root, schema)
                args = self.command(Path(directory))
                trace["command"] = args
                process = subprocess.Popen(args, cwd=directory, stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
                try:
                    stdout, stderr = process.communicate(prompt, timeout=max(.001, timeout - (time.monotonic() - started)))
                except BaseException:
                    try:
                        if os.name == "posix":
                            os.killpg(process.pid, signal.SIGKILL)
                        else:
                            process.kill()
                    except ProcessLookupError:
                        pass
                    stdout, stderr = process.communicate()
                    raise
                trace["returncode"] = process.returncode
                if process.returncode:
                    raise ValueError(f"Codex exited with status {process.returncode}")
            answer, details = parse_response(stdout)
            trace.update(details)
        except BaseException as exc:
            trace.update(elapsed_seconds=time.monotonic() - started,
                         stdout=retain_source(root, stdout), stderr=retain_source(root, stderr))
            if not isinstance(exc, Exception):
                exc.trace = trace
                raise
            raise OwnerTransportError(str(exc), trace) from exc
        trace.update(elapsed_seconds=time.monotonic() - started,
                     stdout=retain_source(root, stdout), stderr=retain_source(root, stderr))
        return answer, trace


def save_journal(path: Path, value: dict) -> None:
    with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        try:
            json.dump(value, stream, ensure_ascii=False, allow_nan=False, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)


def decode_answer(value: dict, supplied: dict) -> dict:
    if value.get("kind") != "answer":
        raise ValueError("owner did not return a decision")
    choices = {}
    for row in value["choices"]:
        selector = row["selector"]
        if not isinstance(selector, str) or not all(selector.split(".")) or selector in choices:
            raise ValueError("choice selectors must be distinct nonempty paths")
        choices[selector] = json.loads(row["value_json"])
    ids = value["source_ids"]
    if not isinstance(ids, list) or any(i not in supplied for i in ids):
        raise ValueError("answer cites material not supplied in this invocation")
    return {"choices": choices, "rationale": value["rationale"], "observation": value["observation"],
            "grounds": [supplied[i]["source"] for i in dict.fromkeys(ids)]}


class CodexOwnerAdapter:
    name = "codex-owner"

    def __init__(self, packet: dict, backend: CodexBackend, *, max_calls: int, timeout_seconds: float):
        if type(max_calls) is not int or max_calls < 1 or not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
            raise ValueError("set a positive call allowance and total transport timeout")
        self.packet, self.backend = packet, backend
        self.max_calls, self.timeout = max_calls, timeout_seconds

    def reply(self, root: Path, prompt: str) -> OwnerReply:
        root = root.resolve()
        verify_packet(root, self.packet)
        if prompt != request_text(self.packet["prepared"]):
            raise ValueError("Batch request differs from the prepared owner request")
        state = Batch.open(root, self.packet["batch"]).view._record
        invocation = state["current"]["realization"]["invocation"]
        invocation_id = invocation["id"]
        if invocation["status"] != "awaiting_response" or invocation["adapter"] != self.name:
            raise ValueError("the owner invocation is not current")
        directory = root / "artifacts/workflow-harness/owner-calls" / invocation_id
        directory.mkdir(parents=True, exist_ok=False)
        journal_path = directory / "call.json"
        journal = {"invocation_id": invocation_id, "packet_identity": self.packet["identity"],
                   "packet": retain_source(root, json.dumps(self.packet)), "status": "pending", "rounds": []}
        save_journal(journal_path, journal)
        available = {row["id"]: row for row in self.packet["catalog"] if row["available"]}
        supplied = {source_id(s["source"]): s for s in self.packet["prepared"]["problem"]["sources"]}
        started = time.monotonic()
        try:
            for _ in range(self.max_calls):
                verify_packet(root, self.packet)
                for source in supplied.values():
                    if selected_source(root, source["source"])["sha256"] != source["sha256"]:
                        raise ValueError("supplied professional material changed before the next call")
                active = Batch.open(root, self.packet["batch"]).view._record["current"]["realization"]["invocation"]
                if active["id"] != invocation_id or active["status"] != "awaiting_response":
                    raise ValueError("owner invocation was retired or replaced")
                remaining = self.timeout - (time.monotonic() - started)
                if remaining <= 0:
                    raise ValueError("owner transport time allowance exhausted")
                delivered = (prompt + "\n\nAllowed source descriptions:\n" + json.dumps(self.packet["catalog"])
                    + "\n\nActual source content supplied so far:\n" + json.dumps(supplied)
                    + '\n\nReturn kind="read" with source_ids for needed material from this catalog, '
                      'empty choices and a brief rationale; or kind="answer" with the actual choices and '
                      'first observation. Encode each choice as selector plus value_json (a valid JSON value). '
                      'For an answer, source_ids names only supplied sources actually used. No source count is '
                      'required. Tools are disabled; a missing method outside this scope remains an open '
                      'professional question, not evidence of adequacy. Do not turn technical defaults into '
                      'user constraints. Reuse sufficient grounds and retain valid simple work.')
                row = {"status": "started", "request": retain_source(root, delivered)}
                journal["rounds"].append(row)
                save_journal(journal_path, journal)
                raw, trace = self.backend.call(root, delivered, remaining)
                row.update(status="completed", trace=trace, response=retain_source(root, json.dumps(raw)))
                save_journal(journal_path, journal)
                if raw.get("kind") == "read":
                    ids = raw.get("source_ids")
                    if (not isinstance(ids, list) or not ids or raw.get("choices")
                            or any(i not in available for i in ids) or all(i in supplied for i in ids)):
                        raise ValueError("owner requested unavailable or already supplied material")
                    for sid in ids:
                        if sid not in supplied:
                            supplied[sid] = selected_source(root, available[sid]["source"])
                    continue
                answer = decode_answer(raw, supplied)
                validate_choice(root, answer, tuple(supplied.values()))
                verify_packet(root, self.packet)
                reply_trace = {"journal": str(journal_path.relative_to(root)),
                               "packet_identity": self.packet["identity"], "rounds": journal["rounds"]}
                reply = OwnerReply(answer, identity({"invocation": invocation_id, "rounds": journal["rounds"]}),
                                   reply_trace, tuple(supplied.values()))
                journal.update(status="responded", reply=retain_source(root, json.dumps(asdict(reply))))
                save_journal(journal_path, journal)
                return reply
            raise ValueError("owner requested further work beyond this call allowance; retain the open question")
        except BaseException as exc:
            journal.update(status="failed", error=f"{type(exc).__name__}: {exc}")
            if getattr(exc, "trace", None):
                journal["transport_failure"] = exc.trace
            save_journal(journal_path, journal)
            if not isinstance(exc, Exception):
                raise
            raise OwnerTransportError(str(exc), {"journal": str(journal_path.relative_to(root))}) from exc


def recover_response(root: Path, batch_name: str) -> dict:
    """Recover only a completed host return; never repeat an uncertain model call."""
    batch = Batch.open(root, batch_name)
    current = batch.view._record["current"].get("realization", {})
    invocation = current.get("invocation")
    if not invocation:
        raise ValueError("no owner invocation to recover")
    if invocation["status"] in {"responded", "adopted"}:
        verify(root, batch_name, _realization_definition(batch.view._record), current["spec"], invocation["input"])
        check_grounds(root, invocation["choice"])
        return {"invocation_id": invocation["id"], "response_id": invocation["response_id"],
                "choice": invocation["choice"], "coverage": "retained_owner_response"}
    if invocation["status"] != "awaiting_response" or invocation["adapter"] != CodexOwnerAdapter.name:
        raise ValueError("no pending Codex return; reconcile or explicitly retire the failed invocation")
    path = root / "artifacts/workflow-harness/owner-calls" / invocation["id"] / "call.json"
    journal = json.loads(path.read_text())
    if journal["status"] != "responded" or journal["invocation_id"] != invocation["id"]:
        raise ValueError("response is incomplete or uncertain; do not automatically replay the call")
    packet = json.loads(read_retained(root, journal["packet"]))
    verify_packet(root, packet)
    if (packet["prepared"] != invocation["input"] or packet["identity"] != journal["packet_identity"]
            or request_text(packet["prepared"]) != read_retained(root, invocation["request"])):
        raise ValueError("saved transport belongs to a different owner request")
    saved = json.loads(read_retained(root, journal["reply"]))
    return batch.receive_realization(invocation["id"], OwnerReply(**saved))


def answer_request(root: Path, packet: dict, backend: CodexBackend, *, max_calls: int,
                   timeout_seconds: float) -> dict:
    verify_packet(root, packet)
    batch = Batch.open(root, packet["batch"])
    prior = batch.view._record["current"]["realization"].get("invocation")
    if prior and prior["status"] != "retired":
        # Changed input cannot borrow an otherwise valid retained response.
        if prior["input"]["input_identity"] != packet["prepared"]["input_identity"]:
            raise ValueError("prior response covers different input; reconcile the affected choice")
        return recover_response(root, packet["batch"])
    return batch.answer_realization(packet["prepared"], CodexOwnerAdapter(packet, backend,
                                    max_calls=max_calls, timeout_seconds=timeout_seconds))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["prepare", "answer", "recover", "adopt", "retire"])
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--batch", required=True)
    parser.add_argument("--spec", type=Path)
    parser.add_argument("--materials", type=Path, help="Exact source selector list; replaces the maintained default scope")
    parser.add_argument("--request", type=Path, help="Prepared request file; prepare writes it, answer reads it")
    parser.add_argument("--binary", default="codex")
    parser.add_argument("--model")
    parser.add_argument("--effort")
    parser.add_argument("--max-calls", type=int)
    parser.add_argument("--timeout-seconds", type=float)
    parser.add_argument("--invocation")
    parser.add_argument("--reason")
    args = parser.parse_args()
    root = args.root.resolve()
    if args.command == "prepare":
        value = prepare_request(root, args.batch,
            spec=json.loads(args.spec.read_text()) if args.spec else None,
            materials=json.loads(args.materials.read_text()) if args.materials else None)
        if args.request:
            args.request.write_text(json.dumps(value, ensure_ascii=False, indent=2))
            value = {"request": str(args.request), "identity": value["identity"],
                     "allowed_sources": value["catalog"], "coverage": "prepared_only"}
    elif args.command == "answer":
        if not args.request or args.max_calls is None or args.timeout_seconds is None:
            parser.error("answer requires --request, --model, --effort, --max-calls and --timeout-seconds")
        packet = json.loads(args.request.read_text())
        if packet["batch"] != args.batch:
            parser.error("request belongs to another Batch")
        value = answer_request(root, packet, CodexBackend(binary=args.binary, model=args.model, effort=args.effort),
                               max_calls=args.max_calls, timeout_seconds=args.timeout_seconds)
    elif args.command == "recover":
        value = recover_response(root, args.batch)
    elif args.command == "adopt":
        batch = Batch.open(root, args.batch)
        batch.adopt_realization(args.invocation)
        value = {"choices": batch.realization_choices(), "coverage": "adopted_owner_response"}
    else:
        Batch.open(root, args.batch).retire_realization_response(args.invocation, args.reason)
        value = {"retired": args.invocation, "backend_stopped": "not asserted"}
    print(json.dumps(value, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
