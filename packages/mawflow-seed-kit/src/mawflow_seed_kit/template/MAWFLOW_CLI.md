# MAWflow CLI

CLI 是确定性的终端接口，适合极客、高频操作和自动化。

```bash
# 统一添加入口；默认项目内源码
mawflow component add api --type backend

# 外部 Git 源码：共享仓库只记录远端身份，本机目录与 Profile 留在 .local
mawflow component add worker --type backend --source-mode external_git \
  --repository-url https://git.example.com/team/worker.git \
  --source-directory /path/on/this-device/worker \
  --git-access-profile mawgit://example-profile

# 在当前 Git 仓库建立 Seed（新目录先 git init）
mawflow project init .

# 创建空组件目录与组件说明，默认禁用
mawflow component init api --type backend

# 把已有目录纳入治理，不覆盖源码
mawflow component adopt code/legacy --key legacy --type custom

# 查看、检查、启用和禁用
mawflow component list
mawflow component show api
mawflow component doctor api
mawflow component enable api
mawflow component disable api

# 每台设备可绑定不同的外部目录；解绑和移除均保留磁盘源码
mawflow component source bind worker /path/on/another-device/worker \
  --git-access-profile mawgit://example-profile
mawflow component source unbind worker
mawflow component remove worker
```

需要先审阅变更时给写操作加 `--plan`；应用已保存计划使用 `mawflow component apply --execute --plan-file <path> --confirm '<确认串>'`。直接执行写操作时，CLI 仍会在内部生成可回滚计划再应用。Git Access Profile 可独立选择继承、直连或 SecretStore 网络路由；共享 Seed 与 CLI 输出不保存代理明文。
