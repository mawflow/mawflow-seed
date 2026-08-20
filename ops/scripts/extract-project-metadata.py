#!/usr/bin/env python3
"""Extract project metadata for audits, dashboards, and AI preconditions."""

from __future__ import annotations

import argparse
import copy
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

try:
    import yaml
except ImportError as exc:  # pragma: no cover - environment guard
    raise RuntimeError("PyYAML is required for project metadata extraction") from exc


DEFAULT_SECTIONS = (
    "repository_identity",
    "host_project_mcp",
    "modules",
    "capabilities",
    "signals",
    "todos",
    "experience_candidates",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract MAW repository identity, module, capability, project signal, TODO, and experience metadata.",
    )
    parser.add_argument("--root", default=".", help="Project root. Default: current directory.")
    parser.add_argument(
        "--section",
        default="all",
        choices=[
            "all",
            "repository-identity",
            "host-project-mcp",
            "modules",
            "capabilities",
            "signals",
            "todos",
            "experience",
            "ai-preconditions",
        ],
        help="Limit output to one section.",
    )
    parser.add_argument("--format", default="json", choices=["json", "markdown"], help="Output format.")
    parser.add_argument("--output", default="-", help="Output path or '-' for stdout.")
    parser.add_argument(
        "--include-resolved",
        action="store_true",
        help="Include resolved/superseded/ignored project signals in summaries.",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.root).resolve()
    payload = build_payload(root, include_resolved=args.include_resolved)
    selected = select_section(payload, args.section)

    if args.format == "json":
        text = json.dumps(selected, ensure_ascii=False, indent=2) + "\n"
    else:
        text = render_markdown(selected, section=args.section)

    if args.output == "-":
        print(text, end="")
    else:
        Path(args.output).write_text(text, encoding="utf-8")
    return 0


def build_payload(root: Path, include_resolved: bool = False) -> Dict[str, Any]:
    repository_identity_doc = load_repository_identity(root)
    environments_doc = load_yaml(root / ".maw" / "environments.yaml")
    host_project_mcp_doc = build_host_project_mcp(environments_doc, repository_identity_doc)
    modules_doc = load_yaml(root / ".maw" / "modules.yaml")
    capabilities_doc = load_yaml(root / ".maw" / "capabilities.yaml")
    signals_doc = load_yaml(root / ".maw" / "project-signals.yaml")

    modules = modules_doc.get("modules") or []
    capabilities = capabilities_doc.get("capabilities") or []
    signals = signals_doc.get("signals") or []
    if not include_resolved:
        signals = [
            item for item in signals if str(item.get("status") or "").strip() not in {"resolved", "superseded", "ignored"}
        ]

    todos = read_markdown_table(root / "docs" / "planning" / "todos" / "active.md")
    experience_candidates = read_markdown_table(root / "docs" / "ai-instructions" / "experience-candidates.md")
    keyword_candidates = read_markdown_table(root / "docs" / "ai-instructions" / "keyword-candidates.md")
    execution_candidates = read_markdown_table(root / "docs" / "ai-instructions" / "execution-lesson-candidates.md")

    ai_preconditions = build_ai_preconditions(
        signals=signals,
        todos=todos,
        capabilities=capabilities,
        repository_identity=repository_identity_doc,
        host_project_mcp=host_project_mcp_doc,
    )

    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "project_root": ".",
        "summary": {
            "repository_roles": len(
                ((repository_identity_doc.get("effective_identity") or {}).get("current_repository") or {}).get("roles")
                or []
            ),
            "host_project_mcp_status": host_project_mcp_doc.get("status") or "unknown",
            "modules": len(modules),
            "capabilities": len(capabilities),
            "signals": len(signals),
            "active_todos": len(todos),
            "experience_candidates": len(experience_candidates),
            "keyword_candidates": len(keyword_candidates),
            "execution_lesson_candidates": len(execution_candidates),
            "ai_preconditions": len(ai_preconditions),
        },
        "repository_identity": repository_identity_doc,
        "host_project_mcp": host_project_mcp_doc,
        "modules": modules,
        "capabilities": capabilities,
        "signals": signals,
        "todos": todos,
        "experience_candidates": experience_candidates,
        "keyword_candidates": keyword_candidates,
        "execution_lesson_candidates": execution_candidates,
        "ai_preconditions": ai_preconditions,
    }


