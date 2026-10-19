"""Opt-in evidence provenance, with explicit reuse rather than implicit replay."""
from __future__ import annotations

from datetime import datetime
import re
from typing import Any

SCHEMA = "mawflow.task_evidence_policy.v1"
SHA256 = re.compile(r"sha256:[0-9a-f]{64}")


def nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def timestamp(value: Any) -> bool:
    try:
        return isinstance(value, str) and datetime.fromisoformat(value).utcoffset() is not None
    except (ValueError, TypeError):
        return False


def candidate_valid(value: Any, revision: str) -> bool:
    if not isinstance(value, dict) or set(value) != {"kind", "value"}:
        return False
    if value.get("kind") == "commit":
        return value.get("value") == revision and bool(re.fullmatch(r"[0-9a-f]{40}", str(revision)))
    return value.get("kind") in {"working_tree", "artifact"} and bool(SHA256.fullmatch(str(value.get("value", ""))))


def policy_issues(task: dict) -> list[str]:
    if "evidence_policy" not in task:
        return []
    policy = task["evidence_policy"]
    if not isinstance(policy, dict) or policy.get("schema") != SCHEMA or not nonempty(policy.get("run_ref")):
        return ["evidence_policy_invalid"]
    lifecycle = task.get("lifecycle")
    if isinstance(lifecycle, dict) and policy["run_ref"] != lifecycle.get("run_ref"):
        return ["evidence_policy_run_mismatch"]
    scope = task.get("scope")
    if not isinstance(scope, dict) or not candidate_valid(scope.get("candidate"), scope.get("source_revision", "")):
        return ["evidence_candidate_missing_or_invalid"]
    return []


def evidence_issues(task: dict, item: dict) -> list[str]:
    if "evidence_policy" not in task:
        return []
    policy = task["evidence_policy"]
    if policy_issues(task):
        return ["evidence_policy_invalid"]
    issues = []
    scope = task.get("scope", {})
    candidate = scope.get("candidate")
    if not candidate_valid(candidate, scope.get("source_revision", "")):
        issues.append("evidence_candidate_missing_or_invalid")
    elif item.get("candidate") != candidate:
        issues.append("evidence_candidate_stale")
    if not nonempty(item.get("method")) or not timestamp(item.get("observed_at")):
        issues.append("evidence_method_or_time_missing")
    if item.get("task_ref") != task.get("task_ref") or not nonempty(item.get("run_ref")):
        issues.append("evidence_task_or_run_mismatch")
    lifecycle = task.get("lifecycle")
    if isinstance(lifecycle, dict) and (type(item.get("scope_revision")) is not int
                                      or item.get("scope_revision") != lifecycle.get("scope_revision")):
        issues.append("evidence_scope_revision_stale")
    if item.get("run_ref") != policy["run_ref"]:
        reuse = item.get("reuse")
        if (not isinstance(reuse, dict) or reuse.get("from_run_ref") != item.get("run_ref")
                or reuse.get("to_run_ref") != policy["run_ref"]
                or not all(nonempty(reuse.get(field)) for field in ("reason", "record_ref"))
                or not timestamp(reuse.get("checked_at"))):
            issues.append("evidence_reuse_basis_missing")
        elif timestamp(item.get("observed_at")) and datetime.fromisoformat(reuse["checked_at"]) < datetime.fromisoformat(item["observed_at"]):
            issues.append("evidence_reuse_precedes_observation")
    elif "reuse" in item:
        issues.append("evidence_reuse_same_run")
    return issues
