# 指令：种子仓库升级

## 元信息

- ID：TINST-027
- 类型：项目指令
- 状态：启用
- 维护位置：`docs/ai-instructions/instructions/seed-repository-upgrade.md`
- 推荐调用：`#种子仓库升级`
- 精确调用：`#T027` 或 `#T027/<消歧词>`
- 触发词：#种子仓库升级、种子仓库升级、模板仓库升级建议、回流种子仓库、回流模板仓库、建议更新种子仓库、建议更新模板仓库、派生项目反向升级、反向升级种子仓库、能力回流、模板能力回流、upstream seed repository、seed repository upgrade、upstream feedback loop
- 适用范围：派生项目开发中发现可复用能力需要回流到 `maw-project-template`；种子仓库中接收派生项目回流提示词并增量实现。

## 目标

建立派生项目到种子仓库的可复用能力反馈闭环：

1. 统一口径：“种子仓库”和“模板仓库”都指 `maw-project-template`。
2. 派生项目知道自己来自种子仓库，并尽量区分能力来源：来自种子仓库、项目自定义、建议回流种子仓库。
3. AI 在开发过程中发现种子仓库可优化或可新增能力时，最终收口必须明确指出，并记录到合适目录。
4. 用户触发 `#种子仓库升级` 时，在派生项目中生成一段“在种子仓库执行”的任务提示词，把候选能力同步给种子仓库维护会话。
5. 所有建议默认向下兼容，只做增项或默认关闭能力，避免破坏历史派生项目。
6. 反向升级必须形成可追踪证据链：候选记录 -> 种子仓执行提示词 -> 种子仓采纳/拒绝/补证据 -> 模板升级资产 -> 派生项目可执行升级提示。

## 编号规则

- 本指令是模板内置指令 `TINST-027`，精确调用使用 `#T027`。
- 派生项目同步本指令时只追加或更新 `TINST-027`，不得重排已有 `PINST-XXX`。

## 输入要求

- 必需输入：建议回流的场景或问题；若用户只说“种子仓库升级”，AI 应从当前会话上下文、最近 diff、候选记录、能力索引和项目信号中推断。
- 可选输入：涉及文件、已实现的派生项目自定义能力、期望进入种子仓库的能力、优化/新增理由、兼容性要求、风险等级、是否已有人类确认、是否只生成提示词不执行、是否允许在当前种子仓会话直接评估落地。
- 缺失时处理：
  - 能从当前仓库事实安全推断的，直接补齐并标记为“根据当前 diff/上下文推断”。
  - 无法判断建议内容时，先让用户补充 1 到 3 个问题，并给出参数获取步骤、建议选项和填写格式。
  - 涉及敏感参数时，先在 `.local/` 的合适位置创建本机填写文件，让用户填写后回复确认。

## 执行步骤

### 1. 读取最小上下文

读取：

- `.maw/project.yaml`
- `.maw/template-source.yaml`
- `.maw/upgrade-policy.yaml`
- `.maw/repository-identity.yaml`
- `.maw/capabilities.yaml`
- `.maw/project-signals.yaml`
- `.maw/codex-context.md`
- `docs/seed-repository-upgrade-candidates.md`
- `docs/ai-instructions/README.md`
- `docs/ai-instructions/experience-index.md`
- `docs/ai-instructions/terms/seed-repository.md`
- 当前任务直接相关文件、模块档案或脚本说明。

### 2. 判断仓库角色和方向

1. 判断当前仓库角色：
   - 若 `.maw-template/template.yaml` 中 `template.repository_role: maw_project_seed_repository` 存在，则当前仓库是种子仓库。
   - 若存在 `.maw/template-source.yaml` 且不是上述种子仓库角色，则按派生项目处理。
   - 若角色冲突或无法判断，先向用户确认。
2. 判断方向：
   - 派生项目 -> 种子仓库：走本指令，记录候选并生成种子仓执行提示词。
   - 种子仓库 -> 派生项目：走 `TINST-024/TINST-026`，生成或执行模板升级资产。
   - 当前项目同步种子仓能力：走 `TINST-023`，不要误当反向回流。
