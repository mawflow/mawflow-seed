from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import tempfile
from typing import Any
from urllib.parse import urlsplit

import yaml

from .catalog import catalog, contract_fingerprint
from .changes import apply_change_plan, plan_change_set
from .compiler import compile_project_definition


KEY_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{0,159}$")
SCP_REPOSITORY_PATTERN = re.compile(r"^(?:[A-Za-z0-9._-]+@)?([A-Za-z0-9.-]+):([^?#\s]+)$")
MAX_TEXT_LENGTH = 200


def _hash(text: str) -> str:
    return f"sha256:{hashlib.sha256(text.encode()).hexdigest()}"


def _atomic_write(path: Path, text: str, mode: int = 0o644) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(name, mode)
        os.replace(name, path)
    except Exception:
        try:
            os.unlink(name)
        except OSError:
            pass
        raise


def _project_root(root: Path | str) -> Path:
    project_root = Path(root).expanduser().resolve(strict=True)
    if not (project_root / ".maw/project.yaml").is_file():
        raise ValueError("seed_component_project_required")
    return project_root


def _component_type(value: str) -> str:
    component_type = value.strip()
    allowed = set(catalog()["targets"]["component"]["fields"]["type"]["options"])
    if component_type not in allowed:
        raise ValueError("seed_component_type_invalid")
    return component_type


def _component_key(value: str) -> str:
    key = value.strip()
    if not KEY_PATTERN.fullmatch(key):
        raise ValueError("seed_component_key_invalid")
    return key


def _component_path(root: Path, key: str, value: str | None) -> tuple[str, Path]:
    relative = (value or f"code/{key}").strip().replace("\\", "/").rstrip("/")
    parts = Path(relative).parts
    if (
        not relative
        or relative.startswith("/")
        or re.match(r"^[A-Za-z]:/", relative)
        or ".." in parts
        or len(parts) < 2
        or parts[0] != "code"
        or any(part in {".git", ".local", ".maw"} for part in parts)
    ):
        raise ValueError("seed_component_path_must_be_under_code")
    target = root.joinpath(*parts)
    parent = target.parent.resolve(strict=False)
    parent.relative_to(root)
    if target.is_symlink() or any((root.joinpath(*parts[:index])).is_symlink() for index in range(1, len(parts) + 1)):
        raise ValueError("seed_component_symlink_forbidden")
    return relative, target


def _descriptor(key: str, name: str, component_type: str, relative: str) -> str:
    return yaml.safe_dump(
        {
            "schema": "mawflow.component.v1",
            "component": {
                "key": key,
                "app_key": key,
                "name": name,
                "type": component_type,
                "local_path": relative,
            },
            "commands": {},
            "boundaries": {"allowed_paths": [f"{relative}/**"]},
        },
        allow_unicode=True,
        sort_keys=False,
    )


def _readme(key: str, name: str, component_type: str, enabled: bool) -> str:
    initial_state = "已启用" if enabled else "未启用"
    return f"""# {name}

- 组件标识：`{key}`
- 组件类型：`{component_type}`
- 初始状态：{initial_state}

该目录只建立组件边界，不预置客户端、服务端或技术栈源码。请在确认实现与验证命令后执行：

```bash
mawflow component doctor {key}
mawflow component enable {key}
```
"""


def _file_write(root: Path, source_ref: str, proposed: str) -> dict[str, Any]:
    path = root / source_ref
    if path.is_symlink():
        raise ValueError("seed_component_symlink_forbidden")
    if path.exists():
        if not path.is_file() or path.stat().st_size > 2 * 1024 * 1024:
            raise ValueError("seed_component_file_unavailable")
        original = path.read_text(encoding="utf-8")
        mode = stat.S_IMODE(path.stat().st_mode)
        existed = True
    else:
        original = ""
        mode = 0o644
        existed = False
    return {
        "source_ref": source_ref,
        "expected_hash": _hash(original),
        "proposed_hash": _hash(proposed),
        "original_text": original,
        "proposed_text": proposed,
        "mode": mode,
        "existed": existed,
    }


