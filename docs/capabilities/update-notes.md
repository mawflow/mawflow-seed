---
doc_key: capabilities.update-notes
doc_type: capability
stage: development
status: stable
owner: platform-engineering
tags: [updates, seed, release-notes]
read_contract:
  summary: "复用任务变更片段的更新动态采集、最近100条和全量生成，以及可选的云端手册分页准备。"
  ai_read_hint: "维护更新动态公共能力或回流Seed时读取。"
---

# 公共能力：长期更新动态

- capability_key: project-update-notes
- status: stable
- type: governance_protocol
- origin: seed_repository
- owner_module: project-governance
- owner_component: 无业务运行时组件

权威数据复用 `.maw/changes/*.yaml` 的 `update_note` 片段。`ops/scripts/generate-update-notes.py` 提供 record、显式 import-changelogs、render、render-cloud、check；追加写、同 ID 幂等、指纹绑定、软链接/秘密/路径拒绝、原子写回和更正冲突保护均由同一实现完成。

默认生成最近100条，完整历史保留全部已记录动态。云端目录按月份和每页100条分拆，单页/整次大小与项目手册发布限制一致；只准备项目私有手册页和页哈希，不另建 cloud publisher 或伪造成功回执。详情在仓库可点击，云端对仓库文件保留来源路径，对外部安全链接保留点击能力。

接口契约见 `.maw/schemas/update-note.schema.json`，日常规范见 `docs/ai-coding/update-notes.md`，指令见 `docs/ai-instructions/instructions/generate-update-notes.md`。历史补录只保证明确表格来源的安全、已确认行；所有拒绝/未解析项必须在回执可见，不声称是完整 Git 历史。

验证：`python3 -m pytest tests/test_update_notes.py -q` 与临时新项目 `check`；实际云端同步依赖既有真人基线批准、Publisher Lease、同步回执及读回。当前实现不要求 Host 安装或应用部署，正式发行与实际云端同步仍需各自发布流程。
