# 项目常用指令目录

本文件给人阅读，用来快速找到可以对 AI/Codex 说的触发词。完整执行规则在 `docs/ai-instructions/` 中维护。

## 快捷调用格式

推荐直接使用 `#关键字` 调用项目指令；需要补充目标或消歧时，再追加 `：任务补充` 或 `/任务补充`。这是给人速记的主入口。
这里的 `#+指令` 语义是“`#` + 指令关键字”：凡用户消息中出现以 `#` 开头的短语，都先当作潜在项目指令解析，再结合当前仓库角色、路径、参数和习惯用语判断是否能唯一命中。

- `#项目指令`
- `#任务包：<需求概要>`
- `#交接任务：把 ChatGPT 已确定方案转成 Codex 任务`
- `#模板设计：查看用户版完整设计`
- `#AI设计：查看 AI 版完整设计与执行协议`
- `#生成交付文档：生成用户手册、概要设计、部署手册的 Markdown 事实稿`
- `#提主：把 dev 合并到 main，并按开关同步仓库镜像`
- `#发布公开镜像：把私有开发仓的定版版本发布到公开仓`
- `#客户仓库同步：判断 <component> 的客户仓分支角色`
- `#客入：从客户基线同步 <component>`
- `#客入：从客户基线同步 <component>，使用本机客户仓 <path>`
- `#客主：刷新 <component> 客户交付分支`
- `#客出：同步 <component> 到客户交付分支`
- `#客户合主：为 <component> 生成客户集成分支计划`
- `#发布：发布 <app_key>`
- `#发布：发布 <app_key> 到 <env>`
- `#发布测试`：本地调试 / `local_debug`，通常基于本地环境完成目标组件环境安装、程序部署或启动，并提供可访问调试地址；未指定组件时先按 `environments.test.remote_server.default_release_components` 取候选范围，再按发布版本状态和组件路径差异筛选发布名单；允许当前工作区未提交改动参与测试发布，并记录 dirty snapshot
- `#发布上线`：发布到 `remote_staging_server`，仍属于测试，是在线上服务器完成目标组件环境安装、编译后程序部署并提供线上可访问地址的程序包部署测试；未指定组件时先按 `environments.staging.remote_server.default_release_components` 取候选范围，再按发布版本状态和组件路径差异筛选发布名单；允许当前工作区未提交改动参与测试发布，并记录 dirty snapshot
- `#发布生产` / `#发布生成`：发布到 `remote_production_server`；未指定组件时先按 `environments.production.remote_server.default_release_components` 取候选范围，再按发布版本状态和组件路径差异筛选发布名单；执行前必须确认本地候选 commit 等于发布来源远端分支且工作区干净；涉及生产环境安装、生产服务器部署或生产版本上线必须人工审计
- `#安装开发环境`：先确认本机现有运行时、数据库、端口和项目启动入口，再展示复用/安装方案；确认后安装或开启本地开发/测试入口，并把启动命令增量合并到根 `package.json` scripts；验收目标是 `npm run dev` 能启动或刷新本地调试环境，并输出 `127.0.0.1` 与局域网访问链接（可参考 MAW 主仓转发到 `local:dev`）；`安装本地环境`、`修复本地环境` 等同该口径
- `#安装线上环境`：先确认 staging/remote_staging_server 现状、工作目录、数据库、备份和回滚，再展示线上环境安装方案，确认后执行
- `#安装生产环境`：先确认 production/remote_production_server、审批、备份、回滚和停机影响，再展示生产安装方案，确认后执行
- `#模块地图：初始化/检查/审计/查漏补缺/清理过期/变更影响/发布前检查，建立一级 URL/API 索引、二级模块档案、证据字段和渐进式审计页`
- `#项目评审：<范围或目标>`：AI 作为需求评审会主讲人，基于 docs 评审项目目标、业务流程、验收目标和 docs 口径，并给出接续 `#项目审计：<评审报告路径>`
- `#项目审计：<评审报告路径>`：基于项目评审报告审计验收目标、实现程度、证据、缺口和后续推进建议
- `#项目健康：记录/审计/生成关注建议/导入准备 .maw/health 项目健康上下文`
- `#模块发现：证据不足时先记录候选模块、证据和待确认问题`
- `#待办任务：记录/查询/完成/取消被当前业务闭环依赖但暂不实现、先假设已完成的跨模块待办`
- `#MCP服务诊断：检查项目级 MCP 连通、project_key、仓库身份、宿主机用途、项目归属、开发绑定、工具列表、可写路径和授权拒绝边界`
- `#MCP知识库：查询/规划/审计 MCP Knowledge Runtime Pack registry、locks、Project Override、安装更新和导入导出边界`
- `#技术地图：查询/维护公共能力、功能基类、API 快照、待办、澄清、缺口、口径变更和 AI 前置条件`
- `#仓库身份：查询/维护仓库多角色身份、角色检测证据和差异化约束`
- `#脚本规范：审计和升级现有脚本为 AI Python Script Contract，减少长日志、中间态和多环境差异噪音`
- `#文档索引：为产品、需求、设计、模块、计划和审计文档补写读契约，并生成项目健康和 AI 任务可读取的 docs 索引`
- `#会话概要：检索最近几次 AI 会话任务概要；任务结束时写入可跨设备同步的轻量概要`
- `#项目记忆：把用户澄清、长期偏好或执行经验沉淀到项目记忆`
- `#本机记忆：把本机路径、端口、工具链或调试差异留在 .local`
- `#模板升级：源模板仓库生成升级资产；派生项目计算模板漂移并执行`
- `#模版升级：同 #模板升级`
- `#种子仓库升级：把派生项目中的可复用优化分级记录为种子仓库升级建议，并生成在种子仓库执行的反向回流提示词`
- `#收口格式：按中文人类优先格式说明本次任务结果；默认简化，按需详细；缺敏感参数时先创建 .local 本机填写文件`

