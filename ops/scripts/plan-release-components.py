#!/usr/bin/env python3
"""Plan MAW release components from environment aliases and version state."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))

from ops.lib.maw_config_loader import MawConfigLoader  # noqa: E402


LATEST_REQUIRED_ENVIRONMENTS = {"production"}
DIRTY_ALLOWED_ENVIRONMENTS = {"test", "staging"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Plan publishable MAW components by comparing local commits with per-environment release state.",
    )
    parser.add_argument(
        "target",
        nargs="?",
        help="Environment key or Chinese release phrase, such as test, staging, production, 发布测试, 发布上线, 发布生产.",
    )
    parser.add_argument("--root", default=".", help="Project root. Default: current directory.")
    parser.add_argument("--profile", default=None, help="Config profile. Default: project default.")
    parser.add_argument("--environment", help="Target environment key. Overrides positional target.")
    parser.add_argument("--deployment-target", help="Stable deployment target key from .maw/deployments.yaml.")
    parser.add_argument("--component", action="append", dest="components", help="Limit to an app_key. Repeatable.")
    parser.add_argument("--candidate-commit", help="Commit to release. Default: HEAD.")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--no-local", action="store_true", help="Do not load local config overlays.")
    parser.add_argument("--no-fetch", action="store_true", help="Do not fetch release branch before latest-code checks.")
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Allow dirty-worktree planning for compatible test environments. Production still blocks dirty releases.",
    )
    parser.add_argument(
        "--record-success",
        action="store_true",
        help="After a successful real release, write release-state files for components selected by the plan.",
    )
    parser.add_argument("--record-path", help="Optional release run record path to reference when writing state.")
    return parser


def run_git(args: List[str], root: Path, check: bool = True) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(root),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and proc.returncode != 0:
        detail = proc.stderr.strip() or proc.stdout.strip() or f"git {' '.join(args)} failed"
        raise RuntimeError(detail)
    return proc.stdout.strip()


def git_success(args: List[str], root: Path) -> bool:
    return subprocess.run(
        ["git", *args],
        cwd=str(root),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode == 0


def load_configs(args: argparse.Namespace, root: Path) -> Tuple[Dict[str, Any], ...]:
    loader = MawConfigLoader(
        project_root=root,
        profile=args.profile,
        include_maw_local=not args.no_local,
        include_local_overlay=not args.no_local,
    )
    return (
        loader.load_domain("releases"),
        loader.load_domain("environments"),
        loader.load_domain("components"),
        loader.load_domain("deployments"),
        loader.load_domain("code-sources"),
        loader.load_domain("code-source-bindings"),
    )


def normalize_phrase(value: str) -> str:
    return value.strip().lstrip("#").strip().replace("：", ":")


def resolve_environment(target: str, releases: Dict[str, Any]) -> Tuple[str, Optional[str], Optional[str]]:
    defaults = (releases.get("releases") or {}).get("defaults") or {}
    aliases = defaults.get("release_command_aliases") or {}
    normalized = normalize_phrase(target)

    for alias_key, alias in aliases.items():
        if not isinstance(alias, dict):
            continue
        candidates = [str(alias_key), str(alias.get("environment") or ""), str(alias.get("command") or "")]
        candidates.extend(str(item) for item in (alias.get("phrases") or []))
        if normalized in {normalize_phrase(item) for item in candidates if item}:
            return str(alias.get("environment") or alias_key), str(alias.get("remote_server") or ""), str(alias_key)

    return normalized, None, None


def parse_component_scope(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        result: List[str] = []
        for item in value:
            result.extend(part.strip() for part in str(item).split(",") if part.strip())
        return result
    return [item.strip() for item in str(value).split(",") if item.strip()]


def read_default_components(environments: Dict[str, Any], environment: str) -> List[str]:
    env = (environments.get("environments") or {}).get(environment) or {}
    remote_server = env.get("remote_server") or {}
    return parse_component_scope(remote_server.get("default_release_components"))


def deployment_target_registry(deployments: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    result: Dict[str, Dict[str, Any]] = {}
    for item in deployments.get("deployment_targets") or []:
        if not isinstance(item, dict):
            continue
        key = str(item.get("key") or "").strip()
        if key:
            result[key] = item
    return result


def resolve_deployment_target(
    requested_key: str,
    environment: str,
    environment_role: str,
    deployments: Dict[str, Any],
    environments: Dict[str, Any],
) -> Dict[str, Any]:
    registry = deployment_target_registry(deployments)
    if requested_key:
        target = registry.get(requested_key)
        if target is None:
            raise RuntimeError(f"部署目标 {requested_key} 不存在于 .maw/deployments.yaml")
        return dict(target)
    matches = [
        dict(item)
        for item in registry.values()
        if item.get("enabled", True) is not False
        and str(item.get("environment_key") or "") == environment
    ]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        keys = ", ".join(str(item.get("key")) for item in matches)
        raise RuntimeError(f"环境 {environment} 存在多个部署目标（{keys}）；必须通过 --deployment-target 精确选择")
    legacy_components = read_default_components(environments, environment)
    return {
        "key": f"{environment}-default",
        "name": f"{environment} 兼容部署目标",
        "environment_key": environment,
        "environment_role": environment_role,
        "server_ref": f"legacy://environments/{environment}/remote_server",
        "component_refs": legacy_components,
        "scope_mode": "exclusive",
        "implicit_legacy": True,
    }


def component_registry(components_doc: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    result: Dict[str, Dict[str, Any]] = {}
    for item in components_doc.get("components") or []:
        if not isinstance(item, dict):
            continue
        key = str(item.get("key") or "").strip()
        app_key = str(item.get("app_key") or key).strip()
        if app_key:
            result[app_key] = item
    return result


def component_source_context(
    root: Path,
    component: Dict[str, Any],
    code_sources: Dict[str, Any],
    code_source_bindings: Dict[str, Any],
    outer_candidate: str,
) -> Dict[str, Any]:
    source = component.get("source") if isinstance(component.get("source"), dict) else {}
    if str(source.get("mode") or "embedded") != "external_git":
        return {
            "mode": "embedded",
            "root": root,
            "repository_ref": "project",
            "candidate_commit": outer_candidate,
            "tracked_path": str(component.get("path") or "."),
            "branch": "",
            "dirty": bool(run_git(["status", "--porcelain"], root)),
        }
    repository_ref = str(source.get("repository_ref") or "").strip()
    if not repository_ref:
        return {"mode": "external_git", "status": "blocked", "error": "legacy_external_git_requires_device_binding"}
    registry = code_sources.get("code_sources") if isinstance(code_sources.get("code_sources"), dict) else {}
    bindings = code_source_bindings.get("code_source_bindings") if isinstance(code_source_bindings.get("code_source_bindings"), dict) else {}
    declaration = registry.get(repository_ref) if isinstance(registry.get(repository_ref), dict) else {}
    binding = bindings.get(repository_ref) if isinstance(bindings.get(repository_ref), dict) else {}
    directory_text = str(binding.get("directory_path") or "").strip()
    if not directory_text:
        return {"mode": "external_git", "status": "blocked", "repository_ref": repository_ref, "error": "external_git_source_unbound"}
    source_root = Path(directory_text).expanduser().resolve()
    if not source_root.is_dir() or not git_success(["rev-parse", "--is-inside-work-tree"], source_root):
        return {"mode": "external_git", "status": "blocked", "repository_ref": repository_ref, "error": "external_git_source_not_ready"}
    return {
        "mode": "external_git",
        "status": "ready",
        "root": source_root,
        "repository_ref": repository_ref,
        "repository_url": str(declaration.get("repository_url") or ""),
        "candidate_commit": resolve_commit(source_root, "HEAD"),
        "tracked_path": str(source.get("repository_subpath") or "."),
        "branch": str(declaration.get("default_branch") or source.get("default_branch") or "main"),
        "dirty": bool(run_git(["status", "--porcelain"], source_root)),
    }


def source_latest_check(context: Dict[str, Any], *, required: bool, no_fetch: bool) -> Dict[str, Any]:
    if context.get("status") == "blocked":
        return {"status": "blocked", "message": str(context.get("error") or "源码未就绪")}
    if not required or context.get("mode") != "external_git":
        return {"status": "skipped", "message": "当前源码无需单独远端最新门禁。"}
    source_root = Path(context["root"])
    branch = str(context.get("branch") or "main")
    remote_ref = f"origin/{branch}"
    if not no_fetch:
        fetch = subprocess.run(
            ["git", "fetch", "--prune", "origin", branch],
            cwd=str(source_root),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if fetch.returncode != 0:
            return {"status": "blocked", "message": fetch.stderr.strip() or f"无法 fetch 外部代码源 {remote_ref}"}
    if not git_success(["rev-parse", "--verify", f"{remote_ref}^{{commit}}"], source_root):
        return {"status": "blocked", "message": f"无法解析外部代码源发布分支 {remote_ref}"}
    remote_commit = resolve_commit(source_root, remote_ref)
    if remote_commit != context.get("candidate_commit"):
        return {"status": "blocked", "message": f"外部代码源候选 commit 不等于 {remote_ref}"}
    if context.get("dirty"):
        return {"status": "blocked", "message": "生产部署目标的外部代码源工作区必须干净"}
    return {"status": "ok", "message": f"外部代码源已等于 {remote_ref}", "remote_commit": remote_commit}


def validate_components(
    app_keys: Iterable[str],
    registry: Dict[str, Dict[str, Any]],
    releases: Dict[str, Any],
) -> List[str]:
    errors: List[str] = []
    release_components = ((releases.get("releases") or {}).get("components") or {})
    for app_key in app_keys:
        if app_key not in registry:
            errors.append(f"组件 {app_key} 不存在于 .maw/components.yaml")
        if app_key not in release_components:
            errors.append(f"组件 {app_key} 不存在于 .maw/releases.yaml releases.components")
    return errors


def state_file_path(root: Path, releases: Dict[str, Any], environment: str, deployment_target_key: str, app_key: str) -> Path:
    defaults = (releases.get("releases") or {}).get("defaults") or {}
    tracking = defaults.get("version_tracking") or {}
    state_dir = str(tracking.get("state_dir") or "artifacts/release-state")
    template = str(tracking.get("state_file_template") or "{state_dir}/{environment}/{deployment_target_key}/{app_key}.json")
    path_text = template.format(
        state_dir=state_dir,
        environment=environment,
        deployment_target_key=deployment_target_key,
        app_key=app_key,
    )
    return (root / path_text).resolve()


def legacy_state_file_path(root: Path, releases: Dict[str, Any], environment: str, app_key: str) -> Path:
    defaults = (releases.get("releases") or {}).get("defaults") or {}
    tracking = defaults.get("version_tracking") or {}
    state_dir = str(tracking.get("state_dir") or "artifacts/release-state")
    return (root / state_dir / environment / f"{app_key}.json").resolve()


def read_state(path: Path) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    if not path.exists():
        return None, None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return None, f"无法读取发布状态 {path}: {exc}"
    if not isinstance(data, dict):
        return None, f"发布状态不是对象：{path}"
    return data, None


def deployed_commit_from_state(state: Optional[Dict[str, Any]]) -> str:
    if not state:
        return ""
    for key in ("version_id", "commit", "released_commit"):
        value = str(state.get(key) or "").strip()
        if value:
            return value
    return ""


def resolve_commit(root: Path, commitish: str) -> str:
    return run_git(["rev-parse", "--verify", f"{commitish}^{{commit}}"], root)


def merge_paths(*path_groups: Iterable[str]) -> List[str]:
    seen = set()
    result: List[str] = []
    for group in path_groups:
        for item in group:
            path = str(item).strip()
            if not path or path in seen:
                continue
            seen.add(path)
            result.append(path)
    return result


def tracked_paths_for_component(releases: Dict[str, Any], registry: Dict[str, Dict[str, Any]], app_key: str) -> List[str]:
    defaults = (releases.get("releases") or {}).get("defaults") or {}
    tracking = defaults.get("version_tracking") or {}
    release_components = ((releases.get("releases") or {}).get("components") or {})
    release_app = release_components.get(app_key) or {}
    component = registry.get(app_key) or {}

    source = str(release_app.get("source") or component.get("path") or f"code/{app_key}")
    component_file = f"{source}/.maw.component.yaml"
    overlay = str(release_app.get("overlay") or "")
    overlay_paths = []
    if overlay:
        overlay_paths = [f"{overlay}/default", f"{overlay}/{app_key}"]

    component_tracking = release_app.get("version_tracking") or {}
    configured_component_paths = component_tracking.get("tracked_paths") or []
    shared_paths = tracking.get("shared_tracked_paths") or []

    return merge_paths(
        [source, component_file],
        overlay_paths,
        configured_component_paths,
        shared_paths,
    )


def migration_execution_groups(
    releases: Dict[str, Any], selected_components: List[str]
) -> List[Dict[str, Any]]:
    """Group a shared database/service migration so one target run executes it once."""
    release_components = ((releases.get("releases") or {}).get("components") or {})
    grouped: Dict[str, Dict[str, Any]] = {}
    for app_key in selected_components:
        component = release_components.get(app_key) or {}
        migration = component.get("database_migration") or {}
        if not isinstance(migration, dict) or migration.get("enabled", True) is False:
            continue
        service_ref = str(migration.get("service_ref") or "").strip()
        if not service_ref:
            continue
        group = grouped.setdefault(
            service_ref,
            {
                "service_ref": service_ref,
                "owner_component": app_key,
                "component_refs": [],
                "execute_once": True,
                "strategy": str(migration.get("strategy") or "owner_first"),
            },
        )
        group["component_refs"].append(app_key)
    return list(grouped.values())


def diff_paths(root: Path, old_commit: str, new_commit: str, paths: List[str]) -> List[str]:
    if old_commit == new_commit:
        return []
    output = run_git(["diff", "--name-only", f"{old_commit}..{new_commit}", "--", *paths], root)
    return [line for line in output.splitlines() if line.strip()]


def is_ancestor(root: Path, older: str, newer: str) -> bool:
    return git_success(["merge-base", "--is-ancestor", older, newer], root)


def release_branch_ref(environments: Dict[str, Any], environment: str) -> str:
    env = (environments.get("environments") or {}).get(environment) or {}
    remote_server = env.get("remote_server") or {}
    branch = str(remote_server.get("branch") or "").strip()
    return branch or "main"


def latest_required_environments(releases: Dict[str, Any]) -> set[str]:
    defaults = (releases.get("releases") or {}).get("defaults") or {}
    tracking = defaults.get("version_tracking") or {}
    configured = tracking.get("latest_code_required_environments")
    if configured:
        return {str(item).strip() for item in configured if str(item).strip()}
    return set(LATEST_REQUIRED_ENVIRONMENTS)


def dirty_allowed_environments(releases: Dict[str, Any]) -> set[str]:
    defaults = (releases.get("releases") or {}).get("defaults") or {}
    tracking = defaults.get("version_tracking") or {}
    configured = tracking.get("dirty_worktree_allowed_environments")
    if configured:
        return {str(item).strip() for item in configured if str(item).strip()}
    return set(DIRTY_ALLOWED_ENVIRONMENTS)


def dirty_snapshot_id(root: Path, status_lines: List[str]) -> str:
    diff = run_git(["diff", "--binary", "HEAD"], root, check=False)
    payload = "\n".join(status_lines) + "\n" + diff
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def latest_code_check(
    args: argparse.Namespace,
    root: Path,
    releases: Dict[str, Any],
    environments: Dict[str, Any],
    environment: str,
    environment_role: str,
    candidate: str,
) -> Dict[str, Any]:
    required_environments = latest_required_environments(releases)
    if environment_role != "production" and environment not in required_environments:
        return {
            "required": False,
            "status": "skipped",
            "message": "测试版本不要求本地候选 commit 等于远端发布分支；生产发布才强制检查。",
        }

    branch = release_branch_ref(environments, environment)
    remote = "origin"
    remote_ref = f"{remote}/{branch}"
    result: Dict[str, Any] = {
        "required": True,
        "environment": environment,
        "remote": remote,
        "branch": branch,
        "remote_ref": remote_ref,
        "status": "unknown",
        "message": "",
    }

    if not args.no_fetch:
        fetch = subprocess.run(
            ["git", "fetch", "--prune", remote, branch],
            cwd=str(root),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if fetch.returncode != 0:
            result["status"] = "blocked"
            result["message"] = fetch.stderr.strip() or fetch.stdout.strip() or f"无法 fetch {remote} {branch}"
            return result

    if not git_success(["rev-parse", "--verify", f"{remote_ref}^{{commit}}"], root):
        result["status"] = "blocked"
        result["message"] = f"无法解析发布来源 {remote_ref}；上线/生产发布前必须能确认本地代码最新。"
        return result

    remote_commit = resolve_commit(root, remote_ref)
    result["remote_commit"] = remote_commit
    result["candidate_commit"] = candidate
    if candidate != remote_commit:
        result["status"] = "blocked"
        result["message"] = f"候选 commit 不等于 {remote_ref}；请先更新/合并/推送到发布来源分支后再发布。"
        return result

    result["status"] = "ok"
    result["message"] = f"候选 commit 已等于 {remote_ref}。"
    return result


def worktree_check(args: argparse.Namespace, root: Path, releases: Dict[str, Any], environment: str) -> Dict[str, Any]:
    status = run_git(["status", "--porcelain"], root)
    if not status:
        return {"status": "ok", "message": "工作区干净。", "dirty": False}

    dirty_entries = status.splitlines()
    snapshot_id = dirty_snapshot_id(root, dirty_entries)
    allowed_environments = dirty_allowed_environments(releases)
    if environment in allowed_environments:
        return {
            "status": "warning",
            "message": f"{environment} 是测试版本，允许未提交改动参与发布；发布记录必须写入 dirty snapshot。",
            "dirty": True,
            "dirty_allowed": True,
            "dirty_snapshot_id": snapshot_id,
            "dirty_entries": dirty_entries,
        }

    if status:
        return {
            "status": "blocked",
            "message": f"{environment} 不允许发布未提交改动；生产发布前请先提交、推送或清理工作区。",
            "dirty": True,
            "dirty_allowed": False,
            "dirty_snapshot_id": snapshot_id,
            "dirty_entries": dirty_entries,
        }


def plan_component(
    root: Path,
    releases: Dict[str, Any],
    registry: Dict[str, Dict[str, Any]],
    environment: str,
    deployment_target_key: str,
    app_key: str,
    candidate: str,
    source_context: Dict[str, Any],
    scope_fingerprint: str,
) -> Dict[str, Any]:
    state_path = state_file_path(root, releases, environment, deployment_target_key, app_key)
    legacy_state_path = legacy_state_file_path(root, releases, environment, app_key)
    if not state_path.exists() and legacy_state_path.exists():
        state_path_for_read = legacy_state_path
    else:
        state_path_for_read = state_path
    state, state_error = read_state(state_path_for_read)
    deployed_commitish = str((state or {}).get("source_commit") or deployed_commit_from_state(state))
    component_candidate = str(source_context.get("candidate_commit") or candidate)
    paths = (
        [str(source_context.get("tracked_path") or ".")]
        if source_context.get("mode") == "external_git"
        else tracked_paths_for_component(releases, registry, app_key)
    )
    item: Dict[str, Any] = {
        "app_key": app_key,
        "environment": environment,
        "deployment_target_key": deployment_target_key,
        "candidate_commit": component_candidate,
        "definition_commit": candidate,
        "source_mode": source_context.get("mode"),
        "source_repository_ref": source_context.get("repository_ref"),
        "scope_fingerprint": scope_fingerprint,
        "state_file": str(state_path.relative_to(root)),
        "legacy_state_file_read": str(legacy_state_path.relative_to(root)) if state_path_for_read == legacy_state_path else "",
        "deployed_commit": deployed_commitish,
        "tracked_paths": paths,
        "changed_paths": [],
        "decision": "unknown",
        "reason": "",
    }

    if state_error:
        item["decision"] = "blocked"
        item["reason"] = state_error
        return item

    if source_context.get("status") == "blocked":
        item["decision"] = "blocked"
        item["reason"] = str(source_context.get("error") or "组件源码未就绪")
        return item

    if not deployed_commitish:
        item["decision"] = "include"
        item["reason"] = "目标环境没有该组件发布版本记录。"
        return item

    try:
        deployed = resolve_commit(Path(source_context.get("root") or root), deployed_commitish)
    except RuntimeError as exc:
        if state_path_for_read == legacy_state_path and source_context.get("mode") == "external_git":
            item["decision"] = "include"
            item["reason"] = "旧版状态只记录外层仓库 commit；外部代码源首次按目标范围建立独立状态。"
            return item
        item["decision"] = "blocked"
        item["reason"] = f"发布状态中的 commit 无法在对应源码仓库解析：{exc}"
        return item

    item["deployed_commit"] = deployed
    if deployed == component_candidate:
        if str((state or {}).get("scope_fingerprint") or "") == scope_fingerprint:
            item["decision"] = "skip"
            item["reason"] = "目标环境已是候选 commit，且部署范围未变化。"
        else:
            item["decision"] = "include"
            item["reason"] = "源码 commit 未变化，但部署目标、服务器、组件范围或策略发生变化。"
        return item

    source_root = Path(source_context.get("root") or root)
    if is_ancestor(source_root, deployed, component_candidate):
        changed = diff_paths(source_root, deployed, component_candidate, paths)
        item["changed_paths"] = changed
        if changed:
            item["decision"] = "include"
            item["reason"] = "候选 commit 包含该组件发布相关路径变更。"
        else:
            item["decision"] = "skip"
            item["reason"] = "目标环境落后，但该组件发布相关路径没有变更。"
        return item

    if is_ancestor(source_root, component_candidate, deployed):
        item["decision"] = "blocked"
        item["reason"] = "目标环境记录的 commit 比候选 commit 更新；请先确认本地代码或发布状态。"
        return item

    item["decision"] = "blocked"
    item["reason"] = "目标环境记录的 commit 与候选 commit 分叉；需要人工确认发布基线。"
    return item


def write_success_state(root: Path, plan: Dict[str, Any], record_path: str = "") -> List[str]:
    written: List[str] = []
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    worktree = plan.get("worktree_check") or {}
    for item in plan["components"]:
        if item.get("decision") != "include":
            continue
        state_path = root / item["state_file"]
        state_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": 2,
            "environment": plan["environment"],
            "environment_role": plan["environment_role"],
            "deployment_target_key": plan["deployment_target_key"],
            "scope_fingerprint": plan["scope_fingerprint"],
            "app_key": item["app_key"],
            "version_id": item["candidate_commit"],
            "version_id_type": "git_commit",
            "source_mode": item.get("source_mode"),
            "source_repository_ref": item.get("source_repository_ref"),
            "source_commit": item["candidate_commit"],
            "definition_commit": plan["candidate_commit"],
            "source_branch": plan.get("release_branch"),
            "released_at": now,
            "release_record": record_path,
            "verified": True,
            "notes": "Written by ops/scripts/plan-release-components.py --record-success after a successful release.",
        }
        if worktree.get("dirty"):
            payload.update(
                {
                    "dirty_worktree": True,
                    "dirty_allowed": bool(worktree.get("dirty_allowed")),
                    "dirty_snapshot_id": worktree.get("dirty_snapshot_id"),
                    "dirty_entries": worktree.get("dirty_entries") or [],
                    "snapshot_note": "Test release snapshot includes uncommitted working-tree changes; version_id is the base git commit.",
                }
            )
        state_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        written.append(str(state_path.relative_to(root)))
    return written


def compute_plan(args: argparse.Namespace) -> Dict[str, Any]:
    root = Path(args.root).expanduser().resolve()
    releases, environments, components_doc, deployments, code_sources, code_source_bindings = load_configs(args, root)
    target = args.environment or args.target or ""
    if not target:
        raise RuntimeError("必须提供发布目标，例如 发布测试、发布上线、发布生产 或 --environment staging")

    environment, remote_server, alias_key = resolve_environment(target, releases)
    environment_config = (environments.get("environments") or {}).get(environment) or {}
    environment_role = "production" if str(environment_config.get("role") or "") == "production" else ("local" if environment == "test" else "staging")
    deployment_target = resolve_deployment_target(
        args.deployment_target or "",
        environment,
        environment_role,
        deployments,
        environments,
    )
    environment = str(deployment_target.get("environment_key") or environment)
    environment_role = str(deployment_target.get("environment_role") or environment_role)
    deployment_target_key = str(deployment_target.get("key") or f"{environment}-default")
    registry = component_registry(components_doc)
    target_components = parse_component_scope(deployment_target.get("component_refs"))
    selected_components = args.components or target_components
    selected_components = parse_component_scope(selected_components)
    validation_errors = validate_components(selected_components, registry, releases)
    outside_scope = sorted(set(selected_components) - set(target_components))
    if outside_scope:
        validation_errors.append(
            f"组件 {', '.join(outside_scope)} 不在部署目标 {deployment_target_key} 的显式 component_refs 范围内"
        )
    if not selected_components:
        validation_errors.append(f"部署目标 {deployment_target_key} 没有显式组件范围；空范围不会解释为全部组件")
    candidate = resolve_commit(root, args.candidate_commit or "HEAD")
    scope_fingerprint = "sha256:" + hashlib.sha256(
        json.dumps(
            {
                "deployment_target_key": deployment_target_key,
                "environment_key": environment,
                "environment_role": environment_role,
                "server_ref": deployment_target.get("server_ref"),
                "subproject_ref": deployment_target.get("subproject_ref"),
                "component_refs": target_components,
                "scope_mode": deployment_target.get("scope_mode"),
                "deployment_profile_ref": deployment_target.get("deployment_profile_ref"),
                "access_profile_ref": deployment_target.get("access_profile_ref"),
                "policy": deployment_target.get("policy") or {},
            },
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()

    plan: Dict[str, Any] = {
        "target": target,
        "alias_key": alias_key,
        "environment": environment,
        "environment_role": environment_role,
        "deployment_target_key": deployment_target_key,
        "deployment_target": deployment_target,
        "scope_fingerprint": scope_fingerprint,
        "remote_server": str(deployment_target.get("server_ref") or remote_server or ""),
        "release_branch": release_branch_ref(environments, environment),
        "candidate_commit": candidate,
        "selected_components": selected_components,
        "worktree_check": worktree_check(args, root, releases, environment),
        "latest_code_check": latest_code_check(args, root, releases, environments, environment, environment_role, candidate),
        "validation_errors": validation_errors,
        "components": [],
        "source_checks": [],
        "migration_groups": migration_execution_groups(releases, selected_components),
        "blocked": False,
        "included_components": [],
        "skipped_components": [],
    }

    if validation_errors:
        plan["blocked"] = True

    if plan["worktree_check"]["status"] == "blocked":
        plan["blocked"] = True

    if plan["latest_code_check"]["status"] == "blocked":
        plan["blocked"] = True

    for app_key in selected_components:
        if app_key not in registry:
            continue
        source_context = component_source_context(
            root,
            registry[app_key],
            code_sources,
            code_source_bindings,
            candidate,
        )
        source_check = source_latest_check(
            source_context,
            required=environment_role == "production",
            no_fetch=args.no_fetch,
        )
        plan["source_checks"].append({"app_key": app_key, **source_check})
        if source_check["status"] == "blocked":
            plan["blocked"] = True
        item = plan_component(
            root,
            releases,
            registry,
            environment,
            deployment_target_key,
            app_key,
            candidate,
            source_context,
            scope_fingerprint,
        )
        plan["components"].append(item)
        if item["decision"] == "include":
            plan["included_components"].append(app_key)
        elif item["decision"] == "skip":
            plan["skipped_components"].append(app_key)
        elif item["decision"] == "blocked":
            plan["blocked"] = True

    if args.record_success:
        if plan["blocked"]:
            raise RuntimeError("发布计划仍有阻塞项，不能写入成功发布状态。")
        plan["recorded_state_files"] = write_success_state(root, plan, args.record_path or "")

    return plan


def print_text(plan: Dict[str, Any]) -> None:
    print(f"发布目标: {plan['target']} -> {plan['environment']}")
    print(f"部署目标: {plan['deployment_target_key']} ({plan['environment_role']})")
    if plan.get("remote_server"):
        print(f"执行目标口径: {plan['remote_server']}")
    print(f"发布来源分支: {plan['release_branch']}")
    print(f"候选 commit: {plan['candidate_commit']}")
    print(f"工作区检查: {plan['worktree_check']['status']} - {plan['worktree_check']['message']}")
    latest = plan["latest_code_check"]
    print(f"本地最新检查: {latest['status']} - {latest['message']}")
    if plan["validation_errors"]:
        print("配置错误:")
        for error in plan["validation_errors"]:
            print(f"  - {error}")
    print("组件计划:")
    for item in plan["components"]:
        print(f"  - {item['app_key']}: {item['decision']} - {item['reason']}")
        print(f"    state: {item['state_file']}")
        if item.get("changed_paths"):
            for path in item["changed_paths"][:10]:
                print(f"    changed: {path}")
            if len(item["changed_paths"]) > 10:
                print(f"    changed: ... {len(item['changed_paths']) - 10} more")
    print(f"纳入发布: {', '.join(plan['included_components']) or 'none'}")
    print(f"跳过发布: {', '.join(plan['skipped_components']) or 'none'}")
    if plan.get("migration_groups"):
        print("共享服务迁移（每个 service_ref 只执行一次）:")
        for group in plan["migration_groups"]:
            print(
                f"  - {group['service_ref']}: owner={group['owner_component']} "
                f"components={','.join(group['component_refs'])}"
            )
    print(f"状态: {'blocked' if plan['blocked'] else 'ok'}")
    if plan.get("recorded_state_files"):
        print("已写入发布状态:")
        for path in plan["recorded_state_files"]:
            print(f"  - {path}")


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        plan = compute_plan(args)
    except Exception as exc:
        if args.format == "json":
            print(json.dumps({"error": str(exc)}, ensure_ascii=False, indent=2))
        else:
            print(f"FAIL: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps(plan, ensure_ascii=False, indent=2))
    else:
        print_text(plan)
    return 2 if plan["blocked"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
