"""Version-four source data. These declarations never grant execution authority."""
from __future__ import annotations

import re


CATEGORIES = {"plans": "方案与决策", "requirements": "需求与业务", "design": "设计与技术",
              "acceptance": "测试与验收", "delivery": "发布与交付", "maintenance": "使用与维护",
              "reference": "参考资料", "unclassified": "待整理"}
ORIGINS = {"task_generated", "knowledge", "human_import", "existing", "delivery_generated"}
PROCESS_TYPES = {"understanding", "assumption", "finding", "decision", "adjustment", "verification",
                 "failure", "recovery", "outcome"}
CAPABILITIES = ["readable_governance.v1", "governance_revision_batch.v1", "governance_baseline.v1",
                "curated_archives.v1", "update_batches.v1", "release_version_binding.v1", "post_execution_review.v1",
                "natural_language_learning.v1"]


def normalize_learning(capture, item, activity):
    value = item.get("learning")
    if value is None:
        return None
    kind = value.get("kind") if isinstance(value, dict) else None
    if kind == "rule":
        capture.only_keys(value, {"kind", "utterances", "negative_examples", "intent", "operation_mode", "environments"}, "learning_rule")
        qa = item.get("qa", {})
        if (qa.get("category"), qa.get("claim_type")) != ("experience", "experience") or value.get("operation_mode") not in {"read_only", "modify"}:
            raise ValueError("invalid_learning_rule")
        expressions = capture._strings(value.get("utterances"), "learning_utterances", count=20, limit=400)
        if not expressions or len(expressions) != len(set(expressions)):
            raise ValueError("invalid_learning_utterances")
        return {"kind": kind, "utterances": expressions, "intent": capture.text(value.get("intent"), 1800, "learning_intent"),
            "operation_mode": value["operation_mode"],
            "negative_examples": capture._strings(value.get("negative_examples", []), "learning_negative_examples", count=12, limit=400),
            "environments": [capture.slug(env, "learning_environment") for env in capture._strings(value.get("environments", []), "learning_environments", count=12)]}
    if not activity:
        raise ValueError("learning_activity_required")
    if kind == "reuse":
        capture.only_keys(value, {"kind", "query", "recall_hash", "rule_refs"}, "learning_reuse")
        query = capture.only_keys(value.get("query"), {"utterance", "scope", "module", "environment", "limit"}, "learning_query")
        if type(query.get("limit")) is not int or not 1 <= query["limit"] <= 20:
            raise ValueError("invalid_learning_query")
        normalized = {"utterance": capture.text(query.get("utterance"), 1200, "learning_utterance"), "limit": query["limit"]}
        for key in ("scope", "module", "environment"):
            normalized[key] = capture.slug(query[key], "learning_" + key) if query.get(key) else ""
        if not re.fullmatch(r"[a-f0-9]{64}", str(value.get("recall_hash", ""))):
            raise ValueError("invalid_learning_recall_hash")
        refs = capture._strings(value.get("rule_refs"), "learning_rule_refs", count=20, limit=240)
        if not refs or len(refs) != len(set(refs)):
            raise ValueError("invalid_learning_rule_refs")
        return {"kind": kind, "query": normalized, "recall_hash": value["recall_hash"], "rule_refs": refs}
    if kind == "feedback":
        capture.only_keys(value, {"kind", "reuse_ref", "outcome", "reason"}, "learning_feedback")
        if value.get("outcome") not in {"useful", "corrected", "inapplicable", "unknown"}:
            raise ValueError("invalid_learning_outcome")
        return {"kind": kind, "reuse_ref": capture.text(value.get("reuse_ref"), 240, "learning_reuse_ref"),
            "outcome": value["outcome"], "reason": capture.text(value.get("reason"), 1800, "learning_reason")}
    raise ValueError("invalid_learning_kind")


