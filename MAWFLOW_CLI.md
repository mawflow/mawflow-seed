# MAWflow CLI 使用指南

CLI 是项目治理的确定性入口；AI 指令是对话意图。不要把二者混成同一种语法。

## 项目初始化

```bash
mkdir my-project && cd my-project
git init
mawflow project init .
```

已有 Git 仓库同样在根目录执行 `mawflow project init .`；命令会保留已有业务文件并建立 Seed。`mawflow project adopt` 是兼容别名。

初始化结果不含默认组件，只保留 `code/README.md`。旧 `--profile web-api/service/minimal` 参数暂时兼容，但与 `blank` 一样不再生成 `server/client`。

## 组件流程

```bash
# 统一添加入口：项目内新建或采纳、外部 Git 声明与当前设备绑定
mawflow component add api --type backend
mawflow component add api --type backend --source-mode external_git \
  --repository-url https://git.example.com/team/api.git \
  --source-directory /path/on/this-device/api \
  --git-access-profile mawgit://example-profile

# 新组件：只生成 README 和边界描述，默认禁用
mawflow component init api --type backend

# 存量目录：保留源码并纳入治理
mawflow component adopt code/legacy --key legacy --type custom

mawflow component list
mawflow component show api
mawflow component doctor api
mawflow component enable api
mawflow component disable api

# 外部 Git 组件在另一台设备绑定自己的真实目录；不会改共享仓库
mawflow component source bind api /path/on/another-device/api \
  --git-access-profile mawgit://example-profile
mawflow component source unbind api

# 从项目注销组件；默认保留项目内或外部磁盘目录
mawflow component remove api
```

写操作可加 `--plan` 只保存和展示计划。自动化执行已有计划时使用 `mawflow component apply --execute --plan-file <path> --confirm '<确认串>'`。`init/adopt` 是兼容入口，与 `add` 复用同一 Seed plan/apply 内核和错误码。

外部源码的共享事实只写 `.maw/components.yaml` 中的 `source.mode/repository_url/repository_subpath/default_branch`；每台设备不同的绝对目录和 Git Access Profile 只写被 Git 忽略的 `.local/.maw/component-sources.yaml`。不要把绝对路径、凭证或代理 URL 写入 `.maw/**`。Profile 可选择继承系统代理、强制直连或引用独立 SecretStore 网络路由；代理明文仅在 Host Git 子进程内解析。解绑、禁用和移除都不会永久删除源码目录。

## AI 对话入口

对 AI 说“初始化组件 api，类型 backend”“启用组件 api”时，AI 应读取 `PROJECT_COMMANDS.md`，再调用上述 CLI 或执行同等验证链路。跨 AI 交接见 `CHATGPT_TO_AI.md`。
