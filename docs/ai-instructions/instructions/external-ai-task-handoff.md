---
instruction_id: TINST-012
short_id: T012
name: External AI Task Handoff
trigger: 交接任务
aliases:
  - AI任务交接
  - ChatGPT任务交接
scope: template
status: active
---

# 外部 AI 任务交接

当用户要求把已确定方案交给另一个 AI 执行时，统一遵守根目录 `CHATGPT_TO_AI.md`。

推荐调用：`#交接任务`

- 默认交付可复制的 Markdown；只有用户明确要求才生成 zip。
- 使用通用“接收方 AI”口径，不绑定 Codex 专属目录或运行方式。
- 写清目标、允许范围、禁止项、事实、验证和交付状态。
- 接收方仍必须重新读取目标项目规则并核验事实。
