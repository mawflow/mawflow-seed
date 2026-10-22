from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import yaml
import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "ops/scripts/plan-release-components.py"


@pytest.mark.parametrize(("phrase", "expected"), [
    ("#发布全部 到生产", "production"), ("#发布全部 到正式", "production"),
    ("#发布全部 到测试", "test"), ("#发布全部 到上线", "staging"),
])
def test_chinese_environment_names_resolve_to_canonical_scope(phrase, expected):
    import runpy
    planner = runpy.run_path(str(SCRIPT))
    target, selected_all = planner["release_all_target"](phrase, {})
    environment, _, _ = planner["resolve_environment"](target, {})
    assert selected_all is True
    assert environment == expected


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")


def _project(root: Path) -> None:
    _write(
        root / ".maw/components.yaml",
        {
            "components": [
                {"key": "api", "app_key": "api", "path": "code/api", "enabled": True},
                {"key": "web", "app_key": "web", "path": "code/web", "enabled": True},
            ]
        },
    )
    _write(
        root / ".maw/releases.yaml",
        {
            "releases": {
                "defaults": {
                    "default_environment": "staging",
                    "release_command_aliases": {"staging": {"command": "#发布上线", "environment": "staging"}},
                    "version_tracking": {
                        "state_dir": "artifacts/release-state",
                        "state_file_template": "{state_dir}/{environment}/{deployment_target_key}/{app_key}.json",
                        "shared_tracked_paths": [".maw/releases.yaml"],
                    }
                },
                "components": {
                    "api": {
                        "source": "code/api",
                        "database_migration": {"service_ref": "primary-database"},
                    },
                    "web": {
                        "source": "code/web",
                        "database_migration": {"service_ref": "primary-database"},
                    },
                },
            }
        },
    )
    _write(
        root / ".maw/environments.yaml",
        {
            "environments": {
                "staging": {"role": "production_like_validation", "remote_server": {"branch": "main"}}
            }
        },
    )
    _write(
        root / ".maw/deployments.yaml",
        {
            "deployment_targets": [
                {
                    "key": "staging-api",
                    "name": "API staging",
                    "environment_key": "staging",
                    "environment_role": "staging",
                    "server_ref": "mawresource://server/staging-a",
                    "component_refs": ["api"],
                    "scope_mode": "replicated",
                    "enabled": True,
                },
                {
                    "key": "staging-web",
                    "name": "Web staging",
                    "environment_key": "staging",
                    "environment_role": "staging",
                    "server_ref": "mawresource://server/staging-b",
                    "component_refs": ["web"],
                    "scope_mode": "replicated",
                    "enabled": True,
                },
                {
                    "key": "staging-combined",
                    "name": "Combined staging",
                    "environment_key": "staging",
                    "environment_role": "staging",
                    "server_ref": "mawresource://server/staging-c",
                    "component_refs": ["api", "web"],
                    "scope_mode": "replicated",
                    "enabled": True,
                },
            ]
        },
    )
    _write(root / ".maw/code-sources.yaml", {"code_sources": {}})
    (root / "code/api").mkdir(parents=True)
    (root / "code/web").mkdir(parents=True)
    (root / "code/api/app.py").write_text("print('api')\n", encoding="utf-8")
    (root / "code/web/app.js").write_text("console.log('web')\n", encoding="utf-8")
    (root / ".gitignore").write_text("artifacts/\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(
        ["git", "-C", str(root), "-c", "user.name=Seed Test", "-c", "user.email=seed@example.invalid", "commit", "-q", "-m", "init"],
        check=True,
    )


