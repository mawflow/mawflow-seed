#!/usr/bin/env python3
"""Read-only resource/Host handshake and opt-in, per-user heavy-job gate.

Only stdlib is required. No service lifecycle, credentials, or chat stores are read.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import re
import signal
import subprocess
import sys
import time
import uuid
from urllib.parse import urlsplit


SCHEMA = "mawflow.development_resources.v1"
POLICY_SCHEMA = "mawflow.development_resource_policy.v1"


def valid_policy(data: object) -> bool:
    return (isinstance(data, dict) and set(data) == {"schema", "docker", "heavy_job_limit"}
            and data.get("schema") == POLICY_SCHEMA and type(data.get("heavy_job_limit")) is int
            and data["heavy_job_limit"] == 1 and isinstance(data.get("docker"), dict)
            and set(data["docker"]) == {"mode", "context"}
            and isinstance(data["docker"].get("context"), str)
            and ((data["docker"].get("mode") == "local" and data["docker"]["context"] == "")
                 or (data["docker"].get("mode") == "remote" and
                     bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,95}", data["docker"]["context"])))))


def device_policy() -> dict:
    path = Path.home() / ".local/config/maw-development-resources.json"
    default = {"schema": POLICY_SCHEMA, "docker": {"mode": "local", "context": ""}, "heavy_job_limit": 1}
    try:
        if any(item.is_symlink() for item in (path, *path.parents)):
            raise ValueError("policy_symlink")
        if not path.exists():
            return {"status": "ready", "configured": False, "policy": default, "source": "default"}
        if path.stat().st_size > 16384:
            raise ValueError("policy_too_large")
        data = json.loads(path.read_text())
        if not valid_policy(data):
            raise ValueError("policy_invalid")
        return {"status": "ready", "configured": True, "policy": data, "source": "device_file"}
    except (OSError, ValueError):
        return {"status": "blocked", "source": "device_file", "message": "设备开发资源配置无效；请在工作台设置中核对。"}


def probe(command: list[str], cwd: Path | None = None) -> str:
    env = None
    if command[0] == "docker":
        env = dict(os.environ)
        for key in ("DOCKER_HOST", "DOCKER_CONTEXT", "DOCKER_TLS_VERIFY", "DOCKER_CERT_PATH"):
            env.pop(key, None)
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=5, env=env)
    if result.returncode:
        raise ValueError("probe_failed")
    if len(result.stdout) > 256 * 1024:
        raise ValueError("probe_output_too_large")
    return result.stdout.strip()


def sample() -> dict:
    result = {"os": platform.system(), "cpu_count": os.cpu_count(),
              "pressure": "unknown", "total_bytes": None, "available_bytes": None,
              "sampled_at": datetime.now(timezone.utc).isoformat()}
    try:
        if result["os"] == "Darwin":
            result["total_bytes"] = int(probe(["sysctl", "-n", "hw.memsize"]))
            level = int(probe(["sysctl", "-n", "kern.memorystatus_vm_pressure_level"]))
            result["pressure_level"] = level
            # XNU pressure enum, not the dispatch-source bit mask.
            result["pressure"] = {0: "normal", 1: "warning", 2: "warning",
                                  3: "critical", 4: "critical"}.get(level, "unknown")
        elif result["os"] == "Linux":
            values = {}
            for line in Path("/proc/meminfo").read_text().splitlines():
                key, value = line.split(":", 1)
                values[key] = int(value.strip().split()[0]) * 1024
            result["total_bytes"] = values["MemTotal"]
            result["available_bytes"] = values["MemAvailable"]
            ratio = result["available_bytes"] / result["total_bytes"]
            result["pressure"] = "critical" if ratio < .10 else "warning" if ratio < .20 else "normal"
    except (OSError, ValueError, KeyError, subprocess.SubprocessError):
        result["pressure"] = "unknown"
    return result


def handshake(root: Path) -> dict:
    result = {"transport": "mawflow_cli", "cli": "unavailable", "host": "unverified",
              "context": "unverified", "context_sources": [], "automatic_upload": False,
              "device_policy": device_policy()}
    try:
        capabilities = json.loads(probe(["mawflow", "capabilities"], root))
        if (not isinstance(capabilities, dict) or
                capabilities.get("schema") != "mawflow.host_cli_capabilities.v1" or
                not isinstance(capabilities.get("capabilities"), list)):
            raise ValueError("capability_schema_invalid")
        result["cli"] = "available"
        if "host.development_resources" in capabilities["capabilities"]:
            try:
                policy = json.loads(probe(["mawflow", "development-resources", "show"], root))
                if policy.get("status") != "ready" or not valid_policy(policy.get("policy")):
                    raise ValueError("device_policy_invalid")
                result["device_policy"] = {"status": "ready", "configured": bool(policy.get("configured")),
                    "policy": policy["policy"], "source": "mawflow_cli", "revision": policy.get("revision")}
            except (OSError, ValueError, AttributeError, subprocess.SubprocessError):
                result["device_policy"] = {"status": "blocked", "source": "mawflow_cli", "message": "设备资源策略未回读，暂缓执行；不回退本机 Docker。"}
        # Probe the live Agent; installed CLI availability is a separate fact.
        try:
            state = json.loads(probe(["mawflow", "agent", "status"], root))
            if not isinstance(state, dict) or not isinstance(state.get("health"), dict):
                raise ValueError("agent_status_invalid")
            result["host"] = "ready" if (state.get("running") is True and
                state.get("health", {}).get("ready") is True) else "unavailable"
        except (OSError, ValueError, subprocess.SubprocessError):
            result["host"] = "unavailable"
        if "project.agent_context" in capabilities.get("capabilities", []):
            try:
                context = json.loads(probe(["mawflow", "project", "context", "--root", ".",
                    "--max-chars", "4000", "--format", "json"], root))
                if (not isinstance(context, dict) or context.get("schema") != "mawflow.agent_context.v1" or
                        not isinstance(context.get("documents"), list) or
                        not all(isinstance(doc, dict) for doc in context["documents"])):
                    raise ValueError("context_schema_invalid")
                result["context"] = "read_back"
                result["context_truncated"] = bool(context.get("omitted")) or any(
                    doc.get("truncated") for doc in context.get("documents", []))
                # Contents are consumed separately by the Agent, never echoed into diagnostics.
                result["context_sources"] = [{"source_ref": doc.get("source_ref"),
                    "content_hash": doc.get("content_hash")} for doc in context.get("documents", [])]
            except (OSError, ValueError, subprocess.SubprocessError):
                result["context"] = "failed"
        else:
            result["context"] = "unsupported"
    except (OSError, ValueError, subprocess.SubprocessError):
        result["cli"] = "unavailable"
    return result


def inspect(root: Path) -> dict:
    memory = sample()
    connection = handshake(root)
    pressure = memory["pressure"]
    policy = connection.get("device_policy", {"status": "ready", "policy": {"docker": {"mode": "local", "context": ""}, "heavy_job_limit": 1}})
    warnings = []
    if connection["host"] != "ready":
        warnings.append("本地工作台未验证就绪；按项目文件继续，不自动安装或启动。")
    if connection["context"] != "read_back":
        warnings.append("CLI 上下文未回读；直接读取项目入口和当前模块规则。")
    if pressure == "warning":
        warnings.append("当前内存承压；重任务串行，服务按需复用，避免新增完整项目环境。")
    admitted = pressure in {"normal", "warning"} and policy["status"] == "ready"
    return {"schema": SCHEMA, "status": "success" if admitted else "blocked",
            "summary": "开发资源与本机通信检查完成。", "next_action": "continue" if admitted else "ai_takeover",
            "changed_paths": [], "evidence_refs": [], "log_path": "", "state_path": "",
            "environment": memory, "communication": connection, "warnings": warnings,
            "ai_takeover_reason": "" if admitted else (policy.get("message") or "内存压力严重或无法取得有效采样；暂缓新的重任务。"),
            "heavy_job_limit": 1, "coordination_scope": "same_user_same_device",
            "device_policy": policy,
            "host_connection_verified": connection["host"] == "ready"}


def private_directory(path: Path) -> None:
    for item in (path, *path.parents):
        if item.is_symlink():
            raise ValueError("local_symlink_forbidden")
    path.mkdir(parents=True, exist_ok=True, mode=0o700)


def lock_path() -> Path:
    # One path for every project/worktree of this OS user; never project-local.
    return Path.home() / ".mawflow" / "development-resources" / "heavy.lock"


def stop_child(child: subprocess.Popen) -> None:
    if child.poll() is None:
        os.killpg(child.pid, signal.SIGTERM)
        try:
            child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL)
            child.wait()


def run(root: Path, command: list[str], execute: bool, timeout: float, workload: str = "local") -> tuple[dict, int]:
    result = inspect(root)
    policy = result["device_policy"]
    docker = policy.get("policy", {}).get("docker", {"mode": "local", "context": ""})
    remote = workload == "docker" and docker["mode"] == "remote" and policy["status"] == "ready"
    result["execution"] = {"workload": workload, "docker_mode": docker["mode"], "context": docker["context"]}
    if remote:
        result.update(status="success", next_action="continue", ai_takeover_reason="")
    result["operation"] = "run" if execute else "plan"
    result["summary"] = "重任务计划：同一用户的项目共用一个串行名额；仅执行显式提供的命令。"
    if not execute:
        return result, 0 if result["status"] == "success" else 10
    if result["status"] != "success":
        return result, 10
    env = dict(os.environ)
    if workload == "docker" or docker["mode"] == "remote":
        if any(arg in {"--context", "--host", "-H"} or arg.startswith(("--context=", "--host=", "-H")) for arg in command):
            result.update(status="blocked", next_action="ai_takeover", ai_takeover_reason="命令显式覆盖 Docker 目标；请先核对与设备设置的冲突。")
            return result, 10
    if docker["mode"] == "remote":
        try:
            # Read metadata and prove it is remote before forwarding Docker to it.
            context = json.loads(probe(["docker", "context", "inspect", docker["context"], "--format", "{{json .}}"], root))
            endpoint = context["Endpoints"]["docker"]
            uri = urlsplit(endpoint["Host"])
            import ipaddress
            host = uri.hostname or ""
            is_local = host.lower() in {"localhost", "host.docker.internal", "gateway.docker.internal"}
            try:
                is_local = is_local or ipaddress.ip_address(host).is_loopback or ipaddress.ip_address(host).is_unspecified
            except ValueError:
                pass
            secure = uri.scheme == "ssh" or (uri.scheme in {"tcp", "https"} and endpoint.get("SkipTLSVerify") is False and "ca.pem" in context.get("TLSMaterial", {}).get("docker", []))
            if not host or is_local or not secure or uri.password or uri.query or uri.fragment or uri.path not in {"", "/"}:
                raise ValueError("remote_context_invalid")
            if remote:
                server = json.loads(probe(["docker", "--context", docker["context"], "info", "--format", '{"memory_bytes":{{json .MemTotal}}}'], root))
                if type(server.get("memory_bytes")) is not int or server["memory_bytes"] <= 0:
                    raise ValueError("remote_docker_unavailable")
            for key in ("DOCKER_HOST", "DOCKER_TLS_VERIFY", "DOCKER_CERT_PATH"):
                env.pop(key, None)
            env["DOCKER_CONTEXT"] = docker["context"]
        except (OSError, ValueError, TypeError, KeyError, AttributeError, subprocess.SubprocessError):
            result.update(status="blocked", next_action="ai_takeover", ai_takeover_reason="所选远程 Docker 连接无效、不可达或命令覆盖目标；不回退本机。")
            return result, 10
    elif workload == "docker":
        try:
            # Local mode must not inherit a remote daemon from shell/global defaults.
            name = env.get("DOCKER_CONTEXT", "")
            host = env.get("DOCKER_HOST", "") if not name else ""
            if not host:
                name = name or probe(["docker", "context", "show"], root)
                if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,95}", name):
                    raise ValueError("local_context_invalid")
                context = json.loads(probe(["docker", "context", "inspect", name, "--format", "{{json .}}"], root))
                host = context["Endpoints"]["docker"]["Host"]
            uri = urlsplit(host)
            import ipaddress
            local = uri.scheme in {"unix", "npipe"}
            if uri.scheme in {"tcp", "http", "https"}:
                local = uri.hostname == "localhost"
                try:
                    local = local or ipaddress.ip_address(uri.hostname or "").is_loopback
                except ValueError:
                    pass
            if not local or uri.password or uri.query or uri.fragment:
                raise ValueError("local_context_required")
            if name:
                for key in ("DOCKER_HOST", "DOCKER_TLS_VERIFY", "DOCKER_CERT_PATH"):
                    env.pop(key, None)
                env["DOCKER_CONTEXT"] = name
        except (OSError, ValueError, TypeError, KeyError, AttributeError, subprocess.SubprocessError):
            result.update(status="blocked", next_action="ai_takeover", ai_takeover_reason="当前 Docker 默认目标不是有效本机连接；请核对设备设置和 Docker 客户端。")
            return result, 10
    if os.name != "posix":
        result.update(status="blocked", next_action="ai_takeover",
                      ai_takeover_reason="当前系统尚无已验证的进程锁适配；请人工串行执行。")
        return result, 10
    import fcntl
    path = lock_path()
    private_directory(path.parent)
    fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            result.update(status="blocked", next_action="ai_takeover",
                          ai_takeover_reason="另一个项目正在执行受管重任务；稍后重新检查。")
            return result, 10
        # A fresh sample after taking the slot prevents stale-plan execution.
        result["environment"] = sample()
        if not remote and result["environment"]["pressure"] not in {"normal", "warning"}:
            result.update(status="blocked", next_action="ai_takeover",
                          ai_takeover_reason="取得名额后的内存检查未通过。")
            return result, 10
        directory = root / ".local" / "maw" / "development-resources"
        private_directory(directory)
        logfile = directory / f"{uuid.uuid4().hex}.log"
        logfd = os.open(logfile, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        result["log_path"] = logfile.relative_to(root).as_posix()
        child = None
        with os.fdopen(logfd, "w") as log:
            try:
                # Inherit the flock so a wrapper crash cannot release a live child's slot.
                child = subprocess.Popen(command, cwd=root, stdout=log, stderr=subprocess.STDOUT,
                    start_new_session=True, pass_fds=(fd,), env=env)
                deadline = time.monotonic() + timeout
                while True:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        result["termination_reason"] = "timeout"
                        stop_child(child)
                        break
                    try:
                        child.wait(timeout=min(60, remaining))
                        break
                    except subprocess.TimeoutExpired:
                        result["environment"] = sample()
                        result["communication"] = handshake(root)
                        if result["environment"]["pressure"] == "critical":
                            result["warnings"].append("运行期间出现严重内存压力；完成当前命令后暂缓新重任务。")
                result["child_exit_code"] = child.returncode
                result["status"] = "success" if child.returncode == 0 and "termination_reason" not in result else "failed"
                result["summary"] = "受管重任务执行完成。"
                result["next_action"] = "continue" if result["status"] == "success" else "ai_takeover"
            finally:
                if child is not None:
                    stop_child(child)
        result["environment"] = sample()
        result["communication"] = handshake(root)
        return result, 0 if result["status"] == "success" else 40
    finally:
        # Do not unlink or explicitly unlock: inherited descendants keep the same inode locked.
        os.close(fd)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", nargs="?", default="check", choices=["check", "run"])
    parser.add_argument("--root", default=".")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--workload", choices=["local", "docker"], default="local")
    parser.add_argument("--timeout-seconds", type=float, default=1800)
    parser.add_argument("--format", choices=["json", "markdown", "text"], default="json")
    # Split child argv at -- so options stay options, with no shell interpretation.
    values = list(sys.argv[1:] if argv is None else argv)
    command = values[values.index("--") + 1:] if "--" in values else []
    options = values[:values.index("--")] if "--" in values else values
    args = parser.parse_args(options)
    try:
        root = Path(args.root).expanduser().resolve(strict=True)
        if not root.is_dir() or not (root / ".maw/agent-entry.yaml").is_file():
            raise ValueError("project_entry_required")
        if not 0 < args.timeout_seconds <= 86400:
            raise ValueError("timeout_invalid")
        if args.action == "run" and not command:
            raise ValueError("explicit_command_required")
        if args.action == "check" and (args.execute or command):
            raise ValueError("check_is_read_only")
        if args.action == "check":
            result = inspect(root)
            code = 0 if result["status"] == "success" else 10
        else:
            result, code = run(root, command, args.execute, args.timeout_seconds, args.workload)
    except KeyboardInterrupt:
        result, code = {"schema": SCHEMA, "status": "failed", "summary": "当前重任务已取消。", "next_action": "stop"}, 40
    except (OSError, ValueError, subprocess.SubprocessError):
        result, code = {"schema": SCHEMA, "status": "failed", "summary": "输入或本机环境无效；未获得成功执行回执。", "next_action": "ai_takeover"}, 20
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result["summary"] + "\n" + json.dumps(result, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
