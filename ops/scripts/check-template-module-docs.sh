#!/usr/bin/env sh
set -eu

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

warn() {
  echo "WARN: $*" >&2
}

require_grep() {
  pattern=$1
  shift
  for path in "$@"; do
    grep -Eq "$pattern" "$path" || fail "$path must include required pattern: $pattern"
  done
}

if [ -f PUBLIC_PAYLOAD_MANIFEST.json ] && [ ! -f .maw-template/template.yaml ]; then
  [ -f .maw/modules.yaml ] || fail ".maw/modules.yaml missing"
  [ -f .maw/module-candidates.yaml ] || fail ".maw/module-candidates.yaml missing"
  [ -f .maw/capabilities.yaml ] || fail ".maw/capabilities.yaml missing"
  [ -f .maw/project-signals.yaml ] || fail ".maw/project-signals.yaml missing"
  [ -f docs/modules/README.md ] || fail "docs/modules/README.md missing"
  [ -f docs/changelogs/README.md ] || fail "docs/changelogs/README.md missing"
  [ -f docs/technical-map/README.md ] || fail "docs/technical-map/README.md missing"
  [ -f ops/scripts/migrate-module-changelogs.py ] || fail "module changelog migration script missing"
  [ -f ops/scripts/check-module-candidates.sh ] || fail "module candidates check script missing"
  [ -f ops/scripts/check-technical-map.sh ] || fail "technical map check script missing"
  [ -f ops/scripts/extract-project-metadata.py ] || fail "project metadata extractor missing"

  python3 ops/scripts/migrate-module-changelogs.py check --format json >/dev/null
  sh ops/scripts/check-module-candidates.sh >/dev/null
  sh ops/scripts/check-technical-map.sh >/dev/null
  python3 ops/scripts/extract-project-metadata.py --format json >/dev/null
  echo "OK: public Seed module and technical-map checks passed"
  exit 0
fi

