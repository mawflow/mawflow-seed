# 指令：使用内置模板任务提示词工程

## 元信息

- ID：TINST-009
- 类型：项目指令
- 状态：启用
- 维护位置：`docs/ai-instructions/instructions/use-builtin-template-task-packs.md`
- 触发词：#模板化、内置任务提示词工程、改造成模板仓库、接入 MAW 模板、任意项目改造成模板仓库、模板化改造
- 适用范围：在模板派生项目中同步新版模板能力；或把任意既有项目增量改造成 MAW 模板规范。

## 目标

让 AI 能根据用户一句话选择正确的升级路线，但不抢占升级主入口。`#项目升级` 的主入口是 `TINST-023 项目升级策略`；本指令只在 TINST-023 的取舍矩阵决定执行内置任务包时提供任务包入口。`#模板化` 进入内置模板化任务包。`#模板升级/#模版升级` 在源模板仓库进入 `TINST-024 模板升级策略`，在派生项目进入 `TINST-026 派生项目模板漂移升级`。

## 路由规则

| 用户意图 | 路由 | 说明 |
| --- | --- | --- |
| `#项目升级`、模板派生项目升级、升级到最新模板 | `TINST-023 项目升级策略` | 先解析源模板来源、审计目标项目事实、生成取舍矩阵，再决定是否执行内置任务包 |
| `#模板化`、任意项目改造成模板规范 | `prompts/codex/task-packs/adopt-maw-project-template-codex-tasks` | 建立 MAW 协作控制面，不移动业务源码 |
| `#模板升级/#模版升级`、生成模板升级资产 | 源模板仓库：`TINST-024 模板升级策略`，必要时调用 `TINST-011` | 在模板仓库中生成迁移说明、轻量提示词或任务包 |
| `#模板升级/#模版升级`、派生项目模板漂移升级 | 派生项目：`TINST-026 派生项目模板漂移升级` | 计算当前项目落后源模板多少提交，生成当前会话执行提示词并执行 |

## 内置任务包

| 场景 | 使用任务包 | 适用判断 |
| --- | --- | --- |
| 模板派生项目升级 | `prompts/codex/task-packs/template-feature-upgrade-codex-tasks` | 目标项目已经以本模板为来源，已有 `.maw/`、模块档案、项目指令或任务包等模板痕迹，需要选择性同步新版模板特性 |
| 任意项目改造成模板规范 | `prompts/codex/task-packs/adopt-maw-project-template-codex-tasks` | 目标项目尚未接入本模板规范，或只有零散 AI 规则，需要增量建立 MAW 协作控制面 |

## 可复制执行提示词

模板派生项目升级：

```text
执行任务提示词工程：prompts/codex/task-packs/template-feature-upgrade-codex-tasks
Seed 来源通道：<内部来源通道 | public_seed | unknown_legacy>
源模板本机路径：<源模板本机路径>
源模板 git 地址：<按 Seed 来源通道填写；外部公开项目使用 https://github.com/mawflow/mawflow-seed.git>
公开 Seed 仓：https://github.com/mawflow/mawflow-seed
源模板版本：main；未提供本机路径时可从 git 地址读取 main
源模板读取优先级：用户输入 > .local/.maw/template-source.yaml > .maw/template-source.yaml > 当前仓库；外部公开项目不得读取内部私有 Seed 源。
目标项目仓库：当前 Codex 会话所在仓库
升级范围：同步最新模板能力；必须先审计取舍再增量合并，不得整文件覆盖目标项目 README，不得误删目标项目已有 app_key、发布配置或项目私有规则。
```

任意项目改造成模板规范：

```text
执行任务提示词工程：prompts/codex/task-packs/adopt-maw-project-template-codex-tasks
Seed 来源通道：<内部来源通道 | public_seed | unknown_legacy>
源模板本机路径：<源模板本机路径>
源模板 git 地址：<按 Seed 来源通道填写；外部公开项目使用 https://github.com/mawflow/mawflow-seed.git>
公开 Seed 仓：https://github.com/mawflow/mawflow-seed
源模板版本：main；未提供本机路径时可从 git 地址读取 main
源模板读取优先级：用户输入 > .local/.maw/template-source.yaml > .maw/template-source.yaml > 当前仓库；外部公开项目不得读取内部私有 Seed 源。
目标项目仓库：当前 Codex 会话所在仓库
改造范围：增量接入 MAW 模板规范；先盘点项目事实和风险边界，不移动业务源码，不覆盖目标项目 README，不复制模板仓库远端、镜像目标、密钥或本机 .local 配置。
```

提示词中的 `<源模板本机路径>` 只作为当次执行输入占位。真实本机路径和内部私有 Seed Git URL 应由用户输入、受控内部配置或 `.local/.maw/template-source.yaml` 提供，不应写入目标项目的长期可提交文档；外部公开项目使用公开 Seed 仓。

