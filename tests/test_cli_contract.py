from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages/mawflow-seed-kit/src"))
from mawflow_seed_kit import materialize_project
from mawflow_seed_kit.catalog import SEED_VERSION
from mawflow_seed_kit.cli_contract import project_doctor_output
from mawflow_seed_kit import cli_contract
from mawflow_seed_kit.commands.cli import main


@pytest.mark.parametrize("args", [["version"], ["profile"], ["--version"], ["--read-only", "version"]])
def test_version_reports_source_and_metadata_separately(args, capsys, monkeypatch):
    monkeypatch.setenv("MAWFLOW_EFFECTIVE_PROFILE", "workspace-server")
    monkeypatch.setenv("MAWFLOW_LAUNCHER_VERSION", "0.4.0-rc.5")
    if args == ["--version"]:
        with pytest.raises(SystemExit) as exc:
            main(args)
        assert exc.value.code == 0
    else:
        assert main(args) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["seed_version"] == SEED_VERSION
    assert result["profile"] == "workspace-server"
    assert result["profile_source"] == "npm_launcher"
    assert result["launcher_version"] == "0.4.0-rc.5"
    assert "seed_version" in result["installed_metadata"]


def test_parse_errors_are_json_and_never_echo_untrusted_arguments(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["unknown-command-secret"])
    assert exc.value.code == 2
    captured = capsys.readouterr()
    result = json.loads(captured.err)
    assert result["error_code"] == "cli_usage_error"
    assert result["exit_code"] == 2
    assert not captured.out
    assert "secret" not in captured.err


def test_source_version_never_comes_from_installed_metadata(monkeypatch, capsys):
    monkeypatch.setattr(cli_contract, "_installed", lambda name: "0.0.1")
    assert main(["version"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["seed_version"] == SEED_VERSION
    assert result["installed_metadata"]["seed_version"] == "0.0.1"
    assert result["version_sources"]["seed_version"] == "source_catalog"


def test_workdir_io_errors_are_structured(tmp_path, capsys):
    with pytest.raises(SystemExit) as exc:
        main(["-C", str(tmp_path / "missing"), "version"])
    assert exc.value.code == 2
    result = json.loads(capsys.readouterr().err)
    assert result["error_code"] == "cli_usage_error"
    assert result["exit_code"] == 2


def test_project_doctor_default_omits_shared_and_local_configuration(tmp_path, capsys):
    materialize_project(tmp_path, project_key="cli-contract", name="CLI 契约")
    local = tmp_path / ".local/.maw/project.yaml"
    local.parent.mkdir(parents=True)
    local.write_text("project:\n  private_value: synthetic-local-secret\n")
    assert main(["--read-only", "project", "doctor", "--root", str(tmp_path)]) == 0
    text = capsys.readouterr().out
    result = json.loads(text)
    assert result["summary"]["errors"] == 0
    assert result["presentation"]["mode"] == "summary"
    assert "configs" not in result and "local_configs" not in result and "project" not in result
    assert "synthetic-local-secret" not in text


def test_summary_is_bounded_and_preserves_total_errors():
    result = project_doctor_output({"status": "needs_attention", "summary": {"errors": 90},
        "issues": [{"code": "invalid_source", "source_ref": ".maw/project.yaml", "severity": "error", "message": "private"} for _ in range(90)],
        "diagnostics": [{"status": "invalid", "source_ref": ".maw/project.yaml"} for _ in range(70)]})
    assert result["summary"]["errors"] == 90
    assert len(result["issues"]) == 50
    assert result["presentation"]["issues_omitted"] == 40
    assert result["presentation"]["diagnostics_omitted"] == 20
    assert "private" not in json.dumps(result)
