"""Scoped recall and reuse evidence over the existing confirmed question versions."""
from __future__ import annotations

import re
import unicodedata

from .store import digest


def normalize_query(capture, value: dict) -> dict:
    capture.only_keys(value, {"utterance", "scope", "module", "environment", "limit"}, "recall_query")
    limit = value.get("limit", 5)
    if type(limit) is not int or not 1 <= limit <= 20:
        raise ValueError("invalid_recall_limit")
    result = {"utterance": capture.text(value.get("utterance"), 1200, "recall_utterance"), "limit": limit}
    for key in ("scope", "module", "environment"):
        result[key] = capture.slug(value[key], "recall_" + key) if value.get(key) else ""
    return result


def _normalized(value: str) -> str:
    return re.sub(r"[\W_]+", "", unicodedata.normalize("NFKC", value).casefold())


def _score(query: str, expression: str) -> float:
    query, expression = _normalized(query), _normalized(expression)
    if not query or not expression:
        return 0.0
    if expression in query:
        return 1.0
    if query in expression and len(query) >= 3:
        return 0.8
    left = {query[i:i + 2] for i in range(len(query) - 1)}
    right = {expression[i:i + 2] for i in range(len(expression) - 1)}
    return len(left & right) / max(1, len(left | right))


def recall(service, *, utterance: str, scope: str = "", module: str = "", environment: str = "", limit: int = 5) -> dict:
    query = normalize_query(service.capture, dict(utterance=utterance, scope=scope, module=module, environment=environment, limit=limit))
    snapshot = service.read()
    matches, excluded = [], []
    corrections = set()
    by_id = {item["id"]: item for item in snapshot["items"]}
    for item in snapshot["items"]:
        feedback = item.get("learning", {})
        if feedback.get("kind") == "feedback" and feedback["outcome"] == "corrected":
            reuse = by_id.get(feedback["reuse_ref"], {}).get("learning", {})
            corrections.update(reuse.get("rule_refs", []))
    for question in snapshot["questions"]:
        if question["scope"] != "project" and question["scope"] != scope:
            continue
        for item in question["current"]:
            rule = item.get("learning", {})
            if rule.get("kind") != "rule" or (item.get("modules") and module not in item["modules"]):
                continue
            if rule["environments"] and environment not in rule["environments"]:
                continue
            if any(_normalized(negative) in _normalized(utterance) for negative in rule["negative_examples"]):
                continue
            score = max(_score(utterance, expression) for expression in rule["utterances"])
            if score < 0.15:
                continue
            if item["business_status"] != "current":
                excluded.append({"ref": item["id"], "reason": item["business_status"]})
                continue
            matches.append({"ref": item["id"], "source_hash": item["source_hash"], "question": question["question"],
                "answer": item["statement"], "scope": question["scope"], "modules": item.get("modules", []),
                "learning": rule, "score": round(score, 4), "review_required": item["id"] in corrections,
                "confirmation": item.get("confirmation"), "evidence_freshness": item["freshness"]})
    matches.sort(key=lambda item: (-item["score"], item["ref"]))
    truncated = len(matches) > limit
    selected = matches[:limit]
    modes = {item["learning"]["operation_mode"] for item in selected}
    complete = not snapshot["partial"] and not excluded and not truncated
    status = ("clarification_required" if len(modes) > 1 or any(item["review_required"] for item in selected) or not complete
              else "matched" if selected else "no_match")
    body = {"project_key": service.project_key, "query": query, "source_version": snapshot["source_version"],
        "matches": selected, "excluded": excluded, "total_matches": len(matches), "truncated": truncated,
        "issues": snapshot["issues"], "complete": complete, "status": status}
    return {"schema": "mawflow.language_recall.v1", **body, "recall_hash": digest(body),
        "rule_refs": [item["ref"] for item in selected],
        "instructions": "先阅读当前口径，再用这些案例辅助理解；候选、相似度和历史成功不授予执行权限。仅词面召回，未命中不证明无相关经验；AI可改写检索或按范围阅读全文。理解有歧义只等待依赖动作。",
        "trust_boundary": {"project_mutated": False, "authorization_granted": False, "semantic_judgment": "agent_required"}}


def prepare_reuse(service, payload, snapshot, item):
    query = normalize_query(service.capture, payload.get("recall_query"))
    current = recall(service, **query)
    refs = payload.get("rule_refs")
    consumption = item["consumption"]
    if (query["scope"], query["module"]) != (consumption["context_scope"], consumption["context_module"]):
        raise ValueError("learning_consumption_scope_mismatch")
    if (not current["complete"] or current["status"] != "matched" or
            payload.get("recall_hash") != current["recall_hash"] or refs != current["rule_refs"] or
            not set(refs or []).issubset(consumption["question_refs"])):
        raise ValueError("learning_recall_changed_or_ambiguous")
    if not refs:
        raise ValueError("learning_reuse_requires_rules")
    item["learning"] = {"kind": "reuse", "query": query, "recall_hash": current["recall_hash"], "rule_refs": refs}


def prepare_feedback(service, payload, snapshot, item):
    previous = next((row for row in snapshot["items"] if row["id"] == payload.get("reuse_ref")), None)
    if previous is None or previous.get("learning", {}).get("kind") != "reuse":
        raise ValueError("learning_reuse_missing")
    activity = previous.get("activity", {})
    if (activity.get("task_ref"), activity.get("session_ref")) != (payload.get("task_ref"), payload.get("run_ref")):
        raise ValueError("learning_feedback_run_mismatch")
    item["learning"] = {"kind": "feedback", "reuse_ref": previous["id"], "outcome": payload.get("outcome"),
        "reason": payload.get("rationale")}
    item.update(kind="implementation", statement=payload.get("result"),
        activity={"task_ref": payload.get("task_ref"), "session_ref": payload.get("run_ref"), "phase": "progress",
            "goal": payload.get("goal", "核对本次自然语言理解与经验复用结果"),
            "actions": payload.get("actions", ["核对用户反馈与实际验证"]),
            "result": payload.get("result"), "validation": payload.get("validation")})


def report(service) -> dict:
    snapshot = service.read()
    reuses = [item for item in snapshot["items"] if item.get("learning", {}).get("kind") == "reuse"]
    feedback = [item for item in snapshot["items"] if item.get("learning", {}).get("kind") == "feedback"]
    return {"schema": "mawflow.language_learning_report.v1", "project_key": service.project_key,
        "reuse_count": len(reuses), "feedback_count": len(feedback),
        "outcomes": {state: sum(item["learning"]["outcome"] == state for item in feedback)
                     for state in ("useful", "corrected", "inapplicable", "unknown")},
        "reuses": [{"ref": item["id"], "task_ref": item["activity"]["task_ref"],
                    "run_ref": item["activity"]["session_ref"], "rule_refs": item["learning"]["rule_refs"]} for item in reuses],
        "trust_boundary": {"outcomes_are_recorded_claims": True, "human_acceptance_inferred": False, "project_mutated": False}}
