# AI 编码边界与工程规则

本目录定义 AI 编写、修改、审查代码前必须遵守的边界、风格、工程目录说明和初始化待办清单。

## 读取约束

AI/Codex 不应默认全量读取 `docs/ai-coding/**`。先读取本 README，再按任务风险和触发场景选择具体规则文件：

- 项目初始化、开工检查、大规模功能开发：读取 `initialization-checklist.md`。
- 实现、修 bug、测试、构建、发布、同步或执行脚本：先检索 `../ai-instructions/experience-index.md`；只有索引、候选台账或用户明确路径命中具体文件时，才读取 `../ai-instructions/solutions/**`。
- 用户明确给出禁改范围或风格偏好：读取 `user-provided-rules.md`。
- 需要确认 AI 主力开发的 code 产品交付平面、code 外控制面或最终收口判断：读取 `ai-primary-development-model.md`。
- 需要理解当前工程结构或历史分析结论：读取 `ai-analysis-rules.md`。
- 代码风格、提交、测试、错误处理问题：读取 `coding-style.md`。
- 模块定位、模块档案维护、最终说明格式：读取 `module-dossier-rules.md`。
- 具体端工程任务：读取相关 `component-guides/` 和 `code/<component>/.maw.component.yaml`。

## 文件职责

- `initialization-checklist.md`：项目初始化时必须完成的 AI 编码前置清单。
- `user-provided-rules.md`：用户、客户、负责人明确给出的编码边界、风格要求、禁改范围和交付偏好。
- `ai-primary-development-model.md`：AI 主力开发模型，明确 `code/` 是业务产品交付平面，`.maw/`、`docs/`、`prompts/`、`ops/`、`.local/` 是协作控制面或本机平面。
- `ai-analysis-rules.md`：AI 阅读项目后总结出的工程结构、技术栈、代码习惯、风险点和推荐实践。
- `coding-style.md`：跨端通用代码风格、命名、注释、错误处理、测试和提交规则。
- `module-dossier-rules.md`：AI 使用 `.maw/modules.yaml` 和 `docs/modules/` 定位模块边界、维护档案和输出最终说明的规则。
- `component-guides/`：各端工程目录说明、启动/构建/测试命令、边界和常见改动位置。

项目内短语、固定流程、专有名词和复盘经验应放入 `docs/ai-instructions/`。本目录只保存编码边界和工程规则。

## 执行规则

- 初始化清单未完成前，不开展大规模功能开发。
- 用户提供规则优先级高于 AI 分析规则；如二者冲突，记录到 `initialization-checklist.md` 的待确认项。
- AI 分析规则必须来源于实际代码和文档，不凭空假设。
- 每次实现、修 bug、测试、构建、发布、同步或执行脚本前，先用任务关键词、路径、命令、错误症状和 app_key 检索 `docs/ai-instructions/experience-index.md`；不得主动全量读取 `docs/ai-instructions/solutions/**`。
- 开发任务如包含 `module_key`、模块名、页面路径、接口路径或数据表名，先按需读取 `module-dossier-rules.md` 并定位模块档案。
- 每次新增端、迁移目录或调整构建方式时，同步更新 `component-guides/` 和对应 `.maw.component.yaml`。
- 对代码风格、架构边界或发布规则有不确定性时，先补文档或提出待确认问题，再改代码。
- 每次任务完成时，最终说明必须包含 `experience_lookup`，并判断本轮修改的 `code` 组件应用和 app_key；对需要发布才会生效的组件写明“本轮修改了 <app_key> 的 <内容>，需要发布 <app_key> 才会生效，当前已发布/当前未发布”。需要发布但当前未发布或未验证时，最终说明还必须按 app_key 给出可复制 `#发布：发布 <app_key> 到 <env>...` 和可用中文口令快捷指令，并在收口末尾询问是否“确认发布全部”；多个 app_key 时，用户可以复制其中一条或多条选择部分发布，回复“确认发布全部/确认/是”则发布全部待发布组件。用户说 `发布测试`、`发布上线`、`发布生产` 或 `发布生成` 且未指定组件时，按对应 `remote_server.default_release_components` 解析候选范围，再按发布版本状态和组件路径差异筛选发布名单；`发布测试` 是本地调试版本，需给可访问调试地址；`发布上线` 是部署到 `remote_staging_server` 的编译包部署测试，仍属于测试，需给线上可访问地址；`发布生产` 是部署到 `remote_production_server` 的生产发布，涉及生产环境安装或版本上线必须人工审计；上线和生产发布前必须确认本地候选 commit 等于发布来源远端分支。
- 如果用户要求记录项目指令、术语或经验，按 `docs/ai-instructions/README.md` 更新指令库。
