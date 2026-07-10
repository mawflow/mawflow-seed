---
doc_key: docs.index
doc_type: governance
stage: governance
status: active
owner: planner
tags:
  - docs
  - index
  - read-contract
project_health:
  dimensions:
    - ai_collaboration
  evidence_level: canonical
read_contract:
  summary: "docs 目录菜单和按需读取路线。"
  health_signal: "用于 AI 任务准备时先定位文档目录、入口和读取边界。"
  consumes: []
  produces: []
  ai_read_hint: "开始涉及 docs 的任务时先读取本文件，再按任务类型读取子目录 README 和必要文档。"
---

# docs 文档目录

用于沉淀需求、设计、计划、验收和交付文档。

## 会话读取约束

AI/Codex 不应在任务开始时全量读取 `docs/**`。本目录采用“总索引 -> 子目录 README -> 任务相关文档 -> 必要片段”的按需读取方式。

默认读取顺序：

1. 先读取本文件，了解 `docs/` 的目录菜单。
2. 根据任务类型、用户关键词、路径、`module_key`、组件、发布目标或验收目标，选择相关子目录。
3. 读取对应子目录的 `README.md`，只看该目录职责和文件菜单。
4. 只读取本次任务必需的具体文档；长文档优先用标题、目录、关键词或相关章节定位，避免整本通读。
5. 如果任务从一个文档跳转到另一个文档，应说明触发原因，例如接口变更需要补 `design/api-design.md`，发布检查需要看 `delivery/release-notes.md`。
6. 完成修改后，只更新受影响的文档；不因顺手整理而改动无关文档。

禁止行为：

- 不要用 `find docs -type f` 后逐个读取全部文档。
- 不要为了“了解项目”通读 `docs/requirements/`、`docs/design/`、`docs/planning/`、`docs/acceptance/`、`docs/delivery/` 或 `docs/ai-instructions/`。
- 不要默认读取 `docs/archive/**`；归档只在用户明确给出路径或要求历史追溯时读取最小必要片段。
- 不要因为命中一个目录就读取该目录下所有文件；先读该目录 README，再按文件职责选择。
- 不要把原始需求、旧方案或交付记录当作当前事实来源；需要确认时与当前代码、`.maw`、模块档案和 active 设计文档交叉核对。

常见任务的推荐入口：

