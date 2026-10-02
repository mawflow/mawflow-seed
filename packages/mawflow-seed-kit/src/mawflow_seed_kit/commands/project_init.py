from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib
import inspect
import json
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Any

from mawflow_seed_kit import compile_project_definition, materialize_project

from .template_sources import (
    DEFAULT_PACKAGE_INDEX_URL,
    DEFAULT_TEMPLATE_PACKAGE,
    MaterializedTemplate,
    TemplateSourceConfig,
    TemplateSourceError,
    materialize_template_source,
)


class ProjectInitError(RuntimeError):
    pass


@dataclass
class ProjectInitConfig:
    name: str
    profile: str = "blank"
    source: str = "package"
    index_url: str = DEFAULT_PACKAGE_INDEX_URL
    template: str = DEFAULT_TEMPLATE_PACKAGE
    template_version: str = ""
    repo: str = ""
    ref: str = ""
    path: str = ""
    target_dir: str = ""
    git_init: bool = True
    plan_only: bool = False
    git_env: dict[str, str] | None = None
    classification: dict[str, Any] | None = None
    technology: dict[str, Any] | None = None
    credential_requirements: list[dict[str, Any]] | None = None
    require_seed_2_1: bool = False


SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("private_key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("openai_style_api_key", re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b")),
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("license_code_assignment", re.compile(r"(?i)\blicense[_-]?code\s*[:=]\s*[A-Za-z0-9_-]{8,}")),
    ("api_key_assignment", re.compile(r"(?i)\b(api|secret|provider)[_-]?key\s*[:=]\s*['\"]?[A-Za-z0-9_-]{12,}")),
    ("local_mock_code", re.compile(r"\bMAWFLOW-[A-Z0-9_-]{6,}\b")),
)


def slugify_project_key(name: str) -> str:
    normalized = name.strip()
    value = re.sub(r"[^a-zA-Z0-9_-]+", "-", normalized).strip("-_").lower()
    if any(ord(char) > 127 for char in normalized):
        suffix = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:8]
        return f"{value}-{suffix}" if value else f"mawflow-project-{suffix}"
    return value or "mawflow-project"


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def target_path_for(config: ProjectInitConfig, cwd: Path | None = None) -> tuple[Path, bool]:
    cwd = (cwd or Path.cwd()).expanduser().resolve()
    if config.target_dir:
        return Path(config.target_dir).expanduser().resolve(), True
    return (cwd / config.name).resolve(), False


def ensure_target_allowed(target: Path, explicit_target: bool) -> None:
    home = Path.home().expanduser().resolve()
    if not explicit_target and not is_relative_to(target, home):
        raise ProjectInitError("target_outside_home_requires_explicit_target_dir")


def ensure_target_empty(target: Path) -> None:
    if target.exists() and not target.is_dir():
        raise ProjectInitError("target_path_exists_and_is_not_a_directory")
    if target.exists() and any(target.iterdir()):
        raise ProjectInitError("target_dir_exists_and_is_not_empty")


def scan_template_safety(template_dir: Path) -> None:
    for path in template_dir.rglob("*"):
        rel = path.relative_to(template_dir)
        if path.is_symlink():
            raise ProjectInitError(f"template_symlink_not_allowed:{rel.as_posix()}")
        if ".local" in rel.parts:
            raise ProjectInitError(f"template_contains_forbidden_local_path:{rel.as_posix()}")
        if not path.is_file():
            continue
        if path.stat().st_size > 1024 * 1024:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for label, pattern in SECRET_PATTERNS:
            if pattern.search(content):
                raise ProjectInitError(f"template_contains_forbidden_secret_pattern:{label}:{rel.as_posix()}")


