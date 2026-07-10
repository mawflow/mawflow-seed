# Task Pack 示例

最小 Codex 任务包应包含：

```text
<slug>-codex-tasks/
├── README.md
├── EXECUTE_PROMPT.md
├── PLAN.md
├── manifest.json
└── prompts/
    ├── 00-session-runbook.md
    ├── 01-first-task.md
    └── 02-validation-closeout.md
```

每个任务包还需要独占状态文件：

```text
docs/implementation/<topic>/<slug>-codex-tasks/SESSION_STATE.md
```

不要多个任务包共用同一个 `SESSION_STATE.md`。
