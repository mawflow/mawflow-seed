from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import shlex
import shutil
import subprocess
from typing import Any

from .seed_migration_compat import (
    apply_safe_seed_migration_plan,
    plan_safe_seed_migration,
)
from .git_environment import git_read_only_environment

from .project_contract import project_doctor, project_migration
from .project_init import (
    ProjectInitConfig,
    ProjectInitError,
    init_project,
    initialize_git_repository,
)


PROJECT_INIT_SCHEMA = "mawflow.project_init.result.v3"


def _resolved(path: str | Path, *, cwd: Path) -> Path:
    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        candidate = cwd / candidate
    return candidate.resolve()


def resolve_project_target(
    config: ProjectInitConfig,
    *,
    root: str = "",
    cwd: Path | None = None,
) -> tuple[Path, str]:
    workdir = (cwd or Path.cwd()).expanduser().resolve()
    if root and config.target_dir:
        raise ProjectInitError("project_root_and_target_dir_conflict")
    if root:
        target = _resolved(root, cwd=workdir)
    elif config.target_dir:
        target = _resolved(config.target_dir, cwd=workdir)
    elif config.name:
        target = (workdir / config.name).resolve()
    else:
        target = workdir
    name = config.name.strip() or target.name
    if not name:
        raise ProjectInitError("project_name_required")
    return target, name


def _git(
    root: Path,
    *args: str,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        text=True,
        capture_output=True,
        check=False,
        env=git_read_only_environment(),
    )


def _is_git_repository_root(root: Path) -> bool:
    if shutil.which("git") is None:
        return False
    completed = _git(root, "rev-parse", "--show-toplevel")
    if completed.returncode != 0:
        return False
    try:
        git_root = Path(completed.stdout.strip()).expanduser().resolve(strict=True)
    except (OSError, RuntimeError):
        return False
    return git_root == root.resolve()


def _content_refs(root: Path) -> list[str]:
    return sorted(path.name for path in root.iterdir() if path.name != ".git")


def classify_project_target(root: Path) -> dict[str, Any]:
    if not root.exists():
        return {
            "mode": "new_directory",
            "git_repository": False,
            "content_refs": [],
        }
    if not root.is_dir():
        raise ProjectInitError("target_path_exists_and_is_not_a_directory")
    git_repository = _is_git_repository_root(root)
    if (root / ".git").exists() and not git_repository:
        raise ProjectInitError("git_repository_metadata_invalid")
    content_refs = _content_refs(root)
    if (root / ".maw" / "seed.lock").is_file():
        mode = "seeded_git_repository" if git_repository else "seeded_without_git"
    elif not content_refs:
        mode = "empty_git_repository" if git_repository else "empty_directory"
    elif git_repository:
        mode = "existing_git_repository"
    else:
        mode = "existing_directory_without_git"
    return {
        "mode": mode,
        "git_repository": git_repository,
        "content_refs": content_refs,
    }


def _status_source_ref(line: str) -> str:
    source_ref = line[3:] if len(line) > 3 else ""
    if " -> " in source_ref:
        source_ref = source_ref.rsplit(" -> ", 1)[-1]
    if source_ref.startswith('"'):
        try:
            decoded = json.loads(source_ref)
            return str(decoded)
        except json.JSONDecodeError:
            pass
    return source_ref


def _git_changes(root: Path, *, allowed_refs: set[str] | None = None) -> list[str]:
    completed = _git(root, "status", "--porcelain=v1", "--untracked-files=all")
    if completed.returncode != 0:
        raise ProjectInitError(
            completed.stderr.strip()
            or completed.stdout.strip()
            or "git_status_failed"
        )
    allowed = allowed_refs or set()
    return [
        line
        for line in completed.stdout.splitlines()
        if line and _status_source_ref(line) not in allowed
    ]


def _default_profile(mode: str, requested: str) -> str:
    if requested:
        return requested
    return "blank"


def _migration_plan_path(root: Path, plan_file: Path | str | None) -> Path:
    if plan_file:
        path = Path(plan_file).expanduser()
        return path.resolve() if path.is_absolute() else (Path.cwd() / path).resolve()
    return root / ".local" / ".maw" / "migration-plan.json"


