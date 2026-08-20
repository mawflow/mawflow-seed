#!/usr/bin/env python3
"""Plan or execute migration of legacy module changelogs.

The migration is intentionally conservative: it reads the module index, moves
legacy per-module changelog tables into docs/changelogs/<module_key>.md, removes
duplicated inline history sections from module.md, and rewrites the machine and
human references to changelog_path/changelog_time.  Re-running the command must
produce an empty plan.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

try:
    import yaml
except ImportError as exc:  # pragma: no cover - dependency guard
    raise SystemExit("PyYAML is required to migrate module changelogs") from exc


EXIT_SUCCESS = 0
EXIT_NEEDS_AI = 10
EXIT_INPUT_ERROR = 20
EXIT_BOUNDARY_BLOCKED = 30
EXIT_SCRIPT_ERROR = 50

LEGACY_INLINE_HEADING = re.compile(
    r"^(?P<marks>#{2,6})\s+(?:\d+[A-Za-z]?\.\s*)?(?:最近变更摘要|变更记录|变更历史|Changelog)\s*$",
    re.IGNORECASE | re.MULTILINE,
)
REFERENCE_HEADING = re.compile(
    r"^(?P<marks>#{2,6})\s+(?:\d+[A-Za-z]?\.\s*)?变更日志引用\s*$",
    re.MULTILINE,
)
CHANGELOG_FIELD = re.compile(r"(?m)^\s*-\s*changelog_(?:path|time):.*\n?")
TABLE_SEPARATOR = re.compile(r"^:?-{3,}:?$")
CHANGELOG_RELEASE_HEADING = re.compile(
    r"^##\s+(?P<release_line>1\.0(?:\s+基线历史)?|2\.0)\s*$"
)
BASELINE_RELEASE_LINE = "1.0"
CURRENT_RELEASE_LINE = "2.0"
CHANGELOG_TABLE_HEADER = """| 日期 | 版本/提交 | 来源任务 | 变更类型 | 摘要 | doc_status | 文档同步 |
| --- | --- | --- | --- | --- | --- | --- |"""
MODULE_KEY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


@dataclass(frozen=True)
class ChangeEntry:
    changed_at: str
    version: str
    source: str
    change_type: str
    summary: str
    doc_status: str
    doc_sync: str
    source_module_key: str
    release_line: str = BASELINE_RELEASE_LINE

    @property
    def entry_key(self) -> str:
        normalized = re.sub(r"\s+", " ", self.summary.strip()).lower()
        digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:12]
        return f"{self.release_line}|{self.changed_at}|{self.version}|{digest}"

    def row(self) -> str:
        values = [
            self.changed_at,
            self.version,
            self.source,
            self.change_type,
            self.summary,
            self.doc_status,
            self.doc_sync,
        ]
        escaped = [value.replace("|", "\\|").replace("\n", " ").strip() for value in values]
        return "| " + " | ".join(escaped) + " |"


@dataclass
class ModulePlan:
    key: str
    name: str
    doc_path: Path
    legacy_path: Optional[Path]
    target_path: Path
    changelog_time: str
    target_content: str
    module_content: str
    entries: List[ChangeEntry] = field(default_factory=list)
    changed_paths: List[Path] = field(default_factory=list)
    delete_paths: List[Path] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class FileSnapshot:
    content: Optional[str]
    mode: Optional[int]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Plan, execute, or check centralized module changelog migration."
    )
    parser.add_argument("command", nargs="?", choices=["plan", "migrate", "check"], default="plan")
    parser.add_argument("--root", default=".", help="Project root. Default: current directory.")
    parser.add_argument("--module-key", action="append", default=[], help="Only inspect selected module key; repeatable.")
    parser.add_argument("--execute", action="store_true", help="Write the migration. Required with command=migrate.")
    parser.add_argument("--dry-run", action="store_true", help="Compatibility alias for command=plan.")
    parser.add_argument("--format", choices=["json", "markdown", "text"], default="json")
    parser.add_argument("--output", default="-", help="Output path or '-' for stdout.")
    return parser


def relative(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root).as_posix()


def validate_module_key(value: str) -> str:
    if not MODULE_KEY.fullmatch(value):
        raise ValueError(
            f"invalid module key {value!r}: expected one safe path segment"
        )
    return value


def validated_project_path(
    root: Path,
    value: str,
    *,
    module_key: str,
    field_name: str,
) -> Tuple[PurePosixPath, Path]:
    """Return a project-relative POSIX path after rejecting escape attempts."""

    if not value or "\x00" in value or "\\" in value:
        raise ValueError(
            f"module {module_key} has invalid {field_name} path: {value!r}"
        )
    project_path = PurePosixPath(value)
    if (
        project_path.is_absolute()
        or value.startswith("./")
        or value != project_path.as_posix()
        or any(part in {"", ".", ".."} for part in project_path.parts)
    ):
        raise ValueError(
            f"module {module_key} {field_name} must be a normalized project-relative path: {value}"
        )
    resolved_root = root.resolve()
    lexical_path = resolved_root / Path(*project_path.parts)
    resolved_path = lexical_path.resolve()
    try:
        resolved_path.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError(
            f"module {module_key} {field_name} escapes project root: {value}"
        ) from exc
    if resolved_path != lexical_path:
        raise ValueError(
            f"module {module_key} {field_name} must not resolve through a symlink: {value}"
        )
    return project_path, resolved_path


def validate_module_paths(
    root: Path,
    module_key: str,
    doc_value: str,
    legacy_value: str,
    target_value: str,
) -> Tuple[Path, Optional[Path], Path]:
    """Validate each path field against its one allowed document role."""

    key = validate_module_key(module_key)
    doc_relative, doc_path = validated_project_path(
        root,
        doc_value,
        module_key=key,
        field_name="doc",
    )
    if (
        len(doc_relative.parts) < 4
        or doc_relative.parts[:2] != ("docs", "modules")
        or doc_relative.parts[-2:] != (key, "module.md")
    ):
        raise ValueError(
            f"module {key} doc must be docs/modules/**/{key}/module.md: {doc_value}"
        )

    expected_target = PurePosixPath("docs", "changelogs", f"{key}.md")
    target_relative, target_path = validated_project_path(
        root,
        target_value,
        module_key=key,
        field_name="changelog_path",
    )
    if target_relative != expected_target:
        raise ValueError(
            f"module {key} changelog_path must be {expected_target.as_posix()}: {target_value}"
        )

    legacy_path: Optional[Path] = None
    if legacy_value:
        legacy_relative, legacy_path = validated_project_path(
            root,
            legacy_value,
            module_key=key,
            field_name="changelog",
        )
        expected_legacy = doc_relative.parent / "changelog.md"
        if legacy_relative != expected_legacy:
            raise ValueError(
                f"module {key} changelog must be the changelog.md beside its module doc "
                f"({expected_legacy.as_posix()}): {legacy_value}"
            )

    index_path = (root.resolve() / ".maw" / "modules.yaml").resolve()
    protected_paths = {index_path, doc_path}
    if target_path in protected_paths or (legacy_path and legacy_path in protected_paths):
        raise ValueError(
            f"module {key} changelog path overlaps a protected index or module document"
        )
    role_paths = {
        "doc": doc_path,
        "changelog_path": target_path,
        **({"changelog": legacy_path} if legacy_path else {}),
    }
    existing_roles = [
        (role, path) for role, path in role_paths.items() if path.exists()
    ]
    if doc_path.exists() and index_path.exists() and os.path.samefile(doc_path, index_path):
        raise ValueError(f"module {key} doc aliases the protected module index")
    for position, (left_role, left_path) in enumerate(existing_roles):
        if index_path.exists() and os.path.samefile(left_path, index_path):
            raise ValueError(
                f"module {key} {left_role} aliases the protected module index"
            )
        for right_role, right_path in existing_roles[position + 1 :]:
            if os.path.samefile(left_path, right_path):
                raise ValueError(
                    f"module {key} path roles {left_role} and {right_role} alias the same file"
                )
    return doc_path, legacy_path, target_path


def validate_changelog_time(value: str, module_key: str) -> None:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"module {module_key} has invalid changelog_time: {value}") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"module {module_key} changelog_time must include a timezone: {value}")


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    previous_mode = path.stat().st_mode & 0o777 if path.exists() else None
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(content)
        os.replace(temp_name, path)
        if previous_mode is not None:
            path.chmod(previous_mode)
    except Exception:
        Path(temp_name).unlink(missing_ok=True)
        raise


def snapshot_files(paths: Iterable[Path]) -> Dict[Path, FileSnapshot]:
    snapshots: Dict[Path, FileSnapshot] = {}
    for path in paths:
        if path.exists():
            if not path.is_file():
                raise ValueError(f"cannot safely migrate non-file path: {path}")
            snapshots[path] = FileSnapshot(
                path.read_text(encoding="utf-8"),
                path.stat().st_mode & 0o777,
            )
        else:
            snapshots[path] = FileSnapshot(None, None)
    return snapshots


def restore_files(snapshots: Dict[Path, FileSnapshot]) -> None:
    errors: List[str] = []
    for path, snapshot in snapshots.items():
        try:
            if snapshot.content is None:
                path.unlink(missing_ok=True)
                continue
            atomic_write(path, snapshot.content)
            if snapshot.mode is not None:
                path.chmod(snapshot.mode)
        except Exception as exc:  # pragma: no cover - catastrophic recovery guard
            errors.append(f"{path}: {exc}")
    if errors:
        raise RuntimeError("rollback failed: " + "; ".join(errors))


def read_modules(index_path: Path) -> Tuple[Dict[str, Any], str]:
    raw = index_path.read_text(encoding="utf-8")
    payload = yaml.safe_load(raw) or {}
    modules = payload.get("modules")
    if not isinstance(modules, list):
        raise ValueError(".maw/modules.yaml must contain a modules list")
    return payload, raw


def parse_cells(line: str) -> List[str]:
    body = line.strip().strip("|")
    return [cell.strip().replace("\\|", "|") for cell in re.split(r"(?<!\\)\|", body)]


def canonical_header(value: str) -> str:
    return re.sub(r"[\s`_*]", "", value).lower()


def extract_table_entries(
    text: str,
    module_key: str,
    *,
    preserve_release_sections: bool = False,
) -> List[ChangeEntry]:
    lines = text.splitlines()
    entries: List[ChangeEntry] = []
    index = 0
    release_line = BASELINE_RELEASE_LINE
    while index + 1 < len(lines):
        heading_match = CHANGELOG_RELEASE_HEADING.match(lines[index].strip())
        if preserve_release_sections and heading_match:
            release_line = (
                CURRENT_RELEASE_LINE
                if heading_match.group("release_line") == CURRENT_RELEASE_LINE
                else BASELINE_RELEASE_LINE
            )
            index += 1
            continue
        if not lines[index].lstrip().startswith("|") or not lines[index + 1].lstrip().startswith("|"):
            index += 1
            continue
        headers = parse_cells(lines[index])
        separators = parse_cells(lines[index + 1])
        if len(headers) != len(separators) or not all(TABLE_SEPARATOR.match(cell) for cell in separators):
            index += 1
            continue
        normalized = [canonical_header(header) for header in headers]
        if "日期" not in normalized or not any("摘要" in header for header in normalized):
            index += 2
            continue
        index += 2
        while index < len(lines) and lines[index].lstrip().startswith("|"):
            cells = parse_cells(lines[index])
            if len(cells) == len(headers):
                values = dict(zip(normalized, cells))
                summary_key = next((key for key in normalized if "摘要" in key), "")
                source_key = next((key for key in normalized if key in {"来源任务", "任务/提交", "任务", "来源"}), "")
                version_key = next((key for key in normalized if key in {"版本/提交", "版本", "commit"}), "")
                type_key = next((key for key in normalized if key in {"变更类型", "类型"}), "")
                status_key = next((key for key in normalized if key == "doc_status"), "")
                sync_key = next((key for key in normalized if key in {"文档同步", "是否更新档案"}), "")
                changed_at = values.get("日期", "").strip()
                summary = values.get(summary_key, "").strip()
                if changed_at and summary:
                    entries.append(
                        ChangeEntry(
                            changed_at=changed_at,
                            version=values.get(version_key, "pending") or "pending",
                            source=values.get(source_key, "历史迁移") or "历史迁移",
                            change_type=values.get(type_key, "docs") or "docs",
                            summary=summary,
                            doc_status=values.get(status_key, "confirmed") or "confirmed",
                            doc_sync=values.get(sync_key, "已迁移到集中日志") or "已迁移到集中日志",
                            source_module_key=module_key,
                            release_line=release_line,
                        )
                    )
            index += 1
    return entries


def extract_bullet_entries(text: str, module_key: str) -> List[ChangeEntry]:
    entries: List[ChangeEntry] = []
    current_date = ""
    for raw_line in text.splitlines():
        line = raw_line.strip()
        date_match = re.match(r"^(?:#{2,6}\s+|[-*]\s+)?(20\d{2}-\d{2}-\d{2})(?:[：:\s-]+)(.*)$", line)
        if date_match:
            current_date = date_match.group(1)
            tail = date_match.group(2).strip(" ：:-")
            if tail:
                entries.append(
                    ChangeEntry(current_date, "pending", "旧格式内嵌记录", "docs", tail, "confirmed", "已迁移到集中日志", module_key)
                )
            continue
        bullet_match = re.match(r"^[-*]\s+(.+)$", line)
        if bullet_match and current_date:
            summary = bullet_match.group(1).strip()
            if summary:
                entries.append(
                    ChangeEntry(current_date, "pending", "旧格式内嵌记录", "docs", summary, "confirmed", "已迁移到集中日志", module_key)
                )
    return entries


def section_span(text: str, heading_match: re.Match[str]) -> Tuple[int, int]:
    start = heading_match.start()
    level = len(heading_match.group("marks"))
    next_heading = re.compile(rf"^#{{1,{level}}}\s+", re.MULTILINE).search(text, heading_match.end())
    return start, next_heading.start() if next_heading else len(text)


def inline_history_details(
    text: str, module_key: str
) -> Tuple[str, List[ChangeEntry], bool, List[Tuple[str, str]]]:
    remaining = text
    entries: List[ChangeEntry] = []
    sources: List[Tuple[str, str]] = []
    found = False
    while True:
        match = LEGACY_INLINE_HEADING.search(remaining)
        if not match:
            break
        found = True
        start, end = section_span(remaining, match)
        section = remaining[start:end]
        section_entries = extract_table_entries(
            section, module_key
        ) + extract_bullet_entries(section, module_key)
        if not section_entries:
            heading = match.group(0).strip()
            raise ValueError(
                f"module {module_key} inline history section {heading!r} has no safely parseable entries; "
                "migration stopped without writing or deleting files"
            )
        entries.extend(section_entries)
        sources.append((match.group(0).strip(), section.rstrip()))
        prefix = remaining[:start].rstrip()
        suffix = remaining[end:].lstrip("\n")
        if prefix and suffix:
            remaining = prefix + "\n\n" + suffix
        elif prefix:
            remaining = prefix + "\n"
        else:
            remaining = suffix
    return remaining, entries, found, sources


def inline_history(text: str, module_key: str) -> Tuple[str, List[ChangeEntry], bool]:
    remaining, entries, found, _sources = inline_history_details(text, module_key)
    return remaining, entries, found


def existing_reference_removed(text: str) -> str:
    match = REFERENCE_HEADING.search(text)
    if match:
        start, end = section_span(text, match)
        text = text[:start].rstrip() + "\n" + text[end:].lstrip()
    return CHANGELOG_FIELD.sub("", text)


def add_reference(text: str, target: str, changed_at: str) -> str:
    clean = existing_reference_removed(text).rstrip()
    return (
        clean
        + "\n\n## 变更日志引用\n\n"
        + f"- changelog_path: `{target}`\n"
        + f"- changelog_time: `{changed_at}`\n"
    )


def deduplicate(entries: Iterable[ChangeEntry]) -> List[ChangeEntry]:
    result: List[ChangeEntry] = []
    by_key: Dict[str, ChangeEntry] = {}
    for entry in entries:
        previous = by_key.get(entry.entry_key)
        if previous is not None:
            if previous != entry:
                raise ValueError(f"conflicting changelog entry: {entry.entry_key}")
            continue
        by_key[entry.entry_key] = entry
        result.append(entry)
    return result


def render_changelog(module_key: str, module_name: str, entries: Sequence[ChangeEntry]) -> str:
    unsupported_release_lines = sorted(
        {
            entry.release_line
            for entry in entries
            if entry.release_line not in {BASELINE_RELEASE_LINE, CURRENT_RELEASE_LINE}
        }
    )
    if unsupported_release_lines:
        raise ValueError(
            f"unsupported changelog release line: {', '.join(unsupported_release_lines)}"
        )
    baseline_rows = "\n".join(
        entry.row() for entry in entries if entry.release_line == BASELINE_RELEASE_LINE
    )
    if not baseline_rows:
        baseline_rows = "|  |  |  |  |  | confirmed |  |"
    current_rows = "\n".join(
        entry.row() for entry in entries if entry.release_line == CURRENT_RELEASE_LINE
    )
    current_table = (
        f"\n\n{CHANGELOG_TABLE_HEADER}\n{current_rows}" if current_rows else ""
    )
    return f'''---
doc_key: docs.changelogs.{module_key}
doc_type: module_changelog
stage: development
status: active
owner: planner
tags:
  - modules
  - changelog
entities:
  modules:
    - {module_key}
project_health:
  dimensions:
    - product_module_design
  evidence_level: canonical
read_contract:
  summary: "{module_name}的集中变更日志。"
  health_signal: "用于追溯会影响模块边界、兼容性、状态机、安全、数据或发布语义的实质变化。"
  consumes: []
  produces: []
  ai_read_hint: "仅在需要追溯{module_name}历史变化或更新实质变更时读取。"
---

# 模块变更日志：{module_name}

> 统一存储路径：`docs/changelogs/{module_key}.md`。例行样式、测试补充和措辞调整由 Git 历史追溯，不写入本日志。

## 1.0 基线历史

{CHANGELOG_TABLE_HEADER}
{baseline_rows}

## 2.0{current_table}

从 2.0 起，只记录产品/领域边界、API 或数据兼容、状态机、权限、安全、迁移、发布/回滚语义及模块生命周期变化。
'''


def _release_heading_matches(line: str, release_line: str) -> bool:
    match = CHANGELOG_RELEASE_HEADING.match(line.strip())
    if not match:
        return False
    matched_release = (
        CURRENT_RELEASE_LINE
        if match.group("release_line") == CURRENT_RELEASE_LINE
        else BASELINE_RELEASE_LINE
    )
    return matched_release == release_line


def _insert_release_entries(
    text: str,
    release_line: str,
    entries: Sequence[ChangeEntry],
) -> str:
    if not entries:
        return text
    lines = text.rstrip("\n").splitlines()
    heading_index = next(
        (
            index
            for index, line in enumerate(lines)
            if _release_heading_matches(line, release_line)
        ),
        -1,
    )
    if heading_index < 0:
        heading = (
            "## 1.0 基线历史"
            if release_line == BASELINE_RELEASE_LINE
            else "## 2.0"
        )
        block = [
            heading,
            "",
            *CHANGELOG_TABLE_HEADER.splitlines(),
            *(entry.row() for entry in entries),
            "",
        ]
        if release_line == BASELINE_RELEASE_LINE:
            insert_at = next(
                (
                    index
                    for index, line in enumerate(lines)
                    if _release_heading_matches(line, CURRENT_RELEASE_LINE)
                ),
                len(lines),
            )
        else:
            insert_at = len(lines)
        if insert_at and lines[insert_at - 1].strip():
            block.insert(0, "")
        lines[insert_at:insert_at] = block
        return "\n".join(lines).rstrip() + "\n"

    section_end = next(
        (
            index
            for index in range(heading_index + 1, len(lines))
            if re.match(r"^##\s+", lines[index])
        ),
        len(lines),
    )
    table_end = -1
    for index in range(heading_index + 1, max(heading_index + 1, section_end - 1)):
        if not lines[index].lstrip().startswith("|") or not lines[index + 1].lstrip().startswith("|"):
            continue
        headers = parse_cells(lines[index])
        separators = parse_cells(lines[index + 1])
        normalized = [canonical_header(header) for header in headers]
        if (
            len(headers) == len(separators)
            and all(TABLE_SEPARATOR.match(cell) for cell in separators)
            and "日期" in normalized
            and any("摘要" in header for header in normalized)
        ):
            table_end = index + 2
            while table_end < section_end and lines[table_end].lstrip().startswith("|"):
                table_end += 1
            break

    rows = [entry.row() for entry in entries]
    if table_end >= 0:
        lines[table_end:table_end] = rows
    else:
        block = ["", *CHANGELOG_TABLE_HEADER.splitlines(), *rows, ""]
        lines[section_end:section_end] = block
    return "\n".join(lines).rstrip() + "\n"


def merge_changelog(
    existing: Optional[str],
    module_key: str,
    module_name: str,
    entries: Sequence[ChangeEntry],
) -> str:
    """Merge parsed entries without rebuilding or dropping existing manual content."""

    if existing is None:
        return render_changelog(module_key, module_name, entries)
    existing_entries = deduplicate(
        extract_table_entries(existing, module_key, preserve_release_sections=True)
    )
    existing_keys = {entry.entry_key for entry in existing_entries}
    missing = [entry for entry in entries if entry.entry_key not in existing_keys]
    if not missing:
        return existing
    if "# 模块变更日志" not in existing or not any(
        CHANGELOG_RELEASE_HEADING.match(line.strip()) for line in existing.splitlines()
    ):
        raise ValueError(
            f"module {module_key} central changelog is non-canonical; cannot safely merge entries "
            "without overwriting existing content"
        )
    merged = existing
    for release_line in (BASELINE_RELEASE_LINE, CURRENT_RELEASE_LINE):
        merged = _insert_release_entries(
            merged,
            release_line,
            [entry for entry in missing if entry.release_line == release_line],
        )
    merged_keys = {
        entry.entry_key
        for entry in extract_table_entries(
            merged, module_key, preserve_release_sections=True
        )
    }
    missing_after_merge = [entry.entry_key for entry in entries if entry.entry_key not in merged_keys]
    if missing_after_merge:
        raise ValueError(
            f"module {module_key} central changelog merge could not preserve entries: "
            + ", ".join(missing_after_merge)
        )
    return merged


def append_migration_source(text: str, label: str, content: str) -> str:
    """Keep an auditable, lossless copy of removed legacy Markdown content."""

    normalized = content.strip()
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]
    marker = f"<!-- maw-migrated:{digest} -->"
    if marker in text:
        return text
    quoted = "\n".join(f"> {line}" if line else ">" for line in normalized.splitlines())
    return (
        text.rstrip()
        + f"\n\n{marker}\n### 迁移来源：`{label}`\n\n{quoted}\n"
    )


def replace_index_block(raw: str, key: str, target: str, changelog_time: str) -> str:
    block_pattern = re.compile(rf"(?ms)^  - key:\s*{re.escape(key)}\s*$.*?(?=^  - key:\s|\Z)")
    match = block_pattern.search(raw)
    if not match:
        raise ValueError(f"module block not found in .maw/modules.yaml: {key}")
    block = match.group(0)
    block = re.sub(r"(?m)^    changelog:\s*.*\n", "", block)
    block = re.sub(r"(?m)^    changelog_path:\s*.*\n", "", block)
    block = re.sub(r"(?m)^    changelog_time:\s*.*\n", "", block)
    doc_match = re.search(r"(?m)^    doc:\s*.*$", block)
    if not doc_match:
        raise ValueError(f"module {key} has no doc field")
    insert_at = doc_match.end()
    addition = f'\n    changelog_path: {target}\n    changelog_time: "{changelog_time}"'
    block = block[:insert_at] + addition + block[insert_at:]
    return raw[: match.start()] + block + raw[match.end() :]


def collect_plan(root: Path, selected: Sequence[str]) -> Tuple[List[ModulePlan], str, str]:
    index_path = root / ".maw" / "modules.yaml"
    payload, original_index = read_modules(index_path)
    updated_index = original_index
    now = datetime.now().astimezone().replace(microsecond=0).isoformat()
    plans: List[ModulePlan] = []
    selected_set = set(selected)
    known_keys = {str(item.get("key")) for item in payload["modules"] if isinstance(item, dict)}
    unknown = selected_set - known_keys
    if unknown:
        raise ValueError(f"unknown module_key: {', '.join(sorted(unknown))}")

    for item in payload["modules"]:
        if not isinstance(item, dict):
            continue
        key = str(item.get("key") or "").strip()
        legacy_value = str(item.get("changelog") or "").strip()
        has_target_field = "changelog_path" in item
        if selected_set and key not in selected_set:
            continue
        if not key:
            if legacy_value or has_target_field:
                raise ValueError("module changelog state has no module key")
            continue
        if not legacy_value and not has_target_field:
            continue
        target_value = str(item.get("changelog_path") or f"docs/changelogs/{key}.md").strip()
        doc_value = str(item.get("doc") or "").strip()
        if not doc_value:
            raise ValueError(f"module {key} changelog state has no doc field")
        name = str(item.get("name") or key).strip()
        doc_path, legacy_path, target_path = validate_module_paths(
            root,
            key,
            doc_value,
            legacy_value,
            target_value,
        )
        if not doc_path.is_file():
            raise ValueError(f"module doc does not exist: {doc_value}")
        if target_path.exists() and not target_path.is_file():
            raise ValueError(
                f"module {key} changelog_path is not a regular file: {target_value}"
            )

        target_existing = (
            target_path.read_text(encoding="utf-8") if target_path.is_file() else None
        )
        target_entries = (
            extract_table_entries(
                target_existing,
                key,
                preserve_release_sections=True,
            )
            if target_existing is not None
            else []
        )
        legacy_entries: List[ChangeEntry] = []
        migration_sources: List[Tuple[str, str]] = []
        if legacy_path:
            if not legacy_path.is_file():
                raise ValueError(
                    f"module {key} legacy changelog is referenced but is not a regular file: "
                    f"{legacy_value}; migration stopped without writing or deleting files"
                )
            legacy_text = legacy_path.read_text(encoding="utf-8")
            legacy_entries = extract_table_entries(legacy_text, key)
            if not legacy_entries:
                legacy_entries = extract_bullet_entries(legacy_text, key)
            if not legacy_entries:
                raise ValueError(
                    f"module {key} legacy changelog has no safely parseable entries: {legacy_value}; "
                    "migration stopped without writing or deleting files"
                )
            migration_sources.append((legacy_value, legacy_text))
        module_text = doc_path.read_text(encoding="utf-8")
        (
            module_without_history,
            inline_entries,
            had_inline,
            inline_sources,
        ) = inline_history_details(module_text, key)
        migration_sources.extend(
            (f"{doc_value}#{heading}", section)
            for heading, section in inline_sources
        )
        entries = deduplicate([*target_entries, *legacy_entries, *inline_entries])
        target_content = merge_changelog(target_existing, key, name, entries)
        for source_label, source_content in migration_sources:
            target_content = append_migration_source(
                target_content, source_label, source_content
            )

        existing_time = str(item.get("changelog_time") or "").strip()
        if existing_time:
            validate_changelog_time(existing_time, key)
        content_change = bool(
            legacy_value
            or had_inline
            or target_existing is None
            or target_content != target_existing
        )
        changelog_time = now if content_change or not existing_time else existing_time
        module_content = add_reference(
            module_without_history if had_inline else module_text,
            target_value,
            changelog_time,
        )
        plan = ModulePlan(
            key=key,
            name=name,
            doc_path=doc_path,
            legacy_path=legacy_path,
            target_path=target_path,
            changelog_time=changelog_time,
            target_content=target_content,
            module_content=module_content,
            entries=entries,
        )

        if target_existing is None or target_existing != target_content:
            plan.changed_paths.append(target_path)
        if module_content != module_text:
            plan.changed_paths.append(doc_path)
        if legacy_path:
            plan.delete_paths.append(legacy_path)

        new_index = replace_index_block(updated_index, key, target_value, changelog_time)
        if new_index != updated_index:
            updated_index = new_index
        plans.append(plan)

    return plans, original_index, updated_index


def validate_written_state(root: Path, plans: Sequence[ModulePlan], updated_index: str) -> None:
    index_path = root / ".maw" / "modules.yaml"
    if index_path.read_text(encoding="utf-8") != updated_index:
        raise RuntimeError("module index verification failed after write")
    index_payload, _ = read_modules(index_path)

    for plan in plans:
        target_value = relative(root, plan.target_path)
        if (
            not plan.target_path.is_file()
            or plan.target_path.read_text(encoding="utf-8") != plan.target_content
        ):
            raise RuntimeError(
                f"central changelog verification failed after write: {target_value}"
            )
        parsed_entries = deduplicate(
            extract_table_entries(
                plan.target_content,
                plan.key,
                preserve_release_sections=True,
            )
        )
        parsed_by_key = {entry.entry_key: entry for entry in parsed_entries}
        missing_or_changed = [
            entry.entry_key
            for entry in plan.entries
            if parsed_by_key.get(entry.entry_key) != entry
        ]
        if missing_or_changed:
            raise RuntimeError(
                f"central changelog entry verification failed for module {plan.key}: "
                + ", ".join(missing_or_changed)
            )

        if (
            not plan.doc_path.is_file()
            or plan.doc_path.read_text(encoding="utf-8") != plan.module_content
        ):
            raise RuntimeError(
                f"module document verification failed after write: {relative(root, plan.doc_path)}"
            )
        if LEGACY_INLINE_HEADING.search(plan.module_content):
            raise RuntimeError(
                f"legacy inline history remains after migration: {relative(root, plan.doc_path)}"
            )
        expected_reference = (
            f"- changelog_path: `{target_value}`\n"
            f"- changelog_time: `{plan.changelog_time}`"
        )
        if expected_reference not in plan.module_content:
            raise RuntimeError(f"module {plan.key} changelog reference verification failed")

        matching_items = [
            item
            for item in index_payload["modules"]
            if isinstance(item, dict) and str(item.get("key") or "").strip() == plan.key
        ]
        if len(matching_items) != 1:
            raise RuntimeError(
                f"module index must contain exactly one block for {plan.key} after migration"
            )
        item = matching_items[0]
        if (
            "changelog" in item
            or str(item.get("changelog_path") or "") != target_value
            or str(item.get("changelog_time") or "") != plan.changelog_time
        ):
            raise RuntimeError(f"module {plan.key} index reference verification failed")

        for legacy in plan.delete_paths:
            if not legacy.is_file():
                raise RuntimeError(
                    f"legacy changelog disappeared before verified deletion: {relative(root, legacy)}"
                )


def execute(root: Path, plans: Sequence[ModulePlan], original_index: str, updated_index: str) -> List[str]:
    index_path = root / ".maw" / "modules.yaml"
    snapshot_paths = {
        index_path,
        *(plan.target_path for plan in plans),
        *(plan.doc_path for plan in plans),
        *(path for plan in plans for path in plan.delete_paths),
    }
    snapshots = snapshot_files(snapshot_paths)
    changed: List[str] = []
    try:
        for plan in plans:
            if (
                not plan.target_path.is_file()
                or plan.target_path.read_text(encoding="utf-8") != plan.target_content
            ):
                atomic_write(plan.target_path, plan.target_content)
                changed.append(relative(root, plan.target_path))

            if plan.doc_path.read_text(encoding="utf-8") != plan.module_content:
                atomic_write(plan.doc_path, plan.module_content)
                changed.append(relative(root, plan.doc_path))

        if updated_index != original_index:
            atomic_write(index_path, updated_index)
            changed.append(".maw/modules.yaml")

        # All three destinations must match the plan before any legacy source is removed.
        validate_written_state(root, plans, updated_index)
        for plan in plans:
            for legacy in plan.delete_paths:
                legacy.unlink()
                changed.append(relative(root, legacy))
        return sorted(set(changed))
    except Exception as exc:
        try:
            restore_files(snapshots)
        except Exception as rollback_exc:  # pragma: no cover - catastrophic recovery guard
            raise RuntimeError(
                f"migration failed ({exc}); rollback also failed ({rollback_exc})"
            ) from exc
        raise


def build_result(root: Path, args: argparse.Namespace) -> Tuple[Dict[str, Any], int]:
    plans, original_index, updated_index = collect_plan(root, args.module_key)
    pending_paths = sorted(
        {
            relative(root, path)
            for plan in plans
            for path in [*plan.changed_paths, *plan.delete_paths]
        }
        | ({".maw/modules.yaml"} if updated_index != original_index else set())
    )
    mapped_legacy = {path.resolve() for plan in plans for path in plan.delete_paths}
    selected_keys = set(args.module_key)
    orphan_legacy = sorted(
        path
        for path in (root / "docs" / "modules").rglob("changelog.md")
        if "_template" not in path.parts and path.resolve() not in mapped_legacy
        and (not selected_keys or path.parent.name in selected_keys)
    )
    orphan_inline = sorted(
        path
        for path in (root / "docs" / "modules").rglob("module.md")
        if LEGACY_INLINE_HEADING.search(path.read_text(encoding="utf-8"))
        and all(path.resolve() != plan.doc_path.resolve() for plan in plans)
        and (not selected_keys or path.parent.name in selected_keys)
    )
    pending_paths = sorted(set(pending_paths) | {relative(root, path) for path in [*orphan_legacy, *orphan_inline]})
    changed_paths: List[str] = []
    status = "success"
    next_action = "continue"
    summary = f"{len(plans)} module changelog(s) inspected; {len(pending_paths)} path change(s) planned."

    if args.command == "migrate":
        if not args.execute:
            raise ValueError("command=migrate requires --execute")
        if orphan_legacy or orphan_inline:
            raise ValueError(
                "legacy module changelog content has no unique .maw/modules.yaml owner: "
                + ", ".join(relative(root, path) for path in [*orphan_legacy, *orphan_inline])
            )
        changed_paths = execute(root, plans, original_index, updated_index)
        summary = f"Migrated {len(plans)} module changelog(s); changed {len(changed_paths)} path(s)."
    elif args.command == "check" and pending_paths:
        status = "needs_ai"
        next_action = "ai_takeover"
        summary = f"Legacy or non-canonical module changelog state remains in {len(pending_paths)} path(s)."
    elif pending_paths:
        next_action = "run_migrate"

    result = {
        "status": status,
        "summary": summary,
        "next_action": next_action,
        "changed_paths": changed_paths,
        "planned_paths": pending_paths,
        "evidence_refs": [
            {"path": ".maw/modules.yaml", "kind": "module_index"},
            {"path": "docs/changelogs/README.md", "kind": "protocol"},
        ],
        "log_path": "",
        "state_path": "",
        "environment": {
            "os": platform.system().lower(),
            "python": f"{sys.version_info.major}.{sys.version_info.minor}",
            "workspace": "project_root",
            "root": ".",
        },
        "warnings": [warning for plan in plans for warning in plan.warnings],
        "ai_takeover_reason": "legacy_module_changelog" if status == "needs_ai" else "",
        "modules": [
            {
                "module_key": plan.key,
                "target": relative(root, plan.target_path),
                "entry_count": len(plan.entries),
                "changelog_time": plan.changelog_time,
            }
            for plan in plans
        ],
    }
    return result, EXIT_NEEDS_AI if status == "needs_ai" else EXIT_SUCCESS


def render(result: Dict[str, Any], output_format: str) -> str:
    if output_format == "json":
        return json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if output_format == "markdown":
        lines = [f"# {result['status']}", "", result["summary"], "", f"- next_action: {result['next_action']}"]
        lines.append(f"- planned_paths: {len(result['planned_paths'])}")
        lines.append(f"- changed_paths: {len(result['changed_paths'])}")
        return "\n".join(lines) + "\n"
    return (
        f"status: {result['status']}\n"
        f"summary: {result['summary']}\n"
        f"next_action: {result['next_action']}\n"
    )


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.dry_run:
        args.command = "plan"
    try:
        root = Path(args.root).expanduser().resolve()
        result, code = build_result(root, args)
    except ValueError as exc:
        result = {
            "status": "failed",
            "summary": str(exc),
            "next_action": "stop",
            "changed_paths": [],
            "planned_paths": [],
            "evidence_refs": [],
            "log_path": "",
            "state_path": "",
            "environment": {},
            "warnings": [],
            "ai_takeover_reason": "input_error",
            "modules": [],
        }
        code = EXIT_INPUT_ERROR
    except Exception as exc:  # pragma: no cover - shell-facing guard
        result = {
            "status": "failed",
            "summary": str(exc),
            "next_action": "ai_takeover",
            "changed_paths": [],
            "planned_paths": [],
            "evidence_refs": [],
            "log_path": "",
            "state_path": "",
            "environment": {},
            "warnings": [],
            "ai_takeover_reason": "script_exception",
            "modules": [],
        }
        code = EXIT_SCRIPT_ERROR

    output = render(result, args.format)
    if args.output == "-":
        print(output, end="")
    else:
        Path(args.output).write_text(output, encoding="utf-8")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
