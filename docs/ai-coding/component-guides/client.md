# client 工程目录说明

## 基本信息

- 代码目录：`code/client/`
- 端配置：`code/client/.maw.component.yaml`
- AI 调试索引：`.maw/app-runtime.yaml` 的 `app_runtime.apps.client`
- 技术栈：待项目初始化后补充。

## 目录结构

| 路径 | 用途 | 备注 |
|---|---|---|
| `code/client/src/` | 客户端源码 | 待补充 |
| `code/client/tests/` | 客户端测试 | 待补充 |

## 命令

以 `code/client/.maw.component.yaml` 为准，初始化时需校验安装、启动、测试、构建命令。

## 发布配置

- 默认发布环境：读取 `code/client/.maw.component.yaml` 的 `release.default_environment`，未配置时回退到 `.maw/releases.yaml` 的 `releases.defaults.default_environment`。
- 可选发布环境：读取 `release.environment_options` 和 `.maw/releases.yaml` 的 `releases.defaults.environment_options`；模板默认包含 `test`、`staging`、`production`，项目可追加其它环境。
- 快捷发布指令：读取 `release.commands` 或 `.maw/releases.yaml` 的 `releases.components.client.release_commands`，最终说明中需要发布时必须按配置列出 `#发布：发布 client`、指定环境发布指令，以及可用的 `#发布测试`、`#发布上线`、`#发布生产`、`#发布生成` 中文口令。
- 默认组件范围：如果用户说 `发布测试`、`发布上线`、`发布生产` 或 `发布生成` 且未指定组件，按 `.maw/environments.yaml` 对应 `remote_server.default_release_components` 判断是否包含 `client`；`发布测试` 是本地调试版本，需给可访问调试地址；`发布上线` 是部署到 `remote_staging_server` 的编译包部署测试，仍属于测试，需给线上可访问地址；`发布生产` 是部署到 `remote_production_server` 的生产发布，涉及生产环境安装或版本上线必须人工审计。
- 版本状态：发布前按 `artifacts/release-state/<env>/client.json` 的已发布 commit 与本地候选 commit 比较；只有 `code/client`、`code/client/.maw.component.yaml`、`release/client/default`、`release/client/client` 或共享发布配置发生变化时，client 才应纳入发布名单。`发布上线` 和 `发布生产` 还必须先确认本地候选 commit 等于发布来源远端分支。

## 配置规则

- 业务配置权威来源：`code/client/` 内部工程文件，例如 `.env.example`、请求封装、构建配置和平台配置。
- AI 调试镜像：`.maw/app-runtime.yaml` 和 `.maw/secrets.yaml` 的 `secrets.app_debug.apps.client`，用于显式记录 API 地址、URL 和测试账号引用。
- 如两者冲突，以 `code/client/` 内配置为准，并同步修正 `.maw` 调试索引。

## AI 可改边界

- 可改：待补充。
- 慎改：路由、全局状态、请求封装、构建配置、设计系统基础组件。
- 禁改：`.maw/*.local.yaml`、`.ssh/**` 真实 key 文件、裸 `.env`、构建产物、依赖目录、用户上传素材和未脱敏外部交付资料。

## 常见任务入口

- 待分析。
