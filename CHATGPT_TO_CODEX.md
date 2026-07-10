# ChatGPT 到 Codex 任务交接协议

本文件给 ChatGPT、网页端 AI、其它外部分析工具和人类阅读，用来把已经讨论清楚的方案整理成 Codex 可以执行的任务输入。

目标不是让外部 AI 直接替 Codex 修改仓库，而是让外部 AI 把方案、取舍、风险和验收标准交接给 Codex。Codex 执行时仍必须重新读取目标仓库事实，并按目标项目自己的规则实现、验证、提交和推送。

## 给 ChatGPT Web 的硬性输出协议

ChatGPT Web 读取本文后，必须把本文当作“输出契约”，而不是背景资料。最终回复必须产出交接物本身，不能只解释规则、总结方案或建议用户自行整理。

默认交付物是 Markdown 纯文本：

- 如果用户没有明确说“zip / 压缩包 / 可下载任务包”，最终回复必须给出一份可下载、可复制的 `.md` Markdown。
- 如果当前 ChatGPT Web 不能创建下载文件，必须在回答正文中完整输出 Markdown 正文，方便用户复制或另存为 `.md`。
- “可下载 `.md` 文件”不等于“可下载任务包”；不要因为用户说“可下载”就改成 zip。
- 最终回复必须包含“如何在 Codex 里使用”，并明确告诉用户复制 Markdown 中的【Codex 任务提示词】到目标项目 Codex 会话。

大任务默认仍是 Markdown 纯文本，但 Markdown 里的【Codex 任务提示词】必须让 Codex 先落地任务提示词工程，再执行：

- 必须写清任务包目录：`prompts/codex/task-packs/<slug>-codex-tasks/`。
- 必须写清独占状态文件：`docs/implementation/<topic>/<slug>-codex-tasks/SESSION_STATE.md`。
- 必须列出每个要创建的文件路径，并给出每个文件的完整正文。
- 至少包含 `README.md`、`EXECUTE_PROMPT.md`、`PLAN.md`、`manifest.json`、`prompts/00-session-runbook.md`、一个或多个编号子任务、最终验收子任务和 `SESSION_STATE.md`。
- `manifest.json` 必须是可解析 JSON，不能带注释，不能保留 `<占位符>`。
- 写完任务包后必须要求 Codex 继续读取并执行 `EXECUTE_PROMPT.md`，不能停在“任务包已创建”。

占位符处理规则：

- 本文示例里的 `<slug>`、`<topic>`、`<方案要点>`、`<写出完整内容>` 只用于说明结构；ChatGPT 最终交付给用户时必须替换成具体内容。
- 如果某个路径、模块、app_key 或验收方式无法从当前方案确定，不要留空或保留占位符；应写成“待 Codex 根据目标仓库事实确认”，并同时给出 Codex 要读取的线索。
- 如果输出太长，必须分多条连续消息输出，并标明“第 1/N 部分、第 2/N 部分”；不得省略任务包文件内容，也不得用“其余文件同理”代替。

## 给人看的速记入口

本节只给人类快速复制调用，不是给 Codex 单独看的技能说明，也不是给外部 AI 执行的任务生成规则。外部 AI 读取本文时，只需把本节理解为用户如何发起请求的示例；真正的生成约束从后面的“总体流程”开始。

它是“外部 AI 生成 Codex 任务”的格式契约。用户在 ChatGPT 里讨论完方案后，可以把下面任一示例复制到 ChatGPT Web。

默认只生成纯文本 Markdown。只要用户没有明确说“生成 zip / 压缩包 / 可下载任务包”，ChatGPT 都必须输出可直接复制到 Codex 的 Markdown，并尽量同时提供可下载 `.md` 文件；如果当前 ChatGPT Web 不支持生成下载文件，也必须在回答正文中输出完整 Markdown。

```text
请把当前确定的方案，按照仓库 CHATGPT_TO_CODEX.md 的要求，生成可交给 Codex 执行的任务。
要求生成可下载、可复制的 Markdown（.md）纯文本，不要生成 zip 或压缩包。
如果你不能提供 .md 下载文件，就在回答正文中完整输出这份 Markdown。
小任务输出一段【Codex 任务提示词】。
大任务输出“任务提示词工程落地 + 执行”的【Codex 任务提示词】：让 Codex 先在 prompts/codex/task-packs/<slug>-codex-tasks/ 创建任务提示词工程，写明每个文件路径和每个文件的完整内容，再继续执行这个任务提示词工程。
最终输出不得保留 <占位符>、不得只给目录结构、不得只说“按模板创建文件”。如果内容太长，请分多条消息连续输出完整 Markdown。
最后必须写清“如何在 Codex 里使用”。
```

