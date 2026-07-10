---
doc_key: docs.planning.todos.active
doc_type: task_plan
stage: planning
status: active
owner: planner
tags:
  - todos
  - active
project_health:
  dimensions:
    - task_execution
  evidence_level: canonical
read_contract:
  summary: "当前 active 待办任务台账。"
  health_signal: "用于项目健康判断当前被依赖但暂不实现的缺口。"
  consumes: []
  produces: []
  ai_read_hint: "任务依赖暂未实现能力、假设已完成或查询当前待办时读取。"
---

# 当前待办任务台账

本文件记录当前仍未完成、被依赖、被假设已完成的待办任务。新增、完成、取消或查询待办时，优先使用 `#待办任务` / `#T028` 入口。

| TODO-ID | 状态 | 类型 | 当前假设 | 暂不实现原因 | 主模块 | 受影响模块 | 影响路径 | 完成后联调建议 | 取消影响 | 证据 | 负责人/来源 | 最近更新 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

## 维护规则

- 不要删除已完成或取消的记录；移入 `closed.md`。
- 不要在多个模块档案中复制完整待办事实；模块档案只回链 TODO-ID。
- 如果无法确认主模块，先写 `module_candidate:<名称>`，并同步判断是否需要走 `#模块发现`。
- 如果待办影响支付、权限、生产数据、客户仓同步、发布或不可逆迁移，创建 `records/TODO-YYYYMMDD-<short-slug>.md` 详情页。
