#!/usr/bin/env sh
set -eu

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

[ -f .maw/module-candidates.yaml ] || fail ".maw/module-candidates.yaml missing"
[ -f .maw/modules.yaml ] || fail ".maw/modules.yaml missing"
[ -f docs/modules/_discovery/README.md ] || fail "docs/modules/_discovery/README.md missing"
[ -f docs/modules/_discovery/module-candidates.md ] || fail "docs/modules/_discovery/module-candidates.md missing"
[ -f docs/modules/_discovery/module-evidence.md ] || fail "docs/modules/_discovery/module-evidence.md missing"
[ -f docs/modules/_discovery/pending-module-questions.md ] || fail "docs/modules/_discovery/pending-module-questions.md missing"

python3 - <<'PY'
from pathlib import Path
import sys

try:
    import yaml
except Exception as exc:
    raise SystemExit(f"FAIL: PyYAML is required to parse module candidates: {exc}")

candidates_path = Path(".maw/module-candidates.yaml")
modules_path = Path(".maw/modules.yaml")
candidates_doc = yaml.safe_load(candidates_path.read_text(encoding="utf-8")) or {}
modules_doc = yaml.safe_load(modules_path.read_text(encoding="utf-8")) or {}

allowed_statuses = set(
    (candidates_doc.get("module_discovery") or {}).get("status_values")
    or ["seed", "candidate", "provisional", "confirmed", "deprecated"]
)
candidates = candidates_doc.get("module_candidates") or []
if not isinstance(candidates, list):
    raise SystemExit("FAIL: module_candidates must be a list")

required = {"key", "name", "status", "evidence", "open_questions"}
candidate_keys = set()
for index, candidate in enumerate(candidates):
    if not isinstance(candidate, dict):
        raise SystemExit(f"FAIL: module_candidates[{index}] must be a mapping")
    missing = sorted(required - set(candidate))
    if missing:
        raise SystemExit(
            f"FAIL: module_candidates[{index}] missing required fields: {', '.join(missing)}"
        )
    status = candidate.get("status")
    if status not in allowed_statuses:
        raise SystemExit(
            f"FAIL: module_candidates[{index}].status must be one of {sorted(allowed_statuses)}"
        )
    key = candidate.get("key")
    if key in candidate_keys:
        raise SystemExit(f"FAIL: duplicate module candidate key: {key}")
    candidate_keys.add(key)
    if not candidate.get("evidence"):
        raise SystemExit(f"FAIL: module candidate {key} must include evidence")
    if candidate.get("open_questions") is None:
        raise SystemExit(f"FAIL: module candidate {key} must include open_questions")

modules = modules_doc.get("modules") or []
for index, module in enumerate(modules):
    if not isinstance(module, dict):
        raise SystemExit(f"FAIL: modules[{index}] must be a mapping")
    status = module.get("status")
    if status == "seed":
        key = module.get("key") or index
        raise SystemExit(f"FAIL: seed module {key} belongs in .maw/module-candidates.yaml")

print("OK: module candidate checks passed")
PY
