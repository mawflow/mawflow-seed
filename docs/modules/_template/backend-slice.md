---
doc_key: docs.modules.template.backend-slice
doc_type: module_design
stage: design
status: active
owner: planner
tags:
  - modules
  - template
  - backend
project_health:
  dimensions:
    - product_module_design
  evidence_level: canonical
read_contract:
  summary: "二级模块后端审计页模板。"
  health_signal: "用于人工和 AI 对照 API、后端文件、服务、模型、权限和数据读写。"
  consumes: []
  produces: []
  ai_read_hint: "已经定位到二级模块且任务涉及 API、后端文件、权限、数据读写或后端审计时读取。"
---

# 后端审计：<API 组 / 后端文件 / 业务动作>

> 本文件放在 `docs/modules/<一级模块>/<二级模块>/backend/<api-group-or-file>.md`。它可以对应一个 controller/service 文件、一组强相关 API，或一个明确业务动作；不要为每个微小接口机械创建文件。模块级事实仍以同目录 `module.md` 为准。

## 1. 后端元信息

- 所属一级模块：
- 所属二级模块 / module_key：
- 审计对象：
- 类型：api_group / controller / service / model / command / job / integration
- 后端源码路径：
- 关联页面：
- doc_status：confirmed / inferred / pending_confirm / stale / deprecated
- confidence：high / medium / low
- last_verified_commit：
- last_verified_at：
- last_verified_by：human / ai / reviewer
- source_paths：
- source_commits：
- last_audit_id：
- 证据来源：

## 2. API/命令清单

| API/命令 | 请求方式 | 函数/方法 | 关键入参 | 关键出参 | 权限 | 错误码/异常 | 状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |  | confirmed / inferred / pending_confirm |

## 3. 服务与数据读写

| 服务/函数 | 数据对象 | 读写职责 | 副作用 | 事务/一致性 | 风险 |
| --- | --- | --- | --- | --- | --- |
|  |  | read / write / read_write |  |  |  |

## 4. 权限、状态与业务规则

- 鉴权入口：
- 角色/权限规则：
- 状态校验：
- 幂等规则：
- 限流/频控：
- 审计日志：
- 外部系统调用：
- 安全与隐私：

## 5. 请求响应与兼容性

| 场景 | 请求摘要 | 响应摘要 | 兼容要求 | 待确认 |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |

## 6. 测试与验证

| 验证项 | 测试路径/命令 | 期望 | 状态 |
| --- | --- | --- | --- |
|  |  |  | pending |

## 7. 审计清单

| 检查项 | 期望 | 证据路径 | 状态 |
| --- | --- | --- | --- |
| API/命令已登记到一级模块 `route-api-index.md` | yes |  | pending / covered / stale |
| 后端边界已登记到二级模块 `module.md` | yes |  | pending / covered / stale |
| 关联页面已链接到页面审计页 | yes / none |  | pending / covered / stale |
| `traceability.md` 已覆盖本对象 | yes / none |  | pending / covered / stale |
| 测试或验收点已登记 | yes / none |  | pending / covered / stale |

## 7A. 生命周期与过期处理

- stale_reason：
- deprecated_by：
- superseded_by：
- 清理建议：保留 / 合并 / 删除 / 待人工确认
- 下次复核触发：API 路由变化 / 后端文件变化 / 数据读写变化 / 发布前检查 / 定期 `#模块地图：检查`

## 8. 待确认项

| 编号 | 问题 | 影响 | 建议确认对象 | 状态 |
| --- | --- | --- | --- | --- |
|  |  |  |  | open / resolved |
