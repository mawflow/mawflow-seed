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
    apply_component_plan,
    apply_migration_plan,
    compile_project_definition,
    materialize_project,
    plan_change_set,
    plan_component_init,
    plan_component_state,
    inspect_components,
    plan_contract_repair,
    plan_migration,
    rollback_migration,
)
from mawflow_seed_kit.catalog import (  # noqa: E402
    SEED_VERSION,
    contract_fingerprint,
    public_catalog,
)


def _git_init(root: Path) -> None:
    subprocess.run(["git", "init", "-q", str(root)], check=True)


def test_materialized_project_is_complete_and_editable(tmp_path: Path) -> None:
    root = tmp_path / "project"
    result = materialize_project(root, project_key="demo-project", name="演示项目", profile="blank")
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
    assert projection["configs"][".maw/technology.yaml"]["technology"]["runtime_mode"] == "host"
    assert len(projection["configs"]["docs/handbooks/manifest.yaml"]["handbook_system"]["volumes"]) == 6
    assert projection["configs"][".maw/app-runtime.yaml"]["app_runtime"]["apps"] == {}
    assert projection["configs"][".maw/components.yaml"]["components"] == []
    for source_ref in ("code/README.md", "docs/README.md", "MAWFLOW_CLI.md", "PROJECT_COMMANDS.md", "CHATGPT_TO_AI.md"):
        assert (root / source_ref).is_file()
    assert public_catalog()["trust_boundary"]["arbitrary_paths_writable"] is False


def test_component_init_enable_disable_and_inspect(tmp_path: Path) -> None:
    root = tmp_path / "project"
    materialize_project(root, project_key="demo", name="Demo", profile="blank")
    _git_init(root)

    public, private = plan_component_init(
        root,
        key="api",
        component_type="backend",
        name="业务 API",
    )
    result = apply_component_plan(
        root,
        private,
        public["confirmation_required"],
        backup_root=tmp_path / "backups",
    )

    assert result["status"] == "applied"
    assert (root / "code/api/README.md").is_file()
    descriptor = yaml.safe_load((root / "code/api/.maw.component.yaml").read_text(encoding="utf-8"))
    assert descriptor["component"]["key"] == "api"
    inspection = inspect_components(root, "api")
    assert inspection["status"] == "ready"
    components = yaml.safe_load((root / ".maw/components.yaml").read_text(encoding="utf-8"))["components"]
    assert components[0]["enabled"] is False

    public, private = plan_component_state(root, key="api", enabled=True)
    apply_component_plan(root, private, public["confirmation_required"], backup_root=tmp_path / "backups")
    components = yaml.safe_load((root / ".maw/components.yaml").read_text(encoding="utf-8"))["components"]
    assert components[0]["enabled"] is True

    public, private = plan_component_state(root, key="api", enabled=False)
    apply_component_plan(root, private, public["confirmation_required"], backup_root=tmp_path / "backups")
    components = yaml.safe_load((root / ".maw/components.yaml").read_text(encoding="utf-8"))["components"]
    assert components[0]["enabled"] is False
    assert (root / "code/api").is_dir()


def test_component_adopt_preserves_existing_source(tmp_path: Path) -> None:
    root = tmp_path / "project"
    materialize_project(root, project_key="demo", name="Demo", profile="blank")
    _git_init(root)
    legacy = root / "code/legacy"
    legacy.mkdir()
    readme = legacy / "README.md"
    readme.write_text("# existing\n", encoding="utf-8")
    source = legacy / "main.py"
    source.write_text("print('existing')\n", encoding="utf-8")

    public, private = plan_component_init(
        root,
        key="legacy",
        component_type="custom",
        path="code/legacy",
        adopt=True,
    )
    apply_component_plan(root, private, public["confirmation_required"], backup_root=tmp_path / "backups")

    assert readme.read_text(encoding="utf-8") == "# existing\n"
    assert source.read_text(encoding="utf-8") == "print('existing')\n"
    assert (legacy / ".maw.component.yaml").is_file()


@pytest.mark.parametrize("path", ["server", "../server", "/tmp/server", "code"])
def test_component_init_rejects_paths_outside_component_boundary(tmp_path: Path, path: str) -> None:
    root = tmp_path / "project"
    materialize_project(root, project_key="demo", name="Demo", profile="blank")

    with pytest.raises(ValueError, match="seed_component_path_must_be_under_code"):
        plan_component_init(root, key="api", component_type="backend", path=path)


