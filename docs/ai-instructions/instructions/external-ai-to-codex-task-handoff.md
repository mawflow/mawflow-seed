# 指令：外部 AI 方案转 Codex 任务

## 元信息

- ID：TINST-012
- 类型：项目指令
- 状态：启用
- 维护位置：`docs/ai-instructions/instructions/external-ai-to-codex-task-handoff.md`
- 推荐调用：`#交接任务`
- 精确调用：`#T012`
- 触发词：#交接任务、ChatGPT 生成 Codex 任务、外部 AI 任务交接、把方案生成 Codex 任务、生成 Codex 任务纯文本、生成 Codex 任务 Markdown、生成 Codex 任务 zip、ChatGPT 到 Codex、方案转任务包、任务交接协议
- 适用范围：维护或使用 `CHATGPT_TO_CODEX.md`；把 ChatGPT、网页端 AI、Claude、Gemini 或其它外部分析工具讨论确定的方案，整理成 Codex 可执行的单条任务提示词或任务提示词工程。
- 相关执行入口：默认交接物是可下载、可复制的 Markdown 纯文本；大任务 Markdown 先让 Codex 创建任务提示词工程文件，再执行。只有用户明确要求 zip/压缩包/可下载任务包（不含 `.md` 纯文本）时，大任务才通过本机 zip、远程 zip 直链或包含下载方式的分享页交给 Codex；zip 导入和执行由 `TINST-007` 负责。

## 目标

当用户希望先在 ChatGPT 等外部 AI 中讨论方案，再把已确定方案交给 Codex 执行时，AI 应按 `CHATGPT_TO_CODEX.md` 约束生成交接物：默认输出可下载、可复制的 Markdown 纯文本。小任务 Markdown 内是一段可直接复制的 Codex 任务提示词；大任务 Markdown 内是“任务提示词工程落地 + 执行”的 Codex 任务提示词，要求 Codex 先创建任务包文件，再执行该任务提示词工程。只有用户明确要求 zip/压缩包/可下载任务包（不含 `.md` 纯文本）时，才输出可下载 zip 任务提示词工程。

## 输入要求

- 必需输入：已确定的方案、建议、审计结论、修改任务列表，或用户明确要求“按 `CHATGPT_TO_CODEX.md` 生成 Codex 任务”。
- 推荐输入：目标仓库范围、相关文件路径、风险边界、验收标准、是否明确要求 zip。
- 可选输入：模块、app_key、用户不希望改动的文件、目标项目是否已接入本模板。
- 缺失时处理：
  - 如果方案还没有关键决策、路径或验收标准，先列待确认问题，不生成任务。
  - 如果任务大小不确定，优先按大任务生成任务提示词工程。
  - 如果用户没有明确要求 zip，默认生成可下载、可复制的 Markdown；无法提供 `.md` 下载文件时，在回答正文完整输出 Markdown。
  - 如果用户明确要求 zip 但外部 AI 无法实际生成 zip，必须输出任务包目录结构和每个文件内容，并说明需要人工或工具打包。

## 执行步骤

1. 先读取 `CHATGPT_TO_CODEX.md`，再按需读取 `PROJECT_COMMANDS.md`、`docs/ai-instructions/README.md` 和任务相关的最小仓库文件。
2. 判断任务大小：
   - 小任务：预计 1 到 3 个文件、低风险、单会话可完成，输出可下载、可复制的 Markdown；Markdown 内包含单条 Codex 任务提示词。
   - 大任务：跨模块、跨 app_key、多阶段、高风险、需要取舍矩阵或恢复协议，默认输出可下载、可复制的 Markdown；Markdown 内包含“任务提示词工程落地 + 执行”提示词，写明任务包目录和每个文件内容。只有用户明确要求 zip 时，才生成任务提示词工程 zip。
