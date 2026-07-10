# 指令：发布组件应用并执行上线操作

## 元信息

- ID：TINST-014
- 类型：项目指令
- 状态：启用
- 维护位置：`docs/ai-instructions/instructions/release-component.md`
- 推荐调用：`#发布`
- 精确调用：`#T014`
- 触发词：#发布、#立即发布、#发布生效、发布组件、更新发布、立即发布生效、执行发布、执行SQL、执行 sql、上线、部署、发布测试、发布上线、发布生产、发布生成、发布 server、发布 client
- 适用范围：用户明确要求发布某个 `code/<app_key>` 组件应用，或使用 `发布测试`、`发布上线`、`发布生产`/`发布生成` 这类环境口令发布默认候选范围内、经版本状态筛选后的组件，或 AI 最终说明中判断某组件“需要发布才会生效，当前未发布/未验证”后，用户确认立即发布生效。多个组件需要发布时，用户复制某条或多条 `#发布` 指令则只发布对应 app_key；如果收口已询问“是否全部发布”，用户回复“是/确认/全部发布”则发布全部待发布组件。用户说“发布公开镜像/发布开源镜像/私有仓发布到公开仓”时，不走本指令，改走 `TINST-039`。

## 目标

当用户确认发布时，AI 应按目标项目的发布配置和端工程命令执行完整发布链路，包括必要的 SQL/数据库迁移、构建、发布覆盖层、部署、健康检查、发布记录和回滚信息。该指令用于把已经完成并验证的代码/配置变更发布到指定环境，不用于普通开发实现。

## 输入要求

- 必需输入：`app_key`、组件名，或可唯一映射环境的中文发布口令。`发布测试` 对应本地调试 `local_debug`，通常基于本地环境自主完成目标组件环境安装、程序部署或启动，并提供可访问调试地址，默认不部署远端编译包；`发布上线` 对应 `staging` 和 `remote_staging_server`，通常在线上服务器完成目标组件环境安装、编译后程序部署，并提供线上可访问地址，它仍属于测试，是模拟发布生产的程序包部署测试；`发布生产` 对应 `production` 和 `remote_production_server`，是在生产服务器下进行程序部署，涉及生产环境安装、生产版本上线或客户正式服务变更时必须人工审计；`发布生成` 作为 `发布生产` 的兼容误写处理。目标环境可显式指定；未指定时使用配置中的默认发布环境。
- 推荐输入：发布范围、commit hash、是否包含 SQL/迁移、SQL 文件或迁移命令、回滚要求、验证 URL 或健康检查命令。没有显式 commit 时，候选版本默认使用本地 `HEAD` 的 commit SHA；如果 `发布测试` 或 `发布上线` 时工作区存在未提交改动，发布计划和状态记录还必须记录 dirty 文件列表和 dirty snapshot 标识。
- 可选输入：是否跳过构建、是否仅发布静态资源、发布时间窗口、审批人。
- 缺失时处理：
  - 如果缺少 `app_key`，但用户使用了 `发布测试`、`发布上线`、`发布生产` 或 `发布生成`，先读取聚合后的 `.maw/releases.yaml` 中 `releases.defaults.release_command_aliases`，确定环境和执行目标，再读取聚合后的 `.maw/environments.yaml` 中对应 `environments.<env>.remote_server.default_release_components` 得到候选范围；随后读取 `releases.defaults.version_tracking`，用 `ops/scripts/plan-release-components.py <口令>` 或等价流程按各组件已发布 commit 与本地候选 commit 的组件路径差异筛选实际发布名单。该字段为空、组件不存在、状态记录冲突或范围有歧义时，先向用户确认。
  - 如果缺少 `app_key` 且没有命中中文发布口令默认范围，先向用户确认，不要猜测发布组件。
  - 如果缺少目标环境，先读取聚合后的 `.maw/releases.yaml` 和 `code/<app_key>/.maw.component.yaml`；存在 `release.default_environment` 或 `releases.defaults.default_environment` 时，按默认环境执行并在发布计划中写明“默认发布环境”。配置没有默认环境时，先向用户确认。
  - 如果最终说明已经给出完整 `release_commands` 和 `release_confirmation_prompt`，且用户回复“确认发布全部”“确认”“是”“全部发布”“立即发布”“发布生效”或复制 `#发布` 指令，视为发布确认；目标、环境、SQL 范围已经明确时，直接执行本指令。
  - 如果 `release_confirmation_prompt` 已询问是否“确认发布全部”并列出多个 app_key，用户回复“确认发布全部/确认/是”即表示发布全部待发布组件；用户复制其中一条或多条 `#发布` 指令，就是选择部分发布，只发布对应 app_key。只有收口没有列明待发布组件或发布指令不完整时，才先补问范围。
  - 如果命中生产环境、数据库结构变更、权限/支付/隐私或不可逆 SQL，仍必须执行发布前检查、备份/回滚确认和项目要求的审批记录；若项目信息缺失，先补问唯一缺口。