def test_current_seed_contract_repair_normalizes_legacy_technology(
    tmp_path: Path,
) -> None:
    root = tmp_path / "project"
    materialize_project(
        root, project_key="demo-project", name="演示项目", profile="web-api"
    )
    _git_init(root)
    technology_path = root / ".maw/technology.yaml"
    technology_path.write_text(
        """schema_version: 2
technology:
  runtime_mode: container
  languages:
    - key: maven
      role: build_tool
      required: true
  frameworks:
    - key: spring-boot
      version: "3.5"
      required: true
    - key: vue
      version: "3"
      required: true
    - key: vite
      version: "5"
      required: true
  services:
    - key: redis
      version: "7"
      required: false
    - key: mysql
      version: "8"
      required: false
  development_environment:
    standard: docker_compose
    compose_files: []
    devcontainer: optional
  verification:
    commands: []
# keep-this-project-comment
""",
        encoding="utf-8",
    )
    invalid = compile_project_definition(root)

    assert invalid["status"] == "needs_attention"
    assert invalid["summary"]["errors"] == 8
    public, private = plan_contract_repair(root)
    result = apply_change_plan(
        root,
        private,
        public["confirmation_required"],
        backup_root=tmp_path / "backups",
    )

    assert public["repair"]["mode"] == "deterministic_current_version"
    assert public["repair"]["issue_count"] == 8
    assert len(public["operations"]) == 6
    assert result["projection"]["status"] == "ready"
    repaired_text = technology_path.read_text(encoding="utf-8")
    assert "# keep-this-project-comment" in repaired_text
    technology = yaml.safe_load(repaired_text)["technology"]
    assert technology["languages"][0]["role"] == "tooling"
    assert [item["name"] for item in technology["frameworks"]] == [
        "spring-boot",
        "vue",
        "vite",
    ]
    assert [(item["type"], item["provision"]) for item in technology["services"]] == [
        ("redis", "docker"),
        ("mysql", "docker"),
    ]


