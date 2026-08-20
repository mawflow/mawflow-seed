---
doc_key: docs.technical-map.index
doc_type: governance
stage: governance
status: active
owner: planner
tags:
  - technical-map
  - capabilities
  - signals
project_health:
  dimensions:
    - project_audit
    - ai_collaboration
  evidence_level: canonical
read_contract:
  summary: "技术地图入口，串联项目目标、模块、能力、信号和执行前读取路线。"
  health_signal: "用于项目巡检和 AI 前置读取判断当前项目公共能力和风险信号。"
  consumes: []
  produces: []
  ai_read_hint: "开发前查询公共能力、项目信号、技术地图或巡检入口时读取。"
---

# 技术地图

技术地图把项目开发从“业务模块边界”继续向上串成一条可复用的研发路线：

```text
项目目标
-> app_key / component
-> 业务模块 modules
-> 公共能力 capabilities
-> API / 基类 / 服务 / 组件 / 脚本
-> 仓库身份 repository identity
-> 宿主机项目 MCP 绑定 host-project-mcp
-> Docker-first 但不硬限定的宿主机运行环境 host-runtime-environment
-> 安装开发/线上/生产环境与本地测试入口 closeout
-> 可选 Agent Skill 发现与 CLI/MCP 适配 agent-skill-integration
-> 默认简化、按需详细的中文收口 final-closeout
-> 项目健康上下文 project-health-context
-> 待办、澄清、缺口、口径变更 project signals
-> Story / Task / 验收 / 发布
```

它不是 `docs/modules/` 的替代品。`docs/modules/` 仍然是模块事实源；技术地图负责回答“开发一个新能力之前，应该先看哪些已实现能力、公共基类、API 快照、经验和风险提示”。

## 文件分工

| 文件 | 用途 |
| --- | --- |
| `.maw/capabilities.yaml` | 机器可读公共能力索引，记录可复用 API、基类、服务、组件、脚本和治理协议 |
| `docs/capabilities/` | 公共能力的人类可读说明和能力档案模板 |
| `.maw/project-signals.yaml` | 机器可读项目提示信号，汇总待办、澄清、缺口、口径变更、风险和审计提示 |
| `docs/project-signals/` | 项目提示信号的人类维护规则和记录模板 |
| `.maw/health/` | 项目健康上下文，记录健康问题、需求事实、决策、普通健康待办、审计缺口、调研会话摘要和验收缺口，供主项目导入和 AI 健康关注读取 |
| `docs/capabilities/project-health-context.md` | 项目健康上下文能力说明 |
| `docs/ai-instructions/instructions/project-health-context.md` | `#项目健康` / `TINST-038` 执行协议 |
| `.maw/repository-identity.yaml` | 机器可读仓库身份地图，记录种子仓、主仓、平台项目仓、客户项目仓、混合仓和历史未分类仓角色 |
| `.maw/repository-identity.d/<role>/` | 角色差异化约束覆盖目录；同名字段覆盖基础身份事实 |
| `docs/repository-identity/` | 仓库身份地图的人类维护规则和记录模板 |
| `.maw/environments.yaml` 的 `host_project_binding` | 宿主机用途、项目归属、开发绑定、源码访问方式和 MCP 暴露面的可选协议字段 |
| `.maw/environments.yaml` 的 `host_runtime_environment` | Docker-first 但不硬限定、本地测试即改即生效、线上发布为编译后测试环境、开发/线上/生产环境口径、安装环境前确认、安装测试环境默认沿用线上测试数据库且共库时必须警告、根 `package.json` 本地测试启动命令面板、canonical `npm run local:dev`、`ops/scripts` 自动同步检查、任务收口本地测试入口、`remote_test_server` 缺失回退 `remote_staging_server`、统一 Docker 命名、既有环境保护、本地/线上默认可共库联调、离线镜像、本地宿主机 PG 数据面和项目环境矩阵 |
| `docs/capabilities/host-project-mcp-governance.md` | 宿主机项目 MCP 绑定治理能力说明 |
| `docs/capabilities/host-runtime-environment-protocol.md` | 宿主机运行环境协议能力说明 |
| `docs/capabilities/agent-skill-integration.md` | 可选 Mawflow Agent Skill 的发现、适配、降级与版本兼容协议 |
| `docs/capabilities/final-closeout-response-protocol.md` | 中文收口展示协议能力说明，默认简化验证结论，按需展开命令和技术元数据 |
| `docs/ai-instructions/instructions/install-environment.md` | `#安装开发环境`、`#安装线上环境`、`#安装生产环境` 的执行协议 |
| `ops/scripts/extract-project-metadata.py` | 提取 modules、capabilities、project signals、active TODO 和经验候选，输出 JSON/Markdown |
| `ops/scripts/check-technical-map.sh` | 检查技术地图、能力索引、项目信号和提取脚本是否可用 |

