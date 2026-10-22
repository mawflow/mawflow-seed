#!/usr/bin/env python3
"""Portable, offline project dialogue; source text never grants execution authority."""
import argparse
import json
from pathlib import Path
import sys

from maw_governance import Governance


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("read", "context", "recall", "learning-report", "reading", "baseline", "library", "templates", "batches", "versions", "review", "release-prepare", "release-finalize", "preview", "apply"))
    parser.add_argument("--root", default=".")
    parser.add_argument("--project-key", required=True)
    parser.add_argument("--input", default="-")
    parser.add_argument("--actor", default="external-agent")
    parser.add_argument("--fingerprint", default="")
    parser.add_argument("--work-intent", choices=("read_only", "modify"), default="read_only")
    parser.add_argument("--scope", default="")
    parser.add_argument("--module", default="")
    parser.add_argument("--utterance", default="")
    parser.add_argument("--environment", default="")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--mode", choices=("initialize", "audit", "repair"), default="audit")
    parser.add_argument("--source", action="append", default=[])
    parser.add_argument("--task-ref", default="")
    parser.add_argument("--run-ref", default="")
    args = parser.parse_args()
    try:
        service = Governance(Path(args.root), args.project_key)
        if args.action == "read":
            result = service.read()
        elif args.action == "context":
            result = service.context(scope=args.scope, module=args.module)
        elif args.action == "recall":
            result = service.recall(utterance=args.utterance, scope=args.scope, module=args.module, environment=args.environment, limit=args.limit)
        elif args.action == "learning-report":
            result = service.learning_report()
        elif args.action == "review":
            result = service.review(task_ref=args.task_ref, run_ref=args.run_ref)
        elif args.action == "batches":
            result = service.update_batches()
        elif args.action == "versions":
            result = service.release_versions()
        elif args.action == "library":
            result = service.library()
        elif args.action == "templates":
            result = service.templates()
        elif args.action == "reading":
            result = service.reading(scope=args.scope, module=args.module)
        elif args.action == "baseline":
            result = service.baseline(mode=args.mode, scope=args.scope, module=args.module, source_paths=args.source)
        else:
            raw = sys.stdin.read(262145) if args.input == "-" else Path(args.input).read_text(encoding="utf-8")
            if len(raw.encode()) > 262144:
                raise ValueError("governance_input_too_large")
            payload = json.loads(raw)
            if args.action in {"release-prepare", "release-finalize"}:
                from maw_governance import release_execution
                result = release_execution.prepare(service, payload, actor=args.actor, work_intent=args.work_intent) if args.action == "release-prepare" else release_execution.finalize(service, payload.get("intent_key"), work_intent=args.work_intent)
            else:
                result = service.preview(payload, actor=args.actor) if args.action == "preview" else service.apply(
                    payload, actor=args.actor, expected_fingerprint=args.fingerprint, work_intent=args.work_intent)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (ValueError, OSError, TypeError, KeyError) as exc:
        reason = str(exc) if isinstance(exc, ValueError) and str(exc).replace("_", "").isalnum() else "governance_request_invalid"
        print(json.dumps({"status": "error", "reason": reason}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
