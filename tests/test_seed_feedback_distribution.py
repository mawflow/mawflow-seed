"""The file-only feedback workflow must survive both public Git and Kit delivery."""
from pathlib import Path
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages/mawflow-seed-kit/src"))
from mawflow_seed_kit import materialize_project, inspect_agent_readiness

ASSETS = (
    "docs/ai-instructions/instructions/seed-feedback.md",
    "docs/ai-instructions/templates/seed-feedback-report.md",
)


def test_fresh_kit_contains_canonical_feedback_without_optional_runtime(tmp_path):
    project = tmp_path / "fresh"
    materialize_project(project, project_key="feedback", name="反馈验收")
    assert inspect_agent_readiness(project)["status"] == "ready"
    for ref in ASSETS:
        assert (project / ref).read_bytes() == (ROOT / ref).read_bytes()
    # Web navigation must reach the command from the public command index and
    # resolve every relative document link in the new workflow without a CLI.
    for ref in ("PROJECT_COMMANDS.md", ASSETS[0]):
        doc = project / ref
        links = re.findall(r"\]\(([^)]+)\)", doc.read_text())
        assert links
        for link in links:
            assert (doc.parent / link.split("#")[0]).is_file(), link


def test_public_payload_declares_report_dependency_closure():
    manifest = json.loads((ROOT / "PUBLIC_PAYLOAD_MANIFEST.json").read_text())
    required = set(manifest["required_paths"])
    for ref in ASSETS:
        assert ref in required
        assert (ROOT / ref).is_file()
    assert "tests/test_seed_feedback_distribution.py" in required
