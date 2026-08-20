# 公开 payload 模块地图与技术地图资产对齐

- 日期：2026-08-20
- 风险等级：T2
- 源模板基线：`27b89e575b4e1bcb7f64e24fa3a46c9b7fb330b3`
- 适用范围：通过公开 Seed 使用模块地图、技术地图和集中 changelog 协议的新项目与既有派生项目。

## 问题

旧公开 payload 已分发模块地图、技术地图和集中 changelog 的协议文档，但没有分发对应索引、模板和执行脚本。文档中的 canonical 命令因此在公开工作区直接报“文件不存在”，而旧门禁仍可能返回 ready。

## 变化

- 新项目初始化空的 `.maw/module-candidates.yaml`、`.maw/capabilities.yaml` 和 `.maw/project-signals.yaml`。
- 公开 payload 增加集中 changelog、技术地图、能力模板、项目信号模板和五个地图相关脚本。
- `check-template-module-docs.sh` 与 `check-technical-map.sh` 可识别公开工作区，只校验公开契约；Seed 维护仓仍执行完整维护检查。
- `PUBLIC_PAYLOAD_MANIFEST.json` 同时登记 required paths 和 smoke commands，发布物化阶段必须真实运行文档中的命令。
- 公开物化使用 Seed Kit 的空索引覆盖 Seed 维护仓自身地图，避免把维护事实传播到业务项目。

## 既有项目取舍矩阵

| 目标项目状态 | 处理 |
| --- | --- |
| 三个索引均缺失 | 从公开空索引初始化，再按项目事实填写 |
| 已有任一索引 | 保留原文件，只补缺失字段或缺失文件 |
| 已有集中 changelog | 保留并运行迁移 `plan/check`，禁止覆盖历史 |
| 仍有旧 `docs/modules/**/changelog.md` | 先 `plan`，无冲突后 `migrate --execute`，再次 `check` |
| 自定义检查脚本 | 保留项目脚本，按文档声明与目标 payload 一致性做语义合并 |
| 冲突或无法确认 owner | fail closed，不删除来源，不猜测模块归属 |

## 验证

```bash
python3 ops/scripts/migrate-module-changelogs.py check --format json
sh ops/scripts/check-template-module-docs.sh
sh ops/scripts/check-module-candidates.sh
sh ops/scripts/check-technical-map.sh
python3 ops/scripts/extract-project-metadata.py --format json
```

验证必须分别在 Seed 源树、实际生成的公开 payload 和不含 Seed 维护元数据的 fresh derived fixture 中完成；只在源树通过不算完成。