def _component_map(projection: dict[str, Any]) -> dict[str, dict[str, Any]]:
    config = projection.get("configs", {}).get(".maw/components.yaml", {})
    return {
        str(item.get("key")): dict(item)
        for item in config.get("components", [])
        if isinstance(item, dict) and item.get("key")
    }


def _binding_map(projection: dict[str, Any]) -> dict[str, dict[str, Any]]:
    config = projection.get("configs", {}).get(".maw/component-sources.yaml", {})
    bindings = config.get("component_sources", {}) if isinstance(config, dict) else {}
    return {
        str(key): dict(value)
        for key, value in bindings.items()
        if isinstance(value, dict)
    } if isinstance(bindings, dict) else {}


def _code_source_map(projection: dict[str, Any]) -> dict[str, dict[str, Any]]:
    sources = projection.get("configs", {}).get(".maw/code-sources.yaml", {}).get("code_sources", {})
    return {
        str(key): dict(value)
        for key, value in sources.items()
        if isinstance(value, dict)
    } if isinstance(sources, dict) else {}


def _code_source_binding_map(projection: dict[str, Any]) -> dict[str, dict[str, Any]]:
    bindings = (
        projection.get("configs", {})
        .get(".maw/code-source-bindings.yaml", {})
        .get("code_source_bindings", {})
    )
    return {
        str(key): dict(value)
        for key, value in bindings.items()
        if isinstance(value, dict)
    } if isinstance(bindings, dict) else {}


def _source_mode(value: str) -> str:
    mode = value.strip() or "embedded"
    if mode not in {"embedded", "external_git"}:
        raise ValueError("seed_component_source_mode_invalid")
    return mode


def _repository_identity(value: str) -> str:
    text = value.strip()
    scp = SCP_REPOSITORY_PATTERN.fullmatch(text)
    if scp:
        host, repository_path = scp.group(1), scp.group(2)
    else:
        parsed = urlsplit(text)
        host, repository_path = str(parsed.hostname or ""), parsed.path
    normalized_path = repository_path.strip("/")
    if normalized_path.endswith(".git"):
        normalized_path = normalized_path[:-4]
    if not host or not normalized_path:
        raise ValueError("seed_component_repository_url_invalid")
    return f"{host.lower()}/{normalized_path}"


def _git_output(directory: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(directory), *args],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ValueError("seed_component_git_inspection_failed") from exc
    if result.returncode != 0:
        raise ValueError("seed_component_git_inspection_failed")
    return result.stdout.strip()


def _validate_external_directory(
    directory_path: Path | str,
    *,
    repository_url: str,
    repository_subpath: str = "",
    project_root: Path | None = None,
) -> tuple[Path, str]:
    candidate = Path(directory_path).expanduser()
    if candidate.is_symlink():
        raise ValueError("seed_component_source_directory_symlink_forbidden")
    try:
        directory = candidate.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ValueError("seed_component_source_directory_missing") from exc
    if not directory.is_dir():
        raise ValueError("seed_component_source_directory_missing")
    git_root = Path(_git_output(directory, "rev-parse", "--show-toplevel")).resolve(strict=True)
    if git_root != directory:
        raise ValueError("seed_component_source_directory_must_be_git_root")
    if project_root is not None:
        try:
            directory.relative_to(project_root)
        except ValueError:
            pass
        else:
            outer = subprocess.run(
                ["git", "-C", str(project_root), "rev-parse", "--show-toplevel"],
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if outer.returncode == 0:
                ignored = subprocess.run(
                    ["git", "-C", str(project_root), "check-ignore", "--quiet", "--no-index", str(directory)],
                    check=False,
                    capture_output=True,
                    timeout=5,
                )
                if ignored.returncode != 0:
                    raise ValueError("seed_component_source_project_path_must_be_git_ignored")
    remote_url = _git_output(directory, "remote", "get-url", "origin")
    expected_identity = _repository_identity(repository_url)
    if _repository_identity(remote_url) != expected_identity:
        raise ValueError("seed_component_source_repository_mismatch")
    if repository_subpath:
        subpath = Path(repository_subpath)
        if subpath.is_absolute() or ".." in subpath.parts or not (directory / subpath).is_dir():
            raise ValueError("seed_component_source_subpath_missing")
    return directory, expected_identity


def _external_source(component_key: str, component: dict[str, Any]) -> dict[str, Any]:
    source = component.get("source")
    if not isinstance(source, dict) or source.get("mode") != "external_git":
        raise ValueError("seed_component_external_source_required")
    if source.get("repository_ref"):
        raise ValueError("seed_component_uses_shared_code_source")
    if source.get("ref") != f"mawsource://component/{component_key}":
        raise ValueError("seed_component_source_ref_mismatch")
    _repository_identity(str(source.get("repository_url") or ""))
    return source


def _reference_hit(payload: Any, component_key: str, parent_key: str = "") -> bool:
    if isinstance(payload, dict):
        return any(_reference_hit(value, component_key, str(key)) for key, value in payload.items())
    if isinstance(payload, list):
        if "component" in parent_key or parent_key in {"app_keys", "apps"}:
            return component_key in {str(item) for item in payload if not isinstance(item, (dict, list))}
        return any(_reference_hit(item, component_key, parent_key) for item in payload)
    return ("component" in parent_key or parent_key in {"app_key", "app_ref"}) and str(payload) == component_key


def _assert_optional_component_references_clear(root: Path, component_key: str) -> None:
    for source_ref in (".maw/releases.yaml", ".maw/repositories.yaml"):
        path = root / source_ref
        if not path.is_file() or path.is_symlink():
            continue
        try:
            payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, yaml.YAMLError) as exc:
            raise ValueError("seed_component_reference_source_invalid") from exc
        if _reference_hit(payload, component_key):
            raise ValueError(f"seed_component_referenced_by_{Path(source_ref).stem.lstrip('.')}")


