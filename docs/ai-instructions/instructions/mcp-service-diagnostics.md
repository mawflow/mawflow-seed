# 指令：MCP 服务诊断

## 元信息

- ID：TINST-029
- 类型：项目指令
- 状态：启用
- 维护位置：`docs/ai-instructions/instructions/mcp-service-diagnostics.md`
- 推荐调用：`#MCP服务诊断`
- 精确调用：`#T029` 或 `#T029/MCP服务诊断`
- 触发词：#MCP服务诊断、MCP 服务诊断、MCP 连通性检查、本地 MCP 自检、项目级 MCP、Codex MCP、tools/list、maw.audit.ping、MAW_MCP_ENDPOINT、MAW_MCP_PROJECT_KEY
- 适用范围：配置或排查项目级 MAW MCP 后，检查连通性、项目绑定、仓库身份、宿主机用途、项目归属、开发绑定、工具列表、AI 可写路径、安全拒绝边界和普通非 MAW 项目兼容行为。

## 目标

让 AI 在配置项目级 MCP 后能自检“是否连到了正确项目、是否只暴露授权工具、是否按仓库身份、宿主机用途、项目归属和开发绑定限制读写”，并在 MCP 未实现或未启用时输出 graceful warning，而不是误判为普通开发失败。

## 输入要求

- 必需输入：当前项目工作目录。
- 推荐输入：预期 `project_key`、MCP endpoint 来源、仓库身份、宿主机用途模式、项目归属、开发绑定、源码访问方式、Codex surface（shell/app）和需要检查的工具命名空间。
- 缺失时处理：
  - 先读取 `.maw/project.yaml`、`.maw/repository-identity.yaml`、`.maw/environments.yaml` 和 `docs/implementation/local-mcp-gateway/README.md`。
  - 如果没有 `.maw/project.yaml` 或项目级 MCP 配置，说明“当前项目未启用 MAW MCP”，不强行接管普通 Codex 项目。
  - 如果 endpoint、session 或真实凭证缺失，只输出待配置项和本机填写位置建议，不要求用户在对话里粘贴明文。

## 执行步骤

1. 读取项目级 MCP 配置来源，确认不是全局误配置；优先检查 `MAW_MCP_ENDPOINT`、`MAW_MCP_PROJECT_KEY`、`MAW_PROJECT_ROOT`、`MAW_MCP_CLIENT_PROFILE` 和 `MAW_MCP_CALLER_SURFACE`。
2. 检查 endpoint 可达；不可达时输出 graceful warning、配置来源和下一步建议，不输出敏感值。
3. 执行 MCP `initialize` 或目标项目等价握手，记录协议版本、能力版本和审计 ID。
4. 执行 `tools/list`，确认工具数量、工具命名空间、能力版本和授权状态。
5. 调用 `maw.audit.ping` 或等价 ping 工具，确认返回的 `project_key`、工作目录、仓库角色、宿主机用途、项目归属、开发绑定、源码访问方式、MCP 暴露面和审计 ID。
6. 对比 `.maw/project.yaml`，确认 MCP 返回的 `project_key` 与当前项目一致。
7. 对比 `.maw/repository-identity.yaml` 和 `ops/scripts/extract-project-metadata.py --section repository-identity`，确认 MCP 返回的 `repository_roles` 与本地有效身份一致；不一致时 fail closed。
8. 对比 `.maw/environments.yaml` 的 `host_purpose_modes`、`host_project_binding` 和 `project_level_mcp`，确认 `host_purpose`、`ownership_type`、`binding_type`、`source_access_mode`、`mcp_exposure_profile` 组合合法。
9. 验证 `tools/list`：`mcp_exposure_profile=customer_scoped` 时必须隐藏 platform-only 工具，例如完整源码 clone/fetch/push、平台仓库状态、内部 Template Pack 原始目录和跨项目治理工具。
10. 验证多项目隔离：错误 `project_key` 或错误工作目录应被拒绝。
11. 验证 AI 可写目录：`.maw/**`、`docs/modules/**`、`doc/modules/**`、`docs/ai-instructions/**`、`code/**`。
12. 验证模板规则查询：能读取模块档案、AI 指令、模板约束或经验候选；未授权目录只能通过只读规则或受控写入工具访问。
13. 验证 `code/` 同步安全：客户用途同步时清理 `.git`、secret、缓存和构建产物，并记录 `base_commit`、路径范围、文件 hash 和绑定类型。
14. 验证凭证边界：客户 Git 凭证只允许 `code-directory-mirror`；服务器 SSH 只允许 `deploy-staging`、`deploy-production`。
15. 验证授权拒绝：未授权能力、过期 session、跨项目访问、敏感路径写入、角色/绑定错配应 fail closed。
16. 输出审计摘要：工具、项目、仓库身份、用途、项目归属、开发绑定、源码访问、结果、拒绝项和下一步建议；不得输出 token、私钥、密码、真实连接串、session 明文或未脱敏 endpoint。
17. 外部普通项目兼容：无 MAW 项目配置时提示未启用，不创建或修改全局 Codex MCP 配置。

## 验证方式

- `docs/implementation/local-mcp-gateway/README.md` 和 `.maw/environments.yaml` 已声明项目级 MCP 可选启用。
- `PROJECT_COMMANDS.md` 和 `docs/ai-instructions/README.md` 已注册 `#MCP服务诊断` / `TINST-029`。
- 诊断输出包含 endpoint 可达性、initialize、`tools/list`、ping、project_key、repository_roles、host_purpose、ownership_type、binding_type、source_access_mode、mcp_exposure_profile、可写路径、拒绝边界和普通非 MAW 项目兼容结论。
- 无 MCP 服务时输出 graceful warning，不把任务标记为业务代码失败。

## 禁区

- 不把 MCP endpoint、token、session、SSH 私钥、API key、生产连接串或未脱敏错误栈写入可提交文件、最终说明或诊断包。
- 不修改全局 Codex 配置来“修复”某个项目的 MCP。
- 不在客户用途宿主机暴露完整种子仓、Template Pack、内部任务包、完整 Git 历史或内部远端仓库。
- 不在 `mcp_exposure_profile=customer_scoped` 时暴露 platform-only 工具。
- 不把客户 Git 凭证升级成 `git-clone`、`git-fetch`、`git-push` 或通用 `proxy`。
- 不把客户服务器 SSH 升级成通用 `ssh-wrapper`、`scp` 或 `rsync` shell 能力。

## 冲突与覆盖规则

- 用户最新明确要求优先。
- 与 `TINST-024` / `TINST-026` 冲突时，本指令只负责 MCP 诊断；模板升级仍按模板升级指令执行。
- 与密钥治理冲突时，按 `.maw/secret-bindings.yaml`、`docs/secret-governance-guide.md` 和更保守的 fail closed 规则处理。
- 与客户用途、平台用途、项目归属和开发绑定冲突时，以 `.maw/environments.yaml` 的 `host_purpose_modes`、`host_project_binding` 和 `docs/implementation/host-purpose-modes/README.md` 为准。

## 更新记录

- 2026-06-17：创建，新增项目级 MCP 自检、隔离验证、AI 可写路径和授权拒绝边界诊断流程。
- 2026-06-17：补充仓库身份、项目归属、开发绑定、源码访问方式和 MCP 暴露面检查。
