"""CLI transport for the same trusted governance implementation used by Host."""
import json
from pathlib import Path
import sys

from mawflow_seed_kit.governance import project_governance


def configure(parser):
    parser.add_argument("governance_action", choices=("read", "context", "recall", "learning-report", "reading", "baseline", "library", "templates", "batches", "versions", "review", "release-prepare", "release-finalize", "preview", "apply"))
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


def execute(args):
    service = project_governance(Path(args.root), args.project_key)
    if args.governance_action == "read":
        return service.read()
    if args.governance_action == "context":
        return service.context(scope=args.scope, module=args.module)
    if args.governance_action == "recall":
        return service.recall(utterance=args.utterance, scope=args.scope, module=args.module, environment=args.environment, limit=args.limit)
    if args.governance_action == "learning-report":
        return service.learning_report()
    if args.governance_action == "review":
        return service.review(task_ref=args.task_ref, run_ref=args.run_ref)
    if args.governance_action == "batches":
        return service.update_batches()
    if args.governance_action == "versions":
        return service.release_versions()
    if args.governance_action == "library":
        return service.library()
    if args.governance_action == "templates":
        return service.templates()
    if args.governance_action == "reading":
        return service.reading(scope=args.scope, module=args.module)
    if args.governance_action == "baseline":
        return service.baseline(mode=args.mode, scope=args.scope, module=args.module, source_paths=args.source)
    if args.input != "-" and Path(args.input).stat().st_size > 262144:
        raise ValueError("governance_input_too_large")
    raw = sys.stdin.read(262145) if args.input == "-" else Path(args.input).read_text(encoding="utf-8")
    if len(raw.encode()) > 262144:
        raise ValueError("governance_input_too_large")
    payload = json.loads(raw)
    if args.governance_action in {"release-prepare", "release-finalize"}:
        import importlib
        execution = importlib.import_module(type(service).__module__.rsplit(".", 1)[0] + ".release_execution")
        return execution.prepare(service, payload, actor=args.actor, work_intent=args.work_intent) if args.governance_action == "release-prepare" else execution.finalize(service, payload.get("intent_key"), work_intent=args.work_intent)
    if args.governance_action == "preview":
        return service.preview(payload, actor=args.actor)
    return service.apply(payload, actor=args.actor, expected_fingerprint=args.fingerprint, work_intent=args.work_intent)