def plan_component_init(
    root: Path | str,
    *,
    key: str,
    component_type: str,
    name: str | None = None,
    path: str | None = None,
    subproject_ref: str = "default",
    source_root: str = "",
    source_mode: str = "embedded",
    source_ref: str = "",
    repository_url: str = "",
    repository_ref: str = "",
    repository_subpath: str = "",
    default_branch: str = "",
    source_directory: Path | str | None = None,
    source_origin: str = "existing_directory",
    git_access_profile_ref: str = "",
    enabled: bool = False,
    adopt: bool = False,
) -> tuple[dict[str, Any], dict[str, Any]]:
    project_root = _project_root(root)
    component_key = _component_key(key)
    kind = _component_type(component_type)
    display_name = (name or component_key).strip()
    if not display_name or len(display_name) > MAX_TEXT_LENGTH:
        raise ValueError("seed_component_name_invalid")
    relative, target = _component_path(project_root, component_key, path)
    mode = _source_mode(source_mode)
    projection = compile_project_definition(project_root)
    if projection.get("status") != "ready" or not projection.get("editable"):
        raise ValueError("seed_component_project_not_editable")
    subproject_key = _component_key(subproject_ref or "default")
    subprojects = projection.get("configs", {}).get(".maw/subprojects.yaml", {}).get("subprojects", [])
    if subproject_key not in {
        str(item.get("key")) for item in subprojects if isinstance(item, dict)
    }:
        raise ValueError("seed_component_subproject_missing")
    repository_key = _component_key(repository_ref) if repository_ref else ""
    stable_source_ref = source_ref.strip() or (
        f"mawsource://code-source/{repository_key}"
        if repository_key
        else f"mawsource://component/{component_key}"
    )
    binding_values: dict[str, Any] | None = None
    if mode == "embedded":
        if source_ref or repository_ref or repository_url or repository_subpath or default_branch or source_directory is not None or git_access_profile_ref:
            raise ValueError("seed_component_embedded_source_fields_forbidden")
    else:
        expected_source_ref = (
            f"mawsource://code-source/{repository_key}"
            if repository_key
            else f"mawsource://component/{component_key}"
        )
        if stable_source_ref != expected_source_ref:
            raise ValueError("seed_component_source_ref_mismatch")
        if repository_key:
            registered = _code_source_map(projection).get(repository_key)
            if registered is None:
                raise ValueError("seed_component_code_source_missing")
            if repository_url or default_branch or source_directory is not None or git_access_profile_ref:
                raise ValueError("seed_component_shared_source_fields_forbidden")
            effective_repository_url = str(registered.get("repository_url") or "")
        else:
            effective_repository_url = repository_url
        repository_identity = _repository_identity(effective_repository_url)
        if source_origin not in {"existing_directory", "managed_clone"}:
            raise ValueError("seed_component_source_origin_invalid")
        if source_directory is not None:
            directory, repository_identity = _validate_external_directory(
                source_directory,
                repository_url=effective_repository_url,
                repository_subpath=repository_subpath,
                project_root=project_root,
            )
            binding_values = {
                "source_ref": stable_source_ref,
                "directory_path": str(directory),
                "origin": source_origin,
                "git_access_profile_ref": git_access_profile_ref.strip(),
                "bound_repository_identity": repository_identity,
                "bound_at": datetime.now(timezone.utc).isoformat(),
            }
    if component_key in _component_map(projection):
        raise ValueError("seed_component_exists")
    if adopt:
        if not target.is_dir():
            raise ValueError("seed_component_adopt_directory_required")
    elif target.exists():
        raise ValueError("seed_component_init_target_exists_use_adopt")

    descriptor_ref = f"{relative}/.maw.component.yaml"
    readme_ref = f"{relative}/README.md"
    desired_descriptor = _descriptor(component_key, display_name, kind, relative)
    file_writes: list[dict[str, Any]] = []
    descriptor_path = project_root / descriptor_ref
    if descriptor_path.exists():
        existing = yaml.safe_load(descriptor_path.read_text(encoding="utf-8"))
        component = existing.get("component") if isinstance(existing, dict) else None
        if not isinstance(component, dict) or component.get("key") != component_key or component.get("local_path") != relative:
            raise ValueError("seed_component_descriptor_conflict")
    else:
        file_writes.append(_file_write(project_root, descriptor_ref, desired_descriptor))
    if not (project_root / readme_ref).exists():
        file_writes.append(
            _file_write(
                project_root,
                readme_ref,
                _readme(component_key, display_name, kind, bool(enabled)),
            )
        )

    component_values: dict[str, Any] = {
        "app_key": component_key,
        "name": display_name,
        "type": kind,
        "path": relative,
        "subproject_ref": subproject_key,
        "source_root": source_root.strip(),
        "enabled": bool(enabled),
        "guide": readme_ref,
    }
    if mode == "external_git":
        component_values.update({"source.mode": mode, "source.ref": stable_source_ref})
        if repository_key:
            component_values.update(
                {
                    "source.repository_ref": repository_key,
                    "source.repository_subpath": repository_subpath.strip(),
                }
            )
        else:
            component_values.update(
                {
                    "source.repository_url": repository_url.strip(),
                    "source.repository_subpath": repository_subpath.strip(),
                    "source.default_branch": default_branch.strip(),
                }
            )
    operations: list[dict[str, Any]] = [
        {
            "op": "component.add",
            "key": component_key,
            "scope": "shared",
            "values": component_values,
        }
    ]
    if binding_values is not None:
        operations.append(
            {
                "op": "component_source_binding.upsert",
                "key": component_key,
                "scope": "local",
                "values": binding_values,
            }
        )
    change_public, change_private = plan_change_set(
        project_root,
        {
            "schema": "mawflow.seed_change_set.v2",
            "base_projection_fingerprint": projection["fingerprint"],
            "base_contract_fingerprint": contract_fingerprint(),
            "reason": f"{'采纳' if adopt else '初始化'}组件 {component_key}",
            "operations": operations,
        },
    )
    public = {
        "schema": "mawflow.component_plan.v1",
        "action": "adopt" if adopt else "init",
        "component": {
            "key": component_key,
            "name": display_name,
            "type": kind,
            "path": relative,
            "subproject_ref": subproject_key,
            "enabled": bool(enabled),
            "source_mode": mode,
            "source_ref": stable_source_ref if mode == "external_git" else "",
            "directory_bound": binding_values is not None,
        },
        "plan_key": change_public["plan_key"],
        "confirmation_required": change_public["confirmation_required"],
        "expires_at": change_public["expires_at"],
        "config_writes": change_public["writes"],
        "file_writes": [
            {key: write[key] for key in ("source_ref", "expected_hash", "proposed_hash", "existed")}
            for write in file_writes
        ],
    }
    return public, {**public, "seed_change_plan": change_private, "private_file_writes": file_writes}


