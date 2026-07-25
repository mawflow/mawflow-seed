from __future__ import annotations

from datetime import datetime, timedelta, timezone
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import tempfile
from typing import Any

import yaml
from yaml.nodes import MappingNode, ScalarNode, SequenceNode

from .catalog import CONTRACT_VERSION, SEED_VERSION, contract_fingerprint
from .compiler import compile_project_definition
from .template import materialize_project


def _hash(text: str) -> str:
    return f"sha256:{hashlib.sha256(text.encode()).hexdigest()}"


def _atomic_write(path: Path, text: str, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
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


def _read_mapping(path: Path) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        return {}
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    return dict(loaded) if isinstance(loaded, dict) else {}


def _render(payload: dict[str, Any]) -> str:
    return yaml.safe_dump(payload, allow_unicode=True, sort_keys=False)


def _deep_merge(base: object, overlay: object) -> object:
    if isinstance(base, dict) and isinstance(overlay, dict):
        result = dict(base)
        for key, value in overlay.items():
            result[key] = _deep_merge(result.get(key), value) if key in result else value
        return result
    return overlay


def _normalized_gitignore(root: Path, fallback_text: str) -> str:
    path = root / ".gitignore"
    text = path.read_text(encoding="utf-8") if path.is_file() and not path.is_symlink() else fallback_text
    lines = text.splitlines()
    if ".local/" not in lines:
        lines.append(".local/")
    return "\n".join(lines).rstrip() + "\n"


def _normalized_project(root: Path, project_key: str, name: str) -> str:
    path = root / ".maw/project.yaml"
    original_text = path.read_text(encoding="utf-8") if path.is_file() and not path.is_symlink() else ""
    if original_text:
        return _normalized_project_contract_text(
            original_text, project_key=project_key, name=name
        )
    payload = _read_mapping(path)
    project = payload.get("project") if isinstance(payload.get("project"), dict) else {}
    legacy = project.get("project") if isinstance(project.get("project"), dict) else {}
    key = str(project.get("key") or project.get("project_key") or legacy.get("project_key") or project_key).strip()
    normalized = {key_: value for key_, value in project.items() if key_ not in {"project", "project_key"}}
    normalized["key"] = key
    normalized.setdefault("name", name or key)
    normalized.setdefault("description", "")
    normalized.setdefault("owner", "")
    normalized.setdefault("type", "business_project")
    classification = normalized.get("classification") if isinstance(normalized.get("classification"), dict) else {}
    classification.setdefault("delivery_mode", "existing_evolution")
    classification.setdefault("requirement_maturity", "partial")
    classification.setdefault("source_state", "existing_repository")
    classification.setdefault("onboarding_status", "draft")
    classification.setdefault("selected_methodology", "solo_lean_loop")
    normalized["classification"] = classification
    objective = normalized.get("objective") if isinstance(normalized.get("objective"), dict) else {}
    objective.setdefault("value_statement", "")
    objective.setdefault("primary_users", [])
    objective.setdefault("success_metrics", [])
    normalized["objective"] = objective
    normalized.setdefault("repository_mode", "internal_only")
    normalized.setdefault("default_branch", "main")
    normalized.setdefault("timezone", "Asia/Shanghai")
    comments = [line for line in original_text.splitlines() if line.lstrip().startswith("#")]
    result = dict(payload)
    result["schema_version"] = 2
    result["project"] = normalized
    credentials = result.get("credentials") if isinstance(result.get("credentials"), dict) else {}
    credentials.setdefault("schema_version", 1)
    credentials.setdefault("requirements", [])
    result["credentials"] = credentials
    rendered = _render(result)
    return ("\n".join(comments) + "\n" if comments else "") + rendered


def _normalized_components(root: Path, fallback_text: str) -> str:
    path = root / ".maw/components.yaml"
    if path.is_file() and not path.is_symlink():
        return _normalized_top_level_schema(path.read_text(encoding="utf-8"))
    payload = _read_mapping(root / ".maw/components.yaml")
    components = payload.get("components")
    if not isinstance(components, list):
        return fallback_text
    result = []
    for raw in components:
        if not isinstance(raw, dict):
            continue
        item = dict(raw)
        item["key"] = str(item.get("key") or item.get("app_key") or "").strip()
        item.setdefault("app_key", item["key"])
        item.setdefault("enabled", True)
        result.append(item)
    return _render({"schema_version": 2, "components": result})


def _mapping_value(node: MappingNode, key: str):
    for key_node, value_node in node.value:
        if isinstance(key_node, ScalarNode) and key_node.value == key:
            return value_node
    return None


def _normalized_top_level_schema(text: str) -> str:
    """Upgrade the contract marker without re-rendering project-owned YAML."""

    try:
        root = yaml.compose(text)
        payload = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ValueError("seed_migration_existing_yaml_invalid") from exc
    if not isinstance(root, MappingNode) or not isinstance(payload, dict):
        raise ValueError("seed_migration_existing_yaml_mapping_required")
    schema_node = _mapping_value(root, "schema_version")
    if schema_node is None:
        separator = "" if not text or text.endswith("\n") else "\n"
        return f"{text}{separator}schema_version: 2\n"
    if payload.get("schema_version") == 2:
        return text
    if not isinstance(schema_node, ScalarNode):
        raise ValueError("seed_migration_schema_version_scalar_required")
    return (
        text[: schema_node.start_mark.index]
        + "2"
        + text[schema_node.end_mark.index :]
    )


def _append_missing_mapping_fields(
    text: str, path: tuple[str, ...], fields: dict[str, Any]
) -> str:
    try:
        root = yaml.compose(text)
        payload = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ValueError("seed_migration_existing_yaml_invalid") from exc
    if not isinstance(root, MappingNode) or not isinstance(payload, dict):
        raise ValueError("seed_migration_existing_yaml_mapping_required")
    node: MappingNode = root
    current: Any = payload
    for key in path:
        child = _mapping_value(node, key)
        if not isinstance(child, MappingNode) or not isinstance(current, dict):
            raise ValueError("seed_migration_existing_yaml_mapping_required")
        node = child
        current = current.get(key)
    if not isinstance(current, dict):
        raise ValueError("seed_migration_existing_yaml_mapping_required")
    missing = {key: value for key, value in fields.items() if key not in current}
    if not missing:
        return text
    column = (
        node.value[0][0].start_mark.column
        if node.value and isinstance(node.value[0][0], ScalarNode)
        else node.start_mark.column
    )
    rendered = yaml.safe_dump(
        missing, allow_unicode=True, sort_keys=False
    ).splitlines(keepends=True)
    insertion = [" " * column + line if line.strip() else line for line in rendered]
    lines = text.splitlines(keepends=True)
    lines[node.end_mark.line : node.end_mark.line] = insertion
    return "".join(lines)


def _replace_mapping_scalar(
    text: str, path: tuple[str, ...], key: str, value: str
) -> str:
    root = yaml.compose(text)
    payload = yaml.safe_load(text)
    if not isinstance(root, MappingNode) or not isinstance(payload, dict):
        raise ValueError("seed_migration_existing_yaml_mapping_required")
    node: MappingNode = root
    current: Any = payload
    for part in path:
        child = _mapping_value(node, part)
        if not isinstance(child, MappingNode) or not isinstance(current, dict):
            raise ValueError("seed_migration_existing_yaml_mapping_required")
        node = child
        current = current.get(part)
    scalar = _mapping_value(node, key)
    if scalar is None or not isinstance(current, dict) or current.get(key) == value:
        return text
    if not isinstance(scalar, ScalarNode):
        raise ValueError("seed_migration_existing_yaml_scalar_required")
    rendered = json.dumps(value, ensure_ascii=False)
    return (
        text[: scalar.start_mark.index]
        + rendered
        + text[scalar.end_mark.index :]
    )


def _normalized_project_contract_text(
    text: str, *, project_key: str, name: str
) -> str:
    normalized = _normalized_top_level_schema(text)
    payload = yaml.safe_load(normalized)
    project = payload.get("project") if isinstance(payload, dict) else None
    if not isinstance(project, dict):
        raise ValueError("seed_migration_existing_yaml_mapping_required")
    legacy = project.get("project") if isinstance(project.get("project"), dict) else {}
    key = str(
        project.get("key")
        or project.get("project_key")
        or legacy.get("project_key")
        or project_key
    ).strip()
    display_name = str(project.get("name") or legacy.get("name") or name or key)
    normalized = _append_missing_mapping_fields(
        normalized,
        ("project",),
        {
            "key": key,
            "name": display_name,
            "description": "",
            "owner": "",
            "type": "business_project",
            "classification": {
                "delivery_mode": "existing_evolution",
                "requirement_maturity": "partial",
                "source_state": "existing_repository",
                "onboarding_status": "draft",
                "selected_methodology": "solo_lean_loop",
            },
            "objective": {
                "value_statement": "",
                "primary_users": [],
                "success_metrics": [],
            },
            "repository_mode": "internal_only",
            "default_branch": "main",
            "timezone": "Asia/Shanghai",
        },
    )
    normalized = _append_missing_mapping_fields(
        normalized,
        ("project", "classification"),
        {
            "delivery_mode": "existing_evolution",
            "requirement_maturity": "partial",
            "source_state": "existing_repository",
            "onboarding_status": "draft",
            "selected_methodology": "solo_lean_loop",
        },
    )
    normalized = _append_missing_mapping_fields(
        normalized,
        ("project", "objective"),
        {
            "value_statement": "",
            "primary_users": [],
            "success_metrics": [],
        },
    )
    return _append_missing_mapping_fields(
        normalized,
        (),
        {
            "credentials": {
                "schema_version": 1,
                "requirements": [],
            }
        },
    )


def _normalized_modules(root: Path, fallback_text: str) -> tuple[str, list[dict[str, str]]]:
    """Add only missing v2 evidence fields and preserve project module facts/text."""

    path = root / ".maw/modules.yaml"
    if not path.is_file() or path.is_symlink():
        return fallback_text, []
    text = _normalized_top_level_schema(path.read_text(encoding="utf-8"))
    try:
        document = yaml.compose(text)
        payload = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ValueError("seed_migration_modules_invalid_yaml") from exc
    if not isinstance(document, MappingNode) or not isinstance(payload, dict):
        raise ValueError("seed_migration_modules_mapping_required")
    modules_node = _mapping_value(document, "modules")
    modules = payload.get("modules")
    if modules is None:
        return text, []
    if not isinstance(modules_node, SequenceNode) or not isinstance(modules, list):
        raise ValueError("seed_migration_modules_list_required")
    lines = text.splitlines(keepends=True)
    inserts: list[tuple[int, list[str]]] = []
    additions: list[dict[str, str]] = []
    for index, (node, item) in enumerate(
        zip(modules_node.value, modules, strict=False)
    ):
        if not isinstance(node, MappingNode) or not isinstance(item, dict):
            continue
        missing = [
            field
            for field in ("doc_status", "confidence")
            if not str(item.get(field) or "").strip()
        ]
        if not missing:
            continue
        module_key = str(item.get("key") or f"index-{index}")
        column = (
            node.value[0][0].start_mark.column
            if node.value and isinstance(node.value[0][0], ScalarNode)
            else node.start_mark.column + 2
        )
        indent = " " * column
        inserted: list[str] = []
        if "doc_status" in missing:
            inserted.append(f"{indent}doc_status: pending_confirm\n")
            additions.append(
                {
                    "module_key": module_key,
                    "field": "doc_status",
                    "value": "pending_confirm",
                }
            )
        if "confidence" in missing:
            inserted.append(f"{indent}confidence: low\n")
            additions.append(
                {
                    "module_key": module_key,
                    "field": "confidence",
                    "value": "low",
                }
            )
        inserts.append((node.end_mark.line, inserted))
    for line_number, inserted in reversed(inserts):
        lines[line_number:line_number] = inserted
    normalized = "".join(lines)
    if text and not normalized.endswith("\n"):
        normalized += "\n"
    return normalized, additions


def _normalized_environments(root: Path, fallback_text: str) -> str:
    path = root / ".maw/environments.yaml"
    if path.is_file() and not path.is_symlink():
        normalized = _normalized_top_level_schema(path.read_text(encoding="utf-8"))
        payload = yaml.safe_load(normalized)
        environments = payload.get("environments") if isinstance(payload, dict) else None
        if not isinstance(environments, dict):
            raise ValueError("seed_migration_existing_yaml_mapping_required")
        aliases = {
            "dev": "local",
            "test": "local",
            "online": "staging",
            "pro": "production",
            "prod": "production",
        }
        profile_aliases = {
            "local": "local",
            "dev": "dev",
            "test": "local",
            "staging": "dev",
            "online": "dev",
            "pro": "pro",
            "prod": "pro",
            "production": "pro",
        }
        roles = {
            "local": ("local_development", "development", False),
            "staging": (
                "production_like_validation",
                "compiled_package",
                True,
            ),
            "production": ("production", "production_release", True),
        }
        for key, environment in environments.items():
            if not isinstance(environment, dict):
                continue
            canonical = aliases.get(str(key), str(key))
            role, mode, build_required = roles.get(
                canonical, ("compatibility", "compatibility", False)
            )
            current_profile = str(environment.get("profile") or canonical)
            canonical_profile = profile_aliases.get(
                current_profile,
                "local"
                if canonical == "local"
                else "dev"
                if canonical == "staging"
                else "pro",
            )
            normalized = _replace_mapping_scalar(
                normalized,
                ("environments", str(key)),
                "profile",
                canonical_profile,
            )
            normalized = _append_missing_mapping_fields(
                normalized,
                ("environments", str(key)),
                {
                    "role": role,
                    "runtime_mode": "inherit",
                    "deployment": {
                        "mode": mode,
                        "build_artifact_required": build_required,
                    },
                },
            )
            normalized = _append_missing_mapping_fields(
                normalized,
                ("environments", str(key), "deployment"),
                {
                    "mode": mode,
                    "build_artifact_required": build_required,
                },
            )
        return normalized
    existing = _read_mapping(root / ".maw/environments.yaml")
    fallback = yaml.safe_load(fallback_text)
    merged = _deep_merge(fallback, existing)
    if not isinstance(merged, dict):
        return fallback_text
    environments = merged.get("environments")
    if isinstance(environments, dict):
        aliases = {"dev": "local", "test": "local", "online": "staging", "pro": "production", "prod": "production"}
        profile_aliases = {
            "local": "local",
            "dev": "dev",
            "test": "local",
            "staging": "dev",
            "online": "dev",
            "pro": "pro",
            "prod": "pro",
            "production": "pro",
        }
        roles = {
            "local": ("local_development", "development", False),
            "staging": ("production_like_validation", "compiled_package", True),
            "production": ("production", "production_release", True),
        }
        for key, environment in environments.items():
            if not isinstance(environment, dict):
                continue
            canonical = aliases.get(str(key), str(key))
            role, mode, build_required = roles.get(canonical, ("compatibility", "compatibility", False))
            environment.setdefault("role", role)
            environment["profile"] = profile_aliases.get(
                str(environment.get("profile") or canonical),
                "local" if canonical == "local" else "dev" if canonical == "staging" else "pro",
            )
            environment.setdefault("runtime_mode", "inherit")
            deployment = environment.get("deployment") if isinstance(environment.get("deployment"), dict) else {}
            deployment.setdefault("mode", mode)
            deployment.setdefault("build_artifact_required", build_required)
            environment["deployment"] = deployment
    return _render(merged)


def _normalized_lifecycle(root: Path, fallback_text: str) -> str:
    path = root / ".maw/project-lifecycle.yaml"
    if path.is_file() and not path.is_symlink():
        return path.read_text(encoding="utf-8")
    existing = _read_mapping(root / ".maw/project-lifecycle.yaml")
    fallback = yaml.safe_load(fallback_text)
    merged = _deep_merge(fallback, existing)
    return _render(merged if isinstance(merged, dict) else fallback)


def _normalized_technology(root: Path, fallback_text: str) -> str:
    path = root / ".maw/technology.yaml"
    if path.is_file() and not path.is_symlink():
        return path.read_text(encoding="utf-8")
    existing = _read_mapping(root / ".maw/technology.yaml")
    fallback = yaml.safe_load(fallback_text)
    merged = _deep_merge(fallback, existing)
    return _render(merged if isinstance(merged, dict) else fallback)


def plan_migration(root: Path | str, *, profile: str = "web-api") -> tuple[dict[str, Any], dict[str, Any]]:
    project_root = Path(root).expanduser().resolve(strict=True)
    existing_project = _read_mapping(project_root / ".maw/project.yaml").get("project", {})
    legacy = existing_project.get("project", {}) if isinstance(existing_project, dict) else {}
    project_key = str(
        (existing_project.get("key") or existing_project.get("project_key") or legacy.get("project_key"))
        if isinstance(existing_project, dict)
        else ""
    ).strip() or project_root.name.lower().replace("_", "-")
    name = str(existing_project.get("name") or legacy.get("name") or project_key) if isinstance(existing_project, dict) else project_key
    with tempfile.TemporaryDirectory(prefix="mawflow-seed-migration-") as temporary:
        template_root = Path(temporary) / "project"
        materialize_project(template_root, project_key=project_key, name=name, profile=profile)
        desired: dict[str, str] = {}
        for path in template_root.rglob("*"):
            if path.is_file():
                source_ref = path.relative_to(template_root).as_posix()
                desired[source_ref] = path.read_text(encoding="utf-8")

    desired[".maw/project.yaml"] = _normalized_project(project_root, project_key, name)
    desired[".maw/components.yaml"] = _normalized_components(project_root, desired[".maw/components.yaml"])
    desired[".maw/modules.yaml"], module_field_additions = _normalized_modules(
        project_root, desired[".maw/modules.yaml"]
    )
    desired[".maw/environments.yaml"] = _normalized_environments(project_root, desired[".maw/environments.yaml"])
    desired[".maw/project-lifecycle.yaml"] = _normalized_lifecycle(project_root, desired[".maw/project-lifecycle.yaml"])
    desired[".maw/technology.yaml"] = _normalized_technology(project_root, desired[".maw/technology.yaml"])
    for source_ref in [".maw/app-runtime.yaml", ".maw/project-doctor.yaml", ".maw/template-source.yaml", ".maw/upgrade-policy.yaml", ".maw/agent-entry.yaml", "AI_START_HERE.md"]:
        path = project_root / source_ref
        if path.is_file() and not path.is_symlink():
            desired[source_ref] = path.read_text(encoding="utf-8")
    desired[".gitignore"] = _normalized_gitignore(project_root, desired[".gitignore"])
    desired[".maw/seed.lock"] = _render({
        "schema": "mawflow.seed_lock.v2",
        "contract_version": CONTRACT_VERSION,
        "contract_fingerprint": contract_fingerprint(),
        "seed_version": SEED_VERSION,
        "profile": profile,
        "source": {"kind": "migration", "from": "0.2.x"},
        "bom": {"kit": f"mawflow-seed-kit=={SEED_VERSION}", "contract": "seed-contract-v2"},
    })
    legacy_local = {
        ".maw/app-runtime.local.yaml": ".local/.maw/app-runtime.yaml",
        ".maw/environments.local.yaml": ".local/.maw/environments.yaml",
    }
    for old_ref, new_ref in legacy_local.items():
        old_path = project_root / old_ref
        if old_path.is_file() and not old_path.is_symlink():
            desired[new_ref] = old_path.read_text(encoding="utf-8")

    mutable_existing_refs = {
        ".gitignore",
        ".maw/project.yaml",
        ".maw/components.yaml",
        ".maw/environments.yaml",
        ".maw/project-lifecycle.yaml",
        ".maw/technology.yaml",
        ".maw/modules.yaml",
        ".maw/seed.lock",
        ".local/.maw/app-runtime.yaml",
        ".local/.maw/environments.yaml",
    }
    protected_existing_paths: list[str] = []
    for source_ref in list(desired):
        path = project_root / source_ref
        if (
            path.is_file()
            and not path.is_symlink()
            and source_ref not in mutable_existing_refs
        ):
            desired[source_ref] = path.read_text(encoding="utf-8")
            protected_existing_paths.append(source_ref)

    writes: list[dict[str, Any]] = []
    private_writes: list[dict[str, Any]] = []
    for source_ref, proposed in sorted(desired.items()):
        path = project_root / source_ref
        existed = path.is_file() and not path.is_symlink()
        original = path.read_text(encoding="utf-8") if existed else ""
        if original == proposed:
            continue
        writes.append({"source_ref": source_ref, "action": "update" if existed else "create", "expected_hash": _hash(original), "proposed_hash": _hash(proposed), "diff_lines": list(difflib.unified_diff(original.splitlines(), proposed.splitlines(), fromfile=source_ref, tofile=source_ref, lineterm=""))[:200]})
        private_writes.append({"source_ref": source_ref, "original_text": original, "proposed_text": proposed, "existed": existed})
    deletes = [old_ref for old_ref in legacy_local if (project_root / old_ref).is_file()]
    if not writes and not deletes:
        raise ValueError("seed_migration_no_changes")
    plan_key = f"seedmigration-{secrets.token_hex(12)}"
    now = datetime.now(timezone.utc)
    public = {
        "schema": "mawflow.seed_migration_plan.v2",
        "status": "previewed",
        "plan_key": plan_key,
        "from_contract_version": int(_read_mapping(project_root / ".maw/seed.lock").get("contract_version") or 0),
        "to_contract_version": CONTRACT_VERSION,
        "profile": profile,
        "writes": writes,
        "deletes": deletes,
        "confirmation_required": f"MIGRATE {plan_key[-8:].upper()}",
        "created_at": now.isoformat(),
        "expires_at": (now + timedelta(minutes=30)).isoformat(),
        "migration_safety": {
            "incremental_existing_files_only": True,
            "business_readme_preserved": (
                project_root / "README.md"
            ).is_file(),
            "protected_existing_paths": sorted(protected_existing_paths),
            "module_field_additions": module_field_additions,
            "module_facts_preserved": True,
            "project_owned_yaml_text_preserved": True,
        },
    }
    return public, {**public, "private_writes": private_writes, "private_deletes": [{"source_ref": ref, "original_text": (project_root / ref).read_text(encoding="utf-8")} for ref in deletes]}


def apply_migration_plan(root: Path | str, plan: dict[str, Any], confirmation: str, *, backup_root: Path | str) -> dict[str, Any]:
    project_root = Path(root).expanduser().resolve(strict=True)
    if confirmation != plan.get("confirmation_required"):
        raise ValueError("seed_migration_confirmation_required")
    expires = datetime.fromisoformat(str(plan.get("expires_at") or ""))
    if datetime.now(timezone.utc) >= expires:
        raise ValueError("seed_migration_plan_expired")
    writes = plan.get("private_writes")
    deletes = plan.get("private_deletes", [])
    if not isinstance(writes, list):
        raise ValueError("seed_migration_private_plan_required")
    backup_dir = Path(backup_root).expanduser().resolve() / str(plan["plan_key"])
    backup_dir.mkdir(parents=True, exist_ok=False)
    try:
        for item in [*writes, *deletes]:
            path = project_root / str(item["source_ref"])
            existed = path.is_file() and not path.is_symlink()
            current = path.read_text(encoding="utf-8") if existed else ""
            if current != item["original_text"]:
                raise ValueError("seed_migration_config_conflict")
            if existed:
                _atomic_write(backup_dir / str(item["source_ref"]), current)
        _atomic_write(
            backup_dir / ".migration-manifest.yaml",
            _render(
                {
                    "schema": "mawflow.seed_migration_backup.v2",
                    "plan_key": plan["plan_key"],
                    "writes": [
                        {
                            "source_ref": item["source_ref"],
                            "existed": bool(item["existed"]),
                            "original_hash": _hash(str(item["original_text"])),
                            "proposed_hash": _hash(str(item["proposed_text"])),
                        }
                        for item in writes
                    ],
                    "deletes": [
                        {
                            "source_ref": item["source_ref"],
                            "original_hash": _hash(str(item["original_text"])),
                        }
                        for item in deletes
                    ],
                }
            ),
        )
        for item in writes:
            _atomic_write(project_root / str(item["source_ref"]), str(item["proposed_text"]), 0o644)
        for item in deletes:
            (project_root / str(item["source_ref"])).unlink()
        projection = compile_project_definition(project_root)
        if projection["status"] != "ready":
            issue_codes = ",".join(
                ":".join(
                    str(item.get(key) or "")
                    for key in ("code", "source_ref", "message")
                ).rstrip(":")
                for item in projection.get("issues", [])[:5]
                if isinstance(item, dict)
            )
            raise ValueError(f"seed_migration_validation_failed:{issue_codes or 'invalid'}")
    except Exception:
        for item in writes:
            path = project_root / str(item["source_ref"])
            if item["existed"]:
                _atomic_write(path, str(item["original_text"]), 0o644)
            else:
                path.unlink(missing_ok=True)
        for item in deletes:
            _atomic_write(project_root / str(item["source_ref"]), str(item["original_text"]), 0o600)
        raise
    return {
        "schema": "mawflow.seed_migration_result.v2",
        "status": "applied",
        "plan_key": plan["plan_key"],
        "projection": projection,
        "backup_ref": f"private-backup:{plan['plan_key']}",
        "rollback_confirmation": f"ROLLBACK {str(plan['plan_key'])[-8:].upper()}",
        "applied_at": datetime.now(timezone.utc).isoformat(),
    }


def rollback_migration(
    root: Path | str,
    *,
    plan_key: str,
    confirmation: str,
    backup_root: Path | str,
) -> dict[str, Any]:
    if not re.fullmatch(r"seedmigration-[0-9a-f]{24}", plan_key):
        raise ValueError("seed_migration_plan_key_invalid")
    if confirmation != f"ROLLBACK {plan_key[-8:].upper()}":
        raise ValueError("seed_migration_rollback_confirmation_required")
    project_root = Path(root).expanduser().resolve(strict=True)
    backup_dir = Path(backup_root).expanduser().resolve(strict=True) / plan_key
    manifest = _read_mapping(backup_dir / ".migration-manifest.yaml")
    if manifest.get("schema") != "mawflow.seed_migration_backup.v2" or manifest.get("plan_key") != plan_key:
        raise ValueError("seed_migration_backup_invalid")
    writes = manifest.get("writes")
    deletes = manifest.get("deletes")
    if not isinstance(writes, list) or not isinstance(deletes, list):
        raise ValueError("seed_migration_backup_invalid")
    for item in writes:
        source_ref = str(item.get("source_ref") or "")
        path = project_root / source_ref
        current = path.read_text(encoding="utf-8") if path.is_file() and not path.is_symlink() else ""
        if _hash(current) != item.get("proposed_hash"):
            raise ValueError("seed_migration_rollback_conflict")
    for item in writes:
        source_ref = str(item["source_ref"])
        path = project_root / source_ref
        if item.get("existed"):
            backup_path = backup_dir / source_ref
            if not backup_path.is_file() or backup_path.is_symlink():
                raise ValueError("seed_migration_backup_invalid")
            _atomic_write(path, backup_path.read_text(encoding="utf-8"), 0o644)
        else:
            path.unlink(missing_ok=True)
    for item in deletes:
        source_ref = str(item["source_ref"])
        backup_path = backup_dir / source_ref
        if not backup_path.is_file() or backup_path.is_symlink():
            raise ValueError("seed_migration_backup_invalid")
        _atomic_write(project_root / source_ref, backup_path.read_text(encoding="utf-8"), 0o600)
    projection = compile_project_definition(project_root)
    return {
        "schema": "mawflow.seed_migration_result.v2",
        "status": "rolled_back",
        "plan_key": plan_key,
        "projection": projection,
        "rolled_back_at": datetime.now(timezone.utc).isoformat(),
    }


__all__ = ["apply_migration_plan", "plan_migration", "rollback_migration"]
