from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "ops/scripts/plan-release-components.py"


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
                    "version_tracking": {
                        "state_dir": "artifacts/release-state",
                        "state_file_template": "{state_dir}/{environment}/{deployment_target_key}/{app_key}.json",
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
