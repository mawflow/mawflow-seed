# 指令：发布公开镜像

## 元信息

- ID：TINST-039
- 类型：项目指令
- 状态：启用
- 维护位置：`docs/ai-instructions/instructions/publish-repository-mirror.md`
- 推荐调用：`#发布公开镜像`
- 精确调用：`#T039`
- 触发词：#发布公开镜像、#发布开源镜像、#发布镜像、公开发布镜像、发布 public mirror、私有仓发布到公开仓、开发完成一个版本后发布到公开仓、种子仓发布公开仓
- 适用范围：私有开发仓库在版本定版后，人工显式发布到公开仓库。该指令不处理普通仓库级自动镜像同步、组件镜像同步、客户仓库同步或应用部署。

## 目标

当用户要求把私有开发仓库的某个定版版本发布到公开仓库时，AI 应按 `repository_publish_mirrors` 配置先生成发布计划，确认版本、tag、公开目标、发布模式和检查闸门，再在用户已明确授权或当前请求已明确要求落地执行时运行 `publish --execute`。

该指令用于“公开发布”，不是 `repository_mirrors` 的 push 后自动同步。不要用 `MAW_FORCE_REPOSITORY_MIRROR_SYNC=1` 替代公开发布审批。

## 输入要求

- 必需输入：目标版本，推荐形如 `v0.2.18`。若用户未写版本，可读取 `TEMPLATE_VERSION` 作为候选，但执行前必须在计划中写明。
- 可选输入：发布 target、发布模式、是否只 plan、是否使用脱敏导出。
- 缺失时处理：
  - 未指定 target 时读取 `repository_publish_mirrors.default_target`，缺失时使用 `public_seed`。
  - 未指定版本时读取 `TEMPLATE_VERSION`。
- 未指定发布模式时读取 target 的 `publish_mode`，再回退 `repository_publish_mirrors.default_publish_mode`；模板默认推荐 `export_sanitized_tree`。

## 执行步骤

1. 读取 `.maw/repositories.yaml`、`.local/.maw/repositories.yaml` 示例、`docs/repository-publish-mirror-guide.md`、`docs/repository-mirror-sync-guide.md` 和本指令，确认本次是发布镜像，不是普通同步镜像。

2. 检查工作区、当前分支、版本和 tag。

```bash
git status --short
git branch --show-current
cat TEMPLATE_VERSION
git tag --points-at HEAD
```

3. 运行发布计划。

```bash
ops/scripts/publish-repository-mirror.sh plan public_seed --version v0.2.18
```

计划中重点检查：

- `Configured`
- `Target enabled`
- `Publish target`
- `Target branch`
- `Publish mode`
- `Version`
- `Local tag exists`
- `Tag points at HEAD`
- `Required gates`

4. 根据发布模式判断风险。

- `export_sanitized_tree`：默认推荐模式；私有仓历史可能包含内部内容时使用，公开仓只收到脱敏快照，不收到私有 Git 历史。
- `same_git_history`：只有私有仓 Git 历史已经适合公开时才能使用。

5. 公开发布前必须通过配置启用的检查。默认包括：

```bash
bash ops/scripts/check-seed-distribution-readiness.sh
bash ops/scripts/check-seed-open-source-readiness.sh --strict
bash ops/scripts/check-local-boundary.sh
bash ops/scripts/check-code-deliverable.sh
```

实际执行时由 `publish-repository-mirror.sh publish --execute` 统一串联检查，不要绕过。

6. 执行发布。

```bash
ops/scripts/publish-repository-mirror.sh publish public_seed --version v0.2.18 --execute
```

7. 验证公开仓分支和 tag，并检查记录。

```bash
git ls-remote <public-remote> refs/heads/main refs/tags/v0.2.18
find artifacts/repository-publish-runs/public_seed -maxdepth 1 -type f -name '*-v0.2.18-publish.yaml'
```

8. 最终说明写明：版本、源 commit、发布 target、发布模式、执行的检查、公开分支/tag、记录文件、是否使用同历史发布或脱敏导出。

## 验证方式

- `publish-repository-mirror.sh plan` 显示目标已配置且版本/tag/检查闸门清楚。
- `publish --execute` 成功完成。
- 公开远端目标分支和版本 tag 可通过 `git ls-remote` 查到。
- `artifacts/repository-publish-runs/<target>/` 写入发布记录。
- `git status --short` 没有遗留本次未提交改动，除非发布记录需要单独提交。

## 禁区

- 不要把普通 `repository_mirrors` 同步结果说成公开发布完成。
- 不要用 `MAW_FORCE_REPOSITORY_MIRROR_SYNC=1` 触发公开仓发布。
- 不要在未确认私有 Git 历史适合公开时使用 `same_git_history`。
- 不要执行 `git push --mirror`、`--force`、`--force-with-lease` 或 `--prune`。
- 不要把公开仓作为当前私有开发仓的代码来源。
- 不要把真实公开仓 token、SSH key 路径或私有 URL 写入共享 `.maw/repositories.yaml`；真实值写 `.local/.maw/repositories.yaml` 或本机 git remote。

## 冲突与覆盖规则

- 用户最新明确要求优先。
- 如果“发布镜像”语义不清，先区分：应用发布走 `TINST-014`，仓库级普通同步走 `TINST-013`/`repository_mirrors`，组件镜像走 `TINST-006`，公开仓定版发布走本指令。
- 若公开远端已有同名 tag，默认停止并要求人工确认版本策略，不自动覆盖。

## 更新记录

- 2026-06-29：创建，用于私有开发仓到公开仓的手动发布镜像。
