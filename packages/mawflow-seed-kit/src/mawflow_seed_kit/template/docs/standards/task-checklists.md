---
doc_key: standards.task-checklists
doc_type: governance
stage: governance
status: active
owner: project-owner
tags:
- standards
- lifecycle
read_contract:
  summary: 任务清单、独立状态与证据
  ai_read_hint: 按当前阶段、任务范围与风险读取，不全量扫描规则。
---

# 任务清单、独立状态与证据

任务清单是原任务及证据的快照，不推进PM/TestRun/Audit/Release，不建立新主账。task_ref引用真实任务或当前可定位的用户授权；已有确认沿用同一范围，新任务不继承未证明的授权。

| 深度 | 适用场景 | 必需信息 |
| --- | --- | --- |
| small_change | 单模块小修复、普通文档 | 范围、已有授权、相关契约、定向验证、未覆盖及影响 |
| iteration | 新能力、流程或跨模块变更 | 需求/设计/依赖、任务路径、风险、相关测试、事实更新 |
| formal_delivery | 部署、客户交付、数据库或正式验收 | 冻结来源/目标/制品、审批与恢复、实际候选、回读、交付快照和独立验收 |

每次任务记录源码/制品版本、模块、read/write/blocked路径、目标环境、目标基线、授权依据和允许动作。例外必须显式引用已确认精确范围。授权字段只是声明，检查器不授予权限；读取范围不等于写入许可。

六种状态轴（implementation、verification、external_integration、delivery、deployment、human_acceptance）分别使用pending/partial/passed/failed/not_applicable。passed必须有匹配该轴、版本、环境、scope_hash的原有回执引用与证据文件哈希；真人轴另需actor与confirmation_ref。只有待确认或文档声明不能推导passed；业务不适用才标not_applicable，缺证据用pending。

verification同时列本任务选中suite、结果及证据。空suite不能是passed，失败/未运行的选中suite不能被总体passed掩盖。文件改变、环境或scope_hash不匹配、证据缺失返回blocked，旧回执保留但需重新核验。检查器只核验声明及摘要，不能证明用户说过某句话、命令实际执行、有权审批或目标部署成功。

输入或基线变化时核对影响，复用条件与任务回执一起保存；续跑从未完成步骤开始，不重放非幂等写入。标准模板只包含pending和空证据，填入真实任务后再校验：[小修复](examples/small-change.yaml)、[常规迭代](examples/iteration.yaml)、[正式交付](examples/formal-delivery.yaml)。

```bash
python3 ops/scripts/manage-project-standards.py validate-task --input docs/standards/examples/small-change.yaml
```

规则目录按执行阶段选择，文档front matter的stage用于文档分类，两者分别维护。生成规范索引不是任务完成或部署证明。
