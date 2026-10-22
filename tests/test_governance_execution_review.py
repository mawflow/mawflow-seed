"""Whole-run public review, missing evidence, source validation and isolation."""
from copy import deepcopy
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ops/scripts"))
from maw_governance import Governance
from maw_governance.review import materials, summary_chunks, template_summary, validate_ai_summary, render_summary


GOAL = {"goal": "删除服务器时同步清理凭证并解除项目关联", "scope": "服务器管理", "constraints": "保留无关修改", "acceptance": "清理及失败回滚有真实验证", "source_ref": "task:one:original-request"}
OUTCOME = {"task_ref": "task:one", "run_ref": "run:one", "state": "completed", "summary": "执行已结束，待人工验收。", "source_ref": "runtime:one", "evidence_refs": ["test:one"]}


def public(index, **values):
    return {"id": f"public-{index}", "task_ref": "task:one", "run_ref": "run:one", "sequence": index,
            "occurred_at": "2026-10-22T04:00:00+08:00", "text": f"第{index}项公开执行说明", "event_type": "progress", **values}


def test_late_decision_failure_and_recovery_remain_visible_after_success(tmp_path):
    service = Governance(tmp_path, "example")
    events = [public(0, event_type="understanding", text="我先按仅删除服务器登记理解。")]
    events += [public(i) for i in range(1, 25)]
    events += [public(25, event_type="failure", text="首轮验证发现凭证仍保留。"),
        public(26, event_type="adjustment", text="改为统一清理凭证和项目关系。", reason="原要求明确包含这两项。"),
        public(27, event_type="recovery", text="补齐清理并重新验证。"),
        public(28, event_type="verification", text="定向用例通过，真人验收尚未进行。", evidence_refs=["test:one"])]
    bundle = materials(service, task_ref="task:one", run_ref="run:one", public_messages=events, original_goal=GOAL, outcome=OUTCOME)
    summary = template_summary(bundle)
    markdown = render_summary(summary)
    assert len(bundle["events"]) == 29 and summary["summary_omitted_count"] == 0
    assert all(text in markdown for text in ["仅删除服务器登记", "凭证仍保留", "统一清理", "原要求明确", "补齐清理", "定向用例通过"])
    assert "AI自述" in markdown and "真人验收" in markdown
    assert not bundle["trust_boundary"]["hidden_reasoning_included"]


def test_tool_success_does_not_invent_motivation_and_final_only_is_partial(tmp_path):
    service = Governance(tmp_path, "example")
    event = public(1, event_type="decision", text="选择统一清理。")
    observation = {**public(2, event_type="verification", text="进程退出码0"), "role": "tool", "identity_level": "runtime_observed"}
    bundle = materials(service, task_ref="task:one", run_ref="run:one", public_messages=[event], observations=[observation], outcome=OUTCOME)
    markdown = render_summary(template_summary(bundle))
    assert "未记录，不能从工具结果倒推" in markdown and "系统观测" in markdown
    assert not bundle["coverage"]["goal"] and not bundle["coverage"]["understanding"]
    final_only = service.review(task_ref="task:one", run_ref="run:one", outcome=OUTCOME)
    assert not final_only["materials"]["events"] and len(final_only["materials"]["gaps"]) >= 2


def test_runs_do_not_mix_and_private_material_is_rejected(tmp_path):
    service = Governance(tmp_path, "example")
    with pytest.raises(ValueError, match="run_mismatch"):
        materials(service, task_ref="task:one", run_ref="run:two", public_messages=[public(1)])
    for invalid in [public(1, role="reasoning"), public(1, visibility="private"), public(1, event_type="reasoning")]:
        with pytest.raises(ValueError):
            materials(service, task_ref="task:one", run_ref="run:one", public_messages=[invalid])
    with pytest.raises(ValueError, match="outcome_run_mismatch"):
        materials(service, task_ref="task:one", run_ref="run:two", outcome=OUTCOME)


def test_chunking_covers_all_sources_dedupes_replays_and_input_hash_is_stable(tmp_path):
    service = Governance(tmp_path, "example")
    events = [public(i, text="公开执行材料。" * 250) for i in range(50)]
    bundle = materials(service, task_ref="task:one", run_ref="run:one", public_messages=events + [deepcopy(events[5])])
    chunks = summary_chunks(bundle)
    assert len(chunks["chunks"]) > 1 and bundle["coverage"]["duplicate_count"] == 1
    assert {r for c in chunks["chunks"] for r in c["source_refs"]} == {e["ref"] for e in bundle["events"]}
    assert bundle["input_hash"] == materials(service, task_ref="task:one", run_ref="run:one", public_messages=events + [deepcopy(events[5])])["input_hash"]
    assert not list(tmp_path.iterdir())


def test_ai_summary_must_reference_real_sources_and_preserve_critical_events(tmp_path):
    service = Governance(tmp_path, "example")
    bundle = materials(service, task_ref="task:one", run_ref="run:one", public_messages=[public(1, event_type="failure", text="首次验证失败")], original_goal=GOAL, outcome=OUTCOME)
    basic = template_summary(bundle)
    ai = {"sections": [{"key": s["key"], "paragraphs": s["paragraphs"]} for s in basic["sections"]]}
    assert validate_ai_summary(service, bundle, ai)["generation_method"] == "ai"
    missing = deepcopy(ai)
    missing["sections"][2]["paragraphs"] = []
    with pytest.raises(ValueError, match="critical_source_omitted"):
        validate_ai_summary(service, bundle, missing)
    unknown = deepcopy(ai)
    unknown["sections"][0]["paragraphs"][0]["source_refs"] = ["private-unseen-source"]
    with pytest.raises(ValueError, match="source_invalid"):
        validate_ai_summary(service, bundle, unknown)


def test_structured_reason_links_are_scoped_and_read_only_review_keeps_source_hash(tmp_path):
    service = Governance(tmp_path, "example")
    def request(request_id, **values):
        return {"operation": "work", "request_id": request_id, "occurred_at": "2026-10-22T04:00:00+08:00",
            "expected_source_version": service.read()["source_version"], "task_ref": "task:one", "run_ref": "run:one", "phase": "progress",
            "goal": "核对用户原意", "actions": ["核对删除范围"], "result": "正在实现统一清理", "validation": "待测试", **values}
    start = request("start", process={"event_type": "understanding", "reason": "依据用户要求"})
    preview = service.preview(start, actor="agent")
    receipt = service.apply(start, actor="agent", expected_fingerprint=preview["fingerprint"], work_intent="modify")
    with pytest.raises(ValueError, match="reference_run_mismatch"):
        service.preview(request("wrong-run", run_ref="run:two", process={"event_type": "decision", "previous_refs": receipt["item_refs"]}), actor="agent")
    before = {str(p): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    report = service.review(task_ref="task:one", run_ref="run:one")
    assert report["materials"]["events"][0]["source_hash"] == receipt["sha256"]
    assert {str(p): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()} == before
