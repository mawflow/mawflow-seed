# AI 模块档案规则

本文件定义 AI/Codex 在开发、审查、修 bug、发布检查和模板同步任务中使用模块档案的规则。

## 执行前定位

1. 不允许在任务开始时全量读取 `docs/modules/**`；默认只读 `.maw/modules.yaml`、`docs/modules/README.md`、相关一级模块 `README.md` 和必要的子模块菜单。
2. 如果任务里有 `module_key`，必须先读 `.maw/modules.yaml`，再读取对应 `doc` 指向的叶子模块档案；没有定位到叶子模块前，不读取所有模块详情。
3. 如果用户提到模块名、页面名、页面路径、接口名、接口路径、命令名、数据表名或集合名，必须先尝试从 `.maw/modules.yaml` 定位模块。
4. 如果只能定位到一级大模块，先读取该一级模块 `README.md`；当任务输入是页面 URL、API、命令或文件路径时，再读取同目录 `route-api-index.md` 快速定位二级模块。
5. 如果只能定位到中间模块组，先读取该模块组 `README.md` 的子模块菜单，按需继续向下定位；只有选中具体叶子模块或需要确认跨模块影响时，才读取 `module.md` 和 `changelog.md`。
6. 定位后只读取最小必要上下文：对应叶子模块档案、必要 changelog、相关代码路径和必要设计文档；涉及具体页面或后端审计时，再读取二级模块内的具体 `pages/`、`backend/` 或 `traceability.md`。
7. 如果 `.maw/modules.yaml` 配置了 `ai_doc`，或叶子目录下存在 `ai-context.md`，且当前任务是实现、审查、修 bug、发布判断或该模块容易被 AI 误读，可在读取 `module.md` 后读取该 AI 专用上下文。
8. 找不到模块时，不允许为了省事把所有任务归到 `general`；应记录待确认，并建议补充 `.maw/modules.yaml`、一级模块 `route-api-index.md` 或模块候选。
9. `docs/archive/**` 默认不作为当前实现依据，也不自动读取。

禁止行为：

- 使用“读取全部模块文档”来建立项目上下文。
- 在只需要大模块菜单时读取所有叶子模块 `module.md`。
- 给所有模块批量复制 `_ai` 后缀档案，或把 `module.md` 的完整事实复制到 AI 专用文件。
- 把一级模块 `route-api-index.md` 写成详细页面规格或 API 设计文档；它只负责 URL/API/命令到二级模块的定位。
- 把 `pages/` 或 `backend/` 下的审计页当作正式模块，或为每个按钮、字段、微小接口创建 leaf。
- 默认读取兄弟模块详情；只有共享接口、共享数据表、共享状态流、共享配置、发布覆盖或明确跨模块影响时才读取。
- 把 `stale` 或 `deprecated` 的模块文档当作当前事实源；这类文档只能用于历史追溯或迁移判断。

## 执行中维护

发生以下变化后，必须判断是否更新对应模块档案和 changelog：

- 页面、路由、组件、菜单或用户流程变化。
- API、命令、事件、状态流、权限或错误码变化。
- 数据表、集合、字段、模型、迁移或读写职责变化。
- `.maw` 配置、组件配置、环境变量、AI 调试入口、发布覆盖层变化。
- external_mapped 客户仓库同步边界、脱敏规则或交付包规则变化。
- repository_mirrors 仓库级镜像目标、自动同步开关、同步方向或脱敏规则变化。
- repository_publish_mirrors 公开发布镜像目标、发布模式、版本/tag 闸门或脱敏导出规则变化。
- component_mirrors 组件镜像仓库目标、同步方向、脱敏规则或单向同步边界变化。
- 新增、完成或取消被其它模块依赖、当前流程先假设已完成的待办任务；跨模块待办事实源是 `docs/planning/todos/active.md` 和 `closed.md`，模块档案只回链 TODO-ID。
- 新增、复用、废弃或重命名公共能力、API、基类、服务、组件、脚本或治理协议；公共能力事实源是 `.maw/capabilities.yaml`，模块档案只引用 `capability_key`。
- 新增对人或 AI 有提示意义的澄清、缺口、口径变更、风险、审计提示或 AI 前置条件；结构化信号写入 `.maw/project-signals.yaml`，必要时同步 `docs/ai-instructions/` 候选台账。
- 模块文档本身的证据状态变化，例如从 `pending_confirm` 提升为 `confirmed`、发现路径已过期标记为 `stale`、确认废弃标记为 `deprecated`，或完成一次 `#模块地图` 审计。

