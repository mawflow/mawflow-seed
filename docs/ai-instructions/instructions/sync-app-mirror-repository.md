# 同步 app_key 镜像仓库

## 元信息

- ID：TINST-006
- 类型：项目指令
- 状态：启用
- 维护位置：`docs/ai-instructions/instructions/sync-app-mirror-repository.md`
- 触发词：同步镜像仓库、同步 app_key 镜像仓库、同步[app_key]镜像仓库、同步 server 镜像仓库、同步 client 镜像仓库、推送镜像仓库、mirror repository sync
- 适用范围：按 `app_key` 将当前项目仓库中的组件快照单向同步到目标镜像仓库

## 目标

用户触发“同步[app_key]镜像仓库”时，AI 应按 `.maw/repositories.yaml` 的 `component_mirrors.components.<app_key>` 配置，把当前项目仓库中已提交的 `source_path` 快照同步到目标镜像仓库。镜像仓库只允许作为目标仓库，不允许作为当前项目的代码来源。

## 输入要求

- 必需输入：`app_key`，例如 `server`、`client` 或项目新增的独立应用。
- 可选输入：profile、目标分支、是否只查看计划、是否允许覆盖或清理目标仓库引用。
- 缺失时处理：如果用户未给出 app_key，先从用户上下文判断是否只有一个已启用镜像组件；无法唯一确定时，向用户确认，不要猜测。

## 执行步骤

1. 先确认用户说的是 app_key 组件镜像，而不是整仓 GitHub 镜像；如果用户明确要整仓镜像，应使用项目自己的整仓镜像指令，不走本指令。
2. 读取 `.maw/codex-context.md`、`.maw/components.yaml`、`.maw/app-runtime.yaml`、`.maw/repositories.yaml`、`.maw/policies.yaml` 和 `docs/component-mirror-repository-guide.md`。
3. 使用聚合配置读取 `repositories`，定位 `component_mirrors.components.<app_key>`；确认 `component_mirrors.enabled` 和该组件 `enabled` 均为 `true`。
4. 确认 `source_path` 是项目根相对路径，且匹配当前项目的 `code/<app_key>` 或显式配置的组件源码路径。
5. 确认同步方向为 `push_only_current_project_to_mirror` 且 `forbid_pull_from_mirror: true`；如不是，停止执行并要求人工修正配置。
6. 检查工作区、当前分支和远端；如果本次任务产生了代码、配置、文档或脚本改动，先按项目规则提交并推送当前项目仓库。
7. 查看计划：

```bash
ops/scripts/sync-to-mirror-repo.sh plan <app_key>
```

8. 推送前确认当前工作区干净、当前项目仓库已提交并按项目规则推送、必要测试或人工验证已完成、脱敏检查已通过。
9. 执行单向同步：

```bash
ops/scripts/sync-to-mirror-repo.sh push <app_key> --execute
```

10. 检查 `artifacts/mirror-sync-runs/<app_key>/` 中的同步记录，并在最终说明中写明源提交、目标仓库、目标分支、验证结果，以及未执行的高风险动作。

## 验证方式

- `ops/scripts/sync-to-mirror-repo.sh plan <app_key>` 能输出正确的 `Source path`、`Mirror remote`、`Mirror branch` 和单向方向。
- `git status --short` 在执行前后可解释；推送前必须没有未提交变更。
- 同步记录写入 `artifacts/mirror-sync-runs/<app_key>/`。
- 未经用户明确授权时，不应出现 `git push --mirror`、`--force`、`--force-with-lease` 或 `--prune`。
- 如可访问目标仓库，可用 `git ls-remote` 或平台页面确认目标分支已更新。

## 禁区

- 不得从镜像仓库 pull、merge、rebase 或把镜像仓库变更导入当前项目。
- 不得把镜像仓库作为 `code/<app_key>` 的 clone、submodule 或 worktree。
- 不得使用未在 `.maw/repositories.yaml` 配置的目标仓库 URL。
- 未经用户明确要求，不得使用 `git push --mirror`、`--force`、`--force-with-lease` 或 `--prune`。
- 不得在脱敏检查前推送 `.maw/*.local.yaml`、`.ssh/**`、日志、缓存、构建产物、内部提示词或不应交付的密钥。
- 输入、输出、同步记录和说明文档中，涉及当前项目目录的路径必须使用项目根相对路径。

## 冲突与覆盖规则

- 用户最新明确要求优先于本指令，但不得覆盖“镜像仓库只允许当前项目到目标仓库单向同步”的安全边界。
- 如本指令与客户仓库同步流程冲突，以任务语义区分：客户仓库同步走 `external_mapped`；镜像仓库同步走 `component_mirrors`。
- 如目标镜像仓库存在独立修改，不得拉回当前项目；只允许用当前项目快照覆盖目标仓库内容，或停止并要求人工确认目标仓库用途。

## 更新记录

- 2026-06-12：创建，登记组件镜像仓库单向同步流程。
