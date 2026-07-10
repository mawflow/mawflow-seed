# <任务标题> 任务提示词工程

## 目标

<用一两段说明这个任务包要完成的最终结果、涉及的业务边界和验收目标。>

## 入口

本 README 面向人阅读：先告诉用户复制什么、会做什么、不会做什么，以及完成后能看到哪些验证、Git、发布和交付结果。真正复制给 Codex 的入口是 `EXECUTE_PROMPT.md`。

请先打开 `EXECUTE_PROMPT.md`，复制其中的提示词到 Codex 执行。

也可以使用下面的简化入口：

```text
读取并执行 prompts/codex/task-packs/<slug>-codex-tasks/prompts/00-session-runbook.md
```

## 中断与恢复

如果会话中断，下一次继续时：

1. 读取 `prompts/codex/task-packs/<slug>-codex-tasks/prompts/00-session-runbook.md`。
2. 读取 `docs/implementation/<topic>/<slug>-codex-tasks/SESSION_STATE.md`。
3. 运行 `git status --short`。
4. 从 `NEXT_TASK` 和 `RESUME_FROM` 继续，不要从头重做，不要回滚无关改动。

## 任务列表

| 顺序 | 文件 | 目标 |
| --- | --- | --- |
| 01 | `prompts/01-task-template.md` | <替换为第一个实际任务> |

## 全局原则

- 路径使用项目根相对路径。
- 创建实际任务包时，必须把 `EXECUTE_PROMPT.md` 中的 `<slug>`、`<topic>`、状态文件路径和任务文件名替换为真实值。
- `manifest.json` 默认包含 `language: zh-CN`、`documentation_language: zh-CN`、`audience: human_and_codex`、`closeout_profile: zh_cn_human_first` 和 `delivery_mode: code_only`；如任务不适用 code-only，应在任务包中写明原因。
- 任务包 README、runbook、子任务正文和任务执行中新增或改写的项目文档默认使用中文标题和中文正文；英文仅保留在代码标识、路径、命令、协议名、第三方原文、机器字段 key、品牌/专有名词或用户明确要求的英文内容中。
- 按需读取 `.maw/modules.yaml` 和模块档案，不全量读取 `docs/modules/**`。
- 每个任务开始前检索 `docs/ai-instructions/experience-index.md`；只有命中索引、候选台账或用户明确路径时才读取 `solutions/**` 详情。
- 每个任务完成后更新独占 `SESSION_STATE.md`。
- 每个任务都要说明模块档案、关键词经验、命中 code 组件、发布状态和 code 交付影响。
- 最终说明采用中文、人类优先主展示；`snake_case` 技术字段只放在末尾技术元数据中。
- 不写真实密钥、token、生产连接串、客户隐私或未脱敏日志。
