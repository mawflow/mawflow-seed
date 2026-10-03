# 日常交互来源收录

capability_key: `document-source-capture`

共享契约及消费边界见 [收录规范](../ai-coding/document-source-capture.md)。工具只依赖 Python 标准库；Git 与 Kit 的来源资产一致性由 `tests/test_document_source_capture.py` 验证。

开发仓通过此能力保留最小工作来源；源仓真实记录不会打包进新项目。已安装版本需随正式 Seed/Kit 发布更新，本次 dev 改动不代表公开分发生效。


## 业务与工作事件扩展（开发源码）

`mawflow.document_source.v2` 按稳定业务 key/scope 保存口径和显式修订。`mawflow.document_work_event.v1` 经 record-event 生成来源，check-event 校验收口回执；AI 工作过程不替代业务确认或任务主状态。Agent 在获准里程碑自动执行，v1 来源保留，私有会话不读取。迁移见 `docs/template-migrations/20261003-document-business-events.md`。
