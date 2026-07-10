---
doc_key: docs.ai-instructions.instructions.project-health-context
doc_type: governance
stage: governance
status: active
owner: planner
tags:
  - instruction
  - project-health
  - health-context
project_health:
  dimensions:
    - product_requirement
    - task_execution
    - project_audit
    - ai_collaboration
  evidence_level: canonical
read_contract:
  summary: "TINST-038 / #项目健康 指令，维护 .maw/health/ 项目健康上下文。"
  health_signal: "用于 AI 日常开发和审计时把健康问题、事实、决策、调研摘要和验收缺口沉淀为可导入上下文。"
  consumes:
    - .maw/health/README.md
    - .maw/health/issues.yaml
    - .maw/health/facts.yaml
    - .maw/health/decisions.yaml
  produces:
    - .maw/health/
  ai_read_hint: "用户要求记录项目健康问题、审计项目健康、生成健康关注建议、把缺口变成调研问题或收口更新健康上下文时读取。"
---

# 指令：项目健康上下文

## 1. 指令元信息

- 编号：TINST-038
- 推荐调用：`#项目健康`
- 精确调用：`#T038`
- 触发词：项目健康、健康上下文、记录项目健康问题、记录这个缺口、审计项目健康、摸一下项目健康问题、生成健康关注建议、把这些缺口变成调研问题、收口时更新健康上下文、`.maw/health`
- 适用范围：维护 `.maw/health/` 中的健康问题、需求事实、关键决策、普通健康待办、审计缺口、调研会话摘要和验收标准缺口。
- 收口字段：`health_context_update_status`

## 2. 目标

把 AI 日常开发、任务收口、项目审计和用户调研中长期有价值的健康上下文沉淀为结构化 YAML，让 Mawflow 主项目、Codex、ChatGPT 和其它 AI Agent 可以稳定读取、审计、导入和转化为项目健康关注、调研会话、PM 需求候选、研发任务建议、测试验收点和文档更新建议。

## 3. 触发模式

| 调用 | 行为 |
| --- | --- |
| `#项目健康：记录 <问题或事实>` | 分析类型，写入 `issues.yaml`、`facts.yaml`、`decisions.yaml`、`todos.yaml`、`audit-gaps.yaml` 或 `acceptance-gaps.yaml` |
| `#项目健康：审计` | 读取 `.maw/health/`、`docs/planning/todos/`、项目评审/模块审计报告和必要 TODO/FIXME 摘要，输出健康问题概览 |
| `#项目健康：生成关注建议` | 从健康问题、普通健康待办、审计缺口和验收缺口中筛选 3-5 个自然调研问题和健康确认项草案 |
| `#项目健康：导入准备` | 校验 `.maw/health/`，说明可被主项目导入的文件、字段和风险 |
| 任务收口 | 判断本轮是否新增事实、决策、待办、缺口或验收问题，必要时更新 `.maw/health/` |

## 4. 路由边界

1. 跨模块、被当前业务闭环依赖、先假设已完成的待办，走 `#待办任务` / `TINST-028`，事实源是 `docs/planning/todos/active.md`。`.maw/health/todos.yaml` 只保存普通健康待办或 TODO-ID 摘要。
2. 项目方向、业务流程、验收目标和 docs 口径评审，走 `#项目评审` / `#项目审计` / `TINST-037`，完整报告写 `docs/project-review-audits/`。`.maw/health/audit-gaps.yaml` 只保存可导入缺口。
3. 关键 docs 要被项目健康或审计读取时，走 `#文档索引` / `TINST-033` 补 front matter 和索引。`.maw/health/` 不替代 Markdown 事实源。
4. 对人或 AI 有全局提示意义的高风险内容，可以同步摘要到 `.maw/project-signals.yaml`，但完整上下文仍保留在 `.maw/health/` 或原始事实源。
5. 主仓的数据库、API、页面、PM 系统同步和权限隔离实现不进入种子仓；种子仓只沉淀文件标准、示例、指令和检查脚本。

## 5. 记录流程

1. 读取 `.maw/health/README.md`、目标 YAML 文件，以及相关事实源。
2. 判断事项类型：
   - 健康问题：`issues.yaml`
   - 已确认或待确认事实：`facts.yaml`
   - 用户或负责人拍板：`decisions.yaml`
   - 普通健康待办：`todos.yaml`
   - 审计缺口：`audit-gaps.yaml`
   - 调研会话摘要：`research-sessions.yaml`
   - 验收标准缺口：`acceptance-gaps.yaml`
3. 分配稳定 ID，写项目根相对路径来源。
4. 标记状态和置信度。AI 推断只能写 `ai_inferred`、`uncertain`、`pending` 或等价状态；用户确认后才写 `confirmed`。
5. 如果用户打叉或否定 AI 判断，保留原判断、打叉理由，并生成修正事实或待澄清问题。
6. 运行 `python3 ops/scripts/check-project-health-context.py --format json`。
7. 收口写明 `health_context_update_status`，说明新增、更新、未涉及或未更新原因。

## 6. 审计与关注建议

执行 `#项目健康：审计` 时：

- 先读取 `.maw/health/`。
- 再按需读取 `docs/planning/todos/active.md`、最近项目评审/审计报告、模块审计报告和当前任务涉及路径中的 TODO/FIXME。
- 不全量扫描 `docs/**` 或 `code/**`；先用 `.maw/modules.yaml`、文档索引或用户给定范围缩小读取面。
- 输出高优先级健康问题、需要用户确认的事实、建议发起的调研主题、3-5 个自然问题和确认项草案。

## 7. 安全与敏感信息

- 不记录真实密钥、账号密码、私钥、生产连接串、未脱敏日志、客户隐私或完整源码片段。
- 来源只写路径、摘要、行号或外部系统引用，不复制敏感正文。
- 本机路径、端口、代理和一次性排障细节写 `.local/`，不写 `.maw/health/`。
- 对外部交付或客户仓同步前，健康文件也必须纳入脱敏检查。

## 8. 验证

```bash
python3 ops/scripts/check-project-health-context.py --format json
npm run check:project-health-context
```

## 9. 收口

最终说明包含：

- 是否更新 `.maw/health/`。
- 更新了哪些文件和 ID。
- 是否需要同步 `docs/planning/todos/`、`docs/project-review-audits/`、`docs/modules/`、`docs/acceptance/` 或 `.maw/project-signals.yaml`。
- 是否运行 `check-project-health-context.py`。
- `health_context_update_status`。

## 10. 变更记录

- 2026-06-27：创建，新增项目健康上下文标准、主仓导入衔接、健康关注建议和收口字段。
