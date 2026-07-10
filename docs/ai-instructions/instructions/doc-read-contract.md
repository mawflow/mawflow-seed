# 指令：文档写读契约与索引

## 元信息

- ID：TINST-033
- 类型：项目指令
- 状态：启用
- 维护位置：`docs/ai-instructions/instructions/doc-read-contract.md`
- 推荐调用：`#文档索引`
- 精确调用：`#T033` 或 `#T033/文档索引`
- 触发词：#文档索引、文档写读契约、文档读取契约、docs 索引、生成文档索引、健康面板文档来源、产品设计索引、模块设计索引、doc-read-contract、document index
- 适用范围：新增或重构产品计划、产品需求、产品设计、模块设计、任务拆解、项目审计和 AI 协作过程文档；为项目健康、审计大屏或 AI 任务准备结构化文档索引。

## 目标

让文档在写入时就具备可读取、可索引、可追溯的元数据。AI 不需要全量读取 `docs/**`，而是先用文档索引定位相关文档，再按任务读取最小必要片段。

## 输入要求

- 必需输入：要写入、检查或索引的文档范围，例如 `docs/product`、`docs/design`、`docs/modules` 或具体文档路径。
- 可选输入：项目健康维度、关联产品/需求/模块/任务、是否需要写索引快照、是否开启严格模式。
- 缺失时处理：默认只运行兼容检查和索引生成，不批量改历史文档；只有正在新增或修改的关键文档才补 front matter。

## 执行步骤

### 1. 前置读取

1. 读取 `.maw/doc-taxonomy.yaml`。
2. 读取 `docs/doc-read-contract/README.md`。
3. 需要解释能力边界时读取 `docs/capabilities/doc-read-contract.md`。
4. 派生项目模板升级时，按目标项目 AGENTS/RTK 和 `.maw/template-source.yaml` 增量合并，不覆盖既有项目事实。

### 2. 判断文档是否需要契约

以下文档新写或重构时应补 front matter：

- `docs/product/**`：产品计划、产品设计、产品侧决策。
- `docs/requirements/**`：产品需求、需求基线、需求变更。
- `docs/design/**`：架构、接口、页面、数据模型和设计说明。
- `docs/modules/**`：模块档案、模块设计和模块 AI 上下文。
- `docs/planning/**`：任务拆解、迭代节奏、风险和待办。
- 项目健康、项目审计或 AI 任务明确要读取的其它 Markdown。

历史文档缺少 front matter 时默认只记录 warning，不要求一次性改完。

### 3. 写入 front matter

使用最小可读字段：

```yaml
---
doc_key: product.design.example
doc_type: product_design
stage: design
status: active
owner: product
tags:
  - product
  - design
project_health:
  dimensions:
    - product_module_design
  evidence_level: canonical
read_contract:
  summary: "本文档说明当前产品设计结论、范围和待确认点。"
  health_signal: "用于项目健康读取产品与模块设计状态。"
  consumes: []
  produces: []
  ai_read_hint: "只在产品设计、模块设计、健康体检或需求追溯任务中读取。"
---
```

需要关联实体时补充：

```yaml
entities:
  products: []
  plans: []
  requirements: []
  modules: []
  tasks: []
  app_keys: []
```

### 4. 生成或检查索引

只看结构化结果：

```bash
python3 ops/scripts/check-doc-read-contract.py --format json
python3 ops/scripts/extract-doc-index.py --format json
```

需要生成快照时显式执行：

```bash
python3 ops/scripts/extract-doc-index.py --write --format json
```

严格检查只在项目已决定收敛文档契约时启用：

```bash
python3 ops/scripts/check-doc-read-contract.py --strict --format markdown
```

### 5. 给项目健康和 AI 任务消费

- 项目健康卡片优先读 `project_health.dimensions`、`read_contract.summary` 和 `read_contract.health_signal`。
- AI 任务准备优先读 `doc_type`、`stage`、`tags`、`entities` 和 `ai_read_hint`。
- 文档与 PM 源、任务、代码或审计记录不一致时，Markdown 文档只是一个事实源，必须与 `.maw`、PM 快照、模块档案或代码事实交叉核对。

## 验证方式

最低验证：

```bash
git diff --check
python3 -m py_compile ops/scripts/extract-doc-index.py
python3 -m py_compile ops/scripts/check-doc-read-contract.py
python3 ops/scripts/check-doc-read-contract.py --format json
python3 ops/scripts/extract-doc-index.py --format json
```

修改模板协议或能力登记时还应运行：

```bash
bash ops/scripts/check-template-module-docs.sh
bash ops/scripts/check-technical-map.sh
bash ops/scripts/check-ai-framework-consistency.sh
bash ops/scripts/check-local-boundary.sh
```

## 禁区

- 不为了索引方便而全量重写历史文档。
- 不把生成索引当作事实源反向覆盖 Markdown。
- 不把本机路径、端口、代理、token、账号密码、客户隐私、生产连接串或未脱敏日志写入 front matter。
- 不让 AI 因为生成了索引就默认读取所有命中文档；仍按任务需要读取最小片段。
- 不把 `docs/archive/**` 作为当前事实，除非用户明确要求历史追溯。

## 冲突与覆盖规则

- 用户最新说明、当前 PM 源、代码事实和 `.maw` 结构化配置优先于旧文档。
- 文档索引只提供候选读取路线；如果索引与文档正文冲突，以文档正文和当前项目事实核对为准。
- 派生项目已有自己的文档规范时，保留项目事实，按字段映射增量兼容。

## 更新记录

- 2026-06-20：创建，新增文档写读契约、文档索引和项目健康读取口径。