[ -f .maw/modules.yaml ] || fail ".maw/modules.yaml missing"
[ -f .maw/upgrade-policy.yaml ] || fail ".maw/upgrade-policy.yaml missing"
[ -f .maw/template-source.yaml ] || fail ".maw/template-source.yaml missing"
[ -f .maw-template/template.yaml ] || fail ".maw-template/template.yaml missing"
[ -f TEMPLATE_OVERVIEW.md ] || fail "template overview missing"
[ -f GETTING_STARTED.md ] || fail "human getting started guide missing"
[ -f PROJECT_COMMANDS.md ] || fail "human project commands catalog missing"
[ -f CHATGPT_TO_AI.md ] || fail "generic ChatGPT to AI handoff guide missing"
[ ! -e CHATGPT_TO_CODEX.md ] || fail "legacy CHATGPT_TO_CODEX.md must not remain in the current seed"
[ -f MAWFLOW_CLI.md ] || fail "MAWflow CLI guide missing"
[ -f docs/modules/README.md ] || fail "docs/modules/README.md missing"
[ -f docs/changelogs/README.md ] || fail "centralized changelog README missing"
[ -f .maw/module-candidates.yaml ] || fail ".maw/module-candidates.yaml missing"
[ -f docs/modules/_discovery/README.md ] || fail "module discovery README missing"
[ -f docs/modules/_discovery/module-candidates.md ] || fail "module candidates table missing"
[ -f docs/modules/_discovery/module-evidence.md ] || fail "module evidence table missing"
[ -f docs/modules/_discovery/pending-module-questions.md ] || fail "module pending questions missing"
[ -f docs/modules/_template/module.md ] || fail "module template missing"
[ -f docs/modules/_template/changelog.md ] || fail "centralized changelog template missing"
[ -f docs/modules/_template/group-README.md ] || fail "group README template missing"
[ -f docs/modules/_template/route-api-index.md ] || fail "route/api index template missing"
[ -f docs/modules/_template/page.md ] || fail "page audit template missing"
[ -f docs/modules/_template/backend-slice.md ] || fail "backend slice audit template missing"
[ -f docs/modules/_template/traceability.md ] || fail "traceability template missing"
[ -f docs/modules/_audits/README.md ] || fail "module map audits README missing"
[ -f docs/modules/_audits/_template.md ] || fail "module map audit template missing"
[ -f docs/archive/README.md ] || fail "archive README missing"
grep -Eq '永不自动读取|默认不.*读取|默认禁止.*读取' docs/archive/README.md || fail "archive README must state no-auto-read boundary"
[ -f docs/ai-coding/module-dossier-rules.md ] || fail "module dossier rules missing"
[ -f .local/README.md ] || fail ".local README missing"
[ -f .local/.maw/README.md ] || fail ".local .maw README missing"
[ -f .local/maintenance/README.md ] || fail ".local maintenance README missing"
[ -f .local/config/README.md ] || fail ".local config README missing"
[ -f ops/lib/maw_config_loader.py ] || fail "Python MAW config loader missing"
[ -f ops/scripts/maw-config-merge.py ] || fail "Python MAW config merge CLI missing"
[ -f ops/scripts/maw-config-get.py ] || fail "Python MAW config CLI missing"
[ -f ops/scripts/maw-key-get.py ] || fail "Python MAW logical key CLI missing"
[ -f ops/scripts/generate-uat-business-handoff.py ] || fail "UAT business handoff generator missing"
[ -f docs/ai-instructions/instructions/uat-business-handoff.md ] || fail "TINST-041 UAT business handoff instruction missing"
[ -f docs/delivery/uat/business-handoff-standard.md ] || fail "UAT business handoff standard missing"
[ -f docs/delivery/uat/templates/uat-delivery-spec.example.yaml ] || fail "UAT delivery spec example missing"
[ -f docs/template-migrations/20260811-uat-business-handoff.md ] || fail "UAT business handoff migration note missing"
[ -f .maw-template/upgrades/20260811-uat-business-handoff.yaml ] || fail "UAT business handoff upgrade asset missing"
[ -f prompts/codex/template-upgrade-prompts/20260811-uat-business-handoff-prompt.md ] || fail "UAT business handoff upgrade prompt missing"
[ -f ops/scripts/migrate-module-changelogs.py ] || fail "module changelog migration script missing"
[ -f .maw-template/config-key-index.yaml ] || fail "MAW logical key index missing"
legacy_config_merge=$(find ops/scripts -maxdepth 1 -name 'maw-config-merge.r?' -print -quit)
[ -z "$legacy_config_merge" ] || fail "legacy MAW config merge CLI must be removed; use ops/scripts/maw-config-merge.py"
[ -f ops/scripts/check-module-candidates.sh ] || fail "module candidates check script missing"
[ -f ops/scripts/check-local-boundary.sh ] || fail "local boundary check script missing"
[ -f ops/scripts/check-ai-memory-consistency.sh ] || fail "AI memory consistency check script missing"
[ -f ops/scripts/check-todo-governance.sh ] || fail "todo governance check script missing"
[ -f ops/scripts/check-technical-map.sh ] || fail "technical map check script missing"
[ -f ops/scripts/check-repository-identity.sh ] || fail "repository identity check script missing"
[ -f ops/scripts/extract-project-metadata.py ] || fail "project metadata extractor missing"
[ -f .maw/doc-taxonomy.yaml ] || fail "doc taxonomy missing"
[ -f docs/doc-read-contract/README.md ] || fail "doc read contract guide missing"
[ -f docs/capabilities/doc-read-contract.md ] || fail "doc read contract capability missing"
[ -f docs/ai-instructions/instructions/doc-read-contract.md ] || fail "doc read contract instruction missing"
[ -f ops/scripts/extract-doc-index.py ] || fail "doc index extractor missing"
[ -f ops/scripts/check-doc-read-contract.py ] || fail "doc read contract checker missing"
[ -f docs/ai-session-briefs/README.md ] || fail "recent session briefs README missing"
[ -f docs/ai-session-briefs/_template.md ] || fail "recent session brief template missing"
[ -f docs/capabilities/recent-session-briefs.md ] || fail "recent session briefs capability missing"
[ -f docs/ai-instructions/instructions/recent-session-briefs.md ] || fail "recent session briefs instruction missing"
[ -f ops/scripts/recent-session-briefs.py ] || fail "recent session briefs query script missing"
[ -f ops/scripts/write-session-brief.py ] || fail "recent session briefs writer script missing"
[ -f .maw-template/upgrades/20260621-recent-session-briefs.yaml ] || fail "recent session briefs upgrade asset missing"
[ -f docs/template-migrations/20260621-recent-session-briefs.md ] || fail "recent session briefs migration note missing"
[ -f prompts/codex/template-upgrade-prompts/20260621-recent-session-briefs-prompt.md ] || fail "recent session briefs upgrade prompt missing"
[ -f .maw/health/README.md ] || fail "project health context README missing"
[ -f .maw/health/issues.yaml ] || fail "project health issues file missing"
[ -f .maw/health/facts.yaml ] || fail "project health facts file missing"
[ -f .maw/health/decisions.yaml ] || fail "project health decisions file missing"
[ -f .maw/health/todos.yaml ] || fail "project health todos file missing"
[ -f .maw/health/audit-gaps.yaml ] || fail "project health audit gaps file missing"
[ -f .maw/health/research-sessions.yaml ] || fail "project health research sessions file missing"
[ -f .maw/health/acceptance-gaps.yaml ] || fail "project health acceptance gaps file missing"
[ -f .maw/health/examples/issues.example.yaml ] || fail "project health issues example missing"
[ -f .maw/health/examples/facts.example.yaml ] || fail "project health facts example missing"
[ -f .maw/health/examples/decisions.example.yaml ] || fail "project health decisions example missing"
[ -f .maw/health/examples/todos.example.yaml ] || fail "project health todos example missing"
[ -f .maw/health/examples/audit-gaps.example.yaml ] || fail "project health audit gaps example missing"
[ -f .maw/health/examples/research-sessions.example.yaml ] || fail "project health research sessions example missing"
[ -f .maw/health/examples/acceptance-gaps.example.yaml ] || fail "project health acceptance gaps example missing"
[ -f docs/capabilities/project-health-context.md ] || fail "project health context capability missing"
[ -f docs/ai-instructions/instructions/project-health-context.md ] || fail "project health context instruction missing"
[ -f ops/scripts/check-project-health-context.py ] || fail "project health context check script missing"
[ -f .maw-template/upgrades/20260627-project-health-context.yaml ] || fail "project health context upgrade asset missing"
[ -f docs/template-migrations/20260627-project-health-context.md ] || fail "project health context migration note missing"
[ -f prompts/codex/template-upgrade-prompts/20260627-project-health-context-prompt.md ] || fail "project health context upgrade prompt missing"
[ -f .maw/model-requirements.yaml ] || fail "AI model requirements protocol missing"
[ -f .maw/model-evaluation/cases.example.json ] || fail "AI model evaluation cases example missing"
[ -f .maw/model-evaluation/output-contract.example.json ] || fail "AI model evaluation output contract missing"
[ -f docs/implementation/ai-model-adapter-evaluation/README.md ] || fail "AI model adapter evaluation implementation guide missing"
[ -f docs/capabilities/ai-model-adapter-evaluation.md ] || fail "AI model adapter evaluation capability missing"
[ -f ops/scripts/check-model-evaluation-protocol.py ] || fail "AI model evaluation protocol checker missing"
[ -f .maw-template/upgrades/20260708-ai-model-adapter-evaluation-protocol.yaml ] || fail "AI model adapter evaluation upgrade asset missing"
[ -f docs/template-migrations/20260708-ai-model-adapter-evaluation-protocol.md ] || fail "AI model adapter evaluation migration note missing"
[ -f prompts/codex/template-upgrade-prompts/20260708-ai-model-adapter-evaluation-protocol-prompt.md ] || fail "AI model adapter evaluation upgrade prompt missing"
[ -f .maw-template/upgrades/20260622-module-map-route-api-index.yaml ] || fail "module map route/API index upgrade asset missing"
[ -f docs/template-migrations/20260622-module-map-route-api-index.md ] || fail "module map route/API index migration note missing"
[ -f prompts/codex/template-upgrade-prompts/20260622-module-map-route-api-index-prompt.md ] || fail "module map route/API index upgrade prompt missing"
[ -f .maw-template/upgrades/20260622-module-map-evidence-audit.yaml ] || fail "module map evidence/audit upgrade asset missing"
[ -f docs/template-migrations/20260622-module-map-evidence-audit.md ] || fail "module map evidence/audit migration note missing"
[ -f prompts/codex/template-upgrade-prompts/20260622-module-map-evidence-audit-prompt.md ] || fail "module map evidence/audit upgrade prompt missing"
[ -f docs/capabilities/ai-python-script-contract.md ] || fail "AI Python script contract missing"
[ -f docs/ai-instructions/instructions/script-contract-upgrade.md ] || fail "script contract upgrade instruction missing"
[ -f ops/templates/ai-python-script.py ] || fail "AI Python script template missing"
[ -f ops/scripts/check-ai-python-script-contract.py ] || fail "AI Python script contract checker missing"
[ -f ops/scripts/run-project-tests.py ] || fail "common project test runner missing"
[ -f docs/capabilities/seed-repository-feedback-loop.md ] || fail "seed repository feedback loop capability missing"
[ -f prompts/codex/seed-repository-upgrade-prompts/README.md ] || fail "seed repository upgrade prompts README missing"
[ -f .maw-template/upgrades/20260619-seed-repository-feedback-loop.yaml ] || fail "seed repository feedback loop upgrade asset missing"
[ -f docs/template-migrations/20260619-seed-repository-feedback-loop.md ] || fail "seed repository feedback loop migration note missing"
[ -f prompts/codex/template-upgrade-prompts/20260619-seed-repository-feedback-loop-prompt.md ] || fail "seed repository feedback loop upgrade prompt missing"
[ -f ops/scripts/check-host-purpose-mcp-alignment.sh ] || fail "host purpose MCP alignment check script missing"
[ -f ops/scripts/check-seed-distribution-readiness.sh ] || fail "seed distribution readiness check script missing"
[ -f ops/scripts/check-ai-framework-consistency.sh ] || fail "AI framework consistency check script missing"
[ -f ops/scripts/check-code-deliverable.sh ] || fail "code deliverable check script missing"
[ -f ops/scripts/check-repository-mirror-config.sh ] || fail "repository mirror config check script missing"
[ -f ops/scripts/export-code-only.sh ] || fail "code-only export script missing"
[ -f ops/scripts/download-task-pack-url.py ] || fail "task-pack URL downloader missing"
[ -f docs/ai-instructions/keyword-candidates.md ] || fail "keyword candidates missing"
[ -f docs/ai-instructions/experience-index.md ] || fail "experience index missing"
[ -f docs/ai-instructions/experience-candidates.md ] || fail "experience candidates missing"
[ -f docs/ai-instructions/execution-lesson-candidates.md ] || fail "execution lesson candidates missing"
[ -f docs/ai-instructions/instructions/avoid-repeat-pitfalls.md ] || fail "avoid repeat pitfalls instruction missing"
[ -f docs/ai-instructions/solutions/README.md ] || fail "solutions README missing"
[ -f docs/ai-instructions/instructions/create-task-prompt-project.md ] || fail "task prompt project instruction missing"
[ -f docs/ai-instructions/instructions/use-builtin-template-task-packs.md ] || fail "builtin template task-pack instruction missing"
[ -f docs/ai-instructions/instructions/split-module-tree.md ] || fail "split module tree instruction missing"
[ -f docs/ai-instructions/instructions/module-map.md ] || fail "module map instruction missing"
[ -f docs/ai-instructions/instructions/progressive-module-discovery.md ] || fail "progressive module discovery instruction missing"
[ -f docs/ai-instructions/instructions/project-memory-loop.md ] || fail "project memory loop instruction missing"
[ -f docs/ai-instructions/instructions/project-upgrade-strategy.md ] || fail "project upgrade strategy instruction missing"
[ -f docs/ai-instructions/instructions/template-upgrade-strategy.md ] || fail "template upgrade strategy instruction missing"
[ -f docs/ai-instructions/templates/upgrade-decision-matrix.md ] || fail "upgrade decision matrix template missing"
[ -f .maw-template/upgrades/README.md ] || fail ".maw-template upgrades README missing"
[ -f docs/template-migrations/README.md ] || fail "template migrations README missing"
[ -f .maw-template/upgrades/20260712-centralized-module-changelog.yaml ] || fail "centralized module changelog upgrade asset missing"
[ -f docs/template-migrations/20260712-centralized-module-changelog.md ] || fail "centralized module changelog migration note missing"
[ -f .maw/project-lifecycle.yaml ] || fail "project lifecycle contract missing"
[ -f .maw/schemas/project-lifecycle.schema.json ] || fail "project lifecycle schema missing"
[ -f ops/scripts/manage-project-lifecycle.py ] || fail "project lifecycle manager missing"
[ -f docs/project-manual/manual.yaml ] || fail "project manual manifest missing"
[ -f .maw-template/upgrades/20260720-project-lifecycle-governance-v3.yaml ] || fail "project lifecycle upgrade asset missing"
[ -f docs/template-migrations/20260720-project-lifecycle-governance-v3.md ] || fail "project lifecycle migration note missing"
[ -f prompts/codex/template-upgrade-prompts/20260720-project-lifecycle-governance-v3-prompt.md ] || fail "project lifecycle upgrade prompt missing"
[ -f prompts/codex/template-upgrade-prompts/README.md ] || fail "template upgrade prompts README missing"
[ -f docs/ai-instructions/instructions/generate-template-feature-upgrade-prompt.md ] || fail "template feature upgrade prompt instruction missing"
[ -f docs/ai-instructions/instructions/external-ai-task-handoff.md ] || fail "external AI handoff instruction missing"
[ -f .maw-template/upgrades/20260812-blank-seed-component-cli-and-generic-ai-handoff.yaml ] || fail "blank Seed/component CLI upgrade asset missing"
[ -f docs/template-migrations/20260812-blank-seed-component-cli-and-generic-ai-handoff.md ] || fail "blank Seed/component CLI migration note missing"
[ -f docs/ai-instructions/instructions/dev-to-main-merge.md ] || fail "dev to main merge instruction missing"
[ -f docs/ai-instructions/instructions/release-component.md ] || fail "release component instruction missing"
[ -f docs/ai-instructions/instructions/publish-repository-mirror.md ] || fail "publish repository mirror instruction missing"
[ -f docs/ai-instructions/instructions/technical-map-project-metadata.md ] || fail "technical map project metadata instruction missing"
[ -f docs/ai-instructions/instructions/repository-identity-map.md ] || fail "repository identity instruction missing"
[ -f docs/repository-mirror-sync-guide.md ] || fail "repository mirror sync guide missing"
[ -f docs/repository-publish-mirror-guide.md ] || fail "repository publish mirror guide missing"
[ -f ops/scripts/sync-repository-mirror.sh ] || fail "repository mirror sync script missing"
[ -f ops/scripts/publish-repository-mirror.sh ] || fail "repository publish mirror script missing"
[ -f prompts/codex/task-packs/README.md ] || fail "task-packs README missing"
[ -f prompts/codex/task-packs/_template/manifest.json ] || fail "task-pack manifest template missing"
[ -f prompts/codex/task-packs/_template/EXECUTE_PROMPT.md ] || fail "task-pack execute prompt template missing"
[ -f prompts/codex/task-packs/_template/prompts/00-session-runbook.md ] || fail "task-pack runbook template missing"
[ -f prompts/codex/task-packs/template-feature-upgrade-codex-tasks/manifest.json ] || fail "template feature upgrade task pack missing"
[ -f prompts/codex/task-packs/adopt-maw-project-template-codex-tasks/manifest.json ] || fail "adopt MAW template task pack missing"
grep -Eq '模块档案|module dossier' docs/ai-instructions/README.md || fail "docs/ai-instructions/README.md must register module dossier instruction or term"
grep -Eq '模块树拆分|split-module-tree|生成 modules|模块拆细' docs/ai-instructions/README.md docs/ai-instructions/instructions/split-module-tree.md || fail "docs/ai-instructions must register module tree split instruction"
grep -Eq '渐进式模块发现|module_candidate|候选模块|TINST-021' docs/ai-instructions/README.md docs/ai-instructions/instructions/progressive-module-discovery.md || fail "progressive module discovery must be registered"
grep -Eq '项目记忆闭环|memory_update|local_update|TINST-022' docs/ai-instructions/README.md docs/ai-instructions/instructions/project-memory-loop.md || fail "project memory loop must be registered"
grep -Eq '项目升级策略|upgrade decision matrix|TINST-023' docs/ai-instructions/README.md docs/ai-instructions/instructions/project-upgrade-strategy.md || fail "project upgrade strategy must be registered"
grep -Eq '模板升级策略|升级资产|TINST-024' docs/ai-instructions/README.md docs/ai-instructions/instructions/template-upgrade-strategy.md || fail "template upgrade strategy must be registered"
require_grep '用户输入.*\.local/.maw/template-source\.yaml.*\.maw/template-source\.yaml.*当前仓库' .maw/codex-context.md docs/ai-instructions/instructions/project-upgrade-strategy.md docs/ai-instructions/instructions/use-builtin-template-task-packs.md GETTING_STARTED.md prompts/codex/task-packs/template-feature-upgrade-codex-tasks/README.md prompts/codex/task-packs/adopt-maw-project-template-codex-tasks/README.md
require_grep '个人本机路径|本机路径.*\.local|共享.*git' .maw/template-source.yaml .maw/README.md .local/README.md
require_grep 'R0|R1|R2|R3|R4' .maw/upgrade-policy.yaml docs/ai-instructions/instructions/project-upgrade-strategy.md docs/ai-instructions/templates/upgrade-decision-matrix.md
require_grep 'T0|T1|T2|T3|T4' .maw/upgrade-policy.yaml docs/ai-instructions/instructions/template-upgrade-strategy.md docs/ai-instructions/templates/upgrade-decision-matrix.md
require_grep '模块树优先协议' docs/modules/README.md
require_grep 'docs/changelogs/<module_key>\.md|changelog_path' docs/modules/README.md docs/changelogs/README.md docs/modules/_template/module.md docs/modules/_template/changelog.md docs/ai-coding/module-dossier-rules.md docs/ai-instructions/instructions/module-map.md .maw/modules.yaml .maw-template/template.yaml .maw-template/config-key-index.yaml
require_grep 'changelog_time' docs/modules/README.md docs/changelogs/README.md docs/modules/_template/module.md .maw/modules.yaml .maw-template/template.yaml
require_grep '自动.*迁移|旧格式.*迁移|读到即迁移' docs/modules/README.md docs/changelogs/README.md docs/ai-coding/module-dossier-rules.md docs/ai-instructions/instructions/module-map.md
if find docs/modules -type f -name changelog.md ! -path 'docs/modules/_template/changelog.md' -print -quit | grep -q .; then
  fail "legacy docs/modules/**/changelog.md must be migrated to docs/changelogs/"