## 执行步骤

1. 读取 `.maw/codex-context.md`、`docs/ai-instructions/experience-index.md`、`.maw/releases.yaml`、`.maw/environments.yaml`、`.maw/policies.yaml`、`.maw/secrets.yaml`、`release/rules.yaml`、对应 `code/<app_key>/.maw.component.yaml`、相关模块档案和本指令。
2. 解析发布配置：
   - 读取 `releases.defaults.default_environment`、`releases.defaults.environment_options`、`releases.components.<app_key>.default_environment`、`releases.components.<app_key>.environment_options`、`releases.components.<app_key>.release_commands`。
   - 读取 `releases.defaults.release_command_aliases`，把 `发布测试` 映射到 `test/local_debug`，把 `发布上线` 映射到 `staging/remote_staging_server`，把 `发布生产`/`发布生成` 映射到 `production/remote_production_server`；`发布测试` 和 `发布上线` 都属于测试，前者是本地调试版本，后者是线上服务器上的编译包部署测试，不是生产发布。
   - 如果用户没有指定组件，读取 `.maw/environments.yaml` 聚合结果中 `environments.<env>.remote_server.default_release_components`；该字段是逗号分隔 app_key 字符串，也可兼容目标项目已有的数组写法。发布前必须校验每个 app_key 在 `.maw/components.yaml` 和 `.maw/releases.yaml` 中存在。
   - 读取 `code/<app_key>/.maw.component.yaml` 的 `release.default_environment`、`release.environment_options` 和 `release.commands`。
   - 如果 `.maw/environments.yaml` 聚合结果中存在 `environments.<env>.remote_server.deployment`，把它视作目标环境部署传输方式；`transport: ftp/ftps` 且 `strategy: full_overwrite/managed_sync` 时可使用 `ops/scripts/deploy-via-ftp.py`，但仍必须先完成组件发布名单、构建、脱敏、备份/回滚和确认门。
   - 组件配置优先于全局默认；组件没有配置时再使用全局默认；两者都没有时不得自行猜测环境。
   - 每个启用的 code 组件都应有默认发布指令、按环境发布指令和中文环境口令指令，至少覆盖 test、staging 与 production；项目有 uat、demo、customer 等其它环境时按配置追加。
3. 计算发布名单和版本状态：
   - 读取 `releases.defaults.version_tracking`；模板默认使用 `git_commit` 作为版本标识，状态文件为 `artifacts/release-state/<env>/<app_key>.json`。
   - 优先运行 `python3 ops/scripts/plan-release-components.py <发布口令或环境>`；若目标项目没有该脚本，按等价流程读取每个候选 app_key 的状态文件，比较 `version_id` 与候选 commit。
   - 判断逻辑：状态文件缺失时纳入发布名单；状态 commit 等于候选 commit 时跳过；状态 commit 是候选 commit 的祖先时，只在 `code/<app_key>`、组件 `.maw.component.yaml`、发布覆盖层、`.maw/releases.yaml`、`.maw/environments.yaml` 或 `release/rules.yaml` 等发布相关路径有变化时纳入；状态 commit 比候选 commit 更新或双方分叉时阻塞并要求人工确认。
   - 发布成功后必须更新对应状态文件，至少记录 `environment`、`app_key`、`version_id`、`version_id_type: git_commit`、`source_branch`、`released_at`、`release_record` 和验证结果；不得把服务器密码、token、私钥、生产连接串、客户隐私或未脱敏日志写入状态文件。
