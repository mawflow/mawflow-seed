# server 工程目录说明

## 基本信息

- 代码目录：`code/server/`
- 端配置：`code/server/.maw.component.yaml`
- AI 调试索引：`.maw/app-runtime.yaml` 的 `app_runtime.apps.server`
- 技术栈：待项目初始化后补充。

## 目录结构

| 路径 | 用途 | 备注 |
|---|---|---|
| `code/server/src/` | 服务端源码 | 待补充 |
| `code/server/tests/` | 服务端测试 | 待补充 |

## 命令

以 `code/server/.maw.component.yaml` 为准，初始化时需校验安装、启动、测试、构建命令。

## 发布配置

- 默认发布环境：读取 `code/server/.maw.component.yaml` 的 `release.default_environment`，未配置时回退到 `.maw/releases.yaml` 的 `releases.defaults.default_environment`。
- 可选发布环境：读取 `release.environment_options` 和 `.maw/releases.yaml` 的 `releases.defaults.environment_options`；模板默认包含 `test`、`staging`、`production`，项目可追加其它环境。
- 快捷发布指令：读取 `release.commands` 或 `.maw/releases.yaml` 的 `releases.components.server.release_commands`，最终说明中需要发布时必须按配置列出 `#发布：发布 server`、指定环境发布指令，以及可用的 `#发布测试`、`#发布上线`、`#发布生产`、`#发布生成` 中文口令。
- 默认组件范围：如果用户说 `发布测试`、`发布上线`、`发布生产` 或 `发布生成` 且未指定组件，按 `.maw/environments.yaml` 对应 `remote_server.default_release_components` 判断是否包含 `server`；`发布测试` 是本地调试版本，需给可访问调试地址；`发布上线` 是部署到 `remote_staging_server` 的编译包部署测试，仍属于测试，需给线上可访问地址；`发布生产` 是部署到 `remote_production_server` 的生产发布，涉及生产环境安装或版本上线必须人工审计。
- 版本状态：发布前按 `artifacts/release-state/<env>/server.json` 的已发布 commit 与本地候选 commit 比较；只有 `code/server`、`code/server/.maw.component.yaml`、`release/server/default`、`release/server/server` 或共享发布配置发生变化时，server 才应纳入发布名单。`发布上线` 和 `发布生产` 还必须先确认本地候选 commit 等于发布来源远端分支。

## 配置规则

- 业务配置权威来源：`code/server/` 内部工程文件，例如 `.env.example`、框架配置和数据库迁移配置。
- AI 调试镜像：`.maw/app-runtime.yaml` 和 `.maw/secrets.yaml` 的 `secrets.app_debug.apps.server`，用于显式记录数据库、缓存、URL 和测试账号引用。
- 如两者冲突，以 `code/server/` 内配置为准，并同步修正 `.maw` 调试索引。

## AI 可改边界

- 可改：待补充。
- 慎改：配置、数据库迁移、认证授权、支付、文件上传、发布脚本。
- 禁改：`.maw/*.local.yaml`、`.ssh/**` 真实 key 文件、裸 `.env`、运行日志、缓存、用户上传文件和未确认的生产发布配置。受信任 `.maw/secrets*.yaml` 可按任务要求维护，外部交付前必须脱敏。

## 常见任务入口

- 待分析。
