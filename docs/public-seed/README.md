# Mawflow Seed 公开说明

本目录保存 Mawflow Seed 的公开使用说明。这里的内容面向开源用户和使用 Seed 启动 AI 编程工作目录的人，不依赖 Mawflow Studio 或 Enterprise。

Mawflow Seed 的核心定位是开源 AI 工作目录辅助系统。它不是只给人看的代码模板，而是让 Codex、Claude Code、Gemini CLI、Cursor Agent 等本地 AI coding tools 进入项目目录后，先加载项目事实、模块边界、任务规则、禁止路径、验证命令和收口协议，再开始执行任务。

## 阅读路线

1. `quickstart.md`：从创建工作目录到第一个 AI 可执行任务。
2. 根目录 `AI_START_HERE.md`：AI 进入工作目录后的启动顺序和默认边界。
3. `prompt-spec.md`：如何写一条可执行、可验收、可复用的 AI Coding 提示词。
4. `pack-types.md`：Seed Pack、Prompt Pack、Task Pack、Check Pack 和 Verification Pack 的边界。
5. `desensitization.md`：公开前必须删除或脱敏的内容。
6. `contributing.md`：如何贡献公开 Pack、示例和文档。
7. `open-source-release.md`：正式开源许可证、公开远端和发布边界。

## Seed 边界

Seed 只提供项目装备和协作协议。真实平台控制、节点调度、模型网关、账号池、发布审批、企业 RBAC、SSO 和私有化能力属于 Mawflow Studio / Enterprise，不随公开 Seed 分发。

当前公开许可证为 MIT；正式发布前运行 `bash ops/scripts/check-seed-open-source-readiness.sh --strict --format json` 确认 gate。