调用规则：

- `#关键字` 是推荐给人使用的调用方式，AI 按下表、`docs/ai-instructions/README.md` 和触发词匹配最贴近的指令。
- `#+指令`、`# 关键字`、`#关键字：补充`、`#关键字/补充`、`#T001`、`#P001` 和完整 ID 都要识别；解析时先去掉 `#` 后的空格，统一全角/半角冒号，并把 `模板/模版` 这类稳定同义写法合并判断。
- 没有 `#` 的习惯用语也要按项目指令候选处理，例如“提主”“合主”“跑包/跑任务包”“交接任务”“客入/客主/客出/客户合主”“上线/发布”“同步镜像”“发布公开镜像”“收口”“查历史坑”“模板漂移”“生成交付文档”“新增待办/完成待办/取消待办/待办影响”。
- 需要稳定精确调用或避免歧义时，模板内置指令使用 `#T001` 或 `#T001/关键字`，业务项目特有指令使用 `#P001` 或 `#P001/关键字`。
- 如果 `#关键字` 或自然语言触发词命中多条指令、关键词含义不清，或精确编号和关键字含义冲突，AI 必须先向用户确认，不得自行猜测。
- 兼容识别完整 ID 格式 `#TINST-001/...` 和 `#PINST-001/...`，但新增文档和日常调用统一推荐 `#关键字`，精确调用使用 `#T001` 或 `#P001`。
- 本文件是人用快捷查询帮助文档；新增、改名、废弃指令，或调整推荐关键字、内部指令 ID、编号命名空间、短编号、触发词、适用范围时，必须同步维护本文件的速查表和调用示例。

编号命名空间：

- 模板内置指令：`TINST-XXX` / `#TXXX`，由模板仓库维护。
- 业务项目特有指令：`PINST-XXX` / `#PXXX`，由各业务项目从 `PINST-001` 独立递增。
- 模板升级不得重排业务项目已有 `PINST-XXX` 编号。

## 调用示例

复制下面任一示例到 Codex，按需替换 `<...>` 参数即可使用。

```text
#项目指令：请按当前仓库规则处理 <任务说明>
```

```text
#新增指令：把 <规则/经验/术语> 沉淀到项目指令库，触发词包括 <关键词1>、<关键词2>
```

```text
#模块档案：判断 <页面/接口/数据表/文件路径> 属于哪个模块，并按模块边界处理
```

```text
#模块：根据当前项目结构重新拆分模块树，避免把大模块直接写成单个 module.md
```

```text
#模块地图：检查当前项目 modules，按一级模块 route-api-index、二级 module.md、页面/后端审计页、doc_status 和 module_map_score 给出改造并落地
```

```text
#模块地图：审计 <module_key>，对照页面/API/后端文件，记录 last_verified_commit 并输出需要人工确认的 pending_confirm
```

```text
#模块地图：清理过期，找出 stale/deprecated/orphan 模块文档，先给审计报告和确认清单，不直接删除
```

```text
#项目评审：全量核对当前项目开发方向、业务流程、验收目标和 docs 口径
```

```text
#项目评审：评审 <module_key 或 docs 路径>，只生成评审报告，待人工确认后再回写 docs
```

```text
#项目审计：docs/project-review-audits/rounds/<review_id>/review.md
```

```text
#模块发现：当前还不能确认正式 module_key，先记录候选模块和证据
```

```text
#待办任务：记录“<能力> 暂不实现，但当前 <业务流程/模块> 先假设它已完成”，并列出受影响模块、取消影响和完成后联调建议
```

```text
#待办任务：查询 TODO-YYYYMMDD-<slug> 会影响哪些模块，完成或取消分别要改什么
```

```text
#MCP服务诊断：检查当前项目的 MAW MCP endpoint、tools/list、maw.audit.ping、project_key、仓库身份、项目归属、开发绑定和客户用途权限边界
```

```text
#MCP知识库：为当前项目生成 Framework Pack / Style Pack 解析预览，不执行真实安装或下载
```

```text
#技术地图：开发 <功能/API> 前，先查询已有公共能力、功能基类、API 快照、待办、澄清、缺口和 AI 前置条件
```

```text
#能力快照：把 <模块/接口/基类/脚本> 登记为公共能力候选，并输出给项目巡检/大屏的元数据
```

```text
#仓库身份：检查当前仓库 declared roles、detected roles、角色目录覆盖和高风险操作约束
```

```text
#脚本规范：审计 ops/scripts 现有脚本，并按高频、高风险、耗时、噪音和跨系统差异优先级生成升级清单
```

```text
#脚本规范：接入通用测试入口，先用 run-project-tests.py 生成测试计划，不直接执行长测试
```

```text
#脚本规范：把 <脚本路径> 升级为 Python 优先、结构化 JSON 输出、长日志落盘、支持 dry-run 的规范脚本
```

```text
#文档索引：为 docs/product 和 docs/design 的关键文档补 front matter，并生成项目健康可读取的文档索引
```

```text
#文档索引：检查当前 docs 写读契约，不批量重写历史文档
```

