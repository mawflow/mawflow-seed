# 指令：创建和执行任务提示词工程

## 元信息

- ID：TINST-007
- 类型：项目指令
- 状态：启用
- 维护位置：`docs/ai-instructions/instructions/create-task-prompt-project.md`
- 触发词：#任务包、#跑任务包、创建任务提示词工程、生成任务提示词工程、创建 Codex 任务包、生成 task pack、执行任务提示词工程、执行指定任务提示词工程、继续任务提示词工程、纯文本任务包、Markdown 任务包、任务提示词工程落地、远程任务包 zip、分享页任务包、可道云/Kodbox 任务包、MAW 文件存储任务包、file-storage 任务包、可信文件存储 任务包
- 适用范围：把复杂需求、产品方案、实施计划或复盘经验整理为可恢复、可分阶段执行的 Codex 任务提示词工程；或在当前会话中执行已有任务提示词工程。已有任务包可以是仓库内目录、本机 zip、远程 zip 直链，或包含下载方式的远程分享页；外部 AI 也可能直接给出可下载、可复制的 Markdown 纯文本，要求 Codex 先创建任务包文件再执行。其中外部 AI 生成的 zip 任务包应优先视为按根目录 `CHATGPT_TO_CODEX.md` 生成的交接物来校验。

## 便捷调用

创建任务提示词工程：

```text
#任务包：<需求、方案、实施计划、资料路径或任务目标>
```

执行任务提示词工程：

```text
#跑任务包：prompts/codex/task-packs/<slug>-codex-tasks
#跑任务包：<本机任务包 zip 文件>
#跑任务包：<远程任务包 zip 直链或分享页 URL>
#跑任务包：https://files.example.com/api/maw-file-storage/public?file_key=<file_key>&token=<token>
#跑任务包：https://files.example.com/file-storage/extract?file_key=<file_key>&token=<token>&pwd=<pwd>
```

外部 AI 纯文本大任务交接：

```text
<复制 ChatGPT 生成的 Markdown 中的【Codex 任务提示词】全文>
```

如果用户输入能定位到一个已存在目录，且目录包含 `manifest.json` 和 `prompts/00-session-runbook.md`，按“执行任务提示词工程”处理。如果用户输入是本机 zip、远程 zip 直链，或包含下载入口的远程分享页 URL，先按“任务包导入协议”处理；导入校验通过后再执行。如果用户输入包含“任务类型：大任务提示词工程落地 + 执行”、任务包目录和各文件内容，按“纯文本任务包落地协议”处理。其它输入按“创建任务提示词工程”处理。

内置任务包快捷入口：

```text
#跑任务包：prompts/codex/task-packs/template-feature-upgrade-codex-tasks
#跑任务包：prompts/codex/task-packs/adopt-maw-project-template-codex-tasks
```

当用户说“模板仓库升级”“同步模板新特性”“把任意项目改造成模板仓库”等短语时，先按 `TINST-009` 选择内置任务包，再按本指令的执行协议运行。

## 目标

任务提示词工程是比单条提示词更完整的任务包。它必须让后续 Codex 会话在不依赖原始聊天记录、不依赖本机 Codex skill 的情况下，按仓库内文件完成任务、恢复中断、记录验证并明确收口状态。

默认位置：

```text
prompts/codex/task-packs/<slug>-codex-tasks/
```

## 输入要求

- 必需输入：任务目标、需求描述、方案文档路径或既有任务包路径。
- 推荐输入：业务背景、期望结果、相关 `module_key`、app_key、组件路径、资料路径、验收方式、发布目标和风险边界。
- 可选输入：执行模式、任务拆分粒度、是否只生成不执行、是否允许同会话自动连续执行；执行既有任务包时可提供本机 zip 路径、远程 zip 直链、远程分享页 URL、临时访问口令或提取码；外部 AI 纯文本交接时可提供可下载 `.md` 或直接粘贴 Markdown 正文。
- 缺失时处理：能从当前仓库文件确认的先确认；仍无法判断任务边界、发布目标或高风险操作时，先向用户追问，不要编造。

## 创建步骤

