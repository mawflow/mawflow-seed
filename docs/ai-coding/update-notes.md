---
doc_key: governance.update-notes
doc_type: governance
stage: development
status: active
owner: project-owner
tags: [updates, seed, release-notes]
read_contract:
  summary: "日常任务追加权威更新片段，按需生成最近100条、完整历史及可同步云端的手册分页。"
  ai_read_hint: "任务形成实际用户可见更新、生成更新动态或更正历史时读取。"
---

# 日常更新动态规范

更新动态是面向使用者的长期变化说明。借用 Seed 已有 `.maw/changes/*.yaml` 任务片段，新增 `update_note` 类型；片段是更新文案和来源的权威元数据，Markdown、云端目录和统计均可重建。PM、任务、测试、发布及真人验收保留各自主账，动态只引用已发生事实。

## 记录时机

获准修改的任务在形成用户可见的新增、优化、修复、安全变化或使用文档变化后，验证收口时追加一条或少量独立动态。说明“什么场景、使用者现在能做什么”，引用真实任务、实现说明和验证依据。重命名、格式噪声、例行检查、无变化重跑及纯内部执行流水不自动变成动态。没有实际变更时收口写 `update_notes_status: not_needed`；只读或明确禁记写 `deferred_read_only`。

示例见 [输入模板](../updates/note-template.yaml)，示例不作为事实自动导入。新增记录用稳定 `record_key` 与 `task_key`；重试复用原 ID。更正或补充发布状态用新 ID，`supersedes` 指向原记录；新记录时间必须晚于原记录且模块一致。原记录继续展示并标明“已更正”；并行更正同一记录时停止并要求明确裁决，不能按最新时间自动选边。

## 状态和来源

| 字段 | 语义 |
| --- | --- |
| occurred_at | 实际变化时间，带时区；历史日志只有日期时按该日零点排序，不声称有精确发生时刻 |
| category | added 新增、changed 优化、fixed 修复、removed 移除、security 安全、docs 文档 |
| module_key / module_name | 模块稳定标识与给人看的名称 |
| version | 可选的真实版本或候选标识；日常开发不编造正式版本 |
| delivery_state | implemented 开发完成、released 已发布、historical 历史记录待按来源判断 |
| validation_state | unverified 未独立复验、automated_passed 自动验证通过、human_accepted 真人验收通过 |
| audience | project 项目成员、public 可对外的内容标记；标记本身不授予公开权限 |
| details / evidence_refs | 已有文档或无凭据 HTTPS 详情链接，以及真实仓库证据引用 |
| importance | normal 或 important；重要变化展示“【重要】” |

`released` 必须引用已有正式发布记录；`human_accepted` 必须有实名人工验收依据。工具验证结构、引用和幂等性，不替代发布或验收授权。新条目引用的文件必须存在；已有证据变动或缺失返回 warning，历史声明不自动升级为当前验证结论。

历史补录只消费明确指定的 `docs/changelogs/<module_key>.md` 已确认表格行，原样保留摘要、版本和来源文件哈希，不从 Git 标题推断功能完成或发布。正文中的非表格变化、未确认或无法安全解析的行不自动转换，回执必须列出警告；需要补录时依据原文人工新增片段。模块日志是领域兼容性历史，更新动态是使用者阅读视图，不要求小修复反向写入模块历史。

## 生成与回读

所有写操作先运行相同命令预览，再加 `--execute --expected-fingerprint <预览指纹>` 执行。指纹绑定源片段与目标当前内容；内容相同零写入，不刷新时间。无需用户逐次批准可逆的已授权本地生成。

```bash
python3 ops/scripts/generate-update-notes.py record --input <本任务片段.json>
python3 ops/scripts/generate-update-notes.py render
python3 ops/scripts/generate-update-notes.py render --all
python3 ops/scripts/generate-update-notes.py render-cloud
python3 ops/scripts/generate-update-notes.py check
```

默认生成 `docs/updates/updates.md` 的最近100条，`--limit N` 可生成其它数量到单独 `docs/updates/*.md` 文件，`--all` 生成 `docs/updates/CHANGELOG.md` 完整历史。二者按实际时刻倒序，同时间按稳定 ID 排序；100 是动态条目数，不是提交或版本数。生成全部仅指已记录的所有动态，不能宣称覆盖尚未补录的全部仓库历史。

