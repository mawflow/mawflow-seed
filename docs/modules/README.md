---
doc_key: docs.modules.index
doc_type: governance
stage: design
status: active
owner: planner
tags:
  - modules
  - index
project_health:
  dimensions:
    - product_module_design
  evidence_level: canonical
read_contract:
  summary: "模块档案目录和模块树读取规则。"
  health_signal: "用于项目健康判断模块树、模块档案和读取路径是否可用。"
  consumes: []
  produces: []
  ai_read_hint: "定位模块边界、生成模块档案或读取模块详情前先读取。"
---

# 功能模块档案

`docs/modules/` 是项目的功能模块地图，用来把项目从业务目标自顶向下拆成可理解、可实现、可验收、可交接的功能块。它和 `.maw/modules.yaml` 一起形成“人工可读边界 + 机器可定位索引”的长期迭代协议。

本目录的核心目标不是罗列代码目录，而是让人和 AI 都能回答：

- 这个项目有哪些大模块？
- 每个大模块下面有哪些更小的能力块？
- 当前任务应该落到哪个最小功能模块？
- 这个模块负责什么、不负责什么、依赖谁、影响谁？
- 页面、接口、数据、配置、测试和发布边界分别在哪里？
- 哪些跨模块待办正在被当前模块依赖，完成或取消后需要怎么联调？
- 当前模块引用了哪些公共能力、API、基类、脚本或治理协议，是否应该从 `.maw/capabilities.yaml` 复用而不是重复实现？

## 模块树优先协议

自动生成或大范围重建模块档案时，必须先生成“模块树”，再生成叶子模块档案。不能把用户给出的一个大词直接落成 `docs/modules/<module-key>/module.md`。

推荐流程：

1. 先识别一级业务域或系统域。
2. 再识别二级能力组、业务流程、页面组、接口组或数据能力。
3. 对每个候选节点做 leaf 判定。
4. 只有满足“最小可交付功能模块”的候选节点，才创建 `module.md` 和 `changelog.md`。
5. 不满足 leaf 条件的候选节点，只能创建或更新模块组 `README.md`，并在子模块菜单中列出下一层。

模块树草案应至少包含：

| 候选节点 | 建议 module_key | 父级 | 类型 | 拆分依据 | 是否可独立验收 | 是否继续拆 | 文档落点 |
| --- | --- | --- | --- | --- | --- | --- | --- |
|  |  |  | group / leaf / cross-cutting | 业务域 / 角色 / 页面组 / 接口组 / 数据对象 / 状态流 / 发布边界 | yes / no / unknown | yes / no / unknown |  |

判定结果为 `unknown` 时，不要强行生成 leaf；先写入父级模块组的“待确认问题”、`docs/modules/_discovery/` 或最终说明中的 `module_candidate`。

## 模块地图与 URL/API 定位索引

模块地图用于把“人眼看到的页面 URL、AI 命中的 API、代码路径”快速定位到正式二级模块。它是轻量索引，不替代二级模块 `module.md`，也不承载字段、按钮、入参出参和状态流等详细事实。

推荐约定：

- 根目录 `docs/modules/README.md` 维护一级模块入口和跨一级模块关系。
- 根目录可按需维护 `docs/modules/module-relations.md`，只记录跨一级模块引用、依赖、共享数据和风险。
- 每个一级模块目录必须优先维护 `README.md`；当该一级模块下存在可识别页面 URL、API 或入口命令时，建议维护 `route-api-index.md`。
- `route-api-index.md` 只记录 `page/api/command/file` 到二级模块的定位关系，详细页面规则和后端规则继续放到二级模块内的 `pages/`、`backend/` 或 `traceability.md`。
- 二级模块才是执行任务、审查、发布判断和 changelog 的主要归属；页面审计页和后端审计页只是二级模块下的证据维度，不升级为第三级正式模块。
- 缺少证据时允许先写 `pending_confirm`、空详情链接或待确认问题；不要为了填满模块地图而编造 URL、API、代码文件、表名、权限或状态流。

