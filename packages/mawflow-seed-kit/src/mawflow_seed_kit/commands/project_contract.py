from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
from typing import Any

from mawflow_seed_kit import compile_project_definition
from .seed_migration_compat import (
    apply_safe_seed_migration_plan as apply_migration_plan,
    plan_safe_seed_migration as plan_migration,
)


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def project_doctor(root: Path | str) -> dict[str, Any]:
    return compile_project_definition(Path(root))


def default_plan_path(root: Path) -> Path:
    return root / ".local" / ".maw" / "migration-plan.json"


def project_migration(
    root: Path | str,
    *,
    profile: str,
    execute: bool,
    confirmation: str = "",
    plan_file: Path | str | None = None,
) -> dict[str, Any]:
    project_root = Path(root).expanduser().resolve(strict=True)
    plan_path = Path(plan_file).expanduser().resolve() if plan_file else default_plan_path(project_root)
    if not execute:
        public, private = plan_migration(project_root, profile=profile)
        _atomic_json(plan_path, private)
        return {
            **public,
            "plan_ref": ".local/.maw/migration-plan.json" if plan_file is None else str(plan_path),
            "private_plan_persisted": True,
        }
    if not plan_path.is_file() or plan_path.is_symlink():
        raise ValueError("seed_migration_plan_file_missing")
    try:
        private = json.loads(plan_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("seed_migration_plan_file_invalid") from exc
    if not isinstance(private, dict):
        raise ValueError("seed_migration_plan_file_invalid")
    result = apply_migration_plan(
        project_root,
        private,
        confirmation,
        backup_root=project_root / ".local" / ".maw" / "migration-backups",
    )
    plan_path.unlink(missing_ok=True)
    return result


__all__ = ["project_doctor", "project_migration"]
