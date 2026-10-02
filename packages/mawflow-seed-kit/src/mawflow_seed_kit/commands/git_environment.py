"""Environment for observational Git commands; never take an optional index lock."""
from __future__ import annotations

import os

def git_read_only_environment() -> dict[str, str]:
    return {**os.environ, "GIT_OPTIONAL_LOCKS": "0"}
