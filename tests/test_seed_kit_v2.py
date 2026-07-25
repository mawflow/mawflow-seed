from __future__ import annotations

from pathlib import Path
import subprocess
import sys

import pytest
import yaml


KIT_SRC = Path(__file__).resolve().parents[1] / "packages" / "mawflow-seed-kit" / "src"
if str(KIT_SRC) not in sys.path:
    sys.path.insert(0, str(KIT_SRC))

from mawflow_seed_kit import (  # noqa: E402
    apply_change_plan,
    apply_migration_plan,
    compile_project_definition,
    materialize_project,
    plan_change_set,
    plan_migration,
    rollback_migration,
)
from mawflow_seed_kit.catalog import contract_fingerprint, public_catalog  # noqa: E402


def _git_init(root: Path) -> None:
    subprocess.run(["git", "init", "-q", str(root)], check=True)


def test_materialized_project_is_complete_and_editable(tmp_path: Path) -> None:
    root = tmp_path / "project"
    result = materialize_project(root, project_key="demo-project", name="演示项目", profile="web-api")
    _git_init(root)

    projection = compile_project_definition(root)

    assert result["contract_fingerprint"] == contract_fingerprint()
    assert projection["schema"] == "mawflow.seed_project_definition.v2"
    assert projection["status"] == "ready"
    assert projection["editable"] is True
    assert projection["project"]["key"] == "demo-project"
    assert projection["project"]["classification"]["delivery_mode"] == "new_defined"
    assert set(projection["configs"][".maw/environments.yaml"]["environments"]) == {
        "local",
        "staging",
        "production",
    }
    assert projection["configs"][".maw/technology.yaml"]["technology"]["runtime_mode"] == "container"
    assert len(projection["configs"]["docs/handbooks/manifest.yaml"]["handbook_system"]["volumes"]) == 6
    assert set(projection["configs"][".maw/app-runtime.yaml"]["app_runtime"]["apps"]) == {"server", "client"}
    assert public_catalog()["trust_boundary"]["arbitrary_paths_writable"] is False


def test_multi_file_change_set_adds_component_and_runtime_atomically(tmp_path: Path) -> None:
    root = tmp_path / "project"
    materialize_project(root, project_key="demo", name="Demo", profile="minimal")
    _git_init(root)
    components_path = root / ".maw/components.yaml"
    components_path.write_text(components_path.read_text(encoding="utf-8") + "# keep-this-comment\n", encoding="utf-8")
    projection = compile_project_definition(root)
    payload = {
        "schema": "mawflow.seed_change_set.v2",
        "base_projection_fingerprint": projection["fingerprint"],
        "base_contract_fingerprint": contract_fingerprint(),
        "reason": "从本地工作台添加 worker",
        "operations": [
            {
                "op": "component.add",
                "key": "worker",
                "scope": "shared",
                "values": {
                    "app_key": "worker",
                    "name": "任务执行器",
                    "type": "job",
                    "path": "code/worker",
                    "source_root": "src",
                    "enabled": True,
                    "guide": "docs/components/worker.md",
                },
            },
            {
                "op": "runtime.app.upsert",
                "key": "worker",
                "scope": "shared",
                "values": {
                    "enabled": True,
                    "component_ref": "worker",
                    "code_path": "code/worker",
                    "local_url": "http://127.0.0.1:8090",
                    "healthcheck_path": "/health",
                },
            },
        ],
    }

    public, private = plan_change_set(root, payload)
    result = apply_change_plan(root, private, public["confirmation_required"], backup_root=tmp_path / "backups")

    assert len(public["writes"]) == 2
    assert result["status"] == "applied"
    assert result["projection"]["status"] == "ready"
    assert "# keep-this-comment" in components_path.read_text(encoding="utf-8")
    components = yaml.safe_load(components_path.read_text(encoding="utf-8"))["components"]
    assert components[0]["key"] == "worker"
    runtime = yaml.safe_load((root / ".maw/app-runtime.yaml").read_text(encoding="utf-8"))
    assert runtime["app_runtime"]["apps"]["worker"]["component_ref"] == "worker"
    assert list((root / ".maw/changes").glob("seed-change-*.yaml"))


def test_local_scope_requires_ignored_canonical_overlay(tmp_path: Path) -> None:
    root = tmp_path / "project"
    materialize_project(root, project_key="demo", name="Demo", profile="service")
    _git_init(root)
    projection = compile_project_definition(root)
    payload = {
        "schema": "mawflow.seed_change_set.v2",
        "base_projection_fingerprint": projection["fingerprint"],
        "operations": [{
            "op": "runtime.app.upsert",
            "key": "server",
            "scope": "local",
            "values": {"local_url": "http://127.0.0.1:18080", "database_ref": "database/local"},
        }],
    }

    public, private = plan_change_set(root, payload)
    result = apply_change_plan(root, private, public["confirmation_required"], backup_root=tmp_path / "backups")

    local_path = root / ".local/.maw/app-runtime.yaml"
    assert local_path.is_file()
    assert result["projection"]["configs"][".maw/app-runtime.yaml"]["app_runtime"]["apps"]["server"]["local_url"] == "http://127.0.0.1:18080"
    assert subprocess.run(["git", "-C", str(root), "check-ignore", "--quiet", ".local/.maw/app-runtime.yaml"], check=False).returncode == 0


