# Seed 经验反馈报告

`#Seed反馈`（TINST-042，别名 `#Seed复盘`、`#Seed优化报告`）补齐已有种子仓升级闭环的输入端。任意 Agent 都能从当前可见任务生成 Markdown 报告，接收方在平台主仓或种子仓进行证据核验和去重，再进入 TINST-027 的候选台账。

- 执行规范：[Seed 反馈](../ai-instructions/instructions/seed-feedback.md)。
- 报告格式：[报告模板](../ai-instructions/templates/seed-feedback-report.md)。
- 既有回流：[种子仓库升级](../ai-instructions/instructions/seed-repository-upgrade.md)。

报告只总结实际可访问的上下文，不依赖某一种 Agent 的会话存储，也不自动抓取或上传私有对话。ChatGPT Web 可以沿仓库链接读取规范，并在会话内输出报告；Skill、CLI 和 MCP 均为可选入口。历史声明与本轮验证分级记录，已有能力、已修复问题、项目特例和通用缺口分开判断。

本次补丁不改变 Seed Contract 2、项目写入协议或 Host API。旧项目通过增量模板升级增加文件与指令路由，保留已有台账、业务规则和历史报告。
