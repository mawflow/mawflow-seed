@RTK.md

# AGENTS.md

本文件是 Codex、CLI Agent 和其它自动化协作者进入本仓库时的轻量入口。通用 AI 工作目录入口以 `AI_START_HERE.md` 和 `.maw/agent-entry.yaml` 为准；详细规则以 `RTK.md`、`.maw/codex-context.md`、`.maw/agent-briefing.md`、`docs/ai-instructions/README.md` 和任务命中的具体指令为准。

## Startup Context

开始任何开发、配置、文档、脚本或模板协议任务前，先按需读取：

1. `AI_START_HERE.md`
2. `.maw/agent-entry.yaml`
3. `.maw/codex-context.md`
4. `.maw/agent-briefing.md`
5. `.maw/project.yaml`
6. `.maw/components.yaml`
7. `.maw/modules.yaml`
8. `.maw/app-runtime.yaml`
9. `.maw/policies.yaml`
10. `docs/README.md`
11. `docs/ai-instructions/README.md`
12. 与当前任务直接相关的 README、指令或脚本说明

只有模板维护、来源升级、能力地图、项目信号或仓库身份任务才继续读取 `.maw/upgrade-policy.yaml`、`.maw/template-source.yaml`、`.maw/capabilities.yaml`、`.maw/project-signals.yaml` 和 `.maw/repository-identity.yaml`。公开 payload 不包含内部模板来源文件；缺少这些高级维护文件时按当前公开项目事实继续，不得反向读取私有来源。

不要为了建立上下文全量读取 `docs/**`、`prompts/**`、`release/**`、`artifacts/**`、`reports/**` 或 `code/**`。

## Repository Role

- 本仓库是 MAW 新项目种子模板仓库，不是已有项目整包覆盖工具。
- Mawflow Seed 的公开定位是 AI 工作目录辅助系统：给本地 AI coding tools 提供项目事实、模块边界、行为约束、任务协议、验证入口和收口方式，而不是替代 IDE、项目管理系统或云端平台。
- “种子仓库”和“模板仓库”统一指本项目仓库 `maw-project-template`；派生项目应知道自己来自本仓库，并尽量区分能力来源是种子仓库、项目自定义还是建议回流种子仓库。
- 模板默认组件口径是 `server` / `client`；派生项目已有 `admin`、`mobile`、`worker` 或其它 app_key 时，必须以目标项目事实为准。
- 同步模板能力到派生项目时，只做增量语义合并；不得覆盖目标项目 `README.md`、`code/`、真实 app_key、发布配置、仓库映射、secrets、`.local/` 或模块档案。
- 开发过程中发现适合回流到种子仓库的优化或新增能力时，最终说明必须明确指出，并记录到 `docs/seed-repository-upgrade-candidates.md`，写清使用场景、优化/新增理由和向下兼容要求。

## Commands And Routing

- 所有 `#+指令` 都按“`#` + 指令关键字”处理；没有 `#` 的习惯用语也要按候选项目指令识别。若触发词、仓库角色或执行目标有歧义，必须先向用户确认再执行。
- `#模版升级/#模板升级`：
  - 未指定 commit 时，不改变执行仓库；先按当前仓库角色路由。
  - 在源模板仓库中生成升级资产、迁移说明或派生项目提示词。
  - 在派生项目中按 `template_source.version`（默认 `main`）解析目标模板 commit，与 `template_source.applied_version` 计算模板漂移，并在当前会话执行升级提示词。
  - 不要把派生项目的模板升级误路由到 `#项目升级`。