def test_migration_normalizes_legacy_project_and_moves_local_overlay(tmp_path: Path) -> None:
    root = tmp_path / "legacy"
    (root / ".maw").mkdir(parents=True)
    (root / ".maw/project.yaml").write_text("project:\n  project:\n    project_key: legacy-demo\n    name: Legacy Demo\n", encoding="utf-8")
    (root / ".maw/app-runtime.local.yaml").write_text("app_runtime:\n  apps: {}\n", encoding="utf-8")
    _git_init(root)

    public, private = plan_migration(root, profile="minimal")
    result = apply_migration_plan(root, private, public["confirmation_required"], backup_root=tmp_path / "backups")

    assert result["projection"]["status"] == "ready"
    assert result["projection"]["project"]["key"] == "legacy-demo"
    assert not (root / ".maw/app-runtime.local.yaml").exists()
    assert (root / ".local/.maw/app-runtime.yaml").is_file()
    assert ".local/" in (root / ".gitignore").read_text(encoding="utf-8").splitlines()


def test_compiler_rejects_catalog_value_drift(tmp_path: Path) -> None:
    root = tmp_path / "project"
    materialize_project(root, project_key="demo", name="Demo", profile="minimal")
    project_path = root / ".maw/project.yaml"
    project_path.write_text(
        project_path.read_text(encoding="utf-8").replace("repository_mode: internal_only", "repository_mode: copied_everywhere"),
        encoding="utf-8",
    )

    projection = compile_project_definition(root)

    assert projection["status"] == "needs_attention"
    assert projection["editable"] is False
    assert "seed_field_value_invalid" in {issue["code"] for issue in projection["issues"]}


def test_change_set_rejects_authenticated_url_and_unknown_permissions(tmp_path: Path) -> None:
    root = tmp_path / "project"
    materialize_project(root, project_key="demo", name="Demo", profile="service")
    _git_init(root)
    projection = compile_project_definition(root)
    payload = {
        "schema": "mawflow.seed_change_set.v2",
        "base_projection_fingerprint": projection["fingerprint"],
        "operations": [{
            "op": "runtime.app.upsert",
            "key": "server",
            "scope": "local",
            "values": {"local_url": "http://user:password@127.0.0.1:8080"},
        }],
    }

    with pytest.raises(ValueError, match="seed_change_invalid_url"):
        plan_change_set(root, payload)

    payload["operations"][0]["op"] = "repository.file.write"
    with pytest.raises(ValueError, match="seed_change_operation_forbidden"):
        plan_change_set(root, payload)


def test_multi_file_change_conflict_leaves_zero_partial_writes(tmp_path: Path) -> None:
    root = tmp_path / "project"
    materialize_project(root, project_key="demo", name="Demo", profile="minimal")
    _git_init(root)
    projection = compile_project_definition(root)
    payload = {
        "schema": "mawflow.seed_change_set.v2",
        "base_projection_fingerprint": projection["fingerprint"],
        "operations": [
            {
                "op": "component.add",
                "key": "worker",
                "scope": "shared",
                "values": {
                    "app_key": "worker", "name": "Worker", "type": "worker", "path": "code/worker",
                    "enabled": True,
                },
            },
            {
                "op": "runtime.app.upsert",
                "key": "worker",
                "scope": "shared",
                "values": {"enabled": True, "component_ref": "worker", "code_path": "code/worker"},
            },
        ],
    }
    public, private = plan_change_set(root, payload)
    components_path = root / ".maw/components.yaml"
    components_path.write_text(components_path.read_text(encoding="utf-8") + "# concurrent edit\n", encoding="utf-8")
    runtime_before = (root / ".maw/app-runtime.yaml").read_text(encoding="utf-8")

    with pytest.raises(ValueError, match="seed_change_(projection|config)_conflict"):
        apply_change_plan(root, private, public["confirmation_required"], backup_root=tmp_path / "backups")

    assert "worker" not in {
        item["key"] for item in yaml.safe_load(components_path.read_text(encoding="utf-8"))["components"]
    }
    assert (root / ".maw/app-runtime.yaml").read_text(encoding="utf-8") == runtime_before


@pytest.mark.parametrize(
    ("profile", "runtime_mode", "component_keys"),
    [
        ("minimal", "host", set()),
        ("service", "container", {"server"}),
        ("web-api", "container", {"server", "client"}),
    ],
)
def test_seed_21_profiles_compile(
    tmp_path: Path,
    profile: str,
    runtime_mode: str,
    component_keys: set[str],
) -> None:
    root = tmp_path / profile
    materialize_project(root, project_key=f"{profile}-demo", name=profile, profile=profile)

    projection = compile_project_definition(root)

    assert projection["status"] == "ready"
    assert projection["configs"][".maw/technology.yaml"]["technology"]["runtime_mode"] == runtime_mode
    assert {
        item["key"] for item in projection["configs"][".maw/components.yaml"]["components"]
    } == component_keys