只有明确需要 zip 时，才使用下面的说法：

```text
请把当前确定的方案，按照仓库 CHATGPT_TO_CODEX.md 的要求，生成可交给 Codex 执行的任务。
这次我明确要求生成可下载 zip 任务包。请按大任务 zip 契约生成 prompts/codex/task-packs/<slug>-codex-tasks/ 目录结构，并在回答最后写清下载、解压、#跑任务包 的使用方式。
```

如果 ChatGPT 可以读取仓库文件，应先读取本文件，再读取与方案相关的最小必要文件。不要为了了解项目而全量读取仓库。

## 总体流程

1. 先确认当前方案已经足够明确，可以交给 Codex 执行。
2. 判断任务大小：小任务输出一份可下载、可复制的 Markdown 任务提示词；大任务默认输出一份可下载、可复制的 Markdown“任务提示词工程落地 + 执行”提示词，让 Codex 先创建任务包文件，再执行任务包。
3. 默认输出中文；交给 Codex 的最终说明要求采用中文、人类优先主展示，技术元数据附后。
4. 生成内容时只引用项目根相对路径，不写本机项目绝对路径。
5. 不把仓库源码、`.git`、`.local` 私有资料、真实密钥、token、客户隐私、生产连接串、依赖目录或构建产物放入输出。
6. 需要交付 `code/` 时，要求 Codex 先运行 `ops/scripts/check-code-deliverable.sh`；需要导出时先运行 `ops/scripts/export-code-only.sh --dry-run`。
7. 只有用户明确要求生成 zip、压缩包或可下载任务包时，才生成大任务 zip；“可下载 .md”仍属于纯文本交付，不属于 zip 交付。
8. 生成大任务纯文本 Markdown 时，必须在【Codex 任务提示词】内写出每个任务包文件的完整正文，不得只写目录结构或说明“文件内容略”。
9. 最后必须输出“如何在 Codex 里使用”。

如果用户明确要求大任务通过远程下载地址交付，可以给出远程 zip 直链；也可以给出包含下载方式的分享页 URL，但必须写清这是分享页，不是 zip 直链。远程交付只使用团队确认的可信文件存储。可下载 `.md` 纯文本不需要按 zip 导入，用户只需打开 Markdown 并复制其中【Codex 任务提示词】到 Codex。可道云/Kodbox 等私有云盘分享页需要提取码、访问密码或登录态时，凭证只应由用户在 Codex 当次会话中提供，不写入任务包、可提交文档或长期说明。Codex 导入远程 zip 或分享页任务包时，会按本文的大任务 zip 契约反向校验结构；因此 zip 内容必须符合本文要求。

如果仍有关键业务决策、路径、验收标准或高风险边界没有确认，不要生成任务；先列出待确认问题。

## 任务大小判断

优先按风险和执行复杂度判断，而不是只按字数判断。

小任务适合直接输出单条 Codex 任务提示词：

- 预计改动 1 到 3 个文件。
- 不涉及数据库、权限、安全、发布、镜像仓库、客户仓库同步或架构迁移。
- 不跨多个业务模块或多个 app_key。
- 验收标准明确，一次 Codex 会话大概率可以完成。
- 不需要分阶段执行或中断恢复。

大任务应生成任务提示词工程；默认交付可下载、可复制的 Markdown 纯文本，明确要求 zip 时才生成 zip：

- 预计改动多个模块、多个 app_key 或多个阶段。
- 涉及数据库、权限、安全、发布、镜像仓库、客户仓库同步、架构调整或模板升级。
- 有多个方案取舍点，需要 Codex 先审计再执行。
- ChatGPT 审计产生了较多修改项，不适合塞进单条实现提示词。
- 需要 `SESSION_STATE.md` 支持中断恢复和续跑。

如果介于两者之间，优先生成任务提示词工程；未明确要求 zip 时，按“大任务纯文本 Markdown 输出格式（默认）”交付。

## 小任务输出格式

小任务必须输出一份可下载、可复制的 Markdown；Markdown 内包含一个可直接复制到 Codex 的完整提示词，并在提示词后给出使用说明。如果 ChatGPT Web 不能提供 `.md` 下载文件，就在回答正文中完整输出这份 Markdown。

