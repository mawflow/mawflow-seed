# Codex 任务提示词工程

本目录保存可恢复、可分阶段执行的 Codex 任务提示词工程。它不同于单条一次性提示词：任务包必须能让后续 Codex 会话只凭仓库内文件理解目标、继续执行、记录状态并完成验收。

## 触发方式

创建：

```text
创建任务提示词工程：<需求、方案、实施计划或资料路径>
```

执行：

```text
执行任务提示词工程：prompts/codex/task-packs/<slug>-codex-tasks
执行任务提示词工程：<本机任务包 zip 文件>
执行任务提示词工程：<远程任务包 zip 直链或分享页 URL>
执行任务提示词工程：https://files.example.com/api/maw-file-storage/public?file_key=<file_key>&token=<token>
执行任务提示词工程：https://files.example.com/file-storage/extract?file_key=<file_key>&token=<token>&pwd=<pwd>
```

外部 AI 纯文本大任务：

```text
<复制 ChatGPT 生成的 Markdown 中的【Codex 任务提示词】全文>
```

项目指令见 `docs/ai-instructions/instructions/create-task-prompt-project.md`。

## 公开示例

公开 Seed 只把任务包机制和最小示例作为默认入口，不暴露内部模板治理任务路线。需要为自己的项目创建任务包时，先复制 `_template/`，再按实际目标补齐任务说明、执行提示、状态文件和验收命令。

不要只发送一个任务包路径让 AI 自行推测任务；完整入口应写明目标、上下文、任务包目录、恢复状态、验证命令和提交推送要求。Seed 默认组件口径是 `server` / `client`，派生项目已有其它 app_key 时以目标项目事实为准。

| 示例 | 说明 |
| --- | --- |
| `_template/` | 新建任务包时复制的结构模板。 |
| `examples/mawflow-packs/task-pack/` | 最小公开 Task Pack 示例。 |

模板升级、既有项目改造、密钥治理、开源准备和其它维护任务属于具体项目或维护者工作流，不作为公开 Seed 默认任务包入口。公开发布包只应包含通用模板、公开示例和安全边界说明。

## 安全边界

- 任务包正文不得包含真实密钥、token、SSH 私钥、生产连接串、客户资料、未脱敏日志或机器本机路径。
- 任务包可以引用公开仓路径、公开文档和项目根相对路径；不要写需要内部私有仓访问权限才能理解的执行入口。
- 外部分享链接只在当次会话使用，不写入任务包、可提交文档或最终说明。
- 公开示例必须能被独立阅读；内部维护任务、发布准入任务和私有治理任务应留在维护者私有工作流中。

## 外部纯文本任务包落地

根目录 `CHATGPT_TO_CODEX.md` 的默认大任务交付物是可下载、可复制的 Markdown 纯文本，不是 zip。用户把 Markdown 中的【Codex 任务提示词】复制到 Codex 后，Codex 应先创建 `prompts/codex/task-packs/<slug>-codex-tasks/` 下的任务包文件，并创建独占状态文件：

```text
docs/implementation/<topic>/<slug>-codex-tasks/SESSION_STATE.md
```

纯文本大任务必须写明每个文件的内容，至少包括 `README.md`、`EXECUTE_PROMPT.md`、`PLAN.md`、`manifest.json`、`prompts/00-session-runbook.md`、编号子任务和 `SESSION_STATE.md`。写完后如果提示词要求继续执行，不要停在“任务包已创建”，而是读取 `EXECUTE_PROMPT.md`、`PLAN.md`、`manifest.json`、`prompts/00-session-runbook.md` 和 `SESSION_STATE.md` 后继续执行。

如果纯文本缺少关键文件内容，先让用户回到 ChatGPT 补齐可下载/可复制 Markdown，或由当前 Codex 按 TINST-007 的创建步骤补齐任务包；不要把大任务直接当作一条不可恢复的实现提示词执行。

## 外部 zip 任务包导入