def test_change_set_updates_technology_and_credential_requirements(tmp_path: Path) -> None:
    root = tmp_path / "project"
    materialize_project(root, project_key="demo", name="Demo", profile="minimal")
    _git_init(root)
    projection = compile_project_definition(root)
    payload = {
        "schema": "mawflow.seed_change_set.v2",
        "base_projection_fingerprint": projection["fingerprint"],
        "base_contract_fingerprint": contract_fingerprint(),
        "reason": "补齐本地开发环境和项目凭证需求",
        "operations": [
            {
                "op": "technology.update",
                "scope": "shared",
                "values": {
                    "runtime_mode": "container",
                    "development_environment.standard": "docker_compose",
                    "development_environment.compose_files": ["compose.dev.yml"],
                    "development_environment.devcontainer": "optional",
                },
            },
            {
                "op": "technology.language.add",
                "key": "python",
                "scope": "shared",
                "values": {
                    "version": ">=3.11",
                    "package_manager": "uv",
                    "role": "server",
                    "required": True,
                },
            },
            {
                "op": "credential.requirement.add",
                "key": "database-local",
                "scope": "shared",
                "values": {
                    "name": "本地数据库",
                    "credential_type": "database",
                    "required": True,
                    "credential_class": "project",
                    "subject_scope": "project",
                    "storage_location": "host",
                    "environments": ["local"],
                    "required_fields": ["username", "password"],
                    "allowed_use_modes": ["runtime"],
                    "host_authorization_required": False,
                },
            },
        ],
    }

    public, private = plan_change_set(root, payload)
    result = apply_change_plan(root, private, public["confirmation_required"], backup_root=tmp_path / "backups")

    assert result["projection"]["status"] == "ready"
    technology = yaml.safe_load((root / ".maw/technology.yaml").read_text(encoding="utf-8"))["technology"]
    assert technology["runtime_mode"] == "container"
    assert technology["languages"][0]["key"] == "python"
    requirements = yaml.safe_load((root / ".maw/project.yaml").read_text(encoding="utf-8"))["credentials"]["requirements"]
    assert requirements[0]["key"] == "database-local"


def test_migration_round_trip_preserves_existing_project_facts(tmp_path: Path) -> None:
    root = tmp_path / "legacy"
    materialize_project(root, project_key="legacy", name="Legacy", profile="minimal")
    original_project = {
        "schema_version": 1,
        "project": {
            "key": "legacy",
            "name": "Legacy",
            "description": "保留现有业务项目事实",
            "owner": "delivery-team",
            "type": "business_project",
            "repository_mode": "internal_only",
            "default_branch": "main",
            "timezone": "Asia/Shanghai",
        },
    }
    original_environments = {
        "schema_version": 1,
        "environments": {
            "local": {
                "profile": "local",
                "description": "保留本地自定义配置",
                "remote_required": False,
                "custom_existing_field": "keep-me",
            },
            "test": {
                "profile": "test",
                "description": "兼容旧测试别名",
                "remote_required": True,
            },
        },
    }
    (root / ".maw/project.yaml").write_text(
        yaml.safe_dump(original_project, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    (root / ".maw/environments.yaml").write_text(
        yaml.safe_dump(original_environments, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    (root / ".maw/technology.yaml").unlink()
    for path in sorted((root / "docs/handbooks").rglob("*"), key=lambda item: len(item.parts), reverse=True):
        path.unlink() if path.is_file() else path.rmdir()
    (root / "docs/handbooks").rmdir()
    (root / "compose.dev.yml").write_text("services: {}\n", encoding="utf-8")
    _git_init(root)
    original_environment_text = (root / ".maw/environments.yaml").read_text(encoding="utf-8")
    original_project_text = (root / ".maw/project.yaml").read_text(encoding="utf-8")

    public, private = plan_migration(root, profile="minimal")
    backup_root = tmp_path / "backups"
    applied = apply_migration_plan(
        root,
        private,
        public["confirmation_required"],
        backup_root=backup_root,
    )

    assert applied["projection"]["status"] == "ready"
    migrated_environments = yaml.safe_load((root / ".maw/environments.yaml").read_text(encoding="utf-8"))
    assert migrated_environments["environments"]["local"]["custom_existing_field"] == "keep-me"
    assert {"local", "test", "staging", "production"} <= set(migrated_environments["environments"])
    assert (root / "compose.dev.yml").read_text(encoding="utf-8") == "services: {}\n"
    assert (root / "docs/handbooks/manifest.yaml").is_file()

    rolled_back = rollback_migration(
        root,
        plan_key=applied["plan_key"],
        confirmation=applied["rollback_confirmation"],
        backup_root=backup_root,
    )

    assert rolled_back["status"] == "rolled_back"
    assert not (root / ".maw/technology.yaml").exists()
    assert not (root / "docs/handbooks/manifest.yaml").exists()
    assert (root / ".maw/environments.yaml").read_text(encoding="utf-8") == original_environment_text
    assert (root / ".maw/project.yaml").read_text(encoding="utf-8") == original_project_text
