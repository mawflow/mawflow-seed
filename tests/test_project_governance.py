"""Exercise the actual append/projection protocol used by external agents and Host."""
from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ops/scripts"))
from maw_governance import Governance


def request(service, operation="propose", **kwargs):
    return {"operation": operation, "request_id": kwargs.pop("request_id", operation),
            "occurred_at": "2026-10-21T12:00:00+08:00", "expected_source_version": service.read()["source_version"],
            "question_key": "course.visibility", "scope": "project", "question": "课程列表显示哪些记录？",
            "answer": "仅显示当前角色有权访问的课程。", "category": "business", "claim_type": "requirement",
            "rationale": "明确项目业务约束", **kwargs}


def apply(service, payload, actor="operator"):
    preview = service.preview(payload, actor=actor)
    return service.apply(payload, actor=actor, expected_fingerprint=preview["fingerprint"], work_intent="modify")


def test_human_dialogue_confirmation_consumption_and_retirement(tmp_path):
    service = Governance(tmp_path, "test-project")
    proposed = apply(service, request(service))
    assert service.context()["questions"] == []
    issue = apply(service, request(service, "message", message="是否包含已归档课程？", issue_type="ambiguity",
        impact="影响列表查询范围", blocked_actions=["修改过滤条件"], continue_actions=["检查现有代码"]))
    assert len(service.read()["pending"]) == 1
    confirmed = apply(service, request(service, "confirm", base_refs=proposed["item_refs"],
        confirmation_scope="确认当前角色权限约束", resolves_issues=issue["item_refs"]))
    snapshot = service.read()
    assert not snapshot["pending"]
    assert snapshot["questions"][0]["status"] == "current"
    context = service.context()
    assert context["question_refs"] == confirmed["item_refs"]
    consumed = apply(service, request(service, "consume", task_ref="task-1", run_ref="run-1", consumer_ref="agent-a",
        scope="", context_hash=context["context_hash"], question_refs=context["question_refs"]))
    assert consumed["status"] == "recorded"
    assert service.read()["consumptions"][0]["consumption"]["evidence_level"] == "ai_reported"
    assert service.read()["consumptions"][0]["consumption_check"]["status"] == "current"
    apply(service, request(service, "retire", base_refs=confirmed["item_refs"], confirmation_scope="停用该约束"))
    assert service.read()["consumptions"][0]["consumption_check"]["status"] == "reread_required"
    assert service.context()["question_refs"] == []
    assert service.read()["questions"][0]["status"] == "retired"


def test_preview_is_readonly_and_retries_are_exact(tmp_path):
    service = Governance(tmp_path, "test-project")
    payload = request(service)
    preview = service.preview(payload, actor="operator")
    assert not list(tmp_path.iterdir())
    with pytest.raises(ValueError, match="modify_intent_required"):
        service.apply(payload, actor="operator", expected_fingerprint=preview["fingerprint"])
    with pytest.raises(ValueError, match="preview_changed"):
        service.apply(payload, actor="operator", expected_fingerprint="wrong", work_intent="modify")
    receipt = apply(service, payload)
    repeated = service.apply(payload, actor="operator", expected_fingerprint=preview["fingerprint"], work_intent="modify")
    assert repeated["status"] == "unchanged" and receipt["sha256"] == repeated["sha256"]
    with pytest.raises(ValueError, match="request_conflict"):
        apply(service, {**payload, "answer": "不同答案"})
    with pytest.raises(ValueError, match="request_conflict"):
        service.preview(payload, actor="someone-else")


def test_proposal_cannot_replace_confirmed_and_stale_preview_fails(tmp_path):
    service = Governance(tmp_path, "test-project")
    old = apply(service, request(service, "confirm", confirmation_scope="明确权限"))
    stale = request(service, "propose", request_id="stale")
    proposed = apply(service, request(service, request_id="proposal", base_refs=old["item_refs"], answer="所有人可见"))
    assert service.context()["question_refs"] == old["item_refs"]
    with pytest.raises(ValueError, match="source_changed"):
        service.preview(stale, actor="operator")
    with pytest.raises(ValueError, match="all_current_branches"):
        apply(service, request(service, "confirm", request_id="missing-base", confirmation_scope="确认新口径"))
    new = apply(service, request(service, "confirm", request_id="new-confirm", base_refs=proposed["item_refs"], confirmation_scope="确认变更"))
    assert service.context()["question_refs"] == new["item_refs"]


def test_ai_cannot_assert_human_confirmation_and_changed_evidence_blocks_context(tmp_path):
    (tmp_path / "code.py").write_text("old")
    service = Governance(tmp_path, "test-project")
    payload = request(service, "confirm", confirmation_scope="确认当前代码行为", claim_type="implementation_fact", evidence_paths=[{"path": "code.py", "kind": "code"}])
    with pytest.raises(ValueError, match="human_confirmation_required"):
        service.preview({**payload, "source_kind": "ai_analysis"}, actor="agent")
    apply(service, payload)
    (tmp_path / "code.py").write_text("new")
    assert not service.context()["complete"]
    assert service.context()["blockers"][0]["reason"] == "source_changed"