def _relative_ref(root: Path, path: Path) -> str | None:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return None


def _preview_command(root: Path, confirmation: str, plan_file: Path | str | None) -> str:
    command = [
        "mawflow",
        "project",
        "init",
        "--root",
        str(root),
        "--execute",
        "--confirm",
        confirmation,
    ]
    if plan_file:
        command.extend(["--plan-file", str(plan_file)])
    return " ".join(shlex.quote(item) for item in command)


def _projection_summary(projection: object) -> dict[str, Any]:
    value = projection if isinstance(projection, dict) else {}
    project = value.get("project") if isinstance(value.get("project"), dict) else {}
    return {
        "schema": value.get("schema"),
        "status": value.get("status"),
        "editable": value.get("editable"),
        "migration_required": value.get("migration_required"),
        "project": project,
        "contract_version": value.get("contract_version"),
        "contract_fingerprint": value.get("contract_fingerprint"),
        "fingerprint": value.get("fingerprint"),
        "summary": value.get("summary"),
        "issues": list(value.get("issues") or [])[:20],
    }


def _public_migration_result(result: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in result.items()
        if key not in {"private_rollback_manifest", "projection"}
    } | {"projection": _projection_summary(result.get("projection"))}


def _already_seeded(root: Path, mode: str, profile: str) -> dict[str, Any]:
    if mode == "seeded_without_git":
        raise ProjectInitError("seed_project_requires_git_repository")
    projection = project_doctor(root)
    ready = projection.get("status") == "ready"
    return {
        "schema": PROJECT_INIT_SCHEMA,
        "status": "ready" if ready else "needs_attention",
        "mode": "already_seeded",
        "profile": profile,
        "target_dir": str(root),
        "git_repository": True,
        "changed": False,
        "projection": _projection_summary(projection),
        "next_steps": (
            ["No initialization changes are required."]
            if ready
            else ["Run mawflow project doctor --root . and repair the reported Seed facts."]
        ),
    }


def _empty_target_plan(root: Path, *, profile: str, mode: str) -> tuple[dict[str, Any], dict[str, Any]]:
    public, private = plan_safe_seed_migration(
        root,
        profile=profile,
        initialization_mode="empty_repository",
    )
    validation = public.get("validation")
    if not isinstance(validation, dict) or validation.get("status") != "ready":
        raise ProjectInitError("seed_initialization_preview_not_ready")
    return (
        {
            **public,
            "schema": PROJECT_INIT_SCHEMA,
            "status": "planned",
            "mode": mode,
            "profile": profile,
            "target_dir": str(root),
            "git_repository": mode == "empty_git_repository",
            "write_policy": "read_only_empty_repository_preview",
        },
        private,
    )


def _remove_empty_target_changes(root: Path, *, remove_git: bool) -> None:
    for path in root.iterdir():
        if path.name == ".git" and not remove_git:
            continue
        if path.is_dir() and not path.is_symlink():
            shutil.rmtree(path, ignore_errors=True)
        else:
            path.unlink(missing_ok=True)


def _seed_empty_target(root: Path, *, profile: str, initialize_git: bool) -> dict[str, Any]:
    mode = "empty_directory" if initialize_git else "empty_git_repository"
    _preview, private = _empty_target_plan(root, profile=profile, mode=mode)
    git_result: dict[str, Any] = {
        "git_init": True,
        "git_status": "already_exists",
    }
    created_git = False
    try:
        if initialize_git:
            git_result = initialize_git_repository(root, True)
            if git_result.get("git_status") != "initialized":
                raise ProjectInitError("git_initialization_failed")
            created_git = git_result.get("git_status") == "initialized"
        result = apply_safe_seed_migration_plan(
            root,
            private,
            str(private["confirmation_required"]),
            backup_root=root / ".local" / ".maw" / "migration-backups",
        )
    except Exception:
        _remove_empty_target_changes(root, remove_git=created_git)
        raise
    public_result = _public_migration_result(result)
    return {
        "schema": PROJECT_INIT_SCHEMA,
        "status": "initialized",
        "mode": mode,
        "profile": profile,
        "target_dir": str(root),
        "git_repository": True,
        "write_policy": "atomic_seed_files_with_private_backup",
        "migration": public_result,
        "projection": public_result["projection"],
        "next_steps": [
            "Read AI_START_HERE.md",
            "Run mawflow project doctor --root .",
            "Create components explicitly with mawflow component init <key> --type <type>",
            "Replace placeholder project facts with the repository's real facts",
            "Review git status and commit the shared Seed files",
        ],
        **git_result,
    }


