"""Version negotiation and trust boundaries for the four governance domains."""
from copy import deepcopy
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("source_v4", ROOT / "ops/scripts/capture-document-source.py")
capture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(capture)


def event():
    return {"schema": capture.EVENT_SCHEMA_V3, "event_id": "public-understanding", "title": "核对任务目标",
        "occurred_at": "2026-10-22T03:00:00+08:00", "source": {"kind": "ai_analysis", "ref": "task:one", "excerpt": "先核对范围"},
        "context": {"session_ref": "run:one", "task_ref": "task:one", "trigger": "progress"},
        "items": [{"key": "understanding", "kind": "implementation", "statement": "只调整课程研发的审核入口。",
            "volume": "task-audit", "owner": "测试执行器", "decision_status": "not_applicable",
            "implementation_status": "not_applicable", "audit_status": "not_applicable", "next_action": "核对证据",
            "activity": {"task_ref": "task:one", "session_ref": "run:one", "phase": "started", "goal": "修正审核入口",
                         "actions": ["核对授权范围"], "result": "目标已留存", "validation": "尚未验证"},
            "process": {"event_type": "understanding", "reason": "依据当前明确任务", "assumptions": ["不修改其它模块"],
                        "goal_snapshot": {"goal": "修正审核入口", "scope": "课程研发", "constraints": "保持权限门禁", "acceptance": "真实角色验证"}}}]}


def test_v4_process_roundtrip_preserves_goal_and_reason(tmp_path):
    source = capture.event_payload(event())
    assert source["schema"] == capture.SCHEMA_V4
    receipt = capture.capture(tmp_path, event(), action="record-event", work_intent="modify")
    assert capture.capture(tmp_path, event(), action="check-event")["sha256"] == receipt["sha256"]
    body = (tmp_path / receipt["path"]).read_text()
    assert "真实角色验证" in body and "依据当前明确任务" in body


def test_new_fields_cannot_be_written_in_old_version(tmp_path):
    old = event()
    old["schema"] = capture.EVENT_SCHEMA_V2
    with pytest.raises(ValueError, match="v4_required"):
        capture.capture(tmp_path, old, action="preview-event")
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("field,value", [("event_type", "hidden_reasoning"), ("reason", "password=forbidden")])
def test_private_or_sensitive_material_is_rejected(tmp_path, field, value):
    invalid = deepcopy(event())
    invalid["items"][0]["process"][field] = value
    with pytest.raises(ValueError):
        capture.capture(tmp_path, invalid, action="preview-event")


def test_baseline_cannot_claim_complete_with_gaps():
    ext = capture.source_extensions()
    with pytest.raises(ValueError, match="baseline_with_gaps"):
        ext.normalize_extensions(capture, {"baseline": {"mode": "initialize", "status": "frozen", "input_hash": "a" * 64,
            "gaps": ["业务规则尚未确认"]}}, activity=None)
