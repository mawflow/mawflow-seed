---
doc_key: docs.capabilities.index
doc_type: governance
stage: governance
status: active
owner: planner
tags:
  - capabilities
  - technical-map
project_health:
  dimensions:
    - ai_collaboration
    - project_audit
  evidence_level: canonical
read_contract:
  summary: "公共能力说明目录和能力文档模板入口。"
  health_signal: "用于项目审计和 AI 任务识别可复用公共能力文档。"
  consumes: []
  produces: []
  ai_read_hint: "新增或查询 capability_key、公共脚本、协议或治理能力时读取。"
---

# 公共能力索引

本目录保存公共能力的人类可读说明。机器可读索引在 `.maw/capabilities.yaml`。

公共能力包括但不限于：

- 可复用 API、服务、SDK 封装、领域基类。
- 前端基础组件、页面基类、状态管理封装。
- 后端基类、权限/审计/导入导出/文件/通知/支付等共享服务。
- 运维、发布、镜像、脱敏、巡检和审计脚本。
- 模板治理协议、项目指令和检查脚本。
- 可被主项目、审计或 AI 健康关注导入的数据契约，例如项目健康上下文。
- 可被 AI Coding 选择、锁定、预览和注入的工程知识资源协议，例如 MCP Knowledge Runtime Pack registry。

## 维护规则

- `.maw/capabilities.yaml` 是 AI 和工具优先读取的能力索引。
- `docs/capabilities/<capability-key>.md` 用于记录较长设计、使用示例、迁移说明或兼容性说明。
- 模块档案只引用 `capability_key`，不要复制完整公共能力事实。
- 能力从一个模块抽出时，先标记为 `candidate`；确认可复用后再标记为 `stable`。
- 废弃能力不要直接删除，先标记 `deprecated` 并给替代能力。

## 新增能力档案

复制 `_template/capability.md` 到：

```text
docs/capabilities/<capability-key>.md
```

同时在 `.maw/capabilities.yaml` 中新增同名 `key`。