def plan_component_source_binding(
    root: Path | str,
    *,
    key: str,
    directory_path: Path | str,
    git_access_profile_ref: str = "",
    origin: str = "existing_directory",
) -> tuple[dict[str, Any], dict[str, Any]]:
    project_root = _project_root(root)
    component_key = _component_key(key)
    projection = compile_project_definition(project_root)
    if projection.get("status") != "ready" or not projection.get("editable"):
        raise ValueError("seed_component_project_not_editable")
    component = _component_map(projection).get(component_key)
    if component is None:
        raise ValueError("seed_component_missing")
    source = _external_source(component_key, component)
    if origin not in {"existing_directory", "managed_clone"}:
        raise ValueError("seed_component_source_origin_invalid")
    directory, repository_identity = _validate_external_directory(
        directory_path,
        repository_url=str(source.get("repository_url") or ""),
        repository_subpath=str(source.get("repository_subpath") or ""),
        project_root=project_root,
    )
    change_public, change_private = plan_change_set(
        project_root,
        {
            "schema": "mawflow.seed_change_set.v2",
            "base_projection_fingerprint": projection["fingerprint"],
            "base_contract_fingerprint": contract_fingerprint(),
            "reason": f"绑定组件 {component_key} 的本机外部源码目录",
            "operations": [
                {
                    "op": "component_source_binding.upsert",
                    "key": component_key,
                    "scope": "local",
                    "values": {
                        "source_ref": source["ref"],
                        "directory_path": str(directory),
                        "origin": origin,
                        "git_access_profile_ref": git_access_profile_ref.strip(),
                        "bound_repository_identity": repository_identity,
                        "bound_at": datetime.now(timezone.utc).isoformat(),
                    },
                }
            ],
        },
    )
    public = {
        "schema": "mawflow.component_plan.v1",
        "action": "source_bind",
        "component": {
            "key": component_key,
            "source_ref": source["ref"],
            "directory_path": str(directory),
            "origin": origin,
            "git_access_profile_ref": git_access_profile_ref.strip(),
        },
        "plan_key": change_public["plan_key"],
        "confirmation_required": change_public["confirmation_required"],
        "expires_at": change_public["expires_at"],
        "config_writes": change_public["writes"],
        "file_writes": [],
    }
    return public, {**public, "seed_change_plan": change_private, "private_file_writes": []}


