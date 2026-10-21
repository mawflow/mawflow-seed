---
doc_key: ai-coding.project-governance
doc_type: protocol
stage: development
status: active
owner: project-owner
---

# 项目口径、AI任务与交付档案

项目口径是有版本、有范围、有确认依据的权威问答；档案是从口径与代码事实形成的固定版本交付物；更新动态说明一次任务实际改变了什么；任务记录说明公开的理解摘要、计划、动作、验证与收口。工作台读取项目目录，不把个人聊天、隐藏推理或通知送达当作执行事实。

## 共享入口

`ops/scripts/manage-project-governance.py` 与已安装 Kit 的 `mawflow_seed_kit.governance.project_governance` 使用同一实现。Host 只加载可信安装包，不执行项目提供的脚本。命令均要求 `--project-key`，`read/context` 只读；`preview/apply` 通过 `--input` 接收 JSON，`apply` 另需 `--work-intent modify --fingerprint <预览指纹>`。

```sh
python3 ops/scripts/manage-project-governance.py read --project-key example
python3 ops/scripts/manage-project-governance.py context --project-key example
python3 ops/scripts/manage-project-governance.py preview --project-key example --input request.json
```

写请求含 `operation/request_id/occurred_at/expected_source_version`，稳定请求标识使重试幂等。精确预览绑定项目、提交身份、请求、来源及证据哈希；内容变化须刷新预览。`occurred_at` 使用带时区的 ISO 时间。来源保持在 `docs/intake`，正文是数据，不授予执行权限。

## 人机对话闭环

- `propose`：AI理解候选。提供 `question_key/scope/question/answer/category/claim_type/rationale`；category 为 business、technical、experience。代码现状使用 implementation_fact，不据此推定需求。
- `message`：疑义、风险、冲突、待办、建议或回复。提供 question_key、scope、message、issue_type、impact、options、recommendation、blocked_actions、continue_actions；reply_to 指向原问题。只等待依赖该结论的动作，其余已授权工作继续。
- `confirm`：人工精确确认答案、适用范围与变更。提供 base_refs 和 confirmation_scope；拒绝 AI 自行把 ai_analysis 标为人工确认。确认可用 resolves_issues 关闭已覆盖的问题。
- `reject/retire`：拒绝候选或停用有效口径；保留历史，不恢复旧祖先。并行确认分支显式冲突，裁决须覆盖全部有效分支。
- `work`：使用 task_ref、run_ref、phase、goal、actions、result、validation 追加公开执行过程；生成说明尚未交给AI时明确记录等待执行，不虚构读取或完成。
- `consume`：AI读取指定 context_hash 和 question_refs 后，以 task_ref、run_ref、consumer_ref 写读取声明。它属于 ai_reported，不能代表运行时证明、实施完成或真人验收。回执保存 context_scope/context_module；读视图按相同范围核对最新上下文，变化时标为 reread_required，历史缺少范围的声明标为 scope_unknown，不推定已消费新版本。

确认来源声明与登录身份验证分开。离线文件可记录用户原话和确认范围，但不能伪称已验证账号。Host 在当前真实会话中校验身份并绑定精确记录哈希；跨设备没有对应证明时显示来源声明。

模块 context 同时包含项目级口径及选中模块口径。超过100条有效口径时返回范围过宽阻断，须缩小任务范围；不静默截掉权威。

外部 AI 接任务时读取项目入口与范围内有效 context，写消费回执，然后按既有任务生命周期记录公开摘要、行动和验证。执行期间新口径出现时，先判断影响范围，在安全检查点重新读取并续写回执；不能把复制交接文案当成 AI 已消费。

## 档案与修订

`artifact` 手动生成 requirements、design、acceptance、delivery、maintenance 五类档案，需 document_key/document_kind，可选 selected_question_refs、evidence_paths、body。依据不足时明确缺口，不虚构完整分析、代码行为或验证结论。代码事实绑定具体文件哈希，因此可以追溯工作区未提交修改。

输出为 `docs/deliverables/<document_key>/<version>.md`，来源条目包含输入指纹、确切问答版本、证据、previous_ref、review_refs。已有版本不可覆盖。通过既有项目空间固定版本分享与审计入口发布所选正文；分享和审阅不自动改口径。

修订指定 previous_ref。文字修订用 editorial，只改变档案；改变业务或技术设定用 substantive，必须有 question_changes 与 review_refs。人工可一次确认精确档案差异和对应问答差异，未覆盖推断仍为候选。

联合修订先原子写入准备中的新档案，核验内容后，再原子追加一个 v3 来源事件，其中同时包含档案版本及所有问答变更。该来源文件是唯一完成标记。标记前的档案不进入档案有效列表，口径与 AI context 仍指向旧版。中断重试继续同一请求，不能补写第二份确认。文件提交完成不等于 Git提交、分享、发布或真人验收。

## 协议兼容与迁移

新增 `mawflow.document_source.v3` 与 `mawflow.document_work_event.v2`；v1/v2历史保持可读。旧写工具拒绝新字段和未知版本，不降级丢弃确认、关联或事务语义。部署新能力前需匹配 Kit/Host；通过能力检测提示升级，不用旧读器写新记录。手册索引和工作台投影是可重建视图，不能成为第二套权威台账。

旧资料保持原样。人工触发按项目或模块生成业务/技术理解时，只显式选择允许读取的来源；AI产出候选及证据，再经上述确认机制成为权威。未识别、过大、失效或冲突来源须暴露解析问题并阻止有歧义的写入。

规范性需求与实现事实分别判断：代码变化只令对应事实依据待复核，不自动撤销已确认需求；实现事实或经验依据变化后不再作为已验证现状消费。联合版本的固定档案自身缺失或哈希不符时，关联问答仍整体隔离，不能提前或单独生效。
