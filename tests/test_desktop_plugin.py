"""Test installed package boundaries and preservation of consuming project state."""
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import sys
import zipfile

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_distribution as builder
import noehub_setup as setup


@pytest.fixture
def project(tmp_path):
    root = tmp_path / "project with spaces"
    root.mkdir()
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    return root


def snapshot(root):
    return {p.relative_to(root).as_posix(): p.read_bytes()
            for p in root.rglob("*") if p.is_file() and ".git" not in p.parts}


def install(root):
    report, files, originals = setup.plan(root)
    setup.apply(root, files, originals)
    return report


def test_plan_is_read_only_and_apply_preserves_instructions(project):
    original = b"# Project rules\r\n\r\nNever publish without an explicit request.\r\n"
    (project / "AGENTS.md").write_bytes(original)
    before = snapshot(project)
    report, files, originals = setup.plan(project)
    assert snapshot(project) == before
    setup.apply(project, files, originals)
    assert (project / "AGENTS.md").read_bytes().startswith(original)
    first = snapshot(project)
    assert setup.plan(project)[0]["changes"] == []
    install(project)
    assert snapshot(project) == first
    assert set(first) == {"AGENTS.md", ".noehub/workflow.md", ".noehub/setup.json"}
    assert not report["hook_installed"] and not report["independent_review_verified"]
    assert str(ROOT).encode() not in (project / ".noehub/setup.json").read_bytes()


def test_override_and_nested_rules_are_preserved(project):
    (project / "AGENTS.md").write_text("Base rules.\n")
    (project / "AGENTS.override.md").write_text("Effective rules.\n")
    (project / "src").mkdir()
    (project / "src/AGENTS.md").write_text("Narrower rules.\n")
    (project / "CLAUDE.md").write_text("@AGENTS.md\nClaude-specific rules.\n")
    before = snapshot(project)
    report = install(project)
    assert report["instruction_file"] == "AGENTS.override.md"
    for path in ("AGENTS.md", "src/AGENTS.md", "CLAUDE.md"):
        assert (project / path).read_bytes() == before[path]


def test_existing_shared_guidance_is_not_duplicated(project):
    original = setup.shared_guidance(ROOT)
    (project / "AGENTS.md").write_text(original)
    assert install(project)["review_existing_guidance"] is True
    assert (project / "AGENTS.md").read_text().count(setup.SHARED_HEADINGS[0]) == 1
    assert setup.SHARED_HEADINGS[0] not in (project / ".noehub/workflow.md").read_text()


@pytest.mark.parametrize("relative", [".noehub/workflow.md", "AGENTS.md"])
def test_user_edits_are_not_overwritten(project, relative):
    install(project)
    path = project / relative
    path.write_text(path.read_text().replace("Noehub", "User-edited Noehub"))
    before = snapshot(project)
    with pytest.raises(ValueError, match="edited|merge"):
        install(project)
    assert snapshot(project) == before


def test_conflicting_file_and_symlink_are_not_replaced(project, tmp_path):
    (project / ".noehub").mkdir()
    (project / ".noehub/workflow.md").write_text("Existing user content")
    with pytest.raises(ValueError, match="Preserve"):
        setup.plan(project)
    assert not (project / "AGENTS.md").exists()
    (project / ".noehub/workflow.md").unlink()
    (project / ".noehub").rmdir()
    outside = tmp_path / "external"
    outside.mkdir()
    (project / ".noehub").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="escapes|symlink"):
        setup.plan(project)
    assert list(outside.iterdir()) == []


def test_concurrent_edit_prevents_all_setup_writes(project):
    _, files, originals = setup.plan(project)
    (project / "AGENTS.md").write_text("A newer user edit")
    with pytest.raises(ValueError, match="changed after planning"):
        setup.apply(project, files, originals)
    assert not (project / ".noehub").exists()


@pytest.mark.parametrize("record", ["{}", "[]", '"user data"'])
def test_unowned_setup_record_is_preserved(project, record):
    (project / ".noehub").mkdir()
    state = project / ".noehub/setup.json"
    state.write_text(record)
    with pytest.raises(ValueError, match="not this plugin"):
        setup.plan(project)
    assert state.read_text() == record and not (project / "AGENTS.md").exists()