## 指令与收口字段

- 推荐调用：`#技术地图`
- 精确调用：`#T030` / `TINST-030`
- 公共能力收口字段：`capability_map_update_status`
- 项目信号收口字段：`project_signal_update_status`

## 开发前使用方式

开发新功能或接口前，AI/Planner 应按以下顺序查找：

1. 用 `.maw/modules.yaml` 定位业务模块和 app_key。
2. 如果只有页面 URL、API、命令或文件路径，先读所属一级模块 `route-api-index.md`，落到二级模块后再读 `module.md` 和必要的 detail docs。
3. 用 `.maw/capabilities.yaml` 查是否已有同类公共能力、API、服务、基类、组件或脚本。
4. 用 `.maw/project-signals.yaml` 和 `docs/planning/todos/active.md` 查当前是否有待办、澄清、缺口、口径变更或风险提示。
5. 如命中公共能力，优先复用或扩展；如需要新增公共能力，先登记为 `candidate`，至少写清来源模块、实现路径、复用约束和验证方式。
6. 如命中项目信号，把它列为 AI 前置条件；如果信号已过期或被解决，同步更新状态。

可直接用脚本生成给人或 AI 的摘要：

```bash
python3 ops/scripts/extract-project-metadata.py --format json
python3 ops/scripts/extract-project-metadata.py --format markdown
python3 ops/scripts/extract-project-metadata.py --section host-project-mcp --format markdown
python3 ops/scripts/extract-project-metadata.py --section ai-preconditions --format markdown
```

## 能力沉淀规则

公共能力进入 `.maw/capabilities.yaml` 的条件：

- 一个模块已经实现，且另一个模块可能复用。
- API、服务、基类、组件、脚本或治理协议有稳定名称和路径。
- 需要避免其它模块重复造同类能力。
- 修改该能力会影响多个模块、app_key、发布或验收。

状态建议：

| 状态 | 含义 |
| --- | --- |
| `candidate` | 已发现复用价值，但仍需验证或第二个模块消费 |
| `stable` | 已被复用或确认可作为长期公共能力 |
| `deprecated` | 不再推荐新模块使用，但保留兼容说明 |
| `blocked` | 设计未定或依赖待办未完成，暂不能复用 |

公共能力说明不要复制进每个模块档案。模块档案只引用 `capability_key`，能力事实写在 `.maw/capabilities.yaml` 和 `docs/capabilities/<capability-key>.md`。

## 项目信号沉淀规则

以下内容对人和 AI 都有提示意义，必须判断是否进入 `.maw/project-signals.yaml`：

- 当前业务闭环依赖的待办或缺口。
- 用户澄清、项目口径、术语或范围发生变化。
- 某个模块依赖另一个模块尚未稳定的 API、字段、状态或权限。
- 巡检、审计、验收、大屏展示需要高亮的风险、阻塞、缺口或人工确认项。
- AI 开发前必须知道的前置条件。

`docs/planning/todos/active.md` 仍是跨模块待办事实源；`.maw/project-signals.yaml` 可以引用 TODO-ID，并额外记录对人类大屏和 AI 前置读取友好的摘要、严重程度、受影响模块和处置建议。

## 验证

```bash
python3 -m py_compile ops/scripts/extract-project-metadata.py
python3 ops/scripts/extract-project-metadata.py --format json
bash ops/scripts/check-technical-map.sh
```