```text
下面是一段可直接复制到 Codex 的任务提示词：

【Codex 任务提示词】
#项目指令
任务来源：ChatGPT 方案交接

目标：
<用 1 到 3 句写清本次要完成什么。>

已确定方案：
- <方案要点 1>
- <方案要点 2>

涉及范围：
- 参考路径：<项目根相对路径>
- 可能影响的模块或 app_key：<如无法判断写待 Codex 根据仓库事实确认>

执行要求：
1. 先读取当前仓库相关文件，以仓库事实为准；不要直接相信本提示词里的路径和结论。
2. 所有写入仓库的项目路径使用项目根相对路径。
3. 保留目标项目已有业务规则、模块档案、app_key、发布流程、README 和私有配置。
4. 修改后运行目标项目可用的最小验证。
5. 如果影响模块档案、项目指令、任务提示词工程、运行配置、发布规则或 code 组件，按仓库规则同步更新。
6. 本次产生实际改动后，按目标项目规则提交并推送当前分支，并按仓库级 mirror 开关同步镜像；无法 push 时写清原因。
7. 如果命中多个 app_key 且需要发布才会生效，最终说明必须按 app_key 分别给出 `#发布` 指令，用户可复制其中一条或多条选择部分发布；发布指令和默认环境必须来自目标项目 `.maw/releases.yaml` 与 `code/<app_key>/.maw.component.yaml`。收口末尾必须询问是否“确认发布全部”，用户回复“确认发布全部/确认/是”表示发布全部待发布组件。

验收标准：
- <可检查的验收项 1>
- <可检查的验收项 2>

最终说明必须包含：
- 变更了哪些文件
- 运行了哪些验证
- 是否已提交、推送并按开关同步镜像
- experience_lookup
- module_key
- module_dossier_updated
- module_dossier_reason
- updated_module_docs
- hit_code_components
- release_update_status
- release_commands
- release_confirmation_prompt
【结束】
```

使用说明必须放在提示词后：

```text
使用方式：下载或复制这份 Markdown，打开后复制上面的【Codex 任务提示词】整段内容，到目标项目 Codex 会话中执行。
```

## 大任务纯文本 Markdown 输出格式（默认）

大任务默认不生成 zip，而是输出一份可下载、可复制的 Markdown。该 Markdown 内必须包含一段可直接复制到 Codex 的完整提示词。该提示词不是让 Codex 用一条长提示词直接实现全部需求，而是让 Codex 先按 ChatGPT 给定的文件内容创建任务提示词工程，再继续执行这个任务提示词工程。

如果 ChatGPT Web 能创建文件，应提供 `.md` 下载文件，并在回复中说明文件名；如果不能创建文件，应在回复正文中完整输出 Markdown，方便用户复制或另存为 `.md`。不要为了“可下载”改成 zip，除非用户明确要求 zip。

ChatGPT 最终回复必须采用以下交付外壳：

````text
已按 CHATGPT_TO_CODEX.md 生成 Codex 交接 Markdown。

文件名建议：<slug>-codex-handoff.md

<如果支持下载文件，在这里提供 .md 下载入口；如果不支持下载文件，在下面完整输出 Markdown 正文。>

```markdown
# <任务标题> - Codex 任务交接

下面是一段可直接复制到 Codex 的大任务提示词：

【Codex 任务提示词】
...
【结束】

## 如何在 Codex 里使用

