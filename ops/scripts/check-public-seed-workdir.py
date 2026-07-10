#!/usr/bin/env python3
"""Validate the materialized public MAWflow Seed workdir without private-source dependencies."""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any


MARKDOWN_LINK_RE = re.compile(r"!?\[[^\]]+\]\(([^)]+)\)")
SECRET_PATTERNS = (
    ("private_key", re.compile(r"-----BEGIN (?:OPENSSH|RSA|DSA|EC|PRIVATE) KEY-----")),
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("openai_like_key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
)


def rel_exists(root: Path, rel_path: str) -> bool:
    target = root / rel_path
    if target.exists():
        return True
    if not target.suffix and target.with_suffix(".md").exists():
        return True
    return (target / "README.md").exists()


def check_markdown_links(root: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*.md")):
        rel_file = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        for line_no, line in enumerate(text.splitlines(), start=1):
            for match in MARKDOWN_LINK_RE.finditer(line):
                raw = match.group(1).strip()
                if not raw or raw.startswith(("#", "http://", "https://", "mailto:", "tel:", "data:")):
                    continue
                target = raw.split()[0].strip("<>").split("#", 1)[0]
                if not target or target.startswith("/") or re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target):
                    continue
                normalized = os.path.normpath((Path(rel_file).parent / target).as_posix()).replace("\\", "/")
                if normalized.startswith("../"):
                    findings.append({"kind": "relative_link_escapes_payload", "path": rel_file, "line": line_no, "target": target})
                    continue
                if not rel_exists(root, normalized):
                    findings.append({"kind": "broken_relative_link", "path": rel_file, "line": line_no, "target": target})
    return findings


def check_public_workdir(root: Path, manifest_path: Path, strict: bool) -> dict[str, Any]:
    blockers: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    for rel_path in manifest.get("required_paths") or []:
        if not (root / rel_path).is_file():
            blockers.append({"kind": "missing_required_path", "path": rel_path})

    for rel_path in manifest.get("forbidden_paths") or []:
        if (root / rel_path).exists():
            blockers.append({"kind": "forbidden_path_present", "path": rel_path})

    for path in sorted(root.rglob("*")):
        rel_path = path.relative_to(root).as_posix()
        if path.is_symlink():
            blockers.append({"kind": "symlink_not_allowed", "path": rel_path})
            continue
        if not path.is_file():
            continue
        if ".git" in path.relative_to(root).parts:
            blockers.append({"kind": "nested_git_metadata", "path": rel_path})
        if path.suffix == ".json":
            try:
                json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                blockers.append({"kind": "invalid_json", "path": rel_path})
        if path.stat().st_size > 1024 * 1024:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for kind, pattern in SECRET_PATTERNS:
            if pattern.search(text):
                blockers.append({"kind": kind, "path": rel_path})
                break

    readme = (root / "README.md").read_text(encoding="utf-8", errors="replace") if (root / "README.md").exists() else ""
    if "MAWflow Seed" not in readme:
        blockers.append({"kind": "public_readme_identity_missing", "path": "README.md"})

    link_findings = check_markdown_links(root)
    if strict:
        blockers.extend(link_findings)
    else:
        warnings.extend(link_findings)

    return {
        "schema": "mawflow.seed_public_workdir_check.v1",
        "status": "ready" if not blockers else "blocked",
        "blocker_count": len(blockers),
        "warning_count": len(warnings),
        "blockers": blockers[:100],
        "warnings": warnings[:100],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="materialized public Seed root")
    parser.add_argument("--manifest", default="PUBLIC_PAYLOAD_MANIFEST.json")
    parser.add_argument("--format", choices=["json", "text"], default="text")
    parser.add_argument("--strict", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    root = Path(args.root).resolve()
    manifest_path = Path(args.manifest)
    if not manifest_path.is_absolute():
        manifest_path = root / manifest_path
    try:
        summary = check_public_workdir(root, manifest_path, args.strict)
    except Exception as exc:  # noqa: BLE001 - CLI should report a concise structured failure.
        summary = {"schema": "mawflow.seed_public_workdir_check.v1", "status": "error", "error": str(exc)}
    if args.format == "json":
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(f"Public Seed workdir status: {summary.get('status')}")
        print(f"Blockers: {summary.get('blocker_count', 1 if summary.get('status') == 'error' else 0)}")
        print(f"Warnings: {summary.get('warning_count', 0)}")
        for finding in summary.get("blockers", [])[:10]:
            print(f"  - {json.dumps(finding, ensure_ascii=False)}")
        if summary.get("status") == "error":
            print(f"  - {summary.get('error')}")
    return 0 if summary.get("status") == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
