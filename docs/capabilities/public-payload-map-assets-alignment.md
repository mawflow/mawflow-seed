---
doc_key: docs.capabilities.public-payload-map-assets-alignment
doc_type: capability
stage: governance
status: active
owner: planner
tags:
  - public-seed
  - module-map
  - technical-map
read_contract:
  summary: "约束公开 Seed 的模块地图、技术地图、集中 changelog 文档与实际分发资产始终一致。"
  ai_read_hint: "维护公开 payload、地图协议、检查脚本或派生项目初始化资产时读取。"
---

# 公开 payload 地图资产一致性

## 能力边界

公开 Seed 只声明公开工作区内真实存在且可运行的模块地图、技术地图与集中 changelog 命令。Seed 维护仓可以保留更完整的维护检查，但公开工作区必须具备自己的安全降级路径，不能依赖未分发的维护元数据。

## 公开资产

- 空的 `.maw/module-candidates.yaml`、`.maw/capabilities.yaml` 和 `.maw/project-signals.yaml`，供新项目增量填写，不携带 Seed 维护仓或来源项目事实。
- `docs/changelogs/`、`docs/technical-map/`、能力模板和项目信号模板。
- 集中 changelog 迁移、模块候选检查、技术地图检查、项目元数据提取和公开模块文档检查脚本。
- `PUBLIC_PAYLOAD_MANIFEST.json` 中的 required paths 与 smoke commands，作为文档和分发清单的一致性门禁。

## 安全与兼容

- 公开物化时用 Seed Kit 的空索引覆盖维护仓的能力与信号事实；维护仓原始地图不进入公开 payload。
- 已有派生项目存在同名索引时保留项目事实，只初始化缺失文件；不得整文件覆盖。
- `migrate-module-changelogs.py` 继续先计划、冲突失败关闭、成功后删除旧格式，并保证重复执行幂等。
- `extract-project-metadata.py` 对缺失的可选仓库身份、待办和经验索引返回兼容结果，不读取 `.local`、secrets 或客户数据。

## 验证

```bash
python3 ops/scripts/migrate-module-changelogs.py check --format json
sh ops/scripts/check-template-module-docs.sh
sh ops/scripts/check-module-candidates.sh
sh ops/scripts/check-technical-map.sh
python3 ops/scripts/extract-project-metadata.py --format json
```

上述命令同时由公开 payload smoke 运行；只有源树、物化 payload 和 fresh derived fixture 三层均通过才可发布。
