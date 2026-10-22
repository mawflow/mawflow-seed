"""Explicit enrollment, independent documents and immutable version recovery."""
import hashlib
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ops/scripts"))
from maw_governance import Governance


def request(service, **values):
    return {"operation": "register", "request_id": values.pop("request_id", "document"),
        "occurred_at": "2026-10-22T04:00:00+08:00", "expected_source_version": service.read()["source_version"],
        "document_key": "governance-plan", "document_kind": "plans", "document_title": "项目治理实施方案",
        "summary": "说明治理能力和实施次序", "body": "## 实施目标\n\n先完成共享协议，再增量采用。", "origin": "task_generated", **values}


def apply(service, payload):
    preview = service.preview(payload, actor="operator")
    return service.apply(payload, actor="operator", expected_fingerprint=preview["fingerprint"], work_intent="modify")


def test_only_enrolled_members_with_body_first_and_registration_readback(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/unselected.md").write_text("不自动收录")
    service = Governance(tmp_path, "example")
    assert service.library()["total"] == 0
    payload = request(service)
    receipt = apply(service, payload)
    member = receipt["documents"][0]
    assert member["title"] == "项目治理实施方案" and member["category_label"] == "方案与决策"
    assert member["registration_status"] == "registered" and member["task_ref"]
    body = (tmp_path / member["path"]).read_text()
    assert body.index("先完成共享协议") < body.index("## 已确认的项目口径")
    assert member["content_hash"] == hashlib.sha256(body.encode()).hexdigest()
    assert apply(service, payload)["status"] == "unchanged"
    assert (tmp_path / "docs/unselected.md").read_text() == "不自动收录"


def test_unrelated_stale_facts_do_not_block_independent_registration(tmp_path):
    (tmp_path / "fact.txt").write_text("old")
    service = Governance(tmp_path, "example")
    apply(service, {"operation": "confirm", "request_id": "fact", "occurred_at": "2026-10-22T04:00:00+08:00",
        "expected_source_version": service.read()["source_version"], "question_key": "runtime.fact", "scope": "project",
        "question": "当前运行状态是什么？", "answer": "当前处于旧状态", "category": "technical", "claim_type": "implementation_fact",
        "rationale": "记录运行事实", "confirmation_scope": "确认当前事实", "evidence_paths": [{"path": "fact.txt", "kind": "code"}]})
    (tmp_path / "fact.txt").write_text("new")
    assert not service.context()["complete"]
    assert apply(service, request(service))["documents"][0]["integrity"] == "current"
    assert not service.context()["complete"]


def test_selected_existing_markdown_preserves_original_and_freezes_revision(tmp_path):
    (tmp_path / "docs").mkdir()
    original = tmp_path / "docs/existing.md"
    original.write_text("# 原方案\n\n当前正文。")
    service = Governance(tmp_path, "example")
    first = apply(service, request(service, body="", source_path="docs/existing.md", origin="existing"))
    first_member = first["documents"][0]
    first_content = (tmp_path / first_member["path"]).read_bytes()
    with pytest.raises(ValueError, match="current_version_required"):
        service.preview(request(service, request_id="overwrite", body="未经版本关联的修改"), actor="operator")
    second = apply(service, request(service, request_id="revision", previous_ref=first_member["version_ref"], body="新版正文。"))
    assert service.library()["total"] == 1
    assert service.library(include_history=True)["total"] == 2
    assert (tmp_path / first_member["path"]).read_bytes() == first_content
    assert original.read_text() == "# 原方案\n\n当前正文。"
    assert second["documents"][0]["previous_ref"] == first_member["version_ref"]


def test_managed_original_is_a_reference_not_git_content_or_existence_proof(tmp_path):
    service = Governance(tmp_path, "example")
    sha = "a" * 64
    imported = request(service, body="", document_kind="reference", category="reference", origin="human_import",
        resource_ref=f"mawdoc://governance-plan/{sha}", content_hash=sha, mime="application/pdf", size=1234, original_name="业务参考.pdf")
    preview = service.preview(imported, actor="operator")
    assert preview["prepared_files"] == {}
    receipt = apply(service, imported)
    member = receipt["documents"][0]
    assert member["path"] == "" and member["availability"] == "host_verification_required"
    assert not (tmp_path / "docs/deliverables").exists()
    assert not service.context()["question_refs"]


def test_registration_retry_does_not_regenerate_body(tmp_path, monkeypatch):
    service = Governance(tmp_path, "example")
    payload = request(service)
    capture = service.capture.capture
    def fail(*args, **kwargs):
        if kwargs.get("action") == "record-event":
            raise OSError("registration interrupted after save")
        return capture(*args, **kwargs)
    monkeypatch.setattr(service.capture, "capture", fail)
    with pytest.raises(OSError):
        apply(service, payload)
    saved = next((tmp_path / "docs/deliverables/governance-plan").glob("*.md"))
    checksum = hashlib.sha256(saved.read_bytes()).hexdigest()
    assert service.library()["total"] == 0
    monkeypatch.setattr(service.capture, "capture", capture)
    receipt = apply(service, payload)
    assert receipt["documents"][0]["content_hash"] == checksum
    assert len(list(saved.parent.glob("*.md"))) == 1


def test_final_requires_review_and_five_delivery_templates_have_readable_structure(tmp_path):
    service = Governance(tmp_path, "example")
    with pytest.raises(ValueError, match="final_review_required"):
        service.preview(request(service, document_state="final", source_kind="ai_analysis"), actor="operator")
    templates = service.templates()
    assert len(templates["templates"]) == 5
    assert all(len(t["sections"]) >= 6 for t in templates["templates"].values())
    assert "完整正文" in templates["instructions"]
