"""Bind a task to selected authorities; projections never advance a task ledger."""
from __future__ import annotations

import copy
import json
from typing import Any

from .standard_evidence import nonempty

SCHEMA = "mawflow.standards_binding.v1"


def rule_fingerprint(root, rule, safe_path, digest) -> str:
    path = safe_path(root, rule["authority"])
    if path.stat().st_size > 512 * 1024:
        raise ValueError("authority_budget_exceeded")
    declaration = {key: value for key, value in rule.items() if key != "selection"}
    return digest(json.dumps({"rule": declaration, "authority_hash": digest(path.read_bytes())},
                             sort_keys=True, ensure_ascii=False).encode())


def plan_binding(root, task: dict, selection: dict, safe_path, digest) -> dict:
    if selection["status"] != "ready":
        return selection
    planned = copy.deepcopy(task)
    planned["standards_binding"] = {
        "schema": SCHEMA, "catalog_hash": selection["source_hash"],
        "selection": {key: selection[key] for key in ("phase", "task_class", "task_kind", "facts")},
        "rules": [{"key": rule["key"], "version": rule["version"],
                   "fingerprint": rule_fingerprint(root, rule, safe_path, digest),
                   "decision": "pending" if rule["selection"]["status"] == "pending_applicability" else "applicable",
                   "reason": rule["selection"]["reason"], "record_ref": "", "evidence_refs": []}
                  for rule in selection["rules"]],
    }
    # A plan is not an adoption decision, a write authorization, or a completed run.
    return {"status": "planned", "task": planned, "excluded_rules": selection["excluded_rules"],
            "changed_paths": [], "authorization_granted": False,
            "summary": "已生成规范引用预览；待判断条件与回执仍由当前任务补充，不写项目。"}


def validate_binding(root, task: dict, select, safe_path, digest, valid_evidence: set[str]) -> dict:
    if "standards_binding" not in task:
        return {"status": "not_adopted", "issues": [], "warnings": [], "rule_refs": []}
    binding = task["standards_binding"]
    if not isinstance(binding, dict) or binding.get("schema") != SCHEMA:
        return {"status": "blocked", "issues": ["standards_binding_invalid"], "warnings": [], "rule_refs": []}
    choice = binding.get("selection")
    issues, warnings = [], []
    if (not isinstance(choice, dict)
            or any(choice.get(key) != task.get(key) for key in ("phase", "task_class", "task_kind"))):
        return {"status": "blocked", "issues": ["standards_selection_stale"], "warnings": [], "rule_refs": []}
    selection = select(root, choice["phase"], choice["task_class"], choice["task_kind"], choice.get("facts", {}))
    if selection["status"] != "ready":
        return {"status": "blocked", "issues": ["standards_catalog_not_ready"], "warnings": [], "rule_refs": []}
    if not nonempty(binding.get("catalog_hash")):
        issues.append("standards_catalog_hash_missing")
    elif binding["catalog_hash"] != selection["source_hash"]:
        warnings.append("规范目录已变；逐条核对选中规则，未受影响的证据可继续复用。")
    expected = {rule["key"]: rule for rule in selection["rules"]}
    entries = binding.get("rules")
    if not isinstance(entries, list):
        entries = []
        issues.append("standards_rules_invalid")
    seen = set()
    lifecycle = task.get("lifecycle") or {}
    complete = isinstance(lifecycle, dict) and lifecycle.get("outcome") == "succeeded"
    refs = []
    for item in entries:
        if not isinstance(item, dict) or not isinstance(item.get("key"), str) or item["key"] in seen or item["key"] not in expected:
            issues.append("standards_rule_identity_invalid")
            continue
        key = item["key"]
        seen.add(key)
        rule = expected[key]
        if (item.get("version") != rule["version"]
                or item.get("fingerprint") != rule_fingerprint(root, rule, safe_path, digest)):
            issues.append("standards_rule_stale:" + key)
        decision = item.get("decision")
        if decision not in {"applicable", "not_applicable", "exception", "pending"}:
            issues.append("standards_decision_invalid:" + key)
        if decision in {"not_applicable", "exception"} and not nonempty(item.get("reason")):
            issues.append("standards_decision_reason_missing:" + key)
        if decision == "not_applicable" and rule["requirement"] == "required" and rule["selection"]["status"] == "applicable":
            issues.append("standards_required_rule_excluded:" + key)
        if decision == "exception" and not nonempty(item.get("authorization_ref")):
            issues.append("standards_exception_basis_missing:" + key)
        evidence = item.get("evidence_refs", [])
        if not isinstance(evidence, list) or any(not isinstance(ref, str) or ref not in valid_evidence for ref in evidence):
            issues.append("standards_rule_evidence_invalid:" + key)
        if complete and (decision == "pending" or (decision == "applicable" and not evidence and not nonempty(item.get("record_ref")))):
            issues.append("standards_rule_unresolved:" + key)
        refs.append({"key": key, "version": rule["version"], "authority": rule["authority"],
                     "decision": decision, "record_ref": item.get("record_ref", ""), "evidence_refs": evidence})
    if seen != set(expected):
        issues.append("standards_rule_set_incomplete")
    return {"status": "blocked" if issues else "declaration_validated", "issues": sorted(set(issues)),
            "warnings": warnings, "rule_refs": refs}


def task_projection(task: dict, report: dict) -> dict:
    """Reference-only view; no copied mutable outcomes or independent IDs."""
    lifecycle = task.get("lifecycle") or {}
    return {"schema": "mawflow.standard_task_projection.v1", "task_ref": task.get("task_ref"),
            "run_ref": lifecycle.get("run_ref") if isinstance(lifecycle, dict) else None,
            "validation": report["status"], "rules": report.get("rule_refs", []),
            "evidence_refs": report.get("valid_evidence_keys", []),
            "related_refs": task.get("related_refs", []), "writes_task_state": False}