fi
if grep -Eq '^    changelog:' .maw/modules.yaml; then
  fail ".maw/modules.yaml must use changelog_path and changelog_time"
fi
if rg -n '^#{2,6} (最近变更摘要|变更记录|变更历史|Changelog)$' docs/modules --glob 'module.md' >/dev/null 2>&1; then
  fail "module.md must not embed changelog history"
fi
python3 ops/scripts/migrate-module-changelogs.py check --format json >/dev/null || fail "centralized module changelog migration check failed"
require_grep 'route-api-index|URL/API 定位索引|页面审计页|后端审计页|traceability' docs/modules/README.md docs/modules/_template/route-api-index.md docs/modules/_template/page.md docs/modules/_template/backend-slice.md docs/modules/_template/traceability.md docs/ai-coding/module-dossier-rules.md
require_grep 'doc_status|last_verified_commit|confidence|source_paths' docs/modules/README.md .maw/modules.yaml docs/modules/_template/module.md docs/modules/_template/route-api-index.md docs/modules/_template/page.md docs/modules/_template/backend-slice.md docs/modules/_template/traceability.md docs/ai-instructions/instructions/module-map.md docs/ai-coding/module-dossier-rules.md
require_grep 'stale|deprecated|last_audit_id|module_map_score' docs/modules/README.md .maw/modules.yaml docs/modules/_audits/README.md docs/modules/_audits/_template.md docs/ai-instructions/instructions/module-map.md .maw-template/template.yaml
require_grep 'route_index_coverage|api_owner_coverage|detail_doc_coverage|traceability_coverage|stale_docs_count|orphan_docs_count|missing_changelog_count' docs/modules/README.md docs/modules/_audits/_template.md docs/ai-instructions/instructions/module-map.md .maw/modules.yaml .maw-template/template.yaml
require_grep '渐进式模块发现|module-candidates|module_candidate' docs/modules/README.md .maw/module-candidates.yaml docs/modules/_discovery/README.md
require_grep 'group.*/.*leaf|group / leaf|模块拆分判定表' docs/modules/README.md docs/modules/_template/group-README.md
require_grep 'TINST-036|#模块地图|route-api-index|渐进式补全' docs/ai-instructions/README.md docs/ai-instructions/instructions/module-map.md PROJECT_COMMANDS.md .maw-template/upgrades/20260622-module-map-route-api-index.yaml docs/template-migrations/20260622-module-map-route-api-index.md prompts/codex/template-upgrade-prompts/20260622-module-map-route-api-index-prompt.md
require_grep '#模块地图：检查|#模块地图：清理过期|#模块地图：变更影响|发布前检查' docs/ai-instructions/README.md docs/ai-instructions/instructions/module-map.md PROJECT_COMMANDS.md
require_grep 'TINST-036|module_map_score|last_verified_commit|stale|deprecated' .maw-template/upgrades/20260622-module-map-evidence-audit.yaml docs/template-migrations/20260622-module-map-evidence-audit.md prompts/codex/template-upgrade-prompts/20260622-module-map-evidence-audit-prompt.md
require_grep 'TINST-038|#项目健康|check-project-health-context|health_context_update_status' docs/ai-instructions/README.md docs/ai-instructions/instructions/project-health-context.md PROJECT_COMMANDS.md docs/ai-instructions/instructions/final-closeout-response.md docs/ai-instructions/templates/final-closeout.zh-CN.md docs/ai-coding/module-dossier-rules.md docs/ai-coding/coding-style.md
require_grep 'project-health-context|\.maw/health|20260627-project-health-context' .maw/capabilities.yaml .maw/project-signals.yaml .maw-template/template.yaml .maw-template/upgrades/20260627-project-health-context.yaml docs/template-migrations/20260627-project-health-context.md prompts/codex/template-upgrade-prompts/20260627-project-health-context-prompt.md docs/capabilities/project-health-context.md
require_grep 'ai-model-adapter-evaluation|model-requirements|pending_eval|public_safe_summary|mawflow base model-adapter|MCP Knowledge Runtime' .maw/model-requirements.yaml .maw/model-evaluation/cases.example.json .maw/model-evaluation/output-contract.example.json docs/implementation/ai-model-adapter-evaluation/README.md docs/capabilities/ai-model-adapter-evaluation.md
require_grep 'ai_model_adapter_evaluation_protocol|provider_specific_adapters_live_in_main_repo|public_summary_excludes_raw_prompts_and_outputs' .maw-template/template.yaml .maw-template/upgrades/20260708-ai-model-adapter-evaluation-protocol.yaml
require_grep 'SIG-20260708-ai-model-adapter-evaluation|ai-model-adapter-evaluation|check-model-evaluation-protocol' .maw/capabilities.yaml .maw/project-signals.yaml package.json ops/scripts/README.md docs/README.md docs/template-migrations/20260708-ai-model-adapter-evaluation-protocol.md prompts/codex/template-upgrade-prompts/20260708-ai-model-adapter-evaluation-protocol-prompt.md
require_grep 'AI_START_HERE|agent-entry|agent-rules|AI 工作目录|workdir assistant' AI_START_HERE.md AGENTS.md .maw/agent-entry.yaml .maw/agent-rules.yaml docs/capabilities/ai-workdir-entry-protocol.md docs/public-seed/README.md docs/public-seed/quickstart.md
require_grep 'ai-workdir-entry-protocol|SIG-20260709-ai-workdir-entry-protocol|AI 工作目录入口协议' .maw/capabilities.yaml .maw/project-signals.yaml docs/README.md docs/capabilities/ai-workdir-entry-protocol.md
require_grep 'ai_workdir_entry_protocol|existing_agents_md_must_be_merged_not_overwritten|prompts_remain_manual_only' .maw-template/template.yaml .maw-template/upgrades/20260709-ai-workdir-entry-protocol.yaml docs/template-migrations/20260709-ai-workdir-entry-protocol.md prompts/codex/template-upgrade-prompts/20260709-ai-workdir-entry-protocol-prompt.md
require_grep 'TINST-010|模块树|leaf 判定|group' docs/ai-instructions/instructions/generate-module-dossier-draft.md
require_grep 'group|leaf|component|cross-cutting' .maw/modules.yaml
require_grep '业务项目|项目 README|TEMPLATE_OVERVIEW.md' README.md
require_grep 'GETTING_STARTED.md' README.md TEMPLATE_OVERVIEW.md
require_grep 'PROJECT_COMMANDS.md' README.md TEMPLATE_OVERVIEW.md
require_grep 'CHATGPT_TO_AI.md' README.md TEMPLATE_OVERVIEW.md GETTING_STARTED.md docs/template-usage-guide.md
require_grep '目标|范围|验收|接收方 AI' CHATGPT_TO_AI.md
require_grep '远程.*zip|zip.*直链|分享页' PROJECT_COMMANDS.md docs/ai-instructions/README.md docs/ai-instructions/instructions/create-task-prompt-project.md prompts/codex/task-packs/README.md
require_grep '可道云|Kodbox' PROJECT_COMMANDS.md docs/ai-instructions/README.md docs/ai-instructions/instructions/create-task-prompt-project.md prompts/codex/task-packs/README.md
require_grep 'CHATGPT_TO_AI\.md' docs/ai-instructions/instructions/create-task-prompt-project.md
require_grep 'CHATGPT_TO_CODEX\.md' prompts/codex/task-packs/README.md docs/template-migrations/20260614-task-pack-remote-zip-import.md
require_grep '临时.*工作区|临时.*下载|不.*直接执行远程内容' docs/ai-instructions/instructions/create-task-prompt-project.md prompts/codex/task-packs/README.md docs/template-repository-ai-design.md
require_grep 'ChatGPT.*AI|外部 AI|任务交接协议' CHATGPT_TO_AI.md docs/ai-instructions/instructions/external-ai-task-handoff.md
require_grep '生成 modules|模块树|模板仓库升级' PROJECT_COMMANDS.md
require_grep '快捷调用格式' PROJECT_COMMANDS.md
require_grep '调用示例|复制.*<\\.\\.\\.>|改.*参数' PROJECT_COMMANDS.md
require_grep 'TINST-XXX|#TXXX|PINST-XXX|#PXXX|编号命名空间' docs/ai-instructions/README.md PROJECT_COMMANDS.md
require_grep '#关键字' PROJECT_COMMANDS.md docs/ai-instructions/README.md
require_grep '#\\+指令|习惯用语|口头指令' PROJECT_COMMANDS.md docs/ai-instructions/README.md docs/ai-instructions/instructions/use-project-instructions.md AGENTS.md
require_grep '#项目指令' PROJECT_COMMANDS.md
require_grep '#任务包' PROJECT_COMMANDS.md GETTING_STARTED.md
require_grep '#跑任务包' PROJECT_COMMANDS.md
require_grep '#模版升级' PROJECT_COMMANDS.md GETTING_STARTED.md docs/ai-instructions/README.md docs/ai-instructions/instructions/generate-template-feature-upgrade-prompt.md
require_grep '#项目升级' PROJECT_COMMANDS.md GETTING_STARTED.md docs/ai-instructions/README.md docs/ai-instructions/instructions/use-builtin-template-task-packs.md
require_grep '#模板化' PROJECT_COMMANDS.md GETTING_STARTED.md docs/ai-instructions/README.md docs/ai-instructions/instructions/use-builtin-template-task-packs.md
require_grep '#跑任务包：prompts/codex/task-packs/<slug>-codex-tasks' PROJECT_COMMANDS.md
require_grep '#项目升级：把源模板' PROJECT_COMMANDS.md
require_grep '#同步镜像仓库：同步 <app_key> 镜像仓库' PROJECT_COMMANDS.md
require_grep '#T001' PROJECT_COMMANDS.md
require_grep '#P001|PINST-001' docs/ai-instructions/README.md docs/ai-instructions/instructions/use-project-instructions.md
require_grep '#T007/创建|#T007/执行' PROJECT_COMMANDS.md
require_grep '#T011' PROJECT_COMMANDS.md
require_grep '#交接任务' PROJECT_COMMANDS.md docs/ai-instructions/README.md docs/ai-instructions/instructions/external-ai-task-handoff.md
require_grep '#T012|TINST-012' PROJECT_COMMANDS.md docs/ai-instructions/README.md docs/ai-instructions/instructions/external-ai-task-handoff.md
require_grep '#提主' PROJECT_COMMANDS.md docs/ai-instructions/README.md docs/ai-instructions/instructions/dev-to-main-merge.md
require_grep '#T013|TINST-013' PROJECT_COMMANDS.md docs/ai-instructions/README.md docs/ai-instructions/instructions/dev-to-main-merge.md
require_grep 'dev.*main|origin/dev|origin/main|仓库级镜像' docs/ai-instructions/instructions/dev-to-main-merge.md
require_grep '#发布' PROJECT_COMMANDS.md docs/ai-instructions/README.md docs/ai-instructions/instructions/release-component.md docs/ai-coding/module-dossier-rules.md
require_grep '#T014|TINST-014' PROJECT_COMMANDS.md docs/ai-instructions/README.md docs/ai-instructions/instructions/release-component.md
require_grep '发布测试|发布上线|发布生产|发布生成' PROJECT_COMMANDS.md docs/ai-instructions/README.md docs/ai-instructions/instructions/release-component.md docs/ai-instructions/experience-index.md
require_grep '#发布公开镜像|#发布开源镜像|TINST-039|repository_publish_mirrors' PROJECT_COMMANDS.md docs/ai-instructions/README.md docs/ai-instructions/instructions/publish-repository-mirror.md docs/ai-instructions/experience-index.md docs/repository-publish-mirror-guide.md
require_grep 'publish-repository-mirror\.sh|same_git_history|export_sanitized_tree' .maw/repositories.yaml docs/repository-publish-mirror-guide.md ops/scripts/README.md docs/capabilities/repository-publish-mirror.md
private_seed_channel='internal_'"seed"
require_grep "seed-source-channel-publication|${private_seed_channel}|public_seed|unknown_legacy" .maw/template-source.yaml .maw/capabilities.yaml .maw/project-signals.yaml .maw-template/template.yaml docs/capabilities/seed-source-channel-publication.md docs/template-migrations/20260701-seed-source-channel-publication.md prompts/codex/template-upgrade-prompts/20260701-seed-source-channel-publication-prompt.md
require_grep 'release_commands|release_confirmation_prompt' docs/ai-coding/module-dossier-rules.md .maw/codex-context.md docs/ai-coding/coding-style.md prompts/codex/task-packs/_template/prompts/01-task-template.md prompts/codex/task-packs/_template/EXECUTE_PROMPT.md
require_grep '多个 app_key|部分发布|复制其中一条' docs/ai-coding/module-dossier-rules.md .maw/codex-context.md docs/ai-instructions/instructions/release-component.md PROJECT_COMMANDS.md prompts/codex/task-packs/_template/prompts/01-task-template.md
require_grep 'default_environment|environment_options|release_commands' .maw/releases.yaml docs/configuration-guide.md docs/ai-instructions/instructions/release-component.md
require_grep 'release_command_aliases|发布测试|发布上线|发布生产|发布生成' .maw/releases.yaml docs/configuration-guide.md docs/ai-instructions/instructions/release-component.md
require_grep 'default_release_components' .maw/environments.yaml .maw/environments.dev.yaml .maw/environments.pro.yaml .local/.maw/environments.example.yaml docs/configuration-guide.md docs/ai-instructions/instructions/release-component.md
require_grep 'remote_test_server|remote_staging_server|remote_production_server' .maw/releases.yaml docs/ai-instructions/instructions/release-component.md PROJECT_COMMANDS.md
require_grep 'release-experience|发布经验|local_update' .local/README.md .local/ai/README.md docs/ai-instructions/instructions/release-component.md docs/ai-instructions/instructions/project-memory-loop.md docs/ai-instructions/instructions/final-closeout-response.md docs/template-usage-guide.md
require_grep '^components: \[\]|components: \[\]' .maw/components.yaml
require_grep 'components: \{\}' .maw/releases.yaml
require_grep 'test.*staging.*production|test.*production' .maw/releases.yaml
require_grep '歧义|向用户确认|不得自行猜测' PROJECT_COMMANDS.md docs/ai-instructions/README.md docs/ai-instructions/instructions/use-project-instructions.md
require_grep '当前仓库角色|先问清楚|先向用户确认' .maw/codex-context.md AGENTS.md docs/ai-instructions/instructions/use-project-instructions.md
require_grep '#T001' docs/ai-instructions/README.md docs/ai-instructions/instructions/use-project-instructions.md
require_grep '#T指令号/关键字|#P指令号/关键字' docs/ai-instructions/instructions/use-project-instructions.md
require_grep '维护 PROJECT_COMMANDS' docs/ai-instructions/instructions/update-project-instructions.md
require_grep 'PROJECT_COMMANDS.md' docs/ai-instructions/instructions/update-project-instructions.md
require_grep '调用示例|可复制调用示例' docs/ai-instructions/README.md docs/ai-instructions/instructions/update-project-instructions.md
require_grep '推荐调用.*#<最常用关键字>' docs/ai-instructions/templates/instruction.md
require_grep '精确调用.*#TXXX|精确调用.*#PXXX' docs/ai-instructions/templates/instruction.md
require_grep '不创建任何默认组件|默认组件.*空' GETTING_STARTED.md
require_grep '不创建任何默认组件|默认组件.*空|不预设任何端|不内置.*组件' GETTING_STARTED.md TEMPLATE_OVERVIEW.md code/README.md
require_grep 'group.*leaf' GETTING_STARTED.md docs/modules/README.md
python3 - <<'PY'
from pathlib import Path

