# MultiAgentWorker 项目模板仓库说明

本文件是种子开发仓的维护入口地图；根目录 `README.md` 是种子开发仓和公开仓的产品首页。使用 Seed 创建业务项目后，派生项目应把自己的根 README 改为真实项目说明；模板升级或模板化改造不得整文件覆盖目标项目 README。派生项目 README 初稿位于 `docs/public-seed/template-project-readme.md`。

本仓库是 MAW 创建新研发项目时使用的官方种子仓库。每次创建新项目时，可以从本模板拉取目录、配置、文档、Codex 上下文和发布/脱敏策略；它不是已有项目的整包覆盖工具，已有项目只能按取舍矩阵做增量迁移。“种子仓库”和“模板仓库”统一指本仓库 `maw-project-template`。

Mawflow v1.1 对外口径中，本仓库承接 **Mawflow Seed 开源版**：一个公开 AI Coding 研发装备包。公开入口见 `MAWFLOW_SEED.md`，使用说明见 `docs/public-seed/`，最小 Pack 示例见 `examples/mawflow-packs/`。公开 Seed 不包含主仓 Orchestrator、Workbench、Platform MCP、HostCommand、ActionRun、Secret Governance 运行时代码、客户数据、内部 prompt、hidden workspace 或真实 secret。正式开源 gate 以 MIT `LICENSE`、`docs/public-seed/open-source-release.md` 公开目标和 `ops/scripts/check-seed-open-source-readiness.sh --strict` 为准；发布操作仍需确认 GitHub 仓库对外可见、默认分支和 tag/release 策略。

## 支持场景

1. **仅我方仓库模式**：客户没有代码仓库，我方仓库是主开发仓库和交付源。
2. **客户仓库映射模式**：客户已有 GitLab/GitHub/Gitea 等仓库，我方仓库作为 AI/人工协作主仓库；`code/` 下每个组件可独立配置客户仓库，但组件目录始终只是本仓库普通源码目录，不保存客户仓库 `.git`。人工显式触发时，按分支角色执行客入、客主、客出和客户合主：`CUSTOMER_BASE -> INTERNAL_DEV`、`INTERNAL_DEV -> INTERNAL_RELEASE`、`CUSTOMER_BASE -> CUSTOMER_DELIVERY`、`INTERNAL_RELEASE -> CUSTOMER_DELIVERY`、`CUSTOMER_DELIVERY -> CUSTOMER_INTEGRATION -> CUSTOMER_BASE`。分支名全部可在 `.maw/repositories.yaml` 或 `.maw/repositories.d/*.yaml` 片段配置；测试/正式等同构多分支场景可用顶层 `enabled` 预配置后按需启用。客户仓很大时，可在本机 overlay 配置 `external.local_repository_path`，客入先更新本机预克隆仓再从本地目录读取，客出/客主/客户合主用它作为 clone reference。旧项目未配置 `branch_roles` 时继续回退到 `external.default_branch`。客户只有一个分支时支持 `single_with_temporary_delivery` 或 `single_direct`，其中直推唯一分支需要更高安全门禁。
3. **仓库级镜像模式**：为整个项目仓库配置 mirror remote。项目仓库 push 成功后，默认按 `repository_mirrors.auto_sync_after_project_push: true` 自动同步仓库级镜像；关闭该开关后只推送项目主仓库。
4. **组件镜像仓库模式**：为 `code/<app_key>` 配置只出不进的目标镜像仓库。镜像仓库只能从当前项目仓库同步到目标仓库，禁止从镜像仓库拉取、合并或反向覆盖当前项目。
5. **派生项目能力回流**：派生项目开发中发现通用协作、脚本、配置、提示词或收口规则优化时，记录为种子仓库升级候选，并生成在本仓库执行的提示词。
6. **待办任务治理**：开发闭环中暂不实现但被当前流程依赖的能力，记录到 `docs/planning/todos/`，保留当前假设、受影响模块、完成/取消影响和联调建议。
7. **技术地图与项目提示元数据**：通过 `.maw/capabilities.yaml`、`.maw/project-signals.yaml` 和 `ops/scripts/extract-project-metadata.py`，把公共能力、功能基类、API 快照、待办、澄清、缺口、口径变更和 AI 前置条件提供给项目审计、巡检和人看的数据大屏。
8. **宿主机项目 MCP 绑定治理**：区分宿主机用途、项目归属、开发绑定、源码访问方式和 MCP 暴露面，支持客户宿主机开发客户项目或平台授权项目，同时保留完整源码通道只属于可信平台宿主机。
9. **项目健康上下文**：通过 `.maw/health/` 记录健康问题、需求事实、决策、普通健康待办、审计缺口、调研会话摘要和验收缺口，为 Mawflow 主项目导入、AI 主动健康关注和调研会话预留结构化载体。

