# 更新动态内置指令的增量升级

`TINST-043 / #更新动态` 随 Seed 提供权威片段、生成工具和日常记录规范。默认最近100条，`--all` 或“全部”生成全部已记录动态；生成文件不替代权威来源或发布记录。

其它项目在自己的会话执行 `#模板升级`（兼容 `#模版升级`），按 `template_source.source_channel`、目标版本和已采用 commit 计算漂移，再采用本升级策略。开发候选仅在源 `dev` 时，可明确指定目标 `dev` 或候选 commit；默认 `main` 仍以实际晋级的正式源为准，公开项目只能使用其公开来源已发布的版本。

| 资产 | 升级取舍 |
| --- | --- |
| `docs/ai-instructions/instructions/generate-update-notes.md` | 新增 TINST-043，并在指令索引和 PROJECT_COMMANDS 增量登记；原有同名 PINST 保留为兼容别名，不重复路由 |
| `ops/scripts/generate-update-notes.py`、`ops/scripts/update_notes/` | 整套依赖一起采用；有项目定制时先比较，保留差异并执行回归 |
| `docs/ai-coding/update-notes.md`、`docs/updates/README.md`、`note-template.yaml`、`.maw/schemas/update-note.schema.json` | 增量采用规范和示例，不把示例作为已发生更新 |
| Agent entry、rules、project-workflow | 合并 `execution_contract.update_notes` 和 `record_project_update_notes`，保留项目授权、只读和禁记规则 |
| lifecycle | 合并 `project_lifecycle.change_fragments.update_notes`；未使用任务片段的旧项目按新增命名空间处理 |
| package.json | 按项目脚本规范增量合并 updates、updates:all、updates:cloud、updates:check、updates:record；不覆盖业务脚本 |
| `.maw/changes/*.yaml`、已生成更新文档、云端准备回执 | 不从源仓复制；保留目标项目全部历史，以目标自己的片段生成新视图 |
| 云端 | 本地仅生成 Markdown 目录、分页和 prepared_not_published；缺少兼容服务时写明 cloud_not_configured |
| Seed lock / Kit | 版本与指纹由受控迁移工具处理；不手改锁文件绕过迁移，不把部分采用写成全量升级 |

保护 README、code、app_key、模块档案、发布配置、仓库映射、凭据、`.local/`、现有动态和云端权限。历史补录只能显式选择目标项目模块日志，警告和遗漏必须保留；不能用 Git 提交标题推断发布或验收。

验收依次执行：临时新项目空状态 → 一条真实测试输入追加 → 同 ID 重试零写入 → 最近100/全部/云端准备 → check；105条验证100条上限与全量保留。旧项目验证既有事实、记录和自定义规则保留。最后复核模板 commit 和 Seed Contract 两条版本线，再按目标项目提交、推送与 mirror 策略收口。

源开发仓、Kit 模板和 PUBLIC_PAYLOAD_MANIFEST 必须携带完整通用依赖；源仓实际来源记录和动态历史不作为新项目初始事实。正式发行、Host 安装、实际云端发布与真人验收分别记录。
