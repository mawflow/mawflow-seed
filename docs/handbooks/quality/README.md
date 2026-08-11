# 测试与质量手册

记录测试策略、质量证据、UAT 业务交付、三 Profile 物化、Doctor、迁移、回滚、构建与公开 payload 验证。

## UAT 业务交付

- 正式测试人员文档：`uat/<delivery_id>/business-acceptance-guide.md`
- 同批审计清单：`uat/<delivery_id>/delivery-manifest.json`
- 生成标准：`docs/delivery/uat/business-handoff-standard.md`
- 生成器：`ops/scripts/generate-uat-business-handoff.py`

UAT 文档以业务自述为主、测试引导为辅。实际执行结果进入 TestRun/Bug/Evidence；云端文档审阅通过不等于真人 UAT 通过。