- `#项目升级`：在目标项目按取舍矩阵同步模板能力，必须先审计目标项目事实。
- `#种子仓库升级`：在派生项目中记录可回流候选能力，并生成一段在种子仓库执行的任务提示词；在种子仓库中接收提示词后再评估并增量实现。
- `#待办任务`：记录、查询、完成或取消被当前业务闭环依赖但暂不实现、先假设已完成的跨模块待办；全局事实写入 `docs/planning/todos/active.md` 或 `closed.md`，模块档案只回链 TODO-ID。
- `#技术地图`：查询或维护公共能力、功能基类、API 快照、能力索引、项目提示信号和 AI 前置条件；公共能力写入 `.maw/capabilities.yaml`，项目提示写入 `.maw/project-signals.yaml`。
- `#仓库身份`：查询或维护仓库多角色身份、角色检测证据和差异化约束；基础事实写入 `.maw/repository-identity.yaml`，角色覆盖写入 `.maw/repository-identity.d/<role>/*.yaml`，不得只依赖配置声明值。
- `#发布测试/#发布上线/#发布生产`：发布测试通常基于本地环境，自主完成目标组件环境安装、程序部署或启动，并提供可访问调试地址；发布上线通常在线上服务器完成目标组件环境安装、编译后程序部署，并提供线上可访问地址，它仍属于测试，是模拟发布生产的程序包部署测试；发布生产是在生产服务器下进行程序部署，涉及生产环境安装、生产版本上线或客户正式服务变更时必须人工审计。
- `#跑任务包`：支持仓库内任务包目录、外部 AI 纯文本 Markdown、本机 zip、远程 zip 直链和分享页 URL；远程任务包必须先下载到临时目录、校验 zip 和任务包结构，再导入执行。
- `#交接任务`：默认生成可下载、可复制 Markdown；只有用户明确要求 zip/压缩包/可下载任务包时才生成 zip。
- `#安装开发环境/#安装线上环境/#安装生产环境`：安装或开启环境前必须先只读确认现有运行时、数据库、端口、工作目录、日志、备份和回滚条件，展示哪些复用现有、哪些用 Docker、哪些需本机或远端安装；确认后再执行。开发环境指本机/本地测试入口，本地测试默认是本地调试模式、即改即生效；线上环境指 staging/remote_staging_server，本质是编译后的测试环境，部署包和运行环境按生产发布对齐，并应提供线上可访问地址；生产环境指 production/remote_production_server，环境安装和版本上线必须有人工审计。

## Paths And Secrets

- 可提交文档、提示词、报告和最终说明中，涉及当前项目目录或文件路径时使用项目根相对路径。
- 唯一例外：模板仓库生成给目标项目执行的模板升级提示词，可以在 `本机模板仓库目录` 字段写入生成时当前模板仓库的绝对路径；目标项目只把它当作当次会话输入，不写入长期文档。
- 不提交 `.local/` 真实内容、`.maw/*.local.yaml`、真实密钥、token、账号密码、生产连接串、未脱敏日志、构建产物或用户上传文件。

## Machine-Local Notes

- `AGENTS.md` 只记录跨机器共享规则，并应与 `.maw/agent-entry.yaml` 保持一致；具体本机命令、端口、代理、浏览器 profile、工具路径和一次性排障说明不得写在本文件。
- 本机调试差异写入 `.local/config/`、`.local/ai/` 或 `.local/device.yaml` 这类被忽略的本机文件；需要给团队示例时，只提交 README 或 `*.example.yaml`。
- 当本机浏览器调试遇到 CORS、web-security 或 profile 差异时，先读取 `.local/config/` 的本机说明再执行，不要把具体机器命令复制回共享文档、提示词或默认 `.maw` 配置。

## Validation And Git

- Shell 命令默认使用 `rtk`；需要原始机器输出时使用 `rtk proxy`，并限制路径和输出行数。
- 修改模板协议、指令、任务包或检查脚本后，优先运行：
  - `git diff --check`
  - `bash ops/scripts/check-template-module-docs.sh`
  - `bash ops/scripts/check-todo-governance.sh`
  - `bash ops/scripts/check-technical-map.sh`
  - `bash ops/scripts/check-repository-identity.sh`
  - `bash ops/scripts/check-host-purpose-mcp-alignment.sh`
  - `bash ops/scripts/check-host-runtime-environment.sh`
  - `bash ops/scripts/check-seed-distribution-readiness.sh`（准备定版或正式分发前）
  - `bash ops/scripts/check-ai-framework-consistency.sh`
  - `bash ops/scripts/check-local-boundary.sh`
- 产生实际改动后，按仓库规则提交并推送当前分支；推送成功后运行 `ops/scripts/sync-repository-mirror.sh plan`，按有效计划决定是否执行 `ops/scripts/sync-repository-mirror.sh push --execute`。
