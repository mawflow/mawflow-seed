#!/usr/bin/env python3
"""Use the canonical Seed Kit template-upgrade planner."""
from pathlib import Path
import sys

# A Seed checkout uses its tracked implementation; derived projects use their installed Kit.
_source = Path(__file__).resolve().parents[2] / "packages/mawflow-seed-kit/src"
if _source.is_dir():
    sys.path.insert(0, str(_source))
try:
    from mawflow_seed_kit.commands.template_drift import build_parser, compute_plan, inspect_seed_contract, main
except ImportError as exc:
    raise RuntimeError("Template upgrades require mawflow-seed-kit >=2.12.0; install a compatible Kit before planning.") from exc

if __name__ == "__main__":
    raise SystemExit(main())
