# 通用代码风格与质量规则

本文件定义跨端通用规则；各端差异以 `component-guides/` 为准。

## 基本原则

- 优先遵循现有代码风格和框架约定。
- 不做无关重构，不顺手改格式，不批量改名。
- 受信任私有仓库允许提交 `.maw/secrets.yaml`、`.maw/secrets.dev.yaml`、`.maw/secrets.pro.yaml`，但不得提交 `.maw/*.local.yaml`。
- 不提交客户隐私、用户上传文件、运行日志、缓存、裸证书私钥文件、`.ssh/` 下真实 key 文件或未脱敏外部交付资料。
- 业务代码相关配置优先写入 `code/<app_key>/` 内部工程文件；`.maw/app-runtime*.yaml` 只同步 AI 调试索引和 secret 引用。
- 文档、提示词、报告、交付说明和最终输出中涉及当前项目目录或文件路径时，必须使用项目根相对路径；不要写本机项目绝对路径。唯一例外是模板仓库生成给目标项目执行的模板升级提示词，可以在“本机模板仓库目录”字段写入生成时当前模板仓库的绝对路径，并要求目标会话先检查路径存在，不存在再兜底。
- 仓库级镜像由聚合后的仓库配置和 `ops/scripts/sync-repository-mirror.sh plan` 有效计划控制；项目仓库 push 成功后应先查看计划，再按 `Configured`、`Config source`、`Auto sync`、`Target enabled` 和 `Target auto sync` 判断是否继续同步 mirror。
- 公开发布镜像由 `repository_publish_mirrors` 和 `ops/scripts/publish-repository-mirror.sh` 控制；它只在人工显式 `publish --execute` 时发布定版版本，不参与普通仓库级 mirror 自动同步。
- 组件镜像仓库只允许当前项目仓库单向同步到目标仓库；不得从镜像仓库拉取、合并或反向覆盖当前项目。
- 共享 dev/pro 调试信息可提交，本机差异写入 local。
- 新增依赖前说明原因、影响范围和替代方案。
- 新增或改造 AI 可复用脚本时，优先使用 Python，并遵守 `docs/capabilities/ai-python-script-contract.md`：stdout 只输出最终结构化结论，长日志落盘，可能写入或远端操作必须支持 dry-run/plan，本机差异留在 `.local/`。
- AI 完成一段任务、任务包子任务或其它可独立验证的里程碑后，只要产生了代码、配置、文档或脚本改动，就必须完成必要验证、提交并推送当前分支，并按仓库级 mirror 有效计划同步镜像；不要等用户再次要求“提交 push”。commit message 和提交内容说明必须使用中文。

## 命名和结构

- 命名应与所在端现有习惯一致。
- 新文件应放在同类功能已有目录下，不随意创建平行体系。
- 公共工具、基础组件、全局配置属于高影响范围，修改前必须确认调用面。

## 注释和文档

- 只在复杂业务规则、非显然兼容逻辑、协议转换、临时绕行方案处写注释。
- 不写解释字面代码的空注释。
- 变更影响使用方式、配置、发布或接口时，同步更新相关文档。

## 文档同步判断

每次新增或调整内容后，AI 必须判断是否需要同步更新项目文档，确保任意新的 AI 会话能快速掌握项目整体情况。

需要更新文档的典型情况：

- 新增、删除或调整目录结构、模块边界、端职责、工程命令、构建或启动方式。
- 新增、调整或废弃接口、事件、协议、数据模型、数据库表、配置项、环境变量或发布流程。
- 改变用户流程、页面入口、权限、菜单、状态流转、错误码、运维步骤或验收方式。
- 引入新依赖、新框架、新脚本、新发布随带文件或新的外部服务。
- 修复的问题会影响排障经验、风险认知、后续开发约束或初始化待办清单。

优先更新位置：