try:
    import yaml
except ImportError as exc:
    raise SystemExit(f"FAIL: PyYAML is required to check .maw-template/template.yaml: {exc}")

doc = yaml.safe_load(Path(".maw-template/template.yaml").read_text(encoding="utf-8")) or {}
template = doc.get("template") or {}
default_components = template.get("default_components") or []
if default_components != []:
    raise SystemExit(
        "FAIL: .maw-template/template.yaml default_components must be empty"
    )

optional_components = template.get("optional_components") or []
optional_names = []
for item in optional_components:
    if isinstance(item, dict):
        optional_names.append(item.get("key"))
    else:
        optional_names.append(item)

if optional_names:
    raise SystemExit("FAIL: .maw-template/template.yaml optional_components must be empty")
PY
if find code/admin release/admin docs/modules/admin -maxdepth 0 -print 2>/dev/null | grep -q . || [ -f docs/ai-coding/component-guides/admin.md ]; then
  fail "template must not include default admin component files"
fi
if rg -n 'code/admin|release/admin|app_runtime\.apps\.admin|component_mirrors\.components\.admin|external_components\.admin' .maw docs code release prompts README.md GETTING_STARTED.md PROJECT_COMMANDS.md >/dev/null 2>&1; then
  fail "default admin component references must not appear outside explicit non-default guidance"