推荐目录：

```text
docs/modules/
  README.md
  module-relations.md
  _template/
    route-api-index.md
    page.md
    backend-slice.md
    traceability.md
  <一级模块>/
    README.md
    route-api-index.md
    <二级模块>/
      module.md
      changelog.md
      flows.md
      pages/
        README.md
        <page-key>.md
      backend/
        README.md
        <api-group-or-file>.md
      traceability.md
      ai-context.md
```

`route-api-index.md` 推荐字段：

| 类型 | 路径/模式 | 名称 | owner_module | consumer_modules | 详情文档 | 源码路径 | 状态 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| page / api / command / file |  |  |  |  |  |  | confirmed / inferred / pending_confirm |  |

读取策略：

1. 已知 `module_key` 时，仍先读 `.maw/modules.yaml` 并直接定位二级模块。
2. 只知道页面 URL、API 路径、命令名或文件路径时，先用 `.maw/modules.yaml` 的路径字段缩小范围。
3. 只能定位到一级模块时，读取该一级模块 `README.md` 和 `route-api-index.md`。
4. 根据索引落到二级模块后，只读该二级模块的 `module.md`、必要的 `pages/<page>.md`、`backend/<slice>.md` 或 `traceability.md`。
5. 索引命中多个二级模块时，优先找 `owner_module`；被调用方写入 `consumer_modules`，不要把共享调用误当作所有模块共同拥有。

## 渐进式模块发现

新项目或证据不足的项目不要求一开始就生成完整 confirmed modules。模块线索先进入 `.maw/module-candidates.yaml` 和 `docs/modules/_discovery/`，再根据证据逐步提升。

模块状态建议：

- `seed`：初始线索，只有名称或弱证据。
- `candidate`：已有部分证据，但边界不稳定。
- `provisional`：可用于临时定位和任务收口，但仍需复核。
- `confirmed`：已满足用户确认、稳定业务边界、页面/API/数据/任务证据和复核记录，可进入 `.maw/modules.yaml`。
- `deprecated`：候选废弃或合并到其它模块。

候选模块必须记录名称、别名、状态、置信度、证据、关联 app_key、已知边界、待确认问题和提升条件。证据不足时，最终说明写 `module_candidate` 和不更新正式模块档案原因。

模块地图也遵循渐进式补全策略：

- 第一步只要求一级模块、二级模块和 owner 关系可读。
- 第二步再补一级模块 `route-api-index.md` 的页面/API/命令定位行。
- 第三步只给高频、复杂、易误读或正在审计的页面/API 创建详细审计页。
- 第四步再补 `traceability.md`，把页面、API、后端文件、数据对象和测试串起来。
- 历史项目缺少页面审计页或后端审计页时默认 warning-only，不阻塞普通开发；但新增或重构相关页面/API 时应顺手补齐。

## 证据、生命周期与定期审计

模块地图是 AI 边界和人工审计的共同入口，所以每份正式模块文档都应尽量记录证据，而不是只记录结论。证据不足不阻塞渐进补全，但必须显式标注。

推荐字段：

- `doc_status`：`confirmed` / `inferred` / `pending_confirm` / `stale` / `deprecated`
- `confidence`：`high` / `medium` / `low`
- `last_verified_commit`：最近一次与代码、路由、API、测试或发布事实对齐的 commit。
- `last_verified_at`：最近复核日期。
- `source_paths` / `source_commits`：本次判断依据。
- `last_audit_id`：最近一次 `docs/modules/_audits/` 审计报告 ID。

生命周期规则：

- `confirmed`：有当前代码、路由、API、测试、发布记录或人工确认支撑。
- `inferred`：根据命名、相邻路径、历史档案或局部证据推断，仍需复核。
- `pending_confirm`：owner、边界、状态或来源尚不能确认。
- `stale`：文档可能已过期，例如路径不存在、路由迁移、API 下线或模块合并，但尚未完成确认。
- `deprecated`：确认废弃、合并或被替代，应写明 `superseded_by` 或删除计划。

