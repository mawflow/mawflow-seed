from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import os
import subprocess

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages/mawflow-seed-kit/src"))
from mawflow_seed_kit import (  # noqa: E402
    apply_component_plan, apply_migration_plan, compile_project_definition, export_agent_context, inspect_components,
    materialize_project, plan_component_init, plan_migration,
)
from mawflow_seed_kit.agent_context import MAX_BYTES, render_agent_context  # noqa: E402
from mawflow_seed_kit import compatibility  # noqa: E402
from mawflow_seed_kit.components import _git_output  # noqa: E402
from mawflow_seed_kit.commands.cli import main  # noqa: E402


def snapshot(root):
    return {str(p.relative_to(root)): (p.stat().st_mtime_ns, p.stat().st_mode,
            hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None)
            for p in root.rglob("*")}


@pytest.fixture
def project(tmp_path):
    root = tmp_path / "project"
    materialize_project(root, project_key="governance", name="指令治理")
    return root


@pytest.mark.parametrize("version,contract", [("99.0.0", 2), ("2.0.0", 99), ("99.0.0rc1", 2)])
def test_newer_project_requires_tool_upgrade_and_cannot_be_migrated(project, version, contract):
    path = project / ".maw/seed.lock"
    lock = yaml.safe_load(path.read_text())
    lock.update(seed_version=version, contract_version=contract, contract_fingerprint="changed")
    path.write_text(yaml.safe_dump(lock))
    before = snapshot(project)
    result = compile_project_definition(project)
    assert result["editable"] is False
    assert result["migration_required"] is False
    assert result["tool_compatibility"]["status"] == "tool_upgrade_required"
    assert "seed_tool_upgrade_required" in {x["code"] for x in result["issues"]}
    with pytest.raises(ValueError, match="seed_tool_upgrade_required"):
        plan_migration(project)
    backup = project.parent / "unexpected-backup"
    with pytest.raises(ValueError, match="seed_tool_upgrade_required"):
        apply_migration_plan(project, {}, "not-authorized", backup_root=backup)
    assert not backup.exists()
    assert snapshot(project) == before


def test_old_tool_detects_newer_lock_even_when_contract_fingerprint_matches(project, monkeypatch):
    monkeypatch.setattr(compatibility, "SEED_VERSION", "2.12.0")
    result = compile_project_definition(project)
    assert result["tool_compatibility"]["status"] == "tool_upgrade_required"
    assert not result["editable"] and not result["migration_required"]


@pytest.mark.parametrize("command,code", [(["project", "doctor"], 0), (["project", "upgrade"], 1), (["project", "sources", "consolidate"], 1)])
def test_seed_readonly_dispatch_never_persists_plans(project, capsys, command, code):
    before = snapshot(project)
    assert main(["--read-only", *command, "--root", str(project)]) == code
    result = json.loads(capsys.readouterr().out)
    assert result.get("error") == ("readonly_command_forbidden" if code else None)
    assert snapshot(project) == before


@pytest.mark.parametrize("version,status", [("2.0.0", "project_migration_required"), ("unrecognized", "unknown")])
def test_other_version_directions_remain_explicit(project, version, status):
    path = project / ".maw/seed.lock"
    lock = yaml.safe_load(path.read_text())
    lock.update(seed_version=version, contract_fingerprint="different")
    path.write_text(yaml.safe_dump(lock))
    result = compile_project_definition(project)
    assert result["tool_compatibility"]["status"] == status
    assert not result["editable"]
    assert result["migration_required"] == (status == "project_migration_required")


def test_unknown_contract_does_not_suggest_migration():
    result = compatibility.tool_compatibility({"contract_version": "future", "seed_version": compatibility.SEED_VERSION})
    assert result["status"] == "unknown" and not result["migration_required"]


def test_large_utf8_module_exports_bounded_prefix_without_writing(project):
    path = project / "docs/large.md"
    path.write_text("界" * (MAX_BYTES // 3 + 100))
    (project / ".maw/modules.yaml").write_text(yaml.safe_dump({"modules": [{"key": "large", "doc": "docs/large.md"}]}))
    before = snapshot(project)
    result = export_agent_context(project, module_key="large", max_chars=50000)
    doc = next(x for x in result["documents"] if x["source_ref"] == "docs/large.md")
    assert doc["truncated"] and doc["hash_scope"] == "read_prefix"
    assert doc["source_bytes"] == path.stat().st_size
    assert doc["read_bytes"] <= MAX_BYTES
    assert doc["content"] and set(doc["content"]) == {"界"}
    assert result["content_chars"] <= 50000
    assert "read_prefix" in render_agent_context(result)
    assert snapshot(project) == before


def test_exhausted_budget_does_not_open_later_module(project, monkeypatch):
    (project / ".maw/modules.yaml").write_text(yaml.safe_dump({"modules": [{"key": "large", "doc": "docs/not-read.md"}]}))
    original = Path.open
    def guarded(path, *args, **kwargs):
        assert path.name != "not-read.md"
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, "open", guarded)
    result = export_agent_context(project, module_key="large", max_chars=1000)
    assert {"source_ref": "docs/not-read.md", "reason": "budget"} in result["omitted"]


def test_git_inspection_does_not_refresh_index(tmp_path):
    repo = tmp_path / "git"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    file = repo / "tracked.txt"
    file.write_text("synthetic\n")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    # Force a stat-cache refresh opportunity without changing tracked content.
    now = file.stat().st_mtime_ns
    os.utime(file, ns=(now + 2_000_000_000, now + 2_000_000_000))
    before = snapshot(repo)
    assert _git_output(repo, "status", "--porcelain") == "A  tracked.txt"
    assert snapshot(repo) == before


@pytest.mark.parametrize("fields,ready", [
    ({"path": "code/api"}, True), ({"local_path": "code/api"}, True),
    ({"path": "code/api", "local_path": "code/api"}, True),
    ({"path": "code/api", "local_path": "code/other"}, False),
    ({"path": "../outside"}, False), ({}, False),
])
def test_legacy_component_paths_preserve_conflict_checks(project, tmp_path, fields, ready):
    public, private = plan_component_init(project, key="api", component_type="backend", name="API")
    apply_component_plan(project, private, public["confirmation_required"], backup_root=tmp_path / "backups")
    path = project / "code/api/.maw.component.yaml"
    value = yaml.safe_load(path.read_text())
    value["component"].pop("local_path", None)
    value["component"].pop("path", None)
    value["component"].update(fields)
    path.write_text(yaml.safe_dump(value))
    before = snapshot(project)
    result = inspect_components(project, "api")
    assert (result["status"] == "ready") == ready
    assert snapshot(project) == before
