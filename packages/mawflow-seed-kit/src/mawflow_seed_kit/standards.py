"""Read stage standards and validate scoped task declarations; never execute them."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import tempfile
from typing import Any

import yaml

PHASES = ("initiation", "design", "development", "testing", "deployment", "delivery")
CLASSES = ("small_change", "iteration", "formal_delivery")
KINDS = ("read_only", "modify", "test", "deploy", "deliver")
AXES = ("implementation", "verification", "external_integration", "delivery",
        "deployment", "human_acceptance")
STATES = {"pending", "partial", "passed", "failed", "not_applicable"}
BLOCKED = {".git", ".local", ".ssh", "prompts", "archive", "runtime", "workspaces",
           "artifacts", "payload", "node_modules"}
CATALOG = ".maw/standards.yaml"
INDEX = "docs/standards/index.md"
SNAPSHOT = ".maw/generated/standards-index.json"
MAX_BYTES = 512 * 1024
KEY = re.compile(r"^[a-z][a-z0-9._-]{0,119}$")


def digest(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def safe_path(root: Path, ref: str) -> Path:
    if not isinstance(ref, str):
        raise ValueError("reference_invalid")
    parts = PurePosixPath(ref).parts
    if (not parts or PurePosixPath(ref).is_absolute() or "\\" in ref or ":" in ref
            or ".." in parts or any(part in BLOCKED for part in parts)
            or any(part.startswith(("secrets.", ".env")) or ".local." in part
                   or part.lower().endswith((".pem", ".key", ".p12", ".pfx")) for part in parts)):
        raise ValueError("reference_forbidden")
    path = root
    for part in parts:
        path = path / part
        if path.is_symlink():
            raise ValueError("symlink_forbidden")
    path.resolve().relative_to(root)
    return path


def read_mapping(root: Path, ref: str) -> dict[str, Any]:
    path = safe_path(root, ref)
    if path.stat().st_size > MAX_BYTES:
        raise ValueError("source_budget_exceeded")
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("mapping_required")
    return value


def string_list(value: Any, allowed: set[str] | None = None) -> bool:
    return (isinstance(value, list) and bool(value)
            and all(isinstance(item, str) and item for item in value)
            and len(value) == len(set(value))
            and (allowed is None or set(value) <= allowed))


def inspect_catalog(root: Path) -> dict[str, Any]:
    """Validate only explicit catalog references, without reading their bodies."""
    if not safe_path(root, CATALOG).exists():
        return {"status": "not_adopted", "rules": [], "issues": [],
                "summary": "项目尚未采用阶段规范目录；不阻断既有开发。"}
    data = read_mapping(root, CATALOG)
    issues: list[str] = []
    if data.get("schema") != "mawflow.standards_catalog.v1":
        issues.append("catalog_schema_invalid")
    phases = data.get("phases", [])
    if not isinstance(phases, list) or [p.get("key") for p in phases if isinstance(p, dict)] != list(PHASES):
        issues.append("phase_set_invalid")
    for phase in phases if isinstance(phases, list) else []:
        if not isinstance(phase, dict):
            issues.append("phase_invalid")
            continue
        ref = phase.get("guide")
        if not safe_path(root, ref).is_file():
            issues.append("phase_guide_missing:" + str(phase.get("key")))
    rules = data.get("rules")
    if not isinstance(rules, list) or not rules:
        issues.append("rules_missing")
        rules = []
    seen: set[str] = set()
    required = {"key", "title", "category", "primary_phase", "applies_to_phases",
                "task_classes", "task_kinds", "trigger", "authority", "owner",
                "requirement", "deliverables", "validation", "enforcement",
                "version", "exception_policy", "reuse_policy"}
    for rule in rules:
        if not isinstance(rule, dict):
            issues.append("rule_invalid")
            continue
        key = rule.get("key", "")
        if not isinstance(key, str) or not KEY.fullmatch(key) or key in seen:
            issues.append("rule_identity_invalid")
            continue
        seen.add(key)
        if not required <= rule.keys():
            issues.append("rule_fields_missing:" + key)
        for field in required - {"applies_to_phases", "task_classes", "task_kinds",
                                  "deliverables", "validation"}:
            if not isinstance(rule.get(field), str) or not rule[field].strip():
                issues.append("rule_field_invalid:" + key + ":" + field)
        if rule.get("category") not in {"common", "stage", "project", "resource"}:
            issues.append("category_invalid:" + key)
        if rule.get("primary_phase") not in PHASES:
            issues.append("primary_phase_invalid:" + key)
        for field, allowed in (("applies_to_phases", set(PHASES)),
                               ("task_classes", set(CLASSES)), ("task_kinds", set(KINDS))):
            if not string_list(rule.get(field), allowed):
                issues.append("rule_selection_invalid:" + key + ":" + field)
        for field in ("deliverables", "validation"):
            if not string_list(rule.get(field)):
                issues.append("rule_outputs_invalid:" + key)
        if rule.get("requirement") not in {"required", "conditional", "recommended"}:
            issues.append("requirement_invalid:" + key)
        if rule.get("enforcement") not in {"documented", "manual", "script"}:
            issues.append("enforcement_invalid:" + key)
        authority = rule.get("authority", "")
        if isinstance(authority, str) and authority and not safe_path(root, authority).is_file():
            issues.append("authority_missing:" + key)
    return {"schema": "mawflow.standards_inspection.v1",
            "status": "blocked" if issues else "ready", "issues": sorted(set(issues)),
            "rules": rules, "phases": phases,
            "source_hash": digest(safe_path(root, CATALOG).read_bytes()),
            "summary": "规范目录有缺口。" if issues else "阶段规范目录及显式权威引用完整。"}


def context(root: Path, phase: str, task_class: str, task_kind: str) -> dict[str, Any]:
    report = inspect_catalog(root)
    if report["status"] != "ready":
        return report
    selected = [r for r in report["rules"]
                if (not phase or phase in r["applies_to_phases"])
                and task_class in r["task_classes"] and task_kind in r["task_kinds"]]
    return {**report, "rules": selected, "phase": phase, "task_class": task_class,
            "task_kind": task_kind, "authorization_granted": False,
            "summary": "已选择适用规范；仍须核对触发条件、项目规则及已有授权。"}


def render_blobs(root: Path) -> dict[str, bytes]:
    report = inspect_catalog(root)
    if report["status"] != "ready":
        raise ValueError("catalog_not_ready")
    lines = ["# 阶段规范索引", "", "本页由 .maw/standards.yaml 生成；规则正文与项目事实仍由各自权威文件维护。",
             "", "按任务范围选择规范。阶段导航不授予写入、测试、部署或对外共享权限。", ""]
    for phase in report["phases"]:
        lines += ["## " + phase["title"], "", "[阶段清单](" + Path(phase["guide"]).name + ")", "",
                  "| 规范 | 类型 | 条件 | 执行方式 | 权威来源 |",
                  "| --- | --- | --- | --- | --- |"]
        for rule in report["rules"]:
            if phase["key"] not in rule["applies_to_phases"]:
                continue
            values = [rule["title"], rule["category"], rule["trigger"], rule["enforcement"]]
            values = [v.replace("|", "\\|").replace("\n", " ") for v in values]
            ref = os.path.relpath(rule["authority"], "docs/standards").replace("\\", "/")
            lines.append("| " + " | ".join(values) + " | [" + rule["key"] + "](" + ref + ") |")
        lines.append("")
    snapshot = {k: report[k] for k in ("schema", "source_hash", "phases", "rules")}
    return {INDEX: ("\n".join(lines).rstrip() + "\n").encode(),
            SNAPSHOT: (json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n").encode()}


def render(root: Path, execute: bool = False, fingerprint: str = "") -> dict[str, Any]:
    blobs = render_blobs(root)
    targets = {ref: safe_path(root, ref) for ref in blobs}
    old = {ref: path.read_bytes() if path.exists() else None for ref, path in targets.items()}
    binding = json.dumps({ref: [digest(blobs[ref]), digest(old[ref]) if old[ref] is not None else None]
                          for ref in sorted(blobs)}, sort_keys=True).encode()
    expected = digest(binding)
    pending = [ref for ref in blobs if old[ref] != blobs[ref]]
    if execute:
        if fingerprint != expected:
            raise ValueError("stale_preview_fingerprint")
        written: list[str] = []
        try:
            for ref in pending:
                path = targets[ref]
                path.parent.mkdir(parents=True, exist_ok=True)
                with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as out:
                    out.write(blobs[ref])
                    temporary = Path(out.name)
                os.replace(temporary, path)
                written.append(ref)
        except Exception:
            for ref in written:
                if old[ref] is None:
                    targets[ref].unlink()
                else:
                    targets[ref].write_bytes(old[ref])
            raise
    return {"status": "ready" if execute else "planned", "fingerprint": expected,
            "changed_paths": pending if execute else [], "proposed_paths": pending,
            "summary": "规范索引已生成。" if execute else "只读预览；索引可由权威目录重建。"}


def validate_task(root: Path, ref: str) -> dict[str, Any]:
    task = read_mapping(root, ref)
    issues: list[str] = []
    warnings = ["只核验声明、引用与哈希；不证明实际授权、测试活动、发布或真人验收。"]
    required = {"schema", "task_ref", "phase", "task_class", "task_kind", "scope",
                "authorization", "states", "verification", "evidence"}
    if not required <= task.keys() or task.get("schema") != "mawflow.standard_task_snapshot.v1":
        issues.append("task_schema_invalid")
    if (task.get("phase") not in PHASES or task.get("task_class") not in CLASSES
            or task.get("task_kind") not in KINDS or not task.get("task_ref")):
        issues.append("task_selection_invalid")
    scope = task.get("scope") or {}
    if not isinstance(scope, dict):
        scope = {}
        issues.append("scope_invalid")
    for field in ("source_revision", "environment", "module_keys", "read_paths", "write_paths",
                  "blocked_paths", "target_baseline"):
        if field not in scope:
            issues.append("scope_field_missing:" + field)
    if not re.fullmatch(r"[0-9a-f]{40}", str(scope.get("source_revision", ""))):
        issues.append("source_revision_invalid")
    if not isinstance(scope.get("environment"), str) or not scope["environment"].strip():
        issues.append("environment_invalid")
    if not isinstance(scope.get("module_keys"), list):
        issues.append("modules_invalid")
    for field in ("read_paths", "write_paths", "blocked_paths"):
        if not isinstance(scope.get(field), list):
            issues.append("scope_paths_invalid:" + field)
            continue
        for path in scope[field]:
            safe_path(root, path)
    writes, blocked = [scope.get(f, []) for f in ("write_paths", "blocked_paths")]
    if any(w == b or w.startswith(b.rstrip("/") + "/") for w in writes for b in blocked):
        issues.append("write_path_blocked")
    authorization = task.get("authorization") or {}
    if not isinstance(authorization, dict):
        authorization = {}
    if (authorization.get("mode") not in {"read_only", "modify"}
            or not authorization.get("source_ref") or not authorization.get("scope_ref")):
        issues.append("authorization_declaration_missing")
    if (authorization.get("mode") == "read_only" or task.get("task_kind") == "read_only") and writes:
        issues.append("read_only_has_write_paths")
    actions = authorization.get("allowed_actions", [])
    if task.get("task_kind") in {"deploy", "deliver"} and task["task_kind"] not in actions:
        issues.append("operation_outside_declared_authorization")
    if task.get("task_kind") in {"deploy", "deliver"} and authorization.get("mode") != "modify":
        issues.append("external_operation_requires_modify_declaration")
    if scope.get("environment") not in authorization.get("environments", []):
        issues.append("environment_outside_declared_authorization")
    scope_hash = digest(json.dumps(scope, sort_keys=True, ensure_ascii=False).encode())
    evidence = task.get("evidence")
    if not isinstance(evidence, list):
        evidence = []
        issues.append("evidence_invalid")
    keys: set[str] = set()
    valid: set[str] = set()
    verification_evidence: set[str] = set()
    axes_with_evidence: set[str] = set()
    for item in evidence:
        if not isinstance(item, dict):
            issues.append("evidence_item_invalid")
            continue
        key = item.get("key")
        if not isinstance(key, str) or not KEY.fullmatch(key) or key in keys:
            issues.append("evidence_identity_invalid")
            continue
        keys.add(key)
        axis = item.get("axis")
        if axis not in AXES or item.get("status") not in STATES:
            issues.append("evidence_state_invalid:" + key)
            continue
        if item.get("status") != "passed":
            continue
        path = safe_path(root, item.get("path", ""))
        if not path.is_file() or path.stat().st_size > MAX_BYTES:
            issues.append("evidence_missing_or_large:" + key)
            continue
        if digest(path.read_bytes()) != item.get("content_hash"):
            issues.append("evidence_changed:" + key)
            continue
        if (item.get("source_revision") != scope.get("source_revision")
                or item.get("environment") != scope.get("environment")
                or item.get("scope_hash") != scope_hash):
            issues.append("evidence_scope_stale:" + key)
            continue
        if not item.get("record_ref"):
            issues.append("evidence_record_ref_missing:" + key)
            continue
        if axis == "human_acceptance" and (not item.get("actor") or not item.get("confirmation_ref")):
            issues.append("human_confirmation_missing:" + key)
            continue
        valid.add(key)
        axes_with_evidence.add(axis)
        if axis == "verification":
            verification_evidence.add(key)
    states = task.get("states") or {}
    if not isinstance(states, dict):
        states = {}
    for axis in AXES:
        if states.get(axis) not in STATES:
            issues.append("axis_state_invalid:" + axis)
        elif states[axis] == "passed" and axis not in axes_with_evidence:
            issues.append("axis_evidence_missing:" + axis)
    verification = task.get("verification") or {}
    if not isinstance(verification, dict):
        verification = {}
    suites = verification.get("suites", [])
    if not isinstance(suites, list):
        suites = []
        issues.append("suite_list_invalid")
    if states.get("verification") == "passed" and not suites:
        issues.append("empty_suites_are_not_passed")
    suite_keys: set[str] = set()
    for suite in suites:
        if (not isinstance(suite, dict) or not suite.get("key")
                or suite["key"] in suite_keys or suite.get("status") not in STATES):
            issues.append("suite_invalid")
            continue
        suite_keys.add(suite["key"])
        if suite["status"] == "passed" and (not suite.get("evidence_refs")
                or not set(suite["evidence_refs"]) <= verification_evidence):
            issues.append("suite_evidence_missing")
    if states.get("verification") == "passed" and any(s["status"] != "passed" for s in suites if isinstance(s, dict)):
        issues.append("verification_overstates_suites")
    return {"schema": "mawflow.standard_task_validation.v1",
            "status": "blocked" if issues else "declaration_validated",
            "issues": sorted(set(issues)), "warnings": warnings, "scope_hash": scope_hash,
            "valid_evidence_keys": sorted(valid), "authorization_granted": False,
            "summary": "任务声明有缺口。" if issues else "任务声明一致；实际完成仍以原任务、测试及发布回执为准。"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="六阶段规范导航、索引检查与任务声明核验")
    parser.add_argument("command", choices=["check", "context", "render", "validate-task"])
    parser.add_argument("--root", default=".")
    parser.add_argument("--phase", choices=PHASES, default="")
    parser.add_argument("--task-class", choices=CLASSES, default="small_change")
    parser.add_argument("--task-kind", choices=KINDS, default="modify")
    parser.add_argument("--input", default="")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--expected-fingerprint", default="")
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    args = parser.parse_args(argv)
    try:
        root = Path(args.root).resolve(strict=True)
        if args.execute and args.command != "render":
            raise ValueError("execute_only_for_render")
        if args.command == "context":
            result = context(root, args.phase, args.task_class, args.task_kind)
        elif args.command == "render":
            result = render(root, args.execute, args.expected_fingerprint)
        elif args.command == "validate-task":
            result = validate_task(root, args.input)
        else:
            result = inspect_catalog(root)
            if result["status"] == "ready":
                missing = render(root)["proposed_paths"]
                result["index_drift"] = missing
                if missing:
                    result.update(status="blocked", summary="生成索引与权威目录不一致。")
        if args.format == "markdown":
            print("# " + result["summary"])
            for rule in result.get("rules", []):
                print("- " + rule["title"] + "：" + rule["authority"] + "（" + rule["enforcement"] + "）")
            for issue in result.get("issues", []):
                print("- " + issue)
        else:
            result.setdefault("next_action", "ai_takeover" if result["status"] == "blocked" else "continue")
            result.setdefault("changed_paths", [])
            result.setdefault("evidence_refs", [])
            result.setdefault("log_path", "")
            result.setdefault("state_path", "")
            result.setdefault("environment", {"os": platform.system().lower(), "python": platform.python_version(), "workspace": "project_root"})
            print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1 if result["status"] == "blocked" else 0
    except (ValueError, TypeError, KeyError, OSError, yaml.YAMLError) as exc:
        # Do not echo YAML, user input, local paths, or arbitrary exception text.
        reason = str(exc) if isinstance(exc, ValueError) and KEY.fullmatch(str(exc)) else "invalid_input"
        print(json.dumps({"status": "blocked", "issues": [reason], "changed_paths": [],
                          "authorization_granted": False}, ensure_ascii=False))
        return 1