4. 确认当前工作区和待发布提交：
   - 发布源默认是当前项目工作目录；固定 clone 或发布工作副本只用于复用依赖、缓存和部署目录，不替代用户当前工作区的发布意图。
   - `发布测试` 和 `发布上线` 都属于测试版本，允许未提交改动参与发布；发布计划和发布状态必须记录 `base commit`、dirty 文件列表、dirty snapshot 标识和验证结果，不能把测试快照伪装成完全可复现的 clean commit。
   - `发布测试` 不强制本地代码与远端分支完全一致，也不默认部署远端编译包；应安装或开启目标组件本地环境，部署或启动程序，刷新或确认本地调试入口，提供可访问调试地址，并记录候选 commit、dirty 状态和本地验证状态。
   - `发布上线` 是线上服务器上的编译包部署测试；允许发布当前工作区快照，包括未提交改动，但必须在发布记录中写明它是测试快照，并提供线上可访问地址和回滚方式。
   - `发布生产` 必须先执行最新代码和干净工作区检查：按 `environments.<env>.remote_server.branch`（默认 `main`）fetch 对应远端分支，并确认本地候选 commit 等于 `origin/<branch>` 或项目明确配置的发布来源 ref；若本地落后、超前、无法解析远端 ref、工作区有未提交改动或提交未推送，阻塞发布。
   - `发布生产` 涉及生产环境安装、生产服务器部署、生产版本上线、数据库结构变更、客户正式服务流量或不可逆变更时，必须先完成人工审计和审批记录；缺少人工审计结论时不得继续执行真实生产写入。
5. 根据项目配置确定发布链路：
   - 构建、测试、打包命令以 `code/<app_key>/.maw.component.yaml` 和端工程自身脚本为准。
   - 发布目标以 `.maw/releases.yaml`、`.maw/environments.yaml`、组件配置和项目发布脚本为准。
   - 发布覆盖层按 `release/rules.yaml` 先叠加 `release/<component>/default`，再叠加 `release/<component>/<app_key>`。
6. 检查是否包含 SQL 或迁移：
   - 若存在 `migrations`、`sql`、`database`、`schema`、`db` 相关变更，纳入发布计划。
   - 执行 SQL/迁移前确认目标环境、备份或回滚方案；项目有 dry-run、备份、事务或迁移工具时优先使用。
   - 不得把未确认环境的 SQL 执行到生产或错误数据库。
7. 执行发布前验证：
   - 运行测试、构建、lint、脱敏检查或项目发布前检查。
   - 检查发布覆盖层 forbidden 规则和敏感信息。
   - 如果本次还要向客户或外部渠道交付 `code/`，先运行 `ops/scripts/check-code-deliverable.sh`；需要生成 code-only 包时先运行 `ops/scripts/export-code-only.sh --dry-run`。
8. 执行发布：
   - 按项目约定顺序执行 SQL/迁移、构建、打包、发布覆盖、部署和服务重启/刷新。
   - 若目标环境配置 `deployment.transport: ftp` 或 `ftps`，先运行 `python3 ops/scripts/deploy-via-ftp.py --environment <env> --app-key <app_key> --format json` 查看计划；只有计划、保留路径、远端目录和回滚方式确认后，才追加 `--execute` 执行覆盖上传。
   - FTP 覆盖部署默认只覆盖同路径文件，不删除远端未管理文件；只有用户明确确认且配置 `delete_unmanaged: true` 或命令行 `--delete-unmanaged` 时，才允许删除未管理文件，并必须保留 `preserve_paths`。
   - 如果项目要求先发布应用再执行兼容 SQL，按项目发布说明执行；不确定时采用更保守顺序并说明。
