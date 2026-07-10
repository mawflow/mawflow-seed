# AI 主力开发模型

本文件说明 MAW 模板中 AI 主力开发的默认协作模型。它适用于模板仓库自身，也适用于基于模板初始化或升级的业务项目。

## 平面划分

- `code/` 是业务产品交付平面。业务源码、业务运行配置、构建配置、路由、框架 env 示例和线上可见行为以 `code/<app_key>/` 为权威来源。
- `.maw/`、`docs/`、`prompts/`、`ops/`、`release/` 是 AI/人工协作控制面，用于上下文、治理规则、提示词工程、脚本、发布覆盖和交付检查。
- `.local/` 是本机资料和本机 overlay 平面，真实资料、本机维护记录、个人路径、临时配置和模板仓库自身 mirror 记录默认不提交。

AI 可以主力承担实现、脚本、文档、验证和收口，但必须先确认改动落在哪个平面。业务运行行为以 `code/` 事实为准；控制面只提供索引、流程和审计能力，不替代业务代码配置。

## 执行原则

1. 先读 `.maw/codex-context.md`、`.maw/agent-briefing.md`、`.maw/*.yaml` 和任务相关 README，避免全量读取仓库。
2. 修改 `code/` 前，先定位 app_key、模块边界、组件说明和发布影响。
3. 修改控制面时，保持增量语义合并，不整文件覆盖业务 README、真实 app_key、发布流程、客户仓库映射、secrets 或 `.local` 资料。
4. 任务提示词、报告、交付说明和最终回复中的项目路径使用项目根相对路径。
5. 日常开发中如果发现将来生成用户手册、概要设计或部署手册有价值的事实，应分别沉淀到 `.maw/modules.yaml` 和 `docs/modules/`、`docs/design/`、`ops/`，必要时补 README 入口。
6. 完成实际改动后运行最小相关验证，并按仓库规则提交、推送当前分支，再运行仓库级 mirror 计划命令，按有效计划处理镜像同步。

## 收口判断

每次任务完成时都要判断：

- 是否修改了 `code/<app_key>` 下的业务代码、业务运行配置或线上可见行为。
- 是否需要发布某个 app_key 才会生效。
- 是否只修改了控制面、文档、任务包或检查脚本。
- 是否需要同步更新模块档案、项目指令、任务包协议、本机说明或升级策略。
- 是否影响 code-only 交付边界。

未命中 `code/` 组件应用时，收口应明确写明“未命中 code 组件应用，无需更新发布”。

## 相关入口

- 交互和收口默认值：`.maw/interaction.yaml`
- 中文收口指令：`docs/ai-instructions/instructions/final-closeout-response.md`
- 中文收口模板：`docs/ai-instructions/templates/final-closeout.zh-CN.md`
- 模块档案规则：`docs/ai-coding/module-dossier-rules.md`