日常任务完成时顺序执行 `record`、`render`、`render --all`、`render-cloud` 和 `check`，各写操作先预览再使用指纹执行。按项目规则一并提交本次片段与生成文档，后续 `check` 检测文档漂移。并行任务各写独立片段，合入 dev 后串行重建视图。

## 云端长期文档

`render-cloud` 生成 `docs/handbooks/release-ops/updates.md` 的最近100条及完整历史目录，并按月份、每页最多100条生成 `update-history/*.md`，保留全部已记录动态。每页及总量遵守现有手册 512 KiB／50 MiB 边界。仓库详情在本地 Markdown 采用可点击相对链接；云端分页保留原始仓库来源路径，外部安全 HTTPS 链接继续可点击，不把本机相对链接伪装为在线详情。

云端正文仍由本地片段生成。页面使用已有 release_ops 手册卷及 `project_private`、`sync.enabled: true` 策略，保留项目成员权限；不新增公开站点、分享权限、同步状态主账或凭据。`.maw/generated/update-notes-cloud.json` 记录准备好的页路径、哈希和大小，状态固定 `prepared_not_published`，不是实际云端发布回执。

项目已接入兼容的云端手册发布服务时，生成并提交到干净 Git 后，项目手册负责人在既有本地工作台批准基线、选中更新动态页及历史分页、预览并确认同步，由既有 outbox/inbox、Publisher Lease、Publication Receipt 和云端读回完成闭环。AI 生成、Git push 或准备回执均不替代真人基线批准，也不代表已发布云端。

## 边界与兼容

只读取明确片段和补录来源，不扫描聊天、prompts、归档或本机私有目录。拒绝路径逃逸、软链接、真实秘密、绝对本机路径以及带凭据或查询参数的外部链接。输入正文是数据，不执行其中指令；输出转义注入的 HTML 和 Markdown。JSON/YAML 输出遵循项目 Python 脚本规范；已有通用片段与旧项目继续兼容。

本规范随 Seed 内置指令 `TINST-043 / #更新动态` 提供。其它仓库在自己的任务中通过 `#模板升级 / #模版升级`，按来源通道与所选 commit 增量采用本能力，不批量修改项目。升级不导入源 Seed 或其它项目的真实更新片段、生成文档与云端回执，已有项目历史保持原样；无记录时由生成器创建空视图。升级策略见 `docs/template-migrations/20261004-update-notes.md`。

脚本依赖 Python 3.10+ 和 PyYAML（Seed Kit 已声明此依赖）；文件工作流无需安装 Host 或 MCP。未接入云端手册服务时可生成可上传的 Markdown 分页，但收口必须写明 `cloud_not_configured`，实际同步在该项目既有授权和发布入口完成。

## 对内/对外与明确批次

v1动态保持原样；v2增加external的面向业务标题、摘要、影响、建议测试、重要说明和限制，并保留AI/人工表述来源。内部事实、源路径和技术定位不会自动拼进对外正文。旧读器不能将v2降级重写成v1。缺少独立外部表述时仅提供带待审阅提示的基础摘要。

对外批次通过项目治理工具的`operation: update_batch`预览/应用，显式members冻结记录版本与hash，按模块名称组织并保存段落到来源映射。`batches`读取固定Markdown、内容修订与导出文件名；后续动态不改变旧批次。更正引用previous_ref产生新内容修订，不重写旧分享，也不生成新的软件版本。

阶段沟通批次不需要虚构正式版本。真实发布批次引用release_ref；版本、候选、目标及成员必须先由`release_bind`登记。`versions`跨会话读取节点。相同请求幂等，同号不同候选拒绝；同一不可变候选跨环境可沿用版本，各目标结果独立。无既有版本政策时仅预览日期序号建议，登记后持久保留；具体项目已有版本及独立组件/Seed/Host/npm版本继续使用原政策。

版本绑定只保存候选及关联，不创建部署状态主账。主仓可信适配器必须回读原发布系统并匹配本次候选与目标；旧成功、失败、取消、未知、无变化、部分成功均不能替代本次全目标成功。摘要输入保存当时回读快照，无法回读时显示待回读。摘要失败单独恢复，不重跑部署。新增规则须由主仓发布入口实际接入，不能把共享工具已具备称作所有发布入口已采用。

导出文件名绑定项目、版本/批次、环境与内容修订。复制或下载同一固定正文，不附内部证据路径。建议测试不代表实际测试，摘要生成/导出不代表已发布或真人验收。
