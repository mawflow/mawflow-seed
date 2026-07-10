---
doc_key: docs.ai-instructions.index
doc_type: governance
stage: governance
status: active
owner: planner
tags:
  - ai-instructions
  - commands
  - experience
project_health:
  dimensions:
    - ai_collaboration
  evidence_level: canonical
read_contract:
  summary: "项目指令、术语、经验和快捷调用入口。"
  health_signal: "用于 AI 协作健康读取项目指令体系是否完整，以及任务前命中可复用经验。"
  consumes: []
  produces: []
  ai_read_hint: "用户命中项目指令、关键词、经验或需要更新 AI 协作知识时读取。"
---

# 项目指令与经验库

本目录用于沉淀项目内可被 AI 精准命中的指令、专有名词和经验总结。它的目标不是替代一次性任务提示词，而是把项目越做越清楚的协作知识留在仓库里，让后续 Codex 会话可以通过触发词快速找到完整执行说明。

## 与其他目录的关系

- `prompts/`：存放可复制到 AI 工具中的提示词草案或成品，偏一次性任务输入。
- `docs/ai-coding/`：存放 AI 编码边界、工程规则、代码风格和端说明，偏通用开发约束。
- `docs/ai-instructions/`：存放项目内可复用的指令、术语和经验，偏“用户一句话下发后 AI 应该怎么理解和执行”。
- `experience-index.md` 是经验命中索引，AI 可以主动检索；`solutions/**` 保存较大的具体解决方案，必须先从索引命中后再按链接读取。

## Codex 使用规则

1. 不要在每个项目任务开始时全量读取本目录；只有用户消息、任务提示词或当前错误命中项目指令、术语、别名、经验主题，或需要新增/更新项目经验时，才读取本文件。
2. 当用户消息命中某个触发词、别名、专有名词或经验主题时，读取本文件的索引，再读取对应的完整说明文档后行动。
3. 当用户使用 `#关键字`、`#关键字：任务补充`、`#关键字/任务补充`，或表达“`#+指令`”这类“# + 指令关键字”格式时，按关键词匹配本总纲和 `PROJECT_COMMANDS.md`；这是推荐给人使用的主入口。解析前先去掉 `#` 后的空格，统一全角/半角冒号，并把 `模板/模版` 这类稳定同义写法合并判断。
4. 当用户使用 `#T001` 或 `#T001/<关键字或任务补充>` 时，映射到模板内置指令 `TINST-001`；当用户使用 `#P001` 或 `#P001/<关键字或任务补充>` 时，映射到当前业务项目特有指令 `PINST-001`。`/` 后面的内容只作为触发关键词、任务补充或歧义提示。
5. 没有 `#` 的习惯用语也要按项目指令候选处理，例如“提主”“合主”“跑包/跑任务包”“交接任务”“客入/客主/客出/客户合主”“上线/发布”“同步镜像”“发布公开镜像”“收口”“查历史坑”“模板漂移”“生成交付文档”“新增待办/完成待办/取消待办/待办影响”。
6. 如果 `#关键字`、`#+指令` 或自然语言触发词命中多条指令、关键词含义不清、当前仓库角色无法判断，或精确编号和关键字含义冲突，必须先向用户确认，不得自行猜测。
7. 如果用户要求“新增指令”“记录经验”“记住这个术语”“沉淀一下”等，按 `TINST-002` 更新本目录和本总纲。
8. 每次执行较复杂任务时，快速扫描任务提示词和用户消息中的项目关键词；命中候选或多次出现时，按 `TINST-004` 更新候选台账或术语文档。
9. 用户补充的澄清、说明、纠偏和有复用价值的边界信息，应提取标题、关键词和内容摘要，暂存到 `experience-candidates.md`，后续可升级为经验或指令。
10. AI 自己在执行中先错误尝试、再找到正确方法的可复用经验，应记录到 `execution-lesson-candidates.md`，例如错误运行时版本、错误测试命令、错误脚本入口或错误调试方式。
11. 每次实现、修 bug、测试、构建、发布、同步或执行脚本前，先用任务关键词、路径、命令和错误症状检索 `experience-index.md`；命中后才读取索引指向的 `lessons/**`、`solutions/**` 或指令全文。
12. AI 不得为了“了解经验库”主动全量读取 `solutions/**`；`solutions/**` 只在 `experience-index.md`、候选台账、用户明确路径或已命中经验条目指向时读取。
13. 本目录不得保存真实密钥、账号密码、客户隐私、生产连接串或不可外传资料；需要引用时只写配置位置或脱敏描述。
14. 用户最新明确要求优先于本目录旧记录；发生冲突时更新对应文档的“冲突与覆盖规则”。
15. “种子仓库”和“模板仓库”统一指 `maw-project-template`。Seed 来源通道分为 `内部来源通道`、`public_seed` 和 `unknown_legacy`：内部派生项目优先从内部种子开发源读取升级资产，外部公开派生项目优先从 `https://github.com/mawflow/mawflow-seed` 读取公开升级资产，来源不清时先输出证据并人工确认。派生项目开发中如果发现适合回流到种子仓库的优化或新增能力，最终说明必须明确指出，并记录到 `docs/seed-repository-upgrade-candidates.md`；需要生成种子仓库执行提示词时走 `TINST-027` / `#种子仓库升级`。

