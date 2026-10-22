"""Immutable external summaries with explicit members and paragraph provenance."""
from __future__ import annotations

from collections import defaultdict
from html import escape
import json

from .releases import freeze_members, read_manifest, update_store
from .store import digest


STATE_LABELS = {"released": "已发布", "partial": "部分目标已发布", "failed": "发布失败", "cancelled": "已取消",
                "no_change": "目标无变化", "rolled_back": "已回滚", "unknown": "发布结果待回读", "not_started": "尚未发布"}


def owner_results(service, binding):
    if not service.release_reader:
        return [], "unknown"
    results = service.release_reader(binding)
    if not isinstance(results, list):
        raise ValueError("invalid_release_owner_results")
    targets = {(t["environment"], t["target"], t["component"]) for t in binding["targets"]}
    selected = {}
    for result in results:
        service.capture.only_keys(result, {"environment", "target", "component", "state", "receipt_ref", "candidate_hash"}, "release_owner_result")
        identity = tuple(result.get(key) for key in ("environment", "target", "component"))
        if identity not in targets or identity in selected or result.get("state") not in STATE_LABELS or not result.get("receipt_ref") or result.get("candidate_hash") != digest(binding["candidate"]):
            raise ValueError("invalid_release_owner_results")
        service.capture.text(result["receipt_ref"], 400, "release_owner_receipt")
        selected[identity] = result
    states = [selected.get(identity, {}).get("state", "unknown") for identity in sorted(targets)]
    if states and all(state == "released" for state in states):
        state = "released"
    elif "released" in states:
        state = "partial"
    elif states and len(set(states)) == 1:
        state = states[0]
    elif "failed" in states:
        state = "failed"
    else:
        state = "unknown"
    return [selected[key] for key in sorted(selected)], state


