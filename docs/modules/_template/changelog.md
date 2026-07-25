---
doc_key: docs.modules.template.changelog
doc_type: governance
stage: design
status: active
owner: planner
tags:
  - modules
  - template
  - changelog
project_health:
  dimensions:
    - product_module_design
  evidence_level: canonical
read_contract:
  summary: "集中模块变更日志模板。"
  health_signal: "用于保持 docs/changelogs/<module_key>.md 与模块索引同步。"
  consumes: []
  produces: []
  ai_read_hint: "维护模块 changelog 模板时读取。"
---

# 模块变更日志：<模块名称>

> 从本模板生成到 `docs/changelogs/<module_key>.md`，不要放入 `docs/modules/<...>/`。模块档案只保留 `changelog_path` 与 `changelog_time`。

## 1.0 基线历史

| 日期 | 版本/提交 | 来源任务 | 变更类型 | 摘要 | doc_status | 文档同步 |
| --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  | confirmed / inferred / pending_confirm / stale / deprecated |  |

变更类型建议：`feature` / `fix` / `refactor` / `api` / `db` / `ui` / `config` / `release` / `docs` / `security` / `deprecate`。

## 2.0

只记录产品/领域边界、API 或数据兼容、状态机、权限、安全、迁移、发布/回滚语义及模块生命周期变化。
