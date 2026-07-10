# 指令库与提示词目录分工

## 元信息

- ID：LESSON-001
- 类型：经验
- 状态：启用
- 适用场景：判断项目知识应沉淀到 `docs/ai-instructions/` 还是 `prompts/`

## 经验结论

如果内容是“用户在项目内说一句短语，AI 就应该按固定理解或流程行动”，应放入 `docs/ai-instructions/`。如果内容是“某次任务要复制给 AI 的完整提示词、分析输入或执行草稿”，应放入 `prompts/`。

## 判断标准

- 可长期复用、需要触发词命中、会影响 AI 对项目术语或流程的理解：放入 `docs/ai-instructions/`。
- 一次性任务输入、外部工具分析提示、可复制的大段 Codex prompt：放入 `prompts/`。
- 编码边界、代码风格、工程规范、禁改范围：放入 `docs/ai-coding/`。
- 原始需求、客户资料、验收材料：放入 `docs/requirements/`、`docs/acceptance/` 或其他对应资料目录。

## 示例

- “发布客户云服务器”在某项目里固定映射到某个发布目标：适合写入 `docs/ai-instructions/terms/` 或 `instructions/`。
- “请根据这些资料生成任务拆解”的完整提示词：适合写入 `prompts/external-analysis/` 或 `prompts/codex/`。
- “AI 不得修改支付回调签名逻辑”：适合写入 `docs/ai-coding/user-provided-rules.md`。

## 后续行动

当不确定应该放在哪个目录时，优先先写入最保守、最接近用途的位置，并在最终说明中标注判断依据，方便人工后续调整。