## 人类使用入口

- 派生项目 README 初稿：`docs/public-seed/template-project-readme.md`，创建业务项目时由项目负责人改成真实项目介绍。
- Mawflow Seed 公开入口：`MAWFLOW_SEED.md`，面向开源用户说明 Seed 是什么、如何开始、公开边界和当前阻塞项。
- Mawflow Seed 公开文档：`docs/public-seed/`，包含 quickstart、Prompt Spec、Pack 类型、脱敏和贡献规则。
- Mawflow Pack 示例：`examples/mawflow-packs/`，展示 Prompt Pack、Task Pack、Check Pack 和 Verification Pack 的最小结构。
- 新手指南：`GETTING_STARTED.md`，面向第一次使用本模板的人，记录初始化操作和快速入门。
- 常用指令目录：`PROJECT_COMMANDS.md`，面向人类快速查触发词和指令概要；AI 执行细则仍以 `docs/ai-instructions/` 为准。
- 用户版完整设计：`docs/template-repository-design.md`，面向项目负责人、开发者和客户侧技术负责人理解模板设计。
- AI 版设计协议：`docs/template-repository-ai-design.md`，面向 Codex/Agent/Reviewer 按需读取完整执行协议。
- 设计同步清单：`docs/template-repository-design-sync.md`，用于判断用户版设计和 AI 版设计何时需要同步。
- 种子仓库升级候选记录：`docs/seed-repository-upgrade-candidates.md`，用于派生项目记录可回流到本仓库的优化或新增能力。
- ChatGPT 到 Codex 任务交接协议：`CHATGPT_TO_CODEX.md`，面向网页端 ChatGPT、其它外部 AI 和人类，用于把已确定方案整理成 Codex 可执行任务或任务提示词工程 zip。

## 给 Codex 的第一条规则

开始任何开发、配置、文档或脚本任务前，以 `.maw/codex-context.md` 为最小启动上下文的权威来源。该文件会列出当前需要读取的 `.maw` 配置、docs 入口和任务相关端目录说明；本总览只保留入口地图，不复制完整启动清单，避免两处规则漂移。

`docs/**` 必须按需读取：先看 `docs/README.md` 和相关子目录 `README.md`，再根据任务类型读取具体文档或章节。不要为了建立上下文全量读取 `docs/**`。

如果任务中包含 `module_key`，必须先从 `.maw/modules.yaml` 定位模块；如果只能定位到一级模块或中间模块组，先读取对应 `README.md` 的子模块菜单，再按需读取叶子模块 `module.md`。如果用户只提供模块名、页面路径、接口路径或数据表名，也必须先尝试用 `.maw/modules.yaml` 缩小上下文边界，不要全量读取 `docs/modules/**`。

完成任何由 AI 执行的代码、配置、文档或脚本改动后，AI 必须在完成验证后提交并推送当前分支；commit message 和提交内容说明必须使用中文，清楚记录本次变更范围、验证结果和未完成事项。如果项目配置了启用的仓库级镜像且 `auto_sync_after_project_push` 为 `true`，AI 推送项目仓库成功后必须继续同步仓库级镜像。

输入资料整理、提示词、报告、交付说明和 AI 最终输出中，凡涉及当前项目目录或文件路径，一律使用项目根相对路径，例如 `code/server`、`docs/requirements/README.md`。如果用户输入里包含某台设备上的项目绝对路径，写入可提交文档或复用提示词前必须改写为相对路径；远程服务器 workdir、公共 SSH key 目录、URL 和第三方系统路径不受此限制。