| 任务类型 | 默认入口 | 继续读取条件 |
| --- | --- | --- |
| 功能开发 / 修 bug | `.maw/modules.yaml`、`.maw/module-candidates.yaml`、`docs/modules/README.md`、相关模块组 README | 定位到叶子模块后读 `module.md`；只有页面 URL/API/命令只能定位到一级模块时读该一级模块 `route-api-index.md`；具体页面或后端审计再读二级模块内命中的 `pages/`、`backend/` 或 `traceability.md`；复杂模块可按需读 `ai-context.md`；无法确定正式 module_key 时读 `docs/modules/_discovery/` 并输出 `module_candidate`；执行 `#模块地图：检查/审计/清理过期/变更影响/发布前检查` 时按需写入 `docs/modules/_audits/` 并记录 `module_map_score`；涉及设计时再读 `docs/design/**` |
| AI 工作目录入口 / Agent 启动协议 | `AI_START_HERE.md`、`.maw/agent-entry.yaml`、`.maw/agent-rules.yaml`、`AGENTS.md` | 调整 AI 进入目录后的启动顺序、工具适配规则、禁读路径、验证入口或收口字段时读取；派生项目只做增量合并，不覆盖目标项目事实 |
| 需求澄清 / 范围确认 | `docs/requirements/README.md` | 需要基线时读 `requirement-baseline.md`；需要原始资料分析结果时按主题读 `raw/` 相关 Markdown；用户要求追溯原始资料时再读 `.local/docs/requirements/raw/` |
| 架构 / API / 数据模型 | `docs/design/README.md` | 只读相关的 `architecture.md`、`api-design.md`、`data-model.md`、`page-flow.md` 或 `feature-spec.md` |
| 任务拆解 / 迭代计划 | `docs/planning/README.md` | 按需读项目路线、任务拆解、迭代模块计划、风险清单 |
| 待办任务治理 | `docs/planning/README.md`、`docs/planning/todos/README.md` | 当功能被当前业务闭环依赖但暂不实现、先假设已完成，或用户说新增/完成/取消/查询待办时，读取 `active.md`、`closed.md` 和受影响模块档案 |
| 技术地图 / 公共能力 / 项目提示元数据 | `docs/technical-map/README.md`、`.maw/capabilities.yaml`、`.maw/project-signals.yaml` | 开发新功能/API 前查复用能力、功能基类、API 快照、待办、澄清、缺口、口径变更、审计提示和 AI 前置条件；需要导出给巡检或大屏时运行 `ops/scripts/extract-project-metadata.py` |
| 文档写读契约 / 文档索引 / 项目健康文档来源 | `.maw/doc-taxonomy.yaml`、`docs/doc-read-contract/README.md`、`docs/capabilities/doc-read-contract.md` | 新写或重构产品、需求、设计、模块、计划和审计文档时补 front matter；需要给项目健康、审计或 AI 任务准备文档候选时运行 `ops/scripts/extract-doc-index.py` 和 `ops/scripts/check-doc-read-contract.py` |
| 项目评审 / 项目审计 / docs 口径治理 | `.maw/project-review-audit.yaml`、`docs/project-review-audits/README.md`、`docs/ai-instructions/instructions/project-review-audit.md` | `#项目评审` 用于 AI 会议式复述项目目标、业务流程和验收目标，并生成接续 `#项目审计：<评审报告路径>`；`#项目审计` 基于评审报告审计实现程度、证据和后续推进 |
| 项目健康上下文 / 健康关注建议 / 主项目导入准备 | `.maw/health/README.md`、`docs/capabilities/project-health-context.md`、`docs/ai-instructions/instructions/project-health-context.md` | 记录或审计健康问题、需求事实、决策、普通健康待办、审计缺口、调研会话摘要和验收缺口时读取；跨模块被依赖待办仍走 `docs/planning/todos/`，完整评审报告仍走 `docs/project-review-audits/` |
| 最近会话概要 / 跨设备接力 / 短期上下文 | `docs/ai-session-briefs/README.md` | 任务开始时先运行 `ops/scripts/recent-session-briefs.py` 检索候选，只在相关时读取具体概要；任务结束时用 `ops/scripts/write-session-brief.py` 写入一会话一文件的共享概要 |
| 脚本规范 / 耗时任务降噪 / 多环境脚本升级 | `docs/capabilities/ai-python-script-contract.md`、`docs/ai-instructions/instructions/script-contract-upgrade.md` | 新增或升级 AI 可复用脚本时，优先使用 Python、结构化输出、日志落盘、状态可恢复和多环境兼容；派生项目已有脚本先运行 `ops/scripts/check-ai-python-script-contract.py` 审计，再分批升级；常见测试入口可用 `ops/scripts/run-project-tests.py` |
| 仓库身份 / 多角色约束 / 身份地图 | `docs/repository-identity/README.md`、`.maw/repository-identity.yaml`、`.maw/repository-identity.d/<role>/` | 模板升级、客户同步、MCP、发布、密钥、外部交付或 code-only 导出前确认当前仓库是种子仓、主仓、平台项目仓、客户项目仓、混合仓或历史未分类仓 |
| Docker-first 宿主机运行环境 / 安装环境 / 本地测试入口 / 根 package.json 启动脚本 / 离线镜像 / 本地 PG | `docs/implementation/host-runtime-environments/README.md`、`.maw/environments.yaml`、`package.json`、`docs/capabilities/host-runtime-environment-protocol.md`、`docs/ai-instructions/instructions/install-environment.md` | 配置本地开发宿主机、开发/测试环境、线上/生产环境、离线 Docker 镜像包、本地宿主机 PG 数据面、主仓/平台项目/客户项目环境矩阵，或需要判断是否会破坏既有环境时读取；Docker-first 是默认建议，安装或改造环境前必须先摸清现有运行时、数据库、端口、部署目录、备份和回滚条件并让用户确认；安装测试/开发环境时应把启动命令落到根 `package.json` scripts，验收入口为 `npm run dev`，并输出本机与局域网访问链接；新增可单独运行脚本后用 `npm run scripts:sync:check` 检查命令面板；任务收口时已配置本地环境应提示进入调试地址查看改动生效，未配置时提示 `#安装开发环境` |
| 宿主机用途 / 项目级 MCP / MCP 服务诊断 | `docs/implementation/host-purpose-modes/README.md`、`docs/implementation/local-mcp-gateway/README.md`、`docs/ai-instructions/instructions/mcp-service-diagnostics.md` | 只有配置或排查平台/客户用途宿主机、项目归属、开发绑定、源码访问方式、Codex Shell/App 项目级 MCP、工具授权和跨项目隔离时读取 |
| 代码规范 / AI 边界 | `docs/ai-coding/README.md` | 按需读 AI 主力开发模型、模块档案规则、初始化清单、代码风格或端说明 |
| 项目指令 / 术语 / 经验 | `docs/ai-instructions/README.md`、`docs/ai-instructions/experience-index.md` | 任务前可检索经验索引；只有命中触发词、索引、候选台账、用户明确路径或需要更新候选台账时读具体详情；最终收口默认简化展示，用户要求详细收口或验证异常/高风险时再展开命令和技术元数据 |
| 种子仓库升级建议 | `docs/seed-repository-upgrade-candidates.md`、`docs/ai-instructions/instructions/seed-repository-upgrade.md` | 派生项目开发中发现可复用优化或新增能力时，记录场景、理由、证据和兼容性要求，并生成在种子仓库执行的提示词 |
| 验收 / 测试报告 | `docs/acceptance/README.md` | 按需读验收清单、缺陷清单或测试报告 |
| 发布 / 交付 / 交接 | `docs/delivery/README.md`、`release/rules.yaml`、`.maw/releases.yaml` | 按需读发布说明、交付摘要、交接清单 |
| 客户仓库 / 镜像仓库 / 凭证 / 配置 | `docs/configuration-guide.md`、`docs/secret-governance-guide.md`、`docs/customer-repository-sync-guide.md`、`docs/repository-mirror-sync-guide.md`、`docs/component-mirror-repository-guide.md`、`docs/git-credentials-guide.md` | 仅在配置、同步、凭证、部署或发布任务中读取 |
| 模板架构 / 项目升级 / 模板升级 / 任务提示词协议 / 模块发现 / `.local` / 项目记忆 / 中文收口 / code-only 交付 / 生成交付文档 | `docs/template-repository-ai-design.md` | 该文档是 AI/Codex/Agent 按需读取的完整设计与执行协议，不是每次任务默认全文读取 |

