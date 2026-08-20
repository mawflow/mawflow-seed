from __future__ import annotations

import importlib.util
from pathlib import Path
import shutil
import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "ops/scripts/check-seed-version-alignment.py"
SPEC = importlib.util.spec_from_file_location("check_seed_version_alignment", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def _copy_alignment_inputs(target: Path) -> None:
    paths = [
        "TEMPLATE_VERSION",
        "PUBLIC_PAYLOAD_MANIFEST.json",
        ".maw/seed.lock",
        ".maw-template/template.yaml",
        "packages/mawflow-seed-kit/pyproject.toml",
        "packages/mawflow-seed-kit/src/mawflow_seed_kit/manifest.json",
        "packages/mawflow-seed-kit/src/mawflow_seed_kit/catalog.py",
        "packages/mawflow-seed-kit/src/mawflow_seed_kit/__init__.py",
        "packages/mawflow-seed-kit/src/mawflow_seed_kit/resources/contracts/v2/catalog.json",
        "packages/mawflow-seed-kit/src/mawflow_seed_kit/template/.maw/seed.lock",
    ]
    for relative in paths:
        source = ROOT / relative
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def test_current_seed_release_family_is_aligned() -> None:
    result = MODULE.check_alignment(ROOT)

    assert result["status"] == "ready"
    assert result["observations"]["release_version"] == "2.3.2"
    assert result["observations"]["seed_contract_version"] == 2
    assert result["observations"]["template_metadata_checked"] is True


def test_public_payload_can_validate_without_internal_template_metadata(
    tmp_path: Path,
) -> None:
    _copy_alignment_inputs(tmp_path)
    (tmp_path / ".maw-template/template.yaml").unlink()

    result = MODULE.check_alignment(tmp_path)

    assert result["status"] == "ready"
    assert result["observations"]["template_metadata_checked"] is False


def test_major_upgrade_blocks_until_all_three_versions_move_together(tmp_path: Path) -> None:
    _copy_alignment_inputs(tmp_path)
    (tmp_path / "TEMPLATE_VERSION").write_text("v3.0.0\n", encoding="utf-8")

    result = MODULE.check_alignment(tmp_path)

    assert result["status"] == "blocked"
    codes = {item["code"] for item in result["blockers"]}
    assert "seed_release_version_mismatch" in codes
    assert "seed_contract_major_mismatch" in codes
    assert "seed_contract_catalog_source_mismatch" in codes