1. 读取 `.maw/codex-context.md`、`docs/ai-instructions/experience-index.md`、`prompts/README.md`、`prompts/codex/README.md` 和 `prompts/codex/task-packs/README.md`；只在索引或用户明确路径命中时读取 `solutions/**` 的具体详情。
2. 如果任务涉及模块、页面、接口、表、配置、发布或组件，读取 `.maw/modules.yaml` 并按需读取对应模块档案；不要全量读取 `docs/modules/**`。
3. 从需求生成小写短横线 `slug`。不要在任务包路径中写本机项目绝对路径。
4. 创建 `prompts/codex/task-packs/<slug>-codex-tasks/`，至少包含：
   - `README.md`
   - `EXECUTE_PROMPT.md`
   - `PLAN.md`
   - `manifest.json`
   - `prompts/00-session-runbook.md`
   - `prompts/01-*.md` 到最终验收任务
5. 为该任务包创建独占状态文件，推荐路径：

```text
docs/implementation/<topic>/<slug>-codex-tasks/SESSION_STATE.md
```

6. 默认执行模式使用 `same_session_auto_run`：同一 Codex 会话中完成任务 `01` 后更新 `SESSION_STATE.md`，并在该子任务产生实际改动时按仓库规则验证、提交、推送当前分支；推送项目仓库成功后先运行仓库级 mirror 计划命令，按有效计划决定是否继续同步 mirror；然后再继续任务 `02`，直到 `NEXT_TASK=none`、遇到阻塞、上下文不安全或用户打断。
7. 如果用户明确要求每个任务单独交接，使用 `per_task_handoff`；如果希望自动执行但随时可交接，使用 `hybrid_auto_with_handoff`。
8. `EXECUTE_PROMPT.md` 必须写成可直接复制到 Codex 的执行提示词，包含任务包路径、状态文件路径、执行模式、恢复方式、验证、提交推送和最终说明要求。
9. `00-session-runbook.md` 必须写清楚目标、当前基线、最高优先级规则、必读文件、执行规则、经验索引检索规则、状态文件格式、中断恢复协议、任务列表和第一个任务。
10. 每个子任务提示词必须包含：目标、必读文件、实现要求、建议命令、验收标准、最终说明要求。
11. `README.md` 面向人，写清复制什么、会做什么、不会做什么、完成后看到什么；`EXECUTE_PROMPT.md` 面向人复制给 Codex，短、完整、自包含；`prompts/*.md` 面向 AI，承载详细规则、验收和收口字段。
12. `manifest.json` 必须支持并默认写入 `language: zh-CN`、`documentation_language: zh-CN`、`audience: human_and_codex`、`closeout_profile: zh_cn_human_first` 和 `delivery_mode: code_only`；不适用 code-only 时在任务包中写明原因。
13. 任务包 README、`EXECUTE_PROMPT.md`、runbook、子任务正文和任务执行中新增或改写的项目文档必须继承 `language: zh-CN` 与 `.maw/interaction.yaml` 的 `documentation/generated_documentation/task_pack_body` 默认值。正文和 Markdown 标题默认写中文；英文仅保留在代码标识、路径、命令、协议名、第三方原文、机器 key、品牌/专有名词或用户明确要求的英文内容中。
14. 新建任务包或项目文档时，不使用 `Goal`、`Baseline`、`Objective`、`Required Reads`、`Implementation Requirements`、`Acceptance Criteria`、`Final Response Requirements`、`Component Guide`、`Scope`、`Build Notes`、`Sensitive Config` 等英文标题；对应中文建议为“目标”“基线”“必读文件”“实现要求”“验收标准”“最终说明要求”“组件说明”“范围”“构建说明”“敏感配置”。
15. 如果任务包 manifest、升级资产或配置样例需要同时给人和 AI 读取说明，默认展示字段写中文；英文说明放入同一对象的 `i18n.ai.en-US`，中文人读说明可放入 `i18n.human.zh-CN`。英文主要服务 AI，不作为人读默认文案。
16. 每个子任务的最终说明要求必须采用中文、人类优先主展示，并在末尾“技术元数据”中包含 `experience_lookup`、`module_key`、`module_dossier_updated`、`updated_module_docs`、`hit_code_components`、`release_update_status`、`release_commands`、`release_confirmation_prompt`、`code_delivery_status`、`memory_update`、`local_update`、`upgrade_strategy_update` 和 `seed_repository_upgrade_suggestions`。
17. 任务包内必须继承本仓库规则：路径使用项目根相对路径、先检索 `docs/ai-instructions/experience-index.md`、只按命中读取 `solutions/**`、按需读取模块档案、更新受影响文档、判断命中 code 组件和发布状态；需要发布但当前未发布或未验证时，按 app_key 输出可复制 `#发布` 指令，并在收口末尾询问是否“确认发布全部”，多个 app_key 可由用户复制具体指令选择部分发布，用户回复“确认发布全部/确认/是”则发布全部待发布组件，发布指令和默认环境必须来自 `.maw/releases.yaml` 与 `code/<app_key>/.maw.component.yaml`；需要交付 `code/` 时先运行 `ops/scripts/check-code-deliverable.sh`，需要导出时先运行 `ops/scripts/export-code-only.sh --dry-run`；不得读取 `docs/archive/**` 作为当前依据、不得提交真实密钥或本机 local 配置，并在每个产生实际改动且可独立验证的子任务完成后主动提交、推送当前分支，推送后运行仓库级 mirror 计划命令并按有效计划同步 mirror。

