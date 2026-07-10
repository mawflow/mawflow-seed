# <任务标题> 会话运行手册

## 目标

<说明本任务包最终要交付什么。>

## 基线

- 仓库根：当前会话所在项目根目录。
- 任务包：`prompts/codex/task-packs/<slug>-codex-tasks/`
- 状态文件：`docs/implementation/<topic>/<slug>-codex-tasks/SESSION_STATE.md`
- 执行模式：`same_session_auto_run`
- 输出语言：中文。
- 收口格式：中文、人类优先，技术元数据附后。
- 文档语言：任务包正文、项目文档、模块档案、component guide 和 README 补充段落默认中文；英文仅保留在代码标识、路径、命令、协议名、第三方原文、机器字段 key、品牌/专有名词或用户明确要求的英文内容中。

## 最高优先规则

- 先运行 `git status --short`，识别并保护无关改动。
- 路径使用项目根相对路径。
- 新增或改写人维护文档时使用中文标题和中文正文，不使用 `Goal`、`Baseline`、`Objective`、`Required Reads`、`Implementation Requirements`、`Acceptance Criteria` 或 `Final Response Requirements` 等英文标题。
- 如果任务涉及模块、页面、接口、数据表、配置或发布，先用 `.maw/modules.yaml` 定位模块，再按需读取模块档案。
- 每个任务开始前用任务关键词、路径、命令名、错误症状和 app_key 检索 `docs/ai-instructions/experience-index.md`；只有命中索引、候选台账或用户明确路径时才读取 `docs/ai-instructions/solutions/**` 的具体详情。
- 不全量读取 `docs/modules/**`；不把 `docs/archive/**` 作为当前依据，除非用户明确要求历史追溯。
- 不提交真实密钥、token、生产连接串、客户隐私、`.maw/*.local.yaml`、`.ssh/**` key 文件、日志或缓存。
- 每个任务结束后更新 `SESSION_STATE.md`，并判断命中的 code 组件应用与发布状态。
- 涉及对外交付 code 时，先运行 `ops/scripts/check-code-deliverable.sh`；需要导出时先运行 `ops/scripts/export-code-only.sh --dry-run`，确认后再真实导出。
- 每个产生实际改动且可独立验证的任务段完成后，必须运行相关验证、提交并推送当前分支；推送后运行仓库级 mirror 计划命令，按有效计划同步镜像；不要等用户再次要求“提交 push”。只有用户明确禁止 git 写入、没有实际变更、存在无法安全暂存的无关脏改动，或认证、网络、分支保护、远端拒绝导致无法 push 时，才可跳过，并必须记录原因。
- 提交推送时先只处理本任务实际改动；本任务提交推送后再次检查剩余工作区。剩余变动若全部在 `code/**` 之外且不属于禁提交文件，可作为独立补充提交推送；剩余 `code/**` 组件业务代码、组件运行配置或组件内文件变动不得纳入顺手推送。

## 必读文件

1. `.maw/codex-context.md`
2. `prompts/codex/task-packs/<slug>-codex-tasks/README.md`
3. `prompts/codex/task-packs/<slug>-codex-tasks/PLAN.md`
4. `prompts/codex/task-packs/<slug>-codex-tasks/manifest.json`
5. `docs/implementation/<topic>/<slug>-codex-tasks/SESSION_STATE.md`
6. `docs/ai-instructions/experience-index.md`

## SESSION_STATE 格式

```text
TOPIC_STATUS: in_progress | ready_for_staging | ready_for_production | blocked | done
CURRENT_TASK: <task-key>
NEXT_TASK: <task-key or none>
RESUME_FROM: <one sentence explaining exactly where to continue>

DONE:
- ...

CHANGED_FILES:
- ...

COMMANDS_RUN:
- ...

TESTS_RUN:
- ...

RISKS:
- ...

NEXT_TASK_CONTEXT:
- ...

COPY_READY_RESUME_PROMPT:
<copy-ready prompt>

SAME_SESSION_AUTO_RUN: true
CLI_WINDOW_HANDOFF: disabled_by_default
```

## 中断恢复协议

1. Read this runbook.
2. Read `SESSION_STATE.md`.
3. Run `git status --short`.
4. Read changed files listed in `SESSION_STATE.md` if needed.
5. Continue from `NEXT_TASK` and `RESUME_FROM`.
6. Do not revert unrelated changes.

## 任务列表

| 顺序 | 文件 | 目标 |
| --- | --- | --- |
| 01 | `prompts/01-task-template.md` | <替换为第一个实际任务> |

## 开始

从 `prompts/01-task-template.md` 开始。完成后更新 `SESSION_STATE.md`；如果本任务产生实际改动，先按仓库规则验证、提交并推送当前分支，推送后运行仓库级 mirror 计划命令并按有效计划同步镜像；如果 `NEXT_TASK` 不是 `none` 且没有阻塞，在同一会话继续下一任务。
