"""New projects receive the same protocol; old real projects cannot silently upgrade writers."""
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ops/scripts"))
sys.path.insert(0, str(ROOT / "packages/mawflow-seed-kit/src"))
from maw_governance import Governance
from mawflow_seed_kit import materialize_project
from mawflow_seed_kit.governance import project_governance


def test_real_legacy_project_is_readable_but_requires_adoption_before_new_write(tmp_path):
    (tmp_path / ".maw").mkdir()
    (tmp_path / ".maw/project.yaml").write_text("project:\n  key: legacy\n")
    service = Governance(tmp_path, "legacy")
    assert service.read()["adoption"]["status"] == "not_adopted"
    assert service.reading()["total"] == 0
    payload = {"operation": "confirm", "request_id": "manual-create", "occurred_at": "2026-10-22T04:00:00+08:00",
        "expected_source_version": service.read()["source_version"], "question_key": "business.scope", "scope": "project",
        "question": "项目负责什么？", "answer": "仅负责明确授权业务。", "category": "business", "claim_type": "requirement",
        "rationale": "人工直接录入", "confirmation_scope": "确认所见正文与范围"}
    with pytest.raises(ValueError, match="project_upgrade_required"):
        service.preview(payload, actor="human")
    assert not (tmp_path / "docs").exists()
    (tmp_path / ".maw/project-governance.yaml").write_bytes((ROOT / ".maw/project-governance.yaml").read_bytes())
    preview = service.preview(payload, actor="human")
    service.apply(payload, actor="human", expected_fingerprint=preview["fingerprint"], work_intent="modify")
    assert service.reading()["total"] == 1


def test_materialized_project_and_installed_kit_support_all_four_domains(tmp_path):
    root = tmp_path / "fresh"
    materialize_project(root, project_key="fresh", name="四项治理物化验收")
    engine = project_governance(root, "fresh")
    assert engine.read()["adoption"]["status"] == "adopted"
    assert "natural_language_learning.v1" in engine.read()["capabilities"]
    manifest = json.loads((ROOT / "PUBLIC_PAYLOAD_MANIFEST.json").read_text())
    for path in (ROOT / "ops/scripts/maw_governance").glob("*.py"):
        relative = path.relative_to(ROOT).as_posix()
        assert relative in manifest["required_paths"]
        assert path.read_bytes() == (root / relative).read_bytes()
    assert engine.templates()["version"] == "delivery-v1"
    assert engine.baseline(mode="audit")["trust_boundary"]["project_mutated"] is False
    assert engine.library()["total"] == 0 and engine.release_versions()["bindings"] == []