def test_broken_source_is_bounded_and_prevents_mutation(tmp_path):
    service = Governance(tmp_path, "test-project")
    apply(service, request(service))
    source = next((tmp_path / "docs/intake").glob("*.md"))
    raw = source.read_text()
    meta = json.loads(raw.split("\n---", 1)[0][4:])
    meta["content_contract"]["items"][0]["business"] = {"key": []}
    source.write_text("---\n" + json.dumps(meta) + "\n---\n")
    assert service.read()["partial"]
    with pytest.raises(ValueError, match="projection_incomplete"):
        service.preview(request(service), actor="operator")


def test_fixed_artifact_and_combined_revision_are_one_commit(tmp_path, monkeypatch):
    service = Governance(tmp_path, "test-project")
    original = apply(service, request(service, "confirm", confirmation_scope="确认项目列表权限"))
    generate = request(service, "artifact", document_key="requirements", document_kind="requirements",
        selected_question_refs=original["item_refs"], body="课程列表必须根据当前用户的角色权限过滤。")
    preview = service.preview(generate, actor="operator")
    assert not (tmp_path / "docs/deliverables").exists()
    first = apply(service, generate)
    artifact = service.read()["artifacts"][0]
    first_bytes = (tmp_path / artifact["artifact"]["path"]).read_bytes()
    assert "课程列表" in first_bytes.decode()
    revision = request(service, "artifact", request_id="revision", source_kind="user_statement",
        document_key="requirements", document_kind="requirements", previous_ref=first["item_refs"][0],
        change_kind="substantive", review_refs=["manual-review:review-1:paragraph-2"],
        confirmation_scope="同时确认档案修订及课程可见范围的对应变更", body="排除归档课程。",
        question_changes=[{"question_key": "course.visibility", "scope": "project", "question": "课程列表显示哪些记录？",
            "answer": "显示当前角色有权访问且未归档的课程。", "category": "business", "claim_type": "requirement",
            "rationale": "采纳人工档案审阅结论", "base_refs": original["item_refs"]}])
    preview = service.preview(revision, actor="operator")
    original_capture = service.capture.capture

    def fail_before_commit(*args, **kwargs):
        if kwargs.get("action") == "record-event":
            raise OSError("injected failure")
        return original_capture(*args, **kwargs)

    monkeypatch.setattr(service.capture, "capture", fail_before_commit)
    with pytest.raises(OSError):
        service.apply(revision, actor="operator", expected_fingerprint=preview["fingerprint"], work_intent="modify")
    # A prepared document is physically present, but no reader can see its new
    # answer or committed artifact until the single source marker is durable.
    assert len(list((tmp_path / "docs/deliverables/requirements").glob("*.md"))) == 2
    assert service.context()["question_refs"] == original["item_refs"]
    assert len(service.read()["artifacts"]) == 1
    monkeypatch.setattr(service.capture, "capture", original_capture)
    completed = service.apply(revision, actor="operator", expected_fingerprint=preview["fingerprint"], work_intent="modify")
    assert len(completed["item_refs"]) == 2
    assert service.context()["questions"][0]["answer"].endswith("未归档的课程。")
    assert (tmp_path / artifact["artifact"]["path"]).read_bytes() == first_bytes
    assert service.apply(revision, actor="operator", expected_fingerprint=preview["fingerprint"], work_intent="modify")["status"] == "unchanged"
    revised = next(a for a in service.read()["artifacts"] if a["artifact"]["previous_ref"])
    (tmp_path / revised["artifact"]["path"]).unlink()
    assert not service.context()["complete"]
    assert not service.context()["questions"]


def test_prepared_evidence_cannot_be_committed_without_real_file(tmp_path):
    service = Governance(tmp_path, "test-project")
    apply(service, request(service, "confirm", confirmation_scope="权限约束"))
    preview = service.preview(request(service, "artifact", document_key="requirements", document_kind="requirements"), actor="operator")
    with pytest.raises(ValueError, match="prepared_files_preview_only"):
        service.capture.capture(tmp_path, preview["event"], action="record-event", work_intent="modify",
            prepared_files={p: body.encode() for p, body in preview["prepared_files"].items()})


def test_cli_consumes_actual_context_from_project(tmp_path):
    import subprocess
    service = Governance(tmp_path, "test-project")
    receipt = apply(service, request(service, "confirm", confirmation_scope="权限约束"))
    result = subprocess.run([sys.executable, str(ROOT / "ops/scripts/manage-project-governance.py"),
        "context", "--root", str(tmp_path), "--project-key", "test-project"], text=True, capture_output=True)
    assert result.returncode == 0
    assert json.loads(result.stdout)["question_refs"] == receipt["item_refs"]


