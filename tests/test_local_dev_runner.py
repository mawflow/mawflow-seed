from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "mawflow_local_dev_runner",
    ROOT / "ops/scripts/run-local-dev.py",
)
assert SPEC and SPEC.loader
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


def test_selection_only_includes_requested_runnable_services() -> None:
    preset, selected, unavailable = runner._resolve_selection(
        {
            "defaults": {
                "development_start_preset": "custom",
                "development_app_keys": ["server", "device"],
            }
        },
        {
            "server": {"runnable": True, "component_type": "backend"},
            "client": {"runnable": True, "component_type": "frontend"},
            "device": {"runnable": False, "component_type": "custom"},
        },
        [],
    )

    assert preset == "custom"
    assert selected == ["server"]
    assert unavailable == ["device"]


def test_execution_step_accepts_scoped_command_without_shell(tmp_path: Path) -> None:
    component = tmp_path / "code/server"
    component.mkdir(parents=True)

    argv, cwd = runner._execution_step(
        tmp_path.resolve(),
        "cd code/server && npm run dev",
    )

    assert argv == ["npm", "run", "dev"]
    assert cwd == component.resolve()


def test_detached_compose_launcher_must_finish_before_start_is_successful() -> None:
    assert runner._waits_for_launcher_completion(
        [
            "docker",
            "compose",
            "-f",
            "ops/local/docker-compose.yml",
            "up",
            "-d",
            "--build",
        ]
    )
    assert not runner._waits_for_launcher_completion(["npm", "run", "dev"])


def test_background_start_propagates_late_compose_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FailedComposeLauncher:
        pid = 42
        waited = False

        def wait(self, *, timeout: int) -> int:
            assert timeout == runner.LAUNCHER_COMPLETION_TIMEOUT_SECONDS
            self.waited = True
            return 1

        def poll(self) -> None:
            return None

    process = FailedComposeLauncher()
    monkeypatch.setattr(runner.subprocess, "Popen", lambda *_args, **_kwargs: process)

    result = runner._run_background(
        tmp_path,
        ["server"],
        {
            "server": {
                "command": "docker compose -f ops/local/docker-compose.yml up -d",
                "command_key": "start",
            }
        },
    )

    assert result == 1
    assert process.waited is True
    _, manifest = runner._manifest(tmp_path)
    assert manifest["services"] == []


def test_foreground_start_waits_for_finite_compose_launcher(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class CompletedComposeLauncher:
        pid = 43
        waited = False

        def wait(self, *, timeout: int) -> int:
            assert timeout == runner.LAUNCHER_COMPLETION_TIMEOUT_SECONDS
            self.waited = True
            return 0

        def poll(self) -> int:
            return 0

    process = CompletedComposeLauncher()
    monkeypatch.setattr(runner.subprocess, "Popen", lambda *_args, **_kwargs: process)

    result = runner._run_foreground(
        tmp_path,
        ["server"],
        {
            "server": {
                "command": "docker compose -f ops/local/docker-compose.yml up -d",
            }
        },
    )

    assert result == 0
    assert process.waited is True


@pytest.mark.parametrize(
    "command",
    [
        "echo prepare && npm run dev",
        "npm run dev; touch leaked",
        "npm run dev | tee output.log",
        "npm run $(printf dev)",
        "cd .local/runtime && npm run dev",
    ],
)
def test_execution_step_rejects_shell_control_and_private_paths(
    tmp_path: Path,
    command: str,
) -> None:
    with pytest.raises(ValueError):
        runner._execution_step(tmp_path.resolve(), command)
