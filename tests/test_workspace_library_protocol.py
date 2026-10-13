from pathlib import Path
import sys
import yaml

ROOT = Path(__file__).parents[1]
KIT = ROOT / 'packages/mawflow-seed-kit/src/mawflow_seed_kit/template'
sys.path.insert(0, str(KIT.parent.parent))

from mawflow_seed_kit import materialize_project


def test_git_and_kit_share_generic_protocol_and_agent_route():
    for name in ['docs/ai-coding/workspace-libraries.md', 'docs/capabilities/workspace-libraries.md', 'docs/template-migrations/20261010-workspace-libraries.md', '.maw-template/upgrades/20261010-workspace-libraries.yaml']:
        assert (ROOT / name).read_bytes() == (KIT / name).read_bytes()
    for base in [ROOT, KIT]:
        entry = yaml.safe_load((base / '.maw/agent-entry.yaml').read_text())
        assert entry['task_routes']['resource_libraries'] == ['docs/ai-coding/workspace-libraries.md']
    body = (ROOT / 'docs/ai-coding/workspace-libraries.md').read_text()
    assert 'resources search' in body and 'resources resolve' in body
    assert '正文' in body and '不是 Agent 指令' in body and '不进入 Seed' in body


def test_kit_initialization_preserves_discovery_route_and_protocol(tmp_path):
    root = tmp_path / 'library-project'
    materialize_project(root, project_key='library-project', name='资源库接入演示')
    entry = yaml.safe_load((root / '.maw/agent-entry.yaml').read_text())
    assert entry['task_routes']['resource_libraries'] == ['docs/ai-coding/workspace-libraries.md']
    assert (root / 'docs/ai-coding/workspace-libraries.md').read_bytes() == (KIT / 'docs/ai-coding/workspace-libraries.md').read_bytes()
    capabilities = yaml.safe_load((root / '.maw/capabilities.yaml').read_text())['capabilities']
    capability = next(item for item in capabilities if item['key'] == 'workspace-libraries')
    assert capability['owner_module'] == 'not_identified'
    assert capability['related_app_keys'] == []