`#跑任务包` 可以接收仓库内目录、本机 zip、远程 zip 直链，或包含下载方式的远程分享页 URL。外部 AI 生成的 zip 任务包只在用户明确要求 zip/压缩包/可下载任务包（不含 `.md` 纯文本）时使用，并默认应是按根目录 `CHATGPT_TO_CODEX.md` 生成的大任务 zip 交接物。远程任务包必须先导入再执行：下载物放在临时工作区，解压后按 `CHATGPT_TO_CODEX.md` 和 TINST-007 校验结构与安全边界，通过后才移动到 `prompts/codex/task-packs/<slug>-codex-tasks/`。

分享页不是 zip 直链。可道云/Kodbox 这类带 `/#s/<share-id>` 的分享页应先解析页面中的下载方式；需要提取码、访问密码或登录态时，只在当次会话使用，不写入任务包、可提交文档或最终说明。自建可信文件存储服务 `files.example.com` 有两个受支持入口：`/api/maw-file-storage/public` 直接返回 zip，`/file-storage/extract?...&pwd=...` 返回自动填入密码的分享页，应向表单提交 `extract_password` 后下载 zip；推荐用 `python3 ops/scripts/download-task-pack-url.py "<URL>" --output "<临时目录>/task-pack.zip"` 统一处理。若无法自动解析下载方式，要求用户提供本机 zip、远程 zip 直链或明确下载步骤。

导入校验至少包括：

- zip 内直接包含 `prompts/codex/task-packs/<slug>-codex-tasks/`，或 zip 根目录是单个 `<slug>-codex-tasks/`。
- 任务包包含 `manifest.json`、`README.md`、`EXECUTE_PROMPT.md`、`PLAN.md` 和 `prompts/00-session-runbook.md`。
- 不包含路径穿越、绝对路径、隐藏 `.git` 仓库、`.local` 私有资料、真实密钥、依赖目录、构建产物、仓库源码副本或明显无关大文件。
- 目标目录已存在时不得覆盖或合并，必须先让用户确认改名、覆盖或继续执行已有目录。

## 目录结构

```text
<slug>-codex-tasks/
├── README.md
├── EXECUTE_PROMPT.md
├── PLAN.md
├── manifest.json
└── prompts/
    ├── 00-session-runbook.md
    ├── 01-baseline-audit.md
    ├── 02-implementation.md
    └── NN-final-acceptance.md
```

每个任务包必须有独占状态文件，推荐放在：

```text
docs/implementation/<topic>/<slug>-codex-tasks/SESSION_STATE.md
```

不要多个任务包共用同一个 `SESSION_STATE.md`。

## 必需文件

- `README.md`：面向人阅读，说明复制什么、会做什么、不会做什么、完成后看到什么，以及任务包目标、恢复方式、任务列表和全局原则。
- `EXECUTE_PROMPT.md`：面向人复制给 Codex 的执行本任务提示词，必须短、完整、自包含，并包含真实任务包路径、状态文件路径、执行模式、恢复方式、验证、提交推送和最终说明要求。
- `PLAN.md`：说明核心对象、数据流、任务拆分、非目标和风险边界。
- `manifest.json`：机器可读元信息，至少包含 `schema_version`、`package`、`language`、`documentation_language`、`audience`、`execution_mode`、`closeout_profile`、`delivery_mode`、`module_keys`、`app_keys`、`session_state`、`entry_prompt` 和 `files`；需要中英双受众说明时增加 `i18n.human.zh-CN` 和 `i18n.ai.en-US`；`entry_prompt` 优先指向 `EXECUTE_PROMPT.md`。
- `prompts/00-session-runbook.md`：面向 AI 的执行总纲，包含目标、基线、必读文件、执行规则、状态格式、中断恢复协议和任务列表。
- `prompts/01-*.md` 起的编号任务：每个任务独立可执行、可验证，并要求更新 `SESSION_STATE.md`；只要该子任务产生实际改动，就必须按仓库规则提交并推送当前分支，且在仓库级 mirror 自动同步开关开启时继续同步镜像。

每个任务包都必须继承经验防重踩规则：任务开始前检索 `docs/ai-instructions/experience-index.md`；只有命中索引、候选台账或用户明确路径时，才读取 `docs/ai-instructions/solutions/**` 的具体方案详情。

## 执行模式

