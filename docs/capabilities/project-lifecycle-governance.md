---
doc_key: capability.project-lifecycle-governance
doc_type: capability
stage: governance
status: active
owner: planner
tags: [project-lifecycle, git, release, migration]
project_health:
  dimensions: [ai_collaboration, release_readiness]
  evidence_level: canonical
read_contract:
  summary: "main/dev、正式发布来源、工作台字段、变更片段、项目手册和旧项目迁移的通用协议。"
  consumes: [.maw/project-lifecycle.yaml]
  produces: [project_lifecycle_validation, project_lifecycle_migration_plan]
  ai_read_hint: "项目创建、多人协作、正式发布、模板升级或项目迁移时读取。"
---

# 项目生命周期治理

Seed 只定义跨项目通用契约：`main` 是正式发布分支，`dev` 是开发集成分支；生产候选必须可从 `origin/main` 到达，正式 tag 必须精确指向候选且位于该历史。成员分支需要独立 worktree、基线 SHA、路径边界和写租约；共享分支只允许串行集成。

本地工作台负责真实 Git、worktree、原子写入、租约和本地账本；云端负责组织、成员、跨宿主机调度与集中审计。云端不能绕过本地仓库安全门禁。

## 机器入口

- 协议与字段元数据：`.maw/project-lifecycle.yaml`
- JSON Schema：`.maw/schemas/project-lifecycle.schema.json`
- 任务片段：`.maw/changes/*.yaml`
- 项目手册：`docs/project-manual/manual.yaml`
- 检查、汇总、创建、发布门禁和迁移：`ops/scripts/manage-project-lifecycle.py`

迁移默认为 preview，只新增缺失治理文件；执行要求传入 preview 返回的 fingerprint，并使用原子替换。已有文件、项目配置、README、代码、模块档案、密钥、本机配置和运行时目录均不覆盖。