9. 发布后验证：
   - 运行健康检查、关键接口/页面冒烟、数据库版本或迁移状态检查。
   - 确认目标环境包含本次 commit 或构建产物。
10. 记录发布结果：
   - 按 `.maw/releases.yaml` 的 `record_dir` 或项目约定写入发布记录。
   - 记录发布时间、app_key、环境、commit、SQL/迁移、验证、回滚方式和异常。
   - 同步更新 `artifacts/release-state/<env>/<app_key>.json` 或配置中的等价状态文件；如果使用脚本，可在真实发布成功后运行 `python3 ops/scripts/plan-release-components.py <口令> --record-success --record-path <发布记录路径>`。
11. 沉淀派生项目本机发布经验：
   - 派生自本种子仓库的项目，发布、回滚、健康检查或排障后，应把本机/本环境相关经验写入 `.local/ai/` 或 `.local/maintenance/` 下的被忽略文件，例如 `.local/ai/release-experience-<env>.md`。
   - 记录内容包括口令映射、默认组件范围、服务器差异、健康检查路径、常见失败症状、验证命令和下次避免重复踩坑的处理步骤。
   - 不得把真实密钥、token、密码、私钥、生产连接串、客户隐私或未脱敏日志写入可提交文件；如需长期共享，先脱敏后再抽象到 `docs/ai-instructions/`。
   - 最终说明的 `local_update` 必须写明是否已更新 `.local` 发布经验；如未更新，说明原因。
12. 如果发布过程失败：
   - 停止后续高风险步骤。
   - 说明已执行到哪一步、是否需要回滚、已执行的 SQL/迁移、当前环境状态和下一步。

## 验证方式

- 发布前验证、构建或项目发布前检查已完成，或说明无法执行的原因。
- 已写明实际使用的发布环境；未显式指定环境时，说明来自配置默认环境。
- 使用 `发布测试`、`发布上线`、`发布生产` 或 `发布生成` 且未指定组件时，已写明候选组件范围来自 `environments.<env>.remote_server.default_release_components`，并说明版本状态筛选后的实际发布名单；其中 `发布测试` 的目标是本地环境中的调试版本和可访问调试地址，`发布上线` 是线上服务器上的编译包部署测试并需要给出线上可访问地址。
- 已基于发布版本状态计算实际发布名单：写明每个候选 app_key 的状态文件、已发布 commit、候选 commit、纳入/跳过/阻塞原因；状态缺失时说明按首次发布纳入。
- `发布生产` 已完成本地最新代码和干净工作区检查：fetch 发布来源分支，并确认候选 commit 等于 `origin/<remote_server.branch>` 或项目配置的发布来源 ref，且工作区没有未提交改动；`发布测试` 和 `发布上线` 可说明该检查不强制。
- 如果 `发布测试` 或 `发布上线` 使用了未提交改动，发布记录和 `artifacts/release-state/<env>/<app_key>.json` 或等价状态必须写明 `dirty_worktree: true`、dirty 文件列表和 dirty snapshot 标识。
- `发布生产` 已写明人工审计、审批、备份、回滚、停机影响评估和生产健康检查结果；未完成时阻塞生产发布。
- SQL/迁移状态已验证；若无 SQL/迁移，明确写“无 SQL/迁移”。
- 目标环境健康检查或冒烟验证已完成。
- 发布记录已写入或说明目标项目没有发布记录目录。
- 使用 FTP/FTPS 部署时，发布记录和最终说明只写脱敏目标、上传数量、删除数量、健康检查和回滚信息，不写 FTP 密码或未脱敏 URL。
- `artifacts/release-state/<env>/<app_key>.json` 或等价状态文件已更新为本次成功发布的 git commit；如果目标项目没有采用版本状态文件，必须说明等价记录位置。
- 派生项目本机发布经验已写入 `.local/`，或已说明本次没有新增可沉淀的本机发布经验。
- 最终说明中对应组件写明“本轮修改了 <app_key> 的 <内容>，需要发布 <app_key> 才会生效，当前已发布”，并列出发布命令、SQL/迁移执行结果和验证结果；如果本轮只发布了多个待发布组件中的一部分，未选中的组件仍写“当前未发布/未验证”，并保留对应可复制 `#发布` 指令。