定期执行 `#模块地图：检查` 时，建议写入 `docs/modules/_audits/YYYYMMDD-module-map-audit.md`。审计报告只记录检查结果和整改闭环，不替代模块事实源。发现事实变化后仍要同步更新 `.maw/modules.yaml`、一级 `route-api-index.md`、二级 `module.md`、detail docs 和 `changelog.md`。

`module_map_score` 用于查漏补缺，推荐维度：

| 维度 | 含义 |
| --- | --- |
| route_index_coverage | 页面 URL/API/命令/关键文件能通过一级索引定位到二级模块的覆盖度 |
| api_owner_coverage | API/命令是否有明确 owner_module |
| detail_doc_coverage | 高频、复杂、正在审计页面/API 是否有页面或后端审计页 |
| traceability_coverage | 关键链路是否能从页面追到 API、后端、数据和测试 |
| pending_confirm_count | 仍需人工确认的条目数量 |
| stale_docs_count | 疑似过期文档数量 |
| orphan_docs_count | 未被 `.maw/modules.yaml`、一级索引或二级模块回链的文档数量 |
| missing_changelog_count | 已发生事实变化但缺少 changelog 的数量 |

旧项目不要求一次性满分；评分是为了决定下一轮优先补哪里，而不是驱动 AI 编造事实。

## 会话读取约束

AI/Codex 不应在任务开始时全量读取 `docs/modules/**`。模块文档必须按“目录 -> 一级说明 -> 子模块菜单 -> 叶子详情”的顺序逐层读取，只有当任务已经定位到具体叶子模块，或需要确认跨模块影响时，才读取对应 `module.md` 和 `changelog.md`。

默认读取顺序：

1. 读取 `.maw/modules.yaml`，用 `module_key`、模块名、页面路径、接口路径、数据表或配置路径做机器定位。
2. 读取 `docs/modules/README.md`，确认当前模块拆分协议。
3. 读取相关一级大模块的 `README.md`，只看大模块目标、共享边界和子模块菜单；如果任务输入是 URL、API、命令或代码路径，再读取该一级模块 `route-api-index.md`。
4. 如果一级大模块下还有中间模块组，继续读取对应中间模块组的 `README.md`。
5. 根据任务范围选择最可能的一个或少数几个叶子模块。
6. 只读取被选中叶子模块的 `module.md`；需要页面或后端审计时，再读取二级模块内具体 `pages/`、`backend/` 或 `traceability.md`。
7. 如果 `.maw/modules.yaml` 为该模块配置了 `ai_doc`，或叶子目录下存在 `ai-context.md`，且任务属于实现、审查、修 bug、发布判断或 AI 经常误读的复杂模块，可以在读取 `module.md` 后读取该 AI 专用上下文。

禁止行为：

- 不要用 `find docs/modules -type f` 后逐个读取全部模块档案。
- 不要为了“了解项目”读取所有叶子模块的 `module.md`。
- 不要给所有模块批量复制一份 `_ai` 后缀档案；`module.md` 仍是唯一模块事实源，AI 专用上下文只能按需创建。
- 不要在只需要一级模块菜单时读取叶子模块详情。
- 不要把一级模块 `route-api-index.md` 写成详细页面规格或 API 设计文档；它只做定位索引。
- 不要把 `pages/` 或 `backend/` 下的审计页当成正式模块，也不要给每个按钮、字段或微小接口都创建独立模块。
- 不要把兄弟模块详情作为默认上下文；只有出现共享接口、共享数据表、共享状态流、发布覆盖或明确跨模块影响时才读取。
- 不要把 `docs/archive/**` 当作模块定位依据。

允许读取多个叶子模块详情的场景：

