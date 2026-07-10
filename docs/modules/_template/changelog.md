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
  summary: "模块变更日志模板。"
  health_signal: "用于保持模块 changelog 字段和文档同步口径一致。"
  consumes: []
  produces: []
  ai_read_hint: "维护模块 changelog 模板时读取。"
---

# 模块变更日志：<模块名称>

| 日期 | 版本/提交 | 来源任务 | 变更类型 | 摘要 | doc_status | 文档同步 |
| --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  | confirmed / inferred / pending_confirm / stale / deprecated |  |

变更类型建议：`feature` / `fix` / `refactor` / `api` / `db` / `ui` / `config` / `release` / `docs` / `security` / `deprecate`。
