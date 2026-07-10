# 指令：脚本规范升级

## 元信息

- ID：TINST-032
- 类型：项目指令
- 状态：启用
- 维护位置：`docs/ai-instructions/instructions/script-contract-upgrade.md`
- 推荐调用：`#脚本规范`
- 精确调用：`#T032` 或 `#T032/脚本规范`
- 触发词：#脚本规范、脚本规范、脚本契约、AI Python Script Contract、规范化脚本、脚本标准化、已有脚本升级、升级现有脚本、脚本输出规范、脚本日志降噪、耗时任务脚本化、Python 脚本优先、py-first、noise-reduction script
- 适用范围：新增 AI 可复用脚本；把派生项目现有 `ops/scripts/` 脚本升级为结构化输入输出、日志落盘、状态可恢复、多环境兼容的规范脚本；为模板升级生成脚本规范迁移资产。

## 目标

让 AI 遇到重复、耗时、可验证且中间态噪音大的任务时，优先编写或扩展规范 Python 脚本。脚本负责消化长过程、过滤噪音、沉淀证据和处理本机环境差异；AI 只消费最终结构化结论，只有失败、不确定或未达预期时才接手分析并修复脚本。

## 输入要求

- 必需输入：要新增或升级的脚本范围，例如 `ops/scripts/`、具体脚本路径、任务类型或派生项目升级目标。
- 可选输入：目标系统环境、是否允许改造 shell 为 Python、是否只审计不修改、是否启用严格模式、需要保留的历史 CLI 兼容入口。
- 缺失时处理：默认只审计 `ops/scripts/`，先运行规范检查并给出升级清单；不直接重写所有旧脚本。

## 执行步骤

### 1. 前置读取

1. 读取 `docs/capabilities/ai-python-script-contract.md`。
2. 读取 `ops/scripts/README.md` 和目标脚本。
3. 读取 `.maw/capabilities.yaml`，确认是否已有 `ai-python-script-contract` 能力。
4. 派生项目模板升级时，先按目标项目规则读取 AGENTS/RTK、`.maw/codex-context.md`、`.maw/repository-identity.yaml` 和 `docs/README.md`。

### 2. 审计当前脚本

优先运行：

```bash
python3 ops/scripts/check-ai-python-script-contract.py --format json
```

如目标项目还没有该脚本，先从源模板增量合并以下文件：

- `docs/capabilities/ai-python-script-contract.md`
- `docs/ai-instructions/instructions/script-contract-upgrade.md`
- `ops/templates/ai-python-script.py`
- `ops/scripts/check-ai-python-script-contract.py`
- `ops/scripts/run-project-tests.py`

审计结果只作为升级路线，不代表旧项目必须一次性改完。默认 `--strict` 不开启；只有用户要求强制收敛或新增脚本门禁时才启用：

```bash
python3 ops/scripts/check-ai-python-script-contract.py --format json --strict
```

派生项目需要开箱测试入口时，先生成测试计划，不直接执行：

```bash
python3 ops/scripts/run-project-tests.py --format json
```

只有用户确认或当前任务要求运行测试时，才显式执行：

```bash
python3 ops/scripts/run-project-tests.py --suite test --execute --format json
```

### 3. 分类升级

按以下优先级改造：

1. 高频脚本：AI 或人经常调用的计划、检查、提取、同步脚本。
2. 高风险脚本：发布、客户仓库、镜像、密钥、脱敏、远端写操作。
3. 耗时脚本：构建、导出、下载、长流程校验。
4. 噪音脚本：输出大量中间态、日志、进度或外部命令原始输出。
5. 跨系统脚本：Linux、Windows、macOS 或多台设备协同开发时容易受环境差异影响的脚本。

保留兼容策略：

