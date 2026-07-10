# 指令：模块树拆分与模块档案生成

## 元信息

- ID：TINST-010
- 类型：项目指令
- 状态：启用
- 维护位置：`docs/ai-instructions/instructions/split-module-tree.md`
- 触发词：#模块、生成 modules、拆分模块、模块树、模块拆细、modules 拆分、模块太大、自动生成模块档案、重建模块索引、按业务拆 modules、不要只拆二级目录、模块地图、URL/API 索引、route-api-index、页面审计页、后端审计页、AI 模块上下文、ai-context、ai_doc、_ai 模块副本
- 适用范围：从项目、需求、代码路径或功能描述中生成/重建 `docs/modules/` 和 `.maw/modules.yaml`；处理 AI 自动生成模块过粗、没有拆到 leaf、只拆成一级/二级目录的问题。

## 目标

让 AI 先生成模块树和拆分判定，再创建叶子模块档案，避免把端工程、大业务域或多个流程混在一个 `module.md` 里。模块拆分的结果应服务于后续开发定位、文档维护、测试验收和发布判断。

## 输入要求

- 必需输入：项目范围、需求描述、代码路径或需要重建的模块范围。
- 推荐输入：端工程/app_key、页面路径、接口路径、数据表、用户角色、主要业务流程、发布边界、已有模块文档路径。
- 可选输入：需求文档、原型、Story/Task、已有模块拆分偏好。
- 缺失时处理：能从当前项目文件确认的先确认；无法判断是否可独立验收时，标记 `unknown` 或 `defer`，不要强行生成 leaf。

## 执行步骤

1. 读取 `.maw/modules.yaml`、`.maw/module-candidates.yaml`、`docs/modules/README.md`、`docs/modules/_discovery/README.md` 和 `docs/modules/_template/group-README.md`；如果需要创建 leaf，再读取 `docs/modules/_template/module.md` 和 `docs/modules/_template/changelog.md`。如果需要建立 URL/API 定位或审计页，再读取 `docs/modules/_template/route-api-index.md`、`page.md`、`backend-slice.md` 和 `traceability.md`。只有模块复杂、AI 经常误读或用户明确需要 AI 读取提示时，才读取 `docs/modules/_template/ai-context.md`。
2. 根据任务输入和最小必要代码/文档，识别候选模块节点。
3. 为每个候选节点填写模块拆分判定：

```text
候选节点:
建议 module_key:
父级:
类型: group / leaf / cross-cutting / defer
拆分依据:
主要角色:
页面边界:
API/命令边界:
数据/状态边界:
是否可独立验收: yes / no / unknown
是否继续拆: yes / no / unknown
结论:
```

4. 判定为 `group` 的节点，只创建或更新 `README.md`，并维护子模块菜单、共享边界、不做范围和待确认问题。
5. 一级 `group` 下有页面 URL、API、命令或关键文件线索时，创建或更新同目录 `route-api-index.md`；该文件只写轻量定位，不写字段、按钮、入参出参和状态流详情。
6. 判定为 `leaf` 的节点，才创建或更新 `module.md` 与 `changelog.md`；同时记录 `doc_status`、`confidence`、`last_verified_commit` 和 `source_paths`，证据不足时写 `pending_confirm` 或 `inferred`。
   - 普通 leaf 不创建 AI 专用文件。
   - 有页面、API 或后端文件需要人工对照审计时，可以在 leaf 下按需创建 `pages/`、`backend/` 和 `traceability.md`。这些是 detail docs，不是新的正式模块。
   - 复杂 leaf 可以按需创建 `ai-context.md`，只写 AI 读取路线、常见误判、执行提示和验证提示。
7. 判定为 `cross-cutting` 的节点，优先写入相关 group 的共享边界；只有它能独立验收并有清晰路径、配置、测试或发布边界时，才生成 leaf。
8. 判定为 `defer` 或 `unknown` 的节点，不生成 leaf；写入 `.maw/module-candidates.yaml`、`docs/modules/_discovery/`、父级 group 的待确认问题或最终说明。
9. 更新 `.maw/modules.yaml`：
   - group/component 节点可以登记 `key`、`name`、`type`、`doc`、`parent_key` 和共享路径。
   - leaf 节点必须登记 `doc`、`changelog`、`parent_key`、`component_refs`、`app_keys`、路径/API/表/配置/测试边界。
   - 一级 group 可以可选登记 `route_api_index` 指向 `docs/modules/<group>/route-api-index.md`。
   - leaf 可以可选登记 `detail_docs.page_docs`、`detail_docs.backend_docs` 和 `detail_docs.traceability_doc`。
   - leaf 可以可选登记 `doc_status`、`confidence`、`last_verified_commit`、`last_verified_at`、`last_audit_id` 和 `audit_docs`。
   - 复杂 leaf 可以可选登记 `ai_doc` 指向 `docs/modules/<...>/<leaf>/ai-context.md`。
   - 路径、接口、表名未知时使用空列表，不猜测。
