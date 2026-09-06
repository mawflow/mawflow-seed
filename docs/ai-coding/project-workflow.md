# 项目工作流程与高级治理规则

本文件按任务需要读取；默认启动顺序统一以 `.maw/agent-entry.yaml` 为准。

`docs/**` 必须按需读取：先读 `docs/README.md` 和相关子目录 `README.md`，再根据任务类型读取具体文件或章节。不要为了建立上下文全量读取 `docs/**`。配置、Git 凭证、客户仓库同步、AI 编码、需求、设计、计划、验收、交付和项目指令文档，都只有在当前任务命中对应场景时才读取。

涉及模板架构、项目升级、模板升级、任务提示词协议、模块发现、技术地图、公共能力、项目提示元数据、`.local`、项目记忆、中文收口、code-only 交付或生成交付文档时，按需读取 `docs/template-repository-ai-design.md`。该文件是完整设计与执行协议，不加入每次任务默认必读清单。

如果任务包含 `module_key`，必须先读取 `.maw/modules.yaml` 定位模块；如果只定位到一级模块或中间模块组，先读取对应 `README.md` 的子模块菜单，再按需读取叶子模块 `doc`。如果用户提到模块名、页面 URL、页面路径、接口路径、命令名、代码文件或数据表名，先用 `.maw/modules.yaml` 缩小范围；只能定位到一级模块时，再读取该一级模块 `route-api-index.md` 快速落到二级模块，不要全量读取 `docs/modules/**`。具体页面或后端审计只读取二级模块内命中的 `pages/`、`backend/` 或 `traceability.md`。只有执行 `#模块地图：检查/审计/清理过期/变更影响/发布前检查`、追溯 `last_audit_id` 或确认 stale/deprecated 文档时，才读取 `docs/modules/_audits/` 的具体报告。复杂模块如果配置了 `ai_doc` 或存在 `ai-context.md`，只在实现、审查、修 bug、发布判断或 AI 易误读时读取；不要给所有模块批量生成 `_ai` 副本。

开发新功能、接口、公共基类、组件、脚本或横切能力前，先查询 `.maw/capabilities.yaml` 和 `docs/technical-map/README.md`，确认是否已有可复用 `capability_key`。涉及模板升级、客户同步、MCP、发布、密钥、外部交付或 code-only 导出前，先查询 `.maw/repository-identity.yaml` 和 `docs/repository-identity/README.md`，确认 declared roles、detected roles、角色目录覆盖和有效约束；涉及 MCP、客户同步、发布、密钥或外部交付时，还要读取 `.maw/environments.yaml` 的 `host_project_binding` 或运行 `ops/scripts/extract-project-metadata.py --section host-project-mcp`，确认宿主机用途、项目归属、开发绑定、源码访问方式和 MCP 暴露面；角色或绑定不一致时普通开发 warning，高风险操作先人工复核，MCP 角色/绑定错配 fail closed。遇到对人或 AI 有提示意义的待办、澄清、缺口、口径变更、风险、审计提示或 AI 前置条件时，判断是否更新 `.maw/project-signals.yaml`；跨模块被依赖待办仍以 `docs/planning/todos/active.md` 为事实源，项目信号只做摘要和回链。需要给巡检、大屏或 AI 前置读取时，使用 `ops/scripts/extract-project-metadata.py` 输出 JSON/Markdown。

如果无法确定正式 `module_key`，先读取 `.maw/module-candidates.yaml` 和 `docs/modules/_discovery/README.md`，记录 `module_candidate`、证据和待确认问题。证据不足时不要强行创建正式 leaf `module.md`。

## 工作原则

