from __future__ import annotations

import argparse
import json
from pathlib import Path

from .catalog import public_catalog
from .compiler import compile_project_definition
from .credential_doctor import scan_credentials
from .template import materialize_project


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mawflow-seed-kit")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("catalog")
    doctor = subparsers.add_parser("doctor")
    doctor.add_argument("target_or_root", nargs="?", default=".")
    doctor.add_argument("root", nargs="?", default=".")
    doctor.add_argument("--include-source", action="store_true")
    doctor.add_argument("--fail-on-plaintext", action="store_true")
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
        else:
            payload = compile_project_definition(Path(args.target_or_root))
    else:
        payload = materialize_project(Path(args.root), project_key=args.project_key, name=args.name, profile=args.profile)
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    allowed = {"ready", "applied"}
    if args.command == "doctor" and args.target_or_root == "credentials" and not args.fail_on_plaintext:
        allowed.add("unsafe")
    return 0 if payload.get("status", "ready") in allowed else 1


if __name__ == "__main__":
    raise SystemExit(main())
