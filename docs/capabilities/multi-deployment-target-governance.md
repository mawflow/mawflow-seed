# 多部署目标治理

- capability_key: `multi-deployment-target-governance`
- status: stable
- source: `.maw/deployments.yaml`

该能力把物理服务器资产与项目部署范围拆开。部署目标用稳定 key 绑定环境角色、服务器、可选子项目、显式组件范围和部署策略；一个环境可以有多个目标，一个服务器也可以被多个目标复用。

生产权限依据 `environment_role: production`，目标范围指纹变化后必须重新审批并撤销旧租约。外部 Git 组件使用设备本地绑定仓库的版本事实。共享/云端数据不得包含凭据值或本机绝对路径。

多个组件共用同一数据库或服务迁移时，用相同的 `releases.components.<app_key>.database_migration.service_ref` 声明共享边界；发布规划器按 `service_ref` 归并，并在一个部署目标发布中只安排一个 `owner_component` 执行迁移。
