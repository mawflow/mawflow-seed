# 指令：派生项目模板漂移升级

## 元信息

- ID：TINST-026
- 类型：项目指令
- 状态：启用
- 维护位置：`docs/ai-instructions/instructions/derived-template-drift-upgrade.md`
- 触发词：#模版升级、#模板升级、派生项目模板升级、模板漂移升级、当前模板落后多少提交、落后模板仓库多少提交、按模板仓库最新提交升级、模板差异提示词并执行
- 适用范围：在模板派生项目中，基于 `.maw/template-source.yaml` 记录的已应用模板基线，计算当前项目落后源模板仓库多少提交，生成当前会话执行提示词，并直接在当前 Codex 会话执行。

## 目标

当用户在派生项目中执行 `#模版升级/#模板升级` 时，AI 不走 `#项目升级` 的泛化策略入口，也不只生成给另一个会话复制的提示词。AI 必须先计算模板漂移，再根据漂移结果生成本轮当前会话执行提示词，并继续执行该提示词。

本指令从包含 `template_source.applied_version` 的模板版本开始生效；不追溯兼容此前没有记录模板基线的旧项目。

## 未指定 commit 时的默认路由

- 是否指定 commit 不决定在哪个仓库执行；当前 Codex 会话所在仓库的角色才决定路由。
- 当前仓库是派生项目时，`#模版升级/#模板升级` 在当前派生项目执行本指令；不会改去源模板仓库生成资产。
- 未指定 commit、branch 或 tag 时，先读取 `.maw/template-source.yaml` 的 `template_source.source_channel`，再读取 `template_source.version` 作为目标模板版本；该字段缺省时按 `main` 解析源模板目标 commit。
- `source_channel=内部来源通道` 时，内部派生项目优先从内部 `maw-project-template` 源、本机模板目录或 `.local/.maw/template-source.yaml` 解析升级资产；不得把内部私有 Git URL 写入公开提示词。
- `source_channel=public_seed` 时，外部公开派生项目优先从 `https://github.com/mawflow/mawflow-seed` 解析公开升级资产，不要求访问内部种子开发仓。
- `source_channel` 缺失、冲突或为 `unknown_legacy` 时，输出 `.maw/template-source.yaml`、Git remote 和仓库身份检测证据，要求人工确认来源通道后再自动升级。
- 如果 `template_source.applied_version` 为空，只把本次目标模板 commit 初始化为从当前版本开始的基线，不追溯猜测历史差异。
- 当前仓库其实是源模板仓库时，同一触发词走 `TINST-024`；如果无法判断仓库角色，先向用户确认。

## 路由判定

1. 如果当前仓库是源模板仓库本身，且存在 `.maw-template/template.yaml` 并标记 `repository_role: maw_project_seed_repository`，并且仓库身份检测确认当前 Git `origin`、`.maw/template-source.yaml` 的 `template_source.git_url` 和 `template_source.source_channel` 与源模板仓证据一致，`#模版升级/#模板升级` 仍走 `TINST-024 模板升级策略`，用于生成可传播升级资产。
2. 如果当前仓库是派生项目，且存在 `.maw/template-source.yaml`，`#模版升级/#模板升级` 走本指令。
3. 如果当前仓库是从 `maw-project-template` 直接 fork 出来的派生项目，可能仍保留 `.maw/repository-identity.yaml` 和 `.maw-template/template.yaml` 里的 `seed_repository` 声明。此时不能只凭这些可复制声明走 `TINST-024`；若用户说明该仓库就是派生项目，或仓库身份检测发现 Git `origin` 不等于源模板 `template_source.git_url`，应先按 `TINST-031` 修正/记录仓库身份，再按本指令执行模板漂移升级。
4. 如果用户明确说 `#项目升级`，仍走 `TINST-023 项目升级策略`；本指令不得抢占。
5. 如果无法判断当前仓库角色，先读取 `.maw/template-source.yaml`、`.maw-template/template.yaml`、`docs/ai-instructions/README.md` 和 `PROJECT_COMMANDS.md`，再运行 `python3 ops/scripts/extract-project-metadata.py --section repository-identity --format markdown` 辅助判断；仍无法判断时向用户说明缺少模板来源或基线。

## 模板基线字段

派生项目必须维护：

```yaml
template_source:
  source_channel: 内部来源通道 | public_seed | unknown_legacy
  git_url: "<internal seed git url or public seed git url>"
  public_source:
    canonical_public_repository_url: "https://github.com/mawflow/mawflow-seed"
    default_git_url: "https://github.com/mawflow/mawflow-seed.git"
  version: "main"
  applied_version: "<当前项目已实际采用的源模板 commit SHA>"
```

- `source_channel` 表示本项目的 Seed 来源通道。`内部来源通道` 面向内部受控项目，`public_seed` 面向外部公开项目，`unknown_legacy` 表示旧项目或来源冲突，自动升级前必须人工确认。
- `version` 表示本次对齐的源模板目标，可以是 branch、tag 或 commit，默认 `main`；用户未指定 commit 时使用该字段解析目标模板 commit。
- `applied_version` 表示当前项目上一次成功采用并提交的源模板 commit。
- 完成一次模板漂移升级后，必须把 `applied_version` 更新为本次目标模板 commit。
- 如果 `applied_version` 为空，本指令只初始化当前版本基线，不追溯历史提交差异；这是从本版本开始生效的前提。

