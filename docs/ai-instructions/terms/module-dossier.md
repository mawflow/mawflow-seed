# 术语：模块档案 / module dossier

## 定义

模块档案是 `docs/modules/<module-key>/module.md` 中维护的功能模块边界文档，配合 `.maw/modules.yaml` 的机器可读索引使用。

## 包含内容

- 模块元信息、当前功能描述、实现程度和迭代计划。
- 待办、前端页面边界、后端接口边界、数据表边界。
- 配置与运行边界、任务与节点边界、文档维护规则。
- 最近变更摘要和独立 changelog。

## 使用场景

- AI/Codex 通过 `module_key`、模块名、页面路径、接口路径或数据表名缩小上下文。
- Planner 拆分 Story/Task 时指定模块、owned paths、blocked paths 和验收项。
- Reviewer 检查页面/API/DB/状态流/配置/发布变化是否同步文档。
- Release Manager 检查模块发布、脱敏和客户仓库同步边界。

## 易混淆概念

- 模块档案不是一次性提示词；一次性提示词放在 `prompts/`。
- 模块档案不是历史归档；过期资料放在 `docs/archive/`，且 AI 默认不读。
- 模块档案不是业务代码权威来源；代码和 `.maw` 当前配置仍是实现依据，档案负责记录边界和维护状态。
- 跨模块待办任务不是模块档案局部待办；被其它模块依赖、当前流程先假设已完成的缺口应记录到 `docs/planning/todos/active.md`，模块档案只回链 TODO-ID。
