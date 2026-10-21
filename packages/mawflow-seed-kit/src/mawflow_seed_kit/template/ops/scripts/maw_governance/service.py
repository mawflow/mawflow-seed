"""Preview, conditional append and explicit AI consumption for any Seed project."""
from __future__ import annotations

from pathlib import Path

from .artifacts import FIELDS as ARTIFACT_FIELDS, prepare as prepare_artifact
from .model import context, project
from .store import atomic_file, digest, mutation_lock, recorder


OPERATIONS = {"propose", "confirm", "reject", "retire", "message", "consume", "artifact", "work"}
FIELDS = {"operation", "request_id", "occurred_at", "expected_source_version", "task_ref", "run_ref",
          "question_key", "scope", "question", "answer", "category", "claim_type", "rationale", "exceptions",
          "base_refs", "evidence_paths", "modules", "source_kind", "source_ref", "confirmation_scope",
          "message", "issue_type", "issue_status", "reply_to", "impact", "options", "recommendation",
          "blocked_actions", "continue_actions", "resolves_issues", "context_hash", "question_refs", "consumer_ref",
          "scope_revision", "module", "goal", "actions", "result", "validation", "phase"} | ARTIFACT_FIELDS


class Governance:
    def __init__(self, root: Path, project_key: str):
        self.root = Path(root).resolve()
        self.capture = recorder()
        self.project_key = self.capture.slug(project_key, "project_key")
        if not self.root.is_dir():
            raise ValueError("project_root_missing")

    def read(self) -> dict:
        return project(self.root, self.project_key)

    def context(self, *, scope: str = "", module: str = "") -> dict:
        return context(self.read(), scope, module)

    def _identity(self, payload: dict, actor: str) -> tuple[str, str]:
        self.capture.only_keys(payload, FIELDS, "governance_request")
        request_id = self.capture.slug(payload.get("request_id"), "request_id")
        actor = self.capture.text(actor, 120, "actor")
        return "governance-" + digest([self.project_key, request_id])[:40], digest({"project_key": self.project_key, "actor": actor, "request": payload})

    def _existing(self, snapshot: dict, event_id: str, request_hash: str) -> dict | None:
        existing = next((i for i in snapshot["items"] if i["id"].startswith(event_id + "#")), None)
        if existing is None:
            return None
        if "governance-request:" + request_hash not in existing.get("related_refs", []):
            raise ValueError("governance_request_conflict")
        return {"schema": "mawflow.governance_receipt.v1", "status": "unchanged", "path": existing["source_path"],
                "sha256": existing["source_hash"], "item_refs": [i["id"] for i in snapshot["items"] if i["source_path"] == existing["source_path"]],
                "source_version": snapshot["source_version"], "project_key": self.project_key}

    def preview(self, payload: dict, *, actor: str) -> dict:
        event_id, request_hash = self._identity(payload, actor)
        snapshot = self.read()
        existing = self._existing(snapshot, event_id, request_hash)
        if existing:
            return {**existing, "fingerprint": digest([request_hash, existing["sha256"]])}
        if snapshot["partial"]:
            raise ValueError("governance_projection_incomplete")
        if payload.get("expected_source_version") != snapshot["source_version"]:
            raise ValueError("governance_source_changed")
        event, prepared = self._event(payload, snapshot, actor, event_id, request_hash)
        receipt = self.capture.capture(self.root, event, action="preview-event", prepared_files=prepared or None)
        return {"schema": "mawflow.governance_preview.v1", "status": "previewed", "project_key": self.project_key,
                "operation": payload["operation"], "fingerprint": digest([request_hash, receipt["sha256"]]),
                "source_version": snapshot["source_version"], "changes": event["items"],
                "source_receipt": receipt, "event": event,
                "prepared_files": {path: content.decode("utf-8") for path, content in prepared.items()},
                "trust_boundary": {"project_mutated": False, "identity_assertion": "caller_declared", "uploaded": False}}

    def apply(self, payload: dict, *, actor: str, expected_fingerprint: str, work_intent: str = "read_only") -> dict:
        if work_intent != "modify":
            raise ValueError("modify_intent_required")
        with mutation_lock(self.root):
            preview = self.preview(payload, actor=actor)
            if preview["fingerprint"] != expected_fingerprint:
                raise ValueError("governance_preview_changed")
            if preview["status"] == "unchanged":
                return preview
            # The source append is the transaction's sole commit marker. Until it
            # exists, prepared files cannot affect effective answers or artifacts.
            for path, content in preview.get("prepared_files", {}).items():
                atomic_file(self.root, path, content.encode("utf-8"))
            live = self.capture.capture(self.root, preview["event"], action="preview-event")
            if live["sha256"] != preview["source_receipt"]["sha256"]:
                raise ValueError("governance_prepared_facts_changed")
            receipt = self.capture.capture(self.root, preview["event"], action="record-event", work_intent="modify")
            if receipt["sha256"] != preview["source_receipt"]["sha256"]:
                raise ValueError("governance_write_readback_failed")
            self.capture.capture(self.root, preview["event"], action="check-event")
            snapshot = self.read()
            return {"schema": "mawflow.governance_receipt.v1", **receipt, "project_key": self.project_key,
                    "item_refs": [i["id"] for i in snapshot["items"] if i["source_path"] == receipt["path"]],
                    "source_version": snapshot["source_version"],
                    "trust_boundary": {"project_mutated": True, "uploaded": False, "human_acceptance_claimed": False}}

    def _event(self, payload: dict, snapshot: dict, actor: str, event_id: str, request_hash: str) -> tuple[dict, dict[str, bytes]]:
        op = payload.get("operation")
        if op not in OPERATIONS:
            raise ValueError("governance_operation_unsupported")
        item = {"key": "entry", "kind": "observation", "volume": "task-audit", "owner": actor,
                "decision_status": "not_applicable", "implementation_status": "not_applicable", "audit_status": "not_applicable",
                "evidence": payload.get("evidence_paths", []), "modules": payload.get("modules", []),
                "related_refs": ["governance-request:" + request_hash], "next_action": "回读项目记录并按确认范围继续"}
        source_kind = payload.get("source_kind", "ai_analysis" if op in {"propose", "consume", "work"} else "user_statement")
        if op in {"confirm", "retire", "reject"} and source_kind != "user_statement":
            raise ValueError("governance_human_confirmation_required")
        prepared, items = {}, []
        if op in {"propose", "confirm", "reject", "retire"}:
            item = self._answer(payload, snapshot, item, source_kind)
        elif op == "message":
            item.update(statement=self.capture.text(payload.get("message"), 1800, "message"),
                        kind="question" if payload.get("issue_type") != "reply" else "observation",
                        dialogue=self._dialogue(payload, snapshot))
        elif op == "work":
            item.update(kind="implementation", statement=payload.get("result"),
                activity={"task_ref": payload.get("task_ref"), "session_ref": payload.get("run_ref"),
                          "phase": payload.get("phase"), "goal": payload.get("goal"), "actions": payload.get("actions"),
                          "result": payload.get("result"), "validation": payload.get("validation")})
        elif op == "consume":
            current = context(snapshot, payload.get("scope", ""), payload.get("module", ""))
            if not current["complete"] or payload.get("context_hash") != current["context_hash"] or payload.get("question_refs") != current["question_refs"]:
                raise ValueError("governance_consumption_context_changed")
            item.update(kind="implementation", statement=payload.get("result", "已读取任务所需口径，执行与验证结果另行记录"),
                activity={"task_ref": payload.get("task_ref"), "session_ref": payload.get("run_ref"), "phase": "progress",
                          "goal": payload.get("goal", "读取本次任务所需的项目口径"),
                          "actions": payload.get("actions", ["读取并核对问答版本和来源"]),
                          "result": payload.get("result", "已声明读取对应版本，尚不代表执行已完成"),
                          "validation": payload.get("validation", "读取声明；执行结果和测试仍待提供")},
                consumption={"context_hash": current["context_hash"], "run_ref": payload.get("run_ref"),
                             "question_refs": current["question_refs"], "consumer_ref": payload.get("consumer_ref"),
                             "scope_revision": payload.get("scope_revision", "1"),
                             "context_scope": current["scope"], "context_module": current["module"]})
        elif op == "artifact":
            items, prepared = prepare_artifact(self, payload, snapshot, item, event_id)
            item = items[0]
        title = item.get("business", {}).get("title") or item["statement"][:160]
        return {"schema": self.capture.EVENT_SCHEMA_V2, "event_id": event_id, "title": title,
                "occurred_at": payload.get("occurred_at"), "source": {"kind": source_kind,
                    "ref": payload.get("source_ref", "项目治理交互"), "excerpt": item["statement"][:1200]},
                "context": {"session_ref": payload.get("run_ref", "governance-dialogue"),
                            "task_ref": payload.get("task_ref", "governance:" + payload.get("question_key", "context")),
                            "trigger": "decision" if op in {"confirm", "retire", "reject"} else "progress"},
                "items": items or [item]}, prepared

    def _answer(self, payload: dict, snapshot: dict, item: dict, source_kind: str) -> dict:
        op = payload["operation"]
        key, scope = payload.get("question_key"), payload.get("scope", "project")
        bases = payload.get("base_refs", [])
        if not isinstance(bases, list) or len(bases) > 20 or any(not isinstance(x, str) for x in bases) or len(set(bases)) != len(bases):
            raise ValueError("governance_invalid_bases")
        by_id = {i["id"]: i for i in snapshot["items"]}
        for ref in bases:
            previous = by_id.get(ref)
            if previous is None:
                raise ValueError("governance_base_missing")
            identity = previous.get("business") or {}
            if identity and (identity.get("key"), identity.get("scope")) != (key, scope):
                raise ValueError("governance_base_identity_mismatch")
        question = next((q for q in snapshot["questions"] if q["question_key"] == key and q["scope"] == scope), None)
        if op in {"confirm", "retire"} and question:
            covered, queue = set(), list(bases)
            while queue:
                ref = queue.pop()
                if ref in covered:
                    continue
                covered.add(ref)
                old = by_id.get(ref, {})
                queue.extend(([old["supersedes"]] if old.get("supersedes") else []) + old.get("resolves", []))
            if any(i["id"] not in covered for i in question["current"]):
                raise ValueError("governance_all_current_branches_required")
        if op in {"reject", "retire"} and not bases:
            raise ValueError("governance_base_required")
        item.update(kind="decision", statement=payload.get("answer"),
            evidence=payload.get("evidence_paths", []), modules=payload.get("modules", []),
            volume="technical" if payload.get("category") == "technical" else "requirements",
            decision_status="confirmed" if op in {"confirm", "retire"} else "rejected" if op == "reject" else "pending",
            implementation_status="unknown", audit_status="not_assessed",
            business={"key": key, "scope": scope, "title": payload.get("question"),
                      "effect": "retire" if op == "retire" else "define", "change_reason": payload.get("rationale")},
            qa={"category": payload.get("category", "business"), "claim_type": payload.get("claim_type", "requirement"),
                "rationale": payload.get("rationale"), "exceptions": payload.get("exceptions", []),
                "origin_ref": bases[0] if bases else payload.get("source_ref", "项目治理交互")},
            supersedes=bases[0] if bases else "", resolves=bases[1:])
        if len(bases) > 1 and op not in {"confirm", "retire"}:
            raise ValueError("governance_resolution_requires_confirmation")
        if item["decision_status"] == "confirmed":
            item["confirmation"] = {"basis": "explicit_user", "ref": payload.get("source_ref", "项目治理精确差异确认"),
                                    "scope": self.capture.text(payload.get("confirmation_scope"), 400, "confirmation_scope")}
            if payload.get("resolves_issues"):
                item["dialogue"] = self._dialogue({**payload, "issue_type": "reply", "issue_status": "resolved"}, snapshot)
        return item

    def _dialogue(self, payload: dict, snapshot: dict) -> dict:
        refs = {i["id"]: i for i in snapshot["items"] if i.get("dialogue")}
        for ref in ([payload["reply_to"]] if payload.get("reply_to") else []) + payload.get("resolves_issues", []):
            old = refs.get(ref, {}).get("dialogue", {})
            if (old.get("question_key"), old.get("scope")) != (payload.get("question_key"), payload.get("scope", "project")):
                raise ValueError("governance_dialogue_reference_mismatch")
        return {"question_key": payload.get("question_key"), "scope": payload.get("scope", "project"),
                "type": payload.get("issue_type", "ambiguity"), "status": payload.get("issue_status", "open"),
                "reply_to": payload.get("reply_to", ""), "impact": payload.get("impact", ""),
                "options": payload.get("options", []), "recommendation": payload.get("recommendation", ""),
                "blocked_actions": payload.get("blocked_actions", []), "continue_actions": payload.get("continue_actions", []),
                "resolves_issues": payload.get("resolves_issues", [])}