## 快捷调用格式

人类快捷查询入口是根目录 `PROJECT_COMMANDS.md`。推荐在 Codex 里使用 `#关键字` 直接调用项目指令：

```text
#模版升级：模板仓库生成升级资产；派生项目计算模板漂移并在当前会话执行升级
#种子仓库升级：把派生项目中发现的可复用优化分级记录为种子仓库升级建议，并生成在种子仓库执行的反向回流提示词
#任务包：<需求概要>
#跑任务包：<任务包目录、ChatGPT Markdown 纯文本、本机 zip、远程 zip 直链、分享页 URL、MAW 文件存储 URL>
#交接任务：把 ChatGPT 已确定方案转成 Codex 任务
#提主：把 dev 合并到 main，并按仓库级 mirror 有效计划同步镜像
#发布公开镜像：把私有开发仓的定版版本发布到公开仓
#客户仓库同步：判断客户仓分支角色和同步动作
#客入：从客户基线同步 <component>
#客入：从客户基线同步 <component>，使用本机客户仓 <path>
#客主：刷新 <component> 客户交付分支
#客出：同步 <component> 到客户交付分支
#客户合主：生成 <component> 客户合主集成计划
#发布：发布 <app_key>
#发布：发布 <app_key> 到 <env>
#发布测试：本地调试版本，安装或开启目标组件并给出可访问调试地址
#发布上线：线上服务器编译包部署测试，提供线上可访问地址，不等同生产
#发布生产：生产服务器部署，生产环境安装或版本上线必须人工审计
#发布生成：兼容误写，按 #发布生产 处理
#安装开发环境
#安装线上环境
#安装生产环境
#简化收口
#详细收口
#模块地图：初始化、检查、审计、查漏补缺、清理过期、变更影响或发布前检查已有项目 modules，建立一级 URL/API 索引、二级模块档案、证据字段和渐进式审计页
#项目评审：基于 docs 会议式评审项目目标、业务流程、验收目标和 docs 口径，评审报告给出接续 #项目审计 调用
#项目审计：<评审报告路径>，按评审成果审计验收目标、实现程度、证据和后续推进建议
#项目健康：记录、审计或生成 .maw/health 项目健康上下文和健康关注建议
#待办任务：记录/查询/完成/取消被当前业务闭环依赖但暂不实现、先假设已完成的跨模块待办
#MCP服务诊断：检查项目级 MCP 连通、project_key、仓库身份、宿主机用途、项目归属、开发绑定、tools/list、AI 可写路径和安全拒绝边界
#MCP知识库：查询、规划或审计 MCP Knowledge Runtime Pack registry、locks、Project Override 和安装/更新/导入/导出边界
#技术地图：查询/维护公共能力、功能基类、API 快照、待办、澄清、缺口、口径变更和 AI 前置条件
#仓库身份：查询/维护种子仓、主仓、平台项目仓、客户项目仓、混合仓和历史未分类仓的多角色身份、角色检测和差异化约束
#脚本规范：审计和升级现有脚本为 AI Python Script Contract，减少长日志、中间态和多环境差异噪音
#文档索引：为产品、需求、设计、模块、计划和审计文档补写读契约，生成项目健康和 AI 任务可读取的 docs 索引
#会话概要：检索最近几次 AI 会话任务概要，命中相关再细读；任务结束时写入可跨设备同步的轻量概要
#项目指令
#生成交付文档：生成用户手册、概要设计、部署手册的 Markdown 事实稿
```

