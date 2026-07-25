# __PROJECT_NAME__ · AI Start Here

本项目采用 MAWflow Seed Contract v2。开始工作前依次读取：

1. `.maw/agent-entry.yaml`
2. `.maw/project.yaml`
3. `.maw/components.yaml`
4. `.maw/modules.yaml`
5. `.maw/project-lifecycle.yaml`

`.maw/**` 是共享项目事实，`.local/.maw/**` 是被 Git 忽略的本机覆盖。不要在共享配置中写入凭据值。
