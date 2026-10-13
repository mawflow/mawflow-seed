# AI 项目指令

这里记录对 AI 说的意图，不是 Shell 命令。AI 必须先读取 `AI_START_HERE.md` 和 `.maw/agent-entry.yaml`，再把意图映射为可验证的项目操作。

- `初始化项目`：检查 Git 与 Seed 状态，建立项目治理骨架。
- `初始化组件 <key>，类型 <type>`：调用或等价执行 `mawflow component init`，默认不启用。
- `采纳组件 <path>，标识 <key>`：保留现有源码并纳入组件治理。
- `启用组件 <key>` / `禁用组件 <key>`：显式切换组件状态，不删除目录。
- `检查项目` / `检查组件 <key>`：运行 doctor 并解释阻塞项。
- `发布上线`：按项目定义的发布环境与审批边界执行；不自动等同于生产发布。

跨 AI 工具转交任务时使用 `CHATGPT_TO_AI.md` 的通用格式。

- `#Seed反馈` / `#Seed复盘` / `#Seed优化报告`：按 [TINST-042](docs/ai-instructions/instructions/seed-feedback.md) 从可访问的任务经验生成脱敏建议报告；`#Seed反馈：评审 <报告>` 接入既有种子仓回流流程。

- `#更新动态` / `#T043`：按 [TINST-043](docs/ai-instructions/instructions/generate-update-notes.md) 默认生成最近100条；`#更新动态 --all` 或 `#更新动态：全部` 生成全部已记录历史；日常更新追加权威片段，支持云端 Markdown 分页。

模板升级统一采用已验证公共稳定 tag 与同版本 Kit；仅平台主仓由自身项目身份及源码绑定读取独立 Seed Git 目录。`mawflow project drift` 与项目计划脚本共用 Seed Kit >=2.12.0 实现。来源或基线迁移必须先预览并验证，不能只换 URL 或清空旧基线。

- `#规范` / `#阶段规范` / `#T044`：按 TINST-044 查询六阶段、项目适用规则、任务清单及证据声明；不授予执行或发布权限。
