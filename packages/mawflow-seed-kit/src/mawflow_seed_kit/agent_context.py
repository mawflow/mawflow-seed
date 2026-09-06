"""Portable project bootstrap, bounded context, and independent agent readiness.

This module reads shared declarations only. It neither executes project commands
nor reads local bindings, credentials, source trees, or session transcripts.
"""
from __future__ import annotations

import hashlib
from importlib.resources import files
import json
from pathlib import Path, PurePosixPath
from typing import Any

import yaml

START = "<!-- mawflow:bootstrap:start -->"
END = "<!-- mawflow:bootstrap:end -->"
MAX_BYTES = 256 * 1024
FORBIDDEN_PARTS = {".git", ".local", ".ssh", "node_modules", "runtime", "workspaces", "artifacts", "prompts"}


def agent_contract() -> dict[str, Any]:
    return json.loads(files("mawflow_seed_kit").joinpath("resources/agent-contract.v1.json").read_text(encoding="utf-8"))


def resolve_agent_adapter(agent_name: str = "") -> dict[str, str]:
    """Use explicit host identity only; unknown tools take the generic entry."""
    normalized = agent_name.strip().lower().replace("_", "-")
    aliases = {"claude code": "claude", "claude-code": "claude", "gemini cli": "gemini", "gemini-cli": "gemini", "cursor agent": "cursor", "cursor-agent": "cursor", "generic": "generic_ai", "generic-ai": "generic_ai"}
    aliases.update({"chatgpt": "chatgpt_web", "chatgpt web": "chatgpt_web", "chatgpt-web": "chatgpt_web", "github-web": "chatgpt_web"})
    key = aliases.get(normalized, normalized)
    if key not in agent_contract()["adapters"]:
        key = "generic_ai"
    return {"agent": key, "entry_file": agent_contract()["adapters"][key]["file"], "resolution": "generic_fallback" if key == "generic_ai" else "explicit_identity"}


def _hash(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode()).hexdigest()


def _safe_path(root: Path, ref: str) -> Path:
    relative = PurePosixPath(ref)
    if (not ref or relative.is_absolute() or ".." in relative.parts or "\\" in ref
            or ":" in ref or any(part in FORBIDDEN_PARTS for part in relative.parts)
            or "docs/archive" in ref or "payload" in relative.parts
            or any("secret" in part.lower() or ".local." in part for part in relative.parts)):
        raise ValueError("seed_agent_ref_forbidden")
    path = root
    for part in relative.parts:
        path = path / part
        if path.is_symlink():
            raise ValueError("seed_agent_symlink_forbidden")
    path.resolve().relative_to(root)
    return path


def _text(root: Path, ref: str) -> str:
    path = _safe_path(root, ref)
    if path.stat().st_size > MAX_BYTES:
        raise ValueError("seed_agent_source_too_large")
    return path.read_text(encoding="utf-8")


def _mapping(root: Path, ref: str) -> dict[str, Any]:
    value = yaml.safe_load(_text(root, ref))
    if not isinstance(value, dict):
        raise ValueError("seed_agent_mapping_required")
    return value


def _merge_missing(existing: dict[str, Any], defaults: dict[str, Any]) -> dict[str, Any]:
    result = dict(existing)
    for key, value in defaults.items():
        if key not in result:
            result[key] = value
        elif isinstance(value, dict) and isinstance(result[key], dict):
            result[key] = _merge_missing(result[key], value)
    return result


def upgrade_agent_entry(existing: dict[str, Any]) -> dict[str, Any]:
    """Add portable fields while retaining project extensions and legacy aliases."""
    result = _merge_missing(existing, agent_contract()["entry_defaults"])
    result["schema_version"] = max(3, int(existing.get("schema_version") or 0))
    result["agent_protocol_version"] = 1
    for key, definition in agent_contract()["adapters"].items():
        adapter = result["tool_adapters"].setdefault(key, {})
        if adapter.get("status") == "planned_generated_adapter":
            adapter["status"] = "supported"
        if key == "cursor" and adapter.get("file") == ".cursor/rules/mawflow.md":
            adapter["file"] = "AGENTS.md"
        for field, value in definition.items():
            adapter.setdefault(field, value)
    return result


