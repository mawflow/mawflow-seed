# 指令：客户仓库分支角色与同步总览

## 元信息

- ID：TINST-015
- 类型：项目指令
- 状态：启用
- 维护位置：`docs/ai-instructions/instructions/customer-repository-branch-flow.md`
- 推荐调用：`#客户仓库同步`
- 精确调用：`#T015`
- 触发词：客户仓库同步、external_mapped、分支流向、客户分支角色、客户单分支、客户交付分支
- 适用范围：`external_mapped` 客户仓库同步的分支角色判断、动作选择和安全边界。

## 目标

当用户提到客户仓库同步、客户分支角色或单分支客户仓时，AI 应先判断分支模式和动作方向，再进入 `#客入`、`#客主`、`#客出` 或 `#客户合主` 的具体流程。角色定义如下：

- `INTERNAL_DEV`：我方内部开发分支，承接客入和测试单修复。
- `INTERNAL_RELEASE`：我方内部发布/交付分支，客出的唯一来源。
- `CUSTOMER_BASE`：客户最新基线分支，是客户公共模块和其它团队最新代码的事实源。
- `CUSTOMER_DELIVERY`：客户交付/测试目标分支，是我方客出目标。
- `CUSTOMER_INTEGRATION`：客户合主前的临时集成分支。
- `CUSTOMER_ONLY`：客户只有一个分支时，同时承担 `CUSTOMER_BASE` 和 `CUSTOMER_DELIVERY`。

## 输入要求

- 必需输入：目标动作或至少一个组件 `component`，例如 `server`、`client`。
- 可选输入：客户分支模式、具体分支名、profile、是否执行远端写入、预先 clone 的客户仓本地工作树路径。
- 缺失时处理：读取聚合后的 `.maw/repositories.yaml`；若缺少 `sync.branch_roles`，按旧项目兼容逻辑回退到 `external_mapped.components.<component>.external.default_branch`，但不得猜测真实客户分支。

## 执行步骤

1. 读取 `.maw/repositories.yaml`、`.maw/customer-repository-rules.yaml`、`docs/customer-repository-sync-guide.md` 和本指令。
2. 使用聚合配置定位 `sync.branch_roles` 和 `external_mapped.components.<component>.sync.branch_roles`；组件级配置优先，全局配置兜底，最后才回退到 `external.default_branch`。
   - 测试/正式等多套同构分支配置可拆到 `.maw/repositories.d/*.yaml`，用顶层 `enabled` 控制哪一套参与合并；同类片段同一时间只启用一份。
   - 大客户仓可在 `external_mapped.components.<component>.external.local_repository_path` 配置本机预克隆仓；真实路径应放 local overlay 或当次命令。
3. 判断 `customer_branch_mode`：
   - `separated`：客户基线和客户交付分支分离。
   - `single_with_temporary_delivery`：客户正式只有一个分支，但允许创建临时交付分支。
   - `single_direct`：客户只有一个分支且不允许临时交付分支。
   - 空值或未配置：保持旧项目 `external.default_branch` 行为。
4. 按动作选择具体指令：
   - 客入：`CUSTOMER_BASE -> INTERNAL_DEV`，执行 `TINST-016`。
   - 提主：`INTERNAL_DEV -> INTERNAL_RELEASE`，执行 `TINST-013`，不属于客户仓脚本。
   - 客主：`CUSTOMER_BASE -> CUSTOMER_DELIVERY`，执行 `TINST-017`。
   - 客出：`INTERNAL_RELEASE -> CUSTOMER_DELIVERY` 或 `CUSTOMER_ONLY`，执行 `TINST-018`。
   - 客户合主：`CUSTOMER_DELIVERY -> CUSTOMER_INTEGRATION -> CUSTOMER_BASE`，执行 `TINST-019`。
5. 明确测试单边界：客户测试反馈只形成测试单并回到 `INTERNAL_DEV` 修复，不把 `CUSTOMER_DELIVERY` 当作常规客入源。
6. 远端写操作必须先生成 plan，并且只有用户或命令显式 `--execute` 时才执行。

## 验证方式

- plan 文件写出 `internal_development_branch`、`internal_release_branch`、`customer_branch_mode`、`customer_base_branch`、`customer_delivery_branch` 和 `effective_external_branch`。
- 如果使用本地客户仓，plan 文件写出 `customer_repository_source`；本地仓必须干净，并且不得位于 `code/<component>` 内。
- 旧项目未配置 `branch_roles` 时，`plan/pull/push` 仍回退到 `external.default_branch`。
- 单分支模式下，客主和客户合主为 no-op 或仅检查；客出执行更高安全门禁。

## 禁区

- 不要把客户交付分支当作常规客入源。
- 不要规定每次客入前必须客主；正确规则是正式客出前先客主，或确认客户交付分支已包含最新客户基线。
- 不要把测试人员反馈设计成客户交付分支代码回流；测试反馈走测试单回到 `INTERNAL_DEV`。
- 不要把 `external_mapped` 客户仓库同步和 `component_mirrors`、`repository_mirrors` 混为一谈。
- 不得从镜像仓库 pull、merge、rebase。
- 不要在模板中写真实客户 URL、真实账号、真实密钥或项目私有路径。

## 冲突与覆盖规则

- 用户最新明确要求优先，但不得覆盖客户仓同步的 plan、白名单、脱敏和远端写入门禁。
- 与 `#提主/TINST-013` 冲突时，按方向区分：`#提主` 只处理 `INTERNAL_DEV -> INTERNAL_RELEASE`；客户仓动作由 `TINST-016` 至 `TINST-019` 处理。
- 与镜像仓库同步冲突时，按仓库类型区分：客户仓库走 `external_mapped`，组件镜像走 `component_mirrors`，整仓镜像走 `repository_mirrors`。

## 更新记录

- 2026-06-13：创建，内置客户仓库分支角色和同步动作总览。
- 2026-06-15：补充多环境分支片段开关和本地客户仓大仓优化说明。