def test_selecting_nested_or_plugin_directory_is_rejected(project):
    child = project / "nested"
    child.mkdir()
    with pytest.raises(ValueError, match="root explicitly"):
        setup.plan(child)
    with pytest.raises(ValueError, match="consuming project"):
        setup.plan(ROOT)


def test_archives_are_reproducible_and_separate_hook_distribution(tmp_path):
    one, two, full = (tmp_path / name for name in ("one.zip", "two.zip", "full.zip"))
    builder.build(ROOT, "marketplace", one)
    builder.build(ROOT, "marketplace", two)
    builder.build(ROOT, "github", full)
    assert one.read_bytes() == two.read_bytes()
    with zipfile.ZipFile(one) as archive:
        names = set(archive.namelist())
        assert len([p for p in names if p.endswith("/SKILL.md")]) == 14
        assert "scripts/workflow_task.py" in names
        assert "tools/workflow-harness/adapters/direction_owner.py" in names
        assert ".codex/hooks.json" not in names and "AGENTS.md" not in names
        assert not any(p.startswith((".git/", "artifacts/", "tools/workflow-harness/src/")) for p in names)
        record = json.loads(archive.read("distribution.json"))
        assert all(hashlib.sha256(archive.read(p)).hexdigest() == h for p, h in record["files"].items())
    with zipfile.ZipFile(full) as archive:
        assert ".codex/hooks.json" in archive.namelist()
        assert archive.read(".codex/hooks.json") == (ROOT / ".codex/hooks.json").read_bytes()
        assert archive.read("CLAUDE.md") == (ROOT / "CLAUDE.md").read_bytes()
    with pytest.raises(ValueError, match="already exists"):
        builder.build(ROOT, "marketplace", one)


def test_source_symlinks_and_traversal_are_rejected(tmp_path):
    (tmp_path / "link").symlink_to(ROOT / "LICENSE")
    with pytest.raises(ValueError, match="escapes|symlink"):
        builder.source_file(tmp_path, "link")
    with pytest.raises(ValueError, match="Invalid"):
        builder.source_file(tmp_path, "../LICENSE")


@pytest.mark.parametrize("profile", ["marketplace", "github"])
def test_archive_contains_declared_logo_assets(tmp_path, profile):
    output = tmp_path / f"{profile}.zip"
    builder.build(ROOT, profile, output)
    with zipfile.ZipFile(output) as archive:
        manifest = json.loads(archive.read("plugin.json"))
        interface = manifest["extensions"]["com.openai"]["interface"]
        for field, size in (("logo", 512), ("composerIcon", 256)):
            reference = interface[field]
            assert reference.startswith("./assets/")
            name = reference.removeprefix("./")
            data = archive.read(name)
            assert data == (ROOT / name).read_bytes()
            assert len(data) <= 5 * 1024 * 1024
            assert data[:16] == b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
            assert struct.unpack(">II", data[16:24]) == (size, size)
        readme = archive.read("README.md").decode("utf-8")
        image_references = re.findall(r'<(?:img|source)\b[^>]+\b(?:src|srcset)="([^"]+)"', readme)
        assert image_references
        for reference in image_references:
            if reference.startswith("https://img.shields.io/badge/"):
                continue
            assert reference.startswith("./assets/")
            name = reference.removeprefix("./")
            assert archive.read(name) == (ROOT / name).read_bytes()
        if profile == "github":
            assert archive.read("assets/logo-source.png") == (ROOT / "assets/logo-source.png").read_bytes()
        else:
            assert "assets/logo-source.png" not in archive.namelist()


@pytest.fixture
def package(tmp_path):
    archive = tmp_path / "market.zip"
    builder.build(ROOT, "marketplace", archive)
    destination = tmp_path / "plugin cache with spaces"
    with zipfile.ZipFile(archive) as source:
        source.extractall(destination)
    return destination