- 任务明确跨多个模块。
- `.maw/modules.yaml` 的路径匹配落到多个候选模块，且一级/中间 README 无法区分。
- 变更会影响共享 API、共享数据表、共享配置、统一权限、公共状态流或发布覆盖层。
- Reviewer 需要核对跨模块边界是否被破坏。

## 模块层级定义

功能模块必须按自顶向下原则拆分：

```text
项目目标
-> 一级大模块：稳定业务域或系统域
-> 二级模块：大模块内可独立理解的一组能力
-> 三级及以下模块：继续细分的业务流程、页面组、接口组或数据能力
-> 叶子模块：最小可交付功能模块
```

目录结构可以是一层，也可以是多层。最后一级目录才代表一个最小功能模块，必须包含 `module.md` 和 `changelog.md`。

```text
docs/modules/
  README.md
  _template/
    module.md
    changelog.md
    route-api-index.md
    page.md
    backend-slice.md
    traceability.md
  <一级大模块>/
    README.md
    route-api-index.md
    <二级模块>/
      module.md
      changelog.md
      pages/
      backend/
      traceability.md
```

如果项目规模较小，可以直接使用一层叶子模块：

```text
docs/modules/
  order-list/
    module.md
    changelog.md
```

如果项目规模较大，应保留中间层级的 `README.md` 作为模块组说明：

```text
docs/modules/
  trading/
    README.md
    order/
      README.md
      order-list/
        module.md
        changelog.md
      refund-review/
        module.md
        changelog.md
```

规则补充：

- `group` 只负责分组、菜单、共享边界和不做范围，可以有 `README.md`，不应承载执行任务的完整业务档案。
- `leaf` 才是开发、审查、发布判断和 changelog 的主要归属，必须有 `module.md` 与 `changelog.md`。
- 页面审计页和后端审计页是 leaf 下的 detail doc，不进入正式模块树；它们用于人工对照页面、API、代码文件和 AI 口径。
- `component` 可用于表示 `server`、`client` 这类端工程或运行应用，但它通常不是业务 leaf；业务任务应继续落到更细的 leaf。
- `cross-cutting` 用于权限、埋点、通知、配置、发布等横切能力；只有它能独立验收并有清晰边界时才作为 leaf，否则应作为共享边界写入相关 group。

## 大模块与小模块

一级大模块应选择项目中长期稳定的业务域或系统域，例如用户中心、订单交易、支付结算、设备管理、内容运营、报表分析、系统配置、消息通知。

一级大模块只描述边界和子模块菜单，不承载过细实现。它的 `README.md` 应说明：

- 大模块目标和业务角色。
- 覆盖哪些子模块，以及每个子模块的简短职责。
- 与其它大模块的关系。
- 共享规则，例如统一权限、状态、数据归属、发布约束。
- 不做范围，避免后续任务误归类。

二级及以下模块用于继续缩小范围。拆分依据可以是业务流程、用户角色、页面组、接口能力、数据对象或发布边界，但不要只按一次性任务、临时分支或单个按钮命名。

叶子模块是最小可交付功能模块。它应该满足：

- 有清晰业务目标和用户角色。
- 有相对独立的页面、接口、数据、配置或测试边界。
- 可以被一个 Story 或一组紧密相关 Task 交付。
- 变更后能明确判断需要更新哪些文档和验收项。
- 与兄弟模块的职责边界可以说清楚。

如果一个候选模块不满足这些条件，应继续拆成模块组和更小的 leaf。AI 自动生成模块时，不能因为缺少信息就把大模块当 leaf；缺失信息应写成待确认项。

## 合适的颗粒度

模块不应太大，否则 AI 和人都会被迫读取过宽上下文；模块也不应太小，否则维护成本会超过收益。

适合作为叶子模块的粒度：