- `#关键字`：推荐给人使用，按本总纲和 `PROJECT_COMMANDS.md` 匹配指令；`#+指令` 视作“# + 指令关键字”的泛称，不要求字面包含加号。
- `#T001` 或 `#T001/...`：精确调用模板内置指令，等价于 `TINST-001`；`/` 后内容用于补充目标或消歧。
- `#P001` 或 `#P001/...`：精确调用当前业务项目特有指令，等价于 `PINST-001`；各业务项目独立编号。
- `#TINST-001/...`、`#PINST-001/...`：兼容识别完整 ID；新增文档和日常调用统一推荐 `#关键字`，精确调用使用 `#T001` 或 `#P001`。
- 存在歧义时必须先向用户确认，不得自行猜测；尤其是同一习惯用语可能映射到客户仓库、组件镜像、仓库级 mirror、发布镜像、应用发布或模板升级双路由时。
- 新增、改名、废弃指令，或调整推荐关键字、内部指令 ID、短编号、触发词、适用范围时，必须同步维护 `PROJECT_COMMANDS.md` 的快捷调用、概要和可复制调用示例。
- `maw-project-template` 的主定位是 MAW 新项目种子仓库；`#项目升级` 只能在目标项目按取舍矩阵增量合并。`#模板升级/#模版升级` 未指定 commit 时，先按当前仓库角色路由：在源模板仓库中生成迁移说明、提示词或任务包；在派生项目中按 `TINST-026` 先识别 `template_source.source_channel`，再用 `template_source.version`（默认 `main`）解析目标模板 commit，计算模板漂移并在当前会话执行升级。
- `#种子仓库升级` 是反向回流入口：在派生项目中记录候选能力、按 S0-S4 分级，并生成“在种子仓库执行”的提示词；提示词落库时放在 `prompts/codex/seed-repository-upgrade-prompts/`。在种子仓库中按提示词评估并输出接纳、拒绝或补证据结论，接纳后再生成模板升级资产。它不等同于 `#项目升级` 或 `#模板升级/#模版升级`。

## 指令编号命名空间

- `TINST-XXX` / `#TXXX`：模板内置指令，由模板仓库维护；派生业务项目不得重排、复用或改写这些编号。
- `PINST-XXX` / `#PXXX`：业务项目特有指令，由各业务项目从 `PINST-001` 独立递增；模板仓库后续新增 `TINST-XXX` 不影响业务项目编号。
- 业务项目把模板能力升级进来时，只追加或更新模板内置 `TINST-XXX`，不得把本项目已有 `PINST-XXX` 改号。
- 人类日常优先记 `#关键字`，编号只用于歧义消解和稳定引用。

## 当前模板内置指令列表