- 初始化清单未完成前，只做资料归档、只读分析、规则补齐和低风险整理。
- 修改代码前先确认端边界、禁改路径、测试要求和发布影响。
- 读取 `.maw` 配置时必须使用聚合规则：基础配置、`dev/pro` profile 覆盖、本地 `local` 覆盖依次叠加，`local` 优先级最高。
- 面向用户的输出默认使用 `.maw/interaction.yaml` 约定的中文、人类优先收口；新增或改写的项目文档、任务包正文、模块档案、component guide 和 README 补充段落也默认使用中文。配置、升级资产、能力索引、项目信号和仓库身份等机器可读文件采用“双受众”策略：默认展示字段给人读时写中文，英文主要给 AI 或机器读取，放入同一对象的 `i18n.ai.en-US`；中文说明可放入 `i18n.human.zh-CN`。英文还可保留在代码标识、文件名/路径、命令、协议名、第三方库原文、机器字段 key、品牌/专有名词或用户明确要求的英文内容中；不要因为模板文件名、Markdown 标题习惯或外部库文档是英文，就把目标项目可维护文档写成英文。日常默认简化主展示，验证区用可读结论说明覆盖范围和风险，不用命令清单替代结论；用户要求详细收口、展开验证、审计版或验证异常/高风险场景时，再展开命令明细和完整技术元数据。
- 业务代码相关配置以 `code/<app_key>/` 内部工程文件为权威来源；`.maw/app-runtime.yaml` 只为 AI 调试提供按 app_key 区分的入口、URL、数据库引用和测试账号引用。
- `.maw/subprojects.yaml` 组织独立交付单元，`.maw/code-sources.yaml` 登记共享 Git 身份，`.maw/deployments.yaml` 登记可重复的服务器部署目标与显式组件范围。组件仍是 app_key、构建、运行和发布叶子。真实源码目录绑定写入 `.local/.maw/code-source-bindings.yaml`；托管 clone 默认位于被外层 Git 明确忽略的 `.local/code-sources/<source-key>/`。云端只同步声明和脱敏 readiness，不同步绝对路径、凭据、源码、分支工作区或未提交改动。
- `external_mapped` 模式下，客户仓库按组件配置在 `.maw/repositories.yaml` 的 `external_mapped.components.<component>`；`code/<component>` 必须保持普通目录，不得保存客户仓库 `.git`、submodule 或 worktree 信息。同步只能由人工显式触发，且只能使用配置指定的客户仓库 URL 或临时工作副本；顺序是先拉客户仓库到本仓库组件，解决冲突并提交本仓库，再推送组件到客户仓库。
- 仓库级镜像默认配置在 `.maw/repositories.yaml` 的 `repository_mirrors`；AI 每次成功推送项目仓库后，必须先运行 `ops/scripts/sync-repository-mirror.sh plan`，以计划输出中的 `Configured`、`Config source`、`Auto sync`、`Target enabled` 和 `Target auto sync` 判断是否继续执行 `ops/scripts/sync-repository-mirror.sh push --execute`。不要只凭原始 `repository_mirrors.enabled=false` 判断未启用，因为聚合配置、`.local/.maw/repositories.yaml` 本机 overlay 或模板仓库兼容字段可能使有效计划启用镜像。普通业务提交后的 mirror 同步默认保留记录；如果本次项目仓库提交只是为了提交上一轮 mirror 记录，执行 `push --execute --no-record` 避免记录提交循环。
- 发布公开镜像使用 `.maw/repositories.yaml` 的 `repository_publish_mirrors` 和 `ops/scripts/publish-repository-mirror.sh`；它只在人工显式 `publish --execute` 时把定版版本发布到公开仓，不参与普通 push 后自动 mirror，也不得用 `MAW_FORCE_REPOSITORY_MIRROR_SYNC=1` 替代公开发布审批。
- `component_mirrors` 组件镜像仓库按 app_key 配置在 `.maw/repositories.yaml` 的 `component_mirrors.components.<app_key>`；镜像仓库是单向目标，只允许当前项目仓库同步到目标仓库，禁止从镜像仓库 pull、merge、rebase 或反向覆盖当前项目。
- 输入资料整理、提示词、报告、交付说明和 AI 最终输出中，涉及当前项目目录或文件路径时必须写项目根相对路径；用户输入里的本机项目绝对路径落库前应改写为相对路径。唯一例外是模板仓库生成给目标项目执行的模板升级提示词，可以在“本机模板仓库目录”字段写入生成时当前模板仓库的绝对路径，并要求目标会话先检查路径存在，不存在再兜底。
- 用户提供规则优先于 AI 分析规则。
- 用户消息命中项目内指令、专有名词、别名或经验主题时，按需读取 `docs/ai-instructions/README.md`，再进入最匹配的完整说明文档。
- 执行较复杂任务时，快速扫描用户消息和任务提示词中的项目关键词、习惯用语和别称；如果关键词多次出现、影响模块/页面/API/表/发布边界或后续收口口径，按 `docs/ai-instructions/instructions/keyword-learning-loop.md` 更新候选台账或正式术语。用户补充的澄清、说明和纠偏如有复用价值，应暂存到 `docs/ai-instructions/experience-candidates.md`。AI 自己试错后找到正确方法的可复用经验，应暂存到 `docs/ai-instructions/execution-lesson-candidates.md`。
- 每次实现、修 bug、测试、构建、发布、同步或执行脚本前，必须用任务关键词、路径、命令名、错误症状和 app_key 检索 `docs/ai-instructions/experience-index.md`；命中后才读取索引指向的 `lessons/**`、`solutions/**` 或指令全文。不得为了了解经验库主动全量读取 `docs/ai-instructions/solutions/**`。
- 模块任务必须按需读取并遵守 `docs/ai-coding/module-dossier-rules.md`：页面、API、数据表、状态流、配置、发布或外部同步边界变化后，判断是否更新模块档案和集中 changelog；遇到旧格式先自动迁移到 `docs/changelogs/`。
- 新项目或证据不足的模块拆分任务必须先走渐进式模块发现：候选写入 `.maw/module-candidates.yaml` 和 `docs/modules/_discovery/`，正式稳定模块才写入 `.maw/modules.yaml`。
- 项目升级和模板升级必须策略先行、取舍矩阵先行。`#项目升级` 按用户输入、`.local/.maw/template-source.yaml`、`.maw/template-source.yaml`、当前仓库解析源模板；共享配置不得写个人本机模板路径。`#模版升级/#模板升级` 未指定 commit 时先按当前仓库角色路由：源模板仓库生成升级资产；派生项目走 `TINST-026`，先识别来源属于受控内部来源、`public_seed` 或 `unknown_legacy`，再用 `template_source.version`（默认 `main`）解析目标模板 commit，并与 `template_source.applied_version` 计算落后提交数，生成当前会话执行提示词并继续执行；外部公开项目不得读取内部私有 Seed 源，不要误走 `#项目升级`。如果仓库角色、来源通道或触发词含义有歧义，先问清楚再执行。
- “种子仓库”和“模板仓库”统一指 `maw-project-template`。派生项目应知道自己来自种子仓库，并尽量区分能力来源：`seed_repository`、`derived_project_custom`、`candidate_for_seed_repository` 或 `unknown_legacy`；旧项目缺少来源字段时按兼容处理，不阻塞开发。
- 派生项目开发中如果发现适合回流到种子仓库的优化或新增能力，必须在收口中明确指出，并记录到 `docs/seed-repository-upgrade-candidates.md`，写清使用场景、优化/新增理由、证据路径和向下兼容要求。需要生成在种子仓库执行的提示词时，走 `#种子仓库升级` / `TINST-027`；该流程是派生项目到种子仓库的反向回流，不等同于 `#项目升级` 或 `#模板升级/#模版升级`。
- `docs/archive/**` 是历史归档，AI/Codex 默认永不自动读取；只有用户明确给出具体归档文件路径或要求历史追溯时，才读取最小必要片段。
- 受信任私有 git 可以提交 `.maw/secrets.yaml`、`.maw/secrets.dev.yaml`、`.maw/secrets.pro.yaml`；`.maw/*.local.yaml`、日志、缓存、构建产物和用户上传文件不得提交。
- `.local/` 是本机资料、同名配置 overlay 和维护目录；Python 配置读取器会把 `.local/<same-path>` 作为最高优先级 overlay。真实原始资料、本机辅助配置、具体浏览器调试命令、端口/代理/工具路径、模板仓库自身 mirror remote 记录和一次性排障资料只留在本机，不作为项目指令、`AGENTS.md` 内容或默认 `.maw` 配置提交。
- 任务开始时按关键词检索项目记忆：`docs/ai-instructions/README.md`、`experience-index.md`、候选台账和相关正式术语/经验；如果任务可能受最近几次会话、跨设备接力、任务包续做或刚发生的提交影响，先运行 `python3 ops/scripts/recent-session-briefs.py --recent 8 --query "<当前任务>" --format markdown`，只在相关度为 high/medium 时读取对应 `docs/ai-session-briefs/**`；如任务涉及本机差异，再读取 `.local/ai/README.md`、`.local/config/README.md` 或 `.local/device.example.yaml` 的示例规则。
- AI 日常开发时，如果发现将来生成用户手册、概要设计、部署手册有价值的事实，应分别沉淀到 `.maw/modules.yaml` 和 `docs/modules/`、`docs/design/`、`ops/`；必要时可以自主新增合适的 Markdown 文档和 README 入口。生成交付文档只使用这些权威来源生成 Markdown 事实稿，不把事实稿当作最终正式文档。
- 任务结束时在最终说明中报告 `memory_update` 和 `local_update`：项目共享术语、用户澄清、长期偏好和执行经验沉淀到 `docs/ai-instructions/`；本机路径、端口、工具链、代理、浏览器调试和本机临时状态留在 `.local/`。派生自本种子仓库的项目执行或排查发布后，涉及本机/环境差异的发布经验必须沉淀到 `.local/ai/` 或 `.local/maintenance/` 的被忽略文件，避免重复踩坑。
- 任务中发现当前业务闭环依赖一个暂不实现的能力、先假设已完成，或用户说新增/完成/取消/查询待办时，走 `TINST-028`，使用 `docs/planning/todos/active.md` 和 `closed.md` 记录影响模块、取消后果和完成后联调建议；模块档案只回链 TODO-ID。
- 任务中发现项目健康问题、需求事实、关键决策、普通健康待办、审计缺口、调研会话摘要、验收缺口，或用户说记录/审计项目健康、生成健康关注建议、主仓导入 `.maw/health` 时，走 `TINST-038`，使用 `.maw/health/` 保存轻量健康上下文；跨模块被依赖待办仍走 `TINST-028`，完整项目评审/审计仍走 `TINST-037`，AI 推断事实不得写成 confirmed，变更后运行 `python3 ops/scripts/check-project-health-context.py --format json`。
- 任务中发现可复用公共能力、功能基类、API 快照、脚本或治理协议时，走 `TINST-030`，使用 `.maw/capabilities.yaml` 记录能力 key、实现路径、消费模块、复用策略和验证方式；模块档案只引用 `capability_key`。
- 任务中发现对人或 AI 有提示意义的澄清、缺口、口径变更、审计/巡检提示或 AI 前置条件时，走 `TINST-030`，使用 `.maw/project-signals.yaml` 记录结构化 signal，并按需同步 `docs/ai-instructions/experience-candidates.md` 或 `keyword-candidates.md`。
- 任务中涉及仓库身份、种子仓/主仓/平台项目仓/客户项目仓/混合仓/历史未分类仓、多角色约束或角色检测时，走 `TINST-031`，使用 `.maw/repository-identity.yaml` 和 `.maw/repository-identity.d/<role>/*.yaml` 记录基础身份与角色差异化覆盖；不能只依赖声明值，必须结合目录结构和关键文件检测角色。
- SSH key 可放在仓库根 `.ssh/` 或团队公共目录，但真实 key 文件不得提交 git。
- 同步客户仓库、仓库级镜像、组件镜像仓库、导出交付包、写外部提示词前，必须移除或脱敏真实密钥、内部服务器、内部账号和生产连接串。
- 根目录 `README.md` 属于业务项目，`TEMPLATE_OVERVIEW.md` 才是模板仓库说明。模板升级或模板化改造不得整文件覆盖目标项目 README；如需补入口，只做最小段落合并。
- 每次新增或调整内容后，必须判断是否需要同步更新项目 README、`TEMPLATE_OVERVIEW.md`、`docs/`、`.maw/`、端工程说明、模块档案或发布/运维文档；若不需要，在最终说明中简要说明原因。
- 最终说明应包含 `experience_lookup` 和关键词/经验学习判断：是否检索 `docs/ai-instructions/experience-index.md`、命中哪些经验、是否读取详情、是否更新 `docs/ai-instructions/keyword-candidates.md`、`docs/ai-instructions/experience-candidates.md`、`docs/ai-instructions/execution-lesson-candidates.md`、`docs/ai-instructions/terms/`、`docs/ai-instructions/lessons/` 或 `docs/ai-instructions/solutions/`，未更新时说明原因。已确认含义的用户习惯用语和别称，收口主展示优先使用用户口径；技术元数据 key 保持稳定。每次收口还必须判断 `seed_repository_upgrade_suggestions`：未发现、已记录、已生成提示词、已在种子仓库执行，或仅适合当前项目。
- 最终说明如果需要用户补参数、回答问题或做人工确认，必须给出参数用途、具体获取步骤、建议选项和填写格式；涉及 token、cookie、密码、私钥、生产连接串、客户隐私或内部账号等敏感参数时，先在合适的 `.local/` 位置创建本机填写文件，让用户本机填写并回复确认，不要要求用户直接粘贴明文。
- 最终说明必须判断 `module_key`、`module_dossier_updated`、`module_dossier_reason`、`updated_module_docs`、`hit_code_components`、`todo_task_update_status`、`health_context_update_status`、`capability_map_update_status`、`project_signal_update_status`、`repository_identity_update_status`、`release_update_status`、`release_commands`、`release_confirmation_prompt`、`local_environment_status`、`local_test_entry`、`local_update_commands`、`local_environment_install_hint` 和 `seed_repository_upgrade_suggestions`；默认收口只展示有实际信息量或用户决策需要的字段，详细收口、审计或任务包固定格式再输出完整技术元数据。
  - 每次完成任务时都要判断本轮修改了 `code/` 下哪些组件应用，以及是否需要刷新或开启本地开发/测试环境；根 `npm run dev` 是默认本地调试验收入口，已实现且正在运行时，收口应提示进入调试地址查看改动生效；未实现时引导派生项目把真实本地环境命令接到 `dev` 或 `local:dev`，并输出 `127.0.0.1` 与局域网访问链接；项目已配置本地环境时，应在收口提供入口 URL、健康检查、关键页面/API 或验证命令，未配置时提示 `#安装开发环境`。
  - 只有修改组件代码、运行配置、发布覆盖、部署脚本或线上可见行为时，才写该组件“需要发布才会生效”。若需要发布但当前未发布或未验证，必须从聚合后的 `.maw/releases.yaml` 和 `code/<app_key>/.maw.component.yaml` 读取默认环境、环境选项、版本状态策略和 `#发布` 快捷指令，按 app_key 给出可复制指令；多个 app_key 需要发布时支持部分发布，用户可以复制其中一条或多条组件指令只发布对应组件。
  - 用户说 `发布测试`、`发布上线`、`发布生产` 或兼容口令 `发布生成` 且未指定组件时，先读 `.maw/releases.yaml` 的 `releases.defaults.release_command_aliases` 和 `.maw/environments.yaml` 对应 `remote_server.default_release_components` 取得候选范围，再按 `artifacts/release-state/<env>/<app_key>.json` 的发布版本状态和组件路径差异筛选实际发布名单；`发布测试` 通常基于本地环境安装或开启目标组件、部署或启动程序，并提供可访问调试地址；`发布上线` 是在线上服务器完成编译包部署测试并提供线上可访问地址，它仍属于测试；`发布生产` 是部署到 `remote_production_server`，涉及生产环境安装、生产服务器部署或生产版本上线时必须写明人工审计状态。
  - `发布上线` 与 `发布生产` 执行前必须确认本地候选 commit 等于发布来源远端分支，`发布测试` 不强制该检查。收口末尾必须询问是否“确认发布全部”，用户回复“确认发布全部/确认/是/全部发布”则发布全部待发布组件，包括 SQL/迁移、构建、发布覆盖、健康检查、发布记录和发布状态文件更新。
