# MAWflow CLI

CLI 是确定性的终端接口，适合极客、高频操作和自动化。

```bash
# 统一添加入口；默认项目内源码
mawflow component add api --type backend

# 一个 MAWflow 项目可登记多个独立子项目
mawflow subproject add customer-portal --name 客户门户 --grouping-basis same_customer

# 同一 Git 仓库登记一次，多个组件共享
mawflow code-source add customer-suite \
  --repository-url https://git.example.com/customer/suite.git \
  --default-branch main
mawflow component add portal-api --type backend --subproject customer-portal \
  --source-mode external_git --repository-ref customer-suite --repository-subpath server
mawflow component add portal-web --type frontend --subproject customer-portal \
  --source-mode external_git --repository-ref customer-suite --repository-subpath web

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

# 新设备补全全部缺失源码；托管 clone 默认放在 .local/code-sources/<source-key>/
mawflow project hydrate --git-access-profile mawgit://example-profile --execute

# 2.4 项目可先审阅再把同仓库的组件级声明归并为共享代码源；不移动源码
mawflow project sources consolidate --plan
```

需要先审阅变更时给写操作加 `--plan`；应用已保存计划使用对应命令的精确确认串。直接执行写操作时，CLI 仍会在内部生成可回滚计划再应用。Git Access Profile 可独立选择继承、直连或 SecretStore 网络路由；共享 Seed 与云端 readiness 不保存代理明文、本机绝对路径、源码内容或未提交改动。

多个线上或生产服务器通过 `.maw/deployments.yaml` 的稳定部署目标配置。服务器资源可复用，但每个目标必须显式选择 `environment_role`、`server_ref`、可选子项目和 `component_refs`；空范围不代表全部组件，生产门禁不能通过自定义环境 key 绕过。
