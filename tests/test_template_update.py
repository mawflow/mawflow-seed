import json
from pathlib import Path
import subprocess

import pytest
import yaml

from mawflow_seed_kit import materialize_project
from mawflow_seed_kit.commands import template_update as updater
from mawflow_seed_kit.commands.template_sources import template_tree_sha256


def _commit(root):
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                    "commit", "-qm", "Metadata baseline"], cwd=root, check=True)


def _stale_metadata(root, version):
    lock_path, source_path = root / ".maw/seed.lock", root / ".maw/template-source.yaml"
    lock, source = yaml.safe_load(lock_path.read_text()), yaml.safe_load(source_path.read_text())
    identity = {"kind": "package", "template": "mawflow-seed-kit", "index_url": "https://example.invalid/simple",
                "source_commit": "project-source-identity", "custom": {"keep": True}}
    stale = {**identity, "version": "2.17.0", "template_version": "2.17.0",
             "template_tree_sha256": "sha256:" + "0" * 64}
    lock.update(seed_version=version, source=dict(stale))
    source["template_source"].update(applied_version=version, distribution=dict(stale),
                                     source_channel="public_seed", version="latest_verified_stable")
    lock_path.write_text(yaml.safe_dump(lock, sort_keys=False))
    source_path.write_text(yaml.safe_dump(source, sort_keys=False))
    _commit(root)
    return identity, {p: p.read_bytes() for p in (lock_path, source_path)}


@pytest.mark.parametrize("previous", ["2.17.0", "2.17.1", "current"])
def test_upgrade_converges_distribution_and_tree_with_recovery(fixture, previous):
    root, sources = fixture
    identity, originals = _stale_metadata(root, updater.SEED_VERSION if previous == "current" else previous)
    protected = {p: p.read_bytes() for p in (root / "README.md", root / ".maw/project.yaml",
                                            root / ".maw/components.yaml", root / ".maw/modules.yaml")}
    plan = updater.update_template(root, **sources)
    applied = updater.update_template(root, execute=True, confirmation=plan["confirmation_required"], **sources)
    expected = {"version": updater.SEED_VERSION, "template_version": updater.SEED_VERSION,
                "template_tree_sha256": template_tree_sha256(sources["target_template"])}
    lock = yaml.safe_load((root / ".maw/seed.lock").read_text())
    source = yaml.safe_load((root / ".maw/template-source.yaml").read_text())["template_source"]
    for metadata in (lock["source"], source["distribution"]):
        assert {key: metadata[key] for key in expected} == expected
        assert {key: metadata[key] for key in identity} == identity
    assert source["version"] == "latest_verified_stable"
    assert source["source_channel"] == "public_seed"
    assert all(p.read_bytes() == value for p, value in protected.items())
    _commit(root)
    assert updater.update_template(root, **sources)["status"] == "up_to_date"
    recovery = updater.update_template(root, rollback=applied["recovery_key"])
    updater.update_template(root, rollback=applied["recovery_key"], execute=True,
                            confirmation=recovery["confirmation_required"])
    assert all(p.read_bytes() == value for p, value in originals.items())


def test_same_version_metadata_repair_is_offline(tmp_path, monkeypatch):
    root = tmp_path / "project"
    materialize_project(root, project_key="offline", name="Offline")
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    _stale_metadata(root, updater.SEED_VERSION)
    def no_download(*args, **kwargs):
        pytest.fail("same-version repair must use the installed template")
    monkeypatch.setattr(updater, "materialize_template_source", no_download)
    plan = updater.update_template(root)
    assert plan["status"] == "planned"
    assert {w["path"] for w in plan["writes"]} == {".maw/seed.lock", ".maw/template-source.yaml"}
    updater.update_template(root, execute=True, confirmation=plan["confirmation_required"])
    assert updater.update_template(root)["status"] == "up_to_date"


def test_template_digest_change_invalidates_preview(fixture):
    root, sources = fixture
    _stale_metadata(root, "2.17.0")
    plan = updater.update_template(root, **sources)
    # Even a non-managed file affects the exact distributed template identity.
    (sources["target_template"] / "distribution.txt").write_text("Changed payload")
    with pytest.raises(ValueError, match="confirmation_conflict"):
        updater.update_template(root, execute=True, confirmation=plan["confirmation_required"], **sources)