- 项目全局变化：项目 `README.md`、`TEMPLATE_OVERVIEW.md`、`docs/template-usage-guide.md`、`.maw/*.yaml`。
- AI 编码规则变化：`docs/ai-coding/`。
- 端工程变化：`docs/ai-coding/component-guides/<component>.md`、`code/<component>/.maw.component.yaml` 和 `.maw/app-runtime.yaml`。
- 需求和设计变化：`docs/requirements/`、`docs/design/`、`docs/planning/`。
- 发布和运维变化：`release/rules.yaml`、`ops/`、`docs/delivery/`。
- 仓库同步变化：`docs/customer-repository-sync-guide.md`、`docs/component-mirror-repository-guide.md`、`.maw/repositories.yaml`。
- 模块边界变化：优先更新 `docs/modules/<module-key>/module.md` 和 `docs/modules/<module-key>/changelog.md`。
- 公共能力变化：优先更新 `.maw/capabilities.yaml`、必要的 `docs/capabilities/<capability-key>.md` 和 `docs/technical-map/README.md`。
- 脚本规范变化：优先更新 `docs/capabilities/ai-python-script-contract.md`、`docs/ai-instructions/instructions/script-contract-upgrade.md`、`ops/scripts/README.md` 和 `.maw/capabilities.yaml`。
- 项目健康上下文变化：优先更新 `.maw/health/`、`docs/capabilities/project-health-context.md`、`docs/ai-instructions/instructions/project-health-context.md` 和 `ops/scripts/check-project-health-context.py`。
- 对人或 AI 有提示意义的待办、澄清、缺口、口径变更、风险或审计提示：优先更新 `.maw/project-signals.yaml`，必要时同步 `docs/planning/todos/active.md` 或 `docs/ai-instructions/` 候选台账。

如果页面、接口、数据表、状态流、配置或发布规则发生变化，应优先判断是否更新对应模块档案和 changelog。如果判断不需要更新文档，应在最终说明中简要说明原因。

最终说明必须写出模块档案更新判断、经验命中判断、命中的 code 组件应用和发布更新状态：

```text
experience_lookup:
  checked: yes/no
  matched:
    - <EXP-XXX 或 none>
  detail_read:
    - <路径或 none>
  updated:
    - <路径或 none>
module_key: <涉及模块或 not_identified>
module_dossier_updated: yes/no/not_required
module_dossier_reason: <原因>
updated_module_docs:
  - <路径>
hit_code_components:
  - <component>/<app_key 或 none>
release_update_status:
  - <本轮修改了 <app_key> 的 <代码/运行配置/发布覆盖/部署脚本/线上可见行为>，需要发布 <app_key> 才会生效，当前已发布/当前未发布/当前未发布或未验证；或未命中 code 组件应用，无需更新发布>
release_commands:
  - <app_key>: <按配置列出 #发布：发布 <app_key>（默认 <env>）、#发布：发布 <app_key> 到 <env_option> 以及可用中文口令 #发布测试/#发布上线/#发布生产/#发布生成；多个 app_key 分别列出，用户可复制其中一条或多条；或 none>
release_confirmation_prompt:
  - <本轮需要发布 <app_key 列表> 才会生效。是否确认发布全部？回复“确认发布全部/确认/是”将发布全部；如只发布部分，请复制上方对应组件的 #发布 指令；或 none>
todo_task_update_status:
  - <新增/完成/取消/查询了哪些 TODO-ID；或未涉及被依赖但暂不实现的待办任务>
health_context_update_status:
  - <新增/更新/审计/未涉及哪些 .maw/health 记录 ID；是否运行 check-project-health-context.py；如发现应登记但未登记，写明原因>
capability_map_update_status:
  - <新增/复用/废弃/未涉及哪些 capability_key；是否更新 .maw/capabilities.yaml 或不更新原因>
project_signal_update_status:
  - <新增/更新/关闭/未涉及哪些 signal_id；是否同步待办、澄清、缺口、口径变更或 AI 前置条件>
repository_identity_update_status:
  - <新增/更新/判断/未涉及 declared roles、detected roles、角色目录覆盖和高风险约束>
mcp_diagnostics_instruction:
  - <added/planned/not_applicable，并说明 #MCP服务诊断 或等价诊断是否注册>
host_purpose_mcp_alignment:
  - <platform/customer 宿主机用途、本地项目级 MCP 和普通非 MAW 项目兼容是否已对齐>
capability_credential_variable_alignment:
  - <MAW_*_REF、凭证类型、能力矩阵和 legacy alias 是否已对齐>
seed_repository_upgrade_suggestions:
  - <未发现新的种子仓库升级建议；或已记录到 docs/seed-repository-upgrade-candidates.md，并说明使用场景、理由和兼容性要求>
```

