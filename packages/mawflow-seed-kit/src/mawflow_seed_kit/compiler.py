from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Any
from urllib.parse import urlsplit

import yaml

from .catalog import CONTRACT_VERSION, catalog, contract_fingerprint


MAX_CONFIG_BYTES = 2 * 1024 * 1024
KEY_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{0,159}$")
GIT_REF_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,239}$")
REF_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,239}$")
COMPONENT_SOURCE_REF_PATTERN = re.compile(r"^mawsource://component/[a-z0-9][a-z0-9._-]{0,159}$")
CODE_SOURCE_REF_PATTERN = re.compile(r"^mawsource://code-source/[a-z0-9][a-z0-9._-]{0,159}$")
GIT_ACCESS_PROFILE_REF_PATTERN = re.compile(r"^mawgit://[A-Za-z0-9][A-Za-z0-9._/-]{0,239}$")
SCP_REPOSITORY_PATTERN = re.compile(r"^(?:[A-Za-z0-9._-]+@)?([A-Za-z0-9.-]+):([^?#\s]+)$")


def _deep_merge(base: object, overlay: object) -> object:
    if isinstance(base, dict) and isinstance(overlay, dict):
        result = dict(base)
        for key, value in overlay.items():
            result[key] = _deep_merge(result.get(key), value) if key in result else value
        return result
    return overlay


def _safe_yaml(root: Path, source_ref: str, *, required: bool) -> tuple[dict[str, Any], dict[str, Any]]:
    root = root.resolve(strict=True)
    path = root / source_ref
    diagnostic: dict[str, Any] = {"source_ref": source_ref, "required": required}
    if path.is_symlink():
        diagnostic.update(status="rejected", code="seed_source_symlink_forbidden")
        return {}, diagnostic
    try:
        resolved = path.resolve(strict=True)
        resolved.relative_to(root)
    except FileNotFoundError:
        diagnostic.update(status="missing", code="seed_source_missing")
        return {}, diagnostic
    except (OSError, ValueError):
        diagnostic.update(status="rejected", code="seed_source_outside_project")
        return {}, diagnostic
    if not resolved.is_file() or resolved.stat().st_size > MAX_CONFIG_BYTES:
        diagnostic.update(status="rejected", code="seed_source_unavailable")
        return {}, diagnostic
    try:
        text = resolved.read_text(encoding="utf-8", errors="strict")
        loaded = yaml.safe_load(text)
    except (OSError, UnicodeError, yaml.YAMLError):
        diagnostic.update(status="invalid", code="seed_source_invalid_yaml")
        return {}, diagnostic
    if not isinstance(loaded, dict):
        diagnostic.update(status="invalid", code="seed_source_mapping_required")
        return {}, diagnostic
    diagnostic.update(
        status="loaded",
        bytes=len(text.encode("utf-8")),
        content_hash=f"sha256:{hashlib.sha256(text.encode()).hexdigest()}",
    )
    return dict(loaded), diagnostic


def _issue(code: str, source_ref: str, message: str, *, severity: str = "error") -> dict[str, str]:
    return {"code": code, "source_ref": source_ref, "message": message, "severity": severity}


def _nested_value(item: dict[str, Any], field: str) -> tuple[bool, Any]:
    current: Any = item
    for part in field.split("."):
        if not isinstance(current, dict) or part not in current:
            return False, None
        current = current[part]
    return True, current


def _relative_path_valid(value: str) -> bool:
    path = Path(value)
    return bool(value) and not path.is_absolute() and ".." not in path.parts and "\\" not in value


def _url_valid(value: str) -> bool:
    try:
        parsed = urlsplit(value)
    except ValueError:
        return False
    return (
        parsed.scheme in {"http", "https"}
        and bool(parsed.netloc)
        and not parsed.username
        and not parsed.password
        and not parsed.query
        and not parsed.fragment
    )


