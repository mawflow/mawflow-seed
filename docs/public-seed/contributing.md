# 贡献 Mawflow Seed

欢迎贡献文档、Prompt Spec、Pack 示例、检查脚本和模板协议改进。

## 可以优先贡献

- 更清晰的新手指南。
- 更小、更可验收的 Task Pack 示例。
- 新项目初始化检查。
- 脱敏检查和公开安全边界。
- 不绑定具体业务的 Prompt Pack。

## 不接受

- 真实客户资料。
- 真实密钥、token、私钥和生产连接串。
- 未授权 Prompt Case。
- 绑定内部平台、内部远端或私有客户环境的脚本。
- 会让公开 Seed 变成主仓控制面的运行时代码。

## 提交前

请至少运行：

```bash
git diff --check
bash ops/scripts/check-seed-open-source-readiness.sh --format json
bash ops/scripts/check-local-boundary.sh
```

如果贡献内容会影响模板协议、项目升级、模块档案、发布或脱敏边界，请同步更新相关 docs 和任务包说明。