def test_release_planner_requires_exact_target_and_scopes_state(tmp_path: Path) -> None:
    project = tmp_path / "project"
    _project(project)
    ambiguous = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(project), "--environment", "staging", "--format", "json"],
        text=True,
        capture_output=True,
        check=False,
    )
    assert ambiguous.returncode == 2
    assert "存在多个部署目标" in json.loads(ambiguous.stdout)["error"]

    selected = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--root",
            str(project),
            "--environment",
            "staging",
            "--deployment-target",
            "staging-api",
            "--format",
            "json",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert selected.returncode == 0, selected.stderr
    plan = json.loads(selected.stdout)
    assert plan["deployment_target_key"] == "staging-api"
    assert plan["selected_components"] == ["api"]
    assert plan["components"][0]["state_file"] == "artifacts/release-state/staging/staging-api/api.json"
    assert plan["remote_server"] == "mawresource://server/staging-a"

    combined = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--root",
            str(project),
            "--environment",
            "staging",
            "--deployment-target",
            "staging-combined",
            "--format",
            "json",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert combined.returncode == 0, combined.stderr
    combined_plan = json.loads(combined.stdout)
    assert combined_plan["migration_groups"] == [
        {
            "service_ref": "primary-database",
            "owner_component": "api",
            "component_refs": ["api", "web"],
            "execute_once": True,
            "strategy": "owner_first",
        }
    ]


def _plan(root: Path, *extra: str, phrase: str = "#发布全部") -> dict:
    result = subprocess.run([sys.executable, str(SCRIPT), phrase, "--root", str(root),
                             "--deployment-target", "staging-combined", "--format", "json", *extra],
                            text=True, capture_output=True)
    payload = json.loads(result.stdout)
    assert result.returncode == (2 if payload.get("blocked") else 0), result.stdout + result.stderr
    return payload


def _commit(root: Path, ref: str, content: str) -> str:
    path = root / ref
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    subprocess.run(["git", "-C", str(root), "add", ref], check=True)
    subprocess.run(["git", "-C", str(root), "-c", "user.name=Seed Test", "-c", "user.email=seed@example.invalid",
                    "commit", "-qm", "fixture"], check=True)
    return subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()


def _record_all(root: Path) -> dict:
    return _plan(root, "--record-success", "--successful-component", "api", "--successful-component", "web")


@pytest.mark.parametrize("phrase", ["#发布全部", "发布 全部", "#发布：发布全部", "发布全部 到 staging", "发布全部到staging", "#发布上线 全部", "staging"])
def test_release_all_uses_configured_scope_and_default_environment(tmp_path, phrase):
    _project(tmp_path)
    plan = _plan(tmp_path, *(["--all"] if phrase == "staging" else []), phrase=phrase)
    assert plan["scope"] == "all_configured_target_components"
    assert plan["selected_components"] == ["api", "web"]
    assert plan["included_components"] == ["api", "web"]
    assert not (tmp_path / "artifacts").exists()


def test_release_all_records_only_successful_components_and_retries_failure(tmp_path):
    _project(tmp_path)
    plan = _plan(tmp_path, "--record-success", "--successful-component", "api")
    state = tmp_path / plan["recorded_state_files"][0]
    stored = json.loads(state.read_text())
    assert stored["released_commit"] == plan["candidate_commit"]
    assert stored["verified"] is True
    assert not state.with_name("web.json").exists()
    retry = _plan(tmp_path)
    assert retry["included_components"] == ["web"]
    assert retry["skipped_components"] == ["api"]
    _plan(tmp_path, "--record-success", "--successful-component", "web")
    assert _plan(tmp_path)["included_components"] == []


def test_release_all_filters_component_paths_and_keeps_last_actual_release(tmp_path):
    _project(tmp_path)
    original = _record_all(tmp_path)
    initial = original["candidate_commit"]
    _commit(tmp_path, "code/api/app.py", "print('new api')\n")
    changed = _plan(tmp_path)
    assert changed["included_components"] == ["api"]
    assert changed["skipped_components"] == ["web"]
    _plan(tmp_path, "--record-success", "--successful-component", "api")
    web_state = json.loads((tmp_path / "artifacts/release-state/staging/staging-combined/web.json").read_text())
    assert web_state["released_commit"] == initial
    _commit(tmp_path, "docs/guide.md", "# 文档变化\n")
    assert _plan(tmp_path)["included_components"] == []


