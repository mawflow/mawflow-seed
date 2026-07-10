# 指令：dev 合并到 main 并同步仓库镜像

## 元信息

- ID：TINST-013
- 类型：项目指令
- 状态：启用
- 维护位置：`docs/ai-instructions/instructions/dev-to-main-merge.md`
- 推荐调用：`#提主`
- 精确调用：`#T013`
- 触发词：#提主、#合并主分支、#合并dev到main、合并dev到main、dev合并到main、dev 合并 main、将 dev 分支合并到 main、合并到 main、内部提主合并、同步 main 镜像、多镜像仓库
- 适用范围：项目内部源分支合并到主分支，默认 `origin/dev -> main`，并在项目配置启用仓库级镜像且自动同步开关为 true 时同步镜像。该指令不处理客户仓库同步、组件镜像仓库同步、公开发布镜像或发布部署。

## 目标

当用户要求把 `dev` 合并到 `main` 或进行“提主”时，AI 应在工作区干净、远端引用已刷新的前提下，将源分支合并到目标主分支，推送 `origin/main`，并在 `ops/scripts/sync-repository-mirror.sh plan` 的有效计划允许时同步主分支和 tags。

该指令用于内部 Git 分支收口，不等同于 `external_mapped` 客户仓库的客入、客出、组件同步，也不等同于 `component_mirrors` 的 app_key 组件镜像同步或 `repository_publish_mirrors` 的公开发布镜像。

## 输入要求

- 必需输入：无。默认源分支为 `origin/dev`，目标分支为 `main`。
- 可选输入：源分支、目标分支、是否只演练、是否同步镜像、镜像 remote 名称。
- 缺失时处理：
  - 未指定源分支时使用 `origin/dev`。
  - 未指定目标分支时使用 `main`。
  - 未明确禁止镜像同步时，在 `origin/main` 推送成功后先运行 `ops/scripts/sync-repository-mirror.sh plan`；计划显示 `Configured: true`、目标启用且自动同步开启时同步镜像。
  - 镜像目标以 `plan` 输出的 `Target key`、`Mirror target`、`Mirror branch` 和 `Config source` 为准；配置了 `repository_mirrors.default_targets` 时默认可能包含多个 target。用户指定 target 时只使用指定 target；用户要求所有目标时使用 `plan --all` / `push --all --execute`。无法通过计划判断时不要猜测，先说明并跳过镜像同步或请用户确认。

## 执行步骤

1. 读取根 `AGENTS.md`、`.maw/repositories.yaml`、`.maw/policies.yaml`、`PROJECT_COMMANDS.md`、`docs/repository-mirror-sync-guide.md` 和本指令，确认本次是项目内部源分支合并到主分支。
2. 检查工作区、当前分支和 remote。如果存在未提交改动，除非能确认是本轮改动且已按项目规则处理，否则先停止并说明风险。

```bash
git status --short
git branch --show-current
git remote -v
```

3. 刷新内部远端并确认源分支、目标分支存在。

```bash
git fetch origin --prune
git rev-list --left-right --count origin/main...origin/dev
git log --oneline --decorate --max-count=20 origin/main..origin/dev
git log --oneline --decorate --max-count=20 origin/dev..origin/main
```

如果用户指定了其它源分支或目标分支，把命令中的 `origin/dev` 和 `origin/main` 替换为对应远端引用。

4. 切换到目标分支，确保本地目标分支不落后于 `origin/<target>`。如果本地目标分支可快进，先快进；如果本地目标分支有未推送提交，先说明并确认这些提交是否应保留。

```bash
git switch main
git merge --ff-only origin/main
```

5. 合并源分支到目标分支。默认保留合并提交，方便追踪本次收口。

```bash
git merge --no-ff origin/dev -m "合并 dev 分支到 main"
```

6. 如出现冲突，逐项检查冲突双方内容，按用户最新要求、模块边界和当前项目规则解决；不得无脑选择一边。冲突解决后检查冲突标记并继续提交。

```bash
git diff --name-only --diff-filter=U
rg -n "^(<<<<<<<|=======|>>>>>>>)" <冲突文件>
git add <已解决文件>
git commit --no-edit
```

