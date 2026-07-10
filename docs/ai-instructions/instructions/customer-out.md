# 指令：客出

## 元信息

- ID：TINST-018
- 类型：项目指令
- 状态：启用
- 维护位置：`docs/ai-instructions/instructions/customer-out.md`
- 推荐调用：`#客出`
- 精确调用：`#T018`
- 触发词：客出、同步到客户仓、推客户分支、INTERNAL_RELEASE到CUSTOMER_DELIVERY、客户交付
- 适用范围：把我方内部发布/交付分支中允许交付的组件范围推送到客户仓库交付分支或客户唯一分支。

## 目标

执行 `INTERNAL_RELEASE -> CUSTOMER_DELIVERY`，单分支客户仓执行 `INTERNAL_RELEASE -> CUSTOMER_ONLY`。必须保留源提交证据，遵守白名单、脱敏、plan、未管理路径保护和单分支安全门禁。

## 输入要求

- 必需输入：组件 `component`。
- 可选输入：`--execute` 表示执行远端客户仓 push。
- 缺失时处理：不带 `--execute` 只生成计划；push 不允许 `--external-branch`，目标分支只能从 `customer_delivery_branch` 或旧 `external.default_branch` 计算。

## 执行步骤

1. 先按 `TINST-015` 判断分支角色，确认本次来源是 `INTERNAL_RELEASE`。
2. 正式客出前先执行 `#客主/TINST-017`，或确认 `CUSTOMER_DELIVERY` 已包含最新 `CUSTOMER_BASE`。
3. 查看计划：

```bash
ops/scripts/sync-to-external-repo.sh plan <component>
```

4. 确认 `.maw/customer-repository-rules.yaml` 已配置允许客出的路径；默认 `explicit_allowlist` 无白名单时拒绝 push。
5. 如果配置 `require_push_on_source_branch: true`，执行前必须确认当前分支是 `INTERNAL_RELEASE`。
6. 执行客出：

```bash
ops/scripts/sync-to-external-repo.sh push <component> --execute
```

7. single_direct 模式下，必须显式允许直接推客户唯一分支，并按配置确认备份 ref、白名单、不整仓替换、不删除未管理路径。

## 验证方式

- plan 文件写出 `INTERNAL_RELEASE`、`CUSTOMER_DELIVERY` 或 `CUSTOMER_ONLY`、`effective_external_branch` 和 `action_direction`。
- 客户仓提交信息保留来源项目分支、来源项目提交、组件目录、客出范围、上次成功客出 `internal_head` 和影响白名单路径的项目提交列表。
- 执行记录写入 `artifacts/sync-runs/<component>/`。
- 未列入白名单的客户仓路径保持不变。

## 禁区

- 不要从 `INTERNAL_DEV` 直接客出；先按 `#提主/TINST-013` 完成内部提主。
- push 不允许 `--external-branch`，避免误推客户基线。
- 不得在默认白名单模式下整仓替换客户仓。
- single_direct 模式不得绕过人工确认、plan、白名单、备份 ref 和未管理路径保护。
- 不得从 `component_mirrors` 或 `repository_mirrors` 读取客户代码。

## 冲突与覆盖规则

- 与 `#提主/TINST-013` 冲突时，提主只处理 `INTERNAL_DEV -> INTERNAL_RELEASE`；客出只处理 `INTERNAL_RELEASE -> CUSTOMER_DELIVERY/CUSTOMER_ONLY`。
- 与 `#客入/TINST-016` 冲突时，客入来源是客户基线，客出目标是客户交付分支，不得相互替代。
- 用户要求扩大客出范围时，先更新 `.maw/customer-repository-rules.yaml` 并生成 plan，不得临时绕过白名单。

## 更新记录

- 2026-06-13：创建，内置内部发布分支到客户交付分支的客出流程。