需要更新时，优先更新：

- `docs/modules/<module-key>/module.md`
- `docs/modules/<module-key>/changelog.md`
- 归属一级模块的 `docs/modules/<group>/route-api-index.md`，当页面 URL、API、命令、关键文件或 owner_module 变化时更新。
- 受影响二级模块的 `docs/modules/<group>/<module-key>/pages/<page-key>.md`，当具体页面字段、按钮、交互、状态或 API 调用变化时更新。
- 受影响二级模块的 `docs/modules/<group>/<module-key>/backend/<api-group-or-file>.md`，当 API、后端文件、服务、权限、错误码或数据读写变化时更新。
- 受影响二级模块的 `docs/modules/<group>/<module-key>/traceability.md`，当页面到 API、后端文件、数据对象、测试或跨模块影响链路变化时更新。
- 已存在且被本轮事实影响的 `docs/modules/<module-key>/ai-context.md`
- 相关 `docs/design/`、`docs/planning/`、`docs/delivery/` 或 `.maw` 说明
- 被依赖但暂不实现的跨模块待办：`docs/planning/todos/active.md`、必要的 `records/<TODO-ID>.md`，完成或取消后移入 `docs/planning/todos/closed.md`
- 公共能力和技术地图：`.maw/capabilities.yaml`、`docs/capabilities/`、`docs/technical-map/README.md`
- 项目提示信号：`.maw/project-signals.yaml`、`docs/project-signals/`、必要的 `docs/ai-instructions/experience-candidates.md` 或 `keyword-candidates.md`
- 模块地图审计报告：`docs/modules/_audits/`，当执行 `#模块地图：审计`、`#模块地图：清理过期`、`#模块地图：变更影响`、发布前检查或发现结构性缺口时更新。

更新模块档案、一级索引或 detail docs 时，应同步维护证据字段：

- `doc_status`：`confirmed` / `inferred` / `pending_confirm` / `stale` / `deprecated`
- `confidence`：`high` / `medium` / `low`
- `last_verified_commit`：最近一次和代码、路由、API、测试或发布事实对齐的 commit。
- `last_verified_at`、`last_verified_by`
- `source_paths` / `source_commits`
- `last_audit_id` / `audit_docs`

证据不足时宁可写 `pending_confirm` 或 `inferred`，不得为了让文档看起来完整而写成 `confirmed`。发现路径、API、页面或 owner 已失效但未完成确认时，先标记 `stale`；确认废弃或迁移后标记 `deprecated` 并写明替代路径。

不更新时，最终说明必须写明原因，例如“只调整错别字，不影响模块边界”或“只新增检查脚本，模块业务边界未变化”。

AI 专用上下文是可选文件，建议命名为 `ai-context.md`，或由 `.maw/modules.yaml` 的 `ai_doc` 指向。它只记录读取路线、常见误判、执行提示、验证提示和收口注意事项；真实页面/API/数据表边界仍以 `module.md` 为准，历史变化仍以 `changelog.md` 为准。

页面和后端审计页也是可选的渐进式 detail docs。新增或改造模块地图时，先保证一级/二级模块与 owner 关系可读，再补 `route-api-index.md`；只有高频、复杂、正在审计或容易误读的页面/API 需要立即创建详细审计页。历史项目缺少这些 detail docs 时默认 warning-only，不阻塞普通开发。

定期治理使用 `#模块地图`：

- `#模块地图：检查`：查漏补缺、计算 `module_map_score`，必要时写 `docs/modules/_audits/`。
- `#模块地图：审计 <module_key>`：聚焦某个二级模块，对照前端页面、后端文件、API、测试和 AI 边界。
- `#模块地图：清理过期`：先标记 `stale/deprecated` 并输出候选，删除前需要证据和人工确认。
- `#模块地图：变更影响 <commit_range>`：根据提交范围更新受影响的模块索引、changelog 和审计报告。
- `#模块地图：发布前检查`：关键 `pending_confirm`、`stale` 或 owner 冲突必须进入发布风险清单。

