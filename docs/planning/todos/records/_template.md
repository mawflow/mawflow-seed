---
doc_key: docs.planning.todos.records.template
doc_type: governance
stage: planning
status: active
owner: planner
tags:
  - todos
  - template
project_health:
  dimensions:
    - task_execution
  evidence_level: canonical
read_contract:
  summary: "待办任务详情模板。"
  health_signal: "用于保持新建 TODO 详情记录的字段和读写口径一致。"
  consumes: []
  produces: []
  ai_read_hint: "新增待办详情模板或维护待办治理规则时读取。"
---

# TODO-YYYYMMDD-<short-slug>：<待办标题>

## 基本信息

- TODO-ID:
- 状态: assumed_done / open / in_progress / ready_for_integration
- 类型: deferred_dependency / assumed_done / integration_gap / external_system_gap / data_gap / release_gap
- 主模块:
- 受影响模块:
- 负责人/来源:
- 创建日期:
- 最近更新:

## 当前假设

说明当前业务闭环先把什么能力当成已经完成。写清楚哪些页面、接口、数据、权限、状态、任务或发布流程正在依赖这个假设。

## 暂不实现原因

说明为什么本轮先不做，例如业务闭环优先、外部系统未准备、数据未到位、接口契约未确认、风险需要人工审批等。

## 影响范围

| 类型 | 路径或对象 | 影响说明 |
| --- | --- | --- |
| 页面/组件 |  |  |
| 接口/命令 |  |  |
| 数据表/字段 |  |  |
| 配置/环境 |  |  |
| 测试/验收 |  |  |
| 发布/交付 |  |  |

## 完成待办时需要处理

-

## 取消待办时需要处理

-

## 联调建议

| 模块 | 联调内容 | 建议验证方式 | 阻塞项 |
| --- | --- | --- | --- |
|  |  |  |  |

## 证据

- 需求/设计：
- 模块档案：
- 代码/配置：
- 任务/提交：

## 更新记录

| 日期 | 更新人/角色 | 变更 | 影响 |
| --- | --- | --- | --- |
|  |  |  |  |
