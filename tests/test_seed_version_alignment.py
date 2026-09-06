from __future__ import annotations

import importlib.util
from pathlib import Path
import shutil
import sys
import yaml


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
        "packages/mawflow-seed-kit/src/mawflow_seed_kit/resources/agent-contract.v1.json",
        "packages/mawflow-seed-kit/src/mawflow_seed_kit/template/.maw/seed.lock",
        "packages/mawflow-seed-kit/src/mawflow_seed_kit/template/.maw/template-source.yaml",
    ]
    for relative in paths:
        source = ROOT / relative
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        if relative == ".maw-template/template.yaml" and not source.exists():
            # The public tree deliberately omits internal maintainer metadata.
            version = (ROOT / "TEMPLATE_VERSION").read_text().strip().removeprefix("v")
            destination.write_text(yaml.safe_dump({"template": {"seed_contract": {
                "seed_version": version, "contract_version": 2,
                "kit_package": "mawflow-seed-kit==" + version,
                "catalog_source": "packages/mawflow-seed-kit/src/mawflow_seed_kit/resources/contracts/v2/catalog.json",
            }}}))
        else:
            shutil.copy2(source, destination)


def test_current_seed_release_family_is_aligned() -> None:
    result = MODULE.check_alignment(ROOT)

    assert result["status"] == "ready"
    assert result["observations"]["release_version"] == "2.8.0"
    assert result["observations"]["seed_contract_version"] == 2
    assert result["observations"]["template_metadata_checked"] is (ROOT / ".maw-template/template.yaml").is_file()


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


def test_template_source_baseline_must_match_seed_release(tmp_path: Path) -> None:
    _copy_alignment_inputs(tmp_path)
    template_source_path = (
        tmp_path
        / "packages/mawflow-seed-kit/src/mawflow_seed_kit/template/.maw/template-source.yaml"
    )
    text = template_source_path.read_text(encoding="utf-8")
    template_source_path.write_text(
        text.replace("applied_version: 2.8.0", "applied_version: 2.3.1"),
        encoding="utf-8",
    )

    result = MODULE.check_alignment(tmp_path)

    assert result["status"] == "blocked"
    assert any(
        item["code"] == "seed_release_version_mismatch"
        and "template_source.applied_version=2.3.1" in item["actual"]
        for item in result["blockers"]
    )


def test_agent_contract_tampering_blocks_release(tmp_path: Path) -> None:
    _copy_alignment_inputs(tmp_path)
    contract = tmp_path / "packages/mawflow-seed-kit/src/mawflow_seed_kit/resources/agent-contract.v1.json"
    contract.write_text(contract.read_text() + "\n")
    result = MODULE.check_alignment(tmp_path)
    assert any(item["code"] == "seed_agent_contract_fingerprint_mismatch" for item in result["blockers"])
