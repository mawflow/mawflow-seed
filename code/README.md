# 组件目录

种子仓库不内置 `server`、`client` 或示例组件。新组件由 CLI 显式建立，默认禁用：

```bash
mawflow component init api --type backend
mawflow component adopt code/legacy --key legacy --type custom
mawflow component doctor api
mawflow component enable api
```

每个组件初始只包含 `README.md` 与隐藏的 `.maw.component.yaml` 边界描述，不预设技术栈、源码目录或运行端口。
