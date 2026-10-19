"""The repair workflow must reach Git and Kit users without mutating project facts."""
import json
from pathlib import Path
import re
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages/mawflow-seed-kit/src"))
from mawflow_seed_kit import materialize_project, inspect_agent_readiness
from mawflow_seed_kit.migration import plan_migration, apply_migration_plan

ASSETS = (
    "docs/ai-instructions/instructions/configuration-repair.md",
    "docs/ai-instructions/templates/configuration-repair-report.md",
    "docs/capabilities/seed-workbench-integration.md",
)


def test_fresh_kit_contains_same_workflow_and_resolvable_navigation(tmp_path):
    project = tmp_path / "project"
    materialize_project(project, project_key="repair", name="配置诊断")
    assert inspect_agent_readiness(project)["status"] == "ready"
    for ref in ASSETS:
        assert (project / ref).read_bytes() == (ROOT / ref).read_bytes()
        for link in re.findall(r"\]\(([^)]+)\)", (project / ref).read_text()):
            assert (project / ref).parent.joinpath(link.split("#")[0]).is_file(), link
    entry = yaml.safe_load((project / ".maw/agent-entry.yaml").read_text())
    assert ASSETS[0] in entry["task_routes"]["configuration_repair"]
    assert not (project / ".maw/runtime-health.json").exists()
    assert list((project / ".maw/changes").glob("*.yaml")) == []


def test_migration_adds_missing_assets_and_preserves_business_and_optional_state(tmp_path):
    project = tmp_path / "legacy"
    materialize_project(project, project_key="legacy", name="已有项目")
    for ref in ASSETS:
        (project / ref).unlink()
    readme = project / "README.md"
    readme.write_text("业务自有说明\n")
    source = project / "code/existing.txt"
    source.write_text("existing business source\n")
    optional = project / ".maw/runtime-health.json"
    optional.write_text('{"schema":"mawflow.runtime_health_contract.v1","enabled":false}\n')
    before = {p: p.read_bytes() for p in (readme, source, optional)}
    public, private = plan_migration(project, profile="blank")
    writes = {item["source_ref"] for item in private["private_writes"]}
    assert set(ASSETS).issubset(writes)
    assert not {"README.md", "code/existing.txt", ".maw/runtime-health.json"} & writes
    assert all(p.read_bytes() == value for p, value in before.items())  # preview is read-only
    result = apply_migration_plan(project, private, public["confirmation_required"], backup_root=tmp_path / "backups")
    assert result["status"] == "applied"
    assert all(p.read_bytes() == value for p, value in before.items())
    assert all((project / ref).is_file() for ref in ASSETS)
    assert inspect_agent_readiness(project)["status"] == "ready"


def test_instruction_ids_are_unique_and_public_payload_is_complete():
    ids = {}
    for path in (ROOT / "docs/ai-instructions/instructions").glob("*.md"):
        match = re.search(r"^- ID[：:]\s*(TINST-\d+)", path.read_text(), re.M)
        if match:
            assert match[1] not in ids, (path, ids.get(match[1]))
            ids[match[1]] = path
    assert ids["TINST-045"].name == "configuration-repair.md"
    assert ids["TINST-044"].name == "stage-standards.md"
    required = set(json.loads((ROOT / "PUBLIC_PAYLOAD_MANIFEST.json").read_text())["required_paths"])
    assert {*ASSETS, "tests/test_configuration_repair_distribution.py"}.issubset(required)
    upgrade = yaml.safe_load((ROOT / ".maw-template/upgrades/20261015-configuration-repair.yaml").read_text())
    assert set(ASSETS).issubset(upgrade["source_template_files"])
