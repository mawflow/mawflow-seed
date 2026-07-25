---
doc_key: docs.modules.index
doc_type: governance
stage: development
status: active
owner: planner
tags:
  - modules
  - module-map
project_health:
  dimensions:
    - product_module_design
  evidence_level: canonical
read_contract:
  summary: "模块树、模块档案、集中变更日志和模块地图审计的唯一人工入口。"
  health_signal: "用于判断模块边界、证据、生命周期和集中日志是否完整。"
  consumes:
    - .maw/modules.yaml
    - .maw/module-candidates.yaml
  produces:
    - docs/modules/<module>/module.md
    - docs/changelogs/<module_key>.md
  ai_read_hint: "需要定位、创建、检查、审计或重构模块地图时读取。"
---

# 模块地图与模块档案

## 模块树优先协议

模块地图先建立可逐层读取的树，再为最小可交付 `leaf` 建档：

```text
项目模块地图
  -> group README（分组、菜单、共享边界）
    -> route-api-index.md（URL/API/命令轻量定位）
      -> leaf module.md（当前事实与边界）
        -> pages/、backend/、traceability.md（按需审计维度）
  -> docs/changelogs/<module_key>.md（集中历史）
```

不要把端工程、整个后台、整个服务端或“用户中心”等大域长期当作唯一 `leaf`；也不要把单个按钮、字段或一次性任务拆成模块。证据不足的候选先进入 `.maw/module-candidates.yaml` 和 `_discovery/`，不得为了填满地图编造 URL、API、表或状态流。

## 唯一事实分工

| 位置 | 职责 | 禁止内容 |
| --- | --- | --- |
| `.maw/modules.yaml` | 机器路由、父子关系、owner、路径/API/表/配置/测试边界、证据状态 | 长篇说明、执行流水 |
| `docs/modules/<...>/<leaf>/module.md` | 当前业务目标、负责/不负责、页面/API/数据/运行边界、验收和证据 | 历史表、逐日任务流水 |
| `docs/changelogs/<module_key>.md` | 实质变更历史 | 例行样式、措辞和测试补充 |
| `route-api-index.md` | URL/API/命令到 owner_module 的轻量映射 | 字段、按钮、入参出参全文 |
| `pages/`、`backend/`、`traceability.md` | 复杂或正在审计模块的细粒度证据 | 新的正式模块节点 |
| `ai-context.md` | 可选的最小 AI 读取提示 | `module.md` 的复制品 |

## 集中 changelog

所有模块日志统一放在：

```text
docs/changelogs/<module_key>.md
```

模块页只保留：

```text
changelog_path: docs/changelogs/<module_key>.md
changelog_time: <带时区 ISO 8601 时间>
```

机器索引使用相同字段。`changelog_time` 只在集中日志内容实际变化时更新；空跑或重复迁移不得刷新。

### 旧格式读到即迁移

任何模块档案、模块地图、变更影响或 changelog 规则开始时，先执行：

```bash
python3 ops/scripts/migrate-module-changelogs.py plan --format json
```

发现旧 `docs/modules/**/changelog.md`、旧 `changelog:` 字段或 module.md 内嵌“最近变更摘要/变更记录”时，规则执行者必须自动继续：

```bash
python3 ops/scripts/migrate-module-changelogs.py migrate --execute --format json
```

迁移先合并、去重和写入新引用，验证成功后才删除旧格式；冲突时 fail closed。再次执行必须零变更。完整规则见 `docs/changelogs/README.md`。

## 模块类型与粒度

- `group`：分组、菜单、共享边界和不做范围；只需 README。
- `leaf`：可由一个 Story 或一组强相关 Task 独立交付和验收；必须有 `module.md` 与集中 changelog。
- `component`：`server`、`client` 等端工程或运行应用，可作为路径和 app_key 索引，但通常不是业务 leaf。
- `cross-cutting`：权限、通知、配置、发布等横切能力；只有能独立验收且边界稳定时才建 leaf。

一个合格 leaf 应满足：业务目标可一句话说明；负责与不负责清楚；页面/API/数据/状态或发布边界相对独立；测试和验收可落到稳定入口；兄弟模块只通过显式契约协作。

## 证据与生命周期

模块索引和档案使用同一组状态：