- 种子仓准备定版、正式分发、模板基线公告或大范围派生项目升级前，必须运行 `bash ops/scripts/check-seed-distribution-readiness.sh`，并查看 `reports/audits/20260617-seed-distribution-readiness.md`。
- 每次 AI 完成一段任务、任务包子任务或其它可独立验证的里程碑后，只要产生了代码、配置、文档或脚本改动，就必须完成必要验证、提交并推送当前分支，并按仓库级 mirror 有效计划同步镜像；不要等用户再次要求“提交 push”。commit message 和提交内容说明必须使用中文，记录变更范围、验证结果和遗留风险。推送成功后必须先运行 `ops/scripts/sync-repository-mirror.sh plan`，以计划输出判断是否继续同步仓库级镜像。
- 推送收口时必须先只暂存、提交、推送本次任务实际改动。该提交完成后重新运行 `git status --short`；若仍有其它文件变动，只有确认剩余变动全部位于 `code/**` 之外，且不属于 `.maw/*.local.yaml`、`.local/`、`.ssh/**`、日志、缓存、构建产物或真实密钥等禁提交范围时，才允许追加一个独立中文 commit message 的补充提交并推送。剩余 `code/**` 组件业务代码、组件运行配置或组件内文件变动不得顺手纳入补充提交，必须保持未暂存并在最终说明中列出。
- 只有用户明确禁止 git 写入、没有实际变更、存在无法安全暂存的无关脏改动，或认证、网络、分支保护、远端拒绝导致无法 push 时，才可跳过提交或推送；最终说明必须写清失败原因、当前 commit hash 或未提交状态，以及需要人工处理的下一步。
