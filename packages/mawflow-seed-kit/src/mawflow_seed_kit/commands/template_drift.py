from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Any

import yaml


class TemplateDriftError(RuntimeError):
    pass


@dataclass(frozen=True)
class TemplateDriftConfig:
    root: Path
    applied_version: str = ""
    target_version: str = ""
    git_url: str = ""
    max_commits: int = 20


def _merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    result = dict(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _merge(result[key], value)
        else:
            result[key] = value
    return result


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise TemplateDriftError(f"template_source_yaml_invalid:{path}") from exc
    if not isinstance(data, dict):
        raise TemplateDriftError(f"template_source_yaml_not_mapping:{path}")
    return data


def load_template_source(root: Path) -> dict[str, Any]:
    base_path = root / ".maw" / "template-source.yaml"
    if not base_path.is_file():
        raise TemplateDriftError("template_source_not_found:.maw/template-source.yaml")
    data = _load_yaml(base_path)
    local_path = root / ".local" / ".maw" / "template-source.yaml"
    if local_path.is_file():
        data = _merge(data, _load_yaml(local_path))
    source = data.get("template_source")
    if not isinstance(source, dict):
        raise TemplateDriftError("template_source_mapping_missing")
    return source


def _git(args: list[str], cwd: Path | None = None, *, check: bool = True) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and completed.returncode != 0:
        raise TemplateDriftError(completed.stderr.strip() or completed.stdout.strip() or "git_command_failed")
    return completed.stdout.strip()


def _resolve_commit(repo: Path, ref: str) -> str:
    for candidate in (ref, f"refs/heads/{ref}", f"refs/remotes/origin/{ref}", f"refs/tags/{ref}"):
        completed = subprocess.run(
            ["git", "rev-parse", "--verify", f"{candidate}^{{commit}}"],
            cwd=repo,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if completed.returncode == 0:
            return completed.stdout.strip()
    raise TemplateDriftError(f"template_ref_not_found:{ref}")


def _is_commit(value: str) -> bool:
    return len(value) >= 7 and all(character in "0123456789abcdefABCDEF" for character in value)


def _execution_prompt(plan: dict[str, Any]) -> str:
    if plan["status"] != "behind":
        return ""
    commits = "\n".join(f"- {item}" for item in plan["commits"]) or "- none"
    return f"""在当前项目继续执行 Seed 模板增量升级。
Seed 来源通道：{plan['source_channel']}
源模板 git 地址：{plan['git_url']}
当前模板基线：{plan['applied_commit']}
目标模板 commit：{plan['target_commit']}
待同步范围：{plan['commit_range']}
待同步提交：
{commits}
先创建升级分支并审计上述提交的文件和语义差异；只增量采用适合当前项目的变更。保护 README.md、code/、app_key、发布配置、仓库映射、secrets、.local 和模块档案，禁止整仓覆盖。运行项目自身检查并确认业务事实未丢失后，才把 .maw/template-source.yaml 的 template_source.applied_version 更新为 {plan['target_commit']}。再次运行 mawflow project drift，必须得到 up_to_date。"""


def plan_template_drift(config: TemplateDriftConfig) -> dict[str, Any]:
    if shutil.which("git") is None:
        raise TemplateDriftError("git_not_available")
    root = config.root.expanduser().resolve()
    source = load_template_source(root)
    source_channel = str(source.get("source_channel") or "unknown_legacy").strip() or "unknown_legacy"
    public_source = source.get("public_source") if isinstance(source.get("public_source"), dict) else {}
    git_url = config.git_url or str(source.get("git_url") or "").strip()
    if source_channel == "public_seed" and not git_url:
        git_url = str(public_source.get("default_git_url") or "").strip()
    target_version = config.target_version or str(source.get("version") or "main").strip() or "main"
    applied_version = config.applied_version or str(source.get("applied_version") or "").strip()
    base: dict[str, Any] = {
        "schema": "mawflow.template_drift.plan.v2",
        "source_channel": source_channel,
        "git_url": git_url,
        "target_version": target_version,
        "target_commit": "",
        "applied_version": applied_version,
        "applied_commit": "",
        "status": "unknown",
        "behind_count": None,
        "ahead_count": None,
        "commit_range": "",
        "commits": [],
        "current_session_prompt": "",
    }
    if source_channel not in {"public_seed", "public_seed"}:
        return {
            **base,
            "status": "source_channel_unconfirmed",
            "message": "Confirm template_source.source_channel as public_seed or public_seed before drift execution.",
        }
    if not git_url:
        raise TemplateDriftError("template_source_git_url_missing")

    with tempfile.TemporaryDirectory(prefix="mawflow-template-drift-") as tmp:
        repo = Path(tmp) / "source.git"
        _git(["clone", "--quiet", "--bare", "--filter=blob:none", git_url, str(repo)])
        target_commit = _resolve_commit(repo, target_version)
        plan = {**base, "target_commit": target_commit}
        if not applied_version:
            return {
                **plan,
                "status": "baseline_missing",
                "message": "Adopt and verify the target version before recording it as the initial baseline.",
            }
        if not _is_commit(applied_version):
            return {
                **plan,
                "status": "baseline_invalid",
                "message": "template_source.applied_version must be a commit SHA.",
            }
        applied_commit = _resolve_commit(repo, applied_version)
        plan["applied_commit"] = applied_commit
        if applied_commit == target_commit:
            return {
                **plan,
                "status": "up_to_date",
                "behind_count": 0,
                "ahead_count": 0,
                "commit_range": f"{applied_commit}..{target_commit}",
            }

        applied_is_ancestor = subprocess.run(
            ["git", "merge-base", "--is-ancestor", applied_commit, target_commit], cwd=repo, check=False
        ).returncode == 0
        target_is_ancestor = subprocess.run(
            ["git", "merge-base", "--is-ancestor", target_commit, applied_commit], cwd=repo, check=False
        ).returncode == 0
        if applied_is_ancestor:
            commit_range = f"{applied_commit}..{target_commit}"
            log = _git(["log", "--oneline", "--decorate", f"--max-count={config.max_commits}", commit_range], repo)
            plan.update(
                status="behind",
                behind_count=int(_git(["rev-list", "--count", commit_range], repo)),
                ahead_count=0,
                commit_range=commit_range,
                commits=[line for line in log.splitlines() if line],
            )
        elif target_is_ancestor:
            plan.update(
                status="ahead",
                behind_count=0,
                ahead_count=int(_git(["rev-list", "--count", f"{target_commit}..{applied_commit}"], repo)),
                commit_range=f"{applied_commit}..{target_commit}",
            )
        else:
            ahead, behind = [int(value) for value in _git(["rev-list", "--left-right", "--count", f"{applied_commit}...{target_commit}"], repo).split()]
            plan.update(
                status="diverged",
                behind_count=behind,
                ahead_count=ahead,
                commit_range=f"{applied_commit}...{target_commit}",
            )
        plan["current_session_prompt"] = _execution_prompt(plan)
        return plan