def upgrade_agent_rules(existing: dict[str, Any]) -> dict[str, Any]:
    result = dict(existing)
    result["schema_version"] = max(1, int(existing.get("schema_version") or 0))
    rules = list(existing.get("rules") or [])
    ids = {item.get("id") for item in rules if isinstance(item, dict)}
    rules.extend(item for item in agent_contract()["rules"] if item["id"] not in ids)
    result["rules"] = rules
    return result


def bootstrap_block(adapter: str) -> str:
    contract = agent_contract()
    definition = contract["adapters"][adapter]
    load = "@AI_START_HERE.md" if definition["loader"] == "import" else "Read [AI_START_HERE.md](AI_START_HERE.md) before working in this project."
    web = []
    if definition["loader"] == "repository_links":
        web = [
            "",
            "## 从 GitHub 读取源码的网页 Agent",
            "本文件是用户显式指定的网页入口，不假定 ChatGPT Web 或连接器自动加载 AGENTS.md、@ 导入或隐藏目录。",
            "先记录 owner/repository、目标 branch/ref 与实际 commit SHA；所有引用固定到同一提交。连接器不能选择 ref 时说明实际读取范围与版本不确定性。",
            "打开 [通用规则](.maw/agent-rules.yaml)、[读取路由](.maw/agent-entry.yaml)、[项目](.maw/project.yaml)、[组件](.maw/components.yaml) 与 [模块](.maw/modules.yaml)，然后只读取当前任务相关文件。",
            "搜索片段不是完整源码；先获取文件正文。仓库无权限、文件缺失或内容截断时明确说明缺口，不猜测未读代码。",
            "只有读取能力时交付带路径和提交依据的分析、建议补丁与待执行验证。测试、提交、推送、部署必须有当前会话可用工具和真实结果才能标为完成。",
            "需要执行环境时按 [交接协议](CHATGPT_TO_AI.md) 交接仓库/ref/commit、目标、已读文件、允许路径、修改建议、验证命令和未验证项；不要索取或导出私钥与生产凭据。",
            "可选：有 CLI 的协作者运行 `mawflow-seed-kit context . --agent chatgpt-web --format markdown`，提供带来源和哈希的有界上下文。网页端无需安装 CLI、MCP、RTK 或 Skill。",
        ]
    return "\n".join([
        START,
        "# MAWflow Agent 入口",
        load,
        "共享规则与项目事实以 `.maw/agent-entry.yaml`、`.maw/agent-rules.yaml` 为准。",
        "只读取本任务所需的模块和文档；先确认允许路径、禁止路径及验证命令。",
        "不自动读取 prompts、归档、本机私有目录；不提交秘密或无关改动。",
        "工具、Skill、MCP、RTK 均非读取项目规则的前置条件；已有授权按任务范围延续。",
        "完成时区分已修改、已验证、已发布与真人验收，列出未验证项。",
        *web,
        END,
    ]) + "\n"


def merge_bootstrap(text: str, adapter: str) -> str:
    block = bootstrap_block(adapter)
    if START in text or END in text:
        if text.count(START) != 1 or text.count(END) != 1 or text.index(START) > text.index(END):
            raise ValueError("seed_agent_managed_block_ambiguous")
        before, rest = text.split(START, 1)
        _, after = rest.split(END, 1)
        return before + block.rstrip("\n") + after
    return block + ("\n" + text if text else "")


def portable_agent_files(root: Path | str) -> dict[str, str]:
    """Return reviewable proposals; never write files or overwrite custom prose."""
    project_root = Path(root).expanduser().resolve()
    proposed: dict[str, str] = {}
    for ref, transform in [(".maw/agent-entry.yaml", upgrade_agent_entry), (".maw/agent-rules.yaml", upgrade_agent_rules)]:
        path = _safe_path(project_root, ref)
        current = _mapping(project_root, ref) if path.exists() else {}
        updated = transform(current)
        proposed[ref] = _text(project_root, ref) if updated == current else yaml.safe_dump(updated, allow_unicode=True, sort_keys=False)
    for key, adapter in agent_contract()["adapters"].items():
        ref = adapter["file"]
        if ref in proposed or key == "generic_ai":
            continue
        path = _safe_path(project_root, ref)
        proposed[ref] = merge_bootstrap(_text(project_root, ref) if path.exists() else "", key)
    return proposed