## 纯文本任务包落地协议

当用户粘贴 ChatGPT 等外部 AI 生成的 Markdown 纯文本，且内容要求“任务提示词工程落地 + 执行”时，必须先把纯文本里的任务包文件落到仓库，再按普通任务包执行。不要因为输入是纯文本就把大任务当成一条不可恢复的长提示词直接实现。

1. 先确认纯文本中包含任务包目录、状态文件路径、任务目标、执行要求和“任务包文件内容”；如果缺少关键文件内容，先让用户回到 ChatGPT 补齐可下载/可复制 Markdown，或由当前 Codex 按“创建步骤”补齐任务包。
2. 任务包目标目录必须是 `prompts/codex/task-packs/<slug>-codex-tasks/`；状态文件优先使用 `docs/implementation/<topic>/<slug>-codex-tasks/SESSION_STATE.md`。路径不得使用本机项目绝对路径。
3. 只写入纯文本要求的任务包文件和状态文件；不得把 ChatGPT 原始讨论全文、仓库源码副本、`.git`、`.local`、真实密钥、token、客户隐私、生产连接串、依赖目录或构建产物写入任务包。
4. 写入前运行 `git status --short`，识别已有未提交改动；不得回滚或覆盖无关改动。目标目录已存在时，不得静默覆盖，先判断是继续执行已有任务包、改名新建，还是需要用户确认覆盖。
5. 写入后校验 `manifest.json` 可解析，任务包包含 `README.md`、`EXECUTE_PROMPT.md`、`PLAN.md`、`prompts/00-session-runbook.md` 和至少一个编号子任务，且出现 `SESSION_STATE`、`NEXT_TASK`、`RESUME_FROM`。
6. 纯文本要求写完后继续执行时，不要停在“任务包已创建”。立即读取 `EXECUTE_PROMPT.md`、`PLAN.md`、`manifest.json`、`prompts/00-session-runbook.md` 和 `SESSION_STATE.md`，然后进入“执行步骤”。
7. 如果纯文本只是让 Codex 创建任务包而没有要求执行，创建并验证后按用户要求停下，给出 `#跑任务包：prompts/codex/task-packs/<slug>-codex-tasks`。

## 任务包导入协议

当 `#跑任务包` 的参数不是已存在任务包目录，而是本机 zip、远程 zip 直链或远程分享页 URL 时，必须先导入和校验，不得直接执行远程内容。

1. 先分类输入，并确认来源契约：
   - 外部 AI 或用户提供的 zip/下载地址，默认按根目录 `CHATGPT_TO_CODEX.md` 的“大任务 zip 输出格式”和“任务包内容要求”校验；不符合该契约时，不得直接导入执行。
   - 已存在目录：确认 `manifest.json` 和 `prompts/00-session-runbook.md` 后进入执行步骤。
   - 本机 zip：复制或读取到临时工作区后解压校验。
   - 远程 zip 直链：使用支持重定向的下载方式保存到临时工作区，例如 `curl -L --fail --output <临时文件> <URL>`。
   - 远程分享页：先检查页面是否提供下载方式，再取得真实 zip 下载入口；可道云/Kodbox 分享页，包括 `/#s/<share-id>` 这类 hash 路由，应按分享页处理，不把页面 URL 当成 zip 直接解压。
   - 自建可信文件存储服务 `https://files.example.com` 必须重点兼容：
     - `/api/maw-file-storage/public?file_key=<file_key>&token=<token>` 是直接可下载 zip URL，按远程 zip 直链处理。
     - `/file-storage/extract?file_key=<file_key>&token=<token>&pwd=<pwd>` 是带密码分享页，按远程分享页处理；`pwd` 只用于当次会话。页面会自动填入密码，CLI 场景可向页面表单 action 发 POST，字段名为 `extract_password`。
     - 推荐先用仓库脚本下载到临时目录：`python3 ops/scripts/download-task-pack-url.py "<URL>" --output "<临时目录>/task-pack.zip"`；该脚本会识别直链和分享页，输出时脱敏 `token`、`pwd` 等查询参数。
