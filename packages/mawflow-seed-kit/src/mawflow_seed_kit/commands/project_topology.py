from __future__ import annotations

import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
from typing import Any, Callable

from mawflow_seed_kit import (
    apply_component_plan,
    apply_topology_plan,
    default_managed_clone_path,
    inspect_project_sources,
    plan_code_source_binding,
    plan_code_source_remove,
    plan_code_source_unbind,
    plan_code_source_upsert,
    plan_component_source_binding,
    plan_source_registry_consolidation,
    plan_subproject_remove,
    plan_subproject_upsert,
)


CloneEnvFactory = Callable[[str, str], dict[str, str]]


def _root(value: Path | str) -> Path:
    root = Path(value).expanduser().resolve(strict=True)
    if not (root / ".maw/project.yaml").is_file():
        raise ValueError("mawflow_project_required")
    return root


def _backup_root(root: Path) -> Path:
    return root / ".local/.maw/topology-backups"


def topology_plan_path(root: Path | str, value: Path | str | None = None) -> Path:
    project_root = _root(root)
    if value:
        path = Path(value).expanduser()
        return path.resolve() if path.is_absolute() else (Path.cwd() / path).resolve()
    return project_root / ".local/.maw/topology-plan.json"


def save_topology_plan(root: Path | str, plan: dict[str, Any], path: Path | str | None = None) -> Path:
    target = topology_plan_path(root, path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    target.chmod(0o600)
    return target


def load_topology_plan(root: Path | str, path: Path | str | None = None) -> dict[str, Any]:
    target = topology_plan_path(root, path)
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError("project_topology_plan_missing") from exc
    except json.JSONDecodeError as exc:
        raise ValueError("project_topology_plan_invalid") from exc
    if not isinstance(payload, dict) or payload.get("schema") != "mawflow.seed_change_plan.v2":
        raise ValueError("project_topology_plan_invalid")
    return payload


def apply_saved_topology_plan(
    root: Path | str,
    *,
    confirmation: str,
    plan_file: Path | str | None = None,
) -> dict[str, Any]:
    project_root = _root(root)
    path = topology_plan_path(project_root, plan_file)
    plan = load_topology_plan(project_root, path)
    result = apply_topology_plan(
        project_root,
        plan,
        confirmation,
        backup_root=_backup_root(project_root),
    )
    path.unlink(missing_ok=True)
    return result


def finish_topology_plan(
    root: Path | str,
    public: dict[str, Any],
    private: dict[str, Any],
    *,
    preview_only: bool,
    plan_file: Path | str | None = None,
) -> dict[str, Any]:
    project_root = _root(root)
    if preview_only:
        path = save_topology_plan(project_root, private, plan_file)
        return {**public, "status": "planned", "plan_file": str(path)}
    return apply_topology_plan(
        project_root,
        private,
        str(public["confirmation_required"]),
        backup_root=_backup_root(project_root),
    )


def _clone(
    *,
    repository_url: str,
    default_branch: str,
    target: Path,
    profile_ref: str,
    clone_env_factory: CloneEnvFactory | None,
) -> None:
    if target.exists() or target.is_symlink():
        raise ValueError("project_hydration_target_conflict")
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.parent / f".{target.name}.maw-hydrate-{secrets.token_hex(6)}"
    command = ["git", "clone"]
    if default_branch:
        command.extend(["--single-branch", "--branch", default_branch])
    command.extend(["--", repository_url, str(temporary)])
    env = (
        clone_env_factory(repository_url, profile_ref)
        if clone_env_factory is not None
        else {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
    )
    try:
        completed = subprocess.run(
            command,
            cwd=str(target.parent),
            env=env,
            check=False,
            capture_output=True,
            text=True,
            timeout=600,
        )
        if completed.returncode != 0:
            message = str(completed.stderr or completed.stdout or "git clone failed").strip()
            raise ValueError(f"project_hydration_clone_failed:{message[-240:]}")
        temporary.replace(target)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary, ignore_errors=True)


def hydrate_project(
    root: Path | str,
    *,
    execute: bool = False,
    source_keys: list[str] | None = None,
    git_access_profile_ref: str = "",
    clone_env_factory: CloneEnvFactory | None = None,
) -> dict[str, Any]:
    project_root = _root(root)
    inspection = inspect_project_sources(project_root)
    selected = set(source_keys or [])
    actions: list[dict[str, Any]] = []
    for item in inspection.get("code_sources", []):
        source_key = str(item.get("key") or "")
        if selected and source_key not in selected:
            continue
        if item.get("status") == "ready":
            continue
        actions.append({
            "kind": "code_source",
            "key": source_key,
            "repository_url": str(item.get("repository_url") or ""),
            "default_branch": str(item.get("default_branch") or ""),
            "target": str(default_managed_clone_path(project_root, source_key)),
            "action": "managed_clone",
        })
    for item in inspection.get("legacy_component_sources", []):
        component_key = str(item.get("component_key") or "")
        if selected and component_key not in selected:
            continue
        if item.get("status") == "bound":
            continue
        actions.append({
            "kind": "legacy_component_source",
            "key": component_key,
            "repository_url": str(item.get("repository_url") or ""),
            "default_branch": "",
            "target": str(default_managed_clone_path(project_root, component_key)),
            "action": "managed_clone",
        })
    if not execute:
        return {
            "schema": "mawflow.project_hydration_plan.v1",
            "status": "ready" if not actions else "planned",
            "actions": actions,
            "default_root": str(project_root / ".local/code-sources"),
            "outer_git_ignore_required": True,
            "source_directories_moved": False,
            "cloud_payload": inspection.get("cloud_summary", {}),
        }
    completed_actions: list[dict[str, Any]] = []
    for action in actions:
        target = Path(str(action["target"]))
        created = False
        try:
            if not target.exists():
                _clone(
                    repository_url=str(action["repository_url"]),
                    default_branch=str(action["default_branch"]),
                    target=target,
                    profile_ref=git_access_profile_ref,
                    clone_env_factory=clone_env_factory,
                )
                created = True
            if action["kind"] == "code_source":
                public, private = plan_code_source_binding(
                    project_root,
                    key=str(action["key"]),
                    directory_path=target,
                    git_access_profile_ref=git_access_profile_ref,
                    origin="managed_clone",
                )
                apply_topology_plan(
                    project_root,
                    private,
                    str(public["confirmation_required"]),
                    backup_root=_backup_root(project_root),
                )
            else:
                public, private = plan_component_source_binding(
                    project_root,
                    key=str(action["key"]),
                    directory_path=target,
                    git_access_profile_ref=git_access_profile_ref,
                    origin="managed_clone",
                )
                apply_component_plan(
                    project_root,
                    private,
                    str(public["confirmation_required"]),
                    backup_root=_backup_root(project_root),
                )
            completed_actions.append({**action, "status": "applied"})
        except Exception:
            if created and target.is_dir() and not target.is_symlink():
                shutil.rmtree(target, ignore_errors=True)
            raise
    result = inspect_project_sources(project_root)
    return {
        "schema": "mawflow.project_hydration_result.v1",
        "status": "applied" if completed_actions else "unchanged",
        "actions": completed_actions,
        "inspection": result,
        "source_directories_moved": False,
    }


__all__ = [
    "apply_saved_topology_plan",
    "finish_topology_plan",
    "hydrate_project",
    "inspect_project_sources",
    "load_topology_plan",
    "plan_code_source_binding",
    "plan_code_source_remove",
    "plan_code_source_unbind",
    "plan_code_source_upsert",
    "plan_source_registry_consolidation",
    "plan_subproject_remove",
    "plan_subproject_upsert",
    "save_topology_plan",
]
