#!/usr/bin/env python3
"""Plan and optionally run project tests from the Seed Test Contract."""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import platform
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


try:
    import yaml
except ImportError:  # pragma: no cover - optional fallback
    yaml = None


TEST_TYPES = {
    "static",
    "unit",
    "component",
    "contract",
    "integration",
    "migration",
    "browser",
    "visual",
    "accessibility",
    "performance",
    "security",
    "smoke",
    "acceptance-assist",
}
RISK_ORDER = {"L0": 0, "L1": 1, "L2": 2, "L3": 3}
ENVIRONMENT_RISK = {
    "local": "L1",
    "test": "L1",
    "staging": "L2",
    "uat": "L2",
    "production": "L3",
}
COMMAND_SUITES = {"test", "lint", "typecheck", "build"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Plan project verification and optionally execute approved commands.",
    )
    parser.add_argument("--root", default=".", help="Project root. Default: current directory.")
    parser.add_argument(
        "--contract",
        default=".maw/testing.yaml",
        help="Project-relative Seed Test Contract path.",
    )
    parser.add_argument(
        "--component",
        action="append",
        default=[],
        help="Limit to a component key or app_key. Can be provided multiple times.",
    )
    parser.add_argument(
        "--changed-path",
        action="append",
        default=[],
        help="Project-relative changed path used by the planner. Repeatable.",
    )
    parser.add_argument("--task-scope", default="", help="Short task scope or acceptance tags.")
    parser.add_argument("--risk", choices=sorted(RISK_ORDER), default="")
    parser.add_argument(
        "--target-environment",
        choices=sorted(ENVIRONMENT_RISK),
        default="local",
    )
    parser.add_argument(
        "--execution-mode",
        choices=["plan", "execute"],
        default="",
        help="Explicit planner mode. --execute remains supported.",
    )
    parser.add_argument(
        "--suite",
        choices=["all", "test", "lint", "typecheck", "build"],
        default="all",
    )
    parser.add_argument("--execute", action="store_true", help="Run approved commands.")
    parser.add_argument("--timeout", type=int, default=900, help="Default per-command timeout.")
    parser.add_argument(
        "--log-dir",
        default="artifacts/script-runs/project-tests",
        help="Directory for redacted command logs and structured evidence.",
    )
    parser.add_argument("--task-key", default="")
    parser.add_argument("--task-version", default="")
    parser.add_argument("--format", choices=["json", "markdown", "text"], default="json")
    parser.add_argument("--output", default="-", help="Output path or '-' for stdout.")
    return parser


def _arg(args: argparse.Namespace, name: str, default: Any) -> Any:
    return getattr(args, name, default)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _fingerprint(value: object) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


