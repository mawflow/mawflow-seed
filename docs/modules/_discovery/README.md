---
doc_key: docs.modules.discovery.index
doc_type: governance
stage: discovery
status: active
owner: planner
tags:
  - modules
  - discovery
project_health:
  dimensions:
    - product_module_design
  evidence_level: canonical
read_contract:
  summary: "渐进式模块发现目录入口。"
  health_signal: "用于项目健康判断候选模块、证据和待确认问题是否有记录。"
  consumes: []
  produces: []
  ai_read_hint: "证据不足、无法确认正式 module_key 或重建模块树时读取。"
---

# 模块发现区

本目录用于新项目或证据不足场景下的渐进式模块发现。它不是正式模块档案目录；正式模块仍以 `.maw/modules.yaml` 和 `docs/modules/<...>/module.md` 为准。

## 使用原则

- 先记录候选模块、证据和待确认问题，再决定是否生成正式 leaf。
- 证据不足时，不把 `seed` 或 `candidate` 直接写入 `.maw/modules.yaml` 作为 confirmed leaf。
- 只有达到用户确认、稳定业务边界、页面/API/数据/任务证据和复核记录等提升条件后，才把候选提升到 `.maw/modules.yaml`。
- 如果任务收口无法确定正式 `module_key`，最终说明应输出 `module_candidate` 和不更新模块档案原因。

## 文件职责

- `.maw/module-candidates.yaml`：机器可读候选模块索引。
- `module-candidates.md`：人工可读候选模块台账。
- `module-evidence.md`：候选模块证据表，记录来源和置信度。
- `pending-module-questions.md`：模块边界待确认问题。

## 推荐流程

1. 从用户描述、需求、页面/API/表、代码路径或任务历史提取候选节点。
2. 记录候选名称、别名、状态、置信度、证据、关联 app_key、已知边界和待确认问题。
3. 通过 `ops/scripts/check-module-candidates.sh` 做轻量结构检查。
4. 候选达到提升条件后，再更新 `.maw/modules.yaml` 和正式模块档案。
