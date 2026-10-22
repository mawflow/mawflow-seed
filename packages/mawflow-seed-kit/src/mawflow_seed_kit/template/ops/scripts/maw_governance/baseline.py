"""Read-only baseline inventory. Coverage assertions need explicit version references."""
from __future__ import annotations

import hashlib
import subprocess

from .model import context
from .reading import reading, render_reading
from .store import digest


DIMENSIONS = ("scope", "roles", "objects", "workflow", "exceptions", "dependencies")
LABELS = dict(zip(DIMENSIONS, ("职责与范围", "角色权限", "对象与术语", "主流程与状态", "约束与异常", "外部依赖")))


def inventory(service, *, mode="audit", scope="", module="", source_paths=None, coverage=None) -> dict:
    if mode not in {"initialize", "audit", "repair"}:
        raise ValueError("invalid_baseline_mode")
    snapshot = service.read()
    view = reading(snapshot, scope, module)
    current = context(snapshot, scope, module)
    source_paths = source_paths or []
    if not isinstance(source_paths, list) or len(source_paths) > 200 or len(set(source_paths)) != len(source_paths):
        raise ValueError("invalid_baseline_sources")
    files = []
    for relative in source_paths:
        path = service.capture.safe_path(service.root, relative)
        if path.stat().st_size > 2_000_000:
            raise ValueError("baseline_source_too_large")
        files.append({"path": relative, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    files.sort(key=lambda f: f["path"])
    try:
        code_ref = subprocess.run(["git", "rev-parse", "HEAD"], cwd=service.root, capture_output=True,
                                  text=True, timeout=3, check=True).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        code_ref = "unversioned"
    all_questions = [q for q in snapshot["questions"] if (not scope or q["scope"] in {"project", scope}) and
                     (not module or any(not r.get("modules") or module in r["modules"] for r in q["history"]))]
    mappings = [{"question_key": q["question_key"], "scope": q["scope"], "question": q["question"],
                 "old_refs": [r["id"] for r in q["history"]], "current_refs": [r["id"] for r in q["current"]],
                 "target_key": q["question_key"], "target_scope": q["scope"], "action": "retain",
                 "status": q["status"], "reason": "保留主题身份、原文、历史和确认；语义整理须另行预览确认。"} for q in all_questions]
    modules = sorted({m for c in view["chapters"] for q in c["questions"] for m in q["modules"]}) or [module or "project"]
    # The module manifest adds genuinely uncovered modules; answer count alone
    # never proves that roles, exceptions, or external dependencies were audited.
    manifest = service.capture.safe_path(service.root, ".maw/modules.yaml", must_exist=False)
    if manifest.is_file() and manifest.stat().st_size <= 2_000_000:
        import yaml
        try:
            entries = (yaml.safe_load(manifest.read_text()) or {}).get("modules", [])
            if not isinstance(entries, list):
                raise ValueError("invalid_module_manifest")
        except (OSError, ValueError, TypeError, AttributeError, yaml.YAMLError):
            raise ValueError("baseline_module_manifest_invalid") from None
        modules = sorted(set(modules) | {i["key"] for i in entries if isinstance(i, dict) and i.get("key") and
                                        (not module or i["key"] == module) and i.get("lifecycle", "active") != "deprecated"})
    asserted = {}
    if not isinstance(coverage or [], list) or len(coverage or []) > 200:
        raise ValueError("invalid_baseline_coverage")
    refs = set(current["question_refs"])
    for row in coverage or []:
        service.capture.only_keys(row, {"module", "dimension", "status", "question_refs", "reason"}, "coverage")
        identity = (row.get("module"), row.get("dimension"))
        if identity in asserted or identity[0] not in modules or identity[1] not in DIMENSIONS:
            raise ValueError("invalid_baseline_coverage_identity")
        if row.get("status") not in {"covered", "gap", "excluded"}:
            raise ValueError("invalid_baseline_coverage_status")
        selected = service.capture._strings(row.get("question_refs", []), "coverage_question_refs", count=100, limit=240)
        if not set(selected).issubset(refs) or (row["status"] == "covered" and not selected):
            raise ValueError("baseline_coverage_requires_confirmed_refs")
        asserted[identity] = {**row, "question_refs": selected, "reason": service.capture.text(row.get("reason"), 1000, "coverage_reason")}
    matrix = [asserted.get((m, dimension), {"module": m, "dimension": dimension, "status": "gap", "question_refs": [],
              "reason": "尚未明确核验此项覆盖，不能从主题数量推定完整。"}) for m in modules for dimension in DIMENSIONS]
    gaps = [f"{row['module']}：{LABELS[row['dimension']]}：{row['reason']}" for row in matrix if row["status"] == "gap"]
    gaps += [f"{q['question']}：{q['status']}" for q in all_questions if q["status"] not in {"current", "retired", "superseded", "rejected"}]
    gaps += [f"{b['question']}：{b['reason']}" for b in current["blockers"] if b["reason"] != "context_scope_too_broad"]
    gaps += [f"待回应：{p['question']}" for p in current["pending_decisions"]]
    gaps += [f"来源问题：{i['path']}：{i['reason']}" for i in snapshot["issues"]]
    if not all_questions:
        gaps.append("当前范围尚无项目口径，全面初始化未完成。")
    if len(refs) > 1000:
        gaps.append("范围超过基线引用上限，须分范围形成基线。")
    inputs = {"project_key": service.project_key, "scope": scope, "module": module, "questions": [
        {"ref": q["ref"], "source_hash": q["source_hash"]} for q in current["questions"]],
        "sources": files, "code_ref": code_ref, "coverage": matrix, "migration": mappings}
    return {"schema": "mawflow.governance_baseline_report.v1", "mode": mode, **inputs, "input_hash": digest(inputs),
            "source_version": snapshot["source_version"], "question_refs": sorted(refs), "coverage": matrix,
            "migration": mappings, "total_topics": len(all_questions), "gaps": gaps, "complete": not gaps,
            "reading": view, "reading_markdown": render_reading(view),
            "trust_boundary": {"project_mutated": False, "coverage_is_ai_reported": True, "code_worktree_fully_hashed": False,
                               "human_confirmation_claimed": False, "mode_does_not_grant_write_authority": True}}


def prepare(service, payload, snapshot, item, event_id):
    if payload.get("mode") == "audit":
        raise ValueError("baseline_audit_is_read_only")
    report = inventory(service, mode=payload.get("mode", "initialize"), scope=payload.get("scope", ""),
                       module=payload.get("module", ""), source_paths=payload.get("source_paths", []), coverage=payload.get("coverage", []))
    status = payload.get("baseline_status", "candidate")
    if status == "frozen" and (not report["complete"] or payload.get("source_kind") != "user_statement"):
        raise ValueError("baseline_confirmation_or_coverage_required")
    previous = payload.get("previous_ref", "")
    if previous and not any(i["id"] == previous and i.get("baseline") for i in snapshot["items"]):
        raise ValueError("baseline_previous_missing")
    relative = f"docs/deliverables/governance-baseline/{event_id}.md"
    lines = ["# 项目口径基线治理报告", "", f"项目：{service.project_key}；模式：{report['mode']}；状态：{status}。", "",
             f"完整盘点{report['total_topics']}个主题；按以下逐项映射保留身份及历史。", "", "## 覆盖与未解决项", ""]
    for row in report["coverage"]:
        lines += [f"- {row['module']} · {LABELS[row['dimension']]} · {row['status']}：{row['reason']}"]
    lines += ["", *[f"- 缺口：{gap}" for gap in report["gaps"]], "", "## 迁移对照", ""]
    for row in report["migration"]:
        lines += [f"- {row['question']}（{row['question_key']} / {row['scope']}）：{row['action']}；{row['reason']}",
                  *[f"  - 历史引用：`{ref}`" for ref in row["old_refs"]]]
    lines += ["", "## 固定阅读预览", "", report["reading_markdown"], "", "## 输入依据", "",
              f"代码提交：`{report['code_ref']}`；只对显式来源核验文件hash，不宣称全工作区已干净。", "",
              f"输入hash：`{report['input_hash']}`", *[f"- `{f['path']}` · `{f['sha256']}`" for f in report["sources"]], ""]
    content = "\n".join(lines).encode()
    if len(content) > 262144:
        raise ValueError("baseline_report_too_large")
    item.update(statement=f"项目口径基线形成{status}快照；完整盘点{report['total_topics']}个主题，{len(report['gaps'])}项缺口。",
        evidence=[{"path": relative, "kind": "document"}],
        baseline={"mode": report["mode"], "scope": report["scope"], "module": report["module"],
            "input_hash": report["input_hash"], "question_refs": report["question_refs"],
            "source_refs": [f"{f['path']}@{f['sha256']}" for f in report["sources"]], "code_ref": report["code_ref"],
            "coverage": [f"{r['module']}:{r['dimension']}:{r['status']}" for r in report["coverage"]],
            "gaps": report["gaps"], "status": status, "previous_ref": previous, "report_path": relative})
    return [item], {relative: content}