def load_yaml(path: Path) -> Dict[str, Any]:
    if yaml is None or not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def project_relative(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def normalize_relative_path(value: object) -> str:
    text = str(value or "").strip().replace("\\", "/")
    if not text or text.startswith("/") or re.match(r"^[A-Za-z]:/", text):
        return ""
    parts = [item for item in text.split("/") if item not in {"", "."}]
    if not parts or ".." in parts:
        return ""
    return "/".join(parts)


def discover_components(root: Path) -> List[Dict[str, str]]:
    components_doc = load_yaml(root / ".maw" / "components.yaml")
    configured = components_doc.get("components") or []
    components: List[Dict[str, str]] = []
    if isinstance(configured, list):
        for item in configured:
            if not isinstance(item, dict) or item.get("enabled") is False:
                continue
            key = str(item.get("key") or "").strip()
            app_key = str(item.get("app_key") or key).strip()
            rel_path = normalize_relative_path(item.get("path") or f"code/{app_key}")
            if key and rel_path and (root / rel_path).is_dir():
                components.append({"key": key, "app_key": app_key or key, "path": rel_path})
    if components:
        return components

    code_dir = root / "code"
    if not code_dir.is_dir():
        return []
    for path in sorted(code_dir.iterdir()):
        if path.is_dir():
            components.append(
                {"key": path.name, "app_key": path.name, "path": project_relative(root, path)}
            )
    return components


def choose_package_manager(component_dir: Path) -> str:
    if (component_dir / "pnpm-lock.yaml").is_file():
        return "pnpm"
    if (component_dir / "yarn.lock").is_file():
        return "yarn"
    return "npm"


def package_manager_command(manager: str, script_name: str) -> List[str]:
    return [manager, "run", script_name]


def load_package_scripts(component_dir: Path) -> Dict[str, Any]:
    package_json = component_dir / "package.json"
    if not package_json.is_file():
        return {}
    try:
        data = json.loads(package_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    scripts = data.get("scripts") or {}
    return scripts if isinstance(scripts, dict) else {}


def makefile_has_target(component_dir: Path, target: str) -> bool:
    makefile = component_dir / "Makefile"
    if not makefile.is_file():
        return False
    pattern = re.compile(rf"^{re.escape(target)}\s*:", re.MULTILINE)
    return bool(pattern.search(makefile.read_text(encoding="utf-8", errors="replace")))


def contains_python_test_files(path: Path) -> bool:
    if not path.exists():
        return False
    roots = [path] if path.is_dir() else [path.parent]
    for current_root in roots:
        for candidate in current_root.rglob("*.py"):
            if candidate.name.startswith("test_") or candidate.name.endswith("_test.py"):
                return True
    return False


def detect_python_test(component_dir: Path) -> bool:
    markers = [component_dir / "pytest.ini", component_dir / "pyproject.toml", component_dir / "setup.cfg"]
    if any(path.exists() for path in markers):
        return True
    tests_dir = component_dir / "tests"
    if tests_dir.is_dir() and contains_python_test_files(tests_dir):
        return True
    return contains_python_test_files(component_dir)


def python_test_command(component_dir: Path) -> List[str]:
    candidates = (
        ".venv/bin/python",
        "venv/bin/python",
        ".venv/Scripts/python.exe",
        "venv/Scripts/python.exe",
    )
    for relative_path in candidates:
        if (component_dir / relative_path).is_file():
            return [relative_path, "-m", "pytest"]
    return ["python3", "-m", "pytest"]


def add_command(
    commands: List[Dict[str, Any]],
    component: Dict[str, str],
    suite: str,
    command: List[str],
    source: str,
) -> None:
    commands.append(
        {
            "component": component["key"],
            "app_key": component["app_key"],
            "suite": suite,
            "cwd": component["path"],
            "command": command,
            "source": source,
            "status": "planned",
            "exit_code": None,
            "log_path": "",
        }
    )


def discover_commands(root: Path, component: Dict[str, str], suite_filter: str) -> List[Dict[str, Any]]:
    component_dir = root / component["path"]
    commands: List[Dict[str, Any]] = []
    package_scripts = load_package_scripts(component_dir)
    manager = choose_package_manager(component_dir)
    npm_mapping = {
        "test": ["test"],
        "lint": ["lint"],
        "typecheck": ["typecheck", "type-check", "check"],
        "build": ["build"],
    }
    selected_suites = list(npm_mapping) if suite_filter == "all" else [suite_filter]
    for suite in selected_suites:
        for script_name in npm_mapping.get(suite, []):
            if script_name in package_scripts:
                add_command(
                    commands,
                    component,
                    suite,
                    package_manager_command(manager, script_name),
                    f"package.json#scripts.{script_name}",
                )
                break
    if suite_filter in {"all", "test"}:
        if detect_python_test(component_dir):
            add_command(
                commands,
                component,
                "test",
                python_test_command(component_dir),
                "python",
            )
        if makefile_has_target(component_dir, "test"):
            add_command(commands, component, "test", ["make", "test"], "Makefile")
    return commands


def _contract_items(contract: Dict[str, Any], key: str) -> List[Dict[str, Any]]:
    value = contract.get(key)
    return [dict(item) for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def validate_contract(contract: Dict[str, Any], *, contract_path: str) -> List[str]:
    errors: List[str] = []
    if not contract:
        return []
    if contract.get("schema") != "maw.seed.testing.v1":
        errors.append("testing_contract_schema_invalid")
    if not re.match(r"^[0-9]+\.[0-9]+\.[0-9]+$", str(contract.get("contract_version") or "")):
        errors.append("testing_contract_version_invalid")
    registry = contract.get("command_registry")
    if not isinstance(registry, dict):
        errors.append("testing_contract_command_registry_missing")
        registry = {}
    journey_keys = {str(item.get("key") or "") for item in _contract_items(contract, "journeys")}
    suite_keys: set[str] = set()
    for suite in _contract_items(contract, "suites"):
        key = str(suite.get("key") or "").strip()
        if not key or key in suite_keys:
            errors.append("testing_contract_suite_key_invalid")
        suite_keys.add(key)
        if str(suite.get("type") or "") not in TEST_TYPES:
            errors.append(f"testing_contract_suite_type_invalid:{key}")
        if str(suite.get("risk") or "") not in RISK_ORDER:
            errors.append(f"testing_contract_suite_risk_invalid:{key}")
        command_ref = str(suite.get("command_ref") or "")
        command_spec = registry.get(command_ref) if isinstance(registry, dict) else None
        if not isinstance(command_spec, dict):
            errors.append(f"testing_contract_command_ref_unknown:{key}")
            continue
        resolver = str(command_spec.get("resolver") or "")
        if resolver == "component_suite":
            if str(command_spec.get("suite") or "") not in COMMAND_SUITES:
                errors.append(f"testing_contract_command_suite_invalid:{key}")
        elif resolver == "browser_journey":
            if str(command_spec.get("journey") or "") not in journey_keys:
                errors.append(f"testing_contract_journey_ref_unknown:{key}")
        else:
            errors.append(f"testing_contract_resolver_invalid:{key}")
    for gate in _contract_items(contract, "human_gates"):
        if gate.get("automatic") is not False:
            errors.append(f"testing_contract_human_gate_must_be_manual:{gate.get('key', '')}")
    for journey in _contract_items(contract, "journeys"):
        for step in journey.get("steps", []) if isinstance(journey.get("steps"), list) else []:
            if isinstance(step, dict) and str(step.get("semantic") or "").startswith((".", "#", "[")):
                errors.append(f"testing_contract_css_semantic_forbidden:{journey.get('key', '')}")
    if contract_path.startswith("/") or ".." in Path(contract_path).parts:
        errors.append("testing_contract_path_invalid")
    return sorted(set(errors))


def _path_matches(path: str, pattern: str) -> bool:
    normalized = normalize_relative_path(path)
    candidate = normalize_relative_path(pattern)
    return bool(
        normalized
        and candidate
        and (fnmatch.fnmatch(normalized, candidate) or normalized == candidate.rstrip("/*"))
    )


def _module_paths(item: Dict[str, Any]) -> List[str]:
    paths: List[str] = []
    for key, value in item.items():
        if key.endswith("_paths") and isinstance(value, list):
            paths.extend(normalize_relative_path(entry) for entry in value)
    doc = normalize_relative_path(item.get("doc"))
    changelog = normalize_relative_path(item.get("changelog_path"))
    return [item for item in [*paths, doc, changelog] if item]


def impacted_modules(root: Path, changed_paths: List[str]) -> set[str]:
    module_doc = load_yaml(root / ".maw" / "modules.yaml")
    modules = [dict(item) for item in module_doc.get("modules", []) if isinstance(item, dict)]
    direct = {
        str(item.get("key") or "")
        for item in modules
        if any(
            path == prefix or path.startswith(prefix.rstrip("/") + "/")
            for path in changed_paths
            for prefix in _module_paths(item)
        )
    }
    impacted = set(direct)
    changed = True
    while changed:
        changed = False
        for item in modules:
            key = str(item.get("key") or "")
            dependencies = {str(value) for value in item.get("dependencies", [])}
            if key and key not in impacted and dependencies & impacted:
                impacted.add(key)
                changed = True
    return impacted


def _suite_filter_matches(suite: Dict[str, Any], command_spec: Dict[str, Any], suite_filter: str) -> bool:
    if suite_filter == "all":
        return True
    if str(command_spec.get("resolver") or "") == "browser_journey":
        return suite_filter == "test"
    return str(command_spec.get("suite") or "") == suite_filter


def select_contract_suites(
    root: Path,
    contract: Dict[str, Any],
    *,
    changed_paths: List[str],
    component_filter: set[str],
    suite_filter: str,
    task_scope: str,
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    registry = contract.get("command_registry") or {}
    modules = impacted_modules(root, changed_paths)
    task_tokens = {item for item in re.split(r"[^a-zA-Z0-9_-]+", task_scope.lower()) if item}
    selected: List[Dict[str, Any]] = []
    skipped: List[Dict[str, Any]] = []
    for raw_suite in _contract_items(contract, "suites"):
        suite = dict(raw_suite)
        key = str(suite.get("key") or "")
        command_spec = dict(registry.get(str(suite.get("command_ref") or "")) or {})
        component = str(suite.get("component") or "")
        if component_filter and component not in component_filter:
            skipped.append({"key": key, "reason": "component_filter"})
            continue
        if not _suite_filter_matches(suite, command_spec, suite_filter):
            skipped.append({"key": key, "reason": "suite_filter"})
            continue
        selection = dict(suite.get("selection") or {})
        patterns = [str(item) for item in selection.get("paths", [])]
        suite_modules = {str(item) for item in selection.get("modules", [])}
        suite_tags = {str(item).lower() for item in selection.get("task_tags", [])}
        reasons: List[str] = []
        if not changed_paths and suite.get("required"):
            reasons.append("required_default")
        if changed_paths and any(
            _path_matches(path, pattern) for path in changed_paths for pattern in patterns
        ):
            reasons.append("changed_path")
        if modules & suite_modules:
            reasons.append("module_dependency")
        if task_tokens & suite_tags:
            reasons.append("task_scope")
        if selection.get("always") is True:
            reasons.append("always")
        if reasons:
            suite["selection_reasons"] = sorted(set(reasons))
            selected.append(suite)
        else:
            skipped.append({"key": key, "reason": "not_impacted"})
    return selected, skipped


def resolve_suite_commands(
    root: Path,
    components: List[Dict[str, str]],
    contract: Dict[str, Any],
    suites: List[Dict[str, Any]],
) -> tuple[List[Dict[str, Any]], List[str], List[Dict[str, Any]]]:
    registry = contract.get("command_registry") or {}
    component_map = {
        value: item
        for item in components
        for value in {item["key"], item["app_key"]}
    }
    commands: List[Dict[str, Any]] = []
    blockers: List[str] = []
    external: List[Dict[str, Any]] = []
    for suite in suites:
        key = str(suite.get("key") or "")
        command_ref = str(suite.get("command_ref") or "")
        command_spec = dict(registry.get(command_ref) or {})
        resolver = str(command_spec.get("resolver") or "")
        if resolver == "browser_journey":
            external.append(
                {
                    "suite_key": key,
                    "journey_key": str(command_spec.get("journey") or ""),
                    "runner": "browser.acceptance.run",
                    "required": bool(suite.get("required")),
                }
            )
            continue
        component_key = str(command_spec.get("component") or suite.get("component") or "")
        component = component_map.get(component_key)
        if component is None:
            blockers.append(f"testing_component_missing:{key}")
            continue
        discovered = discover_commands(root, component, str(command_spec.get("suite") or "test"))
        if not discovered:
            blockers.append(f"testing_command_unresolved:{key}")
            continue
        for command in discovered:
            command.update(
                {
                    "suite_key": key,
                    "test_type": str(suite.get("type") or "unit"),
                    "risk": str(suite.get("risk") or "L0"),
                    "required": bool(suite.get("required")),
                    "command_ref": command_ref,
                    "timeout_seconds": int(suite.get("timeout_seconds") or 0),
                }
            )
            commands.append(command)
    return commands, blockers, external


def command_available(command: List[str], cwd: Path) -> bool:
    if not command:
        return False
    executable = command[0]
    if "/" in executable or "\\" in executable:
        return (cwd / executable).is_file()
    return shutil.which(executable) is not None


def _redact_log(output: str) -> str:
    patterns = [
        (re.compile(r"(?i)(authorization\s*[:=]\s*)([^\s]+)"), r"\1[REDACTED]"),
        (re.compile(r"(?i)((?:token|password|secret|api[_-]?key)\s*[:=]\s*)([^\s]+)"), r"\1[REDACTED]"),
        (re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]+"), r"\1[REDACTED]"),
        (
            re.compile(
                r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----"
            ),
            "[REDACTED PRIVATE KEY]",
        ),
    ]
    redacted = output
    for pattern, replacement in patterns:
        redacted = pattern.sub(replacement, redacted)
    return redacted


def _test_counts(output: str) -> Dict[str, int]:
    counts = {"passed": 0, "failed": 0, "skipped": 0}
    for key in counts:
        matches = re.findall(rf"(\d+)\s+{key}", output)
        if matches:
            counts[key] = int(matches[-1])
        tap_key = {"passed": "pass", "failed": "fail", "skipped": "skipped"}[key]
        tap = re.findall(rf"^# {tap_key} (\d+)$", output, flags=re.MULTILINE)
        if tap:
            counts[key] = int(tap[-1])
    return counts


def run_command(root: Path, item: Dict[str, Any], log_dir: Path, timeout: int) -> Dict[str, Any]:
    component = item["component"]
    suite_key = str(item.get("suite_key") or item.get("suite") or "test")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    suffix = hashlib.sha256(json.dumps(item["command"]).encode("utf-8")).hexdigest()[:8]
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{timestamp}-{component}-{suite_key}-{suffix}.log"
    rel_log_path = project_relative(root, log_path)
    started_at = _now()
    started = time.monotonic()
    command_cwd = root / item["cwd"]
    if not command_available(item["command"], command_cwd):
        item.update(
            {
                "status": "blocked",
                "exit_code": 40,
                "log_path": rel_log_path,
                "summary": f"Command not available: {item['command'][0]}",
                "started_at": started_at,
                "completed_at": _now(),
                "duration_seconds": round(time.monotonic() - started, 3),
                "counts": {"passed": 0, "failed": 0, "skipped": 0},
            }
        )
        log_path.write_text(item["summary"] + "\n", encoding="utf-8")
        return item
    command_timeout = int(item.get("timeout_seconds") or timeout)
    proc = subprocess.run(
        item["command"],
        cwd=str(command_cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=command_timeout,
        check=False,
    )
    output = _redact_log(proc.stdout or "")
    log_path.write_text(output, encoding="utf-8")
    counts = _test_counts(output)
    common = {
        "started_at": started_at,
        "completed_at": _now(),
        "duration_seconds": round(time.monotonic() - started, 3),
        "counts": counts,
        "log_path": rel_log_path,
    }
    if is_pytest_no_tests(item, proc.returncode, output):
        item.update(
            {
                **common,
                "status": "skipped",
                "exit_code": proc.returncode,
                "summary": "skipped: pytest collected no tests",
            }
        )
        return item
    item.update(
        {
            **common,
            "status": "passed" if proc.returncode == 0 else "failed",
            "exit_code": proc.returncode,
            "summary": "passed" if proc.returncode == 0 else f"failed with exit code {proc.returncode}",
        }
    )
    return item


def is_pytest_no_tests(item: Dict[str, Any], returncode: int, output: str) -> bool:
    command = item.get("command") or []
    return (
        returncode == 5
        and len(command) >= 3
        and command[-1] == "pytest"
        and ("no tests ran" in output or "collected 0 items" in output)
    )


def build_environment() -> Dict[str, Any]:
    return {
        "os": platform.system().lower(),
        "python": f"{sys.version_info.major}.{sys.version_info.minor}",
        "workspace": "project_root",
    }


def _git_revision(root: Path) -> str:
    proc = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(root),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return proc.stdout.strip() if proc.returncode == 0 else "unknown"


def _selected_suite_summary(
    suites: List[Dict[str, Any]],
    external: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    external_map = {str(item.get("suite_key") or ""): item for item in external}
    result: List[Dict[str, Any]] = []
    for suite in suites:
        key = str(suite.get("key") or "")
        external_item = external_map.get(key)
        result.append(
            {
                "key": key,
                "type": str(suite.get("type") or ""),
                "component": str(suite.get("component") or ""),
                "command_ref": str(suite.get("command_ref") or ""),
                "required": bool(suite.get("required")),
                "risk": str(suite.get("risk") or "L0"),
                "selection_reasons": list(suite.get("selection_reasons") or []),
                "execution": "external_capability" if external_item else "named_command",
                **({"journey_key": external_item.get("journey_key", "")} if external_item else {}),
            }
        )
    return result


def _manual_gates(contract: Dict[str, Any], target_environment: str) -> List[Dict[str, Any]]:
    gates: List[Dict[str, Any]] = []
    for gate in _contract_items(contract, "human_gates"):
        required_for = [str(item) for item in gate.get("required_for", [])]
        if required_for and target_environment not in required_for:
            continue
        gates.append(
            {
                "key": str(gate.get("key") or ""),
                "automatic": False,
                "status": "pending",
                "evidence_required": bool(gate.get("evidence_required")),
            }
        )
    return gates


def _risk_for(suites: List[Dict[str, Any]], requested: str, environment: str) -> str:
    risks = [str(item.get("risk") or "L0") for item in suites]
    risks.extend([requested or "L0", ENVIRONMENT_RISK.get(environment, "L1")])
    return max(risks, key=lambda item: RISK_ORDER.get(item, 0))


def _write_evidence(
    root: Path,
    log_dir: Path,
    payload: Dict[str, Any],
    args: argparse.Namespace,
    started_at: str,
) -> str:
    plan = payload["test_plan"]
    commands = payload["project_tests"]["commands"]
    selected = plan["selected_suites"]
    suites: List[Dict[str, Any]] = []
    for suite in selected:
        items = [item for item in commands if item.get("suite_key") == suite["key"]]
        if suite.get("execution") == "external_capability":
            status = "pending_external"
        elif any(item.get("status") == "failed" for item in items):
            status = "failed"
        elif any(item.get("status") == "blocked" for item in items):
            status = "blocked"
        elif items and all(item.get("status") in {"passed", "skipped"} for item in items):
            status = "passed"
        else:
            status = "not_run"
        suites.append(
            {
                "key": suite["key"],
                "status": status,
                "command_ref": suite.get("command_ref", ""),
                "exit_code": next(
                    (
                        item.get("exit_code")
                        for item in items
                        if item.get("exit_code") not in {None, 0}
                    ),
                    0 if items else None,
                ),
                "duration_seconds": round(
                    sum(float(item.get("duration_seconds") or 0) for item in items), 3
                ),
                "counts": {
                    name: sum(
                        int(dict(item.get("counts") or {}).get(name) or 0) for item in items
                    )
                    for name in ("passed", "failed", "skipped")
                },
                "artifact_refs": [item["log_path"] for item in items if item.get("log_path")],
            }
        )
    statuses = {str(item.get("status") or "") for item in suites}
    if "failed" in statuses:
        automatic_status = "failed"
    elif "blocked" in statuses:
        automatic_status = "blocked"
    elif statuses & {"pending_external", "not_run"}:
        automatic_status = "partial"
    else:
        automatic_status = "passed"
    evidence = {
        "schema": "maw.test_evidence.v1",
        "task_key": str(_arg(args, "task_key", "")),
        "task_version": str(_arg(args, "task_version", "")),
        "source_revision": _git_revision(root),
        "test_plan_fingerprint": plan["fingerprint"],
        "started_at": started_at,
        "completed_at": _now(),
        "suites": suites,
        "browser_journeys": [
            {
                "key": item.get("journey_key", ""),
                "status": "pending_external",
                "screenshot_refs": [],
                "trace_ref": "",
                "console_error_count": None,
            }
            for item in selected
            if item.get("execution") == "external_capability"
        ],
        "human_gates": plan["manual_gates"],
        "overall": {
            "automatic_status": automatic_status,
            "human_acceptance_required": any(
                item.get("key") == "business_acceptance" for item in plan["manual_gates"]
            ),
        },
    }
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    target = log_dir / f"{timestamp}-test-evidence.json"
    target.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return project_relative(root, target)


def build_payload(args: argparse.Namespace) -> Dict[str, Any]:
    started_at = _now()
    root = Path(_arg(args, "root", ".")).expanduser().resolve()
    component_filter = {str(item) for item in (_arg(args, "component", []) or [])}
    changed_paths = [
        normalized
        for value in (_arg(args, "changed_path", []) or [])
        if (normalized := normalize_relative_path(value))
    ]
    invalid_changed_paths = [
        str(value)
        for value in (_arg(args, "changed_path", []) or [])
        if not normalize_relative_path(value)
    ]
    execution_mode = str(_arg(args, "execution_mode", "") or "")
    execute = bool(_arg(args, "execute", False) or execution_mode == "execute")
    if execution_mode == "plan":
        execute = False
    selected_components = [
        item
        for item in discover_components(root)
        if not component_filter
        or item["key"] in component_filter
        or item["app_key"] in component_filter
    ]

    contract_rel = normalize_relative_path(_arg(args, "contract", ".maw/testing.yaml"))
    contract_path = root / contract_rel if contract_rel else root / ".maw/testing.yaml"
    contract = load_yaml(contract_path)
    contract_status = "active" if contract else "missing"
    contract_errors = validate_contract(contract, contract_path=contract_rel)
    warnings: List[str] = []
    blockers = list(contract_errors)
    if invalid_changed_paths:
        blockers.append("changed_path_invalid")
    suites: List[Dict[str, Any]] = []
    skipped_suites: List[Dict[str, Any]] = []
    external: List[Dict[str, Any]] = []
    commands: List[Dict[str, Any]] = []
    if contract and not contract_errors:
        suites, skipped_suites = select_contract_suites(
            root,
            contract,
            changed_paths=changed_paths,
            component_filter=component_filter,
            suite_filter=str(_arg(args, "suite", "all")),
            task_scope=str(_arg(args, "task_scope", "")),
        )
        commands, resolution_blockers, external = resolve_suite_commands(
            root, selected_components, contract, suites
        )
        blockers.extend(resolution_blockers)
    else:
        if not contract:
            warnings.append("Seed Test Contract missing; using legacy component discovery.")
        for component in selected_components:
            commands.extend(
                discover_commands(root, component, str(_arg(args, "suite", "all")))
            )

    if not selected_components:
        warnings.append("No components found from .maw/components.yaml or code/*.")
    if selected_components and not commands and not external:
        if contract:
            warnings.append("No approved test commands or browser journeys were selected.")
        else:
            warnings.append(
                "No test, lint, typecheck, build, pytest, or Makefile test commands were discovered."
            )

    target_environment = str(_arg(args, "target_environment", "local"))
    manual_gates = _manual_gates(contract, target_environment) if contract else []
    selected_summary = _selected_suite_summary(suites, external)
    required_apps = sorted(
        {
            str(item.get("component") or "")
            for item in selected_summary
            if str(item.get("component") or "")
        }
    )
    artifacts = dict(contract.get("artifacts") or {}) if contract else {}
    evidence_requirements = sorted(
        [key for key, value in artifacts.items() if value not in {False, "never", None}]
    )
    plan_core = {
        "schema": "maw.test_plan.v1",
        "project": str(
            dict(load_yaml(root / ".maw" / "project.yaml").get("project") or {}).get("key")
            or root.name
        ),
        "contract": {
            "status": contract_status,
            "path": contract_rel or ".maw/testing.yaml",
            "schema": str(contract.get("schema") or ""),
            "version": str(contract.get("contract_version") or ""),
        },
        "changed_paths": changed_paths,
        "task_scope": str(_arg(args, "task_scope", "")),
        "target_environment": target_environment,
        "selected_suites": selected_summary,
        "skipped_suites": skipped_suites,
        "manual_gates": manual_gates,
        "required_apps": required_apps,
        "estimated_risk": _risk_for(
            suites, str(_arg(args, "risk", "")), target_environment
        ),
        "evidence_requirements": evidence_requirements,
        "blocked_by": sorted(set(blockers)),
    }
    plan_core["fingerprint"] = _fingerprint(plan_core)

    log_dir = root / str(_arg(args, "log_dir", "artifacts/script-runs/project-tests"))
    if execute and not blockers:
        executed: List[Dict[str, Any]] = []
        for item in commands:
            try:
                executed.append(
                    run_command(root, item, log_dir, int(_arg(args, "timeout", 900)))
                )
            except subprocess.TimeoutExpired:
                item.update(
                    {
                        "status": "failed",
                        "exit_code": 40,
                        "summary": (
                            "timed out after "
                            f"{item.get('timeout_seconds') or _arg(args, 'timeout', 900)}s"
                        ),
                        "completed_at": _now(),
                    }
                )
                executed.append(item)
        commands = executed
        for item in external:
            if item.get("required"):
                plan_core["blocked_by"].append(
                    f"external_browser_journey_pending:{item.get('journey_key', '')}"
                )
        plan_core["blocked_by"] = sorted(set(plan_core["blocked_by"]))

    failures = [item for item in commands if item.get("status") in {"failed", "blocked"}]
    if contract_errors or invalid_changed_paths:
        status = "blocked"
        next_action = "stop"
        ai_takeover_reason = "testing_contract_invalid"
    elif failures or (execute and plan_core["blocked_by"]):
        status = "needs_ai"
        next_action = "ai_takeover"
        ai_takeover_reason = (
            "project_test_command_failed" if failures else "external_test_runner_required"
        )
    else:
        status = "success"
        next_action = "continue"
        ai_takeover_reason = ""

    mode = "execute" if execute else "plan"
    summary = (
        f"Project test {mode} selected {len(selected_summary) or len(commands)} suite(s) "
        f"across {len(selected_components)} components."
    )
    if failures:
        summary += f" {len(failures)} command(s) need attention."
    payload: Dict[str, Any] = {
        "status": status,
        "summary": summary,
        "next_action": next_action,
        "changed_paths": changed_paths,
        "evidence_refs": [
            {"path": ".maw/components.yaml", "kind": "config"},
            {"path": contract_rel or ".maw/testing.yaml", "kind": "test_contract"},
            {"path": "code/", "kind": "component_root"},
        ],
        "log_path": str(_arg(args, "log_dir", "")) if execute else "",
        "state_path": "",
        "environment": build_environment(),
        "warnings": warnings,
        "ai_takeover_reason": ai_takeover_reason,
        "test_plan": plan_core,
        "project_tests": {
            "mode": mode,
            "suite": str(_arg(args, "suite", "all")),
            "components": selected_components,
            "commands": commands,
            "external_runners": external,
            "failure_count": len(failures),
        },
    }
    if execute:
        evidence_path = _write_evidence(root, log_dir, payload, args, started_at)
        payload["test_evidence_ref"] = evidence_path
        payload["evidence_refs"].append({"path": evidence_path, "kind": "test_evidence"})
    return payload


def render_markdown(payload: Dict[str, Any]) -> str:
    tests = payload["project_tests"]
    plan = payload["test_plan"]
    lines = [
        f"# {payload['status']}",
        "",
        payload["summary"],
        "",
        f"- schema: {plan['schema']}",
        f"- contract: {plan['contract']['status']} {plan['contract']['version']}",
        f"- mode: {tests['mode']}",
        f"- selected suites: {len(plan['selected_suites'])}",
        f"- commands: {len(tests['commands'])}",
        f"- failures: {tests['failure_count']}",
        f"- estimated risk: {plan['estimated_risk']}",
        f"- manual gates: {len(plan['manual_gates'])}",
    ]
    if plan["blocked_by"]:
        lines.append(f"- blocked_by: {', '.join(plan['blocked_by'])}")
    if payload.get("test_evidence_ref"):
        lines.append(f"- evidence: {payload['test_evidence_ref']}")
    return "\n".join(lines) + "\n"


def render_text(payload: Dict[str, Any]) -> str:
    tests = payload["project_tests"]
    plan = payload["test_plan"]
    lines = [
        f"status: {payload['status']}",
        f"summary: {payload['summary']}",
        f"next_action: {payload['next_action']}",
        f"mode: {tests['mode']}",
        f"selected_suites: {len(plan['selected_suites'])}",
        f"commands: {len(tests['commands'])}",
        f"failures: {tests['failure_count']}",
        f"estimated_risk: {plan['estimated_risk']}",
    ]
    if payload["ai_takeover_reason"]:
        lines.append(f"ai_takeover_reason: {payload['ai_takeover_reason']}")
    return "\n".join(lines) + "\n"


def write_output(payload: Dict[str, Any], output_format: str, output_path: str) -> None:
    if output_format == "json":
        text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    elif output_format == "markdown":
        text = render_markdown(payload)
    else:
        text = render_text(payload)
    if output_path == "-":
        print(text, end="")
    else:
        Path(output_path).write_text(text, encoding="utf-8")


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    payload = build_payload(args)
    write_output(payload, args.format, args.output)
    if payload["status"] == "blocked":
        return 20
    return 10 if payload["status"] == "needs_ai" else 0


if __name__ == "__main__":
    raise SystemExit(main())
