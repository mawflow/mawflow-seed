# 指令：客户合主

## 元信息

- ID：TINST-019
- 类型：项目指令
- 状态：启用
- 维护位置：`docs/ai-instructions/instructions/customer-delivery-to-base.md`
- 推荐调用：`#客户合主`
- 精确调用：`#T019`
- 触发词：客户合主、客户交付分支合入客户主线、CUSTOMER_DELIVERY到CUSTOMER_BASE、客户集成分支
- 适用范围：客户交付分支准备合入客户基线前的计划、集成分支创建和人工确认。

## 目标

执行或计划 `CUSTOMER_DELIVERY -> CUSTOMER_INTEGRATION -> CUSTOMER_BASE`。默认由客户负责人确认；AI 可生成计划或创建 integration 分支，但不能无脑覆盖客户基线。

## 输入要求

- 必需输入：组件 `component`。
- 可选输入：`--execute` 表示创建客户集成分支；`--local-repository-path PATH` 指向预先 clone 好的客户仓本地工作树，用作大仓 clone reference。
- 缺失时处理：默认只生成 `integration-plan`；single_direct 模式跳过客户合主。

## 执行步骤

1. 先按 `TINST-015` 判断分支角色和客户分支模式。
2. 默认生成客户合主计划：

```bash
ops/scripts/sync-customer-branch.sh integration-plan <component>
```

3. 如客户负责人要求创建集成分支，执行；如配置了 `external.local_repository_path`，脚本会先更新本地客户仓，再将其作为临时 clone 的 reference：

```bash
ops/scripts/sync-customer-branch.sh create-integration <component> --execute
```

4. 脚本从 `CUSTOMER_BASE` 创建 `CUSTOMER_INTEGRATION`，再合入 `CUSTOMER_DELIVERY`，供客户负责人审核。
5. 白名单外文件以 `CUSTOMER_BASE` 为准；冲突时停止并输出人工处理建议。

## 验证方式

- plan 写出源分支、目标集成分支、客户仓 URL、组件、凭证引用、branch mode、安全策略和风险说明。
- 执行记录写入 `artifacts/customer-branch-sync-runs/<component>/`。
- 客户基线分支未被脚本直接覆盖。
- 未出现 force push、prune 或 mirror push。
- 使用本地客户仓 reference 时，本地仓必须是干净 git working tree，真实路径只放 local overlay 或当次命令。

## 禁区

- 不要直接把 `CUSTOMER_DELIVERY` 强推到 `CUSTOMER_BASE`。
- 不要删除客户基线中白名单外或未管理路径。
- 不要把客户合主当作内部 `#提主`；内部 `INTERNAL_DEV -> INTERNAL_RELEASE` 仍由 `TINST-013` 处理。
- 不要从镜像仓库 pull/merge/rebase。

## 冲突与覆盖规则

- 客户负责人或客户仓治理规则优先；AI 只生成计划和安全集成分支，不替代客户最终合主审批。
- 与 `#客主/TINST-017` 冲突时，客主是基线刷新到交付分支，客户合主是交付分支准备回到基线。
- 与 `component_mirrors`、`repository_mirrors` 冲突时，客户仓 external_mapped 不是镜像同步。

## 更新记录

- 2026-06-13：创建，内置客户交付分支到客户基线的合主计划和集成分支流程。
- 2026-06-15：支持本地客户仓 clone reference，降低大仓客户合主时的重复下载成本。
