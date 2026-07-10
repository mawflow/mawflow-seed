# 新手指南

本文件给第一次使用本模板仓库的人阅读。AI/Codex 的完整执行规则仍以 `AGENTS.md`、`RTK.md`、`.maw/codex-context.md` 和 `docs/ai-instructions/` 为准。

如果你是从 Mawflow v1.1 的公开 Seed 入口进入，先读 `MAWFLOW_SEED.md` 和 `docs/public-seed/README.md`。本文件继续保留模板仓库初始化细节，根目录 `README.md` 仍是派生业务项目的 README 占位。

## 1. 初始化一个新项目

1. 从本模板创建或同步项目骨架。
2. 确认项目 git remote、分支策略和是否需要客户仓库或镜像仓库。
3. 修改根目录 `README.md`，把占位内容替换为当前业务项目的真实介绍、启动方式和维护入口；模板仓库说明见 `TEMPLATE_OVERVIEW.md`，不要把模板说明长期留在业务项目 README 中。
4. 修改基础配置：
   - `.maw/project.yaml`
   - `.maw/components.yaml`
   - `.maw/app-runtime.yaml`
   - `.maw/repositories.yaml`
   - `.maw/environments.yaml`
   - `.maw/releases.yaml`
   - `.maw/policies.yaml`
5. 按项目实际补充密钥引用：
   - `.maw/secrets.yaml`
   - `.maw/secrets.dev.yaml`
   - `.maw/secrets.pro.yaml`
   - `.maw/*.local.yaml` 只放本机差异，不提交。
6. 如需本机覆盖配置，在 `.local/<same-path>` 下放同名文件；读取时本机覆盖优先于 git 中同名配置。

## 2. 组件默认口径

大多数项目建议先使用两个核心 app_key：

- `server`：后端/API/任务/数据库访问。
- `client`：前端、移动端、H5 或用户侧应用。

模板默认不内置 `admin` 组件。若项目确实有独立管理后台前端、独立构建或独立发布目标，应按项目实际新增一个前端 app_key；若后台只是后端框架内置页面、同一个前端中的管理路由，或项目暂时没有后台，应把它记录为业务模块或页面边界，不新增默认组件。

注意：`server`、`client` 是组件/app_key 口径，不是业务模块拆分口径。业务模块应继续按用户、订单、支付、设备、内容、报表等能力拆成 group 和 leaf。

## 3. 初始化模块档案

不要把整个服务端、整个前端或整个后台场景直接当成一个业务模块。

推荐流程：

1. 先用 `#模块` 让 AI 输出模块树。
2. 确认一级 group、二级能力组和 leaf。
3. 只有最小可交付功能模块才创建 `module.md` 和 `changelog.md`。
4. 同步更新 `.maw/modules.yaml`，让页面、接口、数据表、配置、测试和发布路径能定位到 leaf；活跃模块记录 `doc_status`、`last_verified_commit` 和必要的 `source_paths`。
5. 同步更新 `.maw/capabilities.yaml` 和 `.maw/project-signals.yaml`，登记公共能力、功能基类、API 快照、待办、澄清、缺口、口径变更和 AI 前置条件。
6. 定期执行 `#模块地图：检查`，把 `module_map_score`、待确认项和过期文档候选记录到 `docs/modules/_audits/`。
7. 为每个启用的 `code/<app_key>` 校准发布配置：`.maw/components.yaml` 的 `release_ref`、`.maw/releases.yaml` 的默认环境/环境选项/发布指令/版本状态策略，以及 `code/<app_key>/.maw.component.yaml` 的 `release`；发布成功后用 `artifacts/release-state/<env>/<app_key>.json` 记录已发布 commit。

## 4. 使用内置模板任务包

本模板内置两份给 Codex 执行的任务提示词工程，用于模板能力升级和模板化改造。它们不依赖本机 Codex skill，目标是让其它项目也能按仓库内文件继续执行。

执行任务包时必须给 Codex 提供源模板来源和 Seed 来源通道，或让 Codex 按“用户输入 > `.local/.maw/template-source.yaml` > `.maw/template-source.yaml` > 当前仓库”的顺序解析。下面的提示词使用 `<源模板本机路径>` 占位；真实本机路径和内部私有源只作为当次执行输入、受控内部配置或本机 `.local` 配置，不应写入目标项目的长期可提交文档。外部公开项目使用 `public_seed` 和公开 Seed 仓 `https://github.com/mawflow/mawflow-seed`。

极简口令优先记这三个：

```text
#项目升级：按源模板来源和取舍矩阵增量同步新版模板能力
```

```text
#模板化：把当前项目增量接入 MAW 模板规范
```

```text
#模板升级：覆盖模板提交 <commit1>、<commit2>，生成给其它项目使用的升级资产
```

`#项目升级` 是在目标项目里先生成取舍矩阵再增量同步模板能力；`#模板升级/#模版升级` 是在模板仓库里生成迁移说明、轻量提示词或完整任务包。含义不确定时让 AI 先确认。

### 4.1 模板派生项目升级

