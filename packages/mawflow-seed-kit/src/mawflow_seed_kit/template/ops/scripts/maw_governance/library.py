"""Curated archive members; ordinary repository files are never auto-enrolled."""
from collections import defaultdict

from .extensions import CATEGORIES
from .store import digest


TEMPLATES = {
    "requirements": {"title": "需求文档", "sections": ["背景与业务目标", "读者、范围与不覆盖事项", "业务角色与术语", "业务流程和规则", "约束、条件与异常", "验收标准", "待确定事项与来源"]},
    "design": {"title": "设计文档", "sections": ["设计目标与范围", "现状及已确认约束", "总体方案与关键取舍", "模块、数据与接口设计", "异常、安全与兼容", "实现和验证计划", "风险与依据"]},
    "acceptance": {"title": "测试与验收文档", "sections": ["验收对象与版本", "范围、环境和准备条件", "场景、步骤与预期结果", "实际验证与证据", "未验证项和缺陷", "人工验收结论与后续事项"]},
    "delivery": {"title": "部署与交付文档", "sections": ["交付范围与适用读者", "版本、制品与依赖", "部署准备和操作步骤", "核验、回滚与异常恢复", "实际交付与部署状态", "使用影响、限制与待办"]},
    "maintenance": {"title": "使用与维护文档", "sections": ["用途、读者与使用范围", "准备条件与权限", "日常操作和业务流程", "维护、监控与排障", "恢复和升级", "已知限制与支持依据"]},
}


def templates():
    return {"schema": "mawflow.delivery_templates.v1", "version": "delivery-v1", "templates": TEMPLATES,
            "instructions": "按目标读者生成完整正文。冻结选择的问答和资料版本，分别陈述要求、实现与验证。缺少依据写待完善，不能只拼字段清单，也不能编造接口、功能、测试或承诺。默认草稿，正文和来源均可审阅。"}


def library(snapshot: dict, *, include_history=False, search="", category="") -> dict:
    groups = defaultdict(list)
    for row in snapshot["artifacts"]:
        groups[row["artifact"]["document_key"]].append(row)
    members = []
    for key, rows in groups.items():
        replaced = {row["artifact"]["previous_ref"] for row in rows}
        heads = [row for row in rows if row["id"] not in replaced]
        for row in rows:
            artifact = row["artifact"]
            history = row["id"] in replaced
            if history and not include_history:
                continue
            classification = artifact.get("category", artifact["document_kind"])
            title = artifact.get("document_title") or row["title"] or key
            summary = artifact.get("summary", "")
            if (category and classification != category) or (search and search.casefold() not in (title + " " + summary).casefold()):
                continue
            content_hash = artifact.get("content_hash") or next((e["sha256"] for e in row["evidence"] if e["path"] == artifact["path"]), "")
            members.append({"document_key": key, "version_ref": row["id"], "version_key": artifact["version_key"],
                "title": title, "summary": summary, "category": classification, "category_label": CATEGORIES.get(classification, "待整理"),
                "origin": artifact.get("origin", "existing"), "document_state": artifact.get("document_state", "draft"),
                "retention": artifact.get("retention", "current"), "tags": artifact.get("tags", []),
                "path": artifact["path"], "resource_ref": artifact.get("resource_ref", ""), "content_hash": content_hash,
                "mime": artifact.get("mime", "text/markdown"), "size": artifact.get("size"), "previous_ref": artifact["previous_ref"],
                "history": history, "conflict": not history and len(heads) > 1, "updated_at": row["captured_at"],
                "task_ref": row["context"].get("task_ref", ""), "run_ref": row["context"].get("session_ref", ""),
                "release_ref": artifact.get("release_ref", ""), "freshness": row["freshness"], "integrity": row["artifact_integrity"],
                "availability": "host_verification_required" if artifact.get("resource_ref") else row["artifact_integrity"],
                "source_path": row["source_path"], "source_hash": row["source_hash"], "question_refs": artifact["question_refs"]})
    members.sort(key=lambda m: (m["updated_at"], m["version_ref"]), reverse=True)
    return {"schema": "mawflow.curated_archives.v1", "project_key": snapshot["project_key"], "members": members,
            "total": len(members), "input_hash": digest(members), "source_version": snapshot["source_version"],
            "partial": snapshot["partial"], "issues": snapshot["issues"], "categories": CATEGORIES,
            "trust_boundary": {"repository_files_auto_enrolled": False, "uploaded": False, "business_rules_confirmed": False}}
