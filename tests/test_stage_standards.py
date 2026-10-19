"""Lifecycle evidence failures must not turn declarations into successful work."""
from copy import deepcopy
import json
from pathlib import Path
import shutil
import sys

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages/mawflow-seed-kit/src"))
from mawflow_seed_kit import standards as s
from mawflow_seed_kit.template import materialize_project


@pytest.fixture
def project(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    shutil.copytree(ROOT / "docs/standards", root / "docs/standards")
    (root / "docs/ai-coding").mkdir()
    shutil.copyfile(ROOT / "docs/ai-coding/task-lifecycle.md", root / "docs/ai-coding/task-lifecycle.md")
    (root / s.INDEX).unlink()
    (root / ".maw").mkdir()
    shutil.copyfile(ROOT / ".maw/standards.yaml", root / s.CATALOG)
    return root


def snapshot(root):
    return yaml.safe_load((root / "docs/standards/examples/small-change.yaml").read_text())


def save(root, task):
    path = "docs/standards/examples/test-task.yaml"
    (root / path).write_text(yaml.safe_dump(task))
    return path


def passed_verification(root):
    task = snapshot(root)
    path = "docs/standards/result.txt"
    (root / path).write_text("fixture evidence only")
    scope_hash = s.digest(json.dumps(task["scope"], sort_keys=True, ensure_ascii=False).encode())
    task["states"]["verification"] = "passed"
    task["verification"]["suites"] = [
        {"key": "focused", "status": "passed", "evidence_refs": ["focused-result"]}
    ]
    task["evidence"] = [
        {"key": "focused-result", "axis": "verification", "status": "passed",
         "path": path, "content_hash": s.digest((root / path).read_bytes()),
         "source_revision": task["scope"]["source_revision"], "environment": "local",
         "scope_hash": scope_hash, "record_ref": "test-run:fixture"}
    ]
    return task


def test_context_is_scoped_and_does_not_grant_authority(project):
    selected = s.context(project, "testing", "small_change", "test")
    keys = {rule["key"] for rule in selected["rules"]}
    assert "std.test-scope" in keys and "std.customer-candidate" not in keys
    assert not selected["authorization_granted"]
    assert s.inspect_catalog(project)["status"] == "ready"


def test_absent_adoption_is_visible_and_read_only(tmp_path):
    assert s.inspect_catalog(tmp_path)["status"] == "not_adopted"
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("change", ["duplicate", "missing_authority", "unknown_phase"])
def test_invalid_catalog_cannot_generate_index(project, change):
    data = yaml.safe_load((project / s.CATALOG).read_text())
    if change == "duplicate":
        data["rules"].append(deepcopy(data["rules"][0]))
    elif change == "missing_authority":
        data["rules"][0]["authority"] = "docs/standards/missing.md"
    else:
        data["rules"][0]["applies_to_phases"] = ["invented"]
    (project / s.CATALOG).write_text(yaml.safe_dump(data))
    assert s.inspect_catalog(project)["status"] == "blocked"
    with pytest.raises(ValueError):
        s.render(project)
    assert not (project / s.INDEX).exists()


@pytest.mark.parametrize("ref", [".local/private.yaml", "prompts/run.md", "../outside",
                                  "/absolute", "docs/archive/old.md", ".env",
                                  "docs/private.key"])
def test_catalog_cannot_route_into_protected_sources(project, ref):
    data = yaml.safe_load((project / s.CATALOG).read_text())
    data["rules"][0]["authority"] = ref
    (project / s.CATALOG).write_text(yaml.safe_dump(data))
    with pytest.raises(ValueError):
        s.inspect_catalog(project)


def test_symlink_cannot_redirect_authority(project, tmp_path):
    outside = tmp_path / "outside.md"
    outside.write_text("not an allowed source")
    (project / "docs/standards/general.md").unlink()
    (project / "docs/standards/general.md").symlink_to(outside)
    with pytest.raises(ValueError):
        s.inspect_catalog(project)


def test_render_preview_staleness_and_idempotence(project):
    preview = s.render(project)
    assert not (project / s.INDEX).exists()
    s.render(project, True, preview["fingerprint"])
    assert s.render(project)["proposed_paths"] == []
    assert s.render(project, True, s.render(project)["fingerprint"])["changed_paths"] == []
    (project / s.INDEX).write_text("concurrent edit")
    with pytest.raises(ValueError, match="stale_preview"):
        s.render(project, True, preview["fingerprint"])
    assert (project / s.INDEX).read_text() == "concurrent edit"


def test_empty_tests_remain_pending_and_not_accepted(project):
    task = snapshot(project)
    assert s.validate_task(project, save(project, task))["status"] == "declaration_validated"
    task["states"]["verification"] = "passed"
    result = s.validate_task(project, save(project, task))
    assert result["status"] == "blocked"
    assert "empty_suites_are_not_passed" in result["issues"]


def test_valid_verification_never_advances_delivery_or_human_axis(project):
    task = passed_verification(project)
    result = s.validate_task(project, save(project, task))
    assert result["status"] == "declaration_validated"
    assert not result["authorization_granted"]
    assert task["states"]["deployment"] == task["states"]["human_acceptance"] == "pending"


@pytest.mark.parametrize("change", ["content", "source", "environment", "scope", "suite"])
def test_stale_or_wrong_evidence_is_blocked(project, change):
    task = passed_verification(project)
    if change == "content":
        (project / task["evidence"][0]["path"]).write_text("changed")
    elif change == "source":
        task["evidence"][0]["source_revision"] = "a" * 40
    elif change == "environment":
        task["evidence"][0]["environment"] = "staging"
    elif change == "scope":
        task["scope"]["module_keys"] = ["another-module"]
    else:
        task["verification"]["suites"][0]["status"] = "pending"
    assert s.validate_task(project, save(project, task))["status"] == "blocked"


def test_release_evidence_cannot_substitute_for_tests(project):
    task = passed_verification(project)
    task["evidence"][0]["axis"] = "deployment"
    result = s.validate_task(project, save(project, task))
    assert "suite_evidence_missing" in result["issues"]
    assert "axis_evidence_missing:verification" in result["issues"]


def test_read_permission_cannot_become_modification_or_deployment(project):
    task = snapshot(project)
    task["scope"]["write_paths"] = ["docs/standards"]
    assert "read_only_has_write_paths" in s.validate_task(project, save(project, task))["issues"]
    task["scope"]["write_paths"] = []
    task["task_kind"] = "deploy"
    result = s.validate_task(project, save(project, task))
    assert "operation_outside_declared_authorization" in result["issues"]
    task["authorization"]["allowed_actions"] = ["deploy"]
    result = s.validate_task(project, save(project, task))
    assert "external_operation_requires_modify_declaration" in result["issues"]


def test_passed_human_acceptance_requires_own_confirmation(project):
    task = passed_verification(project)
    task["evidence"][0]["axis"] = "human_acceptance"
    task["states"]["verification"] = "pending"
    task["verification"]["suites"] = []
    task["states"]["human_acceptance"] = "passed"
    assert "human_confirmation_missing:focused-result" in s.validate_task(project, save(project, task))["issues"]


def test_blocked_paths_and_source_revision_are_checked(project):
    task = snapshot(project)
    task["authorization"]["mode"] = "modify"
    task["task_kind"] = "modify"
    task["scope"]["write_paths"] = ["docs/standards/general.md"]
    task["scope"]["blocked_paths"] = ["docs/standards"]
    task["scope"]["source_revision"] = ""
    issues = s.validate_task(project, save(project, task))["issues"]
    assert "write_path_blocked" in issues and "source_revision_invalid" in issues


def test_actual_kit_materialization_has_same_stage_rules_and_empty_evidence(tmp_path):
    root = tmp_path / "materialized"
    materialize_project(root, project_key="standards-fixture", name="规范验证项目")
    assert s.inspect_catalog(root)["status"] == "ready"
    assert s.render(root)["proposed_paths"] == []
    result = s.validate_task(root, "docs/standards/examples/formal-delivery.yaml")
    assert result["status"] == "declaration_validated"
    assert not result["valid_evidence_keys"] and not result["authorization_granted"]
