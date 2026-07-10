# 经验候选台账

本文件用于暂存用户在任务过程中的澄清、说明、纠偏、边界补充和偏好表达。它们不一定立刻成为正式指令或经验，但应先提取标题、关键词和内容摘要，供后续 Codex 会话复用。

AI 自己在执行中试错后找到正确方法的经验，记录到 `execution-lesson-candidates.md`，不要混在本文件里。

当某条经验多次被验证、反复适用或用户明确要求长期记住时，应升级为：

- `docs/ai-instructions/lessons/<topic>.md`：复盘经验、踩坑记录、偏好总结。
- `docs/ai-instructions/solutions/<category>/<topic>.md`：较大的具体解决方案、完整排查过程、命令序列和验收清单。
- `docs/ai-instructions/instructions/<topic>.md`：可执行流程。
- `docs/ai-instructions/terms/<keyword>.md`：稳定术语定义。

## 使用规则

- 用户澄清了某个词的含义、边界、默认处理方式或禁止事项时，应记录。
- 用户纠正了 AI 的理解、执行路径、部署目标、模块归属或文档位置时，应记录。
- 用户补充的信息能帮助后续任务减少误读、缩小上下文、避免重复确认时，应记录。
- 不记录纯寒暄、一次性情绪表达、与项目无关的信息。
- 不记录真实密钥、token、账号密码、客户隐私、生产连接串或不可外传资料。

## 候选表

| 标题 | 关键词 | 来源 | 首次记录 | 最近更新 | 内容摘要 | 适用范围 | 相关 module_key | 相关路径/对象 | 状态 | 升级目标 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 模板升级偏好：可信设备、code-only、local 强化和持续记忆 | 可信设备开发、code-only 交付、.local 强化、多设备开发、越用越聪明 | 任务包执行要求 | 2026-06-14 | 2026-06-14 | 当前模板升级要求强化 AI 主力开发：可信设备上开发，业务项目默认只交付 `code/`；本机差异进入 `.local`，项目共享术语/澄清/偏好/执行经验进入 `docs/ai-instructions/`，最终说明报告 `memory_update` 与 `local_update`。 | MAW 模板仓库和派生项目升级/模板化改造 | not_identified | `.local/README.md`, `docs/ai-instructions/instructions/project-memory-loop.md`, `docs/ai-coding/ai-primary-development-model.md` | refining | lesson_created |
| 用户口径偏好：确认含义后收口沿用习惯用语和别称 | 用户口径、习惯用语、别称、收口口径、项目内叫法 | 用户澄清 | 2026-06-15 | 2026-06-15 | 用户要求 AI 记住其习惯用语和别称；明确含义后，后续收口信息里的 AI 主展示口径也尽量按用户叫法表达。含义不明确时先问清楚。技术元数据 key 仍保持稳定。 | MAW 模板仓库和派生项目的项目指令、关键词学习、最终收口 | not_identified | `docs/ai-instructions/instructions/project-memory-loop.md`, `docs/ai-instructions/instructions/keyword-learning-loop.md`, `docs/ai-instructions/instructions/final-closeout-response.md` | refining | instruction_updated |
|  |  | 用户澄清/任务说明/执行复盘 |  |  |  |  |  |  | candidate |  |

当某条候选需要承载大篇幅解决方案时，不要把正文塞进本表；应在本表保留摘要和关键词，在 `experience-index.md` 登记 `EXP-XXX`，并把详细方案写入 `solutions/**`。

状态建议：

- `candidate`：已暂存，有复用价值但尚未稳定。
- `refining`：多次出现或正在补充边界。
- `lesson_created`：已升级为正式经验文档。
- `solution_created`：已升级为解决方案详情文档。
- `instruction_created`：已升级为正式指令。
- `term_created`：已升级为正式术语。
- `merged`：已合并到其它条目。
- `ignored`：确认无需继续跟踪。

## 内容摘要写法

内容摘要建议包含：

- 用户原意的简明改写。
- 它纠正了什么旧理解或补充了什么边界。
- 后续 AI 应怎样使用这条信息。
- 是否需要人工确认、有效期或适用仓库范围。
