from __future__ import annotations

from datetime import datetime, timedelta, timezone
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import stat
import subprocess
import tempfile
from typing import Any
from urllib.parse import urlsplit

import yaml
from yaml.nodes import MappingNode, Node, ScalarNode, SequenceNode

from .catalog import SEED_VERSION, catalog, contract_fingerprint
from .compiler import compile_project_definition


KEY_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{0,159}$")
GIT_REF_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,239}$")
REF_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,239}$")
COMPONENT_SOURCE_REF_PATTERN = re.compile(r"^mawsource://component/[a-z0-9][a-z0-9._-]{0,159}$")
GIT_ACCESS_PROFILE_REF_PATTERN = re.compile(r"^mawgit://[A-Za-z0-9][A-Za-z0-9._/-]{0,239}$")
RESOURCE_REF_PATTERN = re.compile(r"^mawresource://server/[A-Za-z0-9][A-Za-z0-9._/-]{0,239}$")
ACCESS_PROFILE_REF_PATTERN = re.compile(r"^(?:mawaccess|mawresource)://[A-Za-z0-9][A-Za-z0-9._/-]{0,239}$")
SCP_REPOSITORY_PATTERN = re.compile(r"^(?:[A-Za-z0-9._-]+@)?([A-Za-z0-9.-]+):([^?#\s]+)$")
SENSITIVE_TEXT = re.compile(r"(?i)(?:(?<![A-Za-z0-9_])sk-[A-Za-z0-9_-]{12,}|(?:password|passwd|secret|token|api[_-]?key)\s*[:=]\s*\S+)")
MAX_FIELD_LENGTH = 2000
RISK_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash(text: str) -> str:
    return f"sha256:{hashlib.sha256(text.encode()).hexdigest()}"


def _atomic_write(path: Path, text: str, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(name, mode)
        os.replace(name, path)
    except Exception:
        try:
            os.unlink(name)
        except OSError:
            pass
        raise


def _mapping_entries(node: MappingNode) -> dict[str, tuple[ScalarNode, Node]]:
    return {str(key.value): (key, value) for key, value in node.value if isinstance(key, ScalarNode)}


def _mapping_field_indent(node: MappingNode, fallback: int) -> int:
    if node.value and isinstance(node.value[0][0], ScalarNode):
        return node.value[0][0].start_mark.column
    return fallback


def _mapping_value(node: MappingNode, key: str) -> Node | None:
    entry = _mapping_entries(node).get(key)
    return entry[1] if entry else None


def _scalar_text(value: object) -> str:
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if value is True:
        return "true"
    if value is False:
        return "false"
    if value is None:
        return "null"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, list):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    raise ValueError("seed_change_value_type_forbidden")


def _node_replacement(text: str, node: Node, value: object) -> str:
    replacement = _scalar_text(value)
    if isinstance(node, SequenceNode) and not node.flow_style:
        # PyYAML starts an indentless block sequence at the dash. Replacing the
        # sequence with a flow scalar must indent it beneath the mapping key.
        replacement = f"  {replacement}"
    original = text[node.start_mark.index : node.end_mark.index]
    trailing_indent = re.search(r"\n[ \t]*\Z", original)
    if trailing_indent:
        replacement += trailing_indent.group(0)
    return replacement


def _parse(text: str) -> tuple[dict[str, Any], MappingNode]:
    try:
        payload, node = yaml.safe_load(text), yaml.compose(text)
    except yaml.YAMLError as exc:
        raise ValueError("seed_change_invalid_yaml") from exc
    if not isinstance(payload, dict) or not isinstance(node, MappingNode):
        raise ValueError("seed_change_yaml_mapping_required")
    return dict(payload), node


def _node_insertion_index(text: str, node: Node) -> int:
    """Insert before indentation owned by the following sibling, if present."""

    index = node.end_mark.index
    if index >= len(text):
        return index
    line_start = text.rfind("\n", 0, index) + 1
    return line_start if not text[line_start:index].strip() else index


def _read(root: Path, source_ref: str, skeleton: str) -> tuple[str, int, bool]:
    root = root.resolve(strict=True)
    path = root / source_ref
    if path.is_symlink():
        raise ValueError("seed_change_symlink_forbidden")
    if not path.exists():
        path.parent.resolve(strict=False).relative_to(root)
        return skeleton, 0o600, False
    resolved = path.resolve(strict=True)
    resolved.relative_to(root)
    if not resolved.is_file() or resolved.stat().st_size > 2 * 1024 * 1024:
        raise ValueError("seed_change_source_unavailable")
    return resolved.read_text(encoding="utf-8", errors="strict"), stat.S_IMODE(resolved.stat().st_mode), True


