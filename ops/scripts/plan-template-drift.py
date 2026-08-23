#!/usr/bin/env python3
"""Plan MAW template drift upgrades for derived projects."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))

from ops.lib.maw_config_loader import MawConfigLoader  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Resolve source-template drift from template_source.applied_version to target version.",
    )
    parser.add_argument("--root", default=".", help="Project root. Default: current directory.")
    parser.add_argument("--profile", default=None, help="Config profile. Default: project default.")
    parser.add_argument("--applied-version", help="Override template_source.applied_version.")
    parser.add_argument("--target-version", help="Override template_source.version.")
    parser.add_argument("--source-path", help="Override template_source.local_path.")
    parser.add_argument("--git-url", help="Override template_source.git_url.")
    parser.add_argument("--max-commits", type=int, default=20, help="Max commits to print. Default: 20.")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    return parser


def run_git(args: List[str], cwd: Optional[Path] = None, check: bool = True) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(cwd) if cwd else None,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or f"git {' '.join(args)} failed")
    return proc.stdout.strip()


def resolve_commit(repo: Path, ref: str) -> str:
    candidates = [
        ref,
        f"refs/heads/{ref}",
        f"refs/remotes/origin/{ref}",
        f"refs/tags/{ref}",
    ]
    for candidate in candidates:
        proc = subprocess.run(
            ["git", "rev-parse", "--verify", f"{candidate}^{{commit}}"],
            cwd=str(repo),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if proc.returncode == 0:
            return proc.stdout.strip()
    raise RuntimeError(f"Cannot resolve template ref: {ref}")


def prepare_source_repo(
    local_path: str,
    git_url: str,
    root: Path,
) -> tuple[Path, Optional[tempfile.TemporaryDirectory[str]], str]:
    if local_path:
        repo = Path(local_path).expanduser()
        if not repo.is_absolute():
            repo = root / repo
        if repo.is_dir() and (repo / ".git").exists():
            return repo.resolve(), None, "local_path"

    if not git_url:
        raise RuntimeError("No template_source.local_path or template_source.git_url is available")

    tmp = tempfile.TemporaryDirectory(prefix="maw-template-drift-")
    repo = Path(tmp.name) / "source-template.git"
    run_git(["clone", "--quiet", "--bare", "--filter=blob:none", git_url, str(repo)], check=True)
    return repo, tmp, "git_url"


def is_probably_commit(value: str) -> bool:
    return len(value) >= 7 and all(ch in "0123456789abcdefABCDEF" for ch in value)


def _seed_version_tuple(value: Any) -> Optional[tuple[int, int, int]]:
    parts = str(value or "").strip().split(".")
    if len(parts) != 3 or not all(part.isdigit() for part in parts):
        return None
    return tuple(int(part) for part in parts)


def _seed_lock_summary(payload: Any) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        return {
            "available": False,
            "seed_version": "",
            "contract_version": None,
            "contract_fingerprint": "",
        }
    return {
        "available": True,
        "seed_version": str(payload.get("seed_version") or ""),
        "contract_version": payload.get("contract_version"),
        "contract_fingerprint": str(payload.get("contract_fingerprint") or ""),
    }


def inspect_seed_contract(root: Path, repo: Path, target_commit: str) -> Dict[str, Any]:
    project_path = root / ".maw" / "seed.lock"
    project_payload: Any = None
    project_error = ""
    if project_path.is_file() and not project_path.is_symlink():
        try:
            project_payload = yaml.safe_load(project_path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as exc:
            project_error = str(exc)

    proc = subprocess.run(
        ["git", "show", f"{target_commit}:.maw/seed.lock"],
        cwd=str(repo),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    source_payload: Any = None
    source_error = ""
    if proc.returncode == 0:
        try:
            source_payload = yaml.safe_load(proc.stdout)
        except yaml.YAMLError as exc:
            source_error = str(exc)
    else:
        source_error = proc.stderr.strip() or "source_seed_lock_missing"

    project = _seed_lock_summary(project_payload)
    source = _seed_lock_summary(source_payload)
    status = "unavailable"
    message = "Seed Contract comparison is unavailable."
    if source["available"] and not project["available"]:
        status = "missing"
        message = "Project .maw/seed.lock is missing or invalid."
    elif source["available"] and project["available"]:
        project_version = _seed_version_tuple(project["seed_version"])
        source_version = _seed_version_tuple(source["seed_version"])
        if project_version is not None and source_version is not None:
            if project_version < source_version:
                status = "behind"
                message = "Project Seed Contract version is behind the source template."
            elif project_version > source_version:
                status = "ahead"
                message = "Project Seed Contract version is ahead of the source template."
            elif project["contract_version"] != source["contract_version"]:
                status = "contract_drift"
                message = "Seed versions match but contract versions differ."
            elif (
                project["contract_fingerprint"]
                and source["contract_fingerprint"]
                and project["contract_fingerprint"] != source["contract_fingerprint"]
            ):
                status = "contract_drift"
                message = "Seed versions match but contract fingerprints differ."
            else:
                status = "current"
                message = "Project Seed Contract matches the source template."
        else:
            status = "contract_drift"
            message = "Seed Contract version cannot be compared as semantic x.y.z."

    return {
        "status": status,
        "message": message,
        "project": {
            **project,
            "source_ref": ".maw/seed.lock",
            "error": project_error,
        },
        "source": {
            **source,
            "source_ref": f"{target_commit}:.maw/seed.lock",
            "error": source_error,
        },
    }


def compute_plan(args: argparse.Namespace) -> Dict[str, Any]:
    root = Path(args.root).expanduser().resolve()
    loader = MawConfigLoader(project_root=root, profile=args.profile)
    config = loader.load_domain("template-source")
    source = config.get("template_source", {})

    local_path = args.source_path if args.source_path is not None else str(source.get("local_path") or "")
    git_url = args.git_url if args.git_url is not None else str(source.get("git_url") or "")
    source_channel = str(source.get("source_channel") or "unknown_legacy").strip() or "unknown_legacy"
    public_source = source.get("public_source") or {}
    public_git_url = str(public_source.get("default_git_url") or "").strip()
    target_version = args.target_version if args.target_version else str(source.get("version") or "main")
    applied_version = args.applied_version if args.applied_version else str(source.get("applied_version") or "")

    if source_channel == "public_seed" and not git_url and public_git_url:
        git_url = public_git_url

    if source_channel != "public_seed" and args.source_path is None and args.git_url is None:
        return {
            "source_channel": source_channel,
            "source_kind": "unconfirmed",
            "git_url": git_url,
            "public_git_url": public_git_url,
            "target_version": target_version,
            "target_commit": "",
            "applied_version": applied_version,
            "status": "source_channel_unconfirmed",
            "behind_count": None,
            "ahead_count": None,
            "commit_range": None,
            "commits": [],
            "current_session_prompt": "",
            "message": "template_source.source_channel is missing, unknown_legacy or unsupported; confirm public_seed before automatic template drift upgrade.",
            "evidence": {
                "template_source.source_channel": source_channel,
                "template_source.git_url_present": bool(git_url),
                "template_source.public_source.default_git_url_present": bool(public_git_url),
            },
        }

    repo, tmp, source_kind = prepare_source_repo(local_path, git_url, root)
    try:
        target_commit = resolve_commit(repo, target_version)
        plan: Dict[str, Any] = {
            "source_channel": source_channel,
            "source_kind": source_kind,
            "git_url": git_url,
            "public_git_url": public_git_url,
            "target_version": target_version,
            "target_commit": target_commit,
            "applied_version": applied_version,
            "status": "unknown",
            "behind_count": None,
            "ahead_count": None,
            "commit_range": None,
            "commits": [],
            "seed_contract": inspect_seed_contract(root, repo, target_commit),
        }

        if not applied_version:
            plan["status"] = "baseline_missing"
            plan["message"] = "template_source.applied_version is empty; initialize it after this template version is adopted."
            return add_prompt(plan, args.max_commits)

        if not is_probably_commit(applied_version):
            plan["status"] = "baseline_invalid"
            plan["message"] = "template_source.applied_version must be a commit SHA from this version onward."
            return add_prompt(plan, args.max_commits)

        applied_commit = resolve_commit(repo, applied_version)
        plan["applied_commit"] = applied_commit

        if applied_commit == target_commit:
            seed_status = str(plan["seed_contract"].get("status") or "")
            plan["status"] = (
                "seed_contract_behind"
                if seed_status in {"behind", "missing", "contract_drift"}
                else "up_to_date"
            )
            plan["behind_count"] = 0
            plan["ahead_count"] = 0
            plan["commit_range"] = f"{applied_commit}..{target_commit}"
            if plan["status"] == "seed_contract_behind":
                plan["message"] = (
                    "Template commit baseline is current, but the project Seed "
                    "Contract requires a controlled migration."
                )
            return add_prompt(plan, args.max_commits)

        applied_is_ancestor = subprocess.run(
            ["git", "merge-base", "--is-ancestor", applied_commit, target_commit],
            cwd=str(repo),
            check=False,
        ).returncode == 0
        target_is_ancestor = subprocess.run(
            ["git", "merge-base", "--is-ancestor", target_commit, applied_commit],
            cwd=str(repo),
            check=False,
        ).returncode == 0

        if applied_is_ancestor:
            plan["status"] = "behind"
            plan["behind_count"] = int(run_git(["rev-list", "--count", f"{applied_commit}..{target_commit}"], cwd=repo))
            plan["ahead_count"] = 0
            plan["commit_range"] = f"{applied_commit}..{target_commit}"
            log = run_git(
                ["log", "--oneline", "--decorate", f"--max-count={args.max_commits}", f"{applied_commit}..{target_commit}"],
                cwd=repo,
            )
            plan["commits"] = [line for line in log.splitlines() if line]
        elif target_is_ancestor:
            plan["status"] = "ahead"
            plan["behind_count"] = 0
            plan["ahead_count"] = int(run_git(["rev-list", "--count", f"{target_commit}..{applied_commit}"], cwd=repo))
            plan["commit_range"] = f"{applied_commit}..{target_commit}"
        else:
            left_right = run_git(["rev-list", "--left-right", "--count", f"{applied_commit}...{target_commit}"], cwd=repo)
            left, right = [int(part) for part in left_right.split()]
            plan["status"] = "diverged"
            plan["ahead_count"] = left
            plan["behind_count"] = right
            plan["commit_range"] = f"{applied_commit}...{target_commit}"
        return add_prompt(plan, args.max_commits)
    finally:
        if tmp is not None:
            tmp.cleanup()


def add_prompt(plan: Dict[str, Any], max_commits: int) -> Dict[str, Any]:
    if plan["status"] == "seed_contract_behind":
        seed = plan.get("seed_contract") or {}
        project_seed = seed.get("project") or {}
        source_seed = seed.get("source") or {}
        plan["current_session_prompt"] = f"""执行受控 Seed Contract 迁移：
