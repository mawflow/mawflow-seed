# 模板变更记录

## Unreleased

- 暂无。

## v0.2.26 - 2026-07-10

- 修复主仓公开 payload 对 `.maw`、`.maw-template`、`.github` 等根级隐藏目录规则失效的问题，公开发布改由单一 release gate 清单驱动物化。
- 新增 `PUBLIC_PAYLOAD_MANIFEST.json`、公开 workdir 自检脚本和产物级 smoke，要求真实物化 payload 的核心入口、配置、文档、任务包模板、CI 和安全边界全部可验证。
- 修复种子仓 CI 遗留 Ruby 入口并改为自动发现完整测试；公开 payload CI 使用独立 smoke，内部种子开发仓继续运行 source-only 完整 gate。
- 将仓库级镜像脚本的 Bash 4 `mapfile` 改为兼容 macOS 默认 Bash 3.2 的读取循环。
- 统一 Seed 产品定位、种子仓/派生项目 README 所有权和公开任务包示例，公开候选不再携带内部来源或私有文件存储地址。

## v0.2.25 及更早版本

- 升级到 `v0.2.25`，对当前 Mawflow Seed 种子开发仓状态做定版发布：承接 `v0.2.24` 已完成的开源仓 README 口径重构、公开 payload 准入和镜像同步结果，提升 `TEMPLATE_VERSION`，形成新的 `release/v0.2.25` / `v0.2.25` 开发仓版本基线。
- 升级到 `v0.2.24`，重构 MAWflow Seed 公开仓 README 口径：将根 `README.md` 调整为面向公开 GitHub 首页的正式说明，明确 Seed 是开源 AI 项目导航系统，校准 Seed / Host Base / Project Space / Studio / Enterprise 的产品关系，补齐正式目录结构、升级路径、联系方式和 MIT License 说明，并避免把 Seed 写成普通脚手架、云端平台或 AI 自动开发承诺。
- 升级到 `v0.2.23`，新增 AI 工作目录入口协议：把 Mawflow Seed 的公开定位收敛为安装在 AI 编程工作目录里的开源辅助系统，新增 `AI_START_HERE.md`、`.maw/agent-entry.yaml` 和 `.maw/agent-rules.yaml`，让 Codex、Claude Code、Gemini CLI、Cursor Agent 等本地 AI coding tools 进入目录后先读取项目事实、模块边界、禁止路径、验证入口和收口协议；同步公开 Seed 说明、能力索引、项目信号、迁移说明、升级提示词和分发/开源检查。
- 升级到 `v0.2.22`，修复 Mawflow Seed 公开候选密钥策略阻塞：`.maw/README.md` 不再鼓励公开项目提交真实 `.maw/secrets*.yaml`，明确公开 Seed 只导出示例密钥文件，真实凭证应进入 `.local/`、环境变量、宿主机密钥管理或 mawsec / mawlocal / mawproxy 引用；同时保留受信任私有派生项目按自身安全策略使用 secrets 文件的兼容说明。
- 升级到 `v0.2.21`，对修复后的 Mawflow Seed 公开候选 payload 边界做种子开发仓定版发布：承接 `v0.2.20` 的 public-safe `.maw/template-source.example.yaml`、公开 payload allowlist 和 admission gate 结果，形成新的 `release/v0.2.21` / `v0.2.21` 开发仓版本基线。
- 升级到 `v0.2.20`，对当前 Mawflow Seed 种子开发仓状态做定版发布：延续 `v0.2.19` 已完成的 public-safe Seed payload、公开发布契约和镜像同步能力，提升 `TEMPLATE_VERSION`，形成新的 `release/v0.2.20` / `v0.2.20` 开发仓版本基线。
- 修复 `v0.2.20` 公开候选 payload 审计阻塞：公开导出不再依赖内部开发源 `.maw/template-source.yaml`，新增 public-safe `.maw/template-source.example.yaml`，并在公开快速开始、开源发布清单和 `.maw` 说明中补齐公开来源文件边界。
- 升级到 `v0.2.19`，修复 Mawflow Seed 公开 payload 发布阻塞项：根 `README.md` 改为 public-safe Seed 入口，业务项目 README 模板迁入 `docs/public-seed/template-project-readme.md`；公开导出的 AI 指令、任务包说明、模块模板、健康上下文示例和开源发布说明清理内部来源标记、私有命名空间、本机用户标记和固定 PM 系统字段；补齐 public payload 相对链接，并让公开 payload gate 达到 `internal_keyword_hits=0`、`secret_pattern_hits=0`。
- 升级到 `v0.2.18`，新增发布镜像手动发布能力：`repository_publish_mirrors` 独立于普通 `repository_mirrors` 自动同步，支持私有开发仓定版后人工发布到公开仓；新增 `ops/scripts/publish-repository-mirror.sh`，默认 plan、显式 `publish --execute` 才写远端，支持 `same_git_history` 和 `export_sanitized_tree` 两种模式，并串联版本、tag、分发就绪、开源就绪、本机边界和 code 交付检查；新增 `#发布公开镜像` / `TINST-039`、配置指南、能力档案和升级资产。
- 升级到 `v0.2.17`，新增 FTP/FTPS 覆盖部署通道与仓库级多镜像同步：`environments.<env>.remote_server.deployment` 支持 `ftp/ftps`、`full_overwrite/managed_sync`、保留路径和计划先行；新增 `ops/scripts/deploy-via-ftp.py`，可信私有项目配置可明文保存 FTP URL 但发布记录、日志、诊断包、客户同步和外部交付必须脱敏；`repository_mirrors.default_targets` 支持多个整仓 mirror target，`sync-repository-mirror.sh` 支持 `--all`。
- 升级到 `v0.2.16`，新增项目健康上下文标准：用 `.maw/health/` 保存可被 Mawflow 主项目、Codex、ChatGPT 和其它 AI Agent 读取的健康问题、需求事实、决策记录、普通健康待办、审计缺口、调研会话摘要和验收缺口；新增 `#项目健康` / `TINST-038`、`project-health-context` 能力、项目信号、`ops/scripts/check-project-health-context.py`、迁移说明和派生项目升级提示词。`.maw/health/` 不替代正式需求、测试、部署手册、模块档案、项目评审报告或跨模块待办事实源，AI 推断必须和用户确认事实区分。
- 升级到 `v0.2.15`，新增项目评审与审计治理：`#项目评审` 让 AI 作为需求评审会主讲人，基于 docs 复述项目目标、业务流程、验收目标和口径冲突；评审报告存档到 `docs/project-review-audits/rounds/<review_id>/review.md`，并固定给出 `#项目审计：<评审报告路径>` 接续调用；`#项目审计` 基于评审报告审计实现程度、证据、缺口和后续推进建议，未经人工确认的 AI 评审结论不得直接回写 docs。
- 统一本地测试、线上发布和测试服务器回退口径：本地测试默认指本地调试模式，改动应尽量即改即生效；线上发布本质是编译后的测试/联调环境，部署包和运行环境按发布生产对齐；默认本地和线上可连接同一个数据库；`remote_test_server` 配置缺失或为空时从 `remote_staging_server` 读取同名字段。
- 升级到 `v0.2.14`，增强模块地图治理：`#模块地图` 增加初始化、检查、审计、查漏补缺、清理过期、变更影响和发布前检查子模式；模块模板、一级索引、页面/后端审计页和追踪矩阵新增 `doc_status`、`confidence`、`last_verified_commit`、`source_paths`、`last_audit_id` 等证据字段；新增 `docs/modules/_audits/` 审计报告模板和 `module_map_score` 评分维度，支持定期查漏补缺、标记 `stale/deprecated` 文档并保持渐进式补全。
- 升级到 `v0.2.13`，修复种子仓测试与脚本契约开箱体验：根 pytest 自动加入项目根导入路径，配置测试隔离本机 `.local` overlay；`run-project-tests.py` 不再把只有 `.gitkeep` 的占位 tests 目录误判为 pytest 命令，并把 pytest “no tests ran” 视为 skipped；`download-task-pack-url.py`、`maw-git-credential.py`、`write-session-brief.py` 补齐 `--format json|markdown|text`；同步升级资产、迁移说明和派生项目提示词。
- 增加默认简化收口与详细收口展开策略：`TINST-020` 默认只展示结论、关键变更、验证结论、入口/发布影响和必要下一步，用户要求 `#详细收口`、展开验证或遇到验证异常/高风险/审计/交接场景时再展开命令明细和完整技术元数据；新增 `final-closeout-response-protocol` 能力、项目信号、迁移说明和派生项目升级提示词。
- 升级到 `v0.2.12`，新增模块地图协议：一级模块可维护 `route-api-index.md` 快速把页面 URL/API/命令定位到二级模块，二级模块继续以 `module.md` 为事实源，并按需维护 `pages/`、`backend/`、`traceability.md` 审计页；新增 `#模块地图` / `TINST-036`、模板文件、能力/项目信号、迁移说明和派生项目升级提示词，保持渐进式补全和 `pending_confirm` 兼容。
- 增加直接 fork 派生项目模板升级路由防护：仓库身份检测要求源模板仓的 Git `origin` 匹配 `template_source.git_url`，避免 fork 项目继承 `seed_repository` 声明后把 `#模板升级/#模版升级` 误路由到 `TINST-024`；同步更新 `TINST-024/TINST-026/TINST-031`、迁移说明、升级提示词和回归测试。
- 新增最近会话概要能力：用 `docs/ai-session-briefs/` 保存可跨设备同步的一会话一文件概要，新增 `recent-session-briefs` 能力、`#会话概要` / `TINST-034`、`ops/scripts/recent-session-briefs.py` 和 `ops/scripts/write-session-brief.py`，任务开始只读轻量候选，命中相关后再细读具体概要或 `SESSION_STATE.md`。
- 新增文档写读契约与文档索引能力：用 `.maw/doc-taxonomy.yaml`、front matter 和 `doc-read-contract` 约束新写产品/需求/设计/模块/计划文档的可读元数据，新增 `extract-doc-index.py`、`check-doc-read-contract.py`、`TINST-033` / `#文档索引`、模板迁移说明和派生项目升级提示词；历史文档默认 warning-only，当前模板已对 `docs/design`、`docs/modules`、`docs/planning`、`docs/requirements` 和关键入口文档完成首轮基线补齐。
- 增加测试契约漂移防护：当产品口径、PM 源称谓、API 摘要、状态标签或静态 UI 文案调整时，要求同步搜索并更新 pytest/static 断言，运行聚焦 pytest 与相关测试入口，避免 CI 因旧字面量断言反复失败；新增 `test-contract-drift-guard` 能力、项目信号、经验条目、迁移说明和派生项目升级提示词。
- 升级到 `v0.2.11`，强化派生项目反向升级种子仓库闭环：增强 `#种子仓库升级` / `TINST-027`，新增自动发现信号、S0-S4 候选分级、`needs_more_evidence` 状态和 `prompts/codex/seed-repository-upgrade-prompts/` 反向提示词目录，登记 `seed-repository-feedback-loop` 能力、项目信号、迁移说明和派生项目升级提示词。
- 升级到 `v0.2.10`，新增 AI Python 脚本规范：用 `ai-python-script-contract` 约束 AI 可复用脚本的结构化输出、长日志落盘、可恢复状态、多环境兼容和退出码，新增 `#脚本规范` / `TINST-032`、`ops/templates/ai-python-script.py`、`ops/scripts/check-ai-python-script-contract.py`、迁移说明和派生项目升级提示词；旧脚本默认兼容保留，按审计结果分批升级。
- 升级到 `v0.2.9`，新增宿主机项目 MCP 绑定治理：用 `.maw/environments.yaml` 的 `host_project_binding` 记录 `ownership_type`、`binding_type`、`source_access_mode` 和 `mcp_exposure_profile` 值域，扩展 `#MCP服务诊断`、`host-project-mcp-governance` 能力、项目信号、`extract-project-metadata.py --section host-project-mcp`、迁移说明和升级提示词；保持 MCP 默认关闭，旧项目缺失绑定字段时按 unknown/not_applicable 兼容。
- 升级到 `v0.2.8`，新增仓库身份地图：用 `.maw/repository-identity.yaml` 记录 primary_role、roles、角色检测规则和基础边界，用 `.maw/repository-identity.d/<role>/*.yaml` 维护角色差异化约束覆盖，新增 `#仓库身份` / `TINST-031`、`repository_identity_update_status`、`ops/scripts/check-repository-identity.sh` 和 `extract-project-metadata.py --section repository-identity`，为种子仓、主仓、平台项目仓、客户项目仓、混合仓和历史未分类仓提供可检测、可覆盖、可审计的统一身份口径。
- 升级到 `v0.2.7`，新增技术地图、公共能力索引和项目提示元数据：用 `.maw/capabilities.yaml` 维护可复用 API/基类/脚本/治理能力，用 `.maw/project-signals.yaml` 结构化沉淀待办、澄清、缺口、口径变更、风险和 AI 前置条件，并新增 `ops/scripts/extract-project-metadata.py` 给项目审计、巡检和数据大屏提取 JSON/Markdown。
- 升级到 `v0.2.6`，新增宿主机用途模式、本地项目级 MCP 接入协议、`#MCP服务诊断` / `TINST-029`、能力凭证变量矩阵和客户用途限制；本次只包含模板协议、AI 指令、示例配置、迁移说明和检查脚本，不包含 MultiAgentWorker 主仓平台实现代码。
- 升级到 `v0.2.5`，增强发布指令：按环境和 app_key 记录已发布 commit，新增 `ops/scripts/plan-release-components.py` 根据发布状态与组件路径差异计算实际发布名单，并要求 `发布上线` / `发布生产` 前本地候选 commit 必须等于发布来源远端分支；`发布测试` 不强制该最新代码门。
- 升级到 `v0.2.4`，新增待办任务治理能力：用 `docs/planning/todos/` 记录被当前业务闭环依赖但暂不实现、先假设已完成的跨模块缺口，并新增 `#待办任务` / `TINST-028`、`todo_task_update_status` 收口字段、模块档案 TODO-ID 回链规则和模板升级资产。
- 统一环境服务器命名口径：`test` 默认指本地调试/本地测试环境，`remote_test_server` 仅在显式远端测试机或旧脚本兼容时使用；新增 `remote_staging_server` / `remote_production_server` 口径和本机宿主机能力缺失 warning policy。
- 统一配置工具链为 Python：新增 `ops/scripts/maw-config-merge.py`，移除旧脚本入口，并将同步脚本中的 JSON 解析改为 Python。
- 升级到 `v0.2.3`，统一“种子仓库/模板仓库”口径，新增 `#种子仓库升级`、候选记录台账和收口字段，支持派生项目把可复用优化回流到种子仓库并保持历史项目兼容。
- 增加可选 AI 模块上下文规则：复杂模块可按需创建 `ai-context.md` 并用 `ai_doc` 指向，默认不批量复制 `_ai` 模块副本，保持 `module.md` 为单一事实源。
- 增加客户仓库分支角色模型，支持 `INTERNAL_DEV`、`INTERNAL_RELEASE`、`CUSTOMER_BASE`、`CUSTOMER_DELIVERY`、`CUSTOMER_INTEGRATION` 与客户单分支兼容配置，并内置客入、客主、客出、客户合主指令和脚本入口。
- 优化任务完成后的 git 推送原则：先独立提交并推送本次任务改动，随后仅允许将 `code/**` 之外且非禁提交范围的剩余变动作为补充提交推送，`code/**` 组件业务变动不得顺手带入。
- 增加 `repository_mirrors` 仓库级镜像配置和 `ops/scripts/sync-repository-mirror.sh`，项目仓库 push 成功后可按 `auto_sync_after_project_push` 默认自动同步整仓 mirror。
- 优化发布收口字段：明确“本轮修改了哪个 app_key、需要发布哪个组件才会生效”，提供按组件可复制 `#发布` 指令，并在末尾询问是否全部发布。
- 增加 `docs/ai-instructions/lessons/release/` 发布经验目录，并新增 FastAdmin 服务端发布参考经验，供 fork 项目按需改造。
- 升级到 `v0.2.2`，新增 AI 执行经验候选台账，支持记录错误尝试后的正确方法、触发场景和验证方式。
- 升级到 `v0.2.1`，新增任务关键词学习循环和经验候选台账，支持从任务提示词、用户澄清、说明和纠偏中持续沉淀项目关键词与可复用经验。
- 升级到 `v0.2.0`，新增 `.maw/modules.yaml`、`docs/modules/`、模块档案维护规则、迭代与模块拆分说明、历史归档禁读边界和模板模块文档检查脚本。
- 增加 `docs/requirements/raw/`，用于归档用户原始需求资料。
- 增加 `prompts/external-analysis/`，用于保存外部 AI 或人工分析产出的任务提示词。
- 增加 `release/` 和 `release/rules.yaml`，用于描述各端发布随带文件的覆盖规则。
- 增加 `docs/ai-coding/`，用于约束 AI 编码边界、代码风格、工程目录说明和初始化待办清单。
- 增加 `.maw/` 和 `.maw-template/` 骨架，补齐项目控制配置和模板元信息。
- 增加 `docs/template-repository-design.md` 和 `docs/template-usage-guide.md`，说明模板设计与使用方式。
- 增加文档同步判断约束，要求 AI 在新增或调整内容后判断是否需要更新相关文档。
- 增加 MAW 配置读取协议，兼容 `.maw/<domain>.yaml` 单文件，并自动聚合 `.maw/<domain>.d/*.yaml`，独立文件优先级更高。
- 调整密钥策略：受信任私有 git 可提交 `.maw/secrets.yaml`、`.maw/secrets.dev.yaml`、`.maw/secrets.pro.yaml`，local 覆盖不提交。
- 增加 dev/pro/local profile 配置读取、远程测试服务器配置模板和 git 凭证获取指南。
- 增加实际 `.maw/secrets.yaml` 最小集，并扩展 `.maw/secrets.example.yaml` 为完整注释示例。
- 增加 `.maw/app-runtime.yaml`，按 app_key 维护 AI 调试运行索引；明确业务配置权威来源在 `code/<app_key>/`。
- 增加仓库根 `.ssh/` 作为可选 SSH key 存放目录，真实 key 文件被 git 忽略。
- 增强 `external_mapped` 仓库模式：支持 `code/` 下每个组件独立配置客户仓库，组件目录保持无嵌套 `.git`，并提供人工显式 `plan/pull/push` 同步脚本与完整同步指南。
- 增加 `docs/ai-instructions/`，用于沉淀项目内可被 Codex 精准命中的指令、专有名词和经验总结。

## v0.1.0

- 初始化 MultiAgentWorker 项目模板仓库。
- 支持 internal_only 与 external_mapped 两种仓库模式。
- 增加 Codex 上下文、脱敏策略、发布配置和多端目录。
