---
doc_key: docs.modules.template.module
doc_type: governance
stage: design
status: active
owner: planner
tags:
  - modules
  - template
  - module
project_health:
  dimensions:
    - product_module_design
  evidence_level: canonical
read_contract:
  summary: "模块档案模板。"
  health_signal: "用于保持正式 leaf module.md 的字段、边界和读取口径一致。"
  consumes: []
  produces: []
  ai_read_hint: "维护模块档案模板或生成新模块档案时读取。"
---

# 模块：<模块名称>

> 复制本模板到 `docs/modules/<一级模块>/<二级模块>/module.md` 后填写。二级模块代表最小可交付功能模块；如果需要大模块或中间模块组，请先创建对应目录的 `README.md`。默认内容是边界与功能规格填写指南，不代表完整业务实现；不要把一次性需求原文整段粘贴到模板或模块档案中，应提炼为可维护的页面、接口、状态、规则和待确认项。
> 如果本模块有复杂页面或后端接口，详细审计内容放入同目录 `pages/`、`backend/` 和 `traceability.md`；本文件只维护模块级事实和索引。

## 1. 模块元信息

- module_key:
- status: planned / in_progress / usable / production_ready / deprecated
- doc_status: confirmed / inferred / pending_confirm / stale / deprecated
- confidence: high / medium / low
- parent_module:
- owner_role:
- source_required:
- related_components:
- related_app_keys:
- related_pm_story_refs:
- related_pm_task_refs:
- last_verified_commit:
- last_verified_at:
- last_verified_by: human / ai / reviewer
- verified_scope: route / page / api / backend / db / tests / release
- last_audit_id:
- audit_docs:

## 2. 需求来源与证据

- 主要来源：
- 原型/截图：
- 需求文档：
- 会议/沟通记录：
- source_commits：
- source_paths：
- 已确认口径：
- 待确认口径：
- 信息可信度：confirmed / inferred / pending_confirm / stale / deprecated

## 2A. 文档证据与生命周期

> 模块档案允许渐进补全，但每次修改必须说明依据。`last_verified_commit` 记录本档案最近一次和代码/路由/接口/测试对齐的提交；无法确认时写 `pending_confirm`，不要把推断写成 confirmed。

- 文档生命周期：active / stale / deprecated
- stale_reason：
- deprecated_by：
- superseded_by：
- 下一次复核触发：页面/API/代码路径变化 / 发布前检查 / 定期 `#模块地图：检查`

| 证据类型 | 证据路径/commit | 覆盖范围 | doc_status | confidence | 备注 |
| --- | --- | --- | --- | --- | --- |
| route / page / api / backend / db / tests / release |  |  | confirmed / inferred / pending_confirm / stale / deprecated | high / medium / low |  |

## 3. 当前功能描述

- 业务目标：
- 用户角色：
- 核心场景：
- 不做范围：
- 上游触发：
- 下游影响：
- 关键状态/枚举：

## 3A. AI 边界指引

> 本节服务 AI 最小上下文读取和人工审计。写清哪些边界不能被 AI 扩大、哪些上下游必须先核对。

- 本模块负责：
- 本模块不负责：
- 修改前必读：
- 禁止直接修改：
- 常见误判：
- 跨模块影响：
- 验证入口：

## 4. 页面与流程拆解

> 适合从功能描述、原型或截图中提炼“从哪里来、到哪里去、点什么、状态如何变化”。复杂流程可补充 `docs/design/page-flow.md` 或 Mermaid 图。

| 场景/入口 | 触发条件 | 用户操作 | 系统行为 | 成功结果 | 失败/空态 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |  |

## 5. 页面/弹窗/组件规格

| 页面/弹窗/组件 | 布局结构 | 主要字段/表格 | 主要按钮 | 展示条件 | 只读/编辑规则 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |  |

## 6. 字段与校验规则

| 所属页面/区块 | 字段名称 | 字段类型 | 是否可编辑 | 是否必填 | 校验/取值规则 | 默认值/占位 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |  |  |

## 7. 按钮与交互规则

| 页面/区块 | 按钮/操作 | 可用条件 | 点击行为 | 状态变化 | 成功反馈 | 失败反馈 |
| --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |  |

## 8. 状态流与业务规则

- 状态集合：
- 初始状态：
- 状态流转：
- 自动生成/覆盖规则：
- 联动更新规则：
- 权限/角色规则：
- 消息/通知规则：
- 文件/附件规则：
- 分页/排序/查询规则：

## 9. 异常、边界与待确认项

| 类型 | 场景 | 当前规则 | 风险 | 待确认问题 | 处理建议 | 状态 |
| --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |  |

## 10. 实现程度

- 已完成：
- 部分完成：
- 未开始：
- 未验证：
- 风险：

## 11. 迭代计划

