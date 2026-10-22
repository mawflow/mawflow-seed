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

## 可读口径、人工维护与批量修订（v4）

`reading`从同一精确问答版本生成分章全文，业务、技术、环境阶段、经验分区；目录排序不改变question_key/scope或确认效力。`organize`只改章节和顺序。

人工可直接`confirm`新增/编辑，或`retire`删除当前口径，不依赖AI任务；预览提供完整前后正文和档案/基线/读取引用影响。删除只退出有效阅读/context，保留历史引用。

自然语言经AI整理为`revision_batch`候选，`intent: propose`不改变有效规则。人工精确选中后以`intent: confirm`提交changes，每批最多30项，完整正文、base_refs、来源版本和指纹共同绑定。部分选择只确认选中项，一批一个完成标记；旧页面与并发变更不得静默覆盖。

`baseline --mode initialize|audit|repair`只读生成完整盘点、逐题迁移对照、六维覆盖和缺口；显式`--source`冻结允许的来源。真正写候选/固定快照使用`operation: baseline`的预览/应用。audit禁止项目写入；报告可由原执行器保存为本任务结果。未核验的覆盖保持缺口，全面初始化不能由AI执行成功替代。冻结需要精确人工来源、已确认问答和无范围缺口。相同输入重复运行复用原快照。

覆盖六维是职责范围、角色权限、对象术语、流程状态、约束异常、外部依赖。覆盖声明需明确问答版本和理由；它仍是审计声明，人工审阅与业务规则确认独立。代码提交及显式文件hash用于追溯，不表示整个工作区均已验证。来源变化只提示基线复核，不自动废除规范性需求。

此扩展使用document_source.v4/work_event.v3；未知版本须升级，旧工具不能丢字段重写。详见`docs/ai-coding/governance-suite.md`。

## 自然语言理解、纠偏与经验复用

自然语言是正常入口。用户表达目标后，AI负责整理对象、范围、环境、读写意图和完成标准，并映射既有指令；信息足够时沿用已有授权继续，只有影响依赖动作的真实歧义才需澄清。快捷指令仍可精确调用，不要求用户填写内部字段。

每次任务判断学习价值，只保存新叫法、纠偏、边界变化与有效复用反馈的最小公开摘要；重复表达复用原记录。完整聊天、私人会话、隐藏推理、秘密和本机绑定不收录。只读任务只在输出提供待收录摘要，不写来源、消费或反馈。

先检查`read.capabilities`是否包含`natural_language_learning.v1`。共享实现提供只读`recall --utterance <用户表达> [--scope ... --module ... --environment ...]`与`learning-report`；安装Kit与项目内工具同源，旧工具明确升级，不伪装已接入。

- 理解案例沿用`propose/confirm/reject/retire`，`category/claim_type`均为`experience`，稳定question_key/scope管理版本。可附`learning: {kind: rule, utterances: [...], negative_examples: [...], intent: ..., operation_mode: read_only|modify, environments: [...]}`。完整含义仍写在answer。用户明确纠偏可作为其准确范围的确认依据；AI新解释保持候选，不由次数或执行成功自动确认。
- `recall`只返回当前已确认且条件匹配的案例；模块、特定scope和环境需显式匹配。候选、冲突、证据变化、负例与停用版本不作为可复用结论。结果包含精确rule_refs、来源hash、recall_hash、截断和缺口。当前实现是有界词面召回，语义理解由实际Agent完成；未命中须改写检索或按范围读取context中的完整案例，不宣称语义搜索已覆盖。
- 案例模式只是理解提示，不授予执行权限。多种模式冲突、截断或收到纠偏反馈时提示澄清，仅暂停依赖动作。当前任务授权始终独立核对。
- 实际阅读`context`和召回正文后，沿用`consume`增加`recall_query/recall_hash/rule_refs`，绑定真实task/run/consumer及精确context_hash/question_refs。变化或歧义拒绝消费。回执为AI声明，不证明执行或真人验收。
- `feedback`引用同任务同轮的`reuse_ref`，提供outcome（useful/corrected/inapplicable/unknown）、rationale、result、validation。反馈不改口径；corrected使旧案例提示复核，人工确认继承旧版的新口径后才恢复。反馈数量和useful只是记录声明，不当作理解准确率或自动晋级依据。

经验仍保存在`docs/intake`来源事件；`docs/ai-instructions`负责可检索说明和索引，不复制第二套可独立修订的规则。项目、本机、账号/空间与公开范围分开，项目经验不自动进入Seed公共默认案例。

验收需覆盖真实纠偏摘要、独立新进程召回/消费、同义改写、负例、歧义、越范围、失效证据、停用、过期回执、重复请求和只读零写入。合成回归只证明协议与传输；实际模型理解、跨Agent效果和真人验收分别给出证据。迁移见`docs/template-migrations/20261022-natural-language-learning.md`。

## 明确收录的项目档案（v4）

`library`只列出来源事件明确登记的成员，保留稳定文档身份和固定修订，不把目录里所有文件自动列为档案。分类为方案与决策、需求与业务、设计与技术、测试与验收、发布与交付、使用与维护、参考资料；不明确时保留待整理。来源与分类、草稿/待审阅/定稿、当前/历史、来源新鲜度、同步及软件发布状态独立。

`register`用于明确任务文档、沉淀、已有资料和人工导入。输入document_key/document_title/document_kind、document_category、summary、origin，可提供body或显式docs下Markdown/文本source_path。普通登记默认不选择业务口径，无关口径待复核不阻断方案入档。输出正文优先，来源与版本可展开。未选资料不读取、不移动。

人工原件使用受管resource_ref、content_hash、mime、size、original_name；共享工具只登记引用，不宣称已保存或可预览。Host必须按项目身份验证原件字节和受管存储，默认不进Git或云端。相同文件名不静默覆盖。

body、source_path和resource_ref不能混淆；同请求重试复用回执，文件已保存但来源完成标记失败时只恢复登记。回执documents返回确切版本、内容hash及可读引用。修订必须引用当前previous_ref，已有正文/分享不变；分支冲突不按更新时间覆盖。定稿需明确人工来源与审阅引用，不等同业务确认或真人验收。

`templates`提供delivery-v1五类交付文档结构及生成约束。真实AI按选定读者、范围、精确口径与资料生成完整正文，再以草稿登记；资料不足明确缺口。结构清单或字段汇编不冒充正式交付正文。