- 复杂逻辑优先迁移到 Python。
- 历史 shell 入口可以保留为薄包装，调用同名 Python 脚本。
- 旧 CLI 参数如已被任务包、文档或人工使用，必须保留或给出兼容别名。
- 不把派生项目真实本机路径、token、账号密码、生产连接串或未脱敏日志写进共享文件。

### 4. 新增或改造脚本

新增 Python 脚本时从模板开始：

```bash
cp ops/templates/ai-python-script.py ops/scripts/<script-name>.py
```

规范要求：

- stdout 只输出最终结果；长日志写 `artifacts/script-runs/`、`reports/` 或 `.local/`。
- 支持 `--format json|markdown|text`，给 AI 的默认输出优先 `json`。
- 支持 `--root`；项目路径输出使用项目根相对路径。
- 可能写文件、远端、数据库、发布状态或客户仓库的脚本必须支持 `--dry-run` 或 `plan` 子命令。
- 返回 `status`、`summary`、`next_action`、`changed_paths`、`evidence_refs`、`log_path`、`state_path`、`environment`、`warnings`、`ai_takeover_reason`。
- 多环境兼容使用 `pathlib.Path`、`platform.system()`、`shutil.which()` 和 `subprocess.run([...])`。
- 脚本失败或结果不符合预期时，AI 接手分析，并把修复沉淀回脚本或经验候选。
- 通用测试类脚本默认应先输出计划；`run-project-tests.py` 已内置 `.maw/components.yaml` / `code/*` 发现、package.json scripts、pytest 和 Makefile test 检测，并把执行日志写入 `artifacts/script-runs/project-tests/`。

### 5. 能力和文档登记

如果目标项目新增或显著改造了可复用脚本，判断是否更新：

- `.maw/capabilities.yaml`
- `docs/capabilities/<capability-key>.md`
- `ops/scripts/README.md`
- `docs/ai-instructions/experience-index.md`
- `docs/ai-instructions/execution-lesson-candidates.md`
- 相关模板迁移说明和升级提示词

模块档案只引用 `capability_key`，不复制完整脚本规范。

## 验证方式

最低验证：

```bash
git diff --check
python3 -m py_compile ops/scripts/check-ai-python-script-contract.py
python3 -m py_compile ops/templates/ai-python-script.py
python3 -m py_compile ops/scripts/run-project-tests.py
python3 ops/scripts/check-ai-python-script-contract.py --format json
python3 ops/scripts/run-project-tests.py --format json
```

如果修改了模板协议或公共能力，还应运行：

```bash
bash ops/scripts/check-template-module-docs.sh
bash ops/scripts/check-technical-map.sh
bash ops/scripts/check-ai-framework-consistency.sh
bash ops/scripts/check-local-boundary.sh
```

准备正式分发种子仓或大范围派生项目升级前，再运行：

```bash
bash ops/scripts/check-seed-distribution-readiness.sh
```

## 禁区

- 不为了一次性任务强行新增脚本。
- 不把业务取舍、架构判断、复杂冲突语义合并硬编码进脚本。
- 不让脚本默认打印长日志给 AI；stdout 只保留最终结构化结论。
- 不让脚本静默执行远端写操作；必须有 plan/dry-run 和显式执行参数。
- 不把 `.local/` 真实内容、密钥、token、账号密码、生产连接串、本机绝对路径或未脱敏日志写入可提交文档、提示词或报告。
- 不要求历史派生项目旧脚本一次性全量重写；先审计、再分批升级。

## 冲突与覆盖规则

- 用户最新要求优先；如果用户只要求评估或只审计，不修改脚本。
- 目标项目已有脚本 CLI 被发布、同步或任务包引用时，兼容性优先于重命名。
- 当前代码和脚本行为优先于模板示例；模板只提供契约和迁移路线。
- 本机环境差异写 `.local/`，共享项目规则写 `docs/`、`.maw/` 或 `ops/`。

## 更新记录

- 2026-06-19：创建，新增 AI Python 脚本规范升级指令和派生项目脚本改造路线。
