from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import zipfile

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages/mawflow-seed-kit/src"))
from mawflow_seed_kit.commands import template_policy as policy
from mawflow_seed_kit.commands.template_drift import TemplateDriftConfig, plan_template_drift
from mawflow_seed_kit.components import _repository_identity
from test_plan_template_drift import _write_yaml, _git, drift_project


@pytest.fixture
def public_release(tmp_path, monkeypatch):
    repo = tmp_path / "public"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    fingerprint = "sha256:" + "a" * 64
    manifest = {"schema": "mawflow.seed_public_payload.v2", "seed_version": "2.10.0",
                "contract_version": 2, "contract_fingerprint": fingerprint,
                "bom": {"kit": "mawflow-seed-kit==2.10.0", "contract": "seed-contract-v2"}}
    lock = {**manifest, "schema": "mawflow.seed_lock.v2"}
    _write_yaml(repo / ".maw/seed.lock", lock)
    (repo / "PUBLIC_PAYLOAD_MANIFEST.json").write_text(json.dumps(manifest) + "\n")
    (repo / "TEMPLATE_VERSION").write_text("v2.10.0\n")
    _git(repo, "add", ".")
    _git(repo, "-c", "user.name=Tests", "-c", "user.email=test@example.invalid", "commit", "-m", "public release")
    _git(repo, "tag", "v2.10.0")
    kit = {"version": "2.10.0", "contract_version": 2, "contract_fingerprint": fingerprint}
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr("mawflow_seed_kit/manifest.json", json.dumps(kit))
    wheel = stream.getvalue()
    digest = hashlib.sha256(wheel).hexdigest()
    artifact_url = policy.PACKAGE_INDEX_URL + "mawflow_seed_kit-2.10.0-py3-none-any.whl"
    responses = {
        policy.PUBLIC_MANIFEST_URL: json.dumps(manifest).encode(),
        policy.PACKAGE_INDEX_URL: f'<a href="{artifact_url}#sha256={digest}">wheel</a>'.encode(),
        artifact_url: wheel,
    }
    monkeypatch.setattr(policy, "_read_url", lambda url: responses[url])
    def clone(target, url):
        assert url == policy.PUBLIC_GIT_URL
        subprocess.run(["git", "clone", "--quiet", "--bare", str(repo), str(target)], check=True)
    monkeypatch.setattr(policy, "_clone_public", clone)
    project = tmp_path / "project"
    _write_yaml(project / ".maw/template-source.yaml", {"template_source": {
        "source_channel": "public_seed", "kind": "package", "applied_version": "2.10.0",
        "git_url": policy.PUBLIC_GIT_URL, "version": "latest_verified_stable"}})
    _write_yaml(project / ".maw/seed.lock", lock)
    return project, repo, responses, artifact_url


def test_public_upgrade_freezes_tag_commit_and_verified_kit(public_release):
    project, repo, _, _ = public_release
    plan = plan_template_drift(TemplateDriftConfig(project))
    assert plan["status"] == "up_to_date"
    assert plan["source_kind"] == "verified_public_release"
    assert plan["target_version"] == "v2.10.0"
    assert plan["target_commit"] == _git(repo, "rev-parse", "HEAD")
    assert plan["release"]["kit"]["version"] == "2.10.0"
    assert plan["release"]["payload_manifest_sha256"] == hashlib.sha256((repo / "PUBLIC_PAYLOAD_MANIFEST.json").read_bytes()).hexdigest()
    assert plan["seed_contract"]["status"] == "current"


@pytest.mark.parametrize("target", ["main", "dev", "v2.10.0-rc.1", "abcd1234"])
def test_public_rejects_unreleased_refs(public_release, target):
    project, _, _, _ = public_release
    assert plan_template_drift(TemplateDriftConfig(project, target_version=target))["status"] == "public_release_required"


@pytest.mark.parametrize("override", ["private_url", "path", "local_overlay", "internal_channel"])
def test_business_project_cannot_bypass_public_route(public_release, override):
    project, repo, _, _ = public_release
    options = {}
    if override == "private_url":
        options["git_url"] = "https://example.invalid/private/seed.git"
    elif override == "path":
        options["source_path"] = str(repo)
    elif override == "local_overlay":
        _write_yaml(project / ".local/.maw/template-source.yaml", {"template_source": {"local_path": str(repo)}})
    else:
        _write_yaml(project / ".maw/template-source.yaml", {"template_source": {"source_channel": "internal_seed"}})
    plan = plan_template_drift(TemplateDriftConfig(project, **options))
    assert plan["status"] == ("public_source_migration_required" if override == "internal_channel" else "source_policy_violation")
    assert plan["current_session_prompt"] == ""


