#!/usr/bin/env python3
"""Canonical Seed Kit adapter for scoped lifecycle standards."""
import sys
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[2] / "packages/mawflow-seed-kit/src"
if SOURCE.is_dir():
    sys.path.insert(0, str(SOURCE))

from mawflow_seed_kit.standards import main

if __name__ == "__main__":
    raise SystemExit(main())
