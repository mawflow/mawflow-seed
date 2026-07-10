# 指令：中文人类优先收口

## 元信息

- ID：TINST-020
- 类型：项目指令
- 状态：启用
- 维护位置：`docs/ai-instructions/instructions/final-closeout-response.md`
- 触发词：#收口格式、#中文收口、#简化收口、#详细收口、中文人类优先收口、最终说明格式、final closeout、技术元数据、展开验证、验证明细
- 适用范围：AI/Codex 完成任务、任务包子任务、发布、同步、验证或代码审查后的最终说明。

## 目标

让最终说明默认使用中文，并优先服务人类决策。机器字段仍保留，但集中放在“技术元数据”中，避免主要结论被 `snake_case` 字段淹没。

本指令也约束任务过程中新增或改写的人类维护文档语言：`.maw/interaction.yaml` 是语言口径事实源，项目文档、生成文档、任务包正文、模块档案、component guide 和 README 补充段落默认使用中文。英文仅保留在代码标识、文件名/路径、命令、协议名、第三方库原文、机器字段 key、品牌/专有名词或用户明确要求的英文内容中。

配置描述采用“双受众”策略：`title`、`summary`、`description`、`purpose`、`notes` 等默认展示字段面向人，优先使用中文；英文主要给 AI 或机器读取，放入同一对象的 `i18n.ai.en-US`。如果需要同时显式保存中文与英文，使用 `i18n.human.zh-CN` 和 `i18n.ai.en-US`，不要把英文说明作为人读默认文案。

## 收口详细度

默认使用“简化收口”：主展示只保留结论、关键变更、验证结论、本地测试入口/Git/发布影响和必要下一步。验证区默认用自然语言说明是否通过、覆盖了什么、是否有风险；不要把 `git diff --check`、`bash ops/scripts/...` 等命令清单作为默认主展示。

用户明确要求“详细收口”“完整收口”“展开验证”“给命令明细”“给技术元数据”“审计版收口”或等价表达时，使用“详细收口”：展开实际执行的命令、结果、完整技术元数据、发布/mirror 细节、风险和阻塞证据。

即使用户未要求详细收口，以下情况也应主动展开必要细节：

- 验证失败、未运行、存在 warning 或结论依赖人工判断。
- 涉及生产环境、线上环境、客户仓库、密钥、发布、回滚、迁移、数据修复或外部交付。
- 本地开发/测试环境未配置好，需要用户安装、补参数或确认风险。
- 任务包、审计、交接或复盘要求保留可追溯证据。
- 用户需要复制命令继续执行。

## 用户口径规则

- 用户习惯用语、别称或项目内叫法已经确认含义后，最终说明的主展示优先沿用用户口径。
- 技术元数据 key 保持稳定英文，不因用户口径变化而改名；值可以补充用户叫法，例如“本轮是 #提主 收口”。
- 如果某个叫法仍有歧义，不要在收口中装作已经确认；先说明待确认问题，或写明本轮暂未沉淀为正式口径。
- “种子仓库”和“模板仓库”统一指 `maw-project-template`。每次开发、修复、同步、发布或任务包收口时，必须判断是否发现适合回流种子仓库的优化或新增能力；如果有，主展示明确指出并说明是否已记录到 `docs/seed-repository-upgrade-candidates.md` 或已生成 `#种子仓库升级` 提示词；如果没有，也写明“未发现新的种子仓库升级建议”。

## 用户补充规则

最终说明如果需要用户继续提供参数、回答问题或做人工决策，不得只写一句笼统追问。每个需要用户补充的项目都要给出可执行信息：

