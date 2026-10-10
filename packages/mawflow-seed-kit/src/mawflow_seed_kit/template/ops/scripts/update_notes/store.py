"""Append-only update-note fragments; generated Markdown is a projection."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

import yaml

LATEST = "docs/updates/updates.md"
HISTORY = "docs/updates/CHANGELOG.md"
CLOUD = "docs/handbooks/release-ops/updates.md"
CATEGORIES = {
    "added": "新增",
    "changed": "优化",
    "fixed": "修复",
    "removed": "移除",
    "security": "安全",
    "docs": "文档",
}
DELIVERY = {
    "implemented": "开发完成",
    "released": "已发布",
    "historical": "历史记录，发布状态见来源",
}
VALIDATION = {
    "unverified": "未独立复验",
    "automated_passed": "自动验证通过",
    "human_accepted": "真人验收通过",
}
KEY = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_.-]{0,159}\Z")
PRIVATE = {
    ".git",
    ".local",
    ".ssh",
    "runtime",
    "workspaces",
    "artifacts",
    "prompts",
    "node_modules",
    "dist",
    "build",
}
SENSITIVE_PATTERN = re.compile(
    r"(?i)(-----BEGIN .*PRIVATE KEY|\bsk-[A-Za-z0-9_-]{12,}|\b(?:password|passwd|token|secret|api[_-]?key)\s*[:=]\s*[^\s<>{}\[\]`]{8,})"
)
ABSOLUTE = re.compile(r"(?:^|[\s`\"'(])(?:/(?:home|Users|tmp|var|opt)/|[A-Za-z]:[\\/])")
MAX_FILE = 256 * 1024
MAX_RECORDS = 10000


def digest(value) -> str:
    return hashlib.sha256(
        json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode()
    ).hexdigest()


def safe_path(root: Path, relative: str) -> Path:
    if not isinstance(relative, str):
        raise ValueError("unsafe_relative_path")
    path = Path(relative)
    if (
        not relative
        or path.is_absolute()
        or ".." in path.parts
        or "\\" in relative
        or ":" in relative
    ):
        raise ValueError("unsafe_relative_path")
    if (
        PRIVATE.intersection(path.parts)
        or path.parts[:2] == ("docs", "archive")
        or "payload" in path.parts
    ):
        raise ValueError("private_path_forbidden")
    if any(part.endswith((".local.yaml", ".local.yml")) for part in path.parts):
        raise ValueError("private_path_forbidden")
    target = root
    for part in path.parts:
        target = target / part
        if target.is_symlink():
            raise ValueError("symlink_forbidden")
    target.resolve().relative_to(root.resolve())
    return target


def safe_text(value, limit=2000) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or len(value) > limit
        or "\n" in value
        or "\r" in value
    ):
        raise ValueError("invalid_note_text")
    if SENSITIVE_PATTERN.search(value) or ABSOLUTE.search(value):
        raise ValueError("sensitive_note_text")
    return value


def timestamp(value: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError("invalid_occurred_at")
    try:
        parsed = datetime.fromisoformat(value)
    except (ValueError, TypeError):
        raise ValueError("invalid_occurred_at") from None
    if parsed.tzinfo is None:
        raise ValueError("occurred_at_timezone_required")
    return parsed.astimezone(timezone.utc)


def validate(root: Path, item: dict) -> dict:
    if (
        not isinstance(item, dict)
        or item.get("schema_version") != 1
        or item.get("record_type") != "update_note"
        or item.get("operation") != "append"
    ):
        raise ValueError("invalid_update_fragment")
    if set(item) - {
        "schema_version",
        "record_key",
        "task_key",
        "record_type",
        "operation",
        "payload",
        "evidence_refs",
    }:
        raise ValueError("unknown_fragment_field")
    for key in ("record_key", "task_key"):
        if not isinstance(item.get(key), str) or not KEY.fullmatch(item[key]):
            raise ValueError("invalid_record_identity")
    payload = item.get("payload")
    required = {
        "schema",
        "occurred_at",
        "title",
        "summary",
        "category",
        "module_key",
        "module_name",
        "delivery_state",
        "validation_state",
        "importance",
        "audience",
        "details",
    }
    if (
        not isinstance(payload, dict)
        or not required.issubset(payload)
        or set(payload) - required - {"version", "supersedes", "provenance"}
    ):
        raise ValueError("invalid_note_fields")
    if payload["schema"] != "mawflow.update_note.v1":
        raise ValueError("invalid_note_schema")
    timestamp(payload["occurred_at"])
    for key in ("title", "summary", "module_name"):
        safe_text(payload[key], 4000 if key == "summary" else 2000)
    if not isinstance(payload["module_key"], str) or not KEY.fullmatch(
        payload["module_key"]
    ):
        raise ValueError("invalid_module_key")
    for key, values in (
        ("category", CATEGORIES),
        ("delivery_state", DELIVERY),
        ("validation_state", VALIDATION),
        ("importance", {"normal", "important"}),
        ("audience", {"project", "public"}),
    ):
        if not isinstance(payload[key], str) or payload[key] not in values:
            raise ValueError("invalid_" + key)
    if payload.get("version"):
        safe_text(payload["version"], 256)
    if payload.get("supersedes") and (
        not isinstance(payload["supersedes"], str)
        or not KEY.fullmatch(payload["supersedes"])
    ):
        raise ValueError("invalid_supersedes")
    details = payload["details"]
    if not isinstance(details, list) or not details or len(details) > 10:
        raise ValueError("details_required")
    for detail in details:
        if not isinstance(detail, dict) or set(detail) not in (
            {"label", "path"},
            {"label", "url"},
        ):
            raise ValueError("invalid_detail")
        safe_text(detail["label"], 80)
        if "path" in detail:
            safe_path(root, detail["path"])
        else:
            safe_text(detail["url"], 1000)
            url = urlsplit(detail["url"])
            if (
                url.scheme != "https"
                or not url.hostname
                or url.username
                or url.password
                or url.query
                or any(c in detail["url"] for c in '<>"\\ \t')
            ):
                raise ValueError("unsafe_detail_url")
    evidence = item.get("evidence_refs")
    if not isinstance(evidence, list) or not evidence:
        raise ValueError("evidence_refs_required")
    for ref in evidence:
        if (
            not isinstance(ref, dict)
            or set(ref) - {"path", "kind", "sha256"}
            or not {"path", "kind"}.issubset(ref)
        ):
            raise ValueError("invalid_evidence_ref")
        safe_path(root, ref["path"])
        safe_text(ref["kind"], 80)
        if "sha256" in ref and not re.fullmatch(r"[0-9a-f]{64}", ref["sha256"]):
            raise ValueError("invalid_evidence_hash")
    if payload["delivery_state"] == "released" and not any(
        ref["kind"] == "release_record" for ref in evidence
    ):
        raise ValueError("released_note_requires_release_evidence")
    if payload["validation_state"] == "human_accepted" and not any(
        ref["kind"] == "human_acceptance" for ref in evidence
    ):
        raise ValueError("human_acceptance_evidence_required")
    provenance = payload.get("provenance")
    if provenance is not None:
        if (
            not isinstance(provenance, dict)
            or set(provenance) != {"kind", "source_path", "source_sha256"}
            or provenance["kind"] != "module_changelog_table"
        ):
            raise ValueError("invalid_provenance")
        safe_path(root, provenance["source_path"])
        if not re.fullmatch(r"[0-9a-f]{64}", provenance["source_sha256"]):
            raise ValueError("invalid_provenance_hash")
    return item


def read_mapping(path: Path) -> dict:
    if path.stat().st_size > MAX_FILE:
        raise ValueError("source_file_too_large")
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("mapping_required")
    return value


def load_notes(root: Path) -> tuple[list[dict], list[str]]:
    directory = safe_path(root, ".maw/changes")
    paths = sorted(directory.glob("*.yaml"))
    if len(paths) > MAX_RECORDS:
        raise ValueError("record_budget_exceeded")
    records, warnings = {}, []
    for path in paths:
        safe_path(root, path.relative_to(root).as_posix())
        raw = read_mapping(path)
        if raw.get("record_type") != "update_note":
            continue
        item = validate(root, raw)
        key = item["record_key"]
        if key in records and digest(records[key]) != digest(item):
            raise ValueError("conflicting_record_identity:" + key)
        records[key] = item
        for ref in item["evidence_refs"]:
            target = safe_path(root, ref["path"])
            if not target.is_file():
                warnings.append("evidence_missing:" + key)
            elif (
                ref.get("sha256")
                and hashlib.sha256(target.read_bytes()).hexdigest() != ref["sha256"]
            ):
                warnings.append("historical_evidence_changed:" + key)
    replaced = set()
    for item in records.values():
        parent = item["payload"].get("supersedes")
        if not parent:
            continue
        if parent not in records or parent == item["record_key"]:
            raise ValueError("invalid_supersedes_reference")
        if records[parent]["payload"]["module_key"] != item["payload"][
            "module_key"
        ] or timestamp(records[parent]["payload"]["occurred_at"]) >= timestamp(
            item["payload"]["occurred_at"]
        ):
            raise ValueError("invalid_revision_order_or_module")
        if parent in replaced:
            raise ValueError("conflicting_revision_requires_review")
        replaced.add(parent)
    active = list(records.values())
    active.sort(
        key=lambda item: (
            timestamp(item["payload"]["occurred_at"]),
            item["record_key"],
        ),
        reverse=True,
    )
    return active, sorted(set(warnings))


def write_bytes(root: Path, relative: str, content: bytes, *, append=False) -> bool:
    target = safe_path(root, relative)
    if target.exists():
        if target.read_bytes() == content:
            return False
        if append:
            raise ValueError("immutable_record_conflict")
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".update-note-", dir=target.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        if append:
            try:
                os.link(name, target)
            except FileExistsError:
                if target.read_bytes() == content:
                    return False
                raise ValueError("immutable_record_conflict") from None
        else:
            os.replace(name, target)
        if target.read_bytes() != content:
            raise ValueError("write_readback_failed")
        return True
    finally:
        Path(name).unlink(missing_ok=True)
