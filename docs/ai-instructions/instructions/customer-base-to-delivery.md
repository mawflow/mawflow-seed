# 指令：客主

## 元信息

- ID：TINST-017
- 类型：项目指令
- 状态：启用
- 维护位置：`docs/ai-instructions/instructions/customer-base-to-delivery.md`
- 推荐调用：`#客主`
- 精确调用：`#T017`
- 触发词：客主、刷新客户交付分支、客户主分支到专属分支、CUSTOMER_BASE到CUSTOMER_DELIVERY
- 适用范围：正式客出前刷新客户交付分支基线，或确认客户交付分支已包含最新客户基线。

## 目标

执行 `CUSTOMER_BASE -> CUSTOMER_DELIVERY`。它用于正式客出前刷新客户交付分支，不包含本项目客出内容。单分支模式下跳过或仅检查。

## 输入要求

- 必需输入：组件 `component`。
- 可选输入：`--execute` 表示实际创建/合并客户交付分支；`--local-repository-path PATH` 指向预先 clone 好的客户仓本地工作树，用作大仓 clone reference。
- 缺失时处理：不带 `--execute` 只生成计划；如果 `CUSTOMER_BASE == CUSTOMER_DELIVERY`，输出 no-op。

## 执行步骤

1. 先按 `TINST-015` 判断 `customer_branch_mode`。
2. separated 模式下，生成客主计划：

```bash
ops/scripts/sync-customer-branch.sh plan <component>
```

3. 执行客主时，客户仓工作副本只能位于系统临时目录；如配置了 `external.local_repository_path`，脚本会先更新本地客户仓，再将其作为临时 clone 的 reference：

```bash
ops/scripts/sync-customer-branch.sh merge-base-to-delivery <component> --execute
```

4. `single_with_temporary_delivery` 模式下，如果未配置 `CUSTOMER_DELIVERY`，脚本可从 `CUSTOMER_BASE` 创建临时交付分支。
5. 冲突时停止，不自动偏向客户基线或客户交付分支，输出人工处理建议。

## 验证方式

- plan 写出客户仓 URL、凭证引用、`CUSTOMER_BASE`、`CUSTOMER_DELIVERY`、branch mode、安全策略和风险说明。
- 执行记录写入 `artifacts/customer-branch-sync-runs/<component>/`。
- 单分支模式下不执行无意义 merge。
- 未出现 force push、prune 或 mirror push。
- 使用本地客户仓 reference 时，本地仓必须是干净 git working tree，真实路径只放 local overlay 或当次命令。

## 禁区

- 客主不包含本项目客出，不得把 `INTERNAL_RELEASE` 内容带入客户交付分支。
- 不要把客主当作客入前置条件；客入默认直接从 `CUSTOMER_BASE` 到 `INTERNAL_DEV`。
- 不要直接覆盖客户基线分支。
- 不要从镜像仓库 pull/merge/rebase。

## 冲突与覆盖规则

- 与 `#客出/TINST-018` 冲突时，客主只刷新客户交付分支基线；项目负责范围代码以后续客出提交为准。
- 与 `#提主/TINST-013` 冲突时，客主属于客户仓分支操作，不处理内部 `INTERNAL_DEV -> INTERNAL_RELEASE`。
- 用户要求跳过客主时，必须确认 `CUSTOMER_DELIVERY` 已包含最新 `CUSTOMER_BASE`，并在最终说明中记录风险。

## 更新记录

- 2026-06-13：创建，内置客户基线到客户交付分支的客主流程。
- 2026-06-15：支持本地客户仓 clone reference，降低大仓客主时的重复下载成本。