def test_interrupted_metadata_pair_restores_both_originals(fixture, monkeypatch):
    root, sources = fixture
    _, originals = _stale_metadata(root, "2.17.0")
    plan = updater.update_template(root, **sources)
    real_atomic = updater._atomic
    def fail_second_metadata(path, data):
        if path == root / ".maw/template-source.yaml":
            raise OSError("fault injection after lock update")
        real_atomic(path, data)
    monkeypatch.setattr(updater, "_atomic", fail_second_metadata)
    with pytest.raises(ValueError, match="interrupted"):
        updater.update_template(root, execute=True, confirmation=plan["confirmation_required"], **sources)
    monkeypatch.setattr(updater, "_atomic", real_atomic)
    record = next((root / ".local/seed-upgrades").glob("*.json"))
    recovery = updater.update_template(root, rollback=record.stem)
    updater.update_template(root, rollback=record.stem, execute=True, confirmation=recovery["confirmation_required"])
    assert all(p.read_bytes() == value for p, value in originals.items())


@pytest.mark.parametrize("customized", [False, True])
def test_execution_protocol_upgrade_preserves_local_rules(fixture, customized):
    root, sources = fixture
    ref = "docs/standards/execution-protocol.md"
    # This fixture models a project that has not adopted the new file yet.
    (root/ref).unlink()
    subprocess.run(["git", "add", ref], cwd=root, check=True)
    subprocess.run(["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "Legacy baseline"], cwd=root, check=True)
    target = sources["target_template"]/ref
    target.parent.mkdir(parents=True)
    target.write_text("New shared protocol\n")
    if customized:
        (root/ref).write_text("Project custom policy\n")
    before_project = (root/".maw/project.yaml").read_bytes()
    result = updater.update_template(root, **sources)
    if customized:
        assert ref in result["conflicts"]
        assert (root/ref).read_text() == "Project custom policy\n"
    else:
        updater.update_template(root, execute=True, confirmation=result["confirmation_required"], **sources)
        assert (root/ref).read_text() == "New shared protocol\n"
    assert (root/".maw/project.yaml").read_bytes() == before_project


@pytest.fixture
def fixture(tmp_path):
    project = tmp_path / "project"
    materialize_project(project, project_key="example", name="Example", seed_version="2.8.3")
    old, new = tmp_path / "old", tmp_path / "new"
    old.mkdir(); new.mkdir()
    for root in (project, old):
        (root / "MAWFLOW_CLI.md").write_text("Original command\n")
    (new / "MAWFLOW_CLI.md").write_text("Updated command\n")
    for args in (["init", "-q"], ["add", "."], ["-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "baseline"]):
        subprocess.run(["git", *args], cwd=project, check=True)
    return project, {"base_template": old, "target_template": new}


def test_three_way_conflict_preserves_customization_and_recovery_refuses_parallel_edit(fixture):
    root, sources = fixture
    (root / "MAWFLOW_CLI.md").write_text("User customization\n")
    plan = updater.update_template(root, **sources)
    assert plan["conflicts"] == ["MAWFLOW_CLI.md"]
    assert updater.update_template(root, execute=True, confirmation=plan["confirmation_required"], **sources)["status"] == "blocked"
    (root / "MAWFLOW_CLI.md").write_text("Original command\n")
    plan = updater.update_template(root, **sources)
    result = updater.update_template(root, execute=True, confirmation=plan["confirmation_required"], **sources)
    assert (root / "MAWFLOW_CLI.md").read_text() == "Updated command\n"
    (root / "MAWFLOW_CLI.md").write_text("Concurrent edit\n")
    recovery = updater.update_template(root, rollback=result["recovery_key"])
    assert recovery["status"] == "blocked"
    assert (root / "MAWFLOW_CLI.md").read_text() == "Concurrent edit\n"
    (root / "MAWFLOW_CLI.md").write_text("Updated command\n")
    recovery = updater.update_template(root, rollback=result["recovery_key"])
    assert updater.update_template(root, rollback=result["recovery_key"], execute=True, confirmation=recovery["confirmation_required"])["status"] == "restored"
    assert (root / "MAWFLOW_CLI.md").read_text() == "Original command\n"
    assert yaml.safe_load((root / ".maw/seed.lock").read_text())["seed_version"] == "2.8.3"


def test_interrupted_update_keeps_journal_and_can_restore_offline(fixture, monkeypatch):
    root, sources = fixture
    plan = updater.update_template(root, **sources)
    real_atomic = updater._atomic
    def fail_metadata(path, data):
        if path == root / ".maw/seed.lock":
            raise OSError("fault injection")
        real_atomic(path, data)
    monkeypatch.setattr(updater, "_atomic", fail_metadata)
    with pytest.raises(ValueError, match="interrupted"):
        updater.update_template(root, execute=True, confirmation=plan["confirmation_required"], **sources)
    record = next((root / ".local/seed-upgrades").glob("*.json"))
    assert json.loads(record.read_text())["state"] == "prepared"
    monkeypatch.setattr(updater, "_atomic", real_atomic)
    key = record.stem
    plan = updater.update_template(root, rollback=key)
    updater.update_template(root, rollback=key, execute=True, confirmation=plan["confirmation_required"])
    assert (root / "MAWFLOW_CLI.md").read_text() == "Original command\n"


def test_source_materialization_uses_selected_template(fixture):
    root, sources = fixture
    selected = root.parent / "selected"
    import shutil
    from importlib.resources import files
    shutil.copytree(Path(str(files("mawflow_seed_kit").joinpath("template"))), selected)
    (selected / "selected-source.txt").write_text("Selected source content")
    destination = root.parent / "new-project"
    materialize_project(destination, project_key="selected", name="Selected", template_root=selected, seed_version="2.8.3")
    assert (destination / "selected-source.txt").read_text() == "Selected source content"
    assert yaml.safe_load((destination / ".maw/seed.lock").read_text())["seed_version"] == "2.8.3"


def test_corrupt_later_backup_aborts_before_any_restore(fixture):
    root, sources = fixture
    plan = updater.update_template(root, **sources)
    applied = updater.update_template(root, execute=True, confirmation=plan["confirmation_required"], **sources)
    record = root / ".local/seed-upgrades" / (applied["recovery_key"] + ".json")
    journal = json.loads(record.read_text())
    journal["writes"][-1]["before"] = "Y29ycnVwdA=="
    record.write_text(json.dumps(journal))
    plan = updater.update_template(root, rollback=applied["recovery_key"])
    with pytest.raises(ValueError, match="backup_corrupt"):
        updater.update_template(root, rollback=applied["recovery_key"], execute=True, confirmation=plan["confirmation_required"])
    assert (root / "MAWFLOW_CLI.md").read_text() == "Updated command\n"


@pytest.mark.parametrize("customized", [False, True])
def test_lifecycle_assets_upgrade_without_overwriting_project_data(fixture, customized):
    root, sources = fixture
    ref = "docs/ai-coding/task-lifecycle.md"
    (sources["target_template"] / ref).parent.mkdir(parents=True)
    (sources["target_template"] / ref).write_text("New lifecycle policy")
    (root / "README.md").write_text("Project-owned README")
    (root / "code/custom.txt").write_text("Business-owned code")
    if customized:
        (root / ref).write_text("Project custom lifecycle")
    else:
        (root / ref).unlink()
    for args in (["add", "."], ["-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "custom baseline"]):
        subprocess.run(["git", *args], cwd=root, check=True)
    plan = updater.update_template(root, **sources)
    if customized:
        assert plan["status"] == "blocked" and ref in plan["conflicts"]
        assert (root / ref).read_text() == "Project custom lifecycle"
    else:
        result = updater.update_template(root, execute=True, confirmation=plan["confirmation_required"], **sources)
        assert result["status"] == "applied"
        assert (root / ref).read_text() == "New lifecycle policy"
    assert (root / "README.md").read_text() == "Project-owned README"
    assert (root / "code/custom.txt").read_text() == "Business-owned code"
