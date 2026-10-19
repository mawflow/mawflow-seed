#!/usr/bin/env python3
"""Canonical Seed Kit adapter for scoped lifecycle standards."""
import argparse
import json
import sys
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[2] / "packages/mawflow-seed-kit/src"
if SOURCE.is_dir():
    sys.path.insert(0, str(SOURCE))

from mawflow_seed_kit import standards


def main():
    # A copied adapter must not let an older Kit silently ignore new declarations.
    if getattr(standards, "STANDARDS_EXECUTION_PROTOCOL", 0) < 1:
        required = any(arg in {"plan-task", "report-task", "--fact"} or arg.startswith("--fact=")
                       for arg in sys.argv[1:])
        if "validate-task" in sys.argv[1:]:
            parser = argparse.ArgumentParser(add_help=False)
            parser.add_argument("--root", default=".")
            parser.add_argument("--input", default="")
            args, _ = parser.parse_known_args()
            try:
                task = standards.read_mapping(Path(args.root).resolve(strict=True), args.input)
                required = required or any(key in task for key in ("standards_binding", "evidence_policy"))
                lifecycle = task.get("lifecycle") or {}
                if isinstance(lifecycle, dict):
                    resources = lifecycle.get("resources")
                    resources = resources if isinstance(resources, list) else []
                    required = required or lifecycle.get("protocol_revision", 1) != 1 or "continuation" in lifecycle
                    required = required or any(isinstance(r, dict) and ("control" in r or "temporary_change" in r)
                                               for r in resources)
            except (ValueError, TypeError, OSError, standards.yaml.YAMLError):
                return standards.main()
        if required:
            print(json.dumps({"status": "blocked", "issues": ["standards_validator_upgrade_required"],
                              "summary": "当前Kit不支持已声明的规范执行扩展；请使用兼容工具复检。",
                              "changed_paths": [], "authorization_granted": False}, ensure_ascii=False))
            return 1
    if "validate-task" in sys.argv[1:] and not hasattr(standards, "validate_lifecycle"):
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument("--root", default=".")
        parser.add_argument("--input", default="")
        args, _ = parser.parse_known_args()
        try:
            task = standards.read_mapping(Path(args.root).resolve(strict=True), args.input)
        except (ValueError, TypeError, OSError, standards.yaml.YAMLError):
            return standards.main()
        if "lifecycle" in task:
            print(json.dumps({"status": "blocked", "issues": ["lifecycle_validator_upgrade_required"],
                              "summary": "当前Kit不支持生命周期扩展；升级兼容工具后复检，未执行资源回收。",
                              "lifecycle_status": "unsupported", "changed_paths": [],
                              "authorization_granted": False}, ensure_ascii=False))
            return 1
    return standards.main()

if __name__ == "__main__":
    raise SystemExit(main())