3. 如果回流内容涉及 Seed 来源、公开仓、发布镜像或开源发布，先区分通用模板协议与来源项目专用实现：
   - 种子仓可接纳 `内部来源通道` / `public_seed` / `unknown_legacy` 来源通道、通用 `repository_publish_mirrors` 结构、`#发布公开镜像` 和开源发布前 gate。
   - 种子仓不得写入来源项目或主仓的真实发布 target、本机 remote、真实 token、`.local` 配置、发布记录目录或专用指令，例如主仓特有的 `#发布Seed开源仓`。

### 3. 自动发现候选能力

派生项目每次开发、修复、同步、发布、任务包或脚本规范化收口时，都应判断是否出现以下信号：

- 为当前项目新写了可复用脚本、检查器、提取器、模板、任务包或治理协议。
- 修复了多项目都会遇到的坑，而不是单项目业务规则。
- 当前项目 `.local`、发布、同步、客户仓、MCP、宿主机、脚本执行、测试入口或收口流程出现可抽象规范。
- AI 多次被同类中间态、长日志、环境差异、歧义触发词或旧协议误导。
- 派生项目新增字段、状态文件、目录结构或提示词模式，能默认关闭并兼容旧项目。
- 候选能力已在一个派生项目验证，但另一个派生项目也可能复用。
- 调整产品口径、PM 源称谓、API 摘要、状态标签、命令输出或静态 UI 文案后，CI/pytest 因旧字面量断言失败。
- 修复 CI 时发现实现和测试断言分离更新，例如实现已从具体系统名改成通用口径，但 `tests/` 仍断言旧名称。

不要回流以下内容：

- 单项目业务流程、客户私有规则、真实 app_key 私有逻辑、客户数据或生产连接信息。
- 需要覆盖派生项目 `README.md`、`code/`、发布配置、仓库映射、secrets、`.local` 或模块档案才能生效的能力。
- 还没有稳定边界、无法描述输入输出、或没有证据路径的想法。

### 4. 候选分级

| 级别 | 含义 | 处理 |
| --- | --- | --- |
| S0 | 明显只适合当前项目 | 标记 `rejected_or_local_only` 或不记录，收口说明原因 |
| S1 | 有复用可能但证据不足 | 记录为 `candidate`，补证据，不生成执行提示词或标记待补 |
| S2 | 已验证且可默认关闭/可选启用 | 记录候选并生成种子仓执行提示词 |
| S3 | 多项目高价值治理能力 | 记录候选，生成提示词，建议种子仓接纳后生成模板升级资产 |
| S4 | 涉及发布、客户仓、密钥、MCP、宿主机或远端写 | 记录候选和人工确认清单，种子仓接纳时按高风险升级处理 |

### 5. 在派生项目中执行

1. 识别候选能力来源：`seed_repository`、`derived_project_custom`、`candidate_for_seed_repository` 或 `unknown_legacy`。
2. 若 `.maw/template-source.yaml`、`.maw/capabilities.yaml` 或模块档案存在能力来源字段，优先使用；旧项目缺字段时按兼容推断，不阻塞。
3. 把候选项记录到 `docs/seed-repository-upgrade-candidates.md`，必须写清：
   - 使用场景。
   - 建议优化/新增内容。
   - 优化/新增理由。
   - 向下兼容要求。
   - 风险与影响。
   - 证据路径。
   - 建议修改位置。
   - 验证建议。
4. 生成可复制到种子仓库会话执行的任务提示词；派生项目中不要直接修改种子仓库文件。
5. 如果需要落库提示词，优先写入：

```text
prompts/codex/seed-repository-upgrade-prompts/YYYYMMDD-<slug>-prompt.md
```

该目录只保存“派生项目 -> 种子仓库”的反向回流提示词；不要混入 `prompts/codex/template-upgrade-prompts/`，后者用于“种子仓库 -> 派生项目”的模板能力传播。

6. 如果用户只要求评估，不落文件，则在最终说明中给出完整提示词，并标记 `seed_repository_upgrade_suggestions=已生成提示词未落库`。

