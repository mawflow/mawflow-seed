---
doc_key: docs.changelogs.index
doc_type: governance
stage: development
status: active
owner: planner
tags:
  - modules
  - changelog
project_health:
  dimensions:
    - product_module_design
  evidence_level: canonical
read_contract:
  summary: "模块变更日志的集中存储、读取与自动迁移规则。"
  health_signal: "用于检查模块日志是否集中、可追溯且未与 module.md 重复。"
  consumes:
    - .maw/modules.yaml
  produces:
    - docs/changelogs/<module_key>.md
  ai_read_hint: "新增模块、更新实质变更、执行模块地图或遇到旧格式 changelog 时读取。"
---

# 模块变更日志中心

`docs/changelogs/` 是所有正式模块变更日志的唯一存储目录。每个模块使用一个扁平文件：

```text
docs/changelogs/<module_key>.md
```

模块档案不再保存历史表或“最近变更摘要”，只保留：

```text
changelog_path: docs/changelogs/<module_key>.md
changelog_time: <带时区 ISO 8601 时间>
```

`.maw/modules.yaml` 使用相同的 `changelog_path`、`changelog_time` 字段作为机器索引。`changelog_time` 表示集中日志内容最后一次实际变化的时间；只读检查、重复执行或没有新增日志内容时不得刷新。

## 写入范围

集中日志只记录会影响长期理解和兼容性的实质变化：

- 产品或领域边界；
- API、事件或数据兼容；
- 状态机、权限和安全约束；
- 数据迁移；
- 发布、回滚或交付语义；
- 模块合并、拆分、重命名、废弃或替代关系。

例行样式调整、小修复、测试补充、文档措辞和一次性执行流水由 Git 历史追溯，不写入模块 changelog。

## 旧格式自动迁移

执行模块档案、模块地图、变更影响或 changelog 规则前，先运行：

```bash
python3 ops/scripts/migrate-module-changelogs.py plan --format json
```

只要计划发现下列任一旧格式，当前规则执行者必须自动继续运行迁移，不把逐份搬运工作留给用户：

```bash
python3 ops/scripts/migrate-module-changelogs.py migrate --execute --format json
```

自动迁移同时处理：

- `docs/modules/**/changelog.md`；
- `.maw/modules.yaml` 的旧 `changelog:` 字段；
- `module.md` 内嵌的“最近变更摘要”“变更记录”或 `Changelog` 段。

迁移先合并并去重历史，再写集中日志和新引用；只有目标日志与引用写入成功后才删除旧文件。遇到无法唯一归属或相同 entry key 的内容冲突时停止，不删除来源。迁移必须幂等，第二次执行应为零变更。

## 验证

```bash
python3 ops/scripts/migrate-module-changelogs.py check --format json
```

检查必须阻断旧 `changelog:` 字段、旧模块目录日志、内嵌历史段、不存在的 `changelog_path`、无法解析的 `changelog_time` 和重复迁移后仍产生变更的状态。
