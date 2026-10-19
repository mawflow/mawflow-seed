# 阶段规范索引

本页由 .maw/standards.yaml 生成；规则正文与项目事实仍由各自权威文件维护。

按任务范围选择规范。阶段导航不授予写入、测试、部署或对外共享权限。

## 立项与初始化

[阶段清单](01-initiation.md)

| 规范 | 类型 | 条件 | 执行方式 | 权威来源 |
| --- | --- | --- | --- | --- |
| 来源与版本 | common | 模板创建、升级或发布 | manual | [std.source-route](general.md) |
| 读取与动作授权 | common | 开工或动作/环境范围变化 | manual | [std.authorization](general.md) |
| 模块所有权与公共缺口 | common | 定位改动或发现范围外依赖 | manual | [std.ownership](general.md) |
| 状态与证据有效性 | common | 验证、交付、部署或收口 | script | [std.evidence](task-checklists.md) |
| 规则修订与冲突 | common | 发现重复、冲突或过期口径 | manual | [std.rule-lifecycle](general.md) |
| 项目分类与规则取舍 | project | 新建、接管或采用外部规范 | manual | [std.project-adoption](project-adoption.md) |
| 项目创建和存量接管 | stage | 用户授权创建/采纳/接管 | manual | [std.onboarding](01-initiation.md) |
| 组件与环境资源配置 | stage | 新增组件、环境或部署目标 | manual | [std.configuration](01-initiation.md) |
| 公共经验与资源采用 | resource | 任务需要共享资源或工程经验 | manual | [std.libraries](knowledge-resources.md) |
| 经验候选与审核回流 | resource | 产生跨项目可复用经验 | manual | [std.feedback](knowledge-resources.md) |
| 任务生命周期与资源收尾 | common | 开工、恢复、等待、失败、取消、交接与结束 | script | [std.task-lifecycle](../ai-coding/task-lifecycle.md) |

## 需求与设计

[阶段清单](02-design.md)

| 规范 | 类型 | 条件 | 执行方式 | 权威来源 |
| --- | --- | --- | --- | --- |
| 来源与版本 | common | 模板创建、升级或发布 | manual | [std.source-route](general.md) |
| 读取与动作授权 | common | 开工或动作/环境范围变化 | manual | [std.authorization](general.md) |
| 模块所有权与公共缺口 | common | 定位改动或发现范围外依赖 | manual | [std.ownership](general.md) |
| 状态与证据有效性 | common | 验证、交付、部署或收口 | script | [std.evidence](task-checklists.md) |
| 规则修订与冲突 | common | 发现重复、冲突或过期口径 | manual | [std.rule-lifecycle](general.md) |
| 项目分类与规则取舍 | project | 新建、接管或采用外部规范 | manual | [std.project-adoption](project-adoption.md) |
| 需求与验收目标 | stage | 需求范围或验收目标变化 | manual | [std.requirements](02-design.md) |
| 模块地图 | stage | 页面/API/表/状态归属变化 | manual | [std.module-map](02-design.md) |
| 技术地图与公共复用 | stage | 开发新能力或接口 | manual | [std.technical-map](02-design.md) |
| 外部契约与集成 | stage | 依赖外部服务或公共模块 | manual | [std.external-contract](02-design.md) |
| 公共经验与资源采用 | resource | 任务需要共享资源或工程经验 | manual | [std.libraries](knowledge-resources.md) |
| 经验候选与审核回流 | resource | 产生跨项目可复用经验 | manual | [std.feedback](knowledge-resources.md) |
| 任务生命周期与资源收尾 | common | 开工、恢复、等待、失败、取消、交接与结束 | script | [std.task-lifecycle](../ai-coding/task-lifecycle.md) |

## 开发与集成

[阶段清单](03-development.md)