7. 验证合并结果并推送 `origin/main`。

```bash
git merge-base --is-ancestor origin/dev main
git status -sb
git push origin main
git ls-remote origin refs/heads/main refs/heads/dev
```

8. 在 `origin/main` 推送成功后运行仓库级 mirror 计划。以计划输出中每个 target 的 `Target key`、`Configured`、`Config source`、`Auto sync`、`Target enabled`、`Target auto sync`、`Mirror target` 和 `Mirror branch` 判断是否同步；不要只凭原始 `repository_mirrors.enabled=false` 判断未配置，因为 `.local/.maw/repositories.yaml` 本机 overlay 或模板仓库兼容字段可能启用 mirror。计划显示已配置、目标启用且自动同步开启时执行自动同步；如果计划显示未配置或自动同步关闭，最终说明写明已按有效计划跳过。默认按 `repository_mirrors.default_targets` 或旧 `default_target` 推送目标主分支和 tags，并按 target 写入 mirror 同步记录；如需临时同步全部目标，使用 `--all`。如果本次项目仓库提交只是为了提交上一轮 mirror 记录，使用 `--no-record` 避免记录提交循环。不要使用 `--mirror`、`--prune` 或强推。

```bash
ops/scripts/sync-repository-mirror.sh plan
ops/scripts/sync-repository-mirror.sh push --execute
# 临时查看或同步所有 targets：
ops/scripts/sync-repository-mirror.sh plan --all
ops/scripts/sync-repository-mirror.sh push --all --execute
# 仅提交上一轮 mirror 记录时：
ops/scripts/sync-repository-mirror.sh push --execute --no-record
```

9. 最终说明写明源分支、目标分支、合并提交、`origin/main` 指向、源分支远端指向、冲突文件和解决原则、镜像同步结果、工作区是否干净。

## 验证方式

- `git merge-base --is-ancestor <source-remote-ref> <target-branch>` 返回成功。
- `git push origin <target-branch>` 成功完成，`origin/<target>` 指向本次合并提交或已包含源分支目标提交。
- 如果 mirror 计划显示已配置且自动同步开启，目标主分支和 tags 已同步成功，或明确说明失败原因和未同步内容；如果计划显示未配置或自动同步关闭，明确说明按有效计划跳过，并报告 `Config source` 或未配置原因。
- `git status --short` 没有遗留本次未提交改动。

## 禁区

- 不要把本指令理解为客户仓库同步、客入、客出、组件快照推送或发布部署。
- 不要把本指令的 `repository_mirrors` 普通同步结果写成公开仓定版发布；发布公开镜像必须走 `TINST-039` / `publish-repository-mirror.sh`。
- 不要从 `dev` 直接向客户仓库客出；客户仓库同步必须按目标项目自己的客户仓库同步指令执行。
- 不要把仓库级镜像 `repository_mirrors` 和 `.maw/repositories.yaml` 中的 `component_mirrors` 混为一谈；组件镜像同步按 `TINST-006` 或目标项目等价指令执行。
- 不要在未检查工作区和远端差异时直接合并。
- 不要在未获得用户明确确认时使用 `git push --force`、`--force-with-lease`、`--mirror` 或 `--prune`。
- 不要为了解冲突而删除无关模块、缓存规则、发布规则或历史记录。
- 不要把镜像推送成功误说成内部 `origin` 推送成功；两个 remote 必须分别说明。

## 冲突与覆盖规则

- 用户最新明确要求优先；如果用户指定源分支、目标分支或要求不推送镜像，以用户指定为准。
- 与客户仓库同步指令冲突时，先区分目标：内部分支合并用本指令，客户仓库同步或“客出/客入”用客户仓库同步指令。
- 与 `TINST-006 同步 app_key 镜像仓库` 冲突时，先区分镜像类型：仓库级主分支镜像用本指令，`code/<app_key>` 组件镜像同步用 `TINST-006`。
- 若 `origin/main` 或仓库级镜像 remote 拒绝非强制推送，必须先说明影响并等待用户明确确认，不得擅自覆盖远端。

## 更新记录

- 2026-06-12：创建，从业务项目内部分支合并经验中抽象为模板内置指令。
