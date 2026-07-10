# 指令：安装项目环境

## 元信息

- ID：TINST-035
- 类型：项目指令
- 状态：启用
- 维护位置：`docs/ai-instructions/instructions/install-environment.md`
- 推荐调用：`#安装环境`
- 精确调用：`#T035`
- 触发词：#安装环境、#安装开发环境、#安装线上环境、#安装生产环境、安装环境、安装开发环境、安装本地环境、修复本地环境、安装线上环境、安装生产环境、配置开发环境、配置线上环境、配置生产环境、本地开发环境、本地测试环境
- 适用范围：用户要求在本机、测试/预发/线上或生产目标上安装、补齐、修复或开启项目运行环境；也适用于任务收口提示“本机未配置好开发环境”后，用户确认继续安装。

## 目标

让 AI/Codex 在安装或改造任何项目环境前，先确认目标环境、只读探测现状、展示安装方案和风险，再经用户确认后执行安装、启动、验证和入口回报。Docker-first 是默认建议，但不是硬性要求；项目已有环境、用户指定方案和客户/生产事实优先。

## 环境口径

- 开发环境：当前宿主机/本机的本地开发调试环境；发布测试/本地测试默认同属本地调试模式，通常需要自主完成目标组件环境安装、程序部署或启动，并提供可访问调试地址，改动应尽量即改即生效。
- 线上环境：线上发布本质是编译后的测试/联调环境，对应 `staging` / `remote_staging_server`；发布上线通常在线上服务器完成目标组件环境安装、编译后程序部署，并提供线上可访问地址，用于模拟发布生产的程序包部署测试，部署包、服务编排、目录、健康检查、备份和回滚口径应与发布生产对齐，但不等同于 `production`。
- 生产环境：正式生产环境，对应 `production` / `remote_production_server`；生产服务器程序部署、生产环境安装和生产版本上线必须经过人工审计。
- 测试环境：默认指本地调试模式；如果语境是“线上发布后的测试/验收”，按 `staging` / `remote_staging_server` 处理。旧项目或脚本需要 `remote_test_server` 且配置缺失时，从 `remote_staging_server` 读取同名字段；显式独立远端测试机以项目事实为准。
- 测试环境数据库：本地环境和线上测试环境本质都属于测试，一个是本地调试，一个是预生产部署测试。生成安装测试环境方案时，默认保持数据库与线上测试环境一致；只有配置文件中显式配置了 `remote_test_server` 的数据库时，才使用该独立测试数据库。若方案复用线上测试数据库，必须在方案中给出警告，说明这是共用测试/联调库、可能影响预生产验收数据，并要求确认备份与回滚。
- 测试环境启动命令：种子仓库默认提供根目录 `package.json` 作为本地测试启动命令面板。触发安装测试环境、安装开发环境、安装本地环境或修复本地环境时，必须把最终确认的测试环境启动命令增量合并到根 `package.json` 的 `scripts` 中，并以 `npm run dev` 作为验收入口：执行该命令应能一键启动或重启本地开发环境，并输出本机 `127.0.0.1` 访问链接和局域网访问链接；可参考 MAW 主仓模式让 `dev` 转发到稳定底层入口 `local:dev`，`test:dev`、`local:test` 作为兼容别名。真实命令仍以 `code/<app_key>/.maw.component.yaml`、端工程 `package.json`、`ops/scripts`、Makefile 或 Docker Compose 为来源。项目内可单独运行的 `ops/scripts` 也应注册为根 npm scripts，并在 `mawScriptDescriptions` 中写明用途和风险；`npm run scripts:help` 应能列出说明。新增脚本后先运行 `npm run scripts:sync:check`，需要自动补齐时运行 `npm run scripts:sync:write`。

## 输入要求

- 必需输入：目标环境口径，至少能唯一映射到开发环境、线上环境或生产环境之一。
- 推荐输入：目标 app_key、是否允许 Docker、是否允许使用现有数据库、端口偏好、是否需要远端服务器、是否有备份/回滚要求。
- 可选输入：本机/远端路径、域名、健康检查 URL、测试账号引用、安装窗口、审批人。
- 缺失时处理：
  - 用户只说“安装环境”且不能从上下文唯一判断环境时，先询问要安装开发、线上还是生产环境。
  - 缺少敏感参数时，先在 `.local/` 创建本机填写文件或要求使用既有 secret 引用，不让用户在对话里粘贴明文。
  - 目标环境涉及线上或生产、数据库改指向、删卷、重建、停服务、替换运行时或迁移数据时，必须先输出方案并等待用户确认。