- 一个可独立验收的业务能力，例如登录注册、订单列表、退款审核、设备绑定、报表导出。
- 一组高度内聚的页面和接口，例如订单查询页、详情页、筛选、导出共同组成订单列表模块。
- 一个明确的数据写入或状态流，例如支付回调、审批流转、库存扣减。
- 一个独立运行或发布风险明显的能力，例如文件导入、批量任务、外部系统同步。

可能太大的信号：

- 同时覆盖多个用户角色、多个业务对象和多个状态流。
- 同时覆盖多个端工程，例如后台管理、用户端和服务端所有接口。
- 名称是“用户中心”“订单管理”“服务端”“管理后台”“客户端”这类大域，但没有继续拆到具体流程。
- 一次普通任务需要读取大量无关页面、接口或表。
- 无法用几句话讲清“不做范围”。
- 需要多个负责人长期并行维护。
- 测试和发布无法收敛到明确路径。

可能太小的信号：

- 只包含一个字段、一个按钮、一个提示文案或一个纯样式改动。
- 没有独立验收价值，必须永远和兄弟模块一起变更。
- 没有清晰页面、接口、数据、配置或测试边界。
- 模块名称更像临时任务标题，而不是长期能力。

拆分时优先让每个叶子模块有“大事化小、小事化了”的感觉：任务能落到一个模块内完成，跨模块影响能被显式列出，遗留问题能放回对应边界。

## 文件职责

- `.maw/modules.yaml`：模块机器索引，记录 `module_key`、模块文档、父子关系、组件、app_key、页面路径、接口路径、数据表、配置、发布和测试边界。
- `.maw/module-candidates.yaml`：候选模块机器索引，记录 seed/candidate/provisional 模块、证据和提升条件。
- `docs/modules/<...>/<leaf>/module.md`：叶子模块档案，是人工和 AI 理解当前功能、实现程度、待办、页面/API/数据表边界的入口。
- `docs/modules/<group>/route-api-index.md`：一级模块轻量定位索引，把页面 URL、API、命令和关键文件映射到二级模块。
- `docs/modules/<...>/<leaf>/pages/`：二级模块内的前端页面审计页，用于按页面对照路由、组件、字段、按钮、状态和 API 调用。
- `docs/modules/<...>/<leaf>/backend/`：二级模块内的后端审计页，用于按后端文件、API 组或业务动作对照接口、服务、模型、权限、错误码和数据读写。
- `docs/modules/<...>/<leaf>/traceability.md`：二级模块内的追踪矩阵，把页面、API、后端文件、数据对象、测试和验收串起来。
- `.maw/capabilities.yaml`：公共能力机器索引，记录可复用 API、基类、服务、组件、脚本和治理协议；模块档案只引用 `capability_key`。
- `.maw/project-signals.yaml`：项目提示信号机器索引，给审计、巡检、大屏和 AI 前置读取结构化的待办、澄清、缺口、口径变更和风险摘要。
- `docs/planning/todos/active.md`：跨模块待办任务事实源，记录被当前业务闭环依赖但暂不实现、先假设已完成的缺口；模块档案只回链 TODO-ID。
- `docs/modules/<...>/<leaf>/ai-context.md`：可选 AI 专用上下文，只写读取路线、常见误判、执行提示和验证提示；不复制完整事实，不替代 `module.md`。
- `docs/modules/<...>/<leaf>/changelog.md`：叶子模块变更日志，用于记录 feature、fix、api、db、ui、config、release 等变更是否同步文档。
- `docs/modules/<group>/README.md`：大模块或中间模块组说明，只描述子模块菜单、共享规则和跨模块边界，不替代叶子模块档案。
- `docs/modules/_template/`：新增叶子模块时复制的模板，不应写入项目私有业务结论。
- `docs/modules/_discovery/`：渐进式模块发现区，不替代正式模块档案。

## 模块待办与全局待办

模块档案的“待办”章节只承载模块内部局部事项。只要待办被其它模块依赖、当前业务流程先假设它已完成、或完成/取消会影响其它模块联调，必须进入 `docs/planning/todos/active.md`。

