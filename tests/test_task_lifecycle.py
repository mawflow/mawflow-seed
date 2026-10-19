"""A successful run must not conceal stale evidence or uncollected resources."""
import json
from pathlib import Path
import sys
import runpy

import pytest
import yaml

from test_stage_standards import project, passed_verification, save

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages/mawflow-seed-kit/src"))
from mawflow_seed_kit import standards as s
from mawflow_seed_kit.template import materialize_project


def ready(root):
    task = passed_verification(root)
    task["lifecycle"] = {
        "schema": "mawflow.task_lifecycle.v1", "scope_revision": 1,
        "run_ref": "attempt.one", "stage": "ended", "condition": "active",
        "outcome": "succeeded", "task_closure": "ready_for_review",
        "human_acceptance_required": True, "required_axes": ["verification"],
        "completion_criteria": [{"key": "requested-result", "status": "passed",
                                 "evidence_refs": ["focused-result"]}],
        "resource_cleanup_status": "not_applicable", "resources": [],
        "next_action": "等待独立真人验收，不保持临时执行资源。",
    }
    return task


def browser(root, task, ownership="created"):
    path = "docs/standards/resource-receipt.json"
    (root / path).write_text('{"resource":"temporary-tab","state":"closed"}')
    receipt = {"run_ref": "attempt.one", "task_ref": task["task_ref"], "scope_revision": 1,
               "resource_key": "temporary-tab", "action": "close",
               "source_revision": task["scope"]["source_revision"], "environment": "local",
               "scope_hash": s.digest(json.dumps(task["scope"], sort_keys=True, ensure_ascii=False).encode()),
               "record_ref": "browser-adapter:fixture", "observed_at": "2026-10-19T22:00:00+08:00",
               "path": path, "content_hash": s.digest((root / path).read_bytes())}
    resource = {"key": "temporary-tab", "kind": "browser_tab", "ownership": ownership,
                "holder_run_ref": "attempt.one", "state": "released", "action": "close",
                "control_state": "released", "receipt": receipt}
    task["lifecycle"].update(resources=[resource], resource_cleanup_status="passed")
    return resource


def check(root, task):
    return s.validate_task(root, save(root, task))


def test_successful_attempt_does_not_close_business_task(project):
    task = ready(project)
    assert check(project, task)["status"] == "declaration_validated"
    task["lifecycle"].update(task_closure="closed", closure_ref="acceptance:claim")
    assert "lifecycle_human_acceptance_missing" in check(project, task)["issues"]


@pytest.mark.parametrize("field,value", [("run_ref", "attempt.other"), ("task_ref", "other-task"),
                                        ("scope_revision", 2), ("environment", "production"),
                                        ("source_revision", "1" * 40), ("scope_hash", "sha256:stale"),
                                        ("resource_key", "another-tab"), ("action", "stop"),
                                        ("observed_at", "2026-10-19T22:00:00")])
def test_resource_receipt_bound_to_attempt_scope_and_resource(project, field, value):
    task = ready(project)
    resource = browser(project, task)
    assert check(project, task)["status"] == "declaration_validated"
    resource["receipt"][field] = value
    assert "lifecycle_resource_receipt_invalid" in check(project, task)["issues"]
    if field == "scope_revision":
        resource["receipt"][field] = True
        assert "lifecycle_resource_receipt_invalid" in check(project, task)["issues"]


def test_changed_resource_evidence_is_not_reused(project):
    task = ready(project)
    resource = browser(project, task)
    (project / resource["receipt"]["path"]).write_text("changed")
    assert "lifecycle_resource_receipt_invalid" in check(project, task)["issues"]


@pytest.mark.parametrize("ownership", ["borrowed", "shared"])
def test_cleanup_cannot_authorize_closing_user_or_shared_tabs(project, ownership):
    task = ready(project)
    resource = browser(project, task, ownership)
    assert "lifecycle_borrowed_resource_destructive_action" in check(project, task)["issues"]
    resource["action"] = resource["receipt"]["action"] = "release_control"
    assert check(project, task)["status"] == "declaration_validated"


@pytest.mark.parametrize("state", ["pending_automatic", "failed", "unknown"])
def test_pending_or_failed_cleanup_does_not_hide_implementation_success(project, state):
    task = ready(project)
    resource = browser(project, task)
    resource.update(state=state, control_state=state if state != "failed" else "unknown")
    assert "lifecycle_cleanup_overstated" in check(project, task)["issues"]
    task["lifecycle"]["resource_cleanup_status"] = "partial"
    assert check(project, task)["status"] == "declaration_validated"


def test_retained_tab_requires_purpose_owner_review_and_control_evidence(project):
    task = ready(project)
    resource = browser(project, task)
    resource.update(state="retained", action="retain", control_state="unknown")
    report = check(project, task)
    assert "lifecycle_resource_retention_missing" in report["issues"]
    assert "lifecycle_browser_release_unverified" in report["issues"]
    resource["retention"] = {"purpose": "等待用户查看", "owner": "任务负责人", "review_condition": "查看后处理"}
    task["lifecycle"]["resource_cleanup_status"] = "partial"
    assert check(project, task)["status"] == "declaration_validated"