- 当前迭代：
- 本迭代目标：
- 下一迭代候选：
- 阻塞项：

## 12. 待办

> 模块内部局部事项可写在这里。若待办被其它模块依赖、当前业务流程先假设它已完成、或完成/取消会影响其它模块联调，必须登记到 `docs/planning/todos/active.md`，本表只回链 TODO-ID。

| TODO-ID/局部ID | 类型 | 内容 | 优先级 | 来源 | 影响模块 | 对应 Story/Task | 状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |  |  |

## 13. 前端页面边界

| 页面/组件 | URL/路由 | 源码路径 | 职责 | 不负责 | 详情文档 | doc_status | confidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  | `pages/<page-key>.md` / none | confirmed / inferred / pending_confirm / stale / deprecated | high / medium / low |

## 14. 后端接口边界

| 接口/命令 | URL/命令 | 文件或目录 | 方法/函数 | 请求方式 | 详情文档 | 权限/风险 | doc_status | confidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  | `backend/<api-group-or-file>.md` / none |  | confirmed / inferred / pending_confirm / stale / deprecated | high / medium / low |

## 15. 数据表边界

| 表/集合 | 模型/迁移 | 读写职责 | 关键字段 | 风险 |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |

## 16. 配置与运行边界

- `.maw` 配置：
- 组件配置：
- 环境变量：
- AI 调试入口：
- 发布覆盖层：

## 16A. 追踪矩阵与审计页

> `traceability.md` 用来把页面、API、后端文件、数据对象、测试和验收串起来。只有复杂模块、正在审计的模块或页面/API 较多的模块才需要立即补齐；历史项目可按渐进式策略逐步完善。

- 一级模块 URL/API 索引：
- 页面审计页目录：`pages/` / none
- 后端审计页目录：`backend/` / none
- 追踪矩阵：`traceability.md` / none

| 对照项 | 前端页面 | API/命令 | 后端文件 | 数据对象 | 测试/验收 | 状态 |
| --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  | confirmed / inferred / pending_confirm |

## 17. 公共能力引用

> 只引用 `capability_key` 和用途摘要。公共能力的完整事实、实现路径、复用规范和消费方维护在 `.maw/capabilities.yaml` 与 `docs/capabilities/`，不要在每个模块档案中复制一份。

| capability_key | 使用方式 | 复用/扩展要求 | 风险或待确认 |
| --- | --- | --- | --- |
|  |  |  |  |

## 18. 项目信号与 AI 前置条件

> 对人或 AI 有提示意义的待办、澄清、缺口、口径变更、审计提示和风险写入 `.maw/project-signals.yaml`，本节只做回链。

| signal_id / TODO-ID | 类型 | 摘要 | 影响 |
| --- | --- | --- | --- |
|  |  |  |  |

## 19. 任务与节点边界

- 推荐任务类型：
- 可执行节点角色：
- 是否需要源码权限：
- 是否需要人工审批：
- 测试/验收要求：

## 20. 文档维护规则

- 每次更新档案时必须更新 `doc_status`、`confidence`、`last_verified_commit`、`last_verified_at`、`verified_scope` 和必要的 `source_paths/source_commits`；只做草稿或证据不足时保持 `pending_confirm`。
- 定期执行 `#模块地图：检查` 或 `#模块地图：审计 <module_key>` 时，若源码路径、路由、API 或页面已不存在，应标记 `stale`；确认废弃或迁移后标记 `deprecated` 并写 `superseded_by`。
- 修改页面 URL、路由、菜单或页面归属时必须更新：一级模块 `route-api-index.md`、本文件第 13 节、对应 `pages/<page-key>.md` 和必要的 `traceability.md`。
- 修改页面字段、按钮、展示规则、空态、交互或 API 调用时必须更新：本文件第 4-8 节、对应 `pages/<page-key>.md` 和必要的 `traceability.md`。
- 修改接口 URL、请求方式、owner_module、后端文件或模块归属时必须更新：一级模块 `route-api-index.md`、本文件第 14 节、对应 `backend/<api-group-or-file>.md` 和必要的 `traceability.md`。
- 修改接口入参、出参、权限、错误码、副作用或数据读写时必须更新：本文件第 8、14、15 节、对应 `backend/<api-group-or-file>.md` 和必要的 `traceability.md`。
- 修改数据表时必须更新：
- 修改状态流/权限/发布规则时必须更新：
- 新增或复用公共能力时必须更新：
- 新增澄清、缺口、口径变更或审计提示时必须更新：

## 21. 最近变更摘要

| 日期 | commit | 任务/提交 | 变更摘要 | doc_status | 是否更新档案 |
| --- | --- | --- | --- | --- | --- |
|  |  |  |  | confirmed / inferred / pending_confirm / stale / deprecated |  |