fi
if rg -n 'code/client2|apps\.client2|component_mirrors\.components\.client2|external_components\.client2|mirror_components\.client2' .maw docs code release prompts README.md GETTING_STARTED.md PROJECT_COMMANDS.md >/dev/null 2>&1; then
  fail "template must not commit client2 placeholders"
fi
grep -Eq '关键词学习|经验候选|执行复盘|keyword-candidates|experience-candidates|execution-lesson-candidates' docs/ai-instructions/README.md || fail "docs/ai-instructions/README.md must register keyword learning"
require_grep '用户口径|习惯用语|别称' docs/ai-instructions/instructions/project-memory-loop.md docs/ai-instructions/instructions/keyword-learning-loop.md docs/ai-instructions/instructions/final-closeout-response.md PROJECT_COMMANDS.md
require_grep 'user_terms_style|用户口径' docs/ai-instructions/templates/final-closeout.zh-CN.md docs/ai-instructions/instructions/final-closeout-response.md
grep -Eq 'local_update|memory_update|项目记忆|本机记忆' docs/ai-instructions/instructions/project-memory-loop.md docs/ai-instructions/templates/final-closeout.zh-CN.md || fail "project memory closeout metadata must be documented"
require_grep 'TINST-028|#待办任务|docs/planning/todos|todo_task_update_status' PROJECT_COMMANDS.md docs/ai-instructions/README.md docs/ai-instructions/instructions/todo-task-governance.md docs/planning/todos/README.md docs/ai-coding/module-dossier-rules.md
require_grep 'TINST-030|#技术地图|capability_map_update_status|project_signal_update_status' PROJECT_COMMANDS.md docs/ai-instructions/README.md docs/ai-instructions/instructions/technical-map-project-metadata.md docs/technical-map/README.md docs/ai-coding/module-dossier-rules.md
require_grep 'TINST-027|#种子仓库升级|seed-repository-upgrade-prompts|seed-repository-feedback-loop|needs_more_evidence' PROJECT_COMMANDS.md docs/ai-instructions/README.md docs/ai-instructions/instructions/seed-repository-upgrade.md docs/seed-repository-upgrade-candidates.md prompts/codex/seed-repository-upgrade-prompts/README.md .maw/capabilities.yaml .maw/project-signals.yaml .maw/upgrade-policy.yaml .maw-template/template.yaml
require_grep 'TINST-031|#仓库身份|repository_identity_update_status' PROJECT_COMMANDS.md docs/ai-instructions/README.md docs/ai-instructions/instructions/repository-identity-map.md docs/repository-identity/README.md docs/ai-coding/module-dossier-rules.md
require_grep 'TINST-032|#脚本规范|AI Python Script Contract|check-ai-python-script-contract|run-project-tests.py' PROJECT_COMMANDS.md docs/ai-instructions/README.md docs/ai-instructions/instructions/script-contract-upgrade.md docs/capabilities/ai-python-script-contract.md ops/scripts/README.md
require_grep 'TINST-033|#文档索引|doc-read-contract|extract-doc-index|check-doc-read-contract' PROJECT_COMMANDS.md docs/ai-instructions/README.md docs/ai-instructions/instructions/doc-read-contract.md docs/capabilities/doc-read-contract.md docs/doc-read-contract/README.md ops/scripts/README.md
require_grep 'TINST-034|#会话概要|recent-session-briefs|write-session-brief|ai-session-briefs' PROJECT_COMMANDS.md docs/ai-instructions/README.md docs/ai-instructions/instructions/recent-session-briefs.md docs/capabilities/recent-session-briefs.md docs/ai-session-briefs/README.md ops/scripts/README.md .maw/capabilities.yaml .maw/project-signals.yaml .maw-template/template.yaml
require_grep 'TINST-029|#MCP服务诊断|MAW_MCP_ENDPOINT|project_level_mcp' PROJECT_COMMANDS.md docs/ai-instructions/README.md docs/ai-instructions/instructions/mcp-service-diagnostics.md docs/implementation/local-mcp-gateway/README.md .maw/environments.yaml
require_grep 'host_project_binding|ownership_type|binding_type|source_access_mode|mcp_exposure_profile|host-project-mcp-governance' .maw/environments.yaml .maw/capabilities.yaml .maw/project-signals.yaml docs/implementation/host-purpose-modes/README.md docs/implementation/local-mcp-gateway/README.md docs/ai-instructions/instructions/mcp-service-diagnostics.md ops/scripts/extract-project-metadata.py
require_grep 'host_runtime_environment|host-runtime-environment-protocol|Docker-first|offline_image_delivery|local_host_data_plane|naming_convention|change_safety' .maw/environments.yaml .maw/capabilities.yaml .maw/project-signals.yaml .maw-template/template.yaml docs/implementation/host-runtime-environments/README.md docs/capabilities/host-runtime-environment-protocol.md ops/scripts/check-host-runtime-environment.sh
require_grep 'check-host-runtime-environment|Docker.*命名|用户确认|本地宿主机 PG' docs/README.md docs/implementation/README.md docs/technical-map/README.md ops/scripts/README.md
require_grep 'check-seed-distribution-readiness.sh|seed-distribution-readiness-audit|分发就绪' .maw/capabilities.yaml .maw/project-signals.yaml ops/scripts/README.md reports/audits/20260617-seed-distribution-readiness.md
require_grep 'ai-python-script-contract|project-test-runner|script-contract-upgrade|check-ai-python-script-contract.py|run-project-tests.py' .maw/capabilities.yaml .maw/project-signals.yaml .maw-template/template.yaml .maw-template/upgrades/20260619-ai-python-script-contract.yaml
require_grep 'doc-read-contract|doc_read_contract|extract-doc-index.py|check-doc-read-contract.py|project_health' .maw/doc-taxonomy.yaml .maw/capabilities.yaml .maw/project-signals.yaml .maw-template/template.yaml .maw-template/upgrades/20260620-doc-read-contract.yaml
require_grep 'recent-session-briefs|recent_session_briefs|会话概要|cross-device|short-term' .maw/capabilities.yaml .maw/project-signals.yaml .maw-template/template.yaml .maw-template/upgrades/20260621-recent-session-briefs.yaml docs/template-migrations/20260621-recent-session-briefs.md prompts/codex/template-upgrade-prompts/20260621-recent-session-briefs-prompt.md
require_grep 'extract-project-metadata.py|check-technical-map.sh' docs/technical-map/README.md ops/scripts/README.md .maw-template/template.yaml
require_grep 'repository-identity|check-repository-identity.sh|role_detection|repository.identity.role' docs/repository-identity/README.md ops/scripts/README.md .maw-template/template.yaml .maw-template/config-key-index.yaml
require_grep '公共能力|项目提示信号|AI 前置' docs/technical-map/README.md docs/capabilities/README.md docs/project-signals/README.md
require_grep 'check-ai-framework-consistency|check-code-deliverable|export-code-only' ops/scripts/README.md PROJECT_COMMANDS.md prompts/README.md prompts/codex/README.md prompts/codex/task-packs/README.md
require_grep 'check-repository-mirror-config|template_maintenance.github_mirror|auto_sync_after_project_push' ops/scripts/README.md docs/repository-mirror-sync-guide.md .local/README.md
require_grep 'template_maintenance:|github_mirror:|auto_sync_after_project_push' .local/.maw/repositories.example.yaml
require_grep 'language.*zh-CN|audience.*human_and_codex|closeout_profile.*zh_cn_human_first|delivery_mode.*code_only' prompts/codex/task-packs/_template/manifest.json docs/ai-instructions/instructions/create-task-prompt-project.md
require_grep 'documentation_language.*zh-CN' prompts/codex/task-packs/_template/manifest.json prompts/codex/task-packs/adopt-maw-project-template-codex-tasks/manifest.json
require_grep 'documentation: zh-CN|generated_documentation: zh-CN|task_pack_body: zh-CN' .maw/interaction.yaml
require_grep 'i18n|中文给人读|英文.*AI|human.*zh-CN|ai.*en-US' .maw/interaction.yaml .maw-template/template.yaml docs/template-repository-ai-design.md docs/ai-instructions/instructions/final-closeout-response.md docs/ai-instructions/instructions/create-task-prompt-project.md docs/ai-instructions/instructions/use-builtin-template-task-packs.md prompts/codex/task-packs/_template/manifest.json prompts/codex/task-packs/adopt-maw-project-template-codex-tasks/manifest.json .maw-template/upgrades/20260706-derived-doc-language-default.yaml
require_grep '文档语言|默认.*中文|documentation|generated_documentation|task_pack_body|component guide|Component Guide|中文标题' .maw/codex-context.md docs/template-repository-ai-design.md docs/ai-instructions/instructions/create-task-prompt-project.md docs/ai-instructions/instructions/use-builtin-template-task-packs.md docs/ai-instructions/instructions/final-closeout-response.md prompts/codex/task-packs/adopt-maw-project-template-codex-tasks/README.md prompts/codex/task-packs/adopt-maw-project-template-codex-tasks/PLAN.md
require_grep '中文.*人类优先|人类优先.*中文' prompts/codex/task-packs/_template/EXECUTE_PROMPT.md prompts/codex/task-packs/_template/prompts/00-session-runbook.md prompts/codex/task-packs/README.md
if grep -R -nE '^(## (Goal|Baseline|Highest Priority Rules|Required Reads|Objective|Implementation Requirements|Suggested Commands|Acceptance Criteria|Final Response Requirements)|# .*Session Runbook|# .+ Component Guide|## (Scope|Build Notes|Sensitive Config))$' \
  prompts/codex/task-packs/_template \
  prompts/codex/task-packs/adopt-maw-project-template-codex-tasks \
  docs/ai-coding/component-guides >/tmp/maw-english-doc-headings.$$; then
  cat /tmp/maw-english-doc-headings.$$ >&2
  rm -f /tmp/maw-english-doc-headings.$$
  fail "task-pack templates and generated component guide templates must use Chinese headings by default"
