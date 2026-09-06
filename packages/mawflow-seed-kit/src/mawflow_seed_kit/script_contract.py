from __future__ import annotations

from functools import lru_cache
from importlib.resources import files
import json
from typing import Any


@lru_cache(maxsize=1)
def script_contract() -> dict[str, Any]:
    path = files("mawflow_seed_kit").joinpath("resources/script-contract.v1.json")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != "mawflow.seed_script_contract.v1":
        raise RuntimeError("seed_script_contract_invalid")
    return payload


def public_script_contract() -> dict[str, Any]:
    return json.loads(json.dumps(script_contract(), ensure_ascii=False))


__all__ = ["public_script_contract", "script_contract"]
