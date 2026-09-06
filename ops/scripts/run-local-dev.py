#!/usr/bin/env python3
"""Run only the local development services selected by the current machine."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import signal
import shlex
import subprocess
import sys
import time
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))

from ops.lib.maw_config_loader import MawConfigLoader  # noqa: E402


PRESETS = {
    "default_application": "项目默认应用",
    "frontend_backend": "前端 + 后端联调",
    "all_runnable": "全部可自动启动",
    "custom": "自定义服务",
}
RUN_ROOT = Path(".local/run/local-dev")
MANIFEST_NAME = "services.json"
LAUNCHER_COMPLETION_TIMEOUT_SECONDS = 600


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink() or path.stat().st_size > 512 * 1024:
        return {}
    try:
        import yaml

        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        return {}
    return dict(value) if isinstance(value, dict) else {}


def _component_inventory(root: Path) -> dict[str, dict[str, Any]]:
    document = _load_yaml(root / ".maw/components.yaml")
    result: dict[str, dict[str, Any]] = {}
    for raw in document.get("components", []):
        item = _mapping(raw)
        key = str(item.get("key") or "").strip()
        if key and item.get("enabled") is not False:
            result[key] = item
    return result


def _safe_relative(value: object) -> str:
    text = str(value or "").strip().replace("\\", "/")
    relative = Path(text)
    if (
        not text
        or relative.is_absolute()
        or ".." in relative.parts
        or any(part in {".git", ".local"} for part in relative.parts)
    ):
        return ""
    return relative.as_posix()


def _command_for(root: Path, app_key: str, app: dict[str, Any]) -> tuple[str, str]:
    command_ref = str(app.get("command_ref") or "").strip().replace("\\", "/")
    relative = _safe_relative(command_ref)
    if relative:
        descriptor = _load_yaml(root / relative)
        commands = _mapping(descriptor.get("commands"))
        for key in ("dev", "start"):
            command = str(commands.get(key) or "").strip()
            if command:
                return command, key
    code_path = _safe_relative(app.get("code_path") or f"code/{app_key}")
    if code_path:
        package_path = root / code_path / "package.json"
        if package_path.is_file() and not package_path.is_symlink():
            try:
                package = json.loads(package_path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError):
                package = {}
            scripts = _mapping(package.get("scripts"))
            for key in ("dev", "start"):
                if str(scripts.get(key) or "").strip():
                    return f"npm --prefix {code_path} run {key}", f"package:{key}"
    return "", ""


def _looks_automatic(command: str) -> bool:
    value = command.strip()
    if not value or "\n" in value or "\r" in value:
        return False
    if "&&" in value:
        parts = value.split("&&")
        if len(parts) != 2 or not parts[0].strip().startswith("cd "):
            return False
        value = parts[1].strip()
    if any(marker in value for marker in (";", "|", "`", "$(", ">", "<", "&")):
        return False
    try:
        argv = shlex.split(value, posix=os.name != "nt")
    except ValueError:
        return False
    executable = argv[0].lower() if argv else ""
    return executable in {
        "bash", "bun", "composer", "docker", "gradle", "java", "make", "node",
        "npm", "npx", "php", "pnpm", "poetry", "python", "python3", "sh", "uv",
        "yarn", "yarnpkg",
    } or executable.startswith("./")


def _execution_step(root: Path, command: str) -> tuple[list[str], Path]:
    if not _looks_automatic(command):
        raise ValueError("local_dev_command_not_automatic")
    value = command.strip()
    cwd = root
    if "&&" in value:
        change_directory, value = value.split("&&", 1)
        try:
            change_argv = shlex.split(change_directory, posix=os.name != "nt")
        except ValueError as exc:
            raise ValueError("local_dev_command_directory_invalid") from exc
        if len(change_argv) != 2 or change_argv[0] != "cd":
            raise ValueError("local_dev_command_directory_invalid")
        relative = _safe_relative(change_argv[1])
        if not relative:
            raise ValueError("local_dev_command_directory_invalid")
        cwd = (root / relative).resolve()
        try:
            cwd.relative_to(root)
        except ValueError as exc:
            raise ValueError("local_dev_command_directory_invalid") from exc
        if not cwd.is_dir():
            raise ValueError("local_dev_command_directory_missing")
    try:
        argv = shlex.split(value.strip(), posix=os.name != "nt")
    except ValueError as exc:
        raise ValueError("local_dev_command_invalid") from exc
    if not argv:
        raise ValueError("local_dev_command_invalid")
    return argv, cwd


def _waits_for_launcher_completion(argv: list[str]) -> bool:
    """Return whether a detached service launcher must finish before success.

    ``docker compose up -d`` is a finite launcher, not the service process.  If
    it is detached again after a short grace period, a later Compose failure is
    incorrectly recorded as a successful development start.
    """

    normalized = [
        Path(item).name.lower() if index == 0 else item.lower()
        for index, item in enumerate(argv)
    ]
    return bool(
        len(normalized) >= 3
        and normalized[0] in {"docker", "docker.exe"}
        and normalized[1] == "compose"
        and "up" in normalized[2:]
        and any(item in {"-d", "--detach"} for item in normalized[2:])
    )


def _catalog(root: Path) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    runtime = MawConfigLoader(project_root=root, profile="dev").load_domain("app-runtime")
    runtime_root = _mapping(runtime.get("app_runtime"))
    components = _component_inventory(root)
    apps: dict[str, dict[str, Any]] = {}
    for raw_key, raw_app in sorted(_mapping(runtime_root.get("apps")).items()):
        app_key = str(raw_key).strip()
        app = _mapping(raw_app)
        component_ref = str(app.get("component_ref") or app_key).strip()
        component = components.get(component_ref)
        if not app_key or not component or app.get("enabled") is False:
            continue
        command, command_key = _command_for(root, app_key, app)
        apps[app_key] = {
            "app_key": app_key,
            "component_ref": component_ref,
            "component_type": str(component.get("type") or "custom"),
            "command": command,
            "command_key": command_key,
            "runnable": _looks_automatic(command),
            "local_url": str(app.get("local_url") or "").strip(),
        }
    return runtime_root, apps


def _resolve_selection(
    runtime_root: dict[str, Any],
    apps: dict[str, dict[str, Any]],
    overrides: list[str],
) -> tuple[str, list[str], list[str]]:
    defaults = _mapping(runtime_root.get("defaults"))
    preset = str(defaults.get("development_start_preset") or "default_application")
    if preset not in PRESETS:
        preset = "custom"
    requested = [str(item) for item in defaults.get("development_app_keys", [])]
    if overrides:
        preset = "custom"
        requested = overrides
    runnable = [key for key, item in apps.items() if item["runnable"]]
    if preset == "default_application":
        default_key = str(defaults.get("default_app_key") or "")
        selected = [default_key] if default_key in runnable else []
    elif preset == "frontend_backend":
        selected = []
        for component_type in ("backend", "frontend"):
            candidate = next(
                (key for key in runnable if apps[key]["component_type"] == component_type),
                "",
            )
            if candidate:
                selected.append(candidate)
    elif preset == "all_runnable":
        selected = runnable
    else:
        selected = [key for key in requested if key in runnable]
    unavailable = [key for key in requested if key not in runnable]
    return preset, selected, unavailable


def _pid_running(pid: int) -> bool:
    if pid <= 1:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _manifest(root: Path) -> tuple[Path, dict[str, Any]]:
    path = root / RUN_ROOT / MANIFEST_NAME
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        value = {}
    return path, _mapping(value)


def _write_manifest(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.chmod(temporary, 0o600)
    temporary.replace(path)


def _print_plan(preset: str, selected: list[str], apps: dict[str, dict[str, Any]]) -> None:
    print(f"本机开发启动方案：{PRESETS[preset]}")
    if not selected:
        print("- 当前没有选中可自动启动的服务。请在本地工作台的“环境与资源”中配置启动范围。")
    for key, item in apps.items():
        marker = "将启动" if key in selected else "不启动"
        capability = item["command_key"] if item["runnable"] else "需人工启动"
        print(f"- {key}: {marker} · {capability}")
        if key in selected and item["local_url"]:
            print(f"  验证入口：{item['local_url']}")


def _stop(root: Path) -> int:
    manifest_path, manifest = _manifest(root)
    stopped = 0
    for item in manifest.get("services", []):
        record = _mapping(item)
        pid = int(record.get("pid") or 0)
        if not _pid_running(pid):
            continue
        try:
            os.killpg(pid, signal.SIGTERM)
        except (OSError, ProcessLookupError):
            continue
        stopped += 1
        print(f"已请求停止 {record.get('app_key')}（PID {pid}）。")
    if manifest_path.exists():
        manifest_path.unlink()
    print(f"本次停止 {stopped} 个本机开发服务。")
    return 0


def _status(root: Path) -> int:
    _, manifest = _manifest(root)
    services = [_mapping(item) for item in manifest.get("services", [])]
    if not services:
        print("当前没有由 npm run dev 后台启动的服务。")
        return 0
    for item in services:
        running = _pid_running(int(item.get("pid") or 0))
        state = (
            "运行中"
            if running
            else "启动命令已完成"
            if item.get("launcher_status") == "completed"
            else "已停止"
        )
        scope = "当前选择" if item.get("selected", True) else "旧范围，仍保留进程"
        print(f"- {item.get('app_key')}: {state} · {scope} · 日志 {item.get('log_ref')}")
    return 0


def _run_background(root: Path, selected: list[str], apps: dict[str, dict[str, Any]]) -> int:
    manifest_path, previous = _manifest(root)
    previous_by_key = {
        str(_mapping(item).get("app_key") or ""): _mapping(item)
        for item in previous.get("services", [])
    }
    records: list[dict[str, Any]] = []
    failures: list[str] = []
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    for key, existing in previous_by_key.items():
        if key in selected or not _pid_running(int(existing.get("pid") or 0)):
            continue
        records.append({**existing, "selected": False})
    for key in selected:
        existing = previous_by_key.get(key, {})
        if _pid_running(int(existing.get("pid") or 0)):
            records.append({**existing, "selected": True})
            print(f"{key} 已在后台运行，保留现有进程。")
            continue
        log_path = manifest_path.parent / f"{key}.log"
        output = log_path.open("ab")
        try:
            argv, cwd = _execution_step(root, str(apps[key]["command"]))
            process = subprocess.Popen(
                argv,
                cwd=cwd,
                shell=False,
                stdin=subprocess.DEVNULL,
                stdout=output,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
        finally:
            output.close()
        if _waits_for_launcher_completion(argv):
            try:
                exit_code = process.wait(timeout=LAUNCHER_COMPLETION_TIMEOUT_SECONDS)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                except (OSError, ProcessLookupError):
                    pass
                failures.append(key)
                print(f"{key} 启动超时，请查看 {log_path.relative_to(root)}。", file=sys.stderr)
                continue
        else:
            time.sleep(0.35)
            exit_code = process.poll()
        if exit_code not in {None, 0}:
            failures.append(key)
            print(f"{key} 启动失败，请查看 {log_path.relative_to(root)}。", file=sys.stderr)
            continue
        records.append({
            "app_key": key,
            "pid": process.pid if exit_code is None else 0,
            "log_ref": log_path.relative_to(root).as_posix(),
            "command_source": apps[key]["command_key"],
            "selected": True,
            "launcher_status": "running" if exit_code is None else "completed",
        })
        if exit_code is None:
            print(f"{key} 已在后台启动（PID {process.pid}），日志：{log_path.relative_to(root)}")
        else:
            print(f"{key} 启动命令已成功完成，服务状态将由工作台入口复检。")
    _write_manifest(manifest_path, {"schema": "mawflow.local_dev_services.v1", "services": records})
    return 1 if failures else 0


def _run_foreground(root: Path, selected: list[str], apps: dict[str, dict[str, Any]]) -> int:
    processes: list[tuple[str, subprocess.Popen[Any]]] = []
    try:
        for key in selected:
            argv, cwd = _execution_step(root, str(apps[key]["command"]))
            process = subprocess.Popen(argv, cwd=cwd, shell=False, start_new_session=True)
            if _waits_for_launcher_completion(argv):
                try:
                    exit_code = process.wait(timeout=LAUNCHER_COMPLETION_TIMEOUT_SECONDS)
                except subprocess.TimeoutExpired:
                    try:
                        os.killpg(process.pid, signal.SIGTERM)
                    except (OSError, ProcessLookupError):
                        pass
                    print(f"{key} 启动超时。", file=sys.stderr)
                    return 124
                if exit_code != 0:
                    print(f"{key} 启动失败（退出码 {exit_code}）。", file=sys.stderr)
                    return int(exit_code)
                print(f"{key} 启动命令已成功完成，服务状态请通过本机入口复检。")
                continue
            processes.append((key, process))
            print(f"已启动 {key}（PID {process.pid}）。")
        while processes:
            for _, process in processes:
                code = process.poll()
                if code is not None:
                    return int(code)
            time.sleep(0.25)
    except KeyboardInterrupt:
        return 130
    finally:
        for _, process in processes:
            if process.poll() is None:
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                except (OSError, ProcessLookupError):
                    pass
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="按本机选择启动 Seed 项目的开发服务。")
    parser.add_argument("--root", default=".", help="项目根目录。")
    parser.add_argument("--app", action="append", default=[], help="临时只启动指定 app_key，可重复。")
    parser.add_argument("--background", action="store_true", help="后台启动并写入 .local/run 状态。")
    parser.add_argument("--list", action="store_true", help="只显示本次启动范围。")
    parser.add_argument("--status", action="store_true", help="查看后台服务状态。")
    parser.add_argument("--stop", action="store_true", help="停止由本脚本后台启动的服务。")
    args = parser.parse_args()
    root = Path(args.root).expanduser().resolve(strict=True)
    if args.stop:
        return _stop(root)
    if args.status:
        return _status(root)
    runtime_root, apps = _catalog(root)
    preset, selected, unavailable = _resolve_selection(runtime_root, apps, args.app)
    _print_plan(preset, selected, apps)
    if unavailable:
        print(f"以下服务不存在或不能自动启动：{'、'.join(unavailable)}。", file=sys.stderr)
    if args.list:
        return 0
    if not selected:
        return 2
    return _run_background(root, selected, apps) if args.background else _run_foreground(root, selected, apps)


if __name__ == "__main__":
    raise SystemExit(main())
