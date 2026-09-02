# 多服务器部署目标与组件范围治理

- 日期：2026-09-02
- 风险等级：T4
- 适用范围：一个 MAWflow 项目内包含多个独立子项目，且线上验证或生产组件部署到不同服务器的项目。

## 核心模型

`.maw/deployments.yaml` 的 `deployment_targets` 是组件发布到服务器的权威关系。服务器是可复用的全局资源，不保存项目组件列表；每个部署目标显式声明 `environment_key`、规范 `environment_role`、`server_ref`、可选 `subproject_ref`、`component_refs`、`scope_mode` 和策略引用。一个服务器可以支持多个目标，一个环境也可以有多个目标。

`component_refs` 永远是显式范围。新增组件不会自动进入任何目标，空列表也不会解释为全部组件。默认 `scope_mode: exclusive`；只有明确的蓝绿、灰度或多地域场景才使用 `replicated`，且同环境内的所有重叠目标都必须为 replicated。

生产门禁依据 `environment_role: production`，不能用自定义环境 key 绕过。目标、服务器、组件范围、访问配置或策略发生变化时，需要使既有审批和短期凭证租约失效并重新确认。

## 兼容迁移

- 旧 `environments.<env>.remote_server` 可展示为 `<env>-default` 只读隐式目标，待用户在工作台确认后写入新文件。
- 旧 `default_release_components` 迁入目标的显式 `component_refs`；旧值为空时保持空并阻断发布，不推断为全部组件。
- 旧 `artifacts/release-state/<env>/<app_key>.json` 继续只读；新成功记录写入 `<env>/<deployment-target>/<app_key>.json`。
- `deployment_group_ref` 继续表示非原子协调发布组，不替代部署目标。
- 外部 Git 组件按 `.local/.maw/code-source-bindings.yaml` 解析当前设备的 Git 根、分支、dirty 和 commit；外层 MAWflow 仓库 commit 不再冒充外部源码版本。
- 多组件共享数据库迁移按 `database_migration.service_ref` 分组；同一目标的一次发布只由分组的 `owner_component` 执行一次。

## 工作台预期

项目空间的“环境与凭证”页面应提供“部署目标 / 凭证绑定 / 健康与发布准备度”三个视图。创建流程依次选择环境、服务器、子项目、组件范围、访问配置与策略，最后预览确认；生产目标进入独立审批，不因保存配置直接获得自动使用权。
