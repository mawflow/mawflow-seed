# 指令：渐进式模块发现

## 元信息

- ID：TINST-021
- 类型：项目指令
- 状态：启用
- 维护位置：`docs/ai-instructions/instructions/progressive-module-discovery.md`
- 触发词：#模块发现、渐进式模块发现、候选模块、module_candidate、模块证据、证据不足、不确定 module_key
- 适用范围：新项目、模板化改造、模块树证据不足、无法确认正式 `module_key`、需要先记录候选模块而不是创建正式 leaf 的场景。

## 目标

让 AI 在模块证据不足时先建立候选模块和证据闭环，避免把 `server/client`、大业务域、一次性任务标题或缺少证据的节点强行写成正式模块档案。

## 执行步骤

1. 读取 `.maw/modules.yaml`、`.maw/module-candidates.yaml`、`docs/modules/README.md` 和 `docs/modules/_discovery/README.md`。
2. 从用户描述、需求、页面/API/数据表、代码路径、发布边界或任务历史中提取候选节点。
3. 为候选节点记录：
   - key/name/aliases
   - status：`seed`、`candidate`、`provisional`、`confirmed` 或 `deprecated`
   - confidence：`low`、`medium` 或 `high`
   - evidence
   - app_keys
   - known_boundaries
   - open_questions
   - promotion_criteria
4. 证据不足时，只更新 `.maw/module-candidates.yaml` 和 `docs/modules/_discovery/`，不创建正式 leaf `module.md`。
5. 候选达到用户确认、稳定业务边界、页面/API/数据/任务证据和复核记录后，再按 `TINST-010` 提升为正式模块树或 leaf。
6. 收口时若仍无法确定正式 `module_key`，输出 `module_candidate`、不更新模块档案原因和下一步确认问题。
7. 运行 `ops/scripts/check-module-candidates.sh` 做轻量结构检查。

## 与模块树拆分的关系

- `TINST-010` 负责模块树拆分和正式模块档案生成。
- 本指令负责证据不足时的候选记录和提升条件。
- 候选树可以先进入 `.maw/module-candidates.yaml`，正式、稳定、可验证的 leaf 才进入 `.maw/modules.yaml`。

## 验证方式

- `.maw/module-candidates.yaml` 可解析。
- `docs/modules/_discovery/` 必需文件存在。
- 候选模块若存在，至少包含 key/name/status/evidence/open_questions。
- `.maw/modules.yaml` 中没有把 `seed` 候选误写为 confirmed leaf。

## 禁区

- 不得把证据不足的候选模块直接创建成正式 leaf。
- 不得为了完成任务而编造页面、接口、表、权限、状态流或发布目标。
- 不得把 `server`、`client` 等端工程长期当作唯一业务 leaf。
- 不得全量读取 `docs/modules/**` 或 `code/**` 来“找灵感”。