### 6. 在种子仓库中执行

1. 读取派生项目生成的任务提示词和候选记录。
2. 先判断建议是否应进入种子仓库：
   - 是否跨项目可复用。
   - 是否能默认关闭、可选启用或仅作为检查/提示。
   - 是否不覆盖历史项目事实。
   - 是否有明确输入输出、验证方式和证据路径。
   - 是否属于种子仓的协议、文档、提示词、检查脚本、模板资产或公共脚本范围。
3. 按决策输出处理状态：
   - `accepted_in_seed_repository`：接纳并增量实现。
   - `prompt_generated`：候选记录完成，提示词已生成，等待种子仓执行。
   - `rejected_or_local_only`：只适合来源项目，写明拒绝理由。
   - `needs_more_evidence`：证据不足，列出需要派生项目补充的路径、验证或场景。
4. 若接纳，按 `TINST-024` 判断风险等级并生成必要资产：
   - `.maw-template/upgrades/<upgrade_key>.yaml`
   - `docs/template-migrations/YYYYMMDD-<slug>.md`
   - `prompts/codex/template-upgrade-prompts/YYYYMMDD-<slug>-prompt.md`
   - 高风险时生成 `prompts/codex/task-packs/<slug>-codex-tasks/`
   - 若候选来自测试契约漂移，必须同步生成 pytest/static 断言检索、聚焦测试和 `run-project-tests` 验证要求。
5. 更新 `docs/seed-repository-upgrade-candidates.md` 的状态和提示词状态。
6. 必要时更新 `.maw/capabilities.yaml`、`.maw/project-signals.yaml`、`PROJECT_COMMANDS.md`、`docs/ai-instructions/README.md`、`experience-index.md` 和对应检查脚本。

### 7. 收口要求

- 最终说明必须包含“种子仓库升级建议”状态：未发现、已记录、已生成提示词、已在种子仓库执行、证据不足待补、或仅适合当前项目。
- 技术元数据必须包含 `seed_repository_upgrade_suggestions`。
- 如果写入反向提示词，报告路径。
- 如果种子仓接纳并产生模板升级资产，报告升级资产路径和派生项目采用方式。
- 若需要用户补参数，按 `TINST-020` 给出获取步骤、建议选项、填写格式；敏感参数写入 `.local/` 本机填写文件。

## 派生项目执行简版

```text
1. 判断是否是可复用能力，而不是单项目业务逻辑。
2. 在 docs/seed-repository-upgrade-candidates.md 记录候选。
3. 生成 prompts/codex/seed-repository-upgrade-prompts/YYYYMMDD-<slug>-prompt.md。
4. 最终说明写 seed_repository_upgrade_suggestions。
5. 不直接修改种子仓库文件。
```

## 种子仓执行简版

```text
1. 读取反向提示词和候选记录。
2. 判断 accepted / rejected_or_local_only / needs_more_evidence。
3. 接纳时增量实现，默认关闭或兼容旧项目。
4. 生成模板升级资产，让派生项目能吃到能力。
5. 更新候选状态、验证、提交、推送和 mirror plan。
```

## 种子仓库执行提示词模板

