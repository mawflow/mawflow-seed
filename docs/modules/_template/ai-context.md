---
doc_key: docs.modules.template.ai-context
doc_type: governance
stage: design
status: active
owner: planner
tags:
  - modules
  - template
  - ai-context
project_health:
  dimensions:
    - product_module_design
    - ai_collaboration
  evidence_level: canonical
read_contract:
  summary: "可选 AI 模块上下文模板。"
  health_signal: "用于保持复杂模块 AI 读取提示模板可追溯。"
  consumes: []
  produces: []
  ai_read_hint: "维护复杂模块 ai-context 模板或解释 AI 读取路线时读取。"
---

# AI 模块上下文：<模块名称>

> 本文件是可选文件，只在模块复杂、AI 经常误读、`module.md` 过长或需要固定执行提示时创建。它不是新的事实源，不替代 `module.md` 和 `changelog.md`。如果内容冲突，以 `module.md`、`.maw/modules.yaml` 和当前代码为准。

## 何时读取

- <哪些任务、关键词、页面/API/数据表命中时读取本文件>
- <哪些任务只读 module.md 即可，不需要读本文件>

## AI 快速判断

- 模块职责一句话：
- 本轮任务优先检查：
- 最容易误判的边界：
- 常见不做范围：

## 最小必读路径

- 模块档案：`docs/modules/<...>/<leaf>/module.md`
- 变更日志：`docs/modules/<...>/<leaf>/changelog.md`
- 代码路径：
  - `<code path>`
- 相关设计：
  - `<docs/design/... 或 none>`

## 执行提示

- 实现前：
- 修改中：
- 验证时：
- 收口时：

## 常见坑

| 场景 | 容易误判 | 正确做法 | 参考 |
| --- | --- | --- | --- |
|  |  |  |  |

## 维护规则

- 只写 AI 读取路线、常见误判、执行提示和验证提示。
- 不复制 `module.md` 的完整需求、页面、接口、数据表或待办清单。
- `module.md` 相关边界变化后，如果本文件引用了该边界，需要同步更新。
