from __future__ import annotations

import difflib
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import tempfile
from typing import Any

import yaml
from yaml.nodes import MappingNode, ScalarNode, SequenceNode

from mawflow_seed_kit import (
    apply_migration_plan,
    compile_project_definition,
    plan_migration,
)
from mawflow_seed_kit.catalog import public_catalog
from mawflow_seed_kit.agent_context import portable_agent_files


SAFE_EXISTING_WRITE_REFS = {
    ".gitignore",
    ".maw/project.yaml",
    ".maw/components.yaml",
    ".maw/environments.yaml",
    ".maw/project-lifecycle.yaml",
    ".maw/project-doctor.yaml",
    ".maw/technology.yaml",
    ".maw/template-source.yaml",
    ".maw/modules.yaml",
    ".maw/app-runtime.yaml",
    ".maw/seed.lock",
    ".local/.maw/app-runtime.yaml",
    ".local/.maw/environments.yaml",
    "docs/handbooks/manifest.yaml",
}
VALIDATION_SOURCE_REFS = SAFE_EXISTING_WRITE_REFS | {
    ".maw/template-source.yaml",
    ".maw/upgrade-policy.yaml",
    ".maw/agent-entry.yaml",
    "AI_START_HERE.md",
}

MODULE_TYPE_VALUES = {
    "group",
    "leaf",
    "component",
    "cross-cutting",
    "domain",
    "product-surface",
}
MODULE_TYPE_MIGRATIONS = {
    "feature_group": "group",
    "feature-group": "group",
    "feature": "leaf",
    "business": "domain",
    "product_surface": "product-surface",
    "cross_cutting": "cross-cutting",
}
MODULE_STATUS_VALUES = {"active", "stale", "deprecated"}
MODULE_STATUS_MIGRATIONS = {
    "planned": "active",
    "in_progress": "active",
    "in-progress": "active",
    "completed": "active",
    "enabled": "active",
    "normal": "active",
    "disabled": "stale",
    "archived": "deprecated",
}
MODULE_VERIFIER_VALUES = {"human", "ai", "reviewer"}
MODULE_VERIFIER_MIGRATIONS = {
    "human_ai_review": "reviewer",
    "human-ai-review": "reviewer",
    "human+ai": "reviewer",
    "codex": "ai",
}
PROJECT_REQUIRED_FIELDS = (
    "key",
    "name",
    "repository_mode",
    "default_branch",
    "timezone",
)
PROJECT_REPOSITORY_MODE_MIGRATIONS = {
    "internal": "internal_only",
    "local": "internal_only",
    "external": "external_mapped",
    "mapped": "external_mapped",
}
HANDBOOK_VOLUME_DEFAULTS = {
    "requirements": ["product_owner", "project_manager", "acceptance_owner"],
    "technical": ["technical_owner", "developer", "ai_executor"],
    "task-audit": ["project_owner", "auditor"],
    "quality": ["tester", "acceptance_owner"],
    "release-ops": ["release_owner", "operator"],
    "decisions-risks": ["project_owner", "technical_owner", "auditor"],
}


def _hash(text: str) -> str:
    return f"sha256:{hashlib.sha256(text.encode()).hexdigest()}"