```text
请在种子仓库 maw-project-template 中评估并增量实现以下来自派生项目的种子仓库升级建议。

来源派生项目：<项目名、仓库角色或脱敏描述>
发现方式/使用场景：<在哪次开发、修复、发布、同步、任务包或收口中发现>
当前派生项目实现或问题：<项目自定义能力、痛点或已验证方案>
建议进入种子仓库的能力：<要抽象成模板能力的内容>
优化/新增理由：<为什么多个派生项目会受益>
能力来源判断：<derived_project_custom / candidate_for_seed_repository / unknown_legacy>
候选分级：<S1/S2/S3/S4>
兼容性要求：
- 只做增项或默认关闭能力，不破坏历史派生项目。
- 保留旧字段、旧指令和旧目录语义；旧项目缺少新字段时按兼容处理。
- 不覆盖目标项目 README、code、app_key、发布配置、仓库映射、secrets、.local 或模块档案。
- 如需派生项目采用，生成 .maw-template/upgrades、docs/template-migrations 和 prompts/codex/template-upgrade-prompts 中的升级资产。

参考证据路径：
- <项目根相对路径；禁止真实密钥、本机路径和客户隐私>

建议修改位置：
- <种子仓库中可能涉及的 .maw/docs/prompts/ops 路径>

验证建议：
- <在来源派生项目已通过的命令或人工验证>
- <种子仓接纳后应运行的模板检查>

执行要求：
1. 先读取 AGENTS.md、.maw/codex-context.md、.maw/agent-briefing.md、.maw/template-source.yaml、.maw/upgrade-policy.yaml、docs/ai-instructions/README.md、docs/ai-instructions/instructions/template-upgrade-strategy.md 和当前建议相关文件。
2. 判断是否接纳为种子仓库通用能力；如果只适合来源项目，记录拒绝理由。
3. 如果证据不足，先标记 needs_more_evidence，并列出派生项目需要补充的证据，不要强行实现。
4. 接纳时按向下兼容原则增量实现，默认不改变历史派生项目行为。
5. 必要时生成模板升级资产和派生项目执行提示词。
6. 运行 git diff --check、bash ops/scripts/check-template-module-docs.sh、bash ops/scripts/check-ai-framework-consistency.sh、bash ops/scripts/check-local-boundary.sh，以及相关专项检查。
7. 按种子仓库规则提交、推送，并在推送后运行 ops/scripts/sync-repository-mirror.sh plan，根据有效计划决定是否同步 mirror。
8. 最终说明中明确“种子仓库升级建议”的处理状态、兼容性取舍、生成的升级资产和验证结果。
```

## 验证方式

- `docs/seed-repository-upgrade-candidates.md` 已新增或更新候选项，且包含使用场景和优化/新增理由。
- 收口说明包含 `seed_repository_upgrade_suggestions`。
- 生成的种子仓库执行提示词包含来源派生项目、使用场景、建议能力、理由、候选分级、兼容性要求、证据路径、执行要求和验证要求。
- 若落库提示词，路径位于 `prompts/codex/seed-repository-upgrade-prompts/`，不混用模板升级提示词目录。
- 若在种子仓库接纳建议，已按 `TINST-024` 判断是否需要升级资产。
- 运行项目可用的文档/配置检查，至少包含 `git diff --check` 和相关模板一致性检查。

## 禁区

- 不在派生项目中直接改种子仓库文件；派生项目只记录候选项并生成种子仓库执行提示词。
- 不把派生项目反向回流提示词放入 `prompts/codex/template-upgrade-prompts/`；该目录只用于种子仓向派生项目传播模板能力。
- 不把只适合单个项目的业务逻辑强行抽象到种子仓库。
- 不写真实密钥、token、客户隐私、生产连接串、未脱敏日志或个人本机路径。
- 不覆盖历史派生项目已有 README、`code/`、app_key、发布配置、仓库映射、secrets、`.local/` 和模块档案。
- 不为了新字段要求历史项目一次性补齐；缺字段时必须兼容。

## 冲突与覆盖规则

- 用户最新明确要求优先；但任何要求若会泄露敏感信息或破坏历史项目兼容性，必须先说明风险并给出安全替代方案。
- `#种子仓库升级` 与 `#模板升级/#模版升级` 同时出现时，先判断方向：派生项目回流到种子仓库走本指令；种子仓库向派生项目传播能力走 `TINST-024/TINST-026`。
- 与 `#项目升级` 同时出现时，先确认是“把种子仓库能力同步到当前项目”，还是“把当前项目能力建议回流到种子仓库”。

## 更新记录

- 2026-06-20：接纳测试契约漂移防护经验，明确口径、文案、API 摘要、状态标签、PM 源或命令输出变化后必须同步搜索和更新 pytest/static 断言。
- 2026-06-19：强化派生项目反向升级种子仓库流程，新增自动发现信号、候选分级、反向提示词目录和种子仓采纳/拒绝/补证据闭环。
- 2026-06-15：创建，增加派生项目到种子仓库的升级建议记录和提示词生成闭环。
