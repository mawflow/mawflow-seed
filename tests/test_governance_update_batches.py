"""Version nodes and external export never create or infer deployment success."""
from copy import deepcopy
from pathlib import Path
import sys

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ops/scripts"))
from maw_governance import Governance
from maw_governance.store import digest
from update_notes.store import validate


def note(root, key="change-one", external=True):
    (root / "docs").mkdir(exist_ok=True)
    (root / "docs/source.md").write_text("公开合成验证依据")
    result = {"schema_version": 1, "record_key": key, "record_type": "update_note", "operation": "append", "task_key": "task.one",
        "payload": {"schema": "mawflow.update_note.v2" if external else "mawflow.update_note.v1", "occurred_at": "2026-10-22T03:00:00+08:00",
            "title": "内部实现与代码定位", "summary": "更新了内部组件路径和回归证据", "category": "fixed", "module_key": "course",
            "module_name": "课程研发", "delivery_state": "implemented", "validation_state": "automated_passed", "importance": "normal",
            "audience": "project", "details": [{"label": "内部依据", "path": "docs/source.md"}]},
        "evidence_refs": [{"path": "docs/source.md", "kind": "repository_path"}]}
    if external:
        result["payload"]["external"] = {"title": "修复课程审核入口", "summary": "审核人可以从待办进入对应课程。", "impact": "仅影响课程审核。",
            "testing": ["建议核对审核人和无权限角色的入口"], "important": [], "limitations": ["仍需真人业务验收"], "authorship": "ai"}
    validate(root, result)
    directory = root / ".maw/changes"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / (key + ".yaml")).write_text(yaml.safe_dump(result, allow_unicode=True))
    return result


def request(service, operation="release_bind", **values):
    return {"operation": operation, "request_id": values.pop("request_id", operation), "occurred_at": "2026-10-22T04:00:00+08:00",
            "expected_source_version": service.read()["source_version"], **values}


def source(**values):
    return {"source_commit": "a" * 40, "dirty": False, "artifacts": [{"component": "server", "sha256": "b" * 64, "version": "1.2.0"}], **values}


TARGET = {"environment": "staging", "target": "test", "component": "server"}


def bind(service, **values):
    return request(service, members=["change-one"], candidate=source(), targets=[TARGET], release_version="1.2.0", **values)


def apply(service, payload):
    preview = service.preview(payload, actor="operator")
    return service.apply(payload, actor="operator", expected_fingerprint=preview["fingerprint"], work_intent="modify")


def test_version_persists_across_instances_retries_and_environment_promotion(tmp_path):
    note(tmp_path)
    service = Governance(tmp_path, "example")
    payload = bind(service)
    first = apply(service, payload)
    restarted = Governance(tmp_path, "example")
    assert apply(restarted, payload)["status"] == "unchanged"
    binding = restarted.release_versions()["bindings"][0]
    assert binding["version"] == "1.2.0" and binding["candidate"]["artifacts"][0]["version"] == "1.2.0"
    assert binding["execution_state"] == "requires_release_owner_readback" and not binding["owner_results"]
    promoted = bind(restarted, request_id="promote")
    promoted["targets"] = [{**TARGET, "environment": "production"}]
    apply(restarted, promoted)
    assert len(restarted.release_versions()["bindings"]) == 2
    different = bind(restarted, request_id="different")
    different["candidate"] = source(source_commit="c" * 40)
    with pytest.raises(ValueError, match="candidate_conflict"):
        restarted.preview(different, actor="operator")
    assert first["item_refs"]


def test_concurrent_version_allocation_and_dirty_snapshot_are_exact(tmp_path):
    note(tmp_path)
    service = Governance(tmp_path, "example")
    first = bind(service)
    first["release_version"] = ""
    competing = {**first, "request_id": "competing", "candidate": source(source_commit="c" * 40)}
    p1 = service.preview(first, actor="operator")
    p2 = service.preview(competing, actor="operator")
    service.apply(first, actor="operator", expected_fingerprint=p1["fingerprint"], work_intent="modify")
    with pytest.raises(ValueError, match="source_changed"):
        service.apply(competing, actor="operator", expected_fingerprint=p2["fingerprint"], work_intent="modify")
    competing["expected_source_version"] = service.read()["source_version"]
    apply(service, competing)
    assert {b["version"] for b in service.release_versions()["bindings"]} == {"2026.10.22.1", "2026.10.22.2"}
    dirty = bind(service, request_id="dirty")
    dirty["candidate"] = source(dirty=True)
    with pytest.raises(ValueError, match="snapshot_required"):
        service.preview(dirty, actor="operator")


def test_export_freezes_members_and_corrections_do_not_change_software_version(tmp_path):
    note(tmp_path)
    service = Governance(tmp_path, "example")
    binding = apply(service, bind(service))["item_refs"][0]
    batch = request(service, "update_batch", batch_key="release-one", batch_title="本批更新说明", members=["change-one"], release_ref=binding)
    first = apply(service, batch)
    exported = service.update_batches()["batches"][0]
    assert exported["version"] == "1.2.0" and "1.2.0-staging-r001.md" in exported["filename"]
    assert "审核人可以" in exported["content_markdown"] and "内部实现" not in exported["content_markdown"]
    assert "发布结果待回读" in exported["content_markdown"]
    old = (tmp_path / exported["markdown_path"]).read_bytes()
    note(tmp_path, key="later-change")
    assert service.update_batches()["batches"][0]["members"] == exported["members"]
    changed = request(service, "update_batch", request_id="correction", batch_key="release-one", members=["change-one"], release_ref=binding,
        previous_ref=first["item_refs"][0], external_overrides={"change-one": {"title": "课程审核入口说明", "summary": "更正业务表述，代码版本保持。", "authorship": "human"}})
    apply(service, changed)
    versions = service.update_batches()["batches"]
    assert {v["version"] for v in versions} == {"1.2.0"} and {v["revision"] for v in versions} == {1, 2}
    assert (tmp_path / exported["markdown_path"]).read_bytes() == old
    assert exported["source_map"][0]["record_key"] == "change-one"