def test_local_identity_overlay_cannot_grant_main_exception(public_release):
    project, _, _, _ = public_release
    _write_yaml(project / ".local/.maw/project.yaml", {"project": {"key": "multiagentworker", "type": "maw_control_plane"}})
    _write_yaml(project / ".local/.maw/repository-identity.yaml", {"current_repository": {"primary_role": "main_repository", "repository_key": "multiagentworker"}})
    assert not policy.is_main_repository(project)


@pytest.mark.parametrize("failure", ["checksum", "missing_kit", "family"])
def test_partial_or_corrupt_publication_fails_closed(public_release, failure):
    project, _, responses, artifact = public_release
    if failure == "checksum":
        responses[artifact] += b"broken"
    elif failure == "missing_kit":
        responses[policy.PACKAGE_INDEX_URL] = b""
    else:
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w") as archive:
            archive.writestr("mawflow_seed_kit/manifest.json", json.dumps({"version": "2.9.0"}))
        responses[artifact] = stream.getvalue()
        digest = hashlib.sha256(responses[artifact]).hexdigest()
        responses[policy.PACKAGE_INDEX_URL] = f'<a href="{artifact}#sha256={digest}">wheel</a>'.encode()
    before = (project / ".maw/template-source.yaml").read_bytes()
    plan = plan_template_drift(TemplateDriftConfig(project))
    assert plan["status"] == "public_release_unavailable"
    assert plan["current_session_prompt"] == ""
    assert (project / ".maw/template-source.yaml").read_bytes() == before


def test_missing_public_baseline_returns_migration_plan_without_rewrite(public_release):
    project, _, _, _ = public_release
    before = (project / ".maw/template-source.yaml").read_bytes()
    plan = plan_template_drift(TemplateDriftConfig(project, applied_version="b" * 40))
    assert plan["status"] == "source_baseline_migration_required"
    assert (project / ".maw/template-source.yaml").read_bytes() == before


def test_public_release_never_downgrades_newer_project(public_release):
    project, _, _, _ = public_release
    path = project / ".maw/seed.lock"
    lock = yaml.safe_load(path.read_text()); lock["seed_version"] = "2.12.0"
    _write_yaml(path, lock)
    plan = plan_template_drift(TemplateDriftConfig(project))
    assert plan["status"] == "public_release_behind_project"
    assert plan["current_session_prompt"] == ""
    assert yaml.safe_load(path.read_text())["seed_version"] == "2.12.0"


def test_registered_main_seed_dirty_or_wrong_origin_is_blocked(drift_project):
    source, project, args, commit = drift_project
    (source / "uncommitted.txt").write_text("candidate")
    assert plan_template_drift(TemplateDriftConfig(project))["status"] == "seed_source_dirty"
    commit()
    _git(source, "remote", "set-url", "origin", "https://example.invalid/other.git")
    assert plan_template_drift(TemplateDriftConfig(project))["status"] == "seed_source_invalid"


def test_https_and_ssh_identify_same_repository():
    assert _repository_identity("https://example.invalid/seed.git") == _repository_identity("git@example.invalid:seed.git")


def test_configuration_fragments_and_disabled_overlays_preserve_policy(tmp_path):
    _write_yaml(tmp_path / ".maw/template-source.yaml", {"template_source": {"source_channel": "public_seed"}})
    _write_yaml(tmp_path / ".maw/template-source.d/10-version.yaml", {"template_source": {"version": "v2.10.0"}})
    _write_yaml(tmp_path / ".local/.maw/template-source.yaml", {"enabled": False, "template_source": {"source_channel": "internal_seed"}})
    source = policy.load_domain(tmp_path, "template-source")["template_source"]
    assert source == {"source_channel": "public_seed", "version": "v2.10.0"}


def test_standalone_kit_cli_uses_same_project_drift_policy(public_release, capsys):
    from mawflow_seed_kit.cli import main
    project, _, _, _ = public_release
    expected = plan_template_drift(TemplateDriftConfig(project))
    assert main(["project", "drift", "--root", str(project)]) == 0
    actual = json.loads(capsys.readouterr().out)
    assert actual == expected
    assert main(["project", "drift", "--root", str(project), "--target-version", "main"]) == 1
    assert json.loads(capsys.readouterr().out)["status"] == "public_release_required"
