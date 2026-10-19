---
doc_key: standards.execution-protocol
doc_type: governance
stage: governance
status: active
owner: project-owner
---

# 规范选择、证据绑定与渐进采用

本协议补充任务清单的执行字段；规则正文仍由目录中的 authority 负责。任务快照只引用原任务、测试、审批与发布对象，不创建可独立推进的第二份主账。新任务使用本协议；旧快照缺少扩展时显示 not_adopted，不批量改写历史或阻断原有开发。

## 按事实选择

`context` 先按阶段、任务类型裁剪，再用 `--fact NAME=true|false` 判断条件。支持 source_change（源码变化）、project_setup（新建/接管/配置或升级）、requirements_change、public_contract（页面/API/表/公共状态契约）、external_dependency、browser、database、resources（服务/构建/重测试/续跑）、knowledge_reuse。事实由当前任务提供，不能从工具是否可用推断。条件缺失时保留规则并标记 pending_applicability；明确不适用时给出 excluded_rules 及原因。any_facts 任一为真成立，all_facts 全部为真成立；两组同时声明时取交集。

small_change、iteration、formal_delivery 决定交付深度，详见 [任务清单](task-checklists.md)。降低任务深度不能跳过真实部署、数据库、客户交付或浏览器条件。选中规则的 required_reads 仅列权威路径，不自动读取整个文档库。

```bash
python3 ops/scripts/manage-project-standards.py context --phase testing --task-class iteration --task-kind test --fact browser=true --fact database=false
python3 ops/scripts/manage-project-standards.py plan-task --input docs/standards/examples/execution-task.yaml --fact browser=false
python3 ops/scripts/manage-project-standards.py report-task --input docs/standards/examples/execution-task.yaml
```

`plan-task` 只输出 task 预览，使用者保存前核对原授权与范围；命令不写文件，也不将原快照自动升级为完成。`standards_binding` 绑定选择参数、规则版本及规则声明与权威正文的联合指纹。每条决定为 applicable/not_applicable/exception/pending；不适用需理由，例外另需原授权引用。required 规则不能在条件明确适用时标成不适用。成功收口前，待判断须解决，适用项至少引用原记录或有效证据。目录整体变化只提示复核，选中规则或权威内容变化阻断旧绑定，未受影响规则不强制重跑。

`report-task` 生成 task_ref/run_ref、规则和有效证据引用及校验结果；没有状态推进、审批或新任务编号。来源收录、更新动态与模块历史均引用这些原记录，避免重复叙述同一事实。

## 范围边界

read_paths/write_paths/blocked_paths 使用项目相对路径。先消除 `./`、重复斜杠和尾斜杠，再比较相交关系。目录及末尾 `/**` 均包含后代；不支持其它 glob，避免匹配方言差异。写入祖先目录与禁止后代也构成冲突，应细化写入范围，不能把“允许父目录”解释为自动排除禁止子目录。拒绝 `..`、绝对路径、反斜杠和软链接读取。blocked_paths 可以声明 `.local/**`、`prompts/**` 等禁止区，声明不触发读取。

## 执行证据与复用

新任务声明 `evidence_policy.schema: mawflow.task_evidence_policy.v1` 及 run_ref。scope.candidate 为 kind/value：干净提交用 commit/40位提交号（等于 source_revision）；未提交源码或冻结制品用 working_tree/artifact 和 SHA-256。工作树摘要须从明确候选文件清单的相对路径及内容哈希计算，不能只对 HEAD 求哈希。检查器验证声明之间的一致性，实际摘要采集由验证工具负责。

passed 证据必须含 method、带时区 observed_at、task_ref、run_ref、candidate；采用生命周期时另含 scope_revision。继续保留原 path/content_hash、source_revision、environment、scope_hash、record_ref。相同 HEAD 下未提交内容变化也会改变候选摘要并使旧证据失效。方法、时间与文件哈希不是对“真实执行”的密码学证明，仍需可追溯的执行回执。

跨尝试复用必须增加 reuse：from_run_ref、to_run_ref、reason、record_ref、checked_at；检查时间不得早于观察时间，任务、候选、环境及范围仍一致。不得仅换 run_ref 冒充重跑，范围变化必须重新采集相应证据。没有证据用 pending，未采用显示 not_adopted，不补造历史时间。

## 上下文与升级

上下文导出优先分配共享规则和 task_routes，之后才读模块说明。模块可显式声明 ai_doc，或提供同目录 ai-context.md 作为当前职责、边界、入口及验证的短摘要，历史继续保留 module.md。导出显示 required_refs、included_authorities、pending_required_reads（含继续读取偏移）及 deferred_refs。预算不足会显示 needs_required_reads，不能把截断当成已读完。

Agent readiness 对已声明 standards/task_lifecycle 做嵌套结构校验；空值、扁平缩进和缺必需字段不能 ready。旧项目缺扩展仍允许渐进采用。新适配器遇到不支持本协议的旧 Kit 返回明确升级缺口，不静默接受。Git Seed、Kit物化、公共装备包清单、CI pytest 和旧项目升级清单同步维护；发布、Host安装和客户项目采用分别执行，不以本地通过代替。