def test_release_owner_partial_failure_and_summary_retry_never_deploy(tmp_path):
    note(tmp_path)
    service = Governance(tmp_path, "example")
    payload = bind(service)
    payload["targets"] = [TARGET, {**TARGET, "component": "client"}]
    binding = apply(service, payload)["item_refs"][0]
    calls = []
    def owner(manifest):
        calls.append(manifest["version"])
        return [{**TARGET, "state": "released", "receipt_ref": "release-owner:one", "candidate_hash": digest(manifest["candidate"])},
                {**TARGET, "component": "client", "state": "failed", "receipt_ref": "release-owner:two", "candidate_hash": digest(manifest["candidate"])}]
    service.release_reader = owner
    batch = request(service, "update_batch", batch_key="partial", members=["change-one"], release_ref=binding)
    apply(service, batch)
    summary = service.update_batches()["batches"][0]
    assert summary["observed_release_state"] == "partial" and "部分目标" in summary["content_markdown"]
    count = len(calls)
    assert apply(service, batch)["status"] == "unchanged" and len(calls) == count
    assert len(service.release_versions()["bindings"]) == 1


def test_legacy_stage_summary_has_no_fabricated_version_and_v1_rejects_new_fields(tmp_path):
    legacy = note(tmp_path, external=False)
    service = Governance(tmp_path, "example")
    apply(service, request(service, "update_batch", batch_key="stage", members=["change-one"]))
    summary = service.update_batches()["batches"][0]
    assert summary["version"] == "" and "阶段沟通摘要（未发布）" in summary["content_markdown"]
    assert summary["warnings"] and not service.release_versions()["bindings"]
    invalid = deepcopy(legacy)
    invalid["payload"]["external"] = {"title": "新表述", "summary": "不能写进旧协议"}
    with pytest.raises(ValueError, match="requires_v2"):
        validate(tmp_path, invalid)


def test_missing_or_other_release_members_are_rejected(tmp_path):
    note(tmp_path)
    note(tmp_path, key="other-change")
    service = Governance(tmp_path, "example")
    binding = apply(service, bind(service))["item_refs"][0]
    with pytest.raises(ValueError, match="outside_release"):
        service.preview(request(service, "update_batch", batch_key="bad", members=["other-change"], release_ref=binding), actor="operator")


def test_previous_candidate_success_cannot_prove_new_candidate_release(tmp_path):
    note(tmp_path)
    service = Governance(tmp_path, "example")
    binding = apply(service, bind(service))["item_refs"][0]
    service.release_reader = lambda manifest: [{**TARGET, "state": "released", "receipt_ref": "release-owner:old",
                                              "candidate_hash": "f" * 64}]
    apply(service, request(service, "update_batch", batch_key="stale-result", members=["change-one"], release_ref=binding))
    summary = service.update_batches()["batches"][0]
    assert summary["observed_release_state"] == "unknown" and "发布状态：已发布" not in summary["content_markdown"]


def test_summary_failure_recovers_without_rebinding_release(tmp_path, monkeypatch):
    note(tmp_path)
    service = Governance(tmp_path, "example")
    binding = apply(service, bind(service))["item_refs"][0]
    payload = request(service, "update_batch", batch_key="recover", members=["change-one"], release_ref=binding)
    capture = service.capture.capture
    def fail(*args, **kwargs):
        if kwargs.get("action") == "record-event":
            raise OSError("summary registration interrupted")
        return capture(*args, **kwargs)
    monkeypatch.setattr(service.capture, "capture", fail)
    with pytest.raises(OSError):
        apply(service, payload)
    assert not service.update_batches()["batches"] and len(service.release_versions()["bindings"]) == 1
    monkeypatch.setattr(service.capture, "capture", capture)
    apply(service, payload)
    assert len(service.update_batches()["batches"]) == len(service.release_versions()["bindings"]) == 1


@pytest.mark.parametrize("operation", ["release_bind", "update_batch"])
def test_confirmation_survives_host_json_round_trip(tmp_path, operation):
    """Host persists preview payloads with sorted keys before human confirmation."""
    import json
    note(tmp_path)
    service = Governance(tmp_path, "example")
    if operation == "release_bind":
        payload = bind(service)
    else:
        binding = apply(service, bind(service))["item_refs"][0]
        payload = request(service, "update_batch", batch_key="round-trip", members=["change-one"],
            release_ref=binding, external_overrides={"change-one": {"summary": "公开业务说明", "title": "人工措辞", "authorship": "human"}})
    preview = service.preview(payload, actor="operator")
    persisted = json.loads(json.dumps(payload, sort_keys=True))
    reread = service.preview(persisted, actor="operator")
    assert reread["fingerprint"] == preview["fingerprint"]
    assert reread["prepared_files"] == preview["prepared_files"]
    result = service.apply(persisted, actor="operator", expected_fingerprint=preview["fingerprint"], work_intent="modify")
    assert result["item_refs"]