def load_yaml(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be a mapping: {path}")
    return data


def load_repository_identity(root: Path) -> Dict[str, Any]:
    base_path = root / ".maw" / "repository-identity.yaml"
    base = load_yaml(base_path)
    if not base:
        return {
            "schema_version": 1,
            "status": "missing",
            "declared_roles": [],
            "detected_roles": [
                {
                    "role": "unknown_legacy",
                    "confidence": "low",
                    "evidence": ["missing .maw/repository-identity.yaml"],
                }
            ],
            "effective_identity": {},
            "applied_overlays": [],
            "warnings": ["Repository identity map missing; treating repository as unknown_legacy."],
        }

    effective = copy.deepcopy(base)
    current = effective.setdefault("current_repository", {})
    declared_roles = normalize_roles(current)
    applied_overlays: List[Dict[str, Any]] = []

    for role in declared_roles:
        for overlay_path in sorted((root / ".maw" / "repository-identity.d" / role).glob("*.yaml")):
            overlay = load_yaml(overlay_path)
            priority = read_overlay_priority(overlay)
            applied_overlays.append(
                {
                    "role": role,
                    "path": str(overlay_path.relative_to(root)),
                    "priority": priority,
                }
            )

    applied_overlays.sort(key=lambda item: (declared_roles.index(item["role"]), item["priority"], item["path"]))
    for item in applied_overlays:
        overlay = load_yaml(root / item["path"])
        effective = deep_merge(effective, strip_overlay_metadata(overlay))

    detected_roles = detect_repository_roles(root, base)
    detected_role_names = [item["role"] for item in detected_roles]
    warnings = build_identity_warnings(declared_roles, detected_role_names)

    return {
        "schema_version": base.get("schema_version", 1),
        "status": "ready",
        "declared_primary_role": current.get("primary_role") or current.get("role") or "",
        "declared_roles": declared_roles,
        "detected_roles": detected_roles,
        "effective_identity": effective,
        "applied_overlays": applied_overlays,
        "warnings": warnings,
    }


def normalize_roles(current: Dict[str, Any]) -> List[str]:
    roles = normalize_list(current.get("roles"))
    fallback = str(current.get("primary_role") or current.get("role") or "").strip()
    if fallback and fallback not in roles:
        roles.insert(0, fallback)
    return roles or ["unknown_legacy"]


def read_overlay_priority(overlay: Dict[str, Any]) -> int:
    marker = overlay.get("repository_identity_overlay") or {}
    try:
        return int(marker.get("priority", 500))
    except (TypeError, ValueError):
        return 500


def strip_overlay_metadata(overlay: Dict[str, Any]) -> Dict[str, Any]:
    clean = copy.deepcopy(overlay)
    clean.pop("repository_identity_overlay", None)
    clean.pop("schema_version", None)
    return clean


def deep_merge(base: Dict[str, Any], overlay: Dict[str, Any]) -> Dict[str, Any]:
    result = copy.deepcopy(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def detect_repository_roles(root: Path, identity_doc: Dict[str, Any]) -> List[Dict[str, Any]]:
    detection = identity_doc.get("role_detection") or {}
    detectors = detection.get("detectors") or {}
    matched: List[Dict[str, Any]] = []

    for role, rules in detectors.items():
        if not isinstance(rules, dict) or rules.get("fallback"):
            continue
        evidence: List[str] = []
        if detector_matches(root, rules, evidence):
            matched.append(
                {
                    "role": role,
                    "confidence": rules.get("confidence") or "medium",
                    "evidence": evidence,
                    "required_context": normalize_list(rules.get("required_context")),
                }
            )

    if not matched:
        fallback_rules = detectors.get("unknown_legacy") or {}
        matched.append(
            {
                "role": "unknown_legacy",
                "confidence": fallback_rules.get("confidence") or "low",
                "evidence": ["no role detector matched"],
                "required_context": [],
            }
        )

    return matched


def detector_matches(root: Path, rules: Dict[str, Any], evidence: List[str]) -> bool:
    all_of = rules.get("all_of") or []
    any_of = rules.get("any_of") or []
    none_of = rules.get("none_of") or []

    for condition in all_of:
        if not condition_matches(root, condition, evidence):
            return False

    if any_of and not any(condition_matches(root, condition, evidence) for condition in any_of):
        return False

    for condition in none_of:
        local_evidence: List[str] = []
        if condition_matches(root, condition, local_evidence):
            return False

    return True


def condition_matches(root: Path, condition: Any, evidence: List[str]) -> bool:
    if not isinstance(condition, dict):
        return False

    path_value = condition.get("path_exists")
    if path_value:
        path = root / str(path_value)
        if path.exists():
            evidence.append(f"path exists: {path_value}")
            return True
        return False

    file_contains = condition.get("file_contains")
    if isinstance(file_contains, dict):
        rel_path = str(file_contains.get("path") or "")
        pattern = str(file_contains.get("pattern") or "")
        if not rel_path or not pattern:
            return False
        path = root / rel_path
        if not path.is_file():
            return False
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return False
        if re.search(pattern, text, flags=re.MULTILINE):
            evidence.append(f"file contains {pattern!r}: {rel_path}")
            return True
        return False

    if condition.get("git_origin_matches_template_source_git_url"):
        origin = read_git_origin_url(root)
        template_git_url = read_template_source_git_url(root)
        if not origin or not template_git_url:
            return False
        if normalize_git_url(origin) == normalize_git_url(template_git_url):
            evidence.append("git origin matches template_source.git_url")
            return True
        return False

    return False


def read_git_origin_url(root: Path) -> str:
    proc = subprocess.run(
        ["git", "config", "--get", "remote.origin.url"],
        cwd=str(root),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        return ""
    return proc.stdout.strip()


def read_template_source_git_url(root: Path) -> str:
    template_source = load_yaml(root / ".maw" / "template-source.yaml").get("template_source") or {}
    return str(template_source.get("git_url") or "").strip()


def normalize_git_url(value: str) -> str:
    normalized = value.strip()
    normalized = re.sub(r"^ssh://", "", normalized)
    normalized = re.sub(r"^https?://", "", normalized)
    normalized = re.sub(r"^git@", "", normalized)
    if ":" in normalized and "/" not in normalized.split(":", 1)[0]:
        normalized = normalized.replace(":", "/", 1)
    normalized = normalized.rstrip("/")
    if normalized.endswith(".git"):
        normalized = normalized[:-4]
    return normalized.lower()


def build_identity_warnings(declared_roles: List[str], detected_roles: List[str]) -> List[str]:
    warnings: List[str] = []
    declared_set = set(declared_roles)
    detected_set = set(detected_roles)
    if "unknown_legacy" in detected_set and declared_set != {"unknown_legacy"}:
        warnings.append("Declared repository roles exist, but role detection only matched unknown_legacy.")
    missing = sorted(role for role in declared_set if role not in detected_set and role != "unknown_legacy")
    extra = sorted(role for role in detected_set if role not in declared_set and role != "unknown_legacy")
    if missing:
        warnings.append(f"Declared roles not detected from repository structure: {', '.join(missing)}")
    if extra:
        warnings.append(f"Repository structure suggests additional roles: {', '.join(extra)}")
    return warnings


def build_host_project_mcp(environments_doc: Dict[str, Any], repository_identity: Dict[str, Any]) -> Dict[str, Any]:
    host_purpose_modes = environments_doc.get("host_purpose_modes") or {}
    host_project_binding = environments_doc.get("host_project_binding") or {}
    project_level_mcp = environments_doc.get("project_level_mcp") or {}
    effective_identity = repository_identity.get("effective_identity") or {}
    current_repository = effective_identity.get("current_repository") or {}
    repository_roles = normalize_list(current_repository.get("roles"))

    warnings: List[str] = []
    if not host_purpose_modes:
        warnings.append("host_purpose_modes missing from .maw/environments.yaml")
    if not host_project_binding:
        warnings.append("host_project_binding missing from .maw/environments.yaml")
    if not project_level_mcp:
        warnings.append("project_level_mcp missing from .maw/environments.yaml")
    if project_level_mcp and project_level_mcp.get("enabled_by_default") is not False:
        warnings.append("project_level_mcp.enabled_by_default should remain false in the seed protocol")
    if host_project_binding and host_project_binding.get("enabled_by_default") is not False:
        warnings.append("host_project_binding.enabled_by_default should remain false in the seed protocol")
    if project_level_mcp and project_level_mcp.get("non_maw_project_behavior") != "disabled_without_project_config":
        warnings.append("project_level_mcp.non_maw_project_behavior should preserve ordinary non-MAW projects")

    value_sets = {
        "purpose_type": sorted(host_purpose_modes.keys()),
        "ownership_type": normalize_list(host_project_binding.get("ownership_type_values")),
        "binding_type": normalize_list(host_project_binding.get("binding_type_values")),
        "source_access_mode": normalize_list(host_project_binding.get("source_access_mode_values")),
        "mcp_exposure_profile": normalize_list(host_project_binding.get("mcp_exposure_profile_values")),
    }
    required_ping_fields = [
        "project_key",
        "project_root",
        "repository_roles",
        "host_purpose",
        "ownership_type",
        "binding_type",
        "source_access_mode",
        "mcp_exposure_profile",
        "audit_id",
        "capability_version",
    ]

    status = "ready" if not warnings else "partial"
    if not host_purpose_modes and not host_project_binding and not project_level_mcp:
        status = "missing"

    return {
        "schema_version": 1,
        "status": status,
        "repository_roles": repository_roles,
        "host_purpose_modes": host_purpose_modes,
        "project_level_mcp": project_level_mcp,
        "host_project_binding": host_project_binding,
        "value_sets": value_sets,
        "channel_matrix": host_project_binding.get("channel_matrix") or {},
        "code_mirror_return_protocol": host_project_binding.get("code_mirror_return_protocol") or {},
        "required_mcp_audit_ping_fields": required_ping_fields,
        "ai_preconditions": [
            "Before MCP controlled writes, compare MCP audit ping repository_roles and binding fields with local .maw metadata.",
            "Customer hosts use customer_development binding and code_mirror source access; they do not receive full source clone/fetch/push.",
            "When MCP is unavailable, ordinary development can continue with warning, but customer sync, release, secrets, external delivery, and controlled writes require review.",
        ],
        "warnings": warnings,
    }


def read_markdown_table(path: Path) -> List[Dict[str, str]]:
    if not path.is_file():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    rows: List[Dict[str, str]] = []
    headers: List[str] = []
    in_table = False

    for raw_line in lines:
        line = raw_line.strip()
        if not line.startswith("|") or not line.endswith("|"):
            if in_table and headers:
                break
            continue

        cells = split_markdown_row(line)
        if not headers:
            headers = cells
            in_table = True
            continue

        if all(re.fullmatch(r":?-{3,}:?", cell.strip()) for cell in cells):
            continue

        if len(cells) < len(headers):
            cells.extend([""] * (len(headers) - len(cells)))
        row = {headers[index]: cells[index].strip() for index in range(len(headers))}
        if any(value for value in row.values()) and not is_placeholder_row(row):
            rows.append(row)

    return rows


def split_markdown_row(line: str) -> List[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def is_placeholder_row(row: Dict[str, str]) -> bool:
    identity_headers = ["TODO-ID", "TODO ID", "标题", "关键词", "key", "id", "signal_id"]
    present_identity_headers = [header for header in identity_headers if header in row]
    if not present_identity_headers:
        return False
    return not any(row.get(header, "").strip() for header in present_identity_headers)


def build_ai_preconditions(
    signals: Iterable[Dict[str, Any]],
    todos: Iterable[Dict[str, str]],
    capabilities: Iterable[Dict[str, Any]],
    repository_identity: Dict[str, Any],
    host_project_mcp: Dict[str, Any],
) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []

    effective_identity = repository_identity.get("effective_identity") or {}
    for text in normalize_list(effective_identity.get("ai_preconditions")):
        items.append(
            {
                "source_type": "repository_identity",
                "source_id": "repository-identity",
                "severity": "medium",
                "title": "仓库身份地图",
                "precondition": text,
                "related_modules": ["not_identified"],
                "related_capabilities": ["repository-identity-map"],
            }
        )

    for text in normalize_list(host_project_mcp.get("ai_preconditions")):
        items.append(
            {
                "source_type": "host_project_mcp",
                "source_id": "host-project-mcp",
                "severity": "high",
                "title": "宿主机项目 MCP 绑定治理",
                "precondition": text,
                "related_modules": ["not_identified"],
                "related_capabilities": ["host-project-mcp-governance"],
            }
        )

    for signal in signals:
        audiences = normalize_list(signal.get("audience"))
        if not audiences:
            audiences = ["human", "ai", "dashboard"]
        if "ai" not in audiences and "dashboard" not in audiences:
            continue
        for text in normalize_list(signal.get("ai_preconditions")):
            if text:
                items.append(
                    {
                        "source_type": "project_signal",
                        "source_id": signal.get("id") or "",
                        "severity": signal.get("severity") or "info",
                        "title": signal.get("title") or "",
                        "precondition": text,
                        "related_modules": normalize_list(signal.get("related_modules")),
                        "related_capabilities": normalize_list(signal.get("related_capabilities")),
                    }
                )

    for todo in todos:
        todo_id = todo.get("TODO-ID") or todo.get("TODO ID") or ""
        if not todo_id:
            continue
        items.append(
            {
                "source_type": "todo",
                "source_id": todo_id,
                "severity": "medium",
                "title": todo.get("当前假设") or todo_id,
                "precondition": f"该任务存在 active TODO {todo_id}：{todo.get('当前假设', '')}",
                "related_modules": split_list_cell(todo.get("受影响模块") or ""),
                "related_capabilities": [],
            }
        )

    for capability in capabilities:
        if str(capability.get("status") or "") == "blocked":
            items.append(
                {
                    "source_type": "capability",
                    "source_id": capability.get("key") or "",
                    "severity": "medium",
                    "title": capability.get("name") or capability.get("key") or "",
                    "precondition": f"公共能力 {capability.get('key')} 当前 blocked，复用前需确认阻塞原因。",
                    "related_modules": normalize_list(capability.get("consumed_by_modules")),
                    "related_capabilities": [capability.get("key") or ""],
                }
            )

    return items


def normalize_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return split_list_cell(value)
    return [str(value).strip()] if str(value).strip() else []


def split_list_cell(value: str) -> List[str]:
    return [part.strip() for part in re.split(r"[,，、/]", value) if part.strip()]


def select_section(payload: Dict[str, Any], section: str) -> Dict[str, Any]:
    if section == "all":
        return payload
    if section == "repository-identity":
        return {
            "schema_version": payload["schema_version"],
            "generated_at": payload["generated_at"],
            "repository_identity": payload["repository_identity"],
        }
    if section == "host-project-mcp":
        return {
            "schema_version": payload["schema_version"],
            "generated_at": payload["generated_at"],
            "host_project_mcp": payload["host_project_mcp"],
        }
    if section == "experience":
        return {
            "schema_version": payload["schema_version"],
            "generated_at": payload["generated_at"],
            "experience_candidates": payload["experience_candidates"],
            "keyword_candidates": payload["keyword_candidates"],
            "execution_lesson_candidates": payload["execution_lesson_candidates"],
        }
    key = "ai_preconditions" if section == "ai-preconditions" else section
    return {
        "schema_version": payload["schema_version"],
        "generated_at": payload["generated_at"],
        key: payload.get(key, []),
    }


def render_markdown(data: Dict[str, Any], section: str) -> str:
    lines = ["# 项目元数据摘要", ""]
    generated_at = data.get("generated_at", "")
    if generated_at:
        lines.extend([f"- generated_at: `{generated_at}`", ""])

    if "summary" in data:
        lines.extend(["## Summary", ""])
        for key, value in data["summary"].items():
            lines.append(f"- {key}: {value}")
        lines.append("")

    render_list_section(lines, "AI Preconditions", data.get("ai_preconditions"), "precondition")
    render_repository_identity(lines, data.get("repository_identity"))
    render_host_project_mcp(lines, data.get("host_project_mcp"))
    render_list_section(lines, "Project Signals", data.get("signals"), "title")
    render_list_section(lines, "Capabilities", data.get("capabilities"), "key")
    render_list_section(lines, "Active Todos", data.get("todos"), "TODO-ID")
    render_list_section(lines, "Modules", data.get("modules"), "key")

    if section == "experience" or "experience_candidates" in data:
        render_list_section(lines, "Experience Candidates", data.get("experience_candidates"), "标题")
        render_list_section(lines, "Keyword Candidates", data.get("keyword_candidates"), "关键词")
        render_list_section(lines, "Execution Lesson Candidates", data.get("execution_lesson_candidates"), "标题")

    return "\n".join(lines).rstrip() + "\n"


def render_repository_identity(lines: List[str], identity: Optional[Dict[str, Any]]) -> None:
    if identity is None:
        return
    lines.extend(["## Repository Identity", ""])
    if not identity:
        lines.extend(["- none", ""])
        return
    lines.append(f"- status: {identity.get('status') or 'unknown'}")
    primary = identity.get("declared_primary_role") or ""
    if primary:
        lines.append(f"- primary_role: {primary}")
    declared = identity.get("declared_roles") or []
    if declared:
        lines.append(f"- declared_roles: {', '.join(declared)}")
    detected = [item.get("role") for item in identity.get("detected_roles") or [] if item.get("role")]
    if detected:
        lines.append(f"- detected_roles: {', '.join(detected)}")
    overlays = identity.get("applied_overlays") or []
    if overlays:
        lines.append(f"- applied_overlays: {len(overlays)}")
    warnings = identity.get("warnings") or []
    if warnings:
        for warning in warnings:
            lines.append(f"- warning: {warning}")
    lines.append("")


def render_host_project_mcp(lines: List[str], host_project_mcp: Optional[Dict[str, Any]]) -> None:
    if host_project_mcp is None:
        return
    lines.extend(["## Host Project MCP", ""])
    if not host_project_mcp:
        lines.extend(["- none", ""])
        return
    lines.append(f"- status: {host_project_mcp.get('status') or 'unknown'}")
    roles = host_project_mcp.get("repository_roles") or []
    if roles:
        lines.append(f"- repository_roles: {', '.join(roles)}")
    value_sets = host_project_mcp.get("value_sets") or {}
    for key in ("purpose_type", "ownership_type", "binding_type", "source_access_mode", "mcp_exposure_profile"):
        values = value_sets.get(key) or []
        if values:
            lines.append(f"- {key}: {', '.join(values)}")
    matrix = host_project_mcp.get("channel_matrix") or {}
    if matrix:
        lines.append(f"- channel_matrix: {len(matrix)}")
    required = host_project_mcp.get("required_mcp_audit_ping_fields") or []
    if required:
        lines.append(f"- required_mcp_audit_ping_fields: {', '.join(required)}")
    warnings = host_project_mcp.get("warnings") or []
    if warnings:
        for warning in warnings:
            lines.append(f"- warning: {warning}")
    lines.append("")


def render_list_section(lines: List[str], title: str, items: Optional[List[Dict[str, Any]]], title_key: str) -> None:
    if items is None:
        return
    lines.extend([f"## {title}", ""])
    if not items:
        lines.extend(["- none", ""])
        return
    for item in items:
        name = item.get(title_key) or item.get("name") or item.get("id") or item.get("key") or "untitled"
        status = item.get("status")
        severity = item.get("severity")
        suffix_parts = [str(value) for value in (status, severity) if value]
        suffix = f" ({', '.join(suffix_parts)})" if suffix_parts else ""
        lines.append(f"- {name}{suffix}")
    lines.append("")


if __name__ == "__main__":
    raise SystemExit(main())
