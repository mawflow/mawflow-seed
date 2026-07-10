# RTK Rules For MAW Projects

本仓库默认启用 `rtk` 作为 shell 输出压缩层。

本文件面向由 MultiAgentWorker 项目模板初始化的项目仓库。它适用于业务项目、客户交付镜像仓库、内部开发仓库，以及仍在维护模板本身的仓库。使用 shell 命令时，目标是减少无关输出进入上下文、按项目边界读取资料、保留必要诊断信息，并避免长日志、构建产物、依赖目录或历史归档干扰判断。

## 基本规则

所有 shell 命令默认先尝试 `rtk` 包装。

- 优先使用 `rtk <command>`。
- 只有 `rtk` 不支持、会破坏命令行为、或必须获取原始机器可解析输出时，才使用 `rtk proxy <command>`。
- 文件读取、搜索、diff、git 状态查看和脚本验证默认不要直接使用原生命令。
- 长输出先落盘或缩小范围，再用 `rtk log`、`rtk summary`、`sed -n` 或限定路径读取摘要。
- 搜索和读取必须先限定任务相关目录；不要因为缺少上下文就整仓扫描。

## 推荐命令映射

```bash
rtk git status --short
rtk git diff -- README.md docs .maw code/<component>
rtk read README.md
rtk read .maw/codex-context.md
rtk read .maw/agent-briefing.md
rtk read docs/README.md
rtk read docs/ai-coding/README.md
rtk read docs/ai-instructions/README.md
rtk grep "module_key" .maw docs/modules docs/ai-coding
rtk grep "external_mapped" README.md docs .maw
rtk grep "<keyword>" docs code/<component>
rtk find docs/modules -name 'module.md'
rtk bash -n ops/scripts/<script>.sh
rtk python -m py_compile ops/scripts/<script>.py
rtk bash ops/scripts/check-template-module-docs.sh
rtk yaml .maw/project.yaml
```

如果某条命令在 `rtk` 下不可用，使用：

```bash
rtk proxy <command>
```

使用 `rtk proxy` 后仍必须自行限制目录、文件和输出行数。

## 上下文读取边界

MAW 项目通常同时包含需求、设计、模块档案、AI 协作规则、运维脚本、发布覆盖层和一次性提示词。默认按“启动上下文 -> 总索引 -> 子目录 README -> 任务相关文档 -> 必要片段”的顺序读取。

- 开始任何开发、配置、文档或脚本任务前，先读 `README.md`、`.maw/codex-context.md`、`.maw/agent-briefing.md`、`.maw/project.yaml`、`.maw/components.yaml`、`.maw/modules.yaml`、`.maw/policies.yaml`、`docs/README.md`。
- 处理具体端代码时，先读对应 `code/<component>/.maw.component.yaml` 和 `docs/ai-coding/component-guides/<component>.md`。
- 处理需求、设计、计划、验收或交付资料时，先读 `docs/README.md` 和对应子目录 `README.md`，再读任务相关文件。
- 处理 AI 编码边界时，先读 `docs/ai-coding/README.md`，再按任务风险读取初始化清单、模块档案规则、代码风格或端说明。
- 处理项目指令、术语、别名或经验沉淀时，先读 `docs/ai-instructions/README.md`；涉及实现、修 bug、测试、构建、发布、同步或脚本执行经验时，先检索 `docs/ai-instructions/experience-index.md`，再读命中的完整说明。
- 处理模块任务时，先读 `.maw/modules.yaml` 定位 `module_key`，再读对应模块组 README、叶子模块 `module.md` 和 `changelog.md`。
- 处理发布、脱敏、部署、交付包或客户仓库同步时，按需读 `release/rules.yaml`、`.maw/releases.yaml`、`.maw/environments.yaml`、`.maw/repositories.yaml`、`.maw/policies.yaml`、`docs/customer-repository-sync-guide.md` 和对应 `ops/` 脚本说明。

禁止为了“了解项目”全量读取 `docs/**`、`prompts/**`、`release/**`、`artifacts/**`、`reports/**` 或 `code/**`。

## 默认排除目录

搜索、diff、统计和日志查看默认排除：

- `.git/`
- `.local/`
- `artifacts/`
- `reports/`
- `node_modules/`
- `.venv/`
- `dist/`
- `build/`
- `coverage/`
- 运行日志、缓存、依赖目录、构建产物和用户上传文件

`docs/archive/**` 是历史归档，默认不读；只有用户明确给出具体路径或要求历史追溯时，才读取最小必要片段。

## MAW 项目通用注意事项

