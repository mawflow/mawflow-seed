"""Portable version bindings. Execution results remain owned by the release system."""
from __future__ import annotations

from datetime import datetime
import importlib.util
import json
import re
from pathlib import Path

from .store import digest


def update_store():
    path = Path(__file__).resolve().parents[1] / "update_notes/store.py"
    spec = importlib.util.spec_from_file_location("_trusted_update_store", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def freeze_members(service, members):
    if not isinstance(members, list) or len(members) > 1000 or any(not isinstance(k, str) for k in members) or len(set(members)) != len(members):
        raise ValueError("explicit_update_members_required")
    store = update_store()
    notes, warnings = store.load_notes(service.root)
    by_key = {note["record_key"]: note for note in notes}
    if not set(members).issubset(by_key):
        raise ValueError("update_member_missing")
    warnings = [warning for warning in warnings if warning.rsplit(":", 1)[-1] in set(members)]
    replaced = {n["payload"].get("supersedes") for n in notes}
    warnings += ["superseded_update_member:" + key for key in members if key in replaced]
    return [{"record_key": key, "sha256": store.digest(by_key[key]), "record": by_key[key]} for key in sorted(members)], warnings


def candidate(capture, value):
    capture.only_keys(value, {"source_commit", "dirty", "snapshot_hash", "artifacts"}, "release_candidate")
    if not re.fullmatch(r"[a-f0-9]{40,64}", str(value.get("source_commit", ""))) or type(value.get("dirty")) is not bool:
        raise ValueError("invalid_release_candidate")
    snapshot = value.get("snapshot_hash", "")
    if (value["dirty"] and not snapshot) or (snapshot and not re.fullmatch(r"[a-f0-9]{64}", snapshot)):
        raise ValueError("dirty_candidate_snapshot_required")
    artifacts = value.get("artifacts", [])
    if not isinstance(artifacts, list) or len(artifacts) > 100:
        raise ValueError("invalid_release_artifacts")
    result = []
    for artifact in artifacts:
        capture.only_keys(artifact, {"component", "sha256", "version"}, "release_artifact")
        if not re.fullmatch(r"[a-f0-9]{64}", str(artifact.get("sha256", ""))):
            raise ValueError("invalid_release_artifact_hash")
        result.append({"component": capture.slug(artifact.get("component"), "component"), "sha256": artifact["sha256"],
                       "version": capture.text(artifact["version"], 120, "component_version") if artifact.get("version") else ""})
    if len({a["component"] for a in result}) != len(result):
        raise ValueError("duplicate_release_component")
    return {"source_commit": value["source_commit"], "dirty": value["dirty"], "snapshot_hash": snapshot,
            "artifacts": sorted(result, key=lambda a: a["component"])}


def read_manifest(service, row, field):
    metadata = row[field]
    path = service.capture.safe_path(service.root, metadata["manifest_path"])
    if path.stat().st_size > 2_000_000:
        raise ValueError("governance_manifest_too_large")
    import hashlib
    expected = next((e["sha256"] for e in row["evidence"] if e["path"] == metadata["manifest_path"]), "")
    content = path.read_bytes()
    if hashlib.sha256(content).hexdigest() != expected:
        raise ValueError("governance_manifest_changed")
    value = json.loads(content)
    if value.get("input_hash") != metadata["input_hash"] or value.get("input_hash") != digest({k: v for k, v in value.items() if k != "input_hash"}):
        raise ValueError("governance_manifest_hash_mismatch")
    return value


def prepare_binding(service, payload, snapshot, item, event_id):
    capture = service.capture
    channel = capture.slug(payload.get("channel", "project"), "release_channel")
    frozen, warnings = freeze_members(service, payload.get("members"))
    source = candidate(capture, payload.get("candidate"))
    targets = payload.get("targets")
    if not isinstance(targets, list) or not 1 <= len(targets) <= 100:
        raise ValueError("explicit_release_targets_required")
    clean_targets = []
    for target in targets:
        capture.only_keys(target, {"environment", "target", "component"}, "release_target")
        clean_targets.append({key: capture.slug(target.get(key), "release_" + key) for key in ("environment", "target", "component")})
    clean_targets.sort(key=lambda t: (t["environment"], t["target"], t["component"]))
    if len({digest(t) for t in clean_targets}) != len(clean_targets):
        raise ValueError("duplicate_release_target")
    manifests = [read_manifest(service, row, "release_binding") for row in snapshot["items"]
                 if (row.get("release_binding") or {}).get("channel") == channel]
    version = payload.get("release_version", "")
    if not version:
        existing = {m["version"] for m in manifests if m["candidate"] == source and m["members"] == frozen}
        if len(existing) > 1:
            raise ValueError("release_version_selection_required")
        if existing:
            version = existing.pop()
        else:
            date = datetime.fromisoformat(payload["occurred_at"].replace("Z", "+00:00")).strftime("%Y.%m.%d")
            number = 1
            while any(m["version"] == f"{date}.{number}" for m in manifests):
                number += 1
            version = f"{date}.{number}"
    if not isinstance(version, str) or not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9._+-]{0,79}", version):
        raise ValueError("invalid_release_version")
    if any(m["version"] == version and (m["candidate"] != source or m["members"] != frozen) for m in manifests):
        raise ValueError("release_version_candidate_conflict")
    body = {"schema": "mawflow.release_version_binding.v1", "project_key": service.project_key, "request_id": payload["request_id"],
            "channel": channel, "version": version, "candidate": source, "targets": clean_targets, "members": frozen,
            "previous_success_refs": capture._strings(payload.get("previous_success_refs", []), "previous_success_refs", count=100, limit=240),
            "warnings": warnings + ([] if frozen else ["本次没有登记更新说明，不能推定没有业务变化。"]),
            "execution_state": "requires_release_owner_readback", "occurred_at": payload["occurred_at"]}
    body["input_hash"] = digest(body)
    relative = f".maw/release-versions/{event_id}.json"
    item.update(volume="release-ops", statement=f"发布请求已绑定版本{version}；尚待原发布系统执行与回读。",
                evidence=[{"path": relative, "kind": "release"}],
                release_binding={"channel": channel, "version": version, "candidate_hash": digest(source),
                                 "manifest_path": relative, "input_hash": body["input_hash"]})
    return [item], {relative: (json.dumps(body, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()}


def bindings(service, snapshot):
    rows = []
    for item in snapshot["items"]:
        if not item.get("release_binding"):
            continue
        try:
            manifest = read_manifest(service, item, "release_binding")
            from .update_batches import owner_results
            results, state = owner_results(service, manifest)
            rows.append({"ref": item["id"], **manifest, "owner_results": results, "owner_state": state,
                         "state_source": "original_release_owner" if service.release_reader else "not_read_back"})
        except (ValueError, OSError, KeyError, TypeError, json.JSONDecodeError):
            rows.append({"ref": item["id"], **item["release_binding"], "state_source": "unavailable", "owner_results": []})
    from .release_execution import intents
    pending = [v for v in intents(service) if not any(r.get("channel") == v["channel"] and r.get("version") == v["version"] and r.get("candidate") == v["candidate"] and r.get("targets") == v["targets"] for r in rows)]
    return {"schema": "mawflow.release_versions.v1", "bindings": rows, "execution_intents": pending, "source_version": snapshot["source_version"],
            "trust_boundary": {"release_execution_owned_elsewhere": True, "version_does_not_mean_published": True}}