def test_contract_repair_refuses_project_seed_version_mismatch(
    tmp_path: Path,
) -> None:
    root = tmp_path / "project"
    materialize_project(root, project_key="demo", name="Demo", profile="web-api")
    lock_path = root / ".maw/seed.lock"
    lock = yaml.safe_load(lock_path.read_text(encoding="utf-8"))
    lock["seed_version"] = "2.0.0"
    lock_path.write_text(
        yaml.safe_dump(lock, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    technology_path = root / ".maw/technology.yaml"
    technology = yaml.safe_load(technology_path.read_text(encoding="utf-8"))
    technology["technology"]["frameworks"] = [
        {"key": "demo-framework", "required": True}
    ]
    technology_path.write_text(
        yaml.safe_dump(technology, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="seed_repair_version_mismatch"):
        plan_contract_repair(root)


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


def test_project_change_set_updates_nested_project_fields(tmp_path: Path) -> None:
    root = tmp_path / "project"
    materialize_project(root, project_key="demo", name="Demo", profile="minimal")
    _git_init(root)
    projection = compile_project_definition(root)
    public, private = plan_change_set(
        root,
        {
            "schema": "mawflow.seed_change_set.v2",
            "base_projection_fingerprint": projection["fingerprint"],
            "operations": [
                {
                    "op": "project.update",
                    "scope": "shared",
                    "values": {
                        "classification.delivery_mode": "existing_evolution",
                        "classification.requirement_maturity": "partial",
                        "classification.onboarding_status": "confirmed",
                        "objective.value_statement": "真实项目演进目标",
                        "objective.primary_users": ["教师", "学员"],
                        "objective.success_metrics": ["真实旅程通过"],
                    },
                }
            ],
        },
    )
    result = apply_change_plan(
        root,
        private,
        public["confirmation_required"],
        backup_root=tmp_path / "backups",
    )

    assert result["projection"]["project"]["classification"]["delivery_mode"] == "existing_evolution"
    assert result["projection"]["project"]["classification"]["onboarding_status"] == "confirmed"
    assert result["projection"]["project"]["objective"]["primary_users"] == ["教师", "学员"]
    project = yaml.safe_load((root / ".maw/project.yaml").read_text(encoding="utf-8"))["project"]
    assert "classification.delivery_mode" not in project


def test_module_update_preserves_following_sequence_item_indentation(
    tmp_path: Path,
) -> None:
    root = tmp_path / "project"
    materialize_project(
        root, project_key="demo", name="Demo", profile="web-api"
    )
    modules_path = root / ".maw/modules.yaml"
    modules_path.write_text(
        """schema_version: 2
modules:
  - key: server-module
    name: 服务端
    type: component
    status: active
    doc_status: pending_confirm
    confidence: low
    component_refs: []
  - key: client-module
    name: 客户端
    type: component
    status: active
    doc_status: pending_confirm
    confidence: low
    component_refs: []
""",
        encoding="utf-8",
    )
    modules = yaml.safe_load(modules_path.read_text(encoding="utf-8"))
    first = modules["modules"][0]
    first.pop("last_verified_at", None)
    first.pop("last_verified_by", None)
    modules_path.write_text(
        yaml.safe_dump(modules, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    _git_init(root)
    projection = compile_project_definition(root)

    public, private = plan_change_set(
        root,
        {
            "schema": "mawflow.seed_change_set.v2",
            "base_projection_fingerprint": projection["fingerprint"],
            "operations": [
                {
                    "op": "module.update",
                    "key": first["key"],
                    "scope": "shared",
                    "values": {
                        "doc_status": "confirmed",
                        "confidence": "high",
                        "last_verified_at": "2026-07-26",
                        "last_verified_by": "human",
                    },
                }
            ],
        },
    )
    apply_change_plan(
        root,
        private,
        public["confirmation_required"],
        backup_root=tmp_path / "backups",
    )

    migrated = yaml.safe_load(modules_path.read_text(encoding="utf-8"))
    assert migrated["modules"][0]["last_verified_by"] == "human"
    assert migrated["modules"][1]["key"] == modules["modules"][1]["key"]


def test_local_scope_requires_ignored_canonical_overlay(tmp_path: Path) -> None:
    root = tmp_path / "project"
    materialize_project(root, project_key="demo", name="Demo", profile="service")
    _git_init(root)
    component_public, component_private = plan_component_init(
        root, key="server", component_type="backend"
    )
    apply_component_plan(
        root,
        component_private,
        component_public["confirmation_required"],
        backup_root=tmp_path / "backups",
    )
    projection = compile_project_definition(root)
    runtime_public, runtime_private = plan_change_set(
        root,
        {
            "schema": "mawflow.seed_change_set.v2",
            "base_projection_fingerprint": projection["fingerprint"],
            "operations": [{
                "op": "runtime.app.upsert",
                "key": "server",
                "scope": "shared",
                "values": {
                    "app_key": "server",
                    "enabled": False,
                    "component_ref": "server",
                    "code_path": "code/server",
                },
            }],
        },
    )
    apply_change_plan(
        root,
        runtime_private,
        runtime_public["confirmation_required"],
        backup_root=tmp_path / "backups",
    )
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


def test_migration_advances_package_template_source_without_losing_project_text(
    tmp_path: Path,
) -> None:
    root = tmp_path / "legacy"
    materialize_project(root, project_key="legacy", name="Legacy", profile="blank")
    template_source_path = root / ".maw/template-source.yaml"
    template_source_path.write_text(
        """# 项目自己的 Seed 来源说明
schema_version: 2
template_source:
  kind: package
  package: mawflow-seed-kit
  applied_version: 2.2.1 # 上次已应用版本
  project_extension: keep-me
  distribution:
    kind: package
    package: mawflow-seed-kit
    version: 2.2.1
""",
        encoding="utf-8",
    )
    (root / ".maw/seed.lock").write_text(
        (root / ".maw/seed.lock").read_text(encoding="utf-8").replace(
            SEED_VERSION, "2.2.1"
        ),
        encoding="utf-8",
    )
    _git_init(root)

    public, private = plan_migration(root, profile="blank")
    result = apply_migration_plan(
        root,
        private,
        public["confirmation_required"],
        backup_root=tmp_path / "backups",
    )

    assert result["projection"]["status"] == "ready"
    migrated_text = template_source_path.read_text(encoding="utf-8")
    migrated = yaml.safe_load(migrated_text)["template_source"]
    assert migrated["applied_version"] == SEED_VERSION
    assert migrated["distribution"]["version"] == SEED_VERSION
    assert migrated["project_extension"] == "keep-me"
    assert "# 项目自己的 Seed 来源说明" in migrated_text
    assert "# 上次已应用版本" in migrated_text
    assert ".maw/template-source.yaml" not in public["migration_safety"][
        "protected_existing_paths"
    ]


def test_migration_preserves_non_package_template_source(tmp_path: Path) -> None:
    root = tmp_path / "legacy"
    materialize_project(root, project_key="legacy", name="Legacy", profile="blank")
    template_source_path = root / ".maw/template-source.yaml"
    original = """schema_version: 2
template_source:
  kind: git
  git_url: https://example.invalid/seed.git
  applied_version: abc123
"""
    template_source_path.write_text(original, encoding="utf-8")
    (root / ".maw/seed.lock").write_text(
        (root / ".maw/seed.lock").read_text(encoding="utf-8").replace(
            SEED_VERSION, "2.2.1"
        ),
        encoding="utf-8",
    )
    _git_init(root)

    public, private = plan_migration(root, profile="blank")
    apply_migration_plan(
        root,
        private,
        public["confirmation_required"],
        backup_root=tmp_path / "backups",
    )

    assert template_source_path.read_text(encoding="utf-8") == original


@pytest.mark.parametrize("directory_name", ["empty-project", "新 项目"])
def test_migration_bootstraps_repository_without_existing_project_contract(
    tmp_path: Path, directory_name: str
) -> None:
    root = tmp_path / directory_name
    root.mkdir()
    _git_init(root)

    public, private = plan_migration(
        root, profile="minimal", initialization_mode="empty_repository"
    )
    result = apply_migration_plan(
        root,
        private,
        public["confirmation_required"],
        backup_root=tmp_path / "backups",
    )

    assert result["projection"]["status"] == "ready"
    assert result["projection"]["project"]["key"] in {
        "empty-project",
        "mawflow-project",
    }
    assert (
        result["projection"]["project"]["classification"]["delivery_mode"]
        == "new_defined"
    )
    assert public["initialization_mode"] == "empty_repository"
    lock = yaml.safe_load((root / ".maw" / "seed.lock").read_text(encoding="utf-8"))
    assert lock["source"] == {
        "kind": "project_init",
        "from": "empty_repository",
    }
    assert (root / ".maw" / "seed.lock").is_file()


def test_migration_preserves_business_readme_private_docs_and_repairs_modules(
    tmp_path: Path,
) -> None:
    root = tmp_path / "legacy"
    materialize_project(root, project_key="learning", name="AI Learning Engine", profile="web-api")
    readme = root / "README.md"
    private_doc = root / "docs/handbooks/requirements/README.md"
    project_path = root / ".maw/project.yaml"
    components_path = root / ".maw/components.yaml"
    readme.write_text("# AI Learning Engine\n\n真实业务事实\n", encoding="utf-8")
    private_doc.write_text("# 私有需求手册\n\n不得覆盖\n", encoding="utf-8")
    project_payload = yaml.safe_load(project_path.read_text(encoding="utf-8"))
    project_payload.pop("schema_version", None)
    project_original = (
        "# 项目自己的定义注释\n"
        + yaml.safe_dump(project_payload, allow_unicode=True, sort_keys=False)
    )
    project_path.write_text(project_original, encoding="utf-8")
    components_payload = yaml.safe_load(components_path.read_text(encoding="utf-8"))
    components_payload.pop("schema_version", None)
    components_original = (
        "# 项目自己的组件注释\n"
        + yaml.safe_dump(components_payload, allow_unicode=True, sort_keys=False)
    )
    components_path.write_text(components_original, encoding="utf-8")
    technology_path = root / ".maw/technology.yaml"
    technology_path.write_text(
        """# 保留技术栈注释
schema_version: 1
technology:
  runtime_mode: container
  languages:
    - key: maven
      role: build_tool
      required: true
  frameworks:
    - key: spring-boot
      version: "3.5"
      required: true
  services:
    - key: mysql
      version: "8"
      required: false
  development_environment:
    standard: docker_compose
    compose_files: [compose.dev.yml]
    devcontainer: optional
  verification:
    commands: []
""",
        encoding="utf-8",
    )
    modules_path = root / ".maw/modules.yaml"
    modules_path.write_text(
        """# 真实模块事实
schema_version: 2
modules:
  - key: server
    name: 服务端
    type: component
    status: active
    private_extension:
      owner: learning-team
  - key: client
    name: 客户端
    type: component
    status: active
    doc_status: confirmed
    confidence: high
""",
        encoding="utf-8",
    )
    _git_init(root)

    public, private = plan_migration(root, profile="web-api")
    result = apply_migration_plan(
        root,
        private,
        public["confirmation_required"],
        backup_root=tmp_path / "backups",
    )

    assert result["projection"]["status"] == "ready"
    assert readme.read_text(encoding="utf-8") == "# AI Learning Engine\n\n真实业务事实\n"
    assert private_doc.read_text(encoding="utf-8") == "# 私有需求手册\n\n不得覆盖\n"
    assert public["migration_safety"]["business_readme_preserved"] is True
    assert public["migration_safety"]["project_owned_yaml_text_preserved"] is True
    assert "README.md" in public["migration_safety"]["protected_existing_paths"]
    assert project_path.read_text(encoding="utf-8") == (
        project_original + "schema_version: 2\n"
    )
    assert components_path.read_text(encoding="utf-8") == (
        components_original + "schema_version: 2\n"
    )
    migrated = yaml.safe_load(modules_path.read_text(encoding="utf-8"))
    assert migrated["modules"][0]["doc_status"] == "pending_confirm"
    assert migrated["modules"][0]["confidence"] == "low"
    assert migrated["modules"][0]["private_extension"] == {"owner": "learning-team"}
    assert migrated["modules"][1]["doc_status"] == "confirmed"
    migrated_technology_text = technology_path.read_text(encoding="utf-8")
    assert "# 保留技术栈注释" in migrated_technology_text
    migrated_technology = yaml.safe_load(migrated_technology_text)["technology"]
    assert migrated_technology["languages"][0]["role"] == "tooling"
    assert migrated_technology["frameworks"][0]["name"] == "spring-boot"
    assert migrated_technology["services"][0]["type"] == "mysql"
    assert migrated_technology["services"][0]["provision"] == "docker"
    assert public["migration_safety"]["technology_field_normalizations"]


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
        ("blank", "host", set()),
        ("minimal", "host", set()),
        ("service", "host", set()),
        ("web-api", "host", set()),
    ],
)
def test_seed_23_profiles_compile_without_implicit_components(
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
                    "verification.commands": ["npm run app:test"],
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
    assert technology["verification"]["commands"] == ["npm run app:test"]
    assert technology["languages"][0]["key"] == "python"
    requirements = yaml.safe_load((root / ".maw/project.yaml").read_text(encoding="utf-8"))["credentials"]["requirements"]
    assert requirements[0]["key"] == "database-local"


def test_change_set_appends_to_existing_indentless_technology_sequence(
    tmp_path: Path,
) -> None:
    root = tmp_path / "project"
    materialize_project(root, project_key="demo", name="Demo", profile="web-api")
    _git_init(root)
    projection = compile_project_definition(root)

    public, private = plan_change_set(
        root,
        {
            "schema": "mawflow.seed_change_set.v2",
            "base_projection_fingerprint": projection["fingerprint"],
            "base_contract_fingerprint": contract_fingerprint(),
            "reason": "补齐真实工具链",
            "operations": [
                {
                    "op": "technology.language.add",
                    "key": "python",
                    "scope": "shared",
                    "values": {
                        "version": ">=3.10",
                        "package_manager": "pip",
                        "role": "server",
                        "required": True,
                    },
                }
            ],
        },
    )
    result = apply_change_plan(
        root,
        private,
        public["confirmation_required"],
        backup_root=tmp_path / "backups",
    )

    assert result["projection"]["status"] == "ready"
    technology = yaml.safe_load(
        (root / ".maw/technology.yaml").read_text(encoding="utf-8")
    )["technology"]
    assert [item["key"] for item in technology["languages"]] == ["python"]


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
    assert set(migrated_environments["environments"]) == {"local", "test"}
    assert migrated_environments["environments"]["local"]["custom_existing_field"] == "keep-me"
    assert migrated_environments["environments"]["test"]["description"] == "兼容旧测试别名"
    assert migrated_environments["environments"]["test"]["profile"] == "local"
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