- `same_session_auto_run`：默认模式。当前 Codex 会话完成一个任务后更新 `SESSION_STATE.md`；如果产生实际改动，先验证、提交并推送当前分支，再运行 `ops/scripts/sync-repository-mirror.sh plan`，按有效计划同步仓库级镜像，然后继续下一个任务，直到完成、阻塞或用户打断。
- `per_task_handoff`：每次只执行一个任务，结束时先完成验证、提交、推送，并按仓库级 mirror 有效计划同步镜像，再给出下一会话可复制的恢复提示词。
- `hybrid_auto_with_handoff`：同会话自动推进，但每个任务结束都写好恢复提示词；产生实际改动时同样先提交、推送当前分支，并按仓库级 mirror 有效计划同步镜像。

不把本机 Codex skill、私有脚本或绝对路径作为任务包依赖。

## 子任务模板要求

每个编号任务至少包含：

```text
## 目标
## 必读文件
## 实现要求
## 建议命令
## 验收标准
## 最终说明要求
```

任务包 README、runbook、子任务正文和任务执行中新增或改写的项目文档默认使用中文标题与中文正文。英文仅保留在代码标识、文件名/路径、命令、协议名、第三方库原文、机器字段 key、品牌/专有名词或用户明确要求的英文内容中；不要把 `Objective`、`Required Reads`、`Implementation Requirements`、`Acceptance Criteria`、`Final Response Requirements` 作为新任务包标题。

最终说明必须采用中文、人类优先的主展示。主展示先写结论、变更、验证、Git/镜像、模块与记忆、种子仓库升级建议、发布影响和 code 交付影响；机器字段集中放在末尾“技术元数据”中。技术元数据必须继承项目通用收口字段：

```text
module_key:
module_dossier_updated:
module_dossier_reason:
updated_module_docs:
experience_lookup:
hit_code_components:
release_update_status:
release_commands:
release_confirmation_prompt:
code_delivery_status:
memory_update:
local_update:
upgrade_strategy_update:
seed_repository_upgrade_suggestions:
```

如果 `release_update_status` 中存在多个需要发布才会生效且当前未发布或未验证的 app_key，`release_commands` 必须按 app_key 分别列出；用户可以复制其中一条或多条选择部分发布。`release_confirmation_prompt` 必须在收口末尾询问是否“确认发布全部”，用户回复“确认发布全部/确认/是”则发布全部待发布组件。发布指令必须来自聚合后的 `.maw/releases.yaml` 和 `code/<app_key>/.maw.component.yaml`，并写清默认发布环境与可选环境。

## 质量检查

创建或更新任务包后至少检查：

- `manifest.json` 可解析。
- `EXECUTE_PROMPT.md` 存在，且可直接复制到 Codex 执行本任务提示词工程。
- 入口 `prompts/00-session-runbook.md` 存在。
- 包内包含 `SESSION_STATE`、`NEXT_TASK` 和 `RESUME_FROM`。
- 包内要求检索 `experience-index.md`，且不得主动全量读取 `solutions/**`。
- 包内要求每个产生实际改动的子任务完成后主动验证、提交、推送当前分支，并在推送后运行仓库级 mirror 计划命令，按有效计划同步镜像。
- 包内要求推送时先只提交本任务实际改动；本任务推送后，剩余 `code/**` 之外且非禁提交范围的无关变动可作为独立补充提交推送，剩余 `code/**` 组件业务变动不得纳入顺手推送。
- 路径使用项目根相对路径，不写本机项目绝对路径。
- 不写真实密钥、token、客户隐私、生产连接串或未脱敏日志。
- 涉及模块、配置、发布或同步边界时，任务包要求更新对应模块档案或说明不更新原因。
- 升级/改造任务包必须说明默认 `server` / `client` 口径，并防止误删目标项目已有独立 `admin` 或凭空新增后台组件。
- code-only 交付任务必须先运行 `ops/scripts/check-code-deliverable.sh`；需要导出时先运行 `ops/scripts/export-code-only.sh --dry-run`，确认后再导出。

## 模板

复制 `_template/` 后替换占位内容。不要把 `_template/` 本身当成实际任务包执行。
