# mawflow-seed-kit

`mawflow-seed-kit` 是 Seed Contract v2 的唯一可执行分发包。v2.1.2 在保持协议主版本为 2 的同时，补齐项目分类与目标、技术栈、三层环境、凭证需求、模块依赖和六卷项目手册，并继续提供 Project Definition 编译器、ChangeSet 规划与应用、当前版本契约安全修复、旧项目一次性增量迁移以及新项目模板。迁移会保护业务 README、既有模块事实和项目私有文件，只归一化能够确定含义的契约字段。

主仓 CLI 和 Host Program 必须固定消费同一版本；项目仓库通过 `.maw/seed.lock` 记录版本、BOM 和契约指纹。

本包提供 Python API 与只读诊断命令：

```bash
mawflow-seed-kit catalog
mawflow-seed-kit doctor /path/to/project
```

项目创建应通过 `mawflow project init`，已有项目迁移应通过 `mawflow project adopt/upgrade` 或本地工作台执行；不要直接复制包内模板覆盖现有仓库。

迁移应用会生成仅保存在指定私有备份目录的哈希清单。需要回退时，调用 `rollback_migration(...)` 并提供迁移结果中的 `plan_key` 与精确确认串；回退前会校验当前文件仍等于迁移候选，避免覆盖迁移后的并发修改。
