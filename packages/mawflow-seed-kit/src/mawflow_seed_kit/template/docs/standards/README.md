---
doc_key: standards.README
doc_type: governance
stage: governance
status: active
owner: project-owner
tags:
- standards
- lifecycle
read_contract:
  summary: 项目阶段规范入口
  ai_read_hint: 按当前阶段、任务范围与风险读取，不全量扫描规则。
---

# 项目阶段规范入口

按立项、设计、开发、测试、部署、交付六阶段定位规范；同一迭代、模块或变更按其范围进入相应阶段。小修复可直接进入开发，补查受影响设计和验证，不重做整个项目立项。故障、回滚、维护和升级按影响返回相关阶段。

- [六阶段规范索引](index.md)：由 `.maw/standards.yaml` 生成，显示触发条件、执行方式及唯一权威引用。
- [统一总则](general.md)：来源、授权、责任边界、证据和规则修订。
- [项目适用规则](project-adoption.md)：新建、存量接管、技术栈和客户交付按事实裁剪。
- [任务清单与证据](task-checklists.md)：最小任务、常规迭代、正式交付；状态和回执独立。
- [经验与资源复用](knowledge-resources.md)：项目经验、共享/公开经验、文件、测试身份用途和技术 Pack。

规范目录负责分类和引用，不复制业务事实或建立第二份任务、测试、审批、发布账本。六卷手册仍按需求、技术、任务审计、质量、发布运维、决策风险组织阅读与交付产物，卷和执行阶段分别维护。

```bash
python3 ops/scripts/manage-project-standards.py context --phase testing --task-class small_change --task-kind test --format markdown
python3 ops/scripts/manage-project-standards.py check
python3 ops/scripts/manage-project-standards.py render
python3 ops/scripts/manage-project-standards.py validate-task --input docs/standards/examples/small-change.yaml
```

`context/check/validate-task` 只读。`render` 先预览，再用返回指纹追加 `--execute --expected-fingerprint <指纹>`；内容相同零写入。未采用项目返回 not_adopted，不能报告规范已接入或检查通过。模板示例只说明结构，状态固定 pending，不作为项目授权或执行证据。

- [任务生命周期与资源收尾](../ai-coding/task-lifecycle.md)：跨工具任务阶段、恢复、浏览器控制交还、资源保留及文件侧回执检查。

- [规范执行协议](execution-protocol.md)：显式条件、规则指纹、执行证据、只读任务投影及渐进采用。