每次任务完成时，AI 最终说明必须判断本轮修改了 `code/` 下哪些组件应用和 app_key。涉及代码、运行配置、构建、发布覆盖层、部署脚本或线上可见行为变化时，对应组件必须给出发布判断，例如“本轮修改了 server 的运行配置，需要发布 server 才会生效，当前未发布”；如果需要发布但当前未发布或未验证，必须按 app_key 从 `.maw/releases.yaml` 与 `code/<app_key>/.maw.component.yaml` 读取默认环境、可选环境、版本状态策略和可复制的 `#发布` 快捷指令，并在收口末尾询问是否“确认发布全部”。多个组件需要发布时，分别列出指令，用户可以复制其中一条或多条选择部分发布；中文环境口令未指定组件时，先按 `remote_server.default_release_components` 取得候选范围，再按 `artifacts/release-state/<env>/<app_key>.json` 的已发布 commit 和组件路径差异筛选实际发布名单。用户回复“确认发布全部/确认/是/全部发布”时按项目发布流程执行全部待发布组件的 SQL/迁移、构建、发布覆盖、健康检查、发布记录和发布状态文件更新；`发布上线` 与 `发布生产` 执行前必须确认本地候选 commit 等于发布来源远端分支；如果未命中 code 组件应用，应写明“未命中 code 组件应用，无需更新发布”。

每次最终说明还必须判断是否发现新的种子仓库升级建议。发现时，写明候选记录位置、使用场景、优化/新增理由和向下兼容要求；未发现时，也写明“未发现新的种子仓库升级建议”。

## 目录概览

- `.maw-template/`：模板仓库自身元信息，用于项目初始化和模板版本管理。
- `.maw/`：AI/人工协作用控制配置目录，支持 base、dev/pro、local 三层配置自动聚合，并按 app_key 记录 AI 调试索引。
- `.maw/health/`：项目健康上下文目录，保存可被主项目和 AI 导入的健康问题、事实、决策、调研摘要和验收缺口；示例在 `examples/`，不代表当前项目事实。
- `.ssh/`：可选的仓库本地 SSH key 存放目录；真实 key 文件被忽略，只提交说明文件。
- `code/`：业务代码根目录，默认以 `server` 和 `client` 表示后端与前端；模板不内置 `admin`，如项目确实需要独立后台前端，应按项目实际新增 app_key。
- `.local/`：本机资料、本机配置 overlay 和维护者本机记录目录，默认只提交 README 说明；其中 `.local/.maw/` 可覆盖同名 `.maw` 配置，`.local/docs/requirements/raw/` 存放用户原始大文件资料，`.local/maintenance/` 可存放模板仓库自身 mirror remote 等本机维护记录。
- `docs/`：需求、AI 编码边界、功能模块档案、设计、计划、验收、交付文档，其中 `docs/requirements/raw/` 存放原始资料分析结果 Markdown。
- `docs/modules/`：功能模块档案目录，配合 `.maw/modules.yaml` 维护模块边界、实现程度、页面/API/数据表边界、证据字段、过期状态和 changelog；`docs/modules/_audits/` 记录模块地图检查、审计、查漏补缺和 `module_map_score`。
- `docs/modules/_discovery/`：渐进式模块发现区，记录候选模块、证据和待确认问题，证据不足时不生成正式 leaf。
- `docs/technical-map/`：技术地图入口，说明开发前如何查询 modules、capabilities、project signals、任务和验收。
- `docs/repository-identity/`：仓库身份地图入口，说明种子仓、主仓、平台项目仓、客户项目仓、混合仓和历史未分类仓的多角色约束。
- `docs/capabilities/`：公共能力说明和能力档案模板，机器可读索引在 `.maw/capabilities.yaml`；其中 `host-project-mcp-governance.md` 说明宿主机项目 MCP 绑定治理，`seed-open-source-readiness-audit.md` 说明种子仓公开开源前的额外审计。
- `docs/project-signals/`：项目提示信号说明和模板，机器可读索引用于巡检、大屏和 AI 前置读取。
- `docs/planning/todos/`：待办任务治理目录，记录被业务闭环依赖但暂不实现、先假设已完成的跨模块缺口和联调/回归建议。
- `docs/archive/`：历史归档目录，AI/Codex 默认永不自动读取。
- `docs/ai-coding/`：AI 编写代码前必须遵守的边界、代码风格、工程规范和初始化待办清单。
- `docs/ai-instructions/`：项目内可被 Codex 精准命中的指令、专有名词、关键词候选、经验索引和方案详情库。
- `docs/seed-repository-upgrade-candidates.md`：派生项目记录适合回流到种子仓库的候选优化或新增能力。
- `ops/`：本地、测试、预发、生产环境说明和脚本。
- `prompts/`：Codex、Agent、外部分析工具提示词和可恢复任务提示词工程，manual-only，不是默认上下文。
- `docs/template-migrations/`：模板新特性同步给派生项目时的迁移说明。
- `prompts/codex/template-upgrade-prompts/`：模板升级轻量提示词资产。
- `release/`：发布随带文件覆盖层和规则，强制按 `release/<component>/default` 与 `release/<component>/<app_key>` 分层叠加。
- `artifacts/`：任务记录、执行结果、发布记录和交付包归档。
- `reports/`：日报、周报、审计报告；`reports/audits/` 保存种子仓分发就绪等可复查审计。
- `tests/`：跨端冒烟和 E2E 测试。