| ID | 指令名称 | 触发词或别名 | 完整说明 |
| --- | --- | --- | --- |
| TINST-001 | 查找并执行项目指令 | 项目指令、按指令、走某某流程、执行某某指令、精准命中 | [instructions/use-project-instructions.md](instructions/use-project-instructions.md) |
| TINST-002 | 更新项目指令与经验库 | 新增指令、记录指令、更新指令、记住这个术语、沉淀经验、让 AI 记住 | [instructions/update-project-instructions.md](instructions/update-project-instructions.md) |
| TINST-003 | 使用模块档案定位开发边界 | 模块档案、功能模块、module dossier、模块边界、页面边界、接口边界、数据表边界、按模块处理、这个页面属于哪个模块、这个接口属于哪个模块 | [instructions/use-module-dossier.md](instructions/use-module-dossier.md) |
| TINST-004 | 任务关键词学习循环 | 关键词学习、关键词沉淀、任务提示词关键词、项目关键词、特有名词、业务黑话、用户澄清、用户说明、AI 试错、执行复盘、错误尝试、正确方法、经验暂存、越做越聪明、边界细化、名词定义 | [instructions/keyword-learning-loop.md](instructions/keyword-learning-loop.md) |
| TINST-005 | 生成模块档案初版 | 生成模块档案初版、生成 module.md 初版、根据描述生成模块档案、模块初稿、模块档案草稿 | [instructions/generate-module-dossier-draft.md](instructions/generate-module-dossier-draft.md) |
| TINST-006 | 同步 app_key 镜像仓库 | 同步镜像仓库、同步 app_key 镜像仓库、同步[app_key]镜像仓库、同步 server 镜像仓库、同步 client 镜像仓库、推送镜像仓库、mirror repository sync | [instructions/sync-app-mirror-repository.md](instructions/sync-app-mirror-repository.md) |
| TINST-007 | 创建和执行任务提示词工程 | #任务包、#跑任务包、创建任务提示词工程、生成任务提示词工程、创建 Codex 任务包、生成 task pack、执行任务提示词工程、执行指定任务提示词工程、继续任务提示词工程、纯文本任务包、Markdown 任务包、任务提示词工程落地、远程任务包 zip、分享页任务包、可道云/Kodbox 任务包、MAW 文件存储任务包、file-storage 任务包、可信文件存储 任务包 | [instructions/create-task-prompt-project.md](instructions/create-task-prompt-project.md) |
| TINST-008 | 经验防重复踩坑闭环 | 避免重复踩坑、查历史经验、经验防重踩、AI 试错复盘、执行经验命中、这个坑以后别再踩、防止另一个会话重复踩坑 | [instructions/avoid-repeat-pitfalls.md](instructions/avoid-repeat-pitfalls.md) |
| TINST-009 | 使用内置模板任务提示词工程 | #模板化、内置任务提示词工程、改造成模板仓库、接入 MAW 模板、任意项目改造成模板仓库、模板化改造 | [instructions/use-builtin-template-task-packs.md](instructions/use-builtin-template-task-packs.md) |
| TINST-010 | 模块树拆分与模块档案生成 | #模块、生成 modules、拆分模块、模块树、模块拆细、modules 拆分、模块太大、自动生成模块档案、重建模块索引、按业务拆 modules、不要只拆二级目录、AI 模块上下文、ai-context、ai_doc、_ai 模块副本 | [instructions/split-module-tree.md](instructions/split-module-tree.md) |
| TINST-011 | 生成模板新特性轻量升级提示词 | #模版升级、模版升级、生成模板新特性升级提示词、生成轻量升级提示词、模板特性升级提示词、把这条变动生成升级提示词、把这个新特性同步给派生项目、给派生项目的升级提示词、轻量化升级模板 | [instructions/generate-template-feature-upgrade-prompt.md](instructions/generate-template-feature-upgrade-prompt.md) |
| TINST-012 | 外部 AI 方案转 Codex 任务 | #交接任务、ChatGPT 生成 Codex 任务、外部 AI 任务交接、把方案生成 Codex 任务、生成 Codex 任务纯文本、生成 Codex 任务 Markdown、生成 Codex 任务 zip、ChatGPT 到 Codex、方案转任务包、任务交接协议、完整任务包文件内容、Codex 使用方式 | [instructions/external-ai-to-codex-task-handoff.md](instructions/external-ai-to-codex-task-handoff.md) |
| TINST-013 | dev 合并到 main 并按开关同步仓库镜像 | #提主、#合并主分支、#合并dev到main、合并dev到main、dev合并到main、内部提主合并、同步 main 镜像、仓库级镜像、repository_mirrors | [instructions/dev-to-main-merge.md](instructions/dev-to-main-merge.md) |
| TINST-014 | 发布组件应用并执行上线操作 | #发布、#立即发布、#发布生效、发布组件、更新发布、执行SQL、上线、部署、发布测试、发布上线、发布生产、发布生成、发布 server、发布 client、发布到 test、发布到 production、发布版本状态、发布名单、本地代码最新 | [instructions/release-component.md](instructions/release-component.md) |
| TINST-015 | 客户仓库分支角色与同步总览 | #客户仓库同步、客户仓库同步、external_mapped、分支流向、客户分支角色、客户单分支、客户交付分支 | [instructions/customer-repository-branch-flow.md](instructions/customer-repository-branch-flow.md) |
| TINST-016 | 客入 | #客入、客入、从客户主线拉代码、从客户基线同步、客户公共模块回流、CUSTOMER_BASE到INTERNAL_DEV、本机客户仓、大仓客入 | [instructions/customer-in.md](instructions/customer-in.md) |
| TINST-017 | 客主 | #客主、客主、刷新客户交付分支、客户主分支到专属分支、CUSTOMER_BASE到CUSTOMER_DELIVERY、本机客户仓 | [instructions/customer-base-to-delivery.md](instructions/customer-base-to-delivery.md) |
| TINST-018 | 客出 | #客出、客出、同步到客户仓、推客户分支、INTERNAL_RELEASE到CUSTOMER_DELIVERY、客户交付 | [instructions/customer-out.md](instructions/customer-out.md) |
| TINST-019 | 客户合主 | #客户合主、客户合主、客户交付分支合入客户主线、CUSTOMER_DELIVERY到CUSTOMER_BASE、客户集成分支 | [instructions/customer-delivery-to-base.md](instructions/customer-delivery-to-base.md) |
| TINST-020 | 中文人类优先收口 | #收口格式、#中文收口、中文人类优先收口、最终说明格式、final closeout、技术元数据、参数获取步骤、建议选项、敏感参数本机填写、.local 填写文件 | [instructions/final-closeout-response.md](instructions/final-closeout-response.md) |
| TINST-021 | 渐进式模块发现 | #模块发现、渐进式模块发现、候选模块、module_candidate、模块证据、证据不足、不确定 module_key | [instructions/progressive-module-discovery.md](instructions/progressive-module-discovery.md) |
| TINST-022 | 项目记忆闭环 | #项目记忆、#本机记忆、记忆闭环、越用越聪明、用户澄清、长期偏好、本机差异、local_update、memory_update | [instructions/project-memory-loop.md](instructions/project-memory-loop.md) |
| TINST-023 | 项目升级策略 | #项目升级、项目升级、模板派生项目升级、升级到最新模板、同步模板新特性、源模板升级、upgrade decision matrix | [instructions/project-upgrade-strategy.md](instructions/project-upgrade-strategy.md) |
| TINST-024 | 模板升级策略 | #模板升级、#模版升级、模板升级、模版升级、生成模板升级资产、升级迁移说明、派生项目升级提示词 | [instructions/template-upgrade-strategy.md](instructions/template-upgrade-strategy.md) |
| TINST-025 | 生成交付文档事实稿 | #生成交付文档、交付文档、生成用户手册、生成概要设计、生成部署手册、生成文档事实稿 | [instructions/generate-delivery-docs.md](instructions/generate-delivery-docs.md) |
| TINST-026 | 派生项目模板漂移升级 | #模版升级、#模板升级、派生项目模板升级、模板漂移升级、当前模板落后多少提交、按模板仓库最新提交升级、source_channel、内部来源通道、public_seed | [instructions/derived-template-drift-upgrade.md](instructions/derived-template-drift-upgrade.md) |
| TINST-027 | 种子仓库升级 | #种子仓库升级、种子仓库升级、模板仓库升级建议、回流种子仓库、回流模板仓库、反向升级种子仓库、能力回流、建议更新种子仓库、建议更新模板仓库 | [instructions/seed-repository-upgrade.md](instructions/seed-repository-upgrade.md) |
| TINST-028 | 待办任务治理 | #待办任务、新增待办、记录待办、完成待办、取消待办、查询待办、待办影响、假设已完成、先不做但依赖、被依赖但暂不实现、完成后联调 | [instructions/todo-task-governance.md](instructions/todo-task-governance.md) |
| TINST-029 | MCP 服务诊断 | #MCP服务诊断、MCP 服务诊断、本地 MCP 自检、项目级 MCP、Codex MCP、tools/list、maw.audit.ping、MAW_MCP_ENDPOINT、MAW_MCP_PROJECT_KEY、ownership_type、binding_type、source_access_mode | [instructions/mcp-service-diagnostics.md](instructions/mcp-service-diagnostics.md) |
| TINST-030 | 技术地图与项目提示元数据 | #技术地图、#项目提示、#能力快照、公共能力、功能基类、API 快照、能力索引、项目大屏、项目审计、项目巡检、澄清记录、缺口记录、口径变更、AI 前置条件 | [instructions/technical-map-project-metadata.md](instructions/technical-map-project-metadata.md) |
| TINST-031 | 仓库身份地图 | #仓库身份、仓库身份、身份地图、仓库角色、多角色、角色目录、种子仓、主仓、平台项目仓、客户项目仓、混合仓、unknown_legacy、repository identity、repository role | [instructions/repository-identity-map.md](instructions/repository-identity-map.md) |
| TINST-032 | 脚本规范升级 | #脚本规范、脚本规范、脚本契约、AI Python Script Contract、规范化脚本、脚本标准化、已有脚本升级、脚本输出规范、脚本日志降噪、耗时任务脚本化、Python 脚本优先、py-first | [instructions/script-contract-upgrade.md](instructions/script-contract-upgrade.md) |
| TINST-033 | 文档写读契约与索引 | #文档索引、文档写读契约、文档读取契约、docs 索引、生成文档索引、健康面板文档来源、产品设计索引、模块设计索引、doc-read-contract、document index | [instructions/doc-read-contract.md](instructions/doc-read-contract.md) |
| TINST-034 | 最近会话概要检索与写入 | #会话概要、最近会话、会话摘要、任务概要、最近任务、读取最近几次会话、recent-session-briefs、session briefs、跨设备接力、短期记忆 | [instructions/recent-session-briefs.md](instructions/recent-session-briefs.md) |
| TINST-035 | 安装项目环境 | #安装环境、#安装开发环境、#安装线上环境、#安装生产环境、安装环境、安装开发环境、安装本地环境、修复本地环境、安装线上环境、安装生产环境、配置开发环境、配置线上环境、配置生产环境、本地开发环境、本地测试环境 | [instructions/install-environment.md](instructions/install-environment.md) |
| TINST-036 | 模块地图初始化、检查、审计与规范改造 | #模块地图、模块地图、初始化 modules、检查 modules、审计 modules、查漏补缺、清理过期、变更影响、发布前检查、页面 URL 索引、API 索引、route-api-index、页面审计页、后端审计页、模块 traceability、module_map_score | [instructions/module-map.md](instructions/module-map.md) |
| TINST-037 | 项目评审与审计治理 | #项目评审、项目评审、需求评审会议、业务流程评审、开发方向核对、docs 口径治理、#项目审计、项目审计、验收目标审计、实现程度审计、评审报告路径 | [instructions/project-review-audit.md](instructions/project-review-audit.md) |
| TINST-038 | 项目健康上下文 | #项目健康、项目健康、健康上下文、记录项目健康问题、记录这个缺口、审计项目健康、摸一下项目健康问题、生成健康关注建议、把缺口变成调研问题、.maw/health | [instructions/project-health-context.md](instructions/project-health-context.md) |
| TINST-039 | 发布公开镜像 | #发布公开镜像、#发布开源镜像、#发布镜像、公开发布镜像、发布 public mirror、私有仓发布到公开仓、开发完成一个版本后发布到公开仓、种子仓发布公开仓 | [instructions/publish-repository-mirror.md](instructions/publish-repository-mirror.md) |
| TINST-040 | MCP Knowledge Runtime | #MCP知识库、#MCP安装、#MCP更新、#MCP同步、#MCP审计、#技术选型、#框架包、#风格包、#项目蓝图、#提示词包、Framework Pack、Style Pack、Blueprint Pack、Prompt Pack、Pack Registry、Project Override | [instructions/mcp-knowledge-runtime.md](instructions/mcp-knowledge-runtime.md) |

