---
doc_key: docs.modules.template.traceability
doc_type: module_design
stage: design
status: active
owner: planner
tags:
  - modules
  - template
  - traceability
project_health:
  dimensions:
    - product_module_design
  evidence_level: canonical
read_contract:
  summary: "二级模块页面/API/代码/数据/测试追踪矩阵模板。"
  health_signal: "用于人工和 AI 对照模块内页面、API、后端文件、数据对象、测试和验收闭环。"
  consumes: []
  produces: []
  ai_read_hint: "模块需要审计端到端链路、排查口径漂移或确认跨页面/API 影响时读取。"
---

# 追踪矩阵：<二级模块名称>

> 本文件放在 `docs/modules/<一级模块>/<二级模块>/traceability.md`。它把页面、API、后端文件、数据对象、测试和验收串起来，服务人工审计和 AI 最小上下文定位；不替代 `module.md`。

## 1. 总览

- 所属一级模块：
- 所属二级模块 / module_key：
- 一级模块 URL/API 索引：
- doc_status：confirmed / inferred / pending_confirm / stale / deprecated
- confidence：high / medium / low
- last_verified_commit：
- last_verified_at：
- last_verified_by：human / ai / reviewer
- source_paths：
- source_commits：
- last_audit_id：

## 2. 页面到 API

| 页面 | 页面审计页 | API/命令 | 后端审计页 | 交互/触发 | 状态 |
| --- | --- | --- | --- | --- | --- |
|  | `pages/<page-key>.md` |  | `backend/<api-group-or-file>.md` |  | confirmed / inferred / pending_confirm |

## 3. API 到代码与数据

| API/命令 | 后端文件 | 服务/函数 | 数据表/集合/模型 | 读写职责 | 状态 |
| --- | --- | --- | --- | --- | --- |
|  |  |  |  | read / write / read_write | confirmed / inferred / pending_confirm |

## 4. 状态流与副作用

| 触发点 | 初始状态 | 目标状态 | 副作用 | 回滚/补偿 | 风险 |
| --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |

## 5. 测试与验收覆盖

| 链路 | 测试路径/命令 | 验收点 | 当前状态 | 缺口 |
| --- | --- | --- | --- | --- |
|  |  |  | pending / covered / blocked |  |

## 6. 跨模块影响

| 外部模块 | 关系 | owner/consumer | 影响 | 回归建议 |
| --- | --- | --- | --- | --- |
|  |  | owner / consumer / shared |  |  |

## 7. 待确认项

| 编号 | 问题 | 影响 | 建议确认对象 | 状态 |
| --- | --- | --- | --- | --- |
|  |  |  |  | open / resolved |

## 8. 生命周期与过期处理

- stale_reason：
- deprecated_by：
- superseded_by：
- 清理建议：保留 / 合并 / 删除 / 待人工确认
- 下次复核触发：页面/API/后端文件/数据对象/测试变化 / 发布前检查 / 定期 `#模块地图：检查`