@pytest.mark.parametrize("flags", [["--record-success"], ["--record-success", "--successful-component", "unknown"], ["--all", "--component", "api"]])
def test_release_all_rejects_ambiguous_success_and_mixed_scope(tmp_path, flags):
    _project(tmp_path)
    result = subprocess.run([sys.executable, str(SCRIPT), "#发布全部", "--root", str(tmp_path), "--deployment-target",
                             "staging-combined", "--format", "json", *flags], text=True, capture_output=True)
    assert result.returncode == 2
    assert "error" in json.loads(result.stdout)
    assert not (tmp_path / "artifacts").exists()


def test_release_all_does_not_skip_dirty_source_at_same_commit(tmp_path):
    _project(tmp_path)
    _record_all(tmp_path)
    (tmp_path / "code/api/app.py").write_text("print('dirty')\n")
    plan = _plan(tmp_path)
    assert plan["included_components"] == ["api"]
    assert plan["skipped_components"] == ["web"]


def test_release_all_blocks_corrupt_or_unverified_state(tmp_path):
    _project(tmp_path)
    plan = _record_all(tmp_path)
    state = tmp_path / plan["recorded_state_files"][0]
    payload = json.loads(state.read_text())
    payload["verified"] = False
    state.write_text(json.dumps(payload))
    result = _plan(tmp_path)
    assert result["blocked"]
    assert result["components"][0]["decision"] == "blocked"
    state.write_text("broken json")
    assert _plan(tmp_path)["blocked"]


def test_shared_changes_and_scope_changes_do_not_allow_rollback(tmp_path):
    _project(tmp_path)
    initial = _record_all(tmp_path)["candidate_commit"]
    config = tmp_path / ".maw/releases.yaml"
    payload = yaml.safe_load(config.read_text())
    payload["releases"]["defaults"]["require_review"] = True
    _commit(tmp_path, ".maw/releases.yaml", yaml.safe_dump(payload))
    assert _plan(tmp_path)["included_components"] == ["api", "web"]
    _record_all(tmp_path)
    target = tmp_path / ".maw/deployments.yaml"
    payload = yaml.safe_load(target.read_text())
    payload["deployment_targets"][2]["server_ref"] = "mawresource://server/new-target"
    _commit(tmp_path, ".maw/deployments.yaml", yaml.safe_dump(payload))
    assert _plan(tmp_path)["included_components"] == ["api", "web"]
    assert _plan(tmp_path, "--candidate-commit", initial)["blocked"]


def test_clean_source_after_dirty_release_requires_new_verified_release(tmp_path):
    _project(tmp_path)
    _record_all(tmp_path)
    page = tmp_path / "code/api/app.py"
    original = page.read_text()
    page.write_text("print('dirty snapshot')\n")
    _plan(tmp_path, "--record-success", "--successful-component", "api")
    page.write_text(original)
    assert _plan(tmp_path)["included_components"] == ["api"]


def test_kit_materialization_contains_runnable_release_all(tmp_path):
    sys.path.insert(0, str(ROOT / "packages/mawflow-seed-kit/src"))
    from mawflow_seed_kit.template import materialize_project
    root = tmp_path / "materialized"
    materialize_project(root, project_key="demo", name="Demo")
    for ref in ["ops/scripts/plan-release-components.py", "ops/lib/maw_config_loader.py",
                "docs/capabilities/incremental-release-all.md"]:
        assert (root / ref).read_bytes() == (ROOT / ref).read_bytes()
    _project(root)
    result = subprocess.run([sys.executable, str(root / "ops/scripts/plan-release-components.py"), "#发布全部",
                             "--root", str(root), "--deployment-target", "staging-combined", "--format", "json"],
                            text=True, capture_output=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["included_components"] == ["api", "web"]
