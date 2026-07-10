---
doc_key: docs.modules.discovery.evidence
doc_type: module_design
stage: discovery
status: active
owner: planner
tags:
  - modules
  - evidence
project_health:
  dimensions:
    - product_module_design
  evidence_level: canonical
read_contract:
  summary: "模块发现证据清单。"
  health_signal: "用于项目健康判断模块拆分证据是否足够。"
  consumes: []
  produces: []
  ai_read_hint: "评估候选模块是否可升级为正式模块时读取。"
---

# 模块证据表

候选模块进入正式模块树前，应保留足够证据，方便人工和后续 AI 复核。

| 日期 | module_candidate | 证据类型 | 证据摘要 | 来源路径或来源说明 | 置信度 | 复核人/来源 |
| --- | --- | --- | --- | --- | --- | --- |
|  |  | user_statement / requirement / page_path / api_path / table_name / code_path / task_history / release_boundary |  |  | low / medium / high |  |
| 2026-06-15 | template-secret-governance | user_statement | 用户要求当前仓库作为 `maw-project-template` 种子仓完成敏感配置治理第一阶段模板协议升级。 | 当前会话用户输入 | high | user |
| 2026-06-15 | template-secret-governance | task_history | 任务包将该能力定义为模板协议、示例、Git 凭证脚本、文档和派生项目升级资产，不实现主仓服务。 | prompts/codex/task-packs/maw-secret-governance-template-phase1-codex-tasks/PLAN.md | medium | task-pack |

## 证据使用规则

- 用户明确命名和边界说明优先级最高，但仍需与当前代码、`.maw` 配置和 active 文档交叉验证。
- 页面、API、数据表、配置和发布边界能提升置信度。
- 一次性任务标题只能作为弱证据，不能单独支撑 confirmed leaf。
- 历史归档和旧方案只能作为参考，不作为当前事实来源。
