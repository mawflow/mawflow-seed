# code 代码根目录

本目录按照端拆分业务代码：

- `server/`：服务端。
- `client/`：客户端。

每个端都有自己的 `.maw.component.yaml`，用于说明边界、命令、发布配置和 Codex 工作规则。

如果项目确实有独立管理后台前端、独立构建或独立发布目标，可按项目实际新增一个前端组件和 app_key；模板默认不内置 `admin`。

如启用组件镜像仓库，端内 `.maw.component.yaml` 的 `mirror_repository_ref` 只指向 `.maw/repositories.yaml` 中的单向同步配置；`code/<component>` 仍必须是当前项目仓库的普通源码目录，不能变成目标镜像仓库 clone、submodule 或 worktree。

## AI 编码前置规则

AI 修改任何端代码前，必须先阅读：

- `docs/ai-coding/README.md`
- `docs/ai-coding/initialization-checklist.md`
- `docs/ai-coding/coding-style.md`
- `docs/ai-coding/component-guides/<component>.md`
- 当前端目录下的 `.maw.component.yaml`

如果对应端的工程目录说明尚未完成，应先补齐 `docs/ai-coding/component-guides/<component>.md`，再开展功能开发。

## 发布随带文件

发布时需要额外覆盖进某个端目录或发布包的文件，不直接散落在 `code/` 下维护，应放入仓库根目录的 `release/<component>/default` 或 `release/<component>/<app_key>`。

- `release/server/default` + `release/server/<app_key>` 叠加到服务端发布树。
- `release/client/default` + `release/client/<app_key>` 叠加到客户端发布树。

具体规则以 `release/rules.yaml` 为准。
