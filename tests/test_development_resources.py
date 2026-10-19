from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "ops/scripts/development-resources.py"
spec = importlib.util.spec_from_file_location("development_resources", SCRIPT)
resources = importlib.util.module_from_spec(spec)
spec.loader.exec_module(resources)


@pytest.fixture
def project(tmp_path, monkeypatch):
    root = tmp_path / "project"
    (root / ".maw").mkdir(parents=True)
    (root / ".maw/agent-entry.yaml").write_text("schema_version: 3\n")
    monkeypatch.setattr(resources, "sample", lambda: {"pressure": "warning"})
    monkeypatch.setattr(resources, "handshake", lambda root: {"host": "ready", "context": "read_back"})
    monkeypatch.setattr(resources, "lock_path", lambda: tmp_path / "shared/heavy.lock")
    return root


def test_read_only_and_preview_never_create_state_or_execute(project, tmp_path):
    before = list(tmp_path.rglob("*"))
    assert resources.main(["check", "--root", str(project)]) == 0
    result, code = resources.run(project, [sys.executable, "-c", "raise SystemExit(99)"], False, 10)
    assert code == 0 and result["operation"] == "plan"
    assert list(tmp_path.rglob("*")) == before


@pytest.mark.parametrize("pressure", ["critical", "unknown"])
def test_pressure_blocks_command_without_state(project, monkeypatch, pressure):
    monkeypatch.setattr(resources, "sample", lambda: {"pressure": pressure})
    result, code = resources.run(project, [sys.executable, "-c", "raise SystemExit(99)"], True, 10)
    assert code == 10 and result["status"] == "blocked"
    assert not (project / ".local").exists()
    assert not resources.lock_path().exists()


def test_cli_missing_is_a_reported_file_only_fallback(project, monkeypatch):
    monkeypatch.setattr(resources, "probe", lambda *args: (_ for _ in ()).throw(FileNotFoundError()))
    # Load a separate module so fixture's handshake replacement does not hide the real adapter.
    real = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(real)
    monkeypatch.setattr(real.Path, "home", lambda: project.parent / "isolated-home")
    monkeypatch.setattr(real, "probe", lambda *args: (_ for _ in ()).throw(FileNotFoundError()))
    real.sample = lambda: {"pressure": "normal"}
    result = real.inspect(project)
    assert result["status"] == "success"
    assert result["communication"]["cli"] == "unavailable"
    assert not result["host_connection_verified"]
    assert result["warnings"]


def test_cli_health_and_context_are_independent_and_do_not_echo_content(project, monkeypatch):
    real = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(real)
    def fake(command, cwd=None):
        if command[1] == "capabilities":
            return json.dumps({"schema": "mawflow.host_cli_capabilities.v1", "capabilities": ["project.agent_context"]})
        if command[1] == "agent":
            return json.dumps({"running": False, "health": {"ready": False}})
        return json.dumps({"schema": "mawflow.agent_context.v1", "omitted": ["budget"], "documents": [
            {"source_ref": ".maw/agent-rules.yaml", "content_hash": "sha256:test", "content": "PRIVATE_CONTENT"}]})
    monkeypatch.setattr(real, "probe", fake)
    result = real.handshake(project)
    assert result["cli"] == "available" and result["host"] == "unavailable"
    assert result["context"] == "read_back" and result["context_truncated"]
    assert "PRIVATE_CONTENT" not in json.dumps(result)


@pytest.mark.parametrize("payload", ["[]", "{}", '{"schema":"mawflow.host_cli_capabilities.v1","capabilities":null}'])
def test_incompatible_cli_payload_is_reported_without_crash(project, monkeypatch, payload):
    real = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(real)
    monkeypatch.setattr(real, "probe", lambda *args: payload)
    assert real.handshake(project)["cli"] == "unavailable"


