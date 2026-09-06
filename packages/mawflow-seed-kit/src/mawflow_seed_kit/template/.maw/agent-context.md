# 通用 Agent 工作约定

本文件适用于 Codex、Claude Code、Gemini CLI、Cursor 及其它 Agent。

- 先读 `.maw/project.yaml`、`.maw/components.yaml` 与 `.maw/modules.yaml`，按模块进入任务相关文档。
- 通用规则在 `.maw/agent-rules.yaml`，项目扩展与权限边界以当前项目文件和用户授权为准。
- 只读取当前任务需要的路径。prompts、归档、运行产物不进入默认上下文。
- `.maw` 保存共享事实，`.local` 保存本机覆盖；共享输出不包含秘密或本机私有绑定。
- 有 CLI 时可执行 `mawflow-seed-kit doctor agents .` 与 `mawflow-seed-kit context . --module <key>`；没有 CLI 时直接按本入口读取文件，仍可开发和协作。
- RTK 可用时用于压缩输出；缺失时使用原生命令并限定路径、行数与输出大小。
- 验证命令取自实际组件或项目命令，不凭模板名称猜测。未执行的检查明确标为未验证。
- 提交、推送、镜像和发布按项目策略及本轮授权执行；只处理当前任务改动。
- 交接写清目标、事实、范围、验证证据与未完成项；不依赖任何工具的私有会话格式。
