---
doc_key: intake.index
doc_type: index
stage: discovery
status: active
owner: project-owner
read_contract:
  summary: "日常交互最小来源记录入口；目录和模板本身不代表项目已确认内容。"
  ai_read_hint: "先看收录规范，仅按任务需要读取具体来源。"
---

# 交互来源

日常 AI 协作按 [收录规范](../ai-coding/document-source-capture.md)积累必要摘要、确认范围、未知、证据与下一步。具体记录由 `ops/scripts/capture-document-source.py` 生成；[JSON 模板](source-template.json)是格式示例，不是项目事实。

来源文件只作为需求、任务、审计和文档的依据。未确认记录也应保留，但不能被当作已确认结论。敏感原文、完整聊天、本机路径不进入此目录。