## 执行步骤

1. 先读取 `docs/ai-instructions/README.md`、`docs/ai-instructions/experience-index.md`、本指令、`.maw/upgrade-policy.yaml` 和 `.maw/template-source.yaml`，确认用户目标属于项目升级、模板化改造、源模板仓库升级资产生成，还是派生项目模板漂移升级。
2. 如果用户给出目标项目路径，只把它用于当前会话定位和命令执行；不要把本机绝对路径写入可提交文档。
3. 解析源模板来源时，按用户输入 > `.local/.maw/template-source.yaml` > `.maw/template-source.yaml` > 当前仓库的顺序；共享配置只写占位和 git 来源，个人本机路径只写 `.local` 或当次用户输入。
4. `#项目升级` 必须先按 `TINST-023` 生成取舍矩阵；只有矩阵决定执行内置任务包时，才运行 `template-feature-upgrade-codex-tasks`。派生项目中的 `#模版升级/#模板升级` 不走 TINST-023，必须按 `TINST-026` 先计算模板漂移。
5. 如果目标项目已经包含对应任务包，按完整执行提示词执行，不要只传任务包路径。
6. 如果目标项目尚未包含对应任务包，先从模板仓库复制对应任务包目录到目标项目相同路径；只复制任务包文件，不复制模板仓库远端、镜像目标、密钥、`.local/` 私有配置或业务占位值。
7. 执行任务包时，先读该包的 `prompts/00-session-runbook.md`、`README.md`、`PLAN.md`、`manifest.json` 和独占 `SESSION_STATE.md`；如果状态文件不存在，从任务 01 开始并创建。
8. 保持默认 `same_session_auto_run`：完成一个子任务后更新 `SESSION_STATE.md`，继续下一个任务，直到 `NEXT_TASK: none`、遇到阻塞或用户打断。
9. 整个过程必须遵守经验索引优先、`solutions/**` 按命中读取、路径使用项目根相对路径、保护无关改动、不得提交真实密钥和本机 local 配置等仓库规则。
10. 模板升级和模板化改造都必须先审计、再取舍、后落地；不得把模板仓库文件整包覆盖目标项目。
11. 当前模板默认只内置 `server` / `client`。执行模板升级时，不得因为源模板删除默认 `admin` 占位就删除目标项目已有独立后台或其它 app_key；执行模板化改造时，也不得凭空新增后台组件，必须以目标项目事实为准。
12. 根目录 `README.md` 属于目标业务项目。执行模板升级或模板化改造时，不得用模板说明覆盖目标项目 README；模板仓库说明使用 `TEMPLATE_OVERVIEW.md` 或目标项目等价文件。
13. 模板升级和模板化改造中新建或改写的人类维护文档必须继承目标项目 `.maw/interaction.yaml` 的中文默认值；任务包正文、模块档案、component guide、README 补充段落和交付事实稿默认写中文。英文仅保留在代码标识、文件名/路径、命令、协议名、第三方库原文、机器字段 key、品牌/专有名词或用户明确要求的英文内容中。
14. 新建 component guide、模块档案或任务包子任务时，不使用 `Component Guide`、`Scope`、`Build Notes`、`Sensitive Config`、`Objective`、`Required Reads`、`Implementation Requirements`、`Acceptance Criteria`、`Final Response Requirements` 等英文标题；使用“组件说明”“范围”“构建说明”“敏感配置”“目标”“必读文件”“实现要求”“验收标准”“最终说明要求”等中文标题。
15. 配置、任务包 manifest、升级资产或模板元数据需要保留英文说明时，默认人读字段写中文；英文说明放入同一对象的 `i18n.ai.en-US`，中文说明可放入 `i18n.human.zh-CN`。英文主要给 AI 读，不作为人读默认文案。
16. 如果本指令只是为目标项目生成内置任务包执行入口、handoff prompt 或可复制提示词，而不是在当前目标项目内直接执行，最终说明必须包含“目标项目使用方式”：
    - 先写清固定入口语：“复制以下提示词到目标仓库会话执行。”
    - 列出提示词、handoff prompt、`EXECUTE_PROMPT.md` 或任务包入口文件的项目根相对路径和当前本机绝对路径；本机绝对路径只允许出现在当次最终说明里。
    - 如果目标仓库 Codex 会话能访问当前机器上的本地文件，给出：

