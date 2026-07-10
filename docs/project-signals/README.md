# 项目提示信号

项目提示信号是给人和 AI 的结构化提醒。它覆盖待办、澄清、缺口、口径变更、风险、审计提示和开发前置条件。

机器可读事实源是 `.maw/project-signals.yaml`。本目录保存维护规则和详情模板。

## 信号类型

| 类型 | 使用场景 |
| --- | --- |
| `todo` | 关联 `docs/planning/todos/active.md` 的待办 |
| `clarification` | 用户澄清、项目口径补充、术语边界 |
| `gap` | 功能、接口、数据、权限、外部系统或联调缺口 |
| `scope_change` | 需求范围、模块边界、发布范围或交付范围变化 |
| `terminology_change` | 用户习惯用语、别名或项目术语变化 |
| `risk` | 审计、巡检、发布、客户仓、数据或安全风险 |
| `audit_hint` | 后续审计/巡检/大屏应提示的检查点 |
| `ai_precondition` | AI 执行任务前必须先读取或确认的条件 |

## 维护规则

- 对人有提示意义，且可能影响后续开发、审查、发布或审计的内容，应登记信号。
- 普通模块内小 TODO 不进 `.maw/project-signals.yaml`；跨模块或被依赖的待办先进入 `docs/planning/todos/active.md`，再由信号引用 TODO-ID。
- 用户澄清和口径变化仍应按 `docs/ai-instructions/` 的项目记忆规则沉淀；项目信号负责给大屏和 AI 前置读取一个结构化摘要。
- 本机路径、端口、代理、账号、token、生产连接串和未脱敏日志不进入信号元数据。
- 关闭或替代信号时保留记录，更新 `status`、`resolution` 和 `last_updated`。

## 提取

```bash
python3 ops/scripts/extract-project-metadata.py --section signals --format json
python3 ops/scripts/extract-project-metadata.py --section ai-preconditions --format markdown
```