```text
#会话概要：用当前任务关键词检索最近 8 次会话概要，命中相关再细读
```

```text
#会话概要：为本轮任务写入共享概要，标题为“<任务标题>”，能力为 <capability_key>
```

```text
#完成待办：TODO-YYYYMMDD-<slug>
```

```text
#取消待办：TODO-YYYYMMDD-<slug>，改为 <替代方案>
```

```text
#项目记忆：把“可信设备开发、只交付 code、.local 强化、多设备开发、越用越聪明”沉淀为项目偏好
```

```text
#本机记忆：把当前设备的端口、代理、浏览器调试和工具链差异留在 .local
```

```text
#任务包：围绕 <任务目标> 创建可恢复、可分阶段执行的 Codex 任务包
```

```text
#跑任务包：prompts/codex/task-packs/<slug>-codex-tasks
#跑任务包：<复制 ChatGPT Markdown 里的【Codex 任务提示词】全文>
#跑任务包：<本机任务包 zip 文件>
#跑任务包：<远程任务包 zip 直链或分享页 URL>
#跑任务包：https://files.example.invalid/task-pack.zip
#跑任务包：https://files.example.invalid/share/<share_key>
```

远程 zip 或分享页只从团队确认的可信文件存储下载；提取码、访问密码和临时凭证仅用于当次会话，不写入仓库。

```text
#交接任务：把 ChatGPT 已确定的 <方案/审计建议> 生成 Codex 可执行任务；默认输出可下载、可复制 Markdown，大任务必须写出任务包每个文件完整内容和 Codex 用法，明确要求 zip 时才生成任务包 zip
```

```text
#模板设计：查看模板仓库用户版完整设计
```

```text
#AI设计：查看模板仓库 AI 版完整设计与执行协议
```

```text
#生成交付文档：根据 modules、design、ops 生成用户手册、概要设计、部署手册的 Markdown 事实稿
```

```text
#提主：把 origin/dev 合并到 main，推送 origin/main，并按 repository_mirrors 开关同步仓库级镜像
```

```text
#发布公开镜像：发布 v0.2.18 到 public_seed
```

```text
#发布开源镜像：按 export_sanitized_tree 发布 v0.2.18 到公开仓
```

```text
#客户仓库同步：检查 server 的 INTERNAL_DEV、INTERNAL_RELEASE、CUSTOMER_BASE、CUSTOMER_DELIVERY 流向
```

```text
#客入：从 CUSTOMER_BASE 同步 server 到 INTERNAL_DEV
```

```text
#客入：从 CUSTOMER_BASE 同步 server 到 INTERNAL_DEV，客户仓很大，使用本机客户仓 <本机客户仓目录>
```

```text
#客主：刷新 server 的客户交付分支，正式客出前确认客户基线已同步
```

```text
#客出：把 server 从 INTERNAL_RELEASE 同步到 CUSTOMER_DELIVERY
```

```text
#客户合主：为 server 生成 CUSTOMER_DELIVERY 合入 CUSTOMER_BASE 的 integration 计划
```

```text
#发布：发布 <app_key>
```

```text
#发布：发布 <app_key> 到 test
```

```text
#发布：发布 <app_key> 到 production
```

```text
#发布测试
```

```text
#发布上线
```

```text
#发布生产
```

```text
#发布生成
```

```text
#收口格式：请用中文人类优先格式收口，并把技术字段放到末尾
```

```text
#详细收口：展开验证命令、逐项结果和完整技术元数据
```

```text
#简化收口：只保留结论、关键变更、验证结论、入口和必要下一步
```

```text
#项目升级：把源模板的新版能力按源模板来源和取舍矩阵增量同步到当前项目，不能覆盖当前项目业务规则
```

```text
#模版升级：在派生项目中计算当前模板落后源模板多少提交，生成当前会话执行提示词并执行
```

```text
#模板化：把当前项目增量接入 MAW 模板规范，保留已有业务代码、app_key、发布流程和 README
```

```text
#模板升级（源模板仓库）：覆盖模板提交 <commit1>、<commit2>，生成迁移说明、升级资产和可复制到目标项目 Codex 的提示词
```

```text
#模版升级：在源模板仓库同 #模板升级；在派生项目中执行模板漂移升级
```

```text
#模板升级：未指定 commit 时，仍先按当前仓库角色路由；源模板仓库生成升级资产，派生项目先识别 template_source.source_channel，再按 template_source.version（默认 main）解析目标模板 commit 并执行漂移升级
```

```text
#种子仓库升级：把当前派生项目里发现的 <可复用问题/自定义能力> 记录为种子仓库候选优化，分级为 S1-S4，并生成在种子仓库 maw-project-template 执行的任务提示词
```

```text
#种子仓库升级：把 <能力/脚本/治理协议> 的反向回流提示词落到 prompts/codex/seed-repository-upgrade-prompts/
```

```text
#同步镜像仓库：同步 <app_key> 镜像仓库，只允许从当前项目仓库同步到目标镜像仓库
```

```text
#避免重复踩坑：先按 <关键词/错误症状/命令> 检索经验索引，再继续处理
```

## 指令速查