1. 下载或复制本 Markdown。
2. 复制【Codex 任务提示词】整段内容。
3. 粘贴到目标项目 Codex 会话执行。
4. Codex 会先创建任务提示词工程，再继续执行该工程。
```
````

最终交付时，上面 `...` 必须替换为完整【Codex 任务提示词】正文；不得输出省略号、不得保留 `<slug>` 这类尖括号占位符。

纯文本大任务提示词必须包含：

- 任务目标、已确定方案、涉及范围、风险边界和验收标准。
- 任务包目录，例如 `prompts/codex/task-packs/<slug>-codex-tasks/`。
- 独占状态文件路径，例如 `docs/implementation/<topic>/<slug>-codex-tasks/SESSION_STATE.md`。
- 需要创建的每个文件名和每个文件的完整内容。
- 写完任务包后继续执行 `EXECUTE_PROMPT.md` 或 `prompts/00-session-runbook.md` 的要求。
- Codex 必须重新读取目标仓库事实、保护已有业务规则、验证、提交、推送和按开关同步镜像的要求。

文件内容完整性要求：

- `README.md` 必须面向人说明任务来源、使用方式、任务列表、恢复方式和安全边界。
- `EXECUTE_PROMPT.md` 必须是短而完整的入口提示词，包含任务包目录、状态文件路径、执行模式、恢复协议、验证、提交、推送、mirror 和最终说明要求。
- `PLAN.md` 必须包含阶段表，写清每阶段目标、涉及范围、产出、验证方式和是否需要用户确认。
- `manifest.json` 必须是具体、可解析 JSON，包含 `schema_version`、`package`、`title`、`status`、`language`、`documentation_language`、`audience`、`created_from`、`execution_mode`、`closeout_profile`、`delivery_mode`、`module_keys`、`app_keys`、`risk_level`、`session_state`、`entry_prompt` 和 `files`。
- `prompts/00-session-runbook.md` 必须写清启动顺序、必读文件、执行规则、`SESSION_STATE.md` 格式、中断恢复协议和任务列表。
- 每个编号子任务必须包含目标、必读文件、执行要求、建议命令、验收标准和最终说明要求。
- 任务包正文和任务执行中新增或改写的项目文档默认使用中文标题和中文正文；英文仅保留在代码标识、路径、命令、协议名、第三方原文、机器字段 key、品牌/专有名词或用户明确要求的英文内容中。
- `SESSION_STATE.md` 初始内容必须至少包含 `NEXT_TASK`、`RESUME_FROM`、`BLOCKED_REASON`、`DONE`、`CHANGED_FILES`、`COMMANDS_RUN`、`TESTS_RUN`、`RISKS`。
- 如果方案需要 3 个以上阶段，继续增加 `prompts/03-*.md`、`prompts/04-*.md` 等；不要把多个阶段硬塞进一个含糊任务。

推荐格式：

```text
下面是一段可直接复制到 Codex 的大任务提示词：

【Codex 任务提示词】
# 项目指令

任务来源：ChatGPT 方案交接
任务类型：大任务提示词工程落地 + 执行
目标仓库：当前 Codex 会话所在仓库
任务包目录：prompts/codex/task-packs/<slug>-codex-tasks/
状态文件：docs/implementation/<topic>/<slug>-codex-tasks/SESSION_STATE.md

## 目标

<用 2 到 5 句写清本次最终要完成什么。>

## 已确定方案

1. <方案要点 1>
2. <方案要点 2>
3. <方案要点 3>

## 涉及范围

- 参考路径：<项目根相对路径>
- 可能影响的模块或 app_key：<如无法判断写待 Codex 根据仓库事实确认>
- 高风险边界：<数据库、权限、发布、客户仓库、镜像仓库、安全等>

## 执行要求

1. 先读取当前仓库相关文件，以仓库事实为准；不要直接相信本提示词里的路径、接口名或结论。
2. 创建任务包目录：prompts/codex/task-packs/<slug>-codex-tasks/。
3. 创建状态文件：docs/implementation/<topic>/<slug>-codex-tasks/SESSION_STATE.md。
4. 按下面“任务包文件内容”写入每个文件；如仓库已有更严格任务包模板，保持本文目标不变并按仓库模板补齐字段。
5. 写完任务包后，不要停在“任务包已创建”。继续读取并执行：prompts/codex/task-packs/<slug>-codex-tasks/EXECUTE_PROMPT.md。
6. 执行任务包时每阶段都更新 SESSION_STATE.md；遇到阻塞写清 BLOCKED_REASON。
7. 修改后运行目标项目可用的最小验证。
8. 本次产生实际改动后，按目标项目规则提交并推送当前分支，并按仓库级 mirror 开关同步镜像；无法 push 时写清原因。

## 任务包文件内容

注意：ChatGPT 最终交付时，本节下面每个文件都必须写出完整正文。不能保留“<写出完整内容>”，不能写“同上”，不能写“按模板生成”，不能只列目录。

### prompts/codex/task-packs/<slug>-codex-tasks/README.md

<写出 README.md 的完整内容。>

### prompts/codex/task-packs/<slug>-codex-tasks/EXECUTE_PROMPT.md

<写出 EXECUTE_PROMPT.md 的完整内容。>

### prompts/codex/task-packs/<slug>-codex-tasks/PLAN.md

<写出 PLAN.md 的完整内容。>

### prompts/codex/task-packs/<slug>-codex-tasks/manifest.json

<写出可解析 JSON。>