## 关键资料归档规则

### 用户原始需求

- 用户直接提供的 Word、PDF、图片、聊天记录导出、邮件正文、原始表格和压缩包，放入 `.local/docs/requirements/raw/`，不提交 git。
- 当用户要求分析原始资料时，把分析结果以 Markdown 写入 `docs/requirements/raw/`。
- 分析结果建议按 `YYYYMMDD-来源-主题-analysis.md` 命名，并记录来源文件、核心结论、需求线索、风险点和待确认问题。
- 不要直接修改原始需求文件；可确认的需求沉淀到 `docs/requirements/requirement-baseline.md`，待确认问题沉淀到 `docs/requirements/pending-questions.md`。

### 本机维护资料

- `.local/maintenance/` 存放当前仓库维护者本机专用记录，例如模板仓库自身的 GitHub mirror remote、一次性同步检查清单和临时排障备注。
- `.local/.maw/` 存放当前 checkout 专用的同名 `.maw` 配置 overlay，读取时优先覆盖项目 git 中的同名配置。
- `.local/config/` 存放不进入 `.maw` 聚合配置的本机辅助配置；如果某个本机覆盖需要被 Python 工具稳定读取，应改用 `.local/<same-path>`。
- 模板仓库自身的 GitHub mirror 目标不得写入 `.maw/repositories.yaml`、`docs/ai-instructions/` 或提示词；这类信息只属于维护者本机 `.git/config` 或 `.local/maintenance/`。
- 同步模板到已有项目时，只同步 `.local/**/README.md` 说明文件，不同步 `.local/` 下真实资料、维护记录和本机配置。

### 外部分析提示词

- 通过 ChatGPT、Claude、Gemini 或其他外部工具分析项目后产出的任务提示词，放入 `prompts/external-analysis/`。
- 每个提示词文件应说明来源、输入资料、适用端、目标任务和人工复核结论。
- 可复用到 Codex 会话的提示词，再整理迁移到 `prompts/codex/`。

### 项目指令与经验

- 项目内固定流程、专有名词、环境别名、模块俗称和复盘经验，放入 `docs/ai-instructions/`。
- `docs/ai-instructions/README.md` 是总纲，必须罗列当前项目已登记的指令、术语和经验，并链接到完整说明文档。
- `docs/ai-instructions/experience-index.md` 是经验命中索引，AI 可以主动检索；较大的具体解决方案放入 `docs/ai-instructions/solutions/`，必须先从索引、候选台账或用户明确路径命中后再读取。
- 用户在 Codex 会话中说“新增指令”“记录经验”“记住这个术语”等时，AI 应更新对应条目和总纲索引。
- 指令库只保存可复用协作知识，不保存真实密钥、账号密码、客户隐私或生产连接串。