def init_or_seed_project(
    config: ProjectInitConfig,
    *,
    root: str = "",
    execute: bool = False,
    confirmation: str = "",
    plan_file: Path | str | None = None,
    cwd: Path | None = None,
) -> dict[str, Any]:
    target, project_name = resolve_project_target(config, root=root, cwd=cwd)
    state = classify_project_target(target)
    mode = str(state["mode"])
    profile = _default_profile(mode, config.profile)

    if mode == "new_directory":
        result = init_project(
            replace(
                config,
                name=project_name,
                profile=profile,
                target_dir=str(target),
            ),
            cwd=cwd,
        )
        return {**result, "schema": PROJECT_INIT_SCHEMA, "mode": mode}
    if mode in {"seeded_git_repository", "seeded_without_git"}:
        return _already_seeded(target, mode, profile)
    if mode == "existing_directory_without_git":
        raise ProjectInitError("existing_content_requires_git_repository")
    if mode in {"empty_directory", "empty_git_repository"}:
        if mode == "empty_directory" and not config.git_init:
            raise ProjectInitError("seed_initialization_requires_git_repository")
        if config.plan_only:
            public, _private = _empty_target_plan(
                target,
                profile=profile,
                mode=mode,
            )
            return public
        return _seed_empty_target(
            target,
            profile=profile,
            initialize_git=mode == "empty_directory",
        )

    if any(
        [
            config.source != "package",
            bool(config.template_version),
            bool(config.repo),
            bool(config.ref),
            bool(config.path),
        ]
    ):
        raise ProjectInitError("existing_repository_source_overrides_not_supported")

    migration_plan_path = _migration_plan_path(target, plan_file)
    allowed_refs: set[str] = set()
    if execute:
        relative_plan = _relative_ref(target, migration_plan_path)
        if relative_plan:
            allowed_refs.add(relative_plan)
    changes = _git_changes(target, allowed_refs=allowed_refs)
    if changes:
        raise ProjectInitError("git_worktree_not_clean")

    result = project_migration(
        target,
        profile=profile,
        execute=execute,
        confirmation=confirmation,
        plan_file=plan_file,
    )
    if execute:
        public_result = _public_migration_result(result)
        return {
            "schema": PROJECT_INIT_SCHEMA,
            "status": "initialized",
            "mode": mode,
            "profile": profile,
            "target_dir": str(target),
            "git_repository": True,
            "write_policy": "atomic_seed_files_with_private_backup",
            "migration": public_result,
            "projection": public_result["projection"],
            "next_steps": [
                "Review and replace placeholder Seed facts with real repository facts",
                "Run mawflow project doctor --root .",
                "Adopt existing component directories with mawflow component adopt <path> --key <key> --type <type>",
                "Review git status and commit the shared Seed files",
            ],
        }

    validation = result.get("validation")
    ready = isinstance(validation, dict) and validation.get("status") == "ready"
    required = str(result.get("confirmation_required") or "")
    return {
        **result,
        "schema": PROJECT_INIT_SCHEMA,
        "status": "previewed" if ready else "blocked",
        "mode": mode,
        "profile": profile,
        "target_dir": str(target),
        "git_repository": True,
        "write_policy": "preview_then_atomic_seed_files_with_private_backup",
        "next_command": _preview_command(target, required, plan_file),
    }


__all__ = [
    "PROJECT_INIT_SCHEMA",
    "classify_project_target",
    "init_or_seed_project",
    "resolve_project_target",
]