## 当前术语列表

| ID | 术语 | 别名 | 说明 |
| --- | --- | --- | --- |
| TERM-001 | 项目指令 | 指令、项目内指令、AI 指令 | [terms/project-instruction.md](terms/project-instruction.md) |
| TERM-002 | 模块档案 | 功能模块档案、module dossier、模块边界、页面边界、接口边界、数据表边界 | [terms/module-dossier.md](terms/module-dossier.md) |
| TERM-003 | 项目关键词 | 关键词、任务关键词、特有名词、业务黑话、项目内叫法 | [terms/project-keyword.md](terms/project-keyword.md) |
| TERM-004 | 种子仓库 | 模板仓库、源模板仓库、MAW 种子仓库、maw-project-template、seed repository、template repository | [terms/seed-repository.md](terms/seed-repository.md) |

## 当前经验列表

| ID | 经验主题 | 适用场景 | 说明 |
| --- | --- | --- | --- |
| LESSON-001 | 指令库与提示词目录分工 | 判断知识应该放入 `docs/ai-instructions/` 还是 `prompts/` | [lessons/instructions-vs-prompts.md](lessons/instructions-vs-prompts.md) |
| LESSON-002 | FastAdmin 服务端发布经验 | 迁移或审查 FastAdmin / ThinkPHP 后端发布脚本、发布流程和验收清单 | [lessons/release/fastadmin-server-release.md](lessons/release/fastadmin-server-release.md) |
| LESSON-003 | 中文收口偏好 | 任务完成、验证、提交推送和发布影响说明 | [lessons/final-closeout-preferences.md](lessons/final-closeout-preferences.md) |
| LESSON-004 | 多设备 `.local` overlay 经验 | 多设备开发、本机差异、本机 AI 临时状态和 local overlay 边界 | [lessons/local-overlay-for-multi-device-development.md](lessons/local-overlay-for-multi-device-development.md) |
| LESSON-005 | 测试契约漂移防护 | 口径、文案、API 摘要、状态标签或命令输出变更后同步 pytest/static 断言 | [lessons/test-contract-drift-guard.md](lessons/test-contract-drift-guard.md) |
| LESSON-006 | Git 提交信息规范 | AI 或人工提交代码、配置、文档、脚本或模板协议改动 | [lessons/git-commit-message-conventions.md](lessons/git-commit-message-conventions.md) |

