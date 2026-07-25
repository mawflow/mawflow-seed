# Seed Contract v2

Seed Contract v2 是 MAWflow CLI、Host、本地工作台和项目仓库共同遵守的项目定义协议。它的目标不是把一套大模板复制到每个项目，而是让项目事实可编译、可视化、可安全变更、可迁移。

## 单一事实链

```text
maw-project-template
  └─ mawflow-seed-kit 2.1.0
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
- `.maw/components.yaml`
- `.maw/modules.yaml`
- `.maw/app-runtime.yaml`
- `.maw/environments.yaml`
- `.maw/project-doctor.yaml`
- `.maw/template-source.yaml`
- `.maw/upgrade-policy.yaml`
- `.maw/agent-entry.yaml`
- `AI_START_HERE.md`
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

新项目选择 `web-api`、`service` 或 `minimal` profile：

```bash
mawflow project init my-project --profile web-api
cd my-project
mawflow project doctor --root .
```

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
