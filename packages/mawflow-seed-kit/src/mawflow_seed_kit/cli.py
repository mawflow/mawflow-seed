from __future__ import annotations

import argparse
import json
from pathlib import Path

from .catalog import public_catalog
from .compiler import compile_project_definition
from .template import materialize_project


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mawflow-seed-kit")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("catalog")
    doctor = subparsers.add_parser("doctor")
    doctor.add_argument("root", nargs="?", default=".")
    build = subparsers.add_parser("build")
    build.add_argument("root")
    build.add_argument("--project-key", required=True)
    build.add_argument("--name", required=True)
    build.add_argument("--profile", choices=["web-api", "service", "minimal"], default="web-api")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "catalog":
        payload = public_catalog()
    elif args.command == "doctor":
        payload = compile_project_definition(Path(args.root))
    else:
        payload = materialize_project(Path(args.root), project_key=args.project_key, name=args.name, profile=args.profile)
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0 if payload.get("status", "ready") in {"ready", "applied"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
