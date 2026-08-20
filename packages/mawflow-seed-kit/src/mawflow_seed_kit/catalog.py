from __future__ import annotations

from functools import lru_cache
import hashlib
from importlib.resources import files
import json
from typing import Any


SEED_VERSION = "2.3.2"
CONTRACT_VERSION = 2


@lru_cache(maxsize=1)
def catalog() -> dict[str, Any]:
    path = files("mawflow_seed_kit").joinpath("resources/contracts/v2/catalog.json")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != "mawflow.seed_contract_catalog.v2":
        raise RuntimeError("seed_contract_catalog_invalid")
    return payload


def contract_fingerprint() -> str:
    encoded = json.dumps(catalog(), sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode()
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def public_catalog() -> dict[str, Any]:
    payload = catalog()
    return {
        "schema": payload["schema"],
        "contract_version": payload["contract_version"],
        "seed_version": payload["seed_version"],
        "contract_fingerprint": contract_fingerprint(),
        "required_files": list(payload["required_files"]),
        "targets": payload["targets"],
        "operations": payload["operations"],
        "profiles": payload["profiles"],
        "trust_boundary": {
            "arbitrary_paths_writable": False,
            "project_schema_can_expand_host_permissions": False,
            "credential_values_accepted": False,
        },
    }
