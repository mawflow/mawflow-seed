from __future__ import annotations

import argparse
import json
from pathlib import Path

from .catalog import public_catalog
from .compiler import compile_project_definition
from .credential_doctor import scan_credentials
from .project_topology import inspect_deployment_targets
from .template import materialize_project
from .agent_context import export_agent_context, inspect_agent_readiness, render_agent_context


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mawflow-seed-kit")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("catalog")
    doctor = subparsers.add_parser("doctor")
    doctor.add_argument("target_or_root", nargs="?", default=".")
    doctor.add_argument("root", nargs="?", default=".")
    doctor.add_argument("--include-source", action="store_true")
    doctor.add_argument("--fail-on-plaintext", action="store_true")
    context = subparsers.add_parser("context", help="导出有界、可追溯的共享任务上下文")
    context.add_argument("root", nargs="?", default=".")
    context.add_argument("--module", default="")
    context.add_argument("--agent", default="", help="明确的 Agent 名称；未知或未提供时使用通用入口")
    context.add_argument("--task-kind", choices=["development", "review", "delivery", "governance"], default="development")
    context.add_argument("--max-chars", type=int, default=12000)
    context.add_argument("--format", choices=["json", "markdown"], default="json")
    build = subparsers.add_parser("build")
    build.add_argument("root")
    build.add_argument("--project-key", required=True)
    build.add_argument("--name", required=True)
    build.add_argument("--profile", choices=["blank", "minimal", "service", "web-api"], default="blank")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "catalog":
        payload = public_catalog()
    elif args.command == "doctor":
        if args.target_or_root == "credentials":
            payload = scan_credentials(Path(args.root), include_source=args.include_source)
        elif args.target_or_root == "deployments":
            payload = inspect_deployment_targets(Path(args.root))
        elif args.target_or_root == "agents":
            payload = inspect_agent_readiness(Path(args.root))
        else:
            payload = compile_project_definition(Path(args.target_or_root))
    elif args.command == "context":
        payload = export_agent_context(args.root, module_key=args.module, task_kind=args.task_kind, max_chars=args.max_chars, agent_name=args.agent)
        if args.format == "markdown":
            print(render_agent_context(payload))
            return 0
    else:
        payload = materialize_project(Path(args.root), project_key=args.project_key, name=args.name, profile=args.profile)
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    allowed = {"ready", "applied"}
    if args.command == "doctor" and args.target_or_root == "credentials" and not args.fail_on_plaintext:
        allowed.add("unsafe")
    if args.command == "doctor" and payload.get("agent_readiness", {}).get("status") == "needs_attention":
        return 1
    return 0 if payload.get("status", "ready") in allowed else 1


if __name__ == "__main__":
    raise SystemExit(main())
