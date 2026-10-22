---
doc_key: docs.capabilities.agent-portability
doc_type: capability
stage: governance
status: active
owner: platform-engineering
tags: [seed, agent, context]
read_contract:
  summary: "各 Agent 专用入口、未知 Agent 通用回退、可追溯任务上下文和独立就绪检查。"
  ai_read_hint: "涉及 Agent 入口、跨工具交接或 Seed 创建和迁移时读取。"
---

# 跨 Agent 入口与任务上下文

capability_key: `agent-portability`

Seed 2.8 保持 Contract 2。项目入口统一为 schema 3 / agent_protocol_version 1；历史入口通过迁移预览补齐，原有自定义字段和人工适配文本保留。

| 使用者 | 原生入口 |
| --- | --- |
| Codex | AGENTS.md |
| Claude Code | CLAUDE.md，导入 AI_START_HERE.md |
| Gemini CLI | GEMINI.md，导入 AI_START_HERE.md |
| Cursor | AGENTS.md |
| WorkBuddy 桌面对话 | AGENTS.md，继续读取 AI_START_HERE.md |
| ChatGPT Web / GitHub 源码阅读 | CHATGPT.md，用户显式给链接 |
| 未识别 Agent / 手动启动 | AI_START_HERE.md |

入口选择只依赖明确的工具身份；无法识别时走 generic_fallback。不会因为安装了某个二进制就猜测当前 Agent，也不要求修改用户全局配置。

## 共享与专用边界

`.maw/agent-entry.yaml` 负责启动、任务路由和适配声明；`.maw/agent-rules.yaml` 保存通用规则与项目扩展；`.maw/agent-context.md` 是短小的人类可读规则。专用入口仅维护受管区块，区块之外的团队内容保留。存在重复或不完整受管标记时停止迁移并报告冲突。

包内 `resources/agent-contract.v1.json` 定义默认语义和适配格式，版本摘要进入 Catalog。源仓、公开 payload 与 Kit materialization 均执行同一检查。高级维护者规则按任务读取，不强迫所有用户加载源仓维护流程。

## 命令与证据

```bash
mawflow-seed-kit doctor agents .
mawflow-seed-kit context . --agent 'Claude Code' --module example --format markdown
python3 ops/scripts/check-agent-portability.py --check-distribution
```

上下文按明确模块与 task_kind 读取，携带来源路径、内容哈希、字符预算与截断说明。不导出本机 overlay、凭据或会话历史；私有/手动目录、路径穿越及符号链接全部拒绝。字符预算控制文档正文，不表示模型 Token 精确计量。

Project Doctor 的结构状态与 `agent_readiness` 独立；静态检查不会伪造运行验证。Agent 检查缺失文件、空入口、必要规则、受管适配漂移和启动断链；普通 Seed Kit doctor 在 Agent 未就绪时返回非零，但结构编译器保留原有结构状态供迁移和工作台使用。

文件读取是基础层；CLI 提供确定性检查、计划和导出；MCP、Skill、RTK 是可选增强。缺少 RTK 时使用有界原生命令。提交、推送、镜像与发布服从当前项目策略及用户授权。

## 升级与验收

使用受控 Seed 迁移 preview/confirm/rollback；不复制整个模板覆盖项目。检查新项目、v1/v2 入口迁移、重复执行零变更、人工内容保留、缺失/空文件、越界/链接拒绝和哈希保护回滚。

真实会话验收应记录工具版本、加载入口、任务范围、验证命令与结果；各工具独立验收。没有启动对应 Agent 时明确为 runtime unverified。

## 网页仓库阅读

README 与通用入口提供 CHATGPT.md 的相对链接，适用于公开或用户有权限的私有 GitHub 仓库。网页适配使用 repository_links，不假定文件名自动发现，也不依赖 @ 导入、隐藏目录扫描、本机终端或插件。按仓库/ref/commit 固定源码，逐个读取链接正文；权限缺失、版本不可选、搜索片段和内容截断都属于证据缺口。只读能力仍可完成审阅、方案和交接；有实际写入或执行工具时才按授权执行并给结果。

[OpenAI 的代码审查说明](https://learn.chatgpt.com/docs/code-review)建议明确指定仓库的 PR、分支、提交或文件；本项目进一步要求跨文件使用同一提交作为证据。这是 Seed 的协作约定，不是对 ChatGPT Web 自动加载入口的产品保证。

## WorkBuddy 桌面对话

当前研发验收优先级为 Codex 第一、WorkBuddy 第二；先完成 Seed 文件对话，再评估 CLI 派发。选择项目与分支后，从共享入口定界，修改前核对 owned paths、真实检查入口及授权。无需额外 CODEBUDDY.md，不复制第二套项目规则。若客户端未自动加载入口，显式要求读取 AI_START_HERE.md；文件存在与静态 ready 不证明自动加载。

`--agent WorkBuddy`、`work-buddy`、`Work Buddy`、`WorkBuddy Desktop` 明确解析为 workbuddy，复用 AGENTS.md。未知身份仍走 generic_fallback；不检测本机二进制猜身份，也不改变权限或全局模型。每次真实会话独立记录客户端版本、档位、实际模型标签和执行结果，静态 readiness 的 runtime_verified 仍为 false。

核对派生项目版本时按需读取 `.maw/seed.lock` 与 `.maw/template-source.yaml`，分别报告 Contract、已应用 Seed/Kit 与当前解释器/工具版本。未读、缺失、截断分别记录；不因没读到具体版本断言文件不存在。事实导航不授权读取私有 Seed 源或自动升级目标项目。全仓递归 Glob 也是全仓搜索。

跨会话接续使用 CHATGPT_TO_AI.md 的通用格式，把 task/run、基线、目标、允许/禁止路径、已完成动作、实际验证及未完成项保存到任务已有文件并提供可发现的手册链接。新任务先核对文件和 Git 是否变化，再推进未完成项；不依赖客户端私有历史、隐藏推理或整段聊天。来源事件追加，旧事件不覆盖；工具错误需保留原失败与恢复后结果。

2026-10-22 的 Seed 2.17.0 blank 项目真实只读验收证明共享入口可用；一次递归 Glob 和一次版本依据漏读分别保留为边界偏差与导航缺口。小修改和跨会话接续以本轮后续验收回执为准，不能从静态测试推断完整兼容。公开稳定 Seed/Kit 发行、已安装 Host 升级、CLI 自动派发和真人验收分别记录。