fi
rm -f /tmp/maw-english-doc-headings.$$
require_grep 'dry-run|customer|developer|CHECKSUMS|delivery-report' ops/scripts/export-code-only.sh ops/scripts/README.md
grep -Eq '经验防重复踩坑|avoid-repeat-pitfalls|experience-index|solutions' docs/ai-instructions/README.md docs/ai-instructions/experience-index.md docs/ai-instructions/solutions/README.md || fail "experience index and solutions protocol must be registered"
grep -Eq '不得主动全量读取|不主动.*solutions|命中.*索引' docs/ai-instructions/solutions/README.md .maw/codex-context.md || fail "solutions must require index-first reading"
require_grep 'experience-index' RTK.md docs/ai-coding/README.md docs/ai-instructions/instructions/use-project-instructions.md docs/ai-instructions/instructions/update-project-instructions.md
require_grep 'solutions' RTK.md docs/ai-coding/README.md docs/ai-instructions/instructions/use-project-instructions.md docs/ai-instructions/instructions/update-project-instructions.md
require_grep 'maw-key-get|config-key-index|template\.applied_version|release\.component\.command|module\.dossier' docs/configuration-guide.md ops/scripts/README.md .maw-template/config-key-index.yaml
grep -Eq '同步.*镜像仓库|component_mirrors|sync-app-mirror-repository' docs/ai-instructions/README.md || fail "docs/ai-instructions/README.md must register mirror repository sync instruction"
grep -Eq '创建任务提示词工程|执行任务提示词工程|task-packs' docs/ai-instructions/README.md prompts/codex/task-packs/README.md || fail "task prompt project instruction must be registered"
grep -Eq 'EXECUTE_PROMPT\.md|执行本次任务提示词' docs/ai-instructions/instructions/create-task-prompt-project.md prompts/README.md prompts/codex/README.md prompts/codex/task-packs/README.md prompts/codex/task-packs/_template/README.md prompts/codex/task-packs/_template/EXECUTE_PROMPT.md || fail "task pack execute prompt file must be documented"
grep -Eq '内置任务提示词工程|模板仓库升级|模板化改造|use-builtin-template-task-packs' docs/ai-instructions/README.md docs/ai-instructions/instructions/use-builtin-template-task-packs.md || fail "builtin template task-pack instruction must be registered"
grep -Eq '生成模板新特性升级提示词|generate-template-feature-upgrade-prompt|轻量升级提示词' docs/ai-instructions/README.md docs/ai-instructions/instructions/generate-template-feature-upgrade-prompt.md PROJECT_COMMANDS.md || fail "template feature upgrade prompt instruction must be registered"
require_grep 'TINST-026|plan-template-drift|applied_version|模板漂移' docs/ai-instructions/README.md docs/ai-instructions/experience-index.md docs/ai-instructions/instructions/derived-template-drift-upgrade.md PROJECT_COMMANDS.md ops/scripts/README.md .maw/template-source.yaml
python3 -m json.tool prompts/codex/task-packs/_template/manifest.json >/dev/null
grep -Eq '"entry_prompt": "EXECUTE_PROMPT.md"' prompts/codex/task-packs/_template/manifest.json || fail "task-pack template manifest must use EXECUTE_PROMPT.md as entry_prompt"
require_grep '"EXECUTE_PROMPT.md"' prompts/codex/task-packs/_template/manifest.json
for manifest in prompts/codex/task-packs/*-codex-tasks/manifest.json; do
  python3 -m json.tool "$manifest" >/dev/null
done
grep -Eq 'SESSION_STATE|NEXT_TASK|RESUME_FROM' prompts/codex/task-packs/README.md prompts/codex/task-packs/_template/prompts/00-session-runbook.md || fail "task-pack docs must include resume protocol"
require_grep 'download-task-pack-url|file-storage|可信文件存储|trusted file storage' docs/ai-instructions/instructions/create-task-prompt-project.md PROJECT_COMMANDS.md prompts/codex/task-packs/README.md ops/scripts/README.md
require_grep '执行任务提示词工程：prompts/codex/task-packs/<slug>-codex-tasks' prompts/codex/task-packs/_template/EXECUTE_PROMPT.md
require_grep 'same_session_auto_run' prompts/codex/task-packs/_template/EXECUTE_PROMPT.md
require_grep 'SESSION_STATE|NEXT_TASK|RESUME_FROM' prompts/codex/task-packs/_template/EXECUTE_PROMPT.md
require_grep '提交并推送|git status --short' prompts/codex/task-packs/_template/EXECUTE_PROMPT.md
require_grep 'SESSION_STATE' prompts/codex/task-packs/template-feature-upgrade-codex-tasks/prompts/00-session-runbook.md prompts/codex/task-packs/adopt-maw-project-template-codex-tasks/prompts/00-session-runbook.md
require_grep 'NEXT_TASK' prompts/codex/task-packs/template-feature-upgrade-codex-tasks/prompts/00-session-runbook.md prompts/codex/task-packs/adopt-maw-project-template-codex-tasks/prompts/00-session-runbook.md
require_grep 'RESUME_FROM' prompts/codex/task-packs/template-feature-upgrade-codex-tasks/prompts/00-session-runbook.md prompts/codex/task-packs/adopt-maw-project-template-codex-tasks/prompts/00-session-runbook.md
require_grep 'server.*client' prompts/codex/task-packs/template-feature-upgrade-codex-tasks/README.md prompts/codex/task-packs/adopt-maw-project-template-codex-tasks/README.md prompts/codex/task-packs/README.md
require_grep 'admin.*保留|保留.*admin|不得.*admin.*删除|误删.*admin' prompts/codex/task-packs/template-feature-upgrade-codex-tasks/README.md prompts/codex/task-packs/template-feature-upgrade-codex-tasks/prompts/00-session-runbook.md prompts/codex/06-codex-upgrade-template-features.md
require_grep '不.*凭空新增.*后台|凭空新增.*后台|不创建后台占位|没有独立后台.*不.*创建' prompts/codex/task-packs/adopt-maw-project-template-codex-tasks/README.md prompts/codex/task-packs/adopt-maw-project-template-codex-tasks/prompts/02-template-adoption-plan.md prompts/codex/task-packs/adopt-maw-project-template-codex-tasks/prompts/04-component-module-alignment.md
require_grep 'README.*业务项目|业务项目.*README|不得.*覆盖.*README|TEMPLATE_OVERVIEW' prompts/codex/task-packs/template-feature-upgrade-codex-tasks/README.md prompts/codex/task-packs/adopt-maw-project-template-codex-tasks/README.md docs/ai-instructions/instructions/use-builtin-template-task-packs.md
require_grep 'experience_lookup' prompts/codex/task-packs/template-feature-upgrade-codex-tasks/prompts/01-baseline-and-diff-audit.md prompts/codex/task-packs/adopt-maw-project-template-codex-tasks/prompts/01-project-fact-audit.md
require_grep 'release_update_status' prompts/codex/task-packs/template-feature-upgrade-codex-tasks/prompts/04-validation-and-closeout.md prompts/codex/task-packs/adopt-maw-project-template-codex-tasks/prompts/05-validation-and-handoff.md
require_grep 'template-feature-upgrade-codex-tasks' docs/ai-instructions/README.md docs/ai-instructions/instructions/use-builtin-template-task-packs.md prompts/codex/README.md prompts/README.md
require_grep 'adopt-maw-project-template-codex-tasks' docs/ai-instructions/README.md docs/ai-instructions/instructions/use-builtin-template-task-packs.md prompts/codex/README.md prompts/README.md
require_grep '公开示例|_template|examples/mawflow-packs/task-pack' prompts/codex/task-packs/README.md
require_grep '源模板本机路径：<源模板本机路径' GETTING_STARTED.md docs/ai-instructions/instructions/use-builtin-template-task-packs.md prompts/codex/task-packs/template-feature-upgrade-codex-tasks/README.md prompts/codex/task-packs/adopt-maw-project-template-codex-tasks/README.md docs/ai-instructions/instructions/generate-template-feature-upgrade-prompt.md
require_grep '本机模板仓库目录：<生成时填入当前模板仓库' docs/ai-instructions/instructions/generate-template-feature-upgrade-prompt.md
require_grep '本机模板仓库目录读取规则' docs/ai-instructions/instructions/generate-template-feature-upgrade-prompt.md prompts/codex/template-upgrade-prompts/README.md
require_grep "Seed 来源通道|source_channel|${private_seed_channel}|内部来源通道|public_seed|unknown_legacy" .maw/template-source.yaml GETTING_STARTED.md docs/ai-instructions/README.md docs/ai-instructions/instructions/derived-template-drift-upgrade.md docs/ai-instructions/instructions/generate-template-feature-upgrade-prompt.md prompts/codex/task-packs/template-feature-upgrade-codex-tasks/README.md prompts/codex/task-packs/adopt-maw-project-template-codex-tasks/README.md
require_grep 'https://github\.com/mawflow/mawflow-seed|外部公开项目不得读取内部私有 Seed 源' GETTING_STARTED.md docs/ai-instructions/instructions/use-builtin-template-task-packs.md prompts/codex/task-packs/template-feature-upgrade-codex-tasks/README.md prompts/codex/task-packs/adopt-maw-project-template-codex-tasks/README.md docs/ai-instructions/instructions/generate-template-feature-upgrade-prompt.md
require_grep '源模板读取优先级：用户输入 > \.local/\.maw/template-source\.yaml > \.maw/template-source\.yaml > 当前仓库' GETTING_STARTED.md docs/ai-instructions/instructions/use-builtin-template-task-packs.md prompts/codex/task-packs/template-feature-upgrade-codex-tasks/README.md prompts/codex/task-packs/adopt-maw-project-template-codex-tasks/README.md docs/ai-instructions/instructions/generate-template-feature-upgrade-prompt.md
require_grep '源模板版本：main' GETTING_STARTED.md docs/ai-instructions/instructions/use-builtin-template-task-packs.md prompts/codex/task-packs/template-feature-upgrade-codex-tasks/README.md prompts/codex/task-packs/adopt-maw-project-template-codex-tasks/README.md
require_grep '源模板版本：<生成时填入当前模板仓库 HEAD commit' docs/ai-instructions/instructions/generate-template-feature-upgrade-prompt.md
require_grep '未指定 commit.*当前仓库角色|是否指定 commit 不决定在哪个仓库执行' PROJECT_COMMANDS.md docs/ai-instructions/README.md docs/ai-instructions/instructions/template-upgrade-strategy.md docs/ai-instructions/instructions/derived-template-drift-upgrade.md AGENTS.md
require_grep 'template_source.version.*默认.*main|默认 `main`' docs/ai-instructions/instructions/derived-template-drift-upgrade.md .maw/codex-context.md AGENTS.md
require_grep '不要只.*任务包路径|任务包目录推测|只凭任务包目录' docs/ai-instructions/instructions/use-builtin-template-task-packs.md prompts/codex/task-packs/README.md prompts/codex/task-packs/template-feature-upgrade-codex-tasks/prompts/00-session-runbook.md
require_grep 'EXP-003' docs/ai-instructions/experience-index.md
require_grep 'EXP-005' docs/ai-instructions/experience-index.md
require_grep 'EXP-006' docs/ai-instructions/experience-index.md
require_grep 'CHATGPT_TO_AI|任务提示词 zip|交接任务' docs/ai-instructions/experience-index.md
require_grep 'EXP-007' docs/ai-instructions/experience-index.md
require_grep '提主|合并dev到main|dev 合并 main|仓库级镜像' docs/ai-instructions/experience-index.md
require_grep 'EXP-008' docs/ai-instructions/experience-index.md
require_grep 'release_commands|部分发布|#发布|默认环境' docs/ai-instructions/experience-index.md
require_grep '只同步本次特性相关能力|轻量升级提示词|不直接执行目标项目升级' docs/ai-instructions/instructions/generate-template-feature-upgrade-prompt.md
require_grep 'experience_lookup' docs/ai-instructions/instructions/generate-template-feature-upgrade-prompt.md
project_root=$(pwd -P)
project_root_matches=$(rg -nF "$project_root" --glob '!.git/**' --glob '!.local/**' . || true)
if [ -n "$project_root_matches" ]; then
  disallowed_project_root_matches=$(printf '%s\n' "$project_root_matches" | awk -F: -v root="$project_root" '
    {
      path = $1
      sub(/^\.\//, "", path)
    }
    path ~ /^prompts\/codex\/template-upgrade-prompts\/.*-prompt\.md$/ && index($0, "本机模板仓库目录：" root) > 0 { next }
    { print }
  ')
  if [ -n "$disallowed_project_root_matches" ]; then
    printf '%s\n' "$disallowed_project_root_matches" >&2
    fail "committable files must not contain this machine's project absolute path outside the allowed 本机模板仓库目录 prompt field"
  fi
fi
require_grep 'experience-index' docs/ai-instructions/instructions/create-task-prompt-project.md prompts/codex/06-codex-upgrade-template-features.md prompts/codex/05-codex-desensitize-check.md
require_grep 'solutions' docs/ai-instructions/instructions/create-task-prompt-project.md prompts/codex/06-codex-upgrade-template-features.md prompts/codex/05-codex-desensitize-check.md
require_grep 'experience_lookup' docs/ai-instructions/instructions/create-task-prompt-project.md prompts/codex/06-codex-upgrade-template-features.md prompts/codex/05-codex-desensitize-check.md
grep -Eq 'experience_lookup|experience-index|solutions' docs/ai-coding/coding-style.md docs/ai-coding/module-dossier-rules.md prompts/codex/task-packs/_template/prompts/01-task-template.md || fail "final response and task-pack templates must include experience lookup"
grep -q '.maw/modules.yaml' TEMPLATE_OVERVIEW.md .maw/codex-context.md || fail "template overview or codex context must reference .maw/modules.yaml"
grep -Eq '相对路径|project_root_relative' TEMPLATE_OVERVIEW.md .maw/policies.yaml || fail "template overview and policies must document project-relative path rules"
grep -Eq 'hit_code_components|需要更新发布|当前已发布|当前未发布' docs/ai-coding/module-dossier-rules.md .maw/codex-context.md || fail "final response must require code component and release status judgment"
grep -Eq 'release_commands|release_confirmation_prompt|#发布' docs/ai-coding/module-dossier-rules.md .maw/codex-context.md prompts/codex/task-packs/README.md || fail "final response must require release command and confirmation prompt"
require_grep 'todo_task_update_status' docs/ai-coding/module-dossier-rules.md docs/ai-coding/coding-style.md docs/ai-instructions/instructions/final-closeout-response.md docs/ai-instructions/templates/final-closeout.zh-CN.md prompts/codex/task-packs/_template/prompts/01-task-template.md
require_grep 'health_context_update_status' docs/ai-coding/module-dossier-rules.md docs/ai-coding/coding-style.md docs/ai-instructions/instructions/final-closeout-response.md docs/ai-instructions/templates/final-closeout.zh-CN.md prompts/codex/task-packs/_template/prompts/01-task-template.md prompts/codex/task-packs/_template/EXECUTE_PROMPT.md
require_grep 'require_push_after_task_segment: true' .maw/policies.yaml
require_grep '不要等用户再次要求.*提交 push|任务段.*提交并推送|子任务.*提交.*推送' RTK.md .maw/codex-context.md .maw/agent-briefing.md docs/ai-coding/coding-style.md docs/ai-coding/user-provided-rules.md docs/ai-instructions/instructions/create-task-prompt-project.md prompts/codex/task-packs/README.md prompts/codex/task-packs/_template/prompts/00-session-runbook.md prompts/codex/task-packs/template-feature-upgrade-codex-tasks/prompts/00-session-runbook.md prompts/codex/task-packs/adopt-maw-project-template-codex-tasks/prompts/00-session-runbook.md
if rg -n '如果用户要求提交推送|否则只报告待提交' docs prompts .maw RTK.md >/dev/null 2>&1; then
  fail "task closeout must require proactive commit/push, not only when the user asks"
fi
grep -Eq 'repository_mirrors|auto_sync_after_project_push' .maw/repositories.yaml docs/repository-mirror-sync-guide.md || fail "repository mirror protocol must be documented"
grep -Eq 'repository_publish_mirrors|publish-repository-mirror' .maw/repositories.yaml docs/repository-publish-mirror-guide.md || fail "repository publish mirror protocol must be documented"
grep -Eq 'component_mirrors|镜像仓库' .maw/repositories.yaml docs/component-mirror-repository-guide.md || fail "component mirror repository protocol must be documented"
grep -Eq 'overlay|同名配置|same-path' .local/README.md .local/.maw/README.md docs/configuration-guide.md || fail ".local docs must state overlay role"
grep -Eq 'maintenance|本机维护|mirror remote' .local/README.md .local/maintenance/README.md || fail ".local docs must state local maintenance role"
require_grep '本机 AI|本机.*记忆|AI 临时状态' .local/ai/README.md
require_grep 'device:' .local/device.example.yaml

bash ops/scripts/check-technical-map.sh
bash ops/scripts/check-repository-identity.sh
bash ops/scripts/check-host-purpose-mcp-alignment.sh
python3 -m py_compile ops/scripts/check-project-health-context.py
python3 -m py_compile ops/scripts/generate-uat-business-handoff.py
python3 -m unittest tests/test_generate_uat_business_handoff.py >/dev/null
require_grep 'TINST-041|#UAT交付|uat-business-handoff|TestRun/Bug/Evidence' docs/ai-instructions/README.md docs/ai-instructions/instructions/uat-business-handoff.md PROJECT_COMMANDS.md .maw/capabilities.yaml .maw/project-signals.yaml .maw-template/template.yaml docs/delivery/uat/business-handoff-standard.md
python3 ops/scripts/check-project-health-context.py --format json >/dev/null

template_mirror_target='novelworld'"/maw-project-template"
for path in .maw/repositories.yaml .maw/app-runtime.yaml .maw/components.yaml .maw/project.yaml .maw/releases.yaml release/rules.yaml docs/component-mirror-repository-guide.md; do
  if [ -f "$path" ] && grep -n "$template_mirror_target" "$path" >/dev/null 2>&1; then
    fail "template GitHub repository must not be configured as a mirror or repository target in $path"
  fi
done
for path in code/*/.maw.component.yaml; do
  [ -f "$path" ] || continue
  if grep -n "$template_mirror_target" "$path" >/dev/null 2>&1; then
    fail "template GitHub repository must not be configured as a component mirror in $path"
  fi
done

if find . -name .DS_Store -print -quit | grep -q .; then
  fail ".DS_Store files should not be committed"
fi

if find . -path './.git' -prune -o -path './.ssh/*' ! -name README.md ! -name .gitkeep -print -quit | grep -q .; then
  warn ".ssh contains files other than README.md or .gitkeep; ensure real keys are not committed"
fi

echo "OK: template module documentation checks passed"
