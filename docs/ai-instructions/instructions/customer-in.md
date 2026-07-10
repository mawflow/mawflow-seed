# 指令：客入

## 元信息

- ID：TINST-016
- 类型：项目指令
- 状态：启用
- 维护位置：`docs/ai-instructions/instructions/customer-in.md`
- 推荐调用：`#客入`
- 精确调用：`#T016`
- 触发词：客入、从客户主线拉代码、从客户基线同步、客户公共模块回流、CUSTOMER_BASE到INTERNAL_DEV
- 适用范围：`external_mapped` 模式下把客户基线分支同步到我方内部开发分支。

## 目标

执行 `CUSTOMER_BASE -> INTERNAL_DEV`。默认从客户基线客入，不从 `CUSTOMER_DELIVERY` 常规客入；客入前不要求先客主。

## 输入要求

- 必需输入：组件 `component`。
- 可选输入：`--external-branch BRANCH` 只用于本次 plan/pull 覆盖客入来源；`--local-repository-path PATH` 指向预先 clone 好的客户仓本地工作树；`--execute` 表示执行读取和本仓合并。
- 缺失时处理：从 `branch_roles.customer_base_branch` 读取来源分支；未配置时回退到组件 `external.default_branch`。本地客户仓路径优先读 `external_mapped.components.<component>.external.local_repository_path`，未配置时走原客户仓 URL/凭证通道。

## 执行步骤

1. 先按 `TINST-015` 判断分支角色和客户分支模式。
2. 检查 `.maw/customer-repository-rules.yaml` 的 plan 目录、组件启用状态、同步范围和禁提交范围。
3. 查看计划：

```bash
ops/scripts/sync-to-external-repo.sh plan <component>
```

4. 如需指定一次性客入来源，只允许在 plan/pull 使用：

```bash
ops/scripts/sync-to-external-repo.sh pull <component> --external-branch <CUSTOMER_BASE> --execute
```

5. 客户仓很大时，可使用本地客户仓路径；脚本会先更新本地仓到最新，再从本地目录 fetch：

```bash
ops/scripts/sync-to-external-repo.sh pull <component> --local-repository-path <本机客户仓目录> --execute
```

6. 若配置 `require_pull_on_target_branch: true`，执行前必须确认当前分支是 `INTERNAL_DEV`。
7. 冲突必须停在本仓库解决，运行组件测试或最小验证后提交本仓库。

## 验证方式

- plan 文件的 `action_direction` 为 `CUSTOMER_BASE -> INTERNAL_DEV`，`effective_external_branch` 是客户基线或显式覆盖分支。
- 本仓库合并记录或执行记录保留客户仓库 URL、客户分支、客户提交、上次成功客入 `external_head` 和客户提交列表。
- 使用本地客户仓时，plan/记录写出 `customer_repository_source` 和本地仓 reference；本地仓必须是干净 git working tree，且不得位于 `code/<component>` 内。
- 冲突解决后 `git status` 可解释，且本仓库完成提交后才进入后续客出。

## 禁区

- 不要从 `CUSTOMER_DELIVERY` 常规客入。
- 不要把客入前置绑定为必须客主。
- 不要把客户测试反馈当作客户分支代码回流；测试单回到 `INTERNAL_DEV` 修复。
- 不要把客户仓库 clone、submodule 或 worktree 放进 `code/<component>`。
- 不要把真实本机客户仓路径写入共享配置；应放在 `.maw/repositories.local.yaml`、`.local/.maw/repositories.yaml` 或当次命令参数。

## 冲突与覆盖规则

- 用户指定本次客入分支时，只影响 plan/pull；不得影响 push 目标。
- 与 `#提主/TINST-013` 冲突时，客入只处理客户仓到内部开发分支；内部开发到发布分支仍由 `#提主` 处理。
- 与镜像仓库同步冲突时，客户仓库走 `external_mapped`，不得从 `component_mirrors` 或 `repository_mirrors` 拉取代码。

## 更新记录

- 2026-06-13：创建，内置客户基线到内部开发分支的客入流程。
- 2026-06-15：支持预先 clone 的客户仓本地工作树；客入先更新本地仓再从本地目录读取，适配大仓场景。
