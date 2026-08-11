# MAWflow CLI

CLI 是确定性的终端接口，适合极客、高频操作和自动化。

```bash
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
```

需要先审阅变更时给写操作加 `--plan`；应用已保存计划使用 `--execute --plan-file <path> --confirm '<确认串>'`。直接执行写操作时，CLI 仍会在内部生成可回滚计划再应用。