推荐边界：

| 场景 | 记录位置 | 说明 |
| --- | --- | --- |
| 只影响当前 leaf，未被其它模块依赖 | `docs/modules/<module-key>/module.md` | 模块内局部待办 |
| 当前流程依赖它，但真实能力暂不实现 | `docs/planning/todos/active.md` | 写清当前假设、受影响模块和联调建议 |
| 完成或取消会影响多个模块、app_key、发布或验收 | `docs/planning/todos/active.md`，必要时创建 `records/<TODO-ID>.md` | 模块档案只回链 TODO-ID |
| 已完成、已取消或被替代 | `docs/planning/todos/closed.md` | 保留关闭原因和回归/联调建议 |

不要在多个模块档案中复制同一跨模块待办的完整事实。模块档案只写 TODO-ID、影响摘要和指向 `docs/planning/todos/active.md` 的回链，避免多人协作时几份说明互相漂移。

## 模块命名

模块目录和 `module_key` 使用英文小写短横线。`module_key` 应全局唯一，并优先表达业务能力，而不是代码层名称。

建议：

- 目录层级表达父子关系，例如 `trading/order/order-list/`。
- `module_key` 可以使用短横线全局唯一，例如 `order-list`；如果容易冲突，可以加业务前缀，例如 `trading-order-list`。
- 大模块和中间模块组可以有目录 `README.md`，但真正执行任务时应尽量落到叶子模块。
- 如果需要让 AI 也能定位大模块，可在 `.maw/modules.yaml` 中登记父模块；实际开发、审查和发布任务仍应优先定位到叶子模块。

不建议：

- 使用 `general`、`common`、`misc` 作为兜底模块。
- 按临时需求号、分支名或某一次会话命名模块。
- 把一个页面上的每个按钮都拆成独立模块。
- 把整个前端、整个后台或整个服务端长期作为唯一业务模块。

## AI 定位模块的方法

AI/Codex 开始任务前，应先根据任务输入缩小模块范围：

1. 如果任务给出 `module_key`，读取 `.maw/modules.yaml`，找到对应 `doc` 和 `changelog`。
2. 如果任务给出模块名，匹配 `modules[].name`、`modules[].key` 或父级目录说明。
3. 如果任务给出页面/组件路径，匹配 `frontend_paths`。
4. 如果任务给出接口/命令路径，匹配 `api_paths` 或 `backend_paths`。
5. 如果任务给出数据表/集合名，匹配 `table_names`。
6. 如果只能定位到大模块，继续读取该大模块 `README.md` 和子模块菜单，直到落到最可能的叶子模块。
7. 开发新 API、基类、组件、脚本或横切能力前，检查 `.maw/capabilities.yaml` 是否已有可复用 `capability_key`。
8. 如果任务包含待办、澄清、缺口、口径变更、风险或审计提示，检查 `.maw/project-signals.yaml` 和 `docs/planning/todos/active.md` 是否已有结构化记录。
9. 找不到模块时，不要把任务随手归到 `general`；应在最终说明中记录 `not_identified`，并建议补充 `.maw/modules.yaml` 和对应模块档案。

定位模块后，AI 只读取最小必要的模块档案、相关代码和相关设计文档。`docs/archive/**` 默认不作为定位依据。

## AI 专用上下文

默认不为每个模块创建 AI 副本，也不把现有 `module.md` 批量复制成 `_ai` 后缀文件。原因是双份完整档案会快速漂移，反而让 AI 不知道哪个事实可信。

当出现下列情况时，可以按需新增 `docs/modules/<...>/<leaf>/ai-context.md`，并可在 `.maw/modules.yaml` 中用可选字段 `ai_doc` 指向它：

- `module.md` 很长，AI 只需要固定读取路线和执行提示。
- 某模块经常被误归类、误读边界或误判发布影响。
- 模块有复杂跨端、跨客户仓、跨发布环境或跨权限的注意事项。
- Reviewer 希望给 AI 一份短小的检查清单。

