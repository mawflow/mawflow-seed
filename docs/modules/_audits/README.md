---
doc_key: docs.modules.audits.index
doc_type: audit
stage: governance
status: active
owner: reviewer
tags:
  - modules
  - audit
  - module-map
project_health:
  dimensions:
    - product_module_design
    - ai_collaboration
  evidence_level: canonical
read_contract:
  summary: "模块地图定期审计报告目录。"
  health_signal: "用于记录 #模块地图 检查、审计、查漏补缺和清理过期文档的结果。"
  consumes:
    - .maw/modules.yaml
    - docs/modules/
  produces:
    - module_map_score
  ai_read_hint: "执行 #模块地图：检查、审计、清理过期或发布前检查后，按需写入本目录报告。"
---

# 模块地图审计报告

本目录保存 `#模块地图` 的阶段性检查报告，服务人工复核、AI 边界指引和长期治理。报告不是模块事实源；模块事实仍在 `.maw/modules.yaml`、一级模块 `route-api-index.md`、二级模块 `module.md`、`pages/`、`backend/` 和 `traceability.md`。

推荐命名：

```text
YYYYMMDD-module-map-audit.md
YYYYMMDD-<module-key>-module-map-audit.md
```

使用规则：

- `#模块地图：检查` 只输出短检查表时可不落报告；发现结构性缺口、过期文档、迁移建议或发布前风险时应落报告。
- `#模块地图：审计 <module_key>`、`#模块地图：清理过期`、`#模块地图：变更影响 <commit_range>` 和 `#模块地图：发布前检查` 默认应落报告或更新最近报告。
- 报告必须记录 `checked_commit` 或 `commit_range`，并列出 `module_map_score`，避免后续 AI 把旧审计结论当成当前事实。
- 发现事实变更时，报告只做审计证据；仍要同步更新对应模块档案、一级索引、detail docs 或 `.maw/modules.yaml`。
- 删除或合并过期模块文档前，先在报告中列出候选、证据、替代文档和人工确认状态。

模板：[_template.md](_template.md)