def _absolute_path_valid(value: str) -> bool:
    if not value or "\x00" in value or "\n" in value or "\r" in value:
        return False
    normalized = value.replace("\\", "/")
    return ".." not in Path(normalized).parts and (
        normalized.startswith("/")
        or bool(re.match(r"^[A-Za-z]:/[^/].*", normalized))
        or normalized.startswith("//")
    )


def _repository_url_valid(value: str) -> bool:
    scp = SCP_REPOSITORY_PATTERN.fullmatch(value)
    if scp:
        return bool(scp.group(1) and scp.group(2).strip("/")) and ".." not in Path(scp.group(2)).parts
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        return False
    if parsed.scheme not in {"http", "https", "ssh"} or not parsed.hostname or parsed.password or parsed.query or parsed.fragment:
        return False
    if parsed.scheme in {"http", "https"} and parsed.username:
        return False
    return (port is None or 1 <= port <= 65535) and bool(parsed.path.strip("/"))


def _repository_identity(value: str) -> str:
    scp = SCP_REPOSITORY_PATTERN.fullmatch(value)
    if scp:
        host, repository_path = scp.group(1), scp.group(2)
    else:
        parsed = urlsplit(value)
        host, repository_path = str(parsed.hostname or ""), parsed.path
    normalized_path = repository_path.strip("/")
    if normalized_path.endswith(".git"):
        normalized_path = normalized_path[:-4]
    return f"{host.lower()}/{normalized_path}"


def _field_value_valid(field_type: str, value: Any, definition: dict[str, Any]) -> bool:
    optional_empty = field_type.endswith("_or_empty") and value in {None, ""}
    if optional_empty:
        return True
    if field_type in {"text", "long_text", "long_text_or_empty"}:
        return isinstance(value, str)
    if field_type == "enum":
        if not isinstance(value, str):
            return False
        if value in definition.get("options", []):
            return True
        return bool(
            definition.get("allow_custom_key")
            and KEY_PATTERN.fullmatch(value)
        )
    if field_type in {"key", "key_or_empty"}:
        return isinstance(value, str) and bool(KEY_PATTERN.fullmatch(value))
    if field_type == "key_list":
        return isinstance(value, list) and all(isinstance(item, str) and KEY_PATTERN.fullmatch(item) for item in value)
    if field_type == "text_list":
        return isinstance(value, list) and all(isinstance(item, str) and len(item) <= 2000 for item in value)
    if field_type == "path_list":
        return isinstance(value, list) and all(isinstance(item, str) and _relative_path_valid(item) for item in value)
    if field_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if field_type in {"git_ref", "git_ref_or_empty"}:
        return isinstance(value, str) and bool(GIT_REF_PATTERN.fullmatch(value)) and ".." not in value
    if field_type in {"component_source_ref", "component_source_ref_or_empty"}:
        return isinstance(value, str) and bool(COMPONENT_SOURCE_REF_PATTERN.fullmatch(value))
    if field_type in {"code_source_ref", "code_source_ref_or_empty"}:
        return isinstance(value, str) and bool(CODE_SOURCE_REF_PATTERN.fullmatch(value))
    if field_type == "source_ref_or_empty":
        return isinstance(value, str) and (
            not value
            or bool(COMPONENT_SOURCE_REF_PATTERN.fullmatch(value))
            or bool(CODE_SOURCE_REF_PATTERN.fullmatch(value))
        )
    if field_type == "git_access_profile_ref_or_empty":
        return isinstance(value, str) and (not value or bool(GIT_ACCESS_PROFILE_REF_PATTERN.fullmatch(value)))
    if field_type == "absolute_path":
        return isinstance(value, str) and _absolute_path_valid(value)
    if field_type in {"repository_url", "repository_url_or_empty"}:
        return isinstance(value, str) and _repository_url_valid(value)
    if field_type in {"path", "path_or_empty", "secret_requirement_ref_or_empty", "credential_binding_ref_or_empty"}:
        return isinstance(value, str) and _relative_path_valid(value)
    if field_type == "ref_or_empty":
        return isinstance(value, str) and (not value or bool(REF_PATTERN.fullmatch(value)))
    if field_type == "url_or_path_or_empty":
        return isinstance(value, str) and (
            _url_valid(value) or _relative_path_valid(value) or (value.startswith("/") and ".." not in Path(value).parts)
        )
    if field_type in {"url_or_empty"}:
        return isinstance(value, str) and _url_valid(value)
    if field_type == "url_path_or_empty":
        return isinstance(value, str) and value.startswith("/") and ".." not in Path(value).parts
    if field_type == "bool":
        return isinstance(value, bool)
    if field_type == "bool_or_optional":
        return isinstance(value, bool) or value == "optional"
    if field_type == "port_or_empty":
        return isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= 65535
    if field_type == "date_or_empty":
        return isinstance(value, str) and bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", value))
    return True