适用场景：目标项目已经基于本模板创建，已有 `.maw/`、`docs/ai-coding/`、`docs/ai-instructions/`、`prompts/` 或 `docs/modules/` 等模板痕迹，现在想同步新版模板能力。

使用步骤：

1. 在目标项目仓库中打开 Codex。
2. 如果目标项目还没有该任务包，先从本模板复制 `prompts/codex/task-packs/template-feature-upgrade-codex-tasks/` 到目标项目相同路径。
3. 对 Codex 说下面这段完整提示词：

```text
#项目升级：执行模板派生项目升级任务包
任务包：prompts/codex/task-packs/template-feature-upgrade-codex-tasks
源模板本机路径：<源模板本机路径>
源模板 git 地址：<受控内部项目使用本机或团队配置；公开项目使用 https://github.com/mawflow/mawflow-seed.git>
源模板版本：main
源模板读取优先级：用户输入 > .local/.maw/template-source.yaml > .maw/template-source.yaml > 当前仓库。
目标项目仓库：当前 Codex 会话所在仓库
升级范围：同步最新模板能力；必须先审计取舍再增量合并，不得整文件覆盖目标项目 README，不得误删目标项目已有 app_key、发布配置或项目私有规则。
```

4. Codex 会先审计目标项目现状和源模板差异，再形成取舍矩阵，最后只增量合并被确认采用或改造的模板能力。
5. 升级时不得整文件覆盖目标项目 `README.md`，不得因为模板默认不内置 `admin` 就删除目标项目已有独立后台、设备端、运营端或其它 app_key。

### 4.2 任意项目模板化改造

适用场景：目标项目还没有系统接入本模板规范，希望增量建立 `.maw/` 控制配置、AI 编码边界、模块档案、经验索引、任务提示词工程和 `.local` overlay。

使用步骤：

1. 在目标项目仓库中打开 Codex。
2. 从本模板复制 `prompts/codex/task-packs/adopt-maw-project-template-codex-tasks/` 到目标项目相同路径。
3. 对 Codex 说下面这段完整提示词：

```text
#模板化：执行任意项目模板化改造任务包
任务包：prompts/codex/task-packs/adopt-maw-project-template-codex-tasks
源模板本机路径：<源模板本机路径>
源模板 git 地址：<受控内部项目使用本机或团队配置；公开项目使用 https://github.com/mawflow/mawflow-seed.git>
源模板版本：main
源模板读取优先级：用户输入 > .local/.maw/template-source.yaml > .maw/template-source.yaml > 当前仓库。
目标项目仓库：当前 Codex 会话所在仓库
改造范围：增量接入 MAW 模板规范；先盘点项目事实和风险边界，不移动业务源码，不覆盖目标项目 README，不复制模板仓库远端、镜像目标、密钥或本机 .local 配置。
```

4. Codex 会先盘点项目事实，再设计采纳方案，然后增量加入 AI 协作控制面。
5. 改造时默认从 `server` / `client` 口径起步，但必须以目标项目真实端工程为准；没有独立后台时不创建后台占位，已有独立后台时按事实登记 app_key。
6. 目标项目已有 `README.md` 时只做最小段落合并；缺失时才创建业务项目 README 占位，模板说明放入 `TEMPLATE_OVERVIEW.md` 或等价文件。

## 5. 快速验证

初始化或同步模板能力后，建议至少运行：

```bash
rtk bash ops/scripts/check-template-module-docs.sh
rtk proxy python3 -m unittest tests/test_maw_config_loader.py
rtk proxy python3 - <<'PY'
from pathlib import Path
import yaml
for path in [*Path(".maw").glob("*.yaml"), Path("release/rules.yaml")]:
    yaml.safe_load(path.read_text(encoding="utf-8"))
    print(f"OK {path}")
PY
```

如果当前环境没有 `rtk`，可以用原生命令替代，但要限制输出范围。

## 6. 常用入口

- 人类常用指令目录：`PROJECT_COMMANDS.md`
- Mawflow Seed 公开入口：`MAWFLOW_SEED.md`
- Mawflow Seed 公开说明：`docs/public-seed/README.md`
- Mawflow Pack 示例：`examples/mawflow-packs/README.md`
- 外部 AI 到 Codex 任务交接：`CHATGPT_TO_CODEX.md`，常用口令 `#交接任务`
- 模板仓库说明：`TEMPLATE_OVERVIEW.md`
- 模板使用说明：`docs/template-usage-guide.md`
- 配置读取说明：`docs/configuration-guide.md`
- AI 编码边界：`docs/ai-coding/README.md`
- 项目指令库：`docs/ai-instructions/README.md`
- 任务提示词工程：`prompts/codex/task-packs/README.md`
- 创建任务提示词工程：`#任务包：<任务目标>`；执行已有任务包：`#跑任务包：prompts/codex/task-packs/<slug>-codex-tasks`

## 7. 不要提交的内容

- `.local/` 下真实资料和本机配置。
- `.maw/*.local.yaml`。
- `.ssh/**` 真实 key 文件。
- 裸 `.env`、日志、缓存、依赖目录、构建产物。
- 客户隐私、生产连接串、未脱敏日志、真实 token。

交付包、客户仓库同步或外部分享前，先执行脱敏检查。