def source_metadata_for_project(config: ProjectInitConfig, materialized: MaterializedTemplate) -> dict[str, str]:
    raw_path = str(materialized.metadata.get("path") or config.path or "")
    path_fingerprint = f"sha256:{hashlib.sha256(raw_path.encode('utf-8')).hexdigest()}" if raw_path else ""
    return {
        "source_type": str(materialized.metadata.get("source_type", config.source)),
        "template": str(materialized.metadata.get("package", config.template)),
        "template_version": str(materialized.metadata.get("version", config.template_version or "")),
        "template_tree_sha256": str(materialized.metadata.get("template_tree_sha256") or ""),
        "index_url": str(materialized.metadata.get("index_url", config.index_url if config.source == "package" else "")),
        "repo": str(materialized.metadata.get("repo", config.repo)),
        "ref": str(materialized.metadata.get("ref", config.ref)),
        "source_commit": str(materialized.metadata.get("source_commit") or ""),
        "local_path_fingerprint": path_fingerprint,
    }


def initialize_git_repository(target: Path, enabled: bool) -> dict[str, Any]:
    if not enabled:
        return {"git_init": False, "git_status": "skipped"}
    if (target / ".git").exists():
        return {"git_init": True, "git_status": "already_exists"}
    if shutil.which("git") is None:
        raise ProjectInitError("git_not_available")
    projection = compile_project_definition(target)
    default_branch = str(projection.get("project", {}).get("default_branch") or "main")
    completed = subprocess.run(
        ["git", "init", f"--initial-branch={default_branch}"],
        cwd=target, text=True, capture_output=True, check=False,
    )
    if completed.returncode != 0:
        raise ProjectInitError(completed.stderr.strip() or completed.stdout.strip() or "git_init_failed")
    return {"git_init": True, "git_status": "initialized"}


def created_files(target: Path) -> list[str]:
    return sorted(
        path.relative_to(target).as_posix()
        for path in target.rglob("*")
        if path.is_file() and ".git" not in path.relative_to(target).parts
    )


def run_template_quick_check(target: Path, materialized: MaterializedTemplate) -> dict[str, Any]:
    manifest: dict[str, Any] = {}
    if materialized.manifest_path is not None:
        try:
            manifest = json.loads(materialized.manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ProjectInitError("template_manifest_unreadable_during_quick_check") from exc
    declared = manifest.get("quick_check")
    if not declared:
        return {"status": "not_declared", "command": []}
    if not isinstance(declared, list) or not declared or not all(isinstance(item, str) and item for item in declared):
        raise ProjectInitError("template_quick_check_command_invalid")
    command = list(declared)
    if command[0] in {"python", "python3"}:
        command[0] = sys.executable
    try:
        completed = subprocess.run(command, cwd=target, text=True, capture_output=True, check=False, timeout=30)
    except subprocess.TimeoutExpired as exc:
        raise ProjectInitError("template_quick_check_timed_out") from exc
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "quick_check_failed").strip().splitlines()[0][:240]
        raise ProjectInitError(f"template_quick_check_failed:{detail}")
    payload: dict[str, Any] = {}
    if completed.stdout.strip():
        try:
            payload = json.loads(completed.stdout)
        except json.JSONDecodeError:
            payload = {"output": completed.stdout.strip()[:500]}
    if payload.get("schema") == "mawflow.seed_project_definition.v2":
        payload = {
            "schema": payload["schema"],
            "status": payload.get("status"),
            "editable": payload.get("editable"),
            "contract_version": payload.get("contract_version"),
            "contract_fingerprint": payload.get("contract_fingerprint"),
            "projection_fingerprint": payload.get("fingerprint"),
            "summary": payload.get("summary"),
        }
    return {"status": "passed", "command": declared, "result": payload}


def public_source_metadata(config: ProjectInitConfig, materialized: MaterializedTemplate) -> dict[str, Any]:
    metadata = dict(materialized.metadata)
    if metadata.get("source_type") == "local" and metadata.get("path"):
        raw_path = str(metadata.pop("path"))
        metadata["path"] = "<local-template>"
        metadata["path_fingerprint"] = f"sha256:{hashlib.sha256(raw_path.encode('utf-8')).hexdigest()}"
    return metadata