10. 更新父级 group `README.md` 的子模块菜单，让后续 AI 能逐层定位。
11. 最终说明中写清模块树、leaf 判定理由、没有继续拆的原因、URL/API 索引补齐程度、detail docs 补齐程度、待确认问题和验证结果；无法确定正式 `module_key` 时输出 `module_candidate`。

## 拆分原则

- 先按业务域和系统域分 group，再按业务流程、页面组、接口组、数据对象、状态流或发布边界拆 leaf。
- `server`、`client` 等端工程通常是 component 或 group，不应长期作为唯一业务 leaf；独立后台前端如项目需要，应作为项目新增 app_key 处理。
- “用户中心”“订单管理”“内容运营”“设备管理”这类大域必须先拆成子模块。
- 一个 leaf 应能被一个 Story 或一组强相关 Task 交付，并能单独验收。
- 只包含一个字段、按钮、提示文案或纯样式修改的内容，不应单独成为 leaf。
- URL/API 索引属于一级模块快速定位层；页面审计页和后端审计页属于二级模块 detail docs，不应升级成正式模块。
- `module.md` 是模块事实源；`ai-context.md` 只是可选 AI 读取提示。不要把所有 `module.md` 批量复制成 `_ai` 副本。

## 验证方式

- `.maw/modules.yaml` 能被 YAML 解析。
- `.maw/module-candidates.yaml` 能被 YAML 解析；候选模块字段完整。
- group `README.md` 包含子模块菜单和模块拆分判定表。
- 一级 group 如存在 URL/API 定位索引，`route-api-index.md` 只包含定位关系和待确认项，不复制详细规格。
- 每个 leaf 都有 `module.md` 和 `changelog.md`。
- `.maw/modules.yaml` 中 leaf 的 `doc` 和 `changelog` 路径真实存在。
- leaf 下存在 `pages/`、`backend/` 或 `traceability.md` 时，它们被 `module.md` 或 `.maw/modules.yaml` 可追溯引用。
- 如果 leaf 登记了 `ai_doc`，该路径真实存在，且内容只包含 AI 读取路线、常见误判、执行和验证提示，不复制完整模块事实。
- 没有新增 `general`、`misc`、`common` 这类兜底模块。
- 没有把明显过宽的大模块直接落成单个 leaf。
- `seed`、`candidate` 或证据不足的 `provisional` 模块没有被误写入 `.maw/modules.yaml`。

## 禁区

- 不得为了快速完成而只生成一级/二级粗模块。
- 不得把整端工程、整后台、整服务端、整用户中心或整订单管理当成唯一 leaf。
- 不得凭空编造接口、表、字段、权限、状态流或发布目标。
- 不得覆盖已有模块档案中的人工确认内容；已有项目只做 additive 合并。
- 不得把 `route-api-index.md` 当成 API 设计文档或页面规格文档；不得把 `pages/`、`backend/` 审计页当成正式模块。
- 不得给所有模块批量生成 `_ai` 后缀档案，或让 AI 专用文件替代 `module.md`。
- 不得全量读取 `docs/modules/**` 或 `code/**` 来生成模块树；按任务范围读取最小必要上下文。

## 冲突与覆盖规则

- 用户明确指定的业务边界优先，但如果指定范围明显过宽，先给出拆分建议并标记风险。
- 当前代码、`.maw` 配置和 active 文档优先于旧模块草稿或归档资料。
- 与 `TINST-005 生成模块档案初版` 冲突时，本指令负责模块树和多模块拆分，`TINST-005` 只负责已判定为 leaf 的单个模块档案初版。

## 更新记录

- 2026-06-22：补充模块地图、一级 `route-api-index.md`、二级 `pages/` / `backend/` / `traceability.md` 审计页规则，并保持渐进式补全。
- 2026-06-15：补充可选 `ai-context.md` / `ai_doc` 规则；复杂模块可给 AI 短上下文，但不批量复制 `_ai` 副本。
- 2026-06-12：创建，建立“先模块树、后叶子档案”的 modules 自动生成协议。
