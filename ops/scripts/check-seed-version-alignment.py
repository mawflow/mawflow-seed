#!/usr/bin/env python3
"""Check that Seed Git, Seed Kit, and Seed Contract share one version family."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import tomllib
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
SEMVER_PATTERN = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected_object:{path}")
    return payload


def _read_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"expected_mapping:{path}")
    return payload


def _python_constant(path: Path, name: str) -> str:
    text = path.read_text(encoding="utf-8")
    match = re.search(rf"^{re.escape(name)}\s*=\s*(?:[\"']([^\"']+)[\"']|(\d+))\s*$", text, re.MULTILINE)
    if match is None:
        raise ValueError(f"missing_python_constant:{path}:{name}")
    return str(match.group(1) or match.group(2) or "")


def _contract_fingerprint(catalog: dict[str, Any]) -> str:
    encoded = json.dumps(
        catalog,
        sort_keys=True,
        ensure_ascii=True,
        separators=(",", ":"),
    ).encode()
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def check_alignment(root: Path = ROOT) -> dict[str, Any]:
    blockers: list[dict[str, str]] = []
    observations: dict[str, object] = {}

    def block(code: str, *, actual: object = "", expected: object = "") -> None:
        blockers.append(
            {
                "code": code,
                "actual": str(actual),
                "expected": str(expected),
            }
        )

    try:
        version_text = (root / "TEMPLATE_VERSION").read_text(encoding="utf-8").strip()
        if not version_text.startswith("v"):
            block("template_version_must_use_v_prefix", actual=version_text, expected="vX.Y.Z")
        release_version = version_text.removeprefix("v")
        match = SEMVER_PATTERN.fullmatch(release_version)
        if match is None:
            block("canonical_release_version_invalid", actual=release_version, expected="X.Y.Z")
            return {
                "schema": "mawflow.seed_version_alignment.v1",
                "status": "blocked",
                "policy": {},
                "observations": {"release_version": release_version},
                "blockers": blockers,
            }
        contract_major = int(match.group(1))
        expected_catalog_relative = Path(
            f"packages/mawflow-seed-kit/src/mawflow_seed_kit/resources/contracts/v{contract_major}/catalog.json"
        )
        public_manifest = _read_json(root / "PUBLIC_PAYLOAD_MANIFEST.json")
        package_config = tomllib.loads(
            (root / "packages/mawflow-seed-kit/pyproject.toml").read_text(encoding="utf-8")
        )
        package_root = root / "packages/mawflow-seed-kit/src/mawflow_seed_kit"
        kit_manifest = _read_json(package_root / "manifest.json")
        root_lock = _read_yaml(root / ".maw/seed.lock")
        template_lock = _read_yaml(package_root / "template/.maw/seed.lock")
        template_source = _read_yaml(package_root / "template/.maw/template-source.yaml")
        template_source_config = template_source.get("template_source") or {}
        if not isinstance(template_source_config, dict):
            template_source_config = {}
        template_config_path = root / ".maw-template/template.yaml"
        template_config_exported = template_config_path.is_file()
        seed_contract: dict[str, Any] = {}
        if template_config_exported:
            template_config = _read_yaml(template_config_path)
            seed_contract = (
                template_config.get("template", {}).get("seed_contract", {})
                if isinstance(template_config.get("template"), dict)
                else {}
            )
            if not isinstance(seed_contract, dict):
                seed_contract = {}
            catalog_source = str(seed_contract.get("catalog_source") or "")
            catalog_relative = Path(catalog_source)
            if (
                not catalog_source
                or catalog_relative.is_absolute()
                or ".." in catalog_relative.parts
            ):
                raise ValueError(f"invalid_catalog_source:{catalog_source}")
        else:
            catalog_relative = expected_catalog_relative
            catalog_source = catalog_relative.as_posix()
        catalog = _read_json(root / catalog_relative)
        fingerprint = _contract_fingerprint(catalog)
        catalog_py = package_root / "catalog.py"
        init_py = package_root / "__init__.py"

        version_values: dict[str, object] = {
            "public_payload.seed_version": public_manifest.get("seed_version"),
            "public_payload.bom.kit": (public_manifest.get("bom") or {}).get("kit")
            if isinstance(public_manifest.get("bom"), dict)
            else "",
            "seed_kit.pyproject.version": (package_config.get("project") or {}).get("version")
            if isinstance(package_config.get("project"), dict)
            else "",
            "seed_kit.manifest.version": kit_manifest.get("version"),
            "catalog.seed_version": catalog.get("seed_version"),
            "root_lock.seed_version": root_lock.get("seed_version"),
            "root_lock.bom.kit": (root_lock.get("bom") or {}).get("kit")
            if isinstance(root_lock.get("bom"), dict)
            else "",
            "template_lock.seed_version": template_lock.get("seed_version"),
            "template_lock.source.version": (template_lock.get("source") or {}).get("version")
            if isinstance(template_lock.get("source"), dict)
            else "",
            "template_lock.bom.kit": (template_lock.get("bom") or {}).get("kit")
            if isinstance(template_lock.get("bom"), dict)
            else "",
            "template_source.applied_version": template_source_config.get(
                "applied_version"
            ),
            "catalog.py.SEED_VERSION": _python_constant(catalog_py, "SEED_VERSION"),
            "__init__.py.__version__": _python_constant(init_py, "__version__"),
        }
        if template_config_exported:
            version_values.update(
                {
                    "template.seed_contract.seed_version": seed_contract.get("seed_version"),
                    "template.seed_contract.kit_package": seed_contract.get("kit_package"),
                }
            )
        exact_version_expected = {
            "public_payload.bom.kit": f"mawflow-seed-kit=={release_version}",
            "root_lock.bom.kit": f"mawflow-seed-kit=={release_version}",
            "template_lock.bom.kit": f"mawflow-seed-kit=={release_version}",
            "template.seed_contract.kit_package": f"mawflow-seed-kit=={release_version}",
        }
        for label, actual in version_values.items():
            expected = exact_version_expected.get(label, release_version)
            if str(actual) != expected:
                block("seed_release_version_mismatch", actual=f"{label}={actual}", expected=expected)

        contract_values: dict[str, object] = {
            "public_payload.contract_version": public_manifest.get("contract_version"),
            "seed_kit.manifest.contract_version": kit_manifest.get("contract_version"),
            "catalog.contract_version": catalog.get("contract_version"),
            "root_lock.contract_version": root_lock.get("contract_version"),
            "template_lock.contract_version": template_lock.get("contract_version"),
            "template_source.contract_version": template_source_config.get(
                "contract_version"
            ),
            "catalog.py.CONTRACT_VERSION": _python_constant(catalog_py, "CONTRACT_VERSION"),
        }
        if template_config_exported:
            contract_values["template.seed_contract.contract_version"] = seed_contract.get(
                "contract_version"
            )
        for label, actual in contract_values.items():
            if str(actual) != str(contract_major):
                block(
                    "seed_contract_major_mismatch",
                    actual=f"{label}={actual}",
                    expected=contract_major,
                )

        contract_name = f"seed-contract-v{contract_major}"
        for label, parent in (
            ("public_payload.bom.contract", public_manifest),
            ("root_lock.bom.contract", root_lock),
            ("template_lock.bom.contract", template_lock),
        ):
            bom = parent.get("bom") or {}
            actual = bom.get("contract") if isinstance(bom, dict) else ""
            if str(actual) != contract_name:
                block("seed_contract_bom_mismatch", actual=f"{label}={actual}", expected=contract_name)

        for label, actual in {
            "public_payload.contract_fingerprint": public_manifest.get("contract_fingerprint"),
            "seed_kit.manifest.contract_fingerprint": kit_manifest.get("contract_fingerprint"),
            "root_lock.contract_fingerprint": root_lock.get("contract_fingerprint"),
            "template_lock.contract_fingerprint": template_lock.get("contract_fingerprint"),
        }.items():
            if str(actual) != fingerprint:
                block("seed_contract_fingerprint_mismatch", actual=f"{label}={actual}", expected=fingerprint)

        expected_catalog_source = expected_catalog_relative.as_posix()
        if catalog_source != expected_catalog_source:
            block(
                "seed_contract_catalog_source_mismatch",
                actual=catalog_source,
                expected=expected_catalog_source,
            )
        catalog_py_text = catalog_py.read_text(encoding="utf-8")
        expected_runtime_catalog = f"resources/contracts/v{contract_major}/catalog.json"
        if expected_runtime_catalog not in catalog_py_text:
            block(
                "seed_contract_runtime_catalog_mismatch",
                actual="catalog.py",
                expected=expected_runtime_catalog,
            )
        expected_catalog_schema = f"mawflow.seed_contract_catalog.v{contract_major}"
        if str(catalog.get("schema") or "") != expected_catalog_schema:
            block(
                "seed_contract_catalog_schema_mismatch",
                actual=catalog.get("schema"),
                expected=expected_catalog_schema,
            )

        observations = {
            "release_version": release_version,
            "public_seed_version": release_version,
            "seed_kit_version": str((package_config.get("project") or {}).get("version") or ""),
            "seed_contract_version": contract_major,
            "contract_fingerprint": fingerprint,
            "catalog_source": expected_catalog_source,
            "template_metadata_checked": template_config_exported,
        }
    except (OSError, ValueError, json.JSONDecodeError, tomllib.TOMLDecodeError, yaml.YAMLError) as exc:
        block("seed_version_alignment_source_unreadable", actual=f"{type(exc).__name__}:{exc}")

    return {
        "schema": "mawflow.seed_version_alignment.v1",
        "status": "ready" if not blockers else "blocked",
        "policy": {
            "canonical_version_source": "TEMPLATE_VERSION",
            "public_seed_exact_release_version": True,
            "seed_kit_exact_release_version": True,
            "seed_contract_version": "release_semver_major",
            "major_upgrade_requires_all_three": True,
        },
        "observations": observations,
        "blockers": blockers,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    result = check_alignment(args.root.resolve())
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"Seed version alignment: {result['status']}")
        for key, value in result["observations"].items():
            print(f"- {key}: {value}")
        for blocker in result["blockers"]:
            print(
                f"- blocker: {blocker['code']} "
                f"actual={blocker['actual']} expected={blocker['expected']}"
            )
    return 1 if args.strict and result["status"] != "ready" else 0


if __name__ == "__main__":
    sys.exit(main())