def _validate_fields(
    item: dict[str, Any],
    definitions: dict[str, dict[str, Any]],
    *,
    source_ref: str,
    label: str,
) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    for field, definition in definitions.items():
        present, value = _nested_value(item, field)
        if definition.get("required") and (not present or value is None or value == ""):
            issues.append(_issue("seed_required_field_missing", source_ref, f"{label} 缺少 {field}"))
            continue
        if present and not _field_value_valid(str(definition.get("type") or ""), value, definition):
            issues.append(_issue("seed_field_value_invalid", source_ref, f"{label}.{field} 不符合 {definition.get('type')} 契约"))
    return issues


def _validate_model(configs: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    project = configs.get(".maw/project.yaml", {}).get("project")
    project_key = str(project.get("key") or "").strip() if isinstance(project, dict) else ""
    if not KEY_PATTERN.fullmatch(project_key):
        issues.append(_issue("seed_project_key_invalid", ".maw/project.yaml", "project.key 必须是稳定的小写项目标识"))
    if isinstance(project, dict):
        issues.extend(
            _validate_fields(
                project,
                catalog()["targets"]["project"]["fields"],
                source_ref=".maw/project.yaml",
                label="project",
            )
        )

    raw_subprojects = configs.get(".maw/subprojects.yaml", {}).get("subprojects")
    subprojects = raw_subprojects if isinstance(raw_subprojects, list) else []
    subproject_keys: list[str] = []
    for item in subprojects:
        key = str(item.get("key") or "").strip() if isinstance(item, dict) else ""
        if not KEY_PATTERN.fullmatch(key):
            issues.append(_issue("seed_subproject_key_invalid", ".maw/subprojects.yaml", f"非法子项目标识：{key or '<empty>'}"))
        subproject_keys.append(key)
        if isinstance(item, dict):
            issues.extend(
                _validate_fields(
                    item,
                    catalog()["targets"]["subproject"]["fields"],
                    source_ref=".maw/subprojects.yaml",
                    label=f"子项目 {key or '<empty>'}",
                )
            )
    if len(subproject_keys) != len(set(subproject_keys)):
        issues.append(_issue("seed_subproject_key_duplicate", ".maw/subprojects.yaml", "子项目标识不得重复"))

    raw_code_sources = configs.get(".maw/code-sources.yaml", {}).get("code_sources")
    code_sources = raw_code_sources if isinstance(raw_code_sources, dict) else {}
    code_source_map: dict[str, dict[str, Any]] = {}
    code_source_identities: dict[str, str] = {}
    if not isinstance(raw_code_sources, dict):
        issues.append(_issue("seed_code_sources_invalid", ".maw/code-sources.yaml", "code_sources 必须是映射"))
    else:
        for raw_key, raw_source in raw_code_sources.items():
            key = str(raw_key).strip()
            if not KEY_PATTERN.fullmatch(key) or not isinstance(raw_source, dict):
                issues.append(_issue("seed_code_source_invalid", ".maw/code-sources.yaml", f"非法代码源：{key or '<empty>'}"))
                continue
            source = dict(raw_source)
            code_source_map[key] = source
            issues.extend(
                _validate_fields(
                    source,
                    catalog()["targets"]["code_source"]["fields"],
                    source_ref=".maw/code-sources.yaml",
                    label=f"代码源 {key}",
                )
            )
            repository_url = str(source.get("repository_url") or "")
            if _repository_url_valid(repository_url):
                identity = _repository_identity(repository_url)
                previous = code_source_identities.get(identity)
                if previous is not None:
                    issues.append(_issue("seed_code_source_repository_duplicate", ".maw/code-sources.yaml", f"代码源 {previous} 与 {key} 指向同一仓库"))
                else:
                    code_source_identities[identity] = key

    raw_components = configs.get(".maw/components.yaml", {}).get("components")
    components = raw_components if isinstance(raw_components, list) else []
    component_keys: list[str] = []
    component_map: dict[str, dict[str, Any]] = {}
    for item in components:
        key = str(item.get("key") or "").strip() if isinstance(item, dict) else ""
        if not KEY_PATTERN.fullmatch(key):
            issues.append(_issue("seed_component_key_invalid", ".maw/components.yaml", f"非法组件标识：{key or '<empty>'}"))
        component_keys.append(key)
        if isinstance(item, dict):
            component_map[key] = item
            issues.extend(
                _validate_fields(
                    item,
                    catalog()["targets"]["component"]["fields"],
                    source_ref=".maw/components.yaml",
                    label=f"组件 {key or '<empty>'}",
                )
            )
            subproject_ref = str(item.get("subproject_ref") or "default")
            if subproject_ref not in subproject_keys:
                issues.append(_issue("seed_component_subproject_missing", ".maw/components.yaml", f"组件 {key} 引用了不存在的子项目 {subproject_ref}"))
            source = item.get("source")
            mode = str(source.get("mode") or "embedded") if isinstance(source, dict) else "embedded"
            if source is not None and not isinstance(source, dict):
                issues.append(_issue("seed_component_source_invalid", ".maw/components.yaml", f"组件 {key} 的 source 必须是映射"))
            elif mode == "external_git":
                repository_ref = str(source.get("repository_ref") or "")
                expected_ref = (
                    f"mawsource://code-source/{repository_ref}"
                    if repository_ref
                    else f"mawsource://component/{key}"
                )
                if source.get("ref") != expected_ref:
                    issues.append(_issue("seed_component_source_ref_mismatch", ".maw/components.yaml", f"组件 {key} 的 source.ref 必须为 {expected_ref}"))
                if repository_ref:
                    registered = code_source_map.get(repository_ref)
                    if registered is None:
                        issues.append(_issue("seed_component_code_source_missing", ".maw/components.yaml", f"组件 {key} 引用了不存在的代码源 {repository_ref}"))
                    elif source.get("repository_url") and _repository_identity(str(source.get("repository_url"))) != _repository_identity(str(registered.get("repository_url") or "")):
                        issues.append(_issue("seed_component_code_source_repository_mismatch", ".maw/components.yaml", f"组件 {key} 的内联仓库与代码源 {repository_ref} 不一致"))
                elif not _repository_url_valid(str(source.get("repository_url") or "")):
                    issues.append(_issue("seed_component_repository_url_invalid", ".maw/components.yaml", f"组件 {key} 缺少合法 repository_url"))
            elif mode == "embedded":
                if isinstance(source, dict) and any(source.get(field) for field in ("ref", "repository_url", "repository_subpath", "default_branch")):
                    issues.append(_issue("seed_component_embedded_source_fields_forbidden", ".maw/components.yaml", f"组件 {key} 的 embedded 模式不得声明外部仓库字段"))
            else:
                issues.append(_issue("seed_component_source_mode_invalid", ".maw/components.yaml", f"组件 {key} 的 source.mode 非法"))
    if len(component_keys) != len(set(component_keys)):
        issues.append(_issue("seed_component_key_duplicate", ".maw/components.yaml", "组件标识不得重复"))

    raw_bindings = configs.get(".maw/component-sources.yaml", {}).get("component_sources", {})
    if not isinstance(raw_bindings, dict):
        issues.append(_issue("seed_component_source_bindings_invalid", ".local/.maw/component-sources.yaml", "component_sources 必须是映射"))
    else:
        for binding_key, binding in raw_bindings.items():
            key = str(binding_key)
            if not KEY_PATTERN.fullmatch(key) or not isinstance(binding, dict):
                issues.append(_issue("seed_component_source_binding_invalid", ".local/.maw/component-sources.yaml", f"非法源码绑定：{key}"))
                continue
            issues.extend(
                _validate_fields(
                    binding,
                    catalog()["targets"]["component_source_binding"]["fields"],
                    source_ref=".local/.maw/component-sources.yaml",
                    label=f"源码绑定 {key}",
                )
            )
            component = component_map.get(key)
            source = component.get("source") if isinstance(component, dict) else None
            if not isinstance(source, dict) or source.get("mode") != "external_git" or source.get("repository_ref"):
                issues.append(_issue("seed_component_source_binding_orphan", ".local/.maw/component-sources.yaml", f"源码绑定 {key} 没有对应的 external_git 组件"))
                continue
            expected_ref = f"mawsource://component/{key}"
            if binding.get("source_ref") != expected_ref:
                issues.append(_issue("seed_component_source_binding_ref_mismatch", ".local/.maw/component-sources.yaml", f"源码绑定 {key} 的 source_ref 不匹配"))
            repository_url = str(source.get("repository_url") or "")
            if _repository_url_valid(repository_url) and binding.get("bound_repository_identity") != _repository_identity(repository_url):
                issues.append(_issue("seed_component_source_binding_repository_mismatch", ".local/.maw/component-sources.yaml", f"源码绑定 {key} 的仓库身份不匹配"))

    raw_code_source_bindings = configs.get(".maw/code-source-bindings.yaml", {}).get("code_source_bindings", {})
    if not isinstance(raw_code_source_bindings, dict):
        issues.append(_issue("seed_code_source_bindings_invalid", ".local/.maw/code-source-bindings.yaml", "code_source_bindings 必须是映射"))
    else:
        for binding_key, binding in raw_code_source_bindings.items():
            key = str(binding_key)
            if not KEY_PATTERN.fullmatch(key) or not isinstance(binding, dict):
                issues.append(_issue("seed_code_source_binding_invalid", ".local/.maw/code-source-bindings.yaml", f"非法代码源绑定：{key}"))
                continue
            issues.extend(
                _validate_fields(
                    binding,
                    catalog()["targets"]["code_source_binding"]["fields"],
                    source_ref=".local/.maw/code-source-bindings.yaml",
                    label=f"代码源绑定 {key}",
                )
            )
            registered = code_source_map.get(key)
            if registered is None:
                issues.append(_issue("seed_code_source_binding_orphan", ".local/.maw/code-source-bindings.yaml", f"代码源绑定 {key} 没有对应声明"))
                continue
            expected_ref = f"mawsource://code-source/{key}"
            if binding.get("source_ref") != expected_ref:
                issues.append(_issue("seed_code_source_binding_ref_mismatch", ".local/.maw/code-source-bindings.yaml", f"代码源绑定 {key} 的 source_ref 不匹配"))
            repository_url = str(registered.get("repository_url") or "")
            if _repository_url_valid(repository_url) and binding.get("bound_repository_identity") != _repository_identity(repository_url):
                issues.append(_issue("seed_code_source_binding_repository_mismatch", ".local/.maw/code-source-bindings.yaml", f"代码源绑定 {key} 的仓库身份不匹配"))

    raw_modules = configs.get(".maw/modules.yaml", {}).get("modules")
    modules = raw_modules if isinstance(raw_modules, list) else []
    module_keys: list[str] = []
    for item in modules:
        key = str(item.get("key") or "").strip() if isinstance(item, dict) else ""
        if not KEY_PATTERN.fullmatch(key):
            issues.append(_issue("seed_module_key_invalid", ".maw/modules.yaml", f"非法模块标识：{key or '<empty>'}"))
        module_keys.append(key)
        if isinstance(item, dict):
            issues.extend(
                _validate_fields(
                    item,
                    catalog()["targets"]["module"]["fields"],
                    source_ref=".maw/modules.yaml",
                    label=f"模块 {key or '<empty>'}",
                )
            )
        for ref in item.get("component_refs", []) if isinstance(item, dict) else []:
            if ref not in component_keys:
                issues.append(_issue("seed_module_component_missing", ".maw/modules.yaml", f"模块 {key} 引用了不存在的组件 {ref}"))
        for ref in item.get("depends_on", []) if isinstance(item, dict) else []:
            if ref == key:
                issues.append(_issue("seed_module_dependency_self", ".maw/modules.yaml", f"模块 {key} 不得依赖自身"))
    if len(module_keys) != len(set(module_keys)):
        issues.append(_issue("seed_module_key_duplicate", ".maw/modules.yaml", "模块标识不得重复"))
    module_key_set = set(module_keys)
    graph = {
        str(item.get("key") or ""): [str(ref) for ref in item.get("depends_on", []) if isinstance(ref, str)]
        for item in modules
        if isinstance(item, dict)
    }
    for key, dependencies in graph.items():
        for ref in dependencies:
            if ref not in module_key_set:
                issues.append(_issue("seed_module_dependency_missing", ".maw/modules.yaml", f"模块 {key} 引用了不存在的依赖 {ref}"))
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(key: str) -> bool:
        if key in visiting:
            return True
        if key in visited:
            return False
        visiting.add(key)
        has_cycle = any(ref in graph and visit(ref) for ref in graph.get(key, []))
        visiting.remove(key)
        visited.add(key)
        return has_cycle

    if any(visit(key) for key in graph):
        issues.append(_issue("seed_module_dependency_cycle", ".maw/modules.yaml", "模块依赖不得形成循环"))

    runtime = configs.get(".maw/app-runtime.yaml", {}).get("app_runtime")
    apps = runtime.get("apps") if isinstance(runtime, dict) else {}
    if not isinstance(apps, dict):
        issues.append(_issue("seed_runtime_apps_invalid", ".maw/app-runtime.yaml", "app_runtime.apps 必须是映射"))
    else:
        for app_key, app in apps.items():
            component_ref = str(app.get("component_ref") or "") if isinstance(app, dict) else ""
            if not KEY_PATTERN.fullmatch(str(app_key)) or not isinstance(app, dict):
                issues.append(_issue("seed_runtime_app_invalid", ".maw/app-runtime.yaml", f"非法应用定义：{app_key}"))
            elif component_ref not in component_keys:
                issues.append(_issue("seed_runtime_component_missing", ".maw/app-runtime.yaml", f"应用 {app_key} 引用了不存在的组件 {component_ref}"))
            if isinstance(app, dict):
                runtime_item = {"app_key": app_key, **app}
                issues.extend(
                    _validate_fields(
                        runtime_item,
                        catalog()["targets"]["runtime_app"]["fields"],
                        source_ref=".maw/app-runtime.yaml",
                        label=f"应用 {app_key}",
                    )
                )
    environments = configs.get(".maw/environments.yaml", {}).get("environments")
    if not isinstance(environments, dict):
        issues.append(_issue("seed_environments_invalid", ".maw/environments.yaml", "environments 必须是映射"))
    else:
        for environment_key, environment in environments.items():
            if not KEY_PATTERN.fullmatch(str(environment_key)) or not isinstance(environment, dict):
                issues.append(_issue("seed_environment_invalid", ".maw/environments.yaml", f"非法环境定义：{environment_key}"))
                continue
            issues.extend(
                _validate_fields(
                    environment,
                    catalog()["targets"]["environment"]["fields"],
                    source_ref=".maw/environments.yaml",
                    label=f"环境 {environment_key}",
                )
            )

    project_config = configs.get(".maw/project.yaml", {})
    credentials = project_config.get("credentials") if isinstance(project_config, dict) else {}
    requirements = credentials.get("requirements") if isinstance(credentials, dict) else None
    if not isinstance(requirements, list):
        issues.append(_issue("seed_credential_requirements_invalid", ".maw/project.yaml", "credentials.requirements 必须是列表"))
    else:
        requirement_keys: list[str] = []
        for item in requirements:
            key = str(item.get("key") or "").strip() if isinstance(item, dict) else ""
            if not KEY_PATTERN.fullmatch(key):
                issues.append(_issue("seed_credential_requirement_key_invalid", ".maw/project.yaml", f"非法凭证需求标识：{key or '<empty>'}"))
            requirement_keys.append(key)
            if isinstance(item, dict):
                issues.extend(
                    _validate_fields(
                        item,
                        catalog()["targets"]["credential_requirement"]["fields"],
                        source_ref=".maw/project.yaml",
                        label=f"凭证需求 {key or '<empty>'}",
                    )
                )
        if len(requirement_keys) != len(set(requirement_keys)):
            issues.append(_issue("seed_credential_requirement_key_duplicate", ".maw/project.yaml", "凭证需求标识不得重复"))

    technology = configs.get(".maw/technology.yaml", {}).get("technology")
    if not isinstance(technology, dict):
        issues.append(_issue("seed_technology_invalid", ".maw/technology.yaml", "technology 必须是映射"))
    else:
        issues.extend(
            _validate_fields(
                technology,
                catalog()["targets"]["technology"]["fields"],
                source_ref=".maw/technology.yaml",
                label="technology",
            )
        )
        for target_key, collection_key in (
            ("technology_language", "languages"),
            ("technology_framework", "frameworks"),
            ("technology_service", "services"),
        ):
            entries = technology.get(collection_key)
            if not isinstance(entries, list):
                issues.append(_issue("seed_technology_collection_invalid", ".maw/technology.yaml", f"technology.{collection_key} 必须是列表"))
                continue
            keys: list[str] = []
            for item in entries:
                key = str(item.get("key") or "").strip() if isinstance(item, dict) else ""
                if not KEY_PATTERN.fullmatch(key):
                    issues.append(_issue("seed_technology_key_invalid", ".maw/technology.yaml", f"非法技术标识：{key or '<empty>'}"))
                keys.append(key)
                if isinstance(item, dict):
                    issues.extend(
                        _validate_fields(
                            item,
                            catalog()["targets"][target_key]["fields"],
                            source_ref=".maw/technology.yaml",
                            label=f"技术项 {key or '<empty>'}",
                        )
                    )
            if len(keys) != len(set(keys)):
                issues.append(_issue("seed_technology_key_duplicate", ".maw/technology.yaml", f"technology.{collection_key} 标识不得重复"))

    handbook = configs.get("docs/handbooks/manifest.yaml", {}).get("handbook_system")
    if not isinstance(handbook, dict):
        issues.append(_issue("seed_handbook_system_invalid", "docs/handbooks/manifest.yaml", "handbook_system 必须是映射"))
    else:
        issues.extend(
            _validate_fields(
                handbook,
                catalog()["targets"]["handbook_system"]["fields"],
                source_ref="docs/handbooks/manifest.yaml",
                label="handbook_system",
            )
        )
        volumes = handbook.get("volumes")
        if not isinstance(volumes, list):
            issues.append(_issue("seed_handbook_volumes_invalid", "docs/handbooks/manifest.yaml", "handbook_system.volumes 必须是列表"))
        else:
            volume_keys: list[str] = []
            for item in volumes:
                key = str(item.get("key") or "").strip() if isinstance(item, dict) else ""
                if not KEY_PATTERN.fullmatch(key):
                    issues.append(_issue("seed_handbook_volume_key_invalid", "docs/handbooks/manifest.yaml", f"非法手册卷标识：{key or '<empty>'}"))
                volume_keys.append(key)
                if isinstance(item, dict):
                    issues.extend(
                        _validate_fields(
                            item,
                            catalog()["targets"]["handbook_volume"]["fields"],
                            source_ref="docs/handbooks/manifest.yaml",
                            label=f"手册卷 {key or '<empty>'}",
                        )
                    )
            if len(volume_keys) != len(set(volume_keys)):
                issues.append(_issue("seed_handbook_volume_key_duplicate", "docs/handbooks/manifest.yaml", "手册卷标识不得重复"))
    return issues


def compile_project_definition(root: Path | str) -> dict[str, Any]:
    project_root = Path(root).expanduser().resolve(strict=True)
    contract = catalog()
    required_files = set(contract["required_files"])
    yaml_sources = [item for item in contract["required_files"] if item.endswith((".yaml", ".yml", ".lock"))]
    configs: dict[str, dict[str, Any]] = {}
    diagnostics: list[dict[str, Any]] = []
    for source_ref in yaml_sources:
        payload, diagnostic = _safe_yaml(project_root, source_ref, required=True)
        configs[source_ref] = payload
        diagnostics.append(diagnostic)
    for source_ref in required_files - set(yaml_sources):
        path = project_root / source_ref
        status = "loaded" if path.is_file() and not path.is_symlink() else "missing"
        diagnostics.append({"source_ref": source_ref, "required": True, "status": status})

    local_configs: dict[str, dict[str, Any]] = {}
    for target in contract["targets"].values():
        local_source = target.get("local_source")
        shared_source = target.get("source")
        if not local_source or local_source in local_configs:
            continue
        local_payload, diagnostic = _safe_yaml(project_root, local_source, required=False)
        diagnostics.append(diagnostic)
        if diagnostic["status"] == "loaded":
            local_configs[local_source] = local_payload
            configs[shared_source] = _deep_merge(configs.get(shared_source, {}), local_payload)  # type: ignore[assignment]

    issues = _validate_model(configs)
    lock = configs.get(".maw/seed.lock", {})
    lock_contract = int(lock.get("contract_version") or 0) if isinstance(lock, dict) else 0
    lock_fingerprint = str(lock.get("contract_fingerprint") or "") if isinstance(lock, dict) else ""
    migration_required = lock_contract != CONTRACT_VERSION or lock_fingerprint != contract_fingerprint()
    if migration_required:
        issues.append(_issue("seed_contract_migration_required", ".maw/seed.lock", "项目必须迁移到当前 Seed Contract 后才可写入", severity="warning"))

    fingerprint_inputs = [
        {"source_ref": item["source_ref"], "content_hash": item.get("content_hash", ""), "status": item["status"]}
        for item in sorted(diagnostics, key=lambda value: value["source_ref"])
    ]
    fingerprint = "sha256:" + hashlib.sha256(
        json.dumps(fingerprint_inputs, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    required_failures = [item for item in diagnostics if item.get("required") and item["status"] != "loaded"]
    error_count = sum(1 for item in issues if item["severity"] == "error") + len(required_failures)
    project = configs.get(".maw/project.yaml", {}).get("project")
    return {
        "schema": "mawflow.seed_project_definition.v2",
        "contract_version": CONTRACT_VERSION,
        "contract_fingerprint": contract_fingerprint(),
        "status": "ready" if not error_count and not migration_required else "needs_attention",
        "editable": not error_count and not migration_required,
        "migration_required": migration_required,
        "project": project if isinstance(project, dict) else {},
        "configs": configs,
        "local_configs": local_configs,
        "diagnostics": diagnostics,
        "issues": issues,
        "summary": {
            "required_sources": len(required_files),
            "loaded_sources": sum(1 for item in diagnostics if item["status"] == "loaded"),
            "errors": error_count,
            "warnings": sum(1 for item in issues if item["severity"] == "warning"),
        },
        "fingerprint": fingerprint,
    }


__all__ = ["compile_project_definition"]
