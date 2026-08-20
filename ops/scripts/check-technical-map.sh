#!/usr/bin/env sh
set -eu

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

public_payload_mode=false
if [ -f PUBLIC_PAYLOAD_MANIFEST.json ] && [ ! -f .maw-template/template.yaml ]; then
  public_payload_mode=true
fi

require_grep() {
  pattern=$1
  shift
  for path in "$@"; do
    grep -Eq "$pattern" "$path" || fail "$path must include required pattern: $pattern"
  done
}

[ -f docs/technical-map/README.md ] || fail "technical map README missing"
[ -f docs/capabilities/README.md ] || fail "capabilities README missing"
[ -f docs/capabilities/_template/capability.md ] || fail "capability template missing"
[ -f docs/project-signals/README.md ] || fail "project signals README missing"
[ -f docs/project-signals/_template.md ] || fail "project signal template missing"
[ -f .maw/capabilities.yaml ] || fail ".maw/capabilities.yaml missing"
[ -f .maw/project-signals.yaml ] || fail ".maw/project-signals.yaml missing"
[ -f ops/scripts/extract-project-metadata.py ] || fail "project metadata extractor missing"

require_grep '技术地图|公共能力|项目提示信号|AI 前置' docs/technical-map/README.md
require_grep 'capability_key|status|type|origin' docs/capabilities/_template/capability.md
require_grep 'signal_id|type|status|severity|AI 前置条件' docs/project-signals/_template.md
require_grep 'capability_map_update_status' .maw/capabilities.yaml docs/ai-coding/coding-style.md docs/ai-coding/module-dossier-rules.md docs/ai-instructions/instructions/final-closeout-response.md docs/ai-instructions/templates/final-closeout.zh-CN.md
require_grep 'project_signal_update_status' .maw/project-signals.yaml docs/ai-coding/coding-style.md docs/ai-coding/module-dossier-rules.md docs/ai-instructions/instructions/final-closeout-response.md docs/ai-instructions/templates/final-closeout.zh-CN.md
require_grep '#技术地图|TINST-030|#T030' PROJECT_COMMANDS.md docs/ai-instructions/README.md docs/ai-instructions/instructions/technical-map-project-metadata.md
require_grep 'extract-project-metadata.py|check-technical-map.sh' docs/technical-map/README.md

if [ "$public_payload_mode" = false ]; then
  require_grep 'extract-project-metadata.py|check-technical-map.sh' ops/scripts/README.md .maw-template/template.yaml
  require_grep 'capability.index|project.signals|capability.detail' .maw-template/config-key-index.yaml docs/configuration-guide.md ops/scripts/README.md
fi

python3 - <<'PY'
from pathlib import Path
import yaml

paths = [".maw/capabilities.yaml", ".maw/project-signals.yaml"]
if Path(".maw-template/template.yaml").is_file():
    paths.append(".maw-template/upgrades/20260617-technical-map-project-metadata.yaml")

for path in paths:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit(f"FAIL: {path} must parse as mapping")

capabilities = yaml.safe_load(Path(".maw/capabilities.yaml").read_text(encoding="utf-8")).get("capabilities") or []
if not capabilities and Path(".maw-template/template.yaml").is_file():
    raise SystemExit("FAIL: seed source .maw/capabilities.yaml must contain at least one capability")
for item in capabilities:
    for field in ["key", "name", "type", "status", "origin", "implementation_paths"]:
        if not item.get(field):
            raise SystemExit(f"FAIL: capability {item.get('key') or '<unknown>'} missing {field}")

signals = yaml.safe_load(Path(".maw/project-signals.yaml").read_text(encoding="utf-8")).get("signals") or []
if not signals and Path(".maw-template/template.yaml").is_file():
    raise SystemExit("FAIL: seed source .maw/project-signals.yaml must contain at least one signal")
for item in signals:
    for field in ["id", "type", "status", "severity", "title", "human_summary", "ai_preconditions"]:
        if not item.get(field):
            raise SystemExit(f"FAIL: project signal {item.get('id') or '<unknown>'} missing {field}")
PY

python3 -m py_compile ops/scripts/extract-project-metadata.py
python3 ops/scripts/extract-project-metadata.py --format json >/tmp/maw-project-metadata.json
python3 ops/scripts/extract-project-metadata.py --section ai-preconditions --format markdown >/tmp/maw-project-ai-preconditions.md

echo "OK: technical map and project metadata checks passed"