def normalize_extensions(capture, item: dict, *, activity: dict | None) -> dict:
    result = {}
    learning = normalize_learning(capture, item, activity)
    if learning is not None:
        result["learning"] = learning
    organization = item.get("organization")
    if organization is not None:
        capture.only_keys(organization, {"question_key", "scope", "chapter", "order"}, "organization")
        order = organization.get("order", 0)
        if type(order) is not int or not 0 <= order <= 100000:
            raise ValueError("invalid_organization_order")
        result["organization"] = {"question_key": capture.slug(organization.get("question_key"), "question_key"),
            "scope": capture.slug(organization.get("scope"), "scope"),
            "chapter": capture.text(organization.get("chapter"), 180, "chapter"), "order": order}
    process = item.get("process")
    if process is not None:
        capture.only_keys(process, {"event_type", "reason", "assumptions", "alternatives", "previous_refs", "goal_snapshot", "action_state"}, "process")
        if not activity or process.get("event_type") not in PROCESS_TYPES:
            raise ValueError("invalid_process_event")
        result["process"] = {"event_type": process["event_type"],
            "reason": capture.text(process["reason"], 1800, "process_reason") if process.get("reason") else ""}
        if process.get("action_state", "unknown") not in {"planned", "performed", "passed", "failed", "unknown"}:
            raise ValueError("invalid_process_action_state")
        result["process"]["action_state"] = process.get("action_state", "unknown")
        for field in ("assumptions", "alternatives", "previous_refs"):
            result["process"][field] = capture._strings(process.get(field, []), field, count=20, limit=600)
        if process.get("goal_snapshot") is not None:
            goal = capture.only_keys(process["goal_snapshot"], {"goal", "scope", "constraints", "acceptance"}, "goal_snapshot")
            result["process"]["goal_snapshot"] = {field: capture.text(goal.get(field), 3000, "goal_" + field)
                                                      for field in ("goal", "scope", "constraints", "acceptance")}
    baseline = item.get("baseline")
    if baseline is not None:
        capture.only_keys(baseline, {"mode", "scope", "module", "input_hash", "question_refs", "source_refs",
                                    "code_ref", "coverage", "gaps", "status", "previous_ref", "report_path"}, "baseline")
        if baseline.get("mode") not in {"initialize", "audit", "repair"} or baseline.get("status") not in {"candidate", "frozen"}:
            raise ValueError("invalid_baseline_state")
        if not re.fullmatch(r"[a-f0-9]{64}", str(baseline.get("input_hash", ""))):
            raise ValueError("invalid_baseline_hash")
        result["baseline"] = {field: capture.text(baseline.get(field), 300, "baseline_" + field) if baseline.get(field) else ""
                               for field in ("scope", "module", "code_ref", "previous_ref", "report_path")}
        result["baseline"].update(mode=baseline["mode"], status=baseline["status"], input_hash=baseline["input_hash"])
        for field in ("question_refs", "source_refs"):
            result["baseline"][field] = capture._strings(baseline.get(field, []), field, count=1000, limit=300)
        for field in ("coverage", "gaps"):
            result["baseline"][field] = capture._strings(baseline.get(field, []), field, count=200, limit=1000)
        if baseline["status"] == "frozen" and baseline.get("gaps"):
            raise ValueError("baseline_with_gaps_cannot_complete")
    for name in ("release_binding", "update_batch"):
        value = item.get(name)
        if value is None:
            continue
        fields = ({"channel", "version", "candidate_hash", "manifest_path", "input_hash"} if name == "release_binding" else
                  {"batch_key", "revision", "version", "release_ref", "manifest_path", "markdown_path", "input_hash", "previous_ref"})
        capture.only_keys(value, fields, name)
        if not fields.issubset(value):
            raise ValueError("invalid_" + name)
        for field in fields - {"revision"}:
            if not isinstance(value[field], str) or len(value[field]) > 400 or (value[field] and capture.SENSITIVE.search(value[field])):
                raise ValueError("invalid_" + name + "_value")
        if not re.fullmatch(r"[a-f0-9]{64}", value["input_hash"]):
            raise ValueError("invalid_governance_manifest_hash")
        if (name == "release_binding" or value["version"]) and not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9._+-]{0,79}", value["version"]):
            raise ValueError("invalid_release_version")
        folder = "release-versions" if name == "release_binding" else "update-batches"
        if not re.fullmatch(r"\.maw/" + folder + r"/[a-z0-9._-]+\.json", value["manifest_path"]):
            raise ValueError("invalid_governance_manifest_path")
        paths = [value["manifest_path"]]
        if name == "release_binding":
            capture.slug(value["channel"], "release_channel")
            if not re.fullmatch(r"[a-f0-9]{64}", value["candidate_hash"]):
                raise ValueError("invalid_release_candidate_hash")
        else:
            capture.slug(value["batch_key"], "batch_key")
            if type(value["revision"]) is not int or not 1 <= value["revision"] <= 100000:
                raise ValueError("invalid_update_batch_revision")
            if not value["markdown_path"].startswith("docs/deliverables/update-batches/"):
                raise ValueError("invalid_update_batch_markdown")
            paths.append(value["markdown_path"])
        if any(not any(e.get("path") == path for e in item.get("evidence", [])) for path in paths):
            raise ValueError("governance_manifest_evidence_required")
        result[name] = dict(value)
    return result


def normalize_archive(capture, artifact: dict) -> dict:
    category = artifact.get("category", artifact.get("document_kind", "unclassified"))
    if category not in CATEGORIES or artifact.get("origin", "delivery_generated") not in ORIGINS:
        raise ValueError("invalid_archive_classification")
    state = artifact.get("document_state", "draft")
    if state not in {"draft", "in_review", "final"} or artifact.get("retention", "current") not in {"current", "historical"}:
        raise ValueError("invalid_archive_state")
    result = {"category": category, "origin": artifact.get("origin", "delivery_generated"),
              "document_state": state, "retention": artifact.get("retention", "current"),
              "summary": capture.text(artifact["summary"], 1200, "archive_summary") if artifact.get("summary") else "",
              "tags": capture._strings(artifact.get("tags", []), "archive_tags", count=20, limit=120)}
    for field in ("release_ref", "original_name", "document_title", "template_version"):
        result[field] = capture.text(artifact[field], 240, "archive_" + field) if artifact.get(field) else ""
    resource = artifact.get("resource_ref", "")
    if resource:
        if not re.fullmatch(r"mawdoc://[a-z0-9][a-z0-9._-]{0,119}/[a-f0-9]{64}", resource):
            raise ValueError("invalid_archive_resource")
        if artifact.get("mime") not in {"text/markdown", "text/plain", "application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}:
            raise ValueError("invalid_archive_mime")
        if type(artifact.get("size")) is not int or not 0 < artifact["size"] <= 20_000_000:
            raise ValueError("invalid_archive_size")
        if artifact.get("content_hash") != resource.rsplit("/", 1)[1]:
            raise ValueError("archive_resource_hash_mismatch")
        result.update(resource_ref=resource, mime=artifact["mime"], size=artifact["size"], content_hash=artifact["content_hash"])
    return result
