"""Exercise the reusable workflow after Kit materialization and safe migration."""

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages/mawflow-seed-kit/src"))
from mawflow_seed_kit import inspect_agent_readiness, materialize_project  # noqa: E402
from mawflow_seed_kit.migration import apply_migration_plan, plan_migration  # noqa: E402

ASSETS = (
    "docs/ai-instructions/instructions/generate-update-notes.md",
    "docs/ai-coding/update-notes.md",
    "docs/updates/README.md",
    "docs/updates/note-template.yaml",
    ".maw/schemas/update-note.schema.json",
    ".maw/changes/README.md",
    "ops/scripts/generate-update-notes.py",
    "ops/scripts/update_notes/__init__.py",
    "ops/scripts/update_notes/store.py",
    "ops/scripts/update_notes/render.py",
)


def command(root, *args):
    result = subprocess.run(
        [sys.executable, str(root / ASSETS[6]), *args, "--root", str(root)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return json.loads(result.stdout)


def apply(root, *args):
    preview = command(root, *args)
    assert preview["changed_paths"] == []
    return command(
        root, *args, "--execute", "--expected-fingerprint", preview["fingerprint"]
    )


def test_new_kit_project_contains_workflow_without_source_history(tmp_path):
    project = tmp_path / "fresh"
    materialize_project(project, project_key="updates", name="空项目更新验收")
    assert inspect_agent_readiness(project)["status"] == "ready"
    for ref in ASSETS:
        assert (project / ref).read_bytes() == (ROOT / ref).read_bytes()
    assert list((project / ".maw/changes").glob("*.yaml")) == []
    assert not (project / "docs/intake/20261004-update-notes-seed-start.md").exists()
    for ref in (ASSETS[0], ASSETS[1], ASSETS[2]):
        doc = project / ref
        for link in re.findall(r"\]\(([^)]+)\)", doc.read_text()):
            assert (doc.parent / link.split("#")[0]).is_file(), link
    for args in (("render",), ("render", "--all"), ("render-cloud",)):
        assert apply(project, *args)["total"] == 0
    assert "暂无已记录动态" in (project / "docs/updates/updates.md").read_text()
    assert command(project, "check")["status"] == "success"
    entry = yaml.safe_load((project / ".maw/agent-entry.yaml").read_text())
    assert entry["execution_contract"]["update_notes"]["default_limit"] == 100
    rules = yaml.safe_load((project / ".maw/agent-rules.yaml").read_text())["rules"]
    assert any(r["id"] == "record_project_update_notes" for r in rules)


def test_materialized_cli_records_once_and_prepares_cloud(tmp_path):
    project = tmp_path / "project"
    materialize_project(project, project_key="demo", name="项目自己的动态")
    value = yaml.safe_load((project / ASSETS[3]).read_text())
    value["record_key"] = "update.demo.001"
    value["task_key"] = "demo-task"
    payload = value["payload"]
    payload["summary"] = "本项目支持更新动态查询"
    payload["details"] = [{"label": "说明", "path": ASSETS[1]}]
    evidence = project / "docs/evidence.md"
    evidence.write_text("此为临时项目测试证据\n")
    value["evidence_refs"] = [{"path": "docs/evidence.md", "kind": "test_result"}]
    test_input = tmp_path / "note.json"
    test_input.write_text(json.dumps(value, ensure_ascii=False))
    assert (
        apply(project, "record", "--input", str(test_input))["imported_or_recorded"]
        == 1
    )
    assert apply(project, "record", "--input", str(test_input))["changed_paths"] == []
    for args in (("render",), ("render", "--all"), ("render-cloud",)):
        apply(project, *args)
        assert apply(project, *args)["changed_paths"] == []
    assert command(project, "check")["total"] == 1
    receipt = json.loads(
        (project / ".maw/generated/update-notes-cloud.json").read_text()
    )
    assert receipt["status"] == "prepared_not_published"
    assert (
        "本项目支持更新动态查询" in (project / "docs/updates/CHANGELOG.md").read_text()
    )


@pytest.mark.parametrize("has_fragments", [True, False])
def test_controlled_migration_adds_assets_preserves_existing_facts(
    tmp_path, has_fragments
):
    project = tmp_path / "legacy"
    materialize_project(project, project_key="legacy", name="保留目标项目")
    for ref in ASSETS:
        (project / ref).unlink()
    entry_path = project / ".maw/agent-entry.yaml"
    entry = yaml.safe_load(entry_path.read_text())
    entry["execution_contract"].pop("update_notes")
    entry["project_extension"] = {"readonly_area": "code/customer"}
    entry_path.write_text(yaml.safe_dump(entry, allow_unicode=True))
    rules_path = project / ".maw/agent-rules.yaml"
    rules = yaml.safe_load(rules_path.read_text())
    rules["rules"] = [
        r for r in rules["rules"] if r["id"] != "record_project_update_notes"
    ]
    rules["rules"].append(
        {"id": "customer_boundary", "severity": "required", "summary": "保留项目规则"}
    )
    rules_path.write_text(yaml.safe_dump(rules, allow_unicode=True))
    lifecycle_path = project / ".maw/project-lifecycle.yaml"
    lifecycle = yaml.safe_load(lifecycle_path.read_text())
    lifecycle["project_lifecycle"]["change_fragments"].pop("update_notes")
    if not has_fragments:
        lifecycle["project_lifecycle"].pop("change_fragments")
    lifecycle_path.write_text(yaml.safe_dump(lifecycle, allow_unicode=True))
    readme = project / "README.md"
    readme.write_text("业务项目自有 README\n")
    history = project / ".maw/changes/project-existing.yaml"
    original_fragment = "schema_version: 1\nrecord_type: task\npayload: {}\n"
    history.write_text(original_fragment)
    public, private = plan_migration(project, profile="blank")
    writes = {r["source_ref"]: r["proposed_text"] for r in private["private_writes"]}
    assert set(ASSETS).issubset(writes)
    assert "README.md" not in writes
    assert str(history.relative_to(project)) not in writes
    proposed = yaml.safe_load(writes[".maw/agent-entry.yaml"])
    assert proposed["project_extension"] == entry["project_extension"]
    assert (
        proposed["execution_contract"]["update_notes"]["record_type"] == "update_note"
    )
    proposed_rules = yaml.safe_load(writes[".maw/agent-rules.yaml"])["rules"]
    assert {"customer_boundary", "record_project_update_notes"}.issubset(
        {r["id"] for r in proposed_rules}
    )
    assert (
        "update_notes"
        in yaml.safe_load(writes[".maw/project-lifecycle.yaml"])["project_lifecycle"][
            "change_fragments"
        ]
    )
    assert public["migration_safety"]["business_readme_preserved"]
    result = apply_migration_plan(
        project,
        private,
        public["confirmation_required"],
        backup_root=tmp_path / "backups",
    )
    assert result["status"] == "applied"
    assert history.read_text() == original_fragment
    assert readme.read_text() == "业务项目自有 README\n"
    assert inspect_agent_readiness(project)["status"] == "ready"
    for args in (("render",), ("render", "--all"), ("render-cloud",)):
        assert apply(project, *args)["total"] == 0
    assert command(project, "check")["status"] == "success"


def test_git_payload_and_upgrade_declare_complete_general_assets():
    manifest = json.loads((ROOT / "PUBLIC_PAYLOAD_MANIFEST.json").read_text())
    required = set(manifest["required_paths"])
    assert set(ASSETS).issubset(required)
    assert "tests/test_update_notes_distribution.py" in required
    policy = yaml.safe_load(
        (ROOT / ".maw-template/upgrades/20261004-update-notes.yaml").read_text()
    )
    assert set(ASSETS).issubset(set(policy["source_template_files"]))
    assert not any(ref.startswith(".maw/changes/update.") for ref in required)
    assert "#模板升级" in (ROOT / policy["propagation"]["migration_note"]).read_text()
    assert "TINST-043" in (ROOT / "docs/ai-instructions/README.md").read_text()
