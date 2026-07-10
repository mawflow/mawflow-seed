# Check Pack 示例

## purpose

在提交、分发或公开前运行稳定检查。

## suggested_commands

```bash
git diff --check
bash ops/scripts/check-template-module-docs.sh
bash ops/scripts/check-seed-open-source-readiness.sh --format json
bash ops/scripts/check-local-boundary.sh
```

## result_policy

- `OK`：可以继续下一步。
- `WARN`：记录风险，必要时人工确认。
- `BLOCKED`：不能公开或分发，先解决阻塞项。
