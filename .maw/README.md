# .maw 项目控制配置

本目录存放 MultiAgentWorker 项目的控制配置、Codex 上下文、组件清单、环境、发布和脱敏策略。

## 文件职责

- `codex-context.md`：给 Codex 的项目级背景和工作入口。
- `agent-briefing.md`：给 Planner、Executor、Reviewer、Release Manager 等 Agent 的协作说明。
- `agent-entry.yaml`：Mawflow Seed 的通用 AI 工作目录入口协议，定义启动顺序、项目事实、禁止路径、验证入口和收口协议。
- `agent-rules.yaml`：多 Agent 共享规则源，用于对齐 `AGENTS.md`、`CLAUDE.md`、`GEMINI.md` 和 `.cursor/rules/mawflow.md` 等工具适配文件。
- `project.yaml`：项目基础信息和仓库模式。
- `interaction.yaml`：人机交互默认值，记录默认中文输出、中文人类优先收口顺序、双受众 `i18n` 描述字段和发布确认文案。
- `upgrade-policy.yaml`：项目升级和模板升级的风险分级、取舍矩阵和保护边界。
- `template-source.yaml`：共享源模板来源占位、git 来源和 Seed 来源通道；统一“种子仓库/模板仓库”口径，并提供派生项目能力来源追踪字段；个人本机路径和内部私有源覆盖写入 `.local/.maw/template-source.yaml`。公开仓不会导出该文件；外部项目如需声明来源，可复制 `template-source.example.yaml` 为 `template-source.yaml` 后按项目事实修改。
- `template-source.example.yaml`：公开安全的 Seed 来源示例，默认指向 `https://github.com/mawflow/mawflow-seed`。
- `components.yaml`：端和组件清单。
- `modules.yaml`：功能模块机器索引，连接 module_key、模块档案、页面/API/数据表、配置、发布和测试边界。
- `module-candidates.yaml`：渐进式模块发现索引，用于记录 seed/candidate/provisional 模块、证据和提升条件。
- `health/`：项目健康上下文目录，保存健康问题、需求事实、决策、普通健康待办、审计缺口、调研会话摘要和验收缺口，供 Mawflow 主项目和 AI 健康关注导入。
- `app-runtime.yaml`：按 app_key 组织的 AI 调试运行索引，帮助 AI 找到启动入口、URL、数据库引用和测试账号引用。
- `repositories.yaml`：内部仓库、仓库级镜像、按组件映射的外部客户仓库、组件镜像仓库和同步关系。
- `customer-repository-rules.yaml`：客户仓库同步/客出范围规则，记录白名单路径、客户仓子目录、整仓替换开关和执行前方案文件位置，人工可按项目调整。
- `environments.yaml`：本地、测试、预发、生产环境说明，以及 dev/pro/local 配置档规则。
- `environments.dev.yaml`：可提交的开发/测试环境覆盖配置；test 默认 Docker-first，但已有测试机、共用数据库或用户特别说明时，先摸清现有环境并确认后填写。
- `environments.pro.yaml`：可提交的生产环境覆盖配置。
- `releases.yaml`：发布目标、默认发布环境、环境选项、发布快捷指令、发布策略、审批和回滚要求。
- `policies.yaml`：脱敏、保密、禁提交和交付策略。
- `secrets.example.yaml`：公开安全的密钥配置示例。
- `secrets.yaml` / `secrets.dev.yaml` / `secrets.pro.yaml`：仅限受信任私有派生项目按自身安全策略使用；公开 Seed 不导出这些文件，公开项目不得提交真实密钥。
- `*.local.yaml`：本机覆盖配置，优先级最高，不提交 git。
- `.maw/<domain>.d/*.yaml`：同一配置域的拆分片段；片段顶层可写 `enabled: false` 暂不参与合并，适合测试/正式客户仓分支、不同镜像目标等预先配好后按需启用。

公开 Seed 默认不提交真实密钥。`.maw/secrets.yaml`、`.maw/secrets.dev.yaml`、`.maw/secrets.pro.yaml` 不进入公开发布 payload，也不应在公开派生项目中保存真实密钥。公开仓只提供 `.maw/secrets.example.yaml` 等示例文件；真实凭证应写入 `.local/`、运行环境变量、宿主机密钥管理、mawsec / mawlocal / mawproxy 引用，或受信任私有派生项目自己的安全配置中。