2. 临时工作区优先使用系统临时目录，或项目已忽略的临时目录；不要先把下载物放入 `prompts/codex/task-packs/`。
3. 如果分享页需要提取码、访问密码、登录态或一次性下载链接，优先从用户输入 URL 的一次性查询参数或页面表单读取；仍缺失时向用户索取或让用户提供直链/本机 zip。这些信息只用于当次会话，不写入可提交文档、任务包、日志或最终说明；命令输出和错误说明必须脱敏。
4. 下载后先校验文件确实是 zip，再解压到临时目录。解压时必须拒绝路径穿越、绝对路径、隐藏 `.git` 仓库、`.local` 私有资料、真实密钥、依赖目录、构建产物、仓库源码副本或明显无关大文件。
5. 接受两种结构：
   - zip 内直接包含 `prompts/codex/task-packs/<slug>-codex-tasks/`。
   - zip 根目录是单个 `<slug>-codex-tasks/`，其中包含任务包文件。
6. 任务包目录必须包含 `manifest.json`、`README.md`、`EXECUTE_PROMPT.md`、`PLAN.md` 和 `prompts/00-session-runbook.md`。缺少任一必须文件时，不得作为结构无误的任务包自动导入或执行；如用户确认这是旧格式任务包，只能转入人工审阅或让用户补齐文件后重试。
7. 目标目录使用 `manifest.json` 的 `package` 字段或 zip 内单顶层目录名生成，并规范为 `prompts/codex/task-packs/<slug>-codex-tasks/`。目标目录已存在时，不得覆盖或合并；先让用户确认覆盖、改名导入或继续执行已有目录。
8. 只有结构、安全和目标目录检查全部通过后，才把任务包移动或复制到 `prompts/codex/task-packs/`。导入后删除临时下载物和解压目录；如无法删除，记录为本机临时状态，不提交。
9. 导入完成后，按普通任务包目录继续执行；执行时仍以当前仓库事实为准，不直接相信任务包里的旧路径、旧结论或外部 AI 结论。
10. 如果分享页无法自动解析下载方式，或下载结果不是 zip，停止执行并请用户提供本机 zip、远程 zip 直链或明确的下载步骤。

## 执行步骤

1. 若输入是外部 AI 纯文本大任务 Markdown，先完成“纯文本任务包落地协议”；若输入是本机 zip、远程 zip 直链或远程分享页 URL，先完成“任务包导入协议”；若输入是已存在目录，确认任务包目录存在，并且包含 `manifest.json` 与 `prompts/00-session-runbook.md`。
2. 读取 `README.md`、`EXECUTE_PROMPT.md`、`PLAN.md`、`manifest.json`、`prompts/00-session-runbook.md` 和 `SESSION_STATE.md`。
3. 运行 `git status --short`，识别用户或其他任务留下的未提交改动；不得回滚无关改动。
4. 根据 `SESSION_STATE.md` 的 `NEXT_TASK` 和 `RESUME_FROM` 继续；如果状态文件尚未创建，从任务 `01` 开始并创建初始状态。
5. 每完成一个子任务，运行相关验证，更新 `SESSION_STATE.md`，记录 `DONE`、`CHANGED_FILES`、`COMMANDS_RUN`、`TESTS_RUN`、`RISKS` 和下一步；如果该子任务产生了实际改动，必须按仓库规则提交、推送当前分支，并在推送后运行仓库级 mirror 计划命令，按有效计划同步镜像。
6. 在 `same_session_auto_run` 模式下，除非阻塞或用户打断，完成子任务级验证、状态更新、提交、推送和必要的镜像同步后，再继续下一任务。
7. 完成全部任务后，确认最后一个任务段也已按仓库规则提交、推送并按开关完成镜像同步，并在最终说明中写清经验命中、模块档案、关键词经验、命中 code 组件和发布状态。

## 验证方式