- 参数或问题名称：明确要用户给什么，例如 `component`、`app_key`、客户仓分支、发布环境、服务器地址或是否确认执行。
- 用途与影响：说明这个参数会影响哪一步、选错会有什么风险。
- 获取步骤：给出具体拿到参数的方法，例如查看哪个配置文件、运行哪个只读命令、从哪个系统页面复制、或让客户/负责人确认哪一项。
- 建议选项：给出推荐选项和可选项；有默认值时说明“推荐使用 <默认值>”，有风险差异时用一句话说明取舍。
- 填写格式：给一个示例格式；敏感值不要要求直接粘贴明文，应使用 secret 引用、本机路径、环境变量名或让用户完成本机配置后回复确认。
- 敏感参数本机填写：如果缺少 token、cookie、密码、私钥、生产连接串、客户隐私、内部系统账号或其它敏感参数，AI/Codex 应先在 `.local/` 下创建合适的本机填写文件，再让用户填写；不要要求用户把明文贴到对话、共享文档、`.maw/` 可提交配置或最终说明里。文件中只写占位字段、注释、示例格式和获取步骤，不写真实值。
- `.local` 路径选择：需要被 MAW Python 配置读取器稳定读取的本机覆盖，放 `.local/.maw/<domain>.yaml` 或 `.local/.maw/<domain>.d/<slug>.yaml`；一次性任务参数、临时命令参数或人工确认值，放 `.local/config/<task>-sensitive-params.yaml`；只给当前 AI 会话继续执行看的短期线索，放 `.local/ai/<task>-sensitive-params.md`。如果目标文件已存在，必须保留用户已填写内容，只补缺失字段或改用新的任务文件。
- 收口说明敏感参数时，必须写清“本机填写文件”、需要填写的字段、每个字段的获取步骤、建议选项和填完后的回复方式，例如“请填写 `.local/config/<task>-sensitive-params.yaml` 后回复：已填写”。不要在收口里回显用户已经填写的敏感值。
- 派生自本种子仓库的项目，如果本轮执行或排查了发布、回滚、健康检查、服务器路径、端口、凭证位置或环境差异，应把避免重复踩坑的本机发布经验写入 `.local/ai/` 或 `.local/maintenance/` 的被忽略文件，并在 `local_update` 中写明路径或未更新原因。

同一轮收口中需要用户回答的问题建议控制在 1 到 3 个；必须阻塞下一步的标为“必填”，可后续优化的标为“可选”。如果可以通过当前仓库只读命令自己确认，应先自行确认，不把可自动发现的问题抛给用户。

## 收口顺序

默认按以下顺序组织：

1. 结论：一句话说明任务是否完成、是否阻塞、是否需要用户确认。
2. 变更：列出新增、修改或删除的关键文件和能力。
3. 验证：默认写人能读懂的验证结论和覆盖范围；详细收口、失败、warning 或用户要命令时，再列出实际运行的检查、测试、脚本和逐项结果。未运行的说明原因。
4. 本地测试入口：优先说明 `npm run dev` 是否已实现、是否已启动或刷新，并给出本机与局域网调试地址、健康检查或未配置提示；无运行态影响时可一句话说明无需更新。
5. Git/镜像：说明是否提交、推送、仓库级 mirror 是否同步或为何跳过；无异常时可压缩成一句话。
6. 模块与记忆：说明模块档案、项目指令、经验索引、本机记忆和关键词候选是否更新。
7. 待办、项目健康与项目信号：说明本轮是否新增、完成、取消、查询或未涉及 `docs/planning/todos/` 中的被依赖待办任务；是否更新 `.maw/health/` 中的健康问题、事实、决策、调研摘要或验收缺口；是否更新 `.maw/project-signals.yaml` 中对人或 AI 有提示意义的澄清、缺口、口径变更、风险或 AI 前置条件。
8. 技术地图与公共能力：说明是否新增、复用、废弃或未涉及 `.maw/capabilities.yaml` 中的公共能力、API、基类、组件、脚本或治理协议。
9. 仓库身份：说明是否新增、更新或判断 `.maw/repository-identity.yaml`、角色目录覆盖、declared roles、detected roles 和高风险操作约束。
10. 种子仓库升级建议：说明本轮是否发现可回流种子仓库的候选能力、候选记录位置、是否生成种子仓库执行提示词，以及兼容性取舍。
11. 发布影响：说明命中的 app_key、是否需要发布、当前发布状态和可复制发布指令。
12. code 交付影响：说明 code-only 交付是否受影响，以及是否有检查脚本或交付包建议。
13. 下一步可复制指令：只在用户需要继续操作时提供；如需用户补参数或回答问题，必须包含获取步骤、建议选项和填写格式。
14. 技术元数据：默认只保留本轮有实际信息量或任务包硬性要求的稳定字段；用户要求详细收口、审计或机器可读交接时，再输出完整字段清单。

## 本地测试入口规则

