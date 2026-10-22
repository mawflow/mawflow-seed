"""Bind versions before side effects without dirtying a frozen code checkout.

Intents belong to the existing release executor. They are preparation receipts,
never deployment results. Closeout appends portable bindings and derived batches.
"""
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import tempfile

from .store import digest, mutation_lock
from .releases import freeze_members


def directory(service):
    root = service.root.resolve()
    target = root / ".local/state/project-governance/release-intents"
    for part in [target, *target.parents]:
        if part == root:
            break
        if part.is_symlink():
            raise ValueError("release_intent_symlink_forbidden")
    return target


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise ValueError("release_intent_symlink_forbidden")
    fd, temporary = tempfile.mkstemp(prefix=".release-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, sort_keys=True, indent=2)
            handle.write("\n"); handle.flush(); os.fsync(handle.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def read(path):
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 2_000_000:
        raise ValueError("release_intent_unavailable")
    value = json.loads(path.read_text())
    if value.get("input_hash") != digest({k: v for k, v in value.items() if k != "input_hash"}):
        raise ValueError("release_intent_changed")
    return value


def intents(service):
    target = directory(service)
    if not target.is_dir():
        return []
    rows = []
    for path in sorted(target.glob("*.json")):
        if re.fullmatch(r"[a-f0-9]{64}\.json", path.name):
            value = read(path)
            if value["project_key"] != service.project_key:
                raise ValueError("release_intent_project_mismatch")
            rows.append(value)
            if len(rows) > 1000:
                raise ValueError("release_intent_inventory_too_large")
    return rows


def prepare(service, payload, *, actor, work_intent="read_only"):
    if work_intent != "modify" or payload.get("operation") != "release_bind":
        raise ValueError("release_intent_modify_required")
    with mutation_lock(service.root):
        prior = intents(service)
        request = dict(payload)
        preview = service.preview(request, actor=actor)
        if preview["status"] == "unchanged":
            raise ValueError("release_intent_new_request_required")
        manifest = json.loads(next(v for p, v in preview["prepared_files"].items() if p.endswith(".json")))
        matching = [v for v in prior if v["channel"] == manifest["channel"] and
                    v["candidate"] == manifest["candidate"] and v["members"] == manifest["members"]]
        if not payload.get("release_version") and matching:
            versions = {v["version"] for v in matching}
            if len(versions) != 1:
                raise ValueError("release_version_selection_required")
            request["release_version"] = versions.pop()
        elif not payload.get("release_version"):
            date = datetime.fromisoformat(payload["occurred_at"].replace("Z", "+00:00")).strftime("%Y.%m.%d")
            occupied = {v["version"] for v in prior if v["channel"] == manifest["channel"]}
            occupied |= {v.get("version") for v in service.release_versions()["bindings"] if v.get("channel") == manifest["channel"]}
            number = 1
            while f"{date}.{number}" in occupied:
                number += 1
            request["release_version"] = f"{date}.{number}"
        if request != payload:
            preview = service.preview(request, actor=actor)
            manifest = json.loads(next(v for p, v in preview["prepared_files"].items() if p.endswith(".json")))
        if any(v["channel"] == manifest["channel"] and v["version"] == manifest["version"] and
               (v["candidate"] != manifest["candidate"] or v["members"] != manifest["members"]) for v in prior):
            raise ValueError("release_version_candidate_conflict")
        key = digest([service.project_key, manifest["channel"], manifest["candidate"], manifest["members"], manifest["targets"]])
        old = next((v for v in prior if v["key"] == key), None)
        if old:
            if old["version"] != manifest["version"]:
                raise ValueError("release_intent_version_changed")
            return {**old, "status": "prepared", "reused": True}
        value = {"schema": "mawflow.release_execution_intent.v1", "key": key,
            **{k: manifest[k] for k in ("project_key", "channel", "version", "candidate", "targets", "members", "occurred_at")},
            "actor": actor, "candidate_hash": digest(manifest["candidate"]), "execution_state": "requires_release_owner_readback"}
        value["input_hash"] = digest(value)
        write(directory(service) / (key + ".json"), value)
        return {**value, "status": "prepared", "reused": False}


@contextmanager
def lock(path):
    if path.is_symlink():
        raise ValueError("release_intent_symlink_forbidden")
    with path.open("a+b") as handle:
        if os.name == "nt":
            import msvcrt
            if path.stat().st_size == 0:
                handle.write(b"0"); handle.flush()
            handle.seek(0); msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            if os.name == "nt":
                handle.seek(0); msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _apply(service, request, actor, journal):
    if journal.is_file():
        request = json.loads(journal.read_text())
    for _ in range(3):
        write(journal, request)
        try:
            preview = service.preview(request, actor=actor)
            return service.apply(request, actor=actor, expected_fingerprint=preview["fingerprint"], work_intent="modify")
        except ValueError as exc:
            if str(exc) != "governance_source_changed":
                raise
            request = {**request, "expected_source_version": service.read()["source_version"]}
    raise ValueError("release_closeout_source_changed")


def finalize(service, key, *, work_intent="read_only"):
    if work_intent != "modify" or not re.fullmatch(r"[a-f0-9]{64}", str(key)):
        raise ValueError("release_intent_modify_required")
    folder = directory(service)
    value = read(folder / (key + ".json"))
    if value["project_key"] != service.project_key:
        raise ValueError("release_intent_project_mismatch")
    with lock(folder / (key + ".lock")):
        frozen, _ = freeze_members(service, [m["record_key"] for m in value["members"]])
        if frozen != value["members"]:
            raise ValueError("release_frozen_update_changed")
        request = {"operation": "release_bind", "request_id": "release-" + key[:40],
            "occurred_at": value["occurred_at"], "expected_source_version": service.read()["source_version"],
            "channel": value["channel"], "release_version": value["version"], "candidate": value["candidate"],
            "targets": value["targets"], "members": [m["record_key"] for m in value["members"]]}
        binding = _apply(service, request, value["actor"], folder / (key + ".binding-request.json"))
        from .update_batches import owner_results
        manifest = next(row for row in service.release_versions()["bindings"] if row["ref"] == binding["item_refs"][0])
        results, state = owner_results(service, manifest)
        batch_key = "release-" + key[:32]
        batches = [row for row in service.update_batches()["batches"] if row.get("batch_key") == batch_key and row.get("integrity") == "current"]
        replaced = {row.get("previous_ref") for row in batches}
        heads = [row for row in batches if row["ref"] not in replaced]
        if len(heads) > 1:
            return {"status": "summary_pending", "intent_key": key, "version": value["version"], "binding": binding,
                    "business_execution_repeated": False}
        previous = heads[0] if heads else None
        if previous and previous["owner_results_snapshot"] == results and previous["observed_release_state"] == state:
            return {"status": "registered", "intent_key": key, "version": value["version"], "binding": binding,
                    "batch": {"status": "unchanged", "item_refs": [previous["ref"]]}, "business_execution_repeated": False}
        phase = digest([key, results, state, previous["ref"] if previous else ""])
        batch_request = {"operation": "update_batch", "request_id": "release-batch-" + phase[:40],
            "occurred_at": datetime.now(timezone.utc).isoformat(), "expected_source_version": service.read()["source_version"],
            "batch_key": batch_key, "batch_title": previous["title"] if previous else "项目更新说明", "release_ref": binding["item_refs"][0],
            "previous_ref": previous["ref"] if previous else "", "external_overrides": previous["external_overrides"] if previous else {},
            "members": [m["record_key"] for m in value["members"]]}
        try:
            batch = _apply(service, batch_request, value["actor"], folder / (key + ".batch-" + phase[:32] + ".json"))
            return {"status": "registered", "intent_key": key, "version": value["version"], "binding": binding, "batch": batch,
                    "business_execution_repeated": False}
        except (ValueError, OSError):
            return {"status": "summary_pending", "intent_key": key, "version": value["version"], "binding": binding,
                    "business_execution_repeated": False}


def record_owner_result(service, key, states, *, exit_code, work_intent="read_only"):
    """Called by the original executor after its real command/readback returns."""
    if work_intent != "modify" or not re.fullmatch(r"[a-f0-9]{64}", str(key)) or type(exit_code) is not int:
        raise ValueError("release_owner_result_invalid")
    value = read(directory(service) / (key + ".json"))
    if value["project_key"] != service.project_key or not isinstance(states, list):
        raise ValueError("release_owner_result_invalid")
    targets = {(t["environment"], t["target"], t["component"]) for t in value["targets"]}
    seen = set()
    for row in states:
        if set(row) != {"environment", "target", "component", "state"}:
            raise ValueError("release_owner_result_invalid")
        identity = tuple(row[k] for k in ("environment", "target", "component"))
        if identity not in targets or identity in seen or row["state"] not in {"released", "failed", "cancelled", "unknown", "rolled_back", "no_change"}:
            raise ValueError("release_owner_result_invalid")
        if row["state"] == "released" and exit_code:
            raise ValueError("release_owner_verification_failed")
        seen.add(identity)
    from uuid import uuid4
    attempt = uuid4().hex
    result = {"schema": "mawflow.release_executor_result.v1", "project_key": service.project_key, "intent_key": key,
        "version": value["version"], "candidate_hash": value["candidate_hash"], "states": states, "exit_code": exit_code,
        "observed_at": datetime.now(timezone.utc).isoformat(), "receipt_ref": "release-executor:" + key + ":" + attempt}
    result["input_hash"] = digest(result)
    target = directory(service) / (key + ".results")
    if target.is_symlink():
        raise ValueError("release_intent_symlink_forbidden")
    write(target / (attempt + ".json"), result)
    return result


def read_owner_results(service, binding):
    """Read only this candidate's executor receipts; missing remains unknown."""
    selected = {}
    for value in intents(service):
        if any(value[k] != binding[k] for k in ("project_key", "channel", "version", "candidate", "targets", "members")):
            continue
        folder = directory(service) / (value["key"] + ".results")
        if folder.is_symlink():
            raise ValueError("release_intent_symlink_forbidden")
        if not folder.is_dir():
            continue
        paths = sorted(folder.glob("*.json"))
        if len(paths) > 1000:
            raise ValueError("release_owner_result_inventory_too_large")
        for path in paths:
            result = read(path)
            if result.get("schema") != "mawflow.release_executor_result.v1" or any(result[k] != value[k] for k in ("project_key", "version", "candidate_hash")):
                raise ValueError("release_owner_result_invalid")
            if result.get("intent_key") != value["key"]:
                raise ValueError("release_owner_result_invalid")
            for row in result["states"]:
                identity = tuple(row[k] for k in ("environment", "target", "component"))
                if identity not in selected or selected[identity][0] < result["observed_at"]:
                    selected[identity] = (result["observed_at"], {**row, "candidate_hash": value["candidate_hash"], "receipt_ref": result["receipt_ref"]})
    return [row for _, row in selected.values()]