def inspect_agent_readiness(root: Path | str) -> dict[str, Any]:
    project_root = Path(root).expanduser().resolve(strict=True)
    findings: list[dict[str, str]] = []
    sources: list[dict[str, str]] = []

    def report(code: str, ref: str, message: str, severity: str = "error") -> None:
        findings.append({"code": code, "source_ref": ref, "message": message, "severity": severity})

    def read(ref: str) -> str:
        try:
            text = _text(project_root, ref)
            if not text.strip():
                raise ValueError("empty")
            sources.append({"source_ref": ref, "content_hash": _hash(text)})
            return text
        except (OSError, UnicodeError, ValueError):
            report("seed_agent_source_invalid", ref, "入口引用必须是项目内非空、非链接的共享文件")
            return ""

    try:
        entry = yaml.safe_load(read(".maw/agent-entry.yaml")) or {}
        if not isinstance(entry, dict):
            raise ValueError("mapping")
    except (ValueError, yaml.YAMLError):
        entry = {}
    if entry.get("agent_protocol_version") != 1:
        report("seed_agent_protocol_upgrade_required", ".maw/agent-entry.yaml", "请通过 Seed 迁移预览补齐通用 Agent 协议；项目结构状态独立保留")
    read("AI_START_HERE.md")
    startup = entry.get("startup") or {}
    order = startup.get("recommended_order") if isinstance(startup, dict) else None
    if not isinstance(order, list) or not order:
        report("seed_agent_startup_missing", ".maw/agent-entry.yaml", "缺少启动读取顺序")
    else:
        for ref in order:
            if not isinstance(ref, str) or not ref.strip():
                report("seed_agent_startup_invalid", ".maw/agent-entry.yaml", "启动引用必须是非空路径")
            elif ref not in {"AGENTS.md", "AI_START_HERE.md", ".maw/agent-entry.yaml"}:
                read(ref)
    for key in ("facts", "protected_paths", "execution_contract"):
        if not isinstance(entry.get(key), dict) or not entry[key]:
            report("seed_agent_contract_missing", ".maw/agent-entry.yaml", f"缺少 {key} 契约")
    try:
        rules_doc = yaml.safe_load(read(".maw/agent-rules.yaml")) or {}
        rules = rules_doc.get("rules") or []
        present = {item.get("id"): item for item in rules if isinstance(item, dict)}
        for rule in agent_contract()["rules"]:
            found = present.get(rule["id"], {})
            if not str(found.get("summary") or "").strip():
                report("seed_agent_rule_missing", ".maw/agent-rules.yaml", f"缺少通用规则 {rule['id']}")
    except (AttributeError, TypeError, yaml.YAMLError):
        report("seed_agent_rules_invalid", ".maw/agent-rules.yaml", "通用规则格式无效")
    adapters: dict[str, Any] = {}
    for key, definition in agent_contract()["adapters"].items():
        ref = definition["file"]
        text = read(ref)
        valid = bool(text)
        declared = entry.get("tool_adapters")
        declared = declared.get(key) if isinstance(declared, dict) else None
        if not isinstance(declared, dict) or any(declared.get(field) != definition[field] for field in ("file", "loader")):
            valid = False
            report("seed_agent_adapter_declaration_invalid", ".maw/agent-entry.yaml", f"工具入口声明不匹配：{key}")
        if key != "generic_ai" and bootstrap_block(key).strip() not in text:
            valid = False
            report("seed_agent_adapter_drift", ref, "工具入口缺失或生成块漂移；通过受控迁移保留人工内容并更新入口")
        adapters[key] = {"file": ref, "static_status": "ready" if valid else "needs_attention", "runtime_status": "unverified"}
    return {
        "schema": "mawflow.agent_readiness.v1",
        "status": "ready" if not findings else "needs_attention",
        "protocol_version": entry.get("agent_protocol_version"),
        "evidence_level": "static_contract",
        "runtime_verified": False,
        "adapters": adapters,
        "issues": findings,
        "sources": sources,
        "capability_tiers": agent_contract()["capability_tiers"],
    }


