# AI 项目指令

这里记录对 AI 说的意图，不是 Shell 命令。AI 必须先读取 `AI_START_HERE.md` 和 `.maw/agent-entry.yaml`，再把意图映射为可验证的项目操作。

- `初始化项目`：检查 Git 与 Seed 状态，建立项目治理骨架。
- `初始化组件 <key>，类型 <type>`：调用或等价执行 `mawflow component init`，默认不启用。
- `采纳组件 <path>，标识 <key>`：保留现有源码并纳入组件治理。
- `启用组件 <key>` / `禁用组件 <key>`：显式切换组件状态，不删除目录。
- `检查项目` / `检查组件 <key>`：运行 doctor 并解释阻塞项。
- `发布上线`：按项目定义的发布环境与审批边界执行；不自动等同于生产发布。

跨 AI 工具转交任务时使用 `CHATGPT_TO_AI.md` 的通用格式。
