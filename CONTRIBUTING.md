# Contributing

感谢你愿意改进 Mawflow Seed。

## 贡献范围

欢迎贡献：

- 文档和新手指南。
- Prompt Spec 和 Prompt Pack 示例。
- Task Pack 结构和执行经验。
- 检查脚本、脱敏规则和公开安全边界。
- 不绑定具体客户或内部平台的模板协议改进。

暂不接受：

- 真实客户资料、真实项目日志、真实账号或密钥。
- 未授权 Prompt Case。
- 生产连接串、内部远端、内部主机路径。
- 会把公开 Seed 变成 Mawflow 主仓控制面的运行时代码。

## 提交前检查

```bash
git diff --check
python3 ops/scripts/check-public-seed-workdir.py --format json --strict
```

种子开发仓维护者还应运行 source-only 的 distribution、open-source、local-boundary 和 code-deliverable gate；公开 payload 不携带内部维护源和 source-only 检查依赖。

## 许可证

Mawflow Seed 使用 MIT License，见 `LICENSE`。提交贡献即表示你同意按该许可证授权贡献内容。