- 每次完成开发、修 bug、配置、脚本或模板协议任务后，必须判断本轮是否需要更新本地开发/测试环境。
- 根目录 `npm run dev` 是默认本地开发/调试验收入口；它应一键启动或重启本地开发环境，并输出本机 `127.0.0.1` 与局域网调试地址。可参考 MAW 主仓模式让 `dev` 转发到稳定底层入口 `local:dev`，`test:dev` 和 `local:test` 继续作为兼容入口。
- 如果派生项目没有实现 `npm run dev`，不要只说“未配置本地环境”；应明确引导派生项目把真实 dev server、服务重启脚本、Docker Compose、Makefile 或其它本地环境命令接到根 `package.json` 的 `dev` 或 `local:dev`，并保证命令输出本机与局域网调试地址。局域网访问要求服务监听 `0.0.0.0` 或等价可访问地址。
- 如果项目已配置本地开发或本地测试环境，修改后应实时完成必要的环境更新：例如运行或刷新 `npm run dev`、重启 dev server、刷新 Docker compose、执行迁移、重新构建本地服务、或确认热更新已经生效。
- 如果环境支持热更新或 watch，说明“已由本地开发入口实时加载”；如果 `dev` 或 `local:dev` 已经处于启动状态，收口应提示用户进入调试地址查看改动生效，并给出入口 URL、健康检查路径、关键页面/API 或验证命令。
- 如果项目没有可视页面，提供 API、CLI、健康检查、单元测试或脚本入口作为测试入口。
- 如果本机没有配置好开发环境，写明缺失项和阻塞原因，并给出可复制指令 `#安装开发环境` 或 `#安装环境：开发环境`。
- 如果本轮只改文档、模板协议、任务提示词或 code 外治理规则，且不影响运行应用，写明“本轮无需更新本地运行环境”。
- 不得把“已运行测试”误写成“本地环境已更新”。只有实际启动、刷新或确认无需刷新后，才写本地入口可用。

## 技术元数据字段

技术元数据使用英文稳定 key，值用中文说明即可。常用字段：

```text
experience_lookup:
module_key:
module_candidate:
module_dossier_updated:
module_dossier_reason:
updated_module_docs:
hit_code_components:
modified_components:
release_update_status:
release_commands:
release_confirmation_prompt:
local_environment_status:
local_test_entry:
local_update_commands:
local_environment_install_hint:
code_delivery_status:
todo_task_update_status:
capability_map_update_status:
project_signal_update_status:
repository_identity_update_status:
mcp_diagnostics_instruction:
host_purpose_mcp_alignment:
capability_credential_variable_alignment:
memory_update:
local_update:
upgrade_strategy_update:
seed_repository_upgrade_suggestions:
user_terms_style:
```

## 发布确认规则

- 如果本轮没有修改 `code/` 组件应用，写明“未命中 code 组件应用，无需更新发布”。
- 如果某个 app_key 需要发布才会生效，必须从 `.maw/releases.yaml`、`.maw/environments.yaml` 和 `code/<app_key>/.maw.component.yaml` 读取默认环境、可选环境、中文发布口令、默认组件范围、版本状态策略和发布快捷指令。
- 用户说 `发布测试`、`发布上线`、`发布生产` 或 `发布生成` 且未指定组件时，先读 `releases.defaults.release_command_aliases` 和对应 `environments.<env>.remote_server.default_release_components` 得到候选范围，再按 `artifacts/release-state/<env>/<app_key>.json` 的发布版本状态和组件路径差异计算实际发布名单；状态缺失按首次发布纳入。`发布测试` 通常基于本地环境安装或开启目标组件、部署或启动程序，并提供可访问调试地址；`发布上线` 是在线上服务器完成编译包部署测试并提供线上可访问地址，它仍属于测试；这两类测试发布允许当前工作区未提交改动，但必须在发布记录和状态文件中写明 dirty snapshot。`发布生产` 是部署到 `remote_production_server`，涉及生产环境安装、生产服务器部署或生产版本上线时必须写明人工审计状态。
- `发布生产` 执行前必须确认本地候选 commit 等于发布来源远端分支，且工作区没有未提交改动；不满足时阻塞发布。`发布测试` 和 `发布上线` 不强制该最新代码门。
- 发布成功后必须更新发布记录和 `artifacts/release-state/<env>/<app_key>.json` 或目标项目等价状态文件。
- 多个 app_key 需要发布时，按 app_key 分别列出 `#发布` 指令，用户可以复制其中一条或多条选择部分发布。
- 统一确认文案使用“确认发布全部”。用户回复“确认发布全部”“确认”“是”时，才发布全部待发布组件。

## code-only 交付规则

业务项目默认只交付 `code/`，但 AI 控制面仍可能在内部仓库维护。收口必须说明本轮是否影响 code-only 交付：