@pytest.mark.parametrize("outcome", ["partial", "failed", "cancelled", "interrupted"])
def test_non_successful_runs_can_end_without_false_closure(project, outcome):
    task = ready(project)
    task["lifecycle"].update(outcome=outcome, task_closure="open")
    assert check(project, task)["status"] == "declaration_validated"
    resource = browser(project, task)
    resource["state"] = "active"
    task["lifecycle"]["resource_cleanup_status"] = "pending"
    assert "lifecycle_ended_resource_active" in check(project, task)["issues"]


@pytest.mark.parametrize("condition", ["blocked", "waiting_human", "paused"])
def test_wait_and_pause_have_explicit_resume_basis(project, condition):
    task = ready(project)
    task["lifecycle"].update(stage="executing", outcome="pending", task_closure="open", condition=condition)
    assert "lifecycle_wait_reason_missing" in check(project, task)["issues"]
    task["lifecycle"]["reason_ref"] = "current-task:missing-input"
    if condition == "paused":
        assert "lifecycle_pause_authorization_missing" in check(project, task)["issues"]
        task["lifecycle"]["pause_authorization_ref"] = "current-user:pause"
    assert check(project, task)["status"] == "declaration_validated"


def test_success_requires_actual_criteria_and_required_axis(project):
    task = ready(project)
    task["lifecycle"]["completion_criteria"][0]["status"] = "pending"
    assert "lifecycle_completion_overstated" in check(project, task)["issues"]
    task = ready(project)
    task["lifecycle"]["required_axes"].append("deployment")
    assert "lifecycle_required_axis_incomplete" in check(project, task)["issues"]


def test_private_or_symlink_resource_receipts_are_rejected(project):
    task = ready(project)
    resource = browser(project, task)
    for ref in [".local/receipt.json", "../receipt.json", "/tmp/receipt.json", "prompts/receipt.json"]:
        resource["receipt"]["path"] = ref
        assert "lifecycle_resource_receipt_invalid" in check(project, task)["issues"]
    outside = project.parent / "outside.json"
    outside.write_text("private")
    (project / "docs/standards/link.json").symlink_to(outside)
    resource["receipt"]["path"] = "docs/standards/link.json"
    assert "lifecycle_resource_receipt_invalid" in check(project, task)["issues"]


def test_old_snapshot_is_compatible_but_not_adopted_and_check_is_read_only(project):
    task = passed_verification(project)
    ref = save(project, task)
    before = {p.relative_to(project): p.read_bytes() for p in project.rglob("*") if p.is_file()}
    result = s.validate_task(project, ref)
    assert result["status"] == "declaration_validated" and result["lifecycle_status"] == "not_adopted"
    assert before == {p.relative_to(project): p.read_bytes() for p in project.rglob("*") if p.is_file()}


def test_kit_materializes_contract_and_checks_without_host(tmp_path):
    target = tmp_path / "fresh"
    materialize_project(target, project_key="lifecycle", name="生命周期验收")
    for ref in ["docs/ai-coding/task-lifecycle.md", ".maw/schemas/task-lifecycle.schema.json",
                "docs/standards/examples/task-lifecycle.yaml"]:
        assert (target / ref).read_bytes() == (ROOT / ref).read_bytes()
    assert s.validate_task(target, "docs/standards/examples/task-lifecycle.yaml")["status"] == "declaration_validated"
    entry = yaml.safe_load((target / ".maw/agent-entry.yaml").read_text())
    assert "task_lifecycle" in entry["execution_contract"]
    manifest = json.loads((ROOT / "packages/mawflow-seed-kit/src/mawflow_seed_kit/manifest.json").read_text())
    assert all((target / ref).exists() for ref in manifest["required_paths"])


def test_older_installed_kit_cannot_silently_accept_lifecycle(project, monkeypatch, capsys):
    task = ready(project)
    ref = save(project, task)
    adapter = runpy.run_path(str(ROOT / "ops/scripts/manage-project-standards.py"))
    monkeypatch.delattr(s, "validate_lifecycle")
    monkeypatch.setattr(sys, "argv", ["adapter", "validate-task", "--root", str(project), "--input", ref])
    assert adapter["main"]() == 1
    result = json.loads(capsys.readouterr().out)
    assert result["lifecycle_status"] == "unsupported" and not result["changed_paths"]


def test_older_kit_adapter_does_not_expose_malformed_snapshot(project, monkeypatch, capsys):
    ref = "docs/standards/examples/malformed.yaml"
    (project / ref).write_text("schema: [broken\nprivate-content")
    adapter = runpy.run_path(str(ROOT / "ops/scripts/manage-project-standards.py"))
    monkeypatch.delattr(s, "validate_lifecycle")
    monkeypatch.setattr(sys, "argv", ["adapter", "validate-task", "--root", str(project), "--input", ref])
    assert adapter["main"]() == 1
    output = capsys.readouterr().out
    assert json.loads(output)["status"] == "blocked" and "private-content" not in output
