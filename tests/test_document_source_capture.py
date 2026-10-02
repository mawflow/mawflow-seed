"""Exercise durable source capture, trust boundaries and real Kit materialization."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("capture_source", ROOT / "ops/scripts/capture-document-source.py")
capture_source = importlib.util.module_from_spec(spec)
spec.loader.exec_module(capture_source)


@pytest.fixture
def payload():
    return json.loads((ROOT / "docs/intake/source-template.json").read_text())


def record(root, payload):
    return capture_source.capture(root, payload, action="record", work_intent="modify")


def test_preview_readonly_idempotency_conflict_and_atomic_concurrency(tmp_path, payload):
    assert capture_source.capture(tmp_path, payload)["status"] == "planned"
    assert not list(tmp_path.iterdir())
    with pytest.raises(ValueError, match="modify_intent_required"):
        capture_source.capture(tmp_path, payload, action="record")
    with ThreadPoolExecutor(max_workers=5) as pool:
        results = list(pool.map(lambda _: record(tmp_path, payload), range(5)))
    assert [r["status"] for r in results].count("recorded") == 1
    assert len({r["sha256"] for r in results}) == 1
    original = (tmp_path / results[0]["path"]).read_bytes()
    assert original.endswith(b"\n") and not original.endswith(b"\n\n")
    payload["title"] = "不同内容"
    with pytest.raises(ValueError, match="capture_id_conflict"):
        record(tmp_path, payload)
    assert (tmp_path / results[0]["path"]).read_bytes() == original
    assert len(list((tmp_path / "docs/intake").iterdir())) == 1


@pytest.mark.parametrize("path", ["../outside.txt", "/tmp/private", ".local/config.yaml", "prompts/a.md", "docs/archive/a.md"])
def test_forbidden_evidence_does_not_write(tmp_path, payload, path):
    payload["items"][0]["evidence"] = [{"path": path, "kind": "document"}]
    with pytest.raises(ValueError):
        record(tmp_path, payload)
    assert not (tmp_path / "docs/intake").exists()


def test_symlink_destination_and_evidence_are_rejected(tmp_path, payload):
    outside = tmp_path / "outside"
    outside.mkdir()
    (tmp_path / "docs").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        record(tmp_path, payload)
    assert not list(outside.iterdir())
    (tmp_path / "docs").unlink()
    (tmp_path / "actual.md").write_text("safe")
    (tmp_path / "linked.md").symlink_to(tmp_path / "actual.md")
    payload["items"][0]["evidence"] = [{"path": "linked.md", "kind": "document"}]
    with pytest.raises(ValueError, match="symlink"):
        record(tmp_path, payload)


@pytest.mark.parametrize("value", ["password" + "=do-not-print-this", "Bearer do-not-print-this", "https://user:private@example.com", "/" + "home/private/path"])
def test_secrets_are_rejected_without_echo(tmp_path, payload, value):
    payload["source"]["excerpt"] = value
    result = subprocess.run([sys.executable, str(ROOT / "ops/scripts/capture-document-source.py"), "record", "--root", str(tmp_path), "--input", "-", "--work-intent", "modify"], input=json.dumps(payload), text=True, capture_output=True)
    assert result.returncode == 1
    assert json.loads(result.stdout)["reason"] == "sensitive_content_forbidden"
    assert value not in result.stdout + result.stderr
    assert not list(tmp_path.iterdir())


def test_confirmation_and_completion_require_evidence(tmp_path, payload):
    item = payload["items"][0]
    item["decision_status"] = "confirmed"
    item["confirmation"] = {"basis": "explicit_user", "ref": "当前用户消息", "scope": "仅需求"}
    with pytest.raises(ValueError, match="confirmation_evidence_required"):
        record(tmp_path, payload)
    payload["source"]["kind"] = "user_statement"
    item["implementation_status"] = "implemented"
    with pytest.raises(ValueError, match="implementation_evidence_required"):
        record(tmp_path, payload)
    (tmp_path / "code.py").write_text("pass\n")
    item["evidence"] = [{"path": "code.py", "kind": "code"}]
    item["audit_status"] = "passed"
    with pytest.raises(ValueError, match="audit_evidence_required"):
        record(tmp_path, payload)
    item["audit_status"] = "pending"
    result = record(tmp_path, payload)
    data = json.loads((tmp_path / result["path"]).read_text().split("---", 2)[1])["content_contract"]
    assert len(data["items"][0]["evidence"][0]["sha256"]) == 64


def test_correction_preserves_source_and_requires_existing_item(tmp_path, payload):
    payload["source"]["excerpt"] = "原始说明包含 --- 分隔文字"
    record(tmp_path, payload)
    corrected = deepcopy(payload)
    corrected["capture_id"] = "correction-001"
    corrected["items"][0]["supersedes"] = payload["capture_id"] + "#missing"
    with pytest.raises(ValueError, match="supersedes_item_missing"):
        record(tmp_path, corrected)
    corrected["items"][0]["supersedes"] = payload["capture_id"] + "#scope-question"
    assert record(tmp_path, corrected)["status"] == "recorded"
    assert record(tmp_path, payload)["status"] == "unchanged"


def test_generated_record_respects_reader_limit_without_partial_file(tmp_path, payload):
    (tmp_path / "reference.md").write_text("evidence")
    prototype = payload["items"][0]
    prototype["statement"] = "来源正文" * 400
    prototype["evidence"] = [{"path": "reference.md", "kind": "document"}] * 20
    payload["items"] = [{**deepcopy(prototype), "key": f"entry-{n}"} for n in range(40)]
    with pytest.raises(ValueError, match="record_too_large"):
        record(tmp_path, payload)
    assert not (tmp_path / "docs/intake").exists()


def test_git_and_kit_have_same_protocol_and_working_capture(tmp_path, payload):
    sys.path.insert(0, str(ROOT / "packages/mawflow-seed-kit/src"))
    from mawflow_seed_kit import materialize_project, inspect_agent_readiness
    project = tmp_path / "fresh"
    materialize_project(project, project_key="capture-acceptance", name="来源收录验收")
    assert inspect_agent_readiness(project)["status"] == "ready"
    manifest = json.loads((ROOT / "PUBLIC_PAYLOAD_MANIFEST.json").read_text())
    for path in ("ops/scripts/capture-document-source.py", "docs/ai-coding/document-source-capture.md", "docs/intake/README.md", "docs/intake/source-template.json"):
        assert path in manifest["required_paths"]
        assert (ROOT / path).read_bytes() == (project / path).read_bytes()
    assert "capture_document_sources" in (project / ".maw/agent-rules.yaml").read_text()
    assert "document-source-capture.md" in (project / "AGENTS.md").read_text()
    result = subprocess.run([sys.executable, str(project / "ops/scripts/capture-document-source.py"), "record", "--root", str(project), "--input", "-", "--work-intent", "modify"], input=json.dumps(payload), text=True, capture_output=True)
    assert result.returncode == 0, result.stdout
    assert json.loads(result.stdout)["status"] == "recorded"