### 发布随带文件

- 发布时需要额外覆盖进端代码目录或发布包的文件，统一放在 `release/<component>/default` 或 `release/<component>/<app_key>`。
- 覆盖规则写在 `release/rules.yaml`，默认先叠加公共 `default`，再叠加当前发布目标的 `app_key`。
- `release/` 仅存放发布随带文件，不存放构建产物、日志、缓存、用户上传文件或裸凭证文件。
- 如历史项目中存在误拼写目录 `realse/`，应迁移到 `release/` 后再发布。

### AI 编码边界

- AI 开始实现任务前，先按 `docs/README.md` 进入 `docs/ai-coding/README.md`，再按任务风险读取初始化清单、模块档案规则、代码风格或端说明；不要全量读取 `docs/ai-coding/**`。
- AI 完成任何实际改动后，必须提交并推送代码；commit message 和提交说明必须使用中文记录变更内容。若启用仓库级镜像且自动同步开关为 true，推送项目仓库成功后继续同步镜像。
- 用户明确给出的代码边界、风格偏好和禁改范围，放入 `docs/ai-coding/user-provided-rules.md`。
- AI 对现有工程分析后总结出的目录结构、架构约束、代码风格和风险点，放入 `docs/ai-coding/ai-analysis-rules.md`。
- 各端工程目录说明放入 `docs/ai-coding/component-guides/`，并与 `code/<component>/.maw.component.yaml` 保持一致。
- 项目内短语、别名、固定流程和经验沉淀放入 `docs/ai-instructions/`，不要混写进一次性提示词。
- 初始化清单未完成前，不应开展大规模功能开发，只允许做资料归档、只读分析和规则补齐。

## 初始化建议

新项目初始化后，至少需要修改：

- `.maw/project.yaml`
- `.maw/components.yaml`
- `.maw/repositories.yaml`
- `.maw/environments.yaml`
- `.maw/releases.yaml`
- `.maw/secrets.yaml`
- 如需完整字段，参考 `.maw/secrets.example.yaml`
- `.maw/modules.yaml`，先按模块树和 group/leaf 调整模块索引。
- `.maw/module-candidates.yaml`，证据不足的新项目先登记候选模块和提升条件，不强行生成正式模块树。
- `.maw/health/`，按项目事实逐步登记健康问题、事实、决策、调研摘要和验收缺口；初始化时保留空清单，示例不要复制成真实项目事实。
- `.maw/upgrade-policy.yaml` 和 `.maw/template-source.yaml`，配置项目升级/模板升级策略和共享源模板来源占位；个人本机模板路径写入 `.local/.maw/template-source.yaml`。
- `docs/modules/<...>/<leaf>/module.md`，为每个核心功能 leaf 补齐模块档案。
- `.maw/releases.yaml` 和每个 `code/<app_key>/.maw.component.yaml` 的 `release`，为每个启用组件配置默认发布环境、可选发布环境、按环境发布快捷指令和版本状态策略；发布成功后按 `artifacts/release-state/<env>/<app_key>.json` 记录已发布 commit。

默认组件按前后端两类理解：`server` 是后端/API，`client` 是前端或用户侧应用。`admin`、`mobile`、`worker` 等只能由创建向导或项目事实按需启用；模板不把它们作为默认必启组件。如果项目确实存在独立后台代码、构建或发布目标，应按项目实际新增前端 app_key。模块档案不要停留在 `server`、`client` 这种 component 粒度，应按业务域继续拆成 group 和 leaf。

