---
doc_key: updates.index
doc_type: governance
stage: development
status: active
owner: project-owner
read_contract:
  summary: "更新动态的权威片段、生成入口和使用范围。"
  ai_read_hint: "生成或记录更新动态时读取。"
---

# 项目更新动态

使用 `#更新动态` / `#T043` 生成最近100条；`#更新动态 --all` 或 `#更新动态：全部` 生成全部已记录动态。使用规范见 [日常更新动态](../ai-coding/update-notes.md)，输入示例见 [片段模板](note-template.yaml)。

`.maw/changes/*.yaml` 中的 `update_note` 是权威来源。日常已授权、实际用户可见的变化在验证后追加，生成页可重建；示例不自动导入。最近视图保存到 `docs/updates/updates.md`，完整历史保存到 `docs/updates/CHANGELOG.md`，没有记录时显示空状态。

`render-cloud` 可生成 `docs/handbooks/release-ops/updates.md` 与历史分页；未接入项目云端发布服务时仅准备 Markdown，不声称已同步。升级采用指令、工具和规范，保留各项目自己的记录与权限。