### prompts/codex/task-packs/<slug>-codex-tasks/prompts/00-session-runbook.md

<写出 00-session-runbook.md 的完整内容。>

### prompts/codex/task-packs/<slug>-codex-tasks/prompts/01-<task>.md

<写出第一个子任务提示词的完整内容。>

### prompts/codex/task-packs/<slug>-codex-tasks/prompts/NN-final-acceptance.md

<写出最终验收子任务提示词的完整内容。>

### docs/implementation/<topic>/<slug>-codex-tasks/SESSION_STATE.md

<写出初始 SESSION_STATE.md 内容，至少包含 NEXT_TASK、RESUME_FROM、BLOCKED_REASON。>

## 验收标准

- <可检查的验收项 1>
- <可检查的验收项 2>

## 最终说明必须包含

- 创建并执行了哪个任务提示词工程
- 变更了哪些文件
- 运行了哪些验证
- 是否已提交、推送并按开关同步镜像
- experience_lookup
- module_key
- module_dossier_updated
- module_dossier_reason
- updated_module_docs
- hit_code_components
- release_update_status
- release_commands
- release_confirmation_prompt
【结束】
```

使用说明必须放在提示词后：

```text
使用方式：下载或复制这份 Markdown，打开后复制其中【Codex 任务提示词】整段内容，到目标项目 Codex 会话中执行。Codex 会先创建任务提示词工程，再继续执行该工程。
```

生成前自检：如果【Codex 任务提示词】里仍出现 `<写出`、`<slug>`、`<topic>`、`<方案要点>`、`...`、`同理`、`略`、`自行补齐`、`按模板生成`，说明输出不合格，必须继续补全后再交付。

## 大任务 zip 输出格式（仅在明确要求时）

只有用户明确要求生成 zip、压缩包或可下载任务包（不含 `.md` 纯文本）时，大任务才生成可下载 zip。zip 内建议保留完整项目根相对路径，解压到目标项目根目录后直接出现任务包目录和状态文件：

```text
prompts/codex/task-packs/<slug>-codex-tasks/
  README.md
  EXECUTE_PROMPT.md
  PLAN.md
  manifest.json
  prompts/
    00-session-runbook.md
    01-context-review.md
    02-implementation.md
    03-verification-and-closeout.md
docs/implementation/<topic>/<slug>-codex-tasks/
  SESSION_STATE.md
```

如果外部 AI 无法控制 zip 内路径，也可以只打包 `<slug>-codex-tasks/` 目录，但最终说明必须要求用户把该目录复制到 `prompts/codex/task-packs/` 下。

### `manifest.json` 最小字段

```json
{
  "schema_version": 1,
  "package": "<slug>-codex-tasks",
  "title": "<任务标题>",
  "status": "draft",
  "language": "zh-CN",
  "audience": "human_and_codex",
  "created_from": "ChatGPT 方案交接",
  "execution_mode": "same_session_auto_run",
  "closeout_profile": "zh_cn_human_first",
  "delivery_mode": "code_only",
  "module_keys": [],
  "app_keys": [],
  "risk_level": "medium",
  "session_state": "docs/implementation/<topic>/<slug>-codex-tasks/SESSION_STATE.md",
  "entry_prompt": "EXECUTE_PROMPT.md",
  "files": [
    "README.md",
    "EXECUTE_PROMPT.md",
    "PLAN.md",
    "manifest.json",
    "prompts/00-session-runbook.md",
    "prompts/01-context-review.md",
    "prompts/02-implementation.md",
    "prompts/03-verification-and-closeout.md",
    "docs/implementation/<topic>/<slug>-codex-tasks/SESSION_STATE.md"
  ]
}
```

### `EXECUTE_PROMPT.md` 必须自包含

`EXECUTE_PROMPT.md` 是用户复制给 Codex 的入口，必须包含：

- 任务目标。
- 任务包目录。
- ChatGPT 已确认的方案摘要。
- Codex 必须重新读取仓库事实的要求。
- 分阶段执行顺序。
- `SESSION_STATE.md` 恢复要求。
- 验证要求。
- 提交、推送和仓库级 mirror 同步要求。
- 中文、人类优先最终说明要求；`snake_case` 字段只放末尾技术元数据。
- code-only 交付影响；需要交付时先检查 `code/`，需要导出时先 dry-run。

示例入口：

```text
#跑任务包：prompts/codex/task-packs/<slug>-codex-tasks

