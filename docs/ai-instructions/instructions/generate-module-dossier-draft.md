# 指令：生成模块档案初版

## 元信息

- ID：TINST-005
- 类型：项目指令
- 状态：启用
- 维护位置：`docs/ai-instructions/instructions/generate-module-dossier-draft.md`
- 触发词：生成模块档案初版、生成 module.md 初版、根据描述生成模块档案、模块初稿、模块档案草稿
- 适用范围：用户在 Codex 会话中用简短描述要求生成或补齐 `docs/modules/<module-key>/module.md` 初版。

## 便捷调用

在 Codex 会话中可以直接使用这一句：

```text
生成模块档案初版：<用一两句话描述这个模块的业务目标、用户角色、主要页面/接口/数据对象；如已知可补 module_key、组件、页面路径、接口路径>
```

示例：

```text
生成模块档案初版：module_key=order-management，模块名=订单管理。运营人员查看订单、筛选订单状态、处理退款和导出订单；涉及前端订单页面、server 订单接口和 orders 表。
```

## 目标

根据用户的一段简短描述，生成可维护的模块档案初版，至少能说明模块目标、当前边界、待确认项、页面/API/数据表线索、任务与验收要求，并能被后续 Codex 会话通过 `.maw/modules.yaml` 定位。

## 输入要求

- 必需输入：模块业务目标或模块名称二选一。
- 推荐输入：`module_key`、模块名、所属一级模块、所属组件、页面 URL/路由、接口路径、后端文件、数据表/集合、用户角色、核心流程、已知状态或枚举。
- 可选输入：需求文档路径、原型/截图路径、Story/Task、发布或运行边界。
- 缺失时处理：能合理推断的先生成草稿；不能确认的写入“待确认”或“待项目填写”，不要虚构接口、字段、表名、权限和验收结论。
- 如果输入明显覆盖多个业务域、用户角色、页面组、接口组、数据对象、状态流或端工程，先按 `TINST-010` 生成模块树拆分方案，不直接创建叶子模块档案。

## 执行步骤

1. 读取 `.maw/modules.yaml`、`docs/modules/README.md`、`docs/modules/_template/group-README.md`、`docs/modules/_template/module.md` 和 `docs/modules/_template/changelog.md`；如果用户提供页面 URL、API、命令或后端文件线索，再读取 `docs/modules/_template/route-api-index.md`；如果需要具体页面或后端审计页，再读取 `page.md`、`backend-slice.md` 或 `traceability.md`。
2. 如果用户给出需求文档、原型、截图或相关资料路径，读取最小必要片段，提炼为页面、流程、字段、按钮、状态、接口、数据表和待确认项。
3. 先做 leaf 判定：
   - 如果候选模块可以独立验收、边界清晰、无需继续拆分，继续生成 `module.md`。
   - 如果候选模块只是一级业务域、中间能力组、端工程或横切能力集合，先创建或更新模块组 `README.md`，并在“模块拆分判定表”中列出下一层候选 leaf。
   - 如果无法判断是否可独立验收，写入待确认项，不要为了填满模板强行生成 leaf。
4. 确定 `module_key`：
   - 用户已提供时优先使用用户提供值。
   - 未提供时，根据模块英文含义生成小写短横线 key。
   - 若无法可靠生成或与现有模块冲突，先向用户确认。
5. 检查 `.maw/modules.yaml` 中是否已有同名或近似模块：
   - 已存在时，读取对应 `doc`，在不覆盖已有有效内容的前提下补齐缺失章节。
   - 不存在时，创建 `docs/modules/<module-key>/module.md`，并按需要创建 `docs/modules/<module-key>/changelog.md`。
6. 按 `docs/modules/_template/module.md` 填写初版：
   - 用用户描述填充业务目标、用户角色、核心场景、上游触发、下游影响和关键状态。
   - 将页面、弹窗、字段、按钮、状态流、异常边界拆成结构化条目。
   - 填写 `doc_status`、`confidence`、`last_verified_commit`、`source_paths` 等证据字段；只有当前代码、路由、API、测试或人工确认支撑时才写 `confirmed`。
   - 未确认信息集中进入“需求来源与证据”“异常、边界与待确认项”“待办”。
7. 如果用户提供了页面 URL、API、命令或关键文件线索，同步更新所属一级模块 `route-api-index.md`；该索引只写 owner_module、consumer_modules、详情文档、源码路径和确认状态，不写详细规格。
8. 只有页面或后端规则复杂、正在审计或用户明确要求时，才在二级模块下创建 `pages/<page-key>.md`、`backend/<api-group-or-file>.md` 或 `traceability.md`；否则先在 `module.md` 写索引和待确认项。
9. 如果新建了模块档案，同步向 `.maw/modules.yaml` 增加最小模块索引；路径、接口、表名未知时使用空列表，不猜测。一级 group 可选登记 `route_api_index`，leaf 可选登记 `detail_docs`、`doc_status`、`confidence`、`last_verified_commit` 和 `last_audit_id`。
10. 如果新建或更新了模块组，同步更新父级 `README.md` 的子模块菜单；如果只生成拆分方案，不创建 leaf 的 `module.md`。
11. 更新模块 `changelog.md`，记录本次生成初版属于 `docs` 变更。
12. 最终说明中给出：生成的调用句、拆分判定、更新文件、URL/API 索引补齐程度、detail docs 补齐程度、推断内容、待确认项和后续补齐建议。

## 验证方式

- 确认 `docs/modules/<module-key>/module.md` 存在，标题、`module_key` 和章节编号完整。
- 如新增模块，确认 `.maw/modules.yaml` 中存在对应 `key`、`doc`、`changelog`。
- 如输入是大模块或中间模块组，确认只更新 group `README.md` 和拆分判定表，没有误建过宽 leaf。
- 如输入包含 URL/API/命令，确认所属一级模块 `route-api-index.md` 已更新或说明未更新原因。
- 如新增页面/后端审计页，确认它们仍归属于二级模块，不被登记为新的正式 leaf。
- 如新增 changelog，确认记录了本次模块档案初版生成。
- 检查档案中没有真实密钥、账号密码、客户隐私、生产连接串，也没有把外部需求原文整段粘贴进模块档案。

## 禁区

- 不得为了填满模板而编造接口、数据库字段、权限、状态流或验收结果。
- 不得把一级业务域、端工程、角色集合或多个状态流组成的大模块直接生成单个 leaf。
- 不得把一级模块 URL/API 索引写成详细规格；不得把页面/后端审计页升级成正式模块。
- 不得覆盖已有模块档案中的人工确认内容；只能补齐、重组或标注待确认。
- 不得把 `docs/archive/**` 作为当前实现依据，除非用户明确给出归档路径并要求追溯。
- 不得写入真实密钥、账号密码、客户隐私或生产连接串。

## 冲突与覆盖规则

- 用户当前明确描述优先于旧模块档案。
- 当前代码、`.maw` 配置和 active 文档优先于旧草稿或归档资料。
- 与 `TINST-003 使用模块档案定位开发边界` 冲突时，以本指令负责“生成/补齐初版”，以 `TINST-003` 负责“后续开发任务定位边界”。

## 更新记录

- 2026-06-22：补充一级模块 `route-api-index.md` 和二级模块页面/后端审计页的按需生成规则。
- 2026-05-22：创建。