def prepare(service, payload, snapshot, item, event_id):
    capture = service.capture
    key = capture.slug(payload.get("batch_key"), "batch_key")
    members, warnings = freeze_members(service, payload.get("members"))
    rows = [row for row in snapshot["items"] if (row.get("update_batch") or {}).get("batch_key") == key]
    previous_ref = payload.get("previous_ref", "")
    replaced = {row["update_batch"]["previous_ref"] for row in rows}
    heads = [row for row in rows if row["id"] not in replaced]
    if heads and (len(heads) != 1 or heads[0]["id"] != previous_ref):
        raise ValueError("update_batch_current_revision_required")
    previous = next((row for row in rows if row["id"] == previous_ref), None)
    if previous_ref and previous is None:
        raise ValueError("update_batch_previous_missing")
    revision = previous["update_batch"]["revision"] + 1 if previous else 1
    binding_ref = payload.get("release_ref", "")
    version, results, state = "", [], "not_started"
    binding = None
    if binding_ref:
        row = next((row for row in snapshot["items"] if row["id"] == binding_ref and row.get("release_binding")), None)
        if row is None:
            raise ValueError("update_batch_release_binding_missing")
        binding = read_manifest(service, row, "release_binding")
        version = binding["version"]
        bound_keys = {m["record_key"] for m in binding["members"]}
        all_notes = {n["record_key"]: n for n in update_store().load_notes(service.root)[0]}
        for member in members:
            note, seen = member["record"], set()
            while note["record_key"] not in bound_keys:
                if note["record_key"] in seen or not note["payload"].get("supersedes"):
                    raise ValueError("update_batch_member_outside_release")
                seen.add(note["record_key"])
                note = all_notes[note["payload"]["supersedes"]]
        try:
            results, state = owner_results(service, binding)
        except (OSError, ValueError, KeyError, TypeError):
            warnings.append("原发布系统结果暂不可读，摘要保留待回读状态；不重新部署。")
            results, state = [], "unknown"
    if previous:
        old = read_manifest(service, previous, "update_batch")
        if old["release_ref"] != binding_ref:
            raise ValueError("update_batch_release_identity_changed")
    overrides = payload.get("external_overrides", {})
    if not isinstance(overrides, dict) or not set(overrides).issubset({m["record_key"] for m in members}):
        raise ValueError("invalid_external_overrides")
    groups = defaultdict(list)
    source_map = []
    store = update_store()
    for member in members:
        note, record_key = member["record"]["payload"], member["record_key"]
        external = overrides.get(record_key, note.get("external"))
        if external is not None:
            external = store.validate_external(external)
        else:
            external = {"title": note["title"], "summary": note["summary"], "impact": "", "testing": [], "important": [],
                        "limitations": ["历史记录未提供独立对外表述，请审阅业务影响。"], "authorship": "legacy"}
            warnings.append("对外措辞待审阅：" + record_key)
        groups[note["module_name"]].append({"record_key": record_key, "category": note["category"], **external})
        source_map.append({"paragraph": len(source_map) + 1, "record_key": record_key, "sha256": member["sha256"],
                           "external_hash": digest(external), "overridden": record_key in overrides})
    title = capture.text(payload.get("batch_title", "项目更新说明"), 180, "batch_title")
    lines = [f"# {escape(title)}", "", f"版本：{version}" if version else "阶段沟通摘要（未发布）", "",
             f"发布状态：{STATE_LABELS[state]}。" if binding else "此批用于阶段沟通，没有分配正式发布版本。", "",
             f"内容修订：{revision}；整理时间：{payload['occurred_at']}。", ""]
    if not members:
        lines += ["本批尚无明确登记的变更说明，不能据此判断没有业务变化。", ""]
    for module, notes in sorted(groups.items()):
        lines += [f"## {escape(module)}", ""]
        for note in notes:
            lines += [f"### {escape(note['title'])}", "", escape(note["summary"]), ""]
            if note["impact"]:
                lines += ["影响：" + escape(note["impact"]), ""]
            for field, label in (("testing", "建议关注"), ("important", "重要说明"), ("limitations", "限制与待确认")):
                if note[field]:
                    lines += [label + "：", "", *["- " + escape(text) for text in note[field]], ""]
    if state == "partial":
        lines += ["## 发布范围", "", "本批仅部分目标发布成功，其余结果须单独核对；不能视为全环境完成。", ""]
    lines += ["测试建议不代表已完成测试；自动验证、目标发布和真人验收分别以实际回执为准。", ""]
    body = "\n".join(lines)
    target_label = "-".join(sorted({t["environment"] for t in binding["targets"]})) if binding else "stage"
    filename = f"{service.project_key}-{version or key}-{target_label}-r{revision:03d}.md"
    relative = f"docs/deliverables/update-batches/{key}/{filename}"
    manifest_path = f".maw/update-batches/{event_id}.json"
    manifest = {"schema": "mawflow.update_batch.v1", "project_key": service.project_key, "batch_key": key, "revision": revision,
                "previous_ref": previous_ref, "release_ref": binding_ref, "version": version, "members": members,
                "source_map": source_map, "external_overrides": overrides, "title": title, "markdown_path": relative,
                "filename": filename, "occurred_at": payload["occurred_at"], "observed_release_state": state,
                "owner_results_snapshot": results, "warnings": warnings, "generation_method": payload.get("generation_method", "template")}
    if manifest["generation_method"] not in {"template", "ai", "human"}:
        raise ValueError("invalid_summary_generation_method")
    manifest["input_hash"] = digest(manifest)
    item.update(volume="release-ops", statement=f"{title}形成内容修订{revision}；{len(members)}项明确来源，发布状态单独回读。",
                evidence=[{"path": manifest_path, "kind": "release"}, {"path": relative, "kind": "document"}],
                update_batch={"batch_key": key, "revision": revision, "version": version, "release_ref": binding_ref,
                              "manifest_path": manifest_path, "markdown_path": relative, "input_hash": manifest["input_hash"],
                              "previous_ref": previous_ref})
    blobs = {manifest_path: (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(), relative: body.encode()}
    if any(len(content) > 2_000_000 for content in blobs.values()):
        raise ValueError("update_batch_too_large")
    return [item], blobs


def batches(service, snapshot):
    result = []
    for row in snapshot["items"]:
        if not row.get("update_batch"):
            continue
        try:
            manifest = read_manifest(service, row, "update_batch")
            path = service.capture.safe_path(service.root, manifest["markdown_path"])
            import hashlib
            content = path.read_bytes()
            expected = next(e["sha256"] for e in row["evidence"] if e["path"] == manifest["markdown_path"])
            if hashlib.sha256(content).hexdigest() != expected:
                raise ValueError("update_batch_markdown_changed")
            result.append({"ref": row["id"], **manifest, "content_markdown": content.decode(), "content_hash": expected, "integrity": "current"})
        except (ValueError, OSError, KeyError, TypeError, StopIteration):
            result.append({"ref": row["id"], **row["update_batch"], "integrity": "unavailable"})
    return {"schema": "mawflow.update_batches.v1", "batches": result, "source_version": snapshot["source_version"]}
