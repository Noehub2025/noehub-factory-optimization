"""Read checked task context in current Codex and recover its original basis.

An explicitly configured subprocess remains supported. Current Codex reading
does not start another model or attest native tool payloads and model output.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "tools/workflow-harness/adapters"))
try:
    import direction_owner
except ModuleNotFoundError as exc:
    if exc.name != "yaml" or __name__ != "__main__":
        raise
    raise SystemExit("PyYAML is missing. Use a Python 3.10+ project environment with "
                     "the plugin's requirements-runtime.txt; do not install into the plugin cache.") from exc
from context_delivery import consume_request, digest
from frontier_context import root_session
from frontier_references import _document, _source_metadata


def project_path(root: Path, value: str) -> Path:
    path = (root / value).resolve()
    if not path.is_relative_to(root):
        raise ValueError("task paths must remain inside the repository")
    return path


def owner_path(root: Path, explicit: str | None) -> str:
    if explicit:
        return str(project_path(root, explicit).relative_to(root))
    session = root_session()
    if not session:
        raise ValueError("No current host association; supply the existing --owner.")
    pointer = root / ".frontier/hook-context" / f"{session}.json"
    active = _document(pointer.read_bytes())
    if active.get("kind") != "adopted_work" or active.get("workspace") != str(root):
        raise ValueError("The host association does not identify adopted work in this repository.")
    return str(project_path(root, active["selection"]["path"]).relative_to(root))


def settings(root: Path, owner: str) -> dict:
    owner_text = project_path(root, owner).read_text()
    metadata = _source_metadata(owner_text)
    state = metadata.get("current_state", {})
    if state.get("campaign_status") != "running":
        raise ValueError("This owner has no running work. Preserve its pause or completion; recovery is read-only.")
    entry = metadata.get("execution_entry", {})
    config_path = project_path(root, entry["configuration"])
    raw = config_path.read_text()
    config = _document(raw.encode())
    receiver = config.get("receiver", "subprocess")
    if receiver == "subprocess":
        command = config.get("command")
        if not isinstance(command, list) or not command or any(not isinstance(x, str) or not x for x in command):
            raise ValueError("Configure an explicit consumer argument list.")
    elif receiver != "current_codex" or "command" in config:
        raise ValueError("Select current_codex without a command, or an explicit subprocess.")
    return {**config, "configuration": str(config_path.relative_to(root)),
            "receiver": receiver,
            "configuration_sha256": digest(raw), "running_owner_sha256": digest(owner_text)}


def prepare_call(root: Path, owner: str, assignment: str, event: str) -> tuple[dict, dict]:
    config = settings(root, owner)
    assignment = str(project_path(root, assignment).relative_to(root))
    # Configuration is part of the checked use, so the actual consumer is not
    # detached from the material that was prepared for it.
    prepared = direction_owner.prepare(root, owner, assignment=assignment,
        sources=(config["configuration"],), event=event)
    captured_owner = next(x for x in prepared["sources"] if x["source"]["path"] == owner)
    if captured_owner["sha256"] != config["running_owner_sha256"]:
        raise ValueError("Owner changed after the running check; no call was sent.")
    captured = next(x for x in prepared["sources"] if x["source"]["path"] == config["configuration"])
    if captured["sha256"] != config["configuration_sha256"]:
        raise ValueError("Consumer configuration changed during preparation; no call was sent.")
    return config, prepared


def current(root: Path, owner: str, assignment: str, invocation: str, event: str) -> dict:
    """Emit local checked material to the current caller; no model is launched."""
    directory = project_path(root, str(direction_owner._location(root, invocation)))
    config, prepared = prepare_call(root, owner, assignment, event)
    if config["receiver"] != "current_codex":
        raise ValueError("The selected owner is not configured for current Codex.")
    request = consume_request(root, prepared)
    directory.mkdir(parents=True, exist_ok=False)
    path = directory / "request.txt"
    path.write_text(request, encoding="utf-8")
    direction_owner.save(directory / "prepared.json", prepared)
    direction_owner.save(directory / "receipt.json", {
        "invocation": invocation, "status": "material_ready", "receiver": "current_codex",
        "delivery_identity": prepared["delivery_identity"],
        "request": {"path": path.relative_to(root).as_posix(),
                    "sha256": digest(request), "bytes": len(request.encode("utf-8"))},
        "coverage": "Local material prepared for current tool output. No new model process, native dispatch interception or authenticated model-return capture."})
    # Recheck after persistence before emitting the exact text to the host.
    return receive(root, invocation)


def run(root: Path, owner: str, assignment: str, invocation: str, event: str) -> dict:
    project_path(root, str(direction_owner._location(root, invocation)))
    config, prepared = prepare_call(root, owner, assignment, event)
    if config["receiver"] != "subprocess":
        raise ValueError("This owner uses current Codex. Use current; no CLI model call is configured.")
    command = [str(root) if x == "{root}" else x for x in config["command"]]
    receipt = direction_owner.send(root, prepared, command, invocation=invocation,
        timeout_seconds=config.get("timeout_seconds", 600),
        max_output_bytes=config.get("max_output_bytes", 2_000_000))
    if receipt["status"] != "completed":
        return receipt
    return receive(root, invocation)


def final_message(raw: bytes) -> str:
    """Read the actual completed Codex event stream, not a caller-supplied answer."""
    messages = []
    completed = False
    for line in raw.decode("utf-8").splitlines():
        event = json.loads(line)
        if event.get("type") in ("turn.failed", "error"):
            raise ValueError("The consumer reported a failed turn; inspect its retained stream.")
        if event.get("type") == "turn.completed":
            completed = True
        if event.get("type") == "item.completed" and event.get("item", {}).get("type") == "agent_message":
            messages.append(event["item"]["text"])
    if not completed or not messages:
        raise ValueError("The retained stream has no completed consumer answer.")
    return messages[-1]


def receive(root: Path, invocation: str) -> dict:
    directory = project_path(root, str(direction_owner._location(root, invocation)))
    receipt = direction_owner.recover(root, invocation)
    local_material = receipt.get("receiver") == "current_codex" and receipt["status"] == "material_ready"
    if receipt["status"] != "completed" and not local_material:
        return {"receipt": receipt, "applicability": "unresolved", "replayed": False}
    prepared = _document((directory / "prepared.json").read_bytes())
    if prepared.get("delivery_identity") != receipt["delivery_identity"]:
        raise ValueError("Prepared input does not belong to the original invocation.")
    # consume_request reuses current-use, original-material and exact-source
    # checks. Recovery never prepares newer evidence for an older answer.
    request = consume_request(root, prepared)
    if digest(request) != receipt["request"]["sha256"]:
        raise ValueError("The retained request does not match the dispatched material.")
    if local_material:
        return {"invocation": invocation, "receipt": receipt, "applicability": "current",
                "replayed": False, "request": request,
                "meaning": "Original material is current. The current Codex owner judges and records its use; this is not a captured model answer."}
    answer = final_message(project_path(root, receipt["stdout"]["path"]).read_bytes())
    result = {"invocation": invocation, "receipt": receipt,
              "applicability": "current", "replayed": False,
              "answer": answer,
              "meaning": "Actual completed return with current input checks; the existing owner must judge and adopt its content."}
    direction_owner.save(directory / "received.json", result)
    return result


def recover(root: Path, invocation: str) -> dict:
    # Read the original effect/transport record first, even when the current
    # owner has changed or paused. Never call run as a recovery fallback.
    project_path(root, str(direction_owner._location(root, invocation)))
    receipt = direction_owner.recover(root, invocation)
    try:
        return receive(root, invocation)
    except (ValueError, OSError) as exc:
        return {"receipt": receipt, "applicability": "requires_owner_reconciliation",
                "reason": str(exc), "replayed": False,
                "meaning": "Historical transport remains recorded; do not adopt it as current or send again automatically."}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("current", "run", "receive", "recover"))
    parser.add_argument("--root", type=Path, required=True,
                        help="Consuming project root; never defaults to the installed package.")
    parser.add_argument("--owner")
    parser.add_argument("--assignment")
    parser.add_argument("--invocation", required=True)
    parser.add_argument("--event", choices=("direction", "scope", "design", "continuation"), default="direction")
    args = parser.parse_args()
    try:
        root = args.root.resolve()
        if args.operation in {"current", "run"}:
            if not args.assignment:
                raise ValueError("current/run requires the actual --assignment")
            operation = current if args.operation == "current" else run
            result = operation(root, owner_path(root, args.owner), args.assignment, args.invocation, args.event)
        else:
            if args.assignment or args.owner:
                raise ValueError("Receive/recover use the original invocation; do not substitute a new owner or assignment.")
            result = receive(root, args.invocation) if args.operation == "receive" else recover(root, args.invocation)
        if args.operation == "current":
            sys.stdout.write(result["request"])
        else:
            print(json.dumps({k: v for k, v in result.items() if k != "request"}, ensure_ascii=False, indent=2))
        return 0 if result.get("applicability") == "current" else 2
    except (ValueError, OSError, KeyError) as exc:
        print(json.dumps({"status": "not_adopted", "error": str(exc),
                          "recovery": "Inspect the original invocation record before any repeat."}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