经验命中只允许主动检索 `docs/ai-instructions/experience-index.md`、候选台账和总纲索引；`docs/ai-instructions/solutions/**` 只能在索引、候选台账、用户明确路径或当前错误精确命中后读取对应单个详情文件。

发布状态只描述本轮任务后的状态：本轮执行并验证发布才写“当前已发布”；需要发布但未执行发布时写“当前未发布”；无法确认目标环境时写“当前未发布/未验证”。需要发布且当前未发布或未验证时，必须按 app_key 同步输出配置中登记的可复制 `#发布` 快捷指令，并在收口末尾询问是否“确认发布全部”；用户回复“确认发布全部/确认/是/全部发布”时发布全部待发布组件，复制其中一条或多条指令时只发布对应组件，包括 SQL/迁移。用户说 `发布测试`、`发布上线`、`发布生产` 或 `发布生成` 且未指定组件时，先读取 `releases.defaults.release_command_aliases` 和对应 `environments.<env>.remote_server.default_release_components`，再按发布版本状态和组件路径差异筛选实际发布名单。`发布测试` 是本地调试版本，需给可访问调试地址；`发布上线` 是部署到 `remote_staging_server` 的编译包部署测试，仍属于测试，需给线上可访问地址；`发布生产` 是部署到 `remote_production_server` 的生产发布，涉及生产环境安装或版本上线必须人工审计。`发布上线` 和 `发布生产` 执行前必须确认本地候选 commit 等于发布来源远端分支；发布成功后更新 `artifacts/release-state/<env>/<app_key>.json`。

## Git 提交和推送

- AI 每次改完代码、配置、文档或脚本后，必须先运行与改动范围匹配的验证，再执行 `git status` 确认变更范围。
- 验证通过或已明确说明无法验证的原因后，AI 必须提交并推送当前分支；对于任务包或较长任务，每个完成并可独立验证的子任务也按此规则主动提交并推送。推送项目仓库成功后，先运行 `ops/scripts/sync-repository-mirror.sh plan`，以 `Configured`、`Config source`、`Auto sync`、`Target enabled` 和 `Target auto sync` 判断是否继续执行仓库级 mirror 同步；不要只凭原始 `repository_mirrors.enabled=false` 判断未启用。
- 提交推送要先保证本次任务改动独立：先只暂存、提交并推送本次任务实际修改的文件；推送后再看剩余 `git status`。若存在其它非本次任务文件，只有确认它们全部不在 `code/**` 内，且不是密钥、本机 local、日志、缓存或构建产物，才允许用单独中文 commit message 做补充提交并推送。剩余 `code/**` 组件业务代码、组件运行配置或组件内文件变动不得顺手纳入本次推送。
- commit message 和提交内容说明必须使用中文，至少覆盖变更范围、验证结果和遗留风险或未完成事项。
- 只有用户明确禁止 git 写入、没有实际变更、存在无法安全暂存的无关脏改动，或认证、网络、分支保护、远端拒绝导致无法 push 时，才可跳过提交或推送。
- 如果无法 push，AI 必须在最终说明中明确写出失败原因、当前 commit hash 或未提交状态，以及需要人工处理的下一步。

## 错误处理和日志

- 错误处理应保留上下文，避免吞异常。
- 面向用户的错误提示要清晰，面向开发/运维的日志要可定位。
- 不在日志中输出密钥、token、密码、身份证号、手机号全量、生产连接串等敏感信息。

## 测试和验证

- 优先运行与改动范围最小匹配的测试。
- 无法运行测试时，说明原因并给出人工验证步骤。
- 涉及权限、支付、数据删除、发布、同步、数据库迁移的改动，需要更高等级复核。

## 禁止事项

- 禁止无明确需求删除业务代码、数据库脚本、发布脚本或历史资料。
- 禁止绕过类型检查、lint、测试或安全校验来“让构建通过”。
- 禁止把外部 AI 输出直接落代码，必须结合本仓库实际模式复核。
