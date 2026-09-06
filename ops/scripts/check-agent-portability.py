#!/usr/bin/env python3
"""Check actual agent bootstrap files and optional bundled-template parity."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
KIT_SRC = ROOT / "packages/mawflow-seed-kit/src"
if KIT_SRC.is_dir():
    sys.path.insert(0, str(KIT_SRC))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--format", choices=["json", "text"], default="json")
    parser.add_argument("--check-distribution", action="store_true")
    args = parser.parse_args()
    try:
        from mawflow_seed_kit import inspect_agent_readiness, materialize_project
        result = inspect_agent_readiness(args.root)
        if args.check_distribution:
            with tempfile.TemporaryDirectory(prefix="seed-agent-parity-") as tmp:
                target = Path(tmp) / "project"
                materialize_project(target, project_key="agent-check", name="Agent Check")
                package = inspect_agent_readiness(target)
                result["materialized_template"] = package
                if package["status"] != "ready":
                    result["status"] = "needs_attention"
    except (ImportError, OSError, ValueError) as exc:
        result = {"status": "needs_attention", "error": str(exc), "next_step": "安装当前 Seed Kit 后重试；基础文件入口仍可直接使用"}
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.format == "json" else f"Agent portability: {result['status']}")
    return 0 if result["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
