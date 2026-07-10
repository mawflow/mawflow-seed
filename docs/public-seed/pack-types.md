# Mawflow Pack 类型

Mawflow Seed 使用 Pack 把 AI Coding 项目里的可复用资产整理成稳定形态。

| Pack | 用途 | 典型位置 |
| --- | --- | --- |
| Seed Pack | 项目初始化装备，包含 `.maw`、docs、prompts、ops 和示例目录 | 仓库根目录 |
| Prompt Pack | 可复用提示词结构和案例 | `prompts/` 或 `examples/mawflow-packs/prompt-pack/` |
| Task Pack | 可恢复、分阶段执行的 Codex 任务提示词工程 | `prompts/codex/task-packs/<slug>-codex-tasks/` |
| Check Pack | 项目检查脚本和检查说明 | `ops/scripts/`、`docs/capabilities/` |
| Verification Pack | 交付后的验收、证据和风险记录 | `docs/acceptance/`、`docs/delivery/` |
| Case Pack | 可公开的 Prompt Case 和执行复盘 | 后续由 Prompt Hub 承接 |

## Pack 元数据建议

每个可复用 Pack 应至少说明：

- `name`：稳定名称。
- `purpose`：解决什么问题。
- `inputs`：需要哪些上下文。
- `outputs`：产出什么文件或证据。
- `safe_to_publish`：是否可公开。
- `sanitization`：公开前脱敏要求。
- `validation`：检查命令或人工验收。

## 示例

最小示例在 `examples/mawflow-packs/`。