3. 生成小任务提示词时，默认中文输出，必须包含目标、已确定方案、涉及范围、执行要求、验收标准和最终说明字段；最终说明要求采用中文、人类优先主展示，技术元数据附后；若可能命中多个 app_key 发布，提示词必须要求 Codex 读取 `.maw/releases.yaml` 与 `code/<app_key>/.maw.component.yaml`，按 app_key 分别给出 `#发布` 指令，在收口末尾询问是否“确认发布全部”，并支持用户复制指令选择部分发布。
4. 生成大任务纯文本 Markdown 时，必须按 `CHATGPT_TO_CODEX.md` 的“大任务纯文本 Markdown 输出格式（默认）”写成可复制给 Codex 的落地提示词：包含任务包目录、状态文件路径、`README.md`、`EXECUTE_PROMPT.md`、`PLAN.md`、`manifest.json`、`prompts/00-session-runbook.md`、编号子任务和 `SESSION_STATE.md` 的完整内容，并要求 Codex 写完任务包后继续执行；最终输出不得保留 `<slug>`、`<写出完整内容>`、省略号、“同理”或“按模板生成”，内容太长时分多条消息连续输出，不能删减任务包文件。
5. 生成大任务 zip 时，必须包含面向人的 `README.md`、可复制给 Codex 的 `EXECUTE_PROMPT.md`、`PLAN.md`、`manifest.json` 和 `prompts/00-session-runbook.md`；`manifest.json` 默认包含 `language: zh-CN`、`documentation_language: zh-CN`、`audience: human_and_codex`、`closeout_profile: zh_cn_human_first` 和 `delivery_mode: code_only`；任务包正文和任务执行中新增或改写的项目文档默认中文；复杂任务继续拆出编号子任务。
6. 如任务包 manifest、升级资产或配置样例需要同时保存中英文说明，默认展示字段写中文给人读；英文说明放入 `i18n.ai.en-US` 给 AI/机器读，中文说明可放入 `i18n.human.zh-CN`。
7. 输出中涉及目标项目目录或文件路径时，统一使用项目根相对路径。
8. 明确要求 Codex 执行时重新读取目标项目当前仓库事实，不直接相信外部 AI 的路径、代码或结论。
9. 明确禁止复制 `.git`、`.local` 私有资料、真实密钥、token、客户隐私、生产连接串、依赖目录、构建产物和仓库源码副本。
10. 如果交接任务涉及对外交付 `code/`，提示 Codex 先运行 `ops/scripts/check-code-deliverable.sh`；需要导出时先运行 `ops/scripts/export-code-only.sh --dry-run`。
11. 最终必须输出 Codex 使用方式：
   - 纯文本 Markdown：下载或复制 `.md`，打开后复制其中【Codex 任务提示词】到目标项目 Codex 会话执行；如果大任务 Markdown 已要求 Codex 创建任务提示词工程，Codex 创建后继续执行。
   - zip 任务包：下载、解压或复制到 `prompts/codex/task-packs/<slug>-codex-tasks/`，再在 Codex 输入 `#跑任务包：prompts/codex/task-packs/<slug>-codex-tasks`；如果目标项目已支持新版 `#跑任务包`，也可以直接输入本机 zip、远程 zip 直链或分享页 URL，由 Codex 按 TINST-007 先临时下载、解压校验并导入后执行；如果目标项目不支持 `#跑任务包`，复制 `EXECUTE_PROMPT.md` 全文执行。
   - 分享页任务包：必须写清页面中包含下载方式；可道云/Kodbox 等分享页需要提取码、访问密码或登录态时，凭证只由用户当次提供，不写入任务包、提示词或可提交文档。
   - 自建可信文件存储服务任务包：`https://files.example.com/api/maw-file-storage/public?file_key=<file_key>&token=<token>` 作为远程 zip 直链；`https://files.example.com/file-storage/extract?file_key=<file_key>&token=<token>&pwd=<pwd>` 作为带密码分享页。目标项目 Codex 应按 TINST-007 使用 `ops/scripts/download-task-pack-url.py` 或等价方式下载到临时 zip，再做解压和结构校验；`token`、`pwd` 只作为当次输入，不写入任务包或可提交文档。
12. 如果本指令或 `CHATGPT_TO_CODEX.md` 发生变化，必须同步维护 `PROJECT_COMMANDS.md`、`docs/ai-instructions/README.md`、`docs/ai-instructions/experience-index.md` 和模板自检脚本。

## 验证方式

- `CHATGPT_TO_CODEX.md` 存在，并写清小任务、大任务、纯文本 Markdown、zip、`EXECUTE_PROMPT.md` 和 Codex 使用方式。
- `PROJECT_COMMANDS.md` 存在 `#交接任务` 和 `#T012`。
- `docs/ai-instructions/README.md` 登记 `TINST-012`。
- `docs/ai-instructions/experience-index.md` 登记外部 AI 到 Codex 任务交接经验入口。
- 生成的交接内容不包含真实密钥、绝对项目路径、仓库源码副本或 `.local` 私有资料。
- 生成的交接内容不包含远程分享页提取码、访问密码、登录态或一次性下载链接；远程 zip 或分享页只作为当次输入交给 Codex。
- 如果使用自建可信文件存储服务，只写占位 URL 或用户当次输入；不要把真实 `file_key`、`token`、`pwd` 固化到可提交文件。
- 大任务纯文本 Markdown 已写明任务包每个文件内容，并要求 Codex 创建后继续执行。
- 大任务纯文本 Markdown 没有保留尖括号占位符、省略号、“同理”、“略”、“自行补齐”或“按模板生成”等未完成内容。
- 大任务 manifest 包含 `language`、`audience`、`closeout_profile` 和 `delivery_mode`，并默认中文、人类优先收口。

## 禁区

- 不让 Codex 直接执行未经目标仓库事实校验的外部 AI 方案。
- 不把大型任务压缩成一条不可恢复的实现提示词；纯文本大任务也必须先落任务提示词工程和 `SESSION_STATE.md`。
- 不把一次性 ChatGPT 讨论全文写入项目指令库。
- 不把任务包 zip 做成源码交付包。
- 不把远程分享页凭证或私有云盘会话信息写进可提交文件。
- 不在可提交文档中写入本机项目绝对路径。

## 冲突与覆盖规则

- 用户最新明确要求优先。
- `CHATGPT_TO_CODEX.md` 是外部 AI 交接物格式的权威说明；本指令负责让项目指令系统能命中和维护该说明。
- 与 `TINST-007 创建和执行任务提示词工程` 冲突时：本指令负责外部 AI 到 Codex 的交接判断和输出要求，`TINST-007` 负责本仓库内任务提示词工程的通用结构与执行协议。
- 与 `TINST-001 查找并执行项目指令` 冲突时，以 `TINST-001` 的指令命中和歧义确认规则为准。

## 更新记录

- 2026-06-18：强化 ChatGPT Web 输出约束，大任务纯文本必须写出任务包每个文件完整正文、禁止占位符和省略内容，并明确 Codex 用法。
- 2026-06-14：默认大任务交接改为可下载、可复制 Markdown 纯文本；未明确要求 zip 时，不生成 zip，而是让 Codex 先落任务提示词工程文件再执行。
- 2026-06-15：补充自建可信文件存储服务 `files.example.com` 的直链和带密码分享页任务包使用方式。
- 2026-06-14：补充远程 zip 直链和分享页 URL 的 Codex 使用方式，交由 TINST-007 导入校验。
- 2026-06-12：创建，纳入 ChatGPT/外部 AI 方案转 Codex 任务的交接协议。
