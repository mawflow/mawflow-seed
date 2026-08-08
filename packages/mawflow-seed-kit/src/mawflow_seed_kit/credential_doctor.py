from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
from typing import Any


_CONFIG_SUFFIXES = {".env", ".ini", ".conf", ".properties", ".json", ".toml", ".yaml", ".yml"}
_CONFIG_NAMES = {"Dockerfile", "docker-compose.yml", "docker-compose.yaml", "application.yml", "application.yaml"}
_SOURCE_SUFFIXES = {".go", ".java", ".js", ".jsx", ".kt", ".php", ".py", ".rb", ".rs", ".ts", ".tsx"}
_SECRET_KEY = r"password|passwd|token|api[_-]?key|secret(?:[_-]?key)?|private[_-]?key|connection[_-]?string|webhook[_-]?url|refresh[_-]?token"
_PUBLIC_KEY = r"host|hostname|server|port|database|service|provider"
_ASSIGNMENT_RE = re.compile(
    rf"(?i)^\s*(?:\"(?P<double>{_SECRET_KEY})\"|'(?P<single>{_SECRET_KEY})'|(?P<plain>{_SECRET_KEY}))"
    r"\s*[=:]\s*[\"']?(?P<value>[^\s\"'#,;]{6,})"
)
_PUBLIC_FIELD_RE = re.compile(
    rf"(?i)^\s*(?:\"(?P<double>{_PUBLIC_KEY})\"|'(?P<single>{_PUBLIC_KEY})'|(?P<plain>{_PUBLIC_KEY}))"
    r"\s*[=:]\s*[\"']?(?P<value>[^\s\"'#,;]+)"
)
_SAFE_PREFIXES = ("mawsec://", "mawlocal://", "mawproxy://", "${", "$", "{{", "<")
_SAFE_WORDS = {
    "changeme", "dummy", "example", "example-only", "fake", "none", "null", "placeholder",
    "redacted", "replace-me", "secret", "test", "true", "false", "unknown",
}


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _tracked_paths(root: Path) -> list[Path]:
    completed = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if completed.returncode != 0:
        return []
    paths: list[Path] = []
    for raw in completed.stdout.split(b"\0"):
        if not raw:
            continue
        try:
            relative = Path(raw.decode("utf-8"))
        except UnicodeDecodeError:
            continue
        if relative.parts and relative.parts[0] in {".git", ".local", "artifacts", "node_modules", "vendor"}:
            continue
        candidate = (root / relative).resolve()
        if candidate.is_file() and not candidate.is_symlink():
            paths.append(candidate)
    return paths


def _is_scan_target(relative: Path, *, include_source: bool) -> bool:
    if relative.name in _CONFIG_NAMES or relative.suffix.lower() in _CONFIG_SUFFIXES:
        return True
    return include_source and relative.suffix.lower() in _SOURCE_SUFFIXES


def _safe_value(value: str) -> bool:
    normalized = value.strip().strip("\"'").lower()
    if not normalized or normalized in _SAFE_WORDS:
        return True
    if normalized.startswith(_SAFE_PREFIXES):
        return True
    if any(marker in normalized for marker in ("<", ">", "example.com", "localhost", "127.0.0.1")):
        return True
    if normalized.endswith(("_ref", "-ref")):
        return True
    return False


def scan_credentials(
    root: Path | str,
    *,
    include_source: bool = False,
    max_files: int = 4000,
    max_bytes: int = 64 * 1024 * 1024,
) -> dict[str, Any]:
    project_root = Path(root).resolve()
    findings: list[dict[str, Any]] = []
    resource_candidates: dict[str, dict[str, Any]] = {}
    scanned_files = 0
    scanned_bytes = 0
    truncated = False
    for path in _tracked_paths(project_root):
        relative = path.relative_to(project_root)
        if not _is_scan_target(relative, include_source=include_source):
            continue
        size = path.stat().st_size
        if scanned_files >= max_files or scanned_bytes + size > max_bytes:
            truncated = True
            break
        if size > 2 * 1024 * 1024:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        scanned_files += 1
        scanned_bytes += size
        public_fields: dict[str, str] = {}
        for line_number, line in enumerate(text.splitlines(), 1):
            for public_match in _PUBLIC_FIELD_RE.finditer(line):
                public_key = next(
                    value
                    for value in (
                        public_match.group("double"),
                        public_match.group("single"),
                        public_match.group("plain"),
                    )
                    if value
                )
                public_fields[public_key.lower()] = public_match.group("value")
            for match in _ASSIGNMENT_RE.finditer(line):
                field = next(
                    value
                    for value in (
                        match.group("double"),
                        match.group("single"),
                        match.group("plain"),
                    )
                    if value
                ).lower().replace("-", "_")
                value = match.group("value").rstrip(")]}")
                if _safe_value(value):
                    continue
                fingerprint = hashlib.sha256(
                    f"mawflow-doctor-v3\0{field}\0{value}".encode("utf-8")
                ).hexdigest()
                stable = hashlib.sha256(
                    f"{relative.as_posix()}\0{line_number}\0{field}\0{fingerprint}".encode("utf-8")
                ).hexdigest()[:24]
                findings.append(
                    {
                        "finding_key": f"tracked-secret-{stable}",
                        "source_ref": relative.as_posix(),
                        "line": line_number,
                        "field_name": field,
                        "severity": "hard",
                        "confidence": "high",
                        "tracked": True,
                        "value_fingerprint": f"SHA256:{fingerprint}",
                        "duplicate_group_key": f"duplicate-{fingerprint[:20]}",
                        "raw_value_in_report": False,
                        "recommended_action": "move_to_secret_store_and_replace_with_runtime_reference",
                    }
                )
        if public_fields:
            identity = json.dumps(public_fields, ensure_ascii=True, sort_keys=True)
            key = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:20]
            resource_candidates[key] = {
                "candidate_key": f"resource-{key}",
                "source_ref": relative.as_posix(),
                "public_fields": public_fields,
                "requires_confirmation": True,
                "auto_create_allowed": False,
            }
    duplicate_counts: dict[str, int] = {}
    for finding in findings:
        group = str(finding["duplicate_group_key"])
        duplicate_counts[group] = duplicate_counts.get(group, 0) + 1
    history_warning = bool(findings and (project_root / ".git").exists())
    return {
        "schema": "mawflow.seed_credential_doctor.v3",
        "status": "unsafe" if findings else "ready",
        "scanned_at": _utcnow(),
        "scan_scope": "tracked_config_and_source" if include_source else "tracked_configuration_only",
        "scanned_file_count": scanned_files,
        "scanned_bytes": scanned_bytes,
        "truncated": truncated,
        "finding_count": len(findings),
        "hard_blocker_count": len(findings),
        "duplicate_group_count": sum(1 for count in duplicate_counts.values() if count > 1),
        "findings": findings,
        "resource_candidates": list(resource_candidates.values()),
        "history_exposure": {
            "possible": history_warning,
            "rotation_required_after_cleanup": history_warning,
            "history_rewrite_automatic": False,
        },
        "remediation": {
            "mode": "preview_then_confirm",
            "secret_store_write_before_reference_change": True,
            "multi_file_atomic_changeset_required": True,
            "rollback_required": True,
        },
        "trust_boundary": {
            "plaintext_values_returned": False,
            "source_scan_default_enabled": False,
            "tracked_plaintext_fail_closed": True,
        },
    }