本模板默认信任受控开发节点、AI 节点和私有 git 仓库，继续兼容把项目协作必需的真实密钥提交到 `.maw/secrets.yaml`、`.maw/secrets.dev.yaml`、`.maw/secrets.pro.yaml`；新项目推荐优先使用 `mawsec://`、`mawlocal://`、`mawproxy://` 或宿主机本地 SecretStore。可信私有仓库中的明文检查默认 warning，不阻断协作；公开仓库、发布包、日志、诊断包、外部交付、客户仓库同步或显式严格模式必须 block 或先脱敏。本地机器差异写入 `.maw/*.local.yaml`，不提交 git。种子仓若准备公开开源，先运行 `bash ops/scripts/check-seed-open-source-readiness.sh --strict`，确认 `LICENSE`、`docs/public-seed/open-source-release.md` 和公开 Git remote 均满足 gate；开源种子仓只是公开装备包，主仓中枢和 MCP/HostCommand/Approval 链路仍负责 loop 控制。

业务代码相关配置以 `code/<app_key>/` 内部工程文件为权威来源，例如 `.env.example`、框架配置、构建配置和路由配置。为了方便 Codex 或其它 AI 调试，`.maw/app-runtime.yaml` 会按 `server`、`client` 和项目实际新增 app_key 显式记录调试 URL、数据库引用、API 地址引用和测试账号引用。

如需仓库级镜像，在 `.maw/repositories.yaml` 的 `repository_mirrors.targets.default` 填写 mirror remote 或 URL，并确认 `repository_mirrors.enabled`、目标 `enabled` 和自动同步开关均已打开，才会让 AI 在项目仓库 push 成功后自动同步整仓 mirror。需要关闭自动同步时，把全局或目标级 `auto_sync_after_project_push` 改为 `false`。

如需客户仓库映射，在 `.maw/repositories.yaml` 的 `external_mapped.components.<app_key>` 填写客户仓库 URL、组件路径、凭证引用和分支角色；通用分支角色写在 `sync.branch_roles`，组件差异写在 `external_mapped.components.<app_key>.sync.branch_roles`。客出范围和白名单继续维护在 `.maw/customer-repository-rules.yaml`。

如需组件镜像仓库，在 `.maw/repositories.yaml` 的 `component_mirrors.components.<app_key>` 填写目标仓库，并在 `.maw/components.yaml`、`.maw/app-runtime.yaml` 和 `code/<app_key>/.maw.component.yaml` 中保留 `mirror_repository_ref`。组件镜像仓库同步只允许当前项目仓库到目标仓库，使用 `ops/scripts/sync-to-mirror-repo.sh` 人工显式触发。

`test` 默认指本地测试，也就是本地调试模式，代码改动应尽量即改即生效，通常不需要 SSH 凭证；`发布测试` 等同本地调试，默认不部署远端编译包。`发布上线` 才把编译包部署到 `remote_staging_server`，这是编译后的测试/联调环境，部署包和运行环境按发布生产对齐；`发布测试` 和 `发布上线` 都允许当前工作区未提交改动参与测试发布，并在发布记录中写明 dirty snapshot。`发布生产` 部署到 `remote_production_server`，执行前必须确认发布来源分支和工作区干净。只有项目特别指定独立远端测试机时，才在 `.maw/environments.dev.yaml` 中填写 `remote_test_server` 主机、SSH 用户和工作目录，并在 `.maw/secrets.yaml` 中填写对应凭证；旧脚本读取 `remote_test_server` 且配置缺失或为空时可从 `remote_staging_server` 读取同名字段。默认本地和线上可连接同一个数据库以方便联调，改数据库指向或生产共库前必须记录风险、备份和回滚策略。Git 参数是可选项；不填写时默认使用本机 git 环境、当前 remote、SSH agent、`~/.ssh/config` 或 credential helper。需要固定 AI/部署节点凭证时，优先使用项目级 SSH deploy key；需要 API/PR/CI 能力时再使用细粒度 token。获取步骤见 `docs/git-credentials-guide.md`。

## 日常维护规则

