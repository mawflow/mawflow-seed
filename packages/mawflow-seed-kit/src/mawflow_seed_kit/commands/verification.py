"""A confirmation boundary around registered Seed Test Contract commands."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from mawflow_seed_kit import testing


def verify_project(root: str, *, execute: bool = False, confirmation: str = "", component: list[str] | None = None, suite: str = "all", task_key: str = "", task_version: str = "") -> dict:
    project = Path(root).expanduser().resolve(strict=True)
    contract = project / ".maw/testing.yaml"
    if not contract.is_file() or contract.is_symlink() or not contract.resolve().is_relative_to(project):
        raise ValueError("registered_testing_contract_required: create .maw/testing.yaml")
    args = argparse.Namespace(root=str(project), component=component or [], suite=suite,
        execute=False, execution_mode="plan", log_dir=".local/verification", timeout=900,
        task_key=task_key, task_version=task_version)
    plan = testing.build_payload(args)
    commands = plan["project_tests"]["commands"]
    if plan["test_plan"]["blocked_by"]:
        return {**plan, "status": "blocked"}
    if not commands and not plan["project_tests"]["external_runners"]:
        return {**plan, "status": "not_run", "reason": "no_registered_commands_selected"}
    sources = {".maw/testing.yaml": hashlib.sha256(contract.read_bytes()).hexdigest()}
    for item in commands:
        cwd = (project / item["cwd"]).resolve()
        if not cwd.is_relative_to(project):
            raise ValueError("verification_working_directory_outside_project")
        for name in ("package.json", "Makefile", "pyproject.toml", "pytest.ini", "setup.cfg"):
            file = cwd / name
            if file.is_file():
                if file.is_symlink():
                    raise ValueError("verification_config_symlink_refused")
                sources[file.relative_to(project).as_posix()] = hashlib.sha256(file.read_bytes()).hexdigest()
    digest = hashlib.sha256(json.dumps({"plan": plan["test_plan"], "commands": commands, "sources": sources}, sort_keys=True).encode()).hexdigest()
    required = "VERIFY:" + digest[:16]
    if not execute:
        return {**plan, "status": "planned", "confirmation_required": required, "command_fingerprint": digest}
    if confirmation != required:
        return {**plan, "status": "blocked", "error": "verification_confirmation_mismatch", "confirmation_required": required}
    evidence_root = project / ".local/verification"
    if not evidence_root.resolve().is_relative_to(project):
        raise ValueError("verification_evidence_path_outside_project")
    args.execute = True
    args.execution_mode = "execute"
    result = testing.build_payload(args)
    return {**result, "command_fingerprint": digest}
