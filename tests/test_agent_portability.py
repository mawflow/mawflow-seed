from __future__ import annotations

from pathlib import Path
import sys

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages/mawflow-seed-kit/src"))
from mawflow_seed_kit import (  # noqa: E402
    apply_migration_plan, compile_project_definition, export_agent_context,
    inspect_agent_readiness, materialize_project, plan_migration, rollback_migration,
)
from mawflow_seed_kit.agent_context import portable_agent_files, resolve_agent_adapter  # noqa: E402


@pytest.mark.parametrize("name,expected", [("codex", "AGENTS.md"), ("Claude Code", "CLAUDE.md"), ("gemini-cli", "GEMINI.md"), ("ChatGPT Web", "CHATGPT.md"), ("", "AI_START_HERE.md"), ("unrecognized-agent", "AI_START_HERE.md")])
def test_explicit_agent_entries_and_unknown_agent_fallback(name: str, expected: str) -> None:
    assert resolve_agent_adapter(name)["entry_file"] == expected


@pytest.fixture
def project(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    materialize_project(root, project_key="portable", name="可迁移项目")
    return root


def test_materialized_bootstrap_supports_all_adapters_without_plugins(project: Path) -> None:
    status = inspect_agent_readiness(project)
    assert status["status"] == "ready", status["issues"]
    assert set(status["adapters"]) == {"codex", "claude", "gemini", "cursor", "generic_ai", "chatgpt_web"}
    assert status["runtime_verified"] is False
    assert all(item["static_status"] == "ready" for item in status["adapters"].values())
    assert "@AI_START_HERE.md" in (project / "CLAUDE.md").read_text()
    assert "@AI_START_HERE.md" in (project / "GEMINI.md").read_text()
    assert compile_project_definition(project)["agent_readiness"]["status"] == "ready"


@pytest.mark.parametrize("ref", ["AGENTS.md", "CLAUDE.md", "GEMINI.md", "CHATGPT.md", "AI_START_HERE.md", ".maw/agent-entry.yaml", ".maw/agent-rules.yaml"])
def test_missing_or_empty_bootstrap_never_reports_agent_ready(project: Path, ref: str) -> None:
    (project / ref).write_text("")
    assert inspect_agent_readiness(project)["status"] == "needs_attention"


def test_empty_entry_is_detected_independently_of_project_structure(project: Path) -> None:
    (project / ".maw/agent-entry.yaml").write_text("schema_version: 2\nagent_entry: {}\n")
    projection = compile_project_definition(project)
    assert projection["status"] == "ready"
    assert projection["agent_readiness"]["status"] == "needs_attention"


def test_migration_preserves_custom_rules_and_adapter_text_and_rolls_back(project: Path, tmp_path: Path) -> None:
    (project / "CLAUDE.md").write_text("# 团队规则\n必须运行实际集成测试。\n")
    (project / ".maw/agent-entry.yaml").write_text("schema_version: 2\nagent_entry:\n  start_here: AI_START_HERE.md\ncustom_team: retained\n")
    original = {str(p.relative_to(project)): p.read_bytes() for p in project.rglob("*") if p.is_file()}
    public, private = plan_migration(project)
    result = apply_migration_plan(project, private, public["confirmation_required"], backup_root=tmp_path / "backups")
    assert "必须运行实际集成测试" in (project / "CLAUDE.md").read_text()
    assert yaml.safe_load((project / ".maw/agent-entry.yaml").read_text())["custom_team"] == "retained"
    assert inspect_agent_readiness(project)["status"] == "ready"
    assert all((project / ref).read_text() == text for ref, text in portable_agent_files(project).items())
    # The existing migration rollback verifies post-apply hashes before restoring.
    assert result["status"] == "applied"
    assert original["CLAUDE.md"] != (project / "CLAUDE.md").read_bytes()
    rollback = rollback_migration(project, plan_key=result["plan_key"], confirmation=result["rollback_confirmation"], backup_root=tmp_path / "backups")
    assert rollback["status"] == "rolled_back"
    assert {str(p.relative_to(project)): p.read_bytes() for p in project.rglob("*") if p.is_file()} == original


def test_context_is_bounded_and_only_loads_the_selected_module(project: Path) -> None:
    (project / "docs/selected.md").write_text("选中模块的真实说明" * 2000)
    (project / "docs/unselected.md").write_text("DO_NOT_LOAD")
    (project / ".maw/modules.yaml").write_text(yaml.safe_dump({"modules": [
        {"key": "selected", "doc": "docs/selected.md"},
        {"key": "unselected", "doc": "docs/unselected.md"},
    ]}))
    payload = export_agent_context(project, module_key="selected", max_chars=4000)
    assert payload["content_chars"] <= 4000
    assert all(item["source_ref"] != "docs/unselected.md" for item in payload["documents"])
    assert all(item["content_hash"].startswith("sha256:") for item in payload["documents"])
    assert payload["local_overlays_included"] is False


@pytest.mark.parametrize("ref", [".local/private.md", "../outside.md", ".ssh/key", "prompts/task.md", "docs/archive/task.md"])
def test_context_rejects_private_or_manual_only_references(project: Path, ref: str) -> None:
    (project / ".maw/modules.yaml").write_text(yaml.safe_dump({"modules": [{"key": "unsafe", "doc": ref}]}))
    with pytest.raises(ValueError, match="seed_agent_ref_forbidden"):
        export_agent_context(project, module_key="unsafe")


def test_context_rejects_symlinked_parent(project: Path, tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "context.md").write_text("private")
    (project / "linked").symlink_to(outside, target_is_directory=True)
    (project / ".maw/modules.yaml").write_text(yaml.safe_dump({"modules": [{"key": "unsafe", "doc": "linked/context.md"}]}))
    with pytest.raises(ValueError, match="seed_agent_symlink_forbidden"):
        export_agent_context(project, module_key="unsafe")


def test_damaged_managed_adapter_block_requires_review(project: Path) -> None:
    (project / "CLAUDE.md").write_text("<!-- mawflow:bootstrap:start -->\nmissing end")
    with pytest.raises(ValueError, match="seed_agent_managed_block_ambiguous"):
        portable_agent_files(project)


def test_web_adapter_links_resolve_in_materialized_project(project: Path) -> None:
    import re
    text = (project / "CHATGPT.md").read_text()
    for ref in re.findall(r"\]\(([^)]+)\)", text):
        assert (project / ref).is_file(), ref
    assert "commit SHA" in text
    assert "只读" in text or "只有读取能力" in text
    assert "不假定" in text
    assert "CHATGPT.md" in (project / "README.md").read_text()


def test_mismatched_declared_adapter_fails_readiness(project: Path) -> None:
    path = project / ".maw/agent-entry.yaml"
    entry = yaml.safe_load(path.read_text())
    entry["tool_adapters"]["claude"]["file"] = "WRONG.md"
    path.write_text(yaml.safe_dump(entry))
    assert inspect_agent_readiness(project)["status"] == "needs_attention"


def test_agent_upgrade_preserves_newer_project_schemas(project: Path) -> None:
    path = project / ".maw/modules.yaml"
    path.write_text(path.read_text().replace("schema_version: 2", "schema_version: 3"))
    public, _ = plan_migration(project)
    assert all(item["source_ref"] != ".maw/modules.yaml" for item in public["writes"])