- 只改 `.maw/`、`docs/`、`prompts/`、`ops/` 或任务状态：通常不影响业务运行发布，但可能影响内部协作或交付检查。
- 修改 `code/`：说明受影响 app_key、是否需要发布、是否应重新导出 code-only 交付包。
- 修改脱敏、客户仓库同步或交付脚本：说明需要重新运行对应检查。

## 验证方式

- `.maw/interaction.yaml` 可解析。
- `.maw/interaction.yaml` 包含 `documentation`、`generated_documentation` 和 `task_pack_body` 的中文默认值。
- 新增或改写的项目文档、任务包正文、模块档案、component guide 和 README 补充段落使用中文标题和中文正文；不使用 `Objective`、`Required Reads`、`Implementation Requirements`、`Acceptance Criteria`、`Final Response Requirements`、`Component Guide`、`Scope`、`Build Notes` 或 `Sensitive Config` 等英文标题，除非用户明确要求英文或该文件是第三方原文。
- 配置、升级资产、能力索引、项目信号和仓库身份中的默认展示字段面向人时使用中文；需要英文给 AI 读取时，使用 `i18n.ai.en-US` 对照字段。
- 最终说明包含中文主展示和技术元数据；默认主展示为简化收口，不用命令清单淹没结论。
- 验证通过时，默认写“验证：通过”以及覆盖范围，例如“已覆盖模板协议、技术地图、仓库身份和本地边界检查；本轮未改 code，无需启动业务应用。”用户要求详细收口或验证异常时，再展开逐条命令。
- 需要发布时，`release_commands` 可复制，`release_confirmation_prompt` 使用“确认发布全部”，并在 `release_update_status` 中说明发布版本状态、实际发布名单和上线/生产本地最新检查结果。
- 需要说明 code-only 交付时，包含 `code_delivery_status`。
- 需要用户补参数或回答问题时，主展示包含参数获取步骤、建议选项和填写格式。
- 需要用户补敏感参数时，已创建合适的 `.local/` 本机填写文件，主展示包含本机填写文件路径、字段说明、获取步骤、建议选项和填完后的回复方式。
- 主展示包含“种子仓库升级建议”判断；有候选时说明 `docs/seed-repository-upgrade-candidates.md` 记录位置或 `#种子仓库升级` 提示词状态，技术元数据包含 `seed_repository_upgrade_suggestions`。
- 主展示包含“本地测试入口”判断；已配置环境时说明入口、健康检查和更新方式，未配置时说明缺失项和 `#安装开发环境` 指令，技术元数据包含 `local_environment_status`、`local_test_entry`、`local_update_commands` 和 `local_environment_install_hint`。
- 主展示包含“待办任务”判断；新增、完成、取消或查询待办时说明 TODO-ID、受影响模块和联调/回归建议，技术元数据包含 `todo_task_update_status`。
- 主展示包含“项目健康上下文”判断；新增或更新健康问题、需求事实、决策、普通健康待办、审计缺口、调研摘要或验收缺口时说明 `.maw/health/` 文件和记录 ID，技术元数据包含 `health_context_update_status`。
- 主展示包含“技术地图与公共能力”判断；新增、复用、废弃或未涉及公共能力时说明 capability_key、复用方式和验证，技术元数据包含 `capability_map_update_status`。
- 主展示包含“项目信号”判断；对人或 AI 有提示意义的澄清、缺口、口径变更、风险或 AI 前置条件更新时说明 signal_id，技术元数据包含 `project_signal_update_status`。
- 主展示包含“仓库身份”判断；涉及种子仓、主仓、平台项目仓、客户项目仓、混合仓、角色目录覆盖、MCP、客户同步、发布、密钥或外部交付时说明 declared roles、detected roles、有效约束和是否更新身份地图，技术元数据包含 `repository_identity_update_status`。
- 已确认用户口径时，主展示沿用用户叫法，并在技术元数据中用 `user_terms_style` 说明是否新增、沿用或未涉及。

## 冲突与覆盖规则

- 用户明确指定输出格式时优先用户最新要求。
- 任务包要求的固定字段仍要保留，但放入“技术元数据”。
- 如果因为阻塞无法验证、提交、推送或同步 mirror，先用中文说明真实阻塞，再在技术元数据中记录状态。
- 如果用户最新要求只要极简回答，也不能省略高风险必填参数的获取步骤和建议选项；可以压缩成短句。
