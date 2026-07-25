from __future__ import annotations

from importlib.resources import files
from pathlib import Path
import re
from typing import Any

import yaml

from .catalog import CONTRACT_VERSION, SEED_VERSION, catalog, contract_fingerprint


PROJECT_KEY_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{0,159}$")


def _copy_tree(source: Any, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for item in source.iterdir():
        target = destination / item.name
        if item.is_dir():
            _copy_tree(item, target)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(item.read_bytes())


def _write_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")


def _deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    result = dict(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(dict(result[key]), value)
        else:
            result[key] = value
    return result


def materialize_project(
    root: Path | str,
    *,
    project_key: str,
    name: str,
    profile: str = "web-api",
    source: dict[str, Any] | None = None,
    classification: dict[str, Any] | None = None,
    technology: dict[str, Any] | None = None,
    credential_requirements: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    destination = Path(root).expanduser().resolve()
    if destination.exists() and any(destination.iterdir()):
        raise ValueError("seed_materialize_destination_not_empty")
    if not PROJECT_KEY_PATTERN.fullmatch(project_key):
        raise ValueError("seed_materialize_project_key_invalid")
    if profile not in {item["key"] for item in catalog()["profiles"]}:
        raise ValueError("seed_materialize_profile_invalid")
    destination.mkdir(parents=True, exist_ok=True)
    _copy_tree(files("mawflow_seed_kit").joinpath("template"), destination)

    replacements = {"__PROJECT_KEY__": project_key, "__PROJECT_NAME__": name.strip() or project_key}
    for path in destination.rglob("*"):
        if path.is_file():
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeError:
                continue
            for before, after in replacements.items():
                text = text.replace(before, after)
            path.write_text(text, encoding="utf-8")

    profile_payload = yaml.safe_load(
        files("mawflow_seed_kit").joinpath(f"resources/profiles/{profile}.yaml").read_text(encoding="utf-8")
    )
    _write_yaml(destination / ".maw/components.yaml", {"schema_version": 2, "components": profile_payload["components"]})
    _write_yaml(destination / ".maw/modules.yaml", {"schema_version": 2, "modules": profile_payload["modules"]})
    _write_yaml(destination / ".maw/app-runtime.yaml", {"schema_version": 2, "app_runtime": {"apps": profile_payload["apps"]}})
    _write_yaml(
        destination / ".maw/technology.yaml",
        {
            "schema_version": 1,
            "technology": _deep_merge(
                dict(profile_payload.get("technology") or {}),
                dict(technology or {}),
            ),
        },
    )
    if classification is not None or credential_requirements is not None:
        project_path = destination / ".maw/project.yaml"
        project_payload = yaml.safe_load(project_path.read_text(encoding="utf-8"))
        if classification is not None:
            project_payload["project"]["classification"] = _deep_merge(
                dict(project_payload["project"].get("classification") or {}),
                dict(classification),
            )
        if credential_requirements is not None:
            project_payload["credentials"] = {
                "schema_version": 1,
                "requirements": list(credential_requirements),
            }
        _write_yaml(project_path, project_payload)
    source_payload = dict(source or {})
    source_payload.setdefault("kind", "package")
    source_payload.setdefault("package", "mawflow-seed-kit")
    source_payload.setdefault("version", SEED_VERSION)
    _write_yaml(
        destination / ".maw/template-source.yaml",
        {
            "schema_version": 2,
            "template_source": {
                "kind": source_payload["kind"],
                "package": source_payload.get("package") or source_payload.get("template") or "mawflow-seed-kit",
                "applied_version": source_payload.get("version") or source_payload.get("template_version") or SEED_VERSION,
                "contract_version": CONTRACT_VERSION,
                "distribution": source_payload,
            },
        },
    )
    _write_yaml(
        destination / ".maw/seed.lock",
        {
            "schema": "mawflow.seed_lock.v2",
            "contract_version": CONTRACT_VERSION,
            "contract_fingerprint": contract_fingerprint(),
            "seed_version": SEED_VERSION,
            "profile": profile,
            "source": source_payload,
            "bom": {"kit": f"mawflow-seed-kit=={SEED_VERSION}", "contract": "seed-contract-v2"},
        },
    )
    return {
        "schema": "mawflow.seed_materialization.v2",
        "project_key": project_key,
        "profile": profile,
        "seed_version": SEED_VERSION,
        "contract_fingerprint": contract_fingerprint(),
        "root": str(destination),
    }


__all__ = ["materialize_project"]
