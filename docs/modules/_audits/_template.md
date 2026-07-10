---
doc_key: docs.modules.audits.template
doc_type: audit
stage: governance
status: template
owner: reviewer
tags:
  - modules
  - audit
  - module-map
project_health:
  dimensions:
    - product_module_design
    - ai_collaboration
  evidence_level: template
read_contract:
  summary: "模块地图审计报告模板。"
  health_signal: "用于记录模块地图评分、缺口、过期文档和整改闭环。"
  consumes:
    - .maw/modules.yaml
    - docs/modules/
  produces:
    - module_map_score
  ai_read_hint: "生成模块地图审计报告时复制本模板。"
---

# 模块地图审计报告：<范围>

## 1. 审计元信息

- audit_id:
- audit_type: init / check / audit / gap-fill / stale-cleanup / change-impact / release-gate
- checked_commit:
- commit_range:
- checked_at:
- checked_by: human / ai / reviewer
- scope_modules:
- scope_paths:
- related_app_keys:
- source_paths:
- source_commits:

## 2. module_map_score

> 分数用于暴露缺口，不用于强行补全。旧项目缺少 detail docs 默认 warning-only；发布前、高风险改造或人工审计场景可提升为阻塞项。

| 维度 | 分数/计数 | 说明 | 处理建议 |
| --- | --- | --- | --- |
| route_index_coverage |  | 页面 URL/API/命令/关键文件能通过一级索引定位到二级模块的比例 |  |
| api_owner_coverage |  | API/命令是否有明确 owner_module |  |
| detail_doc_coverage |  | 高频、复杂、正在审计页面/API 是否有 pages/backend 审计页 |  |
| traceability_coverage |  | 关键链路是否有 traceability 覆盖 |  |
| confirmed_ratio |  | confirmed 条目比例 |  |
| pending_confirm_count |  | 待确认条目数量 |  |
| stale_docs_count |  | 疑似过期文档数量 |  |
| deprecated_docs_count |  | 已废弃文档数量 |  |
| orphan_docs_count |  | 未被 `.maw/modules.yaml`、一级索引或二级模块回链的文档数量 |  |
| missing_changelog_count |  | 已发生事实变化但缺少 changelog 的数量 |  |
| ai_boundary_coverage |  | 活跃二级模块是否写清 AI 边界指引 |  |

综合结论：

- overall_status: pass / warning / blocked
- overall_reason:

## 3. 检查范围

| 对象 | 路径/模式 | 当前 doc_status | confidence | last_verified_commit | 备注 |
| --- | --- | --- | --- | --- | --- |
| root / group / leaf / route_index / page / backend / traceability |  | confirmed / inferred / pending_confirm / stale / deprecated | high / medium / low |  |  |

## 4. 发现项

| ID | 严重度 | 类型 | 位置 | 发现 | 证据 | 建议 |
| --- | --- | --- | --- | --- | --- | --- |
| MMA-001 | info / low / medium / high / critical | missing / stale / orphan / mismatch / risk / cleanup |  |  |  |  |

## 5. stale / deprecated 候选

| 文档 | 原 owner_module | 证据 | 建议状态 | 替代路径 | 是否需人工确认 |
| --- | --- | --- | --- | --- | --- |
|  |  |  | stale / deprecated / keep |  | yes / no |

## 6. pending_confirm 与人工问题

| 编号 | 问题 | 影响模块 | 需要谁确认 | 阻塞范围 | 状态 |
| --- | --- | --- | --- | --- | --- |
|  |  |  | human / reviewer / developer / product | dev / review / release / none | open / resolved |

## 7. 整改动作

| 动作 | 目标路径 | 类型 | 负责人 | 状态 | 备注 |
| --- | --- | --- | --- | --- | --- |
| create / update / mark_stale / mark_deprecated / remove / merge |  | docs / index / module / audit | human / ai / reviewer | pending / done / skipped |  |

## 8. 验证

| 验证项 | 命令/方式 | 结果 | 备注 |
| --- | --- | --- | --- |
| diff check | `git diff --check` | pending / pass / fail / skipped |  |
| module docs check | `bash ops/scripts/check-template-module-docs.sh` | pending / pass / fail / skipped |  |
| module candidates check | `bash ops/scripts/check-module-candidates.sh` | pending / pass / fail / skipped |  |

## 9. 审计结论

- 结论：
- 需立即处理：
- 可渐进补全：
- 不处理原因：
