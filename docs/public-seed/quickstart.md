# 快速开始

Mawflow Seed 不是只复制一组目录的代码模板。它是一个 AI 工作目录辅助系统：你把 Seed 放进项目后，本地 AI coding tool 可以先读规则、项目事实、模块边界、禁止路径、验证入口和收口方式，再开始执行开发任务。

## 1. 创建项目

```bash
git clone https://github.com/mawflow/mawflow-seed.git my-project
cd my-project
```

正式公开远端见 `docs/public-seed/open-source-release.md`；发布公告前仍需确认 GitHub 仓库对外可见。

## 2. 写入项目事实

至少更新这些文件：

- `README.md`：你的项目介绍、启动方式、维护入口。
- `AI_START_HERE.md`：保留 AI 启动顺序和默认边界；可补充项目自己的第一步说明。
- `.maw/agent-entry.yaml`：AI 工作目录入口协议；可按项目事实调整启动文件、禁止路径和收口字段。
- `.maw/project.yaml`：项目 key、项目名称、负责人和协作模式。
- `.maw/components.yaml`：`server`、`client` 或你的真实 app_key。
- `.maw/modules.yaml`：业务模块树。
- `.maw/app-runtime.yaml`：本地调试入口和测试账号引用。

公开仓不包含内部开发源 `.maw/template-source.yaml`。如需在项目中声明 Seed 来源，可复制 `.maw/template-source.example.yaml` 为 `.maw/template-source.yaml`，再按项目事实调整；本机路径、私有模板源和维护者覆盖只能写入 `.local/.maw/template-source.yaml`。

通过 `mawflow project init` 创建的项目会自动写入公开来源、tag 和已采用 commit。后续先运行：

```bash
mawflow project drift
```

状态为 `behind` 时，按输出的 commit 范围在当前会话做语义增量升级；不得整仓覆盖已有 `README.md`、`code/`、发布配置、仓库映射、secrets、`.local` 或模块档案。验证通过并更新 `template_source.applied_version` 后再次运行，状态应为 `up_to_date`。

## 3. 启动 AI 会话

在 Codex、Claude Code、Gemini CLI 或 Cursor Agent 中进入项目目录后，先让 AI 读取：

```text
请先读取当前项目 Seed 工作规则：
- AI_START_HERE.md
- AGENTS.md
- .maw/agent-entry.yaml
- .maw/project.yaml
- .maw/components.yaml
- .maw/modules.yaml
- .maw/app-runtime.yaml
- docs/README.md

确认项目身份、修改范围和验证方式后，再执行任务。
```

## 4. 写第一条 Prompt Spec

使用 `docs/public-seed/prompt-spec.md` 的结构，把原始想法整理成：

- 目标。
- 背景和输入资料。
- 允许修改的路径。
- 禁止修改的路径。
- 验收标准。
- 验证命令。
- 收口要求。

## 5. 拆成 Task Pack

简单任务可以直接交给 AI 执行。复杂任务应创建 `prompts/codex/task-packs/<slug>-codex-tasks/`，包含 `README.md`、`EXECUTE_PROMPT.md`、`PLAN.md`、`manifest.json`、`prompts/00-session-runbook.md` 和编号任务。

## 6. 提交前检查

建议至少运行：

```bash
git diff --check
python3 ops/scripts/check-public-seed-workdir.py --format json --strict
```

公开仓或公开 payload 使用 `PUBLIC_PAYLOAD_MANIFEST.json` 作为文件完整性契约。种子开发仓维护者还需在内部 release 分支运行 distribution、open-source、local-boundary、code-deliverable 和主仓 admission gate。