def plan_component_source_unbind(root: Path | str, *, key: str) -> tuple[dict[str, Any], dict[str, Any]]:
    project_root = _project_root(root)
    component_key = _component_key(key)
    projection = compile_project_definition(project_root)
    if component_key not in _component_map(projection):
        raise ValueError("seed_component_missing")
    if component_key not in _binding_map(projection):
        raise ValueError("seed_component_source_binding_missing")
    change_public, change_private = plan_change_set(
        project_root,
        {
            "schema": "mawflow.seed_change_set.v2",
            "base_projection_fingerprint": projection["fingerprint"],
            "base_contract_fingerprint": contract_fingerprint(),
            "reason": f"解绑组件 {component_key} 的本机外部源码目录",
            "operations": [
                {
                    "op": "component_source_binding.remove",
                    "key": component_key,
                    "scope": "local",
                    "values": {},
                }
            ],
        },
    )
    public = {
        "schema": "mawflow.component_plan.v1",
        "action": "source_unbind",
        "component": {"key": component_key, "source_directory_action": "retained"},
        "plan_key": change_public["plan_key"],
        "confirmation_required": change_public["confirmation_required"],
        "expires_at": change_public["expires_at"],
        "config_writes": change_public["writes"],
        "file_writes": [],
    }
    return public, {**public, "seed_change_plan": change_private, "private_file_writes": []}


