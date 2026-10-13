# 项目资源库与经验库增量接入

新增 docs/ai-coding/workspace-libraries.md 和 docs/capabilities/workspace-libraries.md，增量合并 .maw/agent-entry.yaml 的 resource_libraries 路由与 docs/ai-coding/README.md 链接。运行时由正式 Host 提供 resources.search / resources.resolve，不复制账号索引或正文到项目。没有相应能力时保持项目文件回退。保持既有项目 key、README、源码、app_key、发布配置、凭据及 .local 私人资料。公共发行与正式 Host 更新尚待全量发布，不能仅按开发提交宣称所有项目可用。
