# 关键词候选台账

本文件用于记录 Codex/Agent 在任务提示词、用户消息、Story/Task、模块档案或执行过程中反复遇到但尚未完全定义的项目关键词。

目标不是把每个普通词都收集起来，而是让项目里的业务黑话、模块别名、页面俗称、接口简称、数据表简称、客户/环境/发布目标别名逐步沉淀成可复用术语。候选词成熟后，应迁移或合并到 `docs/ai-instructions/terms/<keyword>.md`，并更新 `docs/ai-instructions/README.md`。

## 使用规则

- 首次遇到疑似项目特有关键词时，可以先新增候选行，填写粗略含义和边界。
- 同一关键词在后续任务提示词中再次出现时，不重复新增；更新 `出现次数`、`最近出现`、`边界补充` 和 `相关模块/路径`。
- 当关键词已经有稳定定义、触发词、适用范围和禁区时，创建或更新正式术语文档。
- 普通技术词、通用动词、一次性临时描述和敏感信息不进入本台账。
- 不记录真实密钥、token、账号密码、客户隐私、生产连接串或不可外传资料。

## 候选表

| 关键词 | 别名/写法 | 出现次数 | 首次出现 | 最近出现 | 粗略定义 | 边界补充 | 相关 module_key | 相关路径/对象 | 状态 | 术语文档 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 可信设备开发 | 受控开发节点、可信私有仓库 | 1 | 2026-06-14 | 2026-06-14 | 模板默认面向受控设备和私有仓库中的 AI 主力开发。 | 不等于外部交付可携带 secrets；客户仓库同步和交付包仍需脱敏。 | not_identified | `.maw/policies.yaml`, `docs/ai-instructions/instructions/project-memory-loop.md` | candidate |  |
| code-only 交付 | 只交付 code、业务项目只交付 code | 1 | 2026-06-14 | 2026-06-14 | 业务项目默认只交付 `code/` 产品平面，AI 控制面用于内部协作和检查。 | 修改 code 外控制面通常无需业务发布，但可能影响内部交付检查。 | not_identified | `docs/ai-coding/ai-primary-development-model.md` | candidate |  |
| .local 强化 | 本机差异、多设备 local、local overlay | 1 | 2026-06-14 | 2026-06-14 | 本机路径、端口、工具链、代理、浏览器调试和维护记录进入 `.local/`。 | 真实 `.local` 配置不提交；只提交 README/example。 | not_identified | `.local/README.md`, `.local/device.example.yaml` | candidate |  |
| 越用越聪明 | 项目记忆闭环、记忆沉淀 | 1 | 2026-06-14 | 2026-06-14 | AI 持续沉淀用户澄清、术语、长期偏好和执行经验。 | 项目共享记忆进 `docs/ai-instructions/`，本机差异进 `.local/`。 | not_identified | `docs/ai-instructions/instructions/project-memory-loop.md` | candidate |  |
| 用户口径 | 习惯用语、别称、项目内叫法、收口口径 | 1 | 2026-06-15 | 2026-06-15 | 用户确认某个习惯用语或别称含义后，AI 后续任务和收口主展示优先沿用该叫法。 | 含义不明确时先问清楚；技术元数据 key 保持稳定英文，不随口径改名。 | not_identified | `docs/ai-instructions/instructions/keyword-learning-loop.md`, `docs/ai-instructions/instructions/final-closeout-response.md` | candidate |  |
|  |  | 0 |  |  |  |  |  |  | candidate |  |

状态建议：

- `candidate`：已记录，但定义或边界仍不稳定。
- `refining`：多次出现，正在补充定义、边界和触发条件。
- `term_created`：已创建正式术语文档。
- `merged`：已合并到其它术语。
- `ignored`：确认只是普通词或临时词，不再跟踪。

## 边界补充写法

边界补充建议写清楚：

- 属于哪个模块、页面、接口、数据表、配置、发布目标或客户仓库同步范围。
- 不属于哪些相近模块或路径。
- 当前信息来源是用户提示词、模块档案、代码路径、接口名还是人工确认。
- 还有哪些待确认问题。
