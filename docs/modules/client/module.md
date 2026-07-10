---
doc_key: docs.modules.client.module
doc_type: module_design
stage: design
status: active
owner: planner
tags:
  - modules
  - client
entities:
  modules:
    - client
  app_keys:
    - client
project_health:
  dimensions:
    - product_module_design
  evidence_level: canonical
read_contract:
  summary: "client 端模块档案。"
  health_signal: "用于项目健康读取 client 端模块边界、页面、接口和实现状态。"
  consumes: []
  produces: []
  ai_read_hint: "涉及 client 端边界、页面、接口、发布或模块归属时读取。"
---

# 模块：用户端前端

本档案是模板默认用户端前端 component 占位与填写指南。真实项目应按实际页面、路由、状态管理、接口调用和构建方式更新，并继续把用户侧业务能力拆到更细的 group / leaf 模块；不要长期把整个 `client` 当成唯一业务 leaf。

## 1. 模块元信息

- module_key: client
- status: planned
- parent_module:
- owner_role: developer
- source_required: true
- related_components: client
- related_app_keys: client
- related_pm_story_refs:
- related_pm_task_refs:

## 2. 当前功能描述

- 业务目标：承载面向最终用户的前端、移动端或 H5 交互入口。
- 用户角色：终端用户、访客、已登录用户、客服或运营协作角色。
- 核心场景：展示业务页面、调用后端 API、管理用户侧状态、完成用户侧业务流程。
- 不做范围：不直接维护服务端数据库结构；不保存真实密钥。若项目需要独立后台前端，应按项目实际新增 app_key。

## 3. 实现程度

- 已完成：模板已提供 `code/client`、`code/client/.maw.component.yaml`、`.maw/app-runtime.yaml` 中的 `client` 调试索引、`.maw/repositories.yaml` 中的镜像仓库引用，以及 `release/client` 覆盖层。
- 部分完成：安装、启动、测试、构建命令是模板示例，需要按真实前端工程校准。
- 未开始：真实页面、路由、状态流、接口调用、权限和埋点规则需要项目初始化后填写。
- 未验证：当前模板不代表任何具体页面已可用。
- 风险：页面路径、API 调用和状态流变更后不更新档案，会导致 AI 后续误判页面职责或跨模块改动。
- 拆分提醒：本档案只表达用户侧前端 component 边界。登录注册、个人资料、订单列表、设备绑定、报表查看等业务能力应拆成独立 leaf，并在 `.maw/modules.yaml` 绑定页面、接口和测试路径。

## 4. 迭代计划

- 当前迭代：项目初始化迭代。
- 本迭代目标：确认前端技术栈、入口页面、路由边界、API 调用边界和测试方式。
- 下一迭代候选：按业务功能拆分用户侧页面模块、复用组件和状态流。
- 阻塞项：真实页面清单、设计稿、接口契约和用户角色未确认。

## 5. 待办

> 本表只记录 client component 内部待办。若某项前端流程依赖暂未实现的服务端、数据、权限或外部系统能力，必须登记到 `docs/planning/todos/active.md`，这里只回链 TODO-ID。

| TODO-ID/局部ID | 类型 | 内容 | 优先级 | 来源 | 影响模块 | 对应 Story/Task | 状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| local-client-config | config | 校准 `code/client/.maw.component.yaml` 中的安装、启动、测试、构建命令 | P1 | 模板初始化 | client |  | planned |
| local-client-ui | ui | 填写用户端页面、路由和组件边界 | P1 | 项目初始化 | client |  | planned |
| local-client-api | api | 填写用户端调用的 API 基础地址和接口清单 | P1 | 项目初始化 | client |  | planned |

## 6. 前端页面边界

| 页面/组件 | 路径 | 职责 | 不负责 | 备注 |
| --- | --- | --- | --- | --- |
| 用户端应用根目录 | `code/client` | 前端页面、路由、状态、组件和接口调用 | 服务端 API 实现 | 真实项目应按页面或业务模块继续拆分 |

