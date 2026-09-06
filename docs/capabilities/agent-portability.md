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
