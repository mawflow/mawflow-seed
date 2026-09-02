# mawflow-seed-kit

`mawflow-seed-kit` 是 Seed Contract v2 的唯一可执行分发包。v2.6.0 增加多部署目标：一个环境可绑定多个服务器目标，每个目标显式选择子项目与组件范围；服务器仍是可复用资源，组件继续保持独立 app_key、源码、构建、发布和回滚边界。v2.5 的多子项目、共享代码源、新设备 hydrate 与 `.local/code-sources/` 托管 clone 保持兼容。

主仓 CLI 和 Host Program 必须固定消费同一版本；项目仓库通过 `.maw/seed.lock` 记录版本、BOM 和契约指纹。

本包提供 Python API 与只读诊断命令，面向用户的组件操作由 `mawflow component ...` 暴露：

```bash
mawflow-seed-kit catalog
mawflow-seed-kit doctor /path/to/project
mawflow-seed-kit doctor credentials /path/to/project --fail-on-plaintext
```

项目创建应通过 `mawflow project init`，已有项目迁移应通过 `mawflow project adopt/upgrade` 或本地工作台执行；不要直接复制包内模板覆盖现有仓库。

迁移应用会生成仅保存在指定私有备份目录的哈希清单。需要回退时，调用 `rollback_migration(...)` 并提供迁移结果中的 `plan_key` 与精确确认串；回退前会校验当前文件仍等于迁移候选，避免覆盖迁移后的并发修改。