## 禁区

- 不得在 app_key、默认发布组件范围、目标环境或数据库目标不明确时执行发布。
- 不得绕过 `.maw/releases.yaml` 和 `code/<app_key>/.maw.component.yaml` 中的默认环境、环境选项和发布指令配置。
- 不得在未确认用户发布意图时，把“需要发布”的提示自动升级为真实发布；用户确认后才执行。
- 不得跳过 SQL/迁移风险检查、备份/回滚说明和脱敏检查。
- 不得把 `.local` 本机配置、真实密钥、未脱敏日志或裸 `.env` 打进发布包。
- 不得把派生项目发布踩坑经验只留在对话里；涉及本机或环境差异时应沉淀到 `.local/`，但不得提交真实内容。
- 不得跳过 code-only 交付检查，把依赖目录、构建产物、AI 过程文件或组件外本机资料交付给客户。
- 不得把“已构建”误写成“已发布”；只有目标环境验证通过后才写“当前已发布”。
- 不得在 `发布生产` 时跳过本地最新代码和干净工作区检查；本地候选 commit 不等于发布来源远端分支、工作区有未提交改动、提交未推送或远端 ref 无法确认时必须阻塞。
- 不得把 `发布测试` 或 `发布上线` 的 dirty 工作区测试快照记录成普通 clean commit 发布；测试环境允许未提交改动，但状态和收口必须如实标记。
- 不得把 `发布上线` 写成生产发布；它是线上服务器上的编译包部署测试。不得在缺少人工审计时执行生产环境安装、生产版本上线或真实生产服务器写入。
- 不得只用仓库 HEAD 粗暴判断所有组件都需要发布；应优先按组件源码、组件配置和发布覆盖层等路径差异计算发布名单。
- 不得把发布版本状态文件写成凭证、日志或服务器事实仓库；状态文件只记录最小版本事实和验证摘要。

## 冲突与覆盖规则

- 用户最新明确要求优先。
- 目标项目发布脚本、端工程 `.maw.component.yaml` 和 `.maw/releases.yaml` 优先于模板默认说明。
- 与模块档案规则冲突时，发布完成后仍必须更新受影响模块档案或说明不更新原因。
- 与经验索引命中项冲突时，以当前项目事实和用户最新确认优先，并记录待更新经验。

## 更新记录

- 2026-06-12：创建，补充发布快捷指令和“确认后直接发布生效”的执行协议。
- 2026-06-15：补充 `发布测试`、`发布上线`、`发布生产`/`发布生成` 中文口令、`remote_*_server` 映射和默认发布组件范围规则。
- 2026-06-15：补充派生项目发布经验沉淀到 `.local/` 的约束，避免重复踩坑。
- 2026-06-16：补充发布版本状态、按组件路径差异计算发布名单，以及发布环境本地最新代码门。
- 2026-06-23：统一本地测试、线上发布和远端测试回退口径：`发布测试` 等同本地调试，`发布上线` 是编译包部署到 `remote_staging_server`，`发布生产` 部署到 `remote_production_server`。
- 2026-06-29：强化发布测试、发布上线、发布生产边界：发布测试需给本地调试地址，发布上线仍属测试且需给线上可访问地址，发布生产涉及环境安装或版本上线必须人工审计。
- 2026-07-08：统一 dirty 工作区口径：发布测试和发布上线都属于测试版本，允许未提交改动参与发布并记录 dirty snapshot；发布生产才因未提交改动阻塞。