def test_installed_api_and_materialized_project_have_same_implementation(tmp_path):
    sys.path.insert(0, str(ROOT / "packages/mawflow-seed-kit/src"))
    from mawflow_seed_kit import materialize_project
    from mawflow_seed_kit.governance import project_governance
    from mawflow_seed_kit.commands.cli import main
    root = tmp_path / "fresh"
    materialize_project(root, project_key="fresh", name="新项目")
    for path in (ROOT / "ops/scripts/maw_governance").glob("*.py"):
        assert path.read_bytes() == (root / path.relative_to(ROOT)).read_bytes()
    service = project_governance(root, "fresh")
    receipt = apply(service, request(service, "confirm", confirmation_scope="新项目的角色权限约束"))
    assert Governance(root, "fresh").context()["question_refs"] == receipt["item_refs"]
    assert main(["--read-only", "project", "governance", "context", "--root", str(root), "--project-key", "fresh"]) == 0
    assert main(["--read-only", "project", "governance", "apply", "--root", str(root), "--project-key", "fresh"]) == 1


def test_module_context_includes_project_rules_and_public_work(tmp_path):
    service = Governance(tmp_path, "test-project")
    global_rule = apply(service, request(service, "confirm", confirmation_scope="全项目权限"))
    module_rule = apply(service, request(service, "confirm", request_id="module-rule", scope="module.courses",
        modules=["courses"], confirmation_scope="课程模块范围"))
    apply(service, request(service, "confirm", request_id="other-rule", scope="module.people",
        modules=["people"], confirmation_scope="人员模块范围"))
    context = service.context(scope="module.courses", module="courses")
    assert set(context["question_refs"]) == set(global_rule["item_refs"] + module_rule["item_refs"])
    apply(service, request(service, "work", task_ref="task-a", run_ref="run-a", phase="completed",
        goal="梳理课程权限", actions=["核对两个已确认口径"], result="已形成公开理解摘要", validation="尚未修改代码"))
    item = service.read()["tasks"][0]
    assert item["source"]["kind"] == "ai_analysis"
    assert item["activity"]["task_ref"] == "task-a"


def test_malformed_dialogue_is_isolated_not_project_crash(tmp_path):
    service = Governance(tmp_path, "test-project")
    result = apply(service, request(service, "message", message="权限有疑义", issue_type="ambiguity"))
    source = tmp_path / result["path"]
    meta = json.loads(source.read_text().split("\n---", 1)[0][4:])
    meta["content_contract"]["items"][0]["dialogue"]["resolves_issues"] = {"bad": "input"}
    source.write_text("---\n" + json.dumps(meta) + "\n---\n")
    assert service.read()["partial"]
    assert not service.context()["complete"]


def test_historical_task_and_risk_identifiers_are_not_misread_as_api_keys(tmp_path):
    service = Governance(tmp_path, "test-project")
    apply(service, request(service, question_key="task-source-authorization", request_id="course-integration-risk-report"))
    assert not service.read()["partial"]
    assert not service.capture.SENSITIVE.search("course-integration-risk-report-started")
    assert service.capture.SENSITIVE.search("sk-" + "abcdefghijklmnopqrstuv")


def test_requirement_survives_code_evolution_but_joint_document_integrity_is_required(tmp_path):
    (tmp_path / "code.py").write_text("before")
    service = Governance(tmp_path, "test-project")
    original = apply(service, request(service, "confirm", confirmation_scope="确认需求，现状仅为对照",
        claim_type="requirement", evidence_paths=[{"path": "code.py", "kind": "code"}]))
    generate = request(service, "artifact", document_key="requirements", document_kind="requirements",
        evidence_paths=[{"path": "code.py", "kind": "code"}], selected_question_refs=original["item_refs"])
    apply(service, generate)
    artifact = service.read()["artifacts"][0]
    revised = apply(service, request(service, "artifact", request_id="revise-normative", source_kind="user_statement",
        document_key="requirements", document_kind="requirements", previous_ref=artifact["id"],
        evidence_paths=[{"path": "code.py", "kind": "code"}], change_kind="substantive",
        review_refs=["review:test"], confirmation_scope="确认新需求与档案",
        question_changes=[{"question_key": "course.visibility", "scope": "project", "question": "课程列表显示哪些记录？",
            "answer": "只显示有权访问且未归档课程。", "category": "business", "claim_type": "requirement",
            "rationale": "明确归档规则", "base_refs": original["item_refs"]}]))
    (tmp_path / "code.py").write_text("after")
    assert service.context()["complete"]
    assert service.context()["question_refs"] == [revised["item_refs"][1]]
    doc = next(a for a in service.read()["artifacts"] if a["id"] == revised["item_refs"][0])
    assert doc["freshness"] == "changed"
    (tmp_path / doc["artifact"]["path"]).write_text("tampered")
    assert not service.context()["complete"]
    assert not service.context()["questions"]