## 7. 后端接口边界

| 接口/命令 | 文件或目录 | 方法/函数 | 请求/响应概要 | 权限/风险 |
| --- | --- | --- | --- | --- |
| API 基础地址引用 | `.maw/app-runtime.yaml` | `app_runtime.apps.client.api_base_url_ref` | 指向用户端联调 API 地址引用 | 不在前端源码中硬编码生产密钥或内部地址 |

## 8. 数据表边界

| 表/集合 | 模型/迁移 | 读写职责 | 关键字段 | 风险 |
| --- | --- | --- | --- | --- |
| 不直接负责 |  | 前端通过 API 间接读取或提交数据 |  | 数据结构变化应由服务端模块和设计文档维护 |

## 9. 配置与运行边界

- `.maw` 配置：`.maw/components.yaml`、`.maw/app-runtime.yaml`、`.maw/environments.yaml`、`.maw/repositories.yaml`、`.maw/releases.yaml`、`.maw/policies.yaml`；其中 `.maw/components.yaml` 通过 `release_ref` 指向发布配置。
- 客户仓库规则：`.maw/customer-repository-rules.yaml` 记录 client 客出白名单、客户仓子目录、整仓替换开关和执行前方案目录；默认不得整仓替换客户仓库。
- 组件配置：`code/client/.maw.component.yaml`、`code/client/.env.example`。
- 环境变量：前端公开变量写入 code 内示例；真实密钥不得打包到前端。
- AI 调试入口：`.maw/app-runtime.yaml` 的 `app_runtime.apps.client`。
- 仓库级镜像边界：整仓 mirror 由聚合后的仓库配置和 `ops/scripts/sync-repository-mirror.sh plan` 有效计划控制；`auto_sync_after_project_push` 默认开启，项目仓库 push 成功后先看计划再同步。
- 组件镜像仓库边界：`.maw/repositories.yaml` 的 `component_mirrors.components.client` 只允许当前项目仓库单向同步到目标仓库。
- 发布环境配置：`.maw/releases.yaml` 的 `releases.components.client` 和 `code/client/.maw.component.yaml` 的 `release`；默认发布环境为 `test`，可选环境包含 `test`、`staging`、`production`，项目可按实际追加。中文口令 `发布测试` 映射到本地调试 `local_debug`，需给可访问调试地址；`发布上线` 映射到编译包部署测试目标 `remote_staging_server`，仍属于测试，需给线上可访问地址；`发布生产`/`发布生成` 映射到 `remote_production_server`，涉及生产环境安装或版本上线必须人工审计；未指定组件时按 `.maw/environments.yaml` 对应 `remote_server.default_release_components` 判断候选范围，再按 `artifacts/release-state/<env>/client.json` 的 commit 记录和 client 相关路径差异判断是否发布 client。
- 发布版本状态：client 成功发布后应更新 `artifacts/release-state/<env>/client.json`；`发布上线` 和 `发布生产` 执行前必须确认本地候选 commit 等于发布来源远端分支。
- 发布覆盖层：`release/client/default` 和 `release/client/<app_key>`。

## 10. 任务与节点边界

- 推荐任务类型：ui、feature、fix、api、config、release、docs。
- 可执行节点角色：Planner、Executor、Reviewer、Release Manager。
- 是否需要源码权限：是。
- 是否需要人工审批：涉及登录权限、支付、隐私数据、外部 SDK、发布覆盖和客户仓库同步时需要。
- 测试/验收要求：至少运行前端单测、构建、页面冒烟或手工验证路径；无法运行时说明原因。
- 任务完成说明：若本轮修改 `client` 或 `app_key=client` 且需要发布才会生效，必须说明“本轮修改了 client 的 <内容>，需要发布 client 才会生效，当前已发布/当前未发布”；需要发布但未发布或未验证时，必须给出可复制 `#发布：发布 client 到 <env>...` 和可用中文口令快捷指令，并在收口末尾询问是否“确认发布全部”；未命中时说明无需发布。

