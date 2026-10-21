"""Immutable deliverables compiled from confirmed answers and explicitly selected facts."""
from __future__ import annotations

import hashlib
from .model import context
from .store import digest


KINDS = {"requirements": "需求文档", "design": "设计文档", "acceptance": "测试与验收文档",
         "delivery": "部署与交付文档", "maintenance": "使用与维护文档"}
FIELDS = {"document_key", "document_kind", "document_title", "body", "previous_ref", "change_kind",
          "question_changes", "review_refs", "selected_question_refs"}
CHANGE_FIELDS = {"question_key", "scope", "question", "answer", "category", "claim_type", "rationale",
                 "exceptions", "base_refs", "evidence_paths", "modules", "resolves_issues"}


def prepare(service, payload: dict, snapshot: dict, item: dict, event_id: str) -> tuple[list[dict], dict[str, bytes]]:
    capture = service.capture
    kind = payload.get("document_kind")
    if kind not in KINDS:
        raise ValueError("invalid_artifact_kind")
    key = capture.slug(payload.get("document_key"), "document_key")
    title = capture.text(payload.get("document_title", KINDS[kind]), 180, "document_title")
    previous_ref = payload.get("previous_ref", "")
    previous = next((x for x in snapshot["artifacts"] if x["id"] == previous_ref), None)
    revisions = [x for x in snapshot["artifacts"] if x["artifact"]["document_key"] == key]
    replaced = {x["artifact"]["previous_ref"] for x in revisions}
    heads = [x for x in revisions if x["id"] not in replaced]
    if previous_ref and (previous is None or previous["artifact"]["document_key"] != key):
        raise ValueError("artifact_previous_version_invalid")
    if previous:
        prior_path = capture.safe_path(service.root, previous["artifact"]["path"])
        expected = next((e["sha256"] for e in previous["evidence"] if e["path"] == previous["artifact"]["path"]), "")
        if hashlib.sha256(prior_path.read_bytes()).hexdigest() != expected:
            raise ValueError("artifact_previous_version_invalid")
    if heads and (len(heads) != 1 or heads[0]["id"] != previous_ref):
        raise ValueError("artifact_current_version_required")
    changes = payload.get("question_changes", [])
    if not isinstance(changes, list) or len(changes) > 20:
        raise ValueError("invalid_artifact_question_changes")
    change_kind = payload.get("change_kind", "generated" if not previous else "editorial")
    if change_kind == "substantive" and not changes:
        raise ValueError("artifact_substantive_mapping_required")
    if changes and change_kind != "substantive":
        raise ValueError("artifact_question_changes_require_substantive_revision")
    if changes and payload.get("source_kind") != "user_statement":
        raise ValueError("governance_human_confirmation_required")
    mapped = []
    seen = set()
    for index, change in enumerate(changes):
        capture.only_keys(change, CHANGE_FIELDS, "question_change")
        identity = (change.get("question_key"), change.get("scope", "project"))
        if identity in seen:
            raise ValueError("artifact_duplicate_question_mapping")
        seen.add(identity)
        answer = service._answer({**payload, **change, "evidence_paths": change.get("evidence_paths", []), "operation": "confirm"}, snapshot,
                                 {**item, "key": f"answer-{index + 1}"}, "user_statement")
        mapped.append(answer)
    current = context(snapshot, payload.get("scope", ""), payload.get("module", ""))
    # A combined revision can resolve existing branches, but may not silently omit
    # other unresolved conflicts in a document's selected scope.
    mapped_refs = {ref for change in changes for ref in change.get("base_refs", [])}
    if any(b["ref"] not in mapped_refs for b in current["blockers"]):
        raise ValueError("artifact_unresolved_authority_conflict")
    requested = payload.get("selected_question_refs")
    if requested is not None and (not isinstance(requested, list) or any(not isinstance(x, str) for x in requested)):
        raise ValueError("invalid_artifact_selected_questions")
    selected = [x for x in current["questions"] if requested is None or x["ref"] in requested]
    if requested is not None and set(requested) != {q["ref"] for q in selected}:
        raise ValueError("artifact_question_version_changed")
    selected = [q for q in selected if q["ref"] not in mapped_refs]
    selected += [{"ref": f"{event_id}#{a['key']}", "question": a["business"]["title"], "answer": a["statement"],
                  "scope": a["business"]["scope"], "claim_type": a["qa"]["claim_type"]} for a in mapped]
    if not selected and not payload.get("evidence_paths"):
        raise ValueError("artifact_authority_or_facts_required")
    facts = []
    if not isinstance(payload.get("evidence_paths", []), list) or len(payload.get("evidence_paths", [])) > 19:
        raise ValueError("artifact_evidence_limit_exceeded")
    for evidence in payload.get("evidence_paths", []):
        capture.only_keys(evidence, {"path", "kind"}, "evidence")
        path = capture.safe_path(service.root, evidence.get("path"))
        if path.stat().st_size > 2_000_000:
            raise ValueError("evidence_too_large")
        facts.append({**evidence, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    body = payload.get("body", "")
    if body:
        body = capture.text(body, 90000, "artifact_body")
    review_refs = capture._strings(payload.get("review_refs", []), "artifact_review_refs", count=20, limit=240)
    if previous and change_kind == "substantive" and not review_refs:
        raise ValueError("artifact_revision_review_reference_required")
    manifest = {"questions": selected, "facts": facts, "previous_ref": previous_ref, "review_refs": review_refs,
                "scope": payload.get("scope", "project"), "body": body, "kind": kind}
    input_hash = digest(manifest)
    version = event_id.removeprefix("governance-")
    relative = f"docs/deliverables/{key}/{version}.md"
    lines = [f"# {title}", "", f"项目：{service.project_key} · 档案：{key} · 版本：{version}", "",
             "版本状态以对应项目来源回执为准；没有完成回执时仅为准备中的草稿。", "",
             "## 已确认的项目口径", ""]
    for q in selected:
        lines += [f"### {q['question']}", "", q["answer"], "",
                  f"依据：`{q['ref']}`；范围：`{q['scope']}`；类型：`{q['claim_type']}`。", ""]
    if not selected:
        lines += ["此范围尚无已确认口径，不能据代码现状推定需求已获确认。", ""]
    lines += ["## 代码与资料事实", ""]
    for fact in facts:
        lines += [f"- `{fact['path']}` · {fact['kind']} · SHA-256 `{fact['sha256']}`"]
    if not facts:
        lines += ["尚未选择代码或验证证据；本文不宣称功能已经实现或验收通过。"]
    lines += ["", "## 档案正文", "", body or "以上为依据汇编。请结合所列证据完善交付说明，再进入人工审阅。", "",
              "## 修订与审计", "", f"上一版本：{previous_ref or '首次生成'}", "",
              *[f"- 审阅依据：{ref}" for ref in review_refs], "", f"输入指纹：`{input_hash}`", ""]
    content = "\n".join(lines).encode("utf-8")
    if len(content) > 262144:
        raise ValueError("artifact_too_large")
    artifact = {**item, "key": "document", "kind": "observation", "volume": "technical" if kind == "design" else "requirements",
        "statement": f"{title}形成固定版本；{len(selected)}条口径，{len(facts)}份代码或资料依据。",
        "evidence": [*payload.get("evidence_paths", []), {"path": relative, "kind": "document"}],
        "artifact": {"document_key": key, "version_key": version, "document_kind": kind, "path": relative,
                     "input_hash": input_hash, "previous_ref": previous_ref, "question_refs": [q["ref"] for q in selected],
                     "change_kind": change_kind, "review_refs": review_refs}}
    return [artifact, *mapped], {relative: content}
