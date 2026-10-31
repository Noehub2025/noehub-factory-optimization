"""One bounded integration observation for the ordinary owner entry.

This runner is acceptance evidence, not a restriction on the general adapter.
It sends generated task facts and the maintained integration guide only.
"""
import json
from pathlib import Path
import subprocess
import sys

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "tools/workflow-harness/adapters"))
from codex_owner import CodexBackend, prepare_request, answer_request, recover_response
from frontier_batch import Batch, DefineBatch, Action, OperationBinding, OperationResult


def main():
    root = REPO / "artifacts/workflow-harness/project-owner-integration-20261016"
    root.mkdir(parents=True, exist_ok=False)
    subprocess.run(["git", "init", "-q", str(root)], check=True, capture_output=True)
    (root / "AGENTS.md").write_text("Use the maintained [entry guide](knowledge.md) for supported operations.\n")
    (root / "knowledge.md").write_text("# Local capabilities\n\n[Owner integration](guide.md) describes the current entry, its operations and recovery.\n")
    (root / "guide.md").write_text((REPO / "tools/workflow-harness/adapters/README.md").read_text())
    (root / "owner.md").write_text("Choose the concrete continuation and its first observation.\n")
    facts = {"interruption": "Transport completed and saved its return; the host stopped before adopting it.",
             "interface": "Select the operation field in the continuation configuration using a supported entry operation.",
             "observation": "The receiver will exercise that operation on a retained completed response."}
    (root / "facts.json").write_text(json.dumps(facts, indent=2))
    (root / "configuration.json").write_text(json.dumps({"operation": "repeat"}))
    batch = Batch.open(root, "B917")
    batch.apply(DefineBatch(objective="Resume the interrupted owner work while preserving its completed result.",
                            acceptance="Use a supported continuation and observe the resulting response identity.",
                            scope=("local Workflow integration observation",)))
    spec = {"owner": "owner.md", "intended_decision": "Choose the continuation configuration and first observation.",
            "consumer": "local-owner-entry", "operations": ["continue-owner"],
            "sources": [{"path": "facts.json"}], "conditions": {"retained_completed_response": True}}
    packet = prepare_request(root, "B917", spec=spec)
    (root / "request.json").write_text(json.dumps(packet, indent=2))

    class ObservedBackend(CodexBackend):
        calls = 0

        def call(self, *args, **kwargs):
            self.calls += 1
            return super().call(*args, **kwargs)

    backend = ObservedBackend(binary="codex",
                              model="gpt-6-astra", effort="xhigh")
    response = answer_request(root, packet, backend, max_calls=3, timeout_seconds=180)
    batch.adopt_realization(response["invocation_id"])
    calls_before_consumption = backend.calls

    def consume(action, context, effective):
        if effective["operation"] == "recover":
            recovered = recover_response(root, "B917")
        elif effective["operation"] == "answer":
            recovered = answer_request(root, packet, backend, max_calls=3, timeout_seconds=180)
        else:
            raise ValueError("the selected operation does not retrieve the retained response")
        return OperationResult("completed", result={"response_id": recovered["response_id"],
            "unchanged_response": recovered["response_id"] == response["response_id"],
            "additional_model_calls": backend.calls - calls_before_consumption})

    binding = OperationBinding.configured(lambda a, c: json.loads((root / "configuration.json").read_text()), consume)
    outcome = Batch.open(root, "B917", operations={"continue-owner": binding}).perform(
        Action("resume-local-owner", "continue-owner", "preparation"))
    result = {"model_calls": backend.calls, "response": response, "result": outcome.operation_result.result}
    (root / "result.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