当前项目 Seed：{project_seed.get('seed_version') or '(missing)'}
源模板 Seed：{source_seed.get('seed_version') or '(unavailable)'}
Seed Contract 状态：{seed.get('status') or 'unknown'}
目标项目仓库：当前 Codex 会话所在仓库
执行方式：先生成迁移 preview 并完成隔离校验，再由当前用户确认应用；不要把 Seed Contract 迁移误当成模板 commit 漂移。
保护边界：保留 README、code、真实 app_key、模块档案、发布配置、仓库映射、secrets、.local、较新的 schema_version、项目 profile/source 身份和项目生命周期 methodology。
完成要求：应用后重新运行项目空间健康检测和本计划器，确认 Seed 不再落后；然后按目标项目规则提交、推送，并按仓库级 mirror 有效计划同步。"""
        return plan

    if plan["status"] != "behind":
        plan["current_session_prompt"] = ""
        return plan

    commits = "\n".join(f"- {line}" for line in plan["commits"][:max_commits]) or "- none"
    plan["current_session_prompt"] = f"""执行任务提示词工程：prompts/codex/task-packs/template-feature-upgrade-codex-tasks
Seed 来源通道：{plan.get('source_channel') or 'unknown_legacy'}
源模板本机路径：<源模板本机路径，如本机会话可访问则填写；否则留空并使用 git 地址>
源模板 git 地址：{plan['git_url']}
公开 Seed 仓：https://github.com/mawflow/mawflow-seed
源模板版本：{plan['target_commit']}
当前模板基线：{plan.get('applied_commit') or plan['applied_version']}
模板落后提交数：{plan['behind_count']}
Seed Contract 状态：{(plan.get('seed_contract') or {}).get('status') or 'unknown'}
待同步提交范围：{plan['commit_range']}
待同步提交列表：
{commits}
源模板读取优先级：用户输入 > .local/.maw/template-source.yaml > .maw/template-source.yaml > 当前仓库；外部公开项目不得读取内部私有 Seed 源。
目标项目仓库：当前 Codex 会话所在仓库
执行方式：当前会话继续执行；不要只生成给另一个会话的提示词。
升级范围：只同步上述提交范围内的模板能力；先审计仓库角色和 Seed 来源通道，再按取舍增量合并，不得整文件覆盖目标项目 README，不得误删目标项目已有 app_key、发布配置、仓库映射、secrets、.local 或项目私有规则。
完成要求：升级和验证完成后，将 .maw/template-source.yaml 中的 template_source.applied_version 更新为 {plan['target_commit']}；然后按目标项目规则提交、推送，并按仓库级 mirror 有效计划同步。"""
    return plan


def print_text(plan: Dict[str, Any]) -> None:
    print("Template drift plan")
    print(f"  status: {plan['status']}")
    print(f"  source_channel: {plan.get('source_channel') or '(missing)'}")
    print(f"  source_kind: {plan['source_kind']}")
    print(f"  git_url: {plan['git_url']}")
    if plan.get("public_git_url"):
        print(f"  public_git_url: {plan['public_git_url']}")
    print(f"  target_version: {plan['target_version']}")
    print(f"  target_commit: {plan['target_commit']}")
    print(f"  applied_version: {plan['applied_version'] or '(empty)'}")
    if plan.get("applied_commit"):
        print(f"  applied_commit: {plan['applied_commit']}")
    print(f"  behind_count: {plan['behind_count']}")
    print(f"  ahead_count: {plan['ahead_count']}")
    if plan.get("commit_range"):
        print(f"  commit_range: {plan['commit_range']}")
    if plan.get("message"):
        print(f"  message: {plan['message']}")
    if plan.get("seed_contract"):
        seed = plan["seed_contract"]
        print(f"  seed_contract_status: {seed.get('status')}")
        print(
            "  project_seed_version: "
            f"{(seed.get('project') or {}).get('seed_version') or '(missing)'}"
        )
        print(
            "  source_seed_version: "
            f"{(seed.get('source') or {}).get('seed_version') or '(unavailable)'}"
        )
    if plan.get("commits"):
        print()
        print("Commits to review:")
        for line in plan["commits"]:
            print(f"  {line}")
    if plan.get("current_session_prompt"):
        print()
        print("Current-session execution prompt:")
        print("```text")
        print(plan["current_session_prompt"])
        print("```")


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if not shutil.which("git"):
        raise RuntimeError("git is required")
    plan = compute_plan(args)
    if args.format == "json":
        print(json.dumps(plan, ensure_ascii=False, indent=2))
    else:
        print_text(plan)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
