---
doc_key: docs.modules.server.module
doc_type: module_design
stage: design
status: active
owner: planner
tags:
  - modules
  - server
entities:
  modules:
    - server
  app_keys:
    - server
project_health:
  dimensions:
    - product_module_design
  evidence_level: canonical
read_contract:
  summary: "server 端模块档案。"
  health_signal: "用于项目健康读取 server 端模块边界、接口、数据表和实现状态。"
  consumes: []
  produces: []
  ai_read_hint: "涉及 server 端边界、接口、数据模型、发布或模块归属时读取。"
---

# 模块：服务端

本档案是模板默认服务端 component 占位与填写指南。真实项目应按实际后端框架、接口、任务、数据库和部署方式更新，并继续把业务能力拆到更细的 group / leaf 模块；不要长期把整个 `server` 当成唯一业务 leaf。

## 1. 模块元信息

- module_key: server
- status: planned
- parent_module:
- owner_role: developer
- source_required: true
- related_components: server
- related_app_keys: server
- related_pm_story_refs:
- related_pm_task_refs:

## 2. 当前功能描述

- 业务目标：承载项目后端 API、业务服务、数据库访问、缓存、文件处理和后台任务等能力。
- 用户角色：终端用户、管理人员、外部系统、运维和 AI 调试节点。
- 核心场景：为 `client` 和项目实际新增前端应用提供接口；维护业务数据；暴露健康检查；执行必要的服务端任务。
- 不做范围：不维护前端页面；不保存客户仓库 `.git`；不在模块档案中记录真实密钥。

## 3. 实现程度

- 已完成：模板已提供 `code/server`、`code/server/.maw.component.yaml`、`.maw/app-runtime.yaml` 中的 `server` 调试索引、`.maw/repositories.yaml` 中的镜像仓库引用，以及 `release/server` 覆盖层。
- 部分完成：安装、启动、测试、构建命令是模板示例，需要按真实后端工程校准。
- 未开始：真实 API、数据模型、队列任务、权限规则和运维监控需要项目初始化后填写。
- 未验证：当前模板不代表任何具体业务接口已可用。
- 风险：接口、数据库和发布规则变更时，如果不同步本档案，后续 AI 会话容易读取过宽上下文或误改边界。
- 拆分提醒：本档案只表达后端 component 边界。登录注册、订单查询、支付回调、文件导入、外部同步等业务能力应拆成独立 leaf，并在 `.maw/modules.yaml` 绑定对应 API、表和测试路径。

## 4. 迭代计划

- 当前迭代：项目初始化迭代。
- 本迭代目标：确认服务端技术栈、启动命令、接口边界、数据库边界和测试方式。
- 下一迭代候选：按业务模块拆分 API、任务、模型和权限。
- 阻塞项：真实需求、数据模型、第三方服务和部署目标未确认。

## 5. 待办

> 本表只记录 server component 内部待办。若某项服务端能力被 client 或其它模块先假设已完成，必须登记到 `docs/planning/todos/active.md`，这里只回链 TODO-ID。

| TODO-ID/局部ID | 类型 | 内容 | 优先级 | 来源 | 影响模块 | 对应 Story/Task | 状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| local-server-config | config | 校准 `code/server/.maw.component.yaml` 中的安装、启动、测试、构建命令 | P1 | 模板初始化 | server |  | planned |
| local-server-api | api | 填写真实 API 路径、命令和权限边界 | P1 | 项目初始化 | server |  | planned |
| local-server-db | db | 补齐服务端读写的数据表/集合清单 | P1 | 项目初始化 | server |  | planned |

## 6. 前端页面边界

| 页面/组件 | 路径 | 职责 | 不负责 | 备注 |
| --- | --- | --- | --- | --- |
| 不适用 |  | 服务端默认不负责前端页面 | `code/client` 或项目实际新增前端应用的页面实现 | 如服务端含内置后台页面，应按项目实际记录为业务模块或页面边界 |

## 7. 后端接口边界