| 推荐调用 | 精确调用 | 触发关键词 | 指令内容概要 | 完整说明 |
| --- | --- | --- | --- | --- |
| `#项目指令` | `#T001` | 项目指令、按指令、精准命中 | 让 AI 先查项目指令库，再按命中的项目规则行动 | `docs/ai-instructions/instructions/use-project-instructions.md` |
| `#新增指令` | `#T002` | 新增指令、记录经验、沉淀经验、记住这个术语 | 把项目流程、术语、偏好或经验沉淀到项目指令库，并同步维护本速查表 | `docs/ai-instructions/instructions/update-project-instructions.md` |
| `#模块档案` | `#T003` | 模块档案、module dossier、这个页面属于哪个模块 | 让 AI 用 `.maw/modules.yaml` 和 `docs/modules/` 定位开发边界 | `docs/ai-instructions/instructions/use-module-dossier.md` |
| `#关键词学习` | `#T004` | 关键词学习、项目关键词、业务黑话、执行复盘 | 记录高频项目关键词、用户澄清和 AI 试错经验 | `docs/ai-instructions/instructions/keyword-learning-loop.md` |
| `#生成模块档案初版` | `#T005` | 生成模块档案初版、生成 module.md 初版、模块档案草稿 | 为已判定为 leaf 的单个模块生成或补齐 `module.md` 初版 | `docs/ai-instructions/instructions/generate-module-dossier-draft.md` |
| `#同步镜像仓库` | `#T006` | 同步 app_key 镜像仓库、同步 server 镜像仓库、推送镜像仓库 | 将当前项目中的某个组件单向同步到目标镜像仓库 | `docs/ai-instructions/instructions/sync-app-mirror-repository.md` |
| `#任务包` | `#T007/创建` | 创建任务提示词工程、生成 task pack | 把复杂需求整理成可恢复、多步骤执行的任务提示词工程 | `docs/ai-instructions/instructions/create-task-prompt-project.md` |
| `#跑任务包` | `#T007/执行` | 执行任务提示词工程、继续任务提示词工程、纯文本任务包、Markdown 任务包、远程任务包 zip、分享页任务包、文件存储任务包 | 读取已有任务包；外部 AI 纯文本 Markdown 先落成任务包文件和独占 `SESSION_STATE.md` 再执行；本机 zip、远程 zip 直链或分享页 URL 先临时下载、解压、校验并导入，再从 `SESSION_STATE.md` 恢复执行 | `docs/ai-instructions/instructions/create-task-prompt-project.md` |
| `#避免重复踩坑` | `#T008` | 避免重复踩坑、查历史经验、这个坑以后别再踩 | 先查 `experience-index.md`，按命中经验修正执行路径 | `docs/ai-instructions/instructions/avoid-repeat-pitfalls.md` |
| `#项目升级` | `#T023` | 模板派生项目升级、升级到最新模板、同步模板新特性、取舍矩阵 | 先解析源模板来源、盘点目标项目事实，再按取舍矩阵增量同步模板能力 | `docs/ai-instructions/instructions/project-upgrade-strategy.md` |
| `#模版升级` | `#T024/#T026` | 模板升级资产、派生项目模板升级、模板漂移升级、当前模板落后多少提交、applied_version、source_channel、受控内部来源、public_seed | 在源模板仓库中生成升级资产；在派生项目中先识别 Seed 来源通道，再运行模板漂移计划，计算落后源模板提交数，生成当前会话执行提示词并执行 | `docs/ai-instructions/instructions/template-upgrade-strategy.md` / `docs/ai-instructions/instructions/derived-template-drift-upgrade.md` |
| `#种子仓库升级` | `#T027` | 种子仓库升级、模板仓库升级建议、回流种子仓库、反向升级种子仓库、能力回流、建议更新模板仓库 | 在派生项目中记录可回流种子仓库的候选能力，按 S0-S4 分级，并生成 `prompts/codex/seed-repository-upgrade-prompts/` 下的反向回流提示词；在种子仓库中按提示词评估、接纳/拒绝/补证据、增量实现并生成必要升级资产 | `docs/ai-instructions/instructions/seed-repository-upgrade.md` |
| `#模板化` | `#T009/改造` | 改造成模板仓库、接入 MAW 模板、模板化改造 | 把任意既有项目增量接入 MAW 模板规范 | `docs/ai-instructions/instructions/use-builtin-template-task-packs.md` |
| `#模块` | `#T010` | 生成 modules、拆分模块、模块树、模块拆细、模块太大、AI 模块上下文、ai-context、ai_doc | 先生成模块树和 group/leaf 判定，再创建叶子模块档案；复杂模块可按需补 `ai-context.md`，不批量复制 `_ai` 副本 | `docs/ai-instructions/instructions/split-module-tree.md` |
| `#模块地图` | `#T036` | 初始化 modules、检查 modules、审计 modules、查漏补缺、清理过期、变更影响、发布前检查、页面 URL 索引、API 索引、route-api-index、页面审计页、后端审计页、traceability、module_map_score | 对已有项目 modules 做初始化、检查、审计和规范化改造：一级模块维护 URL/API 定位索引，二级模块维护 `module.md`、AI 边界指引、证据字段和按需 detail docs，缺失内容按渐进式策略补全，定期审计输出 `module_map_score` | `docs/ai-instructions/instructions/module-map.md` |
| `#项目评审` | `#T037/项目评审` | 项目评审、需求评审会议、业务流程评审、开发方向核对、docs 口径治理 | AI 作为需求评审会主讲人，基于 docs 复述项目目标、业务流程、验收目标和口径冲突，生成 `docs/project-review-audits/rounds/<review_id>/review.md`，并在报告和收口中给出 `#项目审计：<评审报告路径>` 接续调用 | `docs/ai-instructions/instructions/project-review-audit.md` |
| `#项目审计` | `#T037/项目审计` | 项目审计、验收目标审计、实现程度审计、评审报告路径、项目审计: | 读取指定项目评审报告，按验收目标审计实现程度、证据强度、docs 与实现一致性、缺口和后续推进建议，输出同轮审计报告 | `docs/ai-instructions/instructions/project-review-audit.md` |
| `#项目健康` | `#T038` | 项目健康、健康上下文、记录项目健康问题、记录这个缺口、审计项目健康、生成健康关注建议、把缺口变成调研问题、.maw/health | 维护 `.maw/health/` 项目健康上下文，记录健康问题、需求事实、决策、普通健康待办、审计缺口、调研摘要和验收缺口，并为 Mawflow 主项目导入和 AI 健康关注预留结构 | `docs/ai-instructions/instructions/project-health-context.md` |
| `#模板特性提示词` | `#T011` | 生成模板新特性升级提示词、生成轻量升级提示词、把这条变动生成升级提示词 | 在源模板仓库中为单项模板能力生成可复制到派生项目的轻量升级提示词 | `docs/ai-instructions/instructions/generate-template-feature-upgrade-prompt.md` |
| `#模板升级` | `#T024/#T026` | 模板升级资产、派生项目模板升级、模板漂移升级、source_channel | 在源模板仓库中生成升级资产；在派生项目中先识别 Seed 来源通道，再计算模板漂移并当前会话执行升级 | `docs/ai-instructions/instructions/template-upgrade-strategy.md` / `docs/ai-instructions/instructions/derived-template-drift-upgrade.md` |
| `#交接任务` | `#T012` | ChatGPT 生成 Codex 任务、外部 AI 任务交接、方案转任务包、生成 Codex 任务 Markdown、生成 Codex 任务 zip | 把外部 AI 已确定方案整理成可下载、可复制 Markdown；小任务是一段任务提示词，大任务必须写出任务包每个文件完整内容、让 Codex 落任务提示词工程后继续执行，并在末尾给出用法；明确要求 zip 时才生成 zip | `docs/ai-instructions/instructions/external-ai-to-codex-task-handoff.md` |
| `#提主` | `#T013` | 合并dev到main、dev 合并 main、合并主分支、内部提主合并、同步 main 镜像、多镜像仓库 | 把项目内部源分支合并到主分支，推送 `origin/main`，并按 `repository_mirrors.auto_sync_after_project_push`、`default_targets` 和目标级开关同步一个或多个仓库级镜像 | `docs/ai-instructions/instructions/dev-to-main-merge.md` |
| `#发布` | `#T014` | 发布组件、更新发布、立即发布生效、执行SQL、上线、部署、FTP 部署、覆盖部署、发布测试、发布上线、发布生产、发布生成、发布版本状态、发布名单、本地代码最新 | 发布指定 app_key；未写环境时使用配置默认环境，也可指定 test、staging、production 或项目自定义环境；中文口令中，`发布测试` 是本地调试版本并需给可访问调试地址，`发布上线` 部署编译包到 `remote_staging_server` 且仍属于测试，需要给线上可访问地址，两者都允许当前工作区未提交改动参与测试发布并记录 dirty snapshot；`发布生产` 部署到 `remote_production_server`，生产环境安装/生产版本上线必须人工审计，且执行前必须确认本地候选 commit 等于发布来源远端分支、工作区干净；`发布生成` 兼容为生产发布；未写组件时读取对应 `remote_server.default_release_components` 并用 `artifacts/release-state/<env>/<app_key>.json` 的 commit 记录按组件路径差异筛选发布名单；配置 FTP/FTPS 覆盖部署时先运行 `deploy-via-ftp.py` 计划，确认后才 `--execute` | `docs/ai-instructions/instructions/release-component.md` |
| `#发布公开镜像` | `#T039` | 发布公开镜像、发布开源镜像、发布镜像、公开发布镜像、私有仓发布到公开仓、开发完成一个版本后发布到公开仓 | 把私有开发仓库中已定版的版本人工发布到公开仓；先运行 `publish-repository-mirror.sh plan`，通过版本、tag、开源和脱敏闸门后才 `publish --execute`；支持同历史发布和脱敏导出发布 | `docs/ai-instructions/instructions/publish-repository-mirror.md` |
| `#安装环境` | `#T035` | 安装环境、安装开发环境、安装本地环境、修复本地环境、安装线上环境、安装生产环境、配置开发环境、配置线上环境、配置生产环境、本地开发环境、本地测试环境 | 安装或开启开发/线上/生产环境前，先做只读环境确认，展示哪些复用本机现有、哪些用 Docker、哪些需本机或远端安装、哪些高风险动作需确认；安装本地环境和修复本地环境等同安装开发环境；确认后执行安装、启动、健康检查，把本地测试启动命令落到根 `package.json` scripts，默认实现 `npm run dev` 并输出本机与局域网调试地址，可转发到 `local:dev`，用 `scripts:sync:check` 保持可单独运行脚本入口完整，在收口提供测试入口 | `docs/ai-instructions/instructions/install-environment.md` |
| `#客户仓库同步` | `#T015` | 客户仓库同步、external_mapped、分支流向、客户分支角色、客户单分支 | 总览 `INTERNAL_DEV`、`INTERNAL_RELEASE`、`CUSTOMER_BASE`、`CUSTOMER_DELIVERY`、`CUSTOMER_INTEGRATION` 和单分支模式 | `docs/ai-instructions/instructions/customer-repository-branch-flow.md` |
| `#客入` | `#T016` | 客入、从客户主线拉代码、从客户基线同步、客户公共模块回流、本机客户仓、大仓客入 | 从 `CUSTOMER_BASE` 同步到 `INTERNAL_DEV`，默认不从客户交付分支常规客入；客户仓很大时可先更新本机预克隆仓再从本地目录读取 | `docs/ai-instructions/instructions/customer-in.md` |
| `#客主` | `#T017` | 客主、刷新客户交付分支、客户主分支到专属分支、本机客户仓 | 将 `CUSTOMER_BASE` 刷新到 `CUSTOMER_DELIVERY`，正式客出前执行或检查；可使用本机客户仓作为 clone reference | `docs/ai-instructions/instructions/customer-base-to-delivery.md` |
| `#客出` | `#T018` | 客出、同步到客户仓、推客户分支、客户交付 | 从 `INTERNAL_RELEASE` 同步到 `CUSTOMER_DELIVERY/CUSTOMER_ONLY`，遵守白名单、脱敏、plan 和证据保留 | `docs/ai-instructions/instructions/customer-out.md` |
| `#客户合主` | `#T019` | 客户合主、客户交付分支合入客户主线、客户集成分支 | 创建或计划 `CUSTOMER_DELIVERY -> CUSTOMER_INTEGRATION -> CUSTOMER_BASE`，默认由客户负责人确认 | `docs/ai-instructions/instructions/customer-delivery-to-base.md` |
| `#收口格式` | `#T020` | 中文收口、最终说明格式、final closeout、简化收口、详细收口、完整收口、展开验证、验证明细、技术元数据、参数获取步骤、建议选项、敏感参数本机填写、.local 填写文件 | 按中文人类优先格式说明结论、变更、验证、Git/镜像、种子仓库升级建议、发布影响和技术元数据；默认简化主展示和验证结论，用户要求详细收口或验证异常/高风险时展开命令明细和完整技术元数据；需要用户补参数时给出获取步骤和建议选项，涉及敏感参数时先创建 `.local` 本机填写文件 | `docs/ai-instructions/instructions/final-closeout-response.md` |
| `#模块发现` | `#T021` | 候选模块、module_candidate、证据不足、不确定 module_key | 证据不足时先记录候选模块、证据和待确认问题，不强行创建正式 leaf | `docs/ai-instructions/instructions/progressive-module-discovery.md` |
| `#项目记忆` | `#T022` | 记忆闭环、越用越聪明、用户澄清、长期偏好、memory_update | 把可复用项目知识沉淀到 `docs/ai-instructions/`，并在收口说明记忆更新 | `docs/ai-instructions/instructions/project-memory-loop.md` |
| `#本机记忆` | `#T022/local` | 本机差异、本机路径、端口、工具链、代理、local_update | 把当前设备差异留在 `.local/`，只提交 README/example | `docs/ai-instructions/instructions/project-memory-loop.md` |
| `#待办任务` | `#T028` | 新增待办、记录待办、完成待办、取消待办、查询待办、待办影响、假设已完成、先不做但依赖、被依赖但暂不实现、完成后联调 | 管理被当前业务闭环依赖但暂不实现的跨模块待办，记录当前假设、受影响模块、完成/取消影响和联调建议 | `docs/ai-instructions/instructions/todo-task-governance.md` |
| `#MCP服务诊断` | `#T029` | MCP 服务诊断、项目级 MCP、本地 MCP 自检、tools/list、maw.audit.ping、MAW_MCP_ENDPOINT | 检查项目级 MCP 连通、initialize、工具列表、project_key、仓库身份、宿主机用途、项目归属、开发绑定、源码访问方式、多项目隔离、AI 可写目录、code 同步安全和授权拒绝边界；无 MCP 时 graceful warning | `docs/ai-instructions/instructions/mcp-service-diagnostics.md` |
| `#技术地图` | `#T030` | 技术地图、项目提示、能力快照、公共能力、功能基类、API 快照、能力索引、项目大屏、项目审计、项目巡检、澄清记录、缺口记录、口径变更、AI 前置条件 | 查询和维护 `.maw/capabilities.yaml`、`.maw/project-signals.yaml`、技术地图和元数据提取脚本；开发前查复用能力，收口时记录 capability_map_update_status 和 project_signal_update_status | `docs/ai-instructions/instructions/technical-map-project-metadata.md` |
| `#仓库身份` | `#T031` | 仓库身份、身份地图、仓库角色、多角色、角色目录、种子仓、主仓、平台项目仓、客户项目仓、混合仓、unknown_legacy、repository identity | 查询和维护 `.maw/repository-identity.yaml`、`.maw/repository-identity.d/<role>/*.yaml`、声明角色、检测角色和差异化约束；高风险操作前确认身份一致性，收口时记录 repository_identity_update_status | `docs/ai-instructions/instructions/repository-identity-map.md` |
| `#脚本规范` | `#T032` | 脚本规范、脚本契约、AI Python Script Contract、规范化脚本、脚本标准化、已有脚本升级、脚本输出规范、脚本日志降噪、耗时任务脚本化、Python 脚本优先、py-first | 审计和升级现有脚本到 AI Python Script Contract；优先处理高频、高风险、耗时、噪音大和跨系统差异明显的脚本，要求结构化输出、日志落盘、状态可恢复和多环境兼容 | `docs/ai-instructions/instructions/script-contract-upgrade.md` |
| `#文档索引` | `#T033` | 文档写读契约、文档读取契约、docs 索引、生成文档索引、健康面板文档来源、产品设计索引、模块设计索引、doc-read-contract | 为新写或重构的产品、需求、设计、模块、计划和审计文档补可读元数据；生成项目健康、审计和 AI 任务可读取的文档索引，历史文档默认 warning-only | `docs/ai-instructions/instructions/doc-read-contract.md` |
| `#会话概要` | `#T034` | 最近会话、会话摘要、任务概要、最近任务、读取最近几次会话、recent-session-briefs、session briefs、跨设备接力、短期记忆 | 任务开始时检索最近会话概要，判断相关后再细读；任务结束时写入一会话一文件的共享概要，支持多电脑协同且避免全量读取历史聊天 | `docs/ai-instructions/instructions/recent-session-briefs.md` |
| `#模板设计` | 文档入口 | 模板设计、用户版设计、模板仓库设计 | 查看面向人类用户的模板仓库完整设计说明 | `docs/template-repository-design.md` |
| `#AI设计` | 文档入口 | AI设计、AI 版设计、Agent 执行协议、模板执行协议 | 查看面向 Codex/Agent/Reviewer 的完整设计与执行协议 | `docs/template-repository-ai-design.md` |
| `#生成交付文档` | `#T025` | 交付文档、生成用户手册、生成概要设计、生成部署手册、生成文档事实稿 | 按 modules 生成用户手册事实稿、按 design 生成概要设计事实稿、按 ops 生成部署手册事实稿；只生成 Markdown 事实稿，格式由用户模板或专门文档 AI 处理 | `docs/ai-instructions/instructions/generate-delivery-docs.md` |

