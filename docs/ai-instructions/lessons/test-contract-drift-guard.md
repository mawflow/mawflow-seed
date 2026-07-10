# 经验：测试契约漂移防护

## 触发场景

- GitHub Actions 或本地 pytest 在口径、文案、API 摘要、状态标签、PM 源称谓或命令输出调整后失败。
- 实现已经从某个具体系统名改为通用概念，但测试仍断言旧名称。
- 前端静态页面、路由测试或 API 摘要测试断言了用户可见文案。
- 用户要求“把 Ruff 换成 pytest”“全面取消 Ruff”后，CI 仍失败在 pytest 断言。

## 处理步骤

1. 先确认失败测试的真实意图：它是在保护公开文案、API contract、路由结构、权限状态，还是只是在锁定旧实现细节。
2. 用失败信息里的旧字面量、字段名、页面标题和接口名搜索 `tests/`、`code/*/tests/`、前端静态检查和快照文件。
3. 对比当前实现或产品口径，判断应该更新测试断言、保留兼容断言，还是修复实现回归。
4. 如果新口径是正确契约，把 pytest/static 断言同步改为新文案或稳定语义标记。
5. 运行聚焦失败测试，再运行相关 suite；目标项目测试入口不明确时，先用 `python3 ops/scripts/run-project-tests.py --format json` 发现命令。
6. 收口时说明这是测试契约同步，不要把它描述成单纯“放宽测试”。

## 判断规则

- 产品公开文案变化：测试应跟随真实文案。
- API 字段或状态 contract 变化：测试应断言新 contract，并按需要保留兼容分支。
- 结构性测试：避免断言容易变化的长文本，改用稳定字段、角色、语义标记或 `data-testid`。
- CI 工具切换：移除 Ruff/lint 不代表 pytest 已处理；仍要看失败 job 的实际测试命令和断言。
- 种子仓回流：如果这是多个派生项目都会遇到的口径变更漏同步问题，记录为 `test-contract-drift-guard` 候选或能力。

## 验证建议

```bash
pytest <失败测试路径>::<失败用例>
python3 ops/scripts/run-project-tests.py --format json
```

目标项目没有 `run-project-tests.py` 时，按项目已有 README、Makefile、pytest.ini 或 CI workflow 中的 pytest 命令执行。

## 常见坑

- 只删除旧文案断言，导致测试失去契约保护。
- 忽略前端静态页面测试，只改后端 API 测试。
- 搜索了实现文件但没搜测试文件。
- 看到 CI 邮件里的旧 commit，以为是同一次失败；必须用最新 GitHub Actions run 和 commit 对齐。
