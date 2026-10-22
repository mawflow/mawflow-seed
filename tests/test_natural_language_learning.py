"""Language correction survives new consumers while authority stays in source events."""
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ops/scripts"))
from maw_governance import Governance


def request(engine, operation="propose", request_id="candidate", **values):
    return {"operation": operation, "request_id": request_id, "occurred_at": "2026-10-22T12:00:00+08:00",
        "expected_source_version": engine.read()["source_version"], "task_ref": "language-task", "run_ref": "run-one",
        "source_ref": "合成对话验收样例，非实际业务口径", **values}


def rule(**values):
    return {"question_key": "language.inspect", "scope": "project", "question": "先摸一下应该怎样理解？",
        "answer": "只读了解现状并提出建议，修改需要相应授权。", "category": "experience", "claim_type": "experience",
        "rationale": "用户明确纠正先了解现状的含义", "confirmation_scope": "仅确认本项目这组表达的含义",
        "learning": {"kind": "rule", "utterances": ["先摸一下", "先了解现状", "先帮我看看"],
            "intent": "先调研，再给建议", "operation_mode": "read_only", "negative_examples": ["先帮我看看并直接修复"], "environments": []}, **values}


def apply(engine, payload, actor="test-agent"):
    preview = engine.preview(payload, actor=actor)
    return engine.apply(payload, actor=actor, expected_fingerprint=preview["fingerprint"], work_intent="modify")


def confirmed(engine, **values):
    return apply(engine, request(engine, "confirm", "confirmed", **rule(**values)))


def reuse(engine, recalled, **values):
    context = engine.context()
    return request(engine, "consume", "consumption", context_hash=context["context_hash"],
        question_refs=context["question_refs"], consumer_ref="second-agent", recall_query=recalled["query"],
        recall_hash=recalled["recall_hash"], rule_refs=recalled["rule_refs"], **values)


def test_user_correction_and_cross_process_reuse_preserve_exact_versions(tmp_path):
    engine = Governance(tmp_path, "demo")
    candidate = apply(engine, request(engine, **rule(answer="直接开始修改。", learning={**rule()["learning"], "operation_mode": "modify"})))
    assert engine.recall(utterance="先摸一下")["status"] == "no_match"
    accepted = apply(engine, request(engine, "confirm", "correction", **rule(base_refs=candidate["item_refs"])))
    # A genuinely separate Python process has no access to the first consumer's memory.
    output = subprocess.check_output([sys.executable, str(ROOT / "ops/scripts/manage-project-governance.py"), "recall",
        "--root", str(tmp_path), "--project-key", "demo", "--utterance", "先帮我看看项目，给一些建议"], text=True)
    recalled = json.loads(output)
    assert recalled["rule_refs"] == accepted["item_refs"]
    assert recalled["matches"][0]["learning"]["operation_mode"] == "read_only"
    assert recalled["trust_boundary"]["authorization_granted"] is False
    new_engine = Governance(tmp_path, "demo")
    receipt = apply(new_engine, reuse(new_engine, recalled))
    feedback = request(new_engine, "feedback", "feedback", reuse_ref=receipt["item_refs"][0], outcome="useful",
        rationale="样例人工核对与预期一致", result="第二会话仅给出调研建议。", validation="合成旅程已核对")
    apply(new_engine, feedback)
    assert apply(new_engine, feedback)["status"] == "unchanged"
    report = new_engine.learning_report()
    assert report["reuse_count"] == 1 and report["outcomes"]["useful"] == 1
    assert new_engine.context()["question_refs"] == accepted["item_refs"]