`ai-context.md` 只写 AI 读取路线、常见误判、执行提示、验证提示和收口注意事项。真实业务目标、页面/API/数据表边界、实现程度和待办仍写在 `module.md`；变更历史仍写在 `changelog.md`。如果三者冲突，以 `.maw/modules.yaml`、`module.md` 和当前代码为准，并同步修正 `ai-context.md`。

## 新增模块步骤

1. 先从项目目标或迭代目标生成模块树草案。
2. 对每个候选节点填写拆分判定表，确认 `group`、`leaf` 或 `cross-cutting`。
3. 如果一级大模块不存在，创建 `docs/modules/<一级大模块>/README.md`，写清目标、子模块菜单、共享规则和不做范围。
4. 判断当前需求是否还能继续拆小；如果能，继续创建中间目录和 `README.md`，不要生成 leaf。
5. 到达最小可交付功能时，才创建叶子模块目录。
6. 从 `docs/modules/_template/module.md` 复制到叶子目录的 `module.md`。
7. 从 `docs/modules/_template/changelog.md` 复制到叶子目录的 `changelog.md`。
8. 如果模块复杂或 AI 需要固定读取提示，可从 `docs/modules/_template/ai-context.md` 复制到叶子目录的 `ai-context.md`；普通模块不要创建。
9. 在 `.maw/modules.yaml` 新增或更新 `modules[]`，至少填写 `key`、`name`、`type`、`doc`、`parent_key`、路径边界和测试边界；只有 leaf 必须填写 `changelog`，复杂模块可选填 `ai_doc`。
10. 更新父级模块组 `README.md` 的子模块菜单，确保 AI 能从 group 继续定位到 leaf。
11. 填写模块目标、实现程度、页面/API/数据表边界、配置与运行边界、测试/验收要求。
12. 如果接入 issue/PM 系统，在 `.maw/modules.yaml` 的 `external_refs.pm_story_ids` / `external_refs.pm_task_ids` 或模块档案中记录映射。
13. 新增页面、接口、表、状态流、配置或发布规则时，同步判断是否更新模块档案、changelog 和已存在的 `ai-context.md`。

## 模块组 README 模板

大模块或中间模块组的 `README.md` 可以从 `docs/modules/_template/group-README.md` 复制，建议使用以下结构。该文件应作为会话入口菜单，控制 AI 只在需要时继续读取叶子模块详情：

```md
# 模块组：<模块组名称>

## 目标

## 用户角色

## 子模块菜单

| 子模块 | module_key | 类型 | 职责 | 不负责 | 何时继续读取详情 | 文档 |
| --- | --- | --- | --- | --- | --- | --- |

## 共享边界

- 页面/入口：
- API/命令：
- 数据对象：
- 权限/状态：
- 配置/发布：

## 与其它模块的关系

| 外部模块 | 关系 | 边界 |
| --- | --- | --- |

## 拆分规则

- 什么时候应新增子模块：
- 什么时候应合并回已有子模块：
- 待确认问题：
```

## 同步模板到已有项目

同步本目录到已有项目时，应保持 additive：

- 可以直接补齐 `docs/modules/_template/`、`docs/modules/README.md` 和缺失的 `.maw/modules.yaml` 初始建议。
- 如果已有项目已经有 `docs/modules/<...>/module.md`，不要覆盖；只补缺失章节、生成迁移说明或交给人工合并。
- 可以新增大模块或中间模块组 `README.md` 来说明层级和子模块菜单，但不要擅自移动已有叶子模块目录，除非用户明确要求重构目录。
- 不移动历史文档到 `docs/archive/`，除非用户明确要求。
- 不覆盖 `.maw/secrets.yaml`、`.maw/*.local.yaml`、客户仓库映射和 `code/<component>` 业务代码。
