# 指令：模块地图初始化、检查、审计与规范改造

## 元信息

- ID：TINST-036
- 类型：项目指令
- 状态：启用
- 维护位置：`docs/ai-instructions/instructions/module-map.md`
- 推荐调用：`#模块地图`
- 精确调用：`#T036` 或 `#T036/<目标范围>`
- 触发词：#模块地图、模块地图、初始化 modules、检查 modules、规范改造 modules、modules 规范改造、模块地图初始化、模块地图检查、模块地图审计、模块地图查漏补缺、清理过期模块文档、页面 URL 索引、API 索引、route-api-index、页面审计页、后端审计页、模块 traceability、按页面审计模块、按 API 审计模块、module_map_score
- 适用范围：对已有项目的 `docs/modules/`、`.maw/modules.yaml` 和模块候选进行初始化、检查、审计、查漏补缺、清理过期和规范化改造；按一级模块 URL/API 索引、二级模块事实源、页面/后端审计页、commit 证据和渐进式补全策略维护模块地图。

## 目标

让 AI 在已有项目中建立可渐进维护、可审计、可追溯的模块地图：

- 根目录维护一级模块入口、跨一级模块关系和审计报告入口。
- 一级模块维护二级模块菜单、共享边界和 `route-api-index.md`。
- 二级模块维护 `module.md`、`changelog.md`、页面索引、后端/API 索引、业务流程、AI 边界指引和必要的 detail docs。
- 页面和后端审计页只作为二级模块下的证据维度，不升级为正式模块。
- 文档记录 `doc_status`、`confidence`、`last_verified_commit`、`source_paths` 和必要的 `last_audit_id`。
- 证据不足时进入 `.maw/module-candidates.yaml` 和 `docs/modules/_discovery/`，不强行补全。

## 子模式

用户只说 `#模块地图` 时，默认执行 `检查`；用户要求“完成改造/初始化”时可以在检查后继续落地改造。

| 调用 | 用途 | 默认写入 |
| --- | --- | --- |
| `#模块地图：初始化` | 从已有 `.maw/modules.yaml`、路由/API/README 和用户给定范围建立一级/二级模块地图骨架 | `.maw/modules.yaml`、一级 `README.md`、必要的 `route-api-index.md`、模块候选 |
| `#模块地图：检查` | 只读或低风险检查模块地图完整性、过期风险和评分 | 默认输出检查表；发现结构性缺口时写 `docs/modules/_audits/` |
| `#模块地图：审计 <module_key>` | 对单个二级模块或一级模块做细审，检查页面/API/后端/traceability/AI 边界 | 模块档案、detail docs、审计报告 |
| `#模块地图：查漏补缺` | 根据检查结果补缺失字段、索引、回链和待确认项 | 只补有证据的缺口，未知项写 `pending_confirm` |
| `#模块地图：清理过期` | 标记或移除已过期、孤立、被替代的模块文档 | 审计报告、`stale` / `deprecated` 标记；删除前需人工确认 |
| `#模块地图：变更影响 <commit_range>` | 依据提交范围识别页面/API/路径变化并更新模块地图 | 受影响索引、模块档案、changelog、审计报告 |
| `#模块地图：发布前检查` | 发布前确认页面/API/模块边界、待确认项和 stale 文档风险 | 发布前风险清单；必要时阻塞发布 |

## 输入要求

- 必需输入：目标项目仓库，或当前 Codex 会话所在仓库。
- 推荐输入：子模式、需要治理的一级模块、页面 URL、API 前缀、app_key、代码路径、已有模块文档路径、commit range、是否只检查不改。
- 可选输入：需求文档、原型、Story/Task、近期任务包、用户确认的模块边界。
- 缺失时处理：能从 `.maw/modules.yaml`、`docs/modules/`、代码路由和 API 路径确认的先确认；无法确认 owner_module、二级模块边界或是否可独立验收时，写 `pending_confirm` 或进入模块候选，不编造事实。

## 执行步骤