- `code/<component>` 是普通业务源码目录，不要把它变成客户仓库 clone、submodule 或 worktree。
- 业务配置以 `code/<component>` 内部工程文件为权威来源；`.maw/app-runtime.yaml` 只作为 AI 调试索引。
- `.maw/` 是 AI/人工协作控制配置，读取配置时要考虑 base、dev/pro profile、local 覆盖的聚合关系。
- `.maw/*.local.yaml`、`.local/`、日志、缓存、构建产物和用户上传文件默认不提交。
- 内部受信任仓库可以按项目规则保存必要 `.maw/secrets*.yaml`；导出交付包、同步客户仓库或写外部提示词前必须执行脱敏检查。
- `prompts/` 存放一次性提示词，manual-only；可长期触发的项目指令应放在 `docs/ai-instructions/`。
- 每次实现、修 bug、测试、构建、发布、同步或执行脚本前，先用任务关键词、路径、命令和错误症状检索 `docs/ai-instructions/experience-index.md`；`docs/ai-instructions/solutions/**` 只在索引、候选台账或用户明确路径命中具体文件后读取，不主动全量读取。
- `release/` 只存发布随带文件覆盖层和规则，不存构建产物、日志、缓存、用户上传文件或裸凭证文件。
- 页面、接口、数据表、配置、状态流、发布规则或客户仓库同步边界变化后，要判断是否同步更新 `.maw/modules.yaml`、对应模块档案、changelog 和相关设计/交付文档。
- 如果当前仓库仍是模板仓库，维护模板协议时优先做 additive 变更；同步到已有项目时不覆盖已有业务代码、项目私有文档、真实 secrets、`.maw/*.local.yaml` 或客户仓库映射。
- “种子仓库”和“模板仓库”统一指 `maw-project-template`。派生项目开发中如果发现适合回流种子仓库的优化或新增能力，必须记录到 `docs/seed-repository-upgrade-candidates.md`，写清使用场景、优化/新增理由、证据路径和向下兼容要求。
- 需要把派生项目建议同步给种子仓库维护会话时，使用 `#种子仓库升级` / `TINST-027` 生成在种子仓库执行的任务提示词；旧派生项目缺少能力来源字段时按兼容处理，不阻塞当前任务。
- 输入资料整理、提示词、报告、交付说明和最终输出中，凡涉及当前项目目录或文件路径，一律使用项目根相对路径；不要把某台设备上的项目绝对路径写入可提交文档或可复用提示词。
- 仓库级镜像配置默认在 `.maw/repositories.yaml` 的 `repository_mirrors`，但收口判断必须以 `ops/scripts/sync-repository-mirror.sh plan` 的有效结果为准；该脚本会读取聚合配置、`.local/.maw/repositories.yaml` 本机 overlay 和模板仓库兼容字段。不要只凭原始 `repository_mirrors.enabled=false` 判断未启用。`plan` 显示已配置且自动同步开启时，每次成功推送项目仓库后继续执行 `ops/scripts/sync-repository-mirror.sh push --execute` 同步 mirror。
- 组件镜像仓库是单向目标仓库，只允许当前项目仓库同步到目标仓库；禁止从镜像仓库拉取、合并或反向覆盖当前项目。

## 测试与验证输出规则

- Shell 脚本优先用 `rtk bash -n <script>` 做语法检查，再运行目标脚本。
- Python 脚本优先用 `rtk python -m py_compile <script>` 做语法检查；配置聚合脚本可补一个 dry-run，例如 `rtk python ops/scripts/maw-config-merge.py environments --profile dev --get environments.test.profile --format text`。
- YAML 或配置聚合相关改动，优先验证 `.maw/*.yaml` 能被解析，并按 `docs/configuration-guide.md` 的聚合规则检查。
- 模块档案协议相关改动，优先运行项目提供的模块档案检查脚本；模板默认脚本是 `ops/scripts/check-template-module-docs.sh`。
- 端工程测试、构建、类型检查和 lint 命令以 `code/<component>/.maw.component.yaml`、端工程 README、package 脚本或构建文件为准。
- 导出、部署、脱敏、客户仓库同步脚本默认先读脚本 README 和 dry-run 说明；不要直接执行会改远端状态的命令。
- 构建、导出或长任务输出只保留失败摘要、warning/error、退出码和关键产物路径。

## Git 与变更查看规则

- 看状态优先用 `rtk git status --short`。
- 看 diff 优先限制文件或目录，例如 `rtk git diff -- docs/ai-instructions README.md code/<component>`。
- 不要默认输出整仓 diff 或长 patch。
- 完成一段任务、任务包子任务或其它可独立验证的里程碑后，只要产生了代码、配置、文档或脚本改动，就必须按项目规则验证、提交并推送当前分支，并按仓库级 mirror 有效计划同步镜像；不要等用户再次要求“提交 push”。推送成功后先运行 `ops/scripts/sync-repository-mirror.sh plan`，以 `Configured`、`Config source`、`Auto sync`、`Target enabled` 和 `Target auto sync` 判断是否继续同步仓库级镜像。commit message 和提交内容说明使用中文。
- 推送时先提交并推送本次任务实际改动；随后再次检查工作区。若仍有无关脏改动，只有确认它们都不是 `code/**` 组件业务代码、组件运行配置或禁提交文件时，才允许用单独中文 commit message 作为补充提交一并推送；剩余 `code/**` 变动必须保持未暂存，并在最终说明中列出为未纳入本次推送。
- 只有用户明确禁止 git 写入、没有实际变更、存在无法安全暂存的无关脏改动，或认证、网络、分支保护、远端拒绝导致无法 push 时，才可跳过提交或推送；最终说明必须写清原因、当前 commit hash 或未提交状态，以及需要人工处理的下一步。
- 完成改动后要判断是否同步更新 README、`docs/`、`.maw/`、端工程说明、模块档案、发布/运维文档或项目指令库。
- 如果没有更新模块档案、项目指令候选、`experience-index.md`、`solutions/**` 或执行经验候选，最终说明中简要写明原因；最终说明应包含 `experience_lookup`，写清是否检索经验、命中哪些经验和是否读取详情。

## 何时允许使用 `rtk proxy`

只有下面几类情况可以绕过过滤：

- 交互式工具在 `rtk` 包装下行为异常。
- 需要机器精确解析原始输出。
- 需要验证 `rtk` 是否裁剪了关键诊断信息。
- 需要执行 `rtk` 尚未支持的命令形态。

绕过过滤不等于放开输出；仍要限定范围、行数、目录和文件。

## 自检

```bash
rtk --version
rtk gain
which rtk
```
