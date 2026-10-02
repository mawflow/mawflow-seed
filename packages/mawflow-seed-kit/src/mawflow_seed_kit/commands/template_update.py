"""Conservative three-way updates of package-managed Seed files.

Project facts are retained. Modified upstream files with local edits block the
whole change set. Recovery only restores files still matching this transaction.
"""
from __future__ import annotations

import base64
from contextlib import contextmanager
import hashlib
from importlib.resources import files
import json
import os
from pathlib import Path
import re
import subprocess
from uuid import uuid4

import yaml

from mawflow_seed_kit.catalog import SEED_VERSION, contract_fingerprint
from .project_init import scan_template_safety
from .template_sources import TemplateSourceConfig, materialize_template_source

ENTRIES = {"AI_START_HERE.md", "AGENTS.md", "CLAUDE.md", "GEMINI.md", "CHATGPT.md", "CHATGPT_TO_AI.md", "MAWFLOW_CLI.md", "PROJECT_COMMANDS.md"}
MANAGED = {".maw/agent-entry.yaml", ".maw/agent-rules.yaml", ".maw/agent-context.md", ".maw/project-doctor.yaml", ".maw/testing.yaml"}


def _digest(value: bytes | None) -> str:
    return hashlib.sha256(value).hexdigest() if value is not None else "absent"


def _path(root: Path, relative: str) -> Path:
    path = root / relative
    if not relative or Path(relative).is_absolute() or ".." in Path(relative).parts or not path.resolve().is_relative_to(root):
        raise ValueError("template_upgrade_path_invalid")
    for parent in (path, *path.parents):
        if parent == root:
            break
        if parent.is_symlink():
            raise ValueError("template_upgrade_symlink_refused")
    return path


def _read(root: Path, relative: str) -> bytes | None:
    path = _path(root, relative)
    return path.read_bytes() if path.exists() else None


def _atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + "." + uuid4().hex + ".tmp")
    try:
        with temporary.open("xb") as stream:
            stream.write(data); stream.flush(); os.fsync(stream.fileno())
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


@contextmanager
def _lock(root: Path):
    # OS locks are released on process death; the inert file may safely remain.
    path = _path(root, ".local/seed-upgrade.lock")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as stream:
        if os.name == "nt":
            import msvcrt
            stream.seek(0, os.SEEK_END)
            if not stream.tell():
                stream.write(b"0"); stream.flush()
            stream.seek(0)
            try:
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as exc:
                raise ValueError("template_upgrade_busy") from exc
        else:
            import fcntl
            try:
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise ValueError("template_upgrade_busy") from exc
        try:
            yield
        finally:
            if os.name == "nt":
                stream.seek(0); msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def _yaml(data: bytes | None) -> dict:
    value = yaml.safe_load(data or b"")
    if not isinstance(value, dict):
        raise ValueError("template_upgrade_project_metadata_invalid")
    return value


def plan_update(root: Path, *, base_template: Path | None = None, target_template: Path | None = None) -> dict:
    root = root.expanduser().resolve(strict=True)
    lock = _yaml(_read(root, ".maw/seed.lock"))
    if lock.get("contract_version") != 2:
        raise ValueError("template_upgrade_contract_migration_required")
    previous = str(lock.get("seed_version") or "")
    source = _yaml(_read(root, ".maw/template-source.yaml"))
    origin = source.get("template_source") or {}
    if origin.get("kind", "package") != "package":
        raise ValueError("template_upgrade_package_source_required: use project drift for a Git source")
    if previous == SEED_VERSION and target_template is None:
        return {"status": "up_to_date", "target_version": SEED_VERSION, "writes": [], "conflicts": []}
    if not re.fullmatch(r"\d+\.\d+\.\d+(?:rc\d+)?", previous):
        raise ValueError("template_upgrade_baseline_version_required")
    def release_order(version: str):
        parts = version.split("rc")
        return (*map(int, parts[0].split(".")), int(parts[1]) if len(parts) > 1 else 1000000)
    if release_order(previous) > release_order(SEED_VERSION):
        raise ValueError("template_upgrade_downgrade_refused: use the saved recovery transaction")
    project = _yaml(_read(root, ".maw/project.yaml"))["project"]
    replacements = {"__PROJECT_KEY__": str(project.get("key") or project.get("project_key") or ""), "__PROJECT_NAME__": str(project.get("name") or "")}
    materialized = None
    try:
        if base_template is None:
            materialized = materialize_template_source(TemplateSourceConfig(source="package", template_version=previous))
            base_template = materialized.template_dir
        target = target_template or Path(str(files("mawflow_seed_kit").joinpath("template")))
        scan_template_safety(base_template); scan_template_safety(target)
        names = {p.relative_to(tree).as_posix() for tree in (base_template, target) for p in tree.rglob("*") if p.is_file()}
        names = {name for name in names if name in ENTRIES | MANAGED or name.startswith("docs/ai-instructions/")}
        writes, conflicts = [], []
        for name in sorted(names):
            def render(tree):
                value = _read(tree.resolve(), name)
                if value is not None:
                    for before, after in replacements.items():
                        value = value.replace(before.encode(), after.encode())
                return value
            before, after, current = render(base_template), render(target), _read(root, name)
            if before == after or current == after:
                continue
            # Test registration belongs to the project after its first creation.
            if name == ".maw/testing.yaml" and current is not None:
                continue
            if current != before:
                conflicts.append(name); continue
            writes.append({"path": name, "before": before, "after": after})
        updated_lock = {**lock, "seed_version": SEED_VERSION, "contract_fingerprint": contract_fingerprint(), "bom": {**lock.get("bom", {}), "kit": f"mawflow-seed-kit=={SEED_VERSION}"}, "source": {**lock.get("source", {}), "version": SEED_VERSION, "template_version": SEED_VERSION}}
        updated_source = {**source, "template_source": {**origin, "applied_version": SEED_VERSION}}
        for name, value in ((".maw/seed.lock", updated_lock), (".maw/template-source.yaml", updated_source)):
            before, after = _read(root, name), yaml.safe_dump(value, allow_unicode=True, sort_keys=False).encode()
            if before != after:
                writes.append({"path": name, "before": before, "after": after})
        serial = [{"path": w["path"], "before_sha256": _digest(w["before"]), "after_sha256": _digest(w["after"])} for w in writes]
        confirmation = "SEED:" + hashlib.sha256(json.dumps(serial, sort_keys=True).encode()).hexdigest()[:20]
        return {"status": "blocked" if conflicts else "planned", "from_version": previous, "target_version": SEED_VERSION,
            "writes": serial, "conflicts": conflicts, "confirmation_required": confirmation, "_writes": writes}
    finally:
        if materialized is not None:
            materialized.close()


