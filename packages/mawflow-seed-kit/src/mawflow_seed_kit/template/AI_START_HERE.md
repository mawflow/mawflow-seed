# __PROJECT_NAME__ · AI Start Here

本项目采用 MAWflow Seed Contract v2 与通用 Agent 协议。Codex、Claude Code、Gemini CLI、Cursor 和其它 Agent 共享同一份项目事实。

1. 读取 `.maw/agent-entry.yaml` 与 `.maw/agent-context.md`。
2. 读取 `.maw/agent-rules.yaml`、`.maw/project.yaml`、`.maw/components.yaml`、`.maw/modules.yaml`。
3. 定位当前模块，按 `.maw/agent-entry.yaml` 的 task_routes 读取必要文档。
4. 修改前确认允许路径、禁止路径、验证命令与已有授权。

`.maw/**` 是共享事实，`.local/**` 是本机私有数据。不要将凭据、本机绑定或无关改动带入提交。
CLI、MCP、Skill 和 RTK 均可选；无工具集成时仍能直接读取本入口。静态入口检查不等于真实 Agent 已加载或完成任务。

结束时说明变更、验证、未验证项、风险和发布影响。跨 Agent 接力使用 `CHATGPT_TO_AI.md`。

## 选择 Agent 入口

[Codex / Cursor](AGENTS.md) · [Claude Code](CLAUDE.md) · [Gemini CLI](GEMINI.md) · [ChatGPT Web / GitHub 源码阅读](CHATGPT.md) · [通用入口](AI_START_HERE.md)。无法识别 Agent 时使用通用入口。网页 Agent 由用户显式提供入口链接与仓库目标分支或提交。