经验命中入口：

- [experience-index.md](experience-index.md)：经验索引，只记录概述、触发关键词、症状、适用范围、风险等级和详情链接。
- [solutions/](solutions/)：较大的具体解决方案详情库；默认不主动读取全文，只能在索引、候选台账或用户明确路径命中后按需读取。
- `docs/ai-session-briefs/`：最近 AI 会话概要账本；任务开始先运行 `recent-session-briefs.py`，只在命中相关时读取具体概要。

内置任务提示词工程：

- `prompts/codex/task-packs/template-feature-upgrade-codex-tasks/`：模板派生项目升级，新版模板能力按审计和取舍矩阵增量同步到目标项目。
- `prompts/codex/task-packs/adopt-maw-project-template-codex-tasks/`：任意项目模板化改造，先建立 MAW 协作控制面，再按项目事实补齐组件、模块和文档。

## 新增条目规则

- 新增可执行流程时，放入 `instructions/`，使用 [templates/instruction.md](templates/instruction.md)。模板仓库新增模板内置指令用 `TINST-XXX`；业务项目新增项目特有指令用 `PINST-XXX`。
- 新增专有名词、业务黑话、客户简称或项目内约定时，放入 `terms/`，使用 [templates/term.md](templates/term.md)。
- 新增复盘经验、踩坑记录、偏好总结或最佳实践时，放入 `lessons/`，使用 [templates/lesson.md](templates/lesson.md)。
- 发布、部署、上线、回滚等运维经验优先放入 `lessons/release/`；它们是给 fork 项目按需改造的参考经验，不是模板仓库对所有项目的强约束。
- 新增尚未稳定的任务关键词时，先写入 [keyword-candidates.md](keyword-candidates.md)；多次出现并边界稳定后，再升级到 `terms/`。
- 用户澄清、说明和纠偏有复用价值时，先写入 [experience-candidates.md](experience-candidates.md)；多次适用后，再升级到 `lessons/` 或 `instructions/`。
- AI 执行中试错后找到正确方法时，先写入 [execution-lesson-candidates.md](execution-lesson-candidates.md)；多次适用或风险较高后，再升级到 `lessons/`、`solutions/`、`instructions/` 或 `docs/ai-coding/`。
- 经验正文较大、包含完整排查过程、命令序列、替代方案或验收清单时，详情写入 `solutions/<category>/<topic>.md`，并只在 `experience-index.md` 中保留概述和触发关键词。
- 新增或升级正式经验、解决方案详情时，必须同步更新 `experience-index.md`，确保后续会话先命中索引再读取详情。
- 生成或重建 modules 时，先按 `TINST-010` 生成模块树和 group/leaf 判定；只有 leaf 才创建 `module.md` 与 `changelog.md`。
- 初始化、检查、审计或规范改造已有项目 modules 时，按 `TINST-036` 建立模块地图；一级模块维护 `route-api-index.md`，二级模块维护 `module.md`、AI 边界指引、证据字段和按需 detail docs，缺失内容渐进补全，定期用 `module_map_score` 查漏补缺并标记 stale/deprecated 文档。
- 项目方向、需求理解、业务流程、验收目标或 docs 口径需要人工评审时，按 `TINST-037` 执行 `#项目评审`；评审报告必须给出 `#项目审计：<评审报告路径>` 接续调用。基于评审成果核对实现程度、验收证据和后续推进建议时，使用 `#项目审计：<评审报告路径>`。
- 需要记录或审计健康问题、需求事实、决策、普通健康待办、调研会话摘要和验收缺口时，按 `TINST-038` 执行 `#项目健康`；`.maw/health/` 是可导入健康上下文，不替代 `docs/planning/todos/`、`docs/project-review-audits/`、正式需求或验收文档。
- 私有开发仓库完成版本后需要发布到公开仓时，按 `TINST-039` 执行 `#发布公开镜像`；普通仓库级 mirror 同步仍走 `TINST-013`，应用部署仍走 `TINST-014`。
- 文件名使用英文小写短横线，例如 `customer-cloud-release.md`。
- 每次新增、改名或废弃条目，都必须同步更新本总纲中的对应列表。
- 每次新增、改名、废弃指令，或调整推荐关键字、内部指令 ID、短编号、触发词、适用范围，都必须同步更新根目录 `PROJECT_COMMANDS.md`，保证人类优先可用 `#关键字` 快速调用，必要时模板指令可用 `#T001` 精确调用，业务项目指令可用 `#P001` 精确调用，并能复制调用示例后只改参数就使用。
