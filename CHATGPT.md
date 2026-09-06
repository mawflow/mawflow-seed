<!-- mawflow:bootstrap:start -->
# MAWflow Agent 入口
Read [AI_START_HERE.md](AI_START_HERE.md) before working in this project.
共享规则与项目事实以 `.maw/agent-entry.yaml`、`.maw/agent-rules.yaml` 为准。
只读取本任务所需的模块和文档；先确认允许路径、禁止路径及验证命令。
不自动读取 prompts、归档、本机私有目录；不提交秘密或无关改动。
工具、Skill、MCP、RTK 均非读取项目规则的前置条件；已有授权按任务范围延续。
完成时区分已修改、已验证、已发布与真人验收，列出未验证项。

## 从 GitHub 读取源码的网页 Agent
本文件是用户显式指定的网页入口，不假定 ChatGPT Web 或连接器自动加载 AGENTS.md、@ 导入或隐藏目录。
先记录 owner/repository、目标 branch/ref 与实际 commit SHA；所有引用固定到同一提交。连接器不能选择 ref 时说明实际读取范围与版本不确定性。
打开 [通用规则](.maw/agent-rules.yaml)、[读取路由](.maw/agent-entry.yaml)、[项目](.maw/project.yaml)、[组件](.maw/components.yaml) 与 [模块](.maw/modules.yaml)，然后只读取当前任务相关文件。
搜索片段不是完整源码；先获取文件正文。仓库无权限、文件缺失或内容截断时明确说明缺口，不猜测未读代码。
只有读取能力时交付带路径和提交依据的分析、建议补丁与待执行验证。测试、提交、推送、部署必须有当前会话可用工具和真实结果才能标为完成。
需要执行环境时按 [交接协议](CHATGPT_TO_AI.md) 交接仓库/ref/commit、目标、已读文件、允许路径、修改建议、验证命令和未验证项；不要索取或导出私钥与生产凭据。
可选：有 CLI 的协作者运行 `mawflow-seed-kit context . --agent chatgpt-web --format markdown`，提供带来源和哈希的有界上下文。网页端无需安装 CLI、MCP、RTK 或 Skill。
<!-- mawflow:bootstrap:end -->
