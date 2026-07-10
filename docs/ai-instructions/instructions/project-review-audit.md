# 指令：项目评审与审计治理

## 元信息

- ID：TINST-037
- 类型：项目指令
- 状态：启用
- 维护位置：`docs/ai-instructions/instructions/project-review-audit.md`
- 推荐调用：`#项目评审`、`#项目审计`
- 精确调用：`#T037`、`#T037/项目评审` 或 `#T037/项目审计`
- 触发词：#项目评审、项目评审、需求评审、需求评审会议、业务流程评审、开发方向核对、docs 口径治理、#项目审计、项目审计、验收目标审计、实现程度审计、评审报告路径、项目审计:、项目审计：
- 适用范围：基于 `docs/` 当前事实做项目方向、需求理解、业务流程、验收目标和 docs 口径评审；在人工确认后，基于评审报告对验收目标、实现程度、证据和后续推进建议做项目级审计。

## 目标

让 AI 能像参与一次需求评审会议的主讲人一样，基于当前项目文档复述项目目标、业务流程、验收目标和开发方向，暴露 docs 口径冲突与待确认问题；评审经人工确认后，再用项目审计对照验收目标核对实现程度、证据强度、缺口和后续推进建议。

项目评审和项目审计都必须有可追溯报告。评审完成后，报告和最终说明必须给出可复制接续调用：

```text
#项目审计：<评审报告路径>
```

## 子模式

| 调用 | 用途 | 默认产物 |
| --- | --- | --- |
| `#项目评审` | 全量或按当前请求做项目方向、需求、业务流程和验收目标评审 | `docs/project-review-audits/rounds/<review_id>/review.md` |
| `#项目评审：<范围>` | 评审指定模块、文档、commit range、交付范围或业务流程 | 同上 |
| `#项目审计：<评审报告路径>` | 基于指定评审报告审计验收目标、实现程度和后续推进建议 | `docs/project-review-audits/rounds/<review_id>/audit-YYYYMMDD.md` |
| `项目审计:<评审报告路径>` | 兼容无 `#` 的接续调用写法 | 同上 |

## 输入要求

- 评审必需输入：当前项目仓库；没有明确范围时默认全量 docs 评审，但仍按目录索引最小读取。
- 评审推荐输入：业务范围、模块、需求文档路径、评审主题、commit range、交付目标、是否只出报告不回写 docs。
- 审计必需输入：评审报告路径，例如 `#项目审计：docs/project-review-audits/rounds/PRA-YYYYMMDD-slug/review.md`。
- 审计推荐输入：是否允许读取代码和运行测试、目标环境、commit range、验收重点。
- 缺失时处理：评审范围不明确时先从 `docs/README.md`、`.maw/project-review-audit.yaml`、文档索引和最近 approved 评审记录定位；审计缺少评审报告路径时必须要求用户补充，不能猜测。

## 执行步骤

### 1. 评审前读取

1. 读取启动上下文、`docs/README.md`、`.maw/project-review-audit.yaml` 和本指令。
2. 读取 `docs/project-review-audits/README.md`，确认报告路径、模板和边界。
3. 按任务范围读取相关目录 README：
   - `docs/requirements/README.md`
   - `docs/design/README.md`
   - `docs/modules/README.md`
   - `docs/planning/README.md`
   - `docs/acceptance/README.md`
4. 需要增量评审时，读取 `.maw/project-review-audit.yaml` 的 `latest_approved_review_id`、`latest_audit_id` 和相关报告；再用 commit range 或 docs diff 定位变化范围。
5. 不全量读取 `docs/**`；只读取本次评审命中的文档、章节和索引。

### 2. 生成项目评审报告

1. 分配 `review_id`，推荐格式 `PRA-YYYYMMDD-<slug>`。
2. 复制 `docs/project-review-audits/_templates/project-review.md` 到：

```text
docs/project-review-audits/rounds/<review_id>/review.md
```

3. AI 以主讲人视角填写：
   - 项目目标复述。
   - 当前开发方向判断。
   - 业务流程复述。
   - 需求、设计和模块口径核对。
   - 验收目标草案。
   - docs 口径治理清单。
   - 人工评审问题。
4. 所有 AI 推断必须标注 `proposal`、`inferred` 或 `pending_confirm`；不得写成已确认事实。
5. 报告必须保留“接续审计调用”章节，并填入真实评审报告路径：

```text
#项目审计：docs/project-review-audits/rounds/<review_id>/review.md
```

6. 最终说明也必须单独列出同一条接续调用，方便用户复制到后续对话。