```text
请完成 <提示词或执行入口文件本机绝对路径> 任务
```

    - 如果目标仓库 Codex 会话不能访问该本机文件，说明：打开 `<提示词或执行入口文件项目根相对路径>`；若文件内有 `text` 代码块，复制代码块整段，粘贴到目标派生项目的 Codex 会话里执行；若是 `EXECUTE_PROMPT.md` 等无 `text` 代码块的入口文件，则复制文件全文。
    - 如果目标项目已经包含任务包目录，也可以给出 `#跑任务包：<任务包目录>`；如果尚未包含，先复制任务包目录到目标项目相同路径。

## 验证方式

- 选中的任务包目录存在，并包含 `manifest.json` 与 `prompts/00-session-runbook.md`。
- `manifest.json` 可被 JSON 解析。
- 任务包内包含 `SESSION_STATE`、`NEXT_TASK`、`RESUME_FROM`、`experience_lookup`、`release_update_status`、`release_commands` 和 `release_confirmation_prompt`。
- 执行提示词、任务包 README 或 `SESSION_STATE.md` 中已明确源模板仓库位置或版本引用。
- 如果只是生成给目标项目会话的执行入口，最终说明包含本地文件可访问和不可访问两种使用方式。
- 可提交文件中没有本机项目绝对路径、真实密钥、模板仓库私有远端或未脱敏日志。
- 新建或改写的任务包正文、模块档案、component guide、README 补充段落和交付事实稿默认中文；未出现 `Objective`、`Required Reads`、`Implementation Requirements`、`Acceptance Criteria`、`Final Response Requirements`、`Component Guide`、`Scope`、`Build Notes`、`Sensitive Config` 等英文标题，除非用户明确要求英文或文件属于第三方原文。
- 最终说明采用中文、人类优先主展示，写清使用了哪个内置任务包、经验命中、模块档案是否更新、命中的 code 组件应用和发布状态；需要发布但当前未发布或未验证时，按 app_key 给出可复制 `#发布` 指令，并在收口末尾询问是否“确认发布全部”，多个 app_key 可选择部分发布，用户回复“确认发布全部/确认/是”则发布全部待发布组件，发布指令和默认环境必须来自目标项目发布配置。机器字段集中放到末尾技术元数据。

## 禁区

- 不得要求后续会话安装本机 Codex skill 才能执行任务包。
- 不得把源模板仓库的 `.git`、remote、镜像目标、客户仓库映射、真实 secrets 或 `.local/` 私有配置复制到目标项目。
- 不得为了符合模板结构强行移动业务源码、改发布脚本或覆盖真实配置；这类动作必须先列为高风险待确认项。
- 不得把“模板默认无 admin”误用成“目标项目必须无 admin”；目标项目已有独立后台时应保留并适配，目标项目没有独立后台时也不新建后台占位。
- 不得整文件覆盖目标项目根 `README.md`；已有 README 只能做最小段落合并，缺失时才创建业务项目 README 占位。
- 不得把任务包执行成一次性长提示词；必须维护 `SESSION_STATE.md`。

## 冲突与覆盖规则

- 用户最新明确要求优先。
- 目标项目当前代码、配置、模块档案和 active 文档优先于模板默认值。
- 如果任务包与目标项目规则冲突，先按更保守、更保护现有项目的规则执行，并在 `SESSION_STATE.md` 记录冲突。
- 源模板默认组件变化与目标项目真实 app_key 冲突时，以目标项目真实 app_key 和发布边界为准；模板变化只作为新项目默认口径或待确认的清理建议。
- 源模板 README 结构与目标项目 README 冲突时，以目标项目 README 为准；模板说明迁移到 `TEMPLATE_OVERVIEW.md`。
- 与 `TINST-007 创建和执行任务提示词工程` 冲突时，本指令只负责内置包路由，`TINST-007` 负责通用任务包创建与执行协议。
- 与 `TINST-023 项目升级策略` 冲突时，本指令只负责路由和内置任务包入口，项目升级策略以 `TINST-023` 为准。
- 与 `TINST-024 模板升级策略` 冲突时，模板仓库自身升级资产生成以 `TINST-024` 为准；派生项目模板漂移升级以 `TINST-026` 为准。

## 更新记录

- 2026-06-14：改为升级路线 router；`#项目升级` 进入 TINST-023，`#模板升级/#模版升级` 进入 TINST-024/TINST-011；源模板本机路径改为占位或 `.local` 来源。
- 2026-06-14：补充派生项目 `#模版升级/#模板升级` 路由到 TINST-026，不再误走 `#项目升级`。
- 2026-06-12：补充内置任务包完整执行提示词，默认填入本机模板路径和项目 git 地址，并要求优先读取本机路径。
- 2026-06-12：补充根 README 属于业务项目、模板说明改用 `TEMPLATE_OVERVIEW.md` 的非覆盖口径。
- 2026-06-12：补充默认无 admin 的非破坏性升级/改造口径。
- 2026-06-12：创建，登记模板派生项目升级和任意项目模板化改造两个内置任务包。
