# 组件目录

新项目不内置组件。请用 CLI 显式创建或采纳组件：

```bash
mawflow component init api --type backend
mawflow component adopt code/legacy --key legacy --type custom
```

组件默认禁用；确认可以参与开发、验证和发布后再执行 `mawflow component enable <key>`。