| 规范 | 类型 | 条件 | 执行方式 | 权威来源 |
| --- | --- | --- | --- | --- |
| 来源与版本 | common | 模板创建、升级或发布 | manual | [std.source-route](general.md) |
| 读取与动作授权 | common | 开工或动作/环境范围变化 | manual | [std.authorization](general.md) |
| 模块所有权与公共缺口 | common | 定位改动或发现范围外依赖 | manual | [std.ownership](general.md) |
| 状态与证据有效性 | common | 验证、交付、部署或收口 | script | [std.evidence](task-checklists.md) |
| 规则修订与冲突 | common | 发现重复、冲突或过期口径 | manual | [std.rule-lifecycle](general.md) |
| 项目分类与规则取舍 | project | 新建、接管或采用外部规范 | manual | [std.project-adoption](project-adoption.md) |
| 模块地图 | stage | 页面/API/表/状态归属变化 | manual | [std.module-map](02-design.md) |
| 技术地图与公共复用 | stage | 开发新能力或接口 | manual | [std.technical-map](02-design.md) |
| 编码与接口兼容 | stage | 实现、修复或重构 | manual | [std.coding](03-development.md) |
| 分支协作与集成 | stage | 多个写入者或任务分支集成 | manual | [std.collaboration](03-development.md) |
| 设备预算与制品复用 | resource | 服务启动、构建、重测试或续跑 | manual | [std.resources](03-development.md) |
| 测试授权与影响范围 | stage | 选择或扩大验证范围 | manual | [std.test-scope](04-testing.md) |
| 失败恢复与最小续跑 | stage | 失败、输入变化或继续未完步骤 | manual | [std.recovery](05-deployment.md) |
| 更新文档与冻结快照 | stage | 用户可见变化、部署或交付收尾 | manual | [std.update-notes](06-delivery.md) |
| 公共经验与资源采用 | resource | 任务需要共享资源或工程经验 | manual | [std.libraries](knowledge-resources.md) |
| 经验候选与审核回流 | resource | 产生跨项目可复用经验 | manual | [std.feedback](knowledge-resources.md) |
| 任务生命周期与资源收尾 | common | 开工、恢复、等待、失败、取消、交接与结束 | script | [std.task-lifecycle](../ai-coding/task-lifecycle.md) |

## 测试与质量

[阶段清单](04-testing.md)

| 规范 | 类型 | 条件 | 执行方式 | 权威来源 |
| --- | --- | --- | --- | --- |
| 来源与版本 | common | 模板创建、升级或发布 | manual | [std.source-route](general.md) |
| 读取与动作授权 | common | 开工或动作/环境范围变化 | manual | [std.authorization](general.md) |
| 模块所有权与公共缺口 | common | 定位改动或发现范围外依赖 | manual | [std.ownership](general.md) |
| 状态与证据有效性 | common | 验证、交付、部署或收口 | script | [std.evidence](task-checklists.md) |
| 规则修订与冲突 | common | 发现重复、冲突或过期口径 | manual | [std.rule-lifecycle](general.md) |
| 项目分类与规则取舍 | project | 新建、接管或采用外部规范 | manual | [std.project-adoption](project-adoption.md) |
| 需求与验收目标 | stage | 需求范围或验收目标变化 | manual | [std.requirements](02-design.md) |
| 外部契约与集成 | stage | 依赖外部服务或公共模块 | manual | [std.external-contract](02-design.md) |
| 设备预算与制品复用 | resource | 服务启动、构建、重测试或续跑 | manual | [std.resources](03-development.md) |
| 测试授权与影响范围 | stage | 选择或扩大验证范围 | manual | [std.test-scope](04-testing.md) |
| 测试接入与空套件 | stage | Test Contract注册或验证收口 | script | [std.test-registration](task-checklists.md) |
| 真实角色与页面旅程 | stage | 页面、权限和业务流程变化 | manual | [std.real-journeys](04-testing.md) |
| 失败恢复与最小续跑 | stage | 失败、输入变化或继续未完步骤 | manual | [std.recovery](05-deployment.md) |
| 公共经验与资源采用 | resource | 任务需要共享资源或工程经验 | manual | [std.libraries](knowledge-resources.md) |
| 经验候选与审核回流 | resource | 产生跨项目可复用经验 | manual | [std.feedback](knowledge-resources.md) |
| 任务生命周期与资源收尾 | common | 开工、恢复、等待、失败、取消、交接与结束 | script | [std.task-lifecycle](../ai-coding/task-lifecycle.md) |

## 部署与发布

[阶段清单](05-deployment.md)