def _require_ignored(root: Path, source_ref: str) -> None:
    try:
        result = subprocess.run(["git", "-C", str(root), "check-ignore", "--quiet", source_ref], timeout=3, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ValueError("seed_change_local_ignore_unverified") from exc
    if result.returncode != 0:
        raise ValueError("seed_change_local_not_ignored")


def _validate_path(value: object, *, empty: bool) -> str:
    text = str(value or "").strip().replace("\\", "/")
    if not text and empty:
        return ""
    if not text or text.startswith("/") or re.match(r"^[A-Za-z]:/", text) or ".." in Path(text).parts:
        raise ValueError("seed_change_relative_path_required")
    if any(part in {".git", ".local"} for part in Path(text).parts):
        raise ValueError("seed_change_path_forbidden")
    return text


def _absolute_path_valid(value: str) -> bool:
    if not value or "\x00" in value or "\n" in value or "\r" in value:
        return False
    normalized = value.replace("\\", "/")
    if ".." in Path(normalized).parts:
        return False
    return normalized.startswith("/") or bool(re.match(r"^[A-Za-z]:/[^/].*", normalized)) or normalized.startswith("//")


def _repository_url_valid(value: str) -> bool:
    scp = SCP_REPOSITORY_PATTERN.fullmatch(value)
    if scp:
        return bool(scp.group(1) and scp.group(2).strip("/")) and ".." not in Path(scp.group(2)).parts
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        return False
    if parsed.scheme not in {"http", "https", "ssh"} or not parsed.hostname or parsed.password or parsed.query or parsed.fragment:
        return False
    if parsed.scheme in {"http", "https"} and parsed.username:
        return False
    if port is not None and not 1 <= port <= 65535:
        return False
    return bool(parsed.path.strip("/"))


def _validate(field: str, value: object, rule: str) -> object:
    if isinstance(value, str) and (len(value) > MAX_FIELD_LENGTH or SENSITIVE_TEXT.search(value)):
        raise ValueError("seed_change_sensitive_or_long_text_forbidden")
    if rule == "bool":
        if type(value) is not bool:
            raise ValueError("seed_change_boolean_required")
        return value
    if rule == "bool_or_optional":
        if value not in {True, False, "optional"}:
            raise ValueError("seed_change_boolean_or_optional_required")
        return value
    if rule in {"port", "port_or_empty"}:
        if value in {"", None} and rule.endswith("_or_empty"):
            return ""
        try:
            port = int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("seed_change_invalid_port") from exc
        if not 1 <= port <= 65535:
            raise ValueError("seed_change_invalid_port")
        return port
    if rule == "integer":
        try:
            return int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("seed_change_integer_required") from exc
    if rule == "key_list":
        if not isinstance(value, list) or len(value) > 40:
            raise ValueError("seed_change_key_list_required")
        result = []
        for raw in value:
            item = str(raw or "").strip()
            if not KEY_PATTERN.fullmatch(item):
                raise ValueError("seed_change_invalid_key")
            if item not in result:
                result.append(item)
        return result
    if rule in {"string_list", "text_list"}:
        if not isinstance(value, list) or len(value) > 40:
            raise ValueError("seed_change_text_list_required")
        result = []
        for raw in value:
            item = str(raw or "").strip()
            if not item or len(item) > MAX_FIELD_LENGTH or SENSITIVE_TEXT.search(item):
                raise ValueError("seed_change_sensitive_or_long_text_forbidden")
            if item not in result:
                result.append(item)
        return result
    if rule == "path_list":
        if not isinstance(value, list) or len(value) > 40:
            raise ValueError("seed_change_path_list_required")
        result = []
        for raw in value:
            item = _validate_path(raw, empty=False)
            if item not in result:
                result.append(item)
        return result
    text = str(value or "").strip()
    if rule in {"path", "path_or_empty"}:
        return _validate_path(text, empty=rule.endswith("_or_empty"))
    if rule in {"key", "key_or_empty"}:
        if (text or rule == "key") and not KEY_PATTERN.fullmatch(text):
            raise ValueError("seed_change_invalid_key")
        return text
    if rule in {"git_ref", "git_ref_or_empty"}:
        if not text and rule.endswith("_or_empty"):
            return ""
        if not GIT_REF_PATTERN.fullmatch(text) or ".." in text or "//" in text or text.endswith(("/", ".")):
            raise ValueError("seed_change_invalid_git_ref")
        return text
    if rule in {"component_source_ref", "component_source_ref_or_empty"}:
        if not text and rule.endswith("_or_empty"):
            return ""
        if not COMPONENT_SOURCE_REF_PATTERN.fullmatch(text):
            raise ValueError("seed_change_invalid_component_source_ref")
        return text
    if rule == "git_access_profile_ref_or_empty":
        if not text:
            return ""
        if not GIT_ACCESS_PROFILE_REF_PATTERN.fullmatch(text):
            raise ValueError("seed_change_invalid_git_access_profile_ref")
        return text
    if rule == "resource_ref":
        if not RESOURCE_REF_PATTERN.fullmatch(text):
            raise ValueError("seed_change_invalid_resource_ref")
        return text
    if rule == "access_profile_ref_or_empty":
        if not text:
            return ""
        if not ACCESS_PROFILE_REF_PATTERN.fullmatch(text):
            raise ValueError("seed_change_invalid_access_profile_ref")
        return text
    if rule == "absolute_path":
        if not _absolute_path_valid(text):
            raise ValueError("seed_change_absolute_path_required")
        return text
    if rule == "repository_url_or_empty":
        if not text:
            return ""
        if not _repository_url_valid(text):
            raise ValueError("seed_change_invalid_repository_url")
        return text
    if rule in {"date", "date_or_empty"}:
        if not text and rule.endswith("_or_empty"):
            return ""
        try:
            datetime.fromisoformat(text[:10])
        except ValueError as exc:
            raise ValueError("seed_change_invalid_date") from exc
        return text[:10]
    if rule in {"url", "url_or_empty", "url_or_path_or_empty"}:
        if not text and rule.endswith("_or_empty"):
            return ""
        if rule == "url_or_path_or_empty" and text.startswith("/"):
            if "?" in text or "#" in text or ".." in Path(text).parts:
                raise ValueError("seed_change_invalid_url_path")
            return text
        try:
            parsed = urlsplit(text)
            port = parsed.port
        except ValueError as exc:
            raise ValueError("seed_change_invalid_url") from exc
        if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("seed_change_invalid_url")
        if port is not None and not 1 <= port <= 65535:
            raise ValueError("seed_change_invalid_url")
        return text
    if rule == "url_path_or_empty":
        if not text:
            return ""
        if not text.startswith("/") or "?" in text or "#" in text or ".." in Path(text).parts:
            raise ValueError("seed_change_invalid_url_path")
        return text
    if rule in {"secret_requirement_ref_or_empty", "credential_binding_ref_or_empty"}:
        if not text:
            return ""
        if rule.startswith("credential_"):
            if not text.startswith(("mawsec://", "mawlocal://", "mawproxy://")):
                raise ValueError("seed_change_invalid_credential_binding")
            suffix = text.split("://", 1)[1]
        else:
            suffix = text
        if ".." in Path(suffix).parts or not REF_PATTERN.fullmatch(suffix):
            raise ValueError("seed_change_invalid_reference")
        return text
    if rule == "ref_or_empty":
        if not text:
            return ""
        if ".." in Path(text).parts or not REF_PATTERN.fullmatch(text):
            raise ValueError("seed_change_invalid_reference")
        return text
    if rule == "enum":
        raise ValueError("seed_change_catalog_enum_missing")
    if not text and not rule.endswith("_or_empty"):
        raise ValueError(f"seed_change_{field}_required")
    return text


def _validate_field(field: str, value: object, definition: dict[str, Any], scope: str) -> object:
    if scope not in definition.get("scope", []):
        raise ValueError("seed_change_field_scope_forbidden")
    rule = str(definition["type"])
    if rule == "enum":
        text = str(value or "").strip()
        if text not in definition.get("options", []):
            raise ValueError(f"seed_change_invalid_{field}")
        return text
    return _validate(field, value, rule)


def _apply_fields(text: str, mapping: MappingNode, fields: dict[str, object], indent: int) -> str:
    edits: list[tuple[int, int, str]] = []
    missing: list[tuple[str, object]] = []
    entries = _mapping_entries(mapping)
    for field, value in fields.items():
        entry = entries.get(field)
        if entry:
            edits.append((
                entry[1].start_mark.index,
                entry[1].end_mark.index,
                _node_replacement(text, entry[1], value),
            ))
        else:
            missing.append((field, value))
    if missing:
        insertion = "".join(f"{' ' * indent}{field}: {_scalar_text(value)}\n" for field, value in missing)
        insertion_index = _node_insertion_index(text, mapping)
        edits.append((insertion_index, insertion_index, insertion))
    for start, end, replacement in sorted(edits, reverse=True):
        text = text[:start] + replacement + text[end:]
    return text


def _apply_paths(text: str, mapping: MappingNode, fields: dict[str, object], indent: int) -> str:
    edits: list[tuple[int, int, str]] = []
    missing_by_mapping: dict[int, tuple[MappingNode, int, list[tuple[str, object]]]] = {}

    def collect(target: MappingNode, field: str, value: object, field_indent: int) -> None:
        entry = _mapping_entries(target).get(field)
        if entry:
            edits.append((
                entry[1].start_mark.index,
                entry[1].end_mark.index,
                _node_replacement(text, entry[1], value),
            ))
            return
        bucket = missing_by_mapping.setdefault(id(target), (target, field_indent, []))
        bucket[2].append((field, value))

    for field, value in fields.items():
        target = mapping
        parts = field.split(".")
        for part in parts[:-1]:
            child = _mapping_value(target, part)
            if not isinstance(child, MappingNode):
                raise ValueError("seed_change_nested_mapping_missing")
            target = child
        collect(target, parts[-1], value, indent + 2 * (len(parts) - 1))
    for target, field_indent, missing in missing_by_mapping.values():
        insertion = "".join(f"{' ' * field_indent}{field}: {_scalar_text(value)}\n" for field, value in missing)
        insertion_index = _node_insertion_index(text, target)
        edits.append((insertion_index, insertion_index, insertion))
    for start, end, replacement in sorted(edits, reverse=True):
        text = text[:start] + replacement + text[end:]
    return text


def _sequence_item(sequence: SequenceNode, key: str) -> MappingNode | None:
    for item in sequence.value:
        identity = _mapping_value(item, "key") if isinstance(item, MappingNode) else None
        if isinstance(identity, ScalarNode) and str(identity.value) == key:
            return item
    return None


def _append_sequence(
    text: str,
    sequence: SequenceNode,
    key: str,
    fields: dict[str, object],
    *,
    base_indent: int,
) -> str:
    if any("." in field for field in fields):
        payload: dict[str, Any] = {"key": key}
        for field, value in fields.items():
            current = payload
            parts = field.split(".")
            for part in parts[:-1]:
                current = current.setdefault(part, {})
            current[parts[-1]] = value
        lines = [" " * base_indent + line for line in yaml.safe_dump([payload], allow_unicode=True, sort_keys=False).rstrip().splitlines()]
    else:
        lines = [f"{' ' * base_indent}- key: {_scalar_text(key)}"]
        lines.extend(f"{' ' * (base_indent + 2)}{field}: {_scalar_text(value)}" for field, value in fields.items())
    insertion = "\n".join(lines) + "\n"
    if sequence.flow_style:
        replacement = "\n" + insertion.rstrip("\n")
        return text[:sequence.start_mark.index] + replacement + text[sequence.end_mark.index:]
    insertion_index = _node_insertion_index(text, sequence)
    return text[:insertion_index] + insertion + text[insertion_index:]


def _remove_node(text: str, node: Node) -> str:
    start, end = node.start_mark.index, node.end_mark.index
    line_start = text.rfind("\n", 0, start) + 1
    line_end = text.find("\n", end)
    return text[:line_start] + text[(len(text) if line_end < 0 else line_end + 1):]


def _remove_sequence_item(text: str, sequence: SequenceNode, item: Node) -> str:
    if len(sequence.value) != 1:
        start = text.rfind("\n", 0, item.start_mark.index) + 1
        position = sequence.value.index(item)
        if position + 1 < len(sequence.value):
            next_item = sequence.value[position + 1]
            after = text.rfind("\n", 0, next_item.start_mark.index) + 1
        else:
            line_end = text.find("\n", item.end_mark.index)
            after = len(text) if line_end < 0 else line_end + 1
        return text[:start] + text[after:]
    line_start = text.rfind("\n", 0, item.start_mark.index) + 1
    line_end = text.find("\n", item.end_mark.index)
    after = len(text) if line_end < 0 else line_end + 1
    parent_line_end = line_start - 1
    parent_line_start = text.rfind("\n", 0, parent_line_end) + 1
    colon = text.rfind(":", parent_line_start, parent_line_end)
    if colon >= parent_line_start:
        return text[: colon + 1] + " []\n" + text[after:]
    return _remove_node(text, item)


def _remove_mapping_entry(text: str, mapping: MappingNode, key: str) -> str:
    entry = _mapping_entries(mapping).get(key)
    if not entry:
        raise ValueError("seed_change_item_missing")
    key_node, value_node = entry
    line_start = text.rfind("\n", 0, key_node.start_mark.index) + 1
    following = sorted(
        candidate_key.start_mark.index
        for candidate_key, _ in mapping.value
        if candidate_key.start_mark.index > key_node.start_mark.index
    )
    if following:
        after = text.rfind("\n", 0, following[0]) + 1
    else:
        line_end = text.find("\n", value_node.end_mark.index)
        after = len(text) if line_end < 0 else line_end + 1
    if len(mapping.value) == 1:
        parent_line_end = line_start - 1
        parent_line_start = text.rfind("\n", 0, parent_line_end) + 1
        colon = text.rfind(":", parent_line_start, parent_line_end)
        if colon >= parent_line_start:
            return text[: colon + 1] + " {}\n" + text[after:]
    return text[:line_start] + text[after:]


def _append_mapping(text: str, mapping: MappingNode, key: str, fields: dict[str, object], indent: int) -> str:
    nested: dict[str, Any] = {}
    for field, value in fields.items():
        current = nested
        parts = field.split(".")
        for part in parts[:-1]:
            current = current.setdefault(part, {})
        current[parts[-1]] = value
    rendered = yaml.safe_dump({key: nested}, allow_unicode=True, sort_keys=False).rstrip().splitlines()
    insertion = "\n".join(" " * indent + line for line in rendered) + "\n"
    if mapping.flow_style:
        replacement = "\n" + insertion.rstrip("\n")
        return text[:mapping.start_mark.index] + replacement + text[mapping.end_mark.index:]
    insertion_index = _node_insertion_index(text, mapping)
    return text[:insertion_index] + insertion + text[insertion_index:]


def _operation_map() -> dict[str, dict[str, Any]]:
    return {str(item["key"]): item for item in catalog()["operations"]}


def _skeleton(target: str) -> str:
    if target == "runtime_app":
        return "app_runtime:\n  apps: {}\n"
    if target == "environment":
        return "environments: {}\n"
    if target == "component_source_binding":
        return "component_sources: {}\n"
    target_definition = catalog()["targets"].get(target, {})
    root = str(target_definition.get("root") or target or "configuration")
    return f"{root}: {{}}\n"


def _validate_proposed_projection(root: Path, texts: dict[str, str]) -> None:
    with tempfile.TemporaryDirectory(prefix="mawflow-seed-change-preview-") as temporary:
        preview_root = Path(temporary)
        source_refs = set(catalog()["required_files"])
        source_refs.update(
            str(target["local_source"])
            for target in catalog()["targets"].values()
            if target.get("local_source")
        )
        for source_ref in source_refs:
            source = root / source_ref
            if source.is_file() and not source.is_symlink():
                destination = preview_root / source_ref
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
        for source_ref, proposed in texts.items():
            destination = preview_root / source_ref
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(proposed, encoding="utf-8")
        projection = compile_project_definition(preview_root)
        if projection["status"] != "ready":
            codes = ",".join(str(item.get("code") or "invalid") for item in projection["issues"][:5])
            raise ValueError(f"seed_change_proposed_projection_invalid:{codes}")


def _apply_operation(root: Path, texts: dict[str, str], operation: dict[str, Any]) -> tuple[str, str, str, list[dict[str, object]]]:
    op_key = str(operation.get("op") or "")
    op_def = _operation_map().get(op_key)
    if not op_def:
        raise ValueError("seed_change_operation_forbidden")
    target_key = str(op_def["target"])
    target = catalog()["targets"][target_key]
    scope = str(operation.get("scope") or "shared")
    source_ref = str(target.get("local_source") if scope == "local" else target["source"])
    if scope == "local":
        if not target.get("local_source"):
            raise ValueError("seed_change_local_scope_forbidden")
        _require_ignored(root, source_ref)
    key = str(operation.get("key") or "").strip()
    if target["kind"] != "mapping" and target["kind"] != "mapping_paths" and not KEY_PATTERN.fullmatch(key):
        raise ValueError("seed_change_invalid_item_key")
    raw_values = operation.get("values")
    if not isinstance(raw_values, dict):
        raw_values = {}
    field_defs = target.get("fields", {})
    if target_key == "lifecycle":
        field_defs = _lifecycle_fields(root)
    if set(raw_values) - set(field_defs):
        raise ValueError("seed_change_field_forbidden")
    values = {field: _validate_field(field, value, field_defs[field], scope) for field, value in raw_values.items()}
    if not values and not op_key.endswith("remove"):
        raise ValueError("seed_change_values_required")
    original = texts.get(source_ref)
    if original is None:
        original, _, _ = _read(root, source_ref, _skeleton(target_key))
    payload, document = _parse(original)
    root_node = _mapping_value(document, str(target["root"]))
    kind = str(target["kind"])
    mode = "create" if op_key.endswith(".add") else "update"
    if op_key.endswith(".remove"):
        mode = "remove"
    if kind in {"mapping", "mapping_paths"}:
        if not isinstance(root_node, MappingNode):
            raise ValueError("seed_change_target_missing")
        proposed = _apply_paths(original, root_node, values, 2) if kind == "mapping_paths" else _apply_fields(original, root_node, values, 2)
    elif kind == "sequence":
        collection = (
            _mapping_value(root_node, str(target.get("collection")))
            if target.get("collection") and isinstance(root_node, MappingNode)
            else root_node
        )
        if not isinstance(collection, SequenceNode):
            raise ValueError("seed_change_target_missing")
        base_indent = (
            collection.start_mark.column
            if not collection.flow_style
            else (4 if target.get("collection") else 2)
        )
        item = _sequence_item(collection, key)
        if mode == "create":
            if item:
                raise ValueError("seed_change_item_exists")
            proposed = _append_sequence(original, collection, key, values, base_indent=base_indent)
        elif mode == "remove":
            if not item:
                raise ValueError("seed_change_item_missing")
            if target_key == "component":
                _assert_component_unreferenced(root, texts, key)
            proposed = _remove_sequence_item(original, collection, item)
        else:
            if not item:
                raise ValueError("seed_change_item_missing")
            proposed = (_apply_paths if any("." in field for field in values) else _apply_fields)(
                original,
                item,
                values,
                _mapping_field_indent(item, base_indent + 2),
            )
    else:
        if not isinstance(root_node, MappingNode):
            raise ValueError("seed_change_target_missing")
        collection = _mapping_value(root_node, str(target.get("collection"))) if target.get("collection") else root_node
        if not isinstance(collection, MappingNode):
            raise ValueError("seed_change_target_missing")
        item = _mapping_value(collection, key)
        values = {field: value for field, value in values.items() if field != "app_key"}
        if mode == "remove":
            if not isinstance(item, MappingNode):
                raise ValueError("seed_change_item_missing")
            proposed = _remove_mapping_entry(original, collection, key)
        elif not isinstance(item, MappingNode):
            proposed = _append_mapping(original, collection, key, values, 4 if target.get("collection") else 2)
            mode = "create"
        else:
            proposed = _apply_paths(original, item, values, 6 if target.get("collection") else 4)
    _parse(proposed)
    texts[source_ref] = proposed
    changes = [{"field": field, "after": value} for field, value in values.items()]
    return source_ref, target_key, mode, changes


def _lifecycle_fields(root: Path) -> dict[str, dict[str, Any]]:
    loaded = yaml.safe_load((root / ".maw/project-lifecycle.yaml").read_text(encoding="utf-8"))
    lifecycle = loaded.get("project_lifecycle") if isinstance(loaded, dict) else None
    configuration = lifecycle.get("configuration") if isinstance(lifecycle, dict) else None
    metadata = configuration.get("field_metadata") if isinstance(configuration, dict) else None
    result: dict[str, dict[str, Any]] = {}
    for item in metadata if isinstance(metadata, list) else []:
        if not isinstance(item, dict) or item.get("editable") is not True or item.get("sensitive") is True:
            continue
        key = str(item.get("key") or "").removeprefix("project_lifecycle.")
        kind = str(item.get("type") or "string")
        mapped = {"string": "text", "boolean": "bool", "integer": "integer", "enum": "enum"}.get(kind)
        if not key or not mapped:
            continue
        result[key] = {"type": mapped, "options": item.get("options", []), "scope": ["shared"], "risk": item.get("risk", "high")}
    if not result:
        raise ValueError("seed_change_lifecycle_metadata_missing")
    return result


def _assert_component_unreferenced(root: Path, texts: dict[str, str], key: str) -> None:
    modules_text = texts.get(".maw/modules.yaml") or (root / ".maw/modules.yaml").read_text(encoding="utf-8")
    runtime_text = texts.get(".maw/app-runtime.yaml") or (root / ".maw/app-runtime.yaml").read_text(encoding="utf-8")
    modules = yaml.safe_load(modules_text).get("modules", [])
    apps = yaml.safe_load(runtime_text).get("app_runtime", {}).get("apps", {}) or {}
    if any(key in item.get("component_refs", []) for item in modules if isinstance(item, dict)):
        raise ValueError("seed_change_component_referenced_by_module")
    if any(isinstance(item, dict) and item.get("component_ref") == key for item in apps.values()):
        raise ValueError("seed_change_component_referenced_by_runtime")


def _plan_change_set(
    root: Path | str,
    payload: dict[str, Any],
    *,
    allow_invalid_base: bool = False,
) -> tuple[dict[str, Any], dict[str, Any]]:
    project_root = Path(root).expanduser().resolve(strict=True)
    projection = compile_project_definition(project_root)
    if not projection["editable"] and not allow_invalid_base:
        raise ValueError("seed_change_project_not_editable")
    if payload.get("schema") != "mawflow.seed_change_set.v2":
        raise ValueError("seed_change_schema_invalid")
    if payload.get("base_projection_fingerprint") != projection["fingerprint"]:
        raise ValueError("seed_change_projection_conflict")
    if payload.get("base_contract_fingerprint") not in {None, "", contract_fingerprint()}:
        raise ValueError("seed_change_contract_conflict")
    operations = payload.get("operations")
    if not isinstance(operations, list) or not 1 <= len(operations) <= 40:
        raise ValueError("seed_change_operations_required")
    texts: dict[str, str] = {}
    summaries: list[dict[str, Any]] = []
    risks: list[str] = []
    for operation in operations:
        if not isinstance(operation, dict):
            raise ValueError("seed_change_operation_invalid")
        source_ref, target, mode, changes = _apply_operation(project_root, texts, operation)
        op_def = _operation_map()[str(operation["op"])]
        risk = str(op_def.get("risk") or "high")
        risks.append(risk)
        summaries.append({"op": operation["op"], "target": target, "mode": mode, "key": operation.get("key", ""), "scope": operation.get("scope", "shared"), "source_ref": source_ref, "risk": risk, "changes": changes})
    _validate_proposed_projection(project_root, texts)
    writes = []
    private_writes = []
    for source_ref, proposed in texts.items():
        original, mode, existed = _read(project_root, source_ref, _skeleton(next((s["target"] for s in summaries if s["source_ref"] == source_ref), "")))
        if proposed == original:
            continue
        diff = list(difflib.unified_diff(original.splitlines(), proposed.splitlines(), fromfile=source_ref, tofile=source_ref, lineterm=""))[:300]
        writes.append({"source_ref": source_ref, "expected_hash": _hash(original), "proposed_hash": _hash(proposed), "diff_lines": diff, "existed": existed})
        private_writes.append({"source_ref": source_ref, "expected_hash": _hash(original), "original_text": original, "proposed_text": proposed, "mode": mode, "existed": existed})
    if not writes:
        raise ValueError("seed_change_no_changes")
    plan_key = f"seedchange-{secrets.token_hex(12)}"
    now = datetime.now(timezone.utc)
    public = {
        "schema": "mawflow.seed_change_plan.v2",
        "status": "previewed",
        "plan_key": plan_key,
        "risk": max(risks, key=lambda item: RISK_ORDER[item]),
        "operations": summaries,
        "writes": writes,
        "base_projection_fingerprint": projection["fingerprint"],
        "base_contract_fingerprint": contract_fingerprint(),
        "reason": str(payload.get("reason") or "")[:500],
        "confirmation_required": f"APPLY {plan_key[-8:].upper()}",
        "created_at": now.isoformat(),
        "expires_at": (now + timedelta(minutes=30)).isoformat(),
        "trust_boundary": {"arbitrary_paths_writable": False, "credential_values_accepted": False, "full_configs_returned": False},
    }
    return public, {**public, "private_writes": private_writes}


def plan_change_set(
    root: Path | str, payload: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    return _plan_change_set(root, payload)


def _technology_repair_operations(
    projection: dict[str, Any],
) -> list[dict[str, Any]]:
    configs = projection.get("configs")
    technology_config = (
        configs.get(".maw/technology.yaml")
        if isinstance(configs, dict)
        else None
    )
    technology = (
        technology_config.get("technology")
        if isinstance(technology_config, dict)
        else None
    )
    if not isinstance(technology, dict):
        return []
    targets = catalog()["targets"]
    operations: list[dict[str, Any]] = []

    language_roles = set(
        targets["technology_language"]["fields"]["role"].get("options", [])
    )
    for item in technology.get("languages", []):
        if not isinstance(item, dict):
            continue
        key = str(item.get("key") or "").strip()
        role = str(item.get("role") or "").strip()
        if key and role and role not in language_roles and role == "build_tool":
            operations.append(
                {
                    "op": "technology.language.update",
                    "key": key,
                    "scope": "shared",
                    "values": {"role": "tooling"},
                }
            )

    for item in technology.get("frameworks", []):
        if not isinstance(item, dict):
            continue
        key = str(item.get("key") or "").strip()
        if key and not str(item.get("name") or "").strip():
            operations.append(
                {
                    "op": "technology.framework.update",
                    "key": key,
                    "scope": "shared",
                    "values": {"name": key},
                }
            )

    service_fields = targets["technology_service"]["fields"]
    service_types = set(service_fields["type"].get("options", []))
    provisions = set(service_fields["provision"].get("options", []))
    environment = technology.get("development_environment")
    standard = str(
        environment.get("standard")
        if isinstance(environment, dict)
        else ""
    ).strip()
    default_provision = {
        "docker_compose": "docker",
        "devcontainer": "docker",
        "host_runtime": "host",
        "external": "external",
    }.get(standard, "user_selectable")
    for item in technology.get("services", []):
        if not isinstance(item, dict):
            continue
        key = str(item.get("key") or "").strip()
        if not key:
            continue
        values: dict[str, str] = {}
        service_type = str(item.get("type") or "").strip()
        if not service_type:
            values["type"] = key if key in service_types else "custom"
        elif service_type not in service_types and key in service_types:
            values["type"] = key
        provision = str(item.get("provision") or "").strip()
        if not provision or provision not in provisions:
            values["provision"] = default_provision
        if values:
            operations.append(
                {
                    "op": "technology.service.update",
                    "key": key,
                    "scope": "shared",
                    "values": values,
                }
            )
    return operations


def _deterministic_contract_file_repairs(
    root: Path | str,
) -> tuple[dict[str, str], list[dict[str, Any]]]:
    """Build text-preserving deterministic repairs without requiring other files ready."""

    project_root = Path(root).expanduser().resolve(strict=True)
    projection = compile_project_definition(project_root)
    operations = _technology_repair_operations(projection)
    texts: dict[str, str] = {}
    summaries: list[dict[str, Any]] = []
    for operation in operations:
        source_ref, target, mode, changes = _apply_operation(
            project_root, texts, operation
        )
        summaries.append(
            {
                "target": target,
                "key": str(operation.get("key") or ""),
                "mode": mode,
                "source_ref": source_ref,
                "changes": changes,
            }
        )
    return texts, summaries


def plan_contract_repair(
    root: Path | str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Plan only deterministic repairs for a current-version invalid contract."""

    project_root = Path(root).expanduser().resolve(strict=True)
    projection = compile_project_definition(project_root)
    if projection.get("migration_required"):
        raise ValueError("seed_repair_migration_required")
    configs = projection.get("configs")
    lock = configs.get(".maw/seed.lock") if isinstance(configs, dict) else None
    seed_version = str(lock.get("seed_version") or "") if isinstance(lock, dict) else ""
    if seed_version != SEED_VERSION:
        raise ValueError("seed_repair_version_mismatch")
    if projection.get("status") == "ready":
        raise ValueError("seed_repair_not_required")
    operations = _technology_repair_operations(projection)
    if not operations:
        raise ValueError("seed_repair_manual_resolution_required")
    try:
        public, private = _plan_change_set(
            project_root,
            {
                "schema": "mawflow.seed_change_set.v2",
                "base_projection_fingerprint": projection["fingerprint"],
                "base_contract_fingerprint": contract_fingerprint(),
                "reason": "本地工作台按当前 Seed 契约修复可确定的结构字段",
                "operations": operations,
            },
            allow_invalid_base=True,
        )
    except ValueError as exc:
        if str(exc).startswith("seed_change_proposed_projection_invalid"):
            raise ValueError("seed_repair_manual_resolution_required") from exc
        raise
    repair = {
        "schema": "mawflow.seed_contract_repair.v1",
        "mode": "deterministic_current_version",
        "issue_count": int(projection.get("summary", {}).get("errors") or 0),
        "operation_count": len(operations),
        "manual_resolution_required": False,
    }
    public["repair"] = repair
    private["repair"] = repair
    return public, private


def apply_change_plan(root: Path | str, plan: dict[str, Any], confirmation: str, *, backup_root: Path | str) -> dict[str, Any]:
    project_root = Path(root).expanduser().resolve(strict=True)
    if confirmation != plan.get("confirmation_required"):
        raise ValueError("seed_change_confirmation_required")
    try:
        expires = datetime.fromisoformat(str(plan.get("expires_at") or ""))
    except ValueError as exc:
        raise ValueError("seed_change_plan_invalid") from exc
    if datetime.now(timezone.utc) >= expires:
        raise ValueError("seed_change_plan_expired")
    current = compile_project_definition(project_root)
    if current["fingerprint"] != plan.get("base_projection_fingerprint"):
        raise ValueError("seed_change_projection_conflict")
    private_writes = plan.get("private_writes")
    if not isinstance(private_writes, list) or not private_writes:
        raise ValueError("seed_change_private_plan_required")
    backup_dir = Path(backup_root).expanduser().resolve() / str(plan["plan_key"])
    backup_dir.mkdir(parents=True, exist_ok=False)
    written: list[Path] = []
    try:
        for write in private_writes:
            source_ref = str(write["source_ref"])
            path = project_root / source_ref
            current_text, _, exists = _read(project_root, source_ref, str(write["original_text"]) if not write["existed"] else "")
            if exists != bool(write["existed"]) or _hash(current_text) != write["expected_hash"]:
                raise ValueError("seed_change_config_conflict")
            backup_path = backup_dir / source_ref
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            _atomic_write(backup_path, current_text, 0o600)
            _atomic_write(path, str(write["proposed_text"]), int(write["mode"]) or 0o600)
            if path.read_text(encoding="utf-8") != write["proposed_text"]:
                raise ValueError("seed_change_readback_failed")
            written.append(path)
        projection = compile_project_definition(project_root)
        if projection["status"] != "ready":
            raise ValueError("seed_change_validation_failed")
        change_key = f"seed-change-{secrets.token_hex(10)}"
        record_path = project_root / ".maw" / "changes" / f"{change_key}.yaml"
        record = {
            "schema": "mawflow.seed_change_record.v2",
            "change_key": change_key,
            "plan_key": plan["plan_key"],
            "reason": plan.get("reason", ""),
            "risk": plan.get("risk", "high"),
            "operations": plan["operations"],
            "previous_projection_fingerprint": plan["base_projection_fingerprint"],
            "projection_fingerprint": projection["fingerprint"],
            "applied_at": _utcnow(),
        }
        _atomic_write(record_path, yaml.safe_dump(record, allow_unicode=True, sort_keys=False), 0o644)
    except Exception:
        for write in reversed(private_writes):
            path = project_root / str(write["source_ref"])
            if write["existed"]:
                _atomic_write(path, str(write["original_text"]), int(write["mode"]) or 0o600)
            else:
                path.unlink(missing_ok=True)
        raise
    return {
        "schema": "mawflow.seed_change_result.v2",
        "status": "applied",
        "change_key": change_key,
        "plan_key": plan["plan_key"],
        "record_ref": f".maw/changes/{record_path.name}",
        "projection": projection,
        "rollback": {"available": True, "backup_ref": f"private-backup:{plan['plan_key']}"},
        "applied_at": _utcnow(),
    }


__all__ = ["apply_change_plan", "plan_change_set", "plan_contract_repair"]
