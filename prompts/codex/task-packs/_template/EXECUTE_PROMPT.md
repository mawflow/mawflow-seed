# 执行本任务提示词

把下面提示词复制到 Codex，会在当前项目仓库中执行本任务提示词工程。

```text
执行任务提示词工程：prompts/codex/task-packs/<slug>-codex-tasks
目标项目仓库：当前 Codex 会话所在仓库
执行模式：same_session_auto_run
任务状态文件：docs/implementation/<topic>/<slug>-codex-tasks/SESSION_STATE.md
输出语言：中文
收口格式：中文、人类优先，技术元数据附后
文档语言：任务包正文、项目文档、模块档案、component guide 和 README 补充段落默认中文；英文仅保留在代码标识、路径、命令、协议名、第三方原文、机器字段 key、品牌/专有名词或用户明确要求的英文内容中

执行要求：
1. 先读取 `prompts/codex/task-packs/<slug>-codex-tasks/prompts/00-session-runbook.md`、`README.md`、`PLAN.md`、`manifest.json` 和任务状态文件；如果状态文件不存在，从任务 01 开始并创建。
2. 执行前运行 `git status --short`，识别并保护无关改动，不要回滚用户或其它任务留下的变更。
3. 从 `NEXT_TASK` 和 `RESUME_FROM` 继续；如果没有状态文件，从 `prompts/01-task-template.md` 开始。
4. 新增或改写人维护项目文档时使用中文标题和中文正文；不要使用 `Objective`、`Required Reads`、`Implementation Requirements`、`Acceptance Criteria`、`Final Response Requirements`、`Component Guide`、`Scope`、`Build Notes`、`Sensitive Config` 等英文标题。
5. 每完成一个子任务，运行相关验证，更新 `SESSION_STATE.md`，记录 `DONE`、`CHANGED_FILES`、`COMMANDS_RUN`、`TESTS_RUN`、`RISKS` 和下一步。
6. 如果该子任务产生实际改动，按仓库规则提交并推送当前分支；推送后运行仓库级 mirror 计划命令，按有效计划同步镜像；无法 push 或无法执行 mirror 计划时写清失败原因、当前 commit hash 或未提交状态，以及需要人工处理的下一步。
7. 提交推送时先只处理本子任务实际改动；推送后若还有 `code/**` 之外且非禁提交范围的无关变动，可用独立中文 commit message 做补充提交并推送；剩余 `code/**` 组件业务代码、组件运行配置或组件内文件变动不得纳入顺手推送。
8. 在没有阻塞、上下文安全且用户未打断时，继续执行下一任务，直到 `NEXT_TASK: none`。

最终说明必须包含：
- 本次执行到哪个任务
- 是否更新 `SESSION_STATE.md`
- 运行了哪些验证
- 是否已提交、推送并按开关同步镜像
- code 交付影响；如需要交付 code-only，先运行 `ops/scripts/check-code-deliverable.sh`，再按需要运行 `ops/scripts/export-code-only.sh --dry-run`
- experience_lookup
- module_key
- module_dossier_updated
- module_dossier_reason
- updated_module_docs
- hit_code_components
- todo_task_update_status
- health_context_update_status
- repository_identity_update_status
- seed_repository_upgrade_suggestions
- release_update_status
- release_commands
- release_confirmation_prompt
```

创建实际任务包时，必须把 `<slug>`、`<topic>`、任务文件名和状态文件路径替换为真实值；不要把本模板文件原样作为实际任务包入口交付。