| 规范 | 类型 | 条件 | 执行方式 | 权威来源 |
| --- | --- | --- | --- | --- |
| 来源与版本 | common | 模板创建、升级或发布 | manual | [std.source-route](general.md) |
| 读取与动作授权 | common | 开工或动作/环境范围变化 | manual | [std.authorization](general.md) |
| 模块所有权与公共缺口 | common | 定位改动或发现范围外依赖 | manual | [std.ownership](general.md) |
| 状态与证据有效性 | common | 验证、交付、部署或收口 | script | [std.evidence](task-checklists.md) |
| 规则修订与冲突 | common | 发现重复、冲突或过期口径 | manual | [std.rule-lifecycle](general.md) |
| 项目分类与规则取舍 | project | 新建、接管或采用外部规范 | manual | [std.project-adoption](project-adoption.md) |
| 组件与环境资源配置 | stage | 新增组件、环境或部署目标 | manual | [std.configuration](01-initiation.md) |
| 外部契约与集成 | stage | 依赖外部服务或公共模块 | manual | [std.external-contract](02-design.md) |
| 设备预算与制品复用 | resource | 服务启动、构建、重测试或续跑 | manual | [std.resources](03-development.md) |
| 测试授权与影响范围 | stage | 选择或扩大验证范围 | manual | [std.test-scope](04-testing.md) |
| 部署方案与冻结制品 | stage | 用户授权目标部署 | manual | [std.deployment](05-deployment.md) |
| 数据库诊断与增量交付 | stage | 涉及目标结构、配置或数据写入 | manual | [std.database](05-deployment.md) |
| 失败恢复与最小续跑 | stage | 失败、输入变化或继续未完步骤 | manual | [std.recovery](05-deployment.md) |
| 更新文档与冻结快照 | stage | 用户可见变化、部署或交付收尾 | manual | [std.update-notes](06-delivery.md) |
| 公共经验与资源采用 | resource | 任务需要共享资源或工程经验 | manual | [std.libraries](knowledge-resources.md) |
| 经验候选与审核回流 | resource | 产生跨项目可复用经验 | manual | [std.feedback](knowledge-resources.md) |
| 任务生命周期与资源收尾 | common | 开工、恢复、等待、失败、取消、交接与结束 | script | [std.task-lifecycle](../ai-coding/task-lifecycle.md) |

## 交付与移交

[阶段清单](06-delivery.md)

| 规范 | 类型 | 条件 | 执行方式 | 权威来源 |
| --- | --- | --- | --- | --- |
| 来源与版本 | common | 模板创建、升级或发布 | manual | [std.source-route](general.md) |
| 读取与动作授权 | common | 开工或动作/环境范围变化 | manual | [std.authorization](general.md) |
| 模块所有权与公共缺口 | common | 定位改动或发现范围外依赖 | manual | [std.ownership](general.md) |
| 状态与证据有效性 | common | 验证、交付、部署或收口 | script | [std.evidence](task-checklists.md) |
| 规则修订与冲突 | common | 发现重复、冲突或过期口径 | manual | [std.rule-lifecycle](general.md) |
| 项目分类与规则取舍 | project | 新建、接管或采用外部规范 | manual | [std.project-adoption](project-adoption.md) |
| 模块地图 | stage | 页面/API/表/状态归属变化 | manual | [std.module-map](02-design.md) |
| 外部契约与集成 | stage | 依赖外部服务或公共模块 | manual | [std.external-contract](02-design.md) |
| 设备预算与制品复用 | resource | 服务启动、构建、重测试或续跑 | manual | [std.resources](03-development.md) |
| 测试授权与影响范围 | stage | 选择或扩大验证范围 | manual | [std.test-scope](04-testing.md) |
| 数据库诊断与增量交付 | stage | 涉及目标结构、配置或数据写入 | manual | [std.database](05-deployment.md) |
| 失败恢复与最小续跑 | stage | 失败、输入变化或继续未完步骤 | manual | [std.recovery](05-deployment.md) |
| 更新文档与冻结快照 | stage | 用户可见变化、部署或交付收尾 | manual | [std.update-notes](06-delivery.md) |
| 客户真实候选验证 | stage | 对客户代码或制品交付 | manual | [std.customer-candidate](06-delivery.md) |
| 文档审计与责任移交 | stage | 用户、技术、运维或UAT交付 | manual | [std.handoff](06-delivery.md) |
| 公共经验与资源采用 | resource | 任务需要共享资源或工程经验 | manual | [std.libraries](knowledge-resources.md) |
| 经验候选与审核回流 | resource | 产生跨项目可复用经验 | manual | [std.feedback](knowledge-resources.md) |
| 任务生命周期与资源收尾 | common | 开工、恢复、等待、失败、取消、交接与结束 | script | [std.task-lifecycle](../ai-coding/task-lifecycle.md) |
