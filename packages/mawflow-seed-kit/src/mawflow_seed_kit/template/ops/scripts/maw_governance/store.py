"""Bounded source reads and atomic append operations shared by CLI and Host."""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
import re
from pathlib import Path
import tempfile


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def recorder():
    # This is a sibling of this trusted installation, never a path supplied by a project.
    path = Path(__file__).resolve().parents[1] / "capture-document-source.py"
    spec = importlib.util.spec_from_file_location("_governance_source_recorder", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if getattr(module, "SCHEMA_V3", "") != "mawflow.document_source.v3":
        raise ValueError("governance_source_contract_unsupported")
    return module


def read_sources(root: Path) -> dict:
    capture = recorder()
    directory = capture.safe_path(root, "docs/intake", must_exist=False)
    rows, issues, files = [], [], []
    if directory.is_dir():
        paths = sorted(directory.glob("*.md"))
        if len(paths) > 5000:
            issues.append({"path": "docs/intake", "reason": "source_limit_exceeded"})
        for path in paths[:5000]:
            relative = path.relative_to(root).as_posix()
            try:
                capture.safe_path(root, relative)
                if path.stat().st_size > 262144:
                    raise ValueError("source_too_large")
                raw = path.read_bytes()
                sha = hashlib.sha256(raw).hexdigest()
                files.append({"path": relative, "sha256": sha})
                content = raw.decode("utf-8")
                if not content.startswith("---\n{"):
                    continue
                contract = json.loads(content.split("\n---", 1)[0][4:]).get("content_contract", {})
                def safe_values(value, depth=0):
                    if depth > 12:
                        raise ValueError("source_nesting_limit")
                    if isinstance(value, str) and capture.SENSITIVE.search(value):
                        raise ValueError("sensitive_content_forbidden")
                    if isinstance(value, dict):
                        for child in value.values():
                            safe_values(child, depth + 1)
                    if isinstance(value, list):
                        for child in value:
                            safe_values(child, depth + 1)
                safe_values(contract)
                if contract.get("schema") not in {capture.SCHEMA, capture.SCHEMA_V2, capture.SCHEMA_V3, capture.SCHEMA_V4}:
                    if contract.get("schema", "").startswith("mawflow.document_source."):
                        raise ValueError("source_version_unsupported")
                    continue
                capture.slug(contract.get("capture_id"), "capture_id")
                if path.stem != contract["capture_id"]:
                    raise ValueError("source_identity_mismatch")
                items = contract.get("items")
                if not isinstance(items, list) or not 1 <= len(items) <= 40:
                    raise ValueError("invalid_source_items")
                file_rows = []
                for item in items:
                    if not isinstance(item, dict):
                        raise ValueError("invalid_source_item")
                    capture.slug(item.get("key"), "item_key")
                    for name in ("business", "qa", "dialogue", "activity", "consumption", "artifact", "organization", "process", "baseline", "release_binding", "update_batch", "learning"):
                        if item.get(name) is not None and not isinstance(item[name], dict):
                            raise ValueError("invalid_source_structure")
                    if contract["schema"] == capture.SCHEMA_V4:
                        capture.source_extensions().normalize_extensions(capture, item, activity=item.get("activity"))
                    elif item.get("learning") is not None:
                        raise ValueError("v4_required")
                    for name in ("business", "dialogue"):
                        identity = item.get(name)
                        if identity:
                            capture.slug(identity.get("key" if name == "business" else "question_key"), "question_key")
                            capture.slug(identity.get("scope"), "scope")
                    if item.get("business"):
                        capture.text(item["business"].get("title"), 180, "business_title")
                    capture.text(item.get("statement"), 14000 if contract["schema"] == capture.SCHEMA_V4 else 1800, "statement")
                    if item.get("volume") not in capture.VOLUMES or item.get("decision_status") not in capture.DECISIONS:
                        raise ValueError("invalid_source_state")
                    for identity, fields in ((item.get("dialogue") or {}, ("type", "status")),
                                             (item.get("qa") or {}, ("category", "claim_type"))):
                        if identity and any(not isinstance(identity.get(key), str) for key in fields):
                            raise ValueError("invalid_source_structure")
                    for name in ("statement", "volume", "decision_status", "supersedes"):
                        if not isinstance(item.get(name, ""), str):
                            raise ValueError("invalid_source_structure")
                    for name in ("resolves", "related_refs", "modules"):
                        if not isinstance(item.get(name, []), list) or any(not isinstance(x, str) for x in item.get(name, [])):
                            raise ValueError("invalid_source_structure")
                    for name, fields in (("dialogue", ("resolves_issues", "blocked_actions", "continue_actions")),
                                         ("artifact", ("question_refs", "review_refs")),
                                         ("consumption", ("question_refs",))):
                        for field in fields:
                            values = (item.get(name) or {}).get(field, [])
                            if not isinstance(values, list) or any(not isinstance(value, str) for value in values):
                                raise ValueError("invalid_source_structure")
                    options = (item.get("dialogue") or {}).get("options", [])
                    if not isinstance(options, list) or any(not isinstance(value, dict) for value in options):
                        raise ValueError("invalid_source_structure")
                    artifact = item.get("artifact")
                    if artifact:
                        for field in ("document_key", "version_key", "document_kind", "path", "input_hash", "previous_ref", "change_kind"):
                            if not isinstance(artifact.get(field), str):
                                raise ValueError("invalid_artifact_structure")
                        if artifact["path"] and not any(e.get("path") == artifact["path"] and e.get("kind") == "document" for e in item.get("evidence", []) if isinstance(e, dict)):
                            raise ValueError("artifact_evidence_required")
                    fresh = "current"
                    evidence_states = {}
                    evidence = item.get("evidence", [])
                    if not isinstance(evidence, list) or len(evidence) > 20 or any(not isinstance(x, dict) for x in evidence):
                        raise ValueError("invalid_evidence")
                    for ref in evidence:
                        ref_fresh = "current"
                        try:
                            target = capture.safe_path(root, ref["path"])
                            if target.stat().st_size > 2_000_000 or hashlib.sha256(target.read_bytes()).hexdigest() != ref["sha256"]:
                                ref_fresh = "changed"
                        except (ValueError, OSError, KeyError):
                            ref_fresh = "missing"
                        evidence_states[ref.get("path", "")] = ref_fresh
                        if ref_fresh != "current":
                            fresh = ref_fresh
                    file_rows.append({**item, "id": f"{contract['capture_id']}#{item['key']}",
                        "title": contract.get("title", ""), "captured_at": contract.get("captured_at", ""),
                        "source": contract.get("source", {}), "context": contract.get("context", {}),
                        "source_path": relative, "source_hash": sha, "freshness": fresh,
                        "artifact_integrity": evidence_states.get((item.get("artifact") or {}).get("path"), "current"),
                        "lifecycle": "active", "superseded_by": [], "supersedes": item.get("supersedes", ""),
                        "resolves": item.get("resolves", []), "evidence": evidence})
                if any(row.get("artifact") and row["artifact_integrity"] != "current" for row in file_rows):
                    # The artifact and answers share a commit marker. A checkout
                    # with a missing/tampered prepared document cannot activate
                    # only the answer half of that transaction.
                    for row in file_rows:
                        row["freshness"] = "changed"
                        row["artifact_integrity"] = "changed"
                rows.extend(file_rows)
            except (ValueError, OSError, KeyError, TypeError, UnicodeError, AttributeError) as exc:
                reason = str(exc) if isinstance(exc, ValueError) and re.fullmatch(r"[a-z_]{3,100}", str(exc)) else "source_invalid_or_unavailable"
                issues.append({"path": relative, "reason": reason})
    return {"items": rows, "sources": files, "issues": issues, "source_version": digest(files), "partial": bool(issues)}


@contextmanager
def mutation_lock(root: Path):
    """Coordinate local writers; revision chains still detect branches after Git merges."""
    directory = root / ".local" / "state" / "project-governance"
    current = root
    for part in (".local", "state", "project-governance"):
        current = current / part
        if current.is_symlink():
            raise ValueError("governance_state_symlink_forbidden")
    directory.mkdir(parents=True, exist_ok=True)
    lock_path = directory / "write.lock"
    if lock_path.is_symlink():
        raise ValueError("governance_state_symlink_forbidden")
    with lock_path.open("a+b") as handle:
        if os.name == "nt":
            import msvcrt
            if lock_path.stat().st_size == 0:
                handle.write(b"0")
                handle.flush()
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield directory
        finally:
            if os.name == "nt":
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def atomic_file(root: Path, relative: str, content: bytes) -> None:
    target = recorder().safe_path(root, relative, must_exist=False)
    if target.exists():
        if target.read_bytes() != content:
            raise ValueError("governance_target_conflict")
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    recorder().safe_path(root, relative, must_exist=False)
    fd, name = tempfile.mkstemp(prefix=".governance-", dir=target.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(name, target)
        except FileExistsError:
            if target.read_bytes() != content:
                raise ValueError("governance_target_conflict")
    finally:
        Path(name).unlink(missing_ok=True)
