"""Human maintenance, exact batch confirmation, full migration and read-only audit."""
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ops/scripts"))
from maw_governance import Governance
from maw_governance.baseline import DIMENSIONS


def request(service, operation="confirm", **values):
    return {"operation": operation, "request_id": values.pop("request_id", operation),
            "occurred_at": "2026-10-22T03:00:00+08:00", "expected_source_version": service.read()["source_version"],
            "source_ref": "测试人工精确选择", "confirmation_scope": "确认预览中全部正文及适用范围", **values}


def question(index=1, **values):
    return {"question_key": f"course.rule-{index}", "scope": "project", "question": f"第{index}条课程规则如何执行？",
        "answer": f"仅处理当前授权范围的课程；第{index}条有完整说明与例外。", "category": "business", "claim_type": "requirement",
        "rationale": "人工直接维护", **values}


def apply(service, payload):
    preview = service.preview(payload, actor="human")
    return service.apply(payload, actor="human", expected_fingerprint=preview["fingerprint"], work_intent="modify")


def test_human_create_edit_delete_preserve_old_consumptions_and_artifacts(tmp_path):
    service = Governance(tmp_path, "example")
    first = apply(service, request(service, **question(answer="完整答案" * 600)))
    context = service.context()
    assert service.reading()["question_refs"] == context["question_refs"]
    artifact = apply(service, request(service, "artifact", document_key="business", document_kind="requirements",
        selected_question_refs=context["question_refs"], body="当前完整业务规则。"))
    revised = request(service, request_id="edit", **question(answer="人工直接编辑后的规则。", base_refs=first["item_refs"]))
    preview = service.preview(revised, actor="human")
    assert preview["diff"][0]["before"][0]["answer"] == "完整答案" * 600
    assert preview["diff"][0]["impacts"]["artifacts"] == artifact["item_refs"]
    second = apply(service, revised)
    apply(service, request(service, "retire", request_id="delete", **question(answer="人工删除此口径；保留历史。", base_refs=second["item_refs"])))
    assert service.context()["question_refs"] == [] and service.reading()["total"] == 0
    assert len(service.read()["questions"][0]["history"]) == 3
    assert service.read()["artifacts"][0]["artifact"]["question_refs"] == first["item_refs"]


def test_batch_is_atomic_precise_and_cannot_self_confirm(tmp_path, monkeypatch):
    service = Governance(tmp_path, "example")
    payload = request(service, "revision_batch", intent="confirm", changes=[question(1), question(2)])
    preview = service.preview(payload, actor="human")
    assert len(preview["diff"]) == 2 and not list(tmp_path.iterdir())
    with pytest.raises(ValueError, match="human_confirmation_required"):
        service.preview({**payload, "source_kind": "ai_analysis"}, actor="ai")
    capture = service.capture.capture
    def fail(*args, **kwargs):
        if kwargs.get("action") == "record-event":
            raise OSError("injected interruption")
        return capture(*args, **kwargs)
    monkeypatch.setattr(service.capture, "capture", fail)
    with pytest.raises(OSError):
        service.apply(payload, actor="human", expected_fingerprint=preview["fingerprint"], work_intent="modify")
    assert not service.context()["question_refs"]
    monkeypatch.setattr(service.capture, "capture", capture)
    receipt = apply(service, payload)
    assert len(receipt["item_refs"]) == 2
    assert apply(service, payload)["status"] == "unchanged"
    with pytest.raises(ValueError, match="request_conflict"):
        apply(service, {**payload, "changes": [question(1)]})


def test_candidates_do_not_replace_authority_and_stale_manual_edits_fail(tmp_path):
    service = Governance(tmp_path, "example")
    old = apply(service, request(service, **question()))
    pending = request(service, request_id="stale", **question(answer="旧页面编辑", base_refs=old["item_refs"]))
    apply(service, request(service, "revision_batch", request_id="natural-language", intent="propose", changes=[
        question(answer="AI整理的自然语言修订候选", base_refs=old["item_refs"])], source_kind="ai_analysis"))
    assert service.context()["question_refs"] == old["item_refs"]
    with pytest.raises(ValueError, match="source_changed"):
        service.preview(pending, actor="human")


def test_organization_keeps_human_and_ai_versions_identical(tmp_path):
    service = Governance(tmp_path, "example")
    apply(service, request(service, **question(category="environment")))
    context = service.context()
    apply(service, request(service, "organize", organizations=[{"question_key": "course.rule-1", "scope": "project", "chapter": "SIT与UAT", "order": 2}]))
    reading = service.reading()
    assert reading["question_refs"] == context["question_refs"] == service.context()["question_refs"]
    assert reading["chapters"][0]["title"] == "SIT与UAT"
    assert "完整说明与例外" in reading["markdown"]


def test_full_topic_inventory_no_hardcoded_87_or_first_page(tmp_path):
    service = Governance(tmp_path, "example")
    for start in range(0, 117, 30):
        apply(service, request(service, "revision_batch", request_id=f"batch-{start}", intent="confirm",
            changes=[question(i) for i in range(start, min(start + 30, 117))]))
    before = {str(p.relative_to(tmp_path)): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    report = service.baseline(mode="audit")
    after = {str(p.relative_to(tmp_path)): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    assert before == after and report["total_topics"] == len(report["migration"]) == 117
    assert len(report["question_refs"]) == 117 and not report["complete"]
    assert all(row["target_key"] == row["question_key"] and row["old_refs"] for row in report["migration"])


def test_baseline_requires_explicit_coverage_and_confirmation(tmp_path):
    service = Governance(tmp_path, "example")
    answer = apply(service, request(service, **question()))
    coverage = [{"module": "project", "dimension": dimension, "status": "covered", "question_refs": answer["item_refs"],
                 "reason": "本合成样本仅一项规则；逐项核对本维度。"} for dimension in DIMENSIONS]
    assert service.baseline(coverage=coverage)["complete"]
    candidate = request(service, "baseline", mode="initialize", coverage=coverage, baseline_status="frozen", source_kind="ai_analysis")
    with pytest.raises(ValueError, match="confirmation_or_coverage"):
        service.preview(candidate, actor="ai")
    receipt = apply(service, {**candidate, "source_kind": "user_statement"})
    item = next(i for i in service.read()["items"] if i["id"] in receipt["item_refs"])
    assert item["baseline"]["question_refs"] == answer["item_refs"]
    with pytest.raises(ValueError, match="audit_is_read_only"):
        service.preview(request(service, "baseline", request_id="audit", mode="audit"), actor="human")
    repeated = apply(service, request(service, "baseline", request_id="repeat", mode="initialize", coverage=coverage,
                                     baseline_status="frozen", source_kind="user_statement"))
    assert repeated["status"] == "unchanged" and repeated["item_refs"] == receipt["item_refs"]
    apply(service, request(service, "retire", request_id="delete", **question(answer="删除本条", base_refs=answer["item_refs"])))
    assert service.read()["baselines"][0]["baseline_check"]["status"] == "review_required"