### 3. 人工确认与 docs 回写

1. 评审报告默认状态为 `pending_review`，不能直接把 AI 评审结论回写为项目事实。
2. 用户确认后，创建或更新：

```text
docs/project-review-audits/rounds/<review_id>/doc-fix-plan.md
```

3. 只把人工确认的结论回写到相关事实源：
   - 需求基线和待确认问题：`docs/requirements/`
   - 架构、API、数据模型、页面流和功能规格：`docs/design/`
   - 模块事实和变更：`.maw/modules.yaml`、`docs/modules/`
   - 计划、风险和跨模块待办：`docs/planning/`
   - 验收清单、缺陷和测试报告：`docs/acceptance/`
   - 跨模块提示：`.maw/project-signals.yaml`
4. 跨模块暂不实现但被当前业务闭环依赖的缺口，走 `#待办任务`；复杂整改建议走 `#任务包`。

### 4. 执行项目审计

1. 解析用户输入中的评审报告路径；路径必须存在。
2. 读取评审报告、同轮 `doc-fix-plan.md`、相关验收清单和评审报告引用的事实源。
3. 如果用户只要求 docs 审计，证据等级写 `docs_only`。
4. 如果要判断真实实现程度，必须按项目边界读取代码、测试、运行态、发布记录或人工确认；没有证据时写 `unknown`，不能把 docs 口径当实现事实。
5. 分配 `audit_id`，推荐格式 `PAA-YYYYMMDD-<slug>`。
6. 复制 `docs/project-review-audits/_templates/project-audit.md` 到：

```text
docs/project-review-audits/rounds/<review_id>/audit-YYYYMMDD.md
```

7. 按验收目标逐项标记：
   - `met`
   - `partial`
   - `missing`
   - `blocked`
   - `unknown`
8. 输出 docs 与实现一致性、缺口整改队列、未覆盖范围和后续推进建议。

### 5. 增量评审与增量审计

1. 没有历史 approved 评审时，执行全量评审。
2. 有历史 approved 评审时，默认比较 `docs_applied_commit..HEAD` 范围内的 `docs/`、`.maw/` 和 `README.md` 变化。
3. 未变化的结论可以继承，但必须在报告中写明“沿用上轮确认结论”。
4. 需求、设计、模块、验收目标或项目提示信号变化时，只重评审受影响流程和验收目标。
5. 审计默认基于指定评审报告；如果报告已被 `superseded`，必须提醒用户改用最新 approved 评审，或由用户确认仍审计旧报告。

## 验证方式

最低验证：

```bash
git diff --check
python3 ops/scripts/check-doc-read-contract.py --format json
bash ops/scripts/check-template-module-docs.sh
bash ops/scripts/check-technical-map.sh
```

修改模板协议、指令索引或升级资产时还应运行：

```bash
bash ops/scripts/check-ai-framework-consistency.sh
bash ops/scripts/check-local-boundary.sh
```

## 禁区

- 不把 AI 主讲稿、推断或建议当成已确认项目事实。
- 不在没有人工确认时批量回写 `docs/requirements`、`docs/design`、`docs/modules`、`docs/planning` 或 `docs/acceptance`。
- 不为了评审而全量读取 `docs/**`、`code/**`、`reports/**` 或历史归档。
- 不把项目审计混同于模块地图审计；模块页面/API/后端细节审计仍优先走 `#模块地图`。
- 不把 docs-only 结论写成实现已完成；没有代码、测试、运行态、发布或人工确认时，状态必须是 `docs_only` 或 `unknown`。
- 不覆盖目标项目 README、`code/`、真实 app_key、发布配置、仓库映射、secrets、`.maw/*.local.yaml`、`.local/` 或人工确认文档。

## 冲突与覆盖规则

- 用户最新说明和人工评审结论优先于 AI 评审报告。
- 当前代码、运行态、测试和发布证据优先于旧 docs；docs 口径与实现冲突时，审计报告必须列为 drift。
- 与 `TINST-036 #模块地图` 冲突时，本指令负责项目方向、业务流程和验收目标；模块页面/API/后端事实细审交给模块地图。
- 与 `TINST-030 #技术地图` 冲突时，本指令负责评审/审计报告闭环；技术地图负责公共能力、项目信号和机器提取入口。
- 与 `TINST-033 #文档索引` 冲突时，本指令负责评审/审计内容；文档索引负责 front matter 和可读取元数据。

## 更新记录

- 2026-06-23：创建，新增项目评审、项目审计、报告模板、接续调用和增量评审/审计口径。

