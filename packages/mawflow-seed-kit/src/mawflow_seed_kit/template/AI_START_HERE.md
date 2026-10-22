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

[Codex / WorkBuddy / Cursor](AGENTS.md) · [Claude Code](CLAUDE.md) · [Gemini CLI](GEMINI.md) · [ChatGPT Web / GitHub 源码阅读](CHATGPT.md) · [通用入口](AI_START_HERE.md)。无法识别 Agent 时使用通用入口。网页 Agent 由用户显式提供入口链接与仓库目标分支或提交。

只读任务不发起文件写入，包括客户端工作区记忆（如 `.workbuddy/memory/`）、用户级记忆、临时文件和来源记录；修改任务的这些写入也必须属于 owned_paths。客户端内建流程和 Git 忽略规则不扩大授权；存在强制写入冲突时如实报告，交由控制侧处理，不把越界记忆算成“任务外自动行为”。

## 版本来源与有界读取

核对派生项目的具体 Seed 版本时，按需读取 `.maw/seed.lock` 和 `.maw/template-source.yaml`；Contract 版本、已应用 Seed/Kit 版本和当前工具安装版本分别说明。只读现有文件，缺失则标记未配置，不扫描私有来源或更改锁文件。源 Seed 仓自己的候选版本以 `TEMPLATE_VERSION` 与实际 Git 提交为准。

全仓递归 Glob 也属于全仓搜索；从已知入口沿明确路径读取，工具输出截断时补读必要部分。WorkBuddy 桌面对话可沿 `AGENTS.md` 进入本页；未自动加载时手动指向本页即可，CLI、MCP 和专用 Skill 不作为文件对话前置条件。

## 文档来源积累

产生长期结论或缺口时按 [交互来源收录规范](docs/ai-coding/document-source-capture.md)记录最小来源与回执；只读任务不写入。

- 本地开发开工、恢复与重任务前后按 `docs/ai-coding/development-resources.md` 检查资源和工作台/CLI；按需复用服务，跨项目重任务串行，通信失败回退项目文件。

- [六阶段规范导航](docs/standards/README.md)：按项目适用条件、任务范围与风险选择规范，验证与交付状态分别记录。

任务开工、恢复与收尾按 `docs/ai-coding/task-lifecycle.md` 执行，分别记录执行、业务关闭和资源状态。
