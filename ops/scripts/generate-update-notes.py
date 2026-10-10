#!/usr/bin/env python3
"""Record, import, render and check authoritative project update notes.

Preview is read-only. Writes require --execute and a fresh fingerprint.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from pathlib import Path

import yaml

from update_notes.render import cloud_documents, import_changelogs, render
from update_notes.store import (
    CLOUD,
    HISTORY,
    LATEST,
    MAX_RECORDS,
    digest,
    load_notes,
    read_mapping,
    safe_path,
    safe_text,
    timestamp,
    validate,
    write_bytes,
)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="生成项目更新动态，默认最近100条，--all生成全部。"
    )
    result.add_argument(
        "command",
        choices=["record", "import-changelogs", "render", "render-cloud", "check"],
    )
    result.add_argument("--root", default=".")
    result.add_argument(
        "--format", choices=["json", "text", "markdown"], default="json"
    )
    result.add_argument("--input", help="record 输入的 JSON/YAML；- 表示标准输入")
    result.add_argument(
        "--source", action="append", default=[], help="明确指定历史模块日志，可重复"
    )
    selection = result.add_mutually_exclusive_group()
    selection.add_argument("--all", action="store_true")
    selection.add_argument("--limit", type=int, default=100)
    result.add_argument("--output", help="render 的 docs/updates 内目标 Markdown")
    result.add_argument("--execute", action="store_true")
    result.add_argument("--expected-fingerprint", default="")
    return result


def run(args) -> dict:
    root = Path(args.root).resolve(strict=True)
    if not root.is_dir() or args.limit < 1 or args.limit > MAX_RECORDS:
        raise ValueError("invalid_root_or_limit")
    notes, warnings = load_notes(root)
    proposed, blobs = {}, {}
    if args.command == "record":
        if not args.input:
            raise ValueError("record_input_required")
        if args.input == "-":
            raw = sys.stdin.read(256 * 1024 + 1)
            if len(raw.encode()) > 256 * 1024:
                raise ValueError("input_budget_exceeded")
            candidates = [validate(root, yaml.safe_load(raw))]
        else:
            candidates = [validate(root, read_mapping(Path(args.input)))]
    elif args.command == "import-changelogs":
        if not args.source:
            raise ValueError("explicit_import_sources_required")
        candidates, import_warnings = import_changelogs(root, args.source)
        warnings += import_warnings
    else:
        candidates = []
    if candidates:
        existing = {item["record_key"]: item for item in notes}
        for item in candidates:
            key = item["record_key"]
            relative = ".maw/changes/" + key + ".yaml"
            target = safe_path(root, relative)
            if target.is_file():
                # Preserve the original historical import receipt when the source
                # acquires new rows; semantic changes still fail closed.
                old = validate(root, read_mapping(target))
                old_comparable, new_comparable = (
                    json.loads(json.dumps(old)),
                    json.loads(json.dumps(item)),
                )
                if args.command == "import-changelogs":
                    for value in (old_comparable, new_comparable):
                        value["payload"].pop("provenance", None)
                if old_comparable != new_comparable:
                    raise ValueError("immutable_record_conflict:" + key)
                continue
            if key in existing and existing[key] != item:
                raise ValueError("conflicting_record_identity:" + key)
            if key in existing:
                continue
            for ref in item["evidence_refs"]:
                if not safe_path(root, ref["path"]).is_file():
                    raise ValueError("new_record_evidence_missing")
            blobs[relative] = yaml.safe_dump(
                item, allow_unicode=True, sort_keys=False, width=10000
            ).encode()
            proposed[relative] = item
            existing[key] = item
        # Validate the complete proposed graph before writing any new fragment.
        graph = {item["record_key"]: item for item in notes}
        graph.update({item["record_key"]: item for item in proposed.values()})
        children = {}
        for item in graph.values():
            parent = item["payload"].get("supersedes")
            if parent:
                if parent not in graph or parent == item["record_key"]:
                    raise ValueError("invalid_supersedes_reference")
                if graph[parent]["payload"]["module_key"] != item["payload"][
                    "module_key"
                ] or timestamp(graph[parent]["payload"]["occurred_at"]) >= timestamp(
                    item["payload"]["occurred_at"]
                ):
                    raise ValueError("invalid_revision_order_or_module")
                if parent in children:
                    raise ValueError("conflicting_revision_requires_review")
                children[parent] = item["record_key"]
    if args.command in {"render", "render-cloud", "check"}:
        project_file = safe_path(root, ".maw/project.yaml")
        project = (
            read_mapping(project_file).get("project", {})
            if project_file.exists()
            else {}
        )
        name = safe_text(project.get("name") or project.get("key") or "项目", 160)
        output = args.output or (HISTORY if args.all else LATEST)
        if not output.startswith("docs/updates/") or not output.endswith(".md"):
            raise ValueError("output_outside_update_documents")
        safe_path(root, output)
        if args.command == "render":
            blobs[output] = render(
                root, notes, output, None if args.all else args.limit, name
            )
        elif args.command == "render-cloud":
            blobs.update(cloud_documents(root, notes, name))
        else:
            documents = {
                path: render(root, notes, path, limit, name)
                for path, limit in ((LATEST, 100), (HISTORY, None))
            }
            documents.update(cloud_documents(root, notes, name))
            for path, expected in documents.items():
                target = safe_path(root, path)
                if not target.is_file() or target.read_bytes() != expected:
                    raise ValueError("generated_document_drift:" + path)
    current = {
        path: hashlib.sha256(safe_path(root, path).read_bytes()).hexdigest()
        if safe_path(root, path).exists()
        else None
        for path in blobs
    }
    source_paths = sorted(safe_path(root, ".maw/changes").glob("*.yaml"))
    evidence_hashes = {
        ref["path"]: hashlib.sha256(
            safe_path(root, ref["path"]).read_bytes()
        ).hexdigest()
        for item in candidates
        for ref in item["evidence_refs"]
        if safe_path(root, ref["path"]).is_file()
    }
    fingerprint = digest(
        {
            "sources": {
                path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                for path in source_paths
            },
            "blobs": {
                path: hashlib.sha256(content).hexdigest()
                for path, content in blobs.items()
            },
            "current": current,
            "evidence": evidence_hashes,
        }
    )
    changed = [
        path
        for path, content in blobs.items()
        if not safe_path(root, path).exists()
        or safe_path(root, path).read_bytes() != content
    ]
    if args.execute and args.command != "check":
        if args.expected_fingerprint != fingerprint:
            raise ValueError("stale_or_missing_preview_fingerprint")
        for path in changed:
            write_bytes(
                root,
                path,
                blobs[path],
                append=args.command not in {"render", "render-cloud"},
            )
    return {
        "status": "success",
        "summary": f"更新动态{args.command}：{len(notes)}条有效动态，{len(changed)}个文件待更新",
        "next_action": "continue",
        "changed_paths": changed if args.execute else [],
        "proposed_paths_count": len(changed),
        "fingerprint": fingerprint,
        "total": len(notes),
        "selected": len(notes) if args.all else min(args.limit, len(notes)),
        "imported_or_recorded": len(proposed),
        "output_path": CLOUD
        if args.command == "render-cloud"
        else args.output or (HISTORY if args.all else LATEST)
        if args.command in {"render", "check", "render-cloud"}
        else "",
        "evidence_refs": [
            {"path": ".maw/changes", "kind": "authoritative_change_fragments"}
        ],
        "log_path": "",
        "state_path": ".maw/changes",
        "environment": {
            "os": platform.system().lower(),
            "python": platform.python_version(),
            "workspace": "project_root",
        },
        "warnings": sorted(set(warnings)),
        "ai_takeover_reason": "",
        "mode": "execute" if args.execute else "preview",
    }


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    try:
        result = run(args)
        code = 0
    except (ValueError, OSError, UnicodeError, yaml.YAMLError) as exc:
        reason = (
            str(exc)
            if isinstance(exc, ValueError) and not isinstance(exc, yaml.YAMLError)
            else "invalid_input_or_filesystem"
        )
        result = {
            "status": "failed",
            "summary": reason,
            "next_action": "stop",
            "changed_paths": [],
            "warnings": [],
            "ai_takeover_reason": reason,
        }
        code = 20
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(result["summary"])
        if result.get("output_path"):
            print(result["output_path"])
    return code


if __name__ == "__main__":
    raise SystemExit(main())
