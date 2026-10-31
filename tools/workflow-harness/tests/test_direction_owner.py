"""Normal exact-delivery entry, bounded transport and no-replay recovery."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

REPOSITORY = Path(__file__).resolve().parents[3]
sys.path.append(str(REPOSITORY / "skills/frontier-optimization/scripts"))
import frontier_references as refs
from context_delivery import consume_request

SPEC = importlib.util.spec_from_file_location("direction_owner", REPOSITORY / "tools/workflow-harness/adapters/direction_owner.py")
owner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(owner)


def material_case(root):
    (root / "evidence.md").write_text("Original observation: treatment changes latency only under load.")
    (root / "user.md").write_text("Question: Where may training run? Answer: Local. Later correction: external feedback was not prohibited.")
    (root / "scope.md").write_text("Claimed explicit restriction: no external feedback.")
    (root / "owner.json").write_text(json.dumps({"objective": "Improve the complete result", "decision_material": {
        "evidence": [{"path": "evidence.md"}],
        "user_scope": [{"original": [{"path": "user.md"}], "interpretation": {"path": "scope.md"}}]}}))
    return owner.prepare(root, "owner.json")


def test_real_subprocess_receives_exact_request_and_return(tmp_path):
    prepared = material_case(tmp_path)
    result = owner.send(tmp_path, prepared, [sys.executable, "-c", "import sys; sys.stdout.buffer.write(sys.stdin.buffer.read())"], invocation="exact")
    assert result["status"] == "completed"
    original = consume_request(tmp_path, prepared).encode()
    assert (tmp_path / result["request"]["path"]).read_bytes() == original
    assert (tmp_path / result["stdout"]["path"]).read_bytes() == original
    assert b"Answer: Local" in original
    assert b"Claimed explicit restriction" in original
    assert owner.recover(tmp_path, "exact")["stdout"] == result["stdout"]


def test_stale_or_changed_packet_never_starts_receiver(tmp_path):
    prepared = material_case(tmp_path)
    command = [sys.executable, "-c", "from pathlib import Path; Path('started').touch()"]
    (tmp_path / "user.md").write_text("Permission withdrawn.")
    with pytest.raises(ValueError, match="decision material changed"):
        owner.send(tmp_path, prepared, command, invocation="stale")
    assert not (tmp_path / "started").exists()
    assert not owner._location(tmp_path, "stale").exists()


def test_completed_or_ambiguous_identity_never_replays(tmp_path):
    prepared = material_case(tmp_path)
    command = [sys.executable, "-c", "from pathlib import Path; p=Path('count'); p.write_text(p.read_text()+'x' if p.exists() else 'x')"]
    result = owner.send(tmp_path, prepared, command, invocation="one")
    assert result["status"] == "completed"
    with pytest.raises(FileExistsError):
        owner.send(tmp_path, prepared, command, invocation="one")
    result["status"] = "started"
    owner.save(owner._location(tmp_path, "one") / "receipt.json", result)
    assert owner.recover(tmp_path, "one")["status"] == "uncertain"
    with pytest.raises(FileExistsError):
        owner.send(tmp_path, prepared, command, invocation="one")
    assert (tmp_path / "count").read_text() == "x"
    owner._location(tmp_path, "lost").mkdir()
    assert owner.recover(tmp_path, "lost")["status"] == "uncertain"


def test_timeout_and_large_output_keep_uncertain_effects_bounded(tmp_path):
    prepared = material_case(tmp_path)
    result = owner.send(tmp_path, prepared,
        [sys.executable, "-c", "import time; from pathlib import Path; Path('effect').touch(); print('started',flush=True); time.sleep(10)"],
        invocation="slow", timeout_seconds=.2)
    assert result["status"] == "uncertain"
    assert (tmp_path / "effect").exists()
    assert b"started" in (tmp_path / result["stdout"]["path"]).read_bytes()
    result = owner.send(tmp_path, prepared,
        [sys.executable, "-c", "import sys; sys.stdout.write('x'*100000)"], invocation="large", max_output_bytes=200)
    assert result["status"] == "uncertain" and result["output_truncated"]
    assert result["stdout"]["bytes"] + result["stderr"]["bytes"] == 200


def test_cli_normal_entry_assembles_and_dispatches_without_a_prepared_file(tmp_path):
    material_case(tmp_path)
    scripts = tmp_path / ".agents/skills/frontier-optimization/scripts"
    shutil.copytree(Path(refs.__file__).parent, scripts, ignore=shutil.ignore_patterns("__pycache__"))
    adapter = tmp_path / "tools/workflow-harness/adapters/direction_owner.py"
    adapter.parent.mkdir(parents=True)
    shutil.copyfile(Path(owner.__file__), adapter)
    result = subprocess.run([sys.executable, str(adapter), "run", "--root", str(tmp_path),
        "--owner", "owner.json", "--invocation", "normal", "--", sys.executable, "-c",
        "import sys; print(sys.stdin.read())"], capture_output=True, text=True, check=True)
    receipt = json.loads(result.stdout)
    actual = (tmp_path / receipt["stdout"]["path"]).read_text()
    assert "Original observation: treatment" in actual
    assert "Question: Where may training run? Answer: Local." in actual
    assert "Claimed explicit restriction" in actual


def test_normal_send_cli_refreshes_restored_original_before_start(tmp_path):
    material_case(tmp_path)
    scripts = tmp_path / ".agents/skills/frontier-optimization/scripts"
    shutil.copytree(Path(refs.__file__).parent, scripts, ignore=shutil.ignore_patterns("__pycache__"))
    adapter = tmp_path / "tools/workflow-harness/adapters/direction_owner.py"
    adapter.parent.mkdir(parents=True)
    shutil.copyfile(Path(owner.__file__), adapter)
    (tmp_path / "user.md").unlink()
    prepared_path = tmp_path / "prepared.json"
    preparation = subprocess.run([sys.executable, str(adapter), "prepare", "--root", str(tmp_path),
        "--owner", "owner.json", "--prepared", str(prepared_path)], capture_output=True, text=True, check=True)
    assert json.loads(preparation.stdout)["prepared"] == str(prepared_path)
    # Missing material by itself does not block covered ordinary use.
    command = [sys.executable, "-c", "import sys; from pathlib import Path; Path('received.txt').write_text(sys.stdin.read())"]
    unchanged = subprocess.run([sys.executable, str(adapter), "send", "--root", str(tmp_path),
        "--prepared", str(prepared_path), "--invocation", "unchanged-missing", "--", *command],
        capture_output=True, text=True, check=True)
    assert json.loads(unchanged.stdout)["status"] == "completed"
    first = (tmp_path / "received.txt").read_bytes()
    (tmp_path / "user.md").write_text("Actual correction: do not continue the selected operation.")
    restored = subprocess.run([sys.executable, str(adapter), "send", "--root", str(tmp_path),
        "--prepared", str(prepared_path), "--invocation", "restored", "--", *command], capture_output=True, text=True)
    assert restored.returncode == 2
    assert "prepared decision material changed" in restored.stdout
    assert (tmp_path / "received.txt").read_bytes() == first
    assert not owner._location(tmp_path, "restored").exists()
