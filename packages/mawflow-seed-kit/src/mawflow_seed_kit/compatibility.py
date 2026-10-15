"""Determine upgrade direction without rewriting a project's lock."""
from __future__ import annotations

import re
from typing import Any

from .catalog import CONTRACT_VERSION, SEED_VERSION, contract_fingerprint


def _version(value: str) -> tuple[int, ...] | None:
    match = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)(?:(?:-?rc)(\d+))?", value)
    if not match:
        return None
    major, minor, patch, rc = match.groups()
    return int(major), int(minor), int(patch), 0 if rc else 1, int(rc or 0)


def tool_compatibility(lock: dict[str, Any]) -> dict[str, Any]:
    raw_contract = lock.get("contract_version")
    invalid_contract = False
    try:
        project_contract = int(raw_contract or 0)
    except (ValueError, TypeError):
        project_contract = 0
        invalid_contract = True
    project_version = str(lock.get("seed_version") or "")
    project_key, tool_key = _version(project_version), _version(SEED_VERSION)
    ahead = project_contract > CONTRACT_VERSION or bool(project_key and tool_key and project_key > tool_key)
    mismatch = project_contract != CONTRACT_VERSION or lock.get("contract_fingerprint") != contract_fingerprint()
    unknown = invalid_contract or bool(project_version and project_key is None)
    status = "tool_upgrade_required" if ahead else "unknown" if unknown else "project_migration_required" if mismatch else "current"
    return {"status": status, "tool_seed_version": SEED_VERSION, "project_seed_version": project_version,
            "project_contract_version": project_contract, "tool_contract_version": CONTRACT_VERSION,
            "migration_required": mismatch and not ahead and not unknown}


def require_compatible_migration(root) -> None:
    from pathlib import Path
    import yaml

    path = Path(root) / ".maw/seed.lock"
    if path.is_symlink():
        raise ValueError("seed_source_symlink_forbidden")
    if path.is_file():
        if path.stat().st_size > 2 * 1024 * 1024:
            raise ValueError("seed_source_unavailable")
        lock = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(lock, dict):
            raise ValueError("seed_lock_mapping_required")
        state = tool_compatibility(lock)["status"]
        if state == "tool_upgrade_required":
            raise ValueError("seed_tool_upgrade_required")
        if state == "unknown":
            raise ValueError("seed_contract_compatibility_unknown")
