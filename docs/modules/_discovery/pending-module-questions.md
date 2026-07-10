---
doc_key: docs.modules.discovery.pending-questions
doc_type: module_design
stage: discovery
status: active
owner: planner
tags:
  - modules
  - questions
project_health:
  dimensions:
    - product_module_design
  evidence_level: canonical
read_contract:
  summary: "模块待确认问题清单。"
  health_signal: "用于项目健康判断模块拆分或归属卡点。"
  consumes: []
  produces: []
  ai_read_hint: "模块归属、边界或证据不足需要澄清时读取。"
---

# 模块待确认问题

本文件记录候选模块提升为正式模块前仍需确认的问题。

| 编号 | module_candidate | 问题 | 影响 | 建议确认对象 | 状态 |
| --- | --- | --- | --- | --- | --- |
|  |  |  |  | 用户 / 产品 / 技术负责人 / Reviewer | open / answered / deferred |
| Q-20260615-001 | template-secret-governance | 模板敏感配置治理是否应提升为正式 cross-cutting leaf module，还是长期只作为候选能力记录？ | 影响是否创建正式 `docs/modules/<module>/module.md` 与 changelog，以及后续任务的 `module_key` 收口口径。 | 用户 / Reviewer | open |

## 使用规则

- 无法确认正式 `module_key` 时，最终说明应引用这里的待确认问题或新增一条问题。
- 如果问题答案会改变页面/API/数据表、app_key、发布或交付边界，应在答案明确后同步模块候选、正式模块档案和 changelog。
- 已回答的问题可以保留在表中，状态改为 `answered`，并在相关模块档案中沉淀结论。
