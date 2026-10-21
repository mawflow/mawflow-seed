"""CLI transport for the same trusted governance implementation used by Host."""
import json
from pathlib import Path
import sys

from mawflow_seed_kit.governance import project_governance


def configure(parser):
    parser.add_argument("governance_action", choices=("read", "context", "preview", "apply"))
    parser.add_argument("--root", default=".")
    parser.add_argument("--project-key", required=True)
    parser.add_argument("--input", default="-")
    parser.add_argument("--actor", default="external-agent")
    parser.add_argument("--fingerprint", default="")
    parser.add_argument("--work-intent", choices=("read_only", "modify"), default="read_only")
    parser.add_argument("--scope", default="")
    parser.add_argument("--module", default="")


def execute(args):
    service = project_governance(Path(args.root), args.project_key)
    if args.governance_action == "read":
        return service.read()
    if args.governance_action == "context":
        return service.context(scope=args.scope, module=args.module)
    if args.input != "-" and Path(args.input).stat().st_size > 262144:
        raise ValueError("governance_input_too_large")
    raw = sys.stdin.read(262145) if args.input == "-" else Path(args.input).read_text(encoding="utf-8")
    if len(raw.encode()) > 262144:
        raise ValueError("governance_input_too_large")
    payload = json.loads(raw)
    if args.governance_action == "preview":
        return service.preview(payload, actor=args.actor)
    return service.apply(payload, actor=args.actor, expected_fingerprint=args.fingerprint, work_intent=args.work_intent)
