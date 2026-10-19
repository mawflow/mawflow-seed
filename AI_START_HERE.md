# AI Start Here

MAWflow Seed is an open source AI project navigation system and workdir assistant for local coding agents.
This AI workdir gives those tools a stable local starting point without replacing project facts or human review.

When Codex, Claude Code, Gemini CLI, Cursor Agent, or another local AI coding tool enters this project directory, start here before changing files.

## What This Directory Provides

Seed gives the AI:

- project facts in `.maw/project.yaml`;
- subproject boundaries in `.maw/subprojects.yaml`;
- shared Git declarations in `.maw/code-sources.yaml`, deployment targets in `.maw/deployments.yaml`, and component boundaries in `.maw/components.yaml`;
- module boundaries in `.maw/modules.yaml`;
- runtime hints in `.maw/app-runtime.yaml`;
- collaboration rules in `.maw/agent-entry.yaml`;
- protected path and secret rules in `.maw/policies.yaml`;
- task and prompt structures under `prompts/`;
- validation and release checks under `ops/`.

Seed does not replace the user's IDE, project manager, cloud platform, or review process. It gives local AI tools a stable project map and execution contract.

## Optional Agent Skill

Mawflow Agent Skills may be installed at user scope to help an Agent discover this directory and adapt natural-language requests to the `mawflow` CLI or Local MCP. The Skill is optional: when it is absent, disabled, uninstalled, or older than this Seed, continue with the project-local startup order below. A Skill never replaces project files, never overrides project facts, and never becomes a prerequisite for development or validation.

## Startup Order

1. Read `.maw/agent-entry.yaml` and `.maw/agent-context.md`.
2. Read `.maw/agent-rules.yaml`, `.maw/project.yaml`, `.maw/components.yaml`, and `.maw/modules.yaml`.
3. Follow task_routes and the selected module doc; load only task-relevant context.
4. Identify allowed paths, validation commands, and existing authorization before editing.

## Default Boundaries

- Do not modify unrelated modules.
- Do not copy template defaults over real project facts.
- Do not commit `.local/**`, real secrets, tokens, private keys, production connection strings, raw logs, build output, or user-uploaded files.
- Do not read `prompts/**`, `runtime/**`, `workspaces/**`, `artifacts/**`, or `docs/archive/**` unless the user explicitly points to them or the active task directly requires them.

## Completion Contract

At the end of a task, report:

- what changed;
- what was verified;
- what was not verified and why;
- known risks;
- release or local environment impact;
- suggested next step when a human decision is needed.

## 选择 Agent 入口

[Codex / Cursor](AGENTS.md) · [Claude Code](CLAUDE.md) · [Gemini CLI](GEMINI.md) · [ChatGPT Web / GitHub 源码阅读](CHATGPT.md) · [通用入口](AI_START_HERE.md)。无法识别 Agent 时使用通用入口。网页 Agent 由用户显式提供入口链接与仓库目标分支或提交。

## 文档来源积累

产生长期结论或缺口时按 [交互来源收录规范](docs/ai-coding/document-source-capture.md)记录最小来源与回执；只读任务不写入。

- 本地开发开工、恢复与重任务前后按 `docs/ai-coding/development-resources.md` 检查资源和工作台/CLI；按需复用服务，跨项目重任务串行，通信失败回退项目文件。

- [六阶段规范导航](docs/standards/README.md)：按项目适用条件、任务范围与风险选择规范，验证与交付状态分别记录。

任务开工、恢复与收尾按 `docs/ai-coding/task-lifecycle.md` 执行；分别说明执行结果、业务关闭与资源回收，等待/失败/取消/交接也清点资源。
