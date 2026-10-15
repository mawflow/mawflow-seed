"""Public CLI presentation contract. No account, Host or filesystem writes."""
from __future__ import annotations

import argparse
from functools import wraps
from importlib.metadata import PackageNotFoundError, version
import json
import os
import re
import sys

from .catalog import SEED_VERSION


def error_code(value: object, fallback: str = "command_failed") -> str:
    candidate = str(value or "").partition(":")[0]
    return candidate if re.fullmatch(r"[a-z][a-z0-9_]{1,95}", candidate) else fallback


def json_result(payload):
    if not isinstance(payload, dict):
        return payload
    result = dict(payload)
    if result.get("error") or result.get("status") in {"blocked", "failed", "needs_attention"}:
        findings = [item for name in ("blockers", "issues", "checks") for item in (result.get(name) if isinstance(result.get(name), list) else [])]
        finding = next((item.get("code") for item in findings if isinstance(item, dict)
                        and (item.get("severity") == "error" or item.get("status") == "blocked" or item in result.get("blockers", []))), None)
        code = error_code(result.get("error") or finding, "command_" + str(result.get("status") or "failed"))
        result.setdefault("error_code", code)
        result.setdefault("exit_code", 1)
    return result


def print_json(payload, *, file=None):
    print(json.dumps(json_result(payload), ensure_ascii=False, indent=2, sort_keys=True, default=str), file=file)


class CliParser(argparse.ArgumentParser):
    def error(self, message):
        # argparse messages can echo argv credentials or private paths.
        print_json({"schema": "mawflow.cli_error.v1", "status": "failed", "error": "cli_usage_error",
                    "exit_code": 2, "message": "Invalid command or arguments; use --help.", "mutated": False}, file=sys.stderr)
        self.exit(2)


class JsonVersionAction(argparse.Action):
    def __init__(self, option_strings, dest, version=None, **kwargs):
        super().__init__(option_strings, dest, nargs=0, **kwargs)
        self.version = version

    def __call__(self, parser, namespace, values, option_string=None):
        # argparse's normal version action wraps long JSON strings inside paths.
        parser._print_message(str(self.version) + "\n", sys.stdout)
        parser.exit(0)


def guard_cli(function):
    @wraps(function)
    def run(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except (OSError, ValueError) as exc:
            code = error_code(exc) if isinstance(exc, ValueError) and not isinstance(exc, json.JSONDecodeError) else "cli_io_error"
            print_json({"schema": "mawflow.cli_error.v1", "status": "failed", "error": code, "exit_code": 1})
            return 1
    return run


def _installed(name):
    try:
        return version(name)
    except PackageNotFoundError:
        return None


def runtime_info(*, profile="seed-cli", host_version=None, cli_version=None):
    selected = os.environ.get("MAWFLOW_EFFECTIVE_PROFILE", "")
    if selected not in {"seed-cli", "desktop-host", "workspace-server"}:
        selected = profile
    launcher = os.environ.get("MAWFLOW_LAUNCHER_VERSION", "")
    return {"schema": "mawflow.cli_runtime.v1", "cli_contract_version": 1, "status": "ready", "profile": selected,
            "profile_source": "npm_launcher" if selected == os.environ.get("MAWFLOW_EFFECTIVE_PROFILE") else "python_entrypoint",
            "launcher_version": launcher if re.fullmatch(r"[0-9][0-9A-Za-z.+-]{0,63}", launcher) else None,
            "cli_version": cli_version, "host_version": host_version, "seed_version": SEED_VERSION,
            "version_sources": {"seed_version": "source_catalog", "host_version": "source_module" if host_version else None, "cli_version": "source_module" if cli_version else None},
            "installed_metadata": {"seed_version": _installed("mawflow-seed-kit"),
                                   "host_version": _installed("mawflow-host") if host_version else None,
                                   "cli_version": _installed("mawflow-cli") if cli_version else None},
            "executable": sys.executable, "mutated": False}


def drift_exit_code(result):
    code = 0 if result.get("status") in {"up_to_date", "behind", "ahead", "baseline_missing", "seed_contract_behind"} else 1
    if code:
        result["error_code"] = error_code(result.get("status"))
        result["exit_code"] = code
    return code


def project_doctor_output(result):
    """Publish diagnostics without compiled/shared/local configuration bodies."""
    keys = ("schema", "contract_version", "contract_fingerprint", "status", "editable", "migration_required",
            "tool_compatibility", "summary", "fingerprint")
    output = {key: result[key] for key in keys if key in result}
    issues = sorted(result.get("issues", []), key=lambda item: (str(item.get("source_ref", "")), str(item.get("code", "")), str(item.get("severity", ""))))
    diagnostics = sorted((item for item in result.get("diagnostics", []) if item.get("status") != "loaded"), key=lambda item: (str(item.get("source_ref", "")), str(item.get("status", ""))))
    # Source paths/codes are useful; raw messages can contain configuration values.
    output["issues"] = [{key: item[key] for key in ("code", "source_ref", "severity") if key in item} for item in issues[:50]]
    output["diagnostics"] = [{key: item[key] for key in ("source_ref", "required", "status") if key in item} for item in diagnostics[:50]]
    output["presentation"] = {"mode": "summary", "issue_count": len(issues), "diagnostic_count": len(diagnostics),
                              "issues_omitted": max(0, len(issues) - 50), "diagnostics_omitted": max(0, len(diagnostics) - 50)}
    if isinstance(output.get("tool_compatibility"), dict):
        output["tool_compatibility"] = {key: value[:128] if isinstance(value, str) else value for key, value in output["tool_compatibility"].items()}
    output["mutated"] = False
    return output
