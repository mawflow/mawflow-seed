"""Lexical scope declarations; declaring a forbidden path never reads that path."""
from __future__ import annotations

from pathlib import PurePosixPath
from typing import Any


def normalize_scope_path(value: str) -> str:
    if (not isinstance(value, str) or not value.strip() or value != value.strip()
            or value.startswith("/") or "\\" in value or ":" in value
            or any(ord(char) < 32 for char in value)):
        raise ValueError("scope_reference_invalid")
    parts = PurePosixPath(value).parts
    if not parts or ".." in parts:
        raise ValueError("scope_reference_invalid")
    # A directory and its /** spelling both include descendants. Other glob syntax
    # is deliberately rejected instead of being mistaken for a literal filename.
    if parts[-1] == "**":
        parts = parts[:-1]
    if not parts or any(any(char in part for char in "*?[]{}") for part in parts):
        raise ValueError("scope_pattern_unsupported")
    return "/".join(parts)


def validate_scope_paths(scope: dict[str, Any], safe_path, root) -> tuple[list[str], dict[str, list[str]]]:
    issues: list[str] = []
    normalized: dict[str, list[str]] = {}
    for field in ("read_paths", "write_paths", "blocked_paths"):
        values = scope.get(field)
        normalized[field] = []
        if not isinstance(values, list):
            issues.append("scope_paths_invalid:" + field)
            continue
        for value in values:
            try:
                ref = normalize_scope_path(value)
                if field != "blocked_paths":
                    safe_path(root, ref)
                normalized[field].append(ref)
            except (ValueError, TypeError):
                issues.append("scope_path_invalid:" + field)
    for write in normalized["write_paths"]:
        for blocked in normalized["blocked_paths"]:
            if (write == blocked or write.startswith(blocked + "/")
                    or blocked.startswith(write + "/")):
                issues.append("write_path_blocked")
    return sorted(set(issues)), normalized
