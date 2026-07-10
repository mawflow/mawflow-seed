---
doc_key: docs.planning.todos.records.index
doc_type: governance
stage: planning
status: active
owner: planner
tags:
  - todos
  - records
project_health:
  dimensions:
    - task_execution
  evidence_level: canonical
read_contract:
  summary: "待办任务详情记录目录入口。"
  health_signal: "用于项目健康定位单个 TODO-ID 的详情文档。"
  consumes: []
  produces: []
  ai_read_hint: "需要查看待办详情、影响面或联调建议时读取。"
---

# 待办任务详情记录

本目录用于保存高风险或跨模块复杂待办的详情页。普通待办只写入 `../active.md` 即可。

建议创建详情页的情况：

- 影响多个 app_key、多个模块或跨前后端联调。
- 涉及数据库、支付、权限、生产数据、客户仓同步、发布或不可逆迁移。
- 当前假设较复杂，单行台账难以说清完成/取消影响。
- 需要长期跟踪联调结论、验收证据或替代方案。

详情页文件名：

```text
TODO-YYYYMMDD-<short-slug>.md
```