- `manifest.json` 可被 JSON 解析。
- `manifest.json` 包含 `language`、`documentation_language`、`audience`、`closeout_profile` 和 `delivery_mode`，且默认中文、人类优先收口。
- 任务包 README、runbook、子任务正文和任务执行中新增或改写的项目文档使用中文标题与中文正文；英文仅用于代码标识、路径、命令、协议名、第三方原文、机器 key、品牌/专有名词或用户明确要求的英文内容。
- 任务包包含 `README.md`、`EXECUTE_PROMPT.md`、`PLAN.md`、`prompts/00-session-runbook.md` 和至少一个编号子任务。
- 外部 AI 纯文本大任务 Markdown 必须先落成任务包文件和独占 `SESSION_STATE.md`，再执行。
- 从本机 zip、远程 zip 直链或分享页 URL 导入时，先在临时工作区下载、解压和校验，通过后再落到 `prompts/codex/task-packs/`；`files.example.com/api/maw-file-storage/public` 直链和 `files.example.com/file-storage/extract` 带密码分享页必须被视为受支持的任务包来源。
- `EXECUTE_PROMPT.md` 可直接复制到 Codex 执行，且包含真实任务包路径、状态文件路径、`same_session_auto_run` 或实际执行模式。
- 任务包内出现 `SESSION_STATE`、`NEXT_TASK`、`RESUME_FROM` 和执行模式。
- 任务包 runbook 和子任务包含 `docs/ai-instructions/experience-index.md` 检索规则、`solutions/**` 按命中读取边界和 `experience_lookup` 输出字段。
- 任务包中没有本机项目绝对路径、真实密钥、生产账号、未脱敏日志或大段原始资料。
- 如果任务包影响模块、配置或发布边界，同步更新相关模块档案或说明不更新原因。
- 任务包要求每个产生实际改动且可独立验证的子任务完成后主动提交并推送当前分支、推送后按仓库级 mirror 有效计划同步镜像，且写清无法推送或无法执行 mirror 计划时的阻塞说明。
- 任务包要求推送时先提交并推送本任务实际改动；本任务提交完成后，如果工作区还有 `code/**` 之外且非禁提交范围的无关变动，可补独立中文 commit message 推送；剩余 `code/**` 组件业务代码、组件运行配置或组件内文件变动不得纳入顺手推送。

## 禁区

- 不得引用本机 Codex skill 路径、私有脚本路径或要求后续会话必须安装某个 skill。
- 不得把任务提示词工程写成只有一条长提示词；复杂任务必须有任务拆分、状态文件和恢复协议。
- 不得把外部 AI 纯文本大任务直接当作最终实现指令跳过任务包落地；除非用户明确改口要求按单条提示词执行。
- 不得复用其他任务包的 `SESSION_STATE.md`，避免 `NEXT_TASK` 和 `RESUME_FROM` 串线。
- 不得把真实密钥、token、客户隐私、生产连接串、原始日志或未脱敏资料写进任务包。
- 不得为了补全任务而猜测接口、数据库字段、发布目标或验收结果。
- 不得把远程分享页 URL、提取码、访问密码、一次性下载链接或下载态写入可提交文件。
- 不得直接从下载目录执行任务包；必须先校验并导入到 `prompts/codex/task-packs/`。

## 冲突与覆盖规则

- 用户最新明确要求优先于旧任务包。
- 当前代码、`.maw` 配置、模块档案和 active 文档优先于任务包中的旧基线。
- 任务包与 `docs/ai-coding/`、`.maw/policies.yaml`、镜像仓库或客户仓库同步规则冲突时，以更保守、更高风险控制的规则为准。
- 与 `TINST-003 使用模块档案定位开发边界` 冲突时，本指令负责任务包创建/执行，`TINST-003` 负责模块定位和模块档案维护。

## 更新记录

- 2026-06-14：补充外部 AI 纯文本 Markdown 任务包落地协议；未明确要求 zip 时，大任务先创建任务提示词工程文件再执行。
- 2026-06-15：重点兼容自建可信文件存储服务 `files.example.com` 的直接下载 URL 和带 `pwd` 的分享页 URL，并新增 `ops/scripts/download-task-pack-url.py` 作为下载辅助。
- 2026-06-14：补充本机 zip、远程 zip 直链和分享页 URL 的任务包导入协议，兼容可道云/Kodbox 分享页。
- 2026-06-12：任务包模板新增 `EXECUTE_PROMPT.md`，用于保存可直接复制到 Codex 的执行提示词。
- 2026-06-14：强化任务包 mirror 收口协议，要求推送后先运行仓库级 mirror 计划命令，并按有效计划同步镜像。
- 2026-06-13：强化任务包执行协议，要求子任务完成并验证后主动提交、推送当前分支，并同步仓库级 mirror。
- 2026-06-12：强化任务包执行协议，要求子任务完成并验证后主动提交并推送当前分支。
- 2026-06-12：创建，纳入项目内任务提示词工程协议。