@pytest.mark.skipif(os.name != "posix", reason="POSIX process locks")
def test_failure_and_timeout_clean_up_owned_command_and_release_slot(project):
    result, code = resources.run(project, [sys.executable, "-c", "print('log only'); raise SystemExit(7)"], True, 10)
    assert code == 40 and result["child_exit_code"] == 7
    assert "log only" in (project / result["log_path"]).read_text()
    result, code = resources.run(project, [sys.executable, "-c", "import time; time.sleep(20)"], True, .05)
    assert code == 40 and result["termination_reason"] == "timeout"
    result, code = resources.run(project, [sys.executable, "-c", "pass"], True, 10)
    assert code == 0


def wrapper(project, lock, marker):
    code = f"""
import importlib.util, pathlib, sys
s=importlib.util.spec_from_file_location('r', {str(SCRIPT)!r}); r=importlib.util.module_from_spec(s); s.loader.exec_module(r)
r.sample=lambda: {{'pressure':'normal'}}
r.handshake=lambda root: {{'host':'ready','context':'read_back'}}
r.lock_path=lambda: pathlib.Path({str(lock)!r})
command=[sys.executable,'-c',"import pathlib,time; pathlib.Path({str(marker)!r}).touch(); time.sleep(1)"]
result,exit_code=r.run(pathlib.Path({str(project)!r}),command,True,10)
sys.exit(exit_code)
"""
    return subprocess.Popen([sys.executable, "-c", code], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


@pytest.mark.skipif(os.name != "posix", reason="POSIX process locks")
@pytest.mark.parametrize("crash", [False, True])
def test_two_projects_share_slot_and_crashed_wrapper_keeps_live_child_lock(project, tmp_path, crash):
    marker = tmp_path / "started"
    child = wrapper(project, resources.lock_path(), marker)
    try:
        deadline = time.monotonic() + 5
        while not marker.exists() and time.monotonic() < deadline:
            time.sleep(.01)
        assert marker.exists(), child.communicate(timeout=5)
        if crash:
            child.kill()
            child.wait(timeout=5)
        other = tmp_path / "other-project"
        other.mkdir()
        result, code = resources.run(other, [sys.executable, "-c", "raise SystemExit(99)"], True, 10)
        assert code == 10 and result["status"] == "blocked"
        assert not (other / ".local").exists()
        if not crash:
            assert child.wait(timeout=5) == 0
        else:
            time.sleep(1.1)
        result, code = resources.run(other, [sys.executable, "-c", "pass"], True, 10)
        assert code == 0
    finally:
        if child.poll() is None:
            child.kill()
            child.wait()


def test_materialized_project_has_identical_tool_and_resource_rule(tmp_path):
    sys.path.insert(0, str(ROOT / "packages/mawflow-seed-kit/src"))
    from mawflow_seed_kit import materialize_project
    root = tmp_path / "new"
    materialize_project(root, project_key="resources", name="资源协调验收")
    assert (root / "ops/scripts/development-resources.py").read_bytes() == SCRIPT.read_bytes()
    for ref in ["AGENTS.md", "CLAUDE.md", "GEMINI.md", "CHATGPT.md", "AI_START_HERE.md", ".maw/agent-entry.yaml", ".maw/agent-rules.yaml"]:
        assert "development-resources" in (root / ref).read_text(), ref
    assert (root / "docs/ai-coding/development-resources.md").read_bytes() == (ROOT / "docs/ai-coding/development-resources.md").read_bytes()


def test_device_workbench_policy_is_consumed_without_new_cli(tmp_path, monkeypatch):
    real = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(real)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    path = tmp_path / ".local/config/maw-development-resources.json"
    path.parent.mkdir(parents=True)
    data = {"schema": resources.POLICY_SCHEMA, "docker": {"mode": "remote", "context": "development"}, "heavy_job_limit": 1}
    path.write_text(json.dumps(data))
    monkeypatch.setattr(real, "probe", lambda *args: (_ for _ in ()).throw(FileNotFoundError()))
    assert real.handshake(tmp_path)["device_policy"]["policy"] == data
    path.write_text('{"secret":"invalid"}')
    assert real.handshake(tmp_path)["device_policy"]["status"] == "blocked"


@pytest.mark.skipif(os.name != "posix", reason="POSIX process locks")
def test_remote_docker_injects_selected_context_even_when_local_memory_is_critical(project, monkeypatch):
    policy = {"schema": resources.POLICY_SCHEMA, "docker": {"mode": "remote", "context": "development"}, "heavy_job_limit": 1}
    monkeypatch.setattr(resources, "sample", lambda: {"pressure": "critical"})
    monkeypatch.setattr(resources, "handshake", lambda root: {"host": "ready", "context": "read_back", "device_policy": {"status": "ready", "policy": policy}})
    def probe(command, root=None):
        if "inspect" in command:
            return json.dumps({"Endpoints": {"docker": {"Host": "ssh://docker.example.test"}}})
        return json.dumps({"memory_bytes": 16 * 1024 ** 3})
    monkeypatch.setattr(resources, "probe", probe)
    monkeypatch.setenv("DOCKER_HOST", "tcp://wrong.example.test:2375")
    marker = project / "docker-context.txt"
    command = [sys.executable, "-c", f"import os,pathlib; assert 'DOCKER_HOST' not in os.environ; pathlib.Path({str(marker)!r}).write_text(os.environ['DOCKER_CONTEXT'])"]
    result, code = resources.run(project, command, True, 10, "docker")
    assert code == 0 and result["execution"]["docker_mode"] == "remote"
    assert marker.read_text() == "development"


def test_remote_docker_failure_never_falls_back_or_runs_command(project, monkeypatch):
    policy = {"schema": resources.POLICY_SCHEMA, "docker": {"mode": "remote", "context": "development"}, "heavy_job_limit": 1}
    monkeypatch.setattr(resources, "handshake", lambda root: {"host": "ready", "context": "read_back", "device_policy": {"status": "ready", "policy": policy}})
    monkeypatch.setattr(resources, "probe", lambda *args: (_ for _ in ()).throw(FileNotFoundError()))
    result, code = resources.run(project, [sys.executable, "-c", "raise SystemExit(99)"], True, 10, "docker")
    assert code == 10 and result["status"] == "blocked"
    assert not (project / ".local").exists()


def test_local_docker_does_not_inherit_a_remote_environment_target(project, monkeypatch):
    monkeypatch.delenv("DOCKER_CONTEXT", raising=False)
    monkeypatch.setenv("DOCKER_HOST", "tcp://remote.example.test:2375")
    result, code = resources.run(project, [sys.executable, "-c", "raise SystemExit(99)"], True, 10, "docker")
    assert code == 10 and result["status"] == "blocked"
    assert not (project / ".local").exists()


@pytest.mark.skipif(os.name != "posix", reason="POSIX process locks")
def test_local_docker_pins_verified_local_context(project, monkeypatch):
    monkeypatch.setenv("DOCKER_CONTEXT", "colima")
    monkeypatch.setenv("DOCKER_HOST", "tcp://wrong.example.test:2375")
    monkeypatch.setattr(resources, "probe", lambda *args: json.dumps({"Endpoints": {"docker": {"Host": "unix:///tmp/test.sock"}}}))
    command = [sys.executable, "-c", "import os; assert os.environ['DOCKER_CONTEXT']=='colima'; assert 'DOCKER_HOST' not in os.environ"]
    result, code = resources.run(project, command, True, 10, "docker")
    assert code == 0 and result["status"] == "success"


def test_compact_host_flag_cannot_override_device_target(project):
    result, code = resources.run(project, ["docker", "-Hssh://remote.example.test", "info"], True, 10, "docker")
    assert code == 10 and result["status"] == "blocked"
    assert not (project / ".local").exists()
