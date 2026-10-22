import json
from pathlib import Path
import subprocess

import pytest

from test_governance_update_batches import Governance, note, bind, request, source, TARGET
from maw_governance import release_execution as execution


def prepare(engine, **values):
    return execution.prepare(engine, bind(engine, **values), actor="release-owner", work_intent="modify")


def test_prebinding_does_not_dirty_frozen_source_and_retry_reuses_version(tmp_path):
    note(tmp_path)
    (tmp_path / ".gitignore").write_text(".local/\n")
    for command in [["init", "-q"], ["config", "user.name", "Synthetic Release Test"], ["config", "user.email", "release@example.invalid"],
                    ["add", "."], ["commit", "-qm", "synthetic source"]]:
        subprocess.run(["git", "-C", str(tmp_path), *command], check=True, capture_output=True)
    engine = Governance(tmp_path, "example")
    first = prepare(engine)
    second = prepare(engine, request_id="retry")
    assert first["version"] == second["version"] == "1.2.0" and second["reused"]
    assert not subprocess.check_output(["git", "-C", str(tmp_path), "status", "--porcelain"])
    assert engine.release_versions()["execution_intents"][0]["version"] == "1.2.0"
    assert not engine.release_versions()["bindings"]


def test_pending_versions_allocate_atomically_and_environments_keep_version(tmp_path):
    note(tmp_path); engine = Governance(tmp_path, "example")
    one = bind(engine); one["release_version"] = ""
    first = execution.prepare(engine, one, actor="release-owner", work_intent="modify")
    two = {**one, "request_id": "other", "candidate": source(source_commit="c" * 40)}
    second = execution.prepare(engine, two, actor="release-owner", work_intent="modify")
    promoted = {**one, "request_id": "promoted", "targets": [{**TARGET, "environment": "production"}]}
    promotion = execution.prepare(engine, promoted, actor="release-owner", work_intent="modify")
    assert {first["version"], second["version"]} == {"2026.10.22.1", "2026.10.22.2"}
    assert promotion["version"] == first["version"]
    with pytest.raises(ValueError, match="candidate_conflict"):
        execution.prepare(engine, {**one, "request_id": "bad", "release_version": first["version"], "candidate": source(source_commit="c" * 40)}, actor="release-owner", work_intent="modify")


def test_closeout_and_summary_retry_are_idempotent_and_never_deploy(tmp_path, monkeypatch):
    note(tmp_path); engine = Governance(tmp_path, "example"); intent = prepare(engine)
    original = engine.apply
    def fail_batch(payload, **kwargs):
        if payload["operation"] == "update_batch":
            raise OSError("synthetic summary append interrupted")
        return original(payload, **kwargs)
    monkeypatch.setattr(engine, "apply", fail_batch)
    first = execution.finalize(engine, intent["key"], work_intent="modify")
    assert first["status"] == "summary_pending" and first["business_execution_repeated"] is False
    assert len(engine.release_versions()["bindings"]) == 1
    monkeypatch.setattr(engine, "apply", original)
    second = execution.finalize(engine, intent["key"], work_intent="modify")
    again = execution.finalize(engine, intent["key"], work_intent="modify")
    assert second["status"] == again["status"] == "registered"
    assert not engine.release_versions()["execution_intents"]
    assert len(engine.release_versions()["bindings"]) == len(engine.update_batches()["batches"]) == 1
    assert engine.update_batches()["batches"][0]["observed_release_state"] == "unknown"


def test_frozen_members_and_intent_hash_are_verified_before_closeout(tmp_path):
    note(tmp_path); engine = Governance(tmp_path, "example"); intent = prepare(engine)
    note(tmp_path, key="later-change")
    execution.finalize(engine, intent["key"], work_intent="modify")
    assert [m["record_key"] for m in engine.update_batches()["batches"][0]["members"]] == ["change-one"]
    path = execution.directory(engine) / (intent["key"] + ".json")
    value = json.loads(path.read_text()); value["version"] = "tampered"
    path.write_text(json.dumps(value))
    with pytest.raises(ValueError, match="changed"):
        execution.finalize(engine, intent["key"], work_intent="modify")


def test_original_executor_receipts_keep_partial_and_failed_targets_separate(tmp_path):
    note(tmp_path); engine = Governance(tmp_path, "example")
    payload = bind(engine); payload["targets"] = [TARGET, {**TARGET, "component": "client"}]
    intent = execution.prepare(engine, payload, actor="release-owner", work_intent="modify")
    engine.release_reader = lambda binding: execution.read_owner_results(engine, binding)
    execution.record_owner_result(engine, intent["key"], [{**TARGET, "state": "released"}], exit_code=0, work_intent="modify")
    execution.record_owner_result(engine, intent["key"], [{**TARGET, "component": "client", "state": "failed"}], exit_code=1, work_intent="modify")
    result = execution.finalize(engine, intent["key"], work_intent="modify")
    assert result["status"] == "registered"
    assert engine.update_batches()["batches"][0]["observed_release_state"] == "partial"
    assert engine.release_versions()["bindings"][0]["owner_state"] == "partial"
    with pytest.raises(ValueError, match="verification_failed"):
        execution.record_owner_result(engine, intent["key"], [{**TARGET, "state": "released"}], exit_code=1, work_intent="modify")


def test_later_owner_readback_appends_content_revision_and_preserves_export(tmp_path):
    note(tmp_path); engine = Governance(tmp_path, "example"); intent = prepare(engine)
    engine.release_reader = lambda binding: execution.read_owner_results(engine, binding)
    execution.finalize(engine, intent["key"], work_intent="modify")
    first = engine.update_batches()["batches"][0]
    original = (tmp_path / first["markdown_path"]).read_bytes()
    execution.record_owner_result(engine, intent["key"], [{**TARGET, "state": "released"}], exit_code=0, work_intent="modify")
    execution.finalize(engine, intent["key"], work_intent="modify")
    execution.finalize(engine, intent["key"], work_intent="modify")
    rows = engine.update_batches()["batches"]
    assert len(rows) == 2 and {r["version"] for r in rows} == {"1.2.0"}
    assert {r["observed_release_state"] for r in rows} == {"unknown", "released"}
    assert (tmp_path / first["markdown_path"]).read_bytes() == original