| 接口/命令 | 文件或目录 | 方法/函数 | 请求/响应概要 | 权限/风险 |
| --- | --- | --- | --- | --- |
| 健康检查 | `code/server` | 待项目填写 | 用于本地或测试环境可用性验证 | 不应泄露内部状态和密钥 |
| API 根路径 | `code/server` | 待项目填写 | `.maw/app-runtime.yaml` 默认记录 `/api` | 需按真实权限、鉴权和错误码补充 |

## 8. 数据表边界

| 表/集合 | 模型/迁移 | 读写职责 | 关键字段 | 风险 |
| --- | --- | --- | --- | --- |
| 待项目填写 | 待项目填写 | 待项目填写 | 待项目填写 | 数据表变更必须同步设计文档和模块档案 |

## 9. 配置与运行边界

- `.maw` 配置：`.maw/components.yaml`、`.maw/app-runtime.yaml`、`.maw/environments.yaml`、`.maw/repositories.yaml`、`.maw/releases.yaml`、`.maw/policies.yaml`；其中 `.maw/components.yaml` 通过 `release_ref` 指向发布配置。
- 客户仓库规则：`.maw/customer-repository-rules.yaml` 记录 server 客出白名单、客户仓子目录、整仓替换开关和执行前方案目录；默认不得整仓替换客户仓库。
- 组件配置：`code/server/.maw.component.yaml`、`code/server/.env.example`。
- 环境变量：真实值放入允许提交的 `.maw/secrets*.yaml` 或本机 `.maw/*.local.yaml`，不要写入本档案。
- AI 调试入口：`.maw/app-runtime.yaml` 的 `app_runtime.apps.server`。
- 仓库级镜像边界：整仓 mirror 由聚合后的仓库配置和 `ops/scripts/sync-repository-mirror.sh plan` 有效计划控制；`auto_sync_after_project_push` 默认开启，项目仓库 push 成功后先看计划再同步。
- 逻辑 key 读取边界：平台、节点脚本和 AI 提示词可通过 `ops/scripts/maw-key-get.py` 读取 `template.applied_version`、`release.component.command`、`module.dossier` 等稳定语义 key；索引定义在 `.maw-template/config-key-index.yaml`，项目只允许用声明式 `.maw/config-key-index*.yaml` 增补，不执行目标项目任意代码作为读取逻辑。
- 组件镜像仓库边界：`.maw/repositories.yaml` 的 `component_mirrors.components.server` 只允许当前项目仓库单向同步到目标仓库。
- 发布环境配置：`.maw/releases.yaml` 的 `releases.components.server` 和 `code/server/.maw.component.yaml` 的 `release`；默认发布环境为 `test`，可选环境包含 `test`、`staging`、`production`，项目可按实际追加。中文口令 `发布测试` 映射到本地调试 `local_debug`，需给可访问调试地址；`发布上线` 映射到编译包部署测试目标 `remote_staging_server`，仍属于测试，需给线上可访问地址；`发布生产`/`发布生成` 映射到 `remote_production_server`，涉及生产环境安装或版本上线必须人工审计；未指定组件时按 `.maw/environments.yaml` 对应 `remote_server.default_release_components` 判断候选范围，再按 `artifacts/release-state/<env>/server.json` 的 commit 记录和 server 相关路径差异判断是否发布 server。
- 发布版本状态：server 成功发布后应更新 `artifacts/release-state/<env>/server.json`；`发布上线` 和 `发布生产` 执行前必须确认本地候选 commit 等于发布来源远端分支。
- 发布覆盖层：`release/server/default` 和 `release/server/<app_key>`。

## 10. 任务与节点边界

- 推荐任务类型：api、db、config、release、fix、refactor、security、docs。
- 可执行节点角色：Planner、Executor、Reviewer、Release Manager。
- 是否需要源码权限：是。
- 是否需要人工审批：涉及数据库迁移、权限、支付、外部同步、生产发布和密钥时需要。
- 测试/验收要求：至少运行服务端单测、接口冒烟或健康检查；无法运行时说明原因。
- 任务完成说明：若本轮修改 `server` 或 `app_key=server` 且需要发布才会生效，必须说明“本轮修改了 server 的 <内容>，需要发布 server 才会生效，当前已发布/当前未发布”；需要发布但未发布或未验证时，必须给出可复制 `#发布：发布 server 到 <env>...` 和可用中文口令快捷指令，并在收口末尾询问是否“确认发布全部”；未命中时说明无需发布。

