from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import re
import shutil
import stat
import tempfile
from typing import Any

import yaml

from .catalog import catalog, contract_fingerprint
from .changes import apply_change_plan, plan_change_set
from .compiler import compile_project_definition


KEY_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{0,159}$")
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


def plan_component_init(
    root: Path | str,
    *,
    key: str,
    component_type: str,
    name: str | None = None,
    path: str | None = None,
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
    projection = compile_project_definition(project_root)
    if projection.get("status") != "ready" or not projection.get("editable"):
        raise ValueError("seed_component_project_not_editable")
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

    change_public, change_private = plan_change_set(
        project_root,
        {
            "schema": "mawflow.seed_change_set.v2",
            "base_projection_fingerprint": projection["fingerprint"],
            "base_contract_fingerprint": contract_fingerprint(),
            "reason": f"{'采纳' if adopt else '初始化'}组件 {component_key}",
            "operations": [
                {
                    "op": "component.add",
                    "key": component_key,
                    "scope": "shared",
                    "values": {
                        "app_key": component_key,
                        "name": display_name,
                        "type": kind,
                        "path": relative,
                        "source_root": "",
                        "enabled": bool(enabled),
                        "guide": readme_ref,
                    },
                }
            ],
        },
    )
    public = {
        "schema": "mawflow.component_plan.v1",
        "action": "adopt" if adopt else "init",
        "component": {"key": component_key, "name": display_name, "type": kind, "path": relative, "enabled": bool(enabled)},
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
        total_errors += len([item for item in issues if item["severity"] == "error"])
        records.append({**component, "issues": issues, "status": "ready" if not issues else "needs_attention"})
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
    "plan_component_state",
]
