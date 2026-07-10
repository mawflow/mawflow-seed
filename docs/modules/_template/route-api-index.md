---
doc_key: docs.modules.template.route-api-index
doc_type: governance
stage: design
status: active
owner: planner
tags:
  - modules
  - template
  - route-api-index
project_health:
  dimensions:
    - product_module_design
  evidence_level: canonical
read_contract:
  summary: "一级模块 URL/API 快速定位索引模板。"
  health_signal: "用于从页面 URL、API、命令或关键文件快速定位到二级模块。"
  consumes: []
  produces: []
  ai_read_hint: "只知道 URL、API、命令或文件路径，需要定位二级模块时读取。"
---

# URL/API 定位索引：<一级模块名称>

> 本文件放在 `docs/modules/<一级模块>/route-api-index.md`。它只做轻量定位索引：把页面 URL、API、命令或关键文件映射到二级模块。字段、按钮、入参出参、状态流、权限、错误码和测试细节不要写在这里，应写入二级模块 `module.md`、`pages/`、`backend/` 或 `traceability.md`。

## 维护规则

- `owner_module` 写真正负责该页面/API/命令的二级模块。
- `consumer_modules` 写调用、依赖或受影响的二级模块；不要因为被调用就改 owner。
- 证据不足时 `doc_status` 写 `pending_confirm`，并在备注里写待确认问题。
- 每次更新索引时记录 `last_verified_commit`、`source_paths` 和 `confidence`；无法和当前代码对齐时不要写 confirmed。
- 定期 `#模块地图：检查` 发现路径消失、owner 迁移或页面/API 下线时，先标记 `stale`，确认废弃后标记 `deprecated` 并回链替代模块或审计报告。
- 动态路由、通配 API 和前缀匹配要写清模式，例如 `/orders/:id`、`/api/orders/**`。
- 路径归属变化时，同步更新本文件、二级模块 `module.md`、相关审计页和 `.maw/modules.yaml`。

## 索引证据

- doc_status: confirmed / inferred / pending_confirm / stale / deprecated
- confidence: high / medium / low
- last_verified_commit:
- last_verified_at:
- source_paths:
- last_audit_id:

## 页面 URL 索引

| URL/路由模式 | 页面名称 | owner_module | consumer_modules | 详情文档 | 源码路径 | doc_status | confidence | last_verified_commit | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  | `docs/modules/<一级模块>/<二级模块>/pages/<page-key>.md` / none |  | confirmed / inferred / pending_confirm / stale / deprecated | high / medium / low |  |  |

## API/命令索引

| API/命令模式 | 名称 | owner_module | consumer_modules | 详情文档 | 源码路径 | doc_status | confidence | last_verified_commit | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  | `docs/modules/<一级模块>/<二级模块>/backend/<api-group-or-file>.md` / none |  | confirmed / inferred / pending_confirm / stale / deprecated | high / medium / low |  |  |

## 关键文件索引

| 文件或目录 | 类型 | owner_module | consumer_modules | 详情文档 | doc_status | confidence | last_verified_commit | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | frontend / backend / model / config / test / release |  |  |  | confirmed / inferred / pending_confirm / stale / deprecated | high / medium / low |  |  |

## 待确认项

| 编号 | 问题 | 影响 | 建议确认对象 | 状态 |
| --- | --- | --- | --- | --- |
|  |  |  |  | open / resolved |