def test_extracted_package_setup_without_source_checkout(package, project):
    command = [sys.executable, str(package / "scripts/noehub_setup.py"), "--root", str(project)]
    before = snapshot(package)
    planned = subprocess.run(command, cwd=project, capture_output=True, text=True)
    assert planned.returncode == 0, planned.stderr + planned.stdout
    applied = subprocess.run([*command, "--apply"], cwd=project, capture_output=True, text=True)
    assert applied.returncode == 0, applied.stderr + applied.stdout
    assert snapshot(package) == before
    assert setup.SHARED_HEADINGS[0] in (project / ".noehub/workflow.md").read_text()


def test_package_update_and_relocation_preserve_project_rules(package, project):
    _, files, originals = setup.plan(project, package)
    setup.apply(project, files, originals)
    rules = project / "AGENTS.md"
    rules.write_text(rules.read_text() + "\nA new project-specific limit.\n")
    before = rules.read_bytes()
    moved = package.with_name("moved package")
    package.rename(moved)
    manifest = moved / "plugin.json"
    metadata = json.loads(manifest.read_text())
    metadata["version"] = "1.3.0"
    manifest.write_text(json.dumps(metadata))
    report, files, originals = setup.plan(project, moved)
    assert report["changes"] == [".noehub/setup.json"]
    setup.apply(project, files, originals)
    assert rules.read_bytes() == before
    assert json.loads((project / ".noehub/setup.json").read_text())["version"] == "1.3.0"


def test_external_package_context_recovery_uses_only_selected_project(package, project, tmp_path):
    (project / "original.md").write_text("Optimize locally. No remote submission is authorized.")
    (project / "interpretation.md").write_text("Keep all work local.")
    (project / "assignment.md").write_text("Inspect the current scope; do not start an experiment.")
    (project / "entry.json").write_text('{"receiver":"current_codex"}')
    owner = {"current_state": {"campaign_status": "running"},
             "execution_entry": {"configuration": "entry.json"},
             "decision_material": {"user_scope": [{"original": [{"path": "original.md"}],
                  "interpretation": {"path": "interpretation.md"}}]}}
    (project / "owner.json").write_text(json.dumps(owner))
    before = snapshot(package)
    other = tmp_path / "unrelated cwd"
    other.mkdir()
    script = str(package / "scripts/workflow_task.py")
    command = [sys.executable, script, "current", "--root", str(project), "--owner", "owner.json",
               "--assignment", "assignment.md", "--invocation", "external", "--event", "scope"]
    result = subprocess.run(command, cwd=other, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "No remote submission is authorized" in result.stdout
    assert snapshot(package) == before and list(other.iterdir()) == []
    recovery = [sys.executable, script, "recover", "--root", str(project), "--invocation", "external"]
    restored = subprocess.run(recovery, cwd=other, capture_output=True, text=True)
    assert restored.returncode == 0, restored.stdout + restored.stderr
    assert json.loads(restored.stdout)["replayed"] is False
    (project / "original.md").write_text("Scope changed; wait for the owner.")
    changed = subprocess.run(recovery, cwd=other, capture_output=True, text=True)
    assert json.loads(changed.stdout)["applicability"] == "requires_owner_reconciliation"
    missing_root = subprocess.run([sys.executable, script, "recover", "--invocation", "external"],
                                  cwd=other, capture_output=True, text=True)
    assert missing_root.returncode != 0 and "--root" in missing_root.stderr


def test_missing_dependency_reports_remedy_without_traceback(package, project):
    result = subprocess.run([sys.executable, "-S", str(package / "scripts/workflow_task.py"),
                             "recover", "--root", str(project), "--invocation", "missing"],
                            capture_output=True, text=True)
    assert result.returncode != 0 and "PyYAML is missing" in result.stderr
    assert "Traceback" not in result.stderr


def test_task_storage_cannot_follow_a_symlink_into_plugin_cache(package, project):
    outside = package / "external-records"
    outside.mkdir()
    (project / "artifacts").symlink_to(outside, target_is_directory=True)
    result = subprocess.run([sys.executable, str(package / "scripts/workflow_task.py"),
        "current", "--root", str(project), "--owner", "owner.json", "--assignment", "assignment.md",
        "--invocation", "escape"], capture_output=True, text=True)
    assert result.returncode == 2
    assert "inside the repository" in result.stdout
    assert list(outside.iterdir()) == []
