---
doc_key: docs.capabilities.uat-business-handoff
doc_type: capability
stage: stable
status: active
owner: quality_owner
tags: [uat, tester, audit, handbook, sharing]
---

# UAT Business Handoff

`uat-business-handoff` 是项目通用的业务验收交付能力：以正式模块事实和真实证据生成不可变的测试人员文档，并通过测试与质量手册进入本地工作台和受控云端分享。

能力由 `TINST-041/#UAT交付`、`docs/delivery/uat/` 标准、结构化 spec 和 `ops/scripts/generate-uat-business-handoff.py` 组成。它只生成业务意图与测试引导，不替代 TestRun、Bug、Evidence、真人验收或发布审批。

关键安全边界：业务事实不足时保持 draft；状态晋级 fail closed；输出全量扫描敏感值和绝对路径；历史 `delivery_id` 不覆盖；云端分享必须人工触发。