1. 先读取启动上下文、`.maw/modules.yaml`、`.maw/module-candidates.yaml`、`docs/modules/README.md`、`docs/modules/_discovery/README.md`、`docs/modules/_audits/README.md`、`docs/ai-coding/module-dossier-rules.md`、`docs/ai-instructions/instructions/split-module-tree.md` 和 `docs/ai-instructions/instructions/progressive-module-discovery.md`。
2. 读取模板：`docs/modules/_template/group-README.md`、`route-api-index.md`、`module.md`、`changelog.md`、`page.md`、`backend-slice.md`、`traceability.md` 和 `docs/modules/_audits/_template.md`。只在复杂模块需要 AI 读取提示时读取 `ai-context.md`。
3. 盘点现状：
   - `.maw/modules.yaml` 中已有 group / leaf / component / cross-cutting，以及 `doc_status`、`last_verified_commit`、`detail_docs` 等字段。
   - `docs/modules/` 下已有一级模块、二级模块、孤立 `module.md`、过宽 component 档案、候选区和审计报告。
   - 任务指定范围内的页面 URL、API 路径、命令、后端文件、表名、测试路径和相关 commit。
   - 不全量读取 `code/**`；优先从路由文件、API 注册文件、README、模块档案、`.maw` 索引和用户指定路径抽取证据。
4. 建立或更新“模块地图检查表”：
   - 一级模块是否清晰。
   - 二级模块是否是可独立交付 leaf。
   - 页面 URL/API 是否能通过一级 `route-api-index.md` 定位到二级模块。
   - 二级模块是否有 `module.md`、`changelog.md`、AI 边界指引和必要索引。
   - detail docs 是否存在、缺失是否可接受、哪些需要优先补。
   - `doc_status`、`confidence`、`last_verified_commit`、`source_paths` 是否可信。
   - 不确定项进入待确认或候选模块，不阻塞可确认部分。
5. 计算 `module_map_score`：
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
6. 按子模式决定是否改造：
   - `检查` 默认不改文件，除非用户明确要求落地或发现已有报告需要更新。
   - `初始化`、`查漏补缺`、`审计` 可以增量写入模板、索引和报告。
   - `清理过期` 删除文件前必须有证据和人工确认；未确认时只标记 `stale` 或列入审计报告。
   - `发布前检查` 遇到 `stale`、关键 `pending_confirm`、owner_module 冲突或发布影响未回链时，必须在收口中列为发布风险。
7. 改造目录：
   - 根目录只补一级模块入口、跨一级模块关系说明和 `_audits/`。
   - 一级模块补 `README.md` 和按需 `route-api-index.md`。
   - 二级模块补 `module.md`、`changelog.md`、页面/API/后端索引和 AI 边界指引。
   - 高频、复杂、正在审计或容易误读的页面/API 才创建 `pages/`、`backend/`、`traceability.md`。
8. 更新 `.maw/modules.yaml`：
   - group 可登记 `route_api_index`。
   - leaf 必须登记 `doc`、`changelog`、`parent_key`、`component_refs`、`app_keys` 和已知路径/API/表/配置/测试边界。
   - leaf 可登记 `detail_docs.page_docs`、`detail_docs.backend_docs`、`detail_docs.traceability_doc`。
   - 可选登记 `doc_status`、`confidence`、`last_verified_commit`、`last_verified_at`、`last_audit_id`、`audit_docs` 和 `lifecycle`。
   - 未知路径使用空列表，不猜测。
9. 证据不足时走渐进式补全：
   - 新线索写入 `.maw/module-candidates.yaml` 和 `docs/modules/_discovery/`。
   - `route-api-index.md` 可先写 `pending_confirm` 行。
   - detail docs 可以先不创建；在 `module.md` 写缺口和后续补齐条件。
10. 如果产生改动，同步更新相关 changelog、`docs/ai-instructions/experience-index.md` 中的模块地图经验索引、`PROJECT_COMMANDS.md` 和必要模板升级资产。
11. 最终说明写清：子模式、模块地图状态、`module_map_score` 摘要、已初始化/改造范围、过期或孤立文档、未补齐原因、候选模块、待确认问题、验证命令、是否仍需人工确认。

## 渐进式补全策略

模块地图不要求一次性完美。建议分四步：

1. `map-skeleton`：一级模块、二级模块、owner 关系和 `.maw/modules.yaml` 可定位。
2. `route-api-index`：一级模块能用 URL/API/命令定位二级模块。
3. `audit-detail`：高频、复杂、正在审计或易误读的页面/API 有 detail docs。
4. `traceability`：关键链路能从页面追到 API、后端文件、数据对象、测试和验收。

