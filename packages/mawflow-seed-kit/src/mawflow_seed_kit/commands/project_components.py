from __future__ import annotations

import json
from pathlib import Path
import shlex
from typing import Any

from mawflow_seed_kit import (
    apply_component_plan,
    inspect_components,
    plan_component_init,
    plan_component_remove,
    plan_component_source_binding,
    plan_component_source_unbind,
    plan_component_state,
)


COMPONENT_PLAN_SCHEMA = "mawflow.host_component_result.v1"


def _root(value: Path | str) -> Path:
    root = Path(value).expanduser().resolve(strict=True)
    if not (root / ".maw/project.yaml").is_file():
        raise ValueError("mawflow_project_required")
    return root


def _plan_path(root: Path, value: Path | str | None) -> Path:
    if value:
        path = Path(value).expanduser()
        return path.resolve() if path.is_absolute() else (Path.cwd() / path).resolve()
    return root / ".local/.maw/component-plan.json"


def _backup_root(root: Path) -> Path:
    return root / ".local/.maw/component-backups"


def _save_plan(path: Path, plan: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    path.chmod(0o600)


def _load_plan(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError("component_plan_file_missing") from exc
    except json.JSONDecodeError as exc:
        raise ValueError("component_plan_file_invalid") from exc
    if not isinstance(payload, dict) or payload.get("schema") != "mawflow.component_plan.v1":
        raise ValueError("component_plan_file_invalid")
    return payload


def _public(plan: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in plan.items()
        if key not in {"seed_change_plan", "private_file_writes"}
    }


def _execute_command(root: Path, path: Path, confirmation: str) -> str:
    return " ".join(
        shlex.quote(item)
        for item in [
            "mawflow",
            "component",
            "apply",
            "--root",
            str(root),
            "--execute",
            "--plan-file",
            str(path),
            "--confirm",
            confirmation,
        ]
    )


def _finish_plan(
    root: Path,
    public: dict[str, Any],
    private: dict[str, Any],
    *,
    preview_only: bool,
    plan_file: Path | str | None,
) -> dict[str, Any]:
    path = _plan_path(root, plan_file)
    _save_plan(path, private)
    if preview_only:
        confirmation = str(public["confirmation_required"])
        return {
            **public,
            "schema": COMPONENT_PLAN_SCHEMA,
            "status": "planned",
            "plan_file": str(path),
            "next_command": _execute_command(root, path, confirmation),
        }
    result = apply_component_plan(
        root,
        private,
        str(public["confirmation_required"]),
        backup_root=_backup_root(root),
    )
    path.unlink(missing_ok=True)
    return {**result, "schema": COMPONENT_PLAN_SCHEMA, "plan_file": str(path)}


def component_init(
    root: Path | str,
    *,
    key: str,
    component_type: str = "custom",
    name: str = "",
    path: str = "",
    subproject_ref: str = "default",
    source_root: str = "",
    source_mode: str = "embedded",
    repository_url: str = "",
    repository_ref: str = "",
    repository_subpath: str = "",
    default_branch: str = "",
    source_directory: Path | str | None = None,
    source_origin: str = "existing_directory",
    git_access_profile_ref: str = "",
    enabled: bool = False,
    adopt: bool = False,
    preview_only: bool = False,
    plan_file: Path | str | None = None,
) -> dict[str, Any]:
    project_root = _root(root)
    public, private = plan_component_init(
        project_root,
        key=key,
        component_type=component_type,
        name=name or None,
        path=path or None,
        subproject_ref=subproject_ref,
        source_root=source_root,
        source_mode=source_mode,
        repository_url=repository_url,
        repository_ref=repository_ref,
        repository_subpath=repository_subpath,
        default_branch=default_branch,
        source_directory=source_directory,
        source_origin=source_origin,
        git_access_profile_ref=git_access_profile_ref,
        enabled=enabled,
        adopt=adopt,
    )
    return _finish_plan(
        project_root,
        public,
        private,
        preview_only=preview_only,
        plan_file=plan_file,
    )


def component_state(
    root: Path | str,
    *,
    key: str,
    enabled: bool,
    preview_only: bool = False,
    plan_file: Path | str | None = None,
) -> dict[str, Any]:
    project_root = _root(root)
    try:
        public, private = plan_component_state(project_root, key=key, enabled=enabled)
    except ValueError as exc:
        if str(exc) != "seed_component_state_unchanged":
            raise
        inspection = inspect_components(project_root, key)
        return {
            "schema": COMPONENT_PLAN_SCHEMA,
            "status": "unchanged",
            "action": "enable" if enabled else "disable",
            "component": inspection["components"][0],
        }
    return _finish_plan(
        project_root,
        public,
        private,
        preview_only=preview_only,
        plan_file=plan_file,
    )


def component_source_bind(
    root: Path | str,
    *,
    key: str,
    directory_path: Path | str,
    git_access_profile_ref: str = "",
    origin: str = "existing_directory",
    preview_only: bool = False,
    plan_file: Path | str | None = None,
) -> dict[str, Any]:
    project_root = _root(root)
    public, private = plan_component_source_binding(
        project_root,
        key=key,
        directory_path=directory_path,
        git_access_profile_ref=git_access_profile_ref,
        origin=origin,
    )
    return _finish_plan(
        project_root,
        public,
        private,
        preview_only=preview_only,
        plan_file=plan_file,
    )


def component_source_unbind(
    root: Path | str,
    *,
    key: str,
    preview_only: bool = False,
    plan_file: Path | str | None = None,
) -> dict[str, Any]:
    project_root = _root(root)
    public, private = plan_component_source_unbind(project_root, key=key)
    return _finish_plan(
        project_root,
        public,
        private,
        preview_only=preview_only,
        plan_file=plan_file,
    )


def component_remove(
    root: Path | str,
    *,
    key: str,
    preview_only: bool = False,
    plan_file: Path | str | None = None,
) -> dict[str, Any]:
    project_root = _root(root)
    public, private = plan_component_remove(project_root, key=key)
    return _finish_plan(
        project_root,
        public,
        private,
        preview_only=preview_only,
        plan_file=plan_file,
    )


def component_apply(
    root: Path | str,
    *,
    confirmation: str,
    plan_file: Path | str | None = None,
) -> dict[str, Any]:
    project_root = _root(root)
    path = _plan_path(project_root, plan_file)
    plan = _load_plan(path)
    result = apply_component_plan(
        project_root,
        plan,
        confirmation,
        backup_root=_backup_root(project_root),
    )
    path.unlink(missing_ok=True)
    return {**result, "schema": COMPONENT_PLAN_SCHEMA, "plan_file": str(path)}


def component_inspect(root: Path | str, key: str | None = None) -> dict[str, Any]:
    return inspect_components(_root(root), key)


__all__ = [
    "component_apply",
    "component_init",
    "component_inspect",
    "component_remove",
    "component_source_bind",
    "component_source_unbind",
    "component_state",
]
