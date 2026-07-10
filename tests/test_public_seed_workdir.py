from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "ops/scripts/check-public-seed-workdir.py"
SPEC = importlib.util.spec_from_file_location("check_public_seed_workdir", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def materialize_minimal_payload(tmp_path: Path) -> Path:
    source_manifest = json.loads((ROOT / "PUBLIC_PAYLOAD_MANIFEST.json").read_text(encoding="utf-8"))
    manifest = {
        "schema": source_manifest["schema"],
        "required_paths": source_manifest["required_paths"],
        "forbidden_paths": source_manifest["forbidden_paths"],
        "smoke_commands": source_manifest["smoke_commands"],
    }
    (tmp_path / "PUBLIC_PAYLOAD_MANIFEST.json").write_text(json.dumps(manifest), encoding="utf-8")
    for rel_path in manifest["required_paths"]:
        path = tmp_path / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.name == "PUBLIC_PAYLOAD_MANIFEST.json":
            continue
        if path.name == "README.md" and path.parent == tmp_path:
            content = "# MAWflow Seed\n"
        elif path.suffix == ".json":
            content = "{}\n"
        else:
            content = "fixture\n"
        path.write_text(content, encoding="utf-8")
    return tmp_path / "PUBLIC_PAYLOAD_MANIFEST.json"


class PublicSeedWorkdirTest(unittest.TestCase):
    def test_accepts_complete_payload(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            manifest_path = materialize_minimal_payload(root)
            summary = MODULE.check_public_workdir(root, manifest_path, strict=True)
            self.assertEqual(summary["status"], "ready")

    def test_blocks_missing_and_forbidden_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            manifest_path = materialize_minimal_payload(root)
            (root / "AGENTS.md").unlink()
            forbidden = root / ".maw/template-source.yaml"
            forbidden.parent.mkdir(parents=True, exist_ok=True)
            forbidden.write_text("source_channel: internal\n", encoding="utf-8")
            summary = MODULE.check_public_workdir(root, manifest_path, strict=True)
            self.assertEqual(summary["status"], "blocked")
            kinds = {item["kind"] for item in summary["blockers"]}
            self.assertIn("missing_required_path", kinds)
            self.assertIn("forbidden_path_present", kinds)

    def test_blocks_relative_link_escape(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            manifest_path = materialize_minimal_payload(root)
            (root / "README.md").write_text(
                "# MAWflow Seed\n\n[private](../private.md)\n",
                encoding="utf-8",
            )
            summary = MODULE.check_public_workdir(root, manifest_path, strict=True)
            self.assertEqual(summary["status"], "blocked")
            self.assertIn("relative_link_escapes_payload", {item["kind"] for item in summary["blockers"]})


if __name__ == "__main__":
    unittest.main()
