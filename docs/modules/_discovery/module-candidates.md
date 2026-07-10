---
doc_key: docs.modules.discovery.candidates
doc_type: module_design
stage: discovery
status: active
owner: planner
tags:
  - modules
  - candidate
project_health:
  dimensions:
    - product_module_design
  evidence_level: canonical
read_contract:
  summary: "候选模块清单。"
  health_signal: "用于项目健康判断待确认模块和候选边界是否被记录。"
  consumes: []
  produces: []
  ai_read_hint: "无法确定正式模块或需要记录候选模块时读取。"
---

# 候选模块台账

本台账用于人工阅读和复核，机器可读索引见 `.maw/module-candidates.yaml`。

| module_candidate | 名称 | 别名 | 状态 | 置信度 | 关联 app_key | 已知边界 | 待确认问题 | 提升条件 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  |  |  | seed / candidate / provisional / confirmed / deprecated | low / medium / high |  |  |  | 用户确认、稳定业务边界、页面/API/数据/任务证据、复核记录 |
| template-secret-governance | 模板敏感配置治理 | secret governance、secret bindings、敏感配置治理、凭证治理 | candidate | medium | none | `.maw/secret-bindings.yaml`、`.maw/secrets*.yaml` 示例与引用协议、`policies.secrets`、Git 凭证 resolver host/proxy 通道、派生项目升级资产 | 是否提升为正式 cross-cutting leaf module 仍需用户或 Reviewer 确认 | 完成第一阶段落地、用户确认长期边界、Reviewer 复核不归入 server/client |

## 记录规则

- `seed`：只有初始线索，不足以拆模块。
- `candidate`：已有名称和部分证据，但边界仍不稳定。
- `provisional`：可以用于任务收口和临时定位，但还未成为正式 leaf。
- `confirmed`：已满足提升条件，可同步到 `.maw/modules.yaml` 和正式模块档案。
- `deprecated`：候选已废弃或合并到其它模块。

不要为了填满表格而编造页面、接口、表、用户角色或发布目标。没有证据的内容写入待确认问题。