## 执行步骤

1. 读取 `.maw/codex-context.md`、`docs/ai-instructions/experience-index.md`、`.maw/environments.yaml`、`.maw/app-runtime.yaml`、`.maw/components.yaml`、`.maw/releases.yaml`、`.maw/policies.yaml`、相关 `code/<app_key>/.maw.component.yaml` 和 `docs/implementation/host-runtime-environments/README.md`。
2. 解析目标环境：
   - `安装开发环境`、`安装本地环境`、`修复本地环境` 都映射到本机开发/本地测试环境，优先读取 `app_runtime.apps.<app_key>.local_url`、组件本地启动命令和本机 local 覆盖；发布测试需要能安装或开启目标组件本地环境、部署或启动程序，并输出可访问调试地址。
   - `安装线上环境` 映射到 `staging` / `remote_staging_server`，按线上服务器上的编译包部署测试处理，必须确认服务器、分支、工作目录、健康检查、可访问 URL、备份/回滚，以及与生产对齐的部署包和运行环境。
   - `安装生产环境` 映射到 `production` / `remote_production_server`，必须确认人工审计结论、生产审批、备份、回滚、发布窗口、健康检查和数据风险。
   - 目标为测试环境或本地测试入口时，数据库默认沿用线上测试环境数据库；仅当 `.maw/environments*.yaml` 或 `.maw/secrets*.yaml` 显式存在 `remote_test_server.database` / `environments.test.remote_server.database` 时，才把它作为独立测试数据库。
3. 环境确认只读探测：
   - 探测 Docker Engine / Docker Compose、systemd、PM2、宝塔/面板、裸进程、语言运行时、包管理器和端口占用。
   - 探测已有数据库类型、连接引用、数据目录、备份目录、是否与测试/线上/生产共库。
   - 探测已有工作目录、反向代理、域名、日志目录、发布状态和健康检查入口。
   - 不读取或输出真实密码、token、私钥、生产连接串和客户隐私。
4. 展示安装方案：
   - 列出复用现有能力：例如本机 Docker、已有数据库、已有 Node/Python/Java/PHP、已有端口和已有服务。
   - 列出需要安装或补齐的能力：例如 Docker、Compose、数据库、Redis、语言运行时、依赖包、反向代理配置。
   - 列出推荐运行方式：继续既有环境、补 Docker、部分服务容器化、迁移到 Docker，或保持数据库共用。
   - 列出数据库选择：说明使用线上测试数据库还是显式独立测试数据库；若复用线上测试数据库，必须突出警告“本测试环境将与线上测试/预生产共用数据库”，并列出可能影响的数据、备份和回滚确认项。
   - 列出根目录 `package.json` 启动入口计划：说明将新增或合并哪些 npm scripts，例如 `dev`、`local:dev`、`test:dev`、`local:test`、`client:dev`、`server:start`、`server:restart`，并说明 `npm run dev` 如何启动/重启本地环境、输出哪些本机与局域网调试地址，以及它们转发到哪些真实组件命令或 `ops/scripts`。
   - 列出风险与确认项：安装软件、启动/停止服务、改端口、改数据库连接、执行迁移、替换数据库引擎、删除或重建卷、清空状态；生产环境安装或生产版本上线必须列出人工审计结论。
5. 等待用户确认。只有开发环境中完全无破坏、无系统安装、无远端写入且项目已明确允许自动启动时，才可直接启动或刷新本地 dev server；其它安装、迁移、线上/生产写入必须确认。
6. 执行安装或启动：
   - 优先使用目标项目已有脚本、组件 `.maw.component.yaml` 命令、Docker compose 文件和 release/ops 说明。
   - 安装测试环境时，新增或合并根目录 `package.json` 的本地测试启动 scripts：保留已有 scripts，不覆盖用户自定义命令；新增或修正 `dev` 只做入口转发和调试地址输出，不把真实业务配置迁出 `code/<app_key>`；`local:dev`、`test:dev`、`local:test` 作为兼容别名；不得写入本机私有 PATH、token、密码、生产连接串或客户隐私。同步检查、提取、发布计划、交付 dry-run、mirror plan、客户仓 plan 等可单独运行脚本时，也要补 `mawScriptDescriptions` 注释；高风险脚本默认保留 plan/dry-run/`--execute` 或人工确认门槛。
   - 如果目标项目不是 Node/前端项目，也仍可使用根 `package.json` 聚合 `ops/scripts`、Docker Compose、Makefile、Maven、Go、Python 或 PHP 启动命令；若本机无法使用 Node/npm，则在安装方案中说明原因并保留等价 `ops/`、Makefile 或 Compose 入口。
   - 新建 Docker 资源使用 `maw_<project_key>_<environment>`、`maw-<project_key>-<service>-<environment>`、`maw_<project_key>_<environment>_net`、`maw_<project_key>_<service>_<purpose>_<environment>` 推荐命名。
   - 保留已有 Docker project、container、network、volume、端口、数据库和非 Docker 运行方式，除非用户确认变更。
