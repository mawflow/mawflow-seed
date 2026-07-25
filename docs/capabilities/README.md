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
- 可选用户级 Agent Skill 的发现、CLI/MCP 适配、无 Skill 降级和版本兼容协议。

## Agent 发现与适配

- [Mawflow Agent Skill 集成](agent-skill-integration.md)：定义可选用户级 Skill 与 Seed 项目规则的权威顺序、安装计划、无 Skill 降级和版本兼容边界。

## 凭证治理

- [项目凭证需求与本机引用绑定](project-credential-requirements.md)：定义 requirement、ref-only binding、Git Commit Identity 分离、readiness 消费和兼容边界。

## 本机目录治理

- [本机文件 `.local` 规范目录](local-directory-canonicalization.md)：定义本机配置、凭证引用、运行状态、旧路径兼容读取和公开安全示例边界。

## 项目生命周期

- [项目生命周期与双端工作台治理](project-lifecycle-governance.md)：定义 main/dev、正式发布来源、配置字段元数据、成员分支/worktree/租约、变更片段、项目手册和 preview-first 迁移边界。

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