受信任私有派生项目如果确实需要使用 `.maw/secrets*.yaml`，必须由项目自身安全策略确认，并确保外部交付、公开发布、诊断包、日志和客户仓同步前完成脱敏。`.maw/*.local.yaml` 只用于本机路径、临时账号和个人覆盖，必须被 `.gitignore` 忽略。

业务代码相关配置的权威来源始终在 `code/<app_key>/` 内部工程文件中，例如 `.env.example`、框架配置、构建配置和路由配置。`.maw/app-runtime.yaml` 只为 AI 和人工协作提供调试索引，模板默认按 `server`、`client` 区分后端和前端；如项目确实存在独立管理后台、设备端、运营端等独立构建或发布目标，应按项目实际新增 app_key。若与 code 内配置冲突，以 code 为准并同步修正 `.maw`。

SSH key 可以放在仓库根目录 `.ssh/`，也可以放在团队约定的任意公共目录；路径可写相对路径或绝对路径。`.ssh/` 下真实 key 文件必须被 git 忽略，只保留说明文件。

客户仓很大时，`external_mapped.components.<component>.external.local_repository_path` 可指向本机预克隆客户仓。真实本机路径请写入 `.maw/repositories.local.yaml` 或 `.local/.maw/repositories.yaml`，不要提交共享配置；共享 `.maw/repositories.yaml` 只保留空占位和说明。

可提交文档、提示词、报告、交付说明和 AI 最终输出中，凡指向当前项目目录或文件的路径，一律写项目根相对路径，避免多台设备协作时混入某台机器的项目绝对路径。远程服务器 workdir、公共 SSH key 目录、URL 和第三方系统路径不是项目目录路径，可保留原始形式。

当 `project.repository_mode` 为 `external_mapped` 时，`.maw/repositories.yaml` 的 `external_mapped.components.<component>` 可为 `code/server`、`code/client` 或项目新增的 `code/<app_key>` 分别配置客户仓库。组件目录必须保持为本仓库普通源码目录，不保存客户仓库 `.git`、submodule 或 worktree 信息。客户仓库同步必须人工显式触发，默认流程是先从指定客户仓库 pull 到本仓库组件，冲突在本仓库解决并提交后，再通过临时客户仓库工作副本 push 允许范围。客户仓库可能包含其它团队或其它模块代码，客出范围必须由 `.maw/customer-repository-rules.yaml` 明确授权；默认只允许白名单路径，禁止整仓替换。

仓库级镜像用于把当前项目仓库分支和 tags 推送到整仓 mirror。AI 每次成功推送项目仓库后，应先执行 `ops/scripts/sync-repository-mirror.sh plan`，以有效计划判断是否继续执行 `ops/scripts/sync-repository-mirror.sh push --execute`；不要只凭原始 `repository_mirrors.enabled=false` 判断未启用，因为 `.local/.maw/repositories.yaml` 本机 overlay 或模板仓库兼容字段可能启用 mirror。

当 `.maw/repositories.yaml` 的 `component_mirrors` 启用时，可按 app_key 把 `code/<app_key>` 的已提交快照同步到目标镜像仓库。镜像仓库是单向目标，只允许当前项目仓库同步到目标仓库；禁止从镜像仓库 pull、merge、rebase 或反向覆盖当前项目。

`.maw/modules.yaml` 用于长期迭代开发的模块定位。AI/Codex 遇到 `module_key`、模块名、页面 URL、页面路径、接口路径、命令名、文件路径或数据表名时，应先用它定位一级模块、子模块和叶子模块；只能定位到一级模块且任务输入是 URL/API/命令/文件时，先读对应 `README.md` 和 `route-api-index.md`，再按需读取二级模块 `module.md`、`pages/`、`backend/` 或 `traceability.md`。不要为了建立上下文全量读取 `docs/modules/**`。`docs/archive/**` 是历史归档，默认不自动读取。

`.maw/health/` 用于保存可被 AI 和 Mawflow 主项目导入的健康上下文。它不替代 `docs/planning/todos/` 的跨模块被依赖待办事实源，不替代 `docs/project-review-audits/` 的完整评审/审计报告，也不替代正式需求、验收、模块档案或部署文档。AI 推断的事实必须标记为 `ai_inferred`、`uncertain` 或待确认状态，用户或权威来源确认后才能写 `confirmed`。