## 常用任务包

| 任务包 | 用途 | 入口 |
| --- | --- | --- |
| 模板派生项目升级 | 已基于本模板的项目同步新版模板特性，先审计取舍再增量合并 | `prompts/codex/task-packs/template-feature-upgrade-codex-tasks/` |
| 任意项目模板化改造 | 为既有项目建立 MAW 协作控制面和模块/指令/任务包规范 | `prompts/codex/task-packs/adopt-maw-project-template-codex-tasks/` |

## 常用脚本

```bash
bash ops/scripts/check-ai-framework-consistency.sh
bash ops/scripts/check-template-module-docs.sh
python3 ops/scripts/check-ai-python-script-contract.py --format json
python3 ops/scripts/run-project-tests.py --format json
python3 ops/scripts/check-doc-read-contract.py --format json
python3 ops/scripts/extract-doc-index.py --format json
python3 ops/scripts/check-project-health-context.py --format json
python3 ops/scripts/recent-session-briefs.py --recent 8 --format markdown
bash ops/scripts/check-code-deliverable.sh
bash ops/scripts/export-code-only.sh --dry-run
bash ops/scripts/export-code-only.sh --mode developer --dry-run
bash ops/scripts/export-code-only.sh --mode customer --zip --dry-run
```

## 使用建议

