# 指令：使用模块档案定位开发边界

## 触发词

模块档案、功能模块、module dossier、模块边界、页面边界、接口边界、数据表边界、按模块处理、这个页面属于哪个模块、这个接口属于哪个模块。

## 执行规则

1. 先读取 `.maw/modules.yaml`。
2. 如果任务给出 `module_key`，先定位它是模块组还是叶子模块；只有叶子模块才读取对应 `doc` 和必要的 `changelog`。
3. 如果任务给出模块名、页面 URL、页面路径、接口路径、命令名、文件路径或数据表名，先在 `.maw/modules.yaml` 的 `name`、`frontend_paths`、`api_paths`、`backend_paths`、`table_names` 中定位。
4. 如果只能定位到一级模块，先读取该一级模块 `README.md`；当任务输入是 URL、API、命令或文件路径时，再读取同目录 `route-api-index.md` 快速定位二级模块。
5. 如果只能定位到中间模块组，先读取该模块组 `README.md` 的子模块菜单，按需继续向下定位。
6. 定位后只读取对应叶子模块档案、相关代码路径和必要设计文档；具体页面或后端审计只读取命中的 `pages/`、`backend/` 或 `traceability.md`；禁止全量读取 `docs/modules/**`。
7. 读取模块档案时关注 `doc_status`、`confidence` 和 `last_verified_commit`；`stale` 或 `deprecated` 文档不能作为当前事实源，只能用于历史追溯或迁移判断。
8. 修改页面 URL、API、数据表、状态流、配置、发布或外部同步边界后，判断是否更新 `docs/modules/<group>/route-api-index.md`、`docs/modules/<module-key>/module.md`、对应 detail docs、`last_verified_commit` 和 `changelog.md`。
9. 最终说明必须包含 `module_key`、`module_dossier_updated`、`module_dossier_reason` 和 `updated_module_docs`。

## 冲突与覆盖规则

- 用户当前明确指令优先于旧模块档案。
- 模块档案与当前代码冲突时，以当前代码为准，并同步修正档案或记录待确认。
- 模块档案证据不足时写 `pending_confirm`，不要把推断内容提升为 `confirmed`。
- `docs/archive/**` 默认永不自动读取，不作为当前实现依据。
