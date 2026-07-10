---
doc_key: docs.modules.template.page
doc_type: module_design
stage: design
status: active
owner: planner
tags:
  - modules
  - template
  - page
project_health:
  dimensions:
    - product_module_design
  evidence_level: canonical
read_contract:
  summary: "二级模块前端页面审计页模板。"
  health_signal: "用于人工和 AI 对照页面、路由、字段、按钮、状态和 API 调用。"
  consumes: []
  produces: []
  ai_read_hint: "已经定位到二级模块且任务涉及具体页面、交互或前端审计时读取。"
---

# 页面审计：<页面名称>

> 本文件放在 `docs/modules/<一级模块>/<二级模块>/pages/<page-key>.md`。它是二级模块下的审计页，不是新的正式模块；模块级事实仍以同目录 `module.md` 为准。

## 1. 页面元信息

- 所属一级模块：
- 所属二级模块 / module_key：
- 页面名称：
- URL/路由：
- 前端源码路径：
- 入口菜单/来源：
- 用户角色：
- doc_status：confirmed / inferred / pending_confirm / stale / deprecated
- confidence：high / medium / low
- last_verified_commit：
- last_verified_at：
- last_verified_by：human / ai / reviewer
- source_paths：
- source_commits：
- last_audit_id：
- 证据来源：

## 2. 页面职责

- 负责：
- 不负责：
- 上游入口：
- 下游动作：
- 关联 API：
- 关联后端审计页：

## 3. 布局与区块

| 区块 | 展示条件 | 主要内容 | 数据来源 | 空态/异常 | 备注 |
| --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |

## 4. 字段与校验

| 字段 | 所属区块 | 类型 | 可编辑 | 必填 | 取值/校验 | 默认值/占位 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- |
|  |  |  | yes / no | yes / no |  |  |  |

## 5. 按钮与交互

| 操作 | 可用条件 | 点击行为 | 调用 API/命令 | 状态变化 | 成功反馈 | 失败反馈 |
| --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |  |

## 6. 状态、权限与边界

- 页面状态：
- 权限/角色：
- 加载态：
- 空态：
- 错误态：
- 分页/排序/筛选：
- 文件/附件：
- 安全与隐私：

## 7. 审计清单

| 检查项 | 期望 | 证据路径 | 状态 |
| --- | --- | --- | --- |
| URL 已登记到一级模块 `route-api-index.md` | yes |  | pending / covered / stale |
| 页面已登记到二级模块 `module.md` | yes |  | pending / covered / stale |
| API 调用已链接到后端审计页 | yes / none |  | pending / covered / stale |
| `traceability.md` 已覆盖本页面 | yes / none |  | pending / covered / stale |
| 测试或验收点已登记 | yes / none |  | pending / covered / stale |

## 7A. 生命周期与过期处理

- stale_reason：
- deprecated_by：
- superseded_by：
- 清理建议：保留 / 合并 / 删除 / 待人工确认
- 下次复核触发：页面路由变化 / 组件路径变化 / API 调用变化 / 发布前检查 / 定期 `#模块地图：检查`

## 8. 待确认项

| 编号 | 问题 | 影响 | 建议确认对象 | 状态 |
| --- | --- | --- | --- | --- |
|  |  |  |  | open / resolved |
