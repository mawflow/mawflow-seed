# 公开与脱敏规则

公开 Mawflow Seed、Pack、Prompt Case 或任务包前，必须先确认以下内容没有进入仓库或交付包。

## 不得公开

- `.local/**` 真实内容。
- `.maw/*.local.yaml`。
- SSH 私钥、API Key、token、cookie、账号密码。
- 生产数据库连接串、客户服务器地址、未脱敏日志。
- 客户源码、客户数据、客户 issue、客户截图。
- 内部 prompt、hidden workspace、内部运维路径。
- 主仓 Orchestrator / Workbench / Platform MCP / HostCommand / ActionRun 运行时代码。

## 可以公开

- 模板协议和说明文档。
- 不含真实项目数据的示例 `.maw` 配置。
- 可复用 Prompt Spec。
- 可复用 Task Pack 结构。
- 检查脚本和文档治理规则。
- 已脱敏、已授权、已复核的 Prompt Case。

## Prompt Case 公开流程

1. 用户主动授权。
2. 删除项目名、客户名、账号、URL、路径、token 和日志正文。
3. 保留目标、约束、验收、验证和复盘结构。
4. 用户二次确认。
5. 维护者审核后再发布。

## 推荐检查

```bash
bash ops/scripts/check-seed-open-source-readiness.sh --format json
bash ops/scripts/check-local-boundary.sh
```
