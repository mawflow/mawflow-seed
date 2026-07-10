# 01｜<任务名称>

## 目标

<说明本任务要完成的可验证目标。>

## 必读文件

- `.maw/codex-context.md`
- `docs/ai-instructions/experience-index.md`
- `prompts/codex/task-packs/<slug>-codex-tasks/PLAN.md`
- <按任务补充最小必要文件>

## 实现要求

- <要求 1>
- <要求 2>
- 新增或改写人维护项目文档时使用中文标题和中文正文；英文仅保留在代码标识、路径、命令、协议名、第三方原文、机器字段 key、品牌/专有名词或用户明确要求的英文内容中。
- 如涉及模块、配置或发布边界，更新对应模块档案或说明无需更新原因。
- 执行前检索经验索引；只有命中索引、候选台账或用户明确路径时才读取 `docs/ai-instructions/solutions/**` 的具体详情。
- 保持路径为项目根相对路径。

## 建议命令

```bash
git status --short
```

## 验收标准

- <验收点 1>
- <验收点 2>
- 新增或改写的任务包正文、项目文档、模块档案、component guide 和 README 补充段落默认中文；未使用 `Objective`、`Required Reads`、`Implementation Requirements`、`Acceptance Criteria`、`Final Response Requirements`、`Component Guide`、`Scope`、`Build Notes`、`Sensitive Config` 等英文标题。
- `SESSION_STATE.md` 已更新到下一任务或 `NEXT_TASK: none`。
- 如果本任务产生实际改动，当前分支已按仓库规则提交并推送；无法推送时已记录失败原因、当前 commit hash 或未提交状态，以及需要人工处理的下一步。

## 最终说明要求

最终说明必须包含：

```text
experience_lookup:
  checked: yes/no
  matched:
    - <EXP-XXX 或 none>
  detail_read:
    - <路径或 none>
  updated:
    - <路径或 none>
module_key: <涉及模块或 not_identified>
module_dossier_updated: yes/no/not_required
module_dossier_reason: <原因>
updated_module_docs:
  - <路径或 none>
hit_code_components:
  - <component>/<app_key 或 none>
seed_repository_upgrade_suggestions:
  - <未发现新的种子仓库升级建议；或已记录到 docs/seed-repository-upgrade-candidates.md，并说明使用场景、理由和兼容性要求>
release_update_status:
  - <本轮修改了 <app_key> 的 <代码/运行配置/发布覆盖/部署脚本/线上可见行为>，需要发布 <app_key> 才会生效，当前已发布/当前未发布/当前未发布或未验证；或未命中 code 组件应用，无需更新发布>
release_commands:
  - <app_key>: <按配置列出 #发布：发布 <app_key>（默认 <env>）、#发布：发布 <app_key> 到 <env_option> 以及可用中文口令 #发布测试/#发布上线/#发布生产/#发布生成；多个 app_key 分别列出，用户可复制其中一条或多条；或 none>
release_confirmation_prompt:
  - <本轮需要发布 <app_key 列表> 才会生效。是否全部发布？回复“是”将发布全部；如只发布部分，请复制上方对应组件的 #发布 指令；或 none>
todo_task_update_status:
  - <新增/完成/取消/查询了哪些 TODO-ID；或未涉及被依赖但暂不实现的待办任务>
health_context_update_status:
  - <新增/更新/审计/未涉及哪些 .maw/health 记录 ID；是否需要把健康问题、事实、决策、审计缺口或验收缺口沉淀到项目健康上下文>
repository_identity_update_status:
  - <新增/更新/判断/未涉及 declared roles、detected roles、角色目录覆盖和高风险约束>
```
