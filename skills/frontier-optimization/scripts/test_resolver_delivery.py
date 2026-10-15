"""Resolver preparation, real CLI consumption and scoped freshness regressions."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

import frontier_references as refs
from context_delivery import consume_request, digest, model_view, read_retained, verify_prepared
from test_frontier_references import git, save


CLI = Path(refs.__file__).resolve()


def command(root, kind, *args):
    return subprocess.run([sys.executable, str(CLI), kind, "--repo", str(root), *args],
                          capture_output=True, text=True, timeout=30)


@pytest.fixture
def resolver_repo(tmp_path):
    git(tmp_path, "init")
    git(tmp_path, "config", "user.email", "delivery@example.invalid")
    git(tmp_path, "config", "user.name", "Delivery Test")
    save(tmp_path, {
        "owner.md": "---\nobjective_basis:\n  objective_source: goal.md\n  evaluation_source: evaluation.md\n  current_work_source: old.md\nfeedback_not_due: Original pending observation.\n---\n[old](old.md) [selected](selected.md)\n",
        "goal.md": "Improve accepted output under the governing conditions. " * 12,
        "evaluation.md": json.dumps({"meaning": "Accepted output per actual input.", "condition": "Required condition. " * 25}, indent=4),
        "old.md": "An inherited local assignment.",
        "selected.md": "The explicitly selected current research question.",
        "assignment.md": "Compare the available information for the governing outcome.",
        "evidence.json": json.dumps({"observed": "Retained historical observation.", "alternatives": ["Old offer"]}),
        refs.DECISION_POLICY_PATH: "# Role guidance\nUse original grounds and preserve transfer conditions.\n" * 6,
    })
    return tmp_path


def prepare_cli(root, *extra):
    result = command(root, "resolver", "--path", "evidence.json", "--owner-source", "owner.md",
                     "--output", str(root / "prepared.json"), *extra)
    assert result.returncode == 0, result.stdout + result.stderr
    return Path(json.loads(result.stdout)["delivery"])


def test_cli_delivers_policy_selected_work_assignment_timing_and_exact_json(resolver_repo):
    root = resolver_repo
    path = prepare_cli(root, "--assignment", "assignment.md", "--current-work-source", "selected.md",
                       "--feedback-trigger", "A decision is now due.")
    verified = command(root, "verify-delivery", "--path", str(path))
    assert verified.returncode == 0, verified.stdout
    delivered = command(root, "deliver", "--path", str(path))
    assert delivered.returncode == 0, delivered.stdout
    # A different process consumes the actual command output, not prepared JSON.
    received = subprocess.run([sys.executable, "-c", "import sys; from pathlib import Path; Path(sys.argv[1]).write_text(sys.stdin.read())", str(root / "received.txt")],
                              input=delivered.stdout, text=True, capture_output=True, timeout=10)
    assert received.returncode == 0, received.stderr
    text = (root / "received.txt").read_text()
    for name in ("goal.md", "evaluation.md", "selected.md", "assignment.md"):
        assert (root / name).read_text() in text
    policy = (root / refs.DECISION_POLICY_PATH).read_text()
    assert text.count(policy) == 1
    assert text.index(policy) < text.index("Retained historical observation")
    assert "A decision is now due." in text and "feedback_decision" in text
    context = json.loads(path.read_text())["adoption_context"]
    assert context["selected_sources"]["current_work_source"]["source"]["path"] == "selected.md"
    assert {item["source"]["path"] for item in context["incoming_assignments"]} == {"evidence.json", "assignment.md"}


@pytest.mark.parametrize("name", ["goal.md", "evaluation.md", "assignment.md"])
def test_changed_current_source_refused_then_refreshed_delivery(resolver_repo, name):
    root = resolver_repo
    path = prepare_cli(root, "--assignment", "assignment.md")
    assert command(root, "verify-delivery", "--path", str(path)).returncode == 0
    (root / name).write_text("Changed governing or assigned content.")
    for kind in ("verify-delivery", "deliver"):
        result = command(root, kind, "--path", str(path))
        assert result.returncode == 2
        assert "Workspace:" not in result.stdout
        assert json.loads(result.stdout)["status"] == "NOT_READY"
    save(root, {name: (root / name).read_text()})
    path = prepare_cli(root, "--assignment", "assignment.md")
    result = command(root, "deliver", "--path", str(path))
    assert result.returncode == 0, result.stdout
    assert "Changed governing or assigned content." in result.stdout


def test_historical_evidence_and_prepared_policy_survive_working_file_changes(resolver_repo):
    root = resolver_repo
    path = prepare_cli(root)
    policy = (root / refs.DECISION_POLICY_PATH).read_text()
    (root / "evidence.json").write_text(json.dumps({"observed": "New later observation"}))
    (root / refs.DECISION_POLICY_PATH).write_text("New role guidance for future preparation.")
    result = command(root, "deliver", "--path", str(path))
    assert result.returncode == 0, result.stdout
    assert policy in result.stdout
    assert "Retained historical observation" in result.stdout
    assert "New later observation" not in result.stdout


@pytest.mark.parametrize("spelling", ["plain", "relative", "absolute"])
def test_current_assignment_and_task_are_not_replaced_by_evidence_revision(resolver_repo, spelling):
    root = resolver_repo
    save(root, {"task.md": "The earlier task implementation."})
    (root / "assignment.md").write_text("The current uncommitted assignment.")
    (root / "task.md").write_text("The current uncommitted task implementation.")
    assignment = {"plain": "assignment.md", "relative": "./assignment.md",
                  "absolute": str(root / "assignment.md")}[spelling]
    path = prepare_cli(root, "--assignment", assignment, "--source", "task.md")
    result = command(root, "deliver", "--path", str(path))
    assert result.returncode == 0, result.stdout
    assert "The current uncommitted assignment." in result.stdout
    assert "The current uncommitted task implementation." in result.stdout
    assert "The earlier task implementation." not in result.stdout
    assert "Retained historical observation." in result.stdout
    context = json.loads(path.read_text())["adoption_context"]
    assert "assignment.md" in context["actual_use"]
    (root / "task.md").write_text("A later task change.")
    assert command(root, "deliver", "--path", str(path)).returncode == 2


@pytest.mark.parametrize("change", ["text", "identity", "missing", "scope", "assignment"])
def test_resealed_malformed_contract_is_not_deliverable(resolver_repo, change):
    root = resolver_repo
    path = prepare_cli(root, "--assignment", "assignment.md")
    view = json.loads(path.read_text())
    if change == "text":
        view["decision_policy"]["text"] = "Changed policy"
    elif change == "identity":
        view["decision_policy"]["sha256"] = "0" * 64
    elif change == "missing":
        del view["decision_policy"]["text"]
    elif change == "scope":
        view["adoption_context"]["selected_sources"]["current_work_source"]["source"]["path"] = "selected.md"
    else:
        view["adoption_context"]["incoming_assignments"].pop()
    view["delivery_identity"] = digest(json.dumps({k: v for k, v in view.items() if k != "delivery_identity"}, ensure_ascii=False, sort_keys=True))
    with pytest.raises(ValueError, match="resolver"):
        consume_request(root, view)


@pytest.mark.parametrize("status", ["absent", "empty"])
def test_optional_policy_does_not_block_valid_current_work(resolver_repo, status):
    root = resolver_repo
    policy = root / refs.DECISION_POLICY_PATH
    policy.unlink() if status == "absent" else policy.write_text("")
    view = model_view(root, refs.prepare_resolver(root, "HEAD", "evidence.json", owner_source="owner.md"))
    request = consume_request(root, view)
    assert "Optional role guidance:" in request
    assert "Current resolver responsibility" in request
    assert "Original pending observation." in request


def test_raw_export_cannot_gain_delivery_status_at_consumption(resolver_repo):
    root = resolver_repo
    prepared = refs.prepare_resolver(root, "HEAD", "evidence.json", owner_source="owner.md")
    with pytest.raises(ValueError, match="delivery envelope"):
        verify_prepared(root, prepared)


def test_exact_source_repeated_as_policy_is_rendered_once(resolver_repo):
    root = resolver_repo
    policy = (root / refs.DECISION_POLICY_PATH).read_text()
    save(root, {"goal.md": policy})
    request = consume_request(root, model_view(root, refs.prepare_resolver(root, "HEAD", "evidence.json", owner_source="owner.md")))
    assert request.count(policy) == 1
    assert "use the exact text already delivered" in request


def test_retained_judgment_is_delivered_without_a_duplicate_resolution(resolver_repo):
    root = resolver_repo
    prepared = refs.prepare_resolver(root, "HEAD", "evidence.json", owner_source="owner.md",
                                     assignment="assignment.md")
    bound = refs.bind_resolution(root, prepared, {"reason": "Continue the supported current work."})
    save(root, {"prior.json": json.dumps(bound)})
    reused = refs.prepare_resolver(root, "HEAD", "evidence.json", ["prior.json"],
                                  owner_source="owner.md", assignment="assignment.md")
    assert reused["reuse_resolution"]["path"] == "prior.json"
    view = model_view(root, reused)
    request = consume_request(root, view)
    assert "Use the retained judgment only within its applicable scope" in request
    assert "do not publish a duplicate resolution" in request
    assert "Continue the supported current work." in request
    (root / "assignment.md").write_text("A changed current assignment.")
    with pytest.raises(ValueError, match="changed"):
        consume_request(root, view)


@pytest.mark.parametrize("current", [True, False])
def test_incorporated_basis_uses_the_same_current_or_historical_body(resolver_repo, current):
    root = resolver_repo
    account = {"source": {"path": "understanding.md"}, "sha256": digest("Adopted understanding."),
               "incorporates": [{"path": "support.md", "sha256": digest("Original supporting fact.")}]}
    save(root, {"account-owner.json": json.dumps({"context_account": account}),
                "understanding.md": "Adopted understanding.", "support.md": "Original supporting fact."})
    revision = git(root, "rev-parse", "HEAD")
    (root / "support.md").write_text("Changed supporting fact.")
    context = refs.prepare_adoption_context(root, "account-owner.json", revision=revision,
                                            task_sources=["support.md"] if current else [])
    warnings = [item for item in context["limitations"] if "Incorporated basis changed" in item]
    assert bool(warnings) == current
    source = next(item for item in context["sources"] if item["source"]["path"] == "support.md")
    if current:
        assert source["contents"] == "Changed supporting fact."
    else:
        assert source["source"]["commit"] == revision
        assert read_retained(root, source["retrieval"]) == "Original supporting fact."