- `doc_status`: `confirmed` / `inferred` / `pending_confirm` / `stale` / `deprecated`
- `confidence`: `high` / `medium` / `low`
- `last_verified_commit`
- `last_verified_at`
- `last_verified_by`
- `source_paths` / `source_commits`
- `last_audit_id` / `audit_docs`

`stale` 表示路径、路由、API 或 owner 可能已漂移但未完成确认；`deprecated` 表示已确认废弃、合并或被替代。两者都不能作为当前实现事实源。未知证据保持 `pending_confirm`，不要伪造 commit 或把推断写成 confirmed。

模块内部局部待办可留在 `module.md`。被其它模块依赖、当前流程先假设已完成或取消后会影响联调的待办，以 `docs/planning/todos/active.md` 为事实源；完成、取消或替代后进入 `docs/planning/todos/closed.md`，模块页只回链 TODO-ID。

## 渐进式补全

模块地图分四层推进：

1. `map-skeleton`：group、leaf 和 owner 关系。
2. `route-api-index`：URL/API/命令轻量定位。
3. `audit-detail`：高频、复杂或风险模块的页面/后端审计页。
4. `traceability`：页面到 API、后端、数据、测试和验收的链路。

缺 detail docs 默认 warning-only；关键流程在发布前仍为 `pending_confirm`、`stale` 或 owner 冲突时必须进入风险清单。

## 模块地图审计

审计报告放在 `docs/modules/_audits/`，使用 `_template.md`。`module_map_score` 至少包含：

- `route_index_coverage`
- `api_owner_coverage`
- `detail_doc_coverage`
- `traceability_coverage`
- `confirmed_ratio`
- `pending_confirm_count`
- `stale_docs_count`
- `deprecated_docs_count`
- `orphan_docs_count`
- `missing_changelog_count`
- `ai_boundary_coverage`

可用模式：`#模块地图：检查`、`#模块地图：审计 <module_key>`、`#模块地图：查漏补缺`、`#模块地图：清理过期`、`#模块地图：变更影响 <commit_range>`、`#模块地图：发布前检查`。删除或合并旧模块前必须有代码/路由/API/人工确认等证据，并在审计报告记录替代关系。

## AI 定位顺序

1. 从 `.maw/modules.yaml` 按 `module_key`、名称、页面/API/命令、文件或表定位。
2. 只能落到 group 时读取对应 README；输入包含 URL/API 时再读 `route-api-index.md`。
3. 只读取命中的 `module.md`；需要追溯实质变化时按 `changelog_path` 读取集中日志。
4. 具体页面或后端审计只读命中的 detail doc。
5. 找不到稳定模块时记录 `module_candidate`，不得落入 `general`、`misc` 或 `common`。
6. `docs/archive/**` 默认不作为当前定位依据。

## 新增 leaf

1. 完成 group / leaf / cross-cutting / defer 判定。
2. 从 `_template/module.md` 创建 leaf `module.md`。
3. 从 `_template/changelog.md` 创建 `docs/changelogs/<module_key>.md`。
4. 在 `.maw/modules.yaml` 登记 `key`、`name`、`type`、`doc`、`changelog_path`、`changelog_time`、`parent_key`、组件/app_key 与已知边界；未知列表留空。
5. 更新父级菜单；有 URL/API 线索时更新 `route-api-index.md`。
6. 只有复杂或正在审计的模块才创建 detail docs / `ai-context.md`。
7. 运行集中日志检查和模块地图校验。

## 验证

```bash
python3 ops/scripts/migrate-module-changelogs.py check --format json
bash ops/scripts/check-template-module-docs.sh
bash ops/scripts/check-module-candidates.sh
```

验证至少确认：YAML 可解析；confirmed leaf 的 `doc` 与 `changelog_path` 存在；`changelog_time` 可解析且带时区；没有旧模块目录 changelog、旧字段或内嵌历史段；route/API owner 不被无证据重复声明；detail docs 可回链；没有新增兜底模块。

## 已有项目增量升级

已有项目只做审计后的语义合并。保留真实 README、`code/`、app_key、发布配置、仓库映射、secrets、`.local/`、人工确认边界和现有 WIP。集中日志迁移可以自动执行，但模块重命名、合并、拆分和 owner 变化仍需证据；一对多历史归属不得自动猜测。