## 子目录

- `configuration-guide.md`：MAW 配置读取、拆分、聚合规则和 app_key 调试索引约定。
- `secret-governance-guide.md`：敏感配置治理协议，说明可信宿主机明文兼容、warning/block 边界、`mawsec://`、`mawlocal://`、`mawproxy://`、secret bindings、managed envelope、authorized recipient、short TTL handle、host/proxy Git 通道和派生项目迁移。
- `customer-repository-sync-guide.md`：external_mapped 模式下按组件映射客户仓库、保持组件目录无嵌套 `.git`、并人工显式同步。
- `repository-mirror-sync-guide.md`：配置仓库级镜像，在项目仓库 push 后先查看 mirror 计划，并按有效计划自动同步整仓 mirror。
- `component-mirror-repository-guide.md`：按 app_key 将当前项目仓库中的组件快照单向同步到目标镜像仓库。
- `git-credentials-guide.md`：git deploy key、细粒度 token、可选远端测试机、staging/中枢和 production/客户服务器凭证建议。
- `template-repository-design.md`：模板仓库用户版完整设计，面向项目负责人、开发者、客户侧技术负责人和人类读者。
- `template-repository-ai-design.md`：模板仓库 AI 版设计与执行协议，涉及模板架构、项目升级、模板升级、任务提示词协议、模块发现、`.local`、项目记忆、中文收口、code-only 交付或生成交付文档时按需读取。
- `template-repository-design-sync.md`：用户版设计和 AI 版设计的同步清单。
- `template-usage-guide.md`：模板仓库使用说明。
- `public-seed/`：MAWflow Seed 公开使用说明，覆盖 quickstart、Prompt Spec、Pack 类型、脱敏、贡献规则、`PUBLIC_PAYLOAD_MANIFEST.json` 和正式开源发布 gate。
- `AI_START_HERE.md` 与 `.maw/agent-entry.yaml`：AI 工作目录入口协议，定义本地 AI coding tools 进入项目目录后的启动读取顺序、保护边界和收口要求。
- `implementation/host-purpose-modes/`：宿主机用途模式模板协议，区分平台可信完整 clone 开发和客户用途 code 镜像出口，并补充项目归属、开发绑定和源码访问方式。
- `implementation/host-runtime-environments/`：Docker-first 但不硬限定的宿主机运行环境协议，覆盖现有环境探测、用户确认、统一 Docker 命名、既有环境保护、测试/线上/生产共库联调、离线镜像、本地宿主机 PG 数据面，以及主仓/平台项目/客户项目环境矩阵。
- `implementation/local-mcp-gateway/`：本地项目级 MCP 接入协议，说明 Codex Shell / Codex App 的项目绑定、普通非 MAW 项目兼容、仓库身份/绑定握手和安全拒绝边界。
- `implementation/mcp-knowledge-runtime/`：MCP Knowledge Runtime v1.1 离线协议，说明 Pack 类型、四层 registry、locks、示例 Pack、校验脚本和种子仓/主仓/Framework Hub 边界。
- `implementation/ai-model-adapter-evaluation/`：AI 模型适配与评测供应商无关协议，说明模型需求声明、评测用例、输出契约、官网公开摘要和种子仓/主仓/派生项目边界。
- `requirements/`：需求资料、需求基线、变更请求和待确认问题。
- `requirements/raw/`：基于 `.local/docs/requirements/raw/` 原始资料整理出的 Markdown 分析结果、摘要和证据索引。
- `ai-coding/`：AI 编写代码前必须遵守的边界、代码风格、工程规范和初始化待办清单。
- `ai-coding/ai-primary-development-model.md`：AI 主力开发模型，说明 `code/` 产品交付平面、code 外控制面和收口判断。
- `ai-coding/module-dossier-rules.md`：AI 使用模块档案定位边界和维护文档的规则。
- `ai-instructions/`：项目内可被 Codex 精准命中的指令、专有名词、关键词候选、经验索引、用户经验候选、执行经验候选、经验总结和方案详情库。
- `ai-instructions/templates/final-closeout.zh-CN.md`：中文人类优先最终说明模板。
- `seed-repository-upgrade-candidates.md`：派生项目记录适合回流到 `maw-project-template` 种子仓库的候选优化或新增能力；种子仓库自身保留模板和示例口径。
- `modules/`：功能模块档案目录，配合 `.maw/modules.yaml` 记录模块边界、实现程度、页面/API/数据表边界和变更日志；一级模块可维护 `route-api-index.md` 用 URL/API 快速定位二级模块，二级模块可按需维护 `pages/`、`backend/` 和 `traceability.md` 审计页，并用 `doc_status`、`last_verified_commit` 和 `module_map_score` 做渐进审计。
- `modules/_audits/`：模块地图审计报告目录，记录 `#模块地图` 检查、审计、查漏补缺、清理过期、变更影响和发布前检查结果。
- `modules/_template/ai-context.md`：可选 AI 模块上下文模板，只在复杂模块需要短小读取路线和常见误判提示时使用。
- `modules/_discovery/`：渐进式模块发现区，记录候选模块、证据和待确认问题。
- `design/`：架构、接口、数据模型、页面流程和功能设计。
- `planning/`：项目路线、任务拆解、迭代与模块拆分、交付计划和风险清单。
- `planning/todos/`：待办任务台账，记录被当前业务闭环依赖但暂不实现、先假设已完成的跨模块缺口、影响面、取消后果和完成后联调建议。
- `technical-map/`：技术地图入口，把项目目标、app_key、modules、公共能力、项目信号、任务和验收串成开发前读取路线。
- `doc-read-contract/`：文档写读契约说明，约束新写关键 docs 的 front matter、项目健康维度、实体标签和 AI 读取提示。
- `project-review-audits/`：项目评审与审计报告目录，保存 AI 会议式评审、人工确认后的 docs 回写计划和基于评审报告的验收目标审计；评审报告必须给出 `#项目审计：<评审报告路径>` 接续调用。
- `ai-session-briefs/`：最近 AI 会话概要账本，用于多设备协同和任务开始前轻量检索近期上下文。
- `capabilities/`：公共能力说明和模板；机器可读索引在 `.maw/capabilities.yaml`。
- `capabilities/doc-read-contract.md`：文档写读契约，要求新写或重构产品/需求/设计/模块/计划文档时带上可索引元数据，历史文档默认兼容。
- `capabilities/project-review-audit-governance.md`：项目评审与审计治理协议，约束 `#项目评审` / `#项目审计` 的报告、接续调用、人工确认和 docs 回写边界。
- `capabilities/project-health-context.md`：项目健康上下文协议，约束 `.maw/health/` 的健康问题、事实、决策、调研摘要和验收缺口记录边界。
- `capabilities/mcp-knowledge-runtime.md`：MCP Knowledge Runtime 协议，约束 Pack registry、locks、示例、检查和运行时边界。
- `capabilities/ai-model-adapter-evaluation.md`：AI 模型适配与评测协议，约束模型需求、评测用例、输出契约、公开摘要和供应商适配分仓边界。
- `capabilities/ai-workdir-entry-protocol.md`：AI 工作目录入口协议，约束 `AI_START_HERE.md`、`.maw/agent-entry.yaml`、`.maw/agent-rules.yaml` 和工具适配文件边界。
- `capabilities/ai-python-script-contract.md`：AI Python 脚本规范，要求可复用脚本输出最终结构化结论、详细日志落盘、处理多系统环境差异，并指导派生项目分批升级已有脚本。
- `project-signals/`：项目信号说明和模板；机器可读索引用于大屏、巡检和 AI 前置读取。
- `repository-identity/`：仓库身份地图说明和模板；机器可读索引在 `.maw/repository-identity.yaml`，角色覆盖目录在 `.maw/repository-identity.d/<role>/`。
- `planning/iteration-module-plan.md`：项目目标到迭代、模块、Story/Task 和 MAW 执行任务的拆解说明。
- `acceptance/`：验收清单、测试报告和缺陷清单。
- `delivery/`：发布说明、交付摘要和交接清单。
- `archive/`：历史归档目录，AI/Codex 默认永不自动读取。
