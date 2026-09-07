from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "ops" / "scripts" / "plan-template-drift.py"
SPEC = importlib.util.spec_from_file_location("plan_template_drift", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return result.stdout.strip()


def _seed_lock(version: str, fingerprint: str) -> dict[str, object]:
    return {
        "schema": "mawflow.seed_lock.v2",
        "contract_version": 2,
        "contract_fingerprint": fingerprint,
        "seed_version": version,
        "profile": "blank",
        "source": {"kind": "test"},
        "bom": {
            "kit": f"mawflow-seed-kit=={version}",
            "contract": "seed-contract-v2",
        },
    }


def _write_yaml(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def test_current_template_commit_exposes_seed_contract_drift(tmp_path: Path) -> None:
    source = tmp_path / "seed"
    source.mkdir()
    _git(source, "init", "-b", "main")
    _write_yaml(
        source / ".maw/seed.lock",
        _seed_lock("2.3.1", "sha256:source"),
    )
    _git(source, "add", ".maw/seed.lock")
    _git(
        source,
        "-c",
        "user.name=MAWflow Tests",
        "-c",
        "user.email=tests@example.invalid",
        "commit",
        "-m",
        "seed baseline",
    )
    target_commit = _git(source, "rev-parse", "HEAD")

    project = tmp_path / "project"
    _write_yaml(
        project / ".maw/template-source.yaml",
        {
            "schema_version": 2,
            "template_source": {
                "source_channel": "public_seed",
                "local_path": str(source),
                "git_url": "",
                "version": "main",
                "applied_version": target_commit,
            },
        },
    )
    _write_yaml(
        project / ".maw/seed.lock",
        _seed_lock("2.0.0", "sha256:legacy"),
    )
    args = MODULE.build_parser().parse_args(
        ["--root", str(project), "--format", "json"]
    )

    plan = MODULE.compute_plan(args)

    assert plan["behind_count"] == 0
    assert plan["status"] == "seed_contract_behind"
    assert plan["seed_contract"]["status"] == "behind"
    assert "受控 Seed Contract 迁移" in plan["current_session_prompt"]

    _write_yaml(
        project / ".maw/seed.lock",
        _seed_lock("2.3.1", "sha256:source"),
    )
    current = MODULE.compute_plan(args)

    assert current["status"] == "up_to_date"
    assert current["seed_contract"]["status"] == "current"
    assert current["current_session_prompt"] == ""

    _write_yaml(
        project / ".maw/seed.lock",
        _seed_lock("2.3.1", "sha256:different-contract"),
    )
    drifted = MODULE.compute_plan(args)

    assert drifted["status"] == "seed_contract_behind"
    assert drifted["seed_contract"]["status"] == "contract_drift"


def test_newer_project_seed_does_not_mask_template_alignment(tmp_path: Path) -> None:
    source = tmp_path / "seed"
    source.mkdir()
    _git(source, "init", "-b", "main")
    _write_yaml(
        source / ".maw/seed.lock",
        _seed_lock("2.2.0", "sha256:source"),
    )
    _git(source, "add", ".maw/seed.lock")
    _git(
        source,
        "-c",
        "user.name=MAWflow Tests",
        "-c",
        "user.email=tests@example.invalid",
        "commit",
        "-m",
        "seed baseline",
    )
    target_commit = _git(source, "rev-parse", "HEAD")

    project = tmp_path / "project"
    _write_yaml(
        project / ".maw/template-source.yaml",
        {
            "schema_version": 2,
            "template_source": {
                "source_channel": "public_seed",
                "local_path": str(source),
                "version": "main",
                "applied_version": target_commit,
            },
        },
    )
    _write_yaml(
        project / ".maw/seed.lock",
        _seed_lock("2.3.1", "sha256:newer"),
    )
    args = MODULE.build_parser().parse_args(["--root", str(project)])

    plan = MODULE.compute_plan(args)

    assert plan["status"] == "up_to_date"
    assert plan["seed_contract"]["status"] == "ahead"


@pytest.fixture
def drift_project(tmp_path: Path):
    source = tmp_path / "seed"
    source.mkdir()
    _git(source, "init", "-b", "main")

    def commit_source():
        _git(source, "add", ".")
        _git(
            source,
            "-c",
            "user.name=MAWflow Tests",
            "-c",
            "user.email=tests@example.invalid",
            "commit",
            "--allow-empty",
            "-m",
            "test source",
        )
        return _git(source, "rev-parse", "HEAD")

    _write_yaml(source / ".maw/seed.lock", _seed_lock("2.8.2", "sha256:target"))
    baseline = commit_source()
    project = tmp_path / "project"
    _write_yaml(
        project / ".maw/template-source.yaml",
        {
            "template_source": {
                "source_channel": "public_seed",
                "local_path": str(source),
                "version": "main",
                "applied_version": baseline,
            },
        },
    )
    _write_yaml(project / ".maw/seed.lock", _seed_lock("2.8.2", "sha256:target"))
    args = MODULE.build_parser().parse_args(["--root", str(project)])
    return source, project, args, commit_source


@pytest.mark.parametrize("relation", ["aligned", "behind", "baseline_missing"])
@pytest.mark.parametrize(
    "invalid_source", ["absent", "bad_yaml", "empty", "missing_fingerprint"]
)
def test_unverifiable_source_never_reports_alignment(
    drift_project, relation, invalid_source
):
    source, project, args, commit = drift_project
    source_lock = source / ".maw/seed.lock"
    if invalid_source == "absent":
        source_lock.unlink()
    elif invalid_source == "bad_yaml":
        source_lock.write_text("seed_version: [", encoding="utf-8")
    elif invalid_source == "empty":
        _write_yaml(source_lock, {})
    else:
        payload = _seed_lock("2.8.2", "")
        _write_yaml(source_lock, payload)
    target = commit()
    if relation == "aligned":
        args.applied_version = target
    elif relation == "baseline_missing":
        path = project / ".maw/template-source.yaml"
        payload = yaml.safe_load(path.read_text())
        payload["template_source"]["applied_version"] = ""
        _write_yaml(path, payload)
    before = (project / ".maw/seed.lock").read_bytes()

    plan = MODULE.compute_plan(args)

    assert plan["status"] == "seed_contract_unavailable"
    assert plan["template_status"] == {"aligned": "up_to_date"}.get(relation, relation)
    assert plan["seed_contract"]["status"] == "unavailable"
    assert plan["current_session_prompt"] == ""
    assert (project / ".maw/seed.lock").read_bytes() == before


@pytest.mark.parametrize(
    "contract_state", ["behind", "missing", "fingerprint_drift", "missing_fingerprint"]
)
def test_commit_and_contract_upgrade_continue_until_both_align(
    drift_project, contract_state
):
    source, project, args, commit = drift_project
    target = commit()
    lock_path = project / ".maw/seed.lock"
    if contract_state == "missing":
        lock_path.unlink()
    else:
        _write_yaml(
            lock_path,
            _seed_lock(
                "2.0.0" if contract_state == "behind" else "2.8.2",
                "" if contract_state == "missing_fingerprint" else "sha256:old",
            ),
        )

    plan = MODULE.compute_plan(args)
    assert plan["status"] == "behind"
    prompt = plan["current_session_prompt"]
    assert "受控 Seed Contract 迁移" in prompt
    assert ".maw/seed.lock" in prompt and "preview" in prompt
    assert target in prompt and "sha256:target" in prompt
    assert "本机 Seed Kit" in prompt

    # Advancing only the commit baseline must keep the migration pending.
    args.applied_version = target
    pending = MODULE.compute_plan(args)
    assert pending["status"] == "seed_contract_behind"
    assert pending["template_status"] == "up_to_date"
    assert "受控 Seed Contract 迁移" in pending["current_session_prompt"]

    _write_yaml(lock_path, _seed_lock("2.8.2", "sha256:target"))
    complete = MODULE.compute_plan(args)
    assert complete["status"] == "up_to_date"
    assert complete["seed_contract"]["status"] == "current"


@pytest.mark.parametrize(
    "project_version,fingerprint",
    [
        ("2.8.2", "sha256:target"),
        ("2.9.0", "sha256:target"),
        ("2.9.0", ""),
    ],
)
def test_template_only_upgrade_does_not_request_contract_rewrite(
    drift_project, project_version, fingerprint
):
    source, project, args, commit = drift_project
    commit()
    _write_yaml(project / ".maw/seed.lock", _seed_lock(project_version, fingerprint))
    plan = MODULE.compute_plan(args)
    assert plan["status"] == "behind"
    assert "受控 Seed Contract 迁移" not in plan["current_session_prompt"]
    assert "最终复检" in plan["current_session_prompt"]


def test_missing_baseline_still_requires_contract_migration(drift_project):
    source, project, args, commit = drift_project
    path = project / ".maw/template-source.yaml"
    payload = yaml.safe_load(path.read_text())
    payload["template_source"]["applied_version"] = ""
    _write_yaml(path, payload)
    _write_yaml(project / ".maw/seed.lock", _seed_lock("2.0.0", "sha256:old"))
    plan = MODULE.compute_plan(args)
    assert plan["status"] == "baseline_missing"
    assert "受控 Seed Contract 迁移" in plan["current_session_prompt"]
    assert "不追溯猜测历史差异" in plan["current_session_prompt"]


@pytest.mark.parametrize("relation", ["ahead", "diverged"])
def test_unavailable_contract_does_not_override_unsafe_commit_relationship(
    drift_project, relation
):
    source, project, args, commit = drift_project
    baseline = _git(source, "rev-parse", "HEAD")
    (source / ".maw/seed.lock").unlink()
    applied = commit()
    args.applied_version = applied
    args.target_version = baseline
    if relation == "diverged":
        _git(source, "checkout", "-b", "other", baseline)
        (source / ".maw/seed.lock").write_text("invalid: [", encoding="utf-8")
        args.target_version = commit()
    else:
        # The target contract is absent on the earlier side of the relation too.
        _git(source, "checkout", "-b", "older-missing", applied)
        args.target_version = applied
        args.applied_version = commit()
    plan = MODULE.compute_plan(args)
    assert plan["status"] == relation
    assert plan["seed_contract"]["status"] == "unavailable"
    assert plan["current_session_prompt"] == ""