## 执行步骤

1. 读取 `docs/ai-instructions/README.md`、`docs/ai-instructions/experience-index.md`、`.maw/template-source.yaml`、必要时读取 `.local/.maw/template-source.yaml`、本指令和 `docs/ai-instructions/instructions/create-task-prompt-project.md`。
2. 检查工作区：

```bash
git status --short
```

   如果存在未提交改动，先判断是否与本次模板升级相关；无法安全区分时停止并说明风险，不要把用户其它改动混进模板升级。

3. 运行模板漂移计划：

```bash
mawflow project drift
```

   `mawflow project drift` 是公开 Seed 和 Project Init 项目的统一入口，由 Host Base 提供，不依赖目标仓库携带内部脚本。只有当前仓库是完整 Seed 源码开发 checkout、且尚未安装新版 Host Base 时，才使用源码兼容入口：

```bash
python3 ops/scripts/plan-template-drift.py
```

4. 按计划结果处理：
   - `status: up_to_date`：说明当前模板基线已到目标模板 commit，无需执行升级。
   - `status: baseline_missing`：将本次目标模板 commit 作为从本版本开始的基线写入 `.maw/template-source.yaml` 的 `template_source.applied_version`；验证、提交、推送并按 mirror 有效计划同步。不要尝试补算旧历史。
   - `status: behind`：读取 `behind_count`、`commit_range` 和 `Current-session execution prompt`，在当前会话继续执行该提示词。
   - `status: ahead` 或 `diverged`：停止自动升级，说明当前项目记录的模板基线与目标模板不是简单落后关系，需要人工确认。
   - `status: baseline_invalid`：停止并要求修正 `template_source.applied_version` 为 commit SHA。

5. 直接执行 `current_session_prompt` 给出的语义增量升级：先创建安全分支，审计 commit 范围，只采用适合目标项目的差异，并保护目标项目事实。目标项目已经有模板升级任务包时可以按 `TINST-007` 继续使用；没有任务包时不得从私有 Seed 源复制，也不得因此阻塞公开项目升级。

6. 升级完成后，必须把 `.maw/template-source.yaml` 中的 `template_source.applied_version` 更新为计划中的 `target_commit`。
7. 运行目标项目可用的最小验证；至少包含：

```bash
git diff --check
mawflow project drift
```

   如果项目有对应检查脚本，按目标项目规则补充运行。

8. 本次产生实际改动后，按目标项目规则提交并推送当前分支；推送后运行仓库级 mirror 计划命令，按有效计划同步镜像。

## 当前会话提示词要求

生成或使用的当前会话提示词必须包含：

- 源模板 git 地址。
- 源模板目标 commit。
- 当前模板基线 commit。
- 模板落后提交数。
- 待同步提交范围。
- 待同步提交列表。
- 明确说明“当前会话继续执行；不要只生成给另一个会话的提示词”。
- 明确升级完成后更新 `template_source.applied_version`。

## 验证方式

- `mawflow project drift` 能输出 `target_commit`、`applied_version`、`behind_count` 和状态；完整源码开发 checkout 的兼容脚本应保持同一状态语义。
- 当 `behind_count > 0` 时，输出包含当前会话执行提示词。
- 当升级完成后再次运行计划，应显示 `status: up_to_date` 或 `behind_count: 0`。
- `.maw/template-source.yaml` 已记录新的 `template_source.applied_version`。
- 未覆盖目标项目 README、`code/`、app_key、发布配置、仓库映射、secrets、`.local/` 或项目私有规则。

## 禁区

- 不把本指令当作 `#项目升级` 的别名。
- 不在派生项目里生成只给另一个会话复制的提示词后停止；必须在当前会话执行，除非用户明确要求只生成提示词。
- 不把直接 fork 后继承的 `seed_repository` 声明当作不可推翻的事实；当前项目事实、用户明确说明和 Git 来源检测优先。
- 不在 `applied_version` 为空时猜测历史模板基线；从本版本开始初始化即可。
- 不复制源模板仓库的 `.git`、remote、镜像目标、真实 secrets 或 `.local/` 私有配置。
- 不整文件覆盖目标项目 README、业务代码、app_key、发布配置或项目私有规则。

## 冲突与覆盖规则

- 用户最新明确要求优先。
- 目标项目事实优先于模板默认值。
- 与 `TINST-023` 冲突时：用户说 `#项目升级` 才走 TINST-023；用户说 `#模版升级/#模板升级` 且当前是派生项目时走本指令。
- 与 `TINST-024` 冲突时：源模板仓库自身生成升级资产走 TINST-024；派生项目执行模板漂移升级走本指令。
- 与 `TINST-007` 冲突时：本指令负责漂移检测和当前会话提示词生成；TINST-007 负责任务包执行协议。

## 更新记录

- 2026-06-14：创建派生项目模板漂移升级指令，基于 `template_source.applied_version` 计算落后提交数，并在当前会话执行升级提示词。
- 2026-07-13：公开项目统一优先使用 `mawflow project drift`；源码脚本降级为完整 Seed checkout 的兼容入口，任务包改为可选而非公开升级前置。