## 组件应用与发布判断

每次任务完成时，必须判断本轮改动命中了 `code/` 下哪些组件应用，尤其是需要发布的组件。判断来源包括：

- 改动路径命中 `code/<component>`、`release/<component>`、`docs/ai-coding/component-guides/<component>.md` 或 `code/<component>/.maw.component.yaml`。
- `.maw/modules.yaml` 的 `component_refs`、`app_keys`、`config_paths`、`release_paths` 或 `test_paths` 指向某个组件。
- `.maw/app-runtime.yaml`、`.maw/components.yaml`、`.maw/releases.yaml`、`release/rules.yaml` 或同步脚本变更会影响某个 app_key 的启动、构建、发布、同步或运行配置。

发布判断规则：

- 如果本轮改动会改变某个组件的代码、运行配置、构建产物来源、发布覆盖层、部署脚本、外部同步边界或线上可见行为，该组件应判定为“需要更新发布”。
- 只有本轮已经执行该组件的发布动作，并完成目标环境验证或明确的发布验收，才写“当前已发布”。
- 如果需要发布但本轮没有执行发布，必须写“当前未发布”。
- 如果无法确认目标环境是否已经包含本轮改动，不得猜测为已发布；应写“当前未发布/未验证”，并说明需要人工或发布流程确认。
- 如果某组件需要发布且当前未发布或未验证，最终说明必须同时输出可复制的 `release_commands`。发布指令必须先通过 `.maw/components.yaml` 的 `release_ref` 定位发布配置，再读取聚合后的 `.maw/releases.yaml` 的 `releases.components.<app_key>.release_commands`、`releases.defaults.version_tracking` 和 `code/<app_key>/.maw.component.yaml` 的 `release.commands`；默认环境来自组件 `release.default_environment` 或全局 `releases.defaults.default_environment`。多个 app_key 需要发布时，必须按 app_key 分别列出多条指令，用户可以复制其中一条或多条选择部分发布；目标环境不明确时，列出默认发布指令和可选环境指令，不要临时编造配置外环境。用户说 `发布测试`、`发布上线`、`发布生产` 或 `发布生成` 且未指定组件时，先读 `releases.defaults.release_command_aliases` 和对应 `environments.<env>.remote_server.default_release_components`，再按 `artifacts/release-state/<env>/<app_key>.json` 的发布版本状态和组件路径差异筛选实际发布名单；`发布测试` 是本地调试版本，需给可访问调试地址；`发布上线` 是部署到 `remote_staging_server` 的编译包部署测试，仍属于测试，需给线上可访问地址；`发布生产` 是部署到 `remote_production_server` 的生产发布，涉及生产环境安装或版本上线必须人工审计；上线和生产发布前必须确认本地候选 commit 等于发布来源远端分支。
- 如果某组件需要发布且当前未发布或未验证，最终说明必须输出 `release_confirmation_prompt`，在收口末尾询问用户是否“确认发布全部”，例如“本轮需要发布 server、client 才会生效。是否确认发布全部？回复‘确认发布全部/确认/是’将发布全部；如只发布部分，请复制上方对应组件的 #发布 指令。”单个 app_key 时也使用同一语义，回复“确认发布全部/确认/是”表示发布该组件。
- 用户在同一会话中回复“确认发布全部、是、确认、全部发布、立即发布、发布生效”时，若 `release_confirmation_prompt` 已明确列出全部待发布组件，则 AI 必须发布全部待发布组件；用户复制某条或多条 `#发布` 指令时，只发布对应 app_key。AI 不得停留在说明层面；在 app_key、目标环境和 SQL/迁移范围明确时，按 `docs/ai-instructions/instructions/release-component.md` 执行发布。若缺少关键信息，先只补问缺口。
- 如果本轮未命中任何 `code/` 组件应用，应写“未命中 code 组件应用，无需更新发布”。

## 最终说明格式

AI 最终说明必须包含：

