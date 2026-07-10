# 各端工程目录说明

本目录按端维护工程结构、命令、边界和常见改动入口。

## 文件

- `server.md`：服务端工程说明。
- `client.md`：客户端工程说明。

每个文件应与对应端的 `code/<component>/.maw.component.yaml` 保持一致。

组件 guide 只描述端工程边界，不替代业务模块档案。业务模块应继续在 `docs/modules/` 中按 group / leaf 拆分。

如项目存在独立管理后台前端，可按项目实际新增组件 guide；模板默认只内置 `server` 和 `client`。
