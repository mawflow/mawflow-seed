# Mawflow Seed

MAWflow Seed 是安装在 AI 编程工作目录里的开源 AI 项目导航系统，也是工作目录辅助层。它帮助个人开发者、独立开发者和小团队把一个普通代码仓库整理成 AI 可以接手、可以检查、可以交付的项目工作区。

Seed 的核心不是传统代码模板，而是给 Codex、Claude Code、Gemini CLI、Cursor Agent 等本地 AI coding tools 一个稳定工作环境：AI 进入目录后先读取项目事实、模块边界、任务规则、禁止路径、验证入口和收口协议，再开始执行开发任务。

它提供：

- `.maw` 项目协议：项目、组件、模块、运行时、发布、仓库和安全边界的可读配置。
- AI 工作目录入口：`AI_START_HERE.md`、`.maw/agent-entry.yaml` 和 `AGENTS.md` 共同定义启动顺序、读写边界和收口方式。
- Prompt Spec：把一句想法整理成目标、上下文、边界、验收和验证。
- Task Pack：把复杂工作拆成可恢复、可验证、可提交的 Codex 任务包。
- Check Pack：把项目初始化、模块档案、脱敏、发布和本地边界变成可执行检查。
- Verification Pack：把功能完成后的证据、测试、风险和交付说明沉淀下来。
- 模块档案和 AI 指令：让后续 AI 会话不用从空白对话重新解释项目。

## 它不是什么

Mawflow Seed 不是 Mawflow Studio、Enterprise 或主仓控制面。公开 Seed 不包含 Orchestrator、Workbench、Governance Admin、Platform MCP、HostCommand、ActionRun、Secret Governance 运行时代码、客户数据、内部 prompt、hidden workspace 或真实 secret。

## 快速开始

1. 用 `mawflow project init my-project`、公开 Git 仓库或本机模板创建项目目录。
2. 进入项目目录后先读 `AI_START_HERE.md`。
3. 把根目录 `README.md` 改成你的真实业务项目说明。
4. 按项目事实更新 `.maw/project.yaml`、`.maw/components.yaml`、`.maw/modules.yaml` 和 `.maw/app-runtime.yaml`。
5. 阅读 `docs/public-seed/quickstart.md`，用 Prompt Spec 写清第一个任务。
6. 需要复杂任务时，按 `prompts/codex/task-packs/README.md` 创建 Task Pack。
7. 提交前运行公开和脱敏检查。

## 公开状态

当前种子开发仓候选已具备 source gate 和公开 payload 自检：

- 开源许可证：MIT，见 `LICENSE`。
- 公开远端：`https://github.com/mawflow/mawflow-seed`，见 `docs/public-seed/open-source-release.md`。
- 公开 payload 自检：`python3 ops/scripts/check-public-seed-workdir.py --format json --strict`。

发布操作仍需确认 GitHub 仓库对外可见、默认分支和 tag/release 策略符合当次公告。

## 继续阅读

- `docs/public-seed/README.md`
- `docs/public-seed/quickstart.md`
- `AI_START_HERE.md`
- `docs/public-seed/prompt-spec.md`
- `docs/public-seed/pack-types.md`
- `docs/public-seed/desensitization.md`
- `docs/public-seed/open-source-release.md`
- `examples/mawflow-packs/README.md`
