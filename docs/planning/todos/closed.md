---
doc_key: docs.planning.todos.closed
doc_type: task_plan
stage: planning
status: active
owner: planner
tags:
  - todos
  - closed
project_health:
  dimensions:
    - task_execution
  evidence_level: canonical
read_contract:
  summary: "已关闭待办任务台账。"
  health_signal: "用于项目健康追溯待办完成、取消或关闭原因。"
  consumes: []
  produces: []
  ai_read_hint: "需要追溯已完成、取消或关闭的待办时读取。"
---

# 已关闭待办任务台账

本文件归档已完成、已取消、已废弃或被替代的待办任务。关闭记录必须保留影响说明和联调/回归建议，方便后续追溯为什么当时完成、取消或改用替代方案。

| TODO-ID | 关闭状态 | 原状态 | 类型 | 原当前假设 | 主模块 | 受影响模块 | 关闭原因 | 完成/取消后的影响处理 | 联调或回归建议 | 证据 | 关闭日期 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

## 维护规则

- `completed`：写清真实实现、移除的假设、已联调或建议联调的模块。
- `cancelled`：写清不做原因、替代方案和受影响模块如何撤销依赖。
- `superseded`：写清替代 TODO-ID、Story/Task 或设计方案。
- 关闭后如果发现仍有模块依赖旧假设，应重新打开原 TODO 或新增后续 TODO，并在本文件回链。