def plan_component_remove(root: Path | str, *, key: str) -> tuple[dict[str, Any], dict[str, Any]]:
    project_root = _project_root(root)
    component_key = _component_key(key)
    projection = compile_project_definition(project_root)
    component = _component_map(projection).get(component_key)
    if component is None:
        raise ValueError("seed_component_missing")
    _assert_optional_component_references_clear(project_root, component_key)
    modules = projection.get("configs", {}).get(".maw/modules.yaml", {}).get("modules", [])
    if any(component_key in item.get("component_refs", []) for item in modules if isinstance(item, dict)):
        raise ValueError("seed_component_referenced_by_module")
    operations: list[dict[str, Any]] = []
    apps = projection.get("configs", {}).get(".maw/app-runtime.yaml", {}).get("app_runtime", {}).get("apps", {})
    for app_key, app in (apps.items() if isinstance(apps, dict) else []):
        if isinstance(app, dict) and app.get("component_ref") == component_key:
            operations.append(
                {"op": "runtime.app.remove", "key": str(app_key), "scope": "shared", "values": {}}
            )
    if component_key in _binding_map(projection):
        operations.append(
            {"op": "component_source_binding.remove", "key": component_key, "scope": "local", "values": {}}
        )
    operations.append({"op": "component.remove", "key": component_key, "scope": "shared", "values": {}})
    change_public, change_private = plan_change_set(
        project_root,
        {
            "schema": "mawflow.seed_change_set.v2",
            "base_projection_fingerprint": projection["fingerprint"],
            "base_contract_fingerprint": contract_fingerprint(),
            "reason": f"从项目注销组件 {component_key}，保留磁盘源码目录",
            "operations": operations,
        },
    )
    public = {
        "schema": "mawflow.component_plan.v1",
        "action": "remove",
        "component": {
            "key": component_key,
            "path": component.get("path"),
            "source_mode": str((component.get("source") or {}).get("mode") or "embedded") if isinstance(component.get("source") or {}, dict) else "embedded",
            "source_directory_action": "retained",
        },
        "plan_key": change_public["plan_key"],
        "confirmation_required": change_public["confirmation_required"],
        "expires_at": change_public["expires_at"],
        "config_writes": change_public["writes"],
        "file_writes": [],
    }
    return public, {**public, "seed_change_plan": change_private, "private_file_writes": []}


def plan_component_state(root: Path | str, *, key: str, enabled: bool) -> tuple[dict[str, Any], dict[str, Any]]:
    project_root = _project_root(root)
    component_key = _component_key(key)
    projection = compile_project_definition(project_root)
    component = _component_map(projection).get(component_key)
    if component is None:
        raise ValueError("seed_component_missing")
    _, target = _component_path(project_root, component_key, str(component.get("path") or ""))
    if enabled and (not target.is_dir() or not (target / ".maw.component.yaml").is_file()):
        raise ValueError("seed_component_enable_requires_initialized_directory")
    operations: list[dict[str, Any]] = []
    if component.get("enabled") is not enabled:
        operations.append(
            {
                "op": "component.enable" if enabled else "component.disable",
                "key": component_key,
                "scope": "shared",
                "values": {"enabled": enabled},
            }
        )
    apps = projection.get("configs", {}).get(".maw/app-runtime.yaml", {}).get("app_runtime", {}).get("apps", {})
    for app_key, app in apps.items():
        if isinstance(app, dict) and app.get("component_ref") == component_key and app.get("enabled") is not enabled:
            operations.append(
                {
                    "op": "runtime.app.upsert",
                    "key": str(app_key),
                    "scope": "shared",
                    "values": {"enabled": enabled},
                }
            )
    if not operations:
        raise ValueError("seed_component_state_unchanged")
    change_public, change_private = plan_change_set(
        project_root,
        {
            "schema": "mawflow.seed_change_set.v2",
            "base_projection_fingerprint": projection["fingerprint"],
            "base_contract_fingerprint": contract_fingerprint(),
            "reason": f"{'启用' if enabled else '禁用'}组件 {component_key}",
            "operations": operations,
        },
    )
    public = {
        "schema": "mawflow.component_plan.v1",
        "action": "enable" if enabled else "disable",
        "component": {"key": component_key, "enabled": enabled},
        "plan_key": change_public["plan_key"],
        "confirmation_required": change_public["confirmation_required"],
        "expires_at": change_public["expires_at"],
        "config_writes": change_public["writes"],
        "file_writes": [],
    }
    return public, {**public, "seed_change_plan": change_private, "private_file_writes": []}