def init_project(config: ProjectInitConfig, cwd: Path | None = None) -> dict[str, Any]:
    target, explicit_target = target_path_for(config, cwd)
    ensure_target_allowed(target, explicit_target)
    ensure_target_empty(target)
    source_config = TemplateSourceConfig(
        source=config.source,
        index_url=config.index_url,
        template=config.template,
        template_version=config.template_version,
        repo=config.repo,
        ref=config.ref,
        path=config.path,
        git_env=config.git_env,
    )
    materialized: MaterializedTemplate | None = None
    staging: Path | None = None
    try:
        materialized = materialize_template_source(source_config)
        scan_template_safety(materialized.template_dir)
        source = public_source_metadata(config, materialized)
        plan = {
            "schema": "mawflow.project_init.result.v2",
            "status": "planned" if config.plan_only else "ready_to_initialize",
            "project_name": config.name,
            "target_dir": str(target),
            "target_state": "empty_existing" if target.exists() else "new",
            "source": source,
            "write_policy": "atomic_new_directory_only",
            "rollback_hint": "Remove only the newly created target directory before adding project work.",
        }
        if config.plan_only:
            return plan
        manifest = (
            json.loads(materialized.manifest_path.read_text(encoding="utf-8"))
            if materialized.manifest_path is not None
            else {}
        )
        if manifest.get("name") != "mawflow-seed-kit" or int(manifest.get("contract_version") or 0) != 2:
            raise ProjectInitError("seed_contract_v2_source_required")
        target.parent.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix=f".{target.name}.mawflow-init-", dir=target.parent))
        shutil.rmtree(staging)
        project_key = slugify_project_key(config.name)
        materialize_parameters = inspect.signature(materialize_project).parameters
        seed_21_fields = {
            "classification": config.classification,
            "technology": config.technology,
            "credential_requirements": config.credential_requirements,
        }
        if config.require_seed_2_1 and not set(seed_21_fields) <= set(
            materialize_parameters
        ):
            raise ProjectInitError("seed_contract_2_1_package_required")
        materialize_kwargs = {
            key: value
            for key, value in seed_21_fields.items()
            if key in materialize_parameters and value is not None
        }
        materialize_project(
            staging,
            project_key=project_key,
            name=config.name,
            profile=config.profile,
            source={**source_metadata_for_project(config, materialized), "kind": config.source},
            template_root=materialized.template_dir,
            seed_version=str(manifest.get("version") or ""),
            seed_fingerprint=str(manifest.get("contract_fingerprint") or ""),
            **materialize_kwargs,
        )
        verification = run_template_quick_check(staging, materialized)
        projection = compile_project_definition(staging)
        if projection["status"] != "ready":
            raise ProjectInitError("seed_contract_v2_compilation_failed")
        git_result = initialize_git_repository(staging, config.git_init)
        files = created_files(staging)
        if target.exists():
            target.rmdir()
        staging.replace(target)
        staging = None
        return {
            "schema": "mawflow.project_init.result.v2",
            "status": "initialized",
            "project_name": config.name,
            "profile": config.profile,
            "target_dir": str(target),
            "source": source,
            "write_policy": "atomic_new_directory_only",
            "created_files": files,
            "verification": verification,
            "next_steps": [
                "Read AI_START_HERE.md",
                "Run mawflow project doctor --root .",
                "Open the local workbench to add components, modules, applications, and environments",
                "Commit shared .maw changes; keep .local/.maw bindings on this computer",
            ],
            "rollback_hint": "Remove only this newly created target directory before adding project work.",
            **git_result,
            "project_key": project_key,
            "contract_version": projection["contract_version"],
            "contract_fingerprint": projection["contract_fingerprint"],
            "projection_fingerprint": projection["fingerprint"],
            "template_source": str(target / ".maw/template-source.yaml"),
            "project_yaml": str(target / ".maw/project.yaml"),
        }
    except TemplateSourceError as exc:
        raise ProjectInitError(str(exc)) from exc
    finally:
        if staging is not None:
            shutil.rmtree(staging, ignore_errors=True)
        if materialized is not None:
            materialized.close()
