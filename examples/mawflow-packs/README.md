# MAWflow Pack Examples

本目录保存 MCP Knowledge Runtime 的公开示例 Pack。它们只用于模板协议、校验脚本和派生项目取舍矩阵，不代表正式官方资源库。

正式 Framework / Style / Blueprint / Prompt / Check / Verification / Case / Connector Pack 后续应进入独立 `mawflow-framework-hub` 或目标项目自己的 registry。

## 示例目录

| 示例 | 用途 |
| --- | --- |
| `prompt-pack/` | 把原始想法整理为 Prompt Spec。 |
| `task-pack/` | 展示 Codex 任务包的最小公开结构，可配合 `prompts/codex/task-packs/_template/` 使用。 |
| `check-pack/` | 展示检查脚本入口和检查说明。 |
| `verification-pack/` | 展示验收证据和交付摘要结构。 |
| `framework-fastapi-pack/` | 展示 Framework Pack manifest 和 AI context 入口。 |
| `style-default-pack/` | 展示 Style Pack manifest 和 AI context 入口。 |

## Pack Manifest

每个 Pack 至少包含：

- `pack.json`：Pack 元数据。
- `ai-context.md`：AI 可注入的短上下文入口。
- `README.md`：给人阅读的说明。

`pack.json` 的核心字段：

- `schema_version`
- `pack_id`
- `pack_type`
- `version`
- `status`
- `visibility`
- `ai_context_entry`
- `human_takeover_entry`

## 安全边界

- 示例不得包含真实 secret、客户隐私、生产日志、未脱敏源码或内部 URL。
- 派生项目采用示例前，先复制到项目自己的 `.maw/mcp/registry.json` 或私有 registry，再补 checksum、来源和审计记录。
- strict lock 下 shared registry 更新不能隐式改变当前项目。
