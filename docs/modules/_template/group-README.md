---
doc_key: docs.modules.template.group-readme
doc_type: governance
stage: design
status: active
owner: planner
tags:
  - modules
  - template
  - group
project_health:
  dimensions:
    - product_module_design
  evidence_level: canonical
read_contract:
  summary: "模块组 README 模板。"
  health_signal: "用于保持模块组菜单和子模块索引一致。"
  consumes: []
  produces: []
  ai_read_hint: "维护模块组模板或生成模块树时读取。"
---

# 模块组：<模块组名称>

> 复制本模板到 `docs/modules/<group>/README.md` 或 `docs/modules/<group>/<sub-group>/README.md` 后填写。模块组只描述自顶向下的分组、共享边界和子模块菜单；真正可执行、可验收的最小功能模块应继续放在最后一级目录，并维护 `module.md` 与 `changelog.md`。AI/Codex 会话默认只读到本菜单，只有定位到具体叶子模块或需要确认跨模块影响时，才继续读取对应模块详情。
> 一级模块如果有页面 URL、API、命令或关键文件线索，应同时维护同目录 `route-api-index.md`。该索引只用于从 URL/API 快速定位二级模块，不替代二级模块 `module.md`。

## 目标

- 业务目标：
- 服务对象：
- 本组存在的原因：

## 用户角色

| 角色 | 关注点 | 可操作范围 |
| --- | --- | --- |
|  |  |  |

## 子模块菜单

| 子模块 | module_key | 类型 | 职责 | 不负责 | 何时继续读取详情 | 文档 |
| --- | --- | --- | --- | --- | --- | --- |
|  |  | group / leaf |  |  |  |  |

## URL/API 快速定位索引

- 索引文件：`route-api-index.md` / none
- 维护范围：仅登记本一级模块下的页面 URL、API、命令或关键文件到二级模块的定位关系。
- 细节边界：字段、按钮、入参出参、权限、状态流和测试点写入二级模块 `module.md`、`pages/`、`backend/` 或 `traceability.md`。

| 类型 | 路径/模式 | 名称 | owner_module | consumer_modules | 详情文档 | 源码路径 | 状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| page / api / command / file |  |  |  |  |  |  | confirmed / inferred / pending_confirm |

## 模块拆分判定表

> 自动生成模块树时先填写本表。只有“是否可独立验收=yes”且“是否继续拆=no”的候选节点，才应成为 leaf 并创建 `module.md` / `changelog.md`。

| 候选节点 | 建议 module_key | 父级 | 拆分依据 | 主要角色 | 页面边界 | API/命令边界 | 数据/状态边界 | 是否可独立验收 | 是否继续拆 | 结论 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  |  |  | 业务域 / 角色 / 页面组 / 接口组 / 数据对象 / 状态流 / 发布边界 |  |  |  |  | yes / no / unknown | yes / no / unknown | group / leaf / cross-cutting / defer |

## 共享边界

- 页面/入口：
- API/命令：
- 数据对象：
- 权限/状态：
- 配置/发布：
- 测试/验收：

## 与其它模块的关系

| 外部模块 | 关系 | 边界 |
| --- | --- | --- |
|  |  |  |

## 拆分规则

- 什么时候应新增子模块：
- 什么时候应合并回已有子模块：
- 什么时候应拆到其它模块组：
- 待确认问题：
