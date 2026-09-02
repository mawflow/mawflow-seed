# __PROJECT_NAME__ · AI Start Here

本项目采用 MAWflow Seed Contract v2。开始工作前依次读取：

1. `.maw/agent-entry.yaml`
2. `.maw/project.yaml`
3. `.maw/subprojects.yaml`
4. `.maw/code-sources.yaml`
5. `.maw/deployments.yaml`
6. `.maw/components.yaml`
7. `.maw/modules.yaml`
8. `.maw/project-lifecycle.yaml`
9. `PROJECT_COMMANDS.md`（AI 对话指令）
10. `MAWFLOW_CLI.md`（终端命令）

`.maw/**` 是共享项目事实，`.local/.maw/**` 是被 Git 忽略的本机覆盖。托管 clone 默认位于 `.local/code-sources/<source-key>/`，允许嵌套 Git，但必须保持被外层项目 Git 忽略。不要在共享配置中写入凭据值或本机绝对路径。
