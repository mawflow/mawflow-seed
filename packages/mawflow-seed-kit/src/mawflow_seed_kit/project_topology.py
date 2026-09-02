from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import re
from typing import Any

from .catalog import contract_fingerprint
from .changes import apply_change_plan, plan_change_set
from .compiler import compile_project_definition
from .components import (
    KEY_PATTERN,
    _git_output,
    _repository_identity,
    _validate_external_directory,
)


def _root(root: Path | str) -> Path:
    project_root = Path(root).expanduser().resolve(strict=True)
    if not (project_root / ".maw/project.yaml").is_file():
        raise ValueError("seed_project_required")
    return project_root


def _key(value: str, code: str) -> str:
    key = value.strip()
    if not KEY_PATTERN.fullmatch(key):
        raise ValueError(code)
    return key


def _configs(projection: dict[str, Any], source_ref: str, root_key: str) -> Any:
    return projection.get("configs", {}).get(source_ref, {}).get(root_key)


def _code_sources(projection: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw = _configs(projection, ".maw/code-sources.yaml", "code_sources")
    return {
        str(key): dict(value)
        for key, value in raw.items()
        if isinstance(value, dict)
    } if isinstance(raw, dict) else {}


def _code_source_bindings(projection: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw = _configs(projection, ".maw/code-source-bindings.yaml", "code_source_bindings")
    return {
        str(key): dict(value)
        for key, value in raw.items()
        if isinstance(value, dict)
    } if isinstance(raw, dict) else {}


def _legacy_bindings(projection: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw = _configs(projection, ".maw/component-sources.yaml", "component_sources")
    return {
        str(key): dict(value)
        for key, value in raw.items()
        if isinstance(value, dict)
    } if isinstance(raw, dict) else {}


def _components(projection: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw = _configs(projection, ".maw/components.yaml", "components")
    return {
        str(item.get("key")): dict(item)
        for item in raw
        if isinstance(item, dict) and item.get("key")
    } if isinstance(raw, list) else {}


def _deployment_targets(projection: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw = _configs(projection, ".maw/deployments.yaml", "deployment_targets")
    return {
        str(item.get("key")): dict(item)
        for item in raw
        if isinstance(item, dict) and item.get("key")
    } if isinstance(raw, list) else {}


def _change(
    root: Path,
    projection: dict[str, Any],
    operations: list[dict[str, Any]],
    reason: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    return plan_change_set(
        root,
        {
            "schema": "mawflow.seed_change_set.v2",
            "base_projection_fingerprint": projection["fingerprint"],
            "base_contract_fingerprint": contract_fingerprint(),
            "reason": reason,
            "operations": operations,
        },
    )


def default_managed_clone_path(root: Path | str, source_key: str) -> Path:
    project_root = _root(root)
    key = _key(source_key, "seed_code_source_key_invalid")
    return project_root / ".local" / "code-sources" / key


def plan_subproject_upsert(
    root: Path | str,
    *,
    key: str,
    name: str,
    description: str = "",
    status: str = "active",
    grouping_basis: str = "standalone",
    customer_ref: str = "",
    deployment_group_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any]]:
    project_root = _root(root)
    projection = compile_project_definition(project_root)
    subproject_key = _key(key, "seed_subproject_key_invalid")
    existing = _configs(projection, ".maw/subprojects.yaml", "subprojects")
    existing_keys = {
        str(item.get("key")) for item in existing if isinstance(item, dict)
    } if isinstance(existing, list) else set()
    operation = "subproject.update" if subproject_key in existing_keys else "subproject.add"
    return _change(
        project_root,
        projection,
        [{
            "op": operation,
            "key": subproject_key,
            "scope": "shared",
            "values": {
                "name": name.strip() or subproject_key,
                "description": description.strip(),
                "status": status,
                "grouping_basis": grouping_basis,
                "customer_ref": customer_ref.strip(),
                "deployment_group_ref": deployment_group_ref.strip(),
            },
        }],
        f"{'更新' if operation.endswith('update') else '新增'}子项目 {subproject_key}",
    )


def plan_subproject_remove(root: Path | str, *, key: str) -> tuple[dict[str, Any], dict[str, Any]]:
    project_root = _root(root)
    projection = compile_project_definition(project_root)
    subproject_key = _key(key, "seed_subproject_key_invalid")
    if subproject_key == "default":
        raise ValueError("seed_default_subproject_remove_forbidden")
    if any(
        str(component.get("subproject_ref") or "default") == subproject_key
        for component in _components(projection).values()
    ):
        raise ValueError("seed_subproject_referenced_by_component")
    return _change(
        project_root,
        projection,
        [{"op": "subproject.remove", "key": subproject_key, "scope": "shared", "values": {}}],
        f"移除空子项目 {subproject_key}",
    )


def plan_code_source_upsert(
    root: Path | str,
    *,
    key: str,
    repository_url: str,
    name: str = "",
    default_branch: str = "",
    visibility: str = "private",
    credential_requirement_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any]]:
    project_root = _root(root)
    projection = compile_project_definition(project_root)
    source_key = _key(key, "seed_code_source_key_invalid")
    _repository_identity(repository_url)
    for existing_key, source in _code_sources(projection).items():
        if existing_key != source_key and _repository_identity(str(source.get("repository_url") or "")) == _repository_identity(repository_url):
            raise ValueError("seed_code_source_repository_duplicate")
    return _change(
        project_root,
        projection,
        [{
            "op": "code_source.upsert",
            "key": source_key,
            "scope": "shared",
            "values": {
                "name": name.strip() or source_key,
                "type": "git",
                "repository_url": repository_url.strip(),
                "default_branch": default_branch.strip(),
                "visibility": visibility,
                "credential_requirement_ref": credential_requirement_ref.strip(),
            },
        }],
        f"登记或更新共享代码源 {source_key}",
    )


def plan_code_source_binding(
    root: Path | str,
    *,
    key: str,
    directory_path: Path | str,
    git_access_profile_ref: str = "",
    origin: str = "existing_directory",
) -> tuple[dict[str, Any], dict[str, Any]]:
    project_root = _root(root)
    projection = compile_project_definition(project_root)
    source_key = _key(key, "seed_code_source_key_invalid")
    source = _code_sources(projection).get(source_key)
    if source is None:
        raise ValueError("seed_code_source_missing")
    if origin not in {"existing_directory", "managed_clone"}:
        raise ValueError("seed_code_source_origin_invalid")
    directory, identity = _validate_external_directory(
        directory_path,
        repository_url=str(source.get("repository_url") or ""),
        project_root=project_root,
    )
    return _change(
        project_root,
        projection,
        [{
            "op": "code_source_binding.upsert",
            "key": source_key,
            "scope": "local",
            "values": {
                "source_ref": f"mawsource://code-source/{source_key}",
                "directory_path": str(directory),
                "origin": origin,
                "git_access_profile_ref": git_access_profile_ref.strip(),
                "bound_repository_identity": identity,
                "bound_at": datetime.now(timezone.utc).isoformat(),
            },
        }],
        f"绑定共享代码源 {source_key} 的本机 Git 目录",
    )


def plan_code_source_unbind(root: Path | str, *, key: str) -> tuple[dict[str, Any], dict[str, Any]]:
    project_root = _root(root)
    projection = compile_project_definition(project_root)
    source_key = _key(key, "seed_code_source_key_invalid")
    if source_key not in _code_source_bindings(projection):
        raise ValueError("seed_code_source_binding_missing")
    return _change(
        project_root,
        projection,
        [{"op": "code_source_binding.remove", "key": source_key, "scope": "local", "values": {}}],
        f"解绑共享代码源 {source_key}，保留磁盘目录",
    )


def plan_code_source_remove(root: Path | str, *, key: str) -> tuple[dict[str, Any], dict[str, Any]]:
    project_root = _root(root)
    projection = compile_project_definition(project_root)
    source_key = _key(key, "seed_code_source_key_invalid")
    if any(
        str((component.get("source") or {}).get("repository_ref") or "") == source_key
        for component in _components(projection).values()
        if isinstance(component.get("source") or {}, dict)
    ):
        raise ValueError("seed_code_source_referenced_by_component")
    operations: list[dict[str, Any]] = []
    if source_key in _code_source_bindings(projection):
        operations.append({"op": "code_source_binding.remove", "key": source_key, "scope": "local", "values": {}})
    operations.append({"op": "code_source.remove", "key": source_key, "scope": "shared", "values": {}})
    return _change(project_root, projection, operations, f"移除共享代码源 {source_key}，保留磁盘目录")


def plan_deployment_target_upsert(
    root: Path | str,
    *,
    key: str,
    name: str,
    environment_key: str,
    environment_role: str,
    server_ref: str,
    component_refs: list[str],
    subproject_ref: str = "",
    scope_mode: str = "exclusive",
    deployment_profile_ref: str = "",
    access_profile_ref: str = "",
    enabled: bool = True,
    approval_required: bool | None = None,
    backup_required: bool = True,
    rollback_required: bool = True,
    health_freshness_seconds: int = 900,
) -> tuple[dict[str, Any], dict[str, Any]]:
    project_root = _root(root)
    projection = compile_project_definition(project_root)
    target_key = _key(key, "seed_deployment_target_key_invalid")
    if environment_role not in {"local", "staging", "production"}:
        raise ValueError("seed_deployment_target_environment_role_invalid")
    if scope_mode not in {"exclusive", "replicated"}:
        raise ValueError("seed_deployment_target_scope_mode_invalid")
    if enabled and not component_refs:
        raise ValueError("seed_deployment_target_scope_empty")
    normalized_refs = list(dict.fromkeys(_key(item, "seed_deployment_target_component_ref_invalid") for item in component_refs))
    operation = "deployment_target.update" if target_key in _deployment_targets(projection) else "deployment_target.add"
    require_approval = environment_role == "production" if approval_required is None else bool(approval_required)
    if environment_role == "production" and not require_approval:
        raise ValueError("seed_deployment_target_production_approval_required")
    return _change(
        project_root,
        projection,
        [{
            "op": operation,
            "key": target_key,
            "scope": "shared",
            "values": {
                "name": name.strip() or target_key,
                "environment_key": _key(environment_key, "seed_deployment_target_environment_key_invalid"),
                "environment_role": environment_role,
                "server_ref": server_ref.strip(),
                "subproject_ref": subproject_ref.strip(),
                "component_refs": normalized_refs,
                "scope_mode": scope_mode,
                "deployment_profile_ref": deployment_profile_ref.strip(),
                "access_profile_ref": access_profile_ref.strip(),
                "enabled": bool(enabled),
                "policy.approval_required": require_approval,
                "policy.backup_required": bool(backup_required),
                "policy.rollback_required": bool(rollback_required),
                "policy.health_freshness_seconds": int(health_freshness_seconds),
            },
        }],
        f"{'更新' if operation.endswith('update') else '新增'}部署目标 {target_key}",
    )


def plan_deployment_target_remove(root: Path | str, *, key: str) -> tuple[dict[str, Any], dict[str, Any]]:
    project_root = _root(root)
    projection = compile_project_definition(project_root)
    target_key = _key(key, "seed_deployment_target_key_invalid")
    if target_key not in _deployment_targets(projection):
        raise ValueError("seed_deployment_target_missing")
    return _change(
        project_root,
        projection,
        [{"op": "deployment_target.remove", "key": target_key, "scope": "shared", "values": {}}],
        f"移除部署目标 {target_key}；不会删除服务器资产或组件源码",
    )


def inspect_deployment_targets(root: Path | str) -> dict[str, Any]:
    project_root = _root(root)
    projection = compile_project_definition(project_root)
    components = _components(projection)
    explicit = list(_deployment_targets(projection).values())
    environments = _configs(projection, ".maw/environments.yaml", "environments")
    implicit: list[dict[str, Any]] = []
    explicitly_covered = {str(item.get("environment_key") or "") for item in explicit}
    for environment_key, environment in (environments.items() if isinstance(environments, dict) else []):
        if environment_key in explicitly_covered or not isinstance(environment, dict):
            continue
        remote = environment.get("remote_server") if isinstance(environment.get("remote_server"), dict) else {}
        component_refs = list(dict.fromkeys(str(item) for item in (remote.get("default_release_components") or []) if str(item)))
        configured = bool(component_refs or remote.get("credential_ref") or remote.get("healthcheck_url") or remote.get("port"))
        if not configured:
            continue
        role = "production" if str(environment.get("role") or "") == "production" else "staging"
        implicit.append({
            "key": f"{environment_key}-default",
            "name": f"{environment_key} 兼容部署目标",
            "environment_key": environment_key,
            "environment_role": role,
            "server_ref": f"legacy://environments/{environment_key}/remote_server",
            "subproject_ref": "",
            "component_refs": component_refs,
            "scope_mode": "exclusive",
            "enabled": True,
            "implicit_legacy": True,
            "migration_required": True,
        })
    targets = [*explicit, *implicit]
    return {
        "schema": "mawflow.deployment_targets.v2",
        "status": "ready" if not implicit else "migration_recommended",
        "deployment_targets": targets,
        "summary": {
            "explicit": len(explicit),
            "implicit_legacy": len(implicit),
            "components_scoped": len({ref for item in targets for ref in item.get("component_refs", []) if ref in components}),
        },
        "cloud_summary": {
            "deployment_targets": [
                {
                    "key": item.get("key"),
                    "name": item.get("name"),
                    "environment_key": item.get("environment_key"),
                    "environment_role": item.get("environment_role"),
                    "server_ref": item.get("server_ref"),
                    "subproject_ref": item.get("subproject_ref"),
                    "component_refs": item.get("component_refs", []),
                    "scope_mode": item.get("scope_mode"),
                    "deployment_profile_ref": item.get("deployment_profile_ref", ""),
                    "access_profile_ref": item.get("access_profile_ref", ""),
                    "enabled": item.get("enabled", True),
                }
                for item in targets
            ],
            "credential_values_included": False,
            "local_paths_included": False,
        },
    }


def _available_source_key(preferred: str, used: set[str]) -> str:
    base = re.sub(r"[^a-z0-9._-]+", "-", preferred.lower()).strip("-._") or "repository"
    candidate = base
    suffix = 2
    while candidate in used:
        candidate = f"{base}-{suffix}"
        suffix += 1
    used.add(candidate)
    return candidate


def plan_source_registry_consolidation(root: Path | str) -> tuple[dict[str, Any], dict[str, Any]]:
    project_root = _root(root)
    projection = compile_project_definition(project_root)
    components = _components(projection)
    registry = _code_sources(projection)
    identity_to_key = {
        _repository_identity(str(source.get("repository_url") or "")): key
        for key, source in registry.items()
    }
    used_keys = set(registry)
    legacy_groups: dict[str, list[tuple[str, dict[str, Any], dict[str, Any]]]] = {}
    for component_key, component in components.items():
        source = component.get("source") if isinstance(component.get("source"), dict) else {}
        if source.get("mode") != "external_git" or source.get("repository_ref"):
            continue
        identity = _repository_identity(str(source.get("repository_url") or ""))
        legacy_groups.setdefault(identity, []).append((component_key, component, source))
    if not legacy_groups:
        raise ValueError("seed_source_registry_already_consolidated")
    legacy_bindings = _legacy_bindings(projection)
    operations: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []
    migrations: list[dict[str, Any]] = []
    for identity, group in sorted(legacy_groups.items()):
        source_key = identity_to_key.get(identity)
        representative = group[0][2]
        if source_key is None:
            source_key = _available_source_key(identity.rsplit("/", 1)[-1], used_keys)
            identity_to_key[identity] = source_key
            operations.append({
                "op": "code_source.upsert",
                "key": source_key,
                "scope": "shared",
                "values": {
                    "name": source_key,
                    "type": "git",
                    "repository_url": str(representative.get("repository_url") or ""),
                    "default_branch": str(representative.get("default_branch") or ""),
                    "visibility": "private",
                    "credential_requirement_ref": "",
                },
            })
        bindings = [
            (component_key, legacy_bindings[component_key])
            for component_key, _, _ in group
            if component_key in legacy_bindings
        ]
        binding_paths = {str(binding.get("directory_path") or "") for _, binding in bindings}
        if len(binding_paths) > 1:
            conflicts.append({
                "repository_identity": identity,
                "component_keys": [item[0] for item in bindings],
                "reason": "multiple_local_git_roots",
            })
            continue
        for component_key, _, source in group:
            operations.append({
                "op": "component.update",
                "key": component_key,
                "scope": "shared",
                "values": {
                    "source.ref": f"mawsource://code-source/{source_key}",
                    "source.repository_ref": source_key,
                    "source.repository_url": "",
                    "source.default_branch": "",
                },
            })
        if bindings:
            binding = bindings[0][1]
            operations.append({
                "op": "code_source_binding.upsert",
                "key": source_key,
                "scope": "local",
                "values": {
                    "source_ref": f"mawsource://code-source/{source_key}",
                    "directory_path": str(binding.get("directory_path") or ""),
                    "origin": str(binding.get("origin") or "existing_directory"),
                    "git_access_profile_ref": str(binding.get("git_access_profile_ref") or ""),
                    "bound_repository_identity": identity,
                    "bound_at": str(binding.get("bound_at") or datetime.now(timezone.utc).isoformat()),
                },
            })
            for component_key, _ in bindings:
                operations.append({"op": "component_source_binding.remove", "key": component_key, "scope": "local", "values": {}})
        migrations.append({
            "code_source_key": source_key,
            "repository_identity": identity,
            "component_keys": [item[0] for item in group],
            "binding_reused": bool(bindings),
        })
    if conflicts:
        raise ValueError("seed_source_registry_binding_conflict:" + ",".join(item["repository_identity"] for item in conflicts))
    public, private = _change(project_root, projection, operations, "将组件级外部 Git 声明归并为共享代码源")
    public["consolidation"] = {"migrations": migrations, "source_directories_moved": False}
    private["consolidation"] = public["consolidation"]
    return public, private


def inspect_project_sources(root: Path | str, *, include_local: bool = True) -> dict[str, Any]:
    project_root = _root(root)
    projection = compile_project_definition(project_root)
    components = _components(projection)
    registry = _code_sources(projection)
    bindings = _code_source_bindings(projection)
    legacy_bindings = _legacy_bindings(projection)
    records: list[dict[str, Any]] = []
    for source_key, source in sorted(registry.items()):
        component_keys = sorted(
            key for key, component in components.items()
            if isinstance(component.get("source"), dict)
            and component["source"].get("repository_ref") == source_key
        )
        binding = bindings.get(source_key)
        status = "unbound"
        error = ""
        local: dict[str, Any] = {}
        if binding:
            directory = Path(str(binding.get("directory_path") or "")).expanduser()
            try:
                validated, _ = _validate_external_directory(
                    directory,
                    repository_url=str(source.get("repository_url") or ""),
                    project_root=project_root,
                )
                status = "ready"
                local = {
                    "directory_path": str(validated),
                    "origin": str(binding.get("origin") or ""),
                    "git_access_profile_ref": str(binding.get("git_access_profile_ref") or ""),
                    "head": _git_output(validated, "rev-parse", "HEAD"),
                    "branch": _git_output(validated, "branch", "--show-current"),
                    "dirty": bool(_git_output(validated, "status", "--porcelain")),
                }
            except ValueError as exc:
                status = "needs_attention"
                error = str(exc)
        record = {
            "key": source_key,
            "name": str(source.get("name") or source_key),
            "repository_url": str(source.get("repository_url") or ""),
            "default_branch": str(source.get("default_branch") or ""),
            "visibility": str(source.get("visibility") or "private"),
            "component_keys": component_keys,
            "status": status,
            "error": error,
            "default_managed_clone_path": str(default_managed_clone_path(project_root, source_key)),
        }
        if include_local:
            record["local"] = local
        records.append(record)
    legacy: list[dict[str, Any]] = []
    for component_key, component in sorted(components.items()):
        source = component.get("source") if isinstance(component.get("source"), dict) else {}
        if source.get("mode") != "external_git" or source.get("repository_ref"):
            continue
        binding = legacy_bindings.get(component_key)
        status = "unbound"
        error = ""
        local: dict[str, Any] = {}
        if binding:
            directory = Path(str(binding.get("directory_path") or "")).expanduser()
            try:
                validated, _ = _validate_external_directory(
                    directory,
                    repository_url=str(source.get("repository_url") or ""),
                    project_root=project_root,
                )
                status = "bound"
                local = {
                    **dict(binding),
                    "directory_path": str(validated),
                    "head": _git_output(validated, "rev-parse", "HEAD"),
                    "branch": _git_output(validated, "branch", "--show-current"),
                    "dirty": bool(_git_output(validated, "status", "--porcelain")),
                }
            except ValueError as exc:
                status = "needs_attention"
                error = str(exc)
        legacy.append({
            "component_key": component_key,
            "source_ref": str(source.get("ref") or ""),
            "repository_url": str(source.get("repository_url") or ""),
            "status": status,
            "error": error,
            "default_managed_clone_path": str(default_managed_clone_path(project_root, component_key)),
            **({"local": local} if include_local else {}),
        })
    subprojects_raw = _configs(projection, ".maw/subprojects.yaml", "subprojects")
    subprojects = []
    for item in subprojects_raw if isinstance(subprojects_raw, list) else []:
        if not isinstance(item, dict):
            continue
        subproject_key = str(item.get("key") or "")
        subprojects.append({
            **item,
            "component_keys": sorted(
                key for key, component in components.items()
                if str(component.get("subproject_ref") or "default") == subproject_key
            ),
        })
    unbound_count = sum(item["status"] != "ready" for item in records) + sum(item["status"] != "bound" for item in legacy)
    return {
        "schema": "mawflow.project_source_hydration.v1",
        "status": "ready" if unbound_count == 0 else "needs_attention",
        "subprojects": subprojects,
        "code_sources": records,
        "legacy_component_sources": legacy,
        "summary": {
            "subprojects": len(subprojects),
            "code_sources": len(records),
            "legacy_component_sources": len(legacy),
            "unbound": unbound_count,
        },
        "cloud_summary": {
            "code_sources": [
                {
                    "key": item["key"],
                    "component_keys": item["component_keys"],
                    "binding_required": item["status"] != "ready",
                }
                for item in records
            ],
            "legacy_component_sources": [
                {"component_key": item["component_key"], "binding_required": item["status"] != "bound"}
                for item in legacy
            ],
            "absolute_paths_included": False,
            "credential_refs_included": False,
            "source_content_included": False,
        },
    }


def apply_topology_plan(
    root: Path | str,
    plan: dict[str, Any],
    confirmation: str,
    *,
    backup_root: Path | str,
) -> dict[str, Any]:
    return apply_change_plan(_root(root), plan, confirmation, backup_root=backup_root)


__all__ = [
    "apply_topology_plan",
    "default_managed_clone_path",
    "inspect_deployment_targets",
    "inspect_project_sources",
    "plan_code_source_binding",
    "plan_code_source_remove",
    "plan_code_source_unbind",
    "plan_code_source_upsert",
    "plan_deployment_target_remove",
    "plan_deployment_target_upsert",
    "plan_source_registry_consolidation",
    "plan_subproject_remove",
    "plan_subproject_upsert",
]