## 11. 文档维护规则

- 修改页面时必须更新：通常不适用；若服务端提供页面，补充本档案第 6 节。
- 修改接口时必须更新：第 7 节、`docs/design/api-design.md` 和 changelog。
- 修改数据表时必须更新：第 8 节、`docs/design/data-model.md` 和 changelog。
- 修改状态流/权限/发布规则时必须更新：第 2、7、9、10 节及 `release/rules.yaml` 或相关 `.maw` 配置说明。
- 修改仓库级镜像或组件镜像仓库目标、自动同步开关或同步方向时必须更新：第 9、10 节、`.maw/repositories.yaml`、`docs/repository-mirror-sync-guide.md`、`docs/component-mirror-repository-guide.md` 和 changelog。
- 修改源码、运行配置、发布覆盖、部署脚本或外部同步逻辑时必须在最终说明同步 `release_update_status`、`release_commands` 和 `release_confirmation_prompt`；本轮未执行并验证发布时写 `当前未发布` 或 `当前未发布/未验证`，并给出 `#发布` 指令。中文环境口令未指定组件时，先按默认组件范围和发布版本状态计算实际发布名单；收口末尾询问是否“确认发布全部”，用户回复“确认发布全部/确认/是”则发布全部待发布组件，复制单条指令则只发布对应组件。

## 12. 最近变更摘要

| 日期 | 任务/提交 | 变更摘要 | 是否更新档案 |
| --- | --- | --- | --- |
| 2026-06-29 | 发布测试/上线/生产边界强化 | 补充 `发布测试` 的本地调试地址、`发布上线` 仍属测试且需线上可访问地址、`发布生产` 生产环境安装或版本上线必须人工审计 | 是 |
| 2026-06-17 | 配置逻辑 key 索引 | 补充 `maw-key-get.py` 和 `.maw-template/config-key-index.yaml` 作为平台/节点/AI 读取稳定语义事实的工具链边界 | 是 |
| 2026-06-16 | 待办任务治理 | 区分模块内部待办与 `docs/planning/todos/active.md` 跨模块被依赖待办，模块档案只回链 TODO-ID | 是 |
| 2026-06-16 | 发布版本状态与最新代码门 | 补充 server 按 `artifacts/release-state/<env>/server.json` 记录已发布 commit、按组件路径差异筛选发布名单，以及上线/生产必须校验本地候选 commit 等于发布来源远端分支 | 是 |
| 2026-06-15 | 中文发布口令与默认组件范围 | 补充 `发布测试`、`发布上线`、`发布生产`/`发布生成` 口令和默认发布范围；基础映射为 `发布测试` 本地调试、`发布上线` 部署到 `remote_staging_server`、`发布生产` 部署到 `remote_production_server` | 是 |
| 2026-06-14 | 中文人类优先收口规则同步 | 将发布确认文案同步为“确认发布全部”，与 TINST-020 中文收口规则保持一致 | 是 |
| 2026-06-13 | 仓库级镜像与发布收口优化 | 补充 repository_mirrors 自动同步开关，并将发布收口改为“需要发布才会生效/是否全部发布”语义 | 是 |
| 2026-06-12 | 客户仓库规则治理 | 补充 server 客户仓库白名单客出、执行前方案和多通道 git 凭证配置边界 | 是 |
| 2026-06-12 | 发布配置环境选项 | 补充 server 默认发布环境、可选环境和快捷发布指令配置边界 | 是 |
| 2026-06-12 | 发布快捷指令收口规则 | 补充 server 需要发布但未发布时的 `#发布` 快捷指令和确认后执行发布要求 | 是 |
| 2026-06-12 | 最终说明发布状态约束 | 补充 server 命中与发布状态最终说明要求 | 是 |
| 2026-06-12 | 组件镜像仓库协议 | 补充 server 镜像仓库单向同步边界和配置引用 | 是 |
| 2026-05-20 | 模板模块档案协议初始化 | 新增服务端模块档案样例 | 是 |