请执行该任务提示词工程。先读取 EXECUTE_PROMPT.md、PLAN.md、manifest.json 和 prompts/00-session-runbook.md，再按任务包步骤执行。

如果当前项目不支持 #跑任务包，请直接按本 EXECUTE_PROMPT.md 的全部内容执行。
```

## 大任务 zip 的使用说明（仅在明确要求时）

ChatGPT 返回 zip 时，最后必须输出：

```text
使用方式：

1. 下载 zip。
2. 在目标项目根目录解压，确保生成目录：
   prompts/codex/task-packs/<slug>-codex-tasks/
3. 打开目标项目 Codex 会话。
4. 对 Codex 输入：

#跑任务包：prompts/codex/task-packs/<slug>-codex-tasks

如果目标项目尚未支持 #跑任务包，则打开：
prompts/codex/task-packs/<slug>-codex-tasks/EXECUTE_PROMPT.md
复制其中全部内容到 Codex 执行。
```

如果返回的是远程 zip 直链或分享页 URL，而目标项目已支持新版 `#跑任务包`，也可以让用户直接在目标项目 Codex 会话输入：

```text
#跑任务包：<远程任务包 zip 直链或分享页 URL>
```

Codex 会先把任务包下载到临时工作区，解压并检查结构，通过后再导入 `prompts/codex/task-packs/<slug>-codex-tasks/` 执行。分享页交付必须确保页面中能找到下载方式；可道云/Kodbox 等分享页按分享页处理，提取码或访问密码不写入可提交文件。若目标项目没有自动下载能力，则按上面的手动下载、解压、复制目录方式处理。

## 大任务任务包内容要求

`README.md` 应说明：

- 任务来源是 ChatGPT 方案交接。
- 本任务包只保存执行计划和上下文摘要，不保存仓库源码副本。
- Codex 执行时以目标项目当前仓库事实为准。
- 风险边界和禁止事项。

`PLAN.md` 应包含阶段表：

- 阶段目标。
- 涉及文件或模块。
- 预期产出。
- 验证方式。
- 是否需要用户确认。

`prompts/00-session-runbook.md` 应包含：

- 启动顺序。
- 每阶段完成后更新 `SESSION_STATE.md`。
- `NEXT_TASK`、`RESUME_FROM`、`BLOCKED_REASON` 的记录规则。
- 中断恢复时先读状态文件，不从头猜测。

`SESSION_STATE.md` 应初始化：

- `NEXT_TASK` 指向第一个编号子任务。
- `RESUME_FROM` 写 `start` 或更精确的恢复点。
- `BLOCKED_REASON` 初始写 `none`。
- 后续每阶段完成后记录已完成步骤、改动文件、验证和下一步。

子任务提示词应避免把 ChatGPT 讨论内容原样塞进来，应提炼为可执行目标、约束和验收标准。

## 禁区

- 不生成需要 Codex 直接信任 ChatGPT 结论的任务；必须要求 Codex 重新读取仓库事实。
- 不把真实密钥、token、cookie、客户隐私、生产连接串或未脱敏日志写入提示词或 zip。
- 不把仓库源码、依赖目录、构建产物、`.git`、`.local` 私有资料打包进 zip。
- 不把远程分享页的提取码、访问密码、登录态、一次性下载链接或私有云盘会话信息写入 zip、提示词或可提交文档。
- 不要求 Codex 整文件覆盖目标项目 README、模块档案、运行配置、发布配置或项目私有规则。
- 不使用本机项目绝对路径作为可提交文档内容；ChatGPT 如看到绝对路径，应转换为项目根相对路径。
- 不把任务包当成长期项目指令；长期可复用规则应建议沉淀到 `docs/ai-instructions/`。

## 质量检查清单

交付给用户前，ChatGPT 应自检：

- 已判断小任务或大任务。
- 小任务输出了完整可复制提示词。
- 大任务在未明确要求 zip 时，输出了可下载、可复制的 Markdown 纯文本“任务提示词工程落地 + 执行”提示词，并写明每个任务包文件的内容。
- 只有用户明确要求 zip 时，才输出可下载 zip，且 zip 内不包含禁止内容。
- 如果大任务使用远程 zip 直链或分享页 URL，已写明下载方式、Codex 导入路径和凭证不落库边界。
- 所有项目路径都是项目根相对路径。
- 已写明 Codex 必须重新读取仓库事实。
- 已写明验证、提交、推送和最终说明字段。
- 已输出清晰的 Codex 使用方式。