```text
experience_lookup:
  checked: yes/no
  matched:
    - <EXP-XXX 或 none>
  detail_read:
    - <路径或 none>
  updated:
    - <路径或 none>
module_key: <涉及模块或 not_identified>
module_dossier_updated: yes/no/not_required
module_dossier_reason: <原因>
updated_module_docs:
  - <路径>
hit_code_components:
  - <component>/<app_key 或 none>
release_update_status:
  - <本轮修改了 <app_key> 的 <代码/运行配置/发布覆盖/部署脚本/线上可见行为>，需要发布 <app_key> 才会生效，当前已发布/当前未发布/当前未发布或未验证；或未命中 code 组件应用，无需更新发布>
release_commands:
  - <app_key>: <按配置列出 #发布：发布 <app_key>（默认 <env>）、#发布：发布 <app_key> 到 <env_option> 以及可用中文口令 #发布测试/#发布上线/#发布生产/#发布生成；多个 app_key 分别列出，用户可复制其中一条或多条；或 none>
release_confirmation_prompt:
  - <本轮需要发布 <app_key 列表> 才会生效。是否确认发布全部？回复“确认发布全部/确认/是”将发布全部；如只发布部分，请复制上方对应组件的 #发布 指令；或 none>
todo_task_update_status:
  - <新增/完成/取消/查询了哪些 TODO-ID；或未涉及被依赖但暂不实现的待办任务；如发现应登记但未登记，写明原因>
health_context_update_status:
  - <新增/更新/审计/未涉及哪些 .maw/health 记录 ID；是否需要把模块健康问题、审计缺口或验收缺口沉淀到项目健康上下文>
capability_map_update_status:
  - <新增/复用/废弃/未涉及哪些 capability_key；是否更新 .maw/capabilities.yaml 或不更新原因>
project_signal_update_status:
  - <新增/更新/关闭/未涉及哪些 signal_id；是否同步待办、澄清、缺口、口径变更或 AI 前置条件>
repository_identity_update_status:
  - <新增/更新/判断/未涉及 declared roles、detected roles、角色目录覆盖和高风险约束>
seed_repository_upgrade_suggestions:
  - <未发现新的种子仓库升级建议；或已记录到 docs/seed-repository-upgrade-candidates.md，并说明使用场景、理由和兼容性要求>
```

如果涉及多个模块，`module_key` 可写逗号分隔列表，并在 `updated_module_docs` 中列出所有更新的模块档案或 changelog。

## Reviewer 检查点

Reviewer 应检查：

- 改动路径是否落在 `.maw/modules.yaml` 登记的模块边界内。
- 页面/API/DB/状态流/配置/发布变化是否同步模块档案。
- 页面 URL、API、命令或关键文件 owner_module 变化是否同步一级模块 `route-api-index.md`。
- 具体页面或后端审计相关变化是否同步二级模块的 `pages/`、`backend/` 或 `traceability.md`，且未把这些 detail docs 当成正式模块。
- 最终说明是否包含 `experience_lookup`，且未绕过 `experience-index.md` 主动读取大型 `solutions/**` 详情。
- 最终说明是否列出本轮修改的 `code` 组件应用，并对需要发布才会生效的组件使用“本轮修改了 <app_key> 的 <内容>，需要发布 <app_key> 才会生效，当前已发布/当前未发布”这类明确字眼。
- 需要发布且当前未发布或未验证时，最终说明是否按 app_key 给出可复制 `#发布` 快捷指令，并在收口末尾询问是否“确认发布全部”，说明回复“确认发布全部/确认/是”发布全部、复制对应指令可选择部分发布。
- 中文环境口令未指定组件时，是否用发布版本状态和组件路径差异计算实际发布名单；上线/生产是否明确执行本地最新代码阻塞检查。
- 不更新模块档案的理由是否可信。
- 如果当前业务流程依赖暂未实现的能力，是否登记到 `docs/planning/todos/active.md`，并在模块档案中只回链 TODO-ID。
- 公共能力是否登记到 `.maw/capabilities.yaml`，模块档案是否只引用 `capability_key`。
- 对人或 AI 有提示意义的澄清、缺口、口径变更、风险和审计提示是否登记到 `.maw/project-signals.yaml`，并能被 `ops/scripts/extract-project-metadata.py` 提取。
- 是否错误读取或引用了 `docs/archive/**` 作为当前实现依据。