- 页面、接口、数据表、配置、状态流、发布规则、external_mapped 同步边界发生变化后，必须判断是否同步更新对应 `docs/modules/<module-key>/module.md` 和 `changelog.md`。
- 当前业务流程依赖暂不实现的能力时，必须判断是否登记到 `docs/planning/todos/active.md`；完成或取消后移入 `closed.md`，并同步受影响模块档案和联调/回归建议。
- 开发新功能、接口、公共基类或横切能力前，先查 `.maw/capabilities.yaml`，避免重复实现；对人或 AI 有提示意义的澄清、缺口、口径变更或审计提示进入 `.maw/project-signals.yaml`。
- 无法确定正式 `module_key` 时，先把 `module_candidate`、证据和待确认问题写入 `.maw/module-candidates.yaml` 与 `docs/modules/_discovery/`，不要把 seed/candidate 直接写入正式 leaf。
- 仓库级镜像或组件镜像仓库配置、同步方向、脱敏规则、自动同步开关或目标仓库边界变化后，必须判断是否同步更新 `.maw/repositories.yaml`、`docs/repository-mirror-sync-guide.md`、`docs/component-mirror-repository-guide.md`、项目指令和相关模块档案。
- 任务提示词中的项目关键词如果反复出现，或会影响模块、页面、接口、数据表、环境、发布目标边界，必须判断是否更新 `docs/ai-instructions/keyword-candidates.md` 或正式术语文档。
- 实现、修 bug、测试、构建、发布、同步或执行脚本前，必须用任务关键词、路径、命令名、错误症状和 app_key 检索 `docs/ai-instructions/experience-index.md`；不得主动全量读取 `docs/ai-instructions/solutions/**`。
- 用户澄清、说明、纠偏和有复用价值的边界补充，应提取标题、关键词和内容摘要，暂存到 `docs/ai-instructions/experience-candidates.md`；多次适用后升级为正式经验或指令。
- AI 执行中先用错命令、运行时、脚本入口、测试方式或调试方式，随后找到正确方法时，应把可复用经验暂存到 `docs/ai-instructions/execution-lesson-candidates.md`。
- 复杂需求、产品方案或长期实施计划应优先沉淀为 `prompts/codex/task-packs/<slug>-codex-tasks/` 任务提示词工程，并包含 `manifest.json`、`prompts/00-session-runbook.md` 和独占 `SESSION_STATE.md` 恢复协议。
- 如果不更新模块档案，AI/Codex 最终说明必须写明原因。
- AI/Codex 最终说明必须列出本轮修改的 code 组件应用和发布更新状态，尤其是需要发布才会生效的组件要写清“本轮修改了哪个 app_key、发布哪个 app_key 才会生效、当前已发布/当前未发布”；需要发布但当前未发布或未验证时，还必须按 app_key 给出可复制 `#发布` 快捷指令，并在收口末尾询问是否“确认发布全部”，多个组件时支持用户复制指令选择部分发布。
- `docs/archive/**` 只保存历史资料；除非用户明确给出具体归档文件路径或要求历史追溯，AI/Codex 默认永不自动读取。
- 同步模板到已有项目时，只按取舍矩阵增量补 `.maw/modules.yaml`、`docs/modules/_template/`、`docs/archive/README.md` 等缺失协议文件，不整包覆盖目标项目，不覆盖已有模块档案、项目私有文档、真实 secrets、`.maw/*.local.yaml`、客户仓库映射或业务代码。
- 执行 `#项目升级` 时，必须先生成升级取舍矩阵，再按风险等级增量合并；执行 `#模板升级/#模版升级` 时，在模板仓库生成迁移说明、轻量提示词或任务包，不直接修改目标项目；执行 `#种子仓库升级` 时，在派生项目记录回流候选并生成一段在种子仓库执行的任务提示词。
- 如果已有项目已经有模块文档，只补缺失字段或生成迁移说明，由人工确认合并。

## 设计和使用说明

- 配置读取说明：`docs/configuration-guide.md`
- Git 凭证说明：`docs/git-credentials-guide.md`
- 客户仓库同步说明：`docs/customer-repository-sync-guide.md`
- 仓库级镜像同步说明：`docs/repository-mirror-sync-guide.md`
- 组件镜像仓库同步说明：`docs/component-mirror-repository-guide.md`
- 模板用户版完整设计：`docs/template-repository-design.md`
- 模板 AI 版设计与执行协议：`docs/template-repository-ai-design.md`
- 模板设计同步清单：`docs/template-repository-design-sync.md`
- 模板使用说明：`docs/template-usage-guide.md`
