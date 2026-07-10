# 指令：技术地图与项目提示元数据

## 元信息

- ID：TINST-030
- 类型：项目指令
- 状态：启用
- 维护位置：`docs/ai-instructions/instructions/technical-map-project-metadata.md`
- 推荐调用：`#技术地图`
- 精确调用：`#T030` 或 `#T030/技术地图`
- 触发词：#技术地图、#项目提示、#能力快照、公共能力、功能基类、API 快照、能力索引、项目大屏、项目审计、项目巡检、澄清记录、缺口记录、口径变更、AI 前置条件
- 适用范围：开发新功能/API 前查询可复用能力；沉淀公共能力、待办、澄清、缺口、口径变更和审计提示；为项目大屏、巡检和 AI 前置读取提取结构化元数据。

## 目标

让项目从业务模块树继续形成自顶向下的技术地图。开发新模块、新功能或新接口前，先查询已有模块快照、公共能力、API/基类/脚本和项目信号，减少重复实现，并把对人和 AI 有提示意义的信息沉淀到结构化元数据。

## 输入要求

- 推荐输入：功能/API/模块描述、涉及 app_key、候选 module_key、已有实现路径、用户澄清、待办或缺口说明。
- 可选输入：Story/Task、接口路径、数据表、公共基类路径、审计或巡检目标。
- 缺失时处理：能从 `.maw/modules.yaml`、`.maw/capabilities.yaml`、`.maw/project-signals.yaml`、`docs/planning/todos/active.md` 和经验候选台账确认的先确认；证据不足时记录 `candidate` 或 `monitoring`，不要编造已实现能力。

## 执行步骤

### 开发前查询

1. 读取 `.maw/modules.yaml` 定位模块和 app_key。
2. 读取 `.maw/capabilities.yaml` 查找同类公共能力、API、服务、基类、组件或脚本。
3. 读取 `.maw/project-signals.yaml` 和 `docs/planning/todos/active.md`，查找待办、澄清、缺口、口径变更、风险和 AI 前置条件。
4. 必要时运行：

```bash
python3 ops/scripts/extract-project-metadata.py --section ai-preconditions --format markdown
```

5. 命中公共能力时，优先复用或扩展；如果必须新建相似能力，在收口中说明不复用原因。

### 新增公共能力

1. 判断能力是否跨模块可复用，或是否应作为 API/基类/服务/脚本/治理协议沉淀。
2. 在 `.maw/capabilities.yaml` 新增 `capability_key`，状态初始为 `candidate` 或 `stable`。
3. 如说明较长，复制 `docs/capabilities/_template/capability.md` 创建详情页。
4. 模块档案只引用 `capability_key`，不复制完整公共能力事实。
5. 最终说明写 `capability_map_update_status`。

### 新增项目信号

1. 判断信息类型：`todo`、`clarification`、`gap`、`scope_change`、`terminology_change`、`risk`、`audit_hint` 或 `ai_precondition`。
2. 跨模块待办先进入 `docs/planning/todos/active.md`，再在 `.maw/project-signals.yaml` 引用 TODO-ID。
3. 用户澄清和口径变化按项目记忆规则进入 `docs/ai-instructions/experience-candidates.md` 或 `keyword-candidates.md`；`.maw/project-signals.yaml` 只保存大屏和 AI 前置需要的摘要。
4. 填写 severity、audience、相关模块、相关能力、证据路径和 AI 前置条件。
5. 最终说明写 `project_signal_update_status`。

### 提取给大屏或 AI

```bash
python3 ops/scripts/extract-project-metadata.py --format json
python3 ops/scripts/extract-project-metadata.py --format markdown
python3 ops/scripts/extract-project-metadata.py --section signals --format json
python3 ops/scripts/extract-project-metadata.py --section ai-preconditions --format markdown
```

## 验证方式

- `.maw/capabilities.yaml` 和 `.maw/project-signals.yaml` 可被 YAML 解析。
- `python3 -m py_compile ops/scripts/extract-project-metadata.py` 通过。
- `python3 ops/scripts/extract-project-metadata.py --format json` 可输出结构化摘要。
- `bash ops/scripts/check-technical-map.sh` 通过。
- `docs/README.md`、`PROJECT_COMMANDS.md`、`docs/ai-instructions/README.md`、最终收口模板和模块档案规则已登记本能力。

## 禁区

- 不把所有普通模块 TODO 都写入项目信号；只有对人或 AI 有跨模块提示意义的内容才进入结构化元数据。
- 不用公共能力索引替代当前代码、模块档案或设计文档；索引只指向事实源。
- 不把本机路径、端口、代理、token、账号密码、生产连接串、未脱敏日志或客户隐私写入 `.maw/project-signals.yaml`。
- 不把生成的 snapshot 当权威事实；snapshot 只用于检索，必须带生成时间或验证 commit。
- 不创建 `common/misc/general` 兜底能力；能力必须有明确复用场景和 owner。

## 冲突与覆盖规则

- 当前代码和端工程配置优先，其次是聚合 `.maw` 配置、模块档案、active 设计文档、项目信号和经验候选。
- `.maw/project-signals.yaml` 与 `docs/planning/todos/active.md` 冲突时，以 active TODO 台账的跨模块待办事实为准，并修正信号摘要。
- 用户最新澄清优先于旧项目信号；旧信号不要删除，更新为 `resolved`、`superseded` 或 `ignored`。
- 与 `TINST-037 项目评审与审计治理` 冲突时，`#项目审计：<评审报告路径>` 或 `项目审计:<评审报告路径>` 明确归 `TINST-037`；本指令只处理项目审计/巡检所需的公共能力、项目信号和机器可读元数据。

## 更新记录

- 2026-06-17：创建，新增技术地图、公共能力索引、项目信号元数据、提取脚本和收口字段。