def apply_component_plan(
    root: Path | str,
    plan: dict[str, Any],
    confirmation: str,
    *,
    backup_root: Path | str,
) -> dict[str, Any]:
    project_root = _project_root(root)
    if plan.get("schema") != "mawflow.component_plan.v1" or confirmation != plan.get("confirmation_required"):
        raise ValueError("seed_component_confirmation_required")
    seed_plan = plan.get("seed_change_plan")
    file_writes = plan.get("private_file_writes")
    if not isinstance(seed_plan, dict) or not isinstance(file_writes, list):
        raise ValueError("seed_component_private_plan_required")
    component_backup = Path(backup_root).expanduser().resolve() / f"{plan['plan_key']}-component-files"
    component_backup.mkdir(parents=True, exist_ok=False)
    written: list[Path] = []
    try:
        for write in file_writes:
            path = project_root / str(write["source_ref"])
            if path.is_symlink():
                raise ValueError("seed_component_symlink_forbidden")
            exists = path.exists()
            current = path.read_text(encoding="utf-8") if exists and path.is_file() else ""
            if exists != bool(write["existed"]) or _hash(current) != write["expected_hash"]:
                raise ValueError("seed_component_file_conflict")
            if exists:
                backup = component_backup / str(write["source_ref"])
                _atomic_write(backup, current, 0o600)
            _atomic_write(path, str(write["proposed_text"]), int(write["mode"]))
            written.append(path)
        result = apply_change_plan(
            project_root,
            seed_plan,
            confirmation,
            backup_root=backup_root,
        )
    except Exception:
        for write in reversed(file_writes):
            path = project_root / str(write["source_ref"])
            if write["existed"]:
                _atomic_write(path, str(write["original_text"]), int(write["mode"]))
            elif path.exists():
                path.unlink()
        for directory in sorted({path.parent for path in written}, key=lambda item: len(item.parts), reverse=True):
            if directory != project_root and directory.exists() and not any(directory.iterdir()):
                directory.rmdir()
        shutil.rmtree(component_backup, ignore_errors=True)
        raise
    return {
        "schema": "mawflow.component_apply_result.v1",
        "status": "applied",
        "action": plan["action"],
        "component": plan["component"],
        "change": result,
        "applied_at": datetime.now(timezone.utc).isoformat(),
    }


