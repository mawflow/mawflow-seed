# 指令：模板升级策略

## 元信息

- ID：TINST-024
- 类型：项目指令
- 状态：启用
- 维护位置：`docs/ai-instructions/instructions/template-upgrade-strategy.md`
- 触发词：#模板升级、#模版升级、模板升级、模版升级、生成模板升级资产、升级迁移说明、派生项目升级提示词
- 适用范围：源模板仓库自身把一次模板变更整理成派生项目可安全采用的升级资产。派生项目执行 `#模版升级/#模板升级` 时不使用本指令，应走 `TINST-026 派生项目模板漂移升级`。

## 目标

在源模板仓库中，`#模板升级/#模版升级` 不直接升级目标项目，而是生成可传播资产：机器策略、迁移说明、轻量提示词或完整任务包。在派生项目中，同样的触发词用于计算模板漂移并当前会话执行升级，路由到 `TINST-026`。

## 未指定 commit 时的默认路由

- 是否指定 commit 不决定在哪个仓库执行；当前 Codex 会话所在仓库的角色才决定路由。
- 当前仓库是源模板仓库时，`#模板升级/#模版升级` 仍在源模板仓库执行本指令，生成迁移说明、提示词或任务包；不切换到派生项目，也不直接修改目标项目。源模板仓判断不能只看 fork 后会被复制的 `.maw-template/template.yaml` 或 `.maw/repository-identity.yaml`，还应结合仓库身份检测、Git `origin`、`template_source.git_url` 和 `template_source.source_channel` 的证据。
- 未指定 commit/range 时，先用当前源模板仓库的 `git status --short`、`git log -1 --oneline`、必要时 `git diff --name-only` 或用户刚才的说明识别本次模板变更；若仍无法判断具体新特性或传播范围，先向用户确认，不得编造升级内容。
- 当前仓库是派生项目时，同一触发词不使用本指令，应走 `TINST-026`：先读取 `.maw/template-source.yaml` 的 `template_source.source_channel`，再按 `template_source.version`（默认 `main`）解析目标模板 commit，并与 `template_source.applied_version` 比较后执行。直接 fork 的派生项目即使继承了 `seed_repository` 声明，只要用户说明当前仓库作为派生项目使用，或 Git `origin` 不再是源模板 `template_source.git_url`，就不能默认走本指令。

## 输出资产

按风险和范围生成：

1. 机器策略：`.maw-template/upgrades/<upgrade_key>.yaml`。
2. 迁移说明：`docs/template-migrations/YYYYMMDD-<slug>.md`。
3. 派生项目提示词：`prompts/codex/template-upgrade-prompts/YYYYMMDD-<slug>-prompt.md`。
4. 高风险时生成完整任务包或人工确认清单。

## 风险等级

- T0：模板内部说明，不需要派生项目升级。
- T1：文档/提示词增强，轻量提示词。
- T2：`.maw` 配置字段、任务路由、收口协议，迁移说明 + 提示词。
- T3：脚本、发布、客户仓、密钥策略，任务包 + 人工确认。
- T4：影响 `code/` 结构、app_key、发布行为，默认不自动传播。

## 执行步骤

1. 读取 `.maw/upgrade-policy.yaml`、`.maw/template-source.yaml`、`.maw-template/upgrades/README.md`、`docs/template-migrations/README.md` 和 `prompts/codex/template-upgrade-prompts/README.md`。
2. 用当前 diff、commit、用户说明或文件列表识别模板变更。
   - 未指定 commit 时按“未指定 commit 时的默认路由”处理；如果当前仓库角色或变更范围有歧义，先问清楚。
3. 判断风险等级和传播方式。
4. 使用 `docs/ai-instructions/templates/upgrade-decision-matrix.md` 描述目标项目取舍建议。
5. 生成升级资产，所有路径使用项目根相对路径。
   - 生成派生项目提示词文件时，必须新增字段“本机模板仓库目录”，填入当前源模板仓库 `pwd -P` 的绝对路径；目标项目执行时先检查该目录是否存在，存在则优先读取，不存在才按原“源模板本机路径”和其它来源兜底。不要改变“源模板本机路径”字段只来自用户输入或 `.local` 的原语义。
   - 生成给外部公开项目的提示词时，必须写明 `source_channel: public_seed` 和公开 Seed URL，不得要求外部项目访问内部私有 Seed 源。
6. 对高风险项明确人工确认和不自动传播规则。
7. 验证后按中文人类优先格式收口，并记录 `upgrade_strategy_update`。
   - 如果升级资产或提示词要求目标项目在完成升级后提交、推送并同步 mirror，必须写成“推送后先运行仓库级 mirror 计划命令，以有效计划判断是否同步”；不要让目标项目只读取原始 `repository_mirrors.enabled`。
8. 最终说明必须包含“目标项目使用方式”，尤其是生成了派生项目提示词时：
   - 先写清固定入口语：“复制以下提示词到目标仓库会话执行。”
   - 先列出本次生成的提示词文件路径，包含项目根相对路径和当前本机绝对路径；本机绝对路径只允许出现在当次最终说明里，不写入可提交文档正文。
   - 如果目标仓库 Codex 会话能访问当前机器上的本地提示词文件，给出可直接复制到目标仓库会话执行的一行：

```text
请完成 <提示词文件本机绝对路径> 任务
```

   - 如果目标仓库 Codex 会话不能访问该本机文件，说明：打开 `<提示词文件项目根相对路径>`，复制里面的 `text` 代码块整段，粘贴到目标派生项目的 Codex 会话里执行。
   - 如果生成了多个提示词文件，逐个列出上述两种用法；如果只在聊天中输出提示词而未生成文件，说明直接复制当前回答中的 `text` 代码块到目标项目 Codex 会话。

## 禁区

- 不把个人本机模板路径写入目标项目长期可提交文档；真实本机路径只放 `.local/.maw/template-source.yaml`、当次用户输入，或生成给目标项目执行的模板升级提示词字段“本机模板仓库目录”。
- 不把提示词文件的本机绝对路径写入迁移说明、机器策略、提示词正文或其它可提交文档；最终答复中可作为当次使用说明提供。这里的“提示词文件本机绝对路径”指 `请完成 <提示词文件本机绝对路径> 任务` 的文件路径，不是提示词正文里的“本机模板仓库目录”字段。
- 不复制源模板 Git remote、镜像目标、真实 secrets、`.local` 私有配置或测试账号到派生项目。
- 不要求目标项目整文件覆盖 README、`code/`、app_key、发布配置、仓库映射或模块档案。
- 不把 T4 风险变更自动传播给派生项目。

## 冲突与覆盖规则

- 与 `TINST-011` 冲突时，本指令负责策略和资产边界；`TINST-011` 负责生成轻量提示词文本。
- 与 `TINST-023` 冲突时，本指令在模板仓库生成资产；`TINST-023` 在目标项目执行升级。
- 与 `TINST-026` 冲突时，本指令只适用于源模板仓库；派生项目执行模板漂移升级走 `TINST-026`。
