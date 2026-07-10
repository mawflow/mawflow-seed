TOPIC_STATUS: in_progress
CURRENT_TASK: 01-task-template
NEXT_TASK: 01-task-template
RESUME_FROM: 从任务包入口开始，读取 runbook 后执行第一个任务。

DONE:
- 尚未开始。

CHANGED_FILES:
- none

COMMANDS_RUN:
- none

TESTS_RUN:
- none

EXPERIENCE_LOOKUP:
- checked: no
- matched: none
- detail_read: none
- updated: none

RISKS:
- 待执行前确认。

NEXT_TASK_CONTEXT:
- 先读取 `prompts/00-session-runbook.md`。

COPY_READY_RESUME_PROMPT:
继续当前仓库的 `<任务标题>` 任务。先读取 `prompts/codex/task-packs/<slug>-codex-tasks/prompts/00-session-runbook.md` 和 `docs/implementation/<topic>/<slug>-codex-tasks/SESSION_STATE.md`，执行 `git status --short`，从 NEXT_TASK/RESUME_FROM 继续，不要从头重做，不要回滚无关改动。

SAME_SESSION_AUTO_RUN: true
CLI_WINDOW_HANDOFF: disabled_by_default
