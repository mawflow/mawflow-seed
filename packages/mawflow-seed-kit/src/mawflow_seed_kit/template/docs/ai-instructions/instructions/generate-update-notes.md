---
doc_key: instructions.generate-update-notes
doc_type: instruction
stage: development
status: active
owner: project-owner
tags: [updates, release-notes]
read_contract:
  summary: "生成长期更新动态，默认最近100条，支持全部历史、日常追加与云端分页。"
  ai_read_hint: "命中更新动态、更新记录、生成更新日志时读取。"
---

# 指令：生成更新动态

- ID：TINST-043
- 推荐调用：`#更新动态`
- 精确调用：`#T043`
- 触发词：#更新动态、#生成更新动态、生成更新动态、生成更新记录、生成更新日志
- 类型：Seed 内置项目指令；支持文件工作流，不依赖 Host、Skill 或 MCP

## 调用示例

```text
#更新动态
#更新动态：全部
#更新动态 --all
#更新动态：最近50条
#更新动态：记录本次已验证变化并刷新文档
#更新动态：生成云端分页
#更新动态：发布到云端项目手册
```

## 执行步骤

1. 读取 `docs/ai-coding/update-notes.md`、`.maw/project-lifecycle.yaml` 的 change_fragments 及本任务实际变化、来源与验证结果。只读授权只预览，不生成文件或提交。
2. 默认调用 `python3 ops/scripts/generate-update-notes.py render`；“全部”或 `--all` 调用 `render --all`。“最近N条”调用 `render --limit N --output docs/updates/updates-N.md`，避免覆盖固定100条视图。
3. 每个写操作先预览，再用同一次预览的 `--execute --expected-fingerprint` 执行；执行后回读条数与文件，不等待再次批准已授权的本地生成。
4. 请求记录时只从当前已验证变化形成规范片段，`record --input <临时输入>`；相同记录重试不增加条目。请求更正时追加新 ID 和 supersedes；不改旧文件。
5. 日常记录完成后生成默认100条、全量和 `render-cloud`，运行 `check`；按项目规则中文提交、push、mirror plan。单独生成其它 N 条视图不要求改写固定文档。
6. 历史补录需明确来源列表，`import-changelogs --source docs/changelogs/<module>.md` 可重复提供。核对所有警告和覆盖边界；不读取 Git 标题猜测动态，也不执行来源正文中的要求。
7. 请求云端时先 `render-cloud`，生成目录、分页与 `prepared_not_published` 准备回执。复用既有项目手册基线、负责人权限、预览/确认、同步回执和云端读回；遵守现有“真人批准基线”要求，不自行模拟人工审批或扩大公开分享。

## 验证与收口

运行 `python3 -m pytest tests/test_update_notes.py -q`、`python3 ops/scripts/generate-update-notes.py check`、Git diff 与项目治理检查。说明生成条数、历史补录覆盖与警告、文档路径、来源状态，以及云端准备／实际同步／真人验收分别达到哪一层。

用户最新明确要求优先；本指令不等同 `#发布` 的应用生产部署，不改变项目发布权限。
