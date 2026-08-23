from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess

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