- 指令触发词可以自然表达，不需要逐字复制。
- 人类速记优先使用 `#关键字`；需要完全精确或同一关键词可能命中多条指令时，模板指令用 `#T001`，业务项目指令用 `#P001`。
- AI 判断存在歧义时，必须先向用户确认要执行哪条指令。
- 用户习惯用语、别称或项目内叫法一旦确认含义，后续收口主展示优先沿用用户口径；如果仍有歧义，先问清楚再执行或沉淀。
- `#模板升级/#模版升级` 未指定 commit 时，不以“有没有 commit”决定源仓库或派生仓库；先按当前仓库角色路由。源模板仓库走 `TINST-024` 生成迁移说明、提示词或任务包；派生项目走 `TINST-026`，用 `.maw/template-source.yaml` 的 `template_source.version`（默认 `main`）解析目标模板 commit，再和 `applied_version` 比较并执行。
- “种子仓库”和“模板仓库”统一指 `maw-project-template`。派生项目开发过程中发现适合回流到种子仓库的优化或新增能力时，使用 `#种子仓库升级`：先记录到 `docs/seed-repository-upgrade-candidates.md`，再按 S0-S4 分级，并把可落库提示词写入 `prompts/codex/seed-repository-upgrade-prompts/`；该流程只做增项和兼容增强，不覆盖历史派生项目事实。
- 执行“模板派生项目升级”或“任意项目模板化改造”时，使用 `GETTING_STARTED.md` 中的完整 Codex 提示词，必须带源模板来源和版本；本机路径只作为当次输入或 `.local` 配置，不写入长期文档。
- 在源模板仓库里，想把某个新特性同步给派生项目时说 `#模板升级/#模版升级`，AI 会生成迁移说明、提示词或任务包。在派生项目里，同样的触发词用于按 `template_source.applied_version` 计算落后源模板多少提交，生成当前会话执行提示词并执行。种子仓库默认组件只有 `server` / `client`，已有项目中的 `admin`、移动端、任务进程或其它 app_key 必须按项目事实保护。
- 已经在 ChatGPT 或其它外部 AI 中讨论完方案时，优先按 `CHATGPT_TO_CODEX.md` 或 `#交接任务` 生成可下载、可复制 Markdown；小任务复制提示词到 Codex，大任务复制 Markdown 内的“任务提示词工程落地 + 执行”提示词。只有明确要求 zip 时，才生成任务包 zip。
- `#跑任务包` 可以接收仓库内任务包目录、外部 AI 纯文本 Markdown、本机任务包 zip、远程 zip 直链，或包含下载方式的分享页 URL。纯文本 Markdown 先落任务包文件再执行；远程分享页会先按 TINST-007 下载到临时工作区、解压和校验，通过后再导入 `prompts/codex/task-packs/`；可道云/Kodbox 等分享页按分享页处理，提取码或访问密码只用于当次会话，不写入可提交文件。
- 需要理解模板整体设计时，使用 `#模板设计` 查看用户版完整设计；需要审查 AI 执行协议、升级策略、模块发现、`.local`、项目记忆、中文收口、code-only 交付或交付文档事实稿规则时，使用 `#AI设计`。
- 需要生成用户手册、概要设计或部署手册初稿时，使用 `#生成交付文档`。用户手册事实来自 `.maw/modules.yaml` 和 `docs/modules/`，概要设计事实来自 `docs/design/`，部署手册事实来自 `ops/`；未指定输出位置时默认在会话中输出 Markdown 事实稿，最终格式由用户模板、人工或专门文档 AI 处理。
- 内部 `dev -> main` 收口优先使用 `#提主`；它只处理本项目仓库分支合并和 `repository_mirrors` 仓库级镜像同步，不处理客户仓库同步、组件镜像同步、公开发布镜像或应用发布部署。仓库级镜像可配置多个 target：默认按 `repository_mirrors.default_targets` 同步，临时全量查看或同步可用 `ops/scripts/sync-repository-mirror.sh plan --all` / `push --all --execute`。
- 私有开发仓定版后发布到公开仓使用 `#发布公开镜像`；它读取 `repository_publish_mirrors`，只在人工显式 `publish --execute` 时写公开远端，不参与普通 push 后镜像同步。
- 客户仓库 `external_mapped` 流程按方向选择 `#客入`、`#客主`、`#客出`、`#客户合主`；它不是 `component_mirrors` 或 `repository_mirrors` 镜像同步。
- 客户仓很大时，可先在本机 clone 客户仓，再通过 `.maw/repositories.local.yaml`、`.local/.maw/repositories.yaml` 的 `external_mapped.components.<component>.external.local_repository_path` 或命令参数 `--local-repository-path` 使用；真实本机路径不要写进共享配置。
- 测试/正式等多套客户仓分支配置可拆到 `.maw/repositories.d/*.yaml`，顶层 `enabled: false/true` 控制是否参与合并；同一时间只启用一套会覆盖相同 `sync.branch_roles` 的片段。
- 最终说明中如果本轮修改了某组件且“需要发布才会生效，当前未发布/未验证”，必须从 `.maw/releases.yaml`、`.maw/environments.yaml` 和 `code/<app_key>/.maw.component.yaml` 读取发布配置，同时给出可复制的默认发布指令和指定环境发布指令；多个组件需要发布时按 app_key 分别列出，用户可以复制其中一条或多条选择部分发布。用户说 `发布测试`、`发布上线`、`发布生产` 或 `发布生成` 且未指定组件时，先按对应 `remote_server.default_release_components` 取得候选范围，再按发布版本状态和组件路径差异计算实际发布名单。发布测试收口给本地调试地址；发布上线收口给线上可访问地址并说明它仍属测试；两者如使用未提交改动，必须写明 dirty snapshot；发布生产收口写明人工审计状态，且执行前必须确认本地候选 commit 等于发布来源远端分支、工作区干净。收口末尾必须询问是否“确认发布全部”，用户回复“确认发布全部/确认/是”则按 `#发布` 执行全部待发布组件。
- 最终说明中必须判断本地开发/测试入口是否需要更新。项目已配置本地环境时，修改后应实时刷新或开启本地开发调试入口，并给出 URL、健康检查、关键页面/API 或测试命令；本机未配置好环境时，说明缺失项并给出 `#安装开发环境`。安装开发/线上/生产环境时，统一先环境确认，再展示方案和风险，确认后执行。
- 新增或调整 `docs/ai-instructions/instructions/**` 中的项目指令时，必须同步维护本文件中的快捷调用、触发关键词、概要和调用示例。
- 涉及项目路径时，在可提交文档中使用项目根相对路径。
- 根目录 `README.md` 属于业务项目；模板仓库说明看 `TEMPLATE_OVERVIEW.md`。
- 涉及模块生成时，优先说“生成模块树”或“模块拆细”，不要直接让 AI 把大模块生成成单个 `module.md`。
- 涉及已有项目 modules 初始化、检查、URL/API 索引、按页面/后端审计改造、清理过期文档或发布前模块风险确认时，优先使用 `#模块地图`，并要求渐进式补全和 `last_verified_commit` 证据记录。
- 涉及项目开发方向、需求理解、业务流程、验收目标或 docs 口径核对时，优先使用 `#项目评审`；评审报告经人工确认后，用报告内给出的 `#项目审计：<评审报告路径>` 继续审计。
- 涉及项目健康问题池、健康上下文、需求事实、决策记录、调研会话摘要、验收缺口或主项目导入 `.maw/health/` 时，使用 `#项目健康`；跨模块被依赖待办仍走 `#待办任务`，完整评审/审计报告仍走 `#项目评审/#项目审计`。
- 涉及跨模块复用、公共 API、功能基类、项目审计元数据、巡检或数据大屏时，优先使用 `#技术地图`；机器可读提取入口是 `ops/scripts/extract-project-metadata.py`。用户给出 `#项目审计：<评审报告路径>` 或 `项目审计:<评审报告路径>` 时，明确走 `#项目审计` / `TINST-037`。
- 涉及发布、镜像仓库、客户仓库、密钥或生产数据时，让 AI 先执行脱敏和风险检查。
