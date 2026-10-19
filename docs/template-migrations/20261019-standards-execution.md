---
doc_key: migration.standards-execution
doc_type: governance
stage: development
status: active
owner: project-owner
---

# 规范执行三批次增量采用

第一批修复路径归一化、祖先范围交集、浏览器控制回执、嵌套契约 readiness 和 pytest CI 漏跑；第二批引入显式适用条件、执行证据与规则指纹、必读上下文预算；第三批提供 plan-task/report-task 只读预览、旧任务兼容与新旧项目采用验证。完整字段见 docs/standards/execution-protocol.md，生命周期修订见 docs/ai-coding/task-lifecycle.md。

仍属 Seed 2.15.0 开发候选，未另建发行版本。将新增共享文件、Schema、适配器和规范目录纳入 Git/Kit 清单，增量合并 Agent 入口及项目定制规则。不得覆盖项目身份、业务源码、app_key、发布配置、仓库映射、模块历史、来源记录与更新动态；源仓真实审计记录不进入新建项目。

旧快照扩展缺失显示 not_adopted；进行中任务在安全恢复点采用，新任务启用 evidence_policy 与 protocol_revision: 2，并用 plan-task 生成规则绑定预览。旧 Kit 不认识新声明时返回升级缺口，先使用候选 Kit 验证，不静默安装 Host。公共稳定版本、主仓采用、客户项目更新与浏览器实际能力验收分别留证。