def update_template(root: Path, *, execute=False, confirmation="", rollback="", **sources) -> dict:
    root = root.expanduser().resolve(strict=True)
    if rollback:
        return restore_update(root, rollback, execute=execute, confirmation=confirmation)
    plan = plan_update(root, **sources)
    private = plan.pop("_writes", [])
    if not execute or plan["status"] != "planned":
        return plan
    if confirmation != plan["confirmation_required"]:
        raise ValueError("template_upgrade_confirmation_conflict")
    git = subprocess.run(["git", "status", "--porcelain", "--untracked-files=normal"], cwd=root, capture_output=True, text=True)
    if git.returncode or git.stdout.strip():
        raise ValueError("template_upgrade_clean_git_required")
    with _lock(root):
        for item in private:
            if _read(root, item["path"]) != item["before"]:
                raise ValueError("template_upgrade_file_conflict")
        key = "seed-" + uuid4().hex
        journal = {"schema": "mawflow.seed_update.v1", "key": key, "state": "prepared", "writes": [
            {"path": w["path"], "before": base64.b64encode(w["before"]).decode() if w["before"] is not None else None,
             "before_sha256": _digest(w["before"]), "after_sha256": _digest(w["after"])} for w in private]}
        record = _path(root, f".local/seed-upgrades/{key}.json")
        _atomic(record, json.dumps(journal, ensure_ascii=False).encode()); record.chmod(0o600)
        try:
            for item in private:
                if _read(root, item["path"]) != item["before"]:
                    raise ValueError("template_upgrade_file_conflict")
                path = _path(root, item["path"])
                if item["after"] is None:
                    path.unlink()
                else:
                    _atomic(path, item["after"])
            journal["state"] = "applied"
            _atomic(record, json.dumps(journal, ensure_ascii=False).encode()); record.chmod(0o600)
        except BaseException as exc:
            raise ValueError(f"template_upgrade_interrupted: offline recovery --rollback {key}") from exc
        return {**plan, "status": "applied", "recovery_key": key, "recovery_command": f"mawflow project upgrade --rollback {key}"}


def restore_update(root: Path, key: str, *, execute=False, confirmation="") -> dict:
    if not re.fullmatch(r"seed-[a-f0-9]{32}", key):
        raise ValueError("template_upgrade_recovery_key_invalid")
    record = _path(root, f".local/seed-upgrades/{key}.json")
    journal = json.loads(record.read_text())
    if journal.get("schema") != "mawflow.seed_update.v1" or journal.get("key") != key:
        raise ValueError("template_upgrade_recovery_invalid")
    with _lock(root):
        states = [{"path": w["path"], "current": _digest(_read(root, w["path"]))} for w in journal["writes"]]
        required = "RESTORE:" + hashlib.sha256(json.dumps(states, sort_keys=True).encode()).hexdigest()[:20]
        conflicts = [w["path"] for w, state in zip(journal["writes"], states) if state["current"] not in {w["before_sha256"], w["after_sha256"]}]
        plan = {"status": "blocked" if conflicts else "planned", "conflicts": conflicts, "confirmation_required": required, "recovery_key": key}
        if not execute or conflicts:
            return plan
        if confirmation != required:
            raise ValueError("template_upgrade_confirmation_conflict")
        originals = []
        for item in journal["writes"]:
            before = base64.b64decode(item["before"], validate=True) if item["before"] is not None else None
            if _digest(before) != item["before_sha256"]:
                raise ValueError("template_upgrade_backup_corrupt")
            originals.append(before)
        for item, state, before in zip(journal["writes"], states, originals):
            path = _path(root, item["path"])
            if _digest(_read(root, item["path"])) != state["current"]:
                raise ValueError("template_upgrade_file_conflict")
            if before is None:
                path.unlink(missing_ok=True)
            else:
                _atomic(path, before)
        journal["state"] = "restored"
        _atomic(record, json.dumps(journal, ensure_ascii=False).encode()); record.chmod(0o600)
        return {**plan, "status": "restored"}