7. 验证并回报入口：
   - 开发环境给出本地 URL、健康检查、关键页面/API、dev server 状态和需要用户打开的入口。
   - 线上环境给出 staging URL/healthcheck、部署目录、服务状态和验证结果。
   - 生产环境给出生产 healthcheck、服务状态、当前版本、回滚方式和监控/日志入口引用。
8. 沉淀本机差异：
   - 本机端口、路径、代理、浏览器 profile、工具安装差异写入 `.local/ai/`、`.local/config/` 或 `.local/maintenance/`。
   - 可共享的抽象经验再按项目记忆/经验规则进入 `docs/ai-instructions/`，不得写入真实密钥或不可外传信息。

## 验证方式

- 已说明目标环境是开发、线上还是生产，且口径无歧义。
- 已完成只读环境确认，或说明无法确认的项目和原因。
- 已展示安装方案，区分复用现有、Docker 安装、本机安装、远端安装和不建议改动的内容。
- 安装测试环境方案已明确数据库来源；复用线上测试数据库时已给出警告、影响范围、备份和回滚确认项。
- 安装测试环境已新增或合并根目录 `package.json` 启动脚本，且 `npm run dev` 可作为一键本地开发/调试入口，执行后能输出本机 `127.0.0.1` 访问链接和局域网访问链接；如无法使用 npm 入口，说明等价替代入口和派生项目后续应如何实现 `dev`。
- 高风险动作已获得用户确认后才执行。
- 安装或启动后已给出入口 URL、健康检查、关键命令和验证结果；本地/发布测试给出调试地址，线上/发布上线给出线上可访问地址，生产给出人工审计与审批状态。
- 本机差异已写入 `.local/` 或说明无需更新。

## 禁区

- 不得在未确认环境口径时安装或写远端。
- 不得把“线上环境”自动等同于生产环境。
- 不得把 Docker-first 解释为必须安装 Docker 或必须迁移已有生产环境。
- 不得在未确认前删除 volume、改端口、停共享服务、替换数据库、清空同步状态或执行生产迁移。
- 不得把真实密钥、账号密码、生产连接串、客户隐私、未脱敏日志或离线镜像 blob 写入可提交文件。
- 不得把本机私有 PATH、绝对路径、代理、token 或一次性排障命令写入根 `package.json`；这些内容只写 `.local/` 或本机配置。
- 不得把模板仓库协议误写成 MAW 主仓 Host Manager、安装器或生产运维运行时代码。

## 冲突与覆盖规则

- 用户最新明确要求和目标项目真实配置优先。
- `code/<app_key>` 内部工程配置和组件 `.maw.component.yaml` 优先于 `.maw/app-runtime.yaml` 调试索引；冲突时按 code 事实修正 `.maw` 索引。
- 根目录 `package.json` 是本地测试命令面板，不是业务配置权威来源；与组件命令冲突时，以组件配置和端工程事实为准，并同步修正根 scripts。
- 线上/生产环境安装和发布规则冲突时，采用更保守的发布/运维确认规则。
- 与宿主机用途、仓库身份、MCP、密钥和客户交付边界冲突时，先按高风险路径人工确认。

## 更新记录

- 2026-06-24：补充安装测试环境时必须把本地测试启动命令落实到根目录 `package.json`，作为默认 npm 启动入口和命令面板。
- 2026-06-25：统一“安装本地环境、修复本地环境”为安装开发环境口径；把 `npm run dev` 升级为本地环境安装验收入口，并要求输出 127.0.0.1 与局域网访问链接。
- 2026-06-23：统一安装测试环境数据库口径：默认沿用线上测试环境数据库，除非显式配置 `remote_test_server` 数据库；复用线上测试数据库时方案必须警告。
- 2026-06-22：创建，补充开发环境、线上环境、生产环境安装口径和环境确认优先规则。
