# 任务级变更片段

每个任务只新增或修改自己拥有的 `.maw/changes/<task-key>-<record-key>.yaml`，不要在并行分支直接重写聚合索引。

最小格式：

```yaml
schema_version: 1
record_key: capability.example
task_key: TASK-001
record_type: capability
operation: upsert
payload:
  summary: 示例能力
evidence_refs:
  - path: code/example
    kind: repository_path
```

`record_key` 相同且规范化后的 `payload` 不同，不自动覆盖或选边；聚合结果会保留全部候选并标记 `needs_human_review`。运行：

```bash
python3 ops/scripts/manage-project-lifecycle.py aggregate --format json
```

## 更新动态片段

面向使用者的实际更新采用 `record_type: update_note`、`operation: append`，payload 遵循 `.maw/schemas/update-note.schema.json`。日常新增、优化、修复、安全或使用文档变化在验证后追加；同 ID 重试不重复，更正用新 ID 的 `payload.supersedes` 关联旧条目，保留原文。

`#更新动态` 默认生成最近 100 条，`#更新动态：全部` 生成完整历史。规范、示例和云端分页见 [更新动态规范](../../docs/ai-coding/update-notes.md)。通用 aggregate 继续兼容全部片段；更新动态生成器只消费 `update_note`。
