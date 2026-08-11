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
# 新组件：只生成 README 和边界描述，默认禁用
mawflow component init api --type backend

# 存量目录：保留源码并纳入治理
mawflow component adopt code/legacy --key legacy --type custom

mawflow component list
mawflow component show api
mawflow component doctor api
mawflow component enable api
mawflow component disable api
```

写操作可加 `--plan` 只保存和展示计划。自动化执行已有计划时使用 `--execute --plan-file <path> --confirm '<确认串>'`。禁用组件不会删除目录或源码。

## AI 对话入口

对 AI 说“初始化组件 api，类型 backend”“启用组件 api”时，AI 应读取 `PROJECT_COMMANDS.md`，再调用上述 CLI 或执行同等验证链路。跨 AI 交接见 `CHATGPT_TO_AI.md`。
