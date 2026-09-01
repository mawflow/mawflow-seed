# Seed Contract v2

Seed Contract v2 是 MAWflow CLI、Host、本地工作台和项目仓库共同遵守的项目定义协议。它的目标不是把一套大模板复制到每个项目，而是让项目事实可编译、可视化、可安全变更、可迁移。

从统一候选 `v2.3.1` 起，公开 Seed Git 与 Seed Kit 使用同一个完整 SemVer，`contract_version` 固定取该 SemVer 的主版本；重大升级必须三者同时更新。Catalog 指纹继续区分同一主版本内的契约内容变化。

## 单一事实链

```text
maw-project-template
  └─ mawflow-seed-kit 2.5.0
       ├─ Contract / JSON Schema
       ├─ UI + Operation Catalog
       ├─ profiles / project template
       ├─ Project Definition compiler
       ├─ ChangeSet planner + applier
       ├─ 0.2.x / Seed 2.0 migration + rollback
       └─ technology / environments / six-volume handbooks
                ↓ fixed dependency
MultiAgentWorker CLI + Host Adapter + local Seed Studio
                ↓ preview / confirm
project .maw/ + .local/.maw/
```

种子仓是协议和工具的唯一开发源；主仓提供产品适配与本地 UI；项目仓保存事实；Project OS 是可重建投影，不是第二账本。

## v2 内核

有效项目必须包含：

- `.maw/seed.lock`
- `.maw/project.yaml`
- `.maw/project-lifecycle.yaml`
- `.maw/technology.yaml`
- `.maw/subprojects.yaml`
- `.maw/code-sources.yaml`
- `.maw/components.yaml`
- `.maw/modules.yaml`
- `.maw/app-runtime.yaml`
- `.maw/environments.yaml`
- `.maw/project-doctor.yaml`
- `.maw/template-source.yaml`
- `.maw/upgrade-policy.yaml`
- `.maw/agent-entry.yaml`
- `AI_START_HERE.md`
- `MAWFLOW_CLI.md`
- `PROJECT_COMMANDS.md`
- `CHATGPT_TO_AI.md`
- `code/README.md`
- `docs/handbooks/manifest.yaml`

`.maw/seed.lock` 固定 `seed_version`、`contract_version`、`contract_fingerprint`、profile、来源和 BOM。lock 缺失或指纹漂移时，编译器可以诊断，但本地工作台不得写入。

## 可视化管理契约

本地工作台从 Kit 内的 Catalog 生成字段、枚举、必填规则、shared/local 作用域和风险，不维护第二份字段表。当前登记操作包括：

- 更新项目定义；
- 新增、更新、停用或删除组件；
- 新增、更新和确认模块及其依赖、并行组、交付优先级；
- 新增或更新应用运行配置；
- 新增或更新 local/staging/production 环境；
- 更新技术栈，新增或更新语言、框架和基础服务；
- 声明凭证需求但不接受凭证值；
- 更新六卷手册清单和证据要求；
- 更新项目生命周期白名单字段。

新增组件时，工作台可在同一个 ChangeSet 中同时写入 `.maw/components.yaml` 和 `.maw/app-runtime.yaml`。本机运行入口、端口和凭据引用可写入 `.local/.maw/app-runtime.yaml` 或 `.local/.maw/environments.yaml`，写前必须由 Git ignore 事实确认。

### 子项目与共享代码源

`.maw/subprojects.yaml` 把同一 MAWflow 项目中的客户、部署组、产品或其它独立交付单元组织起来。组件通过 `subproject_ref` 归属子项目，但继续独立拥有 app_key、构建、运行、发布和回滚边界。没有显式引用的旧组件按 `default` 子项目解释。

`.maw/code-sources.yaml` 为 Git 仓库提供稳定注册表。同一仓库包含多个端时只登记、clone 和绑定一次，各组件用 `source.repository_ref` 与 `repository_subpath` 指向自己的源码子目录。本机绑定保存在 `.local/.maw/code-source-bindings.yaml`，托管 clone 默认位于 `.local/code-sources/<source-key>/`；外层 Git 必须明确忽略该路径，因此允许嵌套 Git 而不会进入项目版本库。

新设备运行 `mawflow project hydrate` 后按声明补全缺失代码源。云端只允许同步 source key、关联组件和是否需要绑定等脱敏 readiness，不同步本机绝对路径、Git Access Profile、凭据、源码内容、HEAD/dirty 详情或未提交改动。2.4 的组件级外部 Git 声明继续兼容，可通过显式归并计划复用现有目录，不移动源码。