`.maw/module-candidates.yaml` 用于证据不足时的渐进式模块发现。`seed`、`candidate` 和边界不稳定的 `provisional` 模块先留在候选索引和 `docs/modules/_discovery/`，只有满足确认和证据条件后才提升到 `.maw/modules.yaml` 与正式模块档案。

`.maw/interaction.yaml` 用于统一项目内 AI/Codex 的人类可见输出、项目文档语言和最终收口形态。默认输出、任务提示词、提交信息、最终说明、新增或改写的项目文档、任务包正文、模块档案、component guide 和 README 补充段落均使用中文；配置描述采用“中文给人读、英文给 AI 读”的双受众策略，默认展示字段写中文，英文说明放入 `i18n.ai.en-US`，中文说明可放入 `i18n.human.zh-CN`。英文还可保留在代码标识、文件名/路径、命令、协议名、第三方库原文、机器字段 key、品牌/专有名词或用户明确要求的英文内容中。最终说明先展示结论、变更、验证、Git/镜像、模块与记忆、种子仓库升级建议、发布影响和 code 交付影响，再把稳定机器字段放入技术元数据。收口中如需用户补参数、回答问题或做确认，必须给出参数获取步骤、建议选项和填写格式；涉及敏感参数时，先在 `.local/` 下创建本机填写文件，让用户本机填写。

`.maw/upgrade-policy.yaml` 和 `.maw/template-source.yaml` 用于升级策略。项目升级必须先解析源模板来源、盘点目标项目事实和源模板变化，再生成取舍矩阵；源模板仓库中的模板升级必须生成迁移说明、提示词或任务包等升级资产。派生项目中的 `#模版升级/#模板升级` 使用 `template_source.source_channel` 先判断来源通道，再用 `template_source.applied_version` 记录的已应用模板 commit 计算落后源模板多少提交，最后生成当前会话执行提示词并执行。个人本机源模板路径和内部私有源覆盖不写入公开文档，统一放 `.local/.maw/template-source.yaml` 或受控内部配置。

`template_source.source_channel` 区分内部来源通道、`public_seed` 和 `unknown_legacy`。内部派生项目通过受控源或本机 overlay 读取升级资产；外部公开派生项目默认使用 `public_seed`，通过 `https://github.com/mawflow/mawflow-seed` 读取公开升级资产；历史项目缺少字段时按 `unknown_legacy` 兼容，输出证据并要求人工确认后再继续自动升级。

“种子仓库”和“模板仓库”统一指 `maw-project-template`。派生项目可通过 `.maw/template-source.yaml` 的 `seed_repository_relationship.capability_origin_tracking` 追踪能力来源；旧项目缺字段时按兼容处理。派生项目开发中如果发现适合回流种子仓库的优化或新增能力，应记录到 `docs/seed-repository-upgrade-candidates.md`，并可通过 `#种子仓库升级` 生成一段在种子仓库执行的任务提示词。

## 配置聚合规则

每个配置域都兼容单文件读取，例如 `.maw/releases.yaml`。

如果存在同名目录 `.maw/releases.d/*.yaml`，读取配置时必须自动聚合进去，且独立文件优先级高于默认文件。

拆分片段支持顶层 `enabled` 开关：`enabled: false` 表示跳过该片段，`enabled: true` 或省略时参与合并；顶层 `enabled` 只作为片段元数据，不进入最终配置。同类片段如果会覆盖相同字段，同一时间只启用一份。

可提交配置按 profile 叠加：

```text
.maw/<domain>.yaml
.maw/<domain>.d/*.yaml
.maw/<domain>.dev.yaml 或 .maw/<domain>.pro.yaml
.maw/<domain>.dev.d/*.yaml 或 .maw/<domain>.pro.d/*.yaml
.maw/<domain>.local.yaml
.maw/<domain>.local.d/*.yaml
```

`local` 永远最后读取，优先级最高。
未显式传入 profile 时，脚本优先使用 `MAW_PROFILE`，否则使用 `.maw/project.yaml` 的 `configuration_profiles.default_profile`。

统一读取方法见 `docs/configuration-guide.md`，推荐使用：

```bash
python3 ops/scripts/maw-config-merge.py environments --profile dev
python3 ops/scripts/maw-config-merge.py secrets --profile pro
python3 ops/scripts/maw-config-merge.py app-runtime --profile dev
```