def test_recall_is_readonly_and_empty_or_candidate_only_does_not_assert_success(tmp_path):
    engine = Governance(tmp_path, "demo")
    assert engine.recall(utterance="看看项目")["status"] == "no_match"
    assert engine.learning_report()["reuse_count"] == 0
    assert not list(tmp_path.iterdir())
    apply(engine, request(engine, **rule()))
    before = {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    assert engine.recall(utterance="先摸一下")["matches"] == []
    assert before == {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}


@pytest.mark.parametrize("kwargs", [{"scope": "customer"}, {"modules": ["merchant"]},
    {"learning": {**rule()["learning"], "environments": ["sit"]}}])
def test_restricted_rule_requires_matching_scope_module_and_environment(tmp_path, kwargs):
    engine = Governance(tmp_path, "demo")
    confirmed(engine, **kwargs)
    assert engine.recall(utterance="先摸一下")["matches"] == []
    assert len(engine.recall(utterance="先摸一下", scope="customer", module="merchant", environment="sit")["matches"]) == 1


def test_negative_example_is_not_reused_and_unseen_rephrasing_requires_agent_judgment(tmp_path):
    engine = Governance(tmp_path, "demo")
    confirmed(engine)
    assert not engine.recall(utterance="先帮我看看并直接修复")["matches"]
    result = engine.recall(utterance="探究一下现有实现")
    assert result["status"] == "no_match" and result["trust_boundary"]["semantic_judgment"] == "agent_required"


def test_ambiguous_modes_and_truncation_do_not_create_consumption(tmp_path):
    engine = Governance(tmp_path, "demo")
    confirmed(engine)
    apply(engine, request(engine, "confirm", "modify", **rule(question_key="language.modify",
        learning={**rule()["learning"], "operation_mode": "modify"})))
    result = engine.recall(utterance="先摸一下")
    assert result["status"] == "clarification_required"
    with pytest.raises(ValueError, match="ambiguous"):
        engine.preview(reuse(engine, result), actor="agent")
    assert engine.recall(utterance="先摸一下", limit=1)["truncated"]


def test_stale_recall_and_context_cannot_be_consumed(tmp_path):
    engine = Governance(tmp_path, "demo")
    first = confirmed(engine)
    recalled = engine.recall(utterance="先摸一下")
    apply(engine, request(engine, "confirm", "new-version", **rule(base_refs=first["item_refs"], answer="先调研并给出问题清单。")))
    with pytest.raises(ValueError, match="recall_changed"):
        engine.preview(reuse(engine, recalled), actor="agent")


def test_feedback_cannot_target_another_run_or_confirm_a_rule(tmp_path):
    engine = Governance(tmp_path, "demo")
    confirmed(engine)
    receipt = apply(engine, reuse(engine, engine.recall(utterance="先摸一下")))
    feedback = request(engine, "feedback", "bad-run", run_ref="different-run", reuse_ref=receipt["item_refs"][0],
        outcome="useful", rationale="样例", result="结果", validation="未验证")
    with pytest.raises(ValueError, match="run_mismatch"):
        engine.preview(feedback, actor="agent")
    bad = request(engine, "confirm", "ai-confirm", source_kind="ai_analysis", **rule())
    with pytest.raises(ValueError, match="human_confirmation_required"):
        engine.preview(bad, actor="agent")


def test_recall_scope_cannot_be_substituted_for_the_consumed_scope(tmp_path):
    engine = Governance(tmp_path, "demo")
    confirmed(engine, scope="customer")
    recalled = engine.recall(utterance="先摸一下", scope="customer")
    with pytest.raises(ValueError, match="scope_mismatch"):
        engine.preview(reuse(engine, recalled), actor="agent")


def test_correction_feedback_requires_review_until_exact_reconfirmation(tmp_path):
    engine = Governance(tmp_path, "demo")
    first = confirmed(engine)
    receipt = apply(engine, reuse(engine, engine.recall(utterance="先摸一下")))
    apply(engine, request(engine, "feedback", "corrected", reuse_ref=receipt["item_refs"][0], outcome="corrected",
        rationale="用户补充了适用边界", result="本次理解需修订", validation="待确认新口径"))
    assert engine.recall(utterance="先摸一下")["status"] == "clarification_required"
    fresh = apply(engine, request(engine, "confirm", "reconfirmed", **rule(base_refs=first["item_refs"])))
    assert engine.recall(utterance="先摸一下")["rule_refs"] == fresh["item_refs"]
    assert engine.recall(utterance="先摸一下")["status"] == "matched"


def test_retired_rule_and_changed_evidence_are_not_reused(tmp_path):
    engine = Governance(tmp_path, "demo")
    evidence = tmp_path / "docs/evidence.md"
    evidence.parent.mkdir()
    evidence.write_text("已核对样例")
    first = confirmed(engine, evidence_paths=[{"path": "docs/evidence.md", "kind": "test"}])
    evidence.write_text("样例已改变")
    assert engine.recall(utterance="先摸一下")["matches"] == []
    assert not engine.recall(utterance="先摸一下")["complete"]
    apply(engine, request(engine, "retire", "retired", **rule(base_refs=first["item_refs"])))
    assert engine.recall(utterance="先摸一下")["matches"] == []


@pytest.mark.parametrize("learning", [{**rule()["learning"], "operation_mode": "production"},
    {**rule()["learning"], "utterances": []}, {**rule()["learning"], "hidden_reasoning": "private"}])
def test_invalid_learning_contract_is_rejected_without_source_writes(tmp_path, learning):
    engine = Governance(tmp_path, "demo")
    with pytest.raises(ValueError):
        engine.preview(request(engine, **rule(learning=learning)), actor="agent")
    assert not list(tmp_path.iterdir())