def inspect_components(root: Path | str, key: str | None = None) -> dict[str, Any]:
    project_root = _project_root(root)
    projection = compile_project_definition(project_root)
    components = _component_map(projection)
    bindings = _binding_map(projection)
    code_sources = _code_source_map(projection)
    code_source_bindings = _code_source_binding_map(projection)
    if key is not None:
        selected = _component_key(key)
        if selected not in components:
            raise ValueError("seed_component_missing")
        components = {selected: components[selected]}
    records: list[dict[str, Any]] = []
    total_errors = 0
    for component_key, component in components.items():
        issues: list[dict[str, str]] = []
        try:
            relative, target = _component_path(project_root, component_key, str(component.get("path") or ""))
        except ValueError as exc:
            relative, target = str(component.get("path") or ""), project_root
            issues.append({"severity": "error", "code": str(exc)})
        descriptor = target / ".maw.component.yaml"
        if not target.is_dir():
            issues.append({"severity": "error", "code": "seed_component_directory_missing"})
        elif not descriptor.is_file():
            issues.append({"severity": "error", "code": "seed_component_descriptor_missing"})
        else:
            try:
                payload = yaml.safe_load(descriptor.read_text(encoding="utf-8"))
                detail = payload.get("component") if isinstance(payload, dict) else None
                if not isinstance(detail, dict) or detail.get("key") != component_key or detail.get("local_path") != relative:
                    issues.append({"severity": "error", "code": "seed_component_descriptor_mismatch"})
            except (OSError, UnicodeError, yaml.YAMLError):
                issues.append({"severity": "error", "code": "seed_component_descriptor_invalid"})
        source = component.get("source") if isinstance(component.get("source"), dict) else {}
        mode = str(source.get("mode") or "embedded")
        source_status: dict[str, Any] = {
            "mode": mode,
            "source_ref": str(source.get("ref") or ""),
            "repository_identity": "",
            "repository_subpath": str(source.get("repository_subpath") or ""),
            "default_branch": str(source.get("default_branch") or ""),
            "directory_path": "",
            "origin": "",
            "git_access_profile_ref": "",
        }
        readiness = "embedded_ready"
        if mode == "external_git":
            repository_ref = str(source.get("repository_ref") or "")
            registered = code_sources.get(repository_ref) if repository_ref else None
            repository_url = str(
                (registered or {}).get("repository_url")
                or source.get("repository_url")
                or ""
            )
            source_status["repository_ref"] = repository_ref
            if registered:
                source_status["default_branch"] = str(registered.get("default_branch") or "")
            try:
                source_status["repository_identity"] = _repository_identity(repository_url)
            except ValueError as exc:
                issues.append({"severity": "error", "code": str(exc)})
            binding = (
                code_source_bindings.get(repository_ref)
                if repository_ref
                else bindings.get(component_key)
            )
            if binding is None:
                issues.append({"severity": "error", "code": "seed_component_source_unbound"})
                readiness = "unbound"
            else:
                directory_text = str(binding.get("directory_path") or "")
                source_status.update(
                    {
                        "directory_path": directory_text,
                        "origin": str(binding.get("origin") or ""),
                        "git_access_profile_ref": str(binding.get("git_access_profile_ref") or ""),
                    }
                )
                directory = Path(directory_text).expanduser()
                if not directory.is_dir() or directory.is_symlink():
                    issues.append({"severity": "error", "code": "seed_component_source_directory_missing"})
                    readiness = "directory_missing"
                else:
                    try:
                        validated, repository_identity = _validate_external_directory(
                            directory,
                            repository_url=repository_url,
                            repository_subpath=str(source.get("repository_subpath") or ""),
                            project_root=project_root,
                        )
                        source_status["directory_path"] = str(validated)
                        source_status["repository_identity"] = repository_identity
                        source_status["head"] = _git_output(validated, "rev-parse", "HEAD")
                        source_status["branch"] = _git_output(validated, "branch", "--show-current")
                        source_status["dirty"] = bool(_git_output(validated, "status", "--porcelain"))
                        source_root = str(component.get("source_root") or "")
                        repository_subpath = str(source.get("repository_subpath") or "")
                        effective_root = validated
                        for relative_source in (repository_subpath, source_root):
                            if relative_source:
                                effective_root /= relative_source
                        if not effective_root.is_dir():
                            issues.append({"severity": "error", "code": "seed_component_source_root_missing"})
                            readiness = "source_subpath_missing"
                        else:
                            readiness = "external_ready"
                    except ValueError as exc:
                        code = str(exc)
                        issues.append({"severity": "error", "code": code})
                        readiness = (
                            "repository_mismatch"
                            if code == "seed_component_source_repository_mismatch"
                            else "source_subpath_missing"
                            if code == "seed_component_source_subpath_missing"
                            else "attention_required"
                        )
        elif mode != "embedded":
            issues.append({"severity": "error", "code": "seed_component_source_mode_invalid"})
            readiness = "attention_required"
        error_count = len([item for item in issues if item["severity"] == "error"])
        total_errors += error_count
        source_status["status"] = (
            readiness
            if error_count == 0 or readiness not in {"embedded_ready", "external_ready"}
            else "attention_required"
        )
        records.append(
            {
                **component,
                "source": source_status,
                "issues": issues,
                "status": "ready" if error_count == 0 else "needs_attention",
            }
        )
    return {
        "schema": "mawflow.component_inspection.v1",
        "status": "ready" if total_errors == 0 else "needs_attention",
        "summary": {"components": len(records), "errors": total_errors},
        "components": records,
    }


__all__ = [
    "apply_component_plan",
    "inspect_components",
    "plan_component_init",
    "plan_component_remove",
    "plan_component_source_binding",
    "plan_component_source_unbind",
    "plan_component_state",
]