def _atomic_write(path: Path, text: str, mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def _safe_project_path(root: Path, source_ref: str) -> Path:
    relative = Path(source_ref)
    if relative.is_absolute() or ".." in relative.parts or not source_ref:
        raise ValueError("seed_migration_source_ref_invalid")
    resolved_root = root.resolve()
    target = (resolved_root / relative).resolve()
    if resolved_root != target and resolved_root not in target.parents:
        raise ValueError("seed_migration_source_ref_invalid")
    return target


def _mapping_value(node: MappingNode, key: str):
    for key_node, value_node in node.value:
        if isinstance(key_node, ScalarNode) and key_node.value == key:
            return value_node
    return None


def _mapping_key_column(node: MappingNode) -> int:
    if node.value and isinstance(node.value[0][0], ScalarNode):
        return node.value[0][0].start_mark.column
    return node.start_mark.column + 2


def _replace_scalars(text: str, replacements: list[tuple[ScalarNode, str]]) -> str:
    normalized = text
    for node, value in sorted(
        replacements,
        key=lambda item: item[0].start_mark.index,
        reverse=True,
    ):
        normalized = (
            normalized[: node.start_mark.index]
            + value
            + normalized[node.end_mark.index :]
        )
    return normalized


def _insert_mapping_lines(
    text: str,
    inserts: list[tuple[int, list[str]]],
) -> str:
    lines = text.splitlines(keepends=True)
    for line_number, additions in sorted(inserts, reverse=True):
        lines[line_number:line_number] = additions
    normalized = "".join(lines)
    if text and not normalized.endswith("\n"):
        normalized += "\n"
    return normalized


def normalize_top_level_schema_text(text: str) -> str:
    """Upgrade only the top-level schema marker without re-rendering project YAML."""

    try:
        root = yaml.compose(text)
        parsed = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ValueError("seed_migration_existing_yaml_invalid") from exc
    if not isinstance(root, MappingNode) or not isinstance(parsed, dict):
        raise ValueError("seed_migration_existing_yaml_mapping_required")
    schema_node = _mapping_value(root, "schema_version")
    if schema_node is None:
        separator = "" if not text or text.endswith("\n") else "\n"
        return f"{text}{separator}schema_version: 2\n"
    schema_version = parsed.get("schema_version")
    if (
        isinstance(schema_version, int)
        and not isinstance(schema_version, bool)
        and schema_version >= 2
    ):
        return text
    if not isinstance(schema_node, ScalarNode):
        raise ValueError("seed_migration_schema_version_scalar_required")
    return (
        text[: schema_node.start_mark.index] + "2" + text[schema_node.end_mark.index :]
    )


def _render_yaml_scalar(value: Any) -> str:
    rendered = yaml.safe_dump(
        value,
        allow_unicode=True,
        default_flow_style=True,
    ).splitlines()
    if not rendered:
        raise ValueError("seed_migration_scalar_render_failed")
    return rendered[0]


def normalize_seed_lock_text(
    text: str,
    fallback_text: str,
) -> tuple[str, list[dict[str, str]]]:
    """Advance contract-owned lock fields while retaining project-owned identity."""

    try:
        root = yaml.compose(text)
        parsed = yaml.safe_load(text)
        fallback = yaml.safe_load(fallback_text)
    except yaml.YAMLError as exc:
        raise ValueError("seed_migration_seed_lock_invalid_yaml") from exc
    if not isinstance(root, MappingNode) or not isinstance(parsed, dict):
        raise ValueError("seed_migration_seed_lock_mapping_required")
    if not isinstance(fallback, dict):
        raise ValueError("seed_migration_seed_lock_fallback_required")

    replacements: list[tuple[ScalarNode, str]] = []
    inserts: list[tuple[int, list[str]]] = []
    changes: list[dict[str, str]] = []
    top_level_additions: list[str] = []
    for field in (
        "schema",
        "contract_version",
        "contract_fingerprint",
        "seed_version",
    ):
        desired = fallback.get(field)
        if desired in (None, ""):
            continue
        current = parsed.get(field)
        if current == desired:
            continue
        node = _mapping_value(root, field)
        rendered = _render_yaml_scalar(desired)
        if node is None:
            top_level_additions.append(f"{field}: {rendered}\n")
        elif isinstance(node, ScalarNode):
            replacements.append((node, rendered))
        else:
            raise ValueError("seed_migration_seed_lock_scalar_required")
        changes.append(
            {"field": field, "from_value": str(current or ""), "to_value": str(desired)}
        )

    fallback_bom = fallback.get("bom")
    current_bom = parsed.get("bom")
    bom_node = _mapping_value(root, "bom")
    if isinstance(fallback_bom, dict):
        if bom_node is None:
            top_level_additions.append("bom:\n")
            for field in ("kit", "contract"):
                desired = fallback_bom.get(field)
                if desired not in (None, ""):
                    top_level_additions.append(
                        f"  {field}: {_render_yaml_scalar(desired)}\n"
                    )
                    changes.append(
                        {
                            "field": f"bom.{field}",
                            "from_value": "",
                            "to_value": str(desired),
                        }
                    )
        elif isinstance(bom_node, MappingNode) and isinstance(current_bom, dict):
            bom_additions: list[str] = []
            indent = " " * _mapping_key_column(bom_node)
            for field in ("kit", "contract"):
                desired = fallback_bom.get(field)
                if desired in (None, "") or current_bom.get(field) == desired:
                    continue
                node = _mapping_value(bom_node, field)
                rendered = _render_yaml_scalar(desired)
                if node is None:
                    bom_additions.append(f"{indent}{field}: {rendered}\n")
                elif isinstance(node, ScalarNode):
                    replacements.append((node, rendered))
                else:
                    raise ValueError("seed_migration_seed_lock_scalar_required")
                changes.append(
                    {
                        "field": f"bom.{field}",
                        "from_value": str(current_bom.get(field) or ""),
                        "to_value": str(desired),
                    }
                )
            if bom_additions:
                inserts.append((bom_node.end_mark.line, bom_additions))
        else:
            raise ValueError("seed_migration_seed_lock_bom_mapping_required")

    if top_level_additions:
        inserts.append((root.end_mark.line, top_level_additions))
    normalized = _replace_scalars(text, replacements)
    normalized = _insert_mapping_lines(normalized, inserts)
    return normalized, changes


def align_project_methodology_text(
    text: str,
    lifecycle_text: str,
) -> tuple[str, list[dict[str, str]]]:
    """Keep the project classification aligned with its lifecycle authority."""

    try:
        root = yaml.compose(text)
        parsed = yaml.safe_load(text)
        lifecycle = yaml.safe_load(lifecycle_text)
    except yaml.YAMLError as exc:
        raise ValueError("seed_migration_project_methodology_invalid_yaml") from exc
    if not isinstance(root, MappingNode) or not isinstance(parsed, dict):
        raise ValueError("seed_migration_project_mapping_required")
    lifecycle_root = (
        lifecycle.get("project_lifecycle") if isinstance(lifecycle, dict) else None
    )
    methodology = (
        lifecycle_root.get("methodology") if isinstance(lifecycle_root, dict) else None
    )
    desired = (
        str(methodology.get("key") or "").strip()
        if isinstance(methodology, dict)
        else ""
    )
    if not desired:
        return text, []

    project_node = _mapping_value(root, "project")
    project = parsed.get("project")
    if not isinstance(project_node, MappingNode) or not isinstance(project, dict):
        raise ValueError("seed_migration_project_definition_required")
    classification_node = _mapping_value(project_node, "classification")
    classification = project.get("classification")
    if not isinstance(classification_node, MappingNode) or not isinstance(
        classification,
        dict,
    ):
        return text, []
    current = str(classification.get("selected_methodology") or "").strip()
    if current == desired:
        return text, []

    methodology_node = _mapping_value(classification_node, "selected_methodology")
    if methodology_node is None:
        normalized = _insert_mapping_lines(
            text,
            [
                (
                    classification_node.end_mark.line,
                    [
                        f"{' ' * _mapping_key_column(classification_node)}"
                        f"selected_methodology: {_render_yaml_scalar(desired)}\n"
                    ],
                )
            ],
        )
    elif isinstance(methodology_node, ScalarNode):
        normalized = _replace_scalars(
            text,
            [(methodology_node, _render_yaml_scalar(desired))],
        )
    else:
        raise ValueError("seed_migration_project_methodology_scalar_required")
    return normalized, [
        {
            "field": "project.classification.selected_methodology",
            "from_value": current,
            "to_value": desired,
        }
    ]


def normalize_legacy_modules_text(text: str) -> tuple[str, list[dict[str, str]]]:
    """Normalize deterministic legacy module values without discarding their meaning."""

    try:
        root = yaml.compose(text)
        parsed = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ValueError("seed_migration_modules_invalid_yaml") from exc
    if not isinstance(root, MappingNode) or not isinstance(parsed, dict):
        raise ValueError("seed_migration_modules_mapping_required")
    modules_node = _mapping_value(root, "modules")
    modules = parsed.get("modules")
    if modules is None:
        return text, []
    if not isinstance(modules_node, SequenceNode) or not isinstance(modules, list):
        raise ValueError("seed_migration_modules_list_required")
    changes: list[dict[str, str]] = []
    replacements: list[tuple[ScalarNode, str]] = []
    inserts: list[tuple[int, list[str]]] = []
    for index, (node, item) in enumerate(
        zip(modules_node.value, modules, strict=False)
    ):
        if not isinstance(node, MappingNode) or not isinstance(item, dict):
            continue
        key = str(item.get("key") or f"index-{index}")
        field_column = _mapping_key_column(node)
        indent = " " * field_column
        additions: list[str] = []

        verified = item.get("last_verified_at")
        verified_node = _mapping_value(node, "last_verified_at")
        if isinstance(verified, (str, datetime)) and isinstance(verified_node, ScalarNode):
            raw_verified = str(verified)
            if "T" in raw_verified or isinstance(verified, datetime):
                try:
                    parsed_verified = datetime.fromisoformat(raw_verified.replace("Z", "+00:00"))
                except ValueError:
                    pass
                else:
                    date_value = parsed_verified.date().isoformat()
                    replacements.append((verified_node, f"'{date_value}'"))
                    if "legacy_last_verified_at" not in item:
                        additions.append(f"{indent}legacy_last_verified_at: {_render_yaml_scalar(raw_verified)}\n")
                    changes.append({
                        "module_key": key, "field": "last_verified_at",
                        "from_value": raw_verified, "to_value": date_value,
                        "preserved_as": "legacy_last_verified_at",
                        "reason": "保留原始复核时间戳并投影已有日期，不新增验证证据",
                    })

        deterministic_values = (
            (
                "type",
                MODULE_TYPE_VALUES,
                MODULE_TYPE_MIGRATIONS,
                "legacy_type",
                "旧模块分类映射到 Seed v2 模块层级",
            ),
            (
                "status",
                MODULE_STATUS_VALUES,
                MODULE_STATUS_MIGRATIONS,
                "legacy_status",
                "旧实现进度映射到 Seed v2 生命周期",
            ),
            (
                "last_verified_by",
                MODULE_VERIFIER_VALUES,
                MODULE_VERIFIER_MIGRATIONS,
                "legacy_last_verified_by",
                "旧复核方映射到 Seed v2 确认方",
            ),
        )
        for field, allowed, aliases, preserved_as, reason in deterministic_values:
            raw_value = str(item.get(field) or "").strip()
            if not raw_value or raw_value in allowed:
                continue
            mapped = ""
            if field == "status":
                lifecycle = str(item.get("lifecycle") or "").strip()
                if lifecycle in MODULE_STATUS_VALUES:
                    mapped = lifecycle
            mapped = mapped or aliases.get(raw_value, "")
            value_node = _mapping_value(node, field)
            if not mapped or not isinstance(value_node, ScalarNode):
                continue
            replacements.append((value_node, mapped))
            if not str(item.get(preserved_as) or "").strip():
                additions.append(f"{indent}{preserved_as}: {raw_value}\n")
            changes.append(
                {
                    "module_key": key,
                    "field": field,
                    "from_value": raw_value,
                    "to_value": mapped,
                    "preserved_as": preserved_as,
                    "reason": reason,
                }
            )

        missing = [
            field
            for field in ("doc_status", "confidence")
            if not str(item.get(field) or "").strip()
        ]
        if "doc_status" in missing:
            additions.append(f"{indent}doc_status: pending_confirm\n")
            changes.append(
                {
                    "module_key": key,
                    "field": "doc_status",
                    "value": "pending_confirm",
                }
            )
        if "confidence" in missing:
            additions.append(f"{indent}confidence: low\n")
            changes.append({"module_key": key, "field": "confidence", "value": "low"})
        if additions:
            inserts.append((node.end_mark.line, additions))
    normalized = _replace_scalars(text, replacements)
    normalized = _insert_mapping_lines(normalized, inserts)
    normalized = normalize_top_level_schema_text(normalized)
    return normalized, changes


def normalize_legacy_project_text(
    text: str,
    fallback_text: str,
) -> tuple[str, list[dict[str, str]]]:
    """Add only deterministic v2 project requirements while retaining source text."""

    try:
        root = yaml.compose(text)
        parsed = yaml.safe_load(text)
        fallback = yaml.safe_load(fallback_text)
    except yaml.YAMLError as exc:
        raise ValueError("seed_migration_project_invalid_yaml") from exc
    if not isinstance(root, MappingNode) or not isinstance(parsed, dict):
        raise ValueError("seed_migration_project_mapping_required")
    project_node = _mapping_value(root, "project")
    project = parsed.get("project")
    fallback_project = fallback.get("project") if isinstance(fallback, dict) else {}
    if not isinstance(project_node, MappingNode) or not isinstance(project, dict):
        raise ValueError("seed_migration_project_definition_required")
    if not isinstance(fallback_project, dict):
        fallback_project = {}

    changes: list[dict[str, str]] = []
    replacements: list[tuple[ScalarNode, str]] = []
    additions: list[str] = []
    indent = " " * _mapping_key_column(project_node)
    for field in PROJECT_REQUIRED_FIELDS:
        if str(project.get(field) or "").strip():
            continue
        value = str(fallback_project.get(field) or "").strip()
        if not value:
            continue
        additions.append(f"{indent}{field}: {value}\n")
        changes.append({"field": field, "value": value})

    repository_mode = str(project.get("repository_mode") or "").strip()
    mapped_repository_mode = PROJECT_REPOSITORY_MODE_MIGRATIONS.get(
        repository_mode,
        "",
    )
    repository_mode_node = _mapping_value(project_node, "repository_mode")
    if mapped_repository_mode and isinstance(repository_mode_node, ScalarNode):
        replacements.append((repository_mode_node, mapped_repository_mode))
        if not str(project.get("legacy_repository_mode") or "").strip():
            additions.append(f"{indent}legacy_repository_mode: {repository_mode}\n")
        changes.append(
            {
                "field": "repository_mode",
                "from_value": repository_mode,
                "to_value": mapped_repository_mode,
                "preserved_as": "legacy_repository_mode",
            }
        )

    normalized = _replace_scalars(text, replacements)
    if additions:
        normalized = _insert_mapping_lines(
            normalized,
            [(project_node.end_mark.line, additions)],
        )
    normalized = normalize_top_level_schema_text(normalized)
    return normalized, changes


def normalize_legacy_app_runtime_text(
    text: str,
) -> tuple[str, list[dict[str, str]]]:
    """Translate legacy optional runtime apps to an explicit disabled v2 state."""

    try:
        root = yaml.compose(text)
        parsed = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ValueError("seed_migration_app_runtime_invalid_yaml") from exc
    if not isinstance(root, MappingNode) or not isinstance(parsed, dict):
        raise ValueError("seed_migration_app_runtime_mapping_required")
    runtime_node = _mapping_value(root, "app_runtime")
    runtime = parsed.get("app_runtime")
    if not isinstance(runtime_node, MappingNode) or not isinstance(runtime, dict):
        raise ValueError("seed_migration_app_runtime_definition_required")
    apps_node = _mapping_value(runtime_node, "apps")
    apps = runtime.get("apps")
    if not isinstance(apps_node, MappingNode) or not isinstance(apps, dict):
        normalized = normalize_top_level_schema_text(text)
        return normalized, []

    changes: list[dict[str, str]] = []
    replacements: list[tuple[ScalarNode, str]] = []
    inserts: list[tuple[int, list[str]]] = []
    for key_node, app_node in apps_node.value:
        if not isinstance(key_node, ScalarNode) or not isinstance(
            app_node, MappingNode
        ):
            continue
        app_key = str(key_node.value)
        app = apps.get(app_key)
        if not isinstance(app, dict):
            continue
        enabled = app.get("enabled")
        if not isinstance(enabled, str) or enabled.strip().lower() != "optional":
            continue
        enabled_node = _mapping_value(app_node, "enabled")
        if not isinstance(enabled_node, ScalarNode):
            continue
        replacements.append((enabled_node, "false"))
        additions: list[str] = []
        if not str(app.get("legacy_enabled") or "").strip():
            additions.append(
                f"{' ' * _mapping_key_column(app_node)}legacy_enabled: optional\n"
            )
        if additions:
            inserts.append((app_node.end_mark.line, additions))
        changes.append(
            {
                "app_key": app_key,
                "field": "enabled",
                "from_value": "optional",
                "to_value": "false",
                "preserved_as": "legacy_enabled",
                "reason": "可选占位应用在 Seed v2 中显式保持停用",
            }
        )
    normalized = _replace_scalars(text, replacements)
    normalized = _insert_mapping_lines(normalized, inserts)
    normalized = normalize_top_level_schema_text(normalized)
    return normalized, changes


def normalize_legacy_handbook_text(
    text: str,
    fallback_text: str,
) -> tuple[str, list[dict[str, str]]]:
    """Add v2 handbook audience/required fields while retaining volume facts."""

    try:
        root = yaml.compose(text)
        parsed = yaml.safe_load(text)
        fallback = yaml.safe_load(fallback_text)
    except yaml.YAMLError as exc:
        raise ValueError("seed_migration_handbook_invalid_yaml") from exc
    if not isinstance(root, MappingNode) or not isinstance(parsed, dict):
        raise ValueError("seed_migration_handbook_mapping_required")
    system_node = _mapping_value(root, "handbook_system")
    system = parsed.get("handbook_system")
    fallback_system = (
        fallback.get("handbook_system") if isinstance(fallback, dict) else {}
    )
    if not isinstance(system_node, MappingNode) or not isinstance(system, dict):
        raise ValueError("seed_migration_handbook_system_required")
    volumes_node = _mapping_value(system_node, "volumes")
    volumes = system.get("volumes")
    fallback_volumes = (
        fallback_system.get("volumes") if isinstance(fallback_system, dict) else []
    )
    if not isinstance(fallback_volumes, list):
        fallback_volumes = []
    if not isinstance(volumes_node, SequenceNode) or not isinstance(volumes, list):
        raise ValueError("seed_migration_handbook_volumes_required")
    fallback_index = {
        str(item.get("key") or "").replace("_", "-"): item
        for item in fallback_volumes
        if isinstance(item, dict)
    }
    changes: list[dict[str, str]] = []
    inserts: list[tuple[int, list[str]]] = []
    for index, (node, volume) in enumerate(
        zip(volumes_node.value, volumes, strict=False)
    ):
        if not isinstance(node, MappingNode) or not isinstance(volume, dict):
            continue
        key = str(volume.get("key") or f"index-{index}")
        normalized_key = key.replace("_", "-")
        fallback_volume = fallback_index.get(normalized_key, {})
        indent = " " * _mapping_key_column(node)
        additions: list[str] = []
        if not isinstance(volume.get("audience"), list) or not volume.get("audience"):
            audience = (
                fallback_volume.get("audience")
                if isinstance(fallback_volume, dict)
                else None
            )
            if not isinstance(audience, list) or not audience:
                audience = HANDBOOK_VOLUME_DEFAULTS.get(normalized_key) or [
                    str(volume.get("owner") or "project_owner")
                ]
            rendered = yaml.safe_dump(
                audience,
                allow_unicode=True,
                default_flow_style=True,
            ).strip()
            additions.append(f"{indent}audience: {rendered}\n")
            changes.append({"volume_key": key, "field": "audience", "value": rendered})
        if not isinstance(volume.get("required"), bool):
            required = (
                bool(fallback_volume.get("required"))
                if isinstance(fallback_volume, dict)
                and isinstance(fallback_volume.get("required"), bool)
                else normalized_key in HANDBOOK_VOLUME_DEFAULTS
            )
            additions.append(f"{indent}required: {'true' if required else 'false'}\n")
            changes.append(
                {
                    "volume_key": key,
                    "field": "required",
                    "value": "true" if required else "false",
                }
            )
        if additions:
            inserts.append((node.end_mark.line, additions))
    normalized = _insert_mapping_lines(text, inserts)
    normalized = normalize_top_level_schema_text(normalized)
    return normalized, changes


def _projected_migration_validation(
    project_root: Path,
    private_writes: list[dict[str, Any]],
    private_deletes: list[dict[str, Any]],
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="mawflow-seed-safe-preview-") as temporary:
        preview_root = Path(temporary) / "project"
        preview_root.mkdir()
        refs = set(VALIDATION_SOURCE_REFS)
        refs.update(str(item) for item in public_catalog().get("required_files", []))
        refs.update(
            str(item.get("source_ref") or "")
            for item in [*private_writes, *private_deletes]
        )
        for source_ref in sorted(ref for ref in refs if ref):
            current = _safe_project_path(project_root, source_ref)
            if current.is_file() and not current.is_symlink():
                target = _safe_project_path(preview_root, source_ref)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(current.read_text(encoding="utf-8"), encoding="utf-8")
        for item in private_writes:
            target = _safe_project_path(
                preview_root,
                str(item.get("source_ref") or ""),
            )
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(str(item.get("proposed_text") or ""), encoding="utf-8")
        for item in private_deletes:
            _safe_project_path(
                preview_root,
                str(item.get("source_ref") or ""),
            ).unlink(missing_ok=True)
        projection = compile_project_definition(preview_root)
    issues = [
        {
            "code": str(item.get("code") or "seed_migration_validation_failed"),
            "source_ref": str(item.get("source_ref") or ""),
            "message": str(item.get("message") or "Seed Contract v2 校验未通过"),
            "severity": str(item.get("severity") or "error"),
        }
        for item in projection.get("issues", [])
        if isinstance(item, dict)
    ]
    ready = projection.get("status") == "ready"
    return {
        "status": "ready" if ready else "blocked",
        "issue_count": len(issues),
        "issues": issues[:20],
        "confirmation_allowed": ready,
    }


def plan_safe_seed_migration(
    root: Path | str,
    *,
    profile: str = "blank",
    initialization_mode: str = "existing_repository",
) -> tuple[dict[str, Any], dict[str, Any]]:
    project_root = Path(root).expanduser().resolve(strict=True)
    public, private = plan_migration(
        project_root,
        profile=profile,
        initialization_mode=initialization_mode,
    )
    raw_private_writes = private.get("private_writes")
    if not isinstance(raw_private_writes, list):
        raise ValueError("seed_migration_private_plan_required")
    upstream_safety = (
        public.get("migration_safety")
        if isinstance(public.get("migration_safety"), dict)
        else {}
    )
    protected_preserved: list[str] = [
        str(item)
        for item in upstream_safety.get("protected_existing_paths", [])
        if str(item)
    ]
    private_writes: list[dict[str, Any]] = []
    agent_proposals = portable_agent_files(project_root)
    for raw in raw_private_writes:
        if not isinstance(raw, dict):
            continue
        item = dict(raw)
        source_ref = str(item.get("source_ref") or "")
        existed = bool(item.get("existed"))
        if existed and source_ref not in SAFE_EXISTING_WRITE_REFS:
            # Accept only the Kit's deterministic, additive bootstrap proposal.
            if source_ref in agent_proposals and item.get("proposed_text") == agent_proposals[source_ref]:
                private_writes.append(item)
                protected_preserved = [ref for ref in protected_preserved if ref != source_ref]
                continue
            if source_ref not in protected_preserved:
                protected_preserved.append(source_ref)
            continue
        private_writes.append(item)

    # Existing project and component manifests are project-owned source text.
    # Only the mandatory top-level schema marker may change automatically.
    upstream_preserves_project_yaml = bool(
        upstream_safety.get("project_owned_yaml_text_preserved")
    )
    project_field_changes: list[dict[str, str]] = []
    project_methodology_alignments: list[dict[str, str]] = []
    seed_lock_field_changes: list[dict[str, str]] = []
    runtime_field_normalizations: list[dict[str, str]] = []
    handbook_field_additions: list[dict[str, str]] = []
    technology_field_normalizations = [
        dict(item)
        for item in upstream_safety.get("technology_field_normalizations", [])
        if isinstance(item, dict)
    ]
    for item in private_writes:
        source_ref = str(item.get("source_ref") or "")
        if not bool(item.get("existed")):
            continue
        original = str(item.get("original_text") or "")
        if upstream_preserves_project_yaml:
            continue
        if source_ref == ".maw/project.yaml":
            normalized, project_field_changes = normalize_legacy_project_text(
                original,
                str(item.get("proposed_text") or ""),
            )
            item["proposed_text"] = normalized
        elif source_ref == ".maw/components.yaml":
            item["proposed_text"] = normalize_top_level_schema_text(original)
        elif source_ref == ".maw/app-runtime.yaml":
            normalized, runtime_field_normalizations = (
                normalize_legacy_app_runtime_text(original)
            )
            item["proposed_text"] = normalized
        elif source_ref == "docs/handbooks/manifest.yaml":
            normalized, handbook_field_additions = normalize_legacy_handbook_text(
                original,
                str(item.get("proposed_text") or ""),
            )
            item["proposed_text"] = normalized
        elif source_ref in {
            ".maw/environments.yaml",
            ".maw/project-lifecycle.yaml",
        }:
            item["proposed_text"] = original

    lifecycle_path = project_root / ".maw" / "project-lifecycle.yaml"
    lifecycle_text = (
        lifecycle_path.read_text(encoding="utf-8")
        if lifecycle_path.is_file() and not lifecycle_path.is_symlink()
        else ""
    )
    for item in private_writes:
        source_ref = str(item.get("source_ref") or "")
        if not bool(item.get("existed")):
            continue
        if source_ref == ".maw/project.yaml" and lifecycle_text:
            normalized, project_methodology_alignments = align_project_methodology_text(
                str(item.get("proposed_text") or ""),
                lifecycle_text,
            )
            item["proposed_text"] = normalized
        elif source_ref == ".maw/seed.lock":
            normalized, seed_lock_field_changes = normalize_seed_lock_text(
                str(item.get("original_text") or ""),
                str(item.get("proposed_text") or ""),
            )
            item["proposed_text"] = normalized

    modules_path = project_root / ".maw" / "modules.yaml"
    module_field_changes: list[dict[str, str]] = []
    if modules_path.is_file() and not modules_path.is_symlink():
        original = modules_path.read_text(encoding="utf-8")
        proposed, module_field_changes = normalize_legacy_modules_text(original)
        current = next(
            (
                item
                for item in private_writes
                if str(item.get("source_ref") or "") == ".maw/modules.yaml"
            ),
            None,
        )
        if proposed != original:
            replacement = {
                "source_ref": ".maw/modules.yaml",
                "original_text": original,
                "proposed_text": proposed,
                "existed": True,
            }
            if current is None:
                private_writes.append(replacement)
            else:
                current.update(replacement)
        elif current is not None:
            # A no-op normalization must also discard an older upstream rewrite.
            current["proposed_text"] = original

    runtime_path = project_root / ".maw" / "app-runtime.yaml"
    if runtime_path.is_file() and not runtime_path.is_symlink():
        original = runtime_path.read_text(encoding="utf-8")
        proposed, runtime_field_normalizations = normalize_legacy_app_runtime_text(
            original
        )
        current = next(
            (
                item
                for item in private_writes
                if str(item.get("source_ref") or "") == ".maw/app-runtime.yaml"
            ),
            None,
        )
        if proposed != original:
            replacement = {
                "source_ref": ".maw/app-runtime.yaml",
                "original_text": original,
                "proposed_text": proposed,
                "existed": True,
            }
            if current is None:
                private_writes.append(replacement)
            else:
                current.update(replacement)
            protected_preserved = [
                item for item in protected_preserved if item != ".maw/app-runtime.yaml"
            ]

    handbook_path = project_root / "docs" / "handbooks" / "manifest.yaml"
    if handbook_path.is_file() and not handbook_path.is_symlink():
        original = handbook_path.read_text(encoding="utf-8")
        proposed, handbook_field_additions = normalize_legacy_handbook_text(
            original,
            "",
        )
        if proposed != original:
            replacement = {
                "source_ref": "docs/handbooks/manifest.yaml",
                "original_text": original,
                "proposed_text": proposed,
                "existed": True,
            }
            current = next(
                (
                    item
                    for item in private_writes
                    if str(item.get("source_ref") or "")
                    == "docs/handbooks/manifest.yaml"
                ),
                None,
            )
            if current is None:
                private_writes.append(replacement)
            else:
                current.update(replacement)
            protected_preserved = [
                item
                for item in protected_preserved
                if item != "docs/handbooks/manifest.yaml"
            ]

    public_writes: list[dict[str, Any]] = []
    for item in sorted(
        private_writes, key=lambda value: str(value.get("source_ref") or "")
    ):
        source_ref = str(item.get("source_ref") or "")
        original = str(item.get("original_text") or "")
        proposed = str(item.get("proposed_text") or "")
        if original == proposed:
            continue
        public_writes.append(
            {
                "source_ref": source_ref,
                "action": "update" if bool(item.get("existed")) else "create",
                "expected_hash": _hash(original),
                "proposed_hash": _hash(proposed),
                "diff_lines": list(
                    difflib.unified_diff(
                        original.splitlines(),
                        proposed.splitlines(),
                        fromfile=source_ref,
                        tofile=source_ref,
                        lineterm="",
                    )
                )[:200],
            }
        )
    private_writes = [
        item
        for item in private_writes
        if str(item.get("original_text") or "") != str(item.get("proposed_text") or "")
    ]
    private_deletes = [
        dict(item)
        for item in private.get("private_deletes", [])
        if isinstance(item, dict)
    ]
    if not private_writes and not private_deletes:
        raise ValueError("seed_migration_no_changes")
    module_field_additions = [item for item in module_field_changes if "value" in item]
    module_field_normalizations = [
        item for item in module_field_changes if "to_value" in item
    ]
    validation = _projected_migration_validation(
        project_root,
        private_writes,
        private_deletes,
    )
    safety = {
        "incremental_existing_files_only": True,
        "business_readme_preserved": bool(
            upstream_safety.get("business_readme_preserved")
        )
        or "README.md" in protected_preserved
        or (project_root / "README.md").is_file(),
        "protected_existing_paths": sorted(protected_preserved),
        "project_field_changes": project_field_changes,
        "project_methodology_alignments": project_methodology_alignments,
        "seed_lock_field_changes": seed_lock_field_changes,
        "seed_lock_project_identity_preserved": True,
        "module_field_additions": module_field_additions,
        "module_field_normalizations": module_field_normalizations,
        "runtime_field_normalizations": runtime_field_normalizations,
        "handbook_field_additions": handbook_field_additions,
        "technology_field_normalizations": technology_field_normalizations,
        "module_facts_preserved": True,
        "project_owned_yaml_text_preserved": True,
    }
    public = {
        **public,
        "writes": public_writes,
        "migration_safety": safety,
        "validation": validation,
    }
    private = {
        **private,
        "writes": public_writes,
        "private_writes": private_writes,
        "private_deletes": private_deletes,
        "migration_safety": safety,
        "validation": validation,
    }
    return public, private


def apply_safe_seed_migration_plan(
    root: Path | str,
    plan: dict[str, Any],
    confirmation: str,
    *,
    backup_root: Path | str,
) -> dict[str, Any]:
    validation = plan.get("validation")
    if not isinstance(validation, dict) or validation.get("status") != "ready":
        raise ValueError("seed_migration_preview_not_ready")
    try:
        result = apply_migration_plan(root, plan, confirmation, backup_root=backup_root)
    except ValueError as exc:
        if str(exc) != "seed_migration_validation_failed":
            raise
        projection = compile_project_definition(Path(root).expanduser().resolve())
        details = ",".join(
            ":".join(
                str(item.get(key) or "") for key in ("code", "source_ref", "message")
            ).rstrip(":")
            for item in projection.get("issues", [])[:8]
            if isinstance(item, dict)
        )
        raise ValueError(
            f"seed_migration_validation_failed:{details or 'invalid'}"
        ) from exc
    private_rollback_manifest = [
        {
            "source_ref": str(item.get("source_ref") or ""),
            "operation": "write",
            "existed": bool(item.get("existed")),
            "proposed_text": str(item.get("proposed_text") or ""),
        }
        for item in plan.get("private_writes", [])
        if isinstance(item, dict)
    ] + [
        {
            "source_ref": str(item.get("source_ref") or ""),
            "operation": "delete",
            "existed": True,
            "proposed_text": "",
        }
        for item in plan.get("private_deletes", [])
        if isinstance(item, dict)
    ]
    return {
        **result,
        "migration_safety": dict(plan.get("migration_safety") or {}),
        "rollback_available": bool(private_rollback_manifest),
        "private_rollback_manifest": private_rollback_manifest,
    }


def rollback_safe_seed_migration(
    root: Path | str,
    applied: dict[str, Any],
    confirmation: str,
    *,
    backup_root: Path | str,
) -> dict[str, Any]:
    """Restore a safe migration only while every migrated file still matches."""

    project_root = Path(root).expanduser().resolve(strict=True)
    plan_key = str(applied.get("plan_key") or "")
    if confirmation != f"ROLLBACK {plan_key[-8:].upper()}":
        raise ValueError("seed_migration_rollback_confirmation_required")
    manifest = applied.get("private_rollback_manifest")
    if not isinstance(manifest, list) or not manifest:
        raise ValueError("seed_migration_rollback_manifest_missing")
    backup_dir = Path(backup_root).expanduser().resolve() / plan_key
    operations: list[tuple[dict[str, Any], Path, Path]] = []
    for raw in manifest:
        if not isinstance(raw, dict):
            raise ValueError("seed_migration_rollback_manifest_invalid")
        item = dict(raw)
        source_ref = str(item.get("source_ref") or "")
        target = _safe_project_path(project_root, source_ref)
        backup = _safe_project_path(backup_dir, source_ref)
        operation = str(item.get("operation") or "")
        proposed_text = str(item.get("proposed_text") or "")
        if operation == "write":
            if target.is_symlink() or not target.is_file():
                raise ValueError("seed_migration_rollback_config_conflict")
            if _hash(target.read_text(encoding="utf-8")) != _hash(proposed_text):
                raise ValueError("seed_migration_rollback_config_conflict")
            if bool(item.get("existed")) and not backup.is_file():
                raise ValueError("seed_migration_rollback_backup_missing")
        elif operation == "delete":
            if target.exists() or target.is_symlink():
                raise ValueError("seed_migration_rollback_config_conflict")
            if not backup.is_file():
                raise ValueError("seed_migration_rollback_backup_missing")
        else:
            raise ValueError("seed_migration_rollback_manifest_invalid")
        operations.append((item, target, backup))

    try:
        for item, target, backup in operations:
            operation = str(item.get("operation") or "")
            if operation == "write" and not bool(item.get("existed")):
                target.unlink(missing_ok=True)
                continue
            mode = (
                0o600
                if str(item.get("source_ref") or "").startswith(".local/")
                else 0o644
            )
            _atomic_write(target, backup.read_text(encoding="utf-8"), mode)
    except Exception:
        for item, target, _backup in operations:
            if str(item.get("operation") or "") == "write":
                _atomic_write(
                    target,
                    str(item.get("proposed_text") or ""),
                    0o600
                    if str(item.get("source_ref") or "").startswith(".local/")
                    else 0o644,
                )
            else:
                target.unlink(missing_ok=True)
        raise
    return {
        "schema": "mawflow.seed_migration_result.v2",
        "status": "rolled_back",
        "plan_key": plan_key,
        "rolled_back_at": datetime.now(timezone.utc).isoformat(),
    }


__all__ = [
    "align_project_methodology_text",
    "apply_safe_seed_migration_plan",
    "normalize_legacy_app_runtime_text",
    "normalize_legacy_handbook_text",
    "normalize_legacy_modules_text",
    "normalize_legacy_project_text",
    "normalize_seed_lock_text",
    "normalize_top_level_schema_text",
    "plan_safe_seed_migration",
    "rollback_safe_seed_migration",
]
