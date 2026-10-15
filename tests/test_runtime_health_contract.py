"""Optional adoption must preserve old projects and perform no runtime actions."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('runtime_health_check', ROOT / 'ops/scripts/check-runtime-health.py')
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)
ASSETS = ('.maw/runtime-health.example.json', '.maw/schemas/runtime-health.schema.json',
          '.maw/schemas/runtime-health-snapshot.schema.json', 'docs/capabilities/runtime-health-contract.md',
          'docs/capabilities/examples/runtime-health-native.json', 'docs/capabilities/examples/runtime-health-sidecar.json',
          'ops/scripts/check-runtime-health.py')


def test_missing_and_disabled_declarations_are_success_without_writes(tmp_path):
    assert checker.inspect(tmp_path)['adoption'] == 'not_adopted'
    assert list(tmp_path.iterdir()) == []
    path = tmp_path / '.maw/runtime-health.json'
    path.parent.mkdir()
    path.write_bytes((ROOT / ASSETS[0]).read_bytes())
    before = {str(p): p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}
    result = checker.inspect(tmp_path)
    assert result['status'] == 'success' and result['adoption'] == 'disabled'
    assert result['changed_paths'] == [] and result['score_effect'] == 'none' and not result['runtime_verified']
    assert before == {str(p): p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}


@pytest.mark.parametrize('mode', ['native', 'sidecar'])
def test_examples_and_schema_are_compatible(mode, tmp_path):
    raw = json.loads((ROOT / f'docs/capabilities/examples/runtime-health-{mode}.json').read_text())
    assert checker.validate(raw) == mode
    path = tmp_path / '.maw/runtime-health.json'
    path.parent.mkdir()
    path.write_text(json.dumps(raw))
    result = subprocess.run([sys.executable, str(ROOT / ASSETS[-1]), '--root', str(tmp_path)], capture_output=True, text=True)
    assert result.returncode == 0 and json.loads(result.stdout)['adoption'] == mode


@pytest.mark.parametrize('mutation', ['command', 'url', 'method', 'duplicate', 'pointer', 'nan', 'secret', 'empty'])
def test_uncontrolled_declarations_fail_closed(mutation, tmp_path):
    raw = json.loads((ROOT / 'docs/capabilities/examples/runtime-health-sidecar.json').read_text())
    check = raw['checks'][0]
    if mutation in ('command', 'url', 'method', 'secret'):
        check[mutation] = 'invalid-private-value'
    elif mutation == 'duplicate':
        raw['checks'].append(copy.deepcopy(check))
    elif mutation == 'pointer':
        check['path'] = '/../../private'
    elif mutation == 'nan':
        check['assertion'] = {'type': 'json_number_max', 'pointer': '/count', 'maximum': float('nan')}
    else:
        raw['checks'] = []
    path = tmp_path / '.maw/runtime-health.json'
    path.parent.mkdir()
    path.write_text(json.dumps(raw))
    result = checker.inspect(tmp_path)
    assert result['status'] == 'failed' and result['changed_paths'] == []
    assert 'invalid-private-value' not in json.dumps(result)


def test_native_does_not_allow_sidecar_or_remote_urls(tmp_path):
    raw = json.loads((ROOT / 'docs/capabilities/examples/runtime-health-native.json').read_text())
    raw['checks'] = []
    with pytest.raises(ValueError):
        checker.validate(raw)
    raw.pop('checks')
    raw['native']['path'] = 'https://private.example.invalid/health'
    with pytest.raises(ValueError):
        checker.validate(raw)


def test_git_and_packaged_template_assets_are_identical_and_opt_in(tmp_path):
    package = ROOT / 'packages/mawflow-seed-kit/src'
    if not (package / 'mawflow_seed_kit/template').exists():
        pytest.skip('Seed distribution check belongs to the Seed repository')
    sys.path.insert(0, str(package))
    from mawflow_seed_kit import materialize_project
    project = tmp_path / 'fresh'
    materialize_project(project, project_key='optional-health', name='可选运行健康')
    for ref in ASSETS:
        assert (project / ref).read_bytes() == (ROOT / ref).read_bytes()
    assert not (project / '.maw/runtime-health.json').exists()
    assert not (project / 'code/mawflow-ops').exists()
    assert checker.inspect(project)['adoption'] == 'not_adopted'
