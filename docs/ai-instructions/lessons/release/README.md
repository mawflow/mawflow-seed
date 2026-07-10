# 发布经验目录

本目录保存发布、部署、上线、回滚和上线后验收相关经验。它面向模板仓库的 fork 项目提供参考：后续项目可以按技术栈、服务器环境、组织流程和安全要求删改、复制或升级为自己的项目指令。

## 定位

- 本目录是“经验库”，不是强制流程库。
- 经验文档可以包含命令示例、目录模型和检查清单，但示例中的项目名、域名、数据库、服务器路径、密钥引用和客户配置都必须按 fork 项目实际情况修改。
- 如果某条经验在 fork 项目中已经稳定成为固定流程，应在该项目内沉淀到 `docs/ai-instructions/instructions/`，并在项目总纲中登记触发词。
- 新增发布经验时可参考 `../../templates/lesson.md`，但发布类文档必须额外写清脱敏边界和项目字段替换规则。

## 建议文件命名

- `<stack>-<component>-release.md`：适合框架或组件发布经验，例如 `fastadmin-server-release.md`。
- `<component>-<environment>-deploy.md`：适合按环境沉淀部署经验，例如 `server-test-deploy.md`。
- `<platform>-<artifact>-publish.md`：适合平台或制品发布经验，例如 `oss-static-publish.md`。

## 当前条目

| 文件 | 主题 | 适用场景 |
| --- | --- | --- |
| [fastadmin-server-release.md](fastadmin-server-release.md) | FastAdmin 服务端发布经验 | 迁移或审查 FastAdmin / ThinkPHP 后端发布脚本、发布流程和验收清单 |