def export_agent_context(root: Path | str, *, module_key: str = "", task_kind: str = "development", max_chars: int = 12000, agent_name: str = "") -> dict[str, Any]:
    """Export safe shared metadata and bounded task docs; local overlays stay private."""
    if not 1000 <= max_chars <= 50000:
        raise ValueError("seed_agent_context_budget_invalid")
    project_root = Path(root).expanduser().resolve(strict=True)
    contract = agent_contract()
    if task_kind not in contract["task_kinds"]:
        raise ValueError("seed_agent_task_kind_invalid")
    entry = _mapping(project_root, ".maw/agent-entry.yaml")
    project = _mapping(project_root, ".maw/project.yaml").get("project") or {}
    modules = _mapping(project_root, ".maw/modules.yaml").get("modules") or []
    selected = [item for item in modules if isinstance(item, dict) and item.get("key") == module_key] if module_key else []
    if module_key and not selected:
        raise ValueError("seed_agent_module_not_found")
    refs = [".maw/agent-context.md", ".maw/agent-rules.yaml"]
    routes = entry.get("task_routes") or {}
    for module in selected:
        if module.get("doc"):
            refs.append(module["doc"])
    refs.extend(routes.get(task_kind, []) if isinstance(routes, dict) else [])
    documents: list[dict[str, Any]] = []
    omitted: list[dict[str, str]] = []
    remaining = max_chars
    for ref in dict.fromkeys(refs):
        try:
            text = _text(project_root, ref)
        except FileNotFoundError:
            omitted.append({"source_ref": ref, "reason": "not_configured"})
            continue
        if remaining <= 0:
            omitted.append({"source_ref": ref, "reason": "budget"})
            continue
        content = text[:remaining]
        documents.append({"source_ref": ref, "content_hash": _hash(text), "content": content, "truncated": len(content) < len(text)})
        remaining -= len(content)
    return {
        "schema": "mawflow.agent_context.v1",
        "adapter": resolve_agent_adapter(agent_name),
        "project": {key: project.get(key, "") for key in ("key", "name", "type")},
        "task_kind": task_kind,
        "module_key": module_key,
        "module": [{key: item[key] for key in ("key", "name", "doc", "owned_paths", "source_paths", "blocked_paths") if key in item} for item in selected],
        "documents": documents,
        "omitted": omitted,
        "content_chars": max_chars - remaining,
        "max_chars": max_chars,
        "local_overlays_included": False,
        "provenance": "shared_project_files",
    }


def render_agent_context(payload: dict[str, Any]) -> str:
    lines = [f"# {payload['project']['name']} · 任务上下文", f"任务类型：{payload['task_kind']}；模块：{payload['module_key'] or '待定位'}",
             f"Agent 入口：{payload['adapter']['entry_file']}（{payload['adapter']['resolution']}）",
             f"正文预算：{payload['content_chars']}/{payload['max_chars']} 字符；仅共享文件，不含本机 overlay。",
             "仓库/ref/commit 由提供者补充；本导出不证明测试、部署或真实 Agent 运行。", ""]
    if payload["module"]:
        lines.extend(["模块边界：", json.dumps(payload["module"], ensure_ascii=False), ""])
    for document in payload["documents"]:
        lines.extend([f"## {document['source_ref']}", f"来源摘要：{document['content_hash']}；正文截断：{'是' if document['truncated'] else '否'}", document["content"], ""])
    if payload["omitted"]:
        lines.append("未载入：" + json.dumps(payload["omitted"], ensure_ascii=False))
    return "\n".join(lines)