## 11. 文档维护规则

- 修改页面时必须更新：第 6 节、`docs/design/page-flow.md` 和 changelog。
- 修改接口时必须更新：第 7 节、`docs/design/api-design.md` 和 changelog。
- 修改数据表时必须更新：通常不直接更新；如页面依赖字段变化，记录到第 7 节或相关设计文档。
- 修改状态流/权限/发布规则时必须更新：第 2、6、9、10 节及相关 `.maw` 或 `release/` 文档。
- 修改仓库级镜像或组件镜像仓库目标、自动同步开关或同步方向时必须更新：第 9、10 节、`.maw/repositories.yaml`、`docs/repository-mirror-sync-guide.md`、`docs/component-mirror-repository-guide.md` 和 changelog。
- 修改源码、运行配置、发布覆盖、部署脚本或外部同步逻辑时必须在最终说明同步 `release_update_status`、`release_commands` 和 `release_confirmation_prompt`；本轮未执行并验证发布时写 `当前未发布` 或 `当前未发布/未验证`，并给出 `#发布` 指令。中文环境口令未指定组件时，先按默认组件范围和发布版本状态计算实际发布名单；收口末尾询问是否“确认发布全部”，用户回复“确认发布全部/确认/是”则发布全部待发布组件，复制单条指令则只发布对应组件。

## 12. 最近变更摘要

| 日期 | 任务/提交 | 变更摘要 | 是否更新档案 |
| --- | --- | --- | --- |
| 2026-06-29 | 发布测试/上线/生产边界强化 | 补充 `发布测试` 的本地调试地址、`发布上线` 仍属测试且需线上可访问地址、`发布生产` 生产环境安装或版本上线必须人工审计 | 是 |
| 2026-06-16 | 待办任务治理 | 区分模块内部待办与 `docs/planning/todos/active.md` 跨模块被依赖待办，模块档案只回链 TODO-ID | 是 |
| 2026-06-16 | 发布版本状态与最新代码门 | 补充 client 按 `artifacts/release-state/<env>/client.json` 记录已发布 commit、按组件路径差异筛选发布名单，以及上线/生产必须校验本地候选 commit 等于发布来源远端分支 | 是 |
| 2026-06-15 | 中文发布口令与默认组件范围 | 补充 `发布测试`、`发布上线`、`发布生产`/`发布生成` 口令和默认发布范围；基础映射为 `发布测试` 本地调试、`发布上线` 部署到 `remote_staging_server`、`发布生产` 部署到 `remote_production_server` | 是 |
| 2026-06-14 | 中文人类优先收口规则同步 | 将发布确认文案同步为“确认发布全部”，与 TINST-020 中文收口规则保持一致 | 是 |
| 2026-06-13 | 仓库级镜像与发布收口优化 | 补充 repository_mirrors 自动同步开关，并将发布收口改为“需要发布才会生效/是否全部发布”语义 | 是 |
| 2026-06-12 | 客户仓库规则治理 | 补充 client 客户仓库白名单客出、执行前方案和多通道 git 凭证配置边界 | 是 |
| 2026-06-12 | 发布配置环境选项 | 补充 client 默认发布环境、可选环境和快捷发布指令配置边界 | 是 |
| 2026-06-12 | 发布快捷指令收口规则 | 补充 client 需要发布但未发布时的 `#发布` 快捷指令和确认后执行发布要求 | 是 |
| 2026-06-12 | 最终说明发布状态约束 | 补充 client 命中与发布状态最终说明要求 | 是 |
| 2026-06-12 | 组件镜像仓库协议 | 补充 client 镜像仓库单向同步边界和配置引用 | 是 |
| 2026-05-20 | 模板模块档案协议初始化 | 新增用户端前端模块档案样例 | 是 |