旧项目缺少第 2-4 步时默认 warning-only；新增或重构相关页面/API 时，应顺手向前补齐。`pending_confirm` 是合格中间态，不是失败；但发布前检查中命中关键流程时必须提示风险。

## 文档生命周期

- `confirmed`：有当前代码、路由、API、测试、发布记录或人工确认支撑。
- `inferred`：根据命名、相邻路径、历史档案或局部证据推断，仍需复核。
- `pending_confirm`：owner、边界、状态或来源尚不能确认。
- `stale`：文档可能已过期，例如路径不存在、路由迁移、API 下线或模块合并，但尚未完成确认。
- `deprecated`：确认废弃、合并或被替代，应写明 `superseded_by` 或删除计划。

AI 不得把 `stale` 或 `deprecated` 文档当作当前实现依据。确需读取时，只能用于追溯历史或迁移判断，并在结论中说明它不是当前事实源。

## 审计报告规则

- 报告目录：`docs/modules/_audits/`
- 模板：`docs/modules/_audits/_template.md`
- 推荐字段：`audit_id`、`audit_type`、`checked_commit`、`commit_range`、`module_map_score`、发现项、过期候选、待确认问题、整改动作和验证结果。
- `检查` 可以只输出会话检查表；发现结构性缺口、过期文档、发布前风险或执行 `审计/清理过期/变更影响` 时应落报告。
- 报告只记录审计结论，不替代 `.maw/modules.yaml` 或模块档案事实；事实变化必须回写对应源。

## 验证方式

- `.maw/modules.yaml` 可被 YAML 解析。
- `.maw/module-candidates.yaml` 可被 YAML 解析。
- 一级模块 `README.md` 包含子模块菜单；如有 URL/API 索引，`route-api-index.md` 存在且只写轻量定位。
- 每个 confirmed leaf 都有 `module.md` 和 `changelog.md`。
- `pages/`、`backend/` 和 `traceability.md` 如存在，能被 `module.md`、`route-api-index.md` 或 `.maw/modules.yaml` 追溯引用。
- `doc_status`、`confidence`、`last_verified_commit`、`source_paths` 没有把未知事实伪装成 confirmed。
- 没有新增 `general`、`misc`、`common` 兜底模块。
- 运行：

```bash
git diff --check
bash ops/scripts/check-template-module-docs.sh
bash ops/scripts/check-module-candidates.sh
```

种子仓库或模板协议改造还应运行：

```bash
bash ops/scripts/check-technical-map.sh
bash ops/scripts/check-ai-framework-consistency.sh
bash ops/scripts/check-local-boundary.sh
```

## 禁区

- 不得把一级业务域、端工程、整后台、整服务端、整用户中心或整订单管理当成唯一 leaf。
- 不得为了补地图而编造页面 URL、API、后端文件、表名、权限、状态流、测试、commit 或发布目标。
- 不得全量读取 `docs/modules/**` 或 `code/**` 来找灵感；按任务范围和索引逐层读取。
- 不得把 `route-api-index.md` 写成页面/API 详细设计。
- 不得把 `pages/`、`backend/` 或 `traceability.md` 当作正式模块树节点。
- 不得在没有证据和人工确认时删除历史模块文档；先标记 `stale` 并写审计报告。
- 不得覆盖目标项目已有 README、`code/`、真实 app_key、发布配置、仓库映射、secrets、`.local` 或人工确认的模块档案。

## 冲突与覆盖规则

- 与 `TINST-010 模块树拆分与模块档案生成` 冲突时，本指令负责“已有项目模块地图初始化、检查、审计和规范化改造”；`TINST-010` 负责具体模块树拆分和 leaf 生成。
- 与 `TINST-021 渐进式模块发现` 冲突时，证据不足部分走 `TINST-021`，已确认部分继续按本指令改造。
- 与 `TINST-033 文档写读契约与索引` 冲突时，本指令负责模块地图内容结构、证据链和审计评分，`TINST-033` 负责 docs front matter 和文档索引契约。
- 用户明确指定的业务边界优先；如果边界明显过宽，先提示风险并给出拆分建议。
- 当前代码、`.maw` 配置和 active 文档优先于旧模块草稿、过期审计报告或归档资料。

## 更新记录

- 2026-06-22：增强为带子模式、commit 证据、文档生命周期、审计报告和 `module_map_score` 的模块地图治理指令。
- 2026-06-22：创建。