### 组件源码工作区

组件没有 `source` 或 `source.mode: embedded` 时，真实工程位于项目内 `path`；`source.mode: external_git` 时，推荐引用共享 code source。2.4 兼容模式仍可在 `.maw/components.yaml` 保存无凭据 `repository_url`、可选 `repository_subpath/default_branch` 和稳定组件引用，并把设备目录写入 `.local/.maw/component-sources.yaml`。

外部源码未绑定、目录缺失、仓库身份不匹配、Profile 不兼容或网络路由不可解析时，Project Definition 仍可读取共享定义，但当前设备开发 readiness 必须失败关闭，且不得静默回退到 `code/<component>/src`。Git Access Profile 的网络策略与认证引用相互独立：可继承系统环境、强制直连，或引用 SecretStore 中的专用 HTTP/HTTPS/SOCKS 路由；代理 URL 不进入 Seed、计划公开结果或审计事件。

`component add`、`component source bind|unbind` 和 `component remove` 与工作台“添加 code / 绑定 / 仅解绑本机 / 从项目移除”共用 Seed ChangeSet、指纹、精确确认和错误码。remove 先检查 module、runtime、release、mirror 等引用；解绑和移除默认只改治理声明与本机绑定，永不永久删除用户已有目录。

## 写入事务

所有写入都使用两阶段事务：

1. 以 contract/projection fingerprint 和 Catalog 操作生成预览。
2. 校验字段、引用、路径、URL、secret 边界和目标文件 hash。
3. 返回多文件 diff、风险、到期时间和精确确认串。
4. 人工确认后保存私有备份并原子写入全部文件。
5. 重新编译 Project Definition；回读失败时自动恢复所有原文件。
6. 向 `.maw/changes/` 写入不含配置正文和凭据的审计片段。

任一并发冲突、未知操作、越界路径、明文 secret、带认证信息 URL、无效引用或未忽略本机文件都会在写前失败，不允许部分成功。

## 初始化与迁移

新项目默认使用 `blank` profile，不内置 server/client 或示例组件：

```bash
mawflow project init my-project
cd my-project
mawflow project doctor --root .
mawflow component add api
mawflow component enable api
```

旧 `web-api`、`service` 和 `minimal` 参数仅保留调用兼容，与 `blank` 一样不再隐式创建组件。

已有 0.2.x 项目只允许一次性迁移：

```bash
mawflow project adopt --root .
# 核对 preview 返回的写入、删除、风险和确认串后再确认
mawflow project doctor --root .
```

迁移会补齐 v2 内核、规范项目身份和组件、增量合并环境/生命周期/技术栈、移动旧本机 overlay、生成 lock 和私有备份清单，并在失败时自动回滚。成功后可使用迁移结果中的精确确认串执行一次可校验回退；如果迁移后文件已被并发修改，回退会拒绝覆盖。迁移成功后不保留 v1/v2 长期双写。

## v2.1 项目开发控制面

Seed 2.1 沿用 `contract_version: 2`，新增的事实仍由同一个 Catalog 和 Project Definition 编译器消费：

- `.maw/project.yaml` 描述项目交付模式、需求成熟度、来源状态、方法论和价值目标；
- `.maw/technology.yaml` 描述语言、框架、服务、容器/宿主机开发方式与验证命令；
- `.maw/environments.yaml` 以 local、staging、production 为规范环境，并保留旧别名迁移；
- `.maw/modules.yaml` 描述模块依赖、并行组、交付优先级、关键性和验收引用；
- `credentials.requirements` 只声明用途、范围、字段需求和授权要求，不保存真实凭证；
- `docs/handbooks/manifest.yaml` 索引需求、技术、任务审计、质量、发布运维、决策风险六卷手册。

本地工作台应双读 Seed 2.0 与 2.1：2.0 项目保持可诊断、只通过迁移事务升级；2.1 项目才开放新增字段的预览和写入。

## 安全边界

- Catalog 不能扩大 Host 的固定文件与操作权限。
- 项目 Schema 不能声明任意写路径。
- 浏览器响应不包含完整配置、本机绝对路径、备份正文或凭据值。
- 云端不能直接写本机项目；未来只能提交 proposal，由本机重新规划并人工确认。
- package、公开 Git 和 Host Program 分别通过独立发布闸门，不能用源码完成状态冒充已发布。
